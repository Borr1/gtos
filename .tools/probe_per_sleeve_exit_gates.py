"""THROWAWAY gate probe: build a V4 trade_params for EACH of the 5 supported live
dynamic execution policies and RUN the 3 fail-closed gates against the FTMO-merged
live config. Reports PASS/FAIL per policy with the exact refusal reasons.

NO MT5 / NO broker / NO order. Stub engine + stub tick exactly like
tests/ultimate_book/test_order_route.py. Read-only on src/ and config/.
"""
import sys, json
REPO = r"C:\Users\MSI\Documents\ai-trading-agent"
sys.path.insert(0, REPO)

import yaml
from src.utils.config import apply_profile_overrides, apply_instrument_overrides
from src.components.ultimate_book.admission import SizedUnit, TradeIntent
from src.components.ultimate_book import execution_packets as EP
from src.components.execution_manager_v4 import evaluate_execution_manager_v4
from src.components.broker_net_cost_engine import build_pretrade_cost_packet
from src.components.execution import ExecutionEngine
from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)


class _Tick:
    def __init__(self, bid, ask):
        self.bid = bid; self.ask = ask
        self.time = "2026-06-15T01:00:00+00:00"
        self.spread_cents = (ask - bid) * 100


class _StubMT5:
    def get_tick(self, symbol): return _Tick(2999.7, 3000.0)
    def get_account_balance(self): return 100000.0
    def get_account_equity(self): return 100000.0
    def get_positions(self, symbol=None): return []
    def is_connected(self): return True
    def get_margin_mode(self): return "hedging"


def merged_cfg():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    cfg = apply_profile_overrides(cfg, "operator_profile")
    cfg = apply_instrument_overrides(cfg, "XAUUSD")
    return cfg


