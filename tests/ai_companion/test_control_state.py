from datetime import datetime, timedelta, timezone

from src.components.ai_companion.control_state import (
    AICompanionRuntimeGate,
    build_empty_control_state,
    validate_control_state,
    write_control_state_atomic,
)


NOW = datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc)


def _gate_config(**overrides):
    companion = {
        "enabled": True,
        "authority_level": "protective",
        "control_state_path": "pipeline_state/ai_companion/control_state.json",
    }
    companion.update(overrides)
    return {"gtos_vnext_runtime": {"ai_companion": companion}}


def _control(**overrides):
    base = {
        "type": "pause_new_entries",
        "control_id": "pause-test",
        "namespace": "operator_profile",
        "reason": "test_pause",
        "generated_at_utc": NOW.isoformat(),
        "expires_at_utc": (NOW + timedelta(minutes=15)).isoformat(),
        "evidence": [{"path": "pipeline_state/ai_companion/cycle_digest.json"}],
    }
    base.update(overrides)
    return base


def _state(*controls, authority="protective"):
    state = build_empty_control_state(authority_level=authority, now=NOW, ttl_minutes=30)
    state["controls"] = list(controls)
    return state


def test_protective_pause_control_is_accepted_for_matching_namespace():
    ok, summary = validate_control_state(
        _state(_control()),
        now=NOW,
        namespace="operator_profile",
    )

    assert ok is True
    assert summary["active"] is True
    assert summary["accepted_controls"][0]["control_id"] == "pause-test"


def test_expired_and_wrong_namespace_controls_do_not_apply():
    expired = _control(control_id="expired", expires_at_utc=(NOW - timedelta(minutes=1)).isoformat())
    wrong_ns = _control(control_id="wrong", namespace="redacted_account_live_bee34003")

    ok, summary = validate_control_state(
        _state(expired, wrong_ns),
        now=NOW,
        namespace="operator_profile",
    )

    assert ok is True
    assert summary["active"] is False
    assert summary["accepted_controls"] == []
    assert {item["reason"] for item in summary["rejected_controls"]} == {"expired", "namespace_mismatch"}


def test_missing_namespace_control_is_rejected_not_global():
    ok, summary = validate_control_state(
        _state(_control(namespace=None)),
        now=NOW,
        namespace="operator_profile",
    )

    assert ok is True
    assert summary["active"] is False
    assert summary["accepted_controls"] == []
    assert summary["rejected_controls"][0]["reason"] == "missing_namespace"


def test_control_missing_generated_timestamp_is_rejected():
    control = _control()
    control.pop("generated_at_utc")

    ok, summary = validate_control_state(
        _state(control),
        now=NOW,
        namespace="operator_profile",
    )

    assert ok is True
    assert summary["active"] is False
    assert summary["accepted_controls"] == []
    assert summary["rejected_controls"][0]["reason"] == "missing_or_invalid_generated_at_utc"


def test_future_control_timestamp_is_rejected():
    future = _control(
        generated_at_utc=(NOW + timedelta(minutes=10)).isoformat(),
        expires_at_utc=(NOW + timedelta(minutes=20)).isoformat(),
    )

    ok, summary = validate_control_state(
        _state(future),
        now=NOW,
        namespace="operator_profile",
    )

    assert ok is True
    assert summary["active"] is False
    assert summary["rejected_controls"][0]["reason"] == "generated_at_utc_in_future"


def test_control_expiry_must_be_after_generated_timestamp():
    backwards = _control(
        generated_at_utc=NOW.isoformat(),
        expires_at_utc=(NOW - timedelta(minutes=1)).isoformat(),
    )

    ok, summary = validate_control_state(
        _state(backwards),
        now=NOW - timedelta(minutes=2),
        namespace="operator_profile",
    )

    assert ok is True
    assert summary["active"] is False
    assert summary["rejected_controls"][0]["reason"] == "expires_at_not_after_generated_at"


def test_state_clock_and_ttl_are_validated():
    state = _state()
    state["generated_at_utc"] = (NOW + timedelta(minutes=10)).isoformat()
    state["expires_at_utc"] = (NOW + timedelta(minutes=200)).isoformat()

    ok, summary = validate_control_state(
        state,
        now=NOW,
        namespace="operator_profile",
        max_ttl_minutes=120,
    )

    assert ok is False
    codes = {issue["code"] for issue in summary["issues"]}
    assert "state_generated_at_utc_in_future" in codes
    assert "state_ttl_exceeds_max" in codes


def test_explicit_star_namespace_control_is_global():
    ok, summary = validate_control_state(
        _state(_control(namespace="*")),
        now=NOW,
        namespace="redacted_account_live_bee34003",
    )

    assert ok is True
    assert summary["active"] is True
    assert summary["accepted_controls"][0]["namespace"] == "*"


def test_risk_multiplier_cannot_increase_risk():
    bad = _control(
        type="risk_multiplier",
        control_id="risk-up",
        multiplier=1.1,
    )

    ok, summary = validate_control_state(
        _state(bad),
        now=NOW,
        namespace="operator_profile",
    )

    assert ok is True
    assert summary["active"] is False
    assert summary["rejected_controls"][0]["reason"] == "risk_multiplier_above_one_forbidden"


