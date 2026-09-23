# The instrumented 2-day walk — 2026-01-01/02, every candidate's fate (B1)

**Session FA continuation, Phase B item 1 — the owner's literal ask.** One 2-day January
lane window, CJ's exact cut+repair recipe plus two default-off instrumentation patches
(`hard_eligibility_observability`, `condition_feature_propagation`), `--keep-outputs`.
Arm: S0R0, purpose LANE_ITERATION, R2 contract bound (sha `0667d2de…`), source plan
digest `8b7d3b26…`, partition authorization `gtos_trainer_partition_registry_v2` with
blackout checked. Run: 481 s, 3.38 GB peak. Economics **identical to the fence arm**
(4 trades / 8 orders / 96 scorecards / 8,448 missed) — the instrumentation moved nothing,
as designed. Machine artifacts: `WALK_2D_ANNEX.json` + `WALK_2D_CANDIDATES.jsonl.gz`
(one row per candidate-fate) beside this file; raw route
`fa2-integration-20260803/research/operations/…/attempt_5_typed_sparse/FA2_WALK_S0R0_2D/`.
Everything here is DEVELOPMENT-FITTED lane evidence, billed:false.

## Day 1 — 2026-01-01: the system correctly stands down

Zero candidates, zero scorecard windows, zero trades. The session guards refuse the
holiday end to end (DECISION rows carry no session; the fence adjudication independently
established `source_sha256` null on all 2,304 day-1 rows — no session, no slice). A whole
calendar day produces nothing but refusal evidence, exactly as intended. **L1 verdict
input: the stand-down path is clean.**

## Day 2 — 2026-01-02: 96 windows, 8,448 candidate-fates, 4 trades

### The funnel, walked

| stage | count | share |
|---|---:|---|
| candidate-fates entering the pool | 8,448 | 100 % |
| … blocked `cost_authority` | 7,029 | **83.2 %** |
| … blocked `source_or_signature_authority` | 510 | 6.0 % |
| … blocked `other` | 298 | 3.5 % |
| … blocked `execution_fillability` | 280 | 3.3 % |
| … blocked `package_authority` | 237 | 2.8 % |
| … blocked `scheduler_selection` | 46 | 0.5 % |
| … blocked `selector_materialization` | 26 | 0.3 % |
| … blocked `fill_realism` / `marketable_guard` / `daily_lockout` | 15 / 6 / 1 | 0.3 % |
| **hard-eligible at the finalizer (whole day)** | **5 pairs over 4 windows** | **0.06 %** |
| executed | 4 | 0.05 % |

Family mix entering the pool: `current_fvg_fill` 5,456 (64.6 %), `current_ob_retest`
1,572, `current_breaker_re_entry` 588, `liquidity_sweep_reclaim` 275, seven more ≤ 212
each. The commission repair charged every row (8,452/8,452 calls, mean 0.0736 R, max
1.43 R — per-symbol table in the run receipt). Scoreable subset: 1,412 rows — 413
positive (+306.1 R), 999 negative (−1,899.2 R).

### The finding that names the day: selection is DEGENERATE

The `hard_eligibility_observability` patch lifted the finalizer's exact per-window pool:

- **92 of 96 windows: hard-eligible pool EMPTY.**
- 3 windows: exactly one candidate (08:00, 09:00, 13:15).
- 1 window: exactly two candidates (16:15) — **and both are XAUUSD LONG** (same symbol,
  same side). The rank-1 (`c336…`, scheduler-preserved rank 1, transfer score −0.11906)
  was stamped `same_symbol_same_side_window_duplicate_requires_explicit_scale_or_replace`;
  the neutral-hash-preferred `a996…` (rank hash `1bd8f1…` < `e8a658…`) executed.
  Whichever ordering had won, **the day's book was identical**.

**By the finalizer stage there is nothing left to select between.** On this day the
S0-vs-S1 selection axis had zero economic degrees of freedom — the one contested window
was a same-symbol-same-side pair. This is the sharpest day-scale corroboration of the
campaign's arm-indistinguishability and of Phase 1's "selection is not the defect": the
funnel (cost gate + upstream authorities) decides the book; the selector chooses among
survivors that barely exist. It also bounds what the seed replicates (B2) can move:
a different neutral seed can only reorder windows with ≥2 candidates — composition of
the pool, not choice within it, is where day-to-day variance lives.

