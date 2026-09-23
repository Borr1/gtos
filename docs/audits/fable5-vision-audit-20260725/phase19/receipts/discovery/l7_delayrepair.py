#!/usr/bin/env python3
"""l7_delayrepair — the actionable form of the finding: DO NOT flip the direction, just stop
entering at the trigger bar's close. Paired per-row delta vs delay 0, day-block bootstrapped.
Same side, same risk distance, same +2R/-1R, same 120-bar wall. Only the entry instant moves."""
import gzip, json, os, sys, collections, random
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); import w0_ws
base = {}
for l in gzip.open(os.path.join(H, "l7_BASE.jsonl.gz"), "rt"):
    r = json.loads(l); base[(r["candidate_id"], r["decision_time_utc"])] = r
def walk(fav, adv, cls, s, t=2.0, st=-1.0):
    for i in range(s, len(fav)):
        if adv[i] <= st + 1e-12: return st
        if fav[i] >= t - 1e-12: return t
    return cls[-1] if len(cls) > s else 0.0
DELAYS = [0, 1, 2, 3, 5, 10, 15, 30]
rec = []
for rp in w0_ws.iter_rpaths():
    b = base.get((rp["candidate_id"], rp["decision_time_utc"]))
    if b is None or b["mkt_r_prev_close"] is None or b["born_state"] != "born_at_limit": continue
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]; n = len(fav)
    if n < 40: continue
    row = dict(day=b["decision_time_utc"][:10], fam=b["family"], sess=b["route_session"],
               sp=b["spread_r"] or 0.0, cost=b["cost_r"])
    ok = True
    for k in DELAYS:
        m = b["mkt_r_prev_close"] if k == 0 else (cls[k-1] if k <= n-2 else None)
        if m is None: ok = False; break
        fa = [x-m for x in fav]; aa = [x-m for x in adv]; ca = [x-m for x in cls]
        row["d%d" % k] = walk(fa, aa, ca, 0 if k == 0 else k)
    if ok: rec.append(row)
mean = lambda v: sum(v)/len(v)
def db(v, f, B=2000, seed=31):
    rnd = random.Random(seed); d = collections.defaultdict(list)
    for r in v: d[r["day"]].append(r)
    ks = list(d); o = []
    for _ in range(B):
        s = []
        for _ in range(len(ks)): s.extend(d[rnd.choice(ks)])
        o.append(f(s))
    o.sort(); return o[int(.025*B)], o[int(.975*B)], sum(1 for x in o if x <= 0)/B
res = dict(n=len(rec), rungs=[])
for k in DELAYS:
    lvl = mean([r["d%d" % k] for r in rec])
    dl = [r["d%d" % k] - r["d0"] for r in rec]
    lo, hi, p = db(rec, lambda s: mean([x["d%d" % k] - x["d0"] for x in s]))
    net73 = mean([r["d%d" % k] - ((r["cost"]-r["sp"]) + r["sp"]/7.3) for r in rec])
    res["rungs"].append(dict(delay=k, n=len(rec), orig_level=lvl, delta_vs_d0=mean(dl),
        delta_lo=lo, delta_hi=hi, p_le0=p, orig_net73=net73,
        pct_changed=sum(1 for x in dl if abs(x) > 1e-9)/len(dl)))
fam = collections.defaultdict(list)
for r in rec: fam[r["fam"]].append(r)
res["by_family_delay5"] = sorted([dict(family=k, n=len(v), d0=mean([r["d0"] for r in v]),
    d5=mean([r["d5"] for r in v]), delta=mean([r["d5"]-r["d0"] for r in v])) for k, v in fam.items()],
    key=lambda x: -x["delta"])
ses = collections.defaultdict(list)
for r in rec: ses[r["sess"]].append(r)
res["by_session_delay5"] = sorted([dict(session=k, n=len(v), d0=mean([r["d0"] for r in v]),
    d5=mean([r["d5"] for r in v]), delta=mean([r["d5"]-r["d0"] for r in v])) for k, v in ses.items()],
    key=lambda x: -x["delta"])
json.dump(res, open(os.path.join(H, "L7_DELAYREPAIR_V1.json"), "w"), indent=1)
print(f"DELAYED-ENTRY REPAIR, same side, CLEAN born_at_limit, n={res['n']}")
print(f"{'delay':>6s} {'orig level':>11s} {'delta vs d0':>12s} {'95% lo':>8s} {'95% hi':>8s} {'p<=0':>6s} {'orig NET@7.3':>13s} {'% rows moved':>13s}")
for t in res["rungs"]:
    print(f"{t['delay']:6d} {t['orig_level']:+11.4f} {t['delta_vs_d0']:+12.4f} {t['delta_lo']:+8.4f} {t['delta_hi']:+8.4f} "
          f"{t['p_le0']:6.3f} {t['orig_net73']:+13.4f} {t['pct_changed']:13.1%}")
print("\nby family, delay 5 min:")
for t in res["by_family_delay5"]: print(f"  {t['family']:34s} n={t['n']:5d} d0 {t['d0']:+.4f} -> d5 {t['d5']:+.4f}  delta {t['delta']:+.4f}")
print("by session, delay 5 min:")
for t in res["by_session_delay5"]: print(f"  {t['session']:26s} n={t['n']:5d} d0 {t['d0']:+.4f} -> d5 {t['d5']:+.4f}  delta {t['delta']:+.4f}")
