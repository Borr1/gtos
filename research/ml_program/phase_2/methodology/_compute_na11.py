"""NA-11 — Pairwise alpha correlation audit + corrected portfolio Sharpe math.

Author:  Forensic Agent NA-11 (Phase 4, Opus 4.7 / max effort).
Date:    2026-04-29.
Mandate: Validate Agent J's asserted rho_bar = 0.10 against EMPIRICAL pairwise
         correlations across 5 alphas, then re-run Sharpe-target math.

ALPHAS (5):
   1. J46-J49 portfolio policy  -> per-trade R (realized_r post-policy)
   2. S79 risk policy           -> per-trade sizing series (uniform 2.0% in shipped FN profile)
   3. Mechanical OB (2022-2023) -> per-trade indicator and within-cohort R-when-fired
   4. K54 v3 top-3% confidence  -> per-trade indicator (top 3% by mean_p_v3)
   5. AI baseline ~63% WR       -> per-trade win/loss indicator from AI source

DATA SOURCE:  research/ml_program/scout/feature_matrix.parquet  (n=528, 2024-04-01 -> 2026-04-24)
              research/ml_program/models/k54_v3/cpcv_paired_results.json (CPCV path predictions)

OUTPUTS:
   - na11_correlation_matrix.csv  (5x5 Pearson + Spearman + Kendall variants)
   - na11_portfolio_sharpe_corrected.json  (corrected N-edges-to-target table)
   - na11_alpha_correlation_audit.md  (synthesis, written by parent agent)

Read-only over production. No code path imports src/ or modifies any other file.
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[3].parents[0]  # ai-trading-agent/
SCOUT = ROOT / "research/ml_program/scout/feature_matrix.parquet"
CPCV  = ROOT / "research/ml_program/models/k54_v3/cpcv_paired_results.json"
OUT   = ROOT / "research/ml_program/phase_2/methodology"


# ---------------------------------------------------------------- helpers

def safe_corr(method, x, y):
    """Return (statistic, p) handling NaNs and degenerate inputs."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 5:
        return (float("nan"), float("nan"), int(mask.sum()))
    if np.std(x[mask]) == 0 or np.std(y[mask]) == 0:
        return (float("nan"), float("nan"), int(mask.sum()))
    if method == "pearson":
        r, p = stats.pearsonr(x[mask], y[mask])
    elif method == "spearman":
        r, p = stats.spearmanr(x[mask], y[mask])
    elif method == "kendall":
        r, p = stats.kendalltau(x[mask], y[mask])
    else:
        raise ValueError(method)
    return float(r), float(p), int(mask.sum())


def cohort_indicator(s, kind):
    """Build per-trade indicator series from source label."""
    if kind == "mechanical":
        return (s == "f11_mechanical").astype(int).to_numpy()
    if kind == "ai":
        return s.isin(["trade_index", "unified_csv"]).astype(int).to_numpy()
    raise ValueError(kind)


def sharpe_portfolio(s, N, rho):
    """Equal-weight aggregation Sharpe formula."""
    return s * math.sqrt(N) / math.sqrt(1.0 + (N - 1) * rho)


# ---------------------------------------------------------------- load cohort

print("[NA-11] Loading n=528 K54 v3 cohort.")
df = pd.read_parquet(SCOUT)
n = len(df)
assert n == 528, f"expected 528 rows, got {n}"

realized_r = df["__realized_r"].to_numpy()
win_label  = df["__win_label"].to_numpy()
source     = df["__source"].to_numpy()
direction  = df["__direction"].to_numpy()
symbol     = df["__symbol"].to_numpy()


# ---------------------------------------------------------------- reconstruct K54 v3 mean_p_v3

print("[NA-11] Reconstructing K54 v3 mean_p_v3 from CPCV paths.")
cpcv = json.loads(CPCV.read_text())
sum_p_v3 = np.zeros(n)
count = np.zeros(n, dtype=int)
for path in cpcv["paths"]:
    for i, idx in enumerate(path["test_idx"]):
        sum_p_v3[idx] += path["p_v3_te"][i]
        count[idx] += 1
