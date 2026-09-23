"""SYNTHESIS part 4 — join the lane economics onto every record and emit SLEEVE_FORENSIC_V1.json."""
from __future__ import annotations
import json, os, pickle, collections, datetime
P=os.path.dirname(os.path.abspath(__file__)); PROV=os.path.dirname(P); PH20=os.path.dirname(PROV)
V=pickle.load(open(f"{P}/_v_broad.pkl","rb"))
X1V=json.load(open(f"{PROV}/x1_receipts/X1_VERDICTS_V1.json"))
X1C=json.load(open(f"{PROV}/x1_receipts/X1_CEILING_V1.json"))["rows"]
S1 =json.load(open(f"{PROV}/s1_receipts/S1_DISCRIMINATOR_V1.json"))["rows"]
S2 =json.load(open(f"{PROV}/s2_receipts/S2_REGISTRY_DOSSIER_V1.json"))["sleeves"]
SYN=json.load(open(f"{P}/SYN_IRRELEVANT_V1.json"))
R2 =json.load(open(f"{PH20}/receipts/r2/R2_CENSUS_V1.json"))["families"]

for name,rec in V.items():
    x=X1V["rows"].get(name); c=X1C.get(name)
    if x:
        rec["x1"]={"class":x["cls"],"mechanism_tags":x["tags"],"IR_at_own_hold":x["IR_at_res"],
                   "TIGHT_stop_over_sigma":x["TIGHT_at_res"],"cost_r_toll_over_stop":x["cost_r"],
                   "RATIO_signal_over_toll":x["RATIO"],"SHORT_log2_peak_over_hold":x["SHORT"],
                   "T_res_h":x["T_res"],"T_peak_h":x["T_peak"],"stop_bps":x["stop_bps"],
                   "max_signed_t":x["max_signed_t"]}
    if c:
        rec["ceiling"]={"best_h":c["best_h"],"drift_bps":c["drift_bps"],"toll_bps":c["toll_bps"],
                        "net_bps":c["net_bps"],"ci95":[c["ci_lo"],c["ci_hi"]],"n":c["n"],"verdict":c["verdict"]}
    if name in S1:
        s=S1[name]; rec["s1"]={"n":s["n"],"timeframe":s["timeframe"],"hold_h_median":s["hold_h_median"],
            "stop_bps":s["stop_bps"],"stop_over_atr":s["stop_over_atr"],"cost_r":s["cost_r"],"toll_bps":s["toll_bps"],
            "signal_at_own_hold_bps":s["signal_at_own_hold_bps"],"signal_over_toll":s["signal_over_toll"],
            "ci_excludes_zero_at_h":s["ci_excludes_zero_at"],"gate_verdict":s["gate_verdict"],
            "estate_decision":s["estate_decision"],"capture_frac":s["lifecycle"]["capture_frac"],
            "mfe_r_mean":s["lifecycle"]["mfe_r_mean"],"exit_reasons":s["lifecycle"]["exit_reasons"]}
    if name in S2:
        s=S2[name]; rec["s2"]={"confidence":s["confidence"],"corr_cluster":s["cluster"],"status":s["status"],
            "grid":s["grid"],"n_trades":s["n_trades"],"per_year":s["per_year"],
            "live_horizon_own_bars":s["live_horizon_own_bars"],"med_hold_own_bars":s["med_hold_own_bars"],
            "p90_hold_own_bars":s["p90_hold_own_bars"],"frac_resolved_in_entry_bar":s["frac_resolved_1_bar"],
            "frac_over_live_horizon":s["frac_over_horizon"],"mfe_med_r":s["mfe_med"],"exit_mix":s["exit_mix"],
            "gate_verdict_mid":s["aq_verdict_mid"],"gate_r_per_day_mid":s["aq_live_true_r_per_day_mid"]}
    if name in SYN["families"]:
        s=SYN["families"][name]
        rec["irrelevant_by_construction"]={"n_emissions":s["n"],
            "union_share":s["union_share"],"clean_share":s["clean_share"],
            "off_configured_session":s["r1_off_share"],"born_past_stop":s["r2_past_stop_share"],
            "target_already_behind":s["r3_target_through_share"],"stale_bar":s["r4_stale_share"]}
    if name in R2:
        s=R2[name]; rec["r2_emission_census"]={"kind":s["kind"],"n":s["n"],"median_risk_bps":s["risk_bps_median"],
            "gap_r_median":s["gap_r_median"],"share_resting":s["share_resting"],"share_marketable":s["share_marketable"]}

gens={k:v for k,v in V.items() if not k.startswith("__")}
mach={k:v for k,v in V.items() if k.startswith("__")}
cen=collections.Counter(v["verdict"] for v in gens.values())
by_class=collections.defaultdict(lambda: collections.Counter())
for v in gens.values(): by_class[v["klass"]][v["verdict"]]+=1

# --- the geometry adjudication, computed from X1 not asserted -----------------
rows=X1V["rows"]
broad=[k for k,v in rows.items() if v["cls"]=="BROAD"]; sleeve=[k for k,v in rows.items() if v["cls"]=="SLEEVE"]
def med(a):
    a=sorted(a)
    if not a: return None
    n=len(a)
    return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2.0  # true median; broad set has n=10 (even)
