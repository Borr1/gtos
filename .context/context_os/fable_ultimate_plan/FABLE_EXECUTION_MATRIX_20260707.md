# Fable Execution Matrix - 2026-07-07

Generated UTC: 2026-07-07T05:18:00Z

Purpose: current execution control surface before any new replay. This matrix is
derived from the saved Fable implementation sequence, the Fable root-cause audit,
the 20260706 detailed matrix, `CURRENT_ROOT_CAUSE_MAP.json`, and the V144
post-replay proof artifacts. It does not replace the detailed 20260706 matrix; it
selects the next dependency batch from current disk evidence.

## Current V154 Checkpoint - Selected-Package Replay Source Materialization Propagation

Generated UTC: 2026-07-08T01:45:00Z.

This section supersedes V153 where it disagrees. Older sections remain
checkpoint evidence.

### Current Disk/Process State

- HEAD entering this checkpoint: `cc9666db7 Repair B7 lifecycle context attribution scope`.
- No broad replay was started for this checkpoint.
- Latest completed behavior proof remains
  `BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`.
- V154 parity artifacts were rebuilt for
  `V154_B7_SELECTED_PACKAGE_REPLAY_SOURCE_MATERIALIZATION_20260601_20260605_TARGETED`.
- Authority boundary remains unchanged: broker mutation false, live broker
  authority false, final selection false, local replay/package evaluation full.

### V154 Deterministic Artifact Evidence

- `ULTIMATE_CANDIDATE_PACKAGE_REPLAY_AUTHORITY_CANDIDATE_LEDGER.jsonl` now
  preserves explicit selected-package member-axis IDs and source-bound fields
  from package replay authority candidates. The two known recoverable target
  candidates now carry row-bound IDs:
  `broadorigin_82c9fd8b6cb32cbf876e45df` and
  `broadorigin_08dfd67007345cb70fea97fe`.
- `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` and
  `DENOMINATOR_NAMESPACE_REPAIR_LEDGER.jsonl`: `1101` rows each after rebuild.
  Exact join status counts are now:
  - `selected_package_replay_bridge_candidate_materialized_no_lifecycle_label_join`: `823`;
  - `context_labels_available_but_no_selected_package_replay_rows_in_lifecycle_window`: `168`;
  - `axis_candidate_namespace_materialized_no_lifecycle_label_context`: `69`;
  - `no_hydrated_selector_candidate_rows_for_member_axis`: `41`.
- Selected-package materialization binding status counts are now:
  - `explicit_and_heuristic_member_axis_binding`: `815`;
  - `explicit_candidate_member_axis_binding`: `20`;
  - no binding status: `278`.
- Source-count sums now include
  `ultimate_replay_authority_candidate_axis_materialization=30782`,
  `m15_grid_all_symbol_proxy_replay_bridge=14027`,
  `m15_grid_order_intent_proxy_replay_bridge=3093`,
  `pending_created_proxy_replay_bridge=1014`, and
  `selected_package_lifecycle_label_replay_bridge=236`.
- `SOURCE_BOUND_TO_EXECUTED_PARITY_V154_B7_SELECTED_PACKAGE_REPLAY_SOURCE_MATERIALIZATION_20260601_20260605_TARGETED_LEDGER.jsonl`:
  parity rows `5461`, source-member axis rows `1101`, and all `1101`
  source-member rows now carry `source_axis_row_index`.
- V154 moved two former V153 target axes:
  - `selected_package_lifecycle_context_without_current_replay_source_materialization`:
    `79 -> 78` axes, diagnostic source-bound R `95981.210142 -> 95979.710142`;
  - `selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap`:
    `21 -> 20` axes, diagnostic source-bound R `32776.039521 -> 32774.539521`.
- The two recovered axes were reclassified into:
  - `source_axis_selected_package_bridge_materialized_no_lifecycle_label_context`: `+1`;
  - `source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_source_window_missing_pending_created_proxy_only`: `+1`.
- Residual B7 materialization gap after V154: `98` former target axes remain,
  diagnostic source-bound R `128754.249663185`. They have zero stable-member-axis
  hits in the regenerated replay authority candidate ledger:
  - `78` rows remain
    `context_labels_available_but_no_selected_package_replay_rows_in_lifecycle_window`;
  - `20` rows remain
    `axis_candidate_namespace_materialized_no_lifecycle_label_context`;
  - lifecycle transfer status split: `61`
    `source_window_missing_pending_created_proxy_only`, `17`
    `bridge_window_missing`, and `20` `no_axis_lifecycle_context`.
- Focused proof:
  - `py_compile` passed for touched route/component modules.
  - `tests/test_ultimate_candidate_package.py -k replay_authority_selects_candidates_and_order_policy_without_live_authority`:
    `1 passed, 23 deselected`.
  - `tests/test_build_source_bound_execution_parity.py -k 'package_authority_materialization_uses_explicit_member_axis_ids or parity_reclassifies_missing_selected_package_source_statuses or selected_package_bridge_materialization_gets_source_only_label'`:
    `3 passed, 78 deselected`.
  - `tests/test_denominator_to_deployment_verifier.py -k selected_package_bridge_lifecycle_context_contract_scan`:
    `1 passed, 124 deselected`.
  - Route verifier exited `0`; `VERIFICATION_RESULT.json` reports `ok=true`,
    `issue_count=0`, `final_package_selected=false`, and
    `live_trading_enabled=false`.
  - Prompt hardening passed for `VPS_HANDOFF_PROMPT.md`.
  - Standard route artifact audit passed with `ok=true`,
    `missing_required=[]`, and `missing_warnings=[]`.

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | No V154 evidence reopens instrumentation; current matrix/root map remain route authority. | None. | Preserve. |
| B1 provenance truth contract | DONE | V154 preserves selected-package replay source identity and adds binding-status proof instead of relying on unconsumed helper fields. | None unless later patches reopen provenance drift. | Keep producer, consumer, ledger, and verifier paths green. |
| B2 fillability/reallocation truth chain | DONE | REFUSED/source-gap/unfillable execution authority is unchanged; V154 is materialization/proof only. | Reallocation value remains B7 transfer work. | Preserve non-executable authority. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | No sizing policy changed in V154. | Full-risk expression remains weak in B7 slices. | Reopen only when B7 risk-expression consumer changes. |
| B4 fill-simulation realism | DONE WITH LABEL | No fill simulation changed in V154. | Broader regime realism proof remains later B7 ladder work. | Reopen only on new fill-source truth regression. |
| B5 verifier/comparison precision | DONE | V154 extends the selected-package bridge lifecycle contract scan so package authority materialization source rows require explicit binding statuses. Focused verifier test and route verifier are green. | None for the V154 proof surface. | Keep precision scans green after upstream candidate/member-axis generation patches. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority remains active; cost-refused rows remain non-executable diagnostic/missed. | Large cost-failed opportunity remains scoreable but not executable without same-window calibration evidence. | Do not loosen REFUSED execution. |
| B7 full proof ladder | PARTIAL | V154 closes the downstream propagation leak: explicit member-axis/source-index evidence from replay authority candidates is now produced, consumed, proven in parity, and verifier-guarded. | `98` former target axes remain unmaterialized because their stable-member-axis IDs are absent from the regenerated replay authority candidate ledger. This is now an upstream candidate/member-axis generation or selected-package bridge producer gap, not a denominator materializer omission. B7.4 19-day and B7.5 extended history remain open. | Next same-root batch: candidate/member-axis generation parity for the `98` residual axes, especially scheduler-lifecycle merge sleeves with no replay-authority stable-member-axis hit. |
| B8 live path | OPEN | Fable B8 remains defined but ineligible while B7 is partial. | Production-return dossier, live-shadow, canary, and scale schedule remain blocked. | Broker/live/final stay false until B7 gates pass. |

### V154 Selected Next Same-Root Batch

Selected dependency after V154: B7 upstream candidate/member-axis generation
parity for the `98` residual selected-package materialization rows.

Patch requirements before any runtime replay:

- Trace why the residual stable member-axis IDs do not appear in
  `ULTIMATE_CANDIDATE_PACKAGE_REPLAY_AUTHORITY_CANDIDATE_LEDGER.jsonl` under
  `matched_stable_member_axis_ids`, `ultimate_package_matched_member_axis_ids`,
  or `selected_package_matched_member_axis_ids`.
- Repair the producer that should materialize those IDs if current source
  evidence exists. If no source evidence exists, preserve exact non-materialized
  source-gap labels with row-level source-axis indexes.
- Preserve V153/V154 truth boundaries: pair-broadcast lifecycle context remains
  diagnostic proxy context, not exact denominator authority.
- Expected behavior before runtime replay: neutral or reclassification until a
  runtime consumer intentionally admits newly materialized executable
  candidates. Use targeted producer proof before any broad replay.

## Current V153 Checkpoint - Pair-Broadcast Lifecycle Context Demoted

Generated UTC: 2026-07-07T18:15:23Z.

This section supersedes V151F where it disagrees. Older sections remain
checkpoint evidence.

### Current Disk/Process State

- HEAD entering this checkpoint: `39e289bf5 Repair B7 source-window transfer classification`.
- No broad replay, targeted replay, builder, verifier, audit, compile, or pytest
  process is running after verification.
- Latest completed behavior proof remains
  `BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`.
- V153 artifacts were rebuilt for
  `V153_B7_PAIR_BROADCAST_LIFECYCLE_CONTEXT_DEMOTION_20260601_20260605_TARGETED`.
- Authority boundary remains unchanged: broker mutation false, live broker
  authority false, final selection false, local replay/package evaluation full.

### V153 Deterministic Artifact Evidence

- `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` and
  `DENOMINATOR_NAMESPACE_REPAIR_LEDGER.jsonl`: `1101` rows each after rebuild.
  Transfer status counts are now:
  - `source_window_missing_pending_created_proxy_only`: `607`;
  - `no_axis_lifecycle_context`: `371`;
  - `bridge_window_mismatch`: `81`;
  - `bridge_window_missing`: `31`;
  - `bridge_window_overlap_denominator_authority_closed`: `11`.
- Lifecycle context attribution scope counts are now:
  - `symbol_side_pair_broadcast_only`: `695`;
  - `no_lifecycle_context`: `371`;
  - `bridge_window_label_context_without_denominator_authority`: `35`.
- Exact denominator authority remains closed for the selected-package lifecycle
  bridge surface: source-member parity rows show `exact_denominator_join_rows=0`
  for all `1101` source-member axes.
- V153 source-member leakage labels no longer include false
  `stable_window_lifecycle_label_context` or legacy exact
  `axis_lifecycle_label_context` strings. The former generic lifecycle-context
  bucket is now split as:
  - `source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_source_window_missing_pending_created_proxy_only`:
    `255` axes, diagnostic source-bound R `341455.380939`;
  - `source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_bridge_window_mismatch_same_trading_day_different_decision_window`:
    `29` axes, diagnostic source-bound R `104477.035877`;
  - `source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_bridge_window_mismatch_different_trading_day_decision_window`:
    `9` axes, diagnostic source-bound R `35437.331010`;
  - `source_axis_selected_package_bridge_materialized_window_lifecycle_label_context_denominator_authority_closed`:
    `28` axes, diagnostic source-bound R `54294.697558`.
- Other leading B7 buckets after V153 remain:
  - `candidate_generated_broker_cost_refused_not_executable`: `51` axes,
    diagnostic source-bound R `202258.382340`;
  - scheduler-not-selected classes:
    `64 + 7` axes, diagnostic source-bound R `193479.149317`;
  - `source_axis_selected_package_bridge_materialized_no_lifecycle_label_context`:
    `162` axes, diagnostic source-bound R `174696.612870`;
  - `selected_package_lifecycle_context_without_current_replay_source_materialization`:
    `79` axes, diagnostic source-bound R `95981.210142`;
  - `selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap`:
    `21` axes, diagnostic source-bound R `32776.039521`.
- Focused proof:
  - `py_compile` passed for the touched route modules.
  - `tests/test_build_source_bound_execution_parity.py -k 'denominator_builder_stabilizes_axis_lifecycle_context_ids or selected_package_bridge or repair_stage'`:
    `9 passed, 71 deselected`.
  - `tests/test_denominator_to_deployment_verifier.py -k 'selected_package_bridge_lifecycle_context_contract_scan'`:
    `1 passed, 124 deselected`.
  - Route verifier exited `0`; `VERIFICATION_RESULT.json` reports `ok=true`,
    `issue_count=0`, `final_package_selected=false`, and
    `live_trading_enabled=false`.
  - Prompt hardening audit passed.
  - Standard route artifact audit passed with `ok=true`,
    `missing_required=[]`, and `missing_warnings=[]`. A separate intentionally
    giant full-JSONL scan failed on a read timeout for an old ordered-path
    oracle ledger; it found no missing artifacts or parse errors and is not the
    checkpoint guardrail.
  - Scoped `git diff --check` passed.

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | No V153 evidence reopens instrumentation; existing provenance/cost/refusal histograms remain current for this route. | None. | Preserve. |
| B1 provenance truth contract | DONE | V153 preserves raw/effective action, selected-package denominator reason split, and now prevents pair-broadcast lifecycle context from masquerading as exact lineage. | None unless later patches reopen provenance drift. | Keep producer, consumer, ledger, and verifier paths green. |
| B2 fillability/reallocation truth chain | DONE | V153 does not loosen REFUSED/source-gap/unfillable execution authority; these rows remain scoreable/missed but non-executable. | Reallocation value remains B7 transfer work. | Preserve non-executable authority. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | No sizing policy changed in V153; risk provenance remains a B7 transfer/expression concern, not a B3 truth regression. | Full-risk expression remains weak in B7 slices. | Reopen only when B7 risk-expression consumer changes. |
| B4 fill-simulation realism | DONE WITH LABEL | No fill simulation changed in V153; V150 remains the latest bounded behavior proof. | Broader regime realism proof remains later B7 ladder work. | Reopen only on new fill-source truth regression. |
| B5 verifier/comparison precision | DONE | V153 adds verifier assertions for lifecycle context attribution scope and rejects bridge-window overlap without exact axis authority. Focused tests and route verifier are green. | None for this checkpoint. | Keep precision scans green after each B7 source-materialization patch. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority remains active; cost-refused rows remain non-executable diagnostic/missed. | Large cost-failed opportunity remains scoreable but not executable without same-window calibration evidence. | Do not loosen REFUSED execution. |
| B7 full proof ladder | PARTIAL | V153 closes the false exact-lifecycle transfer claim: pair-broadcast and bridge-window-label contexts are now separated from exact denominator authority, and all 1101 source-member axes have explicit transfer/scope classification. | B7 still has material source-transfer gaps: 79 selected-package lifecycle-context rows without current replay source materialization, 21 candidate-namespace materialized source-gap rows, 162 no-lifecycle-context rows, and scheduler/cost/risk reallocation buckets. B7.4 19-day and B7.5 extended history remain open. | Next same-root batch: selected-package replay source materialization for the 79 + 21 rows, then scheduler/reallocation for the 64 + 7 generated-but-not-selected rows if materialization does not unlock them. |
| B8 live path | OPEN | Fable B8 remains defined but ineligible while B7 is partial. | Production-return dossier, live-shadow, canary, and scale schedule remain blocked. | Broker/live/final stay false until B7 gates pass. |

### V153 Selected Next Same-Root Batch

Selected dependency after V153 commit: B7 selected-package replay source
materialization.

Patch requirements before another runtime replay:

- Trace the `79` `selected_package_lifecycle_context_without_current_replay_source_materialization`
  axes and `21` `selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap`
  axes into row-bound selected-package replay source/candidate/decision-window
  evidence where it exists.
- Preserve the V153 truth split: pair-broadcast lifecycle context is diagnostic
  proxy context, not exact denominator authority.
- Add producer, consumer, proof surface, verifier/focused tests, and repair-plan
  labels for any materialized source bridge.
- Expected behavior before runtime replay: neutral or reclassification unless a
  runtime consumer intentionally begins admitting newly materialized executable
  candidates. Use targeted proof before any broad replay.

## Current V151F Prepatch Refresh - Stable-Window Lifecycle Transfer Selected

Generated UTC: 2026-07-07T15:10:29Z.

This section supersedes the V151E section where it disagrees. Older sections
remain checkpoint evidence.

### Current Disk/Process State

- HEAD: `541c089c2 fix B7 selected package lifecycle context parity`.
- No broad replay, targeted replay, route builder, verifier, compile, or pytest
  process is running.
- Latest completed behavior proof remains
  `BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`.
- Latest committed checkpoint: V151E selected-package bridge lifecycle-context
  producer/consumer parity. Route verifier, route artifact audit, prompt
  hardening audit, focused tests, and `git diff --check` were green at commit.
- Authority boundary remains unchanged: broker mutation false, live broker
  authority false, final selection false, local replay/package evaluation full.

### Current Evidence Refresh

