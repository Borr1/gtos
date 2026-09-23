# LANE D — THE POSITIVE FINDINGS LEDGER

> ## ⚠ ONE CLAIM QUALIFIED 2026-08-12 — `LANE_G_RECONCILIATION_V1.md` §1, §3
>
> **"Every walker in the estate resolved stops and targets against a BID archive without ever
> crossing the spread" (§0 item 2, and the same sentence at §5 and §7) — QUALIFY. It is true of
> the estate and discovery-swarm walkers; it is NOT true of the walker that produced the wave-21
> funnel caches.** Named here so the next reader does not retract sound numbers.
>
> The exception is `quote_side.resolve_post_submission_m1_lifecycle`, called by
> `candidate_funnel_analysis._lifecycle_row` with **both** `m1_price_basis=BarQuote.BID` **and**
> `spread_by_bar=spreads[start:end]` (`candidate_funnel_analysis.py:146-162`). `BarQuote.BID` is
> the *declaration that the OHLC archive is a bid archive*, not an instruction to ignore the
> spread: the resolver shifts every bar by `entry_quote_offset` on the entry side and
> `exit_quote_offset` on the exit side before any touch test (`quote_side.py:1238-1244`,
> `:1247-1252`, offsets at `:385-412`). **This is the repaired instrument — the one this ledger
> itself records being built** ("a quote-side walker with 27 hand-computed tests").
>
> Verified three independent ways: (1) the code path above; (2) a per-row identity — an intrabar
> stop must realise `gross = −1 − drift − spread_r` for a LONG and `−1 − drift` for a SHORT —
> holding to |residual| < 1e-9 on **98.48 / 98.38 / 98.27 / 98.68 %** of 52,655 barrier rows, the
> ~1.6 % residual being the `SUCCESSOR_M1_OPEN_GAP` branch; (3) the population-level martingale,
> `E[gross] = −0.1331` against `−E[spread_r] = −0.1409`, residual +0.0078 ± 0.0042 on n = 74,249.
> [`lane_g_receipts/frame_check2.py`, `martingale.json`]
>
> **Nothing in the wave-21 funnel work needs re-walking, and this ledger's own conclusion is
> confirmed rather than weakened.** Lane D's "broad-origin family 5/10 → 0/10 gross-positive" is a
> statement about the *pre-repair* estate walk; Lane C's "8/10 gross-positive" is the *post-repair*
> funnel walk with the spread added back afterwards. Two bases, one apparent contradiction, no
> conflict. With the spread left where the repaired walker puts it, the funnel population is
> **0 of 10 gross-positive** — Lane D's number, reached independently. Lane D's own **G3
> mirror-limit control (≈0.179 R/trade magnet ratio on `current_fvg_fill`)** is also what bounds
> Lane C's three LIMIT-family residuals, at 3.3× the size of the number they would have to explain.
>
> **The rest of this ledger is untouched** — the attrition register, the multiplicity finding, the
> ~190 positives and their fates. Only the universality of the instrument sentence is qualified.

**Every positive result this programme has ever produced, and what happened to each one.**

Owner commission, verbatim: *"We had so many positive candidates, and we could actually get
positive months… How so that we made so many sleeves out of the fruits of all of the research,
and we still have negative results?"*

Analysis lane, wave-21 swarm. Read-only over `origin/main` at `9dbf79368`. No live path, no
config, no VPS was touched. Every figure is quoted at the precision its receipt states and
carries an evidence label. Where two receipts disagree, both are shown.

---

## 0. THE ANSWER, IN SEVEN SENTENCES

1. **The programme produced a great deal of positive economics. Almost none of it was ever
   measured on data nobody had read.** Of ~190 distinct positive findings recovered here,
   **eleven** were measured on genuinely virgin windows, and of those eleven, **one** survived
   its own follow-up read.
2. **The single largest destroyer of positive results is not a gate and not attrition — it is
   the measuring instrument.** Every walker in the estate resolved stops and targets against a
   **BID** archive without ever crossing the spread. Repairing that one thing moved the live
   sleeve estate's published gross from **+2,520.7 R to −619.8 R** over 22,354 trades, flipped
   **9 of 29** sleeves' gross sign, and took the broad-V4 family from **5 of 10 families
   gross-positive to 0 of 10**, and **36 of 80 family-months to 2 of 80**.
   [`phase20/FOUNDATIONAL_REPAIRS_RESULT.md` §0, §2.1, §2.4]
3. **The second largest is the multiplicity bill, and it is now dominated by the estate's own
   research activity.** At a declared family of **m ≤ 16** the two best sleeves in the book
   (`sub_xvol_pullback` p 0.006099 — *armed*; `mx_btcusd` p 0.011999) both **ADMIT** at α 0.10.
   At m ≥ 17 neither does. The estate declared 32 and now bills **59** — a bill that grew
   **84 % in 72 hours** after the ratchet was ratified, and *"nothing prices that at the moment
   a look is taken."* [`phase20/SLEEVE_FORENSIC_REPORT.md` §7.1]
4. **Attrition is the third cause and it is a quarter of the output.** Roughly **50** measured
   positives were never refuted and never continued. The largest single one —
   `volume_surge_reversal × index × D1` gated on `VOL_REGIME == hi`, **+0.2248 R/day, raw
   p 0.0127, 5 of 5 out-of-sample folds positive, n = 203** — was routed to the owner *and* to
   the next session as *"the strongest new candidate this wave produced"*, and the string
   `VOL_REGIME == hi` **appears in no document of any later phase.**
5. **What is deployed today earns its living on the window that selected it.** The armed four
   are `crypto`, `energy_agri`, `sub_xvol_pullback`, `sub_mid_dn_revert`. Their headline
   **+2.617 %/month** (5.460 % at the live dial) is measured on `d.year >= 2025` —
   character-for-character the predicate that selected them. Outside it the same book is
   **+0.100 %/month over ten years** and **−0.220 %/month in 2015–2019**. The ratio between the
   in-window and out-of-window monthly rate on the armed three is **14.38×**.
6. **In seventeen months of real-money operation the book has placed one trade that resolved,
   and the owner chose its exit.** FTMO `energy_agri` SHORT UKOIL.cash, **+$493.20 net,
   +0.398 R** — closed on a stop Borhen moved from his own device. redacted_account has **zero fills,
   ever**; it was refused the same signal **231 times in two hours** by a token namespace typo.
7. **The one thing that has survived every out-of-sample read ever run is not an edge — it is a
   discipline.** The funnel's abstain rule beat its own naive expression by **+18.9 R (Feb),
   +6.6 R (Apr+May), +28.9583 R (Jun+Jul)** — three sealed reads across five months, never
   negative, and it is the single **passing** gate in the read that killed the rule. Nothing has
   ever been built on it.

> **The owner's question has a precise answer.** The programme did not fail to produce positive
> results. It produced them and then, three times over, discovered it had been measuring them
> with a ruler bent in its own favour; it billed the survivors against a family of looks that its
> own research activity kept inflating; and it left a quarter of the remainder on the floor
> because each was found by a session commissioned to answer a different question. **The sleeves
> are not the problem and the gates are not the problem. The instrument was, the sample size is,
> and there has never been anywhere to put a positive result that was not the answer to the
> session's own question.**

---

## 1. METHOD, AND THE THREE EVIDENCE CLASSES

Every row carries one of four labels. Conflating them is the failure this lane exists to
correct, so they are defined once and enforced everywhere.

| label | meaning |
|---|---|
| **IS** | in-sample. Measured on data already read, or on data used to choose the thing being measured. Includes every "development", TRAIN, post-hoc overlay, argmax cell, and re-derivation on an opened window. |
| **OOS-w** | out-of-sample *within* a study — held-out folds inside an already-opened population (the ratified `RECORDED` purged/embargoed fold machinery). Real, but the window was open, and in most cases **the cell was selected on the same statistic** (see §1.1). |
| **OOS-v** | **virgin.** Measured on a window never read for any purpose before the measurement, under a prereg frozen before the read. **This is the only class that has ever surprised the programme.** |
| **LIVE** | realised broker P&L on a funded account. |

### 1.1 The caveat that governs every OOS-w number in this document

`SESSION_AL_ADMISSION_CLOSERS_RESULT.md` states it plainly: **"cells are ranked on the same
`pooled_oos_mean_r` that defines them"**, and **"no held-out selection estimate exists."** The
only genuinely held-out *selection* results in the entire corpus are AW's declared-before-outcome
funnel (train→holdout Spearman 0.919, AUC 0.712 — insufficient) and AV's expanding-window
meta-label (AUC 0.5233 — negative). Treat OOS-w as "the folds are honest, the choice of cell is
not."

### 1.2 Cause-of-death taxonomy

| code | meaning |
|---|---|
| **ARTIFACT** | the number was never real — instrument, unit, fill-conditioning or accounting defect manufactured it |
| **EVIDENCE** | a later honest measurement on more or better data contradicted it |
| **GATE** | economics stood; a statistical rule (multiplicity / significance / robustness / fold count) refused it |
| **ACCOUNTING** | a protocol rule refused it — population, cost authority, era, coverage floor, NOT_EVALUABLE, registry |
| **OWNER** | a decision by Borhen |
| **ATTRITION** | nothing killed it; no later document picks it up. **The free-option class.** |
| **DEPLOYED** | live on a funded account |
| **OPEN** | still being worked at HEAD |

---

## 2. THE LEDGER

### 2.A THE FUNNEL LINE — the only line that ever ran a frozen prereg against virgin months

**The five-month sealed record: February PASS / April+May REJECT / June+July REJECT.**

| window | what | actual net R | worst-case | n | class | verdict |
|---|---|---:|---:|---|---|---|
| Oct/Nov 2025 | funnel V1 Jeffreys rule | **+6.272135564222465** | — | 24 sel, 46,252 occ | **IS** (development) | development only |
| 2025-10-30 + 11-06 | the frozen untouched read of the above | **no R published anywhere** | — | — | was to be OOS-v | **no verdict artifact exists** |
| January 2026 | MARKET-top-choice rule | **+10.53639** | — | 52 sel / 51 res | **IS** (`"posthoc January development diagnostic, not validation"`) | development finding |
| **February 2026** | **the same frozen rule V1.1** | **+14.168399** | **+13.144092** | **106 sel / 105 res**, 20 days, 121,302 occ | **OOS-v** | **PASS — all three gates** |
| April 2026 | verbatim, prereg V1.6 | **−7.742114** | −8.815477 | 50 / 49 | OOS-v | — |
| May 2026 | verbatim | **+5.130257** | **+5.130257** | 17 / 17, 10 no-trade days | OOS-v | — |
| **April+May** | pooled | **−2.611858** | **−3.685220** | 67 / 66, 43 days | OOS-v | **REJECT** (gate 2) |
| June 2026 | BAR-3 confirm, prereg V1_3 | **+3.963843** | −0.116157 | 49 / 45 | OOS-v | — |
| July 2026 | verbatim | **−14.566020** | −16.606020 | 68 / 66 | OOS-v | — |
| **June+July** | pooled | — | **−16.722177** | 117 / 111, 42 days | OOS-v | **REJECT** (3 of 4 BAR-3 gates) |
| March 2026 | never funnel-read | — | — | — | — | **virgin** |
| 2025-10-31, 11-05 | held reserves | — | — | — | — | **never read** |

#### The funnel's positive findings

