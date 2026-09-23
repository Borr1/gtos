# OTL2 Synthetic Replay Packet Audit - 2026-05-07

**Scope:** OTL2 packet-readiness audit for the 16 `synthetic_replay_existing_data_audit` packets in `OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json`  
**Branch/worktree:** `otl2-synthetic` at `C:\tmp\gtos_otl\OTL2`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Replay outcomes run:** `false`  
**Result/quarantine outputs created:** `false`

## Audit Decision

All 16 OTL2 packets are `BLOCKED_WITH_EXACT_FIELDS`. None are ready for test implementation from the current worktree evidence without first creating concrete frozen packet files and source/as-of field contracts.

This is not a market verdict. The audit only says the packet substrate is not yet safe enough to open replay outcomes.

## Controlling Evidence

| Evidence | Status |
|---|---|
| `.context/LIVE_STATE.md` regenerated | Done. HEAD `edb04ba6`; branch `otl2-synthetic`; working tree was clean before preflight except generated live state. |
| `OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json` | 97 packets, 16 synthetic replay packets. Manifest says packet definitions only, outcomes closed. |
| `OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md` | Requires packet audit before lifecycle/synthetic outcome tests; no source validation flips; result quarantine only after packet readiness. |
| `SOURCE_CONTRACT_REGISTRY_2026-05-06.json` | 86 source contracts, `validation_safe=true` count is 0. |
| `EXPERIMENT_PREREGISTRY_2026-05-06.json` | 97 preregs, `outcome_review_opened=true` count is 0. |
| Replay default event log | `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/` is absent in this worktree. |
| OTL2 quarantine path | `research/science_program_2026_05/06_outcome_testing/quarantine/` does not exist and was not created. |

## Packet Readiness Table

