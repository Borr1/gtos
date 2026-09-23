from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import (  # noqa: E402
    SCID_CAPTURE_GROUPS,
    SCID_GROUP_FIELDS,
    validate_scid_forward_source_capture_row,
)


DATE = "2026-05-12"
PREFIX = "G12_SCID_FC_BLOCKED15_AUDIT"
ROUTE_ID = "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT"
EVIDENCE_CLASS = "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY"
TARGET_ROUTE_ID = "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15"
TARGET_EVIDENCE_CLASS = "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY"
TERMINAL_REPAIR = "REPAIR_REQUIRED_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION"

OUTCOME_ROOT = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing"
PROMPT_ROOT = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"
TARGET_DIR = OUTCOME_ROOT / "scid_future_capture_field_source_state_materialization_for_blocked15"
G0_SYNTHESIS_DIR = OUTCOME_ROOT / "g0_scid_noapi_40card_prereg_replay_input_design_synthesis"

BLOCKED_LEDGER = G0_SYNTHESIS_DIR / f"G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_{DATE}.json"
TARGET_PROMPT = PROMPT_ROOT / f"G0NAPI_R3_FUTURE_CAPTURE_SOURCE_GOAL_PROMPT_{DATE}.md"
CONTROL_PROMPT = PROMPT_ROOT / f"G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT_GOAL_PROMPT_{DATE}.md"
NEXT_G0_PROMPT = PROMPT_ROOT / f"G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_AFTER_FC_G12_AUDIT_GOAL_PROMPT_{DATE}.md"
NEXT_G0_STARTER = ROUTE_DIR / f"NEXT_G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_STARTER_{DATE}.txt"

TARGET_ARTIFACTS = {
    "card_set": TARGET_DIR / f"SCID_FUTURE_CAPTURE_BLOCKED15_CARD_SET_{DATE}.json",
    "matrix": TARGET_DIR / f"SCID_FUTURE_CAPTURE_FIELD_TO_SOURCE_STATE_MATRIX_{DATE}.json",
    "search_ledger": TARGET_DIR / f"SCID_FUTURE_CAPTURE_HISTORICAL_RECOVERY_SEARCH_LEDGER_{DATE}.json",
    "recovered_rows": TARGET_DIR / f"SCID_FUTURE_CAPTURE_RECOVERED_SOURCE_STATE_ROWS_{DATE}.jsonl",
    "prospective_contract": TARGET_DIR / f"SCID_FUTURE_CAPTURE_PROSPECTIVE_CONTRACT_{DATE}.json",
    "unblocking": TARGET_DIR / f"SCID_FUTURE_CAPTURE_UNBLOCKING_CRITERIA_BY_CARD_{DATE}.json",
    "expansion": TARGET_DIR / f"SCID_FUTURE_CAPTURE_QUARANTINED_EXPANSION_OBSERVATIONS_{DATE}.json",
    "noleak": TARGET_DIR / f"SCID_FUTURE_CAPTURE_NO_LEAK_REDACTION_FAILCLOSED_AUDIT_{DATE}.json",
    "saturation": TARGET_DIR / f"SCID_FUTURE_CAPTURE_SATURATION_SELF_RED_TEAM_{DATE}.md",
    "completion": TARGET_DIR / f"SCID_FUTURE_CAPTURE_COMPLETION_AUDIT_{DATE}.json",
    "verification": TARGET_DIR / f"SCID_FUTURE_CAPTURE_VERIFICATION_RESULT_{DATE}.json",
    "manifest": TARGET_DIR / f"SCID_FUTURE_CAPTURE_OUTPUT_MANIFEST_{DATE}.json",
    "builder": TARGET_DIR / "build_scid_future_capture_blocked15_materialization_2026_05_12.py",
    "verifier": TARGET_DIR / "verify_scid_future_capture_blocked15_materialization_2026_05_12.py",
    "focused_tests": TARGET_DIR / "test_scid_future_capture_blocked15_materialization_2026_05_12.py",
    "g12_starter": TARGET_DIR / f"G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_STARTER_{DATE}.txt",
    "target_prompt": TARGET_PROMPT,
    "control_prompt": CONTROL_PROMPT,
    "blocked_32_ledger": BLOCKED_LEDGER,
}

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
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".zip", ".bin", ".dly")
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_future_capture_blocked15_source_state_materialization_audit/",
    "research/science_program_2026_05/04_goal_prompts/G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_AFTER_FC_G12_AUDIT_GOAL_PROMPT_2026-05-12.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)

FORBIDDEN_ROW_KEYS = {
    "actual_r",
    "broker_actual_r",
    "synthetic_r",
    "synthetic_path_r",
    "realized_r",
    "pnl",
    "profit",
    "loss",
    "win_rate",
    "expectancy",
    "performance",
    "validation_label",
    "outcome_label",
    "result_label",
    "target_hit",
    "stop_hit",
    "raw_ticket",
    "order_ticket",
    "mt5_order_ticket",
    "history_order",
    "history_deal",
    "deal_id",
    "position_id",
    "account_id",
    "account_number",
    "balance",
    "equity",
}
ALLOWED_SAFE_KEYS = {
    "promotion_verdict",
    "validation_safe",
    "outcome_review_opened",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_raw_market_data_blob_commit",
    "downstream_g12_acceptance_rule",
    "forbidden_value_policy_id",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}{suffix}"


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip():
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_md(path: Path, title: str, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n",
        encoding="utf-8",
    )
    return path


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(artifact_path(stem), payload), write_md(artifact_path(stem, ".md"), title, payload)]


