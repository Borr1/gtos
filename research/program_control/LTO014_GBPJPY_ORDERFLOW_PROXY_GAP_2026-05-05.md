# LTO-014 GBPJPY Orderflow Proxy Gap

Date: 2026-05-05
Scope: research/tooling only; existing local artifacts only
Promotion verdict: `NO_PROMOTION_VERDICT`
Status: `BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN`

## Synthesis

GBPJPY remains blocked for external orderflow confluence because no direct Sierra/Databento proxy exists. The viable research path is a pre-registered two-book 6B/6J design that first proves price-transfer stability and then keeps leg-specific orderflow semantics separate.

## Completion Evidence

| field | value |
| --- | --- |
| candidate_status_rows_built | 50 |
| gbpjpy_candidates_seen | 50 |
| gbpjpy_registry_status_rows_seen | 709 |
| direct_proxy_registered | False |
| existing_gbpjpy_confluence_inferred | False |
| live_trading_behavior_changed | False |
| ai_calls | 0 |
| canary_calls | 0 |
| order_calls | 0 |
| paid_data_calls | 0 |
| status_rows_appended | 3 |

## Proxy Designs

| design | status | source legs | allowed now | direct confluence |
| --- | --- | --- | --- | --- |
| NO_DIRECT_PROXY_CURRENT | CURRENT_BLOCKER | [] | blocker/status rows only | False |
| 6J_YEN_LEG_CONTEXT_ONLY | PRE_REGISTERED_CONTEXT_ONLY | ["6J.v.0"] | design/readiness only | False |
| 6B_GBP_LEG_CONTEXT_ONLY | PRE_REGISTERED_CONTEXT_ONLY | ["6B.v.0"] | design/readiness only | False |
| TWO_BOOK_SYNTHETIC_6B_6J | PRE_REGISTERED_NOT_ACTIVE | ["6B.v.0", "6J.v.0"] | pre-registered shadow design only | False |
| BROKER_CROSS_OHLC_CONTROL | CONTROL_ONLY | ["GBPUSD broker OHLC", "USDJPY broker OHLC", "GBPJPY broker OHLC"] | control diagnostics only | False |

## Pre-Registered Tests

| test | purpose | current status | outcomes opened |
| --- | --- | --- | --- |
| GBPJPY-PROXY-T1-CORRELATION-STABILITY | Check whether the synthetic 6B-6J return path tracks MT5 GBPJPY before any outcome join. | NOT_PASSED_OR_NOT_RUN | False |
| GBPJPY-PROXY-T2-LEAD-LAG | Detect whether 6B/6J leads or lags GBPJPY enough to create timestamp/no-leak risk. | NOT_PASSED_OR_NOT_RUN | False |
| GBPJPY-PROXY-T3-SESSION-OVERLAP | Confirm the source legs have overlap in GBPJPY Tokyo/London/NY decision sessions. | PASS | False |
| GBPJPY-PROXY-T4-CONTRACT-LIQUIDITY | Confirm both futures legs are liquid enough in the exact common window. | PASS | False |
| GBPJPY-PROXY-T5-OUTCOME-TRANSFER-CAVEAT | Prevent future reports from treating two-leg context as direct broker outcome validation. | PASS | False |

## Price-Transfer Diagnostic

| field | value |
| --- | --- |
| diagnostic_status | PRELIMINARY_PRICE_TRANSFER_DIAGNOSTIC_ONLY |
| common_m15_bars | 268 |
| zero_lag_corr | 0.013697 |
| best_lag_bars | -2 |
| best_lag_corr | 0.096928 |
| session_overlap_bars | {"london_gbpjpy": 30, "ny_gbpjpy": 30, "other": 172, "tokyo": 35} |
| common_volume_6b | 208741.000000 |
| common_volume_6j | 419901.000000 |
| no_outcomes_opened | True |

## Current GBPJPY Rows

| candidate_id | status | direct confluence | confluence inferred | proxy design |
| --- | --- | --- | --- | --- |
| GBPJPY_2026-05-04T02:15:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-04T02:30:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-04T03:00:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-06T02:30:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-06T07:30:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-06T07:45:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-11T01:15:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-11T01:45:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-11T07:30:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-11T13:30:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-11T15:15:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-12T01:15:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-12T01:45:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-12T02:30:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-12T03:00:00+00:00 | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-05-31T22:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T00:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T00:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T01:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T01:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T02:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T03:45:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T04:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T05:15:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T05:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T05:45:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T06:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T06:15:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T06:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T06:45:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T07:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T07:15:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T07:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T07:45:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T13:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T13:15:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T13:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T13:45:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T14:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T14:15:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T14:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T15:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T16:45:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T17:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T17:45:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T19:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T19:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T21:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T21:30:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |
| GBPJPY_2026-06-01T22:00:00Z | BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN | False | False | gbpjpy_two_leg_proxy_design_v1 |

## Non-Claims

- No GBPJPY confluence was inferred for existing rows.
- No two-book orderflow signal is active.
- 6B and 6J are not treated as one synthetic GBPJPY ladder.
- No broker actual-R or candidate outcome rows were opened by this audit.
- No paid Databento, AI, canary, MT5 order, or execution call was made.

## Next Steps

1. Keep current GBPJPY candidate rows marked no-proxy/source-blocked.
2. Before any outcome join, freeze the 6B/6J price-transfer source window, lead/lag convention, and pass/fail gates.
3. After 6B common-second and USDJPY/6J transfer gates pass, collect leg-specific footprint/depth features as context only.
4. Only later test entry timing, veto, stop/invalidation, or target/RR expansion roles against broker actual-R and lifecycle truth.
