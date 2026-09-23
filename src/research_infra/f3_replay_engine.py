"""L58 — F3-replay engine ("Forward, Frozen, Faithful" replay).

This module ships the *seam* that lets future research tasks replay
historical CANDIDATEs through any evaluator — production primary
analyzer, mocked decision engine, or D.3 (Phase 3) tool-use-grounded
evaluator — without touching production code.

Why F3-replay
=============
Three properties define a replay that is safe to use as evidence:

  - **Forward** — the replay re-ingests the *same* market-state inputs
    that produced a historical decision and runs them forward through
    a configurable evaluator. The chronology of the replay matches the
    chronology of the live decisions: nothing in the replay can see a
    future candle.
  - **Frozen** — the replay does not mutate any historical artifact.
    Live evaluations and trade records are read-only inputs. The replay
    writes ONLY to the caller-supplied output directory; it never
    touches ``knowledge_base/``, ``shadow_logs/``, ``pipeline_state/``,
    or ``logs/``.
  - **Faithful** — when ``LiveReplayEvaluator`` is opted into (NOT in
    Wave 1), it calls the *real* ``primary_analyzer`` surface with the
    same system blocks + user message it would have built at decision
    time. ``RecordedReplayEvaluator`` is the deterministic ground-truth
    baseline; identical inputs produce identical outputs by construction.

What this is for
================
D.3 (Phase 3) plans to inject Anthropic tool-use scaffolding into the
live evaluation path. Before doing that to production, we need a replay
harness that can:

  1. Re-ingest a historical CAND's market_state inputs (raw_data, mso,
     candle_close_time, kill_zone, etc.).
  2. Pass them through a configurable evaluator (live primary_analyzer,
     a tool-use-augmented variant, or a mock).
  3. Compare outputs side-by-side.
  4. Join to realized R.

This module ships the seam; D.3 (Phase 3) adds the tool-use evaluator
that subclasses :class:`ReplayEvaluator`.

Walk-level vs realized-R discipline
===================================
Memory ``feedback_walk_level_evidence_not_predictive.md``: replay
outputs are walk-level. CR rate, decision-flip rate, and side-agreement
rate are walk-level metrics that REVERSED on Track A's
touch-count-decay study under realized-R join. The harness MUST emit
realized-R when available so downstream analysis can join it; the
harness itself does not promote a walk-level pattern to evidence.

Out of scope
============
- Modifying ``src/components/primary_analyzer.py`` or any other
  production module.
- Calling the real Anthropic API by default. ``LiveReplayEvaluator``
  is gated behind ``GTOS_F3_REPLAY_ALLOW_LIVE=1`` and CEO authorization;
  Wave 1 ships the seam only.
- Wiring D.3 tool-use grounding. That belongs to Phase 3.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Iterator,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    runtime_checkable,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project-root resolution + default paths
# ---------------------------------------------------------------------------

# src/research_infra/f3_replay_engine.py → project root is parents[2]
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

#: Default location of historical live evaluation JSONL files.
#: Layout: ``knowledge_base/live_evaluations/{INSTRUMENT}/YYYY-MM-DD.jsonl``.
DEFAULT_EVAL_DIR: Path = PROJECT_ROOT / "knowledge_base" / "live_evaluations"

#: Default location of trade records (filled CANDIDATEs only).
#: Layout: ``knowledge_base/trade_records/{INSTRUMENT}/<trade_id>.json``.
DEFAULT_TRADE_RECORDS_DIR: Path = (
    PROJECT_ROOT / "knowledge_base" / "trade_records"
)

#: Harness version embedded in run_metadata.json. Bump when the engine
#: contract changes (e.g. new field on HistoricalCandidate, new evaluator
#: name in BUILTIN_EVALUATORS, callback signature change).
HARNESS_VERSION: str = "L58-v1"


# ---------------------------------------------------------------------------
# HistoricalCandidate
# ---------------------------------------------------------------------------


@dataclass
class HistoricalCandidate:
    """A single historical evaluation record.

    Attributes
    ----------
    cand_id:
        Stable identifier derived from ``(symbol, candle_close_time)``.
        Format: ``"{SYMBOL}|{ISO8601_UTC_MINUTE}"`` so two CANDIDATEs on
        the same candle but different instruments are distinct, and
        microsecond drift in source timestamps does not change the id.
    symbol:
        Upper-cased instrument name, e.g. ``"XAUUSD"``, ``"USDJPY"``,
        ``"US30_cash"`` (the trade-records dir uses the latter casing).
    candle_close_time:
        Timezone-aware UTC ``datetime`` of the M15 candle close. The
        loader normalizes input timestamps (strings with microseconds,
        naive UTC, ``Z`` suffix, etc.) to whole-minute UTC.
    kill_zone:
        ``"london"``, ``"ny"``, ``"tokyo"`` or ``""`` if not recorded.
    raw_data:
        The richest available context block:

          - if loaded from a trade record: the full record (which
            contains the captured ``mso``, ``prompt``,
            ``ai_response``, ``trade_parameters``, etc.),
          - if loaded from a live_evaluations row: the decision record
            (which contains the AI's compressed decision fields but
            NOT the full MSO — live evaluation files are
            decision-summary-only).

        Mocked / RecordedReplayEvaluator do not need full MSO.
        LiveReplayEvaluator (Phase 3) re-derives what it needs from
        ``raw_data`` and is responsible for failing closed when the
        record lacks the keys it requires. The engine itself does NOT
        validate raw_data shape — that is the evaluator's job.
    framework_used:
        Framework string from the source record. ``"ob_retest"``,
        ``"fvg_fill"``, ``"breaker_re_entry"``, ``"none"`` (NO_TRADE),
        or ``""`` if not recorded.
    decision_recorded:
        The original AI decision dict — what
        ``RecordedReplayEvaluator`` returns verbatim. At minimum this
        carries ``decision`` + ``side`` (when CANDIDATE). Other fields
        (confidence, rationale snippets, framework, kill_zone) are
        passed through if present in the source record.
    realized_r:
        Joined realized R-multiple, populated post-load when
        ``trade_records_dir`` is supplied to
        :func:`load_historical_candidates`. ``None`` if no matching
        trade record was found (e.g. NO_TRADE evaluations, or
        CANDIDATEs that did not fill).
    """

    cand_id: str
    symbol: str
    candle_close_time: dt.datetime
    kill_zone: str
    raw_data: Mapping[str, Any]
    framework_used: str
    decision_recorded: Mapping[str, Any]
    realized_r: Optional[float] = None


# ---------------------------------------------------------------------------
# Time normalization (mirrors L56 join contract)
# ---------------------------------------------------------------------------


def _normalize_to_utc_minute(ts: Any) -> Optional[dt.datetime]:
    """Normalize a timestamp to a timezone-aware UTC ``datetime`` rounded
    to the whole minute.

    Accepts:
      * an ISO-8601 string (with or without microseconds, with or
        without timezone offset, ``Z`` suffix tolerated),
      * a ``datetime.datetime`` (naive treated as UTC),
      * ``None`` / ``""`` → returns ``None``.

    Returns ``None`` for unparseable inputs. The candle-close convention
    in this codebase is minute-aligned, so seconds + microseconds are
    truncated to make the join key stable. This matches L56's
    ``_normalize_candle_time`` contract so realized-R indices built by
    L56 helpers remain compatible with this loader.
    """
    if ts is None:
        return None
    if isinstance(ts, dt.datetime):
        parsed = ts
    else:
        s = str(ts).strip()
        if not s:
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            parsed = dt.datetime.fromisoformat(s)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    parsed = parsed.astimezone(dt.timezone.utc)
    return parsed.replace(second=0, microsecond=0)


def _make_cand_id(symbol: str, candle_close_time: dt.datetime) -> str:
    """Build the stable ``cand_id`` from ``(symbol, candle_close_time)``."""
    return f"{symbol.upper()}|{candle_close_time.isoformat()}"


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _iter_eval_files(
    eval_dir: Path, instruments: Optional[Sequence[str]]
) -> Iterator[Path]:
    """Yield every ``*.jsonl`` file under ``eval_dir/{INSTRUMENT}/`` that
    matches the (optional) instrument filter. Sorted for determinism.

    The filter is upper-case-insensitive and matches against the
    directory name (e.g. ``"XAUUSD"``, ``"US30_cash"``). Unknown
    instruments produce no files (silent — the caller may have
    intentionally narrowed to a smaller set).
    """
    if not eval_dir.exists():
        return
    inst_filter: Optional[set[str]] = None
    if instruments:
        inst_filter = {i.upper() for i in instruments}
    for inst_dir in sorted(eval_dir.iterdir()):
        if not inst_dir.is_dir():
            continue
        if inst_filter is not None and inst_dir.name.upper() not in inst_filter:
            continue
        for path in sorted(inst_dir.glob("*.jsonl")):
            yield path


def _parse_eval_row(
    row: Mapping[str, Any], inst_dir_name: str, source_path: Path
) -> Optional[HistoricalCandidate]:
    """Parse one JSONL row from ``live_evaluations/`` into a
    :class:`HistoricalCandidate`. Returns ``None`` if mandatory fields
    are missing or unparseable.

    Mandatory fields (a row missing any of these is dropped with a
    warning, NOT a hard error — historical files predate the current
    schema):

      * ``candle_time`` (or ``candle_close_time``)
      * ``symbol`` (falls back to the instrument directory name)
    """
    # candle close time — accept either field name
    raw_ts = row.get("candle_time") or row.get("candle_close_time")
    candle_close_time = _normalize_to_utc_minute(raw_ts)
    if candle_close_time is None:
        logger.warning(
            "Dropping eval row in %s: unparseable candle_time=%r",
            source_path,
            raw_ts,
        )
        return None
    symbol = (row.get("symbol") or inst_dir_name or "").strip()
    if not symbol:
        logger.warning(
            "Dropping eval row in %s: missing symbol", source_path
        )
        return None
    symbol = symbol.upper()
    decision = row.get("decision") or ""
    framework = row.get("framework") or ""
    kill_zone = row.get("kill_zone") or ""
    # decision_recorded is the compressed live-evaluation row itself —
    # callers (RecordedReplayEvaluator) read decision + side from it.
    side: Optional[str] = None
    # Some rows store side under ``trade_parameters.direction`` (trade
    # records) or ``ai_response.trade_parameters.direction``; live
    # evaluations are decision-only and don't carry side. Best-effort.
    if isinstance(row.get("trade_parameters"), Mapping):
        side = row["trade_parameters"].get("direction")
    if side is None and isinstance(row.get("ai_response"), Mapping):
        ar = row["ai_response"]
        if isinstance(ar.get("trade_parameters"), Mapping):
            side = ar["trade_parameters"].get("direction")
    decision_recorded: dict[str, Any] = {
        "decision": decision,
        "side": side,
        "framework": framework,
        "kill_zone": kill_zone,
        # Pass-through summary fields used by ranking / diff tools.
        "confidence_score": row.get("confidence_score"),
        "setup_grade": row.get("setup_grade"),
        "no_trade_reason": row.get("no_trade_reason"),
        "wait_reason": row.get("wait_reason"),
        "overall_reasoning": row.get("overall_reasoning"),
    }
    return HistoricalCandidate(
        cand_id=_make_cand_id(symbol, candle_close_time),
        symbol=symbol,
        candle_close_time=candle_close_time,
        kill_zone=kill_zone,
        raw_data=dict(row),  # full source row stays accessible
        framework_used=framework,
        decision_recorded=decision_recorded,
    )


def _iter_trade_records(
    trade_records_dir: Path, instruments: Optional[Sequence[str]]
) -> Iterator[tuple[Path, Mapping[str, Any]]]:
    """Yield ``(path, record_dict)`` for every trade record JSON under
    ``trade_records_dir/{INSTRUMENT}/``. Sorted for determinism. Skips
    ``_pending_records_index.json`` and any unreadable file with a
    warning.
    """
    if not trade_records_dir.exists():
        return
    inst_filter: Optional[set[str]] = None
    if instruments:
        inst_filter = {i.upper() for i in instruments}
    for inst_dir in sorted(trade_records_dir.iterdir()):
        if not inst_dir.is_dir():
            continue
        if inst_filter is not None and inst_dir.name.upper() not in inst_filter:
            continue
        for path in sorted(inst_dir.glob("*.json")):
            if path.stem.startswith("_"):  # _pending_records_index etc.
                continue
            try:
                with path.open("r", encoding="utf-8") as fh:
                    rec = json.load(fh)
            except Exception as exc:
                logger.warning("Skipping unreadable trade record %s: %s",
                               path, exc)
                continue
            yield path, rec


def _extract_realized_r_from_trade_record(
    rec: Mapping[str, Any],
) -> Optional[float]:
    """Best-effort extraction of realized R from a trade record.

    Trade records evolved across versions; this checks the locations
    used in 2026-Q1+:

      1. ``decision_pipeline.outcome.r_multiple``
      2. ``exit.r_multiple`` (when ``exit`` is a dict)
      3. top-level ``r_multiple`` (rare, T7-sim-style flat shape)

    Returns ``None`` if no usable value is found.
    """
    pipeline = rec.get("decision_pipeline") or {}
    if isinstance(pipeline, Mapping):
        outcome = pipeline.get("outcome")
        if isinstance(outcome, Mapping):
            r = outcome.get("r_multiple")
            if isinstance(r, (int, float)):
                return float(r)
    exit_block = rec.get("exit")
    if isinstance(exit_block, Mapping):
        r = exit_block.get("r_multiple")
        if isinstance(r, (int, float)):
            return float(r)
    r = rec.get("r_multiple")
    if isinstance(r, (int, float)):
        return float(r)
    return None


def _build_realized_r_index(
    trade_records_dir: Path, instruments: Optional[Sequence[str]]
) -> dict[tuple[str, dt.datetime, Optional[str]], float]:
    """Build the realized-R join index from a trade-records directory.

    Key shape: ``(SYMBOL, candle_close_time_minute_utc, side_or_None)``.
    The keyed-with-side entry plus a side-less fallback (``None``) are
    both written so direction-mismatched lookups succeed when the trade
    record only has one side recorded. This matches L56's join contract
    (memory ``project_research_program_phase1_kickoff_2026-04-26.md``).
    """
    index: dict[tuple[str, dt.datetime, Optional[str]], float] = {}
    for path, rec in _iter_trade_records(trade_records_dir, instruments):
        meta = rec.get("metadata") or {}
        symbol = (meta.get("symbol") or path.parent.name or "").strip().upper()
        ts = _normalize_to_utc_minute(meta.get("candle_time"))
        if not symbol or ts is None:
            continue
        pipeline = rec.get("decision_pipeline") or {}
        side = None
        if isinstance(pipeline, Mapping):
            side = pipeline.get("ai_direction")
        # Fall back to trade_parameters.direction if pipeline didn't have it
        if side is None:
            tp = rec.get("trade_parameters") or {}
            if isinstance(tp, Mapping):
                side = tp.get("direction")
        r = _extract_realized_r_from_trade_record(rec)
        if r is None:
            continue
        index[(symbol, ts, side)] = r
        # side-less fallback
        index[(symbol, ts, None)] = r
    logger.info(
        "Built realized-R index: %d keys from %s",
        len(index),
        trade_records_dir,
    )
    return index


def _join_realized_r(
    cand: HistoricalCandidate,
    index: Mapping[tuple[str, dt.datetime, Optional[str]], float],
) -> Optional[float]:
    """Look up realized R for a candidate via (symbol, candle_close_time,
    side) → side-less fallback. Returns ``None`` on miss."""
    side = cand.decision_recorded.get("side")
    direct = index.get((cand.symbol, cand.candle_close_time, side))
    if direct is not None:
        return direct
    return index.get((cand.symbol, cand.candle_close_time, None))


def load_historical_candidates(
    eval_dir: Path = DEFAULT_EVAL_DIR,
    trade_records_dir: Optional[Path] = None,
    since: Optional[dt.datetime] = None,
    until: Optional[dt.datetime] = None,
    instruments: Optional[List[str]] = None,
) -> List[HistoricalCandidate]:
    """Load historical CANDIDATE records from ``eval_dir``, optionally
    joining realized R from ``trade_records_dir``.

    Parameters
    ----------
    eval_dir:
        Directory with the ``{INSTRUMENT}/YYYY-MM-DD.jsonl`` layout used
        by the orchestrator's evaluation logger. Defaults to
        ``knowledge_base/live_evaluations/`` under the project root.
    trade_records_dir:
        Optional directory with ``{INSTRUMENT}/<trade_id>.json`` trade
        records. When provided, ``realized_r`` is populated on every
        candidate that joins to a record under L56's join contract
        ``(symbol, candle_close_time, side)`` with a side-less fallback.
        Pass ``None`` (default) to skip the join — useful when running
        replays whose evaluators do not depend on realized R.
    since:
        Inclusive lower bound on ``candle_close_time``. ``None`` =
        no lower bound. Naive datetimes are interpreted as UTC.
    until:
        Inclusive upper bound on ``candle_close_time``. ``None`` =
        no upper bound. Naive datetimes are interpreted as UTC.
    instruments:
        Optional list of instrument directory names. Filtering is
        case-insensitive and matches against the directory name (so
        ``"us30_cash"`` and ``"US30_cash"`` are equivalent). ``None``
        loads every instrument under ``eval_dir``.

    Returns
    -------
    list[HistoricalCandidate]
        Sorted by ``(candle_close_time, symbol)`` for deterministic
        downstream processing. Order is the SAME on every load given
        the same inputs.

    Determinism contract
    --------------------
    The loader is deterministic: identical ``eval_dir`` contents +
    identical filter args produce identical output (same ordering,
    same parsed candidates, same realized-R values). Two consecutive
    calls in a single process MUST return equal lists. This property
    is what lets :class:`ReplayRun` produce a stable ``replay_results.jsonl``
    across re-runs.
    """
    # Normalize bounds
    lo = _normalize_to_utc_minute(since) if since is not None else None
    hi = _normalize_to_utc_minute(until) if until is not None else None

    realized_r_index: Mapping[
        tuple[str, dt.datetime, Optional[str]], float
    ] = {}
    if trade_records_dir is not None:
        realized_r_index = _build_realized_r_index(
            Path(trade_records_dir), instruments
        )

    candidates: list[HistoricalCandidate] = []
    for path in _iter_eval_files(Path(eval_dir), instruments):
        inst_dir_name = path.parent.name
        try:
            with path.open("r", encoding="utf-8") as fh:
                for line_no, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        logger.warning(
                            "Malformed JSON in %s:%d: %s",
                            path,
                            line_no,
                            exc,
                        )
                        continue
                    if not isinstance(row, Mapping):
                        continue
                    cand = _parse_eval_row(row, inst_dir_name, path)
                    if cand is None:
                        continue
                    if lo is not None and cand.candle_close_time < lo:
                        continue
                    if hi is not None and cand.candle_close_time > hi:
                        continue
                    if realized_r_index:
                        cand.realized_r = _join_realized_r(
                            cand, realized_r_index
                        )
                    candidates.append(cand)
        except OSError as exc:
            logger.warning("Could not read eval file %s: %s", path, exc)
            continue

    candidates.sort(key=lambda c: (c.candle_close_time, c.symbol))
    logger.info(
        "Loaded %d historical candidates from %s (realized-R: %d joined)",
        len(candidates),
        eval_dir,
        sum(1 for c in candidates if c.realized_r is not None),
    )
    return candidates


# ---------------------------------------------------------------------------
# ReplayDecision + ReplayEvaluator protocol + concrete subclasses
# ---------------------------------------------------------------------------


@dataclass
class ReplayDecision:
    """The result of one evaluator's pass over one candidate.

    Attributes
    ----------
    decision:
        ``"CANDIDATE"`` or ``"NO_TRADE"`` (or ``"MALFORMED"`` if the
        evaluator could not produce a parseable answer).
    side:
        ``"LONG"``, ``"SHORT"``, or ``None`` (NO_TRADE / unparseable).
    raw_response:
        Evaluator-defined free-form payload. Mocked evaluator returns
        a JSON string; the live evaluator (Phase 3) returns the API
        response text.
    evaluator_id:
        Stable string identifying the evaluator (e.g.
        ``"recorded"``, ``"mock_seed_42"``). Used for join keys in
        ``replay_results.jsonl``.
    error:
        Optional error message; ``None`` on success.
    """

    decision: str
    side: Optional[str]
    raw_response: str
    evaluator_id: str
    error: Optional[str] = None


@runtime_checkable
class ReplayEvaluator(Protocol):
    """Protocol for replay evaluators.

    A replay evaluator takes a :class:`HistoricalCandidate` and returns
    a :class:`ReplayDecision`. The protocol is the seam D.3 (Phase 3)
    will plug a tool-use-grounded evaluator into.

    Contract
    --------
    * Evaluators MUST be deterministic when their configuration is
      fixed. ``RecordedReplayEvaluator`` is deterministic by
      construction. ``MockReplayEvaluator(seed=N)`` is deterministic
      for a given ``N``. ``LiveReplayEvaluator`` (Phase 3) is NOT
      bit-deterministic because Anthropic ``effort=max`` is non-seeded —
      this is documented at the call site.
    * Evaluators MUST NOT mutate the candidate. Inputs are read-only.
    * Evaluators MUST NOT write to ``knowledge_base/``,
      ``shadow_logs/``, ``pipeline_state/``, ``logs/``, or any other
      production path. Writing belongs to :class:`ReplayRun` and only
      to the caller-supplied output directory.
    """

    @property
    def evaluator_id(self) -> str:  # pragma: no cover — Protocol
        ...

    def evaluate(
        self, candidate: HistoricalCandidate
    ) -> ReplayDecision:  # pragma: no cover — Protocol
        ...


class RecordedReplayEvaluator:
    """Returns the historical decision verbatim.

    Useful as a baseline: pairing ``RecordedReplayEvaluator`` against
    itself MUST produce zero divergence. Pairing it against a live or
    mock evaluator gives the divergence rate of the experimental
    evaluator vs the historical truth.
    """

    def __init__(self) -> None:
        self._evaluator_id = "recorded"

    @property
    def evaluator_id(self) -> str:
        return self._evaluator_id

    def evaluate(self, candidate: HistoricalCandidate) -> ReplayDecision:
        rec = candidate.decision_recorded
        decision = rec.get("decision") or "NO_TRADE"
        side = rec.get("side")
        return ReplayDecision(
            decision=decision,
            side=side,
            raw_response=json.dumps(dict(rec), default=str),
            evaluator_id=self._evaluator_id,
        )


class MockReplayEvaluator:
    """Deterministic mock evaluator.

    Hashes ``(seed, candidate.cand_id)`` to derive a stable
    pseudo-random outcome. Two evaluators with the same seed MUST
    produce identical outputs. Two evaluators with different seeds
    typically diverge on a non-trivial fraction of candidates — this
    is what makes the harness exercise the divergence-tracking code
    path without any real API call.
    """

    def __init__(self, seed: int = 1) -> None:
        self.seed = int(seed)
        self._evaluator_id = f"mock_seed_{self.seed}"

    @property
    def evaluator_id(self) -> str:
        return self._evaluator_id

    def evaluate(self, candidate: HistoricalCandidate) -> ReplayDecision:
        seed_material = f"{self.seed}|{candidate.cand_id}"
        h = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
        bucket = int(h[:8], 16)
        # ~60% CANDIDATE — matches batch CR distribution roughly.
        decision = "CANDIDATE" if (bucket % 100) < 60 else "NO_TRADE"
        side: Optional[str] = None
        if decision == "CANDIDATE":
            side_bit = int(h[8:16], 16) % 2
            side = "LONG" if side_bit == 0 else "SHORT"
        raw = json.dumps(
            {
                "decision": decision,
                "side": side,
                "_mock_seed": self.seed,
                "_cand_id": candidate.cand_id,
            }
        )
        return ReplayDecision(
            decision=decision,
            side=side,
            raw_response=raw,
            evaluator_id=self._evaluator_id,
        )


class LiveReplayEvaluator:
    """Calls the *real* primary_analyzer surface.

    NOT exercised in Wave 1. Construction raises
    ``RuntimeError`` unless the environment variable
    ``GTOS_F3_REPLAY_ALLOW_LIVE=1`` is set AND the caller has wired the
    appropriate Anthropic client. The check exists to make accidental
    invocation impossible during research builds — the L58 brief
    explicitly defers Live to Phase 3.

    Phase 3 D.3 will subclass this class (or re-implement the same
    Protocol) to inject Anthropic tool-use scaffolding without modifying
    ``src/components/primary_analyzer.py``. The L58 seam is what makes
    that injection a one-file change in research.
    """

    _ALLOW_ENV: str = "GTOS_F3_REPLAY_ALLOW_LIVE"

    def __init__(self, client: Any = None) -> None:
        if os.environ.get(self._ALLOW_ENV) != "1":
            raise RuntimeError(
                "LiveReplayEvaluator is gated. To opt in, set "
                f"{self._ALLOW_ENV}=1 AND pass a configured Anthropic "
                "client. NOT exercised in Wave 1."
            )
        if client is None:
            raise RuntimeError(
                "LiveReplayEvaluator requires a configured Anthropic "
                "client; got None."
            )
        self._client = client
        self._evaluator_id = "live"

    @property
    def evaluator_id(self) -> str:
        return self._evaluator_id

    def evaluate(
        self, candidate: HistoricalCandidate
    ) -> ReplayDecision:  # pragma: no cover — Phase 3
        # Intentionally not implemented in Wave 1. Phase 3 D.3 will fill
        # this in by subclassing or reimplementing on top of the
        # primary_analyzer call surface in
        # ``src/components/primary_analyzer.py:217-237`` (mirrors the
        # L56 ``_real_api_decision`` shape so a future T0.1 batch
        # wrapper can drop in cleanly).
        raise NotImplementedError(
            "LiveReplayEvaluator is a Phase 3 deliverable; not "
            "implemented in Wave 1."
        )


# ---------------------------------------------------------------------------
# ReplayRun + hookable callbacks
# ---------------------------------------------------------------------------


#: Type alias for ``before_evaluate`` / ``after_evaluate`` callbacks.
#: Receives the candidate, the evaluator (A or B), and a
#: dict-of-anything ``context`` callbacks may mutate / read across
#: hook calls. The return value is ignored — callbacks communicate
#: via the context dict (D.3 will use it to record tool-use traces).
ReplayHook = Callable[
    [HistoricalCandidate, ReplayEvaluator, dict],
    None,
]


@dataclass
class ReplayRunMetrics:
    """Summary metrics aggregated by :class:`ReplayRun`.

    All metrics here are **walk-level** (CR rate, side disagreement,
    decision-flip rate). Per memory
    ``feedback_walk_level_evidence_not_predictive.md``, they are NOT
    sufficient as evidence on their own. The realized-R fields make
    realized-R metrics computable downstream, but the run itself does
    NOT perform the realized-R hypothesis test — that belongs to the
    consumer (e.g. ``compute_metrics`` in L56).
    """

    n_candidates: int = 0
    n_a_candidate: int = 0
    n_a_no_trade: int = 0
    n_b_candidate: int = 0
    n_b_no_trade: int = 0
    n_decision_diff: int = 0  # A.decision != B.decision
    n_side_diff_when_both_cand: int = 0  # both CAND, sides disagree
    n_with_realized_r: int = 0
    sum_realized_r_when_a_cand: float = 0.0
    sum_realized_r_when_b_cand: float = 0.0


@dataclass
class ReplayRun:
    """Pair two evaluators across a candidate set, emit results +
    summary.

    Parameters
    ----------
    candidates:
        Sequence of :class:`HistoricalCandidate` from
        :func:`load_historical_candidates`. Order is preserved in the
        output JSONL.
    evaluator_a:
        First evaluator (Protocol :class:`ReplayEvaluator`).
    evaluator_b:
        Second evaluator (Protocol :class:`ReplayEvaluator`). Pairing
        a single evaluator against itself is supported; expect
        ``n_decision_diff == 0``.
    output_dir:
        Directory where ``replay_results.jsonl``, ``replay_summary.md``,
        and ``run_metadata.json`` are written. Created if missing. The
        run REFUSES to point at any prefix under
        ``knowledge_base/``, ``shadow_logs/``, ``pipeline_state/``,
        or ``logs/`` — see :func:`_validate_output_dir`.
    run_tag:
        Free-form label embedded in ``run_metadata.json``. Convention:
        ``"phase1_<task_id>"`` to match :class:`CostTracker`.
    before_evaluate:
        Optional hook fired BEFORE each evaluator pass. Signature:
        ``(candidate, evaluator, context_dict) -> None``. Called twice
        per candidate (once per evaluator). The context dict persists
        for the lifetime of the run and is the reserved channel for
        D.3 tool-use observation.
    after_evaluate:
        Optional hook fired AFTER each evaluator pass with the same
        signature plus the produced :class:`ReplayDecision` injected
        into the context as ``context["last_decision"]``.

    Hookable contract
    -----------------
    The hook signature is INTENTIONALLY narrow: ``(candidate,
    evaluator, context)``. Hooks are NOT permitted to:

      * mutate the candidate (Frozen),
      * call the API directly (each evaluator owns its own API
        budget),
      * write to disk outside the run's output_dir.

    D.3 (Phase 3) will use ``context`` to record tool-use trace
    fragments and assemble them post-run; the engine itself never
    inspects the context dict.
    """

    candidates: Sequence[HistoricalCandidate]
    evaluator_a: ReplayEvaluator
    evaluator_b: ReplayEvaluator
    output_dir: Path
    run_tag: str
    before_evaluate: Optional[ReplayHook] = None
    after_evaluate: Optional[ReplayHook] = None
    _context: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Coerce path-like to Path; defer existence check to run().
        self.output_dir = Path(self.output_dir)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_output_dir(out: Path) -> None:
        """Refuse to write into protected production paths.

        Engineered systemic protection (memory
        ``feedback_engineer_systemic_not_patches.md``): any caller-
        supplied output_dir that resolves under
        ``knowledge_base/``, ``shadow_logs/``, ``pipeline_state/``, or
        ``logs/`` is rejected. The caller may write to
        ``research/<task_id>/`` or to ``tmp_path``.
        """
        try:
            resolved = out.resolve()
        except OSError:
            resolved = out
        # Compare against project-root-relative protected prefixes.
        try:
            rel = resolved.relative_to(PROJECT_ROOT)
        except ValueError:
            # Not under project root (e.g. tmp_path on Windows lives
            # under AppData) — outside our jurisdiction, allow.
            return
        first_part = rel.parts[0] if rel.parts else ""
        protected = {
            "knowledge_base",
            "shadow_logs",
            "pipeline_state",
            "logs",
        }
        if first_part in protected:
            raise ValueError(
                f"Refusing to write replay artifacts under protected path "
                f"{first_part!r}: {out}. Use a research/<task_id>/ output "
                f"directory or pass tmp_path in tests."
            )

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> ReplayRunMetrics:
        """Execute the paired replay.

        Side effects (only):

          * mkdir ``output_dir`` (and parents) if missing,
          * write ``replay_results.jsonl`` (one row per candidate),
          * write ``replay_summary.md``,
          * write ``run_metadata.json``.

        Returns the aggregated :class:`ReplayRunMetrics`.
        """
        self._validate_output_dir(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        results_path = self.output_dir / "replay_results.jsonl"
        summary_path = self.output_dir / "replay_summary.md"
        metadata_path = self.output_dir / "run_metadata.json"

        metrics = ReplayRunMetrics()
        rows: list[dict[str, Any]] = []

        for cand in self.candidates:
            metrics.n_candidates += 1

            # Evaluator A pass
            self._fire_hook(self.before_evaluate, cand, self.evaluator_a)
            dec_a = self.evaluator_a.evaluate(cand)
            self._context["last_decision"] = dec_a
            self._fire_hook(self.after_evaluate, cand, self.evaluator_a)

            # Evaluator B pass
            self._fire_hook(self.before_evaluate, cand, self.evaluator_b)
            dec_b = self.evaluator_b.evaluate(cand)
            self._context["last_decision"] = dec_b
            self._fire_hook(self.after_evaluate, cand, self.evaluator_b)

            # Aggregates
            if dec_a.decision == "CANDIDATE":
                metrics.n_a_candidate += 1
            elif dec_a.decision == "NO_TRADE":
                metrics.n_a_no_trade += 1
            if dec_b.decision == "CANDIDATE":
                metrics.n_b_candidate += 1
            elif dec_b.decision == "NO_TRADE":
                metrics.n_b_no_trade += 1
            if dec_a.decision != dec_b.decision:
                metrics.n_decision_diff += 1
            elif (
                dec_a.decision == "CANDIDATE"
                and dec_b.decision == "CANDIDATE"
                and dec_a.side != dec_b.side
            ):
                metrics.n_side_diff_when_both_cand += 1
            if cand.realized_r is not None:
                metrics.n_with_realized_r += 1
                if dec_a.decision == "CANDIDATE":
                    metrics.sum_realized_r_when_a_cand += cand.realized_r
                if dec_b.decision == "CANDIDATE":
                    metrics.sum_realized_r_when_b_cand += cand.realized_r

            rows.append(
                {
                    "cand_id": cand.cand_id,
                    "symbol": cand.symbol,
                    "candle_close_time": cand.candle_close_time.isoformat(),
                    "kill_zone": cand.kill_zone,
                    "framework_recorded": cand.framework_used,
                    "realized_r": cand.realized_r,
                    "evaluator_a": {
                        "id": dec_a.evaluator_id,
                        "decision": dec_a.decision,
                        "side": dec_a.side,
                        "error": dec_a.error,
                    },
                    "evaluator_b": {
                        "id": dec_b.evaluator_id,
                        "decision": dec_b.decision,
                        "side": dec_b.side,
                        "error": dec_b.error,
                    },
                }
            )

        # Write outputs
        with results_path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, default=str) + "\n")

        summary_path.write_text(
            self._render_summary(metrics), encoding="utf-8"
        )
        metadata_path.write_text(
            json.dumps(self._render_metadata(metrics), indent=2,
                       default=str),
            encoding="utf-8",
        )
        logger.info(
            "ReplayRun done: %d candidates, %d decision diffs, "
            "wrote %s",
            metrics.n_candidates,
            metrics.n_decision_diff,
            self.output_dir,
        )
        return metrics

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fire_hook(
        self,
        hook: Optional[ReplayHook],
        cand: HistoricalCandidate,
        evaluator: ReplayEvaluator,
    ) -> None:
        if hook is None:
            return
        try:
            hook(cand, evaluator, self._context)
        except Exception as exc:  # pragma: no cover — error path
            logger.warning(
                "Replay hook raised %s on cand_id=%s — continuing.",
                exc,
                cand.cand_id,
            )

    def _render_summary(self, metrics: ReplayRunMetrics) -> str:
        a_id = self.evaluator_a.evaluator_id
        b_id = self.evaluator_b.evaluator_id
        n = metrics.n_candidates
        cr_a = (metrics.n_a_candidate / n) if n else 0.0
        cr_b = (metrics.n_b_candidate / n) if n else 0.0
        diff_rate = (metrics.n_decision_diff / n) if n else 0.0
        lines = [
            f"# F3 Replay Summary — `{self.run_tag}`",
            "",
            f"- Harness: `{HARNESS_VERSION}`",
            f"- Evaluator A: `{a_id}`",
            f"- Evaluator B: `{b_id}`",
            f"- Candidates: **{n}**",
            f"- Decision diffs: **{metrics.n_decision_diff}** "
            f"({diff_rate:.1%})",
            f"- Side diffs (both CAND): **{metrics.n_side_diff_when_both_cand}**",
            f"- Realized-R join hits: **{metrics.n_with_realized_r}**",
            "",
            "## Walk-level CR rates",
            "",
            "| Evaluator | CANDIDATE | NO_TRADE | CR |",
            "|---|---|---|---|",
            f"| {a_id} | {metrics.n_a_candidate} | "
            f"{metrics.n_a_no_trade} | {cr_a:.1%} |",
            f"| {b_id} | {metrics.n_b_candidate} | "
            f"{metrics.n_b_no_trade} | {cr_b:.1%} |",
            "",
            "## Realized-R sums (CANDIDATE-only, walk-level)",
            "",
            "Per memory `feedback_walk_level_evidence_not_predictive.md`, "
            "these sums are NOT sufficient as evidence on their own. "
            "Join replay_results.jsonl to a realized-R analysis (paired "
            "t-test / Wilcoxon) before treating any divergence as "
            "evidence.",
            "",
            f"- Sum R when A=CANDIDATE: **{metrics.sum_realized_r_when_a_cand:+.2f}**",
            f"- Sum R when B=CANDIDATE: **{metrics.sum_realized_r_when_b_cand:+.2f}**",
            "",
        ]
        return "\n".join(lines)

    def _render_metadata(
        self, metrics: ReplayRunMetrics
    ) -> dict[str, Any]:
        return {
            "harness_version": HARNESS_VERSION,
            "run_tag": self.run_tag,
            "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "evaluator_a_id": self.evaluator_a.evaluator_id,
            "evaluator_b_id": self.evaluator_b.evaluator_id,
            "n_candidates": metrics.n_candidates,
            "n_decision_diff": metrics.n_decision_diff,
            "n_side_diff_when_both_cand": (
                metrics.n_side_diff_when_both_cand
            ),
            "n_with_realized_r": metrics.n_with_realized_r,
            "metrics": dataclasses.asdict(metrics),
        }


# ---------------------------------------------------------------------------
# __all__
# ---------------------------------------------------------------------------


__all__ = [
    "DEFAULT_EVAL_DIR",
    "DEFAULT_TRADE_RECORDS_DIR",
    "HARNESS_VERSION",
    "HistoricalCandidate",
    "LiveReplayEvaluator",
    "MockReplayEvaluator",
    "RecordedReplayEvaluator",
    "ReplayDecision",
    "ReplayEvaluator",
    "ReplayHook",
    "ReplayRun",
    "ReplayRunMetrics",
    "load_historical_candidates",
]
