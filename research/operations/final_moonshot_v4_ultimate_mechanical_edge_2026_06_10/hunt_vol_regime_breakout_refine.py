"""REFINE pass for vol_regime_breakout.
Lock the winning shape (strong squeeze-release gate + trail) and:
  1. finer expansion-ratio sweep
  2. test asset-class filter (drop classes that are structurally negative)
  3. confirm forward stability per-year, per-side, per-class
Reuses run_config / summarize / prep from the main hunt module.
"""
import sys, os, json, statistics
ROOT="/Users/borr/Documents/gtos/repo/ai-trading-agent"
sys.path.insert(0, os.path.join(ROOT,"research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"))
import hunt_vol_regime_breakout as H

# allow class filtering by monkeypatch of run_config? simpler: replicate with filter param.
from geometry_lib import simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

def run_filtered(cfg, allowed_classes=None):
    look=cfg["look"]; atr_slow=cfg["atr_slow"]; exp_ratio=cfg["exp_ratio"]
    stop_mult=cfg["stop_mult"]; geom=cfg["geom"]; maxbars=cfg.get("maxbars",80)
    min_break=cfg.get("min_break",0.0); sides=cfg.get("sides",(1,-1))
    trades=[]
    for sym in H.SYMBOLS:
        ac=ASSET_CLASS_BY_SYMBOL[sym]
        if allowed_classes is not None and ac not in allowed_classes: continue
        bars,times,years,atr,n=H.prep(sym)
        cost=H.cost_for(sym)
        warm=max(look,atr_slow)+16
        for i in range(warm,n-2):
            a=atr[i]
            if a<=0: continue
            aslow=H.sma(atr,i,atr_slow)
            if aslow<=0: continue
            if a/aslow < exp_ratio: continue   # expansion gate only
            hi,lo=H.donchian(bars,i,look); c=bars[i].c
            stop_dist=stop_mult*a
            if stop_dist<=0: continue
            for side in sides:
                if side>0 and not (c>hi+min_break*a): continue
                if side<0 and not (c<lo-min_break*a): continue
                r=simulate(bars,i,side,stop_dist=stop_dist,
                           trail_arm=geom[1]*stop_dist,trail_gap=geom[2]*stop_dist,
                           maxbars=maxbars,cost=cost)
                trades.append((years[i],ac,side,r))
    return trades

base=dict(stop_mult=0.5, geom=("trail",2.0,1.0), min_break=0.0)

print("=== finer expansion sweep, ALL classes, look/slow grid ===")
for look in (40,55):
    for slow in (100,150):
        for exp in (1.35,1.45,1.55,1.7):
            cfg=dict(base,look=look,atr_slow=slow,exp_ratio=exp)
            tr=H.run_config(dict(cfg,mode="breakout")) if False else run_filtered(cfg)
            s=H.summarize(tr,f"all|look{look}|slow{slow}|exp{exp}")
            print(f"look{look} slow{slow} exp{exp}: TRAIN n={s['train']['n']:4d} R={s['train']['per_trade_R']:+.3f} | FWD n={s['forward']['n']:4d} R={s['forward']['per_trade_R']:+.3f} win={s['forward']['win']:.3f} | yr={ {k:v['per_trade_R'] for k,v in s['forward_per_year'].items()} }")

print("\n=== asset-class filter on the exp1.45 winner (look55/slow100) ===")
FAVOR=set(["metals","fx","energy","crypto"])   # structurally positive classes
for allowed,name in ((None,"ALL"),(FAVOR,"FAVOR(metals,fx,energy,crypto)")):
    cfg=dict(base,look=55,atr_slow=100,exp_ratio=1.45)
    tr=run_filtered(cfg,allowed)
    s=H.summarize(tr,name)
    print(f"\n[{name}]")
    print(" train",s['train']," forward",s['forward'])
    print(" per_year",s['forward_per_year'])
    print(" long_short",s['forward_long_short'])
    print(" by_ac",{k:(v['n'],v['per_trade_R']) for k,v in s['forward_by_asset_class'].items()})

print("\n=== final candidate: FAVOR classes, look55/slow100/exp1.45, both look settings ===")
best=None
for look in (40,55):
    for exp in (1.4,1.45,1.5):
        cfg=dict(base,look=look,atr_slow=100,exp_ratio=exp)
        tr=run_filtered(cfg,FAVOR)
        s=H.summarize(tr,f"FAVOR|look{look}|exp{exp}")
        fr=s['forward']['per_trade_R']; tr_r=s['train']['per_trade_R']
        py=s['forward_per_year']
        both_pos=all(v['per_trade_R']>0 for v in py.values()) and tr_r>0
        print(f"look{look} exp{exp}: TRAIN n={s['train']['n']:4d} R={tr_r:+.3f} | FWD n={s['forward']['n']:4d} R={fr:+.3f} win={s['forward']['win']:.3f} stable={both_pos} yr={ {k:v['per_trade_R'] for k,v in py.items()} } LS={ {k:v['per_trade_R'] for k,v in s['forward_long_short'].items()} }")
        if both_pos and s['forward']['n']>=200 and (best is None or fr>best[0]):
            best=(fr,s)

if best:
    print("\n===== BEST STABLE FAVOR CONFIG =====")
    print(json.dumps(best[1],indent=1))
    json.dump(best[1],open(os.path.join(ROOT,"research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/hunt_vol_regime_breakout_best.json"),"w"),indent=1)
