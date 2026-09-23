"""The generation half of the W7 book port: bars -> candidate intents.

Session H ported the book's *decision* side (``sleeve_book.SleeveBookPolicy``) and
deliberately stopped at generation (its B91).  ``core.py:241`` and
``sleeve_book.py:37`` both name a ``generate_from_bars`` that was never written;
this module is it.

Why delegation, not reimplementation
------------------------------------
The whole value of this lane is that it measures **what actually trades**.  A
port that re-derives the sleeve logic measures the port instead, and re-opens F1
rather than closing it.  So this module reimplements **no** generation
arithmetic.  It constructs the production ``UltimateBookLiveEngine`` and calls
``_generate_intents`` — the exact method ``book_engine.py:720`` calls in
production — behind an ``mt5``-shaped bar feed.  Every gate the live engine
applies (``book_engine.py:439-529``: the DF-1 active-book filter, the
``supports()`` profile intersection, the ``enough()`` warmup floor, the future-
bar and 2-interval staleness guards, the per-sleeve generator itself) therefore
applies here **because it is the same code**, not because it was copied.

The three impurities, reproduced rather than fixed
--------------------------------------------------
Live generation is not a pure function of bars.  Three inputs make it
wall-clock- and disk-dependent, and a faithful port reproduces all three rather
than quietly improving on them (defect register D13/D14/D15):

1. ``runtime_now`` -> the market-expansion ``decision_day``.
   ``market_expansion_d1.next_open_decision_day`` (``:147-161``) returns the
   **wall-clock** date, not the bar's, and overrides the bar-derived day on all
   12 market-expansion intents (``:217-221``).  Replaying the same bars at a
   different moment therefore yields a different correlated-unit bucket.  We
   drive it from the replay clock, so a replay is reproducible *given its clock*
   — which is the strongest fidelity available without changing live behaviour.
2. The bar-time repair latch (``book_engine.py:119-122, 214-309``) is persisted
   under ``pipeline_state/ultimate_book/<namespace>/``.  It can shift ``times``
   and therefore move ``decision_day`` and ``decision_bar_iso``.  A replay must
   NOT read or write the live latch, so ``state_root`` defaults to a scratch
   directory; pass the live root explicitly to reproduce a latched run.
3. The recency gates (``book_engine.py:488-500``) compare bar close against
   ``now``.  They are driven by the replay clock.

Nothing here places, sizes, or admits.  Generation runs before the authority
gates in live too (``book_engine.py:720`` vs ``:741``), so this module is
inert with respect to the broker by construction: it never constructs a real
MT5 client and ``ReplayMT5`` has no ``order_send``.
"""

from __future__ import annotations

import gzip
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, Optional, Protocol, Sequence, runtime_checkable

from .core import PolicyCandidate

SCHEMA = "gtos.phase3.replay_policy.generation.v1"

#: A bare number in a bar file's ``time`` column is an MT5 epoch, never a date. The two
#: cannot be confused: an ISO stamp always carries a ``-`` or a ``:``, and an epoch never
#: does. Used to decode the ENCODING from the bytes, because no sidecar schema in this repo
#: declares it --- see ``CsvBarSource._load``.
_EPOCH_TOKEN = re.compile(r"^[+-]?\d+(?:\.\d+)?$")

# MT5 timeframe constant -> bar interval in minutes.  Mirrors book_engine.py:21;
# duplicated rather than imported so a bar source can be used without importing
# the live engine.
TF_MINUTES: Mapping[int, int] = {1: 1, 5: 5, 15: 15, 30: 30, 16385: 60, 16388: 240, 16408: 1440}


class GenerationError(ValueError):
    """A generation replay could not be run, and refuses to guess one."""


