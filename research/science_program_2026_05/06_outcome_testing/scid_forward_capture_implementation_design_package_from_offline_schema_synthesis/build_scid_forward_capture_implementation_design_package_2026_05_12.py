"""Build the SCID forward-capture implementation design package.

This route is design-only. It emits review artifacts and proposed patch plans
under this research directory; it does not edit production code.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-12"
ROUTE_ID = "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS"
EVIDENCE_CLASS = (
    "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY"
)
CANDIDATE_ROWS_EXPECTED = 3014
SCHEMA_VERSION = "scid_forward_source_capture_v1"
ROUTE_DIR = Path(__file__).resolve().parent
PROPOSED_PATCH_DIR = ROUTE_DIR / "proposed_patches"

SAFE_FLAGS: dict[str, Any] = {
    "evidence_class": EVIDENCE_CLASS,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "broker_or_account_evidence_opened": False,
    "ai_api_call_opened": False,
    "paid_vendor_call_opened": False,
    "raw_blob_capture_opened": False,
    "result_scoring_opened": False,
    "performance_claim_opened": False,
    "prompt_change_opened": False,
    "config_change_opened": False,
    "risk_logic_change_opened": False,
    "execution_logic_change_opened": False,
    "canary_or_selector_change_opened": False,
}

CONTROL_INPUTS = [
    {
        "name": "accepted_g12_decision",
        "path": "research/science_program_2026_05/06_outcome_testing/"
        "g12_scid_forward_capture_offline_schema_implementation_package_audit/"
        "G12_SCID_FC_SCHEMA_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "required_status": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
    },
    {
        "name": "accepted_g12_schema_contract",
        "path": "research/science_program_2026_05/06_outcome_testing/"
        "g12_scid_forward_capture_offline_schema_implementation_package_audit/"
        "G12_SCID_FC_SCHEMA_AUDIT_SCHEMA_CONTRACT_AUDIT_2026-05-12.json",
        "required_status": "ten accepted capture groups, 3014 candidate-row coverage expectation, duplicate-key policy accepted",
    },
    {
        "name": "accepted_offline_schema_package",
        "path": "research/science_program_2026_05/06_outcome_testing/"
        "scid_forward_capture_offline_schema_implementation_package/"
        "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_ACCEPTED_G12_G0_HANDOFF_RECONCILIATION_2026-05-12.json",
        "required_status": "schema version scid_forward_source_capture_v1 accepted for future source capture",
    },
    {
        "name": "g0_synthesis_route_bundle",
        "path": "research/science_program_2026_05/06_outcome_testing/"
        "g0_scid_forward_capture_offline_schema_package_synthesis_control/"
        "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_DECISION_LEDGER_2026-05-12.json",
        "required_status": "rank 1 route is implementation design package; live_wiring_ready=false",
    },
    {
        "name": "g0_future_source_capture_gate",
        "path": "research/science_program_2026_05/06_outcome_testing/"
        "g0_scid_forward_capture_offline_schema_package_synthesis_control/"
        "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_FUTURE_SOURCE_CAPTURE_APPROVAL_GATE_LEDGER_2026-05-12.json",
        "required_status": "design/test-harness/read-only alignment allowed; live wiring requires owner approval",
    },
]


CAPTURE_GROUPS: list[dict[str, Any]] = [
    {
        "capture_group": "baseline_control_fields",
        "required_fields": [
            "partition_assignment",
            "symbol",
            "session_bucket",
            "time_of_day_bucket",
            "baseline_family_session_only_volatility_only_random_proxy_matched",
            "baseline_assignment_seed",
            "baseline_duplicate_policy_id",
        ],
        "source_contract": "offline_baseline_control_assignment_manifest",
        "runtime_source_surfaces": [
            "context_control_ledger.jsonl",
            "strategy_follow_candidates.jsonl",
            "candidate_features_log.jsonl",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_baseline_control_fields",
        "insertion_points": [
            "src/research_infra/forward_capture.py::build_scid_forward_source_capture_row",
            "src/components/orchestrator.py::_record_forward_capture_candidate_shadow",
        ],
        "source_asof_rule": "Use closed source-control descriptors and frozen assignment seed known at candidate decision time; never recompute from outcome labels.",
        "no_leak_rule": "No target, stop outcome, PnL, realized R, win/loss, future path, or performance threshold can influence baseline assignment.",
        "redaction_rule": "Emit only partition/session/time buckets and deterministic seed identifiers; no account, order, deal, position, ticket, or broker identifiers.",
        "fail_closed_behavior": "If partition seed, duplicate policy id, symbol, or time bucket is absent, emit an unavailable status and parser rejects the group.",
        "duplicate_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required; the same candidate id must retain the same duplicate key across rows.",
        "rollback_plan": "Disable the additive SCID writer or revert the scoped forward_capture.py patch; preserve historical rows and quarantine any invalid schema file.",
        "test_plan": "Synthetic row with valid baseline controls passes; missing seed and duplicate-key drift fixtures fail closed.",
        "g12_acceptance_criteria": "G12 must observe no result-derived partitioning, exact duplicate key stability, and no expansion beyond the 3014-candidate source boundary.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
    },
    {
        "capture_group": "framework_setup_family",
        "required_fields": [
            "frameworks_evaluated",
            "framework_qualified_flags",
            "selected_framework_or_none",
            "setup_family",
            "framework_tiebreak_rule_id",
            "framework_source_snapshot_hash",
        ],
        "source_contract": "source_safe_strategy_decision_packet_logger",
        "runtime_source_surfaces": [
            "strategy_follow_candidates.jsonl",
            "strategy_follow_evaluations.jsonl",
            "candidate_features_log.jsonl",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_framework_setup_family",
        "insertion_points": [
            "src/research_infra/forward_capture.py::record_live_candidate_forward_shadow",
            "src/components/orchestrator.py::_record_forward_capture_candidate_shadow",
        ],
        "source_asof_rule": "Freeze frameworks evaluated, qualified flags, selected framework, and tie-break rule before L2 verification, fill, or path observation.",
        "no_leak_rule": "Do not infer setup family from later continuation, stop/target behavior, realized path, or reviewer outcome.",
        "redaction_rule": "Keep framework labels and source snapshot hash only; block prompt text, raw model transcript, account/order/deal/position identifiers, and result fields.",
        "fail_closed_behavior": "Unknown framework enum, missing qualified flags, missing snapshot hash, or selected-framework mismatch emits fail-closed parser rejection.",
        "duplicate_policy": "One framework packet per candidate denominator key; later lifecycle events may reference but not rewrite the frozen setup row.",
        "rollback_plan": "Revert additive framework adapter in forward_capture.py and remove only the new writer call after owner-approved rollout.",
        "test_plan": "Fixtures cover multi-framework qualified flags, no-framework neutral rows, selected-framework mismatch, and missing snapshot hash.",
        "g12_acceptance_criteria": "G12 must confirm framework source was pre-path, deterministic, framework-neutral, and compatible with accepted G12/G0 dispatch boundaries.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
    },
    {
        "capture_group": "future_orderflow_depth_proxy_requirements",
        "required_fields": [
            "proxy_instrument",
            "proxy_contract_month",
            "source_family_scid_depth_mbo_mbp_other",
            "source_file_pointer_or_vendor_cache_id",
            "proxy_mapping_version",
            "publication_or_capture_asof_utc",
            "derived_feature_schema_version",
            "orderflow_proxy_availability_status",
        ],
        "source_contract": "orderflow_depth_proxy_context_capture",
        "runtime_source_surfaces": [
            "sierra_proxy_registry_status.jsonl",
            "sierra_depth_feature_snapshots.jsonl",
            "databento_live_trigger_decisions.jsonl",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_orderflow_depth_proxy_context",
        "insertion_points": [
            "src/research_infra/sierra_proxy_registry.py::registry_entry",
            "src/research_infra/databento_forward_capture.py::build_databento_forward_request",
            "src/research_infra/forward_capture.py::build_scid_forward_source_capture_row",
        ],
        "source_asof_rule": "Only local/cache/source-control proxy context captured at or before candidate decision_asof_utc is eligible; unavailable depth is encoded as unavailable, not fetched.",
        "no_leak_rule": "No post-event depth, post-fill/order book, paid vendor pull, broker execution, or future path proxy can backfill this group.",
        "redaction_rule": "Emit source-family, version, cache pointer hash, and availability status; forbid raw depth blobs, vendor credentials, broker ids, account ids, order ids, and paid-call payloads.",
        "fail_closed_behavior": "If source pointer, as-of timestamp, mapping version, or feature schema version is absent or stale, parser rejects the group as unavailable/fail-closed.",
        "duplicate_policy": "One orderflow availability descriptor per candidate key and proxy mapping version; duplicate rows must match source hash and as-of.",
        "rollback_plan": "Disable the orderflow adapter branch while leaving other SCID capture groups intact; quarantine rows with raw depth/blob leakage.",
        "test_plan": "Fixtures cover source unavailable, stale publication as-of, forbidden raw blob field, and valid local cache pointer.",
        "g12_acceptance_criteria": "G12 must confirm zero API/vendor/broker calls, no raw blob retention, and explicit unavailable status where source context is absent.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
    },
    {
        "capture_group": "intended_entry_reference",
        "required_fields": [
            "entry_reference_type_market_limit_zone_midpoint_other",
            "entry_reference_price",
            "entry_reference_time_utc",
            "entry_source_timeframe",
            "entry_source_bar_hash_or_mso_snapshot_hash",
        ],
        "source_contract": "source_safe_strategy_decision_packet_logger",
        "runtime_source_surfaces": [
            "candidate_features_log.jsonl",
            "strategy_follow_candidates.jsonl",
            "prefill_delivery_path.jsonl",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_intended_entry_reference",
        "insertion_points": [
            "src/research_infra/forward_capture.py::record_live_candidate_forward_shadow",
            "src/components/orchestrator.py::_record_forward_capture_candidate_shadow",
        ],
        "source_asof_rule": "Entry reference price/type/timeframe must be emitted from the decision packet before fill, cancel, expiry, target, stop, or path review.",
        "no_leak_rule": "Do not substitute actual fill price, slippage, broker order ticket, realized entry quality, later candle high/low, or path hindsight.",
        "redaction_rule": "Keep intended reference and source snapshot hash only; block MT5 order tickets, pending tickets, deal ids, account ids, and slippage fields.",
        "fail_closed_behavior": "Missing entry price/type/timeframe/snapshot hash, stale as-of, or raw fill identifier causes parser rejection for this group.",
        "duplicate_policy": "The first accepted intended-entry packet freezes the candidate denominator key; replacements require a lifecycle event rather than in-place rewrite.",
        "rollback_plan": "Revert the additive entry-reference adapter and stop writing new SCID rows; invalid historical rows remain quarantined for audit.",
        "test_plan": "Fixtures cover market entry, limit-zone midpoint, missing source hash, fill-price substitution, and duplicate replacement handling.",
        "g12_acceptance_criteria": "G12 must verify intended-entry provenance is pre-fill and source-safe, with no broker or realized execution fields.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
    },
    {
        "capture_group": "intended_side_direction",
        "required_fields": [
            "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY",
            "side_source_component",
            "side_source_rule_or_model_hash",
            "side_emission_reason_code",
        ],
        "source_contract": "source_safe_strategy_decision_packet_logger",
        "runtime_source_surfaces": [
            "strategy_follow_candidates.jsonl",
            "strategy_follow_evaluations.jsonl",
            "candidate_features_log.jsonl",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_intended_side_direction",
        "insertion_points": [
            "src/research_infra/forward_capture.py::record_live_candidate_forward_shadow",
            "src/components/orchestrator.py::_record_forward_capture_candidate_shadow",
        ],
        "source_asof_rule": "Freeze LONG/SHORT/NEUTRAL/NO_STRATEGY side and reason code before target, stop, path, fill, or result horizon opens.",
        "no_leak_rule": "Do not infer side from realized trend, future labels, post-decision price movement, reviewer outcome, or result attribution.",
        "redaction_rule": "Emit side enum and source-rule/model hash only; never include raw prompt text, raw model response, broker account, order, deal, or position ids.",
        "fail_closed_behavior": "Invalid side enum, missing reason code, missing source hash, or post-decision timestamp causes fail-closed parser rejection.",
        "duplicate_policy": "One frozen side per candidate denominator key; lifecycle replacements must emit a new event state and preserve previous row immutability.",
        "rollback_plan": "Disable or revert the side adapter in the forward-capture writer; restart orchestrators only after owner-approved implementation rollback.",
        "test_plan": "Fixtures cover all side enums, missing reason, invalid enum, post-decision as-of, and duplicate side drift.",
        "g12_acceptance_criteria": "G12 must confirm side is emitted before path/result and has no dependence on future labels or broker execution state.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
    },
    {
        "capture_group": "intended_stop_reference",
        "required_fields": [
            "stop_reference_price",
            "stop_reference_type",
            "stop_buffer_rule_id",
            "stop_source_structure_id",
            "stop_source_snapshot_hash",
        ],
        "source_contract": "source_safe_strategy_decision_packet_logger",
        "runtime_source_surfaces": [
            "candidate_features_log.jsonl",
            "strategy_follow_candidates.jsonl",
            "prefill_delivery_path.jsonl",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_intended_stop_reference",
        "insertion_points": [
            "src/research_infra/forward_capture.py::record_live_candidate_forward_shadow",
            "src/components/orchestrator.py::_record_forward_capture_candidate_shadow",
        ],
        "source_asof_rule": "Stop reference and buffer rule are frozen at strategy decision time before path review or any terminal state.",
        "no_leak_rule": "Do not refit stop from later adverse excursion, broker close, target/stop outcome, trailing stop behavior, or reviewer judgment.",
        "redaction_rule": "Emit intended stop structure id, rule id, and snapshot hash; block broker close tickets, realized loss/R, account ids, and order/deal ids.",
        "fail_closed_behavior": "Missing stop price/type/rule/source hash, impossible price, stale as-of, or result-derived stop source causes parser rejection.",
        "duplicate_policy": "Same candidate key must retain the same frozen stop unless a separate lifecycle replacement event is recorded.",
        "rollback_plan": "Revert the stop adapter; use existing forward-capture flags to stop writes, then G12-review any quarantined invalid stop rows.",
        "test_plan": "Fixtures cover valid OB/FVG/breaker stop sources, missing source hash, result-fitted stop, and duplicate drift.",
        "g12_acceptance_criteria": "G12 must verify no stop field is derived from realized path or broker close evidence.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
    },
    {
        "capture_group": "intended_target_reference",
        "required_fields": [
            "target_reference_price",
            "target_reference_type",
            "target_rule_id",
            "risk_reward_reference",
            "target_source_snapshot_hash",
        ],
        "source_contract": "source_safe_strategy_decision_packet_logger",
        "runtime_source_surfaces": [
            "candidate_features_log.jsonl",
            "strategy_follow_candidates.jsonl",
            "prefill_delivery_path.jsonl",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_intended_target_reference",
        "insertion_points": [
            "src/research_infra/forward_capture.py::record_live_candidate_forward_shadow",
            "src/components/orchestrator.py::_record_forward_capture_candidate_shadow",
        ],
        "source_asof_rule": "Target reference, target rule, and RR reference are emitted and frozen before fill, path review, or terminal status.",
        "no_leak_rule": "Neutral horizons are not strategy targets; no later high/low, target hit, stop hit, realized R, PnL, or performance outcome may define target fields.",
        "redaction_rule": "Emit intended target metadata and source snapshot hash only; block broker tickets, deal ids, result labels, and performance metrics.",
        "fail_closed_behavior": "Missing target price/type/rule/source hash, result-derived target, or stale as-of causes parser rejection.",
        "duplicate_policy": "Target packet is immutable per candidate denominator key; replacement can only occur through explicit lifecycle state event.",
        "rollback_plan": "Revert the target adapter and quarantine any row that includes result/performance fields.",
        "test_plan": "Fixtures cover valid RR target, neutral no-strategy target absence, result-derived target rejection, and duplicate target drift.",
        "g12_acceptance_criteria": "G12 must confirm target semantics are intended-source only and do not open outcome review.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
    },
    {
        "capture_group": "lifecycle_fill_cancel_expiry_source_status",
        "required_fields": [
            "pending_intent_id",
            "source_event_type_created_updated_expired_cancelled_replaced_no_order",
            "source_event_utc",
            "source_event_clock_basis",
            "intent_state_before",
            "intent_state_after",
            "redacted_order_bridge_hash_optional",
        ],
        "source_contract": "nonbroker_pending_intent_lifecycle_event_logger",
        "runtime_source_surfaces": [
            "pending_limit_lifecycle.jsonl",
            "strategy_follow_candidates.jsonl",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_lifecycle_source_status",
        "insertion_points": [
            "src/components/pending_limit_lifecycle_logger.py::record_pending_limit_lifecycle",
            "src/research_infra/forward_capture.py::record_scid_forward_capture_lifecycle_event",
        ],
        "source_asof_rule": "Append-only intent lifecycle state is eligible only from GTOS internal intent events as of event time; broker history is not a source.",
        "no_leak_rule": "Do not include broker account/order/deal/position/history ids, fill price, slippage, realized R, synthetic path R, PnL, or target/stop result labels.",
        "redaction_rule": "Map pending/order/ticket fields to forbidden or salted optional bridge hash only after owner approval; default raw ids are rejected.",
        "fail_closed_behavior": "Any raw pending_ticket, mt5_order_ticket, trade_state_ticket, actual_r, synthetic_path_r, slippage_price, broker_fill_state, or account id fails closed.",
        "duplicate_policy": "Lifecycle rows are append-only by event time and intent id; they reference but never mutate the frozen candidate denominator row.",
        "rollback_plan": "Disable lifecycle adapter independently; leave existing pending_limit_lifecycle logger untouched and quarantine SCID lifecycle rows if redaction fails.",
        "test_plan": "Fixtures cover created/no_order/expired/cancelled/replaced states plus forbidden ticket, realized R, and slippage leakage.",
        "g12_acceptance_criteria": "G12 must verify status-only lifecycle capture, no broker identifiers, and no result/performance leakage.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_002_ORCHESTRATOR_AND_LIFECYCLE_WIRING_2026-05-12.patch.md",
    },
    {
        "capture_group": "lower_timeframe_asof_path_availability",
        "required_fields": [
            "ltf_timeframes_available",
            "ltf_source_file_pointer_or_cache_id",
            "ltf_source_hash",
            "decision_minus_window_start_utc",
            "bars_present_by_timeframe",
            "asof_path_descriptor_version",
            "ltf_availability_status",
        ],
        "source_contract": "ltf_source_availability_and_path_descriptor_capture",
        "runtime_source_surfaces": [
            "candidate_ltf_path_order.jsonl",
            "prefill_delivery_path.jsonl",
            "strategy_follow_candidates.jsonl",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_ltf_asof_path_availability",
        "insertion_points": [
            "src/research_infra/candidate_path_contract.py::build_candidate_path_contract_row",
            "src/research_infra/prefill_delivery_path_audit.py::build_prefill_delivery_path_audit_rows",
            "src/research_infra/forward_capture.py::build_scid_forward_source_capture_row",
        ],
        "source_asof_rule": "Only bars or ticks with timestamps <= decision_asof_utc may be summarized; future path descriptors must be unavailable/fail-closed.",
        "no_leak_rule": "No target/stop hit, fill outcome, post-decision high/low, path result, or realized label may be encoded in availability fields.",
        "redaction_rule": "Emit cache/source pointer hashes and bar-count descriptors only; block raw tick blobs, broker ids, account ids, order ids, and result metrics.",
        "fail_closed_behavior": "Missing source hash, stale bar range, post-decision timestamp, or future-path descriptor triggers fail-closed unavailable status.",
        "duplicate_policy": "Availability descriptor is stable per candidate key, timeframe set, source hash, and descriptor version.",
        "rollback_plan": "Disable the LTF adapter branch and keep existing candidate_ltf_path_order/prefill logs unchanged.",
        "test_plan": "Fixtures cover valid as-of availability, missing cache, stale source hash, and post-decision bar inclusion.",
        "g12_acceptance_criteria": "G12 must verify all LTF references are as-of and availability-only, not outcome/path scoring.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
    },
    {
        "capture_group": "poi_type_bounds_source",
        "required_fields": [
            "poi_type_enum_ob_fvg_breaker_swing_other_none",
            "poi_lower_bound",
            "poi_upper_bound",
            "poi_source_timeframe",
            "poi_source_bar_ids",
            "mso_snapshot_hash",
            "poi_detection_rule_version",
        ],
        "source_contract": "source_safe_mso_snapshot_and_poi_logger",
        "runtime_source_surfaces": [
            "strategy_follow_evaluations.jsonl",
            "candidate_features_log.jsonl",
            "trade_capture.py decision packet surface",
        ],
        "future_capture_owner": "src/research_infra/forward_capture.py::build_scid_poi_type_bounds_source",
        "insertion_points": [
            "src/research_infra/forward_capture.py::record_live_mso_forward_shadow",
            "src/components/orchestrator.py::_record_forward_capture_evaluation_shadow",
        ],
        "source_asof_rule": "POI type, bounds, source timeframe/bar ids, and MSO snapshot hash must come from the market-state snapshot before candidate path/result review.",
        "no_leak_rule": "Do not reconstruct POI from later price path, fill result, target/stop event, reviewer outcome, or performance label.",
        "redaction_rule": "Emit bounded POI metadata and snapshot hashes; block raw prompt/model transcript, broker identifiers, account/order/deal/position ids, and result metrics.",
        "fail_closed_behavior": "Invalid POI enum, missing bounds for non-none POI, missing MSO snapshot hash, or post-decision reconstruction fails closed.",
        "duplicate_policy": "POI snapshot hash and bounds are immutable per candidate denominator key unless a new evaluation row is emitted before candidate decision.",
        "rollback_plan": "Disable POI adapter independently and quarantine any rows with missing snapshot provenance.",
        "test_plan": "Fixtures cover OB/FVG/breaker/swing/none POI, missing bounds, invalid enum, and reconstructed-after-path rejection.",
        "g12_acceptance_criteria": "G12 must confirm POI provenance is source-safe MSO state and no path/result data influenced bounds.",
        "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
    },
]


PROPOSED_PATCHES: dict[str, str] = {
    "PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md": """# Proposed Patch 001 - Research Infra Adapter

