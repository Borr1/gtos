# G8 CD2-02 Short-Vol Execution Missing-Source Ledger - 2026-05-06

Promotion verdict: `NO_PROMOTION_VERDICT`

## Purpose

This G8-owned ledger records the source and label blockers for joining short-tenor volatility context to execution lifecycle rows under `CD2-02`. It is not a master-registry edit and not a validation result.

## Bottom Line

Short-vol context can join pending-limit lifecycle rows only as pre-outcome context after Cboe as-of timing, parser, and no-lookahead tests exist. It cannot join close-side cost, synthetic path-R, or broker actual-R as a primary metric in this lifecycle-only prereg.

No access request is needed to write this prereg/ledger because the controlling local artifacts and cached Cboe files are already present. Future work may need public-source fetch access or owner/legal review to prove Cboe same-day publication timing and license terms.

## Missing-Source And Blocker Ledger

| ID | Blocker | Current Evidence | Required Resolution | Current Handling |
|---|---|---|---|---|
| `G8-CD2-02-MISS-001` | Cboe CSV same-day availability | G8 cached VIX1D/VIX9D CSVs through 2026-05-05, but the source contract says publication timing is unknown. | Prove `publication_asof_utc` for each CSV row or source family; add parser/cache metadata and no-lookahead tests. | Same-day intraday joins are blocked; use prior fully closed Cboe trading day only until proven otherwise. |
| `G8-CD2-02-MISS-002` | Cboe parser and no-lookahead join tests | G8 source index confirms raw CSVs exist; G8 source contract keeps `validation_safe=false`. | Build parser that records `source_row_date`, `source_cached_at_utc`, `publication_asof_utc`, row value, stale flag, and join mode; test same-day and previous-day joins. | Source can define a prereg, not a validation-safe feature. |
| `G8-CD2-02-MISS-003` | Index-vol proxy transfer to broker CFDs | VIX1D/VIX9D are SPX option volatility indices while GTOS rows are `NAS100`, `US30`, and `US30_cash`. | Add proxy-transfer diagnostics by instrument, date block, and session; reject if basis/session mapping is unstable. | Treat as broad equity-index stress context only. |
| `G8-CD2-02-MISS-004` | Pending lifecycle ordering | G10 preregs require decision/pending/source-capture ordering; current live lifecycle rows contain useful fields, but historical prefill coverage lacks true pending-created time and broker lifecycle state. | Prospective rows must freeze `decision_asof_utc`, `pending_created_utc`, `source_capture_utc`, and lifecycle state before outcome review. | Historical path-only rows are excluded from the primary prereg unless marked coverage-only. |
| `G8-CD2-02-MISS-005` | Original POI bounds and ordered path | The prefill coverage report shows `0` rows with original POI bounds and `0` with broker lifecycle state. | Capture exact POI type/bounds and ordered M1/tick path before fill/cancel for future rows. | `G10-HYP-PREFILL-003` remains prospective-only for this prereg. |
| `G8-CD2-02-MISS-006` | Decision-time spread for all lifecycle states | Pending lifecycle rows may have `spread=null`; slippage rows are sparse and tied to successful order attempts. | Record spread timestamp and value for every lifecycle snapshot, including no-fill/cancel states, without waiting for broker fill. | Spread is optional context only; missing spread cannot drop the lifecycle row unless a future prereg says so. |
| `G8-CD2-02-MISS-007` | Entry slippage integrity | The latest cost coverage has 3 entry slippage rows; broker actual-R audit marks broker-zero fill-price slippage rows as not usable actual fills. | Require observed non-zero broker fill evidence and order-attempt linkage before using entry slippage diagnostics. | Entry slippage is child diagnostic only, not primary lifecycle label. |
| `G8-CD2-02-MISS-008` | Close-side cost coverage | Cost coverage reports `0` close-side slippage rows, `0` close commission rows, `0` close swap rows, and `0` close deal-id rows. | Add separate close-side cost telemetry and a separate broker_actual_r/cost prereg before any close-cost study. | Close-side cost rows are excluded from CD2-02 lifecycle primary. |
| `G8-CD2-02-MISS-009` | Broker actual-R sample scarcity | LTO-015 permits broker actual-R claims on only `3` account-history realized rows. | Collect sufficient closed broker trades with account-history evidence and close-cost attribution under a separate prereg. | Broker actual-R is excluded from CD2-02 lifecycle primary. |
| `G8-CD2-02-MISS-010` | G11 no-leak field semantic inversion | G0 flagged `HYP-G11-FRICTION-GATE-007` because its `no_leak_fields` list reads as forbidden outcome/future field names. | G12 or lane cleanup must convert forbidden-field lists into exclusion fields or replace them with true as-of feature names. | Do not consume G11 no-leak fields as allowed features; use G11 only as a blocker/source-readiness signal. |
| `G8-CD2-02-MISS-011` | Validation-safe source boundary | G0 master registry reports `0` validation-safe source contracts and `0` opened outcome preregs. | Source contracts need legal, timestamp, parser, cache, and no-lookahead blocker clearance before validation use. | All CD2-02 outputs remain research-only. |

## Required Join Contract Before Any Outcome Review

The minimum safe CD2-02 lifecycle join row must include:

- `candidate_decision_time_utc`
- `pending_created_utc`
- `lifecycle_source_capture_utc`
- `lifecycle_state_before_outcome`
- `fill_no_fill_label`
- `short_vol_source_id`
- `vix1d_source_row_date`
- `vix9d_source_row_date`
- `short_vol_publication_asof_utc`
- `short_vol_join_mode`
- `short_vol_stale_or_unverified_flag`
- `spread_timestamp_utc`
- `spread_asof`
- `label_family = lifecycle_no_fill`

Rows must exclude or separately store:

- `synthetic_path_r`
- `broker_actual_r`
- `actual_r`
- `trade_result`
- `future_return`
- `post_entry_path`
- `close_slippage`
- `commission`
- `swap`
- `close_deal_id`

## Access And Spend State

- New external cash spend: `$0`.
- Paid data calls: `0`.
- MT5 calls: `0`.
- AI calls: `0`.
- Canary calls: `0`.
- Remote pushes: `0`.

Final verdict: `NO_PROMOTION_VERDICT`.
