# V120E Blocker Taxonomy And Missed Attribution Brief

Broker/live/final remain closed. Local replay/package authority remains full. This checkpoint is a correctness and diagnostic-ledger repair, not a trade-release patch.

## Current Completed Run

- Latest prefix: `BROAD_LIVE_AS_IF_REPLAY_V120D_RAW_REJECT_PROMOTION_CONTRACT_20260515_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window: `2026-05-15..2026-05-15`
- Status: `broad_live_as_if_replay_zero_candidates_no_terminal_execution_broker_live_closed`
- Rows: 96 scorecard, 0 order, 0 trade, 672 missed, 15 bucket, 275 source, 0 oracle
- Result: 0 trades, `0R` net/gross/final, `$0` cash PnL, W/L/F `0/0/0`
- Interpretation: V120D removed the two V120C invalid low-limit-fillability raw-reject fills. That is a local truth repair, not proof of a profitable system; it exposes reallocation/admission starvation.

## Active Process State

No broad replay, pytest, compile, or git-helper process is currently active. Do not duplicate a broad run.

## Baselines

- V89D five-day hostile bucket: 56 trades, `+34.84520454R`, W/L/F `41/15/0`
- V90 five-day hostile bucket: 51 trades, `+28.84201157R`, W/L/F `37/14/0`, scorecard-artifact warning
- V92 five-day hostile bucket: 51 trades, `+29.35570236R`, W/L/F `37/14/0`
- V120C same day: 2 trades, `-2.19911518R`, gross/final `-2.0R`, cash `-$219.7906166`, W/L/F `0/2/0`
- V120D same day delta vs V120C: removed 2 invalid losing fills, order rows `6 -> 0`, trade rows `2 -> 0`, net R `-2.19911518 -> 0`

## Dirty Worktree

Tracked dirty code/config/test files include `config/agent_config.yaml`, route builders/verifiers/harness scripts, `src/components/selector_v4.py`, `src/research/moonshot_scheduler_v4_best_trade_allocator.py`, `src/research/reduced_risk_action_reason_contract.py`, `src/research_infra/v4_timewarp_simulated_live_research_loop.py`, and related tests. Context OS files and old science JSONL deletions are also dirty and must not be mixed into a route commit unless intentionally scoped.

## Subagent Findings

- Franklin: incorporated in V120D. Low passive-limit fillability was hidden by high entry-quality fill on selected losers.
- Russell: incorporated in V120D. Raw reject rows were promoted into executable open-reduced rows without a separate order-executable promotion contract.
- Ptolemy: incorporate now. `risk_pct_basis_missing` is mostly stale attribution; real causes are fill/guard/daily/lifecycle/stop/headroom, and replace-pending missed rows are lifecycle/root-authority veto diagnostics with negative counterfactual fills.
- Copernicus: incorporate now and in the next policy batch. There are +53.50441866R cost-passed positive missed rows in V120C, but diagnostic-only rows are not executable and blanket guard/stop/risk release is negative. Preserve floors; only release with causal predecision evidence.

## Known Mismatch Classes

- source-bound -> candidate: use exact replay-window denominators; one-day V120D is local repair evidence only.
- candidate -> selector: router-refusal floors block some positive diagnostics, but global relaxation is unsafe.
- selector -> scheduler: diagnostic materialization is now split from order-executable promotion, but replacement/reallocation is still starved.
- scheduler -> risk: generic `risk_pct_basis_missing` masks selector materialization, cost, scheduler displacement, lifecycle, guard, and stop causes.
- risk -> order: not-order-executable rows need named classes without becoming executable.
- order -> lifecycle: replace-pending lifecycle-veto rows remain diagnostic unless predecision lifecycle authority exists.
- fill -> exit: no V120D fills; exits are not proven by this local slice.
- ledger: 598 V120D missed rows have no official transfer fields and fall back to stale sizing risk labels.

## Same-Root Patch Batch

Patch `v4_timewarp_simulated_live_research_loop.py`, `moonshot_scheduler_v4_best_trade_allocator.py`, verifier blocker allowlist, and focused tests.

Patch types:

- Correctness: make generic `risk_pct_basis_missing` weak; prefer explicit miss/scheduler/lifecycle/cost/guard/stop causes.
- Diagnostic ledger: add blocker classes for `selector_materialization`, `scheduler_selection`, `cost_authority`, `package_authority`, and `lifecycle_authority`; stamp not-order-executable missed diagnostics with a reason/class/source.
- Performance: none in this batch.

Expected before replay:

- Candidate -> scorecard unchanged.
- Scorecard -> order unchanged.
- Order -> fill unchanged.
- Missed positive/negative R unchanged, with clearer reason buckets.
- Trade count/net/gross/final R unchanged for same-day V120D if rerun before policy release.
- Cost REFUSED/source-gap executions stay zero.
- Risk-reduced/full-risk distribution unchanged.

Success:

- V120D-shaped missed rows no longer aggregate under stale `risk_pct_basis_missing` when explicit miss/scheduler/cost reasons exist.
- Diagnostic rows remain non-order-bound and non-trade-bound.
- Verifier accepts the expanded blocker taxonomy.

Failure:

- Diagnostics become executable without explicit order authority.
- `risk_pct_basis_missing` remains dominant for rows with explicit miss/scheduler causes.
- Verifier rejects the new blocker classes.
