# XAGUSD Account-History Join Repair Attempt

Generated: `2026-05-16T14:47:59+00:00`
Fill: `XAGUSD_2026-05-14_ny_1315`
Repair status: `NOT_REPAIRABLE_FROM_CURRENT_LOCAL_ACCOUNT_HISTORY_EXPORTS`

The J46/J49 shadow outcome exists for the XAGUSD 2026-05-14 NY fill, and LTO-016 correctly marks it action-required because it lacks `ACCOUNT_HISTORY_REALIZED` broker evidence.

Current local `data/account_history/mt5_deals_*.jsonl` exports were searched and contain no XAGUSD 2026-05-14 deal rows. The current disk state therefore cannot repair the account-history join without a newer read-only MT5 account-history export.

No actual-R, validation-safe, promotion, live-effect, or broker-operation claim is opened by this artifact.
