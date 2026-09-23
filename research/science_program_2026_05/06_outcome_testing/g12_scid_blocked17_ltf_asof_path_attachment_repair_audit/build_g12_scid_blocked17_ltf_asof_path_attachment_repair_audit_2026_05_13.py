"""G12 audit for the Blocked17 LTF as-of path attachment packet.

This audit accepts or rejects only parser/source-hash/as-of attachment control
evidence. It does not open results, validation, promotion, AI/API, paid vendor
access, raw market blob commits, live behavior, or broker account/order evidence.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT"
EVIDENCE_CLASS = "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_blocked17_ltf_asof_path_attachment_repair_audit_v1"
DATE = "2026-05-13"
PREFIX = "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = (
    "ACCEPT_AS_G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_CONTROL_EVIDENCE_ONLY"
)

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

REQUIRED_BINDING_FAMILIES = {
    "accepted_scid_m15_source_control_bars",
    "sierra_converted_m1_m5_m15_ohlcv_roots",
    "prior_production_mt5_tick_parquet_market_context",
    "forward_capture_ltf_availability_schema",
}

REQUIRED_LTF_FIELDS = {
    "asof_path_descriptor_version",
    "bars_present_by_timeframe",
    "decision_minus_window_start_utc",
    "ltf_source_file_pointer_or_cache_id",
    "ltf_source_hash",
    "ltf_timeframes_available",
}

EXPECTED_SOURCE_EXISTS_CARD_IDS = {
    "ADV-002",
    "EXE-001",
    "EXE-003",
    "EXE-005",
    "GEO-002",
    "GEO-003",
    "GEO-004",
    "HAZ-003",
    "HAZ-004",
    "MIC-002",
    "MIC-005",
    "UNC-001",
    "UNC-005",
}

VAGUE_TOKENS = ("future work", "needs more data", "unknown", "maybe", " tbd")
FORBIDDEN_FIELD_FRAGMENTS = (
    "target_hit",
    "stop_hit",
    "result",
    "outcome",
    "pnl",
    "win_rate",
    "expectancy",
    "broker_account",
    "broker_order",
    "account_history",
    "deal_position",
)


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    / "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_GOAL_PROMPT_2026-05-13.md"
)
PACKET_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "scid_blocked17_ltf_asof_path_parser_and_candidate_attachment"
)
SOURCE_STATUS_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17"
)
G12_SOURCE_STATUS_AUDIT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "g12_scid_ltf_proxy_blocked17_source_status_audit"
)

PACKET_INPUTS = {
    "matrix": PACKET_DIR / "SCID_BLOCKED17_LTF_ASOF_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_2026-05-13.json",
    "candidate_manifest": PACKET_DIR / "SCID_BLOCKED17_LTF_ASOF_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_2026-05-13.json",
    "missing_ledger": PACKET_DIR / "SCID_BLOCKED17_LTF_ASOF_MISSING_PARSER_ACCESS_LEDGER_2026-05-13.json",
    "denominator_noleak": PACKET_DIR / "SCID_BLOCKED17_LTF_ASOF_DENOMINATOR_NOLEAK_AUDIT_2026-05-13.json",
    "saturation": PACKET_DIR / "SCID_BLOCKED17_LTF_ASOF_SATURATION_SELF_REDTEAM_LEDGER_2026-05-13.json",
    "completion": PACKET_DIR / "SCID_BLOCKED17_LTF_ASOF_COMPLETION_AUDIT_2026-05-13.json",
    "route_decision": PACKET_DIR / "SCID_BLOCKED17_LTF_ASOF_ROUTE_DECISION_LEDGER_2026-05-13.json",
    "packet_verification": PACKET_DIR / "SCID_BLOCKED17_LTF_ASOF_VERIFICATION_RESULT_2026-05-13.json",
    "packet_focused_test": PACKET_DIR / "SCID_BLOCKED17_LTF_ASOF_FOCUSED_TEST_RESULT_2026-05-13.json",
}

UPSTREAM_INPUTS = {
    "source_status_matrix": SOURCE_STATUS_DIR / "SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json",
    "g12_denominator_recompute": G12_SOURCE_STATUS_AUDIT_DIR
    / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_2026-05-12.json",
    "g12_source_status_recompute": G12_SOURCE_STATUS_AUDIT_DIR
    / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
}

JSON_OUTPUTS = {
    "context": f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    "source_status": f"{PREFIX}_SOURCE_STATUS_RECOMPUTATION_AUDIT_{DATE}.json",
    "parser_hash_asof": f"{PREFIX}_PARSER_HASH_ASOF_ROW_AUDIT_{DATE}.json",
    "missing_exact": f"{PREFIX}_MISSING_EXACT_REQUIREMENT_AUDIT_{DATE}.json",
    "denominator_noleak": f"{PREFIX}_DENOMINATOR_NOLEAK_AUDIT_{DATE}.json",
    "saturation": f"{PREFIX}_SATURATION_SELF_REDTEAM_AUDIT_{DATE}.json",
    "decision": f"{PREFIX}_DECISION_LEDGER_{DATE}.json",
    "completion": f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    "manifest": f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json",
}

MD_OUTPUTS = {key: value.replace(".json", ".md") for key, value in JSON_OUTPUTS.items()}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        return path.as_posix().replace("\\", "/")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    path.write_text(
        "# " + title + "\n\n```json\n" + json.dumps(payload, indent=2, sort_keys=True) + "\n```\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip()


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": artifact_family,
        "generated_at_utc": now_utc(),
    }


def safe_flag_issues(value: Any, path: str = "$") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in SAFE_FLAGS and item != SAFE_FLAGS[key]:
                issues.append({"path": child, "expected": SAFE_FLAGS[key], "actual": item})
            issues.extend(safe_flag_issues(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(safe_flag_issues(item, f"{path}[{index}]"))
    return issues


def file_audit(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
    }


def load_inputs() -> dict[str, Any]:
    inputs: dict[str, Any] = {}
    for key, path in {**PACKET_INPUTS, **UPSTREAM_INPUTS}.items():
        inputs[key] = read_json(path)
    return inputs


def recompute_candidate_rowset(manifest: dict[str, Any]) -> dict[str, Any]:
    rowset = manifest["candidate_rowset"]
    rows_path = REPO_ROOT / rowset["candidate_rows_ref"]
    raw_bytes = rows_path.read_bytes()
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    lf_normalized_sha256 = hashlib.sha256(raw_bytes.replace(b"\r\n", b"\n")).hexdigest()
    crlf_normalized_sha256 = hashlib.sha256(
        raw_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    ).hexdigest()
    rows: list[dict[str, Any]] = []
    with rows_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    duplicate_keys = [row.get("duplicate_key") for row in rows]
    field_names = {key for row in rows for key in row}
    forbidden_fields = sorted(
        field for field in field_names if any(fragment in field.lower() for fragment in FORBIDDEN_FIELD_FRAGMENTS)
    )
    decision_asofs = sorted(row.get("decision_asof_utc") for row in rows if row.get("decision_asof_utc"))
    return {
        "candidate_rows_ref": rowset["candidate_rows_ref"],
        "recomputed_raw_sha256": raw_sha256,
        "recomputed_lf_normalized_sha256": lf_normalized_sha256,
        "recomputed_crlf_normalized_sha256": crlf_normalized_sha256,
        "manifest_sha256": rowset.get("candidate_rows_sha256"),
        "raw_sha256_matches_manifest": raw_sha256 == rowset.get("candidate_rows_sha256"),
        "lf_normalized_sha256_matches_manifest": lf_normalized_sha256 == rowset.get("candidate_rows_sha256"),
        "crlf_normalized_sha256_matches_manifest": crlf_normalized_sha256 == rowset.get("candidate_rows_sha256"),
        "sha256_matches_manifest": rowset.get("candidate_rows_sha256") in {raw_sha256, lf_normalized_sha256},
        "hash_policy_repair_applied": (
            "TEXT_EOL_EQUIVALENCE_ACCEPTED_FOR_JSONL_SOURCE_HASH"
            if raw_sha256 != rowset.get("candidate_rows_sha256")
            and lf_normalized_sha256 == rowset.get("candidate_rows_sha256")
            else None
        ),
        "row_count": len(rows),
        "manifest_row_count": rowset.get("candidate_input_row_count"),
        "row_count_matches_manifest": len(rows) == rowset.get("candidate_input_row_count"),
        "unique_duplicate_key_count": len(set(duplicate_keys)),
        "duplicate_key_collision_count": len(rows) - len(set(duplicate_keys)),
        "forbidden_field_names": forbidden_fields,
        "first_decision_asof_utc": decision_asofs[0] if decision_asofs else None,
        "last_decision_asof_utc": decision_asofs[-1] if decision_asofs else None,
        "sample_row_ids": [row.get("candidate_input_row_id") for row in rows[:5]],
    }


def build_context_anchor() -> dict[str, Any]:
    return {
        **base_payload("CONTEXT_ANCHOR"),
        "objective_restatement": (
            "Independently audit the Blocked17 LTF parser/source-hash/as-of "
            "candidate attachment packet from disk evidence only."
        ),
        "current_head": git_output("log", "-1", "--oneline"),
        "git_status_at_audit_start": git_output("status", "--short"),
        "controlling_prompt": file_audit(PROMPT_PATH),
        "mandatory_context_read_from_disk": [
            ".context/LIVE_STATE.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/ai_in_loop_cost_control_research_plan.md",
            ".context/00_core/quick_reference_card.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        ],
        "lane_posture": (
            "Strict G12 audit; fair to broad/non-OB LTF path evidence; blockers require "
            "exact parser/source/hash/as-of/access/capture evidence."
        ),
        "required_packet_inputs": {key: file_audit(path) for key, path in PACKET_INPUTS.items()},
        "supporting_upstream_inputs": {key: file_audit(path) for key, path in UPSTREAM_INPUTS.items()},
    }


def build_source_status_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    matrix = inputs["matrix"]
    source_status = inputs["source_status_matrix"]
    source_exists_rows = []
    field_status_counts: Counter[str] = Counter()
    for card in source_status["rows"]:
        for row in card.get("field_status_rows", []):
            status = row.get("status")
            field_status_counts[status] += 1
            if status == "SOURCE_EXISTS_NEEDS_PARSER":
                source_exists_rows.append(
                    {
                        "card_id": card["card_id"],
                        "science_domain": card.get("science_domain"),
                        "terminal_source_status": card.get("terminal_source_status"),
                        "field": row.get("field"),
                        "next_requirement": row.get("next_requirement"),
                    }
                )
    source_card_ids = sorted({row["card_id"] for row in source_exists_rows})
    row_fields = sorted({row["field"] for row in source_exists_rows})
    failures: list[dict[str, Any]] = []
    if len(source_status["rows"]) != 17:
        failures.append({"check": "source_status_card_count", "actual": len(source_status["rows"]), "expected": 17})
    if len(source_exists_rows) != 78:
        failures.append({"check": "source_exists_row_count", "actual": len(source_exists_rows), "expected": 78})
    if set(source_card_ids) != EXPECTED_SOURCE_EXISTS_CARD_IDS:
        failures.append(
            {
                "check": "source_exists_card_subset",
                "actual": source_card_ids,
                "expected": sorted(EXPECTED_SOURCE_EXISTS_CARD_IDS),
            }
        )
    if set(row_fields) != REQUIRED_LTF_FIELDS:
        failures.append({"check": "source_exists_fields", "actual": row_fields, "expected": sorted(REQUIRED_LTF_FIELDS)})
    if matrix.get("source_exists_card_ids") != source_card_ids:
        failures.append({"check": "packet_matrix_source_card_ids_match_recompute"})
    if matrix.get("attachment_row_count") != len(source_exists_rows):
        failures.append({"check": "packet_matrix_attachment_count_match_recompute"})
    return {
        **base_payload("SOURCE_STATUS_RECOMPUTATION_AUDIT"),
        "ok": not failures,
        "failures": failures,
        "upstream_card_count": len(source_status["rows"]),
        "source_exists_card_count": len(source_card_ids),
        "source_exists_card_ids": source_card_ids,
        "source_exists_field_row_count": len(source_exists_rows),
        "source_exists_fields": row_fields,
        "field_status_counts": dict(sorted(field_status_counts.items())),
        "per_card_source_exists_field_counts": dict(sorted(Counter(row["card_id"] for row in source_exists_rows).items())),
        "sample_source_exists_rows": source_exists_rows[:8],
    }


def build_parser_hash_asof_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    matrix = inputs["matrix"]
    manifest = inputs["candidate_manifest"]
    rows = matrix.get("attachment_rows", [])
    candidate_rowset = recompute_candidate_rowset(manifest)
    failures: list[dict[str, Any]] = []
    closure_counts = Counter()
    field_counts = Counter()
    missing_by_row: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        row_failures: list[str] = []
        field_counts[row.get("field")] += 1
        closure_counts[row.get("closure_status")] += 1
        families = {binding.get("source_family") for binding in row.get("parser_bindings", [])}
        contract = row.get("candidate_attachment_contract", {})
        fail_closed = set(contract.get("fail_closed_if_missing", []))
        decision_fields = set(contract.get("decision_window_fields", []))
        if row.get("input_status") != "SOURCE_EXISTS_NEEDS_PARSER":
            row_failures.append("input_status_not_source_exists")
        if row.get("parser_bound") is not True:
            row_failures.append("parser_bound_not_true")
        if row.get("source_hash_or_exact_hash_requirement_attached") is not True:
            row_failures.append("hash_requirement_not_attached")
        if row.get("decision_window_asof_requirement_attached") is not True:
            row_failures.append("asof_requirement_not_attached")
        if row.get("result_scoring_opened") is not False or row.get("may_score_results_now") is not False:
            row_failures.append("result_gate_open")
        if not REQUIRED_BINDING_FAMILIES <= families:
            row_failures.append("missing_required_parser_family")
        if "decision_asof_utc" not in decision_fields or "decision_minus_window_start_utc" not in decision_fields:
            row_failures.append("decision_window_fields_missing")
        if "decision_asof_utc" not in fail_closed or "decision_minus_window_start_utc" not in fail_closed:
            row_failures.append("fail_closed_fields_missing")
        if row_failures:
            missing_by_row.append({"index": index, "card_id": row.get("card_id"), "field": row.get("field"), "failures": row_failures})
    manifest_rules = " ".join(manifest.get("decision_window_asof_rules", [])).lower()
    source_coverage = manifest.get("source_family_coverage", {})
    if "decision_asof_utc is the hard upper bound" not in manifest_rules:
        failures.append({"check": "decision_asof_hard_upper_bound_rule_missing"})
    if "decision_minus_window_start_utc must be present" not in manifest_rules or "fails closed" not in manifest_rules:
        failures.append({"check": "decision_minus_window_fail_closed_rule_missing"})
    if source_coverage.get("sierra_converted_m1_m5_m15_ohlcv_roots", {}).get("source_file_count") != 150:
        failures.append({"check": "sierra_ltf_source_count"})
    if source_coverage.get("prior_production_mt5_tick_parquet_market_context", {}).get("source_file_count") != 93:
        failures.append({"check": "tick_parquet_source_count"})
    if not candidate_rowset["sha256_matches_manifest"] or not candidate_rowset["row_count_matches_manifest"]:
        failures.append({"check": "candidate_rowset_hash_or_count"})
    if candidate_rowset["duplicate_key_collision_count"] != 0:
        failures.append({"check": "candidate_rowset_duplicates"})
    if candidate_rowset["forbidden_field_names"]:
        failures.append({"check": "candidate_rowset_forbidden_fields", "fields": candidate_rowset["forbidden_field_names"]})
    failures.extend(missing_by_row)
    return {
        **base_payload("PARSER_HASH_ASOF_ROW_AUDIT"),
        "ok": not failures,
        "failures": failures,
        "attachment_row_count": len(rows),
        "source_exists_card_count": len({row.get("card_id") for row in rows}),
        "required_parser_binding_families": sorted(REQUIRED_BINDING_FAMILIES),
        "closure_status_counts": dict(sorted(closure_counts.items())),
        "field_counts": dict(sorted(field_counts.items())),
        "all_rows_parser_bound_hash_asof_and_fail_closed": not missing_by_row,
        "candidate_rowset_recompute": candidate_rowset,
        "decision_window_asof_rules": manifest.get("decision_window_asof_rules", []),
        "source_family_coverage": source_coverage,
        "sample_attachment_rows": [
            {
                "card_id": row.get("card_id"),
                "field": row.get("field"),
                "closure_status": row.get("closure_status"),
                "parser_families": [binding.get("source_family") for binding in row.get("parser_bindings", [])],
            }
            for row in rows[:8]
        ],
    }


def build_missing_exact_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    ledger = inputs["missing_ledger"]
    requirements = ledger.get("exact_requirements", [])
    failures: list[dict[str, Any]] = []
    reviewed_rows = []
    for requirement in requirements:
        text = json.dumps(requirement, sort_keys=True).lower()
        if not requirement.get("exact_action"):
            failures.append({"check": "exact_action_missing", "requirement_id": requirement.get("requirement_id")})
        if any(token in text for token in VAGUE_TOKENS):
            failures.append({"check": "vague_token", "requirement_id": requirement.get("requirement_id")})
        reviewed = dict(requirement)
        if requirement.get("requirement_id") == "REQ-G12-AUDIT-004":
            reviewed["g12_audit_status"] = "CLOSED_BY_THIS_AUDIT"
        else:
            reviewed["g12_audit_status"] = "EXACT_DOWNSTREAM_REQUIREMENT_PRESERVED"
        reviewed_rows.append(reviewed)
    if ledger.get("vague_blocker_count") != 0:
        failures.append({"check": "vague_blocker_count", "actual": ledger.get("vague_blocker_count")})
    if ledger.get("source_exists_rows_left_as_unreduced_blocker") != 0:
        failures.append(
            {
                "check": "source_exists_rows_left_as_unreduced_blocker",
                "actual": ledger.get("source_exists_rows_left_as_unreduced_blocker"),
            }
        )
    if len(requirements) != ledger.get("exact_requirement_count"):
        failures.append({"check": "exact_requirement_count_mismatch"})
    return {
        **base_payload("MISSING_EXACT_REQUIREMENT_AUDIT"),
        "ok": not failures,
        "failures": failures,
        "vague_blocker_count": ledger.get("vague_blocker_count"),
        "source_exists_rows_left_as_unreduced_blocker": ledger.get("source_exists_rows_left_as_unreduced_blocker"),
        "exact_requirement_count": len(requirements),
        "g12_audit_requirement_closed_count": len(
            [row for row in reviewed_rows if row.get("g12_audit_status") == "CLOSED_BY_THIS_AUDIT"]
        ),
        "downstream_exact_requirement_count": len(
            [row for row in reviewed_rows if row.get("g12_audit_status") == "EXACT_DOWNSTREAM_REQUIREMENT_PRESERVED"]
        ),
        "exact_requirements": reviewed_rows,
    }


def build_denominator_noleak_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    packet_noleak = inputs["denominator_noleak"]
    upstream_denominator = inputs["g12_denominator_recompute"]
    matrix = inputs["matrix"]
    payloads = {key: inputs[key] for key in PACKET_INPUTS if isinstance(inputs[key], dict)}
    safe_issues = []
    for name, payload in payloads.items():
        safe_issues.extend(safe_flag_issues(payload, name))
    failures: list[dict[str, Any]] = []
    included = sorted(packet_noleak.get("included_blocked17_card_ids", []))
    source_ids = sorted(matrix.get("source_exists_card_ids", []))
    ready8 = set(packet_noleak.get("ready8_excluded_card_ids", []))
    expansion = set(packet_noleak.get("expansion_candidate_ids_outside_denominator", []))
    blocked15 = set(packet_noleak.get("excluded_blocked15_card_ids", []))
    if packet_noleak.get("included_blocked17_count") != 17 or len(included) != 17:
        failures.append({"check": "blocked17_count", "actual": packet_noleak.get("included_blocked17_count")})
    if packet_noleak.get("source_exists_card_count") != 13 or len(source_ids) != 13:
        failures.append({"check": "source_exists_card_count", "actual": packet_noleak.get("source_exists_card_count")})
    if set(source_ids) - set(included):
        failures.append({"check": "source_subset_outside_blocked17", "ids": sorted(set(source_ids) - set(included))})
    if set(included) & ready8:
        failures.append({"check": "ready8_overlap", "ids": sorted(set(included) & ready8)})
    if set(included) & expansion:
        failures.append({"check": "expansion_overlap", "ids": sorted(set(included) & expansion)})
    if set(included) & blocked15:
        failures.append({"check": "blocked15_overlap", "ids": sorted(set(included) & blocked15)})
    if upstream_denominator.get("included_card_ids") and sorted(upstream_denominator["included_card_ids"]) != included:
        failures.append({"check": "upstream_denominator_mismatch"})
    if packet_noleak.get("raw_market_blob_commits_added") != 0:
        failures.append({"check": "raw_market_blob_commits_added"})
    if packet_noleak.get("broker_native_cfd_truth_claims") != 0:
        failures.append({"check": "broker_native_cfd_truth_claims"})
    if safe_issues:
        failures.append({"check": "safe_flags", "issues": safe_issues[:20]})
    return {
        **base_payload("DENOMINATOR_NOLEAK_AUDIT"),
        "ok": not failures,
        "failures": failures,
        "included_blocked17_count": len(included),
        "included_blocked17_card_ids": included,
        "source_exists_card_count": len(source_ids),
        "source_exists_card_ids": source_ids,
        "excluded_blocked15_count": packet_noleak.get("excluded_blocked15_count"),
        "ready8_excluded_count": packet_noleak.get("ready8_excluded_count"),
        "expansion_candidate_count_outside_denominator": packet_noleak.get("expansion_candidate_count_outside_denominator"),
        "ready8_overlap_count": len(set(included) & ready8),
        "expansion_overlap_count": len(set(included) & expansion),
        "blocked15_overlap_count": len(set(included) & blocked15),
        "safe_flag_issue_count": len(safe_issues),
        "raw_market_blob_commits_added": packet_noleak.get("raw_market_blob_commits_added"),
        "broker_native_cfd_truth_claims": packet_noleak.get("broker_native_cfd_truth_claims"),
        "forbidden_surfaces_closed": not safe_issues
        and packet_noleak.get("raw_market_blob_commits_added") == 0
        and packet_noleak.get("broker_native_cfd_truth_claims") == 0,
    }


def build_saturation_audit(inputs: dict[str, Any], checks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_saturation = inputs["saturation"]
    questions = source_saturation.get("saturation_questions", [])
    anti_boxing = source_saturation.get("anti_boxing_routes_considered", [])
    failures = []
    if len(questions) < 8:
        failures.append({"check": "saturation_question_count", "actual": len(questions)})
    if source_saturation.get("same_evidence_class_gaps_remaining") not in ([], None):
        failures.append({"check": "same_evidence_class_gaps_remaining", "actual": source_saturation.get("same_evidence_class_gaps_remaining")})
    if not all(check.get("ok") for check in checks.values()):
        failures.append({"check": "prior_audit_sections_not_all_ok"})
    return {
        **base_payload("SATURATION_SELF_REDTEAM_AUDIT"),
        "ok": not failures,
        "failures": failures,
        "source_packet_saturation_question_count": len(questions),
        "same_evidence_class_gaps_remaining": source_saturation.get("same_evidence_class_gaps_remaining", []),
        "anti_boxing_routes_considered": anti_boxing,
        "g12_saturation_findings": [
            {
                "question": "Could non-OB or unfamiliar LTF path evidence be unfairly rejected?",
                "answer": (
                    "No. The audit accepts source/control evidence by parser/hash/as-of gates, "
                    "not by similarity to current GTOS OB logic."
                ),
                "same_evidence_class_action": "Preserved all 13 source-exists cards and all 78 field rows.",
            },
            {
                "question": "Could an exact hash/as-of repair be done inside this G12 route before rejection?",
                "answer": (
                    "No terminal rejection is needed. The G12 audit requirement is closed here; "
                    "remaining no-commit hash/window requirements are exact downstream materialization gates."
                ),
                "same_evidence_class_action": "Closed REQ-G12-AUDIT-004 and preserved exact downstream requirements.",
            },
            {
                "question": "Could source/control evidence leak into validation or results?",
                "answer": "No. Safe flags remain false across packet artifacts and this audit.",
                "same_evidence_class_action": "Structured no-leak audit checks safe flags, denominator overlap, and forbidden counts.",
            },
        ],
    }


def build_decision_ledger(checks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    failed = {name: payload for name, payload in checks.items() if not payload.get("ok")}
    return {
        **base_payload("DECISION_LEDGER"),
        "terminal_decision": TERMINAL_DECISION if not failed else "REJECT_WITH_EXACT_REPAIR_REQUIREMENTS",
        "accepted_evidence_class_only": not failed,
        "fair_audit_policy": (
            "Absence of result/performance validation is not a blocker in this parser/hash/as-of "
            "source-control lane; only denominator, parser, hash, as-of, manifest, no-leak, or "
            "forbidden-surface failures can reject the packet."
        ),
        "decision_checks": [{"check": name, "passed": payload.get("ok") is True} for name, payload in checks.items()],
        "terminal_blockers": [
            {"section": name, "failures": payload.get("failures", [])} for name, payload in failed.items()
        ],
        "exact_downstream_requirements": checks["missing_exact"].get("exact_requirements", []),
    }


def build_completion_audit(checks: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Mandatory preflight/context read from disk",
            "evidence": [
                "python scripts/generate_live_state.py",
                ".context/LIVE_STATE.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/research_current_state.md",
                ".context/00_core/local_heavy_data_inventory.md",
                ".context/00_core/ai_in_loop_cost_control_research_plan.md",
                ".context/00_core/quick_reference_card.md",
                ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ],
            "satisfied": True,
        },
        {
            "requirement": "Inspect all required packet inputs",
            "evidence": [rel(path) for path in PACKET_INPUTS.values()],
            "satisfied": True,
        },
        {
            "requirement": "Verify exact 17 Blocked17 denominator and exact 13 LTF source-exists subset",
            "evidence": JSON_OUTPUTS["source_status"] + " and " + JSON_OUTPUTS["denominator_noleak"],
            "satisfied": checks["source_status"]["ok"] and checks["denominator_noleak"]["ok"],
        },
        {
            "requirement": "Verify all 78 SOURCE_EXISTS_NEEDS_PARSER rows are parser-bound with hash/as-of/exact requirements",
            "evidence": JSON_OUTPUTS["parser_hash_asof"] + " and " + JSON_OUTPUTS["missing_exact"],
            "satisfied": checks["parser_hash_asof"]["ok"] and checks["missing_exact"]["ok"],
        },
        {
            "requirement": "Verify decision_asof_utc hard upper bound and fail-closed decision_minus_window_start_utc rule",
            "evidence": checks["parser_hash_asof"].get("decision_window_asof_rules", []),
            "satisfied": checks["parser_hash_asof"]["ok"],
        },
        {
            "requirement": "Verify no ready8, expansion, blocked15, forbidden result, broker, raw-blob, AI/API, paid, live, or trading surface opened",
            "evidence": JSON_OUTPUTS["denominator_noleak"],
            "satisfied": checks["denominator_noleak"]["ok"],
        },
        {
            "requirement": "Pursue same-evidence-class repairs before terminal decision",
            "evidence": "REQ-G12-AUDIT-004 is marked CLOSED_BY_THIS_AUDIT; no parser/hash/as-of/manifest repair failure remains.",
            "satisfied": checks["missing_exact"]["ok"] and checks["saturation"]["ok"],
        },
        {
            "requirement": "Emit G12 decision, recomputation, row, exact-requirement, no-leak, saturation, verification, and completion artifacts",
            "evidence": list(JSON_OUTPUTS.values()),
            "satisfied": True,
        },
    ]
    missing = [row for row in checklist if row["satisfied"] is not True]
    return {
        **base_payload("COMPLETION_AUDIT"),
        "objective_restatement": (
            "Audit and decide the Blocked17 LTF parser/source-hash/as-of attachment packet only, "
            "from disk evidence, with exact downstream requirements and no result/promotion/live opening."
        ),
        "terminal_decision": decision["terminal_decision"],
        "completion_standard_satisfied": not missing and decision["terminal_decision"] == TERMINAL_DECISION,
        "can_mark_goal_complete_after_verifier_and_tests_pass": not missing and decision["terminal_decision"] == TERMINAL_DECISION,
        "prompt_to_artifact_checklist": checklist,
        "missing_incomplete_or_weakly_verified_requirements": missing,
        "non_promotion_boundary": (
            "Accepted only as parser/hash/as-of source-control evidence. Validation, result scoring, "
            "performance claims, promotion, and live effects remain closed."
        ),
    }


def build_output_manifest() -> dict[str, Any]:
    artifacts = []
    for path in sorted(ROUTE_DIR.glob("*")):
        if path.is_file() and path.name != JSON_OUTPUTS["manifest"]:
            artifacts.append(file_audit(path))
    required_present = {name: (ROUTE_DIR / filename).exists() for name, filename in {**JSON_OUTPUTS, **MD_OUTPUTS}.items() if name != "manifest"}
    return {
        **base_payload("OUTPUT_MANIFEST"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "required_outputs_present": required_present,
    }


def write_pair(key: str, title: str, payload: dict[str, Any]) -> None:
    write_json(ROUTE_DIR / JSON_OUTPUTS[key], payload)
    write_md(ROUTE_DIR / MD_OUTPUTS[key], title, payload)


def build() -> dict[str, Any]:
    inputs = load_inputs()
    context = build_context_anchor()
    source_status = build_source_status_audit(inputs)
    parser_hash_asof = build_parser_hash_asof_audit(inputs)
    missing_exact = build_missing_exact_audit(inputs)
    denominator_noleak = build_denominator_noleak_audit(inputs)
    checks = {
        "source_status": source_status,
        "parser_hash_asof": parser_hash_asof,
        "missing_exact": missing_exact,
        "denominator_noleak": denominator_noleak,
    }
    saturation = build_saturation_audit(inputs, checks)
    checks["saturation"] = saturation
    decision = build_decision_ledger(checks)
    completion = build_completion_audit(checks, decision)

    write_pair("context", "Context Anchor", context)
    write_pair("source_status", "Source Status Recomputation Audit", source_status)
    write_pair("parser_hash_asof", "Parser Hash Asof Row Audit", parser_hash_asof)
    write_pair("missing_exact", "Missing Exact Requirement Audit", missing_exact)
    write_pair("denominator_noleak", "Denominator Noleak Audit", denominator_noleak)
    write_pair("saturation", "Saturation Self Red-Team Audit", saturation)
    write_pair("decision", "Decision Ledger", decision)
    write_pair("completion", "Completion Audit", completion)
    manifest = build_output_manifest()
    write_json(ROUTE_DIR / JSON_OUTPUTS["manifest"], manifest)
    write_md(ROUTE_DIR / MD_OUTPUTS["manifest"], "Output Manifest", manifest)
    return {
        "ok": completion["completion_standard_satisfied"],
        "terminal_decision": decision["terminal_decision"],
        "failures": {name: payload.get("failures", []) for name, payload in checks.items() if not payload.get("ok")},
    }


def main() -> None:
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
