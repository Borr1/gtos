"""
GARCH-EVT Regime Analysis of Trade Outcomes (Q-5.1)
====================================================

Question: Does the volatility regime at trade entry predict trade outcome?
If trades entered during high-volatility states have systematically worse
outcomes, that is an actionable entry filter.

Methodology:
1. Load GARCH(1,1) parameters from existing distributional characterization
2. Compute conditional variance series σ²_t for each instrument via GARCH recursion
3. Classify trade entries by GARCH volatility quartile and Markov regime state
4. Test: WR by quartile, logistic regression, MAE analysis
5. Tail analysis: ξ of standardized residuals vs raw returns
6. Filter simulation: would removing Q4 entries improve expectancy?

Data sources:
- GARCH params: research/diagnostics/distributional_characterization_20260411_012816.json
- Markov 2-state params: research/diagnostics/nonlinear_structure/nonlinear_results_20260411_030330.json
- H1 OHLCV: data/historical/{SYMBOL}_H1.csv
- Trade data: knowledge_base_backtest/sessions/*.json (XAUUSD AI trades)
             knowledge_base_backtest/mechanical_backtest_results.json (all instruments)

Constraints:
- seed=42 for all randomization
- Output to research/diagnostics/garch_regime_analysis/
- Per-instrument analysis mandatory
- Null result is valid and useful

Author: Claude Code (Sonnet 4.6)
Date: 2026-04-11
Version: v1
"""

import json
import glob
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from scipy.stats import genpareto, fisher_exact, chi2_contingency, mannwhitneyu
import statsmodels.api as sm

warnings.filterwarnings("ignore")
np.random.seed(42)

# ===========================================================================
# PATHS
# ===========================================================================
BASE = Path("/Users/borr/Documents/trading/gold-agent")
DIAG_JSON = BASE / "research/diagnostics/distributional_characterization_20260411_012816.json"
NONLIN_JSON = BASE / "research/diagnostics/nonlinear_structure/nonlinear_results_20260411_030330.json"
HIST_DIR = BASE / "data/historical"
SESSION_DIR = BASE / "knowledge_base_backtest/sessions"
MECH_RESULTS = BASE / "mechanical_backtest_results.json"
OUT_DIR = BASE / "research/diagnostics/garch_regime_analysis"
OUT_DIR.mkdir(exist_ok=True)

# Bonferroni correction: count tests upfront
# Per instrument: quartile WR test (3 pairwise), logistic regression
# Combined: logistic regression, filter simulation, 2x2 Fisher
# Estimate ~20 tests total
N_TESTS = 20
ALPHA_BONFERRONI = 0.05 / N_TESTS  # 0.0025

# ===========================================================================
# STEP 0: Load GARCH and regime model parameters
# ===========================================================================
print("=" * 70)
print("STEP 0: Loading GARCH and Markov regime parameters")
print("=" * 70)

with open(DIAG_JSON) as f:
    diag = json.load(f)

with open(NONLIN_JSON) as f:
    nonlin = json.load(f)

INSTRUMENT_MAP = {
    "XAUUSD": "XAUUSD_H1.csv",
    "US30":   "US30_cash_H1.csv",
    "USDJPY": "USDJPY_H1.csv",
    "GBPJPY": "GBPJPY_H1.csv",
    "GBPUSD": "GBPUSD_H1.csv",
}

garch_params = {}
gpd_params = {}
markov_params = {}

for sym in INSTRUMENT_MAP:
    h1_all = diag["instruments"][sym]["H1"]["All"]
    g = h1_all["garch"]["garch11"]
    # NOTE: GARCH was fitted on r_pct = r * 100 (percentage returns) for numerical stability.
    # The stored omega is in units of (pct)² = (100 × decimal_return)².
    # To use in a recursion on decimal log-returns, divide omega by 100² = 10000.
    omega_decimal = g["omega"] / 10000.0
    alpha = g["alpha_arch"]
    beta  = g["beta_garch"]
    persistence = alpha + beta
    garch_params[sym] = {
        "omega": omega_decimal,
        "omega_stored": g["omega"],    # original value for reporting
        "alpha": alpha,
        "beta":  beta,
        "persistence": persistence,
        # Long-run variance: valid only for persistence < 1 (not IGARCH)
        "long_run_var": omega_decimal / (1.0 - persistence)
        if (1.0 - persistence) > 0.001 else None,
    }
    tails = h1_all.get("tails", {})
    gpd_params[sym] = {
        "lower_xi":   tails.get("lower", {}).get("gpd_shape_xi", np.nan),
        "lower_sigma": tails.get("lower", {}).get("gpd_scale_sigma", np.nan),
        "lower_u":    tails.get("lower", {}).get("threshold_u", np.nan),
        "upper_xi":   tails.get("upper", {}).get("gpd_shape_xi", np.nan),
        "upper_sigma": tails.get("upper", {}).get("gpd_scale_sigma", np.nan),
        "upper_u":    tails.get("upper", {}).get("threshold_u", np.nan),
    }
    # Markov 2-state parameters
    c2 = nonlin.get("C2_markov_regime", {}).get(sym, {})
    rp = c2.get("2state", {}).get("regime_params", {})
    if rp:
        markov_params[sym] = {
            "means":     rp["means"],           # [mu_0, mu_1]
            "variances": rp["variances"],        # [var_0, var_1]
            "std_devs":  rp["std_devs"],         # [sigma_0, sigma_1]
            "trans_P":   rp["transition_P"],     # [[P00, P01], [P10, P11]]
            "state_fracs": rp["state_fractions"],# [pi_0, pi_1]
        }
        print(f"{sym}: Markov quiet σ={rp['std_devs'][0]*10000:.2f}bps, "
              f"volatile σ={rp['std_devs'][1]*10000:.2f}bps, "
              f"quiet_freq={rp['state_fractions'][0]*100:.1f}%")
    else:
        markov_params[sym] = None
        print(f"{sym}: Markov 2-state data not available")

print()
print("GARCH parameters (converted to decimal return units):")
for sym, p in garch_params.items():
    print(f"  {sym}: ω(stored)={p['omega_stored']:.4e} ω(dec)={p['omega']:.4e} "
          f"α={p['alpha']:.4f} β={p['beta']:.4f} persistence={p['persistence']:.4f}")


# ===========================================================================
# STEP 1: Compute GARCH conditional variance series for each instrument
# ===========================================================================
print()
print("=" * 70)
print("STEP 1: Computing GARCH conditional variance series")
print("=" * 70)

h1_data = {}      # {sym: DataFrame with time, returns, sigma2, z}
h1_index = {}     # {sym: dict mapping datetime → row index}

for sym, fname in INSTRUMENT_MAP.items():
    fpath = HIST_DIR / fname
    if not fpath.exists():
        print(f"  WARNING: {fname} not found — skipping {sym}")
        continue

    df = pd.read_csv(fpath)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)

    # Log returns
    df["log_ret"] = np.log(df["close"] / df["close"].shift(1))
    df = df.dropna(subset=["log_ret"]).reset_index(drop=True)

    # GARCH(1,1) recursion: σ²_t = ω + α * ε²_{t-1} + β * σ²_{t-1}
    # omega is already converted to decimal units (÷10000 from stored pct² value)
    p = garch_params[sym]
    omega = p["omega"]
    alpha = p["alpha"]
    beta  = p["beta"]
    # Initialization: use empirical variance (robust for near-IGARCH instruments like US30)
    r = df["log_ret"].values
    emp_var = float(np.var(r))
    n = len(df)
    sigma2 = np.full(n, emp_var)   # initialize at empirical variance

    for t in range(1, n):
        sigma2[t] = omega + alpha * r[t-1]**2 + beta * sigma2[t-1]

    df["sigma2"] = sigma2
    df["sigma"]  = np.sqrt(sigma2)
    df["z"]      = r / np.sqrt(sigma2)    # standardized residuals

    # Build lookup: floor H1 time → row
    df["h1_time"] = df["time"].dt.floor("h")
    h1_idx = {}
    for i, row in df.iterrows():
        h1_idx[row["h1_time"]] = i

    h1_data[sym]  = df
    h1_index[sym] = h1_idx

    print(f"  {sym}: {len(df)} bars, median σ_GARCH={np.median(np.sqrt(sigma2))*10000:.2f}bps "
          f"vs empirical σ={np.sqrt(emp_var)*10000:.2f}bps")


