"""The B7.5 sealed-arm diagnostic pool, as a typed row set. Read-only, seal-checked.

WHAT THIS IS AND WHY IT EXISTS
------------------------------
`JANUARY_BANK.md` §7.5 records that the campaign's cited residual value — a learning-lane
dataset — was not collectible, because *"the arms emit no ledger the dataset builder can
read"*. That sentence is about a missing READER, not a missing ledger: the arms emit a
`*_MISSED_OPPORTUNITY_LEDGER.jsonl` per arm carrying, on the January reference arm,
**28,519 scoreable diagnostic rows** whose counterfactual outcomes sum to +6,916.95 R
positive against −31,400.82 R negative (`…MATRIX_AUDIT.json` → `arms.S0R0.missed_outcomes`).
This module is that reader.

The pool is the campaign's REJECTED candidates with their counterfactual outcomes scored.
`JANUARY_BANK.md` §3 states the open question it exists to serve: the factorial tested
whether **two particular pre-registered switches** separate those rows, and they did not.
Whether ANY rule separates them is *"open and unmeasured at any useful resolution"*.

WHAT A CALLER MUST KNOW BEFORE USING A NUMBER FROM HERE
-------------------------------------------------------
1. **These are PROXY outcomes, not realised trades.** `opportunity_net_proxy_r` is the
   counterfactual R of a candidate the incumbent did not take, computed on the replay's
   own exit model — which grants **exactly zero gap-through** (F31, `GATE_G1A_RECEIPT.md`
   §4). The measured gap-through on covered level exits is **−0.038186 R/row** and it is a
   LOWER bound, because the 47 rows with no executable close-side quote are precisely the
   `stop_reached_before_target` / `target_reached_before_stop` population. Charge it before
   any economic claim. `F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW` below is that constant.
2. **The pool is not symmetric, and the "±38,317 R" framing overstates what is capturable.**
   Positive rows mean +0.864 R each; negative rows mean −1.531 R each. A selector must
   therefore reach a precision of about 64 % before it breaks even, against a base rate of
   28.1 %. `pool_summary()` returns those numbers rather than leaving them to be re-derived.
3. **Features and outcomes are separated by construction.** `PROJECTION` carries only
   fields the replay itself stamps `no_outcome_fields` in their provenance; every outcome
   is prefixed `outcome_` and lives in `OUTCOME_PROJECTION`. A miner that only ever reads
   `FEATURE_NAMES` cannot leak a label into a rule by accident.
4. **`asof_utc` is a true UTC instant here**, unlike the tick archive (CLAUDE.md §4). The
   replay's decision clock is UTC and the row carries `utc_hour_bucket` derived from it.
   The BROKER hour is a different quantity; derive it with `src/utils/broker_clock.py` at
   the point of use, never by adding a constant.

THE SEAL CHECK IS THE TEST
--------------------------
`build_pool()` streams each ledger once and returns, per arm, the four counts the sealed
matrix audit already published: `rows`, `diagnostic_scoreable_rows`,
`diagnostic_positive_rows`, `diagnostic_negative_rows`, plus the two net-R sums.
`verify_against_sealed_audit()` compares them. A byte-level prefilter is used to skip the
81.5 % of rows that are not diagnostic-scoreable — that is a ~5× speedup on 7.6 GB — and
the seal comparison is exactly what proves the prefilter is not dropping a row: a
prefilter that were wrong would move `diagnostic_scoreable_rows` off the sealed value.

NOTHING HERE WRITES INTO THE ROUTE. Every ledger is opened through
`b7_5_cold_evidence.RawOrColdResolver`, which refuses ambiguous raw+cold representations
and verifies each shard's hash as it inflates it.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The producing worktree. Sealed authority binds absolute paths (CLAUDE.md H4), so the
#: ledgers are read where they were written and are never copied. Overridable for tests.
DEFAULT_LEDGER_ROOT = Path(
    os.environ.get(
        "GTOS_B7_5_LEDGER_ROOT",
        "/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/research/operations"
        "/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20",
    )
)

SEALED_JANUARY_MATRIX_AUDIT = (
    REPO_ROOT
    / "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
    / "B7_5_SELECTION_SIZING_DEVELOPMENT_JANUARY_SOURCE_REPAIRED_R3_CAP_R2_MATRIX_AUDIT.json"
)

#: `GATE_G1A_RECEIPT.md` §4 / `IMPLEMENTATION_STATE.md` B33: net gap-through over the 212
#: covered level-exit rows of the four sealed January arms. Adverse on 204 of 212. A LOWER
#: bound — the 47 uncovered rows are the ones most likely to gap.
F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW = -0.038186

#: Close reasons whose exit is a LEVEL (stop / target / giveback), i.e. the family F31
#: measured. Mark exits (`path_end_mark_to_market`, time stops) do not gap through.
LEVEL_EXIT_TERMINAL_OUTCOMES = frozenset(
    {"stop_reached_before_target", "target_reached_before_stop"}
)


class DiagnosticPoolError(RuntimeError):
    """Raised when a pool invariant or a seal comparison fails."""


# ---------------------------------------------------------------------------------------
# arms
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ArmSpec:
    """One sealed replay arm and where its missed-opportunity ledger lives."""

    arm_id: str
    window: str
    prefix: str
    #: Sub-path under the ledger root. January's four arms sit at the root; April's
    #: partial sits under its own `attempt_5_typed_sparse/PHASE_D_…` namespace.
    subdir: str = ""
    selection_factor: str = ""
    sizing_factor: str = ""
    note: str = ""

    def ledger_path(self, root: Path | None = None) -> Path:
        base = Path(root) if root is not None else DEFAULT_LEDGER_ROOT
        if self.subdir:
            base = base / self.subdir
        return base / f"{self.prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl"


_JAN_PREFIX = "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_{arm}_SOURCE_REPAIRED_R3_CAP_R2"

ARMS: dict[str, ArmSpec] = {
    "S0R0": ArmSpec(
        "S0R0", "JANUARY_2026", _JAN_PREFIX.format(arm="S0R0"),
        selection_factor="S0", sizing_factor="R0",
        note="reference arm: fixed selection, fixed sizing. The least-bad cell and the "
             "arm JANUARY_BANK section 3 quotes.",
    ),
    "S1R0": ArmSpec(
        "S1R0", "JANUARY_2026", _JAN_PREFIX.format(arm="S1R0"),
        selection_factor="S1", sizing_factor="R0", note="selection switch only.",
    ),
    "S0R1": ArmSpec(
        "S0R1", "JANUARY_2026", _JAN_PREFIX.format(arm="S0R1"),
        selection_factor="S0", sizing_factor="R1", note="sizing switch only.",
    ),
    "S1R1": ArmSpec(
        "S1R1", "JANUARY_2026", _JAN_PREFIX.format(arm="S1R1"),
        selection_factor="S1", sizing_factor="R1", note="joint incumbent.",
    ),
    "APR_S1R1_PARTIAL": ArmSpec(
        "APR_S1R1_PARTIAL", "APRIL_2026_PARTIAL",
        "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_SELECTION_SIZING_S1R1_SOURCE_REPAIRED_R5_CAP_R2",
        subdir="attempt_5_typed_sparse/PHASE_D_APRIL_S1R1_R1_20260725T070249Z",
        selection_factor="S1", sizing_factor="R1",
        note="15 sealed days, 9 trading sessions, no comparand, no resume path "
             "(JANUARY_BANK section 5.1). Secondary holdout only.",
    ),
}

JANUARY_ARMS: tuple[str, ...] = ("S0R0", "S1R0", "S0R1", "S1R1")


# ---------------------------------------------------------------------------------------
# projection
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Field_:
    """One projected column. `source` may be dotted for a nested payload."""

    name: str
    source: str
    family: str
    kind: str  # "cat" | "num" | "bool" | "id" | "time"
    note: str = ""


#: Predecision features only. Every one of these is stamped by the replay under a
#: `…_no_outcome_fields` source boundary, or is a mechanical identity/time field.
PROJECTION: tuple[Field_, ...] = (
    # --- identity (never a feature; carried so a row can be traced back) --------------
    Field_("candidate_instance_key", "canonical_replay_candidate_instance_key", "ID", "id"),
    Field_("candidate_id", "candidate_id", "ID", "id"),
    Field_("decision_window_id", "decision_window_id", "ID", "id"),
    Field_("candidate_set_id", "candidate_set_id", "ID", "id"),
    Field_("stable_decision_window_id", "stable_decision_window_id", "ID", "id"),
    Field_("decision_time_utc", "decision_time_utc", "ID", "time"),
    Field_("trading_day", "trading_day", "ID", "cat"),
    Field_("split", "split", "ID", "cat"),
    Field_("chunk_id", "chunk_id", "ID", "id"),
    # --- A: instrument and mechanism ---------------------------------------------------
    Field_("symbol", "symbol", "A_INSTRUMENT", "cat"),
    Field_("direction", "direction", "A_INSTRUMENT", "cat"),
    Field_("origin_family", "origin_family", "A_INSTRUMENT", "cat"),
    Field_("framework", "framework", "A_INSTRUMENT", "cat"),
    Field_("route_family", "route_family", "A_INSTRUMENT", "cat"),
    Field_("setup_family", "setup_family", "A_INSTRUMENT", "cat"),
    Field_("bucket_source_family", "bucket_source_family", "A_INSTRUMENT", "cat"),
    Field_("dynamic_geometry_policy", "dynamic_geometry_policy", "A_INSTRUMENT", "cat"),
    Field_("selected_policy_for_expected_net_r", "selected_policy_for_expected_net_r",
           "A_INSTRUMENT", "cat"),
    Field_("decision_timeframe", "decision_timeframe", "A_INSTRUMENT", "cat"),
    Field_("market_timeframe", "market_timeframe", "A_INSTRUMENT", "cat"),
    # --- B: time and session -----------------------------------------------------------
    Field_("session_bucket", "session_bucket", "B_TIME", "cat"),
    Field_("authority_session", "authority_session", "B_TIME", "cat"),
    Field_("kill_zone", "kill_zone", "B_TIME", "cat"),
    Field_("route_session", "route_session", "B_TIME", "cat"),
    Field_("utc_hour_bucket", "utc_hour_bucket", "B_TIME", "cat"),
    # --- C: cost and microstructure ----------------------------------------------------
    Field_("spread_r", "spread_r", "C_COST", "num"),
    Field_("cost_r", "cost_r", "C_COST", "num"),
    Field_("expected_cost_r", "expected_cost_r", "C_COST", "num"),
    Field_("commission_r", "commission_r", "C_COST", "num"),
    Field_("swap_cost_r", "swap_cost_r", "C_COST", "num"),
    Field_("expected_slippage_r", "expected_slippage_r", "C_COST", "num"),
    Field_("fallback_execution_surcharge_r", "fallback_execution_surcharge_r", "C_COST", "num"),
    Field_("guarded_market_fallback_extra_cost_r", "guarded_market_fallback_extra_cost_r",
           "C_COST", "num"),
    Field_("old_proxy_vs_broker_calibrated_delta_r", "old_proxy_vs_broker_calibrated_delta_r",
           "C_COST", "num"),
    Field_("broker_pretrade_cost_executable", "broker_pretrade_cost_executable", "C_COST", "bool"),
    Field_("broker_pretrade_diag_expected_cost_r",
           "broker_pretrade_cost_non_executable_diagnostic_expected_cost_r", "C_COST", "num"),
    # --- D: the model's own predecision scores -----------------------------------------
    Field_("candidate_probability", "candidate_probability", "D_SCORE", "num"),
    Field_("candidate_ev_r", "candidate_ev_r", "D_SCORE", "num"),
    Field_("expectancy_r", "expectancy_r", "D_SCORE", "num"),
    Field_("expected_net_r", "expected_net_r", "D_SCORE", "num"),
    Field_("candidate_confidence", "candidate_confidence", "D_SCORE", "num"),
    Field_("confidence_default_applied", "confidence_missing_degraded_default_applied",
           "D_SCORE", "bool"),
    Field_("fill_probability", "fill_probability", "D_SCORE", "num"),
    Field_("entry_quality_fill_probability",
           "candidate_decision_quality.entry_quality_fill_probability", "D_SCORE", "num"),
    Field_("execution_fill_probability",
           "candidate_decision_quality.execution_fill_probability", "D_SCORE", "num"),
    Field_("limit_fillability_probability",
           "candidate_decision_quality.limit_fillability_probability", "D_SCORE", "num"),
    Field_("source_completeness", "source_completeness", "D_SCORE", "num"),
    Field_("source_bound_signal_r", "source_bound_signal_r", "D_SCORE", "num"),
    Field_("matched_sleeve_count", "ultimate_package_matched_sleeve_count", "D_SCORE", "num"),
    Field_("effective_admission_count", "ultimate_package_effective_admission_count",
           "D_SCORE", "num"),
    # --- E: selector / scheduler state -------------------------------------------------
    Field_("selector_action", "selector_action", "E_SELECTOR", "cat"),
    Field_("selector_reason", "selector_reason", "E_SELECTOR", "cat"),
    Field_("effective_selector_action", "effective_selector_action", "E_SELECTOR", "cat"),
    Field_("effective_selector_reason", "effective_selector_reason", "E_SELECTOR", "cat"),
    Field_("admission_risk_class", "admission_risk_class", "E_SELECTOR", "cat"),
    Field_("scheduler_materialization_status", "scheduler_materialization_status",
           "E_SELECTOR", "cat"),
    Field_("scheduler_selection_disposition", "scheduler_selection_disposition",
           "E_SELECTOR", "cat"),
    Field_("risk_finalizer_rank", "risk_finalizer_rank", "E_SELECTOR", "num"),
    Field_("risk_finalizer_reason", "risk_finalizer_reason", "E_SELECTOR", "cat"),
    Field_("miss_reason", "miss_reason", "E_SELECTOR", "cat"),
    Field_("candidate_lifecycle_action", "candidate_lifecycle_action", "E_SELECTOR", "cat"),
    Field_("final_blocker_class",
           "missed_package_replay_order_executable_final_blocker_class", "E_SELECTOR", "cat"),
    Field_("effective_order_type", "effective_order_type", "E_SELECTOR", "cat"),
    Field_("fill_realism_class", "fill_realism_class", "E_SELECTOR", "cat"),
    Field_("fill_realism_executable", "fill_realism_executable", "E_SELECTOR", "bool"),
    Field_("entry_fill_executable", "entry_fill_executable", "E_SELECTOR", "bool"),
    Field_("limit_marketable_at_decision", "limit_marketable_at_decision", "E_SELECTOR", "bool"),
    # --- F: geometry -------------------------------------------------------------------
    Field_("entry_price", "entry_price", "F_GEOMETRY", "num"),
    Field_("stop_loss", "stop_loss", "F_GEOMETRY", "num"),
    Field_("take_profit_1", "take_profit_1", "F_GEOMETRY", "num"),
    Field_("policy_target_r", "policy_target_r", "F_GEOMETRY", "num"),
    Field_("raw_target_r", "raw_target_r", "F_GEOMETRY", "num"),
    Field_("risk_per_trade_pct", "risk_per_trade_pct", "F_GEOMETRY", "num"),
    # --- G: exposure context -----------------------------------------------------------
    Field_("same_symbol_lifecycle_action", "same_symbol_lifecycle_action", "G_CONTEXT", "cat"),
    Field_("same_symbol_exposure_risk_pct", "same_symbol_lifecycle_exposure_risk_pct",
           "G_CONTEXT", "num"),
    Field_("same_side_pending_risk_pct", "same_side_pending_risk_pct", "G_CONTEXT", "num"),
    Field_("opposite_pending_risk_pct", "opposite_pending_risk_pct", "G_CONTEXT", "num"),
)

#: Outcome columns. Deliberately a separate tuple with a separate prefix so a miner that
#: iterates `FEATURE_NAMES` can never see one.
OUTCOME_PROJECTION: tuple[Field_, ...] = (
    Field_("outcome_net_proxy_r", "opportunity_net_proxy_r", "OUTCOME", "num"),
    Field_("outcome_gross_r", "opportunity_gross_r", "OUTCOME", "num"),
    Field_("outcome_close_reason", "opportunity_close_reason", "OUTCOME", "cat"),
    Field_("outcome_terminal_outcome", "terminal_outcome", "OUTCOME", "cat"),
    Field_("outcome_close_time_utc", "counterfactual_order_close_time_utc", "OUTCOME", "time"),
    Field_("outcome_scoreability_status", "missed_opportunity_r_scoreability_status",
           "OUTCOME", "cat"),
)

#: Columns derived in this module rather than read from the row. Each states its formula.
DERIVED: tuple[Field_, ...] = (
    Field_("decision_hour_utc", "derived:decision_time_utc.hour", "B_TIME", "num"),
    Field_("decision_dow", "derived:decision_time_utc.weekday()", "B_TIME", "num"),
    Field_("decision_dom", "derived:decision_time_utc.day", "B_TIME", "num"),
    Field_("stop_distance_frac", "derived:abs(entry-stop)/abs(entry)", "F_GEOMETRY", "num",
           "A unitless volatility/stop-width proxy comparable across the 24-symbol surface."),
    Field_("rr_ratio", "derived:abs(tp1-entry)/abs(entry-stop)", "F_GEOMETRY", "num"),
    Field_("cost_over_rr", "derived:cost_r/rr_ratio", "C_COST", "num",
           "Cost charged per unit of reward the geometry offers."),
    Field_("ev_minus_cost", "derived:candidate_ev_r - cost_r", "D_SCORE", "num"),
    Field_("outcome_hold_hours", "derived:(close_time-decision_time)/3600", "OUTCOME", "num"),
    Field_("outcome_is_level_exit",
           "derived:outcome_terminal_outcome in LEVEL_EXIT_TERMINAL_OUTCOMES", "OUTCOME", "bool"),
    Field_("outcome_net_proxy_r_f31",
           "derived:outcome_net_proxy_r + F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW "
           "if outcome_is_level_exit else outcome_net_proxy_r", "OUTCOME", "num",
           "The F31-charged outcome. JANUARY_BANK section 4 requires this before any "
           "economic claim; the raw column is retained so the two are comparable."),
)

FEATURE_FIELDS: tuple[Field_, ...] = tuple(
    f for f in PROJECTION + DERIVED if f.family not in ("ID", "OUTCOME")
)
FEATURE_NAMES: tuple[str, ...] = tuple(f.name for f in FEATURE_FIELDS)
OUTCOME_NAMES: tuple[str, ...] = tuple(
    f.name for f in OUTCOME_PROJECTION + tuple(d for d in DERIVED if d.family == "OUTCOME")
)
ALL_COLUMNS: tuple[str, ...] = (
    ("arm_id", "window")
    + tuple(f.name for f in PROJECTION)
    + tuple(f.name for f in DERIVED)
    + tuple(f.name for f in OUTCOME_PROJECTION)
)

SCHEMA = "gtos.b7_5.diagnostic_pool.v1"

# ---------------------------------------------------------------------------------------
# streaming
# ---------------------------------------------------------------------------------------

#: The analyzer's own diagnostic predicate, as bytes, for a pre-parse skip.
#: `analyze_b7_5_selection_sizing_matrix.py:750-754` — a row is diagnostic-scoreable when
#: `missed_opportunity_non_executable_diagnostic_scoreable is True` OR
#: `missed_opportunity_r_scoreability_status == "diagnostic_opportunity_r_scoreable"`.
#: The ledgers are written with `", "` / `": "` separators; the seal check below is what
#: proves this prefilter drops nothing.
_DIAG_MARKERS: tuple[bytes, ...] = (
    b'"missed_opportunity_non_executable_diagnostic_scoreable": true',
    b'"missed_opportunity_r_scoreability_status": "diagnostic_opportunity_r_scoreable"',
)


_COLD_EVIDENCE_READER = (
    REPO_ROOT
    / "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
    / "b7_5_cold_evidence.py"
)
_COLD_MODULE_NAME = "b7_5_cold_evidence_for_diagnostic_pool"


def cold_evidence_module():
    """Import the route's sealed reader by path — the route is not a package.

    Cached in `sys.modules` under a private name, matching
    `replay_differential_harness._cold_evidence_module`: a second module object would
    break pickling for any caller that later parallelises over these rows.
    """

    import importlib.util
    import sys

    existing = sys.modules.get(_COLD_MODULE_NAME)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(_COLD_MODULE_NAME, _COLD_EVIDENCE_READER)
    if spec is None or spec.loader is None:
        raise DiagnosticPoolError(f"cold_evidence_reader_unloadable:{_COLD_EVIDENCE_READER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_COLD_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _resolver():
    return cold_evidence_module().RawOrColdResolver()


def _dig(row: Mapping[str, Any], path: str) -> Any:
    if "." not in path:
        return row.get(path)
    cur: Any = row
    for part in path.split("."):
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(part)
    return cur


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _parse_utc(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def is_diagnostic_scoreable(row: Mapping[str, Any]) -> bool:
    """The analyzer's predicate, on a parsed row. Kept beside the byte markers."""

    return bool(
        row.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
        or str(row.get("missed_opportunity_r_scoreability_status") or "")
        == "diagnostic_opportunity_r_scoreable"
    )


