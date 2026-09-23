# CNR Source Field Next G12 Audit Prompt Pack - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

## Prompt

/goal Run G12/G0 audit over CNR_SOURCE_FIELD_PACKET_BUILDER artifacts under `research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder` using `research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_MANIFEST_2026-05-07.json`, `research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl`, `research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST_2026-05-07.json`, `research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_DATA_EXTRACTION_LEDGER_2026-05-07.json`, `research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN_2026-05-07.json`, `research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json`, and `research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_COMPLETION_AUDIT_2026-05-07.json` as controlling inputs. Verify that packet rows are input-only, source-hashed, duplicate-safe, no-leak scanned, and either ready for a future result lane or blocked with exact source-field requirements. Do not score outcomes, do not open result/quarantine directories, do not use broker actual-R/account history/live order state, and do not touch prompts, risk, execution, permissions, safety gates, selectors, canaries, credentials, remotes, paid/API/Databento, MT5 order paths, or order behavior. Preserve `NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false`.

## Exact Audit Questions

1. Are all consumed source files present and SHA256-hashed?
2. Are all CNR timing families E0-E4 and target families T0-T3 represented for each source record, with field values or exact blockers?
3. Do rows contain any forbidden outcome/result fields?
4. Does duplicate denominator counting remain stable by packet/timing/target?
5. Are ready rows only input-ready for audit, not result-scored?
6. Are blocked rows actionable by source/parser/logger/approval requirement?
7. Did the builder avoid live trading surfaces and result/quarantine directories?
