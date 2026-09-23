# SCID FC Implementation Design Capture Group Ledger

Route: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS`
Evidence class: `SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
Candidate boundary: `3014` source candidates; coverage only, not validation.

## baseline_control_fields
- Source contract: `offline_baseline_control_assignment_manifest`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_baseline_control_fields`
- Required fields: `partition_assignment, symbol, session_bucket, time_of_day_bucket, baseline_family_session_only_volatility_only_random_proxy_matched, baseline_assignment_seed, baseline_duplicate_policy_id`
- Runtime source surfaces: `context_control_ledger.jsonl, strategy_follow_candidates.jsonl, candidate_features_log.jsonl`
- Insertion points: `src/research_infra/forward_capture.py::build_scid_forward_source_capture_row, src/components/orchestrator.py::_record_forward_capture_candidate_shadow`
- Source/as-of rule: Use closed source-control descriptors and frozen assignment seed known at candidate decision time; never recompute from outcome labels.
- No-leak rule: No target, stop outcome, PnL, realized R, win/loss, future path, or performance threshold can influence baseline assignment.
- Redaction rule: Emit only partition/session/time buckets and deterministic seed identifiers; no account, order, deal, position, ticket, or broker identifiers.
- Fail-closed behavior: If partition seed, duplicate policy id, symbol, or time bucket is absent, emit an unavailable status and parser rejects the group.
- Duplicate policy: candidate_input_row_id and duplicate_proxy_denominator_key are required; the same candidate id must retain the same duplicate key across rows.
- Rollback plan: Disable the additive SCID writer or revert the scoped forward_capture.py patch; preserve historical rows and quarantine any invalid schema file.
- Test plan: Synthetic row with valid baseline controls passes; missing seed and duplicate-key drift fixtures fail closed.
- G12 acceptance criteria: G12 must observe no result-derived partitioning, exact duplicate key stability, and no expansion beyond the 3014-candidate source boundary.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md`

## framework_setup_family
- Source contract: `source_safe_strategy_decision_packet_logger`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_framework_setup_family`
- Required fields: `frameworks_evaluated, framework_qualified_flags, selected_framework_or_none, setup_family, framework_tiebreak_rule_id, framework_source_snapshot_hash`
- Runtime source surfaces: `strategy_follow_candidates.jsonl, strategy_follow_evaluations.jsonl, candidate_features_log.jsonl`
- Insertion points: `src/research_infra/forward_capture.py::record_live_candidate_forward_shadow, src/components/orchestrator.py::_record_forward_capture_candidate_shadow`
- Source/as-of rule: Freeze frameworks evaluated, qualified flags, selected framework, and tie-break rule before L2 verification, fill, or path observation.
- No-leak rule: Do not infer setup family from later continuation, stop/target behavior, realized path, or reviewer outcome.
- Redaction rule: Keep framework labels and source snapshot hash only; block prompt text, raw model transcript, account/order/deal/position identifiers, and result fields.
- Fail-closed behavior: Unknown framework enum, missing qualified flags, missing snapshot hash, or selected-framework mismatch emits fail-closed parser rejection.
- Duplicate policy: One framework packet per candidate denominator key; later lifecycle events may reference but not rewrite the frozen setup row.
- Rollback plan: Revert additive framework adapter in forward_capture.py and remove only the new writer call after owner-approved rollout.
- Test plan: Fixtures cover multi-framework qualified flags, no-framework neutral rows, selected-framework mismatch, and missing snapshot hash.
- G12 acceptance criteria: G12 must confirm framework source was pre-path, deterministic, framework-neutral, and compatible with accepted G12/G0 dispatch boundaries.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md`

