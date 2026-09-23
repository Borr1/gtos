"""Independent reviewer analysis for the touch-count gate decision.

Re-derives WR, Exp R, CIs, and threshold counterfactuals from A1+A2 raw data
without copying A11's bucketing decisions. Outputs:
  _reviewer_results.json — machine-readable
  _reviewer_results.txt  — human-readable summary
"""
from __future__ import annotations
import json
import math
import random
from pathlib import Path
from collections import Counter, defaultdict
from itertools import product

random.seed(20260425)

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
AUD = ROOT / "research" / "touch_count_audit"


def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    p = wins / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def bootstrap_mean_ci(values: list[float], iters: int = 5000, alpha: float = 0.05):
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    n = len(values)
    means = []
    for _ in range(iters):
        sample = [values[random.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(alpha / 2 * iters)]
    hi = means[int((1 - alpha / 2) * iters)]
    return (sum(values) / n, lo, hi)


def fisher_2x2(a: int, b: int, c: int, d: int) -> float:
    """Fisher exact test, two-sided. a+b in row 1, c+d in row 2.
    Returns p-value."""
    from math import comb
    n = a + b + c + d
    r1 = a + b
    r2 = c + d
    c1 = a + c
    if r1 == 0 or r2 == 0 or c1 == 0:
        return 1.0
    obs = comb(r1, a) * comb(r2, c) / comb(n, c1)
    p_val = 0.0
    for ai in range(max(0, c1 - r2), min(c1, r1) + 1):
        bi = r1 - ai
        ci = c1 - ai
        di = r2 - ci
        prob = comb(r1, ai) * comb(r2, ci) / comb(n, c1)
        if prob <= obs + 1e-12:
            p_val += prob
    return min(1.0, p_val)


def chi_square_independence(observed: list[list[int]]) -> tuple[float, float, int]:
    """Returns (chi2, p, dof) for an R x C contingency table.
    Uses survival function of chi2 from scipy if available, else gamma fallback."""
    rows = len(observed)
    cols = len(observed[0])
    row_tot = [sum(r) for r in observed]
    col_tot = [sum(observed[r][c] for r in range(rows)) for c in range(cols)]
    total = sum(row_tot)
    if total == 0:
        return (0.0, 1.0, (rows - 1) * (cols - 1))
    chi2 = 0.0
    for r in range(rows):
        for c in range(cols):
            exp = row_tot[r] * col_tot[c] / total
            if exp > 0:
                chi2 += (observed[r][c] - exp) ** 2 / exp
    dof = (rows - 1) * (cols - 1)
    # Use scipy if avail
    try:
        from scipy.stats import chi2 as _c2
        p = float(_c2.sf(chi2, dof))
    except Exception:
        # crude approximation
        p = math.exp(-chi2 / 2)  # rough lower bound
    return (chi2, p, dof)


def power_analysis_two_means(n1: int, n2: int, sd: float, delta: float, alpha: float = 0.05) -> float:
    """Approximate two-sample t-test power.
    Returns power for detecting difference of `delta` between two means."""
    try:
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha / 2)
        # Pooled SE under equal SD
        se = sd * math.sqrt(1 / n1 + 1 / n2)
        z_beta = abs(delta) / se - z_alpha
        return float(norm.cdf(z_beta))
    except Exception:
        # rough approximation w/o scipy
        z_alpha = 1.96
        se = sd * math.sqrt(1 / n1 + 1 / n2)
        z_beta = abs(delta) / se - z_alpha
        # Standard normal CDF approximation
        if z_beta < -8:
            return 0.0
        if z_beta > 8:
            return 1.0
        # Erf series
        def phi(x):
            t = 1 / (1 + 0.2316419 * abs(x))
            d = 0.3989423 * math.exp(-x * x / 2)
            p = d * t * (0.319382 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
            return 1 - p if x > 0 else p
        return phi(z_beta)


# ----------------------------------------------------------------------
# Load combined dataset
# ----------------------------------------------------------------------

def load_combined():
    rows = []
    with open(AUD / "_combined.jsonl") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def filled_rows(rows):
    return [r for r in rows if r["outcome"] in ("WIN", "LOSS", "BE")]


def dedup_rows(rows):
    """Dedup on (symbol, ts) preferring A2 (v2-active)."""
    out = {}
    for r in rows:
        k = (r["symbol"], r["ts"])
        if k not in out:
            out[k] = r
        elif r["src"] == "A2":
            out[k] = r
    return list(out.values())


def bucket_a11(touch: int) -> str:
    """A11's bucketing: touch <= 1 -> '1'."""
    if touch <= 1:
        return "1"
    elif touch == 2:
        return "2"
    else:
        return ">=3"


def bucket_pure(touch: int) -> str:
    """Pure direction-aware: -1 -> 'missing'; 0/1 -> respective; >=3 -> bucket."""
    if touch < 0:
        return "missing"
    elif touch == 0:
        return "0"
    elif touch == 1:
        return "1"
    elif touch == 2:
        return "2"
    else:
        return ">=3"


def stratum_stats(rs: list[dict]) -> dict:
    n = len(rs)
    if n == 0:
        return {"n": 0}
    wins = sum(1 for r in rs if r["outcome"] == "WIN")
    losses = sum(1 for r in rs if r["outcome"] == "LOSS")
    bes = sum(1 for r in rs if r["outcome"] == "BE")
    wr = wins / n
    wr_lo, wr_hi = wilson_ci(wins, n)
    rs_R = [r["r_multiple"] for r in rs if r["r_multiple"] is not None]
    if rs_R:
        exp, exp_lo, exp_hi = bootstrap_mean_ci(rs_R, iters=5000)
    else:
        exp, exp_lo, exp_hi = float("nan"), float("nan"), float("nan")
    total_r = sum(rs_R)
    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "be": bes,
        "wr": wr,
        "wr_ci95": [wr_lo, wr_hi],
        "exp_r": exp,
        "exp_ci95": [exp_lo, exp_hi],
        "total_r": total_r,
    }


