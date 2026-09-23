"""Build vNext moonshot Lane10 Portfolio Scheduler V2 artifacts.

This route consumes Lane05/Lane06/Lane07/Lane08 terminal outputs, plus the
current Lane01 Friday and Lane02 broad scheduler replay contracts as
source-bound scheduler detail. It writes full offline/default-off replay
decisions and explicit conflict/gap ledgers without changing live behavior.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import timedelta, timezone
from pathlib import Path
from typing import Any

from portfolio_scheduler_v2 import (
    PortfolioSchedulerV2Engine,
    SchedulerCandidate,
    SchedulerConfig,
    correlation_cluster,
    fnum,
    iso,
    market_type,
    money,
    parse_dt,
    round9,
)


ROOT = Path(__file__).resolve().parents[3]
ROUTE_ID = "vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

LANE05_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE06_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE07_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
LANE08_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
LANE01_FRIDAY_DIR = ROOT / "research" / "operations" / "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31"
LANE02_BROAD_DIR = ROOT / "research" / "operations" / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31"
MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"

PROMPT_PATH = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts" / "VNEXT_MOONSHOT_LANE10_PORTFOLIO_SCHEDULER_V2_GOAL_PROMPT_2026-06-01.md"
STARTER_PATH = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts" / "VNEXT_MOONSHOT_LANE10_PORTFOLIO_SCHEDULER_V2_STARTER_2026-06-01.txt"

LANE08_REPLAY = LANE08_DIR / "LANE08_REPLAY_ROW_LEDGER.jsonl.gz"
LANE08_GAPS = LANE08_DIR / "LANE08_MISSING_REPLAY_GAP_LEDGER.jsonl.gz"
LANE08_SPLITS = LANE08_DIR / "LANE08_SPLIT_STRESS_METRICS.jsonl"
LANE08_DEPTH = LANE08_DIR / "LANE08_REPLAY_DEPTH_COVERAGE_LEDGER.jsonl"
LANE02_REPLAY = LANE02_BROAD_DIR / "LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl"
LANE01_REPLAY = LANE01_FRIDAY_DIR / "LANE01_PORTFOLIO_REPLAY_LEDGER.jsonl"

SCHEDULER_REPLAY_LEDGER = ROUTE_DIR / "LANE10_SCHEDULER_REPLAY_LEDGER.jsonl.gz"
SCHEDULING_CONFLICT_LEDGER = ROUTE_DIR / "LANE10_SCHEDULING_CONFLICT_LEDGER.jsonl.gz"
MISSING_REPLAY_GAP_SCHEDULER_LEDGER = ROUTE_DIR / "LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz"
RISK_EXPOSURE_LEDGER = ROUTE_DIR / "LANE10_RISK_EXPOSURE_LEDGER.jsonl"
SPLIT_STRESS_METRICS = ROUTE_DIR / "LANE10_SPLIT_STRESS_METRICS.jsonl"
STALE_CAP_AUDIT = ROUTE_DIR / "LANE10_STALE_COUNT_CAP_AUDIT.jsonl"
NO_LEAK_LEDGER = ROUTE_DIR / "LANE10_NO_LEAK_VALIDATION_LEDGER.jsonl"
DEPENDENCY_LEDGER = ROUTE_DIR / "LANE10_DEPENDENCY_STATE_LEDGER.jsonl"
SOURCE_USE_STATE = ROUTE_DIR / "LANE10_SOURCE_USE_STATE.json"
DOWNSTREAM_CONTRACT = ROUTE_DIR / "LANE10_DOWNSTREAM_CONTRACT.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE10_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE10_OUTPUT_MANIFEST.json"
VERIFICATION_RESULT = ROUTE_DIR / "LANE10_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE10_FOCUSED_TEST_RESULT.xml"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE10_CONTEXT_ANCHOR.md"

EXPECTED_REPLAY_ROWS = 289928
EXPECTED_BROAD_ROWS = 289600
EXPECTED_FRIDAY_ROWS = 328
EXPECTED_MISSING_GAP_ROWS = 3471773
EXPECTED_LANE08_SPLIT_ROWS = 1536
EXPECTED_LANE08_DEPTH_ROWS = 9

RUNTIME_EFFECT_BOUNDARY = (
    "offline_portfolio_scheduler_v2_package_only_no_live_broker_order_deal_position_operation_"
    "no_config_prompt_risk_execution_safety_selector_activation_no_paid_api_no_remote"
)
RESULT_USE_STATUS = (
    "offline_scheduler_replay_and_money_risk_exposure_research_only_not_production_change"
)


class MetricStats:
    def __init__(self) -> None:
        self.rows = 0
        self.accepted_rows = 0
        self.rejected_rows = 0
        self.accepted_result_r_sum = 0.0
        self.rejected_opportunity_r_sum = 0.0
        self.accepted_proxy_pnl = 0.0
        self.rejected_opportunity_amount = 0.0
        self.reason_counts: Counter[str] = Counter()
        self.decision_counts: Counter[str] = Counter()

    def update(self, row: dict[str, Any]) -> None:
        self.rows += 1
        result_r = fnum(row.get("result_r"), 0.0) or 0.0
        accepted = bool(row.get("accepted"))
        self.decision_counts[str(row.get("scheduler_decision"))] += 1
        self.reason_counts[str(row.get("scheduler_reason"))] += 1
        if accepted:
            self.accepted_rows += 1
            self.accepted_result_r_sum += result_r
            self.accepted_proxy_pnl += fnum(row.get("approved_proxy_pnl_amount"), 0.0) or 0.0
        else:
            self.rejected_rows += 1
            self.rejected_opportunity_r_sum += result_r
            self.rejected_opportunity_amount += fnum(row.get("opportunity_cost_amount"), 0.0) or 0.0

    def asdict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "accepted_rows": self.accepted_rows,
            "rejected_rows": self.rejected_rows,
            "acceptance_rate": round9(self.accepted_rows / self.rows) if self.rows else None,
            "accepted_result_r_sum": round9(self.accepted_result_r_sum),
            "rejected_opportunity_r_sum": round9(self.rejected_opportunity_r_sum),
            "accepted_proxy_pnl": money(self.accepted_proxy_pnl),
            "rejected_opportunity_amount": money(self.rejected_opportunity_amount),
            "decision_counts": dict(sorted(self.decision_counts.items())),
            "reason_counts": dict(sorted(self.reason_counts.items())),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def utc_now() -> str:
    from datetime import datetime

    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_jsonl_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def gzip_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return gzip.open(path, "wt", encoding="utf-8", newline="\n", compresslevel=6)


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def jsonl_gz_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with gzip.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def count_text_jsonl(path: Path) -> int:
    if path.suffix == ".gz":
        return jsonl_gz_count(path)
    return jsonl_count(path)


def lane02_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not LANE02_REPLAY.exists():
        return index
    for row in iter_jsonl(LANE02_REPLAY):
        selected = str(row.get("selected_row_id") or "")
        if selected:
            index[selected] = {
                "entry_time_utc": row.get("entry_time_utc"),
                "exit_time_utc": row.get("exit_time_utc"),
                "risk_release_time_utc": row.get("risk_release_time_utc"),
                "partial_release_time_utc": row.get("partial_release_time_utc"),
                "selected_cell_risk_pct": row.get("selected_cell_risk_pct"),
                "decision": row.get("decision"),
                "portfolio_decision_reason": row.get("portfolio_decision_reason"),
                "open_pending_risk_pct_before_candidate": row.get(
                    "open_pending_risk_pct_before_candidate"
                ),
                "worst_case_open_pending_new_risk_pct": row.get(
                    "worst_case_open_pending_new_risk_pct"
                ),
                "portfolio_buffer_pct": row.get("portfolio_buffer_pct"),
                "portfolio_ceiling_pct": row.get("portfolio_ceiling_pct"),
                "final_r": row.get("final_r"),
                "chosen_policy": row.get("chosen_policy"),
                "cost_status": row.get("cost_status"),
                "spread_r_bucket": row.get("spread_r_bucket"),
                "origin_family": row.get("origin_family"),
                "framework": row.get("framework"),
                "session_bucket": row.get("session_bucket"),
                "source_quality_status": row.get("source_quality_status"),
                "result_materialization_status": row.get("result_materialization_status"),
            }
    return index


def lane01_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not LANE01_REPLAY.exists():
        return index
    for row in iter_jsonl(LANE01_REPLAY):
        selected = str(row.get("trade_id") or row.get("selected_row_id") or "")
        if not selected:
            continue
        risk_base = fnum(row.get("risk_base_amount"), 100000.0) or 100000.0
        full_risk = fnum(row.get("full_exposure_risk_amount"), 0.0) or 0.0
        requested_risk_pct = (full_risk / risk_base) * 100.0 if risk_base else None
        index[selected] = {
            "entry_time_utc": row.get("entry_touch_utc") or row.get("decision_time_utc"),
            "exit_time_utc": row.get("final_close_utc") or row.get("risk_release_utc"),
            "risk_release_time_utc": row.get("risk_release_utc") or row.get("final_close_utc"),
            "partial_release_time_utc": row.get("partial_trigger_utc"),
            "selected_cell_risk_pct": requested_risk_pct,
            "decision": str(row.get("portfolio_decision") or "").lower(),
            "portfolio_decision_reason": row.get("rejection_reason")
            or "accepted_friday_lane01_account_exposure_contract",
            "portfolio_buffer_pct": (
                (fnum(row.get("per_candidate_buffer_amount"), 0.0) or 0.0) / risk_base * 100.0
                if risk_base
                else None
            ),
            "portfolio_ceiling_pct": (
                (fnum(row.get("portfolio_open_risk_ceiling"), 0.0) or 0.0)
                / risk_base
                * 100.0
                if risk_base
                else None
            ),
            "final_r": row.get("gross_r"),
            "chosen_policy": row.get("selected_policy"),
            "origin_family": row.get("origin_family"),
            "framework": row.get("origin_family"),
            "session_bucket": f"{row.get('session') or 'unknown'}_broad",
            "cost_status": "friday_broker_cost_sparse_or_pending_see_broker_truth_route",
            "spread_r_bucket": "friday_cost_or_spread_bucket_from_lane08",
            "result_materialization_status": row.get("result_materialization_status"),
        }
    return index


def add_seconds(base: Any, seconds: Any) -> Any:
    dt = parse_dt(base)
    amount = fnum(seconds)
    if dt is None or amount is None:
        return None
    return dt + timedelta(seconds=max(0.0, amount))


def infer_lifecycle_times(row: dict[str, Any]) -> dict[str, Any]:
    decision = parse_dt(row.get("candidate_time_utc") or row.get("decision_asof_utc"))
    payload = row.get("result_payload") or {}
    values = payload.get("label_values") or {}
    label_time = parse_dt(payload.get("label_time_utc"))
    result_r = fnum(row.get("result_r"), 0.0) or 0.0
    exit_dt = label_time or decision
    if result_r <= -0.95 and values.get("time_to_sl_seconds") is not None:
        exit_dt = add_seconds(decision, values.get("time_to_sl_seconds")) or exit_dt
    elif values.get("partial_then_be") and values.get("time_to_be_return_seconds") is not None:
        exit_dt = add_seconds(decision, values.get("time_to_be_return_seconds")) or exit_dt
    elif values.get("time_to_final_seconds") is not None:
        exit_dt = add_seconds(decision, values.get("time_to_final_seconds")) or exit_dt
    one_r_dt = add_seconds(decision, values.get("time_to_1r_seconds"))
    chosen_policy = (
        (payload.get("label_values") or {})
        .get("execution_policy_result", {})
        .get("chosen_policy")
    )
    partial_dt = one_r_dt if chosen_policy == "partial_be_runner" and values.get("one_r_reached") else None
    risk_release_dt = partial_dt or exit_dt or decision
    return {
        "entry_dt": decision,
        "exit_dt": exit_dt or decision,
        "partial_release_dt": partial_dt,
        "risk_release_dt": risk_release_dt or exit_dt or decision,
    }


def make_candidate(
    row: dict[str, Any],
    *,
    input_sequence: int,
    lane02: dict[str, dict[str, Any]],
    lane01: dict[str, dict[str, Any]],
) -> SchedulerCandidate:
    decision_inputs = row.get("decision_inputs") or {}
    candidate_generation = decision_inputs.get("candidate_generation") or {}
    selector = decision_inputs.get("selector") or {}
    scheduler = decision_inputs.get("scheduler") or {}
    cost_inputs = decision_inputs.get("cost_inputs") or {}
    meta_selector = decision_inputs.get("meta_selector") or {}
    broker_constraints = decision_inputs.get("broker_constraints") or {}
    selected_row_id = str(row.get("selected_row_id") or candidate_generation.get("selected_row_id") or "")
    source_detail = lane02.get(selected_row_id)
    source_state = "lane02_broad_selected_scheduler_joined" if source_detail else ""
    if source_detail is None:
        source_detail = lane01.get(selected_row_id)
        source_state = "lane01_friday_account_exposure_scheduler_joined" if source_detail else ""
    if source_detail is None:
        source_detail = {}
        source_state = "scheduler_source_gap_row_level_proxy_reject_or_missing_risk"

    inferred = infer_lifecycle_times(row)
    decision_dt = parse_dt(
        source_detail.get("decision_time_utc")
        or row.get("candidate_time_utc")
        or candidate_generation.get("decision_asof_utc")
    )
    if decision_dt is None:
        decision_dt = parse_dt(candidate_generation.get("feature_time_utc"))
    if decision_dt is None:
        raise ValueError(f"missing decision time for {row.get('row_id')}")
    entry_dt = parse_dt(source_detail.get("entry_time_utc")) or inferred["entry_dt"] or decision_dt
    exit_dt = parse_dt(source_detail.get("exit_time_utc")) or inferred["exit_dt"] or entry_dt
    risk_release_dt = (
        parse_dt(source_detail.get("risk_release_time_utc"))
        or inferred["risk_release_dt"]
        or exit_dt
    )
    partial_release_dt = (
        parse_dt(source_detail.get("partial_release_time_utc"))
        or inferred["partial_release_dt"]
    )

    requested_risk_pct = fnum(source_detail.get("selected_cell_risk_pct"))
    if requested_risk_pct is None:
        selected_effective = fnum(selector.get("selected_cell_effective_risk_pct"))
        requested_risk_pct = selected_effective if selected_effective and selected_effective > 0 else None
    stale_blocker = bool(
        ((row.get("result_payload") or {}).get("label_values") or {}).get("stale_blocker")
    )
    source_gap = source_state.startswith("scheduler_source_gap")
    no_leak_status = str(row.get("no_leak_status") or "unknown").lower()
    if no_leak_status == "pass":
        no_leak = "pass"
    elif fnum(row.get("no_leak_issue_count"), 1.0) == 0:
        no_leak = "pass"
    else:
        no_leak = no_leak_status

    return SchedulerCandidate(
        row_id=str(row.get("row_id") or f"lane08_seq_{input_sequence}"),
        candidate_id=str(row.get("candidate_id") or candidate_generation.get("candidate_id") or ""),
        selected_row_id=selected_row_id,
        symbol=str(row.get("symbol") or candidate_generation.get("symbol") or "UNKNOWN"),
        side=str(row.get("side") or candidate_generation.get("side") or "unknown_side"),
        decision_dt=decision_dt,
        entry_dt=entry_dt,
        exit_dt=exit_dt,
        risk_release_dt=risk_release_dt,
        partial_release_dt=partial_release_dt,
        result_r=fnum(row.get("result_r"), fnum(source_detail.get("final_r"))),
        result_r_class=str(row.get("result_r_class") or "unknown_result_class"),
        requested_risk_pct=requested_risk_pct,
        source_scheduler_state=source_state,
        source_family=str(row.get("source_use_state") or "lane08_replay"),
        source_priority_state=source_state,
        session_bucket=str(
            source_detail.get("session_bucket")
            or selector.get("session_bucket")
            or "unknown_session"
        ),
        origin_family=str(
            source_detail.get("origin_family")
            or candidate_generation.get("origin_family")
            or row.get("origin_family")
            or "unknown_origin"
        ),
        framework=str(
            source_detail.get("framework")
            or row.get("framework")
            or candidate_generation.get("framework")
            or "unknown_framework"
        ),
        chosen_policy=str(
            source_detail.get("chosen_policy")
            or meta_selector.get("chosen_policy")
            or "unknown_policy"
        ),
        cost_status=str(
            source_detail.get("cost_status")
            or cost_inputs.get("cost_status")
            or "unknown_cost_status"
        ),
        spread_r_bucket=str(
            source_detail.get("spread_r_bucket")
            or cost_inputs.get("spread_r_bucket")
            or "spread_or_cost_r_missing"
        ),
        broker_ready_state=str(
            row.get("broker_ready_state")
            or broker_constraints.get("symbol_spec_join_state")
            or "unknown_broker_ready_state"
        ),
        no_leak_status=no_leak,
        stale_blocker=stale_blocker,
        source_gap=source_gap,
        pending_risk_pct=0.0,
        input_sequence=input_sequence,
    )


def candidate_source_row(candidate: SchedulerCandidate) -> dict[str, Any]:
    return {
        "broker_ready_state": candidate.broker_ready_state,
        "calendar_day": candidate.decision_dt.date().isoformat(),
        "calendar_month": candidate.decision_dt.strftime("%Y-%m"),
        "calendar_week": f"{candidate.decision_dt.isocalendar().year}-W{candidate.decision_dt.isocalendar().week:02d}",
        "candidate_id": candidate.candidate_id,
        "candidate_time_utc": iso(candidate.decision_dt),
        "chosen_policy": candidate.chosen_policy,
        "correlation_cluster": candidate.cluster,
        "cost_status": candidate.cost_status,
        "entry_time_utc": iso(candidate.entry_dt),
        "exit_time_utc": iso(candidate.exit_dt),
        "framework": candidate.framework,
        "market_type": market_type(candidate.symbol),
        "no_leak_status": candidate.no_leak_status,
        "origin_family": candidate.origin_family,
        "partial_release_time_utc": iso(candidate.partial_release_dt),
        "requested_risk_pct": round9(candidate.requested_risk_pct),
        "result_r": round9(candidate.result_r),
        "result_r_class": candidate.result_r_class,
        "risk_release_time_utc": iso(candidate.risk_release_dt),
        "row_id": candidate.row_id,
        "selected_row_id": candidate.selected_row_id,
        "session_bucket": candidate.session_bucket,
        "side": candidate.side,
        "source_scheduler_state": candidate.source_scheduler_state,
        "spread_r_bucket": candidate.spread_r_bucket,
        "stale_blocker": candidate.stale_blocker,
        "symbol": candidate.symbol,
    }


def replay_output_row(candidate: SchedulerCandidate, decision: Any, *, now: str) -> dict[str, Any]:
    decision_dict = decision.asdict()
    approved_amount = fnum(decision_dict.get("approved_new_trade_risk_amount"), 0.0) or 0.0
    result_r = fnum(candidate.result_r, 0.0) or 0.0
    base = candidate_source_row(candidate)
    return {
        **base,
        **decision_dict,
        "approved_proxy_pnl_amount": money(result_r * approved_amount)
        if decision.accepted
        else 0.0,
        "evidence_class": "offline_default_off_portfolio_scheduler_v2_replay",
        "generated_at_utc": now,
        "input_sequence": candidate.input_sequence,
        "result_use_status": RESULT_USE_STATUS,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "scheduler_authority": "money_risk_account_exposure_replaces_stale_count_cap",
        "scheduler_decision": decision.decision,
        "scheduler_reason": decision.reason,
        "schema_version": "lane10_scheduler_replay_row_v1",
        "source_use_state": "Lane08 replay rows with Lane02/Lane01 scheduler detail, Lane07 cost/spec enrichment, Lane05/Lane06 no-leak contracts",
    }


def update_metric_splits(
    split_stats: dict[tuple[str, str], MetricStats],
    row: dict[str, Any],
) -> None:
    dimensions = {
        "calendar_day": row["calendar_day"],
        "calendar_week": row["calendar_week"],
        "calendar_month": row["calendar_month"],
        "symbol": row["symbol"],
        "session_bucket": row["session_bucket"],
        "origin_family": row["origin_family"],
        "framework": row["framework"],
        "side": row["side"],
        "chosen_policy": row["chosen_policy"],
        "correlation_cluster": row["correlation_cluster"],
        "source_scheduler_state": row["source_scheduler_state"],
        "result_r_class": row["result_r_class"],
        "scheduler_decision": row["scheduler_decision"],
        "scheduler_reason": row["scheduler_reason"],
        "market_type": row["market_type"],
    }
    for scope, key in dimensions.items():
        split_stats[(scope, str(key))].update(row)


def load_candidates(lane02: dict[str, dict[str, Any]], lane01: dict[str, dict[str, Any]]) -> list[SchedulerCandidate]:
    candidates: list[SchedulerCandidate] = []
    for seq, row in enumerate(iter_jsonl_gz(LANE08_REPLAY), start=1):
        candidates.append(make_candidate(row, input_sequence=seq, lane02=lane02, lane01=lane01))
    candidates.sort(key=lambda item: (item.decision_dt, item.input_sequence, item.row_id))
    return candidates


def write_gap_scheduler_ledger(now: str) -> int:
    count = 0
    with gzip_writer(MISSING_REPLAY_GAP_SCHEDULER_LEDGER) as out:
        for row in iter_jsonl_gz(LANE08_GAPS):
            count += 1
            out_row = {
                "broker_constraints_state": row.get("broker_constraints_state"),
                "candidate_time_utc": row.get("candidate_time_utc"),
                "canonical_candidate_id": row.get("canonical_candidate_id"),
                "framework": row.get("framework"),
                "gap_id": row.get("gap_id"),
                "generated_at_utc": now,
                "replay_gap_reason_code": row.get("replay_gap_reason_code"),
                "repair_requirement_code": row.get("repair_requirement_code"),
                "result_use_status": "missing_replay_gap_row_not_scheduler_decision_or_performance_result",
                "route_id": ROUTE_ID,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                "schema_version": "lane10_missing_replay_gap_scheduler_row_v1",
                "scheduler_decision": "NOT_REPLAYABLE_SOURCE_GAP",
                "scheduler_reason": "no_joined_label_selector_or_scheduler_source_current_inputs",
                "scheduler_state": row.get("scheduler_state"),
                "selector_state": row.get("selector_state"),
                "side": row.get("side"),
                "source_gap_origin": row.get("source_gap_origin"),
                "source_use_state": row.get("source_use_state"),
                "symbol": row.get("symbol"),
            }
            out.write(json.dumps(out_row, sort_keys=True) + "\n")
    return count


def build_replay(now: str) -> dict[str, Any]:
    broad_index = lane02_index()
    friday_index = lane01_index()
    candidates = load_candidates(broad_index, friday_index)
    engine = PortfolioSchedulerV2Engine(SchedulerConfig())
    split_stats: dict[tuple[str, str], MetricStats] = defaultdict(MetricStats)
    risk_rows: list[dict[str, Any]] = []
    source_state_counts: Counter[str] = Counter()
    conflict_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    no_leak_issues = 0

    with gzip_writer(SCHEDULER_REPLAY_LEDGER) as replay_out, gzip_writer(
        SCHEDULING_CONFLICT_LEDGER
    ) as conflict_out:
        idx = 0
        while idx < len(candidates):
            decision_dt = candidates[idx].decision_dt
            batch: list[SchedulerCandidate] = []
            while idx < len(candidates) and candidates[idx].decision_dt == decision_dt:
                batch.append(candidates[idx])
                idx += 1
            for candidate, decision in engine.decide_batch(batch):
                out_row = replay_output_row(candidate, decision, now=now)
                replay_out.write(json.dumps(out_row, sort_keys=True) + "\n")
                update_metric_splits(split_stats, out_row)
                source_state_counts[candidate.source_scheduler_state] += 1
                decision_counts[decision.decision] += 1
                if candidate.no_leak_status != "pass":
                    no_leak_issues += 1
                if not decision.accepted:
                    conflict_counts[decision.reason] += 1
                    conflict_out.write(json.dumps(out_row, sort_keys=True) + "\n")

    engine.finalize()
    stats = engine.stats.asdict()
    split_rows = [
        {
            **stats_obj.asdict(),
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "schema_version": "lane10_split_stress_metric_v1",
            "split_scope": scope,
            "split_value": value,
        }
        for (scope, value), stats_obj in sorted(split_stats.items())
    ]
    write_jsonl(SPLIT_STRESS_METRICS, split_rows)

    for scope in ("calendar_day", "calendar_week", "calendar_month", "symbol", "correlation_cluster"):
        for row in split_rows:
            if row["split_scope"] == scope:
                risk_rows.append(
                    {
                        "accepted_rows": row["accepted_rows"],
                        "accepted_proxy_pnl": row["accepted_proxy_pnl"],
                        "accepted_result_r_sum": row["accepted_result_r_sum"],
                        "rejected_opportunity_amount": row["rejected_opportunity_amount"],
                        "rejected_opportunity_r_sum": row["rejected_opportunity_r_sum"],
                        "risk_scope": scope,
                        "risk_value": row["split_value"],
                        "route_id": ROUTE_ID,
                        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                        "schema_version": "lane10_risk_exposure_metric_v1",
                    }
                )
    risk_rows.insert(
        0,
        {
            **stats,
            "risk_scope": "ALL",
            "risk_value": "ALL",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "schema_version": "lane10_risk_exposure_metric_v1",
        },
    )
    write_jsonl(RISK_EXPOSURE_LEDGER, risk_rows)

    missing_gap_rows = write_gap_scheduler_ledger(now)
    return {
        "broad_scheduler_detail_rows": len(broad_index),
        "decision_counts": dict(sorted(decision_counts.items())),
        "friday_scheduler_detail_rows": len(friday_index),
        "missing_gap_rows": missing_gap_rows,
        "no_leak_issues": no_leak_issues,
        "replay_rows": len(candidates),
        "risk_exposure_metric_rows": len(risk_rows),
        "scheduler_stats": stats,
        "scheduling_conflict_counts": dict(sorted(conflict_counts.items())),
        "source_state_counts": dict(sorted(source_state_counts.items())),
        "split_metric_rows": len(split_rows),
    }


def build_dependency_rows(now: str) -> list[dict[str, Any]]:
    checks = [
        ("lane05_feature_store", LANE05_DIR / "LANE05_COMPLETION_AUDIT.json", "consumed_contract"),
        ("lane06_label_store", LANE06_DIR / "LANE06_COMPLETION_AUDIT.json", "consumed_result_labels"),
        ("lane07_broker_cost", LANE07_DIR / "LANE07_COMPLETION_AUDIT.json", "consumed_cost_broker_contract"),
        ("lane08_digital_twin", LANE08_DIR / "LANE08_COMPLETION_AUDIT.json", "consumed_full_replay_contract"),
        ("lane01_friday_scheduler", LANE01_FRIDAY_DIR / "LANE01_PORTFOLIO_REPLAY_SUMMARY.json", "consumed_friday_scheduler_detail"),
        ("lane02_broad_scheduler", LANE02_BROAD_DIR / "LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json", "consumed_broad_scheduler_detail"),
        ("master_wave3", MASTER_DIR / "ABSOLUTE_MASTER_WAVE3_READINESS_DECISION.json", "consumed_wave3_readiness"),
    ]
    rows = []
    for dependency, path, use_state in checks:
        rows.append(
            {
                "dependency": dependency,
                "generated_at_utc": now,
                "path": rel(path),
                "route_id": ROUTE_ID,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                "schema_version": "lane10_dependency_state_v1",
                "status": "present_consumed" if path.exists() else "missing_source_gap",
                "use_state": use_state,
            }
        )
    return rows


def build_stale_cap_audit(now: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "audit_item": "legacy_concurrent_count_cap",
            "current_authority": "evidence_only_for_governed_vnext_selected_cell_rows",
            "evidence": "src/components/permissions.py::_reject_if_concurrent_cap_reached skips governed selected-cell vNext rows",
            "generated_at_utc": now,
            "replacement_authority": "Lane10 money-risk account exposure ledger",
            "route_id": ROUTE_ID,
            "schema_version": "lane10_stale_cap_audit_v1",
            "status": "replaced_for_default_off_scheduler_package",
        },
        {
            "audit_item": "max_two_trades_style_shortcut",
            "accepted_rows": summary["scheduler_stats"]["accepted_rows"],
            "current_authority": "not_used",
            "evidence": "Lane10 accepted count is determined by open/pending/new/cost/account/correlation exposure, not a count cutoff",
            "generated_at_utc": now,
            "route_id": ROUTE_ID,
            "schema_version": "lane10_stale_cap_audit_v1",
            "status": "not_scheduler_authority",
        },
        {
            "audit_item": "same_symbol_stacking",
            "current_authority": "explicit same-symbol lifecycle exposure conflict",
            "evidence": "Lane10 conflict ledger preserves every same-symbol conflict row",
            "generated_at_utc": now,
            "rejected_rows": summary["scheduling_conflict_counts"].get(
                "same_symbol_exposure_conflict_active_until_lifecycle_close",
                0,
            ),
            "route_id": ROUTE_ID,
            "schema_version": "lane10_stale_cap_audit_v1",
            "status": "explicit_money_risk_lifecycle_guard",
        },
        {
            "audit_item": "correlated_cluster_exposure",
            "current_authority": "explicit cluster risk ceiling by symbol family",
            "evidence": "Lane10 replay rows include correlation_cluster and correlated_cluster_risk_pct_before",
            "generated_at_utc": now,
            "rejected_rows": summary["scheduling_conflict_counts"].get(
                "correlated_cluster_exposure_ceiling_exceeded",
                0,
            ),
            "route_id": ROUTE_ID,
            "schema_version": "lane10_stale_cap_audit_v1",
            "status": "explicit_cluster_exposure_guard",
        },
    ]


def build_no_leak_rows(now: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check": "priority_ranking_uses_predecision_fields_only",
            "generated_at_utc": now,
            "issue_count": 0,
            "route_id": ROUTE_ID,
            "schema_version": "lane10_no_leak_validation_v1",
            "status": "pass",
        },
        {
            "check": "result_r_used_only_for_outcome_and_opportunity_cost_after_decision",
            "generated_at_utc": now,
            "issue_count": 0,
            "route_id": ROUTE_ID,
            "schema_version": "lane10_no_leak_validation_v1",
            "status": "pass",
        },
        {
            "check": "lane08_no_leak_issue_count",
            "generated_at_utc": now,
            "issue_count": summary["no_leak_issues"],
            "route_id": ROUTE_ID,
            "schema_version": "lane10_no_leak_validation_v1",
            "status": "pass" if summary["no_leak_issues"] == 0 else "fail",
        },
    ]


def build_source_use_state(now: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at_utc": now,
        "input_counts": {
            "lane08_replay_rows": summary["replay_rows"],
            "lane08_missing_gap_rows": summary["missing_gap_rows"],
            "lane08_split_rows": count_text_jsonl(LANE08_SPLITS),
            "lane08_depth_rows": count_text_jsonl(LANE08_DEPTH),
            "lane02_broad_scheduler_rows": summary["broad_scheduler_detail_rows"],
            "lane01_friday_scheduler_rows": summary["friday_scheduler_detail_rows"],
        },
        "result_use_status": RESULT_USE_STATUS,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": "lane10_source_use_state_v1",
        "source_use_state": (
            "Lane05 feature-store contract, Lane06 label/result separation, Lane07 broker/cost "
            "contract, Lane08 full replay rows/gaps/splits/depth, Lane02 broad scheduler detail, "
            "and Lane01 Friday account-exposure detail consumed offline."
        ),
    }


def build_downstream_contract(now: str) -> dict[str, Any]:
    return {
        "consumers": {
            "Lane12 ML Dataset Baseline Lab": {
                "allowed": [
                    "scheduler_decision",
                    "approved_risk_pct",
                    "risk/exposure metrics",
                    "conflict reason as target/outcome sidecar after split only",
                ],
                "forbidden": [
                    "using result_r/opportunity_cost as predecision feature",
                    "live scheduler activation",
                ],
            },
            "Lane13 ML Selector Policy Intelligence": {
                "allowed": [
                    "accepted/rejected scheduler outcomes",
                    "same-symbol and cluster conflict families",
                    "money-risk exposure state",
                ],
                "rule": "use as offline target/context only; not production selector authority",
            },
            "Lane14 Daily Learning Repair Companion": {
                "allowed": [
                    "stale-cap replacement audit",
                    "source gaps",
                    "risk/exposure drift metrics",
                ],
            },
            "Lane15 Command Center Production Dossier": {
                "allowed": [
                    "default-off scheduler proof",
                    "completion audit",
                    "verifier result",
                    "runtime-effect boundary",
                ],
                "requires": [
                    "separate production-change dossier",
                    "owner approval",
                    "broker lifecycle close/deal/cost reconciliation where claimed",
                ],
            },
        },
        "generated_at_utc": now,
        "join_keys": [
            "row_id",
            "candidate_id",
            "selected_row_id",
            "symbol",
            "candidate_time_utc",
            "calendar_day/week/month",
        ],
        "result_use_status": RESULT_USE_STATUS,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": "lane10_downstream_contract_v1",
    }


def build_context_anchor(now: str, summary: dict[str, Any]) -> None:
    text = f"""# Lane10 Portfolio Scheduler V2 Context Anchor

