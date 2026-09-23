from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_EXPANSION_AUDIT"
ROUTE_ID = "G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT"
EVIDENCE_CLASS = "G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_ONLY"
TARGET_EVIDENCE_CLASS = "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_ONLY"
TARGET_ROUTE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route"
)
PROMPT_DIR = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"
NEXT_G0_PROMPT = PROMPT_DIR / "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_FROM_G12_AUDIT_GOAL_PROMPT_2026-05-12.md"
NEXT_G0_STARTER = ROUTE_DIR / "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_FROM_G12_AUDIT_STARTER_2026-05-12.txt"

ORIGINAL_8_IDS = {
    "EXP-DENOM-001",
    "EXP-MISS-001",
    "EXP-POI-001",
    "EXP-LTF-001",
    "EXP-PROXY-001",
    "EXP-LIFE-001",
    "EXP-CAL-001",
    "EXP-ADV-001",
}
G0_4_IDS = {
    "G0-EXP-PARTITION-001",
    "G0-EXP-DOMAIN-MISSINGNESS-001",
    "G0-EXP-NEGCTRL-001",
    "G0-EXP-ROWSET-001",
}
EXPECTED_R4_COUNT = 12
EXPECTED_TOTAL = 24
EXPECTED_SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_trading_risk_safety_prompt_decision_behavior",
]
RESULT_LABEL_KEYS = {
    "result_label",
    "outcome_label",
    "target_hit",
    "stop_hit",
    "realized_r",
    "pnl",
    "win_rate",
    "expectancy",
    "performance",
    "broker_account_history",
    "broker_order_ticket",
    "deal_id",
    "position_id",
    "post_decision_path_label",
    "future_target_window_observation",
}


TARGET_FILES = {
    "target_inventory": "SCID_EXPANSION_CANDIDATE_INVENTORY_2026-05-12.json",
    "target_source_matrix": "SCID_EXPANSION_SOURCE_FIELD_DESIGN_MATRIX_2026-05-12.json",
    "target_criteria": "SCID_EXPANSION_ACCEPTANCE_REJECTION_CRITERIA_2026-05-12.json",
    "target_quarantine": "SCID_EXPANSION_DENOMINATOR_QUARANTINE_PROOF_2026-05-12.json",
    "target_ranking": "SCID_EXPANSION_ROUTE_RANKING_MATRIX_2026-05-12.json",
    "target_negative": "SCID_EXPANSION_NEGATIVE_EVIDENCE_AND_BOXING_AUDIT_2026-05-12.json",
    "target_saturation": "SCID_EXPANSION_SATURATION_SELF_RED_TEAM_2026-05-12.md",
    "target_completion": "SCID_EXPANSION_COMPLETION_AUDIT_2026-05-12.json",
    "target_manifest": "SCID_EXPANSION_OUTPUT_MANIFEST_2026-05-12.json",
    "target_verification": "SCID_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
    "target_builder": "build_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
    "target_verifier": "verify_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
    "target_tests": "test_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
}