## future_orderflow_depth_proxy_requirements
- Source contract: `orderflow_depth_proxy_context_capture`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_orderflow_depth_proxy_context`
- Required fields: `proxy_instrument, proxy_contract_month, source_family_scid_depth_mbo_mbp_other, source_file_pointer_or_vendor_cache_id, proxy_mapping_version, publication_or_capture_asof_utc, derived_feature_schema_version, orderflow_proxy_availability_status`
- Runtime source surfaces: `sierra_proxy_registry_status.jsonl, sierra_depth_feature_snapshots.jsonl, databento_live_trigger_decisions.jsonl`
- Insertion points: `src/research_infra/sierra_proxy_registry.py::registry_entry, src/research_infra/databento_forward_capture.py::build_databento_forward_request, src/research_infra/forward_capture.py::build_scid_forward_source_capture_row`
- Source/as-of rule: Only local/cache/source-control proxy context captured at or before candidate decision_asof_utc is eligible; unavailable depth is encoded as unavailable, not fetched.
- No-leak rule: No post-event depth, post-fill/order book, paid vendor pull, broker execution, or future path proxy can backfill this group.
- Redaction rule: Emit source-family, version, cache pointer hash, and availability status; forbid raw depth blobs, vendor credentials, broker ids, account ids, order ids, and paid-call payloads.
- Fail-closed behavior: If source pointer, as-of timestamp, mapping version, or feature schema version is absent or stale, parser rejects the group as unavailable/fail-closed.
- Duplicate policy: One orderflow availability descriptor per candidate key and proxy mapping version; duplicate rows must match source hash and as-of.
- Rollback plan: Disable the orderflow adapter branch while leaving other SCID capture groups intact; quarantine rows with raw depth/blob leakage.
- Test plan: Fixtures cover source unavailable, stale publication as-of, forbidden raw blob field, and valid local cache pointer.
- G12 acceptance criteria: G12 must confirm zero API/vendor/broker calls, no raw blob retention, and explicit unavailable status where source context is absent.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md`

## intended_entry_reference
- Source contract: `source_safe_strategy_decision_packet_logger`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_intended_entry_reference`
- Required fields: `entry_reference_type_market_limit_zone_midpoint_other, entry_reference_price, entry_reference_time_utc, entry_source_timeframe, entry_source_bar_hash_or_mso_snapshot_hash`
- Runtime source surfaces: `candidate_features_log.jsonl, strategy_follow_candidates.jsonl, prefill_delivery_path.jsonl`
- Insertion points: `src/research_infra/forward_capture.py::record_live_candidate_forward_shadow, src/components/orchestrator.py::_record_forward_capture_candidate_shadow`
- Source/as-of rule: Entry reference price/type/timeframe must be emitted from the decision packet before fill, cancel, expiry, target, stop, or path review.
- No-leak rule: Do not substitute actual fill price, slippage, broker order ticket, realized entry quality, later candle high/low, or path hindsight.
- Redaction rule: Keep intended reference and source snapshot hash only; block MT5 order tickets, pending tickets, deal ids, account ids, and slippage fields.
- Fail-closed behavior: Missing entry price/type/timeframe/snapshot hash, stale as-of, or raw fill identifier causes parser rejection for this group.
- Duplicate policy: The first accepted intended-entry packet freezes the candidate denominator key; replacements require a lifecycle event rather than in-place rewrite.
- Rollback plan: Revert the additive entry-reference adapter and stop writing new SCID rows; invalid historical rows remain quarantined for audit.
- Test plan: Fixtures cover market entry, limit-zone midpoint, missing source hash, fill-price substitution, and duplicate replacement handling.
- G12 acceptance criteria: G12 must verify intended-entry provenance is pre-fill and source-safe, with no broker or realized execution fields.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md`

## intended_side_direction
- Source contract: `source_safe_strategy_decision_packet_logger`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_intended_side_direction`
- Required fields: `strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY, side_source_component, side_source_rule_or_model_hash, side_emission_reason_code`
- Runtime source surfaces: `strategy_follow_candidates.jsonl, strategy_follow_evaluations.jsonl, candidate_features_log.jsonl`
- Insertion points: `src/research_infra/forward_capture.py::record_live_candidate_forward_shadow, src/components/orchestrator.py::_record_forward_capture_candidate_shadow`
- Source/as-of rule: Freeze LONG/SHORT/NEUTRAL/NO_STRATEGY side and reason code before target, stop, path, fill, or result horizon opens.
- No-leak rule: Do not infer side from realized trend, future labels, post-decision price movement, reviewer outcome, or result attribution.
- Redaction rule: Emit side enum and source-rule/model hash only; never include raw prompt text, raw model response, broker account, order, deal, or position ids.
- Fail-closed behavior: Invalid side enum, missing reason code, missing source hash, or post-decision timestamp causes fail-closed parser rejection.
- Duplicate policy: One frozen side per candidate denominator key; lifecycle replacements must emit a new event state and preserve previous row immutability.
- Rollback plan: Disable or revert the side adapter in the forward-capture writer; restart orchestrators only after owner-approved implementation rollback.
- Test plan: Fixtures cover all side enums, missing reason, invalid enum, post-decision as-of, and duplicate side drift.
- G12 acceptance criteria: G12 must confirm side is emitted before path/result and has no dependence on future labels or broker execution state.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md`

