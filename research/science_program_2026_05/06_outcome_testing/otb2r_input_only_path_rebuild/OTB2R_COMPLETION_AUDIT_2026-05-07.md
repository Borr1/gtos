# OTB2R Completion Audit - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

## Objective Restatement

Rebuild rejected OTB2 synthetic/path packet inputs under an OTB2R input-only lane by hashing sanitized candidate/path projections, proving coverage through path_end_utc, declaring duplicate and same-bar policies, and leaving uncovered packets blocked without opening outcome review.

## Prompt-To-Artifact Checklist

| Requirement | Status | Evidence |
| --- | --- | --- |
| Run mandatory GTOS preflight from C:/tmp/gtos_otb/OTB2R at main HEAD 6f5fc730 | PASS | LIVE_STATE regenerated before build; builder git_head_at_generation=6f5fc730b86d7c262b939a58bdf9a7cebdbc753a. |
| Use controlling inputs G12 audit, OTB2, OTB3, OTB0/OTG0/OTL2 controls, and research_current_state | PASS | 13 controlling inputs hashed in packet manifest. |
| Create input-only projections before source hashing | PASS | 5 projection files written and hashed; packet source hashes use projection hashes only. |
| Exclude path_order_label, touch times, hit_tp/hit_sl, path/result labels, R values, and future/outcome fields from projections before hashing | PASS | projection forbidden key counts after sanitization are empty for all projection files. |
| Bind every included path window to coverage-valid M1/OHLC or explicit input-only path-order rows reaching path_end_utc | PASS | included=86 blocked=0 coverage_modes={'EXPLICIT_INPUT_ONLY_PATH_ORDER_ROW_COVERAGE_VALID': 86}. |
| Keep packet blocked with exact next question if coverage is incomplete | PASS | coverage audit carries blocked_rows with next_exact_question; G10 has no blocked rows, other packets remain BLOCKED_WITH_NEXT_EXACT_QUESTION. |
| Produce sanitized source hashes, duplicate_group_id policy, coverage audit, same-bar ambiguity policy, and packet manifests under otb2r_input_only_path_rebuild/ | PASS | OTB2R_SANITIZED_SOURCE_HASHES, OTB2R_DUPLICATE_GROUP_POLICY, OTB2R_COVERAGE_AUDIT, OTB2R_SAME_BAR_AMBIGUITY_POLICY, OTB2R_PACKET_MANIFEST, and packet files are written. |
| Preserve NO_PROMOTION_VERDICT, validation_safe=false, and outcome_review_opened=false | PASS | All generated top-level artifacts carry NO_PROMOTION_VERDICT with validation_safe=false and outcome_review_opened=false. |
| No replay outcomes, R/result value use, quarantine/result outputs, paid/API/Databento/network, registry edits, or live-surface changes | PASS | Builder writes only OTB2R research artifacts; manifest reports zero external/API/Databento calls and no result/quarantine outputs. |
| No forbidden result/future keys remain in projection or packet records beyond required guard metadata | PASS | forbidden scan bad path count=0. |
| Declare duplicate raw rows versus unique duplicate_group_id denominator | PASS | raw=86 unique=86 drift=0. |
| Declare same-bar ambiguity policy without guessing terminal order | PASS | terminal_order_claim_allowed=False policy_counts={'M1_PATH_ORDER_LOG_AVAILABLE__SAME_MINUTE_AMBIGUITY_FLAGGED_NOT_GUESSED': 86}. |

## Verdict

- Can mark OTB2R input-only rebuild complete: `True`
- Ready for G12 reaudit: `1`
- Blocked with next exact question: `15`
- External/API/Databento calls: `0`
- Result/quarantine outputs created: `False`
