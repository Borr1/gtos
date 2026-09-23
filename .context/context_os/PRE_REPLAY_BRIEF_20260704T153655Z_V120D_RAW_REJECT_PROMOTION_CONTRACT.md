# V120D Raw-Reject Promotion Contract Pre-Replay Brief

Status: current pre-replay brief for the next targeted proof. Broker/live/final remain closed. This is a correctness repair for executable replay authority, not a final-system claim.

## Latest Completed Run

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V120C_MATERIALIZED_SELECTOR_ORIGIN_CONTRACT_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window: `2026-05-13..2026-05-17`
- Rows: 288 scorecards, 8 order rows, 2 filled trades, 2765 missed rows
- Result: `-2.19911518R` net, `-2.0R` gross/final, `-$219.7906166` cash PnL, W/L/F `0/2/0`
- Behavior: two BTCUSD LONG reduced-risk fills on `2026-05-15`, both raw selector `reject` materialized to effective `open-reduced-risk`, both stopped out.

## Active Process State

No broad replay is running. No duplicate broad replay should be launched. Targeted proof is appropriate because both V120C filled losers occurred on `2026-05-15`.

## Baselines

- V89D same 5-day hostile window: 56 trades, `+34.84520454R`, W/L/F `41/15/0`
- V90: 51 trades, `+28.84201157R`, W/L/F `37/14/0`, with scorecard-artifact warning
- V92: 51 trades, `+29.35570236R`, W/L/F `37/14/0`
- V119C: 5 trades, `-5.50984356R`, W/L/F `0/5/0`
- V120C: 2 trades, `-2.19911518R`, W/L/F `0/2/0`

## Incorporated Subagents

- Franklin: incorporated. Selected losers used `entry_quality_fill_probability=0.95` but only `predecision_limit_fillability` around `0.42`; low passive-limit fillability needed a separate executable-promotion guard.
- Russell: incorporated. Raw selector `reject` rows became executable through materialized open-reduced authority, while high-opportunity cost-passed missed rows stayed diagnostic. The fix splits diagnostic materialization from order-executable promotion.

## Same-Root Batch Patched

- Runtime: raw-reject materialization now stamps `raw_selector_reject_open_reduced_order_executable_promotion_*` fields and sets order-executable authority false unless the contract passes.
- Scheduler: package replay order-executable authority independently enforces the raw-reject promotion contract and predecision limit-fillability floor.
- Verifier: selected-package executed scan uses effective selector action for executable action checks and separately flags raw-reject promotions without contract or below the limit-fillability floor.
- Tests: focused scheduler and verifier regressions cover the V120C failure mode.

## Expected Effects

- Candidate -> scorecard: unchanged.
- Scorecard -> order: low-limit-fillability raw-reject promotions should become blocked/missed rather than executable.
- Order -> fill: V120C BTCUSD low-fillability losers should not fill unless they clear the explicit promotion contract.
- Missed positive/negative R: may increase because invalid fills become visible missed/blocked rows; this is acceptable if reasons are explicit.
- Trade count/net R: may improve by removing invalid losers, but that is a local repair proof, not a final edge proof.
- Cost REFUSED/source-gap executions: must remain zero.
- Risk distribution: full-risk likely remains zero until the next risk-expression signing batch.

## Targeted Proof

Run `BROAD_LIVE_AS_IF_REPLAY_V120D_RAW_REJECT_PROMOTION_CONTRACT_20260515_REPAIRED_ONLY_COMPACT_FULLGRID` on `2026-05-15..2026-05-15`, repaired-only compact fullgrid.

Helped if:

- executable raw-reject promotions without contract are zero;
- the two V120C BTCUSD low-limit-fillability losers no longer fill;
- blocked rows retain scoreable missed-opportunity accounting and named promotion failures;
- cost REFUSED/source-gap execution remains zero;
- verifier scans pass for the new contract.

Failed if:

- the same low-fillability raw-reject rows still fill;
- improvement comes from hidden suppression without missed accounting;
- valid higher-limit-fillability candidates are blocked without a named predecision reason.