mean_p_v3 = np.divide(sum_p_v3, count, out=np.full(n, np.nan), where=count > 0)
n_with_pred = int(np.sum(count > 0))
print(f"  -> n with at least one CPCV prediction: {n_with_pred}/{n}")


# ---------------------------------------------------------------- build 5 alpha series

# Alpha 1 — J46-J49 portfolio policy: per-trade R (realized_r is the R-under-cohort-policy)
alpha1_r = realized_r.copy()

# Alpha 2 — S79 risk policy: per-trade sizing.
#   Shipped: uniform_fn 2.0% across all trades in the FN profile cohort.
#   Per-trade sizing series under the SHIPPED policy is a constant 2.0%.
#   For correlation-with-meaning, we project S79 as: sized_R = size_pct * R = 2.0 * R.
#   This makes alpha2 perfectly collinear with alpha1 (rho=1.0 by construction).
#   To respect the spec ("per-trade size series"), we keep the constant series too.
alpha2_size = np.full(n, 2.0)            # shipped uniform_fn 2.0%
alpha2_sized_r = alpha2_size * realized_r  # alpha2 sized R for E[R]-style correlation

# Alpha 3 — Mechanical OB cross-period (2022-2023).
#   The 2022-2023 cohort n=1798 is on a separate dataset (not in feature_matrix.parquet).
#   In-cohort proxy: rows with source='f11_mechanical' (406/528) representing the
#   mechanical OB-retest signal applied to 2026. Indicator AND R-when-fired.
alpha3_mech_indicator = cohort_indicator(df["__source"], "mechanical")
alpha3_mech_R = np.where(alpha3_mech_indicator == 1, realized_r, np.nan)

# Alpha 4 — K54 v3 top-3% confidence indicator.
#   Top-3% by mean_p_v3 = top 16 trades.
top_pct = 0.03
k_top = int(round(n * top_pct))
sorted_idx = np.argsort(-mean_p_v3)
alpha4_top3pct = np.zeros(n, dtype=int)
alpha4_top3pct[sorted_idx[:k_top]] = 1
print(f"  -> K54 v3 top-3% n: {int(alpha4_top3pct.sum())}")

# Alpha 5 — AI baseline ~63% WR.
#   AI source rows (trade_index + unified_csv) = 122/528.
#   Indicator AND win/loss-when-fired.
alpha5_ai_indicator = cohort_indicator(df["__source"], "ai")
alpha5_ai_win = np.where(alpha5_ai_indicator == 1, win_label, np.nan)
ai_n = int(alpha5_ai_indicator.sum())
ai_wins = int(np.nansum(np.where(alpha5_ai_indicator == 1, win_label, 0)))
print(f"  -> AI baseline n={ai_n}, wins={ai_wins}, WR={ai_wins/max(ai_n,1):.4f}")


# ---------------------------------------------------------------- per-trade alpha series for matrix

# For the 5x5 matrix, use the most-comparable per-trade series:
#   alpha1: realized_r (continuous)
#   alpha2: alpha2_sized_r (continuous; functionally identical to alpha1 up to scale)
#   alpha3: alpha3_mech_indicator (binary; trade was mech-OB-source)
#   alpha4: alpha4_top3pct (binary; trade was top-3% K54)
#   alpha5: alpha5_ai_indicator (binary; trade was AI-source)
#
# Pearson on indicator-vs-R measures point-biserial correlation (E[R | A=1] - E[R | A=0])
# scaled by sigmas — this is the right semantic for "does alpha A pick high-R trades?"

ALPHAS = {
    "J46_J49_R":          alpha1_r,
    "S79_sized_R":        alpha2_sized_r,
    "Mech_OB_indicator":  alpha3_mech_indicator.astype(float),
    "K54_v3_top3pct":     alpha4_top3pct.astype(float),
    "AI_indicator":       alpha5_ai_indicator.astype(float),
}
ALPHA_NAMES = list(ALPHAS.keys())


# ---------------------------------------------------------------- 5x5 correlation matrices

print("\n[NA-11] Computing 5x5 correlation matrices (Pearson, Spearman, Kendall).")
methods = ["pearson", "spearman", "kendall"]
matrices = {m: pd.DataFrame(np.nan, index=ALPHA_NAMES, columns=ALPHA_NAMES) for m in methods}
p_matrices = {m: pd.DataFrame(np.nan, index=ALPHA_NAMES, columns=ALPHA_NAMES) for m in methods}

