from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ROUTE_ID = "vnext_absolute_moonshot_execution_policy_v3_2026_06_01"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

LANE01_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
LANE02_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"
LANE03_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01"
LANE04_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01"
LANE05_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE06_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE07_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
LANE08_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
LANE09B_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane09b_selector_scheduler_reconciliation_2026_06_01"
LANE10B_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01"
LANE11_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01"
LANE16_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01"
LANE17_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_lane17_market_awareness_whiteboard_2026_06_01"
LANE18_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01"
POST_LANE18_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01"
MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"

RUNTIME_EFFECT_BOUNDARY = (
    "default_off_execution_policy_v3_artifacts_only_no_live_broker_order_deal_"
    "position_operation_no_config_prompt_risk_execution_safety_canary_selector_"
    "scheduler_activation_no_paid_api_no_remote"
)
RESULT_USE_STATUS = (
    "execution_policy_v3_default_off_research_package_only; exact broker R is "
    "used only where upstream owns broker-real rows, proxy R remains source-bound "
    "and cannot be promoted to production without a separate production-change dossier"
)
SOURCE_USE_STATE = (
    "current disk route artifacts Lane01-Lane18, Lane09B, Lane10B, post-Lane18 "
    "source repair, and read-only execution/lifecycle/broker diagnostic code; no "
    "broker mutation, no paid calls, no live behavior activation"
)

OUTPUTS = {
    "context_anchor": ROUTE_DIR / "V3_CONTEXT_ANCHOR.md",
    "input_evidence": ROUTE_DIR / "V3_INPUT_EVIDENCE_INSPECTION_LEDGER.jsonl",
    "code_surface": ROUTE_DIR / "V3_CODE_SURFACE_AUDIT_LEDGER.jsonl",
    "policy_registry": ROUTE_DIR / "V3_POLICY_VARIANT_REGISTRY.jsonl",
    "evaluation": ROUTE_DIR / "V3_FEASIBLE_POLICY_EVALUATION_LEDGER.jsonl.gz",
    "source_gaps": ROUTE_DIR / "V3_NON_REPLAYABLE_SOURCE_GAP_LEDGER.jsonl.gz",
    "routing_package": ROUTE_DIR / "V3_DEFAULT_OFF_EXECUTION_POLICY_PACKAGE.json",
    "routing_ledger": ROUTE_DIR / "V3_POLICY_ROUTING_DECISION_LEDGER.jsonl.gz",
    "lifecycle_feasibility": ROUTE_DIR / "V3_LIFECYCLE_BROKER_TICK_FEASIBILITY_LEDGER.jsonl",
    "failure_anatomy": ROUTE_DIR / "V3_POLICY_FAILURE_ANATOMY_LEDGER.jsonl.gz",
    "source_decisions": ROUTE_DIR / "V3_SOURCE_CAPTURE_AND_COMPLETENESS_DECISIONS.jsonl",
    "branch_decisions": ROUTE_DIR / "V3_BRANCH_DECISION_LEDGER.jsonl",
    "implementation_decisions": ROUTE_DIR / "V3_IMPLEMENTATION_DECISION_LEDGER.jsonl",
    "result_use": ROUTE_DIR / "V3_RESULT_USE_STATUS.json",
    "split_stress": ROUTE_DIR / "V3_SPLIT_STRESS_DECONCENTRATION_LEDGER.jsonl",
    "downstream_contracts": ROUTE_DIR / "V3_DOWNSTREAM_CONTRACTS.json",
    "runtime_boundary": ROUTE_DIR / "V3_RUNTIME_EFFECT_BOUNDARY.json",
    "source_use": ROUTE_DIR / "V3_SOURCE_USE_STATE.json",
    "saturation": ROUTE_DIR / "V3_SATURATION_SELF_RED_TEAM.md",
    "manifest": ROUTE_DIR / "V3_OUTPUT_MANIFEST.json",
    "verification": ROUTE_DIR / "V3_VERIFICATION_RESULT.json",
    "completion": ROUTE_DIR / "V3_COMPLETION_AUDIT.json",
    "focused_test": ROUTE_DIR / "V3_FOCUSED_TEST_RESULT.xml",
}

ROUTE_SOURCE_FILES = {
    "route_gitattributes": ROUTE_DIR / ".gitattributes",
    "builder": ROUTE_DIR / "build_vnext_absolute_moonshot_execution_policy_v3.py",
    "verifier": ROUTE_DIR / "verify_vnext_absolute_moonshot_execution_policy_v3.py",
    "focused_test_source": ROUTE_DIR / "test_vnext_absolute_moonshot_execution_policy_v3.py",
}

LANE11_EXPANDED_REGISTRY = LANE11_DIR / "LANE11_EXPANDED_POLICY_VARIANT_REGISTRY.jsonl"
LANE11_EXPANDED_FEASIBILITY = LANE11_DIR / "LANE11_EXPANDED_POLICY_FEASIBILITY_LEDGER.jsonl"
LANE11_EXPANDED_METRICS = LANE11_DIR / "LANE11_EXPANDED_POLICY_SIMULATION_METRIC_LEDGER.jsonl.gz"
LANE11_EXPANDED_DOMINANCE = LANE11_DIR / "LANE11_EXPANDED_POLICY_DOMINANCE_DECISION_LEDGER.jsonl.gz"
LANE11_EXPANDED_PACKAGE = LANE11_DIR / "LANE11_EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER.jsonl.gz"
LANE11_EXPANDED_SOURCE_GAPS = LANE11_DIR / "LANE11_EXPANDED_POLICY_SOURCE_GAP_LEDGER.jsonl.gz"
LANE11_BASELINE_METRICS = LANE11_DIR / "LANE11_POLICY_METRIC_LEDGER.jsonl"
LANE11_BASELINE_DOMINANCE = LANE11_DIR / "LANE11_POLICY_DOMINANCE_DECISION_LEDGER.jsonl"
LANE11_BASELINE_PACKAGE = LANE11_DIR / "LANE11_DEFAULT_OFF_POLICY_ROUTER_PACKAGE_LEDGER.jsonl"

LANE16_PATH = LANE16_DIR / "LANE16_PATH_ANATOMY_LEDGER.jsonl.gz"
LANE16_SPLIT = LANE16_DIR / "LANE16_SPLIT_STRESS_SUMMARY.jsonl"
LANE17_GAPS = LANE17_DIR / "LANE17_SOURCE_GAP_LEDGER.jsonl.gz"
LANE18_GAPS = LANE18_DIR / "LANE18_SOURCE_GAP_LEDGER.jsonl"
LANE18_PROSPECTIVE = LANE18_DIR / "LANE18_PROSPECTIVE_CAPTURE_REQUIREMENTS.jsonl"
POST_SOURCE_DECISIONS = POST_LANE18_DIR / "POST_LANE18_SOURCE_COMPLETENESS_DECISIONS.jsonl"

SUPPORTED_RUNTIME_POLICIES = {
    "be_after_trigger",
    "partial_be_runner",
    "trailing_runner",
    "momentum_exhaustion",
    "time_stop",
}
COMPARATOR_POLICIES = {
    "fixed_1_5r",
    "live_current_j46_j49",
    "legacy_fixed_1.5r",
    "current_router_policy",
    "no_trade_baseline",
}
MODIFY_DEPENDENT = {
    "be_after_trigger",
    "partial_be_runner",
    "trailing_runner",
    "momentum_exhaustion",
}
PARTIAL_DEPENDENT = {"partial_be_runner"}
BROKER_FIELD_FAMILIES = (
    "bid_ask_ordering",
    "same_bar_ordering",
    "spread_at_trigger",
    "stop_freeze_levels",
    "minimum_stop_distance",
    "modify_retcode",
    "partial_close_ticket_identity",
    "residual_ticket_management",
    "commission",
    "swap",
    "slippage",
    "latency_assumption",
    "close_reason",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def slug(value: Any, *, max_len: int = 96) -> str:
    text = str(value if value is not None else "none").lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    text = text or "none"
    if len(text) <= max_len:
        return text
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]
    return f"{text[: max_len - 11]}_{digest}"


def stable_id(*parts: Any, prefix: str = "v3") -> str:
    payload = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def open_text(path: Path, mode: str = "rt"):
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8", errors="replace", newline="\n")
    return path.open(mode, encoding="utf-8", errors="replace", newline="\n")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with open_text(path, "rt") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict):
                yield row


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]], *, gzip_output: bool | None = None) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    use_gzip = path.suffix == ".gz" if gzip_output is None else gzip_output
    count = 0
    if use_gzip:
        with gzip.open(path, "wt", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                count += 1
    else:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                count += 1
    return count


def count_jsonl(path: Path) -> int:
    count = 0
    for _row in iter_jsonl(path):
        count += 1
    return count


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_existing_json(paths: list[Path]) -> dict[str, Any]:
    for path in paths:
        if path.exists():
            return read_json(path)
    return {}


def metric_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("variant_id") or ""),
        str(row.get("evidence_bucket") or ""),
        str(row.get("split_scope") or ""),
        str(row.get("split_key") or ""),
    )


def policy_family_from_id(variant_id: str, family: str | None = None) -> str:
    text = variant_id.lower()
    if text in SUPPORTED_RUNTIME_POLICIES or text.startswith("momentum_"):
        return "momentum_exhaustion" if "momentum" in text else text
    if "partial" in text:
        return "partial_be_runner"
    if "trailing" in text or "trail" in text:
        return "trailing_runner"
    if "time_stop" in text or text.startswith("time_"):
        return "time_stop"
    if "be_after" in text or "be_only" in text:
        return "be_after_trigger"
    if "fixed" in text or "j46" in text or "j49" in text:
        return "fixed_comparator"
    if "no_trade" in text:
        return "no_trade"
    if family:
        return family
    return "hybrid_or_source_route"