# ===========================================================================
# STEP 1b: Markov 2-state smoothed regime probabilities (forward-backward)
# ===========================================================================
print()
print("STEP 1b: Computing Markov smoothed regime probabilities")

def gaussian_emission(r, mu, var):
    """Log-probability of observation r under Gaussian(mu, var)."""
    return -0.5 * np.log(2 * np.pi * var) - 0.5 * (r - mu)**2 / var

def forward_backward(returns, means, variances, trans_P, state_fracs):
    """
    HMM forward-backward algorithm for 2-state model.
    Returns smoothed probabilities P(s_t=k | all data), shape (n, 2).
    Uses log-scale for numerical stability.
    """
    n = len(returns)
    K = 2

    # Log initial probs
    log_pi = np.log(np.array(state_fracs))

    # Log transition matrix (rows: from, cols: to — note: our stored P is [P00, P01; P10, P11])
    # trans_P[i][j] = P(s_t=j | s_{t-1}=i)
    log_A = np.log(np.array(trans_P) + 1e-300)

    # Compute log emission probs
    log_emit = np.zeros((n, K))
    for k in range(K):
        log_emit[:, k] = gaussian_emission(returns, means[k], variances[k])

    # Forward pass (alpha)
    log_alpha = np.zeros((n, K))
    log_alpha[0] = log_pi + log_emit[0]

    for t in range(1, n):
        for k in range(K):
            # log sum_j alpha_{t-1}(j) * A(j, k)
            log_alpha[t, k] = np.logaddexp.reduce(log_alpha[t-1] + log_A[:, k]) + log_emit[t, k]

    # Backward pass (beta)
    log_beta = np.zeros((n, K))
    # log_beta[n-1] = 0 (all ones)

    for t in range(n-2, -1, -1):
        for j in range(K):
            log_beta[t, j] = np.logaddexp.reduce(
                log_A[j, :] + log_emit[t+1, :] + log_beta[t+1, :]
            )

    # Smoothed probabilities
    log_gamma = log_alpha + log_beta
    # Normalize
    log_norm = np.logaddexp(log_gamma[:, 0], log_gamma[:, 1])
    gamma = np.exp(log_gamma - log_norm[:, np.newaxis])

    return gamma  # shape (n, 2); gamma[:, 1] = P(volatile | data)

regime_probs = {}  # {sym: DataFrame with h1_time, p_volatile}

for sym, df in h1_data.items():
    mp = markov_params.get(sym)
    if mp is None:
        print(f"  {sym}: no Markov params — skipping regime probs")
        continue

    r = df["log_ret"].values
    gamma = forward_backward(
        r,
        means=mp["means"],
        variances=mp["variances"],
        trans_P=mp["trans_P"],
        state_fracs=mp["state_fracs"],
    )

    # State 1 = volatile (higher variance) by construction (ordered by variance)
    p_volatile = gamma[:, 1]

    reg_df = pd.DataFrame({
        "h1_time":    df["h1_time"].values,
        "p_volatile": p_volatile,
        "regime":     (p_volatile > 0.5).astype(int),  # 1=volatile
    })
    regime_probs[sym] = reg_df

    n_vol = (reg_df["regime"] == 1).sum()
    print(f"  {sym}: {n_vol}/{len(reg_df)} bars classified volatile "
          f"({n_vol/len(reg_df)*100:.1f}%), "
          f"expected {mp['state_fracs'][1]*100:.1f}%")


# ===========================================================================
# STEP 2: Extract trade data with entry timestamps
# ===========================================================================
print()
print("=" * 70)
print("STEP 2: Extracting trade data with entry timestamps")
print("=" * 70)

def parse_cid_to_datetime(cid):
    """
    Parse cid like '2024-01-25_london_0830' to datetime.
    Returns UTC datetime or None on parse failure.
    """
    try:
        parts = cid.split("_")
        date_str = parts[0]           # YYYY-MM-DD
        time_str = parts[-1]          # HHMM
        hh = int(time_str[:2])
        mm = int(time_str[2:])
        dt = datetime(
            int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10]),
            hh, mm, 0, tzinfo=timezone.utc
        )
        return dt
    except Exception:
        return None

all_trades = []

# -- Source 1: XAUUSD AI session trades --
session_files = sorted(glob.glob(str(SESSION_DIR / "*.json")))
xau_ai_count = 0
for sf in session_files:
    with open(sf) as f:
        d = json.load(f)
    ts = d.get("trade_summary", {})
    trade_list = ts.get("trades", [])
    if not trade_list and ts.get("trade_taken") and ts.get("r_multiple") is not None:
        trade_list = [ts]

    for t in trade_list:
        if t.get("r_multiple") is None or t.get("outcome") is None:
            continue
        # Find entry candle time from evaluations
        entry_time_str = None
        tid = t.get("trade_id")
        for ev in d.get("candle_evaluations", []):
            if ev.get("trade_executed") or (
                ev.get("decision") == "CANDIDATE" and ev.get("trade_id") == tid
            ):
                entry_time_str = ev.get("candle_time")
                break

        if entry_time_str is None:
            continue

        try:
            entry_dt = datetime.fromisoformat(entry_time_str.replace("Z", "+00:00"))
        except Exception:
            continue

        # Strip timezone for consistent lookup against naive Pandas Timestamps from CSV
        entry_h1_naive = entry_dt.replace(minute=0, second=0, microsecond=0, tzinfo=None)

        win = 1 if t["outcome"] == "WIN" else 0
        all_trades.append({
            "symbol":     "XAUUSD",
            "source":     "ai_session",
            "date":       d["date"],
            "entry_dt":   entry_dt,
            "entry_h1":   entry_h1_naive,
            "kill_zone":  t.get("kill_zone", ""),
            "outcome":    t["outcome"],
            "win":        win,
            "r_multiple": float(t["r_multiple"]),
            "mae_r":      float(t["mae_r"]) if t.get("mae_r") is not None else np.nan,
            "mfe_r":      float(t["mfe_r"]) if t.get("mfe_r") is not None else np.nan,
            "ts_precision": "M15",
        })
        xau_ai_count += 1

print(f"  XAUUSD AI session trades: {xau_ai_count}")

# -- Source 2: Mechanical backtest (all instruments) --
with open(MECH_RESULTS) as f:
    mech = json.load(f)

mech_trades = [r for r in mech.get("all_results", [])
               if r.get("decision") == "CANDIDATE" and r.get("r_multiple") is not None]

# For XAUUSD we prefer AI session data; use mech only for other instruments
mech_by_sym = {}
for t in mech_trades:
    sym = t.get("instrument", "")
    # Normalize US30_cash → US30
    if sym == "US30_cash":
        sym = "US30"
    mech_by_sym.setdefault(sym, []).append(t)

