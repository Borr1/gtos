# RECEIPT-F5-GBPUSD-GHOST-CONSUME-20260822

Next to RECEIPT-F5-GBPUSD-GHOST-HEAL-20260822.md.

When: 2026-08-22 10:42 Asia/Bangkok (03:42 UTC)

## Defect

Ticket 177902888 was an honest broker SL (history deal 166847503: profit -78.4, commission -3.5, swap 0, fee 0). Official `on_close` is in-process only. The consume path `broker_closed_absent_on_reconcile` already existed and had closed other 2026-08-21 leftovers, but this ticket never entered it.

Two gates:

1. `_manageable_pairs()` called `active_specs(None)`. Displacement is fail-closed there (`dsp_*` only join when `--tags` is passed). The GBPUSD dsp engine was created at place time and kept `active_trade=177902888`, but the manage loop never visited `(GBPUSD, dsp_small_bar_sit_on_20high_rejects)`, so `_reconcile_absent_active_engine` never ran. Trade-record mtime stayed at open (2026-08-21 19:19 UTC). The still-open USDJPY dsp 177908572 had the same manage hole (left open; not flattened).

2. `_reconcile_absent_trade_records` skipped any ticket still in `active_tickets`. So leftover could not consume a dsp ghost the pair-loop never saw. F5 `reconcile_broker_positions` then saw the ledger unit absent from a real non-empty snapshot and fail-closed (`ledger_open_unit_absent_from_broker` → `reconciliation_complete=False` → equity None).

## Fix (live + Mac frozen-price-intent + audit-fable)

- Leftover: skip `active_tickets` only on an all-empty snapshot (keeps the 2-tick empty debounce). On a non-empty snapshot, consume broker-absent open records even if an engine still holds them; `_clear_engine_ticket`.
- `_f5_reconcile_broker_positions`: on a confirmed non-empty snapshot, consume ledger units missing from broker via the same `broker_closed_absent_on_reconcile` → daily_pnl → `_f5_on_close` seam, then reconcile.
- `_manageable_pairs` uses `owner._generation_tags`; launcher stamps those from `--tags` so dsp is managed after restart.

No `place()`. No flatten of the five remaining tickets. No remint. Ledger file not hand-edited. Restart only via scheduled task redacted_host-VERIFICATION-20260821 Stop → Enable+Start, left enabled.

## Live consume

Happened on the next cycle after restart (pid 22036).

- close_action: broker_closed_absent_on_reconcile
- deal: 166847503
- exit deal: profit -78.4 commission -3.5 swap 0 fee 0 (as given)
- official folded net: -85.4 = position aggregate (entry deal 166840948 commission -3.5 + exit -78.4/-3.5). Source `position_aggregate_includes_entry_and_exit_deals`. Not invented.
- daily_pnl: RECORDED_BROKER_NET
- trades_recorded 3 → 4; real_pnl_usd_cumulative -177.83 → -263.23

## open_units

Before: 177634847 BTCUSD, 177634850 ETHUSD, 177634852 XTZUSD, 177634855 AVAUSD, 177902888 GBPUSD ghost, 177908572 USDJPY

After: 177634847, 177634850, 177634852, 177634855, 177908572 (all still open). Ghost gone. No new placed_decisions after 2026-08-21T20:15Z USDJPY. Heartbeat healthy. equity_unavailable no longer blocked on this ghost.

## Files

- host-local\redacted_host\repo\src\components\ultimate_book\book_owner.py
- host-local\redacted_host\repo\src\components\ultimate_book\launcher.py
- Mac frozen-price-intent-20260816 and audit-fable-20260816: same two files + test_leftover_consumes_dsp_active_ticket_absent_from_nonempty_snapshot
