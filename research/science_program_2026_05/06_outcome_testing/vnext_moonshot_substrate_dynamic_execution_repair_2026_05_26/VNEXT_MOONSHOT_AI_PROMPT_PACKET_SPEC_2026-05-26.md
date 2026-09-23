# vNext Moonshot AI Prompt Packet Spec

## Purpose

Budgeted validation packets test the production AI decision layer after corrected no-API replay. They are not activation approval and they do not expose outcome labels to the AI packet.

## Required Model Binding

- Model: `claude-sonnet-4-6`
- Effort: `max`
- Prompt hash: `ed9a6ff76a5c5788b5e75908b44b686e21391249fc4827695ab85779c58088dd`
- Config hash: `476fea0492baedb3b41644b1407edfd5e589bdaab3f5f8491af4e5a799e33df5`
- redacted_account profile hash: `d43dd9ae5e428a9df85631d4612d0737a18484a2268bf7db8a31b0946566371b`

## Allowed Packet Fields

Only as-of candidate identity, symbol/session/side/framework, source hashes, source-completeness status, market-awareness fields, and prop-rule context are allowed.

## Forbidden Packet Fields

The packet must exclude final R, MFE/MAE, policy outcome, terminal outcome, lifecycle result, post-trade equity, and any future touch/order result. These are referenced only by offline scoring hashes.

## Cache Key

`sha256(model_id, model_effort, prompt_hash, config_hash, profile_hash, packet_spec_hash_seed, packet_hash)`

## Malformed Handling

Malformed, refusal, schema-missing, or hallucinated-field responses stop the current tier if the tier malformed rate exceeds 5% or if three consecutive responses fail. Monitoring agents may repair packet transport/schema only; they may not rewrite the trading decision.

## Expected Output Schema

The AI response must return `decision`, `confidence`, `required_context_fields_used`, `disallowed_fields_used=false`, `reason_codes`, `risk_notes`, and `schema_version`.
