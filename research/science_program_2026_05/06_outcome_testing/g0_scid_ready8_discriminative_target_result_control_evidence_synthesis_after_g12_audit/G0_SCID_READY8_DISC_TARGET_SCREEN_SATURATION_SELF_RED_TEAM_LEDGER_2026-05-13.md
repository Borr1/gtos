# G0 SCID READY8 Discriminative Target-Result Screen Saturation Self-Red-Team

Date: 2026-05-13

Evidence class: `G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_ONLY`

Promotion posture: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Saturation Result

- Target rows processed: `192896` / `192896`.
- Target files read: `16` / `16`.
- Candidate-level rows written: `24112` / `24112`.
- Aggregate rows: `4561`.
- Contrast rows: `3400`.
- Explanation rows: `8689`.
- Ambiguity rows: `8691`.
- Same-class unanswered ambiguities remaining: `0`.

## Red-Team Checks

- Evidence-class confusion: closed. The artifacts are neutral movement control evidence only, not validation or performance.
- Denominator leakage: closed by accepted G12 sidecar quarantine plus this screen's use of only the 16 accepted READY8 target files.
- Silent fail-closed dropping: closed. Fail-closed rows remain in aggregate, candidate, partition, and failure-anatomy ledgers.
- Duplicate/concentration blindness: closed. Duplicate pass-card-count buckets are computed for every target row.
- Top-N shortcut: closed. Candidate and explanation ledgers are full-population derived ledgers, not representative excerpts.
- Horizon/target-family ambiguity: closed into explicit horizon and target-family ledgers.
- Broker/account/order truth temptation: closed as evidence-class impossible.
- Raw market blob commitment: closed. This route writes derived ledgers only; upstream target JSONL files are existing accepted packet inputs.

Stop condition: complete only after independent G12 audit is routed for these new screen artifacts.
