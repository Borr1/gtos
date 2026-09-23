"""KB6_overlay_passrate_test.py — the BINDING-CONSTRAINT verdict on the STATE_D overlays.

DOCTRINE: never per-trade EV alone. The verdict on any book change is the diversification-aware
challenge-pass MC + 1.5x left-tail STRESS on a VOL-MATCHED (risk-equivalent) basis. The KB6 mine
proved the cross-layer leader-veto / VP-acceptance overlays survive the deployed STATE_D exit and
stay low-corr vs the COMBINED book — but corr-check showed they are HIGH-corr vs their own parent
fold sleeve (sub_xvol_pullback / sub_mid_dn_revert). So they are NOT new additive streams; they are
intra-sleeve SIZE-UP SELECTORS. The honest test is therefore:

  Does selecting the leader-veto SUBSET (the higher-odds STATE_D rows) inside an existing fold
  sleeve, instead of trading the whole base sleeve, improve the deployed book's vol-matched
  challenge-pass + 1.5x stress pass-rate?

We test, ALL on the same day grid, vol-matched to the deployed clean_3 daily std, with 1.5x
left-tail stress, via the LOCKED W2 MC engine (mc_series):
  - deploy        : clean_3 exactly as shipped (sub_xvol_pullback base sleeve, fixed-3R label).
  - deploy_sd     : clean_3 but sub_xvol_pullback / sub_mid_dn_revert re-labelled with STATE_D Rd
                    (honesty: what the book ACTUALLY earns if it exits via STATE_D, not fixed-3R).
  - veto_replace  : deploy_sd with sub_xvol_pullback replaced by its leader-veto STATE_D subset.
  - vpacc_replace : deploy_sd with sub_mid_dn_revert replaced by its VP-acceptance STATE_D subset.
  - veto_overlay  : deploy_sd PLUS the veto subset added as a small extra conf (size-up tilt).

NOTE on the fixed-3R vs STATE_D book: the SHIPPED clean_3 book scored sub_* sleeves at fixed-3R
(SC.materialize_cell). The deployed runtime exit is STATE_D. This script surfaces BOTH so the
owner sees the exit-honest pass-rate, not just the as-scored one.
"""
import sys, json, collections, math, pickle, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import INTEG_portfolio_build_w3 as W3
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build as I
import KB5_fold_new_sleeves as FOLD
import datetime

DEPLOY = json.load(open(HERE / "INTEG_W5_CLEAN3_DEPLOY.json"))
CONF = DEPLOY["conf"]
N = I.N


def _asdate(d):
    return d if isinstance(d, datetime.date) else datetime.date.fromisoformat(str(d)[:10])


def candidate_daily(rows, key="R"):
    byday = collections.defaultdict(list)
    for r in rows:
        byday[_asdate(r["date"])].append(r[key])
    return {d: sum(v) / len(v) for d, v in byday.items()}


