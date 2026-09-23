#!/usr/bin/env python3
"""x2 step 5 - M1/M5-native analogues for the close-requiring M15 conditions.

A) SWEEP-LEG-ONLY (M1-native, one-sided level break)
   M15 rule needs BOTH legs at the close: high > prior_20_high AND close < prior_20_high.
   Analogue: fire the minute the running high first prints above prior_20_high (a level
   break, knowable instantly).  Population overlap with the M15 sweep+reclaim set measured.

B) M5-NATIVE DISPLACEMENT
   M15 rule: range/atr14_M15 >= 1.5 AND |close-open|/atr14_M15 >= 0.75, needs the M15 close.
   Analogue: the identical shape test on a completed M5 sub-bar against an M5-native
   atr14 (mean high-low of the 14 preceding M5 bars).  Sub-bar 0 is known at T+5 (10 min
   early), sub-bar 1 at T+10 (5 min early), sub-bar 2 at T+15 (0 early).

Writes DISCOVERY/x2_NATIVE_ANALOGUES_V1.jsonl.gz
"""
import sys, os, json, gzip, collections, datetime as dt
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x2_bars, w0_ws

TIME, O, H, L, C = 0, 1, 2, 3, 4


def main():
    rows = w0_ws.load()
    pool = collections.defaultdict(dict)
    for r in rows:
        bt = dt.datetime.fromisoformat(r["decision_time_utc"]) - dt.timedelta(minutes=15)
        pool[(r["symbol"], bt)][r["origin_family"]] = r
    JAN0 = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc); JAN1 = dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc)
    out = []
    for sym in x2_bars.SYMBOLS:
        m15 = x2_bars.load_m15(sym)
        m15idx = {b[TIME]: i for i, b in enumerate(m15)}
        m1 = x2_bars.load_m1(sym, ("202512", "202601"))
        t1 = {b[TIME]: k for k, b in enumerate(m1)}
        # M5 series built from M1
        m5 = []
        cur = None
        for b in m1:
            slot = b[TIME].replace(minute=(b[TIME].minute // 5) * 5, second=0, microsecond=0)
            if cur is None or cur[TIME] != slot:
                if cur is not None:
                    m5.append(cur)
                cur = [slot, b[O], b[H], b[L], b[C]]
            else:
                cur[H] = max(cur[H], b[H]); cur[L] = min(cur[L], b[L]); cur[C] = b[C]
        if cur is not None:
            m5.append(cur)
        m5idx = {b[TIME]: i for i, b in enumerate(m5)}
        for i, bar in enumerate(m15):
            if not (JAN0 <= bar[TIME] < JAN1) or i < 51:
                continue
            ph20 = max(b[H] for b in m15[i - 20:i]); pl20 = min(b[L] for b in m15[i - 20:i])
            atr14 = sum(b[H] - b[L] for b in m15[i - 13:i + 1]) / 14.0
            mins = [t1.get(bar[TIME] + dt.timedelta(minutes=o)) for o in range(15)]
            mins = [m1[k] if k is not None else None for k in mins]
            present = [b for b in mins if b is not None]
            if not present or atr14 <= 0:
                continue
            # --- A: sweep-leg-only
            sweep_hi_off = sweep_lo_off = None
            rh = -1e30; rl = 1e30
            for o in range(15):
                b = mins[o]
                if b is None:
                    continue
                rh = max(rh, b[H]); rl = min(rl, b[L])
                if sweep_hi_off is None and rh > ph20:
                    sweep_hi_off = o
                if sweep_lo_off is None and rl < pl20:
                    sweep_lo_off = o
            bh = max(b[H] for b in present); bl = min(b[L] for b in present); bc = present[-1][C]
            m15_sweep_short = bh > ph20 and bc < ph20 and not (bl < pl20 and bc > pl20)
            m15_sweep_long = bl < pl20 and bc > pl20 and not (bh > ph20 and bc < ph20)
            # --- B: M5-native displacement
            m5fire = []
            for sub in range(3):
                st = bar[TIME] + dt.timedelta(minutes=5 * sub)
                j = m5idx.get(st)
                if j is None or j < 14:
                    m5fire.append(None); continue
                a5 = sum(m5[k][H] - m5[k][L] for k in range(j - 14, j)) / 14.0
                if a5 <= 0:
                    m5fire.append(None); continue
                b5 = m5[j]
                rng = b5[H] - b5[L]; body = abs(b5[C] - b5[O])
                if rng / a5 >= 1.5 and body / a5 >= 0.75:
                    m5fire.append("LONG" if b5[C] > b5[O] else "SHORT")
                else:
                    m5fire.append("")
            body15 = abs(bc - present[0][O]); rng15 = bh - bl
            m15_disp = (rng15 / atr14 >= 1.5 and body15 / atr14 >= 0.75)
            m15_disp_side = ("LONG" if bc > present[0][O] else "SHORT") if m15_disp else None
            act = pool.get((sym, bar[TIME]), {})
            rec = {"symbol": sym, "bar_time": bar[TIME].isoformat(),
                   "sweep_hi_off": sweep_hi_off, "sweep_lo_off": sweep_lo_off,
                   "m15_sweep_short": m15_sweep_short, "m15_sweep_long": m15_sweep_long,
                   "sweep_in_pool": "liquidity_sweep_reclaim" in act,
                   "sweep_pool_r": act.get("liquidity_sweep_reclaim", {}).get("gross_r"),
                   "m5_disp": m5fire, "m15_disp": m15_disp, "m15_disp_side": m15_disp_side,
                   "disp_in_pool": "displacement_continuation" in act,
                   "disp_pool_r": act.get("displacement_continuation", {}).get("gross_r")}
            out.append(rec)
        print("done", sym, len(out), flush=True)
    with gzip.open(os.path.join(D, "x2_NATIVE_ANALOGUES_V1.jsonl.gz"), "wt") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    print("rows", len(out))


if __name__ == "__main__":
    main()