def test_runtime_gate_matches_cooldown_and_applies_lowest_risk_multiplier(tmp_path):
    state = _state(
        _control(
            type="symbol_sleeve_cooldown",
            control_id="cool-btc",
            symbol="BTCUSD",
            sleeve="crypto",
        ),
        _control(
            type="risk_multiplier",
            control_id="risk-half",
            symbol="BTCUSD",
            sleeve="crypto",
            multiplier=0.5,
        ),
        _control(
            type="risk_multiplier",
            control_id="risk-quarter",
            symbol="BTCUSD",
            sleeve="crypto",
            multiplier=0.25,
        ),
    )
    write_control_state_atomic(tmp_path, state)
    cfg = _gate_config()
    gate = AICompanionRuntimeGate(cfg, tmp_path, "operator_profile")
    snapshot = gate.snapshot(NOW)

    cooldown = gate.cooldown_for(snapshot, symbol="BTCUSD", sleeve="crypto")
    risk = gate.risk_multiplier_for(snapshot, symbol="BTCUSD", sleeve="crypto")
    adjusted = gate.adjusted_unit({"risk_pct_per_trade": 0.02, "unit_risk_pct": 0.04}, risk)

    assert cooldown.control_id == "cool-btc"
    assert risk.control_id == "risk-quarter"
    assert adjusted["risk_pct_per_trade"] == 0.005
    assert adjusted["unit_risk_pct"] == 0.01


def test_runtime_gate_parses_false_string_as_disabled(tmp_path):
    cfg = {
        "gtos_vnext_runtime": {
            "ai_companion": {
                "enabled": "false",
                "authority_level": "protective",
                "control_state_path": "pipeline_state/ai_companion/control_state.json",
            }
        }
    }

    gate = AICompanionRuntimeGate(cfg, tmp_path, "operator_profile")
    snapshot = gate.snapshot(NOW)

    assert gate.enabled is False
    assert snapshot["enabled"] is False
    assert snapshot["active"] is False


def test_protective_runtime_gate_fail_closes_when_control_state_absent(tmp_path):
    gate = AICompanionRuntimeGate(_gate_config(), tmp_path, "operator_profile")

    snapshot = gate.snapshot(NOW)
    pause = gate.control_state_issue_pause(snapshot)

    assert snapshot["ok"] is False
    assert snapshot["fail_closed_new_entries"] is True
    assert snapshot["issues"] == [
        {
            "code": "control_state_absent",
            "path": "pipeline_state/ai_companion/control_state.json",
        }
    ]
    assert pause is not None
    assert pause.type == "pause_new_entries"
    assert "control_state_absent" in pause.reason


def test_protective_runtime_gate_fail_closes_when_control_state_unreadable(tmp_path):
    state_path = tmp_path / "pipeline_state" / "ai_companion" / "control_state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text("{not json", encoding="utf-8")
    gate = AICompanionRuntimeGate(_gate_config(), tmp_path, "operator_profile")

    snapshot = gate.snapshot(NOW)
    pause = gate.control_state_issue_pause(snapshot)

    assert snapshot["ok"] is False
    assert snapshot["fail_closed_new_entries"] is True
    assert snapshot["issues"][0]["code"] == "control_state_unreadable"
    assert pause is not None
    assert "control_state_unreadable" in pause.reason


def test_protective_runtime_gate_fail_closes_when_control_state_expired(tmp_path):
    state = build_empty_control_state(
        authority_level="protective",
        now=NOW - timedelta(minutes=60),
        ttl_minutes=10,
    )
    write_control_state_atomic(tmp_path, state)
    gate = AICompanionRuntimeGate(_gate_config(), tmp_path, "operator_profile")

    snapshot = gate.snapshot(NOW)
    pause = gate.control_state_issue_pause(snapshot)

    assert snapshot["ok"] is False
    assert snapshot["fail_closed_new_entries"] is True
    assert snapshot["issues"][0]["code"] == "state_expired"
    assert pause is not None
    assert "state_expired" in pause.reason


def test_protective_runtime_gate_fail_closes_on_authority_mismatch(tmp_path):
    state = _state(authority="observe")
    write_control_state_atomic(tmp_path, state)
    gate = AICompanionRuntimeGate(_gate_config(), tmp_path, "operator_profile")

    snapshot = gate.snapshot(NOW)
    pause = gate.control_state_issue_pause(snapshot)

    assert snapshot["ok"] is False
    assert snapshot["authority_level"] == "protective"
    assert snapshot["fail_closed_new_entries"] is True
    assert snapshot["issues"][0]["code"] == "authority_level_mismatch"
    assert snapshot["issues"][0]["configured_authority_level"] == "protective"
    assert snapshot["issues"][0]["loaded_authority_level"] == "observe"
    assert pause is not None
    assert "authority_level_mismatch" in pause.reason


def test_runtime_gate_fail_closed_can_be_disabled_explicitly(tmp_path):
    gate = AICompanionRuntimeGate(
        _gate_config(fail_closed_on_issue=False),
        tmp_path,
        "operator_profile",
    )

    snapshot = gate.snapshot(NOW)

    assert snapshot["ok"] is False
    assert snapshot["fail_closed_new_entries"] is False
    assert gate.control_state_issue_pause(snapshot) is None
