from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.broker_truth_cost_capture_v2 import capture_log_path
from src.components.execution import ExecutionEngine
from src.components.orchestrator import apply_runtime_namespace_to_config
from src.utils.broker_profile import (
    assert_mt5_account_matches_profile,
    broker_account_namespace,
    namespaced_daemon_name,
    namespaced_directory_path,
    namespaced_file_path,
    resolve_mt5_portable_mode,
    resolve_mt5_terminal_path,
    sha256_text,
)


def test_broker_namespace_helpers_preserve_legacy_defaults():
    cfg = {"profile_name": "redacted_account"}

    assert broker_account_namespace(cfg) == ""
    assert namespaced_file_path("pipeline_state/state.json", "") == Path("pipeline_state/state.json")
    assert namespaced_directory_path("data/m1", "") == Path("data/m1")
    assert namespaced_daemon_name("m1_capture_all", "") == "m1_capture_all"


def test_broker_namespace_helpers_resolve_profile_namespace():
    cfg = {
        "runtime": {
            "broker_account_namespace": "FTMO Challenge Live #1",
        },
        "mt5": {
            "terminal_path": "C:/Program Files/FTMO/terminal64.exe",
        },
    }

    assert broker_account_namespace(cfg) == "ftmo_challenge_live_1"
    assert namespaced_daemon_name("m1_capture_all", broker_account_namespace(cfg)) == (
        "m1_capture_all_ftmo_challenge_live_1"
    )
    assert str(namespaced_file_path("pipeline_state/m1_capture_state.json", broker_account_namespace(cfg))).endswith(
        "m1_capture_state_ftmo_challenge_live_1.json"
    )
    assert namespaced_directory_path(
        "data/m1",
        broker_account_namespace(cfg),
    ) == Path("data/m1/ftmo_challenge_live_1")
    assert resolve_mt5_terminal_path(cfg) == "C:/Program Files/FTMO/terminal64.exe"
    assert resolve_mt5_portable_mode(cfg) is False


def test_mt5_portable_mode_resolves_from_profile_and_env(monkeypatch):
    cfg = {"mt5": {"portable": True}}

    assert resolve_mt5_portable_mode(cfg) is True
    assert resolve_mt5_portable_mode(cfg, explicit=False) is False

    monkeypatch.setenv("GTOS_MT5_PORTABLE", "0")
    assert resolve_mt5_portable_mode(cfg) is False


def test_execution_engine_namespaces_pending_intent_and_checkpoint(monkeypatch):
    monkeypatch.setattr(ExecutionEngine, "_load_pending_intent", lambda self: None)
    cfg = {
        "runtime": {"broker_account_namespace": "operator_profile"},
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
    }
    engine = ExecutionEngine(mt5=SimpleNamespace(), config=cfg)

    assert engine._pending_intent_path.endswith("pending_intent_XAUUSD_operator_profile.pkl")
    assert engine._checkpoint_path.endswith("execution_checkpoint_operator_profile.json")


def test_orchestrator_stamps_cli_runtime_namespace_into_config():
    cfg = {
        "profile_name": "redacted_account",
        "runtime": {},
    }

    namespace = apply_runtime_namespace_to_config(
        cfg,
        "redacted_account Live BEE34003",
    )

    assert namespace == "redacted_account_live_bee34003"
    assert cfg["runtime"]["broker_account_namespace"] == "redacted_account_live_bee34003"


def test_broker_truth_capture_default_log_path_is_namespaced():
    cfg = {"runtime": {"broker_account_namespace": "operator_profile"}}

    assert capture_log_path(cfg) == Path(
        "shadow_logs/operator_profile/broker_truth_cost_capture_v2.jsonl"
    )


def test_mt5_account_assertion_passes_redacted_identity():
    login = 0
    mt5_module = SimpleNamespace(
        terminal_info=lambda: SimpleNamespace(
            path="C:/Program Files/MetaTrader 5",
            data_path="C:/Users/MSI/AppData/Roaming/MetaQuotes/Terminal/ABC",
        ),
        account_info=lambda: SimpleNamespace(
            login=login,
            server="FTMO-Server3",
            company="FTMO Global Markets Ltd",
            currency="USD",
        ),
    )
    wrapper = SimpleNamespace(_mt5=mt5_module)
    cfg = {
        "broker_profile": {
            "expected_account": {
                "server": "FTMO-Server3",
                "company": "FTMO Global Markets Ltd",
                "currency": "USD",
                "login_sha256": sha256_text(login),
            }
        }
    }

    result = assert_mt5_account_matches_profile(wrapper, cfg)

    assert result["status"] == "passed"
    assert result["actual_redacted"]["login_sha256"] == sha256_text(login)


def test_mt5_account_assertion_rejects_server_mismatch():
    mt5_module = SimpleNamespace(
        terminal_info=lambda: SimpleNamespace(path="C:/MT5", data_path="C:/MT5/data"),
        account_info=lambda: SimpleNamespace(
            login=1,
            server="redacted_account-Server2",
            company="redacted_account",
            currency="USD",
        ),
    )
    wrapper = SimpleNamespace(_mt5=mt5_module)
    cfg = {"broker_profile": {"expected_account": {"server": "FTMO-Server3"}}}

    with pytest.raises(RuntimeError, match="MT5 account/profile mismatch"):
        assert_mt5_account_matches_profile(wrapper, cfg)
