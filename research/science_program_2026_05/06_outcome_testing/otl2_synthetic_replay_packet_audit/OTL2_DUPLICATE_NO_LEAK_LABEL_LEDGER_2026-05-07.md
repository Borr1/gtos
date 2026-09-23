# OTL2 Duplicate, No-Leak, And Label Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

## Duplicate Ledger

| Packet family | Status | Required denominator policy |
|---|---|---|
| `G10-EXP-RISKBANK-005` | `BLOCKED` | One setup-level episode is the independent unit; child reentry legs cannot count as independent trades. Packet needs `setup_id`, `episode_id`, `duplicate_group_id`, and child-leg table. |
| `EXP-G3-DC-*` and `EXP-G3-TDA-007` | `BLOCKED` | Active setup lifecycle dedupe plus time-block clustering before sample floors. Packet needs `duplicate_group_id` and terminal/reopened state. |
| `EXP-G4-STOP-CASCADE-MOMENTUM-006` / `EXP-G4G6-CASCADE-GENERIC-010` | `BLOCKED` | Cascade and generic baseline rows share one `matched_group_id`; paired rows cannot be counted as independent validations. |
| `EXP-G5-AMH-004` | `BLOCKED` | One row per closed month/symbol/timeframe bundle; no intramonth row multiplication. Packet needs month-close freeze id. |
| `EXP-G5-CROWD-001` / `EXP-G5-PRED-003` | `BLOCKED` | Earliest row per setup/event cluster; repeated crowding or stress windows cluster by month/event/liquidity pool. |
| `G6-EXP-*` | `BLOCKED` | One primary setup per impulse/session/OB-zone/round-number interaction; later overlaps are diagnostics only. |
| `EXP-G7-*` | `BLOCKED` | Cluster by day/source state/fix type/stress episode and keep earliest setup per symbol/session. |

## No-Leak Ledger

| Control | Status | Evidence | Required field or test |
|---|---|---|---|
| Feature as-of cutoff | `BLOCKED` | OTL2 uses several timestamp names and no normalized packet field. | `decision_asof_utc` plus `feature_asof_utc <= decision_asof_utc` test. |
| Path labels excluded from features | `BLOCKED` | G12 leakage review requires separate decision, ordered-path, lifecycle, and execution/friction packets. | `decision_feature_allowed=false` for post-decision path/label fields. |
| Source freshness | `BLOCKED` | G7 and G5 source contracts lack parser/cache/as-of proof. | `source_fetch_or_file_asof_utc`, `source_hash`, `parser_version`, and no-lookahead fixtures. |
| Same-bar ordering | `BLOCKED` | Code has policies, but no packet field proves row-level ordering. | `same_bar_ambiguity_policy` and lower-timeframe/tick source availability fields. |
| Same-dataset contamination | `BLOCKED_FOR_VALIDATION_LANGUAGE` | Existing V2/V3 artifacts are discovery outputs; future tests must be quarantined. | `variant_frozen_at_utc`, `outcome_review_opened=false`, and pre-outcome packet hash before result read. |

## Label Ledger

| Label boundary | Status | Rule |
|---|---|---|
| Synthetic path-R primary | `CONTROL_PRESENT_PACKET_FIELD_MISSING` | All 16 OTL2 rows are synthetic replay candidates and must use `label_family=synthetic_path_r`. |
| Broker actual-R | `ABSENT_FROM_OTL2_PRIMARY_METRIC` | Broker actual-R may appear only in separate broker lanes; OTL2 packets must carry `broker_actual_r_absent_from_primary_metric=true`. |
| Lifecycle/no-fill | `SEPARATE_LANE` | Fill/no-fill and cancel/expiry states may be context but cannot be ranked by synthetic R unless a separate packet declares that role. |
| Context-only sources | `SEPARATE_LANE` | Source/readiness/status rows are not R labels and cannot inflate synthetic sample floors. |

## Ledger Decision

Every duplicate, no-leak, and label control is sufficiently defined as a governance rule but not sufficiently implemented as a concrete OTL2 packet field. Therefore every synthetic packet remains `BLOCKED_WITH_EXACT_FIELDS`.
