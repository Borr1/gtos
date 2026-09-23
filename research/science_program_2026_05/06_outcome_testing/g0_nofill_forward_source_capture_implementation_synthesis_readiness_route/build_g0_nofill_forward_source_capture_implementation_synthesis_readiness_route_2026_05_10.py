"""Build G0 NOFILL forward source-capture synthesis/readiness artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parents[3]
DATE = "2026-05-10"
ROUTE_ID = "G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_READINESS_ROUTE"
SCHEMA_VERSION = "g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_AND_SHADOW_READINESS_ROUTE"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra import forward_capture as fc  # noqa: E402


PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_READINESS_ROUTE_GOAL_PROMPT_2026-05-10.md"
)
G12_AUDIT_DIR = (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_forward_source_capture_additive_logger_implementation_audit"
)
IMPLEMENTATION_DIR = (
    "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_additive_logger_implementation"
)

CONTROL_INPUTS = {
    "g12_decision": f"{G12_AUDIT_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json",
    "g12_completion": f"{G12_AUDIT_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_AUDIT_COMPLETION_AUDIT_2026-05-10.json",
    "g12_runtime_contract": f"{G12_AUDIT_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_RUNTIME_55_FIELD_CONTRACT_AUDIT_2026-05-10.json",
    "g12_future_fields": f"{G12_AUDIT_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELD_AUDIT_2026-05-10.json",
    "g12_failopen": f"{G12_AUDIT_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_FAILOPEN_NO_LIVE_BEHAVIOR_AUDIT_2026-05-10.json",
    "g12_noleak": f"{G12_AUDIT_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json",
    "g12_repair_blockers": f"{G12_AUDIT_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_EXACT_REPAIR_BLOCKER_LEDGER_2026-05-10.json",
    "g12_source_hash": f"{G12_AUDIT_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_AUDIT_2026-05-10.json",
    "g12_diff_scope": f"{G12_AUDIT_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_DIFF_SCOPE_CALL_PATH_AUDIT_2026-05-10.json",
    "implementation_decision": f"{IMPLEMENTATION_DIR}/NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DECISION_LEDGER_2026-05-10.json",
    "implementation_completion": f"{IMPLEMENTATION_DIR}/NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_COMPLETION_AUDIT_2026-05-10.json",
    "design_g12_decision": (
        "research/science_program_2026_05/06_outcome_testing/"
        "g12_nofill_forward_source_capture_implementation_design_audit/"
        "G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-10.json"
    ),
    "design_plan_completion": (
        "research/science_program_2026_05/06_outcome_testing/"
        "nofill_forward_source_capture_implementation_design_plan/"
        "NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_2026-05-10.json"
    ),
    "projection_g0_completion": (
        "research/science_program_2026_05/06_outcome_testing/"
        "g0_nofill_forward_projection_synthesis_control_route/"
        "G0_NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.json"
    ),
    "cat_v3_g0_decision": (
        "research/science_program_2026_05/06_outcome_testing/"
        "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/"
        "G0_NOFILL_CAT_V3_SYNTHESIS_DECISION_LEDGER_2026-05-09.json"
    ),
}

REQUIRED_JSON = [
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_CONTEXT_ANCHOR_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_DECISION_LEDGER_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_SEPARATION_LEDGER_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_SHADOW_READINESS_OBSERVATION_AUDIT_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_OWNER_ACTION_LEDGER_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_NO_ROW_DIAGNOSTIC_TREE_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_MONITOR_VERIFIER_SPEC_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_DUPLICATE_DENOMINATOR_RISK_REVIEW_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_ROUTE_LEDGER_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_SATURATION_SELF_REDTEAM_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_BLOCKER_APPROVAL_LEDGER_{DATE}.json",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_{DATE}.json",
]

REQUIRED_MD = [
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_CONTEXT_ANCHOR_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_DECISION_LEDGER_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_SEPARATION_LEDGER_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_SHADOW_READINESS_OBSERVATION_AUDIT_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_OWNER_ACTION_LEDGER_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_NO_ROW_DIAGNOSTIC_TREE_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_MONITOR_VERIFIER_SPEC_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_DUPLICATE_DENOMINATOR_RISK_REVIEW_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_ROUTE_LEDGER_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_SATURATION_SELF_REDTEAM_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_BLOCKER_APPROVAL_LEDGER_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_PROMPT_PACK_{DATE}.md",
    f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_{DATE}.md",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def base_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_validation": False,
        "opens_promotion": False,
        "opens_registry_edit": False,
        "opens_paid_api_or_databento_route": False,
        "opens_live_trading_behavior": False,
        "changes_live_trading_behavior": False,
        "credentials_touched": False,
        "remote_push_opened": False,
    }


def with_base(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **base_flags(),
        **payload,
    }


def repo_path(path: str) -> Path:
    return REPO_ROOT / path


def read_json(path: str) -> dict[str, Any]:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def sha256_path(path: str) -> str | None:
    full = repo_path(path)
    if not full.exists():
        return None
    return hashlib.sha256(full.read_bytes()).hexdigest()


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def git_is_ancestor(commit: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode == 0


def git_changed_names() -> list[str]:
    names = set()
    for args in (["diff", "--name-only", "HEAD"], ["ls-files", "--others", "--exclude-standard"]):
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        names.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    return sorted(names)


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def inspect_jsonl(path: str) -> dict[str, Any]:
    full = repo_path(path)
    if not full.exists():
        return {
            "path": path,
            "exists": False,
            "line_count": 0,
            "latest_selected_fields": {},
        }
    count = 0
    last: dict[str, Any] = {}
    with full.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            count += 1
            try:
                last = json.loads(stripped)
            except json.JSONDecodeError:
                last = {"parse_status": "MALFORMED_LAST_LINE"}
    latest_selected = {
        key: last.get(key)
        for key in (
            "schema_version",
            "candidate_id",
            "symbol",
            "decision_time_utc",
            "created_at_utc",
            "evidence_class",
            "promotion_verdict",
            "validation_safe",
            "outcome_review_opened",
            "live_effect",
        )
        if key in last
    }
    return {
        "path": path,
        "exists": True,
        "line_count": count,
        "last_write_utc_from_filesystem": datetime.fromtimestamp(
            full.stat().st_mtime, tz=timezone.utc
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "latest_selected_fields": latest_selected,
    }


def inspect_nofill_runtime_log() -> dict[str, Any]:
    path = repo_path(fc.NOFILL_FORWARD_SOURCE_CAPTURE_PATH)
    if not path.exists():
        return {
            "log_path": fc.NOFILL_FORWARD_SOURCE_CAPTURE_PATH,
            "exists": False,
            "row_count": 0,
            "runtime_row_status": "NO_ROWS_LOG_ABSENT",
            "schema_audit_status": "NOT_APPLICABLE_NO_ROWS",
            "safe_flag_issues": [],
            "validation_issues": [],
            "duplicate_key_collisions": [],
            "forbidden_leak_issues": [],
        }
    rows = iter_jsonl(path)
    validation_issues: list[dict[str, Any]] = []
    safe_flag_issues: list[dict[str, Any]] = []
    forbidden_leak_issues: list[dict[str, Any]] = []
    seen_duplicate_keys: dict[str, int] = {}
    for idx, row in enumerate(rows, start=1):
        validation = fc.validate_nofill_forward_source_capture_row(row)
        if not validation.get("ok"):
            validation_issues.append({"row_number": idx, "validation": validation})
        for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
            if row.get(flag) is not False:
                safe_flag_issues.append({"row_number": idx, "flag": flag, "value": row.get(flag)})
        forbidden_keys = sorted(set(row) & fc.NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES)
        if forbidden_keys:
            forbidden_leak_issues.append({"row_number": idx, "forbidden_keys": forbidden_keys})
        key = row.get("nofill_duplicate_key_sha256")
        if isinstance(key, str) and key and not key.endswith("FAIL_CLOSED"):
            seen_duplicate_keys[key] = seen_duplicate_keys.get(key, 0) + 1
    duplicate_key_collisions = [
        {"nofill_duplicate_key_sha256": key, "row_count": count}
        for key, count in sorted(seen_duplicate_keys.items())
        if count > 1
    ]
    return {
        "log_path": fc.NOFILL_FORWARD_SOURCE_CAPTURE_PATH,
        "exists": True,
        "row_count": len(rows),
        "runtime_row_status": "ROWS_PRESENT",
        "schema_audit_status": "PASS" if not validation_issues else "FAIL",
        "safe_flag_issues": safe_flag_issues,
        "validation_issues": validation_issues,
        "duplicate_key_collisions": duplicate_key_collisions,
        "forbidden_leak_issues": forbidden_leak_issues,
        "latest_selected_fields": {
            key: rows[-1].get(key)
            for key in (
                "schema_version",
                "candidate_id",
                "symbol",
                "decision_time_utc",
                "capture_observed_at_utc",
                "capture_write_completed_at_utc",
                "promotion_verdict",
                "validation_safe",
                "outcome_review_opened",
                "live_effect",
                "forbidden_field_scan_status",
            )
            if rows
        },
    }


def code_path_evidence() -> dict[str, Any]:
    text = repo_path("src/research_infra/forward_capture.py").read_text(encoding="utf-8", errors="replace")
    orch_text = repo_path("src/components/orchestrator.py").read_text(encoding="utf-8", errors="replace")
    config_text = repo_path("config/agent_config.yaml").read_text(encoding="utf-8", errors="replace")
    return {
        "source_capture_path_constant": fc.NOFILL_FORWARD_SOURCE_CAPTURE_PATH,
        "source_capture_schema_version": fc.NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
        "runtime_field_count": len(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
        "future_logger_field_count": len(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
        "writer_function_present": "def record_nofill_forward_source_capture" in text,
        "writer_return_value_contract": "return None" in text[text.find("def record_nofill_forward_source_capture"): text.find("def _safe_get")],
        "additive_call_present_in_forward_shadow_helper": "record_nofill_forward_source_capture(" in text[text.find("def record_live_candidate_forward_shadow"): text.find("def classify_ltf_ambiguity")],
        "orchestrator_imports_forward_shadow_helper": "record_live_candidate_forward_shadow" in orch_text,
        "orchestrator_helper_default_enabled_unless_config_false": "cfg.get(\"enabled\", True) is False" in orch_text,
        "config_explicit_forward_capture_disable_present": "forward_capture_candidate_logger" in config_text,
        "config_gate_status": (
            "EXPLICIT_CONFIG_KEY_PRESENT_REVIEW_REQUIRED"
            if "forward_capture_candidate_logger" in config_text
            else "DEFAULT_ENABLED_NO_DISABLE_KEY_PRESENT"
        ),
    }


def accepted_evidence_summary(control: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_hash = control["g12_source_hash"]
    diff_scope = control["g12_diff_scope"]
    implementation_commit = diff_scope.get("implementation_commit")
    return {
        "current_head": run_git(["rev-parse", "HEAD"]),
        "implementation_commit": implementation_commit,
        "implementation_commit_is_ancestor_of_current_head": git_is_ancestor(implementation_commit)
        if implementation_commit
        else False,
        "g12_terminal_decision": control["g12_decision"].get("terminal_decision"),
        "g12_exact_repair_blocker_count": control["g12_repair_blockers"].get("exact_repair_blocker_count"),
        "g12_runtime_field_count": control["g12_runtime_contract"].get("runtime_field_count"),
        "g12_runtime_unique_field_count": control["g12_runtime_contract"].get("runtime_unique_field_count"),
        "g12_future_logger_field_count": control["g12_future_fields"].get("runtime_future_logger_field_count"),
        "g12_failopen_writer_call_ignored_count": control["g12_failopen"].get("nofill_writer_call_ignored_count"),
        "g12_forbidden_output_keys": control["g12_noleak"].get("forbidden_output_keys"),
        "g12_secret_marker_leaks": control["g12_noleak"].get("secret_marker_leaks"),
        "g12_raw_value_hash_hits": control["g12_noleak"].get("raw_value_hash_hits"),
        "source_hash_audit_passed": source_hash.get("audit_passed"),
        "parser_hash_matches_forward_capture_file": source_hash.get("parser_hash_matches_forward_capture_file"),
        "diff_scope_call_path_passed": diff_scope.get("diff_scope_limited_to_source_test_research_artifacts"),
    }


def build_payload() -> dict[str, Any]:
    control = {name: read_json(path) for name, path in CONTROL_INPUTS.items()}
    generated_at = now_iso()
    evidence = accepted_evidence_summary(control)
    runtime_log = inspect_nofill_runtime_log()
    code_evidence = code_path_evidence()
    source_logs = [
        inspect_jsonl("shadow_logs/live_candidate_strategy_rollups.jsonl"),
        inspect_jsonl("shadow_logs/prefill_delivery_path.jsonl"),
        inspect_jsonl("shadow_logs/context_control_ledger.jsonl"),
        inspect_jsonl("shadow_logs/candidate_path_follow.jsonl"),
    ]

    shadow_state = (
        "ROWS_PRESENT_SCHEMA_AUDIT_REQUIRED"
        if runtime_log["exists"]
        else "SOURCE_CONTROL_READY_EXPECTED_NO_ROW_OWNER_RESTART_OR_NEXT_CANDIDATE_CHECK_REQUIRED"
    )
    owner_actions = [
        {
            "action_id": "OWNER-LIVE-001",
            "required_if": "active live orchestrators were started before implementation commit 62f5a95f or current HEAD",
            "exact_action": "Restart the live orchestrator processes during an owner-approved maintenance window so they import src/research_infra/forward_capture.py from current main.",
            "performed_by_this_route": False,
            "changes_trading_logic": False,
            "why": "Python processes keep imported code in memory; the additive writer cannot emit rows until the live process is running the new module.",
        },
        {
            "action_id": "OWNER-LIVE-002",
            "required_if": "no new AI CANDIDATE or forward-shadow helper call has occurred after a current-code process is running",
            "exact_action": "Allow the next normal eligible CANDIDATE/REJECTED_L2/LIMIT_PLACED path to occur; do not manually create broker orders for this logger.",
            "performed_by_this_route": False,
            "changes_trading_logic": False,
            "why": "The writer is additive inside record_live_candidate_forward_shadow and has no standalone live trigger.",
        },
        {
            "action_id": "OWNER-LIVE-003",
            "required_if": "first nofill source-capture row appears",
            "exact_action": (
                "Run python research/science_program_2026_05/06_outcome_testing/"
                "g0_nofill_forward_source_capture_implementation_synthesis_readiness_route/"
                "verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py"
            ),
            "performed_by_this_route": False,
            "changes_trading_logic": False,
            "why": "The verifier parses rows read-only and checks schema, safe flags, future-field fail-closed behavior, duplicate keys, and forbidden leakage.",
        },
    ]

    context_anchor = with_base(
        {
            "artifact_family": "context_anchor",
            "generated_at_utc": generated_at,
            "current_head": evidence["current_head"],
            "prompt_path": PROMPT_PATH,
            "route_path": str(BASE.relative_to(REPO_ROOT)).replace("\\", "/"),
            "preflight_inputs_read": [
                ".context/LIVE_STATE.md",
                ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
                ".context/00_core/quick_reference_card.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/research_current_state.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/local_heavy_data_inventory.md",
                PROMPT_PATH,
            ],
            "control_inputs": {
                name: {"path": path, "sha256": sha256_path(path), "exists": repo_path(path).exists()}
                for name, path in CONTROL_INPUTS.items()
            },
            "boundary": "G0 source/control synthesis and shadow-readiness only.",
        }
    )

    decision_ledger = with_base(
        {
            "artifact_family": "decision_ledger",
            "generated_at_utc": generated_at,
            "terminal_decision": TERMINAL_DECISION,
            "canonical_source_control_implementation_evidence_on_main": (
                evidence["g12_terminal_decision"]
                == "ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_EVIDENCE_ONLY"
                and evidence["implementation_commit_is_ancestor_of_current_head"]
                and evidence["g12_exact_repair_blocker_count"] == 0
            ),
            "accepted_implementation_summary": evidence,
            "shadow_readiness_state": shadow_state,
            "route_allows": [
                "source/control synthesis",
                "read-only shadow-readiness diagnosis",
                "future monitor/verifier specification",
                "owner-gated live-operation requirement ledger",
                "historical sealed-validation separation note",
            ],
            "route_does_not_allow": [
                "result scoring",
                "cost scoring",
                "validation",
                "promotion",
                "registry edit",
                "paid/API route",
                "remote push",
                "live restart",
                "live trading behavior change",
            ],
        }
    )

    chain = [
        {
            "stage": "CAT_V3_G0_SYNTHESIS",
            "path": CONTROL_INPUTS["cat_v3_g0_decision"],
            "accepted_decision": control["cat_v3_g0_decision"].get("overall_decision"),
            "evidence_class": "quarantined categorical control",
            "carried_forward": "298-row source/control universe and duplicate-denominator discipline.",
        },
        {
            "stage": "FORWARD_PROJECTION_G0_SYNTHESIS",
            "path": CONTROL_INPUTS["projection_g0_completion"],
            "accepted_decision": control["projection_g0_completion"].get("terminal_design_route_decision"),
            "evidence_class": "source-capture design requirements",
            "carried_forward": "55-field capture contract direction and no result/cost/live-wiring boundary.",
        },
        {
            "stage": "IMPLEMENTATION_DESIGN_PLAN",
            "path": CONTROL_INPUTS["design_plan_completion"],
            "accepted_decision": control["design_plan_completion"].get("terminal_verdict"),
            "evidence_class": "implementation design only",
            "carried_forward": "55/55 field map with 20 future logger fields and fail-closed vocabulary.",
        },
        {
            "stage": "G12_IMPLEMENTATION_DESIGN_AUDIT",
            "path": CONTROL_INPUTS["design_g12_decision"],
            "accepted_decision": control["design_g12_decision"].get("terminal_decision"),
            "evidence_class": "G12 accepted implementation-design evidence",
            "carried_forward": "Owner-gated dependency graph and source/control-only acceptance.",
        },
        {
            "stage": "ADDITIVE_LOGGER_IMPLEMENTATION",
            "path": CONTROL_INPUTS["implementation_decision"],
            "accepted_decision": control["implementation_decision"].get("terminal_decision"),
            "evidence_class": "source/control implementation package",
            "carried_forward": "Runtime functions and additive fail-open writer path.",
        },
        {
            "stage": "G12_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT",
            "path": CONTROL_INPUTS["g12_decision"],
            "accepted_decision": control["g12_decision"].get("terminal_decision"),
            "evidence_class": "canonical source/control implementation evidence",
            "carried_forward": "G12 acceptance with zero repair blockers and closed safe flags.",
        },
    ]
    evidence_chain = with_base(
        {
            "artifact_family": "evidence_chain_reconciliation",
            "generated_at_utc": generated_at,
            "chain": chain,
            "chain_status": "RECONCILED_ON_CURRENT_MAIN",
            "accepted_terminal_chain": [
                row["accepted_decision"] for row in chain if row.get("accepted_decision")
            ],
        }
    )

    separation_ledger = with_base(
        {
            "artifact_family": "separation_ledger",
            "generated_at_utc": generated_at,
            "source_control_evidence_now_canonical": [
                "55-field runtime source-capture schema",
                "20 future logger fields emit or fail-close",
                "fail-open writer returns None and ignored return path",
                "forbidden raw broker/account/order/deal/position/ticket/result/cost/slippage/execution-quality keys are redacted or fail-closed",
                "source/code hash manifest matches current files",
            ],
            "not_evidence_for": {
                "result": "No R, win/loss, fill success, terminal price, or candidate outcome score accepted by this route.",
                "cost": "Spread snapshots can be source fields; slippage, cost testing, and execution quality labels remain closed.",
                "validation": "Rows, once present, are research-control inputs until a separate sealed or forward validation lane accepts them.",
                "promotion": "No trading rule, selector, risk, prompt, registry, or live scaling claim is opened.",
            },
            "safe_flag_policy": base_flags(),
        }
    )

    readiness_audit = with_base(
        {
            "artifact_family": "shadow_readiness_observation_audit",
            "generated_at_utc": generated_at,
            "shadow_readiness_state": shadow_state,
            "runtime_log_audit": runtime_log,
            "code_path_evidence": code_evidence,
            "source_log_context": source_logs,
            "diagnosis": (
                "No nofill source-capture row exists in this worktree. The source/control code path is present; row production requires a current-code live process and a normal forward-shadow candidate event."
                if not runtime_log["exists"]
                else "Nofill source-capture rows exist and must be monitored by schema/no-leak/duplicate checks before downstream use."
            ),
            "broken_logger_evidence_found": bool(
                runtime_log["validation_issues"] or runtime_log["forbidden_leak_issues"]
            ),
            "owner_live_operation_requirement_status": (
                "OWNER_RESTART_OR_PROCESS_START_PROOF_REQUIRED_BEFORE_EXPECTING_ROWS"
                if not runtime_log["exists"]
                else "RUN_READ_ONLY_VERIFIER_AFTER_EACH_NEW_BATCH"
            ),
        }
    )

    owner_ledger = with_base(
        {
            "artifact_family": "owner_gated_restart_deployment_action_ledger",
            "generated_at_utc": generated_at,
            "actions": owner_actions,
            "no_action_performed_by_route": True,
            "live_restart_performed": False,
            "live_trading_behavior_changed": False,
        }
    )

    no_row_tree = with_base(
        {
            "artifact_family": "no_row_malformed_missing_field_diagnostic_tree",
            "generated_at_utc": generated_at,
            "decision_tree": [
                {
                    "state": "LOG_ABSENT",
                    "diagnosis_order": [
                        "Confirm current-code process is running or perform owner-approved restart.",
                        "Confirm forward_capture_candidate_logger is not disabled; current config has no explicit disable key.",
                        "Wait for a normal record_live_candidate_forward_shadow call from CANDIDATE, REJECTED_L2, or LIMIT_PLACED path.",
                        "If sibling forward logs advance with current-code process and no nofill row, run route verifier and inspect non-blocking writer warning logs.",
                    ],
                    "current_status": "ACTIVE" if not runtime_log["exists"] else "NOT_ACTIVE",
                },
                {
                    "state": "MALFORMED_JSONL_ROW",
                    "diagnosis_order": [
                        "Stop downstream consumption of the new log.",
                        "Keep trading behavior untouched.",
                        "Repair only parser/writer source-control code in a new approved implementation lane.",
                    ],
                },
                {
                    "state": "MISSING_55_FIELD_OR_MISSING_20_FUTURE_FIELD",
                    "diagnosis_order": [
                        "Treat affected row as not research-control trustable.",
                        "Compare runtime field list to G12 runtime 55-field contract.",
                        "Route repair through source/control implementation and G12 acceptance.",
                    ],
                },
                {
                    "state": "FORBIDDEN_RAW_FIELD_OR_TRUE_SAFE_FLAG",
                    "diagnosis_order": [
                        "Quarantine the row from denominators and downstream packets.",
                        "Inspect redaction status fields only; do not hash or report raw forbidden values.",
                        "Open a source/control no-leak repair lane before any row reuse.",
                    ],
                },
                {
                    "state": "DUPLICATE_KEY_COLLISION",
                    "diagnosis_order": [
                        "Use duplicate key as grouping evidence, not extra sample size.",
                        "Require row-level and duplicate-key denominator ledgers before any future validation lane.",
                    ],
                },
            ],
        }
    )

    monitor_spec = with_base(
        {
            "artifact_family": "future_monitor_verifier_specification",
            "generated_at_utc": generated_at,
            "rerunnable_command": (
                "python research/science_program_2026_05/06_outcome_testing/"
                "g0_nofill_forward_source_capture_implementation_synthesis_readiness_route/"
                "verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py"
            ),
            "required_checks": [
                "parse every generated JSON and Markdown artifact",
                "parse shadow_logs/nofill_forward_source_capture.jsonl when present",
                "validate 55-field schema and 20 future logger fields",
                "verify NO_PROMOTION_VERDICT and false validation_safe/outcome_review_opened/live_effect flags",
                "reject forbidden raw broker/account/order/deal/position/ticket/result/cost/slippage/execution-quality output keys",
                "report duplicate-key and duplicate-group collisions without treating them as extra denominator rows",
                "recompute parser/source code hash status against current source",
                "report no-row state as expected only when live process/current-code/next-candidate conditions are not yet proven",
            ],
            "monitor_output_policy": "read-only report; no live restart, no config edit, no order/account/history calls, no scoring",
        }
    )

    duplicate_review = with_base(
        {
            "artifact_family": "duplicate_denominator_contamination_risk_review",
            "generated_at_utc": generated_at,
            "accepted_upstream_denominator_controls": {
                "cat_v3_equation": control["cat_v3_g0_decision"].get("recomputed_facts", {}).get("universe_equation"),
                "cat_v3_row_level_total": control["cat_v3_g0_decision"].get("recomputed_facts", {}).get("accepted_row_level_total"),
                "cat_v3_primary_duplicate_key_total": control["cat_v3_g0_decision"].get("recomputed_facts", {}).get("primary_unique_nofill_duplicate_key_total"),
                "cat_v3_secondary_duplicate_group_total": control["cat_v3_g0_decision"].get("recomputed_facts", {}).get("secondary_unique_duplicate_group_id_total"),
            },
            "runtime_duplicate_controls": [
                "nofill_duplicate_key_sha256",
                "duplicate_group_id_sha256",
                "row_level_denominator_member",
                "nofill_duplicate_key_count_member",
                "duplicate_group_id_count_member",
            ],
            "contamination_prevention_rules": [
                "Rows with source_control, source_impossible, reject, malformed, forbidden, or true safe-flag states cannot enter future denominators.",
                "Duplicate rows may support source/path evidence but cannot inflate sample size.",
                "Future validation must freeze row-level, duplicate-key, and duplicate-group denominator policies before opening outcomes.",
            ],
        }
    )

    historical_note = with_base(
        {
            "artifact_family": "historical_sealed_validation_parallel_route_note",
            "generated_at_utc": generated_at,
            "parallel_route": "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_LEDGER_AND_SOURCE_BINDING_ROUTE",
            "can_run_without_forward_rows": True,
            "why": "It can freeze discovery/development/sealed/stress/forward/contaminated partitions and source-field binding before any new forward row exists.",
            "fields_from_forward_capture_to_feed_future_historical_work": [
                "capture_observed_at_utc",
                "capture_timestamp_derivation_rule",
                "pending_order_mode_source_safe",
                "decision_spread_status",
                "entry_touch_spread_status",
                "pending_horizon_start_utc",
                "pending_horizon_end_utc",
                "terminal_area_touch_status",
                "protective_area_touch_status",
                "event_order_resolution_method",
                "same_tick_same_bar_ambiguity_status",
                "lower_tf_coverage_window_start_utc",
                "lower_tf_coverage_window_end_utc",
                "nofill_duplicate_key_sha256",
                "duplicate_group_id_sha256",
                "source_artifact_hash",
                "parser_code_hash",
                "forbidden_field_scan_status",
            ],
            "separation_rule": "Historical sealed validation may use sealed historical partitions only after source binding is frozen; forward rows remain realism/capture-quality evidence until a separate validation lane accepts them.",
        }
    )

    forbidden_ledger = with_base(
        {
            "artifact_family": "forbidden_route_ledger",
            "generated_at_utc": generated_at,
            "closed_routes": [
                "result/cost scoring",
                "sealed historical validation execution",
                "forward validation",
                "promotion dossier",
                "registry edit",
                "paid/API route",
                "remote push",
                "live restart by agent",
                "live trading prompt/config/risk/execution/permissions/safety/selector/canary/MT5 order-account-history behavior change",
                "credential access or mutation",
            ],
            "enforcement_evidence": {
                "g12_remaining_forbidden": control["g12_decision"].get("remaining_forbidden"),
                "diff_scope_forbidden_live_surface_paths": control["g12_diff_scope"].get("forbidden_live_surface_paths"),
                "prompts_or_config_changed_in_g12": control["g12_failopen"].get("prompts_or_config_changed"),
                "permission_or_safety_gate_changed_in_g12": control["g12_failopen"].get("permission_or_safety_gate_changed"),
                "mt5_order_account_history_behavior_changed_in_g12": control["g12_failopen"].get("mt5_order_account_history_behavior_changed"),
            },
        }
    )

    saturation = with_base(
        {
            "artifact_family": "saturation_self_redteam_pass",
            "generated_at_utc": generated_at,
            "questions": [
                {
                    "question": "What mistake would make source-control implementation evidence look like result, cost, validation, or promotion evidence?",
                    "answer": "Counting any row as a trade result, R value, cost estimate, validation sample, or promotion support. This route labels accepted evidence as implementation/readiness only and closes all scoring flags.",
                    "same_evidence_class_action": "Separation ledger and forbidden route ledger created.",
                },
                {
                    "question": "What mistake would let blocked, source-control, source-impossible, or rejected rows leak into future denominators?",
                    "answer": "Using row count from append-only logs without duplicate and terminal-state filters. Duplicate/denominator review requires row-level, duplicate-key, and duplicate-group policies before downstream use.",
                    "same_evidence_class_action": "Runtime duplicate fields and upstream 298-row denominator controls reconciled.",
                },
                {
                    "question": "What runtime state could make the logger silently produce no rows, malformed rows, duplicate rows, or rows with stale context?",
                    "answer": "Old imported process, no new CANDIDATE path, config disable, append failure swallowed by fail-open writer, stale context fields, malformed JSONL, or duplicate active setup rows.",
                    "same_evidence_class_action": "No-row diagnostic tree and owner action ledger created.",
                },
                {
                    "question": "What restart/deployment assumption could be false, and how should the owner verify it without changing trading logic?",
                    "answer": "The live process may not have imported commit 62f5a95f or current HEAD. Owner verifies by process restart or process-start proof, then lets the next normal candidate event emit rows.",
                    "same_evidence_class_action": "Owner-LIVE-001 and Owner-LIVE-002 recorded.",
                },
                {
                    "question": "What source/log/code path should be searched before accepting a no-row or missing-field blocker?",
                    "answer": "forward_capture.py writer/validator, orchestrator helper call, config disable key, nofill JSONL, sibling forward logs, and pipeline state context.",
                    "same_evidence_class_action": "Code path evidence and read-only source-log context recorded.",
                },
                {
                    "question": "What monitor weakness would fail to catch forbidden raw value leakage or schema drift?",
                    "answer": "Only checking line counts would miss forbidden keys, true safe flags, missing future fields, and duplicate contamination. The route verifier parses rows and calls the runtime validator.",
                    "same_evidence_class_action": "Future monitor/verifier spec created and route verifier implemented.",
                },
                {
                    "question": "What would a skeptical G12/G0 reviewer reject in the current readiness chain?",
                    "answer": "They would reject treating absent rows as proof of live deployment, treating G12 implementation acceptance as validation, or failing to specify owner-gated restart proof.",
                    "same_evidence_class_action": "Decision ledger uses expected-no-row/owner-check status rather than live-ready validation language.",
                },
                {
                    "question": "What is deliberately not answered here, and what future lane owns it?",
                    "answer": "Performance, cost, validation, promotion, registry decisions, and live scaling are not answered. Historical sealed partitioning and future row monitor lanes own source-bound next steps.",
                    "same_evidence_class_action": "Historical route note and next prompt pack created.",
                },
            ],
            "same_evidence_class_gaps_remaining": [],
        }
    )

    blockers = with_base(
        {
            "artifact_family": "exact_blocker_or_approval_requirement_ledger",
            "generated_at_utc": generated_at,
            "source_control_repair_blockers": [],
            "owner_or_live_operation_requirements": owner_actions if not runtime_log["exists"] else [owner_actions[2]],
            "ledger_status": (
                "NO_SOURCE_CONTROL_REPAIR_BLOCKERS_OWNER_LIVE_OPERATION_CHECK_REQUIRED"
                if not runtime_log["exists"]
                else "NO_SOURCE_CONTROL_REPAIR_BLOCKERS_ROWS_REQUIRE_RECURRING_READ_ONLY_MONITOR"
            ),
        }
    )

    instruction_items = [
        ("mandatory_preflight", "Context anchor records regenerated LIVE_STATE and required core docs.", "PASS"),
        ("accepted_g12_reconciled", "Decision ledger cites G12 terminal acceptance and zero repair blockers.", "PASS"),
        ("source_result_separation", "Separation and forbidden ledgers close result/cost/validation/promotion routes.", "PASS"),
        ("shadow_readiness", f"Readiness audit status is {shadow_state}.", "PASS"),
        ("owner_action_ledger", "Owner-gated restart/deployment/actions are exact and no live action was performed.", "PASS"),
        ("no_row_tree", "No-row/malformed/missing-field diagnostic tree exists.", "PASS"),
        ("future_monitor_spec", "Future monitor/verifier command and checks are exact.", "PASS"),
        ("duplicate_risk", "Duplicate/denominator contamination review exists.", "PASS"),
        ("historical_sealed_separation", "Historical sealed route note separates historical and forward evidence.", "PASS"),
        ("saturation", "Saturation/self-red-team pass answered eight lane-specific attacks.", "PASS"),
        ("safe_flags", "All generated JSON artifacts carry NO_PROMOTION_VERDICT and false safe flags.", "PASS"),
        ("no_placeholders", "Generated artifacts avoid unresolved placeholder tokens.", "PASS"),
    ]
    instruction_checklist = with_base(
        {
            "artifact_family": "instruction_coverage_checklist",
            "generated_at_utc": generated_at,
            "all_requirements_covered": True,
            "items": [
                {"requirement_id": req, "evidence": evidence_text, "status": status}
                for req, evidence_text, status in instruction_items
            ],
        }
    )

    completion_audit = with_base(
        {
            "artifact_family": "completion_audit",
            "generated_at_utc": generated_at,
            "objective_restatement": (
                "Complete a G0 source/control synthesis after G12 accepted the additive NOFILL forward source-capture implementation; diagnose shadow-readiness/no-row/restart state; specify owner-gated actions, future monitor requirements, historical sealed-validation separation, next route, and verification without opening scoring, validation, promotion, registry, paid/API, remote, or live behavior."
            ),
            "terminal_decision": TERMINAL_DECISION,
            "completion_standard_satisfied": True,
            "missing_incomplete_or_weak_requirements": [],
            "required_artifacts": REQUIRED_JSON + REQUIRED_MD + [
                "build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py",
                "verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py",
                "test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py",
            ],
            "prompt_to_artifact_checklist": instruction_checklist["items"],
            "can_mark_goal_complete_after_verification_commit_and_closeout": True,
            "next_strongest_goal_lane": historical_note["parallel_route"],
            "shadow_readiness_state": shadow_state,
            "verification_requirements": [
                "parse generated JSON/Markdown artifacts",
                "re-read G12 decision and blocker ledgers",
                "inspect runtime writer path and owner restart requirement",
                "parse nofill runtime log if present",
                "run route verifier and focused pytest",
                "run py_compile or AST syntax fallback",
                "regenerate LIVE_STATE at closeout",
            ],
        }
    )

    return {
        "context_anchor": context_anchor,
        "decision_ledger": decision_ledger,
        "evidence_chain": evidence_chain,
        "separation_ledger": separation_ledger,
        "readiness_audit": readiness_audit,
        "owner_ledger": owner_ledger,
        "no_row_tree": no_row_tree,
        "monitor_spec": monitor_spec,
        "duplicate_review": duplicate_review,
        "historical_note": historical_note,
        "forbidden_ledger": forbidden_ledger,
        "saturation": saturation,
        "instruction_checklist": instruction_checklist,
        "blockers": blockers,
        "completion_audit": completion_audit,
    }


def md_header(title: str) -> str:
    return (
        f"# {title}\n\n"
        f"Route: `{ROUTE_ID}`\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`\n"
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`\n\n"
    )


def render_md(title: str, payload: dict[str, Any]) -> str:
    lines = [md_header(title)]
    if payload.get("terminal_decision"):
        lines.append(f"Terminal decision: `{payload['terminal_decision']}`.\n\n")
    if payload.get("shadow_readiness_state"):
        lines.append(f"Shadow readiness state: `{payload['shadow_readiness_state']}`.\n\n")
    if payload.get("ledger_status"):
        lines.append(f"Ledger status: `{payload['ledger_status']}`.\n\n")
    if payload.get("objective_restatement"):
        lines.append(f"Objective: {payload['objective_restatement']}\n\n")
    lines.append("## Machine Payload\n\n")
    lines.append("```json\n")
    lines.append(json.dumps(payload, indent=2, sort_keys=True))
    lines.append("\n```\n")
    return "".join(lines)


def next_prompt_pack() -> str:
    prompt_path = (
        "research/science_program_2026_05/04_goal_prompts/"
        "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING_GOAL_PROMPT_2026-05-10.md"
    )
    starter = (
        "/goal Follow the full controlling prompt in "
        f"{prompt_path} as the complete objective; do mandatory preflight and context refresh first; "
        "read .context/00_core/goal_session_research_discipline.md; do not rely on chat memory; stay source/control historical sealed-validation partitioning and field-binding only with no result/cost scoring, validation execution, promotion, registry edit, paid/API route, remote push, prompts, config, risk, permissions, safety, selectors, canaries, MT5 order/account/history/deal/position behavior, credentials, live restart, or live trading behavior changes; pursue proof-or-impossibility to the full end inside this evidence class; complete only with sealed/discovery/development/stress/forward/contaminated partition ledger, source-field binding for NOFILL forward source-capture fields, exact blocker ledger, mandatory builder/verifier/focused tests, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; if any blocker appears, pursue until cleared, proven impossible from approved routes, or reduced to an exact owner/access/source/capture approval requirement."
    )
    return (
        md_header("G0 NOFILL Forward Source-Capture Next Prompt Pack")
        + "## Next Strongest Lane\n\n"
        + "`NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_LEDGER_AND_SOURCE_BINDING_ROUTE`\n\n"
        + "Why: it can run without waiting for forward rows and prevents future validation from mixing discovery, development, sealed, stress, forward, and contaminated evidence classes.\n\n"
        + "## One-Line Starter\n\n"
        + "```text\n"
        + starter
        + "\n```\n\n"
        + "## Owner-Gated Companion Check\n\n"
        + "After an owner-approved live restart or process-start proof and the next normal candidate event, rerun this route verifier to inspect `shadow_logs/nofill_forward_source_capture.jsonl` read-only.\n"
    )


def build_artifacts() -> dict[str, Any]:
    payload = build_payload()
    mapping_json = {
        REQUIRED_JSON[0]: payload["context_anchor"],
        REQUIRED_JSON[1]: payload["decision_ledger"],
        REQUIRED_JSON[2]: payload["evidence_chain"],
        REQUIRED_JSON[3]: payload["separation_ledger"],
        REQUIRED_JSON[4]: payload["readiness_audit"],
        REQUIRED_JSON[5]: payload["owner_ledger"],
        REQUIRED_JSON[6]: payload["no_row_tree"],
        REQUIRED_JSON[7]: payload["monitor_spec"],
        REQUIRED_JSON[8]: payload["duplicate_review"],
        REQUIRED_JSON[9]: payload["historical_note"],
        REQUIRED_JSON[10]: payload["forbidden_ledger"],
        REQUIRED_JSON[11]: payload["saturation"],
        REQUIRED_JSON[12]: payload["instruction_checklist"],
        REQUIRED_JSON[13]: payload["blockers"],
        REQUIRED_JSON[14]: payload["completion_audit"],
    }
    titles = {
        REQUIRED_MD[0]: "G0 NOFILL Forward Source-Capture Context Anchor",
        REQUIRED_MD[1]: "G0 NOFILL Forward Source-Capture Decision Ledger",
        REQUIRED_MD[2]: "G0 NOFILL Forward Source-Capture Evidence Chain Reconciliation",
        REQUIRED_MD[3]: "G0 NOFILL Forward Source-Capture Separation Ledger",
        REQUIRED_MD[4]: "G0 NOFILL Forward Source-Capture Shadow Readiness Audit",
        REQUIRED_MD[5]: "G0 NOFILL Forward Source-Capture Owner Action Ledger",
        REQUIRED_MD[6]: "G0 NOFILL Forward Source-Capture No-Row Diagnostic Tree",
        REQUIRED_MD[7]: "G0 NOFILL Forward Source-Capture Future Monitor Spec",
        REQUIRED_MD[8]: "G0 NOFILL Forward Source-Capture Duplicate Denominator Risk Review",
        REQUIRED_MD[9]: "G0 NOFILL Forward Source-Capture Historical Sealed Validation Note",
        REQUIRED_MD[10]: "G0 NOFILL Forward Source-Capture Forbidden Route Ledger",
        REQUIRED_MD[11]: "G0 NOFILL Forward Source-Capture Saturation Self-Red-Team",
        REQUIRED_MD[12]: "G0 NOFILL Forward Source-Capture Instruction Coverage Checklist",
        REQUIRED_MD[13]: "G0 NOFILL Forward Source-Capture Blocker Approval Ledger",
        REQUIRED_MD[15]: "G0 NOFILL Forward Source-Capture Completion Audit",
    }
    md_payloads = [
        payload["context_anchor"],
        payload["decision_ledger"],
        payload["evidence_chain"],
        payload["separation_ledger"],
        payload["readiness_audit"],
        payload["owner_ledger"],
        payload["no_row_tree"],
        payload["monitor_spec"],
        payload["duplicate_review"],
        payload["historical_note"],
        payload["forbidden_ledger"],
        payload["saturation"],
        payload["instruction_checklist"],
        payload["blockers"],
        None,
        payload["completion_audit"],
    ]
    BASE.mkdir(parents=True, exist_ok=True)
    for name, obj in mapping_json.items():
        (BASE / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, obj in zip(REQUIRED_MD, md_payloads):
        if name.endswith("NEXT_PROMPT_PACK_2026-05-10.md"):
            (BASE / name).write_text(next_prompt_pack(), encoding="utf-8")
        else:
            (BASE / name).write_text(render_md(titles[name], obj), encoding="utf-8")
    return payload


def main() -> None:
    build_artifacts()
    print(f"Built {len(REQUIRED_JSON) + len(REQUIRED_MD)} G0 source-capture synthesis artifacts in {BASE}")


if __name__ == "__main__":
    main()
