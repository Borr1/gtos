# Session CP — the first honest read of a virgin window, and the new-family factory on true UTC

**Wave 18. Blocks B2850–B2899. Branch `phase18/true-utc-factory` from current `main`.**
Result doc: `docs/audits/fable5-vision-audit-20260725/phase18/SESSION_CP_TRUE_UTC_FACTORY_RESULT.md`.
Receipts: `phase18/receipts/`. You are Codex, working alone in this worktree. The orchestrator
(Fable 5) reviews and merges your branch; you never touch `main`, the VPS, or any broker-capable
script.

## Owner authority

Borhen's OD-ALL-IN directive (2026-08-01, `phase17/OD_ALL_IN_20260801.md`) governs: build, measure,
and bring candidates to the sealed gate. "Approved" keeps its ratified meaning — `CANDIDATE_BOOK_V1`,
all-declared basis, `B_balanced` α = 0.10 (`phase8/receipts/CANDIDATE_FAMILY_V1.json`,
`ratified_rule`). Use your own judgment throughout: this commission is a brief, not a script. If you
find something better than what is asked, build it and say why. Never refute-and-stop: a blocker is
repaired, proven impossible from available inputs, or reduced to an exact source/capture requirement.

## Standing safety boundary (unchanged, non-negotiable)

- March 2026 outcomes are NEVER read. The live-forward stream (2026-07-29+) is veto-only TEST.
  Blackout windows per the lane surface contract. CJ's April packs mechanically contain March
  lookback rows — lookback is not permission to read a March outcome, pool, or ledger.
- No broker-capable script, no VPS contact, no config/profile byte under token binding
  (`config/agent_config.yaml`, `config/profiles/redacted_account.yaml`), no activation-token action.
- `.hermes/` estates are machine-local; reference them by absolute path, never assume portability.
- Every look is declared in the iteration ledger (`phase14/receipts/TRAINING_LANE_ITERATION_LEDGER.jsonl`,
  append-only) with billed/unbilled status per the lane's DSR accounting.

## Where you start (read these before anything)

1. `phase16/SESSION_CJ_REMATERIALIZATION_RESULT.md` — the true-UTC lane estate you will use.
   The lane root is `.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/`
   inside the worktree `/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/`
   (machine-local; CJ handoff §7.4 — do not copy it, reference it read-only; registry + packs
   authenticate from there via `--lane-input-registry` with `--purpose LANE_ITERATION`).
2. `phase16/receipts/CJ_HOUR_AXIS_CORRECTION_V1.json` — the old-label → true-UTC table. AW's
   B_TIME map (83 cells) must be REGENERATED on true-UTC packs, never relabelled (session/day
   membership moves at the 00/01 boundary).
3. `phase15/SESSION_CH_LEVER_MEASUREMENTS_RESULT.md` — the family-chain state (V13→V25) and how
   looks are billed.
4. `phase17/SESSION_CL_PASS_SURFACE_RESULT.md` §2 — the two incubation dossiers and their exact
   promotion gates (historical-primary on the exact contract at both firms).
5. `WAVE_11_WORKING_AGREEMENT.md` — merge-train discipline, A/B receipt contract
   (tool-emitted `gtos-ab-receipt-v1` fence, embedded not referenced, vs the committed ZERO
   baseline in `receipts/FAILSET_BASELINE_MAIN.json`).

## The mission

The broad-family evidence was measured on a wrong clock. CJ proved the correction moves January
economics by +3.44 R (still negative). February 2026 is the FIRST economic window in this
programme's history that no process has ever read. You own its first read, and you own the first
new-family generation pass on clock-true data. Deliverables, in priority order:

1. **Pre-declare, then read February.** Write the mechanism question and the promote/reject/
   inconclusive thresholds INTO A COMMITTED RECEIPT before the first economic decode (CJ handoff
   §7.1). Then run the S0R0 arm (and S1R1 if the first read justifies it) on CJ's February packs.
   February is VAL-class, used-once; disclose it as such. The question that matters: does the
   broad V4 family's negative January expectancy persist on a virgin window at the true clock,
   or was the negative partly clock-conditioned? This is the cheapest kill-or-revive test the
   old family will ever get. ~2.6 GB / ~2.5 h per arm at the lane floor (CG's numbers).
2. **Regenerate AW's B_TIME map (83 cells) on true-UTC January packs.** The old map's hour/session
   cells are mislabelled by +2h and its day membership is wrong at the boundary. Deliver the
   corrected map with a cell-level diff (old vs new verdict per cell) so downstream sessions stop
   citing the stale one.
3. **New-family generation on true UTC.** With the corrected hour axis, run the generation pass
   the lane was built for: mine the missed-pool (CJ's compact pool,
   `pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz`, 27,658 scoreable rows, plus CD/CK's pool
   contracts) for session/hour-conditioned candidate families that the wrong clock hid.
   Declare every look. Any candidate that survives TRAIN → gate it at the ratified rule on
   RECORDED eras. You are generating CANDIDATES for the sealed gate, not arming anything.
4. **If a candidate passes the sealed gate at α = 0.10**: write the full dossier (contract,
   exit frontier, cost truth at both accounts, per-account verdicts) and hand it to the
   orchestrator's ceremony queue. Do not build an activation package yourself; the OD-ALL-IN
   pipeline arms factory output through the orchestrator's ceremony after CL-class firm-true
   pricing.

## Verification discipline

- Scoped A/B: tool-emitted `gtos-ab-receipt-v1` fence vs the committed ZERO baseline, embedded in
  `phase18/receipts/SESSION_CP_AB_RECEIPT.md`. The orchestrator owns the full-suite train capture.
- Behavioural tests for anything you wire into `src/`. Prefer behavioural over source-string.
- `IMPLEMENTATION_STATE.md` blocks B2850–B2899; retire your in-flight row in
  `tests/test_implementation_state_block_citations.py` in your closing commit.
- Result doc ends with "What I got wrong" — the standing house style.

## Hazards you will actually hit

- H1/R2: CN's merged change to `broker_net_cost_engine.py` means the R2 drift check reports it;
  that break is authorized and recorded. Do not "fix" it back. Check R2 membership before editing
  anything under `src/` (CLAUDE.md §3 H1 snippet).
- The lane registry writer is serialized by an advisory lock (CJ's B-item 9): never run two pack
  builders concurrently.
- `scripts/gtos_hydrate_test_data.py` hydrates on ANY invocation including `--help` (CM's
  gotcha #4).
- pytest here has no `--timeout` plugin.
- LFS: `git lfs checkout <path>` before believing any drift count (B185); never clean
  `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` in the MAIN repo (B905) — irrelevant
  to your worktree but fatal if you wander.
