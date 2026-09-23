"""GOLIVE_vps — tests for the VPS deployment scaffolding.

Covers the kill-switch (halt file + size_cap=0), the monitoring (parity ledger,
daily-DD watch, alert routing), and the bridge adapter (default-off, fail-closed,
gate enforcement). NONE of these touch a broker; the kill-switch/monitor tests use
an isolated tmp repo root so the real pipeline_state flags are never written.

Run:
  ROUTE=.../final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
  python3 -m pytest $ROUTE/GOLIVE_vps_deploy/tests -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_PKG = _HERE.parents[1]                     # GOLIVE_vps_deploy/
sys.path.insert(0, str(_PKG / "monitoring"))
sys.path.insert(0, str(_PKG / "adapters"))

import kill_switch as K          # noqa: E402
import monitor as M              # noqa: E402
import bridge_adapter as B       # noqa: E402


# ----------------------------------------------------------------- kill-switch ----
def test_kill_switch_default_state_is_clear(tmp_path):
    st = K.kill_switch_state(repo_root=tmp_path)
    assert st["kill_switch_engaged"] is False
    assert st["new_entries_allowed"] is True
    assert st["size_cap_override"] == 1.0


def test_engage_writes_halt_flag_and_size_cap_zero(tmp_path):
    res = K.engage_kill_switch(reason="unit test", repo_root=tmp_path)
    assert res["status"] == "kill_switch_engaged"
    assert res["size_cap_override"] == 0.0
    assert (tmp_path / K.HARD_HALT_FLAG).exists()
    assert (tmp_path / K.SIZE_CAP_SIDECAR).exists()
    st = K.kill_switch_state(repo_root=tmp_path)
    assert st["kill_switch_engaged"] is True
    assert st["new_entries_allowed"] is False
    assert st["size_cap_override"] == 0.0
    assert K.load_size_cap_override(repo_root=tmp_path) == 0.0


def test_disengage_requires_token_and_does_not_remove_halt_flag(tmp_path):
    K.engage_kill_switch(reason="x", repo_root=tmp_path)
    with pytest.raises(PermissionError):
        K.disengage_kill_switch(approval_token="", repo_root=tmp_path)
    with pytest.raises(PermissionError):
        K.disengage_kill_switch(approval_token="PLACEHOLDER", repo_root=tmp_path)
    out = K.disengage_kill_switch(approval_token="REAL-OWNER-TOKEN", repo_root=tmp_path)
    assert out["size_cap_override"] == 1.0
    # the HARD halt flag must remain (never auto-cleared by a script)
    assert (tmp_path / K.HARD_HALT_FLAG).exists()
    assert out["hard_halt_flag_still_present"] is True


def test_unreadable_sidecar_fails_closed(tmp_path):
    # a corrupt sidecar must read as fully engaged (fail-closed)
    p = tmp_path / K.SIZE_CAP_SIDECAR
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{ not json", encoding="utf-8")
    st = K.kill_switch_state(repo_root=tmp_path)
    assert st["kill_switch_engaged"] is True
    assert st["size_cap_override"] == 0.0


def test_kill_audit_log_is_appended(tmp_path):
    K.engage_kill_switch(reason="audit", repo_root=tmp_path)
    log = tmp_path / K.KILL_AUDIT_LOG
    assert log.exists()
    assert "engage" in log.read_text(encoding="utf-8")


# ----------------------------------------------------------------- monitoring ----
def test_parity_ledger_records_and_summarizes_drift(tmp_path):
    ns = "acct_a"
    # below the warn band
    for i in range(M.PARITY_MIN_FILLS):
        M.record_parity(M.ParityRow(f"id{i}", "metals_core", "XAUUSD",
                                    live_R=0.50, replay_R=0.45),
                        namespace=ns, repo_root=tmp_path)
    s = M.parity_summary(namespace=ns, repo_root=tmp_path)
    assert s["n_fills"] == M.PARITY_MIN_FILLS
    assert s["verdict"] == "ok"  # mean abs drift 0.05 < warn 0.15


def test_parity_derisk_verdict_on_large_drift(tmp_path):
    ns = "acct_b"
    for i in range(M.PARITY_MIN_FILLS):
        M.record_parity(M.ParityRow(f"id{i}", "crypto", "BTCUSD",
                                    live_R=0.00, replay_R=0.50),  # 0.50 drift
                        namespace=ns, repo_root=tmp_path)
    s = M.parity_summary(namespace=ns, repo_root=tmp_path)
    assert s["verdict"] == "derisk"


def test_parity_insufficient_fills_is_not_actionable(tmp_path):
    M.record_parity(M.ParityRow("only1", "metals_core", "XAUUSD", 0.0, 1.0),
                    namespace="thin", repo_root=tmp_path)
    s = M.parity_summary(namespace="thin", repo_root=tmp_path)
    assert s["verdict"] == "insufficient_fills"


def test_daily_dd_watch_states(tmp_path):
    ok = M.daily_dd_watch(equity=100000, day_start_balance=100000, high_water=100000,
                          namespace="d", repo_root=tmp_path)
    assert ok["state"] == "ok"
    derisk = M.daily_dd_watch(equity=96500, day_start_balance=100000, high_water=100000,
                              namespace="d", repo_root=tmp_path)  # -3.5% daily
    assert derisk["state"] == "derisk"
    breach = M.daily_dd_watch(equity=94000, day_start_balance=100000, high_water=100000,
                              namespace="d", repo_root=tmp_path)  # -6% daily
    assert breach["state"] == "breach"


def test_governor_check_fail_closed_without_wiring():
    out = M.governor_check(state=object())
    assert out["allow_new_entries"] is False


def test_run_monitor_cycle_routes_breach_to_kill_switch(tmp_path):
    captured = []
    rep = M.run_monitor_cycle(equity=94000, day_start_balance=100000, high_water=100000,
                              namespace="c", repo_root=tmp_path,
                              sink=lambda a, **kw: captured.append(a))
    assert rep["daily_dd"]["state"] == "breach"
    assert rep["action"] == "engage_kill_switch"
    assert any(a["severity"] == "critical" for a in captured)


def test_alert_default_sink_appends_jsonl(tmp_path):
    M.send_alert("t", severity="warn", namespace="al", repo_root=tmp_path)
    log = tmp_path / M.ALERT_LEDGER.format(ns="al")
    assert log.exists() and "t" in log.read_text(encoding="utf-8")


# ----------------------------------------------------------------- bridge adapter ----
def test_default_factory_returns_null_adapter():
    a = B.make_bridge_adapter()
    assert isinstance(a, B.NullBridgeAdapter)
    assert a.connect() is False
    assert a.is_connected() is False


def test_null_adapter_order_send_is_fail_closed():
    a = B.make_bridge_adapter()
    r = a.order_send({"symbol": "XAUUSD"})
    assert r.success is False
    assert "fail_closed" in r.comment


def test_bridge_config_never_stores_creds_only_env_names():
    cfg = B.BridgeConfig()
    # creds default to absent (env not set in test)
    present = cfg.credentials_present()
    assert present == {"login": False, "password": False, "server": False}
    assert cfg.live_connect_allowed is False


def test_silicon_adapter_refuses_connect_until_all_gates_pass():
    cfg = B.BridgeConfig(live_connect_allowed=True)
    # gates deny by default -> BridgeGateError, no import of nmetatrader5 attempted
    a = B.SiliconBridgeAdapter(cfg, gate_ok=lambda: False, halt_clear=lambda: True)
    with pytest.raises(B.BridgeGateError):
        a.connect()
    # halt active -> still refused
    a2 = B.SiliconBridgeAdapter(cfg, gate_ok=lambda: True, halt_clear=lambda: False)
    with pytest.raises(B.BridgeGateError):
        a2.connect()
    # gates ok but creds missing -> refused before any socket
    a3 = B.SiliconBridgeAdapter(cfg, gate_ok=lambda: True, halt_clear=lambda: True)
    with pytest.raises(B.BridgeGateError):
        a3.connect()


def test_factory_returns_silicon_only_when_opted_in():
    cfg = B.BridgeConfig(live_connect_allowed=True)
    a = B.make_bridge_adapter(cfg, gate_ok=lambda: True, halt_clear=lambda: True)
    assert isinstance(a, B.SiliconBridgeAdapter)
    assert a.is_connected() is False  # opt-in != connected


def test_module_import_is_side_effect_free():
    # importing the adapter must not connect / require nmetatrader5
    assert "nmetatrader5" not in sys.modules


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
