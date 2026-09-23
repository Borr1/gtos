# Orchestrator Methodology Hardening Controls

Date: 2026-05-15
Status: active control layer
Scope: remaining process limitations in GTOS research orchestration

## Purpose

This file turns the known research-process limitations into concrete controls. It complements:

- `.context/00_core/orchestrator_successor_operating_brief.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/parallel_goal_merge_playbook.md`

## Limitation-To-Control Matrix

| Limitation | Required Control |
|---|---|
| Prompt compliance is never guaranteed | Run `scripts/validate_goal_prompt_hardening.py` before launch; require completion-audit instruction coverage after completion |
| Context compaction can erase rules | Every prompt and starter must require regenerating `LIVE_STATE` and rereading the starter, controlling prompt, doctrine, and latest route artifacts after compaction/resume/interruption/uncertainty |
| "Limitless" can become unfocused | Define exact evidence class and forbidden surfaces, then require maximum pursuit inside that evidence class |
| Top-N truncation loses research intelligence | Forbid arbitrary 3/5/10/top-N cutoffs for questions, ambiguities, doors, opportunities, blockers, source roots, branches, route candidates, and failure families; rank summaries are allowed only after full machine-readable ledgers preserve all material rows |
| Closeout summaries are weak evidence | Run `scripts/audit_goal_route_artifacts.py`; inspect artifacts from disk before advice or merge |
| G0/G12 can loop | Use the loop detector in `orchestrator_successor_operating_brief.md`; next route must produce a new artifact, repair, packet, audit acceptance, or exact gate transition |
| Same-model subagents can echo | Give subagents different roles: artifact auditor, prompt critic, loop/risk reviewer, route sequencer |
| Prompt length can dilute priorities | Keep the prompt structured with terminal artifacts and completion standard; use one-line starter as execution contract |
| Result evidence may be neutral-target-only | Label evidence class exactly, then drive the lane to materialize the highest valid next artifact: scorer, repair, replay rerun, deployment-package dossier, or production-change dossier. Replay-backed dossiers are valid when source-bound validation, holdout, stress, and verifier gates satisfy the deployment question |
| Sessions stop at clean blockers | A blocker ledger, next-route prompt, or clean fail-closed classification is not completion when same-evidence-class repair is possible; require repair and recomputation before handoff |
| Result routes undercompute trade geometry | Require attempts to bind side, entry/reference, stop/invalidation, target/R multiple, horizon, fillability/path ordering, and cost/slippage from accepted local/source-bound artifacts before leaving R/expectancy fail-closed |
| Historical source-state gaps are real | Use `local_heavy_data_inventory.md`; distinguish recoverable market data from non-generatable historical GTOS state |
| Large-ledger complexity creates verifier risk | Use manifests, LFS checks, LF-normalized text policy where appropriate, full JSONL scans for high-value gates, and post-merge reruns |
| Orchestrator becomes bottleneck | Use subagents for bounded review while preserving orchestrator final judgment |
| Research-lane boundaries leak into production integration | For production-code integration lanes, authorize the exact code/config/profile/verifier/launcher surfaces and gate only broker/account/order/deal/position mutation, credentials, paid/vendor calls, remote push, and live restart/reload |
| Stale chat facts pollute prompt files | Remove or mark old hashes/counts/status as anchors to verify; require current-disk branch, route, and artifact refresh before edits |
| V3 packages remain inert ledgers | Require runtime disposition for every component: active, staged/default-off, research-only with exact missing requirement, or rejected with evidence |
| Production branch absorbs research LFS | Require include/exclude scope ledger, LFS pointer review, staged-path review, and recovery pointers for excluded research artifacts |
| Parallel sessions collide on merge/integration | Use one owner integration session for overlapping production files; use subagents as bounded reviewers, not independent writers to shared files |

## Required Current Ledgers

The current route status registry is:

`research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json`

The current cross-route question/ambiguity ledger is:

`research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json`

These are not bureaucratic summaries. They are detail-preservation controls. Update them after every major route completion, merge, G12 acceptance, G0 gate, or material interpretation change.

## Minimum Mechanical Checks

Before launching a prompt:

```powershell
python scripts/validate_goal_prompt_hardening.py <PROMPT_PATH>
```

On this Windows host, if `python` fails before script start due launcher/session friction, use the equivalent `py -3` command and record that fallback:

```powershell
py -3 scripts/validate_goal_prompt_hardening.py <PROMPT_PATH>
```

Before accepting or merging a route:

```powershell
python scripts/audit_goal_route_artifacts.py <ROUTE_DIR> --full-jsonl
```

For launch-pack directories, use:

```powershell
python scripts/audit_goal_route_artifacts.py <ROUTE_DIR> --profile launch-pack --full-jsonl
```

For very large routes where a full JSONL scan is too expensive during an interactive check, the orchestrator may use a capped scan first, but the high-value final review should either run full scan, cite a route verifier that already did full recomputation, or state exactly what was not rescanned.

## Completion Standard

For a high-value route, "complete" means:

- full artifact set exists;
- verifier/tests pass or exact environment friction is documented;
- after any compaction/resume/interruption/uncertainty, the lane reread the starter, controlling prompt, `goal_session_research_discipline.md`, `research_operating_doctrine.md`, lane-specific doctrine, and latest route artifacts from disk;
- large ledgers are counted and status distributions inspected;
- same-evidence-class blockers are pursued or exactly bounded;
- blocker ledgers, next-route prompts, and fail-closed classifications are not used as completion when same-evidence-class repair is possible;
- missing fields, stale hashes, source gaps, geometry gaps, denominator/control/path/fillability/cost/slippage/target/stop/side/entry/stop/target/fillability/R-geometry gaps, and incomplete result conditions have been repaired and recomputed where approved sources allow it;
- result/scoring/validation routes attempted source-bound geometry binding before leaving R/expectancy or target/stop outcomes ambiguous/fail-closed, and any remaining impossibility is row-level and source-specific;
- no arbitrary top-N/3/5/10 cutoff was used for questions, ambiguities, opportunities, doors, blockers, source roots, branches, routes, or failure families; full ledgers preserve all material rows;
- for production-code integration lanes, authorized code/config/profile/verifier/launcher changes are not treated as forbidden merely because they are live-facing, while deployment/broker/credential/paid/remote surfaces remain separately gated;
- stale branch hashes, process counts, broker states, route statuses, and "next wave" facts from prompt creation were refreshed from disk or explicitly labeled historical;
- any V3, FTMO, broker-profile, selector, scheduler, execution, or source-capture package received a runtime disposition instead of being left as an inert report;
- production branch scope was checked against LFS/research-ledger pollution before commit;
- question/ambiguity ledger is updated;
- route-status registry is updated;
- next route is exact or the lane is exhausted;
- boundary fields remain closed unless a separately approved lane changes them.
