#!/usr/bin/env python3
"""l7_magnet — is the generator's entry level a MAGNET, or is reaching it just diffusion?

Symmetric test on the identical path, decided entirely by decision-time information:
  market sits mkt_r risk-distances away from the level E.
  DOWN-side event : price reaches E                      <=>  adv <= 0        (long convention)
  UP-side  event  : price moves the SAME distance the OTHER way from market
                    i.e. high >= M + mkt_r*d = E + 2*mkt_r*d  <=>  fav >= 2*mkt_r
Under symmetric diffusion these two have equal probability. Any excess of the first is a
magnet, measured with no look-ahead and no model.
"""
import gzip, json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); import w0_ws
base = {}
for l in gzip.open(os.path.join(HERE, "l7_BASE.jsonl.gz"), "rt"):
    r = json.loads(l); base[(r["candidate_id"], r["decision_time_utc"])] = r
mean = lambda v: sum(v)/len(v) if v else float("nan")
recs = []
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"]); b = base.get(k)
    if b is None or b["mkt_r_prev_close"] is None: continue
    m = b["mkt_r_prev_close"]
    if m <= 0: continue                      # only meaningful when a real gap to the level exists
    fav, adv = rp["fav"], rp["adv"]
    down = any(a <= 1e-12 for a in adv)      # reached the level
    up   = any(f >= 2*m - 1e-12 for f in fav)  # same distance the other way from market
    bd = next((i+1 for i,a in enumerate(adv) if a <= 1e-12), None)
    bu = next((i+1 for i,f in enumerate(fav) if f >= 2*m - 1e-12), None)
    recs.append(dict(m=m, down=down, up=up, bd=bd, bu=bu, fam=b["family"], sym=b["symbol"],
                     side=b["side"], sess=b["route_session"], orig_h=b["orig_honest_r"],
                     inv_atm=b["inv_atm_r"], first=b["is_first_emission"]))
def blk(v, lab):
    if len(v) < 20: return None
    d = sum(1 for x in v if x["down"])/len(v); u = sum(1 for x in v if x["up"])/len(v)
    bd = [x["bd"] for x in v if x["bd"]]; bu = [x["bu"] for x in v if x["bu"]]
    return dict(label=lab, n=len(v), p_reach_level=d, p_symmetric_control=u, magnet_ratio=(d/u if u else None),
                excess=d-u, median_bars_to_level=(sorted(bd)[len(bd)//2] if bd else None),
                median_bars_to_control=(sorted(bu)[len(bu)//2] if bu else None),
                orig_after_fill=mean([x["orig_h"] for x in v]), inv_atm=mean([x["inv_atm"] for x in v]))
out = {"ALL_resting": blk(recs, "ALL_resting"), "buckets": [], "by_family": [], "by_side": [], "by_session": []}
for lo, hi in [(0,0.5),(0.5,1),(1,2),(2,3),(3,5),(5,99)]:
    b = blk([x for x in recs if lo < x["m"] <= hi], f"mkt_r ({lo},{hi}]")
    if b: out["buckets"].append(b)
for kf, tgt in (("fam","by_family"),("side","by_side"),("sess","by_session")):
    g = collections.defaultdict(list)
    for x in recs: g[x[kf]].append(x)
    for k, v in g.items():
        b = blk(v, k)
        if b: out[tgt].append(b)
    out[tgt].sort(key=lambda z: -z["n"])
json.dump(out, open(os.path.join(HERE, "L7_MAGNET_V1.json"), "w"), indent=1)
a = out["ALL_resting"]
print(f"RESTING population n={a['n']}:  P(price reaches the level) = {a['p_reach_level']:.4%}")
print(f"                              P(same distance the other way) = {a['p_symmetric_control']:.4%}")
print(f"                              MAGNET RATIO = {a['magnet_ratio']:.3f}x   excess = {a['excess']:+.4%}")
print(f"   median bars to level {a['median_bars_to_level']}  vs control {a['median_bars_to_control']}")
print(f"   R after the fill (honest walk) {a['orig_after_fill']:+.4f}   at-market inverse {a['inv_atm']:+.4f}")
print("\n=== by mkt_r bucket ===")
print(f"{'bucket':>16s} {'n':>6s} {'P(level)':>9s} {'P(ctrl)':>9s} {'ratio':>6s} {'barsLvl':>8s} {'barsCtl':>8s} {'afterFill':>10s} {'invATM':>8s}")
for b in out["buckets"]:
    print(f"{b['label']:>16s} {b['n']:6d} {b['p_reach_level']:9.2%} {b['p_symmetric_control']:9.2%} {b['magnet_ratio']:6.2f} "
          f"{str(b['median_bars_to_level']):>8s} {str(b['median_bars_to_control']):>8s} {b['orig_after_fill']:+10.4f} {b['inv_atm']:+8.4f}")
print("\n=== by family (resting only) ===")
print(f"{'family':34s} {'n':>6s} {'P(level)':>9s} {'P(ctrl)':>9s} {'ratio':>6s} {'afterFill':>10s} {'invATM':>8s}")
for b in out["by_family"]:
    print(f"{b['label']:34s} {b['n']:6d} {b['p_reach_level']:9.2%} {b['p_symmetric_control']:9.2%} {b['magnet_ratio']:6.2f} {b['orig_after_fill']:+10.4f} {b['inv_atm']:+8.4f}")