# ---------------------------------------------------------------------------
# the bar seam
# ---------------------------------------------------------------------------
@runtime_checkable
class BarSource(Protocol):
    """Where closed bars come from.

    This is the *only* seam between the port and market data, so ingesting a new
    archive (e.g. the VPS ``copy_rates_range`` pull) is a wiring job: implement
    this protocol and pass it to ``GenerationPort``.  Nothing downstream knows
    where bars came from.

    ``candles`` must return MT5-shaped dicts —
    ``{"time": <UTC ISO8601>, "open", "high", "low", "close", "volume"}`` — in
    ascending time order, being the ``count`` most recent bars **at or before**
    ``as_of_utc``, INCLUDING the bar currently forming at ``as_of_utc`` when one
    exists.  The forming bar is required because ``bar_provider.candles_to_bars``
    drops the last element (``bar_provider.py:58``); a source that omits it
    silently costs the caller its most recent closed bar.

    Returning fewer than ``count`` bars is allowed and is not an error — the live
    warmup gate (``bar_provider.enough``) fails closed on a short series, which
    is the behaviour a replay should reproduce.
    """

    def candles(self, symbol: str, timeframe: int, count: int,
                as_of_utc: datetime) -> list[dict]: ...

    def describe(self) -> Mapping[str, Any]: ...


class EmptyBarSource:
    """A ``BarSource`` that has no data.

    The null control for the port: every sleeve warmup-gates closed, so a
    generation run over it must produce exactly zero candidates.  A run that
    produces anything against this source is measuring something other than
    bars.
    """

    def candles(self, symbol: str, timeframe: int, count: int,
                as_of_utc: datetime) -> list[dict]:
        return []

    def describe(self) -> Mapping[str, Any]:
        return {"kind": "empty", "schema": SCHEMA}


@dataclass
class InMemoryBarSource:
    """Bars held in memory, keyed ``(canonical_symbol, timeframe)``.

    ``series`` values are ascending lists of MT5-shaped candle dicts whose
    ``time`` is a true-UTC ISO8601 string.  Used by the behavioural tests and by
    any caller that has already materialised bars (tick aggregation, CSV
    archive, the VPS pull).
    """

    series: dict[tuple[str, int], list[dict]] = field(default_factory=dict)
    label: str = "in_memory"

    def add(self, symbol: str, timeframe: int, candles: Iterable[dict]) -> None:
        rows = sorted(candles, key=lambda c: c["time"])
        self.series[(symbol, int(timeframe))] = rows

    def candles(self, symbol: str, timeframe: int, count: int,
                as_of_utc: datetime) -> list[dict]:
        rows = self.series.get((symbol, int(timeframe)))
        if not rows:
            return []
        cutoff = as_of_utc.astimezone(timezone.utc).isoformat()
        # bars whose OPEN is at or before `now`; the last of these is the bar
        # forming at `now`, which live also returns and bar_provider then drops.
        visible = [r for r in rows if r["time"] <= cutoff]
        return visible[-int(count):] if count > 0 else []

    def describe(self) -> Mapping[str, Any]:
        return {
            "kind": "in_memory",
            "label": self.label,
            "schema": SCHEMA,
            "series": sorted(f"{s}:{tf}" for (s, tf) in self.series),
        }


