# Ultimate-System Continuation Directive

Status: read-first control directive for the active ultimate-convergence execution goal.

Purpose: keep continuations from drifting into one-symptom patches, immediate broad replays, stale subagent claims, or conservative narrowing. This is not a new scope and not paperwork for its own sake. It is the execution contract before patching or replaying.

## Read This After Compaction Or Restart

Before the next patch or replay:

1. Inspect current process state. If a broad replay is running, decide from current evidence whether to let it finish, parse it, or intentionally replace it.
2. Regenerate/read current disk state and use GTOS Context OS.
3. Read the current root-cause map and pre-replay brief.
4. Consolidate current disk evidence into one root-cause map and one pre-replay brief if they are stale.
5. Patch grouped same-root failures across the affected chain, not one isolated symptom.

## Required Pre-Replay Brief

The brief must include:

1. current latest completed replay prefix and numbers;
2. any currently running replay and whether it should finish, be parsed, or be intentionally replaced;
3. baseline comparison against V89D, V90, V92, and the newest completed run;
4. current dirty files and active code changes;
5. subagent findings already received, with each marked incorporated / rejected / deferred and why;
6. known mismatch classes across source-bound -> candidate -> selector -> scheduler -> risk -> order -> lifecycle -> fill -> exit -> ledger;
7. which issues are fixed, partially fixed, still open, or newly exposed;
8. the highest-leverage same-root batch to patch next;
9. the exact files/components affected by that batch;
10. whether each patch is a correctness repair, performance repair, or diagnostic/ledger repair;
11. expected measurable effect before replay for candidate -> scorecard transfer, scorecard -> order transfer, order -> fill transfer, missed positive R, missed negative R, trade count, net/gross/final R, W/L/F, cost-refused/source-gap execution, and risk-reduced/full-risk distribution;
12. what replay result would prove the batch helped, failed, or exposed the next deeper flaw.

## Replay Discipline

- Do not run broad replay just because one patch landed.
- Run targeted bucket/projection replay first when it can prove the same-root repair faster.
- Run broad replay when the patch affects global behavior or after targeted proof passes.
- Do not accept positive-by-suppression. Every improvement must say whether it came from better candidate conversion, selector admission, scheduler/reallocation, risk sizing, order/fillability behavior, lifecycle handling, exit/profit-harvest behavior, or simply blocking trades.
- Do not overfit the May 13-17 2026 window. Treat it as a hostile/stress bucket, then test other objective regimes before calling the system strong.
- Do not compare a one-day or five-day repaired replay directly against the full source-bound reservoir. Short smokes prove or disprove local code/truth repairs only. For every replay, report the exact selected replay-window denominator: source-bound R available inside that window, package axes available inside that window, candidate-generated axes, scorecard/order-present axes, filled-trade axes, and actual executable R. Keep diagnostic/global reservoir fields separate and explicitly mark them as not the replay denominator. Use this interpretation for bounded smokes: "This smoke proves or disproves the local repair; it does not prove total reservoir conversion."
- Discuss full-reservoir transfer only after the corrected executable path is run across the broad historical universe or another replay whose selected window covers the configured full available universe.

## Authority Boundary

Keep full 82-sleeve authority and missed-opportunity accounting. Do not top-N narrow, hardcode date/symbol/session loss buckets, or hide behind broker/live/final closure. Broker/live/final stay false, but local replay/package evaluation has full authority.

The point is structured execution: gather known evidence, patch the whole same-root failure across all affected layers, then replay with clear success/failure criteria.