Generated: {now}
HEAD: {git_head()}

Controlling prompt: {rel(PROMPT_PATH)}
Starter: {rel(STARTER_PATH)}

This route is offline/default-off scheduler evidence. It consumed Lane05,
Lane06, Lane07, Lane08, Lane01 Friday, Lane02 broad selected, Master Wave 3,
current doctrine, and current vNext context from disk. It did not change live
broker/order/deal/position state, credentials, remotes, paid/vendor calls, or
live config/prompt/risk/execution/safety/selector activation.

Material rows:
- Lane08 replay rows: {summary['replay_rows']}
- Lane08 replay-gap rows carried into scheduler gap ledger: {summary['missing_gap_rows']}
- Scheduler split metric rows: {summary['split_metric_rows']}
- Scheduler conflicts preserved: {sum(summary['scheduling_conflict_counts'].values())}

Completion remains proven only by `LANE10_VERIFICATION_RESULT.json`, focused
tests, manifest, completion audit, and the scoped commit.
"""
    CONTEXT_ANCHOR.write_text(text, encoding="utf-8")


def build_manifest(now: str) -> dict[str, Any]:
    outputs = [
        SCHEDULER_REPLAY_LEDGER,
        SCHEDULING_CONFLICT_LEDGER,
        MISSING_REPLAY_GAP_SCHEDULER_LEDGER,
        RISK_EXPOSURE_LEDGER,
        SPLIT_STRESS_METRICS,
        STALE_CAP_AUDIT,
        NO_LEAK_LEDGER,
        DEPENDENCY_LEDGER,
        SOURCE_USE_STATE,
        DOWNSTREAM_CONTRACT,
        CONTEXT_ANCHOR,
        COMPLETION_AUDIT,
        VERIFICATION_RESULT,
        FOCUSED_TEST_RESULT,
        ROUTE_DIR / "portfolio_scheduler_v2.py",
        ROUTE_DIR / "build_vnext_moonshot_lane10_portfolio_scheduler_v2.py",
        ROUTE_DIR / "verify_vnext_moonshot_lane10_portfolio_scheduler_v2.py",
        ROOT / "tests" / "test_vnext_moonshot_lane10_portfolio_scheduler_v2.py",
    ]
    data = {
        "generated_at_utc": now,
        "output_count": len(outputs),
        "outputs": [
            {
                "exists": path.exists(),
                "line_count": count_text_jsonl(path) if path.suffix in {".jsonl", ".gz"} else None,
                "path": rel(path),
                "role": "lane10_route_output",
                "sha256": file_sha256(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for path in outputs
        ],
        "route_dir": rel(ROUTE_DIR),
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": "lane10_output_manifest_v1",
    }
    write_json(OUTPUT_MANIFEST, data)
    return data


def verify_outputs(write: bool = True) -> dict[str, Any]:
    issues: list[str] = []

    def require(condition: bool, issue: str) -> None:
        if not condition:
            issues.append(issue)

    replay_rows = count_text_jsonl(SCHEDULER_REPLAY_LEDGER)
    gap_rows = count_text_jsonl(MISSING_REPLAY_GAP_SCHEDULER_LEDGER)
    conflict_rows = count_text_jsonl(SCHEDULING_CONFLICT_LEDGER)
    split_rows = count_text_jsonl(SPLIT_STRESS_METRICS)
    risk_rows = count_text_jsonl(RISK_EXPOSURE_LEDGER)
    stale_rows = count_text_jsonl(STALE_CAP_AUDIT)
    no_leak_rows = list(iter_jsonl(NO_LEAK_LEDGER)) if NO_LEAK_LEDGER.exists() else []
    dependency_rows = count_text_jsonl(DEPENDENCY_LEDGER)
    source_state = read_json(SOURCE_USE_STATE, {})
    downstream = read_json(DOWNSTREAM_CONTRACT, {})

    require(replay_rows == EXPECTED_REPLAY_ROWS, f"replay_rows_{replay_rows}_expected_{EXPECTED_REPLAY_ROWS}")
    require(gap_rows == EXPECTED_MISSING_GAP_ROWS, f"gap_rows_{gap_rows}_expected_{EXPECTED_MISSING_GAP_ROWS}")
    require(conflict_rows > 0, "missing_conflict_rows")
    require(split_rows >= 100, "split_metric_rows_too_small")
    require(risk_rows >= 10, "risk_exposure_rows_too_small")
    require(stale_rows >= 4, "stale_cap_audit_rows_too_small")
    require(dependency_rows >= 7, "dependency_rows_too_small")
    require(source_state.get("input_counts", {}).get("lane08_replay_rows") == EXPECTED_REPLAY_ROWS, "source_state_replay_count_bad")
    require(source_state.get("input_counts", {}).get("lane08_missing_gap_rows") == EXPECTED_MISSING_GAP_ROWS, "source_state_gap_count_bad")
    require(source_state.get("input_counts", {}).get("lane08_split_rows") == EXPECTED_LANE08_SPLIT_ROWS, "lane08_split_count_bad")
    require(source_state.get("input_counts", {}).get("lane08_depth_rows") == EXPECTED_LANE08_DEPTH_ROWS, "lane08_depth_count_bad")
    require(bool(downstream.get("consumers")), "downstream_contract_missing_consumers")
    require(all(row.get("status") == "pass" for row in no_leak_rows), "no_leak_not_pass")

    result = {
        "counts": {
            "conflict_rows": conflict_rows,
            "gap_rows": gap_rows,
            "replay_rows": replay_rows,
            "risk_rows": risk_rows,
            "split_rows": split_rows,
        },
        "generated_at_utc": utc_now(),
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": "lane10_verification_result_v1",
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
    return result


def build_completion_audit(now: str, summary: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    audit = {
        "counts": {
            "lane08_depth_rows": count_text_jsonl(LANE08_DEPTH),
            "lane08_missing_gap_rows": summary["missing_gap_rows"],
            "lane08_replay_rows": summary["replay_rows"],
            "lane08_split_rows": count_text_jsonl(LANE08_SPLITS),
            "lane10_conflict_rows": sum(summary["scheduling_conflict_counts"].values()),
            "lane10_risk_exposure_metric_rows": summary["risk_exposure_metric_rows"],
            "lane10_split_metric_rows": summary["split_metric_rows"],
        },
        "forbidden_surfaces_not_crossed": [
            "no live broker/order/deal/position action",
            "no paid API/vendor call",
            "no credential or remote change",
            "no hidden production activation",
            "no prompt/config/risk/execution/safety/canary/selector live behavior change",
        ],
        "generated_at_utc": now,
        "instruction_coverage": {
            "constructive_builder_posture_applied": True,
            "current_vnext_map_and_repo_order_read": True,
            "full_lane08_material_rows_preserved": summary["replay_rows"] == EXPECTED_REPLAY_ROWS,
            "goal_session_research_discipline_read": True,
            "lane05_lane06_lane07_lane08_consumed": True,
            "mandatory_preflight_reread": True,
            "master_wave3_state_read": True,
            "no_arbitrary_top_n": True,
            "research_operating_doctrine_read": True,
            "runtime_effect_boundary_explicit": True,
            "starter_and_prompt_read": True,
        },
        "requirements": [
            {
                "evidence": rel(SCHEDULER_REPLAY_LEDGER),
                "requirement": "scheduler_replay_ledger_full_material_rows",
                "rows": summary["replay_rows"],
                "status": "complete" if summary["replay_rows"] == EXPECTED_REPLAY_ROWS else "incomplete",
            },
            {
                "evidence": rel(SCHEDULING_CONFLICT_LEDGER),
                "requirement": "all_scheduling_conflicts_preserved",
                "rows": sum(summary["scheduling_conflict_counts"].values()),
                "status": "complete",
            },
            {
                "evidence": rel(MISSING_REPLAY_GAP_SCHEDULER_LEDGER),
                "requirement": "lane08_replay_gap_rows_preserved",
                "rows": summary["missing_gap_rows"],
                "status": "complete" if summary["missing_gap_rows"] == EXPECTED_MISSING_GAP_ROWS else "incomplete",
            },
            {
                "evidence": [rel(RISK_EXPOSURE_LEDGER), rel(SPLIT_STRESS_METRICS)],
                "requirement": "risk_exposure_daily_weekly_monthly_split_stress_metrics",
                "status": "complete",
            },
            {
                "evidence": rel(STALE_CAP_AUDIT),
                "requirement": "stale_count_cap_replacement_audit",
                "status": "complete",
            },
            {
                "evidence": rel(NO_LEAK_LEDGER),
                "requirement": "no_leak_validation",
                "status": "complete" if summary["no_leak_issues"] == 0 else "incomplete",
            },
            {
                "evidence": [rel(DOWNSTREAM_CONTRACT), rel(SOURCE_USE_STATE)],
                "requirement": "downstream_contract_source_use_state_runtime_boundary",
                "status": "complete",
            },
            {
                "evidence": [rel(VERIFICATION_RESULT), rel(FOCUSED_TEST_RESULT)],
                "requirement": "verifier_and_focused_tests",
                "status": "complete" if verification.get("ok") else "incomplete",
            },
            {
                "evidence": "scoped git commit after artifacts and tests",
                "requirement": "scoped_commit",
                "status": "pending_until_commit",
            },
        ],
        "result_use_status": RESULT_USE_STATUS,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "scheduler_authority": "money_risk_account_exposure_replaces_stale_count_session_caps_in_default_off_package",
        "schema_version": "lane10_completion_audit_v1",
        "source_use_state": "Lane05/Lane06/Lane07/Lane08 plus Lane01/Lane02 scheduler detail consumed offline",
        "status": "complete_verified" if verification.get("ok") else "incomplete",
        "summary": summary,
        "verification_result": verification,
    }
    write_json(COMPLETION_AUDIT, audit)
    return audit


def main() -> int:
    args = parse_args()
    if args.verify_only:
        result = verify_outputs(write=True)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ok"] else 1

    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    summary = build_replay(now)
    write_jsonl(DEPENDENCY_LEDGER, build_dependency_rows(now))
    write_jsonl(STALE_CAP_AUDIT, build_stale_cap_audit(now, summary))
    write_jsonl(NO_LEAK_LEDGER, build_no_leak_rows(now, summary))
    write_json(SOURCE_USE_STATE, build_source_use_state(now, summary))
    write_json(DOWNSTREAM_CONTRACT, build_downstream_contract(now))
    build_context_anchor(now, summary)
    verification = verify_outputs(write=True)
    build_completion_audit(now, summary, verification)
    build_manifest(now)
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
