"""Build the G12 audit for the blocked-17 LTF/orderflow/proxy source-status packet.

The target R2 packet is source-status/control evidence only. This audit
recomputes denominator membership, safe flags, searched-source proof,
per-card statuses, proxy non-equivalence, hash/as-of/no-leak policy, and the
next G0 prompt without opening results, validation, broker evidence, or live
behavior.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT"
EVIDENCE_CLASS = "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_ltf_proxy_blocked17_source_status_audit_v1"
DATE = "2026-05-12"

TARGET_ROUTE_ID = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17"
TARGET_EVIDENCE_CLASS = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_ONLY"
HASH_LIMIT_BYTES = 2_000_000

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
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
    "changes_live_trading_behavior": False,
}

TARGET_SAFE_FLAGS = {
    key: value
    for key, value in SAFE_FLAGS.items()
    if key not in {"changes_live_trading_behavior"}
}

ALLOWED_STATUSES = {
    "RECOVERED_SOURCE_BOUND",
    "SOURCE_EXISTS_NEEDS_PARSER",
    "PROXY_VALIDITY_REQUIRES_CONTRACT",
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
    "PROSPECTIVE_CAPTURE_REQUIRED",
    "EXACT_OWNER_ACCESS_REQUIRED",
}

VAGUE_TOKENS = ("tbd", "unknown/tbd", "maybe", "needs more data")


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent
TARGET_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17"
G0_SYNTHESIS_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis"
BLOCKED_32_PATH = G0_SYNTHESIS_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json"
TARGET_PROMPT_PATH = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/G0NAPI_R2_LTF_PROXY_SOURCE_GOAL_PROMPT_2026-05-12.md"
AUDIT_PROMPT_PATH = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md"
NEXT_G0_PROMPT_PATH = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"

TARGET_FILES = {
    "card_set": "SCID_LTF_PROXY_BLOCKED17_CARD_SET_2026-05-12.json",
    "search_roots": "SCID_LTF_PROXY_SEARCH_ROOT_LEDGER_2026-05-12.json",
    "source_inventory": "SCID_LTF_PROXY_SOURCE_INVENTORY_2026-05-12.json",
    "status_matrix": "SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json",
    "proxy_matrix": "SCID_LTF_PROXY_VALIDITY_AND_EQUIVALENCE_MATRIX_2026-05-12.json",
    "recoverable": "SCID_LTF_PROXY_RECOVERABLE_VS_NONGENERATABLE_LEDGER_2026-05-12.json",
    "parser_hash_asof": "SCID_LTF_PROXY_PARSER_HASH_ASOF_REQUIREMENTS_2026-05-12.json",
    "expansion": "SCID_LTF_PROXY_QUARANTINED_EXPANSION_OBSERVATIONS_2026-05-12.json",
    "no_leak": "SCID_LTF_PROXY_NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
    "completion": "SCID_LTF_PROXY_COMPLETION_AUDIT_2026-05-12.json",
    "verification": "SCID_LTF_PROXY_VERIFICATION_RESULT_2026-05-12.json",
    "manifest": "SCID_LTF_PROXY_OUTPUT_MANIFEST_2026-05-12.json",
}


def utc_now() -> str:
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


def write_markdown(path: Path, title: str, payload: Any) -> None:
    path.write_text(f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True)}\n```\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": artifact_family,
        "generated_at_utc": utc_now(),
    }


def target_payloads() -> dict[str, Any]:
    return {key: read_json(TARGET_DIR / filename) for key, filename in TARGET_FILES.items()}


def safe_flag_errors(name: str, payload: dict[str, Any], target: bool = False) -> list[str]:
    expected_flags = TARGET_SAFE_FLAGS if target else SAFE_FLAGS
    errors = []
    for key, expected in expected_flags.items():
        if payload.get(key) != expected:
            errors.append(f"{name}: {key} expected {expected!r}, got {payload.get(key)!r}")
    if target and payload.get("route_id") != TARGET_ROUTE_ID:
        errors.append(f"{name}: target route_id mismatch")
    if target and payload.get("evidence_class") != TARGET_EVIDENCE_CLASS:
        errors.append(f"{name}: target evidence_class mismatch")
    return errors


def build_context_anchor() -> dict[str, Any]:
    return {
        **base_payload("CONTEXT_ANCHOR"),
        "controlling_prompt": rel(AUDIT_PROMPT_PATH),
        "target_r2_prompt": rel(TARGET_PROMPT_PATH),
        "target_packet_dir": rel(TARGET_DIR),
        "mandatory_context_read_after_live_state_refresh": [
            ".context/LIVE_STATE.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            rel(TARGET_PROMPT_PATH),
        ],
        "audit_posture": "fair-adversarial source-status/control audit only",
        "proof_or_impossibility_stop_condition": "Accept only disk-backed exact source-status evidence; route exact parser/proxy/capture/access requirements without scoring.",
        "forbidden_surfaces": [
            "validation/results/R/PnL/win-rate/expectancy/performance",
            "promotion",
            "AI/API/paid-vendor access",
            "broker account/order/history/deal/position evidence",
            "raw market blob commit",
            "live restart/live behavior",
            "trading/risk/safety/prompt-decision changes",
        ],
    }


def build_denominator_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    blocked32 = read_json(BLOCKED_32_PATH)
    expected17 = [row for row in blocked32["blocked_cards"] if row["assigned_next_route"] == TARGET_ROUTE_ID]
    expected15 = [row for row in blocked32["blocked_cards"] if row["assigned_next_route"] != TARGET_ROUTE_ID]
    card_set = payloads["card_set"]
    included_ids = sorted(card_set["included_card_ids"])
    expected17_ids = sorted(row["card_id"] for row in expected17)
    excluded15_ids = sorted(card_set["excluded_blocked15_card_ids"])
    expected15_ids = sorted(row["card_id"] for row in expected15)
    ready8_ids = sorted(card_set.get("ready_8_excluded_card_ids", []))
    expansion_ids = sorted(card_set.get("expansion_candidate_ids_outside_denominator", []))
    boundaries = card_set.get("duplicate_denominator_boundaries", {})

    checks = {
        "blocked32_source_count": len(blocked32["blocked_cards"]) == 32,
        "included_17_count": card_set.get("included_card_count") == 17,
        "included_ids_match_g0_ledger": included_ids == expected17_ids,
        "excluded_15_count": card_set.get("excluded_blocked15_card_count") == 15,
        "excluded_15_ids_match_g0_ledger": excluded15_ids == expected15_ids,
        "ready_8_excluded_count": len(ready8_ids) == 8,
        "expansion_denominator_untouched": bool(expansion_ids) and boundaries.get("all_expansion_candidates_outside_accepted_denominator") is True,
        "accepted_40_count": boundaries.get("accepted_40_card_denominator_count") == 40,
        "blocked_32_count": boundaries.get("blocked_32_count") == 32,
        "blocked17_count": boundaries.get("blocked17_ltf_proxy_count") == 17,
        "blocked15_count": boundaries.get("blocked15_future_capture_count") == 15,
    }
    return {
        **base_payload("DENOMINATOR_RECOMPUTATION_AUDIT"),
        "checks": checks,
        "ok": all(checks.values()),
        "included_card_ids": included_ids,
        "excluded_blocked15_card_ids": excluded15_ids,
        "ready_8_excluded_card_ids": ready8_ids,
        "expansion_candidate_ids_outside_denominator": expansion_ids,
        "science_domain_counts": dict(sorted(Counter(row["science_domain"] for row in card_set["card_rows"]).items())),
        "dependency_category_counts": card_set.get("dependency_category_counts", {}),
        "source_ledger": rel(BLOCKED_32_PATH),
    }


def build_artifact_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    rows = []
    failures = []
    for key, filename in TARGET_FILES.items():
        path = TARGET_DIR / filename
        payload = payloads[key]
        flag_errors = safe_flag_errors(key, payload, target=True) if "promotion_verdict" in payload else []
        failures.extend(flag_errors)
        rows.append(
            {
                "artifact_key": key,
                "path": rel(path),
                "exists": path.exists(),
                "json_parsed": True,
                "safe_flags_ok": not flag_errors,
                "safe_flag_errors": flag_errors,
                "route_id": payload.get("route_id"),
                "evidence_class": payload.get("evidence_class"),
                "artifact_family": payload.get("artifact_family"),
                "sha256": sha256_file(path) if path.stat().st_size <= HASH_LIMIT_BYTES else None,
                "hash_status": "HASHED_NOW" if path.stat().st_size <= HASH_LIMIT_BYTES else "HASH_DEFERRED_LARGE_SUPPORTING_FILE",
            }
        )
    return {
        **base_payload("ARTIFACT_AND_SAFE_FLAGS_AUDIT"),
        "target_artifact_count": len(rows),
        "target_artifacts": rows,
        "ok": not failures,
        "failures": failures,
    }


def build_source_status_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    blocked32 = read_json(BLOCKED_32_PATH)
    expected_by_card = {
        row["card_id"]: set(row["exact_missing_fields_or_source_status"])
        for row in blocked32["blocked_cards"]
        if row["assigned_next_route"] == TARGET_ROUTE_ID
    }
    matrix = payloads["status_matrix"]
    rows = matrix["rows"]
    failures: list[str] = []
    status_counts: Counter[str] = Counter()
    terminal_counts: Counter[str] = Counter()
    per_card_rows = []
    for row in rows:
        card_id = row["card_id"]
        field_rows = row.get("field_status_rows", [])
        fields = {field_row.get("field") for field_row in field_rows}
        expected_fields = expected_by_card.get(card_id, set())
        terminal_counts[row.get("terminal_source_status", "MISSING")] += 1
        card_failures = []
        if fields != expected_fields:
            card_failures.append("field set does not match G0 blocked-32 exact missing fields")
        if row.get("may_score_results_now") is not False:
            card_failures.append("may_score_results_now is not false")
        if row.get("accepted_denominator_inclusion") is not True:
            card_failures.append("accepted denominator inclusion not true")
        if row.get("expansion_denominator_inclusion") is not False:
            card_failures.append("expansion denominator inclusion not false")
        for field_row in field_rows:
            status = field_row.get("status")
            status_counts[status] += 1
            if status not in ALLOWED_STATUSES:
                card_failures.append(f"{field_row.get('field')}: invalid status {status!r}")
            if not field_row.get("next_requirement"):
                card_failures.append(f"{field_row.get('field')}: missing exact next requirement")
            text = json.dumps(field_row, sort_keys=True).lower()
            for vague in VAGUE_TOKENS:
                if vague in text:
                    card_failures.append(f"{field_row.get('field')}: vague token {vague!r}")
        failures.extend(f"{card_id}: {failure}" for failure in card_failures)
        per_card_rows.append(
            {
                "card_id": card_id,
                "science_domain": row.get("science_domain"),
                "field_count": len(field_rows),
                "fields_match_g0_exact_missing_list": fields == expected_fields,
                "terminal_source_status": row.get("terminal_source_status"),
                "status_counts": dict(sorted(Counter(field_row.get("status") for field_row in field_rows).items())),
                "failures": card_failures,
            }
        )

    required_status_families_present = {
        status: status_counts[status] > 0
        for status in [
            "RECOVERED_SOURCE_BOUND",
            "SOURCE_EXISTS_NEEDS_PARSER",
            "PROXY_VALIDITY_REQUIRES_CONTRACT",
            "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
            "PROSPECTIVE_CAPTURE_REQUIRED",
        ]
    }
    for status, present in required_status_families_present.items():
        if not present:
            failures.append(f"missing required status family {status}")
    return {
        **base_payload("SOURCE_STATUS_RECOMPUTATION_AUDIT"),
        "ok": not failures,
        "failures": failures,
        "card_count": len(rows),
        "per_card_rows": per_card_rows,
        "status_counts": dict(sorted(status_counts.items())),
        "terminal_source_status_counts": dict(sorted(terminal_counts.items())),
        "required_status_families_present": required_status_families_present,
        "allowed_statuses": sorted(ALLOWED_STATUSES),
    }


def build_search_inventory_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    roots = payloads["search_roots"]
    inventory = payloads["source_inventory"]
    root_ids = {row.get("root_id") for row in roots.get("root_rows", [])}
    required_roots = {
        "current_route_and_source_control_artifacts",
        "current_worktree_shadow_source_status_logs",
        "current_worktree_data_tree",
        "absolute_production_data_tree",
        "absolute_production_tick_root",
        "absolute_external_source_cache",
        "sierrachart_data_root",
        "prior_gtos_worktrees",
    }
    categories = inventory.get("source_category_counts", {})
    required_categories = {
        "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT",
        "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE",
        "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE",
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL",
        "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL",
    }
    failures = []
    missing_roots = sorted(required_roots - root_ids)
    missing_categories = sorted(category for category in required_categories if categories.get(category, 0) < 1)
    if missing_roots:
        failures.append(f"missing searched roots: {missing_roots}")
    if roots.get("searched_root_count", 0) < 12:
        failures.append("searched_root_count below target packet standard")
    if not roots.get("searched_beyond_current_worktree"):
        failures.append("search did not record beyond-worktree coverage")
    if roots.get("forbidden_sources_excluded_count", 0) < 1:
        failures.append("forbidden source exclusions missing")
    if inventory.get("source_inventory_count", 0) < 100:
        failures.append("source inventory too small")
    if missing_categories:
        failures.append(f"missing required source categories: {missing_categories}")
    if inventory.get("raw_market_blob_commits_added") != 0:
        failures.append("raw market blob commits added is not zero")
    if inventory.get("forbidden_broker_account_order_history_deal_position_sources_consumed") != 0:
        failures.append("forbidden broker/account/order sources were consumed")

    return {
        **base_payload("SEARCH_ROOT_SOURCE_INVENTORY_AUDIT"),
        "ok": not failures,
        "failures": failures,
        "searched_root_count": roots.get("searched_root_count"),
        "required_roots_present": sorted(required_roots & root_ids),
        "missing_required_roots": missing_roots,
        "forbidden_sources_excluded_count": roots.get("forbidden_sources_excluded_count"),
        "source_inventory_count": inventory.get("source_inventory_count"),
        "source_category_counts": categories,
        "hash_status_counts": inventory.get("hash_status_counts", {}),
        "required_categories_present": sorted(required_categories - set(missing_categories)),
        "missing_required_categories": missing_categories,
        "root_rows": roots.get("root_rows", []),
    }


def build_proxy_hash_asof_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    proxy = payloads["proxy_matrix"]
    parser = payloads["parser_hash_asof"]
    inventory = payloads["source_inventory"]
    failures = []
    if proxy.get("broker_native_cfd_truth_claims") != 0:
        failures.append("proxy matrix claims broker-native CFD truth")
    if proxy.get("proxy_rows_context_only", 0) != len(proxy.get("equivalence_rows", [])):
        failures.append("proxy_rows_context_only does not match equivalence row count")
    for row in proxy.get("equivalence_rows", []):
        if row.get("broker_cfd_truth_allowed") is not False:
            failures.append(f"{row.get('candidate_symbol')}: broker_cfd_truth_allowed must be false")
        if row.get("equivalence_status") != "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY":
            failures.append(f"{row.get('candidate_symbol')}: equivalence status must be non-equivalent context/control only")
        if not (row.get("future_acceptance_requirement") or row.get("future_acceptance_gate")):
            failures.append(f"{row.get('candidate_symbol')}: missing future acceptance gate")
    if "never copied or committed" not in parser.get("hash_large_file_deferral_policy", "").lower():
        failures.append("hash large-file deferral policy missing no-copy/no-commit wording")
    if len(parser.get("requirement_rows", [])) < 1:
        failures.append("parser/hash/as-of requirement rows missing")
    for row in parser.get("requirement_rows", []):
        if not row.get("parser_asof_requirement"):
            failures.append(f"{row.get('dependency_group')}: missing parser/as-of requirement")
        if not row.get("source_pointer_policy"):
            failures.append(f"{row.get('dependency_group')}: missing source pointer policy")
    hash_counts = inventory.get("hash_status_counts", {})
    if not any(key.startswith("HASH_DEFERRED") for key in hash_counts):
        failures.append("large/raw hash deferral not represented")
    if not any(key.startswith("HASHED_NOW") for key in hash_counts):
        failures.append("hashed source-control artifacts not represented")
    return {
        **base_payload("PROXY_HASH_ASOF_AUDIT"),
        "ok": not failures,
        "failures": failures,
        "broker_native_cfd_truth_claims": proxy.get("broker_native_cfd_truth_claims"),
        "proxy_rows_context_only": proxy.get("proxy_rows_context_only"),
        "equivalence_row_count": len(proxy.get("equivalence_rows", [])),
        "hash_large_file_deferral_policy": parser.get("hash_large_file_deferral_policy"),
        "requirement_row_count": len(parser.get("requirement_rows", [])),
        "hash_status_counts": hash_counts,
    }


def build_noleak_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    target_no_leak = payloads["no_leak"]
    target_inventory = payloads["source_inventory"]
    failures = []
    for key, expected in TARGET_SAFE_FLAGS.items():
        if target_no_leak.get(key) != expected:
            failures.append(f"target no-leak flag {key} expected {expected!r}, got {target_no_leak.get(key)!r}")
    zero_fields = [
        "broker_account_order_history_deal_position_sources_consumed",
        "raw_market_blob_commits_added",
    ]
    for field in zero_fields:
        if target_no_leak.get(field) != 0:
            failures.append(f"target no-leak field {field} must be 0")
    false_fields = [
        "paid_vendor_or_ai_api_calls_opened",
        "live_restart_or_live_behavior_changes_opened",
        "trading_risk_safety_prompt_decision_changes_opened",
    ]
    for field in false_fields:
        if target_no_leak.get(field) is not False:
            failures.append(f"target no-leak field {field} must be false")
    if target_inventory.get("raw_market_blob_commits_added") != 0:
        failures.append("source inventory raw_market_blob_commits_added must be 0")
    if target_inventory.get("forbidden_broker_account_order_history_deal_position_sources_consumed") != 0:
        failures.append("source inventory consumed forbidden broker evidence")
    return {
        **base_payload("NOLEAK_FORBIDDEN_SURFACE_AUDIT"),
        "ok": not failures,
        "failures": failures,
        "target_no_leak_artifact": rel(TARGET_DIR / TARGET_FILES["no_leak"]),
        "forbidden_surface_closure": {
            "validation_results_performance_opened": False,
            "broker_account_order_history_deal_position_evidence_opened": False,
            "raw_market_blob_commit_opened": False,
            "paid_vendor_or_ai_api_opened": False,
            "live_restart_or_behavior_change_opened": False,
            "trading_risk_safety_prompt_decision_change_opened": False,
        },
        "safe_flags_intact": not failures,
    }


def build_decision_ledger(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = [
        "denominator",
        "artifacts",
        "source_status",
        "search_inventory",
        "proxy_hash_asof",
        "noleak",
    ]
    decision_checks = [
        {"check": check, "passed": audits[check].get("ok") is True}
        for check in checks
    ]
    blockers = [
        failure
        for check in checks
        for failure in audits[check].get("failures", [])
    ]
    terminal_decision = (
        "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY"
        if not blockers
        else "REJECT_WITH_EXACT_BLOCKERS"
    )
    return {
        **base_payload("DECISION_LEDGER"),
        "terminal_decision": terminal_decision,
        "accepted_evidence_class_only": not blockers,
        "decision_checks": decision_checks,
        "terminal_blockers": blockers,
        "fair_audit_policy": "Absence of validation/results/performance is not a blocker in this source-status lane. Blockers are limited to denominator, source, status, proxy, hash/as-of, no-leak, verifier, or forbidden-surface failures.",
    }


def build_completion_audit(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Mandatory preflight/context refresh and required context read",
            "evidence": [
                ".context/LIVE_STATE.md regenerated",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/research_current_state.md",
                ".context/00_core/local_heavy_data_inventory.md",
                rel(TARGET_PROMPT_PATH),
                rel(AUDIT_PROMPT_PATH),
            ],
            "satisfied": True,
        },
        {
            "requirement": "Recompute exact 17-card denominator from blocked-32 ledger with 15 blocked excluded and ready-8/expansion untouched",
            "evidence": "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_2026-05-12.json",
            "satisfied": audits["denominator"].get("ok") is True,
        },
        {
            "requirement": "Verify required R2 artifacts exist, parse, and carry safe flags",
            "evidence": "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_ARTIFACT_AND_SAFE_FLAGS_AUDIT_2026-05-12.json",
            "satisfied": audits["artifacts"].get("ok") is True,
        },
        {
            "requirement": "Recompute per-card exact source statuses and reject vague placeholders",
            "evidence": "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
            "satisfied": audits["source_status"].get("ok") is True,
        },
        {
            "requirement": "Verify searched roots and source inventory cover required local/source roots and forbidden exclusions",
            "evidence": "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SEARCH_ROOT_SOURCE_INVENTORY_AUDIT_2026-05-12.json",
            "satisfied": audits["search_inventory"].get("ok") is True,
        },
        {
            "requirement": "Verify proxy non-equivalence plus parser/hash/as-of policy",
            "evidence": "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_PROXY_HASH_ASOF_AUDIT_2026-05-12.json",
            "satisfied": audits["proxy_hash_asof"].get("ok") is True,
        },
        {
            "requirement": "Verify no-leak, no raw blob, and forbidden surfaces remain closed",
            "evidence": "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
            "satisfied": audits["noleak"].get("ok") is True,
        },
        {
            "requirement": "Run R2 route verifier and focused tests plus G12 verifier/focused tests",
            "evidence": "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_VERIFICATION_RESULT_2026-05-12.json finalized with focused-test flags after command reruns",
            "satisfied": "FINALIZED_BY_VERIFIER_AFTER_RERUN",
        },
        {
            "requirement": "Emit G12 decision ledger, completion audit, no-leak audit, and next G0 prompt/starter",
            "evidence": [
                "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DECISION_LEDGER_2026-05-12.json",
                "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
                "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
                rel(NEXT_G0_PROMPT_PATH),
                "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NEXT_G0_STARTER_2026-05-12.txt",
            ],
            "satisfied": decision.get("accepted_evidence_class_only") is True,
        },
    ]
    missing = [item["requirement"] for item in checklist if item["satisfied"] is False]
    return {
        **base_payload("COMPLETION_AUDIT"),
        "objective_restatement": "Independently audit the R2 blocked-17 LTF/orderflow/proxy source-status packet as source-status/control evidence only.",
        "terminal_decision": decision["terminal_decision"],
        "completion_standard_satisfied": not missing and decision.get("accepted_evidence_class_only") is True,
        "can_mark_goal_complete_after_verifier_and_focused_tests_pass": not missing and decision.get("accepted_evidence_class_only") is True,
        "missing_incomplete_or_weakly_verified_requirements": missing,
        "prompt_to_artifact_checklist": checklist,
        "non_promotion_boundary": "Accepted only as source-status/control evidence. No result scoring, validation, promotion, or live effect is opened.",
    }


def build_next_g0_prompt() -> tuple[str, str]:
    prompt = f"""# G0 Synthesis Prompt - SCID Blocked-17 LTF/Orderflow/Proxy Unblocking

