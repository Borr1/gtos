# VPS Runtime Absorption Checkpoint

Date: 2026-06-19
Mac base before absorption: `f5f4ef3804a2a3baa319c9610089bf7f0bc4f628`
VPS live branch inspected: `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`
VPS live branch head inspected: `5f321c6de3c99f5686f79a121f9245862e65bc47`
VPS runtime-learning checkpoint head inspected: `fc61a09faec63da676e0951dadecd5dff6079dc7`
Evidence class: production-code integration backport plus VPS runtime observation evidence.

## Why This Checkpoint Exists

The VPS session found runtime intelligence that was not present in the Mac Wave E packet-only package.
The Mac source package now absorbs the deployable code/config/test/route-evidence parts of that VPS work while
leaving VPS runtime-state authority, halt-flag deletion, and broad context rewrites out of the mechanical backport.

This checkpoint does not execute broker/account/order/deal/position mutation and does not reload the VPS. It records
the Mac-side source package absorption and verification.

## VPS Intelligence Absorbed

- Runtime-learning packet parity was functionally absorbed from the scoped runtime-learning branch into the live
  conditioned-expansion VPS branch.
- Generation-level profile-missing skips now survive into `summary["skipped"]`, launcher logs, and runtime-learning
  `unit_skipped` packets.
- Runtime-learning packets now reject unknown event types, recompute source and packet hashes, separate skip/admission
  /management semantics, include redacted ticket hashes and management timestamps, and preserve joinability status.
- Live monitoring found a real management bug: one broker ticket could be adopted twice across canonical aliases such
  as `JP225` and `JP225_cash`. `UltimateBookOwner.manage_open_positions()` now keeps a pass-wide `claimed_tickets`
  set to prevent duplicate adoption.
- `PlacementLedger` now exposes `row_for_ticket()` so legacy active records can be normalized from source-bound
  durable placement rows.
- Trade-record loading now normalizes missing decision bar/day, cluster, candidate id, broker symbol, placement time,
  and ticket hash when available from the ledger, without fabricating unavailable decision context.
- Close paths now persist `trade_lifecycle_status=closed`, `close_action`, and `closed_at_utc` for managed closes.
- Runtime management packets now carry `trade_record_joinability_status`, distinguishing fully joinable crypto rows
  from older index rows that are only ticket/policy joinable.
- Active monitoring on 2026-06-19 found stale local XAU records that could remain lifecycle-open after broker closure
  if no live `ExecutionEngine.active_trade` observed the transition. `_reconcile_absent_trade_records()` now marks
  such records closed with `broker_closed_absent_on_reconcile` only when a non-empty broker-open snapshot confirms the
  MT5 position snapshot is real. Empty snapshots remain conservative and do not mass-close local records.
- Broker net-cost admission now includes adverse side-aware swap converted to R for MT5 points mode and annual-interest
  modes, with fail-closed behavior when required conversion is unavailable.
- Broker-profile verification now has an `ultimate-active` surface for the current 46-symbol ultimate-book universe.
- FTMO direct profile parity supports `46/46` active symbols. redacted_account supports `36/46`; ten unavailable symbols are
  explicitly allowed as real broker availability gaps, not naming bugs.

## Active Source Package After Absorption

- `ultimate_book_enabled=true`
- `ultimate_book_apply_to_execution=true`
- `ultimate_book_live_activation_allowed=true`
- `selector_v4_apply_to_execution=false`
- `ultimate_book_include_candidate_book=true`
- `ultimate_book_include_market_expansion_book=true`
- `ultimate_book_market_expansion_policy=positive_weighted12_after_swap`
- `ultimate_book_profile=clean3_w7_ceiling_nom2p00`
- `ultimate_book_runtime_learning_packet_enabled=true`
- `ultimate_book_runtime_learning_packet_log_enabled=true`
- `ultimate_book_runtime_learning_packet_log_path=shadow_logs/ultimate_book_runtime_learning_packets.jsonl`
- `ultimate_book_kelly_lite=true`
- `ultimate_book_kelly_running_count=true`
- `ultimate_book_stress_derisk=true`
- `ultimate_book_derisk_mode=smooth`
- `ultimate_book_metals_confluence_gate=true`
- `ultimate_book_drop_w7_symbols=true`
- `selected_cell_swap_cost_model_required=true`
- `selected_cell_swap_cost_horizon_days_cap=1.0`

Resolved active surface from the Mac source package:

- active specs: `32`
- unique on-surface symbols: `46`
- market-expansion policy sleeves: `12`
- policy: `positive_weighted12_after_swap`

## Current Replay Numbers

Evidence class: `source_bound_replay_mc_or_proxy_r_not_broker_real_pnl`.

Active A8 baseline:

- monthly: `2.646%` / `$2,646 per $100k`
- daily meanR: `0.110950`
- daily win rate: `51.1614%`
- daily Sharpe: `0.147757`
- MC pass: `0.99055`
- max-DD fail: `0.00945`
- worst day: `-2.66%`
- maxDD: `8.695125R`

