#!/usr/bin/env python3
"""Verify the G0 NOFILL CAT V3 synthesis/control review artifacts."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_g0_nofill_cat_v3_synthesis_control_review_2026_05_09 as builder


ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)

FORBIDDEN_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "expectancy",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_account",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "pbo",
    "profit",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
)

ALLOWED_POLICY_PATH_PARTS = (
    "forbidden",
    "hard_boundaries",
    "g0_does_not_allow",
    "does_not_mean",
    "not_proven",
    "non_claim",
    "policy",
    "blocked",
    "unblocker",
    "prompt",
    "rejected_next_routes",
    "source_lessons",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def git_output(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.excludesfile=", *args],
        cwd=builder.REPO_ROOT,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def check_artifacts_exist() -> dict[str, Any]:
    required = builder.OUTPUT_JSON + builder.OUTPUT_MD + builder.PY_FILES
    missing = [name for name in required if not (builder.OUT_DIR / name).exists()]
    return {
        "status": "PASS" if not missing else "FAIL",
        "required_count": len(required),
        "missing": missing,
    }


def check_json_jsonl_parse() -> dict[str, Any]:
    results = []
    failures = []
    for name in builder.OUTPUT_JSON:
        path = builder.OUT_DIR / name
        try:
            read_json(path)
            results.append({"path": builder.rel(path), "parse_status": "PASS_JSON"})
        except Exception as exc:
            failures.append({"path": builder.rel(path), "error": str(exc)})
    for path in (
        builder.CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl",
        builder.CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_2026-05-09.jsonl",
        builder.COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_2026-05-09.jsonl",
        builder.COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_2026-05-09.jsonl",
    ):
        try:
            rows = read_jsonl(path)
            results.append({"path": builder.rel(path), "parse_status": "PASS_JSONL", "row_count": len(rows)})
        except Exception as exc:
            failures.append({"path": builder.rel(path), "error": str(exc)})
    return {"status": "PASS" if not failures else "FAIL", "results": results, "failures": failures}


def check_recomputed_counts() -> dict[str, Any]:
    inputs = builder.load_inputs()
    facts = builder.recompute_facts(inputs)
    expected = {
        "accepted_row_level_total": 225,
        "primary_unique_nofill_duplicate_key_total": 182,
        "secondary_unique_duplicate_group_id_total": 139,
        "reject_overlap_count": 47,
        "row_level_label_counts": builder.EXPECTED_ROW_LABELS,
        "primary_nofill_duplicate_key_label_counts": builder.EXPECTED_PRIMARY_LABELS,
        "secondary_duplicate_group_id_label_counts": builder.EXPECTED_SECONDARY_LABELS,
    }
    mismatches = {}
    for key, value in expected.items():
        if facts.get(key) != value:
            mismatches[key] = {"expected": value, "actual": facts.get(key)}
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "facts": facts,
        "mismatches": mismatches,
    }


def walk_flags(payload: Any, path: str = "") -> list[dict[str, Any]]:
    issues = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            next_path = f"{path}.{key}" if path else str(key)
            if key in {"validation_safe", "outcome_review_opened", "live_effect"} and value is not False:
                issues.append({"path": next_path, "expected": False, "actual": value})
            if key == "promotion_verdict" and value != builder.PROMOTION_VERDICT:
                issues.append({"path": next_path, "expected": builder.PROMOTION_VERDICT, "actual": value})
            issues.extend(walk_flags(value, next_path))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            issues.extend(walk_flags(item, f"{path}[{index}]"))
    return issues


def check_safe_flags() -> dict[str, Any]:
    issues = []
    for name in builder.OUTPUT_JSON:
        payload = read_json(builder.OUT_DIR / name)
        issues.extend({"file": name, **issue} for issue in walk_flags(payload))
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def is_allowed_policy_path(path: str) -> bool:
    lowered = path.lower()
    return any(part in lowered for part in ALLOWED_POLICY_PATH_PARTS)


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, Any]]:
    hits = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            next_path = f"{path}.{key}" if path else str(key)
            key_l = str(key).lower()
            if any(part in key_l for part in FORBIDDEN_KEY_PARTS) and not is_allowed_policy_path(next_path):
                hits.append({"path": next_path, "key": str(key)})
            hits.extend(scan_forbidden_keys(value, next_path))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            hits.extend(scan_forbidden_keys(item, f"{path}[{index}]"))
    return hits


def check_forbidden_generated_fields() -> dict[str, Any]:
    hits = []
    for name in builder.OUTPUT_JSON:
        payload = read_json(builder.OUT_DIR / name)
        hits.extend({"file": name, **hit} for hit in scan_forbidden_keys(payload))
    return {
        "status": "PASS" if not hits else "FAIL",
        "policy": "Forbidden strings are allowed only inside explicit forbidden/non-claim/policy text.",
        "unexpected_hits": hits,
    }


def check_python_parse() -> dict[str, Any]:
    failures = []
    for name in builder.PY_FILES:
        path = builder.OUT_DIR / name
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"path": builder.rel(path), "error": str(exc)})
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def check_live_surface_diff() -> dict[str, Any]:
    try:
        committed_raw = git_output("diff", "--name-only", "HEAD^", "HEAD", "--")
        committed_changed = [
            line.strip().replace("\\", "/")
            for line in committed_raw.splitlines()
            if line.strip() and not line.lower().startswith("warning:")
        ]
        workspace_raw = git_output("diff", "--name-only", "HEAD", "--")
        workspace_changed = [
            line.strip().replace("\\", "/")
            for line in workspace_raw.splitlines()
            if line.strip() and not line.lower().startswith("warning:")
        ]
    except Exception as exc:
        return {"status": "FAIL", "error": str(exc)}
    forbidden = [
        path
        for path in committed_changed
        if not path.startswith(ALLOWED_DIFF_PREFIXES)
    ]
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent",
        "changed_paths": committed_changed,
        "forbidden_changed_paths": forbidden,
        "allowed_prefixes": list(ALLOWED_DIFF_PREFIXES),
        "workspace_paths_informational_only": workspace_changed,
    }


def check_context_refresh() -> dict[str, Any]:
    path = builder.REPO_ROOT / ".context" / "00_core" / "research_current_state.md"
    text = path.read_text(encoding="utf-8")
    required = [
        "2026-05-09 G0 NOFILL CAT V3 Categorical Evidence Synthesis Control Review Completed",
        "G0_NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_EVIDENCE_SYNTHESIS_CONTROL_REVIEW",
        "e8a667093b5bac810aa0522c3346907ffb830f64",
        "5287eebd research: synthesize g0 no-fill cat v3 controls",
    ]
    missing = [item for item in required if item not in text]
    return {
        "status": "PASS" if not missing else "FAIL",
        "path": builder.rel(path),
        "missing": missing,
    }


def check_completion_audit_coverage() -> dict[str, Any]:
    path = builder.OUT_DIR / f"G0_NOFILL_CAT_V3_COMPLETION_AUDIT_{builder.DATE}.json"
    payload = read_json(path)
    checklist = payload["prompt_to_artifact_checklist"]
    non_pass = [item for item in checklist if item["status"] != "PASS"]
    required_fragments = [
        "GTOS preflight",
        "V3 source-control",
        "Frozen V3 result contract",
        "Count packet",
        "Required count facts",
        "Categorical evidence meaning",
        "Duplicate/concentration",
        "Exact blockers",
        "Flags preserved",
    ]
    checklist_text = "\n".join(item["requirement"] for item in checklist)
    missing_fragments = [fragment for fragment in required_fragments if fragment not in checklist_text]
    return {
        "status": "PASS" if not non_pass and not missing_fragments else "FAIL",
        "non_pass_items": non_pass,
        "missing_requirement_fragments": missing_fragments,
        "can_mark_goal_complete": payload.get("can_mark_goal_complete"),
    }


def run_verification(update_completion: bool = True) -> dict[str, Any]:
    checks = {
        "artifact_presence": check_artifacts_exist(),
        "json_jsonl_parse": check_json_jsonl_parse(),
        "recomputed_counts": check_recomputed_counts(),
        "safe_flags": check_safe_flags(),
        "forbidden_generated_fields": check_forbidden_generated_fields(),
        "python_parse": check_python_parse(),
        "live_surface_diff": check_live_surface_diff(),
        "context_refresh": check_context_refresh(),
    }
    status = "PASS" if all(check["status"] == "PASS" for check in checks.values()) else "FAIL"
    result = {
        "verification_status": {"status": status},
        "checks": checks,
    }
    if update_completion:
        builder.write_completion_audit("PASS" if status == "PASS" else "VERIFIER_FAIL", result)
        checks["completion_audit_coverage"] = check_completion_audit_coverage()
        status = "PASS" if all(check["status"] == "PASS" for check in checks.values()) else "FAIL"
        result = {
            "verification_status": {"status": status},
            "checks": checks,
        }
        if status == "PASS":
            builder.write_completion_audit("PASS", result)
    return result


def main() -> int:
    result = run_verification(update_completion=True)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result["verification_status"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