PROPOSED ONLY - DO NOT APPLY IN THIS ROUTE
NO_PRODUCTION_EDIT_IN_THIS_ROUTE

Owner-approved future file scope:
- `src/research_infra/forward_capture.py`

Purpose:
- Add `SCID_FORWARD_SOURCE_CAPTURE_PATH = shadow_logs/scid_forward_source_capture.jsonl`.
- Add `SCID_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION = scid_forward_source_capture_v1`.
- Add immutable `SCID_CAPTURE_GROUPS` with the ten accepted G12 group names.
- Add builder adapters:
  - `build_scid_intended_side_direction`
  - `build_scid_intended_entry_reference`
  - `build_scid_intended_stop_reference`
  - `build_scid_intended_target_reference`
  - `build_scid_poi_type_bounds_source`
  - `build_scid_framework_setup_family`
  - `build_scid_lifecycle_source_status`
  - `build_scid_ltf_asof_path_availability`
  - `build_scid_orderflow_depth_proxy_context`
  - `build_scid_baseline_control_fields`
- Add `build_scid_forward_source_capture_row`, `validate_scid_forward_source_capture_row`, and `record_scid_forward_capture_group`.

Required behavior:
- Runtime writer is fail-open for trading behavior but emits no accepted row unless parser validation passes.
- Parser validation is fail-closed for missing required fields, stale as-of, forbidden identifiers, bad enums, duplicate-key drift, source-hash absence, and unsafe flags.
- Redaction blocks raw broker account/order/deal/position/history/ticket identifiers, realized R, PnL, win/loss, expectancy, slippage, and result labels.
- LTF and orderflow groups encode unavailable status when source is absent; they must not fetch data or open API/vendor/broker calls.

