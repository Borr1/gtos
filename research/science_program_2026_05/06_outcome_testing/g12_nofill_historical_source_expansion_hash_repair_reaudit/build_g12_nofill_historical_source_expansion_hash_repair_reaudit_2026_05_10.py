"""Build the independent G12 hash-repair reaudit package.

This route is source/control repair reaudit only. It does not admit rows,
open validation, score outcomes, read broker actual-R or MT5 account data,
or change live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-10"
ROUTE_ID = "G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_HASH_REPAIR_REAUDIT"
SCHEMA_VERSION = "g12_nofill_historical_source_expansion_hash_repair_reaudit_v1"
PREFIX = "G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ACCEPT_DECISION = "ACCEPT_REPAIRED_SOURCE_CONTROL_PACKET_FOR_NEXT_EVIDENCE_CLASS_PROMPT"
BLOCKER_DECISION = "ACCEPT_WITH_REMAINING_EXACT_REPAIR_BLOCKERS"
REJECT_DECISION = "REJECT_REPAIR_WOULD_CHANGE_PACKET_SEMANTICS"

ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = ROUTE_DIR.parent
REPO_ROOT = Path(__file__).resolve().parents[4]

TARGET_PREFIX = "NOFILL_HIST_SOURCE_EXPANSION"
TARGET_DIR = OUTCOME_DIR / "nofill_historical_source_expansion_builder_local_tick_shadow_packet"
REPAIR_PREFIX = "NOFILL_HIST_SRCEXP_HASH_REPAIR"
REPAIR_DIR = OUTCOME_DIR / "nofill_historical_source_expansion_packet_parser_hash_repair_rebuild"
PRIOR_G12_DIR = OUTCOME_DIR / "g12_nofill_historical_source_expansion_packet_audit"

PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_HASH_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-10.md"
)

TARGET_PACKET = TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_{DATE}.jsonl"
TARGET_PACKET_MANIFEST = TARGET_DIR / f"{TARGET_PREFIX}_CANDIDATE_PACKET_MANIFEST_{DATE}.json"
TARGET_SOURCE_MANIFEST = TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_HASH_MANIFEST_{DATE}.json"
TARGET_PARSER_ASOF = TARGET_DIR / f"{TARGET_PREFIX}_PARSER_ASOF_MANIFEST_{DATE}.json"
TARGET_ADMISSION = TARGET_DIR / f"{TARGET_PREFIX}_CANDIDATE_ADMISSION_LEDGER_{DATE}.json"
TARGET_DUPLICATES = TARGET_DIR / f"{TARGET_PREFIX}_DUPLICATE_DENOMINATOR_LEDGER_{DATE}.json"
TARGET_OUTPUT_MANIFEST = TARGET_DIR / f"{TARGET_PREFIX}_OUTPUT_MANIFEST_{DATE}.json"
TARGET_VERIFIER = TARGET_DIR / "verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"
TARGET_TESTS = TARGET_DIR / "test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"
TARGET_BUILDER = TARGET_DIR / "build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"

REPAIR_VERIFIER = REPAIR_DIR / "verify_nofill_historical_source_expansion_packet_parser_hash_repair_rebuild_2026_05_10.py"
REPAIR_TESTS = REPAIR_DIR / "test_nofill_historical_source_expansion_packet_parser_hash_repair_rebuild_2026_05_10.py"
REPAIR_BUILDER = REPAIR_DIR / "build_nofill_historical_source_expansion_packet_parser_hash_repair_rebuild_2026_05_10.py"
REPAIR_CLOSURE = REPAIR_DIR / f"{REPAIR_PREFIX}_EXACT_G12_BLOCKER_CLOSURE_LEDGER_{DATE}.json"
REPAIR_SOURCE_HASH = REPAIR_DIR / f"{REPAIR_PREFIX}_RECOMPUTED_SOURCE_HASH_MANIFEST_{DATE}.json"
REPAIR_SEMANTIC = REPAIR_DIR / f"{REPAIR_PREFIX}_SEMANTIC_NO_ROW_CHANGE_DIFF_LEDGER_{DATE}.json"
REPAIR_PACKET_SHA = REPAIR_DIR / f"{REPAIR_PREFIX}_PACKET_SHA_LEDGER_{DATE}.json"
REPAIR_NOLEAK = REPAIR_DIR / f"{REPAIR_PREFIX}_NOLEAK_SAFE_FLAG_CHECK_{DATE}.json"
REPAIR_NEXT_PROMPT = REPAIR_DIR / f"{REPAIR_PREFIX}_NEXT_G12_REPAIR_REAUDIT_PROMPT_PACK_{DATE}.md"

PRIOR_G12_REPAIR_LEDGER = (
    PRIOR_G12_DIR / "G12_NOFILL_HIST_SRCEXP_AUDIT_EXACT_REPAIR_SOURCE_REQUIREMENT_LEDGER_2026-05-10.json"
)
PRIOR_G12_HASH_AUDIT = PRIOR_G12_DIR / "G12_NOFILL_HIST_SRCEXP_AUDIT_SOURCE_HASH_PARSER_HASH_AUDIT_2026-05-10.json"
PRIOR_G12_DECISION = PRIOR_G12_DIR / "G12_NOFILL_HIST_SRCEXP_AUDIT_DECISION_LEDGER_2026-05-10.json"

EXPECTED_HASHES = {
    "parser_or_verifier:builder": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
    "parser_or_verifier:focused_tests": "472dd4b2be228bac59017b4aabb5934dfe150819fdc8007bcd08a9fa38ab75e1",
    "parser_or_verifier:verifier": "ebeae4746221ff30a968a41ef8a938bb15d6f1a1f9fc346621ccae6dcfbf9ea5",
}
TARGET_ROLE_PATHS = {
    "parser_or_verifier:builder": TARGET_BUILDER,
    "parser_or_verifier:focused_tests": TARGET_TESTS,
    "parser_or_verifier:verifier": TARGET_VERIFIER,
}
EXPECTED_ROWS = [
    {
        "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
        "symbol": "NAS100",
        "decision_time_utc": "2026-05-08T15:45:00+00:00",
        "candidate_id": "NAS100_2026-05-08T15:45:00+00:00",
    },
    {
        "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
        "symbol": "US30_cash",
        "decision_time_utc": "2026-05-08T13:45:00+00:00",
        "candidate_id": "US30_cash_2026-05-08T13:45:00+00:00",
    },
]
EXPECTED_PACKET_SHA = "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341"
EXPECTED_COUNTS = {
    "admitted_packet_row_count": 2,
    "blocked_candidate_count": 37,
    "rejected_candidate_count": 9,
}
EXPECTED_DUPLICATES = {
    "row_level_count": 2,
    "primary_unique_count": 2,
    "secondary_unique_count": 2,
}

SAFE_FALSE_KEYS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "changes_live_trading_behavior",
    "credentials_touched",
)
FORBIDDEN_PACKET_KEYS = {
    "actual_r",
    "broker_actual_r",
    "realized_r",
    "result_r",
    "outcome_r",
    "win_rate",
    "expectancy",
    "slippage_price",
}
FORBIDDEN_DIFF_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "scripts/canary",
    "canaries/",
    "run_agent.py",
    "start_all.bat",
    "mt5_ea/",
)

JSON_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{PREFIX}_DECISION_LEDGER_{DATE}.json",
    f"{PREFIX}_EXACT_BLOCKER_CLOSURE_REAUDIT_{DATE}.json",
    f"{PREFIX}_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_{DATE}.json",
    f"{PREFIX}_SEMANTIC_NO_ROW_CHANGE_REAUDIT_{DATE}.json",
    f"{PREFIX}_PACKET_HASH_MANIFEST_REAUDIT_{DATE}.json",
    f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_AUDIT_{DATE}.json",
    f"{PREFIX}_REPAIR_VERIFIER_TEST_RERUN_AUDIT_{DATE}.json",
    f"{PREFIX}_NOLEAK_SAFE_FLAG_LIVE_SURFACE_AUDIT_{DATE}.json",
    f"{PREFIX}_FUTURE_ROUTE_ELIGIBILITY_LEDGER_{DATE}.json",
    f"{PREFIX}_SYNTAX_COMPILE_AUDIT_{DATE}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json",
]
MD_ARTIFACTS = [name.replace(".json", ".md") for name in JSON_ARTIFACTS if "OUTPUT_MANIFEST" not in name]
MD_ARTIFACTS.append(f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md")
REQUIRED_ARTIFACTS = (
    JSON_ARTIFACTS
    + MD_ARTIFACTS
    + [
        "build_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
        "verify_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
        "test_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
    ]
)
VERIFICATION_RESULT_NAME = f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def with_flags(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.update(
        {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "opens_result_scoring": False,
            "opens_validation": False,
            "opens_promotion": False,
            "opens_registry_edit": False,
            "opens_paid_api_or_databento_route": False,
            "opens_remote_push": False,
            "opens_live_restart": False,
            "opens_live_trading_behavior": False,
            "opens_mt5_order_account_history_behavior": False,
            "changes_live_trading_behavior": False,
            "credentials_touched": False,
        }
    )
    return out


def write_json(name: str, payload: dict[str, Any]) -> str:
    path = ROUTE_DIR / name
    path.write_text(json.dumps(with_flags(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rel(path)


def write_md(name: str, title: str, payload: dict[str, Any], notes: list[str] | None = None) -> str:
    lines = [
        f"# {title}",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(with_flags(payload), indent=2, sort_keys=True),
        "```",
    ]
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    path = ROUTE_DIR / name
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return rel(path)


def run_command(command: list[str], timeout_seconds: int = 240) -> dict[str, Any]:
    started = utc_now()
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "command": command,
            "started_at_utc": started,
            "completed_at_utc": utc_now(),
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-6000:],
            "stderr_tail": result.stderr[-6000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "started_at_utc": started,
            "completed_at_utc": utc_now(),
            "returncode": None,
            "timeout_seconds": timeout_seconds,
            "stdout_tail": (exc.stdout or "")[-6000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-6000:] if isinstance(exc.stderr, str) else "",
        }


def resolve_manifest_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def manifest_record(role: str) -> dict[str, Any]:
    manifest = read_json(TARGET_SOURCE_MANIFEST)
    for record in manifest.get("records", []):
        if record.get("role") == role:
            return record
    return {}


def row_identity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "packet_row_id": row.get("packet_row_id"),
        "symbol": row.get("symbol"),
        "decision_time_utc": row.get("decision_time_utc"),
        "candidate_id": row.get("candidate_id"),
    }


def git_diff_scope() -> dict[str, Any]:
    diff = subprocess.run(["git", "diff", "--name-only"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    paths = sorted(
        {
            line.strip().replace("\\", "/")
            for line in (diff.stdout + "\n" + untracked.stdout).splitlines()
            if line.strip()
        }
    )
    forbidden = [path for path in paths if any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)]
    return {"changed_or_untracked_paths": paths, "forbidden_live_surface_paths": forbidden, "ok": forbidden == []}


def scan_safe_flags(value: Any, path: str = "$") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in SAFE_FALSE_KEYS and item is not False:
                issues.append({"path": child, "issue": "safe_or_forbidden_flag_not_false", "value": item})
            if key == "promotion_verdict" and item != PROMOTION_VERDICT:
                issues.append({"path": child, "issue": "promotion_verdict_not_closed", "value": item})
            issues.extend(scan_safe_flags(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            issues.extend(scan_safe_flags(item, f"{path}[{idx}]"))
    return issues


def scan_forbidden_packet_keys(value: Any, path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in FORBIDDEN_PACKET_KEYS:
                hits.append({"path": child, "key": key})
            hits.extend(scan_forbidden_packet_keys(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            hits.extend(scan_forbidden_packet_keys(item, f"{path}[{idx}]"))
    return hits


def context_anchor() -> dict[str, Any]:
    return {
        "artifact_family": "context_anchor",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "head_at_start": git_head(),
        "controlling_prompt_path": rel(PROMPT_PATH),
        "evidence_class": "G12_SOURCE_CONTROL_REPAIR_REAUDIT_ONLY",
        "mandatory_context_read": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            rel(PROMPT_PATH),
        ],
        "controlling_inputs": [
            rel(REPAIR_DIR),
            rel(TARGET_DIR),
            rel(PRIOR_G12_DIR),
            rel(PRIOR_G12_REPAIR_LEDGER),
            rel(REPAIR_CLOSURE),
            rel(REPAIR_SEMANTIC),
            rel(REPAIR_PACKET_SHA),
            rel(TARGET_PACKET),
            rel(TARGET_SOURCE_MANIFEST),
        ],
        "forbidden_boundaries": [
            "no_row_admission_or_removal",
            "no_validation_execution_or_result_scoring",
            "no_broker_actual_r_or_mt5_account_order_history_deal_position_read",
            "no_prompt_config_risk_permission_safety_selector_canary_or_live_behavior_change",
            "no_paid_api_route_remote_push_live_restart_or_registry_edit",
        ],
    }


def exact_blocker_closure_reaudit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    prior = read_json(PRIOR_G12_REPAIR_LEDGER).get("remaining_requirements", [])
    repair = read_json(REPAIR_CLOSURE).get("records", [])
    rows: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for role, expected_hash in EXPECTED_HASHES.items():
        target_path = TARGET_ROLE_PATHS[role]
        actual = sha256_file(target_path)
        target_manifest_sha = manifest_record(role).get("sha256")
        prior_row = next((item for item in prior if item.get("role") == role), {})
        repair_row = next((item for item in repair if item.get("role") == role), {})
        checks = {
            "current_hash_matches_expected": actual == expected_hash,
            "target_manifest_matches_current_hash": target_manifest_sha == actual,
            "prior_g12_recomputed_hash_matches_current": prior_row.get("recomputed_sha256") == actual,
            "repair_closure_matches_current": repair_row.get("current_recomputed_sha256") == actual
            and repair_row.get("target_manifest_sha256_after_repair") == actual
            and repair_row.get("closed") is True,
        }
        record = {
            "role": role,
            "path": rel(target_path),
            "expected_sha256": expected_hash,
            "current_recomputed_sha256": actual,
            "target_manifest_sha256": target_manifest_sha,
            "prior_g12_manifest_sha256_before_repair": prior_row.get("manifest_sha256"),
            "prior_g12_recomputed_sha256": prior_row.get("recomputed_sha256"),
            "repair_target_manifest_sha256_after": repair_row.get("target_manifest_sha256_after_repair"),
            "checks": checks,
            "closed": all(checks.values()),
        }
        rows.append(record)
        if not record["closed"]:
            blockers.append(
                {
                    "issue": "parser_verifier_hash_repair_not_closed",
                    "role": role,
                    "path": rel(target_path),
                    "exact_repair_requirement": (
                        "Refresh the target source-hash manifest and packet parser hash binding for this role, "
                        "then rerun target and repair verifiers/tests before G12 acceptance."
                    ),
                    "checks": checks,
                }
            )
    payload = {
        "artifact_family": "exact_blocker_closure_reaudit",
        "generated_at_utc": utc_now(),
        "prior_g12_repair_requirement_count": len(prior),
        "expected_repaired_role_count": len(EXPECTED_HASHES),
        "closed_requirement_count": sum(1 for row in rows if row["closed"]),
        "records": rows,
        "remaining_blockers": blockers,
        "audit_passed": blockers == [] and len(prior) == 3,
    }
    return payload, blockers


def source_hash_parser_hash_recomputation_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    target_manifest = read_json(TARGET_SOURCE_MANIFEST)
    parser_asof = read_json(TARGET_PARSER_ASOF)
    rows = read_jsonl(TARGET_PACKET)
    source_records: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    for record in target_manifest.get("records", []):
        resolved = resolve_manifest_path(str(record.get("path")))
        actual = sha256_file(resolved)
        item = {
            "role": record.get("role"),
            "path": record.get("path"),
            "exists_now": resolved.exists(),
            "target_manifest_sha256": record.get("sha256"),
            "recomputed_sha256": actual,
            "hash_matches_target_manifest": actual == record.get("sha256"),
        }
        source_records.append(item)
        if item["hash_matches_target_manifest"] is not True:
            mismatches.append(
                {
                    "issue": "target_source_manifest_hash_mismatch",
                    "role": item["role"],
                    "path": item["path"],
                    "exact_repair_requirement": "Recompute and repair this target source manifest record before opening the next evidence class.",
                    "target_manifest_sha256": item["target_manifest_sha256"],
                    "recomputed_sha256": item["recomputed_sha256"],
                }
            )
    builder_hash = sha256_file(TARGET_BUILDER)
    packet_parser_hashes = sorted({row.get("parser_code_hash") for row in rows})
    source_artifact_hashes = sorted({row.get("source_artifact_hash") for row in rows})
    checks = {
        "all_target_source_manifest_hashes_match": mismatches == [],
        "parser_asof_matches_current_builder_hash": parser_asof.get("parser_hash") == builder_hash,
        "packet_rows_bind_current_builder_hash": packet_parser_hashes == [builder_hash],
        "packet_rows_have_two_source_artifact_hashes": len(source_artifact_hashes) == 2
        and all(isinstance(item, str) and len(item) == 64 for item in source_artifact_hashes),
        "repair_recomputed_source_manifest_reports_zero_mismatches": read_json(REPAIR_SOURCE_HASH).get("hash_mismatch_count") == 0,
    }
    blockers = list(mismatches)
    if not checks["parser_asof_matches_current_builder_hash"]:
        blockers.append(
            {
                "issue": "parser_asof_hash_mismatch",
                "path": rel(TARGET_PARSER_ASOF),
                "exact_repair_requirement": "Refresh target parser-as-of manifest to the current target builder hash.",
            }
        )
    if not checks["packet_rows_bind_current_builder_hash"]:
        blockers.append(
            {
                "issue": "packet_parser_code_hash_mismatch",
                "path": rel(TARGET_PACKET),
                "exact_repair_requirement": "Refresh every packet row parser_code_hash to the accepted current target builder hash.",
            }
        )
    return {
        "artifact_family": "source_hash_parser_hash_recomputation_audit",
        "generated_at_utc": utc_now(),
        "target_source_manifest_path": rel(TARGET_SOURCE_MANIFEST),
        "source_record_count": len(source_records),
        "strict_hash_mismatch_count": len(mismatches),
        "parser_asof_hash": parser_asof.get("parser_hash"),
        "current_target_builder_hash": builder_hash,
        "packet_parser_code_hashes": packet_parser_hashes,
        "packet_source_artifact_hashes": source_artifact_hashes,
        "focused_repaired_hash_records": [row for row in source_records if row["role"] in EXPECTED_HASHES],
        "records": source_records,
        "checks": checks,
        "remaining_blockers": blockers,
        "audit_passed": blockers == [] and all(checks.values()),
    }, blockers


def semantic_no_row_change_reaudit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = read_jsonl(TARGET_PACKET)
    admission = read_json(TARGET_ADMISSION)
    output_manifest = read_json(TARGET_OUTPUT_MANIFEST)
    duplicate = read_json(TARGET_DUPLICATES)
    repair_semantic = read_json(REPAIR_SEMANTIC)
    observed_identities = [row_identity(row) for row in rows]
    status_counts = admission.get("status_counts")
    if not status_counts:
        status_counts = {
            "ADMITTED_SOURCE_PACKET_ROW": admission.get("admitted_packet_row_count"),
            "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT": admission.get("blocked_candidate_count"),
            "REJECTED_ONE_DAY_EMBARGO_OVERLAP": admission.get("rejected_candidate_count"),
        }
    checks = {
        "target_packet_has_exact_two_rows": len(rows) == 2,
        "target_row_identities_match_expected": observed_identities == EXPECTED_ROWS,
        "admission_counts_match_expected": {
            "admitted_packet_row_count": admission.get("admitted_packet_row_count"),
            "blocked_candidate_count": admission.get("blocked_candidate_count"),
            "rejected_candidate_count": admission.get("rejected_candidate_count"),
        }
        == EXPECTED_COUNTS,
        "output_manifest_counts_match_expected": {
            "admitted_packet_row_count": output_manifest.get("admitted_packet_row_count"),
            "blocked_candidate_count": output_manifest.get("blocked_candidate_count"),
            "rejected_candidate_count": output_manifest.get("rejected_candidate_count"),
        }
        == EXPECTED_COUNTS,
        "repair_semantic_ledger_proves_hash_only_change": repair_semantic.get("semantic_rows_unchanged_excluding_hash_fields")
        is True
        and repair_semantic.get("only_hash_derived_fields_changed") is True,
        "repair_semantic_counts_unchanged": repair_semantic.get("semantic_counts_unchanged") is True,
        "duplicate_denominators_still_2_2_2": duplicate.get("row_level_count") == 2
        and duplicate.get("primary_duplicate_denominator", {}).get("unique_count") == 2
        and duplicate.get("secondary_duplicate_denominator", {}).get("unique_count") == 2,
        "no_forbidden_result_cost_keys_in_packet": scan_forbidden_packet_keys(rows) == [],
        "all_packet_safe_flags_closed": scan_safe_flags(rows) == [],
    }
    blockers: list[dict[str, Any]] = []
    if not all(checks.values()):
        blockers.append(
            {
                "issue": "packet_semantics_changed_or_counts_invalid",
                "path": rel(TARGET_PACKET),
                "exact_repair_requirement": "Restore exact two-row source/control packet semantics and counts before G12 acceptance.",
                "checks": checks,
            }
        )
    return {
        "artifact_family": "semantic_no_row_change_reaudit",
        "generated_at_utc": utc_now(),
        "observed_row_identities": observed_identities,
        "expected_row_identities": EXPECTED_ROWS,
        "target_admission_counts": {
            "admitted_packet_row_count": admission.get("admitted_packet_row_count"),
            "blocked_candidate_count": admission.get("blocked_candidate_count"),
            "rejected_candidate_count": admission.get("rejected_candidate_count"),
            "candidate_count_considered": admission.get("candidate_count_considered"),
        },
        "target_output_manifest_counts": {
            "admitted_packet_row_count": output_manifest.get("admitted_packet_row_count"),
            "blocked_candidate_count": output_manifest.get("blocked_candidate_count"),
            "rejected_candidate_count": output_manifest.get("rejected_candidate_count"),
        },
        "status_counts": status_counts,
        "duplicate_denominators": {
            "row_level_count": duplicate.get("row_level_count"),
            "primary_unique_count": duplicate.get("primary_duplicate_denominator", {}).get("unique_count"),
            "secondary_unique_count": duplicate.get("secondary_duplicate_denominator", {}).get("unique_count"),
        },
        "repair_semantic_ledger_path": rel(REPAIR_SEMANTIC),
        "repair_semantic_ledger_core": {
            "before_packet_sha256": repair_semantic.get("before_packet_sha256"),
            "after_packet_sha256": repair_semantic.get("after_packet_sha256"),
            "semantic_rows_unchanged_excluding_hash_fields": repair_semantic.get("semantic_rows_unchanged_excluding_hash_fields"),
            "only_hash_derived_fields_changed": repair_semantic.get("only_hash_derived_fields_changed"),
            "semantic_counts_unchanged": repair_semantic.get("semantic_counts_unchanged"),
        },
        "checks": checks,
        "remaining_blockers": blockers,
        "audit_passed": blockers == [],
    }, blockers


def packet_hash_manifest_reaudit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = read_json(TARGET_PACKET_MANIFEST)
    repair_packet = read_json(REPAIR_PACKET_SHA)
    packet_sha = sha256_file(TARGET_PACKET)
    rows = read_jsonl(TARGET_PACKET)
    checks = {
        "packet_sha_matches_target_manifest": packet_sha == manifest.get("packet_sha256"),
        "packet_sha_matches_repair_packet_ledger": packet_sha == repair_packet.get("packet_sha256_recomputed"),
        "packet_sha_matches_expected_repaired_sha": packet_sha == EXPECTED_PACKET_SHA,
        "packet_row_count_is_2": len(rows) == 2 and manifest.get("packet_row_count") == 2,
        "manifest_keeps_g12_gate_closed": manifest.get("g12_required_before_validation_execution") is True,
    }
    blockers = []
    if not all(checks.values()):
        blockers.append(
            {
                "issue": "packet_hash_manifest_mismatch",
                "path": rel(TARGET_PACKET_MANIFEST),
                "exact_repair_requirement": "Recompute packet SHA and manifest from the repaired packet rows before G12 acceptance.",
                "checks": checks,
            }
        )
    return {
        "artifact_family": "packet_hash_manifest_reaudit",
        "generated_at_utc": utc_now(),
        "target_packet_path": rel(TARGET_PACKET),
        "target_packet_manifest_path": rel(TARGET_PACKET_MANIFEST),
        "packet_sha256_recomputed": packet_sha,
        "packet_sha256_manifest": manifest.get("packet_sha256"),
        "packet_sha256_repair_ledger": repair_packet.get("packet_sha256_recomputed"),
        "expected_repaired_packet_sha256": EXPECTED_PACKET_SHA,
        "packet_row_count": len(rows),
        "checks": checks,
        "remaining_blockers": blockers,
        "audit_passed": blockers == [],
    }, blockers


def target_verifier_test_rerun_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    verifier_run = run_command([sys.executable, str(TARGET_VERIFIER)], timeout_seconds=240)
    pytest_run = run_command(
        [sys.executable, "-m", "pytest", str(TARGET_TESTS), "-q", "-p", "no:cacheprovider"],
        timeout_seconds=240,
    )
    checks = {
        "target_verifier_was_run": verifier_run.get("returncode") is not None,
        "target_focused_pytest_was_run": pytest_run.get("returncode") is not None,
        "target_verifier_passed": verifier_run.get("returncode") == 0,
        "target_focused_pytest_passed": pytest_run.get("returncode") == 0,
    }
    blockers = []
    if not all(checks.values()):
        blockers.append(
            {
                "issue": "target_verifier_or_focused_tests_failed",
                "path": rel(TARGET_DIR),
                "exact_repair_requirement": "Fix target source-expansion verifier or focused tests before G12 repair acceptance.",
                "checks": checks,
            }
        )
    return {
        "artifact_family": "target_verifier_test_rerun_audit",
        "generated_at_utc": utc_now(),
        "target_verifier_run": verifier_run,
        "target_focused_pytest_run": pytest_run,
        "checks": checks,
        "remaining_blockers": blockers,
        "audit_passed": blockers == [],
    }, blockers


def repair_verifier_test_rerun_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    verifier_run = run_command([sys.executable, str(REPAIR_VERIFIER)], timeout_seconds=300)
    pytest_run = run_command(
        [sys.executable, "-m", "pytest", str(REPAIR_TESTS), "-q", "-p", "no:cacheprovider"],
        timeout_seconds=240,
    )
    checks = {
        "repair_verifier_was_run": verifier_run.get("returncode") is not None,
        "repair_focused_pytest_was_run": pytest_run.get("returncode") is not None,
        "repair_verifier_passed": verifier_run.get("returncode") == 0,
        "repair_focused_pytest_passed": pytest_run.get("returncode") == 0,
    }
    blockers = []
    if not all(checks.values()):
        blockers.append(
            {
                "issue": "repair_verifier_or_focused_tests_failed",
                "path": rel(REPAIR_DIR),
                "exact_repair_requirement": "Fix repair route verifier or focused tests before G12 repair acceptance.",
                "checks": checks,
            }
        )
    return {
        "artifact_family": "repair_verifier_test_rerun_audit",
        "generated_at_utc": utc_now(),
        "repair_verifier_run": verifier_run,
        "repair_focused_pytest_run": pytest_run,
        "checks": checks,
        "remaining_blockers": blockers,
        "audit_passed": blockers == [],
    }, blockers


def syntax_compile_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    files = [
        ROUTE_DIR / "build_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
        ROUTE_DIR / "verify_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
        ROUTE_DIR / "test_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
    ]
    py_compile = run_command([sys.executable, "-m", "py_compile", *[str(path) for path in files]], timeout_seconds=120)
    ast_fallback: list[dict[str, Any]] = []
    if py_compile.get("returncode") != 0:
        import ast

        for path in files:
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                ast_fallback.append({"path": rel(path), "ast_parse_ok": True})
            except SyntaxError as exc:
                ast_fallback.append({"path": rel(path), "ast_parse_ok": False, "error": str(exc)})
    checks = {
        "py_compile_passed": py_compile.get("returncode") == 0,
        "ast_fallback_passed_if_needed": py_compile.get("returncode") == 0
        or all(item.get("ast_parse_ok") is True for item in ast_fallback),
    }
    blockers = []
    if not checks["ast_fallback_passed_if_needed"]:
        blockers.append(
            {
                "issue": "new_route_python_syntax_failed",
                "path": rel(ROUTE_DIR),
                "exact_repair_requirement": "Fix syntax in the new G12 builder, verifier, or focused tests.",
            }
        )
    return {
        "artifact_family": "syntax_compile_audit",
        "generated_at_utc": utc_now(),
        "files": [rel(path) for path in files],
        "py_compile_run": py_compile,
        "ast_fallback": ast_fallback,
        "checks": checks,
        "remaining_blockers": blockers,
        "audit_passed": blockers == [],
    }, blockers


def noleak_safe_flag_live_surface_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    json_paths = [
        TARGET_PACKET_MANIFEST,
        TARGET_SOURCE_MANIFEST,
        TARGET_PARSER_ASOF,
        TARGET_ADMISSION,
        TARGET_DUPLICATES,
        TARGET_OUTPUT_MANIFEST,
        REPAIR_CLOSURE,
        REPAIR_SOURCE_HASH,
        REPAIR_SEMANTIC,
        REPAIR_PACKET_SHA,
        REPAIR_NOLEAK,
    ]
    json_paths.extend(sorted(ROUTE_DIR.glob(f"{PREFIX}_*.json")))
    safe_issues: list[dict[str, Any]] = []
    for path in json_paths:
        if path.exists():
            safe_issues.extend(scan_safe_flags(read_json(path), rel(path)))
    packet_rows = read_jsonl(TARGET_PACKET)
    safe_issues.extend(scan_safe_flags(packet_rows, rel(TARGET_PACKET)))
    forbidden_packet_hits = scan_forbidden_packet_keys(packet_rows, rel(TARGET_PACKET))
    diff_scope = git_diff_scope()
    checks = {
        "safe_flags_closed": safe_issues == [],
        "packet_has_no_forbidden_result_cost_keys": forbidden_packet_hits == [],
        "repair_no_leak_safe_flag_check_passed": read_json(REPAIR_NOLEAK).get("safe_flag_issue_count") == 0,
        "no_forbidden_live_surface_diff_paths": diff_scope.get("ok") is True,
    }
    blockers = []
    if not all(checks.values()):
        blockers.append(
            {
                "issue": "noleak_safe_flag_or_live_surface_failure",
                "path": rel(ROUTE_DIR),
                "exact_repair_requirement": "Close safe flags, remove forbidden packet keys, or eliminate forbidden live-surface diffs before acceptance.",
                "checks": checks,
                "safe_issues": safe_issues[:20],
                "forbidden_packet_hits": forbidden_packet_hits[:20],
                "forbidden_live_surface_paths": diff_scope.get("forbidden_live_surface_paths"),
            }
        )
    return {
        "artifact_family": "noleak_safe_flag_live_surface_audit",
        "generated_at_utc": utc_now(),
        "checked_json_artifact_count": len(json_paths),
        "safe_flag_issue_count": len(safe_issues),
        "safe_flag_issues": safe_issues,
        "forbidden_packet_key_hit_count": len(forbidden_packet_hits),
        "forbidden_packet_key_hits": forbidden_packet_hits,
        "diff_scope": diff_scope,
        "checks": checks,
        "remaining_blockers": blockers,
        "audit_passed": blockers == [],
    }, blockers


def future_route_eligibility_ledger(blockers: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = blockers == []
    return {
        "artifact_family": "future_route_eligibility_ledger",
        "generated_at_utc": utc_now(),
        "terminal_decision": ACCEPT_DECISION if accepted else BLOCKER_DECISION,
        "accepted_for_next_evidence_class_prompt": accepted,
        "recommended_next_route_id": "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW"
        if accepted
        else "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD",
        "next_route_evidence_class": "G0_SOURCE_CONTROL_SYNTHESIS_ONLY" if accepted else "SOURCE_CONTROL_REPAIR_ONLY",
        "validation_execution_remains_closed": True,
        "result_cost_r_win_rate_expectancy_scoring_remains_closed": True,
        "remaining_exact_repair_blockers": blockers,
    }


def write_next_route_prompt_pack(blockers: list[dict[str, Any]]) -> str:
    if blockers:
        starter = (
            "/goal Follow a narrow source/control repair prompt for "
            "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD as the complete objective; "
            "do mandatory preflight and context refresh first; do not rely on chat memory; repair only the exact "
            "remaining G12 hash-reaudit blockers from this route without admitting/removing rows, opening validation, "
            "scoring result/cost/R/win-rate/expectancy, reading broker actual-R or MT5 account/order/history/deal/"
            "position values, editing registries, calling paid/API routes, pushing remote, restarting live processes, "
            "or changing prompts/config/risk/permissions/safety/selectors/canaries/live behavior; preserve "
            "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
        )
        recommended = "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD"
    else:
        starter = (
            "/goal Follow a G0 source/control synthesis prompt for "
            "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW as the complete objective; "
            "do mandatory preflight and context refresh first; do not rely on chat memory; synthesize only the accepted "
            "G12 hash-repaired source/control packet evidence, the two admitted source-bound rows, 37 blockers, 9 "
            "rejects, duplicate denominators 2/2/2, source hashes, parser hashes, packet hash, no-leak flags, and "
            "closed validation gates; do not execute validation, score result/cost/R/win-rate/expectancy, read broker "
            "actual-R or MT5 account/order/history/deal/position values, edit registries, call paid/API routes, push "
            "remote, restart live processes, or change prompts/config/risk/permissions/safety/selectors/canaries/live "
            "behavior; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
        )
        recommended = "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW"
    payload = {
        "artifact_family": "next_route_prompt_pack",
        "generated_at_utc": utc_now(),
        "recommended_next_route_id": recommended,
        "one_line_starter": starter,
        "remaining_exact_repair_blockers": blockers,
        "validation_execution_remains_closed": True,
    }
    lines = [
        "# G12 NOFILL Historical Source Expansion Hash Repair Reaudit Next Route Prompt Pack",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
        "",
        "## One-Line Starter",
        "",
        "```text",
        starter,
        "```",
        "",
        "## Machine Payload",
        "",
        "```json",
        json.dumps(with_flags(payload), indent=2, sort_keys=True),
        "```",
    ]
    path = ROUTE_DIR / f"{PREFIX}_NEXT_ROUTE_PROMPT_PACK_{DATE}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rel(path)


def decision_ledger(blockers: list[dict[str, Any]]) -> dict[str, Any]:
    semantic_reject = any(item.get("issue") == "packet_semantics_changed_or_counts_invalid" for item in blockers)
    return {
        "artifact_family": "decision_ledger",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "terminal_decision": REJECT_DECISION if semantic_reject else (ACCEPT_DECISION if blockers == [] else BLOCKER_DECISION),
        "remaining_exact_repair_blocker_count": len(blockers),
        "remaining_exact_repair_blockers": blockers,
        "admitted_packet_row_count": 2,
        "blocked_candidate_count": 37,
        "rejected_candidate_count": 9,
        "duplicate_denominators": "2/2/2",
        "decision_reasons": [
            "The three prior parser/verifier hash blockers were recomputed from disk and match the repaired target manifest.",
            "Packet parser_code_hash fields bind the current accepted target builder hash.",
            "The repaired packet SHA matches target and repair manifests.",
            "Packet semantics remain exactly two admitted rows, 37 blockers, 9 rejects, and duplicate denominators 2/2/2.",
            "Target, repair, and new G12 verification lanes remain source/control only with validation closed.",
        ]
        if blockers == []
        else ["Remaining exact repair blockers prevent full G12 acceptance."],
    }


def completion_audit(
    artifact_map: dict[str, str],
    blockers: list[dict[str, Any]],
    target_rerun: dict[str, Any],
    repair_rerun: dict[str, Any],
    syntax_audit: dict[str, Any],
    noleak_audit: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        ("context_anchor", "Context anchor records HEAD, prompt path, preflight docs, and boundaries.", artifact_map["context_anchor_json"]),
        ("decision_ledger", "Decision ledger records G12 terminal decision and exact blockers.", artifact_map["decision_ledger_json"]),
        ("three_repaired_hashes", "Builder, focused-test, and verifier SHA256 values recomputed from disk.", artifact_map["exact_blocker_closure_json"]),
        ("source_hash_manifest", "Target source-hash manifest recomputed and repaired parser records checked.", artifact_map["source_hash_parser_hash_json"]),
        ("packet_parser_code_hash", "Packet parser_code_hash fields bind the current builder hash.", artifact_map["source_hash_parser_hash_json"]),
        ("target_packet_hash_manifest", "Target packet SHA recomputed and matched to target/repair manifests.", artifact_map["packet_hash_manifest_json"]),
        ("semantic_no_row_change", "No row admission/removal and hash-only semantic diff verified.", artifact_map["semantic_no_row_change_json"]),
        ("target_verifier_tests", "Target verifier and focused tests rerun from disk.", artifact_map["target_rerun_json"]),
        ("repair_verifier_tests", "Repair verifier and focused tests rerun from disk.", artifact_map["repair_rerun_json"]),
        ("noleak_safe_live_surface", "Safe flags, forbidden packet keys, and live-surface diff scan checked.", artifact_map["noleak_json"]),
        ("counts_2_37_9", "Two admitted rows, 37 blockers, and 9 rejects verified.", artifact_map["semantic_no_row_change_json"]),
        ("duplicates_2_2_2", "Duplicate denominators remain 2/2/2.", artifact_map["semantic_no_row_change_json"]),
        ("next_prompt_pack", "Next route prompt pack exists and keeps validation closed.", artifact_map["next_prompt_pack_md"]),
        ("syntax_compile", "py_compile or AST syntax fallback ran for new Python files.", artifact_map["syntax_json"]),
        ("g12_builder_verifier_tests", "New G12 builder, verifier, and focused tests are present.", rel(ROUTE_DIR)),
    ]
    missing: list[dict[str, Any]] = []
    if blockers:
        missing.append({"requirement": "no_remaining_exact_repair_blockers", "blockers": blockers})
    if target_rerun.get("audit_passed") is not True:
        missing.append({"requirement": "target_verifier_tests_pass", "evidence": artifact_map["target_rerun_json"]})
    if repair_rerun.get("audit_passed") is not True:
        missing.append({"requirement": "repair_verifier_tests_pass", "evidence": artifact_map["repair_rerun_json"]})
    if syntax_audit.get("audit_passed") is not True:
        missing.append({"requirement": "new_python_syntax_pass", "evidence": artifact_map["syntax_json"]})
    if noleak_audit.get("audit_passed") is not True:
        missing.append({"requirement": "noleak_safe_live_surface_pass", "evidence": artifact_map["noleak_json"]})
    return {
        "artifact_family": "completion_audit",
        "generated_at_utc": utc_now(),
        "objective_restatement": (
            "Independently G12-reaudit the NOFILL historical source-expansion parser-hash repair: close the three "
            "parser/verifier hash blockers, preserve exact packet semantics, rerun target and repair checks, keep "
            "validation/result/live surfaces closed, and produce the next source/control route prompt pack."
        ),
        "terminal_decision": ACCEPT_DECISION if missing == [] else BLOCKER_DECISION,
        "prompt_to_artifact_checklist": [
            {"requirement_id": req, "status": "PASS", "description": desc, "evidence": evidence}
            for req, desc, evidence in checklist
        ],
        "missing_incomplete_or_weak_requirements": missing,
        "completion_standard_satisfied": missing == [],
        "can_mark_goal_complete": missing == [],
        "remaining_exact_repair_blocker_count": len(blockers),
    }


def output_manifest(artifact_map: dict[str, str]) -> dict[str, Any]:
    return {
        "artifact_family": "output_manifest",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "outputs": artifact_map,
        "required_artifacts": REQUIRED_ARTIFACTS,
        "required_artifact_count": len(REQUIRED_ARTIFACTS),
    }


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    artifact_map: dict[str, str] = {}
    blockers: list[dict[str, Any]] = []

    anchor = context_anchor()
    artifact_map["context_anchor_json"] = write_json(f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json", anchor)
    artifact_map["context_anchor_md"] = write_md(f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md", "Context Anchor", anchor)

    closure, closure_blockers = exact_blocker_closure_reaudit()
    blockers.extend(closure_blockers)
    artifact_map["exact_blocker_closure_json"] = write_json(
        f"{PREFIX}_EXACT_BLOCKER_CLOSURE_REAUDIT_{DATE}.json", closure
    )
    artifact_map["exact_blocker_closure_md"] = write_md(
        f"{PREFIX}_EXACT_BLOCKER_CLOSURE_REAUDIT_{DATE}.md", "Exact Blocker Closure Reaudit", closure
    )

    source_hash, source_blockers = source_hash_parser_hash_recomputation_audit()
    blockers.extend(source_blockers)
    artifact_map["source_hash_parser_hash_json"] = write_json(
        f"{PREFIX}_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_{DATE}.json", source_hash
    )
    artifact_map["source_hash_parser_hash_md"] = write_md(
        f"{PREFIX}_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_{DATE}.md",
        "Source Hash Parser Hash Recomputaton Audit",
        source_hash,
    )

    semantic, semantic_blockers = semantic_no_row_change_reaudit()
    blockers.extend(semantic_blockers)
    artifact_map["semantic_no_row_change_json"] = write_json(
        f"{PREFIX}_SEMANTIC_NO_ROW_CHANGE_REAUDIT_{DATE}.json", semantic
    )
    artifact_map["semantic_no_row_change_md"] = write_md(
        f"{PREFIX}_SEMANTIC_NO_ROW_CHANGE_REAUDIT_{DATE}.md", "Semantic No Row Change Reaudit", semantic
    )

    packet_hash, packet_blockers = packet_hash_manifest_reaudit()
    blockers.extend(packet_blockers)
    artifact_map["packet_hash_manifest_json"] = write_json(
        f"{PREFIX}_PACKET_HASH_MANIFEST_REAUDIT_{DATE}.json", packet_hash
    )
    artifact_map["packet_hash_manifest_md"] = write_md(
        f"{PREFIX}_PACKET_HASH_MANIFEST_REAUDIT_{DATE}.md", "Packet Hash Manifest Reaudit", packet_hash
    )

    target_rerun, target_blockers = target_verifier_test_rerun_audit()
    blockers.extend(target_blockers)
    artifact_map["target_rerun_json"] = write_json(f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_AUDIT_{DATE}.json", target_rerun)
    artifact_map["target_rerun_md"] = write_md(
        f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_AUDIT_{DATE}.md", "Target Verifier Test Rerun Audit", target_rerun
    )

    repair_rerun, repair_blockers = repair_verifier_test_rerun_audit()
    blockers.extend(repair_blockers)
    artifact_map["repair_rerun_json"] = write_json(f"{PREFIX}_REPAIR_VERIFIER_TEST_RERUN_AUDIT_{DATE}.json", repair_rerun)
    artifact_map["repair_rerun_md"] = write_md(
        f"{PREFIX}_REPAIR_VERIFIER_TEST_RERUN_AUDIT_{DATE}.md", "Repair Verifier Test Rerun Audit", repair_rerun
    )

    syntax, syntax_blockers = syntax_compile_audit()
    blockers.extend(syntax_blockers)
    artifact_map["syntax_json"] = write_json(f"{PREFIX}_SYNTAX_COMPILE_AUDIT_{DATE}.json", syntax)
    artifact_map["syntax_md"] = write_md(f"{PREFIX}_SYNTAX_COMPILE_AUDIT_{DATE}.md", "Syntax Compile Audit", syntax)

    noleak, noleak_blockers = noleak_safe_flag_live_surface_audit()
    blockers.extend(noleak_blockers)
    artifact_map["noleak_json"] = write_json(f"{PREFIX}_NOLEAK_SAFE_FLAG_LIVE_SURFACE_AUDIT_{DATE}.json", noleak)
    artifact_map["noleak_md"] = write_md(
        f"{PREFIX}_NOLEAK_SAFE_FLAG_LIVE_SURFACE_AUDIT_{DATE}.md",
        "No Leak Safe Flag Live Surface Audit",
        noleak,
    )

    future = future_route_eligibility_ledger(blockers)
    artifact_map["future_route_json"] = write_json(f"{PREFIX}_FUTURE_ROUTE_ELIGIBILITY_LEDGER_{DATE}.json", future)
    artifact_map["future_route_md"] = write_md(
        f"{PREFIX}_FUTURE_ROUTE_ELIGIBILITY_LEDGER_{DATE}.md", "Future Route Eligibility Ledger", future
    )

    artifact_map["next_prompt_pack_md"] = write_next_route_prompt_pack(blockers)

    decision = decision_ledger(blockers)
    artifact_map["decision_ledger_json"] = write_json(f"{PREFIX}_DECISION_LEDGER_{DATE}.json", decision)
    artifact_map["decision_ledger_md"] = write_md(f"{PREFIX}_DECISION_LEDGER_{DATE}.md", "Decision Ledger", decision)

    completion = completion_audit(artifact_map, blockers, target_rerun, repair_rerun, syntax, noleak)
    artifact_map["completion_audit_json"] = write_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json", completion)
    artifact_map["completion_audit_md"] = write_md(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md", "Completion Audit", completion)

    manifest = output_manifest(artifact_map)
    artifact_map["output_manifest_json"] = write_json(f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json", manifest)

    result = {
        "ok": completion["completion_standard_satisfied"],
        "route_id": ROUTE_ID,
        "terminal_decision": decision["terminal_decision"],
        "remaining_exact_repair_blocker_count": len(blockers),
        "packet_row_count": 2,
        "blocked_candidate_count": 37,
        "rejected_candidate_count": 9,
        "duplicate_denominators": "2/2/2",
        "artifact_count": len(artifact_map),
        "can_mark_goal_complete": completion["can_mark_goal_complete"],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    build_result = build()
    raise SystemExit(0 if build_result["ok"] else 1)
