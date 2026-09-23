#!/usr/bin/env python3
"""Build a full branch-level R-style proxy outcome layer for Route C."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

BRANCH_PROXY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_BRANCH_SCORE_LEDGER_2026-05-16.jsonl"
BRANCH_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_BRANCH_QUEUE_2026-05-16.jsonl"
BRANCH_EFFECTIVE_N_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_2026-05-16.jsonl"
BRANCH_IMPLEMENTATION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_IMPLEMENTATION_IMPLICATION_LEDGER_2026-05-16.jsonl"
TARGET_STOP_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl"
COST_FILL_GRID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_GRID_LEDGER_2026-05-16.jsonl"
PATH_CONTROL_GRID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_GRID_LEDGER_2026-05-16.jsonl"
PATH_CONTROL_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"
PATH_DESCRIPTOR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_EVENT_DESCRIPTOR_LEDGER_2026-05-16.jsonl"
M1_REPLAY_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
FILL_BAR_STRESS_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_SIGNATURE_LEDGER_2026-05-16.jsonl"
PARTIAL_REPAIR_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_SIGNATURE_SCOPE_LEDGER_2026-05-16.jsonl"
TARGETSTOP_NA_REPAIR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_BRANCH_LEDGER_2026-05-16.jsonl"
RECOVERED_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_SIGNATURE_JOIN_LEDGER_2026-05-16.jsonl"
NEAR_MARKET_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_MARKET_ENTRY_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_OFFSET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_OFFSET_BRANCH_LEDGER_2026-05-16.jsonl"
FAR_AVOID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl"
FAR_RETEST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_DESCRIPTOR_DELTA_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS_LEDGER_2026-05-16.jsonl"
CONTROL_SCREEN_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CONTROL_SCREEN_ROUTE_QUEUE_2026-05-15.jsonl"
NEIGHBOR_PLACEBO_SURVIVOR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_SURVIVOR_QUEUE_2026-05-15.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_RESULT_2026-05-16.json"
BRANCH_OUTCOME_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BRANCH_LEDGER_2026-05-16.jsonl"
CONTROL_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CONTROL_DELTA_LEDGER_2026-05-16.jsonl"
CAUSE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CAUSE_LEDGER_2026-05-16.jsonl"
CONCENTRATION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CONCENTRATION_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
SUBAGENT_LEDGER_PATH = ROUTE_DIR / "SUBAGENT_DELEGATION_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay branch R-style proxy outcome layer only. Rows "
    "convert all 386 branch-queue rows into mechanically available target/stop "
    "order proxies, R-style interval proxies, control deltas, source/ambiguity "
    "causes, concentration, and implementation implications. Exact broker R/PnL, "
    "strategy expectancy, win-rate, validation, live-readiness, promotion, and "
    "live behavior change are not claimed."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no, "_source_path": str(path)}


def rows(path: Path) -> list[dict[str, Any]]:
    return list(read_jsonl(path) or [])


def write_jsonl(path: Path, output_rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        BRANCH_PROXY_PATH,
        BRANCH_QUEUE_PATH,
        BRANCH_EFFECTIVE_N_PATH,
        BRANCH_IMPLEMENTATION_PATH,
        TARGET_STOP_CONTRACT_PATH,
        COST_FILL_GRID_PATH,
        PATH_CONTROL_GRID_PATH,
        PATH_CONTROL_STATUS_PATH,
        PATH_DESCRIPTOR_PATH,
        M1_REPLAY_SIGNATURE_PATH,
        FILL_BAR_STRESS_SIGNATURE_PATH,
        PARTIAL_REPAIR_SIGNATURE_PATH,
        TARGETSTOP_NA_REPAIR_PATH,
        RECOVERED_SIGNATURE_PATH,
        NEAR_MARKET_ENTRY_PATH,
        NEAR_OFFSET_PATH,
        FAR_AVOID_PATH,
        FAR_RETEST_PATH,
        EXACT_SPREAD_DELTA_PATH,
        EXACT_SPREAD_UNAVAILABLE_PATH,
        CONTROL_SCREEN_QUEUE_PATH,
        NEIGHBOR_PLACEBO_SURVIVOR_PATH,
    ]
    manifest_rows = []
    for path in paths:
        manifest_rows.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
            }
        )
    digest = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, digest


def compact_counter(counter: Counter[str]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter)}


def id_int(identifier: Any) -> int | None:
    if not identifier:
        return None
    try:
        return int(str(identifier).rsplit("-", 1)[-1])
    except ValueError:
        return None


def branch_key(row: dict[str, Any]) -> tuple[str, str, str]:
    entry = row.get("source_entry_variant") or row.get("entry_variant")
    target_stop = row.get("target_stop_contract_id")
    if target_stop is None:
        target = row.get("target_multiple", row.get("target_multiple_of_rolling_median_range", "NA"))
        stop = row.get("stop_multiple", row.get("stop_multiple_of_rolling_median_range", "NA"))
        target_stop = f"TARGETSTOP_{target}_{stop}"
    return (str(row.get("route_candidate_id")), str(entry), str(target_stop))


def natural_entry_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("route_candidate_id")), str(row.get("source_entry_variant") or row.get("entry_variant")))


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ratio_for(target_multiple: Any, stop_multiple: Any) -> float | None:
    target = to_float(target_multiple)
    stop = to_float(stop_multiple)
    if target is None or stop in (None, 0.0):
        return None
    return target / stop


def status_class(status: str) -> str:
    text = str(status or "").upper()
    if not text or text == "NONE":
        return "missing_status"
    if any(marker in text for marker in ["SOURCE_FAIL", "UNAVAILABLE", "SOURCE_RECHECK", "TICK_ABSENT", "MISSING", "ABSENT"]):
        return "source_stress"
    if any(marker in text for marker in ["AMBIG", "ORDER_UNRESOLVED", "INTERVAL_OPTIMISTIC", "SIDE_UNRESOLVED", "SAME_M15"]):
        return "ambiguous_ordering"
    if text.startswith("TARGET") or "TARGET_TOUCH_FIRST" in text or "TARGET_TOUCH_BEFORE_STOP" in text or "CARRIED_TARGET" in text:
        return "target_first_proxy"
    if text.startswith("STOP") or "STOP_TOUCH_FIRST" in text or "STOP_TOUCH_BEFORE_TARGET" in text:
        return "stop_first_proxy"
    if any(marker in text for marker in ["POST_SIGNAL_ENTRY_NOT_FILLED", "NOT_FILLED", "CONFIRMED_NOFILL", "NOFILL_SCOPE", "UNTOUCHED"]):
        return "no_fill_or_unfilled_proxy"
    if any(marker in text for marker in ["NO_TARGET_OR_STOP", "NO_TOUCH"]):
        return "filled_no_target_or_stop_proxy"
    if any(marker in text for marker in ["RECOVERED", "MARKET_PROXY_FILLED", "OFFSET_PROXY_FILLED"]):
        return "fillability_recovered_or_challenger_proxy"
    return "descriptor_proxy"


def interval_from_status(
    status: str,
    target_multiple: Any,
    stop_multiple: Any,
    close_units: Any = None,
    no_fill_zero: bool = True,
) -> tuple[float | None, float | None, str]:
    ratio = ratio_for(target_multiple, stop_multiple)
    cls = status_class(status)
    if cls == "target_first_proxy" and ratio is not None:
        return ratio, ratio, "target_stop_contract_target_first"
    if cls == "stop_first_proxy":
        return -1.0, -1.0, "target_stop_contract_stop_first"
    if cls == "ambiguous_ordering" and ratio is not None:
        return -1.0, ratio, "target_stop_contract_order_interval"
    if cls == "filled_no_target_or_stop_proxy":
        stop = to_float(stop_multiple)
        close = to_float(close_units)
        if stop not in (None, 0.0) and close is not None:
            proxy = close / stop
            return proxy, proxy, "lower_level_close_units_over_stop_multiple"
        return None, None, "no_target_stop_missing_close_units"
    if cls == "no_fill_or_unfilled_proxy" and no_fill_zero:
        return 0.0, 0.0, "no_fill_no_trade_zero_proxy"
    return None, None, f"{cls}_no_rstyle_mapping"


def blank_component() -> dict[str, Any]:
    return {
        "rows": 0,
        "status_counts": Counter(),
        "lower_values": [],
        "upper_values": [],
        "mid_values": [],
        "method_counts": Counter(),
        "event_ids": set(),
        "cost_fill_ids": set(),
        "source_stress_rows": 0,
        "no_fill_rows": 0,
        "target_first_rows": 0,
        "stop_first_rows": 0,
        "ambiguous_rows": 0,
        "no_resolution_rows": 0,
    }


def add_status_interval(
    component: dict[str, Any],
    status: str,
    target_multiple: Any,
    stop_multiple: Any,
    close_units: Any = None,
    event_id: Any = None,
    cost_fill_id: Any = None,
    count: int = 1,
) -> None:
    count = int(count or 0)
    if count <= 0:
        return
    component["rows"] += count
    component["status_counts"][str(status)] += count
    cls = status_class(status)
    if cls == "target_first_proxy":
        component["target_first_rows"] += count
    elif cls == "stop_first_proxy":
        component["stop_first_rows"] += count
    elif cls == "ambiguous_ordering":
        component["ambiguous_rows"] += count
    elif cls == "no_fill_or_unfilled_proxy":
        component["no_fill_rows"] += count
    elif cls in {"filled_no_target_or_stop_proxy", "descriptor_proxy"}:
        component["no_resolution_rows"] += count
    elif cls == "source_stress":
        component["source_stress_rows"] += count
    lower, upper, method = interval_from_status(status, target_multiple, stop_multiple, close_units=close_units)
    component["method_counts"][method] += count
    if lower is not None and upper is not None:
        midpoint = (lower + upper) / 2.0
        component["lower_values"].extend([lower] * count)
        component["upper_values"].extend([upper] * count)
        component["mid_values"].extend([midpoint] * count)
    if event_id is not None:
        component["event_ids"].add(str(event_id))
    if cost_fill_id is not None:
        component["cost_fill_ids"].add(str(cost_fill_id))


def merge_component(target: dict[str, Any], source: dict[str, Any]) -> None:
    target["rows"] += int(source["rows"])
    target["status_counts"].update(source["status_counts"])
    target["lower_values"].extend(source["lower_values"])
    target["upper_values"].extend(source["upper_values"])
    target["mid_values"].extend(source["mid_values"])
    target["method_counts"].update(source["method_counts"])
    target["event_ids"].update(source["event_ids"])
    target["cost_fill_ids"].update(source["cost_fill_ids"])
    for key in [
        "source_stress_rows",
        "no_fill_rows",
        "target_first_rows",
        "stop_first_rows",
        "ambiguous_rows",
        "no_resolution_rows",
    ]:
        target[key] += int(source[key])


def summarize_component(component: dict[str, Any]) -> dict[str, Any]:
    lower_values = component["lower_values"]
    upper_values = component["upper_values"]
    mid_values = component["mid_values"]
    return {
        "rows": int(component["rows"]),
        "rstyle_proxy_interval_rows": len(mid_values),
        "target_first_rows": int(component["target_first_rows"]),
        "stop_first_rows": int(component["stop_first_rows"]),
        "ambiguous_ordering_rows": int(component["ambiguous_rows"]),
        "no_fill_or_unfilled_rows": int(component["no_fill_rows"]),
        "filled_no_target_or_stop_rows": int(component["no_resolution_rows"]),
        "source_stress_rows": int(component["source_stress_rows"]),
        "unique_event_ids": len(component["event_ids"]),
        "unique_cost_fill_ids": len(component["cost_fill_ids"]),
        "rstyle_lower_mean": round(mean(lower_values), 6) if lower_values else None,
        "rstyle_upper_mean": round(mean(upper_values), 6) if upper_values else None,
        "rstyle_midpoint_mean": round(mean(mid_values), 6) if mid_values else None,
        "rstyle_lower_sum": round(sum(lower_values), 6) if lower_values else None,
        "rstyle_upper_sum": round(sum(upper_values), 6) if upper_values else None,
        "rstyle_midpoint_sum": round(sum(mid_values), 6) if mid_values else None,
        "status_counts": compact_counter(component["status_counts"]),
        "method_counts": compact_counter(component["method_counts"]),
    }


def component_store() -> defaultdict[tuple[str, str, str], defaultdict[str, dict[str, Any]]]:
    return defaultdict(lambda: defaultdict(blank_component))


def add_row_status_component(
    store: defaultdict[tuple[str, str, str], defaultdict[str, dict[str, Any]]],
    row: dict[str, Any],
    component_name: str,
    status_field: str,
    close_field: str | None = None,
) -> None:
    status = row.get(status_field)
    close_units = row.get(close_field) if close_field else None
    add_status_interval(
        store[branch_key(row)][component_name],
        str(status),
        row.get("target_multiple", row.get("target_multiple_of_rolling_median_range")),
        row.get("stop_multiple", row.get("stop_multiple_of_rolling_median_range")),
        close_units=close_units,
        event_id=row.get("event_id"),
        cost_fill_id=row.get("cost_fill_id"),
    )


def build_path_components(
    store: defaultdict[tuple[str, str, str], defaultdict[str, dict[str, Any]]],
    contracts_by_seq: dict[int, dict[str, Any]],
    contracts_by_id: dict[str, dict[str, Any]],
) -> None:
    cost_fill_by_seq: dict[int, dict[str, Any]] = {}
    for row in rows(COST_FILL_GRID_PATH):
        seq = id_int(row.get("cost_fill_id"))
        if seq is not None:
            cost_fill_by_seq[seq] = row
    status_by_cost_fill = {row.get("cost_fill_id"): row for row in rows(PATH_CONTROL_STATUS_PATH)}
    descriptor_by_cost_fill = {row.get("cost_fill_id"): row for row in rows(PATH_DESCRIPTOR_PATH)}

    for path_row in read_jsonl(PATH_CONTROL_GRID_PATH) or []:
        cost_fill = cost_fill_by_seq.get(int(path_row.get("cf") or 0))
        contract = contracts_by_seq.get(int(path_row.get("tc") or 0))
        if not cost_fill or not contract:
            continue
        key = (
            str(cost_fill.get("route_candidate_id")),
            str(cost_fill.get("entry_variant")),
            str(contract.get("target_stop_contract_id")),
        )
        cost_fill_id = cost_fill.get("cost_fill_id")
        status_row = status_by_cost_fill.get(cost_fill_id, {})
        descriptor_row = descriptor_by_cost_fill.get(cost_fill_id, {})
        close_units = (
            status_row.get("directional_close_units_after_cost")
            if status_row.get("directional_close_units_after_cost") is not None
            else descriptor_row.get("directional_close_units")
        )
        add_status_interval(
            store[key]["m15_path_control"],
            str(path_row.get("st")),
            contract.get("target_multiple_of_rolling_median_range"),
            contract.get("stop_multiple_of_rolling_median_range"),
            close_units=close_units,
            event_id=cost_fill.get("event_id"),
            cost_fill_id=cost_fill_id,
        )
    for row in rows(EXACT_SPREAD_DELTA_PATH):
        add_row_status_component(store, row, "exact_spread_recomputed_path", "exact_first_touch_status")
    for row in rows(EXACT_SPREAD_UNAVAILABLE_PATH):
        contract = contracts_by_id.get(str(row.get("target_stop_contract_id")), {})
        key = branch_key(row)
        # Preserve exact-unavailable as a low/high stress interval without pretending the exact spread is known.
        low = blank_component()
        high = blank_component()
        add_status_interval(
            low,
            str(row.get("low_spread_descriptor_status")),
            contract.get("target_multiple_of_rolling_median_range", row.get("target_multiple")),
            contract.get("stop_multiple_of_rolling_median_range", row.get("stop_multiple")),
            event_id=row.get("event_id"),
        )
        add_status_interval(
            high,
            str(row.get("high_spread_descriptor_status")),
            contract.get("target_multiple_of_rolling_median_range", row.get("target_multiple")),
            contract.get("stop_multiple_of_rolling_median_range", row.get("stop_multiple")),
            event_id=row.get("event_id"),
        )
        combined = store[key]["exact_spread_unavailable_low_high_stress"]
        merge_component(combined, low)
        merge_component(combined, high)


def build_auxiliary_components(
    store: defaultdict[tuple[str, str, str], defaultdict[str, dict[str, Any]]],
) -> None:
    for row in rows(M1_REPLAY_SIGNATURE_PATH):
        add_row_status_component(store, row, "m1_spread_adjusted_replay", "m1_first_touch_status")
    for row in rows(FILL_BAR_STRESS_SIGNATURE_PATH):
        key = branch_key(row)
        add_status_interval(
            store[key]["m1_fill_bar_conservative_stress"],
            str(row.get("conservative_first_touch_status")),
            row.get("target_multiple"),
            row.get("stop_multiple"),
            event_id=row.get("event_id"),
            cost_fill_id=row.get("cost_fill_id"),
        )
        add_status_interval(
            store[key]["m1_fill_bar_optimistic_stress"],
            str(row.get("optimistic_first_touch_status")),
            row.get("target_multiple"),
            row.get("stop_multiple"),
            event_id=row.get("event_id"),
            cost_fill_id=row.get("cost_fill_id"),
        )
    for row in rows(PARTIAL_REPAIR_SIGNATURE_PATH):
        add_row_status_component(store, row, "partial_source_recheck_repair", "m1_first_touch_status")
    for row in rows(RECOVERED_SIGNATURE_PATH):
        add_row_status_component(store, row, "recovered_unfilled_path", "recovered_first_touch_status")
    for row in rows(NEAR_MARKET_ENTRY_PATH):
        add_row_status_component(store, row, "near_miss_market_entry_challenger", "market_first_touch_status")
    for row in rows(NEAR_OFFSET_PATH):
        add_row_status_component(
            store,
            row,
            "near_miss_offset_challenger",
            "first_touch_status_offset_proxy",
            close_field="directional_close_units",
        )


def aggregate_branch_context() -> dict[str, Any]:
    context: dict[str, Any] = {
        "far_avoid_counts": defaultdict(Counter),
        "far_retest_counts": defaultdict(Counter),
        "control_screen": {},
        "neighbor_placebo": {},
        "effective_n": {},
        "implementation_tags": defaultdict(list),
        "targetstop_na_repair": {},
    }
    for row in rows(FAR_AVOID_PATH):
        context["far_avoid_counts"][branch_key(row)][str(row.get("avoid_filter_branch_status"))] += 1
    for row in rows(FAR_RETEST_PATH):
        context["far_retest_counts"][branch_key(row)][str(row.get("retest_redesign_branch_status"))] += 1
    for row in rows(CONTROL_SCREEN_QUEUE_PATH):
        context["control_screen"][str(row.get("route_candidate_id"))] = row
    for row in rows(NEIGHBOR_PLACEBO_SURVIVOR_PATH):
        context["neighbor_placebo"][str(row.get("route_candidate_id"))] = row
    for row in rows(BRANCH_EFFECTIVE_N_PATH):
        context["effective_n"][str(row.get("branch_queue_id"))] = row
    for row in rows(BRANCH_IMPLEMENTATION_PATH):
        context["implementation_tags"][str(row.get("branch_queue_id"))].append(
            {
                "implementation_tag": row.get("implementation_tag"),
                "mechanical_next_step": row.get("mechanical_next_step"),
            }
        )
    for row in rows(TARGETSTOP_NA_REPAIR_PATH):
        context["targetstop_na_repair"][str(row.get("branch_queue_id"))] = row
    return context


def classify_source_confidence(branch_row: dict[str, Any], combined: dict[str, Any], context: dict[str, Any]) -> str:
    if branch_row.get("path_scope_bucket") == "REPAIR_ENTRY_ONLY_NO_TARGET_STOP_CONTRACT":
        return "ENTRY_PROVENANCE_ONLY_BOUND_BY_SIGNATURE_SCOPE"
    source_bucket = str(branch_row.get("source_confidence_bucket") or "")
    if "EXACT_SOURCE_SUPPORTED" in source_bucket and combined["source_stress_rows"] == 0:
        return "EXACT_SOURCE_SUPPORTED_NO_COMPONENT_SOURCE_STRESS"
    if combined["source_stress_rows"] > 0 or "STRESS" in source_bucket or "ABSENT" in source_bucket:
        return "SOURCE_STRESS_OR_PROXY_PRESENT"
    return "SOURCE_CONTEXT_MIXED_OR_UNSPECIFIED"


def classify_ambiguity(branch_row: dict[str, Any], combined: dict[str, Any]) -> str:
    interval_rows = len(combined["mid_values"])
    if interval_rows == 0:
        return "NO_RSTYLE_INTERVAL_ROWS"
    ambiguous_share = combined["ambiguous_rows"] / max(1, combined["rows"])
    if "HIGH" in str(branch_row.get("ambiguity_bucket")) or ambiguous_share >= 0.20:
        return "HIGH_ORDERING_AMBIGUITY"
    if combined["ambiguous_rows"] > 0:
        return "SOME_ORDERING_AMBIGUITY"
    return "NO_ORDERING_AMBIGUITY_RECORDED"


def classify_target_stop_result(combined_summary: dict[str, Any]) -> str:
    if int(combined_summary.get("rows") or 0) == 0:
        return "NO_TARGET_STOP_RESULT_ENTRY_PROVENANCE_ONLY"
    target = combined_summary["target_first_rows"]
    stop = combined_summary["stop_first_rows"]
    ambiguous = combined_summary["ambiguous_ordering_rows"]
    no_fill = combined_summary["no_fill_or_unfilled_rows"]
    no_resolution = combined_summary["filled_no_target_or_stop_rows"]
    if target > stop and target >= ambiguous + no_fill:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if stop > target and stop >= ambiguous:
        return "STOP_FIRST_PROXY_DOMINANT"
    if ambiguous >= max(target, stop, no_resolution):
        return "ORDERING_AMBIGUITY_DOMINANT"
    if no_fill >= max(target, stop, ambiguous):
        return "NO_FILL_OR_UNFILLED_DOMINANT"
    if no_resolution > 0:
        return "NO_TARGET_STOP_TOUCH_DESCRIPTOR_DOMINANT"
    return "MIXED_OR_UNDERPOWERED_TARGET_STOP_RESULT"


def branch_result_class(midpoint: float | None, lower: float | None, upper: float | None, target_stop_result: str) -> str:
    if midpoint is None:
        return "NO_RSTYLE_PROXY_INTERVAL_AVAILABLE"
    if lower is not None and upper is not None and lower < 0 < upper:
        return "AMBIGUOUS_INTERVAL_STRADDLES_ZERO"
    if midpoint > 0:
        return "POSITIVE_RSTYLE_PROXY_MIDPOINT"
    if midpoint < 0:
        return "NEGATIVE_RSTYLE_PROXY_MIDPOINT"
    if "NO_FILL" in target_stop_result:
        return "NO_TRADE_ZERO_PROXY"
    return "NEUTRAL_RSTYLE_PROXY_MIDPOINT"


def exact_failure_success_cause(
    branch_row: dict[str, Any],
    combined_summary: dict[str, Any],
    source_status: str,
    ambiguity_status: str,
    context: dict[str, Any],
) -> tuple[str, str, list[str]]:
    tags = set(branch_row.get("system_implication_tags", []))
    fill_bucket = str(branch_row.get("fillability_bucket"))
    cost_bucket = str(branch_row.get("cost_robustness_bucket"))
    causes: list[str] = []
    if combined_summary["rstyle_midpoint_mean"] is not None and combined_summary["rstyle_midpoint_mean"] > 0:
        success = "TARGET_OR_CLOSE_PROXY_POSITIVE_AFTER_AVAILABLE_PATHS"
    elif combined_summary["target_first_rows"] > combined_summary["stop_first_rows"]:
        success = "TARGET_FIRST_COUNT_POSITIVE_BUT_INTERVAL_NOT_CLEAN"
    else:
        success = "NO_SUCCESS_CAUSE_DOMINANT"
    if combined_summary["stop_first_rows"] > combined_summary["target_first_rows"]:
        causes.append("STOP_FIRST_PATH_ORDERING_DOMINATES")
    if "NOFILL" in fill_bucket or "FILLABILITY" in fill_bucket:
        causes.append("LIMIT_ENTRY_FILLABILITY_FRICTION")
    if combined_summary["no_fill_or_unfilled_rows"] > 0:
        causes.append("NO_FILL_OR_UNFILLED_ROWS_PRESENT")
    if "SOURCE_STRESS" in source_status:
        causes.append("SOURCE_STRESS_OR_PROXY_SOURCE_LIMIT")
    if "HIGH" in ambiguity_status:
        causes.append("HIGH_TARGET_STOP_ORDERING_AMBIGUITY")
    if "SPREAD" in cost_bucket or "EXACT" in cost_bucket:
        causes.append(f"COST_SENSITIVITY_{cost_bucket}")
    if "NEAR_MISS_ENTRY_CHALLENGER_AVAILABLE" in fill_bucket or "ENTRY_GEOMETRY_CHALLENGER" in tags:
        causes.append("ENTRY_GEOMETRY_CHALLENGER_AVAILABLE")
    if "RETEST_REDESIGN_QUEUE" in tags:
        causes.append("RETEST_REDESIGN_OR_AVOID_FILTER_QUEUE")
    if not causes:
        causes.append("MIXED_DESCRIPTOR_NO_SINGLE_FAILURE_CAUSE")
    return success, "__".join(causes), sorted(causes)


def build_concentration_rows(branch_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    group_defs = {
        "symbol": lambda row: row.get("symbol"),
        "route_candidate_id": lambda row: row.get("route_candidate_id"),
        "route_session": lambda row: row.get("route_session"),
        "entry_variant": lambda row: row.get("entry_variant"),
        "target_stop_contract_id": lambda row: row.get("target_stop_contract_id"),
        "source_confidence_status": lambda row: row.get("source_confidence_status"),
        "ambiguity_status": lambda row: row.get("ambiguity_status"),
        "target_stop_result": lambda row: row.get("target_stop_result"),
        "branch_result_class": lambda row: row.get("branch_result_class"),
        "exact_failure_cause": lambda row: row.get("exact_failure_cause"),
    }
    output_rows: list[dict[str, Any]] = []
    sequence = 0
    total = len(branch_rows)
    for group_type, getter in group_defs.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in branch_rows:
            groups[str(getter(row))].append(row)
        for group_key, members in sorted(groups.items()):
            sequence += 1
            mids = [
                row.get("rstyle_proxy_all_components", {}).get("rstyle_midpoint_mean")
                for row in members
                if row.get("rstyle_proxy_all_components", {}).get("rstyle_midpoint_mean") is not None
            ]
            output_rows.append(
                {
                    "concentration_id": f"OHLC-GTOS-BRANCH-RSTYLE-CONC-{sequence:05d}",
                    "generated_utc": generated_at,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CONCENTRATION",
                    "claim_boundary": CLAIM_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                    "group_type": group_type,
                    "group_key": group_key,
                    "branch_count": len(members),
                    "branch_share": round(len(members) / total, 9) if total else None,
                    "unique_route_candidate_count": len({row.get("route_candidate_id") for row in members}),
                    "unique_event_proxy_count_sum": sum(
                        int(row.get("effective_n_fields", {}).get("unique_event_or_route_ids", 0)) for row in members
                    ),
                    "rstyle_midpoint_mean": round(mean(mids), 6) if mids else None,
                    "positive_midpoint_rows": sum(1 for value in mids if value > 0),
                    "negative_midpoint_rows": sum(1 for value in mids if value < 0),
                    "neutral_midpoint_rows": sum(1 for value in mids if value == 0),
                }
            )
    return output_rows


def build_control_delta(
    branch_row: dict[str, Any],
    route_peer_rows: list[dict[str, Any]],
    symbol_session_peer_rows: list[dict[str, Any]],
    context: dict[str, Any],
    generated_at: str,
    sequence: int,
) -> dict[str, Any]:
    own_mid = branch_row.get("rstyle_proxy_all_components", {}).get("rstyle_midpoint_mean")
    route_peer_mids = [
        row.get("rstyle_proxy_all_components", {}).get("rstyle_midpoint_mean")
        for row in route_peer_rows
        if row.get("branch_queue_id") != branch_row.get("branch_queue_id")
        and row.get("rstyle_proxy_all_components", {}).get("rstyle_midpoint_mean") is not None
    ]
    symbol_session_mids = [
        row.get("rstyle_proxy_all_components", {}).get("rstyle_midpoint_mean")
        for row in symbol_session_peer_rows
        if row.get("branch_queue_id") != branch_row.get("branch_queue_id")
        and row.get("rstyle_proxy_all_components", {}).get("rstyle_midpoint_mean") is not None
    ]
    route_peer_mean = mean(route_peer_mids) if route_peer_mids and own_mid is not None else None
    symbol_session_mean = mean(symbol_session_mids) if symbol_session_mids and own_mid is not None else None
    control_row = context["control_screen"].get(str(branch_row.get("route_candidate_id")), {})
    neighbor_row = context["neighbor_placebo"].get(str(branch_row.get("route_candidate_id")), {})
    neighbor_deltas = neighbor_row.get("deltas_vs_controls", {}) if neighbor_row else {}
    route_delta = round(own_mid - route_peer_mean, 6) if own_mid is not None and route_peer_mean is not None else None
    symbol_session_delta = (
        round(own_mid - symbol_session_mean, 6)
        if own_mid is not None and symbol_session_mean is not None
        else None
    )
    if route_delta is not None and route_delta > 0:
        status = "BRANCH_PROXY_ABOVE_SAME_ROUTE_PEER_MEAN"
    elif route_delta is not None and route_delta < 0:
        status = "BRANCH_PROXY_BELOW_SAME_ROUTE_PEER_MEAN"
    elif own_mid is None:
        status = "BRANCH_PROXY_DELTA_NOT_COMPUTABLE_NO_RSTYLE_INTERVAL"
    else:
        status = "BRANCH_PROXY_DELTA_NEUTRAL_OR_SINGLETON"
    if control_row:
        status += "__CONTROL_SCREEN_ROUTE_JOINED"
    else:
        status += "__CONTROL_SCREEN_ROUTE_NOT_JOINED"
    if neighbor_row:
        status += "__NEIGHBOR_PLACEBO_JOINED"
    else:
        status += "__NEIGHBOR_PLACEBO_NOT_JOINED"
    return {
        "control_delta_id": f"OHLC-GTOS-BRANCH-RSTYLE-CONTROL-DELTA-{sequence:05d}",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CONTROL_DELTA",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "branch_queue_id": branch_row.get("branch_queue_id"),
        "branch_proxy_score_id": branch_row.get("branch_proxy_score_id"),
        "route_candidate_id": branch_row.get("route_candidate_id"),
        "symbol": branch_row.get("symbol"),
        "side": branch_row.get("side"),
        "route_session": branch_row.get("route_session"),
        "entry_variant": branch_row.get("entry_variant"),
        "target_stop_contract_id": branch_row.get("target_stop_contract_id"),
        "branch_rstyle_midpoint_mean": own_mid,
        "same_route_peer_count": len(route_peer_mids),
        "same_route_peer_midpoint_mean": round(route_peer_mean, 6) if route_peer_mean is not None else None,
        "same_route_peer_delta": route_delta,
        "same_symbol_session_side_targetstop_peer_count": len(symbol_session_mids),
        "same_symbol_session_side_targetstop_peer_midpoint_mean": (
            round(symbol_session_mean, 6) if symbol_session_mean is not None else None
        ),
        "same_symbol_session_side_targetstop_delta": symbol_session_delta,
        "control_screen_delta_mean_directional_close_units": control_row.get("delta_mean_directional_close_units"),
        "control_screen_delta_directional_positive_share": control_row.get("delta_directional_positive_share"),
        "control_screen_delta_total_excursion_units": control_row.get("delta_total_excursion_units"),
        "neighbor_directional_close_vs_minus_1": neighbor_deltas.get("directional_close_vs_neighbor_minus_1"),
        "neighbor_directional_close_vs_plus_1": neighbor_deltas.get("directional_close_vs_neighbor_plus_1"),
        "neighbor_directional_close_vs_permuted": neighbor_deltas.get("directional_close_vs_permuted"),
        "pass_control_delta_status": status,
        "missing_exact_delta_reason": (
            "Exact strategy R/PnL control is unavailable because this layer has no broker realized trade geometry; "
            "the best current delta is branch R-style proxy versus same-route/symbol-session peers plus upstream "
            "directional control and neighbor/placebo deltas."
        ),
    }


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    artifact_paths = [
        RESULT_PATH,
        BRANCH_OUTCOME_PATH,
        CONTROL_DELTA_PATH,
        CAUSE_PATH,
        CONCENTRATION_PATH,
        BUCKET_PATH,
        QUESTION_PATH,
        SUMMARY_PATH,
        Path(__file__).resolve(),
    ]
    artifact_names = {path.name for path in artifact_paths}
    manifest["outputs"] = [row for row in manifest.get("outputs", []) if row.get("artifact") not in artifact_names]
    for path, artifact_type in [
        (RESULT_PATH, "result"),
        (BRANCH_OUTCOME_PATH, "branch_outcome_ledger"),
        (CONTROL_DELTA_PATH, "control_delta_ledger"),
        (CAUSE_PATH, "cause_ledger"),
        (CONCENTRATION_PATH, "concentration_ledger"),
        (BUCKET_PATH, "bucket_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SUMMARY_PATH, "summary"),
    ]:
        manifest["outputs"].append(
            {
                "artifact": path.name,
                "category": "historical_ohlc_gtos_replay_branch_rstyle_proxy_outcome_layer",
                "artifact_type": artifact_type,
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    existing_paths = {str(path.relative_to(REPO)).replace("\\", "/") for path in artifact_paths}
    manifest["artifacts"] = [
        row for row in manifest.get("artifacts", []) if row.get("path") not in existing_paths
    ]
    for path, artifact_type in [
        (Path(__file__).resolve(), "branch_rstyle_proxy_outcome_layer_builder"),
        (RESULT_PATH, "branch_rstyle_proxy_outcome_layer_result"),
        (BRANCH_OUTCOME_PATH, "branch_rstyle_proxy_outcome_branch_ledger"),
        (CONTROL_DELTA_PATH, "branch_rstyle_proxy_outcome_control_delta_ledger"),
        (CAUSE_PATH, "branch_rstyle_proxy_outcome_cause_ledger"),
        (CONCENTRATION_PATH, "branch_rstyle_proxy_outcome_concentration_ledger"),
        (BUCKET_PATH, "branch_rstyle_proxy_outcome_bucket_ledger"),
        (QUESTION_PATH, "branch_rstyle_proxy_outcome_question_ledger"),
        (SUMMARY_PATH, "branch_rstyle_proxy_outcome_summary"),
    ]:
        manifest["artifacts"].append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "status": "created",
                "type": artifact_type,
            }
        )
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "historical_ohlc_gtos_replay_branch_rstyle_proxy_outcome_layer",
        "artifact": RESULT_PATH.name,
        "counts": result["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_subagent_integration(generated_at: str) -> None:
    if not SUBAGENT_LEDGER_PATH.exists():
        return
    rows = [
        {
            "timestamp_utc": generated_at,
            "event_type": "subagent_return_integrated",
            "agent_id": "019e2f48-e38c-7e41-8fbc-b516b22815d1",
            "agent_nickname": "Banach",
            "integration_route": "historical_ohlc_gtos_replay_branch_rstyle_proxy_outcome_layer",
            "integration_status": "USED_SCHEMA_MAP_AND_TARGETSTOP_NA_TRAP_IN_BUILDER",
            "not_completion": True,
        },
        {
            "timestamp_utc": generated_at,
            "event_type": "subagent_return_integrated",
            "agent_id": "019e2f65-bc19-7090-9d7d-451b851e295e",
            "agent_nickname": "Franklin",
            "integration_route": "historical_ohlc_gtos_replay_branch_rstyle_proxy_outcome_layer",
            "integration_status": "USED_CANONICAL_JOIN_MAP_RSTYLE_PROXY_AND_SOURCE_GAP_WARNINGS_IN_BUILDER",
            "not_completion": True,
        },
    ]
    with SUBAGENT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    counts = result["counts"]
    lines = [
        "# Historical OHLC GTOS Branch R-Style Proxy Outcome Layer",
        "",
        f"Generated UTC: {result['generated_utc']}",
        "",
        "## Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
        f"- Branch outcome rows: {counts['branch_outcome_rows']}",
        f"- Control delta rows: {counts['control_delta_rows']}",
        f"- Cause rows: {counts['cause_rows']}",
        f"- Concentration rows: {counts['concentration_rows']}",
        f"- Bucket rows: {counts['bucket_rows']}",
        f"- Question rows: {counts['question_rows']}",
        "",
        "## Outcome Layer",
        "",
        "Every branch row is preserved. Exact broker R/PnL is not available in this evidence class, so the layer uses target/stop contract order, M15/M1 first-touch statuses, no-fill zero-trade proxies, and close-units-over-stop lower-level proxies where target/stop was not touched.",
        "",
        "Target/stop NA rows are not dropped: they remain entry-provenance rows and are bound to the existing partial/source-recheck signature-scope contracts through the target/stop NA repair packet.",
        "",
        "## Bucket Distributions",
        "",
    ]
    for name, counter in result["bucket_distributions"].items():
        lines.append(f"- {name}: {json.dumps(counter, sort_keys=True)}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()

    contracts = rows(TARGET_STOP_CONTRACT_PATH)
    contracts_by_seq = {index + 1: row for index, row in enumerate(contracts)}
    contracts_by_id = {str(row.get("target_stop_contract_id")): row for row in contracts}

    store = component_store()
    build_path_components(store, contracts_by_seq, contracts_by_id)
    build_auxiliary_components(store)
    context = aggregate_branch_context()

    branch_proxy_rows = rows(BRANCH_PROXY_PATH)
    branch_queue_rows = rows(BRANCH_QUEUE_PATH)
    queue_by_id = {str(row.get("branch_queue_id")): row for row in branch_queue_rows}
    branch_group_counts = {
        "symbol": Counter(str(row.get("symbol")) for row in branch_proxy_rows),
        "route_candidate_id": Counter(str(row.get("route_candidate_id")) for row in branch_proxy_rows),
        "route_session": Counter(str(row.get("route_session")) for row in branch_proxy_rows),
        "entry_variant": Counter(str(row.get("entry_variant")) for row in branch_proxy_rows),
        "target_stop_contract_id": Counter(str(row.get("target_stop_contract_id")) for row in branch_proxy_rows),
    }

    branch_rows: list[dict[str, Any]] = []
    cause_rows: list[dict[str, Any]] = []
    bucket_counter: dict[str, Counter[str]] = defaultdict(Counter)

    for sequence, branch in enumerate(branch_proxy_rows, 1):
        bkey = branch_key(branch)
        components = store.get(bkey, {})
        combined = blank_component()
        component_summaries: dict[str, Any] = {}
        for component_name in sorted(components):
            merge_component(combined, components[component_name])
            component_summaries[component_name] = summarize_component(components[component_name])

        # Add no-fill redesign branches as fillability/context rows without coercing them into target/stop outcomes.
        far_avoid_counts = context["far_avoid_counts"].get(bkey, Counter())
        far_retest_counts = context["far_retest_counts"].get(bkey, Counter())
        targetstop_na = context["targetstop_na_repair"].get(str(branch.get("branch_queue_id")), {})
        combined_summary = summarize_component(combined)
        source_status = classify_source_confidence(branch, combined, context)
        ambiguity_status = classify_ambiguity(branch, combined)
        target_stop_result = classify_target_stop_result(combined_summary)
        result_class = branch_result_class(
            combined_summary["rstyle_midpoint_mean"],
            combined_summary["rstyle_lower_mean"],
            combined_summary["rstyle_upper_mean"],
            target_stop_result,
        )
        success_cause, failure_cause, cause_list = exact_failure_success_cause(
            branch,
            combined_summary,
            source_status,
            ambiguity_status,
            context,
        )
        effective_n = context["effective_n"].get(str(branch.get("branch_queue_id")), {})
        effective_fields = dict(branch.get("effective_n_fields") or {})
        for key in [
            "material_joined_rows",
            "unique_event_or_route_ids",
            "unique_cost_fill_ids",
            "duplicate_inflation_ratio_material_rows_over_event_ids",
            "unique_execution_friction_signature_ids",
            "unique_source_requirement_ids",
        ]:
            if key in effective_n:
                effective_fields[key] = effective_n[key]
        concentration_summary = {
            group_type: {
                "group_key": str(branch.get(group_type)),
                "branch_count": branch_group_counts[group_type][str(branch.get(group_type))],
                "branch_share": round(
                    branch_group_counts[group_type][str(branch.get(group_type))] / max(1, len(branch_proxy_rows)),
                    9,
                ),
            }
            for group_type in branch_group_counts
        }
        row = {
            "branch_rstyle_proxy_outcome_id": f"OHLC-GTOS-BRANCH-RSTYLE-OUTCOME-{sequence:05d}",
            "generated_utc": generated_at,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
            "branch_queue_id": branch.get("branch_queue_id"),
            "branch_proxy_score_id": branch.get("branch_proxy_score_id"),
            "family_synthesis_id": branch.get("family_synthesis_id"),
            "route_candidate_id": branch.get("route_candidate_id"),
            "symbol": branch.get("symbol"),
            "side": branch.get("side"),
            "route_session": branch.get("route_session"),
            "entry_variant": branch.get("entry_variant"),
            "target_stop_contract_id": branch.get("target_stop_contract_id"),
            "target_multiple": branch.get("target_multiple"),
            "stop_multiple": branch.get("stop_multiple"),
            "target_stop_reward_to_risk_ratio": ratio_for(branch.get("target_multiple"), branch.get("stop_multiple")),
            "branch_queue_status": branch.get("branch_queue_status"),
            "path_scope_bucket": branch.get("path_scope_bucket"),
            "fillability_bucket": branch.get("fillability_bucket"),
            "cost_robustness_bucket": branch.get("cost_robustness_bucket"),
            "source_confidence_bucket": branch.get("source_confidence_bucket"),
            "ambiguity_bucket": branch.get("ambiguity_bucket"),
            "source_confidence_status": source_status,
            "ambiguity_status": ambiguity_status,
            "target_stop_result": target_stop_result,
            "branch_result_class": result_class,
            "exact_success_cause": success_cause,
            "exact_failure_cause": failure_cause,
            "cause_tags": cause_list,
            "rstyle_proxy_all_components": combined_summary,
            "rstyle_proxy_component_breakdown": component_summaries,
            "expectancy_style_proxy": {
                "method": "mean_midpoint_of_available_rstyle_proxy_intervals_not_broker_expectancy",
                "midpoint_mean": combined_summary["rstyle_midpoint_mean"],
                "lower_mean": combined_summary["rstyle_lower_mean"],
                "upper_mean": combined_summary["rstyle_upper_mean"],
                "interval_rows": combined_summary["rstyle_proxy_interval_rows"],
                "exact_missing_reason": (
                    "No broker realized trade PnL, true executed risk, slippage, partial fills, or order ticket geometry "
                    "is present in this branch evidence class; this is a mechanical target/stop and path proxy."
                ),
            },
            "target_stop_result_counts": {
                "target_first_rows": combined_summary["target_first_rows"],
                "stop_first_rows": combined_summary["stop_first_rows"],
                "ambiguous_ordering_rows": combined_summary["ambiguous_ordering_rows"],
                "no_fill_or_unfilled_rows": combined_summary["no_fill_or_unfilled_rows"],
                "filled_no_target_or_stop_rows": combined_summary["filled_no_target_or_stop_rows"],
                "source_stress_rows": combined_summary["source_stress_rows"],
            },
            "no_fill_impact_proxy": {
                "no_fill_rows": combined_summary["no_fill_or_unfilled_rows"],
                "far_avoid_branch_counts": compact_counter(far_avoid_counts),
                "far_retest_redesign_counts": compact_counter(far_retest_counts),
                "interpretation": "No-fill rows are scored as no-trade zero proxy where execution did not occur; near/far/retest redesign ledgers carry entry-geometry and fillability alternatives.",
            },
            "targetstop_na_binding": targetstop_na if targetstop_na else None,
            "cost_sensitivity": {
                "cost_robustness_bucket": branch.get("cost_robustness_bucket"),
                "exact_spread_recomputed_component": component_summaries.get("exact_spread_recomputed_path"),
                "exact_spread_unavailable_component": component_summaries.get("exact_spread_unavailable_low_high_stress"),
                "branch_status_cost_counters": (branch.get("status_counters") or {}).get("path_m15_cost_model", {}),
            },
            "pass_control_delta_status": "COMPUTED_IN_CONTROL_DELTA_LEDGER",
            "effective_n_fields": effective_fields,
            "concentration_summary": concentration_summary,
            "source_manifest_hash": manifest_hash,
            "branch_actions": branch.get("branch_actions", []),
            "system_implication_tags": branch.get("system_implication_tags", []),
            "implementation_implications": context["implementation_tags"].get(str(branch.get("branch_queue_id")), []),
            "queue_source_row_present": str(branch.get("branch_queue_id")) in queue_by_id,
            "missing_exact_geometry_reason": (
                "Exact R/PnL cannot be computed from this packet because it lacks broker-realized fills, account history, "
                "true executed stop distance, slippage, partial exits, and ticket lifecycle. The layer computes the strongest "
                "available lower-level target/stop/path proxy and records source/ordering/fillability limits per branch."
            ),
        }
        branch_rows.append(row)
        bucket_counter["source_confidence_status"][source_status] += 1
        bucket_counter["ambiguity_status"][ambiguity_status] += 1
        bucket_counter["target_stop_result"][target_stop_result] += 1
        bucket_counter["branch_result_class"][result_class] += 1
        bucket_counter["exact_failure_cause"][failure_cause] += 1
        bucket_counter["fillability_bucket"][str(branch.get("fillability_bucket"))] += 1
        bucket_counter["cost_robustness_bucket"][str(branch.get("cost_robustness_bucket"))] += 1
        cause_rows.append(
            {
                "cause_id": f"OHLC-GTOS-BRANCH-RSTYLE-CAUSE-{sequence:05d}",
                "generated_utc": generated_at,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CAUSE",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "branch_queue_id": branch.get("branch_queue_id"),
                "route_candidate_id": branch.get("route_candidate_id"),
                "symbol": branch.get("symbol"),
                "side": branch.get("side"),
                "route_session": branch.get("route_session"),
                "entry_variant": branch.get("entry_variant"),
                "target_stop_contract_id": branch.get("target_stop_contract_id"),
                "exact_success_cause": success_cause,
                "exact_failure_cause": failure_cause,
                "cause_tags": cause_list,
                "target_stop_result": target_stop_result,
                "branch_result_class": result_class,
                "source_confidence_status": source_status,
                "ambiguity_status": ambiguity_status,
                "implementation_implication_count": len(context["implementation_tags"].get(str(branch.get("branch_queue_id")), [])),
            }
        )

    by_route: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_symbol_session_side_targetstop: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in branch_rows:
        by_route[str(row.get("route_candidate_id"))].append(row)
        by_symbol_session_side_targetstop[
            (
                str(row.get("symbol")),
                str(row.get("route_session")),
                str(row.get("side")),
                str(row.get("target_stop_contract_id")),
            )
        ].append(row)

    control_rows = []
    for sequence, row in enumerate(branch_rows, 1):
        peer_key = (
            str(row.get("symbol")),
            str(row.get("route_session")),
            str(row.get("side")),
            str(row.get("target_stop_contract_id")),
        )
        control_rows.append(
            build_control_delta(
                row,
                by_route[str(row.get("route_candidate_id"))],
                by_symbol_session_side_targetstop[peer_key],
                context,
                generated_at,
                sequence,
            )
        )

    concentration_rows = build_concentration_rows(branch_rows, generated_at)
    bucket_rows = []
    bucket_sequence = 0
    for bucket_name, counter in sorted(bucket_counter.items()):
        for bucket_value, count in sorted(counter.items()):
            bucket_sequence += 1
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-BRANCH-RSTYLE-BUCKET-{bucket_sequence:05d}",
                    "generated_utc": generated_at,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BUCKET",
                    "claim_boundary": CLAIM_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                    "bucket_name": bucket_name,
                    "bucket_value": bucket_value,
                    "branch_count": int(count),
                }
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-BRANCH-RSTYLE-QUESTION-00001",
            "generated_utc": generated_at,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
            "question": "Which branches remain positive after same-route and same-symbol/session/targetstop peer deltas instead of raw proxy midpoint only?",
            "same_resource_next_action": "Use the full control delta ledger; split positive/negative peer deltas by cause, cost bucket, source confidence, and ambiguity bucket without top-N truncation.",
            "branch_count_opened": len(branch_rows),
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-RSTYLE-QUESTION-00002",
            "generated_utc": generated_at,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
            "question": "Which negative branches are true adverse path versus no-fill execution friction versus source/ordering ambiguity?",
            "same_resource_next_action": "Consume the full cause ledger into avoid-filter, retest-redesign, exact-spread/source-repair, and ordering-collapse branch-local design packets.",
            "branch_count_opened": len(branch_rows),
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-RSTYLE-QUESTION-00003",
            "generated_utc": generated_at,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
            "question": "Which R-style proxy intervals still straddle zero only because target/stop ordering is same-bar or M1 fill-bar ambiguous?",
            "same_resource_next_action": "Route those rows into M1/tick ordering collapse where source exists; otherwise preserve conservative/optimistic interval and source requirement.",
            "branch_count_opened": sum(1 for row in branch_rows if row.get("branch_result_class") == "AMBIGUOUS_INTERVAL_STRADDLES_ZERO"),
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-RSTYLE-QUESTION-00004",
            "generated_utc": generated_at,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
            "question": "Can the TARGETSTOP_NA_NA entry-provenance rows be transformed into contract-level branch rows without losing denominator integrity?",
            "same_resource_next_action": "Use the binding repair candidate and contract summary ledgers to explode those entries only in a separate explicitly marked signature-scope design, not by mutating original branch IDs.",
            "branch_count_opened": sum(1 for row in branch_rows if row.get("targetstop_na_binding")),
        },
    ]

    result = {
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "counts": {
            "branch_proxy_input_rows": len(branch_proxy_rows),
            "branch_queue_input_rows": len(branch_queue_rows),
            "branch_outcome_rows": len(branch_rows),
            "control_delta_rows": len(control_rows),
            "cause_rows": len(cause_rows),
            "concentration_rows": len(concentration_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(manifest_rows),
            "targetstop_na_bound_rows": sum(1 for row in branch_rows if row.get("targetstop_na_binding")),
        },
        "bucket_distributions": {name: compact_counter(counter) for name, counter in sorted(bucket_counter.items())},
        "rstyle_component_row_sums": {
            "all_component_rows": sum(row["rstyle_proxy_all_components"]["rows"] for row in branch_rows),
            "all_component_interval_rows": sum(
                row["rstyle_proxy_all_components"]["rstyle_proxy_interval_rows"] for row in branch_rows
            ),
            "m15_component_rows": sum(
                row["rstyle_proxy_component_breakdown"].get("m15_path_control", {}).get("rows", 0)
                for row in branch_rows
            ),
            "m1_component_rows": sum(
                row["rstyle_proxy_component_breakdown"].get("m1_spread_adjusted_replay", {}).get("rows", 0)
                for row in branch_rows
            ),
            "near_challenger_component_rows": sum(
                row["rstyle_proxy_component_breakdown"].get("near_miss_market_entry_challenger", {}).get("rows", 0)
                + row["rstyle_proxy_component_breakdown"].get("near_miss_offset_challenger", {}).get("rows", 0)
                for row in branch_rows
            ),
        },
    }

    write_jsonl(BRANCH_OUTCOME_PATH, branch_rows)
    write_jsonl(CONTROL_DELTA_PATH, control_rows)
    write_jsonl(CAUSE_PATH, cause_rows)
    write_jsonl(CONCENTRATION_PATH, concentration_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    append_subagent_integration(generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
