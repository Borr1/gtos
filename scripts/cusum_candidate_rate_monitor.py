#!/usr/bin/env python3
"""CUSUM on CANDIDATE rate (CR) monitor — T1.5 shadow drift sentinel.

Purpose
-------
Per ``CLAUDE.md`` canonical numbers, the baseline CANDIDATE rate across all
evaluated MSOs is **10.3%**. A sustained shift in that fraction — independent
of any win-rate move — is a leading indicator of prompt drift or silent model
drift (Anthropic silently rolls the ``claude-sonnet-4-6`` alias, a prompt
deploy changes behavior, a regime change makes the gate over- or
under-triggerable). Existing monitors (``SPRTMonitor``, ``CUSUMDetector`` in
``src/components/edge_monitor.py``) cover **win rate**, not CANDIDATE rate.

This script computes a **two-sided Bernoulli CUSUM** over the per-evaluation
CANDIDATE / NO_TRADE stream. Per spec (``backlog_synthesis_2026-04-18``,
T1.5 / R061 / L4 D1):

* ``p0 = 0.103`` — canonical baseline CR (do NOT refit from live data; that
  would be in-sample).
* ``h = 4.0`` — alarm threshold. Standard Page CUSUM convention; the
  log-likelihood statistic crosses ``h`` when the observed sequence is
  ~e^4 = 54× more likely under the shifted regime than under p0.
* Two-sided: upper chart detects shift to ``p1_up = 2 * p0 = 0.206``
  (CR rising → looser gate / prompt drift). Lower chart detects shift to
  ``p1_down = p0 / 2 = 0.0515`` (CR falling → stricter gate / refusal wave).
* Alarm → flag in daily snapshot CSV AND reset the crossed accumulator to
  zero (Page restart rule). The un-crossed side continues unchanged.

The monitor is observation-only. It does NOT gate trades, does NOT modify
any pipeline state, and does NOT send Telegram alerts itself (the alarm
flag in ``shadow_logs/cusum_candidate_rate_daily.csv`` is consumed by the
watchdog and downstream operator reporting — T1.5 is scoped to shadow
data + stdout only).

Data source
-----------
``shadow_logs/candidate_features_log.jsonl`` — one JSONL line per AI
evaluation, written by ``src.components.candidate_features_logger``. Each
row has a stable schema including ``timestamp_utc`` (ISO-8601 with UTC
offset) and ``decision ∈ {"CANDIDATE", "NO_TRADE"}``. We process every
row strictly in ``timestamp_utc`` order and maintain running CUSUM state
across runs.

Cadence
-------
The underlying CUSUM updates on **every evaluation**, not once-per-day
(Page CUSUM is an online statistic). The "daily snapshot" is a checkpoint
of accumulated state as of UTC midnight — we run the script once per UTC
day (watchdog hook, mirroring ``ob_continuation_monitor.py``), catch up
on any observations seen since the previous run, and append one row per
scope (``OVERALL`` + any alarms that fired since the last snapshot).

State persistence
-----------------
``knowledge_base/meta/cusum_candidate_rate_state.json`` holds the running
``(S_up, S_down, last_processed_ts, last_processed_line_hash)``. On each
run we open the JSONL, skip any rows already processed (by timestamp), and
update the state. Corrupted state file → degrade to fresh start (warn +
treat state as zero + unknown cursor). This matches the spec bullet
"State file corruption path — degrade gracefully rather than crash".

Small-sample guard
------------------
If fewer than ``MIN_OBSERVATIONS`` total evaluations have been processed
(lifetime, across runs), the CUSUM statistic CAN be above ``h`` in theory
— but we suppress the alarm flag (``insufficient_sample=true``). The
state still tracks the running statistic; it just doesn't raise an
alarm until the baseline has enough data to be meaningful. This mirrors
``scripts/ob_continuation_monitor.py``'s ``_should_alarm`` gate.

Output
------
``shadow_logs/cusum_candidate_rate_daily.csv`` — schema:

    date_utc, scope, total_obs, candidate_count, observed_cr,
    s_up, s_down, alarm_fired, alarm_side, insufficient_sample,
    last_processed_ts

* ``scope`` = ``OVERALL`` for v1 (per-symbol scoping is a natural future
  extension but the backlog spec is explicit: "standalone script,
  ~100-150 LOC", and per-symbol would require 5x the state management
  + per-symbol baselines that we don't yet have). Mark as TODO.
* Re-runs on the same UTC day dedupe on ``(date_utc, scope)`` — newest row
  wins, via read-existing + filter + atomic rewrite (mirrors ``ob_continuation_monitor``).

CLI
---
    python scripts/cusum_candidate_rate_monitor.py             # default
    python scripts/cusum_candidate_rate_monitor.py --dry-run   # no CSV / no state write
    python scripts/cusum_candidate_rate_monitor.py --date 2026-04-19
    python scripts/cusum_candidate_rate_monitor.py --reset-state   # wipe state + start fresh

Exit codes
----------
    0 — normal run, no alarm
    1 — alarm fired on this run
    2 — unrecoverable error (cannot read log, cannot write state)

Test discipline
---------------
Module-level constants (``LOG_PATH``, ``STATE_PATH``, ``OUTPUT_CSV``,
``P0``, ``H``, ``MIN_OBSERVATIONS``) are intentionally exposed so tests
can monkeypatch them via:

    from scripts import cusum_candidate_rate_monitor as _mod
    monkeypatch.setattr(_mod, "LOG_PATH", tmp_path / "log.jsonl")

The pure-function core (``compute_cusum_step``, ``compute_cusum``) is
fully isolated from I/O — can be unit-tested without a filesystem.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Literal, Optional

# ---------------------------------------------------------------------------
# Project-root importability (script is runnable as ``python scripts/...``).
# We don't actually need any repo imports for v1, but keep the pattern for
# consistency with peer monitors.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-level constants — tests monkeypatch these on the module object.
# ---------------------------------------------------------------------------

LOG_PATH: Path = _PROJECT_ROOT / "shadow_logs" / "candidate_features_log.jsonl"
STATE_PATH: Path = _PROJECT_ROOT / "knowledge_base" / "meta" / "cusum_candidate_rate_state.json"
OUTPUT_CSV: Path = _PROJECT_ROOT / "shadow_logs" / "cusum_candidate_rate_daily.csv"

# Spec-mandated parameters (CLAUDE.md canonical CR + T1.5 research spec).
P0: float = 0.103  # baseline CANDIDATE rate; DO NOT refit from live data
H: float = 4.0     # CUSUM decision threshold

# Two-sided shift targets. A common choice is p1 = p0 ± delta where delta
# is "the shift magnitude worth catching". We pick factor-of-2 shifts on
# each side as a conservative "meaningful drift" specification:
P1_UP: float = min(2.0 * P0, 0.99)   # 0.206 — CR doubled (looser gate)
P1_DOWN: float = max(P0 / 2.0, 0.01)  # 0.0515 — CR halved (stricter / refusal)

# Small-sample guard: don't fire alarms before we've observed enough evals.
# Historical CLAUDE.md baseline implied ~165 evaluations/month at CR 10.3%.
# Keep the sample guard as a drift-statistics floor, not a symbol-universe
# ceiling; the active vNext production surface is the Stage08 broker-native
# set wired through config/startup/monitor tests.
MIN_OBSERVATIONS: int = 30


# ---------------------------------------------------------------------------
# Precomputed log-likelihood increments (pure, module-level).
#
# For a Bernoulli stream with P(CANDIDATE) = p:
#     logL_C(p_alt, p0) = log(p_alt / p0)               (candidate observed)
#     logL_N(p_alt, p0) = log((1-p_alt) / (1-p0))      (no-trade observed)
#
# We precompute these four values so ``compute_cusum_step`` is a couple of
# additions and a ``max``; no math library calls on the hot path.
# ---------------------------------------------------------------------------

def _logL(p_alt: float, p0: float, observed_candidate: bool) -> float:
    """Log-likelihood ratio for one Bernoulli observation.

    Pure function — no dependency on module state. Used both to precompute
    the defaults AND by tests that parametrize p_alt / p0.
    """
    if observed_candidate:
        return math.log(p_alt / p0)
    return math.log((1.0 - p_alt) / (1.0 - p0))


_LOGL_UP_C: float = _logL(P1_UP, P0, True)
_LOGL_UP_N: float = _logL(P1_UP, P0, False)
_LOGL_DOWN_C: float = _logL(P1_DOWN, P0, True)
_LOGL_DOWN_N: float = _logL(P1_DOWN, P0, False)


# ---------------------------------------------------------------------------
# Pure-function core: CUSUM state + per-step update + full-sequence compute.
#
# These are the primary unit-test surface. No I/O, no module singletons.
# ---------------------------------------------------------------------------


@dataclass
class CUSUMState:
    """Running CUSUM state for the CANDIDATE rate stream.

    Attributes
    ----------
    s_up, s_down :
        Non-negative accumulators for the upper and lower charts. Reset to
        0 whenever the corresponding side alarms.
    n_obs :
        Total number of observations (CANDIDATE + NO_TRADE) fed since
        state initialization. Independent of resets — alarms restart the
        accumulator but we keep counting observations for the small-sample
        gate.
    n_candidates :
        Total CANDIDATE count since state initialization. Used only for
        the ``observed_cr`` reporting column — not for alarm logic.
    alarms_up, alarms_down :
        Lifetime alarm counts on each side. Each time ``s_up >= H`` at
        step end we increment ``alarms_up`` and reset ``s_up = 0``.
    last_processed_ts :
        ISO-8601 UTC string of the most-recent observation consumed. Used
        as the cursor for "skip rows already seen" on next run. ``None``
        means no observation has been consumed yet (fresh state).
    """

    s_up: float = 0.0
    s_down: float = 0.0
    n_obs: int = 0
    n_candidates: int = 0
    alarms_up: int = 0
    alarms_down: int = 0
    last_processed_ts: Optional[str] = None


@dataclass
class CUSUMStepResult:
    """Per-step output from ``step_cusum``. Exposed for tests/inspection."""
    state: CUSUMState
    fired_up: bool = False
    fired_down: bool = False


def step_cusum(
    state: CUSUMState,
    observed_candidate: bool,
    p0: float = P0,
    p1_up: float = P1_UP,
    p1_down: float = P1_DOWN,
    h: float = H,
) -> CUSUMStepResult:
    """Advance the CUSUM state by one observation. Returns alarm flags.

    Rules
    -----
    * Upper: ``s_up = max(0, s_up + logL_up(x))``; if ``s_up >= h`` after
      update → ``fired_up = True`` AND reset ``s_up = 0`` (Page restart).
    * Lower: symmetric.
    * Both sides are updated every step (they don't block each other —
      in principle both could fire in the same step from different
      directions if the scenario is pathological, but in practice only
      one side can plausibly alarm at a time).

    The function mutates the state in place AND returns it (plus flags)
    so tests can chain updates trivially.
    """
    if p0 == p1_up or p0 == p1_down:
        raise ValueError(
            f"Degenerate CUSUM targets: p0={p0}, p1_up={p1_up}, p1_down={p1_down}"
        )

    if observed_candidate:
        state.n_candidates += 1
    state.n_obs += 1

    # Upper chart.
    logl_up = _logL(p1_up, p0, observed_candidate)
    state.s_up = max(0.0, state.s_up + logl_up)
    fired_up = False
    if state.s_up >= h:
        fired_up = True
        state.alarms_up += 1
        state.s_up = 0.0  # Page restart rule

    # Lower chart.
    logl_down = _logL(p1_down, p0, observed_candidate)
    state.s_down = max(0.0, state.s_down + logl_down)
    fired_down = False
    if state.s_down >= h:
        fired_down = True
        state.alarms_down += 1
        state.s_down = 0.0  # Page restart rule

    return CUSUMStepResult(state=state, fired_up=fired_up, fired_down=fired_down)


def compute_cusum(
    outcomes: list[bool],
    p0: float = P0,
    h: float = H,
    p1_up: Optional[float] = None,
    p1_down: Optional[float] = None,
    initial_state: Optional[CUSUMState] = None,
) -> CUSUMState:
    """Run the full two-sided CUSUM over ``outcomes`` from an initial state.

    ``outcomes`` is a list of booleans where ``True`` = CANDIDATE observed,
    ``False`` = NO_TRADE observed. Returns the final state. Intended for
    tests that want to verify exact accumulator values at sequence end —
    hand-workable on small examples.

    If ``p1_up`` / ``p1_down`` are not provided, derive ``p1_up = 2*p0``
    and ``p1_down = p0/2``, clipped to (0.01, 0.99).
    """
    if p1_up is None:
        p1_up = min(2.0 * p0, 0.99)
    if p1_down is None:
        p1_down = max(p0 / 2.0, 0.01)
    state = initial_state if initial_state is not None else CUSUMState()
    for x in outcomes:
        step_cusum(state, x, p0=p0, p1_up=p1_up, p1_down=p1_down, h=h)
    return state


# ---------------------------------------------------------------------------
# State persistence — JSON round-trip with graceful-degradation on corruption.
# ---------------------------------------------------------------------------


def load_state(path: Optional[Path] = None) -> CUSUMState:
    """Load state from ``path`` (defaults to ``STATE_PATH``).

    Missing file → fresh state. Corrupted JSON → warn + fresh state
    (spec: "degrade gracefully rather than crash"). Fields missing in
    a partially-written file → default values from ``CUSUMState``.
    """
    path = Path(path) if path is not None else Path(STATE_PATH)
    if not path.exists():
        return CUSUMState()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if not isinstance(raw, dict):
            raise ValueError(f"State root is not a dict: {type(raw).__name__}")
        # Defensive per-field parse — anything missing uses CUSUMState default.
        defaults = CUSUMState()
        state = CUSUMState(
            s_up=float(raw.get("s_up", defaults.s_up)),
            s_down=float(raw.get("s_down", defaults.s_down)),
            n_obs=int(raw.get("n_obs", defaults.n_obs)),
            n_candidates=int(raw.get("n_candidates", defaults.n_candidates)),
            alarms_up=int(raw.get("alarms_up", defaults.alarms_up)),
            alarms_down=int(raw.get("alarms_down", defaults.alarms_down)),
            last_processed_ts=raw.get("last_processed_ts"),
        )
        # Non-negative sanity checks. Tampered-but-JSON-valid files can
        # contain negatives, strings, etc. Clamp to zero + warn.
        if state.s_up < 0 or state.s_down < 0 or state.n_obs < 0:
            logger.warning(
                "State file %s has negative field(s); treating as fresh start",
                path,
            )
            return CUSUMState()
        return state
    except Exception as exc:
        logger.warning(
            "State file %s corrupt (%s: %s); treating as fresh start",
            path, type(exc).__name__, exc,
        )
        return CUSUMState()


def save_state(state: CUSUMState, path: Optional[Path] = None) -> None:
    """Atomically write ``state`` to ``path`` (defaults to ``STATE_PATH``).

    Uses tmp + ``os.replace`` for atomicity; on failure, logs and raises
    so the caller can exit(2) — state-write failure is unrecoverable
    because the next run would re-consume all observations and double-count.
    """
    path = Path(path) if path is not None else Path(STATE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "s_up": state.s_up,
        "s_down": state.s_down,
        "n_obs": state.n_obs,
        "n_candidates": state.n_candidates,
        "alarms_up": state.alarms_up,
        "alarms_down": state.alarms_down,
        "last_processed_ts": state.last_processed_ts,
        "schema_version": 1,
    }
    tmp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


# ---------------------------------------------------------------------------
# Log reader — streams the JSONL, yields ordered (ts, decision) pairs.
# ---------------------------------------------------------------------------


def iter_log_rows(path: Optional[Path] = None) -> Iterable[tuple[str, bool]]:
    """Yield ``(timestamp_utc, observed_candidate: bool)`` per JSONL row.

    Malformed lines are skipped with a WARNING. Rows lacking either
    ``timestamp_utc`` or ``decision`` are skipped. Rows whose ``decision``
    is neither ``CANDIDATE`` nor ``NO_TRADE`` are skipped (do NOT treat
    unknown-decision as NO_TRADE — that would bias the CUSUM).

    Sorting: the emission order is **file order**. Callers must re-sort
    by timestamp if needed (the orchestrator appends in monotonic UTC
    time so file order == timestamp order in practice, but we do not
    assume it in the reader).
    """
    path = Path(path) if path is not None else Path(LOG_PATH)
    if not path.exists():
        logger.warning("CANDIDATE features log missing at %s — no observations to process", path)
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning("Malformed JSONL line %d in %s: %s", line_no, path, exc)
                continue
            ts = row.get("timestamp_utc")
            decision = row.get("decision")
            if not ts or not decision:
                logger.warning(
                    "Skipping row %d (missing timestamp_utc/decision): %r", line_no, row
                )
                continue
            if decision == "CANDIDATE":
                yield ts, True
            elif decision == "NO_TRADE":
                yield ts, False
            else:
                logger.warning(
                    "Skipping row %d (unknown decision %r)", line_no, decision
                )


# ---------------------------------------------------------------------------
# CSV snapshot — append (dedupe on (date,scope)) + atomic rewrite.
# ---------------------------------------------------------------------------


_CSV_FIELDS = [
    "date_utc",
    "scope",
    "total_obs",
    "candidate_count",
    "observed_cr",
    "s_up",
    "s_down",
    "alarms_up_lifetime",
    "alarms_down_lifetime",
    "alarm_fired_today",
    "alarm_side_today",
    "insufficient_sample",
    "last_processed_ts",
]


def _read_existing_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                return []
            return [dict(r) for r in reader]
    except Exception as exc:
        logger.warning("Failed to read existing CSV %s: %s — treating as empty", path, exc)
        return []


def append_snapshot_row(
    *,
    date_utc: str,
    scope: str,
    state: CUSUMState,
    alarm_fired_today: bool,
    alarm_side_today: str,
    insufficient_sample: bool,
    output_csv: Optional[Path] = None,
) -> None:
    """Append (or replace by ``(date_utc, scope)``) one row.

    Atomic rewrite via tmp + ``os.replace``. Mirrors ``ob_continuation_monitor
    .append_daily_snapshot_row``.
    """
    path = Path(output_csv) if output_csv is not None else Path(OUTPUT_CSV)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_existing_rows(path)
    kept = [
        r for r in existing
        if not (r.get("date_utc") == date_utc and r.get("scope") == scope)
    ]
    observed_cr = (state.n_candidates / state.n_obs) if state.n_obs else 0.0
    new_row = {
        "date_utc": date_utc,
        "scope": scope,
        "total_obs": str(state.n_obs),
        "candidate_count": str(state.n_candidates),
        "observed_cr": f"{observed_cr:.6f}",
        "s_up": f"{state.s_up:.6f}",
        "s_down": f"{state.s_down:.6f}",
        "alarms_up_lifetime": str(state.alarms_up),
        "alarms_down_lifetime": str(state.alarms_down),
        "alarm_fired_today": "true" if alarm_fired_today else "false",
        "alarm_side_today": alarm_side_today,
        "insufficient_sample": "true" if insufficient_sample else "false",
        "last_processed_ts": state.last_processed_ts or "",
    }
    kept.append(new_row)

    tmp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS)
            writer.writeheader()
            for r in kept:
                writer.writerow({k: r.get(k, "") for k in _CSV_FIELDS})
        os.replace(tmp_path, path)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_monitor(
    target_date: Optional[date] = None,
    dry_run: bool = False,
    reset_state: bool = False,
    log_path: Optional[Path] = None,
    state_path: Optional[Path] = None,
    output_csv: Optional[Path] = None,
) -> int:
    """Main entrypoint.

    Returns the exit code. Dry-run writes nothing (no state, no CSV) but
    logs everything. ``reset_state`` wipes accumulated state and re-processes
    the whole log from scratch (used when the CR baseline itself is known
    to have changed — e.g. a prompt deploy).
    """
    target_date = target_date or datetime.now(timezone.utc).date()
    date_str = target_date.isoformat()

    log_p = Path(log_path) if log_path is not None else Path(LOG_PATH)
    state_p = Path(state_path) if state_path is not None else Path(STATE_PATH)
    output_p = Path(output_csv) if output_csv is not None else Path(OUTPUT_CSV)

    # 1) Load state (or reset).
    if reset_state:
        logger.info("--reset-state: wiping prior CUSUM state and re-processing from scratch")
        state = CUSUMState()
    else:
        state = load_state(state_p)
    cursor_ts_before = state.last_processed_ts
    logger.info(
        "Starting CUSUM: state=(n_obs=%d, n_cand=%d, s_up=%.4f, s_down=%.4f, "
        "alarms_up=%d, alarms_down=%d, last_ts=%s)",
        state.n_obs, state.n_candidates, state.s_up, state.s_down,
        state.alarms_up, state.alarms_down, cursor_ts_before,
    )

    # 2) Stream log rows, filter to strictly-newer-than-cursor, sort by ts.
    #    We sort defensively: production writes are append-only in UTC order,
    #    but a log-rotation / test scenario might interleave.
    try:
        raw_rows = list(iter_log_rows(log_p))
    except Exception as exc:
        logger.exception("Failed to read log %s: %s", log_p, exc)
        return 2

    # Filter "strictly after cursor" on a string compare — ISO-8601 is
    # lexicographically orderable when format is consistent. The features
    # logger always emits ``datetime.isoformat()`` which is ISO-8601 with
    # fractional seconds and ``+00:00`` offset, so lex compare == time compare.
    if cursor_ts_before is not None and not reset_state:
        new_rows = [(ts, x) for ts, x in raw_rows if ts > cursor_ts_before]
    else:
        new_rows = list(raw_rows)

    # Sort chronologically (defensive — file order should already be sorted).
    new_rows.sort(key=lambda r: r[0])

    n_new = len(new_rows)
    logger.info("Processing %d new observation(s) since cursor %s", n_new, cursor_ts_before)

    # 3) Stream updates. Track "alarm fired since cursor" for CSV reporting.
    alarm_fired_today = False
    alarm_sides: list[str] = []
    for ts, observed_candidate in new_rows:
        step = step_cusum(state, observed_candidate)
        state.last_processed_ts = ts
        if step.fired_up:
            alarm_fired_today = True
            alarm_sides.append("up")
            logger.critical(
                "CUSUM ALARM UP at ts=%s (CR likely >= %.4f) — accumulator reset",
                ts, P1_UP,
            )
        if step.fired_down:
            alarm_fired_today = True
            alarm_sides.append("down")
            logger.critical(
                "CUSUM ALARM DOWN at ts=%s (CR likely <= %.4f) — accumulator reset",
                ts, P1_DOWN,
            )

    insufficient_sample = state.n_obs < MIN_OBSERVATIONS
    if insufficient_sample:
        if alarm_fired_today:
            logger.warning(
                "Alarm(s) fired but n_obs=%d < MIN_OBSERVATIONS=%d — suppressing alarm flag",
                state.n_obs, MIN_OBSERVATIONS,
            )
        alarm_fired_today = False
        alarm_sides = []

    alarm_side_today = ",".join(sorted(set(alarm_sides))) if alarm_sides else ""

    observed_cr = (state.n_candidates / state.n_obs) if state.n_obs else 0.0
    logger.info(
        "After update: n_obs=%d, CR=%.4f (%d CANDIDATE), s_up=%.4f, s_down=%.4f, "
        "alarm_today=%s (side=%r), insufficient=%s",
        state.n_obs, observed_cr, state.n_candidates,
        state.s_up, state.s_down, alarm_fired_today, alarm_side_today,
        insufficient_sample,
    )

    # 4) Persist state + snapshot row (unless dry-run).
    if not dry_run:
        try:
            save_state(state, state_p)
        except Exception as exc:
            logger.exception("Failed to save state to %s: %s", state_p, exc)
            return 2
        try:
            append_snapshot_row(
                date_utc=date_str,
                scope="OVERALL",
                state=state,
                alarm_fired_today=alarm_fired_today,
                alarm_side_today=alarm_side_today,
                insufficient_sample=insufficient_sample,
                output_csv=output_p,
            )
        except Exception as exc:
            logger.exception("Failed to write snapshot CSV %s: %s", output_p, exc)
            # CSV write is non-fatal — state is saved, we can retry next run.

    return 1 if alarm_fired_today else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="CUSUM on CANDIDATE rate (CR) — T1.5 shadow drift monitor.",
    )
    p.add_argument(
        "--date", type=str, default=None,
        help="UTC date to stamp the output row (YYYY-MM-DD). Default: today UTC.",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Compute + log but write no state and no CSV.",
    )
    p.add_argument(
        "--reset-state", action="store_true",
        help="Wipe accumulated state and re-process the log from scratch.",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    target_date: Optional[date] = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            logger.error("Invalid --date (expected YYYY-MM-DD): %r", args.date)
            return 2

    return run_monitor(
        target_date=target_date,
        dry_run=args.dry_run,
        reset_state=args.reset_state,
    )


if __name__ == "__main__":
    sys.exit(main())
