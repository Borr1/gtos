# OTB0 Owner Approval Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**OTB0 spend:** `$0`

## Approved Or Blocked Scope

| Approval | Scope | Status | OTB0 action | Guardrail |
| --- | --- | --- | --- | --- |
| APP-001 | public curl/webfetch for official source docs | APPROVED_FOR_SOURCE_CONTRACT_EVIDENCE_ONLY | No new fetch performed by OTB0. | Use cached raw/source-index outputs; official/vendor/regulator docs only; no snippet-only claims. |
| APP-002 | local calendar source-path cleanup | APPROVED | Assigned to OTB3. | Use `data/news_calendar.json` as schedule/stale-calendar context only; do not change live news-filter behavior. |
| APP-003 | regeneration of missing frozen packet inputs | APPROVED | Assigned to OTB1/OTB2. | Local OHLC/path logs only; no result/R columns; no quarantine/result outputs. |
| APP-004 | Databento usage | APPROVED_CONDITIONALLY_FOR_FUTURE_FREE_CREDITS_ONLY | No Databento call performed by OTB0. | Existing free credits only; pre-call manifest plus cost-credit check; abort on any overage, subscription, top-up, or paid spend risk. |
| APP-005 | G5 prompt-neutral rerun research | APPROVED_CONDITIONALLY_FOR_FUTURE_SONNET_ONLY_PILOT | Design only; no API call performed by OTB0. | Hard $20 cap, no Opus, cached calls, token/cost ledger, frozen prompt hashes, fixed rubric, small stratified sample, no 500-call run. |
| APP-006 | live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, credentials, remotes, order behavior | NOT_APPROVED_AND_OUT_OF_SCOPE | Untouched. | Any future request touching these surfaces requires explicit owner approval and is not part of OTB0. |

## Owner Questions For Future Lanes

| Question |
| --- |
| If OTB3 needs to edit master registry JSON rather than sidecar cleanup artifacts, should it patch master rows directly or emit proposed patch files for G12/G0 review? |
| If Databento free-credit balance cannot be proven without an authenticated API check, should OTB4 stop at a no-access feasibility blocker? |
| If the G5 Sonnet pilot cost estimate exceeds the $20 cap after tokenizing the frozen sample, should OTB5 reduce sample size or stop blocked for owner re-scope? |
