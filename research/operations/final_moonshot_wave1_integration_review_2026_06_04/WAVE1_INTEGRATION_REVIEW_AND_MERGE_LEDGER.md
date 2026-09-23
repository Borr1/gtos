# Wave1 Integration Review And Merge Ledger

Date: 2026-06-04
Integration branch: `final-moonshot-wave1-integration-2026-06-04`
Authority base: `bc797b1081a79ea77aa640f8094d24f21a056932`
Merged head before context commit: `125a7a434ebddd3b352b3f4df875437d4f83da72`

## Merge State

| Lane | Source commit | Merge commit | Decision |
|---|---:|---:|---|
| Wave1A hard-halt forensic matrix | `01783e05a` | `9336f8542` | Accepted |
| Wave1B V3/live authority gap | `af1c94e4c` | `e388f0380` | Accepted |
| Wave1C dual-broker architecture | `5ce6e39df` | `125a7a434` | Accepted |

`main` was not pushed during this review. No broker/runtime/VPS production surfaces were touched.

## Disk Review

Wave1A accepted broker-real denominator truth: `77` grouped redacted_account trades, `31` wins, `46` losses, `-859.69` broker-real net cash, `54` SL/broker-SL exits for `-9280.84`, `548` matrix rows, `471` candidate trade records, `108` exact-R rows, and `24` proxy-R rows.

Wave1B accepted authority truth: V3 was not full live authority. The route matrix has `12,775` rows across runtime decisions, replacement snapshots, pending lifecycle, trade records, and broker-truth trade groups. The accepted production change is capture-only `v3_live_authority` packet emission inside native candidate packets; it records no broker operation and no order calls.

Wave1C accepted architecture truth: redacted_account remains the full primary runtime; FTMO is follower/projector only. FTMO consumes accepted canonical intents, then applies FTMO broker-local risk, lifecycle, and crash recovery. Primary lots, fills, cash PnL, and specs are not copied into FTMO.

## Integration Finding

The first merged focused pytest run failed `4` broader-origin tests because pending-order record indexing writes `_pending_records_index.json`, and those tests globbed every JSON file under the trade-record symbol directory. The production trade record was valid; the tests were reading index metadata nondeterministically.

The integration fix filters index metadata in `tests/test_vnext_broader_origin_orchestrator.py` and hardens `SessionOrchestrator._emit_dual_broker_intent()` to derive profile and namespace via `getattr`/config fallbacks for `__new__` test orchestrators. The rerun passed `116` focused tests.

## Verification

- Wave1A route artifact audit with full JSONL scan: pass.
- Wave1B route artifact audit with full JSONL scan: pass.
- Wave1C route artifact audit with full JSONL scan: pass, with the known non-fatal `blocker_or_repair_ledger` warning from the original package.
- Wave1A route verifier: pass.
- Wave1B route verifier: pass.
- Wave1C root and route verifiers: pass.
- Wave1A, Wave1B, and Wave1C prompt hardening checks: pass.
- Changed-path `py_compile`: pass.
- Merged focused pytest after integration fix: `116 passed in 3.43s`.

## Next Program Decision

Wave1 is accepted as the current post-hard-halt evidence base. The next lane is Wave2 Final Master After Hard Halt: synthesize Wave1A/B/C into the authoritative post-halt master, produce the Wave3 V4 lane plan, and generate launch-ready prompts/worktrees for the V4 selector, scheduler, execution manager, same-symbol lifecycle, cost/swap/slippage engine, market whiteboard, data capture/source repair, runtime control, and LiveDecisionPacketV4 lanes.
