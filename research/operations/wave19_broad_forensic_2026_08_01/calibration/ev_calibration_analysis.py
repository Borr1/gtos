#!/usr/bin/env python3
"""EV-CALIBRATION forensic over the January (CJ) and February (CP) compact scoreable pools.

Session FA wave-19 broad-V4 forensic, EV-CALIBRATION analyst.
Mission: quantify whether the belief layer (probabilities / EVs / fill probs) is a
model output or template fiction, and whether beliefs are informative about realized
opportunity_net_proxy_r.

Realized-event definition (stated per mission):
  PRIMARY  : realized positive event  := opportunity_net_proxy_r > 0
  SENSITIVITY: gross-positive event   := gross_r > 0, where
       gross_r = opportunity_net_proxy_r + cost_r   (January: derived; February: the pool
       also carries opportunity_gross_r, which we verify against the derivation)

All numbers computed from the raw pool rows; nothing taken from prose docs.
Outputs: BELIEF_INVENTORY.json, CALIBRATION_TABLES.json, EV_SIGN_TABLE.json,
COST_BELIEF.json (CALIBRATION.md written by a sibling script / by hand from these).
"""
import gzip, json, math, os, sys
from collections import Counter, defaultdict

OUT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/research/operations/wave19_broad_forensic_2026_08_01/calibration"

POOLS = {
    "january": "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
    "february": "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz",
}

BELIEF_FIELDS = [
    "candidate_probability", "candidate_ev_r", "expectancy_r", "expected_net_r",
    "candidate_confidence", "fill_probability", "entry_quality_fill_probability",
    "execution_fill_probability", "limit_fillability_probability",
]

KEEP = set(BELIEF_FIELDS) | {
    "origin_family", "direction", "symbol", "opportunity_net_proxy_r", "cost_r",
    "expected_cost_r", "spread_r", "commission_r", "expected_slippage_r", "swap_cost_r",
    "old_proxy_vs_broker_calibrated_delta_r", "confidence_default_applied",
    "broker_pretrade_cost_executable", "opportunity_gross_r", "terminal_outcome",
    "policy_target_r", "decision_time_utc",
}


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


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sxx = syy = 0.0
    for x, y in zip(xs, ys):
        dx, dy = x - mx, y - my
        sxy += dx * dy
        sxx += dx * dx
        syy += dy * dy
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def rankdata(xs):
    # average ranks for ties
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs, ys):
    return pearson(rankdata(xs), rankdata(ys))


def pctile(sorted_xs, q):
    if not sorted_xs:
        return None
    idx = q * (len(sorted_xs) - 1)
    lo = int(math.floor(idx)); hi = int(math.ceil(idx))
    if lo == hi:
        return sorted_xs[lo]
    frac = idx - lo
    return sorted_xs[lo] * (1 - frac) + sorted_xs[hi] * frac


def value_key(v):
    if v is None:
        return "null"
    if isinstance(v, float):
        return repr(v)
    return repr(v)


def belief_inventory(rows, window):
    out = {"window": window, "n_rows": len(rows), "fields": {}}
    fam_of = [r["origin_family"] for r in rows]
    default_applied = sum(1 for r in rows if r.get("confidence_default_applied"))
    out["confidence_default_applied_true"] = default_applied
    out["confidence_default_applied_share"] = default_applied / len(rows)
    for f in BELIEF_FIELDS:
        vals = [r.get(f) for r in rows]
        c = Counter(value_key(v) for v in vals)
        nnull = c.get("null", 0)
        distinct = len(c)
        top20 = c.most_common(20)
        top20_share = sum(n for _, n in top20) / len(rows)
        # per-family distincts + constants
        fam_vals = defaultdict(Counter)
        for fam, v in zip(fam_of, vals):
            fam_vals[fam][value_key(v)] += 1
        per_family = {}
        for fam, fc in sorted(fam_vals.items()):
            n_fam = sum(fc.values())
            entry = {
                "n": n_fam,
                "distinct": len(fc),
                "top5": fc.most_common(5),
                "top1_share": fc.most_common(1)[0][1] / n_fam,
            }
            if len(fc) == 1:
                entry["constant"] = fc.most_common(1)[0][0]
            per_family[fam] = entry
        numeric = [v for v in vals if isinstance(v, (int, float))]
        ns = sorted(numeric)
        out["fields"][f] = {
            "distinct_values": distinct,
            "n_null": nnull,
            "top20": top20,
            "top20_cumulative_share": top20_share,
            "min": ns[0] if ns else None,
            "p50": pctile(ns, 0.5),
            "max": ns[-1] if ns else None,
            "mean": mean(ns),
            "classification": (
                "CONSTANT" if distinct == 1 else
                "TEMPLATE_CONSTANTS" if distinct <= 25 or top20_share > 0.99 else
                "COARSE" if distinct <= 500 else
                "CONTINUOUS"
            ),
            "per_origin_family": per_family,
        }
    return out


