#!/usr/bin/env python3
"""Verify OTI7 CNR accepted-row quarantined result artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
READY_PATH = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_cnr_source_field_packet_audit/G12_CNR_READY_ROW_SHORTLIST_2026-05-08.json"
)
BLOCKER_PATH = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_cnr_source_field_packet_audit/G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json"
)
MANIFEST_PATH = OUT / f"OTI7_CNR_ARTIFACT_MANIFEST_{DATE}.json"
RESULT_LEDGER_PATH = OUT / f"OTI7_CNR_RESULT_LEDGER_{DATE}.json"
RESULT_LEDGER_JSONL_PATH = OUT / f"OTI7_CNR_RESULT_LEDGER_{DATE}.jsonl"
SOURCE_AUDIT_PATH = OUT / f"OTI7_CNR_SOURCE_HASH_PATH_COVERAGE_AUDIT_{DATE}.json"
COMPLETION_PATH = OUT / f"OTI7_CNR_COMPLETION_AUDIT_{DATE}.json"
REPORT_JSON = OUT / f"OTI7_CNR_VERIFICATION_REPORT_{DATE}.json"
REPORT_MD = OUT / f"OTI7_CNR_VERIFICATION_REPORT_{DATE}.md"

REQUIRED_STEMS = [
    "OTI7_CNR_RESULT_LEDGER",
    "OTI7_CNR_SOURCE_HASH_PATH_COVERAGE_AUDIT",
    "OTI7_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT",
    "OTI7_CNR_DUPLICATE_EFFECTIVE_N_AUDIT",
    "OTI7_CNR_NOLEAK_LABEL_FAMILY_AUDIT",
    "OTI7_CNR_TIMING_FAMILY_COMPARISON",
    "OTI7_CNR_TARGET_ALREADY_PASSED_AND_NULL_FORENSICS",
    "OTI7_CNR_NEGATIVE_RESULT_LEARNING_LEDGER",
    "OTI7_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT",
    "OTI7_CNR_NEXT_HYPOTHESIS_AND_BLOCKER_LEDGER",
    "OTI7_CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE",
    "OTI7_CNR_COMPLETION_AUDIT",
]

FORBIDDEN_LIVE_SURFACE_PREFIXES = [
    "config/",
    "prompts/",
    "src/",
    "knowledge_base/",
    "pipeline_state/",
    "run_agent.py",
    "start_all.bat",
    "scripts/canary",
    "scripts/canary_test.py",
    "scripts/watchdog",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def verify_required_files() -> dict[str, Any]:
    missing = []
    for stem in REQUIRED_STEMS:
        for suffix in [".json", ".md"]:
            path = OUT / f"{stem}_{DATE}{suffix}"
            if not path.exists():
                missing.append(rel(path))
    if not RESULT_LEDGER_JSONL_PATH.exists():
        missing.append(rel(RESULT_LEDGER_JSONL_PATH))
    return {"status": "PASS" if not missing else "FAIL", "missing": missing}


def verify_json_parse_and_flags() -> dict[str, Any]:
    issues = []
    parsed = []
    for path in sorted(OUT.glob(f"OTI7_CNR_*{DATE}.json")):
        payload = read_json(path)
        parsed.append(rel(path))
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append({"path": rel(path), "issue": "promotion_verdict_not_preserved"})
        if payload.get("validation_safe") is not False:
            issues.append({"path": rel(path), "issue": "validation_safe_not_false"})
        if payload.get("outcome_review_opened") is not False:
            issues.append({"path": rel(path), "issue": "outcome_review_opened_not_false"})
        if payload.get("live_effect") is not False:
            issues.append({"path": rel(path), "issue": "live_effect_not_false"})
    text_hits = []
    for path in sorted(OUT.glob(f"OTI7_CNR_*{DATE}.*")):
        if path.suffix.lower() not in {".json", ".md", ".jsonl"}:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for needle in ['"validation_safe": true', '"outcome_review_opened": true', '"live_effect": true']:
            if needle in text:
                text_hits.append({"path": rel(path), "needle": needle})
    rows = [json.loads(line) for line in RESULT_LEDGER_JSONL_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 102:
        issues.append({"path": rel(RESULT_LEDGER_JSONL_PATH), "issue": f"jsonl_row_count_{len(rows)}"})
    return {
        "status": "PASS" if not issues and not text_hits else "FAIL",
        "parsed_json_files": parsed,
        "issues": issues,
        "unsafe_text_hits": text_hits,
        "jsonl_rows": len(rows),
    }


def verify_manifest_hashes() -> dict[str, Any]:
    manifest = read_json(MANIFEST_PATH)
    mismatches = []
    for item in manifest["artifacts"]:
        path = resolve_path(item["path"])
        if not path.exists():
            mismatches.append({"path": item["path"], "issue": "missing_manifest_artifact"})
            continue
        actual = sha256_file(path)
        if actual != item["sha256"]:
            mismatches.append({"path": item["path"], "issue": "hash_mismatch", "expected": item["sha256"], "actual": actual})
    return {"status": "PASS" if not mismatches else "FAIL", "mismatches": mismatches, "artifact_count": len(manifest["artifacts"])}


def verify_source_hashes() -> dict[str, Any]:
    source = read_json(SOURCE_AUDIT_PATH)
    mismatches = []
    for item in source["source_files"]:
        path = resolve_path(item["path"])
        if not path.exists():
            mismatches.append({"path": item["path"], "issue": "missing_source_file"})
            continue
        actual = sha256_file(path)
        if actual != item["actual_sha256"]:
            mismatches.append({"path": item["path"], "issue": "source_hash_mismatch", "expected": item["actual_sha256"], "actual": actual})
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "mismatches": mismatches,
        "source_file_count": len(source["source_files"]),
        "quote_recompute_mismatch_count": source["quote_recompute_mismatch_count"],
        "listed_source_hash_mismatch_count": source["listed_source_hash_mismatch_count"],
    }


def verify_scope_and_counts() -> dict[str, Any]:
    ready = read_json(READY_PATH)
    blockers = read_json(BLOCKER_PATH)
    ledger = read_json(RESULT_LEDGER_PATH)
    completion = read_json(COMPLETION_PATH)
    result_rows = ledger["rows"]
    ready_sha = {row["row_sha256"] for row in ready["rows"]}
    blocker_sha = {row["row_sha256"] for row in blockers["rows"]}
    result_sha = {row["row_sha256"] for row in result_rows}
    issues = []
    if len(result_rows) != 102:
        issues.append("result_row_count_not_102")
    if ready["ready_row_count"] != 102 or len(ready["rows"]) != 102:
        issues.append("ready_row_count_not_102")
    if blockers["blocked_row_count"] != 6098 or len(blockers["rows"]) != 6098:
        issues.append("blocked_row_count_not_6098")
    if result_sha != ready_sha:
        issues.append("result_sha_set_differs_from_ready_shortlist")
    if result_sha & blocker_sha:
        issues.append("blocked_row_sha_entered_result")
    if ledger["status_counts"] != {
        "SCORED_STOP_FIRST": 64,
        "SCORED_TARGET_FIRST": 12,
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 8,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 18,
    }:
        issues.append("unexpected_status_counts")
    if ledger["countable_rows"] != 54 or ledger["duplicate_context_rows"] != 48:
        issues.append("duplicate_policy_counts_changed")
    if ledger["scored_rows"] != 76:
        issues.append("scored_row_count_changed")
    if completion.get("can_mark_goal_complete") is not True:
        issues.append("completion_audit_not_true")
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "accepted_rows": len(result_rows),
        "blocked_rows": len(blockers["rows"]),
        "status_counts": ledger["status_counts"],
        "countable_rows": ledger["countable_rows"],
        "duplicate_context_rows": ledger["duplicate_context_rows"],
        "scored_rows": ledger["scored_rows"],
    }


def git_status_paths() -> list[str]:
    command = [
        "git",
        "-c",
        "safe.directory=C:/tmp/gtos_otb/OTI7CNRRESULT",
        "-c",
        "core.excludesfile=",
        "status",
        "--porcelain",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    paths = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:].replace("\\", "/"))
    return paths


def verify_forbidden_live_surface_diff() -> dict[str, Any]:
    paths = git_status_paths()
    hits = []
    for path in paths:
        normalized = path.lower()
        for prefix in FORBIDDEN_LIVE_SURFACE_PREFIXES:
            if normalized.startswith(prefix.lower()):
                hits.append(path)
    return {"status": "PASS" if not hits else "FAIL", "changed_paths": paths, "forbidden_live_surface_hits": sorted(set(hits))}


def build_report() -> dict[str, Any]:
    checks = {
        "required_files": verify_required_files(),
        "json_parse_flags": verify_json_parse_and_flags(),
        "manifest_hashes": verify_manifest_hashes(),
        "source_hashes": verify_source_hashes(),
        "scope_and_counts": verify_scope_and_counts(),
        "forbidden_live_surface_diff": verify_forbidden_live_surface_diff(),
    }
    ok = all(check["status"] == "PASS" for check in checks.values())
    return {
        "artifact_family": "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS",
        "artifact_type": "verification_report",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "status": "PASS" if ok else "FAIL",
        "checks": checks,
    }


def render_report_md(report: dict[str, Any]) -> str:
    rows = [[name, check["status"]] for name, check in report["checks"].items()]
    table = ["| check | status |", "| --- | --- |"] + [f"| {name} | {status} |" for name, status in rows]
    return (
        f"# OTI7 CNR Verification Report - {DATE}\n\n"
        f"**Status:** `{report['status']}`  \n"
        f"**Promotion verdict:** `{report['promotion_verdict']}`  \n"
        f"**Validation safe:** `{report['validation_safe']}`  \n"
        f"**Outcome review opened:** `{report['outcome_review_opened']}`  \n"
        f"**Live effect:** `{report['live_effect']}`\n\n"
        + "\n".join(table)
        + "\n"
    )


def main() -> None:
    report = build_report()
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(render_report_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": {k: v["status"] for k, v in report["checks"].items()}}, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
