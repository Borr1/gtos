# Session BB — the fill truth and the sleeve-supply hunt (wave 13, B1950–B1999)

**Owner authority:** Borhen 2026-07-30, "run all… i do give explicit approval."
**Arms nothing.** Every artifact here is a measurement or a shortlist. No config byte moved,
no R2-bound path was touched, no broker-capable script was run, the VPS was not contacted.

Receipts: `phase13/receipts/BB_FILL_TRUTH_V1.json`, `BB_SUPPLY_RANK_V1.json`,
`BB_ADVERSARIAL_V1.json`, `CANDIDATE_FAMILY_V10.json`; drivers `bb_fill_truth.py`,
`bb_supply_rank.py`, `bb_adversarial.py`, `bb_family_v10.py`; shipped tool
`scripts/book_silence_check.py` with `tests/research_infra/test_bb_fill_truth.py` (17 tests).
A/B: `receipts/SESSION_BB_AB.md` — **0 bad → 0 bad, 0 regressed, +18 net new passing.**

---

## 0. The three findings, in the order they matter

**1. The estate has been quoting DECISIONS as if they were FILLS, and the gap is 32 %.**
The live placement path holds at most one open position per **broker symbol across the whole
book** (`book_owner.py:1823-1850`, symbol-scoped via `_same_broker_symbol_open_exposures`
`:386-399`) and dedups per (sleeve, symbol, decision day) (`:1727-1735`). A blocked signal is
`continue`d — dropped, never deferred. Replayed over the armed four's archive walk, **869
archive decisions become 590 live-equivalent fills.** It is almost entirely a sleeve blocking
*itself* on consecutive H4 bars, not cross-sleeve contention (6 cross-sleeve blocks in total).

| sleeve | archive decisions | live-equivalent fills | suppressed |
|---|---:|---:|---:|
| `crypto` | 181 | 94 | **48.1 %** |
| `energy_agri` | 67 | 42 | 37.3 % |
| `sub_xvol_pullback` | 88 | 35 | **60.2 %** |
| `sub_mid_dn_revert` | 533 | 419 | 21.4 % |
| **book** | **869** | **590** | **32.1 %** |

The mechanism is not new — `walkforward/book_replay.py` (Session X) implements these gates and
X published their rejection counts. **Applying them to the CADENCE is new, and that is where
it bites**, because `mc_firm_rules._derived` (`:622-624`) converts book-days to calendar days
by `md × weekday_sessions / book_days`, and `book_days_per_calendar_month` (`:417`) is the
multiplier on every `%/mo`. Both divisors come from per-sleeve day sums with no placement
guard (`recost_w7_validation.build_matrix_from`; `ai_books_mc.archive_daily`).

Measured **two independent ways, and they agree exactly**: a guard-only replay written here
and `book_replay.replay_book` (production sizer + governor + gates). 579 = 579 on the full
archive, 115 = 115 on the full-surface window (`C2_guard_only_vs_book_replay`).

**2. The armed four's honest cadence, and the calendar it implies.** On the only window where
all four symbol surfaces exist (2024-10-29 … 2026-07-27, set by DASHUSD's H4 start —
availability, never results):

| | archive walk | **live-equivalent** |
|---|---:|---:|
| book-days / calendar month | 5.636 | **4.227** |
| fills / week | 2.509 | **1.387** |
| book-day density | 0.2725 | **0.2044** |

Time to target, bootstrapped on the book's own realised daily series at the **production**
sizer (median effective risk **0.12–0.17 % of equity per trade**, not the 2.0 % dial):