for sym, trades_list in mech_by_sym.items():
    if sym == "XAUUSD":
        continue  # prefer AI session data for XAUUSD
    n_added = 0
    for t in trades_list:
        cid = t.get("cid", "")
        entry_dt = parse_cid_to_datetime(cid)
        if entry_dt is None:
            continue
        win = 1 if t.get("outcome") == "WIN" else 0
        # Strip timezone for consistent lookup against naive CSV timestamps
        entry_h1_naive = entry_dt.replace(minute=0, second=0, microsecond=0, tzinfo=None)
        all_trades.append({
            "symbol":     sym,
            "source":     "mechanical",
            "date":       cid[:10],
            "entry_dt":   entry_dt,
            "entry_h1":   entry_h1_naive,
            "kill_zone":  t.get("zone", ""),
            "outcome":    t.get("outcome", ""),
            "win":        win,
            "r_multiple": float(t["r_multiple"]),
            "mae_r":      np.nan,  # not available in mechanical backtest
            "mfe_r":      np.nan,
            "ts_precision": "M15",
        })
        n_added += 1
    print(f"  {sym} mechanical trades: {n_added}")

trades_df = pd.DataFrame(all_trades)
print(f"\nTotal trades: {len(trades_df)}")
print("By instrument:", dict(trades_df.groupby("symbol").size()))


# ===========================================================================
# STEP 3: Match each trade to H1 bar σ²_t
# ===========================================================================
print()
print("=" * 70)
print("STEP 3: Matching trades to GARCH σ² at entry bar")
print("=" * 70)

unmatched = 0
sigma2_at_entry = []
sigma_at_entry  = []
p_volatile_at_entry = []
regime_at_entry = []

for _, row in trades_df.iterrows():
    sym = row["symbol"]
    h1_time = row["entry_h1"]

    # Look up σ² in GARCH series
    idx_map = h1_index.get(sym, {})
    # Try exact match, then ±1 hour (keys are naive pd.Timestamps)
    s2 = np.nan
    h1_ts = pd.Timestamp(h1_time)  # ensure consistent Timestamp type
    for delta in [0, -1, 1, -2, 2]:
        candidate = h1_ts + pd.Timedelta(hours=delta)
        if candidate in idx_map:
            idx = idx_map[candidate]
            df_sym = h1_data[sym]
            s2 = df_sym.loc[idx, "sigma2"]
            break

    if np.isnan(s2):
        unmatched += 1

    sigma2_at_entry.append(s2)
    sigma_at_entry.append(np.sqrt(s2) if not np.isnan(s2) else np.nan)

    # Look up Markov regime
    pv = np.nan
    rv = np.nan
    if sym in regime_probs:
        reg_df = regime_probs[sym]
        h1_ts_lookup = pd.Timestamp(h1_time)
        for delta in [0, -1, 1, -2, 2]:
            candidate = h1_ts_lookup + pd.Timedelta(hours=delta)
            match = reg_df[reg_df["h1_time"] == candidate]
            if not match.empty:
                pv = match.iloc[0]["p_volatile"]
                rv = match.iloc[0]["regime"]
                break

    p_volatile_at_entry.append(pv)
    regime_at_entry.append(rv)

trades_df["sigma2_entry"] = sigma2_at_entry
trades_df["sigma_entry"]  = sigma_at_entry
trades_df["p_volatile"]   = p_volatile_at_entry
trades_df["regime"]       = regime_at_entry  # 0=quiet, 1=volatile

n_matched = trades_df["sigma2_entry"].notna().sum()
print(f"  Matched to H1 bar: {n_matched}/{len(trades_df)} "
      f"({n_matched/len(trades_df)*100:.1f}%)")
print(f"  Unmatched (no H1 bar found): {unmatched}")

# Drop rows where we couldn't match σ²
matched_df = trades_df[trades_df["sigma2_entry"].notna()].copy()

# Compute volatility quartiles PER INSTRUMENT
matched_df["vol_quartile"] = np.nan
for sym, grp in matched_df.groupby("symbol"):
    if len(grp) >= 4:
        q_vals = pd.qcut(grp["sigma2_entry"], q=4, labels=[1, 2, 3, 4])
        matched_df.loc[grp.index, "vol_quartile"] = q_vals.astype(float)
    else:
        matched_df.loc[grp.index, "vol_quartile"] = np.nan

print()
for sym, grp in matched_df.groupby("symbol"):
    print(f"  {sym}: {len(grp)} trades matched, "
          f"σ_entry range [{grp['sigma_entry'].min()*10000:.2f}, "
          f"{grp['sigma_entry'].max()*10000:.2f}] bps")


# ===========================================================================
# STEP 4: Trade Outcome by Volatility State
# ===========================================================================
print()
print("=" * 70)
print("STEP 4: Trade Outcome by Volatility State")
print("=" * 70)

results = {}  # Collects all analysis results for output

# --------------------------------------------------------------------------
# 4a. WR by volatility quartile (per instrument + combined)
# --------------------------------------------------------------------------
def wilson_ci(k, n, alpha=0.05):
    """Wilson score 95% CI for proportion."""
    if n == 0:
        return (0.0, 1.0)
    from scipy.stats import norm
    z = norm.ppf(1 - alpha / 2)
    p_hat = k / n
    center = (p_hat + z**2 / (2*n)) / (1 + z**2 / n)
    spread = z * np.sqrt(p_hat*(1-p_hat)/n + z**2/(4*n**2)) / (1 + z**2/n)
    return (max(0, center - spread), min(1, center + spread))

def quartile_table(df, sym_label="Combined"):
    rows = []
    for q in [1, 2, 3, 4]:
        grp = df[df["vol_quartile"] == q]
        n = len(grp)
        if n == 0:
            continue
        wins = grp["win"].sum()
        wr = wins / n
        mean_r = grp["r_multiple"].mean()
        ci_lo, ci_hi = wilson_ci(wins, n)
        rows.append({
            "Quartile": f"Q{int(q)} (quietest)" if q==1 else (f"Q{int(q)} (noisiest)" if q==4 else f"Q{int(q)}"),
            "n": n,
            "WR": wr,
            "Mean_R": mean_r,
            "CI_lo": ci_lo,
            "CI_hi": ci_hi,
        })
    return rows

print("\n--- 4a. WR by Volatility Quartile ---\n")

all_quartile_results = {}

# Combined
combined_valid = matched_df[matched_df["vol_quartile"].notna()]
# Recompute quartiles on combined log-sigma²
combined_valid = combined_valid.copy()
try:
    combined_valid["vol_q_combined"] = pd.qcut(
        combined_valid["sigma2_entry"], q=4, labels=[1, 2, 3, 4], duplicates="drop"
    ).astype(float)
except Exception:
    combined_valid["vol_q_combined"] = np.nan

qtbl_combined = quartile_table(combined_valid.assign(vol_quartile=combined_valid["vol_q_combined"]), "Combined")
all_quartile_results["Combined"] = qtbl_combined
print(f"{'Combined':}")
print(f"  {'Quartile':<25} {'n':>5} {'WR':>7} {'Mean_R':>8} {'95% CI':>20}")
for r in qtbl_combined:
    print(f"  {r['Quartile']:<25} {r['n']:>5} {r['WR']:>7.1%} {r['Mean_R']:>8.3f} "
          f"  [{r['CI_lo']:.3f}, {r['CI_hi']:.3f}]")

# Per instrument
for sym, grp in matched_df.groupby("symbol"):
    if grp["vol_quartile"].notna().sum() < 8:
        print(f"\n  {sym}: too few trades for quartile analysis "
              f"(n={grp['vol_quartile'].notna().sum()})")
        continue
    qtbl = quartile_table(grp[grp["vol_quartile"].notna()], sym)
    all_quartile_results[sym] = qtbl
    print(f"\n  {sym}:")
    print(f"  {'Quartile':<25} {'n':>5} {'WR':>7} {'Mean_R':>8} {'95% CI':>20}")
    for r in qtbl:
        print(f"  {r['Quartile']:<25} {r['n']:>5} {r['WR']:>7.1%} {r['Mean_R']:>8.3f} "
              f"  [{r['CI_lo']:.3f}, {r['CI_hi']:.3f}]")

