#!/usr/bin/env python3
"""
Fix 2: PE KZ vs Non-KZ Bootstrap Permutation Test
====================================================
Resolves the discrepancy between full-series PE and hourly-bin mean PE
identified in PEER_REVIEW_AUDIT.md, Finding 2.

Method:
  1. Load XAUUSD H1 log returns (gap-filtered, using FIXED gap method).
  2. Compute observed PE difference: PE(KZ full-series) - PE(non-KZ full-series).
  3. Permutation test: shuffle KZ/non-KZ labels 10,000 times, recompute PE
     difference each time → null distribution.
  4. Two-sided p-value: fraction of permuted |diff| >= |observed diff|.
  5. Decision: p < 0.05 → real effect; p >= 0.05 → cannot distinguish from
     sample-size artifact.
  6. Save to: nonlinear_structure/pe_kz_permutation_test_v1.md

IMPORTANT: uses FIXED gap filter (dt.total_seconds(), not astype(np.int64)/1e9)
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR  = os.path.join(REPO_ROOT, "data", "historical")
OUT_DIR   = os.path.join(os.path.dirname(__file__), "nonlinear_structure")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Kill-zone definition (XAUUSD H1, UTC) ─────────────────────────────────
XAUUSD_KZ = [(7.0, 10.5), (13.0, 17.0)]   # London + NY (matches run_nonlinear_structure.py)

# ── PE embedding dim (matches the main analysis) ──────────────────────────
PE_M = 5

# ── Permutation test settings ─────────────────────────────────────────────
N_PERM = 10_000
RNG_SEED = 42


# ── Gap filter (FIXED) ─────────────────────────────────────────────────────
def gap_mask(df: pd.DataFrame, expected_min: int = 60) -> np.ndarray:
    """
    Boolean mask, length n-1.  True = valid consecutive-bar transition.
    FIXED: uses .diff().dt.total_seconds() not astype(np.int64)/1e9.
    """
    gaps_min = df["time"].diff().dt.total_seconds().iloc[1:].values / 60.0
    return gaps_min <= expected_min * 3.0


# ── Kill-zone mask ─────────────────────────────────────────────────────────
def kz_mask_bars(df: pd.DataFrame) -> np.ndarray:
    h    = df["time"].dt.hour + df["time"].dt.minute / 60.0
    mask = np.zeros(len(df), dtype=bool)
    for lo, hi in XAUUSD_KZ:
        mask |= ((h >= lo) & (h < hi)).values
    return mask


# ── Ordinal pattern PE (no external library) ──────────────────────────────
def _ordinal_codes(x: np.ndarray, m: int) -> np.ndarray:
    embedded = np.lib.stride_tricks.sliding_window_view(x, m)
    ranks    = np.argsort(embedded, axis=1)
    mult     = (m ** np.arange(m - 1, -1, -1)).astype(np.int64)
    return (ranks * mult).sum(axis=1).astype(np.int64)


def pe_full(x: np.ndarray, m: int) -> float:
    """Normalized permutation entropy for a 1-D series x."""
    n = len(x)
    if n < m + 5:
        return np.nan
    codes  = _ordinal_codes(x, m)
    _, cnts = np.unique(codes, return_counts=True)
    p      = cnts / cnts.sum()
    H      = -np.sum(p * np.log(p))
    H_max  = np.log(float(np.math.factorial(m)))
    return float(H / H_max) if H_max > 0 else np.nan


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    path = os.path.join(DATA_DIR, "XAUUSD_H1.csv")
    if not os.path.exists(path):
        sys.exit(f"ERROR: {path} not found")

    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    if "time" not in df.columns:
        df.columns = ["time", "open", "high", "low", "close"] + list(df.columns[5:])
    df["time"]  = pd.to_datetime(df["time"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["time", "close"]).sort_values("time").reset_index(drop=True)

    print(f"XAUUSD H1: {len(df)} bars  ({df['time'].iloc[0].date()} – {df['time'].iloc[-1].date()})")

    # Log returns on gap-valid bar transitions
    closes  = df["close"].values.astype(np.float64)
    r_full  = np.diff(np.log(closes))           # length n-1
    gap_ok  = gap_mask(df)                       # length n-1  (FIXED)
    # timestamps of the CLOSING bar of each return
    t_full  = df["time"].values[1:]             # length n-1

    # KZ label for each return (assigned to the closing bar)
    kz_bar  = kz_mask_bars(df)                  # length n
    kz_ret  = kz_bar[1:]                        # length n-1  (same index as r_full)

    # Apply gap filter and finite filter
    valid   = gap_ok & np.isfinite(r_full)
    r       = r_full[valid]
    kz      = kz_ret[valid]

    r_kz    = r[kz]
    r_nonkz = r[~kz]

    n_kz    = len(r_kz)
    n_nonkz = len(r_nonkz)
    n_total = len(r)

    print(f"\nReturns after gap filter: {n_total}")
    print(f"  KZ:     {n_kz}")
    print(f"  Non-KZ: {n_nonkz}")

    # ── Observed PE values ──────────────────────────────────────────────────
    pe_kz    = pe_full(r_kz,    m=PE_M)
    pe_nonkz = pe_full(r_nonkz, m=PE_M)
    obs_diff = pe_kz - pe_nonkz

    print(f"\nObserved PE (m={PE_M}):")
    print(f"  KZ full-series:     {pe_kz:.6f}  (n={n_kz})")
    print(f"  Non-KZ full-series: {pe_nonkz:.6f}  (n={n_nonkz})")
    print(f"  Observed diff (KZ - Non-KZ): {obs_diff:+.6f}")
    print(f"  KZ more ordered (PE_KZ < PE_nonKZ)? {'YES' if pe_kz < pe_nonkz else 'NO'}")

    # ── Permutation test ───────────────────────────────────────────────────
    print(f"\nRunning {N_PERM:,} permutations …", flush=True)
    rng      = np.random.default_rng(RNG_SEED)
    perm_diffs = np.empty(N_PERM)
    kz_labels  = kz.copy()

    for i in range(N_PERM):
        shuffled = rng.permutation(kz_labels)
        p_kz     = pe_full(r[shuffled],  m=PE_M)
        p_nonkz  = pe_full(r[~shuffled], m=PE_M)
        perm_diffs[i] = p_kz - p_nonkz

    # Two-sided p-value
    p_val = float(np.mean(np.abs(perm_diffs) >= abs(obs_diff)))

    print(f"\nPermutation test result:")
    print(f"  |Observed diff| = {abs(obs_diff):.6f}")
    print(f"  Permuted |diff| >= |observed|: {int(np.sum(np.abs(perm_diffs) >= abs(obs_diff)))} / {N_PERM}")
    print(f"  Two-sided p-value: {p_val:.4f}")

    # ── Decision ───────────────────────────────────────────────────────────
    alpha = 0.05
    if p_val < alpha:
        decision = (
            f"**REAL EFFECT** (p={p_val:.4f} < {alpha}). "
            f"KZ PE ({pe_kz:.5f}) < Non-KZ PE ({pe_nonkz:.5f}) — "
            f"KZ returns are more structured (effect size: {abs(obs_diff):.5f} PE units)."
        )
        decision_short = "REAL EFFECT"
    else:
        decision = (
            f"**CANNOT DISTINGUISH FROM SAMPLE-SIZE ARTIFACT** (p={p_val:.4f} >= {alpha}). "
            f"The observed KZ–non-KZ PE difference ({obs_diff:+.5f}) is consistent with "
            f"random label assignment. Finite-sample bias cannot be ruled out as the sole "
            f"explanation (KZ has {n_kz} returns vs {n_nonkz} non-KZ; PE has a known "
            f"downward bias for shorter series)."
        )
        decision_short = "CANNOT DISTINGUISH FROM SAMPLE-SIZE ARTIFACT"

    print(f"\nDecision: {decision_short}")

    # ── Save markdown ──────────────────────────────────────────────────────
    ts     = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_md = os.path.join(OUT_DIR, "pe_kz_permutation_test_v1.md")

    # Null distribution percentiles for the table
    null_p5  = float(np.percentile(perm_diffs, 5))
    null_p95 = float(np.percentile(perm_diffs, 95))

    md = f"""# PE Kill-Zone vs Non-Kill-Zone — Permutation Test

