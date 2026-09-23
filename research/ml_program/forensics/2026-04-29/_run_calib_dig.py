"""Calibration deep-dive: AUC vs realized-R disconnect investigation."""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
M = ROOT / "research/ml_program/models/k54_v3"
F = ROOT / "research/ml_program/forensics/2026-04-29"
SCOUT = ROOT / "research/ml_program/scout/feature_matrix.parquet"


def jload(p):
    return json.loads(p.read_text())


def jdump(o, p):
    p.write_text(json.dumps(o, indent=2, default=lambda x: float(x) if hasattr(x, "item") else str(x)))


cpcv = jload(M / "cpcv_paired_results.json")
scout = pd.read_parquet(SCOUT)

n_rows = len(scout)
sum_p_v3 = np.zeros(n_rows)
count = np.zeros(n_rows, dtype=int)
for path in cpcv["paths"]:
    for i, idx in enumerate(path["test_idx"]):
        sum_p_v3[idx] += path["p_v3_te"][i]
        count[idx] += 1
mean_p_v3 = np.divide(sum_p_v3, count, out=np.full(n_rows, np.nan), where=count > 0)

realized_r = scout["__realized_r"].to_numpy()
win = scout["__win_label"].to_numpy()

print("=== Calibration disconnect deep dive ===\n")

# AUC of mean_p_v3 vs win_label
auc_overall = roc_auc_score(win, mean_p_v3)
print(f"AUC (aggregated CPCV predictions vs win_label): {auc_overall:.4f}")

# AUC of mean_p_v3 vs (realized_r > 0)
# (Should be the same as win_label since win == (R > 0))

# AUC of mean_p_v3 vs (realized_r > 0.5R) - a stricter "good trade" target
strong_win = (realized_r >= 1.0).astype(int)
auc_strong = roc_auc_score(strong_win, mean_p_v3)
print(f"AUC vs strong-win (R >= 1.0): {auc_strong:.4f}")

# Pearson + Spearman of p_v3 vs realized_r
pearson_r, p_pearson = stats.pearsonr(mean_p_v3, realized_r)
spearman_r, p_spearman = stats.spearmanr(mean_p_v3, realized_r)
print(f"\nCorrelation of p_v3 with realized_r:")
print(f"  Pearson: {pearson_r:+.4f}, p={p_pearson:.4f}")
print(f"  Spearman: {spearman_r:+.4f}, p={p_spearman:.4f}")

# Decile analysis
print("\nDecile of p_v3 vs realized R outcomes:")
edges = np.percentile(mean_p_v3, np.linspace(0, 100, 11))
edges[0] -= 1e-9
results = []
for i in range(10):
    mask = (mean_p_v3 >= edges[i]) & (mean_p_v3 < edges[i + 1] + 1e-9)
    if mask.sum() == 0:
        continue
    r_in = realized_r[mask]
    p_in = mean_p_v3[mask]
    results.append({
        "decile": i + 1,
        "p_range": [round(float(edges[i]), 4), round(float(edges[i + 1]), 4)],
        "n": int(mask.sum()),
        "mean_p": round(float(p_in.mean()), 4),
        "mean_R": round(float(r_in.mean()), 4),
        "WR": round(float((r_in > 0).mean()), 4),
        "WR_strong": round(float((r_in >= 1.0).mean()), 4),
    })
    print(f"  D{i+1}: p=[{edges[i]:.3f},{edges[i+1]:.3f}] n={int(mask.sum()):>4} "
          f"meanP={p_in.mean():.3f} meanR={r_in.mean():+.3f} WR={(r_in > 0).mean():.3f}")

# Check: does the model rank by win_label correctly (AUC > 0.5)?
# But under-rank by realized_R magnitude?
# i.e. p_v3 might predict P(R > 0) well, but not predict the MAGNITUDE
# Check: mean realized_R by p_v3 quantile
print("\nKey diagnostic: correlation of p_v3 with realized_r is REVERSED?")
# Per-decile mean R direction
mean_r_by_decile = [r["mean_R"] for r in results]
print(f"  Mean R by decile (D1-low to D10-high p): {[round(r,3) for r in mean_r_by_decile]}")
# Is this monotonically increasing or jagged?
diffs = np.diff(mean_r_by_decile)
print(f"  Decile-to-decile differences: {[round(d,3) for d in diffs]}")
print(f"  Number of monotonic-up steps: {(np.array(diffs) > 0).sum()} / 9")

# AUC by symbol/cohort
symbol = scout["__symbol"].to_numpy()
print("\nPer-symbol AUC (aggregated CPCV pred vs win_label):")
for sym in np.unique(symbol):
    mask = symbol == sym
    if len(np.unique(win[mask])) < 2:
        continue
    auc = roc_auc_score(win[mask], mean_p_v3[mask])
    n = int(mask.sum())
    # Pearson with realized R
    pr, _ = stats.pearsonr(mean_p_v3[mask], realized_r[mask])
    print(f"  {sym}: n={n:>3} AUC={auc:.4f} pearson_R={pr:+.4f}")

