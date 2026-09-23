from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


MODULE_PATH = Path(__file__).with_name("build_vnext_production_change_stage07_ai_policy_2026_05_25.py")
spec = importlib.util.spec_from_file_location("vnext_prod_stage07", MODULE_PATH)
stage07 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage07)

stage06 = stage07.stage06
stage02 = stage07.stage02
REPO_ROOT = stage07.REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.ai_decision_trace_logger import build_ai_decision_trace_row  # noqa: E402
from src.components.ai_supervisor import (  # noqa: E402
    apply_ai_supervisor_runtime_overrides,
    evaluate_ai_supervisor,
    repair_ai_response_format_preserving_semantics,
)
from src.components.primary_analyzer import PrimaryAnalyzer  # noqa: E402


ROUTE_ID = stage07.ROUTE_ID
ROUTE_DIR = stage07.ROUTE_DIR
STATE_PATH = stage07.STATE_PATH
DECISION_SURFACE_PATH = stage07.DECISION_SURFACE_PATH
STAGE08_LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_AI_SUPERVISOR_LEDGER_2026-05-25.jsonl"
STAGE08_SUMMARY_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE08_AI_SUPERVISOR_SUMMARY_2026-05-25.json"
STAGE08_DOSSIER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_AI_SUPERVISOR_DOSSIER_2026-05-25.md"
STAGE08_VERIFICATION_RESULT_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE08_VERIFICATION_RESULT_2026-05-25.json"

REQUIRED_SCENARIOS = {
    "healthy_hash_cost_trace",
    "warn_parse_retry",
    "disable_malformed_threshold",
    "disable_missing_source_bound",
    "disable_abnormal_candidate_cluster",
    "disable_stale_artifact_load",
    "supervisor_disabled",
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


def _counter_to_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted((str(key), int(value)) for key, value in counter.items()))


