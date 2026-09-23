#!/usr/bin/env python3
"""e-coherence step 3 — attach L10's PER-SYMBOL broker-true cost to the base frame and
re-adjudicate A2 (L5 says the cost repair is +0.095; L8/L12 say it is negative).

L8 and L12 both used a FLAT 7.3x spread divisor taken from the swarm brief.  L10 measured
that the frozen model is SCRAMBLED per symbol (0.017x to 33.9x), so the flat divisor is
itself a defect.  This rebuilds the true cost row by row with L10's own method and
constants, then compares the three arms on identical rows.
"""
import json, os, pickle
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
TICK = json.load(open(f"{D}/L10X_TICK_SPREAD_V1.json"))
LIVE = json.load(open(f"{D}/L10X_LIVE_COST_PRICEUNITS_V1.json"))

TMAP = {'XAUUSD': 'XAUUSD', 'UK100': 'UK100_cash', 'SPX500': 'US500_cash', 'NAS100': 'US100_cash',
        'US30_cash': 'US30_cash', 'GBPUSD': 'GBPUSD', 'GER40': 'GER40_cash', 'JP225': 'JP225_cash',
        'USDCAD': 'USDCAD', 'BTCUSD': 'BTCUSD', 'EURJPY': 'EURJPY', 'ETHUSD': 'ETHUSD',
        'XAGUSD': 'XAGUSD', 'USDCHF': 'USDCHF', 'USDJPY': 'USDJPY', 'EURGBP': 'EURGBP',
        'NZDUSD': 'NZDUSD', 'EURUSD': 'EURUSD', 'UKOIL_cash': 'UKOIL_cash', 'GBPJPY': 'GBPJPY',
        'AUDJPY': 'AUDJPY', 'USOIL_cash': 'USOIL_cash', 'AUDUSD': 'AUDUSD', 'CHFJPY': 'CHFJPY'}
JPYCOMM, USDCOMM = 0.00808905, 5.00048e-05
COMM = {'EURUSD': USDCOMM, 'GBPUSD': USDCOMM, 'AUDUSD': USDCOMM, 'NZDUSD': USDCOMM,
        'USDJPY': JPYCOMM, 'GBPJPY': JPYCOMM, 'EURJPY': JPYCOMM, 'AUDJPY': JPYCOMM, 'CHFJPY': JPYCOMM,
        'XAUUSD': 0.0576, 'XAGUSD': 0.001, 'UK100': 0.0, 'SPX500': 0.0, 'NAS100': 0.0,
        'US30_cash': 0.0, 'GER40': 0.0, 'JP225': 0.0, 'UKOIL_cash': 0.0, 'USOIL_cash': 0.0}
BTC_BPS = 39.2778 / 88599.74 * 1e4
SLIPMAP = {'XAUUSD': 'ftmo:XAUUSD', 'SPX500': 'ftmo:US500.cash', 'US30_cash': 'ftmo:US30.cash',
           'UK100': 'ftmo:UK100.cash', 'GER40': 'ftmo:GER40.cash', 'JP225': 'ftmo:JP225.cash',
           'BTCUSD': 'ftmo:BTCUSD', 'ETHUSD': 'ftmo:ETHUSD', 'EURUSD': 'ftmo:EURUSD',
           'GBPUSD': 'ftmo:GBPUSD', 'USDJPY': 'ftmo:USDJPY', 'GBPJPY': 'ftmo:GBPJPY'}


def rowcost(sym, ep, rd):
    tk = TICK.get('ftmo:' + TMAP.get(sym, sym))
    if not tk or not tk.get('spread_bps_median'):
        return None, None, None
    sp = tk['spread_bps_median'] * ep / 1e4
    if sym == 'BTCUSD':
        cm = BTC_BPS * ep / 1e4
    elif sym == 'ETHUSD':
        cm = 1.09905
    elif sym in ('USDCHF', 'USDCAD'):
        cm = USDCOMM * ep
    elif sym == 'EURGBP':
        cm = USDCOMM * 0.74
    else:
        cm = COMM.get(sym, 0.0)
    sl = LIVE.get(SLIPMAP.get(sym, ''), {}).get('slip_px', 0.0) or 0.0
    sl = max(sl, 0.0)
    return sp / rd, cm / rd, sl / rd


tri = [rowcost(s, e, r) for s, e, r in zip(df["symbol"], df["entry_price"], df["risk_distance"])]
df["true_spread_r"] = [t[0] for t in tri]
df["true_comm_r"] = [t[1] for t in tri]
df["true_slip_r"] = [t[2] for t in tri]
df["cost_r_TRUE"] = df["true_spread_r"] + df["true_comm_r"] + df["true_slip_r"]
df["H"] = df["fill_honest_walk_r"].astype(float).fillna(0.0)

