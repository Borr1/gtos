from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, TextIO


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
ROUTE_ID = "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"

STAGE03_SUMMARY = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_SUMMARY_2026-05-25.json"
)
STAGE04_SUMMARY = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_PROP_POLICY_COMPARISON_SUMMARY_2026-05-25.json"
STAGE05_SUMMARY = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_AVOID_PRE_AI_REPAIR_SUMMARY_2026-05-25.json"
)
STAGE06_SUMMARY = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE06_LTF_ENTRY_NOFILL_REPAIR_SUMMARY_2026-05-25.json"
)
STAGE07_SUMMARY = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE07_AI_POLICY_SUPERVISOR_REPAIR_SUMMARY_2026-05-25.json"
)
STAGE07_LEDGER = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE07_AI_POLICY_SUPERVISOR_REPAIR_LEDGER_2026-05-25.jsonl"
)
STAGE08_DECISION_LEDGER = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_REPLAY_DECISION_LEDGER_2026-05-25.jsonl"
)
STAGE08_ATTEMPT_LEDGER = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_PROP_ATTEMPT_LEDGER_2026-05-25.jsonl"
)
STAGE08_REPLAY_SUMMARY = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json"
STAGE08_ABLATION_SUMMARY = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_LAYER_ABLATION_SUMMARY_2026-05-25.json"

STAGE04_MODULE_PATH = ROUTE_DIR / "build_vnext_production_candidate_repair_stage04_ev_prop_governor_2026_05_25.py"
spec = importlib.util.spec_from_file_location("stage04_prop_governor", STAGE04_MODULE_PATH)
stage04 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage04
spec.loader.exec_module(stage04)

POLICIES = stage04.POLICIES
INITIAL_BALANCE = stage04.INITIAL_BALANCE
FULL_RISK_PCT = stage04.FULL_RISK_PCT


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def terminal_family(value: Any) -> str:
    text = str(value or "")
    if text in {"target_first", "target"}:
        return "target_first"
    if text in {"stop_first", "stop"}:
        return "stop_first"
    if text == "no_fill":
        return "no_fill"
    if text == "timeout":
        return "timeout"
    if "missing_source" in text:
        return "missing_source"
    return text or "unknown"