Evidence class: `G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_ONLY`

Input accepted G12 audit:

`research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/`

Target source-status packet:

`research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/`

Objective: synthesize the accepted G12 blocked-17 source-status audit into a ranked, runnable unblocking route bundle. Preserve the exact accepted denominator: `17` LTF/orderflow/proxy blocked cards, `15` other blocked cards excluded, ready-8 and expansion-candidate denominators untouched.

Mandatory preflight:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/local_heavy_data_inventory.md`.
7. Read the G12 decision ledger, denominator audit, source-status recomputation audit, search/source-inventory audit, proxy/hash/as-of audit, no-leak audit, completion audit, and verification result from the accepted G12 route.

Required synthesis:

- Rank exact next route families for the blocked-17 cards: LTF parser/hash/as-of packet construction, proxy-validity contract design, prospective capture for non-generatable strategy/source-state fields, baseline/control packet repairs, and owner/access/export requirements where needed.
- Keep every unresolved dependency exact; do not use vague "needs data" wording.
- Do not open validation/results/R/PnL/win-rate/expectancy/performance, promotion, broker account/order/history/deal/position evidence, AI/API/paid-vendor access, raw market blob commits, live restart/live behavior, or trading/risk/safety/prompt-decision changes.
- Preserve proxy non-equivalence: futures/Sierra/vendor/orderflow sources may be context/control only unless a future G12 accepts a proxy-transfer or same-market contract.
- Emit runnable prompt packs/starters for the highest-ranked source-control routes and define the future result gate that remains closed until source/input prerequisites pass.

Required outputs:

- G0 decision ledger and route ranking matrix.
- Blocked-17 dependency-to-route map.
- Parser/proxy/prospective-capture/access prompt pack ledger.
- Denominator/no-leak/safe-flag audit.
- Completion audit and verifier/focused tests where useful.

Safe flags required: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    starter = (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/04_goal_prompts/G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_GOAL_PROMPT_2026-05-12.md "
        "as the complete objective; run mandatory preflight/context refresh; do not rely on chat memory; synthesize the accepted G12 blocked-17 source-status audit into ranked runnable unblocking route prompts without opening validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-behavior/trading-risk-safety-prompt-decision changes; preserve the exact 17-card denominator, exclude the other 15 blocked cards, keep ready-8 and expansion denominators untouched, preserve proxy non-equivalence, emit exact parser/proxy/prospective-capture/access routes, NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; mark complete only when the G0 synthesis completion standard is fully satisfied."
    )
    return prompt, starter


def build_output_manifest(files: dict[str, str]) -> dict[str, Any]:
    rows = []
    for key, path_text in sorted(files.items()):
        path = REPO_ROOT / path_text
        if path.exists():
            rows.append(
                {
                    "logical_name": key,
                    "path": path_text,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path) if path.stat().st_size <= HASH_LIMIT_BYTES else None,
                    "hash_status": "HASHED_NOW" if path.stat().st_size <= HASH_LIMIT_BYTES else "HASH_DEFERRED_LARGE_SUPPORTING_FILE",
                }
            )
    return {
        **base_payload("OUTPUT_MANIFEST"),
        "output_count": len(rows),
        "outputs": rows,
    }


def initial_verification_result() -> dict[str, Any]:
    return {
        **base_payload("VERIFICATION_RESULT"),
        "ok": False,
        "failure_count": 1,
        "failures": ["Run verify_g12_scid_ltf_proxy_blocked17_source_status_audit_2026_05_12.py after builder output generation and focused pytest reruns."],
        "can_mark_goal_complete": False,
        "source_route_verifier_ok": None,
        "source_route_focused_tests_ok": None,
        "g12_audit_focused_tests_ok": None,
    }


def main() -> None:
    payloads = target_payloads()
    audits = {
        "denominator": build_denominator_audit(payloads),
        "artifacts": build_artifact_audit(payloads),
        "source_status": build_source_status_audit(payloads),
        "search_inventory": build_search_inventory_audit(payloads),
        "proxy_hash_asof": build_proxy_hash_asof_audit(payloads),
        "noleak": build_noleak_audit(payloads),
    }
    context_anchor = build_context_anchor()
    decision = build_decision_ledger(audits)
    completion = build_completion_audit(audits, decision)
    next_g0_prompt, next_g0_starter = build_next_g0_prompt()

    files = {
        "builder": rel(Path(__file__)),
        "verifier": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/verify_g12_scid_ltf_proxy_blocked17_source_status_audit_2026_05_12.py",
        "focused_tests": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/test_g12_scid_ltf_proxy_blocked17_source_status_audit_2026_05_12.py",
        "context_anchor_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_CONTEXT_ANCHOR_2026-05-12.json",
        "denominator_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_2026-05-12.json",
        "artifact_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_ARTIFACT_AND_SAFE_FLAGS_AUDIT_2026-05-12.json",
        "status_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
        "inventory_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SEARCH_ROOT_SOURCE_INVENTORY_AUDIT_2026-05-12.json",
        "proxy_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_PROXY_HASH_ASOF_AUDIT_2026-05-12.json",
        "noleak_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
        "decision_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "completion_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
        "verification_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_VERIFICATION_RESULT_2026-05-12.json",
        "manifest_json": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_OUTPUT_MANIFEST_2026-05-12.json",
        "next_g0_starter": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NEXT_G0_STARTER_2026-05-12.txt",
        "next_g0_prompt": rel(NEXT_G0_PROMPT_PATH),
    }
    json_outputs = {
        files["context_anchor_json"]: context_anchor,
        files["denominator_json"]: audits["denominator"],
        files["artifact_json"]: audits["artifacts"],
        files["status_json"]: audits["source_status"],
        files["inventory_json"]: audits["search_inventory"],
        files["proxy_json"]: audits["proxy_hash_asof"],
        files["noleak_json"]: audits["noleak"],
        files["decision_json"]: decision,
        files["completion_json"]: completion,
        files["verification_json"]: initial_verification_result(),
    }
    for path_text, payload in json_outputs.items():
        write_json(REPO_ROOT / path_text, payload)
        write_markdown(
            (REPO_ROOT / path_text).with_suffix(".md"),
            payload["artifact_family"].replace("_", " ").title(),
            payload,
        )
    NEXT_G0_PROMPT_PATH.write_text(next_g0_prompt, encoding="utf-8")
    (REPO_ROOT / files["next_g0_starter"]).write_text(next_g0_starter + "\n", encoding="utf-8")
    manifest = build_output_manifest(files)
    write_json(REPO_ROOT / files["manifest_json"], manifest)
    write_markdown((REPO_ROOT / files["manifest_json"]).with_suffix(".md"), "Output Manifest", manifest)
    print(json.dumps({"route_id": ROUTE_ID, "decision": decision["terminal_decision"], "outputs": manifest["output_count"]}, indent=2))


if __name__ == "__main__":
    main()
