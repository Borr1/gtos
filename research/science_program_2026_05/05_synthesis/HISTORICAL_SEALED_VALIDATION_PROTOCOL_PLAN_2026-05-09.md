# Historical Sealed Validation Protocol Plan

Date: 2026-05-09
Status: active methodology plan
Scope: GTOS research validation design
Promotion posture: `NO_PROMOTION_VERDICT`

## Purpose

This plan corrects the weak framing that forward shadow/live rows are the only credible validation path. Forward shadow remains the strongest realism check for current code, current broker behavior, spread, latency, capture quality, and deployment drift. It is not the only route to serious evidence.

GTOS has broad historical/local data. Historical data should be used aggressively, but only under a sealed validation protocol that prevents discovery slices from being rebranded as validation.

## Core Doctrine

The strongest research path is:

`discovery historical -> source/control cleanup -> sealed historical validation -> robustness/stress -> forward shadow realism -> promotion dossier`

Research should be hungry and relentless. Patience belongs in live capital deployment, not in historical evidence pursuit.

## Evidence Classes

Every validation-oriented hypothesis lane must classify data into explicit partitions:

- `DISCOVERY_POOL`: exploration, mechanism search, forensics, negative-result learning, and hypothesis generation.
- `DEVELOPMENT_POOL`: rule shaping, source-contract work, parser/projection design, field selection, feature definition, and blocker clearing.
- `SEALED_HISTORICAL_VALIDATION_POOL`: untouched rows/windows/symbols/sessions/regimes opened only after the rule, source fields, no-leak policy, duplicate denominator, cost assumptions, and stop conditions are frozen.
- `STRESS_ROBUSTNESS_POOL`: perturbation, cost/slippage stress, regime/session/symbol holdouts, outlier removal, placebo/baseline tests, and concentration diagnostics.
- `FORWARD_SHADOW_POOL`: current-market/current-system realism, prospective capture quality, execution/cost observability, live-code drift checks, and degradation monitoring.
- `FORBIDDEN_OR_CONTAMINATED_POOL`: slices whose outcomes, path labels, blocked-packet results, post-decision fields, or model-selection exposure contaminated the rule.

## Required Controls

Before any lane claims historical validation, it must produce or cite:

- data partition ledger with row/window/symbol/session/regime exposure status;
- frozen hypothesis and rule before validation slice access;
- source/as-of/no-leak contract;
- duplicate denominator policy;
- cost/spread/slippage assumptions where applicable;
- purged/embargoed split rules for time-neighbor leakage;
- walk-forward design when time ordering matters;
- cross-sectional holdouts by symbol, session, side, regime, volatility state, and news/non-news state when available;
- adversarial baselines: random/shuffled signals, session-only, volatility-only, simple momentum/reversion, and current GTOS baseline comparators;
- perturbation tests: delayed entry/exit, worse spread/slippage, random missed trades, removing best trades/months, and nearby parameter variation;
- multiple-testing debt ledger: variants tried, parameter paths, rejected branches, abandoned ideas, and final selection rule;
- effective-N, duplicate concentration, regime concentration, and outlier-dependence diagnostics.

## Anti-Staleness Rule

No future plan should state that an edge must wait weeks for forward shadow validation if there is an untouched historical validation slice available. The correct response is to build the sealed partition ledger and run the strongest source-safe historical validation design first.

Forward shadow remains required before live behavior promotion, but it is the realism layer after sealed historical validation, not a passive research bottleneck.

## Boundaries

This protocol does not authorize:

- dirty historical reuse as validation;
- post-hoc threshold rescue;
- hidden outcome-field use;
- blocked-packet outcome inspection;
- broker/account/order-history labels unless explicitly authorized by that evidence class;
- live trading prompt, risk, execution, permission, selector, safety, canary, MT5 order behavior, credential, remote, or registry changes;
- promotion claims without a separate promotion dossier.

## Next Required Route

After the current NOFILL forward source/control contract lane, G0 should open a cross-hypothesis historical partition and sealed-validation design lane. That route should inventory major hypothesis families and define which historical data is discovery-exposed, which can be sealed, and which validation/stress tests are allowed for each family.

Candidate route name:

`G0_CROSS_HYPOTHESIS_HISTORICAL_SEALED_VALIDATION_LEDGER_AND_TEST_PLAN`

Required output:

- master historical data partition ledger;
- hypothesis-family exposure matrix;
- sealed validation candidate inventory;
- stress/robustness design matrix;
- multiple-testing debt accounting plan;
- G12-ready audit prompt pack;
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