class CsvBarSource:
    """Bars from an MT5-export CSV archive, converted to true UTC on load.

    The repo's bar archives (``data/historical_2026/``, and the VPS
    ``copy_rates_range`` pulls) are ``time,open,high,low,close[,volume,...]``
    with ``time`` in **broker server local** wall clock, declared by a
    ``<file>.timebase.json`` sidecar.  Reading those stamps as UTC is finding F7
    and puts every session-anchored sleeve on the wrong bar, so conversion is
    done here, once, at load, via ``broker_clock`` — never by the caller.

    A file without a sidecar is refused rather than assumed UTC: an undeclared
    timebase is exactly how F7 happened.  Pass ``assume_rule`` only for archives
    whose basis is independently known.

    ``symbol_files`` maps ``(canonical_symbol, timeframe)`` to a path, so the
    canonical->broker naming crossing stays the caller's business (the live
    engine fetches under the broker name, ``book_engine.py:461``).
    """

    def __init__(self, symbol_files: Mapping[tuple[str, int], Any], *,
                 assume_rule: Any = None, label: str = "csv") -> None:
        self._files = dict(symbol_files)
        self._assume_rule = assume_rule
        self._label = label
        self._cache: dict[tuple[str, int], list[dict]] = {}
        self._keycache: dict[tuple[str, int], list[str]] = {}
        # Rows outside the window a sidecar declares itself valid over, per series. They
        # are dropped --- their basis was never measured --- and the count rides on
        # describe() so the drop can never be silent, which is the failure mode this
        # programme keeps re-finding (wave-10 §2).
        self._out_of_declared_range: dict[str, int] = {}
        # Rows whose `time` cell could not be decoded under the declared basis. Same rule:
        # counted, published on describe(), and --- when it is ALL of them --- fatal.
        self._unparseable: dict[str, int] = {}

    @staticmethod
    def _rule_for(path, assume_rule):
        """``(rule, encoding)`` for a bar file, or raise.

        Two sidecar schemas are in use and both are honoured, because refusing the
        newer one would mean hand-converting outside the seam — which is how F7
        happens.

        * ``gtos_timebase_sidecar_v1`` (``data/historical_2026/``) — declares
          ``time_column_basis`` and ``broker_clock_server``; ``time`` is a naive
          broker-local datetime string.
        * the VPS bars export (``vps-bars-20260727/``) — declares ``timebase``
          and ``broker``; ``time`` is a raw MT5 **epoch integer** whose decode-as-UTC
          yields the broker wall clock.

        ``encoding`` is ``"epoch"``, ``"naive"`` or ``"utc"``.  A file with no
        sidecar is still refused.
        """
        import json
        import pathlib

        from src.utils import broker_clock

        sidecar = pathlib.Path(str(path) + ".timebase.json")
        if sidecar.is_file():
            meta = json.loads(sidecar.read_text())
            # schema 1
            basis = meta.get("time_column_basis")
            if basis is not None:
                # ``"utc"`` is this reader's own historical spelling; ``"true_utc"`` is what
                # src/utils/research_timebase.write_sidecar --- the SANCTIONED writer, and the
                # only one --- actually emits. Accepting only ``"utc"`` meant a true-UTC
                # sidecar written by the sanctioned tool fell through to the broker-local
                # branch and got a SECOND correction applied to already-UTC stamps: F7
                # reintroduced one layer up, by the repair. No such sidecar existed until
                # 2026-07-30, so nothing had ever hit it (Session AV, B1613).
                if basis in ("utc", "true_utc"):
                    return None, "utc"
                if basis == "broker_server_local_eu_calendar_corrected":
                    return None, "eu_corrected"
                if basis != "broker_server_local":
                    raise GenerationError(
                        f"{sidecar}: unrecognised time_column_basis {basis!r}; refusing to guess")
                server = meta.get("broker_clock_server")
                if not server:
                    raise GenerationError(f"{sidecar}: sidecar declares no broker_clock_server")
                return broker_clock.resolve_rule(server), "naive"
            # schema 2 — the VPS export
            timebase = meta.get("timebase")
            if timebase == "broker_server_wall_clock":
                server = meta.get("broker")
                if not server:
                    raise GenerationError(f"{sidecar}: sidecar declares no broker")
                return broker_clock.resolve_rule(server), "epoch"
            raise GenerationError(
                f"{sidecar}: unrecognised timebase declaration {meta!r}; refusing to guess")
        if assume_rule is not None:
            return assume_rule, "naive"
        raise GenerationError(
            f"{path}: no .timebase.json sidecar; refusing to assume the time basis (F7)")

    def _load(self, key: tuple[str, int]) -> list[dict]:
        if key in self._cache:
            return self._cache[key]
        import csv as _csv
        import pathlib

        from src.utils import broker_clock

        path = self._files.get(key)
        if path is None:
            self._cache[key] = []
            return []
        path = pathlib.Path(path)
        if not path.is_file():
            self._cache[key] = []
            return []
        rule, encoding = self._rule_for(path, self._assume_rule)
        lo, hi = self._declared_window(path)
        n_out_of_range = 0
        n_unparseable = 0
        first_bad: str | None = None
        rows: list[dict] = []
        opener = (gzip.open if str(path).endswith(".gz") else open)
        with opener(path, "rt", newline="") as fh:
            for rec in _csv.DictReader(fh):
                raw = (rec.get("time") or "").strip()
                if not raw:
                    continue
                if lo or hi:
                    day = raw[:10]
                    if (lo and day < lo) or (hi and day > hi):
                        n_out_of_range += 1
                        continue
                # ENCODING IS A PROPERTY OF THE BYTES, NOT OF THE SIDECAR SCHEMA.
                # `_rule_for` used to infer it from which schema wrote the sidecar --- schema 2
                # (the VPS bars export) meant epoch, schema 1 meant an ISO string --- and that
                # held only because those two tools happened to pair that way. The sanctioned
                # writer (`research_timebase.write_sidecar`) emits schema 1 and has NO encoding
                # field at all: `time_column_basis` states the BASIS (which clock), never the
                # ENCODING (epoch or ISO). So a bridge export stamped by the sanctioned writer
                # carries schema 1 over epoch integers, every `fromisoformat` raised, every row
                # was `continue`d, and the series loaded as EMPTY --- a fail-CLOSED loader
                # failing open into silence. Measured on
                # `bridge_ftmo_carrycond_h4_m1_20260730` (Session CA, B2104): 8 of 8 files,
                # 0 rows each, no error. Detect from the token instead.
                as_epoch = _EPOCH_TOKEN.match(raw) is not None
                try:
                    if encoding == "epoch" or as_epoch:
                        if rule is None:
                            # a `true_utc` basis over epochs: a plain POSIX timestamp
                            stamp = datetime.fromtimestamp(float(raw), tz=timezone.utc)
                        else:
                            # MT5's epoch decodes-as-UTC to the broker wall clock
                            # (broker_clock.py:434-437); never decode it as UTC and keep it.
                            stamp = broker_clock.broker_epoch_to_utc(float(raw), rule)
                    else:
                        naive = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                        if rule is None:
                            stamp = naive if naive.tzinfo else naive.replace(tzinfo=timezone.utc)
                            stamp = stamp.astimezone(timezone.utc)
                            if encoding == "eu_corrected":
                                from src.utils.research_timebase import (
                                    in_us_eu_dst_disagreement,
                                )
                                if in_us_eu_dst_disagreement(stamp.date()):
                                    stamp = stamp - timedelta(hours=1)
                        else:
                            stamp = broker_clock.broker_naive_to_utc(
                                naive.replace(tzinfo=None), rule)
                except (TypeError, ValueError, OSError, OverflowError):
                    n_unparseable += 1
                    if first_bad is None:
                        first_bad = raw
                    continue
                try:
                    rows.append({
                        "time": stamp.isoformat(),
                        "open": float(rec["open"]), "high": float(rec["high"]),
                        "low": float(rec["low"]), "close": float(rec["close"]),
                        "volume": float(rec.get("tick_volume") or rec.get("volume") or 0.0),
                    })
                except (KeyError, TypeError, ValueError):
                    n_unparseable += 1
                    if first_bad is None:
                        first_bad = raw
                    continue
        rows.sort(key=lambda r: r["time"])
        if n_out_of_range:
            self._out_of_declared_range[f"{key[0]}:{key[1]}"] = n_out_of_range
        if n_unparseable:
            self._unparseable[f"{key[0]}:{key[1]}"] = n_unparseable
        # A SERIES THAT PARSED TO NOTHING IS A REFUSAL, NOT AN EMPTY SERIES.
        # Returning `[]` here is indistinguishable from "this symbol has no file", and the
        # caller's next move is to skip the symbol with every log reading healthy. That is
        # exactly how the mis-declared bridge export above would have silently REMOVED four
        # symbols from a sleeve's surface and made the run look like a smaller-but-fine one.
        # An empty result caused by a *declared* window stays legal --- it is recorded and
        # deliberate --- but an empty result caused by unparseable bytes fails closed, loudly.
        if not rows and n_unparseable:
            raise GenerationError(
                f"{path}: {n_unparseable} rows and 0 usable bars --- the sidecar's declared "
                f"basis/encoding does not fit the bytes (first unparseable time value: "
                f"{first_bad!r}). Refusing to return an empty series that reads as 'no data'.")
        self._cache[key] = rows
        return rows

    @staticmethod
    def _declared_window(path) -> tuple[str | None, str | None]:
        """``(valid_from, valid_through)`` ISO dates from the sidecar, or ``(None, None)``.

        A file spliced from two captures --- ``data/historical/`` is, measured (Session AV,
        B1607) --- has one clock in its body and another in its tail. The sidecar declares
        the span the basis was measured over; rows outside it were never established and
        are dropped rather than read under a basis that does not cover them.
        """
        import json
        import pathlib

        sidecar = pathlib.Path(str(path) + ".timebase.json")
        if not sidecar.is_file():
            return None, None
        meta = json.loads(sidecar.read_text())
        lo = meta.get("valid_from") or None
        hi = meta.get("valid_through") or None
        return (str(lo) if lo else None, str(hi) if hi else None)

    def candles(self, symbol: str, timeframe: int, count: int,
                as_of_utc: datetime) -> list[dict]:
        rows = self._load((symbol, int(timeframe)))
        if not rows or count <= 0:
            return []
        # rows are sorted by ISO time, which is lexicographically ordered, so the
        # visible window is a bisect rather than a scan.  A replay makes one call
        # per (sleeve, symbol, bar close); at M15 over a month that is ~10^5
        # calls, and the linear form made the run quadratic in series length.
        import bisect

        keys = self._keys((symbol, int(timeframe)))
        hi = bisect.bisect_right(keys, as_of_utc.astimezone(timezone.utc).isoformat())
        return rows[max(0, hi - int(count)):hi]

    def _keys(self, key: tuple[str, int]) -> list[str]:
        cached = self._keycache.get(key)
        if cached is None:
            cached = [r["time"] for r in self._load(key)]
            self._keycache[key] = cached
        return cached

    def coverage(self) -> dict[str, tuple[str, str, int]]:
        """``"SYMBOL:tf" -> (first_utc, last_utc, n_bars)`` for every loadable series."""
        out: dict[str, tuple[str, str, int]] = {}
        for key in self._files:
            rows = self._load(key)
            if rows:
                out[f"{key[0]}:{key[1]}"] = (rows[0]["time"], rows[-1]["time"], len(rows))
        return out

    def describe(self) -> Mapping[str, Any]:
        return {"kind": "csv", "label": self._label, "schema": SCHEMA,
                "declared_series": sorted(f"{s}:{tf}" for (s, tf) in self._files),
                "rows_dropped_outside_declared_timebase_window":
                    dict(sorted(self._out_of_declared_range.items())),
                "rows_dropped_unparseable_time_cell":
                    dict(sorted(self._unparseable.items()))}


