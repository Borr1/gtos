#!/usr/bin/env python3
"""F1 supplementary: reconciliation, adversarial checks, magnitude cross-test, dollars."""
import gzip, json, pickle
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
R_USD = 2000.0
MONTHS = ["feb", "apr", "may", "jun", "jul"]

frames = [pd.DataFrame.from_records(pickle.load(gzip.open(HERE / f"f1walk_{m}.pkl.gz", "rb")))
          for m in MONTHS]
df = pd.concat(frames, ignore_index=True)
df["mfe_entry_r"] = df["mfe_r"] - df["entry_slip_r"]
df["mfe_pre_exit_entry_r"] = df["mfe_pre_exit_r"] - df["entry_slip_r"]
df["is_win"] = df.exit_kind == "TARGET"; df["is_stop"] = df.exit_kind == "STOP"
df["is_time"] = df.exit_kind == "TIME_STOP"
out = {}

# ------------------------------------- 0. direction vs spread, separated by MEASUREMENT
# close_full_r is the barrier-free mark at the sealed horizon on the TRADED quote basis
# (we buy the ask, sell the bid). close_full_raw_r restates the identical mark on the raw
# archive basis by adding back the two transform offsets the walker itself applied.
cf = df.close_full_r.to_numpy(float); cr = df.close_full_raw_r.to_numpy(float)
se = lambda a: float(np.std(a, ddof=1) / np.sqrt(len(a)))
out["direction_vs_spread"] = {
    "n": int(len(df)),
    "barrier_free_mark_traded_basis_r": {"mean": float(cf.mean()), "se": se(cf),
                                         "t": float(cf.mean() / se(cf)),
                                         "ci95": [float(cf.mean() - 1.96 * se(cf)),
                                                  float(cf.mean() + 1.96 * se(cf))]},
    "barrier_free_mark_raw_basis_r": {"mean": float(cr.mean()), "se": se(cr),
                                      "t": float(cr.mean() / se(cr)),
                                      "ci95": [float(cr.mean() - 1.96 * se(cr)),
                                               float(cr.mean() + 1.96 * se(cr))]},
    "transform_offsets_r": {"entry_mean": float(df.entry_off_r.mean()),
                            "exit_mean": float(df.exit_off_r.mean()),
                            "sum_mean": float((df.entry_off_r + df.exit_off_r).mean())},
    "estate_modelled_spread_r_mean": float(df.spread_r.mean()),
    "deductible_cost_r_mean": float(df.cost_r.mean()),
    "interpretation": (
        "raw-basis mark = the pool's directional drift over 120 minutes with NO exit rule and "
        "NO spread; traded-basis mark = the same path after paying the quote. The difference "
        "is the spread, and it is measured here rather than inferred."),
}

# ---------------------------------------------------------------- 1. break-even reconciliation
p_T = float(df.is_win.mean()); p_S = float(df.is_stop.mean()); p_TS = float(df.is_time.mean())
m_ts = float(df.loc[df.is_time, "gross_r"].mean())
m_win = float(df.loc[df.is_win, "gross_r"].mean())
m_stop = float(df.loc[df.is_stop, "gross_r"].mean())
c = float(df.cost_r.mean())
f = p_T + p_S
be_all = (f * 1.0 + c - p_TS * m_ts) / 3.0          # payoff +2 / -1 nominal
out["breakeven_reconciliation"] = {
    "n": int(len(df)),
    "hit_rate_all_fills": p_T, "hit_rate_barrier_resolved": p_T / f,
    "stop_share": p_S, "time_stop_share": p_TS,
    "mean_gross_TARGET": m_win, "mean_gross_STOP": m_stop, "mean_gross_TIME_STOP": m_ts,
    "mean_deductible_cost_r": c,
    "mean_spread_r_embedded_in_gross": float(df.spread_r.mean()),
    "all_in_cost_r": float(c + df.spread_r.mean()),
    "breakeven_hit_rate_all_fills": be_all,
    "breakeven_hit_rate_barrier_resolved": be_all / f,
    "shortfall_pp_all_fills": (p_T - be_all) * 100.0,
    "shortfall_pp_barrier_resolved": (p_T / f - be_all / f) * 100.0,
    "note": "deductible = slippage+swap+commission (candidate_funnel_analysis.py:164-167); "
            "spread is charged inside gross via the entry/exit quote transform, not deducted twice",
}

