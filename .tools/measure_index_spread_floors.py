"""GL-4 completion: measure LIVE index+oil spreads (skipped earlier as out-of-session) in stop-R terms.
idxrev geometry: sd=1.5*ATR(H4). energy: ~1*ATR(H4) conservative. Report spread_px, bps, spread/ATR,
spread/(stop) vs the 0.20-R wall. Read-only, FTMO broker names. NO orders."""
import sys
import MetaTrader5 as mt5

# canonical -> (broker_native, stop_atrs, timeframe)
BOOK = {
    "SPX500": ("US500.cash", 1.5), "UK100": ("UK100.cash", 1.5), "JP225": ("JP225.cash", 1.5),
    "GER40": ("GER40.cash", 1.5), "US30_cash": ("US30.cash", 1.5),
    "USOIL_cash": ("USOIL.cash", 1.0), "UKOIL_cash": ("UKOIL.cash", 1.0),
}
WALL = 0.20


def atr14_h4(nat):
    rates = mt5.copy_rates_from_pos(nat, mt5.TIMEFRAME_H4, 0, 60)
    if rates is None or len(rates) < 15:
        return None
    trs = [max(rates[i]['high'] - rates[i]['low'], abs(rates[i]['high'] - rates[i-1]['close']),
               abs(rates[i]['low'] - rates[i-1]['close'])) for i in range(1, len(rates))]
    return sum(trs[-14:]) / 14.0


def main(path):
    if not mt5.initialize(path=path, portable=True):
        print("CONNECT FAIL", mt5.last_error()); return
    print("=== GL-4 INDEX/OIL LIVE SPREAD FLOORS (FTMO, stop-R) ===")
    print(f"{'canon':11s} {'native':11s} {'spread_px':>10} {'bps':>7} {'ATR_H4':>11} "
          f"{'spr/ATR':>9} {'spr/stop':>9} {'verdict'}")
    worst = 0.0
    for canon, (nat, stop_atrs) in BOOK.items():
        mt5.symbol_select(nat, True)
        t = mt5.symbol_info_tick(nat)
        if not t or not t.bid or not t.ask:
            print(f"{canon:11s} {nat:11s} {'--no quote (closed)--':>10}")
            continue
        spread = t.ask - t.bid
        bps = spread / t.bid * 1e4
        atr = atr14_h4(nat)
        spr_atr = (spread / atr) if atr else None
        spr_stop = (spread / (stop_atrs * atr)) if atr else None
        if spr_stop:
            worst = max(worst, spr_stop)
        v = "?"
        if spr_stop is not None:
            v = "OVER WALL!" if spr_stop >= WALL else ("OK (<0.20R)" if spr_stop < 0.10 else "WATCH (0.10-0.20R)")
        print(f"{canon:11s} {nat:11s} {spread:>10.3f} {bps:>7.2f} "
              f"{str(round(atr,3)) if atr else 'n/a':>11} {str(round(spr_atr,4)) if spr_atr else 'n/a':>9} "
              f"{str(round(spr_stop,4)) if spr_stop else 'n/a':>9} {v}")
    print(f"\nworst spread/stop across index+oil: {round(worst,4)}R  (wall={WALL}R)")
    print("VERDICT:", "ALL UNDER WALL" if 0 < worst < WALL else "CHECK — at/over wall" if worst >= WALL
          else "no quotes")
    mt5.shutdown()


if __name__ == "__main__":
    main(sys.argv[1])