Acceptance tests to add in proposed Patch 003:
- Valid synthetic row for every capture group.
- One fail-closed fixture per accepted missing-field family.
- Forbidden broker identifier and forbidden result metric fixtures.
- Duplicate denominator key drift fixture.
- Stale as-of fixture.
""",
    "PROPOSED_PATCH_002_ORCHESTRATOR_AND_LIFECYCLE_WIRING_2026-05-12.patch.md": """# Proposed Patch 002 - Orchestrator And Lifecycle Wiring

PROPOSED ONLY - DO NOT APPLY IN THIS ROUTE
NO_PRODUCTION_EDIT_IN_THIS_ROUTE

Owner-approved future file scope:
- `src/components/orchestrator.py`
- `src/components/pending_limit_lifecycle_logger.py`

Purpose:
- Add additive calls from `_record_forward_capture_candidate_shadow` and `_record_forward_capture_evaluation_shadow` to the SCID source-capture adapter.
- Add status-only lifecycle bridge from `record_pending_limit_lifecycle` to the SCID adapter.

Hard boundaries:
- No trading decision reads the new SCID writer return value.
- No prompt, model, risk, safety, selector, canary, execution, order placement, or config behavior changes.
- Existing shadow loggers remain the source of truth; SCID capture is additive.
- If SCID writer raises, catch/log and preserve existing pipeline behavior.

