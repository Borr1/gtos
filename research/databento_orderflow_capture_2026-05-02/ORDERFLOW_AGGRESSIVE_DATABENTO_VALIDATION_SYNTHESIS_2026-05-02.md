# Aggressive Databento Validation Synthesis

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Executive Answer

Databento is not adding zero value. It is now useful as a cheap, event-window orderflow validation feed. The latest aggressive pass shows that vendor cost and availability are not the main blocker for supported futures proxies. The remaining blocker is whether the orderflow features can survive label, symbol, and forward-validation discipline.

The correct validation definition is:

1. **Data feasibility:** supported futures data can be pulled at candidate windows under explicit caps.
2. **Transfer feasibility:** futures proxy maps must be valid for each GTOS symbol before using futures flow.
3. **Feature feasibility:** trades/depth features must extract cleanly without stale proxy-map artifacts.
4. **Candidate/context separation:** candidate windows should show a repeatable as-of orderflow state versus matched non-candidate structural context.
5. **Outcome separation:** winners and losers must separate within symbol/session/regime, with synthetic/path labels separated from actual broker R.
6. **Promotion readiness:** no live use until a pre-registered validation lane passes sample-size, no-leak, cost, concentration, actual-vs-synthetic, DSR/PBO/effective-N gates.

Current result: stages 1-4 are partially useful; stage 5 is not ready; stage 6 remains blocked.

## Data Pulled Or Estimated In This Pass

All pulls are event-window based, not broad dead-time history.

| Artifact | Schema | Scope | Executed | Estimated cost |
| --- | --- | --- | --- | ---: |
| `ORDERFLOW_AGGRESSIVE_CANDIDATE_SURGICAL_MANIFEST_2026-05-02` | n/a | 58 supported CANDIDATE events, 60m pre + 15m post | n/a | n/a |
| `ORDERFLOW_AGGRESSIVE_SURGICAL_TRADES_FETCH_2026-05-02` | trades | surgical candidate windows | yes | `$0.474594` |
| `ORDERFLOW_AGGRESSIVE_SURGICAL_MBP10_FETCH_2026-05-02` | mbp-10 | surgical candidate windows | yes | `$2.903098` |
| `ORDERFLOW_AGGRESSIVE_PROXY_EXPANDED_MBP10_FETCH_2026-05-02` | mbp-10 | expanded candidate + matched structural context | yes | `$14.357662` |
| `ORDERFLOW_AGGRESSIVE_SURGICAL_MBO_ESTIMATE_2026-05-02` | mbo | surgical candidate windows | no | `$1.889027` |
| `ORDERFLOW_AGGRESSIVE_CANDIDATE_MBO_ESTIMATE_2026-05-02` | mbo | older 60m pre + 60m post candidate windows | no | `$2.580502` |

Fetch-plan represented estimate for executed pulls: `$17.735354`. Vendor final billing may differ, and some expanded MBP-10 groups were cached rather than fetched again.

Databento metadata range at preflight: `GLBX.MDP3` schemas, including `trades`, `mbp-1`, `mbp-10`, and `mbo`, were available through `2026-05-02T01:17:51.087810000Z`.

## MBO Full-Book Feasibility Check

Candidate-window MBO estimates are cheap, but Databento warns that non-midnight MBO requests lack the synthetic full-book snapshot. For real order-book reconstruction, the fair estimate starts at UTC midnight.

NAS100/NQ full-day MBO reconstruction estimates:

| Date | Window | Estimated cost | Records | Billable MB |
| --- | --- | ---: | ---: | ---: |
| 2026-04-28 | `00:00-18:00Z` | `$1.998547` | `21,288,926` | `1192.179856` |
| 2026-04-29 | `00:00-18:00Z` | `$1.471377` | `15,673,399` | `877.710344` |
| 2026-05-01 | `00:00-18:00Z` | `$1.545060` | `16,458,284` | `921.663904` |

Interpretation: for NAS100, full MBO cost is not the limiting factor. The limiting factor is writing a no-leak MBO feature extractor and deciding exactly what MBO is supposed to prove over MBP-10.

## Tooling Corrections

The larger MBP-10 pass surfaced two research-tooling issues that are now corrected:

1. MBP-1/MBP-10 primary-proxy logic was stale and only treated XAUUSD/NAS100/US30 as primary. It now uses the current manifest proxy map, so XAGUSD/SI and GBPUSD/6B are included correctly.
2. MBP-10 DBN sampling now defensively removes duplicate columns before feature computation. The expanded MBP-10 diagnostic completed after this fix.

Verification:

- Direct helper check passed for `XAGUSD -> SI.v.0`, `GBPUSD -> 6B.v.0`, `US30_cash -> YM.v.0`, and `US30_cash -> ES.v.0` as non-primary comparator.
- `python -m pytest` could not run in this sandbox because pytest could not create/read its temporary base directory due Windows ACL errors. This is an environment permissions issue, not a test assertion failure.

## New Evidence

### Surgical Trades

Artifact: `ORDERFLOW_AGGRESSIVE_SURGICAL_TRADES_FEATURES_2026-05-02`

- Feature rows: `59`
- Primary ok rows: `58`
- Data status: `{'ok': 59}`

Outcome join artifact: `ORDERFLOW_AGGRESSIVE_SURGICAL_TRADES_OUTCOME_JOIN_2026-05-02`

- Candidate feature rows: `58`
- Join matched: `35`
- Target available: `22`
- Winners / losers: `12 / 10`
- Status counts: `{'join_matched_no_target': 13, 'join_missing': 23, 'target_available': 22}`