def safe_payload(family: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = {
        "artifact_family": family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "target_route_id": TARGET_ROUTE_ID,
        "target_evidence_class": TARGET_EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }
    base.update(payload)
    return base


def file_info(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists and path.is_file() else 0,
        "sha256": sha256_file(path) if exists and path.is_file() else None,
    }


def run_command(args: list[str], timeout: int = 120) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout, check=False)
    return {
        "command": args,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout": proc.stdout.splitlines(),
        "stderr": proc.stderr.splitlines(),
    }


def git_status_entries() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    rows = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in SCOPED_PREFIXES)
        rows.append(
            {
                "raw": line,
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "scoped_raw_market_blob": scoped and Path(path).suffix.lower() in RAW_SUFFIXES,
            }
        )
    scoped_rows = [row for row in rows if row["scoped"]]
    return {
        "entries": rows,
        "scoped_entries": scoped_rows,
        "unscoped_entry_count": len(rows) - len(scoped_rows),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_rows),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_rows),
    }


def load_target_payloads() -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    for name, path in TARGET_ARTIFACTS.items():
        if path.suffix == ".json":
            payloads[name] = read_json(path)
        elif path.suffix == ".jsonl":
            payloads[name] = read_jsonl(path)
        else:
            payloads[name] = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else None
    return payloads


def context_inventory() -> dict[str, Any]:
    required_context = [
        ".context/LIVE_STATE.md",
        ".context/00_core/quick_reference_card.md",
        ".context/00_core/goal_session_research_discipline.md",
        ".context/00_core/research_operating_doctrine.md",
        ".context/00_core/research_current_state.md",
        ".context/00_core/local_heavy_data_inventory.md",
        ".context/00_core/ai_in_loop_cost_control_research_plan.md",
        str(CONTROL_PROMPT.relative_to(REPO_ROOT)).replace("\\", "/"),
    ]
    artifact_rows = [file_info(path) for path in TARGET_ARTIFACTS.values()]
    return safe_payload(
        "context_and_input_inventory",
        {
            "mandatory_preflight_record": {
                "generate_live_state_ran_this_session": True,
                "live_state_read": True,
                "latest_handoff_read": True,
                "quick_reference_card_read": True,
                "goal_session_research_discipline_read": True,
                "research_operating_doctrine_read": True,
                "research_current_state_read": True,
                "local_heavy_data_inventory_read": True,
                "ai_in_loop_cost_control_plan_read": True,
                "controlling_prompt_read": True,
                "target_route_artifacts_read_from_disk": True,
            },
            "required_context_files": required_context,
            "target_artifact_count": len(artifact_rows),
            "target_artifacts": artifact_rows,
            "all_target_artifacts_exist_and_hash": all(row["exists"] and row["sha256"] for row in artifact_rows),
            "audit_posture": "G12 source-state audit only: accept only source/control materialization proof; reject leakage, denominator closure, vague contracts, missing search saturation, verifier/test failures, or forbidden live/result surfaces.",
        },
    )