for m in methods:
    for a in ALPHA_NAMES:
        for b in ALPHA_NAMES:
            r, p, n_eff = safe_corr(m, ALPHAS[a], ALPHAS[b])
            matrices[m].loc[a, b] = r
            p_matrices[m].loc[a, b] = p

# Persist the Pearson matrix as the primary 5x5 CSV per spec
mat_p = matrices["pearson"]
mat_p.to_csv(OUT / "na11_correlation_matrix.csv", index=True, float_format="%.6f")
print(f"  WROTE: {OUT}/na11_correlation_matrix.csv")


# ---------------------------------------------------------------- per-pair tail-correlation + co-occurrence + conditional E[R]

print("\n[NA-11] Computing per-pair: tail-correlations + co-occurrence + conditional E[R].")

PAIR_DETAILS = []
for i, a in enumerate(ALPHA_NAMES):
    for j, b in enumerate(ALPHA_NAMES):
        if j <= i:
            continue

        sx, sy = ALPHAS[a], ALPHAS[b]

        # Pearson + Spearman + Kendall
        rp, pp, n_eff = safe_corr("pearson", sx, sy)
        rs, ps, _    = safe_corr("spearman", sx, sy)
        rk, pk, _    = safe_corr("kendall", sx, sy)

        # Tail correlation: Kendall tau on left tail (bottom 25%) and right tail (top 25%)
        x = np.asarray(sx, dtype=float)
        y = np.asarray(sy, dtype=float)
        mask = np.isfinite(x) & np.isfinite(y)
        x_, y_ = x[mask], y[mask]

        # Define tail by alpha A (sx) joint with B
        if np.std(x_) > 0:
            q25_x = np.quantile(x_, 0.25)
            q75_x = np.quantile(x_, 0.75)
            left_mask  = x_ <= q25_x
            right_mask = x_ >= q75_x
            if left_mask.sum() >= 5 and np.std(y_[left_mask]) > 0:
                tau_left, p_left = stats.kendalltau(x_[left_mask], y_[left_mask])
            else:
                tau_left, p_left = float("nan"), float("nan")
            if right_mask.sum() >= 5 and np.std(y_[right_mask]) > 0:
                tau_right, p_right = stats.kendalltau(x_[right_mask], y_[right_mask])
            else:
                tau_right, p_right = float("nan"), float("nan")
        else:
            tau_left = tau_right = p_left = p_right = float("nan")

        # Co-occurrence (only meaningful for binary alphas)
        x_is_binary = set(np.unique(x_).tolist()).issubset({0.0, 1.0})
        y_is_binary = set(np.unique(y_).tolist()).issubset({0.0, 1.0})
        co_occ = None
        n_a_signal = n_b_signal = n_both = None
        if x_is_binary and y_is_binary:
            n_a_signal = int(np.sum(x_ == 1))
            n_b_signal = int(np.sum(y_ == 1))
            n_both     = int(np.sum((x_ == 1) & (y_ == 1)))
            # P(B signals | A signals)
            p_b_given_a = n_both / max(n_a_signal, 1)
            p_a_given_b = n_both / max(n_b_signal, 1)
            # Phi coefficient = Pearson on binary-binary
            co_occ = {
                "n_A_signals": n_a_signal,
                "n_B_signals": n_b_signal,
                "n_both_signal": n_both,
                "P_B_given_A": round(p_b_given_a, 4),
                "P_A_given_B": round(p_a_given_b, 4),
                "phi_pearson": round(rp, 4),
            }

        # Conditional E[R | both signal] vs E[R | only A signals]
        cond_R = None
        if x_is_binary and y_is_binary:
            both = (x_ == 1) & (y_ == 1)
            only_a = (x_ == 1) & (y_ == 0)
            only_b = (x_ == 0) & (y_ == 1)
            neither = (x_ == 0) & (y_ == 0)
            r_both   = realized_r[mask][both]
            r_only_a = realized_r[mask][only_a]
            r_only_b = realized_r[mask][only_b]
            r_neither = realized_r[mask][neither]
            cond_R = {
                "E_R_both":     round(float(np.mean(r_both)),     4) if len(r_both)   else None,
                "n_both":       int(len(r_both)),
                "E_R_only_A":   round(float(np.mean(r_only_a)),   4) if len(r_only_a) else None,
                "n_only_A":     int(len(r_only_a)),
                "E_R_only_B":   round(float(np.mean(r_only_b)),   4) if len(r_only_b) else None,
                "n_only_B":     int(len(r_only_b)),
                "E_R_neither":  round(float(np.mean(r_neither)),  4) if len(r_neither) else None,
                "n_neither":    int(len(r_neither)),
            }
        # For binary x continuous: point-biserial -> compare E[R | A=1] vs E[R | A=0]
        elif x_is_binary and not y_is_binary:
            mask_signal = (x_ == 1)
            cond_R = {
                "E_R_y_given_A":     round(float(np.mean(y_[mask_signal])),  4) if mask_signal.sum() else None,
                "n_A_signal":        int(mask_signal.sum()),
                "E_R_y_given_not_A": round(float(np.mean(y_[~mask_signal])), 4) if (~mask_signal).sum() else None,
                "n_A_no_signal":     int((~mask_signal).sum()),
                "delta":             None,
            }
            if cond_R["E_R_y_given_A"] is not None and cond_R["E_R_y_given_not_A"] is not None:
                cond_R["delta"] = round(cond_R["E_R_y_given_A"] - cond_R["E_R_y_given_not_A"], 4)
        elif not x_is_binary and y_is_binary:
            mask_signal = (y_ == 1)
            cond_R = {
                "E_R_x_given_B":     round(float(np.mean(x_[mask_signal])),  4) if mask_signal.sum() else None,
                "n_B_signal":        int(mask_signal.sum()),
                "E_R_x_given_not_B": round(float(np.mean(x_[~mask_signal])), 4) if (~mask_signal).sum() else None,
                "n_B_no_signal":     int((~mask_signal).sum()),
                "delta":             None,
            }
            if cond_R["E_R_x_given_B"] is not None and cond_R["E_R_x_given_not_B"] is not None:
                cond_R["delta"] = round(cond_R["E_R_x_given_B"] - cond_R["E_R_x_given_not_B"], 4)

        PAIR_DETAILS.append({
            "pair": f"{a} ~ {b}",
            "n_eff": n_eff,
            "pearson_r": round(rp, 4),
            "pearson_p": round(pp, 4),
            "spearman_rho": round(rs, 4),
            "spearman_p": round(ps, 4),
            "kendall_tau": round(rk, 4),
            "kendall_p": round(pk, 4),
            "tau_left_tail":  round(tau_left, 4) if not math.isnan(tau_left) else None,
            "tau_right_tail": round(tau_right, 4) if not math.isnan(tau_right) else None,
            "co_occurrence":  co_occ,
            "conditional_R":  cond_R,
        })


