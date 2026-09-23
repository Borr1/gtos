# Subagent Findings - Candidates, Selectors, V3

Agent: `019e89f1-4076-7d72-aea5-625490eb6253`

Scope: candidates/selectors/V3 decision and rejection lifecycle.

Status: read-only audit finalized from raw JSONL/JSON/config/code evidence. The agent reported no broker/order mutation and no generated Python audit scripts as proof.

## Clean Proofs Reported

- Current live runtime is vNext/moonshot, not April/J46/J49/7-symbol/old PA/L2.
  - Evidence:
    - `shadow_logs/gtos_vnext_runtime_decisions.jsonl`, June 2 rows `2636-5185`;
    - `2550` rows through `2026-06-02T20:30:38.994570+00:00`;
    - `old_primary_analyzer_called=true = 0`;
    - `old_l2_required=true = 0`.
- Dynamic selector wiring is current vNext truth.
  - Evidence:
    - `config/agent_config.yaml` runtime block has `moonshot_dynamic_execution_router_policy: "momentum_exhaustion"`;
    - exception policy `partial_be_runner`;
    - `apply_to_execution: true`;
    - `selector_v3_enabled: false`;
    - `selector_v3_apply_to_execution: false`.
- Runtime dynamic decisions are using current promoted policies.
  - Evidence:
    - `shadow_logs/gtos_vnext_runtime_decisions.jsonl`, June 2 dynamic rows `447`;
    - `partial_be_runner=385`;
    - `momentum_exhaustion=62`;
    - `fixed_target_role=baseline_comparator_only=447`.
- Example clean approval:
  - `shadow_logs/gtos_vnext_runtime_decisions.jsonl:5153`;
  - `2026-06-02T20:15:20.123503+00:00`;
  - `US30_cash`;
  - candidate `broadorigin_f0e31d198f29d958393d353f`;
  - `candidate_use_allowed_now=True`;
  - policy `momentum_exhaustion`;
  - risk `0.25`;
  - execution policy `vnext_exec_momentum_1r_pullback_04r_cap_2r`.

## Findings

1. Runtime decision JSONL is not chronological.
   - Evidence:
     - `shadow_logs/gtos_vnext_runtime_decisions.jsonl`, June 2 rows `2636-5185`;
     - `296` backward timestamp transitions;
     - first break: line `2643` `2026-06-02T00:00:08.283148+00:00` followed by line `2644` `2026-06-02T00:00:07.425115+00:00`.
   - Impact:
     - raw decision replay by file order is wrong.
   - Required repair:
     - serialize through one ordered writer or add monotonic sequence/cycle id and make consumers sort by timestamp plus sequence.

2. Safety-gate blocked rows contradict candidate generation status.
   - Evidence:
     - `shadow_logs/gtos_vnext_runtime_decisions.jsonl:2636`;
     - `2026-06-02T00:00:07.123470+00:00`;
     - EURUSD row has `candidate_count=1`;
     - first candidate has `live_generation_status=generated_live_asof`;
     - nested `source_packet.live_generation_status=no_broader_origin_candidate_generated_live_asof`;
     - same contradiction occurs in all `197` June 2 `broader_origin_safety_gate_blocked` rows.
   - Impact:
     - lifecycle accounting can classify generated rejected candidates as no-candidate.
   - Required repair:
     - safety-gate packet writer must emit generated/prescreen-blocked source status when `candidate_count>0`;
     - add invariant test.

3. One selected-cell risk ledger gap is actively blocking a candidate.
   - Evidence:
     - `shadow_logs/gtos_vnext_runtime_decisions.jsonl:4225`;
     - `2026-06-02T12:45:07.374146+00:00`;
     - `US30_cash`;
     - candidate `broadorigin_841a172170361365053e0a2d`;
     - `origin_displacement_continuation`;
     - `moonshot_h12_13`;
     - `SHORT`;
     - policy `partial_be_runner`;
     - `selected_cell_risk_refusal_cause=missing_ledger_row`;
     - action `ACTIVATED_CANDIDATE_HELD_FOR_SOURCE_OR_BRANCH_REPAIR`.
   - Impact:
     - correct fail-closed rejection, but selected-cell coverage is incomplete.
   - Required repair:
     - add exact selected-cell ledger row or explicit source-gap rule for that symbol/family/session/side/policy join.