**Generated:** {ts} UTC
**Script:** run_pe_kz_permutation_test.py
**Addresses:** PEER_REVIEW_AUDIT.md Finding 2 — PE table displays hourly-bin PE but uses full-series PE for Yes/No decision.

---

## Purpose

The original summary table mixed two metrics:
- **Displayed values:** hourly-bin mean PE (KZ=0.98163, non-KZ=0.97955)
- **Yes/No decision:** full-series PE (KZ=0.99537 < non-KZ=0.99854 → "Yes")

These two metrics disagree in direction. Additionally, the full-series comparison
may reflect a finite-sample bias (PE has a downward bias for shorter series; KZ has
{n_kz} returns vs non-KZ {n_nonkz}). This permutation test resolves whether the
full-series finding reflects a real structure difference or a sample-size artifact.

---

## Data

| Item | Value |
|------|-------|
| Instrument | XAUUSD H1 |
| Returns (after gap filter) | {n_total} |
| KZ returns | {n_kz} (London 07:00–10:30 + NY 13:00–17:00 UTC) |
| Non-KZ returns | {n_nonkz} |
| Embedding dimension m | {PE_M} |
| Gap filter | Fixed (`.diff().dt.total_seconds()`) |

---

## Observed PE Values (full-series)

| Series | PE (m={PE_M}) | n |
|--------|---------------|---|
| KZ | {pe_kz:.6f} | {n_kz} |
| Non-KZ | {pe_nonkz:.6f} | {n_nonkz} |
| **Observed diff (KZ − Non-KZ)** | **{obs_diff:+.6f}** | — |

