#!/usr/bin/env python3
"""Verify Wave 1C dual-broker architecture artifacts."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = ROOT / "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04"

REQUIRED_FILES = [
    "WAVE1C_CONTEXT_ANCHOR.json",
    "WAVE1C_SEARCHED_ROOT_LEDGER.jsonl",
    "WAVE1C_SOURCE_INVENTORY.jsonl",
    "BROKER_PROFILE_AND_NAMESPACE_INVENTORY.jsonl",
    "DUAL_BROKER_RUNTIME_PATH_MAP.md",
    "redacted_account_FTMO_AUTHORITY_SEPARATION_MATRIX.jsonl",
    "FOLLOWER_PROJECTOR_LIFECYCLE_LEDGER.jsonl",
    "BROKER_LOCAL_RISK_AND_EXPOSURE_LEDGER.jsonl",
    "TARGET_STATE_AND_NAMESPACE_LEDGER.jsonl",
    "COST_SWAP_SLIPPAGE_SPEC_SESSION_LEDGER.jsonl",
    "CRASH_RECOVERY_AND_HALT_SEMANTICS_LEDGER.jsonl",
    "DUAL_BROKER_ARCHITECTURE_DECISION.md",
    "PRODUCTION_CODE_CHANGE_LEDGER.jsonl",
    "IMPLEMENTATION_DECISION_LEDGER.jsonl",
    "FORWARD_CAPTURE_REQUIREMENTS.md",
    "WAVE1C_SATURATION_AND_SELF_RED_TEAM.md",
    "WAVE1C_VERIFICATION_RESULT.json",
    "WAVE1C_OUTPUT_MANIFEST.json",
    "WAVE1C_COMPLETION_AUDIT.md",
    "WAVE1C_FOCUSED_TEST_RESULT.json",
    "verify_wave1c_dual_broker_architecture.py",
]

REQUIRED_JSONL_FIELDS = {
    "source_capture_state",
    "source_completeness_state",
    "branch_decision",
    "implementation_decision",
    "evidence_class",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def scan_jsonl(path: Path) -> dict[str, Any]:
    rows = 0
    parse_errors = 0
    missing_required_fields = 0
    statuses: Counter[str] = Counter()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            rows += 1
            if not isinstance(row, dict) or not REQUIRED_JSONL_FIELDS.issubset(row):
                missing_required_fields += 1
            for key in ("runtime_disposition", "branch_decision", "implementation_decision", "source_completeness_state"):
                value = row.get(key) if isinstance(row, dict) else None
                if value not in (None, ""):
                    statuses[f"{key}={value}"] += 1
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "rows": rows,
        "parse_errors": parse_errors,
        "missing_required_fields": missing_required_fields,
        "top_statuses": statuses.most_common(20),
    }


def main() -> int:
    issues: list[str] = []
    if not ROUTE_DIR.exists():
        print(json.dumps({"ok": False, "issues": ["route_dir_missing"]}, indent=2, sort_keys=True))
        return 1
    missing = [name for name in REQUIRED_FILES if not (ROUTE_DIR / name).exists()]
    issues.extend(f"missing_required_file:{name}" for name in missing)

    jsonl_scans = []
    for path in sorted(ROUTE_DIR.glob("*.jsonl")):
        scan = scan_jsonl(path)
        jsonl_scans.append(scan)
        if scan["rows"] <= 0:
            issues.append(f"empty_jsonl:{path.name}")
        if scan["parse_errors"]:
            issues.append(f"jsonl_parse_errors:{path.name}:{scan['parse_errors']}")
        if scan["missing_required_fields"]:
            issues.append(
                f"jsonl_missing_required_fields:{path.name}:{scan['missing_required_fields']}"
            )

    try:
        profile_rows = [
            json.loads(line)
            for line in (ROUTE_DIR / "BROKER_PROFILE_AND_NAMESPACE_INVENTORY.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except OSError:
        profile_rows = []
    profile_contracts = {
        row.get("dual_broker_role")
        for row in profile_rows
        if row.get("row_type") == "profile"
    }
    if "primary_full_runtime" not in profile_contracts:
        issues.append("redacted_account_primary_full_runtime_contract_missing")
    if "follower_projector_only" not in profile_contracts:
        issues.append("ftmo_follower_projector_only_contract_missing")

    try:
        implementation_rows = [
            json.loads(line)
            for line in (ROUTE_DIR / "IMPLEMENTATION_DECISION_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except OSError:
        implementation_rows = []
    decision_ids = {row.get("decision_id") for row in implementation_rows}
    for required in {
        "final_runtime_model",
        "ftmo_broker_local_risk",
        "ftmo_lifecycle_authority",
        "primary_copy_boundary",
        "maintenance_bridge_boundary",
        "runtime_return",
    }:
        if required not in decision_ids:
            issues.append(f"implementation_decision_missing:{required}")

    text_checks = {
        "decision_mentions_follower_only": "follower/projector only" in (ROUTE_DIR / "DUAL_BROKER_ARCHITECTURE_DECISION.md").read_text(encoding="utf-8", errors="replace"),
        "forward_capture_mentions_account_history": "account-history" in (ROUTE_DIR / "FORWARD_CAPTURE_REQUIREMENTS.md").read_text(encoding="utf-8", errors="replace"),
        "completion_mentions_no_chat_memory": "No chat memory was used as evidence" in (ROUTE_DIR / "WAVE1C_COMPLETION_AUDIT.md").read_text(encoding="utf-8", errors="replace"),
    }
    for name, ok in text_checks.items():
        if not ok:
            issues.append(f"text_check_failed:{name}")

    result = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "route_dir": ROUTE_DIR.relative_to(ROOT).as_posix(),
        "required_file_count": len(REQUIRED_FILES),
        "jsonl_scans": jsonl_scans,
        "profile_contracts": sorted(str(item) for item in profile_contracts if item),
        "implementation_decision_count": len(implementation_rows),
        "text_checks": text_checks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
