"""Verifier for G0 NOFILL historical source-expansion synthesis artifacts."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import build_g0_nofill_historical_source_expansion_packet_synthesis_control_review_2026_05_10 as builder


ROUTE_DIR = builder.ROUTE_DIR
RESULT_NAME = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"
PLACEHOLDER_FRAGMENTS = ("tbd", "todo", "maybe", "later")


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
    placeholder_hits: list[dict[str, str]] = []
    for path in sorted(list(ROUTE_DIR.glob("*.json")) + list(ROUTE_DIR.glob("*.md"))):
        if path.name == RESULT_NAME:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        for fragment in builder.FORBIDDEN_ARTIFACT_SUBSTRINGS:
            if fragment.lower() in lower:
                forbidden_hits.append({"path": path.name, "fragment": fragment})
        for fragment in PLACEHOLDER_FRAGMENTS:
            if fragment in lower:
                placeholder_hits.append({"path": path.name, "fragment": fragment})
    return {
        "forbidden_hits": forbidden_hits,
        "placeholder_hits": placeholder_hits,
        "ok": forbidden_hits == [] and placeholder_hits == [],
    }


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    missing = [name for name in builder.REQUIRED_ARTIFACTS if not (ROUTE_DIR / name).exists()]
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

    decision = parsed.get(f"{builder.PREFIX}_DECISION_LEDGER_{builder.DATE}.json", {})
    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    counts = decision.get("accepted_upstream_counts", {})
    if counts.get("admitted_source_bound_rows") != 2 or counts.get("blocked_rows") != 37 or counts.get("rejected_rows") != 9:
        failures.append({"check": "accepted_counts", "value": counts})
    if counts.get("duplicate_denominators") != builder.EXPECTED_DUPLICATE_DENOMINATORS:
        failures.append({"check": "duplicate_denominators", "value": counts.get("duplicate_denominators")})
    if counts.get("repaired_packet_hash") != builder.EXPECTED_PACKET_SHA:
        failures.append({"check": "repaired_packet_hash", "value": counts.get("repaired_packet_hash")})

    evidence = parsed.get(f"{builder.PREFIX}_EVIDENCE_CHAIN_RECONCILIATION_{builder.DATE}.json", {})
    if evidence.get("packet_hash", {}).get("g12_packet_sha256_recomputed") != builder.EXPECTED_PACKET_SHA:
        failures.append({"check": "evidence_packet_hash", "value": evidence.get("packet_hash")})
    closed_gates = evidence.get("closed_validation_gates", {})
    if closed_gates.get("g12_future_route_validation_execution_remains_closed") is not True:
        failures.append({"check": "validation_gate_closed", "value": closed_gates})
    if closed_gates.get("g12_future_route_scoring_remains_closed") is not True:
        failures.append({"check": "scoring_gate_closed", "value": closed_gates})

    catalog = parsed.get(f"{builder.PREFIX}_CATALOG_REFRESH_LEDGER_{builder.DATE}.json", {})
    if catalog.get("catalog_row_count") != 1200:
        failures.append({"check": "catalog_row_count", "value": catalog.get("catalog_row_count")})
    if catalog.get("hash_manifest_hashed_file_count") != 1076:
        failures.append({"check": "catalog_hash_count", "value": catalog.get("hash_manifest_hashed_file_count")})
    if catalog.get("hash_manifest_large_file_deferral_count") != 124:
        failures.append({"check": "catalog_large_deferrals", "value": catalog.get("hash_manifest_large_file_deferral_count")})

    admitted = parsed.get(f"{builder.PREFIX}_TWO_ADMITTED_ROW_SYNTHESIS_{builder.DATE}.json", {})
    if admitted.get("admitted_row_count") != 2:
        failures.append({"check": "admitted_rows", "value": admitted.get("admitted_row_count")})
    if admitted.get("validation_sufficiency", {}).get("sufficient_for_validation") is not False:
        failures.append({"check": "admitted_validation_sufficiency", "value": admitted.get("validation_sufficiency")})

    blockers = parsed.get(f"{builder.PREFIX}_BLOCKER_ROUTE_LEDGER_{builder.DATE}.json", {})
    blocker_rows = blockers.get("rows", [])
    if blockers.get("blocked_row_count") != 37 or len(blocker_rows) != 37:
        failures.append({"check": "blocker_count", "value": blockers.get("blocked_row_count"), "len": len(blocker_rows)})
    generic_terms = ("missing_data", "not_local", "worktree_absent", "n_too_small")
    for row in blocker_rows:
        if not row.get("terminal_route_class"):
            failures.append({"check": "blocker_terminal_route_class", "candidate_id": row.get("candidate_id")})
        if not row.get("exact_next_action"):
            failures.append({"check": "blocker_exact_next_action", "candidate_id": row.get("candidate_id")})
        evidence_row = row.get("catalog_search_evidence", {})
        if not evidence_row:
            failures.append({"check": "blocker_catalog_evidence", "candidate_id": row.get("candidate_id")})
        if not evidence_row.get("source_state_catalog_reason"):
            failures.append({"check": "blocker_catalog_non_applicable_reason", "candidate_id": row.get("candidate_id")})
        if row.get("can_enter_clean_source_packet_now") is not False:
            failures.append({"check": "blocker_clean_packet_flag", "candidate_id": row.get("candidate_id")})
        joined = json.dumps(row, sort_keys=True).lower()
        for term in generic_terms:
            if term in joined:
                failures.append({"check": "generic_blocker_term", "candidate_id": row.get("candidate_id"), "term": term})

    reject = parsed.get(f"{builder.PREFIX}_REJECT_LEARNING_LEDGER_{builder.DATE}.json", {})
    reject_rows = reject.get("rows", [])
    if reject.get("rejected_row_count") != 9 or len(reject_rows) != 9:
        failures.append({"check": "reject_count", "value": reject.get("rejected_row_count"), "len": len(reject_rows)})
    for row in reject_rows:
        if row.get("terminal_route_class") != "PERMANENT_CLEAN_DENOMINATOR_EXCLUSION_CONTAMINATION_OR_EMBARGO":
            failures.append({"check": "reject_route_class", "candidate_id": row.get("candidate_id")})

    duplicate = parsed.get(f"{builder.PREFIX}_DUPLICATE_DENOMINATOR_CONTAMINATION_REVIEW_{builder.DATE}.json", {})
    if duplicate.get("duplicate_denominators") != builder.EXPECTED_DUPLICATE_DENOMINATORS:
        failures.append({"check": "duplicate_review", "value": duplicate.get("duplicate_denominators")})

    sealed = parsed.get(f"{builder.PREFIX}_SEALED_VALIDATION_READINESS_GAP_LEDGER_{builder.DATE}.json", {})
    if sealed.get("validation_ready") is not False:
        failures.append({"check": "sealed_validation_ready", "value": sealed.get("validation_ready")})

    ranking = parsed.get(f"{builder.PREFIX}_SOURCE_EXPANSION_OPPORTUNITY_RANKING_{builder.DATE}.json", {})
    ranked_routes = ranking.get("ranked_routes", [])
    if not ranked_routes or ranked_routes[0].get("route_id") != "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE":
        failures.append({"check": "next_route_ranking", "value": ranked_routes[:1]})

    parallel = parsed.get(f"{builder.PREFIX}_PARALLELIZATION_DECISION_LEDGER_{builder.DATE}.json", {})
    if parallel.get("decision") != "ONE_BOTTLENECK_ROUTE_FIRST":
        failures.append({"check": "parallelization_decision", "value": parallel.get("decision")})

    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("can_mark_goal_complete") is not True or completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_audit", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})

    prompt_path = ROUTE_DIR / f"{builder.PREFIX}_NEXT_ROUTE_PROMPT_PACK_{builder.DATE}.md"
    prompt_text = prompt_path.read_text(encoding="utf-8", errors="replace") if prompt_path.exists() else ""
    for token in (
        "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "37 blockers",
        "9 rejects",
        "2/2/2",
    ):
        if token not in prompt_text:
            failures.append({"check": "next_prompt_pack", "missing": token})

    syntax_failures = scan_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_syntax", "failures": syntax_failures})

    text_scan = scan_artifact_text()
    if not text_scan["ok"]:
        failures.append({"check": "artifact_text_scan", "value": text_scan})

    scope = diff_scope()
    if not scope["ok"]:
        failures.append({"check": "diff_scope", "value": scope})

    result = {
        "ok": failures == [],
        "failures": failures,
        "warnings": warnings,
        "terminal_decision": decision.get("terminal_decision"),
        "can_mark_goal_complete": failures == [] and completion.get("can_mark_goal_complete") is True,
        "admitted_rows": counts.get("admitted_source_bound_rows"),
        "blockers": blockers.get("blocked_row_count"),
        "rejects": reject.get("rejected_row_count"),
        "duplicate_denominators": counts.get("duplicate_denominators"),
        "packet_hash": counts.get("repaired_packet_hash"),
        "catalog_rows": catalog.get("catalog_row_count"),
        "catalog_hash_count": catalog.get("hash_manifest_hashed_file_count"),
        "catalog_large_deferrals": catalog.get("hash_manifest_large_file_deferral_count"),
        "next_route_id": ranked_routes[0].get("route_id") if ranked_routes else None,
        "diff_scope": scope,
        "text_scan": text_scan,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    (ROUTE_DIR / RESULT_NAME).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    print(json.dumps(verify(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
