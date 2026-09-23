# vNext Replacement Stage 01 Evidence Reconciliation Report

Generated UTC: `2026-05-26T11:28:31.804894Z`
Route id: `vnext_moonshot_production_replacement_activation_2026_05_26`
Ledger: `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/VNEXT_REPLACEMENT_UPSTREAM_EVIDENCE_RECONCILIATION_LEDGER_2026-05-26.jsonl`

## Scope

This is the initial Stage 01 reconciliation index over the major upstream artifacts. It preserves source paths, hashes, counts, and full status distributions for parsed JSONL inputs. It does not replace row-bearing upstream ledgers and does not complete the full route by itself.

## Coverage

- Reconciliation rows written: `4494`
- Artifact inventory rows written: `4480`
- JSONL rows scanned for distributions: `24383`
- Row-bearing lines scanned for artifact inventory: `26274763`
- Missing row artifacts in this initial set: `0`

## Row Kind Counts

- `artifact_inventory`: `4480`
- `seed_reconciliation`: `14`

## Artifact Role Counts

- `audit`: `8`
- `builder`: `368`
- `candidate_origin_boxing_audit`: `1`
- `candidate_origin_registry`: `1`
- `config`: `1`
- `corrected_branch_prop_ev_summary`: `1`
- `csv_source_or_metric`: `5`
- `dynamic_policy_replay_summary`: `1`
- `final_conversion_freeze_report`: `1`
- `final_replay_decision_map_summary`: `1`
- `focused_test`: `70`
- `forensic_do_not_activate_report`: `1`
- `forward_capture_requirement_ledger`: `1`
- `full_denominator_candidate_generation_summary`: `1`
- `json_artifact`: `648`
- `manifest`: `304`
- `markdown_artifact`: `24`
- `master_intelligence_to_runtime_conversion_summary`: `1`
- `material_artifact`: `2`
- `question_stack_ledger`: `1`
- `repaired_forward_replay_metrics_summary`: `1`
- `report`: `21`
- `row_ledger_or_shard`: `2440`
- `runtime_integration_map`: `1`
- `source_mode_ltf_path_r_summary`: `1`
- `source_or_test_code`: `16`
- `summary`: `406`
- `verifier`: `167`

## Upstream Route Counts

- `gtos_vnext_research_to_runtime_builder`: `183`
- `runtime_config_test_shadow_surface`: `146`
- `vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26`: `193`
- `vnext_full_historical_candidate_generation_replay_2026_05_24`: `1320`
- `vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26`: `161`
- `vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25`: `82`
- `vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25`: `84`
- `weekend_mechanical_edge_factory_moonshot_2026_05_15`: `2325`

## Classification Counts

- `accepted_for_runtime`: `4407`
- `activation_config_applied`: `21`
- `ai_budget_required`: `21`
- `dynamic_valid`: `1559`
- `killed_redesigned_with_reason`: `88`
- `source_capture_required`: `2466`
- `static_proxy_comparator`: `1403`
- `superseded`: `183`

## First Incomplete Invariant

`stage_02_old_gtos_replacement_map_pending`: the Stage 01 high-level classification seed and full artifact inventory now exist. The next route-local action is to convert this inventory into the Stage 02 old-GTOS replacement map and legacy-surface retirement ledger while preserving row-bearing upstream artifacts by path/hash.

## Guardrails

- No arbitrary top-N was used; status distributions are full counters over the scanned JSONL files.
- Artifact inventory rows cover every material text/JSON/JSONL/CSV/GZip row-bearing artifact under the required upstream roots plus active runtime/config/test/shadow-log surfaces.
- Summaries are treated as pointers and classifiers, not evidence replacement.
- The failed production-change route is retained as a negative fixture for semantic verification.
- Source-missing and non-generatable historical truth remain source-capture or exclusion work, not activation permission.
