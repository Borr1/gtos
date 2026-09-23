"""Main analysis pipeline for agent eta.

Outputs intermediate JSONs for each pattern test + a summary stats JSON.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

from load_data import (
    load_xauusd, load_eurusd, load_nas100, load_m15, load_h1, load_h4, load_d1,
    parse_time, find_candle_idx_at_or_before, in_any_kz, KZ_BY_SYMBOL,
)
from forward_replay import replay_hypothetical
from features import build_features

OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\b_deep_audit_2026-04-19\phase1\_eta_scratch")


def _sig_test_prop(wins, n, null_p=0.5):
    """One-sample binomial test vs null_p. Returns (p-value two-sided)."""
    if n == 0:
        return 1.0
    # Normal approximation for n>=30; exact for smaller
    if n < 30:
        # Exact binomial cdf
        from math import comb
        k = wins
        p_at_least = sum(comb(n, i) * (null_p ** i) * ((1 - null_p) ** (n - i)) for i in range(k, n + 1))
        p_at_most = sum(comb(n, i) * (null_p ** i) * ((1 - null_p) ** (n - i)) for i in range(0, k + 1))
        return min(1.0, 2 * min(p_at_least, p_at_most))
    p_hat = wins / n
    se = math.sqrt(null_p * (1 - null_p) / n)
    z = (p_hat - null_p) / se
    # Two-sided p via erfc
    from math import erfc
    return erfc(abs(z) / math.sqrt(2))


def annotate_records(records, symbol):
    """Attach _parsed_time to each record."""
    for r in records:
        r["_parsed_time"] = parse_time(r.get("candle_time"))
        if not r.get("symbol"):
            r["symbol"] = symbol


def compute_outcomes(records, m15, horizon_min=4 * 60, sl_atr=1.0, tp_atr=1.5):
    """For each record, compute forward outcome hypothetical. Attach '_outcome' field."""
    for r in records:
        t = r.get("_parsed_time")
        if t is None:
            r["_outcome"] = None
            continue
        idx = find_candle_idx_at_or_before(m15, t)
        if idx is None:
            r["_outcome"] = None
            continue
        # Only replay if candle idx matches exactly; otherwise t is not an M15 close
        # Accept if candle time is within 15 min of t (allows for record-time rounding)
        if abs((m15[idx]["time"] - t).total_seconds()) > 60:
            r["_outcome"] = None
            continue
        r["_outcome"] = replay_hypothetical(m15, idx, horizon_minutes=horizon_min,
                                            sl_atr_mult=sl_atr, tp_atr_mult=tp_atr)


def extract_features(records, m15, h1, h4, d1):
    for r in records:
        r["_features"] = build_features(r, m15, h1, h4, d1)


# -------- BASELINE: CANDIDATE WR over same horizon/ATR-R framing (sanity) --------
def baseline_candidate_stats(records):
    cand = [r for r in records if r.get("decision") == "CANDIDATE"]
    total = len(cand)
    outcomes = [r["_outcome"] for r in cand if r.get("_outcome")]
    wins_long = sum(1 for o in outcomes if o and o["long_outcome"] == "WIN")
    wins_short = sum(1 for o in outcomes if o and o["short_outcome"] == "WIN")
    # Use CANDIDATE direction if present
    directional_wins = 0
    directional_n = 0
    for r in cand:
        o = r.get("_outcome")
        if not o:
            continue
        d = r.get("direction") or "LONG"
        oc = o["long_outcome"] if d == "LONG" else o["short_outcome"]
        directional_n += 1
        if oc == "WIN":
            directional_wins += 1
    return {
        "n_candidate": total,
        "n_with_outcome": len(outcomes),
        "directional_wins": directional_wins,
        "directional_n": directional_n,
        "directional_wr": directional_wins / directional_n if directional_n else None,
    }


# -------- WINNING NO_TRADE CLUSTER --------
def winning_notrade_analysis(records):
    """Classify every NO_TRADE / REJECTED_L2 / BLOCKED_LIMIT by forward 1.5R winner.
    Extract features for winners."""
    ignored_decisions = {"CANDIDATE", "PARSE_ERROR"}
    pool = [r for r in records if r.get("decision") not in ignored_decisions]
    resolved = 0
    winners = {"LONG": 0, "SHORT": 0, "NONE": 0, "CONFLICT": 0}
    n_feats_ok = 0
    winner_feature_rows = []
    loser_feature_rows = []  # for contrast (NONE)
    for r in pool:
        o = r.get("_outcome")
        if not o:
            continue
        resolved += 1
        w = o["winner"]
        winners[w] += 1
        feats = r.get("_features")
        if feats is None:
            continue
        n_feats_ok += 1
        if w in ("LONG", "SHORT"):
            winner_feature_rows.append({
                "candle_time": r.get("candle_time"),
                "symbol": r.get("symbol"),
                "winner": w,
                "bars_to_resolve": o["bars_to_resolve_winner"],
                "decision": r.get("decision"),
                "no_trade_reason": r.get("no_trade_reason") or r.get("l2_reason") or r.get("block_reason"),
                **feats,
            })
        else:
            loser_feature_rows.append({
                "candle_time": r.get("candle_time"),
                "symbol": r.get("symbol"),
                "winner": w,
                "decision": r.get("decision"),
                **feats,
            })
    return {
        "n_total_nontrade": len(pool),
        "n_resolved_outcomes": resolved,
        "winner_breakdown": winners,
        "n_with_features": n_feats_ok,
        "winner_rows": winner_feature_rows,
        "loser_rows": loser_feature_rows,
    }


# -------- EDGE 1: FVG-only (no OB required, H1 bias aligned) --------
def test_edge_fvg_only(records):
    """Signal: fresh M15 FVG AND H1 trend aligned with FVG direction.
    Direction derived from FVG type (bull FVG → LONG, bear FVG → SHORT).
    Winner: did the corresponding-direction hypothetical win?"""
    results = []
    for r in records:
        f = r.get("_features")
        if f is None:
            continue
        fvg = f.get("fvg_m15")
        if fvg not in ("bull", "bear"):
            continue
        h1_dir = f.get("h1_dir")
        if fvg == "bull" and h1_dir != "bullish":
            continue
        if fvg == "bear" and h1_dir != "bearish":
            continue
        o = r.get("_outcome")
        if not o:
            continue
        direction = "LONG" if fvg == "bull" else "SHORT"
        oc = o["long_outcome"] if direction == "LONG" else o["short_outcome"]
        if oc in ("WIN", "LOSS"):
            results.append({
                "candle_time": r.get("candle_time"),
                "symbol": r.get("symbol"),
                "direction": direction,
                "outcome": oc,
                "kz": f.get("kz"),
                "decision": r.get("decision"),
                "alignment": f.get("alignment_trend"),
                "d1_dir": f.get("d1_dir"),
                "h4_dir": f.get("h4_dir"),
                "h1_dir": f.get("h1_dir"),
            })
    return results


# -------- EDGE 2: Liquidity sweep + displacement (no retest required) --------
def test_edge_sweep_displace(records):
    """Signal: M15 sweep of PDH OR PDL OR Asian H/L OR London H/L on last 5 candles,
    AND current candle displacement >= 0.75 ATR,
    AND H1 trend aligned with sweep-reversal direction.
    Direction: sweep of HIGHS → SHORT; sweep of LOWS → LONG."""
    results = []
    for r in records:
        f = r.get("_features")
        if f is None:
            continue
        if not f.get("displacement_high"):
            continue
        sweep_high = any(f.get(k) for k in ("sweep_pdh", "sweep_asian_hi", "sweep_london_hi"))
        sweep_low = any(f.get(k) for k in ("sweep_pdl", "sweep_asian_lo", "sweep_london_lo"))
        if sweep_high and sweep_low:
            continue  # Ambiguous
        if not (sweep_high or sweep_low):
            continue
        direction = "SHORT" if sweep_high else "LONG"
        # Align with H1 bias
        h1_dir = f.get("h1_dir")
        if direction == "SHORT" and h1_dir == "bullish":
            continue
        if direction == "LONG" and h1_dir == "bearish":
            continue
        o = r.get("_outcome")
        if not o:
            continue
        oc = o["long_outcome"] if direction == "LONG" else o["short_outcome"]
        if oc in ("WIN", "LOSS"):
            which_swept = []
            for k in ("sweep_pdh", "sweep_pdl", "sweep_asian_hi", "sweep_asian_lo", "sweep_london_hi", "sweep_london_lo"):
                if f.get(k):
                    which_swept.append(k)
            results.append({
                "candle_time": r.get("candle_time"),
                "symbol": r.get("symbol"),
                "direction": direction,
                "outcome": oc,
                "kz": f.get("kz"),
                "decision": r.get("decision"),
                "swept_levels": which_swept,
                "displacement_atr": f.get("displacement_atr"),
                "h1_dir": f.get("h1_dir"),
            })
    return results


# -------- EDGE 3: Session reversal at equilibrium/fib50 (mean-reversion) --------
def test_edge_fib50_mr(records):
    """Signal: current close is within ±0.25 ATR of H1 fib50 (equilibrium),
    AND D1 trend is bullish → expect LONG (retrace ending), OR bearish → SHORT.
    This is the "mean-reversion BACK to trend" variant (pullback at equilibrium)."""
    results = []
    for r in records:
        f = r.get("_features")
        if f is None:
            continue
        fib50_dist_atr = f.get("fib50_dist_atr")
        if fib50_dist_atr is None:
            continue
        if abs(fib50_dist_atr) > 0.25:
            continue
        d1_dir = f.get("d1_dir")
        if d1_dir not in ("bullish", "bearish"):
            continue
        direction = "LONG" if d1_dir == "bullish" else "SHORT"
        o = r.get("_outcome")
        if not o:
            continue
        oc = o["long_outcome"] if direction == "LONG" else o["short_outcome"]
        if oc in ("WIN", "LOSS"):
            results.append({
                "candle_time": r.get("candle_time"),
                "symbol": r.get("symbol"),
                "direction": direction,
                "outcome": oc,
                "kz": f.get("kz"),
                "decision": r.get("decision"),
                "d1_dir": d1_dir,
                "fib50_dist_atr": fib50_dist_atr,
            })
    return results


def summarize_edge(results, label):
    total = len(results)
    wins = sum(1 for r in results if r["outcome"] == "WIN")
    losses = total - wins
    wr = wins / total if total else None
    # Expectancy at +1.5R / -1.0R
    exp_r = (wins * 1.5 - losses * 1.0) / total if total else None
    p = _sig_test_prop(wins, total, null_p=0.4)  # null: random long/short at 1.5R:1R = 40% WR breakeven
    # Per instrument
    per_inst = defaultdict(lambda: {"n": 0, "w": 0})
    for r in results:
        per_inst[r["symbol"]]["n"] += 1
        if r["outcome"] == "WIN":
            per_inst[r["symbol"]]["w"] += 1
    per_inst_summary = {}
    for s, d in per_inst.items():
        wr_s = d["w"] / d["n"] if d["n"] else None
        p_s = _sig_test_prop(d["w"], d["n"], null_p=0.4) if d["n"] >= 10 else None
        per_inst_summary[s] = {
            "n": d["n"],
            "w": d["w"],
            "wr": wr_s,
            "exp_r": (d["w"] * 1.5 - (d["n"] - d["w"]) * 1.0) / d["n"] if d["n"] else None,
            "p": p_s,
        }
    return {
        "label": label,
        "n": total,
        "w": wins,
        "l": losses,
        "wr": wr,
        "exp_r": exp_r,
        "p_raw": p,
        "per_instrument": per_inst_summary,
    }


# -------- EXTENDED HOUR / OUT-OF-KZ EDGE --------
def test_ooh_highwr_bins(records):
    """For each record with a winning hypothetical (outside KZ), bin by hour_utc.
    Return per-hour WR counts — indicator of extended-hour edges."""
    pool = [r for r in records if r.get("decision") not in ("CANDIDATE", "PARSE_ERROR")]
    by_hour = defaultdict(lambda: {"n": 0, "long_win": 0, "short_win": 0, "non_kz": 0, "in_kz": 0})
    for r in pool:
        f = r.get("_features")
        o = r.get("_outcome")
        if f is None or o is None:
            continue
        h = f.get("hour_utc")
        by_hour[h]["n"] += 1
        if f.get("kz") == "out":
            by_hour[h]["non_kz"] += 1
        else:
            by_hour[h]["in_kz"] += 1
        if o["winner"] == "LONG":
            by_hour[h]["long_win"] += 1
        elif o["winner"] == "SHORT":
            by_hour[h]["short_win"] += 1
    return dict(sorted(by_hour.items()))


# -------- CLUSTERING WINNING NO_TRADE PATTERNS --------
def cluster_winning_notrades(winner_rows):
    """Partition winners by categorical features."""
    clusters = defaultdict(list)
    for row in winner_rows:
        # Signature: (alignment_trend, has_fvg, sweep_side, kz_class)
        has_fvg = (row.get("fvg_m15") in ("bull", "bear"))
        sweep_hi = any(row.get(k) for k in ("sweep_pdh", "sweep_asian_hi", "sweep_london_hi"))
        sweep_lo = any(row.get(k) for k in ("sweep_pdl", "sweep_asian_lo", "sweep_london_lo"))
        if sweep_hi and not sweep_lo:
            sweep_side = "high"
        elif sweep_lo and not sweep_hi:
            sweep_side = "low"
        elif sweep_hi and sweep_lo:
            sweep_side = "both"
        else:
            sweep_side = "none"
        kz_class = "kz" if row.get("kz") != "out" else "out"
        align = row.get("alignment_trend") or "mixed"
        disp = "high" if row.get("displacement_high") else "low"
        sig = f"align={align}|fvg={'Y' if has_fvg else 'N'}|sweep={sweep_side}|disp={disp}|{kz_class}"
        clusters[sig].append(row)
    # Sort by size
    result = []
    for sig, rows in sorted(clusters.items(), key=lambda x: -len(x[1])):
        per_sym = Counter(r.get("symbol") for r in rows)
        result.append({
            "signature": sig,
            "n": len(rows),
            "by_symbol": dict(per_sym),
        })
    return result


def fdr_bonferroni(p_values):
    """Return bonferroni-adjusted p-values for a list of p-values."""
    k = len(p_values)
    return [min(1.0, p * k) for p in p_values]


def main():
    print("Loading T7 records...", flush=True)
    xau = load_xauusd()
    eur = load_eurusd()
    nas = load_nas100()
    for r in xau:
        r["symbol"] = "XAUUSD"
    for r in eur:
        r["symbol"] = "EURUSD"
    for r in nas:
        r["symbol"] = "NAS100"
    annotate_records(xau, "XAUUSD")
    annotate_records(eur, "EURUSD")
    annotate_records(nas, "NAS100")
    print(f"  XAUUSD={len(xau)}  EURUSD={len(eur)}  NAS100={len(nas)}", flush=True)

    print("Loading candle CSVs...", flush=True)
    m15_xau = load_m15("XAUUSD"); h1_xau = load_h1("XAUUSD"); h4_xau = load_h4("XAUUSD"); d1_xau = load_d1("XAUUSD")
    m15_eur = load_m15("EURUSD"); h1_eur = load_h1("EURUSD"); h4_eur = load_h4("EURUSD"); d1_eur = load_d1("EURUSD")
    m15_nas = load_m15("NAS100"); h1_nas = load_h1("NAS100"); h4_nas = load_h4("NAS100"); d1_nas = load_d1("NAS100")
    print(f"  XAUUSD M15={len(m15_xau)} H1={len(h1_xau)} H4={len(h4_xau)} D1={len(d1_xau)}", flush=True)

    print("Computing outcomes + features (XAUUSD)...", flush=True)
    compute_outcomes(xau, m15_xau)
    extract_features(xau, m15_xau, h1_xau, h4_xau, d1_xau)

    print("Computing outcomes + features (EURUSD)...", flush=True)
    compute_outcomes(eur, m15_eur)
    extract_features(eur, m15_eur, h1_eur, h4_eur, d1_eur)

    print("Computing outcomes + features (NAS100)...", flush=True)
    compute_outcomes(nas, m15_nas)
    extract_features(nas, m15_nas, h1_nas, h4_nas, d1_nas)

    all_records = xau + eur + nas

    # ----- Baseline candidate sanity -----
    base_xau = baseline_candidate_stats(xau)
    base_eur = baseline_candidate_stats(eur)
    base_nas = baseline_candidate_stats(nas)
    print("Baseline CANDIDATE stats:", base_xau, base_eur, base_nas, flush=True)

    # ----- Winning NO_TRADE analysis -----
    print("Winning NO_TRADE analysis...", flush=True)
    wnt_xau = winning_notrade_analysis(xau)
    wnt_eur = winning_notrade_analysis(eur)
    wnt_nas = winning_notrade_analysis(nas)
    wnt_combined = {
        "n_total_nontrade": wnt_xau["n_total_nontrade"] + wnt_eur["n_total_nontrade"] + wnt_nas["n_total_nontrade"],
        "n_resolved_outcomes": wnt_xau["n_resolved_outcomes"] + wnt_eur["n_resolved_outcomes"] + wnt_nas["n_resolved_outcomes"],
        "winner_breakdown": dict(Counter(
            **wnt_xau["winner_breakdown"])) ,
        "n_with_features": wnt_xau["n_with_features"] + wnt_eur["n_with_features"] + wnt_nas["n_with_features"],
    }
    # merge winner breakdowns
    wnt_combined["winner_breakdown"] = {
        k: wnt_xau["winner_breakdown"].get(k, 0) + wnt_eur["winner_breakdown"].get(k, 0) + wnt_nas["winner_breakdown"].get(k, 0)
        for k in ("LONG", "SHORT", "NONE", "CONFLICT")
    }
    all_winner_rows = wnt_xau["winner_rows"] + wnt_eur["winner_rows"] + wnt_nas["winner_rows"]
    cluster_breakdown = cluster_winning_notrades(all_winner_rows)

    # ----- Edge tests -----
    print("Testing edges on combined records...", flush=True)
    e1 = test_edge_fvg_only(all_records)
    e2 = test_edge_sweep_displace(all_records)
    e3 = test_edge_fib50_mr(all_records)

    e1_sum = summarize_edge(e1, "FVG-only (no OB, H1-aligned)")
    e2_sum = summarize_edge(e2, "Sweep + displacement (no retest)")
    e3_sum = summarize_edge(e3, "Fib50 equilibrium mean-reversion (D1-aligned)")

    # Bonferroni for 3 tests
    p_raws = [e1_sum["p_raw"], e2_sum["p_raw"], e3_sum["p_raw"]]
    p_bonf = fdr_bonferroni(p_raws)
    e1_sum["p_bonferroni_3"] = p_bonf[0]
    e2_sum["p_bonferroni_3"] = p_bonf[1]
    e3_sum["p_bonferroni_3"] = p_bonf[2]

    # Per-instrument Bonferroni (3 edges × 3 instruments = 9)
    all_inst_ps = []
    for summ in (e1_sum, e2_sum, e3_sum):
        for inst, row in summ["per_instrument"].items():
            if row["p"] is not None:
                all_inst_ps.append((summ["label"], inst, row["p"]))
    ps_only = [p for _, _, p in all_inst_ps]
    bonf_ps = fdr_bonferroni(ps_only)
    per_inst_bonf = {}
    for (lab, inst, _), bp in zip(all_inst_ps, bonf_ps):
        per_inst_bonf.setdefault(lab, {})[inst] = bp

    for summ, lab in ((e1_sum, e1_sum["label"]), (e2_sum, e2_sum["label"]), (e3_sum, e3_sum["label"])):
        for inst, row in summ["per_instrument"].items():
            row["p_bonferroni_9"] = per_inst_bonf.get(lab, {}).get(inst)

    # ----- Extended-hour test -----
    by_hour_combined = {}
    # Combine by_hour from each instrument
    bh_xau = test_ooh_highwr_bins(xau)
    bh_eur = test_ooh_highwr_bins(eur)
    bh_nas = test_ooh_highwr_bins(nas)

    for h in range(24):
        agg = {"n": 0, "long_win": 0, "short_win": 0, "non_kz": 0, "in_kz": 0}
        for d in (bh_xau, bh_eur, bh_nas):
            if h in d:
                for k in agg:
                    agg[k] += d[h][k]
        by_hour_combined[h] = agg

    # For each hour, compute WR using symmetric both-direction-win logic:
    # Weighted WR = (long_win + short_win) / (n with resolved outcome);
    # but we lost the 'n_resolved' bucket so approximate with total n
    hour_rows = []
    for h, d in by_hour_combined.items():
        resolved = d["long_win"] + d["short_win"]
        # `n` here excludes NONE/CONFLICT by construction (long_win+short_win ≤ n)
        # We want: "at this hour, what fraction of candles had a clean 1.5R directional move?"
        frac = resolved / d["n"] if d["n"] else None
        hour_rows.append({
            "hour_utc": h,
            "n": d["n"],
            "resolved_1_5R_either_side": resolved,
            "resolved_frac": frac,
            "non_kz_frac": d["non_kz"] / d["n"] if d["n"] else None,
            "long_win": d["long_win"],
            "short_win": d["short_win"],
        })

    # ----- Write outputs -----
    out = {
        "baseline_candidate": {
            "XAUUSD": base_xau,
            "EURUSD": base_eur,
            "NAS100": base_nas,
        },
        "winning_notrade": {
            "XAUUSD": {k: v for k, v in wnt_xau.items() if k not in ("winner_rows", "loser_rows")},
            "EURUSD": {k: v for k, v in wnt_eur.items() if k not in ("winner_rows", "loser_rows")},
            "NAS100": {k: v for k, v in wnt_nas.items() if k not in ("winner_rows", "loser_rows")},
            "combined": wnt_combined,
            "cluster_breakdown_top15": cluster_breakdown[:15],
        },
        "edges": {
            "fvg_only_h1_aligned": e1_sum,
            "sweep_displacement_h1_aligned": e2_sum,
            "fib50_equilibrium_d1_aligned": e3_sum,
        },
        "extended_hour_table": hour_rows,
    }

    out_path = OUT_DIR / "analysis_output.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Wrote {out_path}", flush=True)

    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Baseline XAUUSD CAND: {base_xau}")
    print(f"\nWinning NO_TRADE combined:")
    print(f"  total non-trade resolved = {wnt_combined['n_resolved_outcomes']} / {wnt_combined['n_total_nontrade']}")
    print(f"  winners: {wnt_combined['winner_breakdown']}")
    print(f"\nEdge 1 (FVG+H1): n={e1_sum['n']} WR={e1_sum['wr']} ExpR={e1_sum['exp_r']} p_raw={e1_sum['p_raw']:.4f} p_bonf3={e1_sum['p_bonferroni_3']:.4f}")
    print(f"Edge 2 (Sweep+Disp+H1): n={e2_sum['n']} WR={e2_sum['wr']} ExpR={e2_sum['exp_r']} p_raw={e2_sum['p_raw']:.4f} p_bonf3={e2_sum['p_bonferroni_3']:.4f}")
    print(f"Edge 3 (Fib50+D1): n={e3_sum['n']} WR={e3_sum['wr']} ExpR={e3_sum['exp_r']} p_raw={e3_sum['p_raw']:.4f} p_bonf3={e3_sum['p_bonferroni_3']:.4f}")

    print("\nTop winning NO_TRADE clusters:")
    for c in cluster_breakdown[:10]:
        print(f"  n={c['n']:4d}  {c['signature']:60s}  by_symbol={c['by_symbol']}")

    # Save winner rows for η report inspection
    with open(OUT_DIR / "winner_rows_sample.json", "w", encoding="utf-8") as f:
        # Sample 200 rows for review
        import random
        random.seed(42)
        sample = all_winner_rows[:500]  # first 500 for determinism
        json.dump(sample, f, indent=2, default=str)

    return out


if __name__ == "__main__":
    main()
