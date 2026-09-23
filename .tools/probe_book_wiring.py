"""GL-3 DEEP wiring probe: prove the BUILT W7 book engine is actually wired to LIVE FTMO bars.

The plain shadow run reports n_intents=0, which is ambiguous: it cannot tell "wiring broken / no bars"
from "wiring fine / no signal fired this bar". This probe mirrors the engine's _generate_intents loop
per (sleeve, symbol) and reports, for EACH: candles fetched, closed bars, warmup-pass, the live last
close + decision day, and the generator outcome (intent vs None vs exception). It also pulls a live tick
per symbol so the order-geometry seam is proven on real quotes. Read-only. Gates OFF. NO orders.
"""
import sys
import datetime as dt
import yaml
import MetaTrader5 as mt5

from src.components.ultimate_book.bar_provider import (
    get_closed_bars, decision_day_of, enough, TF_M1, TF_M15, TF_H1, TF_H4, TF_D1)
from src.components.ultimate_book.sleeves.registry import active_specs
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.utils.config import apply_profile_overrides

_TF = {TF_M1: mt5.TIMEFRAME_M1, TF_M15: mt5.TIMEFRAME_M15, TF_H1: mt5.TIMEFRAME_H1,
       TF_H4: mt5.TIMEFRAME_H4, TF_D1: mt5.TIMEFRAME_D1}
_TFNAME = {TF_M1: "M1", TF_M15: "M15", TF_H1: "H1", TF_H4: "H4", TF_D1: "D1"}


class LiveMT5Adapter:
    def __init__(self, path):
        if not mt5.initialize(path=path, portable=True):
            raise RuntimeError(f"connect fail: {mt5.last_error()}")

    def get_candles(self, symbol, timeframe, count):
        mt5.symbol_select(symbol, True)
        rates = mt5.copy_rates_from_pos(symbol, _TF.get(timeframe, mt5.TIMEFRAME_H4), 0, count)
        if rates is None:
            return []
        return [{"time": dt.datetime.fromtimestamp(int(r["time"]), dt.timezone.utc).isoformat(),
                 "open": float(r["open"]), "high": float(r["high"]), "low": float(r["low"]),
                 "close": float(r["close"]), "volume": float(r["tick_volume"])} for r in rates]

    def get_account_equity(self):
        info = mt5.account_info()
        return float(info.equity) if info else 0.0


def main(path):
    ad = LiveMT5Adapter(path)
    info = mt5.account_info()
    # build the canonical->broker resolver from the SAME merged profile the live path uses
    merged = apply_profile_overrides(
        yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8")), "operator_profile")
    broker_symbol = build_broker_symbol_resolver(merged)
    print("=== GL-3 DEEP WIRING PROBE (FTMO live, read-only, gates OFF, NO orders) ===")
    if info:
        print(f"account login={info.login} server={info.server} equity={info.equity} "
              f"currency={info.currency} trade_allowed={info.trade_allowed}")
    print(f"{'sleeve':18s} {'canon':11s} {'broker':12s} {'tf':4s} {'cndl':>5s} {'bars':>5s} "
          f"{'warmup':>7s} {'last_close':>13s} {'decision_day':>12s}  outcome")
    print("-" * 118)

    total_intents = 0
    rows = 0
    feed_ok = 0
    bid_ask_ok = 0
    for spec in active_specs(None):       # all BUILT sleeves
        for symbol in spec.on_surface:
            rows += 1
            broker_sym = broker_symbol(symbol)   # canonical -> broker mt5_symbol (the live boundary)
            bars, times = get_closed_bars(ad, broker_sym, spec.timeframe, 260)
            ncndl = len(bars) + 1 if bars else 0   # +1 for the dropped forming bar (approx)
            nbars = len(bars)
            if nbars:
                feed_ok += 1
            warm = enough(bars, spec.cluster) if bars else False
            last_close = round(bars[-1].c, 5) if bars else None
            day = decision_day_of(times[-1]) if times else None
            outcome = "—"
            if not bars:
                outcome = "NO FEED"
            elif not warm:
                outcome = f"warmup<{nbars}"
            else:
                try:
                    intent = spec.generator(symbol, bars, day)
                    if intent is None:
                        outcome = "no-signal (ran OK)"
                    else:
                        total_intents += 1
                        outcome = (f"INTENT dir={'+1' if intent.direction>0 else '-1'} "
                                   f"stop={round(intent.stop_dist,5)} "
                                   f"tgt={round(intent.target_dist,5) if intent.target_dist else None}")
                except Exception as e:
                    outcome = f"GEN EXC {e!r}"
            # live tick for the order-geometry seam (under the BROKER name, as the owner now fetches it)
            mt5.symbol_select(broker_sym, True)
            tk = mt5.symbol_info_tick(broker_sym)
            if tk and tk.bid and tk.ask:
                bid_ask_ok += 1
            print(f"{spec.tag:18s} {symbol:11s} {broker_sym:12s} {_TFNAME.get(spec.timeframe,'?'):4s} "
                  f"{ncndl:5d} {nbars:5d} {str(warm):>7s} {str(last_close):>13s} {str(day):>12s}  {outcome}")

    print("-" * 104)
    print(f"rows={rows} | symbols_with_live_feed={feed_ok}/{rows} | symbols_with_live_tick={bid_ask_ok}/{rows} "
          f"| intents_fired_this_bar={total_intents}")
    print("WIRING VERDICT:", "LIVE FEED PROVEN" if feed_ok == rows and bid_ask_ok == rows
          else f"PARTIAL ({feed_ok}/{rows} feed, {bid_ask_ok}/{rows} tick) — investigate the gaps")
    print("NOTE: 'no-signal (ran OK)' = wiring proven, generator executed on live bars, no entry this bar.")
    mt5.shutdown()


if __name__ == "__main__":
    main(sys.argv[1])
