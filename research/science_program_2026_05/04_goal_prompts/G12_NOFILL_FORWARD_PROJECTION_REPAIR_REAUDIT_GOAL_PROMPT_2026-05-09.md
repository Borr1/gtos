# G12 NOFILL Forward Projection Repair Reaudit Goal Prompt 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`.
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Starter Message

```text
/goal Run the independent G12 repair reaudit for the NOFILL forward source-safe projection builder after main repaired the exact blockers from G12-PROJ-BLOCKER-001 and G12-PROJ-BLOCKER-002. Start from current main HEAD and treat the repaired projection builder as the subject under audit, not the stale blocked verdict. Mandatory preflight: run python scripts/generate_live_state.py, read .context/LIVE_STATE.md, latest .context/02_session_handoffs file, .context/00_core/quick_reference_card.md, .context/00_core/research_operating_doctrine.md, .context/00_core/research_current_state.md, .context/00_core/goal_session_research_discipline.md, and .context/00_core/local_heavy_data_inventory.md before relying on memory. Controlling inputs: research/science_program_2026_05/06_outcome_testing/nofill_forward_source_safe_projection_builder/, prior G12 audit research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_projection_builder_audit/, repair commit 895175ef research: repair nofill forward projection blockers, context refresh 8a5e605a docs: refresh nofill projection repair state, the NOFILL forward addendum plan, G12 forward capture contract audit, NOFILL CAT V3 source-control/result-contract/count/G0 synthesis artifacts, and the builder/verifier/tests themselves. Objective: independently determine whether the repaired projection builder can now be accepted as source/control projection evidence only, or whether it remains blocked/rejected with exact reasons. Recompute from source, not from summaries: 298-row universe, 225 accepted rows, 182 nofill_duplicate_key denominator, 139 duplicate_group_id concentration denominator, 4 source-control exclusions, 4 source-impossible exclusions, 65 rejects, 47 reject-overlap exclusion, all source/parser hashes, mutable-context and line-ending hash policies, no-leak/ticket redaction, missing-status semantics, exhaustive allowlist projection rules, spread-source usage, local-heavy search claims, and committed live-surface scope. Specifically verify that the upstream verifier survives mandatory LIVE_STATE regeneration, that every emitted projection row key is explicitly allowed by the exhaustive allowlist, and that TOUCH_NOT_OBSERVED_SOURCE_SAFE entry-touch spread nulls no longer collapse into SOURCE_FIELD_MISSING. Operate at maximum practical reasoning depth and pursue every audit ambiguity, contradiction, stale-context warning, and newly discovered same-evidence-class question until answered, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement. Do not stop at a shallow checklist or at blocker naming. Treat listed files, current worktree, current timeframe, current instrument, current data modality, and first framing as starting points, not limits; search absolute local-heavy roots and relevant prior worktrees when needed. Enforce curiosity, truthfulness, and active creativity: try to prove the repaired builder is fake, leaky, under-specified, or stale; only accept what survives recomputation. Also be fair, not performatively conservative: if the repaired evidence passes the frozen controls, accept narrowly as source/control projection evidence only instead of inventing vague blockers. Maintain a context anchor, active question stack, searched-root ledger, recomputation ledger, source/hash/no-leak audit, denominator audit, adversarial issue ledger, decision ledger, next-route ledger, and instruction-coverage checklist. Do not score outcomes, compute R/win-rate/expectancy/DSR/PBO, validate, promote, edit registries, wire live loggers, call paid/API/Databento, expose or consume broker/account/order/history/deal/position labels, touch live trading prompts, src trading logic, config/risk/execution/permissions/safety/selectors/canaries/order behavior, credentials, remotes, or live behavior. Output only scoped G12 repair-reaudit artifacts under research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_projection_repair_reaudit/ plus research_current_state refresh if material. Verification required: JSON/JSONL parse, py_compile, focused pytest, upstream projection verifier after LIVE_STATE regeneration, independent G12 verifier, source/parser hash recomputation with mutable-context/line-ending policies checked, exhaustive projection allowlist scan, no-leak/forbidden field scan, missing-status audit, denominator/exclusion audit, committed-diff live-surface check, final LIVE_STATE regeneration, and clean or explained git status. Commit scoped artifacts with Co-Authored-By.
```

## Decision Space

G12 must issue exactly one terminal decision:

- `ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY`
- `BLOCK_ACCEPTANCE_PENDING_EXACT_REPAIR`
- `REJECT_INVALID_SOURCE_CONTROL_PROJECTION`

Acceptance is narrow and must preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`
- no result/cost scoring
- no validation or promotion route
- no live logger wiring or live behavior change

## Required Reaudit Questions

1. Did `G12-PROJ-BLOCKER-001` close under the exact failure mode: mandatory `LIVE_STATE` regeneration followed by upstream verifier rerun?
2. Did `G12-PROJ-BLOCKER-002` close because every emitted projection row key is now inside the explicit exhaustive allowlist?
3. Did the prior missing-status warning close without changing labels, denominators, result flags, or source meaning?
4. Did the repair preserve the exact `298 = 225 + 4 + 4 + 65` partition and the `225 / 182 / 139` denominators?
5. Did any projection field become result evidence, slippage evidence, execution-quality evidence, broker-order evidence, validation evidence, or promotion evidence?
6. Did mutable-context hash policy or line-ending normalization hide a real source-data change?
7. Does any local-heavy root, prior worktree, committed artifact, source hash, or parser hash contradict the repaired builder?
8. What exactly is the next evidence-class gate if G12 accepts: G0 synthesis/control, forward capture implementation design, or another source/control repair?

## Required Artifacts

Create versioned artifacts under:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_projection_repair_reaudit/`

At minimum:

- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_CONTEXT_ANCHOR_2026-05-09.md`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_2026-05-09.md`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_RECOMPUTATION_LEDGER_2026-05-09.json`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_BLOCKER_CLOSURE_AUDIT_2026-05-09.md`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_SOURCE_HASH_AUDIT_2026-05-09.json`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_ALLOWLIST_AUDIT_2026-05-09.json`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_MISSING_STATUS_AUDIT_2026-05-09.md`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_2026-05-09.md`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_DENOMINATOR_AUDIT_2026-05-09.json`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_HOSTILE_EDGE_REVIEW_2026-05-09.md`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_NEXT_PROMPT_PACK_2026-05-09.md`
- `G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_2026-05-09.md`
- `build_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py`
- `verify_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py`
- `test_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py`

## Saturation Pass

Before completion, answer and pursue any same-evidence-class gap exposed by:

- What exact leak would turn source/control projection evidence into result evidence?
- Could any source-control, source-impossible, reject, or reject-overlap row re-enter accepted counts?
- Could spread fields be misread as slippage, execution quality, or survival-adjusted cost?
- Could pending-order statuses leak MT5 tickets, broker order state, deal state, or account/history labels?
- Could the repaired allowlist be broad enough to hide future unsafe fields?
- Could the verifier pass without actually reading the regenerated `LIVE_STATE` state that caused the prior crash?
- Could local-heavy data or prior-worktree artifacts contradict source inventory or missing-status claims?
- If accepted, what is the strongest next research route that uses the accepted projection without crossing into validation or live behavior?

## Verification Commands

Run the strongest feasible checks, including:

```powershell
python scripts\generate_live_state.py
python -B research\science_program_2026_05\06_outcome_testing\nofill_forward_source_safe_projection_builder\verify_nofill_forward_source_safe_projection_builder_2026_05_09.py
python -B -m pytest research\science_program_2026_05\06_outcome_testing\nofill_forward_source_safe_projection_builder\test_nofill_forward_source_safe_projection_builder_2026_05_09.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_nofill_forward_projection_repair_upstream_g12
python -B -m py_compile research\science_program_2026_05\06_outcome_testing\g12_nofill_forward_projection_repair_reaudit\build_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py research\science_program_2026_05\06_outcome_testing\g12_nofill_forward_projection_repair_reaudit\verify_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py research\science_program_2026_05\06_outcome_testing\g12_nofill_forward_projection_repair_reaudit\test_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py
python -B research\science_program_2026_05\06_outcome_testing\g12_nofill_forward_projection_repair_reaudit\verify_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py
python -B -m pytest research\science_program_2026_05\06_outcome_testing\g12_nofill_forward_projection_repair_reaudit\test_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_g12_nofill_forward_projection_repair
```

## Stop Condition

The goal is complete only when G12 has a terminal decision, blocker closure or remaining blocker evidence is explicit, all required artifacts exist, upstream and G12 verification pass or exact blockers are recorded, no forbidden live-surface diff exists, research state is refreshed if material, and git status is clean or has only explained generated closeout dirt.
