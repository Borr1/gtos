# G12 NOFILL Read-Only Tick Recovery Export Source-Control Audit Goal Prompt

Date: 2026-05-10
Owner lane: independent G12 source-control audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE`.

Verify the route pursued all `31` tick/export-dependent blocker rows and all `22` grouped owner/export requests through the market-data recovery ladder, without inferring GTOS source-state truth from price. Recompute the `20` recovered grouped tick sources, the `2` remaining XAUUSD owner/export requests, the `28` recovered candidate rows, the `3` remaining candidate rows, and the `12` contamination/embargo exclusions.

This audit must be strict about evidence and aggressive about audit depth. Do not accept "read-only extraction returned zero ticks" unless the target route records source, command/API class, symbol mapping, UTC window, timezone handling, extraction status, error/retcode if any, and why the zero-row result is not a setup/config/symbol-selection failure. Do not reject exact remaining requests merely because they are not recovered; accept them only if the recovery ladder is demonstrably exhausted inside the allowed market-data source-control evidence class.

## Mandatory Preflight

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\goal_session_research_discipline.md`.
7. Read `.context\00_core\local_heavy_data_inventory.md`.
8. Read `.context\00_core\research_current_state.md`.
9. Read the target route artifacts under `research\science_program_2026_05\06_outcome_testing\nofill_readonly_tick_recovery_export_source_control_route\`.
10. Read `.context\00_core\goal_session_research_discipline.md` standing owner-access pursuit rule and verify the target route complied with it.

## Required Audit Checks

- Parse every target JSON artifact and verify all safe flags remain false with `NO_PROMOTION_VERDICT`.
- Recompute the 31-row and 22-grouped-request reconciliation from the upstream G12 grouping ledger and target route ledgers.
- Recompute the `20` recovered grouped source count and `28` recovered candidate-row count from the recovery ladder, grouped request reconciliation, recovered/absent window ledger, and source hash manifest; do not rely only on the completion audit.
- Rehash each recovered raw tick source path if it exists locally; if not present, verify the committed source-hash manifest records exact hash, size, schema, timestamp span, field coverage, symbol/broker-symbol mapping, and source path.
- Verify every recovered source proves requested UTC-window coverage, not just full-day file presence. Check min/max timestamps, in-window row count, field availability, and alias compatibility.
- Verify no raw parquet/CSV tick source is tracked or staged.
- Verify the two remaining owner/export requests are exactly XAUUSD `2026-04-15` and XAUUSD `2026-04-16`, with read-only extraction attempted and zero ticks returned.
- For those two remaining XAUUSD requests, independently audit that the target route exhausted executable source-safe recovery paths: active catalog search, absolute tick roots, prior worktree/source artifacts, ignored local export paths, approved tick roots, Sierra/vendor/cache roots when available, and approved read-only market-data extraction. If any same-evidence-class source-safe recovery path is unsearched or ambiguous, reduce it to an exact repair blocker or repair it inside the G12 audit write scope if safe.
- Confirm the zero-tick read-only extraction attempts are not explained by wrong symbol, wrong UTC/day boundaries, disconnected terminal, unavailable symbol, market-session closure, weekend/holiday mismatch, or an extraction script bug. If this cannot be confirmed from artifacts, block acceptance with an exact repair prompt.
- If the remaining XAUUSD requests are accepted as exact, produce a next route recommendation that is not passive: either exact owner/manual export instructions, an alternate-source recovery route, or forward-capture/source-state next step, with one-line starter and full prompt where appropriate.
- Verify contamination/embargo rows remain excluded from clean denominators and no recovered tick file admits a row without pending lifecycle/write-clock/order-observability source-state truth.
- Verify no validation execution, result scoring, broker actual-R, MT5 account/order/history/deal/position values, paid/API/Databento route, registry edit, remote push, live restart, prompt/config/risk/permissions/safety/selector/canary change, or live trading behavior occurred.
- Run the target verifier and focused tests.
- Produce a G12 audit report, machine ledger, source-hash/window-coverage audit, no-leak/staging audit, remaining-request exhaustion audit, completion audit, and next-route recommendation.

## Hardening Requirements

Do not stop at surface verification. If a target claim is exact and source-safe, accept it. If it is incomplete but repairable inside this G12 write scope without opening validation/live/forbidden surfaces, repair and record the repair. If it belongs to the target route or a next recovery route, write an exact repair/source prompt with file paths, expected counts, command/source details, and no-leak boundaries.

Do not let the audit become a recovery route unless the action is an audit-safe verification step. This G12 route may verify local files, hashes, source ledgers, and extraction evidence; it must not silently commit raw market data or open result/validation/live behavior.

## Completion Standard

Mark complete only when the audit proves the target route satisfies the controlling prompt, all JSON artifacts parse, verifier/tests pass, recovered source hashes/window coverage are verified, the two remaining XAUUSD requests are either accepted as exact after recovery-ladder exhaustion or reduced to exact repair blockers, raw tick files are not tracked/staged, source-state boundaries are preserved, next-route recommendation exists, and the terminal decision is accepted with `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
