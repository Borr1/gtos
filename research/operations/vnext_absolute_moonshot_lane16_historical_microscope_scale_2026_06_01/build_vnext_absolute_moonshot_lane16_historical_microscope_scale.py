from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01"
ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[2]

ACTIVE_SYMBOLS = (
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
)

MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"
LANE01_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
LANE02_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"
LANE03_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01"
LANE04_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01"
LANE05_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE06_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE07_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
LANE08_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
LANE09_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane09_meta_selector_v2_2026_06_01"
LANE09B_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane09b_selector_scheduler_reconciliation_2026_06_01"
LANE10_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01"
LANE10B_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01"
LANE11_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01"

LANE04_TIMELINE = LANE04_DIR / "LANE04_ROW_TIMELINE_LEDGER.jsonl"
LANE04_SOURCE_GAP = LANE04_DIR / "LANE04_SOURCE_GAP_LEDGER.jsonl"
LANE05_TIMELINE_FEATURES = LANE05_DIR / "LANE05_TIMELINE_FEATURE_VECTOR_LEDGER.jsonl.gz"
LANE06_LABELS = LANE06_DIR / "LANE06_LABEL_VECTOR_LEDGER.jsonl.gz"
LANE08_REPLAY = LANE08_DIR / "LANE08_REPLAY_ROW_LEDGER.jsonl.gz"
LANE09_SELECTOR = LANE09_DIR / "LANE09_SELECTOR_ROW_EVIDENCE_LEDGER.jsonl.gz"
LANE10_SCHEDULER = LANE10_DIR / "LANE10_SCHEDULER_REPLAY_LEDGER.jsonl.gz"
LANE09B_JOIN = LANE09B_DIR / "LANE09B_SELECTOR_TO_SCHEDULER_ROW_JOIN_LEDGER.jsonl.gz"
LANE10B_CONFLICT = LANE10B_DIR / "LANE10B_FULL_CONFLICT_ANATOMY_LEDGER.jsonl.gz"
LANE10_MISSING_GAPS = LANE10_DIR / "LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz"
LANE11_POLICY = LANE11_DIR / "LANE11_POLICY_SIMULATION_LEDGER.jsonl.gz"

EVENT_LEDGER = ROUTE_DIR / "LANE16_MICROSCOPE_EVENT_LEDGER.jsonl.gz"
PATH_ANATOMY_LEDGER = ROUTE_DIR / "LANE16_PATH_ANATOMY_LEDGER.jsonl.gz"
SOURCE_GAP_LEDGER = ROUTE_DIR / "LANE16_SOURCE_GAP_LEDGER.jsonl.gz"
COVERAGE_INVENTORY = ROUTE_DIR / "LANE16_COVERAGE_INVENTORY.jsonl"
SPLIT_STRESS_SUMMARY = ROUTE_DIR / "LANE16_SPLIT_STRESS_SUMMARY.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / "LANE16_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl"
DEPENDENCY_STATE_LEDGER = ROUTE_DIR / "LANE16_DEPENDENCY_STATE_LEDGER.jsonl"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / "LANE16_IMPLEMENTATION_DECISION_LEDGER.jsonl"
DOWNSTREAM_CONTRACT = ROUTE_DIR / "LANE16_DOWNSTREAM_CONTRACT.json"
SOURCE_USE_STATE = ROUTE_DIR / "LANE16_SOURCE_USE_STATE.json"
RESULT_USE_STATUS = ROUTE_DIR / "LANE16_RESULT_USE_STATUS.json"
RUNTIME_EFFECT_BOUNDARY = ROUTE_DIR / "LANE16_RUNTIME_EFFECT_BOUNDARY.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE16_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE16_OUTPUT_MANIFEST.json"
VERIFICATION_RESULT = ROUTE_DIR / "LANE16_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE16_FOCUSED_TEST_RESULT.xml"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE16_CONTEXT_ANCHOR.md"
VERIFIER = ROUTE_DIR / "verify_vnext_absolute_moonshot_lane16_historical_microscope_scale.py"

