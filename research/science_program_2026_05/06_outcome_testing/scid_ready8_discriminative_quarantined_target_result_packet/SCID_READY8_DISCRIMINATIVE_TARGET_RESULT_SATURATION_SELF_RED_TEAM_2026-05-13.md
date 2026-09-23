# READY8 Discriminative Quarantined Target Result Saturation And Self-Red-Team

Route: `SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET`  
Evidence class: `SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY`  
Terminal decision: `MATERIALIZED_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_G12_AUDIT_REQUIRED`  
Promotion posture: `NO_PROMOTION_VERDICT`

## Saturation Questions

- Denominator leakage: checked by the duplicate/denominator ledger. The packet contains `192896` target terminal rows from `24,112` repaired discriminative ready-8 rowset rows only; blocked dependencies and expansion candidates remain outside the denominator.
- Blocked-card leakage: every target row carries one of the eight accepted ready cards. The verifier rejects any card outside `ADV-001, ADV-003, BEH-001, HAZ-001, HAZ-005, MAC-001, MAC-004, UNC-004`.
- Per-card role leakage: target rows preserve `card_row_status`, `denominator_role`, descriptor contrast fields, fail-closed source requirements, and ADV-001/ADV-003 placebo-control status instead of flattening all rows into pass claims.
- Old-rowset leakage: the target-source join ledger binds rowset hash `fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3` and rejects the old redundant rowset hash `7077a0f3fa3da2c854f2a0daab856d876992b927eb3228a161eb1cf02babb54d`.
- Duplicate-key inflation: rowset IDs, candidate-card keys, and target-result IDs are counted machine-readably. Duplicate target-result IDs are `0`.
- Source/as-of drift: target rows preserve `entry_reference_time_utc`, `decision_asof_utc`, `source_observed_asof_utc`, expected source segment hashes, consumed bar hashes, and fail-closed source mismatch reasons.
- Horizon off-by-one: entry close uses the source-control bar ending at entry reference time; horizon close/path bars use bar ends `entry + H * 15m`; excursion path bars are steps `1..H`.
- EOL/hash friction: input rowset and bar-file hashes are recomputed in the target-source join ledger; output JSONL is written with LF newlines.
- Post-outcome contamination: no broker/account/order/deal/position fields, R/PnL/win-rate/expectancy/Sharpe/performance fields, AI/API calls, paid pulls, raw market blobs, or live behavior changes are opened.
- Session/regime concentration: sidecar diagnostics preserve card, source group, seven proxy groups, partition, session, time bucket, and source coverage counts without interpreting movement as strategy performance.
- Sidecar-to-denominator leakage: adjacent route families are emitted only in a quarantined sidecar ledger with `accepted_denominator_inclusion=false`.
- Neutral movement over-interpretation: close-to-close and excursion values are neutral market movement targets only. This packet does not say whether any strategy won, lost, passed validation, or should be promoted.

## Same-Evidence-Class Follow-Through

All allowed target rows were materialized or fail-closed row-by-row. Remaining review belongs to the next G12 audit evidence-class gate, not to this builder.