def project(row: Mapping[str, Any], *, arm: ArmSpec) -> dict[str, Any]:
    """One ledger row -> one typed pool row. Pure; no I/O."""

    out: dict[str, Any] = {"arm_id": arm.arm_id, "window": arm.window}
    for f in PROJECTION:
        value = _dig(row, f.source)
        out[f.name] = _num(value) if f.kind == "num" else value
    for f in OUTCOME_PROJECTION:
        value = _dig(row, f.source)
        out[f.name] = _num(value) if f.kind == "num" else value

    decided = _parse_utc(out.get("decision_time_utc"))
    out["decision_hour_utc"] = float(decided.hour) if decided else None
    out["decision_dow"] = float(decided.weekday()) if decided else None
    out["decision_dom"] = float(decided.day) if decided else None

    entry, stop, tp1 = out.get("entry_price"), out.get("stop_loss"), out.get("take_profit_1")
    stop_dist = abs(entry - stop) if (entry is not None and stop is not None) else None
    out["stop_distance_frac"] = (
        stop_dist / abs(entry) if (stop_dist is not None and entry) else None
    )
    out["rr_ratio"] = (
        abs(tp1 - entry) / stop_dist
        if (tp1 is not None and entry is not None and stop_dist)
        else None
    )
    cost = out.get("cost_r")
    out["cost_over_rr"] = (
        cost / out["rr_ratio"] if (cost is not None and out["rr_ratio"]) else None
    )
    ev = out.get("candidate_ev_r")
    out["ev_minus_cost"] = ev - cost if (ev is not None and cost is not None) else None

    closed = _parse_utc(out.get("outcome_close_time_utc"))
    out["outcome_hold_hours"] = (
        (closed - decided).total_seconds() / 3600.0 if (closed and decided) else None
    )
    is_level = out.get("outcome_terminal_outcome") in LEVEL_EXIT_TERMINAL_OUTCOMES
    out["outcome_is_level_exit"] = is_level
    net = out.get("outcome_net_proxy_r")
    out["outcome_net_proxy_r_f31"] = (
        net + F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW if (net is not None and is_level) else net
    )
    return out