results["quartile_tables"] = all_quartile_results

# --------------------------------------------------------------------------
# 4b. Logistic regression: win ~ log(σ²_entry)
# --------------------------------------------------------------------------
print("\n--- 4b. Logistic Regression: win ~ log(σ²_entry) ---\n")

logit_results = {}

def run_logit(df, sym_label):
    df = df[df["sigma2_entry"].notna() & df["win"].notna()].copy()
    if len(df) < 20:
        return {"note": f"n={len(df)} < 20 — insufficient for logit", "n": len(df)}
    df["log_sigma2"] = np.log(df["sigma2_entry"])
    X = sm.add_constant(df["log_sigma2"])
    y = df["win"]
    try:
        model = sm.Logit(y, X)
        res = model.fit(disp=0, maxiter=100)
        coef = res.params["log_sigma2"]
        pval = res.pvalues["log_sigma2"]
        # McFadden pseudo-R²
        null_ll = sm.Logit(y, np.ones(len(y))).fit(disp=0).llf
        pseudo_r2 = 1 - res.llf / null_ll
        sig_bonf = pval < ALPHA_BONFERRONI
        return {
            "n": len(df),
            "coef": coef,
            "pvalue": pval,
            "pseudo_r2": pseudo_r2,
            "significant_bonferroni": sig_bonf,
            "direction": "higher vol → lower WR" if coef < 0 else "higher vol → higher WR",
        }
    except Exception as e:
        return {"note": f"Logit failed: {e}", "n": len(df)}

# Combined
res_combined = run_logit(matched_df, "Combined")
logit_results["Combined"] = res_combined
print(f"Combined (n={res_combined.get('n', '?')}):")
if "coef" in res_combined:
    print(f"  coef={res_combined['coef']:.4f}, p={res_combined['pvalue']:.4f}, "
          f"pseudo-R²={res_combined['pseudo_r2']:.4f}")
    print(f"  Significant (Bonferroni α={ALPHA_BONFERRONI:.4f}): "
          f"{res_combined['significant_bonferroni']}")
    print(f"  Direction: {res_combined['direction']}")
else:
    print(f"  {res_combined.get('note', 'N/A')}")

for sym, grp in matched_df.groupby("symbol"):
    res = run_logit(grp, sym)
    logit_results[sym] = res
    print(f"\n  {sym} (n={res.get('n', '?')}):")
    if "coef" in res:
        print(f"    coef={res['coef']:.4f}, p={res['pvalue']:.4f}, "
              f"pseudo-R²={res['pseudo_r2']:.4f}")
        print(f"    Significant (Bonferroni): {res['significant_bonferroni']}")
        print(f"    Direction: {res['direction']}")
    else:
        print(f"    {res.get('note', 'N/A')}")

results["logit"] = logit_results

# --------------------------------------------------------------------------
# 4c. MAE analysis by volatility state
# --------------------------------------------------------------------------
print("\n--- 4c. MAE Analysis by Volatility State ---\n")

mae_results = {}

mae_df = matched_df[matched_df["mae_r"].notna() & matched_df["vol_quartile"].notna()].copy()
print(f"Trades with MAE data: {len(mae_df)} "
      f"(only AI session XAUUSD trades have MAE)")

if len(mae_df) >= 20:
    mae_by_q = []
    for q in [1, 2, 3, 4]:
        grp = mae_df[mae_df["vol_quartile"] == q]
        if len(grp) == 0:
            continue
        mae_by_q.append({
            "quartile": int(q),
            "n": len(grp),
            "mean_mae_r": grp["mae_r"].mean(),
            "median_mae_r": grp["mae_r"].median(),
            "mean_r": grp["r_multiple"].mean(),
        })

    print(f"\n  {'Quartile':<8} {'n':>5} {'MeanMAE_R':>10} {'MedianMAE_R':>12} {'Mean_R':>8}")
    for row in mae_by_q:
        print(f"  Q{row['quartile']:<7} {row['n']:>5} {row['mean_mae_r']:>10.3f} "
              f"{row['median_mae_r']:>12.3f} {row['mean_r']:>8.3f}")

    # Kruskal-Wallis test on MAE across quartiles
    from scipy.stats import kruskal
    groups = [mae_df[mae_df["vol_quartile"] == q]["mae_r"].values for q in [1,2,3,4]]
    groups = [g for g in groups if len(g) >= 2]
    if len(groups) >= 2:
        stat, pval = kruskal(*groups)
        print(f"\n  Kruskal-Wallis MAE across quartiles: H={stat:.3f}, p={pval:.4f}")
        print(f"  Significant (Bonferroni): {pval < ALPHA_BONFERRONI}")
        mae_results["kruskal_p"] = pval
        mae_results["kruskal_sig_bonf"] = pval < ALPHA_BONFERRONI

    # Mann-Whitney Q1 vs Q4
    q1_mae = mae_df[mae_df["vol_quartile"] == 1]["mae_r"].values
    q4_mae = mae_df[mae_df["vol_quartile"] == 4]["mae_r"].values
    if len(q1_mae) >= 2 and len(q4_mae) >= 2:
        stat_mw, p_mw = mannwhitneyu(q1_mae, q4_mae, alternative="two-sided")
        print(f"  Mann-Whitney Q1 vs Q4 MAE: U={stat_mw:.1f}, p={p_mw:.4f}")
        mae_results["mw_q1_vs_q4_p"] = p_mw

    mae_results["by_quartile"] = mae_by_q
else:
    print("  Insufficient MAE data for quartile analysis")

results["mae"] = mae_results

# --------------------------------------------------------------------------
# 4d. Markov regime 2×2 table (quiet vs volatile × win vs loss)
# --------------------------------------------------------------------------
print("\n--- 4d. Markov Regime 2×2 Table (Fisher Exact Test) ---\n")

regime_results = {}

regime_df = matched_df[matched_df["regime"].notna()].copy()
regime_df["regime_int"] = regime_df["regime"].astype(int)

print(f"Trades with regime classification: {len(regime_df)}")

for sym_label, df_grp in [("Combined", regime_df)] + list(regime_df.groupby("symbol")):
    if len(df_grp) < 10:
        continue
    quiet = df_grp[df_grp["regime_int"] == 0]
    volatile = df_grp[df_grp["regime_int"] == 1]

    quiet_wins = quiet["win"].sum()
    quiet_n = len(quiet)
    vol_wins = volatile["win"].sum()
    vol_n = len(volatile)

    if quiet_n == 0 or vol_n == 0:
        continue

    table = np.array([
        [quiet_wins, quiet_n - quiet_wins],
        [vol_wins,   vol_n   - vol_wins],
    ])

    oddsratio, pval = fisher_exact(table, alternative="two-sided")

    quiet_wr = quiet_wins/quiet_n if quiet_n > 0 else np.nan
    vol_wr = vol_wins/vol_n if vol_n > 0 else np.nan

    print(f"\n  {sym_label}:")
    print(f"    Quiet   (n={quiet_n:3d}): WR={quiet_wr:.1%}, wins={quiet_wins}, losses={quiet_n-quiet_wins}")
    print(f"    Volatile(n={vol_n:3d}): WR={vol_wr:.1%}, wins={vol_wins}, losses={vol_n-vol_wins}")
    print(f"    Fisher exact: OR={oddsratio:.3f}, p={pval:.4f}, "
          f"Bonferroni sig: {pval < ALPHA_BONFERRONI}")

    regime_results[sym_label] = {
        "quiet_n": int(quiet_n),
        "quiet_wr": float(quiet_wr),
        "volatile_n": int(vol_n),
        "volatile_wr": float(vol_wr),
        "odds_ratio": float(oddsratio),
        "fisher_p": float(pval),
        "significant_bonferroni": bool(pval < ALPHA_BONFERRONI),
    }

