# Worker C Implementation And Test Ideas

Date: 2026-05-15
Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

This file translates all material sources actually used in `SOURCE_LEDGER_2026-05-15.jsonl` into mechanically computable GTOS research ideas. It is not a ranked top-N list. The sequence is grouped by mechanism family, and every item has a corresponding `H###` row in `HYPOTHESIS_LEDGER_2026-05-15.jsonl`.

## A. Orderflow And Microstructure Features

Implementation candidates:

- `I001`: Best-queue OFI feature builder. Compute signed changes in best bid/ask queues over event-time and wall-clock buckets, normalized by local depth. Candidate feature names: `ofi_5s_z`, `ofi_30s_z`, `ofi_depth_norm`, `ofi_slope`, `ofi_last_touch_sign`.
- `I002`: Queue depletion veto. For each pre-entry touch, calculate protective-side queue depletion speed and adverse-side build-up. Emit `adverse_queue_depletion_percentile`.
- `I003`: CVD divergence classifier. Reset CVD by session/KZ/fix window; compute price-vs-CVD higher-low/lower-high divergence before entry.
- `I004`: Sweep toxicity classifier. After a sweep, separate persistent flow in sweep direction from exhaustion/reversal flow.
- `I005`: Boundary absorption detector. At OB/FVG/breaker boundary, measure aggressive delta that fails to move price beyond N ticks.
- `I006`: Liquidity-speed state. Calculate volume per second, delta per second, range per volume, and spread-adjusted speed around candidate entry.

First tests:

- Start with feature-only joins on current candidate windows and Sierra/Databento source windows where present.
- If depth is not available for a historical window, do not backfill true OFI. Mark the row as `source_blocked_depth_absent` and optionally compute a lower-evidence tick proxy.
- Compare each feature against price-only controls, volume-only controls, sign-shuffled orderflow, and neighbor-window placebo events.

Why this matters:

- The strongest direct import is Cont-Kukanov-Stoikov OFI: price impact over short intervals is mechanically tied to order-book imbalance more robustly than trade volume alone (`S001`).
- Sierra-owned footprint/CVD fields are a practical source path for no-API mechanical research (`S003`, `S006`).

## B. Volume Profile And Auction-Value Structure

Implementation candidates:

- `I007`: Profile descriptor builder. Freeze session template, profile period, tick binning, and POC/VAH/VAL method before joining to candidates.
- `I008`: HVN/LVN target-family comparator. Replace or supplement fixed-R targets with nearest POC/HVN/LVN/profile-high/profile-low path targets in research-only replay.
- `I009`: POC migration regime feature. Calculate slope and persistence of session/KZ POC migration.
- `I010`: Value-area reentry challenger. Generate standalone candidate events when price exits value area, re-enters, accepts, and targets POC or opposite value edge.

First tests:

- Compute profile descriptors with futures real volume when possible and label CFD/tick-volume profile as lower evidence.
- Add platform-consistency guardrails: profile period and ticks-per-volume-bar must be frozen and recorded (`S004`).
- Controls: shifted fake POC/VAH/VAL levels, session high/low levels, round-number levels, and profile computed from future-contaminated windows as a leakage sentinel that must be rejected.

Why this matters:

- Volume Profile gives a direct mechanical representation of accepted value, POC, and value area (`S005`), which can become entry context, target selection, and avoid-friction logic.

## C. Session, Benchmark, And Fix Effects

Implementation candidates:

- `I011`: LBMA gold/silver fix calendar. Generate DST-aware AM/PM fix flags for 10:30 and 15:00 London time.
- `I012`: Post-fix impulse event study. Measure pre-fix impulse, auction-window realized volatility, post-fix continuation/reversal, and first-passage outcomes.
- `I013`: Fix-window spread/slippage hazard. Join spread, slippage, no-fill, and pending-limit lifecycle rows to fix windows.
- `I014`: 30-second auction-round event buckets around LBMA fix windows, matching IBA specification granularity.
- `I015`: WMR 4pm FX fix window flags for GBPUSD, USDJPY, and GBPJPY.
- `I016`: Pre-fix trend-following versus post-fix reversal split.
- `I017`: Benchmark-window liquidity regime label for FX execution and monitoring.

