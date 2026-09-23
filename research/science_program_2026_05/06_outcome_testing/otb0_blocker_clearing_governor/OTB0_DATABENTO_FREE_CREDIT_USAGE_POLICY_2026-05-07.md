# OTB0 Databento Free-Credit Usage Policy - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**OTB0 Databento spend:** `$0`

## Policy

| Topic | Scope | Rule |
| --- | --- | --- |
| Scope | OTB0 | No Databento calls, no credit spend, no API spend, no result generation. |
| Future trigger | OTB4 only | Allowed only if a G4/orderflow packet cannot be cleared from local/Sierra/cached evidence. |
| Credit rule | Hard gate | Existing free credits only. Abort if free-credit balance is unknown, insufficient, expired, or requires subscription/top-up/payment method. |
| Pre-call manifest | Required before any future call | dataset, schema, symbols, start/end UTC, rows/window estimate, expected cost, free-credit balance, abort threshold, source IDs, packet IDs. |
| Cost-credit check | Required before any future call | A separate manifest/cost-credit artifact must prove estimated cost <= available free credits and expected paid spend = $0. |
| Allowed web/docs | Source-contract evidence | Official Databento docs may be fetched with curl/webfetch only when cached raw evidence and source index are written. |
| Forbidden | Always | Overage, subscription, paid trial, top-up, broad pull, live decision feature activation, credential disclosure, result/quarantine output from OTB0. |

## Future OTB4 Pre-Call Manifest Fields

| Required field |
| --- |
| manifest_id |
| packet_ids |
| source_contract_ids |
| dataset |
| schema |
| symbols |
| start_utc |
| end_utc |
| estimated_rows_or_bytes |
| estimated_cost_usd |
| available_free_credits_usd |
| paid_spend_expected_usd=0 |
| abort_if_any_paid_spend=true |
| credential_handling=not_recorded |
| raw_source_index_path |

## Current OTB0 Decision

OTB0 does not need a Databento call to produce the blocker-clearing plan. Databento remains a conditional future feasibility lane only.
