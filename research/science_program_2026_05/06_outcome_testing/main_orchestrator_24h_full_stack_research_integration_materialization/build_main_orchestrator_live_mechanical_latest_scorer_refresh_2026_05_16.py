"""Materialize latest-only live mechanical scorer refresh rows.

This plate uses the bounded dry-run mode in ``live_mechanical_shadow`` to show
the concrete scorer rows that current code would append for the latest path row
per candidate. It does not append to ``shadow_logs``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    DEFAULT_CANDIDATES,
    DEFAULT_LTF_PATH_ORDER,
    DEFAULT_OUTPUT,
    DEFAULT_PATHS,
    DEFAULT_PENDING_LIFECYCLE,
    latest_existing_by_key,
    run,
)


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

DRY_RUN_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_DRY_RUN_LEDGER_{DATE}.jsonl"
)
DELTA_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_DELTA_LEDGER_{DATE}.jsonl"
)
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_SUMMARY_{DATE}.json"
MANIFEST = (
    ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_OUTPUT_MANIFEST_{DATE}.json"
)

INPUTS = {
    "strategy_follow_candidates": DEFAULT_CANDIDATES,
    "candidate_path_follow": DEFAULT_PATHS,
    "pending_limit_lifecycle": DEFAULT_PENDING_LIFECYCLE,
    "candidate_ltf_path_order": DEFAULT_LTF_PATH_ORDER,
    "live_mechanical_strategy_shadow_outcomes": DEFAULT_OUTPUT,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def proxy_delta(before: Any, after: Any) -> float | None:
    before_value = safe_float(before)
    after_value = safe_float(after)
    if before_value is None or after_value is None:
        return None
    return round(after_value - before_value, 8)


def delta_class(before: Any, after: Any) -> str:
    before_numeric = safe_float(before) is not None
    after_numeric = safe_float(after) is not None
    if before_numeric and after_numeric:
        delta = proxy_delta(before, after)
        return "NUMERIC_PROXY_UNCHANGED" if delta == 0 else "NUMERIC_PROXY_VALUE_CHANGED"
    if not before_numeric and after_numeric:
        return "NEW_NUMERIC_PROXY_R"
    if before_numeric and not after_numeric:
        return "LOST_NUMERIC_PROXY_R"
    return "NO_NUMERIC_PROXY_BEFORE_OR_AFTER"


def primitive_family(row: dict[str, Any]) -> str:
    strategy_id = str(row.get("strategy_id") or "")
    family = str(row.get("strategy_family") or "")
    if strategy_id == "LIVE_AI_J46_J49_BASELINE_COMPARATOR":
        return "live_shadow_baseline_candidate_path"
    if strategy_id in {"J46_J49_PORTFOLIO_POLICY", "S79_UNIFORM_FN_RISK_POLICY"}:
        return "risk_portfolio_context_policy"
    if strategy_id in {"V2_STRUCT_FVG_MID_EDGE", "V3_FVG_ONLY_RESCUE_RISK_BANK"}:
        return "fvg_entry_geometry_and_lock_metadata"
    if strategy_id == "FVG_OB_CONFLUENCE_OB_AFTER_FVG":
        return "fvg_ob_confluence_shared_path_scorer"
    if strategy_id == "V2_STRUCT_SWING_PROTECTED":
        return "structural_swing_protected_stop_geometry"
    if family in {"v2_structural_selector", "v3_risk_bank"}:
        return "structural_lock_reentry_cost_metadata"
    if strategy_id == "PENDING_LIMIT_LIFECYCLE":
        return "pending_lifecycle_fill_cancel_expiry_source_capture"
    if strategy_id == "PREFILL_DELIVERY_REVERSAL_PATH":
        return "prefill_delivery_adverse_reversal_path"
    if strategy_id == "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC":
        return "orderflow_depth_proxy_diagnostic"
    return family or "other"


def action_class(row: dict[str, Any]) -> str:
    status = str(row.get("after_strategy_status") or "")
    score = str(row.get("after_score_status") or "")
    branch = str(row.get("after_branch_decision") or "")
    if status.startswith("SCORED_") or score.startswith("COMPUTED"):
        return "SCORER_OUTPUT_COMPUTED"
    if status.startswith("KILLED_") or branch.startswith("KILL_"):
        return "KILL"
    if status.startswith("REDESIGN_") or "REDESIGN" in branch:
        return "REDESIGN"
    if "SOURCE_CAPTURE_REQUIRED" in branch or "MISSING_REQUIRED" in score or "MISSING_" in status:
        return "SOURCE_REPAIR"
    if status.startswith("CONTEXT_ONLY") or "PRESERVE" in branch:
        return "KEEP_CONTEXT"
    if score == "WAITING":
        return "WAITING_SOURCE_OR_LICENSE"
    return "KEEP_OR_MONITOR"


def build_delta_rows(after_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_by_key = latest_existing_by_key(DEFAULT_OUTPUT)
    generated = utc_now()
    rows: list[dict[str, Any]] = []
    for after in after_rows:
        key = (
            str(after.get("candidate_id") or ""),
            str(after.get("strategy_id") or ""),
            str(after.get("asof_latest_candle_utc") or ""),
        )
        before = existing_by_key.get(key, {})
        before_r = before.get("strategy_proxy_r")
        after_r = after.get("strategy_proxy_r")
        row = {
            "row_id": f"MAIN-ORCH24-LATEST-SCORER-REFRESH-{len(rows) + 1:05d}",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "candidate_id": after.get("candidate_id"),
            "trade_id": after.get("trade_id"),
            "symbol": after.get("symbol"),
            "broker_symbol": after.get("broker_symbol"),
            "side": after.get("side"),
            "framework": after.get("framework"),
            "strategy_id": after.get("strategy_id"),
            "strategy_family": after.get("strategy_family"),
            "primitive_family": primitive_family(after),
            "asof_latest_candle_utc": after.get("asof_latest_candle_utc"),
            "dry_run_append_status": after.get("dry_run_append_status"),
            "before_created_at_utc": before.get("created_at_utc"),
            "after_created_at_utc": after.get("created_at_utc"),
            "before_strategy_status": before.get("strategy_status"),
            "after_strategy_status": after.get("strategy_status"),
            "before_score_status": before.get("score_status"),
            "after_score_status": after.get("score_status"),
            "before_outcome_status": before.get("outcome_status"),
            "after_outcome_status": after.get("outcome_status"),
            "before_branch_decision": before.get("branch_decision"),
            "after_branch_decision": after.get("branch_decision"),
            "before_implementation_candidate": before.get("implementation_candidate"),
            "after_implementation_candidate": after.get("implementation_candidate"),
            "before_scoring_boundary": before.get("scoring_boundary"),
            "after_scoring_boundary": after.get("scoring_boundary"),
            "before_proxy_r": before_r,
            "after_proxy_r": after_r,
            "proxy_r_delta": proxy_delta(before_r, after_r),
            "proxy_r_delta_class": delta_class(before_r, after_r),
            "current_row_proxy_count_delta": (
                1
                if safe_float(before_r) is None and safe_float(after_r) is not None
                else -1
                if safe_float(before_r) is not None and safe_float(after_r) is None
                else 0
            ),
            "entry_retest_redesign_bucket": after.get("entry_retest_redesign_bucket"),
            "nearest_distance_to_entry_r": after.get("nearest_distance_to_entry_r"),
            "standalone_fvg_poi_status": after.get("standalone_fvg_poi_status"),
            "swing_protected_stop_status": after.get("swing_protected_stop_status"),
            "pending_lifecycle_source_capture_complete": after.get(
                "pending_lifecycle_source_capture_complete"
            ),
            "pending_lifecycle_source_capture_statuses": after.get(
                "pending_lifecycle_source_capture_statuses"
            ),
            "action_class": None,
            "exact_r": None,
            "safe_flags": SAFE_FLAGS,
            "no_live_behavior": True,
            "no_shadow_log_append": True,
            "implementation_decision": after.get("implementation_candidate")
            or after.get("branch_decision")
            or after.get("strategy_status"),
        }
        row["action_class"] = action_class(row)
        rows.append(row)
    return rows


def summarize(rows: list[dict[str, Any]], run_summary: dict[str, Any], shadow_hash_before: str, shadow_hash_after: str) -> dict[str, Any]:
    before_numeric = [value for row in rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
    after_numeric = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_primitive: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_strategy[str(row.get("strategy_id") or "")].append(row)
        by_primitive[str(row.get("primitive_family") or "")].append(row)

    def group_summary(group_rows: list[dict[str, Any]]) -> dict[str, Any]:
        before = [value for row in group_rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
        after = [value for row in group_rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
        return {
            "rows": len(group_rows),
            "before_numeric_proxy_rows": len(before),
            "after_numeric_proxy_rows": len(after),
            "numeric_proxy_row_delta": len(after) - len(before),
            "before_proxy_r_sum": sum(before),
            "after_proxy_r_sum": sum(after),
            "proxy_r_sum_delta": sum(after) - sum(before),
            "after_proxy_r_mean": mean(after),
            "action_class_counts": dict(Counter(str(row.get("action_class")) for row in group_rows)),
            "after_strategy_status_counts": dict(
                Counter(str(row.get("after_strategy_status")) for row in group_rows)
            ),
        }

    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_DRY_RUN",
        "claim_boundary": (
            "Latest-only dry-run materialization of current live mechanical scorer outputs. "
            "No shadow log append, live behavior, exact broker/account R, promotion, validation, "
            "paid fetch, or broker operation is opened."
        ),
        "backfill_run_summary": run_summary,
        "shadow_output_hash_before": shadow_hash_before,
        "shadow_output_hash_after": shadow_hash_after,
        "shadow_output_unchanged": shadow_hash_before == shadow_hash_after,
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "exact_r_rows": 0,
        "before_numeric_proxy_rows": len(before_numeric),
        "after_numeric_proxy_rows": len(after_numeric),
        "numeric_proxy_row_delta": len(after_numeric) - len(before_numeric),
        "before_proxy_r_sum": sum(before_numeric),
        "after_proxy_r_sum": sum(after_numeric),
        "proxy_r_sum_delta": sum(after_numeric) - sum(before_numeric),
        "before_proxy_r_mean": mean(before_numeric),
        "after_proxy_r_mean": mean(after_numeric),
        "dry_run_append_status_counts": dict(
            Counter(str(row.get("dry_run_append_status")) for row in rows)
        ),
        "action_class_counts": dict(Counter(str(row.get("action_class")) for row in rows)),
        "proxy_r_delta_class_counts": dict(
            Counter(str(row.get("proxy_r_delta_class")) for row in rows)
        ),
        "primitive_family_summary": {
            family: group_summary(group_rows) for family, group_rows in sorted(by_primitive.items())
        },
        "strategy_summary": {
            strategy: group_summary(group_rows) for strategy, group_rows in sorted(by_strategy.items())
        },
        "entry_redesign_bucket_counts": dict(
            Counter(
                str(row.get("entry_retest_redesign_bucket") or "")
                for row in rows
                if row.get("strategy_id") == "LIVE_AI_J46_J49_BASELINE_COMPARATOR"
            )
        ),
        "safe_flags": SAFE_FLAGS,
        "terminal_decision": "MATERIALIZED_LATEST_ONLY_SCORER_REFRESH_DRY_RUN_WITH_ROW_LEVEL_DELTAS",
        "no_shadow_log_append": True,
    }


def build_manifest(outputs: list[Path], inputs: dict[str, Path]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
            }
            for name, path in inputs.items()
        },
        "outputs": {
            path.name: {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in outputs
        },
    }


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    shadow_hash_before = sha256_file(DEFAULT_OUTPUT) if DEFAULT_OUTPUT.exists() else ""
    run_summary = run(
        candidates_path=DEFAULT_CANDIDATES,
        paths_path=DEFAULT_PATHS,
        pending_lifecycle_path=DEFAULT_PENDING_LIFECYCLE,
        ltf_path_order_path=DEFAULT_LTF_PATH_ORDER,
        output_path=DEFAULT_OUTPUT,
        latest_paths_only=True,
        dry_run=True,
        dry_run_output_path=DRY_RUN_LEDGER,
    )
    shadow_hash_after = sha256_file(DEFAULT_OUTPUT) if DEFAULT_OUTPUT.exists() else ""
    dry_run_rows = read_jsonl(DRY_RUN_LEDGER)
    delta_rows = build_delta_rows(dry_run_rows)
    write_jsonl(DELTA_LEDGER, delta_rows)
    summary = summarize(delta_rows, run_summary, shadow_hash_before, shadow_hash_after)
    write_json(SUMMARY, summary)
    manifest = build_manifest([DRY_RUN_LEDGER, DELTA_LEDGER, SUMMARY], INPUTS)
    write_json(MANIFEST, manifest)
    print(json.dumps({"summary": str(SUMMARY), "rows": len(delta_rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