- `REPLAY_EXTENSION_SELECTED_PACKAGE_REPLAY_BRIDGE_SUMMARY.json`: generated
  `2026-07-07T14:06:34+00:00`, `bounded_smoke=true`,
  `symbol_scope=lifecycle-labels`, candidate rows `307`, selected-package
  candidate rows `228`, label join rows `1241`, denominator bridge rows `307`,
  `stable_decision_window_label_match_rows=1241`, and
  `stable_window_member_axis_unique_alias_rows=0`.
- `DENOMINATOR_NAMESPACE_REPAIR_LEDGER.jsonl` and
  `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`: `1101` rows each. Axis lifecycle
  context is ID-backed, but the current source-side stable-window transfer is
  incomplete: sampled status counts show source lifecycle IDs without
  decision-window samples on many rows while selected-package bridge decision
  windows are present.
- `SOURCE_BOUND_TO_EXECUTED_PARITY_V151E_B7_SELECTED_PACKAGE_BRIDGE_LIFECYCLE_CONTEXT_PRODUCER_PARITY_20260601_20260605_TARGETED_LEDGER.jsonl`:
  exact source-member surface counts:
  - `source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_not_stable_window_matched`:
    `293` rows.
  - `source_axis_selected_package_bridge_materialized_no_lifecycle_label_context`:
    `162` rows.
  - `selected_package_lifecycle_context_without_current_replay_source_materialization`:
    `79` rows.
  - `selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap`:
    `21` rows.
  - Lifecycle-related source-member rows show source-window samples missing on
    `614/711`, bridge-window samples present on `601/711`, and only `4`
    overlap rows. This proves the next batch is producer/consumer transfer
    classification, not a runtime replay decision.
- Label source check:
  `WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl` has `877` label
  rows; `428` have both `decision_time_utc` and `pending_created_time_utc`;
  `449` have pending-created time only. Current stable source-window derivation
  uses only `decision_time_utc`, while the selected-package replay bridge has a
  separate pending-created mode. The V151F patch must preserve that distinction
  rather than promoting pending-only labels into exact historical joins.

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json` and `BROKER_COST_REFUSAL_HISTOGRAM_V111.json` remain present; no V151E/V151F evidence reopens instrumentation. | None. | Preserve. |
| B1 provenance truth contract | DONE | Raw/effective action, materialization origin, risk-authority raw chain, R identity, and selected-package denominator reason split remain covered by focused tests and verifier scans. | None unless later patches reopen provenance drift. | Keep producer, consumer, ledger, and verifier paths green. |
| B2 fillability/reallocation truth chain | DONE | Cost-refused/source-gap/unresolved-fill-floor rows remain non-executable and scoreable/missed; V151F does not loosen execution authority. | Reallocation value remains a B7 transfer issue. | Preserve non-executable authority while B7 repairs transfer. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Risk provenance and diagnostic block-bucket semantics remain active. | Full-risk expression remains weak in B7 slices. | Treat sizing/allocation as later B7 transfer work, not a B3 truth failure. |
| B4 fill-simulation realism | DONE WITH LABEL | V150 fills remain ordered/tick entry surfaces with explicit fill realism/expiry status. | Broader regime realism proof remains a later B7 proof-ladder item. | Reopen only on new fill-source truth regression. |
| B5 verifier/comparison precision | DONE | Route verifier is green through V151E and has a selected-package lifecycle-context contract scan. | Missing V151F precision: transfer status is not yet produced/consumed/verified for lifecycle IDs vs bridge windows. | Add transfer-status producer, parity consumer, and verifier/focused tests. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority remains active; REFUSED rows remain non-executable diagnostic/missed. | Large cost-failed opportunity remains scoreable but not executable without same-window calibration evidence. | Do not loosen REFUSED execution. |
| B7 full proof ladder | PARTIAL | V151E closes ID-backed axis lifecycle-context producer/consumer proof. V151F evidence shows the next same-root gap is stable-window lifecycle transfer classification, led by `293` source-member axes and diagnostic source-bound R `481369.7478256911`. | B7.4 19-day and B7.5 extended history remain open. The current gap is not replay-ready until stable-window transfer status is deterministic. | Patch denominator producer, parity consumer, repair-plan labels, verifier scan, and focused tests. Rebuild builder/parity; targeted replay only if runtime consumers change. |
| B8 live path | OPEN | Fable B8 is defined but no B8 gate is eligible because B7 is partial. | Production-return dossier, live-shadow, canary, and scale schedule remain blocked. | Broker/live/final stay false until B7.1-B7.5 pass. |

### V151F Selected Same-Root Batch

Selected dependency: B7 transfer recovery, stable-window lifecycle transfer
status and selected-package source-materialization classification.

Patch requirements before another replay:

- Add a deterministic source-axis lifecycle-to-bridge window transfer status in
  `build_denominator_to_deployment_execution.py`: overlap present, source
  window missing, bridge window missing, window mismatch, or no axis context.
- Preserve pending-only lifecycle labels as pending-created/proxy context. Do
  not promote them into exact stable-window historical denominator joins.
- Carry the status, overlap count, and sample overlap/window fields into
  `build_source_bound_execution_parity.py`.
- Split the current generic
  `axis_lifecycle_label_context_available_not_stable_window_matched` bucket
  into exact subreasons so repair plans can distinguish producer gaps from true
  non-executable window mismatches.
- Extend verifier/focused tests so every new field has a producer, consumer,
  proof surface, and failing assertion.
- Expected behavior before runtime replay: neutral or reclassification.
  Candidate->scorecard, scorecard->order, trade count, net/gross/final R, and
  W/L/F should not change unless a runtime consumer is intentionally patched.

## Current V151E Refresh - Selected-Package Bridge Lifecycle Context Verified

Generated UTC: 2026-07-07T14:51:13Z.

This section supersedes the V151D section where it disagrees. Older sections
remain checkpoint evidence.

### Current Disk/Process State

- No broad replay was started for this checkpoint.
- Latest completed behavior proof remains
  `BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`.
- The selected-package replay bridge, denominator builder, canonical
  source-bound parity surface, route verifier, route artifact audit, prompt
  hardening audit, focused tests, and `git diff --check` have all rerun after
  the V151E code patch.
- Authority boundary: broker mutation, live broker authority, and final
  selection remain false; local replay/package evaluation remains
  full-authority.

### V151E Deterministic Artifact Evidence

- `SELECTED_PACKAGE_REPLAY_BRIDGE_SUMMARY.json`: generated
  `2026-07-07T14:06:34+00:00`; candidate rows `307`, selected-package
  candidate rows `228`, label-join rows `1241`, denominator bridge rows `307`,
  exact/canonical denominator joins `0`, `final_package_selected=false`, and
  `live_trading_enabled=false`.
- `DENOMINATOR_TO_DEPLOYMENT_EXECUTION_SUMMARY.json`: generated
  `2026-07-07T14:06:42Z`; final package selection and live trading remain
  false.
- `DENOMINATOR_NAMESPACE_REPAIR_LEDGER.jsonl` and
  `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`: `1101` rows each, `730` rows each
  now carry axis-level source lifecycle-label context, and legacy aggregate-only
  lifecycle context rows are `0`.
- Canonical manifest-selected parity artifacts rebuilt for
  `V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`:
  parity ledger rows `5461`, source-member axis rows `1101`, candidate trace
  rows `4360`, broad candidate rows `6633`, exact package candidate rows
  `59074`, exact package candidate matches `65`, final selection false, and
  broker/live authority false.
- Custom V151E parity artifacts also exist under
  `V151E_B7_SELECTED_PACKAGE_BRIDGE_LIFECYCLE_CONTEXT_PRODUCER_PARITY_20260601_20260605_TARGETED`
  for explicit checkpoint provenance.
- Top canonical B7 leakage ranking after V151E:
  - `source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_not_stable_window_matched`:
    `293` axes, diagnostic source-bound R `481369.7478256911`.
  - `source_axis_selected_package_bridge_materialized_no_lifecycle_label_context`
    and
    `source_axis_selected_package_bridge_materialized_stable_window_lifecycle_label_context`:
    `162 + 28` axes, diagnostic source-bound R `228991.310427867`.
  - `candidate_generated_broker_cost_refused_not_executable`: `51` axes,
    diagnostic source-bound R `202258.382340452`.
  - scheduler-not-selected classes: `64 + 7` axes, diagnostic source-bound R
    `193479.149317165`.
  - `selected_package_lifecycle_context_without_current_replay_source_materialization`:
    `79` axes, diagnostic source-bound R `95981.210142037`.
  - `selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap`:
    `21` axes, diagnostic source-bound R `32776.039521148`.
- `VERIFICATION_RESULT.json`: `ok=true`, `issue_count=0`,
  `final_package_selected=false`, `live_trading_enabled=false`, and
  `selected_package_replay_bridge_lifecycle_context_contract_scan.bad_counts={}`.
  The scan counted `730` namespace lifecycle-context axis rows, `730` member
  lifecycle-context axis rows, `307` bridge denominator rows, and `1241`
  bridge label rows.
- Focused proof:
  - `.codex_run_logs/v151e_py_compile_5.log`: compile passed for the touched
    route modules.
  - `.codex_run_logs/v151e_focused_pytest_5.log`: `7 passed, 197 deselected`.
  - `.codex_run_logs/v151e_hydration_py_compile.log`: compile passed after the
    verifier file-provider hydration retry repair.
  - `.codex_run_logs/v151e_hydration_focused_pytest.log`: `3 passed, 122
    deselected, 1 warning`.
  - `.codex_run_logs/v151e_route_verifier_retry_after_hydration_patch.log`:
    route verifier exited `0`.
  - `.codex_run_logs/v151e_route_artifact_audit.json`: `ok=true`.
  - `.codex_run_logs/v151e_prompt_hardening.json`: `ok=true`.
  - `.codex_run_logs/v151e_git_diff_check.log`: clean.

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | Baseline artifacts remain present and this checkpoint did not reopen B0 truth instrumentation. | None. | Preserve. |
| B1 provenance truth contract | DONE | Raw/effective selector split, materialization origin, risk-authority raw chain, R identity, and selected-package denominator reason split remain covered by focused tests and V151E verifier scans. | None unless later patches reopen provenance drift. | Keep producer, consumer, ledger, and verifier paths green. |
| B2 fillability/reallocation truth chain | DONE | V151E did not loosen fillability, cost, source-gap, or unresolved-fill-floor execution authority; cost-refused/source-gap rows remain non-executable and scoreable/missed. | Reallocation value remains a B7 transfer issue. | Preserve truth split while B7 repairs transfer. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Risk provenance and diagnostic block-bucket semantics remain active; V151E is producer/bridge proof, not a sizing policy change. | Full-risk expression remains weak in B7 slices. | Treat sizing/allocation as B7 transfer work, not B3 truth failure. |
| B4 fill-simulation realism | DONE WITH LABEL | V151E did not change fill simulation; V150 fills remain ordered/tick entry surfaces with explicit fill realism/expiry status. | Broader regime realism proof remains later B7 ladder work. | Reopen only on new fill-source truth regression. |
| B5 verifier/comparison precision | DONE | V151E adds a consumer verifier scan for selected-package bridge lifecycle context and route verifier/artifact audit/prompt hardening/diff check are green. The file-provider hydration retry fix prevents dataless scorecard ledgers from failing closed on the first timeout. | None for this checkpoint. | Keep route verifier green after each B7 producer/consumer proof surface change. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority remains active; cost-refused rows remain non-executable diagnostic/missed. | Large cost-failed opportunity remains scoreable but not executable without same-window calibration evidence. | Do not loosen REFUSED execution. |
| B7 full proof ladder | PARTIAL | V151E closes the selected-package bridge lifecycle-context producer/consumer proof surface: axis-level lifecycle IDs/counts/samples are now produced, bridge reasons distinguish context-present authority-closed rows, parity consumes ID-backed source-axis context only, aggregate-only context no longer masquerades as source-axis context, and verifier enforces the contract. | B7.4 19-day and B7.5 extended history remain open. Current highest same-root B7 gap is stable-window lifecycle alignment for `293` axes with diagnostic source-bound R `481369.7478256911`, followed by true lifecycle-context/source-materialization gaps and scheduler-not-selected classes. | After committing V151E, select the next B7 same-root batch from the canonical repair plan: stable-window lifecycle alignment / source-materialization transfer before any runtime replay. |
| B8 live path | OPEN | B8 is defined by Fable but cannot open until B7.1-B7.5 pass. | Production-return dossier, live-shadow, canary, and scale schedule remain blocked. | Broker/live/final stay false. |

### V151F Candidate Next Same-Root Batch

Selected dependency after V151E commit: B7 transfer recovery, stable-window
lifecycle alignment and source-materialization transfer.

Candidate patch requirements before another replay:

- Trace the `293` context-present axes from source-axis lifecycle context into
  stable-window decision-window keys and classify whether they are bridge key
  mismatch, decision-window derivation gap, or genuinely non-executable
  replay-window mismatch.
- Preserve the V151E distinction between ID-backed source-axis context and
  legacy aggregate context; do not reintroduce aggregate-only promotion.
- Patch producer/consumer code only where the same source evidence can create a
  deterministic stable-window bridge or an explicit non-executable reason.
- Run focused tests and route verifier before any targeted replay. A runtime
  replay is authorized only if the patch changes an executable consumer path,
  not merely a classification surface.

## Current V151D Refresh - Parity Rebuilt, Producer Bridge Patch Selected

Generated UTC: 2026-07-07T13:24:00Z.

This section supersedes the V151 prepatch section where it disagrees. Older
sections remain checkpoint evidence.

### Current Disk/Process State

- No broad replay, targeted replay, route builder, verifier, compile, or pytest
  process is running.
- Latest completed behavior proof remains
  `BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`.
- Latest focused parity rebuild is
  `V151D_B7_SELECTED_PACKAGE_AXIS_CONTEXT_AND_REPAIR_RANKING_20260601_20260605_TARGETED`.
- Authority boundary: broker mutation, live broker authority, and final
  selection remain false; local replay/package evaluation remains
  full-authority.

### V151D Deterministic Artifact Evidence

- `SOURCE_BOUND_TO_EXECUTED_PARITY_V151D_B7_SELECTED_PACKAGE_AXIS_CONTEXT_AND_REPAIR_RANKING_20260601_20260605_TARGETED_SUMMARY.json`:
  parity ledger rows `5461`, source-member axis rows `1101`, candidate trace
  rows `4360`, broad candidates `6633`, exact package candidate rows `59074`,
  exact package candidate matches `65`, final selection false, broker/live
  authority false.
- `EXECUTION_LEAKAGE_REPAIR_PLAN_V151D_B7_SELECTED_PACKAGE_AXIS_CONTEXT_AND_REPAIR_RANKING_20260601_20260605_TARGETED.json`
  now ranks B7 bridge/lifecycle materialization by diagnostic source-bound R
  instead of hiding source-gap rows behind zero executable source R.
- Top open B7 repair actions:
  - `selected_package_bridge_stable_window_lifecycle_context_materialization`:
    `293` axes, diagnostic source-bound R `481369.7478256911`, label
    `source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_not_stable_window_matched`.
  - `selected_package_bridge_lifecycle_context_materialization`: `190` axes,
    diagnostic source-bound R `228991.310427867`, labels
    `source_axis_selected_package_bridge_materialized_no_lifecycle_label_context`
    and `source_axis_selected_package_bridge_materialized_stable_window_lifecycle_label_context`.
  - `selected_package_replay_source_materialization`: `79` axes, diagnostic
    source-bound R `95981.210142037`.
  - `lifecycle_label_context_materialization`: `21` axes, diagnostic
    source-bound R `32776.039521148`.
- Focused proof for the V151D parity patch: `python3 -m py_compile` passed, and
  focused `tests/test_build_source_bound_execution_parity.py` selection passed
  `9 passed, 70 deselected, 1 warning`.

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json` and `BROKER_COST_REFUSAL_HISTOGRAM_V111.json` remain present. | None. | Preserve. |
| B1 provenance truth contract | DONE | Raw/effective selector split, materialization origin, risk-authority raw chain, and R identity checks remain covered by focused tests and V150/V151 artifacts. | None unless a later patch reopens provenance drift. | Keep producer, consumer, ledger, and verifier paths green. |
| B2 fillability/reallocation truth chain | DONE | Raw/resolved/unresolved fill-floor split, route-resolution semantics, fallback clamp, degraded-queue contract, and unresolved-fill-floor executable blocking remain active. | Reallocation value remains a B7 transfer issue. | Preserve truth split while B7 repairs transfer. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Ladder provenance and diagnostic loss-bucket mode remain active; V150 still has all three fills reduced-risk. | Full-risk expression remains weak in B7 slices. | Treat sizing/allocation as B7 transfer work, not B3 truth failure. |
| B4 fill-simulation realism | DONE WITH LABEL | V150 fills use ordered/tick entry surfaces and explicit fill realism/expiry status. | Broader regime realism proof remains later B7 ladder work. | Reopen only on new fill-source truth regression. |
| B5 verifier/comparison precision | DONE | Deterministic V151D parity, leakage bucket, and repair-plan artifacts exist; focused parity tests pass. | Full route verifier/artifact audit/prompt hardening must rerun after the next producer patch. | Keep scans green after producer and bridge reasons are patched. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority remains active; cost-refused rows remain non-executable diagnostic/missed. | Large cost-failed opportunity remains scoreable but not executable without same-window calibration evidence. | Do not loosen REFUSED execution. |
| B7 full proof ladder | PARTIAL | V151D identifies the next highest same-root B7 gap: selected-package bridge axes with lifecycle context not carried into stable-window denominator/bridge surfaces. | B7.4 19-day and B7.5 extended history remain open; V151D is parity proof only, not behavior proof. | Patch `build_denominator_to_deployment_execution.py` and `run_selected_package_replay_bridge.py` producer surfaces, then rebuild builder/parity before any runtime replay. |
| B8 live path | OPEN | B8 is defined by Fable but cannot open until B7.1-B7.5 pass. | Production-return dossier, live-shadow, canary, and scale schedule remain blocked. | Broker/live/final stay false. |

