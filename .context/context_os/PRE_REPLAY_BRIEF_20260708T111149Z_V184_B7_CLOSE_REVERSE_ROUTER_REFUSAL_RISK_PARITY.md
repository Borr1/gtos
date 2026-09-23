# V184 B7 Pre-Replay Brief - Close-Reverse Router-Refusal Risk Parity

Generated UTC: 2026-07-08T11:11:49Z

## Control State

- Fable batch: B7 runtime transfer.
- Latest completed replay baseline: `BROAD_LIVE_AS_IF_REPLAY_V183_B7_SIGNED_EXECUTABLE_COOLDOWN_RELEASE_PROMOTION_CONTRACT_20260604_20260605_XAUUSD_TARGETED`.
- Broker/live/final remain closed. This patch does not grant broker mutation, live authority, or final selection.
- Replay scope for proof: same bounded XAUUSD 2026-06-04..2026-06-05 targeted slice. This is a local repair proof only, not full-reservoir conversion evidence.

## Baseline Evidence

V183 remained behavior-neutral versus V182:
- candidates / scorecards / trades / missed / buckets: `1130 / 184 / 7 / 1122 / 30`;
- W/L/F: `4/3/0`;
- net/gross/final R: `+0.28315612 / +0.86066761 / +0.86066761`;
- cash PnL: `+531.95387131`;
- executed broker-cost REFUSED/source-gap rows: `0 / 0`.

Aristotle returned the concrete next leak:
- V181 filled `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00` as a LONG `new_position` winner (`+0.29090804R`);
- V182/V183 added a 17:00 SHORT, making the 17:45 LONG a `close_and_reverse`;
- lifecycle then rejected it with `package_lifecycle_action_resolution_required:expected_net_r_below_floor`;
- the row was not a source gap. It was a consumer mismatch between source-bound router-refusal materialization floors (`0.55/0.70/0.55`) and stricter close/reverse floors (`0.80/0.75/0.45`).

## Patch Batch

Files changed:
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_broad_replay_repair_config.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`

Repair class:
- behavior-changing correctness repair;
- not a suppression rule;
- not a broad cost/source/fillability bypass;
- keeps REFUSED/source-gap/unfillable rows non-executable;
- keeps broker/live/final false.

Root fixes in this batch:
- close/reverse lifecycle now has explicit router-refusal source-bound floors instead of reusing stricter generic close/reverse floors;
- those floors are propagated into selected scheduler option and candidate-decision inputs before final signed-risk validation;
- stale signed authority packets can be repaired only when current predecision package aliases, broker-cost packet, fillability, and quality-source provenance prove the same authority;
- scheduler no longer treats every `candidate_decision_inputs.*` quality source as inferred when the boundary is predecision/no-outcome;
- executable source-bound boolean aliases can consume sleeve/source-bound match context, while diagnostic-only rows without the boolean remain non-executable;
- risk-finalizer probe/cooldown release fields now preserve raw-selector promotion and cooldown release provenance.

Focused proof passed before replay:
- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k 'package_executable_authority_rederives_stale_partially_materialized_alias_status or optional_confidence_default_is_warning_not_package_authority_veto or optional_confidence_warning_does_not_change_signed_authority_hash or package_executable_authority_does_not_treat_executable_flag_as_source_bound_proof' -q --tb=short`
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k 'package_cooldown_release_uses_raw_selector_promotion_contract_for_signed_executable_daily_loss_lockout or risk_finalizer_primary_probe_alias_fields_preserve_cooldown_release_contract or runtime_close_reverse_uses_router_refusal_lifecycle_floors_for_signed_package_rows or runtime_risk_reconciles_package_close_reverse_lifecycle_in_replay or package_router_refusal_authority_daily_loss_release_is_narrow_replay_path' -q --tb=short`
- `python3 -m pytest tests/test_broad_replay_repair_config.py -k 'repaired_profile_routes_marketable_package_entries_only_in_no_broker_replay or repaired_profile_forwards_window_headroom_policy_to_scheduler' -q --tb=short`

## Expected Replay Effect

Expected improvement class:
- better lifecycle-to-risk conversion and source-bound router-refusal signed floor parity, not broad trade blocking.

Expected measurable movement:
- candidate count: should remain near V183 (`1130`) for the same scope;
- scorecard count: should not collapse;
- order/trade transfer: the 17:45 source-bound router-refusal close/reverse row should either fill again or move to a different exact runtime blocker;
- missed positive R: should fall if that row is restored;
- missed negative R: may also move if other causal rows meet the same contract;
- net R: should improve relative to V183 if restored rows execute and no stronger downstream blocker appears;
- cost-refused/source-gap executions must remain `0 / 0`;
- full-risk/reduced-risk provenance must remain visible in order/trade/missed ledgers.

## Pass / Fail Criteria

Helped:
- the 17:45 V181 winner is restored to order/trade, or the ledger exposes the next exact blocker after lifecycle/risk parity;
- no candidate/order/fill opportunity collapse is used to look positive;
- added/removed trades are attributed by exact candidate instance key;
- broker/live/final remain false.

Failed:
- the same row remains blocked by stale close/reverse/router-refusal floor or stale signed-risk projection;
- REFUSED/source-gap rows execute;
- replay improves only by suppressing opportunity;
- another downstream leak appears, in which case keep the truth and patch that next root cause.

## Planned Targeted Replay

```bash
python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-06-04 \
  --end 2026-06-05 \
  --profiles repaired_package_conversion_v3 \
  --symbols XAUUSD \
  --max-candidates-per-symbol-window 0 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V184_B7_CLOSE_REVERSE_ROUTER_REFUSAL_RISK_PARITY_20260604_20260605_XAUUSD_TARGETED
```
