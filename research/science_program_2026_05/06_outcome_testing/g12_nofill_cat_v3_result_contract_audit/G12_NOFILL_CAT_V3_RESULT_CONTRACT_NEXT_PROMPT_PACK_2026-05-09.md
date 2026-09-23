# G12 NOFILL CAT V3 Result Contract Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`.

Run only after `G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_V1` accepts `NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_RESULT_CONTRACT_V1`.

Recommended next lane: `NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET`.

Objective: build a quarantined categorical count packet from exactly the 225 accepted V3 input-only categorical rows in `NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl`. The lane may count categorical input labels and duplicate/concentration diagnostics only. It must not score outcomes, R, win rate, expectancy, DSR/PBO performance, validation, promotion, broker actual-R, account history, live order/deal/position, hidden labels, paid/API/Databento, registry, or live trading behavior.

Mandatory gates:
- Re-run GTOS preflight and read this G12 audit plus the frozen V3 result contract.
- Recompute upstream source hashes and stop on any strict mismatch. Line-ending-only prompt drift is acceptable only when the normalized LF hash matches.
- Assert `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject` before any count table.
- Consume only rows with `v3_terminal_family=accepted`, `source_safe_input_only=true`, `label_class=input_only_categorical`, and all safe flags false.
- Exclude source-control rows `0049`, `0050`, `0051`, `0241`; source-impossible rows `0130`, `0143`, `0165`, `0178`; and all 65 rejects before sample size, label counts, effective-N, or concentration diagnostics.
- Report row-level counts as descriptive/source-inventory counts only, primary duplicate-collapsed counts by `nofill_duplicate_key`, and secondary concentration by `duplicate_group_id`.
- If any accepted duplicate key has conflicting categorical labels, source geometry, or source ordering, block that key and route to source-control review.
- If a future lane wants to use source-control/source-impossible rows, split into a separate source-control/rebuild/G12 gate first.
- Emit zero R/win/expectancy fields or tables, and emit zero broker/account/live/order/hidden labels.
- Run a separate post-count G12 audit before any G0 synthesis or later validation/promotion dossier.

Freeze rule for ambiguity: accepted and safe rows count; source-control/source-impossible/reject rows exclude; unsafe or conflicting accepted rows block and route back; exact missing USDJPY sequence source requires access to broker-native quote-event sequence with sequence ID or sub-row/sub-millisecond timestamp and no account/order/history labels.
