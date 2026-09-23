"""GL-5 pre-flight: prove the book's GATED-ON sizing is within the owner dial (<=1.25% per unit, <=4%
gross) and that a real realized unit's trade_params clears all 3 live fail-closed gates. Gates are
enabled IN MEMORY ONLY (a copy of the runtime config) — the config file is untouched and NO order path
is exercised (engine.evaluate + a gate dry-run only). Read-only. NO orders. NO open_trade."""
import sys
import copy
import datetime as dt
import yaml
import MetaTrader5 as mt5

from src.utils.config import apply_profile_overrides, apply_instrument_overrides
from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.components.ultimate_book.bar_provider import TF_M1, TF_M15, TF_H1, TF_H4, TF_D1
from src.components.ultimate_book.order_router import UltimateBookOrderRouter
from src.components.ultimate_book import execution_packets as EP
from src.components.execution import ExecutionEngine
from src.components.execution_manager_v4 import evaluate_execution_manager_v4
from src.components.broker_net_cost_engine import build_pretrade_cost_packet

_TF = {TF_M1: mt5.TIMEFRAME_M1, TF_M15: mt5.TIMEFRAME_M15, TF_H1: mt5.TIMEFRAME_H1,
       TF_H4: mt5.TIMEFRAME_H4, TF_D1: mt5.TIMEFRAME_D1}
DIAL = 0.0125     # 1.25% nominal half-Kelly per-unit ceiling
GROSS = 0.04      # 4% gross open-risk cap


class LiveMT5Adapter:
    def __init__(self, path):
        if not mt5.initialize(path=path, portable=True):
            raise RuntimeError(f"connect fail: {mt5.last_error()}")
    def get_candles(self, symbol, timeframe, count):
        mt5.symbol_select(symbol, True)
        r = mt5.copy_rates_from_pos(symbol, _TF.get(timeframe, mt5.TIMEFRAME_H4), 0, count)
        if r is None:
            return []
        return [{"time": dt.datetime.fromtimestamp(int(x["time"]), dt.timezone.utc).isoformat(),
                 "open": float(x["open"]), "high": float(x["high"]), "low": float(x["low"]),
                 "close": float(x["close"]), "volume": float(x["tick_volume"])} for x in r]
    def get_account_equity(self):
        info = mt5.account_info(); return float(info.equity) if info else 0.0
    def get_account_balance(self):
        info = mt5.account_info(); return float(info.balance) if info else 0.0