| # | finding | economics | n / window | class | status | cause |
|---|---|---|---|---|---|---|
| **A1** | **FEBRUARY PASS — the programme's one clean virgin PASS** | **+14.168399 R** actual, **+13.144092** worst-case; 20 TARGET / 40 STOP / 45 TIME_STOP; 13 pos / 6 neg / 1 no-trade days; best +5.881489, worst −4.193; predicted +21.24741. Comparators on the same universe: rerank +4.672755 on 127; mixed **−4.742185 on 360** | 106/105, 20 days, 121,302 occ / 85,940 eligible | **OOS-v** — `no_tuning_after_any_february_market_row_or_outcome_is_opened: true` | **SPENT twice**: the rule it validated was rejected on the next two windows, and February itself is now training data for `GEOMETRY_BOUND_OUTCOME_MODEL_V1` | **EVIDENCE** |
| **A1a** | *(the caveat February's own authors attached)* | even in the PASS month the ridge's confident cohort realized **negative**: `pred ≥ 0.10` cohort n=1,352, **realized −0.072** vs predicted +0.146; top-decile realized −0.010 on 74,271 rows | — | — | *"consistent with a thin per-window edge — and also with selection luck; the score's own magnitude cannot tell them apart"* | — |
| **A2** | **`rule ∘ liquidity_sweep_reclaim` — positive in four consecutive scored months** | **jan +4.4002 · feb +13.635073 · apr +0.69757 · may +0.309303**, `historical_all_positive: true` | n = 24 / 24 / 3 / 2 | jan **IS**, feb/apr/may **OOS-v** | **DEAD.** Owner-ratified as *the primary deployable object* 2026-08-11; failed its own confirm the next read: 23 trades, **2 TARGET / 11 STOP / 8 TIME_STOP / 2 CENSORED**, **−10.3989 actual / −12.4389 worst-case**, June −8.4118 / July −4.0272, 3 positive days against 14 | **EVIDENCE** — *"February was the outlier, not the norm"* |
| **A3** | **The abstain discipline beats its own naive expression in EVERY window ever read** | **+18.9 R (Feb) · +6.6 R (Apr+May) · +28.9583 R (Jun+Jul)**, worst-case basis. It is the **one passing gate** in the read that killed the rule | 20 / 43 / 42 days | **OOS-v ×3** | **ALIVE AND UNUSED.** *"The selection layer has real relative skill; the candidate population underneath it is what is negative out-of-window"* | **ATTRITION** |
| **A4** | May 2026 standalone | **+5.130257 R** | 17 trades in 21 days | OOS-v | absorbed into the pooled REJECT | ACCOUNTING |
| **A5** | June 2026 standalone (actual) | **+3.963843 R** actual — *worst-case −0.116157, i.e. flat* | 49 / 45 | OOS-v | absorbed | ACCOUNTING |
| **A6** | `structural_distance_extreme` as June's hero | **+10.0614 R** | June 2026 | OOS-v | July: **−12.6858 R**. Removing the top contributor moves pooled worst-case only −16.7222 → −16.3518: *"the loss is not one family's"* | **EVIDENCE** |
| **A7** | **Post-mortem overlay SD4 — scope to LSR** | **+9.47 R** actual / **+8.40 R** worst-case over 3 months, max daily DD ≤ 5.1 R, ~43 trades | Feb+Apr+May | **IS** — *"the rules were written after reading all three months"* | became Option B → became A2 → dead | EVIDENCE |
| **A8** | **Post-mortem overlay SD5 — trailing brake (k=5, x=3 R)** | **+11.23 R** 3-month vs +11.56 baseline; Apr+May max DD **14.4 → 12.7 R**; 6 days stood down | Feb+Apr+May | **IS** | Option C never chosen and never rejected; never carried into any prereg | **ATTRITION** |
| **A9** | **Geometry variant `s1p5_t2` — best whole-set cell** | **+16.18 R** 3-month vs native +11.56, at a 71 % time-stop rate | 172 selected trades | **IS** (argmax after all three months) | *"the hypothesis the June/July window tests"* — the prereg that would have tested it was overtaken by the Phase-0 kill | **ATTRITION** |
| **A10** | **`s0p75_t2` on `session_open_range_break`** | **+7.18 R** pooled vs native **+1.00 R** — every one of five alternatives beats native, best +6.2 R | n = 124, 3 months | **IS** | *"choose ONE of {s0p75_t2, t1p0} in the prereg"* — never done | **ATTRITION** |
| **A11** | **LSR's native 2.0R/2h contract is already near-optimal** | native **+14.64** vs t1p0 +9.74, t3p0 +13.60, s0p75 +5.58, s1p5 +8.04, h2x +8.87 | n = 29, 3 months | IS | a genuine negative-space result; still true | — |
| **A12** | **MFE early-exit signal** | candidates not reaching 0.25 × target by 60–120 min complete to target **0 / 190 times** across three families (SORB 0/128, LSR 0/24, DC 0/38); mean nets −0.61…−0.73 vs +0.22…+0.71 | 3 months | IS | **priced and it loses**: naive exit-at-60-min books −1.0 to −8.7 R. Proposed as a *selection feature*; never built | **ATTRITION** as a feature |
| **A13** | **The funnel V1 rule's own development result** | **+6.272135564222465 R** pooled modelled, folds 0.0 / 0.0 / −2.3331924470286824 / **+8.605328011251148** | 24 sel / 24 res, 46,252 dev occ | IS | **Its declared untouched decision days (2025-10-30, 2025-11-06) were OPENED, and no result artifact for them exists anywhere on `origin/main`.** The only trace: *"the frozen decision read opened them and the preregistration's `untouched_repair_rule` moved them into development permanently"* | **ATTRITION — two virgin days spent for an unpublished verdict** |
| **A14** | **The inversion thesis** — the funnel autopsy's one constructive finding | claimed **+0.0927 (SDE) · +0.0864 (LSR) · +0.0718 (CALL) · +0.0308 (DC) R/trade**, 5/5 months | 81,968 MARKET-family occurrences, 5 months | IS (post-read) | **DEAD IN HOURS.** Measured **−0.0560 / −0.0534 / −0.0658 / −0.0514**, 0/5 months each; **34 of 35 family-months negative**; best cell in the entire study **+0.0103**; every family t = −3.9…−13.0 | **ARTIFACT** — RR read as 1.5 when the sealed rows carry **2.0 on 81,968/81,968** (removes 75–80 % of the claim), and the arithmetic never charged the inverted contract its own spread |
| **A15** | *(what Phase 0 proved in passing, and it is a real positive)* | inverted-entry adverse fill measures **0.0057 R**, latency drift **≤ 0.0006 R** at 1–5 s, **+0.0009 R at 100 ms** — against the **≥0.15 R** the plan feared: **refuted by ~250×** | 21,449 trigger instants, 88.7 M ticks | measurement | a reusable engineering fact that removes latency as an objection to any momentum-entry design. **Used for nothing** | **ATTRITION** |

**Two things the funnel proves that nothing else in the estate does.** (i) The prereg discipline
*works*: it took the LSR-scoped arming off the table **before money did**, at a measured saving of
**−10.4 R** of live loss. (ii) The programme *can* generate a virgin PASS. It has done so exactly
once, and the machine that produced it is still standing and now running as a forward shadow.

---

### 2.B THE ARMED SLEEVE ESTATE — what is deployed and what it was measured at

**Armed today, both accounts** (verified from the live process command line, host prestate
2026-08-06 and 2026-08-10): `crypto`, `energy_agri`, `sub_xvol_pullback`, `sub_mid_dn_revert`,
plus `--spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback`.

#### B1 — The book headline, in-window and out-of-window

| basis | monthly rate | `p_pass` (L4) | class |
|---|---:|---:|---|
| **the selection window** `d.year >= 2025`, published sizing | **+2.617 %/month** | 0.99918 | **IS — the window that chose the sleeves** |
| the same window at the live 2.0 % dial | **+5.460 %/month** | 0.96884 | IS |
| pre-2025, ten years | **+0.100 %/month** | 0.76760 | OOS-w |
| **2015–2019** | **−0.220 %/month** | **0.00003** | OOS-w |
| all 2015–2026 | +0.463 %/month | 0.98365 | OOS-w |

`build_survivor_book.py:74` and `KB7_growth_kelly_sizing.py:130` carry the **character-identical**
predicate. The route's own audit says so verbatim — *"NO clean out-of-sample slice exists… the
sleeves and dial were chosen to look good on exactly this window"* — and **`git grep -l
AUDIT_exec_and_untouched` returns nothing.** Both terms move: **5.3× on edge per book-day and
7.1× on frequency**; the headline uses **7.11** book-days/month against **1.81** on the full 136
months, with **61 zero months**, and **52 % of all 246 book-days fall in the last 18 of 136
months.**

**The armed-three version of the same gap**, same arithmetic, same live sizing:

| population | book-days | R/day | %/mo | P2 `p_pass` | P2 cal-days |
|---|---:|---:|---:|---:|---:|
| W7 cache, fwd 2025+, worst carry (**IN-WINDOW**) | 117 | 0.34623 | **4.501** | 0.917167 | 60 |
| ARCHIVE, whole span (**OUT-OF-WINDOW**) | 201 | 0.18846 | **0.313** | 0.566017 | 495 |
| **ratio** | | | **14.38×** | | |

**Status: DEPLOYED at the in-window number.** The out-of-window number has never been retracted
and has never been used to resize anything. Session V's own conclusion: *"the honest expected
rate… is somewhere between 0.1 % and 5.5 % per month, and nothing in this repository can narrow
that."*

#### B2 — Per armed sleeve: published vs wave-20's corrected walk

| sleeve | conf | n | gross R/trade published → **corrected** | Δ | net R/day published → corrected → conservative | p(daily mean ≤ 0) |
|---|---:|---:|---|---:|---|---|
| **`crypto`** | 0.85 | 181 | +0.56732 → **+0.43389** | **−23.5 %** | +0.19296 → +0.15592 → +0.10825 | 0.121 → 0.163 → 0.255 |
| **`sub_mid_dn_revert`** | 0.20 | 533 | +0.47842 → **+0.19325** | **−59.6 %** | +0.12928 → +0.07736 → **−0.16579** | 0.087 → 0.188 → **0.958** |
| **`energy_agri`** | 0.80 | 67 | +0.77921 → +0.77851 | −0.1 % | −0.09178 → −0.06542 → −0.09256 | 0.620 → 0.594 → 0.621 |
| **`sub_xvol_pullback`** | 0.45 | 88 | +1.26850 → **+1.26764** | −0.1 % | +0.92706 → **+0.97050** → +0.93018 | 0.0014 → **0.0009** → 0.0014 |
| `mx_btcusd` *(disarmed 08-05)* | 0.025 | 318 | +0.34906 → +0.34906 | 0.0 % | +0.21130 → +0.22324 → +0.21079 | — |

- **`sub_xvol_pullback` is the estate's best armed sleeve and the correction does not touch it**
  — zero exit-reason changes, `s/d` below 0.02, day-block p on net **0.0002**. It is also *"the
  only sleeve for which the 95 % day-block CI excludes zero at EVERY horizon"* and reads
  **8.51×** on the estate's signal-vs-toll screen (estate high on IR 0.4818, capture 56.0 %,
  MFE/|MAE| 2.563).
- **`sub_mid_dn_revert` lost 97.7 % of its expectancy**: pooled OOS **+0.12065 → +0.00277 →
  −0.19583 R/day**; fold positivity **3/5 → 2/5**, and **the three negative folds are the three
  oldest**. It was already a REJECT so no admission moved — but it is armed, and every sizing
  decision on it rested on the published magnitude.
- **`crypto`'s −23.5 % is five trades out of 181** (four `target → stop`, one `maxbars → stop`),
  band-sensitive (−0.032 low, −0.142 high). *"A point estimate on n = 5 events, not a precise one."*
- **`energy_agri` is armed on redacted_account and 0.0 % of its 67 trades is priceable on that
  account.** `sub_xvol_pullback` on FN is **45.45 %** priceable — below the ratified 0.60 floor,
  so the standard returns **NOT_EVALUABLE**. Whole estate: FTMO **100.00 %**, redacted_account
  **63.76 %**.
- **`fx_jpy` (pulled 2026-07-30 on other evidence) flipped too**: +0.0687 → −0.0473 on n = 3,984.
  *"This correction says it was never positive."*

**One disagreement, flagged rather than averaged.** On `energy_agri`, M3's gate-pricer gives
**−0.06542 R/day** and P4's 39-day day-block bootstrap gives **+1.207859 R/day (p 0.0526)**.
Different populations (M3 drops 14 blackout trades carrying +38.49 R gross and collapses to days;
P4 bootstraps all 67). **Do not average them.**

#### B3 — The out-of-window sleeve-level positives

| # | finding | economics | n / window | class | status | cause |
|---|---|---|---|---|---|---|
| **B3a** | **`crypto`'s first — and only — positive out-of-window number** | **+0.0869 R/day OOS**, 60 % of folds positive, raw **p 0.3001** | n = 182, 2017-02 … 2026-07 | **OOS-w** | never used to justify or size anything | **ATTRITION** |
| **B3b** | **`energy_agri`'s mechanism class** (`energy_fvg_retest` × energy × H4) | **+0.4571 R/day** — the strongest pooled mean in AF's 30-family grid; dispersion ratio **0.117**, **3/3 members positive**, raw p **0.1740**. AP's peer-transfer repair takes it to **+0.5641 R/day (+23.4 %)** and clears `robustness` (retention 0.479 → 0.673) | 3 symbols, whole archive | OOS-w | **1 of only 2 families of 30** to pass the two-clause coherence test. Blocked on a `NATGAS.cash` **commission** + CORN/COTTON bars — *a data capture*. AP signed the transfer and it moved p_raw 0.17398 → 0.17548: *"nine trades cannot move a p-value"* | **ATTRITION** (blocked on a capture nobody made) |
| **B3c** | **`volume_surge_reversal` × index × D1** | dispersion ratio **0.736**, **6/6 members positive**, raw p **0.1204** — the **best p-value in AF's entire grid** | 6 members | OOS-w | the other coherent family | **ATTRITION** |
| **B3d** | **The armed-book screen — the estate's only clean discriminator** | the four sleeves trading real money read **3.58× – 8.51×** signal-vs-toll. Everything pulled, disarmed or never armed reads **−0.32× to 2.49×**. The broad-V4 family reads **0.063×**. *"A clean gap with nothing straddling it, reproduced from scratch on evidence unrelated to any of those eleven decisions"* | 51 generators | unclear (whole-population walk) | standing | — |
| **B3e** | **AW's spread-geometry floor — all four armed sleeves improve** | `asia_pdl_fade` **+0.9977**, `sub_mid_dn_revert` **+0.4260** (p 0.163 → **0.023**), `sub_xvol_pullback` +0.2644 (raw p **0.0020**), `energy_agri` +0.2118. Controls: inverse-cheapest **−0.0601 to −2.7275**; random max +0.1203/+0.2083 | 21,769 priced archive trades | OOS-w at the ratified rule | **ARMED 2026-07-31 on both accounts** for two sleeves — the estate's one frontier repair that reached live money and stayed | **DEPLOYED**, and *"0 ADMIT"* — it is a fidelity repair, not an admission |

#### B4 — What the live book has actually earned

**[MEASURED: absence]** — *"ZERO broker records at or after 2026-07-29 exist on this machine.
The lane brief premise (post-arming fills) is untestable here."*

| date | FTMO | redacted_account |
|---|---:|---:|
| 2026-07-25 (**pre-arming**) | 107,879.56 | 96,229.28 |
| 2026-07-30 (ceremony) | 107,872.28 | 96,229.28 |
| 2026-08-03 | 107,872.28 | 96,229.28 |
| **2026-08-05** | **108,365.48** | 96,229.28 |
| 2026-08-10 | 108,342.47 | 96,229.28 |

**The one book-placed trade that resolved.** FTMO `energy_agri`, SHORT 1.91 lots UKOIL.cash
@ 83.233, decision bar 2026-08-04T09:00Z, filled 13:00:28Z, `reason=EXPERT`, SL 89.984 / TP
56.230 server-side at entry, sized 1.20 % risk = $1,289.44. Closed 2026-08-05T04:56:43Z at 80.547
on `DEAL_REASON_SL`, comment `[sl 80.511]`. **+513.03 gross, −19.83 swap, 0.00 commission →
+493.20 net. Realised 0.398 R; peak floating 0.504 R.**

> **It was not the book's exit.** Borhen moved the stop 89.984 → 80.511 from his own device.
> Proved two independent ways: **zero `modify` lines across ten days of FTMO terminal journals**,
> and a distinct external IP `0.0.0.0` authorising during the position's life against the
> VPS's own `0.0.0.0`. **And the learning lane cannot see the difference** — every field
> says `broker_closed` and `deal.reason == SL` is identically true either way. `edge_state.json`
> now credits `energy_agri` with `n=1, wins=1, sum_profit=+493.2` for a price the owner chose.

**redacted_account: zero fills, ever.** It prepared the *same* signal that day and retried once a minute
from 13:00:41Z to 14:59:08Z — **231 refusals**, all
`activation_token_namespace_mismatch (redacted_account_live_bee34003 != redacted_account)`, surfacing to the
operator as the misleading `Order failed: timeout_no_fill`. Fail-closed; opportunity cost only;
repaired 2026-08-06.

**And the earlier FTMO gains were not the book.** Session LQ established that FTMO's July P&L —
including **+13,338 on 2026-07-03** — is **magic-0 manual trades**. From 2026-07-02 the runtime
was in shadow mode: **1,829 of 1,829 redacted_account cycles report `shadow_apply_to_execution_off`
with 446 intents and 0 placed.**

**This is not a fault.** *"Expected fills since each account's current set took effect: 0.105
(FTMO) and 0.174 (redacted_account). Zero fills is what a healthy book looks like right now, 90 % and
84 % of the time."* `sub_xvol_pullback`'s 60-fill evidence floor is **193.5 months** away.

#### B5 — The book's probability of passing, and the one convention nobody has adjudicated

Armed four on the **archive** population, 581 book-days, 200,000 MC paths, each firm's measured
rules, 2 % nominal:

| arm | R/book-day | p(mean ≤ 0) | **FTMO 2-phase** | **FN 2-phase** |
|---|---:|---:|---:|---:|
| published walk, spread charged | +0.07654 | 0.0244 | **0.5468** | **0.5661** |
| **corrected walk, spread removed** *(arithmetically right)* | +0.06477 | 0.0416 | **0.5157** | **0.5366** |
| corrected walk, spread charged *(conservative)* | +0.02029 | **0.3011** | **0.3370** | **0.3626** |
| corrected at high band, charged | +0.00158 | 0.4837 | 0.2786 | 0.3059 |

**One unadjudicated cost convention is worth 17.87 points of two-phase `p_pass` on FTMO — more
than five times the size of the repair it accounts for.** Both arms are published. Nobody has
picked.

**And [MEASURED: absence] the numbers actually quoted to the owner were never re-walked.** Every
`p_pass` he has seen — 0.9172 / 0.9331, 4.501 %/mo, 6.120 % at five sleeves — comes from the
**W7 recost caches**, which wave 20 did not touch. They were built by the same class of bar walk
on the same BID archive. *"The inference that the defect reaches them is strong — but it is an
inference."* **One session, no new data, and it is the highest-value forward item the wave left
behind.**

---

### 2.C THE STANDING ADMISSION — `mx_btcusd @ target_5R`

The estate's **only** candidate ever to clear the sealed admission standard. Its entire life:

| stage | economics | outcome |
|---|---|---|
| **AA / AD discovery** | `as_walked` +0.2447 R/day; **`target_5R` +0.5535 (+0.3088)**, monotone ridge 1R→5R; 5/5 OOS folds; p_raw 0.0101, **q 0.348 against a family of 69** | REJECT on multiplicity |
| **AI / AL family declaration** | same economics; the historical 69-look family **double-counted** (W's and X's looks are subsets of AA's 32) → q **0.4140 → 0.1740** | ADMIT only at α 0.20, which `options.py:110` disqualifies for arming |
| **AL — the first sealed-α ADMIT** | **pooled OOS +0.98169 R/day**, p_raw **0.0011**, q **0.0385** at BH α 0.10 across family 35; ADMITs under Bonferroni too; folds **[1.134, 1.512, 1.866, 0.284, 0.112]** all positive; drop-best 0.7747; coverage 1.00 | **ADMIT** |
| **AQ contract repair** | the `mx_*` D1 cohort's `time_stop_bars` was **96 — the M15-per-D1 conversion ratio, not a horizon**. 82.3 % of this sleeve's trades are held past 24 h. Repaired to 7,680. **Neither change alone admits**: 2R@repaired p 0.00639936 REJECT; 5R@old-stop p 0.0563944 REJECT; **both p 0.00109989 ADMIT** | admission is *contingent on a repair that had not landed* |
| **AN population rule** | 240 gated arms, exactly **9 ADMIT, all `mx_btcusd` on RECORDED** — and it **decays chronologically 7.6×**: folds 1–3 **+1.5041 R/day** → folds 4–5 **+0.1981** = **13.2 %**. `stability` counts the SIGN of a fold mean, so it reads 5/5 — **the decay is invisible to the standard by construction** | ratified; sized on the recent folds |
| **live** | **ARMED on FTMO 2026-07-31 ~01:26 UTC** at confidence **0.025** (0.32 % of book weight — *"economically inert by design; the n is the point"*). **DISARMED 2026-08-05 ~14:33 UTC** on owner instruction, host `2fa77722d`; the launcher's `tfs` went `[16388, 16408] → [16388]`, proving the resolver dropped it | **six days** |
| **wave-20 walker** | moves it by **nothing**: pooled OOS −0.16 %, `p_raw` unchanged, **1 exit reason changes in 232 trades**, folds stay 5/5 — because BTCUSD's spread-over-risk is **0.0124 R against the estate's 0.1917** | **ADMIT survives** |
| **A1b's corrected null (2026-08-03)** | **ADMIT → REJECT** at all three admitting bands: flat 0.0009999 → **0.00268** (q 0.12864), low → 0.002765, mid → 0.00281. Composed with the walker: 0.002810 → 0.002843 (+1.2 %) — *"the flip is A1b's in full"* | **REJECT** |

> **The precision that must travel with the kill.** At the **measured** within-fold dependence
> **ρ̂ = 0.384 ± 0.069** (179 pairs, a tight estimate) the corrected p is **0.00135166 and it
> still ADMITS** (q ≈ 0.065). **The REJECT comes entirely from the +1SE variant** (ρ 0.452–0.453);
> the flip boundary is ρ ≈ 0.42–0.45. *"The admission carries less than one standard error of
> dependence-model margin at its 48-family bar."* A1b flags explicitly that whether a **<1 SE
> margin should disarm** is **an owner decision, flagged not taken.**

**Cause: ACCOUNTING** (a corrected null, on a <1 SE margin), preceded by **OWNER** (the disarm).
The sleeve forensic states the whole arc in one line: *"exactly one has ever cleared the standard
GTOS now judges by — reversed six days later."*

---

### 2.D THE INVERTED BREAKER — the largest number the estate ever produced, and its five verdicts

`cq_current_breaker_inverted_target_5d_stop_0p25d_v1`. **Five verdicts on identical economics.**

| stage | verdict | basis |
|---|---|---|
| **CQ (wave 18)** | **NOT_EVALUABLE** | TRAIN n=2,257 **+11.87710 net R/trade**, HOLDOUT n=2,006 **+11.92812**, FULL n=4,263 **+11.90111**. 3,082 trades survive the population rule but January supplies **one** evaluable chronological fold and the gate requires three |
| **CS (wave 19)** | **REJECT** | three capture-local OOS folds, **all positive**: Jan **+11.252342** (n=1,664), Apr **+7.453554** (n=768), May **+3.852045** (n=487). Equal-by-fold pooled OOS **+7.519313 R**; scored-trade mean **+10.926325 R** over **2,919 OOS trades**; drop-best **+5.652799** (75.18 % retention); full-lifetime **+12.591781 R/trade** over **6,536** priced RECORDED trades. **"The only failed predicate is significance"**: raw **p = 0.0025997400259974**, BH **q = 0.1533846615338466** vs α 0.10 across a **59-member** declared family |
| **wave 20 (HDF / HI)** | **ADMIT** | independently rebuilt capture-start null: raw **p 0.0009765625**, BH **q 0.0576171875**, status `RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED` |
| **FA / A1b clean-room (2026-08-03)** | **ADMIT** | the published null is **not rotation-invariant** — *"across the 31 circular anchorings p spans 10× and the verdict flips at 14 of 31 rotations"*; support capped at 2¹¹. Corrected: **p = 0.00130**, q@59 **0.0769** ⇒ ADMIT at α 0.10. Fragility disclosed: flips if ρ ≥ ~0.6, 1.2 SE above measurement |
| **wave 21 integration** | **REJECT** | re-gated at the artifact-bound slippage authority: 6 of 16 symbols (AUDJPY, CHFJPY, EURJPY, UKOIL.cash, USOIL.cash, XAGUSD) have **no reconciled price-domain slippage sample** and refuse fail-closed. Evaluable universe **10/16 symbols, 63.556 % of trades**. **q 0.0576 → 0.3169.** Fold means **[12.2497, 7.6666, 1.7106], pooled 7.20899** — *"still large; the multiplicity bill is what fails"* |

**And two independent findings that do not fit any of the five verdicts:**

- **The discovery lane says it is 103.4 % artifact.** Matched trade-by-trade to source candidates:
  **81.33 % of its trades come from candidates whose stop was already broken before the order
  could be sent.** On those it "wins" 83.88 % and books **+15.127 R/trade**; on the **596
  genuinely takeable trades it wins 1.01 % and books −2.644 R/trade.** *"The published edge is
  not merely inflated — it is entirely the artifact, and the real trades lose money."*
  **Recommended action: "that candidate should be struck from the factory family, not promoted."**
- **FA proved the billed edge is INEXPRESSIBLE in the engine.** All 12,668 breaker candidates
  transformed, zero errors, geometry verified 483/483 — **and it bought ZERO trades.** The 0.25D
  stop shrinks the R unit so median `cost_r` goes **0.191 → 0.701 (3.7×)** and **100 % refuse at
  the pre-trade cost gate at ANY declared ceiling.** *"The engine's cost gate is denominated in R
  units and structurally presumes ~unit-R stops; no high-RR candidate can ever pass it, whatever
  its realizable economics."*

**Assessment.** The economics have never been refuted on evidence. The verdict has oscillated
five times on *accounting* — fold count, family size, null construction, slippage coverage. And
two separate structural findings (the past-stop artifact and the R-denominated cost gate) say the
number would not survive contact with the live system even if a verdict admitted it. **Primary
cause: ARTIFACT, with ACCOUNTING as the proximate one at every stage.** The wave-20 generator
repair (`broad_origin_emission_contract.py:214`, default ON) now refuses past-stop emissions by
construction, which removes the artifact **and, if the discovery lane is right, the number with
it.** *That composition has never been measured, and it is the cheapest way to settle the whole
dispute.*

---

### 2.E CP'S NY-METALS-LONG — the NOT_EVALUABLE candidate

`route_session_ny__asset_metals__direction_LONG` (XAGUSD + XAUUSD, NY session, LONG), candidate
`1493e333da89dbd6`. The one factory survivor of **1,092 looks**.

- **Economics**: TRAIN mean R interval **+0.08929324 to +0.12747924**; precision interval
  **0.63448276 to 0.72068966**; lower-edge positive-day share **0.61538462**; **290 rows /
  13 days**. All five checks true, `train_survivor: true`.
- **Class: IS.** Only the first **13 January TRAIN days** were evaluated;
  `holdout_outcome: NOT_EVALUATED_BY_FACTORY`. *"This is a TRAIN survivor, not a sealed-gate
  pass."* Billed once → V26 (57 → 58 declared).
- **Gate: `FROZEN_GATE_NOT_EVALUABLE_SOURCE_AND_FIDELITY_CAPTURE_REQUIRED`.** *"all 249 raw rows
  lack `counterfactual_order_fill_status`… zero join coverage cannot be interpreted as zero
  fills."*
- **Session CR closed one of the four blockers and could not close the others**: generator
  fidelity measured at **recall 1.000** (249/249 identities reproduced, zero reference-only)
  against a frozen 0.50 floor. *"Every one of the 121 filled rows is missing all seven
  gate-bearing groups."* CR-CAPTURE-1..4 filed; **never run.**
- **And then it was refuted independently.** FA measured the same class inside its own February
  funnel: **January +12.7 / +22.0 R by variant → February −75.6 / −80.8 R**, 47.8 % positive at a
  mean cost of only 0.105. *"the signal failed out-of-window, not the cost; corroborates wave-18's
  REJECT independently."*

**Cause: ACCOUNTING** (never granted a population it could be judged on), then **EVIDENCE**. It is
the estate's cleanest case of the distinction this lane insists on: it went from *unfinished* to
*refuted* without ever passing through *admitted*.

---

### 2.F THE EXIT / ENTRY / GEOMETRY FRONTIER — the attrition field

Every row is a measured improvement to a contract the books already run or could run, priced,
published, and then neither armed nor refuted.

| # | finding | economics | class | status | cause |
|---|---|---|---|---|---|
| **F1** | **AD's exit frontier — the largest block of unclaimed economics in the estate** | **1,631 gated exit cells over 25 sleeves. All 25 improve. Median +0.249 R/day, range +0.015 to +0.771.** On **23 of 25** the best exit geometry is worth MORE than eliminating carry entirely | OOS-w | **NONE ADMITTED. The failing gate at all 25 best cells is `significance`** | **GATE** |
| **F1a** | *(and the correction that must travel with F1)* | p2 built the side control AD never had: **64 % of the median exit-frontier improvement is available on a coin flip.** Median best-cell Δ **+0.1136 R/day of which only +0.0409 is earned**; **not one headline cell's earned component excludes zero**; real improvers 26/29 → **18/29** | OOS-w | binding standard now: *"the exit-frontier method has no side control, and should have one before any further cell selection reaches a book"* | **ARTIFACT** (partial) |
| **F2** | **`asia_pdl_fade @ target_5R` — the ONE exit cell that survives the side control** | **earned +0.0526 R/trade, CI95 [+0.0028, +0.1043], p 0.019, n = 2,827**, with a **negative** placebo (−0.0278). *"The single row in the entire estate whose earned interval excludes zero"* | OOS-w | **REFUTED on the corrected walker, in a JSON-only receipt with no session write-up.** p3's stop-floor sweep REJECTS at every k and every band, pooled OOS **−1.2646 to −0.1370 R/day**, best p_raw ≥ 0.9938, `max_declared_family_that_admits` = **0**. Only the *old uncorrected walk with spread removed* admits. Corroborating: r1 moves the sleeve **+0.17195 → −0.32888 R/trade**, 12.98 % of exits changed, `s/d` 0.2435 | **ARTIFACT** — and **no document states the kill** |
| **F3** | `asian_fade` | as-walked −0.780 → `trail_a2_g0.5_prod` **−0.009**: **Δ +0.771 R/day** | OOS-w | never carried | ATTRITION |
| **F4** | `metal_session_reversion` | −0.796 → composite −0.170: **Δ +0.626** | OOS-w | never carried | ATTRITION |
| **F5** | `kz_london_crypto_low` | −0.592 → `stop_3x_tgtscale` −0.011: **Δ +0.581** | OOS-w | never carried | ATTRITION |
| **F6** | `metals_ob_micro` | −0.411 → `flat_before_triple_swap` **+0.097**: **Δ +0.507** — crosses zero | OOS-w | never carried | ATTRITION |
| **F7** | **`mx_us100` / `mx_us500` ATR-MR — both cross negative → positive pooled OOS** | −0.348 → **+0.111** (Δ +0.459) and −0.252 → **+0.202** (Δ +0.454); capture −0.181 → +0.271 and −0.102 → +0.295 | OOS-w | *"the clearest EXIT_REPAIR confirmations in the estate."* AU's 352-arm ladder: magnitudes confirmed, **every cell REJECTS**, wired default-off | **GATE** → ATTRITION |
| **F8** | **`energy_agri` (ARMED) best cell** | +0.417 → `flat_before_triple_swap` **+0.603**: Δ +0.186, `significance` its **only** failing gate | OOS-w, n = 67, 3 folds, p_raw 0.111 | *"the number that makes the question askable, and the question is Borhen's"* — never asked | **ATTRITION** |
| **F9** | **`crypto` (ARMED) best cell — became ceremony CM** | +0.117 → `stop_1.5x_tgtscale` **+0.226** (Δ +0.110). At the ceremony: **mid pooled +0.29843 → +0.55109 = +0.25267**, latest-fold **+0.03552**, **4/5 paired folds improve at every band**, n = 92 FTMO RECORDED | **IS (VAL, disclosed)** | **ARMED on FTMO 2026-08-06 → ROLLED BACK 2026-08-10 on the owner's word** (host `4d28676f8`). On the corrected-quote walker the same population gives **+0.005 R/day at mid** (paired |t| ≈ 0.03), **−0.129 low**, +0.016 high, **2/5 folds**, latest fold worse at every band. *"Nothing in this receipt argues the rollback left money on the table"* | **OWNER**, vindicated by **ARTIFACT** |
| **F9a** | *(the live residue of F9, and it is a real unclaimed lever)* | on the same corrected walker, **both CM and the shipped 4R are dominated at every band** by `target_4.0R\|maxbars_160` and `target_5.0R\|maxbars_160`: **+0.08 to +0.27 R/day over CM, +0.08 to +0.14 over shipped.** *"The lever this population points at is the horizon (80→160 bars), not the stop width"* | IS argmax | never raised as an owner item; carry unpriced | **ATTRITION** |
| **F10** | `vol_compression` | +0.269 → `time_stop_20` **+0.445**: Δ +0.175; AU's ladder peaks **+0.9849 R/day at h=20**; BB gives +0.905 (p 0.046, +0.46 fills/wk marginal) | OOS-w | wired default-off; never armed | GATE |
| **F11** | **`sub_mid_dn_revert`'s exit frontier on the re-clocked population** | **−0.106 R/day with `expectancy` FAILING → +0.092 / +0.059 / +0.008 with it PASSING**; best cell `time_stop_20` → `time_stop_40`; the published frontier was wrong in **sign and in winner** | OOS-w | the sleeve is **ARMED**; the cell has never been wired. CM re-read it at Δ +0.01188 (FTMO) / +0.08139 (FN) and it fails paired-fold stability | **ATTRITION** on armed money |
| **F12** | **`fx_jpy_ny` pre-rollover flat — the free repair** | swap → **structural zero** at a *positive* **+0.0080 R/day**, and it **beats the zero-carry ceiling** because the earlier exit is worth more than the carry it avoids. Converts the sleeve to structurally carry-free | OOS-w | sleeve not armed; repair never carried | **ATTRITION** |
| **F13** | **AK's `sub_xvol_pullback @ target_4R`** (the one ARMED sleeve) | published **+1.157 R/day** — corrected **twice**: that is the *level*, not the delta (`as_walked` 1.0264 → **Δ +0.130**, an **8.9×** overstatement), and AK measured it at ALL_ERAS on a flat 37-day snapshot at the 69-look family. **Re-gated at the ratified rule the delta is +0.3435 R/day, 2.6× larger** and identical across all four bands | OOS-w | **REJECTS at all four bands**, p 0.0080 vs a 0.002083 rank-1 bar (**3.8× short**). And its **train window is negative (−0.190 / −0.278 R) while its test window is +1.02 / +1.37**. Wired default-off. Standing instruction: **"do not propose it"** | **GATE**, with a sign-inversion warning |
| **F14** | **`asia_pdl_fade` stop cell** | −0.0686 → **+0.0846 R/day** (Δ +0.1533), **5/5 OOS folds positive**, retention 0.554, raw p 0.0659 | OOS-w at the flat snapshot | **REFUTED at the ratified cost band**: **+0.08463 → −0.27414 R/day, p 1.0** — a sign flip. AR's 120-cell re-run: **0 of 120 positive**, best −0.16448 at p 0.9935 | **ACCOUNTING** (cost band) |
| **F15** | **The entry-hour lever** | AH: 100 % of FX D1 fills land at broker hour 00, the **13–38×** hour; the shift is worth **+0.063…+0.141 R/trade net**, **38 of 42 members improve**, `mx_cadjpy` crosses zero; cost saving **+0.1567 R/trade**. AM: **one hour buys 94.40 %** of what four hours buy, and the **net frontier peaks at 1–2 h and is negative at both 0 h and AH's 4 h**. AQ confirmed on a third mechanism: **+0.111 R/trade** vs hour 00 | OOS-w / re-simulation | **RATIFIED as a convention**, and **0 of 72 gated arms admit** (best p 0.380); AM's own grid: 726 declared looks, best raw p 0.0324. *"a cost repair, not an edge"* | **GATE** |
| **F15a** | **CE: the lever's real home is the UNARMED FX D1 cohort** | rollover premium **×7.8–×10.6** on those members; AH's +0.063…+0.141 measured end-to-end **on exactly these members**, 38 of 42 improving. Per-symbol premium: CHFJPY **×19.9**, USDJPY ×16.0, GBPJPY ×12.4, AUDJPY ×11.3, EURJPY ×8.0 | IS | *"the natural next incubants and the mechanism is now ready for them"* — CH measured only `sub_mid_dn_revert`'s JPY crosses (7 rows, DO-NOT-ARM). **The cohort was never incubated** | **ATTRITION** |
| **F16** | **AQ's `time_stop_bars` unit repair** | the `mx_*` D1 cohort's live stop was **96 = the M15-per-D1 ratio** against an 80-bar intent — one bar against eighty. Repaired to 7,680. **Signed both ways**: +0.2722 R/day on `mx_btcusd`, **−0.5913 on `mx_us100`**; **five of ten sleeves were BETTER under the accidental one-bar stop** | OOS-w | repair landed, nothing armed moved. **The five short-horizon sleeves were routed as a deliberate exit decision — never taken.** AU declared six horizons; **every one of 352 arms REJECTS** | **ATTRITION** (the decision half) |
| **F17** | **AR/AO's `vr` volatility tilt** | headline **+1.119 pp book return** — and AR's own blind control proved **85 % was equity-path artifact** (a constant of the same magnitude carrying zero `vr` information delivers +0.949 pp). **What survived**: risk-weighted efficiency **×1.0996** vs blind constants **×1.0005 / ×1.0008** — a **125× separation**; and independently AO's tertile net R/trade **0.512 → 1.111 → 2.124**, permutation **p 0.00025** | OOS-w / re-simulation | wired (`run_book.py --vol-level-tilt`), **default OFF, AR recommends NOT arming** (book payoff wins one band of four) | **ARTIFACT** (headline); the **ordering is ATTRITION** |
| **F18** | **`stop_only_horizon` beats `target_2.0R`** | **+0.039161 R/emission** fill-anchored, day-block CI95 **[+0.01154, +0.06977]**, **p 0.00235**, over **1,127,805 emissions**; under level anchoring the delta gets *bigger* and month count improves **7/8 → 8/8** | OOS-w | **survives the quote-side repair as a paired difference** — the level moves −0.102379, the paired delta only −0.003990, ratio **25.7×**. *"The wave-19 reasoning that killed it was a category error."* No follow-up, no gate run, no owner item | **ATTRITION**, after being wrongly killed once |
| **F19** | **AH's `volume_surge_reversal × index × D1` gated on `VOL_REGIME == hi`** | **+0.2248 R/day, raw p 0.0127, 5 of 5 OOS folds positive (1.00)**, n = 203; ungated comparator +0.0999 (p 0.1204, folds 0.4). *"Admits under BH α = 0.20 at ≤ 15 declared looks and Bonferroni α = 0.05 at ≤ 3"* | OOS-w (enumerated cell, carries a 9-cell bill) | routed to Borhen **and** to the next session as *"the strongest new candidate this wave produced."* **The string `VOL_REGIME == hi` appears in no document of any later phase** | **ATTRITION — the largest un-pursued positive in the corpus** |
| **F20** | **AO's `sub_mid_dn_revert` on `slope50 < median`** | **+0.35410 R/day** at mid/RECORDED, p 0.064094, **drop-best retention −0.2704 → +0.2437** (a sign change); positive across the whole band envelope (low +0.38187 p 0.047795; high +0.30096) | OOS-w, n = 162 of 325, post-hoc median cut | AO called it *"the commission's target."* No later document picks it up | **ATTRITION** |
| **F21** | **AK's four orphan-generator cells** | `fam_session_leadlag_us30_cash_usdjpy_t2.0 @ stop_1.5x_tgtscale` **+0.2774 → +0.5637 R/day**, best-cell raw p **0.0130**, *"admits against ≤ 7"*; `ny_index_momentum @ prerollover_flat_h22` **−0.1301 → +0.1065**, 80 % folds positive; `fam_structural_retest_metal_london_short @ stop_2.5x_tgtscale` **−0.2521 → +0.1875** (Δ +0.4396); `mx_jp225 @ target_5R` **+0.6163**, p 0.0313 | OOS-w at the flat snapshot | **all four never re-gated at the ratified rule.** Each has an exact named unblock that was never executed: a cross-symbol leader feed; **"M15 bars for six indices before 2024-01-02 — the cheapest verdict-moving item"**; tick spread for eight symbols worth 2,112 trades on *"the estate's only short-side mechanism"* | **ATTRITION**, each with a priced blocker |

**F1 is the headline and it deserves restating.** *Every sleeve in the estate has a measurably
better exit than the one it runs.* Not one has been armed. And the reason is not that any was
shown to be worse — it is that **the gate that judges them is a significance test against a
32–59-look family, and an exit sweep cannot pay a multiplicity bill.** AD said so in its own §2
and routed it to a family-pool answer; AF ran breadth, refuted it as *diversification*, and left
the *accounting* question open; CS named `BREADTH` in its own repair queue and stopped. **That
decision has never been taken.**

**One caveat binds all of F1–F21**: wave 20's **M4-1** — seven sites pass
`bars_held × nominal_bar_minutes` into a cost function that reads it as wall time, under-counting
swap nights by **34.8–93.0 %** on ten sleeves and under-charging swap by **20.81 % of the term**.
*"Neither AD's exit frontier nor AH's entry-hour lever can be quoted until they are re-run."*
**One line per site. No new data.**

---

### 2.G THE DISCOVERY SWARM (wave 19, 2026-08-06) — 21 lanes, 124,722 candidates

The richest single vein in the programme, and the clearest instance of the positive-then-artifact
pattern.

| # | finding | economics | class | status | cause |
|---|---|---|---|---|---|
| **G1** | **"The signal is real, and it is present on every single instrument"** | under a repaired contract: **+0.038342 R/trade gross, t = +12.35**, CI95 [+0.030076, +0.046177], p(≤0) = 0.0000; **24 of 24 instruments gross-positive**; **53 of 63 days positive**, 43,755 trades | IS | **DEAD.** The bars are BID on OHLC and no walker crossed the spread; the bias is **−0.0696 to −0.1160 R/fill with constant sign — 2.4× to 6.1× larger than every positive gross the wave produced.** On ticks the gross is **−0.0387 (Jan) / −0.1447 (Apr)** | **ARTIFACT** |
| **G2** | **GER40 — the one instrument whose edge exceeds its toll** | net **+0.0180 R/trade** at broker truth; **+0.012 / +0.019 / +0.023** in three months; edge÷cost **1.387**; cheapest instrument on the surface at 0.501 bps | IS, n = 1,858, t = +1.23 | *"a candidate for a forward record, not for capital"* — build item 9, never built; and it inherits G1's bias | ARTIFACT (probable) + **ATTRITION** |
| **G3** | **XAUUSD × `current_fvg_fill` — the biggest number anyone found** | net **+0.284 / +0.251 / +0.276 R/trade** (Jan/Feb/Mar); survives every de-dup cut (+0.328/+0.345/+0.337); both sides positive in all three months; 83–85 % of trades positive | IS | **DEAD TWICE.** (i) It is a **resting limit order and the live engine has never placed one and cannot** — 296 of 296 captured live orders are `TRADE_ACTION_DEAL` at the executable quote, to floating-point exactness. (ii) **The population is conditioned on the fill**: at ≥1 R depth the entry is touched **100.00 %** of the time against **17.6–18.7 %** for an identical mirror limit — a **5.4–5.7× magnet ratio** worth ≈ **0.179 R/trade, larger than the +0.15 net the cell claims** | **ARTIFACT** + capability gap |
| **G4** | **Repair 1 — do not enter at the trigger bar's close** | **+0.0662 R/trade**, replicating within **0.0012 R** across three months (Jan +0.06689, Feb +0.06610, Mar +0.06572), four independent lanes. Mechanism measured: all seven families set `entry = bar.close`; the market gives back **−0.0647 to −0.0767 R** in the first minute = **27–46 % of the entire round-trip cost, paid voluntarily**. And it is adverse selection: candidates touched within 60 s book −0.19754 vs −0.03861, with a **24× separation** by first-minute violence | IS | *"the most reproducible quantitative fact in the whole swarm."* **Never built** | **ATTRITION** |
| **G5** | **Repair 2 — cancel, don't chase (60 s stand-down)** | **+0.1283 R/opportunity**; **5 of 5 months, 101 of 101 trading days positive**; 569 conditioning cells with 11 tiny negatives. Subsumes the stale-level repair — 99.98 % of past-stop rows fill inside the first minute | IS | the largest lever the swarm found. **Never built** | **ATTRITION** |
| **G6** | **Repair 3 — 0.25 R trailing exit** | **+0.0431 R/trade**; 15 of 15 cells; beats a holding-time-matched permutation at **p = 0/200 in all three months**; stacks **95.0 %** cleanly on G4 | IS | *"the only exit component that is not disguised position-sizing."* **Never built** — and the same wave measured its 0.25 R trailing stop manufacturing **+0.084014 R/trade of bar-resolution premium, 2.19× the entire G1 headline** | **ATTRITION**, with an artifact warning |
| **G7** | **Repair 4 — the per-symbol cost model** | **+0.0157 R/trade of real money**, 5 of 5 months — and it **un-deletes the index book**: the frozen model charges SPX500 and NAS100 the config's **refusal ceiling** as their expected spread (**33.90× and 18.16×** the real spread), so **not one index candidate could pass the gate in any month** | IS, 300,538,915 ticks | **BUILT** — `spread_model` shipped; wave-21's cost authority is artifact-bound | **DONE** |
| **G8** | **The stale-level generator bug** | removing candidates whose stop the market had already passed moves January **−0.21724 → −0.10392 R/trade (+0.11332)** with zero look-ahead; **98.61 % of them are one family**; **the only mechanism in the entire swarm that is majority *selection* (76.2 %) rather than abstention** | IS | **BUILT** in wave 20. Isolated: refusing **4.21 %** of emissions removes **26.54 % of the roster's entire net loss** (−33,151 R of −124,930 R); `current_breaker_re_entry` **−0.36457 → −0.04011**; **8 of 8 windows improve** | **DONE** |
| **G9** | Gates refusing profitable cohorts | `numeric_confluence_structured_disagreement` **+0.1533** (n=484), `execution_fillability` **+0.1044** (n=449), the two lockouts +0.1265 / +0.1268 | IS | **REFUTED BY ITS OWN LANE.** On orders the live engine can place: 484 → **20** rows at **−0.2481**; 449 → **0**; only the lockouts stay positive at n = 16 and 11. *"On the 14,911 orders the live engine can place, not one gate is refusing a materially positive cohort"* | **ARTIFACT** (population) |
| **G10** | Stop-width ordering | widest-minus-tightest decile **+0.0931 R/trade, 5 of 5 months** — *"a real effect by accident, through a broken model, in the wrong units"* | IS | **INVERTED** by the quote-side repair: correlation **−0.8287 → +0.8716**; the tightest-stop decile, the only gross-positive cell, becomes the **worst at −0.29168**, handing the broker **29.4 % of its risk unit at the door** | **ARTIFACT** |
| **G11** | **The 507 / 464 trades the system actually took** | 507-trade set: OLD gross +0.18045, toll 0.14938, **net +0.03107**; corrected gross +0.05216, toll 0.01108, **net +0.04108 — it improves**. 464-trade roster: gross **+0.05505**, toll 0.07437, net −0.01932; gross win rate **47.20 % vs 44.13 % breakeven = +3.07 pp** | IS | *"still indistinguishable from zero"* — day-block CI95 **[−0.0525, +0.1389]**, p(≤0) = 0.20 over 153 day blocks; the roster deficit is **2.5× smaller than its own standard error**; resolving it needs **10,951 trades = 14.4 years** | **GATE** (power) |
| **G12** | **The stack ADDS value — three independent measurements** | vs the trades it declined **+0.14961 [+0.03964, +0.26157], p 0.0027** (n 396); vs a random roster draw +0.08800 (p 0.060); vs a clean roster draw +0.06667 (p 0.123). Layer capture: gate **16.75 %**, ranking 10.81 %, exit **−0.44 %** | IS, matched controls | *"Selection adds ~+0.045 gross; management a further ~+0.023… it is the reason the number is near zero instead of well below it."* **This is the direct answer to "is it the way we're using them": NO** | standing |
| **G13** | Signal inversion on at-market rows | **+0.0764 R/trade, t = 8.71**, n = 14,911 | IS | *"Partially real, not harvestable"* — 81 % gone after two minutes, worth 0.783 bps against a 1.566 bps two-leg spread. Killed outright by Phase 0 | EVIDENCE |
| **G14** | Broker-true cost measurement | the frozen model overcharges the pool by **+0.4739 R/trade** | IS | **100 % of the overcharge sits on rows the gate refuses.** On admitted rows the error is **−0.0315** — it slightly *under*charges. *"A bookkeeping correction, not recoverable money"* | honest self-correction |
| **G15** | The detection floor | *"January resolves an effect where only **1.03 % of rows change side** (p = 0.0235). The test can see an effect **32× smaller** than the level the family needs, and it sees nothing"* | IS | **PASS** — makes "nothing found" a result rather than an absence | — |
| **G16** | **The accumulation discriminant** | live sleeves **3.41 bps @ 2 h → 128.04 bps @ 320 h = 37.58×**, edge÷toll at 320 h **4.38**, clearing their own toll by **2.36×–11.46×**; broad family **0.2008 → 0.1938 = 0.97×**, edge÷toll **0.06** | OOS-w | **both ratios retired** — 37.58× was mostly a coin draw (deterministic mirror gives **15.94×**) and 0.97× had CI95 [−2.07, +2.22]. **Replaced and it is cleaner**: **P(growth ≥ 10×) = 0.0073 (broad) vs 0.629 (live sleeves)**; at 320 h the live control clears its own larger toll at the **bottom** of its 95 % interval (1.40× over) while the broad family is **7.4× short at the top** of its own | **ARTIFACT** (the ratios) — **the discriminant survives and is stronger** |
| **G17** | **The oracle ladder** | shipped stack **−0.29226** vs coin flip −0.29447 (own share +0.00221); + oracle exit **+1.71862** vs +1.69333; + oracle entry instant **+2.33914** vs **+2.31133**; + oracle direction **+3.58285** vs +3.58381 | IS | *"Every rung is 98–105 % reproduced by a coin flip. 98.8 % of that perfection is market noise available to anybody holding that instrument."* A correct direction call is worth **+0.88898 R/trade** to the shipped machinery; **this family delivers +0.00221 of it — 0.249 %** | **EVIDENCE**, decisive |

---

### 2.H THE BROAD-V4 / B7.5 LINE

| # | finding | economics | class | status | cause |
|---|---|---|---|---|---|
| **H1** | **THE THREE SEALED MONTHS — the best out-of-sample replication in the corpus** | **gross +0.027176768863484385 R/fill**, CI95 **[+0.010964894, +0.042931939]**, **p(≤0) = 0.001, 3 of 3 windows positive**: June **+0.04023578702708158** (22,494), Aug **+0.025005181615061472** (36,403), Sep **+0.021658268311688576** (38,905). Win rate **39.34 % vs a 38.19 % gross breakeven (+1.15 pp)** | **OOS-v** — June/Aug/Sep 2025 *"sealed all year… opened once, on a hypothesis written down and committed before the seal was broken"*, 97,802 fills | **CONFIRMED, then qualified almost to zero**: *"measured with a walker we now know is optimistic by 0.024–0.070 R/trade. Corrected, the family's true gross is zero or slightly negative."* The toll is **12.6× the entire edge**; in price terms **0.0119 bps captured vs 3.0159 paid = 253×** | **ARTIFACT** + **ACCOUNTING**. **And the three sealed months were never re-walked on the corrected instrument** — wave 20's open-item 5, *"the cheapest remaining item"* | 
| **H2** | **`structural_distance_extreme`** — *"the single most interesting unsettled thing in the estate"* | **gross-positive in 15 consecutive windows across three independently written harnesses**: +0.06639 over eight open months, **+0.12522 over three sealed ones**; then **16** when the never-read tick window extended the streak at +0.0124 | IS ×15, plus **OOS-v** | **CLOSED on 177,046,057 real bid/ask ticks**: frozen roster **+0.0418 → −0.2131** (CI95 [−0.2608, −0.1624], p(≤0) = 1.0000); never-read window **+0.0124 → −0.3586** (CI95 [−0.4097, −0.3054]). Positivity **6/7 → 0/7**, **4/6 → 0/6**, **15/24 → 1/24 instruments**, **0/5 risk quintiles**. *"The persistence is real and it is an artifact of quoting both legs on one side of a book the round trip crosses twice."* **And there was never a direction call**: the exact side mirror books −0.2504 / −0.3453 against the family's −0.2131 / −0.3586 | **ARTIFACT** |
| **H3** | **The BTCUSD cell inside H2's grave** | never-read window, median `s/d` **0.0162** — the **only** instrument of 24 below the measured **s/d ≈ 0.04** break-even — tick-true **+0.1750 R/trade**, raw p **0.063 at 1.5R / 0.050 at 2R**, signal vs mirror **+0.350**, n = 100 over 32 days | **OOS-v** | *"Not admissible: one instrument, one 5-week window, raw p only, 24-instrument family bill unpaid. It is a **pre-declarable hypothesis**"* — filed honestly and **never declared** | **ATTRITION** (deliberate, correctly reasoned, still unclaimed) |
| **H4** | **`liquidity_sweep_reclaim × LONG` — reproducible pre-cost information** | **+0.03013 TRAIN / +0.03483 HOLDOUT gross R/row**, FULL +0.03177, 69.2 % / 62.5 % gross-positive days, family-wise **max-T p = 0.001998**; FULL net **−0.48234** | **TRAIN + untouched HOLDOUT, protocol committed before outcomes** — the strongest genuine OOS claim in the broad line | *"CK files that signal; CK does not graduate it."* CQ re-priced through CN's exact commission chain and confirmed: *"No liquidity cell is persistently net-positive in either orientation"* | **ACCOUNTING** (cost) |
| **H5** | **January's separable opportunity** | **+6,916.94750286 R positive / −31,400.82177687 R negative = ±38,317 R over 28,519 scoreable rows in one month**; 8,006 positive / 20,513 negative rows | IS | *"a discriminator ranks layers of a losing system; it cannot locate edge"* — the sealed factorial tested **two binary switches, four cells, two bits of information**. **AW measured it and both reframed and killed it**: *"a perfect selector captures the +6,917 R, not the 38,317; and any real rule must reach 65.5 % precision against a 26.5 % base rate — a 2.47× lift"*. Result: **0 of 212 declared cells** with a positive train mean; best cell −0.1440 vs a pool mean of −1.0135; pool negative on 21/21 Jan, 8/8 holdout, 9/9 April days | **EVIDENCE** |
| **H6** | **AW's axes ARE informative** | train→holdout Spearman over cell means **0.919**; train→April **0.903**; fitted model **AUC 0.712 on held-out days, 0.669 on April** | **OOS-w, declared before any outcome read** | **INSUFFICIENT**: *"The pool needs +0.947 R/row to break even and the best conditioning delivers +0.87 — consistently 0.15–0.25 R/row short"* | **EVIDENCE** |
| **H7** | **FE's rank persistence** | Spearman **gross 0.443847 (max-adjusted one-sided p 0.002); net 0.894602 (p 0.001)**; family η² 0.06034/0.08684 (p 0.001) | TRAIN→HOLDOUT | **No gate earned** — *"stable ordering inside a wholly negative surface, not ex-ante profitable selection"* | EVIDENCE |
| **H8** | **FE's four gross-positive frontier cells persisting in BOTH splits** | `current_fvg_fill · SHORT · London` **+0.2440 TRAIN / +0.0247 HOLDOUT** gross (net −0.2161 / −0.2410, 48.84 % of rows ≤0.15R); `liquidity_sweep_reclaim · LONG · London` +0.0074 / **+0.1762**; `· SHORT · London` +0.0398 / **+0.1068**; `displacement_continuation · 14:00–15:00 UTC` +0.0355 / **+0.1271** | TRAIN + HOLDOUT + frozen February transfer | **Zero net-positive, zero strict survivors.** Only the FVG cell clears a hypothetical flat 0.15 R cost (+0.01349 R), and *"even that cell transfers at −0.20444 R net in February."* Stop widening left as *"a priced hypothesis requiring path recomputation"* | **ACCOUNTING**, then **ATTRITION** |
| **H9** | **FB's `current_ob_retest` 1.5D/0.25D — a NEW repair needing no inversion** | **TRAIN n=799 +1.630823 net R/trade; HOLDOUT n=541 +1.670197; FULL n=1,340 +2.862377 gross / +1.646719 net**; LONG +1.698900 (746), SHORT +1.581186 (594); family-wise **max-T p = 0.001** (the 999-draw resolution floor) | **TRAIN-only selection + untouched HOLDOUT persistence + both directions**, protocol committed before any outcome computation | Implemented **research-only, explicit-argument, default-off**. **Never promoted, billed, queued or armed.** FG ranks it **#1 next action**; its gate node **O1** is `ADOPTED_AS_WRITTEN` — the declared bill is already sunk | **ATTRITION** |
| **H10** | **FA's oracle gap — the surface measurably contains edge** | **92.5 % / 90.0 %** of January/February decision points carried an ex-post-positive candidate; oracle best **+1.164 / +1.179 R/decision-point**; **≈1.35 R/dp invisible to every field in the ledger family** | IS (ex-post oracle) | *"EVERY rule computable from predecision fields is negative in both windows"* (argmax-EV −0.206/−0.215; argmax-p −0.321/−0.383; min-cost −0.229/−0.129) | **EVIDENCE** |
| **H11** | **February's executed book is GROSS-POSITIVE** | Feb executed **gross +0.203919 R**, cost 4.165 → net −3.961 on 58 trades; **target-first trades are 100 % positive in both months (+12.79 / +12.84 R)** | IS | standing finding; feeds the exit-geometry loss class | — |
| **H12** | **CJ's re-clock** | sealed labels were true UTC **+2.0 h**, validated **54/54 weekly opens**, **96/96 bar pairs**, **778,162 overlap rows**, zero non-time residual. Re-clocked January moves the broad family **+3.435 R** (−8.94126133 → −5.50620829) | **IS (VAL)** | governing; still negative (−5.506), 21/21 negative days unchanged. Cost: **the parked B7.5 campaign's ~36 MH resume option died, exactly as priced** | honest |
| **H13** | **FE / FB's cost-killed strata** | FB: **20 eligible strata gross-positive and cost-killed** (7 family-scope + 13 family×direction); CQ: **86 persistent gross-positive/cost-vetoed cells**; FB February: `session_open_range_break` **+94.727 gross R** and `regime_transition_break` **+9.699** | TRAIN + HOLDOUT | filed as *"higher-information"* repair inputs: *"future repairs should change cost-normalized geometry/execution or condition the mechanism, not declare the broad family dead"* | **ATTRITION** |
| **H14** | **The B7.5 January bank's one positive cell** | interaction **+0.007397383907**, sealed as `non_claimable_positive_with_execution_suppression`; and F31's `final_target` rows: **8 rows, 0/8 adverse, Σ +0.539109 R, mean +0.067389** — the only positive line in a −8.095 R net over 212 rows | IS | never claimable by construction (inside the ±0.1 materiality band) | — |

**The broad-V4 verdict, and it is settled.** *"It is the SIGNAL. Not the usage."* The setups
capture **0.0119 bps of price per trade against a 3.0159 bps round-trip toll — a factor of
253 — and that capture does not grow with holding time. A working sleeve's does, by 37.6×."*
Three levers exist and all three are closed: capturing more price would need 253× (282 contract
shapes priced, 0 net-positive, and the direction call gets *worse* as the contract widens); paying
less toll is closed on arithmetic (**a free broker still leaves the book at −0.00600 R/trade,
102.12 % cost reduction required**); and selecting the good cells is closed empirically (324
out-of-sample selection arms, **zero positive books**, median 97.7 % of every improvement being
toll removed; **the oracle ceiling with perfect hindsight buys +0.02548 against a 0.30825 toll,
12.1× short**).

**Wave 20 sharpened the verdict and retired three of its numbers**: the 253× has *"no numerator"*
(negative before any repair), the 0.97× *"dies as a number, survives as a bound"*, and the 37.58×
*"was mostly a coin flip."* The verdict itself is **UNCHANGED and better supported**.

---

### 2.I THE CEREMONIES — positives that reached a live host

| ceremony | what | economics | current state |
|---|---|---|---|
| **5-sleeve expansion** (2026-07-30) | `--tags` 3 → 5 (`+fx_jpy, +sub_mid_dn_revert`) | priced at OD-AI-3 measured p99: P2 **0.9172 → 0.8915** for **4.501 → 6.120 %/mo** and **60 → 48 days** | `fx_jpy` pulled the same day; **`sub_mid_dn_revert` remains armed** |
| **`mx_btcusd`** (2026-07-31) | the estate's one sealed-standard admission | +0.198 R/day recent-fold basis, conf 0.025 | **DISARMED 2026-08-05** (owner) |
| **Spread-geometry floor** (2026-07-31) | AW/AY's fidelity repair on two sleeves | `sub_mid_dn_revert` +0.4260 R/day (p 0.163 → 0.023); `sub_xvol_pullback` +0.2644 (p 0.012 → 0.0020); recent-fold **+0.0410 / +0.2559** | **STILL ARMED, both accounts** |
| **CM — `crypto @ stop_1p5x_target_scale`** | AD's F9 cell via `--frontier-exits` | +0.25267 R/day pooled, **+0.03552 latest-fold**, 4/5 paired folds | **ARMED 2026-08-06 → ROLLED BACK 2026-08-10** (owner); on the corrected walker it prices at **+0.005 R/day**, 2/5 folds |
| **CN — broker-true commission as the fourth cost term** | fail-closed, both books | 147/174 same-input decisions charged; **7 flips, every one PASSED → REFUSED, zero new-PASS**; commission R median 0.014620 | **LIVE since 2026-08-06.** Its `broker_net_cost_engine.py` edit is the **authorized forward R2 seal break** |
| **CO — the learning lane's first live vector** | FTMO `crypto` ×1.15 + `mx@target_5R` ×1.15 | FTMO `p_pass` 0.99980 → 0.99982; redacted_account byte-equivalent | **LAPSED** — declarations expired 2026-08-08, never executed |
| **Owner-manual-move patch** (2026-08-05) | stop the book overwriting an owner-set SL | measured A/B on the live host: *"BASE sends 1 request and the owner's 80.511 stop becomes 83.233; PATCHED sends **0**"* | **LIVE** |

**Net: of seven things carried live on the strength of a measurement, three survive (CN, the
spread floor, the manual-move patch), one survives partially (`sub_mid_dn_revert`), and three were
withdrawn or lapsed within eleven days.**

---

### 2.J THE INSTRUMENT — positives that are real and are not trades

| # | finding | economics | status |
|---|---|---|---|
| **J1** | **J's broker-truth cost layer** | reproduces realized broker truth to **0.000535 R** against a shipped model whose error is **0.0591 R** — a **110× improvement** | **BUILT, and LIVE via CN** |
| **J2** | **The measured clock** | broker server wall clock = `America/New_York + 7 h` for both brokers over **81 weekly session boundaries per broker**; all transitions on **US** dates | **BUILT** (`broker_clock.py`, fails closed on an unregistered server) |
| **J3** | **AT's test-suite triage** | **639 standing failures → 67**, per-test proof, all live coverage kept | **BUILT** — the suite now reports code |
| **J4** | **AB's regime-dial identity finding** | AB's dials **ARE** the substrate sleeves' own firing coordinates — a bucket-level regime gate is a **no-op**, pinned by 14 tests | a clean negative that saved a wave |
| **J5** | **The candidate-family ratchet** | the historical 69-look family **double-counted**; published q-values were **over-corrected** | **BUILT** and now the binding constraint (see §5.2) |
| **J6** | **AE's cost-true learning lane** | **all seven** legacy-covered verdicts changed. `crypto` INSUFFICIENT_EVIDENCE → **SIZE_UP ×1.08**; **`metals_core` SIZE_UP ×1.15 → DOWN_WEIGHT ×0.50** on a 232-trade / 118-day OOS at −0.205 R | default-off, recommendation-only; `live_n = 0` on every armed sleeve. **The ×1.08 half is ATTRITION** |
| **J7** | **CB / CG / CD's lane engines** | wall **657.0 → 428.8 s (1.532×)**, peak RSS **8.31 → 2.97 GB (0.358×)**, four-arm window **2,628 → 527.6 s (4.98×)**; CG's lean floor 646.830 → 480.429 s at RSS 0.3752×, `OUTCOME_IDENTICAL` at zero tolerance; storage **17.04 GB → 1.92 GB (88.74 % removed)**; a four-arm month **~16.5 h → ~3.0 h** | **ADOPTED** — this is why waves 16–19 could run at all |
| **J8** | **AY's conviction-count contamination, closed by construction** | **16 contaminated account-days, 3 moved the multiplier, worst +25.227 %** on every unit that day | closed by the armed spread floor — *"does NOT depend on whether the filter improves any sleeve's expectancy"* |
| **J9** | **BB's silence alarm** | warn at **15** silent weekday sessions, alert at **22**; all three estimators agree at **1.1 and 0.0** expected false alarms per year (later per-account: FTMO 14/21, FN 15/22) | **SHIPPED** |
| **J10** | **BC's command center** | reads `--tags` from the running worker's own command line and equity from the broker. Demonstrated on the export: **both workers running with NO `--tags` at all**; launcher-log union under-reports redacted_account by **3.2×** | **SHIPPED** |
| **J11** | **CF's symbol sweep** | FTMO 137 slots → **135 resolved, 0 resolved-but-absent**; redacted_account 137 → 104, 0 absent. *"There was no rename… the armed book was never degraded"* | **PASS — the deliverable is the ceremony that does NOT happen** |
| **J12** | **The forward shadow lane** | deployed and **MEASURING** on the VPS 2026-08-11 08:01:24Z; cost preflight ok, **24/24 commission-resolvable**; first cycle 89 candidates / 46 eligible / 24 symbols; `broker mutation: false`; dual-lane with daily prequential refit | **LIVE, zero risk, zero forward result yet.** Caution published: solver drift is **2.8e-3 on the Windows host** vs 1.1e-16 on darwin — *"never read shadow output as bit-identical to the sealed reads"* |
| **J13** | **The geometry-bound outcome model** | first **result-bearing** calibration artifact; 44 days / 292,987 occurrences / 64,389 resolved fills; 198 of 254 cells terminal-evaluated; `economic_authority_allowed: true` | **wired-but-off** — appears in **zero** committed config files; **no out-of-sample economic result has been read through it** |

---

## 3. TOTAL POSITIVE ECONOMICS PRODUCED vs DEPLOYED

The units are incommensurable, so the accounting is done four ways. Each is stated in the unit its
evidence uses; none is added to another.

### 3.1 In absolute R, on populations that were actually walked

| population | published positive | after the repairs that were run | class |
|---|---:|---:|---|
| **the live sleeve estate**, 22,354 trades, 32 sleeves, 2017–2026 | **+2,520.7 R** gross | **−619.8 R** gross | IS |
| the broad-V4 roster, 1,167,099 emissions, 8 windows | **5 of 10** families gross-positive, **36 of 80** family-months | **0 of 10**, **2 of 80** | IS |
| the funnel's five sealed months | **+14.168 (Feb)** | Feb stands; the other four windows pool **−19.33** | **OOS-v** |
| January's diagnostic pool | **+6,916.95 R** of positive rows | 0 of 212 declared cells separate it | IS |
| the 507 trades the broad system took | **+0.03107 R/trade net** | **+0.04108** (improves) | IS, p(≤0) = 0.20 |

> **The estate's headline positive was +2,520.7 R and it is now −619.8 R. That is the best
> one-number answer to the owner's question.** The R did not go to gates and it did not go to
> attrition. It went to the discovery that every walker resolved stops and targets against a bid
> series without ever crossing the spread — a correction of **−0.140489 R/trade (se 0.004619)**,
> one-directional: **732 `target→stop`, 127 `trail→stop`, 50 `maxbars→stop`, and zero the other
> way. 736 of the 7,552 targets the estate books — 9.75 % — did not happen.**

### 3.2 In R/day, on the frontier

| block | measured improvement | admitted | armed |
|---|---|---|---|
| AD's exit frontier | **25 of 25 sleeves improve, median +0.249 R/day** (of which ~+0.041 survives a side control) | **0** | **1** (CM) — withdrawn after 4 days |
| AK's four orphan generators | +0.1065 to +0.5637 R/day, one at 5/5 folds | 0 | 0 |
| AF's 30 mechanism families | best pooled raw p **0.1204**; 2 of 30 coherent (+0.4571 R/day) | **0 of 30 families, 0 of 246 members** | 0 |
| AM/AH's entry hour | +0.063…+0.141 R/trade net, 38/42 members improve | **0 of 72 arms** | ratified as a convention only |
| AU's D1 horizon ladder | six DECLARE prescriptions, Δ up to +0.5913 R/day | **0 of 352 arms** | 0 |
| AY/AW's spread floor | +0.2118 to +0.9977 R/day, all four armed sleeves improve | **0** | **2** (still armed) |

**Deployed share of the measured frontier: three cells out of roughly sixty, one of which was
withdrawn after four days.**

### 3.3 In %/month, at the book level

| basis | rate | deployed? |
|---|---:|---|
| the selection window, published sizing | +2.617 %/month | **the number the book runs on** |
| the selection window, 2.0 % dial | +5.460 %/month | quoted |
| armed three at firm-true rules (W7 caches) | 4.501 %/month, P2 0.9172 | quoted |
| five sleeves | 6.120 %/month, P2 0.8915 | quoted at arming |
| **the same three on the ARCHIVE** | **0.313 %/month, P2 0.566017** | **never used** |
| **pre-2025, ten years** | **+0.100 %/month** | **never used** |
| **2015–2019** | **−0.220 %/month** | **never used** |
| armed four, archive, after wave 20's repair | FTMO 2-phase **0.5157 honest / 0.3370 conservative** | **not yet reconciled to the numbers above** |

### 3.4 In realised money

**+$493.20 on one trade whose exit the owner chose, and $0.00 on the second account.**

### 3.5 The disposition census

Counting ~190 distinct positive findings recovered across all sources. *(Method: each finding
assigned one primary cause; where two causes are independently sufficient the earlier one in the
timeline is recorded. Counts are approximate to ±5 at the boundaries between EVIDENCE and
ARTIFACT.)*

| disposition | count | share |
|---|---:|---:|
| **DEPLOYED and still live** | **5** — CN cost truth, the spread-geometry floor, `sub_mid_dn_revert`'s arming, the broker clock, the owner-manual-move patch | ~3 % |
| **BUILT into the instrument** (real, non-economic value) | ~14 | ~7 % |
| **ARTIFACT** — the number was never real | **~32** | **~17 %** |
| **GATE** — economics stood, statistics refused | ~26 | ~14 % |
| **ACCOUNTING** — a protocol rule refused it | ~14 | ~7 % |
| **EVIDENCE** — a later honest measurement contradicted it | ~24 | ~13 % |
| **OWNER** — withdrawn by decision | 4 | ~2 % |
| **ATTRITION** — nothing killed it; nobody continued it | **~50** | **~26 %** |
| **OPEN / unfinished (not refuted)** | ~9 | ~5 % |
| context, controls and nulls that were never candidates | balance | — |

**Three conclusions from that table:**

1. **ARTIFACT is bigger than GATE.** More positive results were destroyed by the measuring
   instrument than by the multiplicity bill — and the instrument defects were *systemic*, not
   scattered: one bid-series convention, one fill-conditioning bias, one past-stop generator bug,
   one `time_stop_bars` unit error, one missing side control, one holding-time unit error **still
   unrepaired**.
2. **ATTRITION is the largest single category and it is a quarter of everything.** The owner's
   suspicion is confirmed and it is larger than he probably expected.
3. **DEPLOYED is ~3 %.** Five things out of ~190, and one of the five is a defensive patch.

---

## 4. THE ATTRITION LIST — free options the estate already paid for

Ranked by value × credibility × cheapness. Every row was **measured positive and never refuted**;
no document kills it and no later document picks it up. Where a later instrument repair changed
the baseline, that is stated as a precondition rather than a kill.

| rank | finding | measured value | why it is a live option | cost to revive |
|---:|---|---|---|---|
| **1** | **AD's exit frontier — the whole surface** | 25 of 25 sleeves improve, **median +0.249 R/day** (≈+0.041 after the side control); on 23 of 25 the best exit beats eliminating carry entirely | Never contested on economics. AD's own §2: *"an exit sweep cannot pay a multiplicity bill"* — and it routed to a **family-pool answer that was never produced.** Four of the 25 sleeves are **armed today** | Fix **M4-1** (one line per site, no new data), re-run with p2's side control, then take the family-pool decision. **~2 sessions** |
| **2** | **The funnel's abstain discipline** | **+18.9 / +6.6 / +28.9583 R** vs its own naive expression — three windows, **OOS-v ×3**, never negative, and the one **passing** gate in the read that killed the rule | *"The selection layer has real relative skill; the candidate population underneath it is what is negative."* **Nothing has ever been built on the skill half.** It is the only quantity in the programme that has survived three consecutive virgin reads | Point it at a candidate population that is not negative. The forward shadow is already running and is the instrument. **~1 session to specify** |
| **3** | **AH's `volume_surge_reversal × index × D1` @ `VOL_REGIME == hi`** | **+0.2248 R/day, raw p 0.0127, 5 of 5 OOS folds positive**, n = 203; *"admits under BH α = 0.20 at ≤ 15 declared looks and Bonferroni α = 0.05 at ≤ 3"* | Routed to the owner **and** to the next session as *"the strongest new candidate this wave produced."* **The string appears in no later document.** Its family (`volume_surge_reversal × index × D1`) is also **one of only 2 of 30** to pass AF's two-clause coherence test | Re-gate at the ratified rule on the existing trades. **Hours, not sessions** |
| **4** | **The pooling repair — *"the only structure that has ever cleared a family bill"*** | three declaration changes, **no code, no data**: merge `mx_btcusd` + `mx_ethusd` + `vol_compression` (whose BTC/ETH leg is **100 % contained** in the mx sleeves — one hypothesis billed as two members at two weights in two clusters); six index volume-surge sleeves → one member; three killzone sleeves → one family | It attacks the **binding constraint** directly. At **m ≤ 16** the two best sleeves ADMIT at α 0.10; the estate bills **59**. *"AF's coherence test exists for exactly this and **has never been run on the mx cohort**"* | **A declaration, not a measurement.** Cheapest high-leverage item in the ledger |
| **5** | **FB's `current_ob_retest` 1.5D/0.25D** | **FULL +2.862377 gross / +1.646719 net R/trade** on 1,340, family-wise **max-T p = 0.001**, **TRAIN-selected and HOLDOUT-persistent, both directions**, no inversion needed | Built research-only and default-off. **FG ranks it #1 next action.** Its gate node **O1** is `ADOPTED_AS_WRITTEN` — **the declared bill is already sunk** | Run its independent path-complete RECORDED folds. One session |
| **6** | **G5 — cancel-don't-chase (60 s stand-down)** | **+0.1283 R/opportunity**; **5/5 months, 101/101 trading days positive**; 569 conditioning cells, 11 tiny negatives | Largest lever the discovery swarm found; subsumes the stale-level repair. It inherits the quote-side caveat *as a level*, but a stand-down is a **paired filter on the same rows**, and wave 20 proved paired deltas survive the correction at a **25.7× ratio** | Re-price as a paired delta on the corrected walker, then build. ~1.5 sessions |
| **7** | **G4 — the 5-minute entry delay** | **+0.0662 R/trade**, three months within **0.0012 R**, four independent lanes; the mechanism is measured, not inferred (**27–46 % of the round-trip cost conceded voluntarily at `bar.close`**) | Same argument as rank 6, and it is the most reproducible number in the programme. Stacks **95 %** cleanly with rank 8 | Same lane as rank 6 |
| **8** | **F18 — `stop_only_horizon` beats `target_2.0R`** | **+0.039161 R/emission**, day-block CI95 **[+0.01154, +0.06977]**, **p 0.00235**, over **1,127,805 emissions**; **8/8 months** after the correction | **It already survived the instrument repair** — level moves −0.102379, paired delta only −0.003990. It was killed once by a category error (comparing a paired delta to a level bias) and the kill was retracted. **No follow-up, no gate run, no owner item** | Free — it is measured. It needs a decision |
| **9** | **`sub_mid_dn_revert`'s own exit frontier** | **−0.106 R/day with `expectancy` failing → +0.092 / +0.059 / +0.008 with it passing**; best cell `time_stop_20` → `time_stop_40` | **This sleeve is armed today**, lost **97.7 %** of its expectancy to the quote-side correction, and has its three oldest folds negative and its two newest positive. Wave 20's own open-item 4: *"Regime story or spread-era story? That is the difference between 'this sleeve is dead' and 'size it on its recent folds'"* | Re-run the cell on the corrected walker + M4-1. One session |
| **10** | **`energy_agri`'s mechanism class** (`energy_fvg_retest` × energy × H4) | **+0.4571 R/day**, the strongest pooled mean in AF's grid; **3/3 members positive**, dispersion ratio **0.117** — the tightest coherence measured anywhere. AP's peer transfer takes it to **+0.5641** and clears `robustness` | **1 of only 2 of 30** families to pass the coherence test, and the sleeve it generalises is **armed**. It fails on *sample*, and the fix is a **`NATGAS.cash` commission + CORN/COTTON bars** — a data capture, not a research question | The capture |
| **11** | **The three sealed months, re-walked** | **+0.027176768863484385 R/fill, p(≤0) = 0.001, 3 of 3 windows** — the estate's last standing positive statement about the broad family, on genuinely virgin data | Measured on the **uncorrected** walker. Wave 20 **bounded** it (the correction is 4.7× its size with constant sign) rather than measuring it. **Those rows are already spent, so re-walking costs no held-out data** | *"The cheapest remaining item"* — wave 20's own open-item 5 |
| **12** | **The never-opened slow grid** | `deep_universe_h4d1_2014_2026` — **48 files, exactly the broad family's own 24 instruments, H4 + D1, 2014-01-02 → 2026-06-15, 439,895 bars, 12.5 years, 27 MB, zero references across all 607 discovery files** | *"The only untested form of 'the setups are fine, the contract is wrong'."* Its pass condition is **pre-declared**: signal must grow ≥ 3× from shortest to longest horizon and clear its own toll on held-out years | Run it. The data is on disk |
| **13** | **CE's unarmed FX D1 cohort** | rollover premium **×7.8–×10.6**; AH's **+0.063…+0.141 R/trade** measured end-to-end **on exactly these members**, 38 of 42 improving; per-symbol premium up to **CHFJPY ×19.9** | *"The lever's real home… the natural next incubants and the mechanism is now ready for them."* CH measured only 7 rows on a different sleeve. **The cohort was never incubated** | Incubate. The mechanism is built and ratified |
| **14** | **F9a — the horizon lever on armed `crypto`** | on the corrected walker, `target_4.0R\|maxbars_160` and `target_5.0R\|maxbars_160` beat **both** CM and the shipped 4R at **every band**: **+0.08 to +0.27 R/day over CM, +0.08 to +0.14 over shipped** | Found while pricing the CM rollback and **never raised as an owner item**. *"The lever this population points at is the horizon, not the stop width"* | Price the carry (this walker is gross-of-swap) and gate it. ~1 session |
| **15** | **AR/AO's `vr` ordering** | risk-weighted efficiency **×1.0996** vs blind constants **×1.0005 / ×1.0008** — a **125× separation**; independently, tertile net R/trade **0.512 → 1.111 → 2.124**, permutation **p 0.00025** | The *headline* was 85 % artifact and AR was right to withdraw it — **the ordering is separately measured and survives its own control**, and lives wired-but-off | AR's own handoff prices it at **"one afternoon"**: the path-free efficiency measurement at the other three bands with a constant control at each |
| **16** | **AF's `volume_surge_reversal` coherence + AO's `slope50` cut** | 6/6 members positive at raw p **0.1204** (AF's best); `sub_mid_dn_revert` on `slope50 < median` **+0.35410 R/day** with the robustness statistic restored from **−0.2704 to +0.2437** | Both are conditioning results on sleeves the estate already owns; neither has any follow-up | Inside ranks 1 and 4 |
| **17** | **H3 — the BTCUSD cell in `structural_distance_extreme`'s grave** | tick-true **+0.1750 R/trade**, raw p 0.063 / 0.050, signal vs mirror **+0.350**, median `s/d` **0.0162** — the only instrument of 24 below the s/d break-even | Correctly filed as *not admissible* and **pre-declarable**. **Nobody declared it.** It is the one cell that survived the tick walk that killed the family | Declare the 24-instrument family bill **first**, then test |
| **18** | **CL's two incubation proposals** | `mx_ethusd @ target_5R` **n = 217, +0.456628 R/day, recent-two +1.010822**; `asia_pdl_fade @ stop2.5_native_no_ts` **n = 2,827, +0.084626 R/day, 5/5 positive folds** | Both filed `PROPOSED` at confidence 0.025, both blocked on **exact live-contract parity** — a wiring question, not a research one. No later document measures either | Wire the contracts, then re-gate. Note rank-18b below |
| **18b** | *(precondition on the second)* | p3's stop-floor sweep **REJECTS `asia_pdl_fade` at every k and every band on the corrected walker**, best p_raw ≥ 0.9938 — and **no document states this kill** (JSON-only receipt) | This is the clearest example in the ledger of a positive dying in a receipt nobody reads | Write the kill up, or refute p3 |
| **19** | **The CM/CN/CO ceremony residue** | CO's signed vector (**×1.15** on `crypto` and `mx@target_5R`, `p_pass` non-negative both accounts) **lapsed unexecuted on 2026-08-08** | Built, chain-verified against live host bytes in the exact order CM → CO → CN, **executable as built, no rebuild** — and then two of the three were withdrawn and the third expired | Fresh signatures, never date edits |
| **20** | **OD-BA-1 — the cheapest open owner question in the estate** | *"Does the redacted_account weekend rule reach a 24/7 instrument?"* is worth **+0.2197 R/day, +11.7 pp of `p_pass`, −78 days** = **28.3 % of the entire weekend-policy bill** | *"Both are answerable today… the cheapest item in the whole activation package."* No answer is recorded anywhere in phases 15–19 | One question to the prop firm |
| **21** | **A15 — the inverted-entry fill measurement** | adverse fill **0.0057 R**, latency ≤ **0.0006 R**, over 21,449 triggers / 88.7 M ticks — refuting a feared 0.15 R by **~250×** | Removes latency as an objection to **any** momentum-entry design, including ranks 6 and 7 | Free — already measured |
| **22** | **A8/A9/A10 — the post-mortem's unfrozen hypotheses** | SD5 brake **+11.23 R** 3-month with the tail 2.9 R smaller; `s1p5_t2` **+16.18 R** whole-set; SORB `s0p75_t2` **+7.18 vs +1.00** | Explicitly designated *"the hypothesis the June/July window tests"* — and the prereg that would have tested them was overtaken by the Phase-0 kill. **Unfinished, not refuted** | A prereg on a virgin window. **March 2026 is the only one left** |
| **23** | **J46–J49 portfolio policy** | **+0.742 R/trade, n = 321, p = 3.3e-20, deflated 1.23e-7 (5.16σ)** — the strongest single-policy statistic ever recorded in this repository. Its own table row read **"SURVIVES — research-only, branch be33522"** | **Branch `be33522` no longer exists.** Nothing killed it; a CLAUDE.md rewrite reclassified it as *"historical unless a current artifact explicitly labels it active"*, and no current artifact does | Re-derive from the deleted branch's reachable objects, if any survive. **Low probability, extreme value if it lands** |
| **24** | **FA's two licensed-but-unbuilt repairs** | Arm (v): 12,668 breaker candidates transformed, geometry verified 483/483, **zero trades** — **100 % refuse at an R-denominated cost gate at any ceiling** | *"No high-RR candidate can ever pass it, whatever its realizable economics."* The repair is licensed: **(a) a price/notional-denominated pre-trade cost gate, (b) a candidate-declared-target passthrough.** ~1 session each, **neither built** | This blocks every high-RR candidate the estate will ever generate |
| **25** | **FA's fill axis (T1)** | **fvg +0.75 / ob +0.64 R gap** to the fill-free ceiling; the **0.92 `execution_fill_probability` constant is load-bearing and wrong on exactly those families** | *"The deepest open economic thread."* Needs P1-class tick captures, `SCHEDULED-ON-NEED` | The capture |

---

## 5. WHERE THIS PROGRAMME'S OUTPUT HAS ACTUALLY BEEN GOING

Five mechanisms, in descending order of cost.

### 5.1 The ruler was bent, and it was bent in our favour

The largest single cause, and it is not close. **Every walker in the estate resolved stops and
targets against a BID archive without ever crossing the spread** — settled three independent times
at exactness: M15 archive **1.00000 on 33 symbols**, M1 packs **1.000000 on 28 files**, a
never-read tick window **1.0000 on all 24 instruments**, with `(close − mid)/spread = −0.500000`
and a cross-symbol range of exactly `[−0.5, −0.5]`.

The consequence is not a cost. **It is a wrong answer**: 89.6 % of trades keep their exit and move
by exactly 0.000000, while **4.08 % change exit reason and carry 96.5 % of the entire delta**,
one-directionally. **736 of 7,552 targets did not happen.** No cost model can undo that; a cost
model subtracts a level, it cannot un-book a target.

And the pattern is explained entirely by one ratio: **spread-over-risk**. The five worst sleeves
are the five with the widest spread relative to their own stop; the five with `s/d < 0.01` are
unchanged to four decimals. **`sub_xvol_pullback` and `energy_agri` — the two armed sleeves
carrying the confidence weight — move by 0.1 % and have zero exit-reason changes**, for exactly the
same reason that the tight-stop families die.

The same defect class produced four of the programme's most-quoted results as pure artifacts:
`structural_distance_extreme`'s **15-window streak across three independent harnesses**; the
tightest-stop decile's apparent edge (which was the whole *"trade tighter so the edge is a bigger
fraction of R"* argument, now sign-inverted); the discovery swarm's **24-of-24 gross-positive**
table; and the three-sealed-month result that is the family's last standing positive claim.

**The general lesson, and it is worth pinning:** the programme repeatedly found effects whose size
was **smaller than the systematic error of the instrument that found them** — +0.024 to
+0.038 R/fill against a constant-sign bias of −0.070 to −0.141. Wave 19 said it itself: *"Every
surviving positive number in this wave is between 2.4 and 6.1 times smaller than the instrument's
own measured, constant-sign error."*

**But note the honest half, because it changes the prescription.** *The NET numbers survived.* The
estate charges a cash spread term as a cost, which approximately accounts for the same physical
fact — so the estate's published **net** was too **harsh** (−0.174858 → −0.123124 R/trade, **+0.052
in our favour**), and on the armed four **three of the four go up**. **Both published numbers were
wrong, in opposite directions.** And crucially, **paired differences survive the correction**: a
comparison between two exit contracts on the same rows cancels whatever bias is common to both, at
a measured ratio of **25.7×**. That is why the frontier work in §4 is still worth money and the
level claims are not.

**Three instrument repairs landed after most of these numbers were published** — r1's quote side,
M4-1's holding time (**still unrepaired**), and p2's missing side control. **Any revival must
restate its baseline on the corrected walker before quoting the original delta.**

### 5.2 The multiplicity bill has no owner, and the estate's own research inflates it

The estate judges candidates at BH q against a declared family at α = 0.10. The standard is correct
and owner-ratified. But it produced a structural trap nobody was assigned to solve:

- AD's frontier: **25 of 25 best cells fail on `significance` alone.**
- CS's breaker: *"the only failed predicate is significance"* — raw p 0.0026 against q 0.1534.
- `mx_btcusd`: cleared α raw at 0.0064 and failed at **q 1.0 against 276 looks**, then admitted
  only after the family was corrected **69 → 32** for double-counting.
- AF's breadth: **0 of 30 families and 0 of 246 members**, best raw p 0.1204.
- AH's entry hour: **0 of 72 arms**, best p 0.380. AM's grid: **726 declared looks**.
- AU's D1 ladder: **0 of 352 arms.**
- AY's spread floor: **0 of 108 gate runs** — at a self-declared family of **514**.

And the decisive line: **at m ≤ 16 the two best sleeves in the book both ADMIT at α 0.10; at
m ≥ 17 neither does. The estate declared 32 and now bills 59 — a bill that grew 84 % in 72 hours
after the ratchet was ratified, and nothing prices that at the moment a look is taken.**

Every one of these routes to the same prescription — **pool the mechanism across a genuinely
declared family, or go through the book-level diversifier door** — and **that decision has never
been taken.** AD routed it to AF; AF ran breadth and refuted it as *diversification* while leaving
the *accounting* question open; CS named `BREADTH` in its own repair queue and stopped; the sleeve
forensic wrote the three specific declaration merges that would do it, needing **no code and no
data**, and nobody executed them.

**This is not a case for weakening the gate.** It is a case for noticing that a programme
generating ~40 frontier improvements per wave against a monotonically growing family bill will
admit zero of them forever, and that **the family declaration — not the improvements — is the
object that needs work.**

### 5.3 Attrition is a quarter of the output and it has a specific, fixable shape

Every attrition row in §4 shares a signature: **it was found by a session commissioned to answer a
different question.** AD was commissioned to test carry and found the exit frontier. AF was
commissioned to run breadth and found two coherent families. The discovery swarm was commissioned
to explain a loss and found four repairs. The post-mortem was commissioned to autopsy April and
found a geometry surface. CE was commissioned to package an activation and found that the lever's
real home is a cohort nobody armed.

**The estate has excellent machinery for answering the question it was asked and no machinery at
all for banking the answers it was not asked for.** `IMPLEMENTATION_STATE.md` is a magnificent
record of *what was measured*; there has never been a register of *what was measured positive and
not yet spent*. Two partial registers exist and were built for other purposes
(`SUPERSEDED_CLAIMS_V1.json`, `WAVE20_SUPERSESSION_REGISTER.md`) — both record what was **struck**,
neither records what was **left**.

There is a sharper version of the same failure: **the funnel V1 rule's two untouched decision days
(2025-10-30, 2025-11-06) were opened, consumed, converted into training rows, and no verdict for
them was ever published anywhere.** That is virgin data — the scarcest resource the programme has —
spent for nothing recoverable.

### 5.4 The sample size is the binding constraint, and the programme keeps proving it

Strip everything else away and one number recurs:

- **BAR-2, the honest-statistics pass bar, would not have passed even February** — *"a single
  ~20-day month at this trade rate rarely clears a 95 % day-resample bar."*
- The 507 trades the broad system took are **net-positive at p(≤0) = 0.20**; the 464-trade roster's
  deficit is **2.5× smaller than its own standard error**, and resolving it needs **14.4 years**.
- `energy_agri`'s best exit cell fails on **n = 67 over 3 folds**.
- AF's best family is **6 members at p 0.1204**.
- `sub_xvol_pullback`'s own 60-fill evidence floor is **193.5 months** away; `crypto`'s is 46.7.
- The armed book fires **~7 book-days/month in the window that selected it and 1.81 on the full
  136 months, with 61 zero months.**

**The programme is not short of ideas or of positive point estimates. It is short of trades.** Every
structural fix in §4 — pooling to a declared family, the forward shadow, the accumulation screen,
the slow grid — is at bottom an attempt to buy sample. That is the correct diagnosis and it should
be the organising one.

### 5.5 What is genuinely good, and must not be lost in the accounting

Four things this programme built are unambiguously working, and three of them are the reason the
losses above are *known* rather than *suffered*:

1. **The prereg discipline.** It took the LSR-scoped arming off the table **before money did**, at
   a measured **−10.4 R** of avoided live loss, on the owner's own ratified bar. It also caught the
   February NOT_EVALUABLE run **before a single February row reached the model** — the discipline
   held at exactly the moment a weaker process would have laundered a flat-cost result into a PASS.
2. **The self-refutation habit.** Nearly every artifact in this ledger was found by the estate
   itself, usually by the lane with most to lose: AR refuted its own +1.119 pp headline; the
   post-mortem refuted its own vol and trend hypotheses and its own occupancy story; Phase 0 killed
   its own author's inversion thesis within hours and published the scoreboard against its own
   prediction list; the discovery swarm's own gate-check refuted the "gates are strangling us"
   theory; AN withdrew its own τ-instrument verdict on its own placebo.
3. **The instrument, now.** Broker-true costs at **0.000535 R** against a shipped model's 0.0591 R;
   a measured clock validated 54/54; an artifact-bound slippage authority that fails closed; a suite
   that went from 639 standing failures to 67; a quote-side walker with 27 hand-computed tests; a
   lane that runs a four-arm month in **3 hours instead of 16.5**. **The estate can now measure an
   edge it could not have measured six months ago** — which is precisely why so much of what it
   measured six months ago did not survive.
4. **The one measurement that separates the sleeves from the broad family, and it is the estate's
   most valuable single fact.** On the accumulation screen — pre-economic, costing no multiplicity
   and no held-out month — the live sleeves score **P(growth ≥ 10×) = 0.629** and clear their own
   toll by 2.36×–11.46×; the broad family scores **0.0073** and is 7.4× short at the *top* of its
   own interval. On the signal-vs-toll screen the four sleeves trading real money read **3.58×–8.51×
   with nothing else in the estate above 2.49×**. **The book Borhen is running is, on the estate's
   own cleanest discriminator, the right family.** What it lacks is sample and an unbent ruler —
   not an idea.

---

## 6. THE SIX THINGS THAT FOLLOW

1. **Re-walk the W7 recost caches on the corrected instrument.** Every book economic the owner has
   ever seen — 5.46 %/month, `p_pass` 0.9172, 4.501 %, 6.120 % — comes from caches built by the same
   bar walk on the same BID archive, and **wave 20 did not touch them.** One session, no new data.
   *This is the only item in this document that changes what the owner believes about money
   currently at risk.*
2. **Adjudicate the cost convention once.** Charging `cost_r`'s spread on top of a corrected walk
   double-counts one physical fact. It is worth **+0.052 R/trade** on the estate and **17.87 points
   of two-phase `p_pass`** on FTMO — five times the size of the repair it accounts for. Both arms
   are published; nobody has picked.
3. **Take the family-pool decision that AD, AF, CS and the sleeve forensic each routed and none
   took.** The three specific declaration merges are already written and need **no code and no
   data**. Until it is taken, every frontier improvement the estate generates will fail on
   `significance` and be filed — the mechanism converting measured economics into paper at ~40 per
   wave.
4. **Fix M4-1 before quoting any frontier number again.** Seven sites consume trading-time hours as
   wall-clock hours, under-counting swap nights by **34.8–93.0 %** on ten sleeves. **AD's 1,631-cell
   frontier and AH's entry-hour lever both consume it.** One line per site. No new data.
5. **Open a standing bank for unspent positives, and make entering it a session's exit condition.**
   The ~50 attrition rows exist because there has never been a place to put a positive result that
   was not the answer to the session's question. This file is that place until something better
   exists — and ranks 3, 4, 8 and 11 of §4 are together cheaper than one sealed window.
6. **Protect the last virgin data.** **March 2026 is the only funnel-virgin, estate-unread window
   left**, and three of the four 2025 windows the V2 commission named as *"the program's validation
   currency — spend nothing on them"* **were already spent by wave 19, and the fourth was never
   restricted at all.** The programme has repeatedly discovered its held-out set was already gone
   *after* planning around it. Before the next prereg is written, someone should establish — from
   the registries, not from memory — exactly what is left.

---

*Lane D, wave-21 swarm. Sources cited inline as `file` / `§section` against `origin/main`
`9dbf79368`. Machine-readable census and the per-finding index: `swarm/lane_d_receipts/`.*
