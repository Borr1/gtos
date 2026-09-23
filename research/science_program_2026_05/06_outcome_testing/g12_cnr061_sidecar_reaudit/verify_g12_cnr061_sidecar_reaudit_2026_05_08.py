"""Verify G12 CNR061 sidecar reaudit artifacts without opening outcomes."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import build_g12_cnr061_sidecar_reaudit_2026_05_08 as build


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    issues: list[dict[str, Any]] = []
    required = {name: path for name, path in build.OUTPUTS.items()}
    missing = [build.rel(path) for path in required.values() if not path.exists()]
    if missing:
        issues.append({"check": "required_outputs_exist", "missing": missing})

    artifacts = {}
    for name, path in required.items():
        if path.suffix == ".json" and path.exists():
            artifacts[name] = read_json(path)

    for name, artifact in artifacts.items():
        if artifact.get("promotion_verdict") != build.PROMOTION_VERDICT:
            issues.append({"check": "promotion_verdict", "artifact": name, "observed": artifact.get("promotion_verdict")})
        if artifact.get("validation_safe") is not False:
            issues.append({"check": "validation_safe_false", "artifact": name, "observed": artifact.get("validation_safe")})
        if artifact.get("outcome_review_opened") is not False:
            issues.append({"check": "outcome_review_opened_false", "artifact": name, "observed": artifact.get("outcome_review_opened")})
        if artifact.get("live_effect") is not False:
            issues.append({"check": "live_effect_false", "artifact": name, "observed": artifact.get("live_effect")})

    decision = artifacts.get("decision_json", {})
    readiness = artifacts.get("readiness_json", {})
    source = artifacts.get("source_json", {})
    noleak = artifacts.get("noleak_json", {})
    blocked = artifacts.get("blocked_json", {})
    completion = artifacts.get("completion_json", {})

    if decision.get("decision") != build.DECISION_ACCEPT:
        issues.append({"check": "decision_accept", "observed": decision.get("decision")})
    if decision.get("accepted_sidecar_row_count") != 8:
        issues.append({"check": "accepted_sidecar_row_count", "observed": decision.get("accepted_sidecar_row_count")})
    if decision.get("blocked_rows_excluded") != 94:
        issues.append({"check": "blocked_rows_excluded", "observed": decision.get("blocked_rows_excluded")})
    if readiness.get("final_decision") != build.DECISION_ACCEPT:
        issues.append({"check": "readiness_final_decision", "observed": readiness.get("final_decision")})
    if not str(source.get("audit_status", "")).startswith("PASS"):
        issues.append({"check": "source_audit_status", "observed": source.get("audit_status")})
    if source.get("row_join_summary", {}).get("fail_count") != 0:
        issues.append({"check": "row_join_fail_count", "observed": source.get("row_join_summary", {}).get("fail_count")})
    if source.get("quote_path_asof_summary", {}).get("fail_count") != 0:
        issues.append({"check": "quote_path_asof_fail_count", "observed": source.get("quote_path_asof_summary", {}).get("fail_count")})
    if source.get("sidecar_source_evidence_summary", {}).get("mismatch_count") != 0:
        issues.append({"check": "sidecar_source_evidence_mismatch_count", "observed": source.get("sidecar_source_evidence_summary", {}).get("mismatch_count")})
    if source.get("upstream_source_search_ledger_recompute", {}).get("strict_row_or_control_source_mismatch_count") != 0:
        issues.append({
            "check": "strict_row_source_hash_mismatch_count",
            "observed": source.get("upstream_source_search_ledger_recompute", {}).get("strict_row_or_control_source_mismatch_count"),
        })
    if noleak.get("audit_status") != "PASS":
        issues.append({"check": "noleak_audit_status", "observed": noleak.get("audit_status")})
    if noleak.get("forbidden_packet_row_key_hits"):
        issues.append({"check": "forbidden_packet_row_key_hits", "observed": noleak.get("forbidden_packet_row_key_hits")})
    if blocked.get("audit_status") != "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED":
        issues.append({"check": "blocked_audit_status", "observed": blocked.get("audit_status")})
    if blocked.get("exclusion_counts", {}).get("accepted_plus_blocked") != 102:
        issues.append({"check": "accepted_plus_blocked", "observed": blocked.get("exclusion_counts", {}).get("accepted_plus_blocked")})
    otr = blocked.get("otr061_recovery_block_status", {})
    if otr.get("reason") != "TARGET_ALREADY_PASSED_INPUT_GATE_NOT_MISSING_TICK_EVIDENCE":
        issues.append({"check": "otr061_reason", "observed": otr.get("reason")})
    if completion.get("completion_status") != "PASS_VERIFIED_SCOPED_COMMIT":
        issues.append({"check": "completion_status", "observed": completion.get("completion_status")})

    git_cmd = [
        "git",
        "-c",
        "safe.directory=C:/tmp/gtos_otb/G12CNR061",
        "status",
        "--short",
        "src",
        "prompts",
        "config",
        "scripts",
        "tests",
    ]
    git_result = subprocess.run(git_cmd, cwd=build.ROOT, text=True, capture_output=True, check=False)
    live_surface_lines = [line for line in git_result.stdout.splitlines() if line.strip()]
    if live_surface_lines:
        issues.append({"check": "live_surface_git_status_clean", "observed": live_surface_lines})

    result = {
        "artifact_family": "G12_CNR061_SIDECAR_REAUDIT_VERIFICATION",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "decision": decision.get("decision"),
        "accepted_sidecar_rows": decision.get("accepted_sidecar_row_count"),
        "blocked_rows_excluded": decision.get("blocked_rows_excluded"),
        "source_audit_status": source.get("audit_status"),
        "noleak_audit_status": noleak.get("audit_status"),
        "blocked_audit_status": blocked.get("audit_status"),
        "live_surface_git_status_stdout": git_result.stdout,
        "live_surface_git_status_stderr": git_result.stderr,
        "promotion_verdict": build.PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
