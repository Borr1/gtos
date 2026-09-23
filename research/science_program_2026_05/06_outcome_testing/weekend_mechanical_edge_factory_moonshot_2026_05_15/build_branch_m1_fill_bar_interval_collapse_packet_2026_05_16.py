#!/usr/bin/env python3
"""Materialize M1 fill-bar interval collapse/proxy support for branch replay."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

REPLAY_EXEC_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_PACKET_RESULT_2026-05-16.json"
REPLAY_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_BRANCH_LEDGER_2026-05-16.jsonl"
REPLAY_SOURCE_ORDERING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_SOURCE_ORDERING_LEDGER_2026-05-16.jsonl"
M1_INTERVAL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_STRESS_INTERVAL_LEDGER_2026-05-16.jsonl"
M1_STRESS_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_SIGNATURE_LEDGER_2026-05-16.jsonl"
M1_STRESS_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_FAMILY_LEDGER_2026-05-16.jsonl"
MATRIX_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_BRANCH_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_RESULT_2026-05-16.json"
BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
SIGNATURE_SUPPORT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_SIGNATURE_SUPPORT_LEDGER_2026-05-16.jsonl"
FAMILY_SUPPORT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_FAMILY_SUPPORT_LEDGER_2026-05-16.jsonl"
PROXY_VARIANT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_PROXY_VARIANT_LEDGER_2026-05-16.jsonl"
REQUIREMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_REQUIREMENT_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch M1 fill-bar interval collapse packet only. It preserves all M1 "
    "fill-bar ordering-stress support rows, scores the 110 active branch rows "
    "with branch aggregate and M1 support-component proxy bounds, and records "
    "remaining source/tick-ordering ambiguity without broker R/PnL, realized "
    "expectancy, win-rate, validation, live-readiness, promotion, or live behavior change claims."
)
PROXY_VARIANTS = (
    "BRANCH_AGGREGATE_CONSERVATIVE_BOUND",
    "BRANCH_AGGREGATE_OPTIMISTIC_BOUND",
    "BRANCH_AGGREGATE_MIDPOINT",
    "M1_SUPPORT_CONSERVATIVE_SCALAR_MEAN",
    "M1_SUPPORT_OPTIMISTIC_SCALAR_MEAN",
    "M1_SUPPORT_MIDPOINT_SCALAR_MEAN",
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
    return [row for row in (read_jsonl(path) or []) if not row.get("_parse_error")]


def write_jsonl(path: Path, output_rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def norm(value: Any) -> str:
    if value is None:
        return "None"
    try:
        return f"{float(value):.10g}"
    except (TypeError, ValueError):
        return str(value)


def full_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        norm(row.get("route_candidate_id")),
        norm(row.get("entry_variant")),
        norm(row.get("target_stop_contract_id")),
        norm(row.get("symbol")),
        norm(row.get("side")),
        norm(row.get("target_multiple")),
        norm(row.get("stop_multiple")),
    )


def by_branch(input_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in input_rows}


def source_manifest_rows() -> tuple[list[dict[str, Any]], str]:
    source_paths = [
        REPLAY_EXEC_RESULT_PATH,
        REPLAY_BRANCH_PATH,
        REPLAY_SOURCE_ORDERING_PATH,
        M1_INTERVAL_PATH,
        M1_STRESS_SIGNATURE_PATH,
        M1_STRESS_FAMILY_PATH,
        MATRIX_BRANCH_PATH,
    ]
    manifest_rows = []
    for index, path in enumerate(source_paths, 1):
        manifest_rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-M1-FILL-COLLAPSE-SOURCE-{index:03d}",
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "status": "HASHED",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, manifest_hash


def ratio_for(target_multiple: Any, stop_multiple: Any) -> float | None:
    try:
        target = float(target_multiple)
        stop = float(stop_multiple)
    except (TypeError, ValueError):
        return None
    if stop == 0.0:
        return None
    return target / stop


def status_scalar(status: Any, target_multiple: Any, stop_multiple: Any) -> tuple[float | None, str]:
    text = str(status or "").upper()
    ratio = ratio_for(target_multiple, stop_multiple)
    if "SOURCE_FAIL" in text or "FAIL_CLOSED" in text or "UNAVAILABLE" in text or "MISSING" in text:
        return None, "SOURCE_FAIL_OR_MISSING_NO_SCALAR"
    if "TARGET" in text and ("TOUCH" in text or "CARRIED_TARGET" in text):
        return (ratio, "TARGET_FIRST_SCALAR") if ratio is not None else (None, "TARGET_SCALAR_RATIO_MISSING")
    if "STOP" in text and "TOUCH" in text:
        return -1.0, "STOP_FIRST_SCALAR"
    if "NO_TARGET_OR_STOP" in text or "NO_TOUCH" in text:
        return None, "NO_TARGET_STOP_TOUCH_NO_CLOSE_SCALAR"
    if "AMBIG" in text or "ORDER_UNRESOLVED" in text:
        return None, "ORDER_UNRESOLVED_NO_SCALAR"
    return None, "UNMAPPED_STATUS_NO_SCALAR"


def support_interval(row: dict[str, Any]) -> dict[str, Any]:
    conservative, conservative_method = status_scalar(row.get("conservative_first_touch_status"), row.get("target_multiple"), row.get("stop_multiple"))
    optimistic, optimistic_method = status_scalar(row.get("optimistic_first_touch_status"), row.get("target_multiple"), row.get("stop_multiple"))
    if conservative is not None and optimistic is not None:
        lower = min(conservative, optimistic)
        upper = max(conservative, optimistic)
        midpoint = (lower + upper) / 2.0
        scalar_status = "CONSERVATIVE_AND_OPTIMISTIC_SCALAR"
    elif conservative is not None:
        lower = upper = midpoint = conservative
        scalar_status = "CONSERVATIVE_ONLY_SCALAR"
    elif optimistic is not None and conservative_method == "SOURCE_FAIL_OR_MISSING_NO_SCALAR":
        lower = None
        upper = optimistic
        midpoint = None
        scalar_status = "OPTIMISTIC_UPPER_ONLY_CONSERVATIVE_SOURCE_FAIL"
    elif optimistic is not None:
        lower = upper = midpoint = optimistic
        scalar_status = "OPTIMISTIC_ONLY_SCALAR"
    else:
        lower = upper = midpoint = None
        scalar_status = "NO_SCALAR_SUPPORT_VALUE"
    return {
        "support_conservative_scalar": conservative,
        "support_optimistic_scalar": optimistic,
        "support_rstyle_lower": lower,
        "support_rstyle_midpoint": midpoint,
        "support_rstyle_upper": upper,
        "support_scalar_status": scalar_status,
        "support_conservative_scalar_method": conservative_method,
        "support_optimistic_scalar_method": optimistic_method,
    }


def mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def interval_sign_class(lower: Any, upper: Any) -> str:
    if lower is None or upper is None:
        return "INTERVAL_NO_NUMERIC_BOUNDS"
    if lower <= 0 <= upper:
        return "INTERVAL_STRADDLES_ZERO"
    if lower > 0:
        return "INTERVAL_ALL_POSITIVE"
    if upper < 0:
        return "INTERVAL_ALL_NEGATIVE"
    return "INTERVAL_MIXED_NONZERO"


def support_resolution_class(summary: dict[str, Any]) -> str:
    target_rows = int(summary["support_conservative_target_rows"])
    stop_rows = int(summary["support_conservative_stop_rows"])
    source_fail = int(summary["support_conservative_source_fail_rows"])
    no_touch = int(summary["support_conservative_no_touch_rows"])
    stressed = int(summary["fill_bar_order_unresolved_rows"])
    if stop_rows:
        return "M1_SUPPORT_HAS_STOP_FIRST_COMPONENTS"
    if target_rows and not source_fail and not no_touch and stressed:
        return "M1_FILL_BAR_STRESS_TARGET_STABLE_AFTER_NEXT_BAR"
    if target_rows and not source_fail and not no_touch:
        return "M1_SUPPORT_TARGET_STABLE_NO_FILL_BAR_RESIDUAL"
    if target_rows and source_fail:
        return "M1_SUPPORT_TARGET_WITH_SOURCE_FAIL_CLOSED_RESIDUAL"
    if target_rows and no_touch:
        return "M1_SUPPORT_TARGET_WITH_NO_TOUCH_RESIDUAL"
    return "M1_SUPPORT_NO_TARGET_STOP_SCALAR"


def proxy_value(branch: dict[str, Any], summary: dict[str, Any], variant: str) -> Any:
    if variant == "BRANCH_AGGREGATE_CONSERVATIVE_BOUND":
        return branch.get("interval_rstyle_lower_mean")
    if variant == "BRANCH_AGGREGATE_OPTIMISTIC_BOUND":
        return branch.get("interval_rstyle_upper_mean")
    if variant == "BRANCH_AGGREGATE_MIDPOINT":
        return branch.get("interval_rstyle_midpoint_mean")
    if variant == "M1_SUPPORT_CONSERVATIVE_SCALAR_MEAN":
        return summary["support_component_conservative_scalar_mean"]
    if variant == "M1_SUPPORT_OPTIMISTIC_SCALAR_MEAN":
        return summary["support_component_optimistic_scalar_mean"]
    if variant == "M1_SUPPORT_MIDPOINT_SCALAR_MEAN":
        return summary["support_component_midpoint_mean"]
    return None


def requirement_for(summary: dict[str, Any], branch: dict[str, Any]) -> tuple[str, str]:
    if summary["support_rows_matched"] != branch.get("m1_fill_bar_stress_rows"):
        return (
            "M1_FILL_BAR_SUPPORT_COUNT_MISMATCH_REPAIR_REQUIRED",
            "Repair branch-key support matching before interpreting this branch.",
        )
    if summary["support_conservative_source_fail_rows"]:
        return (
            "M1_FILL_BAR_CONSERVATIVE_SOURCE_FAIL_CLOSED_RESIDUAL",
            "Preserve optimistic upper bound and source-fail lower bound gap; search tick/M1 source if a stronger historical route is found.",
        )
    if summary["fill_bar_order_unresolved_rows"]:
        return (
            "M1_FILL_BAR_INTERVAL_COLLAPSED_TO_TARGET_AT_M1_BAR_LEVEL_TICK_ORDER_STILL_UNKNOWN",
            "Use M1 next-bar conservative target evidence as lower-level proxy while keeping sub-M1 fill-bar tick order non-exact.",
        )
    return (
        "M1_SUPPORT_ALREADY_ORDERED_BY_M1_REPLAY",
        "Use existing M1 support component; branch aggregate may still be governed by broader source/fillability/path controls.",
    )


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    artifact_paths = [
        RESULT_PATH,
        BRANCH_PATH,
        SIGNATURE_SUPPORT_PATH,
        FAMILY_SUPPORT_PATH,
        PROXY_VARIANT_PATH,
        REQUIREMENT_PATH,
        BUCKET_PATH,
        QUESTION_PATH,
        SOURCE_MANIFEST_PATH,
        SUMMARY_PATH,
        Path(__file__).resolve(),
    ]
    records = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "category": "historical_ohlc_gtos_replay_branch_m1_fill_bar_interval_collapse",
        }
        for path in artifact_paths
    ]
    manifest["historical_ohlc_branch_m1_fill_bar_interval_collapse_packet_2026_05_16"] = {
        "generated_utc": generated_at,
        "result": records[0],
        "artifacts": records,
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
    }
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "branch_m1_fill_bar_interval_collapse_packet_built",
        "artifact": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Branch M1 Fill-Bar Interval Collapse Packet",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "## Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- {key}: {value}")
    for category in [
        "branch_aggregate_interval_sign_class",
        "m1_support_resolution_class",
        "signature_support_match_status",
        "support_row_match_status",
        "proxy_variant",
        "target_stop_result",
    ]:
        lines.extend(["", f"## {category}", ""])
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- {bucket}: {count}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows()
    replay_result = read_json(REPLAY_EXEC_RESULT_PATH)
    active_branches = rows(M1_INTERVAL_PATH)
    signature_rows_input = rows(M1_STRESS_SIGNATURE_PATH)
    family_rows_input = rows(M1_STRESS_FAMILY_PATH)
    replay_branch_by_id = by_branch(rows(REPLAY_BRANCH_PATH))
    source_ordering_by_id = by_branch(rows(REPLAY_SOURCE_ORDERING_PATH))
    matrix_by_id = by_branch(rows(MATRIX_BRANCH_PATH))

    branch_ids_by_key: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for row in active_branches:
        branch_ids_by_key[full_key(row)].append(str(row.get("branch_queue_id")))

    signature_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    signature_support_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)
    support_scalar_counters: Counter[str] = Counter()

    for row in signature_rows_input:
        support_interval_row = support_interval(row)
        matched_branch_ids = branch_ids_by_key.get(full_key(row), [])
        status = "MATCHED_ACTIVE_M1_FILL_BAR_INTERVAL_BRANCH" if matched_branch_ids else "UNMATCHED_TO_ACTIVE_110_M1_FILL_BAR_INTERVAL_QUEUE"
        for branch_id in matched_branch_ids or [None]:
            if branch_id:
                signature_by_branch[branch_id].append({**row, **support_interval_row})
            signature_support_rows.append(
                {
                    "m1_fill_bar_interval_signature_support_id": f"OHLC-GTOS-M1-FILL-COLLAPSE-SIG-{len(signature_support_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "support_match_status": status,
                    **{
                        key: row.get(key)
                        for key in [
                            "fill_bar_ordering_stress_signature_id",
                            "m1_spread_adjusted_signature_replay_id",
                            "cost_fill_id",
                            "event_id",
                            "route_candidate_id",
                            "symbol",
                            "route_session",
                            "side",
                            "entry_variant",
                            "target_stop_contract_id",
                            "target_multiple",
                            "stop_multiple",
                            "cost_model",
                            "stress_scope_status",
                            "m1_first_touch_status",
                            "optimistic_first_touch_status",
                            "conservative_first_touch_status",
                            "conservative_source_status",
                            "interval_status",
                            "m1_fill_utc",
                            "m1_fill_bar_offset",
                            "conservative_m1_bars_evaluated",
                        ]
                    },
                    **support_interval_row,
                    "exact_chronology_claim": False,
                    "tick_ordering_exact": False,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
        bucket_counters["signature_support_match_status"][status] += 1
        bucket_counters["support_stress_scope_status"][str(row.get("stress_scope_status"))] += 1
        bucket_counters["support_interval_status"][str(row.get("interval_status"))] += 1
        bucket_counters["support_conservative_first_touch_status"][str(row.get("conservative_first_touch_status"))] += 1
        support_scalar_counters[str(support_interval_row["support_scalar_status"])] += 1

    family_support_rows: list[dict[str, Any]] = []
    for row in family_rows_input:
        matched_branch_ids = branch_ids_by_key.get(full_key(row), [])
        status = "MATCHED_ACTIVE_M1_FILL_BAR_INTERVAL_BRANCH" if matched_branch_ids else "UNMATCHED_TO_ACTIVE_110_M1_FILL_BAR_INTERVAL_QUEUE"
        for branch_id in matched_branch_ids or [None]:
            family_support_rows.append(
                {
                    "m1_fill_bar_interval_family_support_id": f"OHLC-GTOS-M1-FILL-COLLAPSE-FAMILY-{len(family_support_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "support_match_status": status,
                    **{
                        key: row.get(key)
                        for key in [
                            "fill_bar_ordering_stress_family_id",
                            "family_key",
                            "route_candidate_id",
                            "symbol",
                            "route_session",
                            "side",
                            "entry_variant",
                            "target_stop_contract_id",
                            "target_multiple",
                            "stop_multiple",
                            "cost_model",
                            "signature_rows",
                            "stress_scope_status_counts",
                            "interval_status_counts",
                            "conservative_first_touch_status_counts",
                        ]
                    },
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
        bucket_counters["family_support_match_status"][status] += 1

    branch_rows: list[dict[str, Any]] = []
    proxy_rows: list[dict[str, Any]] = []
    requirement_rows: list[dict[str, Any]] = []
    for index, branch in enumerate(active_branches, 1):
        branch_id = str(branch.get("branch_queue_id"))
        support_rows = signature_by_branch.get(branch_id, [])
        support_conservative_values = [float(row["support_conservative_scalar"]) for row in support_rows if row.get("support_conservative_scalar") is not None]
        support_optimistic_values = [float(row["support_optimistic_scalar"]) for row in support_rows if row.get("support_optimistic_scalar") is not None]
        support_midpoint_values = [float(row["support_rstyle_midpoint"]) for row in support_rows if row.get("support_rstyle_midpoint") is not None]
        support_lower_values = [float(row["support_rstyle_lower"]) for row in support_rows if row.get("support_rstyle_lower") is not None]
        support_upper_values = [float(row["support_rstyle_upper"]) for row in support_rows if row.get("support_rstyle_upper") is not None]
        conservative_status_counts = Counter(str(row.get("conservative_first_touch_status")) for row in support_rows)
        stress_scope_counts = Counter(str(row.get("stress_scope_status")) for row in support_rows)
        cost_model_counts = Counter(str(row.get("cost_model")) for row in support_rows)
        support_summary = {
            "support_rows_matched": len(support_rows),
            "support_component_conservative_scalar_mean": mean(support_conservative_values),
            "support_component_optimistic_scalar_mean": mean(support_optimistic_values),
            "support_component_lower_mean": mean(support_lower_values),
            "support_component_midpoint_mean": mean(support_midpoint_values),
            "support_component_upper_mean": mean(support_upper_values),
            "support_component_scalar_rows": len(support_midpoint_values),
            "support_component_upper_only_rows": sum(1 for row in support_rows if row.get("support_scalar_status") == "OPTIMISTIC_UPPER_ONLY_CONSERVATIVE_SOURCE_FAIL"),
            "support_component_no_scalar_rows": sum(1 for row in support_rows if row.get("support_scalar_status") == "NO_SCALAR_SUPPORT_VALUE"),
            "support_conservative_target_rows": sum(1 for row in support_rows if row.get("support_conservative_scalar_method") == "TARGET_FIRST_SCALAR"),
            "support_conservative_stop_rows": sum(1 for row in support_rows if row.get("support_conservative_scalar_method") == "STOP_FIRST_SCALAR"),
            "support_conservative_no_touch_rows": sum(1 for row in support_rows if row.get("support_conservative_scalar_method") == "NO_TARGET_STOP_TOUCH_NO_CLOSE_SCALAR"),
            "support_conservative_source_fail_rows": sum(1 for row in support_rows if row.get("support_conservative_scalar_method") == "SOURCE_FAIL_OR_MISSING_NO_SCALAR"),
            "fill_bar_order_unresolved_rows": int(stress_scope_counts.get("FILL_BAR_ORDER_UNRESOLVED_STRESSED", 0)),
        }
        branch_aggregate_interval_sign = interval_sign_class(branch.get("interval_rstyle_lower_mean"), branch.get("interval_rstyle_upper_mean"))
        support_interval_sign = interval_sign_class(support_summary["support_component_lower_mean"], support_summary["support_component_upper_mean"])
        support_class = support_resolution_class(support_summary)
        replay_branch = replay_branch_by_id.get(branch_id, {})
        source_ordering = source_ordering_by_id.get(branch_id, {})
        matrix = matrix_by_id.get(branch_id, {})
        requirement_status, requirement_action = requirement_for(support_summary, branch)
        support_match = (
            "SUPPORT_ROWS_MATCH_UPSTREAM_COUNT"
            if support_summary["support_rows_matched"] == branch.get("m1_fill_bar_stress_rows")
            else "SUPPORT_ROWS_DIFFER_FROM_UPSTREAM_COUNT"
        )
        exact_success_cause = replay_branch.get("exact_success_cause") or matrix.get("exact_success_cause")
        exact_failure_cause = replay_branch.get("exact_failure_cause") or matrix.get("exact_failure_cause")
        if support_class.startswith("M1_SUPPORT_TARGET") or support_class.startswith("M1_FILL_BAR_STRESS_TARGET"):
            support_success_cause = "M1_FILL_BAR_SUPPORT_TARGET_FIRST_DOMINANT"
        else:
            support_success_cause = "NO_M1_FILL_BAR_SUPPORT_SUCCESS_CAUSE_DOMINANT"
        support_failure_bits = []
        if support_summary["support_conservative_source_fail_rows"]:
            support_failure_bits.append("M1_FILL_BAR_CONSERVATIVE_SOURCE_FAIL_CLOSED")
        if support_summary["support_conservative_no_touch_rows"]:
            support_failure_bits.append("M1_FILL_BAR_NO_TARGET_STOP_TOUCH_RESIDUAL")
        if support_summary["support_conservative_stop_rows"]:
            support_failure_bits.append("M1_FILL_BAR_STOP_FIRST_SUPPORT_PRESENT")
        support_failure_cause = "__".join(support_failure_bits) if support_failure_bits else "NO_M1_FILL_BAR_SUPPORT_FAILURE_CAUSE_DOMINANT"
        branch_row = {
            "m1_fill_bar_interval_collapse_branch_id": f"OHLC-GTOS-M1-FILL-COLLAPSE-BRANCH-{index:05d}",
            **{
                key: branch.get(key)
                for key in [
                    "branch_queue_id",
                    "route_candidate_id",
                    "symbol",
                    "route_session",
                    "side",
                    "entry_variant",
                    "target_stop_contract_id",
                    "target_multiple",
                    "stop_multiple",
                    "branch_result_class",
                    "target_stop_result",
                    "interval_policy",
                    "interval_preservation_class",
                    "interval_rstyle_lower_mean",
                    "interval_rstyle_midpoint_mean",
                    "interval_rstyle_upper_mean",
                    "m1_replay_rows",
                    "m1_fill_bar_stress_rows",
                    "path_ambiguity_rows",
                ]
            },
            "sealed_or_proxy_outcome_status": replay_branch.get("sealed_proxy_class") or "PROXY_RSTYLE_OUTCOME_COMPUTED_OR_ENTRY_SCOPE_BOUND",
            "expectancy_style_proxy_method": replay_branch.get("expectancy_style_proxy_method") or "branch_aggregate_and_m1_support_component_proxy_not_broker_expectancy",
            "pass_control_delta_status": replay_branch.get("pass_control_delta_status"),
            "cost_sensitivity_proxy_status": replay_branch.get("cost_sensitivity_proxy_status"),
            "effective_n_concentration_class": replay_branch.get("effective_n_concentration_class") or matrix.get("effective_n_concentration_class"),
            "unique_event_or_route_ids": matrix.get("unique_event_or_route_ids"),
            "duplicate_inflation_ratio_material_rows_over_event_ids": matrix.get("duplicate_inflation_ratio_material_rows_over_event_ids"),
            "concentration_summary": matrix.get("concentration_summary"),
            "same_route_peer_delta": replay_branch.get("same_route_peer_delta"),
            "source_confidence_status": replay_branch.get("source_confidence_status"),
            "source_execution_class": source_ordering.get("source_execution_class") or replay_branch.get("source_execution_class"),
            "ordering_execution_class": source_ordering.get("ordering_execution_class") or replay_branch.get("ordering_execution_class"),
            "source_deep_action_class": source_ordering.get("source_deep_action_class"),
            "ordering_deep_action_class": source_ordering.get("ordering_deep_action_class"),
            "ambiguity_status": replay_branch.get("ambiguity_status"),
            "same_resource_execution_implication": replay_branch.get("same_resource_execution_implication"),
            "branch_local_next_computations": replay_branch.get("branch_local_next_computations"),
            "primary_branch_local_surface": replay_branch.get("primary_branch_local_surface"),
            "branch_aggregate_interval_sign_class": branch_aggregate_interval_sign,
            "m1_support_interval_sign_class": support_interval_sign,
            "m1_support_resolution_class": support_class,
            "support_row_match_status": support_match,
            "support_conservative_first_touch_status_counts": compact_counter(conservative_status_counts),
            "support_stress_scope_status_counts": compact_counter(stress_scope_counts),
            "support_cost_model_counts": compact_counter(cost_model_counts),
            **support_summary,
            "m1_support_exact_success_cause": support_success_cause,
            "m1_support_exact_failure_cause": support_failure_cause,
            "exact_success_cause": exact_success_cause,
            "exact_failure_cause": exact_failure_cause,
            "exact_missing_geometry_or_source_reason": replay_branch.get("exact_missing_geometry_or_source_reason")
            or matrix.get("exact_missing_geometry_reason"),
            "m1_fill_bar_requirement_status": requirement_status,
            "m1_fill_bar_next_action": requirement_action,
            "exact_chronology_claim": False,
            "tick_ordering_exact": False,
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        branch_rows.append(branch_row)
        for variant in PROXY_VARIANTS:
            proxy_rows.append(
                {
                    "m1_fill_bar_interval_proxy_variant_id": f"OHLC-GTOS-M1-FILL-COLLAPSE-PROXY-{len(proxy_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "proxy_variant": variant,
                    "proxy_rstyle_value": proxy_value(branch, support_summary, variant),
                    "proxy_value_source": "BRANCH_AGGREGATE_INTERVAL" if variant.startswith("BRANCH_") else "M1_FILL_BAR_SUPPORT_COMPONENT",
                    "exact_chronology_claim": False,
                    "tick_ordering_exact": False,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
            bucket_counters["proxy_variant"][variant] += 1
        requirement_rows.append(
            {
                "m1_fill_bar_interval_requirement_id": f"OHLC-GTOS-M1-FILL-COLLAPSE-REQ-{index:05d}",
                "branch_queue_id": branch_id,
                "requirement_status": requirement_status,
                "next_repair_or_proxy_action": requirement_action,
                "support_rows_matched": support_summary["support_rows_matched"],
                "upstream_m1_fill_bar_stress_rows": branch.get("m1_fill_bar_stress_rows"),
                "fill_bar_order_unresolved_rows": support_summary["fill_bar_order_unresolved_rows"],
                "support_conservative_source_fail_rows": support_summary["support_conservative_source_fail_rows"],
                "exact_chronology_claim": False,
                "tick_ordering_exact": False,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["branch_aggregate_interval_sign_class"][branch_aggregate_interval_sign] += 1
        bucket_counters["m1_support_interval_sign_class"][support_interval_sign] += 1
        bucket_counters["m1_support_resolution_class"][support_class] += 1
        bucket_counters["support_row_match_status"][support_match] += 1
        bucket_counters["target_stop_result"][str(branch.get("target_stop_result"))] += 1
        bucket_counters["branch_result_class"][str(branch.get("branch_result_class"))] += 1
        bucket_counters["requirement_status"][requirement_status] += 1

    bucket_counters["support_scalar_status"].update(support_scalar_counters)
    question_rows = [
        {
            "question_id": "OHLC-GTOS-M1-FILL-COLLAPSE-QUESTION-001",
            "question": "Do the active M1 fill-bar interval branches remain interval-sign ambiguous at the branch aggregate level?",
            "answer_route": "Use branch_aggregate_interval_sign_class over the 110 active branch rows.",
        },
        {
            "question_id": "OHLC-GTOS-M1-FILL-COLLAPSE-QUESTION-002",
            "question": "Does the M1 fill-bar support component itself point target-first, stop-first, no-touch, or source-fail?",
            "answer_route": "Use m1_support_resolution_class and support_conservative_first_touch_status_counts.",
        },
        {
            "question_id": "OHLC-GTOS-M1-FILL-COLLAPSE-QUESTION-003",
            "question": "Which support signatures and families are outside the active 110 branch interval queue?",
            "answer_route": "Use signature/family support match status; unmatched rows are preserved, not discarded.",
        },
        {
            "question_id": "OHLC-GTOS-M1-FILL-COLLAPSE-QUESTION-004",
            "question": "Which branches still need source/tick-ordering repair rather than scalar collapse?",
            "answer_route": "Use requirement_status and the exact_chronology_claim=false/tick_ordering_exact=false flags.",
        },
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "generated_utc": generated_at, "not_completion": True})

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-M1-FILL-COLLAPSE-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "row_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_replay_execution_branch_rows": replay_result.get("counts", {}).get("branch_replay_execution_rows"),
            "input_m1_fill_bar_interval_branch_rows": len(active_branches),
            "input_m1_fill_bar_stress_signature_rows": len(signature_rows_input),
            "input_m1_fill_bar_stress_family_rows": len(family_rows_input),
            "m1_fill_bar_interval_branch_rows": len(branch_rows),
            "m1_fill_bar_signature_support_rows": len(signature_support_rows),
            "m1_fill_bar_matched_signature_support_rows": int(
                bucket_counters["signature_support_match_status"]["MATCHED_ACTIVE_M1_FILL_BAR_INTERVAL_BRANCH"]
            ),
            "m1_fill_bar_unmatched_signature_support_rows": int(
                bucket_counters["signature_support_match_status"]["UNMATCHED_TO_ACTIVE_110_M1_FILL_BAR_INTERVAL_QUEUE"]
            ),
            "m1_fill_bar_family_support_rows": len(family_support_rows),
            "m1_fill_bar_matched_family_support_rows": int(
                bucket_counters["family_support_match_status"]["MATCHED_ACTIVE_M1_FILL_BAR_INTERVAL_BRANCH"]
            ),
            "m1_fill_bar_unmatched_family_support_rows": int(
                bucket_counters["family_support_match_status"]["UNMATCHED_TO_ACTIVE_110_M1_FILL_BAR_INTERVAL_QUEUE"]
            ),
            "m1_fill_bar_matched_fill_bar_order_unresolved_rows": sum(int(row["fill_bar_order_unresolved_rows"]) for row in branch_rows),
            "m1_fill_bar_matched_source_fail_closed_rows": sum(int(row["support_conservative_source_fail_rows"]) for row in branch_rows),
            "m1_fill_bar_proxy_variant_rows": len(proxy_rows),
            "m1_fill_bar_requirement_rows": len(requirement_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "source_manifest_hash": manifest_hash,
    }
    for path, output_rows in [
        (BRANCH_PATH, branch_rows),
        (SIGNATURE_SUPPORT_PATH, signature_support_rows),
        (FAMILY_SUPPORT_PATH, family_support_rows),
        (PROXY_VARIANT_PATH, proxy_rows),
        (REQUIREMENT_PATH, requirement_rows),
        (BUCKET_PATH, bucket_rows),
        (QUESTION_PATH, question_rows),
        (SOURCE_MANIFEST_PATH, source_rows),
    ]:
        write_jsonl(path, output_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
