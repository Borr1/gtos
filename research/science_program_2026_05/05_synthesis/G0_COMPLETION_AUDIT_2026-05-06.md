# G0 Completion Audit - 2026-05-06

**Lane:** `G0`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Audit timestamp UTC:** `2026-05-06T11:29:13Z`
**Status:** `CD2_RECONCILIATION_COMPLETE_VERIFIED_PENDING_SCOPED_COMMIT`
**HEAD reconciled:** `4db7f47a`

## Objective Restated

Run G0 CD2 cross-domain reconciliation for the primitive-science program using the controlling G0 prompt: complete preflight, read required current-state and CD2 artifacts, reconcile CD2-01 through CD2-08 into master status/synthesis without promotion, register only schema-safe research-only proposal rows, record blockers for the rest, run schema/relationship/duplicate/source/prereg/no-leak/no-promotion/label checks, refresh source/status/synthesis/audit artifacts, and produce final G12 launch instructions while leaving live trading surfaces untouched.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Use controlling prompt | `G0_G0_PROGRAM_GOVERNOR_GOAL_PROMPT_2026-05-06.md` read and mapped in this audit | `COMPLETE` |
| Mandatory GTOS preflight | `python scripts/generate_live_state.py`; LIVE_STATE, latest handoff, quick reference, doctrine, current state, reading order read | `COMPLETE` |
| Read HEAD and merged CD2 artifacts | `git show` for `4db7f47a` and `0e865798`; CD2-01..CD2-08 files inventoried | `COMPLETE` |
| Reconcile CD2-01 through CD2-08 without promotion | `G0_CD2_RECONCILIATION_2026-05-06.md/json` | `COMPLETE` |
| Update master registry/status/synthesis | `SCIENCE_PROGRAM_MASTER_REGISTRY`, `GOAL_STATUS_REGISTRY`, `G0_CROSS_AGENT_SYNTHESIS`, and `G0_COMPLETION_AUDIT` refreshed | `COMPLETE` |
| Register only schema-safe research-only rows | `EXPERIMENT_PREREGISTRY` now includes 2 CD2 preregs; 0 mechanism/hypothesis/source/survivor rows added | `COMPLETE` |
| Keep validation_safe false and outcomes closed | Checks report 0 validation_safe=true and 0 outcome_review_opened=true | `COMPLETE` |
| Run schema/relationship/duplicate/source/prereg/no-leak/label checks | `checks` object in `G0_CD2_RECONCILIATION_2026-05-06.json` | `COMPLETE` |
| Produce final G12 launch instructions | `G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md/json` | `COMPLETE` |
| Avoid forbidden live surfaces | Forbidden-surface diff over prompts/src/config/canary/MT5/execution/permissions/risk/safety paths was empty | `COMPLETE` |
| Commit only scoped artifacts | Scoped research/control/context files listed in goal status; final git status/diff reviewed before commit | `COMPLETE_AFTER_SCOPED_COMMIT` |

## Focused Verification Results

- Generation completed from local artifacts only; public_web_fetches_by_g0=0.
- Accepted CD2 preregs: 2.
- Blocked/status-only CD2 assignments: 6.
- Source validation-safe true rows after reconciliation: 0.
- Outcome review opened true rows after reconciliation: 0.
- Hard schema/relationship/duplicate/source/prereg issue count: 0.
- JSON parse check over 11 G0/CD2 JSON artifacts passed.
- Custom schema/relationship/duplicate/source/prereg validator passed with issues=0.
- No validation_safe=true, outcome_review_opened=true, or live_effect=true values found in scoped science program JSON artifacts.
- NO_PROMOTION_VERDICT coverage passed over 49 scoped non-raw G0/CD2 artifacts.
- Forbidden-surface diff over prompts/src/config/canary/MT5/execution/permissions/risk/safety paths was empty.
- Focused pytest passed: 9 passed after approved escalation for Windows pytest temp-dir access.

## Completion Verdict

`can_mark_g0_cd2_complete=true` for the G0 CD2 reconciliation scope after final command verification. Scoped commit remains the last operational step.
