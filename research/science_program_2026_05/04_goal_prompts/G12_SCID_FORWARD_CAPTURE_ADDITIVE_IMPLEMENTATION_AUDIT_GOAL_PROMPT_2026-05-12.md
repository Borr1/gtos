# G12 SCID Forward Capture Additive Implementation Audit Goal Prompt - 2026-05-12

You are an independent G12 audit wave. Audit the completed additive implementation route:

`research/science_program_2026_05/06_outcome_testing/scid_forward_capture_additive_implementation_from_parallel_g12_wave/`

Execute to terminal completion. Do not rely on chat summaries. Do not make up blockers. Do not be timid or conservative theater. Be adversarial, exact, and fair: accept what is genuinely implemented and source/control-valid; reject or repair only concrete file/line, schema, no-leak, verifier, test, prompt-boundary, or live-surface failures.

## Required Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read the target implementation prompt:
   - `research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION_FROM_ACCEPTED_PARALLEL_G12_WAVE_GOAL_PROMPT_2026-05-12.md`
7. Read the target route artifacts listed below.
8. Run `git status --short` and record unrelated runtime/shadow dirt as informational only. Do not stage or revert unrelated dirt.

## Audit Posture And Evidence Class

This is a G12 audit of additive evidence-capture implementation. The audit may accept source/control implementation evidence only. It must not open validation, result scoring, R/PnL/win-rate/expectancy/performance claims, promotion, paid/API calls, credentials/remotes, order placement/modification/cancellation, risk/safety changes, prompt decision behavior, canary/selector behavior, or raw market/broker blob commits.

G12 should be skeptical about claims, not skeptical about novelty. The route is allowed to be broad, creative, and non-OB-only as long as it stays auditable and hard-boundary-compliant. Do not reject because the implementation supports new hypothesis families, LTF/orderflow/proxy needs, or non-current-GTOS mechanisms. Reject only if the evidence surface is unsafe, unimplemented, unverifiable, stale, leaky, denominator-invalid, behavior-changing, or falsely claimed.

The target route did not claim live row landing and did not perform a controlled restart. Audit that exactly. Absence of default live rows is not a blocker by itself if the implementation is code-complete, fail-open, tested, and the route honestly records `live_row_landing_claimed=false`. It is a blocker only if the code is not actually wired, the verifier masks required rows incorrectly, the prompt required active row landing before completion, or the artifacts falsely imply active live effect.

## Required Target Inputs

Read at minimum:

- Implementation files:
  - `src/research_infra/forward_capture.py`
  - `src/components/pending_limit_lifecycle_logger.py`
  - `scripts/verify_scid_forward_capture_schema.py`
- Focused tests:
  - `tests/test_scid_forward_capture_runtime_adapter.py`
  - `tests/test_scid_forward_capture_lifecycle_redaction.py`
- Route artifacts:
  - `G12_SCID_FORWARD_CAPTURE_AUDIT_PROMPT_HARDENING_ADDENDUM_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_OUTPUT_MANIFEST_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_COMPLETION_AUDIT_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_CAPTURE_GROUP_MATRIX_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_RUNTIME_ADAPTER_LEDGER_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_HYPOTHESIS_FACTORY_COMPATIBILITY_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_LTF_ORDERFLOW_PROXY_COMPATIBILITY_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_SATURATION_AND_SELF_RED_TEAM_LEDGER_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_SEARCHED_ROOT_LEDGER_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_NO_LEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_RESTART_LEDGER_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_BROKER_READ_LEDGER_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_VERIFIER_RESULT_SYNTHETIC_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_VERIFIER_RESULT_DEFAULT_2026-05-12.json`
  - `SCID_FC_ADDITIVE_IMPL_SYNTHETIC_VERIFIER_INPUT_2026-05-12.jsonl`

## Required Recomputations

