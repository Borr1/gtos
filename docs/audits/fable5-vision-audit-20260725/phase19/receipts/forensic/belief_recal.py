#!/usr/bin/env python3
"""BELIEF-RECAL — honest-belief subpopulation screen (Session FA, Phase B item 3).

Protocol implemented exactly as declared in BELIEF_RECAL.md §1 (the declaration was
written to disk BEFORE this script computed any outcome aggregate; this script enforces
the same order internally: the declaration block is emitted from axis fields alone,
then outcomes are aggregated).

EVIDENCE CLASS: DEVELOPMENT-FITTED lane evidence, billed:false, never admission-grade.
February is used-once VAL — attribution-only; selection is January-only.
No March-2026 data, no live-forward (2026-07-29+) data.

Partition (declared, fixed, no fitting): origin_family (10) x cost band on cost_r
(C1 <0.10, C2 0.10-0.30, C3 0.30-1.00, C4 >=1.00) x route_session (4) = 160 cells.

Metrics:
  M1 empirical: per-cell n, mean/median/sd of opportunity_net_proxy_r, one-sided t (H1: mean>0).
  M2 calibrated-belief: win := gross_r > 0 with gross_r = opportunity_net_proxy_r + cost_r;
     p_hat, Wbar (mean gross | win), |Lbar| (|mean gross | loss|), cbar = mean cost_r;
     p_star = (|Lbar|+cbar)/(Wbar+|Lbar|); margin = p_hat - p_star.
     NOTE (declared): margin>0 <=> mean net>0 by identity — M2 is a re-expression, not an
     independent test.
  BH at alpha=0.10 over Jan cells with n>=30 — TRIAGE MARKER ONLY, admits nothing.
  Selection: n_jan>=30 AND mean_net_jan>0 AND BH-marked.
  Transfer: Feb same-cell mean net; sign agreement; Spearman over all n>=30-both cells;
     headline = Feb aggregate of Jan-selected cells (equal-weight, n-weight, total sum),
     with and without asterisked cells.
  Asterisk: positivity depends on placeholder-spread symbols {BTCUSD, UKOIL_cash,
     USOIL_cash} — ex-placeholder Jan mean <= 0 or ex-placeholder n < 30.
"""
import gzip
import hashlib
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timezone

from scipy import stats as st

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
OUTDIR = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic")
POOLS = {
    "january": os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"),
    "february": os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"),
}

FAMILIES = [
    "current_fvg_fill", "liquidity_sweep_reclaim", "displacement_continuation",
    "current_breaker_re_entry", "cross_asset_lead_lag", "structural_distance_extreme",
    "current_ob_retest", "session_open_range_break", "volatility_compression_expansion",
    "regime_transition_break",
]
SESSIONS = ["ny", "london", "tokyo", "off_configured_session"]
COST_BANDS = [("C1", 0.0, 0.10), ("C2", 0.10, 0.30), ("C3", 0.30, 1.00), ("C4", 1.00, float("inf"))]
PLACEHOLDER_SYMBOLS = {"BTCUSD", "UKOIL_cash", "USOIL_cash"}
N_FLOOR = 30
BH_ALPHA = 0.10

# Cross-check anchors from Phase 1 (calibration/CALIBRATION.md + pool receipts), each with
# the tolerance implied by the precision it was quoted at (6dp -> 1e-6; Jan positive share
# was quoted as 27.862 % i.e. 5dp -> 5e-6).
ANCHORS = {
    "january": {"n": 27658, "net_mean": (-0.880657, 1e-6), "gross_mean": (-0.217496, 1e-6),
                "cost_mean": (0.663161, 1e-6), "positive_share": (0.27862, 5e-6)},
    "february": {"n": 24239, "net_mean": (-0.640021, 1e-6), "gross_mean": (-0.150551, 1e-6),
                 "cost_mean": None, "positive_share": (0.309336, 1e-6)},
}

KEEP = ("origin_family", "route_session", "symbol", "opportunity_net_proxy_r", "cost_r",
        "opportunity_gross_r", "candidate_probability")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    rows = []
    with gzip.open(path, "rt") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows.append({k: r.get(k) for k in KEEP})
    return rows


