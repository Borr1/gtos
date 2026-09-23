# Session Z — make the learning stack safe to run

**Stage 5, the estate.** Worktree `worktrees/wave5-trainer-partitions-20260729`, branch
`phase5/trainer-partitions`, from `main`. **Blocks B510–B539.**

**Read `../WAVE_5_WORKING_AGREEMENT.md` first** — especially §3 — then `../WAVE_5_PLAN.md`.

---

## Why now

**FTMO is armed and trading real money** (2026-07-29 12:55 UTC — `CLAUDE.md` §4). The charter's
destination is *replay at scale → feature store → label store → trained models → default-off runtime
intelligence → daily learning loop*. The programme has reached live execution with the **training end
of that chain never made safe to run**, and the standing plan says so:

> Learning lane: … trainer hygiene (per-fold specs, purge/embargo, ~1 AS) **before any training run**;
> the B7.5 partition registry re-authored — **the existing one marks March 2026 as TRAIN and it must
> never be passed to the builder as-is.** (`THIRD_REVIEW.md` §4, Stage 5)

Session R closed the *decision* half of the loop: `recommend()` now consumes live realized evidence at
broker truth, brake-only, default-off. What it feeds is a re-rate rule, not a model. **Nothing has
made the model-training path trustworthy**, and the first person to run it will get a number that
looks fine.

## The hazard that outranks everything else here

**March 2026 is the only outcome-unread month the programme has left.** It is the scarcest resource
in the estate — the last clean window for any future treatment of the broad family — and
`CLAUDE.md` §4 keeps it deliberately unread.

A partition registry that marks it **TRAIN** is not a labelling error. Handing it to a builder burns
the window *and* leaks it into a model that will then be validated against data it has effectively
seen. **Find it, prove what it says, and make it impossible to pass as-is** — a registry that refuses
rather than a comment saying don't.

Verify the claim before you build on it. It is the orchestrator's relay of the plan's text, and
Session W found that a similarly-relayed claim ("there is no walk-forward implementation anywhere")
was false because the search behind it was malformed. **If the registry does not say what this prompt
says, publish that and act on what you find.** Session AC found a related surprise: the plan's
"B7.5 partition registry" may not be a single file — W reported no file by that name and placed the
hazard on a different route. Resolve which is true.

## What you own

**1. Trainer hygiene: per-fold specs, purge and embargo.** The requirement is that a fold's training
data cannot contain information from, or adjacent to, its test window. This programme's data makes
that harder than the textbook case, and the reasons are measured:

- **Positions cross bar boundaries.** Median live hold at broker truth is **1.2603 h**, but the
  used-fraction of horizon across twelve live sleeves runs **0.4 % to 105 %**, three exceeding their
  nominal horizon. An embargo sized off a nominal horizon is wrong for at least three sleeves.
- **Trades cluster by day, and not weakly.** `crypto` fired 104 times on 67 dates, lag-1 ρ 0.441;
  `metals_core` up to 12 in one day, ρ 0.511. Row-level splitting leaks.
- **The timestamps are broker wall clock, not UTC**, whatever the field is named. Convert with
  `src/utils/broker_clock.py`, which fails closed on an unregistered server.

**Do not build this from scratch before reading `src/research_infra/validation_integrity/`** — 15
modules, 94/94 green, including a purged/embargoed walk-forward, DSR, PBO, permutation nulls and a
composing gauntlet. Session W's largest win was composing them instead of rebuilding. If what you need
exists, use it and say so; if it exists and is *wrong*, that is a better finding than a new module.

**2. Re-author the partition registry** so a leaking split cannot be produced silently. Fail closed.

**3. Say what the learning stack can and cannot be trusted to do today**, in one place a future
session can act on. R's honest headline is the model: *"the live record says nothing about any armed
sleeve … closing the loop was necessary and it does nothing today."* Match that standard.

## A known defect on your path

`src/research_infra/validation_integrity/regime_inflation.py` flags contamination on a **positive**
ratio threshold, so once the full-history mean goes negative **the flag can never fire** — the
detector is defeated by making the concealed loss bigger. Same sign-error family as F39. Session W
guarded its own call site only; Session X may have fixed the module — **check `main` before you
touch it**, and if it is still broken, fix it properly and say so in your first commit message
(agreement §3 item 4).

## Traps

- **Do not edit `config/agent_config.yaml`.** The live activation token binds its digest
  (`ffe16657feaf`); one byte and the armed FTMO book refuses to place. It is also H1-bound.
- **Check H1 membership before editing under `src/`** (agreement §6.4). A bound-file edit costs a
  re-seal plus ~16.5 machine-hours per window.
- **Do not run a replay arm.** A sealed month is ~16.5 machine-hours and this machine is the
  constraint; nothing in your scope needs one.
- **Keep March outcome-unread.** If your work would require reading it, stop and say so instead.

## Method

**Commission refuters and default them to "refuted."** Distinct lenses: one that tries to construct a
leaking split your guard accepts, one on whether your embargo is correct for the three sleeves that
exceed their nominal horizon, one that checks you did not rebuild something
`validation_integrity/` already provides, one on whether the March hazard is where this prompt says.

Every session in waves 3–5 that ran refuters had real errors found — W's admitted a sleeve that lost
**17,840 R**; AC's refuted its own runbook outright with five criticals, one of which would have
deleted a module from a live trading host mid-restart. Assume yours can find something equally bad.

**A clean negative beats a rescued pass.** If the honest conclusion is that this data cannot support
trustworthy training without a capture that does not exist, say which capture and why. That is a
result.

## What is NOT yours

Do not touch the VPS — FTMO is live on it. Do not arm, disarm, mint or revoke anything. Do not run a
broker-capable script (agreement §1). Do not merge to `main`. Do not train a model — you are making
training *safe*, not doing it.

Use your own judgment on approach, scope, and on whether anything above is wrong.