First tests:

- Build event-window studies before any candidate outcome interpretation.
- Use pseudo-fix controls inside the same session and same day.
- Separate signal from execution friction: a fix window can be useful as an avoid filter even if direction is not predictive.

Why this matters:

- LBMA and ICE provide official gold auction times and specifications (`S007`, `S008`).
- FCA, Evans, and IOSCO establish that WMR 4pm is a benchmark window with distinct market behavior and liquidity/impact concerns (`S009`, `S010`, `S011`).

## D. Hazard, Duration, And Survival Features

Implementation candidates:

- `I018`: Candidate waiting-time hazard features: `time_since_last_candidate`, `candidate_cluster_count`, `duration_residual_by_symbol_session_regime`.
- `I019`: Pending-limit time-to-fill survival model for cancel/reprice research.
- `I020`: Price-change duration regime for impulse versus chop.

First tests:

- Reuse GTOS opportunity lifecycle and pending-limit lifecycle logs where source-safe.
- Use duration models as descriptors first, not optimized execution policy.
- Controls: raw time-of-day, bar-count clock, candidate count, ATR, randomized event order.

Why this matters:

- Engle and Russell's ACD framework directly motivates event-time/duration modeling for irregular trade and price-change arrivals (`S012`).
- It also connects to active GTOS HAZ001-style waiting-time evidence without making a promotion claim.

## E. Regime, Trend, And Portfolio Allocation

Implementation candidates:

- `I021`: Volatility-targeted risk simulator with prop-rule caps.
- `I022`: Volatility-state strategy router: expansion, stable, shock.
- `I023`: Kill-zone volatility budget allocator.
- `I024`: Time-series momentum high-timeframe side filter.
- `I025`: Trend-age exhaustion filter.

First tests:

- Use ex-ante volatility/trend features only.
- Compare against current D1/H4 bias and existing drawdown/risk controls.
- Run Monte Carlo/path-R simulations as research-only and label them synthetic, not broker-realized.

Why this matters:

- Volatility-managed portfolios motivate risk reduction in high-volatility states (`S013`).
- Time-series momentum motivates own-market multi-horizon trend states as regime context (`S014`).

## F. Cross-Market Confirmation And Divergence

Implementation candidates:

- `I026`: Generic futures/proxy confirmation framework for XAUUSD/GC, XAGUSD/SI, NAS100/NQ, US30/YM, USDJPY/6J, GBPUSD/6B.
- `I027`: COMEX gold lead-lag confirmation for XAUUSD.
- `I028`: Scale-specific lead-lag map, separating sub-minute, M1-M5, M15, and H1.
- `I029`: Index futures cross-orderflow liquidity-propagation veto.
- `I030`: Cross-asset liquidity shock monitor.
- `I031`: Official contract-normalized proxy feature registry.
- `I032`: Proxy-session eligibility filter using official exchange hours and contract metadata.

First tests:

- Build a proxy map and eligibility ledger before using proxy data.
- Run lead-lag and confirmation tests before direct strategy tests.
- Controls: reversed lag direction, unrelated proxy placebo, self-lag only, holiday/session stale-proxy flags.

Why this matters:

- High-frequency lead-lag estimation can handle asynchronous data (`S015`).
- OFR cross-asset orderflow evidence supports liquidity and price-discovery propagation as a real mechanism class (`S016`).
- Gold-futures evidence points to COMEX as a material price-discovery center in the cited sample (`S017`).
- CME specs are needed for correct normalization and proxy contracts (`S018`, `S019`).

## G. Execution, Slippage, And Fill Realism

Implementation candidates:

- `I033`: Fill probability model for pending limits.
- `I034`: Marketable-limit versus passive-limit challenger replay.
- `I035`: Speed-limited execution state machine.
- `I036`: No-arbitrage execution-cost sanity check.

First tests:

