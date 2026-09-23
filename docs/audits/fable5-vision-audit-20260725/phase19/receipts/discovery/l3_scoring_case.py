#!/usr/bin/env python3
"""l3_scoring_case - ground-truth the SUSPECT4 scoring gap on individual candidates.
Is the ENGINE under-booking gold/silver/JPY/EUR winners, or is the PATH's R normalisation
wrong on those symbols? Dump the actual bar-level R path next to both verdicts."""
import json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws

df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
SUS = ["XAUUSD", "XAGUSD", "USDJPY", "EURUSD"]

sel = t[(t["symbol"].isin(SUS)) & (t["fill_honest_which_came_first"] == "target")
        & (t["outcome_band"] != "ge_target")]
ctl = t[(~t["symbol"].isin(SUS)) & (t["fill_honest_which_came_first"] == "target")
        & (t["outcome_band"] == "ge_target")]
print("suspect honest-target-but-not-engine-ge_target n=%d ; control n=%d" % (len(sel), len(ctl)))

cases = pd.concat([sel.head(3), ctl.head(2)])
keys = set(zip(cases["candidate_id"], cases["decision_time_utc"]))
rp = w0_ws.load_rpaths(keys)

out = {"n_suspect_mismatch": int(len(sel)), "n_control": int(len(ctl)), "cases": []}
for _, r in cases.iterrows():
    k = (r["candidate_id"], r["decision_time_utc"])
    p = rp.get(k)
    rec = {
        "candidate_id": r["candidate_id"], "decision_time_utc": r["decision_time_utc"],
        "symbol": r["symbol"], "side": r["side"], "origin_family": r["origin_family"],
        "entry_price": float(r["entry_price"]), "stop_loss": float(r["stop_loss"]),
        "take_profit_1": float(r["take_profit_1"]), "risk_distance": float(r["risk_distance"]),
        "policy_target_r": float(r["policy_target_r"]),
        "ENGINE_gross_r": float(r["gross_r"]), "ENGINE_outcome_band": r["outcome_band"],
        "ENGINE_opportunity_net_proxy_r": float(r["opportunity_net_proxy_r"]),
        "ENGINE_cost_r": float(r["cost_r"]),
        "PATH_which_came_first": r["which_came_first"],
        "PATH_fill_honest_which_came_first": r["fill_honest_which_came_first"],
        "PATH_fill_honest_walk_r": float(r["fill_honest_walk_r"]),
        "PATH_plain_walk_r": float(r["plain_walk_r"]),
        "PATH_mfe_r": float(r["mfe_r"]), "PATH_mae_r": float(r["mae_r"]),
        "PATH_bars_to_target": r["bars_to_target"], "PATH_bars_to_entry_touch": r["bars_to_entry_touch"],
        "PATH_risk_distance_in_sidecar": (float(p["risk_distance"]) if p else None),
        "risk_distance_match": (abs(float(p["risk_distance"]) - float(r["risk_distance"])) < 1e-9 if p else None),
        "implied_target_price_check_r": abs(float(r["take_profit_1"]) - float(r["entry_price"])) / float(r["risk_distance"]),
        "implied_stop_check_r": abs(float(r["entry_price"]) - float(r["stop_loss"])) / float(r["risk_distance"]),
    }
    if p:
        rec["first12_fav"] = [round(x, 3) for x in p["fav"][:12]]
        rec["first12_adv"] = [round(x, 3) for x in p["adv"][:12]]
        rec["first12_cls"] = [round(x, 3) for x in p["cls"][:12]]
        rec["max_fav"] = round(max(p["fav"]), 4)
        rec["min_adv"] = round(min(p["adv"]), 4)
    out["cases"].append(rec)

# systemic: does the engine's gross_r on SUSPECT4 honest-target rows equal r_at_path_end
# or some fixed fraction of 2R? test three hypotheses over the whole 937.
s = t[(t["symbol"].isin(SUS)) & (t["fill_honest_which_came_first"] == "target")].copy()
hyp = {
    "n": int(len(s)),
    "mean_engine_gross_r": round(float(s["gross_r"].mean()), 5),
    "mean_r_at_path_end": round(float(s["r_at_path_end"].mean()), 5),
    "corr_engine_vs_r_at_path_end": round(float(s[["gross_r", "r_at_path_end"]].corr().iloc[0, 1]), 5),
    "corr_engine_vs_mfe": round(float(s[["gross_r", "mfe_r"]].corr().iloc[0, 1]), 5),
    "corr_engine_vs_r_at_bar_120": round(float(s[["gross_r", "r_at_bar_120"]].dropna().corr().iloc[0, 1]), 5),
    "mean_abs_diff_engine_vs_path_end": round(float((s["gross_r"] - s["r_at_path_end"]).abs().mean()), 5),
    "pct_engine_within_0.02_of_path_end": round(100.0 * float(((s["gross_r"] - s["r_at_path_end"]).abs() < 0.02).mean()), 3),
    "pct_engine_within_0.02_of_2R": round(100.0 * float(((s["gross_r"] - 2.0).abs() < 0.02).mean()), 3),
}
o = t[(~t["symbol"].isin(SUS)) & (t["fill_honest_which_came_first"] == "target")].copy()
hyp_other = {
    "n": int(len(o)),
    "mean_engine_gross_r": round(float(o["gross_r"].mean()), 5),
    "mean_r_at_path_end": round(float(o["r_at_path_end"].mean()), 5),
    "pct_engine_within_0.02_of_path_end": round(100.0 * float(((o["gross_r"] - o["r_at_path_end"]).abs() < 0.02).mean()), 3),
    "pct_engine_within_0.02_of_2R": round(100.0 * float(((o["gross_r"] - 2.0).abs() < 0.02).mean()), 3),
}
out["hypotheses_SUSPECT4"] = hyp
out["hypotheses_OTHER20"] = hyp_other

json.dump(out, open(os.path.join(HERE, "l3_SCORING_CASE_V1.json"), "w"), indent=1, default=str)

for c in out["cases"]:
    print("--- %s %s %s %s  entry=%.5f stop=%.5f tp=%.5f d=%.6f" % (
        c["symbol"], c["side"], c["origin_family"][:22], c["candidate_id"][-14:],
        c["entry_price"], c["stop_loss"], c["take_profit_1"], c["risk_distance"]))
    print("    implied_target_R_from_price=%.4f  implied_stop_R=%.4f  sidecar_risk_dist_match=%s" % (
        c["implied_target_price_check_r"], c["implied_stop_check_r"], c["risk_distance_match"]))
    print("    ENGINE band=%-14s gross_r=%+.4f (proxy=%+.4f cost=%.4f)" % (
        c["ENGINE_outcome_band"], c["ENGINE_gross_r"], c["ENGINE_opportunity_net_proxy_r"], c["ENGINE_cost_r"]))
    print("    PATH   first=%-8s honest=%-8s honest_walk=%+.4f mfe=%+.3f mae=%+.3f bars_to_tgt=%s bars_to_entry=%s" % (
        c["PATH_which_came_first"], c["PATH_fill_honest_which_came_first"], c["PATH_fill_honest_walk_r"],
        c["PATH_mfe_r"], c["PATH_mae_r"], c["PATH_bars_to_target"], c["PATH_bars_to_entry_touch"]))
    print("    fav[:12]=%s" % c.get("first12_fav"))
    print("    adv[:12]=%s" % c.get("first12_adv"))
print("SUSPECT4:", json.dumps(hyp))
print("OTHER20 :", json.dumps(hyp_other))
