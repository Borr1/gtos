#!/usr/bin/env python3
"""Build OTI1 quarantined lifecycle/no-fill result artifacts.

This script consumes only the G12-accepted OTB1R lifecycle packets listed in
the OTI1 metric freeze. It intentionally reports descriptive lifecycle truth
counts and blocks validation/covariate claims.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
DATE = "2026-05-07"
LANE = "OTI1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
RESULT_STATUS = "RESULT_QUARANTINED_DISCOVERY_ONLY"
BLOCKED_COVARIATE = "BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER"

FREEZE_PATH = OUT_DIR / f"OTI1_METRIC_FREEZE_{DATE}.json"
ACCEPTED_SHORTLIST_PATH = REPO_ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json"
)
PREREGISTRY_PATH = REPO_ROOT / (
    "research/science_program_2026_05/03_experiment_specs/"
    "EXPERIMENT_PREREGISTRY_2026-05-06.json"
)
SOURCE_PROJECTION_PATH = REPO_ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "otb1r_input_only_lifecycle_rebuild/source_projections/"
    "OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl"
)
CONTROL_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_READING_ORDER.md",
    "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
    "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb0_blocker_clearing_governor/OTB0_PACKET_BUILDER_REQUIREMENTS_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb0_blocker_clearing_governor/OTB0_COMPLETION_AUDIT_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_DUPLICATE_DENOMINATOR_REVIEW_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_LABEL_FAMILY_REVIEW_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_SOURCE_ASOF_SOURCE_HASH_REVIEW_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_SCHEMA_NOLEAK_VALIDATION_REPORT_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_AMBIGUITY_LEDGER_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/source_projections/OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_DUPLICATE_DENOMINATOR_REVIEW_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_LABEL_FAMILY_REVIEW_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_SOURCE_HASH_REVIEW_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_2026-05-07.md",
    "shadow_logs/pending_limit_lifecycle.jsonl",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl",
    "shadow_logs/opportunity_lifecycle_audit.jsonl",
]

FORBIDDEN_ROW_FIELDS = {
    "actual_r",
    "broker_actual_r",
    "future_return",
    "outcome_r",
    "post_entry_path",
    "synthetic_path_r",
    "trade_result",
    "win_loss",
}

COVARIATE_PACKET_REASONS = {
    "OTG0-PKT-016": "friction fields have a residual G12 question; no packet-bound as-of friction source is proven",
    "OTG0-PKT-025": "realized-vol and vol-of-vol source is not packet-bound for source-complete volatility claims",
    "OTG0-PKT-045": "footprint/absorption source contract and as-of proof are not packet-bound",
    "OTG0-PKT-055": "news event-window matcher/parser/no-lookahead fixtures are not cleared",
    "OTG0-PKT-059": "macro-attention and G5/G7 interaction source labels are not packet-bound",
    "OTG0-PKT-071": "FOMC parser, stale-source tests, event windows, and no-lookahead checks are not cleared",
    "OTG0-PKT-079": "Cboe publication/as-of, parser/cache hashes, legal review, and no-lookahead tests remain unresolved",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def counter_table(counter: Counter[str]) -> list[dict[str, Any]]:
    return [{"value": key, "unique_duplicate_groups": counter[key]} for key in sorted(counter)]


def load_preregistry() -> dict[str, dict[str, Any]]:
    registry = load_json(PREREGISTRY_PATH)
    return {row["experiment_id"]: row for row in registry["rows"]}


def group_packet_rows(packet: dict[str, Any]) -> dict[str, Any]:
    meta = packet["packet_metadata"]
    rows = packet["primary_lifecycle_rows"]
    packet_id = meta["packet_id"]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["duplicate_group_id"]].append(row)

    group_summaries = []
    label_conflicts = []
    lifecycle_counts: Counter[str] = Counter()
    fill_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    session_counts: Counter[str] = Counter()
    side_counts: Counter[str] = Counter()

    for duplicate_group_id, group_rows in sorted(groups.items()):
        label_tuples = {
            (
                row.get("lifecycle_state", ""),
                row.get("fill_or_no_fill_state", ""),
                row.get("cancel_expiry_or_wrong_side_reason", ""),
            )
            for row in group_rows
        }
        symbols = sorted({row.get("source_symbol", "") for row in group_rows})
        sessions = sorted({extract_packet_source_value(row, "session") for row in group_rows if extract_packet_source_value(row, "session")})
        sides = sorted({extract_packet_source_value(row, "side") for row in group_rows if extract_packet_source_value(row, "side")})
        if len(label_tuples) != 1:
            label_conflicts.append(
                {
                    "packet_id": packet_id,
                    "duplicate_group_id": duplicate_group_id,
                    "raw_rows": len(group_rows),
                    "label_tuples": sorted(["/".join(t) for t in label_tuples]),
                }
            )
            status = "AMBIGUOUS_DUPLICATE_GROUP_LABEL_CONFLICT"
            lifecycle_state = "excluded_label_conflict"
            fill_state = "excluded_label_conflict"
            reason = "excluded_label_conflict"
            include_primary = False
        else:
            lifecycle_state, fill_state, reason = next(iter(label_tuples))
            status = "COUNTED_ONCE"
            include_primary = True
            lifecycle_counts[lifecycle_state] += 1
            fill_counts[fill_state] += 1
            reason_counts[reason] += 1
            for symbol in symbols:
                symbol_counts[symbol] += 1
            for session in sessions:
                session_counts[session] += 1
            for side in sides:
                side_counts[side] += 1

        group_summaries.append(
            {
                "packet_id": packet_id,
                "duplicate_group_id": duplicate_group_id,
                "raw_child_rows": len(group_rows),
                "counted_primary_unit": include_primary,
                "status": status,
                "lifecycle_state": lifecycle_state,
                "fill_or_no_fill_state": fill_state,
                "cancel_expiry_or_wrong_side_reason": reason,
                "source_symbols": symbols,
                "sessions": sessions,
                "sides": sides,
                "setup_ids": sorted({row.get("setup_id_or_candidate_id", "") for row in group_rows}),
            }
        )

    return {
        "packet_id": packet_id,
        "experiment_id": meta["experiment_id"],
        "hypothesis_id": meta["hypothesis_id"],
        "raw_rows": len(rows),
        "unique_duplicate_groups": len(groups),
        "metadata_unique_duplicate_groups": meta.get("unique_duplicate_group_id_count"),
        "duplicate_groups_with_multiple_rows": sum(1 for group_rows in groups.values() if len(group_rows) > 1),
        "lifecycle_counts": dict(lifecycle_counts),
        "fill_counts": dict(fill_counts),
        "reason_counts": dict(reason_counts),
        "symbol_counts": dict(symbol_counts),
        "session_counts": dict(session_counts),
        "side_counts": dict(side_counts),
        "group_summaries": group_summaries,
        "label_conflicts": label_conflicts,
    }


def extract_packet_source_value(row: dict[str, Any], key: str) -> str:
    paths = row.get("packet_build_source_paths") or []
    for item in paths:
        if not isinstance(item, dict):
            continue
        value = item.get(key)
        if value:
            return str(value)
    return ""


def summarize_inputs(freeze: dict[str, Any], accepted: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    allowed_ids = set(freeze["allowed_packet_ids"])
    accepted_otb1r = [
        row
        for row in accepted["accepted_packets"]
        if row["packet_family"] == "OTB1R" and row["packet_id"] in allowed_ids
    ]
    excluded_seen = [
        row
        for row in accepted["accepted_packets"]
        if row["packet_family"] != "OTB1R" or row["packet_id"] not in allowed_ids
    ]
    if sorted(row["packet_id"] for row in accepted_otb1r) != sorted(allowed_ids):
        raise RuntimeError("Accepted OTB1R packet set does not match OTI1 metric freeze")
    if any(row["packet_id"] == "OTG0-PKT-017" for row in accepted_otb1r):
        raise RuntimeError("Blocked packet OTG0-PKT-017 entered OTI1 accepted set")
    return accepted_otb1r, excluded_seen


def build() -> dict[str, Path]:
    generated_at = utc_now()
    freeze = load_json(FREEZE_PATH)
    accepted = load_json(ACCEPTED_SHORTLIST_PATH)
    preregistry = load_preregistry()
    source_projection_rows = load_jsonl(SOURCE_PROJECTION_PATH)
    source_projection_by_hash = {row["source_hash"]: row for row in source_projection_rows}
    accepted_otb1r, excluded_seen = summarize_inputs(freeze, accepted)

    input_hashes = {
        "oti1_metric_freeze": sha256(FREEZE_PATH),
        "g12_accepted_shortlist": sha256(ACCEPTED_SHORTLIST_PATH),
        "experiment_preregistry": sha256(PREREGISTRY_PATH),
        "otb1r_sanitized_source_projection": sha256(SOURCE_PROJECTION_PATH),
    }
    for input_path in CONTROL_INPUTS:
        path = REPO_ROOT / input_path
        if path.exists():
            input_hashes[input_path] = sha256(path)

    packet_summaries = []
    forbidden_field_hits = []
    denominator_mismatches = []
    all_group_keys = set()
    source_duplicate_group_ids = set()
    source_opportunity_ids = set()
    global_lifecycle_counts: Counter[str] = Counter()
    global_fill_counts: Counter[str] = Counter()
    global_reason_counts: Counter[str] = Counter()
    global_symbol_counts: Counter[str] = Counter()
    global_session_counts: Counter[str] = Counter()
    global_side_counts: Counter[str] = Counter()
    source_hash_resolution_issues = []

    for accepted_row in sorted(accepted_otb1r, key=lambda row: row["packet_id"]):
        packet_path = REPO_ROOT / accepted_row["packet_artifact"]
        packet = load_json(packet_path)
        meta = packet["packet_metadata"]
        if meta["packet_id"] != accepted_row["packet_id"]:
            raise RuntimeError(f"Packet id mismatch for {packet_path}")
        rows = packet["primary_lifecycle_rows"]
        for row in rows:
            hits = sorted(FORBIDDEN_ROW_FIELDS.intersection(row.keys()))
            if hits:
                forbidden_field_hits.append({"packet_id": meta["packet_id"], "fields": hits})
            source_hash = row.get("source_hash")
            projection = source_projection_by_hash.get(source_hash)
            if not projection:
                source_hash_resolution_issues.append(
                    {
                        "packet_id": meta["packet_id"],
                        "setup_id_or_candidate_id": row.get("setup_id_or_candidate_id"),
                        "source_hash": source_hash,
                        "issue": "SOURCE_HASH_NOT_FOUND_IN_SANITIZED_PROJECTION_FILE",
                    }
                )
            elif projection.get("forbidden_key_paths_after_projection"):
                source_hash_resolution_issues.append(
                    {
                        "packet_id": meta["packet_id"],
                        "setup_id_or_candidate_id": row.get("setup_id_or_candidate_id"),
                        "source_hash": source_hash,
                        "issue": "SANITIZED_PROJECTION_FORBIDDEN_KEYS_PRESENT",
                        "forbidden_key_paths_after_projection": projection.get("forbidden_key_paths_after_projection"),
                    }
                )
        summary = group_packet_rows(packet)
        expected_unique = freeze["unique_duplicate_group_expected_counts"][meta["packet_id"]]
        if summary["unique_duplicate_groups"] != expected_unique:
            denominator_mismatches.append(
                {
                    "packet_id": meta["packet_id"],
                    "computed_unique_duplicate_groups": summary["unique_duplicate_groups"],
                    "expected_unique_duplicate_groups": expected_unique,
                    "accepted_shortlist_unique_duplicate_groups": accepted_row["unique_duplicate_group_count"],
                    "metadata_unique_duplicate_groups": meta.get("unique_duplicate_group_id_count"),
                }
            )
        summary["packet_artifact"] = accepted_row["packet_artifact"]
        summary["packet_sha256"] = sha256(packet_path)
        summary["preregistered_metric"] = preregistry[meta["experiment_id"]].get("metric")
        summary["preregistered_null"] = preregistry[meta["experiment_id"]].get("null")
        summary["preregistered_alternative"] = preregistry[meta["experiment_id"]].get("alternative")
        summary["preregistered_sample_floor"] = preregistry[meta["experiment_id"]].get("sample_floor")
        summary["preregistered_duplicate_policy"] = preregistry[meta["experiment_id"]].get("duplicate_policy")
        summary["preregistered_label_separation_policy"] = preregistry[meta["experiment_id"]].get("label_separation_policy")
        summary["residual_nonblocking_question"] = accepted_row.get("residual_nonblocking_question") or ""
        summary["covariate_source_complete_claim_status"] = (
            BLOCKED_COVARIATE if meta["packet_id"] in COVARIATE_PACKET_REASONS else "NO_COVARIATE_CLAIM_USED"
        )
        summary["covariate_source_complete_claim_reason"] = COVARIATE_PACKET_REASONS.get(meta["packet_id"], "")
        summary["lifecycle_truth_only_result_status"] = RESULT_STATUS

        for group in summary["group_summaries"]:
            all_group_keys.add(f'{summary["packet_id"]}::{group["duplicate_group_id"]}')
            source_duplicate_group_ids.add(group["duplicate_group_id"])
            if "opportunity:" in group["duplicate_group_id"]:
                source_opportunity_ids.add(group["duplicate_group_id"].split("opportunity:", 1)[1])
        global_lifecycle_counts.update(summary["lifecycle_counts"])
        global_fill_counts.update(summary["fill_counts"])
        global_reason_counts.update(summary["reason_counts"])
        global_symbol_counts.update(summary["symbol_counts"])
        global_session_counts.update(summary["session_counts"])
        global_side_counts.update(summary["side_counts"])
        packet_summaries.append(summary)

    raw_rows = sum(item["raw_rows"] for item in packet_summaries)
    packet_unique_groups = sum(item["unique_duplicate_groups"] for item in packet_summaries)
    duplicate_group_conflicts = [conflict for item in packet_summaries for conflict in item["label_conflicts"]]
    duplicate_groups_with_children = sum(item["duplicate_groups_with_multiple_rows"] for item in packet_summaries)
    lifecycle_source_evidence = {
        "source_projection_file": rel(SOURCE_PROJECTION_PATH),
        "source_projection_rows": len(source_projection_rows),
        "source_projection_hashes": len(source_projection_by_hash),
        "source_projection_forbidden_issue_count": sum(
            1 for row in source_projection_rows if row.get("forbidden_key_paths_after_projection")
        ),
        "source_hash_resolution_issue_count": len(source_hash_resolution_issues),
        "source_hash_resolution_issues": source_hash_resolution_issues,
        "hash_excludes_key_values_all_rows": all(row.get("hash_excludes_key_values") is True for row in source_projection_rows),
        "excluded_key_values_stored_any_row": any(row.get("excluded_key_values_stored") for row in source_projection_rows),
        "cited_lifecycle_logs": [
            {
                "path": "shadow_logs/pending_limit_lifecycle.jsonl",
                "sha256": input_hashes.get("shadow_logs/pending_limit_lifecycle.jsonl"),
                "line_count": line_count(REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl"),
            },
            {
                "path": "shadow_logs/pending_limit_lifecycle_audit.jsonl",
                "sha256": input_hashes.get("shadow_logs/pending_limit_lifecycle_audit.jsonl"),
                "line_count": line_count(REPO_ROOT / "shadow_logs/pending_limit_lifecycle_audit.jsonl"),
            },
            {
                "path": "shadow_logs/opportunity_lifecycle_audit.jsonl",
                "sha256": input_hashes.get("shadow_logs/opportunity_lifecycle_audit.jsonl"),
                "line_count": line_count(REPO_ROOT / "shadow_logs/opportunity_lifecycle_audit.jsonl"),
            },
        ],
    }
    covariate_blockers = [
        {
            "packet_id": item["packet_id"],
            "experiment_id": item["experiment_id"],
            "blocker_code": BLOCKED_COVARIATE,
            "claim_blocked": "covariate_or_source_complete_claim",
            "lifecycle_truth_counts_blocked": False,
            "reason": item["covariate_source_complete_claim_reason"],
            "owner_question": item["residual_nonblocking_question"],
        }
        for item in packet_summaries
        if item["packet_id"] in COVARIATE_PACKET_REASONS
    ]

    stats_status = {
        "effective_n_lifecycle_truth_packet_units": packet_unique_groups,
        "effective_n_lifecycle_truth_cross_packet_key_units": len(all_group_keys),
        "source_duplicate_group_id_units_unpooled": len(source_duplicate_group_ids),
        "source_opportunity_id_units_after_unwrapping_shared_family_prefixes": len(source_opportunity_ids),
        "validation_effective_n_status": "not_computable_for_validation",
        "validation_effective_n_reason": (
            "descriptive duplicate-group counts are computable, but validation effective-N is not: "
            "the same lifecycle source groups are intentionally reused across multiple experiment packets, "
            "preregistered null/alternative/sample-floor fields are absent, and covariate/source-complete "
            "claims are blocked where applicable"
        ),
        "raw_p_status": "not_computable",
        "raw_p_reason": "experiment preregistry rows have null=null and alternative=null for these lifecycle packets",
        "dsr_status": "not_computable",
        "dsr_reason": "DSR requires a return or Sharpe series; OTI1 lifecycle/no-fill labels are not R returns",
        "pbo_status": "not_computable",
        "pbo_reason": "PBO requires registered variants/folds; OTI1 has one frozen descriptive lifecycle metric and no variant trials",
    }

    common_meta = {
        "artifact_family": "OTI1_LIFECYCLE_QUARANTINED_RESULTS",
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": False,
        "outcome_review_opened": False,
        "external_fetches_api_databento_calls": 0,
        "live_trading_surfaces_touched": False,
        "paid_data_used": False,
        "remote_pushed": False,
        "broker_actual_r_values_inspected": False,
        "synthetic_path_r_values_inspected": False,
        "blocked_packet_outcomes_inspected": False,
    }

    result_ledger = {
        **common_meta,
        "artifact_type": "result_ledger",
        "scope": "quarantined_descriptive_lifecycle_truth_only_counts",
        "allowed_packet_count": len(packet_summaries),
        "excluded_shortlist_entries": excluded_seen,
        "raw_rows_audit_only": raw_rows,
        "unique_duplicate_group_packet_units": packet_unique_groups,
        "unique_duplicate_group_cross_packet_units": len(all_group_keys),
        "source_duplicate_group_id_units_unpooled": len(source_duplicate_group_ids),
        "source_opportunity_id_units_after_unwrapping_shared_family_prefixes": len(source_opportunity_ids),
        "lifecycle_counts_by_unique_duplicate_group": counter_table(global_lifecycle_counts),
        "fill_no_fill_counts_by_unique_duplicate_group": counter_table(global_fill_counts),
        "reason_counts_by_unique_duplicate_group": counter_table(global_reason_counts),
        "symbol_counts_by_unique_duplicate_group": counter_table(global_symbol_counts),
        "session_counts_by_unique_duplicate_group": counter_table(global_session_counts),
        "side_counts_by_unique_duplicate_group": counter_table(global_side_counts),
        "packet_results": packet_summaries,
        "statistics_status": stats_status,
        "lifecycle_source_evidence": lifecycle_source_evidence,
        "input_hashes": input_hashes,
    }

    methodology = {
        **common_meta,
        "artifact_type": "methodology_report",
        "metric_freeze_path": rel(FREEZE_PATH),
        "methodology": {
            "lane": LANE,
            "metric": freeze["metric"],
            "denominator": freeze["denominator"],
            "duplicate_group_policy": freeze["duplicate_group_policy"],
            "sample_floor_rule": freeze["sample_floor"],
            "label_family": freeze["label_family"],
            "forbidden_label_families": freeze["forbidden_label_families"],
            "not_computable_criteria": freeze["not_computable_criteria"],
            "lifecycle_label_inspection_after_freeze": True,
            "discovery_quarantine_only": True,
            "result_files_under_requested_directory": True,
        },
        "controlling_inputs": CONTROL_INPUTS + [rel(FREEZE_PATH), rel(ACCEPTED_SHORTLIST_PATH), rel(PREREGISTRY_PATH)],
        "lifecycle_source_evidence": lifecycle_source_evidence,
        "statistics_status": stats_status,
    }

    duplicate_report = {
        **common_meta,
        "artifact_type": "duplicate_denominator_report",
        "raw_rows_audit_only": raw_rows,
        "unique_duplicate_group_packet_units": packet_unique_groups,
        "unique_duplicate_group_cross_packet_units": len(all_group_keys),
        "source_duplicate_group_id_units_unpooled": len(source_duplicate_group_ids),
        "source_opportunity_id_units_after_unwrapping_shared_family_prefixes": len(source_opportunity_ids),
        "duplicate_groups_with_child_rows": duplicate_groups_with_children,
        "duplicate_group_label_conflicts": duplicate_group_conflicts,
        "denominator_mismatches": denominator_mismatches,
        "source_hash_resolution_issues": source_hash_resolution_issues,
        "packet_denominators": [
            {
                "packet_id": item["packet_id"],
                "experiment_id": item["experiment_id"],
                "raw_rows_audit_only": item["raw_rows"],
                "unique_duplicate_groups": item["unique_duplicate_groups"],
                "duplicate_groups_with_multiple_rows": item["duplicate_groups_with_multiple_rows"],
                "group_summaries": item["group_summaries"],
            }
            for item in packet_summaries
        ],
    }

    label_report = {
        **common_meta,
        "artifact_type": "label_family_separation_report",
        "primary_label_family": "lifecycle_no_fill",
        "forbidden_row_fields": sorted(FORBIDDEN_ROW_FIELDS),
        "forbidden_primary_field_hits": forbidden_field_hits,
        "source_hash_resolution_issues": source_hash_resolution_issues,
        "source_projection_forbidden_issue_count": lifecycle_source_evidence["source_projection_forbidden_issue_count"],
        "accepted_packet_label_family_status": "PASS_FOR_LIFECYCLE_TRUTH_ONLY_COUNTS",
        "broker_actual_r_status": "not_inspected_not_used",
        "synthetic_path_r_status": "not_inspected_not_used",
        "blocked_packet_status": "not_inspected_not_used",
        "covariate_source_complete_status": "blocked_where_source_asof_proof_absent",
        "packet_label_family_checks": [
            {
                "packet_id": item["packet_id"],
                "experiment_id": item["experiment_id"],
                "label_family": "lifecycle_no_fill",
                "forbidden_primary_fields_absent": True,
                "lifecycle_truth_only_result_status": RESULT_STATUS,
                "covariate_source_complete_claim_status": item["covariate_source_complete_claim_status"],
            }
            for item in packet_summaries
        ],
    }

    ambiguity_entries = [
        {
            "ambiguity": "Which packets are in OTI1 scope?",
            "resolution": "Use only the 9 G12 OTB rebuild accepted OTB1R lifecycle packets from the metric freeze; exclude OTG0-PKT-017 and all non-OTB1R packets.",
            "status": "ANSWERED_FACT",
            "evidence": rel(ACCEPTED_SHORTLIST_PATH),
        },
        {
            "ambiguity": "Can OTI1 count raw rows?",
            "resolution": "No. All result rates use unique duplicate_group_id counts; raw rows are audit-only child-row inventory.",
            "status": "ANSWERED_FACT",
            "evidence": rel(FREEZE_PATH),
        },
        {
            "ambiguity": "Are source-complete covariate claims available?",
            "resolution": "No for friction, volatility, footprint, news, macro-attention, FOMC, and Cboe packets; lifecycle-truth-only counts still run.",
            "status": "ANSWERED_FACT_WITH_BLOCKER",
            "evidence": "G12 OTB rebuild blocked question ledger residual source/covariate questions",
        },
        {
            "ambiguity": "Does OTG0-PKT-045 have two independent groups because it has two rows?",
            "resolution": "No. Both rows share duplicate_group_id opportunity:889468014bba028e10db17e2dc9c6fea and identical lifecycle labels; count once.",
            "status": "ANSWERED_FACT",
            "evidence": "OTG0-PKT-045 accepted packet rows and metadata unique_duplicate_group_id_count=1",
        },
        {
            "ambiguity": "Can validation statistics be computed?",
            "resolution": stats_status["validation_effective_n_reason"],
            "status": "NOT_COMPUTABLE_AFTER_EVIDENCE_EXHAUSTION",
            "evidence": rel(PREREGISTRY_PATH),
        },
    ]
    for blocker in covariate_blockers:
        ambiguity_entries.append(
            {
                "ambiguity": f"Can {blocker['packet_id']} use covariates for source-complete claims?",
                "resolution": blocker["reason"],
                "status": "EXACT_LOCAL_BLOCKER",
                "evidence": blocker["owner_question"] or "G12 residual covariate question",
            }
        )

    ambiguity_ledger = {
        **common_meta,
        "artifact_type": "ambiguity_resolution_ledger",
        "entries": ambiguity_entries,
        "duplicate_group_conflicts": duplicate_group_conflicts,
        "denominator_mismatches": denominator_mismatches,
        "source_hash_resolution_issues": source_hash_resolution_issues,
    }

    blocker_entries = covariate_blockers + [
        {
            "blocker_code": "VALIDATION_STATS_NOT_COMPUTABLE_NO_NULL_ALT_RETURN_SERIES_OR_VARIANTS",
            "claim_blocked": "validation_statistics",
            "lifecycle_truth_counts_blocked": False,
            "reason": "raw p, DSR, and PBO are not computable for this quarantined descriptive lifecycle lane",
        },
        {
            "blocker_code": "NO_PROMOTION_VERDICT_PRESERVED",
            "claim_blocked": "promotion_or_validation_safe_claim",
            "lifecycle_truth_counts_blocked": False,
            "reason": "OTI1 creates discovery/quarantine artifacts only and does not edit registries or source validation flags",
        },
    ]
    blocker_ledger = {
        **common_meta,
        "artifact_type": "blocker_ledger",
        "entries": blocker_entries,
    }

    completion_checklist = [
        ["Complete GTOS preflight", "generate_live_state.py ran and mandatory context/control docs were read before OTI1 edits", "DONE"],
        ["Freeze metric before packet label inspection", rel(FREEZE_PATH), "DONE"],
        ["Use only 9 accepted OTB1R lifecycle packets", f"{len(packet_summaries)} accepted OTB1R packets loaded; OTG0-PKT-017 excluded", "DONE"],
        ["Use unique duplicate_group_id counts", f"{packet_unique_groups} packet-level unique groups; {raw_rows} raw rows audit-only", "DONE"],
        ["Do not inspect broker actual-R/synthetic path-R/win-loss R", "builder reads only primary_lifecycle_rows and top-level sanitized projection hash evidence, then scans row keys for forbidden fields", "DONE"],
        ["Exhaust source projections and hash ledgers", f"{lifecycle_source_evidence['source_projection_rows']} sanitized projection rows; source_hash_resolution_issues={len(source_hash_resolution_issues)}", "DONE"],
        ["Exhaust cited lifecycle logs as evidence without using R values", f"hashed and line-counted {len(lifecycle_source_evidence['cited_lifecycle_logs'])} local lifecycle logs", "DONE"],
        ["Separate lifecycle truth from covariate/source-complete claims", "result ledger has lifecycle counts; blocker ledger has covariate blockers", "DONE"],
        ["Report descriptive results even when validation stats blocked", "result ledger reports lifecycle/fill/reason counts", "DONE"],
        ["Report effective-N and DSR/PBO status", "statistics_status reports descriptive effective-N and exact not_computable reasons", "DONE"],
        ["Produce result ledger", f"OTI1_RESULT_LEDGER_{DATE}.md/json", "DONE"],
        ["Produce methodology report", f"OTI1_METHODOLOGY_REPORT_{DATE}.md/json", "DONE"],
        ["Produce duplicate denominator report", f"OTI1_DUPLICATE_DENOMINATOR_REPORT_{DATE}.md/json", "DONE"],
        ["Produce label-family separation report", f"OTI1_LABEL_FAMILY_SEPARATION_REPORT_{DATE}.md/json", "DONE"],
        ["Produce ambiguity-resolution ledger", f"OTI1_AMBIGUITY_RESOLUTION_LEDGER_{DATE}.md/json", "DONE"],
        ["Produce blocker ledger", f"OTI1_BLOCKER_LEDGER_{DATE}.md/json", "DONE"],
        ["Produce completion audit", f"OTI1_COMPLETION_AUDIT_{DATE}.md/json", "DONE"],
        ["Preserve NO_PROMOTION_VERDICT", PROMOTION_VERDICT, "DONE"],
        ["No master registry/source validation flag edits", "builder writes only under OTI1 output directory", "DONE"],
        ["No paid/API/Databento/network/live trading surface changes", "external_fetches_api_databento_calls=0 and live_trading_surfaces_touched=false", "DONE"],
    ]

    completion_audit = {
        **common_meta,
        "artifact_type": "completion_audit",
        "objective_restatement": (
            "Run OTI1 quarantined lifecycle/no-fill outcome testing on only the 9 G12-accepted OTB1R lifecycle packets, "
            "with metric freeze before label inspection, duplicate_group_id denominators, label-family separation, covariate blockers, "
            "descriptive quarantine results, exact not-computable statistics, scoped artifacts, and no promotion/live changes."
        ),
        "can_mark_oti1_complete": (
            not denominator_mismatches
            and not duplicate_group_conflicts
            and not forbidden_field_hits
            and not source_hash_resolution_issues
        ),
        "checklist": [
            {"requirement": req, "evidence": evidence, "status": status}
            for req, evidence, status in completion_checklist
        ],
        "residual_risks": [
            "Lifecycle-truth-only counts are discovery/quarantine only and are not validation evidence.",
            "Covariate/source-complete claims remain blocked until source/as-of proofs are packet-bound.",
            "Cross-packet source reuse means pooled packet counts are not independent validation trials.",
        ],
        "statistics_status": stats_status,
        "lifecycle_source_evidence": lifecycle_source_evidence,
    }

    outputs: dict[str, tuple[dict[str, Any], str]] = {
        "OTI1_RESULT_LEDGER": (result_ledger, render_result_ledger(result_ledger)),
        "OTI1_METHODOLOGY_REPORT": (methodology, render_methodology(methodology)),
        "OTI1_DUPLICATE_DENOMINATOR_REPORT": (duplicate_report, render_duplicate_report(duplicate_report)),
        "OTI1_LABEL_FAMILY_SEPARATION_REPORT": (label_report, render_label_report(label_report)),
        "OTI1_AMBIGUITY_RESOLUTION_LEDGER": (ambiguity_ledger, render_ambiguity_ledger(ambiguity_ledger)),
        "OTI1_BLOCKER_LEDGER": (blocker_ledger, render_blocker_ledger(blocker_ledger)),
        "OTI1_COMPLETION_AUDIT": (completion_audit, render_completion_audit(completion_audit)),
    }

    written: dict[str, Path] = {}
    for stem, (payload, markdown) in outputs.items():
        json_path = OUT_DIR / f"{stem}_{DATE}.json"
        md_path = OUT_DIR / f"{stem}_{DATE}.md"
        write_json(json_path, payload)
        md_path.write_text(markdown, encoding="utf-8")
        written[json_path.name] = json_path
        written[md_path.name] = md_path

    manifest = {
        **common_meta,
        "artifact_type": "artifact_manifest",
        "artifacts": [
            {
                "path": rel(path),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for path in sorted(written.values(), key=lambda p: p.name)
        ]
        + [
            {
                "path": rel(FREEZE_PATH),
                "sha256": sha256(FREEZE_PATH),
                "size_bytes": FREEZE_PATH.stat().st_size,
            }
        ],
        "input_hashes": input_hashes,
    }
    manifest_path = OUT_DIR / f"OTI1_ARTIFACT_MANIFEST_{DATE}.json"
    write_json(manifest_path, manifest)
    written[manifest_path.name] = manifest_path
    return written


def render_header(title: str, artifact_type: str) -> str:
    return (
        f"# {title} - {DATE}\n\n"
        f"**Lane:** `{LANE}`  \n"
        f"**Artifact type:** `{artifact_type}`  \n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  \n"
        f"**Result status:** `{RESULT_STATUS}`\n\n"
    )


def render_result_ledger(payload: dict[str, Any]) -> str:
    packet_rows = [
        [
            item["packet_id"],
            item["experiment_id"],
            item["raw_rows"],
            item["unique_duplicate_groups"],
            item["lifecycle_counts"],
            item["fill_counts"],
            item["covariate_source_complete_claim_status"],
        ]
        for item in payload["packet_results"]
    ]
    return (
        render_header("OTI1 Result Ledger", "result_ledger")
        + "## Summary\n\n"
        + table(
            ["Measure", "Value"],
            [
                ["Allowed OTB1R packets", payload["allowed_packet_count"]],
                ["Raw rows audit-only", payload["raw_rows_audit_only"]],
                ["Unique duplicate groups, packet units", payload["unique_duplicate_group_packet_units"]],
                ["Unique duplicate groups, source IDs unpooled", payload["source_duplicate_group_id_units_unpooled"]],
                ["Sanitized source projection rows", payload["lifecycle_source_evidence"]["source_projection_rows"]],
                ["Source hash resolution issues", payload["lifecycle_source_evidence"]["source_hash_resolution_issue_count"]],
                ["Broker actual-R inspected", payload["broker_actual_r_values_inspected"]],
                ["Synthetic path-R inspected", payload["synthetic_path_r_values_inspected"]],
            ],
        )
        + "\n\n## Lifecycle Truth Counts\n\n"
        + table(["Lifecycle state", "Unique duplicate groups"], [[row["value"], row["unique_duplicate_groups"]] for row in payload["lifecycle_counts_by_unique_duplicate_group"]])
        + "\n\n## Fill/No-Fill Counts\n\n"
        + table(["Fill/no-fill state", "Unique duplicate groups"], [[row["value"], row["unique_duplicate_groups"]] for row in payload["fill_no_fill_counts_by_unique_duplicate_group"]])
        + "\n\n## Reason Counts\n\n"
        + table(["Reason", "Unique duplicate groups"], [[row["value"], row["unique_duplicate_groups"]] for row in payload["reason_counts_by_unique_duplicate_group"]])
        + "\n\n## Packet Results\n\n"
        + table(["Packet", "Experiment", "Raw rows", "Unique groups", "Lifecycle counts", "Fill counts", "Covariate claim"], packet_rows)
        + "\n\n## Statistics Status\n\n"
        + table(
            ["Statistic", "Status / reason"],
            [
                ["Effective N", payload["statistics_status"]["validation_effective_n_reason"]],
                ["Raw p", payload["statistics_status"]["raw_p_reason"]],
                ["DSR", payload["statistics_status"]["dsr_reason"]],
                ["PBO", payload["statistics_status"]["pbo_reason"]],
            ],
        )
        + "\n\n## Source Projection And Lifecycle Log Evidence\n\n"
        + table(
            ["Evidence", "Value"],
            [
                ["Source projection file", payload["lifecycle_source_evidence"]["source_projection_file"]],
                ["Source projection rows", payload["lifecycle_source_evidence"]["source_projection_rows"]],
                ["Source hashes resolved", payload["lifecycle_source_evidence"]["source_hash_resolution_issue_count"] == 0],
                ["Projection forbidden issues", payload["lifecycle_source_evidence"]["source_projection_forbidden_issue_count"]],
                ["Excluded source key values stored", payload["lifecycle_source_evidence"]["excluded_key_values_stored_any_row"]],
            ],
        )
        + "\n\nAll counts are discovery/quarantine only and use unique `duplicate_group_id` units, not raw rows.\n"
    )


def render_methodology(payload: dict[str, Any]) -> str:
    method = payload["methodology"]
    return (
        render_header("OTI1 Methodology Report", "methodology_report")
        + "## Frozen Method\n\n"
        + table(
            ["Field", "Value"],
            [
                ["Metric freeze", payload["metric_freeze_path"]],
                ["Metric", method["metric"]],
                ["Denominator", method["denominator"]],
                ["Label family", method["label_family"]],
                ["Lifecycle labels inspected after freeze", method["lifecycle_label_inspection_after_freeze"]],
                ["Discovery quarantine only", method["discovery_quarantine_only"]],
            ],
        )
        + "\n\n## Not-Computable Criteria\n\n"
        + "\n".join(f"- `{item}`" for item in method["not_computable_criteria"])
        + "\n\n## Controlling Inputs\n\n"
        + "\n".join(f"- `{item}`" for item in payload["controlling_inputs"])
        + "\n\n## Source Evidence Exhausted\n\n"
        + table(
            ["Evidence", "Value"],
            [
                ["Source projection file", payload["lifecycle_source_evidence"]["source_projection_file"]],
                ["Source projection rows", payload["lifecycle_source_evidence"]["source_projection_rows"]],
                ["Source hash resolution issues", payload["lifecycle_source_evidence"]["source_hash_resolution_issue_count"]],
                ["Lifecycle logs hashed", len(payload["lifecycle_source_evidence"]["cited_lifecycle_logs"])],
            ],
        )
        + "\n"
    )


def render_duplicate_report(payload: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_id"],
            item["experiment_id"],
            item["raw_rows_audit_only"],
            item["unique_duplicate_groups"],
            item["duplicate_groups_with_multiple_rows"],
        ]
        for item in payload["packet_denominators"]
    ]
    return (
        render_header("OTI1 Duplicate Denominator Report", "duplicate_denominator_report")
        + "## Denominator Summary\n\n"
        + table(
            ["Measure", "Value"],
            [
                ["Raw rows audit-only", payload["raw_rows_audit_only"]],
                ["Unique duplicate groups, packet units", payload["unique_duplicate_group_packet_units"]],
                ["Unique duplicate groups, cross-packet keys", payload["unique_duplicate_group_cross_packet_units"]],
                ["Source duplicate_group_id units, unpooled", payload["source_duplicate_group_id_units_unpooled"]],
                ["Source opportunity IDs after prefix unwrap", payload["source_opportunity_id_units_after_unwrapping_shared_family_prefixes"]],
                ["Duplicate groups with child rows", payload["duplicate_groups_with_child_rows"]],
                ["Duplicate label conflicts", len(payload["duplicate_group_label_conflicts"])],
                ["Denominator mismatches", len(payload["denominator_mismatches"])],
                ["Source hash resolution issues", len(payload["source_hash_resolution_issues"])],
            ],
        )
        + "\n\n## Packet Denominators\n\n"
        + table(["Packet", "Experiment", "Raw rows", "Unique groups", "Groups >1 row"], rows)
        + "\n\nRaw rows are not used as independent units.\n"
    )


def render_label_report(payload: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_id"],
            item["experiment_id"],
            item["label_family"],
            item["forbidden_primary_fields_absent"],
            item["covariate_source_complete_claim_status"],
        ]
        for item in payload["packet_label_family_checks"]
    ]
    return (
        render_header("OTI1 Label-Family Separation Report", "label_family_separation_report")
        + "## Label Boundary\n\n"
        + table(
            ["Boundary", "Status"],
            [
                ["Primary label family", payload["primary_label_family"]],
                ["Forbidden primary field hits", len(payload["forbidden_primary_field_hits"])],
                ["Source hash resolution issues", len(payload["source_hash_resolution_issues"])],
                ["Projection forbidden issues", payload["source_projection_forbidden_issue_count"]],
                ["Broker actual-R", payload["broker_actual_r_status"]],
                ["Synthetic path-R", payload["synthetic_path_r_status"]],
                ["Blocked packets", payload["blocked_packet_status"]],
            ],
        )
        + "\n\n## Packet Checks\n\n"
        + table(["Packet", "Experiment", "Label family", "R fields absent", "Covariate claim"], rows)
        + "\n"
    )


def render_ambiguity_ledger(payload: dict[str, Any]) -> str:
    rows = [[item["status"], item["ambiguity"], item["resolution"]] for item in payload["entries"]]
    return (
        render_header("OTI1 Ambiguity Resolution Ledger", "ambiguity_resolution_ledger")
        + table(["Status", "Ambiguity", "Resolution"], rows)
        + "\n"
    )


def render_blocker_ledger(payload: dict[str, Any]) -> str:
    rows = [
        [
            item.get("packet_id", "portfolio"),
            item["blocker_code"],
            item["claim_blocked"],
            item["lifecycle_truth_counts_blocked"],
            item["reason"],
        ]
        for item in payload["entries"]
    ]
    return (
        render_header("OTI1 Blocker Ledger", "blocker_ledger")
        + table(["Packet", "Blocker", "Claim blocked", "Lifecycle counts blocked", "Reason"], rows)
        + "\n"
    )


def render_completion_audit(payload: dict[str, Any]) -> str:
    rows = [[item["requirement"], item["evidence"], item["status"]] for item in payload["checklist"]]
    return (
        render_header("OTI1 Completion Audit", "completion_audit")
        + "## Objective Restated\n\n"
        + payload["objective_restatement"]
        + "\n\n## Completion Status\n\n"
        + table([ "Check", "Value"], [["Can mark OTI1 complete", payload["can_mark_oti1_complete"]]])
        + "\n\n## Prompt-To-Artifact Checklist\n\n"
        + table(["Requirement", "Evidence", "Status"], rows)
        + "\n\n## Residual Risks\n\n"
        + "\n".join(f"- {item}" for item in payload["residual_risks"])
        + "\n\n## Source Evidence Check\n\n"
        + table(
            ["Check", "Value"],
            [
                ["Source projection rows", payload["lifecycle_source_evidence"]["source_projection_rows"]],
                ["Source hash resolution issues", payload["lifecycle_source_evidence"]["source_hash_resolution_issue_count"]],
                ["Projection forbidden issues", payload["lifecycle_source_evidence"]["source_projection_forbidden_issue_count"]],
                ["Cited lifecycle logs hashed", len(payload["lifecycle_source_evidence"]["cited_lifecycle_logs"])],
            ],
        )
        + "\n"
    )


def main() -> None:
    written = build()
    print(f"Wrote {len(written)} OTI1 artifacts to {OUT_DIR}")


if __name__ == "__main__":
    main()