# ------------------------------------------------- 2. reconciliation vs W0CAP_MECHANISM_V1
# their population: gross_r <= -1.0 + 1e-3 (a FULL stop or worse), January phase19 pool
w0 = {"share_mfe_ge_0.25R": 0.3469482632662549, "share_mfe_ge_0.5R": 0.21040047818290497,
      "share_mfe_ge_1.0R": 0.08188882247459653, "share_mfe_ge_2.0R": 0.003852028956631467,
      "n": 15057, "mfe_before_stop_mean": -1.814273421771882, "gap_fill_share": 7464 / 15057}
fs = df[df.gross_r <= -1.0 + 1e-3]
rec = {"w0cap_reported": w0, "f1_closest_slice": {
    "definition": "gross_r <= -1.0+1e-3 (full stop or worse), five-month sealed corpus",
    "n": int(len(fs)),
    "share_mfe_ge_0.25R": float((fs.mfe_pre_exit_r >= 0.25).mean()),
    "share_mfe_ge_0.5R": float((fs.mfe_pre_exit_r >= 0.5).mean()),
    "share_mfe_ge_1.0R": float((fs.mfe_pre_exit_r >= 1.0).mean()),
    "share_mfe_ge_2.0R": float((fs.mfe_pre_exit_r >= 2.0).mean()),
    "mfe_pre_exit_mean": float(fs.mfe_pre_exit_r.mean()),
    "gap_fill_share": float(fs.gapped.mean())}}
rec["verdict"] = ("NOT COMPARABLE. W0CAP's mean MFE-before-stop is -1.814 R with min -26.3 R and "
                  "49.6% gap fills: its reference price is one the market gapped away from. The "
                  "sealed resolver used here removes exactly that population via "
                  "CENSORED_INVALID_GAP_THROUGH_SL_OR_TP, so the two ladders measure different objects.")
out["reconciliation_w0cap"] = rec

# --------------------------------------- 3. magnitude cross-test: do MFE and MAE move together?
cells = []
for (fam, sym), sub in df.groupby(["family", "symbol"]):
    if len(sub) < 150:
        continue
    cells.append({"family": str(fam), "symbol": str(sym), "n": int(len(sub)),
                  "mean_mfe_full_r": float(sub.mfe_full_r.mean()),
                  "mean_abs_mae_full_r": float(sub.mae_full_r.abs().mean()),
                  "ratio": float(sub.mfe_full_r.mean() / sub.mae_full_r.abs().mean()),
                  "mean_net_r": float(sub.net_r.mean()),
                  "hit_rate": float(sub.is_win.mean())})
cd = pd.DataFrame(cells)
out["magnitude_cross_test"] = {
    "n_cells": int(len(cd)),
    "corr_mfe_vs_abs_mae_across_cells": float(cd.mean_mfe_full_r.corr(cd.mean_abs_mae_full_r)),
    "ratio_mfe_over_abs_mae": {"mean": float(cd.ratio.mean()), "median": float(cd.ratio.median()),
                               "min": float(cd.ratio.min()), "max": float(cd.ratio.max()),
                               "share_above_1": float((cd.ratio > 1).mean())},
    "corr_ratio_vs_net_r": float(cd.ratio.corr(cd.mean_net_r)),
    "corr_mfe_level_vs_net_r": float(cd.mean_mfe_full_r.corr(cd.mean_net_r)),
    "pooled_mfe_full_r": float(df.mfe_full_r.mean()),
    "pooled_abs_mae_full_r": float(df.mae_full_r.abs().mean()),
    "pooled_ratio": float(df.mfe_full_r.mean() / df.mae_full_r.abs().mean()),
    "note": "MAGNITUDE_PROGRAM_V1 (swarm/, origin/main) found a breakout raises MFE ~16% and MAE "
            "~15% on its best row, ratio +1.3%. This is the same test inside the funnel corpus: "
            "whether any cell buys favourable travel without buying adverse travel with it.",
    "cells": sorted(cells, key=lambda r: -r["ratio"])[:25],
}

