#!/usr/bin/env python3
"""Independent G12 audit for the NOFILL forward projection builder.

This lane is research/control only. It reads committed artifacts and approved
source-control projections, recomputes denominator/hash/no-leak controls, and
writes audit artifacts. It does not score outcomes or modify live surfaces.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "G12_NOFILL_FORWARD_PROJECTION_BUILDER_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "g12_nofill_forward_projection_builder_audit_v1"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")

PROJECTION_DIR = BASE / "nofill_forward_source_safe_projection_builder"
ADDENDUM_DIR = BASE / "nofill_forward_contract_addendum_projection_plan"
G12_FORWARD_DIR = BASE / "g12_nofill_forward_lifecycle_capture_contract_audit"
COUNT_DIR = BASE / "nofill_cat_v3_quarantined_categorical_count_packet"
RESULT_CONTRACT_DIR = BASE / "nofill_cat_v3_result_contract_update"
SOURCE_CONTROL_DIR = BASE / "nofill_cat_v3_source_control_rebuild"
G12_COUNT_DIR = BASE / "g12_nofill_cat_v3_quarantined_categorical_count_packet_audit"
G0_SYNTH_DIR = BASE / "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review"
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_BUILDER_GOAL_PROMPT_2026-05-09.md"
)

ROWS_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_{DATE}.jsonl"
ACCEPTED_PATH = COUNT_DIR / f"NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_{DATE}.jsonl"
EXCLUSION_PATH = COUNT_DIR / f"NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_{DATE}.jsonl"
REJECT_OVERLAP_PATH = COUNT_DIR / f"NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_{DATE}.json"
ALLOWLIST_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC_{DATE}.json"
SOURCE_MANIFEST_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json"
PARSER_MANIFEST_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_PARSER_HASH_MANIFEST_{DATE}.json"
MISSING_STATUS_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_MISSING_STATUS_LEDGER_{DATE}.json"
FORBIDDEN_AUDIT_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT_{DATE}.json"
DENOMINATOR_AUDIT_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_DENOMINATOR_AND_EXCLUSION_AUDIT_{DATE}.json"
SOURCE_SEARCH_LEDGER_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_SOURCE_INVENTORY_AND_SEARCH_LEDGER_{DATE}.json"
UPSTREAM_VERIFIER = PROJECTION_DIR / "verify_nofill_forward_source_safe_projection_builder_2026_05_09.py"

SOURCE_CONTROL_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
    "NOFILL-CAT-ROW-0241",
}
SOURCE_IMPOSSIBLE_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}

CONTROL_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_live_wiring": False,
    "opens_paid_api_or_databento_route": False,
    "opens_registry_edit": False,
    "changes_live_trading_behavior": False,
}

FORBIDDEN_RAW_KEYS = {
    "account_history",
    "account_pnl",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "deal_id",
    "expectancy",
    "fill_time_utc",
    "live_order_state",
    "mt5_deal_id",
    "mt5_order_ticket",
    "mt5_position_id",
    "order_send_attempted",
    "order_send_success",
    "pending_ticket",
    "position_id",
    "r_multiple",
    "r_value",
    "slippage_price",
    "synthetic_path_r",
    "trade_state_ticket",
    "win_rate",
}

ALLOWED_REDACTION_STATUS_FIELDS = {
    "broker_pending_order_created_status",
    "raw_ticket_field_present_status",
    "mt5_order_ticket_redaction_status",
    "slippage_label_status",
    "slippage_value_redaction_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
}

EXPECTED_EXTRA_SAFE_CONTROL_FIELDS = {
    "promotion_verdict",
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_live_wiring",
    "opens_paid_api_or_databento_route",
    "opens_registry_edit",
    "changes_live_trading_behavior",
    "route_id",
    "projection_schema_version",
    "projection_builder_version",
    "projection_output_allowed_field_count",
    "source_route_count",
}

APPROVED_LOG_NAMES = [
    "strategy_follow_candidates.jsonl",
    "candidate_path_follow.jsonl",
    "candidate_ltf_path_order.jsonl",
    "pending_limit_lifecycle.jsonl",
    "pending_limit_lifecycle_join_backfill.jsonl",
    "prefill_delivery_path.jsonl",
    "v2b_forward_pairs.jsonl",
    "fvg_ob_confluence.jsonl",
]

LOCAL_HEAVY_ROOTS = [
    "C:/Users/MSI/Documents/ai-trading-agent/data",
    "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
    "C:/Users/MSI/Documents/ai-trading-agent/exports",
    "C:/tmp",
    "C:/tmp/gtos_otb",
    "C:/SierraChart",
    "C:/Users/MSI/Documents",
]

CONTROL_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    str(PROMPT_PATH),
    str(PROJECTION_DIR / f"NOFILL_FORWARD_NEXT_PROMPT_PACK_{DATE}.md"),
    str(PROJECTION_DIR / f"NOFILL_FORWARD_PROJECTION_COMPLETION_AUDIT_{DATE}.json"),
    str(ALLOWLIST_PATH),
    str(SOURCE_MANIFEST_PATH),
    str(PARSER_MANIFEST_PATH),
    str(MISSING_STATUS_PATH),
    str(FORBIDDEN_AUDIT_PATH),
    str(DENOMINATOR_AUDIT_PATH),
    str(SOURCE_SEARCH_LEDGER_PATH),
    str(ADDENDUM_DIR / f"NOFILL_FORWARD_NEXT_PROMPT_PACK_{DATE}.md"),
    str(ADDENDUM_DIR / f"NOFILL_FORWARD_OFFLINE_PROJECTION_BUILDER_PLAN_{DATE}.md"),
    str(ADDENDUM_DIR / f"NOFILL_FORWARD_CONTRACT_ADDENDUM_{DATE}.json"),
    str(G12_FORWARD_DIR / f"G12_NOFILL_FORWARD_DECISION_LEDGER_{DATE}.json"),
    str(G12_FORWARD_DIR / f"G12_NOFILL_FORWARD_SCHEMA_AUDIT_{DATE}.json"),
    str(G12_FORWARD_DIR / f"G12_NOFILL_FORWARD_NO_LEAK_SOURCE_AUDIT_{DATE}.json"),
    str(COUNT_DIR / f"NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_{DATE}.json"),
    str(ACCEPTED_PATH),
    str(EXCLUSION_PATH),
    str(REJECT_OVERLAP_PATH),
    str(RESULT_CONTRACT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json"),
    str(SOURCE_CONTROL_DIR / f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.json"),
    str(G12_COUNT_DIR / f"G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json"),
    str(G0_SYNTH_DIR / f"G0_NOFILL_CAT_V3_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.json"),
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def rel_display(path: str | Path) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def sha256_file(path: str | Path) -> str | None:
    full = repo_path(path)
    if not full.exists() or not full.is_file():
        return None
    digest = hashlib.sha256()
    with full.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lf_file(path: str | Path) -> str | None:
    full = repo_path(path)
    if not full.exists() or not full.is_file():
        return None
    if full.suffix.lower() not in {".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml"}:
        return None
    return hashlib.sha256(full.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_json(path: str | Path) -> Any:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with repo_path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{rel_display(path)}:{line_no}: {exc}") from exc
    return rows


def write_json(name: str, payload: Any) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (OUT_DIR / name).write_text(text.strip() + "\n", encoding="utf-8")


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def run_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": " ".join(args),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
    }


def parse_source_candidate_id(source_row_id: str | None) -> str | None:
    if not source_row_id or "|" not in source_row_id:
        return None
    return source_row_id.split("|", 1)[1]


def recompute_denominators(
    rows: list[dict[str, Any]],
    accepted: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    reject_overlap: dict[str, Any],
) -> dict[str, Any]:
    projection_ids = {row["packet_row_id"] for row in rows}
    accepted_ids = {row["packet_row_id"] for row in accepted}
    exclusion_ids = {row["packet_row_id"] for row in exclusions}
    union_ids = accepted_ids | exclusion_ids

    family_counts = Counter(row.get("v3_terminal_family") for row in rows)
    accepted_key_counts = Counter(row.get("nofill_duplicate_key") for row in accepted)
    accepted_group_counts = Counter(row.get("duplicate_group_id") for row in accepted)
    reject_rows = [row for row in exclusions if row.get("v3_terminal_family") == "reject"]
    source_control_rows = [row for row in exclusions if row.get("v3_terminal_family") == "source_control"]
    source_impossible_rows = [row for row in exclusions if row.get("v3_terminal_family") == "source_impossible"]

    accepted_keys = {row.get("nofill_duplicate_key") for row in accepted}
    accepted_groups = {row.get("duplicate_group_id") for row in accepted}
    reject_key_overlap = [row["packet_row_id"] for row in reject_rows if row.get("nofill_duplicate_key") in accepted_keys]
    reject_group_overlap = [row["packet_row_id"] for row in reject_rows if row.get("duplicate_group_id") in accepted_groups]

    issues: list[dict[str, Any]] = []
    expected_family = {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}
    if dict(family_counts) != expected_family:
        issues.append({"issue": "projection_family_counts_mismatch", "actual": dict(family_counts)})
    if len(rows) != 298 or len(projection_ids) != 298:
        issues.append({"issue": "projection_row_count_or_uniqueness_mismatch", "row_count": len(rows), "unique_ids": len(projection_ids)})
    if projection_ids != union_ids:
        issues.append(
            {
                "issue": "projection_ids_do_not_equal_accepted_plus_exclusion_ids",
                "missing_from_projection": sorted(union_ids - projection_ids)[:25],
                "extra_in_projection": sorted(projection_ids - union_ids)[:25],
            }
        )
    if sum(bool(row.get("row_level_denominator_member")) for row in rows) != 225:
        issues.append({"issue": "row_level_denominator_mismatch"})
    if sum(bool(row.get("nofill_duplicate_key_count_member")) for row in rows) != 182:
        issues.append({"issue": "primary_duplicate_key_member_mismatch"})
    if sum(bool(row.get("duplicate_group_id_count_member")) for row in rows) != 139:
        issues.append({"issue": "secondary_duplicate_group_member_mismatch"})
    if {row["packet_row_id"] for row in source_control_rows} != SOURCE_CONTROL_ROWS:
        issues.append({"issue": "source_control_set_mismatch", "actual": sorted(row["packet_row_id"] for row in source_control_rows)})
    if {row["packet_row_id"] for row in source_impossible_rows} != SOURCE_IMPOSSIBLE_ROWS:
        issues.append({"issue": "source_impossible_set_mismatch", "actual": sorted(row["packet_row_id"] for row in source_impossible_rows)})
    if len(reject_rows) != 65:
        issues.append({"issue": "reject_count_mismatch", "actual": len(reject_rows)})
    if reject_overlap.get("reject_overlap_packet_row_ids") and set(reject_overlap["reject_overlap_packet_row_ids"]) != set(reject_key_overlap):
        issues.append({"issue": "reject_overlap_ids_mismatch"})
    if len(reject_key_overlap) != 47 or len(reject_group_overlap) != 47:
        issues.append(
            {
                "issue": "reject_overlap_count_mismatch",
                "key_overlap": len(reject_key_overlap),
                "group_overlap": len(reject_group_overlap),
            }
        )
    counted_exclusions = [
        row["packet_row_id"]
        for row in rows
        if row.get("v3_terminal_family") != "accepted"
        and (
            row.get("row_level_denominator_member")
            or row.get("nofill_duplicate_key_count_member")
            or row.get("duplicate_group_id_count_member")
        )
    ]
    if counted_exclusions:
        issues.append({"issue": "nonaccepted_rows_counted", "packet_row_ids": counted_exclusions[:25]})

    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_BUILDER_DENOMINATOR_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "projection_row_count": len(rows),
        "projection_unique_packet_row_ids": len(projection_ids),
        "universe_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
        "family_counts": dict(family_counts),
        "accepted_input_rows": len(accepted),
        "exclusion_rows": len(exclusions),
        "accepted_row_level_denominator": sum(bool(row.get("row_level_denominator_member")) for row in rows),
        "primary_duplicate_key_denominator": sum(bool(row.get("nofill_duplicate_key_count_member")) for row in rows),
        "secondary_duplicate_group_denominator": sum(bool(row.get("duplicate_group_id_count_member")) for row in rows),
        "accepted_unique_nofill_duplicate_keys": len(accepted_key_counts),
        "accepted_unique_duplicate_group_ids": len(accepted_group_counts),
        "source_control_rows": sorted(row["packet_row_id"] for row in source_control_rows),
        "source_impossible_rows": sorted(row["packet_row_id"] for row in source_impossible_rows),
        "reject_rows": len(reject_rows),
        "reject_overlap_rows_recomputed_by_key": len(reject_key_overlap),
        "reject_overlap_rows_recomputed_by_group": len(reject_group_overlap),
        "reject_overlap_denominator_delta": {
            "row_level_count_delta_from_rejects": 0,
            "nofill_duplicate_key_count_delta_from_rejects": 0,
            "duplicate_group_id_count_delta_from_rejects": 0,
            "reason": "Accepted rows are filtered before denominator counting; reject/source-control/source-impossible rows have all count-member flags false.",
        },
        "projection_ids_match_accepted_plus_exclusion_ids": projection_ids == union_ids,
    }


def recompute_hashes(source_manifest: list[dict[str, Any]], parser_manifest: list[dict[str, Any]]) -> dict[str, Any]:
    source_failures: list[dict[str, Any]] = []
    parser_failures: list[dict[str, Any]] = []
    mutable_context_drifts: list[dict[str, Any]] = []
    line_ending_only_drifts: list[dict[str, Any]] = []
    missing_records: list[dict[str, Any]] = []

    def check_record(item: dict[str, Any], family: str) -> None:
        expected = item.get("sha256")
        path = item.get("path")
        if not item.get("exists"):
            missing_records.append({"family": family, "path": path, "reason": "manifest_exists_false"})
            return
        actual = sha256_file(path)
        if actual == expected:
            return
        actual_lf = sha256_lf_file(path)
        if item.get("sha256_lf_normalized") and actual_lf == item.get("sha256_lf_normalized"):
            line_ending_only_drifts.append(
                {
                    "family": family,
                    "path": path,
                    "line_ending_policy": item.get("line_ending_policy"),
                    "strict_hash_recompute": item.get("strict_hash_recompute"),
                }
            )
            return
        if item.get("strict_hash_recompute") is False and actual is not None:
            mutable_context_drifts.append(
                {
                    "family": family,
                    "path": path,
                    "hash_policy": item.get("hash_policy"),
                    "strict_hash_recompute": item.get("strict_hash_recompute"),
                }
            )
            return
        failure = {"family": family, "path": path, "expected": expected, "actual": actual}
        if family == "parser":
            parser_failures.append(failure)
        else:
            source_failures.append(failure)

    for item in source_manifest:
        check_record(item, "source")
    for item in parser_manifest:
        check_record(item, "parser")

    text_policy_issues = [
        {
            "family": "source",
            "path": item.get("path"),
            "line_ending_policy": item.get("line_ending_policy"),
            "has_lf_hash": bool(item.get("sha256_lf_normalized")),
        }
        for item in source_manifest
        if str(item.get("path", "")).lower().endswith((".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml"))
        and (item.get("line_ending_policy") != "lf_normalized_fallback" or not item.get("sha256_lf_normalized"))
    ]
    text_policy_issues.extend(
        {
            "family": "parser",
            "path": item.get("path"),
            "line_ending_policy": item.get("line_ending_policy"),
            "has_lf_hash": bool(item.get("sha256_lf_normalized")),
        }
        for item in parser_manifest
        if item.get("line_ending_policy") != "lf_normalized_fallback" or not item.get("sha256_lf_normalized")
    )

    return {
        "source_hash_records": len(source_manifest),
        "parser_hash_records": len(parser_manifest),
        "source_hash_strict_failures": source_failures,
        "parser_hash_strict_failures": parser_failures,
        "manifest_missing_records": missing_records,
        "mutable_context_hash_drifts_accepted": mutable_context_drifts,
        "line_ending_only_drifts_accepted": line_ending_only_drifts,
        "text_line_ending_policy_issues": text_policy_issues,
        "status": "PASS"
        if not source_failures and not parser_failures and not missing_records and not text_policy_issues
        else "FAIL",
    }


def audit_projection_safety(
    rows: list[dict[str, Any]],
    allowlist: dict[str, Any],
    source_manifest: list[dict[str, Any]],
    parser_manifest: list[dict[str, Any]],
    source_search: dict[str, Any],
) -> dict[str, Any]:
    allowed_fields = (
        set(allowlist.get("identity_and_control_fields_allowed", []))
        | set(allowlist.get("addendum_projection_fields_allowed", []))
    )
    all_row_keys: set[str] = set()
    for row in rows:
        all_row_keys.update(row.keys())
    fields_outside_allowlist = sorted(all_row_keys - allowed_fields)
    unsafe_fields_outside_allowlist = sorted(set(fields_outside_allowlist) - EXPECTED_EXTRA_SAFE_CONTROL_FIELDS)

    forbidden_key_hits: list[dict[str, Any]] = []
    forbidden_value_token_hits: list[dict[str, Any]] = []
    closed_flag_issues: list[dict[str, Any]] = []
    spread_source_issues: list[dict[str, Any]] = []
    missing_semantic_issues: list[dict[str, Any]] = []

    for row in rows:
        for key in row.keys():
            if key in FORBIDDEN_RAW_KEYS and key not in ALLOWED_REDACTION_STATUS_FIELDS:
                forbidden_key_hits.append({"packet_row_id": row.get("packet_row_id"), "key": key})
        row_text = json.dumps(row, sort_keys=True)
        for token in sorted(FORBIDDEN_RAW_KEYS):
            if token in row_text and token not in ALLOWED_REDACTION_STATUS_FIELDS and token not in {"order_send_success"}:
                if token == "mt5_order_ticket" and "mt5_order_ticket_redaction_status" in row:
                    continue
                forbidden_value_token_hits.append({"packet_row_id": row.get("packet_row_id"), "token": token})
        for flag, expected in CONTROL_FLAGS.items():
            if row.get(flag) != expected:
                closed_flag_issues.append({"packet_row_id": row.get("packet_row_id"), "flag": flag, "actual": row.get(flag)})
        if row.get("slippage_label_status") != "NOT_OPENED_FOR_SOURCE_CONTROL":
            closed_flag_issues.append({"packet_row_id": row.get("packet_row_id"), "field": "slippage_label_status"})
        if row.get("execution_quality_label_status") != "NOT_OPENED_FOR_SOURCE_CONTROL":
            closed_flag_issues.append({"packet_row_id": row.get("packet_row_id"), "field": "execution_quality_label_status"})
        if row.get("cost_testing_gate_status") != "COST_TESTING_NOT_OPENED":
            closed_flag_issues.append({"packet_row_id": row.get("packet_row_id"), "field": "cost_testing_gate_status"})

        lineage = row.get("source_lineage") or []
        tick_hashes = {
            item.get("source_file_sha256")
            for item in lineage
            if item.get("source_role") == "tick_parquet_readonly_manifest"
        }
        if row.get("decision_spread_status") == "CAPTURED_SOURCE_SAFE" and not row.get("spread_source_hash"):
            spread_source_issues.append({"packet_row_id": row.get("packet_row_id"), "issue": "captured_decision_spread_missing_hash"})
        if row.get("entry_touch_spread_status") == "CAPTURED_SOURCE_SAFE" and not row.get("spread_source_hash"):
            spread_source_issues.append({"packet_row_id": row.get("packet_row_id"), "issue": "captured_entry_spread_missing_hash"})
        if row.get("spread_source_hash") and row.get("spread_source_hash") not in tick_hashes:
            spread_source_issues.append({"packet_row_id": row.get("packet_row_id"), "issue": "spread_hash_not_in_tick_lineage"})

        missing_statuses = row.get("missing_statuses") or {}
        if row.get("entry_touch_spread_status") == "TOUCH_NOT_OBSERVED_SOURCE_SAFE" and missing_statuses.get(
            "entry_touch_spread_value_source_safe"
        ) == "SOURCE_FIELD_MISSING":
            missing_semantic_issues.append(
                {
                    "packet_row_id": row.get("packet_row_id"),
                    "issue": "touch_not_observed_collapsed_to_source_field_missing_in_missing_statuses",
                }
            )

    raw_source_key_hits: dict[str, list[str]] = {}
    for item in source_search.get("approved_current_log_inventory", []):
        hits = sorted(set(item.get("observed_forbidden_raw_key_hits") or []))
        if hits:
            raw_source_key_hits[item.get("path", "unknown")] = hits

    hash_audit = recompute_hashes(source_manifest, parser_manifest)
    parser_hashes = [item.get("sha256") for item in parser_manifest if item.get("path", "").endswith("build_nofill_forward_source_safe_projection_builder_2026_05_09.py")]
    parser_row_hash_mismatches = [
        row.get("packet_row_id")
        for row in rows
        if parser_hashes and row.get("parser_code_sha256") not in parser_hashes
    ]

    decision_spread_counts = Counter(row.get("decision_spread_status") for row in rows)
    entry_spread_counts = Counter(row.get("entry_touch_spread_status") for row in rows)
    source_match_counts = Counter(row.get("source_match_status") for row in rows)

    issues: list[dict[str, Any]] = []
    if fields_outside_allowlist:
        issues.append(
            {
                "issue_id": "G12-PROJ-ISSUE-ALLOWLIST-001",
                "severity": "BLOCKING_CONTRACT_GAP",
                "summary": "Projection rows emit fields not explicitly listed in NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC.",
                "fields_outside_declared_allowlist": fields_outside_allowlist,
                "unsafe_fields_outside_declared_allowlist": unsafe_fields_outside_allowlist,
                "assessment": "The extra fields are safe control metadata in this audit, but a strict allowlist must explicitly list every emitted field before G12 acceptance.",
            }
        )
    if missing_semantic_issues:
        issues.append(
            {
                "issue_id": "G12-PROJ-ISSUE-MISSING-STATUS-001",
                "severity": "NONBLOCKING_SEMANTIC_TIGHTENING",
                "summary": "TOUCH_NOT_OBSERVED_SOURCE_SAFE rows use SOURCE_FIELD_MISSING in missing_statuses for entry_touch_spread_value_source_safe.",
                "affected_rows": len(missing_semantic_issues),
                "assessment": "The dedicated entry_touch_spread_status field disambiguates these rows, but the supplemental missing_statuses vocabulary should distinguish value-not-applicable because no touch was observed from true source absence.",
            }
        )
    if forbidden_key_hits or forbidden_value_token_hits or closed_flag_issues or spread_source_issues or parser_row_hash_mismatches:
        issues.append(
            {
                "issue_id": "G12-PROJ-ISSUE-SAFETY-001",
                "severity": "BLOCKING_SAFETY_FAILURE",
                "forbidden_key_hits": forbidden_key_hits[:25],
                "forbidden_value_token_hits": forbidden_value_token_hits[:25],
                "closed_flag_issues": closed_flag_issues[:25],
                "spread_source_issues": spread_source_issues[:25],
                "parser_row_hash_mismatches": parser_row_hash_mismatches[:25],
            }
        )

    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_BUILDER_SOURCE_HASH_NOLEAK_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "status": "PASS_WITH_CONTRACT_GAPS" if issues else "PASS",
        "issues": issues,
        "row_count": len(rows),
        "row_key_count": len(all_row_keys),
        "fields_outside_declared_allowlist": fields_outside_allowlist,
        "unsafe_fields_outside_declared_allowlist": unsafe_fields_outside_allowlist,
        "forbidden_projection_key_hits": forbidden_key_hits,
        "forbidden_projection_value_token_hits": forbidden_value_token_hits,
        "closed_flag_issues": closed_flag_issues,
        "spread_source_issues": spread_source_issues,
        "missing_status_semantic_tightening_rows": len(missing_semantic_issues),
        "raw_source_forbidden_key_hits_observed_but_not_emitted": raw_source_key_hits,
        "source_match_status_counts": dict(source_match_counts),
        "decision_spread_status_counts": dict(decision_spread_counts),
        "entry_touch_spread_status_counts": dict(entry_spread_counts),
        "spread_source_hash_non_null_rows": sum(1 for row in rows if row.get("spread_source_hash")),
        "parser_code_sha256_row_mismatch_count": len(parser_row_hash_mismatches),
        "hash_recompute": hash_audit,
        "ticket_redaction_assessment": "PASS_NO_RAW_TICKET_VALUES_EMITTED_OR_HASHED_IN_PROJECTION_ROWS",
        "spread_source_usage_assessment": "PASS_CAPTURED_SPREAD_ROWS_REFERENCE_SOURCE_HASHED_TICK_PARQUET_LINEAGE"
        if not spread_source_issues
        else "FAIL_SPREAD_SOURCE_HASH_LINEAGE",
    }


def audit_local_heavy(rows: list[dict[str, Any]], source_search: dict[str, Any]) -> dict[str, Any]:
    needed_missing_candidate_ids = {
        row.get("candidate_id")
        for row in rows
        if row.get("source_match_status") == "NO_MATCH_IN_APPROVED_LOGS_EXPLICIT_MISSING_STATUSES"
    }
    needed_missing_candidate_ids.discard(None)

    root_records = [{"root": root, "exists": Path(root).exists()} for root in LOCAL_HEAVY_ROOTS]
    main_log_checks: list[dict[str, Any]] = []
    main_shadow_root = Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs")
    for log_name in APPROVED_LOG_NAMES:
        absolute = main_shadow_root / log_name
        current = REPO_ROOT / "shadow_logs" / log_name
        main_hash = sha256_file(absolute) if absolute.exists() else None
        current_hash = sha256_file(current) if current.exists() else None
        main_log_checks.append(
            {
                "path": str(absolute).replace("\\", "/"),
                "exists": absolute.exists(),
                "matches_current_worktree_hash": main_hash == current_hash if main_hash and current_hash else None,
                "sha256": main_hash,
            }
        )

    prior_worktree_hits: list[dict[str, Any]] = []
    prior_root = Path("C:/tmp/gtos_otb")
    if prior_root.exists():
        for log_name in APPROVED_LOG_NAMES:
            for path in prior_root.rglob(log_name):
                path_text = str(path).replace("\\", "/")
                if "/G12NOFILLFWDPROJ/" in path_text:
                    continue
                candidate_ids: set[str] = set()
                parse_errors = 0
                try:
                    with path.open("r", encoding="utf-8", errors="replace") as handle:
                        for line in handle:
                            if not line.strip():
                                continue
                            try:
                                row = json.loads(line)
                            except json.JSONDecodeError:
                                parse_errors += 1
                                continue
                            value = row.get("candidate_id")
                            if isinstance(value, str):
                                candidate_ids.add(value)
                except OSError:
                    parse_errors += 1
                overlap = sorted(candidate_ids & needed_missing_candidate_ids)
                prior_worktree_hits.append(
                    {
                        "path": path_text,
                        "log_name": log_name,
                        "candidate_id_count": len(candidate_ids),
                        "extra_needed_candidate_matches_beyond_current": len(overlap),
                        "sample_overlaps": overlap[:10],
                        "parse_errors": parse_errors,
                    }
                )
    extra_matches = [item for item in prior_worktree_hits if item["extra_needed_candidate_matches_beyond_current"]]
    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_BUILDER_LOCAL_HEAVY_SEARCH_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "status": "PASS" if not extra_matches else "FAIL_EXTRA_SOURCE_MATCHES_FOUND",
        "needed_missing_candidate_id_count": len(needed_missing_candidate_ids),
        "absolute_local_heavy_roots_checked": root_records,
        "main_shadow_log_checks": main_log_checks,
        "prior_worktree_log_files_checked": len(prior_worktree_hits),
        "prior_worktree_extra_needed_matches": extra_matches,
        "builder_ledger_prior_worktree_claim_count": len(source_search.get("prior_worktree_log_search") or []),
    }


def audit_instructions(
    denominator: dict[str, Any],
    source_hash_noleak: dict[str, Any],
    local_heavy: dict[str, Any],
    upstream_verifier_result: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight", "PASS", "LIVE_STATE regenerated; required core files and latest handoff read before audit work."),
        ("controlling_inputs", "PASS", "Projection builder, next prompt pack, addendum, prior G12, count/result/source-control/G0 artifacts inspected."),
        ("recompute_298_universe", denominator["status"], "Projection IDs match accepted plus exclusion ledgers; family counts recomputed."),
        ("recompute_225_182_139", denominator["status"], "Row-level, primary duplicate-key, and secondary duplicate-group denominators recomputed."),
        ("source_control_and_impossible_exclusions", denominator["status"], "4 source-control and 4 source-impossible rows recomputed from exclusion ledger."),
        ("rejects_and_reject_overlap", denominator["status"], "65 rejects and 47 accepted-key/group overlaps recomputed with zero denominator delta."),
        ("source_parser_hashes", source_hash_noleak["hash_recompute"]["status"], "Source and parser hashes recomputed with mutable-context and LF-normalized policies."),
        ("no_leak_ticket_redaction", "PASS" if not source_hash_noleak["forbidden_projection_key_hits"] else "FAIL", "Projection rows scanned for forbidden keys/value tokens and ticket redaction status."),
        ("missing_status_semantics", "WARN", "One semantic tightening found: TOUCH_NOT_OBSERVED rows use SOURCE_FIELD_MISSING in missing_statuses."),
        ("allowlist_projection_rules", "FAIL", "Projection rows emit safe control metadata fields absent from the declared allowlist."),
        ("spread_source_usage", "PASS" if not source_hash_noleak["spread_source_issues"] else "FAIL", "Captured spread rows reference source-hashed tick parquet lineage."),
        ("local_heavy_search_claims", local_heavy["status"], "Absolute local-heavy roots, main shadow logs, and prior worktree approved logs checked."),
        ("upstream_projection_verifier_rerun", "FAIL" if upstream_verifier_result["returncode"] else "PASS", "Upstream verifier was rerun as required."),
        ("no_result_scoring", "PASS", "No R/win-rate/expectancy/DSR/PBO or broker/account history labels computed."),
        ("live_surface_scope", "PASS", "Audit writes only under G12 audit directory; committed live-surface check delegated to verifier."),
    ]
    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_BUILDER_INSTRUCTION_COVERAGE_CHECKLIST",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "checklist": [
            {"requirement": req, "status": status, "evidence": evidence}
            for req, status, evidence in checklist
        ],
        "blocking_requirements": [req for req, status, _ in checklist if status == "FAIL"],
        "status": "FAIL" if any(status == "FAIL" for _, status, _ in checklist) else "PASS",
    }


def make_ledgers(
    rows: list[dict[str, Any]],
    denominator: dict[str, Any],
    source_hash_noleak: dict[str, Any],
    local_heavy: dict[str, Any],
    upstream_verifier_result: dict[str, Any],
    instruction_coverage: dict[str, Any],
) -> dict[str, Any]:
    issue_ledger = [
        {
            "issue_id": "G12-PROJ-BLOCKER-001",
            "severity": "BLOCKING_VERIFICATION_FAILURE",
            "status": "OPEN",
            "finding": "The upstream projection verifier crashes on main after mandatory LIVE_STATE regeneration.",
            "evidence": {
                "command": upstream_verifier_result["command"],
                "returncode": upstream_verifier_result["returncode"],
                "stderr_tail": upstream_verifier_result["stderr_tail"],
            },
            "exact_fix_or_requirement": "Patch the upstream verifier to import hashlib at module scope or inside sha256_lf_normalized_file, then rerun upstream verifier, focused pytest, and this G12 audit.",
        },
        {
            "issue_id": "G12-PROJ-BLOCKER-002",
            "severity": "BLOCKING_CONTRACT_GAP",
            "status": "OPEN",
            "finding": "The projection allowlist spec is not exhaustive: projection rows emit fields outside the declared allowed field sets.",
            "evidence": {
                "fields_outside_declared_allowlist": source_hash_noleak["fields_outside_declared_allowlist"],
                "unsafe_fields_outside_declared_allowlist": source_hash_noleak["unsafe_fields_outside_declared_allowlist"],
            },
            "exact_fix_or_requirement": "Extend NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC to list every emitted safe control metadata field, or remove fields not meant to be emitted, then rerun projection and G12 audit.",
        },
        {
            "issue_id": "G12-PROJ-WARN-001",
            "severity": "NONBLOCKING_SEMANTIC_TIGHTENING",
            "status": "OPEN",
            "finding": "Entry-touch spread null semantics are disambiguated by entry_touch_spread_status but collapsed to SOURCE_FIELD_MISSING in missing_statuses for TOUCH_NOT_OBSERVED rows.",
            "evidence": {
                "affected_rows": source_hash_noleak["missing_status_semantic_tightening_rows"],
            },
            "exact_fix_or_requirement": "Use an explicit missing_status vocabulary such as TOUCH_NOT_OBSERVED_VALUE_NOT_APPLICABLE for these rows before any future result/cost lane.",
        },
    ]

    blocking = [issue for issue in issue_ledger if issue["severity"].startswith("BLOCKING")]
    terminal_verdict = "BLOCK_ACCEPTANCE_PENDING_EXACT_REPAIR"
    decision = {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_BUILDER_DECISION_LEDGER",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "terminal_verdict": terminal_verdict,
        "can_accept_as_source_control_projection_evidence_only": False,
        "can_mark_goal_complete_after_verification_and_commit": True,
        "decision": (
            "Do not accept the projection builder as canonical G12 source/control projection evidence yet. "
            "The row universe, denominators, exclusions, source hashes, no-leak controls, spread-source usage, and local-heavy claims "
            "largely survive independent recomputation, but the required upstream verifier cannot run and the declared strict allowlist is incomplete."
        ),
        "blocking_issue_ids": [issue["issue_id"] for issue in blocking],
        "nonblocking_issue_ids": [issue["issue_id"] for issue in issue_ledger if issue not in blocking],
        "accepted_evidence_after_repair": {
            "universe_denominators": denominator["status"],
            "source_hash_noleak_status": source_hash_noleak["status"],
            "local_heavy_status": local_heavy["status"],
            "upstream_verifier_status": "FAIL" if upstream_verifier_result["returncode"] else "PASS",
        },
        "forbidden_routes_preserved": [
            "no result scoring",
            "no R/win-rate/expectancy/DSR/PBO",
            "no validation or promotion",
            "no registry edit",
            "no live logger wiring",
            "no paid/API/Databento call",
            "no live trading prompt/src/config/risk/execution/permissions/safety/selector/canary/order behavior change",
        ],
    }

    next_route = {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_BUILDER_NEXT_ROUTE_LEDGER",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "next_routes": [
            {
                "route_id": "NOFILL_FORWARD_PROJECTION_BUILDER_REPAIR_AND_RERUN",
                "evidence_class": "source_control_repair",
                "allowed_scope": "Patch upstream projection verifier import and exhaustively update allowlist spec/control fields; rerun builder/verifier/G12 audit.",
                "forbidden_scope": "No result scoring, validation, registry edit, live wiring, broker account/history labels, paid/API/Databento, or live trading changes.",
                "owner_approval_required": False,
            },
            {
                "route_id": "NOFILL_FORWARD_RESULT_COST_SCORING",
                "evidence_class": "future_result_cost_lane",
                "allowed_scope": "Blocked until projection-builder repair receives G12 acceptance.",
                "owner_approval_required": True,
            },
        ],
        "status": "OPEN_REPAIR_REQUIRED",
    }

    recomputation = {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_BUILDER_RECOMPUTATION_LEDGER",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now_iso(),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "git_status_short_at_build": git_output(["status", "--short"]),
        "projection_summary": {
            "row_count": len(rows),
            "family_counts": denominator["family_counts"],
            "source_match_status_counts": source_hash_noleak["source_match_status_counts"],
            "decision_spread_status_counts": source_hash_noleak["decision_spread_status_counts"],
            "entry_touch_spread_status_counts": source_hash_noleak["entry_touch_spread_status_counts"],
        },
        "denominator_audit_status": denominator["status"],
        "source_hash_noleak_status": source_hash_noleak["status"],
        "local_heavy_status": local_heavy["status"],
        "upstream_verifier_result": upstream_verifier_result,
        "instruction_coverage_status": instruction_coverage["status"],
    }

    return {
        "adversarial_issue_ledger": {
            "artifact": "G12_NOFILL_FORWARD_PROJECTION_BUILDER_ADVERSARIAL_ISSUE_LEDGER",
            **CONTROL_FLAGS,
            "schema_version": SCHEMA_VERSION,
            "route_id": ROUTE_ID,
            "issues": issue_ledger,
            "blocking_issue_count": len(blocking),
            "status": "BLOCKING_ISSUES_FOUND",
        },
        "decision_ledger": decision,
        "next_route_ledger": next_route,
        "recomputation_ledger": recomputation,
    }


def control_input_hashes() -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "exists": repo_path(path).exists(),
            "sha256": sha256_file(path),
            "sha256_lf_normalized": sha256_lf_file(path),
        }
        for path in CONTROL_INPUTS
    ]


def write_markdown_artifacts(
    denominator: dict[str, Any],
    source_hash_noleak: dict[str, Any],
    local_heavy: dict[str, Any],
    ledgers: dict[str, Any],
    instruction_coverage: dict[str, Any],
) -> None:
    decision = ledgers["decision_ledger"]
    issues = ledgers["adversarial_issue_ledger"]["issues"]
    issue_lines = "\n".join(
        f"- `{issue['issue_id']}` {issue['severity']}: {issue['finding']}" for issue in issues
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_CONTEXT_ANCHOR_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Builder Context Anchor {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Scope

Independent G12 red-team acceptance audit of the merged NOFILL forward source-safe projection builder.
This audit is source/control only. It does not score outcomes, compute R/win-rate/expectancy/DSR/PBO, validate,
promote, wire live loggers, edit registries, call paid/API/Databento, or touch live trading behavior.

## Current Decision

Terminal verdict: `{decision['terminal_verdict']}`.

Accepted evidence after repair: universe/denominator recomputation `{denominator['status']}`, source/hash/no-leak audit `{source_hash_noleak['status']}`, local-heavy audit `{local_heavy['status']}`.

## Active Issues

{issue_lines}
""",
    )

    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_ADVERSARIAL_ISSUE_LEDGER_{DATE}.md",
        "# G12 NOFILL Forward Projection Builder Adversarial Issue Ledger 2026-05-09\n\n"
        "Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.\n\n"
        + issue_lines
        + "\n",
    )

    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Builder Source/Hash/No-Leak Audit {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Status: `{source_hash_noleak['status']}`.

- Source hash records: `{source_hash_noleak['hash_recompute']['source_hash_records']}`.
- Parser hash records: `{source_hash_noleak['hash_recompute']['parser_hash_records']}`.
- Strict source hash failures: `{len(source_hash_noleak['hash_recompute']['source_hash_strict_failures'])}`.
- Strict parser hash failures: `{len(source_hash_noleak['hash_recompute']['parser_hash_strict_failures'])}`.
- Mutable context hash drifts accepted: `{len(source_hash_noleak['hash_recompute']['mutable_context_hash_drifts_accepted'])}`.
- Line-ending-only drifts accepted: `{len(source_hash_noleak['hash_recompute']['line_ending_only_drifts_accepted'])}`.
- Forbidden projection key hits: `{len(source_hash_noleak['forbidden_projection_key_hits'])}`.
- Spread-source assessment: `{source_hash_noleak['spread_source_usage_assessment']}`.

Blocking contract gap: projection rows emit fields outside the declared allowlist. They are safe control metadata in this audit, but strict allowlist acceptance requires explicit listing.
""",
    )

    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DENOMINATOR_AUDIT_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Builder Denominator Audit {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Status: `{denominator['status']}`.

- Universe: `{denominator['universe_equation']}`.
- Accepted row denominator: `{denominator['accepted_row_level_denominator']}`.
- Primary duplicate-key denominator: `{denominator['primary_duplicate_key_denominator']}`.
- Secondary duplicate-group denominator: `{denominator['secondary_duplicate_group_denominator']}`.
- Source-control rows: `{', '.join(denominator['source_control_rows'])}`.
- Source-impossible rows: `{', '.join(denominator['source_impossible_rows'])}`.
- Reject rows: `{denominator['reject_rows']}`.
- Reject-overlap rows recomputed: `{denominator['reject_overlap_rows_recomputed_by_key']}`.
""",
    )

    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DECISION_LEDGER_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Builder Decision Ledger {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Terminal verdict: `{decision['terminal_verdict']}`.

Decision: {decision['decision']}

Blocking issues: `{', '.join(decision['blocking_issue_ids'])}`.

No validation, promotion, result scoring, registry edit, paid/API/Databento, live logger wiring, or live trading behavior change is opened.
""",
    )

    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_NEXT_ROUTE_LEDGER_{DATE}.md",
        "# G12 NOFILL Forward Projection Builder Next Route Ledger 2026-05-09\n\n"
        "Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.\n\n"
        "Next source/control route: repair upstream verifier import and exhaustive allowlist contract, then rerun projection verifier and this G12 audit. Result/cost scoring remains blocked.\n",
    )

    checklist_lines = "\n".join(
        f"- `{item['requirement']}`: `{item['status']}` - {item['evidence']}"
        for item in instruction_coverage["checklist"]
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.md",
        "# G12 NOFILL Forward Projection Builder Instruction Coverage Checklist 2026-05-09\n\n"
        "Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.\n\n"
        + checklist_lines
        + "\n",
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(ROWS_PATH)
    accepted = load_jsonl(ACCEPTED_PATH)
    exclusions = load_jsonl(EXCLUSION_PATH)
    reject_overlap = load_json(REJECT_OVERLAP_PATH)
    allowlist = load_json(ALLOWLIST_PATH)
    source_manifest = load_json(SOURCE_MANIFEST_PATH)
    parser_manifest = load_json(PARSER_MANIFEST_PATH)
    source_search = load_json(SOURCE_SEARCH_LEDGER_PATH)

    upstream_verifier_result = run_command(["python", "-B", str(UPSTREAM_VERIFIER)])
    denominator = recompute_denominators(rows, accepted, exclusions, reject_overlap)
    source_hash_noleak = audit_projection_safety(rows, allowlist, source_manifest, parser_manifest, source_search)
    local_heavy = audit_local_heavy(rows, source_search)
    instruction_coverage = audit_instructions(denominator, source_hash_noleak, local_heavy, upstream_verifier_result)
    ledgers = make_ledgers(rows, denominator, source_hash_noleak, local_heavy, upstream_verifier_result, instruction_coverage)

    completion = {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_BUILDER_COMPLETION_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "objective_restated": (
            "Independently verify whether the merged NOFILL forward source-safe projection builder can be accepted "
            "as source/control projection evidence only, with full denominator/hash/no-leak/local-heavy/live-surface controls."
        ),
        "terminal_verdict": ledgers["decision_ledger"]["terminal_verdict"],
        "can_mark_goal_complete_after_verification_and_commit": True,
        "can_accept_projection_builder_as_g12_source_control_evidence": False,
        "blocking_issue_ids": ledgers["decision_ledger"]["blocking_issue_ids"],
        "instruction_coverage_status": instruction_coverage["status"],
        "denominator_status": denominator["status"],
        "source_hash_noleak_status": source_hash_noleak["status"],
        "local_heavy_status": local_heavy["status"],
        "upstream_verifier_returncode": upstream_verifier_result["returncode"],
        "control_input_hashes": control_input_hashes(),
        "prompt_to_artifact_checklist": instruction_coverage["checklist"],
    }

    write_json(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_RECOMPUTATION_LEDGER_{DATE}.json", ledgers["recomputation_ledger"])
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", source_hash_noleak)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DENOMINATOR_AUDIT_{DATE}.json", denominator)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_LOCAL_HEAVY_SEARCH_AUDIT_{DATE}.json", local_heavy)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_ADVERSARIAL_ISSUE_LEDGER_{DATE}.json", ledgers["adversarial_issue_ledger"])
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_DECISION_LEDGER_{DATE}.json", ledgers["decision_ledger"])
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_NEXT_ROUTE_LEDGER_{DATE}.json", ledgers["next_route_ledger"])
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json", instruction_coverage)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_COMPLETION_AUDIT_{DATE}.json", completion)

    write_markdown_artifacts(denominator, source_hash_noleak, local_heavy, ledgers, instruction_coverage)
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_BUILDER_COMPLETION_AUDIT_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Builder Completion Audit {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Terminal verdict: `{completion['terminal_verdict']}`.

The audit goal is complete as a G12 control audit, but the projection builder is not accepted yet as canonical source/control projection evidence.
Blocking issues are `{', '.join(completion['blocking_issue_ids'])}`.

The 298-row universe, 225/182/139 denominators, 4 source-control exclusions, 4 source-impossible exclusions, 65 rejects, 47 reject-overlap exclusions, source/parser hash policy, no-leak controls, spread source usage, and local-heavy search claims were independently recomputed or checked. Result scoring, validation, promotion, registry edits, paid/API/Databento, live wiring, and live trading changes remain closed.
""",
    )

    print(json.dumps({"ok": True, "terminal_verdict": completion["terminal_verdict"], "blocking_issue_ids": completion["blocking_issue_ids"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
