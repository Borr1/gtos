"""Verifier for the NOFILL source-expansion parser-hash repair route."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = ROUTE_DIR.parent
REPO_ROOT = Path(__file__).resolve().parents[4]

DATE = "2026-05-10"
PREFIX = "NOFILL_HIST_SRCEXP_HASH_REPAIR"
TARGET_PREFIX = "NOFILL_HIST_SOURCE_EXPANSION"
ROUTE_ID = "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD"
SCHEMA_VERSION = "nofill_historical_source_expansion_packet_parser_hash_repair_rebuild_v1"
TERMINAL_DECISION = "REPAIR_REBUILD_READY_FOR_G12_REAUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

TARGET_DIR = OUTCOME_DIR / "nofill_historical_source_expansion_builder_local_tick_shadow_packet"
G12_DIR = OUTCOME_DIR / "g12_nofill_historical_source_expansion_packet_audit"
TARGET_PACKET = TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_{DATE}.jsonl"
TARGET_PACKET_MANIFEST = TARGET_DIR / f"{TARGET_PREFIX}_CANDIDATE_PACKET_MANIFEST_{DATE}.json"
TARGET_SOURCE_MANIFEST = TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_HASH_MANIFEST_{DATE}.json"
TARGET_PARSER_ASOF = TARGET_DIR / f"{TARGET_PREFIX}_PARSER_ASOF_MANIFEST_{DATE}.json"
TARGET_OUTPUT_MANIFEST = TARGET_DIR / f"{TARGET_PREFIX}_OUTPUT_MANIFEST_{DATE}.json"
TARGET_VERIFIER = TARGET_DIR / "verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"
TARGET_TEST = TARGET_DIR / "test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"
G12_REPAIR_LEDGER = G12_DIR / "G12_NOFILL_HIST_SRCEXP_AUDIT_EXACT_REPAIR_SOURCE_REQUIREMENT_LEDGER_2026-05-10.json"

TARGET_FILES = {
    "parser_or_verifier:builder": TARGET_DIR
    / "build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
    "parser_or_verifier:focused_tests": TARGET_TEST,
    "parser_or_verifier:verifier": TARGET_VERIFIER,
}
SAFE_FLAG_FALSE_KEYS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_TRUE_KEYS = (
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
FORBIDDEN_DIFF_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "canaries/",
)
EXPECTED_ROW_IDENTITIES = [
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


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def with_safe_flags(payload: dict[str, Any]) -> dict[str, Any]:
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(with_safe_flags(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any]) -> None:
    path.write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"Route: `{ROUTE_ID}`",
                f"Terminal decision: `{payload.get('terminal_decision', TERMINAL_DECISION)}`",
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
                "",
                "## Summary",
                "",
                "```json",
                json.dumps(with_safe_flags(payload), indent=2, sort_keys=True),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def scan_safe_flags(obj: Any, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key in SAFE_FLAG_FALSE_KEYS and value is not False:
                issues.append(f"{child} must be false")
            if key in FORBIDDEN_TRUE_KEYS and value is True:
                issues.append(f"{child} opens forbidden surface")
            if key == "promotion_verdict" and value != PROMOTION_VERDICT:
                issues.append(f"{child} must be {PROMOTION_VERDICT}")
            issues.extend(scan_safe_flags(value, child))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            issues.extend(scan_safe_flags(item, f"{path}[{idx}]"))
    return issues


def parse_artifacts() -> list[str]:
    issues: list[str] = []
    for path in list(ROUTE_DIR.glob("*.json")) + list(TARGET_DIR.glob(f"{TARGET_PREFIX}_*.json")):
        try:
            issues.extend(scan_safe_flags(load_json(path), rel(path)))
        except Exception as exc:  # pragma: no cover
            issues.append(f"{rel(path)} JSON parse failed: {exc}")
    for path in [TARGET_PACKET]:
        try:
            for idx, row in enumerate(read_jsonl(path), start=1):
                issues.extend(scan_safe_flags(row, f"{rel(path)}:{idx}"))
        except Exception as exc:  # pragma: no cover
            issues.append(f"{rel(path)} JSONL parse failed: {exc}")
    for path in ROUTE_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "NO_PROMOTION_VERDICT" not in text:
            issues.append(f"{rel(path)} missing NO_PROMOTION_VERDICT")
        if "validation_safe=true" in text or "outcome_review_opened=true" in text or "live_effect=true" in text:
            issues.append(f"{rel(path)} contains true safe flag text")
    return issues


def target_source_manifest_record(role: str) -> dict[str, Any]:
    manifest = load_json(TARGET_SOURCE_MANIFEST)
    for record in manifest.get("records", []):
        if record.get("role") == role:
            return record
    return {}


def verify_exact_hash_closure() -> list[str]:
    issues: list[str] = []
    ledger = load_json(G12_REPAIR_LEDGER)
    requirements = ledger.get("remaining_requirements", [])
    if len(requirements) != 3:
        issues.append(f"expected 3 G12 repair requirements, found {len(requirements)}")
    builder_hash = sha256_file(TARGET_FILES["parser_or_verifier:builder"])
    parser_manifest = load_json(TARGET_PARSER_ASOF)
    if parser_manifest.get("parser_hash") != builder_hash:
        issues.append("target parser_asof manifest does not match current builder hash")
    rows = read_jsonl(TARGET_PACKET)
    parser_hashes = sorted({row.get("parser_code_hash") for row in rows})
    if parser_hashes != [builder_hash]:
        issues.append(f"packet rows parser_code_hash mismatch: {parser_hashes} != {builder_hash}")
    for requirement in requirements:
        role = requirement.get("role")
        target_file = TARGET_FILES.get(role)
        if not target_file:
            issues.append(f"unexpected repair role: {role}")
            continue
        actual = sha256_file(target_file)
        manifest_sha = target_source_manifest_record(str(role)).get("sha256")
        if actual != manifest_sha:
            issues.append(f"target source manifest still mismatches {role}")
    closure = load_json(ROUTE_DIR / f"{PREFIX}_EXACT_G12_BLOCKER_CLOSURE_LEDGER_{DATE}.json")
    if closure.get("closed_requirement_count") != 3:
        issues.append("repair closure ledger does not close all 3 requirements")
    return issues


def verify_packet_and_semantics() -> list[str]:
    issues: list[str] = []
    rows = read_jsonl(TARGET_PACKET)
    identities = [
        {
            "packet_row_id": row.get("packet_row_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "candidate_id": row.get("candidate_id"),
        }
        for row in rows
    ]
    if identities != EXPECTED_ROW_IDENTITIES:
        issues.append(f"target row identities changed: {identities}")
    target_output = load_json(TARGET_OUTPUT_MANIFEST)
    if target_output.get("admitted_packet_row_count") != 2:
        issues.append("target admitted row count changed")
    if target_output.get("blocked_candidate_count") != 37:
        issues.append("target blocked candidate count changed")
    if target_output.get("rejected_candidate_count") != 9:
        issues.append("target rejected candidate count changed")
    manifest = load_json(TARGET_PACKET_MANIFEST)
    packet_sha = sha256_file(TARGET_PACKET)
    if manifest.get("packet_sha256") != packet_sha:
        issues.append("target packet manifest packet_sha256 does not match packet file")
    semantic = load_json(ROUTE_DIR / f"{PREFIX}_SEMANTIC_NO_ROW_CHANGE_DIFF_LEDGER_{DATE}.json")
    if semantic.get("terminal_decision") != TERMINAL_DECISION:
        issues.append("semantic no-row-change ledger did not accept repair")
    if semantic.get("semantic_counts_unchanged") is not True:
        issues.append("semantic counts changed")
    if semantic.get("only_hash_derived_fields_changed") is not True:
        issues.append("repair changed fields outside hash-derived packet fields")
    packet_ledger = load_json(ROUTE_DIR / f"{PREFIX}_PACKET_SHA_LEDGER_{DATE}.json")
    if packet_ledger.get("packet_sha_matches_manifest") is not True:
        issues.append("repair packet SHA ledger does not match manifest")
    return issues


def run_command(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-6000:],
        "stderr_tail": result.stderr[-6000:],
    }


def run_target_verifier_tests() -> dict[str, Any]:
    target_verifier = run_command([sys.executable, str(TARGET_VERIFIER)])
    target_pytest = run_command([sys.executable, "-m", "pytest", str(TARGET_TEST), "-q", "-p", "no:cacheprovider"])
    report = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "target_verifier_test_rerun_report",
            "target_verifier_was_run": True,
            "target_focused_pytest_was_run": True,
            "target_verifier_run": target_verifier,
            "target_focused_pytest_run": target_pytest,
            "target_verifier_passed": target_verifier["returncode"] == 0,
            "target_focused_pytest_passed": target_pytest["returncode"] == 0,
            "status": "TARGET_VERIFIER_AND_FOCUSED_TESTS_PASSED"
            if target_verifier["returncode"] == 0 and target_pytest["returncode"] == 0
            else "TARGET_VERIFIER_OR_FOCUSED_TESTS_FAILED",
            "terminal_decision": TERMINAL_DECISION
            if target_verifier["returncode"] == 0 and target_pytest["returncode"] == 0
            else "BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY",
        }
    )
    write_json(ROUTE_DIR / f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_REPORT_{DATE}.json", report)
    write_md(
        ROUTE_DIR / f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_REPORT_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Target Verifier Test Rerun Report",
        report,
    )
    return report


def verify_recomputed_source_manifest() -> list[str]:
    issues: list[str] = []
    manifest = load_json(ROUTE_DIR / f"{PREFIX}_RECOMPUTED_SOURCE_HASH_MANIFEST_{DATE}.json")
    if manifest.get("hash_mismatch_count") != 0:
        issues.append("repair recomputed source hash manifest has mismatches")
    for record in manifest.get("records", []):
        if record.get("hash_matches_target_manifest") is not True:
            issues.append(f"source hash mismatch: {record.get('role')} {record.get('path')}")
    return issues


def verify_python_syntax() -> list[str]:
    issues: list[str] = []
    for path in list(ROUTE_DIR.glob("*.py")) + [
        TARGET_FILES["parser_or_verifier:builder"],
        TARGET_FILES["parser_or_verifier:focused_tests"],
        TARGET_FILES["parser_or_verifier:verifier"],
    ]:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            issues.append(f"{rel(path)} syntax parse failed: {exc}")
    return issues


def verify_diff_scope() -> dict[str, Any]:
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
    forbidden = [path for path in paths if path.startswith(FORBIDDEN_DIFF_PREFIXES)]
    return {
        "changed_or_untracked_paths": paths,
        "forbidden_live_surface_paths": forbidden,
        "ok": not forbidden,
    }


def update_completion_audit(ok: bool, evidence: dict[str, Any]) -> None:
    path = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json"
    audit = load_json(path)
    audit["can_mark_goal_complete"] = bool(ok)
    audit["completion_status"] = "VERIFIER_PASSED_PENDING_SCOPED_COMMIT_FINAL_LIVE_STATE" if ok else "BLOCKED"
    audit["terminal_decision"] = TERMINAL_DECISION if ok else "BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY"
    audit["closeout_verification_evidence"] = evidence
    write_json(path, audit)
    write_md(
        ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
        "NOFILL Source Expansion Parser Hash Repair Completion Audit",
        audit,
    )


def verify(run_target_checks: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    issues.extend(parse_artifacts())
    issues.extend(verify_exact_hash_closure())
    issues.extend(verify_packet_and_semantics())
    issues.extend(verify_recomputed_source_manifest())
    issues.extend(verify_python_syntax())
    target_report = run_target_verifier_tests() if run_target_checks else load_json(
        ROUTE_DIR / f"{PREFIX}_TARGET_VERIFIER_TEST_RERUN_REPORT_{DATE}.json"
    )
    if target_report.get("target_verifier_passed") is not True:
        issues.append("target verifier rerun failed")
    if target_report.get("target_focused_pytest_passed") is not True:
        issues.append("target focused pytest rerun failed")
    noleak = load_json(ROUTE_DIR / f"{PREFIX}_NOLEAK_SAFE_FLAG_CHECK_{DATE}.json")
    if noleak.get("safe_flag_issue_count") != 0:
        issues.append("no-leak safe-flag check has issues")
    if not (ROUTE_DIR / f"{PREFIX}_NEXT_G12_REPAIR_REAUDIT_PROMPT_PACK_{DATE}.md").exists():
        issues.append("next G12 repair reaudit prompt pack missing")
    diff_scope = verify_diff_scope()
    if not diff_scope["ok"]:
        issues.append(f"forbidden live-surface diff paths: {diff_scope['forbidden_live_surface_paths']}")

    result = with_safe_flags(
        {
            "ok": not issues,
            "route_id": ROUTE_ID,
            "schema_version": f"{SCHEMA_VERSION}_verifier_v1",
            "failures": issues,
            "target_report": target_report,
            "diff_scope": diff_scope,
            "packet_row_count": len(read_jsonl(TARGET_PACKET)),
            "blocked_candidate_count": load_json(TARGET_OUTPUT_MANIFEST).get("blocked_candidate_count"),
            "rejected_candidate_count": load_json(TARGET_OUTPUT_MANIFEST).get("rejected_candidate_count"),
            "exact_repair_requirement_count": len(load_json(G12_REPAIR_LEDGER).get("remaining_requirements", [])),
            "terminal_decision": TERMINAL_DECISION if not issues else "BLOCKED_WITH_EXACT_REPAIR_IMPOSSIBILITY",
            "can_mark_goal_complete": not issues,
        }
    )
    update_completion_audit(result["ok"], {"repair_verifier_result": result})
    write_json(ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json", result)
    return result


if __name__ == "__main__":
    verification = verify()
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
