# Phase 3 Pre-Registered Truth-Layer Matrix Follow-Up Hypotheses

**Created:** 2026-05-01  
**Status:** pre-registered same-dataset follow-up setup  
**Source:** registered matrix replay report  
**Promotion allowed:** no  

## Boundary

This artifact freezes the next research lanes after the full registered-matrix replay. It does not promote alpha and does not authorize live trading changes, prompt changes, parameter optimization, or paid AI/API calls.

The purpose is to prevent ambiguity before the next larger engineering move:

- Keep the original primary controlled family separate.
- Pre-register the non-primary strong discovery leads before deeper same-dataset replay or raw-OHLC adapter work.
- Audit the dominated watchlist before treating those cohorts as candidate families.
- Defer unstable/negative lanes unless a separate protocol is registered.

## Source Evidence

The registered matrix replay evaluated all 44 frozen matrix candidates under the prequential no-leak boundary.

| Metric | Value |
|---|---:|
| rows_replayed | 205197 |
| registered_candidates | 44 |
| matrix_resolved_r_n | 18541 |
| matrix_mean_r | 0.128559 |
| matrix_win_rate | 0.454237 |
| replay_guardrails | PASS |
| historical_pbo_reference | 0.5553613053613053 |
| matrix_effective_N_diagnostic | 20.575922 |
| promotion_verdict | NO_PROMOTION_VERDICT |

## Family A: Non-Primary Strong Leads

This family is pre-registered for diagnostic follow-up only. It was selected after seeing the historical matrix replay, so same-dataset results cannot become promotion-grade proof.

| Cohort | n | mean R | WR | valid years | positive years | max year share |
|---|---:|---:|---:|---:|---:|---:|
| USDJPY\|london\|bearish\|D1 | 154 | 0.428571 | 0.571429 | 3 | 3 | 0.337662 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 252 | 0.387224 | 0.563492 | 4 | 4 | 0.34127 |
| XAGUSD\|london\|bullish\|D1 | 249 | 0.403878 | 0.558233 | 3 | 3 | 0.35743 |

Diagnostic follow-up is allowed if all three remain true under the dominance audit:

- resolved_r_n >= 150
- all valid year folds are positive
- max single-year resolved share <= 0.45

## Family B: Dominance Watchlist

These cohorts looked strong in the matrix report, but year concentration already triggered the dominated bucket. They require dominance/year concentration audit before any controlled family can be registered.

| Cohort | n | mean R | WR | valid years | positive years | max year share |
|---|---:|---:|---:|---:|---:|---:|
| NAS100\|ny\|bullish\|D1 | 631 | 0.373786 | 0.545166 | 3 | 3 | 0.581616 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 320 | 0.508648 | 0.590625 | 3 | 3 | 0.45625 |
| XAUUSD\|ny\|bullish\|D1 | 311 | 0.570303 | 0.62701 | 3 | 3 | 0.453376 |

This lane is blocked from deeper controlled follow-up unless the audit shows the result is not dependent on one year or one month.

## Deferred Lanes

The following are not authorized for deeper follow-up in this artifact:

- high-mean unstable candidates
- marginal positive candidates
- negative/flat candidates, except as controls
- any new cohort not listed in the machine-readable spec

## Next Step

Run the dominance audit evaluator over Family A and Family B. After that, start a fresh session for the larger raw-OHLC replay adapter using only the cleared or explicitly documented target families.

