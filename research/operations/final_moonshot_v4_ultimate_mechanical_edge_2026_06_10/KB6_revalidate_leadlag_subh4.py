"""KB6 (track: deepen_forward) — convert the FORWARD-ONLY sub-H4 lead-lag edges to a REAL
TRAIN<=2024 split, using newly-exported DEEP index/AUDJPY M15.

KB5_leadlag_subh4 found strong sub-H4 (M15) session-gated lead-lag edges but flagged that the
index & AUDJPY followers' M15 only existed 2025-06+ on disk -> those edges were FORWARD-ONLY
(US30->GER40, USDJPY->AUDJPY, US30->AUDJPY, GER40->UK100, US30->USDJPY, NAS100->GER40,...).
The BROKER actually serves deep M15: GER40 2018-03, UK100 2017-12, US30 2019-02, AUDJPY 2014-01
(probed). We exported bridge_ftmo_idx_m15_backfill_2017_2025 (GER40/UK100/US30/AUDJPY).

This re-validation PREPENDS the deep dir to the KB5 engine's _M15_DIRS and re-runs the EXACT
mine_pair / split_stats / null_test / self_gated (leader-vs-follower falsification) on the
forward-only relations -> now with genuine TRAIN(<=2024). Doctrine: engine imported unchanged;
TRAIN<=2024 -> FORWARD per-year + n; perm-null; leader-vs-self falsification; distrust forward-only;
delete nothing.
"""
from __future__ import annotations
import sys, os, json
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
import KB5_leadlag_subh4 as ll
DATA = os.path.dirname(os.path.dirname(os.path.dirname(HERE))) + "/data/mt5_research_exports"
DEEPIDX = DATA + "/bridge_ftmo_idx_m15_backfill_2017_2025"

# PREPEND the deep idx/audjpy M15 dir so load_m15 unions it (deepest-first, dedupe by ts).
if DEEPIDX not in ll._M15_DIRS:
    ll._M15_DIRS.insert(0, DEEPIDX)
ll._M15_CACHE.clear()

GEOMS = ll.GEOMS

# The forward-only sub-H4 head edges from KB5 (now testable on deep follower M15).
# (name, leader, follower, relsign, look, zthr, thesis, geom, sess, regime)
EDGES = [
    ("US30->GER40 [ny_open]",      "US30_cash","GER40", +1, 8, 1.5,"momentum","TRAIL","ny_open", None),
    ("USDJPY->AUDJPY [london_ny]", "USDJPY","AUDJPY",   +1, 8, 2.5,"momentum","T2.0","london_ny", None),
    ("GER40->UK100 [london_open]", "GER40","UK100",     +1, 2, 2.0,"reversion","TRAIL","london_open", None),
    ("US30->USDJPY [ny_open]",     "US30_cash","USDJPY",+1, 4, 2.0,"momentum","T2.0","ny_open", None),
    ("US30->AUDJPY [ny_open] rev", "US30_cash","AUDJPY",+1, 8, 1.5,"reversion","T2.0","ny_open", None),
    ("US30->GER40 [ny_open] L8z2", "US30_cash","GER40", +1, 8, 2.0,"momentum","T2.0","ny_open", None),
    ("GER40->UK100 [london] z2 rev","GER40","UK100",    +1, 8, 2.0,"reversion","T1.5","london_open", None),
]

def coverage(sym):
    pf=ll.load_m15(sym)
    t=pf["times"]
    if not t: return dict(n=0)
    return dict(n=len(t), first=t[0].isoformat(), last=t[-1].isoformat())

def run_edge(name, leader, follower, relsign, look, zthr, thesis, gname, sess, regime):
    geom=GEOMS[gname]
    tr = ll.mine_pair(leader,follower,relsign,look,zthr,thesis,geom,sess=sess,regime=regime)
    sp = ll.split_stats(tr)
    nz = ll.null_test(leader,follower,relsign,look,zthr,thesis,geom,sess=sess,regime=regime,reps=20)
    # leader-vs-self falsification (does the leader add over the follower's OWN move?)
    self_tr = ll.self_gated(follower,relsign,look,zthr,thesis,geom,sess=sess)
    self_sp = ll.split_stats(self_tr)
    leader_adds_fwd = round(sp["forward"]["R"] - self_sp["forward"]["R"],4)
    leader_adds_train = round(sp["train"]["R"] - self_sp["train"]["R"],4)
    holds = (sp["train"]["n"]>=40 and sp["train"]["R"]>0 and
             sp["forward"]["n"]>=40 and sp["forward"]["R"]>0)
    return dict(name=name, leader=leader, follower=follower, cfg=dict(look=look,z=zthr,thesis=thesis,geom=gname,sess=sess,regime=regime),
                train=sp["train"], forward=sp["forward"], fwd_h1=sp["fwd_h1"], fwd_h2=sp["fwd_h2"],
                per_year=sp["per_year"], null_z=nz.get("z"), null_mean=nz.get("null_mean"),
                self_train=self_sp["train"], self_forward=self_sp["forward"],
                leader_adds_train=leader_adds_train, leader_adds_fwd=leader_adds_fwd,
                holds_train_forward=bool(holds))

def main():
    out={"coverage":{s:coverage(s) for s in ["GER40","UK100","US30_cash","AUDJPY","USDJPY"]}, "edges":{}}
    print("COVERAGE (after deep idx M15 union):")
    for s,c in out["coverage"].items(): print(f"  {s}: {c}")
    for e in EDGES:
        r=run_edge(*e); out["edges"][e[0]]=r
        py=" ".join(f"{y}:{v['R']:+.3f}(n{v['n']})" for y,v in r["per_year"].items())
        print(f"\n== {r['name']} ==")
        print(f"  TRAIN<=2024 R={r['train']['R']:+.4f}(n{r['train']['n']})  FWD R={r['forward']['R']:+.4f}(n{r['forward']['n']}) "
              f"[h1 {r['fwd_h1']['R']:+.3f} h2 {r['fwd_h2']['R']:+.3f}]")
        print(f"  null_z={r['null_z']}  leader_adds TRAIN={r['leader_adds_train']:+.3f} FWD={r['leader_adds_fwd']:+.3f} "
              f"(self TRAIN {r['self_train']['R']:+.3f}/FWD {r['self_forward']['R']:+.3f})")
        print(f"  per-year: {py}")
        print(f"  HOLDS train+forward (nTR>=40,TR>0,FWD>0): {r['holds_train_forward']}")
    p=os.path.join(HERE,"KB6_LEADLAG_SUBH4_REVAL_RESULT.json")
    json.dump(out, open(p,"w"), indent=1, default=str)
    print(f"\nwrote {p}")

if __name__=="__main__":
    main()
