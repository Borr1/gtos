# Session AM — the clock re-derivation and the entry frontier's unfinished half

**Wave 9.** Worktree `worktrees/wave9-clock-entry-20260730`, branch `phase9/clock-entry`, from
`main`. **Blocks B1200–B1249.**

**Read `../WAVE_9_WORKING_AGREEMENT.md` in full first**, then AK's result §0 item 1 + §7.1 (the
clock site you are re-deriving), AH's result §3 + §11 (the frontier you are completing), and
AD's result §5 (the tier machinery your re-derivation feeds).

---

## The mission

Two measured defects and two unpriced levers, all owner-independent:

**1. `sub_mid_dn_revert`'s clock re-derivation — the defect in `BUILT` that AK filed and
correctly declined to patch.** `substrate.py:75-84` buckets on raw UTC against server-hour
boundaries; **50.04 % of its 370,808 archive H4 bars bucket into a different session** under the
correct clock. Repair the site (the server-clock index AK built in `walkforward/supply.py` is the
pattern; four tests already pin the defect), then **re-derive everything downstream**: regenerate
the sleeve over the archive, re-walk through the gate (diagnose mode), re-state its carry tier at
measured holds (AD's `ad_carry_tiers.py` machinery — it was UNCONDITIONAL-restated at B753 on the
*wrong-clock* population), and A/B the two populations the way AK did for `structural_retest`
(shared trades, per-clock economics). The sleeve was the "nearest miss in the core book"
(+0.500 R/day OOS, 100 % folds at minimal carry) — on the wrong clock. Find what it is on the
right one. H1: `substrate.py`/`substrate_engine.py` membership check first; they were verified
unbound in AK's pass but verify at your HEAD.

**2. The H4 FX hour-00 subset — AH's declared scope cap, now the cheapest unfinished entry
measurement.** One sixth of an H4 FX trade's fills land at broker 00 (the bar stamped 20:00). Run
AH's four-arm design on that subset (its `ah_entry_shift.py` is the harness; the intersected-
population discipline and the B-control are mandatory). This separates "cost effect" from "D1
mechanism effect" and prices the same lever for every H4 FX sleeve in the estate — including
`fx_jpy`/`fx_jpy_ny`, whose next prescription AD routed to entry-side work.

**3. `atr_mean_reversion`'s own shift.** The cohort's 4 h is measurably wrong for it (pre-entry
drift +0.096 R on cadjpy). Sweep the shift frontier 0 h → 4 h in H4-grid steps on the ATR-MR
members; the mechanism's repair is a shorter delay, and the frontier between 0 and 4 is unpriced.

**4. The min-to-median era-ratio bias (AH §6).** Sized at up to 1.50× on constant-spread FX eras,
direction conservative, not yet repaired. Re-derive the era table on a min-consistent anchor
(AG's `tick_over_bar_factor` machinery measures the same quantity from the other side — reconcile
rather than invent), validate on AG's held-out structure per AH's protocol, and re-run the FX
family verdicts at the repaired term. AH's composition tests (19, behavioural) must stay green —
they were written so a re-measured constant changes one number and not the file.

## Discipline specific to this lane

- Item 1 changes **which trades exist** for a BUILT sleeve — every downstream number must be
  re-derived, never rescaled; publish both-clock A/Bs so the size of the correction is visible.
- Items 2–3 are re-simulations from stored intents + bars where possible; regenerate only where
  the entry instant changes generation (it does — the entry price moves; use AH's arm design).
- Every look to the ledger; new hypotheses join the declared family via the ratchet only if they
  are candidate-book members (the H4-subset re-entries of EXISTING members are new *cells* of
  existing hypotheses — log them as looks, they do not add family members).

## Deliverables

1. `phase9/receipts/SUBMID_RECLOCK_V1.json` — the re-derivation: both-clock A/B, gate verdict,
   restated carry tier, and what changed against B753.
2. `phase9/receipts/ENTRY_FRONTIER_H4_V1.json` — the H4 hour-00 subset + the ATR-MR shift
   frontier, AH's schema so the two concatenate.
3. `phase9/receipts/ERA_ANCHOR_V2_VALIDATION.json` — the min-consistent era term with held-out
   evidence and the verdicts it moves.
4. Repair-queue rows appended (session `AM`); result doc with the §2 scoped receipt; blocks
   B1200–B1249.

## Not yours

The VPS. Arming, tokens, gates, sleeve composition, the dial. Merging to `main`.
`config/agent_config.yaml`.

Use your own judgment on scope and on whether anything above is wrong — and say so in your report
when you do.