Candidate book:

- monthly: `4.969%` / `$4,969 per $100k`
- daily meanR: `0.341331`
- daily win rate: `56.5217%`
- daily Sharpe: `0.277408`
- MC pass: `0.9999`
- max-DD fail: `0.0001`
- worst day: `-2.16%`
- maxDD: `8.766924R`

Current active intended package, positive12 market expansion:

- monthly: `5.090%` / `$5,090 per $100k`
- daily meanR: `0.362467`
- daily win rate: `56.9982%`
- daily Sharpe: `0.284190`
- MC pass: `0.9999`
- max-DD fail: `0.0001`
- worst day: `-2.083%`
- maxDD: `8.842614R`
- rows: `1,679`
- train: meanR `0.276891`, WR `56.1189%`, Sharpe `0.266897`, maxDD `4.952489R`, n `572`
- OOS: meanR `0.279006`, WR `55.3103%`, Sharpe `0.247022`, maxDD `8.842614R`, n `725`
- sealed: meanR `0.649008`, WR `61.5183%`, Sharpe `0.374025`, maxDD `6.653257R`, n `382`

Defensive robust6 fallback:

- monthly: `5.059%` / `$5,059 per $100k`
- daily meanR: `0.354867`
- daily win rate: `56.9387%`
- daily Sharpe: `0.282463`
- MC pass: `0.99995`
- max-DD fail: `0.00005`
- worst day: `-2.115%`
- maxDD: `8.159064R`

## Mac Verification

Passed after absorption:

- `python3 -m py_compile` for changed ultimate-book, cost, verifier, and focused test files.
- `pytest tests/ultimate_book/test_runtime_learning_packet.py tests/ultimate_book/test_book_owner.py tests/ultimate_book/test_placement_ledger.py tests/test_broker_net_cost_engine.py tests/ultimate_book/test_launcher.py tests/test_verify_broker_profile.py tests/ultimate_book/test_active_broker_profile_parity.py -q` -> `81 passed`.
- `python3 research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/verify_market_expansion_conditioned_policy_runtime_alias.py` -> `ok=true`.
- `python3 research/operations/final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18/verify_wave_e_runtime_learning_packet_parity.py` -> `ok=true`.
- `python3 research/operations/vps_runtime_ultimate_monitoring_repair_2026_06_18/verify_vps_runtime_ultimate_monitoring_repair.py` -> `ok=true`.
- `pytest tests/ultimate_book/test_market_expansion_runtime_generator.py -q` -> `10 passed`.
- `rg --files tests/ultimate_book | rg 'market_expansion' | xargs pytest -q` -> `53 passed`.
- activation-adjacent smoke group -> `44 passed`.
- active-monitoring absent-record repair route verifier -> `ok=true`.
- route artifact audits for Wave E, conditioned market expansion, VPS runtime monitoring repair, and VPS active
  monitoring repair -> `ok=true`.
- FTMO `ultimate-active` broker profile verifier -> `ok=true`, `46` active symbols.
- redacted_account `ultimate-active` broker profile verifier -> `ok=true`, `46` active symbols with `10` allowed broker-availability gaps.
- scoped `git diff --check` -> passed.

The first market-expansion slice command failed only because zsh passed a newline-separated file list as one argument.
It was rerun through `xargs` and passed.

## Remaining Work Toward The Ultimate System

Not closed by this checkpoint:

- Broker-real expectancy is still not proven by future PnL. Current performance numbers are replay/MC/proxy-R.
- VPS live packet rows exist and validated after reload, but they are early operational evidence, not enough outcome
  evidence to recalibrate expectancy.
- Active monitoring is now stronger because stale closed-ticket records are reconciled, but legacy index records that
  predate the current durable placement ledger correctly remain only `ticket_policy_joinable`.
- redacted_account is reduced-breadth at `36/46` active symbols unless the ten unavailable symbols are later proven available.
- Orderflow/depth is intentionally out of scope for the current package per owner instruction.
- More MT5 LTF/volume data can still expand replay stress, regime coverage, and candidate failure anatomy.
- The runtime-learning packets should be consumed into the next learning loop: realized management quality, skipped
  symbol/profile gaps, cost/swap pressure, duplicate alias risk, time-stop behavior, and broker-specific divergence.
- The final production-return dossier still needs to combine this package with live packet monitoring rules, kill/reduce
  thresholds, rollback commands, and a clear broker-real evaluation schedule.

## Current Confidence

- Code/config parity after absorption: high.
- Replay package math: moderate-high, because it is verifier-clean and split-backed.
- Broker-real future expectancy: medium, because current evidence is still replay/MC plus early live operational packet
  evidence.
- Runtime observability and joinability: materially stronger after this VPS absorption.
- Whole deployable package: stronger than the prior Mac checkpoint, but not the final "ultimate system" until broker-real
  forward packets and outcomes close the remaining execution/behavior loop.