def main():
    print("=== KB6: STATE_D overlay BINDING-CONSTRAINT pass-rate test (vol-matched + 1.5x stress) ===\n")
    raw = json.load(open(HERE / "KB6_CONFLUENCE_STATE_D_RAW.json"))

    # --- base 8 book sleeves (conf-wtd daily) from W3 cache ---
    streams_w3 = pickle.load(open(HERE / "INTEG_W3_streams_cache.pkl", "rb"))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    base_sleeves = W3.SLEEVES
    base_daily = {sl: {} for sl in base_sleeves}
    for di, day in enumerate(days_w3):
        for si, sl in enumerate(base_sleeves):
            base_daily[sl][day] = M_w3[di][si]

    # --- the 3 fold sleeves as SHIPPED (fixed-3R) ---
    fold_rows = {nm: FOLD.NEW_GENS[nm]() for nm in ("sub_xvol_pullback", "vp_euidx_pocgrav", "sub_mid_dn_revert")}
    fold_daily_3R = {nm: {d: v * CONF[nm] for d, v in candidate_daily(fold_rows[nm], "R").items()}
                     for nm in fold_rows}

    # --- the same fold sleeves re-labelled with STATE_D Rd (exit-honest) ---
    # sub_xvol_pullback fold sleeve drops crypto+jpy; replicate that universe filter on the raw rows.
    DROP = FOLD.DROP_XVOL
    xvol_sd_rows = [dict(date=r["date"], year=r["year"], R=r["Rd"])
                    for r in raw["xvol_up_pullback_L3R"] if r["sym"] not in DROP]
    middn_sd_rows = [dict(date=r["date"], year=r["year"], R=r["Rd"]) for r in raw["mid_dn_revert_ny_L3R"]]
    fold_daily_sd = dict(fold_daily_3R)  # vp_euidx unchanged (own exit), others overwritten
    fold_daily_sd["sub_xvol_pullback"] = {d: v * CONF["sub_xvol_pullback"] for d, v in candidate_daily(xvol_sd_rows, "R").items()}
    fold_daily_sd["sub_mid_dn_revert"] = {d: v * CONF["sub_mid_dn_revert"] for d, v in candidate_daily(middn_sd_rows, "R").items()}

    # --- overlay subsets (STATE_D) at the SAME conf as the parent sleeve ---
    veto_rows = [dict(date=r["date"], year=r["year"], R=r["Rd"])
                 for r in raw["xvol_up_pullback_L3R"]
                 if r["sym"] not in DROP and r["conds"].get("ll_align") == "none"]
    vpacc_rows = [dict(date=r["date"], year=r["year"], R=r["Rd"])
                  for r in raw["mid_dn_revert_ny_L3R"] if r["conds"].get("vp_loc") == "above_va"]
    veto_daily = {d: v * CONF["sub_xvol_pullback"] for d, v in candidate_daily(veto_rows, "R").items()}
    vpacc_daily = {d: v * CONF["sub_mid_dn_revert"] for d, v in candidate_daily(vpacc_rows, "R").items()}

    # all-days grid
    def days_of(*dicts):
        s = set()
        for d in dicts:
            s |= set(d)
        return s
    book_part = days_of(*base_daily.values())
    all_days = sorted(book_part | days_of(*fold_daily_sd.values()) | set(veto_daily) | set(vpacc_daily))

    def base_row_sum(day):
        return sum(base_daily[sl].get(day, 0.0) for sl in base_sleeves)

    def combine(fold_map, replace=None):
        """fold_map: {sleeve:daily}. replace: {parent_sleeve: subset_daily} swaps that sleeve out."""
        fm = dict(fold_map)
        if replace:
            for k, v in replace.items():
                fm[k] = v
        return [base_row_sum(d) + sum(fm[nm].get(d, 0.0) for nm in fm) for d in all_days]

    series = {
        "deploy_3R":     combine(fold_daily_3R),
        "deploy_sd":     combine(fold_daily_sd),
        "veto_replace":  combine(fold_daily_sd, replace={"sub_xvol_pullback": veto_daily}),
        "vpacc_replace": combine(fold_daily_sd, replace={"sub_mid_dn_revert": vpacc_daily}),
        "both_replace":  combine(fold_daily_sd, replace={"sub_xvol_pullback": veto_daily,
                                                         "sub_mid_dn_revert": vpacc_daily}),
    }
    # additive overlay (size-up tilt): deploy_sd + veto subset as extra small conf
    series["veto_overlay_+0.20"] = [v + veto_daily.get(d, 0.0) * (0.20 / CONF["sub_xvol_pullback"])
                                    for v, d in zip(series["deploy_sd"], all_days)]

    fwd_mask = [d.year >= 2025 for d in all_days]
    sd_ref = statistics.pstdev(series["deploy_sd"])  # vol-match everything to the exit-honest book

    print(f"vol-match reference: deploy_sd daily std = {sd_ref:.5f}  (all books scaled so std==this)\n")
    print(f"{'book':>18} {'mean':>9} {'std':>8} {'sharpe':>7} {'volscale':>8} | "
          f"{'P@1%vm':>8} {'stress@1%vm':>11} {'stress@1.5%vm':>13} | {'P@1%fwd':>8}")

    report = {"vol_match_ref_std": round(sd_ref, 6), "books": {}}
    for label, s in series.items():
        m = statistics.fmean(s); sd = statistics.pstdev(s); shp = m / sd if sd else 0
        vs = sd_ref / sd if sd else 1.0
        s_stress = [(v * 1.5 if v < 0 else v) for v in s]
        s_fwd = [v for v, f in zip(s, fwd_mask) if f]
        p1 = W2.mc_series(s, 0.01 * vs, n_paths=N, seed_base=1)["p_pass"]
        st1 = W2.mc_series(s_stress, 0.01 * vs, n_paths=N, seed_base=999)["p_pass"]
        st15 = W2.mc_series(s_stress, 0.015 * vs, n_paths=N, seed_base=999)["p_pass"]
        pf = W2.mc_series(s_fwd, 0.01 * vs, n_paths=N, seed_base=777)["p_pass"]
        report["books"][label] = dict(mean=round(m, 6), std=round(sd, 6), sharpe=round(shp, 4),
                                      vol_scale=round(vs, 4), p_pass_1pct_vm=p1,
                                      stress_1pct_vm=st1, stress_1p5pct_vm=st15, p_pass_1pct_fwd=pf)
        print(f"{label:>18} {m:>+9.5f} {sd:>8.5f} {shp:>7.4f} {vs:>8.3f} | "
              f"{p1:>8.2%} {st1:>11.2%} {st15:>13.2%} | {pf:>8.2%}")

    (HERE / "KB6_OVERLAY_PASSRATE_RESULT.json").write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote KB6_OVERLAY_PASSRATE_RESULT.json")
    return report


if __name__ == "__main__":
    main()
