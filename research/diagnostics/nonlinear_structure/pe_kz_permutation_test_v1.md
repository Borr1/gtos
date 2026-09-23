# PE Kill-Zone vs Non-Kill-Zone — Permutation Test

**Generated:** 20260411_101034 UTC
**Script:** run_pe_kz_permutation_test.py
**Addresses:** PEER_REVIEW_AUDIT.md Finding 2 — PE table displays hourly-bin PE but uses full-series PE for Yes/No decision.

---

## Purpose

The original summary table mixed two metrics:
- **Displayed values:** hourly-bin mean PE (KZ=0.98163, non-KZ=0.97955)
- **Yes/No decision:** full-series PE (KZ=0.99537 < non-KZ=0.99854 → "Yes")

These two metrics disagree in direction. Additionally, the full-series comparison
may reflect a finite-sample bias (PE has a downward bias for shorter series; KZ has
5136 returns vs non-KZ 9427). This permutation test resolves whether the
full-series finding reflects a real structure difference or a sample-size artifact.

---

## Data

| Item | Value |
|------|-------|
| Instrument | XAUUSD H1 |
| Returns (after gap filter) | 14563 |
| KZ returns | 5136 (London 07:00–10:30 + NY 13:00–17:00 UTC) |
| Non-KZ returns | 9427 |
| Embedding dimension m | 5 |
| Gap filter | Fixed (`.diff().dt.total_seconds()`) |

---

## Observed PE Values (full-series)

| Series | PE (m=5) | n |
|--------|---------------|---|
| KZ | 0.997739 | 5136 |
| Non-KZ | 0.998286 | 9427 |
| **Observed diff (KZ − Non-KZ)** | **-0.000547** | — |

KZ PE < Non-KZ PE → KZ returns are MORE structured: **YES**

---

## Permutation Test (n=10,000 shuffles, seed=42)

| Metric | Value |
|--------|-------|
| Permutations | 10,000 |
| |Observed diff| | 0.000547 |
| Permuted |diff| ≥ |observed| | 7919 / 10000 |
| **Two-sided p-value** | **0.7919** |
| Null 5th–95th percentile | [-0.001823, -0.000165] |

---

## Decision

**CANNOT DISTINGUISH FROM SAMPLE-SIZE ARTIFACT** (p=0.7919 >= 0.05). The observed KZ–non-KZ PE difference (-0.00055) is consistent with random label assignment. Finite-sample bias cannot be ruled out as the sole explanation (KZ has 5136 returns vs 9427 non-KZ; PE has a known downward bias for shorter series).

---

## Corrected Summary Table (replaces C1 KZ table in nonlinear_summary_*.md)

The table below uses **full-series PE** for both the displayed values and the Yes/No decision,
eliminating the metric mismatch identified in the audit.

| Instrument | Session | KZ PE (full-series) | Non-KZ PE (full-series) | KZ < nonKZ? | Perm p-value |
|---|---|---|---|---|---|
| XAUUSD | London+NY | 0.99774 | 0.99829 | Yes ✓ | 0.7919 |

*Note: Other instruments not re-run here; their full-series PE values are in nonlinear_results_*.json.*

---

## Interpretation

- The full-series finding that KZ returns are more structured (lower PE) is not supported by the permutation test.
- The hourly-bin PE comparison (which shows the OPPOSITE direction) reflects the extreme outlier at hour 0 (00:00 UTC, n=56 bars) that dominates the non-KZ hourly mean. Excluding hour 0, both metrics agree: KZ is slightly more ordered.
- **The original C1 Yes/No conclusion should be treated with caution.** However, the table display has been corrected to use consistent metrics (full-series PE for both columns and the decision column).

---

*This file was generated to close PEER_REVIEW_AUDIT.md Finding 2.*
*The original nonlinear_summary_20260411_030330.md is preserved unchanged.*