4. Strategy follow evaluation ledger is stale-labeled and not self-sufficient.
   - Evidence:
     - `shadow_logs/strategy_follow_evaluations.jsonl`, June 2 rows `4778-7038`, `2261` rows;
     - all have first strategy `LIVE_AI_J46_J49_BASELINE_COMPARATOR`;
     - role `baseline_comparator`;
     - `result_use_status=LIVE_PRODUCTION_PATH`;
     - all have `selected_side=UNKNOWN_SIDE`, `side=UNKNOWN_SIDE`, `source_hash=null`, `dedupe_key=null`;
     - first row `4778` at `2026-06-02T00:00:06.913060+00:00`;
     - last row `7038` at `2026-06-02T20:45:19.017101+00:00`.
   - Impact:
     - downstream summaries can treat J46/J49 comparator as production and cannot uniquely join rows.
   - Required repair:
     - mark J46/J49 as comparator-only;
     - populate side/source hash/dedupe key;
     - or hard-label ledger non-decision-evaluable.

5. Strategy follow evaluation ledger is also non-chronological.
   - Evidence:
     - same file;
     - `141` backward `created_at_utc` transitions;
     - first break: line `4783` `2026-06-02T00:00:07.581540+00:00` followed by line `4784` `2026-06-02T00:00:07.450923+00:00`.
   - Impact:
     - file-order replay is invalid.
   - Required repair:
     - ordered writer or monotonic sequence id.

6. Selector V3 is not live; it is only shadow/result materialization.
   - Evidence:
     - `config/agent_config.yaml`: `selector_v3_enabled: false`, `selector_v3_apply_to_execution: false`;
     - `shadow_logs/strategy_follow_evaluations.jsonl` all `2261` June 2 rows include V3 snapshot `V3_FVG_ONLY_RESCUE_RISK_BANK` with `result_use_status=RESULT_MATERIALIZATION_REQUIRED`.
   - Impact:
     - V3 cannot be claimed as active selector behavior.
   - Required repair:
     - keep V3 labeled default-off until a production-change dossier enables it;
     - if used in reporting, separate it from live approvals/rejections.

7. Strategy follow candidate ledger is legacy/stale.
   - Evidence:
     - `shadow_logs/strategy_follow_candidates.jsonl`, June 2 rows `541-636`, `96` rows;
     - all `source_component=primary_analyzer_live_candidate`;
     - all `analysis_decision=CANDIDATE`;
     - zero rejection rows;
     - `source_hash=null`;
     - `verification.passed=null`;
     - `verification.checks=[]`;
     - blank `gtos_vnext_decision`;
     - blank dynamic policy;
     - first row `541` `ETHUSD` at `2026-06-02T00:36:39.211939+00:00`;
     - last row `636` `XAUUSD` at `2026-06-02T07:19:54.399354+00:00`.
   - Impact:
     - this ledger is not current vNext candidate truth.
   - Required repair:
     - retire/rename as legacy or rewrite writer to broader-origin vNext schema with vNext decision, dynamic policy, verification, source hash, and reject rows.

8. Candidate LTF path recovery is safe but incomplete.
   - Evidence:
     - `shadow_logs/candidate_ltf_path_order.jsonl`, June 2 rows `12317-13721`, `1405` rows;
     - all `no_execution=true`;
     - all `POST_DECISION_RECOVERY_ROW_NOT_DECISION_FEATURE`;
     - `984` same-M1 ambiguous;
     - `149` source blocked;
     - real June 2 decision-time source blocks: `13`;
     - first decision-time block at line `13132`, `2026-06-02T01:36:11.713492+00:00`, `UKOIL_cash`, decision `2026-06-02T01:15:00Z`, `mt5_read_error=mt5_no_rates`, `m1_bar_count=0`.
   - Impact:
     - post-decision path evidence cannot fully resolve oil candidate paths.
   - Required repair:
     - repair UKOIL/USOIL M1 capture/backfill and add tick fallback where available.

9. Candidate path follow is M15/OHLC-only, not tick-order proof.
   - Evidence:
     - `shadow_logs/candidate_path_follow.jsonl`, June 2 rows `9178-10664`, `1487` rows;
     - all `tick_order_claim_status=NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY`;
     - `776` `M15_TP1_SL_ORDER_AMBIGUOUS_NO_TICK_ORDER_CLAIM`;
     - `709` `M15_OHLC_PATH_LABEL_ONLY`.
   - Impact:
     - this surface cannot prove intra-bar TP/SL order.
   - Required repair:
     - attach tick path order capture or keep this ledger explicitly post-decision/OHLC-only.

