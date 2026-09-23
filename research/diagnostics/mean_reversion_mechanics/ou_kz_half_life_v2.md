# OU Half-Life: KZ-Only Rerun (Bug-Fixed)

**Generated:** 20260411_100923 UTC
**Script:** run_kz_ou_halflife_v2.py
**Fix applied:** `df["time"].diff().dt.total_seconds().iloc[1:].values` replaces `np.diff(df["time"].astype(np.int64)) / 1e9`
**Source file:** data/historical/XAUUSD_H1.csv

---

## Results

### All-Hours (baseline, no change expected)

| Metric | Value |
|--------|-------|
| Half-life (H1 bars) | 23.05 |
| 95% CI | [20.21, 25.88] |
| beta | -0.030073 |
| n_obs | 14514 |
| Note | Audit predicted: 25.4 bars (unchanged) |

### KZ-Only XAUUSD H1 (affected test)

| Metric | Value |
|--------|-------|
| Half-life (H1 bars) | **17.05** |
| 95% CI | **[15.13, 18.98]** |
| beta | -0.040646 |
| n_obs | 4451 |
| Note | Prior (bug): 20.9 bars [16.5, 25.3]. Audit predicted: 17.1 [15.1, 19.0]. |

## Impact on Trailing Stop Calibration

| Scenario | OU Half-Life | Trailing Timeout (1.5×) |
|----------|-------------|------------------------|
| Prior (buggy) | 20.9 H1 bars | 31 H1 bars |
| Corrected | 17.05 H1 bars | 25.6 H1 bars |

**Direction unchanged:** KZ-only reversion (17.05 bars) is faster than all-hours (23.05 bars). The gap correction strengthens this finding.

---

*This file supersedes the KZ-only OU half-life reported in mean_reversion_summary_20260411_025154.md.*
*No other diagnostic conclusions are affected — see PEER_REVIEW_AUDIT.md §Finding 1.*
