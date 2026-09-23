# Session CQ — path-complete pools, the frozen 99-cell grid, and the breaker repair

**Wave 18. Blocks B2900–B2949. Branch `phase18/path-complete-pools` from current `main`.**
Result doc: `docs/audits/fable5-vision-audit-20260725/phase18/SESSION_CQ_PATH_POOLS_RESULT.md`.
Receipts: `phase18/receipts/`. You are Codex, working alone in this worktree. The orchestrator
(Fable 5) reviews and merges your branch; you never touch `main`, the VPS, or any broker-capable
script.

## Owner authority

Borhen's OD-ALL-IN directive (2026-08-01, `phase17/OD_ALL_IN_20260801.md`) governs. Use your own
judgment throughout: this commission is a brief, not a script. Never refute-and-stop: a blocker is
repaired, proven impossible from available inputs, or reduced to an exact source/capture requirement.

## Standing safety boundary (unchanged, non-negotiable)

Same as every wave: March 2026 outcomes NEVER read; live-forward is veto-only TEST; no
broker-capable script, no VPS contact, no token-bound config byte; every look declared in the
iteration ledger; `.hermes/` estates are machine-local.

## Where you start (read before anything)

1. `phase16/SESSION_CK_MECHANISM_AUTOPSY_RESULT.md` — the mechanism verdict and the exact gap you
   are closing: CD's pools lack ordered candidate paths, so CK could answer only 1 of the 99 cells
   exactly. `CK_POOL_PATH_CONTRACT_V1` (its receipt) is the declared contract; CK repaired
   `cd_pool.py` so FUTURE pools carry paths — nobody has yet BUILT the path-complete pools.
2. `phase16/SESSION_CJ_REMATERIALIZATION_RESULT.md` — the true-UTC lane. New pools are built on
   TRUE-UTC packs (lane root: `.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/`
   in `/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/`, read-only, registry via
   `--lane-input-registry` + `--purpose LANE_ITERATION`). CJ's compact S0R0 pool
   (`phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz`, 27,658 rows) is the reference
   population; note it predates path-completeness.
3. `phase15/SESSION_CG_LANE_FOOTPRINT_RESULT.md` — lane floor 480 s / 2.9 GB per bounded run;
   full-January arm ~2.5 h. Budget accordingly; serial pack building only (advisory writer lock).
4. CK's H-CD-7 note: the real hazard was 15 orphaned CD pool PIDs — bounded fixtures serial-prewarm
   via `sealed_inputs.py:170-193`; do not regress that.

## The mission

CK proved the January hole is mechanism-heterogeneous and cost-vetoed, but could not answer the
frozen 99-cell grid because the pools carry no ordered paths. You close that, on the right clock:

1. **Build path-complete pools under `CK_POOL_PATH_CONTRACT_V1` on true-UTC packs** for January
   (S0R0 at minimum; S1R1 if the grid needs the sizing side). Every row carries the ordered
   candidate path the contract demands. Authenticate against the lane registry; declare every look.
2. **Answer the frozen 99-cell grid exactly.** The grid was pre-declared by CD/CK; its cells are
   binding questions, not suggestions. Report every cell with its verdict and the look accounting.
   The two named mechanisms come first:
   - `current_breaker_re_entry` — measured −0.82755 gross R/row on 15.19 % of rows = 21.55 % of all
     negative gross (maxT p 0.000999). The grid decides whether a REPAIR (suppress/repair the
     re-entry) survives out-of-cell.
   - `liquidity_sweep_reclaim × LONG` — +0.03177 FULL gross but −0.48234 net: a cost problem.
     With CN's commission truth now merged, re-price it broker-true before calling it dead.
3. **If a repair cell survives**: wire the `current_breaker_re_entry` repair as a default-off,
   testable candidate transform and gate it at the ratified rule (`CANDIDATE_BOOK_V1`,
   `B_balanced` α = 0.10) on RECORDED eras. A surviving repaired family goes to the orchestrator's
   ceremony queue as a dossier; you arm nothing.
4. **First-touch ambiguity** — CK bounded it at 0–11.91 % (optimistic reading can explain the whole
   remaining hole). Path-complete pools can measure it exactly; do so and retire the bound.

## Verification discipline

Scoped A/B: tool-emitted `gtos-ab-receipt-v1` fence vs the committed ZERO baseline, embedded in
`phase18/receipts/SESSION_CQ_AB_RECEIPT.md`. Behavioural tests for anything wired into `src/`.
`IMPLEMENTATION_STATE.md` blocks B2900–B2949; retire your in-flight row in your closing commit.
Result doc ends with "What I got wrong". pytest here has no `--timeout` plugin;
`gtos_hydrate_test_data.py` hydrates even on `--help`.

## Coordination

Session CP (`phase18/true-utc-factory`) works the same lane concurrently: it owns February's first
economic read and the B_TIME regeneration. You own pools/grid/breaker. Do not read February
economics — that is CP's pre-declared read; if your pool work needs a February population, build
packs/pools without decoding outcome fields and leave the first economic read to CP. The lane
registry writer is serialized by an advisory lock; if you hit it, back off and retry rather than
bypassing it.
