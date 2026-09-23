"""Live-data seam: convert the live MT5 candle feed into CLOSED-bar `Bar` series the vendored
sleeve generators consume. The generators are leak-free (features from closed bars only), so this
provider DROPS the currently-forming bar by default.

MT5 candle dict shape (src/mt5/mt5_real.py:163-180): {"time": <UTC ISO>, "open","high","low",
"close","volume"} — broker epoch already normalized to UTC by the interface. We map open->o etc.
into primitives.Bar(o,h,l,c,v) and keep the parsed UTC datetimes aligned by index.

No order path. Reads only (mt5.get_candles). Warmup gates: a generator that lacks enough closed
bars emits NO intent (never a wrong one).
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Optional

from .primitives import Bar

_CHALLENGE_NS = "operator"

# MT5 timeframe constants (MetaTrader5 package values) — accept ints so we never import MT5 here.
TF_M1 = 1
TF_M15 = 15
TF_H1 = 16385
TF_H4 = 16388
TF_D1 = 16408

# Warmup minimums (closed bars) per the research generators (build-spec):
WARMUP = {
    "metals": 200,      # gold_sleeve_strategy:33 / csb:83 — >=200 closed H4
    "energy": 200,
    "crypto": 200,
    "index": 150,       # idxrev enters at i>=120 (latest closed bar) AND the route required len(B)>=150
    #                     data-completeness; gate at 150 so a thin index the route SKIPPED cannot fire live
    #                     (live indices return ~260 bars -> latent parity guard, not an active restriction).
    "substrate": 210,   # substrate.py:62 — >=210 closed H4
    "jpy": 100,         # fx_jpy/fx_jpy_ny — M15 session bars (i0>=20); 100 M15 is ample
    "volprofile": 200,  # vp_euidx_pocgrav — route _vp_pocgrav_rows guard len(B)>=200 closed H4
}


def _parse_time(t) -> Optional[datetime]:
    if isinstance(t, datetime):
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    if isinstance(t, str):
        try:
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    if isinstance(t, (int, float)):
        return datetime.fromtimestamp(t, tz=timezone.utc)
    return None


def _challenge(namespace: Optional[str]) -> bool:
    return str(namespace or "") == _CHALLENGE_NS


def _challenge_writer() -> bool:
    """This process is the Challenge book. A friend process is not."""
    import sys

    argv = " ".join(sys.argv).replace("\\", "/").lower()
    if "run_book" not in argv:
        return False
    if any(token in argv for token in ("friend_a", "redacted_account", "redacted_account", "redacted_account", "run_book_supervisor")):
        return False
    return _CHALLENGE_NS in argv


def _text(value: object) -> str:
    if value is None or isinstance(value, bool):
        return ""
    text = str(value).strip()
    return text


def _spot_id(symbol: object, timeframe: object, bar: object) -> str:
    """symbol|timeframe|bar. An absent field stays an empty slot, not a dropped one."""
    return f"{_text(symbol)}|{_text(timeframe)}|{_text(bar)}"


def _outer_locals() -> dict:
    """Locals of the first caller outside this module.

    The launcher clock holds the reference symbol in ``ref`` and the
    timeframe in ``tf``, and calls candles_to_bars without passing them.
    """
    import inspect

    frame = inspect.currentframe()
    try:
        current = frame
        while current is not None:
            current = current.f_back
            if current is None:
                return {}
            module = str(current.f_globals.get("__name__") or "")
            if module.endswith("bar_provider"):
                continue
            return dict(current.f_locals)
    finally:
        del frame
    return {}


def _resolved_names(
    symbol: object,
    timeframe: object,
    candles: Optional[list] = None,
) -> tuple[str, str]:
    found_symbol = _text(symbol)
    found_tf = _text(timeframe)
    for candle in candles or []:
        if not isinstance(candle, dict):
            continue
        if not found_symbol:
            found_symbol = _text(candle.get("symbol") or candle.get("broker_symbol"))
        if not found_tf:
            raw_tf = candle.get("timeframe")
            if raw_tf is None:
                raw_tf = candle.get("tf")
            found_tf = _text(raw_tf)
        if found_symbol and found_tf:
            return found_symbol, found_tf
    if found_symbol and found_tf:
        return found_symbol, found_tf
    local = _outer_locals()
    if not found_symbol:
        for key in ("symbol", "ref", "broker_sym"):
            found_symbol = _text(local.get(key))
            if found_symbol:
                break
    if not found_tf:
        spec = local.get("spec")
        if spec is not None:
            found_tf = _text(getattr(spec, "timeframe", None))
        if not found_tf:
            for key in ("timeframe", "tf"):
                found_tf = _text(local.get(key))
                if found_tf:
                    break
    return found_symbol, found_tf


def _resolved_bar(local: Optional[dict] = None) -> str:
    if local is None:
        local = _outer_locals()
    times = local.get("times")
    if isinstance(times, (list, tuple)) and times:
        last = times[-1]
        if hasattr(last, "isoformat"):
            return str(last.isoformat())
        return _text(last)
    return ""


def _ask(question: str, spot_id: str, facts: dict) -> Optional[str]:
    try:
        from src.judgment.pipeline_choices import spot

        return spot(question, spot=spot_id, facts=facts)
    except Exception:
        return None


def _read_candles(mt5, symbol: str, timeframe: int, count: int):
    try:
        candles = mt5.get_candles(symbol, timeframe, count)
    except Exception:
        return None
    if candles is None or isinstance(candles, (str, bytes)):
        return None
    try:
        return list(candles)
    except TypeError:
        return None


def candles_to_bars(candles: list[dict], *, drop_forming: bool = True,
                    now: Optional[datetime] = None,
                    interval_minutes: Optional[int] = None,
                    namespace: Optional[str] = None,
                    symbol: Optional[str] = None,
                    timeframe: Optional[object] = None,
                    ) -> tuple[list[Bar], list[datetime]]:
    """Map MT5 candle dicts -> (closed Bar list, aligned UTC datetimes). Drops the forming bar.

    `now` + `interval_minutes` — THE PRE-GAP BAR, and why the default is unchanged
    ---------------------------------------------------------------------------------
    Dropping the last candle unconditionally assumes the last candle is always forming.
    At a session close it is not: the market shuts, no new bar begins, and the last
    candle IS the freshly-closed decision bar. It is discarded — and by the time the next
    session's bar starts forming, that bar's close is more than two intervals old and
    `book_engine.py:512` refuses it as stale. **The last closed bar before every weekend
    and holiday is therefore unreachable by the live book.**

    Measured on the bar archive by `phase6/receipts/ab_port_parity.py`: 29 fires across
    five H4 sleeves, 29 of 29 immediately before a gap of >= 2 intervals, worth 1.3 % to
    6.8 % of each sleeve's trades — and 6.4 % on `sub_xvol_pullback`, whose gate failure
    is significance at n=88. `[MEASURED]` on the replay, `[UNVERIFIED]` on the live MT5
    feed, where whether a forming candle exists at a session close is a property of the
    terminal.

    Pass both and a last candle whose interval has already elapsed (`time + interval <=
    now`) is kept, because it is provably closed. Omit either and behaviour is byte-
    identical to before, so every existing caller and test is unaffected: this adds a
    capability and changes nothing until someone wires it. Wiring it changes which bars an
    armed book trades, which is an owner decision rather than a session's.
    """
    symbol_s, tf_s = _resolved_names(symbol, timeframe, candles)
    if not candles:
        if _challenge(namespace):
            # An empty pull used to return before any ask. The short side is
            # the withhold. Nothing here invents a candle.
            _ask(
                "raw_series",
                _spot_id(symbol_s, tf_s, ""),
                {
                    "symbol": symbol_s,
                    "timeframe": tf_s,
                    "got": 0,
                    "namespace": _CHALLENGE_NS,
                },
            )
        return [], []
    last_t = _parse_time(candles[-1].get("time")) if drop_forming else None
    keep_last = False
    if drop_forming and last_t is not None and now is not None and interval_minutes:
        ref = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
        keep_last = (last_t + timedelta(minutes=int(interval_minutes))) <= ref
    if not drop_forming:
        rows = list(candles)
    elif now is not None and interval_minutes:
        # This `now` is the card's clock. A candle whose close is after it
        # is forming. A later wall read is a different clock and does not
        # put that candle in the closed series, and it does not ask.
        rows = list(candles) if keep_last else candles[:-1]
    elif _challenge(namespace):
        # No cycle clock was passed. Ask even when the last time will not
        # parse. The candle stays out only when that side is the unique
        # highest. An empty answer, a tie, or an error does not drop it.
        bar_s = last_t.isoformat() if last_t else ""
        winner = _ask(
            "last_bar",
            _spot_id(symbol_s, tf_s, bar_s),
            {
                "symbol": symbol_s,
                "timeframe": tf_s,
                "bar": bar_s,
                "interval_elapsed": bool(keep_last),
                "interval_minutes": interval_minutes,
                "last_time": None if last_t is None else last_t.isoformat(),
                "namespace": _CHALLENGE_NS,
            },
        )
        rows = candles[:-1] if winner == "forming_bar_stays_out" else list(candles)
    elif last_t is None:
        rows = candles[:-1] if len(candles) >= 1 else []
    else:
        rows = candles[:-1] if not keep_last else list(candles)
    bars: list[Bar] = []
    times: list[datetime] = []
    for c in rows:
        try:
            o = float(c["open"]); h = float(c["high"]); l = float(c["low"]); cl = float(c["close"])
            v = float(c.get("volume", 0) or 0)
        except (KeyError, TypeError, ValueError):
            continue
        dt = _parse_time(c.get("time"))
        if dt is None:
            continue
        bars.append(Bar(o, h, l, cl, v))
        times.append(dt)
    return bars, times


def get_closed_bars(mt5, symbol: str, timeframe: int, count: int,
                    *, drop_forming: bool = True,
                    now: Optional[datetime] = None,
                    interval_minutes: Optional[int] = None,
                    namespace: Optional[str] = None,
                    forming_sink: list | None = None,
                    ) -> tuple[list[Bar], list[datetime]]:
    """Fetch `count` recent candles for symbol via the live mt5 interface and return closed Bars.
    Returns ([],[]) on any feed failure (caller treats as 'no data' -> emits no intent).

    `now` / `interval_minutes` are passed straight through to `candles_to_bars`; see its
    docstring for the pre-gap bar they recover and why the default is unchanged.

    On Challenge an unread or empty pull asks raw_series before it returns.
    series_reaches reads the feed once more. series_short does not. An empty
    answer does not invent a candle and does not restore a skip by itself.
    """
    candles = _read_candles(mt5, symbol, timeframe, count)
    if not candles and _challenge(namespace):
        winner = _ask(
            "raw_series",
            _spot_id(symbol, timeframe, ""),
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "requested": count,
                "got": 0 if candles is not None else None,
                "feed": "empty" if candles is not None else "unread",
                "namespace": _CHALLENGE_NS,
            },
        )
        if winner == "series_reaches":
            candles = _read_candles(mt5, symbol, timeframe, count)
    if not candles:
        return [], []
    bars, times = candles_to_bars(
        candles,
        drop_forming=drop_forming,
        now=now,
        interval_minutes=interval_minutes,
        namespace=namespace,
        symbol=symbol,
        timeframe=timeframe,
    )
    if forming_sink is not None:
        last = candles[-1]
        if isinstance(last, Mapping):
            last_t = _parse_time(last.get("time"))
            kept = times[-1] if times else None
            if last_t is not None and last_t != kept:
                forming_sink.append(last)
    return bars, times


def decision_day_of(dt: datetime) -> str:
    """Correlated-unit grouping key = the signal bar's UTC date (matches the locked book grouping)."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _named_count(value: object) -> Optional[int]:
    """A count a caller already read from a fact. A fraction is not a count."""

    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")) or not (number > 0):
        return None
    nearest = round(number)
    if nearest != number:
        return None
    return int(nearest)