@dataclass
class ArmCounts:
    """The six numbers the sealed matrix audit publishes, recomputed."""

    rows: int = 0
    diagnostic_scoreable_rows: int = 0
    diagnostic_positive_rows: int = 0
    diagnostic_negative_rows: int = 0
    diagnostic_flat_rows: int = 0
    diagnostic_positive_net_r: float = 0.0
    diagnostic_negative_net_r: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "diagnostic_scoreable_rows": self.diagnostic_scoreable_rows,
            "diagnostic_positive_rows": self.diagnostic_positive_rows,
            "diagnostic_negative_rows": self.diagnostic_negative_rows,
            "diagnostic_flat_rows": self.diagnostic_flat_rows,
            "diagnostic_positive_net_r": round(self.diagnostic_positive_net_r, 8),
            "diagnostic_negative_net_r": round(self.diagnostic_negative_net_r, 8),
        }


def iter_arm_rows(
    arm: ArmSpec,
    *,
    root: Path | None = None,
    counts: ArmCounts | None = None,
    prefilter: bool = True,
) -> Iterator[dict[str, Any]]:
    """Stream one arm's diagnostic-scoreable rows, projected.

    `counts` (if given) accumulates the sealed-audit comparison numbers as a side effect:
    `rows` counts EVERY physical row, diagnostic or not, so the total is comparable with
    `arms.<id>.missed_outcomes.rows` even under the prefilter.
    """

    path = arm.ledger_path(root)
    resolver = _resolver()
    if not resolver.exists(path):
        raise DiagnosticPoolError(f"ledger_missing:{arm.arm_id}:{path}")
    seen_keys: set[str] = set()
    with resolver.open_binary(path) as handle:
        for raw in handle:
            if not raw.strip():
                continue
            if counts is not None:
                counts.rows += 1
            if prefilter and not any(marker in raw for marker in _DIAG_MARKERS):
                continue
            row = json.loads(raw)
            if not is_diagnostic_scoreable(row):
                continue
            projected = project(row, arm=arm)
            key = projected.get("candidate_instance_key") or ""
            if not key:
                raise DiagnosticPoolError(f"missed_identity_missing:{arm.arm_id}")
            if key in seen_keys:
                raise DiagnosticPoolError(f"missed_identity_duplicate:{arm.arm_id}:{key}")
            seen_keys.add(key)
            if counts is not None:
                net = projected["outcome_net_proxy_r"]
                if net is None:
                    raise DiagnosticPoolError(
                        f"diagnostic_row_without_net_proxy_r:{arm.arm_id}:{key}"
                    )
                counts.diagnostic_scoreable_rows += 1
                if net > 0:
                    counts.diagnostic_positive_rows += 1
                    counts.diagnostic_positive_net_r += net
                elif net < 0:
                    counts.diagnostic_negative_rows += 1
                    counts.diagnostic_negative_net_r += net
                else:
                    counts.diagnostic_flat_rows += 1
            yield projected


