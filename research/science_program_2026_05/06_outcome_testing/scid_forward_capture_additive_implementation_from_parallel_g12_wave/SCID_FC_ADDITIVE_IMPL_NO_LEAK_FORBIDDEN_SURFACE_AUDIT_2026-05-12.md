# SCID FC Additive Impl No-Leak Forbidden Surface Audit - 2026-05-12

- SCID validator rejects forbidden broker/account/order/deal/position/result/cost surfaces.
- Lifecycle bridge deliberately omits raw ticket/order/result fields and leaves `redacted_order_bridge_hash_optional` null by default.
- Safe flags stay false and `NO_PROMOTION_VERDICT` is required on every valid row.
