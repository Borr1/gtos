"""Verifier for G0 SCID blocked-17 LTF/proxy unblocking synthesis."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import build_g0_scid_ltf_proxy_blocked17_unblocking_synthesis_2026_05_13 as builder


ROUTE_DIR = builder.ROUTE_DIR
RESULT_JSON = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"
RESULT_MD = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.md"


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
        for index, item in enumerate(value):
            issues.extend(safe_flag_issues(item, f"{path}[{index}]"))
    return issues


def git_changed_paths() -> list[str]:
    names: set[str] = set()
    for args in (["diff", "--name-only", "HEAD"], ["ls-files", "--others", "--exclude-standard"]):
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
    forbidden = [path for path in paths if any(path.startswith(prefix) for prefix in builder.FORBIDDEN_DIFF_PREFIXES)]
    outside_allowed = [
        path for path in paths if not any(path.startswith(prefix) for prefix in builder.ALLOWED_DIFF_PREFIXES)
    ]
    return {
        "changed_or_untracked_paths": paths,
        "forbidden_live_surface_paths": forbidden,
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


def scan_artifact_text() -> dict[str, Any]:
    forbidden_hits: list[dict[str, str]] = []
    for path in sorted(list(ROUTE_DIR.glob("*.json")) + list(ROUTE_DIR.glob("*.md")) + list(ROUTE_DIR.glob("*.txt"))):
        if path.name in {RESULT_JSON, RESULT_MD}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for fragment in builder.FORBIDDEN_ARTIFACT_SUBSTRINGS:
            if fragment.lower() in text:
                forbidden_hits.append({"path": path.name, "fragment": fragment})
    for path in sorted(builder.PROMPT_ROOT.glob("*_2026-05-13.md")):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for token in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if token in text:
                forbidden_hits.append({"path": builder.rel(path), "fragment": token})
    return {"forbidden_hits": forbidden_hits, "ok": forbidden_hits == []}


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required = list(builder.JSON_ARTIFACTS) + list(builder.MD_ARTIFACTS) + [
        "build_g0_scid_ltf_proxy_blocked17_unblocking_synthesis_2026_05_13.py",
        "verify_g0_scid_ltf_proxy_blocked17_unblocking_synthesis_2026_05_13.py",
        "test_g0_scid_ltf_proxy_blocked17_unblocking_synthesis_2026_05_13.py",
        f"{builder.PREFIX}_FOCUSED_TEST_RESULT_{builder.DATE}.json",
        f"{builder.PREFIX}_FOCUSED_TEST_RESULT_{builder.DATE}.md",
    ]
    for pack in builder.PROMPT_PACKS:
        required.append(pack["starter_filename"])
        prompt_path = builder.PROMPT_ROOT / pack["prompt_filename"]
        if not prompt_path.exists():
            failures.append({"check": "prompt_file_exists", "missing": builder.rel(prompt_path)})

    missing = [name for name in required if not (ROUTE_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_route_artifacts_exist", "missing": missing})

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
        if md_path.name == RESULT_MD:
            continue
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_tokens", "file": md_path.name, "missing": token})

    decision = parsed.get(f"{builder.PREFIX}_DECISION_LEDGER_{builder.DATE}.json", {})
    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    counts = decision.get("denominator_counts", {})
    expected_counts = {
        "blocked17_included": 17,
        "other_blocked15_excluded": 15,
        "ready8_excluded": 8,
    }
    for key, value in expected_counts.items():
        if counts.get(key) != value:
            failures.append({"check": "denominator_counts", "key": key, "value": counts.get(key)})
    if decision.get("source_inventory_count") != 13024:
        failures.append({"check": "source_inventory_count", "value": decision.get("source_inventory_count")})

    ranking = parsed.get(f"{builder.PREFIX}_ROUTE_RANKING_MATRIX_{builder.DATE}.json", {})
    ranked_routes = ranking.get("ranked_routes", [])
    if len(ranked_routes) != 5:
        failures.append({"check": "ranked_route_count", "value": len(ranked_routes)})
    expected_route_order = [pack["route_id"] for pack in builder.PROMPT_PACKS]
    if [row.get("route_id") for row in ranked_routes] != expected_route_order:
        failures.append({"check": "ranked_route_order", "value": [row.get("route_id") for row in ranked_routes]})
    for row in ranked_routes:
        if row.get("may_open_results_now") is not False:
            failures.append({"check": "ranked_route_result_gate", "route_id": row.get("route_id")})
        if not row.get("card_ids_touched"):
            warnings.append({"check": "ranked_route_card_touch_empty", "route_id": row.get("route_id")})

    dep_map = parsed.get(f"{builder.PREFIX}_BLOCKED17_DEPENDENCY_TO_ROUTE_MAP_{builder.DATE}.json", {})
    cards = dep_map.get("cards", [])
    if dep_map.get("card_count") != 17 or len(cards) != 17:
        failures.append({"check": "dependency_card_count", "value": dep_map.get("card_count"), "len": len(cards)})
    if len({row.get("card_id") for row in cards}) != 17:
        failures.append({"check": "dependency_unique_cards", "value": [row.get("card_id") for row in cards]})
    for row in cards:
        if row.get("may_score_results_now") is not False:
            failures.append({"check": "card_result_gate", "card_id": row.get("card_id")})
        if not row.get("recommended_route_ids"):
            failures.append({"check": "card_route_missing", "card_id": row.get("card_id")})

    materialization = parsed.get(f"{builder.PREFIX}_SOURCE_MATERIALIZATION_OPPORTUNITY_LEDGER_{builder.DATE}.json", {})
    if materialization.get("source_inventory_count") != 13024:
        failures.append({"check": "materialization_inventory_count", "value": materialization.get("source_inventory_count")})
    if materialization.get("source_status_rows_inspected") != 17:
        failures.append({"check": "materialization_source_status_rows", "value": materialization.get("source_status_rows_inspected")})
    if len(materialization.get("opportunities", [])) != 5:
        failures.append({"check": "materialization_opportunity_count", "value": len(materialization.get("opportunities", []))})

    prompt_pack = parsed.get(f"{builder.PREFIX}_PARSER_PROXY_CAPTURE_ACCESS_PROMPT_PACK_LEDGER_{builder.DATE}.json", {})
    if prompt_pack.get("prompt_pack_count") != 5 or len(prompt_pack.get("rows", [])) != 5:
        failures.append({"check": "prompt_pack_count", "value": prompt_pack.get("prompt_pack_count")})
    for row in prompt_pack.get("rows", []):
        if not (builder.REPO_ROOT / row["prompt_path"]).exists():
            failures.append({"check": "prompt_path_exists", "path": row["prompt_path"]})
        if not (builder.REPO_ROOT / row["starter_path"]).exists():
            failures.append({"check": "starter_path_exists", "path": row["starter_path"]})
        starter = row.get("one_line_starter", "")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in starter:
                failures.append({"check": "starter_safe_token", "route_id": row.get("route_id"), "missing": token})

    parallel = parsed.get(f"{builder.PREFIX}_PARALLELIZATION_LEDGER_{builder.DATE}.json", {})
    if parallel.get("parallelization_decision") != "FIVE_DISJOINT_SOURCE_CONTROL_ROUTES_CAN_RUN_IN_PARALLEL_AFTER_THIS_G0_SYNTHESIS":
        failures.append({"check": "parallelization_decision", "value": parallel.get("parallelization_decision")})

    noleak = parsed.get(f"{builder.PREFIX}_DENOMINATOR_NOLEAK_SAFE_FLAG_AUDIT_{builder.DATE}.json", {})
    if noleak.get("ok") is not True:
        failures.append({"check": "noleak_ok", "value": noleak.get("failures")})
    if noleak.get("included_card_count") != 17:
        failures.append({"check": "noleak_included_count", "value": noleak.get("included_card_count")})
    if noleak.get("excluded_blocked15_card_count") != 15:
        failures.append({"check": "noleak_excluded_count", "value": noleak.get("excluded_blocked15_card_count")})
    if noleak.get("broker_native_cfd_truth_claims") != 0:
        failures.append({"check": "broker_native_cfd_truth_claims", "value": noleak.get("broker_native_cfd_truth_claims")})
    if noleak.get("raw_market_blob_commits_added") != 0:
        failures.append({"check": "raw_market_blob_commits_added", "value": noleak.get("raw_market_blob_commits_added")})

    saturation = parsed.get(f"{builder.PREFIX}_SATURATION_SELF_REDTEAM_{builder.DATE}.json", {})
    considered = set(saturation.get("anti_boxing_routes_considered", []))
    if set(expected_route_order) - considered:
        failures.append({"check": "saturation_route_coverage", "missing": sorted(set(expected_route_order) - considered)})
    if len(saturation.get("saturation_questions", [])) < 7:
        failures.append({"check": "saturation_question_count", "value": len(saturation.get("saturation_questions", []))})

    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_standard", "value": completion.get("completion_standard_satisfied")})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})

    syntax_failures = scan_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_syntax", "failures": syntax_failures})

    text_scan = scan_artifact_text()
    if not text_scan["ok"]:
        failures.append({"check": "artifact_forbidden_text_scan", "hits": text_scan["forbidden_hits"]})

    scope = diff_scope()
    if not scope["ok"]:
        failures.append({"check": "diff_scope", "scope": scope})

    ok = failures == []
    result = {
        "schema_version": builder.SCHEMA_VERSION,
        "route_id": builder.ROUTE_ID,
        "artifact_family": "VERIFICATION_RESULT",
        "generated_at_utc": builder.now_utc(),
        "ok": ok,
        "can_mark_goal_complete": ok,
        "failure_count": len(failures),
        "failures": failures,
        "warnings": warnings,
        "terminal_decision": builder.TERMINAL_DECISION if ok else "VERIFY_FAILED",
        "card_count": dep_map.get("card_count"),
        "source_inventory_count": decision.get("source_inventory_count"),
        "ranked_route_count": len(ranked_routes),
        "prompt_pack_count": prompt_pack.get("prompt_pack_count"),
        "diff_scope": scope,
        "text_scan": text_scan,
        "promotion_verdict": builder.PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    return result


def write_result(result: dict[str, Any]) -> None:
    (ROUTE_DIR / RESULT_JSON).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (
        "# G0 SCID LTF Proxy Blocked-17 Synthesis Verification Result\n\n"
        f"- `NO_PROMOTION_VERDICT`\n"
        "- `validation_safe=false`\n"
        "- `outcome_review_opened=false`\n"
        "- `live_effect=false`\n\n"
        "```json\n"
        f"{json.dumps(result, indent=2, sort_keys=True)}\n"
        "```\n"
    )
    (ROUTE_DIR / RESULT_MD).write_text(md, encoding="utf-8")


if __name__ == "__main__":
    verification = verify()
    write_result(verification)
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
