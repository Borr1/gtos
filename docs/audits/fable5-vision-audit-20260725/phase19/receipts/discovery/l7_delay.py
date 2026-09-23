#!/usr/bin/env python3
"""l7_delay — how fast does the inversion decay with entry latency? UNAMBIGUOUS construction:
enter at the CLOSE of path bar k (a price fully known at the end of bar k) and walk bars k+1..120.
k=0 means enter at mkt_r_prev_close (the decision instant) and walk bars 1..120 -- the headline.
Everything is in the same R units with the same risk distance d, and orig/inv stay exact mirrors."""
import gzip, json, os, sys, collections, random, math
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); import w0_ws
base = {}
for l in gzip.open(os.path.join(H, "l7_BASE.jsonl.gz"), "rt"):
    r = json.loads(l); base[(r["candidate_id"], r["decision_time_utc"])] = r
def walk(fav, adv, cls, s, t=2.0, st=-1.0):
    for i in range(s, len(fav)):
        if adv[i] <= st + 1e-12: return st
        if fav[i] >= t - 1e-12: return t
    return cls[-1] if len(cls) > s else 0.0
DELAYS = [0, 1, 2, 3, 5, 10, 15, 30, 60]
acc = {k: collections.defaultdict(list) for k in DELAYS}
for rp in w0_ws.iter_rpaths():
    b = base.get((rp["candidate_id"], rp["decision_time_utc"]))
    if b is None or b["mkt_r_prev_close"] is None or b["born_state"] != "born_at_limit": continue
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(fav)
    for k in DELAYS:
        if k == 0: m = b["mkt_r_prev_close"]; s = 0
        else:
            if k > n - 2: continue
            m = cls[k-1]; s = k          # price at the END of bar k == cls[k-1]; walk bars k+1.. (index k..)
        fa = [x - m for x in fav]; aa = [x - m for x in adv]; ca = [x - m for x in cls]
        o = walk(fa, aa, ca, s)
        i_ = walk([-x for x in aa], [-x for x in fa], [-x for x in ca], s)
        acc[k]["o"].append(o); acc[k]["i"].append(i_); acc[k]["d"].append(b["decision_time_utc"][:10])
mean = lambda v: sum(v)/len(v)
res = []
for k in DELAYS:
    o, i_, dd = acc[k]["o"], acc[k]["i"], acc[k]["d"]
    info = [(a-b)/2 for a, b in zip(i_, o)]
    byday = collections.defaultdict(list)
    for day, x in zip(dd, info): byday[day].append(x)
    rnd = random.Random(4); days = list(byday); bs = []
    for _ in range(1000):
        s = []
        for _ in range(len(days)): s.extend(byday[rnd.choice(days)])
        bs.append(mean(s))
    bs.sort()
    sd = (sum((x-mean(info))**2 for x in info)/(len(info)-1))**.5
    res.append(dict(delay_min=k, n=len(o), orig=mean(o), inv=mean(i_), info=mean(info),
        t_naive=mean(info)/(sd/math.sqrt(len(info))), boot_lo=bs[25], boot_hi=bs[975],
        p_le0=sum(1 for x in bs if x <= 0)/1000))
json.dump(res, open(os.path.join(H, "L7_DELAY_V2.json"), "w"), indent=1)
print("ENTRY-LATENCY DECAY, CLEAN born_at_limit population (enter at close of bar k, walk k+1..120)")
print(f"{'delay(min)':>10s} {'n':>6s} {'orig@mkt':>9s} {'inv@mkt':>9s} {'INFO':>8s} {'boot95lo':>9s} {'boot95hi':>9s} {'p<=0':>6s} {'t':>6s}")
for t in res:
    print(f"{t['delay_min']:10d} {t['n']:6d} {t['orig']:+9.4f} {t['inv']:+9.4f} {t['info']:+8.4f} {t['boot_lo']:+9.4f} {t['boot_hi']:+9.4f} {t['p_le0']:6.3f} {t['t_naive']:6.2f}")