geom={
 "question":"Borhen: are these ideas being run on the wrong clock / stop / horizon — is the geometry the defect?",
 "instrument":("X1: contract-free signed close-to-close drift minus a seeded random-side placebo, anchored at the decision-bar "
               "close, day-block bootstrap over decision days, 11 horizons 15 min - 320 trading hours. No stop, no target, no "
               "horizon in the measurement, so it cannot be censored by the contract whose appropriateness is the question."),
 "identity":"RATIO = signal(T_res)/toll = IR(T_res) / ( TIGHT@res x cost_r ); verified row by row to 3 dp across all 39 rows",
 "terms":{"IR":"information ratio at the sleeve's own realised hold = the IDEA",
          "TIGHT":"stop / sigma(T_res) = the STOP GEOMETRY (RATIO is proportional to 1/TIGHT)",
          "cost_r":"toll / stop = the COST GEOMETRY"},
 "medians":{"IR":{"broad":med([rows[k]["IR_at_res"] for k in broad]),"sleeve":med([rows[k]["IR_at_res"] for k in sleeve])},
            "cost_r":{"broad":med([rows[k]["cost_r"] for k in broad]),"sleeve":med([rows[k]["cost_r"] for k in sleeve])},
            "TIGHT":{"broad":med([rows[k]["TIGHT_at_res"] for k in broad]),"sleeve":med([rows[k]["TIGHT_at_res"] for k in sleeve])}},
 "cost_r_by_contract_speed":X1V["cost_r_by_speed"],
 "mechanism_census":{"BROAD":dict(collections.Counter(t for k in broad for t in rows[k]["tags"])),
                     "SLEEVE":dict(collections.Counter(t for k in sleeve for t in rows[k]["tags"]))},
 "spearman_partials":"see X1_MASTER_V1.json: every geometry variable's partial correlation with RATIO collapses to near zero once the common-horizon IR is in the model (TIGHT +0.014, T_res +0.164, stop_bps +0.268; the owner's literal mismatch log2(T_look/T_res) is rho -0.130 p 0.4420)",
 "verdict":("HALF RIGHT, AND THE HALF THAT IS RIGHT IS THE COST TERM. A quick tight contract hands the broker 0.339 of one R at "
            "the median against 0.126 for a slow one (2.7x, pure geometry, X1 cost_r_by_speed). But the geometry terms do not "
            "ORDER the economics: the information ratio does. 10 of 10 broad families are NO_SIGNAL — their drift's argmax does sit "
            "well past their hold, so the owner's hypothesis LOOKS true for them, but the drift AT that argmax is itself "
            "indistinguishable from zero, so lengthening the hold arrives at a peak made of noise."),
 "the_count_that_settles_it":("GEOMETRY_WRONG is the single most common DIAGNOSIS (11 of 51) and the rarest BINDING one: of those "
            "11, only 2 (asia_pdl_fade, metal_session_reversion) show measurable signal at the contract-free instrument, and "
            "exactly 1 (asia_pdl_fade) has a ceiling interval that excludes zero.")}

out={"schema":"sleeve_forensic_v1",
 "generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "wave":"phase20 — the per-sleeve forensic, commissioned by Borhen",
 "commission":("'we can also add an analysis to literally every sleeve there on the family that got hit and to understand exactly "
               "what was wrong with the sleeve or maybe the parameters or the configuration or the way it goes'"),
 "roster":{"n_generators":len(gens),"n_shared_machinery":len(mach),
           "composition":{"broad_origin_production_families":10,"broad_origin_POI_frameworks":3,"core_W7_sleeves":11,
                          "candidate_book_sleeves_incl_3_quarantined":12,"market_expansion_mx_sleeves":14,
                          "registered_for_sizing_no_live_generator":1},
           "source":("src/components/broader_origin_generators.py:39-62; src/components/ultimate_book/sleeves/registry.py:46-110; "
                     "sleeves/candidate_registry.py:47-139; sleeves/market_expansion_d1.py TAG_TO_RULE; admission.py:265-277")},
 "verdict_census":dict(cen.most_common()),
 "verdict_census_by_class":{k:dict(v) for k,v in by_class.items()},
 "geometry_adjudication":geom,
 "irrelevant_by_construction":SYN,
 "lane_receipts":{
   "g1":f"{PROV}/G1_THREE_POI_FAMILIES_DOSSIER.md","g2":f"{PROV}/g2/G2_DOSSIERS.md",
   "g3":f"{PROV}/G3_REVERSION_AND_EXTREME_DOSSIERS.md","g4":f"{PROV}/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md",
   "s1":f"{PROV}/S1_ARMED_SLEEVES_DOSSIER.md","s2":f"{PROV}/S2_REGISTRY_DOSSIERS.md",
   "x1":f"{PROV}/X1_GEOMETRY_HYPOTHESIS.md","x2":f"{PROV}/x2_receipts/X2_WHY_DID_WE_BUILD_THESE.md",
   "r1_concurrent_repair":f"{PH20}/SESSION_R1_QUOTE_SIDE_WALKER.md",
   "r2_concurrent_repair":f"{PH20}/SESSION_R2_GENERATOR_REPAIR.md",
   "synthesis_own_measurement":f"{P}/SYN_IRRELEVANT_V1.json + {P}/SYN_OFFSESSION_V1.json"},
 "generators":gens,"shared_machinery":mach}
json.dump(out, open(f"{PH20}/SLEEVE_FORENSIC_V1.json","w"), indent=1)
print("wrote SLEEVE_FORENSIC_V1.json", os.path.getsize(f"{PH20}/SLEEVE_FORENSIC_V1.json"), "bytes")
print(json.dumps(geom["medians"],indent=1))
print(json.dumps({k:dict(v) for k,v in by_class.items()},indent=1))
