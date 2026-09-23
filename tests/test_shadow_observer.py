from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.research_infra import shadow_observer as so


def make_workdir() -> Path:
    root = Path("_manual_forward_shadow_validation_assert") / "test_shadow_observer"
    root.mkdir(parents=True, exist_ok=True)
    workdir = root / uuid.uuid4().hex
    workdir.mkdir(parents=True, exist_ok=False)
    return workdir


class FakeMT5:
    def __init__(self):
        self._mt5 = None


class FakeMso:
    timestamp_utc = "2026-05-04T07:15:00+00:00"
    timeframes = {}


def write_registry(path: Path, *, enabled: bool = True) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "shadow_observer_registry_v1",
                "defaults": {
                    "output_path": "unused_strategy.jsonl",
                    "status_path": "unused_status.jsonl",
                    "state_path": "unused_state.json",
                },
                "instruments": [
                    {
                        "observer_id": "eurusd_test_shadow_v1",
                        "enabled": enabled,
                        "activation_state": "ACTIVE_MSO_SHADOW",
                        "symbol": "EURUSD",
                        "broker_symbol": "EURUSD",
                        "config_symbol": "EURUSD",
                        "family": "EURUSD/6E",
                        "evidence_class": "FORWARD_SHADOW",
                        "source_status": "LABEL_STATUS_ONLY_NO_REGISTERED_OUTCOME_COHORT",
                        "pre_registered_question_id": "TEST-EURUSD",
                        "allowed_rows": ["strategy_follow_evaluation_v1"],
                        "forbidden": [
                            "ai_api_call",
                            "canary_call",
                            "order_send",
                            "execution_engine",
                            "permission_gate",
                            "outcome_opening",
                        ],
                    },
                    {
                        "observer_id": "spx_prereg_v1",
                        "enabled": False,
                        "activation_state": "PRE_REGISTRATION_REQUIRED",
                        "symbol": "SPX500",
                        "broker_symbol": "SPX500",
                        "config_symbol": None,
                        "family": "ES/MES",
                        "evidence_class": "FORWARD_SHADOW",
                        "source_status": "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT",
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_registry_validation_requires_no_ai_no_execution_contract():
    tmp_path = make_workdir()
    registry_path = tmp_path / "registry.yaml"
    write_registry(registry_path)

    registry = so.load_registry(registry_path)

    assert so.validate_registry(registry) == []
    assert [entry.symbol for entry in registry.active_entries] == ["EURUSD"]
    active = registry.active_entries[0]
    assert "ai_api_call" in active.forbidden
    assert "order_send" in active.forbidden
    assert active.pre_registered_question_id == "TEST-EURUSD"


def test_duplicate_candle_is_not_reemitted(monkeypatch):
    tmp_path = make_workdir()
    registry_path = tmp_path / "registry.yaml"
    config_path = tmp_path / "agent_config.yaml"
    output_path = tmp_path / "strategy.jsonl"
    status_path = tmp_path / "status.jsonl"
    state_path = tmp_path / "state.json"
    write_registry(registry_path)
    config_path.write_text(
        yaml.safe_dump(
            {
                "market": {"symbol": "XAUUSD", "kill_zones": {}},
                "instruments": {
                    "EURUSD": {
                        "market": {
                            "symbol": "EURUSD",
                            "kill_zones": {
                                "london": {
                                    "start_utc": "07:00",
                                    "end_utc": "12:00",
                                }
                            },
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        so,
        "ingest_live_data",
        lambda mt5, cfg: {"candle_close_utc": "2026-05-04T07:15:00+00:00"},
    )
    monkeypatch.setattr(so, "compute_market_state", lambda raw, cfg: FakeMso())
    registry = so.load_registry(registry_path)

    kwargs = dict(
        registry=registry,
        mt5=FakeMT5(),
        base_config_path=config_path,
        output_path=output_path,
        status_path=status_path,
        state_path=state_path,
        now=datetime(2026, 5, 4, 7, 16, tzinfo=timezone.utc),
    )
    first = so.observe_cycle(**kwargs)
    second = so.observe_cycle(**kwargs)

    assert first["emitted"] == 1
    assert second["emitted"] == 0
    assert len(output_path.read_text(encoding="utf-8").splitlines()) == 1
    assert "SKIPPED_DUPLICATE_CANDLE" in status_path.read_text(encoding="utf-8")


def test_repeated_outside_kill_zone_status_is_throttled():
    tmp_path = make_workdir()
    registry_path = tmp_path / "registry.yaml"
    config_path = tmp_path / "agent_config.yaml"
    status_path = tmp_path / "status.jsonl"
    state_path = tmp_path / "state.json"
    write_registry(registry_path)
    config_path.write_text(
        yaml.safe_dump(
            {
                "market": {"symbol": "XAUUSD", "kill_zones": {}},
                "instruments": {
                    "EURUSD": {
                        "market": {
                            "symbol": "EURUSD",
                            "kill_zones": {
                                "london": {
                                    "start_utc": "07:00",
                                    "end_utc": "12:00",
                                }
                            },
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    kwargs = dict(
        registry=so.load_registry(registry_path),
        mt5=FakeMT5(),
        base_config_path=config_path,
        status_path=status_path,
        state_path=state_path,
        now=datetime(2026, 5, 4, 5, 16, tzinfo=timezone.utc),
    )
    first = so.observe_cycle(**kwargs)
    second = so.observe_cycle(**kwargs)

    assert first["emitted"] == 0
    assert second["emitted"] == 0
    lines = status_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["lifecycle_status"] == "SKIPPED_OUTSIDE_KILL_ZONE"


def test_shadow_observer_module_does_not_import_ai_permissions_or_execution():
    source = Path("src/research_infra/shadow_observer.py").read_text(encoding="utf-8")
    forbidden_substrings = [
        "primary_analyzer",
        "ExecutionEngine",
        "check_permissions",
        "order_send(",
        "canary_test",
    ]
    for forbidden in forbidden_substrings:
        assert forbidden not in source
