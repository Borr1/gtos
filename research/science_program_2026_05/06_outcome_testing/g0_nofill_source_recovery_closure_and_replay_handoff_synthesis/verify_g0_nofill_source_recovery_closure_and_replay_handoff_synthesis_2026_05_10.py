"""Verifier for G0 NOFILL source-recovery closure synthesis artifacts."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import build_g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_2026_05_10 as builder


ROUTE_DIR = builder.ROUTE_DIR
RESULT_NAME = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


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


def git_changed_paths() -> list[str]:
    names: set[str] = set()
    commands = (["diff", "--name-only", "HEAD"], ["ls-files", "--others", "--exclude-standard"])
    for args in commands:
        result = subprocess.run(
            ["git", *args],
            cwd=builder.REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        names.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    return sorted(names)


def diff_scope() -> dict[str, Any]:
    paths = git_changed_paths()
    allowed_prefixes = [
        builder.ROUTE_DIR.relative_to(builder.REPO_ROOT).as_posix() + "/",
        builder.NEXT_PROMPT_PATH.relative_to(builder.REPO_ROOT).as_posix(),
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    ]
    forbidden_prefixes = [
        "config/",
        "prompts/",
        "src/",
        "pipeline_state/",
        "knowledge_base/",
        "data/ticks/",
    ]
    forbidden_suffixes = (".scid", ".parquet")
    forbidden = [
        path
        for path in paths
        if any(path.startswith(prefix) for prefix in forbidden_prefixes) or path.lower().endswith(forbidden_suffixes)
    ]
    outside_allowed = [
        path for path in paths if not any(path == prefix or path.startswith(prefix) for prefix in allowed_prefixes)
    ]
    return {
        "changed_or_untracked_paths": paths,
        "forbidden_live_or_raw_data_paths": forbidden,
        "outside_allowed_scope_paths": outside_allowed,
        "ok": forbidden == [] and outside_allowed == [],
    }


def scan_python_syntax() -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for path in ROUTE_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"path": builder.rel(path), "error": str(exc)})
    return failures


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required_paths = []
    for name in builder.JSON_ARTIFACTS + builder.MD_ARTIFACTS:
        required_paths.append(ROUTE_DIR / name)
    required_paths.append(builder.NEXT_PROMPT_PATH)
    required_paths.extend([ROUTE_DIR / name for name in (
        "build_g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_2026_05_10.py",
        "verify_g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_2026_05_10.py",
        "test_g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_2026_05_10.py",
    )])
    missing = [builder.rel(path) for path in required_paths if not path.exists()]
    if missing:
        failures.append({"check": "required_artifacts_exist", "missing": missing})

    parsed: dict[str, dict[str, Any]] = {}
    for name in builder.JSON_ARTIFACTS:
        path = ROUTE_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for name, payload in parsed.items():
        issues = safe_flag_issues(payload, name)
        if issues:
            failures.append({"check": "safe_flags", "file": name, "issues": issues})

    for md_path in ROUTE_DIR.glob("*.md"):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_tokens", "file": md_path.name, "missing": token})
        for token in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if token in text:
                failures.append({"check": "md_true_safe_flag", "file": md_path.name, "token": token})

    chain = parsed.get(f"{builder.PREFIX}_SOURCE_CHAIN_RECONCILIATION_LEDGER_{builder.DATE}.json", {})
    counts = chain.get("reconciled_counts", {})
    for key, expected in builder.EXPECTED_COUNTS.items():
        if counts.get(key) != expected:
            failures.append({"check": "reconciled_count", "key": key, "expected": expected, "actual": counts.get(key)})
    if chain.get("source_control_repair_required_before_broader_replay") is not False:
        failures.append({"check": "chain_repair_required", "value": chain.get("source_control_repair_required_before_broader_replay")})
    if len(chain.get("chain", [])) != 11:
        failures.append({"check": "chain_length", "value": len(chain.get("chain", []))})

    final_status = parsed.get(f"{builder.PREFIX}_FINAL_SOURCE_STATUS_CLOSURE_LEDGER_{builder.DATE}.json", {})
    if final_status.get("owner_tick_0020_0021_closed_as_current_blocker") is not True:
        failures.append({"check": "owner_tick_closed_current_blocker", "value": final_status.get("owner_tick_0020_0021_closed_as_current_blocker")})
    if final_status.get("owner_tick_0020_0021_future_mt5_native_need_only") is not True:
        failures.append({"check": "owner_tick_future_need_only", "value": final_status.get("owner_tick_0020_0021_future_mt5_native_need_only")})
    status_rows = {row.get("status_family"): row for row in final_status.get("status_rows", [])}
    for required in (
        "recovered_mt5_tick_source_evidence",
        "same_market_sierra_scid_context_evidence",
        "exact_mt5_native_bid_ask_flags_fallback_requests",
        "contamination_embargo_exclusions",
        "non_generatable_historical_gtos_source_state_requirements",
        "forward_capture_only_requirements",
        "replay_source_expansion_eligible_context",
    ):
        if required not in status_rows:
            failures.append({"check": "final_status_family", "missing": required})
    fallback = status_rows.get("exact_mt5_native_bid_ask_flags_fallback_requests", {})
    if fallback.get("can_block_broader_replay") is not False:
        failures.append({"check": "fallback_blocks_replay", "value": fallback})
    if fallback.get("owner_request_ids") != ["OWNER-TICK-0020", "OWNER-TICK-0021"]:
        failures.append({"check": "fallback_owner_ids", "value": fallback.get("owner_request_ids")})

    memo = parsed.get(f"{builder.PREFIX}_TWO_DATE_CLOSURE_MEMO_{builder.DATE}.json", {})
    if "OWNER-TICK-0020" not in memo.get("owner_tick_requests", {}) or "OWNER-TICK-0021" not in memo.get("owner_tick_requests", {}):
        failures.append({"check": "two_date_owner_requests", "value": memo.get("owner_tick_requests")})
    if memo.get("mt5_field_blockers", {}).get("hard_absent_fields") != ["bid", "ask", "flags"]:
        failures.append({"check": "two_date_field_blockers", "value": memo.get("mt5_field_blockers")})

    readiness = parsed.get(f"{builder.PREFIX}_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_{builder.DATE}.json", {})
    if readiness.get("source_control_repair_required_before_broader_replay") is not False:
        failures.append({"check": "readiness_repair_required", "value": readiness})
    if readiness.get("selected_next_route_id") != builder.NEXT_ROUTE_ID:
        failures.append({"check": "readiness_next_route", "value": readiness.get("selected_next_route_id")})

    ranking = parsed.get(f"{builder.PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{builder.DATE}.json", {})
    ranked = ranking.get("ranked_routes", [])
    if len(ranked) < 3:
        failures.append({"check": "ranking_min_three", "value": len(ranked)})
    if not ranked or ranked[0].get("route_id") != builder.NEXT_ROUTE_ID or ranked[0].get("selected") is not True:
        failures.append({"check": "rank1_route", "value": ranked[:1]})
    if ranking.get("real_unrepaired_source_control_defect_remains") is not False:
        failures.append({"check": "unrepaired_defect_flag", "value": ranking.get("real_unrepaired_source_control_defect_remains")})

    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("can_mark_goal_complete") is not True or completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_status", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})

    starter = parsed.get(f"{builder.PREFIX}_ONE_LINE_STARTER_{builder.DATE}.json", {})
    starter_text = starter.get("one_line_starter", "")
    if "\n" in starter_text or not starter_text.startswith("/goal Follow the full controlling prompt"):
        failures.append({"check": "one_line_starter_format", "value": starter_text})
    for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false", builder.NEXT_ROUTE_ID):
        if token not in starter_text:
            failures.append({"check": "one_line_starter_token", "missing": token})

    prompt_text = builder.NEXT_PROMPT_PATH.read_text(encoding="utf-8", errors="replace") if builder.NEXT_PROMPT_PATH.exists() else ""
    for token in (
        builder.NEXT_ROUTE_ID,
        "Mandatory Preflight",
        "NO_API_REPLAY_SOURCE_UNIVERSE_AND_DISCOVERY_INVENTORY_ONLY",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "Do not invent historical pending intent",
        "OWNER-TICK-0020",
        "OWNER-TICK-0021",
    ):
        if token not in prompt_text:
            failures.append({"check": "next_prompt_token", "missing": token})

    syntax_failures = scan_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_syntax", "failures": syntax_failures})

    scope = diff_scope()
    if not scope["ok"]:
        failures.append({"check": "diff_scope", "value": scope})

    result = {
        "ok": failures == [],
        "failures": failures,
        "warnings": warnings,
        "terminal_decision": builder.TERMINAL_DECISION if failures == [] else None,
        "can_mark_goal_complete": failures == [] and completion.get("can_mark_goal_complete") is True,
        "selected_next_route_id": ranked[0].get("route_id") if ranked else None,
        "owner_tick_0020_0021_closed_as_current_blocker": final_status.get("owner_tick_0020_0021_closed_as_current_blocker"),
        "source_control_repair_required_before_broader_replay": readiness.get("source_control_repair_required_before_broader_replay"),
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "diff_scope": scope,
    }
    (ROUTE_DIR / RESULT_NAME).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    print(json.dumps(verify(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
