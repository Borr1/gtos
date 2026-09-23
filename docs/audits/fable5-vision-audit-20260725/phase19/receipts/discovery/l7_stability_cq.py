#!/usr/bin/env python3
"""l7_stability_cq — within-January stability, per-symbol table, and the explicit CQ cross-check."""
import gzip, json, os, collections, random
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in gzip.open(os.path.join(HERE, "l7_BASE.jsonl.gz"), "rt")]
rows = [r for r in rows if r["orig_atm_r"] is not None]
for r in rows:
    r["info"] = (r["inv_atm_r"] - r["orig_atm_r"]) / 2.0
    r["day"] = r["decision_time_utc"][:10]
CLEAN = [r for r in rows if r["born_state"] == "born_at_limit"]
mean = lambda v: sum(v)/len(v) if v else float("nan")
res = {}
# --- A. stability: by week and by half
days = sorted({r["day"] for r in CLEAN})
half = days[len(days)//2]
tab = []
for lab, sel in [("H1 %s..%s" % (days[0], half), lambda r: r["day"] < half),
                 ("H2 %s..%s" % (half, days[-1]), lambda r: r["day"] >= half)]:
    v = [r for r in CLEAN if sel(r)]
    tab.append(dict(split=lab, n=len(v), orig=mean([r["orig_atm_r"] for r in v]),
        inv=mean([r["inv_atm_r"] for r in v]), info=mean([r["info"] for r in v])))
wk = collections.defaultdict(list)
for r in CLEAN: wk[r["day"][:8] + ("0" if int(r["day"][8:]) <= 7 else "1" if int(r["day"][8:]) <= 14 else "2" if int(r["day"][8:]) <= 21 else "3")].append(r)
for k, v in sorted(wk.items()):
    tab.append(dict(split="week " + k, n=len(v), orig=mean([r["orig_atm_r"] for r in v]),
        inv=mean([r["inv_atm_r"] for r in v]), info=mean([r["info"] for r in v])))
dd = collections.defaultdict(list)
for r in CLEAN: dd[r["day"]].append(r["info"])
daily = [(k, len(v), mean(v)) for k, v in sorted(dd.items())]
res["stability"] = dict(splits=tab, daily=[dict(day=k, n=n, info=i) for k, n, i in daily],
    days_positive=sum(1 for _, _, i in daily if i > 0), days_total=len(daily))
# --- B. per symbol (CLEAN)
sy = collections.defaultdict(list)
for r in CLEAN: sy[r["symbol"]].append(r)
res["by_symbol"] = sorted([dict(symbol=k, n=len(v), orig=mean([r["orig_atm_r"] for r in v]),
    inv=mean([r["inv_atm_r"] for r in v]), info=mean([r["info"] for r in v]),
    orig_win=sum(1 for r in v if r["orig_atm_r"] > 1e-9)/len(v),
    rd_pct_med=sorted(r["rd_pct"] for r in v)[len(v)//2]) for k, v in sy.items() if len(v) >= 40],
    key=lambda x: -x["info"])
# --- C. CQ cross-check
cq = [json.loads(l) for l in gzip.open("docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz", "rt")]
bycid = collections.defaultdict(list)
for r in rows: bycid[r["candidate_id"]].append(r)
key = "source_candidate_id" if "source_candidate_id" in cq[0] else [k for k in cq[0] if "candidate" in k][0]
m = collections.Counter(); matched = []
for t in cq:
    v = bycid.get(t.get(key))
    if not v: m["unmatched"] += 1; continue
    m["matched"] += 1; matched.append((t, v[0]))
res["cq"] = dict(n_cq=len(cq), join_key=key, **dict(m),
    born_mix=dict(collections.Counter(b["born_state"] for _, b in matched)),
    at_limit_share=sum(1 for _, b in matched if b["born_state"] == "born_at_limit")/max(1, len(matched)),
    cq_rows_in_clean_population=sum(1 for _, b in matched if b["born_state"] == "born_at_limit"),
    inv_atm_on_cq=mean([b["inv_atm_r"] for _, b in matched]),
    inv_atm_on_cq_past_stop=mean([b["inv_atm_r"] for _, b in matched if b["born_state"] == "born_past_stop"]),
    inv_blind_on_cq_past_stop=mean([b["inv_blind_r"] for _, b in matched if b["born_state"] == "born_past_stop"]),
    inv_honest_on_cq_past_stop=mean([b["inv_honest_r"] for _, b in matched if b["born_state"] == "born_past_stop"]))
# breaker family in CLEAN population?
res["breaker_in_clean"] = sum(1 for r in CLEAN if r["family"] == "current_breaker_re_entry")
json.dump(res, open(os.path.join(HERE, "L7_STAB_CQ_V1.json"), "w"), indent=1)
print("=== A. WITHIN-JANUARY STABILITY (CLEAN at-market) ===")
for t in res["stability"]["splits"]:
    print(f"  {t['split']:26s} n={t['n']:5d} origATM {t['orig']:+.4f} invATM {t['inv']:+.4f} INFO {t['info']:+.4f}")
print(f"  daily info positive on {res['stability']['days_positive']}/{res['stability']['days_total']} trading days")
print("\n=== B. per symbol (CLEAN, n>=40) ===")
print(f"{'symbol':12s} {'n':>5s} {'rd%med':>8s} {'origATM':>8s} {'oWin':>6s} {'invATM':>8s} {'INFO':>8s}")
for t in res["by_symbol"]:
    print(f"{t['symbol']:12s} {t['n']:5d} {t['rd_pct_med']:8.4f} {t['orig']:+8.4f} {t['orig_win']:6.1%} {t['inv']:+8.4f} {t['info']:+8.4f}")
print("\n=== C. CQ CROSS-CHECK ===")
c = res["cq"]
print(f"  CQ trades {c['n_cq']}, join key '{c['join_key']}', matched {c.get('matched',0)}, unmatched {c.get('unmatched',0)}")
print(f"  born mix: {c['born_mix']}")
print(f"  CQ rows that sit in THIS lane's CLEAN population: {c['cq_rows_in_clean_population']} ({c['at_limit_share']:.2%})")
print(f"  on CQ's past-stop rows -- inverse BLIND {c['inv_blind_on_cq_past_stop']:+.4f} | inverse HONEST {c['inv_honest_on_cq_past_stop']:+.4f} | inverse AT-MARKET {c['inv_atm_on_cq_past_stop']:+.4f}")
print(f"  current_breaker_re_entry rows in the CLEAN population: {res['breaker_in_clean']}")
