# Session 63 vNext Exact-R Source-Repair Guard Handoff - 2026-05-19

## Current Head And Status

- Runtime checkpoint HEAD at handoff authoring: `310622d0a runtime: convert moonshot exact r missing proof guard`.
- This handoff is intended to be committed immediately after `310622d0a`; use `git log -1 --oneline` after checkout for the final handoff commit hash.
- Working tree status before staging this handoff:
  - Modified but intentionally unstaged: `.context/LIVE_STATE.md` from mandatory preflight regeneration.
  - Large pre-existing untracked `.pytest-tmp-*` directories, untracked research review artifacts, archived divergence files, and `shadow_logs/equity_read_anomalies_2026-05-12.jsonl.gz` remain untouched.
  - No owned runtime/config/test edits are left uncommitted after `310622d0a`.
- Do not clean/reset the worktree broadly. The untracked files predate this handoff and were not part of the checkpoint.

## Active Correction Rules To Preserve

- Active queue is freshness and impact driven, not chronological old handoff order.
- Primary target remains CP280/CP281/CP282 frozen moonshot row-bearing artifacts and high-impact repair-needed units.
- Do not open one old builder/verifier/manifest/summary wrapper at a time when the wrapper class repeats; batch-dispose wrappers only when they are non-runtime and superseded by CP280/CP281/CP282 row-bearing/runtime artifacts.
- No owner/broker-R chase. Simulated/proxy-R, source-bound row-bearing research, and current runtime artifacts are valid system-conversion inputs.
- Repair-needed is not a graveyard: every repair row needs exact missing field/source, runtime surface, and executable code/config/test action.
- Every future checkpoint must produce runtime/code/config/test behavior, row-bearing conversion, executed source repair, or a tested kill/superseded decision.
- Do not reopen USDJPY FOLLOW/AVOID or other closed regressions except as guards when matcher changes touch them.

## Latest Conversion Counts

From `research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_SUMMARY_2026-05-18.json` after `310622d0a`:

- Total intelligence units: `13,395`
- Converted units: `69`
- Implemented units: `20`
- Killed units: `1,116`
- Repair-action-defined units: `183`
- Not-started units: `12,007`
- Delta since previous checkpoint: converted `+1`, implemented `+0`, killed `+0`, repair `+0`, not-started `+0`, total `+1`
- Current unit consumed: `MANUAL_RUNTIME_MOONSHOT_EXACT_R_MISSING_PROOF_SOURCE_REPAIR_GUARD`
- Current conversion state: `CONVERTED_RISK_SIZING_RULE`
- Next unit pointer: `UNIT_001385`

The total/not-started delta follows the existing manual-conversion-row ledger pattern. Do not spend a checkpoint trying to cosmetically normalize counts if runtime behavior and tests are already correct.

## Last Committed Runtime Behaviors

`310622d0a` converted the CP280/CP281/CP282 row-bearing exact-R/missing-proof ledger:

- Source artifact:
  `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_EXACT_R_OR_MISSING_PROOF_LEDGER_2026-05-17.jsonl`
- Full artifact dimensions consumed: `17,916` rows, `0` exact-R value rows, `10,597` broker execution geometry missing rows, `7,045` source-join absent rows, `274` spread-proxy-only rows.
- Runtime now enriches exact-R/missing-proof rows into `moonshot_exact_r_missing_proof` evidence with:
  - `r_evidence_class=SOURCE_REPAIR_FOR_EXACT_R`
  - `source_group=exact_r_missing_proof`
  - `source_role=exact_r_source_repair_proof`
  - `system_surface=exact_r_source_repair_runtime_guard`
  - implementation actions mapped from `exact_r_status`
  - attached `exact_missing_field_proof`, branch match status, sidecar join flag, matched branch queue id, and input execution row id