# ----------------------------------------------------------------------
# Run analysis
# ----------------------------------------------------------------------
def analyze():
    rows = load_combined()
    filled = filled_rows(rows)
    deduped_filled = filled_rows(dedup_rows(rows))
    print(f"Total combined CANDs: {len(rows)}")
    print(f"Filled (A1+A2 no dedup): {len(filled)}")
    print(f"Filled deduped: {len(deduped_filled)}")
    print()

    results = {
        "n_combined": len(rows),
        "n_filled_no_dedup": len(filled),
        "n_filled_dedup": len(deduped_filled),
        "by_dataset": {},
        "by_bucketing": {},
        "per_instrument": {},
        "per_instrument_per_stratum": {},
        "thresholds": {},
        "power": {},
        "fisher_chi2": {},
    }

    # ------------------------------------------------------------------
    # Per-dataset stratified stats (A11 bucketing for direct comparison)
    # ------------------------------------------------------------------
    for label, dataset in [
        ("A1_only", [r for r in filled if r["src"] == "A1"]),
        ("A2_only", [r for r in filled if r["src"] == "A2"]),
        ("Combined_no_dedup", filled),
        ("Combined_dedup_A2_priority", deduped_filled),
    ]:
        for bucketing_name, bucket_fn in [("A11_<=1=1", bucket_a11), ("Pure_dir_aware", bucket_pure)]:
            buckets = defaultdict(list)
            for r in dataset:
                t = r["touch_dir"] if r["touch_dir"] is not None else -1
                b = bucket_fn(t)
                buckets[b].append(r)
            stats = {b: stratum_stats(rs) for b, rs in buckets.items()}
            results["by_dataset"].setdefault(label, {})[bucketing_name] = stats

    # ------------------------------------------------------------------
    # Per-instrument-per-stratum (A11 bucketing)
    # ------------------------------------------------------------------
    for inst in ["XAUUSD", "USDJPY"]:
        inst_rows = [r for r in deduped_filled if r["symbol"] == inst]
        buckets = defaultdict(list)
        for r in inst_rows:
            t = r["touch_dir"] if r["touch_dir"] is not None else -1
            b = bucket_a11(t)
            buckets[b].append(r)
        stats = {b: stratum_stats(rs) for b, rs in buckets.items()}
        results["per_instrument_per_stratum"][inst] = stats

    # ------------------------------------------------------------------
    # Threshold simulator: for each threshold T, what would the gate's
    # realized R total be? (from A11 logic)
    # ------------------------------------------------------------------
    # Threshold T means: REJECT if touch >= T
    # Status quo T=2 (REJECT touch>=2 means we'd lose those trades' R)
    # LOOSEN_TO_3 (T=3) means: only REJECT if touch >= 3
    # LOOSEN_TO_4 (T=4) means: only REJECT if touch >= 4
    # REMOVE means: keep all (T=infinity)
    # SOFT_FEATURE means: keep all (no reject) — same as REMOVE for backtest
    # KEEP means: reject all touch>=2
    #
    # Note: this is a counterfactual — it assumes those rejected trades'
    # outcomes are observable. Since we only see what was actually CAND'd,
    # if the gate was applied at the time, those trades wouldn't have happened.
    # In A1, gate WAS applied (touch>=2 rejected), but those trades still APPEAR
    # in the dataset because A1's touch_count gate was disabled in the backtest.
    # Actually A1 was a VC of the touch gate disabled — let me verify.

    for label, dataset in [
        ("A1_only", [r for r in filled if r["src"] == "A1"]),
        ("A2_only", [r for r in filled if r["src"] == "A2"]),
        ("Combined_no_dedup", filled),
        ("Combined_dedup", deduped_filled),
    ]:
        sim = {}
        for T in [2, 3, 4, 5, 100]:  # 100 = effectively no gate
            # Trades that PASS the gate: touch < T
            keep = [r for r in dataset if (r["touch_dir"] if r["touch_dir"] is not None else -1) < T]
            # Trades that would be REJECTED: touch >= T (we lose their R)
            reject = [r for r in dataset if (r["touch_dir"] if r["touch_dir"] is not None else -1) >= T]
            kept_R = sum(r["r_multiple"] for r in keep if r["r_multiple"] is not None)
            kept_n = len(keep)
            kept_wins = sum(1 for r in keep if r["outcome"] == "WIN")
            kept_wr = kept_wins / kept_n if kept_n else 0
            kept_exp = kept_R / kept_n if kept_n else 0
            rej_R = sum(r["r_multiple"] for r in reject if r["r_multiple"] is not None)
            rej_n = len(reject)
            sim[f"T={T}"] = {
                "kept_n": kept_n,
                "kept_wins": kept_wins,
                "kept_wr": kept_wr,
                "kept_exp_r": kept_exp,
                "kept_total_r": kept_R,
                "rejected_n": rej_n,
                "rejected_total_r_lost": rej_R,
            }
        results["thresholds"][label] = sim

    # ------------------------------------------------------------------
    # Statistical tests
    # ------------------------------------------------------------------
    # Use combined dedup
    ds = deduped_filled
    buckets = defaultdict(list)
    for r in ds:
        t = r["touch_dir"] if r["touch_dir"] is not None else -1
        b = bucket_a11(t)
        buckets[b].append(r)

    # Fisher tests pairwise
    pairs = [("1", "2"), ("2", ">=3"), ("1", ">=3")]
    for a_label, b_label in pairs:
        ar = buckets[a_label]
        br = buckets[b_label]
        a_w = sum(1 for r in ar if r["outcome"] == "WIN")
        a_l = sum(1 for r in ar if r["outcome"] == "LOSS")
        b_w = sum(1 for r in br if r["outcome"] == "WIN")
        b_l = sum(1 for r in br if r["outcome"] == "LOSS")
        p = fisher_2x2(a_w, a_l, b_w, b_l)
        results["fisher_chi2"][f"{a_label}_vs_{b_label}"] = {
            "a_wr": a_w / max(1, len(ar)),
            "b_wr": b_w / max(1, len(br)),
            "a_n": len(ar),
            "b_n": len(br),
            "fisher_p": p,
        }

    # Chi-square 3x2 (WIN vs LOSS across 3 buckets, BE excluded)
    ws = [sum(1 for r in buckets[b] if r["outcome"] == "WIN") for b in ["1", "2", ">=3"]]
    ls = [sum(1 for r in buckets[b] if r["outcome"] == "LOSS") for b in ["1", "2", ">=3"]]
    chi2, p, dof = chi_square_independence([ws, ls])
    results["fisher_chi2"]["chi2_3x2"] = {"chi2": chi2, "p": p, "dof": dof, "ws": ws, "ls": ls}

    # Bonferroni: 3 pairwise tests
    p_vals_corrected = [
        ("1_vs_2", min(1.0, results["fisher_chi2"]["1_vs_2"]["fisher_p"] * 3)),
        ("2_vs_>=3", min(1.0, results["fisher_chi2"]["2_vs_>=3"]["fisher_p"] * 3)),
        ("1_vs_>=3", min(1.0, results["fisher_chi2"]["1_vs_>=3"]["fisher_p"] * 3)),
    ]
    results["bonferroni_3_pairs"] = dict(p_vals_corrected)

    # ------------------------------------------------------------------
    # Power analysis: detecting a +0.20R Exp R difference
    # ------------------------------------------------------------------
    # Get pooled SD of R across all filled
    R_vals = [r["r_multiple"] for r in ds if r["r_multiple"] is not None]
    mean_R = sum(R_vals) / len(R_vals) if R_vals else 0
    var_R = sum((r - mean_R) ** 2 for r in R_vals) / max(1, len(R_vals) - 1)
    sd_R = math.sqrt(var_R)

    # Power for various comparisons
    for delta in [0.10, 0.20, 0.30, 0.50]:
        # Equal-n assumption: each of two groups has n/2
        n_each = len(ds) // 2
        results["power"][f"delta_{delta}_equal_n_each_{n_each}"] = power_analysis_two_means(
            n_each, n_each, sd_R, delta
        )

    # Specific touch=1 vs touch=2 power
    n1 = sum(1 for r in ds if (r["touch_dir"] if r["touch_dir"] is not None else -1) <= 1)
    n2 = sum(1 for r in ds if (r["touch_dir"] if r["touch_dir"] is not None else -1) == 2)
    n3plus = sum(1 for r in ds if (r["touch_dir"] if r["touch_dir"] is not None else -1) >= 3)
    for delta in [0.10, 0.20, 0.30, 0.50]:
        results["power"][f"1vs2_delta_{delta}"] = power_analysis_two_means(n1, n2, sd_R, delta)
        results["power"][f"1vs3plus_delta_{delta}"] = power_analysis_two_means(n1, n3plus, sd_R, delta)

    results["pooled_R_sd"] = sd_R
    results["mean_R"] = mean_R

    # ------------------------------------------------------------------
    # Per-instrument view of A1 vs A2
    # ------------------------------------------------------------------
    for inst in ["XAUUSD", "USDJPY"]:
        d_a1 = [r for r in filled if r["src"] == "A1" and r["symbol"] == inst]
        d_a2 = [r for r in filled if r["src"] == "A2" and r["symbol"] == inst]
        results["per_instrument"][inst] = {
            "A1": stratum_stats(d_a1),
            "A2": stratum_stats(d_a2),
        }

    # Save
    with open(AUD / "_reviewer_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved _reviewer_results.json")

    return results


