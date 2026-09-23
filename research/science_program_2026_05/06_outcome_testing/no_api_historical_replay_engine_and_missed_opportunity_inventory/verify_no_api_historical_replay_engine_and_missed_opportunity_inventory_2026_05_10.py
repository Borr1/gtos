"""Verifier for the no-API historical replay source universe route."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import build_no_api_historical_replay_engine_and_missed_opportunity_inventory_2026_05_10 as builder


ROUTE_DIR = builder.ROUTE_DIR
PREFIX = builder.PREFIX
DATE = builder.DATE
RESULT_NAME = f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json"
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|unknown|maybe|later)\b|unresolved vague", re.I)
REQUIRED_JSON_FAMILIES = {
    "context_anchor",
    "local_source_safe_data_universe_ledger",
    "source_hash_deferral_manifest",
    "search_acquisition_ladder_ledger",
    "partition_contamination_noleak_ledger",
    "missed_opportunity_source_inventory",
    "replay_source_contract",
    "source_state_impossibility_projection_boundary_ledger",
    "next_route_ranking_ledger",
    "source_breadth_scope_audit",
    "noleak_safety_audit",
    "saturation_self_redteam_pass",
    "selected_next_full_controlling_prompt",
    "selected_next_one_line_starter",
    "completion_audit",
    "output_manifest",
}
REQUIRED_MARKDOWN = {
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md",
    f"{PREFIX}_SOURCE_UNIVERSE_LEDGER_{DATE}.md",
    f"{PREFIX}_PARTITION_CONTAMINATION_NOLEAK_LEDGER_{DATE}.md",
    f"{PREFIX}_MISSED_OPPORTUNITY_SOURCE_INVENTORY_{DATE}.md",
    f"{PREFIX}_REPLAY_SOURCE_CONTRACT_{DATE}.md",
    f"{PREFIX}_SOURCE_STATE_PROJECTION_BOUNDARY_LEDGER_{DATE}.md",
    f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.md",
    f"{PREFIX}_SOURCE_BREADTH_SCOPE_AUDIT_{DATE}.md",
    f"{PREFIX}_NOLEAK_SAFETY_AUDIT_{DATE}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
}
REQUIRED_SOURCE_ROW_FIELDS = {
    "source_row_id",
    "root_id",
    "absolute_path",
    "source_family",
    "evidence_class",
    "partition_assignment",
    "symbol",
    "timeframe",
    "source_date_range",
    "available_asof_fields",
    "missing_source_state_fields",
    "duplicate_key",
    "hash_policy",
    "hash_status",
    "eligible_flags",
    "forbidden_uses",
}
REQUIRED_MISSED_ROW_FIELDS = {
    "inventory_row_id",
    "source_family",
    "evidence_class",
    "symbol",
    "timestamp_window",
    "session_or_kill_zone",
    "available_asof_fields",
    "missing_source_state_fields",
    "duplicate_key",
    "contamination_status",
    "eligibility_flags",
    "forbidden_uses",
}
FORBIDDEN_TEXT_TOKENS = (
    "validation_safe=true",
    "outcome_review_opened=true",
    "live_effect=true",
    "PROMOTION_VERDICT_GO",
)
FORBIDDEN_RESULT_TOKENS_IN_INVENTORY = ("win_rate", "expectancy", "pnl")


def rel(path: Path) -> str:
    return builder.rel(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def safe_flag_issues(value: Any, path: str = "$") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in builder.SAFE_FALSE_KEYS and item is not False:
                issues.append({"path": child, "value": item})
            if key == "promotion_verdict" and item != builder.PROMOTION_VERDICT:
                issues.append({"path": child, "value": item})
            issues.extend(safe_flag_issues(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            issues.extend(safe_flag_issues(item, f"{path}[{idx}]"))
    return issues


def parse_artifacts() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    json_payloads: dict[str, dict[str, Any]] = {}
    for path in sorted(ROUTE_DIR.glob("*.json")):
        if path.name == RESULT_NAME:
            continue
        try:
            payload = load_json(path)
            json_payloads[path.name] = payload
            issues = safe_flag_issues(payload, path.name)
            if issues:
                failures.append({"check": "safe_flags", "file": path.name, "issues": issues})
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": path.name, "error": str(exc)})

    for path in sorted(ROUTE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "markdown_control_token", "file": path.name, "missing": token})
        for token in FORBIDDEN_TEXT_TOKENS:
            if token in text:
                failures.append({"check": "forbidden_text_token", "file": path.name, "token": token})
        match = PLACEHOLDER_RE.search(text)
        if match:
            failures.append({"check": "placeholder_text", "file": path.name, "token": match.group(0)})

    source_path = ROUTE_DIR / f"{PREFIX}_SOURCE_UNIVERSE_ROWS_{builder.DATE}.jsonl"
    missed_path = ROUTE_DIR / f"{PREFIX}_MISSED_OPPORTUNITY_SOURCE_INVENTORY_ROWS_{builder.DATE}.jsonl"
    source_rows = read_jsonl(source_path) if source_path.exists() else []
    missed_rows = read_jsonl(missed_path) if missed_path.exists() else []
    for path, rows in ((source_path, source_rows), (missed_path, missed_rows)):
        for idx, row in enumerate(rows, start=1):
            issues = safe_flag_issues(row, f"{path.name}:{idx}")
            if issues:
                failures.append({"check": "jsonl_safe_flags", "file": path.name, "line": idx, "issues": issues})
    return failures, json_payloads, source_rows, missed_rows


def verify_required_artifacts(json_payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    families = {payload.get("artifact_family") for payload in json_payloads.values()}
    missing = REQUIRED_JSON_FAMILIES - families
    if missing:
        failures.append({"check": "required_json_families", "missing": sorted(missing)})
    missing_md = sorted(name for name in REQUIRED_MARKDOWN if not (ROUTE_DIR / name).exists())
    if missing_md:
        failures.append({"check": "required_markdown", "missing": missing_md})
    for required in (
        f"{PREFIX}_SOURCE_UNIVERSE_ROWS_{DATE}.jsonl",
        f"{PREFIX}_MISSED_OPPORTUNITY_SOURCE_INVENTORY_ROWS_{DATE}.jsonl",
        "build_no_api_historical_replay_engine_and_missed_opportunity_inventory_2026_05_10.py",
        "verify_no_api_historical_replay_engine_and_missed_opportunity_inventory_2026_05_10.py",
        "test_no_api_historical_replay_engine_and_missed_opportunity_inventory_2026_05_10.py",
    ):
        if not (ROUTE_DIR / required).exists():
            failures.append({"check": "required_file", "missing": required})
    if not builder.NEXT_PROMPT_PATH.exists():
        failures.append({"check": "selected_next_prompt_exists", "missing": rel(builder.NEXT_PROMPT_PATH)})
    return failures


def verify_source_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if len(source_rows) < 100:
        failures.append({"check": "source_row_count", "value": len(source_rows)})
    source_families = {row.get("source_family") for row in source_rows}
    required_families = {
        "LOCAL_OHLCV_CSV",
        "MT5_TICK_PARQUET_CAPTURE",
        "SIERRA_NATIVE_CONTEXT",
        "SIERRA_DERIVED_OHLCV_EXPORT",
        "SHADOW_SOURCE_STATE_LOG",
        "RAW_OHLC_PRE_AI_REPLAY_LOG",
        "PRIOR_SOURCE_CONTROL_LEDGER",
    }
    missing_families = required_families - source_families
    if missing_families:
        failures.append({"check": "source_family_breadth", "missing": sorted(missing_families)})
    root_ids = {row.get("root_id") for row in source_rows}
    required_roots = {"current_worktree_data", "absolute_main_data_root", "absolute_main_tick_root", "sierra_chart_data_root", "prior_worktrees_root"}
    missing_roots = required_roots - root_ids
    if missing_roots:
        failures.append({"check": "root_breadth", "missing": sorted(missing_roots)})
    hash_complete = 0
    hash_deferred = 0
    for row in source_rows:
        missing = REQUIRED_SOURCE_ROW_FIELDS - set(row)
        if missing:
            failures.append({"check": "source_row_required_fields", "row": row.get("source_row_id"), "missing": sorted(missing)})
        if any(fragment in str(row.get("absolute_path", "")).lower() for fragment in builder.SENSITIVE_PATH_FRAGMENTS):
            failures.append({"check": "sensitive_source_path_leak", "row": row.get("source_row_id"), "path": row.get("absolute_path")})
        if row.get("hash_status") == "sha256_complete":
            hash_complete += 1
            if not row.get("sha256"):
                failures.append({"check": "missing_sha256", "row": row.get("source_row_id")})
        elif row.get("hash_status") == "deferred_large_file_requires_dedicated_hash_manifest":
            hash_deferred += 1
            if row.get("large_file_hash_deferral_id") == "not_applicable":
                failures.append({"check": "missing_large_file_deferral", "row": row.get("source_row_id")})
        else:
            failures.append({"check": "bad_hash_status", "row": row.get("source_row_id"), "value": row.get("hash_status")})
    if hash_complete == 0 or hash_deferred == 0:
        failures.append({"check": "hash_policy_coverage", "hash_complete": hash_complete, "hash_deferred": hash_deferred})
    return failures


def verify_missed_rows(missed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if len(missed_rows) < 100:
        failures.append({"check": "missed_inventory_row_count", "value": len(missed_rows)})
    families = {row.get("source_family") for row in missed_rows}
    if "MISSED_OPPORTUNITY_SHADOW_LOG" not in families:
        failures.append({"check": "missed_shadow_source_present", "families": sorted(str(f) for f in families)})
    if "PROJECTION_ONLY_HISTORICAL_MARKET_DATA_WINDOW" not in {row.get("evidence_class") for row in missed_rows}:
        failures.append({"check": "projection_only_rows_present"})
    duplicate_keys = set()
    for row in missed_rows:
        missing = REQUIRED_MISSED_ROW_FIELDS - set(row)
        if missing:
            failures.append({"check": "missed_required_fields", "row": row.get("inventory_row_id"), "missing": sorted(missing)})
        duplicate = row.get("duplicate_key")
        if duplicate in duplicate_keys:
            failures.append({"check": "missed_duplicate_key", "duplicate_key": duplicate})
        duplicate_keys.add(duplicate)
        flags = row.get("eligibility_flags", {})
        if flags.get("validation_safe") is not False or flags.get("live_effect") is not False:
            failures.append({"check": "missed_row_safe_flags", "row": row.get("inventory_row_id"), "flags": flags})
        scan_payload = {key: value for key, value in row.items() if key not in {"missing_source_state_fields", "forbidden_uses"}}
        text = json.dumps(scan_payload, sort_keys=True).lower()
        for token in FORBIDDEN_RESULT_TOKENS_IN_INVENTORY:
            if token in text:
                failures.append({"check": "forbidden_result_token_in_missed_inventory", "row": row.get("inventory_row_id"), "token": token})
                break
    return failures


def verify_ledgers(json_payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    completion = next((payload for payload in json_payloads.values() if payload.get("artifact_family") == "completion_audit"), {})
    if completion.get("can_mark_goal_complete") is not True or completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_audit_status", "completion": completion})
    if completion.get("missing_incomplete_or_weak_requirements") not in ([], None):
        failures.append({"check": "completion_missing_requirements", "value": completion.get("missing_incomplete_or_weak_requirements")})
    ranking = next((payload for payload in json_payloads.values() if payload.get("artifact_family") == "next_route_ranking_ledger"), {})
    if ranking.get("selected_next_route_id") != "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE":
        failures.append({"check": "selected_next_route", "value": ranking.get("selected_next_route_id")})
    if ranking.get("owner_tick_0020_0021_reopened") is not False:
        failures.append({"check": "owner_tick_reopened", "value": ranking.get("owner_tick_0020_0021_reopened")})
    noleak = next((payload for payload in json_payloads.values() if payload.get("artifact_family") == "noleak_safety_audit"), {})
    if noleak.get("audit_passed") is not True:
        failures.append({"check": "noleak_audit", "payload": noleak})
    breadth = next((payload for payload in json_payloads.values() if payload.get("artifact_family") == "source_breadth_scope_audit"), {})
    if len(breadth.get("by_symbol", {})) < 5 or len(breadth.get("by_source_family", {})) < 5:
        failures.append({"check": "breadth_counts", "by_symbol": breadth.get("by_symbol"), "by_source_family": breadth.get("by_source_family")})
    contract = next((payload for payload in json_payloads.values() if payload.get("artifact_family") == "replay_source_contract"), {})
    hard_rules = " ".join(contract.get("hard_fail_closed_rules", []))
    for phrase in ("Missing prompt", "Missing native bid", "account/order/history/deal/position", "PnL/R"):
        if phrase not in hard_rules:
            failures.append({"check": "contract_fail_closed_rule", "missing_phrase": phrase})
    projection = next((payload for payload in json_payloads.values() if payload.get("artifact_family") == "source_state_impossibility_projection_boundary_ledger"), {})
    owner_tick = projection.get("owner_tick_0020_0021_status", {})
    if owner_tick.get("reopened") is not False:
        failures.append({"check": "projection_owner_tick_status", "value": owner_tick})
    return failures


def verify_git_scope() -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    output = subprocess.run(["git", "diff", "--name-only"], cwd=builder.REPO_ROOT, text=True, capture_output=True, check=False)
    changed = [line.strip().replace("\\", "/") for line in output.stdout.splitlines() if line.strip()]
    allowed_prefixes = {
        "research/science_program_2026_05/06_outcome_testing/no_api_historical_replay_engine_and_missed_opportunity_inventory/",
        "research/science_program_2026_05/04_goal_prompts/NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE_GOAL_PROMPT_2026-05-10.md",
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    }
    forbidden = [
        path
        for path in changed
        if any(path.startswith(prefix) for prefix in builder.FORBIDDEN_DIFF_PREFIXES)
    ]
    if forbidden:
        failures.append({"check": "forbidden_live_surface_diff", "paths": forbidden})
    unexpected = [
        path
        for path in changed
        if not any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in allowed_prefixes)
    ]
    if unexpected:
        failures.append({"check": "unexpected_tracked_diff", "paths": unexpected})
    return failures


def verify_python_syntax() -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for path in (
        ROUTE_DIR / "build_no_api_historical_replay_engine_and_missed_opportunity_inventory_2026_05_10.py",
        ROUTE_DIR / "verify_no_api_historical_replay_engine_and_missed_opportunity_inventory_2026_05_10.py",
        ROUTE_DIR / "test_no_api_historical_replay_engine_and_missed_opportunity_inventory_2026_05_10.py",
    ):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"check": "python_syntax", "file": rel(path), "error": str(exc)})
    return failures


def build_result() -> dict[str, Any]:
    failures, json_payloads, source_rows, missed_rows = parse_artifacts()
    failures.extend(verify_required_artifacts(json_payloads))
    failures.extend(verify_source_rows(source_rows))
    failures.extend(verify_missed_rows(missed_rows))
    failures.extend(verify_ledgers(json_payloads))
    failures.extend(verify_git_scope())
    failures.extend(verify_python_syntax())
    result = builder.base_payload(
        "verification_result",
        ok=not failures,
        can_mark_goal_complete=not failures,
        failures=failures,
        source_row_count=len(source_rows),
        missed_inventory_row_count=len(missed_rows),
        selected_next_route_id="NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE",
        validation_safe=False,
        outcome_review_opened=False,
        live_effect=False,
    )
    return result


def main() -> int:
    result = build_result()
    path = ROUTE_DIR / RESULT_NAME
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "failures": result["failures"], "result": rel(path)}, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
