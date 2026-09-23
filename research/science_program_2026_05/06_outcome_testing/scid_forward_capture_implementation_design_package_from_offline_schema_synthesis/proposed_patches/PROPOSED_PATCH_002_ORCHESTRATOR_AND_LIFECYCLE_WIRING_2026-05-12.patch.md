# Proposed Patch 002 - Orchestrator And Lifecycle Wiring

PROPOSED ONLY - DO NOT APPLY IN THIS ROUTE
NO_PRODUCTION_EDIT_IN_THIS_ROUTE

Owner-approved future file scope:
- `src/components/orchestrator.py`
- `src/components/pending_limit_lifecycle_logger.py`

Purpose:
- Add additive calls from `_record_forward_capture_candidate_shadow` and `_record_forward_capture_evaluation_shadow` to the SCID source-capture adapter.
- Add status-only lifecycle bridge from `record_pending_limit_lifecycle` to the SCID adapter.

Hard boundaries:
- No trading decision reads the new SCID writer return value.
- No prompt, model, risk, safety, selector, canary, execution, order placement, or config behavior changes.
- Existing shadow loggers remain the source of truth; SCID capture is additive.
- If SCID writer raises, catch/log and preserve existing pipeline behavior.

Lifecycle redaction:
- `pending_ticket`, `mt5_order_ticket`, `trade_state_ticket`, account ids, deal ids, order ids, and position ids are forbidden in SCID rows.
- `actual_r`, `synthetic_path_r`, `slippage_price`, `broker_fill_state`, win/loss, PnL, expectancy, and terminal result labels are forbidden.
- Optional `redacted_order_bridge_hash_optional` is disabled by default; it requires explicit owner approval and G12 review before use.

Restart policy for future approved implementation:
- Merge only after G12 accepts this design and focused tests pass.
- Restart all affected orchestrators after the additive patch is merged.
- First monitoring pass checks schema version, group coverage, redaction, fail-closed unavailable statuses, and no decision-path diffs.