# ---------------------------------------------------------------------------------------
# building and verifying
# ---------------------------------------------------------------------------------------


def sealed_arm_counts(audit_path: Path | None = None) -> dict[str, dict[str, Any]]:
    """`arms.<id>.missed_outcomes` from the sealed January matrix audit."""

    path = Path(audit_path) if audit_path is not None else SEALED_JANUARY_MATRIX_AUDIT
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {arm: dict(body["missed_outcomes"]) for arm, body in payload["arms"].items()}


def compare_to_seal(
    arm_id: str, observed: ArmCounts, sealed: Mapping[str, Any]
) -> dict[str, Any]:
    """Field-by-field comparison. Floats to 8 dp, which is the audit's own rounding."""

    obs = observed.as_dict()
    mismatches = []
    for key in (
        "rows",
        "diagnostic_scoreable_rows",
        "diagnostic_positive_rows",
        "diagnostic_negative_rows",
        "diagnostic_flat_rows",
        "diagnostic_positive_net_r",
        "diagnostic_negative_net_r",
    ):
        if key not in sealed:
            continue
        want, got = sealed[key], obs[key]
        if isinstance(want, float) or isinstance(got, float):
            ok = abs(float(want) - float(got)) <= 1e-6
        else:
            ok = want == got
        if not ok:
            mismatches.append({"field": key, "sealed": want, "observed": got})
    return {
        "arm_id": arm_id,
        "observed": obs,
        "sealed": {k: sealed[k] for k in sorted(sealed)},
        "mismatches": mismatches,
        "matches_seal": not mismatches,
    }


