"""Verifier for blocked-17 orderflow/proxy contract packet."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import build_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13 as builder


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


def scan_forbidden_true_tokens() -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    paths = list(ROUTE_DIR.glob("*.json")) + list(ROUTE_DIR.glob("*.md")) + list(ROUTE_DIR.glob("*.txt"))
    prompt_path = builder.PROMPT_ROOT / builder.NEXT_G12_PROMPT_NAME
    if prompt_path.exists():
        paths.append(prompt_path)
    for path in paths:
        if path.name in {RESULT_JSON, RESULT_MD}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for token in builder.FORBIDDEN_TRUE_TOKENS:
            if token.lower() in text:
                hits.append({"path": builder.rel(path), "token": token})
    return {"ok": hits == [], "hits": hits}


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required = (
        list(builder.JSON_ARTIFACTS)
        + list(builder.MD_ARTIFACTS)
        + [
            "build_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py",
            "verify_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py",
            "test_scid_orderflow_proxy_validity_contract_and_context_packet_route_2026_05_13.py",
            builder.NEXT_G12_STARTER_NAME,
        ]
    )
    missing = [name for name in required if not (ROUTE_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_artifacts_exist", "missing": missing})

    next_prompt = builder.PROMPT_ROOT / builder.NEXT_G12_PROMPT_NAME
    if not next_prompt.exists():
        failures.append({"check": "next_g12_prompt_exists", "missing": builder.rel(next_prompt)})
    starter = ROUTE_DIR / builder.NEXT_G12_STARTER_NAME
    if starter.exists():
        starter_text = starter.read_text(encoding="utf-8")
        if "\n\n" in starter_text:
            failures.append({"check": "starter_one_physical_line", "path": builder.rel(starter)})
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in starter_text:
                failures.append({"check": "starter_safe_token", "missing": token})

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
                failures.append({"check": "md_safe_tokens", "file": md_path.name, "missing": token})

    dependency = parsed.get(f"{builder.PREFIX}_SOURCE_DEPENDENCY_LEDGER_{builder.DATE}.json", {})
    if dependency.get("proxy_card_count") != 8:
        failures.append({"check": "proxy_card_count", "value": dependency.get("proxy_card_count")})
    if dependency.get("proxy_field_requirement_count") != 64:
        failures.append({"check": "proxy_field_requirement_count", "value": dependency.get("proxy_field_requirement_count")})
    if dependency.get("proxy_requirement_surface_count") != 72:
        failures.append({"check": "proxy_requirement_surface_count", "value": dependency.get("proxy_requirement_surface_count")})
    if len({row.get("card_id") for row in dependency.get("proxy_cards", [])}) != 8:
        failures.append({"check": "unique_proxy_cards", "value": dependency.get("proxy_cards", [])})
    for row in dependency.get("proxy_dependency_rows", []):
        if row.get("may_score_results_now") is not False:
            failures.append({"check": "dependency_no_score", "row": row})
        if row.get("broker_native_cfd_truth_claim_allowed") is not False:
            failures.append({"check": "dependency_broker_truth", "row": row})
        if not row.get("attached_contract_ids"):
            failures.append({"check": "dependency_contracts_attached", "row": row})
        if not row.get("exact_next_requirement"):
            failures.append({"check": "dependency_exact_requirement", "row": row})

    source_contract = parsed.get(f"{builder.PREFIX}_SOURCE_FAMILY_CONTRACT_{builder.DATE}.json", {})
    contracts = source_contract.get("contracts", [])
    if source_contract.get("contract_count") != 4 or len(contracts) != 4:
        failures.append({"check": "contract_count", "value": source_contract.get("contract_count")})
    for contract in contracts:
        for key in (
            "parser_acceptance_criteria",
            "roll_session_asof_rule",
            "staleness_policy",
            "exact_access_requirement_if_unresolved",
            "invalid_contexts",
        ):
            if not contract.get(key):
                failures.append({"check": "contract_required_field", "contract": contract.get("contract_id"), "missing": key})
        if contract.get("broker_native_cfd_truth_claim_allowed") is not False:
            failures.append({"check": "contract_broker_truth", "contract": contract.get("contract_id")})

    context_schema = parsed.get(f"{builder.PREFIX}_CONTEXT_PACKET_SCHEMA_{builder.DATE}.json", {})
    if len(context_schema.get("required_fields", [])) < 20:
        failures.append({"check": "context_schema_required_fields", "value": context_schema.get("required_fields")})
    for field in ("source_family", "proxy_mapping_version", "contract_month", "source_hash_or_deferral_id", "non_equivalence_label"):
        if field not in context_schema.get("fail_closed_if_missing", []):
            failures.append({"check": "context_schema_fail_closed_field", "missing": field})

    equivalence = parsed.get(f"{builder.PREFIX}_EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX_{builder.DATE}.json", {})
    rows = equivalence.get("equivalence_rows", [])
    if equivalence.get("equivalence_row_count") != 7 or len(rows) != 7:
        failures.append({"check": "equivalence_row_count", "value": equivalence.get("equivalence_row_count")})
    if equivalence.get("broker_native_cfd_truth_claims") != 0:
        failures.append({"check": "equivalence_broker_truth_claims", "value": equivalence.get("broker_native_cfd_truth_claims")})
    for row in rows:
        if row.get("broker_cfd_truth_allowed") is not False:
            failures.append({"check": "equivalence_broker_cfd_truth_allowed", "row": row})
        if row.get("equivalence_status") != "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY":
            failures.append({"check": "equivalence_status", "row": row})
        if not row.get("invalid_context_rules"):
            failures.append({"check": "equivalence_invalid_context_rules", "row": row.get("candidate_symbol")})
    usd = [row for row in rows if row.get("candidate_symbol") == "USDJPY_6J"]
    if not usd or "Inverse FX futures" not in usd[0].get("special_mapping_requirement", ""):
        failures.append({"check": "usdjpy_inverse_policy", "value": usd})

    blocker = parsed.get(f"{builder.PREFIX}_PAID_ACCESS_FREE_BLOCKER_LEDGER_{builder.DATE}.json", {})
    if blocker.get("all_remainders_exact") is not True:
        failures.append({"check": "blocker_remainders_exact", "value": blocker.get("all_remainders_exact")})
    for row in blocker.get("rows", []):
        if row.get("paid_access_required_now") is not False:
            failures.append({"check": "blocker_paid_now", "row": row})
        if not row.get("exact_requirement"):
            failures.append({"check": "blocker_exact_requirement", "row": row})

    decision = parsed.get(f"{builder.PREFIX}_ROUTE_DECISION_LEDGER_{builder.DATE}.json", {})
    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    if decision.get("proxy_requirement_surface_count") != 72:
        failures.append({"check": "decision_surface_count", "value": decision.get("proxy_requirement_surface_count")})
    if decision.get("broker_native_cfd_truth_claims") != 0:
        failures.append({"check": "decision_broker_truth", "value": decision.get("broker_native_cfd_truth_claims")})

    noleak = parsed.get(f"{builder.PREFIX}_NOLEAK_SAFE_FLAG_AUDIT_{builder.DATE}.json", {})
    if noleak.get("included_card_count") != 17:
        failures.append({"check": "noleak_included_card_count", "value": noleak.get("included_card_count")})
    if noleak.get("excluded_blocked15_card_count") != 15:
        failures.append({"check": "noleak_excluded_blocked15", "value": noleak.get("excluded_blocked15_card_count")})
    if noleak.get("raw_market_blob_commits_added") != 0:
        failures.append({"check": "noleak_raw_blob", "value": noleak.get("raw_market_blob_commits_added")})
    if noleak.get("broker_account_order_history_deal_position_sources_consumed") != 0:
        failures.append({"check": "noleak_broker_sources", "value": noleak.get("broker_account_order_history_deal_position_sources_consumed")})

    saturation = parsed.get(f"{builder.PREFIX}_SATURATION_SELF_REDTEAM_{builder.DATE}.json", {})
    if saturation.get("saturation_question_count", 0) < 8:
        failures.append({"check": "saturation_question_count", "value": saturation.get("saturation_question_count")})
    if saturation.get("same_evidence_class_gap_remaining") is not False:
        failures.append({"check": "saturation_gap_remaining", "value": saturation.get("same_evidence_class_gap_remaining")})

    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_standard_satisfied", "value": completion.get("completion_standard_satisfied")})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})

    syntax_failures = scan_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_syntax", "failures": syntax_failures})

    text_scan = scan_forbidden_true_tokens()
    if not text_scan["ok"]:
        failures.append({"check": "forbidden_true_tokens", "hits": text_scan["hits"]})

    scope = diff_scope()
    if not scope["ok"]:
        failures.append({"check": "diff_scope", "scope": scope})

    ok = failures == []
    return {
        "schema_version": builder.SCHEMA_VERSION,
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "artifact_family": "VERIFICATION_RESULT",
        "generated_at_utc": builder.now_utc(),
        "ok": ok,
        "can_mark_goal_complete": ok,
        "failure_count": len(failures),
        "failures": failures,
        "warnings": warnings,
        "terminal_decision": builder.TERMINAL_DECISION if ok else "VERIFY_FAILED",
        "proxy_card_count": dependency.get("proxy_card_count"),
        "proxy_field_requirement_count": dependency.get("proxy_field_requirement_count"),
        "proxy_requirement_surface_count": dependency.get("proxy_requirement_surface_count"),
        "source_family_contract_count": source_contract.get("contract_count"),
        "equivalence_row_count": equivalence.get("equivalence_row_count"),
        "broker_native_cfd_truth_claims": decision.get("broker_native_cfd_truth_claims"),
        "diff_scope": scope,
        "text_scan": text_scan,
        "promotion_verdict": builder.PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def write_result(result: dict[str, Any]) -> None:
    (ROUTE_DIR / RESULT_JSON).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (
        "# SCID Blocked17 Orderflow Proxy Contract Verification Result\n\n"
        "- `NO_PROMOTION_VERDICT`\n"
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