### V151E Selected Same-Root Batch

Selected dependency: B7 transfer recovery, selected-package bridge lifecycle
context producer parity.

Patch requirements before another replay:

- `build_denominator_to_deployment_execution.py`: persist axis-level lifecycle
  context IDs/counts/samples in `DENOMINATOR_NAMESPACE_REPAIR_LEDGER.jsonl`
  and `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`, not only aggregate
  `context_lifecycle_label_rows`.
- `run_selected_package_replay_bridge.py`: emit a distinct denominator reason
  for context-present but exact authority-closed rows, while keeping
  `selected_package_denominator_use_allowed=false` and final/live false.
- `build_source_bound_execution_parity.py`: consume those producer fields and
  keep the V151D diagnostic-source-bound-R repair-plan ranking intact.
- Focused tests: bridge reason, producer field persistence, parity
  classification, and repair-plan ranking. Runtime replay is not authorized
  unless a replay consumer changes.

## Current V150 Result Refresh - Targeted Replay Completed, V151 Batch Selected

Generated UTC: 2026-07-07T12:14:09Z.

This section supersedes the V150 "before targeted replay" section where it
disagrees. Older sections remain checkpoint evidence.

### Current Disk/Process State

- HEAD: `44e892e5c fix B7 router refusal transfer recovery`.
- V150 targeted replay completed; no duplicate broad replay was started.
- Latest completed proof is now
  `BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`.
- Active control files:
  `.context/context_os/PRE_REPLAY_BRIEF_20260707T1214Z_V151_B7_SELECTED_PACKAGE_BRIDGE_LIFECYCLE_CONTEXT_MATERIALIZATION_PREPATCH.md`
  and
  `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260707T1214Z_V151_B7_SELECTED_PACKAGE_BRIDGE_LIFECYCLE_CONTEXT_MATERIALIZATION_PREPATCH.json`.
- Authority boundary: broker mutation, live broker authority, and final
  selection remain false; local replay/package evaluation remains
  full-authority.

### Latest V150 Completed Proof

- Scope: 2026-06-01..2026-06-05; symbols `XAUUSD`, `XAGUSD`, `USDCAD`,
  `USDJPY`, `UKOIL_cash`; profile `repaired_package_conversion_v3`.
- Rows: candidates `6633`, scorecards `480`, order event rows `13`, terminal
  orders `6`, trades `3`, missed rows `6627`, source-universe rows `62`.
- Headline: net `+0.84449709R`, gross/final `+1.09529478R / +1.09529478R`,
  expected cost `0.25079769R`, cash PnL `+211.19447407`, risk cash
  `750.42443587`, risk pct sum `0.75`, W/L/F `3/0/0`.
- Trade frequency: `0.6` trades/day. Orders: `3` filled, `3` expired unfilled,
  `6` pending-accepted rows plus `1` deferred terminal lifecycle mutation row.
- Executable authority checks from exact order/trade fields: order and trade
  rows all carry `pretrade_cost_packet_status=PASSED` and
  `package_execution_result_scope=repaired_executable_package_replay`; live
  broker authority and final selection remain false.
- V150 vs V149/V148/V147/V144: trade delta `0`, net delta `0`.
- V150 vs V146: trade delta `+1`, net delta `+0.29090804R`, added `1`, removed
  `0`.
- Stress/MC: raw net `+0.84449709R`; extra cost stress remains positive at
  `+0.69449709R` for +0.05R/trade, `+0.54449709R` for +0.10R/trade, and
  `+0.24449709R` for +0.20R/trade; deterministic MC trade count `3`, total net
  `+0.84449709R`, drawdown p05/p50/worst `0.0R`.

Interpretation: V150 focused code proof passed but targeted replay is
behavior-neutral versus V149. It did not shrink the targeted V149 consumer
blocker counts: `package_marketable_limit_entry_guard_blocked` stayed `28`,
`pre_order_materialization_preflight_blocked:passive_limit_too_close_predecision_guard`
stayed `11`, and `risk_authority_bound_and_headroom_available` stayed `15` in
the risk-finalizer probe reason counts. The repair is not disproven at unit
level, but the broad rows do not reach those consumers as the next controlling
transfer leak.

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json` and `BROKER_COST_REFUSAL_HISTOGRAM_V111.json` remain present as baseline artifacts. | None. | Preserve; do not rerun unless proven stale. |
| B1 provenance truth contract | DONE | Raw/effective selector split, materialization origin, risk-authority raw chain, R identity, and verifier surfaces remain green through V150 focused tests and targeted replay. | None unless later patches reopen provenance drift. | Keep producer, consumer, ledger, and verifier paths green. |
| B2 fillability/reallocation truth chain | DONE | Raw/resolved/unresolved fill-floor split, route-resolution semantics, fallback clamp, degraded-queue contract, and unresolved-fill-floor executable blocking remain present. V150 order/trade rows all have cost PASSED and repaired executable package replay scope. | Reallocation value remains a B7 transfer issue. | Keep unresolved fill-floor rows scoreable/missed only unless route resolution proves executable authority. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Ladder provenance and diagnostic block-bucket mode remain active; V150 reports risk decisions `open-reduced-risk=6` and all three fills are reduced-risk. | Full-risk expression/allocation remains weak in B7 slices. | Treat sizing/allocation repair as B7 performance/transfer work while preserving B3 truth fields. |
| B4 fill-simulation realism | DONE WITH LABEL | V150 fills use ordered tick entry touch; orders split `filled=3`, `expired_unfilled=3`, and fill realism remains explicit. | Broader regime realism-passing behavior remains unproven. | Reopen only on a new fill-source or lifecycle truth regression. |
| B5 verifier/comparison precision | DONE | V150 flow diagnostics, source-bound parity, repair plan, and comparisons to V149/V148/V147/V146/V144 are materialized. | Full route verifier/artifact audit/prompt hardening still pending after the next code patch. | Keep deterministic parser artifacts current after each targeted proof. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority is active; V150 order/trade rows are all `PASSED`; cost-refused rows remain non-executable diagnostic/missed. | Cost-failed rows remain large; only same-window calibration evidence can reopen cost inputs. | Do not loosen REFUSED execution; repair reallocation away from cost-failed candidates. |
| B7 full proof ladder | PARTIAL | V150 preserves local positive behavior and invalid broker/live/final closure, but did not move the V149 consumer blocker buckets. Source-bound parity now shows next highest same-root blockers: selected-package row-bound source materialization (`79` axes), lifecycle-label context for candidate-namespace materialized axes (`21` axes), selector reject calibration (`6` axes), and redesign/repair generator materialization (`144` axes). | B7.4 19-day and B7.5 extended history remain open. V150 does not prove transfer improvement beyond V146. | Patch V151 selected-package bridge/lifecycle context materialization before another replay. |
| B8 live path | OPEN | Fable B8 live path is defined, but no B8 gate is eligible because B7 is partial. | Production-return dossier, live-shadow, canary micro-live, and scale schedule remain blocked. | Keep broker/live/final false until B7.1-B7.5 pass. |

### V151 Selected Same-Root Batch

Selected dependency: B7 transfer recovery, selected-package bridge and lifecycle
context materialization.

Evidence from V150 parity/repair plan:

- `executable_axis_missing_row_bound_selected_package_replay_candidate_or_decision_window`:
  `79` axes, priority `12`, stage `selected_package_replay_source_materialization`.
- `executable_axis_candidate_namespace_materialized_no_lifecycle_label_context`:
  `21` axes, priority `13`, stage `lifecycle_label_context_materialization`.
- Related broader classification gap:
  `source_axis_selected_package_bridge_materialized_no_lifecycle_label_context=455`
  and `source_axis_selected_package_bridge_materialized_stable_window_lifecycle_label_context=28`.

Files/components selected for the next patch:

- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- focused tests under `tests/test_build_source_bound_execution_parity.py`,
  `tests/test_source_bound_execution_parity.py`, and
  `tests/test_v4_timewarp_simulated_live_research_loop.py` if a replay
  consumer field is changed.

Patch type: correctness/diagnostic transfer repair. Expected behavior before
replay is neutral or reclassification unless row-bound source/lifecycle context
lets already-signed, cost-passed, source-complete candidates reach order/risk
surfaces. Success is measured first by parity bucket shrink, then by targeted
replay if behavior-affecting consumers change.

## Current V150 Control Refresh - Focused Proof Passed, Before Targeted Replay

Generated UTC: 2026-07-07T11:41:17Z.

This section supersedes the V149 "before targeted replay" section where it
disagrees. Older sections remain checkpoint evidence.

### Current Disk/Process State

- HEAD: `44e892e5c fix B7 router refusal transfer recovery`.
- Active process state at brief creation: no broad replay, targeted replay,
  verifier, compile, pytest, route builder, or route verifier process is
  running.
- Latest completed proof is now
  `BROAD_LIVE_AS_IF_REPLAY_V149_B7_MARKETABLE_ENTRY_EXECUTION_SESSION_AND_ACTION_SOURCE_REPAIR_20260601_20260605_TARGETED`.
- Active control files:
  `.context/context_os/PRE_REPLAY_BRIEF_20260707T1141Z_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR.md`
  and
  `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260707T1141Z_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR.json`.
- Authority boundary: broker mutation, live broker authority, and final
  selection remain false; local replay/package evaluation remains
  full-authority.

### Latest V149 Completed Proof

- Scope: 2026-06-01..2026-06-05; symbols `XAUUSD`, `XAGUSD`, `USDCAD`,
  `USDJPY`, `UKOIL_cash`; profile `repaired_package_conversion_v3`.
- Rows: candidates `6633`, scorecards `480`, order event rows `13`, simulated
  orders `6`, trades `3`, missed rows `6627`, source-universe rows `62`.
- Headline: net `+0.84449709R`, gross/final `+1.09529478R / +1.09529478R`,
  cash PnL `+211.19447407`, risk cash `750.42443587`, risk pct sum `0.75`,
  W/L/F `3/0/0`.
- Invalid execution counts: executed REFUSED cost `0`, executed source-gap `0`,
  unresolved-fill-floor order/trade `0/0`, live/final authority rows `0`.
- V149 vs V148: trade delta `0`, net delta `0`, added `0`, removed `0`.
- V149 vs V147: trade delta `0`, net delta `0`.
- V149 vs V146: trade delta `+1`, net delta `+0.29090804R`.
- V149 vs V144: trade delta `0`, net delta `0`.

Interpretation: V149 was behavior-identical to V148/V147 at trade identity and
R, but moved stale marketable-guard blockers into downstream consumer buckets.
It does not prove B7.4 19-day transfer, B7.5 extended-history transfer, or B8
live readiness.

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json` and `BROKER_COST_REFUSAL_HISTOGRAM_V111.json` remain present as baseline artifacts. | None. | Preserve; do not rerun unless proven stale. |
| B1 provenance truth contract | DONE | Raw/effective selector split, materialization origin, risk-authority raw chain, R identity, and verifier surfaces remain green through V149 plus V150 focused tests. | None unless later patches reopen provenance drift. | Keep producer, consumer, ledger, and verifier paths green. |
| B2 fillability/reallocation truth chain | DONE | Raw/resolved/unresolved fill-floor split, route-resolution semantics, fallback clamp, degraded-queue contract, and unresolved-fill-floor executable blocking remain present. V149 invalid execution counts are zero. | Reallocation value remains a B7 transfer issue. | Keep unresolved fill-floor rows scoreable/missed only unless route resolution proves executable authority. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Ladder provenance and diagnostic block-bucket mode remain active; V149 reports full/reduced risk separately and all three fills are still reduced-risk. | Full-risk expression/allocation remains weak in B7 slices. | Treat sizing/allocation repair as B7 performance/transfer work while preserving B3 truth fields. |
| B4 fill-simulation realism | DONE WITH LABEL | V149 fills use ordered/tick entry touch surfaces, expiries are explicit, and REFUSED/source-gap execution is zero. | Broader regime realism-passing behavior remains unproven. | Reopen only on a new fill-source or lifecycle truth regression. |
| B5 verifier/comparison precision | DONE | Route verifier/audit surfaces were green through V147; V150 focused tests add consumer-parity coverage for the current guard/finalizer/preflight class. | V150 targeted replay/verifier/audit still pending after focused proof. | After targeted V150, rerun route verifier/artifact audit/prompt hardening/diff checks. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority is active; V149 executed REFUSED/source-gap rows are zero. | Cost-failed rows remain large; only same-window calibration evidence can reopen cost inputs. | Do not loosen REFUSED execution; repair reallocation away from cost-failed candidates. |
| B7 full proof ladder | PARTIAL | V150 focused patch repairs the next exact consumer class from V149: raw reject overriding signed/materialized package action in risk release, stale guard-block truth outranking finalizer immediate route truth, and immediate-marketable rows leaking into passive-limit-too-close preflight via raw off-configured route provenance. Focused proof: py_compile passed; exact timewarp pytest `12 passed, 1 warning`. | Targeted V150 replay has not proven row-count/R effect. B7.4 19-day and B7.5 extended history remain open. | Run V150 targeted same-window proof only, then parse V150 vs V149/V148/V147/V146/V144 before any broad replay. |
| B8 live path | OPEN | Fable B8 live path is defined, but no B8 gate is eligible because B7 is partial. | Production-return dossier, live-shadow, canary micro-live, and scale schedule remain blocked. | Keep broker/live/final false until B7.1-B7.5 pass. |

### V150 Selected Same-Root Batch

Selected dependency: B7 transfer recovery, signed-action finalizer-route and
immediate-preflight consumer parity.

Evidence from V149 missed rows:

- `risk_finalizer_rejected_preselected_candidate`: `12` rows,
  `+2.29904221R` opportunity proxy, `+3.36310800R` positive opportunity proxy,
  cost-passed `12`.
- `risk_finalizer_rejected_preselected_candidate:package_marketable_limit_entry_guard_blocked`:
  `7` rows, `+3.90723626R` opportunity proxy, `+4.21264074R` positive
  opportunity proxy, cost-passed `7`.
- `risk_finalizer_rejected_preselected_candidate:pre_order_materialization_preflight_blocked:passive_limit_too_close_predecision_guard`:
  `10` rows, `+0.35693456R` opportunity proxy, `+2.22194865R` positive
  opportunity proxy, cost-passed `10`.
- Nonpreselected marketable/preflight variants are net negative (`3` rows,
  `-3.24826289R`) and are not globally opened by this batch.

Files changed by the active V150 patch:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`:
  correctness/performance transfer repair. Runtime risk action resolution now
  consumes signed/materialized package action ahead of raw reject where authority
  is valid; final blocker attribution prefers allowed immediate-route truth over
  stale guard-block truth; immediate-marketable fill preflight uses concrete
  execution-session authority while preserving raw route provenance.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`:
  focused verifier coverage for signed action projection, runtime-risk
  raw/effective split, final blocker precedence, concrete off-session authority,
  and immediate-route preflight behavior.