def stage08_surface_summary() -> dict[str, Any]:
    rows = [
        row
        for row in read_jsonl(DECISION_SURFACE_PATH)
        if "STAGE_08_AI_SUPERVISOR" in (row.get("required_stages") or [])
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


def _trace_row(*, status: str = "parsed_first_attempt", decision: str = "NO_TRADE", symbol: str = "XAUUSD") -> dict[str, Any]:
    class _Result:
        framework = "none"
        no_trade_reason = "fixture"
        trade_parameters = None

        def __init__(self, decision: str) -> None:
            self.decision = decision

        def model_dump(self, mode: str = "json") -> dict[str, Any]:
            return {"decision": self.decision}

    return build_ai_decision_trace_row(
        system_prompt="stage08-system",
        user_message="stage08-user",
        raw_response='{"decision":"NO_TRADE"}',
        result=_Result(decision),
        usage={"input_tokens": 100, "output_tokens": 25, "cache_read_tokens": 10},
        symbol=symbol,
        candle_time="2026-05-25T00:00:00Z",
        kill_zone="london",
        model="claude-sonnet-4-6",
        backend_mode="api",
        response_status=status,
        parse_attempts=2 if status == "parsed_retry" else 1,
    )


def runtime_scenarios() -> list[dict[str, Any]]:
    base_cfg = {
        "ai_supervisor": {
            "enabled": True,
            "apply_runtime_overrides": True,
            "max_malformed_rows": 2,
            "max_malformed_demoted_rows": 1,
            "max_missing_source_bound_rows": 1,
            "max_candidate_cluster_rows": 2,
        },
        "gtos_vnext_runtime": {
            "pre_ai_apply_to_ai_call": True,
            "ai_policy_apply_to_ai_call": True,
        },
    }
    definitions = [
        ("healthy_hash_cost_trace", base_cfg, [_trace_row()], [], []),
        ("warn_parse_retry", base_cfg, [_trace_row(status="parsed_retry")], [], []),
        (
            "disable_malformed_threshold",
            base_cfg,
            [_trace_row(status="malformed_demoted")],
            [{"attempt": 1}, {"attempt": 2}],
            [],
        ),
        (
            "disable_missing_source_bound",
            base_cfg,
            [_trace_row()],
            [],
            [
                {
                    "phase": "ai_policy_pre_call",
                    "decision": {
                        "action": "CALL_AI_NARROWED_ROUTE",
                        "would_action": "CALL_AI_NARROWED_ROUTE",
                        "prompt_scope": {"source_bound": False},
                    },
                }
            ],
        ),
        (
            "disable_abnormal_candidate_cluster",
            base_cfg,
            [
                _trace_row(decision="CANDIDATE", symbol="XAUUSD"),
                _trace_row(decision="CANDIDATE", symbol="XAUUSD"),
                _trace_row(decision="CANDIDATE", symbol="XAUUSD"),
            ],
            [],
            [],
        ),
        (
            "disable_stale_artifact_load",
            base_cfg,
            [_trace_row()],
            [],
            [
                {
                    "phase": "pre_ai",
                    "decision": {"reason": "vnext_evidence_index_below_min_loaded_rows"},
                }
            ],
        ),
        (
            "supervisor_disabled",
            {"ai_supervisor": {"enabled": False}, "gtos_vnext_runtime": {}},
            [],
            [],
            [],
        ),
    ]
    rows: list[dict[str, Any]] = []
    for scenario_id, cfg, trace_rows, malformed_rows, vnext_rows in definitions:
        decision = evaluate_ai_supervisor(
            config=cfg,
            trace_rows=trace_rows,
            malformed_rows=malformed_rows,
            vnext_rows=vnext_rows,
        )
        effective = apply_ai_supervisor_runtime_overrides(cfg, decision)
        rows.append(
            {
                "schema_version": "vnext_production_change_stage08_ai_supervisor_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_08_AI_SUPERVISOR",
                "row_type": "runtime_supervisor_scenario",
                "scenario_id": scenario_id,
                "action": decision.action,
                "severity": decision.severity,
                "disable_ai_narrowing": decision.disable_ai_narrowing,
                "pre_ai_apply_to_ai_call_after": effective.get("gtos_vnext_runtime", {}).get(
                    "pre_ai_apply_to_ai_call"
                ),
                "ai_policy_apply_to_ai_call_after": effective.get("gtos_vnext_runtime", {}).get(
                    "ai_policy_apply_to_ai_call"
                ),
                "decision_record": decision.to_record(),
            }
        )
    return rows


def repair_fixture_rows() -> list[dict[str, Any]]:
    analyzer = PrimaryAnalyzer.__new__(PrimaryAnalyzer)
    analyzer.model = "claude-sonnet-4-6"
    analyzer.config = {"ai_supervisor": {"format_repair_enabled": True}}
    valid_payload = stage07._valid_payload("NO_TRADE")
    fixtures = {
        "preamble_fenced_json": "AI says:\n```json\n" + json.dumps(valid_payload) + "\n```",
        "already_valid_json": json.dumps(valid_payload),
        "no_json_object": "NO_TRADE because no setup",
    }
    rows: list[dict[str, Any]] = []
    for fixture_id, raw in fixtures.items():
        repair = repair_ai_response_format_preserving_semantics(raw)
        parsed = False
        parsed_decision = None
        error = None
        try:
            result = analyzer._parse_and_validate(raw)
            parsed = True
            parsed_decision = result.decision
        except Exception as exc:  # noqa: BLE001 - malformed fixture expected.
            error = type(exc).__name__
        rows.append(
            {
                "schema_version": "vnext_production_change_stage08_ai_supervisor_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_08_AI_SUPERVISOR",
                "row_type": "format_repair_fixture",
                "fixture_id": fixture_id,
                "repaired": repair.repaired,
                "repair_reason": repair.reason,
                "parsed_after_supervisor_repair": parsed,
                "parsed_decision": parsed_decision,
                "error_type": error,
            }
        )
    return rows


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scenario_rows = [row for row in rows if row.get("row_type") == "runtime_supervisor_scenario"]
    repair_rows = [row for row in rows if row.get("row_type") == "format_repair_fixture"]
    return {
        "schema_version": "vnext_production_change_stage08_ai_supervisor_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "stage08_surface": stage08_surface_summary(),
        "scenario_row_count": len(scenario_rows),
        "runtime_scenario_action_counts": _counter_to_dict(
            Counter(str(row.get("action")) for row in scenario_rows)
        ),
        "runtime_scenario_severity_counts": _counter_to_dict(
            Counter(str(row.get("severity")) for row in scenario_rows)
        ),
        "format_repair_fixture_count": len(repair_rows),
        "format_repair_parsed_counts": _counter_to_dict(
            Counter(str(row.get("parsed_after_supervisor_repair")) for row in repair_rows)
        ),
    }


def write_dossier(summary: dict[str, Any]) -> None:
    surface = summary["stage08_surface"]
    lines = [
        "# vNext Production Change Stage08 AI Supervisor Dossier",
        "",
        f"Created: {summary['created_at_utc']}",
        "",
        "## Runtime Change",
        "",
        "- Added `src/components/ai_supervisor.py` as a bounded schema guardian and diagnostics engine.",
        "- The supervisor monitors AI trace hash health, malformed responses, schema/parse failures, token-cost telemetry, route drift, missing source-bound prompt fields, stale artifact loads, and abnormal candidate clusters.",
        "- The supervisor can disable active AI-narrowing effects by forcing `pre_ai_apply_to_ai_call=false` and `ai_policy_apply_to_ai_call=false` in an effective config copy.",
        "- It never changes trade direction, trade parameters, prop budget math, or candidate scoring.",
        "- Formatting repair only extracts an intact JSON object and then relies on `PrimaryAnalysisOutput` schema validation.",
        "",
        "## Evidence Consumed",
        "",
        f"- Stage08 decision-surface groups: {surface['group_count']}.",
        f"- Stage08 decision-map rows: {surface['row_count']}.",
        f"- Runtime surfaces: {json.dumps(surface['runtime_surfaces'], sort_keys=True)}.",
        f"- Source components: {json.dumps(surface['source_components'], sort_keys=True)}.",
        "",
        "## Scenario Coverage",
        "",
        f"- Runtime scenario rows: {summary['scenario_row_count']}.",
        f"- Action counts: {json.dumps(summary['runtime_scenario_action_counts'], sort_keys=True)}.",
        f"- Severity counts: {json.dumps(summary['runtime_scenario_severity_counts'], sort_keys=True)}.",
        f"- Format repair fixtures: {summary['format_repair_fixture_count']}.",
        f"- Format repair parsed counts: {json.dumps(summary['format_repair_parsed_counts'], sort_keys=True)}.",
        "",
        "## Activation Boundary",
        "",
        "- `ai_supervisor.apply_runtime_overrides=true` only disables AI-narrowing active effects when configured health checks fail.",
        "- No live trading, broker mutation, paid API/vendor call, source deletion, remote push, or activation flip is performed.",
        "",
    ]
    STAGE08_DOSSIER_PATH.write_text("\n".join(lines), encoding="utf-8")


def verify_summary(summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    scenario_rows = [row for row in rows if row.get("row_type") == "runtime_supervisor_scenario"]
    scenario_ids = {str(row["scenario_id"]) for row in scenario_rows}
    if scenario_ids != REQUIRED_SCENARIOS:
        failures.append(f"scenario coverage mismatch: {sorted(REQUIRED_SCENARIOS - scenario_ids)}")
    if summary["stage08_surface"]["group_count"] != 51:
        failures.append("Stage08 decision-surface group count mismatch")
    if summary["stage08_surface"]["row_count"] != 149:
        failures.append("Stage08 decision-surface row count mismatch")
    actions = summary["runtime_scenario_action_counts"]
    for required in ("HEALTHY", "WARN", "DISABLE_AI_NARROWING", "SUPERVISOR_DISABLED"):
        if actions.get(required, 0) <= 0:
            failures.append(f"missing supervisor action {required}")
    repair_counts = summary["format_repair_parsed_counts"]
    if repair_counts.get("True", 0) < 2 or repair_counts.get("False", 0) < 1:
        failures.append("format repair fixtures did not cover valid and invalid responses")
    return failures


def update_state(summary: dict[str, Any], *, complete: bool) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = stage02.git_head()
    state["dirty_tracked_paths"] = stage02.git_status_short()
    state["current_stage"] = "STAGE_09_FORWARD_ONLY_REPLAY" if complete else "STAGE_08_AI_SUPERVISOR"
    state["stage_status_table"]["STAGE_08_AI_SUPERVISOR"] = "complete" if complete else "in_progress"
    if complete:
        state["stage_status_table"]["STAGE_09_FORWARD_ONLY_REPLAY"] = "in_progress"
        state["active_invariant"] = "run_post_implementation_forward_only_replay"
        state["first_incomplete_invariant"] = "STAGE_09_FORWARD_ONLY_REPLAY"
        state["exact_next_action"] = (
            "Run the Stage09 post-implementation forward-only replay comparison without "
            "restarting Stage00-08."
        )
    else:
        state["active_invariant"] = "implement_bounded_ai_supervisor"
        state["first_incomplete_invariant"] = "STAGE_08_AI_SUPERVISOR"
        state["exact_next_action"] = (
            "Run Stage08 verifier and focused AI supervisor tests, then mark Stage08 complete."
        )
    outputs = state.setdefault("output_artifact_paths", {})
    outputs["ai_supervisor_ledger"] = rel(STAGE08_LEDGER_PATH)
    outputs["stage08_ai_supervisor_summary"] = rel(STAGE08_SUMMARY_PATH)
    outputs["ai_supervisor_dossier"] = rel(STAGE08_DOSSIER_PATH)
    outputs["stage08_verification_result"] = rel(STAGE08_VERIFICATION_RESULT_PATH)
    state.setdefault("rows_groups_processed", {})[
        "stage08_ai_supervisor_runtime_scenarios"
    ] = summary["scenario_row_count"]
    state["rows_groups_processed"]["stage08_decision_surface_rows"] = summary[
        "stage08_surface"
    ]["row_count"]
    state["row_count_hash_coverage"]["stage08_ai_supervisor_summary"] = {
        "stage08_surface_groups": summary["stage08_surface"]["group_count"],
        "stage08_surface_rows": summary["stage08_surface"]["row_count"],
        "scenario_row_count": summary["scenario_row_count"],
        "format_repair_fixture_count": summary["format_repair_fixture_count"],
        "runtime_scenario_action_counts": summary["runtime_scenario_action_counts"],
    }
    state["verification_status"]["stage08_ai_supervisor_built"] = True
    state["verification_status"]["stage08_ai_supervisor_runtime_scenarios"] = summary[
        "scenario_row_count"
    ]
    state["verification_status"]["stage08_verifier_ok"] = complete
    implemented = state.setdefault("implemented_surfaces", [])
    surface_entry = {
        "stage": "STAGE_08_AI_SUPERVISOR",
        "surface": "bounded_ai_supervisor_malformed_response_controls",
        "runtime_row_count": summary["stage08_surface"]["row_count"],
        "activation_gate": "ai_supervisor.apply_runtime_overrides",
        "artifact": rel(STAGE08_LEDGER_PATH),
    }
    if surface_entry not in implemented:
        implemented.append(surface_entry)
    state["remaining_executable_actions"] = (
        [
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
        if complete
        else [
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ]
    )
    stage02.stage01.stage00.atomic_json_write(state_path, state)


def main() -> int:
    rows = runtime_scenarios() + repair_fixture_rows()
    summary = build_summary(rows)
    failures = verify_summary(summary, rows)
    write_jsonl(STAGE08_LEDGER_PATH, rows)
    atomic_json_write(STAGE08_SUMMARY_PATH, summary)
    write_dossier(summary)
    update_state(summary, complete=False)
    result = {
        "schema_version": "vnext_production_change_stage08_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary": summary,
        "first_incomplete_invariant": "STAGE_08_AI_SUPERVISOR",
    }
    atomic_json_write(STAGE08_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