- The GBPJPY `tokyo_kz` `nofill_far_miss_avoid` cohort matches `1,184` rows and resolves `MIXED`, not directional AVOID/FOLLOW.
- With execution activation enabled, that cohort now drives `vnext_risk_source_repair_required` to zero risk and blocks execution through the existing vNext risk block path.
- The enrichment is path-scoped to the exact-R/missing-proof artifact so it does not override the previously converted unified numeric no-fill path-quality artifact.
- The USDJPY London LONG guard now explicitly proves the newly loaded exact-R source-repair rows are raw evidence only and do not dominate selected side-scoped LONG evidence.

Previous immediately relevant runtime behavior from `e5c645d7f` remains intact:

- Unified numeric result ledger (`17,916` rows) GBPJPY `tokyo_kz` no-fill path-quality cohort still matches `1,184` rows, resolves AVOID from `1,060` avoid-filter rows plus `124` context rows, and can drive `vnext_risk_source_component_avoid_veto` and `SKIP_PENDING_NOFILL_AVOID` when activation is enabled.

## Current Active Pointer

Next row-bearing unit:

- `UNIT_001385`
- Source artifact:
  `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_SOURCE_COMPONENT_SUMMARY_LEDGER_2026-05-17.jsonl`
- Evidence family: `cp280_cp281_cp282_moonshot`
- Runtime surface: `vnext_scorer_filter_router_runtime`
- Required next action: inspect only enough row content to convert source-component summary rows into runtime/config/tests, or compute a tested kill/repair if it is truly non-runtime or superseded. Do not detour into wrapper accounting.

## Next Row-Bearing Units

Priority after `UNIT_001385` remains:

1. CP280/CP281/CP282 row-bearing artifacts from the frozen moonshot universe that carry follow/avoid/risk/router/gate/no-fill/selector/execution dimensions.
2. High-impact replay/simulated-R/proxy-R artifacts already wired by current config paths.
3. Repair-needed rows that unlock runtime behavior, especially exact broker execution geometry, source joins, slippage/fill lifecycle, no-fill/pending lifecycle, and source-bound target/stop geometry.
4. Historical handoff units only after freshness verification against CP280/CP281/CP282, current code/config/tests, and the current master ledger.

Do not process old scripts/manifests/summaries/verifiers one by one unless they expose unique unconsumed row-bearing runtime content.

## High-Impact Repair-Needed Units

Repair-needed count remains `183`. Highest-impact repair themes to pull only when they unlock runtime behavior:

- Broker execution geometry fields for exact-R:
  `order_ticket`, `deal_ticket`, `broker_fill_time_utc`, `executed_entry_price`, `executed_exit_price`, `executed_stop_price`, `executed_target_price`, `executed_lot_size`, `commission`, `swap`, `slippage_price`, `partial_exit_lifecycle`.
- Source-join absent rows that need concrete join keys from execution row id, sidecar source row id, branch queue id, symbol/session/source_component, and filled trade lifecycle.
- No-fill/pending lifecycle source repairs that can change pending placement, skip, expiry, market-entry conversion, or fillability gating.
- Target/stop geometry repairs where source-bound ordering or stop-first/target-first evidence can affect risk blocks or route filtering.
- Any source-component summary repair that narrows broad matching or prevents stale/generic source components from dominating selected routes.

## vNext Config Activation State

Current `config/agent_config.yaml` state:

- `gtos_vnext_runtime.enabled: true`
- `gtos_vnext_runtime.apply_to_execution: false`
- `gtos_vnext_runtime.pre_ai_enabled: true`
- `gtos_vnext_runtime.pre_ai_apply_to_ai_call: false`
- `gtos_vnext_runtime.risk_adjustment_enabled: true`
- `gtos_vnext_runtime.risk_zero_blocks_execution: true`
- `gtos_vnext_runtime.pending_policy_enabled: true`
- Exact-R/missing-proof artifact is now in `gtos_vnext_runtime.artifact_paths`.
- `moonshot_exact_r_missing_proof` is included in `artifact_source_component_evidence_families`.
- `moonshot_exact_r_missing_proof` is allowed as a side-anchor-optional evidence family only for configured no-fill source components.

