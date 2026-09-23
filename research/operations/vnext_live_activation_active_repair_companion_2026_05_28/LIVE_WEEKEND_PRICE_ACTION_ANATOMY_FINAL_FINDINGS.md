# Weekend vNext Price-Action Anatomy Final Findings

Generated: 2026-05-31T07:41:01.118319+00:00
HEAD: 91e28b198a878d45e4987bbe42561e67b5979fde

## Denominator

- Candidate rows studied: 604
- Placed broker autopsies: 8
- Refusal rows classified: 596
- Policy comparison rows: 4832

## Core Findings

- Outcome counts: `{"DEFERRED_GTOS_VNEXT_PROP_RESET": 45, "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN": 8, "REJECTED_GATE1_SAFETY": 76, "REJECTED_GATE3_CIRCUIT_BREAKER": 78, "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC": 397}`
- Refusal correctness counts: `{"correct_current_vnext_operational_gate": 70, "correct_current_vnext_session_contract": 38, "gate_correct_but_historical_packet_incomplete": 8, "stale_or_unresolved_selected_cell_risk_bridge": 118, "stale_or_unresolved_selector_bridge": 241, "stale_under_repaired_vnext": 121}`
- BTCUSD: `{"outcomes": {"REJECTED_GATE1_SAFETY": 1, "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC": 29}, "path_statuses": {"entry_filled_no_sl_or_1r_before_last_available_price": 2, "entry_filled_sl_before_1r_trigger": 16, "partial_1r_then_3r_final": 2, "partial_1r_then_be": 9, "partial_1r_then_open_at_last_available_price": 1}, "refusal_statuses": {"stale_or_unresolved_selected_cell_risk_bridge": 14, "stale_or_unresolved_selector_bridge": 15, "stale_under_repaired_vnext": 1}, "rows": 30}`
- ETHUSD: `{"outcomes": {"REJECTED_GATE1_SAFETY": 6, "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC": 30}, "path_statuses": {"entry_filled_no_sl_or_1r_before_last_available_price": 1, "entry_filled_sl_before_1r_trigger": 21, "partial_1r_then_3r_final": 2, "partial_1r_then_be": 11, "partial_1r_then_open_at_last_available_price": 1}, "refusal_statuses": {"stale_or_unresolved_selected_cell_risk_bridge": 10, "stale_or_unresolved_selector_bridge": 20, "stale_under_repaired_vnext": 6}, "rows": 36}`
- Broker truth status counts: `{"mt5_readonly_not_available": 8}`
- MT5 realized profit sum where available: `0.0`; commission `0.0`; swap `0.0`

## Production Boundary

This pass builds source-bound intelligence and route evidence. It does not authorize a live logic change by itself, and it performs no broker actions.