# --------------------------------------------------------- 4. give-back money and winner fragility
gb = df[df.mfe_r >= 1.0]
out["giveback_money"] = {
    "n_reached_1R": int(len(gb)), "share_of_fills": float(len(gb) / len(df)),
    "outcome_mix": gb.exit_kind.value_counts(normalize=True).to_dict(),
    "mean_giveback_r": float(gb.giveback_r.mean()),
    "total_giveback_r": float(gb.giveback_r.sum()),
    "total_giveback_usd": float(gb.giveback_r.sum() * R_USD),
    "mean_net_r_of_this_cohort": float(gb.net_r.mean()),
    "counterfactual_flat_1R_exit_net_r": float((1.0 - gb.cost_r).mean()),
    "counterfactual_note": "banking exactly 1R on every trade that ever touched 1R is NOT achievable "
                           "ex ante -- it conditions on the realised path. It is the upper bound.",
}
w = df[df.is_win]
out["winner_fragility"] = {
    "n_winners": int(len(w)),
    "mae_headroom_r": {k: float(v) for k, v in w.mae_headroom_r.describe().items()},
    "share_within_0p02R_of_stop": float((w.mae_headroom_r <= 0.02).mean()),
    "share_within_0p05R_of_stop": float((w.mae_headroom_r <= 0.05).mean()),
    "share_within_0p10R_of_stop": float((w.mae_headroom_r <= 0.10).mean()),
    "share_within_0p20R_of_stop": float((w.mae_headroom_r <= 0.20).mean()),
    "share_mae_worse_than_half_stop": float((w.mae_headroom_r <= 0.5).mean()),
    "stop_tightening_kill_curve": {
        "interpretation": "share of the +2R population destroyed by moving the stop X R tighter",
        **{"tighten_%gR" % x: float((w.mae_headroom_r <= x).mean())
           for x in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5)}},
    "_artifact_warning": (
        "mae_before_mfe = 0.9845 for winners is a CONSTRUCTION ARTIFACT of the exit rule, and the "
        "mechanism is measured, not assumed: for TARGET exits mfe_bar_idx == exit_idx in "
        "30737/30737 = 100.0% of cases, and for STOP exits mae_bar_idx == exit_idx in "
        "78207/78207 = 100.0%. The running extremum is pinned to the exit bar by the barrier that "
        "caused the exit, so ordering carries no information for those two cohorts. It is "
        "informative ONLY for TIME_STOP trades, where mfe_bar_idx == exit_idx just 7.37% of the "
        "time. Separately, mae_r >= 0 occurs in 0 of 146,736 trades -- over a 21-minute median "
        "hold, price always trades below the fill at some point. That is measured, not an "
        "artifact of the spread: mae_bar_idx == 0 in only 14.74% of trades."),
    "ordering_where_it_is_informative_TIME_STOP": {
        "n": int(df.is_time.sum()),
        "mae_before_mfe_share": float(df.loc[df.is_time, "mae_before_mfe"].mean()),
        "mfe_bar_idx_eq_exit_idx_share": float(
            (df.loc[df.is_time, "mfe_bar_idx"] == df.loc[df.is_time, "exit_idx"]).mean())},
    "material_adverse_ordering": {
        "definition": "MAE deeper than -0.25R AND its bar strictly precedes the MFE bar",
        "share_of_winners": float(((w.mae_r <= -0.25) & (w.mae_bar_idx < w.mfe_bar_idx)).mean()),
        "share_of_winners_mae_deeper_than_0p25R": float((w.mae_r <= -0.25).mean()),
        "share_of_winners_mae_deeper_than_0p5R": float((w.mae_r <= -0.5).mean()),
        "share_of_all_fills": float(((df.mae_r <= -0.25) & (df.mae_bar_idx < df.mfe_bar_idx)).mean()),
        "mae_bar_idx_is_zero_share_all_fills": float((df.mae_bar_idx == 0).mean()),
        "mfe_bar_idx_is_zero_share_all_fills": float((df.mfe_bar_idx == 0).mean()),
    },
}

