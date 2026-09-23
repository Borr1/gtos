"""Materialize FVG/OB source-bucket scorer decisions.

This plate consumes the current live FVG/OB bucket source and structural
metadata before recomputing the FVG/OB and standalone-FVG scorer surfaces. It
turns generic captured-metadata FVG/OB rows into row-level keep/kill/redesign
decisions from the current source scorer rather than carrying broad default-off
labels forward.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(ROUTE_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    FVG_OB_CONFLUENCE_ID,
    FVG_REQUIRED_IDS,
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    latest_structural_metadata_by_candidate,
    merge_structural_metadata_candidate,
    read_jsonl as read_shadow_jsonl,
)


INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_SUMMARY_{DATE}.json"
SCORER_SOURCE = REPO_ROOT / "src/research_infra/live_mechanical_shadow.py"
TEST_SOURCE = REPO_ROOT / "tests/test_live_mechanical_shadow.py"

SHADOW_INPUTS = {
    "strategy_follow_candidates": REPO_ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
    "candidate_path_follow": REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl",
    "pending_limit_lifecycle": REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
    "candidate_ltf_path_order": REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl",
    "live_structural_strategy_metadata": REPO_ROOT / "shadow_logs/live_structural_strategy_metadata.jsonl",
    "fvg_ob_confluence": REPO_ROOT / "shadow_logs/fvg_ob_confluence.jsonl",
}

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_SOURCE_BUCKET_SCORER_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_SOURCE_BUCKET_SCORER_DECISION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_SOURCE_BUCKET_SCORER_DECISION_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FVG_OB_SOURCE_KILL_BRANCH = "KILL_ROW_NOT_FVG_OB_CONFLUENCE"
FVG_OB_BOTH_FIRE_BRANCH = "IMPLEMENT_SHADOW_SCORER_FVG_OB_BUCKET_DEFAULT_OFF_WITH_EXACT_BOUNDS_MISSING"
STANDALONE_FVG_SOURCE_BRANCH = "IMPLEMENT_SHADOW_SCORER_STANDALONE_FVG_POI_DEFAULT_OFF"
STANDALONE_FVG_SOURCE_REQUIRED_BRANCH = "SOURCE_CAPTURE_REQUIRED_FOR_FVG_SCORER"
STANDALONE_FVG_KILL_BRANCH = "KILL_ROW_NOT_STANDALONE_FVG_POI"
STANDALONE_FVG_NEGATIVE_REDESIGN_BRANCH = (
    "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N_AFTER_SOURCE_RECOMPUTE"
)
TARGET_STRATEGY_IDS = {FVG_OB_CONFLUENCE_ID, *FVG_REQUIRED_IDS}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter("" if row.get(field) is None else str(row.get(field)) for row in rows))


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        observed = (
            parse_utc(row.get("created_at_utc"))
            or parse_utc(row.get("backfilled_at_utc"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        previous = latest.get(cid)
        if previous is None or (observed, idx) >= (previous[0], previous[1]):
            latest[cid] = (observed, idx, row)
    return {cid: item[2] for cid, item in latest.items()}


def latest_path_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[datetime, datetime, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        asof = parse_utc(row.get("asof_latest_candle_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        observed = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous = latest.get(cid)
        if previous is None or (asof, observed, idx) >= (previous[0], previous[1], previous[2]):
            latest[cid] = (asof, observed, idx, row)
    return {cid: item[3] for cid, item in latest.items()}


def build_strategy_recompute_map(generated_utc: str) -> dict[tuple[str, str], dict[str, Any]]:
    candidates = latest_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["candidate_path_follow"]))
    pending_lifecycle_rows = read_shadow_jsonl(SHADOW_INPUTS["pending_limit_lifecycle"])
    ltf_rows = read_shadow_jsonl(SHADOW_INPUTS["candidate_ltf_path_order"])
    structural_metadata = latest_structural_metadata_by_candidate(
        read_shadow_jsonl(SHADOW_INPUTS["live_structural_strategy_metadata"])
    )
    fvg_ob_context = latest_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["fvg_ob_confluence"]))
    recomputed: dict[tuple[str, str], dict[str, Any]] = {}
    for cid in sorted(candidates):
        candidate = merge_structural_metadata_candidate(candidates[cid], structural_metadata.get(cid))
        bucket_row = fvg_ob_context.get(cid)
        if bucket_row:
            candidate = {
                **candidate,
                "fvg_ob_confluence_context": {
                    "bucket": bucket_row.get("bucket"),
                    "created_at_utc": bucket_row.get("created_at_utc"),
                    "source_file": bucket_row.get("source_file"),
                },
            }
        path = paths.get(cid)
        if not path:
            continue
        pending = latest_lifecycle_for_candidate_asof(candidate, path, pending_lifecycle_rows)
        ltf = latest_ltf_for_candidate_asof(candidate, path, ltf_rows)
        for row in build_strategy_outcome_rows(
            candidate,
            path,
            pending_lifecycle_row=pending,
            ltf_row=ltf,
            created_at_utc=generated_utc,
        ):
            key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
            recomputed[key] = row
    return recomputed


def mark_before(row: dict[str, Any]) -> None:
    for field in (
        "action_class",
        "coverage_status",
        "branch_decision",
        "decision_evidence",
        "scoring_boundary",
        "implementation_candidate",
        "implementation_decision",
        "current_action",
        "next_action",
        "after_proxy_r",
    ):
        row[f"before_fvg_ob_source_bucket_{field}"] = row.get(field)


def apply_source_fields(row: dict[str, Any], scorer_row: dict[str, Any]) -> None:
    row["fvg_ob_source_bucket_scorer_source"] = "src/research_infra/live_mechanical_shadow.py"
    row["source_scorer_branch_decision"] = scorer_row.get("branch_decision")
    row["source_scorer_decision_evidence"] = scorer_row.get("decision_evidence")
    row["source_scorer_scoring_boundary"] = scorer_row.get("scoring_boundary")
    row["source_scorer_implementation_candidate"] = scorer_row.get("implementation_candidate")
    row["source_scorer_strategy_status"] = scorer_row.get("strategy_status")
    row["source_scorer_score_status"] = scorer_row.get("score_status")
    row["source_scorer_outcome_status"] = scorer_row.get("outcome_status")
    row["source_scorer_proxy_r"] = scorer_row.get("strategy_proxy_r")
    row["after_proxy_r"] = scorer_row.get("strategy_proxy_r")
    for field in (
        "fvg_ob_confluence_bucket",
        "fvg_ob_confluence_bucket_source_status",
        "standalone_fvg_source_status",
        "standalone_fvg_poi_status",
        "standalone_fvg_poi_type",
        "standalone_fvg_entry_inside_gap",
        "standalone_fvg_matching_gap_timeframes",
    ):
        if field in scorer_row:
            row[field] = scorer_row.get(field)
    for field in (
        "claim_decision_scope",
        "underlying_intelligence_preserved",
        "missed_opportunity_audit",
        "current_claim_proxy_counted",
        "preserved_candidate_path_proxy_r",
        "preserved_candidate_path_outcome_source",
        "preserved_candidate_path_outcome_status",
    ):
        if field in scorer_row:
            row[field] = scorer_row.get(field)


def apply_final_decision(row: dict[str, Any], *, action_class: str, coverage_status: str, branch_decision: str,
                         decision_evidence: str, scoring_boundary: str, implementation_candidate: str,
                         current_action: str | None = None, next_action: str | None = None) -> None:
    row["action_class"] = action_class
    row["coverage_status"] = coverage_status
    row["branch_decision"] = branch_decision
    row["decision_evidence"] = decision_evidence
    row["scoring_boundary"] = scoring_boundary
    row["implementation_candidate"] = implementation_candidate
    row["implementation_decision"] = branch_decision
    row["current_action"] = current_action or implementation_candidate
    row["next_action"] = next_action or implementation_candidate


def materialize_rows(
    rows: list[dict[str, Any]],
    recomputed: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        strategy_id = str(row.get("strategy_id") or "")
        if strategy_id not in TARGET_STRATEGY_IDS:
            row["fvg_ob_source_bucket_scorer_decision_status"] = "NOT_TARGET_ROW"
            output.append(row)
            continue

        stats["target_rows"] += 1
        mark_before(row)
        key = (str(row.get("candidate_id") or ""), strategy_id)
        scorer_row = recomputed.get(key)
        if not scorer_row:
            row["fvg_ob_source_bucket_scorer_decision_status"] = "RECOMPUTE_ROW_MISSING"
            stats["target_recompute_missing"] += 1
            output.append(row)
            continue
        apply_source_fields(row, scorer_row)
        source_branch = str(scorer_row.get("branch_decision") or "")

        if strategy_id == FVG_OB_CONFLUENCE_ID and source_branch == FVG_OB_SOURCE_KILL_BRANCH:
            row["fvg_ob_source_bucket_scorer_decision_status"] = "FVG_OB_BUCKET_KILL_APPLIED"
            apply_final_decision(
                row,
                action_class="KILL",
                coverage_status="KILLED_BY_SOURCE_BUCKET",
                branch_decision=FVG_OB_SOURCE_KILL_BRANCH,
                decision_evidence=str(scorer_row.get("decision_evidence") or ""),
                scoring_boundary=str(scorer_row.get("scoring_boundary") or ""),
                implementation_candidate=str(scorer_row.get("implementation_candidate") or ""),
            )
            stats["fvg_ob_bucket_kill_applied"] += 1
        elif strategy_id == FVG_OB_CONFLUENCE_ID and source_branch == FVG_OB_BOTH_FIRE_BRANCH:
            row["fvg_ob_source_bucket_scorer_decision_status"] = "FVG_OB_BOTH_FIRE_BUCKET_KEEP_DEFAULT_OFF"
            row["claim_decision_scope"] = "CURRENT_FVG_OB_BOTH_FIRE_BUCKET_CLAIM_PRESERVED_DEFAULT_OFF"
            row["underlying_intelligence_preserved"] = True
            row["current_claim_proxy_counted"] = row.get("after_proxy_r") is not None
            row["missed_opportunity_audit"] = {
                "decision_scope": "KEEP_DEFAULT_OFF_CURRENT_CLAIM",
                "what_was_tried": "RECOMPUTED_WITH_FVG_OB_BOTH_FIRE_BUCKET_SOURCE",
                "what_could_make_it_work": (
                    "EXACT_FVG_AND_OB_BOUNDS_WITH_ENTRY_LOCK_COST_AND_FILLABILITY_REPLAY"
                ),
                "preserve_as": "DEFAULT_OFF_BUCKET_ONLY_FVG_OB_CONFLUENCE_PROXY",
                "next_route": "ADD_EXACT_BOUNDS_AND_REPLAY_BEFORE_ANY_STRONGER_FVG_OB_CLAIM",
            }
            apply_final_decision(
                row,
                action_class="KEEP",
                coverage_status="KEPT_WITH_CURRENT_EVIDENCE",
                branch_decision=FVG_OB_BOTH_FIRE_BRANCH,
                decision_evidence=str(scorer_row.get("decision_evidence") or ""),
                scoring_boundary=str(scorer_row.get("scoring_boundary") or ""),
                implementation_candidate=str(scorer_row.get("implementation_candidate") or ""),
                current_action=str(scorer_row.get("implementation_candidate") or ""),
                next_action="Keep bucket-only FVG/OB confluence proxy default-off; exact bounds required for stronger claims.",
            )
            stats["fvg_ob_both_fire_keep_default_off"] += 1
        elif strategy_id in FVG_REQUIRED_IDS and source_branch == STANDALONE_FVG_KILL_BRANCH:
            row["fvg_ob_source_bucket_scorer_decision_status"] = "STANDALONE_FVG_NON_FVG_KILL_PRESERVED"
            apply_final_decision(
                row,
                action_class="KILL",
                coverage_status="KILLED_BY_SELECTED_POI_SOURCE",
                branch_decision=STANDALONE_FVG_KILL_BRANCH,
                decision_evidence=str(scorer_row.get("decision_evidence") or ""),
                scoring_boundary=str(scorer_row.get("scoring_boundary") or ""),
                implementation_candidate=str(scorer_row.get("implementation_candidate") or ""),
            )
            stats["standalone_fvg_non_fvg_kill_preserved"] += 1
        elif strategy_id in FVG_REQUIRED_IDS and source_branch == STANDALONE_FVG_SOURCE_BRANCH:
            row["fvg_ob_source_bucket_scorer_decision_status"] = (
                "STANDALONE_FVG_SOURCE_ELIGIBLE_REDESIGN_CURRENT_PROXY_NEGATIVE"
            )
            row["claim_decision_scope"] = "SOURCE_ELIGIBLE_STANDALONE_FVG_CLAIM_REDESIGN_NOT_KILL"
            row["underlying_intelligence_preserved"] = True
            row["current_claim_proxy_counted"] = row.get("after_proxy_r") is not None
            row["missed_opportunity_audit"] = {
                "decision_scope": "REDESIGN_CURRENT_CLAIM",
                "what_was_tried": (
                    "RECOMPUTED_STANDALONE_FVG_POI_ROWS_WITH_STRUCTURAL_METADATA_AND_CANDIDATE_PATH_PROXY"
                ),
                "why_not_default_off": "CURRENT_SOURCE_ELIGIBLE_PROXY_SUBSET_NEGATIVE_SMALL_N",
                "what_could_make_it_work": (
                    "FVG_ENTRY_SELECTOR_WITH_LOCK_PATH_COST_FILLABILITY_AND_SYMBOL_SESSION_SPECIALIZATION"
                ),
                "preserve_as": "STANDALONE_FVG_SELECTOR_REDESIGN_AND_CONTEXT_FEATURE",
                "next_route": (
                    "ISOLATE_FVG_POI_BY_SYMBOL_SESSION_TIMEFRAME_AND_REPLAY_ENTRY_LOCK_COST_FILLABILITY"
                ),
            }
            apply_final_decision(
                row,
                action_class="REDESIGN",
                coverage_status="QUEUED_FOR_REDESIGN",
                branch_decision=STANDALONE_FVG_NEGATIVE_REDESIGN_BRANCH,
                decision_evidence="SOURCE_ELIGIBLE_STANDALONE_FVG_POI_PROXY_ROWS_CURRENTLY_NEGATIVE_SMALL_N",
                scoring_boundary=(
                    "NO_STANDALONE_FVG_DEFAULT_OFF_IMPLEMENTATION_WITH_CURRENT_NEGATIVE_SMALL_N_SOURCE_RECOMPUTED_PROXY"
                ),
                implementation_candidate="REDESIGN_STANDALONE_FVG_ENTRY_SELECTOR_BEFORE_DEFAULT_OFF_IMPLEMENTATION",
            )
            stats["standalone_fvg_source_eligible_redesign"] += 1
        elif strategy_id in FVG_REQUIRED_IDS and source_branch == STANDALONE_FVG_SOURCE_REQUIRED_BRANCH:
            row["fvg_ob_source_bucket_scorer_decision_status"] = "STANDALONE_FVG_SOURCE_REQUIREMENT_PRESERVED"
            row["claim_decision_scope"] = "SOURCE_INCOMPLETE_STANDALONE_FVG_CLAIM_PRESERVED_FOR_REPAIR"
            row["underlying_intelligence_preserved"] = True
            row["current_claim_proxy_counted"] = False
            row["missed_opportunity_audit"] = {
                "decision_scope": "PRESERVE_SOURCE_REQUIREMENT",
                "what_was_tried": (
                    "RECOMPUTED_STANDALONE_FVG_POI_ROWS_WITH_CURRENT_STRUCTURAL_METADATA"
                ),
                "why_not_killed": "SOURCE_GEOMETRY_INCOMPLETE_SAME_EVIDENCE_REPAIR_NOT_EXHAUSTED",
                "what_could_make_it_work": (
                    "CAPTURE_STANDALONE_FVG_ENTRY_LOCK_AND_POST_LOCK_REENTRY_FIELDS"
                ),
                "preserve_as": "SOURCE_CAPTURE_REQUIREMENT_AND_FVG_SELECTOR_REPAIR_QUEUE",
                "next_route": "REPAIR_FVG_ENTRY_LOCK_SOURCE_CAPTURE_OR_REPLAY_WITH_EXACT_FVG_BOUNDS",
            }
            apply_final_decision(
                row,
                action_class="PRESERVE_REQUIREMENT",
                coverage_status="SOURCE_REQUIREMENT_PRESERVED",
                branch_decision=STANDALONE_FVG_SOURCE_REQUIRED_BRANCH,
                decision_evidence=str(scorer_row.get("decision_evidence") or ""),
                scoring_boundary=str(scorer_row.get("scoring_boundary") or ""),
                implementation_candidate=str(scorer_row.get("implementation_candidate") or ""),
            )
            stats["standalone_fvg_source_requirement_preserved"] += 1
        else:
            row["fvg_ob_source_bucket_scorer_decision_status"] = "UNHANDLED_SOURCE_SCORER_BRANCH"
            stats["unhandled_source_scorer_branch"] += 1
        if row.get("before_fvg_ob_source_bucket_branch_decision") != row.get("branch_decision"):
            stats["target_branch_decision_changed"] += 1
        if row.get("before_fvg_ob_source_bucket_action_class") != row.get("action_class"):
            stats["target_action_class_changed"] += 1
        if safe_float(row.get("before_fvg_ob_source_bucket_after_proxy_r")) != safe_float(row.get("after_proxy_r")):
            stats["target_proxy_r_changed"] += 1
        output.append(row)
    return output, dict(stats)


def target_proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target = [row for row in rows if str(row.get("strategy_id") or "") in TARGET_STRATEGY_IDS]
    values = [value for row in target if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "target_rows": len(target),
        "target_numeric_proxy_rows": len(values),
        "target_proxy_r_sum": round(sum(values), 8),
        "target_strategy_counts": counter(target, "strategy_id"),
        "target_branch_counts": counter(target, "branch_decision"),
    }


def far_miss_invariants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_branch = "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_CHALLENGER"
    kill_branch = "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
    entry_rows = [row for row in rows if row.get("branch_decision") == entry_branch]
    killed_rows = [row for row in rows if row.get("branch_decision") == kill_branch]
    entry_values = [safe_float(row.get("after_proxy_r")) for row in entry_rows]
    entry_values = [value for value in entry_values if value is not None]
    return {
        "entry_default_off_candidates": len({row.get("candidate_id") for row in entry_rows}),
        "entry_default_off_numeric_proxy_rows": len(entry_values),
        "entry_default_off_proxy_r_sum": round(sum(entry_values), 8),
        "killed_far_miss_rows": len(killed_rows),
        "killed_far_miss_candidates": len({row.get("candidate_id") for row in killed_rows}),
    }


def tick_structural_invariants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = counter(rows, "tick_structural_derivation_repair_status")
    converted = sum(
        count
        for status, count in counts.items()
        if status not in {"", "None", "NOT_TARGET_ROW"}
    )
    return {
        "tick_structural_converted_rows": converted,
        "tick_structural_status_counts": counts,
    }


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY, SCORER_SOURCE, TEST_SOURCE, *SHADOW_INPUTS.values()]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path.relative_to(REPO_ROOT)): {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in inputs
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in output_paths
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    recomputed = build_strategy_recompute_map(utc_now())
    output_rows, stats = materialize_rows(input_rows, recomputed)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    before_target = target_proxy_summary(input_rows)
    after_target = target_proxy_summary(output_rows)
    target_rows = [row for row in output_rows if str(row.get("strategy_id") or "") in TARGET_STRATEGY_IDS]
    claim_only_kill_rows = [
        row
        for row in target_rows
        if row.get("action_class") == "KILL"
        and row.get("claim_decision_scope")
        == "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
        and row.get("underlying_intelligence_preserved") is True
        and isinstance(row.get("missed_opportunity_audit"), dict)
    ]
    preserved_path_proxy_values = [
        value
        for row in claim_only_kill_rows
        if (value := safe_float(row.get("preserved_candidate_path_proxy_r"))) is not None
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_FVG_OB_SOURCE_BUCKET_SCORER_DECISION",
        "claim_boundary": (
            "Current FVG/OB and standalone-FVG scorer decisions after consuming live FVG/OB bucket source "
            "and structural metadata. This changes row-level action/result decisions only; it opens no "
            "promotion, validation-safe claim, exact-R claim, live behavior, broker operation, or AI/API call."
        ),
        "rows": len(output_rows),
        "target_rows": len(target_rows),
        "target_strategy_counts": counter(target_rows, "strategy_id"),
        "decision_stats": stats,
        "status_counts": counter(output_rows, "fvg_ob_source_bucket_scorer_decision_status"),
        "source_scorer_branch_counts": counter(target_rows, "source_scorer_branch_decision"),
        "current_claim_only_kill_preservation": {
            "kill_rows": sum(1 for row in target_rows if row.get("action_class") == "KILL"),
            "claim_only_kill_rows_with_audit": len(claim_only_kill_rows),
            "preserved_underlying_proxy_rows": len(preserved_path_proxy_values),
            "preserved_underlying_proxy_r_sum": round(sum(preserved_path_proxy_values), 8),
            "scope": "KILL_ONLY_UNSUPPORTED_CURRENT_CLAIM_NOT_UNDERLYING_MECHANISM",
        },
        "before_target_proxy_summary": before_target,
        "after_target_proxy_summary": after_target,
        "target_proxy_r_delta": round(
            after_target["target_proxy_r_sum"] - before_target["target_proxy_r_sum"], 8
        ),
        "before_action_class_counts": input_summary.get("action_class_counts_after"),
        "after_action_class_counts": counter(output_rows, "action_class"),
        "all_metadata_gaps_after": sum(1 for row in output_rows if has_metadata_gap(row)),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "far_miss_retest_control_invariants": far_miss_invariants(output_rows),
        "tick_structural_source_repair_invariants": tick_structural_invariants(output_rows),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "FVG_OB_BUCKET_SOURCE_KILLS_GENERIC_CONFLUENCE_ROWS_AND_REDIRECTS_STANDALONE_FVG",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "target_rows": len(target_rows),
                "proxy_r_sum_after": summary["proxy_r_sum_after"],
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
