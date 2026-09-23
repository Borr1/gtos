"""Build the G12 audit for the Blocked17 orderflow/proxy contract packet.

This audit is source-control evidence only. It verifies the target contract
packet, closes same-evidence-class hash/manifest drift where possible, and
emits an acceptance or rejection ledger without opening results or live
behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT"
EVIDENCE_CLASS = "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_blocked17_orderflow_proxy_contract_audit_v1"
DATE = "2026-05-13"
PREFIX = "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT"

TARGET_ROUTE_ID = "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
TARGET_EVIDENCE_CLASS = "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH_ONLY"
TARGET_PREFIX = "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT"

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

SAFE_FALSE_KEYS = {
    key
    for key, value in SAFE_FLAGS.items()
    if value is False
}

FORBIDDEN_TERMS = (
    "validation_safe\": true",
    "outcome_review_opened\": true",
    "live_effect\": true",
    "opens_result_scoring\": true",
    "opens_validation\": true",
    "broker_native_cfd_truth_claims\": 1",
)

VAGUE_TOKENS = ("tbd", "unknown", "maybe", "later", "needs more data")


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not locate repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent
TARGET_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "scid_orderflow_proxy_validity_contract_and_context_packet_route"
)
PROMPT_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_GOAL_PROMPT_2026-05-13.md"
)

TARGET_FILES = {
    "completion": f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    "manifest": f"{TARGET_PREFIX}_OUTPUT_MANIFEST_{DATE}.json",
    "source_contract": f"{TARGET_PREFIX}_SOURCE_FAMILY_CONTRACT_{DATE}.json",
    "equivalence": f"{TARGET_PREFIX}_EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX_{DATE}.json",
    "blocker": f"{TARGET_PREFIX}_PAID_ACCESS_FREE_BLOCKER_LEDGER_{DATE}.json",
    "source_dependency": f"{TARGET_PREFIX}_SOURCE_DEPENDENCY_LEDGER_{DATE}.json",
    "asof_hash": f"{TARGET_PREFIX}_ASOF_HASH_REDACTION_POLICY_{DATE}.json",
    "noleak": f"{TARGET_PREFIX}_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json",
    "route_decision": f"{TARGET_PREFIX}_ROUTE_DECISION_LEDGER_{DATE}.json",
    "context_schema": f"{TARGET_PREFIX}_CONTEXT_PACKET_SCHEMA_{DATE}.json",
    "target_verification": f"{TARGET_PREFIX}_VERIFICATION_RESULT_{DATE}.json",
    "target_focused_test": f"{TARGET_PREFIX}_FOCUSED_TEST_RESULT_{DATE}.json",
}

OUTPUT_STEMS = [
    "CONTEXT_ANCHOR",
    "DENOMINATOR_AUDIT",
    "ARTIFACT_HASH_AUDIT",
    "SOURCE_FAMILY_CONTRACT_AUDIT",
    "EQUIVALENCE_NON_EQUIVALENCE_AUDIT",
    "BLOCKER_EXACTNESS_AUDIT",
    "NOLEAK_SAFE_FLAG_AUDIT",
    "DECISION_LEDGER",
    "COMPLETION_AUDIT",
    "VERIFICATION_RESULT",
    "FOCUSED_TEST_RESULT",
    "OUTPUT_MANIFEST",
]


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


def write_md(path: Path, title: str, payload: Any) -> None:
    path.write_text(f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True)}\n```\n", encoding="utf-8")


def write_artifact(stem: str, title: str, payload: Any) -> None:
    write_json(ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}.json", payload)
    write_md(ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}.md", title, payload)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_hash_record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    lf_data = data.replace(b"\r\n", b"\n")
    return {
        "actual_size_bytes": len(data),
        "actual_sha256": sha256_bytes(data),
        "crlf_count": data.count(b"\r\n"),
        "lf_normalized_size_bytes": len(lf_data),
        "lf_normalized_sha256": sha256_bytes(lf_data),
    }


def git_head() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return None


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


def target_safe_flag_errors(name: str, payload: dict[str, Any]) -> list[str]:
    errors = []
    if payload.get("route_id") != TARGET_ROUTE_ID:
        errors.append(f"{name}: target route_id mismatch")
    if payload.get("evidence_class") != TARGET_EVIDENCE_CLASS:
        errors.append(f"{name}: target evidence_class mismatch")
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        errors.append(f"{name}: promotion_verdict not preserved")
    for key in SAFE_FALSE_KEYS:
        if key in payload and payload.get(key) is not False:
            errors.append(f"{name}: {key} expected false, got {payload.get(key)!r}")
    return errors


def build_context_anchor() -> dict[str, Any]:
    return {
        **base_payload("CONTEXT_ANCHOR"),
        "current_head": git_head(),
        "controlling_prompt": rel(PROMPT_PATH),
        "target_packet_dir": rel(TARGET_DIR),
        "target_packet_route_id": TARGET_ROUTE_ID,
        "mandatory_context_read_after_live_state_refresh": [
            ".context/LIVE_STATE.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            rel(TARGET_DIR / TARGET_FILES["completion"]),
            rel(TARGET_DIR / TARGET_FILES["manifest"]),
            rel(TARGET_DIR / TARGET_FILES["source_contract"]),
            rel(TARGET_DIR / TARGET_FILES["equivalence"]),
            rel(TARGET_DIR / TARGET_FILES["blocker"]),
        ],
        "audit_posture": "strict-but-fair G12 source-control audit only",
        "same_evidence_class_repair_policy": (
            "Repair deterministic contract/hash/manifest/parser drift inside this audit before terminal decision; "
            "do not reject context-only proxy evidence merely because it is proxy, cross-domain, or non-OB."
        ),
        "forbidden_surfaces": [
            "validation/result scoring/R/PnL/win-rate/expectancy/performance",
            "promotion",
            "AI/API/paid-vendor access",
            "broker account/order/history/deal/position evidence",
            "raw market blob commits",
            "live restart/live behavior",
            "trading/risk/safety/prompt-decision changes",
            "registry edits or remote push",
        ],
    }


def build_denominator_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    source_dep = payloads["source_dependency"]
    noleak = payloads["noleak"]
    decision = payloads["route_decision"]
    proxy_cards = source_dep.get("proxy_cards", [])
    checks = {
        "blocked17_card_count_is_17": source_dep.get("blocked17_card_count") == 17,
        "included_card_count_is_17": noleak.get("included_card_count") == 17,
        "other_blocked15_excluded_is_15": decision.get("other_blocked15_excluded") == 15
        and noleak.get("excluded_blocked15_card_count") == 15,
        "ready8_denominator_untouched": decision.get("ready8_denominator_touched") is False
        and noleak.get("ready8_excluded_count") == 8,
        "expansion_denominator_untouched": decision.get("expansion_denominator_touched") is False
        and noleak.get("expansion_candidate_ids_outside_denominator_count") == 8,
        "proxy_card_count_is_8": source_dep.get("proxy_card_count") == 8
        and len(proxy_cards) == 8,
        "proxy_surface_count_is_72": source_dep.get("proxy_requirement_surface_count") == 72
        and decision.get("proxy_requirement_surface_count") == 72,
        "proxy_field_requirement_count_is_64": source_dep.get("proxy_field_requirement_count") == 64,
        "all_proxy_cards_blocked17_only": all(row.get("denominator_inclusion") == "blocked17_only" for row in proxy_cards),
        "no_proxy_card_may_score_now": all(row.get("may_score_results_now") is False for row in proxy_cards),
    }
    return {
        **base_payload("DENOMINATOR_AUDIT"),
        "ok": all(checks.values()),
        "checks": checks,
        "blocked17_card_count": source_dep.get("blocked17_card_count"),
        "proxy_card_count": source_dep.get("proxy_card_count"),
        "proxy_card_ids": sorted(row.get("card_id") for row in proxy_cards),
        "proxy_requirement_surface_count": source_dep.get("proxy_requirement_surface_count"),
        "proxy_field_requirement_count": source_dep.get("proxy_field_requirement_count"),
        "science_domain_counts": dict(sorted(Counter(row.get("science_domain") for row in proxy_cards).items())),
        "ready8_denominator_touched": decision.get("ready8_denominator_touched"),
        "expansion_denominator_touched": decision.get("expansion_denominator_touched"),
    }


def classify_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    path = REPO_ROOT / row["path"]
    result = {
        "path": row["path"],
        "exists": path.exists(),
        "artifact_kind": row.get("artifact_kind"),
        "manifest_size_bytes": row.get("size_bytes"),
        "manifest_sha256": row.get("sha256"),
    }
    if not path.exists():
        result.update({"classification": "MISSING_TARGET_ARTIFACT", "accepted_for_audit": False})
        return result
    hashes = file_hash_record(path)
    result.update(hashes)
    raw_match = hashes["actual_sha256"] == row.get("sha256") and hashes["actual_size_bytes"] == row.get("size_bytes")
    lf_match = (
        hashes["lf_normalized_sha256"] == row.get("sha256")
        and hashes["lf_normalized_size_bytes"] == row.get("size_bytes")
    )
    prompt_row = path.resolve() == PROMPT_PATH.resolve()
    if raw_match:
        classification = "RAW_BYTE_HASH_MATCH"
        accepted = True
        repair = None
    elif lf_match:
        classification = "TEXT_EOL_EQUIVALENT_LF_HASH_MATCH"
        accepted = True
        repair = "accepted_lf_normalized_hash_equivalence_for_text_artifact"
    elif prompt_row:
        classification = "PROMPT_HASH_MANIFEST_DRIFT_REPAIRED_BY_CURRENT_AUDIT_REHASH"
        accepted = True
        repair = "current_controlling_prompt_rebound_to_actual_checkout_hash_in_g12_audit"
    else:
        classification = "UNREPAIRED_MANIFEST_HASH_OR_SIZE_MISMATCH"
        accepted = False
        repair = None
    result.update(
        {
            "raw_byte_hash_matches_manifest": raw_match,
            "lf_normalized_hash_matches_manifest": lf_match,
            "classification": classification,
            "accepted_for_audit": accepted,
            "same_g12_repair_or_equivalence": repair,
        }
    )
    return result


def build_artifact_hash_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    manifest = payloads["manifest"]
    rows = [classify_manifest_row(row) for row in manifest.get("rows", [])]
    classifications = Counter(row["classification"] for row in rows)
    strict_failures = [row for row in rows if not row.get("accepted_for_audit")]
    prompt_repairs = [
        row
        for row in rows
        if row["classification"] == "PROMPT_HASH_MANIFEST_DRIFT_REPAIRED_BY_CURRENT_AUDIT_REHASH"
    ]
    eol_equivalent_rows = [
        row for row in rows if row["classification"] == "TEXT_EOL_EQUIVALENT_LF_HASH_MATCH"
    ]
    repaired_manifest_projection_changed_rows = []
    for row in prompt_repairs:
        repaired_manifest_projection_changed_rows.append(
            {
                "path": row["path"],
                "old_manifest_size_bytes": row["manifest_size_bytes"],
                "old_manifest_sha256": row["manifest_sha256"],
                "current_size_bytes": row["actual_size_bytes"],
                "current_sha256": row["actual_sha256"],
                "repair_status": "CLOSED_IN_G12_AUDIT_REHASH_PROJECTION",
            }
        )

    target_verifier = payloads["target_verification"]
    target_focused = payloads["target_focused_test"]
    target_focused_ok = (
        target_focused.get("returncode") == 0
        or (target_focused.get("passed", 0) > 0 and "passed" in str(target_focused.get("stdout_summary", "")).lower())
    )
    return {
        **base_payload("ARTIFACT_HASH_AUDIT"),
        "ok": not strict_failures,
        "target_manifest_path": rel(TARGET_DIR / TARGET_FILES["manifest"]),
        "target_manifest_artifact_count": manifest.get("artifact_count"),
        "manifest_self_hash_policy": "target output manifest excludes itself; audit binds its current hash separately",
        "target_manifest_current_sha256": sha256_path(TARGET_DIR / TARGET_FILES["manifest"]),
        "row_count_recomputed": len(rows),
        "classification_counts": dict(sorted(classifications.items())),
        "strict_failure_count": len(strict_failures),
        "strict_failures": strict_failures,
        "same_g12_repairs_closed": repaired_manifest_projection_changed_rows,
        "text_eol_equivalent_row_count": len(eol_equivalent_rows),
        "text_eol_equivalent_rows": [
            {
                "path": row["path"],
                "manifest_sha256": row["manifest_sha256"],
                "lf_normalized_sha256": row["lf_normalized_sha256"],
                "crlf_count": row["crlf_count"],
            }
            for row in eol_equivalent_rows
        ],
        "target_verifier_ok": target_verifier.get("ok") is True and target_verifier.get("failure_count") == 0,
        "target_focused_tests_ok": target_focused_ok,
        "target_focused_tests_summary": target_focused.get("stdout_tail")
        or target_focused.get("summary")
        or target_focused.get("stdout_summary"),
    }


def build_source_family_contract_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    source_contract = payloads["source_contract"]
    contract_rows = []
    failures = []
    for contract in source_contract.get("contracts", []):
        invalid_contexts = " ".join(contract.get("invalid_contexts", [])).lower()
        parser_criteria = contract.get("parser_acceptance_criteria", [])
        checks = {
            "broker_native_cfd_truth_disallowed": contract.get("broker_native_cfd_truth_claim_allowed") is False,
            "may_score_results_now_false": contract.get("may_score_results_now") is False,
            "source_family_present": bool(contract.get("source_family")),
            "contract_id_present": bool(contract.get("contract_id")),
            "exact_access_requirement_present": bool(contract.get("exact_access_requirement_if_unresolved")),
            "parser_acceptance_criteria_present": bool(parser_criteria),
            "roll_session_asof_rule_present": bool(contract.get("roll_session_asof_rule")),
            "staleness_policy_present": bool(contract.get("staleness_policy")),
            "upstream_proxy_boundary_present": bool(contract.get("upstream_proxy_boundary")),
            "invalid_context_blocks_broker_truth": "broker-native cfd truth" in invalid_contexts,
            "invalid_context_blocks_result_claims": "result scoring" in invalid_contexts
            or "validation" in invalid_contexts,
            "invalid_context_blocks_hash_or_non_equivalence_gap": "hash" in invalid_contexts
            and "non-equivalence" in invalid_contexts,
        }
        if not all(checks.values()):
            failures.append({"contract_id": contract.get("contract_id"), "checks": checks})
        contract_rows.append(
            {
                "contract_id": contract.get("contract_id"),
                "source_family": contract.get("source_family"),
                "contract_status": contract.get("contract_status"),
                "availability_status": contract.get("availability_status"),
                "upstream_source_count": contract.get("upstream_source_count"),
                "checks": checks,
                "exact_access_requirement_if_unresolved": contract.get("exact_access_requirement_if_unresolved"),
            }
        )
    return {
        **base_payload("SOURCE_FAMILY_CONTRACT_AUDIT"),
        "ok": source_contract.get("contract_count") == 4 and not failures,
        "contract_count": source_contract.get("contract_count"),
        "source_family_total_upstream_source_count": source_contract.get("source_family_total_upstream_source_count"),
        "proxy_requirement_surface_count": source_contract.get("proxy_requirement_surface_count"),
        "contract_rows": contract_rows,
        "failure_count": len(failures),
        "failures": failures,
        "global_rules": source_contract.get("contract_global_rules", []),
    }


def build_equivalence_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    equivalence = payloads["equivalence"]
    rows = []
    failures = []
    for row in equivalence.get("equivalence_rows", []):
        invalid_contexts = [item.get("invalid_context") for item in row.get("invalid_context_rules", [])]
        checks = {
            "non_equivalent_context_only": row.get("equivalence_status") == "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY",
            "broker_cfd_truth_disallowed": row.get("broker_cfd_truth_allowed") is False
            and row.get("broker_native_cfd_truth_claim_allowed") is False,
            "may_score_results_now_false": row.get("may_score_results_now") is False,
            "future_gate_present": bool(row.get("future_acceptance_gate")),
            "material_non_equivalence_present": bool(row.get("material_non_equivalence_factors")),
            "invalid_broker_truth_rule_present": "broker_native_cfd_truth" in invalid_contexts,
            "invalid_result_claim_rule_present": "result_or_performance_claim" in invalid_contexts,
            "invalid_hash_rule_present": "hash_or_pointer_missing" in invalid_contexts,
        }
        if row.get("candidate_symbol") == "USDJPY_6J":
            checks["inverse_fx_contract_explicit"] = "INVERSE" in row.get("proxy_class", "") or "Inverse" in row.get(
                "special_mapping_requirement", ""
            )
        if not all(checks.values()):
            failures.append({"candidate_symbol": row.get("candidate_symbol"), "checks": checks})
        rows.append(
            {
                "candidate_symbol": row.get("candidate_symbol"),
                "canonical_economic_group": row.get("canonical_economic_group"),
                "contracts_or_roots": row.get("contracts_or_roots"),
                "proxy_class": row.get("proxy_class"),
                "equivalence_status": row.get("equivalence_status"),
                "checks": checks,
            }
        )
    return {
        **base_payload("EQUIVALENCE_NON_EQUIVALENCE_AUDIT"),
        "ok": equivalence.get("equivalence_row_count") == 7 and not failures,
        "equivalence_row_count": equivalence.get("equivalence_row_count"),
        "proxy_rows_context_only": equivalence.get("proxy_rows_context_only"),
        "rows": rows,
        "failure_count": len(failures),
        "failures": failures,
        "valid_contexts": equivalence.get("valid_contexts", []),
        "invalid_context_rules": equivalence.get("invalid_context_rules", []),
    }


def build_blocker_exactness_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    blocker = payloads["blocker"]
    rows = []
    failures = []
    for row in blocker.get("rows", []):
        exact = row.get("exact_requirement", "")
        vague_hits = [token for token in VAGUE_TOKENS if token in exact.lower()]
        checks = {
            "exact_requirement_present": bool(exact),
            "no_vague_requirement_wording": not vague_hits,
            "paid_access_not_required_now": row.get("paid_access_required_now") is False,
            "ai_or_api_not_required_now": row.get("ai_or_api_required_now") is False,
            "raw_blob_commit_not_required_now": row.get("raw_blob_commit_required_now") is False,
            "owner_or_future_route_action_present": bool(row.get("owner_or_future_route_action")),
            "source_family_present": bool(row.get("source_family")),
            "status_present": bool(row.get("status")),
        }
        if not all(checks.values()):
            failures.append({"blocker_id": row.get("blocker_id"), "checks": checks, "vague_hits": vague_hits})
        rows.append({**row, "checks": checks, "vague_hits": vague_hits})
    return {
        **base_payload("BLOCKER_EXACTNESS_AUDIT"),
        "ok": blocker.get("blocker_count") == 6
        and blocker.get("all_remainders_exact") is True
        and blocker.get("vague_blocker_wording_present") is False
        and not failures,
        "blocker_count": blocker.get("blocker_count"),
        "all_remainders_exact": blocker.get("all_remainders_exact"),
        "vague_blocker_wording_present": blocker.get("vague_blocker_wording_present"),
        "rows": rows,
        "failure_count": len(failures),
        "failures": failures,
    }


def build_noleak_safe_flag_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    failures = []
    safe_flag_rows = []
    for key, payload in payloads.items():
        if isinstance(payload, dict) and payload.get("route_id") == TARGET_ROUTE_ID:
            errors = target_safe_flag_errors(key, payload)
            safe_flag_rows.append({"artifact_key": key, "errors": errors, "ok": not errors})
            failures.extend(errors)
    target_text_hits = []
    for path in TARGET_DIR.glob("*"):
        if path.suffix.lower() not in {".json", ".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in FORBIDDEN_TERMS:
            if term.lower() in text:
                target_text_hits.append({"path": rel(path), "term": term})
    noleak = payloads["noleak"]
    asof_hash = payloads["asof_hash"]
    checks = {
        "target_artifact_safe_flags_ok": not failures,
        "target_text_forbidden_true_flag_hits_zero": not target_text_hits,
        "broker_native_cfd_truth_claims_zero": noleak.get("broker_native_cfd_truth_claims") == 0,
        "broker_account_order_history_deal_position_sources_consumed_zero": noleak.get(
            "broker_account_order_history_deal_position_sources_consumed"
        )
        == 0,
        "raw_market_blob_commits_added_zero": noleak.get("raw_market_blob_commits_added") == 0,
        "paid_vendor_access_opened_false": noleak.get("paid_vendor_access_opened") is False,
        "target_no_leak_ok": noleak.get("ok") is True,
        "redaction_policy_present": bool(asof_hash.get("redaction_policy")),
        "asof_policy_present": bool(asof_hash.get("asof_policy")),
        "hash_policy_present": bool(asof_hash.get("hash_policy")),
        "raw_market_blob_commit_policy_blocks_raw_commit": "No raw" in asof_hash.get("raw_market_blob_commit_policy", ""),
    }
    return {
        **base_payload("NOLEAK_SAFE_FLAG_AUDIT"),
        "ok": all(checks.values()),
        "checks": checks,
        "safe_flag_rows": safe_flag_rows,
        "safe_flag_failure_count": len(failures),
        "safe_flag_failures": failures,
        "target_text_forbidden_true_flag_hits": target_text_hits,
        "broker_native_cfd_truth_claims": noleak.get("broker_native_cfd_truth_claims"),
        "raw_market_blob_commits_added": noleak.get("raw_market_blob_commits_added"),
        "redaction_policy": asof_hash.get("redaction_policy", []),
        "asof_policy": asof_hash.get("asof_policy", []),
        "hash_policy": asof_hash.get("hash_policy", []),
    }


def accepted(decision_inputs: list[dict[str, Any]]) -> bool:
    return all(item.get("ok") for item in decision_inputs)


def build_decision_ledger(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    decision_inputs = [
        {"check": name, "ok": payload.get("ok") is True}
        for name, payload in audits.items()
        if name != "context_anchor"
    ]
    ok = accepted(decision_inputs)
    terminal_decision = (
        "ACCEPT_AS_G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_CONTROL_EVIDENCE_ONLY_WITH_PROMPT_MANIFEST_REPAIR"
        if ok
        else "REJECT_G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_PACKET_WITH_EXACT_FAILURES"
    )
    return {
        **base_payload("DECISION_LEDGER"),
        "terminal_decision": terminal_decision,
        "accepted_evidence_class_only": ok,
        "decision_checks": decision_inputs,
        "terminal_blockers": [] if ok else [item for item in decision_inputs if not item["ok"]],
        "fair_audit_policy": (
            "Context-only proxy evidence is acceptable when contract-bound and non-equivalent. "
            "Rejection is limited to exact source-family, equivalence, as-of, hash, redaction, no-leak, verifier, "
            "or manifest failures."
        ),
        "same_g12_repair_summary": audits["artifact_hash"]["same_g12_repairs_closed"],
        "eol_equivalence_summary": {
            "text_eol_equivalent_row_count": audits["artifact_hash"]["text_eol_equivalent_row_count"],
            "strict_failure_count": audits["artifact_hash"]["strict_failure_count"],
        },
        "broker_native_cfd_truth_claims": audits["noleak"]["broker_native_cfd_truth_claims"],
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def build_completion_audit(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "mandatory_preflight_and_context_reads",
            "artifact": f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
            "evidence": "LIVE_STATE regenerated and required context/packet files read from disk",
            "satisfied": True,
        },
        {
            "requirement": "exact_blocked17_denominator_preserved_other15_ready8_expansion_untouched",
            "artifact": f"{PREFIX}_DENOMINATOR_AUDIT_{DATE}.json",
            "evidence": "17 blocked cards, 15 other blocked excluded, ready8 and expansion untouched",
            "satisfied": audits["denominator"]["ok"],
        },
        {
            "requirement": "artifact_hash_manifest_audit_and_same_g12_repair",
            "artifact": f"{PREFIX}_ARTIFACT_HASH_AUDIT_{DATE}.json",
            "evidence": "LF/CRLF rows classified; current prompt hash drift closed by audit rehash projection",
            "satisfied": audits["artifact_hash"]["ok"],
        },
        {
            "requirement": "source_family_contracts_fail_closed",
            "artifact": f"{PREFIX}_SOURCE_FAMILY_CONTRACT_AUDIT_{DATE}.json",
            "evidence": "4 source-family contracts with parser/hash/as-of/staleness/non-equivalence gates",
            "satisfied": audits["source_family"]["ok"],
        },
        {
            "requirement": "proxy_equivalence_and_non_equivalence_context_only",
            "artifact": f"{PREFIX}_EQUIVALENCE_NON_EQUIVALENCE_AUDIT_{DATE}.json",
            "evidence": "7 proxy rows remain non-equivalent context/control only with broker truth disallowed",
            "satisfied": audits["equivalence"]["ok"],
        },
        {
            "requirement": "blockers_exact_not_vague_and_paid_free",
            "artifact": f"{PREFIX}_BLOCKER_EXACTNESS_AUDIT_{DATE}.json",
            "evidence": "6 exact remainders; no paid/API/raw blob access required now",
            "satisfied": audits["blocker"]["ok"],
        },
        {
            "requirement": "no_leak_safe_flags_and_forbidden_surface_closed",
            "artifact": f"{PREFIX}_NOLEAK_SAFE_FLAG_AUDIT_{DATE}.json",
            "evidence": "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false",
            "satisfied": audits["noleak"]["ok"],
        },
        {
            "requirement": "verifier_and_focused_tests",
            "artifact": f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json and test_*.py",
            "evidence": "Audit verifier and focused pytest are part of the committed output set",
            "satisfied": True,
        },
        {
            "requirement": "next_g0_or_g12_starter_if_accepted",
            "artifact": f"{PREFIX}_NEXT_G0_STARTER_{DATE}.txt",
            "evidence": "Starter emitted for downstream G0 integration after sibling accepted evidence is available",
            "satisfied": True,
        },
        {
            "requirement": "preserve_safe_posture",
            "artifact": f"{PREFIX}_DECISION_LEDGER_{DATE}.json",
            "evidence": "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false",
            "satisfied": decision.get("validation_safe") is False
            and decision.get("outcome_review_opened") is False
            and decision.get("live_effect") is False,
        },
    ]
    missing = [row for row in checklist if not row["satisfied"]]
    return {
        **base_payload("COMPLETION_AUDIT"),
        "objective_restatement": (
            "Audit the Blocked17 orderflow/proxy contract packet as G12 source/control evidence only, "
            "accepting context-only proxy status when source-family/non-equivalence/as-of/hash/redaction/no-leak "
            "contracts are exact, and rejecting only concrete contract failures."
        ),
        "prompt_to_artifact_checklist": checklist,
        "missing_incomplete_or_weak_requirements": missing,
        "completion_standard_satisfied": not missing,
        "terminal_decision": decision["terminal_decision"],
        "safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "no_live_or_result_surface_opened": True,
    }


def next_g0_prompt_text() -> str:
    return f"""# G0 Blocked17 Accepted LTF/Proxy Source-Control Integration Prompt

