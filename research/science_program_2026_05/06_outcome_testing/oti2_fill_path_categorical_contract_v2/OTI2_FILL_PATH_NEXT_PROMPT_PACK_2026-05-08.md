# OTI2 Fill/Path Contract V2 Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Recommended Next Lane

Run `G12_OTI2_FILL_PATH_CATEGORICAL_CONTRACT_V2_AUDIT` against:

- `research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_FROZEN_CONTRACT_2026-05-08.json`
- `research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl`
- `research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_COMPLETION_AUDIT_2026-05-08.json`

## Audit Questions

1. Verify the universe count is 34 rows: original OTI2 1, OTI1 22, OTI3 entry-before-terminal 7, and OTI3 same-timestamp ambiguity 4.
2. Verify the accepted categorical labels are source-event-order labels only and do not compute R/performance.
3. Independently verify that the four OTI3 same-timestamp rows remain blocked because a single quote row/ts_msc satisfies multiple touch predicates.
4. Independently verify that the original OTI2 row remains blocked because M1 context is not side-aware quote proof and XAUUSD 2026-05-06 tick coverage starts after the required source window.
5. Verify source hashes, no-leak checks, duplicate/sample-floor posture, and no live-trading surface changes.

## Forbidden

Do not compute R, win rate, expectancy, broker actual-R, account-history outcomes, live order/deal/position labels, or promotion evidence. Do not touch live trading prompts, risk, execution, permissions, safety selectors, MT5 order/account/history, canaries, paid/API/Databento, credentials, remotes, registries, or order behavior.