# ---------------------------------------------------------------- summary correlation statistics

# Off-diagonal mean for rho_bar estimate. Take Pearson (most comparable to Agent J's spec).
mat_pearson = matrices["pearson"]
n_alpha = len(ALPHA_NAMES)
off_diag_mask = ~np.eye(n_alpha, dtype=bool)
off_diag_pearson = mat_pearson.values[off_diag_mask]
off_diag_pearson_clean = off_diag_pearson[np.isfinite(off_diag_pearson)]
rho_bar_pearson = float(np.mean(off_diag_pearson_clean))
rho_bar_pearson_abs = float(np.mean(np.abs(off_diag_pearson_clean)))

mat_spearman = matrices["spearman"]
off_diag_spearman = mat_spearman.values[off_diag_mask]
off_diag_spearman_clean = off_diag_spearman[np.isfinite(off_diag_spearman)]
rho_bar_spearman = float(np.mean(off_diag_spearman_clean))

# Drop two degenerate pairs from rho_bar:
# (1) J46_J49_R / S79_sized_R: collinear by construction (S79 = 2.0 * R under shipped uniform_fn 2.0%).
# (2) Mech_OB_indicator / AI_indicator: PARTITION artifact — every trade in the cohort is
#     EITHER AI-evaluated OR mechanical-OB-source (disjoint partition; n_both=0). This produces
#     phi = -1.0 by construction, NOT a real alpha correlation. In the LIVE system, both
#     alphas can fire on the same candle (AI CANDIDATE on a mech-OB-qualifying setup);
#     the disjoint structure is an artifact of how the K54 v3 cohort was assembled
#     (mechanical OB cohort separately from AI-decision cohort).
mask_real_pair = np.ones((n_alpha, n_alpha), dtype=bool)
mask_real_pair &= ~np.eye(n_alpha, dtype=bool)
i_a1 = ALPHA_NAMES.index("J46_J49_R")
i_a2 = ALPHA_NAMES.index("S79_sized_R")
mask_real_pair[i_a1, i_a2] = False
mask_real_pair[i_a2, i_a1] = False
i_mech = ALPHA_NAMES.index("Mech_OB_indicator")
i_ai = ALPHA_NAMES.index("AI_indicator")
mask_real_pair[i_mech, i_ai] = False
mask_real_pair[i_ai, i_mech] = False

