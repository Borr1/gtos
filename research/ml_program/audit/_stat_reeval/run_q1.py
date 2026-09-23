"""Q1 — Politis-Romano stationary block bootstrap on per-path AUC diffs.

Two views:
  (a) Stationary block bootstrap with avg block size L=5 (as requested).
  (b) CPCV-correlation-aware SE via empirical path-pair-shared-train fraction
      as a proxy for path correlation (informational; supplements PR bootstrap).
"""
import json, os, sys
import numpy as np
from itertools import combinations

np.random.seed(42)

CPCV_JSON = r"C:/Users/MSI/Documents/ai-trading-agent/research/ml_program/models/k54_v2/cpcv_paired_results.json"
OUT_JSON = r"C:/Users/MSI/Documents/ai-trading-agent/research/ml_program/audit/_stat_reeval/q1_bootstrap.json"

d = json.load(open(CPCV_JSON))
paths = d["paths_fixed_hp"]
diffs = np.array([p["auc_diff"] for p in paths])
delong_ps = np.array([p["delong_p"] for p in paths])
n = len(diffs)

# ---- (a) Politis-Romano stationary bootstrap ----
B = 1000
L = 5
p_jump = 1.0 / L

boot_means = np.zeros(B)
for b in range(B):
    out = np.empty(n, dtype=float)
    i = np.random.randint(0, n)
    for t in range(n):
        out[t] = diffs[i]
        if np.random.random() < p_jump:
            i = np.random.randint(0, n)
        else:
            i = (i + 1) % n
    boot_means[b] = out.mean()

mean_boot = boot_means.mean()
se_boot = boot_means.std(ddof=1)
ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])

obs_mean = diffs.mean()
null_distrib = boot_means - obs_mean
p_onesided = float(np.mean(null_distrib >= obs_mean))
p_twosided = float(2 * min(p_onesided, 1 - p_onesided))

# ---- (b) CPCV-honest SE via path-pair training-set overlap proxy ----
# Each path's test set = 2 of 6 folds; train set = the other 4.
# Two paths share 2 train folds if they share 2 test folds (impossible for
# distinct paths: each pair of paths has different test combos), or share
# 3 train folds if they share 1 test fold, or share 4 train folds if they
# share 0 test folds (impossible at K=6,N=2 without overlap).
# At K=6, N=2: any two paths' test combos either share 0, 1, or 2 elements;
# share 2 means same path; share 1 means 3 train folds in common; share 0
# means 4 train folds in common.
# Train-fold overlap fraction relative to 4 train folds:
#   share 1 test fold => 3/4 train overlap
#   share 0 test folds => 4/4 train overlap (full overlap! both train on same 4 folds)
# Actually rethink: K=6, N=2. Path A test = {a,b}; train = K\{a,b} (4 folds).
# Path B test = {c,d}. If {a,b}∩{c,d} = empty, train_A = K\{a,b} (4 folds: c,d,e,f),
# train_B = K\{c,d} (4 folds: a,b,e,f). Train_A ∩ Train_B = {e,f} = 2 folds.
# So share 0 test folds => 2/4 train overlap.
# If {a,b}∩{c,d}=1 element (say a==c), then train_A = {c,d,e,f} ∩ K\{a,b} =
# K\{a,b} = {c,d,e,f}; train_B = K\{a,d} = {b,c,e,f}. Train_A ∩ Train_B =
# {c,e,f} -> wait that's 3 folds.
# Let me just compute it.

def fold_pair_for_path(p):
    ti = sorted(p["test_idx"])
    counts = {f: 0 for f in range(6)}
    for idx in ti:
        f = idx // 88
        counts[f] += 1
    # Two folds with the largest counts
    return tuple(sorted([f for f, c in sorted(counts.items(), key=lambda x: -x[1])[:2]]))

path_test_folds = [fold_pair_for_path(p) for p in paths]

# Train fold overlap matrix (15 x 15), fraction of train folds shared
train_overlap = np.zeros((n, n))
for i in range(n):
    train_i = set(range(6)) - set(path_test_folds[i])
    for j in range(n):
        train_j = set(range(6)) - set(path_test_folds[j])
        train_overlap[i, j] = len(train_i & train_j) / 4.0  # /4 train folds