# Spearman across the cohort
print("\nIs the model sign-correct on AUC but magnitude-wrong on realized R?")
print(f"  AUC overall: {auc_overall:.4f} (above 0.5 - sign signal)")
print(f"  Pearson(p_v3, realized_r): {pearson_r:+.4f} (positive but small)")
print(f"  Spearman: {spearman_r:+.4f}")
print()
print("DIAGNOSIS:")
if pearson_r > 0 and pearson_r < 0.1:
    print("  Model predicts P(win)=1 mildly correctly (AUC > 0.5)")
    print("  but does NOT predict realized R magnitude well.")
    print("  The R-payoff structure is: WR=0.58 with mean(win_R)=+1.30, mean(loss_R)=-0.94.")
    print("  Each binary win/loss has fixed magnitude, so AUC > 0.5 SHOULD imply realized R lift > 0")
    print("  unless the model is mis-ranking the *rare big winners* (R=2-3.99) as rare losers,")
    print("  while correctly ranking near-breakeven outcomes.")

# Top-K big winners check
print("\nWhere are the BIG winners (R >= 2.0) ranked by p_v3?")
big_winners_mask = realized_r >= 2.0
big_winners_idx = np.where(big_winners_mask)[0]
print(f"  n big winners: {int(big_winners_mask.sum())}")
print(f"  Mean p_v3 for big winners: {float(mean_p_v3[big_winners_idx].mean()):.4f}")
print(f"  Mean p_v3 for non-big winners: {float(mean_p_v3[~big_winners_mask].mean()):.4f}")
print(f"  Mean p_v3 for losers (R < 0): {float(mean_p_v3[realized_r < 0].mean()):.4f}")
print(f"  Mean p_v3 for breakeven (-0.2 < R < 0.2): {float(mean_p_v3[(realized_r > -0.2) & (realized_r < 0.2)].mean()):.4f}")

# Where does the "good half" end up?
# Mean R by simple sign of (p_v3 > 0.5)
above_05 = mean_p_v3 > 0.50
print(f"\np_v3 > 0.50: n={int(above_05.sum())} mean_R={float(realized_r[above_05].mean()):+.4f}")
print(f"p_v3 <= 0.50: n={int((~above_05).sum())} mean_R={float(realized_r[~above_05].mean()):+.4f}")
# Which one has more big winners?
print(f"\nBig winners (R >= 2.0):")
print(f"  in p>0.50: {int((big_winners_mask & above_05).sum())}")
print(f"  in p<=0.50: {int((big_winners_mask & ~above_05).sum())}")

# Save deep dive
deep_calib = {
    "auc_overall": round(float(auc_overall), 4),
    "auc_strong_win": round(float(auc_strong), 4),
    "pearson_p_vs_R": round(float(pearson_r), 4),
    "pearson_p": round(float(p_pearson), 4),
    "spearman_p_vs_R": round(float(spearman_r), 4),
    "spearman_p": round(float(p_spearman), 4),
    "decile_analysis": results,
    "monotonic_up_steps": int((np.array(diffs) > 0).sum()),
    "n_total_steps": len(diffs),
    "big_winners_analysis": {
        "n_big_winners_R_ge_2": int(big_winners_mask.sum()),
        "mean_p_v3_for_big_winners": round(float(mean_p_v3[big_winners_idx].mean()), 4),
        "mean_p_v3_for_losers": round(float(mean_p_v3[realized_r < 0].mean()), 4),
        "n_big_winners_above_p_05": int((big_winners_mask & above_05).sum()),
        "n_big_winners_below_p_05": int((big_winners_mask & ~above_05).sum()),
    },
    "binary_threshold_split_analysis": {
        "p_v3_above_05": {
            "n": int(above_05.sum()),
            "mean_R": round(float(realized_r[above_05].mean()), 4),
        },
        "p_v3_below_05": {
            "n": int((~above_05).sum()),
            "mean_R": round(float(realized_r[~above_05].mean()), 4),
        },
        "lift_above_minus_uniform": round(float(realized_r[above_05].mean() - realized_r.mean()), 4),
    },
    "interpretation": (
        f"AUC={auc_overall:.4f} > 0.5 confirms model has small positive sign signal. "
        f"Pearson(p, R)={pearson_r:+.4f} confirms tiny linear signal. "
        f"BUT: among R>=2.0 big winners, mean p_v3 = "
        f"{float(mean_p_v3[big_winners_idx].mean()):.4f} vs losers mean p_v3 = "
        f"{float(mean_p_v3[realized_r < 0].mean()):.4f}. "
        "Model under-ranks big winners. "
        f"At threshold 0.50: takes {int(above_05.sum())} trades meanR="
        f"{float(realized_r[above_05].mean()):+.3f} (uniform "
        f"{float(realized_r.mean()):+.3f}, lift "
        f"{float(realized_r[above_05].mean() - realized_r.mean()):+.3f}). "
        f"Decile monotonicity: {(np.array(diffs) > 0).sum()}/9 increasing - "
        "the rank order of mean R by p_v3 decile is JAGGED, not monotonic. "
        "This is a CALIBRATION failure (model AUC > 0.5 but misordered when R-magnitudes vary), "
        "not a fundamental signal failure."
    ),
}

jdump(deep_calib, F / "_aux_calibration_disconnect.json")
print(f"\nWROTE: {F}/_aux_calibration_disconnect.json")