real_off_diag = mat_pearson.values[mask_real_pair]
real_off_diag = real_off_diag[np.isfinite(real_off_diag)]
rho_bar_real_pearson = float(np.mean(real_off_diag))
rho_bar_real_pearson_abs = float(np.mean(np.abs(real_off_diag)))

real_off_diag_sp = mat_spearman.values[mask_real_pair]
real_off_diag_sp = real_off_diag_sp[np.isfinite(real_off_diag_sp)]
rho_bar_real_spearman = float(np.mean(real_off_diag_sp))

# Also keep a "with-collinear-only-excluded" variant for transparency (this includes the
# Mech/AI -1.0 partition artifact, exposing how degenerate it is)
mask_excl_collinear_only = np.ones((n_alpha, n_alpha), dtype=bool)
mask_excl_collinear_only &= ~np.eye(n_alpha, dtype=bool)
mask_excl_collinear_only[i_a1, i_a2] = False
mask_excl_collinear_only[i_a2, i_a1] = False
off_diag_excl_coll = mat_pearson.values[mask_excl_collinear_only]
off_diag_excl_coll = off_diag_excl_coll[np.isfinite(off_diag_excl_coll)]
rho_bar_excl_collinear_only = float(np.mean(off_diag_excl_coll))


# ---------------------------------------------------------------- corrected portfolio Sharpe

# Per Agent J: Sharpe_p = s * sqrt(N) / sqrt(1 + (N-1) * rho_bar)
# Asymptotic ceiling: s / sqrt(rho_bar)

# Use real_off_diag rho_bar (exclude the trivially collinear J46_J49 + S79 pair).
empirical_rho_for_projection = rho_bar_real_pearson  # signed (can be negative)
empirical_rho_abs_for_projection = rho_bar_real_pearson_abs

# For Sharpe math we use the ABSOLUTE value: variance reduction depends on |rho| only when
# alphas are equally weighted with arbitrary sign; conventional rho_bar in portfolio
# aggregation is the average pairwise correlation in matrix form. Negative pairwise
# correlations VOID the formula for Var(sum) > 0 unless N is small (matrix must be PSD).
# Use signed rho_bar but cap at machine-zero.
rho_for_math_signed = empirical_rho_for_projection

per_edge_sharpes = [0.30, 0.40, 0.50, 0.60]
N_grid = [3, 5, 8, 12, 16, 20, 30, 45, 81]

# Asymptotic ceiling table at empirical rho
def ceiling(s, rho):
    rho_eff = max(rho, 1e-9)  # guard against div-by-zero
    return s / math.sqrt(rho_eff)

asymptotic_ceilings = {
    f"per_edge_s={s:.2f}": {
        "rho_signed": round(rho_for_math_signed, 4),
        "rho_abs":    round(empirical_rho_abs_for_projection, 4),
        "ceiling_at_signed_rho": round(ceiling(s, max(rho_for_math_signed, 1e-9)), 3),
        "ceiling_at_abs_rho":    round(ceiling(s, empirical_rho_abs_for_projection), 3),
    } for s in per_edge_sharpes
}