Lifecycle redaction:
- `pending_ticket`, `mt5_order_ticket`, `trade_state_ticket`, account ids, deal ids, order ids, and position ids are forbidden in SCID rows.
- `actual_r`, `synthetic_path_r`, `slippage_price`, `broker_fill_state`, win/loss, PnL, expectancy, and terminal result labels are forbidden.
- Optional `redacted_order_bridge_hash_optional` is disabled by default; it requires explicit owner approval and G12 review before use.

Restart policy for future approved implementation:
- Merge only after G12 accepts this design and focused tests pass.
- Restart all affected orchestrators after the additive patch is merged.
- First monitoring pass checks schema version, group coverage, redaction, fail-closed unavailable statuses, and no decision-path diffs.
""",
    "PROPOSED_PATCH_003_TESTS_AND_VERIFIERS_2026-05-12.patch.md": """# Proposed Patch 003 - Runtime Tests And Verifiers

PROPOSED ONLY - DO NOT APPLY IN THIS ROUTE
NO_PRODUCTION_EDIT_IN_THIS_ROUTE

Owner-approved future file scope:
- `tests/test_scid_forward_capture_runtime_adapter.py`
- `tests/test_scid_forward_capture_lifecycle_redaction.py`
- `scripts/verify_scid_forward_capture_schema.py`

