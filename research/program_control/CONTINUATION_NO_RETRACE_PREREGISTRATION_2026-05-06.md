# Continuation/No-Retrace Shadow Strategy Preregistration - 2026-05-06

Status: `PREREGISTERED_SHADOW_ONLY`

Promotion verdict: `NO_PROMOTION_VERDICT`

## Objective

Define the continuation/no-retrace strategy family before outcome scoring or
threshold selection. This is a separate shadow lane. It does not loosen
`m15_choch_exists`, does not alter the current retest/limit strategy, and does
not change live prompts, risk, permissions, execution, order placement, or
safety gates.

## Hypothesis

Some AI CANDIDATE rows rejected by `m15_choch_exists` may represent fast
continuation opportunities where the H1 POI direction was right but price
delivered before retracing to the GTOS limit entry.

This is not a claim that the current gate is wrong. The test is whether a
separate market-entry/continuation model can be defined and validated without
using hindsight.

## Eligibility

A row is eligible for `CONTINUATION_NO_RETRACE_M15_FAIL_V1` only when all of
these are true at decision time:

- `analysis_decision == CANDIDATE`.
- `verification.blocked_by == m15_choch_exists` or the
  `m15_choch_exists` check status is `FAIL`.
- Valid trade geometry exists: `direction`, original GTOS `entry_price`,
  `stop_loss`, and `take_profit_1`.
- The original target is favorable relative to the original stop and side:
  `stop_loss < entry_price < take_profit_1` for LONG, or
  `take_profit_1 < entry_price < stop_loss` for SHORT.
- H1/POI geometry checks other than M15 CHoCH are not known hard failures.

Rows are not aggregate-countable unless their joined opportunity status is
`COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`.

## Entry Models

Entry models are preregistered as candidates, not approved execution rules:

- `CNR_E0_DECISION_CLOSE_MARKET`: enter at the executable market price
  available immediately after the evaluated M15 candle closes. This is the
  primary model, but it requires an exact decision-time price source.
- `CNR_E1_DECISION_PRICE_PROXY`: diagnostic-only proxy using the historical
  trade-record proximity `current_price` when present. This is not
  promotion-eligible because it is derived from a session H/L midpoint proxy,
  not a tradable quote.

No row may compute promotion-grade synthetic R unless `CNR_E0` has an exact
decision-time quote or closed-candle price source plus ordered post-entry path
data.

## Stop And Invalidation

Primary stop model:

- Use the original GTOS structural `stop_loss`.
- If the continuation entry price is on the wrong side of the original stop or
  target, the row is `NOT_ELIGIBLE_BAD_CONTINUATION_GEOMETRY`.

Invalidation model:

- If price touches the original GTOS limit entry before reaching the original
  TP1 area, the lane is no longer a no-retrace continuation case for that row.
- If TP1 and SL ordering is ambiguous at available bar resolution, the row is
  not R-scored.

## Target

Primary target:

- Use original GTOS `take_profit_1`.

No alternate target or trailing rule is selected in this preregistration.

## Duplicate Counting

- Raw candidate rows remain append-only evidence.
- Aggregate opportunity counts use only
  `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`.
- `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE` and
  `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP` rows can support path context but
  must not be summed as independent opportunities.

## Session/Symbol Partitions

Required report partitions:

- `symbol`
- `session` / `kill_zone`
- `framework`
- `side`
- `opportunity_counting_status`
- `later_path_outcome_status`

XAGUSD late-NY fresh-OB rows are tracked separately in the next phase and must
not be merged into the older duplicate XAGUSD OB cluster.

## No-Leak Field Whitelist

Decision-time candidate rows may use only:

- candidate identity fields,
- symbol/session/side/framework,
- original trade parameters,
- verification checks and `m15_choch_diagnostic`,
- H1/M15 setup summaries already recorded at candidate time,
- decision-time or proxy price source status.

Resolution rows may join later path/opportunity data, but must use
`POST_DECISION_CONTINUATION_NO_RETRACE_AUDIT_NO_DECISION_FEATURE` and may not be
fed back into live decisions.

## Scoring

Current scoring status:

- `CNR_E0`: `NOT_SCORED_EXACT_DECISION_ENTRY_PRICE_SOURCE_MISSING` unless exact
  decision price and ordered post-entry path data are present.
- `CNR_E1`: may compute distance/proxy context only; it is not promotion-grade
  R evidence.

Required before any promotion dossier:

- exact decision entry price,
- ordered M1 or tick path after entry,
- spread/slippage assumptions,
- duplicate-aware opportunity aggregation,
- cost sensitivity,
- broker actual-R separation,
- post-cutoff forward sample.

NO_PROMOTION_VERDICT
