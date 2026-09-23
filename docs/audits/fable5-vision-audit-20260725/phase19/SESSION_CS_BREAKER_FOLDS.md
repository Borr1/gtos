# Session CS — two more path-complete folds decide the inverted breaker

**Wave 19. Blocks B3000–B3049. Branch `phase19/breaker-folds` from current `main`.**
Result doc: `phase19/SESSION_CS_BREAKER_FOLDS_RESULT.md`. Receipts: `phase19/receipts/`.
You are Codex, working alone in this worktree. The orchestrator (Fable 5) reviews and merges;
you never touch `main`, the VPS, or any broker-capable script.

## Owner authority

OD-ALL-IN (`phase17/OD_ALL_IN_20260801.md`) governs. Brief, not script; build/improve/fix,
never refute-and-stop. If the gate ADMITS, the repair goes to the orchestrator's ceremony queue
with a full dossier — you arm nothing yourself.

## Standing safety boundary

March 2026 outcomes NEVER read — **and CJ's April packs mechanically contain March lookback
rows; lookback is not permission to decode a March outcome**. February 2026 is CP's used-once
VAL — do not re-read its economics. Live-forward veto-only. No VPS, no broker-capable scripts,
no token-bound config bytes. Every look declared. `.hermes/` estates machine-local.

## Read first

1. `phase18/SESSION_CQ_PATH_POOLS_RESULT.md` — you are executing its §8 prescription exactly:
   the ratified gate on `cq_current_breaker_re_entry_inverted_5d_stop_0p25d` returned
   `NOT_EVALUABLE` on one evaluable chronological fold; it requires **two additional evaluable,
   path-complete chronological folds under the UNCHANGED transform, cost truth, population rule
   and gate contract** (`CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json`).
2. `phase18/receipts/cq_path_pool_grid.py` + `cq_repair_gate.py` — the committed tools. Reuse
   them; do not re-derive the grid (its 201 looks are spent and answered).
3. `phase16/SESSION_CJ_REMATERIALIZATION_RESULT.md` §2 — the eligible history: CJ's true-UTC
   **April 2026 (30 packs) and May 2026 (31 packs)** exist and are economics-unread. They are
   the natural source of the two folds. Ordered-tick coverage is 4/24 symbols for April
   (through Apr 29) and 0/24 for May — CQ's conservative M1 ambiguity semantics already handle
   tick absence; carry the same conservatism and report ambiguity counts per fold.
4. `src/components/current_breaker_re_entry_repair.py` + `broader_origin_generators.py:343-368`
   — the default-off production transform. The gate re-run uses candidates produced by THIS
   transform (as CQ's did), not a re-implementation.

## The mission

1. **Materialize the two folds.** Run the S0R0 candidate surface over CJ's April and May packs
   (LANE_ITERATION purpose, registry authenticated, serial builders), build the path-complete
   pools with the same sidecar contract as `CQ_TRUE_UTC_S0R0_PATH_POOL_V1` (ordered ticks where
   they exist, conservative M1 otherwise), and produce the breaker-repair trade records with
   exact exit timestamps through the production transform.
2. **Declare before reading.** The fold boundaries, population rule, cost truth, and the
   promote/reject thresholds are the UNCHANGED ratified gate contract — write the fold plan
   into a committed receipt before the first economic decode of either month. April/May become
   used-once VAL surfaces for this question; disclose it.
3. **Re-run the unchanged ratified gate** (RECORDED, FTMO mid band, `B_balanced`, α = 0.10,
   all-declared at the **V27** tip — 59 declared / 57 looks) with ≥3 evaluable folds total. No
   new graduation bill for the already-billed member; declare any genuinely new look.
4. **Report the verdict honestly.** January's +11.9 R/trade diagnostic is not permission to
   relax anything; if April/May kill it, that is the answer and it is cheap now versus live.
   If ADMIT: full activation dossier (exact live contract through the transform, cost truth
   both accounts, CL-class firm-true MC pricing, per-account verdicts) to the ceremony queue.

## Verification discipline

Scoped A/B: tool-emitted `gtos-ab-receipt-v1` fence vs the committed ZERO baseline, embedded in
`phase19/receipts/SESSION_CS_AB_RECEIPT.md`. Behavioural tests for anything wired into `src/`.
IMPLEMENTATION_STATE blocks B3000–B3049; retire your in-flight row in your closing commit.
Result doc ends with "What I got wrong". The lane registry writer is serialized by an advisory
lock — Session CR runs concurrently; if you hit the lock, back off and retry. pytest has no
`--timeout`; `gtos_hydrate_test_data.py` hydrates even on `--help`; the R2 drift check reports
CN's authorized engine break — leave it.