# Finite-N projection at empirical rho. If signed rho < 0, the formula gives larger Sharpe
# than at rho=0 (variance is reduced below independent case). Report both.
finite_N_table = {}
rho_options = {
    "empirical_signed":  rho_for_math_signed,
    "empirical_absolute": empirical_rho_abs_for_projection,
    "asserted_J_rho_010": 0.10,
}
for name, rho in rho_options.items():
    rho_eff = max(rho, 1e-9)
    table = {}
    for s in per_edge_sharpes:
        rows = {}
        for N in N_grid:
            rows[f"N={N}"] = round(sharpe_portfolio(s, N, rho_eff), 3)
        rows["N=infinity"] = round(s / math.sqrt(rho_eff), 3)
        table[f"per_edge_s={s:.2f}"] = rows
    finite_N_table[f"rho={name}={rho:.4f}"] = table

# N-required table: minimum N to reach Sharpe target T at given (s, rho).
def min_N_for_target(s, rho, target):
    """Solve s * sqrt(N) / sqrt(1 + (N-1)*rho) >= target for N."""
    # if target > s/sqrt(rho), unreachable
    rho_eff = max(rho, 1e-9)
    if target > s / math.sqrt(rho_eff) - 1e-6:
        return None  # unreachable
    # closed-form: N = (target/s)^2 * (1 - rho) / (1 - (target/s)^2 * rho)
    t_over_s_sq = (target / s) ** 2
    denom = 1.0 - t_over_s_sq * rho_eff
    if denom <= 0:
        return None
    N = t_over_s_sq * (1.0 - rho_eff) / denom
    return int(math.ceil(N))

target_table = {}
for tgt in [1.0, 1.5]:
    target_table[f"target_Sharpe={tgt}"] = {}
    for name, rho in rho_options.items():
        target_table[f"target_Sharpe={tgt}"][f"rho={name}={rho:.4f}"] = {}
        for s in per_edge_sharpes:
            N_req = min_N_for_target(s, rho, tgt)
            target_table[f"target_Sharpe={tgt}"][f"rho={name}={rho:.4f}"][f"per_edge_s={s:.2f}"] = (
                "UNREACHABLE" if N_req is None else N_req
            )


# ---------------------------------------------------------------- write outputs

print("\n[NA-11] Writing outputs.")

