# vNext Moonshot Stage08 AI Role And Budget Design

Generated: `2026-05-26T04:54:09Z`

## Result

- Role decision rows: `7`
- Validation manifest rows: `480`
- Mandatory strata covered: `15` / `15`
- Paid API/vendor calls made: `0`

## Role Decision

- Keep production AI as a budgeted validator/gate pending cached delta validation.
- Use AI most heavily on high-EV, disagreement, source-sensitive, context-rich, no-fill, and prop-near-boundary strata.
- Treat monitoring/supervisor agents as operational repairers, not production decision replacements.
- Do not remove AI from trade selection until a separate cached AI-delta audit proves replacement safety.

## Budget Tiers

- `zero_call_design`: max_calls=0 max_spend_usd=0.0 supports manifest/cache/prompt review only.
- `smoke_plumbing`: max_calls=32 max_spend_usd=5.0 supports cache-key plumbing, prompt packet schema, malformed-response handling smoke.
- `decisive_low_budget`: max_calls=128 max_spend_usd=15.0 supports directional false-positive/false-negative read across mandatory strata.
- `strong_validation`: max_calls=320 max_spend_usd=35.0 supports role decision between production gate, validator, MIXED resolver, and monitoring-only for selected strata.
- `extended_validation`: max_calls=512 max_spend_usd=50.0 supports broad selected-strata AI role decision under monthly cap if owner approves spend.