def build_tp_for_policy(policy, *, trigger_r, final_target_r, time_stop_bars=None,
                        pullback_r=None, partial_close_ratio=None, trail_gap_r=None,
                        target_dist=None):
    """Start from the production momentum builder, then swap policy + R fields +
    the policy-specific management field + rebuild the geometry packet for `policy`."""
    su = SizedUnit(cluster="metals", sleeve_members=["metals_core"], n_trades=1, confidence=1.0,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    intent = TradeIntent(sleeve="metals_core", symbol="XAUUSD", direction=1,
                         decision_day="2026-06-15", stop_dist=10.0,
                         target_dist=target_dist)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    entry = 3000.0
    rd = 10.0
    sign = 1.0
    td = float(target_dist) if target_dist else final_target_r * rd
    geom = {"entry_price": entry, "risk_distance": rd,
            "stop_loss": entry - sign * rd, "take_profit_1": entry + sign * td}
    tp = EP.build_book_trade_params(su, intent, geom, acct,
                                    profile_namespace="operator_profile")

    epid = f"emv4_{policy}_v1"
    tp["gtos_vnext_dynamic_policy_selected"] = policy
    tp["gtos_vnext_execution_policy_id"] = epid
    tp["gtos_vnext_selected_cell_risk_selected_policy"] = policy
    tp["gtos_vnext_selected_cell_risk_cell_id"] = f"metals::{policy}::XAUUSD"
    tp["gtos_vnext_dynamic_be_trigger_r"] = trigger_r
    tp["gtos_vnext_dynamic_final_target_r"] = final_target_r
    tp["gtos_vnext_dynamic_time_stop_bars"] = time_stop_bars
    # policy-specific management fields (only the relevant one is read)
    tp["gtos_vnext_dynamic_momentum_pullback_r"] = pullback_r
    tp["gtos_vnext_dynamic_partial_close_ratio"] = partial_close_ratio
    tp["gtos_vnext_dynamic_trail_gap_r"] = trail_gap_r

    # rebuild the explicit geometry packet for THIS policy (binds exit_management_contract_status)
    mgmt_params = {}
    if pullback_r is not None:
        mgmt_params["gtos_vnext_dynamic_momentum_pullback_r"] = pullback_r
    if partial_close_ratio is not None:
        mgmt_params["gtos_vnext_dynamic_partial_close_ratio"] = partial_close_ratio
    if trail_gap_r is not None:
        mgmt_params["gtos_vnext_dynamic_trail_gap_r"] = trail_gap_r
    if time_stop_bars is not None:
        mgmt_params["gtos_vnext_dynamic_time_stop_bars"] = time_stop_bars
    geo = build_target_stop_geometry_v4_contract(
        config=None, selected_policy=policy, execution_policy_id=epid,
        source_event={
            "source_mode": "ultimate_book_runtime_trade_params",
            "source_path_feature_status": "runtime_asof_ultimate_book_closed_bar_features",
            "source_window_complete": True,
            "selected_policy_ordered_path_status":
                "asof_runtime_path_ordering_not_required_before_order_send",
            "selected_policy_same_bar_ambiguous": False,
        },
        direction="LONG", entry_price=entry, stop_loss=geom["stop_loss"],
        risk_distance=rd, trigger_r=trigger_r, final_target_r=final_target_r,
        trade_params=mgmt_params,
    )
    tp["gtos_vnext_dynamic_target_stop_geometry_v4"] = geo
    return tp


def build_real_sleeve_tp(sleeve):
    """Build a V4 trade_params straight from the REAL per-sleeve profile registry the production
    build_book_trade_params now resolves — a native (stop_dist, target_dist) TradeIntent per sleeve.
    No field-swapping: this exercises the actual SLEEVE_EXIT_PROFILES resolution end-to-end."""
    prof = EP.SLEEVE_EXIT_PROFILES.get(sleeve, EP.DEFAULT_EXIT_PROFILE)
    su = SizedUnit(cluster="book", sleeve_members=[sleeve], n_trades=1, confidence=1.0,
                   risk_pct_per_trade=0.005, unit_risk_pct=0.5, sized=True, reason="ok")
    sd = 10.0
    # native target_dist per sleeve geometry (price distance):
    #   final_from_intent sleeves derive final_target_r = target_dist/stop_dist
    #   (metals runner ~3R = 30.0; vp_euidx measured-move ~1.6R = 16.0). Other sleeves carry the
    #   profile's fixed final_target_r * stop_dist as their native target.
    if prof.get("final_from_intent"):
        td = 16.0 if sleeve == "vp_euidx_pocgrav" else 30.0
    else:
        td = float(prof["final_target_r"]) * sd
    intent = TradeIntent(sleeve=sleeve, symbol="XAUUSD", direction=1,
                         decision_day="2026-06-15", stop_dist=sd, target_dist=td)
    acct = dict(current_equity=100000.0, balance=100000.0, account_login=531325516,
                day_start_equity_or_balance_baseline=100000.0, daily_reset_window_id="2026-06-15")
    entry = 3000.0
    sign = 1.0
    geom = {"entry_price": entry, "risk_distance": sd,
            "stop_loss": entry - sign * sd, "take_profit_1": entry + sign * td}
    return EP.build_book_trade_params(su, intent, geom, acct,
                                      profile_namespace="operator_profile")


def run_gates(cfg, ee, tp):
    out = {}
    # GATE 1
    g1 = ee._vnext_dynamic_policy_support_error(tp)
    out["gate1_support_error"] = g1
    out["gate1_pass"] = g1 is None
    # GATE 3
    risk, err = ee._resolve_vnext_production_risk_pct(tp, risk_pct_override=tp["risk_pct_override"])
    out["gate3_risk"] = risk
    out["gate3_err"] = err
    out["gate3_pass"] = (err is None and risk == tp["risk_pct_override"])
    # GATE 2 (needs cost packet)
    tick = _Tick(2999.7, 3000.0)
    cost = build_pretrade_cost_packet(config=cfg, trade_params=tp, tick=tick,
                                      symbol="XAUUSD", broker_symbol="XAUUSD",
                                      entry_price=tp["entry_price"], stop_loss=tp["stop_loss"],
                                      sl_distance=10.0, risk_pct=tp["risk_pct_override"])
    out["cost_status"] = cost.get("status")
    dec = evaluate_execution_manager_v4(config=cfg, trade_params=tp, symbol="XAUUSD",
                                        broker_symbol="XAUUSD", pretrade_cost_model=cost)
    out["gate2_action"] = dec.action
    out["gate2_should_block"] = dec.should_block
    out["gate2_fatal"] = list(dec.fatal_reasons)
    out["gate2_pass"] = (dec.action == "allow" and not dec.should_block and not dec.fatal_reasons)
    out["all_pass"] = out["gate1_pass"] and out["gate2_pass"] and out["gate3_pass"]
    # also surface what the BROKER TP would become (final_target_r recompute at open_trade)
    out["broker_tp_R_from_final_target_r"] = tp["gtos_vnext_dynamic_final_target_r"]
    return out


def main():
    cfg = merged_cfg()
    ee = ExecutionEngine(_StubMT5(), cfg)
    # XAUUSD instrument context for the engine symbol
    ee.symbol = "XAUUSD"
    ee._persist_symbol = "XAUUSD"

    cases = {
        "momentum_exhaustion": dict(trigger_r=1.0, final_target_r=2.0, pullback_r=0.4),
        "partial_be_runner":   dict(trigger_r=2.0, final_target_r=4.0, partial_close_ratio=0.5),
        "trailing_runner":     dict(trigger_r=1.0, final_target_r=3.0, trail_gap_r=0.5),
        "be_after_trigger":    dict(trigger_r=5.0, final_target_r=4.0),   # trigger>target => BE never arms
        "time_stop":           dict(trigger_r=4.0, final_target_r=4.0, time_stop_bars=80),
    }
    results = {}
    for pol, kw in cases.items():
        tp = build_tp_for_policy(pol, **kw)
        results[pol] = run_gates(cfg, ee, tp)

    # vp_euidx measured-move case: final_target_r derived from target_dist/stop_dist
    tp_vp = build_tp_for_policy("time_stop", trigger_r=1.6, final_target_r=1.6,
                                time_stop_bars=60, target_dist=16.0)  # 16 price / 10 stop = 1.6R
    results["time_stop__vp_measured_move(td=16,sd=10->1.6R)"] = run_gates(cfg, ee, tp_vp)

    print(json.dumps(results, indent=2, default=str))
    print("\n==== SUMMARY (synthetic 5-policy matrix) ====")
    for pol, r in results.items():
        print(f"{pol:55s} G1={r['gate1_pass']!s:5} G2={r['gate2_pass']!s:5} "
              f"G3={r['gate3_pass']!s:5} ALL={r['all_pass']}")
        if not r["all_pass"]:
            print(f"    g1={r['gate1_support_error']} g3={r['gate3_err']} "
                  f"g2_fatal={r['gate2_fatal']} cost={r['cost_status']}")

    # ---- REAL per-sleeve registry: every W7 book sleeve + the default fallback ----
    sleeves = list(EP.SLEEVE_EXIT_PROFILES.keys()) + ["__default_unlisted_sleeve__"]
    print("\n==== SUMMARY (REAL SLEEVE_EXIT_PROFILES — all 11 sleeves + default) ====")
    all_ok = all(r["all_pass"] for r in results.values())
    print(f"{'sleeve':22s} {'policy':18s} {'trig':>5s} {'finalR':>7s} {'tstop':>6s}  "
          f"G1    G2    G3    ALL")
    for sleeve in sleeves:
        tp = build_real_sleeve_tp(sleeve)
        r = run_gates(cfg, ee, tp)
        all_ok = all_ok and r["all_pass"]
        print(f"{sleeve:22s} {str(tp['gtos_vnext_dynamic_policy_selected']):18s} "
              f"{tp['gtos_vnext_dynamic_be_trigger_r']!s:>5} "
              f"{tp['gtos_vnext_dynamic_final_target_r']!s:>7} "
              f"{str(tp['gtos_vnext_dynamic_time_stop_bars']):>6}  "
              f"{r['gate1_pass']!s:5} {r['gate2_pass']!s:5} {r['gate3_pass']!s:5} {r['all_pass']}")
        if not r["all_pass"]:
            print(f"    g1={r['gate1_support_error']} g3={r['gate3_err']} "
                  f"g2_fatal={r['gate2_fatal']} cost={r['cost_status']}")
        # native-geometry cross-check: broker TP R == final_target_r carried on the tp
        assert tp["gtos_vnext_book_native_exit_management"] is True, sleeve
    print(f"\nALL_GATES_PASS_ALL_SLEEVES={all_ok}")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
