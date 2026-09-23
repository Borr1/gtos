# Session F — Divergence matrix v2

**Phase 1 item 4.** Worktree `worktrees/phase1-divergence-matrix-20260726`, branch
`phase1/divergence-matrix`, branched from `main`. **Your block range is B70–B79.**

**Read `../WAVE_2_WORKING_AGREEMENT.md` first** — authority, orchestration grant, hard constraints, and
four environment traps found and fixed the night before this wave.

---

## What this is

A first-class artifact beside **every** arm receipt, auto-generated, and **required by the arm acceptance
path**. It carries three divergences:

- **execution-model divergence** — the E1 table (replay runs a portfolio allocator, Selector V4 admission
  and continuous sizing that the live path does not implement)
- **strategy-family divergence** — F1 (the sealed replay measures one strategy family; the declared live
  book is another)
- **clock divergence** — F7 (now measured and repaired; the residual is what remains)

The point is H7, currently a paragraph of prose in `CLAUDE.md`: *"Replay does not measure the live
system. Do not transfer replay R to a production claim without the divergence matrix."* Today that
warning depends on somebody remembering it. After this session it is an artifact the acceptance path
refuses to proceed without.

**That is the real deliverable — a mechanism, not a document.** If you conclude partway through that a
different mechanism enforces H7 better than a generated matrix, make that case and build the better one.

---

## You can start immediately; one input arrives mid-session

Two of the three divergences are documented **now**:

- **E1** — `docs/audits/opus5-architecture-20260725/FINAL_INDEPENDENT_AUDIT.md` and its divergence
  matrix; `MISMATCH_AND_RISK_REGISTER.md`.
- **F7** — `CLOCK_TRUTH_IMPACT_NOTE.md` plus `IMPLEMENTATION_STATE.md` B27–B31 and B56/B58. The clock
  divergence is now *measured*, so this row should carry numbers, not a caveat.
- **F1** — `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md`, the two-stacks finding.

The **live-divergence row set is Session E's deliverable** (Gate G1b), running right now in
`worktrees/phase1-w7-forensics-20260726`.

### Coordination with E — concrete, because "agree early" is not a mechanism

E has been told to push `LIVE_DIVERGENCE_ROW_SCHEMA.md` to `origin/phase1/w7-forensics` within its first
working hour. Fetch it:

```bash
git fetch origin phase1/w7-forensics
git show origin/phase1/w7-forensics:docs/audits/fable5-vision-audit-20260725/LIVE_DIVERGENCE_ROW_SCHEMA.md
```

If it is not there yet, **design your own, push it on your branch, and tell Borhen** so E can adopt it.
**Whoever pushes a schema first owns it; the other adapts.** A tiebreak rule, not a negotiation — it
exists so neither of you rewrites at the end. Do not block on E either way: build the generator against
the three divergences you already have.

---

## Design constraints that decide whether this survives

**Auto-generated, not hand-maintained.** A hand-written matrix is stale the first time anything changes,
and this repo has just spent two waves proving how much drifts. Derive each row from something
machine-readable: config, code, a sealed artifact, a receipt. Where a row genuinely cannot be derived,
mark it explicitly as a declared constant with an owner and a date — never let a hand-typed value look
derived.

**Required by the arm acceptance path.** That is the plan's word: *required*. A matrix merely produced
beside a receipt gets ignored. The acceptance path already fails closed on missing inputs —
`replay_acceleration_attempt5_typed_sparse_runner.py:400` raises `runtime_evidence_input_missing:<name>`
(guard block from ~366) — follow that pattern rather than inventing a softer one.

**Fail closed on an unknown divergence.** The failure mode you are guarding against is a replay number
being read as a live number. If a divergence cannot be quantified, the matrix must say `UNQUANTIFIED`
loudly rather than omit the row. Session D's harness is the model: every condition it cannot classify
becomes `UNKNOWN`, and `EQUIVALENT` requires that nothing was unknown.

**H1 shapes the wiring.** The runner and `agent_config.yaml` are decision-contract-bound; editing either
forces a re-seal and ~16.5 h/window of re-runs. Run the membership check before touching anything under
`src/`, and prefer a wiring that needs no bound file — a hook, a wrapper, an acceptance-time check that
reads rather than modifies.

If the *only* correct wiring requires a bound file, that is a re-sealing decision and it belongs to
Borhen: **surface it to him with the cost stated, deliver the generator plus the exact one-line change it
would need, and carry on with everything else.** Do not absorb the decision, and do not let it stop the
session — a shipped generator with a documented final wire-up is a good outcome.

---

## Two things to check rather than assume

1. **Does an arm receipt already carry any of this?** Some routes record divergence-adjacent fields. Find
   out before adding a second, disagreeing source of the same fact.
2. **F7's row is no longer hypothetical.** The clock repair landed, so the honest row is "corrected going
   forward; sealed arms unchanged and comparable; session-level attributions inside sealed evidence carry
   a stated caveat". Read `CLOCK_TRUTH_IMPACT_NOTE.md` §5–6 for exactly what was and was not repaired —
   nine gaps are declared there and several belong in your matrix.

## Deliverables — the floor

1. The generator, with behavioural tests, producing the matrix from machine-readable sources.
2. The matrix rendered for the four sealed January arms — the corpus that already exists.
3. The wiring that makes it required by arm acceptance, **or** the precise one-line change plus its
   re-seal cost, surfaced to Borhen.
4. `IMPLEMENTATION_STATE.md` blocks **B70–B79**.

Commit scoped work as you go, and push your branch. Do not merge to `main`.
