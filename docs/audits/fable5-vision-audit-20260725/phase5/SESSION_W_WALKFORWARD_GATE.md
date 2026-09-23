# Session W — build the door

**Stage 5, the estate.** Worktree `worktrees/wave5-walkforward-gate-20260729`, branch
`phase5/walkforward-gate`, from `main`. **Blocks B420–B449.**

**Read `../WAVE_5_WORKING_AGREEMENT.md` first** — especially §3 — then `../WAVE_5_PLAN.md` §0–§1.

---

## What is stranded, and on what

The research built **34 sleeves**. Eleven have been cost-validated. **Twenty-three have never been
validated at any cost model**, and the approved plan says exactly one thing about how they ever could
be — `THIRD_REVIEW.md` §4:

> the 21 candidate/expansion sleeves have no validation and enter `SURVIVOR_BOOK_V1` **only through
> the walk-forward gate**.

**Search `src/` and `scripts/`. There is no walk-forward implementation anywhere.** The door named as
the sole entrance was never built. Every sleeve past the core eleven has been stranded behind a
mechanism that does not exist — while the programme spent four waves refining eleven.

You are building that door. Everything downstream in this wave consumes it.

## The one thing that would make this session worthless

**A gate that cannot fail a sleeve.** If your design admits by construction — because the folds are
chosen after seeing the data, because the cost model is the optimistic one, because the standard is
"beats zero", because leakage lets tomorrow inform today — then it does not validate anything. It
**launders** unvalidated sleeves into a book that carries a funded account.

That is not hypothetical here. The programme's own history:

- The W7 validation was positive over 1,679 days and **contaminated** — the cost model charged
  **zero commission** (F38, `broker_net_cost_engine.py:577-583` sums `spread + slippage + swap`) and
  credited tick erosion with the **wrong sign** (F39).
- The candidate book's cited validation is **proxy-grade and failed its own random-day placebo**,
  p = 0.59 (`THIRD_REVIEW.md` §4, Stage 0.3b), and it has never been jointly validated with the core
  book at the live dial. It is on `true` in the live config today.
- The B7.5 partition registry **marks March 2026 as TRAIN**. March is the only outcome-unread month
  the programme has left. Hand that registry to a builder unmodified and you burn the last clean
  window and leak the future into the past in one move.

So build the gate that would have caught those. **If it would not have, it is the wrong gate.**

## What you own

**1. Design and implement the walk-forward evaluation.** The shape is yours. What it must handle,
because this programme's data has all of it:

- **Leakage controls** — purge and embargo. Sleeves hold positions across bar boundaries; the median
  live hold measured at broker truth is **1.2603 h** but the used-fraction of horizon across twelve
  live sleeves runs **0.4 % to 105 %**, three exceeding their nominal horizon. An embargo sized off a
  nominal horizon will be wrong for at least three sleeves.
- **Fold specification that is fixed before the data is seen**, and recorded. The campaign's standing
  defect is thresholds sealed but **pooling weights not sealed** — so the semantics could be chosen
  after seeing results. Do not rebuild that hole.
- **Day-clustering.** Trades are not iid. R measured `crypto` at 104 fires on 67 dates, lag-1
  ρ 0.441; `metals_core` up to 12 in one day, ρ 0.511. A per-trade bootstrap will overstate
  significance. R's `live_evidence.py` already carries a day-block treatment — read it before
  inventing one.
- **Cost binding.** Session J's layer (`src/costs/`, `cost_r(...)`, `BROKER_TRUE_COSTS_V1.json`) and
  **nothing else**. If `cost_r` cannot answer for a symbol, that is a **coverage fact to publish**,
  not a gap to fill with a plausible number. F38 is what happens otherwise.
- **Multiplicity.** You are about to judge 23 sleeves. Testing 23 hypotheses and reporting the
  winners is how the candidate book got admitted the first time.

**2. Bind it to the production resolvers, not to reimplementations.** This is the failure mode that
bit three separate agents this week, including the orchestrator:

- sleeve sets come from `admission.effective_registry(...)` / `book_engine._active_sleeve_names`
- canonical→broker symbols come from `symbol_map.build_broker_symbol_resolver(config)` — the
  orchestrator probed `mt5.symbol_info` on canonical names, bypassed this, and reported two sleeves
  as untradeable that are at **full surface**
- costs come from `src/costs/`
- generation comes from **K's port**, not a new evaluator

**3. State the gate's own fidelity ceiling, per sleeve class.** This is the honest part and it must be
in the design, not a footnote. K measured the port's live-recall by structure
(`phase3/K1_GATE_RECEIPT.md` §3):

| class | live-recall | sleeves |
|---|---:|---|
| **per-bar** | **96 %** | all 14 `mx_*`, plus `fx_jpy`/`fx_jpy_ny` (100 %) and `idxrev` |
| **first-of-day** | **19 %** | 7 of the 9 candidates |

A gate result for a first-of-day sleeve today measures **the port's defect**, not the sleeve. Your
gate should know that and **refuse to score them**, or score them with the ceiling attached so loudly
it cannot be quoted without it. Session Y is repairing that path; do not pre-empt it, and do not
paper over it.

**4. Propose the admission standard — for Borhen, not for yourself.** What must a sleeve show to earn
a slot? Out-of-sample expectancy net of broker-true cost, at what evidence class, over how many folds,
with what minimum trade count, surviving what multiplicity correction, at what stability across folds?

**This is his decision, the same class as the risk dial.** Your job is to make it a decision he can
actually take: a small number of coherent options with the trade-off stated, and — the part that
matters — **what each option would admit and reject out of the 23**, so he is choosing between
outcomes rather than between adjectives. If you can only run that for the 14 per-bar sleeves, say so
and run it for those.

**5. Prove the gate can fail.** Feed it something you know is bad and watch it reject. Candidates: a
shuffled-label sleeve, a random-entry sleeve at the same trade frequency, the two sleeves measured
**negative before any cost was charged** (`idxrev`, `metals_ob_micro` — `DEAD_BEFORE_COST` in
`SURVIVOR_BOOK_V1.json`), and `fx_jpy`, measured dead live at **−0.453 R gross**, signal-level
p 0.0059. If the gate passes any of those, it is broken and that is your headline.

## What you are NOT deciding

Sleeve composition, the risk dial, and the admission threshold itself are **Borhen's**. Do not merge
to `main`. Do not touch the VPS. Do not run a broker-capable script (agreement §1). A live funded
FTMO account is being armed on four sleeves in parallel with your work — nothing you do reaches it.

## Method

**Commission refuters and default them to "refuted."** Give them distinct lenses: one on leakage, one
on multiplicity and the null, one that tries to *pass a known-dead sleeve through your gate*, one on
whether you reimplemented something the engine already does. Every session in waves 3–4 that ran this
had real errors found — see agreement §7 for the specific cases.

**A clean negative beats a rescued pass.** If your honest conclusion is that the archive cannot
support an honest walk-forward for some sleeve class — M15 only reaches back to 2024-01-01, which is
thin for intraday sleeves — then say so and say what data would fix it. That is a result, and it is
worth more than a gate that produces numbers nobody should trust.

Use your own judgment on design, method, scope, and on whether anything above is wrong.
