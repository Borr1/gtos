# Expanded OOS Full-Unblocking Owner Deep-Dive Report - 2026-05-04

**Scope:** owner-facing research synthesis  
**Underlying research lane:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Live trading changes:** none  
**AI/API calls used in the expanded-OOS pass:** `0`  
**New Databento spend in the expanded-OOS pass:** `$0`  
**Primary final artifact:** `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.md`  

## 1. Executive Verdict

The expanded-OOS full-unblocking research did **not** produce a new live-trading rule.

It did produce something important: it converted a vague blocker, "we need broader data / more OOS / more instruments / orderflow depth," into a structured research system with known inputs, known conversion paths, known replay paths, known source mismatches, known label constraints, and a concrete next plan.

The local May 4 unblocking pass is complete, but it remains **not promotable**. The final synthesis status is:

`LOCAL_FULL_UNBLOCKING_PASS_SYNTHESIZED_NOT_PROMOTABLE`

The pass now has:

| Completion Standard Item | Status |
|---|---|
| Adapter/converter status for every first-wave family | `MET` |
| At least one working converted-source replay path | `MET` |
| Replay or label-status artifacts for every first-wave family | `MET_AS_STATUS_ARTIFACTS_NOT_OUTCOME_REPLAYS` |
| Candidate survival table by evidence class | `MET_BY_THIS_SYNTHESIS` |
| Instrument/source expansion scorecard | `MET_BY_THIS_SYNTHESIS` |
| Data-quality table | `MET_BY_THIS_SYNTHESIS` |
| Opened/burned/reserved slice ledger | `MET_BY_THIS_SYNTHESIS` |
| Cost ledger | `MET` |
| Failure/decay/source-mismatch attribution | `MET_BY_THIS_SYNTHESIS` |
| Final synthesis with `NO_PROMOTION_VERDICT` | `MET_BY_THIS_ARTIFACT` |

The main conclusion:

> We are closer to building a powerful trading operating system, not because we found a deployable edge, but because we removed major data/replay/source-readiness blockers and clarified exactly what must be captured next before advanced strategy, orderflow, and path-management improvements can be honestly promoted.

## 2. The Research Stage We Are At Now

The correct stage label is:

`DATA_AND_REPLAY_INFRASTRUCTURE_UNBLOCKED_FOR_FIRST_WAVE_RESEARCH_NOT_PROMOTABLE`

More plainly:

- The system is no longer blocked by missing Sierra `.scid` converters.
- The system is no longer blocked by having no Sierra `.depth` parser/extractor.
- The first-wave source families are now mapped.
- Every first-wave family has adapter/conversion status.
- Every first-wave family has either replay status or label-status artifact.
- Several futures proxy/depth families are now classified as clean, caution, or blocked.
- The research has not yet created enough actual, unseen, broker-realized outcome evidence for promotion.

This is a **research-machine maturity step**, not a live alpha deployment step.

## 3. Source Artifacts Used For This Report

Primary artifacts:

- `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.md`
- `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.json`
- `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_PROGRESS_CHECKPOINT_2026-05-04.json`
- `research/program_control/EXPANDED_OOS_FIRST_WAVE_FAMILY_STATUS_MATRIX_2026-05-04.md`
- `research/program_control/EXPANDED_OOS_FIRST_WAVE_FAMILY_STATUS_MATRIX_2026-05-04.json`
- `research/program_control/EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_2026-05-04.md`
- `research/program_control/EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_2026-05-04.json`
- `research/program_control/EXPANDED_OOS_FIRST_WAVE_BOUNDED_CONVERSION_STATUS_2026-05-04.json`
- `research/program_control/EXPANDED_OOS_SIERRA_DEPTH_BATCH_PARITY_STATUS_2026-05-04.md`
- `research/program_control/EXPANDED_OOS_SIERRA_DEPTH_BATCH_PARITY_STATUS_2026-05-04.json`
- `research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_SYNTHESIS_2026-05-04.md`
- `research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_SYNTHESIS_2026-05-04.json`
- `.context/00_core/research_current_state.md`
- `.context/LIVE_STATE.md`

Supporting doctrine:

- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/quick_reference_card.md`

## 4. What Was Actually Built

### 4.1 Sierra `.scid` To GTOS OHLCV Converter

Research-only tooling was built to convert Sierra Chart intraday files into GTOS-compatible OHLCV roots.

It outputs:

- M1 CSV
- M5 CSV
- M15 CSV
- H1 CSV
- D1 CSV
- manifest with source metadata
- evidence class
- price transform
- row counts
- gap counts
- invalid record counts
- source hash
- `NO_PROMOTION_VERDICT`

Targeted verification for the converter passed:

| Test Command | Result |
|---|---|
| `python -m pytest tests\test_inspect_sierra_scid.py tests\test_convert_sierra_scid_to_ohlcv.py -q -p no:cacheprovider` | `6 passed` |

### 4.2 First-Wave Broad Conversion

After the first NQ pilot, the pass expanded to the first-wave families.

Broad bounded conversion results:

| Metric | Value |
|---|---:|
| CSV files produced | `95` |
| Source mappings | `19` |
| Required first-wave families | `11` |
| Families with OHLCV adapter status | `11` |
| Families with converted M15 rows | `11` |
| Conversion slice | `2026-04-15T00:00:00Z` to `2026-04-18T00:00:00Z` |
| Timeframes | M1, M5, M15, H1, D1 |
| New Databento cost | `$0` |
| AI/API calls | `0` |

### 4.3 Sierra `.depth` Extractor

Research-only tooling was built to reconstruct local Sierra market-depth books and emit Databento MBP10-compatible feature fields.

Depth features include:

- total top-10 bid depth
- total top-10 ask depth
- depth10 imbalance
- thinness fields
- max bid wall
- max ask wall
- near/far diagnostics
- mid-change
- sample counts
- top-20 diagnostics

Targeted verification passed:

| Test Command | Result |
|---|---|
| `python -m pytest tests\test_extract_sierra_depth_features.py tests\test_inspect_sierra_scid.py tests\test_convert_sierra_scid_to_ohlcv.py -q -p no:cacheprovider` | `11 passed` |

Sampling audit verification passed:

| Test Command | Result |
|---|---|
| `python -m pytest tests\test_audit_sierra_depth_sampling_parity.py tests\test_extract_sierra_depth_features.py tests\test_inspect_sierra_scid.py tests\test_convert_sierra_scid_to_ohlcv.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_sierra_depth_audit_combined` | `15 passed` |

### 4.4 First-Wave Label-Status Audit

The initial matrix showed `5` first-wave families still lacked replay/label status:

- `EURUSD/6E`
- `ES/MES`
- `CL`
- `ZN`
- `VIX/VXM`

The follow-up label-status audit closed that gap without opening outcomes.

| Label-Status Audit Metric | Value |
|---|---:|
| Target families from matrix | `5` |
| Families with label-status artifact | `5` |
| Families replay-ready under current frozen raw-OHLC spec | `0` |
| Families label-status-only with no registered cohort | `2` |
| Families control-status-only | `3` |
| Families missing conversion status | `0` |
| Opened outcome slices | `0` |
| Opened outcome rows | `0` |

Focused tests passed:

| Test Command | Result |
|---|---|
| `python -m pytest tests\test_expanded_oos_family_label_status.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_expanded_oos_label_status` | `5 passed` |

### 4.5 Final Full-Unblocking Synthesis

The final synthesis assembled:

- completion-standard audit
- candidate survival by evidence class
- instrument/source expansion scorecard
- data-quality table
- opened/burned/reserved slice ledger
- cost ledger
- failure/decay/source-mismatch attribution
- promotion-readiness statement
- remaining research triggers

Focused tests passed:

| Test Command | Result |
|---|---|
| `python -m pytest tests\test_expanded_oos_family_label_status.py tests\test_synthesize_expanded_oos_full_unblocking.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_expanded_oos_full_unblocking_final` | `10 passed` |

## 5. Instrument-By-Instrument Outcome

This is the most important table for understanding what worked and what did not.

| Family | Data Status | Replay / Label Outcome | Depth Outcome | Research Classification |
|---|---|---|---|---|
| NAS100/NDX100 with NQ/MNQ | converted | path works, no frozen cohort match | NQ exact cached MBP10 match | promising diagnostic |
| US30/US30_cash with YM/MYM | converted | M15 actions, V2 MTF all no-entry | YM exact cached MBP10 match | neutral diagnostic |
| XAUUSD with XAUUSD.scid and GC/MGC | converted | small-n same-market diagnostic positive | GC near match | promising small-n source transfer |
| XAGUSD with SI/SIL | converted, sparse | M15 positive but V2 MTF not portable | SI source/depth-definition blocked | blocked source mismatch |
| USDJPY with 6J | converted, inverse transform | path works, no actions | not audited | neutral path-only |
| GBPUSD with 6B | converted | path works, no actions | sampling-policy alignment required | neutral path-only, depth caution |
| EURUSD with EURUSD/6E | converted | not opened, no registered cohort | not audited | blocked by missing registered cohort |
| S&P with ES/MES | converted | not opened control/expansion, no registered cohort | not audited | blocked by missing registered cohort |
| CL macro/liquidity proxy/control | converted | not opened control | not audited | control only |
| ZN macro/rates proxy/control | converted | not opened control | not audited | control only |
| VIX/VXM controls | converted, VXMM sparse | not opened control | not audited | control only |

## 6. Exact Replay Numbers

Opened replay and diagnostic slices:

| Batch | Replay Type | Slice | Rows Replayed | Actions / Takes | Resolved R n | Mean R | Status |
|---|---|---|---:|---:|---:|---:|---|
| `sierra_nq_to_nas100_pilot_20260504` | M15 prequential | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | `76` | `0` | `0` | n/a | `PATH_WORKS_NO_FROZEN_COHORT_MATCH` |
| `sierra_xauusd_scid_to_xauusd_pilot_20260504` | M15 prequential | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | `76` | `30` | `0` | n/a | `M15_UNRESOLVED_SAME_BAR_OR_NO_ENTRY` |
| `sierra_xauusd_scid_v2_mtf_pilot_20260504` | V2 MTF | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | `76` | `30` | `5` | `+0.77465R` best variant net | `DIAGNOSTIC_POSITIVE_SMALL_N_SOURCE_TRANSFER_ONLY` |
| `sierra_ym_to_us30_cash_pilot_20260504` | M15 prequential | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | `50` | `6` | `0` | n/a | `NO_RESOLVED_OUTCOMES` |
| `sierra_ym_us30_cash_v2_mtf_pilot_20260504` | V2 MTF | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | `50` | `6` | `0` | n/a | `ALL_NO_ENTRY` |
| `sierra_6j_to_usdjpy_pilot_20260504` | M15 prequential | 2026-04-15 00:00 to 2026-04-17 17:00 UTC | `96` | `0` | `0` | n/a | `PATH_WORKS_NO_ACTIONS` |
| `sierra_6b_to_gbpusd_pilot_20260504` | M15 prequential | 2026-04-15 00:00 to 2026-04-17 17:00 UTC | `90` | `0` | `0` | n/a | `PATH_WORKS_NO_ACTIONS` |
| `sierra_si_to_xagusd_pilot_20260504` | M15 prequential | 2026-04-15 00:00 to 2026-04-17 17:00 UTC | `72` | `6` | `4` | `+1.5R` | `M15_POSITIVE_BUT_PROXY_AND_MTF_NOT_PORTABLE` |
| `sierra_si_xagusd_v2_mtf_pilot_20260504` | V2 MTF | 2026-04-15 00:00 to 2026-04-17 17:00 UTC | `72` | `6` | `0` | n/a | `ALL_NO_ENTRY_ON_LOWER_TIMEFRAME` |

### 6.1 The Most Important Replay Lesson

The XAGUSD/SI row is the warning case.

At M15 level:

- rows replayed: `72`
- actions: `6`
- resolved outcomes: `4`
- mean R: `+1.5R`

That looks good.

But lower-timeframe V2 MTF:

- rows replayed: `72`
- take rows seen: `6`
- resolved lower-timeframe entries: `0`
- status: `ALL_NO_ENTRY_ON_LOWER_TIMEFRAME`

Interpretation:

> The M15 result is not trustworthy by itself. Once fill/path realism is introduced, the apparent positive result disappears. This proves that lower-timeframe path and fill reconstruction is mandatory before any live rule or path-management rule is considered.

### 6.2 The Most Promising Replay Diagnostic

The strongest strategy-related clue is XAUUSD same-market source transfer.

XAUUSD Sierra V2 MTF:

- rows replayed: `76`
- take rows seen: `30`
- resolved reference n: `5`
- best structural variant after `0.05R` cost: `STRUCT_BOS_LEVEL_V2`
- best structural net mean R after cost: `+0.77465R`
- J46 net mean R after cost: `-0.078468R`

Interpretation:

> This is interesting, but not strong enough for promotion. `n=5` is too small. The right next step is to extend this under frozen slices, not deploy it.

## 7. Exact Depth-Parity Numbers

Depth batch status across five registered event windows:

| GTOS Symbol | Futures Symbol | Event ID | Sierra Samples | Cached Databento Samples | Nonzero Registered Field Deltas | Max Abs Registered Delta | Status |
|---|---|---|---:|---:|---:|---:|---|
| GBPUSD | `6B.v.0` | `GBPUSD_20260417T0800_candidate_34` | `683` | `632` | `9` | `51` | `MISMATCH_SAMPLE_CLOCK_OR_SOURCE_DIFF` |
| XAUUSD | `GC.v.0` | `XAUUSD_20260417T1315_candidate_76` | `900` | `900` | `6` | `2` | `NEAR_MATCH_SMALL_FIELD_DELTAS` |
| US30_cash | `YM.v.0` | `US30_cash_20260417T1545_candidate_110` | `900` | `900` | `0` | `0` | `EXACT_CACHED_MBP10_MATCH` |
| NAS100 | `NQ.v.0` | `NAS100_20260428T0730_candidate_141` | `899` | `899` | `0` | `0` | `EXACT_CACHED_MBP10_MATCH` |
| XAGUSD | `SI.v.0` | `XAGUSD_20260501T0815_candidate_443` | `719` | `741` | `9` | `26` | `MISMATCH_SOURCE_OR_DEPTH_DEFINITION_AUDIT_REQUIRED` |

### 7.1 NQ And YM

NQ and YM matched exactly.

This means:

- local Sierra depth extraction is capable of reproducing cached Databento MBP10 rows for these families,
- NQ/YM are the cleanest families for future depth diagnostics,
- still, this is source/field parity, not live CFD broker-truth validation.

### 7.2 GC

GC is near parity:

- Sierra samples: `900`
- Databento samples: `900`
- nonzero deltas: `6`
- max absolute delta: `2`

Interpretation:

GC is not exact, but the mismatch is small. It should be treated as usable only with caution and further field-definition/sampling review.

### 7.3 6B

The initial 6B mismatch looked bad:

- Sierra samples: `683`
- Databento samples: `632`
- max delta: `51`

But after common-second masking:

- common samples: `632`
- Sierra-only samples: `51`
- Databento-only samples: `0`
- common-second max delta: `5`
- all-second max delta before masking: `51`

Interpretation:

> 6B is probably not a source rejection. The main mismatch is sampling policy. The next step is common-second/declarative sampling alignment.

### 7.4 SI

SI stayed blocked after audit:

For `SIM26-COMEX`:

- Sierra samples: `719`
- Databento samples: `741`
- common samples: `718`
- all-second max delta: `25`
- common-second max delta: `25`
- common-second total-depth10 delta: `-25`
- depth10 imbalance remained materially shifted

For alternate `SILM26-COMEX`:

- Sierra samples: `722`
- Databento samples: `741`
- common samples: `679`
- all/common max delta: `25`
- not better than SIM

Interpretation:

> SI is a true source/depth-definition blocker until continuous-contract/source mapping is resolved. It should not be used in replay synthesis yet.

## 8. First-Wave Label-Status Details

The five families that lacked replay/label status were audited without opening outcomes.

| Family | Converted Source Rows | Matched Frozen Raw Replay Cohorts | Status | What It Means |
|---|---|---|---|---|
| EURUSD with EURUSD/6E | `EURUSD_6E: 268 rows, 2 gaps`; `EURUSD_SCID: 276 rows, 0 gaps` | none | `LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT` | Data exists, but strategy question must be pre-registered before outcomes. |
| S&P with ES/MES | `SPX_ES: 268 rows, 2 gaps`; `SPX_MES: 268 rows, 2 gaps` | none | `LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT` | Data exists, but no frozen cohort/question exists. |
| CL macro/liquidity proxy/control | `CL_PROXY: 268 rows, 2 gaps` | none | `LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT` | Control/context only. |
| ZN macro/rates proxy/control | `ZN_CONTROL: 268 rows, 2 gaps` | none | `LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT` | Rates/control context only. |
| VIX/VXM controls | `VIX_VXM: 247 rows, 17 gaps`; `VIX_VXMM: 107 rows, 47 gaps` | none | `LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT` | Volatility/regime control only; VXMM sparse. |

This is not a failure. It prevents fake research.

The right interpretation:

- EURUSD/6E and ES/MES are data-ready but not strategy-ready.
- CL/ZN/VIX are not direct trading validation sources.
- Opening outcomes before registering specific questions would contaminate future validation.

## 9. Candidate Survival By Evidence Class

The frozen candidate registry had six candidates/comparators.

| Candidate | Evidence Class In Final Synthesis | Result Status | Decision |
|---|---|---|---|
| `CAND-001-J46-J49-LIVE-BASELINE` | comparator | `COMPARATOR_ONLY_NO_NEW_BROKER_R` | Kept as comparator; no new broker-realized R labels created. |
| `CAND-002-V2-OB-BOUNDARY` | same-market source transfer plus futures proxy transfer | `SOURCE_TRANSFER_DIAGNOSTIC_MIXED_NOT_PROMOTABLE` | XAUUSD small-n positive, but YM/SI lower-timeframe labels unresolved or no-entry. |
| `CAND-003-V2-FVG-PATH` | discovery only | `NOT_OPENED_REQUIRES_COMPATIBLE_V2_EVENT_LOGS` | No first-wave converted-source survival claim. |
| `CAND-004-V3-FVG-ONLY-RESCUE` | discovery only | `NOT_OPENED_DEPENDS_ON_V2_EVENT_LOGS_AND_LIFECYCLE_FIELDS` | Needs V2 rows, lifecycle, pre-fill fields. |
| `CAND-005-NAS100-DEPTH-THINNESS` | futures proxy transfer | `DEPTH_PARITY_SOURCE_STATUS_ONLY_LABEL_LIMITED` | NQ/YM parity clean, labels insufficient. |
| `CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR` | simulation comparator | `SIMULATION_COMPARATOR_ONLY_NO_LIVE_RISK_CHANGE` | No risk/execution change made or allowed. |

Every row remains `NO_PROMOTION_VERDICT`.

## 10. What Worked

### 10.1 Data Unblocking Worked

The best outcome is that data is now usable.

Before this pass, Sierra `.scid` and `.depth` were mostly raw data assets. After this pass:

- `.scid` can become GTOS OHLCV roots,
- `.depth` can become comparable depth features,
- source families can be classified,
- replay can be attempted under strict evidence-class labels.

This is foundational.

### 10.2 NQ/YM Depth Parity Worked

NQ and YM matched cached Databento MBP10 exactly.

This gives high confidence that:

- Sierra depth extraction logic is correct for at least those tested families,
- future NAS100/US30 depth diagnostics can use Sierra depth with fewer source worries,
- NQ/YM are the cleanest orderflow/depth research path.

### 10.3 XAUUSD Same-Market Source Transfer Was Promising

The only strategy-like positive result worth attention:

- XAUUSD same-market source transfer,
- V2 MTF,
- `n=5`,
- best structural net mean R after cost: `+0.77465R`,
- J46 net mean R after cost: `-0.078468R`.

The mechanism is plausible because same-market XAUUSD Sierra data is closer to the traded instrument than futures proxies.

But `n=5` is too small. It is a candidate for frozen extension, not deployment.

### 10.4 6B Was Diagnosed As Fixable

The audit reduced the 6B max delta from `51` to `5` under common seconds.

This is a good result because it means:

- the data source is not obviously bad,
- the extractor is not fundamentally broken,
- the next step is engineering alignment.

### 10.5 The Discipline Worked

No live behavior changed.

No prompt changed.

No risk/execution/safety setting changed.

No AI/API call was made.

No paid Databento pull was made.

Weak evidence was not promoted.

That matters. A research system that refuses to promote weak evidence is more valuable than a system that produces exciting but false conclusions.

## 11. What Did Not Work

### 11.1 No New Live Strategy Was Validated

This pass did not produce:

- true temporal OOS validation,
- broker-realized sample floors,
- DSR-corrected p-values,
- PBO statistics,
- effective-N statistics,
- a promotion dossier.

Therefore no live strategy change is justified.

### 11.2 XAGUSD/SI Failed Under Realistic Path Reconstruction

The M15 replay looked positive.

But lower-timeframe V2 MTF showed no valid entries.

This is one of the most important negative findings:

> Coarse timeframe replay can fabricate optimism. Lower-timeframe path/fill reconstruction is mandatory.

### 11.3 EURUSD And ES/MES Could Not Be Outcome-Tested Honestly

They have data.

They do not have a registered raw-OHLC cohort/question.

Opening outcomes now would be post-hoc. So the correct status is blocked by missing registered cohort, not failed.

### 11.4 CL, ZN, And VIX Are Not Direct Strategy Validation Sources

They may become useful as:

- macro/liquidity context,
- rates context,
- volatility/regime context,
- risk filter context,
- opportunity filter context.

But they cannot validate the original instrument edge by themselves.

### 11.5 SI Depth Remains Blocked

Common-second masking did not fix the SI mismatch.

This means SI needs source/contract-definition work before any depth replay should use it.

## 12. How Far Back We Went

There are several different "how far back" answers depending on data layer.

### 12.1 Opened Expanded-OOS Sierra OHLCV Replay

The opened replay slices in this pass were mostly:

- start: `2026-04-15`
- end: `2026-04-17` or `2026-04-18`

This was intentionally bounded as a first-wave conversion/replay diagnostic.

### 12.2 Depth Event Windows

Depth parity windows reached:

| Date | Event |
|---|---|
| 2026-04-17 08:00 UTC | GBPUSD/6B candidate |
| 2026-04-17 13:15 UTC | XAUUSD/GC candidate |
| 2026-04-17 15:45 UTC | US30/YM candidate |
| 2026-04-28 07:30 UTC | NAS100/NQ candidate |
| 2026-05-01 08:15 UTC | XAGUSD/SI candidate |

### 12.3 Broader Local Inventory

The repo current-state source map reports:

| Source Layer | Local Inventory |
|---|---:|
| MT5 export manifests | `9` |
| MT5 symbol/timeframe aggregates | `44` |
| MT5 tick probes | `3` |
| MT5 live symbol specs | `22` |
| Sierra `.scid` files | `33` |
| Sierra first-wave relevant `.scid` files | `26` |
| Sierra depth files | `465` |
| Sierra depth total size | `59.701 GB` |
| External validation event logs | `8` |
| Cached Databento/orderflow files | `128` |

### 12.4 Older Mechanical Backfill

Separate from this expanded-OOS pass, the current research state records a D-11 old-label supplement:

- `465` filled F11-style mechanical rows,
- `GBPJPY=238`,
- `US30_cash=227`,
- `684` JSONL BOS/outcome rows.

That old data is useful for mechanical/source-flagged model work, but it is not live-equivalent broker/AI evidence.

## 13. How Deep We Went In The Data

### 13.1 OHLCV Depth

Converted timeframes:

- M1
- M5
- M15
- H1
- D1

That matters because M15-only can be misleading. The XAGUSD/SI result proved this.

### 13.2 Depth/Orderbook Depth

Depth extraction went to:

- Databento MBP10-compatible top-10 depth fields,
- top-20 diagnostics,
- pre-decision `END_OF_BATCH` snapshots,
- book reconstruction through canonical event close.

The largest explicitly reported extraction:

| Metric | NQ Pilot |
|---|---:|
| Records processed until canonical close | `2,738,849` |
| Batches seen until canonical close | `2,493,477` |
| Event15 samples emitted | `899` |
| Cached Databento MBP10 comparison deltas | `0` |

### 13.3 How Deep We Wanted To Go But Could Not

| Wanted Depth | Why We Could Not Go There Yet |
|---|---|
| True temporal OOS strategy validation | V2b has `0` resolved post-cutoff OB-boundary/J46 pairs. |
| Promotion-grade DSR/PBO/effective-N | Sample floors and evidence classes do not qualify. |
| Actual broker-R for all replay rows | Source-transfer/futures/control data is not broker execution truth. |
| Pending-limit fill/expiry/cancel truth | Pending-limit lifecycle telemetry is not shipped. |
| Full V3 validation | V3 needs resolved V2/V2b rows, pre-fill path, POI lifecycle, and actual fill states. |
| Full SI depth replay | SI source/depth-definition mismatch remains unresolved. |
| Pre-2024 tick/depth history | Current MT5/redacted_account retention blocks it. Needs alternate broker/provider/archive. |
| Pre-2022 all-symbol OHLCV | Current redacted_account history availability blocks it. |
| Broad historical MBO | Cost/runtime/labels not ready; needs predeclared question and optimized extractor. |

## 14. Data Constraints

The major constraints were not compute intelligence. They were label and source truth.

### 14.1 Label Constraints

Current research state records:

- actual broker-R labels for orderflow are sparse,
- many candidate rows are pre-execution rejects by design,
- LIMIT_PLACED rows lack lifecycle truth,
- synthetic/path labels must not be mixed with actual broker outcomes.

Operational telemetry gaps:

| Gap | Number |
|---|---:|
| `_trade_index.json` count | `129` |
| Current trade-record count excluding pending index | `259` |
| `_trade_index.json` latest date | `2026-03-13` |
| Trade-record latest date | `2026-05-01` |
| Index staleness | `49` days |
| LIMIT_PLACED rows missing execution/lifecycle fields | `43` |

This blocks clean V3, fill/no-fill, pending-limit, and actual-R validation.

### 14.2 Orderflow Label Constraints

NAS100 orderflow readiness:

| Metric | Value |
|---|---:|
| Orderflow rows | `12` |
| Synthetic/path labels | `11` |
| Actual broker-R labels | `1` |
| Synthetic winners/losers | `1 / 10` |
| MBP-10 candidate rows | `11` |
| Required actual-R floor | `20` |
| Required synthetic winner floor | `10` |
| Required MBP-10 candidate floor | `30` |

The orderflow branch is serious, but not ready as a live filter.

### 14.3 Source Constraints

| Source | Constraint |
|---|---|
| Futures proxies | Not broker-truth validation. |
| Sierra `.scid` | Converted, but source-transfer evidence only unless same-market. |
| Sierra `.depth` | Family-specific parity. NQ/YM exact, GC near, 6B sampling alignment needed, SI blocked. |
| MT5 tick history | Insufficient for older tick/depth expansion. |
| Databento | Useful, but new pulls must be predeclared and cost-capped. |
| CL/ZN/VIX | Context/control only unless named cross-instrument questions are registered. |

## 15. What Worked And Why

### 15.1 NQ/YM Worked Because Source Parity Was Clean

NQ and YM exact MBP10 parity means local Sierra depth can replicate cached Databento MBP10 for those windows.

This makes them the strongest orderflow/depth research families.

What this supports:

- depth availability/thinness diagnostics,
- candidate/context depth studies,
- forward NAS100/US30 orderflow shadowing,
- source-transfer research.

What this does not support:

- live CFD broker-truth validation,
- immediate live filtering,
- broad assumption that every futures family is equivalent.

### 15.2 XAUUSD Worked Because It Was Same-Market Source Transfer

XAUUSD was not a futures-only proxy. It included `XAUUSD.scid`, which is closer to the traded market.

That is likely why it produced the most interesting strategy diagnostic.

But the result is small:

- `n=5` resolved,
- diagnostic only,
- not enough for statistical inference,
- not enough for promotion.

### 15.3 6B Almost Worked Because The Mismatch Was Mostly Sampling

6B was not rejected because common-second masking reduced max delta from `51` to `5`.

This is an engineering problem:

- align sample seconds,
- make sampling policy explicit,
- rerun parity,
- only then use 6B depth diagnostics.

### 15.4 XAGUSD M15 "Worked" For The Wrong Reason

The M15 result looked positive, but MTF replay killed it.

Why:

- M15 can mark an outcome that lower timeframe path would never realistically enter,
- fill/no-fill state matters,
- sparse source and SI depth mismatch increase uncertainty.

This is a valuable negative result because it tells us which kind of optimistic replay to distrust.

## 16. What Did Not Work And What Would Make It Work

| Area | What Did Not Work | What Would Make It Work |
|---|---|---|
| V2 OB-boundary promotion | Mixed source-transfer diagnostics, no true temporal OOS | Resolved post-cutoff OB-boundary/J46 pairs with sample floors |
| V2 FVG path | Not opened in first-wave converted-source survival | Compatible V2 event-log batch and registered survival question |
| V3 FVG-only rescue | Blocked by missing V2 rows/lifecycle/pre-fill fields | Pending lifecycle, pre-fill delivery path, resolved V2/V2b rows |
| NAS100 depth/thinness | Label-limited, actual broker-R only `1` | Forward collection until actual-R >=20 and MBP10 candidate rows >=30 |
| XAGUSD/SI | M15 positive not MTF-portable, depth source blocked | Resolve SI source definition and replay with lower-timeframe fill truth |
| EURUSD/6E | No frozen raw-OHLC cohort | Pre-register cohort/session/side/comparator before outcomes |
| ES/MES | No frozen raw-OHLC cohort | Register expansion/control question and source mapping |
| CL/ZN/VIX | No direct trade-label cohort | Use only after named cross-instrument context question |
| 6B depth | Sampling mismatch | Common-second/declarative sampling alignment |

## 17. Expansion And Growth Potential

Expansion potential is real, but it is not uniform across instruments.

### 17.1 Best Expansion Families

| Family | Expansion Potential | Reason |
|---|---:|---|
| NAS100/NQ | high diagnostic potential | exact depth parity, orderflow branch already active |
| US30/YM | medium-high diagnostic potential | exact depth parity, but replay labels weak |
| XAUUSD/XAUUSD.scid/GC | high strategy research potential | same-market diagnostic positive, GC near parity |
| GBPUSD/6B | medium | path works, depth likely fixable by sampling alignment |
| EURUSD/6E | medium | clean rows exist, but cohort not registered |
| ES/MES | medium | clean rows exist, but source/candidate relevance not registered |
| USDJPY/6J | medium-low | path works, no actions, proxy caution |
| XAGUSD/SI | low until source fixed | MTF not portable and SI depth blocked |
| CL/ZN/VIX | context potential | useful for regime/macro/control, not direct validation |

### 17.2 What Expansion Should Mean

Expansion should not mean "trade more symbols."

Expansion should mean:

- more context,
- better opportunity classification,
- better failure filters,
- better regime awareness,
- better source-transfer diagnostics,
- better forward validation,
- better candidate prioritization.

Some families may never become traded instruments but may still improve decisions.

Examples:

- VIX/VXM can help volatility regime filtering.
- ZN can help rates/macro context.
- CL can help liquidity/macro stress context.
- NQ/YM can help equity-index orderflow diagnostics.

## 18. Potential Live Shadow Logging / Data Capture

This is where I think the next real growth comes from.

### 18.1 Highest-Priority Shadow Capture

| Capture Item | Why It Matters |
|---|---|
| Pending-limit lifecycle | Required for fill/expiry/cancel truth, V3, pre-fill path, actual outcome validity |
| Actual broker-R for LIMIT_PLACED rows | Separates real broker outcomes from synthetic/path outcomes |
| V2b OB-boundary vs J46 forward pairs | Required for true temporal OOS path validation |
| NAS100 MBP-10/trades around candidates | Best current orderflow diagnostic branch |
| Sierra full-depth around NQ/YM candidate windows | NQ/YM exact parity makes this credible |
| Pre-fill delivery-path rows | Needed for delivery-leg plus reversal-leg idea |
| Cost/slippage at entry and exit | Needed for realistic path/R accounting |
| FVG/OB confluence ledger | Needed to distinguish confirmation from overlock |
| Orderflow depth availability/thinness | Best current adverse-selection candidate |

### 18.2 Shadow Logging Principles

All new logging should be:

- additive,
- fail-open,
- no live decision impact,
- versioned,
- separated by actual vs synthetic labels,
- with no-leak timestamps,
- with explicit evidence class.

## 19. More Angles To Research

Yes, there are many. The most valuable are not random new indicators. They are system-level improvements.

### 19.1 Path Management

Research angles:

- V2b OB-boundary forward validation,
- FVG-only rescue pockets,
- OB-after-FVG tail preservation,
- Composite overlock failure modes,
- delivery-leg plus reversal-leg double setup,
- lower-timeframe path ordering,
- same-bar ambiguity classification,
- cost-aware exits,
- session/regime-specific path rules.

### 19.2 Orderflow

Research angles:

- NAS100 thin-depth adverse selection,
- candidate/context depth deltas,
- depth imbalance as secondary field,
- wall concentration,
- near-touch pull/add pressure,
- trapped liquidity behavior,
- recent-period survival,
- orderflow by session/regime,
- orderflow for abort/entry timing rather than binary filtering.

### 19.3 Execution

Research angles:

- pending limit fill probability,
- cancel/expiry behavior,
- slippage by symbol/session,
- entry heat before fill,
- missed-fill opportunity cost,
- partial close variants under actual fill/cost conditions,
- close-side spread/cost.

### 19.4 Signal Intelligence

Research angles:

- regime-aware market-state classification,
- structure detector divergence,
- FVG/OB/Swing agreement and disagreement,
- POI quality scoring,
- liquidity sweep quality,
- touch-count context after more live rejects,
- decay by symbol/session/side/regime.

### 19.5 Data And Validation

Research angles:

- claim ledger automation,
- effective-N per bucket,
- DSR/PBO on eligible future claims,
- forward-only rolling reports,
- source-period flags for old labels,
- broker/source transfer bias,
- alternate provider for pre-2024 tick/LOB.

## 20. Confidence In Findings

Confidence should be split by category.

| Finding | Confidence | Reason |
|---|---:|---|
| Sierra `.scid` conversion works | 9/10 | Tooling and tests passed; broad conversion succeeded. |
| Sierra `.depth` extractor works at tooling level | 8.5/10 | Tests passed and exact NQ/YM parity achieved. |
| NQ/YM exact depth parity is real for tested windows | 9/10 | Exact cached MBP10 match with zero deltas. |
| GC near parity is usable with caution | 7/10 | Small deltas, but not exact. |
| 6B mismatch is mostly sampling policy | 7/10 | Common-second max delta fell from `51` to `5`. |
| SI source/depth-definition is blocked | 8/10 | Common-second masking did not reduce max delta. |
| XAUUSD structural source-transfer is promising | 4/10 | Directionally positive but only `n=5`. |
| XAUUSD structural result is promotable | 0/10 | No sample floor, no unseen validation. |
| NAS100 orderflow depth/thinness is worth forward collection | 7/10 | Best current orderflow branch, but label-limited. |
| NAS100 orderflow is live-filter ready | 1/10 | Actual broker-R labels only `1`. |
| Current expanded-OOS pass completed local unblocking goal | 9/10 | Completion-standard artifacts exist. |
| Broader research phase is complete | 3/10 | Validation and live promotion still blocked. |

## 21. Are We Closer To The Main Goal?

Yes.

But the reason matters.

We are not closer because we found a live strategy to deploy. We are closer because we now have:

- broader data access,
- reusable conversion tooling,
- depth extraction tooling,
- exact source-parity classifications,
- warning cases for false M15 optimism,
- family-by-family expansion map,
- clear label gaps,
- clear future shadow-logging priorities.

This makes the system less random and more organized.

The system is becoming an operating system rather than just a trade signal generator.

## 22. Objective Completion Percentages

These are judgment estimates, not statistical outputs.

| Objective | Completion Estimate | Explanation |
|---|---:|---|
| May 4 full-unblocking local goal | 100% | Completion-standard artifacts exist. |
| First-wave source/data map | 90% | All 11 families covered; some source definitions remain blocked. |
| Sierra OHLCV replay readiness | 75% | Converter works; more slices and registered cohorts needed. |
| Sierra depth readiness | 60% | NQ/YM exact; GC near; 6B needs alignment; SI blocked. |
| Strategy validation readiness | 25% | Most strategy outcomes are label-limited or same-dataset. |
| Live-promotion readiness for new findings | 10% | No true temporal OOS, no sample floors, no DSR/PBO. |
| Orderflow live-filter readiness | 10-15% | Tooling promising, labels sparse. |
| Overall GTOS power/maturity toward ultimate goal | 55-60% | Strong base and discipline, but missing forward truth and validation. |

## 23. Aspect Scores Out Of 10

| System Aspect | Score | Why Not 10 | Highest-Value Improvements |
|---|---:|---|---|
| Live safety and deterministic gates | 8.0 | Strong protection, but operator/runtime and telemetry gaps remain | watchdog freshness, execution reconciliation, operator wake/disk fixes |
| Core OB/structure edge | 6.5 | Mechanism real, but decay/regime sensitivity remains | regime-conditioned monitoring, live sample accumulation |
| AI decision layer | 6.0 | AI still depends on prompt/MSO quality and sparse feedback | grounded structured tools, richer no-leak context, paired shadow labels |
| Market-state/signal detection | 6.5 | Good structure tools, but lower-TF path ambiguity remains | confluence ledgers, POI lifecycle, path ordering |
| Path management/exits | 5.5 | V2/V3 promising but not validated | V2b forward pairs, lifecycle-aware V3, cost-aware exits |
| Orderflow/depth intelligence | 4.5 | Tooling new, labels sparse | NAS100 forward MBP/depth collection, NQ/YM diagnostics |
| Data infrastructure | 7.0 | Sierra conversion/depth improved, older/deeper data still blocked | alternate provider/archive, source indices, pre-2024 tick/LOB |
| Label quality | 4.0 | Actual broker-R sparse, lifecycle missing | pending-limit lifecycle, actual/synthetic/fill-no-fill separation |
| Validation methodology | 8.0 | Strong doctrine, many claims correctly blocked | automated claim ledger, effective-N reporting, promotion dossier templates |
| Execution telemetry | 4.5 | Execution/lifecycle fields missing in many records | fill/expiry/cancel logs, close-side slippage, trade-index migration |
| Expansion readiness | 6.0 | 11 families mapped, many are control/proxy only | register EURUSD/ES, validate one unresolved proxy |
| Live promotion readiness for new research | 2.0 | No unseen validation or sample floors | forward shadow, DSR/PBO gates, separate promotion dossier |

## 24. True Potential I See

The true potential is not one magic rule.

The true potential is compounding incremental improvements across the stack:

1. Better market-state detection.
2. Better candidate filtering.
3. Better orderflow/context awareness.
4. Better path management.
5. Better fill/no-fill understanding.
6. Better execution/cost accounting.
7. Better risk sizing by state.
8. Better exit/partial decisions.
9. Better cross-instrument opportunity awareness.
10. Better validation discipline.

If each layer produces a small real improvement, the combined effect can be large.

The system can become meaningfully stronger than a generic trading bot if it evolves into:

- a live research collector,
- a market-state reasoner,
- an execution-aware path manager,
- a strict validation system,
- a controlled strategy deployment framework.

The highest unrealized potential is in:

- pending-limit lifecycle truth,
- V2b forward validation,
- NAS100/NQ orderflow diagnostics,
- XAUUSD same-market structural path extension,
- V3 reentry after lifecycle truth exists,
- confluence/disagreement mapping,
- context controls from VIX/ZN/CL.

## 25. Does This Wrap The Research Phase?

No.

It wraps the **local expanded-OOS full-unblocking pass**.

It does not wrap:

- V2b validation,
- V3 validation,
- orderflow validation,
- live-promotion research,
- actual broker-R sample collection,
- pending-limit lifecycle telemetry,
- pre-fill delivery-path research,
- source-definition work for SI,
- forward promotion dossiers.

Research phase status:

| Phase | Status |
|---|---|
| Local first-wave data unblocking | complete |
| Data/replay infrastructure | significantly improved |
| Strategy discovery | active |
| Strategy validation | early and blocked by labels |
| Live promotion | not reached for these findings |

## 26. Recommended Next Plan

### Priority 1: Pending-Limit Lifecycle Telemetry

This is the highest-leverage operational improvement.

Needed fields:

- pending limit created time,
- order ticket,
- fill time,
- expiry time,
- cancellation reason,
- broker fill state,
- entry price,
- slippage,
- spread,
- actual R,
- synthetic/path R separated,
- fill/no-fill label.

Why this matters:

- unlocks actual broker-R,
- unlocks V3 validation,
- unlocks pre-fill delivery path,
- fixes LIMIT_PLACED ambiguity,
- improves execution analytics.

### Priority 2: V2b Forward Pair Collector

Every qualifying post-cutoff setup should log:

- OB-boundary outcome,
- J46 baseline outcome,
- fixed-R comparator,
- FVG comparator,
- symbol,
- session,
- side,
- regime,
- lower-timeframe availability,
- ambiguity state,
- cost sensitivity.

Goal:

Get resolved OB-boundary/J46 pairs to sample floor.

### Priority 3: NAS100/NQ Orderflow Forward Diagnostic

Collect:

- MBP-10,
- trades,
- Sierra full-depth where possible,
- depth availability,
- thinness,
- imbalance,
- wall concentration,
- candidate/context windows,
- actual outcome labels.

Do not create a live filter yet.

### Priority 4: 6B Sampling Alignment

Add common-second/declarative sampling alignment.

Then rerun 6B parity.

If 6B becomes clean enough, GBPUSD/6B can become a usable diagnostic branch.

### Priority 5: SI Source Definition Investigation

Resolve:

- continuous contract mapping,
- SIM vs SIL source choice,
- Databento `SI.v.0` definition,
- depth book definition,
- micro vs standard effects.

Until resolved, do not use SI depth in replay synthesis.

### Priority 6: XAUUSD Frozen Slice Extension

Take the promising XAUUSD source-transfer clue and extend honestly:

- pre-register more frozen slices,
- keep same-market source-transfer label,
- target at least `n>=30`,
- preserve costs,
- no live promotion until unseen validation.

### Priority 7: EURUSD/ES Pre-Registration

Before opening outcomes:

- define cohort,
- define session,
- define side,
- define comparator,
- define evidence class,
- define label policy,
- define reserved holdout.

### Priority 8: Pre-Fill Delivery Path Capture

This directly supports the owner's delivery-leg plus reversal-leg idea.

First capture the path.

Then score a strategy.

Do not reverse the order.

## 27. Open Questions And Ambiguities

The major unresolved questions:

1. Does V2b OB-boundary survive once post-cutoff resolved pairs exist?
2. Does the XAUUSD `n=5` structural source-transfer result survive at `n>=30`?
3. Is NAS100 thin-depth a real adverse-selection signal or one-date concentration?
4. Can 6B be fully unblocked by sampling alignment?
5. What exact source-definition mismatch blocks SI?
6. Can EURUSD/6E or ES/MES produce meaningful GTOS cohorts?
7. Can CL/ZN/VIX improve context/regime classification enough to matter?
8. Can V3 reentry work once lifecycle and pre-fill truth exist?
9. How much apparent strategy decay is signal decay versus missing fill/path truth?
10. Which live candidates are being missed because we lack orderflow/context awareness?
11. Can orderflow help more as entry timing/abort/exit infrastructure than as a binary filter?
12. What is the actual broker-R distribution of current LIMIT_PLACED rows?
13. How much slippage/cost changes path-management conclusions?
14. Can the system build enough forward labels quickly without waiting passively for months?

## 28. My Direct Read

This research was a success in the research-infrastructure lane.

It was not a success in the live-promotion lane because it was not supposed to be one.

The most important insight is:

> GTOS is currently bottlenecked less by idea generation and more by forward truth capture, label quality, source parity, and lifecycle-aware replay.

We have plenty of possible strategy ideas:

- V2b OB-boundary,
- V3 FVG-only rescue,
- NAS100 depth/thinness,
- delivery-leg plus reversal-leg,
- FVG/OB confluence,
- same-market XAU structural path,
- regime/context filters.

But the system cannot honestly promote them until it has:

- actual outcomes,
- fill/no-fill truth,
- no-leak path reconstruction,
- forward validation,
- cost/slippage accounting,
- sample floors,
- DSR/PBO/effective-N where applicable.

The next stage should not be random new strategy hunting.

The next stage should be:

1. capture truth,
2. replay with no-leak structure,
3. separate evidence classes,
4. validate forward,
5. promote only through a separate dossier.

If we do that, GTOS can become much more powerful. Not by becoming a one-rule bot, but by becoming a structured intelligence and execution operating system that learns from every opportunity and every non-opportunity.

## 29. Final Conclusion

The expanded-OOS full-unblocking pass moved the project forward in a meaningful way.

It established:

- which instruments are ready for source/replay diagnostics,
- which depth sources can be trusted,
- which sources are blocked,
- which strategy clues are worth extending,
- which apparent positives are false under lower-timeframe replay,
- which telemetry gaps block validation,
- what to collect next,
- and what not to promote.

The strongest current future paths are:

1. pending-limit lifecycle telemetry,
2. V2b forward resolved-pair collection,
3. NAS100/NQ depth/thinness forward diagnostics,
4. XAUUSD same-market structural path extension,
5. 6B sampling alignment,
6. SI source-definition resolution,
7. pre-fill delivery-path capture,
8. strict claim ledger and promotion dossier discipline.

The project is closer to the owner's main goal because the system now has a clearer route to compounding improvements across intelligence, data capture, signal quality, opportunity awareness, execution, path management, and risk/exits.

But it is not time to deploy new strategy logic from this pass.

Final status:

`NO_PROMOTION_VERDICT`

