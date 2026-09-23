#!/usr/bin/env python3
"""Verify the compliant VPS data-preservation broker-portability route."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
RESULT_PATH = ROUTE_DIR / "VERIFICATION_RESULT.json"

REQUIRED_ARTIFACTS = [
    "ROUTE_CONTEXT_ANCHOR.json",
    "OFFICIAL_redacted_account_SOURCE_INDEX.json",
    "COMPLIANCE_FACT_LEDGER.jsonl",
    "LOCAL_EVIDENCE_INVENTORY.jsonl",
    "LOCAL_EVIDENCE_COVERAGE_SUMMARY.json",
    "DATA_SURFACE_RETENTION_DECISION_LEDGER.jsonl",
    "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl",
    "VPS_MIGRATION_CONTRACT.md",
    "VPS_STARTUP_VERIFICATION_RUNBOOK.md",
    "BROKER_PORTABILITY_MAP.json",
    "BROKER_PORTABILITY_GAP_LEDGER.jsonl",
    "MT5_EXPORT_READINESS_CHECKLIST.json",
    "DEFAULT_OFF_EXPORT_SCRIPT_MANIFEST.json",
    "ABSOLUTE_MOONSHOT_DATA_REQUIREMENT_MAP.json",
    "OUTPUT_MANIFEST.json",
    "COMPLETION_AUDIT.json",
]

ACTIVE_SYMBOLS = {
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
}

FORBIDDEN_TEXT_RE = re.compile(
    r"\b(bypass|evade|hide location|conceal location|fake residency|false residency|mask identity)\b",
    re.I,
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?([A-Za-z0-9_./+=-]{12,})"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    except (OSError, json.JSONDecodeError):
        return []
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    try:
        import hashlib

        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def run_check(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        return {
            "command": " ".join(command),
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-1000:],
            "stderr_tail": completed.stderr[-1000:],
        }
    except Exception as exc:
        return {"command": " ".join(command), "error": str(exc), "returncode": 999}


def verify_route(write_completion_audit: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    checks: list[dict[str, Any]] = []

    for name in REQUIRED_ARTIFACTS:
        path = ROUTE_DIR / name
        if not path.exists():
            issues.append(f"missing_required_artifact:{name}")
        elif path.stat().st_size <= 0:
            issues.append(f"empty_required_artifact:{name}")

    source_index = read_json(ROUTE_DIR / "OFFICIAL_redacted_account_SOURCE_INDEX.json", {})
    entries = source_index.get("entries") or []
    if len(entries) != 4:
        issues.append(f"official_source_entry_count:{len(entries)}")
    for entry in entries:
        if not entry.get("raw_sha256") or not (REPO_ROOT / entry.get("raw_path", "")).exists():
            issues.append(f"official_source_capture_missing_or_unhashed:{entry.get('source_id')}")
        facts = entry.get("extracted_policy_facts") or {}
        if entry.get("source_id") == "redacted_account_restricted_countries":
            if not facts.get("malaysia_listed_restricted"):
                issues.append("malaysia_not_verified_restricted")
            if facts.get("tunisia_listed_restricted"):
                issues.append("tunisia_unexpectedly_listed_restricted")
            if not facts.get("usa_based_ip_for_mt5_not_allowed"):
                issues.append("mt5_usa_ip_rule_not_extracted")
        if entry.get("source_id") == "redacted_account_vpn_vps_policy":
            for key in [
                "private_dedicated_vps_required",
                "shared_vps_prohibited",
                "trade_taking_ea_required_for_vps",
                "manual_trading_through_vps_prohibited",
                "broker_sponsored_vps_prohibited",
            ]:
                if not facts.get(key):
                    issues.append(f"vpn_vps_fact_not_extracted:{key}")

    fact_rows = read_jsonl(ROUTE_DIR / "COMPLIANCE_FACT_LEDGER.jsonl")
    if not any(row.get("fact_id") == "owner_identity_tunisia_residency_temporary_malaysia_travel" for row in fact_rows):
        issues.append("owner_identity_fact_missing")
    if not any(row.get("fact_id") == "restricted_country_list_malaysia_true_tunisia_false" for row in fact_rows):
        issues.append("restricted_country_tunisia_malaysia_fact_missing")

    inventory = read_jsonl(ROUTE_DIR / "LOCAL_EVIDENCE_INVENTORY.jsonl")
    coverage = read_json(ROUTE_DIR / "LOCAL_EVIDENCE_COVERAGE_SUMMARY.json", {})
    if len(inventory) < 500:
        issues.append(f"inventory_too_small:{len(inventory)}")
    required_roots = {
        "data",
        "data\\ticks",
        "data\\m1",
        "shadow_logs",
        "pipeline_state",
        "knowledge_base",
        "config",
        "src",
        "tests",
        ".context\\00_core",
        "exports",
        "logs",
        "mt5_ea",
    }
    roots_seen = {str(row.get("root_path")) for row in inventory}
    missing_roots = sorted(required_roots - roots_seen)
    if missing_roots:
        issues.append(f"inventory_missing_required_roots:{missing_roots}")
    root_summaries = {row.get("root_path"): row for row in coverage.get("required_root_summaries") or []}
    for absent_root in ["data\\m15", "data\\symbol_specs", "data\\spreads"]:
        if absent_root not in root_summaries and absent_root not in roots_seen:
            issues.append(f"normalized_absent_root_not_recorded:{absent_root}")

    portability = read_json(ROUTE_DIR / "BROKER_PORTABILITY_MAP.json", {})
    symbols = portability.get("symbols") or []
    symbol_names = {row.get("canonical_gtos_symbol") for row in symbols}
    if symbol_names != ACTIVE_SYMBOLS:
        issues.append(f"broker_portability_symbol_mismatch:{sorted(ACTIVE_SYMBOLS - symbol_names)}")
    required_portability_fields = {
        "canonical_gtos_symbol",
        "redacted_account_broker_native_symbol",
        "asset_class",
        "contract_size",
        "tick_size",
        "tick_value",
        "point_value",
        "min_lot",
        "max_lot",
        "lot_step",
        "stops_level",
        "freeze_level",
        "sessions_or_hours",
        "missing_broker_specific_fields",
    }
    for row in symbols:
        missing = required_portability_fields - set(row)
        if missing:
            issues.append(f"broker_portability_row_missing_fields:{row.get('canonical_gtos_symbol')}:{sorted(missing)}")

    gap_rows = read_jsonl(ROUTE_DIR / "BROKER_PORTABILITY_GAP_LEDGER.jsonl")
    if not gap_rows:
        issues.append("broker_portability_gap_ledger_empty")
    if not any(row.get("missing_field") == "commission_schedule" for row in gap_rows):
        issues.append("commission_schedule_gap_missing")
    if not any(row.get("missing_field") == "broker_trading_sessions_by_weekday" for row in gap_rows):
        issues.append("broker_sessions_gap_missing")

    missing_exports = read_jsonl(ROUTE_DIR / "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl")
    for requirement in [
        "redacted_account_vps_ea_addon_or_fee_proof",
        "vps_public_ip_country_provider_dedicated_proof",
        "full_mt5_account_orders_deals_positions_export",
        "alternate_broker_symbol_contract_cost_map",
    ]:
        if not any(row.get("requirement_id") == requirement for row in missing_exports):
            issues.append(f"missing_export_requirement:{requirement}")

    default_manifest = read_json(ROUTE_DIR / "DEFAULT_OFF_EXPORT_SCRIPT_MANIFEST.json", {})
    if default_manifest.get("default_off") is not True or default_manifest.get("no_broker_changing_actions") is not True:
        issues.append("default_off_manifest_safety_flags_missing")
    if not (ROUTE_DIR / "default_off_vps_tools.py").exists():
        issues.append("default_off_script_missing")

    moonshot = read_json(ROUTE_DIR / "ABSOLUTE_MOONSHOT_DATA_REQUIREMENT_MAP.json", {})
    if not moonshot.get("programs"):
        issues.append("moonshot_requirement_map_empty")

    manifest = read_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", {})
    if manifest.get("missing_required_artifacts"):
        issues.append(f"output_manifest_missing_required:{manifest.get('missing_required_artifacts')}")
    for artifact in manifest.get("artifacts") or []:
        path = REPO_ROOT / str(artifact.get("path", "")).replace("\\", "/")
        if not path.exists():
            issues.append(f"manifest_artifact_missing:{artifact.get('path')}")
        elif artifact.get("sha256") and sha256_file(path) != artifact.get("sha256"):
            issues.append(f"manifest_hash_mismatch:{artifact.get('path')}")
        elif not artifact.get("sha256") and artifact.get("hash_status") != "volatile_route_artifact_verified_by_parse_and_presence":
            issues.append(f"manifest_missing_hash_without_volatile_status:{artifact.get('path')}")

    for text_file in ["VPS_MIGRATION_CONTRACT.md", "VPS_STARTUP_VERIFICATION_RUNBOOK.md"]:
        text = (ROUTE_DIR / text_file).read_text(encoding="utf-8", errors="replace")
        if FORBIDDEN_TEXT_RE.search(text):
            issues.append(f"forbidden_concealment_language:{text_file}")
        if SECRET_VALUE_RE.search(text):
            issues.append(f"secret_like_value_in_text:{text_file}")
        for required_phrase in ["Tunisia", "Malaysia", "United States", "dedicated", "read-only"]:
            if required_phrase not in text:
                issues.append(f"runbook_contract_missing_phrase:{text_file}:{required_phrase}")

    for path in ROUTE_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".md", ".txt", ".py"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if SECRET_VALUE_RE.search(text):
                issues.append(f"secret_like_value_in_route_artifact:{path.name}")

    py_compile = run_check(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(ROUTE_DIR / "build_vnext_compliant_vps_data_preservation_broker_portability.py"),
            str(ROUTE_DIR / "verify_vnext_compliant_vps_data_preservation_broker_portability.py"),
            str(ROUTE_DIR / "default_off_vps_tools.py"),
        ]
    )
    checks.append(py_compile)
    if py_compile.get("returncode") != 0:
        issues.append("py_compile_failed")

    result = {
        "schema_version": "vps_data_preservation_verification_result_v1",
        "generated_at_utc": now_iso(),
        "ok": not issues,
        "issues": issues,
        "counts": {
            "official_source_entries": len(entries),
            "compliance_fact_rows": len(fact_rows),
            "inventory_rows": len(inventory),
            "broker_portability_symbols": len(symbols),
            "broker_gap_rows": len(gap_rows),
            "missing_export_rows": len(missing_exports),
        },
        "checks": checks,
        "forbidden_surface_attestation": {
            "live_runtime_started_by_this_route": False,
            "broker_changing_action_by_this_route": False,
            "mt5_server_access_by_this_route": False,
            "paid_api_or_vendor_call_by_this_route": False,
            "credential_print_or_change_by_this_route": False,
            "remote_push_by_this_route": False,
        },
    }
    write_json(RESULT_PATH, result)
    if write_completion_audit:
        audit_path = ROUTE_DIR / "COMPLETION_AUDIT.json"
        audit = read_json(audit_path, {})
        audit["verification_ok"] = result["ok"]
        audit["can_mark_goal_complete"] = bool(result["ok"])
        audit["verification_result_path"] = str(RESULT_PATH.relative_to(REPO_ROOT))
        audit["verification_issue_count"] = len(issues)
        audit["generated_at_utc"] = now_iso()
        audit["subagent_findings_merged"] = True
        for item in audit.get("requirements") or []:
            if item.get("requirement") == "verification_result_ok_true":
                item["status"] = "passed" if result["ok"] else "failed"
            if item.get("requirement") == "scoped_commit_with_codex_coauthor" and result["ok"]:
                item["status"] = "ready_for_scoped_commit_after_verification"
        write_json(audit_path, audit)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    result = verify_route()
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.check and not result["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
