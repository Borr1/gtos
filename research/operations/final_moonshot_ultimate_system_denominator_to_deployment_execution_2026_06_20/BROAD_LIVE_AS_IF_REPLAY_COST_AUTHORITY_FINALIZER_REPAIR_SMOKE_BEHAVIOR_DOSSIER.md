# Broad Live-As-If Candidate-Parity Repair Comparison

Generated: 2026-06-21T10:54:07Z

Broker/live/final authority remains closed. This compares replay-only artifacts.

## Candidate Generation

- Baseline prefix: `BROAD_LIVE_AS_IF_REPLAY_MEMBER_AXIS_COST_GAP_SMOKE`.
- Repair prefix: `BROAD_LIVE_AS_IF_REPLAY_COST_AUTHORITY_FINALIZER_REPAIR_SMOKE`.
- Baseline generation authority: uncapped_full_authority.
- Repair generation authority: uncapped_full_authority.
- Baseline emitted candidates from decision ledger: 26136.
- Repair raw generated candidates: 26448.
- Repair emitted candidates: 26448.
- Repair truncated candidates: 0.
- Repair max raw generated per symbol-window: 19.

## Replay Outcomes

- raw_package_live_as_if:development: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None
- raw_package_live_as_if:holdout: baseline trades=5 net_r=-4.36555863 cash=-1641.38364683 w/l/f=0/5/0; repair trades=5 net_r=-4.36555863 cash=-1641.38364683 w/l/f=0/5/0; delta_net_r=0.0
- guarded_causal_admission_repair_v2:development: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None
- guarded_causal_admission_repair_v2:holdout: baseline trades=5 net_r=-4.36555863 cash=-1641.38364683 w/l/f=0/5/0; repair trades=5 net_r=-4.36555863 cash=-1641.38364683 w/l/f=0/5/0; delta_net_r=0.0

## Interpretation

- A positive delta here proves only that the executable replay wiring improved for the bounded run.
- A negative or mixed delta means the source-bound reservoir is still not converting after candidate generation, and the next limiting leak is selector/scheduler/risk/exit behavior.
- The 1.249M R source-bound reservoir is not a filled-trade result; parity requires these axes to survive generation, selector, scheduler, risk, order, fillability, lifecycle, and exit conversion.