UPSTREAM_FILES = {
    "accepted_source_mapping": (
        "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/"
        "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SOURCE_FIELD_MAPPING_MATRIX_2026-05-12.json"
    ),
    "accepted_terminal_status": (
        "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/"
        "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_PER_CARD_TERMINAL_STATUS_LEDGER_2026-05-12.json"
    ),
    "g0_expansion_ledger": (
        "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/"
        "G0_SCID_NOAPI_PREREG_SYNTHESIS_EXPANSION_CANDIDATE_LEDGER_2026-05-12.json"
    ),
    "g12_noapi_expansion_quarantine": (
        "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/"
        "G12_SCID_NOAPI_PREREG_AUDIT_EXPANSION_CANDIDATE_QUARANTINE_AUDIT_2026-05-12.json"
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_pair(stem: str, payload: dict[str, Any]) -> None:
    json_path = artifact_path(stem)
    md_path = artifact_path(stem, ".md")
    write_json(json_path, payload)
    md_path.write_text(
        f"# {stem.replace('_', ' ').title()}\n\n```json\n"
        + json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
        + "\n```\n",
        encoding="utf-8",
    )


def base_payload(artifact_family: str) -> dict[str, Any]:
    payload = {
        "schema_version": "g12_scid_expansion_audit_v1",
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    payload.update({flag: False for flag in EXPECTED_SAFE_FALSE_FLAGS})
    return payload


def load_target_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    target: dict[str, Any] = {}
    hashes: dict[str, Any] = {}
    for key, name in TARGET_FILES.items():
        path = TARGET_ROUTE_DIR / name
        hashes[key] = {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
            "bytes": path.stat().st_size if path.exists() else None,
        }
        if path.suffix == ".json" and path.exists():
            target[key] = read_json(path)
        elif path.exists():
            target[key] = path.read_text(encoding="utf-8")
    for key, relative in UPSTREAM_FILES.items():
        path = REPO_ROOT / relative
        hashes[key] = {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
            "bytes": path.stat().st_size if path.exists() else None,
        }
        if path.exists():
            target[key] = read_json(path)
    return target, hashes


def recursive_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, subvalue in value.items():
            found.add(str(key))
            found.update(recursive_keys(subvalue))
    elif isinstance(value, list):
        for item in value:
            found.update(recursive_keys(item))
    return found


def has_phrase(value: Any, phrase: str) -> bool:
    return phrase.lower() in json.dumps(value, sort_keys=True).lower()


def build_context_artifact(target: dict[str, Any], hashes: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("context_and_target_input_inventory")
    required_context = [
        ".context/LIVE_STATE.md",
        ".context/00_core/goal_session_research_discipline.md",
        ".context/00_core/research_operating_doctrine.md",
        ".context/00_core/research_current_state.md",
        ".context/00_core/local_heavy_data_inventory.md",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_R4_EXPANSION_DESIGN_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_GOAL_PROMPT_2026-05-12.md",
    ]
    context_files = []
    for relative in required_context:
        path = REPO_ROOT / relative
        context_files.append(
            {
                "path": relative,
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else None,
            }
        )
    payload.update(
        {
            "audit_lane": "G12 fair-adversarial acceptance audit",
            "target_route_dir": rel(TARGET_ROUTE_DIR),
            "required_context_files": context_files,
            "target_and_upstream_artifact_hashes": hashes,
            "all_required_inputs_disk_backed": all(row["exists"] for row in context_files)
            and all(row["exists"] for row in hashes.values()),
            "parseable_json_target_inputs": sorted(k for k, v in target.items() if isinstance(v, dict)),
        }
    )
    payload["ok"] = payload["all_required_inputs_disk_backed"] is True
    return payload


def build_candidate_count_audit(target: dict[str, Any]) -> dict[str, Any]:
    inventory = target["target_inventory"]
    rows = inventory["rows"]
    ids = [row["candidate_id"] for row in rows]
    origin_counts = Counter(row.get("candidate_origin") for row in rows)
    r4_ids = sorted(
        row["candidate_id"]
        for row in rows
        if row.get("candidate_origin") == "r4_artifact_search_discovered_additional_family"
    )
    payload = base_payload("candidate_count_audit")
    payload.update(
        {
            "candidate_count_recomputed": len(rows),
            "unique_candidate_count_recomputed": len(set(ids)),
            "candidate_origin_counts_recomputed": dict(sorted(origin_counts.items())),
            "preserved_original_8_ids_expected": sorted(ORIGINAL_8_IDS),
            "preserved_original_8_ids_present": sorted(set(ids) & ORIGINAL_8_IDS),
            "preserved_g0_4_ids_expected": sorted(G0_4_IDS),
            "preserved_g0_4_ids_present": sorted(set(ids) & G0_4_IDS),
            "r4_discovered_12_ids_present": r4_ids,
            "target_inventory_declared_counts": {
                "preserved_original_8_count": inventory.get("preserved_original_8_count"),
                "preserved_g0_discovered_4_count": inventory.get("preserved_g0_discovered_4_count"),
                "r4_discovered_additional_count": inventory.get("r4_discovered_additional_count"),
                "candidate_count": inventory.get("candidate_count"),
            },
            "all_candidates_denominator_inclusion_false": all(
                row.get("accepted_40_card_denominator_inclusion") is False for row in rows
            ),
            "duplicate_candidate_ids": sorted([candidate_id for candidate_id, count in Counter(ids).items() if count > 1]),
            "accepted_40_is_floor_not_ceiling": inventory.get("accepted_40_is_floor_not_ceiling") is True,
        }
    )
    payload["ok"] = (
        payload["candidate_count_recomputed"] == EXPECTED_TOTAL
        and payload["unique_candidate_count_recomputed"] == EXPECTED_TOTAL
        and set(payload["preserved_original_8_ids_present"]) == ORIGINAL_8_IDS
        and set(payload["preserved_g0_4_ids_present"]) == G0_4_IDS
        and len(r4_ids) == EXPECTED_R4_COUNT
        and payload["all_candidates_denominator_inclusion_false"] is True
        and payload["accepted_40_is_floor_not_ceiling"] is True
    )
    return payload


def build_source_field_design_audit(target: dict[str, Any]) -> dict[str, Any]:
    inventory_ids = {row["candidate_id"] for row in target["target_inventory"]["rows"]}
    matrix_rows = target["target_source_matrix"]["rows"]
    criteria_rows = target["target_criteria"]["rows"]
    matrix_ids = {row["candidate_id"] for row in matrix_rows}
    criteria_ids = {row["candidate_id"] for row in criteria_rows}
    matrix_missing = []
    for row in matrix_rows:
        missing = [
            field
            for field in [
                "source_fields_or_groups",
                "as_of_rules",
                "duplicate_policy",
                "forbidden_fields",
                "no_leak_requirements",
                "future_g12_g0_acceptance_gates",
            ]
            if not row.get(field)
        ]
        if missing:
            matrix_missing.append({"candidate_id": row.get("candidate_id"), "missing_fields": missing})
    weak_criteria = []
    novelty_guard_rows = 0
    for row in criteria_rows:
        rejection_text = json.dumps(row.get("rejection_criteria", []))
        if row.get("novelty_alone_is_rejection_reason") is False and "Do not reject merely because" in rejection_text:
            novelty_guard_rows += 1
        if len(row.get("acceptance_criteria", [])) < 4 or len(row.get("rejection_criteria", [])) < 4:
            weak_criteria.append(row.get("candidate_id"))
    payload = base_payload("source_field_design_audit")
    payload.update(
        {
            "inventory_candidate_count": len(inventory_ids),
            "source_matrix_row_count": len(matrix_rows),
            "criteria_row_count": len(criteria_rows),
            "matrix_covers_inventory_exactly": matrix_ids == inventory_ids,
            "criteria_covers_inventory_exactly": criteria_ids == inventory_ids,
            "matrix_missing_required_controls": matrix_missing,
            "weak_criteria_candidate_ids": weak_criteria,
            "novelty_guard_row_count": novelty_guard_rows,
            "novelty_guard_covers_all_candidates": novelty_guard_rows == len(inventory_ids),
            "criteria_novelty_global_guard": target["target_criteria"].get("novelty_alone_is_never_rejection_reason")
            is True,
            "criteria_rejection_requires_evidence": target["target_criteria"].get("rejection_requires_evidence") is True,
        }
    )
    payload["ok"] = (
        payload["matrix_covers_inventory_exactly"]
        and payload["criteria_covers_inventory_exactly"]
        and not matrix_missing
        and not weak_criteria
        and payload["novelty_guard_covers_all_candidates"]
        and payload["criteria_novelty_global_guard"]
        and payload["criteria_rejection_requires_evidence"]
    )
    return payload


def build_denominator_quarantine_audit(target: dict[str, Any]) -> dict[str, Any]:
    inventory_rows = target["target_inventory"]["rows"]
    candidate_ids = {row["candidate_id"] for row in inventory_rows}
    accepted_mapping_rows = target["accepted_source_mapping"]["rows"]
    accepted_terminal_rows = target["accepted_terminal_status"]["rows"]
    accepted_ids = {row["card_id"] for row in accepted_mapping_rows}
    terminal_ids = {row["card_id"] for row in accepted_terminal_rows}
    domain_counts = Counter(row.get("science_domain") for row in accepted_mapping_rows)
    readiness_split = Counter(row.get("accepted_readiness") for row in accepted_mapping_rows)
    result_label_key_hits = []
    for row in inventory_rows:
        hits = sorted(recursive_keys(row) & RESULT_LABEL_KEYS)
        if hits:
            result_label_key_hits.append({"candidate_id": row["candidate_id"], "keys": hits})
    safe_flag_failures = []
    for name in [
        "target_inventory",
        "target_source_matrix",
        "target_criteria",
        "target_quarantine",
        "target_ranking",
        "target_negative",
        "target_completion",
        "target_manifest",
        "target_verification",
    ]:
        artifact = target[name]
        for flag in EXPECTED_SAFE_FALSE_FLAGS:
            if flag in artifact and artifact.get(flag) is not False:
                safe_flag_failures.append({"artifact": name, "flag": flag, "value": artifact.get(flag)})
        if artifact.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            safe_flag_failures.append(
                {"artifact": name, "flag": "promotion_verdict", "value": artifact.get("promotion_verdict")}
            )
    payload = base_payload("denominator_quarantine_audit")
    payload.update(
        {
            "accepted_40_count_recomputed_from_source_mapping": len(accepted_ids),
            "accepted_40_count_recomputed_from_terminal_status": len(terminal_ids),
            "accepted_mapping_and_terminal_card_ids_match": accepted_ids == terminal_ids,
            "accepted_domain_count_recomputed": len(domain_counts),
            "accepted_domain_counts_recomputed": dict(sorted(domain_counts.items())),
            "accepted_readiness_split_recomputed": dict(sorted(readiness_split.items())),
            "candidate_overlap_with_accepted_40_card_ids": sorted(candidate_ids & accepted_ids),
            "candidate_overlap_count": len(candidate_ids & accepted_ids),
            "target_quarantine_declared_candidate_overlap_count": target["target_quarantine"].get(
                "candidate_overlap_count"
            ),
            "target_quarantine_declared_denominator_count": target["target_quarantine"].get(
                "accepted_40_card_denominator_count"
            ),
            "all_candidates_denominator_inclusion_false": all(
                row.get("accepted_40_card_denominator_inclusion") is False for row in inventory_rows
            ),
            "candidate_result_label_key_hits": result_label_key_hits,
            "safe_flag_failures": safe_flag_failures,
            "no_candidate_inherits_result_labels_or_accepted_status": not result_label_key_hits
            and all(row.get("accepted_40_card_denominator_inclusion") is False for row in inventory_rows),
        }
    )
    payload["ok"] = (
        payload["accepted_40_count_recomputed_from_source_mapping"] == 40
        and payload["accepted_40_count_recomputed_from_terminal_status"] == 40
        and payload["accepted_mapping_and_terminal_card_ids_match"]
        and payload["accepted_domain_count_recomputed"] == 8
        and set(payload["accepted_domain_counts_recomputed"].values()) == {5}
        and payload["candidate_overlap_count"] == 0
        and payload["target_quarantine_declared_candidate_overlap_count"] == 0
        and payload["target_quarantine_declared_denominator_count"] == 40
        and payload["all_candidates_denominator_inclusion_false"]
        and not result_label_key_hits
        and not safe_flag_failures
    )
    return payload


def build_novelty_anti_boxing_audit(target: dict[str, Any]) -> dict[str, Any]:
    inventory_rows = target["target_inventory"]["rows"]
    candidate_ids = {row["candidate_id"] for row in inventory_rows}
    negative = target["target_negative"]
    search = negative.get("searched_artifacts_proof", {})
    source_summary = search.get("source_inventory_summary", {})
    category_counts = source_summary.get("source_category_counts", {})
    required_r4_families = {
        "R4-EXP-ROOT-001",
        "R4-EXP-PARSER-001",
        "R4-EXP-CAPGROUP-001",
        "R4-EXP-CLOCK-001",
        "R4-EXP-ALIAS-001",
        "R4-EXP-BASIS-001",
        "R4-EXP-NEG-001",
        "R4-EXP-MLDATA-001",
        "R4-EXP-COSTSRC-001",
        "R4-EXP-NEWSMACRO-001",
        "R4-EXP-PLACEBO-001",
        "R4-EXP-CODEHIST-001",
    }
    anti_boxing_checks = {
        "non_ob_framing_preserved": has_phrase(target["target_criteria"], "non-OB")
        and has_phrase(target["target_criteria"], "outside current GTOS"),
        "current_symbol_or_proxy_expansion_preserved": bool(
            {"R4-EXP-ALIAS-001", "R4-EXP-BASIS-001", "R4-EXP-COSTSRC-001"} & candidate_ids
        ),
        "local_heavy_data_roots_preserved": len(search.get("local_heavy_roots_checked", [])) >= 5,
        "source_gaps_preserved_as_route_families": "R4-EXP-NEG-001" in candidate_ids
        and has_phrase(negative, "source gaps"),
        "negative_evidence_failure_anatomy_lane_preserved": len(negative.get("negative_evidence_rows", [])) >= 4
        and has_phrase(negative, "negative"),
        "new_science_doors_preserved": len(required_r4_families & candidate_ids) == EXPECTED_R4_COUNT
        and source_summary.get("source_inventory_count", 0) >= 1,
        "accepted_40_floor_not_ceiling": "floor" in negative.get("anti_boxing_conclusion", "").lower(),
        "sierra_proxy_source_ledgers_present": any("SIERRA" in key for key in category_counts)
        and any("PROXY" in key for key in category_counts),
    }
    payload = base_payload("novelty_anti_boxing_audit")
    payload.update(
        {
            "anti_boxing_checks": anti_boxing_checks,
            "r4_required_family_ids_present": sorted(required_r4_families & candidate_ids),
            "r4_required_family_ids_missing": sorted(required_r4_families - candidate_ids),
            "source_inventory_count": source_summary.get("source_inventory_count"),
            "source_category_counts": category_counts,
            "anti_boxing_conclusion": negative.get("anti_boxing_conclusion"),
            "fair_adversarial_note": "The audit rejects count drift and leakage but does not reject novelty, non-OB framing, or outside-current-GTOS candidates merely for breadth.",
        }
    )
    payload["ok"] = all(anti_boxing_checks.values()) and not payload["r4_required_family_ids_missing"]
    return payload


def build_source_search_audit(target: dict[str, Any]) -> dict[str, Any]:
    search = target["target_negative"].get("searched_artifacts_proof", {})
    scopes = search.get("artifact_search_scopes", [])
    roots = search.get("local_heavy_roots_checked", [])
    source_summary = search.get("source_inventory_summary", {})
    all_scope_paths = [scope.get("path", "") for scope in scopes]
    all_roots = [root.get("root", "") for root in roots]
    category_counts = source_summary.get("source_category_counts", {})
    payload = base_payload("source_search_audit")
    payload.update(
        {
            "artifact_search_scope_count": len(scopes),
            "local_heavy_root_count": len(roots),
            "source_inventory_count": source_summary.get("source_inventory_count"),
            "hash_status_counts": source_summary.get("hash_status_counts", {}),
            "source_category_counts": category_counts,
            "checks": {
                "current_worktree_artifacts_searched": any(path.startswith("research/") for path in all_scope_paths),
                "accepted_artifacts_searched": any("scid_noapi_40card_prereg_input_design" in path for path in all_scope_paths),
                "absolute_local_heavy_roots_checked": any(path.startswith("C:\\Users\\MSI") for path in all_roots),
                "sierra_roots_checked": any("SierraChart" in path for path in all_roots)
                and any("SIERRA" in key for key in category_counts),
                "proxy_source_ledgers_checked": any("PROXY" in key for key in category_counts),
                "prior_worktrees_checked": any(path.startswith("C:\\tmp\\gtos_otb") for path in all_roots),
                "explicit_no_raw_blob_policy": source_summary.get("raw_market_blob_commits_added") == 0
                and all("no raw market blob" in root.get("policy", "").lower() for root in roots),
                "broker_account_order_history_not_consumed": source_summary.get("forbidden_broker_sources_consumed") == 0,
            },
            "roots_checked": roots,
            "artifact_scopes": [
                {
                    "scope_id": scope.get("scope_id"),
                    "path": scope.get("path"),
                    "exists": scope.get("exists"),
                    "files_seen": scope.get("files_seen"),
                    "keyword_file_match_counts": scope.get("keyword_file_match_counts", {}),
                }
                for scope in scopes
            ],
        }
    )
    payload["ok"] = all(payload["checks"].values()) and payload["artifact_search_scope_count"] >= 6
    return payload


def build_negative_evidence_audit(target: dict[str, Any]) -> dict[str, Any]:
    negative = target["target_negative"]
    rows = negative.get("negative_evidence_rows", [])
    statuses = Counter(row.get("status") for row in rows)
    payload = base_payload("negative_evidence_audit")
    payload.update(
        {
            "negative_evidence_row_count": len(rows),
            "status_counts": dict(sorted(statuses.items())),
            "rows": rows,
            "contains_denominator_mixing_check": any(row.get("audit_area") == "denominator_mixing" for row in rows),
            "contains_ob_only_collapse_check": any(row.get("audit_area") == "ob_only_collapse" for row in rows),
            "contains_source_gap_or_passive_waiting_check": any(
                row.get("audit_area") in {"passive_waiting", "source_gap_exactness"} for row in rows
            ),
            "contains_forbidden_surface_check": any(
                row.get("audit_area") in {"forbidden_surface", "forbidden_surfaces"} for row in rows
            ),
            "audit_interpretation": "Negative evidence is control/design evidence only. It preserves failure-anatomy/source-gap lanes without opening outcome review.",
        }
    )
    payload["ok"] = (
        payload["negative_evidence_row_count"] >= 6
        and statuses.get("PASS", 0) == payload["negative_evidence_row_count"]
        and payload["contains_denominator_mixing_check"]
        and payload["contains_ob_only_collapse_check"]
        and payload["contains_source_gap_or_passive_waiting_check"]
        and payload["contains_forbidden_surface_check"]
    )
    return payload


def build_blocker_followup_ledger(target: dict[str, Any]) -> dict[str, Any]:
    target_verification = target["target_verification"]
    prompt_packs = target["target_ranking"].get("prompt_packs", [])
    prompt_pack_status = []
    for pack in prompt_packs:
        prompt_path = REPO_ROOT / pack.get("prompt_path", "")
        starter_path = REPO_ROOT / pack.get("starter_path", "")
        prompt_pack_status.append(
            {
                "evidence_class": pack.get("evidence_class"),
                "prompt_path": pack.get("prompt_path"),
                "prompt_exists": prompt_path.exists(),
                "starter_path": pack.get("starter_path"),
                "starter_exists": starter_path.exists(),
                "starter_one_physical_line": pack.get("starter_one_physical_line") is True,
            }
        )
    payload = base_payload("blocker_followup_ledger")
    payload.update(
        {
            "terminal_blockers": [],
            "exact_nonblocking_followups": [
                {
                    "followup_id": "NEXT-G0-001",
                    "status": "READY_AFTER_G12_ACCEPTANCE",
                    "description": "Run G0 denominator-entry/source-materialization synthesis before any candidate can enter a future denominator.",
                    "prompt_path": rel(NEXT_G0_PROMPT),
                    "starter_path": rel(NEXT_G0_STARTER),
                },
                {
                    "followup_id": "SOURCE-PACKET-001",
                    "status": "AVAILABLE_FROM_R4_ROUTE_AFTER_G12_ACCEPTANCE",
                    "description": "Top-route source-field acceptance packet remains a separate source/control builder; it must not score outcomes.",
                    "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_EXPANSION_TOP_ROUTE_SOURCE_FIELD_ACCEPTANCE_PACKET_GOAL_PROMPT_2026-05-12.md",
                    "starter_path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_TOP_ROUTE_SOURCE_FIELD_ACCEPTANCE_PACKET_STARTER_2026-05-12.txt",
                },
            ],
            "target_verifier_ok": target_verification.get("ok") is True
            and target_verification.get("failure_count") == 0
            and target_verification.get("focused_tests_marked_ok") is True,
            "target_prompt_pack_status": prompt_pack_status,
            "remaining_blockers_cross_evidence_class_only": [
                "No validation/result/performance scoring is opened here; source packets and denominator-entry synthesis are separate future routes.",
                "No expansion candidate is admitted to accepted-card denominators until a future G0/G12 chain accepts source fields and duplicate policy.",
            ],
        }
    )
    payload["ok"] = (
        not payload["terminal_blockers"]
        and payload["target_verifier_ok"]
        and all(row["prompt_exists"] and row["starter_exists"] and row["starter_one_physical_line"] for row in prompt_pack_status)
    )
    return payload


def build_decision_ledger(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload = base_payload("decision_ledger")
    blocking_failures = sorted(stem for stem, audit in audits.items() if audit.get("ok") is not True)
    terminal = (
        "ACCEPT_AS_G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_CONTROL_EVIDENCE_ONLY"
        if not blocking_failures
        else "REJECT_PENDING_REPAIR"
    )
    payload.update(
        {
            "terminal_decision": terminal,
            "accepted_g12_control_evidence_only": terminal.startswith("ACCEPT"),
            "accepted_validation_execution": False,
            "accepted_strategy_performance": False,
            "accepted_promotion": False,
            "terminal_blockers": blocking_failures,
            "acceptance_scope": "Source/control design acceptance for quarantined expansion candidates only.",
            "accepted_counts": {
                "original_8": audits["CANDIDATE_COUNT_AUDIT"]["candidate_origin_counts_recomputed"].get(
                    "preserved_original_8_from_target_input_design"
                ),
                "g0_4": audits["CANDIDATE_COUNT_AUDIT"]["candidate_origin_counts_recomputed"].get(
                    "preserved_g0_discovered_4_from_g0_synthesis"
                ),
                "r4_12": audits["CANDIDATE_COUNT_AUDIT"]["candidate_origin_counts_recomputed"].get(
                    "r4_artifact_search_discovered_additional_family"
                ),
                "total": audits["CANDIDATE_COUNT_AUDIT"]["candidate_count_recomputed"],
                "accepted_40_overlap": audits["DENOMINATOR_QUARANTINE_AUDIT"]["candidate_overlap_count"],
            },
            "fairness_clause": "The route is not rejected for novelty, non-OB framing, current-symbol/source expansion, or being outside current GTOS logic; it is accepted because it keeps denominator and source boundaries explicit.",
        }
    )
    payload["ok"] = terminal.startswith("ACCEPT")
    return payload


def build_completion_audit(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("Mandatory preflight and context files read", "CONTEXT_AND_TARGET_INPUT_INVENTORY"),
        ("Target R4 route artifacts read from disk", "CONTEXT_AND_TARGET_INPUT_INVENTORY"),
        ("Recompute original 8, G0 4, R4 12, total 24", "CANDIDATE_COUNT_AUDIT"),
        ("Verify accepted 40 denominator overlap is zero", "DENOMINATOR_QUARANTINE_AUDIT"),
        ("Verify every candidate stays denominator_inclusion=false", "DENOMINATOR_QUARANTINE_AUDIT"),
        ("Verify no result labels or accepted-card status inherited", "DENOMINATOR_QUARANTINE_AUDIT"),
        ("Verify source-field designs and criteria cover all candidates", "SOURCE_FIELD_DESIGN_AUDIT"),
        ("Verify route ranking and next prompt packs are disk-backed", "BLOCKER_FOLLOWUP_LEDGER"),
        ("Verify novelty and anti-boxing preservation", "NOVELTY_ANTI_BOXING_AUDIT"),
        ("Verify searched roots and no-raw-blob policy", "SOURCE_SEARCH_AUDIT"),
        ("Verify negative evidence/failure-anatomy lanes", "NEGATIVE_EVIDENCE_AUDIT"),
        ("Emit blocker/follow-up ledger", "BLOCKER_FOLLOWUP_LEDGER"),
        ("Emit G12 decision ledger", "DECISION_LEDGER"),
        ("Emit next G0/source-packet prompt only after acceptance", "BLOCKER_FOLLOWUP_LEDGER"),
        ("G12 standalone verifier passed", None),
        ("G12 focused tests passed", None),
        ("Scoped commits complete", None),
    ]
    rows = []
    for requirement, artifact in checklist:
        if artifact == "DECISION_LEDGER":
            satisfied = decision.get("ok") is True
            evidence = rel(artifact_path(artifact))
        elif artifact:
            satisfied = audits[artifact].get("ok") is True
            evidence = rel(artifact_path(artifact))
        else:
            satisfied = False
            evidence = "filled by verifier/focused tests/final commit"
        rows.append({"requirement": requirement, "satisfied": satisfied, "evidence": evidence})
    payload = base_payload("completion_audit")
    payload.update(
        {
            "objective_as_concrete_success_criteria": [
                "Audit only the R4 expansion candidate acceptance/design route.",
                "Recompute exact 8 original plus 4 G0 plus 12 R4 candidate counts.",
                "Prove accepted-40 denominator boundaries remain unchanged with zero overlap.",
                "Accept or reject source/control design only; do not open result or validation evidence.",
                "Emit G12 artifacts, verifier, focused tests, and next prompt only if accepted.",
            ],
            "terminal_decision": decision["terminal_decision"],
            "prompt_to_artifact_checklist": rows,
            "completion_standard_satisfied_before_verifier_tests_commit": False,
            "can_mark_goal_complete": False,
        }
    )
    return payload


def build_output_manifest(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("output_manifest")
    required = [
        "CONTEXT_AND_TARGET_INPUT_INVENTORY",
        "CANDIDATE_COUNT_AUDIT",
        "SOURCE_FIELD_DESIGN_AUDIT",
        "DENOMINATOR_QUARANTINE_AUDIT",
        "NOVELTY_ANTI_BOXING_AUDIT",
        "SOURCE_SEARCH_AUDIT",
        "NEGATIVE_EVIDENCE_AUDIT",
        "BLOCKER_FOLLOWUP_LEDGER",
        "DECISION_LEDGER",
        "COMPLETION_AUDIT",
        "OUTPUT_MANIFEST",
    ]
    payload.update(
        {
            "required_artifact_families": required,
            "all_required_artifact_families_covered": True,
            "decision": decision["terminal_decision"],
            "next_prompt_pack": {
                "prompt_path": rel(NEXT_G0_PROMPT),
                "starter_path": rel(NEXT_G0_STARTER),
                "emitted_only_because_decision_accepts": decision["terminal_decision"].startswith("ACCEPT"),
            },
            "artifacts": [],
            "manifest_self_hash_policy": "Manifest hash is refreshed by verifier and is not a blocking self-hash.",
        }
    )
    return payload


def write_next_prompt(decision: dict[str, Any]) -> None:
    if not decision["terminal_decision"].startswith("ACCEPT"):
        return
    prompt = f"""# G0 SCID Expansion Denominator-Entry Synthesis From G12 Audit

Evidence class: `G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_ONLY`

Run only after `research/science_program_2026_05/06_outcome_testing/g12_scid_expansion_candidate_acceptance_design_audit/` accepts the R4 expansion design. This is a G0 route-selection/source-materialization synthesis, not a scoring route.

## Mandatory Context

Run `python scripts/generate_live_state.py`; read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, the accepted R4 expansion artifacts, and the G12 expansion audit decision ledger. Do not rely on chat memory.

## Accepted Audit Facts

- Original quarantined candidates: 8.
- G0-discovered candidates: 4.
- R4-discovered additional families: 12.
- Total quarantined expansion candidates: 24.
- Accepted-40 denominator overlap: 0.
- Every expansion candidate has `accepted_40_card_denominator_inclusion=false`.
- The accepted 40 remains a floor, not a ceiling.

## Objective

Synthesize which quarantined expansion families should receive future denominator-entry or source-field materialization routes. Consider all 24 families, not only the top-ranked six. Preserve non-OB, current-symbol/source expansion, local-heavy-data roots, source-gap, negative-evidence, placebo/control, code-lineage, parser/hash, proxy/basis, clock/as-of, cost-source, macro/news, and ML/source-readiness routes as real future research doors when source-control criteria support them.

## Required Outputs

- G0 decision ledger.
- Accepted/rejected/deferred route-family ledger for all 24 candidates.
- Ranked denominator-entry/source-materialization route plan.
- Exact prompt packs/starters for accepted next source-control routes only.
- Denominator quarantine proof showing no candidate entered the accepted 40 in this synthesis.
- Saturation/self-red-team ledger showing the synthesis did not collapse back to current OB-only logic.
- Verifier, focused tests, completion audit, and scoped commits.

## Hard Boundaries

No validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    NEXT_G0_PROMPT.write_text(prompt, encoding="utf-8")
    starter = (
        "/goal Follow the full controlling prompt in "
        f"{rel(NEXT_G0_PROMPT)} as the complete objective; run mandatory preflight/context refresh; "
        "do not rely on chat memory; stay G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_ONLY with no "
        "validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/"
        "broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/"
        "trading-risk-safety-prompt-decision changes; preserve accepted 40 denominator boundaries and all "
        "24 quarantined expansion candidates; pursue proof-or-impossibility inside this evidence class; "
        "require exact route-family ledger, ranked source-materialization plan, verifier/focused checks, "
        "scoped commits, NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; "
        "mark complete only when the prompt completion standard is fully satisfied."
    )
    NEXT_G0_STARTER.write_text(starter + "\n", encoding="utf-8")


def refresh_manifest_hashes() -> None:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest = read_json(manifest_path)
    artifact_paths = []
    for path in ROUTE_DIR.iterdir():
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".py", ".txt"}:
            artifact_paths.append(path)
    if NEXT_G0_PROMPT.exists():
        artifact_paths.append(NEXT_G0_PROMPT)
    artifacts = []
    for path in sorted(set(artifact_paths)):
        artifacts.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "raw_market_blob": path.suffix.lower() in {".scid", ".depth", ".parquet", ".zip", ".bin"},
            }
        )
    manifest["artifacts"] = artifacts
    manifest["artifact_count"] = len(artifacts)
    write_json(manifest_path, manifest)
    artifact_path("OUTPUT_MANIFEST", ".md").write_text(
        "# Output Manifest\n\n```json\n"
        + json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True)
        + "\n```\n",
        encoding="utf-8",
    )


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    target, hashes = load_target_artifacts()
    audits: dict[str, dict[str, Any]] = {
        "CONTEXT_AND_TARGET_INPUT_INVENTORY": build_context_artifact(target, hashes),
        "CANDIDATE_COUNT_AUDIT": build_candidate_count_audit(target),
        "SOURCE_FIELD_DESIGN_AUDIT": build_source_field_design_audit(target),
        "DENOMINATOR_QUARANTINE_AUDIT": build_denominator_quarantine_audit(target),
        "NOVELTY_ANTI_BOXING_AUDIT": build_novelty_anti_boxing_audit(target),
        "SOURCE_SEARCH_AUDIT": build_source_search_audit(target),
        "NEGATIVE_EVIDENCE_AUDIT": build_negative_evidence_audit(target),
        "BLOCKER_FOLLOWUP_LEDGER": build_blocker_followup_ledger(target),
    }
    decision = build_decision_ledger(audits)
    write_next_prompt(decision)
    completion = build_completion_audit(audits, decision)
    manifest = build_output_manifest(audits, decision)

    for stem, payload in audits.items():
        write_pair(stem, payload)
    write_pair("DECISION_LEDGER", decision)
    write_pair("COMPLETION_AUDIT", completion)
    write_pair("OUTPUT_MANIFEST", manifest)
    refresh_manifest_hashes()

    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "terminal_decision": decision["terminal_decision"],
                "candidate_count": audits["CANDIDATE_COUNT_AUDIT"]["candidate_count_recomputed"],
                "candidate_overlap_count": audits["DENOMINATOR_QUARANTINE_AUDIT"]["candidate_overlap_count"],
                "all_audits_ok": all(audit.get("ok") is True for audit in audits.values()) and decision.get("ok") is True,
                "next_prompt": rel(NEXT_G0_PROMPT) if NEXT_G0_PROMPT.exists() else None,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
