# Proposed Patch 001 - Research Infra Adapter

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