results["markov_2x2"] = regime_results


# ===========================================================================
# STEP 5: Tail Event Analysis (ξ of standardized vs raw residuals)
# ===========================================================================
print()
print("=" * 70)
print("STEP 5: Tail Analysis — ξ_standardized vs ξ_raw")
print("=" * 70)

def fit_gpd_tails(data, threshold_pct=0.90):
    """Fit GPD to upper and lower tails above/below threshold_pct percentile."""
    results = {}
    # Upper tail
    u_upper = np.percentile(data, threshold_pct * 100)
    exceedances_upper = data[data > u_upper] - u_upper
    if len(exceedances_upper) >= 20:
        xi_u, loc_u, sigma_u = genpareto.fit(exceedances_upper, floc=0)
        results["upper"] = {"xi": xi_u, "sigma": sigma_u, "n": len(exceedances_upper)}
    else:
        results["upper"] = {"xi": np.nan, "sigma": np.nan, "n": len(exceedances_upper)}

    # Lower tail (flip sign)
    u_lower = np.percentile(-data, threshold_pct * 100)
    exceedances_lower = (-data)[(-data) > u_lower] - u_lower
    if len(exceedances_lower) >= 20:
        xi_l, loc_l, sigma_l = genpareto.fit(exceedances_lower, floc=0)
        results["lower"] = {"xi": xi_l, "sigma": sigma_l, "n": len(exceedances_lower)}
    else:
        results["lower"] = {"xi": np.nan, "sigma": np.nan, "n": len(exceedances_lower)}

    return results

tail_results = {}

print(f"\n{'Instrument':<10} {'Tail':<8} {'ξ_raw':>8} {'ξ_stdz':>8} {'Diff':>8} {'Interp'}")
print("-" * 60)

for sym, df in h1_data.items():
    r = df["log_ret"].values
    z = df["z"].values  # GARCH-standardized residuals

    # Raw returns
    gpd_raw = fit_gpd_tails(r)
    # Standardized residuals
    gpd_std = fit_gpd_tails(z)

    # Compare to stored ξ
    stored_xi_lower = gpd_params[sym]["lower_xi"]
    stored_xi_upper = gpd_params[sym]["upper_xi"]

    tail_results[sym] = {
        "raw_lower_xi":  gpd_raw["lower"]["xi"],
        "raw_upper_xi":  gpd_raw["upper"]["xi"],
        "std_lower_xi":  gpd_std["lower"]["xi"],
        "std_upper_xi":  gpd_std["upper"]["xi"],
        "stored_lower_xi": stored_xi_lower,
        "stored_upper_xi": stored_xi_upper,
    }

    for side in ["lower", "upper"]:
        xi_raw = gpd_raw[side]["xi"]
        xi_std = gpd_std[side]["xi"]
        if np.isnan(xi_raw) or np.isnan(xi_std):
            interp = "insufficient data"
        elif xi_std < xi_raw - 0.05:
            interp = "GARCH captures some tail risk (tails thinner after vol-adj)"
        elif xi_std > xi_raw + 0.05:
            interp = "GARCH INFLATES tail risk after vol-adj"
        else:
            interp = "tail risk in innovation (GARCH doesn't help)"
        print(f"{sym:<10} {side:<8} {xi_raw:>8.4f} {xi_std:>8.4f} "
              f"{(xi_std-xi_raw):>8.4f} {interp}")

results["tail_analysis"] = tail_results

# --------------------------------------------------------------------------
# 5b. Tail-vulnerable trades
# --------------------------------------------------------------------------
print("\n--- 5b. Tail-Vulnerable Trades ---\n")
print("Trades where GARCH-predicted 99th percentile move > structural SL distance")
print("(Using σ_entry as proxy for expected SL size = 1.0R)")

tail_vuln_results = {}

for sym, grp in matched_df.groupby("symbol"):
    df_sym = h1_data.get(sym)
    if df_sym is None:
        continue
    # 99th percentile of standardized residuals
    z = df_sym["z"].values
    z99 = np.percentile(np.abs(z), 99)
    # Predicted 99th pct move: σ_entry × z99
    grp = grp.copy()
    grp["pred_99_move"] = grp["sigma_entry"] * z99
    # SL distance proxy: σ_entry (in bps, scaled to returns)
    # A trade with 1R SL has SL = some price distance. We use 1.0 as 1R.
    # Tail-vulnerable: predicted 99th pct move > 1 × σ_entry (always true by construction)
    # Better definition: σ_entry > 75th percentile of σ in the full series
    df_sym_sub = df_sym[df_sym["time"] >= pd.Timestamp("2024-01-01")]
    p75_sigma = np.percentile(df_sym_sub["sigma"].values, 75) if len(df_sym_sub) > 0 else \
                np.percentile(df_sym["sigma"].values, 75)

    grp["tail_vulnerable"] = grp["sigma_entry"] > p75_sigma
    tv = grp[grp["tail_vulnerable"]]
    non_tv = grp[~grp["tail_vulnerable"]]

    tv_wr = tv["win"].mean() if len(tv) > 0 else np.nan
    non_tv_wr = non_tv["win"].mean() if len(non_tv) > 0 else np.nan

    tail_vuln_results[sym] = {
        "n_tail_vulnerable": int(len(tv)),
        "n_non_tail_vulnerable": int(len(non_tv)),
        "tv_wr": float(tv_wr) if not np.isnan(tv_wr) else None,
        "non_tv_wr": float(non_tv_wr) if not np.isnan(non_tv_wr) else None,
        "p75_sigma_bps": float(p75_sigma * 10000),
        "z99": float(z99),
    }

    print(f"{sym}: p75 σ={p75_sigma*10000:.2f}bps, z99={z99:.2f}x")
    print(f"  Tail-vulnerable (σ>p75): n={len(tv)}, WR={tv_wr:.1%}" if len(tv) > 0 else
          f"  Tail-vulnerable: n=0")
    print(f"  Non-vulnerable: n={len(non_tv)}, WR={non_tv_wr:.1%}" if len(non_tv) > 0 else
          f"  Non-vulnerable: n=0")

    if len(tv) >= 5 and len(non_tv) >= 5:
        stat, pval = mannwhitneyu(tv["win"].values, non_tv["win"].values,
                                   alternative="two-sided")
        print(f"  Mann-Whitney WR diff: p={pval:.4f}")
        tail_vuln_results[sym]["mw_p"] = float(pval)

results["tail_vulnerable"] = tail_vuln_results


# ===========================================================================
# STEP 6: Filter Simulation
# ===========================================================================
print()
print("=" * 70)
print("STEP 6: Filter Simulation — Remove Q4 Entries")
print("=" * 70)

filter_results = {}

