# FVG/OB Geometry Capture Audit - 2026-05-12

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Finding

PASS. The commit captures exact FVG/OB geometry from decision-time MSO snapshots, appends recoverable geometry through a no-leak backfill, and updates the FVG/OB audit so bucket-specific exact geometry is accepted instead of collapsing everything to OB-only or requiring both bounds for single-family buckets.

## Source Capture Evidence

- `src/research_infra/forward_capture.py:561` defines `_match_order_block_from_decision_mso`.
- `src/research_infra/forward_capture.py:593` defines `_match_fvg_from_decision_mso`.
- `src/research_infra/forward_capture.py:632` defines `_fvg_ob_geometry_from_decision_mso`.
- `src/research_infra/forward_capture.py:684` emits `exact_geometry_source_status`.
- `src/research_infra/forward_capture.py:688` exposes `fvg_ob_geometry_from_candidate_row` for source/backfill use.
- `src/research_infra/forward_capture.py:1037` preserves geometry fields in `record_fvg_ob_confluence`.
- `src/research_infra/forward_capture.py:2459` computes geometry before forward shadow rows are written.
- `src/research_infra/forward_capture.py:2536` merges `**fvg_ob_geometry` into the confluence row.

## Backfill Evidence

- `scripts/backfill_fvg_ob_confluence_source_geometry.py:24` uses the shared evidence selector.
- `scripts/backfill_fvg_ob_confluence_source_geometry.py:27` imports the same geometry extractor from `forward_capture`.
- `scripts/backfill_fvg_ob_confluence_source_geometry.py:41` records the append-only manual backfill status.
- `scripts/backfill_fvg_ob_confluence_source_geometry.py:42` freezes the no-leak status as `DECISION_TIME_MSO_ONLY_NO_POST_OUTCOME_FIELDS`.
- `scripts/backfill_fvg_ob_confluence_source_geometry.py:112` and `:113` select latest candidate/confluence rows through `latest_by_candidate`.
- `scripts/backfill_fvg_ob_confluence_source_geometry.py:126` recovers geometry from the candidate row.
- `scripts/backfill_fvg_ob_confluence_source_geometry.py:142` to `:147` writes manual backfill status, no-leak status, `no_ai_calls`, `no_execution`, and paid-data false flags.
- `scripts/backfill_fvg_ob_confluence_source_geometry.py:178` writes JSON/Markdown reports.

The current regenerated backfill report shows `6` existing recovered geometry rows, split as `3` FVG exact bounds and `3` OB exact bounds, with `rows_appendable=0` and `rows_appended=0` after the already-applied append-only rows.

## Audit/Monitoring Wiring Evidence

- `src/research_infra/fvg_ob_confluence_audit.py:27` defines the accepted exact-source statuses.
- `src/research_infra/fvg_ob_confluence_audit.py:224` computes overall source-capture status by bucket.
- `src/research_infra/fvg_ob_confluence_audit.py:236` defines bucket-specific required fields.
- `src/research_infra/fvg_ob_confluence_audit.py:404` treats all exact-source statuses as accepted, not only combined FVG+OB.
- `src/research_infra/fvg_ob_confluence_audit.py:539` counts exact captured rows across FVG, OB, and combined statuses.
- `scripts/run_live_monitoring_maintenance.py:89` and `:138` wire the geometry backfill into final catchup and normal maintenance steps.
- `scripts/build_daily_monitoring_checklist.py:56` wires the backfill command into the daily checklist.
- `scripts/verify_shadow_log_integrity.py:3493` allows append-only geometry supersession only for the explicit no-leak manual recovery status.

## Test Evidence

- `tests/test_forward_capture_shadow_loggers.py:520` asserts OB bounds are captured from decision MSO.
- `tests/test_forward_capture_shadow_loggers.py:583` asserts FVG bounds are captured from decision MSO.
- `tests/test_fvg_ob_confluence_audit.py:168` and the new bucket-specific test around `:171` verify exact bounds are counted for single-family buckets.
- `tests/test_fvg_ob_confluence_source_geometry_backfill.py:66` verifies recovered FVG bounds are appended with manual status and `no_execution=true`.
- `tests/test_verify_shadow_log_integrity.py:1567` verifies the integrity checker allows append-only geometry supersession without duplicate-key failure.

## Boundary

This is source/control evidence only. It does not score FVG/OB performance, promote a route, call AI/API/paid data, mutate orders, or change live entry logic.