Focused proof:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- Exact timewarp pytest with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`: `12 passed, 1 warning`.

Expected targeted replay effect:

- Candidate -> scorecard transfer should remain near V149 `6633 -> 480`.
- V149 preselected consumer-mismatch buckets should shrink, transfer, or
  reclassify to later causal blockers.
- Any released row must be signed, cost-passed, source-complete, fillable/order-
  executable, and concrete-session authorized.
- REFUSED/source-gap/unresolved-fill-floor execution must remain zero.
- Improvement must be from better risk/order/fillability conversion, not
  positive-by-suppression or raw-only off-session opening.

Next replay prefix:
`BROAD_LIVE_AS_IF_REPLAY_V150_B7_SIGNED_ACTION_FINALIZER_ROUTE_AND_IMMEDIATE_PREFLIGHT_CONSUMER_REPAIR_20260601_20260605_TARGETED`.

## Current V149 Control Refresh - Focused Proof Passed, Before Targeted Replay

Generated UTC: 2026-07-07T10:35:51Z.

This section supersedes the V148B "before targeted replay" section where it
disagrees. Older sections remain checkpoint evidence.

### Current Disk/Process State

- HEAD: `44e892e5c fix B7 router refusal transfer recovery`.
- Active process state: no broad replay, targeted replay, verifier, compile, or
  pytest process is running.
- Latest completed proof is now
  `BROAD_LIVE_AS_IF_REPLAY_V148_B7_ROUTER_REFUSAL_SELF_LOCK_AUTHORITY_REPAIR_20260601_20260605_TARGETED`.
- Active control files:
  `.context/context_os/PRE_REPLAY_BRIEF_20260707T1035Z_V149_B7_MARKETABLE_ENTRY_EXECUTION_SESSION_AND_ACTION_SOURCE_REPAIR.md`
  and
  `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260707T1035Z_V149_B7_MARKETABLE_ENTRY_EXECUTION_SESSION_AND_ACTION_SOURCE_REPAIR.json`.
- Authority boundary: broker mutation, live broker authority, and final
  selection remain false; local replay/package evaluation remains
  full-authority.

### Latest V148 Completed Proof

- Scope: 2026-06-01..2026-06-05; symbols `XAUUSD`, `XAGUSD`, `USDCAD`,
  `USDJPY`, `UKOIL_cash`; profile `repaired_package_conversion_v3`.
- Rows: candidates `6633`, scorecards `480`, order event rows `13`, simulated
  orders `6`, trades `3`, missed rows `6627`, source-universe rows `62`.
- Headline: net `+0.84449709R`, gross/final `+1.09529478R / +1.09529478R`,
  cash PnL `+211.19447407`, risk cash `750.42443587`, risk pct sum `0.75`,
  W/L/F `3/0/0`.
- Invalid execution counts: executed REFUSED cost `0`, executed source-gap `0`,
  unresolved-fill-floor order/trade `0/0`, live/final authority rows `0`.
- V148 vs V147: trade delta `0`, net delta `0`, added `0`, removed `0`.
- V148 vs V146: trade delta `+1`, net delta `+0.29090804R`, added
  `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`,
  removed `0`.
- V148 vs V144: trade delta `0`, net delta `0`.

Interpretation: V148 self-lock repair is focused-proof green but behavior-neutral
versus V147. It does not prove B7.4 19-day transfer, B7.5 extended-history
transfer, or B8 live readiness.

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json` and `BROKER_COST_REFUSAL_HISTOGRAM_V111.json` remain present as baseline artifacts. | None. | Preserve; do not rerun unless proven stale. |
| B1 provenance truth contract | DONE | Raw/effective selector split, materialization origin, risk-authority raw chain, R identity, and verifier surfaces remain green through V148 and V149 focused tests. | None unless later patches reopen provenance drift. | Keep producer, consumer, ledger, and verifier paths green. |
| B2 fillability/reallocation truth chain | DONE | Raw/resolved/unresolved fill-floor split, route-resolution semantics, fallback clamp, degraded-queue contract, and unresolved-fill-floor executable blocking remain present. V148 invalid execution counts are zero. | Reallocation value remains a B7 transfer issue. | Keep unresolved fill-floor rows scoreable/missed only unless route resolution proves executable authority. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Ladder provenance and diagnostic block-bucket mode remain active; V148 reports full/reduced risk separately and all three fills are still reduced-risk. | Full-risk expression/allocation remains weak in B7 slices. | Treat sizing/allocation repair as B7 performance/transfer work while preserving B3 truth fields. |
| B4 fill-simulation realism | DONE WITH LABEL | V148 fills use ordered/tick entry touch surfaces, expiries are explicit, and REFUSED/source-gap execution is zero. | Broader regime realism-passing behavior remains unproven. | Reopen only on a new fill-source or lifecycle truth regression. |
| B5 verifier/comparison precision | DONE | Route verifier/audit surfaces were green through V147; V149 focused tests add route attribution for the current guard. | V149 replay/verifier/audit still pending after focused proof. | After targeted V149, rerun route verifier/artifact audit/prompt hardening/diff checks. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority is active; V148 executed REFUSED/source-gap rows are zero. | Cost-failed rows remain large; only same-window calibration evidence can reopen cost inputs. | Do not loosen REFUSED execution; repair reallocation away from cost-failed candidates. |
| B7 full proof ladder | PARTIAL | V148 kept local transfer behavior positive and invalid execution zero, but did not shrink transfer labels versus V147. V149 focused patch repairs the next exact class: `22` preselected, cost-passed, source-complete package-marketable guard-blocked rows (`+4.36251202R` opportunity proxy, `19` fillable) where raw off-configured route provenance and raw selector reject overrode concrete execution session and signed effective package action. Focused proof: py_compile passed; timewarp guard tests `4 passed, 567 deselected`. | Targeted V149 replay has not proven row-count/R effect. B7.4 19-day and B7.5 extended history remain open. | Run V149 targeted same-window proof only, then parse V149 vs V148/V147/V146/V144 before any broad replay. |
| B8 live path | OPEN | Fable B8 live path is defined, but no B8 gate is eligible because B7 is partial. | Production-return dossier, live-shadow, canary micro-live, and scale schedule remain blocked. | Keep broker/live/final false until B7.1-B7.5 pass. |

### V149 Selected Same-Root Batch

Selected dependency: B7 transfer recovery, marketable-entry execution namespace
and effective-action authority repair.

Evidence from V148 missed rows:

- `risk_finalizer_rejected_preselected_candidate:package_marketable_limit_entry_guard_blocked`: `22` rows, `+4.36251202R` opportunity proxy, `+7.59699638R` positive opportunity proxy, cost-passed `22`, source-complete `22`, fillable `19`.
- The route object had concrete `route_session_applied`/`authority_session`,
  but `configured_session_for_immediate_marketable_limit` was false because raw
  `route_session=off_configured_session` overrode the concrete execution
  namespace.
- The same route object also emitted
  `immediate_marketable_limit_requires_trade_selector_action` even when signed
  `package_new_entry_authority_selector_action` and
  `scheduler_materialization_selector_action` were `open-reduced-risk`.

Files changed by the active V149 patch:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`:
  correctness/performance repair. The marketable-entry guard now uses concrete
  execution session over raw route provenance, consumes effective/materialized/
  signed package selector action for immediate-limit authority, and records raw
  action/session provenance separately.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`:
  focused verifier coverage for concrete-session release, raw-reject/effective
  open-reduced release, and raw-only off-configured blocking.

Focused proof:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- Timewarp focused pytest: `4 passed, 567 deselected`.

Expected targeted replay effect:

- Candidate -> scorecard transfer should remain near V148 `6633 -> 480`.
- The preselected package-marketable guard-blocked class should shrink from
  `22` rows, or its false action/session blocker subreasons should shrink
  materially.
- Any released row must be signed, cost-passed, source-complete, fillable, and
  still broker/live/final closed.
- REFUSED/source-gap/unresolved-fill-floor execution must remain zero.
- Improvement must be from better risk/order conversion, not positive-by-
  suppression.

Next replay prefix:
`BROAD_LIVE_AS_IF_REPLAY_V149_B7_MARKETABLE_ENTRY_EXECUTION_SESSION_AND_ACTION_SOURCE_REPAIR_20260601_20260605_TARGETED`.

## Current V148B Control Refresh - Focused Proof Passed, Before Targeted Replay

Generated UTC: 2026-07-07T09:53:31Z.

This section supersedes the V148 "before next patch" refresh below where it
disagrees. Older sections remain checkpoint evidence.

### Current Disk/Process State

- HEAD: `44e892e5c fix B7 router refusal transfer recovery`.
- Active process state: no broad replay, targeted replay, verifier, compile, or
  pytest process is running. Stale desktop-app `git diff --numstat` helpers were
  killed when observed.
- Latest completed proof remains
  `BROAD_LIVE_AS_IF_REPLAY_V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`.
- New active control files:
  `.context/context_os/PRE_REPLAY_BRIEF_20260707T0953Z_V148_B7_ROUTER_REFUSAL_SELF_LOCK_AUTHORITY_REPAIR.md`
  and
  `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260707T0953Z_V148_B7_ROUTER_REFUSAL_SELF_LOCK_AUTHORITY_REPAIR.json`.
- Authority boundary: broker mutation, live broker authority, and final
  selection remain false; local replay/package evaluation remains
  full-authority.

### Historical Hostile Comparator Baselines

These are required control-surface references, but they are not
denominator-equivalent to the V148 targeted June 1-5 five-symbol proof slice.
They stay hostile/stress references until a same-window replay is run.

| Run | Scope | Trades | Net R | Gross/Final R | Cash PnL | W/L/F | Source |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| V89D | 2026-05-13..17 fullgrid | 56 | +34.84520454 | +39.93441037 / +39.93441037 | +8178.90660707 | 41/15/0 | `.context/context_os/PRE_REPLAY_BRIEF_20260703T0330Z.md:53` |
| V90 | 2026-05-13..17 fullgrid | 51 | +28.84201157 | +33.36349114 / +33.36349114 | +6371.80465431 | 37/14/0 | `.context/context_os/PRE_REPLAY_BRIEF_20260703T0330Z.md:54` |
| V92 | 2026-05-13..17 fullgrid | 51 | +29.35570236 | +33.93212860 / +33.93212860 | +6228.63096022 | 37/14/0 | `.context/context_os/PRE_REPLAY_BRIEF_20260703T0330Z.md:55` |

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json` and `BROKER_COST_REFUSAL_HISTOGRAM_V111.json` are present and remain the before/after baseline. | None. | Preserve; do not rerun unless a baseline artifact is proven stale. |
| B1 provenance truth contract | DONE | Raw/effective selector split, materialization origin, risk-authority raw chain, R identity, and verifier surfaces remain green through V147/V148B focused tests. | None unless a later patch reopens provenance drift. | Keep producer, consumer, ledger, and verifier paths green for every new field. |
| B2 fillability/reallocation truth chain | DONE | Raw/resolved/unresolved fill-floor split, route-resolution semantics, fallback clamp, degraded-queue contract, and unresolved-fill-floor executable blocking remain present; V147 invalid unresolved-fill-floor execution is zero. | Reallocation value remains a B7 transfer issue, not a B2 truth gap. | Keep unresolved fill-floor rows scoreable/missed only unless route resolution proves executable authority. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Ladder provenance and diagnostic block-bucket mode are active; V147 fills are still `open-reduced-risk=3` with risk distribution visible. | Full-risk expression/allocation remains weak in B7 slices. | Treat sizing/allocation repair as B7 performance/transfer work while preserving B3 truth fields. |
| B4 fill-simulation realism | DONE WITH LABEL | V147 fills use ordered/tick entry touch surfaces, expiries are explicit, and REFUSED/source-gap execution is zero. | Broader regime realism-passing behavior remains unproven. | Reopen only on a new fill-source or lifecycle truth regression. |
| B5 verifier/comparison precision | DONE | V147 route verifier, route artifact audit, prompt hardening, and focused V148B tests are green. | Add scans only if V148B replay exposes a new proof surface. | Keep route verifier and route artifacts green after targeted proof. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority is active; V147 executed REFUSED/source-gap rows are zero. | Cost-failed rows remain large; only same-window calibration evidence can reopen cost inputs. | Do not loosen REFUSED execution; repair reallocation away from cost-failed candidates. |
| B7 full proof ladder | PARTIAL | V147 recovered one valid transfer winner. V148B focused patch now addresses the next recoverable same-root class: 280 cost-passed/source-complete/fillable displacement-quality rows with false source-bound/hash self-lock veto. Focused proof: py_compile passed; scheduler tests `7 passed`; timewarp tests `3 passed`. | Targeted replay has not yet proven whether the 280-row false veto class shrinks or transfers. B7.4 19-day and B7.5 extended history remain open. | Run V148 targeted same-window proof only, then parse V148 vs V147/V146/V144 before any broad replay. |
| B8 live path | OPEN | Fable B8 live path is defined, but no B8 gate is eligible because B7 is partial. | Production-return dossier, live-shadow, canary micro-live, and scale schedule remain blocked. | Keep broker/live/final false until B7.1-B7.5 pass. |

### V148B Selected Same-Root Batch

Selected dependency: B7 transfer recovery, source-bound router-refusal signed
self-lock authority repair.

Subagent findings incorporated:

- Kepler: incorporated. The recoverable 280-row class is a self-lock caused by
  stale signed authority, not missing source evidence. The fix rederives only
  exact source-bound router-refusal self-lock rows through signed source/cost/
  fill authority.
- Archimedes: incorporated. Added positive stale restamp/displacement coverage
  and negative broker-cost REFUSED non-bypass coverage.
- Curie: incorporated. Producer fields are present; downstream signer/backfill/
  missed projection now hydrates aliases, preserves valid hashes, and preserves
  scheduler-materialized intent on diagnostic missed rows.

Files changed by the active V148B patch:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`:
  correctness/performance repair. Adds exact router-refusal self-lock
  rederivation; separates source-bound membership from executable admission;
  revalidates the terminal veto path through derived authority.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`:
  correctness/ledger repair. Hydrates source-bound aliases in signer refresh;
  preserves already-valid authority hashes; carries candidate decision inputs
  into backfilled signing; preserves scheduler materialized action/reason on
  non-executable missed diagnostics.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py` and
  `tests/test_v4_timewarp_simulated_live_research_loop.py`:
  focused verifier coverage for the producer/consumer/proof chain.

Focused proof:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- Scheduler focused pytest: `7 passed, 249 deselected`.
- Timewarp focused pytest: `3 passed, 568 deselected`.

Expected targeted replay effect:

- Candidate -> scorecard transfer should not collapse; expected near V147
  `6633 -> 480`.
- Scorecard -> order transfer should recover or precisely reclassify some of
  the false source-bound/hash veto class.
- Invalid execution counts must stay zero for REFUSED cost, source-gap,
  unresolved-fill-floor, live, final, and off-authority rows.
- Any improvement must be from better conversion or better attribution, not
  positive-by-suppression.

Next replay prefix:
`BROAD_LIVE_AS_IF_REPLAY_V148_B7_ROUTER_REFUSAL_SELF_LOCK_AUTHORITY_REPAIR_20260601_20260605_TARGETED`.

## Current V148 Control Refresh - Before Next Patch

Generated UTC: 2026-07-07T09:25:00Z.

This section supersedes the V147 "commit pending" status below. Older sections
remain checkpoint evidence.

### Current Disk/Process State

- HEAD: `44e892e5c fix B7 router refusal transfer recovery`.
- Active process state: no broad replay, targeted replay, verifier, test, or
  compile process is running. Stale high-CPU `git diff --numstat` helpers were
  terminated before this refresh.
- Latest completed proof remains:
  `BROAD_LIVE_AS_IF_REPLAY_V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`.
- Latest full five-day broad reference remains:
  `BROAD_LIVE_AS_IF_REPLAY_V128_B7_ROUTER_REFUSAL_DERIVED_IMMEDIATE_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`.
- Authority boundary: broker mutation, live broker authority, and final
  selection remain false; local replay/package evaluation remains
  full-authority.

### B0-B8 Execution Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json` and `BROKER_COST_REFUSAL_HISTOGRAM_V111.json` are present; the baseline counts are recorded in the earlier Fable matrix and V114 briefs. | None. | Preserve as the before/after baseline; do not rerun unless a provenance artifact is proven stale. |
| B1 provenance truth contract | DONE | Raw/effective selector split, materialization origin, risk-authority raw chain, and R-identity checks are implemented and remain verifier-green through V147. | None unless a later patch reopens provenance drift. | Keep producer, consumer, ledger, and verifier paths green for every new field. |
| B2 fillability/reallocation truth chain | DONE | Raw/resolved/unresolved fill-floor split, route-resolution semantics, fallback clamp, degraded-queue contract, and unresolved-fill-floor executable blocking are present; V147 has zero unresolved-fill-floor order/trade execution rows. | Reallocation value model remains a B7 transfer issue, not a B2 truth gap. | Keep unresolved fill-floor rows scoreable/missed only unless route resolution proves executable authority. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Ladder provenance and diagnostic block-bucket mode are active; V147 reports fills as `open-reduced-risk=3` with broker/live/final closed. | Full-risk expression and allocation quality remain weak in B7 slices. | Treat sizing/allocation repair as B7 performance/transfer work while preserving B3 truth fields. |
| B4 fill-simulation realism | DONE WITH LABEL | V147 fills use ordered/tick entry touch surfaces, expiries are explicit, and REFUSED/source-gap execution is zero. | Broader regime realism-passing behavior is still unproven. | Reopen only on a new fill-source or lifecycle truth regression. |
| B5 verifier/comparison precision | DONE | V147 verifier `ok=true`, route artifact audit `ok=true`, prompt hardening `ok=true`, and manifest points at V147 parity/provenance artifacts. | None for the current checkpoint. | Add tests/verifier scans only for new B7 proof surfaces. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority is active; V147 executed REFUSED/source-gap rows are zero. Prior B6 audit classified most refusals as honest/non-executable. | Cost-failed rows remain large; only exact same-window calibration evidence can reopen cost inputs. | Do not loosen REFUSED execution; repair scheduler/risk reallocation away from cost-failed candidates. |
| B7 full proof ladder | PARTIAL | V147 recovered the valid `62cb...17:45` transfer while preserving V146 truth cleanup: 6633 candidates, 480 scorecards, 13 order-event rows, 6 simulated orders, 3 fills, net `+0.84449709R`, W/L/F `3/0/0`, invalid execution counts zero. | B7.4 19-day and B7.5 extended history are open; V147 still has large pre-order blocker classes: cost-failed `3285`, router-refusal package-open-reduced authority-not-allowed `1527`, fill-floor quality non-executable `624`, no-shadow-sleeve-match `358`, displacement quality `280`, reduce-risk not-new-entry authority `191`. | Next selected batch: quantify and patch scheduler/reallocation plus package-authority blocker classes for cost-passed/source-complete/fillable rows blocked before order. Run focused tests before any targeted replay. |
| B8 live path | OPEN | Fable B8 live path is defined, but no B8 gate is eligible because B7 is partial. | Production-return dossier, live-shadow, canary micro-live, and scale schedule remain blocked. | Keep broker/live/final false until B7.1-B7.5 pass. |