class ReplayMT5:
    """An ``mt5``-shaped read-only facade over a ``BarSource``.

    Only the surface ``_generate_intents`` actually touches is implemented.  It
    is deliberately NOT an ``MT5Interface`` subclass: the interface declares
    ``order_send`` and the whole point of this object is that no order path
    exists on it.  ``create_mt5("live")`` succeeds on macOS (the ImportError only
    surfaces on ``.connect()``), so "cannot construct a real client" is not a
    safety boundary — "has no method that could send" is.

    ``get_broker_offset_seconds`` returns ``None`` so the engine's bar-time
    repair takes its documented "offset unavailable" path rather than inventing
    one from a live tick that does not exist in replay.
    """

    def __init__(self, bars: BarSource, *, now: Optional[datetime] = None) -> None:
        self._bars = bars
        self._now = now
        self.calls: list[tuple[str, int, int]] = []

    # -- replay clock -------------------------------------------------------
    @property
    def now(self) -> datetime:
        if self._now is None:
            raise GenerationError("replay clock not set; call set_now() before generating")
        return self._now

    def set_now(self, now: datetime) -> None:
        self._now = now.astimezone(timezone.utc)

    # -- the one method generation needs ------------------------------------
    def get_candles(self, symbol: str, timeframe: int, count: int) -> list[dict]:
        self.calls.append((symbol, int(timeframe), int(count)))
        return list(self._bars.candles(symbol, int(timeframe), int(count), self.now))

    # -- inert surface the engine probes ------------------------------------
    def get_broker_offset_seconds(self) -> Optional[float]:
        return None

    def get_tick(self, symbol: str = "XAUUSD") -> None:
        return None

    def get_account_equity(self) -> Optional[float]:
        return None

    def get_account_balance(self) -> Optional[float]:
        return None

    def describe(self) -> Mapping[str, Any]:
        return {"kind": "replay_mt5", "bars": dict(self._bars.describe())}


