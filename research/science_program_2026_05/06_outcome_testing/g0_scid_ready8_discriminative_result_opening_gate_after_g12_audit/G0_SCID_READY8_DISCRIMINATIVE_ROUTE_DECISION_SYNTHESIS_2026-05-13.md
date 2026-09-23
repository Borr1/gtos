# G0 SCID READY8 Discriminative Result-Opening Gate

Terminal decision: `OPEN_DISCRIMINATIVE_READY8_QUARANTINED_TARGET_RESULT_PACKET_PROMPT`

The accepted G12 audit is bound from `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_card_rowset_repair_audit/G12_SCID_READY8_DISCRIMINATIVE_AUDIT_DECISION_LEDGER_2026-05-13.json`. The repaired discriminative rowset is bound from `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl` with SHA256 `fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3`.

This G0 gate does not score targets. It freezes the prerequisites for a separate quarantined target-result/materialization route and emits the exact next prompt only if the disk evidence is clean.

## Frozen Scope

- Source candidates: `3014`
- READY8 cards: `8`
- Rowset rows: `24112`
- Target families for the next route: `neutral_close_to_close_return_m15_horizons_v1, neutral_high_low_excursion_m15_horizons_v1`
- Horizons: `1/4/16/32` closed M15 bars
- Expected next-route row combinations before target-source fail-closed handling: `192896`

## Route Decision

The next route is `SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY`. It must rematerialize target rows over the repaired discriminative rowset and must not reuse the old redundant rowset/result rows.

Safe posture remains `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