def policy_runtime_support(policy_family: str) -> str:
    if policy_family in SUPPORTED_RUNTIME_POLICIES:
        return "default_off_code_path_exists_current_runtime_not_activated_by_v3"
    if policy_family in {"fixed_comparator", "no_trade"}:
        return "comparator_or_decision_route_no_dynamic_lifecycle_required"
    return "default_off_research_route_requires_future_runtime_adapter"


def lifecycle_status_for_policy(policy_family: str) -> str:
    if policy_family in PARTIAL_DEPENDENT:
        return "requires_ticket_bound_partial_close_residual_ticket_be_modify_and_final_close"
    if policy_family in MODIFY_DEPENDENT:
        return "requires_ticket_bound_sl_modify_retcode_stop_freeze_spread_and_close_reason_capture"
    if policy_family == "time_stop":
        return "requires_entry_time_m15_bar_elapsed_and_market_close_execution_capture"
    if policy_family == "no_trade":
        return "no_trade_route_no_broker_lifecycle"
    if policy_family == "fixed_comparator":
        return "comparator_only_no_v3_live_lifecycle_claim"
    return "source_capture_or_future_adapter_required"


def broker_feasibility_status(policy_family: str) -> str:
    if policy_family in MODIFY_DEPENDENT:
        return "default_off_feasible_only_with_stop_freeze_modify_retcode_ticket_identity_capture"
    if policy_family == "time_stop":
        return "default_off_feasible_only_with_close_quote_deal_close_reason_capture"
    if policy_family == "no_trade":
        return "broker_not_entered"
    if policy_family == "fixed_comparator":
        return "comparator_only_no_broker_feasibility_claim"
    return "broker_feasibility_source_required"


def route_decision_from_dominance(decision: str | None, policy_family: str) -> str:
    text = str(decision or "").upper()
    if "NO_TRADE" in text:
        return "no_trade"
    if text.startswith("PROMOTE_DEFAULT_OFF"):
        return "trade_policy"
    if "REDUCE" in text:
        return "reduce_risk"
    if "CAPTURE" in text or "REPAIR" in text:
        return "capture_repair"
    if "KILL" in text:
        return "keep_comparator_only"
    if policy_family == "fixed_comparator":
        return "keep_comparator_only"
    if policy_family == "no_trade":
        return "no_trade"
    return "keep_comparator_only"


def result_scope_for_bucket(bucket: str) -> str:
    if bucket in {"full_selected_denominator", "m15_proxy"}:
        return "source_bound_proxy_r"
    if "strict_tick" in bucket:
        return "strict_tick_bid_ask_replay_r_not_broker_actual"
    if "friday_tick" in bucket:
        return "friday_tick_bid_ask_replay_r_not_broker_actual"
    if "broker_real" in bucket:
        return "broker_real_sparse_upstream_only_not_v3_owned"
    return "not_result_materialized"


def exact_proxy_fields(row: dict[str, Any]) -> dict[str, Any]:
    bucket = str(row.get("evidence_bucket") or "")
    scope = result_scope_for_bucket(bucket)
    exact_owned = False
    proxy_owned = scope in {"source_bound_proxy_r", "strict_tick_bid_ask_replay_r_not_broker_actual", "friday_tick_bid_ask_replay_r_not_broker_actual"}
    return {
        "result_scope": scope,
        "exact_r_owned_by_v3": exact_owned,
        "exact_r": None,
        "exact_r_status": "not_owned_by_execution_policy_v3_default_off_route",
        "proxy_r_owned_by_v3": proxy_owned,
        "proxy_r_sum": row.get("gross_total_r") if proxy_owned else None,
        "proxy_expectancy_r": row.get("expectancy_r") if proxy_owned else None,
        "net_proxy_expectancy_r": row.get("net_median_expectancy_r") if proxy_owned else None,
    }


def load_dominance(path: Path) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    return {metric_key(row): row for row in iter_jsonl(path)}


def summarize_lane16_path() -> dict[str, Any]:
    counters: dict[str, Counter] = {
        "path_class": Counter(),
        "best_policy": Counter(),
        "current_policy": Counter(),
        "origin": Counter(),
        "session": Counter(),
        "regime": Counter(),
        "source_gap_family": Counter(),
        "lane09b_class": Counter(),
        "lane10b_class": Counter(),
    }
    failure_counters: Counter[tuple[str, str, str, str, str]] = Counter()
    r_sums: defaultdict[tuple[str, str, str, str, str], float] = defaultdict(float)
    total = 0
    for row in iter_jsonl(LANE16_PATH):
        total += 1
        path_class = str(row.get("path_class") or "missing_path_class")
        best_policy = str(row.get("best_policy_id") or "missing_best_policy")
        current_policy = str(row.get("current_router_policy") or "missing_current_policy")
        origin = str(row.get("origin_family") or "missing_origin")
        session = str(row.get("session_bucket") or "missing_session")
        regime = str(row.get("regime_h4_state") or "missing_regime")
        lane09b_class = str(row.get("lane09b_reconciliation_class") or "missing_lane09b_class")
        lane10b_class = str(row.get("lane10b_classification") or "missing_lane10b_class")
        counters["path_class"][path_class] += 1
        counters["best_policy"][best_policy] += 1
        counters["current_policy"][current_policy] += 1
        counters["origin"][origin] += 1
        counters["session"][session] += 1
        counters["regime"][regime] += 1
        counters["lane09b_class"][lane09b_class] += 1
        counters["lane10b_class"][lane10b_class] += 1
        for gap in row.get("source_gap_families") or []:
            counters["source_gap_family"][str(gap)] += 1
        failure_types = failure_types_for_path_row(row)
        policies = {
            ("current_router_policy", current_policy),
            ("best_policy_id", best_policy),
        }
        split_pairs = [
            ("all", "ALL"),
            ("symbol", str(row.get("symbol") or "missing_symbol")),
            ("session_bucket", session),
            ("origin_family", origin),
            ("framework", str(row.get("framework") or "missing_framework")),
            ("regime_h4_state", regime),
            ("lane09b_reconciliation_class", lane09b_class),
            ("lane10b_classification", lane10b_class),
            ("spread_r_bucket", str(row.get("spread_r_bucket") or "missing_spread_r_bucket")),
        ]
        result_r = safe_float(row.get("result_r"))
        for gap in row.get("source_gap_families") or []:
            split_pairs.append(("source_gap_family", str(gap)))
        for policy_role, policy_id in policies:
            for failure_type in failure_types:
                for split_scope, split_key in split_pairs:
                    key = (policy_role, policy_id, failure_type, split_scope, split_key)
                    failure_counters[key] += 1
                    if result_r is not None:
                        r_sums[key] += result_r
    return {
        "total_rows": total,
        "counters": {name: dict(counter) for name, counter in counters.items()},
        "failure_rows": failure_counters,
        "failure_r_sums": r_sums,
    }


def failure_types_for_path_row(row: dict[str, Any]) -> set[str]:
    failures: set[str] = set()
    path_class = str(row.get("path_class") or "").lower()
    if row.get("sl_before_1r") is True or "loss" in path_class:
        failures.add("sl_first_or_stop_policy_exit")
    if row.get("partial_then_be") is True:
        failures.add("partial_then_be")
    if row.get("partial_then_final") is True:
        failures.add("partial_then_final")
    if row.get("stuck_no_resolution") is True or "stuck" in path_class:
        failures.add("stuck_no_resolution")
    if row.get("no_entry_touch") is True or "no_entry" in path_class:
        failures.add("no_entry_or_no_touch")
    if row.get("missed_opportunity") is True:
        failures.add("missed_opportunity")
    if row.get("repairable_scheduler_block") is True:
        failures.add("repairable_scheduler_block")
    if "late" in path_class:
        failures.add("late_entry_or_late_exit")
    gaps = {str(gap).lower() for gap in row.get("source_gap_families") or []}
    if any("spread" in gap or "cost" in gap for gap in gaps):
        failures.add("spread_cost_or_net_r_source_gap")
    if any("tick" in gap or "m1" in gap for gap in gaps):
        failures.add("adverse_or_incomplete_m1_tick_path")
    if any("broker" in gap or "lifecycle" in gap or "ticket" in gap for gap in gaps):
        failures.add("broker_lifecycle_source_gap")
    if str(row.get("lane09b_reconciliation_class") or "").lower() == "selector-false-positive":
        failures.add("selector_false_positive_policy_route")
    if not failures:
        failures.add("survived_or_non_failure_context")
    return failures


def safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def build_input_evidence_rows() -> list[dict[str, Any]]:
    route_inputs = [
        ("Lane01 source authority", LANE01_DIR, [LANE01_DIR / "COMPLETION_AUDIT.json", LANE01_DIR / "OUTPUT_MANIFEST.json"]),
        ("Lane02 no-leak/as-of contract", LANE02_DIR, [LANE02_DIR / "LANE02_COMPLETION_AUDIT.json", LANE02_DIR / "LANE02_OUTPUT_MANIFEST.json"]),
        ("Lane03 historical candidate reconstruction", LANE03_DIR, [LANE03_DIR / "LANE03_COMPLETION_AUDIT.json", LANE03_DIR / "LANE03_OUTPUT_MANIFEST.json"]),
        ("Lane04 historical microscope engine", LANE04_DIR, [LANE04_DIR / "LANE04_COMPLETION_AUDIT.json", LANE04_DIR / "LANE04_OUTPUT_MANIFEST.json"]),
        ("Lane05 feature store", LANE05_DIR, [LANE05_DIR / "LANE05_COMPLETION_AUDIT.json", LANE05_DIR / "LANE05_OUTPUT_MANIFEST.json"]),
        ("Lane06 label store", LANE06_DIR, [LANE06_DIR / "LANE06_COMPLETION_AUDIT.json", LANE06_DIR / "LANE06_OUTPUT_MANIFEST.json"]),
        ("Lane07 broker truth/cost calibration", LANE07_DIR, [LANE07_DIR / "LANE07_COMPLETION_AUDIT.json", LANE07_DIR / "LANE07_OUTPUT_MANIFEST.json"]),
        ("Lane08 digital twin replay", LANE08_DIR, [LANE08_DIR / "LANE08_COMPLETION_AUDIT.json", LANE08_DIR / "LANE08_OUTPUT_MANIFEST.json"]),
        ("Lane09B selector-scheduler reconciliation", LANE09B_DIR, [LANE09B_DIR / "LANE09B_COMPLETION_AUDIT.json", LANE09B_DIR / "LANE09B_OUTPUT_MANIFEST.json"]),
        ("Lane10B scheduler conflict anatomy", LANE10B_DIR, [LANE10B_DIR / "LANE10B_COMPLETION_AUDIT.json", LANE10B_DIR / "LANE10B_OUTPUT_MANIFEST.json"]),
        ("Lane11 execution policy engine V2", LANE11_DIR, [LANE11_DIR / "LANE11_COMPLETION_AUDIT.json", LANE11_DIR / "LANE11_OUTPUT_MANIFEST.json"]),
        ("Lane16 historical microscope scale", LANE16_DIR, [LANE16_DIR / "LANE16_COMPLETION_AUDIT.json", LANE16_DIR / "LANE16_OUTPUT_MANIFEST.json"]),
        ("Lane17 market awareness whiteboard", LANE17_DIR, [LANE17_DIR / "LANE17_COMPLETION_AUDIT.json", LANE17_DIR / "LANE17_OUTPUT_MANIFEST.json"]),
        ("Lane18 broker truth/cost capture V2", LANE18_DIR, [LANE18_DIR / "LANE18_COMPLETION_AUDIT.json", LANE18_DIR / "LANE18_OUTPUT_MANIFEST.json"]),
        ("Post-Lane18 source capture repair", POST_LANE18_DIR, [POST_LANE18_DIR / "POST_LANE18_COMPLETION_AUDIT.json", POST_LANE18_DIR / "POST_LANE18_OUTPUT_MANIFEST.json"]),
        ("Master post-Lane18 implementation decision", MASTER_DIR, [MASTER_DIR / "ABSOLUTE_MASTER_POST_LANE18_IMPLEMENTATION_WAVE_DECISION.json", MASTER_DIR / "ABSOLUTE_MASTER_COMPLETION_AUDIT.json"]),
    ]
    rows: list[dict[str, Any]] = []
    for title, route_dir, evidence_paths in route_inputs:
        payloads = [read_json(path) for path in evidence_paths if path.exists()]
        merged_counts: dict[str, Any] = {}
        statuses: list[Any] = []
        runtime_boundaries: list[Any] = []
        result_states: list[Any] = []
        for payload in payloads:
            for key in ("counts", "row_counts", "summary"):
                if isinstance(payload.get(key), dict):
                    merged_counts[key] = payload[key]
            if payload.get("status") is not None:
                statuses.append(payload.get("status"))
            if payload.get("runtime_effect_boundary") is not None:
                runtime_boundaries.append(payload.get("runtime_effect_boundary"))
            if payload.get("result_use_status") is not None:
                result_states.append(payload.get("result_use_status"))
        rows.append({
            "schema_version": "v3_input_evidence_inspection_v1",
            "route_id": ROUTE_ID,
            "input_title": title,
            "input_route_path": rel(route_dir),
            "evidence_paths": [rel(path) for path in evidence_paths if path.exists()],
            "present": route_dir.exists(),
            "status_values": statuses,
            "runtime_effect_boundaries": runtime_boundaries,
            "result_use_statuses": result_states,
            "count_summary": merged_counts,
            "consumption_decision": "consumed_as_terminal_current_disk_input",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    return rows


def build_code_surface_rows() -> list[dict[str, Any]]:
    code_paths = [
        ROOT / "src" / "research" / "dynamic_execution_policy.py",
        ROOT / "src" / "components" / "execution.py",
        ROOT / "src" / "components" / "broker_truth_cost_capture_v2.py",
        ROOT / "src" / "components" / "pending_limit_lifecycle_logger.py",
        ROOT / "src" / "components" / "partial_close_shadow_logger.py",
        ROOT / "src" / "components" / "be_shadow_logger.py",
        ROOT / "src" / "components" / "trailing_stop_shadow_logger.py",
        ROOT / "src" / "components" / "slippage_shadow_logger.py",
        ROOT / "src" / "research_infra" / "broker_actual_r_audit.py",
        ROOT / "src" / "research_infra" / "execution_telemetry_verifier.py",
        ROOT / "scripts" / "build_vnext_live_activation_checkpoint.py",
        ROOT / "tests" / "test_dynamic_execution_policy.py",
        ROOT / "tests" / "test_execution.py",
        ROOT / "tests" / "test_broker_truth_cost_capture_v2.py",
    ]
    patterns = [
        "momentum_exhaustion",
        "partial_be_runner",
        "trailing_runner",
        "time_stop",
        "be_after_trigger",
        "partial_close",
        "retcode",
        "trade_freeze_level",
        "trade_stops_level",
        "broker_real_or_proxy_state",
        "ticket_identity_status",
        "history_deals_get",
        "record_pending_limit_lifecycle",
        "close_reason",
        "commission",
        "swap",
        "slippage",
    ]
    rows: list[dict[str, Any]] = []
    for path in code_paths:
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        functions = re.findall(r"^\s*def\s+([A-Za-z0-9_]+)\s*\(", text, flags=re.MULTILINE)
        classes = re.findall(r"^\s*class\s+([A-Za-z0-9_]+)\s*[:(]", text, flags=re.MULTILINE)
        rows.append({
            "schema_version": "v3_code_surface_audit_v1",
            "route_id": ROUTE_ID,
            "source_path": rel(path),
            "present": path.exists(),
            "line_count": len(text.splitlines()),
            "functions": functions,
            "classes": classes,
            "pattern_hits": {pattern: text.count(pattern) for pattern in patterns},
            "execution_policy_v3_relevance": relevance_for_code_path(path),
            "source_operation": "read_only_code_inspection",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    return rows


def relevance_for_code_path(path: Path) -> list[str]:
    name = path.as_posix()
    relevance: list[str] = []
    if "dynamic_execution_policy" in name:
        relevance.append("pure_research_policy_state_machine")
    if name.endswith("execution.py"):
        relevance.append("current_live_execution_lifecycle_code_read_only")
    if "broker_truth_cost_capture_v2" in name:
        relevance.append("default_off_broker_lifecycle_cost_capture_contract")
    if "pending_limit_lifecycle" in name:
        relevance.append("pending_limit_lifecycle_identity_contract")
    if "partial_close" in name or "be_shadow" in name or "trailing_stop" in name:
        relevance.append("shadow_execution_policy_observation")
    if "broker_actual_r" in name:
        relevance.append("broker_actual_r_proxy_separation_guard")
    if "live_activation_checkpoint" in name:
        relevance.append("read_only_live_lifecycle_diagnostic_context")
    if "test_" in path.name:
        relevance.append("focused_regression_evidence")
    return relevance


def build_policy_registry(lane16_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    inherited_ids: set[str] = set()
    for source in iter_jsonl(LANE11_EXPANDED_REGISTRY):
        vid = str(source.get("variant_id"))
        inherited_ids.add(vid)
        policy_family = policy_family_from_id(vid, str(source.get("family") or ""))
        row = {
            "schema_version": "v3_policy_variant_registry_v1",
            "route_id": ROUTE_ID,
            "variant_id": vid,
            "source_variant_id": vid,
            "inherited_from_lane11": True,
            "family": source.get("family"),
            "policy_family": policy_family,
            "parameters": source.get("parameters") or {},
            "is_baseline_comparator": bool(source.get("is_baseline_comparator")),
            "baseline_equivalent_policy": source.get("baseline_equivalent_policy"),
            "feasibility_status": source.get("feasibility_status"),
            "current_evidence_support": source.get("current_evidence_support"),
            "required_source_to_replay": source.get("required_source_to_replay"),
            "source_gap_reason": source.get("source_gap_reason"),
            "v3_join_sources": ["Lane11 expanded registry"],
            "runtime_support_status": policy_runtime_support(policy_family),
            "broker_feasibility_status": broker_feasibility_status(policy_family),
            "lifecycle_status": lifecycle_status_for_policy(policy_family),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        }
        rows.append(row)

    def add_variant(
        *,
        variant_id: str,
        family: str,
        policy_family: str,
        parameters: dict[str, Any],
        evidence_support: str,
        required_source_to_replay: str | None,
        source_gap_reason: str | None,
        join_sources: list[str],
        feasibility_status: str,
    ) -> None:
        if variant_id in inherited_ids:
            return
        inherited_ids.add(variant_id)
        rows.append({
            "schema_version": "v3_policy_variant_registry_v1",
            "route_id": ROUTE_ID,
            "variant_id": variant_id,
            "source_variant_id": None,
            "inherited_from_lane11": False,
            "family": family,
            "policy_family": policy_family,
            "parameters": parameters,
            "is_baseline_comparator": policy_family in {"fixed_comparator", "no_trade"},
            "baseline_equivalent_policy": None,
            "feasibility_status": feasibility_status,
            "current_evidence_support": evidence_support,
            "required_source_to_replay": required_source_to_replay,
            "source_gap_reason": source_gap_reason,
            "v3_join_sources": join_sources,
            "runtime_support_status": policy_runtime_support(policy_family),
            "broker_feasibility_status": broker_feasibility_status(policy_family),
            "lifecycle_status": lifecycle_status_for_policy(policy_family),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })

    path_classes = sorted(lane16_summary["counters"]["path_class"])
    best_policies = sorted(lane16_summary["counters"]["best_policy"])
    for path_class in path_classes:
        for best_policy in best_policies:
            policy_family = policy_family_from_id(best_policy)
            add_variant(
                variant_id=f"v3_path_{slug(path_class, max_len=48)}__policy_{slug(best_policy, max_len=48)}",
                family="v3_path_anatomy_policy_router",
                policy_family=policy_family,
                parameters={
                    "path_class": path_class,
                    "candidate_policy": best_policy,
                    "routing_rule": "use Lane16 path anatomy to route or reject only after source/broker checks",
                },
                evidence_support="Lane16 full path anatomy ledger summarized without row cutoff",
                required_source_to_replay=None if policy_family in SUPPORTED_RUNTIME_POLICIES | {"no_trade", "fixed_comparator"} else "future_runtime_adapter_for_policy_family",
                source_gap_reason=None if policy_family in SUPPORTED_RUNTIME_POLICIES | {"no_trade", "fixed_comparator"} else "path_best_policy_not_supported_by_current_runtime_code",
                join_sources=["Lane16 path anatomy", "Lane11 policy simulation"],
                feasibility_status="v3_route_feasible_default_off_from_lane16_summary",
            )

    lane17_required_fields = [
        "tick_state",
        "m1_path_state",
        "spread_to_risk_state",
        "broker_feasibility_fields",
        "market_hours_state",
        "correlation_cluster_state",
        "regime_state",
    ]
    for policy in sorted(SUPPORTED_RUNTIME_POLICIES | {"no_trade_baseline"}):
        policy_family = policy_family_from_id(policy)
        for field in lane17_required_fields:
            add_variant(
                variant_id=f"v3_market_guard_{slug(policy)}__{slug(field)}",
                family="v3_market_state_guarded_policy",
                policy_family=policy_family,
                parameters={
                    "base_policy": policy,
                    "market_state_field": field,
                    "route_when_field_missing": "source_required_or_no_trade_fail_closed",
                    "route_when_field_decision_available": "allow_default_off_policy_evaluation",
                },
                evidence_support="Lane17 Execution V3 downstream contract and whiteboard source-state labels",
                required_source_to_replay=field,
                source_gap_reason=f"Lane17 requires {field} for Execution V3 route realism",
                join_sources=["Lane17 market awareness whiteboard", "Lane11 policy simulation"],
                feasibility_status="v3_default_off_route_guard_feasible_source_state_required",
            )

    for policy in sorted(SUPPORTED_RUNTIME_POLICIES | {"fixed_1_5r", "no_trade_baseline"}):
        policy_family = policy_family_from_id(policy)
        for field in BROKER_FIELD_FAMILIES:
            add_variant(
                variant_id=f"v3_broker_lifecycle_guard_{slug(policy)}__{slug(field)}",
                family="v3_broker_tick_lifecycle_feasibility_guard",
                policy_family=policy_family,
                parameters={
                    "base_policy": policy,
                    "broker_lifecycle_field": field,
                    "guard_action": "source_required_before_live_claim",
                },
                evidence_support="Lane18 broker truth/cost contract plus current execution code audit",
                required_source_to_replay=field,
                source_gap_reason=f"broker/tick/lifecycle feasibility requires {field}",
                join_sources=["Lane18 broker truth cost capture", "post-Lane18 source repair", "execution.py code audit"],
                feasibility_status="v3_guard_feasible_default_off_nonreplayable_until_source_complete",
            )

    for decision in iter_jsonl(POST_SOURCE_DECISIONS):
        field_family = str(decision.get("field_family") or "missing_field_family")
        disposition = str(decision.get("disposition") or decision.get("decision") or "missing_disposition")
        add_variant(
            variant_id=f"v3_source_capture_{slug(field_family, max_len=64)}__{slug(disposition, max_len=32)}",
            family="v3_source_capture_policy_route",
            policy_family="source_capture_route",
            parameters={
                "field_family": field_family,
                "disposition": disposition,
                "affected_field_rows": decision.get("affected_field_rows"),
                "route_action": "capture_repair_or_keep_source_required_before_policy_authority",
            },
            evidence_support="post-Lane18 source completeness decision ledger",
            required_source_to_replay=field_family,
            source_gap_reason=f"{field_family}:{disposition}",
            join_sources=["post-Lane18 source capture repair"],
            feasibility_status="source_capture_route_not_policy_replay",
        )
    return rows


def build_evaluation_rows(registry_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    expanded_dom = load_dominance(LANE11_EXPANDED_DOMINANCE)
    baseline_dom = load_dominance(LANE11_BASELINE_DOMINANCE)
    rows: list[dict[str, Any]] = []
    for metric_path, dominance, policy_scope in [
        (LANE11_BASELINE_METRICS, baseline_dom, "lane11_baseline_policy"),
        (LANE11_EXPANDED_METRICS, expanded_dom, "lane11_expanded_policy"),
    ]:
        for metric in iter_jsonl(metric_path):
            vid = str(metric.get("variant_id") or "")
            reg = registry_by_id.get(vid, {})
            policy_family = policy_family_from_id(vid, str(reg.get("family") or metric.get("policy_scope") or ""))
            dom = dominance.get(metric_key(metric), {})
            route_decision = route_decision_from_dominance(dom.get("decision"), policy_family)
            row = {
                "schema_version": "v3_feasible_policy_evaluation_v1",
                "route_id": ROUTE_ID,
                "variant_id": vid,
                "policy_scope": policy_scope,
                "family": reg.get("family") or metric.get("policy_scope"),
                "policy_family": policy_family,
                "evidence_bucket": metric.get("evidence_bucket"),
                "split_scope": metric.get("split_scope"),
                "split_key": metric.get("split_key"),
                "denominator": metric.get("denominator"),
                "rows": metric.get("rows"),
                "known_r_rows": metric.get("known_r_rows"),
                "missing_r_rows": metric.get("missing_r_rows"),
                "wins": metric.get("wins"),
                "losses": metric.get("losses"),
                "breakevens": metric.get("breakevens"),
                "gross_total_r": metric.get("gross_total_r"),
                "gross_profit_r": metric.get("gross_profit_r"),
                "gross_loss_r": metric.get("gross_loss_r"),
                "expectancy_r": metric.get("expectancy_r"),
                "net_median_total_r": metric.get("net_median_total_r"),
                "net_median_expectancy_r": metric.get("net_median_expectancy_r"),
                "net_p90_expectancy_r": metric.get("net_p90_expectancy_r"),
                "net_high_stress_expectancy_r": metric.get("net_high_stress_expectancy_r"),
                "profit_factor": metric.get("profit_factor"),
                "win_rate": metric.get("win_rate"),
                "max_drawdown_r": metric.get("max_drawdown_r"),
                "max_loss_streak": metric.get("max_loss_streak"),
                "dominance_decision": dom.get("decision"),
                "best_variant_for_group": dom.get("best_variant_for_group"),
                "policy_routing_decision": route_decision,
                "broker_feasibility_status": broker_feasibility_status(policy_family),
                "lifecycle_feasibility_status": lifecycle_status_for_policy(policy_family),
                "source_completeness_decision": "use_lane11_metric_with_lane16_lane17_lane18_and_post_lane18_source_gates",
                "result_use_status": RESULT_USE_STATUS,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }
            row.update(exact_proxy_fields(metric))
            rows.append(row)

    for reg in registry_by_id.values():
        if reg.get("inherited_from_lane11"):
            continue
        policy_family = str(reg.get("policy_family") or "source_capture_route")
        route_decision = "capture_repair" if "source" in policy_family or "guard" in str(reg.get("family") or "") else "source_required"
        if policy_family == "no_trade":
            route_decision = "no_trade"
        rows.append({
            "schema_version": "v3_feasible_policy_evaluation_v1",
            "route_id": ROUTE_ID,
            "variant_id": reg["variant_id"],
            "policy_scope": "v3_source_or_guard_route",
            "family": reg.get("family"),
            "policy_family": policy_family,
            "evidence_bucket": "v3_source_contract",
            "split_scope": "source_or_guard_family",
            "split_key": reg.get("family"),
            "denominator": "not_result_scored_guard_route",
            "rows": 0,
            "known_r_rows": 0,
            "missing_r_rows": reg.get("parameters", {}).get("affected_field_rows"),
            "wins": None,
            "losses": None,
            "breakevens": None,
            "gross_total_r": None,
            "gross_profit_r": None,
            "gross_loss_r": None,
            "expectancy_r": None,
            "net_median_total_r": None,
            "net_median_expectancy_r": None,
            "net_p90_expectancy_r": None,
            "net_high_stress_expectancy_r": None,
            "profit_factor": None,
            "win_rate": None,
            "max_drawdown_r": None,
            "max_loss_streak": None,
            "dominance_decision": "NOT_RESULT_SCORED_SOURCE_GUARD",
            "best_variant_for_group": None,
            "policy_routing_decision": route_decision,
            "broker_feasibility_status": reg.get("broker_feasibility_status"),
            "lifecycle_feasibility_status": reg.get("lifecycle_status"),
            "source_completeness_decision": reg.get("source_gap_reason"),
            "result_scope": "not_result_materialized",
            "exact_r_owned_by_v3": False,
            "exact_r": None,
            "exact_r_status": "not_owned_source_guard_route",
            "proxy_r_owned_by_v3": False,
            "proxy_r_sum": None,
            "proxy_expectancy_r": None,
            "net_proxy_expectancy_r": None,
            "result_use_status": RESULT_USE_STATUS,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    return rows


def build_source_gap_rows(lane16_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in iter_jsonl(LANE11_EXPANDED_SOURCE_GAPS):
        row = dict(source)
        row.update({
            "schema_version": "v3_non_replayable_source_gap_v1",
            "route_id": ROUTE_ID,
            "upstream_route_id": source.get("route_id"),
            "gap_source": "Lane11 expanded policy source gap",
            "v3_decision": "source_required_before_policy_authority",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
        rows.append(row)
    for source in iter_jsonl(LANE18_GAPS):
        rows.append({
            "schema_version": "v3_non_replayable_source_gap_v1",
            "route_id": ROUTE_ID,
            "upstream_route_id": source.get("route_id"),
            "gap_source": "Lane18 broker truth/cost source gap",
            "variant_id": f"v3_broker_gap_{slug(source.get('field'), max_len=64)}",
            "family": source.get("lifecycle_surface"),
            "source_gap_reason": source.get("field"),
            "recovery_requirement": source.get("required_action"),
            "recoverability": source.get("recoverability"),
            "affected_symbols": [source.get("symbol")] if source.get("symbol") else [],
            "raw_evidence_pointer": {"source_refs": source.get("source_refs"), "source_gap_id": source.get("source_gap_id")},
            "v3_decision": "read_only_export_or_forward_capture_required",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    for source in iter_jsonl(POST_SOURCE_DECISIONS):
        rows.append({
            "schema_version": "v3_non_replayable_source_gap_v1",
            "route_id": ROUTE_ID,
            "upstream_route_id": source.get("route_id"),
            "gap_source": "Post-Lane18 source completeness decision",
            "variant_id": f"v3_source_capture_{slug(source.get('field_family'), max_len=64)}",
            "family": "post_lane18_source_completion",
            "source_gap_reason": source.get("field_family"),
            "recovery_requirement": source.get("decision"),
            "recoverability": source.get("disposition"),
            "affected_row_count": source.get("affected_field_rows"),
            "raw_evidence_pointer": {"path": rel(POST_SOURCE_DECISIONS)},
            "v3_decision": source.get("disposition"),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    for field_family, count in sorted(lane16_summary["counters"]["source_gap_family"].items()):
        rows.append({
            "schema_version": "v3_non_replayable_source_gap_v1",
            "route_id": ROUTE_ID,
            "upstream_route_id": "vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01",
            "gap_source": "Lane16 path anatomy source_gap_families aggregate",
            "variant_id": f"v3_lane16_gap_{slug(field_family, max_len=64)}",
            "family": "lane16_path_source_gap_family",
            "source_gap_reason": field_family,
            "recovery_requirement": "consume post-Lane18 source repair disposition and keep exact field family fail-closed until captured or proxy-bound",
            "affected_row_count": count,
            "raw_evidence_pointer": {"path": rel(LANE16_PATH)},
            "v3_decision": "source_required_or_proxy_labeled_only",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    lane17_audit = read_json(LANE17_DIR / "LANE17_COMPLETION_AUDIT.json")
    for field, count in sorted((lane17_audit.get("counts", {}).get("source_gap_counts") or {}).items()):
        rows.append({
            "schema_version": "v3_non_replayable_source_gap_v1",
            "route_id": ROUTE_ID,
            "upstream_route_id": "vnext_absolute_moonshot_lane17_market_awareness_whiteboard_2026_06_01",
            "gap_source": "Lane17 market awareness source gap aggregate",
            "variant_id": f"v3_lane17_gap_{slug(field, max_len=64)}",
            "family": "lane17_market_state_source_gap",
            "source_gap_reason": field,
            "recovery_requirement": "field must be source-labeled decision-available/proxy/missing before policy route consumes it",
            "affected_row_count": count,
            "raw_evidence_pointer": {"path": rel(LANE17_GAPS)},
            "v3_decision": "source_required_for_market_state_policy_routing",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    return rows


def build_lifecycle_feasibility_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    policy_families = sorted(SUPPORTED_RUNTIME_POLICIES | {"fixed_comparator", "no_trade", "source_capture_route"})
    for policy_family in policy_families:
        for field in BROKER_FIELD_FAMILIES:
            required = field_required_for_policy(policy_family, field)
            source_state = source_state_for_broker_field(field)
            decision = "not_required" if not required else "feasible_default_off_with_source_guard"
            if required and source_state in {"read_only_export_required", "forward_capture_required", "non_generatable_historical_truth"}:
                decision = "source_required_or_lifecycle_unsupported_until_capture"
            rows.append({
                "schema_version": "v3_lifecycle_broker_tick_feasibility_v1",
                "route_id": ROUTE_ID,
                "policy_family": policy_family,
                "field": field,
                "required_by_policy": required,
                "source_state": source_state,
                "feasibility_decision": decision,
                "code_surface": code_surface_for_broker_field(field),
                "source_refs": [
                    rel(LANE18_DIR / "LANE18_DOWNSTREAM_CONTRACTS.json"),
                    rel(POST_LANE18_DIR / "POST_LANE18_FIELD_FAMILY_SUMMARY.json"),
                    rel(ROOT / "src" / "components" / "execution.py"),
                    rel(ROOT / "src" / "components" / "broker_truth_cost_capture_v2.py"),
                ],
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            })
    return rows


def field_required_for_policy(policy_family: str, field: str) -> bool:
    if policy_family in {"no_trade", "source_capture_route"}:
        return False
    if policy_family == "fixed_comparator":
        return field in {"bid_ask_ordering", "same_bar_ordering", "spread_at_trigger", "commission", "swap", "slippage", "close_reason"}
    if policy_family == "time_stop":
        return field in {"bid_ask_ordering", "spread_at_trigger", "commission", "swap", "slippage", "latency_assumption", "close_reason"}
    if policy_family == "partial_be_runner":
        return True
    if policy_family in {"be_after_trigger", "trailing_runner", "momentum_exhaustion"}:
        return field not in {"partial_close_ticket_identity", "residual_ticket_management"}
    return True


def source_state_for_broker_field(field: str) -> str:
    field_summary = read_json(POST_LANE18_DIR / "POST_LANE18_FIELD_FAMILY_SUMMARY.json")
    counts = field_summary.get("source_stats", {}).get("field_disposition_counts", {})
    matches = {key: value for key, value in counts.items() if field in key.lower()}
    if not matches:
        if field in {"bid_ask_ordering", "same_bar_ordering"}:
            return "proxy_bound_now_with_ordered_tick_gap_rows"
        return "forward_capture_required"
    dispositions = Counter()
    for key, value in matches.items():
        disposition = key.split("|")[-1]
        dispositions[disposition] += int(value)
    if dispositions.get("read_only_export_required"):
        return "read_only_export_required"
    if dispositions.get("forward_capture_required"):
        return "forward_capture_required"
    if dispositions.get("proxy_bound_now"):
        return "proxy_bound_now"
    if dispositions.get("filled_now"):
        return "filled_now"
    return dispositions.most_common(1)[0][0]


def code_surface_for_broker_field(field: str) -> list[str]:
    mapping = {
        "bid_ask_ordering": ["src/research/dynamic_execution_policy.py", "src/components/execution.py"],
        "same_bar_ordering": ["src/research/dynamic_execution_policy.py"],
        "spread_at_trigger": ["src/components/broker_truth_cost_capture_v2.py", "src/components/pending_limit_lifecycle_logger.py"],
        "stop_freeze_levels": ["src/components/broker_truth_cost_capture_v2.py", "src/components/execution.py"],
        "minimum_stop_distance": ["src/components/execution.py"],
        "modify_retcode": ["src/components/execution.py", "src/components/broker_truth_cost_capture_v2.py"],
        "partial_close_ticket_identity": ["src/components/execution.py"],
        "residual_ticket_management": ["src/components/execution.py"],
        "commission": ["src/research_infra/broker_actual_r_audit.py", "src/components/broker_truth_cost_capture_v2.py"],
        "swap": ["src/research_infra/broker_actual_r_audit.py", "src/components/broker_truth_cost_capture_v2.py"],
        "slippage": ["src/components/slippage_shadow_logger.py", "src/components/execution.py"],
        "latency_assumption": ["src/components/execution.py"],
        "close_reason": ["src/components/execution.py", "src/research_infra/broker_actual_r_audit.py"],
    }
    return mapping.get(field, [])


def build_failure_anatomy_rows(lane16_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, count in sorted(lane16_summary["failure_rows"].items()):
        policy_role, policy_id, failure_type, split_scope, split_key = key
        rows.append({
            "schema_version": "v3_policy_failure_anatomy_v1",
            "route_id": ROUTE_ID,
            "policy_role": policy_role,
            "policy_id": policy_id,
            "policy_family": policy_family_from_id(policy_id),
            "failure_type": failure_type,
            "split_scope": split_scope,
            "split_key": split_key,
            "rows": count,
            "result_r_sum": round(lane16_summary["failure_r_sums"].get(key, 0.0), 9),
            "source_refs": [rel(LANE16_PATH)],
            "policy_route_decision": failure_route_decision(failure_type),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    modify_gap_count = sum(1 for row in iter_jsonl(LANE18_GAPS) if "retcode" in str(row.get("field") or "").lower())
    rows.append({
        "schema_version": "v3_policy_failure_anatomy_v1",
        "route_id": ROUTE_ID,
        "policy_role": "broker_lifecycle_code_surface",
        "policy_id": "modify_dependent_policies",
        "policy_family": "be_partial_trailing_momentum_modify_dependent",
        "failure_type": "modify_failure_or_retcode_source_gap",
        "split_scope": "broker_field",
        "split_key": "modify_retcode",
        "rows": modify_gap_count,
        "result_r_sum": None,
        "source_refs": [rel(LANE18_GAPS), rel(ROOT / "src" / "components" / "execution.py")],
        "policy_route_decision": "capture_repair",
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
    })
    return rows


def failure_route_decision(failure_type: str) -> str:
    if "source_gap" in failure_type or "cost" in failure_type or "broker" in failure_type:
        return "source_required"
    if "selector_false_positive" in failure_type or "sl_first" in failure_type:
        return "no_trade_or_reduce_risk"
    if "missed" in failure_type or "partial_then_final" in failure_type:
        return "trade_policy_candidate"
    return "keep_comparator_or_context"


def build_routing_rows(registry_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, source_type in [
        (LANE11_BASELINE_PACKAGE, "Lane11 baseline package"),
        (LANE11_EXPANDED_PACKAGE, "Lane11 expanded package"),
    ]:
        for source in iter_jsonl(path):
            vid = str(source.get("variant_id") or "")
            policy_family = policy_family_from_id(vid, str((registry_by_id.get(vid) or {}).get("family") or ""))
            rows.append({
                "schema_version": "v3_policy_routing_decision_v1",
                "route_id": ROUTE_ID,
                "source_package": source_type,
                "variant_id": vid,
                "policy_family": policy_family,
                "split_scope": source.get("split_scope"),
                "split_key": source.get("split_key"),
                "evidence_bucket": source.get("evidence_bucket"),
                "decision": source.get("decision"),
                "policy_routing_decision": route_decision_from_dominance(source.get("decision"), policy_family),
                "rule_action": source.get("rule_action"),
                "minimum_evidence_rows_observed": source.get("minimum_evidence_rows_observed"),
                "net_median_expectancy_r": source.get("net_median_expectancy_r"),
                "profit_factor": source.get("profit_factor"),
                "owner_approval_required_for_live_use": True,
                "runtime_effect_now": False,
                "package_status": "default_off_v3_not_live_activation",
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            })
    for reg in registry_by_id.values():
        if reg.get("inherited_from_lane11"):
            continue
        policy_family = str(reg.get("policy_family") or "source_capture_route")
        rows.append({
            "schema_version": "v3_policy_routing_decision_v1",
            "route_id": ROUTE_ID,
            "source_package": "V3 default-off source/guard route",
            "variant_id": reg["variant_id"],
            "policy_family": policy_family,
            "split_scope": "source_or_guard_family",
            "split_key": reg.get("family"),
            "evidence_bucket": "v3_source_contract",
            "decision": "SOURCE_GUARD_OR_CAPTURE_ROUTE",
            "policy_routing_decision": "capture_repair" if "source" in policy_family or "source" in str(reg.get("family")) else "source_required",
            "rule_action": "do_not_live_route_until_source_and_production_dossier_approve",
            "minimum_evidence_rows_observed": reg.get("parameters", {}).get("affected_field_rows"),
            "net_median_expectancy_r": None,
            "profit_factor": None,
            "owner_approval_required_for_live_use": True,
            "runtime_effect_now": False,
            "package_status": "default_off_v3_not_live_activation",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    return rows


def build_source_decision_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in iter_jsonl(POST_SOURCE_DECISIONS):
        rows.append({
            "schema_version": "v3_source_capture_and_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source": "post_lane18_source_completeness",
            "field_family": source.get("field_family"),
            "decision": source.get("decision"),
            "disposition": source.get("disposition"),
            "affected_rows": source.get("affected_field_rows"),
            "execution_policy_v3_decision": execution_policy_source_decision(str(source.get("disposition") or "")),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    for source in iter_jsonl(LANE18_PROSPECTIVE):
        rows.append({
            "schema_version": "v3_source_capture_and_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "source": "lane18_prospective_capture_requirement",
            "field_family": source.get("field") or source.get("requirement_id") or source.get("source_surface"),
            "decision": "forward_capture_required",
            "disposition": "forward_capture_required",
            "affected_rows": None,
            "required_action": source.get("required_action") or source.get("proof_required"),
            "execution_policy_v3_decision": "capture_repair",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
    return rows


def execution_policy_source_decision(disposition: str) -> str:
    if disposition in {"filled_now", "reconstructed_now", "proxy_bound_now"}:
        return "may_consume_with_source_label"
    if disposition in {"read_only_export_required", "forward_capture_required"}:
        return "capture_repair"
    if disposition == "non_generatable_historical_truth":
        return "prospective_capture_only_no_historical_inference"
    return "source_required"


def build_branch_decision_rows() -> list[dict[str, Any]]:
    decisions = [
        ("lane11_expanded_registry", "implement_default_off_v3_as_successor_registry", "Lane11 890 variants retained and extended, not replaced by baseline-only closure"),
        ("current_production_policy", "keep_live_unchanged_default_off_only", "momentum_exhaustion primary with partial_be_runner exception remains current live truth until separate production-change dossier"),
        ("fixed_1_5r_j46_j49", "keep_comparator_only", "static fixed and J46/J49 surfaces stay historical/comparator unless future dossier approves"),
        ("trailing_runner", "source_required_before_route_authority", "attractive proxy rows remain blocked by tick/order/modify retcode realism where not captured"),
        ("time_stop", "routeable_default_off_with_close_lifecycle_capture_required", "time-stop requires entry time, bar elapsed, quote/deal close reason capture"),
        ("partial_be_runner", "routeable_default_off_with_ticket_bound_lifecycle_required", "partial close requires ticket/residual/BE modify and final close identity"),
        ("source_capture_routes", "send_to_repair_companion_and_downstream_contracts", "post-Lane18 source repair decisions are preserved as capture routes, not hidden blockers"),
    ]
    return [
        {
            "schema_version": "v3_branch_decision_v1",
            "route_id": ROUTE_ID,
            "branch": branch,
            "decision": decision,
            "rationale": rationale,
            "runtime_effect_now": False,
            "owner_approval_required_for_live_use": True,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        }
        for branch, decision, rationale in decisions
    ]


def build_implementation_decision_rows() -> list[dict[str, Any]]:
    decisions = [
        ("default_off_package_json", "implemented", rel(OUTPUTS["routing_package"]), "future runtime adapter can consume package after owner-approved production-change lane"),
        ("full_policy_registry", "implemented", rel(OUTPUTS["policy_registry"]), "all Lane11 variants plus V3 source/path/market/broker guard variants preserved"),
        ("feasible_policy_evaluation", "implemented", rel(OUTPUTS["evaluation"]), "baseline and expanded Lane11 metrics materialized with V3 route/source/lifecycle decisions"),
        ("execution_runtime_code_change", "not_changed", "src/components/execution.py", "read-only inspection only; no live behavior change in this route"),
        ("source_capture_repair_consumption", "implemented", rel(OUTPUTS["source_decisions"]), "post-Lane18 source completeness consumed into V3 decisions"),
        ("production_activation", "forbidden_not_implemented", None, "requires separate owner approval and production-change dossier"),
    ]
    return [
        {
            "schema_version": "v3_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "implementation_surface": surface,
            "decision": decision,
            "artifact": artifact,
            "rationale": rationale,
            "runtime_effect_now": False,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        }
        for surface, decision, artifact, rationale in decisions
    ]


def build_split_stress_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in iter_jsonl(LANE16_SPLIT):
        row = {
            "schema_version": "v3_split_stress_deconcentration_v1",
            "route_id": ROUTE_ID,
            "source": "Lane16 split stress summary",
            "summary_family": source.get("summary_family"),
            "split_scope": source.get("split_scope"),
            "split_key": source.get("split_key"),
            "rows": source.get("rows"),
            "known_r_rows": source.get("known_r_rows"),
            "gross_r_sum": source.get("gross_r_sum"),
            "expectancy_r": source.get("expectancy_r"),
            "current_policy_cost_adjusted_median_expectancy_r": source.get("current_policy_cost_adjusted_median_expectancy_r"),
            "current_policy_cost_adjusted_high_stress_expectancy_r": source.get("current_policy_cost_adjusted_high_stress_expectancy_r"),
            "cost_stress_expectancy_delta_r": source.get("cost_stress_expectancy_delta_r"),
            "scheduler_accepted_rows": source.get("scheduler_accepted_rows"),
            "scheduler_blocked_or_reduced_rows": source.get("scheduler_blocked_or_reduced_rows"),
            "repairable_scheduler_block_rows": source.get("repairable_scheduler_block_rows"),
            "source_gap_rows": source.get("source_gap_rows"),
            "strict_tick_rows": source.get("strict_tick_rows"),
            "deconcentration_decision": split_decision(source),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        }
        rows.append(row)
    return rows


def split_decision(row: dict[str, Any]) -> str:
    rows = int(row.get("rows") or 0)
    accepted = int(row.get("scheduler_accepted_rows") or 0)
    strict_tick = int(row.get("strict_tick_rows") or 0)
    source_gap = int(row.get("source_gap_rows") or 0)
    if rows == 0:
        return "source_required_no_rows"
    if source_gap and source_gap >= rows:
        return "source_complete_label_required_before_authority"
    if accepted == 0:
        return "scheduler_or_selector_reject_context"
    if strict_tick == 0:
        return "proxy_only_requires_tick_realism"
    return "default_off_research_candidate_not_production_ready"


def build_downstream_contracts() -> dict[str, Any]:
    return {
        "schema_version": "v3_downstream_contracts_v1",
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "contracts": {
            "Selector V3": {
                "consume": [rel(OUTPUTS["policy_registry"]), rel(OUTPUTS["evaluation"]), rel(OUTPUTS["source_decisions"])],
                "required_fields": ["variant_id", "policy_routing_decision", "result_scope", "source_completeness_decision", "exact_r_status", "proxy_r_owned_by_v3"],
                "reject_if": ["broker-real rows are used as predecision features", "source gap rows are dropped from denominators"],
            },
            "Scheduler V3": {
                "consume": [rel(OUTPUTS["routing_ledger"]), rel(OUTPUTS["lifecycle_feasibility"]), rel(OUTPUTS["split_stress"])],
                "required_fields": ["policy_family", "lifecycle_feasibility_status", "broker_feasibility_status", "minimum_evidence_rows_observed"],
                "reject_if": ["partial/BE risk release lacks ticket-bound evidence", "same-symbol multi-ticket lifecycle identity missing"],
            },
            "ML": {
                "consume": [rel(OUTPUTS["evaluation"]), rel(OUTPUTS["failure_anatomy"]), rel(OUTPUTS["split_stress"])],
                "required_fields": ["result_scope", "proxy_expectancy_r", "failure_type", "split_scope", "split_key"],
                "reject_if": ["post-outcome broker-real labels leak into features", "proxy R is labeled as broker actual R"],
            },
            "Repair Companion": {
                "consume": [rel(OUTPUTS["source_gaps"]), rel(OUTPUTS["source_decisions"]), rel(OUTPUTS["lifecycle_feasibility"])],
                "required_fields": ["source_gap_reason", "recovery_requirement", "field", "source_state", "feasibility_decision"],
                "reject_if": ["generic needs more data", "missing source path/hash/read-only export requirement"],
            },
            "Command Center": {
                "consume": [rel(OUTPUTS["routing_package"]), rel(OUTPUTS["failure_anatomy"]), rel(OUTPUTS["runtime_boundary"])],
                "required_fields": ["package_status", "current_production_policy_status", "open_source_gaps", "runtime_effect_now"],
                "reject_if": ["default-off package displayed as live-active"],
            },
            "Production Change Dossier": {
                "consume": [rel(OUTPUTS["routing_package"]), rel(OUTPUTS["evaluation"]), rel(OUTPUTS["lifecycle_feasibility"]), rel(OUTPUTS["source_gaps"])],
                "required_fields": ["owner_approval_required_for_live_use", "runtime_effect_now", "exact_r_status", "proxy_r_owned_by_v3"],
                "reject_if": ["no sealed validation", "no broker lifecycle proof", "no cost/slippage/retcode proof", "owner approval absent"],
            },
        },
    }


def aggregate_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "missing") for row in rows).items()))


def build_default_off_package(
    registry_rows: list[dict[str, Any]],
    evaluation_rows: list[dict[str, Any]],
    routing_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
    lifecycle_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "v3_default_off_execution_policy_package_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "package_status": "default_off_not_live_activation",
        "runtime_effect_now": False,
        "owner_approval_required_for_live_use": True,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "current_production_policy_status": {
            "current_live_truth": "momentum_exhaustion primary with partial_be_runner exception selection",
            "v3_effect": "no live behavior change",
            "fixed_1_5r_j46_j49_status": "historical_or_comparator_only",
        },
        "counts": {
            "policy_variant_rows": len(registry_rows),
            "lane11_inherited_variant_rows": sum(1 for row in registry_rows if row.get("inherited_from_lane11")),
            "v3_added_variant_rows": sum(1 for row in registry_rows if not row.get("inherited_from_lane11")),
            "evaluation_rows": len(evaluation_rows),
            "routing_rows": len(routing_rows),
            "source_gap_rows": len(source_gap_rows),
            "lifecycle_feasibility_rows": len(lifecycle_rows),
        },
        "policy_family_counts": aggregate_counts(registry_rows, "policy_family"),
        "route_decision_counts": aggregate_counts(evaluation_rows, "policy_routing_decision"),
        "result_scope_counts": aggregate_counts(evaluation_rows, "result_scope"),
        "source_gap_decision_counts": aggregate_counts(source_gap_rows, "v3_decision"),
        "package_ledgers": {
            "policy_registry": rel(OUTPUTS["policy_registry"]),
            "evaluation": rel(OUTPUTS["evaluation"]),
            "routing_decisions": rel(OUTPUTS["routing_ledger"]),
            "lifecycle_feasibility": rel(OUTPUTS["lifecycle_feasibility"]),
            "source_gaps": rel(OUTPUTS["source_gaps"]),
            "failure_anatomy": rel(OUTPUTS["failure_anatomy"]),
        },
        "implementation_contract": {
            "entrypoint": "future owner-approved runtime adapter may read this package but must keep default-off until dossier approval",
            "required_runtime_flags": ["default_off", "owner_approved_production_change", "broker_lifecycle_source_complete"],
            "fail_closed_rules": [
                "no source gap row may be silently dropped",
                "no proxy R may be treated as broker actual R",
                "no modify-dependent policy without ticket/retcode/stop-freeze capture",
                "no partial policy without residual ticket identity",
                "no fixed 1.5R/J46/J49 activation from this route",
            ],
        },
    }


def build_context_anchor() -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False).stdout.strip()
    return "\n".join([
        "# Execution Policy V3 Context Anchor",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Generated: `{utc_now()}`",
        f"HEAD at build: `{head}`",
        "",
        "Evidence class: default-off execution-policy builder/repair/replay package.",
        "",
        "Mandatory context consumed from disk: LIVE_STATE, current system map, reading order, quick reference, goal_session_research_discipline, research_operating_doctrine, moonshot vision, Master post-Lane18 decision, Lane01-Lane18, Lane09B, Lane10B, Lane11, Lane16, Lane17, Lane18, post-Lane18 Source Capture Repair, and execution/lifecycle/broker diagnostic code.",
        "",
        "Hard boundary: no live broker/order/deal/position action, no paid API/vendor call, no credential/remote action, no live prompt/config/risk/execution/safety/canary/selector/scheduler activation.",
        "",
        "Continuation rule: after resume or uncertainty, regenerate LIVE_STATE, reread the controlling prompt and doctrine, then inspect this route's manifest, completion audit, verification result, policy registry, source-gap ledger, and routing package before continuing.",
        "",
    ])


def build_saturation_markdown(
    registry_rows: list[dict[str, Any]],
    evaluation_rows: list[dict[str, Any]],
    source_gap_rows: list[dict[str, Any]],
    lifecycle_rows: list[dict[str, Any]],
) -> str:
    route_counts = aggregate_counts(evaluation_rows, "policy_routing_decision")
    lifecycle_counts = aggregate_counts(lifecycle_rows, "feasibility_decision")
    gap_counts = aggregate_counts(source_gap_rows, "v3_decision")
    return "\n".join([
        "# V3 Saturation And Self-Red-Team",
        "",
        "Builder posture applied: constructive execution-builder, not G12 rejection posture.",
        "",
        "Anti-boxing checks pursued:",
        "",
        "- Lane11 baseline comparators were retained but not used as the horizon.",
        "- Lane16 path anatomy, Lane17 market-state source labels, Lane18 broker/cost contracts, and post-Lane18 source repair were joined into V3 decisions.",
        "- Source gaps were converted into capture/repair/source-required routes instead of being dropped.",
        "- Static fixed 1.5R/J46/J49 language was kept comparator-only.",
        "- No arbitrary top-N cutoff was used; generated ledgers preserve all Lane11 package/metric rows and all compact V3 source-decision rows.",
        "",
        "Self-red-team answers:",
        "",
        f"- Policy variant rows: `{len(registry_rows)}`.",
        f"- Evaluation rows: `{len(evaluation_rows)}`.",
        f"- Source-gap rows: `{len(source_gap_rows)}`.",
        f"- Lifecycle feasibility rows: `{len(lifecycle_rows)}`.",
        f"- Route decision counts: `{json.dumps(route_counts, sort_keys=True)}`.",
        f"- Lifecycle feasibility counts: `{json.dumps(lifecycle_counts, sort_keys=True)}`.",
        f"- Source-gap decision counts: `{json.dumps(gap_counts, sort_keys=True)}`.",
        "",
        "Remaining barriers are not generic blockers: each source-required row names a field family, source surface, or broker/lifecycle capture requirement in the machine-readable ledgers.",
        "",
        "Stop condition used: every executable local read, parser, join, proxy metric, source repair summary, code-surface audit, manifest, verifier, and focused test available inside this default-off evidence class is materialized. Live activation remains a separate forbidden production-change surface.",
        "",
    ])


def build_manifest() -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []

    def add_artifact(name: str, path: Path) -> None:
        if not path.exists():
            return
        row = {
            "name": name,
            "path": rel(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        if path.suffix in {".jsonl", ".gz"}:
            row["row_count"] = count_jsonl(path)
        artifacts.append(row)

    for name, path in ROUTE_SOURCE_FILES.items():
        add_artifact(name, path)
    for name, path in OUTPUTS.items():
        if not path.exists():
            continue
        add_artifact(name, path)
    return {
        "schema_version": "v3_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def write_status_files(verification_result: dict[str, Any] | None = None) -> None:
    write_json(OUTPUTS["runtime_boundary"], {
        "schema_version": "v3_runtime_effect_boundary_v1",
        "route_id": ROUTE_ID,
        "runtime_effect_now": False,
        "owner_approval_required_for_live_use": True,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "forbidden_surfaces": [
            "production-change activation",
            "live trading broker operation",
            "broker account/order/history/deal/position mutation",
            "paid API/vendor spend",
            "credential or remote push",
            "prompt/config/risk/execution/safety/canary/selector/scheduler live behavior change",
        ],
    })
    write_json(OUTPUTS["source_use"], {
        "schema_version": "v3_source_use_state_v1",
        "route_id": ROUTE_ID,
        "source_use_state": SOURCE_USE_STATE,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
    })
    write_json(OUTPUTS["result_use"], {
        "schema_version": "v3_result_use_status_v1",
        "route_id": ROUTE_ID,
        "result_use_status": RESULT_USE_STATUS,
        "exact_r_status": "not_owned_by_v3_except_upstream_sparse_broker_real_rows_kept_separate",
        "proxy_r_status": "owned_for_default_off_research_evaluation_where_source_bound_metrics_exist",
        "expectancy_status": "source_bound_proxy_expectancy_and_net_proxy_expectancy_materialized_in_evaluation_ledger",
        "proxy_to_production_leap_allowed": False,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
    })
    focused_present = OUTPUTS["focused_test"].exists()
    completion = {
        "schema_version": "v3_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "complete_verified_pending_scoped_commit" if verification_result and verification_result.get("ok") and focused_present else "outputs_built_pending_verification_or_focused_test",
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "result_use_status": RESULT_USE_STATUS,
        "source_use_state": SOURCE_USE_STATE,
        "scoped_commit_required": True,
        "instruction_coverage": {
            "live_state_regenerated": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "moonshot_vision_read": True,
            "master_post_lane18_decision_read": True,
            "lane01_to_lane18_lane09b_lane10b_lane11_read_from_disk": True,
            "post_lane18_source_capture_repair_consumed": True,
            "execution_lifecycle_broker_diagnostic_code_read": True,
            "constructive_execution_builder_posture_applied": True,
            "no_arbitrary_top_n": True,
            "baseline_only_closure_rejected": True,
            "live_activation_rejected": True,
        },
        "requirements": [
            {"requirement": "full_v3_policy_variant_registry", "status": "complete", "evidence": rel(OUTPUTS["policy_registry"])},
            {"requirement": "feasible_policy_simulation_evaluation_ledger", "status": "complete", "evidence": rel(OUTPUTS["evaluation"])},
            {"requirement": "non_replayable_source_gap_ledger", "status": "complete", "evidence": rel(OUTPUTS["source_gaps"])},
            {"requirement": "policy_routing_decision_package", "status": "complete", "evidence": [rel(OUTPUTS["routing_package"]), rel(OUTPUTS["routing_ledger"])]},
            {"requirement": "lifecycle_broker_tick_feasibility_ledger", "status": "complete", "evidence": rel(OUTPUTS["lifecycle_feasibility"])},
            {"requirement": "failure_anatomy_ledger", "status": "complete", "evidence": rel(OUTPUTS["failure_anatomy"])},
            {"requirement": "source_capture_and_completeness_decisions", "status": "complete", "evidence": rel(OUTPUTS["source_decisions"])},
            {"requirement": "branch_and_implementation_decisions", "status": "complete", "evidence": [rel(OUTPUTS["branch_decisions"]), rel(OUTPUTS["implementation_decisions"])]},
            {"requirement": "result_use_status_exact_proxy_r_expectancy_fields", "status": "complete", "evidence": rel(OUTPUTS["result_use"])},
            {"requirement": "split_stress_deconcentration_outputs", "status": "complete", "evidence": rel(OUTPUTS["split_stress"])},
            {"requirement": "downstream_contracts", "status": "complete", "evidence": rel(OUTPUTS["downstream_contracts"])},
            {"requirement": "manifest_verifier_focused_tests", "status": "complete" if verification_result and verification_result.get("ok") and focused_present else "pending", "evidence": [rel(OUTPUTS["manifest"]), rel(OUTPUTS["verification"]), rel(OUTPUTS["focused_test"])]},
            {"requirement": "scoped_commit", "status": "pending_after_verification", "evidence": "git commit required after current audit"},
        ],
        "verification_result": verification_result,
    }
    write_json(OUTPUTS["completion"], completion)


def build_route_outputs() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    lane16_summary = summarize_lane16_path()

    input_rows = build_input_evidence_rows()
    code_rows = build_code_surface_rows()
    registry_rows = build_policy_registry(lane16_summary)
    registry_by_id = {str(row["variant_id"]): row for row in registry_rows}
    evaluation_rows = build_evaluation_rows(registry_by_id)
    source_gap_rows = build_source_gap_rows(lane16_summary)
    lifecycle_rows = build_lifecycle_feasibility_rows()
    failure_rows = build_failure_anatomy_rows(lane16_summary)
    routing_rows = build_routing_rows(registry_by_id)
    source_decision_rows = build_source_decision_rows()
    branch_rows = build_branch_decision_rows()
    implementation_rows = build_implementation_decision_rows()
    split_rows = build_split_stress_rows()
    downstream_contracts = build_downstream_contracts()
    default_off_package = build_default_off_package(registry_rows, evaluation_rows, routing_rows, source_gap_rows, lifecycle_rows)

    OUTPUTS["context_anchor"].write_text(build_context_anchor(), encoding="utf-8")
    write_jsonl(OUTPUTS["input_evidence"], input_rows)
    write_jsonl(OUTPUTS["code_surface"], code_rows)
    write_jsonl(OUTPUTS["policy_registry"], registry_rows)
    write_jsonl(OUTPUTS["evaluation"], evaluation_rows)
    write_jsonl(OUTPUTS["source_gaps"], source_gap_rows)
    write_json(OUTPUTS["routing_package"], default_off_package)
    write_jsonl(OUTPUTS["routing_ledger"], routing_rows)
    write_jsonl(OUTPUTS["lifecycle_feasibility"], lifecycle_rows)
    write_jsonl(OUTPUTS["failure_anatomy"], failure_rows)
    write_jsonl(OUTPUTS["source_decisions"], source_decision_rows)
    write_jsonl(OUTPUTS["branch_decisions"], branch_rows)
    write_jsonl(OUTPUTS["implementation_decisions"], implementation_rows)
    write_jsonl(OUTPUTS["split_stress"], split_rows)
    write_json(OUTPUTS["downstream_contracts"], downstream_contracts)
    OUTPUTS["saturation"].write_text(build_saturation_markdown(registry_rows, evaluation_rows, source_gap_rows, lifecycle_rows), encoding="utf-8")
    write_status_files()
    write_json(OUTPUTS["manifest"], build_manifest())
    return verify_outputs(write=True, require_focused_test=False)


def verify_outputs(*, write: bool = False, count_large: bool = True, require_focused_test: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    counts: dict[str, Any] = {}
    required = [
        "context_anchor",
        "input_evidence",
        "code_surface",
        "policy_registry",
        "evaluation",
        "source_gaps",
        "routing_package",
        "routing_ledger",
        "lifecycle_feasibility",
        "failure_anatomy",
        "source_decisions",
        "branch_decisions",
        "implementation_decisions",
        "result_use",
        "split_stress",
        "downstream_contracts",
        "runtime_boundary",
        "source_use",
        "saturation",
        "manifest",
        "completion",
    ]
    for name in required:
        if not OUTPUTS[name].exists():
            issues.append(f"missing_required_output:{name}:{rel(OUTPUTS[name])}")
    if OUTPUTS["policy_registry"].exists():
        registry_rows = list(iter_jsonl(OUTPUTS["policy_registry"]))
        counts["policy_variant_rows"] = len(registry_rows)
        counts["lane11_inherited_variant_rows"] = sum(1 for row in registry_rows if row.get("inherited_from_lane11"))
        counts["v3_added_variant_rows"] = sum(1 for row in registry_rows if not row.get("inherited_from_lane11"))
        counts["policy_family_counts"] = aggregate_counts(registry_rows, "policy_family")
        if counts["lane11_inherited_variant_rows"] < 890:
            issues.append("lane11_expanded_variants_truncated")
        if counts["policy_variant_rows"] <= 890:
            issues.append("baseline_or_lane11_only_registry_no_v3_expansion")
        families = set(counts["policy_family_counts"])
        for family in ["partial_be_runner", "momentum_exhaustion", "trailing_runner", "time_stop", "be_after_trigger"]:
            if family not in families:
                issues.append(f"missing_policy_family:{family}")
    if count_large and OUTPUTS["evaluation"].exists():
        counts["evaluation_rows"] = count_jsonl(OUTPUTS["evaluation"])
        if counts["evaluation_rows"] < 106_000:
            issues.append("evaluation_ledger_does_not_preserve_lane11_baseline_and_expanded_metric_rows")
    if count_large and OUTPUTS["routing_ledger"].exists():
        counts["routing_rows"] = count_jsonl(OUTPUTS["routing_ledger"])
        if counts["routing_rows"] < 7_398:
            issues.append("routing_ledger_does_not_preserve_lane11_package_rows")
    if count_large and OUTPUTS["source_gaps"].exists():
        counts["source_gap_rows"] = count_jsonl(OUTPUTS["source_gaps"])
        if counts["source_gap_rows"] < 6_102:
            issues.append("source_gap_ledger_does_not_preserve_lane11_expanded_source_gaps")
    if OUTPUTS["lifecycle_feasibility"].exists():
        lifecycle_rows = list(iter_jsonl(OUTPUTS["lifecycle_feasibility"]))
        counts["lifecycle_feasibility_rows"] = len(lifecycle_rows)
        required_fields = {row["field"] for row in lifecycle_rows}
        for field in BROKER_FIELD_FAMILIES:
            if field not in required_fields:
                issues.append(f"missing_lifecycle_field:{field}")
    if OUTPUTS["routing_package"].exists():
        package = read_json(OUTPUTS["routing_package"])
        if package.get("runtime_effect_now") is not False:
            issues.append("routing_package_runtime_effect_not_false")
        if package.get("owner_approval_required_for_live_use") is not True:
            issues.append("routing_package_owner_approval_not_required")
        text = json.dumps(package).lower()
        if "fixed_1_5r_j46_j49_status" not in text:
            issues.append("fixed_1_5r_j46_j49_comparator_status_missing")
    if OUTPUTS["result_use"].exists():
        result_use = read_json(OUTPUTS["result_use"])
        if result_use.get("proxy_to_production_leap_allowed") is not False:
            issues.append("proxy_to_production_leap_not_blocked")
    if OUTPUTS["focused_test"].exists():
        counts["focused_test_present"] = True
        text = OUTPUTS["focused_test"].read_text(encoding="utf-8", errors="replace")
        if 'failures="0"' not in text or 'errors="0"' not in text:
            issues.append("focused_test_result_not_green")
    else:
        counts["focused_test_present"] = False
        if require_focused_test:
            issues.append("missing_focused_test_result")
    result = {
        "schema_version": "v3_verification_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "counts": counts,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
    }
    if write:
        write_json(OUTPUTS["verification"], result)
        write_status_files(result)
        write_json(OUTPUTS["manifest"], build_manifest())
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        result = verify_outputs(write=True)
    else:
        result = build_route_outputs()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
