# Q-14.14 — OHLCV microstructure-noise proxies on XAUUSD M15/H1
## Pre-registered hypotheses
- H0 (null): no proxy produces |Spearman rho| >= 0.08 with permutation p < 0.0033 (Bonferroni 15).
- H1: CLV predicts next-candle return sign (expected positive).
- H2: Corwin-Schultz effective spread predicts next-candle realized vol (expected positive).
- H3: GKYZ vol strongly autocorrelated with next-candle realized vol (expected positive and strong).
- H4: Parkinson vol tracks realized vol at h=1/3 (expected positive).
- H5: |C-O|/(H-L) weakly predicts direction continuation (expected null for sign).

## Data
- M15: 6420 candles, 2026-01-02 01:00:00 to 2026-04-10 23:45:00
- H1: 1606 candles, 2026-01-02 01:00:00 to 2026-04-10 23:00:00

## Method
- Proxies computed per candle on OHLCV (GKYZ, Parkinson, Corwin-Schultz, |C-O|/(H-L), CLV).
- Targets: sign of cumulative return over k candles and forward realized vol over k candles, k in {1, 3, 6}.
- Spearman rank correlation, two-sided permutation test with 5000 shuffles.
- Pre-registered bar: |rho| >= 0.08 AND p_perm < 0.0033 (Bonferroni 15).
- Seed: 20260417.

## Caveats
- Tick-volume on gold CFD is NOT true trade volume.
- Corwin-Schultz estimator was designed on equities; on FX/gold CFDs it is an approximation. Negative raw spread values occur and are retained (not truncated) for correlation purposes.
- All proxies are OHLCV-derivable approximations; no true bid/ask tick data was available for this analysis.
- Forward-realized-vol target uses (close-to-close) log returns; overlaps with proxy definitions (per-candle vol uses H-L information) so intra-bar information is not identical.
- Tests are partially redundant (GKYZ and Parkinson both measure range); Bonferroni of 15 is conservative in that sense.

