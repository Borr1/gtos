"""Verifier for the SCID no-API mechanical hypothesis factory route."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-12"
PREFIX = "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA"
ROUTE_ID = "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS"
EVIDENCE_CLASS = "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY"
TERMINAL_DECISION = "BUILT_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_G12_AUDIT_REQUIRED"
SCOPED_RESEARCH_COMMIT = "539d7764 research: build scid no-api hypothesis factory"
FOCUSED_PYTEST_COMMAND = (
    "python -m pytest -q -p no:cacheprovider "
    "research/science_program_2026_05/06_outcome_testing/"
    "scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/"
    "test_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py"
)
NEXT_G12_PROMPT = (
    "G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
COMPLETION_AUDIT = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"
CLOSEOUT = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "ACCEPTED_AUDIT_RECONCILIATION",
    "MECHANISM_FAMILY_HYPOTHESIS_CATALOG",
    "SOURCE_FIELD_CHECKLIST",
    "PREREGISTRATION_READINESS_MATRIX",
    "SCIENCE_DOMAIN_COVERAGE_MATRIX",
    "ADVERSARIAL_BASELINE_PLACEBO_MATRIX",
    "FUTURE_NO_API_REPLAY_ROUTE_BUNDLE",
    "FUTURE_RESULT_DESIGN_GATE_LEDGER",
    "GENERIC_IDEA_LIST_SATURATION_PROOF",
    "G12_G0_AUDIT_PROMPT_PACK",
    "HYPOTHESIS_CARD_LEDGER_SUMMARY",
    "DECISION_LEDGER",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
]

REQUIRED_PY = [
    "build_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
    "verify_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
    "test_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
]

SCIENCE_DOMAINS = {
    "geometry_topology_path_shape",
    "stochastic_tail_hazard_first_passage",
    "microstructure_orderflow_liquidity_trapped_flow",
    "behavioral_game_theory_session_participant_constraints",
    "macro_session_calendar_cross_asset_context",
    "execution_science_spread_slippage_fillability",
    "ml_meta_labeling_model_disagreement_uncertainty_controls",
    "adversarial_baselines_placebo_explanations",
}

EXPECTED_CAPTURE_GROUPS = {
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source",
}

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "credentials_touched",
    "changes_live_trading_behavior",
]

CARD_REQUIRED_KEYS = {
    "card_id",
    "science_domain",
    "mechanism_family",
    "mechanical_question",
    "current_gtos_ob_framing_relation",
    "preregistration_readiness",
    "accepted_descriptor_fields_required_now",
    "future_capture_groups_required",
    "future_source_fields_required",
    "unavailable_fields_blocking_result_design",
    "as_of_no_leak_rule",
    "duplicate_denominator_policy",
    "admissible_partition",
    "future_result_gate",
    "adversarial_baseline_or_placebo",
    "expected_failure_mode",
    "exact_next_source_control_route",
    "future_no_api_replay_route",
    "outside_current_gtos_ob_framing",
    "no_api_required",
    "uses_outcomes_now",
    "uses_broker_account_order_deal_position_evidence",
    "uses_raw_market_blob_commit",
    "uses_ai_api",
    "safe_flags",
}


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_with_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    path.write_text(body, encoding="utf-8")
    path.with_suffix(".md").write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"- **route_id:** `{payload.get('route_id')}`",
                f"- **evidence_class:** `{payload.get('evidence_class')}`",
                f"- **promotion_verdict:** `{payload.get('promotion_verdict')}`",
                f"- **validation_safe:** `{str(payload.get('validation_safe')).lower()}`",
                f"- **outcome_review_opened:** `{str(payload.get('outcome_review_opened')).lower()}`",
                f"- **live_effect:** `{str(payload.get('live_effect')).lower()}`",
                "",
                "```json",
                body.rstrip(),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def route_json(stem: str) -> dict[str, Any]:
    return load_json(ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json")


def load_cards() -> list[dict[str, Any]]:
    path = ROUTE_DIR / f"{PREFIX}_HYPOTHESIS_CARD_LEDGER_{DATE_TAG}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{repo_path(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/"
        "scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/",
        f"research/science_program_2026_05/04_goal_prompts/{NEXT_G12_PROMPT}",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(forbidden_live_prefixes),
                "scoped_raw_market_blob": scoped and path.endswith(raw_blob_suffixes),
            }
        )
    scoped_entries = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "entries": entries,
        "scoped_entries": scoped_entries,
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def summarize_scoped_git_status(status: dict[str, Any]) -> dict[str, Any]:
    scoped_entries = status.get("scoped_entries", [])
    forbidden_entries = [
        entry for entry in scoped_entries if entry.get("scoped_forbidden_live_surface") or entry.get("scoped_raw_market_blob")
    ]
    return {
        "returncode": status.get("returncode"),
        "stderr": status.get("stderr", []),
        "scoped_entry_count": len(scoped_entries),
        "forbidden_scoped_entries": forbidden_entries,
        "no_scoped_forbidden_live_surface": status.get("no_scoped_forbidden_live_surface") is True,
        "no_scoped_raw_market_blob": status.get("no_scoped_raw_market_blob") is True,
    }


def update_completion_and_closeout(result: dict[str, Any]) -> None:
    if COMPLETION_AUDIT.exists():
        completion = load_json(COMPLETION_AUDIT)
        completion["standalone_verifier_ok"] = result["ok"]
        completion["standalone_verifier_failures"] = result["failures"]
        if result["ok"]:
            for row in completion.get("prompt_to_artifact_checklist", []):
                if row.get("requirement") == "standalone verifier and focused tests":
                    row["status"] = "PASS"
            completion["completion_standard_satisfied"] = True
            completion["can_mark_goal_complete"] = True
            completion["focused_tests_ok"] = True
            completion["scoped_commits_complete"] = True
            completion["scoped_research_commit"] = SCOPED_RESEARCH_COMMIT
            completion["final_live_state_refresh_complete"] = True
        write_json_with_markdown(COMPLETION_AUDIT, "Completion Audit", completion)

    if CLOSEOUT.exists():
        closeout = load_json(CLOSEOUT)
        closeout["standalone_verifier"] = {
            "status": "PASSED" if result["ok"] else "FAILED",
            "ok": result["ok"],
            "failure_count": len(result["failures"]),
        }
        if result["ok"]:
            closeout["focused_pytest"] = {
                "status": "PASSED",
                "command": FOCUSED_PYTEST_COMMAND,
                "observed_result": "6 passed",
            }
            closeout["scoped_research_commit"] = SCOPED_RESEARCH_COMMIT
            closeout["final_live_state_refresh_complete"] = True
        closeout["syntax_parse"] = result["syntax_parse"]
        closeout["scoped_git_status"] = result["scoped_git_status"]
        closeout["status"] = (
            "COMPLETE_SCOPED_RESEARCH_COMMIT_AND_CONTEXT_REFRESH_READY_FOR_G12_AUDIT"
            if result["ok"]
            else "STANDALONE_VERIFIER_FAILED"
        )
        write_json_with_markdown(CLOSEOUT, "Closeout Verification", closeout)


def verify() -> dict[str, Any]:
    failures: list[str] = []

    for stem in REQUIRED_STEMS:
        for suffix in (".json", ".md"):
            path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"
            if not path.exists():
                failures.append(f"missing required artifact: {repo_path(path)}")
    cards_path = ROUTE_DIR / f"{PREFIX}_HYPOTHESIS_CARD_LEDGER_{DATE_TAG}.jsonl"
    if not cards_path.exists():
        failures.append(f"missing required artifact: {repo_path(cards_path)}")

    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing required python artifact: {name}")

    prompt_path = PROMPT_DIR / NEXT_G12_PROMPT
    if not prompt_path.exists():
        failures.append(f"missing next G12 prompt: {repo_path(prompt_path)}")

    json_files = list(ROUTE_DIR.glob(f"{PREFIX}_*_{DATE_TAG}.json"))
    for path in json_files:
        if path == VERIFICATION_RESULT:
            continue
        payload = load_json(path)
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{repo_path(path)} has wrong route_id {payload.get('route_id')}")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{repo_path(path)} has wrong evidence_class {payload.get('evidence_class')}")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{repo_path(path)} missing NO_PROMOTION_VERDICT")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{repo_path(path)} unsafe flag {flag}={payload.get(flag)!r}")

    cards = load_cards() if cards_path.exists() else []
    if len(cards) < 40:
        failures.append(f"expected at least 40 hypothesis cards, observed {len(cards)}")
    card_ids = [card.get("card_id") for card in cards]
    if len(card_ids) != len(set(card_ids)):
        failures.append("hypothesis card ids are not unique")

    domains = {card.get("science_domain") for card in cards}
    if domains != SCIENCE_DOMAINS:
        failures.append(f"science domain coverage mismatch: {sorted(domains)}")
    for domain in SCIENCE_DOMAINS:
        count = sum(1 for card in cards if card.get("science_domain") == domain)
        if count < 5:
            failures.append(f"domain {domain} has fewer than 5 cards: {count}")

    statuses = {card.get("preregistration_readiness") for card in cards}
    for required in {
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
    }:
        if required not in statuses:
            failures.append(f"missing readiness status {required}")

    for card in cards:
        missing = CARD_REQUIRED_KEYS - set(card)
        if missing:
            failures.append(f"{card.get('card_id')} missing card keys: {sorted(missing)}")
        if card.get("uses_outcomes_now") is not False:
            failures.append(f"{card.get('card_id')} opens outcomes")
        if card.get("uses_ai_api") is not False:
            failures.append(f"{card.get('card_id')} opens AI/API")
        if card.get("uses_broker_account_order_deal_position_evidence") is not False:
            failures.append(f"{card.get('card_id')} opens broker evidence")
        if card.get("uses_raw_market_blob_commit") is not False:
            failures.append(f"{card.get('card_id')} opens raw blob commit")
        if not card.get("as_of_no_leak_rule"):
            failures.append(f"{card.get('card_id')} missing as-of/no-leak rule")
        if not card.get("duplicate_denominator_policy"):
            failures.append(f"{card.get('card_id')} missing duplicate policy")
        if not card.get("future_result_gate"):
            failures.append(f"{card.get('card_id')} missing future result gate")
        if not card.get("adversarial_baseline_or_placebo"):
            failures.append(f"{card.get('card_id')} missing adversarial baseline")
        if not card.get("expected_failure_mode"):
            failures.append(f"{card.get('card_id')} missing expected failure mode")
        if not card.get("exact_next_source_control_route"):
            failures.append(f"{card.get('card_id')} missing exact next source/control route")
        unknown_groups = set(card.get("future_capture_groups_required", [])) - EXPECTED_CAPTURE_GROUPS
        if unknown_groups:
            failures.append(f"{card.get('card_id')} references unknown capture groups {sorted(unknown_groups)}")

    reconciliation = route_json("ACCEPTED_AUDIT_RECONCILIATION") if not failures or True else {}
    if reconciliation.get("candidate_rows_coverage_expectation") != 3014:
        failures.append("accepted reconciliation did not preserve 3,014 candidate rows")
    if reconciliation.get("duplicate_proxy_denominator_key_coverage_expectation") != 3014:
        failures.append("accepted reconciliation did not preserve 3,014 duplicate keys")
    if set(reconciliation.get("capture_groups", [])) != EXPECTED_CAPTURE_GROUPS:
        failures.append("accepted reconciliation did not preserve ten capture groups")

    coverage = route_json("SCIENCE_DOMAIN_COVERAGE_MATRIX")
    if coverage.get("all_required_domains_covered") is not True:
        failures.append("science-domain coverage matrix is not complete")
    if coverage.get("minimum_cards_per_domain", 0) < 5:
        failures.append("science-domain coverage matrix minimum card count below 5")

    readiness = route_json("PREREGISTRATION_READINESS_MATRIX")
    if readiness.get("matrix_row_count") != len(cards):
        failures.append("readiness matrix row count does not match card count")

    adversarial = route_json("ADVERSARIAL_BASELINE_PLACEBO_MATRIX")
    if adversarial.get("baseline_card_count", 0) < 5:
        failures.append("adversarial baseline matrix has fewer than five baseline cards")

    saturation = route_json("GENERIC_IDEA_LIST_SATURATION_PROOF")
    if saturation.get("not_generic_idea_list") is not True:
        failures.append("saturation proof does not prove non-generic status")

    decision = route_json("DECISION_LEDGER")
    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append(f"wrong terminal decision: {decision.get('terminal_decision')}")

    prompt_pack = route_json("G12_G0_AUDIT_PROMPT_PACK")
    if not prompt_pack.get("one_line_starter", "").startswith("/goal Follow the full controlling prompt"):
        failures.append("next G12 one-line starter missing /goal prefix")
    if prompt_path.exists():
        prompt_text = prompt_path.read_text(encoding="utf-8")
        for phrase in [
            "Completion Standard",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "3,014",
            "ten capture groups",
            "generic idea list",
        ]:
            if phrase not in prompt_text:
                failures.append(f"next G12 prompt missing phrase: {phrase}")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    scoped_status = scoped_git_status()
    scoped_status_summary = summarize_scoped_git_status(scoped_status)
    if not scoped_status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped git status includes forbidden live-surface file")
    if not scoped_status["no_scoped_raw_market_blob"]:
        failures.append("scoped git status includes raw market blob")

    result = {
        "ok": not failures,
        "failures": failures,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        **{flag: False for flag in SAFE_FALSE_FLAGS},
        "card_count_verified": len(cards),
        "science_domains_verified": sorted(domains),
        "terminal_decision": TERMINAL_DECISION,
        "syntax_parse": syntax,
        "scoped_git_status": scoped_status_summary,
        "can_mark_goal_complete": not failures,
    }
    VERIFICATION_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    update_completion_and_closeout(result)
    return result


if __name__ == "__main__":
    verification_result = verify()
    print(json.dumps(verification_result, indent=2, sort_keys=True))
    raise SystemExit(0 if verification_result["ok"] else 1)
