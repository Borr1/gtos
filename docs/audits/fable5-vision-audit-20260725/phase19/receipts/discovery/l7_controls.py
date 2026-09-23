#!/usr/bin/env python3
"""l7_controls — the two controls that decide whether the at-market inversion is real.

C1 LATENCY: re-enter at the close of the decision-minute bar (mkt_r_close). Zero staleness --
   that price is where the path itself starts -- and still zero look-ahead on the outcome.
C2 MARKET DRIFT: the inversion statistic could be pure January drift if the signal book is
   side-imbalanced. delta = (short_at_market_r - long_at_market_r)/2 is a pure PRICE-DIRECTION
   quantity that does not know the signal. Any common drift mu sits in delta identically for
   LONG-signalled and SHORT-signalled rows, so
        info_clean = ( E[delta | signal LONG] - E[delta | signal SHORT] ) / 2
   is drift-free by construction. If the signal carries inverted information, delta must be
   HIGHER when the signal says LONG.
"""
import gzip, json, os, collections, random
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in gzip.open(os.path.join(HERE, "l7_BASE.jsonl.gz"), "rt")]
rows = [r for r in rows if r["orig_atm_r"] is not None]
for r in rows:
    r["info"] = (r["inv_atm_r"] - r["orig_atm_r"]) / 2.0
    r["info_lag1"] = (r["inv_atm_lag1_r"] - r["orig_atm_lag1_r"]) / 2.0
    long_r  = r["orig_atm_r"] if r["side"] == "LONG" else r["inv_atm_r"]
    short_r = r["inv_atm_r"]  if r["side"] == "LONG" else r["orig_atm_r"]
    r["long_atm_r"], r["short_atm_r"] = long_r, short_r
    r["delta"] = (short_r - long_r) / 2.0
    r["day"] = r["decision_time_utc"][:10]
mean = lambda v: sum(v)/len(v) if v else float("nan")

def dayboot(v, fn, B=2000, seed=11):
    rnd = random.Random(seed); byday = collections.defaultdict(list)
    for r in v: byday[r["day"]].append(r)
    days = list(byday)
    out = []
    for _ in range(B):
        s = []
        for _ in range(len(days)): s.extend(byday[rnd.choice(days)])
        out.append(fn(s))
    out.sort()
    return dict(obs=fn(v), lo=out[int(.025*B)], hi=out[int(.975*B)],
                p_le0=sum(1 for x in out if x <= 0)/B, n_days=len(days))

def info_clean(v):
    L = [r["delta"] for r in v if r["side"] == "LONG"]
    S = [r["delta"] for r in v if r["side"] == "SHORT"]
    if not L or not S: return float("nan")
    return (mean(L) - mean(S)) / 2.0

res = {}
POPS = {
 "ALL": rows,
 "GEOMETRY_FREE_at_limit": [r for r in rows if r["born_state"] == "born_at_limit"],
 "GEOMETRY_FREE_absmkt_le2": [r for r in rows if abs(r["mkt_r_prev_close"]) <= 2.0],
 "TRADEABLE_ex_past_stop": [r for r in rows if r["born_state"] != "born_past_stop"],
 "FIRST_EMISSION_at_limit": [r for r in rows if r["born_state"] == "born_at_limit" and r["is_first_emission"]],
}
tab = []
for name, v in POPS.items():
    nl = sum(1 for r in v if r["side"] == "LONG")
    tab.append(dict(pop=name, n=len(v), n_long=nl, long_share=nl/len(v),
        long_atm=mean([r["long_atm_r"] for r in v]), short_atm=mean([r["short_atm_r"] for r in v]),
        drift_delta=mean([r["delta"] for r in v]),
        delta_given_LONGsig=mean([r["delta"] for r in v if r["side"]=="LONG"]),
        delta_given_SHORTsig=mean([r["delta"] for r in v if r["side"]=="SHORT"]),
        info=mean([r["info"] for r in v]),
        info_lag1=mean([r["info_lag1"] for r in v]),
        info_clean=info_clean(v),
        boot_info=dayboot(v, lambda s: mean([r["info"] for r in s])),
        boot_info_lag1=dayboot(v, lambda s: mean([r["info_lag1"] for r in s])),
        boot_info_clean=dayboot(v, info_clean)))
res["controls"] = tab
json.dump(res, open(os.path.join(HERE, "L7_CONTROLS_V1.json"), "w"), indent=1)

print("=== C1 + C2 CONTROLS ===")
print(f"{'population':26s} {'n':>6s} {'L%':>6s} {'longATM':>8s} {'shortATM':>8s} {'INFO':>8s} {'95lo':>8s} {'INFOlag1':>9s} {'95lo':>8s} {'INFOclean':>9s} {'95lo':>8s} {'p<=0':>6s}")
for t in res["controls"]:
    print(f"{t['pop']:26s} {t['n']:6d} {t['long_share']:6.1%} {t['long_atm']:+8.4f} {t['short_atm']:+8.4f} "
          f"{t['info']:+8.4f} {t['boot_info']['lo']:+8.4f} {t['info_lag1']:+9.4f} {t['boot_info_lag1']['lo']:+8.4f} "
          f"{t['info_clean']:+9.4f} {t['boot_info_clean']['lo']:+8.4f} {t['boot_info_clean']['p_le0']:6.3f}")
print("\ndelta = (short_at_market - long_at_market)/2, a pure price-direction quantity:")
for t in res["controls"]:
    print(f"  {t['pop']:26s} delta|LONGsig {t['delta_given_LONGsig']:+.4f}   delta|SHORTsig {t['delta_given_SHORTsig']:+.4f}   "
          f"gap {t['delta_given_LONGsig']-t['delta_given_SHORTsig']:+.4f}   unconditional drift {t['drift_delta']:+.4f}")
