from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage06_ltf_entry_nofill_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage06", MODULE_PATH)
stage06 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage06)

stage05 = stage06.stage05
stage02 = stage06.stage02
REPO_ROOT = stage06.REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import (  # noqa: E402
    GTOSVNextPreAIRoutingDecision,
    evaluate_vnext_ai_policy,
    format_vnext_ai_policy_context_for_prompt,
)
from src.components.primary_analyzer import PrimaryAnalyzer  # noqa: E402


ROUTE_ID = stage06.ROUTE_ID
ROUTE_DIR = stage06.ROUTE_DIR
STATE_PATH = stage06.STATE_PATH
DECISION_SURFACE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_DECISION_SURFACE_LEDGER_2026-05-25.jsonl"
AI_NARROWING_SHADOW_PATH = Path("shadow_logs/ai_narrowing_policy_shadow_evaluations.jsonl")
MALFORMED_LOG_PATH = Path("shadow_logs/malformed_responses.jsonl")
STAGE07_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_AI_POLICY_PROMPT_PACKET_LEDGER_2026-05-25.jsonl"
)
STAGE07_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE07_AI_POLICY_SUMMARY_2026-05-25.json"
)
STAGE07_DOSSIER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_AI_POLICY_AND_SUPERVISOR_DOSSIER_2026-05-25.md"
)
STAGE07_VERIFICATION_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE07_VERIFICATION_RESULT_2026-05-25.json"
)

