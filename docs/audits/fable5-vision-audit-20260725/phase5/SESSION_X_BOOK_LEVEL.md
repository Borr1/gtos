# Session X — measure the book, not the sleeve

**Stage 5, the estate.** Worktree `worktrees/wave5-book-level-20260729`, branch
`phase5/book-level`, from `phase5/walkforward-gate` (**not** `main` — you need W's gate, which is
unmerged). **Blocks B450–B479.**

**Read `../WAVE_5_WORKING_AGREEMENT.md` first** — especially §3 — then Session W's
`SESSION_W_WALKFORWARD_GATE_RESULT.md` and `ADMISSION_STANDARD_OPTIONS.md`.

---

## Why you exist: the owner found the gap, and he is right

Session W built a per-sleeve admission gate and ran the 12 live market-expansion sleeves through it.
**Zero admitted** at either armable standard. Borhen's response was, in substance: *that can't be the
whole picture — where did the candidates go, and did anyone measure the sleeves working together?*

He is right, and the repo says so in its own words. `src/research_infra/validation_integrity/portfolio_contribution.py`:

> The standalone Gauntlet deflates a strategy's Sharpe against the expected MAX of N trials — the
> correct test for "is this the best of a big search". But the north star is Sharpe × **BREADTH**: a
> genuine, regime-clean, ~uncorrelated edge **RAISES the pooled book's Sharpe even when its standalone
> Sharpe is below the max-of-N bar.** That is the Fundamental Law of Active Management
> (IR ≈ IC × √breadth) — many small uncorrelated edges pool into a high book Sharpe.

**That module exists, is written, and W's gate does not reference it** [verified: no import, no call
site in `src/research_infra/walkforward/`]. So "zero admitted" is a statement about **standalone**
strategies. Whether any of them *improves the book* is unasked and unanswered.

`mx_btcusd_d1_donchian_20_breakout` is the concrete case: **+0.2446 R/day, 100 % of folds positive,
318 trades**, rejected only on multiplicity at **q = 0.149** against a 0.10 bar. That is exactly the
profile of a sleeve that can fail standalone and earn a slot as a diversifier.

## What you own

**1. Wire the diversifier certification in, and run it.** `portfolio_contribution.py` states six
conditions: a genuine standalone edge (PSR-vs-zero, permutation-significant, PBO < 0.5, regime
contamination flag false), positive contribution at a **fixed, non-optimized** satellite weight,
block-permutation significance of the *improvement*, out-of-sample robustness, a correlation ceiling,
and no risk regression.

**Do not relax any of them to get a pass.** The whole point is a second honest question, not a lower
bar. If nothing certifies, that is the answer.

**Read the module before trusting this description of it** — it is the orchestrator's summary and
carries the orchestrator's usual error rate.

**2. Build the merged-book evaluation that has never been run.** This is the owner's actual question
and no artifact in the programme answers it:

- The sealed replays (~16.5 MH/window) ran the **broad V4 stack** — a different family from the live
  book. `CLAUDE.md` H7: *"Replay does not measure the live system."*
- W's pilot generated **per-sleeve** streams, 2,086 trades over 26 years, and never merged them.

So: compose the sleeves into a **book** — shared equity, the real sizing path, the conviction/Kelly
interaction, the governor's caps — and measure the portfolio, not the sum of its parts. The pieces
exist: K's generation port, Session J's cost layer, Q's firm-rules MC, W's gate and its D1 archive
run.

**The interaction is the point, and it cuts both ways.** `book_engine.py:452-453` (DF-1) exists
because a sleeve that generates but cannot be sized *still inflates the Kelly-lite conviction count
and over-sizes the real units*. Correlated sleeves firing together concentrate risk that per-sleeve
numbers cannot show. A book of individually-mediocre uncorrelated sleeves can beat a book of two good
correlated ones. **Measure it; do not reason about it.**

**3. Score the four armed sleeves through W's gate and through the diversifier test.** They were
**never run through either** — verified: `W_MX_PILOT.json` contains 12 sleeves, none of them
`metals_core`, `crypto`, `energy_agri` or `sub_xvol_pullback`. They earned their slot from the
broker-truth re-costing of the W7 validation, which is a different bar.

**This is the most decision-relevant thing in your prompt and it may be uncomfortable.** A live funded
account is being armed on those four. If they do not clear standard A, Borhen needs that in front of
him — before or shortly after arming, but *known*. Report it plainly whichever way it falls, and do
not soften it. If the honest answer is "the gate cannot score them because X", say that instead of
producing a number.

**4. Say where the next capture pays.** If a family fails only for want of data — M15 reaches back
only to 2024-01-01, thin for intraday — say which data, for which sleeves, and what it would change.

## Traps

- **The cost artifact is a look-ahead and it is first-order.** Spread measured over **37 days in
  2026**, charged to a 2007–2026 panel where cost runs **33–219 % of gross R**. Spreads compressed,
  so every W number is optimistic by an unmeasured amount. Inherit the stamp; do not quietly drop it.
- **`regime_inflation.py` has a sign defect** — it flags contamination on a *positive* ratio
  threshold, so once the full-history mean goes negative the flag **can never fire**; the detector is
  defeated by making the concealed loss bigger. Same family as F39. W guarded its own call site only;
  **the module is still broken** and `portfolio_contribution.py` condition 1 depends on that flag.
  Fix it or guard it, and say which.
- **Do not score the 7 first-of-day candidate sleeves.** Port live-recall is **19 %** — you would
  measure Session Y's bug, not the sleeve. W declined for this reason and was right.
- **Multiplicity across sessions is real.** W tested 12. If you test more families and report the
  winners, the effective trial count is the union, not your slice. Account for it.
- **Correlation estimated on few overlapping days is noise.** These sleeves trade ~7 days a month.
  State the effective sample behind every correlation you use, and treat a correlation ceiling built
  on 20 overlapping observations as the weak evidence it is.

## What is NOT yours

Sleeve composition, the risk dial, and the admission standard are **Borhen's** — he is choosing
between W's options A/B/C now. Do not touch the VPS. Do not arm anything, mint a token, or flip a
gate. Do not run a broker-capable script (agreement §1). Do not merge to `main`.

## Method

**Commission refuters and default them to "refuted."** Distinct lenses: one that tries to get a
known-bad sleeve certified as a diversifier (W's refuter admitted one that lost **17,840 R** by
hiding losses in an unscored fold — assume yours can be fooled the same way), one on whether your
correlation and Sharpe estimates survive their own sample size, one on whether the merged book
reproduces the engine's real sizing rather than a reimplementation of it, one on multiplicity.

**Call the production resolvers.** `admission.effective_registry`, `book_engine._active_sleeve_names`,
`symbol_map.build_broker_symbol_resolver`, `src/costs/cost_r`. Three separate agents this week —
including the orchestrator — reported wrong numbers by reimplementing resolution the engine already
does.

**A clean negative beats a rescued pass.** If the merged book is worse than the four-sleeve book, that
is a result and it is worth more than a number that flatters the estate.

Use your own judgment on method, scope, and on whether anything above is wrong.