| target | median book-days | **median calendar days** | p10 | p90 | the published convention would say |
|---|---:|---:|---:|---:|---:|
| **+1.97 %** (FTMO's remaining distance to its measured 10 % from 1.0787228) | 9 | **62** | 14 | 164 | 46 |
| +5 % (FTMO phase 2) | 21 | **144** | 55 | 295 | 108 |
| +10 % (FTMO phase 1 from scratch) | 41 | **281** | 151 | 480 | 211 |

**Cadence is stable and expectancy is not.** Across five chronological folds the fill rate runs
1.32 / 1.10 / 1.27 / 1.82 / 1.42 per week — no decay — against the 7.6× economic decay AN
measured on the same era. Quietness is not getting worse; the edge is.

**Seasonal honesty: no seasonal adjustment is supportable, and that is the finding.** The
month-of-year counts range 2 (August) to 19 (November) and look like seasonality; they are not.
Every month-of-year count rests on **one or two** calendar occurrences in a 21-month window, and
against a permutation that reshuffles the same 126 fills across the same available weekday
sessions the spread is unremarkable — **χ² 16.06, p 0.14**. A longer window cannot rescue it,
because it would mix eras in which half the book's symbols did not exist. The one intra-week
description worth having: **Friday is the quietest weekday (15 fills against ~26 for Mon–Thu),
Monday the busiest (32)** — reported as a description, with the same power objection, and it
should size and gate nothing.

**One stated blind spot in the alarm.** `crypto` trades at weekends: **7 of 126 fills (5.6 %)
land on a Saturday or Sunday**, and the silence counter indexes book-days to weekday sessions, so
it cannot see them. The bias is *conservative* — fewer counted book-days means a looser
threshold — and at this size it moves nothing, but an operator watching the alarm across a
weekend should know it is blind there.

**3. Nothing in the estate buys cadence AND edge — but the reason is not the one I first
wrote.** Of the 15 candidates that would add more than 1 fill/week to the armed four, **13
carry negative cost-true OOS expectancy on RECORDED at the mid band**; the two that do not
(`session_leadlag_genuine` +0.0023 R/day, `ny_index_momentum` +0.1774) are the two smallest
suppliers of them. The candidates with real positive expectancy — `vol_compression` +0.905
R/day (p 0.046), `mx_btcusd` +0.389 (p 0.0064) — add **0.46** and **0.36** fills/week.

Priced through `book_replay` + `mc_firm_rules.mc` from FTMO's actual equity, buying cadence
from the negative side is brutal and now has a number:

| book | fills/wk | book-days/mo | max DD | **L4 p_pass** | **P2 p_pass** |
|---|---:|---:|---:|---:|---:|
| armed four (baseline) | 1.27 | 3.96 | 2.10 % | 1.0000 | **1.0000** |
| + `asia_pdl_fade` | **8.87** | 10.82 | 11.25 % | 0.6123 | **0.1835** |
| + `metal_session_reversion` | 3.14 | 7.59 | 10.90 % | 0.2331 | **0.0034** |
| + `orb_crypto_london` | 6.56 | 16.91 | 6.55 % | 0.9966 | 0.9497 |
| + `idxrev` | 12.31 | 17.55 | 4.23 % | 1.0000 | 0.9981 |
| + `mx_btcusd` | 1.61 | 5.14 | 1.70 % | 1.0000 | 1.0000 |
| + `vol_compression` | 1.54 | 4.82 | 3.43 % | 1.0000 | 1.0000 |

**Zero ADMIT at all four bands**, 33 sleeves judged, on the as-walked contract. That is
consistent with AI's own RECORDED arm and is **not** a contradiction of the standing
`mx_btcusd` admission, which lives on `target_5R` — a contract this arm does not apply.

---

## 1. What I got wrong

**I asserted an anti-correlation and my own adversarial pass refused it (A2).** The first
draft of finding 3 said supply and edge are anti-correlated across the estate. Measured:
Spearman(marginal fills/week, OOS R/day) = **−0.214, p 0.267** over 28 candidates — not
significant. And `pooled_oos_mean_r` is R per **day**, so a sleeve firing 20×/week pays ~20×
the per-trade cost per day; removing that mechanical term leaves **+0.015, p 0.938** per
trade. There is no estate-wide law. What stands is the descriptive fact about the top of the
ranking, which is what a decision actually needs — and the refutation is **more** useful than
the claim was: the high-supply sleeves are not worse *per decision*, they are worse *per day*
because they trade more and pay more cost per day. That routes the prescription to the cost
geometry — **Session AY's lane** — where the same sleeves could move without a single new
signal. It does not make any of them armable today. Corrected in
`BB_SUPPLY_RANK_V1.json → READING` so a reader of that file alone is not misled.

**"The published calendar clock inflates 1.33×" is true of a population the published figures
do not use (A5).** The 1.333× is measured on the armed four's **archive walk**. `BOOKS_MC_V1`'s
rows are built from the **W7 recost caches**. The *direction* of the error there is certain — a
per-sleeve day-sum can only over-count book-days — but its magnitude on that population is
**not** measured here, and 1.333× must not be applied to those rows as a correction factor.
Closing it is arithmetic on committed caches (~0.25 session); routed below.

**The alarm's p99 is one observation deep (A3).** 86 book-days, 85 gaps, maximum observed gap
21 sessions. ALERT at 22 means "longer than anything the archive showed on this book", which is
what the tool prints — it is not a well-estimated 99th percentile. The 5-year sensitivity gives
18/26 and the full archive 51/81; the longer windows are *looser* because they contain eras in
which two of the four sleeves could not fire at all, so widening the window would make the
alarm less sensitive rather than more accurate.

**Two smaller ones.** I first named the wrong band tokens (`band_mid` rather than `mid`) and
the gate returned 33 × `NOT_EVALUABLE` on `cost_coverage` — caught because a whole-family
refusal is not a result. And my first occupancy model omitted `already_placed_today`
(`book_owner.py:1727-1735`), which turns out to be **131 of the 279 suppressed decisions** —
nearly half, and the half that survives any exit-model objection because it is a day key.

---

## 2. What was built, not just measured

**`scripts/book_silence_check.py`** — the calibrated quiet alarm, adoptable today.
`CANARY_OPERATOR_PAGE.md` tells the operator "long silences are normal, not a fault", which was
true and unactionable because nobody had measured how long normal is. Now:

- **warn at 15 silent weekday sessions (~3 calendar weeks), alert at 22 (~1 month)** — all
  three estimators (empirical, geometric, moving-block bootstrap) agree, at 1.1 and 0.0
  expected false alarms per year on the observed history;
- it counts **weekday sessions, not calendar days** — a weekend is not evidence, and a
  calendar-day rule fires ~40 % early over a long weekend;
- thresholds are **read from the receipt at run time**, never transcribed; absent the receipt
  it refuses rather than falling back to a literal;
- exit code carries the state (0/1/2) so a scheduler branches without parsing;
- it prints, on every run, that it **cannot** distinguish a dead worker from a quiet market —
  that is the heartbeat's question — and that it stops nothing, sizes nothing, touches no gate.

---

## 3. Discipline

**The family was declared before any gate ran** (`CANDIDATE_FAMILY_V10.json`, committed in
`89c3d9334`, before `bb_supply_rank.py` existed). It adds **zero members** to all four
families and is content-identical to V9 — the value is the declaration and the **cut rule**,
declared in advance and outcome-blind: rank by marginal fills/week through the live guards,
report every member with no top-k, and take the economics column from the published verdict at
the ratified rule. The commission's ">= N/week" is published as a continuous column with N left
to the reader. The priced set is the union of two pre-declared screens (top-N by supply; the
commission's own non-negative-economics screen) so the expensive stage could not quietly become
the cut. Written to merge by union — a sibling wave-13 V10 supersedes it losslessly.

**The fire-rate half opens no outcome column**, which is why it costs the family nothing:
`bb_fill_truth.project()` builds new dicts carrying exactly
`(sleeve, symbol, entry_utc, exit_utc, decision_day)`, and two tests pin it — including one
that mutates the source dict afterwards to prove the projection is not an alias.

**Gate arms:** `RECORDED`, four bands, `B_balanced` α = 0.10, `CANDIDATE_BOOK_V1` (53), band
published with every verdict, seals recorded per arm.

**H1:** nothing under `src/` was edited. Drift check reports 2, both `UNHYDRATED-LFS` — the
documented condition, not a seal break.

**Reproducibility, verified rather than claimed.** All four drivers were re-run end to end on
the finished tree. The only bytes that move are the three wall-clock `seconds` fields in the
gate arms; **every verdict, `spec_sha256`, p-value, q-value and count is byte-identical**, and
the working tree is otherwise clean after a full re-run.

**One environment prerequisite, so a re-runner is not surprised.**
`bb_supply_rank.py --stage gate` needs `research/operations/broker_truth_layer_2026_07_29/`
(`BROKER_TRUE_COSTS_V1_1.json`), which is committed but **excluded by this worktree's default
sparse-checkout**. `git sparse-checkout add research/operations/broker_truth_layer_2026_07_29`
resolves it; no file is created and nothing is fetched from a network. This is the
"sparse-checkout lies" hazard the wave-8 agreement §4 names, met in practice.

---

## 4. Handoff for the orchestrator

1. **Re-derive `book_days` on the W7 cache population** and restate `BOOKS_MC_V1`'s calendar
   columns. Direction is certain, magnitude is not; every `median_calendar_days_to_pass` and
   `%/mo` the owner has seen is affected. Arithmetic on committed caches, ~0.25 session. **This
   is the highest-value item here** — it changes numbers already in front of Borhen.
2. **`ny_index_momentum` is the estate's only cadence-with-non-negative-edge candidate**:
   +3.61 fills/week marginal (2.6× the armed book's rate), +0.1774 R/day OOS on RECORDED,
   failing `significance` alone (p 0.118). It is one of AK's four unregistered generators, so
   it **cannot reach a book at all** until a `SleeveSpec` exists — this session reproduced that
   mechanically (`unit:fail_closed:unknown_sleeve`, 312 candidates, 0 placed). AK's
   `REGISTRY_EDIT_PROPOSAL` is the edit. Not an admission and not a recommendation to arm.
3. **Route the supply table to Session AY.** If the high-supply sleeves' deficit is per-day
   cost rather than per-decision edge (A2's refutation says the per-trade signal is absent),
   the spread/cost geometry is where cadence becomes affordable. AY has the lane; this table is
   its target list.
4. **Adopt the silence thresholds in the command center (Session BC).**
   `scripts/book_silence_check.py` is importable and pure; `silence_state()` is the one call.
   Re-run `bb_fill_truth.py` whenever `--tags` changes — the thresholds are a property of the
   armed *set*, and the receipt stamps which set it measured.
5. **`fx_jpy`'s pull cost 87 % of the book's fills.** Correct on the economics (AV's evidence is
   decisive) and worth recording as a *priced* trade-off rather than a free one: it was the
   single largest marginal supplier in the estate at +9.84 fills/week.
6. **`sub_xvol_pullback` loses 60.2 % of its decisions to the guard** — the highest per-trade
   gross R in the book fires ~5 times a year live. Any figure quoted for it on an archive
   decision count is 2.5× the fills it will produce.
