#!/usr/bin/env python3
"""l3_scoring_repair - the HONEST, two-sided size of the SUSPECT4 scoring disagreement.

The engine under-books targets AND stops on XAUUSD/XAGUSD/USDJPY/EURUSD. Correcting only
the target side overstates the repair. Re-score every takeable row at the path's own
contract -- honest first touch of +2R => +2.0, of -1R => -1.0, neither => r_at_path_end --
and report the delta per symbol and per group, both directions.
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
SUS = ["XAUUSD", "XAGUSD", "USDJPY", "EURUSD"]
t["grp"] = np.where(t["symbol"].isin(SUS), "SUSPECT4", "OTHER20")

fh = t["fill_honest_which_came_first"]
t["path_contract_r"] = np.where(fh == "target", 2.0,
                        np.where(fh == "stop", -1.0,
                        np.where(fh == "no_fill", 0.0, t["r_at_path_end"].fillna(0.0))))
t["delta_r"] = t["path_contract_r"] - t["gross_r"]

def blk(s):
    return {"n": int(len(s)),
            "engine_gross_r": round(float(s["gross_r"].mean()), 5),
            "path_contract_r": round(float(s["path_contract_r"].mean()), 5),
            "delta_r_per_trade": round(float(s["delta_r"].mean()), 5),
            "total_delta_R": round(float(s["delta_r"].sum()), 2),
            "target_side_delta_R": round(float(s.loc[fh.reindex(s.index) == "target", "delta_r"].sum()), 2),
            "stop_side_delta_R": round(float(s.loc[fh.reindex(s.index) == "stop", "delta_r"].sum()), 2),
            "other_side_delta_R": round(float(s.loc[~fh.reindex(s.index).isin(["target", "stop"]), "delta_r"].sum()), 2),
            "n_target": int((fh.reindex(s.index) == "target").sum()),
            "n_stop": int((fh.reindex(s.index) == "stop").sum())}

out = {"suspect": SUS, "population": "TAKEABLE", "n": int(len(t))}
out["ALL_takeable"] = blk(t)
out["by_group"] = {g: blk(s) for g, s in t.groupby("grp")}
out["by_symbol"] = {}
for sym, s in t.groupby("symbol"):
    out["by_symbol"][sym] = blk(s)

# pool-level consequence, stated three ways
tot = float(t["delta_r"].sum())
out["consequence"] = {
    "takeable_engine_gross_r": round(float(t["gross_r"].mean()), 5),
    "takeable_path_contract_r": round(float(t["path_contract_r"].mean()), 5),
    "delta_all_symbols_per_trade": round(tot / len(t), 5),
    "delta_from_SUSPECT4_only_per_takeable_trade": round(float(t.loc[t["grp"] == "SUSPECT4", "delta_r"].sum()) / len(t), 5),
    "delta_from_OTHER20_only_per_takeable_trade": round(float(t.loc[t["grp"] == "OTHER20", "delta_r"].sum()) / len(t), 5),
    "SUSPECT4_share_of_total_delta_pct": round(100.0 * float(t.loc[t["grp"] == "SUSPECT4", "delta_r"].sum()) / tot, 3) if tot else None,
    "SUSPECT4_share_of_takeable_rows_pct": round(100.0 * float((t["grp"] == "SUSPECT4").mean()), 3),
}
# how much of the FULL-STOP cohort the mission briefed is a SUSPECT4 scoring artefact?
S = t["outcome_band"] == "full_stop"
out["briefed_stop_cohort_composition"] = {
    "takeable_full_stop_n": int(S.sum()),
    "suspect4_n": int((S & (t["grp"] == "SUSPECT4")).sum()),
    "suspect4_whose_honest_path_says_target_n": int((S & (t["grp"] == "SUSPECT4") & (fh == "target")).sum()),
    "other20_whose_honest_path_says_target_n": int((S & (t["grp"] == "OTHER20") & (fh == "target")).sum()),
}
json.dump(out, open(os.path.join(HERE, "l3_SCORING_REPAIR_V1.json"), "w"), indent=1, default=str)

print("ALL takeable:", json.dumps(out["ALL_takeable"]))
for g, b in out["by_group"].items():
    print("%-9s n=%5d engine=%+.5f path=%+.5f delta=%+.5f  (tgt %+.1f R / stop %+.1f R / other %+.1f R)" % (
        g, b["n"], b["engine_gross_r"], b["path_contract_r"], b["delta_r_per_trade"],
        b["target_side_delta_R"], b["stop_side_delta_R"], b["other_side_delta_R"]))
print("%-10s %6s %9s %9s %9s %10s" % ("symbol", "n", "engine", "path", "delta", "totalR"))
for sym, b in sorted(out["by_symbol"].items(), key=lambda kv: -kv[1]["delta_r_per_trade"]):
    print("%-10s %6d %+9.4f %+9.4f %+9.4f %10.1f" % (sym, b["n"], b["engine_gross_r"], b["path_contract_r"], b["delta_r_per_trade"], b["total_delta_R"]))
print("CONSEQUENCE:", json.dumps(out["consequence"]))
print("BRIEFED STOP COHORT:", json.dumps(out["briefed_stop_cohort_composition"]))
