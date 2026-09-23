from __future__ import annotations

import json

from scripts.run_shadow_observer import write_connect_failure_statuses
from src.research_infra.shadow_observer import ACTIVE_MSO_SHADOW, ShadowObserverEntry, ShadowObserverRegistry


def test_connect_failure_writes_fresh_status_rows(tmp_path):
    registry = ShadowObserverRegistry(
        schema_version="shadow_observer_registry_v1",
        defaults={"status_path": str(tmp_path / "shadow_observer_status.jsonl")},
        instruments=(
            ShadowObserverEntry(
                observer_id="eurusd_shadow",
                symbol="EURUSD",
                broker_symbol="EURUSD",
                config_symbol="EURUSD",
                activation_state=ACTIVE_MSO_SHADOW,
                enabled=True,
                family="EURUSD/6E",
                evidence_class="MSO_SHADOW",
                source_status="SOURCE_REGISTERED",
                pre_registered_question_id="fixture",
                allowed_rows=("strategy_follow_evaluation_v1",),
                forbidden=("ai_api_call", "canary_call", "order_send", "execution_engine", "permission_gate", "outcome_opening"),
            ),
        ),
    )

    result = write_connect_failure_statuses(
        registry=registry,
        symbols=[],
        status_path=None,
        state_path=None,
        observer_run_id="test_run",
    )

    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_observer_status.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert result["status"] == "BLOCKED_MT5_CONNECT_FAILED_STATUS_RECORDED"
    assert result["checked"] == 1
    assert rows[0]["lifecycle_status"] == "BLOCKED_MT5_CONNECT_FAILED"
    assert rows[0]["observer_run_id"] == "test_run"
    assert rows[0]["no_execution"] is True
