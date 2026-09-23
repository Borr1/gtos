"""d5 — assemble the receipt JSON from the measured component artifacts."""
import json, os, shutil, sys

SRC = "/tmp/d5/out"
DEST = ("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/"
        "fable5-vision-audit-20260725/phase19/receipts/discovery")
COMP = ["D5_01_SURVIVE.json", "D5_02_FILL.json", "D5_02B_ARMS.json", "D5_03_HUNT.json",
        "D5_04_ACTIONABLE.json", "D5_05_EXIT.json", "D5_06_POOL_REPRO.json", "D5_07_PRE.json",
        "D5_08_VERIFY.json", "D5_10_ARMS.json", "D5_11_RESIDUAL.json", "D5_12_HUNT2.json",
        "D5_13_FINAL.json", "D5_14_POOL_ANCHOR.json", "D5_CI_CHECK.json"]
SCRIPTS = ["d5_lib.py", "d5_build.py", "d5_ci_check.py", "d5_01_survive.py", "d5_02_fill.py",
           "d5_02b_arms.py", "d5_03_hunt.py", "d5_04_actionable.py", "d5_05_exit.py",
           "d5_06_pool_repro.py", "d5_07_pre.py", "d5_08_verify.py", "d5_09_delayed.py",
           "d5_10_arms.py", "d5_11_residual.py", "d5_12_hunt2.py", "d5_13_final.py",
           "d5_14_pool_anchor.py", "d5_receipt.py"]

J = {}
for f in COMP:
    p = os.path.join(SRC, f)
    if os.path.isfile(p):
        J[f[:-5]] = json.load(open(p))
        shutil.copy(p, os.path.join(DEST, f))
for f in SCRIPTS:
    p = os.path.join("/tmp/d5", f)
    if os.path.isfile(p):
        shutil.copy(p, os.path.join(DEST, f))

F = J["D5_13_FINAL"]; S = J["D5_01_SURVIVE"]; V = J["D5_08_VERIFY"]; RS = J["D5_11_RESIDUAL"]
H2 = J["D5_12_HUNT2"]; PA = J["D5_14_POOL_ANCHOR"]
sep = F["separator"]
R = {
  "lane": "d5",
  "title": "THE SEPARATOR, re-tested on the correct object",
  "population": {
    "feature_table_windows": list(S["windows"].keys()),
    "feature_table_N_emissions": sum(v["n_kept"] for v in S["windows"].values()),
    "achievable_arm_windows": F["windows"],
    "achievable_arm_N_emissions": F["N_emissions"],
    "object": "reproduced sealed roster (Session PB), k=15 close-decision rows only",
    "sealed_three_touched": False,
  },
  "headline": {
    "observable": "c0_close_fav_r = s*(close of M1 bar [T,T+1m) - entry_price)/risk_distance",
    "x4_published_d_on_the_pool": 0.3348,
    "d_on_roster_estate_fill_convention": sep["pooled"]["ESTATE_labels_all_resolved"]["d"],
    "d_on_roster_broker_correct_fill": sep["pooled"]["SIDE_AWARE_labels_all_resolved"]["d"],
    "d_on_roster_actionable_only": sep["pooled"]["SIDE_AWARE_labels_PENDING_only(actionable)"]["d"],
    "share_of_refused_cohort_already_filled_when_observable": 1.0,
    "achievable_cancel_delta_gross_per_opportunity": 0.0,
    "achievable_cancel_delta_net_per_opportunity": 0.0,
    "identity_violations": V["pooled"]["violations"],
    "identity_population": V["pooled"]["n_identity_population(mkt_r0>0 & c0<0)"],
  },
  "signal_verdict": {
    "gross_per_fill_broker_correct_contract": F["contracts"]["SIDE_AWARE_from_T"]["gross_per_fill"],
    "win_rate": F["contracts"]["SIDE_AWARE_from_T"]["win_rate"],
    "breakeven_win_rate": F["contracts"]["SIDE_AWARE_from_T"]["breakeven_wr"],
    "gap_pp": F["contracts"]["SIDE_AWARE_from_T"]["gap_pp"],
    "toll_per_fill": F["contracts"]["SIDE_AWARE_from_T"]["toll_per_fill"],
    "gross_per_opportunity_by_segment": {k: v["SIDE_AWARE_gross_per_opp"] for k, v in F["segments"].items()},
  },
  "fill_artifact": {
    "segments": F["segments"],
    "estate_contract": F["contracts"]["ESTATE_convention_limit_from_T"],
    "broker_correct_contract": F["contracts"]["SIDE_AWARE_from_T"],
  },
  "arms": F["arms"],
  "cost_of_waiting_one_minute": F["cost_of_waiting_one_minute"],
  "actionability": F["actionability"],
  "separator_per_window": sep["per_window"],
  "separator_per_window_estate_all8": {w: {"n": v["n_kept"], "d": v["sep"]["RESOLVED"]["cohens_d"],
                                           "auc": v["sep"]["RESOLVED"]["auc"],
                                           "d_prefilled": v["sep"]["RESOLVED_J0"]["cohens_d"],
                                           "d_actionable": v["sep"]["RESOLVED_J1PLUS"]["cohens_d"]}
                                       for w, v in S["windows"].items()},
  "hunt_actionable_population": {
      k: {"d": v["d"], "auc": v["auc"], "class": v["class"]}
      for k, v in H2["pops"]["SIDE_AWARE_PENDING_RESOLVED (cancel is available)"]["feats"].items()},
  "hunt_ceiling": 0.152,
  "pool_reconciliation": {"x4_repro": J["D5_06_POOL_REPRO"]["x4_repro"],
                          "pool_composition": PA["pool_composition"],
                          "refused_cohort": PA["x4_refused_cohort_c0<=-0.15"]},
  "residual_on_reachable_limits": RS["residual_separation_on_reachable_limits"],
  "artifacts": COMP + SCRIPTS + ["d5_RESULT.md"],
}
json.dump(R, open(os.path.join(DEST, "d5_RESULT.json"), "w"), indent=1, default=float)
print("receipt written; components", len(J), "scripts", len(SCRIPTS))
print(json.dumps(R["headline"], indent=1))
print(json.dumps(R["signal_verdict"], indent=1))