### Selected Next Dependency Batch

Selected dependency: B7 transfer recovery, next same-root batch.

Do not run a broad replay next. The next implementation pass must quantify the
V147 pre-order blocker classes and patch only the recoverable, cost-passed,
source-complete, fillable chain. The expected affected components are scheduler
ranking/reallocation, package authority materialization, risk/finalizer
disposition, lifecycle/order proof surfaces, and focused verifier/tests if a new
authority contract is introduced.

## Current V147 Refresh - Authoritative Before Next Patch

Generated UTC: 2026-07-07T08:45:00Z.

This section supersedes the V146 refresh below where it disagrees. Older
sections remain checkpoint evidence.

### Current Disk/Process State

- HEAD before this checkpoint: `1460e7a1b fix B7 unresolved fill-floor execution authority`.
- Active process state after the targeted replay: no broad replay or targeted
  replay is running. A stale `git add` helper that had been sleeping on a giant
  staging list was terminated before verification work continued.
- Latest completed targeted proof:
  `BROAD_LIVE_AS_IF_REPLAY_V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`.
- Latest completed full 24-symbol five-day B7 broad proof remains:
  `BROAD_LIVE_AS_IF_REPLAY_V128_B7_ROUTER_REFUSAL_DERIVED_IMMEDIATE_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`.
- Authority boundary: broker mutation, live broker authority, and final
  selection remain false; local replay/package evaluation remains full-authority.

### Latest Replay Anchors

| Prefix | Scope | Trades | Net R | Gross/Final R | Cash PnL | W/L/F | Candidate -> Scorecard -> Order -> Fill | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| V147 source-bound router-refusal materialization floor repair | 2026-06-01..2026-06-05, 5 symbols | 3 | +0.84449709 | +1.09529478 / +1.09529478 | +84.46094125 | 3/0/0 | 6633 -> 480 -> 13 event rows / 6 simulated orders -> 3 | Focused B7 transfer repair passed locally: recovered the V144 `62cb...17:45` winner that V146 dropped while preserving V146's unresolved-fill-floor cleanup. |
| V146 unresolved fill-floor execution authority repair | Same targeted scope | 2 | +0.55358905 | +0.72340378 / +0.72340378 | +55.36532564 | 2/0/0 | 6633 -> 480 -> 10 event rows / 5 simulated orders -> 2 | Truth proof passed but dropped the valid V144 `62cb...17:45` winner. |
| V144 router-refusal namespace producer repair | Same targeted scope | 3 | +0.84449709 | +1.09529478 / +1.09529478 | +84.46094125 | 3/0/0 | 6633 -> 480 -> 15 event rows / 7 simulated orders -> 3 | V147 is behavior-identical at trade level while cleaner on unresolved-fill-floor/order-event surface. |
| V128 router-refusal derived immediate authority repair | 2026-06-01..2026-06-05, full 24 symbols | 55 | +1.12099062 | +6.22739670 / +6.22739670 | +3007.28429755 | 38/17/0 | 35191 -> 480 -> 212 -> 55 | Latest full five-day B7 reference; still trails V104 by -13.61002429R and has 0 common V104 canonical trade keys. |

### V147 Result

Patch tested:

- Producer default repair: source-bound router-refusal replay materialization now
  uses execution-fillability floor `0.55`, aligned with selected-policy
  execution fillability, instead of the stale stricter `0.80` materialization
  floor that blocked rows like `62cb...17:45` before scheduler ranking.
- Route profile repair: repaired broad replay profile forwards both scheduler
  and ultimate-package source-bound router-refusal materialization fill floors
  at `0.55`.
- Consumer proof: `materialize_scheduler_window` has focused coverage for a
  `62cb`-class source-bound, broker-cost-passed, source-complete,
  execution-fillability `0.551338888` row becoming signed open-reduced
  scheduler-rankable without live broker authority.

Targeted replay result:

- Scope: 2026-06-01..2026-06-05; symbols `XAUUSD`, `XAGUSD`, `USDCAD`,
  `USDJPY`, `UKOIL_cash`; profile `repaired_package_conversion_v3`.
- Rows: candidates `6633`, scorecards `480`, order event rows `13`, simulated
  orders `6`, fills `3`, missed rows `6627`, source-universe rows `62`.
- Headline: net `+0.84449709R`, gross/final `+1.09529478R / +1.09529478R`,
  cash PnL `+84.46094125`, risk cash `300.06790974`, risk pct sum `0.3`,
  W/L/F `3/0/0`, trade frequency `0.6/day`.
- Cost: broker-calibrated execution cost `0.25079769R`; legacy candidate cost
  remains fallback diagnostic only.
- Risk/action: all fills remain `open-reduced-risk`; this is still a B7
  allocation/risk-expression performance issue, not a B3 truth gap.
- Order lifecycle: `pending_accepted=6`, `filled=3`, `expired_unfilled=3`,
  `terminal_lifecycle_position_state_mutation_deferred=1`.
- Stress/MC: raw net `+0.84449709R`; extra-cost stress stays positive at
  `+0.69449709R` for +0.05R/trade, `+0.54449709R` for +0.10R/trade, and
  `+0.24449709R` for +0.20R/trade; MC total net `+0.84449709R`, 200
  iterations, worst max drawdown `0.0R`.
- Invalid execution counts: executed REFUSED cost rows `0`, executed source-gap
  rows `0`, unresolved-fill-floor order/trade execution rows `0`, live/final
  authority rows `0`.

V147 versus V146:

- Trade delta `+1`, net delta `+0.29090804R`, gross/final delta
  `+0.37189100R / +0.37189100R`, cash delta `+29.09561561`.
- Added exactly one trade and removed none:
  `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`,
  XAUUSD LONG, `moonshot_h17_18`, `ob_retest`, net `+0.29090804R`.
- Candidate and scorecard rows did not collapse: `6633 -> 6633`, `480 -> 480`.

V147 versus V144:

- Same three filled trade keys and same headline net `+0.84449709R`.
- V147 keeps the cleaner V146 unresolved-fill-floor authority surface:
  order event rows are `13` versus V144 `15`, simulated orders are `6` versus
  V144 `7`, and expired unfilled orders are `3` versus V144 `4`.

Interpretation:

- This is a successful bounded B7 transfer-recovery proof. It is not a broad
  B7.4 transfer pass and it is not full-reservoir conversion evidence.
- The repair improved conversion rather than suppressing opportunity: it added a
  valid cost-passed/source-complete/fillable winner, did not remove trades, and
  did not collapse candidates or scorecards.
- B7 remains PARTIAL because the same-window flow still shows large non-order
  surfaces: cost-failed rows `3285`, router-refusal package-open-reduced
  authority not allowed rows `1527`, package fill-floor quality non-executable
  rows `624`, no-shadow-sleeve-match rows `358`, package displacement quality
  rows `280`, and reduce-risk not-new-entry authority rows `191`.

### Updated Batch Status

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | Baseline audit and cost-refusal histogram remain present; no V147 patch reopened B0. | None. | Preserve as fixed before/after baseline. |
| B1 provenance truth contract | DONE | V147 retains raw/effective selector separation, materialization origin, signed authority, R identity, and focused tests. | None unless a later patch reopens provenance drift. | Keep fatal scans green. |
| B2 fillability/reallocation truth chain | DONE | V147 preserves V146 unresolved-fill-floor cleanup: unresolved-fill-floor order/trade rows remain zero. | Reallocation value remains B7-open. | Keep unresolved failures scoreable/missed only. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Risk ladder provenance remains active; V147 reports all fills as `open-reduced-risk=3`. | Performance/allocation remains weak because no full-risk fills appear in this slice. | Treat full/reduced sizing as B7 allocation/risk-expression work, not B3 truth redo. |
| B4 fill-simulation realism | DONE WITH LABEL | V147 fills are ordered tick entry touch; expired rows are explicit; REFUSED/source-gap execution remains zero. | Realism-passing behavior still needs broader regime proof. | Reopen only if a new fill-source realism regression appears. |
| B5 verifier/comparison precision | DONE | Focused tests passed before replay; compact V147 flow/comparison artifacts materialized; V147 route verifier is green; route artifact audit is green; prompt hardening is green; scoped and cached diff checks are green. | None for this checkpoint. | Commit scoped V147 files only. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost remains authoritative; executed REFUSED/source-gap rows remain zero. | Cost-failed rows are large but honest non-executable unless recalibration evidence appears. | Do not loosen broker-cost REFUSED gate; repair reallocation away from cost-failed rows. |
| B7 full proof ladder | PARTIAL | V147 recovered one valid transfer winner and improved V146 locally without suppression. | B7.4 19-day and B7.5 extended history are open; same-window flow still has large materialization/reallocation/authority blocker classes and all fills are reduced risk. | After verifier/audit commit, select the next B7 same-root batch from V147 flow: scheduler/reallocation and package authority blocker classes, especially cost-passed/source-complete/fillable rows blocked before order. |
| B8 live path | OPEN | No B8 gate is eligible because B7 is partial. | Production-return dossier, live-shadow, canary micro-live, and scale schedule remain blocked. | Keep broker/live/final false. |

### V147 Verification After Manifest Repair

After V147 parity/provenance materialization, `OUTPUT_MANIFEST.json` was updated
from V146 to the V147 active broad-quality parity surface:

- Active prefix:
  `BROAD_LIVE_AS_IF_REPLAY_V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`.
- Active tag:
  `V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`.
- `broad_quality_parity_files`: 19 V147 files, including replay ledgers,
  summary, parity/provenance/leakage outputs, and flow diagnostic outputs.
- V147 parity/provenance builder:
  `source_bound_execution_parity_materialized`, parity rows `5461`, leakage
  bucket rows `1101`.

Post-manifest verification:

- `python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py --broad-prefix BROAD_LIVE_AS_IF_REPLAY_V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED --artifact-tag V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`: passed, materialized V147 parity/provenance/leakage artifacts.
- `python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: `ok=true`, `issue_count=0`, active quality prefix V147, `final_package_selected=false`, `live_trading_enabled=false`, verified at `2026-07-07T09:07:56Z`.
- `python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20 --profile standard`: `ok=true`, `missing_required=[]`, `missing_warnings=[]`, active quality prefix V147.
- `python3 scripts/validate_goal_prompt_hardening.py --kind builder --json research/operations/final_moonshot_ultimate_system_denominator_to_deployment_goal_2026_06_20/ULTIMATE_SYSTEM_DENOMINATOR_TO_DEPLOYMENT_GOAL_PROMPT.md research/operations/final_moonshot_ultimate_system_denominator_to_deployment_goal_2026_06_20/ULTIMATE_SYSTEM_DENOMINATOR_TO_DEPLOYMENT_STARTER.md`: `ok=true`, no missing checks.

Scoped worktree diff check and cached diff check passed. Scoped staging/commit
remain for this checkpoint.

## Current V146 Refresh - Authoritative Before Next Patch

Generated UTC: 2026-07-07T08:05:00Z.

This section supersedes the older V144/V145 checkpoint text below where it
disagrees. The older sections remain as historical checkpoint evidence.

### Current Disk/Process State

- HEAD: `1460e7a1b fix B7 unresolved fill-floor execution authority`.
- Active process state: no broad replay, targeted replay, pytest, py_compile,
  route builder, or route verifier process is running.
- Latest completed targeted proof:
  `BROAD_LIVE_AS_IF_REPLAY_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED`.
- Latest completed full 24-symbol five-day B7 broad proof:
  `BROAD_LIVE_AS_IF_REPLAY_V128_B7_ROUTER_REFUSAL_DERIVED_IMMEDIATE_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`.
- Route verifier: `VERIFICATION_RESULT.json` has `ok=true`,
  `issue_count=0`, `final_package_selected=false`, and
  `live_trading_enabled=false` after V146.
- Authority boundary: broker mutation, live broker authority, and final
  selection remain false; local replay/package evaluation remains full-authority.

### Latest Replay Anchors

| Prefix | Scope | Trades | Net R | Gross/Final R | Cash PnL | W/L/F | Candidate -> Scorecard -> Order -> Fill | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| V146 unresolved fill-floor execution authority repair | 2026-06-01..2026-06-05, 5 symbols | 2 | +0.55358905 | +0.72340378 / +0.72340378 | +55.36532564 | 2/0/0 | 6633 -> 480 -> 10 -> 2 | Focused truth proof passed: unresolved fill-floor order/trade rows 0/0; executed REFUSED/source-gap/live/final rows 0. B7 transfer recovery remains open. |
| V145 selector admission transfer and selected-policy quality | Same targeted scope | 3 | +0.18335355 | +0.48352934 / +0.48352934 | +20.25425216 | 2/1/0 | 6633 -> 480 -> 14 -> 3 | Mixed proof exposed unresolved fill-floor executable authority leak. |
| V144 router-refusal namespace producer repair | Same targeted scope | 3 | +0.84449709 | +1.09529478 / +1.09529478 | +84.46094125 | 3/0/0 | 6633 -> 480 -> 15 -> 3 | Truth-surface repair. V146 removed valid `62cb...17:45` winner that V144 executed. |
| V128 router-refusal derived immediate authority repair | 2026-06-01..2026-06-05, full 24 symbols | 55 | +1.12099062 | +6.22739670 / +6.22739670 | +3007.28429755 | 38/17/0 | 35191 -> 480 -> 212 -> 55 | Latest full five-day B7 reference; still trails V104 by -13.61002429R and has 0 common V104 canonical trade keys. |

### Batch Status Matrix

| Batch | Status | Requirement Evidence | Remaining Gap | Next Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json` and `BROKER_COST_REFUSAL_HISTOGRAM_V111.json` exist. The Fable baseline counts are recorded in the earlier matrix and V114 briefs. | None. | Preserve as fixed before/after baseline. |
| B1 provenance truth contract | DONE | Raw/effective selector provenance, risk authority raw-action chain, materialization origin, R identity, and focused selector/timewarp/scheduler tests were implemented before V122. V146 route verifier remains green, so later patches have not reopened these fatal scans. | None unless a later patch reopens raw/effective or R identity drift. | Keep scans green; no B1 redo. |
| B2 fillability/reallocation truth chain | DONE | Unresolved/raw fill-floor split, route-resolution family handling, terminal-veto cap cleanup, fallback clamp, degraded-queue contract, and related tests are present. V146 proves unresolved fill-floor failures no longer bind order/trade authority. | Reallocation value remains incomplete at B7, but B2 truth semantics are closed. | Do not reopen unresolved fill-floor execution; keep unresolved failures scoreable/missed only. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Risk-expression ladder producer/consumer/verifier surfaces are active; block buckets are diagnostic in repaired replay profiles; full/reduced distribution is reported in V128/V146 context. | Performance is not solved. V146 fills remain `open-reduced-risk=2`, so risk expression remains a B7 allocation/performance issue, not a B3 truth gap. | Preserve ladder provenance into every B7 patch and report full/reduced separately. |
| B4 fill-simulation realism | DONE WITH LABEL | Source-time gates, tick/ordered-path realism, diagnostic fill classes, same-bar ambiguity handling, and tick-hydrated hostile proof artifacts exist. V146 has no executed source-gap/REFUSED rows and order expiries are explicit. | Realism-passing behavior can still lose; this is a B7 strategy/transfer problem unless a new realism leak appears. | Reopen only if a new fill-source realism regression appears in focused proof. |
| B5 verifier/comparison precision | DONE | Verifier requires effective action, flags raw/effective authority leaks, scopes proof/cost scans, validates full-risk signing, and V146 route verifier is green. `OUTPUT_MANIFEST.json` includes V146 broad-quality parity files. | Additions are allowed only when next B7 patch creates a new proof surface. | Keep route verifier, route artifact audit, prompt hardening, and scoped diff checks green. |
| B6 broker-cost calibration audit | DONE WITH LABEL | Broker-calibrated cost authority is active; REFUSED/source-gap execution is verifier-fatal and V146 executed counts are zero. Prior B6 audit classified most refusals honest; source-gap/stale/mapping rows remain diagnostic unless exact recalibration evidence appears. | Cost-refused rows remain large but non-executable; repair path is reallocation away from REFUSED rows, not loosening REFUSED execution. | Do not bypass broker-cost authority. Audit only if a new same-window cost-calibration blocker is proven. |
| B7 full proof ladder | PARTIAL | V146 passed focused truth proof: candidate 6633, scorecard 480, order 10, trades 2, net +0.55358905R, W/L/F 2/0/0, unresolved fill-floor order/trade rows 0/0, executed REFUSED/source-gap/live/final rows 0. Subagents Kant/Tesla/Heisenberg all agree B7 remains blocked before order by selector/router materialization, scheduler/reallocation, finalizer blocker classes, lifecycle replacement proof, and valid missed winners. | B7.4 19-day and B7.5 extended history remain open. Same-window transfer is still weak: V146 removed V144 `62cb...17:45` +0.29090804R winner; V128 still trails V104 and has no common V104 trade keys. | Next patch batch is B7 transfer recovery: repair signed router-refusal/source-bound materialization and transfer-blocker proof without reopening unresolved fill-floor or REFUSED/source-gap execution. Run focused tests first, then targeted same-window proof only. |
| B8 live path | OPEN | Fable B8 live path exists in the implementation sequence, but no B8 gate is eligible because B7 is partial. | Production-return dossier, live-shadow, canary micro-live, and scale schedule are all blocked by B7. | Keep broker/live/final false. Prepare B8 only after B7.1-B7.5 pass. |