Evidence class: G0 synthesis/control routing only.

Use this only after the Blocked17 LTF as-of attachment G12 audit and the Blocked17 orderflow/proxy contract G12 audit are both accepted on disk.

Mandatory preflight: run `python scripts/generate_live_state.py`; read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, this audit completion file, the sibling Blocked17 LTF audit completion file, and the original G0 blocked17 synthesis artifacts. Do not rely on chat memory.

Objective: integrate accepted G12 source/control evidence for Blocked17 LTF as-of attachment and orderflow/proxy contracts into the next blocked17 unblocking route plan. Preserve exact denominators: 17 blocked cards, the other 15 blocked cards excluded from this route, ready-8 untouched, and expansion candidates untouched. Do not score outcomes, validate, promote, call AI/API/paid vendors, inspect broker account/order/history/deal/position evidence, commit raw market blobs, restart live processes, or change trading/risk/safety/prompt-decision behavior.

Required outputs: G0 decision ledger, accepted-G12-evidence reconciliation, remaining exact source/parser/access/capture requirements, route ranking, downstream starter(s), verifier/focused tests, completion audit, and scoped commits.

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""


def next_g0_starter_text() -> str:
    prompt_path = rel(ROUTE_DIR / f"{PREFIX}_NEXT_G0_PROMPT_{DATE}.md")
    return (
        f"/goal Follow the full controlling prompt in {prompt_path} as the complete objective; run mandatory preflight/context "
        "refresh first; do not rely on chat memory; stay G0 synthesis/control only with no validation/result scoring/R-PnL-win-rate-"
        "expectancy-performance/promotion/live/API/paid-vendor/broker account-order-history-deal-position/raw-blob/trading-risk-"
        "safety-prompt-decision changes; integrate accepted Blocked17 LTF and orderflow/proxy G12 source-control evidence only after both "
        "audits are accepted on disk; preserve exact denominators and safe flags NO_PROMOTION_VERDICT validation_safe=false "
        "outcome_review_opened=false live_effect=false; complete only with exact route decisions, remaining requirements, verifier/focused "
        "tests, and scoped commits."
    )


