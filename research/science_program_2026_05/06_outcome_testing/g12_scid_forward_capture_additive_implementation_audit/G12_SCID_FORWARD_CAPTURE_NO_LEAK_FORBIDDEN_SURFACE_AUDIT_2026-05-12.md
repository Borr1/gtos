# No-Leak And Forbidden-Surface Audit

Forbidden broker/account/order/deal/position IDs and result/performance fields are blocked in `src/research_infra/forward_capture.py:333-396` and rejected by the validator at `src/research_infra/forward_capture.py:2640-2741`.

I recomputed lifecycle redaction with secret `pending_ticket`, `mt5_order_ticket`, `trade_state_ticket`, `actual_r`, `synthetic_path_r`, and `slippage_price` inputs. The SCID lifecycle row validated, no `SECRET_` value leaked, and none of the forbidden field names appeared in the SCID payload.

No route evidence showed broker reads, paid/vendor fetches, AI/API calls, credential/remote changes, raw market blob commits, order placement/modification/cancellation changes, or result scoring.