def main(path):
    ad = LiveMT5Adapter(path)
    base = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    merged = apply_profile_overrides(base, "operator_profile")
    resolver = build_broker_symbol_resolver(merged)

    # GATED-ON runtime config — IN MEMORY ONLY (deep copy; the file is NOT modified)
    rt = copy.deepcopy(merged.get("gtos_vnext_runtime", {}))
    rt["ultimate_book_enabled"] = True
    rt["ultimate_book_apply_to_execution"] = True
    rt["ultimate_book_live_activation_allowed"] = True
    print("=== GL-5 PRE-FLIGHT: gated-ON sizing (IN MEMORY; config file untouched; NO orders) ===")
    print(f"profile={rt.get('ultimate_book_profile')} kelly_conservative={rt.get('ultimate_book_kelly_conservative')} "
          f"include_clean3={rt.get('ultimate_book_include_clean3')}")

    eng = UltimateBookLiveEngine(rt, ad, ".", namespace="ftmo_preflight", broker_symbol=resolver)
    res = eng.evaluate()
    print(f"ok={res['ok']} reason={res['reason']} runtime_effect_now={res['runtime_effect_now']} "
          f"n_intents={res['n_intents']}")
    dec = res["decision"]
    realized = list(getattr(dec, "realized_units", []) or []) if dec else []
    would = list(getattr(dec, "would_units", []) or []) if dec else []
    units = realized or would     # if a signal fired they are realized (gated on); else inspect would
    print(f"realized_units={len(realized)} would_units={len(would)}")

    ok = True
    gross = 0.0
    for u in units:
        rpt = float(u.get("risk_pct_per_trade", 0.0))
        urp = float(u.get("unit_risk_pct", 0.0))
        gross += urp
        within = rpt <= DIAL + 1e-9
        ok = ok and within
        print(f"  unit cluster={u.get('cluster'):11s} sized={u.get('sized')} n={u.get('n_trades')} "
              f"risk_pct_per_trade={rpt*100:.4f}% unit_risk_pct={urp*100:.4f}% "
              f"{'OK<=1.25%' if within else 'OVER DIAL!'}")
    print(f"gross open risk = {gross*100:.4f}%  (cap {GROSS*100:.1f}%)  "
          f"{'OK' if gross <= GROSS + 1e-9 else 'OVER GROSS CAP!'}")
    ok = ok and (gross <= GROSS + 1e-9)

    # If a unit is realized, dry-run the 3 fail-closed gates on its trade_params (NO open_trade).
    if realized and res["intents"]:
        unit = realized[0]
        members = set(unit.get("sleeve_members", []))
        intent = next((it for it in res["intents"] if it.sleeve in members), None)
        if intent is not None:
            sym = intent.symbol
            tick = mt5.symbol_info_tick(resolver(sym))
            cfg_i = apply_instrument_overrides(merged, sym)
            router = UltimateBookOrderRouter(cfg_i, namespace="operator_profile")
            acct = {"current_equity": ad.get_account_equity(), "balance": ad.get_account_balance(),
                    "account_login": 531325516,
                    "day_start_equity_or_balance_baseline": ad.get_account_equity(),
                    "daily_reset_window_id": "2026-06-15"}

            class _T:
                def __init__(s, b, a): s.bid = b; s.ask = a; s.time = "2026-06-15T04:00:00+00:00"; s.spread_cents = (a - b) * 100
            tk = _T(tick.bid, tick.ask)
            tp = router.build_trade_params(_UV(unit), intent, tk, acct)
            print(f"\n  trade_params for {sym} ({intent.sleeve}): keys={len(tp) if tp else 0} "
                  f"risk_pct_override={tp.get('risk_pct_override') if tp else None}")
            if tp:
                bsym = resolver(sym)
                cost = build_pretrade_cost_packet(config=cfg_i, trade_params=tp, tick=tk, symbol=sym,
                                                  broker_symbol=bsym, entry_price=tp["entry_price"],
                                                  stop_loss=tp["stop_loss"], sl_distance=tp["risk_distance"],
                                                  risk_pct=tp["risk_pct_override"])
                ee = ExecutionEngine(_StubMT5(tk), cfg_i)
                g1 = ee._vnext_dynamic_policy_support_error(tp)
                risk, g3 = ee._resolve_vnext_production_risk_pct(tp, risk_pct_override=tp["risk_pct_override"])
                d = evaluate_execution_manager_v4(config=cfg_i, trade_params=tp, symbol=sym,
                                                  broker_symbol=bsym, pretrade_cost_model=cost)
                print(f"  GATE1 dyn_policy_error={g1} | GATE3 risk={risk} err={g3} | "
                      f"GATE2 action={d.action} block={d.should_block} fatal={getattr(d,'fatal',[])} | "
                      f"cost={cost.get('status')}")
                gates_ok = (g1 is None and g3 is None and d.action == 'allow' and not d.should_block
                            and not (getattr(d, 'fatal', []) or []) and cost.get('status') == 'PASSED')
                print(f"  ALL 3 GATES CLEAR (dry-run, NO order placed): {gates_ok}")
                ok = ok and gates_ok and (risk <= DIAL * 100 + 1e-9)

    print(f"\nPRE-FLIGHT SIZING/GATES: {'PASS' if ok else 'FAIL — DO NOT FLIP'}")
    mt5.shutdown()


class _UV:
    def __init__(s, u):
        s.cluster = u.get("cluster", "book"); s.sleeve_members = u.get("sleeve_members", [])
        s.n_trades = u.get("n_trades", 1); s.confidence = u.get("confidence")
        s.risk_pct_per_trade = u.get("risk_pct_per_trade", 0.0); s.unit_risk_pct = u.get("unit_risk_pct")
        s.sized = u.get("sized", False); s.reason = u.get("reason")


class _StubMT5:
    def __init__(s, tk): s._tk = tk
    def get_tick(s, symbol): return s._tk
    def get_account_balance(s): return 100000.0
    def get_account_equity(s): return 100000.0
    def get_positions(s, symbol=None): return []
    def is_connected(s): return True
    def get_margin_mode(s): return "hedging"


if __name__ == "__main__":
    main(sys.argv[1])
