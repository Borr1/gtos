# Broad Live-As-If Candidate-Parity Repair Comparison

Generated: 2026-06-28T01:49:31Z

Broker/live/final authority remains closed. This compares replay-only artifacts.

## Candidate Generation

- Baseline prefix: `BROAD_LIVE_AS_IF_REPLAY_CONFIDENCE_SOURCE_REQUIRED_ROOT_REPAIR_5D_SMOKE`.
- Repair prefix: `BROAD_LIVE_AS_IF_REPLAY_UPSTREAM_SIGNED_AUTHORITY_REPAIR_5D_SMOKE`.
- Baseline generation authority: uncapped_full_authority.
- Repair generation authority: uncapped_full_authority.
- Baseline emitted candidates from decision ledger: 0.
- Repair raw generated candidates: 78899.
- Repair emitted candidates: 78899.
- Repair truncated candidates: 0.
- Repair max raw generated per symbol-window: 18.

## Replay Outcomes

- raw_package_live_as_if:development: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None
- raw_package_live_as_if:holdout: baseline trades=6 net_r=0.23108671 cash=56.50616995 w/l/f=3/3/0; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=-0.23108671
- guarded_causal_admission_repair_v2:development: baseline trades=None net_r=None cash=None w/l/f=None/None/None; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=None
- guarded_causal_admission_repair_v2:holdout: baseline trades=13 net_r=-2.44992802 cash=-613.65461912 w/l/f=6/7/0; repair trades=None net_r=None cash=None w/l/f=None/None/None; delta_net_r=2.44992802

## Interpretation

- A positive delta here proves only that the executable replay wiring improved for the bounded run.
- A negative or mixed delta means the source-bound reservoir is still not converting after candidate generation, and the next limiting leak is selector/scheduler/risk/exit behavior.
- The 1.249M R source-bound reservoir is not a filled-trade result; parity requires these axes to survive generation, selector, scheduler, risk, order, fillability, lifecycle, and exit conversion.