def selected_stage07_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(STAGE07_LEDGER):
        if not row.get("stage06_selected_stream"):
            continue
        rows.append(
            {
                "candidate_id": row.get("candidate_id"),
                "as_of_utc": row.get("as_of_utc"),
                "symbol": row.get("symbol"),
                "session": row.get("session"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "source_mode": row.get("source_mode"),
                "month": row.get("month"),
                "terminal_outcome": row.get("terminal_outcome_scoring_only"),
                "simulated_r": row.get("simulated_r_scoring_only"),
                "stage07_ai_policy_action": row.get("stage07_ai_policy_action"),
                "stage07_ai_call_required_for_production": row.get(
                    "stage07_ai_call_required_for_production"
                ),
                "stage06_ltf_action": row.get("stage06_ltf_action"),
            }
        )
    rows.sort(key=lambda item: str(item.get("as_of_utc") or ""))
    return rows


def finalize_attempt_stage08(
    *,
    attempt_rows: list[dict[str, Any]],
    scenario: str,
    policy: str,
    state: Any,
    status: str,
    reason: str,
    out_attempt: TextIO,
) -> float | None:
    if not attempt_rows and status == "open_no_trades":
        return None
    first = attempt_rows[0]["as_of_utc"] if attempt_rows else state.attempt_start_utc
    last = attempt_rows[-1]["as_of_utc"] if attempt_rows else state.phase_start_utc
    duration_days = None
    if first and last:
        duration_days = max(
            0.0,
            (stage04.parse_utc(last) - stage04.parse_utc(first)).total_seconds() / 86400.0,
        )
    out_attempt.write(
        json.dumps(
            {
                "schema_version": "vnext_production_candidate_repair_stage08_prop_attempt_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY",
                "scenario": scenario,
                "policy": policy,
                "attempt_id": state.attempt_id,
                "terminal_status": status,
                "terminal_reason": reason,
                "phase": state.phase,
                "phase1_passed": state.phase1_passed,
                "start_utc": first,
                "end_utc": last,
                "duration_days": round(duration_days, 6) if duration_days is not None else None,
                "trade_count": len(attempt_rows),
                "ending_equity": round(state.equity, 6),
                "daily_floor": round(state.daily_floor(), 6),
                "overall_floor": round(state.overall_floor(), 6),
                "segmented_account_attempt": True,
            },
            sort_keys=True,
        )
        + "\n"
    )
    return duration_days


def run_policy_replay_stage08(
    *,
    scenario: str,
    policy: str,
    rows: list[dict[str, Any]],
    out_decision: TextIO,
    out_attempt: TextIO,
) -> tuple[dict[str, Any], dict[str, int]]:
    metrics = stage04.PolicyMetrics(scenario=scenario, policy=policy, input_rows=len(rows))
    state = stage04.AttemptState(scenario=scenario, policy=policy)
    attempt_rows: list[dict[str, Any]] = []
    next_attempt_id = 1
    equity_peak = INITIAL_BALANCE
    extra: Counter[str] = Counter()

    for index, row in enumerate(rows, start=1):
        as_of = stage04.parse_utc(row.get("as_of_utc"))
        if state.attempt_start_utc is None:
            state.reset_for_new_attempt(next_attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, next_attempt_id)
        state.roll_day(as_of)
        action = stage04.choose_action(policy, row, state)
        if action["action"] == "ACCOUNT_ABANDON_OR_RESTART":
            metrics.abandon_restarts += 1
            metrics.abandoned_attempts += 1
            duration_days = finalize_attempt_stage08(
                attempt_rows=attempt_rows,
                scenario=scenario,
                policy=policy,
                state=state,
                status="abandoned_for_restart",
                reason=action["reason"],
                out_attempt=out_attempt,
            )
            metrics.observe_attempt_terminal("abandoned_for_restart", duration_days)
            next_attempt_id += 1
            state.reset_for_new_attempt(next_attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, next_attempt_id)
            attempt_rows = []
            action = stage04.choose_action(policy, row, state)

        decision_attempt_id = state.attempt_id
        decision_phase = state.phase
        r_value = _as_float(row.get("simulated_r"))
        selected = action["action"] in {"ALLOW", "REDUCE_RISK", "MICRO_RISK"}
        before_equity = state.equity
        after_equity = before_equity
        terminal_event: str | None = None
        terminal = terminal_family(row.get("terminal_outcome"))

        if not selected:
            if action["action"] == "DEFER_UNTIL_RESET":
                metrics.deferred_trades += 1
            if action["reason"] == "high_quality_only_source_session_filter":
                metrics.high_quality_skips += 1
            metrics.observe_block(row, action["reason"])
            extra[f"blocked_{terminal}"] += 1
        else:
            if action["action"] == "REDUCE_RISK":
                metrics.reduced_risk_trades += 1
            if action["action"] == "MICRO_RISK":
                metrics.micro_risk_trades += 1
            if r_value is not None:
                after_equity = before_equity + before_equity * action["risk_pct"] / 100.0 * r_value
                state.equity = after_equity
                equity_peak = max(equity_peak, state.equity)
            state.trades += 1
            attempt_rows.append(
                {
                    "as_of_utc": row.get("as_of_utc"),
                    "candidate_id": row.get("candidate_id"),
                    "risk_pct": action["risk_pct"],
                    "simulated_r": r_value,
                }
            )
            metrics.observe_trade(row, action["risk_pct"], equity_peak, after_equity)
            extra[f"accepted_{terminal}"] += 1
            if state.equity <= state.daily_floor() or state.equity <= state.overall_floor():
                metrics.failed_attempts += 1
                terminal_event = "failed_prop_limit"
                duration_days = finalize_attempt_stage08(
                    attempt_rows=attempt_rows,
                    scenario=scenario,
                    policy=policy,
                    state=state,
                    status=terminal_event,
                    reason="daily_or_overall_floor_breached_after_trade",
                    out_attempt=out_attempt,
                )
                metrics.observe_attempt_terminal("failed_prop_limit", duration_days)
                next_attempt_id += 1
                state.reset_for_new_attempt(next_attempt_id, as_of)
                metrics.attempts_started = max(metrics.attempts_started, next_attempt_id)
                attempt_rows = []
            elif state.equity >= state.target_equity():
                if state.phase == 1:
                    metrics.phase1_passes += 1
                    terminal_event = "phase1_passed"
                    state.reset_for_phase2(as_of)
                else:
                    metrics.phase2_passes += 1
                    terminal_event = "phase2_passed_challenge_complete"
                    duration_days = finalize_attempt_stage08(
                        attempt_rows=attempt_rows,
                        scenario=scenario,
                        policy=policy,
                        state=state,
                        status=terminal_event,
                        reason="phase2_target_reached",
                        out_attempt=out_attempt,
                    )
                    metrics.observe_attempt_terminal(
                        "phase2_passed_challenge_complete",
                        duration_days,
                    )
                    next_attempt_id += 1
                    state.reset_for_new_attempt(next_attempt_id, as_of)
                    metrics.attempts_started = max(metrics.attempts_started, next_attempt_id)
                    attempt_rows = []

        extra["ai_calls_required_pre_prop"] += 1
        if selected:
            extra["ai_calls_required_after_prop_accept"] += 1
        else:
            extra["ai_calls_saved_by_prop_block_or_defer"] += 1

        out_decision.write(
            json.dumps(
                {
                    "schema_version": "vnext_production_candidate_repair_stage08_replay_decision_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY",
                    "scenario": scenario,
                    "policy": policy,
                    "row_index": index,
                    "candidate_id": row.get("candidate_id"),
                    "as_of_utc": row.get("as_of_utc"),
                    "symbol": row.get("symbol"),
                    "session": row.get("session"),
                    "side": row.get("side"),
                    "framework": row.get("framework"),
                    "source_mode": row.get("source_mode"),
                    "month": row.get("month"),
                    "attempt_id": decision_attempt_id,
                    "phase": decision_phase,
                    "action": action["action"],
                    "risk_pct": action["risk_pct"],
                    "reason": action["reason"],
                    "selected": selected,
                    "stage07_ai_policy_action": row.get("stage07_ai_policy_action"),
                    "stage06_ltf_action": row.get("stage06_ltf_action"),
                    "terminal_outcome_scoring_only": row.get("terminal_outcome"),
                    "simulated_r_scoring_only": r_value,
                    "decision_inputs_no_future_r": action["decision_inputs_no_future_r"],
                    "pre_trade_equity": round(before_equity, 6),
                    "post_trade_equity": round(after_equity, 6),
                    "remaining_daily_cushion": action["remaining_daily_cushion"],
                    "remaining_overall_cushion": action["remaining_overall_cushion"],
                    "terminal_event_after_scoring": terminal_event,
                },
                sort_keys=True,
            )
            + "\n"
        )

    if attempt_rows:
        metrics.open_attempts += 1
        duration_days = finalize_attempt_stage08(
            attempt_rows=attempt_rows,
            scenario=scenario,
            policy=policy,
            state=state,
            status="open_at_replay_end",
            reason="historical_stream_ended_before_pass_or_fail",
            out_attempt=out_attempt,
        )
        metrics.observe_attempt_terminal("open_at_replay_end", duration_days)

    record = metrics.to_record()
    record.update(
        {
            "no_fill_avoided": extra.get("blocked_no_fill", 0),
            "no_fill_accepted": extra.get("accepted_no_fill", 0),
            "stop_first_avoided": extra.get("blocked_stop_first", 0),
            "stop_first_accepted": extra.get("accepted_stop_first", 0),
            "ai_calls_required_pre_prop": extra["ai_calls_required_pre_prop"],
            "ai_calls_required_after_prop_accept": extra["ai_calls_required_after_prop_accept"],
            "ai_calls_saved_by_prop_block_or_defer": extra[
                "ai_calls_saved_by_prop_block_or_defer"
            ],
            "ai_calls_malformed": 0,
            "ai_calls_repaired": 0,
            "ai_calls_demoted": 0,
            "paid_api_or_vendor_calls_made": 0,
        }
    )
    return record, dict(extra)


def best_policy(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        records.values(),
        key=lambda item: (
            item.get("reference_ev_per_terminal_day_usd_fee599_payout8000") or -10**9,
            item["payout_sensitivity_grid"][4]["expected_value_per_attempt_usd"],
            item["risk_adjusted_r"],
            item["pass_rate"],
            -item["account_loss_rate"],
        ),
        reverse=True,
    )
    top = ranked[0]
    return {
        "policy": top["policy"],
        "reference_expected_value_per_attempt_usd": top["payout_sensitivity_grid"][4][
            "expected_value_per_attempt_usd"
        ],
        "reference_ev_per_terminal_day_usd_fee599_payout8000": top[
            "reference_ev_per_terminal_day_usd_fee599_payout8000"
        ],
        "risk_adjusted_r": top["risk_adjusted_r"],
        "pass_rate": top["pass_rate"],
        "account_loss_rate": top["account_loss_rate"],
        "avg_time_to_pass_days": top["avg_time_to_pass_days"],
        "avg_time_to_terminal_days": top["avg_time_to_terminal_days"],
    }


def build_ablation_summary(
    *,
    stage03_summary: dict[str, Any],
    stage04_summary: dict[str, Any],
    stage05_summary: dict[str, Any],
    stage06_summary: dict[str, Any],
    stage07_summary: dict[str, Any],
    stage08_policy_metrics: dict[str, dict[str, Any]],
    stage08_best: dict[str, Any],
) -> dict[str, Any]:
    s03 = stage03_summary.get("scenario_metrics") or {}
    s07 = stage07_summary.get("scenario_metrics") or {}
    stage04_best = (
        stage04_summary.get("scenarios", {})
        .get("vnext_executable_stream_with_ev_prop_governance_contract", {})
        .get("best_policy_reference_fee_599_payout_8000", {})
    )
    no_prop = s07.get("stage07_production_ai_policy_contract") or {}
    stage05_repaired = (
        stage05_summary.get("scenario_metrics", {}).get(
            "stage05_avoid_pre_ai_repaired_without_prop", {}
        )
        or {}
    )
    best_record = stage08_policy_metrics[stage08_best["policy"]]
    layers = [
        {
            "layer": "baseline_current_shadow",
            "selected_count": s03.get("current_baseline_executable_stream", {}).get(
                "selected_count"
            ),
            "total_r": s03.get("current_baseline_executable_stream", {}).get("total_r"),
            "expectancy_r": s03.get("current_baseline_executable_stream", {}).get(
                "expectancy_r"
            ),
            "interpretation": "current baseline executable stream before vNext repair layers",
        },
        {
            "layer": "stage03_repaired_executable_stream_no_prop",
            "selected_count": s03.get(
                "vnext_executable_stream_without_prop_governance", {}
            ).get("selected_count"),
            "total_r": s03.get("vnext_executable_stream_without_prop_governance", {}).get(
                "total_r"
            ),
            "expectancy_r": s03.get(
                "vnext_executable_stream_without_prop_governance", {}
            ).get("expectancy_r"),
            "interpretation": "LEGACY/MIXED/off-KZ/pre-AI rows no longer consume prop budget",
        },
        {
            "layer": "stage05_avoid_pre_ai_demotion",
            "selected_count": no_prop.get("selected_count"),
            "total_r": no_prop.get("total_r"),
            "expectancy_r": no_prop.get("expectancy_r"),
            "delta_r_vs_stage03_vnext_no_prop": round(
                float(no_prop.get("total_r") or 0)
                - float(
                    s03.get("vnext_executable_stream_without_prop_governance", {}).get(
                        "total_r"
                    )
                    or 0
                ),
                12,
            ),
            "recovered_rows": stage05_repaired.get("recovered_count"),
            "recovered_r": stage05_repaired.get("recovered_r"),
            "interpretation": "harmful broad AVOID/pre-AI pressure demoted to context",
        },
        {
            "layer": "stage06_ltf_execution_monitor",
            "selected_count": stage06_summary.get("scenario_metrics", {})
            .get("stage06_ltf_repaired_execution_policy", {})
            .get("selected_count"),
            "execution_behavior_changed_rows": stage06_summary.get("replay_effect", {}).get(
                "execution_behavior_changed_rows"
            ),
            "source_capture_required_rows": stage06_summary.get("replay_effect", {}).get(
                "source_capture_required_rows"
            ),
            "interpretation": "LTF changes behavior via monitor/source-capture, not a hard skip",
        },
        {
            "layer": "stage07_ai_policy_contract",
            "selected_count": no_prop.get("selected_count"),
            "ai_required_rows": stage07_summary.get("stage07_ai_required_for_production_rows"),
            "no_paid_selected_count": s07.get("stage07_no_paid_call_diagnostic", {}).get(
                "selected_count"
            ),
            "interpretation": "no-paid route is diagnostic only; production stream requires AI validation",
        },
        {
            "layer": "stage04_prop_on_pre_stage05_stream",
            "selected_count": None,
            "best_policy": stage04_best.get("policy"),
            "pass_rate": stage04_best.get("pass_rate"),
            "account_loss_rate": stage04_best.get("account_loss_rate"),
            "reference_ev_per_terminal_day": stage04_best.get(
                "reference_ev_per_terminal_day_usd_fee599_payout8000"
            ),
            "interpretation": "old prop repair over Stage03-only stream, superseded by Stage08",
        },
        {
            "layer": "stage08_prop_on_repaired_stage07_stream",
            "selected_count": best_record.get("allowed_trades"),
            "best_policy": stage08_best.get("policy"),
            "pass_rate": stage08_best.get("pass_rate"),
            "account_loss_rate": stage08_best.get("account_loss_rate"),
            "reference_ev_per_terminal_day": stage08_best.get(
                "reference_ev_per_terminal_day_usd_fee599_payout8000"
            ),
            "risk_adjusted_r": stage08_best.get("risk_adjusted_r"),
            "interpretation": "segmented prop governor recomputed after Stage05-07 repairs",
        },
    ]
    return {
        "schema_version": "vnext_production_candidate_repair_layer_ablation_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "layers": layers,
        "stage08_best_policy": stage08_best,
        "stage08_policy_metric_keys": sorted(stage08_policy_metrics.keys()),
        "stage08_replay_supersedes_stage04_prop_on_stage03_only_stream": True,
    }


def build() -> dict[str, Any]:
    stage03_summary = load_json(STAGE03_SUMMARY)
    stage04_summary = load_json(STAGE04_SUMMARY)
    stage05_summary = load_json(STAGE05_SUMMARY)
    stage06_summary = load_json(STAGE06_SUMMARY)
    stage07_summary = load_json(STAGE07_SUMMARY)
    rows = selected_stage07_rows()

    policy_metrics: dict[str, dict[str, Any]] = {}
    policy_extra_counts: dict[str, dict[str, int]] = {}
    with STAGE08_DECISION_LEDGER.open("w", encoding="utf-8", newline="\n") as decisions, STAGE08_ATTEMPT_LEDGER.open(
        "w", encoding="utf-8", newline="\n"
    ) as attempts:
        for policy in POLICIES:
            record, extra = run_policy_replay_stage08(
                scenario="stage08_repaired_stage07_stream_with_ev_prop_governor",
                policy=policy,
                rows=rows,
                out_decision=decisions,
                out_attempt=attempts,
            )
            policy_metrics[policy] = record
            policy_extra_counts[policy] = extra

    best = best_policy(policy_metrics)
    stage07_no_prop = (
        stage07_summary.get("scenario_metrics", {}).get("stage07_production_ai_policy_contract")
        or {}
    )
    stage07_no_paid = (
        stage07_summary.get("scenario_metrics", {}).get("stage07_no_paid_call_diagnostic") or {}
    )
    best_record = policy_metrics[best["policy"]]
    replay_summary = {
        "schema_version": "vnext_production_candidate_repair_stage08_replay_metrics_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY",
        "created_at_utc": utc_now(),
        "current_git_head": git_head(),
        "inputs": {
            "stage03_summary": rel(STAGE03_SUMMARY),
            "stage03_summary_sha256": sha256_file(STAGE03_SUMMARY),
            "stage04_summary": rel(STAGE04_SUMMARY),
            "stage04_summary_sha256": sha256_file(STAGE04_SUMMARY),
            "stage05_summary": rel(STAGE05_SUMMARY),
            "stage05_summary_sha256": sha256_file(STAGE05_SUMMARY),
            "stage06_summary": rel(STAGE06_SUMMARY),
            "stage06_summary_sha256": sha256_file(STAGE06_SUMMARY),
            "stage07_summary": rel(STAGE07_SUMMARY),
            "stage07_summary_sha256": sha256_file(STAGE07_SUMMARY),
            "stage07_ledger": rel(STAGE07_LEDGER),
            "stage07_ledger_sha256": sha256_file(STAGE07_LEDGER),
        },
        "decision_ledger": rel(STAGE08_DECISION_LEDGER),
        "decision_ledger_sha256": sha256_file(STAGE08_DECISION_LEDGER),
        "attempt_ledger": rel(STAGE08_ATTEMPT_LEDGER),
        "attempt_ledger_sha256": sha256_file(STAGE08_ATTEMPT_LEDGER),
        "candidate_universe_rows": int(stage07_summary.get("ledger_rows") or 0),
        "executable_stream_rows": len(rows),
        "policies_compared": list(POLICIES),
        "policy_metrics": policy_metrics,
        "policy_extra_counts": policy_extra_counts,
        "best_policy_reference_fee_599_payout_8000": best,
        "scenario_metrics": {
            "stage07_no_prop_ai_required_stream": stage07_no_prop,
            "stage08_best_prop_governed_repaired_stream": best_record,
            "stage08_no_paid_call_diagnostic": stage07_no_paid,
        },
        "required_metric_coverage": {
            "candidate_universe_rows": True,
            "executable_stream_rows": True,
            "selected_rows": True,
            "performance_rows": True,
            "total_r": True,
            "risk_adjusted_r": True,
            "exact_r_proxy_r_source_status": True,
            "expectancy": True,
            "win_rate": True,
            "profit_factor": True,
            "drawdown": True,
            "max_loss_streak": True,
            "coverage": True,
            "selected_only_coverage": True,
            "missed_winners_avoided_losers_accepted_losers_blocked_winners": True,
            "prop_pass_fail_ev_time": True,
            "opportunity_cost": True,
            "no_fill_stop_first": True,
            "ai_calls": True,
            "ltf_changed_entry": True,
            "off_kz_treatment": True,
        },
        "source_status_counts": stage06_summary.get("source_status_counts", {}),
        "ai_call_counts": {
            "required_pre_prop": len(rows),
            "required_after_best_prop_accept": best_record.get("ai_calls_required_after_prop_accept"),
            "saved_by_best_prop_block_or_defer": best_record.get(
                "ai_calls_saved_by_prop_block_or_defer"
            ),
            "malformed": 0,
            "repaired": 0,
            "demoted": 0,
            "paid_api_or_vendor_calls_made": 0,
        },
        "ltf_changed_entry_outcomes": stage06_summary.get("replay_effect", {}),
        "off_kz_treatment": {
            "off_kz_rows_in_candidate_universe": stage03_summary.get("candidate_universe_coverage", {})
            .get("sessions", {})
            .get("off_kz"),
            "off_kz_rows_in_repaired_selected_stream": stage07_no_prop.get(
                "selected_only_coverage", {}
            )
            .get("sessions", {})
            .get("off_kz", 0),
            "off_kz_prop_governance_policy": "diagnostic_only_non_executable",
        },
        "no_paid_call_replay_diagnostic_only": True,
        "paid_api_or_vendor_calls_made": 0,
        "broker_facing_activation_change": False,
        "stage08_decision": "full_repaired_forward_replay_materialized_pending_stage09_decision_dossier",
    }
    STAGE08_REPLAY_SUMMARY.write_text(
        json.dumps(replay_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    ablation = build_ablation_summary(
        stage03_summary=stage03_summary,
        stage04_summary=stage04_summary,
        stage05_summary=stage05_summary,
        stage06_summary=stage06_summary,
        stage07_summary=stage07_summary,
        stage08_policy_metrics=policy_metrics,
        stage08_best=best,
    )
    STAGE08_ABLATION_SUMMARY.write_text(
        json.dumps(ablation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return replay_summary


def main() -> None:
    summary = build()
    print(
        json.dumps(
            {
                "ok": True,
                "candidate_universe_rows": summary["candidate_universe_rows"],
                "executable_stream_rows": summary["executable_stream_rows"],
                "best_policy": summary["best_policy_reference_fee_599_payout_8000"]["policy"],
                "best_policy_risk_adjusted_r": summary[
                    "best_policy_reference_fee_599_payout_8000"
                ]["risk_adjusted_r"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