# Test fold overlap matrix
test_overlap = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        test_overlap[i, j] = len(set(path_test_folds[i]) & set(path_test_folds[j])) / 2.0

# Treat correlation between path diffs as proportional to training-overlap
# (heuristic; not exact, but a transparent proxy).
# Effective sample size: n_eff = sum(weights) where weights account for
# correlation. With equal off-diagonal correlation rho, var(mean) = var/n * (1 + (n-1)*rho).
# We compute average off-diagonal training overlap as proxy for rho:
off_diag_train = train_overlap[np.triu_indices(n, k=1)]
rho_proxy = float(off_diag_train.mean())  # avg off-diag train-fold overlap fraction
# Inflated SE under uniform rho assumption
var_corrected = (diffs.var(ddof=1) / n) * (1 + (n - 1) * rho_proxy)
se_corrected = float(np.sqrt(var_corrected))

# Save
out = {
    "method": "Politis-Romano stationary bootstrap (15 paths, B=1000, avg block L=5)",
    "B": B,
    "block_size_avg_L": L,
    "p_jump": p_jump,
    "n_paths": n,
    "naive_mean": float(obs_mean),
    "naive_se_iid": float(diffs.std(ddof=1) / np.sqrt(n)),
    "stouffer_combined_p_reported": 0.0015461310581298404,
    "boot_mean": float(mean_boot),
    "boot_se": float(se_boot),
    "boot_ci_95_pct": [float(ci_lo), float(ci_hi)],
    "p_onesided_h1_mean_gt_0_pr_bootstrap": p_onesided,
    "p_twosided_pr_bootstrap": p_twosided,
    "supplement_cpcv_honest": {
        "rationale": (
            "PR stationary bootstrap on a 15-element vector reduces SE because the "
            "block structure causes ties when sampled blocks repeat (variance-reducing "
            "under positive serial dep). True CPCV path correlation is structural "
            "(shared train folds) rather than serial. Proxy: SE inflation factor = "
            "sqrt(1 + (n-1)*rho_proxy) where rho_proxy = mean off-diagonal training-fold-"
            "overlap fraction across the 15 paths."
        ),
        "rho_proxy_train_overlap_mean": rho_proxy,
        "se_iid": float(diffs.std(ddof=1) / np.sqrt(n)),
        "se_cpcv_honest_proxy": se_corrected,
        "ci_95_cpcv_honest_proxy": [
            float(obs_mean - 1.96 * se_corrected),
            float(obs_mean + 1.96 * se_corrected),
        ],
        "t_cpcv_honest": float(obs_mean / se_corrected),
        "p_twosided_cpcv_honest_normal": float(2 * (1 - 0.5 * (1 + np.tanh((obs_mean / se_corrected) / np.sqrt(2))))),
    },
    "random_seed": 42,
}
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)

print(f"Naive mean: {obs_mean:+.6f}")
print(f"Naive SE (iid): {diffs.std(ddof=1)/np.sqrt(n):.6f}")
print(f"Stouffer combined p (reported): 0.001546")
print()
print(f"PR stationary bootstrap (B={B}, L={L}):")
print(f"  mean: {mean_boot:+.6f}")
print(f"  SE: {se_boot:.6f}")
print(f"  95% CI: [{ci_lo:+.6f}, {ci_hi:+.6f}]")
print(f"  one-sided p (mean > 0): {p_onesided:.4f}")
print(f"  two-sided p: {p_twosided:.4f}")
print()
print(f"CPCV-honest proxy (mean train-overlap rho={rho_proxy:.4f}):")
print(f"  SE: {se_corrected:.6f}")
print(f"  95% CI: [{obs_mean-1.96*se_corrected:+.6f}, {obs_mean+1.96*se_corrected:+.6f}]")
print(f"  t-stat: {obs_mean/se_corrected:.3f}")
print()
print(f"OUT: {OUT_JSON}")
