# Broad Live-As-If Candidate-Parity Repair Comparison

Generated: 2026-06-21T06:43:23Z

Broker/live/final authority remains closed. This compares replay-only artifacts.

## Candidate Generation

- Baseline prefix: `BROAD_LIVE_AS_IF_REPLAY_POLICY_WIRED_COST_AWARE_HOLDOUT_SMOKE`.
- Repair prefix: `BROAD_LIVE_AS_IF_REPLAY_BROKER_COST_AUTHORITY_SMOKE_V2`.
- Baseline generation authority: uncapped_full_authority.
- Repair generation authority: uncapped_full_authority.
- Baseline emitted candidates from decision ledger: 8864.
- Repair raw generated candidates: 26592.
- Repair emitted candidates: 26592.
- Repair truncated candidates: 0.
- Repair max raw generated per symbol-window: 19.

## Replay Outcomes

- raw_package_live_as_if:development: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None
- raw_package_live_as_if:holdout: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=9 net_r=-1.02863089 cash=-875.75479616 w/l/f=3/6/0; delta_net_r=-1.02863089
- guarded_causal_admission_repair_v2:development: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None
- guarded_causal_admission_repair_v2:holdout: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=12 net_r=-2.13673745 cash=-344.22398719 w/l/f=4/8/0; delta_net_r=-2.13673745

## Interpretation

- A positive delta here proves only that the executable replay wiring improved for the bounded run.
- A negative or mixed delta means the source-bound reservoir is still not converting after candidate generation, and the next limiting leak is selector/scheduler/risk/exit behavior.
- The 1.249M R source-bound reservoir is not a filled-trade result; parity requires these axes to survive generation, selector, scheduler, risk, order, fillability, lifecycle, and exit conversion.
