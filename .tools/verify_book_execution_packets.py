"""Adversarial [RAN] verification of build_book_trade_params against the LIVE FTMO-merged config.

Loads config exactly as orchestrator._load_config does (execution.py merge order verified):
  raw = yaml.safe_load(config/agent_config.yaml)
  config = apply_profile_overrides(raw, "operator_profile")
  config = apply_instrument_overrides(config, SYMBOL)

Builds trade_params from a REAL SizedUnit + TradeIntent + geometry + synthetic live account_state,
then runs the THREE live fail-closed gates the runtime calls in ExecutionEngine.open_trade:
  GATE1 self._vnext_dynamic_policy_support_error(trade_params)        -> must be None
  GATE2 evaluate_execution_manager_v4(...)                            -> action=allow, 0 fatal
  GATE3 self._resolve_vnext_production_risk_pct(...)                  -> (risk, None)
Plus adversarial controls (identity_resolved trap, family ablations, headroom insufficiency/stale).
"""
from __future__ import annotations

import copy
import json
import sys
from types import SimpleNamespace

import yaml

from src.utils.config import apply_profile_overrides, apply_instrument_overrides
from src.components.execution import ExecutionEngine
from src.components.execution_manager_v4 import evaluate_execution_manager_v4
from src.components.ultimate_book.admission import SizedUnit, TradeIntent
from src.components.ultimate_book.execution_packets import (
    build_book_trade_params,
    build_prop_firm_headroom_snapshot,
)

SYMBOL = "XAUUSD"

with open("config/agent_config.yaml", encoding="utf-8") as f:
    raw = yaml.safe_load(f)
config = apply_profile_overrides(raw, "operator_profile")
config = apply_instrument_overrides(config, SYMBOL)

# Real ExecutionEngine on the live-merged config; mt5 is a stub (the 3 gate methods never touch it).
engine = ExecutionEngine(mt5=SimpleNamespace(), config=config)

# ---- sample inputs ---------------------------------------------------------------------------
# A real W7 SizedUnit (metals cluster, momentum sleeve). risk_pct_per_trade is a FRACTION.
unit = SizedUnit(
    cluster="metals",
    sleeve_members=("metals_core",),
    n_trades=1,
    confidence=0.6,
    risk_pct_per_trade=0.005,   # FRACTION -> 0.5% per trade
    unit_risk_pct=0.005,
    sized=True,
    reason="sized",
)
intent = TradeIntent(
    sleeve="metals_core",
    symbol=SYMBOL,
    direction=+1,               # LONG
    decision_day="2026-06-15",
    stop_dist=10.0,             # PRICE risk distance
)
geometry = {"entry_price": 3000.0}   # SL/TP/risk_distance derived from intent + momentum R

account_state = {
    "schema_version": "prop_firm_headroom_account_state_v4",
    "account_login": "310fcf06",
    "current_equity": 100000.0,
    "balance": 100000.0,
    "day_start_equity_or_balance_baseline": 100000.0,
    "daily_reset_window_id": "2026-06-15/operator_profile",
}

tp = build_book_trade_params(
    unit, intent, geometry, account_state, profile_namespace="operator_profile"
)

# A separate, PASSED pretrade cost model — the order router builds this from a live tick (emv4 arg).
cost_model = {
    "status": "PASSED",
    "spread_r": 0.02,
    "max_spread_r": 0.20,
    "commission_model_status": "PASSED",
    "refusal_reason": None,
}


def run_emv4(trade_params, cost=cost_model):
    return evaluate_execution_manager_v4(
        config=config,
        trade_params=trade_params,
        symbol=SYMBOL,
        broker_symbol=SYMBOL,
        pretrade_cost_model=cost,
        pending=None,
        trigger=None,
    )


# ================= GATE 1 =================
g1 = engine._vnext_dynamic_policy_support_error(tp)

# ================= GATE 2 =================
d = run_emv4(copy.deepcopy(tp))

# ================= GATE 3 =================
g3_risk, g3_err = engine._resolve_vnext_production_risk_pct(
    tp, risk_pct_override=tp["risk_pct_override"]
)

geom = tp["gtos_vnext_dynamic_target_stop_geometry_v4"]
geom_missing = (geom.get("source_completeness") or {}).get("missing_source_fields")
hr = tp["gtos_vnext_prop_firm_headroom_snapshot_v4"]

print("risk_pct (=risk_pct_per_trade*100):", tp["risk_pct_override"])
print("direction / entry / sl / tp1       :",
      tp["direction"], tp["entry_price"], tp["stop_loss"], tp["take_profit_1"])
