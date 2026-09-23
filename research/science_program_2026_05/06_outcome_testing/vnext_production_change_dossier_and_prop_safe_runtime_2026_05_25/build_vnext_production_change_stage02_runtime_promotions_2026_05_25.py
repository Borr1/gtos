from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage01_decision_surfaces_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage01", MODULE_PATH)
stage01 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage01)

REPO_ROOT = stage01.REPO_ROOT
ROUTE_ID = stage01.ROUTE_ID
ROUTE_DIR = stage01.ROUTE_DIR
REPLAY_DIR = stage01.REPLAY_DIR
STATE_PATH = stage01.STATE_PATH
DECISION_SURFACE_LEDGER_PATH = stage01.DECISION_SURFACE_LEDGER_PATH
RUNTIME_CHANGE_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_RUNTIME_CHANGE_LEDGER_2026-05-25.jsonl"
)
STAGE02_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE02_RUNTIME_PROMOTION_SUMMARY_2026-05-25.json"
)
STAGE02_VERIFICATION_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE02_VERIFICATION_RESULT_2026-05-25.json"
)

PROMOTED_DECISION = "PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER"
EVIDENCE_FAMILY = "gtos_vnext_production_change_promotions"
SOURCE_NAME = "vnext_production_change_promoted_stage06_final_map"
FINAL_DECISION_MAP_REL = (
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24/"
    "VNEXT_FULL_REPLAY_FINAL_DECISION_MAP_2026-05-24.jsonl"
)
EXPECTED_UNIQUE_PROMOTED_DECISION_MAP_IDS = 982

SESSION_BUCKET_TO_ROUTE_SESSION = {
    "london_broad": "london_core",
    "ny_broad": "ny_core",
    "tokyo_broad": "tokyo_kz",
    "off_kz_broad": "off_core_session",
}
FRAMEWORK_ROUTE_FAMILY = {
    "ob_retest": "ob_retest",
    "fvg_fill": "fvg_fill",
    "breaker_re_entry": "breaker_re_entry",
    "breaker_retest": "breaker_re_entry",
    "breaker_block_retest": "breaker_re_entry",
    "breaker_block": "breaker_re_entry",
    "breaker": "breaker_re_entry",
}
SYMBOL_FAMILY_BY_PREFIX = {
    "XAUUSD": "XAUUSD_GC_FAMILY",
    "GC": "XAUUSD_GC_FAMILY",
    "XAGUSD": "XAGUSD_SILVER_FAMILY",
    "SI": "XAGUSD_SILVER_FAMILY",
    "US30": "US30_DOW_FAMILY",
    "NAS100": "NAS100_NQ_FAMILY",
    "NDX100": "NAS100_NQ_FAMILY",
    "GER40": "GER40_DAX_FAMILY",
    "DE40": "GER40_DAX_FAMILY",
    "UK100": "UK100_FTSE_FAMILY",
    "JP225": "JP225_NIKKEI_FAMILY",
    "SPX500": "SPX500_ES_FAMILY",
    "BTCUSD": "BTCUSD_CRYPTO_FAMILY",
    "ETHUSD": "ETHUSD_CRYPTO_FAMILY",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return stage01.rel(path)


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]


def atomic_json_write(path: Path, payload: Any) -> None:
    stage01.atomic_json_write(REPO_ROOT / path if not path.is_absolute() else path, payload)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    target = REPO_ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")
    tmp.replace(target)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except Exception:
        return "UNKNOWN"


def git_status_short() -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            text=True,
        )
    except Exception:
        return []
    return [line for line in output.splitlines() if line.strip()]


def as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    numeric = as_float(value)
    if numeric is None:
        return None
    return int(numeric)


