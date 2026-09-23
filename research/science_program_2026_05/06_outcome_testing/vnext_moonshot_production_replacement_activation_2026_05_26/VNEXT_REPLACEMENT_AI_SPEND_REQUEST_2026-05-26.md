# vNext Replacement AI Calibration Spend Request

Route id: `vnext_moonshot_production_replacement_activation_2026_05_26`
Generated: `2026-05-26T13:45:59Z`

Stage09 prepared the AI calibration package and made **0 paid API/vendor calls** because `route_state_budget_cap_usd` is null.

## Requested Cap

- Requested hard cap: `$5.00`
- Target tier: `smoke_plumbing`
- Target calls: `32`
- Model: `claude-sonnet-4-6`
- Effort: `max`
- Estimated input tokens: `123091`
- Estimated output tokens: `28800`
- Offline estimated spend at the prior planning rate: `$0.8013`
- Price note: refresh provider pricing before any paid run.

## What The Spend Tests

- Cache-key plumbing and prompt hash binding.
- Strict JSON schema compliance.
- Malformed/refusal repair path.
- False accept/reject smoke across selected vNext replacement strata.
- Whether AI should remain validator-only, mixed resolver, safety veto, no-AI-needed, or defer-to-capture for each packet.

## Run Condition

Do not run calls unless the route state is updated with an explicit non-null `route_state_budget_cap_usd` and the cap is at least the requested hard cap. The prompt pack is `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/VNEXT_REPLACEMENT_AI_PROMPT_PACK_2026-05-26.jsonl`.