Purpose:
- Add runtime-adapter unit tests for all ten G12-accepted capture groups.
- Add lifecycle redaction tests that prove existing pending lifecycle fields cannot leak broker ids or result metrics into SCID rows.
- Add a standalone verifier for produced `shadow_logs/scid_forward_source_capture.jsonl` after future owner-approved rollout.

Minimum tests:
- Exactly ten capture groups and exact schema version `scid_forward_source_capture_v1`.
- Valid synthetic row per group.
- Missing required field per group fails closed.
- Forbidden broker id and forbidden result/performance fields fail closed.
- Duplicate candidate id with changed denominator key fails closed.
- LTF stale-as-of and orderflow unavailable-source fixtures fail closed.
- Writer failure does not alter orchestrator decision behavior.

Future rollout verifier:
- Reads only SCID shadow rows and source manifests.
- Confirms no prompt/config/risk/execution/canary/selector files changed.
- Confirms row counts are coverage evidence only, not validation or performance evidence.
""",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def with_common(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "safe_flags": SAFE_FLAGS,
        **payload,
    }


def json_name(stem: str) -> str:
    return f"SCID_FC_IMPL_DESIGN_{stem}_{DATE}.json"


def md_name(stem: str) -> str:
    return f"SCID_FC_IMPL_DESIGN_{stem}_{DATE}.md"


def render_group_markdown(groups: list[dict[str, Any]]) -> str:
    lines = [
        "# SCID FC Implementation Design Capture Group Ledger",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Evidence class: `{EVIDENCE_CLASS}`",
        f"Candidate boundary: `{CANDIDATE_ROWS_EXPECTED}` source candidates; coverage only, not validation.",
        "",
    ]
    for row in groups:
        lines.extend(
            [
                f"## {row['capture_group']}",
                f"- Source contract: `{row['source_contract']}`",
                f"- Future capture owner: `{row['future_capture_owner']}`",
                f"- Required fields: `{', '.join(row['required_fields'])}`",
                f"- Runtime source surfaces: `{', '.join(row['runtime_source_surfaces'])}`",
                f"- Insertion points: `{', '.join(row['insertion_points'])}`",
                f"- Source/as-of rule: {row['source_asof_rule']}",
                f"- No-leak rule: {row['no_leak_rule']}",
                f"- Redaction rule: {row['redaction_rule']}",
                f"- Fail-closed behavior: {row['fail_closed_behavior']}",
                f"- Duplicate policy: {row['duplicate_policy']}",
                f"- Rollback plan: {row['rollback_plan']}",
                f"- Test plan: {row['test_plan']}",
                f"- G12 acceptance criteria: {row['g12_acceptance_criteria']}",
                f"- Proposed patch artifact: `{row['proposed_patch_artifact']}`",
                "",
            ]
        )
    return "\n".join(lines)


def render_json_as_md(title: str, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Route: `{ROUTE_ID}`",
            f"Evidence class: `{EVIDENCE_CLASS}`",
            "",
            "```json",
            stable_json(payload).rstrip(),
            "```",
        ]
    )


def build_payloads() -> dict[str, dict[str, Any]]:
    group_names = [row["capture_group"] for row in CAPTURE_GROUPS]
    context_anchor = with_common(
        {
            "artifact_type": "context_anchor",
            "terminal_boundary": "DESIGN_ONLY_NO_LIVE_WIRING",
            "accepted_candidate_boundary": CANDIDATE_ROWS_EXPECTED,
            "accepted_capture_groups": group_names,
            "control_inputs": CONTROL_INPUTS,
            "preserved_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe_false": True,
                "outcome_review_opened_false": True,
                "live_effect_false": True,
            },
            "non_goals": [
                "No production code changes in this route",
                "No live logger wiring in this route",
                "No validation, outcome review, scoring, R, win rate, expectancy, or promotion verdict",
                "No broker/account/API/paid-vendor/raw-blob evidence opening",
            ],
        }
    )

    reconciliation = with_common(
        {
            "artifact_type": "g12_g0_reconciliation",
            "g12_terminal_decision": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
            "g0_terminal_decision": "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_WITH_RANKED_IMPLEMENTATION_ROUTE_BUNDLE",
            "selected_g0_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
            "live_wiring_ready": False,
            "candidate_boundary_reconciled": CANDIDATE_ROWS_EXPECTED,
            "capture_group_reconciled_count": len(group_names),
            "capture_group_reconciled_names": group_names,
            "manifest_repair_policy_preserved": [
                "G12 prompt hash rebound is accepted",
                "Builder output-manifest self-hash is nonblocking",
                "All other hash mismatches remain strict",
            ],
            "no_live_effect_reason": "This package emits only design ledgers, proposed patch artifacts, a verifier, and route-local tests.",
        }
    )

    insertion_ledger = with_common(
        {
            "artifact_type": "source_logger_insertion_proposal_ledger",
            "proposal_status": "PROPOSED_ONLY_OWNER_GATED",
            "future_file_ownership": [
                {
                    "path": "src/research_infra/forward_capture.py",
                    "ownership": "SCID adapter builders, validator, redaction policy, writer path, schema constants",
                    "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_001_RESEARCH_INFRA_ADAPTER_2026-05-12.patch.md",
                    "no_live_assertion": "No edit in this route; future writer is additive and fail-open for trading behavior.",
                },
                {
                    "path": "src/components/orchestrator.py",
                    "ownership": "Future owner-approved additive calls from existing forward-capture shadow hooks",
                    "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_002_ORCHESTRATOR_AND_LIFECYCLE_WIRING_2026-05-12.patch.md",
                    "no_live_assertion": "No edit in this route; future calls cannot feed trading decisions.",
                },
                {
                    "path": "src/components/pending_limit_lifecycle_logger.py",
                    "ownership": "Future owner-approved status-only lifecycle bridge with strict redaction",
                    "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_002_ORCHESTRATOR_AND_LIFECYCLE_WIRING_2026-05-12.patch.md",
                    "no_live_assertion": "No edit in this route; existing lifecycle logger remains unchanged.",
                },
                {
                    "path": "tests/test_scid_forward_capture_runtime_adapter.py",
                    "ownership": "Future runtime adapter tests",
                    "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_003_TESTS_AND_VERIFIERS_2026-05-12.patch.md",
                    "no_live_assertion": "No root tests are edited in this route; route-local focused tests cover this package only.",
                },
                {
                    "path": "scripts/verify_scid_forward_capture_schema.py",
                    "ownership": "Future rollout verifier after owner-approved live capture wiring",
                    "proposed_patch_artifact": "proposed_patches/PROPOSED_PATCH_003_TESTS_AND_VERIFIERS_2026-05-12.patch.md",
                    "no_live_assertion": "No scripts are edited in this route.",
                },
            ],
            "existing_surfaces_inspected_read_only": [
                "src/research_infra/forward_capture.py",
                "src/components/orchestrator.py",
                "src/components/pending_limit_lifecycle_logger.py",
                "src/components/candidate_features_logger.py",
                "src/components/trade_capture.py",
                "src/components/slippage_shadow_logger.py",
                "src/research_infra/candidate_path_contract.py",
                "src/research_infra/prefill_delivery_path_audit.py",
                "src/research_infra/sierra_proxy_registry.py",
                "src/research_infra/databento_forward_capture.py",
            ],
        }
    )

    patch_plan = with_common(
        {
            "artifact_type": "proposed_patch_plan",
            "proposal_status": "DESIGN_ONLY_NOT_APPLIED",
            "patch_artifacts": [
                {
                    "artifact": name,
                    "path": f"proposed_patches/{name}",
                    "applies_now": False,
                    "requires_owner_approval": True,
                    "requires_g12_review_before_apply": True,
                }
                for name in PROPOSED_PATCHES
            ],
            "function_contracts": [
                "build_scid_forward_source_capture_row(candidate_packet, group_context) -> dict",
                "validate_scid_forward_source_capture_row(row, duplicate_key_registry=None) -> ValidationResult",
                "record_scid_forward_capture_group(row, *, path=SCID_FORWARD_SOURCE_CAPTURE_PATH) -> bool",
                "record_scid_forward_capture_lifecycle_event(lifecycle_event, candidate_context) -> bool",
            ],
            "no_live_assertions": [
                "This route makes no production code changes.",
                "Future runtime writer must be additive and fail-open for trading behavior.",
                "Future parser/validator must be fail-closed for accepted research rows.",
                "Future rollout cannot change prompt/config/risk/safety/execution/canary/selector behavior.",
            ],
        }
    )

    redaction_plan = with_common(
        {
            "artifact_type": "redaction_failclosed_asof_duplicate_rollback_test_plan",
            "forbidden_fields": [
                "account",
                "account_id",
                "login",
                "order_id",
                "deal_id",
                "position_id",
                "ticket",
                "pending_ticket",
                "mt5_order_ticket",
                "trade_state_ticket",
                "broker_fill_state",
                "actual_r",
                "synthetic_path_r",
                "slippage_price",
                "pnl",
                "win_loss",
                "expectancy",
                "target_hit",
                "stop_hit",
            ],
            "fail_closed_triggers": [
                "missing required group field",
                "invalid enum",
                "stale or post-decision as-of timestamp",
                "source hash absent for required source-backed fields",
                "forbidden broker/account/order/deal/position/ticket identifier",
                "forbidden result/performance metric",
                "duplicate candidate id with changed denominator key",
                "raw orderflow/depth/blob payload",
            ],
            "runtime_vs_parser_policy": {
                "runtime_writer": "fail-open for trading behavior, log/quarantine invalid SCID row",
                "research_parser": "fail-closed; invalid rows are not accepted as SCID source evidence",
            },
            "rollback": [
                "Disable future SCID writer through existing forward-capture logger gate or scoped revert",
                "Restart affected orchestrators only after owner approval",
                "Do not delete historical rows; quarantine invalid schema outputs for G12 audit",
                "Run proposed rollout verifier before reopening any capture stream",
            ],
            "test_matrix": [
                "valid synthetic row per group",
                "missing required field per group",
                "forbidden broker identifier",
                "forbidden result/performance metric",
                "stale as-of timestamp",
                "duplicate denominator drift",
                "LTF unavailable source",
                "orderflow unavailable local/cache source",
            ],
        }
    )

    owner_gate = with_common(
        {
            "artifact_type": "owner_approval_restart_rollback_gate_dossier",
            "gates": [
                {
                    "gate": "G12_DESIGN_AUDIT",
                    "required_before": "Any production patch is applied",
                    "pass_condition": "G12 accepts this design package as control evidence only with no live/result boundary breach.",
                },
                {
                    "gate": "OWNER_APPROVAL_TO_EDIT_RUNTIME",
                    "required_before": "Any edit to src/, tests/, or scripts/ outside this research route",
                    "pass_condition": "Owner explicitly approves additive SCID capture wiring and restart window.",
                },
                {
                    "gate": "FOCUSED_TESTS",
                    "required_before": "Future merge",
                    "pass_condition": "Adapter, redaction, duplicate, as-of, unavailable-source, and no-decision-effect tests pass.",
                },
                {
                    "gate": "RESTART_POLICY",
                    "required_before": "Future live monitoring",
                    "pass_condition": "Affected orchestrators restarted after merge; first rows checked for schema/redaction/fail-closed status.",
                },
                {
                    "gate": "ROLLBACK_POLICY",
                    "required_before": "Future rollout",
                    "pass_condition": "Scoped revert or logger-disable path documented; historical rows quarantined, not deleted.",
                },
            ],
            "restart_now": False,
            "owner_approval_required_for_live_wiring": True,
            "monitoring_after_future_rollout": [
                "new shadow_logs/scid_forward_source_capture.jsonl exists",
                "schema_version equals scid_forward_source_capture_v1",
                "all ten groups appear only from source-safe contexts",
                "forbidden fields absent",
                "unavailable sources fail closed",
                "no trading decision-path output diffs",
            ],
        }
    )

    sequencing = with_common(
        {
            "artifact_type": "sequencing_ledger",
            "sequence": [
                {
                    "step": 1,
                    "name": "Design package",
                    "status": "THIS_ROUTE",
                    "allowed": True,
                    "description": "Emit implementation ledgers, proposed patch artifacts, verifier, focused tests, completion audit.",
                },
                {
                    "step": 2,
                    "name": "G12 audit of design",
                    "status": "NEXT_OWNER_OR_AUDIT_ROUTE",
                    "allowed": True,
                    "description": "Independent audit using emitted prompt/starter; still no live/result evidence.",
                },
                {
                    "step": 3,
                    "name": "Owner-approved implementation",
                    "status": "BLOCKED_UNTIL_OWNER_APPROVAL",
                    "allowed": False,
                    "description": "Apply additive runtime writer patch only after G12 and owner approval.",
                },
                {
                    "step": 4,
                    "name": "Restart and monitoring",
                    "status": "BLOCKED_UNTIL_IMPLEMENTATION",
                    "allowed": False,
                    "description": "Restart affected orchestrators and run rollout verifier.",
                },
                {
                    "step": 5,
                    "name": "G12 audit of captured rows",
                    "status": "BLOCKED_UNTIL_SOURCE_ROWS_EXIST",
                    "allowed": False,
                    "description": "Audit source/as-of/redaction/fail-closed evidence only; no outcome review.",
                },
                {
                    "step": 6,
                    "name": "Outcome validation design",
                    "status": "NOT_OPENED",
                    "allowed": False,
                    "description": "Requires separate approval after source capture acceptance; not part of this route.",
                },
            ],
        }
    )

    saturation = with_common(
        {
            "artifact_type": "saturation_self_redteam_ledger",
            "saturation_claim": "This is a bounded implementation design package, not a memo or open-ended loop.",
            "anti_boxing_checks": [
                {
                    "question": "Are all ten accepted capture groups mapped?",
                    "answer": "yes",
                    "evidence": "capture_group_ledger has exactly ten G12 names and required field lists",
                },
                {
                    "question": "Does every group include source/as-of/no-leak/redaction/fail-closed/duplicate/rollback/test/G12 criteria?",
                    "answer": "yes",
                    "evidence": "verifier enforces required keys per group",
                },
                {
                    "question": "Are later code changes represented as proposed patch artifacts?",
                    "answer": "yes",
                    "evidence": "three proposed patch artifacts cover adapter, orchestration/lifecycle wiring, and tests/verifiers",
                },
                {
                    "question": "Does this route alter live behavior?",
                    "answer": "no",
                    "evidence": "scope verifier rejects src/config/prompts/scripts/tests changes outside route",
                },
                {
                    "question": "Does this route open validation or outcome review?",
                    "answer": "no",
                    "evidence": "safe flags keep validation_safe=false and outcome_review_opened=false",
                },
            ],
            "residual_risks": [
                "Future lifecycle bridge must not expose existing pending lifecycle raw ticket/result fields.",
                "Future orderflow group must remain unavailable unless local/cache/source-control evidence exists as-of decision time.",
                "Future owner-approved patch still requires independent G12 audit before live wiring.",
            ],
        }
    )

    completion = with_common(
        {
            "artifact_type": "completion_audit",
            "can_mark_goal_complete": False,
            "completion_status": "PENDING_VERIFIER_AND_FOCUSED_TESTS",
            "required_artifacts_declared": True,
            "capture_groups_declared": len(CAPTURE_GROUPS),
            "candidate_boundary_preserved": CANDIDATE_ROWS_EXPECTED,
            "notes": "The standalone verifier rewrites this audit with observed pass/fail status.",
        }
    )

    closeout = with_common(
        {
            "artifact_type": "closeout_verification",
            "closeout_status": "PENDING_VERIFIER_AND_FOCUSED_TESTS",
            "no_production_changes_claimed": True,
            "restart_required_now": False,
            "owner_approval_required_before_runtime_wiring": True,
        }
    )

    return {
        "CONTEXT_ANCHOR": context_anchor,
        "G12_G0_RECONCILIATION": reconciliation,
        "CAPTURE_GROUP_LEDGER": with_common(
            {
                "artifact_type": "per_capture_group_implementation_design_ledger",
                "candidate_rows_expected": CANDIDATE_ROWS_EXPECTED,
                "capture_group_count": len(CAPTURE_GROUPS),
                "capture_groups": CAPTURE_GROUPS,
            }
        ),
        "INSERTION_POINT_LEDGER": insertion_ledger,
        "PROPOSED_PATCH_PLAN": patch_plan,
        "REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN": redaction_plan,
        "OWNER_APPROVAL_RESTART_ROLLBACK_GATE_DOSSIER": owner_gate,
        "SEQUENCING_LEDGER": sequencing,
        "SATURATION_SELF_REDTEAM_LEDGER": saturation,
        "COMPLETION_AUDIT": completion,
        "CLOSEOUT_VERIFICATION": closeout,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_g12_prompt() -> None:
    prompt = f"""# G12 Audit Prompt - SCID Forward Capture Implementation Design Package

