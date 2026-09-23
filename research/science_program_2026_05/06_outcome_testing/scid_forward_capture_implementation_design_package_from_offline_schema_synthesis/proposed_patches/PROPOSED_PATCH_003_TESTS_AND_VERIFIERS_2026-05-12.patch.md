# Proposed Patch 003 - Runtime Tests And Verifiers

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
