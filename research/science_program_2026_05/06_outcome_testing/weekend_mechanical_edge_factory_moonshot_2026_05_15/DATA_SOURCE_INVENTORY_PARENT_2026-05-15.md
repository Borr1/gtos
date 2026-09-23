# Parent Initial Source Inventory

Generated UTC: `2026-05-15T15:04:53Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Root Summary

| Root | Status | Files | Bytes | Newest UTC | Families |
|---|---:|---:|---:|---|---|
| data | ok | 339 | 182630663 | 2026-05-15T14:02:16Z | {"research_artifact": 181, "shadow_log": 4, "sierra_scid": 153, "tick_data": 1} |
| shadow_logs | ok | 121 | 974459874 | 2026-05-15T14:03:58Z | {"shadow_log": 115, "sierra_scid": 5, "tick_data": 1} |
| research | ok | 9248 | 6116584416 | 2026-05-15T15:04:49Z | {"research_artifact": 8526, "shadow_log": 268, "sierra_depth": 24, "sierra_scid": 152, "tick_data": 278} |
| knowledge_base | ok | 784 | 56641583 | 2026-05-15T14:02:17Z | {"config": 323, "knowledge_base": 6, "research_artifact": 310, "shadow_log": 145} |
| src | ok | 210 | 4271861 | 2026-05-15T14:03:58Z | {"research_artifact": 105, "sierra_scid": 3, "source_code": 98, "tick_data": 4} |
| scripts | ok | 400 | 9392923 | 2026-05-15T14:03:48Z | {"research_artifact": 134, "shadow_log": 1, "sierra_depth": 2, "sierra_scid": 10, "source_code": 251, "tick_data": 2} |
| config | ok | 5 | 63915 | 2026-05-15T14:02:15Z | {"config": 4, "research_artifact": 1} |
| tests | ok | 338 | 4749715 | 2026-05-15T14:04:01Z | {"research_artifact": 28, "shadow_log": 2, "sierra_depth": 2, "sierra_scid": 11, "source_code": 290, "tick_data": 5} |
| pipeline_state | ok | 5 | 269830 | 2026-05-15T14:02:25Z | {"research_artifact": 4, "sierra_scid": 1} |
| absolute::data | ok | 1201 | 22766416926 | 2026-05-15T15:06:04Z | {"market_csv": 6, "other": 121, "research_artifact": 640, "shadow_log": 156, "sierra_scid": 153, "tick_data": 125} |
| absolute::ticks | ok | 122 | 579815184 | 2026-05-15T15:06:04Z | {"tick_data": 122} |
| absolute::external | ok | 582 | 21024659579 | 2026-05-03T20:53:39Z | {"market_csv": 6, "other": 121, "research_artifact": 285, "shadow_log": 152, "sierra_scid": 18} |
| absolute::shadow_logs | ok | 183 | 1272126775 | 2026-05-15T15:05:08Z | {"shadow_log": 172, "sierra_scid": 9, "tick_data": 2} |
| absolute::exports | ok | 90 | 93667713 | 2026-04-25T13:13:58Z | {"other": 3, "research_artifact": 86, "tick_data": 1} |
| absolute::gtos_otb | ok | 0 | 0 |  | {} |
| absolute::SierraChart | ok | 505 | 53396673816 | 2026-05-15T15:06:05Z | {"sierra_scid": 501, "tick_data": 4} |

## Family Totals

| Family | Files | Bytes |
|---|---:|---:|
| config | 327 | 343439 |
| knowledge_base | 6 | 36884 |
| market_csv | 12 | 500 |
| other | 245 | 7536979986 |
| research_artifact | 10300 | 3166763209 |
| shadow_log | 1015 | 41029655142 |
| sierra_depth | 28 | 883839 |
| sierra_scid | 1016 | 53265041749 |
| source_code | 639 | 11075954 |
| tick_data | 545 | 1471644071 |

## Immediate Data Routes

- `shadow_log_market_behavior_mining`: use fresh candidate/path/shadow logs for first no-API descriptor mining.
- `research_artifact_reuse`: reuse accepted READY8/SCID/no-API artifacts before inventing new denominators.
- `tick_and_sierra_targeted_contracts`: consume binary tick/SCID/depth data only through route-specific source contracts.

## Cautions

- This inventory is source discovery, not validation approval.
- Large/binary files are not fully hashed here; route-specific source contracts must hash and parse them before outcome use.
- Worktree absence remains nonterminal; blocked roots should become access/search tasks, not final data absence claims.