def recompute_blocked15_and_capture_groups(payloads: dict[str, Any]) -> dict[str, Any]:
    ledger = read_json(BLOCKED_LEDGER)
    blocked_cards = ledger.get("blocked_cards", [])
    route_cards = [row for row in blocked_cards if row.get("assigned_next_route") == TARGET_ROUTE_ID]
    target_card_set = payloads["card_set"]
    matrix = payloads["matrix"]

    failures = []
    if len(route_cards) != 15:
        failures.append({"issue": "route_card_count_not_15", "observed": len(route_cards)})
    if target_card_set.get("blocked_card_count") != 15:
        failures.append({"issue": "target_card_set_count_not_15", "observed": target_card_set.get("blocked_card_count")})
    route_ids = [row.get("card_id") for row in route_cards]
    target_ids = [row.get("card_id") for row in target_card_set.get("cards", [])]
    if sorted(route_ids) != sorted(target_ids):
        failures.append({"issue": "target_card_ids_do_not_match_recomputed_route_cards", "recomputed": route_ids, "target": target_ids})
    if len(set(route_ids)) != len(route_ids):
        failures.append({"issue": "duplicate_recomputed_route_card_ids"})

    accepted_groups = set(matrix.get("accepted_capture_groups") or [])
    if accepted_groups != set(SCID_CAPTURE_GROUPS):
        failures.append({"issue": "accepted_capture_groups_not_exact", "observed": sorted(accepted_groups)})
    if matrix.get("accepted_capture_group_count") != 10:
        failures.append({"issue": "accepted_capture_group_count_not_10", "observed": matrix.get("accepted_capture_group_count")})

    unmapped_fields = []
    required_group_counts = Counter()
    for card in route_cards:
        required_groups = set(card.get("required_capture_groups") or [])
        for group in required_groups:
            required_group_counts[group] += 1
            if group not in SCID_CAPTURE_GROUPS:
                failures.append({"issue": "required_group_not_accepted", "card_id": card.get("card_id"), "field_group": group})
        matrix_row = next((row for row in matrix.get("card_field_group_matrix", []) if row.get("card_id") == card.get("card_id")), None)
        if not matrix_row:
            failures.append({"issue": "missing_matrix_row", "card_id": card.get("card_id")})
            continue
        matrix_groups = {row.get("field_group") for row in matrix_row.get("field_group_mappings", [])}
        if not required_groups.issubset(matrix_groups):
            failures.append(
                {
                    "issue": "matrix_missing_required_groups",
                    "card_id": card.get("card_id"),
                    "required": sorted(required_groups),
                    "matrix_groups": sorted(matrix_groups),
                }
            )
        for field in card.get("exact_missing_fields_or_source_status", []):
            field_group_hits = [group for group, fields in SCID_GROUP_FIELDS.items() if field in fields]
            if not field_group_hits and field not in {"candidate_input_row_id", "duplicate_proxy_denominator_key", "decision_asof_utc", "mso_snapshot_hash"} and not str(field).endswith("_hash"):
                unmapped_fields.append({"card_id": card.get("card_id"), "field": field})

    if unmapped_fields:
        failures.append({"issue": "missing_fields_without_group_or_common_mapping", "rows": unmapped_fields[:50]})

    return safe_payload(
        "blocked15_recomputation_and_capture_group_audit",
        {
            "blocked_32_ledger_path": rel(BLOCKED_LEDGER),
            "blocked_32_total_count": len(blocked_cards),
            "recomputed_blocked15_count": len(route_cards),
            "recomputed_card_ids": sorted(route_ids),
            "target_card_ids": sorted(target_ids),
            "required_capture_group_counts_recomputed": dict(sorted(required_group_counts.items())),
            "all_ten_capture_groups_visible": accepted_groups == set(SCID_CAPTURE_GROUPS),
            "accepted_capture_groups_recomputed": list(SCID_CAPTURE_GROUPS),
            "missing_field_mapping_failures": unmapped_fields[:50],
            "card_rows": [
                {
                    "card_id": row.get("card_id"),
                    "science_domain": row.get("science_domain"),
                    "required_capture_groups": row.get("required_capture_groups"),
                    "accepted_readiness": row.get("accepted_readiness"),
                    "may_score_results_now": row.get("may_score_results_now"),
                }
                for row in route_cards
            ],
            "failures": failures,
            "ok": not failures,
        },
    )


def source_search_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    search = payloads["search_ledger"]
    routes = search.get("same_evidence_class_recovery_routes_pursued") or []
    roots = search.get("searched_roots") or []
    input_artifacts = search.get("input_artifacts") or []
    source_summary = search.get("source_file_summary") or {}

    route_text = "\n".join(routes).lower()
    artifact_paths = "\n".join(row.get("path", "") for row in input_artifacts).lower()
    root_ids = {row.get("root_id") for row in roots}
    probe_paths = "\n".join(
        probe.get("relative_probe", "")
        for root in roots
        for probe in root.get("probe_results", [])
    ).lower()

    required_evidence = {
        "accepted_artifacts": "accepted" in route_text and "g0" in route_text,
        "additive_implementation_evidence": "scid_forward_capture_additive_implementation" in artifact_paths or "additive implementation" in route_text,
        "code_tests_verifiers": "src/research_infra/forward_capture.py" in artifact_paths and "tests/test_scid_forward_capture_runtime_adapter.py" in artifact_paths and "scripts/verify_scid_forward_capture_schema.py" in artifact_paths,
        "shadow_logs": "shadow_logs/strategy_follow_candidates.jsonl" in probe_paths and "shadow_logs/pending_limit_lifecycle_audit.jsonl" in probe_paths,
        "absolute_local_roots": "absolute_main_repo_root" in root_ids,
        "prior_worktrees": any(str(root_id or "").startswith("prior_parallel_worktree_") for root_id in root_ids),
    }
    failures = [
        {"issue": "missing_required_search_category", "category": key}
        for key, ok in required_evidence.items()
        if not ok
    ]
    if not input_artifacts or any(not row.get("exists") or not row.get("sha256") for row in input_artifacts):
        failures.append({"issue": "input_artifact_hash_gap"})

    return safe_payload(
        "source_search_saturation_audit",
        {
            "searched_root_count": len(roots),
            "searched_root_ids": sorted(str(root_id) for root_id in root_ids),
            "same_evidence_class_recovery_routes_pursued_count": len(routes),
            "same_evidence_class_recovery_routes_pursued": routes,
            "required_search_categories": required_evidence,
            "input_artifact_count": len(input_artifacts),
            "input_artifacts_all_exist_and_hash": bool(input_artifacts) and all(row.get("exists") and row.get("sha256") for row in input_artifacts),
            "source_file_summary": source_summary,
            "historical_non_generatable_boundary": search.get("historical_non_generatable_boundary"),
            "hard_boundary_skips": search.get("hard_boundary_skips", []),
            "failures": failures,
            "ok": not failures,
        },
    )


