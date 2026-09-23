from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

from scripts import audit_shadow_observer_hardening as script
from src.research_infra.shadow_observer_hardening import (
    ACTION_REQUIRED,
    PROMOTION_VERDICT,
    STATUS_OK,
    build_report_payload,
    build_status_row,
    final_closeout_detection,
    normalize_source_registry,
    render_markdown,
    stale_observer_detection,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _observer_registry() -> dict:
    forbidden = [
        "ai_api_call",
        "canary_call",
        "order_send",
        "execution_engine",
        "permission_gate",
        "outcome_opening",
    ]
    return {
        "schema_version": "shadow_observer_registry_v1",
        "instruments": [
            {
                "observer_id": "eurusd_6e_mso_shadow_v1",
                "enabled": True,
                "activation_state": "ACTIVE_MSO_SHADOW",
                "symbol": "EURUSD",
                "broker_symbol": "EURUSD",
                "config_symbol": "EURUSD",
                "family": "EURUSD/6E",
                "evidence_class": "FORWARD_SHADOW",
                "source_status": "LABEL_STATUS_ONLY_NO_REGISTERED_OUTCOME_COHORT",
                "pre_registered_question_id": "SHADOW-EURUSD",
                "allowed_rows": ["strategy_follow_evaluation_v1"],
                "forbidden": forbidden,
            },
            {
                "observer_id": "ger40_tier2_mso_shadow_v1",
                "enabled": True,
                "activation_state": "ACTIVE_MSO_SHADOW",
                "symbol": "GER40",
                "broker_symbol": "GER30",
                "config_symbol": "GER40",
                "family": "GER40 tier-2",
                "evidence_class": "FORWARD_SHADOW",
                "source_status": "TIER2_BACKTEST_ONLY_NO_PROMOTION",
                "pre_registered_question_id": "SHADOW-GER40",
                "allowed_rows": ["strategy_follow_evaluation_v1"],
                "forbidden": forbidden,
            },
            {
                "observer_id": "uko_usd_cl_context_only_v1",
                "enabled": False,
                "activation_state": "CONTEXT_CONTROL_ONLY",
                "symbol": "UKOUSD",
                "broker_symbol": "UKOUSD",
                "config_symbol": None,
                "family": "CL control",
                "evidence_class": "CONTROL_ONLY",
                "source_status": "LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT",
            },
            {
                "observer_id": "spx500_es_prereg_required_v1",
                "enabled": False,
                "activation_state": "PRE_REGISTRATION_REQUIRED",
                "symbol": "SPX500",
                "broker_symbol": "SPX500",
                "config_symbol": None,
                "family": "ES/MES",
                "evidence_class": "FORWARD_SHADOW",
                "source_status": "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT",
            },
            {
                "observer_id": "zn_rates_context_only_v1",
                "enabled": False,
                "activation_state": "CONTEXT_CONTROL_ONLY",
                "symbol": "ZN_CONTROL",
                "broker_symbol": None,
                "config_symbol": None,
                "family": "ZN rates/control",
                "evidence_class": "CONTROL_ONLY",
                "source_status": "LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT",
            },
            {
                "observer_id": "vix_vxm_context_only_v1",
                "enabled": False,
                "activation_state": "CONTEXT_CONTROL_ONLY",
                "symbol": "VIX_VXM",
                "broker_symbol": None,
                "config_symbol": None,
                "family": "VIX/VXM volatility controls",
                "evidence_class": "CONTROL_ONLY",
                "source_status": "LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT",
            },
            {
                "observer_id": "nzdusd_historical_excluded_v1",
                "enabled": False,
                "activation_state": "EXCLUDED_KILLED_HISTORICAL",
                "symbol": "NZDUSD",
                "broker_symbol": "NZDUSD",
                "config_symbol": "NZDUSD",
                "family": "historical killed expansion lane",
                "evidence_class": "DISCOVERY_ONLY",
                "source_status": "DO_NOT_FOLLOW_WITHOUT_NEW_OWNER_DECISION",
            },
            {
                "observer_id": "xagusd_depth_future_v1",
                "enabled": False,
                "activation_state": "PRE_REGISTRATION_REQUIRED",
                "symbol": "XAGUSD",
                "broker_symbol": "XAGUSD",
                "config_symbol": "XAGUSD",
                "family": "future SIL/SI depth follow-up",
                "evidence_class": "FORWARD_SHADOW",
                "source_status": "SOURCE_POLICY_REQUIRED_BEFORE_ENABLE",
            },
        ],
    }


def _agent_config() -> dict:
    return {
        "instruments": {
            "EURUSD": {
                "market": {
                    "kill_zones": {
                        "london": {"start_utc": "07:00", "end_utc": "12:00"},
                        "ny": {"start_utc": "13:00", "end_utc": "15:30"},
                    }
                }
            },
            "GER40": {
                "market": {
                    "kill_zones": {
                        "london": {"start_utc": "08:00", "end_utc": "12:00"},
                        "ny": {"start_utc": "14:00", "end_utc": "19:00"},
                    }
                }
            },
        }
    }


def _status_rows() -> list[tuple[int, dict]]:
    return [
        (
            1,
            {
                "schema_version": "shadow_observer_status_v1",
                "observer_id": "eurusd_6e_mso_shadow_v1",
                "symbol": "EURUSD",
                "created_at_utc": "2026-05-05T00:02:00+00:00",
                "lifecycle_status": "SKIPPED_OUTSIDE_KILL_ZONE",
                "no_ai_calls": True,
                "no_canary_required": True,
                "no_execution": True,
                "promotion_verdict": PROMOTION_VERDICT,
            },
        ),
        (
            2,
            {
                "schema_version": "shadow_observer_status_v1",
                "observer_id": "ger40_tier2_mso_shadow_v1",
                "symbol": "GER40",
                "created_at_utc": "2026-05-05T00:03:00+00:00",
                "lifecycle_status": "SKIPPED_OUTSIDE_KILL_ZONE",
                "no_ai_calls": True,
                "no_canary_required": True,
                "no_execution": True,
                "promotion_verdict": PROMOTION_VERDICT,
            },
        ),
    ]


def _strategy_rows() -> list[tuple[int, dict]]:
    return [
        (
            1,
            {
                "schema_version": "strategy_follow_evaluation_v1",
                "source_file": "shadow_observer_mso_no_ai",
                "symbol": "EURUSD",
                "created_at_utc": "2026-05-04T15:15:00+00:00",
                "ai_status": "NOT_CALLED_BY_SHADOW_OBSERVER",
                "no_leak_status": "NO_AI_NO_EXECUTION_NO_POST_OUTCOME_FIELDS",
                "promotion_verdict": PROMOTION_VERDICT,
            },
        )
    ]


def _observer_state() -> dict:
    return {
        "eurusd_6e_mso_shadow_v1": {"last_candle_close_utc": "2026-05-04T15:15:00+00:00"},
        "ger40_tier2_mso_shadow_v1": {"last_candle_close_utc": "2026-05-04T19:00:00+00:00"},
    }


def test_normalize_source_registry_classifies_active_control_and_prereg():
    rows = normalize_source_registry(_observer_registry())
    by_id = {row["observer_id"]: row for row in rows}

    assert by_id["eurusd_6e_mso_shadow_v1"]["source_proxy_class"] == "FORWARD_SHADOW"
    assert by_id["uko_usd_cl_context_only_v1"]["source_proxy_class"] == "CONTROL_ONLY"
    assert by_id["spx500_es_prereg_required_v1"]["source_proxy_class"] == "PREREGISTRATION_REQUIRED"


def test_stale_observer_detection_flags_missing_or_old_active_rows():
    registry = normalize_source_registry(_observer_registry())
    stale = stale_observer_detection(
        source_registry=registry,
        latest_status={},
        now_utc=datetime.fromisoformat("2026-05-05T03:00:00+00:00"),
    )

    assert stale["status"] == "ACTION_REQUIRED"
    assert stale["action_required_observer_ids"] == [
        "eurusd_6e_mso_shadow_v1",
        "ger40_tier2_mso_shadow_v1",
    ]


def test_ger40_final_closeout_fixture_is_confirmed():
    registry = normalize_source_registry(_observer_registry())
    closeout = final_closeout_detection(
        source_registry=registry,
        latest_status={
            "ger40_tier2_mso_shadow_v1": {
                "lifecycle_status": "SKIPPED_OUTSIDE_KILL_ZONE",
                "created_at_utc": "2026-05-05T00:03:00+00:00",
            }
        },
        observer_state=_observer_state(),
        agent_config=_agent_config(),
    )

    assert "ger40_tier2_mso_shadow_v1" in closeout["confirmed_observer_ids"]


def test_ger40_historical_final_closeout_survives_new_active_session():
    registry = normalize_source_registry(_observer_registry())
    closeout = final_closeout_detection(
        source_registry=registry,
        latest_status={
            "ger40_tier2_mso_shadow_v1": {
                "lifecycle_status": "EMITTED_STRATEGY_FOLLOW_EVALUATION",
                "created_at_utc": "2026-05-05T08:45:12+00:00",
            }
        },
        observer_state={
            "ger40_tier2_mso_shadow_v1": {"last_candle_close_utc": "2026-05-05T08:45:00+00:00"},
        },
        agent_config=_agent_config(),
        status_rows=[
            (
                1,
                {
                    "observer_id": "ger40_tier2_mso_shadow_v1",
                    "created_at_utc": "2026-05-04T18:59:59+00:00",
                    "decision_time_utc": "2026-05-04T19:00:00+00:00",
                    "lifecycle_status": "EMITTED_STRATEGY_FOLLOW_EVALUATION",
                },
            ),
            (
                2,
                {
                    "observer_id": "ger40_tier2_mso_shadow_v1",
                    "created_at_utc": "2026-05-04T19:00:19+00:00",
                    "decision_time_utc": None,
                    "lifecycle_status": "SKIPPED_OUTSIDE_KILL_ZONE",
                },
            ),
        ],
    )

    by_observer = {row["observer_id"]: row for row in closeout["rows"]}
    assert by_observer["ger40_tier2_mso_shadow_v1"]["closeout_status"] == "HISTORICAL_FINAL_CLOSEOUT_CONFIRMED"
    assert "ger40_tier2_mso_shadow_v1" in closeout["confirmed_observer_ids"]


def test_ger40_closeout_not_required_during_active_session_without_history():
    registry = normalize_source_registry(_observer_registry())
    row = build_status_row(
        observer_registry=_observer_registry(),
        agent_config=_agent_config(),
        observer_state={
            "eurusd_6e_mso_shadow_v1": {"last_candle_close_utc": "2026-05-05T08:45:00+00:00"},
            "ger40_tier2_mso_shadow_v1": {"last_candle_close_utc": "2026-05-05T08:45:00+00:00"},
        },
        status_rows=[
            (
                1,
                {
                    "schema_version": "shadow_observer_status_v1",
                    "observer_id": "eurusd_6e_mso_shadow_v1",
                    "symbol": "EURUSD",
                    "created_at_utc": "2026-05-05T08:45:12+00:00",
                    "lifecycle_status": "EMITTED_STRATEGY_FOLLOW_EVALUATION",
                    "no_ai_calls": True,
                    "no_canary_required": True,
                    "no_execution": True,
                    "promotion_verdict": PROMOTION_VERDICT,
                },
            ),
            (
                2,
                {
                    "schema_version": "shadow_observer_status_v1",
                    "observer_id": "ger40_tier2_mso_shadow_v1",
                    "symbol": "GER40",
                    "created_at_utc": "2026-05-05T08:45:12+00:00",
                    "lifecycle_status": "EMITTED_STRATEGY_FOLLOW_EVALUATION",
                    "no_ai_calls": True,
                    "no_canary_required": True,
                    "no_execution": True,
                    "promotion_verdict": PROMOTION_VERDICT,
                },
            ),
        ],
        strategy_rows=_strategy_rows(),
        generated_at_utc="2026-05-05T08:45:30+00:00",
    )

    by_observer = {item["observer_id"]: item for item in row["final_closeout_detection"]["rows"]}
    assert by_observer["ger40_tier2_mso_shadow_v1"]["closeout_status"] == "FINAL_CLOSEOUT_NOT_DUE_ACTIVE_SESSION"
    assert row["status"] == STATUS_OK


def test_ger40_closeout_required_after_final_session_without_evidence():
    row = build_status_row(
        observer_registry=_observer_registry(),
        agent_config=_agent_config(),
        observer_state={
            "eurusd_6e_mso_shadow_v1": {"last_candle_close_utc": "2026-05-05T15:15:00+00:00"},
            "ger40_tier2_mso_shadow_v1": {"last_candle_close_utc": "2026-05-05T18:45:00+00:00"},
        },
        status_rows=[
            (
                1,
                {
                    "schema_version": "shadow_observer_status_v1",
                    "observer_id": "eurusd_6e_mso_shadow_v1",
                    "symbol": "EURUSD",
                    "created_at_utc": "2026-05-05T15:40:00+00:00",
                    "lifecycle_status": "SKIPPED_OUTSIDE_KILL_ZONE",
                    "no_ai_calls": True,
                    "no_canary_required": True,
                    "no_execution": True,
                    "promotion_verdict": PROMOTION_VERDICT,
                },
            ),
            (
                2,
                {
                    "schema_version": "shadow_observer_status_v1",
                    "observer_id": "ger40_tier2_mso_shadow_v1",
                    "symbol": "GER40",
                    "created_at_utc": "2026-05-05T20:00:00+00:00",
                    "lifecycle_status": "EMITTED_STRATEGY_FOLLOW_EVALUATION",
                    "no_ai_calls": True,
                    "no_canary_required": True,
                    "no_execution": True,
                    "promotion_verdict": PROMOTION_VERDICT,
                },
            ),
        ],
        strategy_rows=_strategy_rows(),
        generated_at_utc="2026-05-05T20:00:30+00:00",
    )

    assert row["status"] == ACTION_REQUIRED
    assert "GER40_EXTENDED_SESSION_CLOSEOUT_NOT_CONFIRMED" in row["action_required_codes"]


def test_status_row_hardens_observer_without_ai_or_execution():
    row = build_status_row(
        observer_registry=_observer_registry(),
        agent_config=_agent_config(),
        observer_state=_observer_state(),
        status_rows=_status_rows(),
        strategy_rows=_strategy_rows(),
        generated_at_utc="2026-05-05T00:05:00+00:00",
    )

    assert row["status"] == STATUS_OK
    assert row["promotion_verdict"] == PROMOTION_VERDICT
    assert row["registry_summary"]["active_entries"] == 2
    assert row["ai_calls"] == 0
    assert row["order_calls"] == 0
    assert row["paid_data_calls"] == 0
    assert row["stale_observer_detection"]["status"] == "OK"
    assert "ger40_tier2_mso_shadow_v1" in row["final_closeout_detection"]["confirmed_observer_ids"]


def test_status_row_flags_forbidden_safety_violation():
    status_rows = _status_rows()
    status_rows[0][1]["no_execution"] = False
    row = build_status_row(
        observer_registry=_observer_registry(),
        agent_config=_agent_config(),
        observer_state=_observer_state(),
        status_rows=status_rows,
        strategy_rows=_strategy_rows(),
        generated_at_utc="2026-05-05T00:05:00+00:00",
    )

    assert row["status"] == ACTION_REQUIRED
    assert "SHADOW_OBSERVER_SAFETY_COUNTER_VIOLATION" in row["action_required_codes"]


def test_report_markdown_documents_no_promotion_boundary():
    payload = build_report_payload(
        observer_registry=_observer_registry(),
        agent_config=_agent_config(),
        observer_state=_observer_state(),
        status_rows=_status_rows(),
        strategy_rows=_strategy_rows(),
        generated_at_utc="2026-05-05T00:05:00+00:00",
    )

    rendered = render_markdown(payload)

    assert "NO_PROMOTION_VERDICT" in rendered
    assert "GER40 closeout confirmed: `True`" in rendered


def test_script_appends_status_and_registry_idempotently(tmp_path, monkeypatch, capsys):
    registry_path = tmp_path / "config" / "shadow_observer_registry.yaml"
    config_path = tmp_path / "config" / "agent_config.yaml"
    state_path = tmp_path / "pipeline_state" / "shadow_observer_state.json"
    observer_status_log = tmp_path / "shadow_logs" / "shadow_observer_status.jsonl"
    strategy_evaluations = tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl"
    hardening_status_log = tmp_path / "shadow_logs" / "shadow_observer_hardening_status.jsonl"
    registry_json = tmp_path / "research" / "program_control" / "registry.json"
    registry_md = tmp_path / "research" / "program_control" / "registry.md"
    output_json = tmp_path / "research" / "program_control" / "report.json"
    output_md = tmp_path / "research" / "program_control" / "report.md"

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(yaml.safe_dump(_observer_registry()), encoding="utf-8")
    config_path.write_text(yaml.safe_dump(_agent_config()), encoding="utf-8")
    _write_json(state_path, _observer_state())
    _write_jsonl(observer_status_log, [row for _, row in _status_rows()])
    _write_jsonl(strategy_evaluations, [row for _, row in _strategy_rows()])

    args = [
        "audit_shadow_observer_hardening.py",
        "--observer-registry",
        str(registry_path),
        "--agent-config",
        str(config_path),
        "--observer-state",
        str(state_path),
        "--observer-status-log",
        str(observer_status_log),
        "--strategy-evaluations",
        str(strategy_evaluations),
        "--status-log",
        str(hardening_status_log),
        "--source-registry-json",
        str(registry_json),
        "--source-registry-md",
        str(registry_md),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    ]
    monkeypatch.setattr(sys, "argv", args)

    assert script.main() == 0
    first = json.loads(capsys.readouterr().out)
    assert first["rows_appended"] == 1

    monkeypatch.setattr(sys, "argv", args)
    assert script.main() == 0
    second = json.loads(capsys.readouterr().out)

    assert second["rows_appended"] == 0
    assert registry_json.exists()
    assert registry_md.exists()
    assert output_json.exists()
    assert output_md.exists()
    assert len(hardening_status_log.read_text(encoding="utf-8").splitlines()) == 1
