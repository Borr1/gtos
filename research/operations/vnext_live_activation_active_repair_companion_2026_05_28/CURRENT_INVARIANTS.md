# vNext Live Activation Active Repair Invariants

Updated: 2026-05-28T21:49:33+08:00

- vNext production rows must carry the selected execution policy, execution_policy_id, origin family, selector/proof reference, dynamic trigger/final/pullback parameters when applicable, and prop/risk action into operator-visible Telegram lifecycle alerts.
- Telegram alerts for vNext rows must not present the row as legacy fixed-1.5R or J46/J49 behavior.
- Lifecycle alert coverage now includes limit placement, fill, partial close, BE transition, momentum pullback close, dynamic final close, rejected order, expiry, and broker/deal reconciliation.
- Replacement monitoring must distinguish retired-static-baseline provenance from retired-policy execution. Production runtime rows must use `replaced_policy=retired_static_baseline_comparator` when paired with vNext selected policy/execution_policy_id and `fixed_target_role=baseline_comparator_only`; `live_current_j46_j49`, `J46`, `J49`, and fixed-1.5R labels are not allowed in newly written production runtime rows.
- Live 24-symbol process, MT5/tick/watchdog freshness, and post-reload vNext runtime rows are verified. No eligible live broker lifecycle event occurred during the verification window, so Telegram lifecycle parity remains synthetic-verified until the first live fill/close/reconciliation event appears.
