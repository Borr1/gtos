"""Consume repaired structural metadata source rows in the action queue.

This materializes the current structural-lock scorer repair against the latest
source-safe live/shadow rows. It does not append to shadow logs and does not
change live trading behavior.
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


REPO_ROOT = find_repo_root(Path(__file__).resolve())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import (
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    latest_structural_metadata_by_candidate,
    merge_structural_metadata_candidate,
    read_jsonl,
)


DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR_LEDGER_2026-05-17.jsonl"
)
INPUT_STRATEGY_FOLLOW = Path("shadow_logs/strategy_follow_candidates.jsonl")
INPUT_PATH_FOLLOW = Path("shadow_logs/candidate_path_follow.jsonl")
INPUT_PENDING_LIFECYCLE = Path("shadow_logs/pending_limit_lifecycle.jsonl")
INPUT_LTF_PATH_ORDER = Path("shadow_logs/candidate_ltf_path_order.jsonl")
INPUT_STRUCTURAL_METADATA = Path("shadow_logs/live_structural_strategy_metadata.jsonl")

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

TARGET_SOURCE_DECISION = "SOURCE_CAPTURE_REQUIRED_FOR_STRUCTURAL_LOCK_SCORER"
IMPLEMENT_NUMERIC_DECISION = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER_NOW"
IMPLEMENT_AMBIGUITY_DECISION = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_SCORER_WITH_AMBIGUITY_EXCLUSION"
SCORED_STATUS = "SCORED_STRUCTURAL_LOCK_METADATA_PROXY_SHARED_CANDIDATE_PATH"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_utc(value: Any) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def latest_by_candidate(rows: list[dict[str, Any]], *, asof_key: str = "created_at_utc") -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = parse_utc(row.get(asof_key))
        previous = parse_utc(out.get(cid, {}).get(asof_key))
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
        current_created = parse_utc(row.get("created_at_utc"))
        previous_created = parse_utc(out.get(cid, {}).get("created_at_utc"))
        if current_asof > previous_asof or (
            current_asof == previous_asof and current_created >= previous_created
        ):
            out[cid] = row
    return out


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_numeric(value: Any) -> bool:
    return safe_float(value) is not None


def proxy_delta(before: Any, after: Any) -> float | None:
    before_value = safe_float(before)
    after_value = safe_float(after)
    if before_value is None or after_value is None:
        return after_value if before_value is None and after_value is not None else None
    return round(after_value - before_value, 8)


def proxy_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [safe_float(row.get("after_proxy_r")) for row in rows]
    numeric = [value for value in values if value is not None]
    total = sum(numeric)
    return {
        "numeric_proxy_rows": len(numeric),
        "proxy_r_sum": round(total, 8),
        "proxy_r_mean": round(total / len(numeric), 8) if numeric else None,
    }


def metadata_status(metadata: dict[str, Any], field: str) -> Any:
    statuses = metadata.get("structural_source_field_statuses")
    if isinstance(statuses, dict) and statuses.get(field):
        return statuses.get(field)
    fields = metadata.get("captured_structural_source_fields")
    if isinstance(fields, dict):
        payload = fields.get(field)
        if isinstance(payload, dict):
            return payload.get("source_status")
    return None


def cost_geometry_status(enriched_candidate: dict[str, Any], metadata: dict[str, Any]) -> Any:
    structural = enriched_candidate.get("decision_time_structural_fields")
    if isinstance(structural, dict):
        statuses = structural.get("field_statuses")
        if isinstance(statuses, dict) and statuses.get("cost_aware_min_r_fields"):
            return statuses.get("cost_aware_min_r_fields")
        fields = structural.get("fields")
        if isinstance(fields, dict):
            payload = fields.get("cost_aware_min_r_fields")
            if isinstance(payload, dict) and payload.get("source_status"):
                return payload.get("source_status")
    return metadata_status(metadata, "cost_aware_min_r_fields")


def scorer_row_for_target(
    candidate_id: str,
    strategy_id: str,
    candidates: dict[str, dict[str, Any]],
    paths: dict[str, dict[str, Any]],
    structural_metadata: dict[str, dict[str, Any]],
    pending_lifecycle_rows: list[dict[str, Any]],
    ltf_rows: list[dict[str, Any]],
    generated: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    candidate = candidates.get(candidate_id)
    path = paths.get(candidate_id)
    metadata = structural_metadata.get(candidate_id)
    if not candidate or not path or not metadata:
        return None, metadata, candidate
    enriched = merge_structural_metadata_candidate(candidate, metadata)
    pending = latest_lifecycle_for_candidate_asof(enriched, path, pending_lifecycle_rows)
    ltf = latest_ltf_for_candidate_asof(enriched, path, ltf_rows)
    for row in build_strategy_outcome_rows(
        enriched,
        path,
        pending_lifecycle_row=pending,
        ltf_row=ltf,
        created_at_utc=generated,
    ):
        if row.get("strategy_id") == strategy_id:
            return row, metadata, enriched
    return None, metadata, enriched


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_ACTION_LEDGER)
    candidates = latest_by_candidate(read_jsonl(INPUT_STRATEGY_FOLLOW))
    paths = latest_path_by_candidate(read_jsonl(INPUT_PATH_FOLLOW))
    pending_lifecycle_rows = read_jsonl(INPUT_PENDING_LIFECYCLE)
    ltf_rows = read_jsonl(INPUT_LTF_PATH_ORDER)
    structural_metadata_rows = read_jsonl(INPUT_STRUCTURAL_METADATA)
    structural_metadata = latest_structural_metadata_by_candidate(structural_metadata_rows)

    out: list[dict[str, Any]] = []
    target_strategy_counts: Counter[str] = Counter()
    target_strategy_status_counts: Counter[str] = Counter()
    target_score_status_counts: Counter[str] = Counter()
    target_outcome_status_counts: Counter[str] = Counter()
    repair_decision_counts: Counter[str] = Counter()
    missing_context_rows = 0
    repaired_candidate_ids: set[str] = set()
    touched_candidate_ids: set[str] = set()

    for row in source_rows:
        clean = {k: v for k, v in row.items() if k != "_source_line_no"}
        clean["generated_utc"] = generated
        clean["route_id"] = ROUTE_ID
        clean["safe_flags"] = SAFE_FLAGS

        if clean.get("implementation_decision") != TARGET_SOURCE_DECISION:
            clean["structural_metadata_repair_status"] = "NOT_TARGET_ROW"
            out.append(clean)
            continue

        candidate_id = str(clean.get("candidate_id") or "")
        strategy_id = str(clean.get("strategy_id") or "")
        target_strategy_counts[strategy_id] += 1
        touched_candidate_ids.add(candidate_id)
        scorer, metadata, enriched_candidate = scorer_row_for_target(
            candidate_id,
            strategy_id,
            candidates,
            paths,
            structural_metadata,
            pending_lifecycle_rows,
            ltf_rows,
            generated,
        )
        if scorer is None or metadata is None or enriched_candidate is None:
            clean["structural_metadata_repair_status"] = (
                "UNCHANGED_MISSING_CANDIDATE_PATH_OR_STRUCTURAL_METADATA"
            )
            missing_context_rows += 1
            out.append(clean)
            continue

        target_strategy_status_counts[str(scorer.get("strategy_status") or "")] += 1
        target_score_status_counts[str(scorer.get("score_status") or "")] += 1
        target_outcome_status_counts[str(scorer.get("outcome_status") or "")] += 1
        before_proxy = clean.get("after_proxy_r")
        after_proxy = safe_float(scorer.get("strategy_proxy_r"))
        numeric_proxy = after_proxy is not None
        implementation_decision = (
            IMPLEMENT_NUMERIC_DECISION if numeric_proxy else IMPLEMENT_AMBIGUITY_DECISION
        )

        clean.update(
            {
                "structural_metadata_repair_source_file": str(INPUT_STRUCTURAL_METADATA),
                "structural_metadata_created_at_utc": metadata.get("created_at_utc"),
                "structural_metadata_backfilled_at_utc": metadata.get("backfilled_at_utc"),
                "structural_metadata_manual_backfill_status": metadata.get(
                    "manual_backfill_status"
                ),
                "structural_metadata_no_leak_status": metadata.get("no_leak_status"),
                "structural_lock_event_source_status": metadata_status(
                    metadata, "structural_lock_event_time_price"
                ),
                "post_lock_reentry_source_status": metadata_status(
                    metadata, "post_lock_reentry_state"
                ),
                "cost_geometry_source_status": cost_geometry_status(enriched_candidate, metadata),
                "after_strategy_status": scorer.get("strategy_status"),
                "after_score_status": scorer.get("score_status"),
                "after_outcome_status": scorer.get("outcome_status"),
                "after_branch_decision": scorer.get("branch_decision"),
                "after_scoring_boundary": scorer.get("scoring_boundary"),
                "after_implementation_candidate": scorer.get("implementation_candidate"),
                "outcome_source": scorer.get("outcome_source"),
                "decision_evidence": scorer.get("decision_evidence"),
                "after_proxy_r": after_proxy,
                "proxy_r_delta": proxy_delta(before_proxy, after_proxy),
                "no_live_behavior": True,
                "no_shadow_log_append": True,
            }
        )

        if scorer.get("strategy_status") == SCORED_STATUS:
            clean["structural_metadata_repair_status"] = (
                "REPAIRED_STRUCTURAL_METADATA_SHARED_PATH_PROXY"
                if numeric_proxy
                else "REPAIRED_STRUCTURAL_METADATA_SHARED_PATH_AMBIGUITY_EXCLUDED"
            )
            clean["action_class"] = "IMPLEMENT_DEFAULT_OFF"
            clean["coverage_status"] = "IMPLEMENTATION_CANDIDATE_WITH_CURRENT_METADATA_PROXY"
            clean["branch_decision"] = scorer.get("branch_decision")
            clean["implementation_decision"] = implementation_decision
            clean["current_action"] = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER"
            clean["data_requirement_state"] = (
                "CLOSED_BY_LIVE_STRUCTURAL_METADATA_AND_DECISION_TIME_TRADE_PARAMETERS"
            )
            clean["next_action"] = (
                "Implement default-off structural metadata shared-path proxy scorer; keep exact "
                "lock-reentry scorer and broker-R promotion blocked until stronger source-bound outcomes."
                if numeric_proxy
                else "Implement default-off structural metadata scorer with ambiguity exclusion; do not "
                "count ambiguous path rows in numeric proxy-R summaries."
            )
            clean["scoring_boundary"] = scorer.get("scoring_boundary")
            clean["implementation_candidate"] = scorer.get("implementation_candidate")
            repair_decision_counts[implementation_decision] += 1
            repaired_candidate_ids.add(candidate_id)
        else:
            clean["structural_metadata_repair_status"] = "UNCHANGED_UNSUPPORTED_SCORER_STATUS"

        out.append(clean)

    before_actions = Counter(row.get("action_class") for row in source_rows)
    after_actions = Counter(row.get("action_class") for row in out)
    before_decisions = Counter(row.get("implementation_decision") for row in source_rows)
    after_decisions = Counter(row.get("implementation_decision") for row in out)
    before_proxy = proxy_stats(source_rows)
    after_proxy = proxy_stats(out)
    remaining_source_repair_decisions = {
        str(decision): count
        for decision, count in sorted(after_decisions.items())
        if str(decision).startswith("SOURCE_CAPTURE_REQUIRED")
        or str(decision).startswith("SOURCE_REPAIR_REQUIRED")
    }
    summary = {
        "route_id": ROUTE_ID,
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR",
        "generated_utc": generated,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": (
            "Versioned action queue after consuming live structural metadata for structural-lock "
            "shared-path proxy scorers. This opens default-off implementation candidates only; it "
            "does not claim exact broker R, promotion readiness, or live trading behavior."
        ),
        "primitive_coverage_touch": [
            "structural_lock_event_time_price",
            "post_lock_reentry_state",
            "decision_time_trade_parameter_cost_geometry",
            "candidate_m15_path_ordering_proxy",
            "remaining_swing_protected_stop_source_gap",
            "remaining_standalone_fvg_entry_lock_source_gap",
        ],
        "rows": len(out),
        "input_action_rows": len(source_rows),
        "structural_source_repair_rows_before": before_decisions.get(TARGET_SOURCE_DECISION, 0),
        "structural_source_repair_rows_after": after_decisions.get(TARGET_SOURCE_DECISION, 0),
        "remaining_source_repair_rows_after": after_actions.get("SOURCE_REPAIR", 0),
        "remaining_source_repair_decision_counts": remaining_source_repair_decisions,
        "repaired_action_rows": sum(repair_decision_counts.values()),
        "repaired_candidate_ids": len(repaired_candidate_ids),
        "target_candidate_ids": len(touched_candidate_ids),
        "missing_context_rows": missing_context_rows,
        "structural_metadata_rows_seen": len(structural_metadata_rows),
        "structural_metadata_candidates_seen": len(structural_metadata),
        "target_strategy_counts": dict(sorted(target_strategy_counts.items())),
        "target_strategy_status_counts": dict(sorted(target_strategy_status_counts.items())),
        "target_score_status_counts": dict(sorted(target_score_status_counts.items())),
        "target_outcome_status_counts": dict(sorted(target_outcome_status_counts.items())),
        "repair_decision_counts": dict(sorted(repair_decision_counts.items())),
        "before_action_class_counts": dict(sorted(before_actions.items())),
        "action_class_counts": dict(sorted(after_actions.items())),
        "action_class_delta_vs_previous": {
            key: after_actions.get(key, 0) - before_actions.get(key, 0)
            for key in sorted(set(before_actions) | set(after_actions))
            if after_actions.get(key, 0) - before_actions.get(key, 0)
        },
        "before_implementation_decision_counts": dict(sorted(before_decisions.items())),
        "implementation_decision_counts": dict(sorted(after_decisions.items())),
        "proxy_before": before_proxy,
        "proxy_after": after_proxy,
        "numeric_proxy_row_delta": after_proxy["numeric_proxy_rows"]
        - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "exact_r_rows": 0,
        "plate_decision": "STRUCTURAL_METADATA_SOURCE_REPAIR_CONSUMED_AS_DEFAULT_OFF_SCORER_OUTPUTS",
    }
    return out, summary


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "input_action_ledger": INPUT_ACTION_LEDGER,
        "strategy_follow_candidates": INPUT_STRATEGY_FOLLOW,
        "candidate_path_follow": INPUT_PATH_FOLLOW,
        "pending_limit_lifecycle": INPUT_PENDING_LIFECYCLE,
        "candidate_ltf_path_order": INPUT_LTF_PATH_ORDER,
        "live_structural_strategy_metadata": INPUT_STRUCTURAL_METADATA,
    }
    outputs = {
        "ledger": OUTPUT_LEDGER,
        "summary": OUTPUT_SUMMARY,
    }
    return {
        "route_id": ROUTE_ID,
        "evidence_class": summary["evidence_class"],
        "generated_utc": summary["generated_utc"],
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else None,
            }
            for name, path in inputs.items()
        },
        "outputs": {
            name: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for name, path in outputs.items()
        },
        "summary_counts": {
            "rows": summary["rows"],
            "repaired_action_rows": summary["repaired_action_rows"],
            "remaining_source_repair_rows_after": summary["remaining_source_repair_rows_after"],
            "numeric_proxy_row_delta": summary["numeric_proxy_row_delta"],
            "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(
        json.dumps(
            {
                "ok": True,
                "rows": summary["rows"],
                "repaired_action_rows": summary["repaired_action_rows"],
                "remaining_source_repair_rows_after": summary[
                    "remaining_source_repair_rows_after"
                ],
                "numeric_proxy_row_delta": summary["numeric_proxy_row_delta"],
                "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