KZ PE < Non-KZ PE → KZ returns are MORE structured: **{"YES" if pe_kz < pe_nonkz else "NO"}**

---

## Permutation Test (n={N_PERM:,} shuffles, seed={RNG_SEED})

| Metric | Value |
|--------|-------|
| Permutations | {N_PERM:,} |
| |Observed diff| | {abs(obs_diff):.6f} |
| Permuted |diff| ≥ |observed| | {int(np.sum(np.abs(perm_diffs) >= abs(obs_diff)))} / {N_PERM} |
| **Two-sided p-value** | **{p_val:.4f}** |
| Null 5th–95th percentile | [{null_p5:.6f}, {null_p95:.6f}] |

---

## Decision

{decision}

---

## Corrected Summary Table (replaces C1 KZ table in nonlinear_summary_*.md)

The table below uses **full-series PE** for both the displayed values and the Yes/No decision,
eliminating the metric mismatch identified in the audit.

| Instrument | Session | KZ PE (full-series) | Non-KZ PE (full-series) | KZ < nonKZ? | Perm p-value |
|---|---|---|---|---|---|
| XAUUSD | London+NY | {pe_kz:.5f} | {pe_nonkz:.5f} | {"Yes ✓" if pe_kz < pe_nonkz else "No"} | {p_val:.4f} |

*Note: Other instruments not re-run here; their full-series PE values are in nonlinear_results_*.json.*

---

## Interpretation

- The full-series finding that KZ returns are more structured (lower PE) {"is supported" if p_val < alpha else "is not supported"} by the permutation test.
- The hourly-bin PE comparison (which shows the OPPOSITE direction) reflects the extreme outlier at hour 0 (00:00 UTC, n=56 bars) that dominates the non-KZ hourly mean. Excluding hour 0, both metrics agree: KZ is slightly more ordered.
- **The original C1 Yes/No conclusion {"stands" if p_val < alpha else "should be treated with caution"}.** However, the table display has been corrected to use consistent metrics (full-series PE for both columns and the decision column).

---

*This file was generated to close PEER_REVIEW_AUDIT.md Finding 2.*
*The original nonlinear_summary_20260411_030330.md is preserved unchanged.*
"""

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nSaved: {out_md}")
    return p_val, obs_diff


if __name__ == "__main__":
    import math
    np.math = math   # compatibility shim for numpy <2 .math deprecation
    main()
