# G9 CD2-03 Offline-RL Reward Contract - 2026-05-06

**Lane:** `G9`  
**Assignment:** `CD2-03 - Offline-RL reward and risk-bank boundary`  
**Status:** `FROZEN_REWARD_CONTRACT_PROPOSAL_OUTCOMES_CLOSED`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Scope

This artifact translates the CD2-03 offline policy comparison into an offline-only reward definition. It is a G9-owned research contract, not a master-registry edit, policy promotion, live risk change, execution change, selector change, prompt change, MT5 action, canary change, paid-data request, or order-behavior change.

## Controlling Inputs Read

| Input | Contract use |
| --- | --- |
| `G9_G9_AI_ML_SYSTEMS_GOAL_PROMPT_2026-05-06.md` | G9 lane boundary, offline RL as shadow-only research, no live exploration. |
| `G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md` | CD2-03 objective, blocker checks, and required stop output. |
| `SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md` and G0 wave-2 reconciliation | Master rows remain inventory only; survivor backlog is zero. |
| `G9_AI_ML_SYSTEMS_HYPOTHESES_2026-05-06.json` / preregs | Seed `HYP-G9-OFFLINE-RL-POLICY-009` and `EXP-G9-OFFLINE-RL-009`. |
| `G10_HYPOTHESIS_ROWS_2026-05-06.json` / preregs | Seed `G10-HYP-RISKBANK-005` and `G10-EXP-RISKBANK-005`. |
| `G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json` | Seed `G6-HYP-002`; no-retrace and fill/no-fill stay lifecycle labels. |
| `G1_VALIDATION_STATISTICS_SYNTHESIS_2026-05-06.md` / preregs | DSR/PBO/effective-N, no-leak, target-trial, sample-floor discipline. |
| `PHASE3_DEFERRED_TASKS_AND_NEXT_STEPS_LEDGER_2026-05-02.md` | Canonical risk-bank invariant and V3 design-only boundary. |
| `EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_2026-05-03.md` | J46/J49 and S79 are comparators only; label classes must stay separate. |

## Frozen Reward Definition

### Episode Unit

The independent reward unit is one deduped setup/opportunity lifecycle:

`episode_id = stable setup_id or candidate_id plus symbol, session, decision_time_utc, side, framework, and duplicate_group_id`.

Leg rows inside an episode are child rows, not independent trades. Duplicate active setups, retry attempts, re-entry legs, and lifecycle child events cannot inflate raw `n` or effective-N.

### State Inputs

Allowed state fields must be available as of the decision or policy-evaluation time:

- `state_asof_utc`
- `symbol`
- `session`
- `side`
- `framework`
- `regime`
- `volatility_bucket`
- `lifecycle_state_before_action`
- `behavior_policy_action`
- `cost_model_version`
- `source_path_cutoff_utc`
- `duplicate_group_id`
- `lower_tf_available`
- `same_bar_ambiguity_state`
- `risk_bank_before_action_r`

Forbidden state fields include broker actual-R, synthetic path-R, TP/SL outcome, fill outcome after the action, future candle/tick path, revised source values, or any post-outcome diagnostic.

### Action Space

The offline policy may only choose from frozen research actions that do not alter live behavior:

| Action ID | Meaning | Live effect |
| --- | --- | --- |
| `A0_HAND_POLICY_BASELINE` | Current frozen hand-policy comparator, including J46/J49 and S79 context where applicable. | None |
| `A1_NO_REENTRY_OR_PASS` | Keep the initial policy and do not add a re-entry leg. | None |
| `A2_RISKBANK_BOUNDED_REENTRY_CANDIDATE` | Add one frozen re-entry candidate only if all risk-bank, lifecycle, ambiguity, and cost gates pass. | None |
| `A3_REJECT_INVALID_OR_UNSUPPORTED` | Force no offline action when the proposed action is unsupported, leaky, duplicate, ambiguous without a conservative bound, or risk-bank invalid. | None |

No action may represent a live sizing rule, live order instruction, online exploration step, prompt change, selector change, or risk-configuration change.

### Risk-Bank Invariant

Every proposed action is admissible only if the leg-level ledger proves:

```text
realized_closed_leg_r + sum(open_leg_stop_if_hit_r) - estimated_remaining_cost_r >= -1.0R
```

Definitions:

- `realized_closed_leg_r`: closed-leg realized or path-synthetic R inside the current episode, net of already charged leg costs, depending on the label lane.
- `open_leg_stop_if_hit_r`: worst-case R if each currently open leg is stopped after the proposed action.
- `estimated_remaining_cost_r`: non-negative conservative estimate of entry, exit, spread, slippage, commission, swap, and close-side costs still needed to resolve the episode.
- `risk_bank_after_action_r`: the value of the full invariant after applying the proposed action.

Hard rules:

- If `risk_bank_after_action_r < -1.0`, the action is invalid and excluded from primary policy scoring.
- If a policy repeatedly selects invalid actions, the policy receives a contract-failure count and cannot be compared as a candidate policy.
- A profitable or locked initial leg does not authorize a re-entry unless the aggregate worst-case ledger remains above `-1.0R` after costs.
- Missing leg-level ledger fields are a blocker, not an imputation target.

### Reward Function

Primary offline reward is defined only for valid, deduped, resolved `synthetic_path_r` episodes:

```text
episode_reward_r =
  final_episode_path_r
  - per_leg_cost_r
  - per_exit_cost_r
  - conservative_unresolved_cost_buffer_r
```

Additional controls:

- Broker actual-R is never overwritten by synthetic path-R. Any future broker actual-R experiment requires a separate prereg, sample floor, and cost ledger.
- Fill/no-fill and no-retrace outcomes are lifecycle labels. They can gate eligibility and report secondary rates, but they are not losing R by default and cannot be pooled into R metrics.
- Unfilled pending re-entry legs contribute `0.0R` incremental realized reward and are reported in lifecycle metrics, not as filled losses or wins.
- Same-bar fill/exit ambiguity must be excluded from primary reward unless a predeclared conservative lower bound exists. Guessed ordering is forbidden.
- Costs are charged per leg and per exit. A missing close-side cost estimate blocks promotion language and triggers a sensitivity row in research reports.

### Comparison Baseline

Offline RL is compared only against frozen hand-policy comparators:

- `CAND-001-J46-J49-LIVE-BASELINE` as current live/J46-J49 comparator.
- `CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR` as simulation/risk-policy context only.
- Any V2/V2b/V3 path candidate remains discovery-only unless a later prereg opens an unseen validation split.

### Outcome Review State

This reward contract opens no outcome review. It freezes the reward, gates, exclusions, and label boundaries for future offline-only preregistration. Current status remains `NO_PROMOTION_VERDICT`.

## Required Blocker Checks

| CD2-03 blocker | Contract decision |
| --- | --- |
| No live sizing or execution change | Hard blocked; action space has no live effect. |
| Risk-bank invariant | Required before scoring any re-entry action. |
| Duplicate lifecycle controls | Episode-level dedupe; child legs do not count as independent trades. |
| Broker actual-R versus synthetic path-R separation | Synthetic path-R primary for this contract; broker actual-R requires separate future prereg. |
| DSR/PBO/effective-N policy | Required for any future result; otherwise report `not_computable` with reason. |

## Red-Team Questions

1. Does any state field leak post-action path, fill, or outcome information?
2. Can an invalid re-entry be rewarded indirectly through a fallback score?
3. Are unfilled re-entries, lifecycle no-fill, and broker actual-R kept out of synthetic R performance?
4. Are duplicate setup, retry, and leg rows prevented from inflating sample size?
5. Does the cost model charge every leg and exit before policy comparison?
6. Does every same-bar ambiguity have a conservative bound or exclusion?
7. Does any sentence imply policy promotion, live exploration, or live risk behavior?

## Non-Authorization Boundary

This contract does not authorize online RL, live exploration, policy deployment, live sizing, execution behavior, risk-bank activation, prompt changes, selector changes, safety-gate changes, MT5 calls, canary calls, paid data, credentials, remote pushes, or order behavior.

## NO_PROMOTION_VERDICT

`NO_PROMOTION_VERDICT` is preserved. The only output is a frozen offline-only reward contract for future red-team review and preregistration.