## intended_stop_reference
- Source contract: `source_safe_strategy_decision_packet_logger`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_intended_stop_reference`
- Required fields: `stop_reference_price, stop_reference_type, stop_buffer_rule_id, stop_source_structure_id, stop_source_snapshot_hash`
- Runtime source surfaces: `candidate_features_log.jsonl, strategy_follow_candidates.jsonl, prefill_delivery_path.jsonl`
- Insertion points: `src/research_infra/forward_capture.py::record_live_candidate_forward_shadow, src/components/orchestrator.py::_record_forward_capture_candidate_shadow`
- Source/as-of rule: Stop reference and buffer rule are frozen at strategy decision time before path review or any terminal state.
- No-leak rule: Do not refit stop from later adverse excursion, broker close, target/stop outcome, trailing stop behavior, or reviewer judgment.
- Redaction rule: Emit intended stop structure id, rule id, and snapshot hash; block broker close tickets, realized loss/R, account ids, and order/deal ids.
- Fail-closed behavior: Missing stop price/type/rule/source hash, impossible price, stale as-of, or result-derived stop source causes parser rejection.
- Duplicate policy: Same candidate key must retain the same frozen stop unless a separate lifecycle replacement event is recorded.
- Rollback plan: Revert the stop adapter; use existing forward-capture flags to stop writes, then G12-review any quarantined invalid stop rows.
- Test plan: Fixtures cover valid OB/FVG/breaker stop sources, missing source hash, result-fitted stop, and duplicate drift.
- G12 acceptance criteria: G12 must verify no stop field is derived from realized path or broker close evidence.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md`

## intended_target_reference
- Source contract: `source_safe_strategy_decision_packet_logger`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_intended_target_reference`
- Required fields: `target_reference_price, target_reference_type, target_rule_id, risk_reward_reference, target_source_snapshot_hash`
- Runtime source surfaces: `candidate_features_log.jsonl, strategy_follow_candidates.jsonl, prefill_delivery_path.jsonl`
- Insertion points: `src/research_infra/forward_capture.py::record_live_candidate_forward_shadow, src/components/orchestrator.py::_record_forward_capture_candidate_shadow`
- Source/as-of rule: Target reference, target rule, and RR reference are emitted and frozen before fill, path review, or terminal status.
- No-leak rule: Neutral horizons are not strategy targets; no later high/low, target hit, stop hit, realized R, PnL, or performance outcome may define target fields.
- Redaction rule: Emit intended target metadata and source snapshot hash only; block broker tickets, deal ids, result labels, and performance metrics.
- Fail-closed behavior: Missing target price/type/rule/source hash, result-derived target, or stale as-of causes parser rejection.
- Duplicate policy: Target packet is immutable per candidate denominator key; replacement can only occur through explicit lifecycle state event.
- Rollback plan: Revert the target adapter and quarantine any row that includes result/performance fields.
- Test plan: Fixtures cover valid RR target, neutral no-strategy target absence, result-derived target rejection, and duplicate target drift.
- G12 acceptance criteria: G12 must confirm target semantics are intended-source only and do not open outcome review.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md`

## lifecycle_fill_cancel_expiry_source_status
- Source contract: `nonbroker_pending_intent_lifecycle_event_logger`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_lifecycle_source_status`
- Required fields: `pending_intent_id, source_event_type_created_updated_expired_cancelled_replaced_no_order, source_event_utc, source_event_clock_basis, intent_state_before, intent_state_after, redacted_order_bridge_hash_optional`
- Runtime source surfaces: `pending_limit_lifecycle.jsonl, strategy_follow_candidates.jsonl`
- Insertion points: `src/components/pending_limit_lifecycle_logger.py::record_pending_limit_lifecycle, src/research_infra/forward_capture.py::record_scid_forward_capture_lifecycle_event`
- Source/as-of rule: Append-only intent lifecycle state is eligible only from GTOS internal intent events as of event time; broker history is not a source.
- No-leak rule: Do not include broker account/order/deal/position/history ids, fill price, slippage, realized R, synthetic path R, PnL, or target/stop result labels.
- Redaction rule: Map pending/order/ticket fields to forbidden or salted optional bridge hash only after owner approval; default raw ids are rejected.
- Fail-closed behavior: Any raw pending_ticket, mt5_order_ticket, trade_state_ticket, actual_r, synthetic_path_r, slippage_price, broker_fill_state, or account id fails closed.
- Duplicate policy: Lifecycle rows are append-only by event time and intent id; they reference but never mutate the frozen candidate denominator row.
- Rollback plan: Disable lifecycle adapter independently; leave existing pending_limit_lifecycle logger untouched and quarantine SCID lifecycle rows if redaction fails.
- Test plan: Fixtures cover created/no_order/expired/cancelled/replaced states plus forbidden ticket, realized R, and slippage leakage.
- G12 acceptance criteria: G12 must verify status-only lifecycle capture, no broker identifiers, and no result/performance leakage.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_002_ORCHESTRATOR_AND_LIFECYCLE_WIRING_2026-05-12.patch.md`