print("GATE1 support_err (_vnext_dynamic_policy_support_error)  :", g1)
print("GATE2 emv4 action/should_block/fatal (evaluate_execution_manager_v4):",
      d.action, d.should_block, "(" + ",".join(d.fatal_reasons) + ")")
print("GATE3 resolved_risk/err (_resolve_vnext_production_risk_pct)        :", g3_risk, g3_err)
print("headroom max_allowed_new_trade_risk:", hr.get("max_allowed_new_trade_risk_pct"),
      "  source_status:", hr.get("source_status"))
print("geometry status:", geom.get("status"), "  missing_source_fields:", geom_missing)
all_clear = (g1 is None) and (d.action == "allow") and (not d.fatal_reasons) and (g3_err is None)
print("ALL THREE GATES CLEAR:", all_clear, "  N_KEYS:", len(tp))

# ================= ADVERSARIAL CONTROLS =================
print("\n----- adversarial controls -----")

# (a) identity_resolved trap: clears emv4 (Gate2) but FAILS Gate3.
trap = copy.deepcopy(tp)
trap["gtos_vnext_selected_cell_risk_policy_identity_status"] = "identity_resolved"
dt = run_emv4(copy.deepcopy(trap))
_, trap_err = engine._resolve_vnext_production_risk_pct(
    trap, risk_pct_override=trap["risk_pct_override"]
)
print("identity_resolved -> emv4 fatal:", len(dt.fatal_reasons),
      "| Gate3 err:", trap_err)

# (b) family ablations: each load-bearing family must re-introduce emv4 fatals.
for key in [
    "gtos_vnext_dynamic_policy_applied",
    "gtos_vnext_selected_cell_risk_cell_id",
    "gtos_vnext_scheduler_v4_packet",
    "gtos_vnext_dynamic_target_stop_geometry_v4",
    "gtos_vnext_prop_firm_headroom_snapshot_v4",
    "gtos_vnext_same_symbol_lifecycle_v4_packet",
    "gtos_vnext_source_event_hash",
    "gtos_vnext_execution_policy_id",
]:
    ab = copy.deepcopy(tp)
    ab.pop(key, None)
    dd = run_emv4(ab)
    print(f"  drop {key:48s} -> action={dd.action} n_fatal={len(dd.fatal_reasons)}")

# (c) cost model not PASSED -> Gate2 fatal.
dc = run_emv4(copy.deepcopy(tp), cost=None)
print("  cost=None ->", dc.action, "n_fatal=", len(dc.fatal_reasons),
      "has_cost_fatal:", any("cost" in r for r in dc.fatal_reasons))

# (d) headroom insufficiency: request 99% risk -> emv4 fatal.
big = copy.deepcopy(tp)
big["gtos_vnext_selected_cell_risk_pct"] = 99.0
db = run_emv4(big)
print("  risk_pct=99 -> headroom fatal present:",
      any("headroom" in r for r in db.fatal_reasons),
      [r for r in db.fatal_reasons if "headroom" in r])

# (e) symbol independence: BTCUSD SHORT.
cfg_btc = apply_instrument_overrides(
    apply_profile_overrides(copy.deepcopy(raw), "operator_profile"), "BTCUSD"
)
eng_btc = ExecutionEngine(mt5=SimpleNamespace(), config=cfg_btc)
unit_btc = SizedUnit("crypto", ("btc_core",), 1, 0.5, 0.0025, 0.0025, True, "sized")
intent_btc = TradeIntent("btc_core", "BTCUSD", -1, "2026-06-15", stop_dist=1500.0)
tp_btc = build_book_trade_params(
    unit_btc, intent_btc, {"entry_price": 60000.0}, account_state,
    profile_namespace="operator_profile",
)
g1b = eng_btc._vnext_dynamic_policy_support_error(tp_btc)
db2 = evaluate_execution_manager_v4(
    config=cfg_btc, trade_params=copy.deepcopy(tp_btc), symbol="BTCUSD",
    broker_symbol="BTCUSD", pretrade_cost_model=cost_model, pending=None, trigger=None,
)
_, g3b = eng_btc._resolve_vnext_production_risk_pct(
    tp_btc, risk_pct_override=tp_btc["risk_pct_override"]
)
print("  BTCUSD SHORT sl/tp1:", tp_btc["stop_loss"], tp_btc["take_profit_1"],
      "| G1:", g1b, "G2:", db2.action, len(db2.fatal_reasons), "G3:", g3b)

if not all_clear:
    print("\n>>> NOT ALL CLEAR — remaining fatal_reasons:", list(d.fatal_reasons))
    sys.exit(1)
print("\n>>> CONFIRMED: build_book_trade_params clears all three live gates.")