corrected_payload = {
    "audit_id": "NA-11_alpha_correlation_audit",
    "audit_date": "2026-04-29",
    "model": "claude-opus-4-7-1m",
    "effort": "max",
    "subscription_only": True,
    "agent_j_asserted_rho_bar": 0.10,
    "data_source": {
        "scout_parquet":   str(SCOUT.relative_to(ROOT)),
        "cpcv_paths":      str(CPCV.relative_to(ROOT)),
        "cohort_n":        int(n),
        "date_range":      ["2024-04-01", "2026-04-24"],
    },
    "alpha_definitions": {
        "J46_J49_R":         "per-trade R under the shipped J46-J49 portfolio policy "
                              "(realized_r in feature_matrix.parquet — already J46-J49-encoded)",
        "S79_sized_R":       "per-trade sized-R under shipped S79 uniform_fn 2.0% policy "
                              "(2.0 * realized_r — collinear with J46_J49_R by construction)",
        "Mech_OB_indicator": "per-trade indicator: source == 'f11_mechanical' "
                              "(in-cohort proxy for the cross-period 2022-2023 mechanical OB signal)",
        "K54_v3_top3pct":    "per-trade indicator: trade in top-3% by mean_p_v3 (n=16/528)",
        "AI_indicator":      "per-trade indicator: source in {'trade_index','unified_csv'} "
                              "(AI-CANDIDATE-decision provenance, n=122/528)",
    },
    "n_alpha_signals": {
        "K54_v3_top3pct_n": int(alpha4_top3pct.sum()),
        "Mech_OB_n":        int(alpha3_mech_indicator.sum()),
        "AI_indicator_n":   int(alpha5_ai_indicator.sum()),
        "AI_baseline_WR":   round(ai_wins / max(ai_n, 1), 4),
    },
    "matrices": {
        "pearson":  matrices["pearson"].round(4).to_dict(),
        "spearman": matrices["spearman"].round(4).to_dict(),
        "kendall":  matrices["kendall"].round(4).to_dict(),
        "p_pearson":  p_matrices["pearson"].round(4).to_dict(),
        "p_spearman": p_matrices["spearman"].round(4).to_dict(),
        "p_kendall":  p_matrices["kendall"].round(4).to_dict(),
    },
    "rho_bar_estimates": {
        "_definition": (
            "Excluded from real-pair rho_bar: (a) J46_J49_R / S79_sized_R collinear pair (S79 = "
            "2.0 * R under shipped uniform_fn 2.0%, rho=1.0 by construction). (b) Mech_OB_indicator "
            "/ AI_indicator partition artifact (mutually exclusive sources in the K54 v3 cohort, "
            "rho=-1.0 by construction; not a real alpha correlation in the LIVE system)."
        ),
        "pearson_signed_with_all_pairs":            round(rho_bar_pearson, 4),
        "pearson_abs_with_all_pairs":               round(rho_bar_pearson_abs, 4),
        "spearman_signed_with_all_pairs":           round(rho_bar_spearman, 4),
        "pearson_signed_excl_collinear_only":       round(rho_bar_excl_collinear_only, 4),
        "pearson_signed_excl_collinear_and_partition_AUTHORITATIVE":  round(rho_bar_real_pearson, 4),
        "pearson_abs_excl_collinear_and_partition_AUTHORITATIVE":     round(rho_bar_real_pearson_abs, 4),
        "spearman_signed_excl_collinear_and_partition_AUTHORITATIVE": round(rho_bar_real_spearman, 4),
        "agent_j_asserted":                          0.10,
        "delta_vs_asserted_signed_AUTHORITATIVE":    round(rho_bar_real_pearson - 0.10, 4),
        "delta_vs_asserted_abs_AUTHORITATIVE":       round(rho_bar_real_pearson_abs - 0.10, 4),
    },
    "per_pair_details": PAIR_DETAILS,
    "asymptotic_ceiling_table_at_empirical_rho": asymptotic_ceilings,
    "finite_N_projection_corrected": finite_N_table,
    "min_N_for_target_Sharpe": target_table,
    "interpretation": {
        "headline_rho_bar_signed": (
            f"Empirical rho_bar (signed, excluding S79=2*J46_J49 collinear pair) = "
            f"{rho_bar_real_pearson:+.4f}, vs Agent J's asserted +0.10. "
            f"Delta = {rho_bar_real_pearson - 0.10:+.4f}."
        ),
        "headline_rho_bar_abs": (
            f"Empirical rho_bar (absolute, excluding collinear pair) = "
            f"{rho_bar_real_pearson_abs:.4f}, vs Agent J's asserted 0.10. "
            f"Delta = {rho_bar_real_pearson_abs - 0.10:+.4f}."
        ),
        "sharpe_implication": (
            "If signed rho_bar < 0.10, achievable Sharpe ceiling RISES; aggregation is more "
            "favorable than Agent J's projection. If absolute rho_bar > 0.10, the worst-case "
            "ceiling is LOWER. Use absolute rho_bar for conservative planning, signed rho_bar "
            "for nominal expectations."
        ),
        "collinear_pair_warning": (
            "J46_J49_R and S79_sized_R are functionally identical up to a 2.0x scale factor "
            "in the SHIPPED FN profile. Their pair is rho=1.0 by construction and is excluded "
            "from rho_bar computation to avoid biasing the average upward."
        ),
    },
    "caveats": [
        "Mech_OB_indicator is an in-cohort proxy (source=='f11_mechanical' within the n=528). "
        "The original 2022-2023 cohort n=1798 lives outside feature_matrix.parquet; only v1-schema "
        "cross-period AUC is computed in research/ml_program/models/k54_v3/cross_period_results.json.",
        "Indicator-vs-continuous correlations are point-biserial (Pearson on binary x continuous = "
        "scaled (E[R|A=1] - E[R|A=0]) / sigma_R). Spearman handles ties differently; we report all "
        "three for triangulation.",
        "Tail-correlation uses Kendall tau on top/bottom 25% by alpha A. Where one of the alphas is "
        "binary-only inside the tail, tau is degenerate (ties); we report NaN in that case.",
        "rho_bar excluding the J46_J49/S79 collinear pair AND the Mech/AI partition pair is the "
        "right input for portfolio-aggregation Sharpe math. The collinear pair represents one "
        "alpha (sized-R) reported twice; the partition pair represents the K54 v3 cohort assembly "
        "convention (disjoint AI-cohort and mech-cohort) — in LIVE the two alphas can fire on the "
        "same candle and the relevant rho is unmeasurable from this dataset.",
        "If shipped policy ever changes from uniform_fn 2.0% to a non-trivial S79 variant "
        "(sharpe-weighted, side-aware, regime-conditioned), the J46/S79 collinearity is broken "
        "and the pair becomes a real correlation to measure.",
        "Sample size n=528 means each pair's Pearson SE is ~1/sqrt(528) ~ 0.044. Signed rho_bar "
        "estimate uncertainty is ~+/-0.02 across 7 real pairs.",
        "Sharpe-target reachability assumes per-edge Sharpe is annualized AND that all alphas "
        "fire on the same trade frequency. In practice, J46-J49 fires only on filled trades; "
        "K54 v3 top-3% fires on ~16/528 = 3% of evaluations; AI baseline fires on ~10% of "
        "evaluations (per CR ~10.3%). The aggregation formula assumes equal-weight which "
        "breaks down when alphas have heterogeneous fire rates.",
    ],
    "files_written": [
        "research/ml_program/phase_2/methodology/na11_correlation_matrix.csv",
        "research/ml_program/phase_2/methodology/na11_portfolio_sharpe_corrected.json",
        "research/ml_program/phase_2/methodology/_compute_na11.py",
        "research/ml_program/phase_2/methodology/na11_alpha_correlation_audit.md",
    ],
}

