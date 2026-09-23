# Session AG — make "no measured spread" a band, not a blocker

**Wave 6.** Worktree `worktrees/wave6-spread-model-20260729`, branch `phase6/spread-model`, from
`main`. **Blocks B700–B749.**

**Read `../WAVE_6_WORKING_AGREEMENT.md` §0 first**, then `../FOURTH_REVIEW.md` §4.6 and §5.5.

---

## The single largest disclosed bias in the programme

Every deep-history number this estate has produced charges a **37-day spread snapshot from 2026 to
26 years of data**, on a family where cost runs **33–219 % of gross R** (Session W §4, defect 4).
Spreads compressed over that period, so **every published historical result is optimistic by an
unmeasured amount.**

It is stamped on W's and X's outputs as a disclosure. Your job is to turn the disclosure into a
**measurement with bands**, so a sleeve that survives at the pessimistic band is known-robust and a
sleeve that flips between bands says so in its repair row instead of passing silently.

And the second half matters as much: **"no measured spread" currently reads as unjudgeable.** That
is what put `crypto` — a sleeve trading real money right now — at 47.9 % cost coverage and
NOT_EVALUABLE. A band is always better than a refusal.

## What you own

**1. `spread_model_v1` from the 263.9 M ticks.** Per symbol-class, spread as a function of
**hour-of-week × volatility state**, fitted on the 37-day window and **extrapolated to history via
each era's bar-based volatility**, with stated uncertainty bands.

**2. Calibrate against the second in-tree window, and take its warning seriously.**
`ULTIMATE_TICK_SPREAD_GOLD.json` shows a **24 % spread rise against a 9–14 % price fall** — which
already **refutes naive price-proportional scaling** (Session N §8.5). If your model reduces to
"spread scales with price", it is wrong and this artifact says so before you ship it.

**3. Banded verdicts.** Gate results carry `{low, mid, high}` band outcomes. Re-stamp W's mx pilot
and AA's estate walk. A sleeve robust at the high band is genuinely robust to the look-ahead.

**4. Priceability for the unmeasured symbols.** `CADJPY`, `DASHUSD`, `EU50.cash`,
`XAUEUR`/`XAGEUR`/`XAUAUD`/`XAGAUD`, `NATGAS.cash` and the rest become **priceable-with-bands
immediately**. Note: the four metals crosses landed today (239 MB, and `metals_core`'s coverage went
**58.7 % → 100 %**), and DASHUSD / EU50.cash / CADJPY / NATGAS / SPN35 / AUS200 are exporting now —
**re-read `BROKER_TRUE_COSTS_V1.json` rather than assuming any symbol is unpriced.**

**5. Entry-timing measurement for the M15 sleeves** (§5.5). This feeds the cost-geometry repair lane
in wave 7 — where a sleeve's edge exists and costs eat it, entry timing is one of the three levers.

## The honest limit, stated by Fable and not to be softened

> **Bands narrow the look-ahead; they do not eliminate it. Only capture does.**

Forward tick capture is a standing owner ceremony. Your bands make everything scoreable *today* and
get tighter when capture lands. Say what your bands cannot do.

## Traps

- **Ticks are broker wall clock, not UTC** — every file carries a `.timebase.json` saying so.
  Convert with `src/utils/broker_clock.py`; it fails closed on an unregistered server. A `_utc`
  field name proves nothing.
- **The tick archive is outside the repo** at `/Users/borr/GTOSActive/vps-ticks-20260726/`
  (263,894,769 rows, sha-verified). Do not copy it into the tree.
- **Do not edit `config/agent_config.yaml`** — the live token binds its digest.
- **Two brokers, different symbol specs.** 18 of 19 shared symbols differ in `trade_contract_size`;
  JP225 also differs in digits/point/tick size. Vendored at
  `research/operations/vps_broker_truth_2026_07_26/BROKER_SYMBOL_SPEC_COMPARISON.json`.
- **A band that is too wide to decide anything is not a success.** If a symbol's uncertainty makes
  every verdict indeterminate, that is a **capture requirement to publish**, not a band to ship.

## Method

Log every fitted variant to the trial-budget ledger (agreement §3). **Verify your model does what
you claim** — hold out part of the 37-day window, check the calibration artifact, state where it
fails. Do not commission an adversary whose job is to reject sleeves; if a check ends in "therefore
reject", turn it into "therefore repair X".

## Not yours

The VPS. Arming, tokens, gates. Broker-capable scripts. Merging to `main`. Admission thresholds are
Borhen's.

Use your own judgment on method, scope, and on whether anything above is wrong.
