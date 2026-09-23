# Broad Live-As-If Candidate-Parity Repair Comparison

Generated: 2026-06-29T16:39:28Z

Broker/live/final authority remains closed. This compares replay-only artifacts.

## Candidate Generation

- Baseline prefix: `BROAD_LIVE_AS_IF_REPLAY_SAME_GEOMETRY_EXECUTION_GUARD_20260513_20260517_TARGETED5_SMOKE`.
- Repair prefix: `BROAD_LIVE_AS_IF_REPLAY_SAME_GEOMETRY_CORE_KEY_REPAIR_20260513_20260517_TARGETED5_SMOKE`.
- Baseline generation authority: uncapped_full_authority.
- Repair generation authority: uncapped_full_authority.
- Baseline emitted candidates from decision ledger: 4581.
- Repair raw generated candidates: 4581.
- Repair emitted candidates: 4581.
- Repair truncated candidates: 0.
- Repair max raw generated per symbol-window: 17.

## Replay Outcomes

- raw_package_live_as_if:development: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None
- raw_package_live_as_if:holdout: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None
- guarded_causal_admission_repair_v2:development: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None
- guarded_causal_admission_repair_v2:holdout: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None

## Interpretation

- A positive delta here proves only that the executable replay wiring improved for the bounded run.
- A negative or mixed delta means the source-bound reservoir is still not converting after candidate generation, and the next limiting leak is selector/scheduler/risk/exit behavior.
- The 1.249M R source-bound reservoir is not a filled-trade result; parity requires these axes to survive generation, selector, scheduler, risk, order, fillability, lifecycle, and exit conversion.
