"""l5 item 2+4: decompose the cost refusals and BUILD the money-denominated gate.

Incumbent gate (config/agent_config.yaml:715-716, enforced at
broker_net_cost_engine.py:859-866 and :923-927):
    PASS iff spread_r <= 0.10 AND total_cost_r <= 0.15
Everything else here is an offline scorer. No engine file is touched.
"""
import gzip,json,os,collections,math
DISC="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
rows=[json.loads(l) for l in gzip.open(os.path.join(DISC,"l5_MONEY_TABLE.jsonl.gz"),"rt")]
anch={}
for l in gzip.open(os.path.join(DISC,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt"):
    a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
for r in rows:
    a=anch.get((r["candidate_id"],r["decision_time_utc"])); m=a.get("mkt_r_prev_close") if a else None
    r["born"]=bo(m) if m is not None else "unanchored"
    r["rel_stop"]=r["risk_distance"]/r["entry_price"] if r["entry_price"] else None
    r["gate_R"]= (r["spread_r"] is not None and r["spread_r"]<=0.10 and r["cost_r"] is not None and r["cost_r"]<=0.15)
    tsr=r["true_spread_r"]; ttr=r["true_total_cost_r"]
    r["gate_R_true"]= (tsr is not None and tsr<=0.10 and ttr is not None and ttr<=0.15)
    r["net_true_r"]= (r["gross_r"]-ttr) if (r["gross_r"] is not None and ttr is not None) else None
    r["net_frozen_r"]= (r["gross_r"]-r["cost_r"]) if (r["gross_r"] is not None and r["cost_r"] is not None) else None

def stats(pop,label):
    g=[r["gross_r"] for r in pop if r["gross_r"] is not None]
    nt=[r["net_true_r"] for r in pop if r["net_true_r"] is not None]
    nf=[r["net_frozen_r"] for r in pop if r["net_frozen_r"] is not None]
    fh=[r["fill_honest_walk_r"] for r in pop if r.get("fill_honest_walk_r") is not None]
    dollars=sum((r["gross_r"] or 0)*r["risk_usd"] for r in pop)
    tcost=sum((r["true_total_cost_usd"] or 0) for r in pop)
    fcost=sum((r["cost_usd"] or 0) for r in pop)
    return {"label":label,"n":len(pop),
      "gross_mean_r":round(sum(g)/len(g),5) if g else None,
      "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2) if g else None,
      "net_true_mean_r":round(sum(nt)/len(nt),5) if nt else None,
      "net_frozen_mean_r":round(sum(nf)/len(nf),5) if nf else None,
      "fill_honest_mean_r":round(sum(fh)/len(fh),5) if fh else None,
      "gross_usd_total":round(dollars,0),"true_cost_usd_total":round(tcost,0),
      "frozen_cost_usd_total":round(fcost,0),
      "net_true_usd_total":round(dollars-tcost,0),
      "mean_cost_usd":round(fcost/len(pop),2) if pop else None,
      "mean_true_cost_usd":round(tcost/len(pop),2) if pop else None}

out={}
for popname,pop in (("ALL",rows),("EX_PAST_STOP",[r for r in rows if r["born"]!="born_past_stop"])):
    blk={}
    blk["pool"]=stats(pop,"pool")
    A=[r for r in pop if r["gate_R"]]; Rf=[r for r in pop if not r["gate_R"]]
    blk["gate_R_admit"]=stats(A,"incumbent R-gate ADMIT")
    blk["gate_R_refuse"]=stats(Rf,"incumbent R-gate REFUSE")
    B=[r for r in pop if r["gate_R_true"]]
    blk["gate_Rtrue_admit"]=stats(B,"same thresholds on BROKER-TRUE cost ADMIT")
    blk["gate_Rtrue_refuse"]=stats([r for r in pop if not r["gate_R_true"]],"broker-true REFUSE")
    # 2x2 frozen vs true
    cells=collections.defaultdict(list)
    for r in pop: cells[(r["gate_R"],r["gate_R_true"])].append(r)
    blk["frozen_x_true_2x2"]={f"frozen{'PASS' if k[0] else 'REF'}_true{'PASS' if k[1] else 'REF'}":stats(v,"") for k,v in sorted(cells.items())}
    out[popname]=blk

# --- count-matched alternative gates on EX_PAST_STOP ---
pop=[r for r in rows if r["born"]!="born_past_stop" and r["gross_r"] is not None]
TARGET=sum(1 for r in pop if r["gate_R"])
def matched(key,reverse=False):
    v=[r for r in pop if r.get(key) is not None]
    v.sort(key=lambda r:r[key],reverse=reverse)
    adm=v[:TARGET]
    thr=adm[-1][key] if adm else None
    return adm,[r for r in v if r not in set()] , thr
def take(key,reverse=False,n=None):
    v=sorted([r for r in pop if r.get(key) is not None],key=lambda r:r[key],reverse=reverse)
    n=n or TARGET
    return v[:n],v[n:],(v[n-1][key] if n<=len(v) else None)
alt={}
alt["target_admit_n"]=TARGET
for name,key,rev in (("cost_usd","cost_usd",False),("cost_bp_of_notional","cost_bp_of_notional",False),
                     ("true_total_cost_r","true_total_cost_r",False),("true_total_cost_usd","true_total_cost_usd",False),
                     ("rel_stop_widest","rel_stop",True),("cost_r","cost_r",False)):
    a,rj,thr=take(key,rev)
    alt[name]={"threshold":thr,"admit":stats(a,name+"_admit"),"refuse":stats(rj,name+"_refuse")}
    inc=set(id(r) for r in pop if r["gate_R"])
    aset=set(id(r) for r in a)
    only_new=[r for r in a if id(r) not in inc]
    only_lost=[r for r in pop if r["gate_R"] and id(r) not in aset]
    alt[name]["swap_in"]=stats(only_new,"admitted by "+name+" but NOT by R-gate")
    alt[name]["swap_out"]=stats(only_lost,"admitted by R-gate but NOT by "+name)
out["count_matched_alternatives_EX_PAST_STOP"]=alt

# --- dollar sweep: what does a pure $ ceiling admit? ---
sweep=[]
for T in (25,50,75,100,150,200,300,400,500,750,1000,1500,2000,5000,10**9):
    a=[r for r in pop if r["cost_usd"] is not None and r["cost_usd"]<=T]
    s=stats(a,f"cost_usd<={T}")
    s["threshold_usd"]=T; sweep.append(s)
out["dollar_ceiling_sweep_EX_PAST_STOP"]=sweep
# normalised: dollars per $1000 of risk == cost_r*1000
sweep2=[]
for T in (10,25,50,75,100,150,200,300,500,1000,2000):
    a=[r for r in pop if r["cost_r"] is not None and r["cost_r"]*1000<=T]
    s=stats(a,f"cost_per_1000risk<={T}"); s["usd_per_1000_risk"]=T; sweep2.append(s)
out["cost_per_1000_risk_sweep_EX_PAST_STOP"]=sweep2
sweep3=[]
for T in (10,25,50,75,100,150,200,300,500,1000):
    a=[r for r in pop if r["true_total_cost_r"] is not None and r["true_total_cost_r"]*1000<=T]
    s=stats(a,f"TRUE_cost_per_1000risk<={T}"); s["usd_per_1000_risk"]=T; sweep3.append(s)
out["TRUE_cost_per_1000_risk_sweep_EX_PAST_STOP"]=sweep3
json.dump(out,open(os.path.join(DISC,"l5_GATES_V1.json"),"w"),indent=1)

def line(s): return (f"n {s['n']:6d} gross {str(s['gross_mean_r']):>9s} win {str(s['win_pct']):>6s}% "
                     f"netTRUE {str(s['net_true_mean_r']):>9s} netFROZ {str(s['net_frozen_mean_r']):>9s} "
                     f"cost$ {str(s['mean_cost_usd']):>8s} true$ {str(s['mean_true_cost_usd']):>7s}")
for popname in ("ALL","EX_PAST_STOP"):
    print("### "+popname)
    for k in ("pool","gate_R_admit","gate_R_refuse","gate_Rtrue_admit","gate_Rtrue_refuse"):
        print(f"  {k:20s} {line(out[popname][k])}")
    print("  2x2 frozen x true:")
    for k,v in out[popname]["frozen_x_true_2x2"].items():
        print(f"    {k:26s} {line(v)}")
print("\n### COUNT-MATCHED ALTERNATIVES (ex past-stop, admit exactly %d)"%TARGET)
for name,v in alt.items():
    if name=="target_admit_n": continue
    print(f"  {name:22s} thr {str(round(v['threshold'],6) if v['threshold'] is not None else None):>12s} ADMIT {line(v['admit'])}")
    print(f"  {'':22s} swap_in  {line(v['swap_in'])}")
    print(f"  {'':22s} swap_out {line(v['swap_out'])}")
