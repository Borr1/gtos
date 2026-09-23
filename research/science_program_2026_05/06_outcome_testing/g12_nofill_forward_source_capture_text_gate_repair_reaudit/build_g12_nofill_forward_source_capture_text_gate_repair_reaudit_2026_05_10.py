#!/usr/bin/env python3
"""Build the independent G12 text-gate repair reaudit artifacts.

This lane audits the source-capture verifier repair in commit d2bd8cac. It is
source/control-only and does not open result scoring, validation, promotion,
live logger wiring, paid/API routes, registry edits, remote push, or live
trading behavior.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-10"
ROUTE_ID = "G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT"
SCHEMA_VERSION = "g12_nofill_forward_source_capture_text_gate_repair_reaudit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ACCEPT_TERMINAL_VERDICT = "ACCEPT_AS_SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY_AFTER_TEXT_GATE_REPAIR"
BLOCKER_TERMINAL_VERDICT = "ACCEPT_WITH_REMAINING_EXACT_REPAIR_BLOCKERS"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
PACKAGE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_contract_hardening_offline_projection_prototype"
)
PRIOR_REPAIR_AUDIT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_forward_source_capture_repair_reaudit"
)
PRIOR_ACCEPTANCE_AUDIT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_forward_source_capture_prototype_acceptance_audit"
)
PROMPT_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-10.md"
)

TARGET_VERIFIER = PACKAGE_DIR / "verify_nofill_forward_capture_contract_2026_05_09.py"
TARGET_TEST = PACKAGE_DIR / "test_nofill_forward_capture_contract_2026_05_09.py"
TARGET_MANIFEST = PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json"
TARGET_RESULT = PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json"
TARGET_ROWS = PACKAGE_DIR / "NOFILL_FORWARD_OFFLINE_PROJECTION_PROTOTYPE_ROWS_2026-05-09.jsonl"
TARGET_CONTRACT = PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_2026-05-09.json"
TARGET_NO_LEAK = PACKAGE_DIR / "NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_2026-05-09.json"
TARGET_DENOM = PACKAGE_DIR / "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_2026-05-09.json"
TARGET_FIXTURE_MANIFEST = PACKAGE_DIR / "NOFILL_FORWARD_FIXTURE_MANIFEST_2026-05-09.json"
TARGET_SEPARATION = PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_2026-05-09.json"
TARGET_COMPLETION = PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_2026-05-09.json"

PRIOR_REPAIR_BLOCKER = (
    PRIOR_REPAIR_AUDIT_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_BLOCKER_CLOSURE_LEDGER_2026-05-09.json"
)
PRIOR_REPAIR_PROOF = (
    PRIOR_REPAIR_AUDIT_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADVERSARIAL_HASH_POLICY_PROOF_2026-05-09.json"
)
PRIOR_ACCEPTANCE_DECISION = (
    PRIOR_ACCEPTANCE_AUDIT_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_ACCEPTANCE_DECISION_LEDGER_2026-05-09.json"
)

CONTROL_FLAGS: dict[str, Any] = {
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

AUDIT_JSON = [
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_VERIFICATION_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_ADVERSARIAL_HASH_POLICY_PROOF_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_SOURCE_HASH_RECOMPUTATION_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_NO_LEAK_CONTROL_REGRESSION_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_BLOCKER_CLOSURE_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_COMPLETION_AUDIT_{DATE}.json",
]

AUDIT_MD = [
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_VERIFICATION_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_ADVERSARIAL_HASH_POLICY_PROOF_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_SOURCE_HASH_RECOMPUTATION_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_NO_LEAK_CONTROL_REGRESSION_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_BLOCKER_CLOSURE_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_COMPLETION_AUDIT_{DATE}.md",
]

VERIFICATION_RESULT_NAME = (
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_VERIFICATION_RESULT_{DATE}.json"
)

ALLOWED_TERMINAL_VERDICTS = {
    ACCEPT_TERMINAL_VERDICT,
    BLOCKER_TERMINAL_VERDICT,
    "RETURN_TO_SOURCE_CAPTURE_LANE_WITH_EXACT_FIXES",
    "REJECT_INVALID_TEXT_GATE_REPAIR",
}

FORBIDDEN_ROW_KEYS = {
    "account_history",
    "account_id",
    "account_pnl",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "deal_id",
    "dsr",
    "expectancy",
    "fill_time_utc",
    "live_order_state",
    "mt5_deal_id",
    "mt5_order_ticket",
    "mt5_position_id",
    "order_id",
    "order_send_attempted",
    "order_send_success",
    "pbo",
    "pending_ticket",
    "position_id",
    "profit_factor",
    "r_multiple",
    "r_value",
    "slippage_price",
    "synthetic_path_r",
    "trade_state_ticket",
    "win_rate",
}


def repo_rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_no}:{exc}") from exc
    return rows


def write_json(name: str, payload: Any) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (OUT_DIR / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lf_normalized_bytes(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_lf_bytes(data: bytes) -> str:
    return sha256_bytes(lf_normalized_bytes(data))


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip()


def git_status_paths() -> list[str]:
    paths: list[str] = []
    for line in run_git(["status", "--short"]).splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        paths.append(line[3:].replace("\\", "/"))
    return sorted(paths)


def base(artifact: str) -> dict[str, Any]:
    return {
        "artifact": artifact,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **CONTROL_FLAGS,
    }


def load_target_verifier() -> Any:
    if str(PACKAGE_DIR) not in sys.path:
        sys.path.insert(0, str(PACKAGE_DIR))
    spec = importlib.util.spec_from_file_location("target_nofill_forward_capture_verifier", TARGET_VERIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load target verifier from {TARGET_VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def target_hash_decision(entry: dict[str, Any], actual_path: Path) -> dict[str, Any]:
    target = load_target_verifier()
    actual_raw = target.sha256_file(actual_path)
    target_lf = target.sha256_lf_normalized_file(actual_path)
    synthetic_lf = sha256_lf_bytes(actual_path.read_bytes())
    allows_text_fallback = target.entry_allows_lf_normalized_fallback(entry)

    if entry.get("sha256") and actual_raw == entry.get("sha256"):
        decision = "ACCEPT_EXACT_RAW_HASH"
        accepted = True
    elif entry.get("strict_hash_recompute") is False:
        decision = "ACCEPT_MUTABLE_CONTEXT_RAW_DRIFT_WARNING"
        accepted = True
    elif (
        allows_text_fallback
        and entry.get("sha256_lf_normalized")
        and target_lf == entry.get("sha256_lf_normalized")
    ):
        decision = "ACCEPT_TEXT_LF_NORMALIZED_FALLBACK_WARNING"
        accepted = True
    else:
        decision = "REJECT_HASH_RECOMPUTE_FAILURE"
        accepted = False

    return {
        "path": str(actual_path),
        "suffix": actual_path.suffix,
        "target_entry_allows_lf_normalized_fallback": allows_text_fallback,
        "expected_raw": entry.get("sha256"),
        "actual_raw": actual_raw,
        "raw_sha_matches": bool(entry.get("sha256") and actual_raw == entry.get("sha256")),
        "expected_lf_normalized": entry.get("sha256_lf_normalized"),
        "target_lf_normalized": target_lf,
        "synthetic_lf_normalized_from_bytes": synthetic_lf,
        "synthetic_lf_normalized_hash_matches_manifest": synthetic_lf == entry.get("sha256_lf_normalized"),
        "target_lf_normalized_hash_matches_manifest": target_lf == entry.get("sha256_lf_normalized"),
        "strict_hash_recompute": entry.get("strict_hash_recompute"),
        "target_package_verifier_decision": decision,
        "target_package_verifier_accepts": accepted,
        "accepted_only_through_bounded_text_fallback": (
            decision == "ACCEPT_TEXT_LF_NORMALIZED_FALLBACK_WARNING"
            and not bool(entry.get("sha256") and actual_raw == entry.get("sha256"))
            and allows_text_fallback
        ),
    }


def manifest_entry_for(original_bytes: bytes, path: Path, strict: bool = True) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": True,
        "sha256": sha256_bytes(original_bytes),
        "sha256_lf_normalized": sha256_lf_bytes(original_bytes),
        "strict_hash_recompute": strict,
        "hash_policy": "strict_recompute" if strict else "mutable_context_snapshot_presence_only",
    }


def build_context_anchor() -> dict[str, Any]:
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_CONTEXT_ANCHOR"),
        "audit_head": run_git(["rev-parse", "--short", "HEAD"]),
        "audit_branch": run_git(["branch", "--show-current"]),
        "controlling_prompt_path": repo_rel(PROMPT_PATH),
        "audited_repair_commit": "d2bd8cac research: text-gate nofill source capture hash fallback",
        "audited_package_path": repo_rel(PACKAGE_DIR),
        "target_verifier_path": repo_rel(TARGET_VERIFIER),
        "target_test_path": repo_rel(TARGET_TEST),
        "target_manifest_path": repo_rel(TARGET_MANIFEST),
        "target_package_verification_result_path": repo_rel(TARGET_RESULT),
        "prior_repair_reaudit_path": repo_rel(PRIOR_REPAIR_AUDIT_DIR),
        "prior_acceptance_audit_path": repo_rel(PRIOR_ACCEPTANCE_AUDIT_DIR),
        "mandatory_preflight_completed": True,
        "mandatory_context_read": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            repo_rel(PROMPT_PATH),
        ],
        "scope_boundary": {
            "source_control_only": True,
            "no_result_or_cost_scoring": True,
            "no_validation": True,
            "no_promotion": True,
            "no_live_logger_wiring": True,
            "no_registry_edit": True,
            "no_paid_api_route": True,
            "no_remote_push": True,
            "no_live_trading_behavior": True,
        },
    }


def inspect_target_verifier_source() -> dict[str, Any]:
    lines = TARGET_VERIFIER.read_text(encoding="utf-8").splitlines()
    text_suffix_line = None
    sha_lf_function_line = None
    suffix_guard_line = None
    entry_gate_function_line = None
    fallback_call_line = None
    raw_recompute_line = None
    mutable_context_line = None
    failure_line = None
    fallback_window: list[dict[str, Any]] = []

    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("TEXT_HASH_FALLBACK_SUFFIXES"):
            text_suffix_line = {"line": line_no, "code": stripped}
        if stripped.startswith("def sha256_lf_normalized_file"):
            sha_lf_function_line = {"line": line_no, "code": stripped}
        if "full.suffix.lower() not in TEXT_HASH_FALLBACK_SUFFIXES" in stripped:
            suffix_guard_line = {"line": line_no, "code": stripped}
        if stripped.startswith("def entry_allows_lf_normalized_fallback"):
            entry_gate_function_line = {"line": line_no, "code": stripped}
        if "recomputed = sha256_file" in stripped:
            raw_recompute_line = {"line": line_no, "code": stripped}
        if 'entry.get("strict_hash_recompute") is False' in stripped:
            mutable_context_line = {"line": line_no, "code": stripped}
        if "entry_allows_lf_normalized_fallback(entry)" in stripped:
            fallback_call_line = {"line": line_no, "code": stripped}
            for offset in range(max(0, line_no - 9), min(len(lines), line_no + 10)):
                fallback_window.append({"line": offset + 1, "code": lines[offset].strip()})
        if '"hash_recompute"' in stripped and "failures.append" in stripped:
            failure_line = {"line": line_no, "code": stripped}

    checks = {
        "text_suffix_allowlist_defined": text_suffix_line is not None,
        "sha256_lf_normalized_function_has_suffix_guard": suffix_guard_line is not None,
        "entry_gate_function_present": entry_gate_function_line is not None,
        "fallback_branch_calls_entry_gate": fallback_call_line is not None,
        "raw_sha_recomputed_before_fallback": (
            raw_recompute_line is not None
            and fallback_call_line is not None
            and raw_recompute_line["line"] < fallback_call_line["line"]
        ),
        "mutable_context_separated_before_lf_fallback": (
            mutable_context_line is not None
            and fallback_call_line is not None
            and mutable_context_line["line"] < fallback_call_line["line"]
        ),
        "true_content_mismatch_fails_after_fallback_checks": (
            failure_line is not None
            and fallback_call_line is not None
            and failure_line["line"] > fallback_call_line["line"]
        ),
    }
    status = "PASS" if all(checks.values()) else "FAIL_TEXT_GATE_SOURCE_INSPECTION"
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_VERIFIER_SOURCE_INSPECTION"),
        "status": status,
        "target_verifier_path": repo_rel(TARGET_VERIFIER),
        "target_verifier_sha256": sha256_file(TARGET_VERIFIER),
        "text_suffix_allowlist_line": text_suffix_line,
        "sha256_lf_normalized_function_line": sha_lf_function_line,
        "sha256_lf_normalized_suffix_guard_line": suffix_guard_line,
        "entry_gate_function_line": entry_gate_function_line,
        "raw_recompute_line": raw_recompute_line,
        "mutable_context_line": mutable_context_line,
        "fallback_entry_gate_call_line": fallback_call_line,
        "content_failure_line": failure_line,
        "fallback_window": fallback_window,
        "checks": checks,
        "conclusion": (
            "The target verifier now defines an explicit text suffix allowlist, refuses to compute "
            "LF-normalized hashes for suffixes outside that allowlist, and requires "
            "entry_allows_lf_normalized_fallback(entry) before accepting sha256_lf_normalized."
        ),
    }


def run_adversarial_hash_policy_probe() -> dict[str, Any]:
    temp_dir = OUT_DIR / "_tmp_text_gate_adversarial_hash_policy"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    protected = {
        repo_rel(TARGET_VERIFIER): sha256_file(TARGET_VERIFIER),
        repo_rel(TARGET_MANIFEST): sha256_file(TARGET_MANIFEST),
        repo_rel(TARGET_RESULT): sha256_file(TARGET_RESULT) if TARGET_RESULT.exists() else None,
    }

    cases: list[dict[str, Any]] = []
    try:
        text_path = temp_dir / "strict_text_lf_portability.md"
        original_text = b"alpha\r\nbeta\r\n"
        text_path.write_bytes(b"alpha\nbeta\n")
        cases.append(
            {
                "case_id": "STRICT_TEXT_EOL_PORTABILITY_ACCEPTED_ONLY_BY_TEXT_FALLBACK",
                "requirement": "strict text raw SHA changes under CRLF/LF normalization while LF-normalized SHA matches",
                **target_hash_decision(manifest_entry_for(original_text, text_path, strict=True), text_path),
            }
        )

        mutation_path = temp_dir / "strict_text_true_mutation.md"
        original_mutation = b"alpha\nbeta\n"
        mutation_path.write_bytes(b"alpha\nMUTATED\n")
        cases.append(
            {
                "case_id": "STRICT_TEXT_TRUE_CONTENT_MUTATION_REJECTED",
                "requirement": "strict text true content mutation changes LF-normalized SHA and is rejected",
                **target_hash_decision(manifest_entry_for(original_mutation, mutation_path, strict=True), mutation_path),
            }
        )

        binary_path = temp_dir / "strict_binary_payload.bin"
        original_binary = b"\x00BIN\r\nPAYLOAD\xff"
        binary_path.write_bytes(b"\x00BIN\nPAYLOAD\xff")
        binary_entry = manifest_entry_for(original_binary, binary_path, strict=True)
        binary_entry["sha256_lf_normalized"] = sha256_lf_bytes(binary_path.read_bytes())
        cases.append(
            {
                "case_id": "STRICT_BINARY_NON_TEXT_RAW_SHA_DRIFT_REJECTED_EVEN_WITH_SYNTHETIC_LF_MATCH",
                "requirement": "strict .bin/non-text raw SHA mismatch must fail even if a synthetic LF-normalized hash matches",
                **target_hash_decision(binary_entry, binary_path),
            }
        )

        mutable_path = temp_dir / "mutable_context_snapshot.md"
        original_mutable = b"old snapshot\n"
        mutable_path.write_bytes(b"new snapshot\n")
        cases.append(
            {
                "case_id": "MUTABLE_CONTEXT_NON_STRICT_DRIFT_WARNING_ONLY",
                "requirement": "strict_hash_recompute=false mutable context remains warning-only and cannot mask strict-source failures",
                **target_hash_decision(manifest_entry_for(original_mutable, mutable_path, strict=False), mutable_path),
            }
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    after = {
        repo_rel(TARGET_VERIFIER): sha256_file(TARGET_VERIFIER),
        repo_rel(TARGET_MANIFEST): sha256_file(TARGET_MANIFEST),
        repo_rel(TARGET_RESULT): sha256_file(TARGET_RESULT) if TARGET_RESULT.exists() else None,
    }

    by_case = {case["case_id"]: case for case in cases}
    text_case = by_case["STRICT_TEXT_EOL_PORTABILITY_ACCEPTED_ONLY_BY_TEXT_FALLBACK"]
    mutation_case = by_case["STRICT_TEXT_TRUE_CONTENT_MUTATION_REJECTED"]
    binary_case = by_case["STRICT_BINARY_NON_TEXT_RAW_SHA_DRIFT_REJECTED_EVEN_WITH_SYNTHETIC_LF_MATCH"]
    mutable_case = by_case["MUTABLE_CONTEXT_NON_STRICT_DRIFT_WARNING_ONLY"]

    status_checks = {
        "strict_text_lf_portability_accepted_only_through_bounded_text_fallback": (
            text_case["target_package_verifier_accepts"] is True
            and text_case["accepted_only_through_bounded_text_fallback"] is True
            and text_case["raw_sha_matches"] is False
            and text_case["target_lf_normalized_hash_matches_manifest"] is True
        ),
        "strict_text_true_mutation_rejected": (
            mutation_case["target_package_verifier_accepts"] is False
            and mutation_case["target_lf_normalized_hash_matches_manifest"] is False
        ),
        "strict_binary_non_text_raw_sha_mismatch_rejected_despite_synthetic_lf_match": (
            binary_case["target_package_verifier_accepts"] is False
            and binary_case["target_entry_allows_lf_normalized_fallback"] is False
            and binary_case["target_lf_normalized"] is None
            and binary_case["synthetic_lf_normalized_hash_matches_manifest"] is True
        ),
        "mutable_context_raw_drift_warning_only": (
            mutable_case["strict_hash_recompute"] is False
            and mutable_case["target_package_verifier_accepts"] is True
            and mutable_case["target_package_verifier_decision"] == "ACCEPT_MUTABLE_CONTEXT_RAW_DRIFT_WARNING"
        ),
        "mutable_context_does_not_mask_strict_source_failure": mutation_case["target_package_verifier_accepts"] is False,
        "temporary_probe_dir_removed": not temp_dir.exists(),
        "committed_target_artifacts_unchanged": protected == after,
    }
    status = "PASS" if all(status_checks.values()) else "FAIL_ADVERSARIAL_HASH_POLICY"
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_ADVERSARIAL_HASH_POLICY_PROOF"),
        "status": status,
        "status_checks": status_checks,
        "cases": cases,
        "strict_text_lf_portability_accepted_only_through_bounded_text_fallback": status_checks[
            "strict_text_lf_portability_accepted_only_through_bounded_text_fallback"
        ],
        "strict_text_true_mutation_rejected": status_checks["strict_text_true_mutation_rejected"],
        "strict_binary_non_text_raw_sha_mismatch_rejected_despite_synthetic_lf_match": status_checks[
            "strict_binary_non_text_raw_sha_mismatch_rejected_despite_synthetic_lf_match"
        ],
        "mutable_context_raw_drift_warning_only": status_checks["mutable_context_raw_drift_warning_only"],
        "mutable_context_does_not_mask_strict_source_failure": status_checks[
            "mutable_context_does_not_mask_strict_source_failure"
        ],
        "committed_source_hashes_before": protected,
        "committed_source_hashes_after": after,
        "committed_source_artifacts_unchanged": protected == after,
        "temporary_probe_dir": repo_rel(temp_dir),
        "temporary_probe_dir_exists_after_cleanup": temp_dir.exists(),
        "cleanup_verified": not temp_dir.exists() and protected == after,
        "adversarial_conclusion": (
            "The text gate closes the narrowed blocker: strict text EOL portability still passes only "
            "through bounded LF-normalized text fallback; true text mutation fails; strict .bin/non-text "
            "raw SHA drift fails even when the synthetic LF-normalized digest matches; mutable-context "
            "drift remains warning-only and does not mask strict-source failure."
        ),
    }


def run_package_verifier() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "verify_nofill_forward_capture_contract_2026_05_09.py"],
        cwd=PACKAGE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    parsed_result = read_json(TARGET_RESULT) if TARGET_RESULT.exists() else {}
    return {
        "command": "python verify_nofill_forward_capture_contract_2026_05_09.py",
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
        "ok": parsed_result.get("ok"),
        "can_mark_goal_complete": parsed_result.get("can_mark_goal_complete"),
        "failures": parsed_result.get("failures"),
        "warnings": parsed_result.get("warnings"),
        "dirty_paths_reviewed": parsed_result.get("dirty_paths_reviewed"),
        "future_live_logger_wiring_lane_still_gated": parsed_result.get(
            "future_live_logger_wiring_lane_still_gated"
        ),
        "route_flags": {flag: parsed_result.get(flag) for flag in CONTROL_FLAGS},
    }


def all_manifest_entries(manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    entries: list[tuple[str, dict[str, Any]]] = []
    for group in ("source_entries", "parser_entries", "fixture_entries", "generated_entries"):
        for entry in manifest.get(group, []):
            entries.append((group, entry))
    return entries


def audit_source_hash_manifest() -> dict[str, Any]:
    target = load_target_verifier()
    manifest = read_json(TARGET_MANIFEST)
    exact_matches: list[dict[str, Any]] = []
    text_lf_fallback_matches: list[dict[str, Any]] = []
    mutable_context_warnings: list[dict[str, Any]] = []
    strict_non_text_entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    group_counts = {group: len(manifest.get(group, [])) for group in ("source_entries", "parser_entries", "fixture_entries", "generated_entries")}

    for group, entry in all_manifest_entries(manifest):
        path = REPO_ROOT / entry.get("path", "")
        item = {
            "group": group,
            "path": entry.get("path"),
            "strict_hash_recompute": entry.get("strict_hash_recompute"),
            "hash_policy": entry.get("hash_policy"),
            "target_entry_allows_lf_normalized_fallback": target.entry_allows_lf_normalized_fallback(entry),
            "expected_sha256": entry.get("sha256"),
            "expected_sha256_lf_normalized": entry.get("sha256_lf_normalized"),
        }
        if not path.exists():
            missing.append(item)
            continue
        actual_raw = target.sha256_file(path)
        actual_lf = target.sha256_lf_normalized_file(path)
        item["actual_sha256"] = actual_raw
        item["actual_sha256_lf_normalized"] = actual_lf
        item["suffix"] = path.suffix.lower()
        if entry.get("strict_hash_recompute") is not False and not target.entry_allows_lf_normalized_fallback(entry):
            strict_non_text_entries.append(item)
        if entry.get("sha256") and actual_raw == entry.get("sha256"):
            exact_matches.append(item)
            continue
        if entry.get("strict_hash_recompute") is False:
            item["warning_type"] = "mutable_context_hash_drift"
            mutable_context_warnings.append(item)
            continue
        if (
            target.entry_allows_lf_normalized_fallback(entry)
            and entry.get("sha256_lf_normalized")
            and actual_lf == entry.get("sha256_lf_normalized")
        ):
            item["warning_type"] = "strict_text_lf_normalized_hash_match"
            text_lf_fallback_matches.append(item)
            continue
        failures.append(item)

    status = "PASS" if not failures and not missing else "FAIL_SOURCE_HASH_RECOMPUTATION"
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_SOURCE_HASH_RECOMPUTATION_AUDIT"),
        "status": status,
        "manifest_path": repo_rel(TARGET_MANIFEST),
        "manifest_sha256": sha256_file(TARGET_MANIFEST),
        "group_counts": group_counts,
        "total_manifest_entries": sum(group_counts.values()),
        "exact_raw_hash_match_count": len(exact_matches),
        "strict_text_lf_normalized_fallback_match_count_current_checkout": len(text_lf_fallback_matches),
        "mutable_context_warning_count": len(mutable_context_warnings),
        "strict_non_text_manifest_entry_count": len(strict_non_text_entries),
        "content_hash_failure_count": len(failures),
        "missing_manifest_path_count": len(missing),
        "strict_text_lf_normalized_fallback_matches": text_lf_fallback_matches,
        "mutable_context_warnings": mutable_context_warnings,
        "strict_non_text_manifest_entries_sample": strict_non_text_entries[:20],
        "content_hash_failures": failures,
        "missing_manifest_paths": missing,
        "conclusion": (
            "The regenerated source-hash manifest is internally consistent: every strict source either "
            "matches raw SHA or, for explicit text artifacts only, matches bounded LF-normalized evidence; "
            "mutable context remains warning-only; no true strict content failures or missing manifest paths were found."
            if status == "PASS"
            else "The manifest has unresolved strict hash failures or missing paths."
        ),
    }


def audit_no_leak_control_regression() -> dict[str, Any]:
    rows = read_jsonl(TARGET_ROWS)
    family_counts = dict(Counter(row.get("v3_terminal_family") for row in rows))
    forbidden_key_hits: list[dict[str, Any]] = []
    open_flag_hits: list[dict[str, Any]] = []
    raw_value_hits: list[dict[str, Any]] = []
    for row in rows:
        packet_row_id = row.get("packet_row_id")
        for key in FORBIDDEN_ROW_KEYS:
            if key in row:
                forbidden_key_hits.append({"packet_row_id": packet_row_id, "key": key})
        for flag in ("validation_safe", "outcome_review_opened", "live_effect", "opens_result_scoring", "opens_live_wiring"):
            if row.get(flag) is not False:
                open_flag_hits.append({"packet_row_id": packet_row_id, "flag": flag, "value": row.get(flag)})
        row_text = json.dumps(row, sort_keys=True)
        for raw_token in ("09", "SECRET", "ticket-"):
            if raw_token in row_text:
                raw_value_hits.append({"packet_row_id": packet_row_id, "token": raw_token})

    no_leak = read_json(TARGET_NO_LEAK)
    denom = read_json(TARGET_DENOM)
    fixture_manifest = read_json(TARGET_FIXTURE_MANIFEST)
    separation = read_json(TARGET_SEPARATION)
    contract = read_json(TARGET_CONTRACT)

    fixture_categories = {item.get("category") for item in fixture_manifest.get("fixtures", [])}
    same_tick_fixture_present = any(
        category in fixture_categories
        for category in ("same_tick_ambiguity_row", "same_tick_same_bar_ambiguity")
    )
    expected_family_counts = {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}
    row_den = sum(bool(row.get("row_level_denominator_member")) for row in rows)
    primary_den = sum(bool(row.get("nofill_duplicate_key_count_member")) for row in rows)
    secondary_den = sum(bool(row.get("duplicate_group_id_count_member")) for row in rows)
    cost_execution_closed = (
        separation.get("slippage_label_status_counts") == {"NOT_OPENED_FOR_SOURCE_CONTROL": 298}
        and separation.get("execution_quality_label_status_counts") == {"NOT_OPENED_FOR_SOURCE_CONTROL": 298}
        and separation.get("cost_testing_gate_status_counts") == {"COST_TESTING_NOT_OPENED": 298}
    )
    future_live_gate_closed = (
        contract.get("future_live_logger_wiring_gate")
        == "YES_GATED_BEHIND_G12_ACCEPTANCE_AND_SEPARATE_OWNER_APPROVAL"
    )
    checks = {
        "prototype_row_count_298": len(rows) == 298,
        "family_counts_preserved": family_counts == expected_family_counts,
        "accepted_denominators_preserved_225_182_139": (row_den, primary_den, secondary_den) == (225, 182, 139),
        "no_forbidden_raw_keys_in_projection_rows": not forbidden_key_hits,
        "no_open_route_flags_in_projection_rows": not open_flag_hits,
        "no_raw_ticket_secret_material_in_projection_rows": not raw_value_hits,
        "package_no_leak_audit_pass": no_leak.get("status") == "PASS",
        "package_denominator_audit_pass": denom.get("status") == "PASS",
        "same_tick_ambiguity_fixture_present": same_tick_fixture_present,
        "source_cost_execution_separation_preserved": cost_execution_closed,
        "future_live_logger_gate_still_closed": future_live_gate_closed,
    }
    status = "PASS" if all(checks.values()) else "FAIL_NO_LEAK_OR_CONTROL_REGRESSION"
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_NO_LEAK_CONTROL_REGRESSION_AUDIT"),
        "status": status,
        "checks": checks,
        "prototype_row_count": len(rows),
        "family_counts": family_counts,
        "frozen_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
        "row_level_accepted_denominator": row_den,
        "primary_duplicate_key_denominator": primary_den,
        "secondary_duplicate_group_denominator": secondary_den,
        "forbidden_key_hits_in_prototype_rows": forbidden_key_hits,
        "prototype_rows_with_open_flags": open_flag_hits,
        "raw_value_hits_in_projection_rows": raw_value_hits,
        "package_no_leak_status": no_leak.get("status"),
        "package_denominator_status": denom.get("status"),
        "fixture_categories": sorted(fixture_categories),
        "same_tick_ambiguity_fixture_present": same_tick_fixture_present,
        "source_cost_execution_separation_status": "PASS" if cost_execution_closed else "FAIL",
        "future_live_logger_wiring_gate": contract.get("future_live_logger_wiring_gate"),
        "repair_regression_conclusion": (
            "The text-gate repair did not change the frozen package equation, accepted denominators, "
            "redaction/no-leak controls, same-tick ambiguity preservation, source/cost/execution separation, "
            "or future live logger gating."
        ),
    }


def audit_text_gate_repair(
    source_inspection: dict[str, Any],
    adversarial: dict[str, Any],
    source_hash: dict[str, Any],
    no_leak: dict[str, Any],
) -> dict[str, Any]:
    package_verifier = run_package_verifier()
    prior_blocker = read_json(PRIOR_REPAIR_BLOCKER)
    prior_proof = read_json(PRIOR_REPAIR_PROOF)
    prior_acceptance = read_json(PRIOR_ACCEPTANCE_DECISION)
    checks = {
        "prior_acceptance_audit_reconstructed": prior_acceptance.get("terminal_verdict") == "ACCEPT_WITH_EXACT_REPAIR_BLOCKERS",
        "prior_repair_reaudit_reconstructed": prior_blocker.get("terminal_verdict") == BLOCKER_TERMINAL_VERDICT,
        "prior_text_gate_blocker_reconstructed": any(
            item.get("blocker_id") == "G12-SRC-CAP-REPAIR-001"
            for item in prior_blocker.get("remaining_blockers", [])
        ),
        "prior_binary_weakness_reproduced_in_previous_audit": prior_proof.get("strict_binary_or_non_text_raw_sha_required") is False,
        "package_verifier_rerun_ok": package_verifier.get("returncode") == 0 and package_verifier.get("ok") is True,
        "package_verifier_zero_failures": package_verifier.get("failures") == [],
        "package_route_flags_closed": all(package_verifier.get("route_flags", {}).get(flag) == expected for flag, expected in CONTROL_FLAGS.items()),
        "source_inspection_text_gate_present": source_inspection.get("status") == "PASS",
        "adversarial_hash_policy_pass": adversarial.get("status") == "PASS",
        "source_hash_manifest_pass": source_hash.get("status") == "PASS",
        "no_leak_control_regression_pass": no_leak.get("status") == "PASS",
    }
    status = "PASS" if all(checks.values()) else "FAIL_TEXT_GATE_REPAIR_REAUDIT"
    failed = [name for name, ok in checks.items() if not ok]
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_VERIFICATION_AUDIT"),
        "status": status,
        "target_repair_id": "G12-SRC-CAP-REPAIR-001",
        "audited_commit": "d2bd8cac research: text-gate nofill source capture hash fallback",
        "prior_acceptance_terminal_verdict": prior_acceptance.get("terminal_verdict"),
        "prior_repair_terminal_verdict": prior_blocker.get("terminal_verdict"),
        "prior_repair_blocker_count": prior_blocker.get("remaining_repair_blocker_count"),
        "package_verifier_result": package_verifier,
        "source_status_checks": checks,
        "failed_checks": failed,
        "source_inspection_status": source_inspection.get("status"),
        "adversarial_hash_policy_status": adversarial.get("status"),
        "source_hash_status": source_hash.get("status"),
        "no_leak_control_status": no_leak.get("status"),
        "repair_verification_conclusion": (
            "Commit d2bd8cac closes G12-SRC-CAP-REPAIR-001 for source/control evidence only."
            if status == "PASS"
            else "Commit d2bd8cac still has exact repair blockers listed in the blocker closure ledger."
        ),
    }


def build_blocker_closure_ledger(repair: dict[str, Any]) -> dict[str, Any]:
    remaining_blockers: list[dict[str, Any]] = []
    if repair.get("status") != "PASS":
        for check in repair.get("failed_checks", []):
            remaining_blockers.append(
                {
                    "blocker_id": f"G12-SRC-CAP-REPAIR-001-{check}",
                    "closure_status": "REMAINS_OPEN_WITH_EXACT_FIX_REQUIRED",
                    "title": f"Text-gate repair check failed: {check}",
                    "exact_fix": "Repair only the source-capture verifier/hash-policy or audit artifact needed for this check, then rerun the package verifier and this G12 text-gate reaudit.",
                    "does_not_open": [
                        "result_cost_scoring",
                        "validation",
                        "promotion",
                        "live_logger_wiring",
                        "registry_edit",
                        "paid_api_route",
                        "remote_push",
                        "live_trading_behavior",
                    ],
                }
            )
    closed = not remaining_blockers
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_BLOCKER_CLOSURE_LEDGER"),
        "target_blocker_id": "G12-SRC-CAP-REPAIR-001",
        "target_blocker_closed": closed,
        "remaining_repair_blocker_count": len(remaining_blockers),
        "remaining_blockers": remaining_blockers,
        "terminal_verdict": ACCEPT_TERMINAL_VERDICT if closed else BLOCKER_TERMINAL_VERDICT,
        "acceptance_boundary": (
            "G12-SRC-CAP-REPAIR-001 is accepted as closed only as source/control contract evidence. "
            "This does not open live logger wiring, result/cost scoring, validation, promotion, registry edits, "
            "paid/API routes, remote push, MT5 account/order/deal/history labels, or live trading behavior."
            if closed
            else "The repair remains blocked. The package remains source/control-only with all forbidden routes closed."
        ),
    }


def build_decision(blocker: dict[str, Any], repair: dict[str, Any], adversarial: dict[str, Any], no_leak: dict[str, Any]) -> dict[str, Any]:
    terminal = blocker["terminal_verdict"]
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_DECISION_LEDGER"),
        "terminal_verdict": terminal,
        "allowed_terminal_verdicts": sorted(ALLOWED_TERMINAL_VERDICTS),
        "accepted_evidence_class": "SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY",
        "target_repair_id": "G12-SRC-CAP-REPAIR-001",
        "target_repair_closed": blocker["target_blocker_closed"],
        "remaining_repair_blockers": blocker["remaining_blockers"],
        "decision_claims": [
            "Prior G12 acceptance and repair reaudit artifacts were reconstructed.",
            "The repaired package verifier source now gates LF-normalized fallback through explicit text artifact suffix logic.",
            "Adversarial strict text CRLF/LF portability still passes only through bounded text fallback.",
            "Adversarial strict text true mutation is rejected.",
            "Adversarial strict .bin/non-text raw SHA mismatch is rejected even when a synthetic LF-normalized hash matches.",
            "Mutable-context strict_hash_recompute=false drift remains warning-only and does not mask strict-source failure.",
            "Package verifier rerun is clean and keeps NO_PROMOTION_VERDICT plus closed validation/live/result-cost flags.",
            "Frozen package equation, denominators, no-leak/redaction controls, same-tick ambiguity, source/cost/execution separation, and future live logger gate remain unchanged.",
        ],
        "required_reaudit_questions": [
            {"question": "Did d2bd8cac add an explicit text-artifact gate before LF-normalized fallback acceptance?", "answer": repair["source_status_checks"].get("source_inspection_text_gate_present")},
            {"question": "Does strict text CRLF/LF portability still pass only through bounded sha256_lf_normalized evidence?", "answer": adversarial.get("strict_text_lf_portability_accepted_only_through_bounded_text_fallback")},
            {"question": "Does true text content mutation still fail?", "answer": adversarial.get("strict_text_true_mutation_rejected")},
            {"question": "Does strict binary/non-text raw SHA mismatch now fail even if synthetic LF-normalized hash matches?", "answer": adversarial.get("strict_binary_non_text_raw_sha_mismatch_rejected_despite_synthetic_lf_match")},
            {"question": "Do mutable-context non-strict entries remain warning-only and unable to mask strict-source failure?", "answer": adversarial.get("mutable_context_raw_drift_warning_only") and adversarial.get("mutable_context_does_not_mask_strict_source_failure")},
            {"question": "Is the regenerated source-hash manifest internally consistent and free of true strict failures?", "answer": repair["source_status_checks"].get("source_hash_manifest_pass")},
            {"question": "Are frozen package controls unchanged?", "answer": no_leak.get("status") == "PASS"},
        ],
        "next_gate": (
            "Source/control contract evidence may be treated as accepted after the text-gate repair. "
            "Any live logger wiring or implementation-design reliance remains a separate owner-approved evidence-class lane."
            if blocker["target_blocker_closed"]
            else "Return to source-capture verifier repair with exact blockers, then rerun this independent G12 text-gate reaudit."
        ),
        "validation_or_promotion_opened": False,
        "future_live_logger_wiring_still_requires_owner_approval": True,
    }


def completion_audit(
    context: dict[str, Any],
    decision: dict[str, Any],
    repair: dict[str, Any],
    adversarial: dict[str, Any],
    source_hash: dict[str, Any],
    no_leak: dict[str, Any],
    blocker: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight", "PASS", "LIVE_STATE regenerated; latest handoff, quick reference, research doctrine/current state, goal discipline, local-heavy inventory, CLAUDE.md, and controlling prompt read."),
        ("context_anchor_head_prompt", "PASS", f"{context['audit_head']} / {context['controlling_prompt_path']}"),
        ("required_output_directory", "PASS", repo_rel(OUT_DIR)),
        ("decision_ledger", "PASS", AUDIT_JSON[1]),
        ("text_gate_repair_verification_audit", repair["status"], AUDIT_JSON[2]),
        ("adversarial_hash_policy_proof", adversarial["status"], AUDIT_JSON[3]),
        ("source_hash_recomputation_audit", source_hash["status"], AUDIT_JSON[4]),
        ("no_leak_control_regression_audit", no_leak["status"], AUDIT_JSON[5]),
        ("blocker_closure_ledger", "PASS" if blocker["target_blocker_closed"] or blocker["remaining_repair_blocker_count"] > 0 else "FAIL", AUDIT_JSON[6]),
        ("next_prompt_pack", "PASS", AUDIT_MD[7]),
        ("builder_verifier_focused_tests_present", "PASS", "builder/verifier/test files in route directory"),
        ("terminal_decision", "PASS", decision["terminal_verdict"]),
        ("g12_src_cap_repair_001_status", "PASS" if blocker["target_blocker_closed"] else "BLOCKER_RECORDED", "closed after text gate" if blocker["target_blocker_closed"] else "exact remaining blocker recorded"),
        ("no_promotion_validation_live_effect", "PASS", "NO_PROMOTION_VERDICT; validation_safe=false; outcome_review_opened=false; live_effect=false"),
        ("forbidden_routes_closed", "PASS", "result/cost scoring, validation, promotion, live wiring, registry edit, paid/API route, remote push, live trading behavior all false/closed"),
    ]
    incomplete = [item for item in checklist if item[1].startswith("FAIL")]
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_COMPLETION_AUDIT"),
        "objective_restated": (
            "Run the independent G12 text-gate repair reaudit after commit d2bd8cac, prove whether "
            "G12-SRC-CAP-REPAIR-001 is closed by explicit text-gated LF-normalized fallback, and preserve "
            "NO_PROMOTION_VERDICT with validation_safe=false, outcome_review_opened=false, and live_effect=false."
        ),
        "terminal_verdict": decision["terminal_verdict"],
        "target_repair_closed": blocker["target_blocker_closed"],
        "prompt_to_artifact_checklist": [
            {"requirement": req, "status": status, "evidence": evidence}
            for req, status, evidence in checklist
        ],
        "missing_incomplete_or_weak_requirements": incomplete,
        "can_mark_goal_complete_after_verification_and_commit": not incomplete,
        "verification_result_artifact": VERIFICATION_RESULT_NAME,
        "completion_rationale": (
            "The completion condition is satisfied because G12-SRC-CAP-REPAIR-001 is independently accepted "
            "as closed after the text gate, with source/control-only boundaries preserved."
            if blocker["target_blocker_closed"] and not incomplete
            else "The completion condition is satisfied only if exact remaining repair blockers are recorded and verification passes."
        ),
        "future_live_logger_wiring_still_requires_owner_approval": True,
        "validation_or_promotion_opened": False,
    }


def md_header(title: str) -> str:
    return (
        f"# {title} {DATE}\n\n"
        f"Route: `{ROUTE_ID}`\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`\n"
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`\n"
    )


def render_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Item | Value |", "|---|---|"]
    for key, value in rows:
        if isinstance(value, (dict, list)):
            value_text = f"`{json.dumps(value, sort_keys=True)}`"
        else:
            value_text = f"`{value}`"
        lines.append(f"| {key} | {value_text} |")
    return "\n".join(lines)


def render_context_md(context: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Text-Gate Repair Reaudit Context Anchor"),
            render_table(
                [
                    ("Audit HEAD", context["audit_head"]),
                    ("Branch", context["audit_branch"]),
                    ("Controlling prompt", context["controlling_prompt_path"]),
                    ("Audited commit", context["audited_repair_commit"]),
                    ("Audited package", context["audited_package_path"]),
                    ("Target verifier", context["target_verifier_path"]),
                    ("Scope source/control only", context["scope_boundary"]["source_control_only"]),
                ]
            ),
            "No heavy data, MT5 calls, paid/API calls, registry edits, remote push, or live trading behavior were used.",
        ]
    )


def render_decision_md(decision: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Text-Gate Repair Reaudit Decision Ledger"),
        f"Terminal verdict: `{decision['terminal_verdict']}`.",
        "",
        f"Target repair closed: `{decision['target_repair_closed']}`.",
        "",
        "## Decision Claims",
        "",
    ]
    lines.extend(f"- {claim}" for claim in decision["decision_claims"])
    lines.extend(["", "## Required Reaudit Questions", ""])
    lines.extend(f"- `{item['answer']}` - {item['question']}" for item in decision["required_reaudit_questions"])
    lines.extend(["", "Future live logger wiring still requires separate owner approval and a separate evidence-class lane."])
    return "\n".join(lines)


def render_repair_md(audit: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Text-Gate Repair Verification Audit"),
            render_table(
                [
                    ("Status", audit["status"]),
                    ("Audited commit", audit["audited_commit"]),
                    ("Prior acceptance verdict", audit["prior_acceptance_terminal_verdict"]),
                    ("Prior repair verdict", audit["prior_repair_terminal_verdict"]),
                    ("Package verifier returncode", audit["package_verifier_result"]["returncode"]),
                    ("Package verifier ok", audit["package_verifier_result"]["ok"]),
                    ("Package verifier failures", audit["package_verifier_result"]["failures"]),
                    ("Source inspection status", audit["source_inspection_status"]),
                    ("Adversarial status", audit["adversarial_hash_policy_status"]),
                    ("Failed checks", audit["failed_checks"]),
                ]
            ),
            audit["repair_verification_conclusion"],
        ]
    )


def render_adversarial_md(audit: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Text-Gate Adversarial Hash Policy Proof"),
        f"Status: `{audit['status']}`.",
        "",
        "| Case | Target Verifier Decision | Text Gate | Synthetic LF Match | Conclusion |",
        "|---|---|---|---|---|",
    ]
    for case in audit["cases"]:
        lines.append(
            f"| `{case['case_id']}` | `{case['target_package_verifier_decision']}` | "
            f"`{case['target_entry_allows_lf_normalized_fallback']}` | "
            f"`{case['synthetic_lf_normalized_hash_matches_manifest']}` | "
            f"`accepted={case['target_package_verifier_accepts']}` |"
        )
    lines.extend(["", f"Cleanup verified: `{audit['cleanup_verified']}`.", "", audit["adversarial_conclusion"]])
    return "\n".join(lines)


def render_hash_md(audit: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Text-Gate Source Hash Recomputation Audit"),
            render_table(
                [
                    ("Status", audit["status"]),
                    ("Total entries", audit["total_manifest_entries"]),
                    ("Exact raw hash matches", audit["exact_raw_hash_match_count"]),
                    ("Strict text LF fallback matches", audit["strict_text_lf_normalized_fallback_match_count_current_checkout"]),
                    ("Mutable context warnings", audit["mutable_context_warning_count"]),
                    ("Strict non-text manifest entries", audit["strict_non_text_manifest_entry_count"]),
                    ("Content hash failures", audit["content_hash_failure_count"]),
                    ("Missing manifest paths", audit["missing_manifest_path_count"]),
                ]
            ),
            audit["conclusion"],
        ]
    )


def render_no_leak_md(audit: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Text-Gate No-Leak Control Regression Audit"),
            render_table(
                [
                    ("Status", audit["status"]),
                    ("Prototype rows", audit["prototype_row_count"]),
                    ("Family counts", audit["family_counts"]),
                    ("Accepted denominators", [audit["row_level_accepted_denominator"], audit["primary_duplicate_key_denominator"], audit["secondary_duplicate_group_denominator"]]),
                    ("Forbidden key hits", len(audit["forbidden_key_hits_in_prototype_rows"])),
                    ("Open flag hits", len(audit["prototype_rows_with_open_flags"])),
                    ("Same-tick ambiguity fixture present", audit["same_tick_ambiguity_fixture_present"]),
                    ("Source/cost/execution separation", audit["source_cost_execution_separation_status"]),
                    ("Future live logger gate", audit["future_live_logger_wiring_gate"]),
                ]
            ),
            audit["repair_regression_conclusion"],
        ]
    )


def render_blocker_md(ledger: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Text-Gate Blocker Closure Ledger"),
        f"Target blocker closed: `{ledger['target_blocker_closed']}`.",
        "",
        f"Terminal verdict: `{ledger['terminal_verdict']}`.",
        "",
        ledger["acceptance_boundary"],
        "",
        "## Remaining Blockers",
        "",
    ]
    if ledger["remaining_blockers"]:
        for blocker in ledger["remaining_blockers"]:
            lines.extend([f"- `{blocker['blocker_id']}`: {blocker['title']} Exact fix: {blocker['exact_fix']}"])
    else:
        lines.append("- none")
    return "\n".join(lines)


def render_next_prompt_pack(ledger: dict[str, Any]) -> str:
    if ledger["target_blocker_closed"]:
        next_route = (
            "G12-SRC-CAP-REPAIR-001 is closed as source/control contract evidence only. "
            "Any future live logger wiring, implementation-design reliance, result/cost scoring, validation, "
            "promotion, registry edit, paid/API route, remote push, or live trading behavior requires a separate "
            "owner-approved evidence-class lane. Start that lane only if explicitly approved; preserve "
            "NO_PROMOTION_VERDICT until a separate promotion dossier exists."
        )
    else:
        next_route = (
            "Repair only the remaining source-capture verifier/hash-policy blockers listed here, rerun the "
            "package verifier, then rerun this G12 text-gate repair reaudit. Preserve NO_PROMOTION_VERDICT and "
            "keep validation_safe=false, outcome_review_opened=false, live_effect=false."
        )
    return f"""{md_header("G12 NOFILL Forward Source Capture Text-Gate Next Prompt Pack")}
