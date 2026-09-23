# Session Y — make seven sleeves judgeable

**Stage 5, the estate.** Worktree `worktrees/wave5-first-of-day-20260729`, branch
`phase5/first-of-day-port`, from `main`. **Blocks B480–B509.**

**Read `../WAVE_5_WORKING_AGREEMENT.md` first** — especially §3 — then `../WAVE_5_PLAN.md` §0–§1.

---

## What is blocked on you, and why nobody can route around it

**A live funded FTMO account is trading four sleeves as you work** (armed 2026-07-29 12:55 UTC; see
`CLAUDE.md` §4). The programme built **34** sleeves. Twelve were judged and rejected. Four are armed.
**Nine candidate sleeves cannot be judged at all**, and you are the reason that changes.

Session K measured the generation port's fidelity by sleeve structure
(`phase3/K1_GATE_RECEIPT.md` §3) — and the split is not noise:

| class | agreed | live-only | **live-recall** | sleeves |
|---|---:|---:|---:|---|
| **per-bar** — each bar judged on its own | 160 | 7 | **96 %** | the 14 `mx_*`, `fx_jpy`/`fx_jpy_ny` (100 %), `idxrev` |
| **first-of-day** — emits only on the session's *first* qualifying event | 40 | 175 | **19 %** | `asian_fade`, `asia_pdl_fade`, `orb_crypto_london`, `metal_session_reversion`, `ny_crypto_momentum`, `kz_london_crypto_low`, `liq_asia_up_low_metal` |

**A gate result for a first-of-day sleeve today measures the port's defect, not the sleeve.** Session W
refused to score them for exactly this reason and was right to. Until you land, those seven are
unjudgeable — not rejected, *unjudgeable*, which is worse because it looks like the same thing on a
summary table.

K's §3.5 explains why the gap tracks *structure* rather than symbol, timeframe or data quality.
**Read it before you write anything.** Completing the bars archive did not move it: evidence-gap
misses went to zero, 7 of 28 bar-blocked intents reproduced, 21 became genuine misses, and count
agreement moved *down* 0.15 pp. Every residual disagreement is a real one.

## What you own

**1. Diagnose the first-of-day path against live truth.** 175 live-only intents are enumerated in
`receipts/K1B_DISAGREEMENTS.json`. That is your ground truth: the live book emitted them, the port
did not. Find out why, per class, with a mechanism you can point at in code — not a hypothesis that
fits the aggregate.

The obvious candidates, none of which you should believe without measuring: session-boundary
definition (whose midnight — broker server, UTC, or the instrument's session?), first-event latching
across a restart, state that lives in the live process and is absent in the port, and bar-close vs
tick timing at the session open. **`src/utils/broker_clock.py` is the production answer for "which
midnight" and it fails closed on an unregistered server — use it rather than an offset.**

**2. Fix it, and re-measure K1-b.** The gate's standard is *zero disagreements, or an enumerated and
classified list*. K delivered the second. If you can reach the first, do. If you cannot, deliver a
smaller and better-classified residual and **say exactly what remains and why** — a first-of-day
recall of 60 % that you understand is worth more than 95 % you cannot explain.

**3. State the fidelity ceiling each sleeve can now be judged at.** W's gate refuses to score below a
generation-fidelity floor. Your output is what tells it which of the nine become scoreable. If some
remain unscoreable, name them and say what would fix it.

**4. Do not score them yourself.** Session W owns the admission standard and Session X owns the
book-level question. Your job is to make the evidence trustworthy, not to render the verdict. If you
find something that changes what the gate *should* be, say so — but do not quietly build a second one.

## Traps

- **This is a live-code path.** `book_engine.py` and the sleeve registry are what the armed FTMO book
  runs. Check H1 decision-contract membership before editing under `src/` (agreement §6.4), and
  remember the armed book resolves through `--tags` ∩ `effective_registry` — if you change generation
  semantics, say plainly whether it can affect `crypto`, `energy_agri`, `metals_core` or
  `sub_xvol_pullback`. **If it can, that is a finding to publish before you land it, not after.**
- **Do not edit `config/agent_config.yaml`.** The live activation token binds its digest
  (`ffe16657feaf`); a single byte changes it and the armed book refuses to place. It is also H1-bound.
- **The bars archive is broker wall clock, not UTC.** Every file carries a `.timebase.json` saying so.
  Convert with `broker_clock.broker_epoch_to_utc`; never trust a `_utc` field name. M15 reaches back
  only to 2024-01-01 — thin for intraday sleeves, and worth saying if it bounds you.
- **"first-of-day" is a claim about the code, not a category you inherit.** Verify which sleeves
  actually latch, from the source, before you accept K's split. K's own lesson (B171, after three
  confident wrong answers): *"do not transfer a rate and defend the transfer."*

## Method

**Commission refuters and default them to "refuted."** Distinct lenses: one that checks your fix
against the live-only intents it was *not* fitted on, one on whether you changed live generation
semantics for the armed sleeves, one on timezone/session-boundary correctness across a DST seam, one
that tries to reproduce your recall number independently.

**Three of the orchestrator's own claims were refuted this week by malformed probes** — a `rg -r`
misuse that "proved" a module didn't exist, a raw `mt5.symbol_info` call that bypassed the production
symbol resolver and reported two live sleeves as untradeable, and a regex demanding a quote the shell
never emitted. **When your probe says something surprising, suspect the probe first.**

**A clean negative beats a rescued pass.** If the first-of-day path cannot be reproduced faithfully
from bars alone — because the live book carries state no replay can reconstruct — then say so, prove
it, and say what capture would fix it. That is a result, and it retires a question that has been open
since wave 3.

## What is NOT yours

Do not touch the VPS — FTMO is live on it. Do not arm, disarm, mint or revoke anything. Do not run a
broker-capable script (agreement §1). Do not merge to `main`. Sleeve composition, the risk dial and
the admission standard are Borhen's.

Use your own judgment on approach, scope, and on whether anything above is wrong.