### Subagent Findings Incorporated Into Current Matrix

- Kant: V146 did not newly drop `62cb`; V145 dropped it before order/trade.
  The row is source-bound, cost-passed, and appears in finalizer probes, but
  router-refusal open-reduced materialization fails because
  `source_bound_open_reduced_materialization_allowed=false`, origin family is
  not allowed, and execution fill probability `0.551338888` is below the
  source-bound materialization floor `0.8`.
- Tesla: Highest B7 recoverable class is scheduler/reallocation ranking
  (`69` leakage axes, missed R `+166.58235496 / -401.05522433`), followed by
  broker-cost-preserving reallocation, fill-floor/order authority propagation,
  generator materialization, and selector/router package-admission transfer.
  Do not admit all; rank/reallocate only cost-passed, source-complete, fillable,
  positive-transfer candidates.
- Heisenberg: V146 has no missed rows that are already order-executable.
  The mismatch is earlier: missed rows are made non-order-executable by package
  authority, fill-floor quality, finalizer fill-realism, lifecycle authority,
  and pending replacement gates. Suggested tests/verifier additions should
  ensure every cost-passed/source-complete/fillable missed row has an explicit
  blocker and every pending order terminalizes with risk release.

### Selected Next Batch

Selected dependency: B7 transfer recovery, V147 same-root batch.

Do not run a broad replay next. Do not patch one symptom and replay. The next
implementation batch is:

1. Producer/consumer repair for signed router-refusal source-bound materialization
   so recoverable rows like `62cb...17:45` can become scheduler-rankable without
   using stale executable aliases, unresolved fill-floor failures, or entry-fill
   optimism.
2. Scheduler/finalizer transfer proof so cost-passed, source-complete, fillable
   rows that are still non-order-executable carry exact blocker classes and
   rank/reallocation disposition.
3. Lifecycle/pending-order proof so accepted pending orders terminalize with
   explicit fill/expiry/cancel and risk release, and replacement candidates with
   failed causal gates remain missed with exact reasons.
4. Verifier/focused tests for the new contract before any replay.

### V147 Focused Patch Proof - 2026-07-07T08:18Z

Status: PATCHED, focused proof passed, targeted replay pending.

Same-root B7 repair under test:

- Producer default repair: source-bound router-refusal replay materialization
  now uses execution-fillability floor `0.55`, aligned with selected-policy
  execution fillability, instead of the stale stricter `0.80` materialization
  floor that blocked rows like `62cb...17:45` before scheduler ranking.
- Route profile repair: repaired broad replay profile now forwards
  `scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_fill_probability = 0.55`
  and
  `ultimate_candidate_package_source_bound_router_refusal_materialization_min_fill_probability = 0.55`.
- Consumer proof: `materialize_scheduler_window` now has focused coverage for a
  `62cb`-class source-bound, broker-cost-passed, source-complete,
  execution-fillability `0.551338888` row becoming signed open-reduced
  scheduler-rankable without live broker authority.
- Guard preservation: explicit strong floors still fail below-floor rows; this
  patch does not execute REFUSED cost, source-gap, unresolved fill-floor, live,
  or final rows.

Files changed in the V147 focused patch:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/components/selector_v4.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_broad_replay_repair_config.py`

Focused verification passed:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py src/components/selector_v4.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_broad_replay_repair_config.py`
- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py src/components/selector_v4.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_broad_replay_repair_config.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_broad_replay_repair_config.py -k "repaired_profile_routes_marketable_package_entries_only_in_no_broker_replay" -q`: 1 passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "source_bound_router_refusal_reject_materializes_with_router_floors or source_bound_router_refusal_reject_stays_non_executable_below_strong_floors or source_bound_router_refusal_materialization_uses_execution_fillability_floor or source_bound_router_refusal_materializes_at_selected_policy_execution_floor" -q`: 4 passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "source_bound_router_refusal_signed_authority_uses_materialization_floors or router_refusal_floor_override_requires_structured_proof or ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or ledger_namespace_keeps_signed_source_bound_router_refusal_executable_aliases" -q`: 4 passed.
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "source_bound_router_refusal_signed_authority_requires_execution_fillability_floor or source_bound_router_refusal_open_reduced_releases_zero_risk_with_authority_floors or source_bound_router_refusal_passive_limit_queue_does_not_bypass_execution_authority_floor" -q`: 3 passed.

Targeted replay authorized next:

`BROAD_LIVE_AS_IF_REPLAY_V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`

Success criteria:

- `62cb...17:45` or the same root class becomes signed/rankable/order-eligible,
  or receives a precise downstream blocker.
- Candidate rows and scorecard rows do not collapse through suppression.
- Executed REFUSED/source-gap/unresolved-fill-floor/live/final rows remain zero.
- Added/removed trade keys are causally attributed against V146/V144.
- If R worsens, the result is accepted only as a truth exposure with exact next
  blocker, not as final performance proof.

Patch class:

- Correctness repair: signed materialization/rankability and lifecycle terminal
  truth.
- Diagnostic/ledger repair: explicit blocker-class proof for cost-passed,
  source-complete, fillable missed rows.
- Behavior expectation: neutral to behavior-changing. If the router-refusal
  transfer repair is correct, candidate rows should remain visible, scorecard
  presence should not collapse, `62cb...17:45` or similarly valid rows should
  become rankable/order-eligible only when signed/cost/fill/lifecycle conditions
  pass, and executed REFUSED/source-gap/unresolved-fill-floor/live/final rows
  must remain zero.

Focused proof before replay:

- py_compile on touched code/tests/verifier.
- Focused selector/timewarp/scheduler/verifier tests proving the producer,
  consumer, ledger, and verifier surfaces.
- Only after focused proof: targeted same-window V147 replay on the V146
  five-symbol window/profile. Success is not "more trades"; success is exact
  transfer improvement or exact non-executable classification, with added and
  removed trades causally attributed.

## Current Disk State

- HEAD: `bc609ff0b fix B7 router refusal namespace authority`.
- Active process state: no broad replay, harness, route builder, route verifier,
  pytest, py_compile, or Context OS pack process is running.
- Latest targeted proof: `BROAD_LIVE_AS_IF_REPLAY_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED`.
- Latest full 24-symbol five-day B7 broad proof: `BROAD_LIVE_AS_IF_REPLAY_V128_B7_ROUTER_REFUSAL_DERIVED_IMMEDIATE_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`.
- Authority boundary: broker mutation, live broker authority, and final selection
  remain false; local replay/package evaluation remains full-authority.

## Latest Replay Anchors

| Prefix | Scope | Trades | Net R | Gross/Final R | Cash PnL | W/L/F | Candidate -> Scorecard -> Order -> Fill | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| V144 B7 router-refusal namespace producer repair | 2026-06-01..2026-06-05, 5 symbols | 3 | +0.84449709 | +1.09529478 / +1.09529478 | +84.46094125 | 3/0/0 | 6633 -> 480 -> 15 -> 3 | Targeted proof-surface repair only; behavior-neutral vs V143; unsigned router-refusal executable-authority predicate rows = 0. |
| V128 B7 router-refusal derived immediate authority repair | 2026-06-01..2026-06-05, full 24-symbol | 55 | +1.12099062 | +6.22739670 / +6.22739670 | +3007.28429755 | 38/17/0 | 35191 -> 480 -> 212 -> 55 | Latest full five-day B7 reference; still trails V104 by -13.61002429R and has 0 common V104 canonical trade keys. |

Verifier state: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/VERIFICATION_RESULT.json` is `ok=true`, `issue_count=0`, `verified_utc=2026-07-07T04:58:10Z`.

## Batch Status

| Batch | Status | Requirement Status And Evidence | Remaining Gap | Next Implementation Step |
| --- | --- | --- | --- | --- |
| B0 truth instrumentation baseline | DONE | Baseline audit and cost-refusal histogram exist: `AUDIT_PROVENANCE_AND_FLAGS_V114.json`, `BROKER_COST_REFUSAL_HISTOGRAM_V111.json`. Detailed matrix records V110B/V111 provenance, stale-cap, fallback-expiry, R-accounting, raw-failure, and reallocation histograms. | None. | Keep as fixed baseline for later deltas. |
| B1 provenance truth contract | DONE | Raw/effective selector and R identity contract implemented in `src/components/selector_v4.py`, `src/research_infra/v4_timewarp_simulated_live_research_loop.py`, `src/research/moonshot_scheduler_v4_best_trade_allocator.py`; focused tests in selector, timewarp, scheduler/materialization. V122 B1 proof/verifier green. | None unless later patches reopen raw/effective or R identity. | Do not rerun B1; watch provenance in B7 artifacts. |
| B2 fillability/reallocation truth chain | DONE | Route-resolution family, fill-floor unresolved/raw split, terminal-veto cap cleanup, fallback-time clamp, degraded-queue contract, and tier-demotion context are implemented and test-covered. V122B behavior-neutral targeted proof is recorded. | None unless B7 exposes a regression. | Keep as dependency-complete. |
| B3 risk-expression ladder and loss-bucket demotion | DONE WITH LABEL | Diagnostic exact-block mode, signed package authority requirements, risk-expression ladder producer/consumer, configured-action semantics, and missing-ladder projection repairs are implemented. V122C, V122D, and V122E prove ladder truth; V122D/E no-fill behavior was classified as B4 source/fill realism, not B3 provenance. | Performance is not solved; ladder truth is complete. | Keep ladder fields in every B7 repair and report full/reduced distribution. |
| B4 fill-simulation realism | DONE WITH LABEL | Predecision source-time gates, same-bar ambiguity close, fill-realism classes, diagnostic counterfactual missed expansion, FTMO tick export defaults, lazy tick hash validation, and full 24-symbol hostile tick hydration are implemented. V122J has zero executable M15-proxy/first-touch/source-gap/REFUSED fills and 54 realism-passing fills, but net -3.52793853R. | Behavior remains losing; source/fill truth itself is closed. | Reopen only if B7 exposes a new fill-source realism regression. |
| B5 verifier/comparison precision | DONE | Verifier requires `effective_selector_action`, flags raw-reject/effective-trade leaks, enforces full-risk signing, scopes proof prefixes and selected-package bridge scope, pins expected counts behind snapshots, and comparison/parity tools compute axis-transfer/fill-realism/risk-ladder splits. V122J/V123 verifier/comparison artifacts are green. | None for current dependency ladder. | Keep verifier green after any B7 patch. |
| B6 broker-cost calibration audit | DONE WITH LABEL | B6 audit script/test exist. V122J audit classified 9699 honest refusals, 607 source-gap rows, 12 stale/mapping rows, 7 metadata-review rows. `_broker_cost_tick_from_row` now preserves raw historical predecision bid/ask; V123 USDJPY targeted audit shows 210/210 sampled rows honest, zero stale/mapping. | Remaining cost gaps are labeled and non-executable unless exact same-window recalibration evidence proves otherwise. | Do not loosen REFUSED gate; rerun B6 only if B7 shows new calibrated-cost blocker. |
| B7 full proof ladder | PARTIAL | 7.1 V125 one-day proof green; 7.2 V126 hostile five-day truth-clean but behavior-negative; 7.3 V127B non-hostile five-day truth-clean but behavior-negative; V128 improved V127B but still misses V104 transfer; V129/V138/V142/V144 targeted repairs close specific authority/proof leaks. | 7.4 broad 19-day and 7.5 extended history are open. Current transfer blocker: valid missed winners and V104 winner keys remain candidate/missed but do not reach order/trade; selected transfer/exit/lifecycle/order/reallocation still leak. | Patch next same-root B7 transfer recovery batch from V144/V128 ledgers: rank valid missed winners, separate honest cost/source gaps from recoverable scheduler/materialization/lifecycle/exit blockers, then prove with targeted same-window replay before broad B7.4. |
| B8 live path | OPEN | Fable plan defines production-return dossier, live-shadow with SimulatedBroker, canary micro-live, and scale schedule. No B8 gate is met because B7 is partial. | All B8 requirements remain open. | Do not open live/final. Prepare only after B7.1-B7.5 pass. |

## Selected Next Batch

Selected dependency: B7 transfer recovery.

Do not run a broad replay next. The next action is analysis and code repair on the
same-root B7 transfer blocker:

1. Use V144 targeted ledgers and V128 full five-day ledgers to rank valid missed
   winner keys, including the known V129 winners `bf1a...` and `aa4b...` and the
   recoverable V104 keys identified in current root-cause map.
2. Classify each high-value missed/replaced key as honest broker-cost/source-gap,
   terminal authority veto, scheduler non-selection, lifecycle/same-symbol
   displacement, order/fillability blocker, selected-policy/exit damage, or
   verifier/ledger-only artifact.
3. Patch the highest-leverage recoverable class across producer, consumer,
   ledger, verifier, and focused tests. Do not restore cost-refused/source-gap
   execution and do not suppress opportunities to improve headline R.
4. Run the smallest targeted replay that proves that same-root B7 patch. Run broad
   B7.4 only after targeted transfer behavior is repaired or the blocker is
   precisely proven non-executable.

Expected measurable effect before replay:

- Candidate -> scorecard/order should not collapse through new suppression.
- Scorecard/order -> fill should recover valid cost-passed/source-complete/fillable
  winner paths or explain them as non-executable.
- Missed positive R should fall only by converting valid opportunities or by exact
  non-executable classification; missed negative R must remain visible.
- Net/gross/final R and W/L/F can move either way, but added/removed trades must be
  causally attributed.
- Executed REFUSED/source-gap/live/final counts must remain zero.
- Full-risk/reduced-risk distribution must remain reported separately.

Success: a targeted same-window B7 repair improves valid transfer or exactly
classifies the next limiting blocker while route verifier remains green.

Failure: behavior improves only through trade collapse, any REFUSED/source-gap/live/final
row executes, V104/V129 valid winners remain unexplained, or new B0-B6 truth
contracts regress.

## B7 Checkpoint - 2026-07-07T03:47Z

Selected patch batch: unsigned router-refusal executable authority contract.

Status: PATCHED, focused proof pending.

Changed surfaces:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: selected-package bridge replay materialization is now an explicit passive-limit route family, no longer a generic source-bound boolean alias; selected-bridge source-bound use requires signed bridge authority and canonical source-bound keys.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: selected-bridge fill floor uses the configured fill floor instead of `0.0`; raw router-floor override bool no longer bypasses router floors without structured proof; marketable-immediate fills now fail if applied without routed immediate authority.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: executable-authority leak scans now flag unsigned router-refusal executable aliases in candidate, missed, packet, order, and replay-bridge surfaces.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`, `tests/test_v4_timewarp_simulated_live_research_loop.py`, and `tests/test_denominator_to_deployment_verifier.py`: focused regression coverage for bridge signing, fill-floor enforcement, structured router-floor override proof, unrouted immediate fills, and verifier leak detection.

Focused verification already passed:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py src/research_infra/v4_timewarp_simulated_live_research_loop.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_denominator_to_deployment_verifier.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "session_open_range_break_is_passive_limit_route_resolvable or package_executable_authority_accepts_strict_source_bound_aliases or selected_package_bridge_alias_alone_is_not_source_bound_authority or selected_package_bridge_source_aliases_validate_signed_authority or selected_package_bridge_authority_fails_closed_until_enabled" -q`: 5 passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "candidate_quality_keeps_entry_fill_separate_from_execution_fillability or selected_package_bridge_materialization_enforces_fill_floor or selected_package_bridge_alias_requires_signed_source_bound_authority or router_refusal_floor_override_requires_structured_proof or package_marketable_immediate_route_contract_blocks_unrouted_immediate_fill or package_marketable_immediate_route_contract_blocks_limit_first_fallback or package_marketable_immediate_route_contract_passes_when_immediate_fill_applies" -q`: 7 passed.
- `python3 -m pytest tests/test_denominator_to_deployment_verifier.py -k "replay_bridge_quality_scan_flags_unsigned_router_refusal_executable_alias or order_transfer_scan_flags_unsigned_router_refusal_executable_alias or marketable_route_binding_blocks_non_immediate_order_bound_rows or replay_bridge_quality_scan_requires_compact_and_scorecard_aliases" -q`: 4 passed.