def recovered_row_schema_redaction_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    rows = payloads["recovered_rows"]
    registry: dict[str, str] = {}
    failures = []
    forbidden_hits = []
    group_counts = Counter()
    source_hash_counts = Counter()
    schema_versions = Counter()
    asof_failures = []

    for idx, row in enumerate(rows, start=1):
        group = row.get("field_group")
        group_counts[str(group)] += 1
        schema_versions[str(row.get("schema_version"))] += 1
        source_hash = row.get("source_hash")
        source_hash_counts[str(source_hash)] += 1
        validation = validate_scid_forward_source_capture_row(row, registry)
        if not validation["ok"]:
            failures.append({"row_number": idx, "field_group": group, "validation": validation})
        if not isinstance(source_hash, str) or len(source_hash) != 64:
            failures.append({"row_number": idx, "field_group": group, "issue": "invalid_source_hash"})
        for key, value in row.items():
            lowered_key = str(key).lower()
            if lowered_key in ALLOWED_SAFE_KEYS:
                continue
            if lowered_key in FORBIDDEN_ROW_KEYS or any(frag in lowered_key for frag in ("ticket", "deal_id", "position_id", "account_id", "history_order", "history_deal")):
                forbidden_hits.append({"row_number": idx, "field_group": group, "key": key, "value_preview": str(value)[:120]})
        for key in ("decision_asof_utc", "source_observed_asof_utc"):
            if not row.get(key):
                asof_failures.append({"row_number": idx, "field_group": group, "missing": key})
        if row.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append({"row_number": idx, "field_group": group, "issue": "promotion_verdict_not_safe"})
        if any(row.get(flag) is not False for flag in ("validation_safe", "outcome_review_opened", "live_effect", "opens_validation", "opens_result_scoring")):
            failures.append({"row_number": idx, "field_group": group, "issue": "safe_false_flag_not_false"})

    if forbidden_hits:
        failures.append({"issue": "forbidden_row_payload_or_identifier_hits", "hits": forbidden_hits[:50]})
    if asof_failures:
        failures.append({"issue": "asof_field_failures", "rows": asof_failures[:50]})
    if set(group_counts) != {
        "baseline_control_fields",
        "framework_setup_family",
        "intended_entry_reference",
        "intended_side_direction",
        "intended_stop_reference",
        "intended_target_reference",
        "lifecycle_fill_cancel_expiry_source_status",
    }:
        failures.append({"issue": "unexpected_recovered_group_set", "groups": dict(group_counts)})
    if len(rows) != 1213:
        failures.append({"issue": "recovered_row_count_not_1213", "observed": len(rows)})

    return safe_payload(
        "recovered_row_schema_redaction_audit",
        {
            "recovered_row_count": len(rows),
            "counts_by_group": dict(sorted(group_counts.items())),
            "schema_versions": dict(sorted(schema_versions.items())),
            "unique_source_hash_count": len(source_hash_counts),
            "validator_used": "src.research_infra.forward_capture.validate_scid_forward_source_capture_row",
            "validator_failure_count": sum(1 for row in failures if row.get("validation")),
            "forbidden_row_key_hits": forbidden_hits[:50],
            "asof_failure_count": len(asof_failures),
            "sample_source_identifiers": sorted({str(row.get("source_identifier")) for row in rows})[:10],
            "rows_are_source_state_examples_only": True,
            "accepted_40_result_denominator_closure_from_recovered_rows": False,
            "failures": failures[:100],
            "ok": not failures,
        },
    )


def prospective_contract_exactness_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    contract = payloads["prospective_contract"]
    contracts = contract.get("contracts", [])
    unblocking = payloads["unblocking"]
    matrix = payloads["matrix"]

    required_keys = (
        "source_logger",
        "as_of_clock",
        "redaction",
        "fail_closed_missing_status",
        "parser_hash_requirement",
        "owner_or_restart_gate",
        "tests_required",
        "g12_acceptance_criteria",
        "accepted_40_result_gate",
    )
    failures = []
    group_rows = {}
    for row in contracts:
        group = row.get("field_group")
        group_rows[group] = row
        for key in required_keys:
            if not row.get(key):
                failures.append({"field_group": group, "issue": f"missing_{key}"})
        if row.get("current_route_materialization", {}).get("accepted_40_denominator_unblocked") is not False:
            failures.append({"field_group": group, "issue": "denominator_unblocked_by_contract"})
        if "restart" not in str(row.get("owner_or_restart_gate", "")).lower():
            failures.append({"field_group": group, "issue": "owner_or_restart_gate_not_explicit"})
        if not row.get("tests_required") or not any("verifier" in str(item).lower() for item in row.get("tests_required", [])):
            failures.append({"field_group": group, "issue": "tests_required_lacks_verifier"})

    if set(group_rows) != set(SCID_CAPTURE_GROUPS):
        failures.append({"issue": "contract_group_set_not_exact", "observed": sorted(str(group) for group in group_rows)})
    if contract.get("contract_count") != 10:
        failures.append({"issue": "contract_count_not_10", "observed": contract.get("contract_count")})

    for card in unblocking.get("criteria_by_card", []):
        if card.get("may_score_results_now") is not False:
            failures.append({"card_id": card.get("card_id"), "issue": "may_score_results_now_not_false"})
        if card.get("validation_safe") is not False or card.get("outcome_review_opened") is not False:
            failures.append({"card_id": card.get("card_id"), "issue": "card_safe_flags_not_false"})
        for group in card.get("required_capture_groups", []):
            if group.get("does_recovery_unblock_card_now") is not False:
                failures.append({"card_id": card.get("card_id"), "field_group": group.get("field_group"), "issue": "recovery_unblocks_card_now"})

    return safe_payload(
        "prospective_contract_exactness_audit",
        {
            "contract_count": len(contracts),
            "contract_groups": sorted(str(group) for group in group_rows),
            "required_contract_keys": required_keys,
            "matrix_capture_group_summaries_count": len(matrix.get("capture_group_summaries", [])),
            "unblocking_card_count": unblocking.get("card_count"),
            "all_cards_remain_blocked_for_results": all(card.get("may_score_results_now") is False for card in unblocking.get("criteria_by_card", [])),
            "contract_rows": [
                {
                    "field_group": row.get("field_group"),
                    "source_logger": row.get("source_logger"),
                    "fail_closed_missing_status": row.get("fail_closed_missing_status"),
                    "materialization_status": row.get("current_route_materialization", {}).get("status"),
                    "recovered_row_count": row.get("current_route_materialization", {}).get("recovered_row_count"),
                    "accepted_40_denominator_unblocked": row.get("current_route_materialization", {}).get("accepted_40_denominator_unblocked"),
                }
                for row in contracts
            ],
            "failures": failures,
            "ok": not failures,
        },
    )


