# G4 Market Microstructure, Order Book, Auction Completion Audit - 2026-05-06

**Lane:** `G4`
**Worktree:** `C:\tmp\gtosg\G4`
**Branch:** `science-goals/g4-microstructure-auction`
**Status:** `COMPLETE_COMMITTED`
**Primary commit:** `6f63dd6db39f623e9518ac6e51fcb62aa141f36b`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Objective Restatement

Run the G4 primitive-science research lane for market microstructure, order book, and auction mechanisms under `research/science_program_2026_05/04_goal_prompts/G4_G4_MICROSTRUCTURE_AUCTION_GOAL_PROMPT_2026-05-06.md`.

Success criteria:

- complete mandatory preflight and respect G0 governor/source/schema artifacts;
- produce lane-owned G4 domain synthesis, context/ambiguity ledger, source index/contracts, mechanism rows, hypothesis rows, experiment preregs, goal status, and audit;
- add neighbor-lane cross-domain hypotheses only after reading neighbor-owned outputs and only where source/leakage/killed-route checks survive;
- keep every row/report at `NO_PROMOTION_VERDICT`;
- spend no new cash and mark no source validation-safe;
- touch no live trading prompts, risk, execution, permissions, selectors, safety gates, MT5, canaries, paid-data path, or order behavior.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Mandatory preflight: run live state generator | `python scripts/generate_live_state.py -> Wrote .context\LIVE_STATE.md` recorded in `G4_MICROSTRUCTURE_AUCTION_CONTEXT_LEDGER_2026-05-06.md` and status JSON. | PASS |
| Read live state, handoff, quick reference, doctrine, current state, reading order | `G4_MICROSTRUCTURE_AUCTION_CONTEXT_LEDGER_2026-05-06.md`, `Mandatory Preflight Ledger`. | PASS |
| Respect G0 governor, schema, source/budget, worktree map, cross-agent synthesis, completion audit, master registry | `G4_MICROSTRUCTURE_AUCTION_CONTEXT_LEDGER_2026-05-06.md`, source-read ledger and source/budget blockers. | PASS |
| Work only in G4 lane worktree and branch | Branch check returned `science-goals/g4-microstructure-auction`; scoped files are under `research/science_program_2026_05/` in `C:\tmp\gtosg\G4`. | PASS |
| Domain synthesis | `01_domain_syntheses/G4_MICROSTRUCTURE_AUCTION_SYNTHESIS_2026-05-06.md`. | PASS |
| Lane context ledger, search plan, sources read, evolving questions, stale-context refreshes | `01_domain_syntheses/G4_MICROSTRUCTURE_AUCTION_CONTEXT_LEDGER_2026-05-06.md`. | PASS |
| Ambiguity ledger | Same context ledger, `Ambiguity Ledger`. | PASS |
| Counter-evidence and decay-mode review | Domain synthesis, `Counter-Evidence And Decay-Mode Review`. | PASS |
| Mechanism rows using `science_mechanism_v1` | `02_hypothesis_registry/G4_MICROSTRUCTURE_AUCTION_MECHANISMS_2026-05-06.json`; 8 rows. | PASS |
| Hypothesis rows using `science_hypothesis_v1` | `02_hypothesis_registry/G4_MICROSTRUCTURE_AUCTION_HYPOTHESES_2026-05-06.json`; 14 rows. | PASS |
| Killed-route notes | Domain synthesis, `Killed-Route Notes`. | PASS |
| Experiment prereg specs using `experiment_prereg_v1` | `03_experiment_specs/G4_MICROSTRUCTURE_AUCTION_EXPERIMENT_PREREGS_2026-05-06.json`; 13 rows; all `outcome_review_opened=false`. | PASS |
| Source contracts using `source_contract_v2` | `00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json`; 7 rows; all `validation_safe=false`. | PASS |
| Goal status using `goal_status_v1` | `00_control/G4_MICROSTRUCTURE_AUCTION_GOAL_STATUS_2026-05-06.json`; commit SHA pending until scoped commit. | PASS_PENDING_COMMIT |
| Public/local evidence index and cached source evidence | `00_control/G4_SOURCE_INDEX_2026-05-06.md`; raw cache under `00_control/g4_source_evidence_raw/` with 15 fetched files and statuses recorded. | PASS |
| Neighbor-lane pass after first synthesis | Read G3 synthesis/mechanism/hypothesis/prereg/status, G6 synthesis/rows/audit, and G11 scaffold state. Added 2 G4/G3 and 3 G4/G6 blocked cross-domain hypotheses/preregs; no G11 rows added. | PASS |
| No live trading prompts/risk/execution/permissions/selectors/safety-gates/MT5/canaries/paid-data/order behavior touched | `git diff --name-only -- prompts src config scripts\canary_fixtures scripts\mt5_preflight.py scripts\canary_test.py src\components\permissions.py src\components\execution.py` returned empty. | PASS |
| No promotion claim | Focused `NO_PROMOTION_VERDICT` coverage check returned OK; schema check enforces verdict per row. | PASS |

## Focused Check Results

- JSON/schema contract validation: OK.
- Row counts: source contracts `7`, mechanisms `8`, hypotheses `14`, experiment preregs `13`, goal status `1`.
- Hypothesis label classes checked against schema enum: `broker_actual_r`, `synthetic_path_r`, `lifecycle_no_fill`, `observation_only`, `context_only`.
- Source-contract safety: every `validation_safe` value is `false`.
- Prereg status: every `outcome_review_opened` value is `false`.
- `NO_PROMOTION_VERDICT` coverage: OK across G4 source index, source contracts, status, synthesis, context ledger, mechanisms, hypotheses, and preregs.
- Forbidden-scope diff: empty for live prompt/code/risk/execution/permissions/selector/safety-gate/MT5/canary surfaces checked.
- Git state before commit: only `.context/LIVE_STATE.md` runtime dirt plus scoped untracked G4 research artifacts.

## Blockers Preserved

- Databento live GLBX.MDP3 license remains blocked.
- NAS100 broker actual-R and MBP10 candidate floors are not met.
- Sierra stacked imbalance, VAH, and VAL source definitions remain blocked.
- USDJPY/6J transfer remains review-open; GBPJPY direct orderflow proxy remains blocked.
- Nasdaq NOII and LBMA/ICE auction imbalance data require source contracts/licensing before feature use.
- G3/G6 cross-domain rows are neighbor-informed research hypotheses only, not validation.
- G11 has no neighbor-owned output yet; no G11 cross-domain G4 row was added.

## Audit Verdict

G4 research artifacts satisfy the controlling prompt requirements. The primary scoped artifact commit is `6f63dd6db39f623e9518ac6e51fcb62aa141f36b`. No live behavior was changed. No source is validation-safe. No result is promoted.

**Promotion verdict:** `NO_PROMOTION_VERDICT`