def cost_band(c):
    for name, lo, hi in COST_BANDS:
        if lo <= c < hi:
            return name
    raise ValueError(f"cost_r out of range: {c}")  # negative cost would be a schema break


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def sample_sd(xs):
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def cell_stats(rows):
    """rows: list of (net, cost, gross, symbol, p_stamped). Returns full M1+M2 stat dict."""
    n = len(rows)
    if n == 0:
        return {"n": 0}
    net = [r[0] for r in rows]
    cost = [r[1] for r in rows]
    gross = [r[2] for r in rows]
    m = mean(net)
    sd = sample_sd(net)
    t = p_one_sided = None
    if sd is not None and sd > 0:
        t = m / (sd / math.sqrt(n))
        p_one_sided = float(st.t.sf(t, n - 1))
    wins = [g for g in gross if g > 0]
    losses = [g for g in gross if g <= 0]
    p_hat = len(wins) / n
    wbar = mean(wins)
    lbar_abs = abs(mean(losses)) if losses else 0.0
    cbar = mean(cost)
    denom = (wbar if wbar is not None else 0.0) + lbar_abs
    p_star = (lbar_abs + cbar) / denom if denom > 0 else None
    margin = (p_hat - p_star) if p_star is not None else None
    ph_rows = [r for r in rows if r[3] in PLACEHOLDER_SYMBOLS]
    ex = [r[0] for r in rows if r[3] not in PLACEHOLDER_SYMBOLS]
    return {
        "n": n,
        "mean_net_r": m,
        "median_net_r": median(net),
        "sd_net_r": sd,
        "t_one_sided": t,
        "p_one_sided": p_one_sided,
        "sum_net_r": sum(net),
        "p_hat_win_gross": p_hat,
        "mean_win_gross_r": wbar,
        "mean_loss_gross_abs_r": lbar_abs,
        "mean_cost_r": cbar,
        "p_star_required": p_star,
        "margin_p_hat_minus_p_star": margin,
        "stamped_mean_candidate_probability": mean([r[4] for r in rows if r[4] is not None]),
        "placeholder_row_share": len(ph_rows) / n,
        "ex_placeholder_n": len(ex),
        "ex_placeholder_mean_net_r": mean(ex),
    }


def bh_mark(cells, alpha):
    """cells: list of (cell_id, p). Returns (marked_set, threshold_p, m)."""
    valid = [(cid, p) for cid, p in cells if p is not None]
    m = len(valid)
    if m == 0:
        return set(), None, 0
    ordered = sorted(valid, key=lambda t: t[1])
    thr = None
    for k, (_, p) in enumerate(ordered, start=1):
        if p <= k / m * alpha:
            thr = p
    if thr is None:
        return set(), None, m
    return {cid for cid, p in valid if p <= thr}, thr, m