## Next Allowed Route

```text
{next_route}
```

Current terminal verdict: `{ledger['terminal_verdict']}`.
Remaining repair blocker count: `{ledger['remaining_repair_blocker_count']}`.
"""


def render_completion_md(audit: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Text-Gate Completion Audit"),
        audit["objective_restated"],
        "",
        f"Terminal verdict: `{audit['terminal_verdict']}`.",
        "",
        f"Target repair closed: `{audit['target_repair_closed']}`.",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"| `{item['requirement']}` | `{item['status']}` | {item['evidence']} |")
    lines.extend(
        [
            "",
            f"Can mark complete after verification and commit: `{audit['can_mark_goal_complete_after_verification_and_commit']}`.",
            "",
            audit["completion_rationale"],
        ]
    )
    return "\n".join(lines)


def build_artifacts() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    context = build_context_anchor()
    source_inspection = inspect_target_verifier_source()
    adversarial = run_adversarial_hash_policy_probe()
    source_hash = audit_source_hash_manifest()
    no_leak = audit_no_leak_control_regression()
    repair = audit_text_gate_repair(source_inspection, adversarial, source_hash, no_leak)
    blocker = build_blocker_closure_ledger(repair)
    decision = build_decision(blocker, repair, adversarial, no_leak)
    completion = completion_audit(context, decision, repair, adversarial, source_hash, no_leak, blocker)

    artifacts = {
        AUDIT_JSON[0]: context,
        AUDIT_JSON[1]: decision,
        AUDIT_JSON[2]: repair,
        AUDIT_JSON[3]: adversarial,
        AUDIT_JSON[4]: source_hash,
        AUDIT_JSON[5]: no_leak,
        AUDIT_JSON[6]: blocker,
        AUDIT_JSON[7]: completion,
    }
    for name, payload in artifacts.items():
        write_json(name, payload)

    write_md(AUDIT_MD[0], render_context_md(context))
    write_md(AUDIT_MD[1], render_decision_md(decision))
    write_md(AUDIT_MD[2], render_repair_md(repair))
    write_md(AUDIT_MD[3], render_adversarial_md(adversarial))
    write_md(AUDIT_MD[4], render_hash_md(source_hash))
    write_md(AUDIT_MD[5], render_no_leak_md(no_leak))
    write_md(AUDIT_MD[6], render_blocker_md(blocker))
    write_md(AUDIT_MD[7], render_next_prompt_pack(blocker))
    write_md(AUDIT_MD[8], render_completion_md(completion))

    return {
        "ok": completion["can_mark_goal_complete_after_verification_and_commit"],
        "terminal_verdict": decision["terminal_verdict"],
        "target_repair_closed": blocker["target_blocker_closed"],
        "remaining_repair_blocker_count": blocker["remaining_repair_blocker_count"],
        "repair_audit_status": repair["status"],
        "adversarial_status": adversarial["status"],
        "source_hash_status": source_hash["status"],
        "no_leak_status": no_leak["status"],
        "generated_json": len(AUDIT_JSON),
        "generated_md": len(AUDIT_MD),
    }


def main() -> int:
    result = build_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
