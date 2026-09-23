# Session Q — re-run the survivor-book MC at each firm's true target

**OD-3 option D.** Worktree `worktrees/wave3-mc-true-target-20260729`, branch `phase3/mc-true-target`,
from `main`. **Your block range is B230–B249.**

**Read `../WAVE_3_WORKING_AGREEMENT.md` and `../OD3_DOSSIER_SURVIVOR_BOOK.md` first.**

---

## The defect

`research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/INTEG_portfolio_build.py:298`

```python
TARGET = 0.08; MAXDD = 0.10; DAILY = 0.05; BLOCK = 5; N = 20000; PATHCAP = 2000
```

**`TARGET = 0.08` is redacted_account's phase-1 profit target, applied to both accounts.** FTMO's measured
phase-1 target is **10.0 %** (`FIRM_RULES_V1.json`, coverage `MEASURED`, from FTMO's own captured
page). So **every FTMO `p_pass` figure in `SURVIVOR_BOOK_V1.json` is computed against a target 2
percentage points easier than FTMO actually requires, and is therefore optimistic.**

Found while preparing the OD-3 dossier; recorded as its §5 item 2. It is the one caveat that can be
removed with arithmetic and no new data.

## What to do

1. **Re-run the survivor-book MC at each account's true target** — FTMO 10 %, redacted_account 8 % — across
   every variant already published: `ALL_11_BOOK_OF_RECORD` and `SURVIVORS_ONLY` × `full_2015_2026`
   and `forward_2025+` × nights `0.0 / 1.0 / sleeve_max`, both accounts, at the 2.0 % dial.
2. **Publish the corrected table** and say plainly which dossier figures move and by how much.
3. **Check `MAXDD` and `DAILY` the same way.** Both are 0.10 / 0.05 in code and both firms measure
   5 % daily / 10 % overall — but the *denominators differ* and that is not cosmetic:
   - FTMO: 5 % of **Initial Simulated Capital**, a fixed cash amount, reset **00:00 CE(S)T**
   - redacted_account: 5 % of **Initial Balance + today's realized profit**, reset **00:00 server time**
   If the MC models one denominator for both, say so and quantify it.
4. **Phase 2 as well, if it is cheap.** Both firms require a second phase at 5 %. A book that clears
   phase 1 and stalls in phase 2 has not passed anything.

## Why it matters right now

The owner has approved a canary on the survivor book. **These numbers are what he is deciding on.**
If FTMO's true-target `p_pass` is materially below the published 0.99675 (fwd, worst carry), he needs
that before the account is armed, not after.

## Constraints

- **Do not change `INTEG_portfolio_build.py`'s constants in place.** It is a sealed research module
  and `TARGET` is imported by at least `INTEG_portfolio_build_w2/w5`, `INTEG_W7_final_book`,
  `INTEG_W7_sqrtn_refresh` and `INTEG_w5_clean3_deploy`. Check H1 contract membership
  (`CLAUDE.md` §3) **before** touching anything, and prefer a parameterised call or a local override
  in your own runner over an edit to the shared constant.
- **The 8 % result must stay reproducible.** It is what every published figure rests on; you are
  adding a reading, not replacing one.
- Sparse-checkout hides most of `research/operations/` — `git ls-files -v <path>` shows the `S` bit,
  `git sparse-checkout add /research/operations/<dir>/` hydrates it. Two paths you will need:
  `w7_recost_2026_07_27/` and `final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/`.
- Full-suite A/B by failure set, committed, with captures embedded (`pytest_failset.py receipt`).
  Check `pytest_returncode` and `totals` by hand before trusting any capture.

## Boundary

You produce the corrected measurement. **The dial, the sleeve composition and whether to arm the
account are Borhen's** — he has already accepted the risk and asked for no artificial caps. Your job
is to make sure the number he accepted it against is the right one.

Use your own judgment on method, scope, and how much adversarial verification to spend — including on
whether anything above is wrong.
