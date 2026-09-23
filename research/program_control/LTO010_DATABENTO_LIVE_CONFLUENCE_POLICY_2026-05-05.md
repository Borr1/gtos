# LTO010 Databento Live Confluence Policy - 2026-05-05

**Status:** `OK_OWNER_APPROVED_VALUE_MAX_POLICY_READY_ENV_GATED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Registered Policy

- Policy id: `lto010_databento_live_confluence_policy_v1`
- Registered symbols/schemas: `{'NAS100': ('trades', 'mbp-10', 'mbo'), 'US30': ('trades', 'mbp-10', 'mbo'), 'XAUUSD': ('trades', 'mbp-10', 'mbo'), 'XAGUSD': ('trades', 'mbp-10', 'mbo'), 'USDJPY': ('trades', 'mbp-10'), 'GBPUSD': ('trades', 'mbp-10')}`
- Max cost per trigger: `$2.50`
- Daily spend cap: `$25.00`
- Cooldown seconds: `60`
- Max timeout seconds: `600.0`
- Max records per trigger: `50000`
- Owner approval status: `OWNER_APPROVED_BY_CEO_2026-05-05_VALUE_MAX_FORWARD_COLLECTION`

## Current Rows

- Trigger-decision rows: `72`
- Live confluence rows: `3`
- Budget ledger rows: `4`
- Paid confluence rows: `1`
- Audit AI/canary/order/Databento calls: `0` / `0` / `0` / `0`

## Disabled-Environment Check

- Decision: `DO_NOT_FETCH`
- Trigger status: `DISABLED_BY_ENV`
- Block reasons: `['DISABLED_BY_ENV', 'DATABENTO_API_KEY_MISSING']`

## Guardrail

This audit only inspects local JSONL and evaluates policy in-process. It does not connect to Databento, call MT5, call AI, run canaries, or place orders. The owner approval is now recorded for value-max Databento usage; live collection is env/API/cost-cap gated, not approval-blocked.