Winner-vs-loser as-of medians:

| Feature | Winners | Losers |
| --- | ---: | ---: |
| `pre60_signed_volume` | `217.0000` | `-94.5000` |
| `pre60_buy_fraction` | `0.5056` | `0.4933` |
| `pre60_absorption_volume_per_tick` | `143.6477` | `40.6826` |
| `event15_signed_volume` | `-6.0000` | `-28.0000` |
| `event15_buy_fraction` | `0.4858` | `0.4929` |
| `event15_absorption_volume_per_tick` | `75.2143` | `17.6063` |
| `profile_event_price_volume_percentile` | `0.6722` | `0.6616` |
| `profile_nearest_lvn_distance_ticks` | `4.5000` | `21.5000` |

This looks interesting but is not validation because the target labels are symbol-confounded: GBPUSD is all winners, NAS100 is mostly losers, and XAUUSD is all winners.

### Surgical MBP-10

Artifact: `ORDERFLOW_AGGRESSIVE_SURGICAL_MBP10_FEATURES_2026-05-02`

- Feature rows: `59`
- Data status: `{'ok': 59}`
- Sample method: one-second last quote per symbol
- Depth scope: top 10 book levels

Outcome contrast:

- GBPUSD: winner `9`, loser `0`; no ladder claim.
- NAS100: winner `1`, loser `10`; failure-cluster dominated.
- XAUUSD: winner `2`, loser `0`; no ladder claim.

NAS100 winner-minus-loser MBP-10 deltas:

- `event15_median_depth10_imbalance`: `-0.0135`
- `event15_thin_depth10_rate`: `-0.1693`
- `event15_median_total_depth10`: `34.0000`
- `pre60_median_total_depth10`: `25.0000`

This is not stable because winner n is `1`.

### Expanded MBP-10 Candidate/Context

Artifact: `ORDERFLOW_AGGRESSIVE_PROXY_EXPANDED_MBP10_FEATURES_2026-05-02`

- Feature rows: `324`
- Data status: `{'no_data': 4, 'ok': 320}`
- Databento warnings during fetch: one weekend/no-data request and one >5GB streaming warning.

Candidate/context deltas:

| Symbol | Candidate n | Context n | Depth10 imbalance delta | Thin-rate delta | Total-depth delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| GBPUSD | `21` | `23` | `0.0068` | `0.0825` | `75.0000` |
| NAS100 | `12` | `61` | `0.0145` | `0.0213` | `-20.0000` |
| US30_cash | `1` | `82` | `-0.0441` | `0.0848` | `19.5000` |
| XAGUSD | `10` | `4` | `-0.0086` | `-0.0119` | `0.5000` |
| XAUUSD | `10` | `13` | `0.0167` | `-0.0226` | `-15.5000` |

Interpretation:

- NAS100 remains the cleanest failure-forensics branch: candidates are thinner than context by total top-10 depth (`-20.0000`) and have a higher thin-depth rate (`+0.0213`).
- XAUUSD also shows lower candidate total depth versus context (`-15.5000`), but outcome labels are one-sided winners only, so this cannot become a rule.
- GBPUSD has many candidate labels but all available targets are winners, so it cannot validate winner-vs-loser separation.
- US30 and XAGUSD are too small or too imbalanced for decisive claims.

## What This Means For Databento

Databento is valuable for:

- event-window CME proxy collection,
- checking whether futures/CFD transfer is good enough,
- extracting trades, top-of-book, top-10-depth, and eventually MBO features,
- deciding whether a SierraChart/full-depth workflow is justified.

Databento is not enough by itself for:

- live trading promotion,
- actual broker-R validation when the local trade did not fill,
- universal orderflow claims,
- full heatmap/queue claims unless MBO reconstruction or SierraChart/full-depth export is explicitly used.

## Current Decision

Do not reject orderflow. Do not promote orderflow. Continue with a narrower, more aggressive validation lane.

Best next registered hypothesis candidate:

```text
OF-NAS100-DEPTH-ADVERSE-SELECTION-V1
Scope: NAS100 GTOS CANDIDATE rows only
Inputs: as-of trades + MBP-10 pre60/event15 only
Primary feature family: top-10 total depth, thin-depth rate, last/median depth imbalance
Comparator: matched NAS100 structural context windows from the same date/session bucket
Labels: synthetic/path R, actual broker R, and fill/no-fill kept separate
Forbidden: post15/post60 as decision input, threshold tuning after seeing labels, cross-symbol pooling
Status: CANDIDATE_NOT_REGISTERED
```

MBO is now justified as an estimate/planning branch, not yet as a blind raw-data pull:

- NAS100 full-day MBO is affordable.
- But MBO should answer a specific question MBP-10 cannot answer, such as queue churn/pull-reload around the candidate level.
- Before fetching multi-GB MBO, write the MBO feature spec and extractor contract.

## Next Steps

1. Register `OF-NAS100-DEPTH-ADVERSE-SELECTION-V1` before the next replay-style test.
2. Build an MBO feature spec for NAS100 only: add/cancel imbalance, queue churn, pull/reload rate, and depth persistence around candidate price levels.
3. Estimate and then fetch UTC-midnight-start NQ MBO only after the MBO spec exists.
4. Continue automatic forward collection for every new supported candidate: surgical trades + MBP-10 by default, with labels separated.
5. Do not use Databento/SierraChart as live confirmation until the registered lane clears label and validation gates.