Activation flags are controls, not permission to keep behavior as research-only. Runtime paths execute and attach evidence now; execution effect is ready when the config is flipped.

## Tests Run

- `py -3 -m pytest tests/test_gtos_vnext_runtime.py::test_moonshot_exact_r_missing_proof_rows_drive_source_repair_risk_block tests/test_gtos_vnext_runtime.py::test_agent_config_wires_vnext_runtime_shadow_execution_path tests/test_gtos_vnext_master_conversion_ledger.py::test_moonshot_exact_r_missing_proof_runtime_unit_converts_exact_r_ledger tests/test_gtos_vnext_master_conversion_ledger.py::test_current_manual_units_are_moonshot_exact_r_missing_proof_runtime_conversion -q --basetemp=.pytest-tmp-moonshot-exact-r-proof-focused -o cache_dir=.pytest-tmp-moonshot-exact-r-proof-cache`
  - `4 passed`
- `py -3 -m pytest tests/test_gtos_vnext_runtime.py::test_current_usdjpy_london_long_avoid_rows_are_excluded_by_side_scope tests/test_gtos_vnext_runtime.py::test_moonshot_unified_numeric_result_rows_drive_nofill_path_quality_avoid tests/test_gtos_vnext_runtime.py::test_moonshot_exact_r_missing_proof_rows_drive_source_repair_risk_block -q --basetemp=.pytest-tmp-moonshot-exact-r-proof-regression2 -o cache_dir=.pytest-tmp-moonshot-exact-r-proof-regression2-cache`
  - `3 passed`
- `py -3 -m pytest tests/test_gtos_vnext_runtime.py -q --basetemp=.pytest-tmp-moonshot-exact-r-proof-runtime-full2 -o cache_dir=.pytest-tmp-moonshot-exact-r-proof-runtime-cache2`
  - `151 passed`
- `py -3 -m pytest tests/test_gtos_vnext_master_conversion_ledger.py -q --basetemp=.pytest-tmp-moonshot-exact-r-proof-ledger-full -o cache_dir=.pytest-tmp-moonshot-exact-r-proof-ledger-cache`
  - `70 passed`
- `py -3 scripts/build_gtos_vnext_master_conversion_ledger.py --check`
  - Passed validation and printed the same counts/pointer listed above.

## Demo-Live Activation Path

This is not a brake on builder work. It is the operational feedback path while conversion continues.

- vNext runtime is built and executing in shadow/control mode, but execution-effect flags remain off.
- Next operational path is a demo/free live account run before any real-account flip.
- Observe and fix, from real broker cadence:
  - vNext decisions and evidence attachments
  - risk multipliers and zero-risk execution blocks
  - pre-AI route narrowing and AI-call bypass/removal behavior
  - pending/no-fill lifecycle, expiry, market-entry conversions, and retcodes
  - SL/TP geometry and stop-first/target-first evidence
  - broker symbols, futures aliases, and contract/cash normalization
  - structured logs and trade record evidence payloads
- Demo-live does not reduce the main builder objective: CP280/CP281/CP282 conversion continues on the builder lane.

## Exact Open Risks

- Execution-effect flags are still off: current vNext decisions attach and can compute execution effects, but they do not yet alter live orders until config activation is flipped.
- The exact-R/missing-proof artifact is intentionally `MIXED` source-repair evidence, not a directional edge. It blocks through risk when activated; it should not be converted into AVOID/FOLLOW without new row-bearing evidence.
- Source-component summary is the next active pointer and may reveal broad component-level behavior. Guard against broad/stale/generic component dominance; convert only source-bound dimensions that survive current matching specificity.
- `.context/LIVE_STATE.md` is modified from preflight and not committed here. Regenerate/read it again at next session start per AGENTS.md.
- GitHub push remains separate. Do not push without explicit instruction.
