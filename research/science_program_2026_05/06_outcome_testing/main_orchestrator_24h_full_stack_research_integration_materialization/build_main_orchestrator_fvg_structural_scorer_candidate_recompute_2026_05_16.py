"""Recompute FVG/structural scorer implementation candidates against current rows.

This builder is read-only for shadow logs. It materializes the stricter
standalone-FVG-POI and swing-protected-stop scorer candidate decisions without
appending to live shadow logs or changing live behavior.
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

from src.research_infra.live_mechanical_shadow import (
    FVG_OB_CONFLUENCE_ID,
    FVG_REQUIRED_IDS,
    PENDING_LIMIT_STRATEGY_ID,
    PREFILL_DELIVERY_STRATEGY_ID,
    STRUCTURAL_LOCK_REQUIRED_IDS,
    SWING_PROTECTED_STRATEGY_ID,
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    read_jsonl,
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

INPUTS = {
    "strategy_follow_candidates": Path("shadow_logs/strategy_follow_candidates.jsonl"),
    "candidate_path_follow": Path("shadow_logs/candidate_path_follow.jsonl"),
    "live_mechanical_strategy_shadow_outcomes": Path(
        "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"
    ),
    "pending_limit_lifecycle": Path("shadow_logs/pending_limit_lifecycle.jsonl"),
    "candidate_ltf_path_order": Path("shadow_logs/candidate_ltf_path_order.jsonl"),
}

PRIORITY_STRATEGIES = sorted(
    FVG_REQUIRED_IDS
    | STRUCTURAL_LOCK_REQUIRED_IDS
    | {FVG_OB_CONFLUENCE_ID, PENDING_LIMIT_STRATEGY_ID, PREFILL_DELIVERY_STRATEGY_ID}
)

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_SCORER_CANDIDATE_RECOMPUTE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_SCORER_CANDIDATE_RECOMPUTE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_SCORER_CANDIDATE_RECOMPUTE_OUTPUT_MANIFEST_{DATE}.json"
PREVIOUS_SHARED_METADATA_SUMMARY = (
    ROUTE_DIR / f"MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_SUMMARY_{DATE}.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_numeric(value: Any) -> bool:
    return safe_float(value) is not None


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous = parse_utc(out.get(cid, {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if current >= previous:
            out[cid] = row
    return out


def latest_path_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current_asof = parse_utc(row.get("asof_latest_candle_utc"))
        previous_asof = parse_utc(out.get(cid, {}).get("asof_latest_candle_utc"))
        current_created = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous_created = parse_utc(out.get(cid, {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if previous_asof is None or (
            current_asof is not None
            and (current_asof > previous_asof or (current_asof == previous_asof and current_created >= previous_created))
        ):
            out[cid] = row
    return out


def latest_mechanical_by_candidate_strategy(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
        if not key[0] or not key[1]:
            continue
        current_asof = parse_utc(row.get("asof_latest_candle_utc"))
        previous_asof = parse_utc(out.get(key, {}).get("asof_latest_candle_utc"))
        current_created = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous_created = parse_utc(out.get(key, {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if previous_asof is None or (
            current_asof is not None
            and (current_asof > previous_asof or (current_asof == previous_asof and current_created >= previous_created))
        ):
            out[key] = row
    return out


def source_capture_surface(strategy_id: str) -> str:
    if strategy_id in FVG_REQUIRED_IDS:
        return "standalone_fvg_poi_scorer"
    if strategy_id == SWING_PROTECTED_STRATEGY_ID:
        return "swing_protected_stop_scorer"
    if strategy_id in STRUCTURAL_LOCK_REQUIRED_IDS:
        return "structural_lock_metadata_scorer"
    if strategy_id == FVG_OB_CONFLUENCE_ID:
        return "fvg_ob_confluence_shared_path_scorer"
    if strategy_id == PENDING_LIMIT_STRATEGY_ID:
        return "pending_limit_lifecycle_source_capture"
    if strategy_id == PREFILL_DELIVERY_STRATEGY_ID:
        return "prefill_delivery_redesign"
    return "other"


def implementation_decision(row: dict[str, Any]) -> str:
    strategy_id = str(row.get("strategy_id") or "")
    status = str(row.get("strategy_status") or "")
    score_status = str(row.get("score_status") or "")
    if strategy_id in FVG_REQUIRED_IDS:
        if status == "SCORED_STANDALONE_FVG_POI_PROXY_CANDIDATE_PATH":
            if is_numeric(row.get("strategy_proxy_r")):
                return "IMPLEMENT_DEFAULT_OFF_STANDALONE_FVG_POI_PROXY_SCORER_NOW"
            return "IMPLEMENT_DEFAULT_OFF_STANDALONE_FVG_POI_SCORER_WITH_AMBIGUITY_EXCLUSION"
        if status == "KILLED_STANDALONE_FVG_POI_NOT_SELECTED":
            return "KILL_STANDALONE_FVG_SCORER_FOR_NON_FVG_POI_ROWS"
        if status == "REDESIGN_REQUIRED_FVG_POI_ENTRY_NOT_BOUND_TO_GAP":
            return "REDESIGN_STANDALONE_FVG_ENTRY_SELECTOR"
        return "SOURCE_CAPTURE_REQUIRED_FOR_STANDALONE_FVG_SCORER"
    if strategy_id == SWING_PROTECTED_STRATEGY_ID:
        if status == "SCORED_SWING_PROTECTED_STOP_PROXY_SHARED_CANDIDATE_PATH":
            if is_numeric(row.get("strategy_proxy_r")):
                return "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_PROXY_SCORER_NOW"
            return "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_SCORER_WITH_AMBIGUITY_EXCLUSION"
        if status == "KILLED_SWING_PROTECTED_STOP_NOT_CONFIRMED":
            return "KILL_SWING_PROTECTED_SCORER_FOR_UNPROTECTED_STOP_ROWS"
        return "SOURCE_CAPTURE_REQUIRED_FOR_SWING_PROTECTED_STOP_SCORER"
    if strategy_id in STRUCTURAL_LOCK_REQUIRED_IDS:
        if status == "SCORED_STRUCTURAL_LOCK_METADATA_PROXY_SHARED_CANDIDATE_PATH":
            if is_numeric(row.get("strategy_proxy_r")):
                return "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER_NOW"
            return "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_SCORER_WITH_AMBIGUITY_EXCLUSION"
        return "SOURCE_CAPTURE_REQUIRED_FOR_STRUCTURAL_LOCK_SCORER"
    if strategy_id == FVG_OB_CONFLUENCE_ID:
        if status == "SCORED_FVG_OB_CONFLUENCE_PROXY_SHARED_CANDIDATE_PATH":
            return "KEEP_DEFAULT_OFF_FVG_OB_SHARED_PATH_PROXY_SCORER"
        return "SOURCE_CAPTURE_REQUIRED_FOR_FVG_OB_CONFLUENCE_SCORER"
    if strategy_id == PENDING_LIMIT_STRATEGY_ID:
        if status == "SCORED_PENDING_LIFECYCLE_INTERNAL_TRUTH":
            if row.get("pending_lifecycle_source_capture_complete") is True:
                return "KEEP_PENDING_LIFECYCLE_SCORER_WITH_CAPTURE_FIELDS_COMPLETE"
            return "KEEP_PENDING_LIFECYCLE_SCORER_FORWARD_CAPTURE_FIELDS_IMPLEMENTED_CURRENT_ROWS_PARTIAL"
        if score_status == "WAITING_FOR_PENDING_LIFECYCLE":
            return "SOURCE_CAPTURE_REQUIRED_FOR_PENDING_LIFECYCLE_SCORER"
        return "KEEP_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_SCORER"
    if strategy_id == PREFILL_DELIVERY_STRATEGY_ID:
        return "REDESIGN_PREFILL_DELIVERY_REVERSAL_PATH_SCORER"
    return "NO_PRIORITY_DECISION"


def proxy_delta(before: Any, after: Any) -> float | None:
    before_value = safe_float(before)
    after_value = safe_float(after)
    if before_value is None or after_value is None:
        return None
    return round(after_value - before_value, 8)


def delta_class(before: Any, after: Any) -> str:
    before_numeric = is_numeric(before)
    after_numeric = is_numeric(after)
    if before_numeric and after_numeric:
        delta = proxy_delta(before, after)
        if delta == 0:
            return "NUMERIC_PROXY_UNCHANGED"
        return "NUMERIC_PROXY_VALUE_CHANGED"
    if not before_numeric and after_numeric:
        return "NEW_NUMERIC_PROXY_R"
    if before_numeric and not after_numeric:
        return "LOST_NUMERIC_PROXY_R"
    return "NO_NUMERIC_PROXY_BEFORE_OR_AFTER"


def build_rows() -> list[dict[str, Any]]:
    candidates = latest_by_candidate(read_jsonl(INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_jsonl(INPUTS["candidate_path_follow"]))
    mechanical = latest_mechanical_by_candidate_strategy(
        read_jsonl(INPUTS["live_mechanical_strategy_shadow_outcomes"])
    )
    pending_lifecycle_rows = read_jsonl(INPUTS["pending_limit_lifecycle"])
    ltf_rows = read_jsonl(INPUTS["candidate_ltf_path_order"])
    generated = utc_now()

    out: list[dict[str, Any]] = []
    for cid in sorted(candidates):
        candidate = candidates[cid]
        path = paths.get(cid)
        if not path:
            continue
        pending = latest_lifecycle_for_candidate_asof(candidate, path, pending_lifecycle_rows)
        ltf = latest_ltf_for_candidate_asof(candidate, path, ltf_rows)
        recomputed = {
            str(row.get("strategy_id") or ""): row
            for row in build_strategy_outcome_rows(
                candidate,
                path,
                pending_lifecycle_row=pending,
                ltf_row=ltf,
                created_at_utc=generated,
            )
        }
        for strategy_id in PRIORITY_STRATEGIES:
            after = recomputed.get(strategy_id)
            if not after:
                continue
            before = mechanical.get((cid, strategy_id), {})
            before_r = before.get("strategy_proxy_r")
            after_r = after.get("strategy_proxy_r")
            out.append(
                {
                    "row_id": f"MAIN-ORCH24-FVG-STRUCT-SCORER-CAND-{len(out) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "generated_utc": generated,
                    "candidate_id": cid,
                    "symbol": after.get("symbol"),
                    "side": after.get("side"),
                    "framework": after.get("framework"),
                    "strategy_id": strategy_id,
                    "source_capture_surface": source_capture_surface(strategy_id),
                    "asof_latest_candle_utc": after.get("asof_latest_candle_utc"),
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
                        if not is_numeric(before_r) and is_numeric(after_r)
                        else -1
                        if is_numeric(before_r) and not is_numeric(after_r)
                        else 0
                    ),
                    "entry_touch_distance_status": after.get("entry_touch_distance_status"),
                    "nearest_distance_to_entry_r": after.get("nearest_distance_to_entry_r"),
                    "entry_retest_redesign_bucket": after.get("entry_retest_redesign_bucket"),
                    "standalone_fvg_poi_status": after.get("standalone_fvg_poi_status"),
                    "standalone_fvg_poi_type": after.get("standalone_fvg_poi_type"),
                    "standalone_fvg_entry_inside_gap": after.get("standalone_fvg_entry_inside_gap"),
                    "standalone_fvg_poi_price_inside_gap": after.get(
                        "standalone_fvg_poi_price_inside_gap"
                    ),
                    "standalone_fvg_matching_gap_timeframes": after.get(
                        "standalone_fvg_matching_gap_timeframes"
                    ),
                    "swing_protected_stop_status": after.get("swing_protected_stop_status"),
                    "swing_protected_match_timeframe": after.get("swing_protected_match_timeframe"),
                    "swing_protected_match_price": after.get("swing_protected_match_price"),
                    "swing_protected_stop_distance_price": after.get(
                        "swing_protected_stop_distance_price"
                    ),
                    "pending_lifecycle_source_capture_contract": after.get(
                        "pending_lifecycle_source_capture_contract"
                    ),
                    "pending_lifecycle_source_capture_complete": after.get(
                        "pending_lifecycle_source_capture_complete"
                    ),
                    "pending_lifecycle_source_capture_statuses": after.get(
                        "pending_lifecycle_source_capture_statuses"
                    ),
                    "implementation_decision": implementation_decision(after),
                    "exact_r": None,
                    "safe_flags": SAFE_FLAGS,
                    "no_live_behavior": True,
                    "no_shadow_log_append": True,
                }
            )
    return out


def mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    surface_summary: dict[str, Any] = {}
    by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_surface[str(row.get("source_capture_surface") or "")].append(row)

    for surface, surface_rows in sorted(by_surface.items()):
        before_values = [safe_float(row.get("before_proxy_r")) for row in surface_rows]
        after_values = [safe_float(row.get("after_proxy_r")) for row in surface_rows]
        before_numeric = [value for value in before_values if value is not None]
        after_numeric = [value for value in after_values if value is not None]
        surface_summary[surface] = {
            "rows": len(surface_rows),
            "before_numeric_proxy_rows": len(before_numeric),
            "after_numeric_proxy_rows": len(after_numeric),
            "numeric_proxy_row_delta": len(after_numeric) - len(before_numeric),
            "before_proxy_r_mean": mean(before_numeric),
            "after_proxy_r_mean": mean(after_numeric),
            "before_proxy_r_sum": sum(before_numeric),
            "after_proxy_r_sum": sum(after_numeric),
            "proxy_r_sum_delta": sum(after_numeric) - sum(before_numeric),
            "delta_class_counts": dict(Counter(str(row.get("proxy_r_delta_class")) for row in surface_rows)),
            "implementation_decision_counts": dict(
                Counter(str(row.get("implementation_decision")) for row in surface_rows)
            ),
        }

    before_numeric_all = [value for row in rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
    after_numeric_all = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    previous_summary = {}
    if PREVIOUS_SHARED_METADATA_SUMMARY.exists():
        previous_summary = json.loads(PREVIOUS_SHARED_METADATA_SUMMARY.read_text(encoding="utf-8"))
    candidate_entry_buckets: dict[str, str] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if cid and cid not in candidate_entry_buckets:
            candidate_entry_buckets[cid] = str(row.get("entry_retest_redesign_bucket") or "")
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_FVG_STRUCTURAL_SCORER_IMPLEMENTATION_CANDIDATE_RECOMPUTE",
        "claim_boundary": (
            "Current latest-row recompute of stricter default-off FVG-POI and swing-protected-stop scorer "
            "implementation candidates only. Exact broker R is not opened; proxy R is from existing candidate "
            "path, LTF, and pending lifecycle evidence."
        ),
        "priority_strategy_ids": PRIORITY_STRATEGIES,
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "exact_r_rows": 0,
        "before_numeric_proxy_rows": len(before_numeric_all),
        "after_numeric_proxy_rows": len(after_numeric_all),
        "numeric_proxy_row_delta": len(after_numeric_all) - len(before_numeric_all),
        "before_proxy_r_mean": mean(before_numeric_all),
        "after_proxy_r_mean": mean(after_numeric_all),
        "before_proxy_r_sum": sum(before_numeric_all),
        "after_proxy_r_sum": sum(after_numeric_all),
        "proxy_r_sum_delta": sum(after_numeric_all) - sum(before_numeric_all),
        "delta_vs_previous_shared_metadata_checkpoint": {
            "previous_summary_file": PREVIOUS_SHARED_METADATA_SUMMARY.name
            if previous_summary
            else None,
            "previous_after_numeric_proxy_rows": previous_summary.get("after_numeric_proxy_rows"),
            "current_after_numeric_proxy_rows": len(after_numeric_all),
            "after_numeric_proxy_row_delta_vs_previous": (
                len(after_numeric_all) - int(previous_summary.get("after_numeric_proxy_rows", 0))
                if previous_summary
                else None
            ),
            "previous_after_proxy_r_sum": previous_summary.get("after_proxy_r_sum"),
            "current_after_proxy_r_sum": sum(after_numeric_all),
            "after_proxy_r_sum_delta_vs_previous": (
                sum(after_numeric_all) - float(previous_summary.get("after_proxy_r_sum", 0.0))
                if previous_summary
                else None
            ),
        },
        "surface_summary": surface_summary,
        "delta_class_counts": dict(Counter(str(row.get("proxy_r_delta_class")) for row in rows)),
        "implementation_decision_counts": dict(Counter(str(row.get("implementation_decision")) for row in rows)),
        "entry_retest_redesign_bucket_counts": dict(
            Counter(str(row.get("entry_retest_redesign_bucket")) for row in rows)
        ),
        "entry_retest_redesign_candidate_bucket_counts": dict(Counter(candidate_entry_buckets.values())),
        "pending_lifecycle_capture_complete_counts": dict(
            Counter(str(row.get("pending_lifecycle_source_capture_complete")) for row in rows)
        ),
        "safe_flags": SAFE_FLAGS,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def build_manifest() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path): {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in INPUTS.values()
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in [OUTPUT_LEDGER, OUTPUT_SUMMARY]
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summarize(rows))
    write_json(OUTPUT_MANIFEST, build_manifest())
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