for sym_label, df_grp in [("Combined", matched_df)] + [
    (sym, grp) for sym, grp in matched_df.groupby("symbol")
]:
    df_valid = df_grp[df_grp["vol_quartile"].notna()].copy()
    if len(df_valid) < 8:
        continue

    full_n     = len(df_valid)
    full_wr    = df_valid["win"].mean()
    full_exp   = df_valid["r_multiple"].mean()
    full_total_r = df_valid["r_multiple"].sum()

    # Remove Q4 trades
    filtered   = df_valid[df_valid["vol_quartile"] != 4].copy()
    removed    = df_valid[df_valid["vol_quartile"] == 4].copy()

    filt_n     = len(filtered)
    filt_wr    = filtered["win"].mean() if filt_n > 0 else np.nan
    filt_exp   = filtered["r_multiple"].mean() if filt_n > 0 else np.nan
    filt_total_r = filtered["r_multiple"].sum()

    removed_winners = removed[removed["win"] == 1]["r_multiple"].sum()
    removed_losers  = removed[removed["win"] == 0]["r_multiple"].sum()
    net_r_impact    = filt_total_r - full_total_r  # positive = better after removal

    # Test: is filtered WR significantly different?
    pval_filter = np.nan
    if filt_n >= 10 and full_n - filt_n >= 5:
        stat, pval_filter = mannwhitneyu(
            filtered["win"].values, removed["win"].values, alternative="two-sided"
        )

    filter_results[sym_label] = {
        "full_n": int(full_n),
        "full_wr": float(full_wr),
        "full_expectancy": float(full_exp),
        "full_total_r": float(full_total_r),
        "filtered_n": int(filt_n),
        "filtered_wr": float(filt_wr) if not np.isnan(filt_wr) else None,
        "filtered_expectancy": float(filt_exp) if not np.isnan(filt_exp) else None,
        "filtered_total_r": float(filt_total_r),
        "removed_n": int(full_n - filt_n),
        "removed_winner_r": float(removed_winners),
        "removed_loser_r": float(removed_losers),
        "net_r_impact": float(net_r_impact),
        "mw_pvalue": float(pval_filter) if not np.isnan(pval_filter) else None,
        "significant_bonferroni": bool(pval_filter < ALPHA_BONFERRONI) if not np.isnan(pval_filter) else False,
    }

    print(f"\n{sym_label}:")
    print(f"  Full set:    n={full_n}, WR={full_wr:.1%}, "
          f"expectancy={full_exp:.3f}R, total={full_total_r:.1f}R")
    print(f"  After Q4 rm: n={filt_n}, WR={filt_wr:.1%}, "
          f"expectancy={filt_exp:.3f}R, total={filt_total_r:.1f}R")
    print(f"  Removed Q4:  n={full_n-filt_n}, "
          f"removed W-R={removed_winners:.1f}R, removed L-R={removed_losers:.1f}R")
    print(f"  Net R impact: {net_r_impact:+.1f}R  "
          f"({'positive = filter HELPS' if net_r_impact > 0 else 'negative = filter HURTS'})")
    if not np.isnan(pval_filter):
        print(f"  Mann-Whitney p={pval_filter:.4f}, "
              f"Bonferroni sig: {pval_filter < ALPHA_BONFERRONI}")

results["filter_simulation"] = filter_results


# ===========================================================================
# STEP 7: Summary of Bonferroni-corrected p-values
# ===========================================================================
print()
print("=" * 70)
print("STEP 7: All P-values Summary")
print("=" * 70)

print(f"\nBonferroni threshold: α/{N_TESTS} = {ALPHA_BONFERRONI:.4f}")
print(f"\n{'Test':<45} {'p-value':>10} {'Sig?':>6}")
print("-" * 65)

all_pvals = []

# Logistic regressions
for label, lr in logit_results.items():
    if "pvalue" in lr:
        sig = lr["pvalue"] < ALPHA_BONFERRONI
        all_pvals.append((f"Logit win~log(σ²) [{label}]", lr["pvalue"], sig))

# MAE Kruskal-Wallis
if "kruskal_p" in mae_results:
    sig = mae_results["kruskal_p"] < ALPHA_BONFERRONI
    all_pvals.append(("MAE Kruskal-Wallis (XAUUSD quartiles)", mae_results["kruskal_p"], sig))

# MAE Mann-Whitney Q1 vs Q4
if "mw_q1_vs_q4_p" in mae_results:
    sig = mae_results["mw_q1_vs_q4_p"] < ALPHA_BONFERRONI
    all_pvals.append(("MAE Mann-Whitney Q1 vs Q4 (XAUUSD)", mae_results["mw_q1_vs_q4_p"], sig))

# Fisher exact (Markov 2x2)
for label, mr in regime_results.items():
    sig = mr["fisher_p"] < ALPHA_BONFERRONI
    all_pvals.append((f"Fisher exact Markov [{label}]", mr["fisher_p"], sig))

# Filter simulation
for label, fr in filter_results.items():
    if fr.get("mw_pvalue") is not None:
        sig = fr["mw_pvalue"] < ALPHA_BONFERRONI
        all_pvals.append((f"Filter MW Q4-removed [{label}]", fr["mw_pvalue"], sig))

for test, pval, sig in sorted(all_pvals, key=lambda x: x[1]):
    marker = " ***" if sig else ""
    print(f"  {test:<45} {pval:>10.4f} {'YES' + marker if sig else 'no':>6}")

n_sig = sum(1 for _, _, sig in all_pvals if sig)
print(f"\n  {n_sig}/{len(all_pvals)} tests survive Bonferroni correction")


# ===========================================================================
# STEP 8: Save all results to JSON
# ===========================================================================
print()
print("=" * 70)
print("STEP 8: Saving results")
print("=" * 70)

from datetime import date as dt_date
import traceback

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Prepare output dict
output = {
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "script": "compute_garch_regime_v1.py",
        "question": "Q-5.1: Does entry-time volatility state predict trade outcome?",
        "n_bonferroni_tests": N_TESTS,
        "alpha_bonferroni": ALPHA_BONFERRONI,
        "seed": 42,
    },
    "garch_params": {
        sym: {
            "omega_stored_pct2": p["omega_stored"],
            "omega_decimal":     p["omega"],
            "alpha":             p["alpha"],
            "beta":              p["beta"],
            "persistence":       p["persistence"],
            "note": "omega_stored was fitted on r*100; omega_decimal = omega_stored/10000",
        }
        for sym, p in garch_params.items()
    },
    "gpd_params": {
        sym: {k: float(v) if not (isinstance(v, float) and np.isnan(v)) else None
              for k, v in p.items()}
        for sym, p in gpd_params.items()
    },
    "markov_2state": {
        sym: {
            "quiet_sigma_bps": float(mp["std_devs"][0]*10000) if mp else None,
            "volatile_sigma_bps": float(mp["std_devs"][1]*10000) if mp else None,
            "quiet_freq_pct": float(mp["state_fracs"][0]*100) if mp else None,
            "volatile_freq_pct": float(mp["state_fracs"][1]*100) if mp else None,
        }
        for sym, mp in markov_params.items()
    },
    "trade_counts": dict(trades_df.groupby("symbol").size().to_dict()),
    "trade_counts_matched": dict(matched_df.groupby("symbol").size().to_dict()),
    "quartile_analysis": {
        sym: rows for sym, rows in all_quartile_results.items()
    },
    "logistic_regression": {
        sym: {k: (float(v) if isinstance(v, (float, np.floating)) else v)
              for k, v in res.items()}
        for sym, res in logit_results.items()
    },
    "mae_analysis": {
        k: (v if not isinstance(v, (float, np.floating)) else float(v))
        for k, v in mae_results.items()
    },
    "markov_2x2": regime_results,
    "tail_analysis": {
        sym: {k: (float(v) if isinstance(v, (float, np.floating)) else v)
              for k, v in tr.items()}
        for sym, tr in tail_results.items()
    },
    "tail_vulnerable": tail_vuln_results,
    "filter_simulation": filter_results,
    "all_pvalues": [
        {"test": t, "pvalue": float(p), "significant_bonferroni": bool(s)}
        for t, p, s in all_pvals
    ],
    "n_significant_bonferroni": n_sig,
}

