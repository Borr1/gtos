# G12 NOFILL CAT V2 Blocker Reject Review

Promotion posture: `NO_PROMOTION_VERDICT`.

Status: `PASS`.
Blocked rows: `8`.
Rejected rows: `65`.

## Residual Blockers

| Family | Count | Decision | Unblocker |
|---|---:|---|---|
| `oti4_may3_source_gaps` | 3 | `PRESERVE_EXACT_BLOCKER` | read-only tick parquet quote stream or M1-or-lower OHLC with source hash and as-of provenance for 2026-05-03 13:00-13:30 UTC |
| `oti3_same_tick_order_ambiguities` | 4 | `PRESERVE_EXACT_BLOCKER` | higher-resolution source or explicit broker/native event ordering that proves entry/protective sequence without account/order labels |
| `original_oti2_source_gap` | 1 | `PRESERVE_EXACT_BLOCKER` | side-aware bid/ask tick source covering active pending window through cancel, or an approved source contract that explicitly handles the gap |

## Rejects

| Family | Count | Reason |
|---|---:|---|
| `oti4_contract_excluded_rows` | 26 | OTI4 contract exclusion, not hidden performance or outcome scoring |
| `oti5_noncanonical_duplicate_projections` | 39 | OTI5 canonical geometry rule rejects repeated projections to prevent denominator inflation, not hidden performance or outcome scoring |

Rejected rows are excluded for source/contract/duplicate reasons, not hidden performance reasons.