def build_pool(
    arm_ids: Sequence[str] = JANUARY_ARMS,
    *,
    out_path: Path | None = None,
    root: Path | None = None,
    audit_path: Path | None = None,
    on_row: Any = None,
) -> dict[str, Any]:
    """Stream the named arms, write a gzipped JSONL pool, and check it against the seal.

    Returns the manifest. Writing is optional — pass `out_path=None` to get the counts and
    the seal comparison without materialising anything.
    """

    sealed = sealed_arm_counts(audit_path) if audit_path is not False else {}
    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "ledger_root": str(root or DEFAULT_LEDGER_ROOT),
        "sealed_audit": str(
            Path(audit_path) if audit_path else SEALED_JANUARY_MATRIX_AUDIT
        ),
        "f31_gap_through_r_per_level_exit_row": F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW,
        "columns": list(ALL_COLUMNS),
        "feature_names": list(FEATURE_NAMES),
        "outcome_names": list(OUTCOME_NAMES),
        "arms": {},
        "seal_comparison": {},
    }
    handle = None
    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        handle = gzip.open(out_path, "wt", encoding="utf-8", compresslevel=6)
    try:
        for arm_id in arm_ids:
            arm = ARMS[arm_id]
            counts = ArmCounts()
            for projected in iter_arm_rows(arm, root=root, counts=counts):
                if handle is not None:
                    handle.write(json.dumps(projected, separators=(",", ":")) + "\n")
                if on_row is not None:
                    on_row(projected)
            manifest["arms"][arm_id] = {
                "window": arm.window,
                "ledger": str(arm.ledger_path(root)),
                "selection_factor": arm.selection_factor,
                "sizing_factor": arm.sizing_factor,
                **counts.as_dict(),
            }
            if arm_id in sealed:
                manifest["seal_comparison"][arm_id] = compare_to_seal(
                    arm_id, counts, sealed[arm_id]
                )
    finally:
        if handle is not None:
            handle.close()
    if out_path is not None:
        manifest["pool_path"] = str(out_path)
    checked = [c for c in manifest["seal_comparison"].values()]
    manifest["all_arms_match_seal"] = bool(checked) and all(
        c["matches_seal"] for c in checked
    )
    return manifest