def first_numeric(mapping: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = as_float(mapping.get(key))
        if value is not None:
            return value
    return None


def metric_count(row: dict[str, Any], metrics: dict[str, Any]) -> float:
    count = first_numeric(
        metrics,
        (
            "performance_count",
            "denominator_count",
            "effective_n",
            "n",
            "count",
            "trade_count",
        ),
    )
    if count is not None and count > 0:
        return count
    candidate_count = as_float(row.get("candidate_count"))
    return candidate_count if candidate_count and candidate_count > 0 else 1.0


def metric_total(metrics: dict[str, Any], count: float) -> float | None:
    total = first_numeric(
        metrics,
        (
            "total_r",
            "cost_adjusted_total_r",
            "proxy_total_r",
            "proxy_r_sum",
            "r_sum",
            "sum_r",
        ),
    )
    if total is not None:
        return total
    mean = first_numeric(metrics, ("mean_r", "expectancy_r", "proxy_mean_r", "mean"))
    if mean is not None:
        return mean * count
    return None


def metric_trace(sum_value: float | None, count: float, metrics: dict[str, Any]) -> dict[str, Any]:
    if sum_value is None:
        return {
            "sum": None,
            "mean": None,
            "match_rows_with_metric": 0,
            "positive_rows": 0,
            "negative_rows": 0,
            "zero_rows": 0,
        }
    win_count = as_int(metrics.get("win_count")) or as_int(metrics.get("wins"))
    loss_count = as_int(metrics.get("loss_count")) or as_int(metrics.get("losses"))
    zero_count = as_int(metrics.get("zero_count")) or as_int(metrics.get("scratch_count"))
    return {
        "sum": round(sum_value, 12),
        "mean": round(sum_value / count, 12) if count else None,
        "match_rows_with_metric": count,
        "positive_rows": win_count if win_count is not None else (1 if sum_value > 0 else 0),
        "negative_rows": loss_count if loss_count is not None else (1 if sum_value < 0 else 0),
        "zero_rows": zero_count if zero_count is not None else (1 if sum_value == 0 else 0),
    }


def r_metric_traces(row: dict[str, Any]) -> dict[str, Any]:
    metrics = row.get("r_metrics") if isinstance(row.get("r_metrics"), dict) else {}
    count = metric_count(row, metrics)
    total = metric_total(metrics, count)
    stress_total = first_numeric(
        metrics,
        ("stress_total_r", "stress_simulated_r", "stress_r", "cost_stress_total_r"),
    )
    return {
        "cost_adjusted_simulated_r": metric_trace(total, count, metrics),
        "proxy_score": metric_trace(total, count, metrics),
        "stress_simulated_r": metric_trace(stress_total, count, metrics),
        "effective_n": {
            "sum": count,
            "mean": count,
            "match_rows_with_metric": 1,
            "positive_rows": 1 if count > 0 else 0,
            "negative_rows": 0,
            "zero_rows": 1 if count == 0 else 0,
        },
    }


def route_session(row: dict[str, Any]) -> str:
    bucket = str(row.get("session_bucket") or "")
    return SESSION_BUCKET_TO_ROUTE_SESSION.get(bucket, bucket)


def symbol_family(symbol: str) -> str:
    upper = symbol.upper()
    for prefix, family in SYMBOL_FAMILY_BY_PREFIX.items():
        if upper.startswith(prefix):
            return family
    return ""


def normalized_framework(row: dict[str, Any]) -> str:
    return str(row.get("framework") or "").strip()


def original_source_component(row: dict[str, Any]) -> str:
    return str(row.get("source_component") or "unknown_component")


def generated_source_component(row: dict[str, Any], total: float | None) -> str:
    component = original_source_component(row)
    action_class = str(row.get("action_class") or "").casefold()
    surface = str(row.get("surface") or "")
    if surface == "path_nofill_pending_lifecycle":
        if "target_first" in action_class:
            return "static_limit_adaptive_entry_challenger"
        if total is not None and total > 0:
            return "nofill_near_miss_market_entry"
        return "nofill_far_miss_retest"
    if component == "unknown_component":
        return "vnext_production_change_unknown_component"
    return component


def generated_route_family(row: dict[str, Any], source_component: str) -> str:
    original_component = original_source_component(row)
    if source_component.startswith("nofill_") or source_component.startswith("static_limit_"):
        return "nofill_mechanical"
    if original_component.startswith("rejected_candidate") or original_component.startswith("l2_"):
        return "numeric_router"
    framework = normalized_framework(row).casefold()
    return FRAMEWORK_ROUTE_FAMILY.get(framework, "numeric_router")


def proxy_class(total: float | None, count: float) -> str:
    if total is None:
        return "UNKNOWN_PROXY_R"
    mean = total / count if count else total
    if total > 0:
        return "STRONG_POSITIVE_PROXY_R" if count >= 20 and mean > 0 else "POSITIVE_PROXY_R"
    if total < 0:
        return "STRONG_NEGATIVE_PROXY_R" if count >= 20 and mean < 0 else "NEGATIVE_PROXY_R"
    return "FLAT_PROXY_R"


def target_stop_order_class(row: dict[str, Any], total: float | None) -> str:
    existing = str(row.get("target_stop_order_class") or "")
    if existing:
        return existing
    action_class = str(row.get("action_class") or "").casefold()
    if "stop_first" in action_class:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "target_first" in action_class or (total is not None and total > 0):
        return "TARGET_FIRST_PROXY_DOMINANT"
    return "UNKNOWN_TARGET_STOP_ORDERING"


def runtime_decision(row: dict[str, Any], total: float | None) -> str:
    action_class = str(row.get("action_class") or "").casefold()
    baseline = str(row.get("baseline_decision") or "").upper()
    component = original_source_component(row)
    if component == "unknown_component" or "unknown_action_class" in action_class:
        return "MIXED"
    if "avoid" in action_class or "filter" in action_class or baseline == "AVOID":
        return "AVOID"
    if "follow" in action_class or baseline == "FOLLOW":
        return "FOLLOW"
    if baseline == "PATH_TRUTH_ONLY" and total is not None and total > 0:
        return "FOLLOW"
    if total is not None and total > 0:
        return "FOLLOW"
    if total is not None and total < 0:
        return "AVOID"
    return "MIXED"


def review_action(decision: str) -> str:
    if decision == "FOLLOW":
        return "DEFAULT_OFF_FOLLOW_SCORER_REVIEW"
    if decision == "AVOID":
        return "DEFAULT_OFF_AVOID_FILTER_REVIEW"
    return "DEFAULT_OFF_MIXED_SOURCE_REPAIR_GUARD"


def action_family(decision: str) -> str:
    if decision == "FOLLOW":
        return "production_change_follow_pressure"
    if decision == "AVOID":
        return "production_change_avoid_pressure"
    return "production_change_non_override_guard"


def build_event_scope(
    row: dict[str, Any],
    *,
    source_component: str,
    route_family: str,
    proxy_r_class: str,
    target_stop_class: str,
    actionable: bool,
) -> dict[str, Any]:
    symbol = str(row.get("symbol") or "")
    session = route_session(row)
    side = str(row.get("side") or "")
    framework = normalized_framework(row)
    scope: dict[str, Any] = {}
    if symbol:
        scope["symbol"] = symbol
        scope["source_symbol"] = symbol
        family = symbol_family(symbol)
        if family:
            scope["symbol_family"] = family
        scope["market"] = symbol
    if session:
        scope["route_session"] = session
    if side:
        scope["side"] = side
    if framework:
        scope["framework"] = framework
    if route_family:
        scope["route_family"] = route_family
    timeframe = str(row.get("market_timeframe") or row.get("timeframe") or "M15")
    if timeframe:
        scope["market_timeframe"] = timeframe
        scope["timeframe"] = timeframe
    if actionable and not source_component.endswith("unknown_component"):
        scope["source_component"] = source_component
    if proxy_r_class:
        scope["proxy_r_class"] = proxy_r_class
    if target_stop_class:
        scope["target_stop_order_class"] = target_stop_class
    return {key: value for key, value in scope.items() if value not in (None, "")}


def has_required_anchors(scope: dict[str, Any]) -> bool:
    has_symbol_anchor = any(scope.get(field) for field in ("symbol", "source_symbol", "symbol_family", "market"))
    return bool(has_symbol_anchor and scope.get("route_session") and scope.get("side"))


def load_stage01_group_lookup() -> dict[tuple[str, ...], dict[str, Any]]:
    groups = read_jsonl(DECISION_SURFACE_LEDGER_PATH)
    lookup: dict[tuple[str, ...], dict[str, Any]] = {}
    for group in groups:
        key_payload = group["group_key"]
        key = (
            key_payload["runtime_surface"],
            key_payload["surface"],
            key_payload["source_component"],
            key_payload["action_class"],
            key_payload["implementation_decision"],
            key_payload["runtime_mode"],
            key_payload["baseline_decision"],
            key_payload["evidence_family"],
        )
        lookup[key] = group
    return lookup


def stage01_group_for_row(
    row: dict[str, Any],
    group_lookup: dict[tuple[str, ...], dict[str, Any]],
) -> dict[str, Any] | None:
    target = stage01.target_for_row(row)
    key = stage01.group_key(row, target)
    return group_lookup.get(key)


def runtime_row(
    *,
    row: dict[str, Any],
    meta: dict[str, Any],
    instance_index: int,
    duplicate_index: int,
    group: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = row.get("r_metrics") if isinstance(row.get("r_metrics"), dict) else {}
    count = metric_count(row, metrics)
    total = metric_total(metrics, count)
    decision = runtime_decision(row, total)
    source_component = generated_source_component(row, total)
    route_family = generated_route_family(row, source_component)
    proxy_r_class = proxy_class(total, count)
    target_stop_class = target_stop_order_class(row, total)
    initial_scope = build_event_scope(
        row,
        source_component=source_component,
        route_family=route_family,
        proxy_r_class=proxy_r_class,
        target_stop_class=target_stop_class,
        actionable=decision in {"FOLLOW", "AVOID"},
    )
    actionable = decision in {"FOLLOW", "AVOID"} and has_required_anchors(initial_scope)
    if not actionable:
        decision = "MIXED"
    event_scope = build_event_scope(
        row,
        source_component=source_component,
        route_family=route_family,
        proxy_r_class=proxy_r_class,
        target_stop_class=target_stop_class,
        actionable=actionable,
    )
    decision_map_row_id = str(row.get("decision_map_row_id") or f"missing-{instance_index}")
    review_row_id = f"prodchg_promote_{instance_index:06d}_{stable_hash([decision_map_row_id, duplicate_index])}"
    runtime_surface = (
        group["group_key"]["runtime_surface"] if group else stage01.target_for_row(row)["runtime_surface"]
    )
    implementation_action = {
        "FOLLOW": "PROMOTE_REPLAY_MEASURED_FOLLOW_PRESSURE_ACTIVATION_GATED",
        "AVOID": "PROMOTE_REPLAY_MEASURED_AVOID_PRESSURE_ACTIVATION_GATED",
        "MIXED": "PROMOTE_AS_NON_OVERRIDE_SOURCE_REPAIR_GUARD",
    }[decision]
    scope_key = "|".join(f"{key}={value}" for key, value in sorted(event_scope.items()))
    return {
        "schema_version": "vnext_production_change_runtime_change_row_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_02_PROMOTION_IMPLEMENTATION",
        "row_type": "gtos_vnext_production_change_promoted_runtime_row",
        "review_row_id": review_row_id,
        "row_key": review_row_id,
        "source_row_id": decision_map_row_id,
        "source_row_instance_index": duplicate_index,
        "source_row_fingerprint": stable_hash(row),
        "stage01_group_id": group.get("group_id") if group else None,
        "event_scope": event_scope,
        "scope_key": scope_key,
        "review_action": review_action(decision),
        "computed_decision": decision,
        "implementation_action": implementation_action,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_group": runtime_surface,
        "source_role": "production_change_promotion",
        "system_surface": runtime_surface,
        "source_component": source_component,
        "original_source_component": original_source_component(row),
        "action_family": action_family(decision),
        "action_class": str(row.get("action_class") or "unknown_action_class"),
        "original_action_class": str(row.get("action_class") or "unknown_action_class"),
        "framework": normalized_framework(row),
        "route_family": route_family,
        "market_timeframe": event_scope.get("market_timeframe"),
        "timeframe": event_scope.get("timeframe"),
        "route_session": event_scope.get("route_session"),
        "side": event_scope.get("side"),
        "symbol": event_scope.get("symbol"),
        "source_symbol": event_scope.get("source_symbol"),
        "symbol_family": event_scope.get("symbol_family"),
        "market": event_scope.get("market"),
        "proxy_r_class": proxy_r_class,
        "target_stop_order_class": target_stop_class,
        "r_evidence_class": "STAGE06_REPLAY_PROMOTION_PROXY_R",
        "r_metric_traces": r_metric_traces(row),
        "source_path": FINAL_DECISION_MAP_REL,
        "source_artifact": FINAL_DECISION_MAP_REL,
        "source_chunk_path": meta.get("chunk_path"),
        "source_chunk_sha256": meta.get("sha256"),
        "source_final_decision": row.get("implementation_decision"),
        "baseline_decision": row.get("baseline_decision"),
        "source_surface": row.get("surface"),
        "source_runtime_mode": row.get("runtime_mode"),
        "source_evidence_family": row.get("evidence_family"),
        "source_candidate_count": row.get("candidate_count"),
        "source_counterfactual_change_count": row.get("counterfactual_change_count"),
        "source_r_metrics": metrics,
        "runtime_candidate_use_permitted": actionable,
        "activation_gated": True,
        "production_activation_gate": "gtos_vnext_runtime.apply_to_execution",
        "pre_ai_activation_gate": "gtos_vnext_runtime.pre_ai_apply_to_ai_call",
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "production_change_allowed_by_this_row": False,
        "requires_owner_review_before_runtime_effect": True,
        "no_live_trading": True,
        "no_broker_mutation": True,
        "no_paid_api_or_vendor_call": True,
    }


def build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    group_lookup = load_stage01_group_lookup()
    rows: list[dict[str, Any]] = []
    duplicate_counter: Counter[str] = Counter()
    missing_group_ids: list[str] = []
    for meta, row in stage01.final_decision_rows():
        if row.get("implementation_decision") != PROMOTED_DECISION:
            continue
        decision_map_row_id = str(row.get("decision_map_row_id") or "")
        duplicate_counter[decision_map_row_id] += 1
        group = stage01_group_for_row(row, group_lookup)
        if group is None and decision_map_row_id:
            missing_group_ids.append(decision_map_row_id)
        rows.append(
            runtime_row(
                row=row,
                meta=meta,
                instance_index=len(rows) + 1,
                duplicate_index=duplicate_counter[decision_map_row_id],
                group=group,
            )
        )
    summary = summarize_rows(rows, missing_group_ids)
    return rows, summary


def summarize_rows(rows: list[dict[str, Any]], missing_group_source_ids: list[str]) -> dict[str, Any]:
    source_ids = [str(row.get("source_row_id") or "") for row in rows]
    source_id_counts = Counter(source_ids)
    decision_counts = Counter(str(row.get("computed_decision") or "") for row in rows)
    surface_counts = Counter(str(row.get("system_surface") or "") for row in rows)
    source_component_counts = Counter(str(row.get("source_component") or "") for row in rows)
    original_source_component_counts = Counter(
        str(row.get("original_source_component") or "") for row in rows
    )
    route_family_counts = Counter(str(row.get("route_family") or "") for row in rows)
    actionable_rows = [row for row in rows if row.get("runtime_candidate_use_permitted")]
    unanchored_rows = [
        row for row in rows if not has_required_anchors(row.get("event_scope") or {})
    ]
    return {
        "schema_version": "vnext_production_change_stage02_runtime_promotion_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "runtime_change_ledger_path": rel(REPO_ROOT / RUNTIME_CHANGE_LEDGER_PATH),
        "source_final_decision_map_path": FINAL_DECISION_MAP_REL,
        "expected_unique_promoted_decision_map_ids": EXPECTED_UNIQUE_PROMOTED_DECISION_MAP_IDS,
        "promoted_runtime_row_instances": len(rows),
        "unique_promoted_decision_map_row_ids": len(source_id_counts),
        "duplicate_promoted_decision_map_row_id_count": sum(
            1 for _row_id, count in source_id_counts.items() if count > 1
        ),
        "duplicate_promoted_decision_map_row_id_extra_instances": sum(
            count - 1 for count in source_id_counts.values() if count > 1
        ),
        "runtime_candidate_use_permitted_rows": len(actionable_rows),
        "non_override_guard_rows": len(rows) - len(actionable_rows),
        "unanchored_guard_rows": len(unanchored_rows),
        "decision_counts": dict(sorted(decision_counts.items())),
        "system_surface_counts": dict(sorted(surface_counts.items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "original_source_component_counts": dict(sorted(original_source_component_counts.items())),
        "route_family_counts": dict(sorted(route_family_counts.items())),
        "missing_stage01_group_source_ids": sorted(set(missing_group_source_ids)),
        "artifact_config_path": rel(REPO_ROOT / RUNTIME_CHANGE_LEDGER_PATH),
        "artifact_evidence_family": EVIDENCE_FAMILY,
    }


def verify_rows(rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if summary["unique_promoted_decision_map_row_ids"] != EXPECTED_UNIQUE_PROMOTED_DECISION_MAP_IDS:
        failures.append(
            "unique promoted decision-map ids expected "
            f"{EXPECTED_UNIQUE_PROMOTED_DECISION_MAP_IDS} got "
            f"{summary['unique_promoted_decision_map_row_ids']}"
        )
    if not rows:
        failures.append("no promoted runtime rows generated")
    if summary["missing_stage01_group_source_ids"]:
        failures.append(
            "some promoted rows did not map back to a Stage01 group: "
            f"{summary['missing_stage01_group_source_ids'][:10]}"
        )
    for row in rows:
        for field in (
            "live_effect",
            "broker_operation",
            "paid_api_or_vendor_call",
            "runtime_trading_or_live_broker_effect",
            "production_change_allowed_by_this_row",
        ):
            if row.get(field) is not False:
                failures.append(f"{row.get('review_row_id')} has unsafe flag {field}={row.get(field)}")
        if row.get("requires_owner_review_before_runtime_effect") is not True:
            failures.append(f"{row.get('review_row_id')} does not preserve owner activation gate")
        scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
        if row.get("runtime_candidate_use_permitted") and not has_required_anchors(scope):
            failures.append(f"{row.get('review_row_id')} is actionable without required anchors")
        if not row.get("runtime_candidate_use_permitted") and row.get("computed_decision") != "MIXED":
            failures.append(f"{row.get('review_row_id')} non-actionable row is not MIXED guarded")
    return failures


def update_state(summary: dict[str, Any], *, complete: bool) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = git_head()
    state["dirty_tracked_paths"] = git_status_short()
    state["current_stage"] = (
        "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"
        if complete
        else "STAGE_02_PROMOTION_IMPLEMENTATION"
    )
    state["stage_status_table"]["STAGE_02_PROMOTION_IMPLEMENTATION"] = (
        "complete" if complete else "in_progress"
    )
    if complete:
        state["stage_status_table"]["STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"] = "in_progress"
        state["active_invariant"] = "implement_kill_redesign_and_guard_only_decision_surface_groups"
        state["first_incomplete_invariant"] = "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"
        state["exact_next_action"] = (
            "Implement KILL_OR_REDESIGN_BEFORE_USE and KEEP_SHADOW_OR_GUARD_ONLY "
            "decision-surface groups as runtime kills, redesigns, and non-override guards."
        )
    else:
        state["active_invariant"] = "implement_promoted_decision_surface_groups"
        state["first_incomplete_invariant"] = "STAGE_02_PROMOTION_IMPLEMENTATION"
        state["exact_next_action"] = (
            "Run Stage02 verifier and focused runtime/config tests for the promoted "
            "runtime change ledger, then mark Stage02 complete if all checks pass."
        )
    state["output_artifact_paths"]["runtime_change_ledger"] = rel(
        REPO_ROOT / RUNTIME_CHANGE_LEDGER_PATH
    )
    state["output_artifact_paths"]["stage02_runtime_promotion_summary"] = rel(
        REPO_ROOT / STAGE02_SUMMARY_PATH
    )
    state["output_artifact_paths"]["stage02_verification_result"] = rel(
        REPO_ROOT / STAGE02_VERIFICATION_RESULT_PATH
    )
    state["rows_groups_processed"]["stage02_promoted_runtime_row_instances"] = summary[
        "promoted_runtime_row_instances"
    ]
    state["rows_groups_processed"]["stage02_unique_promoted_decision_map_row_ids"] = summary[
        "unique_promoted_decision_map_row_ids"
    ]
    state["row_count_hash_coverage"]["stage02_runtime_promotion_summary"] = {
        "promoted_runtime_row_instances": summary["promoted_runtime_row_instances"],
        "unique_promoted_decision_map_row_ids": summary[
            "unique_promoted_decision_map_row_ids"
        ],
        "decision_counts": summary["decision_counts"],
        "system_surface_counts": summary["system_surface_counts"],
        "source_component_counts": summary["source_component_counts"],
    }
    state["implemented_surfaces"] = [
        {
            "stage": "STAGE_02_PROMOTION_IMPLEMENTATION",
            "surface": surface,
            "runtime_row_count": count,
            "artifact": summary["runtime_change_ledger_path"],
            "activation_gate": "gtos_vnext_runtime.apply_to_execution",
        }
        for surface, count in summary["system_surface_counts"].items()
    ]
    state["verification_status"]["stage02_runtime_change_ledger_built"] = True
    state["verification_status"]["stage02_runtime_promotion_rows"] = summary[
        "promoted_runtime_row_instances"
    ]
    state["verification_status"]["stage02_runtime_promotion_unique_ids"] = summary[
        "unique_promoted_decision_map_row_ids"
    ]
    state["verification_status"]["stage02_runtime_promotion_verifier_ok"] = complete
    stage01.stage00.atomic_json_write(state_path, state)


def main() -> int:
    rows, summary = build_runtime_rows()
    failures = verify_rows(rows, summary)
    write_jsonl(RUNTIME_CHANGE_LEDGER_PATH, rows)
    atomic_json_write(STAGE02_SUMMARY_PATH, summary)
    update_state(summary, complete=False)
    result = {
        "schema_version": "vnext_production_change_stage02_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary": summary,
        "first_incomplete_invariant": "STAGE_02_PROMOTION_IMPLEMENTATION",
    }
    atomic_json_write(STAGE02_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
