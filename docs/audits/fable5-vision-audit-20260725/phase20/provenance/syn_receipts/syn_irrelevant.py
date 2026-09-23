"""SYNTHESIS — the IRRELEVANT-BY-CONSTRUCTION union, per family, whole population.

Borhen: "a lot of what we generate is already irrelevant". This puts one number on it,
per family, with every reason disjointly attributed and the UNION reported, so the
fractions do not double-count.

Four reasons, each decidable AT THE MOMENT OF GENERATION without seeing a single
future bar:
  R1 off_session   route_session == off_configured_session -> hard reject,
                   selector_v4.py:2553-2570 (agent_config.yaml:816-817)
  R2 past_stop     limit order whose stop is already breached by the decision close
  R3 target_through limit order whose reward (rr x risk) is already behind the market
  R4 stale_bar     priced against a bar that closed > 15 min before the decision instant

Method reuses r2_measure's fill_gap_R and selected-bar recovery verbatim
(phase20/receipts/r2/r2_measure.py) and adds the session flag from
v4_timewarp_simulated_live_research_loop.derive_session. No sampling.
"""
from __future__ import annotations
import bisect, csv, glob, gzip, json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta

REPO="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
sys.path.insert(0,REPO)
from src.research_infra.v4_timewarp_simulated_live_research_loop import derive_session

BARS=("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
      "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/"
      "bridge_ftmo_m15_20250601_20260610")
ROSTERS={"202510":"/tmp/f1/roster_202510","202511":"/tmp/f1/roster_202511",
         "202512":"/tmp/f1/roster_202512","202601":"/tmp/d4/rosters/202601",
         "202602":"/tmp/d4/rosters/202602","202603":"/tmp/d4/rosters/202603",
         "202604":"/tmp/f1/roster_202604","202605":"/tmp/f1/roster_202605"}
RR=1.5
POI={"current_fvg_fill","current_ob_retest","current_breaker_re_entry"}

def load_series():
    out={}
    for p in sorted(glob.glob(os.path.join(BARS,"*_M15.csv"))):
        sym=os.path.basename(p)[:-len("_M15.csv")]; rows=[]
        with open(p,newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append((datetime.fromisoformat(r["time"]).replace(tzinfo=None),float(r["close"])))
        rows.sort(); out[sym]=([r[0] for r in rows],[r[1] for r in rows])
    return out

SER=load_series()
print("series",len(SER),flush=True)

F=defaultdict(lambda: defaultdict(int))
seen_global=set()
for win,indir in sorted(ROSTERS.items()):
    seen=set()
    for p in sorted(glob.glob(os.path.join(indir,"pbg_*.jsonl.gz"))):
        with gzip.open(p,"rt") as fh:
            for line in fh:
                r=json.loads(line)
                if r["k"]!=15: continue
                fam=r["f"]; sym=r["s"]
                key=(sym,r["t"],fam,r["d"],round(float(r["e"]),8),round(float(r["sl"]),8))
                if key in seen: continue
                seen.add(key)
                e=float(r["e"]); sl=float(r["sl"])
                risk=abs(e-sl)
                if risk<=0 or e<=0: continue
                c=F[fam]; c["n"]+=1
                T=datetime.fromisoformat(r["t"]).replace(tzinfo=None)
                # R1
                off = derive_session(sym,datetime.fromisoformat(r["t"]))=="off_configured_session"
                # R4 + selected bar close
                cp=None; age=None
                s=SER.get(sym)
                if s is not None:
                    times,closes=s
                    i=bisect.bisect_right(times,T+timedelta(seconds=2)-timedelta(minutes=15))-1
                    if i>=0:
                        cp=closes[i]; age=(T-(times[i]+timedelta(minutes=15))).total_seconds()/60.0
                stale = (age is not None and age>0.0)
                sgn = 1.0 if r["d"]=="L" else -1.0   # roster encodes L/S, not LONG/SHORT (r2_measure.py:143)
                past=False; thru=False
                if cp is not None and fam in POI:
                    gap=(cp-e)/risk*sgn
                    if gap< -1.0: past=True
                    elif gap>=RR: thru=True
                if off: c["r1_off"]+=1
                if past: c["r2_past_stop"]+=1
                if thru: c["r3_target_through"]+=1
                if stale: c["r4_stale"]+=1
                if off or past or thru or stale: c["union"]+=1
                if not (off or past or thru or stale): c["clean"]+=1
                # disjoint attribution, priority R2>R3>R1>R4
                if past: c["only_past"]+=1
                elif thru: c["only_thru"]+=1
                elif off: c["only_off"]+=1
                elif stale: c["only_stale"]+=1

out={"schema":"syn_irrelevant_by_construction_v1",
 "population":"eight-window close-only roster (2025-10..2026-03, 2026-04, 2026-05), k==15, deduped on (sym,t,family,dir,entry,sl)",
 "reasons":{"R1":"off_configured_session -> hard reject selector_v4.py:2553-2570",
            "R2":"limit already past its own stop at the decision close",
            "R3":"limit whose rr x risk reward is already behind the market at the decision close",
            "R4":"priced against a bar that closed before the decision instant (stale)"},
 "rr":RR,"families":{}}
tot=defaultdict(int)
print(f"{'family':34s} {'n':>8s} {'R1off':>7s} {'R2past':>7s} {'R3thru':>7s} {'R4stale':>7s} {'UNION':>7s} {'clean':>7s}")
for fam,c in sorted(F.items(),key=lambda x:-x[1]["n"]):
    n=c["n"]; row={k:v for k,v in c.items()}
    row["union_share"]=c["union"]/n; row["clean_n"]=c["clean"]; row["clean_share"]=c["clean"]/n
    for k in ("r1_off","r2_past_stop","r3_target_through","r4_stale"): row[k+"_share"]=c[k]/n
    out["families"][fam]=row
    for k,v in c.items(): tot[k]+=v
    print(f"{fam:34s} {n:8d} {c['r1_off']/n:7.4f} {c['r2_past_stop']/n:7.4f} {c['r3_target_through']/n:7.4f} {c['r4_stale']/n:7.4f} {c['union']/n:7.4f} {c['clean']/n:7.4f}")
n=tot["n"]
out["pool"]={k:v for k,v in tot.items()}; out["pool"]["union_share"]=tot["union"]/n; out["pool"]["clean_share"]=tot["clean"]/n
print(f"{'POOL':34s} {n:8d} {tot['r1_off']/n:7.4f} {tot['r2_past_stop']/n:7.4f} {tot['r3_target_through']/n:7.4f} {tot['r4_stale']/n:7.4f} {tot['union']/n:7.4f} {tot['clean']/n:7.4f}")
json.dump(out,open("syn_receipts/SYN_IRRELEVANT_V1.json","w"),indent=1)
print("written")
