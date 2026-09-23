#!/usr/bin/env python3
"""Verify G12 OTI7 CNR post-result audit artifacts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


OUT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

BUILDER_PATH = OUT / "build_g12_oti7_cnr_post_result_audit_2026_05_08.py"

REQUIRED_JSON_MD_STEMS = [
    "G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER",
    "G12_OTI7_CNR_SCORING_SOURCE_NOLEAK_AUDIT",
    "G12_OTI7_CNR_ROW_EXCLUSION_DUPLICATE_AUDIT",
    "G12_OTI7_CNR_GEOMETRY_QUOTE_SIDE_CORRECTNESS_AUDIT",
    "G12_OTI7_CNR_NEGATIVE_RESULT_FORENSICS",
    "G12_OTI7_CNR_METHODOLOGY_EFFECTIVE_N_AUDIT",
    "G12_OTI7_CNR_NEXT_HYPOTHESIS_BLOCKER_MAP",
    "G12_OTI7_CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE",
    "G12_OTI7_CNR_COMPLETION_AUDIT",
]

REQUIRED_MD_ONLY = [
    "G12_OTI7_CNR_NEXT_LANE_PROMPT_PACK",
]

FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "config/",
    "prompts/",
    "src/",
    "knowledge_base/",
    "pipeline_state/",
    "run_agent.py",
    "start_all.bat",
    "scripts/canary",
    "scripts/watchdog",
)


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("g12_oti7_post_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_status_paths() -> list[str]:
    command = [
        "git",
        "-c",
        f"safe.directory={str(ROOT).replace(chr(92), '/')}",
        "-c",
        "core.excludesfile=",
        "status",
        "--porcelain",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return [line[3:].replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def verify_required_files() -> dict[str, Any]:
    missing = []
    for stem in REQUIRED_JSON_MD_STEMS:
        for suffix in [".json", ".md"]:
            path = OUT / f"{stem}_{DATE}{suffix}"
            if not path.exists():
                missing.append(str(path))
    for stem in REQUIRED_MD_ONLY:
        path = OUT / f"{stem}_{DATE}.md"
        if not path.exists():
            missing.append(str(path))
    return {"status": "PASS" if not missing else "FAIL", "missing": missing}


def verify_json_flags_and_parse() -> dict[str, Any]:
    issues = []
    parsed = []
    for stem in REQUIRED_JSON_MD_STEMS:
        path = OUT / f"{stem}_{DATE}.json"
        payload = read_json(path)
        parsed.append(path.name)
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append({"path": path.name, "issue": "promotion_verdict_not_preserved"})
        if payload.get("validation_safe") is not False:
            issues.append({"path": path.name, "issue": "validation_safe_not_false"})
        if payload.get("outcome_review_opened") is not False:
            issues.append({"path": path.name, "issue": "outcome_review_opened_not_false"})
        if payload.get("live_effect") is not False:
            issues.append({"path": path.name, "issue": "live_effect_not_false"})
    text_hits = []
    for path in sorted(OUT.glob(f"G12_OTI7_CNR_*{DATE}.*")):
        if path.suffix.lower() not in {".json", ".md", ".jsonl"}:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for needle in ['"validation_safe": true', '"outcome_review_opened": true', '"live_effect": true']:
            if needle in text:
                text_hits.append({"path": path.name, "needle": needle})
    return {
        "status": "PASS" if not issues and not text_hits else "FAIL",
        "parsed": parsed,
        "issues": issues,
        "unsafe_text_hits": text_hits,
    }


def verify_artifact_invariants() -> dict[str, Any]:
    decision = read_json(OUT / f"G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_{DATE}.json")
    source = read_json(OUT / f"G12_OTI7_CNR_SCORING_SOURCE_NOLEAK_AUDIT_{DATE}.json")
    rowdup = read_json(OUT / f"G12_OTI7_CNR_ROW_EXCLUSION_DUPLICATE_AUDIT_{DATE}.json")
    geometry = read_json(OUT / f"G12_OTI7_CNR_GEOMETRY_QUOTE_SIDE_CORRECTNESS_AUDIT_{DATE}.json")
    methodology = read_json(OUT / f"G12_OTI7_CNR_METHODOLOGY_EFFECTIVE_N_AUDIT_{DATE}.json")
    completion = read_json(OUT / f"G12_OTI7_CNR_COMPLETION_AUDIT_{DATE}.json")
    issues = []
    if decision.get("decision") != "ACCEPT_AS_QUARANTINED_NEGATIVE_DISCOVERY_EVIDENCE":
        issues.append("decision_not_accept")
    scope = rowdup["row_scope_controls"]
    if scope["accepted_rows_processed"] != 102 or scope["blocked_rows_excluded"] != 6098:
        issues.append("row_scope_counts_changed")
    if scope["accepted_blocked_row_sha_overlap_count"] != 0 or scope["accepted_blocked_row_number_overlap_count"] != 0:
        issues.append("blocked_overlap_nonzero")
    if scope["countable_rows"] != 54 or scope["duplicate_context_rows"] != 48:
        issues.append("duplicate_counts_changed")
    if source["source_controls"]["source_rehash_mismatch_count"] != 0:
        issues.append("source_rehash_mismatch")
    if source["source_controls"]["ready_input_forbidden_key_hit_count"] != 0:
        issues.append("ready_input_forbidden_key_hit")
    geom = geometry["geometry_quote_controls"]
    if geom["status_counts"] != {
        "SCORED_STOP_FIRST": 64,
        "SCORED_TARGET_FIRST": 12,
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 8,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 18,
    }:
        issues.append("geometry_status_counts_changed")
    if geom["issue_count"] != 0:
        issues.append("geometry_issue_count_nonzero")
    if methodology["effective_n"]["scored_countable_unique_primary_duplicate_groups"] != 22:
        issues.append("effective_n_changed")
    if methodology["dsr"]["status"] != "not_computable" or methodology["pbo"]["status"] != "not_computable":
        issues.append("methodology_promotional_stats_unexpected")
    if completion.get("can_mark_goal_complete") is not True:
        issues.append("completion_not_true")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def verify_builder_recomputes() -> dict[str, Any]:
    builder = load_builder()
    bundle = builder.build_bundle()
    artifacts = bundle["artifacts"]
    decision = artifacts["decision"][0]
    rowdup = artifacts["row_duplicate"][0]
    geometry = artifacts["geometry"][0]
    source = artifacts["source_noleak"][0]
    issues = []
    if decision["decision"] != "ACCEPT_AS_QUARANTINED_NEGATIVE_DISCOVERY_EVIDENCE":
        issues.append("builder_decision_not_accept")
    if rowdup["row_scope_controls"]["accepted_rows_processed"] != 102:
        issues.append("builder_accepted_count_changed")
    if rowdup["row_scope_controls"]["blocked_rows_excluded"] != 6098:
        issues.append("builder_blocked_count_changed")
    if geometry["geometry_quote_controls"]["issue_count"] != 0:
        issues.append("builder_geometry_issue_count_nonzero")
    if source["source_controls"]["source_rehash_mismatch_count"] != 0:
        issues.append("builder_source_rehash_mismatch")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def verify_forbidden_live_surface_diff() -> dict[str, Any]:
    paths = git_status_paths()
    hits = [
        path
        for path in paths
        if any(path.lower().startswith(prefix.lower()) for prefix in FORBIDDEN_LIVE_SURFACE_PREFIXES)
    ]
    return {"status": "PASS" if not hits else "FAIL", "changed_paths": paths, "forbidden_live_surface_hits": sorted(set(hits))}


def main() -> int:
    checks = {
        "required_files": verify_required_files(),
        "json_flags_and_parse": verify_json_flags_and_parse(),
        "artifact_invariants": verify_artifact_invariants(),
        "builder_recomputes": verify_builder_recomputes(),
        "forbidden_live_surface_diff": verify_forbidden_live_surface_diff(),
    }
    ok = all(check["status"] == "PASS" for check in checks.values())
    print(json.dumps({"status": "PASS" if ok else "FAIL", "checks": checks}, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
