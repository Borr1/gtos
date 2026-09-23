# Session AB — attack the selection-window problem by measurement

**Wave 6.** Worktree `worktrees/wave6-regime-spine-20260729`, branch `phase6/regime-spine`, from
`main`. **Blocks B650–B699.**

**Read `../WAVE_6_WORKING_AGREEMENT.md` §0 first**, then `../FOURTH_REVIEW.md` §3.1 and §5.2.

---

## The problem you own

**FTMO is trading real money on three sleeves right now** — `crypto`, `energy_agri`,
`sub_xvol_pullback`, armed 2026-07-29 12:55 UTC. Every headline number justifying them is computed
**inside the window that selected them**: `build_survivor_book.py:60` and
`KB7_growth_kelly_sizing.py:130` share the `d.year >= 2025` predicate (Session V §7). Outside it the
same sleeves earn **+0.100 %/month over ten years and −0.220 % before 2020**. The repo's own
`AUDIT_exec_and_untouched.md` says *"NO clean out-of-sample slice exists"* and nothing cites it.

Every previous instinct here was to treat that as a reason to doubt the book. **Fable found the
mechanism instead, and it is repairable:**

> book-day density runs **0.4 % (2015) → 28.7 % (2025)**, so the out-of-window silence is mostly
> the sleeves **not firing**, not the sleeves losing.

A sleeve that does not fire earns nothing, and averaging that into "out-of-window return" mixes
*"the edge failed"* with *"the setup never appeared."* Those are different facts with different
repairs, and nobody has separated them.

## What you own

**1. Attribute the frequency ramp.** Regenerate each sleeve's **qualifying conditions** — not just
its intents — over the full archive, and decompose the ramp into:

- **(a) symbol availability.** `crypto`'s history starts 2024-09; several surfaces did not exist
  earlier. This is benign: **restate the out-of-window economics on the surface that existed.** The
  −0.220 % pre-2020 number currently mixes "sleeve lost" with "sleeve's symbols didn't exist."
- **(b) fixed absolute thresholds** that recent volatility and price levels cross more often. **This
  is the high-value case** — re-express the threshold **scale-free** (ATR-relative, percentile) and
  the sleeve may have been firing all along at the right scale.
- **(c) genuine structural change** — the case where a regime gate is the honest answer.

**2. Normalize, with an honest protocol.** Where (b) holds: **refit pre-2024, validate 2024+.**
Fitting the normalization on the same window that selected the sleeve would reproduce the exact
defect you are repairing. Log every variant to the trial-budget ledger (agreement §3).

**3. `sub_xvol_pullback`'s neighborhood.** It is the strongest earner in the estate — **+1.071 R per
trade, +0.978 R/day OOS** — and it fails the gate on *significance alone*, q 0.264 at **n = 88**.
That is a sample-size problem, not an edge problem. Map the parameter neighborhood: is the edge a
spike (fragile) or a plateau (real)? A plateau is the strongest evidence available short of more
trades.

**4. Name the regime dials** the command center will show (Session AJ consumes them), and build the
feature-store precursors inline — Session AH consumes those.

## What is known about the three live sleeves, and it is not what the gate says

From W's negative-controls run and Session X, verified:

| sleeve | state |
|---|---|
| `crypto` | **NOT_EVALUABLE at 47.9 % cost coverage** — DASHUSD had no tick file. Being exported now |
| `sub_xvol_pullback` | 93.9 % coverage (EU50.cash blocked its universe — also exporting); rejects on significance at n=88 while earning +1.071 R/trade |
| `energy_agri` | **OOS +0.302 R/day, 75 % folds positive, q 0.33** — a positive edge that cannot clear the family bar alone. That is a **breadth** repair (§5.4), not a defect |

**None of these is evidence the book is bad.** Two are data gaps and one is a multiplicity bar. Say
so plainly in your report; the orchestrator has repeatedly reported this class of thing as if it
were a verdict, and Borhen has corrected it.

## Traps

- **Do not edit `config/agent_config.yaml`** — the live activation token binds its digest and one
  byte stops the armed book placing. H1-bound.
- **Do not touch the VPS.** You cannot reach it.
- **`p_pass` inverts the leave-one-out ranking** (V §6). If you rank anything, rank on **passes/yr**,
  not `p_pass` — the latter picks the wrong book.
- **The frequency ramp cuts both ways.** If a scale-free threshold makes a sleeve fire far more in
  2015, its out-of-window economics may get *worse*, not better. That is a real result and you should
  publish it as readily as the other direction.
- Bars are **broker wall clock**, not UTC.

## Method

**Verify your repairs; do not verify sleeves to death.** If a check would end in "therefore reject",
turn it into "therefore repair X". Log every variant to the ledger.

The prize here is specific: **if the ramp is mostly (a) and (b), then the out-of-window record is an
artifact of measurement rather than evidence against the book** — and the three sleeves Borhen has
money on get a real out-of-sample basis for the first time. If it is mostly (c), the regime gate is
the repair and you name the variable. Either outcome is worth the session.

## Not yours

Sleeve composition, the risk dial, admission thresholds — Borhen's. Do not merge to `main`.

Use your own judgment on method, scope, and on whether anything above is wrong.