## lower_timeframe_asof_path_availability
- Source contract: `ltf_source_availability_and_path_descriptor_capture`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_ltf_asof_path_availability`
- Required fields: `ltf_timeframes_available, ltf_source_file_pointer_or_cache_id, ltf_source_hash, decision_minus_window_start_utc, bars_present_by_timeframe, asof_path_descriptor_version, ltf_availability_status`
- Runtime source surfaces: `candidate_ltf_path_order.jsonl, prefill_delivery_path.jsonl, strategy_follow_candidates.jsonl`
- Insertion points: `src/research_infra/candidate_path_contract.py::build_candidate_path_contract_row, src/research_infra/prefill_delivery_path_audit.py::build_prefill_delivery_path_audit_rows, src/research_infra/forward_capture.py::build_scid_forward_source_capture_row`
- Source/as-of rule: Only bars or ticks with timestamps <= decision_asof_utc may be summarized; future path descriptors must be unavailable/fail-closed.
- No-leak rule: No target/stop hit, fill outcome, post-decision high/low, path result, or realized label may be encoded in availability fields.
- Redaction rule: Emit cache/source pointer hashes and bar-count descriptors only; block raw tick blobs, broker ids, account ids, order ids, and result metrics.
- Fail-closed behavior: Missing source hash, stale bar range, post-decision timestamp, or future-path descriptor triggers fail-closed unavailable status.
- Duplicate policy: Availability descriptor is stable per candidate key, timeframe set, source hash, and descriptor version.
- Rollback plan: Disable the LTF adapter branch and keep existing candidate_ltf_path_order/prefill logs unchanged.
- Test plan: Fixtures cover valid as-of availability, missing cache, stale source hash, and post-decision bar inclusion.
- G12 acceptance criteria: G12 must verify all LTF references are as-of and availability-only, not outcome/path scoring.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md`

## poi_type_bounds_source
- Source contract: `source_safe_mso_snapshot_and_poi_logger`
- Future capture owner: `src/research_infra/forward_capture.py::build_scid_poi_type_bounds_source`
- Required fields: `poi_type_enum_ob_fvg_breaker_swing_other_none, poi_lower_bound, poi_upper_bound, poi_source_timeframe, poi_source_bar_ids, mso_snapshot_hash, poi_detection_rule_version`
- Runtime source surfaces: `strategy_follow_evaluations.jsonl, candidate_features_log.jsonl, trade_capture.py decision packet surface`
- Insertion points: `src/research_infra/forward_capture.py::record_live_mso_forward_shadow, src/components/orchestrator.py::_record_forward_capture_evaluation_shadow`
- Source/as-of rule: POI type, bounds, source timeframe/bar ids, and MSO snapshot hash must come from the market-state snapshot before candidate path/result review.
- No-leak rule: Do not reconstruct POI from later price path, fill result, target/stop event, reviewer outcome, or performance label.
- Redaction rule: Emit bounded POI metadata and snapshot hashes; block raw prompt/model transcript, broker identifiers, account/order/deal/position ids, and result metrics.
- Fail-closed behavior: Invalid POI enum, missing bounds for non-none POI, missing MSO snapshot hash, or post-decision reconstruction fails closed.
- Duplicate policy: POI snapshot hash and bounds are immutable per candidate denominator key unless a new evaluation row is emitted before candidate decision.
- Rollback plan: Disable POI adapter independently and quarantine any rows with missing snapshot provenance.
- Test plan: Fixtures cover OB/FVG/breaker/swing/none POI, missing bounds, invalid enum, and reconstructed-after-path rejection.
- G12 acceptance criteria: G12 must confirm POI provenance is source-safe MSO state and no path/result data influenced bounds.
- Proposed patch artifact: `proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md`
