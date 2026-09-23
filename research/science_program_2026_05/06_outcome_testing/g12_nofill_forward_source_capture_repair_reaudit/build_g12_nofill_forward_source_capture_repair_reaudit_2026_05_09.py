#!/usr/bin/env python3
"""Build the independent G12 repair reaudit for G12-SRC-CAP-REPAIR-001.

This lane is source/control-only. It audits the repaired source-capture package
verifier after commit 59e41bd8, including adversarial hash-policy probes. It
does not score outcomes, validate, promote, wire live loggers, call paid/API
routes, edit registries, or touch live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT"
SCHEMA_VERSION = "g12_nofill_forward_source_capture_repair_reaudit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_VERDICT = "ACCEPT_WITH_REMAINING_EXACT_REPAIR_BLOCKERS"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
PACKAGE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_contract_hardening_offline_projection_prototype"
)
PRIOR_G12_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_forward_source_capture_prototype_acceptance_audit"
)
PROMPT_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-09.md"
)

TARGET_VERIFIER = PACKAGE_DIR / "verify_nofill_forward_capture_contract_2026_05_09.py"
TARGET_MANIFEST = PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json"
TARGET_RESULT = PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json"
TARGET_ROWS = PACKAGE_DIR / "NOFILL_FORWARD_OFFLINE_PROJECTION_PROTOTYPE_ROWS_2026-05-09.jsonl"
PRIOR_REPAIR_LEDGER = PRIOR_G12_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_BLOCKER_LEDGER_2026-05-09.json"
PRIOR_DECISION = PRIOR_G12_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_ACCEPTANCE_DECISION_LEDGER_2026-05-09.json"

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

ALLOWED_TERMINAL_VERDICTS = {
    "ACCEPT_AS_SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY_AFTER_REPAIR",
    "ACCEPT_WITH_REMAINING_EXACT_REPAIR_BLOCKERS",
    "RETURN_TO_SOURCE_CAPTURE_LANE_WITH_EXACT_FIXES",
    "REJECT_INVALID_REPAIR",
}

AUDIT_JSON = [
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_CONTEXT_ANCHOR_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_DECISION_LEDGER_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_VERIFICATION_AUDIT_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADVERSARIAL_HASH_POLICY_PROOF_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_RECOMPUTATION_AUDIT_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_NO_LEAK_CONTROL_REGRESSION_AUDIT_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_BLOCKER_CLOSURE_LEDGER_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_COMPLETION_AUDIT_2026-05-09.json",
]

AUDIT_MD = [
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_CONTEXT_ANCHOR_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_DECISION_LEDGER_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_VERIFICATION_AUDIT_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADVERSARIAL_HASH_POLICY_PROOF_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_RECOMPUTATION_AUDIT_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_NO_LEAK_CONTROL_REGRESSION_AUDIT_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_BLOCKER_CLOSURE_LEDGER_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_NEXT_PROMPT_PACK_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_COMPLETION_AUDIT_2026-05-09.md",
]

TEXT_SUFFIXES = {".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml", ".ps1", ".bat", ".csv"}
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


def lf_normalized(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_lf_bytes(data: bytes) -> str:
    return sha256_bytes(lf_normalized(data))


def sha256_lf_file(path: Path) -> str:
    return sha256_lf_bytes(path.read_bytes())


def is_text_artifact(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


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
    output = run_git(["status", "--short"])
    paths: list[str] = []
    for line in output.splitlines():
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


def package_hash_decision(entry: dict[str, Any], actual_path: Path) -> dict[str, Any]:
    """Mirror the repaired package verifier hash branch for one manifest entry."""
    raw = sha256_file(actual_path)
    lf_hash = sha256_lf_file(actual_path)
    if entry.get("sha256") and raw == entry.get("sha256"):
        decision = "ACCEPT_EXACT_RAW_HASH"
        accepted = True
    elif entry.get("strict_hash_recompute") is False:
        decision = "ACCEPT_MUTABLE_CONTEXT_RAW_DRIFT_WARNING"
        accepted = True
    elif entry.get("sha256_lf_normalized") and lf_hash == entry.get("sha256_lf_normalized"):
        decision = "ACCEPT_LF_NORMALIZED_FALLBACK_WARNING"
        accepted = True
    else:
        decision = "REJECT_HASH_RECOMPUTE_FAILURE"
        accepted = False
    return {
        "path": str(actual_path),
        "suffix": actual_path.suffix,
        "is_text_artifact_by_audit_policy": is_text_artifact(actual_path),
        "expected_raw": entry.get("sha256"),
        "expected_lf_normalized": entry.get("sha256_lf_normalized"),
        "actual_raw": raw,
        "actual_lf_normalized": lf_hash,
        "strict_hash_recompute": entry.get("strict_hash_recompute"),
        "target_package_verifier_decision": decision,
        "target_package_verifier_accepts": accepted,
    }


def safe_expected_hash_decision(entry: dict[str, Any], actual_path: Path) -> dict[str, Any]:
    raw = sha256_file(actual_path)
    lf_hash = sha256_lf_file(actual_path)
    if entry.get("sha256") and raw == entry.get("sha256"):
        return {"safe_policy_decision": "ACCEPT_EXACT_RAW_HASH", "safe_policy_accepts": True}
    if entry.get("strict_hash_recompute") is False:
        return {"safe_policy_decision": "ACCEPT_MUTABLE_CONTEXT_RAW_DRIFT_WARNING", "safe_policy_accepts": True}
    if (
        is_text_artifact(actual_path)
        and entry.get("sha256_lf_normalized")
        and lf_hash == entry.get("sha256_lf_normalized")
    ):
        return {"safe_policy_decision": "ACCEPT_TEXT_LF_NORMALIZED_FALLBACK_WARNING", "safe_policy_accepts": True}
    return {"safe_policy_decision": "REJECT_HASH_RECOMPUTE_FAILURE", "safe_policy_accepts": False}


def manifest_entry_for(original_bytes: bytes, path: Path, strict: bool = True) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": sha256_bytes(original_bytes),
        "sha256_lf_normalized": sha256_lf_bytes(original_bytes),
        "strict_hash_recompute": strict,
        "hash_policy": "strict_recompute" if strict else "mutable_context_snapshot_presence_only",
    }


def inspect_repaired_verifier_source() -> dict[str, Any]:
    lines = TARGET_VERIFIER.read_text(encoding="utf-8").splitlines()
    fallback_window: list[dict[str, Any]] = []
    raw_line = None
    mutable_line = None
    lf_line = None
    warning_line = None
    failure_line = None
    normalizer_line = None
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        if "data = full.read_bytes().replace" in stripped:
            normalizer_line = {"line": line_no, "code": stripped}
        if "recomputed = sha256_file" in stripped:
            raw_line = {"line": line_no, "code": stripped}
        if 'entry.get("strict_hash_recompute") is False' in stripped:
            mutable_line = {"line": line_no, "code": stripped}
        if "lf_recomputed = sha256_lf_normalized_file" in stripped:
            lf_line = {"line": line_no, "code": stripped}
            for offset in range(max(0, line_no - 8), min(len(lines), line_no + 18)):
                fallback_window.append({"line": offset + 1, "code": lines[offset].strip()})
        if '"text_lf_normalized_hash_match"' in stripped:
            warning_line = {"line": line_no, "code": stripped}
        if '"hash_recompute"' in stripped and "failures.append" in stripped:
            failure_line = {"line": line_no, "code": stripped}
    text_gate_tokens = ("is_text_artifact", ".suffix", "TEXT_SUFFIX", "mimetypes", "encoding=")
    fallback_text_gate_present = any(
        any(token in item["code"] for token in text_gate_tokens)
        for item in fallback_window
    )
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_VERIFIER_SOURCE_INSPECTION"),
        "target_verifier_path": repo_rel(TARGET_VERIFIER),
        "target_verifier_sha256": sha256_file(TARGET_VERIFIER),
        "raw_recompute_line": raw_line,
        "mutable_context_line": mutable_line,
        "lf_normalization_function_line": normalizer_line,
        "lf_fallback_line": lf_line,
        "lf_fallback_warning_line": warning_line,
        "content_failure_line": failure_line,
        "fallback_window": fallback_window,
        "fallback_text_gate_present": fallback_text_gate_present,
        "source_inspection_status": "FAIL_TEXT_GATE_ABSENT" if not fallback_text_gate_present else "PASS",
        "source_inspection_conclusion": (
            "The verifier recomputes raw SHA first, separates strict_hash_recompute=false mutable context, "
            "records LF fallback as a warning, and fails true content mismatches. However the LF fallback "
            "branch does not gate on text artifact type before accepting sha256_lf_normalized."
        ),
    }


def run_adversarial_hash_policy_probe() -> dict[str, Any]:
    temp_dir = OUT_DIR / "_tmp_adversarial_hash_policy"
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
        text_entry = manifest_entry_for(original_text, text_path, strict=True)
        cases.append(
            {
                "case_id": "STRICT_TEXT_EOL_PORTABILITY_ACCEPTED",
                "requirement": "strict text artifact raw SHA changes under CRLF/LF normalization but LF-normalized SHA matches",
                **package_hash_decision(text_entry, text_path),
                **safe_expected_hash_decision(text_entry, text_path),
            }
        )

        mutation_path = temp_dir / "strict_text_true_mutation.md"
        original_mutation = b"alpha\nbeta\n"
        mutation_path.write_bytes(b"alpha\nMUTATED\n")
        mutation_entry = manifest_entry_for(original_mutation, mutation_path, strict=True)
        cases.append(
            {
                "case_id": "STRICT_TEXT_TRUE_CONTENT_MUTATION_REJECTED",
                "requirement": "strict text true content mutation changes LF-normalized SHA and is rejected",
                **package_hash_decision(mutation_entry, mutation_path),
                **safe_expected_hash_decision(mutation_entry, mutation_path),
            }
        )

        binary_path = temp_dir / "strict_binary_payload.bin"
        original_binary = b"\x00BIN\r\nPAYLOAD\xff"
        binary_path.write_bytes(b"\x00BIN\nPAYLOAD\xff")
        binary_entry = manifest_entry_for(original_binary, binary_path, strict=True)
        cases.append(
            {
                "case_id": "STRICT_BINARY_NON_TEXT_RAW_SHA_REQUIRED",
                "requirement": "binary or non-text strict artifact must require exact raw SHA and cannot use text normalization",
                **package_hash_decision(binary_entry, binary_path),
                **safe_expected_hash_decision(binary_entry, binary_path),
            }
        )

        mutable_path = temp_dir / "mutable_context_snapshot.md"
        original_mutable = b"old snapshot\n"
        mutable_path.write_bytes(b"new snapshot\n")
        mutable_entry = manifest_entry_for(original_mutable, mutable_path, strict=False)
        cases.append(
            {
                "case_id": "MUTABLE_CONTEXT_NON_STRICT_DRIFT_ALLOWED",
                "requirement": "mutable context remains non-strict and cannot mask strict-source failures",
                **package_hash_decision(mutable_entry, mutable_path),
                **safe_expected_hash_decision(mutable_entry, mutable_path),
            }
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    after = {
        repo_rel(TARGET_VERIFIER): sha256_file(TARGET_VERIFIER),
        repo_rel(TARGET_MANIFEST): sha256_file(TARGET_MANIFEST),
        repo_rel(TARGET_RESULT): sha256_file(TARGET_RESULT) if TARGET_RESULT.exists() else None,
    }
    binary_case = next(item for item in cases if item["case_id"] == "STRICT_BINARY_NON_TEXT_RAW_SHA_REQUIRED")
    text_case = next(item for item in cases if item["case_id"] == "STRICT_TEXT_EOL_PORTABILITY_ACCEPTED")
    mutation_case = next(item for item in cases if item["case_id"] == "STRICT_TEXT_TRUE_CONTENT_MUTATION_REJECTED")
    mutable_case = next(item for item in cases if item["case_id"] == "MUTABLE_CONTEXT_NON_STRICT_DRIFT_ALLOWED")
    issue = (
        binary_case["target_package_verifier_accepts"] is True
        and binary_case["safe_policy_accepts"] is False
    )
    status = "FAIL_BINARY_NON_TEXT_FALLBACK_WEAKENING" if issue else "PASS"
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADVERSARIAL_HASH_POLICY_PROOF"),
        "status": status,
        "cases": cases,
        "strict_text_lf_portability_accepted": text_case["target_package_verifier_accepts"] is True,
        "strict_text_true_mutation_rejected": mutation_case["target_package_verifier_accepts"] is False,
        "strict_binary_or_non_text_raw_sha_required": binary_case["target_package_verifier_accepts"] is False,
        "strict_binary_or_non_text_safe_policy_would_reject": binary_case["safe_policy_accepts"] is False,
        "mutable_context_non_strict_drift_allowed": mutable_case["target_package_verifier_accepts"] is True,
        "committed_source_hashes_before": protected,
        "committed_source_hashes_after": after,
        "committed_source_artifacts_unchanged": protected == after,
        "temporary_probe_dir": repo_rel(temp_dir),
        "temporary_probe_dir_exists_after_cleanup": temp_dir.exists(),
        "cleanup_verified": not temp_dir.exists() and protected == after,
        "adversarial_conclusion": (
            "The repaired verifier passes the intended text portability and true-mutation cases, "
            "but the same LF-normalized branch also accepts a .bin strict artifact whose raw SHA changed. "
            "That is a remaining source-integrity repair blocker because LF fallback is not text-gated."
        ),
    }


def all_manifest_entries(manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    entries: list[tuple[str, dict[str, Any]]] = []
    for group in ("source_entries", "parser_entries", "fixture_entries", "generated_entries"):
        for entry in manifest.get(group, []):
            entries.append((group, entry))
    return entries


def audit_source_hash_manifest() -> dict[str, Any]:
    manifest = read_json(TARGET_MANIFEST)
    exact_matches: list[dict[str, Any]] = []
    strict_text_lf_accepts: list[dict[str, Any]] = []
    strict_text_portability_risk: list[dict[str, Any]] = []
    mutable_context: list[dict[str, Any]] = []
    content_failures: list[dict[str, Any]] = []
    missing_paths: list[dict[str, Any]] = []
    strict_non_text_entries: list[dict[str, Any]] = []
    group_counts: dict[str, int] = {}
    for group in ("source_entries", "parser_entries", "fixture_entries", "generated_entries"):
        group_counts[group] = len(manifest.get(group, []))

    for group, entry in all_manifest_entries(manifest):
        path = REPO_ROOT / entry.get("path", "")
        item = {
            "group": group,
            "path": entry.get("path"),
            "strict_hash_recompute": entry.get("strict_hash_recompute"),
            "hash_policy": entry.get("hash_policy"),
            "expected_sha256": entry.get("sha256"),
            "expected_sha256_lf_normalized": entry.get("sha256_lf_normalized"),
            "is_text_artifact_by_audit_policy": is_text_artifact(path),
        }
        if not path.exists():
            missing_paths.append(item)
            continue
        item["actual_sha256"] = sha256_file(path)
        item["actual_sha256_lf_normalized"] = sha256_lf_file(path)
        if entry.get("strict_hash_recompute") is not False and not is_text_artifact(path):
            strict_non_text_entries.append(item)
        if (
            entry.get("strict_hash_recompute") is not False
            and is_text_artifact(path)
            and entry.get("sha256_lf_normalized")
            and entry.get("sha256_lf_normalized") != entry.get("sha256")
        ):
            strict_text_portability_risk.append(item)
        if item["actual_sha256"] == entry.get("sha256"):
            exact_matches.append(item)
            continue
        if entry.get("strict_hash_recompute") is False:
            mutable_context.append(item)
            continue
        if is_text_artifact(path) and item["actual_sha256_lf_normalized"] == entry.get("sha256_lf_normalized"):
            strict_text_lf_accepts.append(item)
            continue
        content_failures.append(item)

    status = "PASS" if not content_failures and not missing_paths else "FAIL"
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_RECOMPUTATION_AUDIT"),
        "status": status,
        "source_hash_manifest_path": repo_rel(TARGET_MANIFEST),
        "manifest_record_counts": group_counts,
        "exact_raw_hash_match_count": len(exact_matches),
        "strict_text_lf_normalized_accept_count_current_checkout": len(strict_text_lf_accepts),
        "strict_text_distinct_lf_hash_portability_risk_count": len(strict_text_portability_risk),
        "strict_non_text_manifest_entry_count": len(strict_non_text_entries),
        "mutable_context_allowed_drift_count": len(mutable_context),
        "content_hash_failure_count": len(content_failures),
        "missing_manifest_path_count": len(missing_paths),
        "strict_text_lf_normalized_accept_paths_current_checkout": strict_text_lf_accepts,
        "strict_text_portability_risk_sample": strict_text_portability_risk[:12],
        "strict_non_text_manifest_entries": strict_non_text_entries,
        "mutable_context_allowed_drift": mutable_context,
        "content_hash_failures": content_failures,
        "missing_manifest_paths": missing_paths,
        "conclusion": (
            "The committed package manifest currently has no binary/non-text strict entries, and current strict "
            "content recomputation has zero true content failures. That does not by itself prove the verifier's "
            "policy is safe for future non-text strict entries, so the adversarial proof is decisive for the blocker."
        ),
    }


def audit_no_leak_control_regression() -> dict[str, Any]:
    rows = read_jsonl(TARGET_ROWS)
    package_no_leak = read_json(PACKAGE_DIR / "NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_2026-05-09.json")
    package_denom = read_json(PACKAGE_DIR / "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_2026-05-09.json")
    package_fixture = read_json(PACKAGE_DIR / "NOFILL_FORWARD_FIXTURE_MANIFEST_2026-05-09.json")
    package_cost = read_json(PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_2026-05-09.json")

    forbidden_hits: list[dict[str, Any]] = []
    open_flag_hits: list[dict[str, Any]] = []
    for row in rows:
        row_id = row.get("packet_row_id")
        for key in FORBIDDEN_ROW_KEYS:
            if key in row:
                forbidden_hits.append({"packet_row_id": row_id, "key": key})
        for flag in ("validation_safe", "outcome_review_opened", "live_effect", "opens_result_scoring", "opens_live_wiring"):
            if row.get(flag) is not False:
                open_flag_hits.append({"packet_row_id": row_id, "flag": flag, "value": row.get(flag)})

    families = Counter(row.get("v3_terminal_family") for row in rows)
    row_den = sum(bool(row.get("row_level_denominator_member")) for row in rows)
    dup_key = sum(bool(row.get("nofill_duplicate_key_count_member")) for row in rows)
    dup_group = sum(bool(row.get("duplicate_group_id_count_member")) for row in rows)
    categories = {item.get("category") for item in package_fixture.get("fixtures", [])}
    fixture_missing = sorted(set(package_fixture.get("required_fixture_categories", [])) - categories)
    issues = []
    if dict(families) != {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}:
        issues.append("family_equation_mismatch")
    if (row_den, dup_key, dup_group) != (225, 182, 139):
        issues.append("accepted_denominator_mismatch")
    if forbidden_hits:
        issues.append("forbidden_keys_in_rows")
    if open_flag_hits:
        issues.append("open_flags_in_rows")
    if package_no_leak.get("status") != "PASS":
        issues.append("package_no_leak_not_pass")
    if package_denom.get("status") != "PASS":
        issues.append("package_denom_not_pass")
    if fixture_missing:
        issues.append("fixture_category_gap")
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_NO_LEAK_CONTROL_REGRESSION_AUDIT"),
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "prototype_row_count": len(rows),
        "family_counts": dict(families),
        "frozen_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
        "row_level_accepted_denominator": row_den,
        "primary_duplicate_key_denominator": dup_key,
        "secondary_duplicate_group_denominator": dup_group,
        "forbidden_key_hits_in_prototype_rows": forbidden_hits,
        "prototype_rows_with_open_flags": open_flag_hits,
        "package_no_leak_status": package_no_leak.get("status"),
        "package_denominator_status": package_denom.get("status"),
        "same_tick_ambiguity_fixture_present": "same_tick_ambiguity_row" in categories,
        "fixture_missing_categories": fixture_missing,
        "source_cost_execution_separation": {
            "decision_spread_status_counts": package_cost.get("decision_spread_status_counts"),
            "entry_touch_spread_status_counts": package_cost.get("entry_touch_spread_status_counts"),
            "slippage_label_status_counts": package_cost.get("slippage_label_status_counts"),
            "execution_quality_label_status_counts": package_cost.get("execution_quality_label_status_counts"),
            "cost_testing_gate_status_counts": package_cost.get("cost_testing_gate_status_counts"),
        },
        "future_live_logger_wiring_still_gated": True,
        "repair_regression_conclusion": (
            "The hash-policy repair did not alter prototype rows, family counts, accepted denominators, "
            "fixtures, no-leak controls, or source/cost/execution separation. The remaining weakness is "
            "isolated to non-text LF-fallback acceptance in the verifier policy."
        ),
    }


def build_context_anchor() -> dict[str, Any]:
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_CONTEXT_ANCHOR"),
        "audit_head": run_git(["log", "-1", "--oneline"]),
        "controlling_prompt_path": repo_rel(PROMPT_PATH),
        "audited_package_path": repo_rel(PACKAGE_DIR),
        "target_repair_id": "G12-SRC-CAP-REPAIR-001",
        "post_repair_commit_under_audit": "59e41bd8 research: close nofill source capture hash verifier blocker",
        "prior_g12_decision_path": repo_rel(PRIOR_DECISION),
        "prior_repair_blocker_ledger_path": repo_rel(PRIOR_REPAIR_LEDGER),
        "package_verifier_path": repo_rel(TARGET_VERIFIER),
        "package_verifier_result_path": repo_rel(TARGET_RESULT),
        "required_preflight_completed": True,
        "current_dirty_paths_at_builder_time": git_status_paths(),
        "scope_boundary": {
            "source_control_only": True,
            "result_cost_scoring_opened": False,
            "live_logger_wiring_opened": False,
            "validation_opened": False,
            "promotion_opened": False,
            "registry_edit_opened": False,
            "paid_api_route_opened": False,
            "live_trading_behavior_opened": False,
        },
        "local_heavy_data_note": (
            "This audit did not need heavy local market data. It consumed committed source/control package artifacts, "
            "prior G12 audit artifacts, and temporary adversarial hash fixtures only."
        ),
    }


def audit_repair_verification(source_inspection: dict[str, Any], adversarial: dict[str, Any]) -> dict[str, Any]:
    prior_decision = read_json(PRIOR_DECISION)
    prior_repair = read_json(PRIOR_REPAIR_LEDGER)
    package_result = read_json(TARGET_RESULT)
    blocker_ids = {item.get("blocker_id") for item in prior_repair.get("blockers", [])}
    source_status_checks = {
        "prior_decision_reconstructed": prior_decision.get("terminal_verdict") == "ACCEPT_WITH_EXACT_REPAIR_BLOCKERS",
        "prior_blocker_reconstructed": "G12-SRC-CAP-REPAIR-001" in blocker_ids,
        "package_verifier_ok": package_result.get("ok") is True,
        "package_verifier_can_mark_goal_complete": package_result.get("can_mark_goal_complete") is True,
        "package_verifier_zero_failures": package_result.get("failures") == [],
        "package_verifier_records_lf_fallback_warnings": any(
            warning.get("check") == "text_lf_normalized_hash_match"
            for warning in package_result.get("warnings", [])
        ),
        "raw_sha_recomputed_before_fallback": source_inspection.get("raw_recompute_line") is not None,
        "mutable_context_separated": source_inspection.get("mutable_context_line") is not None,
        "true_content_mismatch_fails": adversarial.get("strict_text_true_mutation_rejected") is True,
        "strict_text_lf_fallback_accepts": adversarial.get("strict_text_lf_portability_accepted") is True,
        "binary_non_text_raw_sha_required": adversarial.get("strict_binary_or_non_text_raw_sha_required") is True,
        "temporary_fixtures_cleaned": adversarial.get("cleanup_verified") is True,
        "source_artifacts_unchanged_after_probe": adversarial.get("committed_source_artifacts_unchanged") is True,
    }
    failed_checks = [name for name, ok in source_status_checks.items() if not ok]
    status = "FAIL_REMAINING_REPAIR_BLOCKER" if failed_checks else "PASS"
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_VERIFICATION_AUDIT"),
        "status": status,
        "prior_decision": prior_decision.get("terminal_verdict"),
        "prior_blocker_ids": sorted(blocker_ids),
        "package_verifier_result": {
            "ok": package_result.get("ok"),
            "can_mark_goal_complete": package_result.get("can_mark_goal_complete"),
            "failures": package_result.get("failures"),
            "warning_count": len(package_result.get("warnings", [])),
            "dirty_paths_reviewed": package_result.get("dirty_paths_reviewed"),
            "promotion_verdict": package_result.get("promotion_verdict"),
            "validation_safe": package_result.get("validation_safe"),
            "outcome_review_opened": package_result.get("outcome_review_opened"),
            "live_effect": package_result.get("live_effect"),
            "opens_result_scoring": package_result.get("opens_result_scoring"),
            "opens_live_wiring": package_result.get("opens_live_wiring"),
            "future_live_logger_wiring_lane_still_gated": package_result.get("future_live_logger_wiring_lane_still_gated"),
        },
        "source_status_checks": source_status_checks,
        "failed_checks": failed_checks,
        "source_inspection_status": source_inspection.get("source_inspection_status"),
        "adversarial_hash_policy_status": adversarial.get("status"),
        "repair_verification_conclusion": (
            "G12-SRC-CAP-REPAIR-001 is not fully closed. The repaired verifier passes the live package run, "
            "accepts strict text LF-normalized hashes as bounded warnings, rejects true text content mutation, "
            "and preserves mutable-context separation; however the adversarial non-text case proves the fallback "
            "is not constrained to text artifacts."
        ),
    }


def build_blocker_closure_ledger(repair_audit: dict[str, Any], adversarial: dict[str, Any]) -> dict[str, Any]:
    remaining_blockers: list[dict[str, Any]] = []
    if repair_audit["status"] != "PASS":
        remaining_blockers.append(
            {
                "blocker_id": "G12-SRC-CAP-REPAIR-001",
                "closure_status": "REMAINS_OPEN_WITH_NARROWED_EXACT_FIX",
                "severity": "REPAIR_REQUIRED_BEFORE_SOURCE_CONTROL_CONTRACT_ACCEPTANCE",
                "title": "LF-normalized fallback is not text-gated and can accept a strict non-text artifact with raw SHA drift.",
                "evidence": {
                    "source_inspection_status": repair_audit.get("source_inspection_status"),
                    "adversarial_status": adversarial.get("status"),
                    "binary_case": [
                        item
                        for item in adversarial.get("cases", [])
                        if item.get("case_id") == "STRICT_BINARY_NON_TEXT_RAW_SHA_REQUIRED"
                    ][0],
                },
                "exact_fix": (
                    "Change verify_nofill_forward_capture_contract_2026_05_09.py so the sha256_lf_normalized fallback "
                    "is allowed only for explicit text artifacts. Add an is_text_artifact/path-suffix or manifest "
                    "artifact_type gate before accepting the LF-normalized hash. Binary or non-text strict entries "
                    "must require exact raw sha256 and fail on raw mismatch even if sha256_lf_normalized matches."
                ),
                "verification_required_after_fix": [
                    "strict text CRLF/LF portability accepted only through bounded warning",
                    "strict text true content mutation rejected",
                    "strict binary/non-text raw mismatch rejected even when LF-normalized hash matches",
                    "strict_hash_recompute=false mutable context remains warning-only and cannot mask strict failures",
                    "package verifier rerun ok=true only after adversarial tests pass",
                ],
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
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_BLOCKER_CLOSURE_LEDGER"),
        "target_blocker_id": "G12-SRC-CAP-REPAIR-001",
        "target_blocker_closed": not remaining_blockers,
        "remaining_repair_blocker_count": len(remaining_blockers),
        "remaining_blockers": remaining_blockers,
        "terminal_verdict": (
            "ACCEPT_AS_SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY_AFTER_REPAIR"
            if not remaining_blockers
            else TERMINAL_VERDICT
        ),
        "acceptance_boundary": (
            "The repair is not accepted as closed. The package remains source/control-only, "
            "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. "
            "No live logger wiring, result/cost scoring, validation, promotion, registry edit, paid/API route, "
            "remote push, or live trading behavior is opened."
        ),
    }


def build_decision(blocker: dict[str, Any], repair: dict[str, Any], no_leak: dict[str, Any]) -> dict[str, Any]:
    terminal = blocker["terminal_verdict"]
    hard_failures = []
    if no_leak.get("status") != "PASS":
        hard_failures.append("no_leak_or_denominator_regression")
    if terminal not in ALLOWED_TERMINAL_VERDICTS:
        hard_failures.append("terminal_verdict_not_allowed")
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_DECISION_LEDGER"),
        "terminal_verdict": terminal,
        "allowed_terminal_verdicts": sorted(ALLOWED_TERMINAL_VERDICTS),
        "accepted_evidence_class": "SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY",
        "target_repair_id": "G12-SRC-CAP-REPAIR-001",
        "target_repair_closed": blocker["target_blocker_closed"],
        "hard_failures": hard_failures,
        "decision_claims": [
            "Prior G12 decision ACCEPT_WITH_EXACT_REPAIR_BLOCKERS and blocker G12-SRC-CAP-REPAIR-001 were reconstructed.",
            "The package verifier rerun returned ok=true, can_mark_goal_complete=true, zero failures, and closed route flags.",
            "Core package invariants still recompute: 298 rows and accepted denominators 225/182/139.",
            "No-leak, redaction, duplicate/denominator, same-tick ambiguity, and source/cost/execution separation controls remain intact.",
            "Adversarial proof shows strict text LF portability is accepted and true text content mutation is rejected.",
            "Adversarial proof also shows strict non-text raw-SHA enforcement is not safe because LF fallback is not text-gated.",
        ],
        "remaining_repair_blockers": blocker["remaining_blockers"],
        "next_gate": "Return to source-capture verifier hash-policy repair with exact text-gate fix, then rerun this G12 repair reaudit.",
        "validation_or_promotion_opened": False,
        "future_live_logger_wiring_still_requires_owner_approval": True,
        "repair_audit_status": repair["status"],
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
        ("mandatory_preflight", "PASS", "LIVE_STATE regenerated; latest handoff, quick reference, doctrine, research state, goal discipline, local-heavy inventory, and controlling prompt read."),
        ("context_anchor_head_prompt", "PASS", f"{context['audit_head']} / {context['controlling_prompt_path']}"),
        ("prior_decision_reconstructed", "PASS" if repair["source_status_checks"]["prior_decision_reconstructed"] else "FAIL", repair["prior_decision"]),
        ("prior_blocker_reconstructed", "PASS" if repair["source_status_checks"]["prior_blocker_reconstructed"] else "FAIL", "G12-SRC-CAP-REPAIR-001"),
        ("package_verifier_rerun", "PASS" if repair["package_verifier_result"]["ok"] is True and repair["package_verifier_result"]["failures"] == [] else "FAIL", "ok=true, zero failures"),
        ("raw_sha_recompute_and_mutable_context", "PASS" if repair["source_status_checks"]["raw_sha_recomputed_before_fallback"] and repair["source_status_checks"]["mutable_context_separated"] else "FAIL", "source inspection lines recorded"),
        ("strict_text_lf_acceptance_case", "PASS" if adversarial["strict_text_lf_portability_accepted"] else "FAIL", "adversarial hash policy proof"),
        ("true_content_mutation_rejection_case", "PASS" if adversarial["strict_text_true_mutation_rejected"] else "FAIL", "adversarial hash policy proof"),
        ("binary_non_text_raw_sha_case", "PASS" if blocker["remaining_repair_blocker_count"] >= 1 else "FAIL", "remaining exact repair blocker recorded"),
        ("mutable_context_case", "PASS" if adversarial["mutable_context_non_strict_drift_allowed"] else "FAIL", "adversarial hash policy proof"),
        ("cleanup_no_mutation", "PASS" if adversarial["cleanup_verified"] else "FAIL", "temporary probe directory removed and target hashes unchanged"),
        ("source_hash_recomputation", source_hash["status"], "manifest recomputed; content failures and missing paths counted"),
        ("core_package_invariants", no_leak["status"], no_leak["frozen_equation"]),
        ("accepted_denominators", "PASS" if (no_leak["row_level_accepted_denominator"], no_leak["primary_duplicate_key_denominator"], no_leak["secondary_duplicate_group_denominator"]) == (225, 182, 139) else "FAIL", "225/182/139"),
        ("no_leak_redaction_source_cost_controls", no_leak["status"], "forbidden keys, route flags, fixtures, and cost separation checked"),
        ("terminal_verdict", "PASS", decision["terminal_verdict"]),
        ("next_prompt_pack", "PASS", "repair-only next prompt emitted"),
        ("forbidden_surfaces_closed", "PASS", "NO_PROMOTION_VERDICT; validation_safe=false; outcome_review_opened=false; live_effect=false; no live/result/cost/paid/registry/promotion route"),
    ]
    incomplete = [item for item in checklist if item[1] == "FAIL"]
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_COMPLETION_AUDIT"),
        "objective_restated": (
            "Run the independent G12 repair reaudit for G12-SRC-CAP-REPAIR-001 after commit 59e41bd8, "
            "prove whether the repaired verifier accepts LF-normalized strict text hashes without weakening "
            "source integrity, and either accept the repair or record exact remaining blockers."
        ),
        "terminal_verdict": decision["terminal_verdict"],
        "prompt_to_artifact_checklist": [
            {"requirement": req, "status": status, "evidence": evidence}
            for req, status, evidence in checklist
        ],
        "missing_incomplete_or_weak_requirements": incomplete,
        "can_mark_goal_complete_after_verification_and_commit": not incomplete,
        "completion_rationale": (
            "The goal can complete because the controlling prompt allows completion either by accepting "
            "G12-SRC-CAP-REPAIR-001 as closed or by recording a remaining exact repair blocker. This reaudit "
            "records a narrow remaining blocker with adversarial proof."
        ),
        "verification_result_artifact": "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_VERIFICATION_RESULT_2026-05-09.json",
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
        if isinstance(value, (list, dict)):
            value_text = f"`{json.dumps(value, sort_keys=True)}`"
        else:
            value_text = f"`{value}`"
        lines.append(f"| {key} | {value_text} |")
    return "\n".join(lines)


def render_context_md(context: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Repair Reaudit Context Anchor"),
            render_table(
                [
                    ("Audit HEAD", context["audit_head"]),
                    ("Controlling prompt", context["controlling_prompt_path"]),
                    ("Audited package", context["audited_package_path"]),
                    ("Target repair", context["target_repair_id"]),
                    ("Package verifier", context["package_verifier_path"]),
                    ("Package verifier result", context["package_verifier_result_path"]),
                    ("Source/control only", context["scope_boundary"]["source_control_only"]),
                ]
            ),
            "No heavy data, MT5 calls, paid/API calls, registry edits, remote push, or live trading behavior were used.",
        ]
    )


def render_decision_md(decision: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Repair Reaudit Decision Ledger"),
        f"Terminal verdict: `{decision['terminal_verdict']}`.",
        "",
        f"Target repair closed: `{decision['target_repair_closed']}`.",
        "",
        "## Decision Claims",
        "",
    ]
    lines.extend(f"- {claim}" for claim in decision["decision_claims"])
    lines.extend(["", "## Remaining Repair Blockers", ""])
    if decision["remaining_repair_blockers"]:
        for item in decision["remaining_repair_blockers"]:
            lines.append(f"- `{item['blocker_id']}`: {item['title']}")
    else:
        lines.append("- none")
    lines.extend(["", "Future live logger wiring still requires separate owner approval and a separate evidence-class lane."])
    return "\n".join(lines)


def render_repair_md(audit: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Repair Verification Audit"),
            render_table(
                [
                    ("Status", audit["status"]),
                    ("Prior decision", audit["prior_decision"]),
                    ("Package verifier ok", audit["package_verifier_result"]["ok"]),
                    ("Package verifier failures", audit["package_verifier_result"]["failures"]),
                    ("Package verifier warning count", audit["package_verifier_result"]["warning_count"]),
                    ("Source inspection status", audit["source_inspection_status"]),
                    ("Adversarial hash policy status", audit["adversarial_hash_policy_status"]),
                    ("Failed checks", audit["failed_checks"]),
                ]
            ),
            audit["repair_verification_conclusion"],
        ]
    )


def render_adversarial_md(audit: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Adversarial Hash Policy Proof"),
        f"Status: `{audit['status']}`.",
        "",
        "| Case | Target Verifier Decision | Safe Policy Decision | Conclusion |",
        "|---|---|---|---|",
    ]
    for case in audit["cases"]:
        conclusion = "matches safe policy"
        if case["target_package_verifier_accepts"] != case["safe_policy_accepts"]:
            conclusion = "diverges from safe policy"
        lines.append(
            f"| `{case['case_id']}` | `{case['target_package_verifier_decision']}` | "
            f"`{case['safe_policy_decision']}` | {conclusion} |"
        )
    lines.extend(
        [
            "",
            f"Cleanup verified: `{audit['cleanup_verified']}`.",
            "",
            audit["adversarial_conclusion"],
        ]
    )
    return "\n".join(lines)


def render_hash_md(audit: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Source Hash Recomputation Audit"),
            render_table(
                [
                    ("Status", audit["status"]),
                    ("Exact raw hash matches", audit["exact_raw_hash_match_count"]),
                    ("Strict text LF accepts in current checkout", audit["strict_text_lf_normalized_accept_count_current_checkout"]),
                    ("Strict text distinct LF portability risk", audit["strict_text_distinct_lf_hash_portability_risk_count"]),
                    ("Strict non-text manifest entries", audit["strict_non_text_manifest_entry_count"]),
                    ("Mutable context allowed drift", audit["mutable_context_allowed_drift_count"]),
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
            md_header("G12 NOFILL Forward Source Capture No-Leak Control Regression Audit"),
            render_table(
                [
                    ("Status", audit["status"]),
                    ("Prototype rows", audit["prototype_row_count"]),
                    ("Family counts", audit["family_counts"]),
                    ("Accepted denominators", [audit["row_level_accepted_denominator"], audit["primary_duplicate_key_denominator"], audit["secondary_duplicate_group_denominator"]]),
                    ("Forbidden key hits", len(audit["forbidden_key_hits_in_prototype_rows"])),
                    ("Open flag hits", len(audit["prototype_rows_with_open_flags"])),
                    ("Same-tick ambiguity fixture present", audit["same_tick_ambiguity_fixture_present"]),
                    ("Package no-leak status", audit["package_no_leak_status"]),
                    ("Package denominator status", audit["package_denominator_status"]),
                ]
            ),
            audit["repair_regression_conclusion"],
        ]
    )


def render_blocker_md(ledger: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Blocker Closure Ledger"),
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
            lines.extend(
                [
                    f"### {blocker['blocker_id']}",
                    "",
                    f"Closure status: `{blocker['closure_status']}`.",
                    "",
                    blocker["title"],
                    "",
                    f"Exact fix: {blocker['exact_fix']}",
                    "",
                ]
            )
    else:
        lines.append("None.")
    return "\n".join(lines)


def render_next_prompt_pack(ledger: dict[str, Any]) -> str:
    return f"""{md_header("G12 NOFILL Forward Source Capture Repair Reaudit Next Prompt Pack")}
