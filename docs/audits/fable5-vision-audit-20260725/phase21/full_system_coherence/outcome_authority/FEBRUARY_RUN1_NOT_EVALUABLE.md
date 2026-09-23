# February MARKET-top-choice validation — run 1: NOT_EVALUABLE (receipt)

**Date:** 2026-08-10. **Author:** orchestrator session (Fable 5), executing the frozen
`MARKET_TOP_CHOICE_VALIDATION_RULE_V1.json` on the owner's go-ahead.

## What happened

The 20 February candidate roots generated 2026-08-09/10 (`/private/tmp/w21-market-top-feb-dc534.p3eUWY`,
per-day `authority_root_sha256` in each `run_summary.json`; preserved in
`hermes-evidence-hold-20260727/w21-tmp-lab-recovery-20260810/`) **cannot satisfy the rule's own
cost-completeness requirements** and the scoring run over them is declared NOT_EVALUABLE under the
rule's clause `candidate_population.missing_or_incomplete_cost_is_ineligible_not_zero` /
`validation.missing_selected_cost_or_source`.

Measured on the run-1 outputs (probe, cost fields only — no outcome consumed):

| field | 2026-02-02 | 2026-02-13 | 2026-02-27 | January 2026-01-05 (control) |
|---|---|---|---|---|
| rows | 5,195 | 5,450 | 5,178 | 6,488 |
| `swap_cost_r` None | 5,195 (100%) | 5,450 (100%) | 5,178 (100%) | 0 |
| `commission_r` None | 5,195 (100%) | 5,450 (100%) | 5,178 (100%) | 0 |
| `spread_r` None | 4,740 (91%) | 4,991 (92%) | 4,659 (90%) | 0 |
| `cost_r` | flat `0.12` on every probed row | same | same | exact 4-component sum, 6,488/6,488 |

The 455 spread-present rows on 02-02 are exactly the four tick-bearing symbols
(EURUSD/USDJPY/XAUUSD/XAGUSD) — spread came only from ticks; the model branch and the swap and
commission engines failed on every row.

## Root cause (isolated in code)

`w21_generate_feb_day.py` obeyed the rule's `validation.runtime_config_change` clause literally:
base `config/agent_config.yaml` + only the truth-mode key. **Base config carries no
`broker_profile`**, so `account_for(server=None, namespace=None)` raises `CostTruthError`
(`src/costs/model.py:1580`) inside the pretrade cost machinery:
- the spread-model branch source-gaps (`_predecision_tick_for_cost`,
  `v4_timewarp_simulated_live_research_loop.py:60274-60299`) on the 20 non-tick symbols;
- side-aware swap and broker-true commission fail on all 24 (`missing_broker_account_profile_namespace`,
  `missing_broker_symbol_spec_fields`, `missing_side_aware_swap_schedule` — reproduced standalone);
- the packet REFUSES (`broker_calibrated_replay_cost_packet` → `not_evaluable_incomplete_component_sum`),
  and the legacy producer default then stamps flat `cost_r = 0.12`
  (`cost_r = safe_float(packet.total_cost_r, broker_replay_default_total_cost_r(config))`,
  timewarp `:69036-69039`) — the convenience-default class wave 20 flagged as the surviving
  producer defect.

**The rule froze a runtime configuration that cannot satisfy the rule's own
`complete declared costs` requirement.** January's development runs (whose diagnostic the rule's
`development_finding` cites) carried complete four-component costs, so January's (lost) generator
supplied the broker profile.

## Why the no-tuning discipline survives

The scoring run crashed while loading day 1, **before any February row reached the model,
selection, or any outcome-consuming code** (`float(None)` in the hash-bound
`candidate_funnel_analysis.py:222`). Post-crash probes read cost/feature fields and row counts
only. The amendment below is forced by a January-visible fact (base config lacks `broker_profile`)
discoverable with zero February data. No model, feature, threshold, selection, or gate parameter
changes.

## Reproduction validation for the amended configuration

Candidate configurations were bisected by regenerating **January 2026-01-05** (already-opened
development data) and comparing to the original run (`authority_root caac9f4a…`):

| mode | population | all rule-consumed fields identical | residual |
|---|---|---|---|
| `merge-ftmo` (research profile) | 6,488/6,488 | 2,617 rows | degraded 1,277 rows to flat 0.12 — rejected |
| **`merge-310`** (live profile `operator_profile.yaml` deep-merged) | **6,488/6,488** | **6,488/6,488** (`cost_r`, `spread_r`, `expected_slippage_r`, `swap_cost_r`, `commission_r`, entry/stop/target, `risk_reward_ratio`) | only `broker_pretrade_cost_r` (populated 5,479 original vs 2,285 repro) + config-envelope hash |

`broker_pretrade_cost_r` is **consumed nowhere in the frozen pipeline** — it is absent from the
rule's feature list, from `eligible()` (cost_r-based), and from `_lifecycle_row`'s label fields.
The authority-root non-match is fully attributed to that diagnostic field plus the config-envelope
echo. Generator: `w21_generate_day_r2.py` (committed alongside; mode `merge-310`).

## Disposition

- Run-1 outputs preserved (hold + `/private/tmp/w21-market-top-feb-dc534.p3eUWY`) as this receipt's
  evidence; **never to be scored**.
- Rule amended as `MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json` — execution-layer clause only;
  model/features/selection/gates/days verbatim from V1.
- February regenerated under `merge-310` (`/private/tmp/w21-market-top-feb-r2`), then scored once
  by the V1.1-bound scorer.