You are auditing the route-local design package at:
`research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/`

Audit scope:
- Evidence class: `{EVIDENCE_CLASS}`.
- This is control evidence only. Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Do not open validation, result scoring, strategy edge review, R/PnL/win-rate/expectancy, broker/account/API/paid-vendor/raw-blob evidence, or live behavior changes.

Required checks:
1. Reconcile this design against the accepted G12 offline-schema audit and G0 synthesis route bundle.
2. Confirm the candidate boundary remains `{CANDIDATE_ROWS_EXPECTED}` source candidates and is coverage evidence only.
3. Confirm exactly the ten accepted capture groups are mapped: `{", ".join(row["capture_group"] for row in CAPTURE_GROUPS)}`.
4. For every group, verify source/as-of/no-leak/redaction/fail-closed/duplicate/rollback/test/G12 acceptance criteria.
5. Verify every future runtime code change is represented as a proposed patch artifact and is owner-gated.
6. Verify no production source/config/prompt/risk/execution/canary/selector changes were made by this route.
7. Verify lifecycle, LTF, and orderflow groups preserve fail-closed unavailable behavior and block broker/result/raw-blob leakage.
8. Emit ACCEPT or REJECT as G12 control evidence only, with exact blocker paths if rejected.
"""
    starter = (
        "Audit the SCID forward-capture implementation design package as G12 "
        "control evidence only; preserve NO_PROMOTION_VERDICT, validation_safe=false, "
        "outcome_review_opened=false, and live_effect=false."
    )
    write_text(ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_G12_AUDIT_PROMPT_{DATE}.md", prompt)
    write_text(ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_G12_AUDIT_STARTER_{DATE}.txt", starter)


def refresh_output_manifest(generated_by: str = "builder") -> dict[str, Any]:
    excluded = {
        f"SCID_FC_IMPL_DESIGN_OUTPUT_MANIFEST_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_OUTPUT_MANIFEST_{DATE}.md",
    }
    entries: list[dict[str, Any]] = []
    for path in sorted(ROUTE_DIR.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROUTE_DIR).as_posix()
        if path.name in excluded or "__pycache__" in path.parts:
            continue
        entries.append(
            {
                "path": rel,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    manifest = with_common(
        {
            "artifact_type": "output_manifest",
            "generated_by": generated_by,
            "manifest_self_hash_policy": "self_hash_excluded_nonblocking_per_upstream_manifest_repair_policy",
            "artifact_count_excluding_manifest": len(entries),
            "artifacts": entries,
        }
    )
    write_json(ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_OUTPUT_MANIFEST_{DATE}.json", manifest)
    write_text(
        ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_OUTPUT_MANIFEST_{DATE}.md",
        render_json_as_md("SCID FC Implementation Design Output Manifest", manifest),
    )
    return manifest


def build_package() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    PROPOSED_PATCH_DIR.mkdir(parents=True, exist_ok=True)

    for name, content in PROPOSED_PATCHES.items():
        write_text(PROPOSED_PATCH_DIR / name, content)

    payloads = build_payloads()
    for stem, payload in payloads.items():
        write_json(ROUTE_DIR / json_name(stem), payload)
        if stem == "CAPTURE_GROUP_LEDGER":
            md = render_group_markdown(payload["capture_groups"])
        else:
            md = render_json_as_md(stem.replace("_", " ").title(), payload)
        write_text(ROUTE_DIR / md_name(stem), md)

    write_g12_prompt()
    manifest = refresh_output_manifest("builder")
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "route_dir": str(ROUTE_DIR),
        "capture_group_count": len(CAPTURE_GROUPS),
        "candidate_rows_expected": CANDIDATE_ROWS_EXPECTED,
        "manifest_artifact_count": manifest["artifact_count_excluding_manifest"],
    }


if __name__ == "__main__":
    print(stable_json(build_package()).rstrip())