Pre-replay audit on existing V142 artifacts:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V142_B7_MISSED_NAMESPACE_EXECUTABLE_AUTHORITY_DEMOTION_20260601_20260605_TARGETED`.
- Scope: 2026-06-01..2026-06-05, targeted symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.
- Summary counts: 6633 candidate rows, 480 scorecards, 15 order rows, 3 trades, 6626 missed rows, 7120 packet sidecar rows.
- Headline behavior: 3 trades, net R +0.84449709, gross/final R +1.09529478 / +1.09529478, cash PnL +211.19447407, W/L/F 3/0/0.
- Unsigned router-refusal executable-authority predicate rows: candidate 1980, missed 1980, packet sidecar 1905, scorecard 0, order 0, trade 0, total 5865.
- Audit artifact: `.context/context_os/B7_UNSIGNED_ROUTER_REFUSAL_AUTHORITY_PRE_REPLAY_AUDIT_20260707.json`.

Next proof:

- Run targeted V143 on the same V142 window/symbol/profile scope, not a broad replay.
- Success requires unsigned router-refusal executable-authority predicate rows to fall to zero on candidate, missed, packet, order, and trade ledgers while executed REFUSED/source-gap/live/final rows stay zero.
- Candidate -> scorecard -> order -> fill counts, net/gross/final R, cash PnL, W/L/F, expired rows, missed scoreability, and added/removed trade keys must be reported.
- If V143 worsens R, treat it as acceptable only if the truth-contract repair explains the delta and exposes the next B7 transfer blocker without suppressing all opportunity.

## B7 Checkpoint - 2026-07-07T04:15Z

V143 result: FAILED focused proof, then patched producer root cause.

V143 completed with broker/live/final closed and no REFUSED/source-gap execution:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V143_B7_UNSIGNED_ROUTER_REFUSAL_EXECUTABLE_AUTHORITY_CONTRACT_20260601_20260605_TARGETED`.
- Counts remained unchanged versus V142: 6633 candidates, 480 scorecards, 15 order rows, 3 trades, 6626 missed rows, 7120 packet sidecar rows.
- Behavior remained unchanged in R terms: 3 trades, net R +0.84449709, gross/final R +1.09529478 / +1.09529478, W/L/F 3/0/0. Cash PnL changed from +211.19447407 to +84.46094125 while trade keys stayed common 3/3; this needs later cash-sizing/cost attribution if it recurs after the namespace proof closes.
- Unsigned router-refusal executable-authority predicate rows did not improve: candidate 1980, missed 1980, packet sidecar 1905, scorecard 0, order 0, trade 0, total 5865.
- Post-replay audit artifact: `.context/context_os/B7_UNSIGNED_ROUTER_REFUSAL_AUTHORITY_POST_REPLAY_AUDIT_20260707_V143.json`.

Root cause exposed by V143:

- The prior patch added detection and blocked order/trade execution, but `ledger_namespace_alias_fields()` still allowed source-bound router-refusal materialization rows to advertise `package_replay_candidate_use_allowed`, `package_replay_executable_candidate_use_allowed`, and `replay_candidate_use_allowed_now` from stale bool aliases even when `package_new_entry_authority_valid=false`.
- Two lifecycle materialization bridges also set executable aliases before signed authority/floor validation; order execution was still false, but candidate/missed/packet namespace truth remained wrong.

Second producer patch:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py` now adds `source_bound_router_refusal_signed_namespace_authority_valid()` and `source_bound_router_refusal_unsigned_namespace_block_reason()`.
- `ledger_namespace_alias_fields()` now keeps source-bound/admission diagnostic fields scoreable, but demotes executable namespace aliases for source-bound router-refusal materialization unless valid signed new-entry authority is present.
- Focused regression tests added:
  - `test_ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases`
  - `test_ledger_namespace_keeps_signed_source_bound_router_refusal_executable_aliases`

Focused verification after second patch:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or ledger_namespace_keeps_signed_source_bound_router_refusal_executable_aliases" -q`: 2 passed.

Next proof:

- Run targeted V144 on the same V142/V143 window/symbol/profile scope.
- Success criteria are unchanged: unsigned router-refusal executable-authority predicate rows must fall to zero in candidate, missed, packet sidecar, scorecard, order, and trade ledgers; REFUSED/source-gap/live/final execution stays zero; candidate/order/fill transfer remains explicit.

## B7 Checkpoint - 2026-07-07T04:42Z

V144 result: PASSED focused proof.

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED`.

Behavior versus V143:

- Candidate rows: 6633, delta 0.
- Scorecard rows: 480, delta 0.
- Order rows: 15, delta 0.
- Trade rows: 3, delta 0.
- Missed rows: 6626, delta 0.
- Packet sidecar rows: 7120, delta 0.
- Net R: +0.84449709, delta 0.
- Gross/final R: +1.09529478 / +1.09529478, delta 0 / 0.
- Cash PnL: +84.46094125, delta 0 versus V143.
- W/L/F: 3/0/0, delta 0/0/0.
- Trade-key delta versus V143: 3 common, 0 added, 0 removed.
- Missed positive/negative R: 0.0 / 0.0.
- Missed executable scoreable R: 0.0.
- Order status counts: expired_unfilled 4, filled 3.
- Cost dispositions: 3285 scoreable cost-refused non-executable diagnostics; 3341 cost-authority-not-primary miss reason rows.

Truth-contract result:

- Unsigned router-refusal executable-authority predicate rows: candidate 0, missed 0, packet sidecar 0, scorecard 0, order 0, trade 0.
- Executed REFUSED rows: 0.
- Executed source-gap rows: 0.
- Broker mutation, live broker authority, and final selection remain false.

Post-replay audit artifact:

- `.context/context_os/B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_POST_REPLAY_AUDIT_20260707_V144.json`.

Route companion artifacts materialized after replay:

- `BIG_R_PROVENANCE_BREAKDOWN_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED.json`.
- `SOURCE_BOUND_TO_EXECUTED_PARITY_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED_LEDGER.jsonl` and `_SUMMARY.json`: 5461 parity rows.
- `EXECUTION_LEAKAGE_BUCKET_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED_LEDGER.jsonl`: 1101 leakage bucket rows.
- `EXECUTION_LEAKAGE_REPAIR_PLAN_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED.json`.
- `BROAD_LIVE_AS_IF_REPLAY_V144_B7_ROUTER_REFUSAL_NAMESPACE_PRODUCER_REPAIR_20260601_20260605_TARGETED_FLOW_DIAGNOSTIC_SUMMARY.json`, `_FLOW_BUCKET_LEDGER.jsonl`, and `_FLOW_DIAGNOSTIC_DOSSIER.md`: 441 flow bucket rows.

Final route verification:

- `OUTPUT_MANIFEST.json`, `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`, and `.context/context_os/CONTINUATION_CURSOR.json` now point the default broad-quality parity surface at V144.
- `python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: `ok=true`, `issue_count=0`, selected prefix V144, `final_package_selected=false`, `live_trading_enabled=false`, verified at 2026-07-07T04:58:10Z.

Final focused checks:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py src/research_infra/v4_timewarp_simulated_live_research_loop.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_denominator_to_deployment_verifier.py`: passed.
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "session_open_range_break_is_passive_limit_route_resolvable or package_executable_authority_accepts_strict_source_bound_aliases or selected_package_bridge_alias_alone_is_not_source_bound_authority or selected_package_bridge_source_aliases_validate_signed_authority or selected_package_bridge_authority_fails_closed_until_enabled" -q`: 5 passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "candidate_quality_keeps_entry_fill_separate_from_execution_fillability or selected_package_bridge_materialization_enforces_fill_floor or selected_package_bridge_alias_requires_signed_source_bound_authority or router_refusal_floor_override_requires_structured_proof or package_marketable_immediate_route_contract_blocks_unrouted_immediate_fill or package_marketable_immediate_route_contract_blocks_limit_first_fallback or package_marketable_immediate_route_contract_passes_when_immediate_fill_applies or ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or ledger_namespace_keeps_signed_source_bound_router_refusal_executable_aliases" -q`: 9 passed.
- `python3 -m pytest tests/test_denominator_to_deployment_verifier.py -k "replay_bridge_quality_scan_flags_unsigned_router_refusal_executable_alias or order_transfer_scan_flags_unsigned_router_refusal_executable_alias or marketable_route_binding_blocks_non_immediate_order_bound_rows or replay_bridge_quality_scan_requires_compact_and_scorecard_aliases" -q`: 4 passed.
- `python3 scripts/validate_goal_prompt_hardening.py --kind builder --json ...ULTIMATE_SYSTEM_DENOMINATOR_TO_DEPLOYMENT_GOAL_PROMPT.md ...ULTIMATE_SYSTEM_DENOMINATOR_TO_DEPLOYMENT_STARTER.md`: `ok=true`.
- `python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20 --profile standard`: `ok=true`, `missing_required=[]`, `missing_warnings=[]`.

Interpretation:

- This batch is a correctness/proof-surface repair, not a performance gain.
- It removed the candidate/missed/packet executable-authority namespace leak without suppressing trades or changing the same-window trade set.
- B7 remains PARTIAL because transfer recovery is still open: V144 still has only 3 fills in this targeted five-symbol slice and V128/V104 transfer gaps remain the next B7 issue class.

## B7 Checkpoint - 2026-07-07T05:46Z

Selected patch batch: selector admission transfer plus selected-policy stop-hazard quality consumer parity.

Status: PATCHED, focused proof passed, targeted replay pending.

Subagent findings incorporated:

- Goodall: source-bound router-refusal materialization must use execution fillability, not entry-quality fill optimism; diagnostic `package_replay_candidate_use_allowed` is scoreable/proof-surface only and must not be a verifier-fatal executable alias.
- Kepler: V144 priority 12/13 selected-package source/lifecycle materialization rows are diagnostic classification gaps in this slice, with zero candidate trace/source-bound/actual/missed R; no behavior patch should promote them into candidates/orders for V145.
- Popper: V128 `selected_policy_replay:stop_loss` is a material losing bucket (13 fills / `-14.31653698R`) and suppressed/score-triggered stop-hazard pressure can remain executable when the direct pressure trigger is false. This is a B7 selected-policy transfer/exit quality leak.

Changed surfaces:

- `src/components/selector_v4.py`: source-bound router-refusal materialization uses execution fill probability only; entry-quality fill probability is retained as diagnostic context but cannot bypass the execution-fillability floor.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: `ledger_namespace_alias_fields()` preserves diagnostic candidate-use while demoting executable aliases until signed/materialized scheduler authority exists.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: `selected_policy_executable_quality_gate_fields()` treats suppressed score-triggered stop-hazard pressure as a causal predecision hazard; finalizer rank, soft-veto probing, finalizer selection, replay-exit, filled-trade, and missed-opportunity consumers use route runtime thresholds.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: unsigned router-refusal executable leak scan excludes diagnostic candidate-use but keeps true executable/order/replay-now aliases fatal.
- `tests/test_selector_v4.py`, `tests/test_v4_timewarp_simulated_live_research_loop.py`, and `tests/test_denominator_to_deployment_verifier.py`: focused regression coverage for execution-fillability floor authority, diagnostic/executable namespace split, suppressed selected-policy stop pressure, runtime-threshold propagation, and blocked selected-policy authority leaks.

Focused verification passed:

- `python3 -m py_compile src/components/selector_v4.py src/research_infra/v4_timewarp_simulated_live_research_loop.py src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_selector_v4.py tests/test_timewarp_scheduler_materialization.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `python3 -m pytest tests/test_selector_v4.py -k "source_bound_router_refusal_materializes_without_origin_allowlist or source_bound_router_refusal_respects_execution_fill_floor or package_router_refusal_softening_uses_signed_sleeve_origin" -q`: 3 passed.
- `python3 -m pytest tests/test_timewarp_scheduler_materialization.py -k "reduce_risk_numeric_open_reduced_disabled_stays_rankable_as_reduce_risk or package_positive_numeric_disagreement_reduce_risk_reaches_scheduler_with_cost_passed or nonpackage_reduce_risk_new_entry_does_not_reach_scheduler or package_positive_reduce_risk_keeps_refused_cost_blocked" -q`: 4 passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "source_bound_router_refusal_materialization_uses_execution_fillability_floor or ledger_namespace_demotes_unsigned_source_bound_router_refusal_executable_aliases or ledger_namespace_alias_keeps_raw_router_rejects_diagnostic_only or scheduler_backfill_refresh_restores_materialized_router_refusal_authority or package_router_refusal_authority_daily_loss_release_is_narrow_replay_path" -q`: 5 passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "selected_policy_quality_gate or selected_execution_policy_replay_blocks_predecision_quality_failure_before_path or selected_execution_policy_replay_uses_runtime_quality_thresholds or finalizer_admission_rank_uses_runtime_selected_policy_pressure_floor or risk_finalizer_blocks_selected_policy_hazard_before_selection" -q`: 7 passed.
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "source_bound_router_refusal_passive_limit_queue_does_not_bypass_execution_authority_floor or package_executable_authority_accepts_strict_source_bound_aliases or selected_package_bridge_alias_alone_is_not_source_bound_authority" -q`: 3 passed.
- `python3 -m pytest tests/test_denominator_to_deployment_verifier.py -k "replay_bridge_quality_scan_flags_unsigned_router_refusal_executable_alias or unsigned_router_refusal_diagnostic_candidate_use_is_not_executable_alias or order_transfer_scan_flags_unsigned_router_refusal_executable_alias" -q`: 3 passed.
- `python3 -m pytest tests/test_denominator_to_deployment_verifier.py -k "broad_selected_policy_replay_authority_flags_quality_gate_leaks" -q`: 1 passed.

Next proof:

- Run targeted V145 on the V144 five-symbol window/symbol/profile scope, not a broad replay.
- Success requires broker/live/final false, executed REFUSED/source-gap rows zero, unsigned router-refusal executable-authority predicate rows still zero, and selected-policy quality-gate blocked rows not reaching executable filled order/trade authority.
- V145 must report candidate -> scorecard -> order -> fill counts, net/gross/final R, cash PnL, W/L/F, missed positive/negative R, selected-policy quality-gate blocker counts, added/removed trade keys, and whether any improvement came from conversion, selected-policy quality repair, or suppression.

## B7 Checkpoint - 2026-07-07T06:15Z

V145 result: mixed transfer proof; exposed unresolved fill-floor execution authority leak.

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V145_B7_SELECTOR_ADMISSION_TRANSFER_AND_SELECTED_POLICY_QUALITY_20260601_20260605_TARGETED`.

V145 behavior versus V144:

- Candidate rows: 6633, delta 0.
- Scorecard rows: 480, delta 0.
- Finalizer terminal orders: 7, delta 0.
- Summary order rows: 14 versus 15 in V144.
- Trade rows: 3, delta 0.
- Net R: `+0.18335355`, delta `-0.66114354`.
- Gross/final R: `+0.48352934 / +0.48352934`, delta `-0.61176544 / -0.61176544`.
- Cost R: `+0.30017579`, delta `+0.04937810`.
- W/L/F: 2/1/0 versus 3/0/0.
- Added trades: 2 XAUUSD SHORT rows, net `+1.12241840R` and `-1.10446455R`.
- Removed trades: 2 V144 rows, net `+0.29090804R` and `+0.38818935R`.
- Common trades: 1, net `+0.16539970R`.
- Executed REFUSED/source-gap/live/final rows: 0.

Truth leak exposed:

- V145 had 8 order/trade rows across 3 unique keys carrying unresolved fill-floor failures into order/trade surfaces.
- Failure names: `fill_probability_below_execution_authority_floor` and `numeric_disagreement_fill_probability`.
- The leak is not missing data. These rows are scoreable/missed opportunities until the fill-floor authority resolves; they cannot be executable order/trade authority.

Selected patch batch: unresolved fill-floor execution authority repair.

Changed surfaces:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: signed package fill-floor execution failures now invalidate reduce-risk package replay authority for all signed entry intents; explicit reduce-risk authority cannot bypass unresolved fill-floor failures.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: unresolved fill-floor failure keys propagate through order-materialization authority surfaces.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: order materialization, replay-order block reason, and final blocker now fail closed before stale allowed aliases can bind an order or trade.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: shared unresolved fill-floor extraction is verifier-fatal for order executable transfer and selected-package executed order/trade authority.
- `tests/test_timewarp_scheduler_materialization.py`, `tests/test_v4_timewarp_simulated_live_research_loop.py`, and `tests/test_denominator_to_deployment_verifier.py`: focused tests cover scheduler fail-closed authority, timewarp order-surface/blocker consumers, and verifier fatal scans.