def denominator_quarantine_and_safe_flag_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    expansion = payloads["expansion"]
    noleak = payloads["noleak"]
    completion = payloads["completion"]
    manifest = payloads["manifest"]
    artifacts = [row for row in manifest.get("artifacts", [])]

    failures = []
    for name, artifact in payloads.items():
        if isinstance(artifact, dict):
            for flag, expected in SAFE_FLAGS.items():
                if flag in artifact and artifact.get(flag) != expected:
                    failures.append({"artifact": name, "issue": "safe_flag_mismatch", "flag": flag, "observed": artifact.get(flag), "expected": expected})
    if expansion.get("accepted_40_card_denominator_unchanged") is not True:
        failures.append({"artifact": "expansion", "issue": "accepted_40_denominator_changed"})
    if expansion.get("accepted_denominator_count") != 40:
        failures.append({"artifact": "expansion", "issue": "accepted_denominator_count_not_40"})
    for row in expansion.get("r3_quarantined_observations", []):
        if row.get("accepted_40_card_denominator_inclusion") is not False:
            failures.append({"artifact": "expansion", "issue": "r3_observation_included_in_accepted_denominator", "observation_id": row.get("observation_id")})
    upstream = expansion.get("upstream_quarantined_expansion_candidates", {})
    if upstream.get("total_quarantined_expansion_candidate_count") != 12:
        failures.append({"artifact": "expansion", "issue": "total_quarantined_expansion_count_not_12", "observed": upstream.get("total_quarantined_expansion_candidate_count")})
    if noleak.get("forbidden_text_scan_passed") is not True:
        failures.append({"artifact": "noleak", "issue": "target_forbidden_text_scan_failed"})
    if completion.get("accepted_40_denominator_boundaries_preserved") is not True:
        failures.append({"artifact": "completion", "issue": "accepted_40_boundaries_not_preserved"})
    if completion.get("historical_intent_order_lifecycle_inferred_from_price") is not False:
        failures.append({"artifact": "completion", "issue": "historical_truth_inferred_from_price"})
    if completion.get("no_validation_or_result_scoring_opened") is not True:
        failures.append({"artifact": "completion", "issue": "validation_or_result_scoring_opened"})
    raw_blob_artifacts = [row for row in artifacts if Path(row.get("path", "")).suffix.lower() in RAW_SUFFIXES]
    if raw_blob_artifacts:
        failures.append({"artifact": "manifest", "issue": "raw_market_blob_artifacts_present", "rows": raw_blob_artifacts})

    return safe_payload(
        "denominator_quarantine_and_safe_flag_audit",
        {
            "accepted_40_denominator_unchanged": expansion.get("accepted_40_card_denominator_unchanged"),
            "accepted_denominator_count": expansion.get("accepted_denominator_count"),
            "r3_quarantined_observation_count": len(expansion.get("r3_quarantined_observations", [])),
            "upstream_quarantined_expansion_candidate_count": upstream.get("total_quarantined_expansion_candidate_count"),
            "forbidden_text_scan_passed": noleak.get("forbidden_text_scan_passed"),
            "target_completion_can_mark_goal_complete": completion.get("can_mark_goal_complete"),
            "target_manifest_artifact_count": len(artifacts),
            "target_manifest_raw_blob_artifacts": raw_blob_artifacts,
            "failures": failures,
            "ok": not failures,
        },
    )