1. Recompute that all ten accepted `scid_forward_source_capture_v1` capture groups exist in code, in synthetic rows, and in validator coverage.
2. Recompute schema enforcement for required fields, allowed fields, enum values, source hash policy, as-of policy, duplicate-key drift rejection, safe flags, and forbidden key/value rejection.
3. Verify candidate-time capture is actually wired from `record_live_candidate_forward_shadow` into nine candidate-time SCID groups, and lifecycle capture is wired from `record_pending_limit_lifecycle` into the lifecycle group.
4. Verify writer failures are fail-open and no live trading decision, risk gate, selector, safety gate, execution path, AI prompt, canary threshold, or config behavior consumes writer return values.
5. Verify lifecycle rows redact or reject raw tickets, order ids, deal ids, position ids, account ids, realized R, PnL, win/loss, result labels, slippage, spread-cost, or execution-quality values unless they are explicitly source-status/redacted/non-scoring and permitted by the route.
6. Verify LTF and orderflow unavailable paths fail closed without vendor/API/broker fetches and without raw market-data blob commits.
7. Verify the 3,014 candidate boundary is represented only as prospective capture denominator context, not as validation sample size or performance evidence.
8. Verify the 40-card/8-domain hypothesis factory is supported as downstream compatibility only, not edge selection, ranking, validation, or promotion.
9. Verify no broad paid/vendor/API access, credential/remote change, or broker actual-R/performance read occurred.
10. Verify route artifacts are committed and machine-checkable, and that the default live verifier uses `--allow-empty` honestly without claiming active live row landing.
11. Inspect `git show --name-only d2ceb35b` and current committed diff scope. Confirm no forbidden production prompt/config/risk/safety/execution/canary/selector/order behavior file was changed.
12. Inspect whether the implementation prompt's hardening requirements were materially satisfied. If not, classify the issue precisely as blocking, repairable, or non-blocking activation follow-up.
13. Reconcile the original output-manifest hash for this G12 prompt with `G12_SCID_FORWARD_CAPTURE_AUDIT_PROMPT_HARDENING_ADDENDUM_2026-05-12.json`. The prompt hash mismatch caused by orchestrator hardening is not a target-route implementation failure; any other strict manifest/input hash mismatch must be audited normally.

## Required Commands

Run or justify an equivalent stronger command:

- `python -m py_compile src/research_infra/forward_capture.py src/components/pending_limit_lifecycle_logger.py scripts/verify_scid_forward_capture_schema.py`
- `python scripts/verify_scid_forward_capture_schema.py --path research/science_program_2026_05/06_outcome_testing/scid_forward_capture_additive_implementation_from_parallel_g12_wave/SCID_FC_ADDITIVE_IMPL_SYNTHETIC_VERIFIER_INPUT_2026-05-12.jsonl --json`
- `python scripts/verify_scid_forward_capture_schema.py --allow-empty --json`
- `python -m pytest tests/test_scid_forward_capture_runtime_adapter.py tests/test_scid_forward_capture_lifecycle_redaction.py -q -p no:cacheprovider --basetemp research/science_program_2026_05/06_outcome_testing/scid_forward_capture_additive_implementation_from_parallel_g12_wave/tmp_pytest_g12`

If Windows cache/temp friction appears, use explicit `--basetemp`, disabled cache provider, AST syntax parsing, or explicit `.pyc` output and record the distinction between environment friction and code failure.

## Required Output Artifacts

Create a new G12 audit directory under:

`research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_additive_implementation_audit/`

Emit at minimum:

- decision ledger JSON and Markdown;
- code-surface/diff-scope audit;
- schema/group recomputation ledger;
- redaction/no-leak/forbidden-surface audit;
- live-row-landing and restart-honesty audit;
- hypothesis/LTF/orderflow downstream compatibility audit;
- test/verifier reproduction result;
- blocker and non-blocking finding ledger;
- completion audit with `can_mark_goal_complete=true` only when all required checks pass;
- next G0 synthesis prompt if accepted, or exact repair prompt if blocked.

## Verdict Rules

Use one exact terminal decision:

- `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION_CONTROL_EVIDENCE_ONLY`
- `ACCEPT_WITH_EXACT_NONBLOCKING_ACTIVATION_FOLLOWUPS`
- `REPAIR_BLOCKED_SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION`
- `REJECT_UNSAFE_OR_UNVERIFIABLE_SCID_FORWARD_CAPTURE_IMPLEMENTATION`

Do not use vague "future work." Every finding must be tied to file/line evidence, artifact evidence, a verifier/test result, or an exact missing source/permission/field. Mark the goal complete only after scoped commits, closeout verification, and final `LIVE_STATE` freshness.

Final safe flags must remain:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`