10. Pending candidate lifecycle rows are not self-sufficient.
    - Evidence:
      - `shadow_logs/pending_limit_lifecycle.jsonl`, June 2 rows `447-702`, `256` rows through `2026-06-02T20:45:05.598133+00:00`;
      - all `decision_time_utc=null`;
      - all `decision_spread_value_source_safe=null`;
      - all `source_hash=null`.
    - Impact:
      - candidate-to-decision replay joins are incomplete.
    - Required repair:
      - populate decision timestamp, decision spread value/unit/source, and source hash from originating runtime packet.

11. Pending lifecycle has failed order-send diagnostics with no MT5 retcode.
    - Evidence:
      - same file;
      - `46` rows `fill_no_fill_label=triggered_order_send_failed_retry`;
      - all `order_result_retcode=null`;
      - all `mt5_entry_order_ticket=null`;
      - example line `447`, `GBPJPY`, `2026-06-02T01:17:34.868297+00:00`.
    - Impact:
      - failure root cause cannot be reconstructed from raw row.
    - Required repair:
      - persist full MT5 result/retcode/comment/last_error/request payload for every failed send.

12. Current trade/candidate records are split across account-scoped and legacy namespaces.
    - Evidence:
      - pending rows reference `223` `knowledge_base\redacted_account_live_bee34003\trade_records\...` paths and `33` legacy `knowledge_base\trade_records\...` paths;
      - trade JSON counts inspected: `316` redacted_account June 2 records and `138` legacy June 2 records.
    - Impact:
      - account isolation and joins are fragile.
    - Required repair:
      - route all current writers and indexes to account-scoped roots;
      - legacy root should be pointer/archive only.

13. Trade records retain false AI labels on pre-AI vNext records.
    - Evidence:
      - inspected June 2 trade JSONs under both trade-record roots;
      - all `316` redacted_account and all `138` legacy records had `decision_pipeline.ai_decision=CANDIDATE`, `ai_grade=A+`, `ai_confidence=100`;
      - L2 not-run reason exists and runtime old PA/L2 flags are false;
      - sample: `knowledge_base\redacted_account_live_bee34003\trade_records\NAS100\2026-06-02_moonshot_h02_03_0215_broadorigin_e09030a834d9f16dec48c610.json`.
    - Impact:
      - records misrepresent pre-AI/pre-L2 vNext decisions as AI approvals.
    - Required repair:
      - replace with explicit `pre_ai_vnext_candidate` / `ai_not_called` fields and null AI grade/confidence.

14. Trade-record dynamic policy instrumentation has a rejected-row gap.
    - Evidence:
      - instrumentation dynamic policy present in `314/316` redacted_account files and `135/138` legacy files;
      - missing files identified:
        - redacted_account `EURJPY` and `GBPJPY` `2026-06-02_moonshot_h04_05_0445_*`;
        - legacy `EURJPY`, `GBPJPY`, and `XAUUSD` same `04:45` batch.
    - Impact:
      - Gate3-rejected rows have incomplete dynamic-policy audit fields.
    - Required repair:
      - write dynamic policy packet for all vNext records, including Gate3 rejected rows.

15. Selector package is active but source-limited.
    - Evidence:
      - `config/agent_config.yaml` has `moonshot_candidate_quality_selector_enabled: true`;
      - `moonshot_candidate_quality_selector_apply_to_execution: true`;
      - package `research/operations/vnext_lane03_meta_selector_discovery_implementation_2026_05_31/LANE03_META_SELECTOR_RULE_PACKAGE.json`;
      - `src/research/moonshot_default_off_policy_router.py:312-416` blocks when no source-bound selector package/rule/spread is present.
    - Impact:
      - selector is fail-closed, but live effectiveness depends on a fully populated, source-bound rule package.
    - Required repair:
      - keep execution apply enabled only with complete tradeable rules/source hash coverage and tests for no blank package/rule joins.

## Not Fully Inspected

- Final all-file recount of `decision_pipeline.gtos_vnext_moonshot_dynamic_execution` packets was interrupted.
  - The agent had instrumentation counts and a raw sample proving packet shape, but not a completed all-file dynamic-packet count.
- The agent did not inspect every route-generated audit JSON because it was told to stop broadening and finalize.
  - Several dual-supervisor route ledgers are stale against live raw logs.
  - Example: `DUAL_V3_RUNTIME_DISPOSITION_LEDGER.jsonl` recorded `2026-06-02T11:38:23.700913+00:00`, while raw runtime decisions continue to `2026-06-02T20:30:38.994570+00:00` and pending lifecycle to `2026-06-02T20:45:05.598133+00:00`.