def reliability_deciles(pairs):
    """pairs = list of (p, y). Equal-count deciles by predicted p (ties broken by sort order)."""
    pairs = sorted(pairs, key=lambda t: t[0])
    n = len(pairs)
    table = []
    for d in range(10):
        lo = d * n // 10
        hi = (d + 1) * n // 10
        chunk = pairs[lo:hi]
        if not chunk:
            continue
        mp = mean([p for p, _ in chunk])
        ry = mean([y for _, y in chunk])
        table.append({
            "decile": d + 1, "n": len(chunk),
            "pred_min": chunk[0][0], "pred_max": chunk[-1][0],
            "mean_predicted": mp, "realized_rate": ry, "gap_pred_minus_realized": mp - ry,
        })
    return table


def brier(pairs):
    return mean([(p - y) ** 2 for p, y in pairs])


def analyze_window(rows, window):
    res = {"window": window, "n_rows": len(rows)}
    net = [r["opportunity_net_proxy_r"] for r in rows]
    cost = [r["cost_r"] for r in rows]
    gross_derived = [n + c for n, c in zip(net, cost)]
    # verify against explicit opportunity_gross_r where present (February)
    explicit = [(g, r["opportunity_gross_r"]) for g, r in zip(gross_derived, rows)
                if r.get("opportunity_gross_r") is not None]
    if explicit:
        maxdiff = max(abs(a - b) for a, b in explicit)
        res["gross_derivation_check"] = {
            "n_with_explicit_gross": len(explicit),
            "max_abs_diff_derived_vs_explicit": maxdiff,
        }
    # ---- cross-checks
    res["cross_check"] = {
        "n_rows": len(rows),
        "net_sum": sum(net),
        "net_mean": mean(net),
        "gross_mean": mean(gross_derived),
        "cost_mean": mean(cost),
        "spread_mean": mean([r["spread_r"] for r in rows]),
        "commission_mean": mean([r["commission_r"] for r in rows]),
        "slippage_mean": mean([r["expected_slippage_r"] for r in rows]),
        "swap_mean": mean([r["swap_cost_r"] for r in rows]),
        "positive_net_rows": sum(1 for x in net if x > 0),
        "positive_net_share": sum(1 for x in net if x > 0) / len(rows),
        "broker_pretrade_cost_executable_true": sum(1 for r in rows if r["broker_pretrade_cost_executable"] is True),
        "broker_pretrade_cost_executable_false": sum(1 for r in rows if r["broker_pretrade_cost_executable"] is False),
    }
    # ---- probability calibration (primary event: net > 0)
    y_net = [1.0 if x > 0 else 0.0 for x in net]
    y_gross = [1.0 if x > 0 else 0.0 for x in gross_derived]
    p = [r["candidate_probability"] for r in rows]
    pairs_net = list(zip(p, y_net))
    pairs_gross = list(zip(p, y_gross))
    base_net = mean(y_net)
    base_gross = mean(y_gross)
    res["probability_calibration"] = {
        "event_definition_primary": "opportunity_net_proxy_r > 0",
        "event_definition_sensitivity": "gross_r = opportunity_net_proxy_r + cost_r > 0",
        "mean_predicted_probability": mean(p),
        "realized_rate_net": base_net,
        "realized_rate_gross": base_gross,
        "brier_model_net": brier(pairs_net),
        "brier_baserate_net": base_net * (1 - base_net),
        "brier_model_gross": brier(pairs_gross),
        "brier_baserate_gross": base_gross * (1 - base_gross),
        "reliability_deciles_net": reliability_deciles(pairs_net),
        "reliability_deciles_gross": reliability_deciles(pairs_gross),
    }
    res["probability_calibration"]["brier_skill_net"] = (
        1 - res["probability_calibration"]["brier_model_net"] / res["probability_calibration"]["brier_baserate_net"])
    res["probability_calibration"]["brier_skill_gross"] = (
        1 - res["probability_calibration"]["brier_model_gross"] / res["probability_calibration"]["brier_baserate_gross"])
    # per-family predicted vs realized
    fam_tab = {}
    by_fam = defaultdict(list)
    for r, yn, yg in zip(rows, y_net, y_gross):
        by_fam[r["origin_family"]].append((r["candidate_probability"], yn, yg))
    for fam, trips in sorted(by_fam.items()):
        fam_tab[fam] = {
            "n": len(trips),
            "mean_predicted_p": mean([t[0] for t in trips]),
            "realized_rate_net": mean([t[1] for t in trips]),
            "realized_rate_gross": mean([t[2] for t in trips]),
            "gap_net": mean([t[0] for t in trips]) - mean([t[1] for t in trips]),
        }
    res["probability_calibration"]["per_origin_family"] = fam_tab

    # ---- EV calibration
    exp_net = [r["expected_net_r"] for r in rows]
    ev = [r["candidate_ev_r"] for r in rows]
    expct = [r["expectancy_r"] for r in rows]
    res["ev_calibration"] = {
        "identity_checks": {
            "candidate_ev_r_equals_expectancy_r_exact": sum(1 for a, b in zip(ev, expct) if a == b),
            "expected_net_r_equals_ev_minus_expected_cost_within_1e-6": sum(
                1 for r in rows
                if abs(r["expected_net_r"] - (r["candidate_ev_r"] - r["expected_cost_r"])) < 1e-6),
        },
        "expected_net_vs_realized_net": {
            "mean_expected_net_r": mean(exp_net),
            "mean_realized_net_r": mean(net),
            "mean_bias_expected_minus_realized": mean(exp_net) - mean(net),
            "pearson": pearson(exp_net, net),
            "spearman": spearman(exp_net, net),
        },
        "candidate_ev_vs_realized_gross": {
            "note": "candidate_ev_r is pre-cost (expected_net_r = candidate_ev_r - expected_cost_r), so gross is the fair comparison",
            "mean_candidate_ev_r": mean(ev),
            "mean_realized_gross_r": mean(gross_derived),
            "mean_bias_ev_minus_gross": mean(ev) - mean(gross_derived),
            "pearson": pearson(ev, gross_derived),
            "spearman": spearman(ev, gross_derived),
        },
    }
    # family x direction sign table
    cells = defaultdict(list)
    for r, nv, gv in zip(rows, net, gross_derived):
        cells[(r["origin_family"], r["direction"])].append((r["expected_net_r"], nv, r["candidate_ev_r"], gv))
    sign_table = []
    for (fam, d), vs in sorted(cells.items()):
        me = mean([v[0] for v in vs]); mr = mean([v[1] for v in vs])
        mev = mean([v[2] for v in vs]); mg = mean([v[3] for v in vs])
        sign_table.append({
            "origin_family": fam, "direction": d, "n": len(vs),
            "mean_expected_net_r": me, "mean_realized_net_r": mr,
            "mean_candidate_ev_r": mev, "mean_realized_gross_r": mg,
            "fiction_cell_net": bool(me > 0 and mr < 0),
            "fiction_cell_gross": bool(mev > 0 and mg < 0),
        })
    res["ev_sign_table"] = sign_table
    res["fiction_cells_net"] = sum(1 for c in sign_table if c["fiction_cell_net"])
    res["fiction_cells_gross"] = sum(1 for c in sign_table if c["fiction_cell_gross"])
    res["fiction_cells_net_row_share"] = sum(c["n"] for c in sign_table if c["fiction_cell_net"]) / len(rows)

    # ---- cost belief
    ec = [r["expected_cost_r"] for r in rows]
    diff_ec = [abs(a - b) for a, b in zip(ec, cost)]
    deltas = sorted(r["old_proxy_vs_broker_calibrated_delta_r"] for r in rows
                    if r["old_proxy_vs_broker_calibrated_delta_r"] is not None)
    spread_by_sym = defaultdict(list)
    for r in rows:
        spread_by_sym[r["symbol"]].append(r["spread_r"])
    res["cost_belief"] = {
        "expected_cost_equals_cost_exact": sum(1 for d in diff_ec if d == 0.0),
        "expected_cost_within_1e-9": sum(1 for d in diff_ec if d < 1e-9),
        "max_abs_diff_expected_vs_cost": max(diff_ec),
        "old_proxy_vs_broker_delta": {
            "n": len(deltas), "n_null": len(rows) - len(deltas),
            "mean": mean(deltas), "min": deltas[0] if deltas else None,
            "p05": pctile(deltas, 0.05), "p25": pctile(deltas, 0.25),
            "p50": pctile(deltas, 0.50), "p75": pctile(deltas, 0.75),
            "p95": pctile(deltas, 0.95), "max": deltas[-1] if deltas else None,
            "share_negative": sum(1 for d in deltas if d < 0) / len(deltas) if deltas else None,
            "share_zero": sum(1 for d in deltas if d == 0) / len(deltas) if deltas else None,
        },
        "spread_r_by_symbol": {
            sym: {"n": len(v), "mean": mean(v), "min": min(v), "max": max(v),
                  "distinct": len(set(v))}
            for sym, v in sorted(spread_by_sym.items())
        },
    }

    # ---- decision-relevant summary: deciles of expected_net_r vs realized net
    pairs = sorted(zip(exp_net, net), key=lambda t: t[0])
    n = len(pairs)
    dec = []
    for d in range(10):
        lo, hi = d * n // 10, (d + 1) * n // 10
        chunk = pairs[lo:hi]
        dec.append({
            "decile_by_expected_net_r": d + 1, "n": len(chunk),
            "expected_net_min": chunk[0][0], "expected_net_max": chunk[-1][0],
            "mean_expected_net_r": mean([c[0] for c in chunk]),
            "mean_realized_net_r": mean([c[1] for c in chunk]),
        })
    res["decision_relevance"] = {
        "deciles": dec,
        "believed_best_top_decile_realized_mean_net": dec[-1]["mean_realized_net_r"],
        "believed_worst_bottom_decile_realized_mean_net": dec[0]["mean_realized_net_r"],
        "best_minus_worst_realized": dec[-1]["mean_realized_net_r"] - dec[0]["mean_realized_net_r"],
        "anti_informative": bool(dec[-1]["mean_realized_net_r"] < dec[0]["mean_realized_net_r"]),
    }
    # same restricted to broker-executable rows
    exe = [(e, nv) for r, e, nv in zip(rows, exp_net, net) if r["broker_pretrade_cost_executable"] is True]
    if exe:
        exe.sort(key=lambda t: t[0])
        ne = len(exe)
        top = exe[9 * ne // 10:]
        bot = exe[: ne // 10]
        res["decision_relevance"]["executable_only"] = {
            "n": ne,
            "top_decile_realized_mean_net": mean([t[1] for t in top]),
            "bottom_decile_realized_mean_net": mean([t[1] for t in bot]),
        }
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    inventories = {}
    analyses = {}
    for window, path in POOLS.items():
        rows = load(path)
        inventories[window] = belief_inventory(rows, window)
        analyses[window] = analyze_window(rows, window)
        del rows

    with open(os.path.join(OUT, "BELIEF_INVENTORY.json"), "w") as f:
        json.dump(inventories, f, indent=1)
    with open(os.path.join(OUT, "CALIBRATION_TABLES.json"), "w") as f:
        json.dump({w: {
            "cross_check": a["cross_check"],
            "gross_derivation_check": a.get("gross_derivation_check"),
            "probability_calibration": a["probability_calibration"],
            "ev_calibration": a["ev_calibration"],
            "decision_relevance": a["decision_relevance"],
        } for w, a in analyses.items()}, f, indent=1)
    with open(os.path.join(OUT, "EV_SIGN_TABLE.json"), "w") as f:
        json.dump({w: {
            "sign_table": a["ev_sign_table"],
            "fiction_cells_net": a["fiction_cells_net"],
            "fiction_cells_gross": a["fiction_cells_gross"],
            "fiction_cells_net_row_share": a["fiction_cells_net_row_share"],
        } for w, a in analyses.items()}, f, indent=1)
    with open(os.path.join(OUT, "COST_BELIEF.json"), "w") as f:
        json.dump({w: a["cost_belief"] for w, a in analyses.items()}, f, indent=1)
    print("done")


if __name__ == "__main__":
    main()