Focused verification passed:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py src/research_infra/v4_timewarp_simulated_live_research_loop.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py tests/test_timewarp_scheduler_materialization.py tests/test_v4_timewarp_simulated_live_research_loop.py tests/test_denominator_to_deployment_verifier.py`
- `python3 -m pytest tests/test_timewarp_scheduler_materialization.py -k "signed_reduce_risk_package_authority_requires_resolved_fill_floor or package_positive_numeric_disagreement_reduce_risk_reaches_scheduler_with_cost_passed or package_positive_reduce_risk_keeps_refused_cost_blocked" -q`: 3 passed.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "package_order_executable_final_blocker_blocks_unresolved_fill_floor_binding or order_materialization_surface_blocks_unresolved_fill_floor_stale_allowed or replay_order_materialization_blocks_unresolved_fill_floor_stale_allowed or risk_finalizer_blocks_unresolved_fill_floor_probe_execution or risk_finalizer_primary_probe_alias_prefers_selected_policy_blocked_probe or selected_policy_quality_gate or selected_execution_policy_replay_uses_runtime_quality_thresholds" -q`: 9 passed.
- `python3 -m pytest tests/test_denominator_to_deployment_verifier.py -k "broad_order_executable_transfer_scan_flags_unresolved_package_fill_floor_execution or selected_package_executed_authority_scan_flags_unresolved_package_fill_floor_order_trade or broad_emitted_scheduler_status_authority_scan_flags_ranked_package_leak or replay_bridge_quality_scan_flags_unsigned_router_refusal_executable_alias or unsigned_router_refusal_diagnostic_candidate_use_is_not_executable_alias or order_transfer_scan_flags_unsigned_router_refusal_executable_alias or broad_selected_policy_replay_authority_flags_quality_gate_leaks" -q`: 7 passed.

Next proof:

- Run targeted V146 on the same V145 five-symbol window/symbol/profile scope, not a broad replay.
- Success requires zero order/trade rows with unresolved fill-floor failures, zero executed REFUSED/source-gap/live/final rows, and exact added/removed/common trade attribution versus V145 and V144.
- If V146 removes V145 trades without reallocation, classify the missed opportunities and keep B7 open; do not count trade collapse as performance proof.

## B7 Checkpoint - 2026-07-07T07:24Z

V146 result: PASSED focused truth proof, B7 remains PARTIAL.

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED`.

Scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.

Behavior:

- Candidate rows: 6633.
- Scorecard rows: 480.
- Order rows: 10.
- Trade rows: 2.
- Missed rows: 6628.
- Net R: `+0.55358905`.
- Gross/final R: `+0.72340378 / +0.72340378`.
- Cost R: `+0.16981473`.
- Cash PnL: `+55.36532564`.
- W/L/F: 2/0/0.
- Order statuses: `pending_accepted=5`, `expired_unfilled=3`, `filled=2`.
- Filled risk decisions: `open-reduced-risk=2`.
- Broker mutation, live broker authority, and final selection remain false.

V146 versus V145:

- Trade delta: `-1`.
- Net R delta: `+0.37023550`.
- Gross/final R delta: `+0.23987444 / +0.23987444`.
- Cost R delta: `-0.13036105`.
- Cash PnL delta: `+35.11107348`.
- Added one V144 winner back: `broadorigin_e59c330b1467251e45c3fd09@@2026-06-04T18:15:00+00:00`, `+0.38818935R`.
- Removed V145 unresolved fill-floor trades: `broadorigin_b8a223d65d654f26188d842f@@2026-06-04T14:30:00+00:00`, `-1.10446455R`; and `broadorigin_bf1a01f81a62731eb07810e1@@2026-06-04T07:30:00+00:00`, `+1.12241840R`.

V146 versus V144:

- Trade delta: `-1`.
- Net R delta: `-0.29090804`.
- Removed V144 valid winner: `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`, XAUUSD LONG, `moonshot_h17_18`, `+0.29090804R`.

Truth-contract result:

- V145 unresolved fill-floor order/trade execution leak: 8 order/trade rows across 3 unique keys.
- V146 unresolved fill-floor order/trade rows: 0.
- V146 keeps unresolved fill-floor reasons scoreable in scorecard/missed ledgers only; they no longer bind executable order/trade authority.
- Executed REFUSED/source-gap/live/final rows: 0.

Route companion artifacts:

- `.context/context_os/V146_B7_UNRESOLVED_FILL_FLOOR_TARGETED_BEHAVIOR_REPORT.md`.
- `.context/context_os/V146_B7_UNRESOLVED_FILL_FLOOR_TARGETED_STRICT_PARSE.json`.
- `BIG_R_PROVENANCE_BREAKDOWN_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED.json`.
- `SOURCE_BOUND_TO_EXECUTED_PARITY_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED_LEDGER.jsonl` and `_SUMMARY.json`: 5461 parity rows.
- `EXECUTION_LEAKAGE_BUCKET_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED_LEDGER.jsonl`: 1101 leakage bucket rows.
- `EXECUTION_LEAKAGE_REPAIR_PLAN_V146_B7_UNRESOLVED_FILL_FLOOR_EXECUTION_AUTHORITY_REPAIR_20260601_20260605_TARGETED.json`.
- V146 flow summary, flow bucket ledger, and flow dossier: 438 flow bucket rows.

Verification:

- `python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: `ok=true`, `issue_count=0`, verified at 2026-07-07T07:19:06Z.
- Manifest registration was repaired by adding the V146 broad-quality artifact set to `OUTPUT_MANIFEST.json` `files` as well as `broad_quality_parity_files`; the initial verifier failure was `manifest_missing` only.

Interpretation:

- This is a correctness repair and proof-surface repair, with behavior impact.
- It improved versus V145 by removing unresolved-fill-floor executable authority, but it is not a complete transfer recovery proof.
- B7 remains PARTIAL because V146 still fills only 2 trades in this targeted slice and loses one valid V144 winner.

Next same-root B7 batch:

1. Rank V146 leakage buckets by recoverable missed positive R and correctness impact.
2. Explain or recover the removed V144 winner `62cb...17:45` without re-opening unresolved fill-floor execution.
3. Patch the next producer/consumer chain across scheduler/reallocation, order/fillability, lifecycle, exit, ledger, verifier, and focused tests.
4. Run a targeted proof only after that same-root batch is patched; do not run a broad B7.4 replay yet.

## B7 Checkpoint - 2026-07-07T16:19Z

V151F result: PASSED focused producer/consumer/verifier proof, B7 remains
PARTIAL. No replay was run; V150 remains the latest behavior proof.

Batch: stable-window lifecycle transfer status for selected-package bridge
materialization.

Changed surfaces:

- `build_denominator_to_deployment_execution.py`: source-member rows now emit
  `source_axis_lifecycle_bridge_window_transfer_status`,
  `source_materialization_transfer_status`,
  overlap counts/samples, and transfer boundary.
- `build_source_bound_execution_parity.py`: parity labels now consume the
  transfer status and split the old generic stable-window mismatch label.
- `verify_denominator_to_deployment_execution.py`: verifier now fails lifecycle
  context rows missing transfer status, unknown status, inconsistent
  source-materialization status, or impossible overlap/source-window states.
- `tests/test_build_source_bound_execution_parity.py` and
  `tests/test_denominator_to_deployment_verifier.py`: focused coverage for
  producer helper, split labels, repair-stage mapping, and verifier fatal
  contract.

Producer status counts from rebuilt denominator ledgers:

- `source_window_missing`: 607.
- `no_axis_lifecycle_context`: 371.
- `bridge_window_mismatch`: 81.
- `bridge_window_missing`: 31.
- `bridge_window_overlap`: 11.

V151F parity source-member leakage labels:

- `source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_source_window_missing`: 255.
- `source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_bridge_window_mismatch`: 38.
- `source_axis_selected_package_bridge_materialized_stable_window_lifecycle_label_context`: 28.
- `source_axis_selected_package_bridge_materialized_no_lifecycle_label_context`: 162.
- `selected_package_lifecycle_context_without_current_replay_source_materialization`: 79.
- `selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap`: 21.

V151F parity row transfer-status counts:

- `source_window_missing`: 3381.
- `no_axis_lifecycle_context`: 998.
- `bridge_window_mismatch`: 659.
- `bridge_window_overlap`: 356.
- `bridge_window_missing`: 67.

Artifacts:

- `SOURCE_BOUND_TO_EXECUTED_PARITY_V151F_B7_STABLE_WINDOW_LIFECYCLE_TRANSFER_20260601_20260605_TARGETED_SUMMARY.json`.
- `SOURCE_BOUND_TO_EXECUTED_PARITY_V151F_B7_STABLE_WINDOW_LIFECYCLE_TRANSFER_20260601_20260605_TARGETED_LEDGER.jsonl`.
- `EXECUTION_LEAKAGE_BUCKET_V151F_B7_STABLE_WINDOW_LIFECYCLE_TRANSFER_20260601_20260605_TARGETED_LEDGER.jsonl`.
- `EXECUTION_LEAKAGE_REPAIR_PLAN_V151F_B7_STABLE_WINDOW_LIFECYCLE_TRANSFER_20260601_20260605_TARGETED.json`.
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260707T1619Z_V151F_STABLE_WINDOW_LIFECYCLE_TRANSFER_POSTPATCH.json`.

Verification:

- `python3 -m py_compile ...`: passed, `.codex_run_logs/v151f_py_compile.log`.
- Focused parity pytest: 5 passed, 75 deselected,
  `.codex_run_logs/v151f_parity_focused_pytest.log`.
- Focused verifier pytest: 1 passed, 124 deselected,
  `.codex_run_logs/v151f_verifier_focused_pytest.log`.
- Route verifier: exit 0, `.codex_run_logs/v151f_route_verifier.log`.
- Prompt hardening: `overall_ok=True`,
  `.codex_run_logs/v151f_prompt_hardening.json`.
- Route artifact audit: rerun passed with `ok=True`, `file_count=5681`,
  `jsonl_read_error_count=0`, `.codex_run_logs/v151f_route_artifact_audit_rerun.json`.
- Scoped `git diff --check`: passed,
  `.codex_run_logs/v151f_git_diff_check_scoped.log`.

Transient audit issue repaired:

- First artifact-audit pass failed on four JSONL files with
  `OSError: [Errno 89] Operation canceled` before row 1.
- Direct reads of the exact four files succeeded after hydration delay.
- Rerun scanned cleanly with zero JSON/JSONL parse or read errors.

Interpretation:

- This is a correctness and diagnostic transfer repair, not a behavior proof.
- It removed the broad generic lifecycle-context mismatch bucket and replaced
  it with executable transfer classes.
- It does not prove full reservoir conversion, and it does not change V150
  trade count or R because no runtime replay was run.

Next same-root B7 batch:

1. Recover or classify `source_window_missing` lifecycle labels from row-bound
   decision-time evidence.
2. Repair bridge decision-window derivation for the `bridge_window_mismatch`
   rows where source and bridge windows should overlap.
3. Keep pending-created proxy-only rows non-executable unless original
   decision time is recovered.
4. Add verifier/tests for that recovery path, rebuild route artifacts, then
   run the smallest targeted behavior proof only if runtime consumers change.

## B7 Checkpoint - 2026-07-07T17:21Z

V152 result: PASSED focused producer/consumer/verifier proof, B7 remains
PARTIAL. No replay was run; V150 remains the latest behavior proof.

Batch: source-window recovery classification and bridge-window mismatch
subclassification for selected-package bridge lifecycle context.

Changed surfaces:

- `build_denominator_to_deployment_execution.py`: `source_window_missing`
  now splits into pending-created proxy-only, exact decision-time recovered, or
  capture-required classes. Bridge-window mismatch rows now carry
  same-trading-day versus different-trading-day subreason.
- `build_source_bound_execution_parity.py`: parity labels now consume the
  recoverability and mismatch subreasons instead of the generic
  `source_window_missing` / `bridge_window_mismatch` labels.
- `verify_denominator_to_deployment_execution.py`: verifier now fails closed
  when lifecycle transfer status is missing its required supporting counts or
  when pending-created proxy context is promoted as exact decision-time truth.
- `tests/test_build_source_bound_execution_parity.py` and
  `tests/test_denominator_to_deployment_verifier.py`: focused coverage for the
  new recoverability statuses, mismatch subreasons, parity labels, repair-stage
  mapping, and verifier count contract.

Producer status counts from rebuilt denominator ledgers:

- `source_window_missing_pending_created_proxy_only`: 607.
- `no_axis_lifecycle_context`: 371.
- `bridge_window_mismatch`: 81.
- `bridge_window_missing`: 31.
- `bridge_window_overlap`: 11.

Producer recoverability counts:

- `pending_created_proxy_only_not_exact_decision_time`: 607.
- `no_axis_lifecycle_context`: 371.
- `source_decision_window_present`: 123.

Producer bridge mismatch counts:

- `source_window_missing`: 978.
- `same_trading_day_different_decision_window`: 55.
- `bridge_window_missing`: 31.
- `different_trading_day_decision_window`: 26.
- `bridge_window_overlap`: 11.

V152 parity source-member leakage labels:

- `source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_source_window_missing_pending_created_proxy_only`: 255.
- `source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_bridge_window_mismatch_same_trading_day_different_decision_window`: 29.
- `source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_bridge_window_mismatch_different_trading_day_decision_window`: 9.
- `source_axis_selected_package_bridge_materialized_stable_window_lifecycle_label_context`: 28.
- `source_axis_selected_package_bridge_materialized_no_lifecycle_label_context`: 162.
- `selected_package_lifecycle_context_without_current_replay_source_materialization`: 79.
- `selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap`: 21.

V152 parity row transfer-status counts:

- `source_window_missing_pending_created_proxy_only`: 3381.
- `no_axis_lifecycle_context`: 998.
- `bridge_window_mismatch`: 659.
- `bridge_window_overlap`: 356.
- `bridge_window_missing`: 67.

V152 repair-plan top action:

- `observed_axis_rows`: 293.
- `diagnostic_source_bound_r_sum`: 481369.7478256909.
- `label_counts`: 255 pending-created proxy-only source-window rows, 29
  same-day bridge-window mismatch rows, and 9 different-day bridge-window
  mismatch rows.

Artifacts:

- `SOURCE_BOUND_TO_EXECUTED_PARITY_V152_B7_SOURCE_WINDOW_RECOVERY_BRIDGE_MISMATCH_CLASSIFICATION_20260601_20260605_TARGETED_SUMMARY.json`.
- `SOURCE_BOUND_TO_EXECUTED_PARITY_V152_B7_SOURCE_WINDOW_RECOVERY_BRIDGE_MISMATCH_CLASSIFICATION_20260601_20260605_TARGETED_LEDGER.jsonl`.
- `EXECUTION_LEAKAGE_BUCKET_V152_B7_SOURCE_WINDOW_RECOVERY_BRIDGE_MISMATCH_CLASSIFICATION_20260601_20260605_TARGETED_LEDGER.jsonl`.
- `EXECUTION_LEAKAGE_REPAIR_PLAN_V152_B7_SOURCE_WINDOW_RECOVERY_BRIDGE_MISMATCH_CLASSIFICATION_20260601_20260605_TARGETED.json`.
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260707T1721Z_V152_B7_SOURCE_WINDOW_RECOVERY_BRIDGE_MISMATCH_POSTPATCH.json`.

Verification:

- `python3 -m py_compile ...`: passed.
- Focused parity pytest: 9 passed, 71 deselected.
- Focused verifier pytest: 1 passed, 124 deselected.
- Route verifier: `ok=true`, `issue_count=0`, verified at
  `2026-07-07T17:21:19Z`.
- Prompt hardening:
  `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_goal_2026_06_20/ULTIMATE_SYSTEM_DENOMINATOR_TO_DEPLOYMENT_GOAL_PROMPT.md`
  passed with `overall_ok=True`.
- Route artifact audit: passed with `ok=true`, `missing_required=[]`, and
  `missing_warnings=[]`.
- Scoped `git diff --check`: passed.
- Parent full-plan verifier was run as an adjacent check and failed on VPS
  freshness drift only: `parent_vps_head_not_current`,
  `current_vps_package_guard_not_current`,
  `vps_ai_companion_head_not_current`,
  `broker_close_history_search_vps_head_not_current`. This is not a B7 route
  verifier failure.

Interpretation:

- This is a correctness and diagnostic transfer repair, not a behavior proof.
- It proves the old generic `source_window_missing` rows are pending-created
  proxy-only on current disk evidence, not recovered historical
  `decision_time_utc` truth.
- It proves the old generic `bridge_window_mismatch` class splits into
  same-day and different-day mismatch rows, giving the next repair a precise
  same-root target.
- It does not change V150 trade count or R because no runtime replay was run.

Next same-root B7 batch:

1. For same-day bridge-window mismatch rows, inspect bridge decision-window
   derivation and repair producer/consumer alignment if the source and bridge
   windows should resolve to the same predecision slot.
2. Keep the 607 pending-created proxy-only source-window rows non-executable
   for exact lifecycle truth unless original `decision_time_utc` is recovered
   by source evidence or prospective capture.
3. Keep different-day bridge-window mismatch rows diagnostic until source
   evidence proves they are same-decision candidates rather than replay-window
   drift.
4. Run a targeted proof only if the next patch changes runtime consumers.
