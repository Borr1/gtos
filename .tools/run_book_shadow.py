"""GL-3 wiring-confirmation: run the BUILT W7 book engine on LIVE FTMO bars in SHADOW (gates OFF,
read-only, NO orders). Proves the engine fetches live bars, runs the validated sleeve generators, and
produces the book's intents + shadow sizing on real current data. The per-sleeve + admission parity
(T1/T2) already prove src==route; this proves the live WIRING on the terminal.
"""
import sys
import json
import yaml
import MetaTrader5 as mt5

from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.bar_provider import TF_H4, TF_M15, TF_H1, TF_D1, TF_M1
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.utils.config import apply_profile_overrides

# map our TF ints -> live MetaTrader5 timeframe constants
_TF = {TF_M1: mt5.TIMEFRAME_M1, TF_M15: mt5.TIMEFRAME_M15, TF_H1: mt5.TIMEFRAME_H1,
       TF_H4: mt5.TIMEFRAME_H4, TF_D1: mt5.TIMEFRAME_D1}


class LiveMT5Adapter:
    """Minimal read-only adapter: the engine needs get_candles + get_account_equity only."""
    def __init__(self, path):
        if not mt5.initialize(path=path, portable=True):
            raise RuntimeError(f"connect fail: {mt5.last_error()}")

    def get_candles(self, symbol, timeframe, count):
        mt5.symbol_select(symbol, True)
        rates = mt5.copy_rates_from_pos(symbol, _TF.get(timeframe, mt5.TIMEFRAME_H4), 0, count)
        if rates is None:
            return []
        import datetime as dt
        return [{"time": dt.datetime.fromtimestamp(int(r["time"]), dt.timezone.utc).isoformat(),
                 "open": float(r["open"]), "high": float(r["high"]), "low": float(r["low"]),
                 "close": float(r["close"]), "volume": float(r["tick_volume"])} for r in rates]

    def get_account_equity(self):
        info = mt5.account_info()
        return float(info.equity) if info else 0.0


def main(path):
    mt5_adapter = LiveMT5Adapter(path)
    # SHADOW config: all gates OFF -> would_units only, NEVER an order
    cfg = {"ultimate_book_enabled": False, "ultimate_book_apply_to_execution": False,
           "ultimate_book_live_activation_allowed": False, "ultimate_book_disable_broad_selector": True,
           "ultimate_book_profile": "clean3_w7_measured_nom1p25", "ultimate_book_include_clean3": True,
           "ultimate_book_kelly_lite": True, "ultimate_book_kelly_conservative": True,
           "ultimate_book_drop_w7_symbols": True,
           "selector_v4_enabled": True, "selector_v4_apply_to_execution": False}
    # the canonical->broker map comes from the merged profile (instruments[].market.mt5_symbol);
    # inject it so the index/oil sleeves fetch under the broker names (US500.cash, USOIL.cash, ...).
    merged = apply_profile_overrides(
        yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8")), "operator_profile")
    broker_symbol = build_broker_symbol_resolver(merged)
    eng = UltimateBookLiveEngine(cfg, mt5_adapter, ".", namespace="ftmo_primary",
                                 broker_symbol=broker_symbol)
    res = eng.evaluate()   # all BUILT sleeves
    print("=== LIVE SHADOW BOOK RUN (FTMO, gates OFF, NO orders) ===")
    print("ok:", res["ok"], "| reason:", res["reason"], "| runtime_effect_now:", res["runtime_effect_now"])
    print("intents generated on latest closed H4 bar:", res["n_intents"])
    for m in res["meta"]:
        print(f"  - {m['tag']:16s} {m['symbol']:11s} day={m['decision_day']} last_close={m['last_close']}")
    for it in res["intents"]:
        print(f"    INTENT {it.sleeve:16s} {it.symbol:11s} dir={'+1' if it.direction>0 else '-1'} "
              f"stop_dist={round(it.stop_dist,4)} target={round(it.target_dist,4) if it.target_dist else None}")
    if res["decision"] is not None:
        wu = getattr(res["decision"], "would_units", []) or []
        print(f"shadow would_units (the book's sizing if gated on): {len(wu)}")
        for u in wu:
            print(f"    WOULD_SIZE cluster={u.get('cluster'):10s} sized={u.get('sized')} "
                  f"risk_pct_per_trade={round(u.get('risk_pct_per_trade',0)*100,4)}% n={u.get('n_trades')} "
                  f"reason={u.get('reason')}")
    print("\nNOTE: gates OFF + no order path exercised. This is a read-only WIRING proof on live bars.")
    mt5.shutdown()


if __name__ == "__main__":
    main(sys.argv[1])