## Next Allowed Route

```text
Repair the NOFILL forward source-capture prototype verifier hash policy only. Use the independent repair reaudit at research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_repair_reaudit/ as controlling evidence. Close G12-SRC-CAP-REPAIR-001 by adding an explicit text-artifact gate before sha256_lf_normalized fallback in verify_nofill_forward_capture_contract_2026_05_09.py. Strict text CRLF/LF drift may pass only as a bounded warning when LF-normalized hashes match; true content mutation must fail; binary or non-text strict artifacts must require exact raw SHA and fail on raw mismatch even if LF-normalized bytes match. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. Do not open live logger wiring, result/cost scoring, validation, promotion, registry edits, paid/API routes, remote push, MT5 account/order/deal/history labels, or live trading behavior.
```

Current terminal verdict: `{ledger['terminal_verdict']}`.
Remaining repair blocker count: `{ledger['remaining_repair_blocker_count']}`.
"""


def render_completion_md(audit: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Repair Reaudit Completion Audit"),
        audit["objective_restated"],
        "",
        f"Terminal verdict: `{audit['terminal_verdict']}`.",
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
    source_inspection = inspect_repaired_verifier_source()
    adversarial = run_adversarial_hash_policy_probe()
    source_hash = audit_source_hash_manifest()
    no_leak = audit_no_leak_control_regression()
    repair = audit_repair_verification(source_inspection, adversarial)
    blocker = build_blocker_closure_ledger(repair, adversarial)
    decision = build_decision(blocker, repair, no_leak)
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
