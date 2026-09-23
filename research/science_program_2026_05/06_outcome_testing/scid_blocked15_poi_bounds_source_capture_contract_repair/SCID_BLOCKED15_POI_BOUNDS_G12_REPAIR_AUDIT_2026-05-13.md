# G12 Blocked15 POI Bounds Repair Audit

Terminal decision: `ACCEPT_AS_G12_SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_CONTROL_EVIDENCE_ONLY`

This audit stays in `G12_SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_AUDIT_ONLY`. It does not open validation, result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid vendor access, broker account/order/history/deal/position evidence, raw market blobs, live restarts, live behavior, or trading/risk/safety/prompt-decision surfaces.

Safe flags are preserved: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Mandatory preflight/context | Ran `python scripts/generate_live_state.py`; read `.context/LIVE_STATE.md`, latest handoff, quick reference, goal-session discipline, research doctrine, research current state, local heavy data inventory, reading order, `CLAUDE.md`, builder prompt, and controlling G12 prompt. | covered |
| Every repair artifact inspected | Package manifest reports `artifact_count=40`; JSON audit lists all manifest keys, including scripts and fixtures. | covered |
| Do not trust closeout claims | Independent verifier initially failed on fixture/hash/manifest mismatches. | covered |
| Same-class repair pursued | Patched the builder so the generated next-G12 prompt includes mandatory context and audit-posture hardening; rebuilt package and regenerated manifest hashes. | closed |
| Duplicate fixture stability | Builder truncates duplicate JSONL before writing; post-rebuild line count is `2`. | covered |
| Final verifier | `python ...verify_scid_blocked15_poi_bounds_source_capture_contract_repair_2026_05_13.py` returned `ok=true`, `issues=[]`. | covered |
| Focused tests | `python -m pytest ...test_scid_blocked15_poi_bounds_source_capture_contract_repair_2026_05_13.py -q` returned `5 passed in 0.29s`. | covered |
| Syntax check | `py_compile` still hits the local Windows `__pycache__` temp-file issue; AST fallback over builder/verifier/test returned `AST_OK 3`. | covered |
| Exact source logger contract | `SCID_BLOCKED15_POI_BOUNDS_SOURCE_LOGGER_CONTRACT_2026-05-13.json` has 46 field contracts, parser/as-of/hash/redaction/duplicate/fail-closed/G12 acceptance rules. | covered |
| MSO/source-bar schema | `SCID_BLOCKED15_POI_BOUNDS_MSO_SNAPSHOT_HASH_SOURCE_BAR_SCHEMA_2026-05-13.json` commits hashes and source pointers only; output manifest has `raw_market_blob_committed=false`. | covered |
| Broad POI support | `poi_mechanism_families_v2` includes OB, FVG, breaker, swing, liquidity, round-number, volume-profile, geometry, macro/calendar, other, and none. | covered |
| Synthetic fixture coverage | Fixture manifest has 10 fixtures and no false coverage flags. | covered |
| Target card fail-closed gates | Card ledger verifies exactly `ADV-005`, `BEH-002`, `BEH-003`, `BEH-005`, `GEO-001`; all remain `card_may_score_results_now=false` and `accepted_40_denominator_unblocked_now=false`. | covered |

## Repair Notes

The first verifier run found real local repair issues: `fixture_validation_failure` plus `manifest_hash_mismatch` for the focused test result, next-G12 prompt, builder script, verifier script, focused test script, and duplicate JSONL fixture. These were not terminal blockers because they were deterministic same-evidence-class hash/generator issues.

The repair patched `build_scid_blocked15_poi_bounds_source_capture_contract_repair_2026_05_13.py` so `make_next_g12_prompt()` regenerates the hardened G12 prompt from disk. Rebuilding the package refreshed the manifest hashes. The duplicate JSONL writer already truncates the duplicate fixture before writing, and the rebuilt fixture stayed at two rows.

## Remaining Requirements

No same-G12 repair blocker remains for this audit. The only future requirement is prospective capture: a future `source_safe_mso_snapshot_and_poi_logger` row must carry the exact source-hashed, as-of-safe, redacted POI/bounds fields and every card dependency must be candidate-attached by `candidate_input_row_id` and `duplicate_proxy_denominator_key` before G12 can consider denominator or result movement.