out_json = OUT_DIR / f"garch_regime_trade_outcomes_v1_{timestamp}.json"
with open(out_json, "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"  Results JSON: {out_json}")

# Also save the matched trades dataframe for later use
trades_out = matched_df[[
    "symbol", "source", "date", "entry_dt", "kill_zone",
    "outcome", "win", "r_multiple", "mae_r", "mfe_r",
    "sigma2_entry", "sigma_entry", "vol_quartile",
    "p_volatile", "regime"
]].copy()
trades_out["sigma_entry_bps"] = trades_out["sigma_entry"] * 10000

trades_csv = OUT_DIR / f"garch_regime_trades_v1_{timestamp}.csv"
trades_out.to_csv(trades_csv, index=False)
print(f"  Trades CSV: {trades_csv}")


# ===========================================================================
# STEP 9: Write markdown report
# ===========================================================================
print()
print("=" * 70)
print("STEP 9: Writing markdown report")
print("=" * 70)

def fmt(v, fmt_str=".4f"):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    return f"{v:{fmt_str}}"

md_lines = [
    "# GARCH-EVT Regime Analysis of Trade Outcomes (Q-5.1)",
    "",
    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}  ",
    f"**Script:** `compute_garch_regime_v1.py`  ",
    f"**Question:** Does entry-time GARCH volatility state predict GTOS trade outcome?  ",
    f"**Bonferroni correction:** α/{N_TESTS} = {ALPHA_BONFERRONI:.4f}",
    "",
    "---",
    "",
    "## 1. GARCH Parameters (H1, All Sessions)",
    "",
    "Source: `distributional_characterization_20260411_012816.json`",
    "",
    "| Instrument | ω (stored, pct²) | ω (decimal) | α (ARCH) | β (GARCH) | Persistence |",
    "|-----------|----------------|------------|---------|---------|------------|",
]

for sym, p in garch_params.items():
    md_lines.append(
        f"| {sym} | {p['omega_stored']:.4e} | {p['omega']:.4e} | "
        f"{p['alpha']:.4f} | {p['beta']:.4f} | {p['persistence']:.4f} |"
    )

md_lines += [
    "",
    "**Note:** US30 has extremely high ARCH coefficient (α=0.538), indicating rapid"
    " vol mean-reversion. GBPUSD/GBPJPY have lower persistence, implying vol shocks"
    " decay faster. XAUUSD and USDJPY are in the classic near-unit-root GARCH regime.",
    "",
    "## 2. Trade Data Coverage",
    "",
    "| Instrument | Source | n (total) | n (matched) | WR |",
    "|-----------|--------|----------|------------|-----|",
]

for sym in INSTRUMENT_MAP:
    total_n = int(trades_df[trades_df["symbol"] == sym].shape[0])
    match_n = int(matched_df[matched_df["symbol"] == sym].shape[0])
    if match_n > 0:
        wr_val = matched_df[matched_df["symbol"] == sym]["win"].mean()
        src = matched_df[matched_df["symbol"] == sym]["source"].iloc[0]
        md_lines.append(f"| {sym} | {src} | {total_n} | {match_n} | {wr_val:.1%} |")

md_lines += [
    "",
    "**XAUUSD:** AI-evaluated batch trades (sessions) with exact M15 entry timestamps.  ",
    "**Others:** Mechanical backtest with date+session+HHMM from cid (M15 precision).  ",
    "Instruments with n<8 are excluded from quartile analysis.",
    "",
    "## 3. Volatility Quartile Distribution at Trade Entry",
    "",
]

for sym_label, qtbl in all_quartile_results.items():
    md_lines.append(f"### {sym_label}")
    md_lines.append("")
    md_lines.append("| Quartile | n | WR | Mean R | 95% CI (Wilson) |")
    md_lines.append("|---------|---|-----|--------|----------------|")
    for r in qtbl:
        md_lines.append(
            f"| {r['Quartile']} | {r['n']} | {r['WR']:.1%} | {r['Mean_R']:.3f} | "
            f"[{r['CI_lo']:.3f}, {r['CI_hi']:.3f}] |"
        )
    md_lines.append("")

md_lines += [
    "## 4. Logistic Regression: win ~ log(σ²_entry)",
    "",
    "Negative coefficient = higher volatility → lower win rate.",
    "",
    "| Instrument | n | Coef | p-value | Pseudo-R² | Bonferroni Sig | Direction |",
    "|-----------|---|------|---------|----------|--------------|---------|",
]

for sym, lr in logit_results.items():
    if "coef" in lr:
        md_lines.append(
            f"| {sym} | {lr['n']} | {lr['coef']:.4f} | {lr['pvalue']:.4f} | "
            f"{lr['pseudo_r2']:.4f} | {lr['significant_bonferroni']} | {lr['direction']} |"
        )
    else:
        md_lines.append(f"| {sym} | {lr.get('n','?')} | — | — | — | — | {lr.get('note','N/A')} |")

md_lines += [
    "",
    "## 5. MAE Analysis by Volatility State",
    "(XAUUSD AI trades only — MAE not available for mechanical backtest)",
    "",
]

if mae_results.get("by_quartile"):
    md_lines.append("| Quartile | n | Mean MAE_R | Median MAE_R | Mean R |")
    md_lines.append("|---------|---|----------|------------|--------|")
    for r in mae_results["by_quartile"]:
        md_lines.append(
            f"| Q{r['quartile']} | {r['n']} | {r['mean_mae_r']:.3f} | "
            f"{r['median_mae_r']:.3f} | {r['mean_r']:.3f} |"
        )
    md_lines.append("")
    if "kruskal_p" in mae_results:
        md_lines.append(
            f"Kruskal-Wallis (MAE across quartiles): p={mae_results['kruskal_p']:.4f}, "
            f"Bonferroni sig: {mae_results['kruskal_sig_bonf']}"
        )
    if "mw_q1_vs_q4_p" in mae_results:
        md_lines.append(
            f"Mann-Whitney Q1 vs Q4 MAE: p={mae_results['mw_q1_vs_q4_p']:.4f}"
        )
else:
    md_lines.append("Insufficient MAE data for analysis.")

md_lines += [
    "",
    "## 6. Markov Regime 2×2 Table (Fisher Exact Test)",
    "",
    "2-state Gaussian HMM fitted via forward-backward algorithm using stored parameters.",
    "",
    "| Instrument | Quiet n | Quiet WR | Volatile n | Volatile WR | OR | Fisher p | Bonf Sig |",
    "|-----------|--------|---------|-----------|-----------|-----|---------|---------|",
]

for sym, mr in regime_results.items():
    md_lines.append(
        f"| {sym} | {mr['quiet_n']} | {mr['quiet_wr']:.1%} | {mr['volatile_n']} | "
        f"{mr['volatile_wr']:.1%} | {mr['odds_ratio']:.3f} | {mr['fisher_p']:.4f} | "
        f"{mr['significant_bonferroni']} |"
    )

md_lines += [
    "",
    "## 7. Tail Analysis: ξ_standardized vs ξ_raw",
    "",
    "Comparing GPD shape parameter for raw returns vs GARCH-standardized residuals.",
    "**If ξ_std < ξ_raw:** GARCH explains some tail risk (thinner tails after vol-adjustment).",
    "**If ξ_std ≈ ξ_raw:** Tail risk is in the innovation process — GARCH doesn't help.",
    "",
    "| Instrument | Tail | ξ_raw (stored) | ξ_raw (fitted) | ξ_std | Diff (std−raw) | Interpretation |",
    "|-----------|-----|-------------|-------------|------|--------------|--------------|",
]

