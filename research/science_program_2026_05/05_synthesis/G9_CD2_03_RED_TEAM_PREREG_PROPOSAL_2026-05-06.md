# G9 CD2-03 Red-Teamable Prereg Proposal - 2026-05-06

**Lane:** `G9`  
**Assignment:** `CD2-03 - Offline-RL reward and risk-bank boundary`  
**Status:** `PREREG_PROPOSAL_RED_TEAM_READY_OUTCOMES_CLOSED`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Objective

Prepare a red-teamable, offline-only preregistration proposal for `HYP-G9-OFFLINE-RL-POLICY-009` using the G10 risk-bank boundary and the G6 no-retrace lifecycle boundary. This proposal does not open outcomes, edit master registries, promote a policy, change live risk, change execution, alter prompts, touch selectors/safety gates/permissions, call MT5, use paid data, or affect order behavior.

## Proposed Experiment Row

| Field | Frozen proposal |
| --- | --- |
| `experiment_id` | `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001` |
| `hypothesis_id` | `HYP-G9-OFFLINE-RL-POLICY-009` plus dependency rows `G10-HYP-RISKBANK-005` and `G6-HYP-002` |
| `frozen_at_utc` | `2026-05-06T09:31:53Z` |
| `outcome_review_opened` | `false` |
| `metric` | Primary: held-out `episode_reward_r` delta versus frozen hand-policy baseline under the G9 CD2-03 reward contract. Safety: minimum `risk_bank_after_action_r` must never be below `-1.0R`. |
| `cohort` | Future frozen offline replay episodes after G10/G6 lifecycle fields, exact path fields, and label/sample triggers exist. Current artifact opens zero outcome rows. |
| `exclusions` | Online exploration; live sizing/execution/risk changes; unsupported action; missing behavior policy; missing leg-level risk-bank ledger; missing duplicate group; unresolved same-bar ordering without conservative bound; unfilled re-entry counted as filled; broker actual-R pooled with synthetic path-R; outcome fields in state. |
| `duplicate_policy` | One countable episode per setup/opportunity lifecycle. Leg rows, retries, re-evaluations, pending lifecycle children, and same-symbol overlaps remain child/diagnostic rows. |
| `cost_slippage_assumptions` | Use frozen conservative cost model version; charge per leg and per exit; report sensitivity rows; missing close-side cost blocks promotion language and can keep results `not_computable_cost_blocked`. |
| `dsr_pbo_effective_n_policy` | DSR/PBO/effective-N required only after a frozen unseen split, policy universe, and sample floors exist. Otherwise report `not_computable` with explicit reason. Any future promotion-grade claim would require G1-style `dsr_p < 0.01`, `PBO < 0.40`, `effective_N >= 3`, and separate broker actual-R handling. |
| `label_separation_policy` | Primary proposal is `synthetic_path_r` only. `broker_actual_r`, `lifecycle_no_fill`, `fill_no_fill`, `observation_only`, and `context_only` labels remain separate artifacts and denominators. |
| `reproducibility_key` | `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001|reward_contract=G9-CD2-03-OFFLINE-RL-REWARD-CONTRACT-2026-05-06|outcomes_closed|NO_PROMOTION_VERDICT` |

## Outcome Opening Gates

The future experiment remains blocked until all gates below are satisfied in a separate artifact:

| Gate | Required evidence |
| --- | --- |
| G0/G9 lane boundary | G9-owned prereg only; no master-registry edit unless G0 later reconciles. |
| G10 risk-bank ledger | Every action has `realized_closed_leg_r`, `open_leg_stop_if_hit_r`, `estimated_remaining_cost_r`, and `risk_bank_after_action_r`. |
| G6 lifecycle/no-retrace fields | Exact decision entry price, ordered M1/tick path or explicit lower-TF blocker, lifecycle state, and no-retrace labels separated from R. |
| Behavior policy | Historical behavior policy and allowed counterfactual action set frozen before outcomes. |
| Duplicate control | Stable `episode_id` and `duplicate_group_id`; child rows cannot count as independent observations. |
| Cost model | Conservative cost/slippage/close-side assumptions frozen and versioned. |
| Same-bar handling | Conservative bound or exclusion before scoring. |
| Sample floors | G9 floor: 500 deduped training episodes and 150 held-out episodes, or `sample_size_blocked`; G10 risk-bank floor: 150 prospectively frozen resolved path rows for risk-bank claim; G6 no-retrace floor: 60 primary lifecycle candidates when that mechanism is used. |
| Statistics | DSR/PBO/effective-N policy declared; if not computable, the reason is explicit and promotion p-values stay forbidden. |

## Frozen Null And Alternative

Null:

`Offline RL or tabular Q-policy over GTOS states cannot match existing hand-tuned sizing/exit policies under identical cost, duplicate, label, lifecycle, and risk-bank controls.`

Alternative:

`A frozen offline policy over regime, side, instrument, framework, volatility, lifecycle state, and risk-bank state matches or beats hand policies in held-out offline replay without live exploration and without breaching the aggregate worst-case risk invariant.`

## Red-Team Checklist

| Review target | Question |
| --- | --- |
| Live exploration | Does any artifact request new exploratory actions from the live system? |
| Live behavior | Does any action imply live sizing, execution, prompt, selector, risk, permission, safety-gate, MT5, canary, or order change? |
| Risk bank | Can a policy receive positive reward after violating `risk_bank_after_action_r >= -1.0R`? |
| Duplicate counting | Can legs, retries, or overlapping active setups inflate `n` or effective-N? |
| Label separation | Are broker actual-R, synthetic path-R, lifecycle no-fill, fill/no-fill, and context labels kept apart? |
| Costs | Are per-leg and per-exit costs subtracted before reward comparison? |
| Same-bar ambiguity | Are unresolved fill/exit orderings excluded or conservatively bounded, never guessed? |
| DSR/PBO/effective-N | Is every future headline blocked unless the declared methodology gates are computable and passed? |
| Source/budget | Does any source become `validation_safe=true` or spend cash from this proposal? |
| Promotion drift | Does any section imply a policy is ready for deployment? |

## Stop Conditions

Stop and keep `NO_PROMOTION_VERDICT` if any of these occur:

- sample floor is unmet,
- policy universe was selected after outcome review,
- risk-bank ledger is missing or breached,
- duplicate grouping is absent,
- label families mix,
- same-bar ambiguity is guessed,
- close-side cost is unavailable for a claimed exit/re-entry comparison,
- broker actual-R is required but not available in a separate preregistered label lane,
- source/budget ledger remains `$0` and a paid source would be required,
- a live trading surface would need to change.

## Non-Authorization Boundary

This proposal is not a policy promotion, live-risk proposal, live-execution proposal, order-routing proposal, prompt edit, selector edit, safety-gate edit, canary edit, paid-data plan, credential change, or remote-push request.

## NO_PROMOTION_VERDICT

`NO_PROMOTION_VERDICT` is preserved. The proposal is ready for G12-style red-team review only.
