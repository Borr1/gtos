"""Diagnose the NO-FEED energy+index symbols on FTMO: is the name wrong, the symbol unsubscribed,
or is there genuinely no H4 history? For each suspect: symbol_info (exists?), select+visible, tick,
copy_rates count. Then list ALL broker symbols matching oil/index patterns to find the REAL names.
Read-only. NO orders."""
import sys
import MetaTrader5 as mt5

SUSPECT = ["USOIL_cash", "UKOIL_cash", "SPX500", "UK100", "JP225", "GER40", "US30_cash"]
# patterns to discover the broker's actual naming for these asset classes
PATTERNS = ["OIL", "WTI", "BRENT", "XTI", "XBR", "US30", "DOW", "SPX", "US500", "NAS", "UK100",
            "FTSE", "GER", "DAX", "DE40", "JP225", "JPN", "NIK", "US2000", "EU50", "STOXX",
            "FRA", "CAC", "CORN", "COTTON", "_cash", ".cash"]


def main(path):
    if not mt5.initialize(path=path, portable=True):
        raise RuntimeError(f"connect fail: {mt5.last_error()}")
    print("=== SUSPECT SYMBOL DIAGNOSIS (FTMO) ===")
    for name in SUSPECT:
        si = mt5.symbol_info(name)
        if si is None:
            print(f"  {name:14s} symbol_info=None  -> NAME DOES NOT EXIST on this broker")
            continue
        mt5.symbol_select(name, True)
        si2 = mt5.symbol_info(name)
        tk = mt5.symbol_info_tick(name)
        rates = mt5.copy_rates_from_pos(name, mt5.TIMEFRAME_H4, 0, 260)
        nrates = 0 if rates is None else len(rates)
        print(f"  {name:14s} exists visible={si2.visible} trade_mode={si2.trade_mode} "
              f"bid={getattr(tk,'bid',None)} ask={getattr(tk,'ask',None)} H4_rates={nrates}")

    print("\n=== BROKER SYMBOLS MATCHING OIL/INDEX/AGRI PATTERNS ===")
    allsyms = mt5.symbols_get()
    print(f"(total broker symbols: {len(allsyms)})")
    hits = []
    for s in allsyms:
        up = s.name.upper()
        if any(p.upper() in up for p in PATTERNS):
            hits.append(s.name)
    for nm in sorted(set(hits)):
        si = mt5.symbol_info(nm)
        print(f"  {nm:18s} visible={si.visible} trade_mode={si.trade_mode} digits={si.digits} "
              f"csz={si.trade_contract_size}")
    mt5.shutdown()


if __name__ == "__main__":
    main(sys.argv[1])