# ---------------------------------------------------------------------------
# outputs
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GenerationResult:
    """One cycle's generation, in the core's vocabulary plus the live telemetry.

    ``candidates`` are ``PolicyCandidate`` — the shape ``SleeveBookPolicy.decide``
    consumes — so a caller can run generation and decision end-to-end.
    ``telemetry`` and ``skips`` are the live engine's own
    ``_last_generation_telemetry`` / ``_last_generation_skips``
    (``book_engine.py:536-538``), carried through unmodified: they are the
    per-cycle record the live packets expose as
    ``bridge.broker_profile_generation``, so a replay can be compared against
    live on the same fields.

    ``evaluations`` is the port's own addition and does not exist live: the
    number of (sleeve, symbol) slots whose generator was actually *invoked*.
    Live leaves no trace when a generator returns ``None``
    (``book_engine.py:528-529``), so this is the denominator G4 needs and the one
    number here that live cannot corroborate.  It is reported separately for
    exactly that reason.
    """

    now_utc: datetime
    candidates: tuple[PolicyCandidate, ...]
    telemetry: Mapping[str, Any]
    skips: tuple[Mapping[str, Any], ...]
    evaluations: tuple[Mapping[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "now_utc": self.now_utc.isoformat(),
            "n_candidates": len(self.candidates),
            "candidates": [
                {
                    "sleeve": c.sleeve, "symbol": c.symbol, "direction": c.direction,
                    "decision_day": c.decision_day, "stop_dist": c.stop_dist,
                    "target_dist": c.target_dist, "intra_size": c.intra_size,
                    "decision_bar_iso": c.decision_bar_iso, "timeframe": c.timeframe,
                }
                for c in self.candidates
            ],
            "telemetry": dict(self.telemetry),
            "skips": [dict(s) for s in self.skips],
            "evaluations": [dict(e) for e in self.evaluations],
        }


def _to_policy_candidate(intent: Any, meta: Mapping[str, Any]) -> PolicyCandidate:
    """Live ``TradeIntent`` + engine meta row -> ``PolicyCandidate``.

    The inverse of ``sleeve_book._to_trade_intent``.  ``decision_day`` is taken
    from the **intent**, not from ``meta``: for the 12 market-expansion sleeves
    the generator overrides the bar-derived day with the wall-clock one
    (``market_expansion_d1.py:217-221``), and the intent carries the value that
    actually reaches the correlated-unit bucket.  ``meta["decision_day"]`` keeps
    the bar-derived value, which is why both are preserved in ``features``.
    """

    # `vr` is here for the WAVE-11 vol-level sizing tilt and its ABSENCE was a latent defect
    # (Session AR, found by an adversarial pass over AR's own wiring). This is the INVERSE
    # adapter; `sleeve_book._to_trade_intent` is the forward one and already forwards any
    # `features` key naming a `TradeIntent` field. Omitting `vr` here meant the
    # LiveGeneration -> PolicyCandidate -> _to_trade_intent round trip rebuilt the intent with
    # `vr=None`, so in THAT lane `vol_level_tilt_for` returned 1.0 and the tilt was a silent
    # no-op EVEN WHEN ARMED -- while `SleeveBookPolicy.describe()["dial"]` reported it True.
    # That is the armed-but-inert failure class, which is the most expensive one here.
    # Adding it is harmless when the tilt is off: the field already exists, the generator
    # already computes it, and the `is not None` filter below drops it for every sleeve that
    # does not. Pinned by `test_ar_vol_level_tilt.py`'s round-trip test.
    feature_names = ("htf_slope_norm", "mom_20_atr", "fvg_freshness_bars",
                     "atr_ratio", "session_hour", "vr")
    features = {n: getattr(intent, n, None) for n in feature_names}
    features = {k: v for k, v in features.items() if v is not None}
    features["bar_decision_day"] = meta.get("decision_day")
    features["last_close"] = meta.get("last_close")
    return PolicyCandidate(
        sleeve=str(getattr(intent, "sleeve", "")),
        symbol=str(getattr(intent, "symbol", "")),
        direction=int(getattr(intent, "direction", 0) or 0),
        decision_day=str(getattr(intent, "decision_day", "")),
        stop_dist=float(getattr(intent, "stop_dist", 0.0) or 0.0),
        target_dist=getattr(intent, "target_dist", None),
        intra_size=float(getattr(intent, "intra_size", 1.0) or 1.0),
        decision_bar_iso=meta.get("decision_bar_iso"),
        timeframe=meta.get("timeframe"),
        ll_impulse=getattr(intent, "ll_impulse", None),
        decision_hour=getattr(intent, "decision_hour", None),
        vp_loc=getattr(intent, "vp_loc", None),
        features=features,
    )


class GenerationPort:
    """Drives the live generation loop over a ``BarSource``.

    Parameters
    ----------
    config:
        The ``gtos_vnext_runtime`` block — the same merged profile+base config
        the live engine receives (``run_book.py:180, 309``).  The include flags
        on it decide the active book, so a replay of the live window must use
        the flags the window actually ran under; ``packet_validation
        .config_from_bridge`` recovers them per cycle from the packets.
    bars:
        Any ``BarSource``.
    namespace / account / bar_count:
        Passed straight to the live engine.  ``bar_count`` is the engine default
        260 (``book_engine.py:75``); a registry ``bar_count`` below it is inert
        because the engine takes ``max()`` (``:462``).
    state_root:
        Where the engine's persisted state lives.  Defaults to a fresh temp
        directory so a replay can neither read nor write the live bar-time
        repair latch.  Pass the live repo root only to reproduce a latched run.
    """

    def __init__(self, config: Mapping[str, Any], bars: BarSource, *,
                 namespace: str = "replay", account: str = "A",
                 bar_count: int = 260, broker_symbol: Any = None,
                 state_root: Optional[str] = None) -> None:
        from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

        self._config = dict(config or {})
        self._bars = bars
        self._mt5 = ReplayMT5(bars)
        self._state_root = state_root or tempfile.mkdtemp(prefix="gtos_generation_replay_")
        self._engine = UltimateBookLiveEngine(
            self._config, self._mt5, self._state_root,
            namespace=namespace, account=account, bar_count=bar_count,
            broker_symbol=broker_symbol,
        )

    @property
    def engine(self) -> Any:
        return self._engine

    def active_sleeve_names(self) -> set:
        """The sleeves that will generate — the DF-1 active book
        (``book_engine.py:177-211``).  This is the *decision* registry, and it is
        what reconciles ``active_specs``' 32 specs to the live 29."""
        return self._engine._active_sleeve_names()

    def generate(self, now_utc: datetime, *, tags: Optional[Sequence[str]] = None
                 ) -> GenerationResult:
        """Run one live generation cycle at ``now_utc``.

        ``tags`` mirrors the live launcher: only sleeves whose timeframe advanced
        at this instant are evaluated (``launcher.py:259-267``).  ``None`` means
        "evaluate every active sleeve", which is what a bar-driven replay wants
        when it is stepping one timeframe at a time.
        """

        now = now_utc.astimezone(timezone.utc)
        self._mt5.set_now(now)
        before = len(self._mt5.calls)
        intents, meta = self._engine._generate_intents(tags, now)
        fetched = self._mt5.calls[before:]

        candidates = tuple(
            _to_policy_candidate(i, m) for i, m in zip(intents, meta)
        )
        return GenerationResult(
            now_utc=now,
            candidates=candidates,
            telemetry=dict(getattr(self._engine, "_last_generation_telemetry", {}) or {}),
            skips=tuple(dict(s) for s in
                        (getattr(self._engine, "_last_generation_skips", []) or [])),
            evaluations=tuple(
                {"symbol": s, "timeframe": tf, "bars_requested": n} for (s, tf, n) in fetched
            ),
        )

    def describe(self) -> Mapping[str, Any]:
        return {
            "schema": SCHEMA,
            "namespace": getattr(self._engine, "_namespace", None),
            "bars": dict(self._bars.describe()),
            "active_sleeves": sorted(self.active_sleeve_names()),
            "state_root": self._state_root,
        }


def bar_closes(start_utc: datetime, end_utc: datetime, timeframe: int) -> list[datetime]:
    """Every bar-close instant for ``timeframe`` in ``[start, end]``.

    A generation replay is driven at bar closes, because that is when the live
    launcher runs a cycle (``launcher.py:259-267``).  Evaluating between closes
    reproduces nothing live ever did and trips the engine's own staleness guard.
    """

    minutes = TF_MINUTES.get(int(timeframe))
    if not minutes:
        raise GenerationError(f"unknown timeframe: {timeframe!r}")
    step = timedelta(minutes=minutes)
    start = start_utc.astimezone(timezone.utc)
    end = end_utc.astimezone(timezone.utc)
    # align forward to the first bar close at or after `start`
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    n = -(-int((start - epoch).total_seconds()) // int(step.total_seconds()))
    out: list[datetime] = []
    cur = epoch + n * step
    while cur <= end:
        out.append(cur)
        cur += step
    return out
