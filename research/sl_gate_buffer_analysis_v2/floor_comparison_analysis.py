"""0.3 Floor vs 0.5 Floor — sweep-risk analysis.

Analyst: Opus 4.7 (2026-04-18)
Session 26 — CEO question: does 0.3 floor add real value, or just risk?

Methodology:
  - Load enriched retest CSV (725 rows, 6 degenerate → 719 clean).
  - Filter to tight-SL cohort: sl_distance < 1.5 * M15_ATR.
  - Subset by buffer/M15_ATR into three bands:
        * Admitted by BOTH 0.3 and 0.5 floor : buffer_atr >= 0.5
        * Admitted by 0.3 only              : 0.3 <= buffer_atr < 0.5
        * Rejected by BOTH                  : buffer_atr <  0.3
  - Report counts, WR, expectancy per band.
  - Sweep-risk analysis on the [0.3, 0.5) band:
        * loss rate
        * MAE (pips & ATR) distribution
        * sweep-risk metric: losses where MAE > buffer (i.e. price swept past OB edge)
        * "sweep-then-continue" approximation: REVERSED outcomes where penetration_a > 0
          means price went past OB_edge before the SL hit; in a "mercy buffer" regime
          (0.3 ATR wider) those could be winners.
  - 0.1-ATR histogram of the full 78-row tight cohort with WR, mean R, sweep count.
"""
from __future__ import annotations
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median, mean
from typing import Dict, List, Optional

REPO = Path(__file__).resolve().parents[2]
ENRICHED = REPO / "research" / "sl_gate_buffer_analysis" / "enriched_retest_with_m15_atr.csv"
OUT_DIR = REPO / "research" / "sl_gate_buffer_analysis_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def fnum(s: str) -> Optional[float]:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def percentile(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    v = sorted(values)
    k = (len(v) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(v) - 1)
    frac = k - lo
    return v[lo] + (v[hi] - v[lo]) * frac


