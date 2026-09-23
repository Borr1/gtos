import json, collections, math
import l9_lib as L

rows = L.load()
for r in rows:
    en = r.get("expected_net_r"); pb = r.get("candidate_probability")
    fp = r.get("execution_fill_probability"); sc = r.get("source_completeness")
    scv = 1.0
    if isinstance(sc,(int,float)): scv = max(0.0,min(1.0,float(sc)))
    elif sc is True: scv=1.0
    elif sc is False: scv=0.0
    r["_sc"] = scv
    r["_en_clip"] = max(0.0, float(en)) if en is not None else 0.0
    r["_pb"] = max(0.0,min(1.0,float(pb))) if pb is not None else 0.5
    r["_fp"] = max(0.0,min(1.0,float(fp))) if fp is not None else 0.0
    r["transfer_score"] = round(r["_en_clip"]*r["_pb"]*r["_fp"]*r["_sc"], 12)

OUT = {}
OUT["source_completeness_values"] = dict(collections.Counter(str(r.get("source_completeness")) for r in rows).most_common(8))
n=len(rows)
z = sum(1 for r in rows if r["transfer_score"] == 0.0)
en0 = sum(1 for r in rows if (r.get("expected_net_r") or 0.0) <= 0.0)
fp0 = sum(1 for r in rows if r["_fp"] == 0.0)
OUT["score_zero_rows"] = {"transfer_score_zero": z, "pct": 100.0*z/n,
                          "expected_net_r_le_0": en0, "pct_en": 100.0*en0/n,
                          "fill_prob_zero_or_null": fp0}
# reconstruction fidelity: within-group spearman(actual rank asc, -transfer_score)
g = L.groups(rows)
pairs=[]; conc=0; disc=0; ties=0
for t,v in g.items():
    if len(v)<3: continue
    order = sorted(v, key=lambda r: r["risk_finalizer_rank"])
    for i,r in enumerate(order): pairs.append((i+1, -r["transfer_score"]))
    for i in range(len(order)):
        for j in range(i+1,len(order)):
            a,b = order[i]["transfer_score"], order[j]["transfer_score"]
            if a==b: ties+=1
            elif a>b: conc+=1
            else: disc+=1
sp,_ = L.spearman(pairs)
OUT["rank_reconstruction"] = {"spearman_rank_vs_negscore": sp,
    "pairs_concordant": conc, "pairs_discordant": disc, "pairs_tied_score": ties,
    "pct_tied": 100.0*ties/(conc+disc+ties), "concordance_of_untied": 100.0*conc/max(1,conc+disc)}

# does the objective / its factors predict outcome (within group, TAKEABLE)?
tk=[r for r in rows if r["takeable"]]
def wg(sub, field, target):
    gg = L.groups(sub); pr=[]
    for t,v in gg.items():
        vv=[r for r in v if r.get(field) is not None and r.get(target) is not None]
        if len(vv)<3: continue
        mu=sum(r[target] for r in vv)/len(vv)
        for i,r in enumerate(sorted(vv,key=lambda x:x[field])): pr.append((i+1, r[target]-mu))
    return L.spearman(pr)[0]
for label,sub in [("ALL",rows),("TAKEABLE",tk)]:
    d={}
    for f in ["transfer_score","_en_clip","expected_net_r","_pb","_fp","_sc","candidate_ev_r","risk_finalizer_rank"]:
        for tgt in ["fill_honest_walk_r","gross_r"]:
            s=wg(sub,f,tgt)
            if s: d[f"{f}->{tgt}"]={"rho":round(s['rho'],4),"z":round(s['z_approx'],1),"n":s["n"]}
    OUT.setdefault("objective_predictivity",{})[label]=d

# selection: pick argmax transfer_score per group vs argmax of each factor alone
import random
rnd=random.Random(7)
def sel(sub,label):
    gg={t:v for t,v in L.groups(sub).items() if len(v)>=2}
    res={"n_groups":len(gg)}
    for tgt in ["fill_honest_walk_r","gross_r"]:
        acc=collections.defaultdict(list)
        for t,v in gg.items():
            vv=[r for r in v if r.get(tgt) is not None]
            if len(vv)<2: continue
            acc["random"].append(sum(r[tgt] for r in vv)/len(vv))
            acc["allocator_rank1"].append(sorted(vv,key=lambda r:r["risk_finalizer_rank"])[0][tgt])
            for f,nm in [("transfer_score","argmax_transfer_score"),("expected_net_r","argmax_expected_net_r"),
                         ("_pb","argmax_probability"),("_fp","argmax_fill_prob"),
                         ("candidate_ev_r","argmax_candidate_ev_r")]:
                cand=[r for r in vv if r.get(f) is not None]
                if cand: acc[nm].append(max(cand,key=lambda r:r[f])[tgt])
            # min-fill-prob = most passive limit
            acc["argmin_fill_prob"].append(min(vv,key=lambda r:r["_fp"])[tgt])
            # only among score>0 rows, argmax
            pos=[r for r in vv if r["transfer_score"]>0]
            if pos: acc["argmax_score_amongPOSITIVE"].append(max(pos,key=lambda r:r["transfer_score"])[tgt])
            zer=[r for r in vv if r["transfer_score"]==0]
            if zer: acc["random_among_ZEROSCORE"].append(sum(r[tgt] for r in zer)/len(zer))
            if pos: acc["random_among_POSITIVE"].append(sum(r[tgt] for r in pos)/len(pos))
        res[tgt]={k:{"n":len(v),"mean":sum(v)/len(v)} for k,v in acc.items()}
    OUT.setdefault("selection_by_objective",{})[label]=res
sel(rows,"ALL"); sel(tk,"TAKEABLE")
json.dump(OUT,open("L9_OBJECTIVE_V1.json","w"),indent=1,default=str)

print("source_completeness:",OUT["source_completeness_values"])
print("score-zero:",{k:(round(v,3) if isinstance(v,float) else v) for k,v in OUT["score_zero_rows"].items()})
rr=OUT["rank_reconstruction"]
print("reconstruction: rho",round(rr["spearman_rank_vs_negscore"]["rho"],4),
      "| tied pairs %",round(rr["pct_tied"],1),"| concordance of untied %",round(rr["concordance_of_untied"],1))
print("== objective predictivity (TAKEABLE) ==")
for k,v in OUT["objective_predictivity"]["TAKEABLE"].items():
    if k.endswith("fill_honest_walk_r"): print(f"   {k:>44} rho={v['rho']:+.4f} z={v['z']:+.1f}")
print("== selection means (TAKEABLE, fill_honest) ==")
for k,v in sorted(OUT["selection_by_objective"]["TAKEABLE"]["fill_honest_walk_r"].items(), key=lambda kv:-kv[1]["mean"]):
    print(f"   {k:>34} {v['mean']:+.4f}  n={v['n']}")