for sym, tr in tail_results.items():
    for side in ["lower", "upper"]:
        stored_key = f"stored_{side}_xi"
        raw_key = f"raw_{side}_xi"
        std_key = f"std_{side}_xi"
        xi_stored = tr.get(stored_key, np.nan)
        xi_raw = tr.get(raw_key, np.nan)
        xi_std = tr.get(std_key, np.nan)
        diff = xi_std - xi_raw if not (np.isnan(xi_std) or np.isnan(xi_raw)) else np.nan
        if np.isnan(xi_std) or np.isnan(xi_raw):
            interp = "N/A"
        elif diff < -0.05:
            interp = "GARCH helps (thinner tails)"
        elif diff > 0.05:
            interp = "GARCH inflates"
        else:
            interp = "neutral (tail in innovation)"
        xi_stored_str = f"{xi_stored:.4f}" if not np.isnan(xi_stored) else "N/A"
        xi_raw_str = f"{xi_raw:.4f}" if not np.isnan(xi_raw) else "N/A"
        xi_std_str = f"{xi_std:.4f}" if not np.isnan(xi_std) else "N/A"
        diff_str = f"{diff:+.4f}" if not np.isnan(diff) else "N/A"
        md_lines.append(
            f"| {sym} | {side} | {xi_stored_str} | {xi_raw_str} | {xi_std_str} | "
            f"{diff_str} | {interp} |"
        )

md_lines += [
    "",
    "## 8. Tail-Vulnerable Trades",
    "",
    "Trades entered when σ_entry > p75 of full H1 σ series (elevated tail risk environment).",
    "",
    "| Instrument | TV n | TV WR | Non-TV n | Non-TV WR | MW p |",
    "|-----------|-----|------|---------|---------|-----|",
]

for sym, tv in tail_vuln_results.items():
    tv_wr_str = f"{tv['tv_wr']:.1%}" if tv.get('tv_wr') is not None else "N/A"
    non_tv_wr_str = f"{tv['non_tv_wr']:.1%}" if tv.get('non_tv_wr') is not None else "N/A"
    mw_p_str = f"{tv['mw_p']:.4f}" if tv.get('mw_p') is not None else "N/A"
    md_lines.append(
        f"| {sym} | {tv['n_tail_vulnerable']} | {tv_wr_str} | "
        f"{tv['n_non_tail_vulnerable']} | {non_tv_wr_str} | {mw_p_str} |"
    )

md_lines += [
    "",
    "## 9. Filter Simulation: Remove Q4 (Noisiest) Entries",
    "",
    "| Instrument | Full n | Full WR | Full Exp | Filt n | Filt WR | Filt Exp | Net ΔR | MW p | Bonf Sig |",
    "|-----------|-------|--------|---------|-------|--------|---------|-------|-----|---------|",
]

for sym, fr in filter_results.items():
    filt_wr = f"{fr['filtered_wr']:.1%}" if fr.get('filtered_wr') is not None else "N/A"
    filt_exp = f"{fr['filtered_expectancy']:.3f}" if fr.get('filtered_expectancy') is not None else "N/A"
    mw_p = f"{fr['mw_pvalue']:.4f}" if fr.get('mw_pvalue') is not None else "N/A"
    net_dr = fr['net_r_impact']
    md_lines.append(
        f"| {sym} | {fr['full_n']} | {fr['full_wr']:.1%} | {fr['full_expectancy']:.3f} | "
        f"{fr['filtered_n']} | {filt_wr} | {filt_exp} | {net_dr:+.1f}R | "
        f"{mw_p} | {fr['significant_bonferroni']} |"
    )

md_lines += [
    "",
    "## 10. All P-values (Bonferroni Corrected)",
    "",
    f"Correction: α/{N_TESTS} = {ALPHA_BONFERRONI:.4f}",
    "",
    "| Test | p-value | Significant? |",
    "|-----|---------|------------|",
]

for t, p, s in sorted(all_pvals, key=lambda x: x[1]):
    md_lines.append(f"| {t} | {p:.4f} | {'**YES**' if s else 'No'} |")

# ==========================================================================
# CONCLUSION
# ==========================================================================
any_sig = n_sig > 0

md_lines += [
    "",
    "---",
    "",
    "## 11. Conclusion",
    "",
]

# Derive key finding from logistic regression
xau_logit = logit_results.get("XAUUSD", {})
combined_logit = logit_results.get("Combined", {})
filter_combined = filter_results.get("Combined", {})
filter_xau = filter_results.get("XAUUSD", {})

logit_sig = combined_logit.get("significant_bonferroni", False)
filter_sig = (filter_combined or filter_xau or {}).get("significant_bonferroni", False)

if not any_sig:
    verdict = "**NULL RESULT — GARCH volatility state at trade entry does NOT predict trade outcome.**"
    action = "Do NOT implement a GARCH-based entry filter. Volatility state is not an actionable signal."
elif logit_sig and not filter_sig:
    verdict = "**WEAK SIGNAL — volatility state shows statistical association but filter simulation does not improve expectancy.**"
    action = "Statistical relationship exists but is not economically actionable. Monitor but do not filter."
elif logit_sig and filter_sig:
    verdict = "**SIGNAL FOUND — removing high-volatility entries significantly improves expectancy.**"
    action = "Consider a GARCH-based entry filter: skip trades when σ_entry > Q3 threshold."
else:
    verdict = "**MIXED — some tests significant, others not. Evidence is inconclusive.**"
    action = "More data needed before implementing a filter."

# Specific numbers
xau_coef = xau_logit.get("coef", None)
xau_p = xau_logit.get("pvalue", None)

md_lines += [
    f"### {verdict}",
    "",
    f"**Logistic regression (XAUUSD):** "
    f"coef={xau_coef:.4f}, p={xau_p:.4f}" if xau_coef is not None else
    "Logistic regression: insufficient data",
    "",
]

if filter_xau and filter_xau.get("filtered_wr") is not None:
    fr_x = filter_xau
    md_lines += [
        f"**Filter simulation (XAUUSD):** Removing Q4 entries changes expectancy from "
        f"{fr_x['full_expectancy']:.3f}R to {fr_x['filtered_expectancy']:.3f}R "
        f"(ΔR = {fr_x['net_r_impact']:+.1f}R on {fr_x['full_n']} trades).  ",
        f"WR change: {fr_x['full_wr']:.1%} → {fr_x['filtered_wr']:.1%}",
        "",
    ]

md_lines += [
    "**Tail analysis:** GARCH standardization of residuals — see Section 7 for whether "
    "GARCH captures or fails to capture tail risk per instrument.",
    "",
    f"**Action:** {action}",
    "",
    "### Instrument-specific notes:",
    "",
]

for sym in INSTRUMENT_MAP:
    n_trades = matched_df[matched_df["symbol"] == sym].shape[0]
    if n_trades == 0:
        continue
    lr = logit_results.get(sym, {})
    if "coef" in lr:
        md_lines.append(
            f"- **{sym}** (n={lr['n']}): coef={lr['coef']:.4f}, p={lr['pvalue']:.4f} "
            f"({'Bonferroni sig' if lr['significant_bonferroni'] else 'not significant'})"
        )
    else:
        md_lines.append(f"- **{sym}** (n={n_trades}): {lr.get('note', 'insufficient data')}")

md_lines += [
    "",
    "---",
    "",
    "*All findings are exploratory. No changes to live trading system without CEO approval.*",
    f"*Bonferroni threshold: {ALPHA_BONFERRONI:.4f} ({N_TESTS} tests).*",
    "",
]

md_content = "\n".join(md_lines)
out_md = OUT_DIR / "garch_regime_trade_outcomes_v1.md"
with open(out_md, "w") as f:
    f.write(md_content)

print(f"\nMarkdown report: {out_md}")
print(f"JSON results:    {out_json}")
print(f"Trades CSV:      {trades_csv}")
print()
print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print()
print(f"KEY FINDING: {n_sig}/{len(all_pvals)} tests survive Bonferroni correction")
print(f"VERDICT: {'ACTIONABLE SIGNAL FOUND' if n_sig > 0 else 'NULL RESULT — no actionable signal'}")