def main():
    rows: List[dict] = []
    with open(ENRICHED, newline="") as f:
        for r in csv.DictReader(f):
            # normalize floats
            r["entry_price"] = fnum(r["entry_price"])
            r["sl_a"] = fnum(r["sl_a"])
            r["ob_edge"] = fnum(r["ob_edge"])
            r["sl_distance"] = fnum(r["sl_distance"])
            r["h1_atr"] = fnum(r["h1_atr"])
            r["m15_atr"] = fnum(r["m15_atr"])
            r["buffer"] = fnum(r["buffer"])
            r["buffer_m15_atr"] = fnum(r["buffer_m15_atr"])
            r["sl_dist_m15_atr"] = fnum(r["sl_dist_m15_atr"])
            r["continuation_r_a"] = fnum(r["continuation_r_a"])
            r["penetration_a_pips"] = fnum(r["penetration_a_pips"])
            r["r_mult"] = fnum(r["r_mult"])
            r["is_sweep_reverse"] = r["is_sweep_reverse"].strip().lower() == "true"
            r["sl_beyond_edge"] = r["sl_beyond_edge"].strip().lower() == "true"
            rows.append(r)

    print(f"Loaded enriched rows: {len(rows)}")

    # ---- 1. Filter degenerate rows ----
    degenerate: List[dict] = []
    good: List[dict] = []
    for r in rows:
        e = r["entry_price"]; sl = r["sl_a"]; d = r["direction"]
        if e is None or sl is None:
            degenerate.append(r); continue
        if d == "LONG" and sl >= e:
            degenerate.append(r); continue
        if d == "SHORT" and sl <= e:
            degenerate.append(r); continue
        # Also treat extreme-R rows as artifact suspects
        good.append(r)

    print(f"Degenerate (SL wrong side): {len(degenerate)}")
    print(f"Clean: {len(good)}")

    # Extreme R check
    extreme = [r for r in good if r["r_mult"] is not None and abs(r["r_mult"]) > 10]
    print(f"\n|R| > 10 rows: {len(extreme)}")
    for r in extreme[:10]:
        print(f"  {r['symbol']} {r['retest_ts']} side={r['side']} entry={r['entry_price']:.5f} "
              f"sl_a={r['sl_a']:.5f} r_mult={r['r_mult']:.3f} outcome={r['outcome_a']} "
              f"buffer_atr={r['buffer_m15_atr']:.3f} sl_dist_atr={r['sl_dist_m15_atr']:.3f}")

    # ---- 2. Tight cohort: sl_distance < 1.5 * M15_ATR ----
    tight = [r for r in good if r["sl_dist_m15_atr"] < 1.5]
    print(f"\nTight cohort (sl_dist < 1.5 M15_ATR): {len(tight)}")

    # Verify sl_beyond_edge on all tight rows
    not_beyond = [r for r in tight if not r["sl_beyond_edge"]]
    print(f"  not sl_beyond_edge: {len(not_beyond)}")  # should be 0 by construction

    # Verify framework == ob_retest
    non_ob = [r for r in tight if r.get("framework", "ob_retest") != "ob_retest"]
    print(f"  non-ob_retest framework: {len(non_ob)}")

    # ---- 3. Subset by buffer/M15_ATR bands within the tight cohort ----
    band_ge05 = [r for r in tight if r["buffer_m15_atr"] >= 0.5]
    band_03_05 = [r for r in tight if 0.3 <= r["buffer_m15_atr"] < 0.5]
    band_lt03 = [r for r in tight if r["buffer_m15_atr"] < 0.3]

    def summarize(label: str, subset: List[dict]) -> Dict:
        clfbl = [r for r in subset if r["r_mult"] is not None]
        wins = [r for r in clfbl if r["r_mult"] > 0]
        losses = [r for r in clfbl if r["r_mult"] < 0]
        sweeps = [r for r in clfbl if r["is_sweep_reverse"]]
        wr = 100.0 * len(wins) / len(clfbl) if clfbl else float("nan")
        exp = sum(r["r_mult"] for r in clfbl) / len(clfbl) if clfbl else float("nan")
        res = {
            "label": label,
            "n": len(subset),
            "classifiable": len(clfbl),
            "wins": len(wins),
            "losses": len(losses),
            "sweeps": len(sweeps),
            "wr_pct": wr,
            "expectancy_r": exp,
        }
        print(f"\n--- {label} ---")
        print(f"  n={res['n']}  classifiable={res['classifiable']}  W={res['wins']} L={res['losses']}  "
              f"WR={res['wr_pct']:.2f}%  E[R]={res['expectancy_r']:+.3f}  sweeps={res['sweeps']}")
        return res

    print("\n=== Q1: Frequency comparison within tight cohort ===")
    q1 = {
        "band_ge05": summarize("Tight with buffer >= 0.5 ATR (admitted by HEAD 0.5 floor AND 0.3 floor)", band_ge05),
        "band_03_05": summarize("Tight with 0.3 <= buffer < 0.5 ATR (admitted by 0.3 floor ONLY)", band_03_05),
        "band_lt03": summarize("Tight with buffer < 0.3 ATR (rejected by BOTH floors)", band_lt03),
    }

    print("\nTotals:")
    n05 = len(band_ge05)
    n0305 = len(band_03_05)
    nlt03 = len(band_lt03)
    print(f"  0.5-floor admits : {n05}")
    print(f"  0.3-floor admits : {n05 + n0305}")
    print(f"  EXTRA via 0.3    : {n0305}  (these are the trades at stake)")
    print(f"  Rejected by both : {nlt03}")

    # ---- 4. Q2: Sweep-risk on the 0.3-0.5 band ----
    print("\n=== Q2: Sweep-risk analysis — 0.3-0.5 buffer band ===")

    # For each trade in the band, compute:
    #   MAE (pips): mae_a_pips from combined_retests.csv (native ISO-Z timestamps match enriched)
    RAW_RETEST = REPO / "research" / "retest_geometry" / "outputs" / "a2_v2_validation" / "combined_retests.csv"
    raw_index: Dict[str, dict] = {}
    with open(RAW_RETEST, newline="") as f:
        for r in csv.DictReader(f):
            key = (r["symbol"], r["retest_ts"], r["side"])
            raw_index[key] = r

    # Attach mae_a to each row in the band
    def attach_mae(subset):
        for r in subset:
            key = (r["symbol"], r["retest_ts"], r["side"])
            raw = raw_index.get(key)
            if raw is None:
                r["mae_a_pips"] = None
                r["mae_a_atr"] = None
                continue
            r["mae_a_pips"] = fnum(raw.get("mae_a_pips"))
            r["mae_a_atr"] = fnum(raw.get("mae_a_atr"))
        return subset

    band_ge05 = attach_mae(band_ge05)
    band_03_05 = attach_mae(band_03_05)
    band_lt03 = attach_mae(band_lt03)

    print("\n--- Loss rate in 0.3-0.5 band ---")
    clfbl_0305 = [r for r in band_03_05 if r["r_mult"] is not None]
    losses_0305 = [r for r in clfbl_0305 if r["r_mult"] < 0]
    wins_0305 = [r for r in clfbl_0305 if r["r_mult"] > 0]
    print(f"  n={len(clfbl_0305)} W={len(wins_0305)} L={len(losses_0305)}  "
          f"loss_rate={100*len(losses_0305)/len(clfbl_0305):.2f}%")

    # MAE distribution for losers in 0.3-0.5 band
    print("\n--- MAE distribution for LOSERS in 0.3-0.5 band ---")
    loser_mae_pips = [r["mae_a_pips"] for r in losses_0305 if r["mae_a_pips"] is not None]
    loser_mae_atr = [r["mae_a_atr"] for r in losses_0305 if r["mae_a_atr"] is not None]

    def stats(label, xs, unit):
        if not xs:
            print(f"  {label}: EMPTY")
            return
        p50 = percentile(xs, 0.50); p75 = percentile(xs, 0.75); p90 = percentile(xs, 0.90)
        print(f"  {label}: n={len(xs)} min={min(xs):.3f} p50={p50:.3f} p75={p75:.3f} p90={p90:.3f} max={max(xs):.3f} ({unit})")

    stats("MAE (pips)", loser_mae_pips, "pips")
    stats("MAE (ATR)", loser_mae_atr, "M15 ATR")

    # Sweep-risk metric: how many losers had MAE > 0.5 ATR past OB edge?
    # MAE is against entry, buffer is entry-to-sl distance component past OB edge.
    # When price swept past SL to trigger -1R, MAE = sl_distance (approximately).
    # So "sweep past OB" means MAE > sl_distance + something, or more cleanly:
    # penetration_a_pips tells us how far past OB edge price went.
    # For a LOSER with penetration_a_pips > 0, price went past the OB edge — a sweep.

    print("\n--- Sweep events (losses with penetration_a > 0, meaning price went past OB edge) ---")
    sweep_0305 = [r for r in losses_0305 if r.get("is_sweep_reverse")]
    print(f"  n={len(losses_0305)} losers; {len(sweep_0305)} had penetration > 0 "
          f"({100*len(sweep_0305)/len(losses_0305) if losses_0305 else 0:.1f}% of losers)")

    # Close MAE bucket: how many losers hit SL where MAE is within 0.5 ATR of OB edge?
    # A "close sweep" = MAE_atr between 1.0 * sl_dist_atr (just enough to trigger SL)
    # and sl_dist_atr + 0.5 = just past SL.
    # We want: losers where MAE_atr - buffer_atr <= 0.5 -> SL hit mostly within buffer zone
    # i.e. "mercy margin" would likely have saved them IF sweep is shallow.
    within_05 = [r for r in losses_0305
                 if r.get("mae_a_atr") is not None and r.get("sl_dist_m15_atr") is not None
                 and r["mae_a_atr"] <= r["sl_dist_m15_atr"] + 0.5]
    print(f"  {len(within_05)} losers within 0.5 ATR past SL (i.e. a 0.5 ATR mercy margin would cover)")

    # ---- Sweep-then-continue: REVERSED outcome where price went back and hit target ----
    # This is hard to confirm without walking forward past SL. Use is_sweep_reverse as proxy.
    # The retest CSV has outcome_b = alternative tight SL outcome. Let's check sweep_b patterns.
    # But outcome_b uses a DIFFERENT SL, so not directly comparable.
    # We'll report what we CAN verify:
    #   - losers with penetration_a_pips > 0 (price went past OB then past SL -> classical sweep)
    # The "reverse into winner" requires extended walk-forward; not available in CSV.

    # ---- 5. Q3: 78-cohort buffer histogram ----
    print("\n=== Q3: 78-cohort buffer distribution (0.1-ATR bins from 0.3 to 2.0) ===")
    bin_edges = [round(0.3 + 0.1 * i, 2) for i in range(18)]  # 0.3..2.0
    bin_edges.append(10.0)  # catch-all
    histogram_rows = []
    for i in range(len(bin_edges) - 1):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        band = [r for r in tight if lo <= r["buffer_m15_atr"] < hi]
        clfbl = [r for r in band if r["r_mult"] is not None]
        wins = [r for r in clfbl if r["r_mult"] > 0]
        losses = [r for r in clfbl if r["r_mult"] < 0]
        mean_r = mean([r["r_mult"] for r in clfbl]) if clfbl else None
        wr = 100.0 * len(wins) / len(clfbl) if clfbl else None
        # Sweep-losses: losses with penetration_a_pips > 0 as proxy
        sweep_losses = [r for r in losses if r.get("is_sweep_reverse")]
        histogram_rows.append({
            "bin_lo": lo, "bin_hi": hi,
            "n": len(band),
            "wins": len(wins),
            "losses": len(losses),
            "wr_pct": wr,
            "mean_r": mean_r,
            "sweep_losses": len(sweep_losses),
        })

    print(f"{'Bin':<18} {'n':>4} {'W':>4} {'L':>4} {'WR%':>7} {'MeanR':>8} {'SwpL':>5}")
    for row in histogram_rows:
        if row["n"] == 0:
            continue
        wrstr = f"{row['wr_pct']:.2f}" if row['wr_pct'] is not None else "---"
        rstr = f"{row['mean_r']:+.3f}" if row['mean_r'] is not None else "---"
        print(f"[{row['bin_lo']:.1f}, {row['bin_hi']:.1f}) {row['n']:>4} {row['wins']:>4} "
              f"{row['losses']:>4} {wrstr:>7} {rstr:>8} {row['sweep_losses']:>5}")

    # Also get full-range buckets for tight cohort (including below 0.3)
    print("\n=== Full tight-cohort buffer distribution (with all buckets 0.0 -> 3.0) ===")
    full_bins = [(i * 0.1, (i + 1) * 0.1) for i in range(30)]  # 0.0..3.0
    for lo, hi in full_bins:
        band = [r for r in tight if lo <= r["buffer_m15_atr"] < hi]
        if not band:
            continue
        clfbl = [r for r in band if r["r_mult"] is not None]
        wins = [r for r in clfbl if r["r_mult"] > 0]
        wr = 100.0 * len(wins) / len(clfbl) if clfbl else None
        print(f"  [{lo:.1f}, {hi:.1f})  n={len(band):>3} W={len(wins):>3} WR={wr:.1f}%" if wr is not None else f"  [{lo:.1f}, {hi:.1f})  n={len(band):>3}")

    # ---- 6. Extra: comparisons between bands ----
    print("\n=== Band comparison: is [0.3, 0.5) better or worse than [>= 0.5]? ===")
    clfbl_ge05 = [r for r in band_ge05 if r["r_mult"] is not None]
    clfbl_0305_t = [r for r in band_03_05 if r["r_mult"] is not None]

    def agg(xs, label):
        if not xs:
            print(f"  {label}: EMPTY"); return None
        wins = sum(1 for r in xs if r["r_mult"] > 0)
        exp = sum(r["r_mult"] for r in xs) / len(xs)
        mae = [r["mae_a_atr"] for r in xs if r.get("mae_a_atr") is not None]
        print(f"  {label}: n={len(xs)} W={wins} WR={100*wins/len(xs):.2f}% E[R]={exp:+.3f}")
        if mae:
            print(f"    MAE(ATR): p50={percentile(mae, 0.5):.3f} p75={percentile(mae, 0.75):.3f} p90={percentile(mae, 0.90):.3f}")
        return (len(xs), wins, exp)

    print("\nTight cohort:")
    agg(clfbl_ge05, "  buffer >= 0.5")
    agg(clfbl_0305_t, "  0.3 <= buffer < 0.5")

    # ---- Non-tight cohort for sanity: when sl_dist >= 1.5 ATR, all admit regardless ----
    non_tight = [r for r in good if r["sl_dist_m15_atr"] >= 1.5]
    clfbl_nt = [r for r in non_tight if r["r_mult"] is not None]
    wins_nt = sum(1 for r in clfbl_nt if r["r_mult"] > 0)
    print(f"\nSanity: non-tight cohort (sl_dist >= 1.5 ATR): n={len(clfbl_nt)} "
          f"WR={100*wins_nt/len(clfbl_nt) if clfbl_nt else 0:.2f}% "
          f"E[R]={sum(r['r_mult'] for r in clfbl_nt)/len(clfbl_nt):+.3f}")

    # ---- 7. Store all results ----
    summary = {
        "rows_total": len(rows),
        "degenerate_excluded": len(degenerate),
        "clean_good": len(good),
        "tight_cohort_n": len(tight),
        "band_ge05_n": len(band_ge05),
        "band_03_05_n": len(band_03_05),
        "band_lt03_n": len(band_lt03),
        "q1": q1,
        "q2_0305_loss_rate": 100 * len(losses_0305) / len(clfbl_0305) if clfbl_0305 else None,
        "q2_loser_mae_atr_p50": percentile(loser_mae_atr, 0.5),
        "q2_loser_mae_atr_p75": percentile(loser_mae_atr, 0.75),
        "q2_loser_mae_atr_p90": percentile(loser_mae_atr, 0.9),
        "q2_sweep_losses_0305": len(sweep_0305),
        "q2_close_sweep_0305": len(within_05),
        "histogram": histogram_rows,
    }
    out_json = OUT_DIR / "floor_comparison_results.json"
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nWrote {out_json}")

    # Write histogram CSV
    hist_csv = OUT_DIR / "floor_comparison_histogram.csv"
    with open(hist_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(histogram_rows[0].keys()))
        w.writeheader()
        for row in histogram_rows:
            w.writerow(row)
    print(f"Wrote {hist_csv}")

    # Write the three band CSVs (full rows) for audit
    for label, subset in [("band_ge05", band_ge05), ("band_03_05", band_03_05), ("band_lt03", band_lt03)]:
        p = OUT_DIR / f"tight_{label}.csv"
        if subset:
            keys = sorted(subset[0].keys())
            with open(p, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                for r in subset:
                    w.writerow({k: r.get(k) for k in keys})
            print(f"Wrote {p} (n={len(subset)})")

    # Per-symbol breakdown on the 78 cohort
    print("\n=== Per-symbol tight-cohort stats ===")
    by_sym: Dict[str, List[dict]] = defaultdict(list)
    for r in tight:
        by_sym[r["symbol"]].append(r)
    per_sym = {}
    print(f"{'Symbol':<12} {'n':>3} {'W':>3} {'L':>3} {'WR%':>7} {'E[R]':>8} {'sweeps':>7}  "
          f"{'n03-05':>7} {'W03-05':>7} {'WR03-05':>8}")
    for sym in sorted(by_sym):
        subset = by_sym[sym]
        clfbl = [r for r in subset if r["r_mult"] is not None]
        wins = sum(1 for r in clfbl if r["r_mult"] > 0)
        losses = sum(1 for r in clfbl if r["r_mult"] < 0)
        sweeps = sum(1 for r in clfbl if r["is_sweep_reverse"])
        wr = 100 * wins / len(clfbl) if clfbl else float("nan")
        exp = sum(r["r_mult"] for r in clfbl) / len(clfbl) if clfbl else float("nan")

        band = [r for r in subset if 0.3 <= r["buffer_m15_atr"] < 0.5]
        band_clfbl = [r for r in band if r["r_mult"] is not None]
        band_wins = sum(1 for r in band_clfbl if r["r_mult"] > 0)
        band_wr = 100 * band_wins / len(band_clfbl) if band_clfbl else float("nan")

        per_sym[sym] = {
            "n": len(subset), "wins": wins, "losses": losses, "wr": wr, "exp": exp,
            "sweeps": sweeps, "band_0305_n": len(band),
            "band_0305_wins": band_wins, "band_0305_wr": band_wr,
        }
        print(f"{sym:<12} {len(subset):>3} {wins:>3} {losses:>3} {wr:>7.2f} "
              f"{exp:>+8.3f} {sweeps:>7}  {len(band):>7} {band_wins:>7} {band_wr:>8.2f}" if band_clfbl else
              f"{sym:<12} {len(subset):>3} {wins:>3} {losses:>3} {wr:>7.2f} "
              f"{exp:>+8.3f} {sweeps:>7}  {len(band):>7} {band_wins:>7} {'n/a':>8}")

    summary["per_symbol"] = per_sym

    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2, default=str)


if __name__ == "__main__":
    main()