def print_summary(results):
    print()
    print("=" * 78)
    print("REVIEWER ANALYSIS SUMMARY (independent re-derivation)")
    print("=" * 78)

    print()
    print(f"Pooled R standard deviation: {results['pooled_R_sd']:.3f}")
    print(f"Mean R across deduped filled: {results['mean_R']:+.3f}")

    print()
    print("--- Per-dataset, A11 bucketing (touch<=1='1') ---")
    for ds_label, sub in results["by_dataset"].items():
        print(f"\n{ds_label} (A11 bucketing):")
        for b, st in sub.get("A11_<=1=1", {}).items():
            if st.get("n", 0) > 0:
                print(f"  bucket={b}: n={st['n']:>3} W{st['wins']:>2}L{st['losses']:>2}BE{st['be']:>2}"
                      f" WR={st['wr']:.3f} [{st['wr_ci95'][0]:.3f},{st['wr_ci95'][1]:.3f}]"
                      f" ExpR={st['exp_r']:+.3f} [{st['exp_ci95'][0]:+.3f},{st['exp_ci95'][1]:+.3f}]"
                      f" TotR={st['total_r']:+.2f}")

    print()
    print("--- Per-dataset, Pure direction-aware bucketing ---")
    for ds_label, sub in results["by_dataset"].items():
        if ds_label != "Combined_dedup_A2_priority":
            continue
        print(f"\n{ds_label} (Pure dir-aware):")
        for b, st in sub.get("Pure_dir_aware", {}).items():
            if st.get("n", 0) > 0:
                print(f"  touch={b}: n={st['n']:>3} W{st['wins']:>2}L{st['losses']:>2}BE{st['be']:>2}"
                      f" WR={st['wr']:.3f} [{st['wr_ci95'][0]:.3f},{st['wr_ci95'][1]:.3f}]"
                      f" ExpR={st['exp_r']:+.3f} [{st['exp_ci95'][0]:+.3f},{st['exp_ci95'][1]:+.3f}]"
                      f" TotR={st['total_r']:+.2f}")

    print()
    print("--- Per-instrument-per-stratum (deduped, A11 bucketing) ---")
    for inst, buckets in results["per_instrument_per_stratum"].items():
        print(f"\n{inst}:")
        for b, st in buckets.items():
            if st.get("n", 0) > 0:
                print(f"  bucket={b}: n={st['n']:>3} W{st['wins']:>2}L{st['losses']:>2}"
                      f" WR={st['wr']:.3f} [{st['wr_ci95'][0]:.3f},{st['wr_ci95'][1]:.3f}]"
                      f" ExpR={st['exp_r']:+.3f} [{st['exp_ci95'][0]:+.3f},{st['exp_ci95'][1]:+.3f}]"
                      f" TotR={st['total_r']:+.2f}")

    print()
    print("--- Threshold counterfactuals ---")
    print("(KEEP=T2; LOOSEN_TO_3=T3; LOOSEN_TO_4=T4; REMOVE=T100)")
    for ds_label, sim in results["thresholds"].items():
        print(f"\n{ds_label}:")
        print(f"  {'Threshold':<10} {'kept_n':>7} {'kept_W':>7} {'WR':>6} {'ExpR':>7} {'TotR':>7} {'rej_n':>6} {'rej_R_lost':>12}")
        for k, st in sim.items():
            print(f"  {k:<10} {st['kept_n']:>7} {st['kept_wins']:>7} {st['kept_wr']:>6.3f} {st['kept_exp_r']:>+7.3f} {st['kept_total_r']:>+7.2f} {st['rejected_n']:>6} {st['rejected_total_r_lost']:>+12.2f}")

    print()
    print("--- Statistical tests ---")
    fc = results["fisher_chi2"]
    print(f"Fisher 1 vs 2: WR {fc['1_vs_2']['a_wr']:.3f} (n={fc['1_vs_2']['a_n']}) vs {fc['1_vs_2']['b_wr']:.3f} (n={fc['1_vs_2']['b_n']}) -> p={fc['1_vs_2']['fisher_p']:.3f}")
    print(f"Fisher 2 vs >=3: WR {fc['2_vs_>=3']['a_wr']:.3f} (n={fc['2_vs_>=3']['a_n']}) vs {fc['2_vs_>=3']['b_wr']:.3f} (n={fc['2_vs_>=3']['b_n']}) -> p={fc['2_vs_>=3']['fisher_p']:.3f}")
    print(f"Fisher 1 vs >=3: WR {fc['1_vs_>=3']['a_wr']:.3f} (n={fc['1_vs_>=3']['a_n']}) vs {fc['1_vs_>=3']['b_wr']:.3f} (n={fc['1_vs_>=3']['b_n']}) -> p={fc['1_vs_>=3']['fisher_p']:.3f}")
    print(f"Chi2 3x2 (W vs L by bucket): chi2={fc['chi2_3x2']['chi2']:.3f} dof={fc['chi2_3x2']['dof']} p={fc['chi2_3x2']['p']:.3f}")
    print(f"Bonferroni-corrected (×3): {results['bonferroni_3_pairs']}")

    print()
    print("--- Power analysis (combined dedup, n={}) ---".format(results["n_filled_dedup"]))
    pw = results["power"]
    n_each_key = "delta_0.2_equal_n_each_" + str(results["n_filled_dedup"]//2)
    print(f"Detect ExpR delta=0.20R between equal-sized halves: power={pw[n_each_key]:.3f}")
    print(f"Detect 1 vs 2 ExpR delta=0.20R: power={pw['1vs2_delta_0.2']:.3f}")
    print(f"Detect 1 vs 2 ExpR delta=0.30R: power={pw['1vs2_delta_0.3']:.3f}")
    print(f"Detect 1 vs >=3 ExpR delta=0.20R: power={pw['1vs3plus_delta_0.2']:.3f}")


if __name__ == "__main__":
    res = analyze()
    print_summary(res)