def target_verifier_test_rerun_ledger() -> dict[str, Any]:
    verifier_command = [
        "python",
        str(TARGET_ARTIFACTS["verifier"].relative_to(REPO_ROOT)),
        "--json",
    ]
    pytest_command = [
        "python",
        "-m",
        "pytest",
        str(TARGET_ARTIFACTS["focused_tests"].relative_to(REPO_ROOT)),
        "-q",
    ]
    verifier = run_command(verifier_command, timeout=120)
    focused = run_command(pytest_command, timeout=120)
    return safe_payload(
        "target_verifier_test_rerun_ledger",
        {
            "target_verifier_command": verifier,
            "target_focused_pytest_command": focused,
            "target_verifier_ok": verifier["ok"],
            "target_focused_tests_ok": focused["ok"],
            "target_verifier_stdout_summary": verifier["stdout"][:20],
            "target_pytest_stdout_summary": focused["stdout"][:20],
            "ok": verifier["ok"] and focused["ok"],
            "failures": [] if verifier["ok"] and focused["ok"] else [{"issue": "target_verifier_or_tests_failed"}],
        },
    )


def decision_ledger(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    check_map = {
        "context_and_inputs": audits["context"]["all_target_artifacts_exist_and_hash"],
        "blocked15_recomputation_and_capture_groups": audits["blocked15"]["ok"],
        "source_search_saturation": audits["source_search"]["ok"],
        "recovered_row_schema_redaction": audits["recovered_rows"]["ok"],
        "prospective_contract_exactness": audits["contract"]["ok"],
        "denominator_quarantine_and_safe_flags": audits["denominator"]["ok"],
        "target_verifier_and_focused_tests": audits["target_rerun"]["ok"],
    }
    terminal_blockers = [name for name, ok in check_map.items() if ok is not True]
    terminal_decision = TERMINAL_REPAIR if terminal_blockers else TERMINAL_ACCEPT
    return safe_payload(
        "decision_ledger",
        {
            "terminal_decision": terminal_decision,
            "terminal_blockers": terminal_blockers,
            "accepted_g12_control_evidence_only": terminal_decision == TERMINAL_ACCEPT,
            "accepted_validation_execution": False,
            "accepted_strategy_performance": False,
            "accepted_promotion": False,
            "next_g0_synthesis_prompt_required": terminal_decision == TERMINAL_ACCEPT,
            "repair_prompt_required": terminal_decision != TERMINAL_ACCEPT,
            "check_map": check_map,
            "verified_counts": {
                "blocked15_card_count": audits["blocked15"]["recomputed_blocked15_count"],
                "capture_group_count": len(audits["blocked15"]["accepted_capture_groups_recomputed"]),
                "recovered_source_state_rows": audits["recovered_rows"]["recovered_row_count"],
                "contract_count": audits["contract"]["contract_count"],
                "r3_quarantined_observations": audits["denominator"]["r3_quarantined_observation_count"],
                "upstream_quarantined_expansion_candidates": audits["denominator"]["upstream_quarantined_expansion_candidate_count"],
            },
            "decision_rationale": "The target route is accepted only as source/control evidence if all recomputed counts, source-search saturation, recovered-row schema/redaction validation, contract exactness, denominator quarantine, safe flags, and target verifier/tests pass. Recovered rows are source-state examples and do not close accepted-40 result denominators.",
        },
    )


def write_next_g0_prompt(decision: dict[str, Any]) -> list[Path]:
    if decision["terminal_decision"] != TERMINAL_ACCEPT:
        return []

    body = {
        "title": "G0 SCID Blocked-Card Unblocking Synthesis After G12 Future-Capture Source Audit",
        "evidence_class": "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT_ONLY",
        "objective": (
            "Synthesize the accepted G12 audit of the blocked15 source-state materialization package with the other accepted blocked-card routes, then rank the next source-control/unblocking route bundle with no validation/results, no promotion, no AI/API, no paid/vendor, no broker-account/order/history/deal/position, no raw-market-blob, no live-restart, no live-behavior, and no trading-risk-safety-prompt-decision changes."
        ),
        "mandatory_preflight": [
            "python scripts/generate_live_state.py",
            ".context/LIVE_STATE.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/ai_in_loop_cost_control_research_plan.md",
        ],
        "required_inputs": [
            rel(artifact_path("DECISION_LEDGER")),
            rel(artifact_path("COMPLETION_AUDIT")),
            rel(artifact_path("RECOVERED_ROW_SCHEMA_REDACTION_AUDIT")),
            rel(artifact_path("PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT")),
            rel(artifact_path("DENOMINATOR_QUARANTINE_AND_SAFE_FLAG_AUDIT")),
            rel(BLOCKED_LEDGER),
        ],
        "accepted_g12_facts_to_preserve": {
            "blocked15_route_accepted_as_control_evidence_only": True,
            "blocked15_card_count": 15,
            "capture_group_count": 10,
            "recovered_source_state_rows": 1213,
            "recovered_groups": [
                "baseline_control_fields",
                "framework_setup_family",
                "intended_entry_reference",
                "intended_side_direction",
                "intended_stop_reference",
                "intended_target_reference",
                "lifecycle_fill_cancel_expiry_source_status",
            ],
            "prospective_or_fail_closed_groups": [
                "poi_type_bounds_source",
                "lower_timeframe_asof_path_availability",
                "future_orderflow_depth_proxy_requirements",
            ],
            "accepted_40_result_denominator_unblocked": False,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "required_outputs": [
            "G0 decision ledger",
            "blocked-card route reconciliation ledger",
            "ranked unblocking route bundle",
            "denominator-quarantine and source-state gate ledger",
            "next controlling prompt/starter or exact repair prompt/starter",
            "completion audit",
            "standalone verifier and focused tests",
        ],
        "forbidden_surfaces": [
            "validation",
            "results",
            "R/PnL/win-rate/expectancy/performance",
            "promotion",
            "AI/API",
            "paid vendor access",
            "broker account/order/history/deal/position evidence",
            "raw market blob commit",
            "live restart",
            "live behavior",
            "trading/risk/safety/prompt-decision changes",
        ],
        "safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "completion_standard": (
            "Complete only when every accepted blocked-card source/control route is reconciled from disk, blocked-card denominators remain quarantined from result rows, next routes are ranked with exact evidence-class gates, verifier/focused tests pass, and scoped artifacts are committed. If any same-evidence-class blocker remains, pursue or reduce it to an exact source/capture/owner/access requirement."
        ),
    }
    NEXT_G0_PROMPT.write_text(
        "# " + body["title"] + "\n\n```json\n" + json.dumps(body, indent=2, sort_keys=True, ensure_ascii=True) + "\n```\n",
        encoding="utf-8",
    )
    starter = (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/04_goal_prompts/G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_AFTER_FC_G12_AUDIT_GOAL_PROMPT_2026-05-12.md "
        "as the complete objective; run mandatory preflight/context refresh; do not rely on chat memory; stay G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT_ONLY "
        "with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes; "
        "reconcile accepted blocked-card source-control routes from disk, preserve denominator quarantine, rank exact next unblocking routes, run verifier/focused tests, emit scoped artifacts, and keep NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false."
    )
    NEXT_G0_STARTER.write_text(starter + "\n", encoding="utf-8")
    return [NEXT_G0_PROMPT, NEXT_G0_STARTER]


def completion_audit(audits: dict[str, dict[str, Any]], decision: dict[str, Any], next_paths: list[Path]) -> dict[str, Any]:
    checklist = [
        ("mandatory preflight/context refresh", True, rel(artifact_path("CONTEXT_AND_INPUT_INVENTORY"))),
        ("recompute blocked15 subset from blocked-32 ledger", audits["blocked15"]["recomputed_blocked15_count"] == 15 and audits["blocked15"]["ok"], rel(artifact_path("BLOCKED15_RECOMPUTATION_AND_CAPTURE_GROUP_AUDIT"))),
        ("verify missing fields map to accepted capture groups and all ten groups visible", audits["blocked15"]["all_ten_capture_groups_visible"] and audits["blocked15"]["ok"], rel(artifact_path("BLOCKED15_RECOMPUTATION_AND_CAPTURE_GROUP_AUDIT"))),
        ("validate every recovered SCID row with forward_capture validator", audits["recovered_rows"]["ok"] and audits["recovered_rows"]["recovered_row_count"] == 1213, rel(artifact_path("RECOVERED_ROW_SCHEMA_REDACTION_AUDIT"))),
        ("confirm recovered rows contain no forbidden broker/result/performance payloads", audits["recovered_rows"]["ok"] and not audits["recovered_rows"]["forbidden_row_key_hits"], rel(artifact_path("RECOVERED_ROW_SCHEMA_REDACTION_AUDIT"))),
        ("confirm recovered rows are source-state examples, not result-denominator closure", audits["denominator"]["ok"] and audits["contract"]["all_cards_remain_blocked_for_results"], rel(artifact_path("DENOMINATOR_QUARANTINE_AND_SAFE_FLAG_AUDIT"))),
        ("confirm prospective contracts cover logger/as-of/redaction/fail-closed/parser-owner-test-G12 fields", audits["contract"]["ok"], rel(artifact_path("PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT"))),
        ("confirm search ledger covers accepted artifacts/additive evidence/code/tests/shadow logs/absolute roots/prior worktrees", audits["source_search"]["ok"], rel(artifact_path("SOURCE_SEARCH_SATURATION_AUDIT"))),
        ("confirm no forbidden validation/result/live/AI/API/broker/raw-market/trading-risk surfaces opened", audits["denominator"]["ok"], rel(artifact_path("DENOMINATOR_QUARANTINE_AND_SAFE_FLAG_AUDIT"))),
        ("rerun target verifier and focused tests", audits["target_rerun"]["ok"], rel(artifact_path("TARGET_VERIFIER_TEST_RERUN_LEDGER"))),
        ("emit next G0 synthesis prompt/starter only if accepted", decision["terminal_decision"] != TERMINAL_ACCEPT or all(path.exists() for path in next_paths), ", ".join(rel(path) for path in next_paths) if next_paths else "not emitted because repair required"),
        ("G12 standalone verifier passed", False, "pending verifier run"),
        ("G12 focused tests passed", False, "pending focused pytest run"),
        ("scoped commit complete", False, "pending commit after verification"),
    ]
    missing = [item[0] for item in checklist if not item[1]]
    return safe_payload(
        "completion_audit",
        {
            "objective_restatement": "Audit the blocked15 future-capture/source-state materialization route as G12 control evidence only, independently recomputing the blocked set, recovered-row validity, source hashes, as-of/redaction/fail-closed boundaries, search saturation, prospective contracts, denominator quarantine, target verifier/tests, and safe flags.",
            "prompt_to_artifact_checklist": [
                {"requirement": req, "satisfied": bool(ok), "evidence": evidence}
                for req, ok, evidence in checklist
            ],
            "instruction_coverage": {
                "goal_session_research_discipline_read_after_preflight": True,
                "research_operating_doctrine_read_after_preflight": True,
                "lane_type": "G12 audit",
                "posture_applied": "fair-adversarial source-state audit; strict on recomputation, source hashes, schema validation, no-leak, denominator quarantine, contracts, verifier/tests, and forbidden surfaces.",
                "anti_boxing_questions_pursued": [
                    "Did the audit recompute the target route's 15 cards from the upstream blocked-32 ledger?",
                    "Did all ten SCID capture groups remain visible even when only seven have recovered rows?",
                    "Are recovered rows valid source-state examples rather than accepted-40 result rows?",
                    "Are non-generatable historical source-state truths left fail-closed with exact prospective contracts?",
                    "Did search saturation include current worktree, absolute local roots, prior worktrees, artifacts, code, tests, verifiers, and shadow logs?",
                ],
                "proof_or_impossibility_stop_condition": "Accept only if all same-evidence-class audit checks and target verifier/tests pass; otherwise emit an exact repair route without G0 synthesis.",
                "requirements_not_answered_because_forbidden": [
                    "validation",
                    "result scoring",
                    "R/PnL/win-rate/expectancy/performance review",
                    "promotion",
                    "AI/API or paid-vendor access",
                    "broker account/order/history/deal/position evidence",
                    "raw market blob inspection/commit",
                    "live restart/live behavior",
                    "trading/risk/safety/prompt-decision changes",
                ],
            },
            "terminal_decision": decision["terminal_decision"],
            "missing_incomplete_or_weakly_verified_requirements": missing,
            "completion_standard_satisfied": False,
            "can_mark_goal_complete": False,
        },
    )


def output_manifest(paths: list[Path]) -> dict[str, Any]:
    artifact_rows = []
    for path in sorted(set(paths)):
        artifact_rows.append(file_info(path))
    return safe_payload(
        "output_manifest",
        {
            "artifact_count": len(artifact_rows),
            "artifacts": artifact_rows,
            "raw_market_blob_artifacts": [row for row in artifact_rows if Path(row["path"]).suffix.lower() in RAW_SUFFIXES],
            "manifest_self_hash_policy": "Verifier recomputes artifact hashes after build. This manifest is not used as its own blocking self-hash input.",
        },
    )


def build() -> dict[str, Any]:
    payloads = load_target_payloads()
    audits = {
        "context": context_inventory(),
        "blocked15": recompute_blocked15_and_capture_groups(payloads),
        "source_search": source_search_audit(payloads),
        "recovered_rows": recovered_row_schema_redaction_audit(payloads),
        "contract": prospective_contract_exactness_audit(payloads),
        "denominator": denominator_quarantine_and_safe_flag_audit(payloads),
        "target_rerun": target_verifier_test_rerun_ledger(),
    }
    decision = decision_ledger(audits)
    next_paths = write_next_g0_prompt(decision)
    completion = completion_audit(audits, decision, next_paths)

    paths: list[Path] = []
    paths += write_pair("CONTEXT_AND_INPUT_INVENTORY", "Context And Input Inventory", audits["context"])
    paths += write_pair("BLOCKED15_RECOMPUTATION_AND_CAPTURE_GROUP_AUDIT", "Blocked15 Recompution And Capture Group Audit", audits["blocked15"])
    paths += write_pair("SOURCE_SEARCH_SATURATION_AUDIT", "Source Search Saturation Audit", audits["source_search"])
    paths += write_pair("RECOVERED_ROW_SCHEMA_REDACTION_AUDIT", "Recovered Row Schema Redaction Audit", audits["recovered_rows"])
    paths += write_pair("PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT", "Prospective Contract Exactness Audit", audits["contract"])
    paths += write_pair("DENOMINATOR_QUARANTINE_AND_SAFE_FLAG_AUDIT", "Denominator Quarantine And Safe Flag Audit", audits["denominator"])
    paths += write_pair("TARGET_VERIFIER_TEST_RERUN_LEDGER", "Target Verifier Test Rerun Ledger", audits["target_rerun"])
    paths += write_pair("DECISION_LEDGER", "Decision Ledger", decision)
    paths += write_pair("COMPLETION_AUDIT", "Completion Audit", completion)
    paths.extend(next_paths)
    paths.extend(
        [
            ROUTE_DIR / "build_g12_scid_future_capture_blocked15_source_state_materialization_audit_2026_05_12.py",
            ROUTE_DIR / "verify_g12_scid_future_capture_blocked15_source_state_materialization_audit_2026_05_12.py",
            ROUTE_DIR / "test_g12_scid_future_capture_blocked15_source_state_materialization_audit_2026_05_12.py",
        ]
    )
    manifest = output_manifest(paths)
    paths += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)
    return decision


if __name__ == "__main__":
    result = build()
    print(json.dumps({"terminal_decision": result["terminal_decision"], "terminal_blockers": result["terminal_blockers"]}, indent=2, sort_keys=True))
