# Append-Only Evidence Selection Audit - 2026-05-12

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Finding

PASS. The commit adds a shared evidence selector that prefers recovered/source-rich rows over later source-blocked placeholders, then routes the changed append-only audit/readout modules through it.

## Selector Evidence

- `src/research_infra/evidence_selection.py:44` defines `evidence_quality`.
- `src/research_infra/evidence_selection.py:61` classifies `SOURCE_BLOCKED`, `ltf_source_blocked`, and `outside_max_hours` rows as blocked.
- `src/research_infra/evidence_selection.py:68` identifies `M1_PATH_RECOVERED` rows.
- `src/research_infra/evidence_selection.py:90` returns quality `0` for blocked rows.
- `src/research_infra/evidence_selection.py:92` returns quality `2` for recovered LTF, path-order, cluster, or terminal evidence.
- `src/research_infra/evidence_selection.py:96` ranks quality before clocks and line number.
- `src/research_infra/evidence_selection.py:100` exposes `latest_by_candidate` with `date_prefix` and `key_field`.

## Adoption Evidence

The changed modules/scripts below import and use the shared selector:

- `src/research_infra/fvg_ob_confluence_audit.py:18`, `:95`
- `src/research_infra/continuation_no_retrace.py:17`, `:70`
- `src/research_infra/k55_ml_shadow.py:20`, `:107`
- `src/research_infra/live_shadow_gap_closure.py:35`, `:207`
- `src/research_infra/m15_choch_diagnostics.py:16`, `:154`
- `src/research_infra/opportunity_lifecycle_audit.py:16`, `:67`
- `src/research_infra/pending_limit_lifecycle_audit.py:18`, `:190`
- `src/research_infra/prefill_delivery_path_audit.py:18`, `:75`
- `src/research_infra/v2_structural_selector_readiness.py:18`, `:85`
- `src/research_infra/v2b_forward_pair_resolution_audit.py:18`, `:96`
- `src/research_infra/xagusd_fresh_ob_late_ny.py:16`, `:119`
- `scripts/audit_live_shadow_data_health.py:31`, `:264`
- `scripts/backfill_candidate_path_contract_audit.py:26`, `:49`
- `scripts/summarize_live_shadow_opportunities.py:23`, `:98`
- `src/research_infra/missed_fill_opportunity_study.py:17`, `:67`

`src/research_infra/decision_layer_diagnostics_join.py` did not have a selector replacement; its target change is framework-aware nearest diagnostic matching.

## Test Evidence

- `tests/test_live_shadow_gap_closure.py:120` proves recovered LTF evidence outranks a later blocked placeholder.
- `tests/test_opportunity_lifecycle_audit.py:167` proves opportunity lifecycle uses recovered LTF over a later blocked placeholder.
- `tests/test_opportunity_lifecycle_audit.py:193` proves recovered cluster rows beat blocked cluster placeholders.
- `tests/test_missed_fill_opportunity_study.py:136` proves the missed-fill study keeps recovered evidence over a later blocked row.
- `tests/test_verify_shadow_log_integrity.py:1567` proves append-only geometry recovery does not trip duplicate unique-key failures.

## Boundary

The selector changes evidence choice for research/monitoring ledgers. It does not alter order entry, position sizing, AI decisions, safety gates, production selectors, or execution behavior.
