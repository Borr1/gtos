# Orderflow Proxy Mapping Weekend Forensics

Date: 2026-05-03
Scope: research/tooling only; cached artifacts only
Promotion verdict: `NO_PROMOTION_VERDICT`
Registration verdict: `NO_PROXY_MAP_ACTIVATION`

## Synthesis

USDJPY/6J remains review-open because 2026-04-27 stays below the strict 0.85 correlation floor. The cached artifacts do not support a timestamp or lag explanation; the weakness is more consistent with magnitude/basis/noise degradation that current aggregate diagnostics cannot isolate.

## USDJPY/6J Weak Window

| window | corr | direction | shift | expected shift | best lag | aligned | volume vs median | beta vs median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-04-27T07:00_2026-04-27T16:59 | 0.825301 | 0.936232 | -180 | -180 | 0 | 591 | -7666.000000 | -0.111645 |

## Cause Readout

| factor | status | evidence |
| --- | --- | --- |
| timestamp | unlikely_from_artifacts | Weak window selected the expected -180 minute shift and best lag remained 0. |
| session | not_evaluable_from_aggregate_07_17_windows | All current follow-up windows are aggregate 07:00-17:00 UTC windows. |
| roll | not_supported_by_current_artifacts | No roll-specific flag or roll-adjacent diagnosis exists in the cached artifacts. |
| basis | plausible_not_proven | Weak window kept high directional agreement but lower correlation/beta; basis fields are null in the inverse-return diagnostics. |
| data quality | not_primary_from_artifacts | Aligned minutes are similar to neighboring windows; futures trade count/volume are below median but not uniquely low. |

## Next Unresolved Symbol

| field | value |
| --- | --- |
| next_symbol | USDJPY |
| next_lane | registered_price_transfer_followup_only |
| why | USDJPY has the largest unresolved candidate inventory and a single direct inverse futures proxy, but it remains under transfer review; the next allowed data should be a registered 6J/USDJPY mapping follow-up, not depth or alpha features. |
| usdjpy_candidate_rows | 34 |
| gbpjpy_candidate_rows | 23 |
| proxy_expansion_status | TRANSFER_REVIEW_REQUIRED |

## GBPJPY Synthetic Mapping

| field | value |
| --- | --- |
| price_transfer_feasibility | CONCEPTUALLY_FEASIBLE_AFTER_LEG_VALIDATION |
| orderflow_depth_feasibility | STAY_BLOCKED_TWO_BOOK_SEMANTICS |
| gbpusd_leg | STRICT_TRANSFER_PASS |
| usdjpy_leg | TRANSFER_REVIEW_REQUIRED |
| current_candidate_rows | 23 |
| required_before_registration | ["6J/USDJPY must pass a pre-registered transfer gate or robust alternative gate", "synthetic GBPJPY return formula must be registered and tested against MT5 GBPJPY", "two-book feature semantics must be defined without pretending 6B and 6J form one ladder", "depth/orderflow pulls require a separate hypothesis after price transfer passes"] |
| verdict | DO_NOT_REGISTER_ORDERFLOW_MAPPING_YET |

## Non-Claims

- USDJPY/6J proxy is not activated.
- GBPJPY synthetic two-book orderflow is not registered.
- No new futures data was fetched.
- No orderflow alpha or live filter is claimed.

## Next Steps

1. If data is allowed, run a pre-registered USDJPY/6J transfer follow-up with robust gate criteria before any depth pull.
2. Keep GBPJPY blocked until both 6B/6J legs and a synthetic-cross price-transfer protocol pass.
3. For GBPJPY, separate price-transfer feasibility from depth/orderflow semantics in any future protocol.
