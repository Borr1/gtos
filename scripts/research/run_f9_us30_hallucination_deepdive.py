"""F9 — US30 hallucination deep-dive (CLI driver).

Characterizes the anomalously-high hallucination rate observed for
``US30_cash`` (23.4%) — 5x the cleanest instrument USDJPY (4.3%) per
B7 (commit ``9611c58``). Filters to US30_cash CANDs only and decomposes
the hallucination rate along four axes:

* **Per-field** — which AI-cited price roles drive US30's rate up?
* **Per-month** — is the rate stable through April, or drifting?
* **Per-session** — does the london / ny / tokyo kill zone matter?
* **Per-CAND-type** — REJECTED_L2 vs LIMIT_PLACED vs other outcomes.

Phase 1 = $0 API. NO Anthropic / OpenRouter calls. Pure-Python join over
B7's existing :mod:`src.research_infra.hallucination_measurement` module.
The B7 module is **not modified** — F9 consumes its API only.

Inputs
======
* ``knowledge_base/trade_records/US30_cash/*.json`` — 26 paired MSO+AI
  CANDIDATE records (April 2026). The precise arm.
* ``knowledge_base/live_evaluations/US30_cash/*.jsonl`` — broader
  text-only stream (April 2026). Used as coarse supplementary arm.
* B7's existing run output ``research/ai_behavior/B7_hallucination/`` —
  read-only, never modified.

Outputs (caller-supplied directory; defaults to
``research/ai_behavior/F9_us30_deepdive/``):

* ``breakdown.json`` — full machine-readable decomposition (per-field,
  per-month, per-session, per-final-outcome rate matrices + sampled
  CAND inspection blobs).
* ``hallucination_rows.jsonl`` — every US30 hallucinated/misattributed
  classification, one per line, with AI value + MSO match (or absence).
* ``report.md`` — human-readable verdict block.

The script writes outputs IDEMPOTENTLY: each run overwrites these three
files; B7's outputs are NEVER touched.

Sampled-CAND inspection
=======================
For the 5-10 highest-hallucination US30 CANDs the script emits a
side-by-side block listing:

* AI-cited prices (role, value, source_field)
* MSO key levels at that timestamp (per-timeframe top-of-list OB / FVG
  / breaker / swings, plus session_levels and current_price)
* The B7 classification per cited price (with delta_ticks)
* Final outcome (REJECTED_L2 / LIMIT_PLACED / etc.)

This is the raw evidence the root-cause hypothesis document
(``root_cause_hypotheses.md``) is built from.

Out of scope
============
* Modifying production code, prompts, or config.
* Modifying the B7 module or B7's output (``research/ai_behavior/B7_hallucination/``).
* Proposing system changes — those are CEO triage decisions.
* Calling Anthropic API.

Usage
-----
::

    python scripts/research/run_f9_us30_hallucination_deepdive.py \\
        --output-dir research/ai_behavior/F9_us30_deepdive

    python scripts/research/run_f9_us30_hallucination_deepdive.py \\
        --output-dir /tmp/scratch --dry-run

Tolerance defaults to 5 ticks (matches B7); ``--tolerance-ticks`` lets
caller sweep.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# Make the project root importable when this script is invoked as a file.
_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.hallucination_measurement import (  # noqa: E402
    DEFAULT_LIVE_EVALUATIONS_DIR,
    DEFAULT_OHLCV_DIR,
    DEFAULT_TOLERANCE_TICKS,
    DEFAULT_TRADE_RECORDS_DIR,
    HARNESS_VERSION,
    EvaluationCheck,
    PriceClassification,
    measure_from_disk,
)


logger = logging.getLogger("f9_us30_deepdive")


HARNESS_VERSION_F9 = "F9-v1"

#: We focus on US30_cash; this is the only target instrument.
TARGET_SYMBOL = "US30_cash"

#: Number of top-hallucinated CANDs to emit detailed side-by-side blocks for.
DEFAULT_SAMPLE_SIZE = 10


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class FieldDecomp:
    """Per-field decomposition row."""

    field: str  # role (ob_high, ob_mid, sweep_price, etc.)
    n: int = 0
    n_accurate: int = 0
    n_hallucinated: int = 0
    n_misattributed: int = 0

    @property
    def hallucinated_pct(self) -> Optional[float]:
        return None if self.n == 0 else 100.0 * self.n_hallucinated / self.n

    @property
    def accurate_pct(self) -> Optional[float]:
        return None if self.n == 0 else 100.0 * self.n_accurate / self.n

    @property
    def misattributed_pct(self) -> Optional[float]:
        return None if self.n == 0 else 100.0 * self.n_misattributed / self.n

    @property
    def contribution_pct(self) -> Optional[float]:
        """How many of US30's TOTAL hallucinations come from this field?

        Filled by caller after total-hallucinations is known.
        """
        return getattr(self, "_contribution", None)


@dataclass
class CohortDecomp:
    """Per-cohort decomposition row (month / session / final-outcome)."""

    cohort: str
    n_evaluations: int = 0
    n_prices: int = 0
    n_accurate: int = 0
    n_hallucinated: int = 0
    n_misattributed: int = 0

    @property
    def hallucinated_pct(self) -> Optional[float]:
        return None if self.n_prices == 0 else 100.0 * self.n_hallucinated / self.n_prices

    @property
    def accurate_pct(self) -> Optional[float]:
        return None if self.n_prices == 0 else 100.0 * self.n_accurate / self.n_prices


# ---------------------------------------------------------------------------
# Cohort assignment helpers
# ---------------------------------------------------------------------------


def _kill_zone_from_record(rec: Mapping[str, Any]) -> str:
    """Read kill_zone from a trade record. Live evaluations expose it
    at top level; trade_records put it under ``metadata``.
    """
    if not isinstance(rec, Mapping):
        return "unknown"
    md = rec.get("metadata") if isinstance(rec.get("metadata"), Mapping) else None
    if md is not None and isinstance(md.get("kill_zone"), str):
        return md["kill_zone"]
    if isinstance(rec.get("kill_zone"), str):
        return rec["kill_zone"]
    return "unknown"


def _final_outcome_from_record(rec: Mapping[str, Any]) -> str:
    """Read decision_pipeline.final_outcome from a trade_records JSON.

    Live evaluations don't carry this — we return ``"none_live_eval"``
    so the cohort split is still meaningful.
    """
    if not isinstance(rec, Mapping):
        return "unknown"
    dp = rec.get("decision_pipeline")
    if isinstance(dp, Mapping) and isinstance(dp.get("final_outcome"), str):
        return dp["final_outcome"]
    # live_evaluations rows: signal source via decision
    if "decision" in rec and "overall_reasoning" in rec:
        return f"live_eval_{rec.get('decision', 'unknown')}"
    return "unknown"


def _record_path_for_check(check: EvaluationCheck, project_root: Path) -> Optional[Path]:
    """Resolve the on-disk path for a trade_records-source EvaluationCheck.

    Trade records on disk follow ``knowledge_base/trade_records/{SYMBOL}/{date}_{kz}_{HHMM}.json``.
    The candle_time_utc lets us pick out exactly which file matches
    (deterministic — the orchestrator emits one file per CAND).

    We re-load that file to fetch the kill_zone + final_outcome (which
    aren't on the EvaluationCheck dataclass).
    """
    if check.record_source != "trade_records":
        return None
    if not check.candle_time_utc:
        return None
    sym_dir = project_root / "knowledge_base" / "trade_records" / check.symbol
    if not sym_dir.exists():
        return None
    # Match the candle date (the file naming uses the local-server date,
    # which equals the UTC date for our broker; we still filter by the
    # full candle_time match inside).
    try:
        ct = check.candle_time_utc
        # candle_time in metadata is ISO with microseconds — exact match
        # against re-loaded file's metadata.candle_time
        for json_path in sorted(sym_dir.glob("*.json")):
            with open(json_path, "r", encoding="utf-8") as f:
                rec = json.load(f)
            md = rec.get("metadata") if isinstance(rec.get("metadata"), Mapping) else {}
            if md.get("candle_time") == ct:
                return json_path
    except (OSError, json.JSONDecodeError, AttributeError):
        return None
    return None


# ---------------------------------------------------------------------------
# Decomposition logic
# ---------------------------------------------------------------------------


def filter_to_us30(checks: List[EvaluationCheck]) -> List[EvaluationCheck]:
    """Keep only US30_cash rows."""
    return [c for c in checks if c.symbol == TARGET_SYMBOL]


def decompose_per_field(checks: List[EvaluationCheck]) -> List[FieldDecomp]:
    """Per-AI-role decomposition: which fields contribute most?"""
    by_field: Dict[str, FieldDecomp] = {}
    total_hall = 0
    for c in checks:
        for cl in c.classifications:
            if cl.classification is None:
                continue
            row = by_field.setdefault(cl.role, FieldDecomp(field=cl.role))
            row.n += 1
            if cl.classification == "accurate":
                row.n_accurate += 1
            elif cl.classification == "hallucinated":
                row.n_hallucinated += 1
                total_hall += 1
            elif cl.classification == "misattributed":
                row.n_misattributed += 1

    # Compute per-field contribution as % of US30 total hallucinations
    for row in by_field.values():
        if total_hall > 0:
            setattr(row, "_contribution", 100.0 * row.n_hallucinated / total_hall)
        else:
            setattr(row, "_contribution", None)

    return sorted(by_field.values(), key=lambda r: -(r.hallucinated_pct or 0))


def decompose_per_month(checks: List[EvaluationCheck]) -> List[CohortDecomp]:
    """Per-month decomposition (period_month from B7)."""
    by_month: Dict[str, CohortDecomp] = {}
    for c in checks:
        key = c.period_month or "unknown_month"
        row = by_month.setdefault(key, CohortDecomp(cohort=key))
        row.n_evaluations += 1
        for cl in c.classifications:
            if cl.classification is None:
                continue
            row.n_prices += 1
            if cl.classification == "accurate":
                row.n_accurate += 1
            elif cl.classification == "hallucinated":
                row.n_hallucinated += 1
            elif cl.classification == "misattributed":
                row.n_misattributed += 1
    return sorted(by_month.values(), key=lambda r: r.cohort)


def decompose_per_session(
    checks: List[EvaluationCheck],
    per_check_kill_zone: Dict[Tuple[str, str], str],
) -> List[CohortDecomp]:
    """Per-session decomposition. Uses pre-resolved kill_zone map."""
    by_session: Dict[str, CohortDecomp] = {}
    for c in checks:
        key = per_check_kill_zone.get((c.candle_time_utc or "", c.record_source), "unknown")
        row = by_session.setdefault(key, CohortDecomp(cohort=key))
        row.n_evaluations += 1
        for cl in c.classifications:
            if cl.classification is None:
                continue
            row.n_prices += 1
            if cl.classification == "accurate":
                row.n_accurate += 1
            elif cl.classification == "hallucinated":
                row.n_hallucinated += 1
            elif cl.classification == "misattributed":
                row.n_misattributed += 1
    return sorted(by_session.values(), key=lambda r: r.cohort)


def decompose_per_final_outcome(
    checks: List[EvaluationCheck],
    per_check_outcome: Dict[Tuple[str, str], str],
) -> List[CohortDecomp]:
    """Per-final-outcome decomposition."""
    by_outcome: Dict[str, CohortDecomp] = {}
    for c in checks:
        key = per_check_outcome.get((c.candle_time_utc or "", c.record_source), "unknown")
        row = by_outcome.setdefault(key, CohortDecomp(cohort=key))
        row.n_evaluations += 1
        for cl in c.classifications:
            if cl.classification is None:
                continue
            row.n_prices += 1
            if cl.classification == "accurate":
                row.n_accurate += 1
            elif cl.classification == "hallucinated":
                row.n_hallucinated += 1
            elif cl.classification == "misattributed":
                row.n_misattributed += 1
    return sorted(by_outcome.values(), key=lambda r: r.cohort)


# ---------------------------------------------------------------------------
# Sampled-CAND inspection
# ---------------------------------------------------------------------------


def _hallucination_score(check: EvaluationCheck) -> Tuple[int, int]:
    """Sortable: (hallucinated count, total non-accurate count)."""
    n_h = sum(1 for c in check.classifications if c.classification == "hallucinated")
    n_m = sum(1 for c in check.classifications if c.classification == "misattributed")
    return (n_h, n_h + n_m)


def _summarize_mso_key_levels(
    rec: Mapping[str, Any],
    *,
    max_per_block: int = 3,
) -> Dict[str, Any]:
    """Produce a compact per-timeframe summary of the MSO's key levels.

    For human inspection: top-of-list OBs, FVGs, breakers, swings + session
    levels. Caps each list to ``max_per_block`` so the output stays scannable.
    """
    out: Dict[str, Any] = {}
    mso = rec.get("mso") if isinstance(rec, Mapping) else None
    if not isinstance(mso, Mapping):
        return {"mso_present": False}

    out["mso_present"] = True
    timeframes = mso.get("timeframes") or {}
    if isinstance(timeframes, Mapping):
        tfs: Dict[str, Any] = {}
        for tf, block in timeframes.items():
            if not isinstance(block, Mapping):
                continue
            tf_out: Dict[str, Any] = {}
            obs = block.get("order_blocks") or []
            tf_out["order_blocks"] = [
                {"high": ob.get("high"), "low": ob.get("low"), "type": ob.get("type"),
                 "time": ob.get("time"), "touch_count": ob.get("touch_count")}
                for ob in obs[:max_per_block] if isinstance(ob, Mapping)
            ]
            fvgs = block.get("fair_value_gaps") or []
            tf_out["fair_value_gaps"] = [
                {"top": fvg.get("top", fvg.get("high")), "bottom": fvg.get("bottom", fvg.get("low")),
                 "type": fvg.get("type"), "time": fvg.get("time")}
                for fvg in fvgs[:max_per_block] if isinstance(fvg, Mapping)
            ]
            bbs = block.get("breaker_blocks") or []
            tf_out["breaker_blocks"] = [
                {"high": bb.get("zone_high", bb.get("high")), "low": bb.get("zone_low", bb.get("low")),
                 "type": bb.get("type"), "time": bb.get("time")}
                for bb in bbs[:max_per_block] if isinstance(bb, Mapping)
            ]
            swings = block.get("swings") or []
            tf_out["swings"] = [
                {"price": sw.get("price"), "type": sw.get("type"), "time": sw.get("time")}
                for sw in swings[-max_per_block:] if isinstance(sw, Mapping)
            ]
            candles = block.get("candles") or []
            if candles and isinstance(candles[-1], Mapping):
                last = candles[-1]
                tf_out["last_candle"] = {
                    "open": last.get("open"), "high": last.get("high"),
                    "low": last.get("low"), "close": last.get("close"),
                    "time": last.get("time"),
                }
            tfs[tf] = tf_out
        out["timeframes"] = tfs

    sl = mso.get("session_levels") or {}
    if isinstance(sl, Mapping):
        out["session_levels"] = {k: v for k, v in sl.items() if isinstance(v, (int, float))}

    return out


def build_inspection_block(
    check: EvaluationCheck,
    *,
    record: Mapping[str, Any],
    kill_zone: str,
    final_outcome: str,
) -> Dict[str, Any]:
    """One side-by-side AI-vs-MSO inspection block for a single CAND."""
    n_h = sum(1 for c in check.classifications if c.classification == "hallucinated")
    n_m = sum(1 for c in check.classifications if c.classification == "misattributed")
    return {
        "candle_time_utc": check.candle_time_utc,
        "kill_zone": kill_zone,
        "final_outcome": final_outcome,
        "framework": check.framework,
        "decision": check.decision,
        "n_classifications": len(check.classifications),
        "n_hallucinated": n_h,
        "n_misattributed": n_m,
        "hallucination_score": float(n_h) + 0.5 * float(n_m),
        "ai_cited_prices": [
            {
                "role": cl.role,
                "value": cl.value,
                "source_field": cl.source_field,
                "classification": cl.classification,
                "matched_mso_field": cl.matched_mso_field,
                "matched_mso_value": cl.matched_mso_value,
                "delta_ticks": cl.delta_ticks,
                "note": cl.note,
            }
            for cl in check.classifications
        ],
        "mso_key_levels": _summarize_mso_key_levels(record),
    }


# ---------------------------------------------------------------------------
# Side-band: cohort lookup tables
# ---------------------------------------------------------------------------


def build_per_check_metadata(
    checks: List[EvaluationCheck],
    *,
    project_root: Path,
    trade_records_dir: Path,
    live_evaluations_dir: Path,
) -> Tuple[Dict[Tuple[str, str], str], Dict[Tuple[str, str], str], Dict[Tuple[str, str], Mapping[str, Any]]]:
    """Resolve ``kill_zone`` + ``final_outcome`` + raw record per check.

    Returns three dicts keyed on ``(candle_time_utc, record_source)``:
      * kill_zone_map
      * final_outcome_map
      * record_map (raw JSON of the record)

    For trade_records we re-load from disk by exact candle_time match.
    For live_evaluations we re-iterate the JSONL files for US30_cash and
    match by exact candle_time.
    """
    kill_zone_map: Dict[Tuple[str, str], str] = {}
    final_outcome_map: Dict[Tuple[str, str], str] = {}
    record_map: Dict[Tuple[str, str], Mapping[str, Any]] = {}

    # Trade records
    sym_dir = trade_records_dir / TARGET_SYMBOL
    if sym_dir.exists():
        for json_path in sorted(sym_dir.glob("*.json")):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    rec = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            md = rec.get("metadata") if isinstance(rec.get("metadata"), Mapping) else {}
            ct = md.get("candle_time")
            if not ct:
                continue
            key = (str(ct), "trade_records")
            kill_zone_map[key] = _kill_zone_from_record(rec)
            final_outcome_map[key] = _final_outcome_from_record(rec)
            record_map[key] = rec

    # Live evaluations
    le_sym_dir = live_evaluations_dir / TARGET_SYMBOL
    if le_sym_dir.exists():
        for jsonl_path in sorted(le_sym_dir.glob("*.jsonl")):
            try:
                with open(jsonl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        ct = rec.get("candle_time")
                        if not ct:
                            continue
                        key = (str(ct), "live_evaluations")
                        kill_zone_map[key] = _kill_zone_from_record(rec)
                        final_outcome_map[key] = _final_outcome_from_record(rec)
                        # Don't store live_eval record_map — we don't need its MSO
                        # for inspection (it has none). Keep map sparse to save mem.
            except OSError:
                continue

    return kill_zone_map, final_outcome_map, record_map


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


@dataclass
class F9Result:
    """Top-level F9 deepdive result."""

    harness_version_b7: str
    harness_version_f9: str
    tolerance_ticks: int
    n_us30_evaluations: int
    n_us30_prices: int
    overall_us30_hallucination_pct: float
    by_field: List[FieldDecomp]
    by_month: List[CohortDecomp]
    by_session: List[CohortDecomp]
    by_final_outcome: List[CohortDecomp]
    sampled_inspections: List[Dict[str, Any]]
    sample_size: int


def run_deepdive(
    *,
    trade_records_dir: Path,
    live_evaluations_dir: Path,
    ohlcv_dir: Path,
    tolerance_ticks: int = DEFAULT_TOLERANCE_TICKS,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    project_root: Path = _PROJECT_ROOT,
) -> Tuple[F9Result, List[EvaluationCheck]]:
    """Run the F9 deep-dive end-to-end.

    Returns the structured result + the list of per-row US30 checks for
    JSONL emission.
    """
    # 1) Drive B7 over the full corpus.
    report = measure_from_disk(
        trade_records_dir=trade_records_dir,
        live_evaluations_dir=live_evaluations_dir,
        ohlcv_dir=ohlcv_dir,
        tolerance_ticks=tolerance_ticks,
        include_live_evaluations=True,
    )

    # 2) Filter to US30_cash.
    us30_checks = filter_to_us30(report.rows)

    n_evals = len(us30_checks)
    n_prices = sum(
        1 for c in us30_checks for cl in c.classifications if cl.classification is not None
    )
    n_hall = sum(
        1 for c in us30_checks for cl in c.classifications if cl.classification == "hallucinated"
    )
    overall_pct = (100.0 * n_hall / n_prices) if n_prices > 0 else 0.0

    # 3) Per-cohort metadata lookup
    kill_zone_map, final_outcome_map, record_map = build_per_check_metadata(
        us30_checks,
        project_root=project_root,
        trade_records_dir=trade_records_dir,
        live_evaluations_dir=live_evaluations_dir,
    )

    # 4) Decomposition axes
    by_field = decompose_per_field(us30_checks)
    by_month = decompose_per_month(us30_checks)
    by_session = decompose_per_session(us30_checks, kill_zone_map)
    by_final_outcome = decompose_per_final_outcome(us30_checks, final_outcome_map)

    # 5) Sample top-N highest-hallucination CANDs (precise arm only — we
    #    need MSO for the side-by-side block).
    precise_checks = [c for c in us30_checks if c.record_source == "trade_records"]
    precise_checks.sort(key=lambda c: _hallucination_score(c), reverse=True)
    sampled = precise_checks[:sample_size]

    inspections: List[Dict[str, Any]] = []
    for ch in sampled:
        key = (ch.candle_time_utc or "", "trade_records")
        rec = record_map.get(key)
        if rec is None:
            continue
        inspections.append(build_inspection_block(
            ch,
            record=rec,
            kill_zone=kill_zone_map.get(key, "unknown"),
            final_outcome=final_outcome_map.get(key, "unknown"),
        ))

    return (
        F9Result(
            harness_version_b7=report.harness_version,
            harness_version_f9=HARNESS_VERSION_F9,
            tolerance_ticks=tolerance_ticks,
            n_us30_evaluations=n_evals,
            n_us30_prices=n_prices,
            overall_us30_hallucination_pct=overall_pct,
            by_field=by_field,
            by_month=by_month,
            by_session=by_session,
            by_final_outcome=by_final_outcome,
            sampled_inspections=inspections,
            sample_size=sample_size,
        ),
        us30_checks,
    )


# ---------------------------------------------------------------------------
# Output emission
# ---------------------------------------------------------------------------


def _field_decomp_to_dict(r: FieldDecomp) -> Dict[str, Any]:
    return {
        "field": r.field,
        "n": r.n,
        "n_accurate": r.n_accurate,
        "n_hallucinated": r.n_hallucinated,
        "n_misattributed": r.n_misattributed,
        "accurate_pct": r.accurate_pct,
        "hallucinated_pct": r.hallucinated_pct,
        "misattributed_pct": r.misattributed_pct,
        "contribution_pct": r.contribution_pct,
    }


def _cohort_decomp_to_dict(r: CohortDecomp) -> Dict[str, Any]:
    return {
        "cohort": r.cohort,
        "n_evaluations": r.n_evaluations,
        "n_prices": r.n_prices,
        "n_accurate": r.n_accurate,
        "n_hallucinated": r.n_hallucinated,
        "n_misattributed": r.n_misattributed,
        "accurate_pct": r.accurate_pct,
        "hallucinated_pct": r.hallucinated_pct,
    }


def write_breakdown_json(result: F9Result, path: Path) -> None:
    payload: Dict[str, Any] = {
        "harness_version_f9": result.harness_version_f9,
        "harness_version_b7": result.harness_version_b7,
        "tolerance_ticks": result.tolerance_ticks,
        "n_us30_evaluations": result.n_us30_evaluations,
        "n_us30_prices": result.n_us30_prices,
        "overall_us30_hallucination_pct": result.overall_us30_hallucination_pct,
        "by_field": [_field_decomp_to_dict(r) for r in result.by_field],
        "by_month": [_cohort_decomp_to_dict(r) for r in result.by_month],
        "by_session": [_cohort_decomp_to_dict(r) for r in result.by_session],
        "by_final_outcome": [_cohort_decomp_to_dict(r) for r in result.by_final_outcome],
        "sample_size": result.sample_size,
        "sampled_inspections": result.sampled_inspections,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_hallucination_rows_jsonl(checks: List[EvaluationCheck], path: Path) -> None:
    """Emit per-classification rows for US30 hallucinated/misattributed only.

    One line per non-accurate classification (exclude accurate ones to
    keep file scannable). For each non-accurate classification we emit
    the AI's role + value + source_field + matched MSO field if any.
    """
    with open(path, "w", encoding="utf-8") as f:
        for c in checks:
            for cl in c.classifications:
                if cl.classification not in ("hallucinated", "misattributed"):
                    continue
                row = {
                    "candle_time_utc": c.candle_time_utc,
                    "record_source": c.record_source,
                    "period_month": c.period_month,
                    "period_half": c.period_half,
                    "decision": c.decision,
                    "framework": c.framework,
                    "realized_r": c.realized_r,
                    "role": cl.role,
                    "value": cl.value,
                    "source_field": cl.source_field,
                    "classification": cl.classification,
                    "matched_mso_field": cl.matched_mso_field,
                    "matched_mso_value": cl.matched_mso_value,
                    "delta_ticks": cl.delta_ticks,
                    "note": cl.note,
                }
                f.write(json.dumps(row) + "\n")


def write_report_md(result: F9Result, path: Path) -> None:
    lines = []
    lines.append("# F9 — US30_cash Hallucination Deep-Dive")
    lines.append("")
    lines.append(
        f"Harness: F9=`{result.harness_version_f9}` consuming "
        f"B7=`{result.harness_version_b7}` · "
        f"tolerance_ticks: {result.tolerance_ticks}"
    )
    lines.append("")
    lines.append(
        f"US30_cash evaluations: {result.n_us30_evaluations} · "
        f"classifications: {result.n_us30_prices} · "
        f"hallucination%: {result.overall_us30_hallucination_pct:.1f}%"
    )
    lines.append("")
    lines.append("Per B7 baseline: US30_cash 23.4% hallucination, 5x cleanest "
                 "(USDJPY 4.3%). This document decomposes that rate.")
    lines.append("")

    # ----- Verdict -----
    lines.append("## US30_cash hallucination decomposition")
    lines.append("")

    # Per-field (top 5)
    lines.append("### Per-field (top 5 by hallucinated%)")
    lines.append("")
    lines.append("| Field | n | hallucinated% | accurate% | misattributed% | contribution% |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in result.by_field[:5]:
        lines.append(
            f"| {r.field} | {r.n} | {_fmt_pct(r.hallucinated_pct)} | "
            f"{_fmt_pct(r.accurate_pct)} | {_fmt_pct(r.misattributed_pct)} | "
            f"{_fmt_pct(r.contribution_pct)} |"
        )
    lines.append("")

    # Per-month
    lines.append("### Per-month")
    lines.append("")
    lines.append("| Month | n_evals | n_prices | hallucination rate |")
    lines.append("|---|---:|---:|---:|")
    for r in result.by_month:
        lines.append(
            f"| {r.cohort} | {r.n_evaluations} | {r.n_prices} | {_fmt_pct(r.hallucinated_pct)} |"
        )
    lines.append("")

    # Per-session
    lines.append("### Per-session (kill zone)")
    lines.append("")
    lines.append("| Session | n_evals | n_prices | hallucination rate |")
    lines.append("|---|---:|---:|---:|")
    for r in result.by_session:
        lines.append(
            f"| {r.cohort} | {r.n_evaluations} | {r.n_prices} | {_fmt_pct(r.hallucinated_pct)} |"
        )
    lines.append("")

    # Per-final-outcome
    lines.append("### Per-CAND-type (final outcome)")
    lines.append("")
    lines.append("| Final outcome | n_evals | n_prices | hallucination rate |")
    lines.append("|---|---:|---:|---:|")
    for r in result.by_final_outcome:
        lines.append(
            f"| {r.cohort} | {r.n_evaluations} | {r.n_prices} | {_fmt_pct(r.hallucinated_pct)} |"
        )
    lines.append("")

    # ----- Sample inspections -----
    lines.append("## Sampled top-hallucination CANDs (top "
                 f"{len(result.sampled_inspections)})")
    lines.append("")
    if not result.sampled_inspections:
        lines.append("_No precise-arm CANDs available for sampling._")
        lines.append("")
    else:
        for i, blk in enumerate(result.sampled_inspections, 1):
            lines.append(f"### {i}. {blk['candle_time_utc']} "
                         f"({blk['kill_zone']}, {blk['final_outcome']})")
            lines.append("")
            lines.append(
                f"Decision: {blk['decision']} · framework: {blk['framework']} · "
                f"hallucinated: {blk['n_hallucinated']} · misattributed: {blk['n_misattributed']} · "
                f"score: {blk['hallucination_score']:.1f}"
            )
            lines.append("")
            lines.append("**AI-cited prices:**")
            lines.append("")
            lines.append("| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |")
            lines.append("|---|---:|---|---|---:|---:|")
            for cp in blk["ai_cited_prices"]:
                matched_field = cp.get("matched_mso_field") or "—"
                matched_val = cp.get("matched_mso_value")
                matched_val_s = f"{matched_val}" if matched_val is not None else "—"
                dt_s = f"{cp.get('delta_ticks'):.1f}" if cp.get("delta_ticks") is not None else "—"
                lines.append(
                    f"| {cp['role']} | {cp['value']} | {cp['classification']} | "
                    f"`{matched_field}` | {matched_val_s} | {dt_s} |"
                )
            lines.append("")
            mso = blk.get("mso_key_levels") or {}
            tfs = mso.get("timeframes") or {}
            if tfs:
                lines.append("**MSO key levels (top 3 per block):**")
                lines.append("")
                for tf in sorted(tfs.keys()):
                    tf_blk = tfs[tf]
                    obs = tf_blk.get("order_blocks") or []
                    fvgs = tf_blk.get("fair_value_gaps") or []
                    bbs = tf_blk.get("breaker_blocks") or []
                    swings = tf_blk.get("swings") or []
                    lc = tf_blk.get("last_candle") or {}
                    lines.append(f"- **{tf}** last close={lc.get('close')} "
                                 f"(O={lc.get('open')} H={lc.get('high')} L={lc.get('low')})")
                    if obs:
                        ob_strs = [f"{ob.get('low')}-{ob.get('high')} ({ob.get('type')})" for ob in obs]
                        lines.append(f"  - OBs: {', '.join(ob_strs)}")
                    if fvgs:
                        fvg_strs = [f"{fvg.get('bottom')}-{fvg.get('top')} ({fvg.get('type')})" for fvg in fvgs]
                        lines.append(f"  - FVGs: {', '.join(fvg_strs)}")
                    if bbs:
                        bb_strs = [f"{bb.get('low')}-{bb.get('high')} ({bb.get('type')})" for bb in bbs]
                        lines.append(f"  - Breakers: {', '.join(bb_strs)}")
                    if swings:
                        sw_strs = [f"{sw.get('price')} ({sw.get('type')})" for sw in swings]
                        lines.append(f"  - Swings: {', '.join(sw_strs)}")
                lines.append("")
            sl = mso.get("session_levels") or {}
            if sl:
                sl_strs = [f"{k}={v}" for k, v in sorted(sl.items())]
                lines.append(f"  - Session levels: {', '.join(sl_strs)}")
                lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "See ``root_cause_hypotheses.md`` (sibling) for the candidate "
        "root-cause inventory derived from these inspections."
    )
    lines.append("")
    return path.write_text("\n".join(lines), encoding="utf-8")


def _fmt_pct(p: Optional[float]) -> str:
    if p is None:
        return "—"
    return f"{p:.1f}%"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_f9_us30_hallucination_deepdive",
        description=(
            "F9 — US30_cash hallucination deep-dive. Decomposes US30's 23.4% "
            "B7 hallucination rate by field / month / session / final-outcome "
            "and emits side-by-side AI-vs-MSO inspection blocks for the top-N "
            "hallucinated CANDs. NO AI calls; pure-Python."
        ),
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for breakdown.json + hallucination_rows.jsonl + report.md.",
    )
    p.add_argument(
        "--tolerance-ticks",
        type=int,
        default=DEFAULT_TOLERANCE_TICKS,
        help=f"Tolerance for price match in ticks (default {DEFAULT_TOLERANCE_TICKS}).",
    )
    p.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help=f"How many top-hallucinated CANDs to inspect side-by-side (default {DEFAULT_SAMPLE_SIZE}).",
    )
    p.add_argument(
        "--trade-records-dir",
        type=Path,
        default=DEFAULT_TRADE_RECORDS_DIR,
        help="Path to knowledge_base/trade_records/.",
    )
    p.add_argument(
        "--live-evaluations-dir",
        type=Path,
        default=DEFAULT_LIVE_EVALUATIONS_DIR,
        help="Path to knowledge_base/live_evaluations/.",
    )
    p.add_argument(
        "--ohlcv-dir",
        type=Path,
        default=DEFAULT_OHLCV_DIR,
        help="Path to data/historical_2026/ for the OHLCV lookback stand-in.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and exit 0 without writing.",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Enable INFO-level logging from the underlying module.",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    print(f"# F9 US30 Hallucination Deep-Dive — harness {HARNESS_VERSION_F9}")
    print(f"# Driving B7 module = {HARNESS_VERSION}")
    print(f"trade_records_dir   : {args.trade_records_dir}")
    print(f"live_evaluations_dir: {args.live_evaluations_dir}")
    print(f"ohlcv_dir           : {args.ohlcv_dir}")
    print(f"tolerance_ticks     : {args.tolerance_ticks}")
    print(f"sample_size         : {args.sample_size}")
    print(f"output_dir          : {args.output_dir}")
    print(f"started             : {dt.datetime.now(dt.timezone.utc).isoformat()}")

    if args.dry_run:
        print("[DRY RUN] No writes. Exiting 0.")
        return 0

    result, us30_checks = run_deepdive(
        trade_records_dir=args.trade_records_dir,
        live_evaluations_dir=args.live_evaluations_dir,
        ohlcv_dir=args.ohlcv_dir,
        tolerance_ticks=args.tolerance_ticks,
        sample_size=args.sample_size,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    breakdown_path = args.output_dir / "breakdown.json"
    write_breakdown_json(result, breakdown_path)
    print(f"[wrote] {breakdown_path}")

    rows_path = args.output_dir / "hallucination_rows.jsonl"
    write_hallucination_rows_jsonl(us30_checks, rows_path)
    print(f"[wrote] {rows_path}")

    report_path = args.output_dir / "report.md"
    write_report_md(result, report_path)
    print(f"[wrote] {report_path}")

    print(f"\nfinished : {dt.datetime.now(dt.timezone.utc).isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
