"""m1_analyse — the broad V4 family, restated on the repaired instrument.

Every table wave 19 published for this family, recomputed from ONE walk of the whole
eight-window population (`m1_walk.py`), on four arms:

  OLD   the estate's published instrument — no spread crossing, legacy generator
  GEN   generator repaired only (r2), old walker
  WALK  walker repaired only (r1), legacy generator
  BOTH  the repaired instrument

The uncorrected arm is byte-equal to `R2_ARM_ECON_V1.json -> arms.legacy` (checked in
`control`), so the A/B is exact by construction.

TWO NETS, and the difference between them is not cosmetic
---------------------------------------------------------
`published net = gross_old - (spread + commission + slippage + swap)/d` charges the
spread as a LEVEL.  The corrected walk charges it as a RESOLUTION effect — it moves the
stop one spread nearer and the target one spread further — so charging both double-counts
it.  r1 settled this on the live estate; the same arithmetic applies here:

    corrected net = gross_cor - (commission + slippage + swap)/d

Both are published, and so is the double-charged variant, explicitly labelled, because it
is the bound a reader who does not accept the substitution would want.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict

import numpy as np

W8 = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
REPO_DISC = ("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/"
             "fable5-vision-audit-20260725/phase19/receipts/discovery")
DEFECT_FAMILY = "current_breaker_re_entry"
RR = 1.5
REASON = {0: "stop", 1: "target", 2: "path_end", 3: "no_fill"}


def load():
    cols = defaultdict(list)
    fams, syms = [], []
    for w in W8:
        z = np.load(f"/tmp/m1/M1_{w}.npz", allow_pickle=True)
        f = np.asarray(z["_fams"])
        s = np.asarray(z["_syms"])
        for k in z.files:
            if k.startswith("_"):
                continue
            cols[k].append(z[k])
        cols["fam_s"].append(f[z["fam"]])
        cols["sym_s"].append(s[z["sym"]])
        cols["win"].append(np.full(z["day"].size, w))
        fams.append(f)
        syms.append(s)
    out = {k: np.concatenate(v) for k, v in cols.items()}
    return out


def econ(g, cost, tag):
    """gross/net economics + win rate against its own payoff-implied breakeven."""
    n = g.size
    if n == 0:
        return {"tag": tag, "n": 0}
    net = g - cost
    wins, loss = g[g > 0], g[g <= 0]
    aw = float(wins.mean()) if wins.size else 0.0
    al = float(-loss.mean()) if loss.size else 0.0
    pay = aw / al if al else None
    be = 1 / (1 + pay) if pay else None
    nw, nl = net[net > 0], net[net <= 0]
    naw = float(nw.mean()) if nw.size else 0.0
    nal = float(-nl.mean()) if nl.size else 0.0
    npay = naw / nal if nal else None
    nbe = 1 / (1 + npay) if npay else None
    se = float(net.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
    return {
        "tag": tag, "n": int(n),
        "gross": float(g.mean()), "cost": float(cost.mean()), "net": float(net.mean()),
        "net_se": se, "net_ci95": [float(net.mean() - 1.96 * se), float(net.mean() + 1.96 * se)],
        "net_total": float(net.sum()),
        "gross_wr": float((g > 0).mean()), "gross_avg_win": aw, "gross_avg_loss": al,
        "gross_payoff": pay, "gross_breakeven_wr": be,
        "gross_gap_pp": (float((g > 0).mean()) - be) * 100 if be else None,
        "net_wr": float((net > 0).mean()), "net_avg_win": naw, "net_avg_loss": nal,
        "net_payoff": npay, "net_breakeven_wr": nbe,
        "net_gap_pp": (float((net > 0).mean()) - nbe) * 100 if nbe else None,
    }


def main(out_path):
    D = load()
    n = D["day"].size
    d = D["d"]
    dbps = D["dbps"]
    fam = D["fam_s"]
    win = D["win"]
    is_poi = np.isin(fam, POI)

    px_all = D["px_spread"] + D["px_comm"] + D["px_slip"] + D["px_swap"]
    px_nospread = D["px_comm"] + D["px_slip"] + D["px_swap"]

    g_old, g_cor, g_era = D["g_old"], D["g_cor"], D["g_era"]
    f_old, f_cor = D["fill_old"], D["fill_cor"]

    # tolls in R, charged once, only on fill, per arm's own fill set
    c_old = np.where(f_old, px_all / d, 0.0)
    c_cor_full = np.where(f_cor, px_all / d, 0.0)          # double-charged bound
    c_cor = np.where(f_cor, px_nospread / d, 0.0)          # r1's substitution
    c_gen = c_old                                           # generator-only arm: old walker

    # --- the repaired emission contract, re-derived from the roster (not taken on trust)
    refused_past_stop = is_poi & (D["gap"] < -1.0)
    refused_stale = D["age"] >= 15
    kept_derived = ~(refused_past_stop | refused_stale)
    kept_roster = D["kept"]

    out = {
        "what": "the broad V4 family restated on the repaired instrument (r1 walker + r2 generator)",
        "population": {"windows": W8, "rows_walked": int(n),
                       "note": "every emission of the eight open windows that the M1 tape "
                               "and the M15 selected-bar series can both resolve"},
        "contract": {"target_r": RR, "horizon_m1_bars": 120, "tie": "stop wins",
                     "at_market_families": "market order at the decision instant",
                     "poi_families": "honest resting limit at the emitted level",
                     "corrected_at_market": "FILL anchoring, quote_side.replay_anchor",
                     "corrected_poi": "LEVEL anchoring + corrected entry trigger"},
    }

    # ---------------------------------------------------------------- control
    out["control"] = {
        "uncorrected_arm_vs_R2_ARM_ECON_legacy": econ(g_old, c_old, "OLD_all_emissions"),
        "refusals_rederived": {
            "past_stop": int(refused_past_stop.sum()),
            "stale": int(refused_stale.sum()),
            "both": int((refused_past_stop & refused_stale).sum()),
            "union": int((~kept_derived).sum()),
            "kept": int(kept_derived.sum()),
            "agrees_with_repaired_roster_rowwise": int((kept_derived == kept_roster).sum()),
            "disagreements": int((kept_derived != kept_roster).sum()),
        },
    }

    # ---------------------------------------------------------------- funnel
    # legacy "clean" cohort, f1's definition: filled, minus the defect family, minus
    # rows born past their own stop
    clean_mask = f_old & (fam != DEFECT_FAMILY) & ~(D["gap"] < -1.0)

    def stage(mask, g, c, tag):
        e = econ(g[mask], c[mask], tag)
        fl = f_cor if c is c_cor or c is c_cor_full else f_old
        e["fills"] = int(fl[mask].sum())
        e["fill_rate"] = float(fl[mask].mean()) if mask.sum() else None
        e["d_bps_median"] = float(np.median(dbps[mask])) if mask.sum() else None
        # price units: bps of price captured and paid, per row
        e["gross_bps"] = float((g[mask] * dbps[mask]).mean())
        e["toll_bps_full"] = float((px_all[mask] / D["e"][mask] * 1e4).mean())
        e["toll_bps_nospread"] = float((px_nospread[mask] / D["e"][mask] * 1e4).mean())
        return e

    # f1's day restriction — the sealed arm's OWN trading days, which is what the
    # published funnel (1,118,694 emissions) was measured on.  The whole population is
    # this lane's primary; this arm exists so the two tables can be compared row for row.
    import json as _json
    AD = _json.load(open(REPO_DISC + "/f1_ARM_TRADING_DAYS_V1.json"))
    ok_days = set()
    for _w, _ds in AD.items():
        for _d in _ds:
            ok_days.add(int(_d.replace("-", "")))
    dayres = np.isin(D["day"], np.array(sorted(ok_days)))

    F = {}
    F["A_emitted_legacy_OLD"] = stage(np.ones(n, bool), g_old, c_old, "A")
    F["A_emitted_legacy_WALK"] = stage(np.ones(n, bool), g_cor, c_cor, "A_corrected")
    F["B_emitted_repaired_GEN"] = stage(kept_derived, g_old, c_old, "B")
    F["B_emitted_repaired_BOTH"] = stage(kept_derived, g_cor, c_cor, "B_corrected")
    F["C_filled_legacy_OLD"] = stage(f_old, g_old, c_old, "C")
    F["C_filled_repaired_OLD"] = stage(kept_derived & f_old, g_old, c_old, "C_gen")
    F["C_filled_repaired_BOTH"] = stage(kept_derived & f_cor, g_cor, c_cor, "C_both")
    F["D_clean_legacy_OLD"] = stage(clean_mask, g_old, c_old, "D_legacy_clean")
    F["D_clean_legacy_BOTH"] = stage(clean_mask & f_cor, g_cor, c_cor, "D_legacy_clean_both")
    out["funnel"] = F

    # --- the same funnel restricted to f1's arm trading days, for exact comparability
    FD = {}
    FD["A_emitted_legacy_OLD"] = stage(dayres, g_old, c_old, "A_dayres")
    FD["B_emitted_repaired_GEN"] = stage(dayres & kept_derived, g_old, c_old, "B_dayres")
    FD["B_emitted_repaired_BOTH"] = stage(dayres & kept_derived, g_cor, c_cor, "B_dayres_both")
    FD["C_filled_legacy_OLD"] = stage(dayres & f_old, g_old, c_old, "C_dayres")
    FD["C_filled_repaired_BOTH"] = stage(dayres & kept_derived & f_cor, g_cor, c_cor, "C_dayres_both")
    FD["D_clean_legacy_OLD"] = stage(dayres & clean_mask, g_old, c_old, "D_dayres")
    FD["D_clean_legacy_BOTH"] = stage(dayres & clean_mask & f_cor, g_cor, c_cor, "D_dayres_both")
    out["funnel_f1_day_restricted"] = FD

    # the double-charged bound, on the two rows that matter
    out["double_charged_bound"] = {
        "B_emitted_repaired": stage(kept_derived, g_cor, c_cor_full, "B_double"),
        "C_filled_repaired": stage(kept_derived & f_cor, g_cor, c_cor_full, "C_double"),
    }

    # era-spread sensitivity
    ok = np.isfinite(g_era)
    out["spread_sensitivity_era_model"] = {
        "rows": int(ok.sum()),
        "s_tick_over_s_era_median": float(np.nanmedian(D["s_tick"] / D["s_era"])),
        "B_emitted_repaired_era": econ(g_era[kept_derived & ok], c_cor[kept_derived & ok],
                                       "B_era"),
    }

    # ---------------------------------------------------------------- exit migration
    mig = defaultdict(int)
    ch = (D["r_old"] != D["r_cor"])
    for a, b in zip(D["r_old"][ch], D["r_cor"][ch]):
        mig[f"{REASON[int(a)]}->{REASON[int(b)]}"] += 1
    kd = kept_derived
    migk = defaultdict(int)
    for a, b in zip(D["r_old"][ch & kd], D["r_cor"][ch & kd]):
        migk[f"{REASON[int(a)]}->{REASON[int(b)]}"] += 1
    dl = g_cor - g_old
    out["exit_migration"] = {
        "all_rows": {"n_changed": int(ch.sum()), "share": float(ch.mean()),
                     "transitions": dict(sorted(mig.items(), key=lambda kv: -kv[1]))},
        "repaired_rows": {"n_changed": int((ch & kd).sum()),
                          "share": float((ch & kd).mean()),
                          "transitions": dict(sorted(migk.items(), key=lambda kv: -kv[1]))},
        "delta_r_mean_all": float(dl.mean()),
        "delta_r_mean_repaired": float(dl[kd].mean()),
        "delta_share_from_reason_changes": float(dl[ch].sum() / dl.sum()) if dl.sum() else None,
        "delta_on_unchanged_rows": float(dl[~ch].sum()),
    }

    # ---------------------------------------------------------------- family table
    fams = sorted(set(fam.tolist()))
    ftab = {}
    for f in fams:
        m = fam == f
        row = {"kind": "POI_limit" if f in POI else "at_market",
               "n_legacy": int(m.sum()), "n_repaired": int((m & kd).sum())}
        for arm, (gg, cc, mm) in (("OLD", (g_old, c_old, m)),
                                  ("GEN", (g_old, c_old, m & kd)),
                                  ("WALK", (g_cor, c_cor, m)),
                                  ("BOTH", (g_cor, c_cor, m & kd))):
            e = econ(gg[mm], cc[mm], f + "_" + arm)
            pos = 0
            for w in W8:
                sel = mm & (win == w)
                if sel.sum() and gg[sel].mean() > 0:
                    pos += 1
            row[arm] = {"n": e["n"], "gross": e.get("gross"), "cost": e.get("cost"),
                        "net": e.get("net"), "months_gross_positive": pos,
                        "gross_wr": e.get("gross_wr"),
                        "gross_breakeven_wr": e.get("gross_breakeven_wr")}
        # filled-only, repaired+corrected
        row["BOTH_filled"] = econ(g_cor[m & kd & f_cor], c_cor[m & kd & f_cor], f + "_BOTHf")
        ftab[f] = row
    out["by_family"] = ftab

    # ---------------------------------------------------------------- toll deciles
    dec = {}
    for arm, (gg, cc, mm, fl) in (("OLD", (g_old, c_old, f_old, f_old)),
                                  ("BOTH", (g_cor, c_cor, kd & f_cor, f_cor))):
        sel = np.nonzero(mm)[0]
        order = sel[np.argsort(dbps[sel], kind="stable")]
        k = order.size // 10
        rows = []
        for i in range(10):
            ix = order[i * k:(i + 1) * k] if i < 9 else order[i * k:]
            e = econ(gg[ix], cc[ix], f"dec{i}")
            e["d_bps_lo"] = float(dbps[ix].min())
            e["d_bps_hi"] = float(dbps[ix].max())
            e["gross_bps"] = float((gg[ix] * dbps[ix]).mean())
            e["toll_bps_full"] = float((px_all[ix] / D["e"][ix] * 1e4).mean())
            rows.append(e)
        dec[arm] = rows
    out["toll_deciles"] = dec

    # ---------------------------------------------------------------- per-window
    pw = {}
    for w in W8:
        m = win == w
        pw[w] = {
            "OLD_emitted": econ(g_old[m], c_old[m], w),
            "BOTH_emitted": econ(g_cor[m & kd], c_cor[m & kd], w),
            "BOTH_filled": econ(g_cor[m & kd & f_cor], c_cor[m & kd & f_cor], w),
            "n_legacy": int(m.sum()), "n_repaired": int((m & kd).sum()),
        }
    out["per_window"] = pw

    # ---------------------------------------------------------------- verdict leg 1+3
    # price-unit shortfall on the filled, repaired, corrected book
    for name, mm, gg, tollpx in (
            ("legacy_clean_OLD", clean_mask, g_old, px_all),
            ("repaired_filled_OLD", kd & f_old, g_old, px_all),
            ("repaired_filled_CORRECTED", kd & f_cor, g_cor, px_nospread)):
        gb = float((gg[mm] * dbps[mm]).mean())
        tb = float((tollpx[mm] / D["e"][mm] * 1e4).mean())
        out.setdefault("price_units", {})[name] = {
            "n": int(mm.sum()), "gross_bps": gb, "toll_bps": tb, "net_bps": gb - tb,
            "shortfall_factor": (tb / gb) if gb > 0 else None,
            "gross_is_negative": bool(gb <= 0),
        }
    # free broker: zero spread means the correction has nothing to charge, so the book
    # earns the UNCORRECTED gross on the repaired roster
    for name, mm in (("legacy_clean", clean_mask), ("repaired_filled", kd & f_old),
                     ("repaired_emitted", kd)):
        out.setdefault("free_broker", {})[name] = {
            "n": int(mm.sum()),
            "net_at_zero_cost_r": float(g_old[mm].mean()),
            "current_toll_r": float(c_old[mm].mean()),
            "reduction_needed_pct": float(
                (c_old[mm].mean() - g_old[mm].mean()) / c_old[mm].mean() * 100)
            if c_old[mm].mean() else None,
            "feasible": bool(g_old[mm].mean() > 0),
        }

    json.dump(out, open(out_path, "w"), indent=1)

    # ---- console
    print("CONTROL uncorrected == R2 legacy:",
          {k: round(v, 6) for k, v in out["control"]["uncorrected_arm_vs_R2_ARM_ECON_legacy"].items()
           if k in ("gross", "cost", "net")}, "n",
          out["control"]["uncorrected_arm_vs_R2_ARM_ECON_legacy"]["n"])
    print("refusals", out["control"]["refusals_rederived"])
    print()
    print(f"{'stage':30s} {'n':>9s} {'gross':>10s} {'toll':>9s} {'net':>10s} {'wr':>7s} {'be':>7s} {'gap_pp':>7s}")
    for k, v in F.items():
        print(f"{k:30s} {v['n']:9d} {v['gross']:10.5f} {v['cost']:9.5f} {v['net']:10.5f} "
              f"{100*v['gross_wr']:7.3f} {100*(v['gross_breakeven_wr'] or 0):7.3f} "
              f"{(v['gross_gap_pp'] or 0):7.3f}")
    print()
    print("EXIT MIGRATION", out["exit_migration"]["repaired_rows"]["n_changed"],
          out["exit_migration"]["repaired_rows"]["transitions"])
    print()
    print(f"{'family':36s} {'kind':11s} {'n_leg':>8s} {'n_rep':>8s} {'OLD':>9s} {'BOTH':>9s} {'mo+':>4s}")
    for f, v in ftab.items():
        print(f"{f:36s} {v['kind']:11s} {v['n_legacy']:8d} {v['n_repaired']:8d} "
              f"{v['OLD']['gross']:9.5f} {v['BOTH']['gross']:9.5f} "
              f"{v['BOTH']['months_gross_positive']:4d}")
    print()
    print()
    print("DAY-RESTRICTED funnel (f1's arm trading days):")
    for k, v in FD.items():
        print(f"{k:30s} {v['n']:9d} {v['gross']:10.5f} {v['cost']:9.5f} {v['net']:10.5f}")
    print()
    for arm, rows in dec.items():
        print(f"TOLL DECILES [{arm}]  (by the generator's own stop width)")
        print(f"{'dec':>4s} {'n':>8s} {'lo_bps':>9s} {'hi_bps':>9s} {'gross_R':>9s} "
              f"{'toll_R':>9s} {'net_R':>9s} {'gross_bps':>10s} {'toll_bps':>9s}")
        for i, e in enumerate(rows):
            print(f"{i:4d} {e['n']:8d} {e['d_bps_lo']:9.3f} {e['d_bps_hi']:9.3f} "
                  f"{e['gross']:9.5f} {e['cost']:9.5f} {e['net']:9.5f} "
                  f"{e['gross_bps']:10.4f} {e['toll_bps_full']:9.4f}")
        print()
    print("PRICE UNITS", json.dumps(out["price_units"], indent=1))
    print("FREE BROKER", json.dumps(out["free_broker"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