- Replay existing pending-limit lifecycle rows where source-safe.
- Separate fill probability from trade profitability.
- Stress every candidate with spread, slippage, and conservative impact assumptions.
- Add adversarial zero-signal round-trip tests so cost assumptions cannot manufacture profit.

Why this matters:

- Execution literature explicitly combines limit/market choice, fill uncertainty, impact, and speed limits (`S020`).
- Market-impact assumptions must not permit dynamic arbitrage or unrealistic repeated round trips (`S021`).

## H. Public Macro/Positioning Data

Implementation candidates:

- `I037`: COT positioning regime join for GC/SI/6J/6B and index futures.
- `I038`: COT concentration risk avoid filter.
- `I039`: Fed H10 dollar/FX regime join.
- `I040`: H10 revision/data-quality guardrail.

First tests:

- Build source-hashed downloads and as-of release ledger before any join.
- For COT, join by release availability, not the Tuesday report date.
- Treat these as slow context filters only; they cannot explain intraday timing by themselves.

Why this matters:

- CFTC provides official public weekly positioning and historical files (`S022`, `S023`, `S024`).
- Fed H10 provides official daily FX data and revision notices (`S025`).

## I. Statistical Validation Rails

Implementation candidates:

- `I041`: Moonshot trial-count and DSR/PBO validation debt ledger.
- `I042`: Purged/embargoed combinatorial validation harness for frozen candidate families.

First tests:

- Before ranking any strategy result, require each row to carry `family_id`, `parameter_set_id`, `denominator_id`, `outcome_peek_status`, `source_partition`, and `trial_count_scope`.
- Use DSR/PBO only when metric assumptions are valid; otherwise record exact non-applicability and use stricter holdout/control language.

Why this matters:

- PBO and DSR directly address the moonshot factory's central risk: many generated ideas will produce false positives unless trial debt is preserved (`S026`, `S027`).

## J. Signal Processing And Control Theory

Implementation candidates:

- `I043`: Kalman hidden fair-value/basis state.
- `I044`: Kalman-HMM dynamic proxy regime.
- `I045`: Causal state estimator for trend/noise decomposition.
- `I046`: Cross-market pair dislocation challenger.
- `I047`: CUSUM drift monitor for candidate rate, OB continuation, slippage, spread, and OFI-response slope.
- `I048`: CUSUM structural-break filter for market regimes.
- `I049`: Causal wavelet/multiscale impulse descriptor.
- `I050`: Wavelet-denoised swing detector challenger.

First tests:

- Enforce causal filtering only. Centered or symmetric filters are leakage sentinels and must fail no-leak checks.
- Compare against simple baselines: EMA, ATR, rolling OLS, static hedge ratio, current structure detector.
- Trial-count debt is high for wavelet/GP/automated-search ideas. They must enter the validation debt ledger before any result ranking.

Why this matters:

- Kalman filtering provides a mechanically expressible way to estimate hidden state from noisy observations (`S028`).
- Kalman-HMM work gives a directly translatable pattern for dynamic hedge/basis and regime states (`S029`).
- CUSUM gives a process-control route for detecting structural breaks (`S030`).
- Wavelet sources motivate multiscale descriptors but require strict causal implementation and overfit controls (`S031`, `S032`).

## Immediate Worker-C Recommended Build Order For Parent Sprint

This is a practical build order, not a top-N claim. The full idea set remains in the JSONL ledgers.

1. Build the validation debt ledger first (`I041`, `I042`), because the moonshot factory is explicitly testing many ideas.
2. Build source-contract metadata for proxy futures and profile/orderflow fields (`I031`, `I032`, `I007`) so downstream features are normalized and no-leak.
3. Implement low-cost deterministic event calendars (`I011`, `I015`) because fix/session labels are cheap and immediately testable on existing bars.
4. Implement OFI/CVD/profile feature joins where owned Sierra/Databento data exists (`I001`, `I003`, `I007`).
5. Build pending-limit survival and execution-cost sanity checks (`I019`, `I033`, `I036`) because execution realism can turn apparent signal into no-trade or routing intelligence.
6. Route signal-processing challengers (`I043`, `I047`, `I049`, `I050`) only after causal/no-leak filter checks are in place.