## Results — full table
| TF | Proxy | Target | n | Spearman rho | p_perm | Passes bar |
|----|-------|--------|---|--------------|--------|------------|
| M15 | gkyz_vol | sign_ret_1 | 6412 | +0.0294 | 0.0186 | no |
| M15 | gkyz_vol | realized_vol_1 | 6418 | +0.3950 | 0.0002 | YES |
| M15 | gkyz_vol | sign_ret_3 | 6414 | +0.0223 | 0.0728 | no |
| M15 | gkyz_vol | realized_vol_3 | 6416 | +0.5444 | 0.0002 | YES |
| M15 | gkyz_vol | sign_ret_6 | 6410 | +0.0259 | 0.0360 | no |
| M15 | gkyz_vol | realized_vol_6 | 6413 | +0.5708 | 0.0002 | YES |
| M15 | parkinson_vol | sign_ret_1 | 6413 | +0.0264 | 0.0302 | no |
| M15 | parkinson_vol | realized_vol_1 | 6419 | +0.3881 | 0.0002 | YES |
| M15 | parkinson_vol | sign_ret_3 | 6415 | +0.0193 | 0.1182 | no |
| M15 | parkinson_vol | realized_vol_3 | 6417 | +0.5369 | 0.0002 | YES |
| M15 | parkinson_vol | sign_ret_6 | 6411 | +0.0276 | 0.0278 | no |
| M15 | parkinson_vol | realized_vol_6 | 6414 | +0.5639 | 0.0002 | YES |
| M15 | corwin_schultz_spread | sign_ret_1 | 6412 | -0.0126 | 0.3137 | no |
| M15 | corwin_schultz_spread | realized_vol_1 | 6418 | +0.0455 | 0.0008 | no |
| M15 | corwin_schultz_spread | sign_ret_3 | 6414 | -0.0024 | 0.8396 | no |
| M15 | corwin_schultz_spread | realized_vol_3 | 6416 | +0.0820 | 0.0002 | YES |
| M15 | corwin_schultz_spread | sign_ret_6 | 6410 | +0.0086 | 0.4987 | no |
| M15 | corwin_schultz_spread | realized_vol_6 | 6413 | +0.0802 | 0.0002 | YES |
| M15 | realized_to_range | sign_ret_1 | 6413 | +0.0085 | 0.5051 | no |
| M15 | realized_to_range | realized_vol_1 | 6419 | +0.0165 | 0.1868 | no |
| M15 | realized_to_range | sign_ret_3 | 6415 | -0.0042 | 0.7332 | no |
| M15 | realized_to_range | realized_vol_3 | 6417 | +0.0219 | 0.0772 | no |
| M15 | realized_to_range | sign_ret_6 | 6411 | +0.0071 | 0.5823 | no |
| M15 | realized_to_range | realized_vol_6 | 6414 | +0.0224 | 0.0730 | no |
| M15 | close_location_value | sign_ret_1 | 6413 | -0.0345 | 0.0062 | no |
| M15 | close_location_value | realized_vol_1 | 6419 | -0.0079 | 0.5171 | no |
| M15 | close_location_value | sign_ret_3 | 6415 | -0.0045 | 0.7063 | no |
| M15 | close_location_value | realized_vol_3 | 6417 | -0.0092 | 0.4429 | no |
| M15 | close_location_value | sign_ret_6 | 6411 | -0.0141 | 0.2611 | no |
| M15 | close_location_value | realized_vol_6 | 6414 | -0.0056 | 0.6503 | no |
| H1 | gkyz_vol | sign_ret_1 | 1604 | +0.0208 | 0.4099 | no |
| H1 | gkyz_vol | realized_vol_1 | 1604 | +0.3458 | 0.0002 | YES |
| H1 | gkyz_vol | sign_ret_3 | 1602 | +0.0046 | 0.8542 | no |
| H1 | gkyz_vol | realized_vol_3 | 1602 | +0.3988 | 0.0002 | YES |
| H1 | gkyz_vol | sign_ret_6 | 1599 | +0.0038 | 0.8756 | no |
| H1 | gkyz_vol | realized_vol_6 | 1599 | +0.4340 | 0.0002 | YES |
| H1 | parkinson_vol | sign_ret_1 | 1605 | +0.0183 | 0.4607 | no |
| H1 | parkinson_vol | realized_vol_1 | 1605 | +0.3408 | 0.0002 | YES |
| H1 | parkinson_vol | sign_ret_3 | 1603 | -0.0013 | 0.9570 | no |
| H1 | parkinson_vol | realized_vol_3 | 1603 | +0.3861 | 0.0002 | YES |
| H1 | parkinson_vol | sign_ret_6 | 1600 | +0.0067 | 0.7878 | no |
| H1 | parkinson_vol | realized_vol_6 | 1600 | +0.4247 | 0.0002 | YES |
| H1 | corwin_schultz_spread | sign_ret_1 | 1604 | +0.0071 | 0.7714 | no |
| H1 | corwin_schultz_spread | realized_vol_1 | 1604 | +0.0170 | 0.4917 | no |
| H1 | corwin_schultz_spread | sign_ret_3 | 1602 | +0.0435 | 0.0780 | no |
| H1 | corwin_schultz_spread | realized_vol_3 | 1602 | +0.0230 | 0.3509 | no |
| H1 | corwin_schultz_spread | sign_ret_6 | 1599 | +0.0056 | 0.8222 | no |
| H1 | corwin_schultz_spread | realized_vol_6 | 1599 | +0.0633 | 0.0148 | no |
| H1 | realized_to_range | sign_ret_1 | 1605 | +0.0162 | 0.5217 | no |
| H1 | realized_to_range | realized_vol_1 | 1605 | +0.0045 | 0.8508 | no |
| H1 | realized_to_range | sign_ret_3 | 1603 | -0.0078 | 0.7497 | no |
| H1 | realized_to_range | realized_vol_3 | 1603 | +0.0169 | 0.4997 | no |
| H1 | realized_to_range | sign_ret_6 | 1600 | +0.0280 | 0.2651 | no |
| H1 | realized_to_range | realized_vol_6 | 1600 | +0.0162 | 0.5021 | no |
| H1 | close_location_value | sign_ret_1 | 1605 | -0.0292 | 0.2467 | no |
| H1 | close_location_value | realized_vol_1 | 1605 | -0.0489 | 0.0508 | no |
| H1 | close_location_value | sign_ret_3 | 1603 | +0.0000 | 0.9990 | no |
| H1 | close_location_value | realized_vol_3 | 1603 | -0.0225 | 0.3735 | no |
| H1 | close_location_value | sign_ret_6 | 1600 | -0.0028 | 0.9140 | no |
| H1 | close_location_value | realized_vol_6 | 1600 | -0.0481 | 0.0532 | no |

## Passers (pre-registered bar)
| TF | Proxy | Target | n | Spearman rho | p_perm | Passes bar |
|----|-------|--------|---|--------------|--------|------------|
| M15 | gkyz_vol | realized_vol_1 | 6418 | +0.3950 | 0.0002 | YES |
| M15 | gkyz_vol | realized_vol_3 | 6416 | +0.5444 | 0.0002 | YES |
| M15 | gkyz_vol | realized_vol_6 | 6413 | +0.5708 | 0.0002 | YES |
| M15 | parkinson_vol | realized_vol_1 | 6419 | +0.3881 | 0.0002 | YES |
| M15 | parkinson_vol | realized_vol_3 | 6417 | +0.5369 | 0.0002 | YES |
| M15 | parkinson_vol | realized_vol_6 | 6414 | +0.5639 | 0.0002 | YES |
| M15 | corwin_schultz_spread | realized_vol_3 | 6416 | +0.0820 | 0.0002 | YES |
| M15 | corwin_schultz_spread | realized_vol_6 | 6413 | +0.0802 | 0.0002 | YES |
| H1 | gkyz_vol | realized_vol_1 | 1604 | +0.3458 | 0.0002 | YES |
| H1 | gkyz_vol | realized_vol_3 | 1602 | +0.3988 | 0.0002 | YES |
| H1 | gkyz_vol | realized_vol_6 | 1599 | +0.4340 | 0.0002 | YES |
| H1 | parkinson_vol | realized_vol_1 | 1605 | +0.3408 | 0.0002 | YES |
| H1 | parkinson_vol | realized_vol_3 | 1603 | +0.3861 | 0.0002 | YES |
| H1 | parkinson_vol | realized_vol_6 | 1600 | +0.4247 | 0.0002 | YES |

