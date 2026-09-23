"""Tests for the VPS active-operator toolkit (operator/operator_toolkit.py).

Covers all eight capabilities (a-g) + the escalation logic. NOTHING here touches a broker; all
ledger writes use an isolated tmp repo root so real pipeline_state files are never written.

Run:
  ROUTE=.../final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
  PYTHONPATH=$REPO:$ROUTE python3 -m pytest $ROUTE/GOLIVE_vps_deploy/tests/test_operator_toolkit.py -q
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_PKG = _HERE.parents[1]                      # GOLIVE_vps_deploy/
sys.path.insert(0, str(_PKG / "operator"))
sys.path.insert(0, str(_PKG / "monitoring"))

import operator_toolkit as OP  # noqa: E402


def _utc(s: str) -> str:
    return s


# --------------------------------------------------------------- (a) health ----
def test_data_freshness_states():
    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    fresh = OP.data_freshness(terminal="FTMO",
                              last_bar_utc=(now - timedelta(seconds=30)).isoformat(),
                              now_utc=now.isoformat())
    assert fresh["state"] == "ok" and fresh["fresh"] is True
    warn = OP.data_freshness(terminal="FTMO",
                             last_bar_utc=(now - timedelta(seconds=300)).isoformat(),
                             now_utc=now.isoformat())
    assert warn["state"] == "warn"
    stale = OP.data_freshness(terminal="FTMO",
                              last_bar_utc=(now - timedelta(seconds=900)).isoformat(),
                              now_utc=now.isoformat())
    assert stale["state"] == "fail_closed"


def test_data_freshness_unparseable_and_future_fail_closed():
    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    bad = OP.data_freshness(terminal="FTMO", last_bar_utc="not-a-time", now_utc=now.isoformat())
    assert bad["state"] == "fail_closed" and bad["reason"] == "unparseable_last_bar_time"
    fut = OP.data_freshness(terminal="FTMO",
                            last_bar_utc=(now + timedelta(seconds=120)).isoformat(),
                            now_utc=now.isoformat())
    assert fut["state"] == "fail_closed" and fut["reason"] == "last_bar_in_future"


def test_health_primary_dead_engages_kill_action(tmp_path):
    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    terms = [OP.TerminalHealth("FTMO", connected=False, last_bar_utc=None, process_alive=False),
             OP.TerminalHealth("redacted_account", connected=True,
                               last_bar_utc=now)]
    rep = OP.health_check(terminals=terms, namespace="h1", now_utc=now, repo_root=tmp_path)
    assert rep["state"] == "fail_closed"
    assert rep["action"] == "fail_closed_primary_engage_kill_switch"


def test_health_follower_stale_skips_follower_only(tmp_path):
    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    terms = [OP.TerminalHealth("FTMO", connected=True, last_bar_utc=(now).isoformat()),
             OP.TerminalHealth("redacted_account", connected=True,
                               last_bar_utc=(now - timedelta(seconds=900)).isoformat())]
    rep = OP.health_check(terminals=terms, namespace="h2", now_utc=now.isoformat(),
                          repo_root=tmp_path)
    assert rep["action"] == "skip_follower_leg"  # follower fault never engages kill


# --------------------------------------------------------- (b) follower parity ----
def test_follower_parity_missing_symbol_skips_leg(tmp_path):
    row = OP.FollowerParityRow("i1", "metals_core", "XAUUSD", None,
                               primary_filled=True, follower_filled=False)
    rec = OP.record_follower_parity(row, namespace="fp1", repo_root=tmp_path)
    assert rec["verdict"] == "skip_follower_leg"
    assert rec["reason"] == "missing_symbol_in_follower_map"
    assert rec["affects_primary"] is False


def test_follower_parity_large_slip_derisks(tmp_path):
    row = OP.FollowerParityRow("i2", "crypto", "BTCUSD", "BTCUSD",
                               primary_filled=True, follower_filled=True,
                               primary_R=0.5, follower_R=0.1)  # slip -0.4R
    rec = OP.record_follower_parity(row, namespace="fp2", repo_root=tmp_path)
    assert rec["verdict"] == "derisk_follower_leg"
    assert rec["slip_R"] == pytest.approx(-0.4)


def test_follower_parity_in_band_is_ok(tmp_path):
    row = OP.FollowerParityRow("i3", "metals_core", "XAUUSD", "XAUUSD",
                               primary_filled=True, follower_filled=True,
                               primary_R=0.5, follower_R=0.47)
    rec = OP.record_follower_parity(row, namespace="fp3", repo_root=tmp_path)
    assert rec["verdict"] == "ok"
    s = OP.follower_parity_summary(namespace="fp3", repo_root=tmp_path)
    assert s["n_ok"] == 1 and s["verdict"] == "ok"


def test_follower_summary_counts_skips_and_derisks(tmp_path):
    ns = "fp4"
    OP.record_follower_parity(OP.FollowerParityRow("a", "s", "X", None, True, False),
                              namespace=ns, repo_root=tmp_path)
    OP.record_follower_parity(OP.FollowerParityRow("b", "s", "X", "X", True, True,
                                                   primary_R=0.5, follower_R=0.05),
                              namespace=ns, repo_root=tmp_path)
    s = OP.follower_parity_summary(namespace=ns, repo_root=tmp_path)
    assert s["n_skip_leg"] == 1 and s["n_derisk"] == 1 and s["verdict"] == "derisk"


# --------------------------------------------------------------- (c) null guard ----
def test_null_guard_admits_complete_candidate(tmp_path):
    cand = {"intent_id": "c1", "vol_gate": True, "ac60": 0.2, "conf_score": 0.8}
    r = OP.null_guard_candidate(candidate=cand, required_gates=["vol_gate"],
                                required_features=["ac60"], required_scores=["conf_score"],
                                namespace="ng1", repo_root=tmp_path)
    assert r["admit"] is True and r["n_nulls"] == 0


def test_null_guard_fails_closed_on_null_with_rootcause(tmp_path):
    cand = {"intent_id": "c2", "vol_gate": None, "ac60": float("nan"), "conf_score": 0.8}
    r = OP.null_guard_candidate(candidate=cand, required_gates=["vol_gate"],
                                required_features=["ac60", "slope30"], required_scores=["conf_score"],
                                field_sources={"vol_gate": "vol_gate_producer",
                                               "ac60": "persistence_feature",
                                               "slope30": "trend_feature"},
                                namespace="ng2", repo_root=tmp_path)
    assert r["admit"] is False
    fields = {n["field"]: n for n in r["nulls"]}
    assert fields["vol_gate"]["issue"] == "null_or_nan"
    assert fields["ac60"]["issue"] == "null_or_nan"
    assert fields["slope30"]["issue"] == "absent"
    assert fields["slope30"]["expected_source"] == "trend_feature"


def test_null_guard_batch_rootcause_rollup(tmp_path):
    cands = [
        {"intent_id": "ok", "g": True, "f": 1.0, "s": 0.5},
        {"intent_id": "bad1", "g": None, "f": 1.0, "s": 0.5},
        {"intent_id": "bad2", "g": True, "f": None, "s": 0.5},
    ]
    out = OP.null_guard_batch(candidates=cands, required_gates=["g"], required_features=["f"],
                              required_scores=["s"],
                              field_sources={"g": "gate_src", "f": "feat_src"},
                              namespace="ng3", repo_root=tmp_path)
    assert out["n_admitted"] == 1 and out["n_rejected"] == 2
    assert out["null_source_rootcause"] == {"gate_src": 1, "feat_src": 1}


# --------------------------------------------------------------- (d) chronology ----
def test_terminal_offset_within_and_beyond_tolerance():
    ref = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    ok = OP.verify_terminal_offset(terminal="FTMO",
                                   server_time_utc=(ref + timedelta(seconds=2)).isoformat(),
                                   reference_utc=ref.isoformat())
    assert ok["ok"] is True
    bad = OP.verify_terminal_offset(terminal="redacted_account",
                                    server_time_utc=(ref + timedelta(seconds=3600)).isoformat(),
                                    reference_utc=ref.isoformat())
    assert bad["ok"] is False and "normalize_to_utc" in bad["reason"]


def test_bar_order_detects_out_of_order_and_dupes():
    asc = [{"time": "2026-06-15T12:00:00Z"}, {"time": "2026-06-15T12:15:00Z"},
           {"time": "2026-06-15T12:30:00Z"}]
    assert OP.verify_bar_order(asc)["ok"] is True
    ooo = [{"time": "2026-06-15T12:30:00Z"}, {"time": "2026-06-15T12:00:00Z"}]
    r = OP.verify_bar_order(ooo)
    assert r["ok"] is False and r["fault_index"] == 1 and r["reason"] == "out_of_order_bar_time"
    dup = [{"time": "2026-06-15T12:00:00Z"}, {"time": "2026-06-15T12:00:00Z"}]
    assert OP.verify_bar_order(dup)["reason"] == "duplicate_bar_time"
    nul = [{"time": None}]
    assert OP.verify_bar_order(nul)["ok"] is False


def test_sequence_order_detects_inversion():
    good = OP.verify_sequence_order(["features", "gates", "score", "size"],
                                    ["features", "gates", "score", "size"])
    assert good["ok"] is True
    bad = OP.verify_sequence_order(["score", "features"],
                                   ["features", "gates", "score", "size"])
    assert bad["ok"] is False and bad["reason"] == "out_of_order_step"


def test_chronology_check_fail_closed(tmp_path):
    ref = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    rep = OP.chronology_check(
        terminals=[{"terminal": "FTMO", "server_time_utc": ref},
                   {"terminal": "redacted_account", "server_time_utc": "2026-06-15T16:00:00Z"}],
        reference_utc=ref,
        primary_bars=[{"time": "2026-06-15T12:00:00Z"}],
        compute_steps=["features", "gates", "score", "size"],
        namespace="ch1", repo_root=tmp_path)
    assert rep["ok"] is False
    assert rep["action"] == "fail_closed_do_not_size"


# --------------------------------------------------------------- (e) artifacts ----
def test_check_artifacts_all_present(tmp_path):
    f = tmp_path / "data" / "stream.pkl"
    f.parent.mkdir(parents=True)
    f.write_bytes(b"real-binary-content")
    out = OP.check_artifacts(required_files=["data/stream.pkl"],
                             required_config_keys=["gtos_vnext_runtime.ultimate_book_enabled"],
                             config={"gtos_vnext_runtime": {"ultimate_book_enabled": False}},
                             namespace="art1", repo_root=tmp_path)
    assert out["ok"] is True


def test_check_artifacts_detects_lfs_pointer_and_missing(tmp_path):
    ptr = tmp_path / "lfs.pkl"
    ptr.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:abc\n")
    out = OP.check_artifacts(required_files=["lfs.pkl", "gone.pkl"],
                             required_config_keys=["gtos_vnext_runtime.missing_key"],
                             config={"gtos_vnext_runtime": {"ultimate_book_enabled": False}},
                             namespace="art2", repo_root=tmp_path)
    assert out["ok"] is False
    assert "lfs.pkl" in out["lfs_pointer_files"]
    assert "gone.pkl" in out["missing_files"]
    assert "gtos_vnext_runtime.missing_key" in out["missing_config_keys"]
    assert any("git lfs pull" in r for r in out["recommended_repair"])


# --------------------------------------------------------------- (f) live miner ----
def test_record_live_trade_matches_miner_schema(tmp_path):
    OP.record_live_trade(intent_id="t1", sleeve="metals_core", symbol="XAUUSD", year=2026,
                         direction=1, realized_R=0.85,
                         features={"ac60": 0.2, "vr": 1.4}, namespace="lm1", repo_root=tmp_path)
    p = OP.live_trade_ledger_path(namespace="lm1", repo_root=tmp_path)
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    assert rows[0]["R"] == 0.85 and rows[0]["year"] == 2026
    assert rows[0]["ac60"] == 0.2 and rows[0]["source"] == "live"


def test_live_miner_readiness_floor(tmp_path):
    ns = "lm2"
    for i in range(8):
        OP.record_live_trade(intent_id=f"t{i}", sleeve="crypto", symbol="BTCUSD", year=2026,
                             direction=1, realized_R=0.2, namespace=ns, repo_root=tmp_path)
    OP.record_live_trade(intent_id="x", sleeve="energy_agri", symbol="USOIL_cash", year=2026,
                         direction=1, realized_R=0.1, namespace=ns, repo_root=tmp_path)
    rd = OP.live_miner_readiness(namespace=ns, repo_root=tmp_path)
    assert rd["n_live_trades"] == 9
    assert "crypto" in rd["sleeves_ready_to_mine"]
    assert "energy_agri" not in rd["sleeves_ready_to_mine"]
    assert rd["any_ready"] is True


# --------------------------------------------------------------- (g) escalation ----
def test_classify_escalation_primary_fault_engages_and_escalates():
    esc = OP.classify_escalation(reports={
        "health": {"action": "fail_closed_primary_engage_kill_switch", "state": "fail_closed"}})
    assert esc["engage_kill_switch"] is True and esc["escalate_to_owner"] is True
    assert esc["severity"] == "critical"


def test_classify_escalation_follower_only_no_kill():
    esc = OP.classify_escalation(reports={
        "health": {"action": "skip_follower_leg", "state": "fail_closed"},
        "follower_parity": {"verdict": "derisk"}})
    assert esc["engage_kill_switch"] is False
    assert "skip_follower_leg" in esc["auto_actions"]


def test_classify_escalation_dd_breach_engages():
    esc = OP.classify_escalation(reports={"daily_dd": {"state": "breach"}})
    assert esc["engage_kill_switch"] is True and "dd_breach" in esc["causes"]


def test_classify_escalation_live_replay_breach_escalates_but_no_kill():
    esc = OP.classify_escalation(reports={"live_replay": {"verdict": "derisk"}})
    assert esc["escalate_to_owner"] is True and esc["engage_kill_switch"] is False
    assert "reduce_size_cap" in esc["auto_actions"]


def test_operator_cycle_recommends_kill_but_does_not_engage_by_default(tmp_path):
    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    terms = [OP.TerminalHealth("FTMO", connected=False, last_bar_utc=None, process_alive=False),
             OP.TerminalHealth("redacted_account", connected=True, last_bar_utc=now)]
    cyc = OP.operator_cycle(terminals=terms, reference_utc=now, namespace="cyc1",
                            repo_root=tmp_path)
    assert cyc["escalation"]["engage_kill_switch"] is True
    # default-off: does NOT pull the switch
    assert cyc["kill_switch"]["status"] == "recommended_not_engaged"
    assert not (tmp_path / "pipeline_state" / "GTOS_HARD_PRODUCTION_HALT.flag").exists()


def test_operator_cycle_engages_when_opted_in(tmp_path):
    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    terms = [OP.TerminalHealth("FTMO", connected=False, last_bar_utc=None, process_alive=False),
             OP.TerminalHealth("redacted_account", connected=True, last_bar_utc=now)]
    cyc = OP.operator_cycle(terminals=terms, reference_utc=now, namespace="cyc2",
                            engage_on_critical=True, repo_root=tmp_path)
    assert cyc["kill_switch"]["status"] == "kill_switch_engaged"
    assert (tmp_path / "pipeline_state" / "GTOS_HARD_PRODUCTION_HALT.flag").exists()


def test_describe_toolkit_is_broker_free():
    d = OP.describe_toolkit()
    assert d["safety"]["no_broker"] is True
    assert d["safety"]["follower_never_touches_primary"] is True
    assert d["safety"]["engage_kill_switch_default"] is False
    assert set("abcdefg") <= {k[0] for k in d["capabilities"]}


def test_module_import_is_broker_free():
    assert "nmetatrader5" not in sys.modules
    assert "MetaTrader5" not in sys.modules


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
