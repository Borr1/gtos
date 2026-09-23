#!/usr/bin/env python3
"""Verify the XAUUSD Sierra SCID alternate source-control route."""

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

import build_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_2026_05_10 as builder  # noqa: E402


RESULT_PATH = ROUTE_DIR / f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"
FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures",
)
ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route/",
    "research/science_program_2026_05/04_goal_prompts/G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-10.md",
    ".context/",
)
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|unknown|maybe|later)\b|unresolved vague", re.I)


def git_stdout(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def git_paths(args: list[str]) -> list[str]:
    return [line.strip().replace("\\", "/") for line in git_stdout(args).splitlines() if line.strip()]


def changed_or_untracked_paths() -> list[str]:
    paths = set(git_paths(["diff", "--name-only", "HEAD"]))
    paths.update(git_paths(["ls-files", "--others", "--exclude-standard"]))
    return sorted(paths)


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def artifact_name(stem: str, suffix: str) -> str:
    return f"{builder.PREFIX}_{stem}_{builder.DATE}.{suffix}"


def all_payloads(parsed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return list(parsed.values())


def main() -> int:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    parsed: dict[str, dict[str, Any]] = {}

    for stem in builder.REQUIRED_ARTIFACT_STEMS:
        json_name = artifact_name(stem, "json")
        md_name = artifact_name(stem, "md")
        json_path = ROUTE_DIR / json_name
        md_path = ROUTE_DIR / md_name
        if not json_path.exists():
            failures.append({"check": "json_artifact_exists", "artifact": json_name})
            continue
        if not md_path.exists():
            failures.append({"check": "md_artifact_exists", "artifact": md_name})
        try:
            parsed[json_name] = load_json(json_name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parses", "artifact": json_name, "error": str(exc)})

    source = parsed.get(artifact_name("SCID_SOURCE_HASH_HEADER_AUDIT", "json"), {})
    coverage = parsed.get(artifact_name("SCID_DAY_CANDIDATE_COVERAGE_LEDGER", "json"), {})
    field_audit = parsed.get(artifact_name("MT5_TICK_CONTRACT_FIELD_COMPARISON_AUDIT", "json"), {})
    decision = parsed.get(artifact_name("ALTERNATE_SOURCE_ADMISSIBILITY_DECISION_LEDGER", "json"), {})
    boundary = parsed.get(artifact_name("SOURCE_STATE_NOLEAK_BOUNDARY_AUDIT", "json"), {})
    owner = parsed.get(artifact_name("OWNER_MANUAL_EXPORT_FALLBACK_MANIFEST", "json"), {})
    packet = parsed.get(artifact_name("SOURCE_HASHED_ALTERNATE_PACKET", "json"), {})
    blockers = parsed.get(artifact_name("FIELD_MISMATCH_BLOCKER_LEDGER", "json"), {})
    next_g12 = parsed.get(artifact_name("NEXT_G12_AUDIT_PROMPT_PACK", "json"), {})
    completion = parsed.get(artifact_name("COMPLETION_AUDIT", "json"), {})

    if source:
        actual_sha = builder.sha256_file(builder.SCID_PATH)
        if source.get("raw_source", {}).get("source_sha256") != actual_sha:
            failures.append(
                {
                    "check": "raw_scid_sha256_matches",
                    "artifact_sha": source.get("raw_source", {}).get("source_sha256"),
                    "actual_sha": actual_sha,
                }
            )
        header = builder.parse_scid_header(builder.SCID_PATH)
        if source.get("scid_header", {}).get("record_count") != header.record_count:
            failures.append({"check": "scid_record_count_matches_actual"})
        if source.get("scid_header", {}).get("magic") != "SCID":
            failures.append({"check": "scid_magic"})

    if coverage:
        actual_header = builder.parse_scid_header(builder.SCID_PATH)
        actual_counts = {
            source_date: builder.day_summary(builder.SCID_PATH, actual_header, source_date)["row_count"]
            for source_date in ["2026-04-15", "2026-04-16"]
        }
        artifact_counts = {row["source_date"]: row["row_count"] for row in coverage.get("day_coverage", [])}
        if actual_counts != artifact_counts:
            failures.append({"check": "day_counts_recompute", "artifact": artifact_counts, "actual": actual_counts})
        if actual_counts != {"2026-04-15": 72119, "2026-04-16": 70048}:
            failures.append({"check": "day_counts_match_prompt_expected", "actual": actual_counts})
        candidate_rows = coverage.get("candidate_coverage", [])
        if len(candidate_rows) != 3:
            failures.append({"check": "candidate_count", "value": len(candidate_rows)})
        for row in candidate_rows:
            if not row.get("nearest_records", {}).get("nearest_record"):
                failures.append({"check": "candidate_nearest_record_present", "candidate": row.get("candidate_id")})
            if int(row.get("rows_plus_minus_60_seconds", 0)) <= 0:
                failures.append({"check": "candidate_plus_minus_60_rows", "candidate": row.get("candidate_id")})
        april16 = [row for row in candidate_rows if row.get("source_date") == "2026-04-16"]
        if not april16 or not all(row.get("contamination_or_embargo_excluded") is True for row in april16):
            failures.append({"check": "april16_contamination_embargo_preserved"})

    if field_audit:
        if field_audit.get("mt5_tick_contract_satisfied") is not False:
            failures.append({"check": "mt5_tick_contract_not_satisfied"})
        if sorted(field_audit.get("hard_absent_fields", [])) != sorted(builder.HARD_ABSENT_MT5_FIELDS):
            failures.append({"check": "hard_absent_fields", "value": field_audit.get("hard_absent_fields")})
        fields = {row.get("field"): row for row in field_audit.get("field_rows", [])}
        for required in builder.REQUIRED_MT5_TICK_FIELDS:
            if required not in fields:
                failures.append({"check": "required_field_compared", "field": required})
        for field in ["bid", "ask", "flags"]:
            if fields.get(field, {}).get("presence_status") != "ABSENT":
                failures.append({"check": "hard_absent_field_status", "field": field, "row": fields.get(field)})

    if decision:
        if decision.get("source_hashed_alternate_packet_should_be_emitted") is not True:
            failures.append({"check": "alternate_packet_should_be_emitted"})
        if decision.get("mt5_tick_recovery_equivalent") is not False:
            failures.append({"check": "decision_mt5_equivalence_false"})
        if decision.get("closes_owner_tick_requests") is not False:
            failures.append({"check": "owner_requests_not_closed"})
        if decision.get("owner_manual_mt5_tick_export_still_required") is not True:
            failures.append({"check": "manual_export_still_required"})

    if boundary:
        if boundary.get("boundary_status") != "PASS_SOURCE_CONTROL_ONLY":
            failures.append({"check": "boundary_status", "value": boundary.get("boundary_status")})
        if boundary.get("forbidden_value_families_present_in_scid") is not False:
            failures.append({"check": "forbidden_values_absent"})

    if owner:
        expected_paths = {"data/ticks/XAUUSD/2026-04-15.parquet", "data/ticks/XAUUSD/2026-04-16.parquet"}
        paths = {row.get("target_path_template") for row in owner.get("market_data_export_requests", [])}
        if owner.get("remaining_market_data_export_request_count") != 2 or paths != expected_paths:
            failures.append({"check": "owner_manual_export_requests", "count": owner.get("remaining_market_data_export_request_count"), "paths": sorted(paths)})
        for row in owner.get("market_data_export_requests", []):
            if sorted(row.get("required_fields", [])) != sorted(builder.REQUIRED_MT5_TICK_FIELDS):
                failures.append({"check": "owner_required_fields", "owner_request_id": row.get("owner_request_id")})

    if packet:
        if packet.get("packet_admissibility_status") != "ADMISSIBLE_AS_SCID_MARKET_ACTIVITY_CONTEXT_ONLY":
            failures.append({"check": "packet_admissibility_status", "value": packet.get("packet_admissibility_status")})
        if packet.get("mt5_tick_recovery_equivalent") is not False:
            failures.append({"check": "packet_non_equivalent_to_mt5"})
        if packet.get("closes_owner_tick_requests") is not False:
            failures.append({"check": "packet_does_not_close_owner_requests"})
        if source and packet.get("source_hash") != source.get("raw_source", {}).get("source_sha256"):
            failures.append({"check": "packet_source_hash_matches_source_audit"})

    if blockers:
        if blockers.get("terminal_blocker_status") != "MT5_BID_ASK_TICK_CONTRACT_NOT_SATISFIED_BY_SCID":
            failures.append({"check": "blocker_terminal_status", "value": blockers.get("terminal_blocker_status")})
        if blockers.get("owner_tick_requests_remain_open") is not True:
            failures.append({"check": "owner_requests_remain_open"})

    if next_g12:
        prompt_path = REPO_ROOT / next_g12.get("full_next_g12_prompt_path", "")
        if not prompt_path.exists():
            failures.append({"check": "next_g12_prompt_file_exists", "path": str(prompt_path)})
        if not next_g12.get("one_line_starter"):
            failures.append({"check": "next_g12_one_line_starter"})

    if completion and completion.get("completion_status") != "PASS":
        failures.append({"check": "completion_audit_pass", "value": completion.get("completion_status")})

    for payload in all_payloads(parsed):
        if payload.get("promotion_verdict") != builder.PROMOTION_VERDICT:
            failures.append({"check": "promotion_verdict", "artifact": payload.get("artifact_family")})
        for key, expected in builder.SAFE_FALSE_PAYLOAD.items():
            if payload.get(key) is not expected:
                failures.append({"check": "safe_false_flag", "artifact": payload.get("artifact_family"), "key": key, "value": payload.get(key)})

    for path in ROUTE_DIR.glob(f"{builder.PREFIX}_*_{builder.DATE}.*"):
        if path.suffix.lower() in {".json", ".md"}:
            text = path.read_text(encoding="utf-8")
            if PLACEHOLDER_RE.search(text):
                failures.append({"check": "placeholder_scan", "path": builder.rel(path)})

    changed_raw = [
        path
        for path in git_paths(["diff", "--name-only", "HEAD"])
        if path.lower().endswith((".parquet", ".csv", ".scid"))
    ]
    staged_raw = [
        path
        for path in git_paths(["diff", "--cached", "--name-only"])
        if path.lower().endswith((".parquet", ".csv", ".scid"))
    ]
    visible_untracked_raw = [
        path
        for path in git_paths(["ls-files", "--others", "--exclude-standard"])
        if path.lower().endswith((".parquet", ".csv", ".scid"))
    ]
    raw_market_data_violations = [
        path
        for path in [*changed_raw, *staged_raw, *visible_untracked_raw]
        if path.startswith("data/") or path.endswith(".scid") or path.startswith("C:/SierraChart/")
    ]
    if raw_market_data_violations:
        failures.append({"check": "raw_market_data_not_tracked_staged_or_visible_untracked", "paths": raw_market_data_violations})

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
