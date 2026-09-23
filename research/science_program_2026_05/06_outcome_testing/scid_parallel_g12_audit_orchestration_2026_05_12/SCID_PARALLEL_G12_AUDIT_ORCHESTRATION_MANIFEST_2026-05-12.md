# SCID Parallel G12 Audit Orchestration Manifest - 2026-05-12

## Purpose

This manifest records the next parallel audit wave after the SCID forward-capture offline schema synthesis branch fan-out. It is intentionally file-backed so orchestration does not depend on chat memory.

## Main Commit Audited Separately

- Main commit to audit: `3faa2b70 research: harden live forward evidence capture`
- Main audit prompt commit: `b056cef0 research: finalize live audit prompt hardening`
- Main prompt: `research/science_program_2026_05/04_goal_prompts/G12_LIVE_FORWARD_EVIDENCE_CAPTURE_HARDENING_AUDIT_GOAL_PROMPT_2026-05-12.md`
- Run in: `C:\Users\MSI\Documents\ai-trading-agent`

## Parallel SCID G12 Worktrees

| Lane | Worktree | Branch | Hardened Prompt Commit | Prompt |
|---|---|---|---|---|
| Implementation design | `C:\tmp\gtos_otb\SCID_IMPL_DESIGN` | `scid-fc-impl-design` | `fab0abd3` | `research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT_GOAL_PROMPT_2026-05-12.md` |
| Synthetic harness | `C:\tmp\gtos_otb\SCID_SYNTH_HARNESS` | `scid-fc-synth-harness` | `752ad91f` | `research/science_program_2026_05/04_goal_prompts/G12_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_AUDIT_GOAL_PROMPT_2026-05-12.md` |
| Read-only alignment | `C:\tmp\gtos_otb\SCID_READONLY_ALIGN` | `scid-fc-readonly-align` | `8fbf9955` | `research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md` |
| No-API hypothesis factory | `C:\tmp\gtos_otb\SCID_NOAPI_HYP_FACTORY` | `scid-noapi-hyp-factory` | `549795f4` | `research/science_program_2026_05/04_goal_prompts/G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md` |
| LTF/orderflow/proxy expansion | `C:\tmp\gtos_otb\SCID_LTF_OF_EXPANSION` | `scid-fc-ltf-of-expansion` | `f8bbb4dc` | `research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md` |

## Prompt Hardening Standard

All audit prompts were strengthened to require:

- mandatory preflight/context refresh and disk artifact reads,
- no reliance on chat summaries,
- fair G12 posture: evidence-bound, not conservative theater,
- no invented hypothetical blockers,
- repair/recompute inside the G12 lane when possible,
- exact terminal blockers only by file/field/hash/source/no-leak/scoped-diff/verifier/test/evidence-class failure,
- scoped dirty-state ledgers so live/runtime churn does not confuse the audit,
- strict closed boundaries: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`,
- no validation/result scoring/strategy-edge/R/PnL/win-rate/expectancy/live/AI/API/paid/broker/raw-blob/prompt-config-risk-safety-execution-canary-selector surface.
- explicit non-boxing audit language: do not collapse to OB-only, do not punish novelty, and treat auditable new doors as valid next-route evidence.

Final review checklist was rerun from disk across all seven prompts after the final hardening commits. Every prompt passed the required preflight/context, no-chat-memory, fair-audit, no-invented-blocker, repair/recompute, exact-blocker, not-edge-selection, no-OB-collapse, new-door, commit-artifact, safe-flag, and one-line-starter-under-4000 checks.

## Known Caveat

`SCID_IMPL_DESIGN` has three untracked sibling helper drafts outside the accepted target route:

- `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/build_scid_forward_capture_implementation_design_package_2026_05_12.py`
- `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/test_scid_forward_capture_implementation_design_package_2026_05_12.py`
- `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/verify_scid_forward_capture_implementation_design_package_2026_05_12.py`

They were not deleted to avoid data loss. The implementation-design G12 prompt scopes the audit to the accepted target route and should ledger these as unrelated unless they touch the target route or a forbidden surface.

## Recommended Execution

Run the five SCID G12 audits in parallel in their own worktrees. Run the main live-forward evidence audit either in parallel if the machine is stable, or after the live monitoring session quiets down if you want less runtime dirt in the scoped-diff ledger.