pickle.dump(df, open("/tmp/ecoh/e_base.pkl", "wb"))

N = len(df)
ps = df["born"] == "past_stop"
b1 = df["bars_to_entry_touch"] == 1
ex = ~ps
gF = df["gate_both"]
gT = (df["true_spread_r"] <= 0.10) & (df["cost_r_TRUE"] <= 0.15)
g73 = (df["spread_r"] / 7.3 <= 0.10) & (df["cost_r_d73"] <= 0.15)

OUT = {"validation_vs_L10": {
    "true_total_mean_all_rows": round(float(df["cost_r_TRUE"].mean()), 6),
    "L10_reported": 0.189297,
    "true_spread_mean": round(float(df["true_spread_r"].mean()), 6), "L10_spread": 0.124828,
    "true_comm_mean": round(float(df["true_comm_r"].mean()), 6), "L10_comm": 0.057102,
    "n_costed": int(df["cost_r_TRUE"].notna().sum()),
}}


def arm(mask, label):
    s = df.loc[mask]
    n = len(s)
    return {"label": label, "n": n, "keep_rate": round(n / N, 5),
            "GROSS": round(float(s["H"].mean()), 6),
            "cost_frozen": round(float(s["cost_r"].mean()), 6),
            "cost_div73": round(float(s["cost_r_d73"].mean()), 6),
            "cost_TRUE": round(float(s["cost_r_TRUE"].mean()), 6),
            "NET_at_TRUE": round(float((s["H"] - s["cost_r_TRUE"]).mean()), 6),
            "NET_at_TRUE_per_opportunity": round(float((s["H"] - s["cost_r_TRUE"]).sum() / N), 6)}


OUT["A2_v2_three_gates_ex_past_stop"] = [
    arm(ex, "no gate"),
    arm(ex & gF, "FROZEN gate (shipped)"),
    arm(ex & g73, "FLAT-7.3 corrected gate (what L8/L12 tested)"),
    arm(ex & gT, "PER-SYMBOL broker-true gate (what L5 tested)"),
]
OUT["A2_v2_what_changes"] = {
    "gross_selection_true_minus_frozen": round(
        float(df.loc[ex & gT, "H"].mean() - df.loc[ex & gF, "H"].mean()), 6),
    "net_at_true_true_minus_frozen": round(
        float((df.loc[ex & gT, "H"] - df.loc[ex & gT, "cost_r_TRUE"]).mean()
              - (df.loc[ex & gF, "H"] - df.loc[ex & gF, "cost_r_TRUE"]).mean()), 6),
    "accounting_only_delta_frozen_minus_true_cost_on_same_rows": round(
        float((df.loc[ex & gF, "cost_r"] - df.loc[ex & gF, "cost_r_TRUE"]).mean()), 6),
    "note": "the third number is pure re-accounting: same rows, same trades, same broker bill",
}
# per-symbol scramble, verified independently
psym = []
for s, g in df.groupby("symbol"):
    if g["cost_r_TRUE"].isna().all():
        continue
    psym.append({"symbol": s, "n": len(g),
                 "frozen_spread_med": round(float(g["spread_r"].median()), 6),
                 "true_spread_med": round(float(g["true_spread_r"].median()), 6),
                 "ratio": round(float(g["spread_r"].median() / g["true_spread_r"].median()), 3),
                 "min_frozen_spread_r": round(float(g["spread_r"].min()), 5),
                 "impossible_under_0.10_cap": bool(g["spread_r"].min() > 0.10),
                 "gross_H": round(float(g["H"].mean()), 5)})
psym.sort(key=lambda r: -r["ratio"])
OUT["per_symbol_scramble"] = psym

json.dump(OUT, open(f"{D}/E_REALCOST_V1.json", "w"), indent=1)
print(json.dumps(OUT["validation_vs_L10"]))
for a in OUT["A2_v2_three_gates_ex_past_stop"]:
    print(f"{a['label']:46s} n={a['n']:6d} GROSS={a['GROSS']:+.5f} costTRUE={a['cost_TRUE']:.4f} NET@TRUE={a['NET_at_TRUE']:+.5f} perOpp={a['NET_at_TRUE_per_opportunity']:+.5f}")
print(json.dumps(OUT["A2_v2_what_changes"]))
print("impossible symbols:", [p["symbol"] for p in psym if p["impossible_under_0.10_cap"]])
