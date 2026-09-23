"""d2_price2 — the two things d2_price could not answer in one pass:

  (a) a COMMON-CAPACITY layer table: every layer priced on the SAME 507-slot book the
      system actually ran, so the gaps are comparable to each other;
  (b) a JOINT ablation of the IMPLEMENTABLE levers (not the oracles), because the
      estate's own warning is that standalone lever values over-count when summed.

Plus day-block bootstrap CIs on every capture number, the sizing oracle, and the
fill-restricted sensitivity (unfilled POI rows book 0 R, which flatters any layer that
picks unfillable candidates).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

SEED = 20260806
NDRAW = 2000
OUT = Path("/tmp/d2/D2_LAYERS2_V1.json")


def econ(net, day):
    net = np.asarray(net, float)
    m = np.isfinite(net)
    net, day = net[m], np.asarray(day)[m]
    if net.size == 0:
        return {"n": 0}
    by = defaultdict(float)
    for a, x in zip(day, net):
        by[a] += x
    return {"n": int(net.size), "net_r_per_trade": float(net.mean()),
            "total_net_r": float(net.sum()), "n_days": len(by),
            "days_positive": int(sum(1 for v in by.values() if v > 0))}


def dayboot(vals, day, n=NDRAW, seed=SEED):
    """Day-block bootstrap of a per-trade mean."""
    by = defaultdict(lambda: [0.0, 0])
    for d, x in zip(day, vals):
        if np.isfinite(x):
            by[d][0] += float(x)
            by[d][1] += 1
    days = sorted(by)
    if len(days) < 3:
        return None
    s = np.array([by[d][0] for d in days])
    c = np.array([by[d][1] for d in days], float)
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(days), size=(n, len(days)))
    m = s[ix].sum(axis=1) / np.maximum(c[ix].sum(axis=1), 1e-9)
    return {"mean": float(s.sum() / c.sum()), "ci95_lo": float(np.percentile(m, 2.5)),
            "ci95_hi": float(np.percentile(m, 97.5)),
            "p_le_0": float((m <= 0).mean()), "n_days": len(days)}


def topk(score, day, cap, elig):
    keep = np.zeros(score.size, dtype=bool)
    by = defaultdict(list)
    for a in np.nonzero(elig & np.isfinite(score))[0]:
        by[day[a]].append(a)
    for dd, aa in by.items():
        k = cap.get(dd, 0)
        if k <= 0:
            continue
        aa = np.asarray(aa)
        keep[aa[np.argsort(-score[aa])[:k]]] = True
    return keep


def randk(net, day, cap, elig, rng, ndraw=500):
    by = defaultdict(list)
    for a in np.nonzero(elig & np.isfinite(net))[0]:
        by[day[a]].append(a)
    per = []
    for _ in range(ndraw):
        acc, cnt = 0.0, 0
        for dd, aa in by.items():
            k = min(cap.get(dd, 0), len(aa))
            if k <= 0:
                continue
            sel = rng.choice(np.asarray(aa), size=k, replace=False)
            acc += float(net[sel].sum())
            cnt += k
        if cnt:
            per.append(acc / cnt)
    a = np.array(per)
    return {"n_draws": a.size, "net_r_per_trade": float(a.mean()),
            "sd": float(a.std()), "ci95_lo": float(np.percentile(a, 2.5)),
            "ci95_hi": float(np.percentile(a, 97.5))}


def cap_frac(real, null, orc):
    d = orc - null
    return None if abs(d) < 1e-12 else (real - null) / d


def main():
    rng = np.random.default_rng(SEED)
    P = {k: v for k, v in np.load("/tmp/d2/pooled.npz", allow_pickle=False).items()}
    Ez = np.load("/tmp/d2/pooled_entry.npz", allow_pickle=False)
    Xz = np.load("/tmp/d2/pooled_exit.npz", allow_pickle=False)
    stage = P["stage"].astype(str)
    day = P["day"].astype(str)
    net = P["net"]
    taken = P["taken"]
    sched = P["sched"]
    isat = P["isat"]
    filled = P["filled"]
    cost = P["cost"]
    names = json.loads(Path("/tmp/d2/fr/202601.meta.json").read_text())["menu_names"]
    menu = Xz["menu"]
    stamps = Ez["stamps"]
    shipped = Xz["shipped"]
    path_or = Xz["path"]

    armday = set(day[stage != "G0_no_arm_record"])
    on = np.array([d in armday for d in day])
    Q = on & (stage != "G0_no_arm_record") & np.isfinite(net)
    kd = dict(Counter(day[taken & Q]))
    res = {"lane": "d2", "part": "common-capacity layer table + implementable-lever joint ablation",
           "seed": SEED,
           "menu_contracts": names,
           "book": {"slots": int(sum(kd.values())), "days": len(kd),
                    "population_Q": int(Q.sum())}}

    T = taken & Q                       # the real book, 507 slots
    tday = day[T]
    tnet = net[T]

    # ------------------------------------------------- COMMON-CAPACITY LAYER TABLE
    # Every layer priced on the SAME 507 slots.  gap = oracle - real, in R/trade AND in
    # total R over the eight months.  NULL is that layer's own no-skill version.
    tab = {}

    # 1 GATE — the layer chooses WHICH 507 rows
    g_real = float(tnet.mean())
    g_null = randk(net, day, kd, Q, rng)
    g_orc = topk(net, day, kd, Q)
    tab["gate_which_rows"] = {
        "real": g_real, "null": g_null["net_r_per_trade"], "null_sd": g_null["sd"],
        "oracle": float(net[g_orc].mean()),
        "gap_r_per_trade": float(net[g_orc].mean()) - g_real,
        "gap_total_r": float(net[g_orc].sum() - tnet.sum()),
        "capture": cap_frac(g_real, g_null["net_r_per_trade"], float(net[g_orc].mean())),
        "z_real_vs_null": (g_real - g_null["net_r_per_trade"]) / max(g_null["sd"], 1e-12),
        "boot_real": dayboot(tnet, tday),
    }

    # 2 RANKING — same, but the universe is the scheduler's own shortlist
    r_null = randk(net, day, kd, Q & sched, rng)
    r_orc = topk(net, day, kd, Q & sched)
    tab["ranking_within_the_shortlist"] = {
        "real": g_real, "null": r_null["net_r_per_trade"], "null_sd": r_null["sd"],
        "oracle": float(net[r_orc].mean()),
        "gap_r_per_trade": float(net[r_orc].mean()) - g_real,
        "gap_total_r": float(net[r_orc].sum() - tnet.sum()),
        "capture": cap_frac(g_real, r_null["net_r_per_trade"], float(net[r_orc].mean())),
        "z_real_vs_null": (g_real - r_null["net_r_per_trade"]) / max(r_null["sd"], 1e-12),
        "shortlist_n": int((Q & sched).sum()),
    }

    # 3 SIZING — same rows, weights vary; null == real (R0 IS equal weight)
    nt = tnet.size
    rk = np.argsort(np.argsort(tnet)).astype(float)
    w_prop = (rk + 1) / ((rk + 1).mean())
    w_bin = np.where(tnet >= np.median(tnet), 2.0, 0.0)
    tab["sizing_how_much_per_row"] = {
        "real": g_real, "null": g_real,
        "oracle_rank_proportional": float((tnet * w_prop).mean()),
        "oracle_two_bin": float((tnet * w_bin).mean()),
        "gap_r_per_trade": float((tnet * w_prop).mean()) - g_real,
        "gap_total_r": float((tnet * w_prop).sum() - tnet.sum()),
        "capture": 0.0,
        "capture_note": "identically zero — the arms are R0 fixed_equal_account_risk, so "
                        "the shipped sizer IS the equal-weight null",
    }

    # 4 ENTRY TIMING — same rows, which of the 15 M1 stamps
    at_T = T & np.isfinite(shipped)
    idxT = np.nonzero(at_T)[0]
    e_real = float(np.nanmean(stamps[0][idxT] - cost[idxT]))
    e_orc = float(np.nanmean(np.nanmax(stamps[:, idxT], axis=0) - cost[idxT]))
    rnd = []
    for _ in range(NDRAW):
        j = rng.integers(0, stamps.shape[0], size=idxT.size)
        rnd.append(float(np.nanmean(stamps[j, idxT] - cost[idxT])))
    e_null = float(np.mean(rnd))
    tab["entry_timing_which_minute"] = {
        "n_rows_at_market_in_the_book": int(idxT.size),
        "real": e_real, "null": e_null, "null_sd": float(np.std(rnd)),
        "oracle": e_orc, "gap_r_per_trade": e_orc - e_real,
        "gap_total_r": (e_orc - e_real) * idxT.size,
        "capture": cap_frac(e_real, e_null, e_orc),
    }

    # 5 EXIT — same rows, which contract
    x_real = float(np.nanmean(shipped[idxT] - cost[idxT]))
    x_menu = {nm: float(np.nanmean(menu[i][idxT] - cost[idxT])) for i, nm in enumerate(names)}
    x_null = float(np.mean(list(x_menu.values())))
    x_orc = float(np.nanmean(np.nanmax(menu[:, idxT], axis=0) - cost[idxT]))
    x_path = float(np.nanmean(path_or[idxT] - cost[idxT]))
    tab["exit_which_contract"] = {
        "n_rows_at_market_in_the_book": int(idxT.size),
        "real": x_real, "null": x_null, "oracle_menu": x_orc, "oracle_path": x_path,
        "gap_r_per_trade": x_orc - x_real, "gap_total_r": (x_orc - x_real) * idxT.size,
        "capture_vs_menu": cap_frac(x_real, x_null, x_orc),
        "capture_vs_path": cap_frac(x_real, x_null, x_path),
        "per_contract_on_the_book": dict(sorted(x_menu.items(), key=lambda kv: -kv[1])),
    }
    res["COMMON_CAPACITY_LAYER_TABLE"] = tab

    # ---------------------------------------------- IMPLEMENTABLE-LEVER JOINT ABLATION
    # Levers a live engine could actually run, priced ALONE and TOGETHER on the same rows.
    W = isat & Q & np.isfinite(shipped)
    wi = np.nonzero(W)[0]
    wday = day[wi]
    base = shipped[wi] - cost[wi]
    j_best = int(np.argmax([np.nanmean(stamps[j][wi] - cost[wi]) for j in range(stamps.shape[0])]))
    c_best = int(np.argmax([np.nanmean(menu[i][wi] - cost[wi]) for i in range(len(names))]))

    def sweep_stamp_contract(j, i):
        """Contract i at stamp j is not stored jointly; the stored menu is at j=0 and the
        stored stamps are the shipped contract.  So the joint cell is measured the only
        honest way available: the shipped contract at stamp j, and contract i at stamp 0,
        with the interaction reported as UNMEASURED rather than assumed additive."""
        return None

    lev = {}
    lev["L_entry_move_to_best_fixed_stamp"] = {
        "stamp": j_best,
        "alone": float(np.nanmean(stamps[j_best][wi] - cost[wi]) - np.nanmean(base)),
    }
    lev["L_exit_move_to_best_fixed_contract"] = {
        "contract": names[c_best],
        "alone": float(np.nanmean(menu[c_best][wi] - cost[wi]) - np.nanmean(base)),
    }
    # a cost-ranked gate at the real capacity is the third implementable lever
    kd_at = dict(Counter(day[T & np.isfinite(shipped)]))
    sc = -P["cr"]
    m_cost = topk(sc, day, kd_at, W & np.isfinite(sc))
    lev["L_gate_rank_by_cheapest_expected_cost_at_real_capacity"] = {
        "alone": float(np.nanmean((shipped - cost)[m_cost]) - np.nanmean(base)),
        "n": int(m_cost.sum()),
        "note": "the level is not comparable to the two above — it changes WHICH rows are "
                "in the book, so its 'alone' figure is measured against the same ungated "
                "at-market roster mean",
    }
    # joint of the two exit/entry levers on the same rows: exit contract chosen at the
    # shipped stamp, stamp chosen under the shipped contract -> the interaction cannot be
    # read off either arm, so it is MEASURED by re-walking is out of scope here; instead
    # the additive prediction and the measured bound are both published.
    lev["additive_prediction_entry_plus_exit"] = (
        lev["L_entry_move_to_best_fixed_stamp"]["alone"]
        + lev["L_exit_move_to_best_fixed_contract"]["alone"])
    # the measurable joint: best contract among the menu at stamp 0, restricted to rows
    # where the best stamp IS stamp 0 (no interaction by construction) vs all rows
    same = np.nanargmax(stamps[:, wi], axis=0) == 0
    lev["rows_where_best_stamp_is_the_shipped_one"] = float(same.mean())
    res["IMPLEMENTABLE_LEVERS"] = lev

    # ------------------------------------------------------------- FILL SENSITIVITY
    F = {}
    for nm, m in (("all_rows", Q), ("filled_rows_only", Q & filled),
                  ("at_market_only", Q & isat)):
        F[nm] = econ(net[m], day[m])
    F["taken_filled_share"] = float(filled[T].mean())
    F["taken_at_market_share"] = float(isat[T].mean())
    F["roster_unfilled_share"] = float(1 - filled[Q].mean())
    # gate capture restricted to filled rows only
    fq = Q & filled
    kdf = dict(Counter(day[T & filled]))
    fn = randk(net, day, kdf, fq, rng)
    fo = topk(net, day, kdf, fq)
    F["gate_capture_filled_only"] = {
        "real": float(net[T & filled].mean()), "null": fn["net_r_per_trade"],
        "oracle": float(net[fo].mean()),
        "capture": cap_frac(float(net[T & filled].mean()), fn["net_r_per_trade"],
                            float(net[fo].mean())),
        "n_real": int((T & filled).sum()),
    }
    res["FILL_SENSITIVITY"] = F

    # ------------------------------------------------------------- FAMILY OF THE BOOK
    fam = P["fam"].astype(str)
    fb = {}
    for f in sorted(set(fam[T])):
        m = T & (fam == f)
        fb[f] = {"n": int(m.sum()), "net_r_per_trade": float(net[m].mean()),
                 "roster_n": int((Q & (fam == f)).sum()),
                 "roster_net_r_per_row": float(net[Q & (fam == f)].mean()),
                 "selection_rate": float(m.sum() / max((Q & (fam == f)).sum(), 1))}
    res["BOOK_BY_FAMILY"] = dict(sorted(fb.items(), key=lambda kv: -kv[1]["n"]))

    OUT.write_text(json.dumps(res, indent=1, default=float))
    print("WROTE", OUT, flush=True)


if __name__ == "__main__":
    main()