def main():
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {}
    data = {}
    for w, path in POOLS.items():
        rows = load(path)
        inputs[w] = {"path": os.path.relpath(path, ROOT), "sha256": sha256_file(path), "n_rows": len(rows)}
        data[w] = rows

    # ---- Declaration block (axis fields only; emitted before outcome aggregation) ----
    declaration = {
        "written_before_outcome_aggregation": True,
        "partition": {
            "axes": ["origin_family", "cost_band(cost_r)", "route_session"],
            "origin_family_values": FAMILIES,
            "cost_bands": [{"name": n, "lo_inclusive": lo, "hi_exclusive": (None if hi == float("inf") else hi)}
                           for n, lo, hi in COST_BANDS],
            "route_session_values": SESSIONS,
            "declared_cell_count": len(FAMILIES) * len(COST_BANDS) * len(SESSIONS),
            "fitting": "none — fixed absolute thresholds, identical in both windows",
        },
        "metrics": {
            "M1_empirical": "per-cell n, mean/median/sd of opportunity_net_proxy_r, one-sided t (H1: mean>0), Student t p-value (n-1 df)",
            "M2_calibrated_belief": "win := gross_r>0, gross_r = opportunity_net_proxy_r + cost_r; p_star=(|Lbar|+cbar)/(Wbar+|Lbar|); margin=p_hat-p_star; NOTE margin>0 <=> mean net>0 by identity (re-expression, not independent test)",
        },
        "multiplicity": {"procedure": "Benjamini-Hochberg", "alpha": BH_ALPHA,
                         "population": f"January cells with n>={N_FLOOR}",
                         "status": "TRIAGE MARKER ONLY — admits nothing; ratified admission rule out of scope"},
        "selection_rule": f"n_jan>={N_FLOOR} AND mean_net_jan>0 AND BH-marked",
        "n_floor": N_FLOOR,
        "transfer_rule": {
            "february_status": "used-once VAL — attribution-only, selects nothing",
            "reports": [
                "sign-agreement of Jan-selected cells (primary: Feb n>=30; secondary: all)",
                "Spearman(Jan cell mean, Feb cell mean) over all cells n>=30 in BOTH windows",
                "headline: Feb aggregate of Jan-selected cells — equal-weight, n-weight pooled, total sum; with and without asterisked cells",
            ],
        },
        "asterisk_rule": {
            "placeholder_symbols": sorted(PLACEHOLDER_SYMBOLS),
            "rule": "Jan-selected cell is ASTERISKED if ex-placeholder Jan mean net <= 0 or ex-placeholder n < 30",
        },
        "evidence_class": "DEVELOPMENT-FITTED lane evidence, billed:false, never admission-grade",
    }

    # ---- Cross-checks ----
    cross = {}
    for w, rows in data.items():
        net = [r["opportunity_net_proxy_r"] for r in rows]
        cost = [r["cost_r"] for r in rows]
        gross = [n_ + c_ for n_, c_ in zip(net, cost)]
        cc = {
            "n": len(rows),
            "net_mean": mean(net),
            "gross_mean": mean(gross),
            "cost_mean": mean(cost),
            "positive_share": sum(1 for x in net if x > 0) / len(net),
        }
        a = ANCHORS[w]

        def near(key):
            if a[key] is None:
                return True
            val, tol = a[key]
            return abs(cc[key] - val) <= tol

        ok = (cc["n"] == a["n"] and near("net_mean") and near("gross_mean")
              and near("cost_mean") and near("positive_share"))
        cc["anchor_match"] = bool(ok)
        cross[w] = cc
        if not ok:
            raise SystemExit(f"CROSS-CHECK FAILED for {w}: {cc} vs {a}")
    # Feb gross derivation vs explicit field
    feb = data["february"]
    maxdiff = max(abs((r["opportunity_net_proxy_r"] + r["cost_r"]) - r["opportunity_gross_r"])
                  for r in feb if r.get("opportunity_gross_r") is not None)
    cross["february"]["gross_derivation_max_abs_diff_vs_explicit"] = maxdiff
    if maxdiff > 1e-8:
        raise SystemExit(f"Feb gross derivation mismatch: {maxdiff}")

    # ---- Per-cell aggregation ----
    def bucket(rows):
        cells = defaultdict(list)
        for r in rows:
            key = (r["origin_family"], cost_band(r["cost_r"]), r["route_session"])
            gross = r["opportunity_net_proxy_r"] + r["cost_r"]
            cells[key].append((r["opportunity_net_proxy_r"], r["cost_r"], gross,
                               r["symbol"], r.get("candidate_probability")))
        return cells

    jan_cells = bucket(data["january"])
    feb_cells = bucket(data["february"])

    all_keys = [(f, b[0], s) for f in FAMILIES for b in COST_BANDS for s in SESSIONS]
    table = []
    for key in all_keys:
        fam, band, sess = key
        cid = f"{fam}|{band}|{sess}"
        js = cell_stats(jan_cells.get(key, []))
        fs = cell_stats(feb_cells.get(key, []))
        table.append({"cell_id": cid, "origin_family": fam, "cost_band": band,
                      "route_session": sess, "january": js, "february": fs})

    # ---- BH over Jan cells n>=30 ----
    eligible = [(c["cell_id"], c["january"].get("p_one_sided")) for c in table
                if c["january"]["n"] >= N_FLOOR]
    marked, bh_thr, bh_m = bh_mark(eligible, BH_ALPHA)
    for c in table:
        c["bh_eligible"] = c["january"]["n"] >= N_FLOOR
        c["bh_marked"] = c["cell_id"] in marked

    # ---- Selection + asterisk ----
    for c in table:
        j = c["january"]
        sel = bool(c["bh_eligible"] and j.get("mean_net_r") is not None
                   and j["mean_net_r"] > 0 and c["bh_marked"])
        c["jan_selected"] = sel
        ast = None
        if j["n"] > 0:
            ast = bool(j["ex_placeholder_n"] < N_FLOOR
                       or (j["ex_placeholder_mean_net_r"] is not None
                           and j["ex_placeholder_mean_net_r"] <= 0)
                       or j["ex_placeholder_mean_net_r"] is None)
        c["asterisk_placeholder_dependent"] = ast
        c["asterisk"] = bool(sel and ast)

    selected = [c for c in table if c["jan_selected"]]

    # ---- Empirical summary (January) ----
    populated = [c for c in table if c["january"]["n"] > 0]
    n30 = [c for c in table if c["january"]["n"] >= N_FLOOR]
    pos30 = [c for c in n30 if c["january"]["mean_net_r"] > 0]
    margins = sorted(c["january"]["margin_p_hat_minus_p_star"] for c in n30
                     if c["january"]["margin_p_hat_minus_p_star"] is not None)

    def pct(sorted_xs, q):
        if not sorted_xs:
            return None
        idx = q * (len(sorted_xs) - 1)
        lo, hi = int(math.floor(idx)), int(math.ceil(idx))
        if lo == hi:
            return sorted_xs[lo]
        fr = idx - lo
        return sorted_xs[lo] * (1 - fr) + sorted_xs[hi] * fr

    empirical_summary = {
        "declared_cells": len(table),
        "populated_cells_jan": len(populated),
        "cells_n_ge_30_jan": len(n30),
        "cells_mean_net_positive_among_n_ge_30": len(pos30),
        "share_cells_mean_net_positive_among_n_ge_30": len(pos30) / len(n30) if n30 else None,
        "positive_cell_ids_n_ge_30": [c["cell_id"] for c in pos30],
        "margin_distribution_n_ge_30": {
            "n_cells": len(margins), "min": margins[0] if margins else None,
            "p10": pct(margins, 0.10), "p25": pct(margins, 0.25), "p50": pct(margins, 0.50),
            "p75": pct(margins, 0.75), "p90": pct(margins, 0.90),
            "max": margins[-1] if margins else None,
            "share_margin_positive": (sum(1 for x in margins if x > 0) / len(margins)) if margins else None,
        },
    }

    # ---- Transfer ----
    both30 = [c for c in table if c["january"]["n"] >= N_FLOOR and c["february"]["n"] >= N_FLOOR]
    rho = rho_p = None
    if len(both30) >= 3:
        r_ = st.spearmanr([c["january"]["mean_net_r"] for c in both30],
                          [c["february"]["mean_net_r"] for c in both30])
        rho, rho_p = float(r_.statistic), float(r_.pvalue)

    def feb_aggregate(cells):
        cells = [c for c in cells if c["february"]["n"] > 0]
        if not cells:
            return {"n_cells": 0, "n_rows_feb": 0, "equal_weight_mean_net_r": None,
                    "n_weight_mean_net_r": None, "total_sum_net_r": None}
        tot = sum(c["february"]["sum_net_r"] for c in cells)
        nrows = sum(c["february"]["n"] for c in cells)
        return {
            "n_cells": len(cells),
            "n_rows_feb": nrows,
            "equal_weight_mean_net_r": mean([c["february"]["mean_net_r"] for c in cells]),
            "n_weight_mean_net_r": tot / nrows,
            "total_sum_net_r": tot,
        }

    # Labeled sensitivity (NOT the declared headline): the declared selection can be empty,
    # in which case "empty book earns 0" is formally correct but uninformative about the
    # nominal positives. Relax ONLY the BH requirement (keep n>=30 and mean>0) and show how
    # that nominal-positive set transfers. Attribution-only; selects nothing.
    nominal_pos = [c for c in table if c["bh_eligible"] and c["january"]["mean_net_r"] is not None
                   and c["january"]["mean_net_r"] > 0]

    sel_feb30 = [c for c in selected if c["february"]["n"] >= N_FLOOR]
    transfer = {
        "february_status": "used-once VAL — attribution-only, labeled; selects nothing",
        "n_jan_selected": len(selected),
        "selected_cells": [c["cell_id"] for c in selected],
        "sign_agreement_primary_feb_n_ge_30": {
            "n_cells": len(sel_feb30),
            "n_feb_mean_positive": sum(1 for c in sel_feb30 if c["february"]["mean_net_r"] > 0),
            "rate": (sum(1 for c in sel_feb30 if c["february"]["mean_net_r"] > 0) / len(sel_feb30)) if sel_feb30 else None,
        },
        "sign_agreement_secondary_all_selected": {
            "n_cells_with_any_feb_rows": sum(1 for c in selected if c["february"]["n"] > 0),
            "n_feb_mean_positive": sum(1 for c in selected if c["february"]["n"] > 0 and c["february"]["mean_net_r"] > 0),
            "rate": (sum(1 for c in selected if c["february"]["n"] > 0 and c["february"]["mean_net_r"] > 0)
                     / max(1, sum(1 for c in selected if c["february"]["n"] > 0))) if selected else None,
        },
        "spearman_all_cells_n_ge_30_both": {"n_cells": len(both30), "rho": rho, "p": rho_p},
        "headline_feb_aggregate_of_jan_selected": feb_aggregate(selected),
        "headline_feb_aggregate_ex_asterisk": feb_aggregate([c for c in selected if not c["asterisk"]]),
        "sensitivity_nominal_positive_no_bh": {
            "label": ("NOT the declared headline — the declared selection requires BH marking; "
                      "this block relaxes ONLY that (keeps n>=30, mean>0) to show how the nominal "
                      "January-positive cells transfer. Attribution-only; selects nothing."),
            "cells": [c["cell_id"] for c in nominal_pos],
            "n_asterisked": sum(1 for c in nominal_pos if c["asterisk_placeholder_dependent"]),
            "feb_aggregate": feb_aggregate(nominal_pos),
            "feb_aggregate_ex_placeholder_dependent": feb_aggregate(
                [c for c in nominal_pos if not c["asterisk_placeholder_dependent"]]),
            "sign_agreement_all": {
                "n_cells_with_any_feb_rows": sum(1 for c in nominal_pos if c["february"]["n"] > 0),
                "n_feb_mean_positive": sum(1 for c in nominal_pos
                                           if c["february"]["n"] > 0 and c["february"]["mean_net_r"] > 0),
            },
            "sign_agreement_feb_n_ge_30": {
                "n_cells": sum(1 for c in nominal_pos if c["february"]["n"] >= N_FLOOR),
                "n_feb_mean_positive": sum(1 for c in nominal_pos
                                           if c["february"]["n"] >= N_FLOOR and c["february"]["mean_net_r"] > 0),
            },
        },
    }

    # Descriptive rollups of the declared cells (no new selection surface): cost-band
    # marginals and within-band Spearman, to locate WHERE the cross-month rank transfer lives.
    def band_rollup(w):
        agg = {}
        for c in table:
            s = c[w]
            if s["n"]:
                a = agg.setdefault(c["cost_band"], {"n": 0, "sum": 0.0})
                a["n"] += s["n"]
                a["sum"] += s["sum_net_r"]
        return {b: {"n": a["n"], "mean_net_r": a["sum"] / a["n"]} for b, a in sorted(agg.items())}

    within_band = {}
    for band, _, _ in COST_BANDS:
        sub = [c for c in both30 if c["cost_band"] == band]
        if len(sub) >= 3:
            r_ = st.spearmanr([c["january"]["mean_net_r"] for c in sub],
                              [c["february"]["mean_net_r"] for c in sub])
            within_band[band] = {"n_cells": len(sub), "rho": float(r_.statistic), "p": float(r_.pvalue)}
    descriptive_rollups = {
        "label": "descriptive only — marginals of the declared cells, no selection surface",
        "by_cost_band": {"january": band_rollup("january"), "february": band_rollup("february")},
        "spearman_within_cost_band_n_ge_30_both": within_band,
    }

    out = {
        "schema": "gtos.session_fa.belief_recal.v1",
        "evidence_class": "DEVELOPMENT-FITTED lane evidence, billed:false, never admission-grade; February attribution-only (used-once VAL); no March, no live-forward data",
        "generated_utc": generated,
        "script": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/belief_recal.py",
        "inputs": inputs,
        "declaration": declaration,
        "cross_checks": cross,
        "bh": {"alpha": BH_ALPHA, "m_cells_tested": bh_m, "n_marked": len(marked),
               "p_threshold": bh_thr, "marked_cell_ids": sorted(marked)},
        "empirical_summary_january": empirical_summary,
        "selection": {"rule": declaration["selection_rule"], "n_selected": len(selected),
                      "cells": [c["cell_id"] for c in selected],
                      "n_asterisked": sum(1 for c in selected if c["asterisk"])},
        "transfer": transfer,
        "descriptive_rollups": descriptive_rollups,
        "cells": table,
    }
    with open(os.path.join(OUTDIR, "BELIEF_RECAL.json"), "w") as f:
        json.dump(out, f, indent=1)

    # ---- Console summary for the receipt ----
    print("CROSS-CHECKS OK:", {w: cross[w]["anchor_match"] for w in cross},
          "feb gross maxdiff", cross["february"]["gross_derivation_max_abs_diff_vs_explicit"])
    print(f"cells: declared 160, populated Jan {len(populated)}, n>=30 Jan {len(n30)}")
    print(f"Jan cells mean>0 among n>=30: {len(pos30)}/{len(n30)}")
    print("margin distribution (n>=30 cells):", json.dumps(empirical_summary["margin_distribution_n_ge_30"], default=float))
    print(f"BH: m={bh_m}, marked={len(marked)}, thr={bh_thr}")
    print(f"SELECTED (n>=30, mean>0, BH): {len(selected)}")
    for c in selected:
        j, fb = c["january"], c["february"]
        print(f"  {c['cell_id']}: Jan n={j['n']} mean={j['mean_net_r']:+.4f} p={j['p_one_sided']:.2e} "
              f"margin={j['margin_p_hat_minus_p_star']:+.4f} p_hat={j['p_hat_win_gross']:.3f} p*={j['p_star_required']:.3f} "
              f"ph_share={j['placeholder_row_share']:.2f} AST={'YES' if c['asterisk'] else 'no'} | "
              f"Feb n={fb['n']} mean={fb.get('mean_net_r') if fb['n'] else None}")
    print("TRANSFER:", json.dumps({k: v for k, v in transfer.items() if k != 'selected_cells'}, default=float, indent=1))
    # Top-15 margin table for the .md
    top = sorted(n30, key=lambda c: c["january"]["margin_p_hat_minus_p_star"], reverse=True)[:15]
    print("\nTOP15 by Jan margin (n>=30):")
    for c in top:
        j, fb = c["january"], c["february"]
        print(f"  {c['cell_id']}: n={j['n']} mean={j['mean_net_r']:+.4f} margin={j['margin_p_hat_minus_p_star']:+.4f} "
              f"p_hat={j['p_hat_win_gross']:.3f} p*={j['p_star_required']:.3f} c̄={j['mean_cost_r']:.3f} "
              f"stamped_p={j['stamped_mean_candidate_probability']:.3f} ph={j['placeholder_row_share']:.2f} "
              f"ast_dep={'Y' if c['asterisk_placeholder_dependent'] else 'n'} bh={'Y' if c['bh_marked'] else 'n'} "
              f"| Feb n={fb['n']} mean={(f'{fb['mean_net_r']:+.4f}' if fb['n'] else 'NA')}")


if __name__ == "__main__":
    main()
