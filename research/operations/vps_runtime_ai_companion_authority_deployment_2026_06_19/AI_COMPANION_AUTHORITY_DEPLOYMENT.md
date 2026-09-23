# AI Companion Authority Deployment

Date: 2026-06-19 UTC

Evidence class: production-code integration plus live runtime deployment evidence.

Runtime effect boundary: `bounded_protective_runtime_controls_only_no_order_placement_no_risk_increase_no_hard_gate_override_no_broker_account_order_deal_position_or_credential_mutation`.

## Deployed Design

The AI companion layer is a supervised control-state system, not a free-form order executor.

- `scripts/run_ai_companion_supervisor.py` reads launcher, runtime-learning packet, and heartbeat evidence.
- `src/components/ai_companion/supervisor.py` writes digest, proposal, heartbeat, decision, and control-state artifacts.
- `src/components/ai_companion/control_state.py` validates the only live-consumable control schema.
- `src/components/ultimate_book/book_owner.py` consumes validated controls before new-entry routing.
- `src/components/ultimate_book/launcher.py` carries companion state into cycle logs.
- `scripts/run_book_supervisor.ps1` restarts the AI companion supervisor alongside the book and monitor daemons.

## Runtime Authority

Allowed live effects:

- `pause_new_entries`: new entries become observe-only while open-position management continues.
- `symbol_sleeve_cooldown`: exact matching symbol/sleeve candidates are skipped until expiry.
- `risk_multiplier`: risk can only be reduced from the book's computed value; values above `1.0` are rejected.

Forbidden effects:

- no order placement;
- no risk increase;
- no hard-gate override;
- no broker/account/order/deal/position mutation;
- no credential mutation or disclosure.

## Active First State

The first supervisor one-shot on the live VPS wrote a protective empty control state because no packet, launcher, or heartbeat integrity issue was present. Current advisory queues identify broker-profile hygiene candidates already fail-closed by runtime.

