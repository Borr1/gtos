"""Apply AR-3's own maxbars lesson to AR-2's winner. Consistency, not courtesy."""
import json,gzip,sys,collections,statistics,importlib.util
from pathlib import Path
REPO=Path('.').resolve(); sys.path.insert(0,str(REPO))
AUD=REPO/"docs/audits/fable5-vision-audit-20260725"
def _load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); sys.modules[n]=m; s.loader.exec_module(m); return m
AD=_load(AUD/"phase7/receipts/ad_exit_sweep.py","h2_ad")
from src.costs.model import load_broker_true_costs
costs=load_broker_true_costs(AD.COSTS); series,index,_=AD.load_bars(); rule=AD.resolve_rule("FTMO-Server3")
af=json.load(gzip.open(AUD+'/phase7/receipts/AF_FAMILY_TRADES.json.gz' if False else AUD/"phase7/receipts/AF_FAMILY_TRADES.json.gz","rt"))
out={}
for m in ("mxf_volume_surge_reversal_us30_cash_d1","mxf_volume_surge_reversal_jp225_d1",
          "mxf_energy_fvg_retest_ukoil_cash_h4"):
    rows=af["trades"].get(m) or []
    for r in rows: r.setdefault("sleeve",m)
    def cen(rs,label):
        er=collections.Counter(r["exit_reason"] for r in rs); n=len(rs)
        h=[r["hold_hours"] for r in rs]
        return {"cell":label,"n":n,"exit_reason":dict(sorted(er.items())),
                "maxbars_frac":round(er.get("maxbars",0)/n,5) if n else None,
                "median_hold_hours":round(statistics.median(h),3),"max_hold_hours":round(max(h),3),
                "mean_r_gross":round(statistics.fmean(r["r_gross"] for r in rs),6)}
    rec=[cen(rows,"as_walked")]
    for cell,kw in (("target_4R",dict(family="target",target_mode="fixed_r",target_r=4.0)),
                    ("target_5R",dict(family="target",target_mode="fixed_r",target_r=5.0))):
        rs,_=AD.resimulate(rows,AD.Variant(name=cell,**kw),series,index,costs,"FTMO",rule)
        rec.append(cen(rs,cell))
    out[m]=rec
    print(m)
    for c in rec:
        flag=" <-- HORIZON-CONFOUNDED" if (c["maxbars_frac"] or 0)>0.25 else ""
        print(f"   {c['cell']:10s} n={c['n']:4d} maxbars {c['maxbars_frac']:.4f} "
              f"median hold {c['median_hold_hours']:8.2f}h max {c['max_hold_hours']:8.1f}h "
              f"gross R {c['mean_r_gross']:+.5f}  {c['exit_reason']}{flag}")
SP='/private/tmp/claude-501/-Users-borr-GTOSActive-worktrees-wave11-conditioning-sizing-20260730/e02391db-fc9f-445c-8371-6708b63399fa/scratchpad'
json.dump(out,open(SP+'/ar2_horizon.json','w'),indent=1)