(OUT / "na11_portfolio_sharpe_corrected.json").write_text(
    json.dumps(corrected_payload, indent=2, default=lambda x: float(x) if hasattr(x, "item") else str(x))
)

print(f"  WROTE: {OUT}/na11_portfolio_sharpe_corrected.json")

# Print headline to stdout for the synthesis
print("\n" + "=" * 60)
print("NA-11 HEADLINE")
print("=" * 60)
print(f"Empirical rho_bar (signed, real pairs, exclude collinear+partition) = {rho_bar_real_pearson:+.4f}")
print(f"Empirical rho_bar (abs,    real pairs, exclude collinear+partition) = {rho_bar_real_pearson_abs:.4f}")
print(f"Empirical rho_bar (signed, all 10 pairs, naive)                     = {rho_bar_pearson:+.4f}")
print(f"Empirical rho_bar (signed, exclude only J46/S79 collinear)          = {rho_bar_excl_collinear_only:+.4f}")
print(f"Agent J asserted rho_bar                                            = 0.1000")
print()
print("Real off-diagonal Pearson correlations (excluding collinear AND partition):")
for i, a in enumerate(ALPHA_NAMES):
    for j, b in enumerate(ALPHA_NAMES):
        if j <= i:
            continue
        if not mask_real_pair[i, j]:
            continue
        r = mat_pearson.loc[a, b]
        print(f"  {a:20s} ~ {b:20s}  pearson = {r:+.4f}")
print()
print("Min-N for Sharpe target at empirical SIGNED rho:")
for tgt in [1.0, 1.5]:
    print(f"  Target Sharpe = {tgt}:")
    for s in per_edge_sharpes:
        N = min_N_for_target(s, rho_for_math_signed, tgt)
        print(f"    s={s:.2f}: N = {'UNREACHABLE' if N is None else N}")
print()
print("Min-N for Sharpe target at empirical ABSOLUTE rho:")
for tgt in [1.0, 1.5]:
    print(f"  Target Sharpe = {tgt}:")
    for s in per_edge_sharpes:
        N = min_N_for_target(s, empirical_rho_abs_for_projection, tgt)
        print(f"    s={s:.2f}: N = {'UNREACHABLE' if N is None else N}")
print()
print("Files written:")
for f in corrected_payload["files_written"]:
    print(f"  - {f}")
