# V121AB Hostile 5-Day Generalization Pre-Replay Brief

Generated: `2026-07-05T17:07:10Z`

Broker/live/final remain closed. Local replay/package authority remains full.

V121AA one-day proof fixed public final-risk mismatch: V121Z `40` -> V121AA `0`; trade/R/cash unchanged from V121Z. That proves ledger authority, not full behavior.

Run current code unchanged over `2026-05-13..2026-05-17` with prefix `BROAD_LIVE_AS_IF_REPLAY_V121AB_HOSTILE_5D_RUNTIME_FINAL_RISK_AUTHORITY_GENERALIZATION_20260513_20260517` before more policy tuning. Compare against V89D/V90/V92 five-day baselines and report same-window rows, transfer, missed R, expired/deferred, full/reduced risk, public-risk mismatch, stop/exit buckets, and added/removed behavior.

Success: zero public risk mismatch, zero executed REFUSED/source-gap, and behavior exposes whether one-day NY/XAGUSD/AUDUSD stop-loss drag is systemic across hostile bucket.

Failure: public risk mismatch returns, cost/source-gap executes, or verifier/truth breaks.