def load_pool(path: Path) -> list[dict[str, Any]]:
    """Read a built pool back. Small enough to hold: ~28.5 k rows per January arm."""

    rows = []
    with gzip.open(Path(path), "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def pool_summary(rows: Iterable[Mapping[str, Any]], *, outcome: str = "outcome_net_proxy_r") -> dict:
    """The four numbers a reader needs before believing any separability claim.

    `breakeven_precision` is the share of selected rows that must be winners for a
    selector to break even at the pool's own conditional means — the honest bar, and the
    reason "±38,317 R of separable opportunity" is not the capturable quantity.
    """

    pos = [float(r[outcome]) for r in rows if r.get(outcome) is not None and r[outcome] > 0]
    neg = [float(r[outcome]) for r in rows if r.get(outcome) is not None and r[outcome] < 0]
    flat = sum(1 for r in rows if r.get(outcome) == 0)
    n = len(pos) + len(neg) + flat
    mean_pos = sum(pos) / len(pos) if pos else 0.0
    mean_neg = sum(neg) / len(neg) if neg else 0.0
    denom = mean_pos - mean_neg
    return {
        "outcome_column": outcome,
        "rows": n,
        "positive_rows": len(pos),
        "negative_rows": len(neg),
        "flat_rows": flat,
        "positive_net_r": round(sum(pos), 8),
        "negative_net_r": round(sum(neg), 8),
        "pool_net_r": round(sum(pos) + sum(neg), 8),
        "base_rate": round(len(pos) / n, 6) if n else None,
        "mean_positive_r": round(mean_pos, 6),
        "mean_negative_r": round(mean_neg, 6),
        "mean_r_per_row": round((sum(pos) + sum(neg)) / n, 6) if n else None,
        "breakeven_precision": round(-mean_neg / denom, 6) if denom else None,
    }


__all__ = [
    "ALL_COLUMNS",
    "ARMS",
    "ArmCounts",
    "ArmSpec",
    "DERIVED",
    "DiagnosticPoolError",
    "F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW",
    "FEATURE_FIELDS",
    "FEATURE_NAMES",
    "JANUARY_ARMS",
    "LEVEL_EXIT_TERMINAL_OUTCOMES",
    "OUTCOME_NAMES",
    "OUTCOME_PROJECTION",
    "PROJECTION",
    "SCHEMA",
    "build_pool",
    "compare_to_seal",
    "is_diagnostic_scoreable",
    "iter_arm_rows",
    "load_pool",
    "pool_summary",
    "project",
    "sealed_arm_counts",
]
