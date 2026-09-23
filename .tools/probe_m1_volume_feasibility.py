"""vp_euidx_pocgrav feasibility: does the live FTMO feed supply M1 bars WITH tick volume for the EU
index symbols, and how deep? The sleeve needs prior-day M1 volume profiles. Read-only. NO orders."""
import sys
import datetime as dt
import MetaTrader5 as mt5

EU_IDX = {"GER40": "GER40.cash", "UK100": "UK100.cash"}


def main(path):
    if not mt5.initialize(path=path, portable=True):
        print("CONNECT FAIL", mt5.last_error()); return
    print("=== M1 TICK-VOLUME FEASIBILITY (FTMO, EU index) ===")
    for canon, nat in EU_IDX.items():
        mt5.symbol_select(nat, True)
        # how many M1 bars can we pull, and do they carry tick volume?
        m1 = mt5.copy_rates_from_pos(nat, mt5.TIMEFRAME_M1, 0, 20000)
        if m1 is None or len(m1) == 0:
            print(f"  {canon:8s} {nat:12s} M1: NONE  -> sleeve NOT feasible from this feed")
            continue
        n = len(m1)
        first = dt.datetime.fromtimestamp(int(m1[0]["time"]), dt.timezone.utc)
        last = dt.datetime.fromtimestamp(int(m1[-1]["time"]), dt.timezone.utc)
        span_days = (last - first).total_seconds() / 86400.0
        # tick volume presence: count bars with tick_volume>0
        nz = sum(1 for r in m1 if int(r["tick_volume"]) > 0)
        # real volume field (broker-dependent; often 0 for CFD)
        rv = sum(1 for r in m1 if int(r["real_volume"]) > 0)
        # how many distinct prior UTC days of M1 are present (for prior-day profiles)
        days = sorted({dt.datetime.fromtimestamp(int(r["time"]), dt.timezone.utc).date() for r in m1})
        print(f"  {canon:8s} {nat:12s} M1 bars={n} span~{span_days:.1f}d  "
              f"first={first:%Y-%m-%d %H:%M} last={last:%Y-%m-%d %H:%M}")
        print(f"           tick_volume>0: {nz}/{n} ({100*nz/n:.1f}%) | real_volume>0: {rv}/{n} | "
              f"distinct UTC days: {len(days)}")
        # sample a couple bars
        for r in (m1[0], m1[n//2], m1[-1]):
            t = dt.datetime.fromtimestamp(int(r["time"]), dt.timezone.utc)
            print(f"           {t:%Y-%m-%d %H:%M} O={r['open']} H={r['high']} L={r['low']} "
                  f"C={r['close']} tickvol={int(r['tick_volume'])} realvol={int(r['real_volume'])}")
    print("\nFEASIBILITY: vp_euidx_pocgrav needs >=1 full prior UTC day of M1 with tick_volume>0 per symbol.")
    mt5.shutdown()


if __name__ == "__main__":
    main(sys.argv[1])