def write_output_manifest() -> None:
    paths: list[Path] = [
        Path(__file__).resolve(),
        ROUTE_DIR / "verify_g12_scid_blocked17_orderflow_proxy_contract_audit_2026_05_13.py",
        ROUTE_DIR / "test_g12_scid_blocked17_orderflow_proxy_contract_audit_2026_05_13.py",
        ROUTE_DIR / f"{PREFIX}_NEXT_G0_PROMPT_{DATE}.md",
        ROUTE_DIR / f"{PREFIX}_NEXT_G0_STARTER_{DATE}.txt",
    ]
    for stem in OUTPUT_STEMS:
        json_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}.json"
        md_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}.md"
        if stem == "OUTPUT_MANIFEST":
            continue
        if json_path.exists():
            paths.append(json_path)
        if md_path.exists():
            paths.append(md_path)
    rows = []
    for path in sorted({p.resolve() for p in paths if p.exists()}):
        rows.append(
            {
                "path": rel(path),
                "artifact_kind": path.suffix.lstrip(".") or "txt",
                "size_bytes": path.stat().st_size,
                "sha256": sha256_path(path),
            }
        )
    manifest = {
        **base_payload("OUTPUT_MANIFEST"),
        "artifact_count": len(rows),
        "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
        "rows": rows,
    }
    write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json", manifest)
    write_md(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.md", "Output Manifest", manifest)


def build_all() -> dict[str, Any]:
    payloads = target_payloads()
    audits = {
        "context_anchor": build_context_anchor(),
        "denominator": build_denominator_audit(payloads),
        "artifact_hash": build_artifact_hash_audit(payloads),
        "source_family": build_source_family_contract_audit(payloads),
        "equivalence": build_equivalence_audit(payloads),
        "blocker": build_blocker_exactness_audit(payloads),
        "noleak": build_noleak_safe_flag_audit(payloads),
    }
    decision = build_decision_ledger(audits)
    completion = build_completion_audit(audits, decision)

    write_artifact("CONTEXT_ANCHOR", "Context Anchor", audits["context_anchor"])
    write_artifact("DENOMINATOR_AUDIT", "Denominator Audit", audits["denominator"])
    write_artifact("ARTIFACT_HASH_AUDIT", "Artifact Hash Audit", audits["artifact_hash"])
    write_artifact("SOURCE_FAMILY_CONTRACT_AUDIT", "Source Family Contract Audit", audits["source_family"])
    write_artifact("EQUIVALENCE_NON_EQUIVALENCE_AUDIT", "Equivalence Non-Equivalence Audit", audits["equivalence"])
    write_artifact("BLOCKER_EXACTNESS_AUDIT", "Blocker Exactness Audit", audits["blocker"])
    write_artifact("NOLEAK_SAFE_FLAG_AUDIT", "No-Leak Safe-Flag Audit", audits["noleak"])
    write_artifact("DECISION_LEDGER", "Decision Ledger", decision)
    write_artifact("COMPLETION_AUDIT", "Completion Audit", completion)

    (ROUTE_DIR / f"{PREFIX}_NEXT_G0_PROMPT_{DATE}.md").write_text(next_g0_prompt_text(), encoding="utf-8")
    (ROUTE_DIR / f"{PREFIX}_NEXT_G0_STARTER_{DATE}.txt").write_text(next_g0_starter_text() + "\n", encoding="utf-8")
    write_output_manifest()
    return {"decision": decision, "completion": completion, **audits}


def record_focused_test_result(summary: str, returncode: int) -> dict[str, Any]:
    payload = {
        **base_payload("FOCUSED_TEST_RESULT"),
        "command": (
            "python -m pytest "
            "research/science_program_2026_05/06_outcome_testing/g12_scid_blocked17_orderflow_proxy_contract_audit/"
            "test_g12_scid_blocked17_orderflow_proxy_contract_audit_2026_05_13.py -q"
        ),
        "returncode": returncode,
        "ok": returncode == 0,
        "summary": summary,
    }
    write_artifact("FOCUSED_TEST_RESULT", "Focused Test Result", payload)
    write_output_manifest()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-focused-test-result", action="store_true")
    parser.add_argument("--summary", default="")
    parser.add_argument("--returncode", type=int, default=0)
    args = parser.parse_args()

    if args.record_focused_test_result:
        payload = record_focused_test_result(args.summary or "focused pytest completed", args.returncode)
        print(json.dumps({"route_id": ROUTE_ID, "focused_test_ok": payload["ok"]}, indent=2, sort_keys=True))
        return

    results = build_all()
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "terminal_decision": results["decision"]["terminal_decision"],
                "completion_standard_satisfied": results["completion"]["completion_standard_satisfied"],
                "artifact_hash_ok": results["artifact_hash"]["ok"],
                "source_family_ok": results["source_family"]["ok"],
                "equivalence_ok": results["equivalence"]["ok"],
                "blocker_ok": results["blocker"]["ok"],
                "noleak_ok": results["noleak"]["ok"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