REQUIRED_SCENARIOS = {
    "shadow_avoid_records_would_skip",
    "active_avoid_skips_ai",
    "narrowed_route_calls_constrained_ai",
    "mixed_source_bound_calls_ai_resolution",
    "active_legacy_blocks_unreplayed_fallback",
    "replayed_legacy_explicitly_allowed",
    "follow_standard_risk_uses_validator",
    "follow_low_risk_shadow_mechanical_no_ai",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return stage02.rel(path)


def atomic_json_write(path: Path, payload: Any) -> None:
    stage02.atomic_json_write(path, payload)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    stage02.write_jsonl(path, rows)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    target = REPO_ROOT / path
    if not target.exists():
        return []
    return [
        json.loads(line)
        for line in target.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _counter_to_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted((str(key), int(value)) for key, value in counter.items()))


def stage07_surface_summary() -> dict[str, Any]:
    rows = [
        row
        for row in read_jsonl(DECISION_SURFACE_PATH)
        if "STAGE_07_AI_POLICY" in (row.get("required_stages") or [])
    ]
    surfaces: Counter[str] = Counter()
    source_components: Counter[str] = Counter()
    implementation_decisions: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    for row in rows:
        key = row.get("group_key") or {}
        surfaces[str(key.get("runtime_surface"))] += 1
        source_components[str(key.get("source_component"))] += 1
        implementation_decisions[str(key.get("implementation_decision"))] += 1
        actions[str(row.get("implementation_action"))] += 1
    return {
        "source_path": rel(DECISION_SURFACE_PATH),
        "group_count": len(rows),
        "row_count": sum(int((row.get("counts") or {}).get("rows") or 0) for row in rows),
        "runtime_surfaces": _counter_to_dict(surfaces),
        "source_components": _counter_to_dict(source_components),
        "implementation_decisions": _counter_to_dict(implementation_decisions),
        "implementation_actions": _counter_to_dict(actions),
    }


def _pre_ai(
    *,
    action: str,
    decision: str,
    would_action: str,
    ai_role: str,
    recommended_side: str | None = None,
    recommended_frameworks: tuple[str, ...] = (),
    recommended_route_families: tuple[str, ...] = (),
    blocked_sides: tuple[str, ...] = (),
    blocked_frameworks: tuple[str, ...] = (),
    matched_rows: int = 0,
) -> GTOSVNextPreAIRoutingDecision:
    return GTOSVNextPreAIRoutingDecision(
        action=action,
        decision=decision,
        enabled=True,
        apply_to_ai_call=action != "ALLOW_AI",
        reason="stage07_scenario",
        event={"symbol": "XAUUSD", "route_session": "london", "side": recommended_side},
        recommended_side=recommended_side,
        recommended_frameworks=recommended_frameworks,
        recommended_route_families=recommended_route_families,
        blocked_sides=blocked_sides,
        blocked_frameworks=blocked_frameworks,
        would_action=would_action,
        ai_role_context={
            "enabled": True,
            "ai_role": ai_role,
            "matched_rows": matched_rows,
            "source_component_counts": {"stage07_source_bound_component": matched_rows}
            if matched_rows
            else {},
            "decision_counts": {decision: matched_rows} if matched_rows else {},
            "source_artifact_path": rel(DECISION_SURFACE_PATH),
        },
    )


def runtime_scenarios() -> list[dict[str, Any]]:
    definitions = [
        (
            "shadow_avoid_records_would_skip",
            _pre_ai(
                action="ALLOW_AI",
                decision="AVOID",
                would_action="SKIP_AI_AVOID_ONLY",
                ai_role="vnext_avoid_blocker_classifier",
                blocked_sides=("LONG",),
                matched_rows=8,
            ),
            {"ai_policy_enabled": True, "ai_policy_apply_to_ai_call": False},
            {},
        ),
        (
            "active_avoid_skips_ai",
            _pre_ai(
                action="SKIP_AI_AVOID_ONLY",
                decision="AVOID",
                would_action="SKIP_AI_AVOID_ONLY",
                ai_role="vnext_avoid_blocker_classifier",
                blocked_sides=("LONG",),
                matched_rows=8,
            ),
            {"ai_policy_enabled": True, "ai_policy_apply_to_ai_call": True},
            {},
        ),
        (
            "narrowed_route_calls_constrained_ai",
            _pre_ai(
                action="NARROW_AI_TO_ROUTE",
                decision="FOLLOW",
                would_action="NARROW_AI_TO_ROUTE",
                ai_role="vnext_route_validator",
                recommended_side="LONG",
                recommended_frameworks=("ob_retest",),
                recommended_route_families=("ob_retest",),
                blocked_frameworks=("fvg_fill",),
                matched_rows=11,
            ),
            {"ai_policy_enabled": True},
            {"risk_tier": "funded_prop", "candidate_id": "stage07-narrowed"},
        ),
        (
            "mixed_source_bound_calls_ai_resolution",
            _pre_ai(
                action="ALLOW_AI",
                decision="MIXED",
                would_action="ALLOW_AI",
                ai_role="vnext_evidence_triage",
                recommended_side="SHORT",
                matched_rows=6,
            ),
            {
                "ai_policy_enabled": True,
                "ai_policy_allow_mixed_ai_resolution": True,
                "ai_policy_mixed_resolution_requires_source_bound_fields": True,
            },
            {"source_packet_id": "stage07-mixed"},
        ),
        (
            "active_legacy_blocks_unreplayed_fallback",
            _pre_ai(
                action="ALLOW_AI",
                decision="LEGACY",
                would_action="ALLOW_AI",
                ai_role="general_trade_decision",
            ),
            {
                "ai_policy_enabled": True,
                "ai_policy_apply_to_ai_call": True,
                "ai_policy_allow_legacy_broad_fallback": False,
            },
            {},
        ),
        (
            "replayed_legacy_explicitly_allowed",
            _pre_ai(
                action="ALLOW_AI",
                decision="LEGACY",
                would_action="ALLOW_AI",
                ai_role="general_trade_decision",
            ),
            {
                "ai_policy_enabled": True,
                "ai_policy_allow_legacy_broad_fallback": True,
                "ai_policy_legacy_requires_replayed_scope": True,
            },
            {"legacy_replayed_scope": True, "replay_scope_id": "stage07-legacy"},
        ),
        (
            "follow_standard_risk_uses_validator",
            _pre_ai(
                action="ALLOW_AI",
                decision="FOLLOW",
                would_action="ALLOW_AI",
                ai_role="vnext_evidence_triage",
                recommended_side="LONG",
                matched_rows=5,
            ),
            {"ai_policy_enabled": True},
            {"risk_tier": "standard"},
        ),
        (
            "follow_low_risk_shadow_mechanical_no_ai",
            _pre_ai(
                action="ALLOW_AI",
                decision="FOLLOW",
                would_action="ALLOW_AI",
                ai_role="vnext_evidence_triage",
                recommended_side="LONG",
                matched_rows=5,
            ),
            {
                "ai_policy_enabled": True,
                "ai_policy_follow_no_ai_enabled": True,
                "ai_policy_follow_validator_risk_tiers": ["high", "funded_prop"],
            },
            {"risk_tier": "low"},
        ),
    ]
    rows: list[dict[str, Any]] = []
    for scenario_id, pre_ai, runtime_cfg, raw_data in definitions:
        decision = evaluate_vnext_ai_policy(
            pre_ai_decision=pre_ai,
            config={"gtos_vnext_runtime": runtime_cfg},
            raw_data=raw_data,
        )
        prompt_text = format_vnext_ai_policy_context_for_prompt(decision)
        packet = {
            "scenario_id": scenario_id,
            "role_context": pre_ai.ai_role_context,
            "ai_policy": decision.to_record(),
            "prompt_text": prompt_text,
            "raw_data_context": raw_data,
        }
        rows.append(
            {
                "schema_version": "vnext_production_change_stage07_ai_policy_packet_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_07_AI_POLICY",
                "row_type": "runtime_prompt_packet_scenario",
                "scenario_id": scenario_id,
                "action": decision.action,
                "would_action": decision.would_action,
                "allowed": decision.allowed,
                "would_allow_ai_call": decision.would_allow_ai_call,
                "ai_role": decision.ai_role,
                "reason": decision.reason,
                "prompt_packet_sha256": sha256_text(json.dumps(packet, sort_keys=True)),
                "prompt_text_sha256": sha256_text(prompt_text),
                "decision_record": decision.to_record(),
            }
        )
    return rows


def _valid_payload(decision: str = "NO_TRADE") -> dict[str, Any]:
    payload = {
        "timestamp_utc": "2026-05-25T00:00:00Z",
        "model_used": "placeholder",
        "decision": decision,
        "confidence_score": 70,
        "framework": "none" if decision != "CANDIDATE" else "ob_retest",
        "kill_zone": "london",
        "reasoning": {
            "daily_bias": {"direction": "bullish", "confidence": "medium"},
            "h4_alignment": {"aligned": True, "h4_pois_identified": []},
            "h1_setup": {"poi_identified": False, "poi_type": "none"},
            "liquidity_sweep": {"detected": False, "pool_type": "none"},
            "m15_confirmation": {"choch_detected": False},
            "setup_grade": "C",
            "overall_reasoning": "offline schema fixture",
        },
        "no_trade_reason": "offline_schema_fixture" if decision == "NO_TRADE" else None,
    }
    if decision == "CANDIDATE":
        payload["trade_parameters"] = {
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 102.0,
            "risk_reward_ratio": 2.0,
        }
    return {key: value for key, value in payload.items() if value is not None}


def parser_fixture_rows() -> list[dict[str, Any]]:
    analyzer = PrimaryAnalyzer.__new__(PrimaryAnalyzer)
    analyzer.model = "claude-sonnet-4-6"
    fixtures = {
        "valid_no_trade_json": json.dumps(_valid_payload("NO_TRADE"), sort_keys=True),
        "valid_candidate_fenced_json": "```json\n"
        + json.dumps(_valid_payload("CANDIDATE"), sort_keys=True)
        + "\n```",
        "malformed_missing_reasoning": json.dumps(
            {
                "timestamp_utc": "2026-05-25T00:00:00Z",
                "model_used": "placeholder",
                "decision": "NO_TRADE",
            },
            sort_keys=True,
        ),
        "malformed_not_json": "CANDIDATE long XAUUSD without JSON",
    }
    rows: list[dict[str, Any]] = []
    for fixture_id, raw in fixtures.items():
        parsed = False
        parsed_decision = None
        error = None
        try:
            result = analyzer._parse_and_validate(raw)
            parsed = True
            parsed_decision = result.decision
        except Exception as exc:  # noqa: BLE001 - expected for malformed fixtures.
            error = type(exc).__name__
        rows.append(
            {
                "schema_version": "vnext_production_change_stage07_ai_policy_packet_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_07_AI_POLICY",
                "row_type": "schema_parser_fixture",
                "fixture_id": fixture_id,
                "raw_response_sha256": sha256_text(raw),
                "parsed": parsed,
                "parsed_decision": parsed_decision,
                "error_type": error,
            }
        )
    return rows


def shadow_log_summary() -> dict[str, Any]:
    ai_rows = read_jsonl(AI_NARROWING_SHADOW_PATH)
    malformed_rows = read_jsonl(MALFORMED_LOG_PATH)
    return {
        "ai_narrowing_shadow": {
            "source_path": rel(AI_NARROWING_SHADOW_PATH),
            "row_count": len(ai_rows),
            "policy_action_counts": _counter_to_dict(
                Counter(str(row.get("policy_action")) for row in ai_rows)
            ),
        },
        "malformed_responses": {
            "source_path": rel(MALFORMED_LOG_PATH),
            "row_count": len(malformed_rows),
            "attempt_counts": _counter_to_dict(Counter(str(row.get("attempt")) for row in malformed_rows)),
        },
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scenario_rows = [row for row in rows if row.get("row_type") == "runtime_prompt_packet_scenario"]
    parser_rows = [row for row in rows if row.get("row_type") == "schema_parser_fixture"]
    parsed_counts = Counter(str(row.get("parsed")) for row in parser_rows)
    return {
        "schema_version": "vnext_production_change_stage07_ai_policy_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "stage07_surface": stage07_surface_summary(),
        "scenario_row_count": len(scenario_rows),
        "runtime_scenario_action_counts": _counter_to_dict(
            Counter(str(row.get("action")) for row in scenario_rows)
        ),
        "runtime_scenario_would_action_counts": _counter_to_dict(
            Counter(str(row.get("would_action")) for row in scenario_rows)
        ),
        "runtime_scenario_allowed_counts": _counter_to_dict(
            Counter(str(row.get("allowed")) for row in scenario_rows)
        ),
        "prompt_packet_count": len(scenario_rows),
        "prompt_packet_hash_count": len(
            {row.get("prompt_packet_sha256") for row in scenario_rows}
        ),
        "parser_fixture_count": len(parser_rows),
        "parser_fixture_parsed_counts": _counter_to_dict(parsed_counts),
        "shadow_logs": shadow_log_summary(),
    }


def write_dossier(summary: dict[str, Any]) -> None:
    surface = summary["stage07_surface"]
    lines = [
        "# vNext Production Change Stage07 AI Policy And Supervisor Dossier",
        "",
        f"Created: {summary['created_at_utc']}",
        "",
        "## Stage07 Runtime Change",
        "",
        "- Added a mechanical-first vNext AI policy decision surface.",
        "- Mechanical AVOID produces `SKIP_AI_MECHANICAL_AVOID`; current config keeps it shadowed by `ai_policy_apply_to_ai_call=false`.",
        "- FOLLOW routes use a constrained validator by default; optional no-AI follow remains gated by config and risk tier.",
        "- NARROW routes call AI only inside the selected side/framework/route-family scope.",
        "- MIXED routes call AI only when source-bound prompt fields are present.",
        "- LEGACY broad fallback is blocked when active unless an explicit replayed scope is present.",
        "- Prompt packets carry deterministic SHA-256 hashes and a schema/cache contract; no paid API call is made by this harness.",
        "",
        "## Evidence Consumed",
        "",
        f"- Stage07 decision-surface groups: {surface['group_count']}.",
        f"- Stage07 decision-map rows: {surface['row_count']}.",
        f"- Runtime surfaces: {json.dumps(surface['runtime_surfaces'], sort_keys=True)}.",
        f"- Source components: {json.dumps(surface['source_components'], sort_keys=True)}.",
        f"- Implementation decisions: {json.dumps(surface['implementation_decisions'], sort_keys=True)}.",
        "",
        "## No-Paid-Call Harness",
        "",
        f"- Runtime scenario rows: {summary['scenario_row_count']}.",
        f"- Action counts: {json.dumps(summary['runtime_scenario_action_counts'], sort_keys=True)}.",
        f"- Would-action counts: {json.dumps(summary['runtime_scenario_would_action_counts'], sort_keys=True)}.",
        f"- Prompt packet hashes: {summary['prompt_packet_hash_count']} unique for {summary['prompt_packet_count']} packets.",
        f"- Schema/parser fixtures: {summary['parser_fixture_count']} with parsed counts {json.dumps(summary['parser_fixture_parsed_counts'], sort_keys=True)}.",
        "",
        "## Supervisor Boundary",
        "",
        "- Stage08 still owns the always-on AI supervisor implementation.",
        "- Stage07 only creates the explicit policy contract, prompt-packet/hash harness, and parser fixtures consumed by that supervisor.",
        "- No live trading, broker mutation, paid API/vendor call, source deletion, remote push, or activation flip is performed.",
        "",
    ]
    STAGE07_DOSSIER_PATH.write_text("\n".join(lines), encoding="utf-8")


def verify_summary(summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    scenario_rows = [row for row in rows if row.get("row_type") == "runtime_prompt_packet_scenario"]
    scenario_ids = {str(row["scenario_id"]) for row in scenario_rows}
    if scenario_ids != REQUIRED_SCENARIOS:
        failures.append(f"scenario coverage mismatch: {sorted(REQUIRED_SCENARIOS - scenario_ids)}")
    required_would = {
        "SKIP_AI_MECHANICAL_AVOID",
        "CALL_AI_NARROWED_ROUTE",
        "CALL_AI_MIXED_RESOLUTION",
        "BLOCK_LEGACY_BROAD_FALLBACK",
        "CALL_AI_LEGACY_REPLAYED",
        "CALL_AI_CONSTRAINED_VALIDATOR",
        "MECHANICAL_FOLLOW_NO_AI",
    }
    would_actions = {str(row.get("would_action")) for row in scenario_rows}
    missing_would = sorted(required_would - would_actions)
    if missing_would:
        failures.append(f"missing Stage07 would actions: {missing_would}")
    if summary["stage07_surface"]["group_count"] != 127:
        failures.append("Stage07 decision-surface group count mismatch")
    if summary["stage07_surface"]["row_count"] != 627:
        failures.append("Stage07 decision-surface row count mismatch")
    if summary["prompt_packet_hash_count"] != summary["prompt_packet_count"]:
        failures.append("prompt packet hashes are not unique")
    parser_counts = summary["parser_fixture_parsed_counts"]
    if parser_counts.get("True", 0) < 2 or parser_counts.get("False", 0) < 2:
        failures.append("schema/parser harness did not include valid and malformed fixtures")
    return failures


def update_state(summary: dict[str, Any], *, complete: bool) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = stage02.git_head()
    state["dirty_tracked_paths"] = stage02.git_status_short()
    state["current_stage"] = "STAGE_08_AI_SUPERVISOR" if complete else "STAGE_07_AI_POLICY"
    state["stage_status_table"]["STAGE_07_AI_POLICY"] = "complete" if complete else "in_progress"
    if complete:
        state["stage_status_table"]["STAGE_08_AI_SUPERVISOR"] = "in_progress"
        state["active_invariant"] = "implement_bounded_ai_supervisor"
        state["first_incomplete_invariant"] = "STAGE_08_AI_SUPERVISOR"
        state["exact_next_action"] = (
            "Implement the Stage08 bounded AI supervisor and malformed-response controls "
            "without restarting Stage00-07."
        )
    else:
        state["active_invariant"] = "define_and_implement_ai_role"
        state["first_incomplete_invariant"] = "STAGE_07_AI_POLICY"
        state["exact_next_action"] = (
            "Run Stage07 verifier and focused no-paid-call AI policy/schema tests, "
            "then mark Stage07 complete."
        )
    outputs = state.setdefault("output_artifact_paths", {})
    outputs["ai_policy_prompt_packet_ledger"] = rel(STAGE07_LEDGER_PATH)
    outputs["stage07_ai_policy_summary"] = rel(STAGE07_SUMMARY_PATH)
    outputs["ai_policy_and_supervisor_dossier"] = rel(STAGE07_DOSSIER_PATH)
    outputs["stage07_verification_result"] = rel(STAGE07_VERIFICATION_RESULT_PATH)
    state.setdefault("rows_groups_processed", {})[
        "stage07_ai_policy_runtime_scenarios"
    ] = summary["scenario_row_count"]
    state["rows_groups_processed"]["stage07_decision_surface_rows"] = summary[
        "stage07_surface"
    ]["row_count"]
    state["row_count_hash_coverage"]["stage07_ai_policy_summary"] = {
        "stage07_surface_groups": summary["stage07_surface"]["group_count"],
        "stage07_surface_rows": summary["stage07_surface"]["row_count"],
        "scenario_row_count": summary["scenario_row_count"],
        "prompt_packet_count": summary["prompt_packet_count"],
        "prompt_packet_hash_count": summary["prompt_packet_hash_count"],
        "parser_fixture_count": summary["parser_fixture_count"],
        "runtime_scenario_action_counts": summary["runtime_scenario_action_counts"],
        "runtime_scenario_would_action_counts": summary[
            "runtime_scenario_would_action_counts"
        ],
    }
    state["verification_status"]["stage07_ai_policy_built"] = True
    state["verification_status"]["stage07_ai_policy_runtime_scenarios"] = summary[
        "scenario_row_count"
    ]
    state["verification_status"]["stage07_verifier_ok"] = complete
    implemented = state.setdefault("implemented_surfaces", [])
    surface_entry = {
        "stage": "STAGE_07_AI_POLICY",
        "surface": "mechanical_first_ai_policy_and_no_paid_call_prompt_schema_harness",
        "runtime_row_count": summary["stage07_surface"]["row_count"],
        "activation_gate": "gtos_vnext_runtime.ai_policy_apply_to_ai_call",
        "artifact": rel(STAGE07_LEDGER_PATH),
    }
    if surface_entry not in implemented:
        implemented.append(surface_entry)
    state["remaining_executable_actions"] = (
        [
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
        if complete
        else [
            "STAGE_07 AI policy",
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
    )
    stage02.stage01.stage00.atomic_json_write(state_path, state)


def main() -> int:
    rows = runtime_scenarios() + parser_fixture_rows()
    summary = build_summary(rows)
    failures = verify_summary(summary, rows)
    write_jsonl(STAGE07_LEDGER_PATH, rows)
    atomic_json_write(STAGE07_SUMMARY_PATH, summary)
    write_dossier(summary)
    update_state(summary, complete=False)
    result = {
        "schema_version": "vnext_production_change_stage07_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary": summary,
        "first_incomplete_invariant": "STAGE_07_AI_POLICY",
    }
    atomic_json_write(STAGE07_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