def enough(
    bars: list[Bar],
    cluster: str,
    symbol: object = None,
    timeframe: object = None,
    bar: object = None,
    needed: object = None,
) -> bool:
    """Closed bars reach this cluster.

    The Challenge writer refuses only when a count named by the caller is
    larger than the series and closed_series_short is the unique highest.
    An empty answer does not refuse. A missing count does not refuse.
    Any other process keeps the friend map.
    """
    if not _challenge_writer():
        return len(bars) >= WARMUP.get(cluster, 200)
    needed_n = _named_count(needed)
    if needed_n is None or len(bars) >= needed_n:
        return True
    symbol_s = _text(symbol)
    tf_s = _text(timeframe)
    if hasattr(bar, "isoformat"):
        bar_s = bar.isoformat()
    else:
        bar_s = _text(bar)
    winner = _ask(
        "closed_series",
        _spot_id(symbol_s, tf_s, bar_s),
        {
            "symbol": symbol_s,
            "timeframe": tf_s,
            "bar": bar_s,
            "cluster": cluster,
            "bars_held": len(bars),
            "bars_needed": needed_n,
            "namespace": _CHALLENGE_NS,
        },
    )
    return winner != "closed_series_short"


def _last_bar_boot() -> None:
    """Stamp when the Challenge writer imports this file. Friends do not write it."""
    try:
        import json
        import os
        import sys
        from pathlib import Path

        argv = " ".join(sys.argv).replace("\\", "/").lower()
        if "--namespace operator" not in argv or "run_book" not in argv:
            return
        if any(tok in argv for tok in ("friend_a", "redacted_account", "redacted_account", "redacted_account", "run_book_supervisor")):
            return
        path = (
            Path(__file__).resolve().parents[3]
            / "pipeline_state"
            / "ultimate_book"
            / _CHALLENGE_NS
            / "judgment"
            / "last_bar_loaded.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema": "gtos.last_bar.loaded.v1",
                    "pid": os.getpid(),
                    "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "asks_when_time_missing": True,
                    "empty_drops_bar": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        return


_last_bar_boot()