In-band honesty note: the option rows declare `hard_eligibility_uses_outcome_fields:
true` / `uses_prior_closed_trade_outcome_fields: true` (the adaptive memory guard —
L6's path dependence, declared) while `neutral_rank_uses_outcome_fields: false` — the
separation between eligibility (outcome-coupled) and neutral ordering (outcome-free)
is stamped correctly on every row.

### The four trades, end to end

All four: `dynamic_geometry_policy = momentum_exhaustion` (router constant — see L3c),
risk 0.10 % fixed (R0), filled at the limit, lifetime capped at 120 min by
`REPAIRED_PENDING_EXPIRY`.

| # | window | symbol/side | family | final R | cost R | exit story (TRADE × ORACLE joined) |
|---|---|---|---|---:|---:|---|
| 1 | 08:00 | XAUUSD LONG | session_open_range_break | **+0.875** | 0.056 | Giveback close. The raw limit path marked only **+0.224** at the 120-min wall (tick_bid 09:59:59.8) — the policy overlay's giveback exit **beat the wall by +0.65 R**. |
| 2 | 09:00 | XAGUSD SHORT | current_fvg_fill | **−0.261** | 0.146 | `path_end_mark_to_market` at the wall (10:59:59.8, tick_ask) — the 120-minute ceiling converts an unresolved position into a marked loss. The L7 story in one row. |
| 3 | 13:15 | XAGUSD SHORT | current_fvg_fill | **+0.906** | 0.073 | Giveback close — but the raw path marked **+1.222** at the wall: the giveback **cost −0.315 R** here. Same contract, opposite sign to trade 1. |
| 4 | 16:15 | XAUUSD LONG | current_fvg_fill | **+0.778** | 0.065 | `giveback_close` while `terminal_outcome = stop_reached_before_target` (stop hit 18:10:21): **the two vocabularies describe different layers** — the raw path DID reach the stop, but the policy overlay had already harvested +0.778 at the giveback trigger before it. Not a contradiction; two truths needing two names (R-SCHEMA). |

Notes. (a) Trades 2 and 3 are the **same candidate** (`bf030f05…`) — refused/expired
earlier, re-admitted at 13:15; the same idea lost at the wall and won by giveback four
hours later. (b) The giveback contract moved ±: +0.65 (t1), −0.315 (t3) vs wall marks —
2 days cannot price it; the exit frontier (T1 on the path sidecar) can. (c) Day book:
gross +2.298 R, cost 0.340 R, net ≈ +1.96 R on 4 fills — one good day of the family
that is −5.5 R/month over the re-clocked window; a 2-day walk illustrates mechanism,
never economics. (d) Condition features on the executed rows put market context in-band:
t1 fired 3 bars after session open at the top of its lookback range (`close_position…
0.994`) with range compression (0.774); t4 fired at range BOTTOM (0.024) with vol
expanding (`atr14/atr50` 1.80, `c2c vol 8/48` 1.92) — LONG at the low of an expanding
range, and the raw path indeed stopped first.

### The biggest missed winner, walked

`current_ob_retest` AUDUSD SHORT at 14:30 (`broadorigin_d4140e10…`): net proxy
**+2.169 R**, cost_r 0.212, candidate EV +0.765 — blocked `cost_authority`. The single
largest opportunity of the day died at the cost gate, not at selection — the L3a/L2
winner-kill mechanism, one concrete row of Phase 1's +3,213.5 R January aggregate.

## Instrumentation findings (the walk's own tooling, disclosed)

- **WALK-F1 — `condition_feature_propagation` never reaches the pool it names.** The
  patch wraps `ledger_namespace_alias_fields` and its stats show the feature block
  present on 93,954 of 97,104 calls — but the fields land only on TRADE (4/4) and ORDER
  (8/8) rows; **0 of 8,448 MISSED rows** carry `predecision_features` or any status
  stamp. ~~because the missed-row assembly path does not consume the wrapped helper's
  return~~ **Root cause corrected by the Phase-C R-SCHEMA implementation (commit
  `364208a0b`): the assembly path DOES consume the wrapped helper (all three
  `ledgers["missed"].append` sites splat it, v4t:93054/:92587/:93560); the drop is
  attempt5's transport compactor — `compact_missed_opportunity_rows`
  (`replay_acceleration_attempt5_typed_sparse_runner.py:5488`), a strict `keep_fields`
  allowlist that strips the 7 condition fields before `append_jsonl` on both write
  paths.** Fixed in Phase C by rebinding the compactor at runtime when the patch is
  active (patch stays default-off; off-state byte-identical, pinned by test). Until an
  arm runs with it, per-candidate market context exists for executed rows only.
- The first walk run omitted `--keep-outputs` and the runner auto-removed the route
  (receipt `outputs_removed`); the re-run kept it. Operating rule: **every evidence arm
  passes `--keep-outputs`.**

## What the walk settles in FULL_FLOW_SPEC

- **L0 CONFIRMED-HONEST**: purpose/window/blackout/contract/digest all stamped and
  verified in the run receipt; cuts+repairs enumerated with per-cut stats; repair
  demonstrably live on every row.
- **L1 CONFIRMED** on both branches: holiday stand-down (day 1) and 96-window assembly
  (day 2).
- **L3c SETTLED: the router is a constant** — `momentum_exhaustion` on 8,448/8,448
  (both `dynamic_geometry_policy` and `selected_policy_for_expected_net_r`). One exit
  contract for ten families is a dead config surface, not a router.
- **L6 MEASURED**: the degenerate hard pool (92/96 empty; 5 pairs; the one contest a
  same-symbol pair); memory-guard coupling declared in-band; cooldown conflicts visible
  on trades 3/4 (fence adjudication's namespace atoms).
- **L7/L8 ILLUSTRATED at row level**: the wall converts unresolved positions to marks
  (t2); the giveback cuts both ways (+0.65 / −0.315); the exit-vocabulary duality is a
  naming defect, not a logic defect.
