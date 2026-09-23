# Session V — measure the book that is actually going to be armed

**OD-3, final input.** Worktree `worktrees/wave4-armed-set-mc-20260729`, branch
`phase4/armed-set-mc`, from `phase3/mc-true-target` (**not** from `main` — Q's MC scripts are only
there and Session U is merging them in parallel). **Blocks B380–B409.**

**Read `../WAVE_4_WORKING_AGREEMENT.md` first** — especially §3.

---

## The gap you are closing, and how it was found

Borhen has approved arming a live funded FTMO account on the **four-sleeve survivor book**:
`metals_core, crypto, energy_agri, sub_xvol_pullback`, at **2.0 % nominal** with mandatory
`derisk_mode: smooth`.

The orchestrator handed him `P(pass) 0.99675` and `2.617 %/month` to justify that. Then Session T
found the orchestrator was about to arm a **different, three-sleeve** book — and the honest position
is worse than that: **neither set has an MC at the dial it will actually run.**

Checked directly in `research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json`:

- `accounts/FTMO/variants` contains exactly **two** entries — `ALL_11_BOOK_OF_RECORD` and
  `SURVIVORS_ONLY`. There is no three-sleeve variant anywhere.
- `SURVIVORS_ONLY/fwd_nights_max` → `p_pass 0.99675`, `monthly_pct_calendar 2.617`,
  `median_calendar_days_to_pass 52`, `book_days_per_calendar_month 7.11`.

**Verify all of that yourself before building on it.** And then the question this session exists for:
*what risk dial, what sizing, and what portfolio interaction does that variant assume* — because if it
was not computed at 2.0 % nominal with `smooth`, then the number the owner made a live decision on
does not describe the thing being armed. **Establishing that honestly is worth more than any new
number you could produce.**

## What you own

**1. Make the MC take an explicit sleeve set.** `scripts/mc_firm_rules.py` has `--paths`,
`--verify-paths`, `--out`, `--shares-only` and no way to name a book. Add one. Keep every existing
default byte-identical in behaviour so Q's published run still reproduces — and **prove that by
re-running it and diffing `MC_FIRM_TRUE_V1.json`**, not by reading the diff of your patch.

**2. Measure the sets that matter, at the dial that will actually run.** At minimum:

| set | why |
|---|---|
| **FTMO survivors (4)** — the armed book | the decision |
| **the three** — armed book minus `sub_xvol_pullback` | what the orchestrator nearly armed; also the fallback if `include_clean3: true` is judged too broad |
| `ALL_11_BOOK_OF_RECORD` | the comparator already published |

Across the carry band, because carry is what OD-3 turns on: `nights 0.0`, `1.0`, and `max`. The live
measurement says the broker charged swap on **zero of 41** JPY-sleeve positions and 39 of 59 `idxrev`
— but none of the four armed sleeves has a measured carry, so the band is the honest answer and a
point estimate is not.

**Add whatever else you judge decision-relevant.** You are closer to the model than this prompt is.

**3. Answer the concentration question, because it is the real risk in the owner's choice.** He picked
four over three knowing this, and it deserves a number rather than a caveat: Session N measured
**46.9 % of the survivor book's edge resting on 194 trades**, with in-sample selection concentrated in
`crypto` and `sub_xvol_pullback` (N §8.2). `sub_xvol_pullback` is therefore both **the reason the
four-sleeve book outperforms the three** and **the sleeve most likely to be a selection artifact.**

Quantify it however you think is right — leave-one-out, a haircut on its contribution, a bootstrap
that respects the day-clustering R found (`crypto` 104 fires on 67 dates, lag-1 ρ 0.441), or something
better. The question to answer is: **how much of the four-sleeve advantage survives if
`sub_xvol_pullback` is half as good as it looks?** If the answer is "all of it", say so; if it is "the
four-sleeve book collapses to the three-sleeve book", that is the more valuable finding.

**4. Say what you would arm.** Not a recommendation on the risk dial — that is Borhen's — but a plain
statement of what the measurement supports, including "the difference is inside the noise and the
choice does not matter", if that is what you find.

## Traps specific to this work

- **`sub_xvol_pullback` cannot be armed by a confidence floor.** Its registry confidence is **0.45**.
  Any mechanism you assume in your write-up must be `run_book.py --tags` plus
  `include_clean3: true`; a floor selects the same three sleeves whether clean3 is on or off
  (measured, both ways).
- **Two firms, two rulebooks, and they are not interchangeable.** FTMO daily loss is 5 % of **Initial
  Capital**, reset **00:00 CE(S)T**; redacted_account is 5 % of **Initial Balance + today's realized
  profit**, reset **00:00 server time**. Q's session exists because of exactly this. **Only FTMO is
  being armed** — redacted_account is at $96,229, −3.5 % from high-water, governor already at
  `size_cap_multiplier 0.622928`.
- **FTMO is at $107,872.28 against a $110,000 phase-1 target and a $90,000 static floor.** That is
  **1.97 % to clear** and $17,872 of headroom. A model that starts from $100,000 is answering a
  different question than the one in front of him. If Q's MC starts from the initial balance, say so
  and give the from-here number too.
- **The armed sleeves have zero live fires** across the whole 38-day live window — `metals_core`
  0/990, `crypto` 0/440, `energy_agri` 0/332, all consistent with natural low frequency (empirical
  P(0) 0.369 / 0.284 / 0.638). `sub_xvol_pullback` could not fire at all in that window, because
  `include_clean3: false` dropped it before generation — so its live record is **absent, not zero**,
  and those are different facts. And R found `crypto` emitted 219 packets in that window with
  216 skipped for a **missing instrument config**, not for lack of signal. **Book-days-per-month is
  therefore a modelled quantity with a live record of zero**, and `SURVIVORS_ONLY` at 7.11 book-days
  is the load-bearing assumption in every headline. Attack it.

## Method

**Commission refuters and default them to "refuted."** Q's own value came from finding that the defect
it was sent for was real but that **correcting only it would have reported a five-point deterioration
that does not exist**, because two other rules were wrong in the opposite direction. That is the
standard: fix one thing, check whether the neighbours were compensating for it.

Give the refuters distinct lenses — one on the sizing/dial assumption, one on the day-clustering and
the null, one on whether `SURVIVORS_ONLY` is survivorship in the pejorative sense, one on arithmetic
and reproduction. Publish what they overturn rather than quietly amending.

**A clean negative beats a rescued pass.** If the four-sleeve book does not survive an honest
concentration haircut, saying so before a funded account is armed is the most valuable thing this
session can do.

## What is NOT yours

Do not touch the VPS. Do not arm anything, mint a token, or flip a gate. Do not run a broker-capable
script (agreement §1). Do not merge to `main`. Sleeve composition and the risk dial are Borhen's — he
has chosen; your job is to tell him what he chose, measured.

Use your own judgment on method, on what else to measure, and on whether anything above is wrong.
