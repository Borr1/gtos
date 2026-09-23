#!/usr/bin/env python3
"""Verify the independent G12 XAUUSD Sierra SCID alternate source audit."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(ROUTE_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTE_DIR))

import build_g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit_2026_05_10 as builder  # noqa: E402


RESULT_PATH = ROUTE_DIR / f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|unknown|maybe|later)\b|unresolved vague", re.I)
FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures",
)
ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit/",
    "research/science_program_2026_05/06_outcome_testing/xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route/XAUUSD_SIERRA_SCID_ALT_ROUTE_VERIFICATION_RESULT_2026-05-10.json",
    ".context/",
)


def git_stdout(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def git_paths(args: list[str]) -> list[str]:
    return [line.strip().replace("\\", "/") for line in git_stdout(args).splitlines() if line.strip()]


def changed_or_untracked_paths() -> list[str]:
    paths = set(git_paths(["diff", "--name-only", "HEAD"]))
    paths.update(git_paths(["ls-files", "--others", "--exclude-standard"]))
    return sorted(paths)


def artifact_path(stem: str, suffix: str = "json") -> Path:
    return ROUTE_DIR / f"{builder.PREFIX}_{stem}_{builder.DATE}.{suffix}"


def load_json(stem: str) -> dict[str, Any]:
    return json.loads(artifact_path(stem).read_text(encoding="utf-8"))


def main() -> int:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    parsed: dict[str, dict[str, Any]] = {}

    for stem in builder.REQUIRED_ARTIFACT_STEMS:
        json_path = artifact_path(stem)
        md_path = artifact_path(stem, "md")
        if not json_path.exists():
            failures.append({"check": "json_artifact_exists", "artifact": json_path.name})
            continue
        if not md_path.exists():
            failures.append({"check": "md_artifact_exists", "artifact": md_path.name})
        try:
            parsed[stem] = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_artifact_parses", "artifact": json_path.name, "error": str(exc)})

    source = parsed.get("SOURCE_HASH_HEADER_COVERAGE_REAUDIT", {})
    candidates = parsed.get("CANDIDATE_WINDOW_REPRODUCIBILITY_AUDIT", {})
    fields = parsed.get("MT5_FIELD_BLOCKER_REAUDIT", {})
    decision = parsed.get("DECISION_LEDGER", {})
    noleak = parsed.get("NOLEAK_RAW_DATA_STAGING_AUDIT", {})
    next_step = parsed.get("NEXT_STEP_RECOMMENDATION", {})
    completion = parsed.get("COMPLETION_AUDIT", {})

    if source:
        actual_sha = builder.sha256_file(builder.SCID_PATH)
        if source.get("raw_source", {}).get("source_sha256") != actual_sha:
            failures.append({"check": "scid_sha_recomputed", "artifact": source.get("raw_source", {}).get("source_sha256"), "actual": actual_sha})
        header = builder.parse_scid_header(builder.SCID_PATH)
        if source.get("scid_header", {}).get("record_count") != header.record_count:
            failures.append({"check": "scid_record_count_recomputed", "artifact": source.get("scid_header", {}).get("record_count"), "actual": header.record_count})
        counts = {row["source_date"]: row["row_count"] for row in source.get("day_coverage", [])}
        if counts != builder.EXPECTED_DAY_COUNTS:
            failures.append({"check": "day_counts_expected", "actual": counts, "expected": builder.EXPECTED_DAY_COUNTS})
        if source.get("target_route_comparison", {}).get("comparison_status") != "MATCH":
            failures.append({"check": "source_target_comparison_match", "mismatches": source.get("target_route_comparison", {}).get("mismatches")})

    if candidates:
        rows = candidates.get("candidate_coverage", [])
        if len(rows) != 3:
            failures.append({"check": "candidate_count", "actual": len(rows)})
        for row in rows:
            cid = row.get("candidate_id")
            if row.get("rows_plus_minus_60_seconds") != builder.EXPECTED_CANDIDATE_ROWS_60S.get(cid):
                failures.append({"check": "candidate_pm60_rows", "candidate_id": cid, "actual": row.get("rows_plus_minus_60_seconds")})
            expected_delta = builder.EXPECTED_NEAREST_DELTA_MS.get(cid)
            if expected_delta is None or abs(float(row.get("nearest_abs_delta_ms")) - float(expected_delta)) > 0.0005:
                failures.append({"check": "candidate_nearest_delta", "candidate_id": cid, "actual": row.get("nearest_abs_delta_ms")})
            if not row.get("nearest_records", {}).get("nearest_record"):
                failures.append({"check": "candidate_nearest_record_present", "candidate_id": cid})
        if candidates.get("target_route_comparison", {}).get("comparison_status") != "MATCH":
            failures.append({"check": "candidate_target_comparison_match", "mismatches": candidates.get("target_route_comparison", {}).get("mismatches")})
        april16 = [row for row in rows if row.get("source_date") == "2026-04-16"]
        if not april16 or not all(row.get("contamination_or_embargo_excluded") is True for row in april16):
            failures.append({"check": "april16_contamination_embargo_preserved"})

    if fields:
        if fields.get("mt5_tick_contract_satisfied") is not False:
            failures.append({"check": "mt5_contract_not_satisfied"})
        if sorted(fields.get("hard_absent_fields", [])) != sorted(builder.HARD_ABSENT_MT5_FIELDS):
            failures.append({"check": "hard_absent_fields", "actual": fields.get("hard_absent_fields")})
        if sorted(fields.get("proxy_only_non_equivalent_fields", [])) != sorted(builder.PROXY_ONLY_NON_EQUIVALENT_FIELDS):
            failures.append({"check": "proxy_only_fields", "actual": fields.get("proxy_only_non_equivalent_fields")})
        if fields.get("substitution_check", {}).get("scid_ohlc_substituted_for_mt5_bid_or_ask") is not False:
            failures.append({"check": "no_ohlc_bid_ask_substitution"})
        if fields.get("target_route_comparison", {}).get("comparison_status") != "MATCH":
            failures.append({"check": "field_target_comparison_match", "mismatches": fields.get("target_route_comparison", {}).get("mismatches")})

    if decision:
        if decision.get("terminal_decision") != "ACCEPT_TARGET_ROUTE_AS_SOURCE_HASHED_SCID_CONTEXT_ONLY_WITH_MT5_TICK_BLOCKERS_OPEN":
            failures.append({"check": "terminal_decision", "actual": decision.get("terminal_decision")})
        if decision.get("mt5_tick_recovery_equivalent") is not False:
            failures.append({"check": "decision_not_mt5_recovery"})
        if decision.get("closes_owner_tick_requests") is not False:
            failures.append({"check": "owner_tick_requests_not_closed"})
        if decision.get("owner_manual_mt5_export_still_required") is not True:
            failures.append({"check": "manual_export_still_required"})
        if decision.get("two_dates_open_ended_drag_closed_for_scid_evidence_class") is not True:
            failures.append({"check": "two_dates_not_open_ended_drag"})

    if noleak:
        if noleak.get("noleak_status") != "PASS":
            failures.append({"check": "noleak_status", "actual": noleak.get("noleak_status")})
        if noleak.get("forbidden_value_families_present_in_scid") is not False:
            failures.append({"check": "forbidden_value_families_absent"})
        raw_violations = noleak.get("raw_market_data_status", {}).get("raw_market_data_violations", [])
        if raw_violations:
            failures.append({"check": "raw_market_data_not_staged_or_tracked", "paths": raw_violations})

    if next_step:
        text = next_step.get("exact_next_step", "")
        if "source expansion and replay infrastructure" not in text:
            failures.append({"check": "exact_next_step_routes_back_to_source_expansion"})
        if next_step.get("no_more_same_evidence_class_work_needed_for_these_dates") is not True:
            failures.append({"check": "no_open_ended_same_evidence_class_drag"})

    if completion:
        if completion.get("completion_status") != "PASS" or completion.get("can_mark_goal_complete") is not True:
            failures.append({"check": "completion_status", "actual": completion.get("completion_status")})
        checklist = completion.get("prompt_to_artifact_checklist", [])
        if any(row.get("status") != "PASS" for row in checklist):
            failures.append({"check": "completion_checklist_all_pass", "checklist": checklist})

    for stem in builder.REQUIRED_ARTIFACT_STEMS:
        for suffix in ("json", "md"):
            path = artifact_path(stem, suffix)
            if path.exists() and PLACEHOLDER_RE.search(path.read_text(encoding="utf-8")):
                failures.append({"check": "placeholder_scan", "path": builder.rel(path)})

    for payload in parsed.values():
        if payload.get("promotion_verdict") != builder.PROMOTION_VERDICT:
            failures.append({"check": "promotion_verdict", "artifact": payload.get("artifact_family")})
        for key, expected in builder.SAFE_FALSE_PAYLOAD.items():
            if payload.get(key) is not expected:
                failures.append({"check": "safe_false_flag", "artifact": payload.get("artifact_family"), "key": key, "value": payload.get(key)})

    changed_raw = [path for path in git_paths(["diff", "--name-only", "HEAD"]) if path.lower().endswith((".parquet", ".csv", ".scid"))]
    staged_raw = [path for path in git_paths(["diff", "--cached", "--name-only"]) if path.lower().endswith((".parquet", ".csv", ".scid"))]
    untracked_raw = [path for path in git_paths(["ls-files", "--others", "--exclude-standard"]) if path.lower().endswith((".parquet", ".csv", ".scid"))]
    raw_market_data_violations = [
        path
        for path in [*changed_raw, *staged_raw, *untracked_raw]
        if path.lower().endswith((".scid", ".parquet")) or path.startswith("data/") or "raw" in path.lower()
    ]
    if raw_market_data_violations:
        failures.append({"check": "workspace_raw_market_data_not_tracked_staged_or_visible_untracked", "paths": raw_market_data_violations})

    changed_paths = changed_or_untracked_paths()
    forbidden_paths = [path for path in changed_paths if any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)]
    outside_allowed = [path for path in changed_paths if not any(path.startswith(prefix) for prefix in ALLOWED_DIFF_PREFIXES)]
    if forbidden_paths:
        failures.append({"check": "forbidden_live_surface_diff_paths", "paths": forbidden_paths})
    if outside_allowed:
        warnings.append({"check": "outside_allowed_scope_paths_in_workspace", "paths": outside_allowed})

    result = {
        "schema_version": builder.SCHEMA_VERSION,
        "route_id": builder.ROUTE_ID,
        "artifact_family": "verification_result",
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "warnings": warnings,
        "changed_paths": changed_paths,
        "raw_market_data_violations": raw_market_data_violations,
        "promotion_verdict": builder.PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
