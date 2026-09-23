"""Does AR-2's winner survive its own sleeve's LIVE time stop? (25.04 trading hours, 96 M15 bars)"""
import json,gzip,sys,collections,statistics,importlib.util
from pathlib import Path
REPO=Path('/Users/borr/GTOSActive/worktrees/wave11-conditioning-sizing-20260730'); sys.path.insert(0,str(REPO))
AUD=REPO/"docs/audits/fable5-vision-audit-20260725"
def _load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); sys.modules[n]=m; s.loader.exec_module(m); return m
AA=_load(AUD/"phase6/receipts/aa_estate_walk.py","lt_aa"); AD=_load(AUD/"phase7/receipts/ad_exit_sweep.py","lt_ad")
ARP=_load(AUD/"phase11/receipts/ar_repair_program.py","lt_arp")
from src.costs.model import load_broker_true_costs
from src.costs.spread_model import load_spread_model
from src.research_infra.walkforward import candidate_family as CF, run_gate, family as WFAM
from src.research_infra.walkforward.options import OPTIONS
costs=load_broker_true_costs(AD.COSTS); smodel=load_spread_model()
series,index,_=AD.load_bars(); rule=AD.resolve_rule("FTMO-Server3")
fam=CF.load_candidate_family(AUD/"phase11/receipts/CANDIDATE_FAMILY_V4.json")
af=json.load(gzip.open(AUD/"phase7/receipts/AF_FAMILY_TRADES.json.gz","rt"))
M="mxf_volume_surge_reversal_us30_cash_d1"
rows=[dict(r,sleeve=M) for r in af["trades"][M]]
info=af["grid"]["families"]["fam_volume_surge_reversal_index_d1"]
tf=AD.TF_D1
members=[WFAM.FamilyMember(member=WFAM.member_name("volume_surge_reversal",s,tf),
        mechanism_key="volume_surge_reversal",mechanism=info["mechanism"],parent_sleeve=info["parent_sleeve"],
        symbol=s,broker_symbol=s,timeframe=tf,asset_class=info["asset_class"],is_authored_cell=True,
        profile_supported=True) for s in info["symbols"]]
allow={M:(rows[0]["symbol"],)}
o=OPTIONS["B_balanced"]
def gate(variant,label):
    rs = rows if variant is None else AD.resimulate(rows,variant,series,index,costs,"FTMO",rule)[0]
    er=collections.Counter(r["exit_reason"] for r in rs)
    med=statistics.median(r["hold_hours"] for r in rs)
    recs={M:AD.to_records(rs)}
    kept,mix=ARP._restrict(recs,"RECORDED",smodel,"mid")
    spec=o.with_(spec_id=f"{o.spec_id}_ar_livets",sleeve_symbol_allowlist=allow,spread_band="mid")
    spec=CF.with_declared_family(spec,"CANDIDATE_BOOK_V1",loaded=fam)
    with WFAM.fidelity_scope(members):
        res=run_gate(kept,spec,costs=costs,server="FTMO-Server3")
    sv=res.verdicts.get(M)
    print(f"  {label:44s} n={sv.n_trades:4d} R/day={sv.pooled_oos_mean_r:+.5f} p={sv.p_raw:.5f} "
          f"{sv.verdict.value:6s} fail={[x for x in ('expectancy','lifetime','stability','robustness','significance') if not sv.gates.get(x,{}).get('pass')]}")
    print(f"       exits={dict(er)}  median hold={med:.1f}h")
    return sv.pooled_oos_mean_r, sv.p_raw
V=AD.Variant
print("PUBLISHED (no live time stop):")
a5,_=gate(V(name="target_5R",family="target",target_mode="fixed_r",target_r=5.0),"target_5R")
aw,_=gate(None,"as_walked")
print(f"       target_5R / as_walked = {a5/aw:.3f}x")
print()
print("WITH THE SLEEVE'S LIVE TIME STOP (96 M15 bars = 1 D1 bar = 25.04 trading h):")
b5,_=gate(V(name="target_5R_ts",family="target",target_mode="fixed_r",target_r=5.0,time_stop_bars=1),"target_5R + live ts")
bw,_=gate(V(name="as_walked_ts",family="cross_stop_target_timestop",stop_mult=1.0,target_mode="scales_with_stop",time_stop_bars=1),"as_walked + live ts")
print(f"       target_5R / as_walked = {b5/bw:.3f}x")
print()
print(f"target_5R: {a5:+.5f} -> {b5:+.5f}  ({(b5/a5-1)*100:+.1f}%)")