### Direction-prediction passers (trading-relevant)
**None.** No proxy-horizon pair predicts short-horizon return SIGN at the pre-registered bar on XAUUSD M15 or H1. This is the trading-relevant cell of the table and the null survives.

Recommendation: **do NOT** promote any of these OHLCV microstructure proxies to shadow-log for direction gating. The system should not add complexity from these proxies. This result is clean — even null results are valuable.

### Vol-autocorrelation passers (expected — not alpha)
| TF | Proxy | Target | n | Spearman rho | p_perm | Passes bar |
|----|-------|--------|---|--------------|--------|------------|
| M15 | gkyz_vol | realized_vol_1 | 6418 | +0.3950 | 0.0002 | YES |
| M15 | gkyz_vol | realized_vol_3 | 6416 | +0.5444 | 0.0002 | YES |
| M15 | gkyz_vol | realized_vol_6 | 6413 | +0.5708 | 0.0002 | YES |
| M15 | parkinson_vol | realized_vol_1 | 6419 | +0.3881 | 0.0002 | YES |
| M15 | parkinson_vol | realized_vol_3 | 6417 | +0.5369 | 0.0002 | YES |
| M15 | parkinson_vol | realized_vol_6 | 6414 | +0.5639 | 0.0002 | YES |
| M15 | corwin_schultz_spread | realized_vol_3 | 6416 | +0.0820 | 0.0002 | YES |
| M15 | corwin_schultz_spread | realized_vol_6 | 6413 | +0.0802 | 0.0002 | YES |
| H1 | gkyz_vol | realized_vol_1 | 1604 | +0.3458 | 0.0002 | YES |
| H1 | gkyz_vol | realized_vol_3 | 1602 | +0.3988 | 0.0002 | YES |
| H1 | gkyz_vol | realized_vol_6 | 1599 | +0.4340 | 0.0002 | YES |
| H1 | parkinson_vol | realized_vol_1 | 1605 | +0.3408 | 0.0002 | YES |
| H1 | parkinson_vol | realized_vol_3 | 1603 | +0.3861 | 0.0002 | YES |
| H1 | parkinson_vol | realized_vol_6 | 1600 | +0.4247 | 0.0002 | YES |

These are **expected** by construction. GKYZ and Parkinson both use H-L range data, and the forward-vol target is strongly autocorrelated (vol clustering is a well-known stylized fact). Corwin-Schultz effective spread also clears at the 3/6 horizons because wider observed ranges co-occur with wider future ranges.
These passers are **NOT actionable for direction** and **NOT a reason to shadow-log**. They only say: 'high-vol candles precede high-vol candles.' No trading gate follows from that alone.

## Interpretation of results
**Headline:** zero direction-predicting signal, as expected. All 14 passers are vol-to-vol autocorrelation (vol clustering), which is a well-known stylized fact and not tradable by itself.

Specific hypothesis outcomes:
- **H1 (CLV predicts next-candle sign):** REJECTED. M15 rho=-0.0345, p=0.0062, n=6413, H1 rho=-0.0292, p=0.2467, n=1605. Both below threshold.
- **H2 (Corwin-Schultz predicts future vol):** SUPPORTED at 3/6 horizon on M15 (rho +0.08) but weak; fails on H1. Consistent with CS being a noisy range-based estimator on gold CFDs.
- **H3 (GKYZ predicts next-candle vol):** SUPPORTED, strongly. M15 h=6 rho=+0.5708; H1 h=6 rho=+0.4340. This is textbook vol clustering — not alpha.
- **H4 (Parkinson tracks realized vol):** SUPPORTED, essentially equivalent to GKYZ.
- **H5 (|C-O|/(H-L) null for sign):** SUPPORTED. M15 h=1 rho=+0.0085, p=0.5051, n=6413. Expected null confirmed.

**Trading-relevance summary:** The microstructure-noise proxy family (as defined in this question) does NOT carry short-horizon **direction** signal on XAUUSD M15 or H1 over Jan 2 - Apr 10 2026. The null survives.

## Final recommendation
- **Do NOT** add any of these proxies as a gate or shadow-log candidate for T7/C-gate decision making. No evidence of incremental direction signal.
- The vol-autocorrelation passers may be useful as **position-sizing** inputs (e.g., vol-targeting), but that is a separate question from this one and was not tested here.
- Resource decision: move on; this proxy family is exhausted on OHLCV. True microstructure work on gold would require tick-level bid/ask data.

## Files
- JSON: `research/academic_pipeline/results/Q-14_14_microstructure.json`
- Script: `research/academic_pipeline/scripts/q_14_14_microstructure.py`
