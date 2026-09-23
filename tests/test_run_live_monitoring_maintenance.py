from __future__ import annotations

import json
from datetime import datetime, timezone

from scripts import run_live_monitoring_maintenance as mod


def test_route_closes_gaps_after_path_capture_and_before_final_audits():
    steps = mod.base_steps(
        max_hours=24,
        sierra_mode="skip",
        skip_live_pulse=True,
        skip_shadow_observer_once=True,
    )
    names = [step.name for step in steps]

    follow_index = names.index("follow_candidate_paths")
    post_gap_index = names.index("post_follow_live_shadow_gap_closure")
    ai_narrowing_index = names.index("ai_narrowing_policy_shadow_evaluations")
    final_gap_index = names.index("final_live_shadow_gap_closure")
    final_ai_narrowing_index = names.index("final_ai_narrowing_policy_shadow_evaluations")
    final_path_audit_index = names.index("final_candidate_path_contract_audit")
    final_observer_index = names.index("final_shadow_observer_once")
    final_observer_hardening_index = names.index("final_shadow_observer_hardening")
    verifier_index = names.index("verify_shadow_log_integrity")

    assert post_gap_index == follow_index + 1
    assert post_gap_index < ai_narrowing_index < final_gap_index
    assert follow_index < final_gap_index < final_ai_narrowing_index < final_path_audit_index < verifier_index
    assert final_path_audit_index < final_observer_index < final_observer_hardening_index < verifier_index


def test_route_defaults_are_bounded_for_daily_live_monitoring():
    parser = mod.build_parser()
    args = parser.parse_args([])

    assert args.max_hours == 24.0
    assert args.step_timeout_seconds == 900


def test_dual_broker_guard_observation_only_by_default(tmp_path, monkeypatch):
    heartbeat = tmp_path / "daemon_heartbeat_dual_broker_trade_record_projector.json"
    heartbeat.write_text(
        json.dumps({"utc": datetime.now(timezone.utc).isoformat()}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "DUAL_BROKER_HEARTBEAT_PATHS", (heartbeat,))

    guard = mod.dual_broker_activation_guard_active()

    assert guard == {
        "active": False,
        "reason": "dual_broker_heartbeat_observation_only_default_allows_maintenance",
    }


def test_dual_broker_guard_skips_widening_maintenance_when_explicitly_suppressed(
    tmp_path,
    monkeypatch,
    capsys,
):
    heartbeat = tmp_path / "daemon_heartbeat_dual_broker_trade_record_projector.json"
    heartbeat.write_text(
        json.dumps({"utc": datetime.now(timezone.utc).isoformat()}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "DUAL_BROKER_HEARTBEAT_PATHS", (heartbeat,))
    monkeypatch.setenv("GTOS_SUPPRESS_LIVE_MONITORING_MAINTENANCE_WITH_DUAL_BROKER", "1")

    rc = mod.main([
        "--run-log",
        str(tmp_path / "runs.jsonl"),
        "--state",
        str(tmp_path / "state.json"),
    ])

    assert rc == 0
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "skipped"
    assert state["reason"] == "dual_broker_activation_guard_suppressed_widening_maintenance"
    assert state["steps"] == []
    assert "dual_broker_activation_guard_suppressed_widening_maintenance" in capsys.readouterr().out