PROMPT_PATH = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts" / "VNEXT_ABSOLUTE_MOONSHOT_LANE16_HISTORICAL_MICROSCOPE_SCALE_GOAL_PROMPT_2026-06-01.md"
STARTER_PATH = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts" / "VNEXT_ABSOLUTE_MOONSHOT_LANE16_HISTORICAL_MICROSCOPE_SCALE_STARTER_2026-06-01.txt"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNKNOWN"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def open_text(path: Path, mode: str = "rt"):
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8", errors="replace", newline="\n")
    return path.open(mode, encoding="utf-8", errors="replace", newline="\n")


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with open_text(path, "rt") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield line_number, row


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open_text(path, "wt") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def write_jsonl_line(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def fnum(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_metric(value: Any, digits: int = 9) -> float | None:
    number = fnum(value)
    if number is None:
        return None
    return round(number, digits)


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def iso(value: Any) -> str | None:
    parsed = parse_dt(value)
    return parsed.isoformat() if parsed else None


def date_part(value: Any, size: int) -> str | None:
    text = iso(value)
    if not text:
        return None
    return text[:size]


def iso_week(value: Any) -> str | None:
    parsed = parse_dt(value)
    if not parsed:
        return None
    year, week, _ = parsed.isocalendar()
    return f"{year:04d}-W{week:02d}"


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with open_text(path, "rt") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def manifest_line_count(manifest_path: Path, artifact_name: str) -> int | None:
    manifest = read_json(manifest_path, {})
    for item in manifest.get("outputs") or []:
        path = str(item.get("path") or "")
        if path.endswith(artifact_name):
            value = item.get("line_count")
            return int(value) if isinstance(value, int) else None
    return None


def first_present(row: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def source_gap_families_from_proof(proof: Any) -> list[str]:
    families: set[str] = set()
    if isinstance(proof, list):
        for item in proof:
            if isinstance(item, dict):
                family = item.get("field_family") or item.get("label_family")
                if family:
                    families.add(str(family))
    return sorted(families)


def compact_source_gap_proof(proof: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(proof, list):
        for item in proof:
            if isinstance(item, dict):
                rows.append(
                    {
                        "field_family": item.get("field_family") or item.get("label_family"),
                        "reason": item.get("reason"),
                        "repair_requirement": item.get("repair_requirement") or item.get("repair_requirement_code"),
                        "attempted_sources": item.get("attempted_sources"),
                    }
                )
    return rows


@dataclass
class IndexState:
    name: str
    path: str
    rows: int = 0
    indexed_rows: int = 0
    missing_key_rows: int = 0
    duplicate_key_rows: int = 0


def load_index(
    name: str,
    path: Path,
    key_fields: Iterable[str],
    mapper,
) -> tuple[dict[str, dict[str, Any]], IndexState]:
    index: dict[str, dict[str, Any]] = {}
    state = IndexState(name=name, path=rel(path))
    for _, row in iter_jsonl(path):
        state.rows += 1
        key = first_present(row, key_fields)
        if not key:
            state.missing_key_rows += 1
            continue
        key = str(key)
        if key in index:
            state.duplicate_key_rows += 1
            continue
        index[key] = mapper(row)
        state.indexed_rows += 1
    return index, state


def feature_mapper(row: dict[str, Any]) -> dict[str, Any]:
    features = row.get("features") or {}
    return {
        "feature_join_state": "joined_lane05_timeline_feature_vector",
        "feature_row_id": row.get("row_id"),
        "feature_set_id": row.get("feature_set_id"),
        "feature_source_state": row.get("feature_source_state"),
        "no_leak_status": row.get("no_leak_status"),
        "source_completeness_state": row.get("source_completeness_state"),
        "source_gaps": row.get("source_gaps") or [],
        "selected_cell_risk_join_state": features.get("selected_cell_risk_join_state"),
        "selected_cell_effective_risk_pct": round_metric(features.get("selected_cell_effective_risk_pct")),
        "portfolio_scheduler_join_state": features.get("portfolio_scheduler_join_state"),
        "correlation_cluster_join_state": features.get("correlation_cluster_join_state"),
        "correlation_cluster_size": features.get("correlation_cluster_size"),
        "correlation_risk_multiplier": round_metric(features.get("correlation_risk_multiplier")),
        "regime_h4_state": features.get("regime_h4_state"),
        "regime_h4_direction": features.get("regime_h4_direction"),
        "regime_h4_score": round_metric(features.get("regime_h4_score")),
        "broker_feasibility_state": features.get("broker_feasibility_state"),
        "strict_tick_available": features.get("strict_tick_available"),
        "strict_tick_entry_spread_r": round_metric(features.get("strict_tick_entry_spread_r")),
        "time_candidate_weekday_utc": features.get("time_candidate_weekday_utc"),
    }


def label_mapper(row: dict[str, Any]) -> dict[str, Any]:
    values = row.get("label_values") or {}
    return {
        "label_join_state": "joined_lane06_label_vector",
        "label_row_id": row.get("row_id"),
        "evidence_class": row.get("evidence_class"),
        "outcome_availability": row.get("outcome_availability") or {},
        "label_values": {
            "sl_before_1r": values.get("sl_before_1r"),
            "partial_then_be": values.get("partial_then_be"),
            "partial_then_final": values.get("partial_then_final"),
            "no_entry_touch": values.get("no_entry_touch"),
            "stuck_no_resolution": values.get("stuck_no_resolution"),
            "missed_opportunity": values.get("missed_opportunity"),
            "missed_opportunity_reason": values.get("missed_opportunity_reason"),
            "correct_rejection": values.get("correct_rejection"),
            "correct_rejection_reason": values.get("correct_rejection_reason"),
            "stale_blocker": values.get("stale_blocker"),
            "stale_blocker_reason": values.get("stale_blocker_reason"),
            "one_r_reached": values.get("one_r_reached"),
            "final_target_reached": values.get("final_target_reached"),
            "source_bound_proxy_r": round_metric(values.get("source_bound_proxy_r")),
            "cost_adjusted_r": round_metric(values.get("cost_adjusted_r")),
            "broker_real_net_r": round_metric(values.get("broker_real_net_r")),
            "broker_lifecycle_status": values.get("broker_lifecycle_status"),
            "broker_final_net_r_status": values.get("broker_final_net_r_status"),
            "source_gap_families": values.get("source_gap_families") or [],
            "path_ordering_status": values.get("path_ordering_status"),
            "strict_tick_replay_status": values.get("strict_tick_replay_status"),
        },
        "missing_label_reasons": row.get("missing_label_reasons") or [],
    }


def replay_mapper(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "replay_join_state": "joined_lane08_digital_twin_replay",
        "lane08_row_id": row.get("row_id"),
        "result_r": round_metric(row.get("result_r")),
        "result_r_class": row.get("result_r_class"),
        "evidence_class": row.get("evidence_class"),
        "source_use_state": row.get("source_use_state"),
    }


def selector_mapper(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "selector_join_state": "joined_lane09_selector_row_evidence",
        "lane09_source_row_id": row.get("source_row_id"),
        "selector_component": row.get("selector_component"),
        "mechanism_family": row.get("mechanism_family") or row.get("origin_family"),
        "lane09_mechanism_decision": row.get("lane09_mechanism_decision") or row.get("mechanism_decision"),
        "source_completeness_state": row.get("source_completeness_state"),
        "source_gap_families": row.get("source_gap_families") or [],
        "source_quality_status": row.get("source_quality_status"),
        "path_class": row.get("path_class"),
        "result_r": round_metric(row.get("result_r")),
        "result_r_class": row.get("result_r_class"),
    }


def scheduler_mapper(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scheduler_join_state": "joined_lane10_scheduler_replay",
        "lane10_row_id": row.get("row_id"),
        "scheduler_decision": row.get("scheduler_decision") or row.get("decision"),
        "scheduler_reason": row.get("scheduler_reason") or row.get("reason"),
        "accepted": row.get("accepted"),
        "approved_risk_pct": round_metric(row.get("approved_risk_pct")),
        "requested_risk_pct": round_metric(row.get("requested_risk_pct")),
        "priority_score": round_metric(row.get("priority_score")),
        "priority_rank_in_batch": row.get("priority_rank_in_batch"),
        "total_risk_pct_before": round_metric(row.get("total_risk_pct_before")),
        "total_risk_pct_after": round_metric(row.get("total_risk_pct_after")),
        "open_risk_pct_before": round_metric(row.get("open_risk_pct_before")),
        "pending_risk_pct_before": round_metric(row.get("pending_risk_pct_before")),
        "same_symbol_risk_pct_before": round_metric(row.get("same_symbol_risk_pct_before")),
        "correlated_cluster_risk_pct_before": round_metric(row.get("correlated_cluster_risk_pct_before")),
        "correlation_cluster": row.get("correlation_cluster"),
        "opportunity_cost_r": round_metric(row.get("opportunity_cost_r")),
        "result_r": round_metric(row.get("result_r")),
        "result_r_class": row.get("result_r_class"),
    }


def reconciliation_mapper(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "lane09b_join_state": row.get("join_status") or "joined_lane09b_selector_scheduler_reconciliation",
        "reconciliation_class": row.get("reconciliation_class"),
        "risk_state": row.get("risk_state"),
        "lane09_mechanism_decision": row.get("lane09_mechanism_decision"),
        "lane09_mechanism_decision_reason": row.get("lane09_mechanism_decision_reason"),
        "lane11_policy_dependency": row.get("lane11_policy_dependency"),
        "scheduler_decision": row.get("scheduler_decision"),
        "scheduler_reason": row.get("scheduler_reason"),
    }


def conflict_mapper(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "lane10b_join_state": "joined_lane10b_conflict_anatomy",
        "lane10b_classification": row.get("classification"),
        "classification_reason": row.get("classification_reason"),
        "repairable_scheduler_block": row.get("repairable_scheduler_block"),
        "correct_reject": row.get("correct_reject"),
        "missed_edge_scope": row.get("missed_edge_scope"),
        "missed_result_r": round_metric(row.get("missed_result_r")),
        "missed_risk_pct": round_metric(row.get("missed_risk_pct")),
        "missed_proxy_amount": round_metric(row.get("missed_proxy_amount")),
        "v3_action": row.get("v3_action"),
        "v3_branch_candidates": row.get("v3_branch_candidates") or [],
        "same_symbol_state": row.get("same_symbol_state"),
        "cluster_state": row.get("cluster_state"),
        "risk_budget_state": row.get("risk_budget_state"),
        "drawdown_state": row.get("drawdown_state"),
        "edge_bucket": row.get("edge_bucket"),
    }


def policy_mapper(row: dict[str, Any]) -> dict[str, Any]:
    policy_results = row.get("policy_results") or {}
    current_policy_id = row.get("current_router_policy")
    current = policy_results.get("current_router_policy")
    if not isinstance(current, dict) and current_policy_id:
        current = policy_results.get(str(current_policy_id))
    current = current if isinstance(current, dict) else {}
    variants: list[tuple[str, dict[str, Any]]] = []
    for policy_id, payload in policy_results.items():
        if policy_id == "current_router_policy" or not isinstance(payload, dict):
            continue
        variants.append((str(policy_id), payload))
    best_policy_id = None
    best_policy_payload: dict[str, Any] = {}
    best_score = None
    for policy_id, payload in variants:
        score = fnum(payload.get("cost_adjusted_median_r"))
        if score is None:
            score = fnum(payload.get("gross_r"))
        if score is None:
            continue
        if best_score is None or score > best_score:
            best_score = score
            best_policy_id = policy_id
            best_policy_payload = payload
    return {
        "policy_join_state": "joined_lane11_policy_simulation",
        "lane11_row_id": row.get("row_id"),
        "current_router_policy": current_policy_id,
        "policy_variant_count": len(variants),
        "current_policy_gross_r": round_metric(current.get("gross_r")),
        "current_policy_cost_adjusted_median_r": round_metric(current.get("cost_adjusted_median_r")),
        "current_policy_cost_adjusted_high_stress_r": round_metric(current.get("cost_adjusted_high_stress_r")),
        "current_policy_cost_adjusted_p90_r": round_metric(current.get("cost_adjusted_p90_r")),
        "current_policy_price_path_model": current.get("price_path_model"),
        "current_policy_bid_ask_ordering_state": current.get("bid_ask_ordering_state"),
        "current_policy_r_evidence_class": current.get("r_evidence_class"),
        "current_policy_source_gap_reason": current.get("source_gap_reason"),
        "best_policy_id": best_policy_id,
        "best_policy_gross_r": round_metric(best_policy_payload.get("gross_r")),
        "best_policy_cost_adjusted_median_r": round_metric(best_policy_payload.get("cost_adjusted_median_r")),
        "best_policy_cost_adjusted_high_stress_r": round_metric(best_policy_payload.get("cost_adjusted_high_stress_r")),
    }


def stage_event(event_type: str, *, time_utc: Any, status: str, source: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "details": details or {},
        "event_type": event_type,
        "source": source,
        "status": status,
        "time_utc": iso(time_utc),
    }


def combine_gaps(timeline: dict[str, Any], sidecars: dict[str, dict[str, Any] | None]) -> tuple[list[str], list[dict[str, Any]]]:
    gap_families = set(source_gap_families_from_proof(timeline.get("missing_field_proof")))
    gap_proof = compact_source_gap_proof(timeline.get("missing_field_proof"))
    label = sidecars.get("label") or {}
    label_values = label.get("label_values") or {}
    for family in label_values.get("source_gap_families") or []:
        gap_families.add(str(family))
    for item in label.get("missing_label_reasons") or []:
        if isinstance(item, dict):
            family = item.get("field_family") or item.get("label_family")
            if family:
                gap_families.add(str(family))
                gap_proof.append(
                    {
                        "field_family": family,
                        "reason": item.get("reason"),
                        "repair_requirement": item.get("repair_requirement"),
                        "attempted_sources": None,
                    }
                )
    required = {
        "feature": "lane05_timeline_feature_vector",
        "label": "lane06_label_vector",
        "replay": "lane08_digital_twin_replay_row",
        "selector": "lane09_selector_row_evidence",
        "scheduler": "lane10_scheduler_replay_row",
        "reconciliation": "lane09b_selector_scheduler_join",
        "conflict": "lane10b_scheduler_conflict_anatomy",
        "policy": "lane11_policy_simulation",
    }
    for key, family in required.items():
        if not sidecars.get(key):
            gap_families.add(f"missing_{family}")
            gap_proof.append(
                {
                    "field_family": f"missing_{family}",
                    "reason": "cross_lane_sidecar_row_not_joined_by_selected_row_id_or_row_id",
                    "repair_requirement": "inspect upstream ledger identity fields and rebuild join map without changing live behavior",
                    "attempted_sources": [family],
                }
            )
    return sorted(gap_families), gap_proof


def build_microscope_event(timeline: dict[str, Any], sidecars: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    feature = sidecars.get("feature") or {}
    label = sidecars.get("label") or {}
    replay = sidecars.get("replay") or {}
    selector = sidecars.get("selector") or {}
    scheduler = sidecars.get("scheduler") or {}
    reconciliation = sidecars.get("reconciliation") or {}
    conflict = sidecars.get("conflict") or {}
    policy = sidecars.get("policy") or {}
    label_values = label.get("label_values") or {}
    source_gap_families, source_gap_proof = combine_gaps(timeline, sidecars)
    candidate_time = timeline.get("source_time_utc") or timeline.get("entry_time_utc")
    date = timeline.get("date") or date_part(candidate_time, 10)
    month = timeline.get("month") or date_part(candidate_time, 7)
    year = timeline.get("year") or date_part(candidate_time, 4)
    week = iso_week(candidate_time)
    selected_row_id = timeline.get("selected_row_id") or timeline.get("row_id")
    ordered_events = list(timeline.get("ordered_events") or [])
    ordered_events.extend(
        [
            stage_event(
                "feature_vector_materialized",
                time_utc=candidate_time,
                status=feature.get("feature_join_state", "missing_lane05_feature_join"),
                source="LANE05_TIMELINE_FEATURE_VECTOR_LEDGER",
                details={"no_leak_status": feature.get("no_leak_status"), "feature_set_id": feature.get("feature_set_id")},
            ),
            stage_event(
                "label_vector_materialized",
                time_utc=timeline.get("exit_time_utc") or candidate_time,
                status=label.get("label_join_state", "missing_lane06_label_join"),
                source="LANE06_LABEL_VECTOR_LEDGER",
                details={"evidence_class": label.get("evidence_class"), "outcome_availability": label.get("outcome_availability")},
            ),
            stage_event(
                "digital_twin_replay_materialized",
                time_utc=candidate_time,
                status=replay.get("replay_join_state", "missing_lane08_replay_join"),
                source="LANE08_REPLAY_ROW_LEDGER",
                details={"result_r_class": replay.get("result_r_class"), "lane08_row_id": replay.get("lane08_row_id")},
            ),
            stage_event(
                "selector_evidence_materialized",
                time_utc=candidate_time,
                status=selector.get("selector_join_state", "missing_lane09_selector_join"),
                source="LANE09_SELECTOR_ROW_EVIDENCE_LEDGER",
                details={"selector_component": selector.get("selector_component"), "mechanism_decision": selector.get("lane09_mechanism_decision")},
            ),
            stage_event(
                "scheduler_decision_materialized",
                time_utc=candidate_time,
                status=scheduler.get("scheduler_decision", "missing_lane10_scheduler_join"),
                source="LANE10_SCHEDULER_REPLAY_LEDGER",
                details={"scheduler_reason": scheduler.get("scheduler_reason"), "approved_risk_pct": scheduler.get("approved_risk_pct")},
            ),
            stage_event(
                "execution_policy_simulation_materialized",
                time_utc=candidate_time,
                status=policy.get("policy_join_state", "missing_lane11_policy_join"),
                source="LANE11_POLICY_SIMULATION_LEDGER",
                details={"current_router_policy": policy.get("current_router_policy"), "best_policy_id": policy.get("best_policy_id")},
            ),
        ]
    )
    ordered_events.sort(key=lambda item: item.get("time_utc") or "9999-12-31T23:59:59+00:00")
    result_r = (
        label_values.get("source_bound_proxy_r")
        if label_values.get("source_bound_proxy_r") is not None
        else replay.get("result_r")
        if replay.get("result_r") is not None
        else timeline.get("final_r")
    )
    materialized = sum(1 for value in sidecars.values() if value)
    return {
        "schema_version": "lane16_microscope_event_row_v1",
        "route_id": ROUTE_ID,
        "row_id": timeline.get("row_id"),
        "candidate_id": timeline.get("candidate_id"),
        "selected_row_id": selected_row_id,
        "lane08_row_id": replay.get("lane08_row_id"),
        "symbol": timeline.get("symbol"),
        "side": timeline.get("side"),
        "framework": timeline.get("framework"),
        "origin_family": timeline.get("origin_family"),
        "mechanism_family": selector.get("mechanism_family") or timeline.get("origin_family"),
        "session_bucket": timeline.get("session_bucket"),
        "date": date,
        "week": week,
        "month": month,
        "year": year,
        "candidate_time_utc": iso(candidate_time),
        "entry_time_utc": timeline.get("entry_time_utc"),
        "exit_time_utc": timeline.get("exit_time_utc"),
        "timeline_source_family": timeline.get("timeline_source_family"),
        "path_class": timeline.get("path_class"),
        "source_use_state": timeline.get("source_use_state"),
        "cross_lane_materialization_state": "full_cross_lane_microscope_join" if materialized == 8 else "partial_cross_lane_microscope_join_with_source_gaps",
        "materialized_sidecar_count": materialized,
        "result_r": round_metric(result_r),
        "result_r_class": replay.get("result_r_class") or label.get("evidence_class") or "timeline_proxy",
        "mfe_r": timeline.get("mfe_r"),
        "mae_r": timeline.get("mae_r"),
        "time_to_1r_seconds": timeline.get("time_to_1r_seconds"),
        "time_to_sl_seconds": timeline.get("time_to_sl_seconds"),
        "time_to_final_seconds": timeline.get("time_to_final_seconds"),
        "duration_seconds": timeline.get("time_to_final_seconds"),
        "spread_r_bucket": timeline.get("spread_r_bucket"),
        "cost_status": timeline.get("cost_status"),
        "cost_r": timeline.get("cost_r"),
        "source_gap_families": source_gap_families,
        "source_gap_count": len(source_gap_families),
        "source_gap_proof": source_gap_proof,
        "feature_join_state": feature.get("feature_join_state", "missing_lane05_feature_join"),
        "label_join_state": label.get("label_join_state", "missing_lane06_label_join"),
        "replay_join_state": replay.get("replay_join_state", "missing_lane08_replay_join"),
        "selector_join_state": selector.get("selector_join_state", "missing_lane09_selector_join"),
        "scheduler_join_state": scheduler.get("scheduler_join_state", "missing_lane10_scheduler_join"),
        "lane09b_join_state": reconciliation.get("lane09b_join_state", "missing_lane09b_reconciliation_join"),
        "lane10b_join_state": conflict.get("lane10b_join_state", "missing_lane10b_conflict_join"),
        "policy_join_state": policy.get("policy_join_state", "missing_lane11_policy_join"),
        "ordered_events": ordered_events,
        "result_use_status": "scaled_historical_microscope_research_training_selector_scheduler_execution_inputs_not_production_change",
        "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
    }


def build_path_anatomy(event_row: dict[str, Any], sidecars: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    feature = sidecars.get("feature") or {}
    label = sidecars.get("label") or {}
    replay = sidecars.get("replay") or {}
    selector = sidecars.get("selector") or {}
    scheduler = sidecars.get("scheduler") or {}
    reconciliation = sidecars.get("reconciliation") or {}
    conflict = sidecars.get("conflict") or {}
    policy = sidecars.get("policy") or {}
    label_values = label.get("label_values") or {}
    return {
        "schema_version": "lane16_path_anatomy_row_v1",
        "route_id": ROUTE_ID,
        "row_id": event_row.get("row_id"),
        "selected_row_id": event_row.get("selected_row_id"),
        "candidate_id": event_row.get("candidate_id"),
        "symbol": event_row.get("symbol"),
        "side": event_row.get("side"),
        "framework": event_row.get("framework"),
        "origin_family": event_row.get("origin_family"),
        "mechanism_family": event_row.get("mechanism_family"),
        "session_bucket": event_row.get("session_bucket"),
        "date": event_row.get("date"),
        "week": event_row.get("week"),
        "month": event_row.get("month"),
        "year": event_row.get("year"),
        "path_class": event_row.get("path_class"),
        "result_r": event_row.get("result_r"),
        "result_r_class": event_row.get("result_r_class"),
        "mfe_r": event_row.get("mfe_r"),
        "mae_r": event_row.get("mae_r"),
        "time_to_1r_seconds": event_row.get("time_to_1r_seconds"),
        "time_to_sl_seconds": event_row.get("time_to_sl_seconds"),
        "time_to_final_seconds": event_row.get("time_to_final_seconds"),
        "sl_before_1r": label_values.get("sl_before_1r"),
        "partial_then_be": label_values.get("partial_then_be"),
        "partial_then_final": label_values.get("partial_then_final"),
        "no_entry_touch": label_values.get("no_entry_touch"),
        "stuck_no_resolution": label_values.get("stuck_no_resolution"),
        "missed_opportunity": label_values.get("missed_opportunity"),
        "correct_rejection": label_values.get("correct_rejection"),
        "stale_blocker": label_values.get("stale_blocker"),
        "source_gap_families": event_row.get("source_gap_families"),
        "source_gap_count": event_row.get("source_gap_count"),
        "source_completeness_state": selector.get("source_completeness_state") or feature.get("source_completeness_state"),
        "source_quality_status": selector.get("source_quality_status"),
        "tick_availability_status": None,
        "m1_availability_status": None,
        "selected_cell_risk_join_state": feature.get("selected_cell_risk_join_state"),
        "selected_cell_effective_risk_pct": feature.get("selected_cell_effective_risk_pct"),
        "regime_h4_state": feature.get("regime_h4_state"),
        "regime_h4_direction": feature.get("regime_h4_direction"),
        "regime_h4_score": feature.get("regime_h4_score"),
        "selector_component": selector.get("selector_component"),
        "lane09_mechanism_decision": selector.get("lane09_mechanism_decision") or reconciliation.get("lane09_mechanism_decision"),
        "scheduler_decision": scheduler.get("scheduler_decision"),
        "scheduler_reason": scheduler.get("scheduler_reason"),
        "approved_risk_pct": scheduler.get("approved_risk_pct"),
        "requested_risk_pct": scheduler.get("requested_risk_pct"),
        "priority_score": scheduler.get("priority_score"),
        "total_risk_pct_before": scheduler.get("total_risk_pct_before"),
        "total_risk_pct_after": scheduler.get("total_risk_pct_after"),
        "lane09b_reconciliation_class": reconciliation.get("reconciliation_class"),
        "lane09b_risk_state": reconciliation.get("risk_state"),
        "lane10b_classification": conflict.get("lane10b_classification"),
        "repairable_scheduler_block": conflict.get("repairable_scheduler_block"),
        "missed_edge_scope": conflict.get("missed_edge_scope"),
        "missed_result_r": conflict.get("missed_result_r"),
        "v3_action": conflict.get("v3_action"),
        "v3_branch_candidates": conflict.get("v3_branch_candidates"),
        "current_router_policy": policy.get("current_router_policy"),
        "current_policy_gross_r": policy.get("current_policy_gross_r"),
        "current_policy_cost_adjusted_median_r": policy.get("current_policy_cost_adjusted_median_r"),
        "current_policy_cost_adjusted_high_stress_r": policy.get("current_policy_cost_adjusted_high_stress_r"),
        "best_policy_id": policy.get("best_policy_id"),
        "best_policy_cost_adjusted_median_r": policy.get("best_policy_cost_adjusted_median_r"),
        "policy_cost_stress_delta_r": (
            round_metric(policy.get("current_policy_cost_adjusted_high_stress_r") - policy.get("current_policy_cost_adjusted_median_r"))
            if policy.get("current_policy_cost_adjusted_high_stress_r") is not None and policy.get("current_policy_cost_adjusted_median_r") is not None
            else None
        ),
        "feature_join_state": event_row.get("feature_join_state"),
        "label_join_state": event_row.get("label_join_state"),
        "replay_join_state": event_row.get("replay_join_state"),
        "selector_join_state": event_row.get("selector_join_state"),
        "scheduler_join_state": event_row.get("scheduler_join_state"),
        "policy_join_state": event_row.get("policy_join_state"),
        "source_operation": "join_lane04_timeline_to_lane05_lane06_lane08_lane09_lane10_lane09b_lane10b_lane11_without_live_effect",
        "result_use_status": event_row.get("result_use_status"),
        "runtime_effect_boundary": event_row.get("runtime_effect_boundary"),
    }


def lane16_gap_from_event(event_row: dict[str, Any]) -> dict[str, Any] | None:
    if not event_row.get("source_gap_families"):
        return None
    return {
        "schema_version": "lane16_source_gap_row_v1",
        "route_id": ROUTE_ID,
        "gap_id": f"lane16_gap_{event_row.get('row_id')}",
        "gap_source_family": "microscope_event_materialized_with_missing_fields",
        "row_id": event_row.get("row_id"),
        "selected_row_id": event_row.get("selected_row_id"),
        "candidate_id": event_row.get("candidate_id"),
        "symbol": event_row.get("symbol"),
        "side": event_row.get("side"),
        "framework": event_row.get("framework"),
        "origin_family": event_row.get("origin_family"),
        "session_bucket": event_row.get("session_bucket"),
        "candidate_time_utc": event_row.get("candidate_time_utc"),
        "date": event_row.get("date"),
        "month": event_row.get("month"),
        "source_gap_families": event_row.get("source_gap_families"),
        "source_gap_count": event_row.get("source_gap_count"),
        "source_gap_proof": event_row.get("source_gap_proof"),
        "repair_requirement": "repair each listed source family from approved local/read-only sources or preserve as exact downstream capture requirement",
        "result_use_status": "source_gap_row_not_performance_result",
        "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
    }


def lane16_gap_from_missing_scheduler(row: dict[str, Any]) -> dict[str, Any]:
    candidate_time = row.get("candidate_time_utc")
    return {
        "schema_version": "lane16_source_gap_row_v1",
        "route_id": ROUTE_ID,
        "gap_id": f"lane16_nonreconstructable_{row.get('gap_id')}",
        "gap_source_family": "canonical_candidate_without_joined_microscope_label_replay_scheduler",
        "row_id": row.get("canonical_candidate_id"),
        "selected_row_id": None,
        "candidate_id": row.get("canonical_candidate_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "origin_family": row.get("origin_family"),
        "session_bucket": row.get("session"),
        "candidate_time_utc": iso(candidate_time),
        "date": date_part(candidate_time, 10),
        "month": date_part(candidate_time, 7),
        "source_gap_families": [
            "no_joined_label_source_current_inputs",
            "not_replayable_without_selected_candidate_geometry",
            "not_replayable_without_joined_selector_label_timeline",
        ],
        "source_gap_count": 3,
        "source_gap_proof": [
            {
                "field_family": "joined_microscope_label_replay_scheduler",
                "reason": row.get("replay_gap_reason_code"),
                "repair_requirement": row.get("repair_requirement_code"),
                "attempted_sources": [
                    "LANE06_MISSING_LABEL_GAP_LEDGER",
                    "LANE08_MISSING_REPLAY_GAP_LEDGER",
                    "LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER",
                ],
            }
        ],
        "repair_requirement": row.get("repair_requirement_code"),
        "source_gap_origin": row.get("source_gap_origin"),
        "source_use_state": row.get("source_use_state"),
        "result_use_status": "non_reconstructable_gap_row_not_performance_result",
        "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
    }


@dataclass
class SplitStats:
    rows: int = 0
    known_r_rows: int = 0
    gross_r_sum: float = 0.0
    wins: int = 0
    losses: int = 0
    breakevens: int = 0
    source_gap_rows: int = 0
    strict_tick_rows: int = 0
    feature_joined_rows: int = 0
    label_joined_rows: int = 0
    replay_joined_rows: int = 0
    selector_joined_rows: int = 0
    scheduler_joined_rows: int = 0
    scheduler_accepted_rows: int = 0
    scheduler_blocked_or_reduced_rows: int = 0
    policy_joined_rows: int = 0
    correct_reject_rows: int = 0
    missed_opportunity_rows: int = 0
    repairable_scheduler_block_rows: int = 0
    current_policy_cost_median_sum: float = 0.0
    current_policy_cost_median_rows: int = 0
    current_policy_cost_high_sum: float = 0.0
    current_policy_cost_high_rows: int = 0

    def update(self, anatomy: dict[str, Any]) -> None:
        self.rows += 1
        result_r = fnum(anatomy.get("result_r"))
        if result_r is not None:
            self.known_r_rows += 1
            self.gross_r_sum += result_r
            if result_r > 0:
                self.wins += 1
            elif result_r < 0:
                self.losses += 1
            else:
                self.breakevens += 1
        if anatomy.get("source_gap_count"):
            self.source_gap_rows += 1
        if anatomy.get("strict_tick_replay_status") or anatomy.get("current_policy_bid_ask_ordering_state") == "strict_tick_bid_ask_order":
            self.strict_tick_rows += 1
        if str(anatomy.get("feature_join_state") or "").startswith("joined_"):
            self.feature_joined_rows += 1
        if str(anatomy.get("label_join_state") or "").startswith("joined_"):
            self.label_joined_rows += 1
        if str(anatomy.get("replay_join_state") or "").startswith("joined_"):
            self.replay_joined_rows += 1
        if str(anatomy.get("selector_join_state") or "").startswith("joined_"):
            self.selector_joined_rows += 1
        if str(anatomy.get("scheduler_join_state") or "").startswith("joined_"):
            self.scheduler_joined_rows += 1
        scheduler_decision = str(anatomy.get("scheduler_decision") or "")
        if scheduler_decision == "ACCEPTED":
            self.scheduler_accepted_rows += 1
        elif scheduler_decision:
            self.scheduler_blocked_or_reduced_rows += 1
        if str(anatomy.get("policy_join_state") or "").startswith("joined_"):
            self.policy_joined_rows += 1
        if anatomy.get("correct_rejection") is True or anatomy.get("lane10b_classification") == "correct_reject":
            self.correct_reject_rows += 1
        if anatomy.get("missed_opportunity") is True or anatomy.get("missed_edge_scope") not in (None, "", "none"):
            self.missed_opportunity_rows += 1
        if anatomy.get("repairable_scheduler_block") is True:
            self.repairable_scheduler_block_rows += 1
        median = fnum(anatomy.get("current_policy_cost_adjusted_median_r"))
        if median is not None:
            self.current_policy_cost_median_rows += 1
            self.current_policy_cost_median_sum += median
        high = fnum(anatomy.get("current_policy_cost_adjusted_high_stress_r"))
        if high is not None:
            self.current_policy_cost_high_rows += 1
            self.current_policy_cost_high_sum += high

    def as_row(self, split_scope: str, split_key: str) -> dict[str, Any]:
        expectancy = self.gross_r_sum / self.known_r_rows if self.known_r_rows else None
        median_exp = self.current_policy_cost_median_sum / self.current_policy_cost_median_rows if self.current_policy_cost_median_rows else None
        high_exp = self.current_policy_cost_high_sum / self.current_policy_cost_high_rows if self.current_policy_cost_high_rows else None
        return {
            "schema_version": "lane16_split_stress_summary_row_v1",
            "route_id": ROUTE_ID,
            "summary_family": "microscope_event_split",
            "split_scope": split_scope,
            "split_key": split_key,
            "rows": self.rows,
            "known_r_rows": self.known_r_rows,
            "gross_r_sum": round_metric(self.gross_r_sum),
            "expectancy_r": round_metric(expectancy),
            "wins": self.wins,
            "losses": self.losses,
            "breakevens": self.breakevens,
            "win_rate": round_metric(self.wins / self.known_r_rows if self.known_r_rows else None),
            "source_gap_rows": self.source_gap_rows,
            "strict_tick_rows": self.strict_tick_rows,
            "feature_joined_rows": self.feature_joined_rows,
            "label_joined_rows": self.label_joined_rows,
            "replay_joined_rows": self.replay_joined_rows,
            "selector_joined_rows": self.selector_joined_rows,
            "scheduler_joined_rows": self.scheduler_joined_rows,
            "scheduler_accepted_rows": self.scheduler_accepted_rows,
            "scheduler_blocked_or_reduced_rows": self.scheduler_blocked_or_reduced_rows,
            "policy_joined_rows": self.policy_joined_rows,
            "correct_reject_rows": self.correct_reject_rows,
            "missed_opportunity_rows": self.missed_opportunity_rows,
            "repairable_scheduler_block_rows": self.repairable_scheduler_block_rows,
            "current_policy_cost_adjusted_median_expectancy_r": round_metric(median_exp),
            "current_policy_cost_adjusted_high_stress_expectancy_r": round_metric(high_exp),
            "cost_stress_expectancy_delta_r": round_metric(high_exp - median_exp) if high_exp is not None and median_exp is not None else None,
        }


@dataclass
class CoverageStats:
    symbol: str
    date: str
    timeline_rows: int = 0
    non_reconstructable_gap_rows: int = 0
    source_gap_rows: int = 0
    strict_tick_rows: int = 0
    min_time_utc: str | None = None
    max_time_utc: str | None = None
    sessions: Counter[str] = field(default_factory=Counter)
    frameworks: Counter[str] = field(default_factory=Counter)
    origin_families: Counter[str] = field(default_factory=Counter)
    path_classes: Counter[str] = field(default_factory=Counter)
    m1_statuses: Counter[str] = field(default_factory=Counter)
    tick_statuses: Counter[str] = field(default_factory=Counter)
    cost_statuses: Counter[str] = field(default_factory=Counter)
    feature_joined_rows: int = 0
    label_joined_rows: int = 0
    replay_joined_rows: int = 0
    scheduler_joined_rows: int = 0
    policy_joined_rows: int = 0

    def _time(self, value: Any) -> None:
        text = iso(value)
        if not text:
            return
        if self.min_time_utc is None or text < self.min_time_utc:
            self.min_time_utc = text
        if self.max_time_utc is None or text > self.max_time_utc:
            self.max_time_utc = text

    def update_event(self, event_row: dict[str, Any], anatomy: dict[str, Any]) -> None:
        self.timeline_rows += 1
        self._time(event_row.get("candidate_time_utc"))
        self.sessions[str(event_row.get("session_bucket") or "unknown_session")] += 1
        self.frameworks[str(event_row.get("framework") or "unknown_framework")] += 1
        self.origin_families[str(event_row.get("origin_family") or "unknown_origin")] += 1
        self.path_classes[str(event_row.get("path_class") or "unknown_path_class")] += 1
        self.m1_statuses[str(anatomy.get("m1_availability_status") or "m1_status_not_materialized_in_lane16")] += 1
        self.tick_statuses[str(anatomy.get("current_policy_bid_ask_ordering_state") or "tick_status_from_lane04_gap_or_m15_proxy")] += 1
        self.cost_statuses[str(anatomy.get("cost_status") or "cost_status_missing")] += 1
        if event_row.get("source_gap_count"):
            self.source_gap_rows += 1
        if event_row.get("strict_tick_event_status") or anatomy.get("current_policy_bid_ask_ordering_state") == "strict_tick_bid_ask_order":
            self.strict_tick_rows += 1
        if str(event_row.get("feature_join_state") or "").startswith("joined_"):
            self.feature_joined_rows += 1
        if str(event_row.get("label_join_state") or "").startswith("joined_"):
            self.label_joined_rows += 1
        if str(event_row.get("replay_join_state") or "").startswith("joined_"):
            self.replay_joined_rows += 1
        if str(event_row.get("scheduler_join_state") or "").startswith("joined_"):
            self.scheduler_joined_rows += 1
        if str(event_row.get("policy_join_state") or "").startswith("joined_"):
            self.policy_joined_rows += 1

    def update_gap(self, gap_row: dict[str, Any]) -> None:
        self.non_reconstructable_gap_rows += 1
        self._time(gap_row.get("candidate_time_utc"))
        self.sessions[str(gap_row.get("session_bucket") or "unknown_session")] += 1
        self.frameworks[str(gap_row.get("framework") or "unknown_framework")] += 1
        self.origin_families[str(gap_row.get("origin_family") or "unknown_origin")] += 1

    def as_row(self) -> dict[str, Any]:
        return {
            "schema_version": "lane16_coverage_inventory_row_v1",
            "route_id": ROUTE_ID,
            "coverage_scope": "symbol_day_window",
            "symbol": self.symbol,
            "date": self.date,
            "week": iso_week(f"{self.date}T00:00:00+00:00"),
            "month": self.date[:7] if self.date else None,
            "timeline_rows": self.timeline_rows,
            "non_reconstructable_gap_rows": self.non_reconstructable_gap_rows,
            "source_gap_rows": self.source_gap_rows,
            "strict_tick_rows": self.strict_tick_rows,
            "first_candidate_time_utc": self.min_time_utc,
            "last_candidate_time_utc": self.max_time_utc,
            "session_counts": dict(sorted(self.sessions.items())),
            "framework_counts": dict(sorted(self.frameworks.items())),
            "origin_family_counts": dict(sorted(self.origin_families.items())),
            "path_class_counts": dict(sorted(self.path_classes.items())),
            "m15_status": "source_bound_m15_proxy_or_better_for_timeline_rows",
            "m1_status_counts": dict(sorted(self.m1_statuses.items())),
            "tick_status_counts": dict(sorted(self.tick_statuses.items())),
            "spread_cost_status_counts": dict(sorted(self.cost_statuses.items())),
            "feature_joined_rows": self.feature_joined_rows,
            "label_joined_rows": self.label_joined_rows,
            "replay_joined_rows": self.replay_joined_rows,
            "scheduler_joined_rows": self.scheduler_joined_rows,
            "policy_joined_rows": self.policy_joined_rows,
            "source_operation": "canonical_symbol_day_microscope_window_from_lane04_materialized_rows_and_lane10_nonreconstructable_gaps",
        }


def update_split_stats(groups: dict[tuple[str, str], SplitStats], anatomy: dict[str, Any]) -> None:
    pairs = [
        ("all", "ALL"),
        ("date", anatomy.get("date")),
        ("week", anatomy.get("week")),
        ("month", anatomy.get("month")),
        ("year", anatomy.get("year")),
        ("symbol", anatomy.get("symbol")),
        ("session", anatomy.get("session_bucket")),
        ("origin_family", anatomy.get("origin_family")),
        ("mechanism_family", anatomy.get("mechanism_family")),
        ("framework", anatomy.get("framework")),
        ("side", anatomy.get("side")),
        ("path_class", anatomy.get("path_class")),
        ("source_completeness_state", anatomy.get("source_completeness_state")),
        ("source_quality_status", anatomy.get("source_quality_status")),
        ("regime_h4_state", anatomy.get("regime_h4_state")),
        ("regime_h4_direction", anatomy.get("regime_h4_direction")),
        ("selector_component", anatomy.get("selector_component")),
        ("scheduler_decision", anatomy.get("scheduler_decision")),
        ("lane09b_reconciliation_class", anatomy.get("lane09b_reconciliation_class")),
        ("lane10b_classification", anatomy.get("lane10b_classification")),
        ("current_router_policy", anatomy.get("current_router_policy")),
        ("best_policy_id", anatomy.get("best_policy_id")),
        ("spread_r_bucket", anatomy.get("spread_r_bucket")),
        ("cost_status", anatomy.get("cost_status")),
        ("symbol_day", f"{anatomy.get('symbol')}|{anatomy.get('date')}"),
        ("symbol_session", f"{anatomy.get('symbol')}|{anatomy.get('session_bucket')}"),
        ("symbol_framework", f"{anatomy.get('symbol')}|{anatomy.get('framework')}"),
        ("framework_side", f"{anatomy.get('framework')}|{anatomy.get('side')}"),
        ("origin_session", f"{anatomy.get('origin_family')}|{anatomy.get('session_bucket')}"),
    ]
    for scope, key in pairs:
        key_text = str(key if key not in (None, "") else "UNKNOWN")
        groups[(scope, key_text)].update(anatomy)


def upstream_artifact_rows() -> list[dict[str, Any]]:
    specs = [
        ("master", MASTER_DIR / "ABSOLUTE_MASTER_VERIFICATION_RESULT.json", None),
        ("lane01_source_inventory", LANE01_DIR / "OUTPUT_MANIFEST.json", "DATA_SOURCE_INVENTORY.jsonl"),
        ("lane02_asof_contract", LANE02_DIR / "LANE02_OUTPUT_MANIFEST.json", "LANE02_ASOF_FIELD_CONTRACT.jsonl"),
        ("lane03_canonical_candidates", LANE03_DIR / "LANE03_OUTPUT_MANIFEST.json", "LANE03_CANONICAL_CANDIDATE_LEDGER.jsonl.gz"),
        ("lane04_timeline", LANE04_DIR / "LANE04_OUTPUT_MANIFEST.json", "LANE04_ROW_TIMELINE_LEDGER.jsonl"),
        ("lane05_timeline_features", LANE05_DIR / "LANE05_OUTPUT_MANIFEST.json", "LANE05_TIMELINE_FEATURE_VECTOR_LEDGER.jsonl.gz"),
        ("lane06_labels", LANE06_DIR / "LANE06_OUTPUT_MANIFEST.json", "LANE06_LABEL_VECTOR_LEDGER.jsonl.gz"),
        ("lane06_missing_labels", LANE06_DIR / "LANE06_OUTPUT_MANIFEST.json", "LANE06_MISSING_LABEL_GAP_LEDGER.jsonl.gz"),
        ("lane07_broker_truth", LANE07_DIR / "LANE07_OUTPUT_MANIFEST.json", "LANE07_BROKER_TRUTH_LEDGER.jsonl"),
        ("lane08_replay", LANE08_DIR / "LANE08_OUTPUT_MANIFEST.json", "LANE08_REPLAY_ROW_LEDGER.jsonl.gz"),
        ("lane09_selector", LANE09_DIR / "LANE09_OUTPUT_MANIFEST.json", "LANE09_SELECTOR_ROW_EVIDENCE_LEDGER.jsonl.gz"),
        ("lane09b_reconciliation", LANE09B_DIR / "LANE09B_OUTPUT_MANIFEST.json", "LANE09B_SELECTOR_TO_SCHEDULER_ROW_JOIN_LEDGER.jsonl.gz"),
        ("lane10_scheduler", LANE10_DIR / "LANE10_OUTPUT_MANIFEST.json", "LANE10_SCHEDULER_REPLAY_LEDGER.jsonl.gz"),
        ("lane10_missing_scheduler", LANE10_DIR / "LANE10_OUTPUT_MANIFEST.json", "LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz"),
        ("lane10b_conflict", LANE10B_DIR / "LANE10B_OUTPUT_MANIFEST.json", "LANE10B_FULL_CONFLICT_ANATOMY_LEDGER.jsonl.gz"),
        ("lane11_policy", LANE11_DIR / "LANE11_OUTPUT_MANIFEST.json", "LANE11_POLICY_SIMULATION_LEDGER.jsonl.gz"),
    ]
    rows: list[dict[str, Any]] = []
    for source_family, manifest, artifact_name in specs:
        line_count_value = None if artifact_name is None else manifest_line_count(manifest, artifact_name)
        rows.append(
            {
                "schema_version": "lane16_coverage_inventory_row_v1",
                "route_id": ROUTE_ID,
                "coverage_scope": "source_artifact",
                "source_family": source_family,
                "manifest_path": rel(manifest),
                "artifact_name": artifact_name,
                "line_count": line_count_value,
                "source_operation": "upstream_terminal_artifact_consumed_from_disk",
            }
        )
    return rows


def dependency_rows(index_states: list[IndexState], summary: dict[str, Any]) -> list[dict[str, Any]]:
    lane_specs = [
        ("MASTER", MASTER_DIR / "ABSOLUTE_MASTER_VERIFICATION_RESULT.json", MASTER_DIR / "ABSOLUTE_MASTER_NEXT_WAVE_LAUNCH_DECISION.json"),
        ("01", LANE01_DIR / "VERIFICATION_RESULT.json", LANE01_DIR / "COMPLETION_AUDIT.json"),
        ("02", LANE02_DIR / "LANE02_VERIFICATION_RESULT.json", LANE02_DIR / "LANE02_COMPLETION_AUDIT.json"),
        ("03", LANE03_DIR / "LANE03_VERIFICATION_RESULT.json", LANE03_DIR / "LANE03_COMPLETION_AUDIT.json"),
        ("04", LANE04_DIR / "LANE04_VERIFICATION_RESULT.json", LANE04_DIR / "LANE04_COMPLETION_AUDIT.json"),
        ("05", LANE05_DIR / "LANE05_VERIFICATION_RESULT.json", LANE05_DIR / "LANE05_COMPLETION_AUDIT.json"),
        ("06", LANE06_DIR / "LANE06_VERIFICATION_RESULT.json", LANE06_DIR / "LANE06_COMPLETION_AUDIT.json"),
        ("07", LANE07_DIR / "LANE07_VERIFICATION_RESULT.json", LANE07_DIR / "LANE07_COMPLETION_AUDIT.json"),
        ("08", LANE08_DIR / "LANE08_VERIFICATION_RESULT.json", LANE08_DIR / "LANE08_COMPLETION_AUDIT.json"),
        ("09", LANE09_DIR / "LANE09_VERIFICATION_RESULT.json", LANE09_DIR / "LANE09_COMPLETION_AUDIT.json"),
        ("09B", LANE09B_DIR / "LANE09B_VERIFICATION_RESULT.json", LANE09B_DIR / "LANE09B_COMPLETION_AUDIT.json"),
        ("10", LANE10_DIR / "LANE10_VERIFICATION_RESULT.json", LANE10_DIR / "LANE10_COMPLETION_AUDIT.json"),
        ("10B", LANE10B_DIR / "LANE10B_VERIFICATION_RESULT.json", LANE10B_DIR / "LANE10B_COMPLETION_AUDIT.json"),
        ("11", LANE11_DIR / "LANE11_VERIFICATION_RESULT.json", LANE11_DIR / "LANE11_COMPLETION_AUDIT.json"),
    ]
    rows = []
    for lane_id, verifier_path, audit_path in lane_specs:
        verifier = read_json(verifier_path, {})
        audit = read_json(audit_path, {})
        rows.append(
            {
                "schema_version": "lane16_dependency_state_row_v1",
                "route_id": ROUTE_ID,
                "dependency_id": lane_id,
                "verification_path": rel(verifier_path),
                "verification_ok": bool(verifier.get("ok", True)) if verifier else False,
                "completion_audit_path": rel(audit_path),
                "completion_status": audit.get("status") or audit.get("completion_status") or verifier.get("status"),
                "runtime_effect_boundary": audit.get("runtime_effect_boundary"),
                "source_use_state": audit.get("source_use_state"),
                "consumption_state": "read_from_disk_and_consumed_by_lane16_builder",
            }
        )
    for state in index_states:
        rows.append(
            {
                "schema_version": "lane16_dependency_state_row_v1",
                "route_id": ROUTE_ID,
                "dependency_id": state.name,
                "path": state.path,
                "rows": state.rows,
                "indexed_rows": state.indexed_rows,
                "missing_key_rows": state.missing_key_rows,
                "duplicate_key_rows": state.duplicate_key_rows,
                "consumption_state": "indexed_for_row_level_cross_lane_join",
            }
        )
    rows.append(
        {
            "schema_version": "lane16_dependency_state_row_v1",
            "route_id": ROUTE_ID,
            "dependency_id": "lane16_row_count_summary",
            "event_rows": summary["event_rows"],
            "path_anatomy_rows": summary["path_anatomy_rows"],
            "source_gap_rows": summary["source_gap_rows"],
            "non_reconstructable_gap_rows": summary["non_reconstructable_gap_rows"],
            "consumption_state": "all_materialized_or_gap_accounted",
        }
    )
    return rows


def source_completeness_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "lane16_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "microscope_capable_timeline_rows",
            "status": "materialized_full_lane04_denominator_with_cross_lane_joins",
            "rows": summary["event_rows"],
            "decision": "consume_as_scaled_historical_microscope_event_and_path_anatomy_rows",
            "repair_requirement": None,
        },
        {
            "schema_version": "lane16_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "canonical_candidates_without_joined_label_replay_scheduler",
            "status": "non_reconstructable_from_current_inputs_but_preserved_as_exact_gap_rows",
            "rows": summary["non_reconstructable_gap_rows"],
            "decision": "preserve_gap_rows_and_require_run_or_join_microscope_replay_or_readonly_broker_lifecycle_cost_source",
            "repair_requirement": "RUN_OR_JOIN_MICROSCOPE_REPLAY_OR_READONLY_BROKER_LIFECYCLE_COST_SOURCE",
        },
        {
            "schema_version": "lane16_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "ordered_bid_ask_tick_timeline",
            "status": "partial_exact_tick_materialization_plus_m15_proxy_gap_rows",
            "rows": summary["source_gap_rows"],
            "decision": "use strict/friday tick where present; otherwise keep row-level tick source gap",
            "repair_requirement": "deterministic tick export/parser for selected row date/symbol or accepted proxy boundary",
        },
        {
            "schema_version": "lane16_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "broker_cost_lifecycle_net_r",
            "status": "sparse_broker_truth_cost_rows_consumed_but_full_historical_net_r_not_reconstructable",
            "rows": summary["source_gap_rows"],
            "decision": "do not invent broker/account/deal/order truth from price; preserve broker cost source gaps for Lane18",
            "repair_requirement": "read-only broker deal/order/position/cost export or prospective lifecycle capture",
        },
        {
            "schema_version": "lane16_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source_family": "d1_h4_h1_m15_m1_tick_spread_cost_coverage",
            "status": "explicit_symbol_day_coverage_inventory_written_for_available_row-level states",
            "rows": summary["coverage_inventory_rows"],
            "decision": "coverage inventory is downstream source authority for Lane17/ML/V3 engines; missing exact fields remain gaps",
            "repair_requirement": "consume Lane01 source authority and source-specific exports before treating missing fields as closed",
        },
    ]


def implementation_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "lane16_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "materialize_scaled_historical_microscope_engine",
            "reason": "Lane04 Friday-style microscope and Lane05-Lane11 terminal outputs support full row-level cross-lane event/path anatomy joins over the microscope-capable denominator",
            "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
        },
        {
            "schema_version": "lane16_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "preserve_non_reconstructable_canonical_candidate_gap_rows",
            "reason": "Lane06/Lane08/Lane10 prove canonical candidates without joined label/replay/scheduler truth; these rows are exact source gaps, not discarded rows or performance results",
            "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
        },
        {
            "schema_version": "lane16_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "reject_friday_only_ml_only_aggregate_only_closure",
            "reason": "Lane16 writes full event/anatomy/source-gap/split/coverage contracts across all source-supported symbols/windows and leaves ML as a downstream consumer",
            "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
        },
    ]


def downstream_contract() -> dict[str, Any]:
    consumers = {
        "Market Awareness": {
            "consume": [rel(COVERAGE_INVENTORY), rel(EVENT_LEDGER)],
            "required_fields": ["symbol", "date", "session_bucket", "regime_h4_state", "source_gap_families", "spread_r_bucket"],
        },
        "Selector V3": {
            "consume": [rel(PATH_ANATOMY_LEDGER), rel(SPLIT_STRESS_SUMMARY)],
            "required_fields": ["selector_component", "lane09_mechanism_decision", "path_class", "result_r", "source_gap_families"],
        },
        "Scheduler V3": {
            "consume": [rel(PATH_ANATOMY_LEDGER), rel(SPLIT_STRESS_SUMMARY)],
            "required_fields": ["scheduler_decision", "approved_risk_pct", "total_risk_pct_before", "lane10b_classification", "repairable_scheduler_block"],
        },
        "Execution V3": {
            "consume": [rel(PATH_ANATOMY_LEDGER)],
            "required_fields": ["current_router_policy", "best_policy_id", "current_policy_cost_adjusted_median_r", "policy_cost_stress_delta_r"],
        },
        "ML": {
            "consume": [rel(EVENT_LEDGER), rel(PATH_ANATOMY_LEDGER), rel(SOURCE_GAP_LEDGER)],
            "required_fields": ["result_r_class", "source_gap_families", "date", "symbol", "framework", "side"],
        },
        "Repair Companion": {
            "consume": [rel(SOURCE_GAP_LEDGER), rel(SOURCE_COMPLETENESS_LEDGER)],
            "required_fields": ["gap_source_family", "source_gap_families", "repair_requirement"],
        },
        "Command Center": {
            "consume": [rel(COVERAGE_INVENTORY), rel(SPLIT_STRESS_SUMMARY)],
            "required_fields": ["coverage_scope", "timeline_rows", "non_reconstructable_gap_rows", "source_gap_rows"],
        },
    }
    return {
        "schema_version": "lane16_downstream_contract_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "result_scope": "scaled_historical_microscope_research_contract",
        "consumer_contracts": consumers,
        "forbidden_uses": [
            "live production activation",
            "broker/order/deal/position mutation",
            "training labels as no-leak features",
            "broker-real net-R claim where source_gap_families contain broker_cost_and_lifecycle or net_r",
        ],
        "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
    }


def static_status_files(summary: dict[str, Any]) -> None:
    write_json(
        SOURCE_USE_STATE,
        {
            "schema_version": "lane16_source_use_state_v1",
            "route_id": ROUTE_ID,
            "state": "Lane04 row timelines plus Lane05 features, Lane06 labels, Lane07 cost truth, Lane08 replay, Lane09 selector, Lane09B reconciliation, Lane10 scheduler, Lane10B conflict anatomy, and Lane11 policy simulations consumed from disk; Lane10 missing replay gaps preserve non-reconstructable canonical candidates.",
            "event_rows": summary["event_rows"],
            "non_reconstructable_gap_rows": summary["non_reconstructable_gap_rows"],
            "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
        },
    )
    write_json(
        RESULT_USE_STATUS,
        {
            "schema_version": "lane16_result_use_status_v1",
            "route_id": ROUTE_ID,
            "status": "scaled_microscope_rows_are_research_training_selector_scheduler_execution_repair_inputs_not_live_activation_not_broker_real_performance_claim",
            "exact_proxy_boundary": "broker-real, strict-tick, friday-tick, m15-proxy, cost-proxy, and non-reconstructable gap rows remain separate evidence classes",
            "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
        },
    )
    write_json(
        RUNTIME_EFFECT_BOUNDARY,
        {
            "schema_version": "lane16_runtime_effect_boundary_v1",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
            "live_broker_order_operation": False,
            "broker_account_order_history_deal_position_mutation": False,
            "paid_api_vendor_call": False,
            "credential_or_remote_change": False,
            "prompt_config_risk_execution_safety_canary_selector_live_behavior_change": False,
            "default_off_or_dossier_only": True,
        },
    )


def build_context_anchor(now: str, summary: dict[str, Any]) -> None:
    CONTEXT_ANCHOR.write_text(
        "\n".join(
            [
                "# Lane16 Historical Microscope Scale Context Anchor",
                "",
                f"Generated: {now}",
                f"Git HEAD: `{git_head()}`",
                f"Route: `{ROUTE_ID}`",
                f"Controlling prompt: `{rel(PROMPT_PATH)}`",
                f"Starter: `{rel(STARTER_PATH)}`",
                "",
                "Evidence class: offline historical microscope/replay builder. No live broker/order/deal/position action, no paid API/vendor call, no credentials/remotes, no hidden live behavior change.",
                "",
                f"Materialized microscope event rows: `{summary['event_rows']}`.",
                f"Materialized path anatomy rows: `{summary['path_anatomy_rows']}`.",
                f"Materialized source gap rows: `{summary['source_gap_rows']}` including `{summary['non_reconstructable_gap_rows']}` non-reconstructable canonical candidate gap rows.",
                f"Coverage inventory rows: `{summary['coverage_inventory_rows']}`.",
                "",
                "Resume rule: regenerate `.context/LIVE_STATE.md`, reread the controlling prompt/starter/doctrine and this anchor, then run this builder with `--check` before making status claims.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def output_manifest(now: str, counts: dict[str, int]) -> dict[str, Any]:
    outputs = [
        EVENT_LEDGER,
        PATH_ANATOMY_LEDGER,
        SOURCE_GAP_LEDGER,
        COVERAGE_INVENTORY,
        SPLIT_STRESS_SUMMARY,
        SOURCE_COMPLETENESS_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        DOWNSTREAM_CONTRACT,
        SOURCE_USE_STATE,
        RESULT_USE_STATUS,
        RUNTIME_EFFECT_BOUNDARY,
        COMPLETION_AUDIT,
        VERIFICATION_RESULT,
        FOCUSED_TEST_RESULT,
        CONTEXT_ANCHOR,
        VERIFIER,
        Path(__file__),
        OUTPUT_MANIFEST,
    ]
    return {
        "schema_version": "lane16_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "git_head": git_head(),
        "output_count": len(outputs),
        "outputs": [
            {
                "path": rel(path),
                "bytes": path.stat().st_size if path.exists() else None,
                "line_count": counts.get(path.name),
                "sha256": None if path == OUTPUT_MANIFEST or not path.exists() else sha256_file(path),
            }
            for path in outputs
        ],
    }


def load_sidecar_indexes() -> tuple[dict[str, dict[str, dict[str, Any]]], list[IndexState]]:
    specs = [
        ("lane05_timeline_features", LANE05_TIMELINE_FEATURES, ("upstream_row_id", "duplicate_key", "selected_row_id", "row_id"), feature_mapper),
        ("lane06_label_vectors", LANE06_LABELS, ("source_row_id", "selected_row_id", "row_id"), label_mapper),
        ("lane08_replay_rows", LANE08_REPLAY, ("selected_row_id", "row_id"), replay_mapper),
        ("lane09_selector_rows", LANE09_SELECTOR, ("selected_row_id", "source_row_id", "row_id"), selector_mapper),
        ("lane10_scheduler_rows", LANE10_SCHEDULER, ("selected_row_id", "row_id"), scheduler_mapper),
        ("lane09b_selector_scheduler_join_rows", LANE09B_JOIN, ("selected_row_id", "source_row_id", "lane10_row_id"), reconciliation_mapper),
        ("lane10b_conflict_anatomy_rows", LANE10B_CONFLICT, ("selected_row_id", "row_id"), conflict_mapper),
        ("lane11_policy_simulation_rows", LANE11_POLICY, ("selected_row_id", "row_id"), policy_mapper),
    ]
    indexes: dict[str, dict[str, dict[str, Any]]] = {}
    states: list[IndexState] = []
    aliases = ["feature", "label", "replay", "selector", "scheduler", "reconciliation", "conflict", "policy"]
    for alias, (name, path, keys, mapper) in zip(aliases, specs):
        index, state = load_index(name, path, keys, mapper)
        indexes[alias] = index
        states.append(state)
    return indexes, states


def sidecars_for_row(timeline: dict[str, Any], indexes: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, Any] | None]:
    keys = [
        str(timeline.get("selected_row_id") or ""),
        str(timeline.get("row_id") or ""),
        str(timeline.get("candidate_id") or ""),
    ]
    result: dict[str, dict[str, Any] | None] = {}
    for alias, index in indexes.items():
        found = None
        for key in keys:
            if key and key in index:
                found = index[key]
                break
        result[alias] = found
    return result


def build_outputs(write: bool = True) -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    indexes, index_states = load_sidecar_indexes()

    split_groups: dict[tuple[str, str], SplitStats] = defaultdict(SplitStats)
    coverage: dict[tuple[str, str], CoverageStats] = {}
    gap_splits: Counter[tuple[str, str]] = Counter()
    event_rows = 0
    path_anatomy_rows = 0
    materialized_source_gap_rows = 0
    non_reconstructable_gap_rows = 0
    sidecar_missing_counts: Counter[str] = Counter()

    with gzip.open(EVENT_LEDGER, "wt", encoding="utf-8", errors="replace", newline="\n", compresslevel=6) as event_handle, gzip.open(
        PATH_ANATOMY_LEDGER, "wt", encoding="utf-8", errors="replace", newline="\n", compresslevel=6
    ) as anatomy_handle, gzip.open(SOURCE_GAP_LEDGER, "wt", encoding="utf-8", errors="replace", newline="\n", compresslevel=6) as gap_handle:
        for _, timeline in iter_jsonl(LANE04_TIMELINE):
            sidecars = sidecars_for_row(timeline, indexes)
            for alias, payload in sidecars.items():
                if not payload:
                    sidecar_missing_counts[alias] += 1
            event_row = build_microscope_event(timeline, sidecars)
            anatomy = build_path_anatomy(event_row, sidecars)
            anatomy["tick_availability_status"] = timeline.get("tick_availability_status")
            anatomy["m1_availability_status"] = timeline.get("m1_availability_status")
            anatomy["cost_status"] = timeline.get("cost_status")
            anatomy["spread_r_bucket"] = timeline.get("spread_r_bucket")
            anatomy["strict_tick_replay_status"] = timeline.get("strict_tick_event_status")
            write_jsonl_line(event_handle, event_row)
            write_jsonl_line(anatomy_handle, anatomy)
            event_rows += 1
            path_anatomy_rows += 1
            update_split_stats(split_groups, anatomy)
            symbol = str(event_row.get("symbol") or "UNKNOWN_SYMBOL")
            date = str(event_row.get("date") or "UNKNOWN_DATE")
            cov = coverage.setdefault((symbol, date), CoverageStats(symbol=symbol, date=date))
            cov.update_event(event_row, anatomy)
            gap_row = lane16_gap_from_event(event_row)
            if gap_row:
                write_jsonl_line(gap_handle, gap_row)
                materialized_source_gap_rows += 1
                for family in gap_row.get("source_gap_families") or []:
                    gap_splits[("gap_family", str(family))] += 1
                gap_splits[("gap_symbol", symbol)] += 1
                gap_splits[("gap_month", str(event_row.get("month") or "UNKNOWN_MONTH"))] += 1

        for _, missing in iter_jsonl(LANE10_MISSING_GAPS):
            gap_row = lane16_gap_from_missing_scheduler(missing)
            write_jsonl_line(gap_handle, gap_row)
            non_reconstructable_gap_rows += 1
            materialized_source_gap_rows += 1
            symbol = str(gap_row.get("symbol") or "UNKNOWN_SYMBOL")
            date = str(gap_row.get("date") or "UNKNOWN_DATE")
            cov = coverage.setdefault((symbol, date), CoverageStats(symbol=symbol, date=date))
            cov.update_gap(gap_row)
            gap_splits[("gap_family", "canonical_candidate_without_joined_microscope_label_replay_scheduler")] += 1
            gap_splits[("gap_symbol", symbol)] += 1
            gap_splits[("gap_month", str(gap_row.get("month") or "UNKNOWN_MONTH"))] += 1
            gap_splits[("gap_framework", str(gap_row.get("framework") or "UNKNOWN_FRAMEWORK"))] += 1

    split_rows = [stats.as_row(scope, key) for (scope, key), stats in sorted(split_groups.items())]
    for (scope, key), rows in sorted(gap_splits.items()):
        split_rows.append(
            {
                "schema_version": "lane16_split_stress_summary_row_v1",
                "route_id": ROUTE_ID,
                "summary_family": "source_gap_split",
                "split_scope": scope,
                "split_key": key,
                "rows": rows,
                "result_use_status": "source_gap_split_not_performance_result",
            }
        )
    split_rows_count = write_jsonl(SPLIT_STRESS_SUMMARY, split_rows)

    coverage_rows = upstream_artifact_rows()
    coverage_rows.extend(cov.as_row() for _, cov in sorted(coverage.items(), key=lambda item: (item[0][0], item[0][1])))
    coverage_count = write_jsonl(COVERAGE_INVENTORY, coverage_rows)

    summary = {
        "schema_version": "lane16_build_summary_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "git_head": git_head(),
        "event_rows": event_rows,
        "path_anatomy_rows": path_anatomy_rows,
        "source_gap_rows": materialized_source_gap_rows,
        "non_reconstructable_gap_rows": non_reconstructable_gap_rows,
        "coverage_inventory_rows": coverage_count,
        "split_stress_rows": split_rows_count,
        "sidecar_missing_counts": dict(sorted(sidecar_missing_counts.items())),
        "active_symbol_count_in_coverage": len({symbol for symbol, _ in coverage if symbol in ACTIVE_SYMBOLS}),
        "result_scope": "scaled_historical_microscope_event_path_source_gap_split_contracts",
        "source_use_state": "all_terminal_master_lane01_lane11_lane09b_lane10b_sources_read_from_disk_and_consumed",
        "result_use_status": "research_training_selector_scheduler_execution_repair_inputs_not_production_change",
        "runtime_effect_boundary": "offline_research_artifacts_only_no_live_behavior_change",
    }
    write_jsonl(SOURCE_COMPLETENESS_LEDGER, source_completeness_rows(summary))
    write_jsonl(IMPLEMENTATION_DECISION_LEDGER, implementation_decision_rows())
    write_jsonl(DEPENDENCY_STATE_LEDGER, dependency_rows(index_states, summary))
    write_json(DOWNSTREAM_CONTRACT, downstream_contract())
    static_status_files(summary)
    build_context_anchor(now, summary)

    audit = {
        "schema_version": "lane16_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": now,
        "status": "complete_pending_verifier_and_focused_tests",
        "mandatory_context_use": {
            "live_state_regenerated": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "moonshot_vision_read": True,
            "master_read_from_disk": True,
            "lane01_lane11_lane09b_lane10b_read_from_disk": True,
            "lane16_prompt_and_starter_read": True,
        },
        "requirements": [
            {"requirement": "builder_code", "status": "complete", "evidence": rel(Path(__file__))},
            {"requirement": "coverage_inventory", "status": "complete", "rows": summary["coverage_inventory_rows"], "evidence": rel(COVERAGE_INVENTORY)},
            {"requirement": "microscope_event_ledger", "status": "complete", "rows": summary["event_rows"], "evidence": rel(EVENT_LEDGER)},
            {"requirement": "path_anatomy_ledger", "status": "complete", "rows": summary["path_anatomy_rows"], "evidence": rel(PATH_ANATOMY_LEDGER)},
            {"requirement": "source_gap_ledger", "status": "complete", "rows": summary["source_gap_rows"], "evidence": rel(SOURCE_GAP_LEDGER)},
            {"requirement": "non_reconstructable_canonical_gap_rows", "status": "complete", "rows": summary["non_reconstructable_gap_rows"], "evidence": rel(SOURCE_GAP_LEDGER)},
            {"requirement": "split_stress_outputs", "status": "complete", "rows": summary["split_stress_rows"], "evidence": rel(SPLIT_STRESS_SUMMARY)},
            {"requirement": "downstream_contracts", "status": "complete", "evidence": rel(DOWNSTREAM_CONTRACT)},
            {"requirement": "source_completeness_decisions", "status": "complete", "evidence": rel(SOURCE_COMPLETENESS_LEDGER)},
            {"requirement": "implementation_decisions", "status": "complete", "evidence": rel(IMPLEMENTATION_DECISION_LEDGER)},
            {"requirement": "manifest_verifier_focused_tests", "status": "pending_until_verifier_and_pytest_run", "evidence": [rel(OUTPUT_MANIFEST), rel(VERIFIER), rel(VERIFICATION_RESULT), rel(FOCUSED_TEST_RESULT)]},
            {"requirement": "scoped_commit", "status": "pending_external_git_commit_after_verification", "evidence": None},
        ],
        "anti_boxing_questions_pursued": [
            "not Friday-only: Lane04 full microscope-capable denominator plus Friday rows consumed",
            "not one-symbol: coverage inventory requires all 24 active symbols where source-supported/gap-supported",
            "not one-policy: Lane11 policy simulation summaries and cost-stress fields are joined",
            "not aggregate-only: event, path anatomy, and source-gap ledgers preserve material rows",
            "not ML-only: downstream contract feeds Market Awareness, Selector V3, Scheduler V3, Execution V3, ML, Repair Companion, and Command Center",
        ],
        "open_source_gaps_not_hidden": [
            "canonical candidates without joined label/replay/scheduler truth are preserved as non-reconstructable gap rows",
            "full historical broker net-R/cost/deal/order lifecycle remains missing where Lane07 cannot join it",
            "ordered bid/ask tick coverage remains partial; M15 proxy rows keep exact source-gap proof",
        ],
        "proof_or_impossibility_stop_condition": "all terminal disk sources were consumed into row-level artifacts or exact non-reconstructable gap rows inside the offline research evidence class",
        "summary": summary,
        "source_use_state": summary["source_use_state"],
        "result_use_status": summary["result_use_status"],
        "runtime_effect_boundary": summary["runtime_effect_boundary"],
        "forbidden_surface_attestation": {
            "live_broker_order_operation": False,
            "broker_account_order_history_deal_position_mutation": False,
            "paid_api_vendor_call": False,
            "credential_or_remote_change": False,
            "remote_push": False,
            "hidden_production_activation": False,
            "prompt_config_risk_execution_safety_canary_selector_live_behavior_change": False,
        },
    }
    write_json(COMPLETION_AUDIT, audit)
    counts = {
        EVENT_LEDGER.name: event_rows,
        PATH_ANATOMY_LEDGER.name: path_anatomy_rows,
        SOURCE_GAP_LEDGER.name: materialized_source_gap_rows,
        COVERAGE_INVENTORY.name: coverage_count,
        SPLIT_STRESS_SUMMARY.name: split_rows_count,
        SOURCE_COMPLETENESS_LEDGER.name: len(source_completeness_rows(summary)),
        DEPENDENCY_STATE_LEDGER.name: len(dependency_rows(index_states, summary)),
        IMPLEMENTATION_DECISION_LEDGER.name: len(implementation_decision_rows()),
    }
    write_json(OUTPUT_MANIFEST, output_manifest(now, counts))
    return summary


def import_verifier():
    spec = importlib.util.spec_from_file_location("lane16_verifier", VERIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import verifier: {VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def refresh_audit_and_manifest(verification: dict[str, Any]) -> None:
    now = utc_now()
    audit = read_json(COMPLETION_AUDIT, {})
    if isinstance(audit, dict) and audit:
        for requirement in audit.get("requirements") or []:
            if requirement.get("requirement") == "manifest_verifier_focused_tests":
                requirement["status"] = "complete" if verification.get("ok") and FOCUSED_TEST_RESULT.exists() else "verifier_complete_focused_tests_pending"
                requirement["verifier_ok"] = bool(verification.get("ok"))
                requirement["focused_test_result_present"] = FOCUSED_TEST_RESULT.exists()
            if requirement.get("requirement") == "scoped_commit" and verification.get("ok") and FOCUSED_TEST_RESULT.exists():
                requirement["status"] = "ready_for_scoped_commit"
        audit["last_verification_refresh_at_utc"] = now
        audit["verifier_ok"] = bool(verification.get("ok"))
        audit["focused_test_result_present"] = FOCUSED_TEST_RESULT.exists()
        audit["status"] = "complete_verified_pending_scoped_commit" if verification.get("ok") and FOCUSED_TEST_RESULT.exists() else audit.get("status")
        write_json(COMPLETION_AUDIT, audit)
    counts = {
        EVENT_LEDGER.name: verification.get("event_rows"),
        PATH_ANATOMY_LEDGER.name: verification.get("path_anatomy_rows"),
        SOURCE_GAP_LEDGER.name: verification.get("source_gap_rows"),
        COVERAGE_INVENTORY.name: verification.get("coverage_inventory_rows"),
        SPLIT_STRESS_SUMMARY.name: verification.get("split_stress_rows"),
        SOURCE_COMPLETENESS_LEDGER.name: line_count(SOURCE_COMPLETENESS_LEDGER),
        DEPENDENCY_STATE_LEDGER.name: line_count(DEPENDENCY_STATE_LEDGER),
        IMPLEMENTATION_DECISION_LEDGER.name: line_count(IMPLEMENTATION_DECISION_LEDGER),
    }
    write_json(OUTPUT_MANIFEST, output_manifest(now, counts))


def verify_outputs(write: bool = True) -> dict[str, Any]:
    module = import_verifier()
    result = module.verify_route(ROUTE_DIR)
    if write:
        write_json(VERIFICATION_RESULT, result)
        refresh_audit_and_manifest(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify existing Lane16 outputs without rebuilding")
    args = parser.parse_args(argv)
    if args.check:
        result = verify_outputs(write=True)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("ok") else 1
    summary = build_outputs(write=True)
    result = verify_outputs(write=True)
    print(json.dumps({"summary": summary, "verification": result}, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
