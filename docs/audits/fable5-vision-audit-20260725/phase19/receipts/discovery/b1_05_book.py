"""b1 step 5 — THE BOOK, priced jointly, then ablated on the same rows.

SPECIFICATION  (b1-BOOK-V1)  — every limb declared before this script was run, and every
limb inherited from a lane that published it, not chosen here:

  universe  all 24 pool instruments; no name is written into the rule
  GATE      admit a candidate only if its own broker-true round-trip toll at the
            decision instant is <= 0.60 bps of notional.   [h6 cell B threshold]
            toll = hour-true tick spread(symbol, broker hour) + broker commission
                 + measured live entry slippage + swap if the horizon crosses rollover
            all four terms are knowable at the decision instant -> the gate is EX-ANTE.
  ENTRY     place NOTHING at the decision. Wait 3 minutes. Enter at MARKET on the close
            of minute 3.                                    [h6 cell B; k plateau 1-3]
  EXIT      stop -1R (the declared risk unit, rebased to the fill). NO target. NO trail.
            Close at market at decision + 120 min.          [h6 cell B; trail-free by
            construction, so no bar-resolution premium -- h6-F8 / B613]
  SIZE      fixed fractional on the declared risk distance (constant-R book)
  no fill-probability floor (h6-F4: identically zero on this cohort)
  no cancel band (there is no resting order to cancel: entry is at market)

ABLATION is leave-one-out AND add-one-in, on the same substrate, at the same cost.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_np as N  # noqa: E402

M3 = ("2026-01", "2026-02", "2026-03")
GATE = 0.60
K = 3
EXIT = "STOPONLY"


def boot_days(net, day, B=4000, seed=20260806):
    rng = np.random.default_rng(seed)
    ud, inv = np.unique(day, return_inverse=True)
    G = len(ud)
    ssum = np.bincount(inv, weights=net, minlength=G)
    scnt = np.bincount(inv, minlength=G).astype(float)
    idx = rng.integers(0, G, size=(B, G))
    tot = ssum[idx].sum(axis=1)
    cnt = scnt[idx].sum(axis=1)
    m = tot / cnt
    m.sort()
    return {"B": B, "p025": float(m[int(0.025 * B)]), "p50": float(m[B // 2]),
            "p975": float(m[int(0.975 * B) - 1]),
            "p_le_0": float((m <= 0).mean())}


def main():
    t0 = time.time()
    M, G, rows = N.load()
    m3 = np.isin(M["month"], M3)
    fin = m3 & np.isfinite(M["cost_h1"])
    cbps_h1 = M["cost_h1"] * M["bpsfac"]
    cbps_hr = M["cost_hour"] * M["bpsfac"]
    BOOK = fin & (cbps_h1 <= GATE + 1e-12)
    g = G[(K, EXIT)]
    out = {"spec": {"gate_bps": GATE, "gate_cost_model": "h1 four-term broker-true",
                    "k": K, "exit": EXIT, "months": list(M3)}}

    # ------------------------------------------------------------------ headline
    for lab, cost in (("h1_broker_true_4term", M["cost_h1"]),
                      ("hour_true_3term", M["cost_hour"]),
                      ("flat_swarm_basis", M["cost_flat"])):
        s = N.score(g, cost, M, BOOK, want_equity=(lab == "h1_broker_true_4term"))
        if lab == "h1_broker_true_4term":
            out["equity"] = {"days": s.pop("equity_days"), "cum_net_R": s.pop("equity_net_R"),
                             "day_mean_net_R": s.pop("day_net_R")}
        out["headline_" + lab] = N.slim(s)

    sel = BOOK & np.isfinite(g)
    gg = g[sel]
    net = gg - M["cost_h1"][sel]
    out["bootstrap_day_block"] = boot_days(net, M["day"][sel])
    out["truncation"] = {
        "n": int(sel.sum()),
        "stopped_share": float((np.abs(gg + 1.0) < 1e-9).mean()),
        "time_exit_share": float((np.abs(gg + 1.0) >= 1e-9).mean()),
        "note": "STOPONLY has no target: every non-stop exit is the 120-minute horizon, "
                "i.e. the truncation share IS the time-exit share.",
        "mean_R_when_stopped": -1.0,
        "mean_R_when_time_exit": float(gg[np.abs(gg + 1.0) >= 1e-9].mean()),
        "gross_R_dist": {p: float(np.quantile(gg, q)) for p, q in
                         (("p01", .01), ("p05", .05), ("p25", .25), ("p50", .5),
                          ("p75", .75), ("p90", .9), ("p95", .95), ("p99", .99))},
        "max_gross_R": float(gg.max()),
        "share_gross_gt_2R": float((gg > 2).mean()),
        "share_gross_gt_5R": float((gg > 5).mean()),
        "top10_trades_share_of_total_net": float(
            np.sort(net)[-10:].sum() / net.sum()) if net.sum() > 0 else None,
        "top1pct_trades_share_of_total_net": float(
            np.sort(net)[-max(1, int(0.01 * len(net))):].sum() / net.sum())
        if net.sum() > 0 else None,
    }

    # ------------------------------------------------------------------ ablation
    # Each row: the book with ONE limb reverted to its "do nothing" default.
    ABL = {
        "BOOK (all limbs)": (BOOK, K, EXIT),
        "no gate (all 24 instruments)": (fin, K, EXIT),
        "gate at the shipped R rule instead": (
            fin & (M["cost_flat"] <= 0.15 + 1e-12), K, EXIT),
        "no entry delay (k=0, the shipped instant)": (BOOK, 0, EXIT),
        "entry delay k=5 (the swarm's)": (BOOK, 5, EXIT),
        "exit = shipped 2R target (INC)": (BOOK, K, "INC"),
        "exit = swarm TRAIL025": (BOOK, K, "TRAIL025"),
        "exit = 3R target": (BOOK, K, "T3S1"),
        "exit = 90-min time stop": (BOOK, K, "TS90S1"),
        "exit = 60-min time stop": (BOOK, K, "TS60S1"),
        "NOTHING (swarm repaired contract, whole book)": (fin, 5, "TRAIL025"),
    }
    out["ablation_leave_one_out"] = {}
    for lab, (m, k, cx) in ABL.items():
        out["ablation_leave_one_out"][lab] = N.slim(N.score(G[(k, cx)], M["cost_h1"], M, m))

    # add-one-in: start from the swarm's repaired contract on the whole book, add one limb
    ADD = {
        "swarm repaired contract (baseline)": (fin, 5, "TRAIL025"),
        "+ gate only": (BOOK, 5, "TRAIL025"),
        "+ entry k=3 only": (fin, 3, "TRAIL025"),
        "+ trail-free exit only": (fin, 5, EXIT),
        "+ gate + k=3": (BOOK, 3, "TRAIL025"),
        "+ gate + exit": (BOOK, 5, EXIT),
        "+ k=3 + exit": (fin, 3, EXIT),
        "+ all three (= BOOK)": (BOOK, 3, EXIT),
    }
    out["ablation_add_one_in"] = {}
    for lab, (m, k, cx) in ADD.items():
        out["ablation_add_one_in"][lab] = N.slim(N.score(G[(k, cx)], M["cost_h1"], M, m))

    # marginal value of each limb, held jointly (leave-one-out delta on net R)
    base_net = out["ablation_leave_one_out"]["BOOK (all limbs)"]["net_R"]
    out["marginal_net_R"] = {
        "gate": base_net - out["ablation_leave_one_out"]["no gate (all 24 instruments)"]["net_R"],
        "entry_delay": base_net - out["ablation_leave_one_out"][
            "no entry delay (k=0, the shipped instant)"]["net_R"],
        "trail_free_exit_vs_TRAIL025": base_net - out["ablation_leave_one_out"][
            "exit = swarm TRAIL025"]["net_R"],
        "no_target_vs_2R_target": base_net - out["ablation_leave_one_out"][
            "exit = shipped 2R target (INC)"]["net_R"],
        "full_horizon_vs_60min": base_net - out["ablation_leave_one_out"][
            "exit = 60-min time stop"]["net_R"],
    }

    # ------------------------------------------------------------------ per-axis
    out["per_symbol"] = {}
    for u in np.unique(M["symbol"][BOOK]):
        out["per_symbol"][str(u)] = N.slim(N.score(g, M["cost_h1"], M, BOOK & (M["symbol"] == u)))
    out["per_month"] = {}
    for u in M3:
        out["per_month"][u] = N.slim(N.score(g, M["cost_h1"], M, BOOK & (M["month"] == u)))

    # leave-one-out robustness: drop each symbol, each month, the best day(s), best hour
    lo = {}
    for u in np.unique(M["symbol"][BOOK]):
        lo["drop_" + str(u)] = N.slim(N.score(g, M["cost_h1"], M, BOOK & (M["symbol"] != u)))
    for u in M3:
        lo["drop_" + u] = N.slim(N.score(g, M["cost_h1"], M, BOOK & (M["month"] != u)))
    # drop the N best days by summed net
    ud, inv = np.unique(M["day"][sel], return_inverse=True)
    dsum = np.bincount(inv, weights=net, minlength=len(ud))
    order = np.argsort(-dsum)
    for nd in (1, 3, 5, 10):
        bad = set(ud[order[:nd]].tolist())
        dmask = np.array([d not in bad for d in M["day"]])
        lo[f"drop_best_{nd}_days"] = N.slim(N.score(g, M["cost_h1"], M, BOOK & dmask))
    # drop the best broker hour
    bh = M["broker_hour"]
    hsum = {int(h): float(net[bh[sel] == h].sum()) for h in np.unique(bh[sel])}
    besth = max(hsum, key=hsum.get)
    lo[f"drop_best_broker_hour_{besth}"] = N.slim(N.score(g, M["cost_h1"], M, BOOK & (bh != besth)))
    lo["_best_hour_net_R_sum"] = hsum
    # trimmed mean
    lo["trimmed_mean_10pct_net_R"] = float(
        np.sort(net)[int(0.05 * len(net)):len(net) - int(0.05 * len(net))].mean())
    lo["median_net_R"] = float(np.median(net))
    out["robustness_leave_out"] = lo

    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_BOOK_V1.json", "w") as f:
        json.dump(out, f, indent=1)

    h = out["headline_h1_broker_true_4term"]
    print("=" * 78)
    print("b1-BOOK-V1  gate<=0.60bps | enter at market at +3min | stop -1R, no target,")
    print("            no trail, close at +120min | Jan+Feb+Mar 2026")
    print("=" * 78)
    print(f"  n              {h['n']}   ({h['n']/int(fin.sum())*100:.2f}% of the 43,755 book)")
    print(f"  gross          {h['gross_R']:+.6f} R   ({h['gross_bps']:+.4f} bps)")
    print(f"  cost           {h['cost_R']:.6f} R   ({h['cost_bps']:.4f} bps)  [strictest basis]")
    print(f"  NET            {h['net_R']:+.6f} R   ({h['net_bps']:+.4f} bps)")
    print(f"  edge:toll      {h['ratio_R']:.4f} R  /  {h['ratio_bps']:.4f} bps")
    print(f"  win rate       {h['win_rate_net']:.4f} net   {h['win_rate_gross']:.4f} gross")
    print(f"  t(net)         {h['t_net']:+.3f} trade-level   {h['t_net_day']:+.3f} day-clustered")
    print(f"  days           {h['n_days_net_pos']}/{h['n_days']} net-positive")
    print(f"  total          {h['total_net_R']:+.2f} R   maxDD {h['max_dd_R']:.2f} R"
          f"   ret/DD {h['ret_over_dd']:.2f}")
    print(f"  months         " + "  ".join(
        f"{m[-2:]}:{h['m_'+m]['net_R']:+.5f}" for m in M3))
    print(f"  truncation     {out['truncation']['time_exit_share']:.4f} time-exit / "
          f"{out['truncation']['stopped_share']:.4f} stopped")
    b = out["bootstrap_day_block"]
    print(f"  bootstrap      95% CI [{b['p025']:+.5f}, {b['p975']:+.5f}]  P(net<=0)={b['p_le_0']:.4f}")
    print()
    print("ABLATION (leave one out, same cost basis)")
    for k2, v in out["ablation_leave_one_out"].items():
        print(f"  {k2:46} n={v['n']:>6} net={v['net_R']:>+9.5f} ratio={(v['ratio_R'] or 0):>7.3f}")
    print()
    print("ADD ONE IN (from the swarm's repaired contract)")
    for k2, v in out["ablation_add_one_in"].items():
        print(f"  {k2:46} n={v['n']:>6} net={v['net_R']:>+9.5f} ratio={(v['ratio_R'] or 0):>7.3f}")
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
