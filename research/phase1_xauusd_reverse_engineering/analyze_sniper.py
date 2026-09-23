"""Phase 1 Track D sniper-subset analysis.

Runs stratified analysis on master_df.jsonl with Wilson 95% CIs for WR,
bootstrap 95% CIs for expectancy, Bonferroni correction.

Per-source verifiability table:
                    setup_grade   touch_count   m5_refined   realized_RR   outcome
batch_index           YES          NO            NO           YES            YES
f3_backtest           YES          PARTIAL*      NO           YES(cap~1.5)   YES
live_trade_record     YES          PARTIAL*      NO           NO             NO

*partial: regex-extracted from OB metadata, target OB matched by entry-price
"""
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

random.seed(42)

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
DIR = ROOT / "research" / "phase1_xauusd_reverse_engineering"
rows = [json.loads(l) for l in (DIR / "master_df.jsonl").open(encoding="utf-8")]


def wilson_ci(wins, n, alpha=0.05):
    """Wilson score 95% CI for a proportion."""
    if n == 0:
        return (None, None, None)
    z = 1.959963984540054  # N(0,1) 97.5%
    p = wins / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (p, max(0.0, center - margin), min(1.0, center + margin))


def bootstrap_expectancy_ci(rs, n_iter=2000, alpha=0.05):
    if not rs:
        return (None, None, None)
    n = len(rs)
    means = []
    for _ in range(n_iter):
        sample = [rs[random.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(alpha / 2 * n_iter)]
    hi = means[int((1 - alpha / 2) * n_iter)]
    return (sum(rs) / n, lo, hi)


def bootstrap_diff_ci(rs_a, rs_b, n_iter=2000, alpha=0.05):
    if not rs_a or not rs_b:
        return (None, None, None)
    diffs = []
    na, nb = len(rs_a), len(rs_b)
    for _ in range(n_iter):
        sa = [rs_a[random.randrange(na)] for _ in range(na)]
        sb = [rs_b[random.randrange(nb)] for _ in range(nb)]
        diffs.append(sum(sa) / na - sum(sb) / nb)
    diffs.sort()
    lo = diffs[int(alpha / 2 * n_iter)]
    hi = diffs[int((1 - alpha / 2) * n_iter)]
    return (sum(diffs) / n_iter, lo, hi)


def bootstrap_wr_diff_p(wins_a, n_a, wins_b, n_b, n_iter=10000):
    """Permutation / bootstrap test for WR difference.

    Return the two-sided p-value for H0: WR_a == WR_b via stratified bootstrap
    on the pool under null.
    """
    if n_a == 0 or n_b == 0:
        return None
    pool = [1] * (wins_a + wins_b) + [0] * ((n_a - wins_a) + (n_b - wins_b))
    obs = wins_a / n_a - wins_b / n_b
    count = 0
    for _ in range(n_iter):
        random.shuffle(pool)
        sa = pool[:n_a]
        sb = pool[n_a:n_a + n_b]
        diff = sum(sa) / n_a - sum(sb) / n_b
        if abs(diff) >= abs(obs):
            count += 1
    return count / n_iter


def fisher_exact_p(wa, na, wb, nb):
    """Fisher's exact two-sided p-value for a 2x2 table (preferred for small n)."""
    try:
        from scipy.stats import fisher_exact
        _, p = fisher_exact([[wa, na - wa], [wb, nb - wb]], alternative="two-sided")
        return p
    except ImportError:
        return None


def stratify_row(r):
    """Return (setup_grade, touch_count_bin, m5_refined_bin, realized_RR_bin)."""
    sg = r.get("setup_grade") or "other"
    if sg not in ("A+", "A", "B", "C"):
        sg = "other"
    tc = r.get("touch_count")
    if tc is None:
        tc_bin = "missing"
    elif tc == 1:
        tc_bin = "1"
    elif tc == 2:
        tc_bin = "2"
    else:
        tc_bin = ">=3"
    m5 = r.get("m5_refined")
    m5_bin = "missing" if m5 is None else ("true" if m5 else "false")
    rr = r.get("r_multiple")
    if rr is None:
        rr_bin = "missing"
    elif rr < 1.5:
        rr_bin = "<1.5"
    elif rr < 2.0:
        rr_bin = "1.5-1.99"
    else:
        rr_bin = ">=2.0"
    return (sg, tc_bin, m5_bin, rr_bin)


# ---------------------------------------------------------------------
# Canonicalize: only keep rows with outcome for WR/expectancy
# ---------------------------------------------------------------------
rows_with_outcome = [r for r in rows if r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN")]
# r_multiple coerce
for r in rows_with_outcome:
    v = r.get("r_multiple")
    r["_r"] = float(v) if v is not None else 0.0
    r["_w"] = 1 if r.get("outcome") == "WIN" else 0
    r["_strata"] = stratify_row(r)

print(f"rows with outcome: {len(rows_with_outcome)}")
print("by source:", Counter(r["source"] for r in rows_with_outcome))


# ---------------------------------------------------------------------
# Full stratification table (cells with n >= 5)
# ---------------------------------------------------------------------
by_strata = defaultdict(list)
for r in rows_with_outcome:
    by_strata[r["_strata"]].append(r)

print("\n=== Full 4-dim stratification (n >= 5) ===")
print(f"{'grade':>6} | {'tc':>7} | {'m5':>7} | {'rr':>9} | {'n':>4} | {'WR%':>5} | {'WR 95% CI':>18} | {'exp R':>7}")
print('-' * 95)
strata_results = []
for key in sorted(by_strata.keys()):
    rs = by_strata[key]
    n = len(rs)
    if n < 5:
        continue
    wins = sum(r["_w"] for r in rs)
    wr, wr_lo, wr_hi = wilson_ci(wins, n)
    exp, exp_lo, exp_hi = bootstrap_expectancy_ci([r["_r"] for r in rs], n_iter=1500)
    sg, tc, m5, rr = key
    print(f"{sg:>6} | {tc:>7} | {m5:>7} | {rr:>9} | {n:>4} | {wr*100:>5.1f} | [{wr_lo*100:5.1f}, {wr_hi*100:5.1f}] | {exp:>7.3f}")
    strata_results.append({
        "grade": sg, "touch_count": tc, "m5_refined": m5, "realized_RR": rr,
        "n": n, "wins": wins, "wr": wr, "wr_lo": wr_lo, "wr_hi": wr_hi,
        "exp": exp, "exp_lo": exp_lo, "exp_hi": exp_hi,
    })

# ---------------------------------------------------------------------
# Sniper cell exact: (A+, tc=1, m5=true, realized_RR>=2.0)
# ---------------------------------------------------------------------
print("\n=== Sniper cell (A+, tc=1, m5=true, realized_RR>=2.0) ===")
exact_sniper = [r for r in rows_with_outcome
                if r["_strata"] == ("A+", "1", "true", ">=2.0")]
print(f"exact sniper n: {len(exact_sniper)}")
# m5=true is never known, tc=1 only from F3 (RR capped at 1.5) → cannot satisfy
# Softened definitions: drop one axis at a time
print("\n--- Softened (drop m5): (A+, tc=1, realized_RR>=2.0) ---")
soft_no_m5 = [r for r in rows_with_outcome
              if r["setup_grade"] == "A+"
              and r.get("touch_count") == 1
              and r["_r"] >= 2.0]
print(f"n: {len(soft_no_m5)}")

print("\n--- Softened (drop m5+tc): (A+, realized_RR>=2.0) ---")
soft_tc_m5 = [r for r in rows_with_outcome
              if r["setup_grade"] == "A+"
              and r["_r"] >= 2.0]
print(f"n: {len(soft_tc_m5)}")
if soft_tc_m5:
    wins = sum(r["_w"] for r in soft_tc_m5)
    wr, lo, hi = wilson_ci(wins, len(soft_tc_m5))
    exp, el, eh = bootstrap_expectancy_ci([r["_r"] for r in soft_tc_m5])
    print(f"  WR: {wr*100:.1f}% [{lo*100:.1f}, {hi*100:.1f}]  Exp: {exp:.3f} [{el:.3f}, {eh:.3f}]")

print("\n--- Softened (drop m5+RR): (A+, tc=1) — WR test ---")
soft_drop_rr = [r for r in rows_with_outcome
                if r["setup_grade"] == "A+"
                and r.get("touch_count") == 1]
print(f"n: {len(soft_drop_rr)}")
if soft_drop_rr:
    wins = sum(r["_w"] for r in soft_drop_rr)
    wr, lo, hi = wilson_ci(wins, len(soft_drop_rr))
    exp, el, eh = bootstrap_expectancy_ci([r["_r"] for r in soft_drop_rr])
    print(f"  WR: {wr*100:.1f}% [{lo*100:.1f}, {hi*100:.1f}]  Exp: {exp:.3f} [{el:.3f}, {eh:.3f}]")

# ---------------------------------------------------------------------
# Sniper vs Non-Sniper comparisons (under softened defn since exact sniper n=0)
# We test 3 softened "sniper-like" definitions against their respective complements
# Bonferroni k = 3
# ---------------------------------------------------------------------
print("\n=== Sniper-like vs Non-Sniper-like (Bonferroni k=3) ===")
defns = {
    "A+_realizedRR>=2.0": lambda r: r["setup_grade"] == "A+" and r["_r"] >= 2.0,
    "A+_tc=1": lambda r: r["setup_grade"] == "A+" and r.get("touch_count") == 1,
    "A+_tc=1_realizedRR>=1.5": lambda r: (
        r["setup_grade"] == "A+" and r.get("touch_count") == 1 and r["_r"] >= 1.5
    ),
}
K = len(defns)
alpha_b = 0.05 / K
print(f"alpha (raw): 0.05, alpha (Bonferroni k={K}): {alpha_b:.4f}\n")

comp_results = []
for name, pred in defns.items():
    A = [r for r in rows_with_outcome if pred(r)]
    B = [r for r in rows_with_outcome if not pred(r)]
    if not A or not B:
        print(f"[{name}] insufficient: |A|={len(A)} |B|={len(B)}")
        continue
    wA = sum(r["_w"] for r in A); nA = len(A)
    wB = sum(r["_w"] for r in B); nB = len(B)
    wrA, lA, hA = wilson_ci(wA, nA)
    wrB, lB, hB = wilson_ci(wB, nB)
    p = bootstrap_wr_diff_p(wA, nA, wB, nB, n_iter=5000)
    p_fisher = fisher_exact_p(wA, nA, wB, nB)
    rA = [r["_r"] for r in A]; rB = [r["_r"] for r in B]
    eA, elA, ehA = bootstrap_expectancy_ci(rA)
    eB, elB, ehB = bootstrap_expectancy_ci(rB)
    dm, dlo, dhi = bootstrap_diff_ci(rA, rB)
    p_bonf = min(1.0, p * K)
    p_fisher_bonf = min(1.0, p_fisher * K) if p_fisher is not None else None
    print(f"[{name}]")
    print(f"  A: n={nA} wr={wrA*100:.1f}% [{lA*100:.1f},{hA*100:.1f}] exp={eA:+.3f} [{elA:+.3f},{ehA:+.3f}]")
    print(f"  B: n={nB} wr={wrB*100:.1f}% [{lB*100:.1f},{hB*100:.1f}] exp={eB:+.3f} [{elB:+.3f},{ehB:+.3f}]")
    print(f"  diff WR: {(wrA-wrB)*100:+.1f}pp   diff Exp: {dm:+.3f} [{dlo:+.3f},{dhi:+.3f}]")
    print(f"  p(boot raw)={p:.4f}  p(boot Bonf k={K})={p_bonf:.4f}")
    if p_fisher is not None:
        print(f"  p(Fisher raw)={p_fisher:.4f}  p(Fisher Bonf k={K})={p_fisher_bonf:.4f}")
    print()
    comp_results.append({
        "defn": name, "nA": nA, "wrA": wrA, "wrA_lo": lA, "wrA_hi": hA,
        "expA": eA, "expA_lo": elA, "expA_hi": ehA,
        "nB": nB, "wrB": wrB, "wrB_lo": lB, "wrB_hi": hB,
        "expB": eB, "expB_lo": elB, "expB_hi": ehB,
        "diff_wr": wrA - wrB, "diff_exp": dm, "diff_exp_lo": dlo, "diff_exp_hi": dhi,
        "p_raw": p, "p_bonferroni": p_bonf, "K": K,
        "p_fisher": p_fisher, "p_fisher_bonf": p_fisher_bonf,
    })

# ---------------------------------------------------------------------
# Required sample size for 80% power to detect 5pp uplift
# Using z_alpha = 1.96 (two-sided, alpha=0.05)
# n per arm ≈ (z_a/2 + z_b)^2 * [p1(1-p1) + p2(1-p2)] / (p1-p2)^2
# ---------------------------------------------------------------------
print("\n=== Required sample size (80% power, 5pp uplift) ===")
for baseline in [0.55, 0.60, 0.62, 0.65]:
    target = baseline + 0.05
    za = 1.96; zb = 0.84
    n = ((za + zb) ** 2) * (baseline*(1-baseline) + target*(1-target)) / (0.05**2)
    print(f"  baseline {baseline*100:.0f}% -> target {target*100:.0f}%: n per arm ~= {int(math.ceil(n))}")

# ---------------------------------------------------------------------
# Per-instrument + per-source breakdown of soft sniper def
# ---------------------------------------------------------------------
print("\n=== Per-instrument breakdown of (A+, realized_RR>=2.0) ===")
syms = sorted(set(r["symbol"] for r in rows_with_outcome if r.get("symbol")))
for s in syms:
    subset = [r for r in rows_with_outcome if r.get("symbol") == s]
    sniper_s = [r for r in subset if r["setup_grade"] == "A+" and r["_r"] >= 2.0]
    non_s = [r for r in subset if not (r["setup_grade"] == "A+" and r["_r"] >= 2.0)]
    if not sniper_s or not non_s:
        print(f"  {s}: subset n={len(subset)} sniper n={len(sniper_s)} non n={len(non_s)} — insufficient")
        continue
    wS = sum(r["_w"] for r in sniper_s); nS = len(sniper_s)
    wN = sum(r["_w"] for r in non_s); nN = len(non_s)
    wrS, loS, hiS = wilson_ci(wS, nS)
    wrN, loN, hiN = wilson_ci(wN, nN)
    print(f"  {s}: subset n={len(subset)} | sniper n={nS} wr={wrS*100:.1f}% [{loS*100:.1f},{hiS*100:.1f}] | non n={nN} wr={wrN*100:.1f}% [{loN*100:.1f},{hiN*100:.1f}]")

print("\n=== Per-source breakdown of (A+, realized_RR>=2.0) ===")
srcs = sorted(set(r["source"] for r in rows_with_outcome))
for s in srcs:
    subset = [r for r in rows_with_outcome if r["source"] == s]
    sniper_s = [r for r in subset if r["setup_grade"] == "A+" and r["_r"] >= 2.0]
    non_s = [r for r in subset if not (r["setup_grade"] == "A+" and r["_r"] >= 2.0)]
    if not sniper_s or not non_s:
        print(f"  {s}: subset n={len(subset)} sniper n={len(sniper_s)} non n={len(non_s)} — insufficient")
        continue
    wS = sum(r["_w"] for r in sniper_s); nS = len(sniper_s)
    wN = sum(r["_w"] for r in non_s); nN = len(non_s)
    wrS, loS, hiS = wilson_ci(wS, nS)
    wrN, loN, hiN = wilson_ci(wN, nN)
    print(f"  {s}: subset n={len(subset)} | sniper n={nS} wr={wrS*100:.1f}% [{loS*100:.1f},{hiS*100:.1f}] | non n={nN} wr={wrN*100:.1f}% [{loN*100:.1f},{hiN*100:.1f}]")

# Write CSV summary
import csv
with (DIR / "strata_summary.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["grade", "touch_count", "m5_refined", "realized_RR_bin", "n", "wins",
                "wr", "wr_lo", "wr_hi", "exp", "exp_lo", "exp_hi"])
    for s in strata_results:
        w.writerow([s["grade"], s["touch_count"], s["m5_refined"], s["realized_RR"], s["n"], s["wins"],
                    f"{s['wr']:.4f}", f"{s['wr_lo']:.4f}", f"{s['wr_hi']:.4f}",
                    f"{s['exp']:.4f}", f"{s['exp_lo']:.4f}", f"{s['exp_hi']:.4f}"])
with (DIR / "sniper_comparisons.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["defn", "nA", "wrA", "wrA_lo", "wrA_hi", "expA", "expA_lo", "expA_hi",
                "nB", "wrB", "wrB_lo", "wrB_hi", "expB", "expB_lo", "expB_hi",
                "diff_wr_pp", "diff_exp", "diff_exp_lo", "diff_exp_hi",
                "p_boot_raw", "p_boot_bonferroni", "p_fisher_raw", "p_fisher_bonferroni", "K"])
    for c in comp_results:
        pf = c.get("p_fisher")
        pfb = c.get("p_fisher_bonf")
        w.writerow([c["defn"], c["nA"], f"{c['wrA']:.4f}", f"{c['wrA_lo']:.4f}", f"{c['wrA_hi']:.4f}",
                    f"{c['expA']:.4f}", f"{c['expA_lo']:.4f}", f"{c['expA_hi']:.4f}",
                    c["nB"], f"{c['wrB']:.4f}", f"{c['wrB_lo']:.4f}", f"{c['wrB_hi']:.4f}",
                    f"{c['expB']:.4f}", f"{c['expB_lo']:.4f}", f"{c['expB_hi']:.4f}",
                    f"{c['diff_wr']*100:.2f}", f"{c['diff_exp']:.4f}",
                    f"{c['diff_exp_lo']:.4f}", f"{c['diff_exp_hi']:.4f}",
                    f"{c['p_raw']:.4f}", f"{c['p_bonferroni']:.4f}",
                    f"{pf:.4f}" if pf is not None else "",
                    f"{pfb:.4f}" if pfb is not None else "",
                    c["K"]])

print("\nWrote CSV artifacts.")