| Packet | Experiment | Decision | Exact blocker fields |
|---|---|---|---|
| `OTG0-PKT-013` | `G10-EXP-RISKBANK-005` | `BLOCKED_WITH_EXACT_FIELDS` | Missing concrete ordered path packet; missing row-level `ordered_path_source_id`, `path_start_utc`, `path_end_utc`, `source_hash`, `duplicate_group_id`, `decision_asof_utc`, and `cost_model_version`; V3 code has risk-bank and same-bar handling but source event log is absent and existing V3 artifacts are same-dataset discovery outputs, not frozen packet inputs. |
| `OTG0-PKT-031` | `EXP-G3-DC-OVERSHOOT-002` | `BLOCKED_WITH_EXACT_FIELDS` | Missing DC feature packet with `dc_overshoot_ratio_at_decision`, normalized `decision_asof_utc`, row-level path packet, `duplicate_group_id`, `source_hash`, cost model, and same-bar policy. Registered sources are context/local only and not validation-safe. |
| `OTG0-PKT-032` | `EXP-G3-DC-SWING-001` | `BLOCKED_WITH_EXACT_FIELDS` | Missing DC threshold-grid feature packet and frozen baseline matrix; no implementation found that emits `dc_event_count_at_decision`, `dc_event_rate_lookback_only`, packet path bounds, `duplicate_group_id`, or source hashes. |
| `OTG0-PKT-036` | `EXP-G3-TDA-007` | `BLOCKED_WITH_EXACT_FIELDS` | Missing TDA embedding packet and fixed parser/window contract; no code path found that emits `embedding_window_end_at_decision`, persistence summary fields, `path_start_utc`, `path_end_utc`, source hashes, or duplicate group fields for OTL2. |
| `OTG0-PKT-044` | `EXP-G4-STOP-CASCADE-MOMENTUM-006` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contracts; no concrete packet for sweep/cascade baseline; missing `ordered_path_source_id`, `entry_sl_tp_or_level_packet`, `matched_group_id` or `duplicate_group_id`, source hashes, and same-bar policy. |
| `OTG0-PKT-049` | `EXP-G4G6-CASCADE-GENERIC-010` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contracts; missing G4/G6 matched packet, source-valid flow/depth fields, `matched_group_id`, ordered path packet, source hashes, cost model, and source-symbol separation. |
| `OTG0-PKT-052` | `EXP-G5-AMH-004` | `BLOCKED_WITH_EXACT_FIELDS` | Unresolved literature/source refs; source is shadow/local monitoring only; missing closed monthly packet with frozen `month_closed_timestamp_utc`, next-month path label separation, `source_hash`, `duplicate_group_id`, and sample floor/effective-N proof. |
| `OTG0-PKT-053` | `EXP-G5-CROWD-001` | `BLOCKED_WITH_EXACT_FIELDS` | Google Trends/crowding source has no extractor/cache/no-lookahead tests; unresolved literature refs remain; missing frozen crowding tercile packet, source publication timestamps, query protocol hash, `duplicate_group_id`, ordered path packet, and cost model. |
| `OTG0-PKT-056` | `EXP-G5-PRED-003` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contracts and unresolved literature refs; missing pre-outcome stress-proxy packet, G4 source-valid stress source, matched baseline packet, source hashes, ordered path, duplicate cluster key, and no-leak whitelist. |
| `OTG0-PKT-060` | `G6-EXP-001-OB-VS-GENERIC-RETRACE` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contracts; missing OB-vs-generic retrace packet, generic 80% retrace comparator, `entry_sl_tp_or_level_packet`, `duplicate_setup_id`/`duplicate_group_id`, source hashes, and same-dataset contamination guard. |
| `OTG0-PKT-062` | `G6-EXP-003-OPENING-DRIVE-CONTINUATION` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contracts; missing session opening-drive packet, frozen range definition, `path_start_utc`, `path_end_utc`, spread/cost packet, duplicate breakout key, and no-lookahead news/window exclusion proof. |
| `OTG0-PKT-063` | `G6-EXP-004-EXHAUSTION-CHANGEPOINT` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contracts; missing exhaustion/changepoint feature packet, threshold freeze, FVG interaction policy, ordered path packet, duplicate impulse key, source hash, cost model, and same-dataset threshold contamination guard. |
| `OTG0-PKT-066` | `G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contracts; missing gold OB/round-number packet with source hash, predefined round-number bands, OB bounds, liquidity sweep as-of fields, ordered path, duplicate OB-zone key, and cost model. |
| `OTG0-PKT-069` | `EXP-G7-CROSSASSET-STRESS-008` | `BLOCKED_WITH_EXACT_FIELDS` | FRED/DXY sources are not validation-safe and lack normalized cache/parser/as-of proof; missing stress-state packet, `source_cache_time_utc`, `stress_state_timestamp_utc`, source hashes, ordered path, duplicate stress episode key, and rate/DXY close-time rule. |
| `OTG0-PKT-074` | `EXP-G7-LBMA-FIX-004` | `BLOCKED_WITH_EXACT_FIELDS` | LBMA source is timestamp context only; parser/timestamp-normalization test missing; missing fix-window packet with source hash, timezone rule, matched non-fix controls, ordered path, duplicate setup/fix key, and spread/cost packet. |
| `OTG0-PKT-075` | `EXP-G7-USD-REALRATE-001` | `BLOCKED_WITH_EXACT_FIELDS` | FRED/DXY sources lack validation-ready cache/parser/as-of proof; local DXY CSV is explicitly not accepted by source contract; missing USD/real-rate state packet, source hashes, publication/close times, ordered path, duplicate day/setup key, and no same-day daily close leakage proof. |

## Resolved Versus Blocked Ambiguities

| Ambiguity | Audit result |
|---|---|
| Ordered path availability | Blocked. Current default V2/V3 event-log directory is absent; existing V3 JSON/report files are output artifacts, not safe input packets. |
| Same-bar ambiguity | Partially controlled in V2/V3 code, but blocked at packet level because no concrete OTL2 packet carries `same_bar_ambiguity_policy` plus ordered lower-timeframe source evidence. |
| `setup_id` uniqueness | Textual duplicate policies exist, but no packet-level `duplicate_group_id` or primary countable key exists for OTL2. |
| `decision_asof_utc` | Blocked. Existing code uses mixed names such as `setup_decision_close_utc` and `decision_time_utc`; OTL2 requires a normalized field. |
| `path_start_utc` / `path_end_utc` | Blocked. Some code reports fill/exit/path-row clocks, but no OTL2 packet guarantees path start/end bounds and source identity. |
| Entry/SL/TP reconstruction | Blocked. V3 can read mechanical entry/SL/TP, and prefill code records entry/initial SL/TP, but original POI bounds and deterministic level-packet references are missing in current G10 audit evidence. |
| Cost model | Blocked. V2 has a summary `cost_model`, V3 has `cost_key`, but OTL2 needs a row-level or packet-level `cost_model_version` tied to the metric. |
| Duplicate families | Global OTG0 duplicate families remain outside these 16 packets, but G4/G6 and G6 comparator packets need matched-group denominator policy before testing. |
| Source hashes | Blocked. Source contracts list paths or pages, but OTL2 packet rows must carry `source_hash`; G10 CD2 missing-field audit explicitly records source hash missing on current prefill/path rows. |
| No-leak fields | Blocked until each packet has an implemented as-of feature whitelist and excludes post-decision labels from decision fields. |
| Synthetic-vs-broker labels | Control passes at governance level; every OTL2 packet remains synthetic-path-only and cannot use broker actual-R. Implementation still needs explicit packet fields. |
| Sample floor and effective-N | Blocked. Raw row counts cannot be accepted before duplicate-aware primary countable rows and effective-N are available. |
| Same-dataset contamination | Blocked for validation language. Existing V3/V2 discovery artifacts are same-dataset and cannot be used as packet-ready validation; future OTL2 results must be quarantined discovery only after packet readiness. |
| Stale context | Resolved for this audit by reading direct OTG0/G0/G12/source/code artifacts instead of relying on stale summary text. Context refresh is required after this audit. |

## Required Next Exact Questions

1. Where is the frozen OTL2 input packet file for each experiment that contains the synthetic class fields, source hashes, duplicate keys, and no-leak timestamps without outcome result columns?
2. If the intended path source is the V2 structural-level event log, should the missing `data/external/validation/calendar_macro_bundle_v1/.../path_scaling_v2_structural_levels/` files be restored to this worktree, or should a new frozen packet builder regenerate non-result packet inputs from local OHLCV?
3. What exact row-level schema will normalize `decision_time_utc`, `setup_decision_close_utc`, and `decision_timestamp_utc` into `decision_asof_utc`?
4. What packet-level `cost_model_version` should be frozen for synthetic replay, and how will it stay separate from broker actual-R cost accounting?
5. For G4/G6/G5/G7 packets with no or unsafe source contracts, which OTL3 source/as-of cleanup dossiers must clear before OTL2 can build packet inputs?

## No Promotion Verdict

This audit authorizes no outcome opening, replay result generation, source validation flip, prompt edit, risk/config change, selector change, execution change, MT5 action, canary action, paid data call, credential action, remote push, or order behavior change.