# --------------------------------------------------------- 5. adversarial: definition sensitivity
adv = {}
for label, col in [("inclusive_of_exit_bar", "mfe_r"), ("strictly_pre_exit_bar", "mfe_pre_exit_r"),
                   ("entry_frame_pre_exit", "mfe_pre_exit_entry_r"),
                   ("barrier_free_full_window", "mfe_full_r")]:
    s = df.loc[df.is_stop, col]
    adv[label] = {"n": int(s.notna().sum()),
                  **{"ge_%gR" % lv: float((s >= lv).mean()) for lv in (0.5, 1.0, 1.5, 1.8, 2.0)},
                  "mean": float(s.mean()), "median": float(s.median())}
adv["_note"] = ("barrier_free_full_window lets the path run past the actual stop to the 120-min "
                "horizon, so it is NOT a near-miss measure -- it is the counterfactual 'what the "
                "price did afterwards'. Included to bound the definition.")
# limit vs market: limit fills get a better price, so their fill-frame MFE is structurally lower
for ot in ("MARKET", "LIMIT"):
    s = df[(df.order_type == ot) & df.is_stop]
    adv["by_order_type_" + ot] = {
        "n": int(len(s)), "mean_entry_slip_r": float(s.entry_slip_r.mean()),
        **{"ge_%gR_preexit" % lv: float((s.mfe_pre_exit_r >= lv).mean()) for lv in (0.5, 1.0, 1.8)}}
out["adversarial_definition_sensitivity"] = adv

# ------------------------------------------------------------------------ 6. dollars
d = {}
d["basis"] = ("1 R = 2.00% of the $100,000 account = $2,000 (config/agent_config.yaml:23 "
              "risk_per_trade_pct: 2.0; :1363 governor_static_initial_balance: 100000.0). "
              "Half-Kelly effective ~1.73% = $1,730 (:1316-1322).")
for k, sub in [("all_fills", df), ("TARGET", df[df.is_win]), ("STOP", df[df.is_stop]),
               ("TIME_STOP", df[df.is_time])]:
    d[k] = {"n": int(len(sub)), "mean_net_r": float(sub.net_r.mean()),
            "mean_net_usd": float(sub.net_r.mean() * R_USD),
            "total_net_r": float(sub.net_r.sum()),
            "total_net_usd": float(sub.net_r.sum() * R_USD),
            "mean_cost_usd": float(sub.cost_r.mean() * R_USD)}
d["per_trade_cost_usd_breakdown"] = {
    "spread_inside_gross": float(df.spread_r.mean() * R_USD),
    "slippage": float(df.slippage_r.mean() * R_USD),
    "swap": float(df.swap_r.mean() * R_USD),
    "commission": float(df.commission_r.mean() * R_USD),
    "all_in": float((df.spread_r + df.cost_r).mean() * R_USD)}
d["scale_note"] = ("146,736 fills over 100 trading days is 1,467/day; nobody trades that. "
                   "These are per-trade magnitudes. A live book takes ~7 book-days/month "
                   "(CLAUDE.md section 4).")
out["dollars"] = d

json.dump(out, open(HERE / "F1_SUPP.json", "w"), indent=1, default=str)
print(json.dumps({"written": "F1_SUPP.json", "cells": len(cd)}))
