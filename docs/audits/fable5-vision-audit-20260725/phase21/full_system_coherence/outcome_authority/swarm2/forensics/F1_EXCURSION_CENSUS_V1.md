# F1 — the excursion census: what actually happens to every trade

**Commission:** owner swarm, forensic lane 1, 2026-08-12. *"All the information about the candidate,
the maximum it reached, what level it went to, and where did it come back to, and why did it come
back. Like an analysis of each trade and each candidate of what happened."*

**Scope discipline.** Measurement only. No broker, no VPS, no config byte, no `src/` edit, no
decision-contract-bound file, no git write. Every number is recomputed on this machine from the
sealed candidate corpora and the true-UTC M1 archive.

**Population: 146,736 filled trades — every fill in all five sealed-read 2026 months** (Feb, Apr,
May, Jun, Jul), 100 trading days, 24 symbols, 10 origin families. This is the **funnel candidate
corpus**, not the armed sleeve estate. §11 states that boundary precisely.

**Deliverable:** `f1_excursion/F1_TRADE_EXCURSION_CENSUS_V1.parquet` — 146,736 rows × 155 columns,
one row per filled trade, schema in §12. Receipts: `f1_excursion/` (4 scripts, 2 JSON aggregates,
5 skip ledgers).

---

## 0. The answer in eight lines

| question | answer |
|---|---|
| **Do losers reach 1.8R first?** | **No. 1.95 % of them.** Of 78,207 stopped-out trades, the share that ever traded 1.8 R in profit before reversing is **1.95 %** (2.26 % in the declared-entry frame). At 1.0 R it is 17.82 %. At 0.5 R, 42.05 %. **The system is not picking correct directions and losing them at the exit.** |
| **Then where do losers die?** | **At the entry.** The median stopped-out trade's best moment is **1 minute after the fill** (mean 6.2 min) at **+0.42 R**, and it is already at **−0.153 R by the first decile of its life**. It never went. |
| **Is 41 % reachable?** | **No, at any target from 0.5 R to 3.0 R.** The measured hit rate is below the break-even hit rate at **every** level, by 15.2 pp at 0.5 R narrowing to 4.8 pp at 3.0 R. The shipped 2 R cell is 20.95 % achieved against 27.43 % required — **6.48 pp short on all fills, 8.73 pp on barrier-resolved trades.** That 8.73 is the owner's "nine points", now measured. |
| **Can a longer clock buy the hit rate?** | **It buys it and the bill rises faster.** At a 24-hour horizon the 2 R hit rate goes **20.95 % → 30.61 %** — and the break-even goes **27.43 % → 36.91 %**. The gap closes by 0.18 pp. Hit rate is not a free variable; it is coupled to break-even by the geometry. |
| **How much of +2R is luck?** | **Modest.** 30,737 winners carry a median **0.60 R of headroom** above their stop at their worst point. Tightening the stop 10 % destroys **6.1 %** of the winner population; 20 % destroys **13.1 %**. |
| **Is give-back a recoverable pool?** | **No — it is a hindsight number.** 57,935 trades touched 1 R and surrendered a mean 0.914 R (57,935 × 0.914 R = **$105.9 M at $2,000/R**). But you cannot know ex ante which trades those are: the achievable version is the ladder at T = 1.0, and it is **worse** than the shipped contract (−0.2576 vs −0.2321 R). |
| **What IS the defect, then?** | **Cost against a near-zero directional edge.** Barrier-free, exit-rule-free, on the raw archive basis, the pool drifts **+0.0301 R/trade** over 120 minutes [+0.0116, +0.0486], t = 3.18. All-in cost is **0.2868 R**. **Cost is 9.5× the edge.** |
| **Is the label the problem?** | **The label is lossy — and fixing it does not fix the money.** `terminal_net_r` genuinely discards the path (§1.2), and this census restores it. But the restored path says the discarded information was not concealing an edge: no target level, no horizon, no family, no symbol, no session, no regime is net-positive. |

> **One sentence for the owner: the nine points are not sitting just out of reach — the losing
> trades do not go anywhere near the target before they die, and the reason the system loses is that
> it pays 0.287 R to express a +0.030 R opinion.**

---

## 1. Inventory — what already existed, and why this is not a rebuild

The owner is right that forensic machinery exists. It exists in **fifteen** places. None of them
produced this census, and the reason is consistent: the estate's excursion vocabulary stops at 1 R.

### 1.1 The engine already existed — reuse, not rebuild

| what | where | verdict |
|---|---|---|
| First-touch path replay returning `mfe_r, mae_r, bars_to_mfe, bars_held, exit_reason` per trade | `src/research_infra/walkforward/exits.py:292` (`replay`), `:205-221` (`PathResult`) | **The correct primitive.** Not usable here directly: it walks the sleeve estate's bar contracts, not the funnel's M1 submission/expiry lifecycle. |
| The sealed outcome authority this corpus is labelled by | `src/research_infra/walkforward/quote_side.py:1032` (`resolve_post_submission_m1_lifecycle`) | **Reproduced, not replaced** (§2). |
| Vectorised re-implementation of that resolver, validated to 0.0 max deviation on all 146,736 fills | `swarm2/lane2_receipts/walk.py` | **Reused as the base of this lane's walker.** Lane 2 computed cumulative MFE/MAE per horizon and **never persisted them**; its published excursion figures cover the **41,204 TIME_STOP trades only** and nothing for the stop-outs. |

### 1.2 What the estate already measured, and where each stops

| artifact | population | per-trade? | MFE/MAE? | where it stops |
|---|---|---|---|---|
| `phase6/receipts/AA_ESTATE_TRADES.json.gz` | **22,324** sleeve-estate trades, 32 sleeves, 2000–2026 | **yes** | **yes**, incl. `bars_to_mfe` | The per-trade excursion data has existed since wave 6 and **nothing has ever mined it beyond `frac_mfe_over_1r` / `frac_mfe_over_2r`.** |
| `run_gate(..., diagnose=True)` → `excursion_from_features` | `gate.py:452`, `:457`; `diagnostics.py:394-457` | no | aggregates | Publishes exactly `mean/median_mfe_r`, `mean_mae_r`, `frac_mfe_over_1r`, `frac_mfe_over_2r`, `capture_ratio`, `mean_bars_to_mfe`. `EXCURSION_ALIVE_R = 1.0` (`diagnostics.py:462`) **is why 1 R is the only rung anyone built.** |
| Session AD's exit frontier (1,507 + 124 = **1,631** gated cells, 25 sleeves) | `phase7/receipts/EXIT_FRONTIER_V1*.json` | **no** | per-cell means | `ad_exit_sweep.py:363-378` builds a per-trade row with `mfe_r`/`mae_r` for every resimulated trade in every cell, hands it to the gate, reads back aggregates, and **discards ~1,631 re-derivations of the same per-trade data.** |
| `W0CAP_MECHANISM_V1.json → full_stops` | 15,057 full stops, phase19 **January** pool | no | `mfe_before_stop` | **The only loser near-miss ladder in the repo** — and only 4 rungs (0.25/0.5/1.0/2.0). Not comparable to this one; see §4.3. |
| `L11_ANALYTIC_V1.json → POOL.TARGET_LEVELS` | **24,142**, phase19 January "TAKEABLE" pool | no | one-sided touch | **The closest existing thing to an achievable-hit-rate ladder** — 13 levels with `p_touch`. Wrong population, and one-sided touch rather than joint barrier resolution against a live stop. |
| `swarm/MAGNITUDE_PROGRAM_V1.md` | 190,638 breakout triggers, 24 symbols, D1+H4, 2014–2026 | no | ATR units | Cross-tested in §8.3. |
| `wave4a_digital_twin_historical_microscope.py:852` | live broker loss rows, tens | yes | **yes + `giveback_r`** | The only per-trade give-back in the repo, on live fills, not on any candidate corpus. |
| `scripts/build_vnext_friday_micro_price_action_anatomy.py` → `FRIDAY_MFE_MAE_TIMING_LEDGER.jsonl` | **328 rows, one Friday** (2026-05-28/29) | yes | **yes, tick-level, with timing** | Right schema, right granularity, **wrong denominator by three orders of magnitude.** |
| `scripts/analyze_historical_opportunity_truth_layer.py:786-794` | 205,197 truth-layer rows, 2022–2026 | no | **MFE only, SL rows only** | `_add_path_metrics:683` gates on `outcome not in {NO_ENTRY, SL}`, so TP and TIMEOUT rows get no path metric at all. Its output directory is absent from the tree. |
| `analyze_raw_ohlc_path_ablation_v1_failure_forensics.py`, `..._scaling_v2_confluence.py` | 4,477 / 4,394 events | 20-row casebooks | read `mfe_r` from upstream | **Both input event logs are missing from the tree**, so even the shipped aggregates are not reproducible from this checkout. |

### 1.3 What was genuinely absent

Verified by search (`near_miss|reached_1r|give_back|giveback|target_ladder|achievable|frac_mfe_over|
mfe_ge|_1_8r`):

1. **A loser near-miss ladder above 1.0 R on any population.** The strings `1.8R` and `1.9R` as
   excursion rungs **appear nowhere in the repository.**
2. **Any per-trade excursion artifact on the 2026 five-month corpus.**
3. **A target-level hit-rate table on that corpus** resolved jointly against the live stop.
4. **Give-back and time-to-MFE on candidate trades** (as opposed to live broker fills).

Those four are this lane's contribution. Everything else above is cited, not recomputed.

---

## 2. The instrument, and its fidelity receipt

`f1_excursion/f1_walk.py` extends Lane 2's walker. It reproduces every branch of the sealed
resolver: the entry/exit quote transform (`quote_side.py:385-412`), the first-complete-successor
MARKET fill (`:1281-1289`), the favourable-open / intrabar-touch LIMIT fill (`:1292-1330`), the
invalid-gap guard (`:1344-1356`), the same-bar-both-touch censor, the
`LAST_COMPLETE_PRE_HORIZON_EXECUTABLE_EXIT_SIDE_CLOSE` mark, and — added here — the post-hoc
M1-interval-gap censor (`lane2_receipts/validate.py::sealed_1x`) so the retained population is
**exactly the sealed corpus's own filled rows**.

**Fidelity, all five months:**

| month | sealed filled rows | walker retained | status mismatches | max abs deviation on net R |
|---|---:|---:|---:|---:|
| feb | 28,969 | 28,969 | 0 | **0.0** |
| apr | 28,708 | 28,708 | 0 | **0.0** |
| may | 27,118 | 27,118 | 0 | **0.0** |
| jun | 32,925 | 32,925 | 0 | **0.0** |
| jul | 29,016 | 29,016 | 0 | **0.0** |
| **all** | **146,745** | **146,736** | **0** | **0.0** |

The 9 unretained rows (0.006 %) are Lane 2's known month-boundary artifacts. The walker's own
**T = 2.0 ladder cell reproduces the sealed exit kind on 146,736 of 146,736 trades and the sealed
gross R to 6.5 × 10⁻¹⁴** — the ladder in §9 is therefore the same instrument that produced the
book, with one parameter moved.

### 2.1 Two frames, and they are not the same

Excursion is measured in R **from the actual fill price** (what you could have banked). The estate's
contract levels (−1 R stop, +2 R target) are denominated **from the declared entry**. They differ by
the fill slippage: `R_from_entry = R_from_fill − entry_slip_r`, mean −0.0445 R. **Every near-miss
number below is reported in both frames.** They agree to within 3 pp and never change a conclusion.

### 2.2 How cost is charged, because it is easy to double-count

`deductible_cost_r = expected_slippage_r + swap_cost_r + commission_r`
(`candidate_funnel_analysis.py:164-167`). **Spread is deliberately excluded** — it is already
charged inside gross R by the entry/exit quote transform. Measured on this corpus:

| term | R/trade | $ at $2,000/R | where charged |
|---|---:|---:|---|
| spread | 0.1213 (estate model) / **0.1451** (walker transform, measured) | $242.57 | inside gross |
| slippage | 0.0200 | $40.00 | deductible |
| swap | 0.0406 | $81.21 | deductible |
| commission | 0.0811 | $162.13 | deductible |
| **all-in** | **0.2630 – 0.2868** | **~$526** | |

---

## 3. The population census

| | n | share |
|---|---:|---:|
| **STOP** | 78,207 | 53.30 % |
| **TIME_STOP** | 37,792 | 25.76 % |
| **TARGET** | 30,737 | 20.95 % |
| MARKET fills | 74,244 | 50.60 % |
| LIMIT fills | 72,492 | 49.40 % |

Hit rate **20.95 %** of all fills, **28.21 %** of barrier-resolved (TARGET + STOP) trades.
Mean net **−0.2321 R = −$464.18**; mean gross −0.0904 R; median hold **21 minutes**.

---

## 4. THE NEAR-MISS LADDER — the lane's headline

**Share of each cohort that ever traded through the level before its exit.** Measured strictly
**before the exit bar**, so the number is path-unambiguous: a level reached in the same M1 bar as
the stop cannot be ordered against it and is excluded.

| cohort | n | ≥0.5R | ≥1.0R | ≥1.5R | **≥1.8R** | ≥1.9R |
|---|---:|---:|---:|---:|---:|---:|
| **STOP losers** (fill frame) | 78,207 | 42.05 % | 17.82 % | 6.15 % | **1.95 %** | 1.03 % |
| **STOP losers** (declared-entry frame) | 78,207 | 44.95 % | 19.69 % | 7.05 % | **2.26 %** | 1.08 % |
| all net-negative trades | 94,991 | 41.34 % | 17.14 % | 5.81 % | 1.84 % | 0.96 % |
| TIME_STOP (all) | 37,792 | 64.19 % | 35.62 % | 14.38 % | 5.13 % | 2.59 % |
| all fills | 146,736 | 59.05 % | 37.42 % | 21.78 % | 10.96 % | 6.56 % |

> **This is the single most important number in the lane, and it refutes the hopeful hypothesis.**
> The commission's framing was: *if a large share of −1R losers touched 1.8R first, the system is
> picking correct directions and losing them at exit, which is a completely different problem from
> picking wrong.* **1.95 % is not a large share.** Losers are not near-misses. They are misses.

### 4.1 Where losers actually die

| cohort | median time to MFE | mean time to MFE | median MFE | median hold |
|---|---:|---:|---:|---:|
| **STOP** | **1 min** | 6.2 min | **+0.42 R** | 11 min |
| TARGET | 19 min | 29.0 min | — | 20 min |
| TIME_STOP | 37 min | 45.5 min | — | 119 min |

**The median stopped-out trade's best moment is sixty seconds after the fill.** Combined with §7's
path shape — the STOP cohort is at −0.153 R by the first decile of its life and declines
monotonically to −1.061 — the answer to *"why did it come back?"* is, for the majority of losers,
**it never went.**

### 4.2 The 1.8 R cohort, for completeness

30,140 trades reached 1.8 R at some point (20.54 % of fills). **88.15 % of them are winners**
(26,567), 6.76 % time-stopped (2,038), and only **5.09 % stopped out (1,535 — 1,523 of them
path-unambiguously).** That is 1.95 % of the stop population, and those ~1,500 trades out of 78,207
are the entire population the "picking the right direction, losing it at the exit" story would have
to live in.

### 4.3 Reconciliation against the one existing near-miss fragment

`W0CAP_MECHANISM_V1.json → full_stops` (n = 15,057, phase19 January pool) reports
0.25R **34.69 %** / 0.5R **21.04 %** / 1.0R **8.19 %** / 2.0R **0.39 %**. On the closest comparable
slice of this corpus (`gross_r ≤ −1.0`, n = 60,488) the same rungs are
**68.05 % / 46.85 % / 19.98 % / 0.00 %** — roughly 2×.

**They are not comparable, and the evidence is in W0CAP's own file.** Its `mfe_before_stop` has
**mean −1.814 R and min −26.33 R**, and its fill class is **49.6 % gap** (7,464 of 15,057). Its
reference price is one the market gapped away from. The sealed resolver used here removes exactly
that population via `CENSORED_INVALID_GAP_THROUGH_SL_OR_TP`, and this corpus's comparable slice has
a gap-fill share of **0.0 %**. The two ladders measure different objects; neither is wrong.

---

## 5. Winner fragility — how much of +2R is luck

30,737 winners. `mae_headroom_r` = how much room the trade's worst point left above its stop.

| statistic | value |
|---|---:|
| mean headroom | 0.610 R |
| median headroom | 0.602 R |
| p25 headroom | 0.347 R |

**The stop-tightening kill curve** — the share of the +2 R population destroyed by moving the stop
X R tighter:

| tighten by | winners destroyed |
|---:|---:|
| 0.05 R (5 %) | 3.02 % |
| 0.10 R (10 %) | **6.12 %** |
| 0.20 R (20 %) | **13.07 %** |
| 0.30 R | 21.08 % |
| 0.50 R (half) | 39.03 % |

**Verdict: the winner population is not fragile.** A 10 % tighter stop costs 6 % of winners. Most
winners endure a real drawdown first — 76.5 % go beyond −0.25 R and 45.7 % beyond −0.5 R before
their peak — but they are not scraping the stop. This is the mirror image of §4: winners are not
lucky and losers are not unlucky.

---

## 6. Give-back — real, large, and not recoverable

| MFE reached | n | share of fills | mean give-back | outcome mix |
|---|---:|---:|---:|---|
| ≥ 0.5 R | 88,311 | 60.2 % | 1.0465 R | 37.5 % STOP / 34.7 % TARGET / 27.8 % TIME |
| **≥ 1.0 R** | **57,935** | **39.5 %** | **0.9143 R** | 52.1 % TARGET / 24.3 % STOP / 23.6 % TIME |
| ≥ 1.5 R | 39,284 | 26.8 % | 0.6789 R | 73.3 % TARGET |
| ≥ 1.8 R | 30,140 | 20.5 % | 0.4881 R | 88.1 % TARGET |

Total give-back on the ≥1 R cohort: **52,971 R = $105.9 M at $2,000/R.**

> **That number is hindsight and must be labelled as such.** The cohort that touched 1 R already
> earns **+0.758 R** net. Banking exactly 1 R on each of them would earn **+0.845 R** — **+0.086 R**,
> and only because you were told in advance which trades they were. The *achievable* version of
> "exit at 1 R" is the ladder cell at T = 1.0 applied to all fills, and it earns **−0.2576 R**,
> which is **worse** than the shipped contract. Give-back is a description of where P&L sits, not a
> pool anyone can harvest.

---

## 7. Path shape — the trajectory of every cohort

Mean unrealised R at each decile of the holding period:

| cohort | n | p10 | p20 | p30 | p40 | p50 | p60 | p70 | p80 | p90 | p100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 146,736 | −0.040 | 0.003 | 0.027 | 0.044 | 0.048 | 0.025 | 0.020 | −0.004 | −0.037 | −0.101 |
| **TARGET** | 30,737 | 0.166 | 0.291 | 0.416 | 0.499 | 0.595 | 0.723 | 0.856 | 1.025 | 1.287 | 1.922 |
| **STOP** | 78,207 | **−0.153** | −0.150 | −0.174 | −0.191 | −0.232 | −0.335 | −0.404 | −0.521 | −0.691 | −1.061 |
| **TIME_STOP** | 37,792 | 0.027 | 0.086 | 0.127 | 0.159 | 0.183 | 0.201 | 0.218 | 0.228 | 0.238 | 0.238 |

Three shapes, and each is a different failure:

* **TARGET** rises monotonically from the first decile. Winners work immediately.
* **STOP** is negative at the first decile and never recovers. **Losers never work.**
* **TIME_STOP** rises to +0.24 R by the 60th percentile of its life and then **flatlines**. These
  trades are right, then stall. They are the only cohort where the exit clock is the binding
  constraint — and Lane 2 already measured that letting them run costs −0.0187 R/trade.

**The pooled path is the most damning line in the table**: the average trade peaks at +0.048 R at
mid-life and ends at −0.101 R. The pool's entire favourable travel is smaller than one leg of its
own spread.

### 7.1 An ordering statistic I had to discard

`mae_before_mfe` reads 98.4 % for winners. **That is a construction artifact, and the mechanism is
measured, not assumed:** for TARGET exits `mfe_bar_idx == exit_idx` in **30,737 of 30,737** cases
(100.0 %), and for STOP exits `mae_bar_idx == exit_idx` in **78,207 of 78,207** (100.0 %). The
running extremum is pinned to the exit bar by the barrier that caused the exit, so ordering carries
no information for those cohorts. It is informative **only for TIME_STOP**, where
`mfe_bar_idx == exit_idx` just 7.37 % of the time — and there, **61.8 %** saw their worst point
before their best.

Separately: `mae_r ≥ 0` occurs in **0 of 146,736** trades. Over a 21-minute median hold, price always
trades below the fill at some point. That is measured, not a spread artifact — `mae_bar_idx == 0` in
only 14.74 % of trades.

---

## 8. MFE conditional on outcome, and the non-circular measurement

### 8.1 The circular version, reported and labelled

| cohort | mean MFE @15min | mean MFE @30min | mean MFE @120min (barrier-free) |
|---|---:|---:|---:|
| TARGET | 1.900 | 2.700 | 4.445 |
| STOP | 0.656 | 0.928 | 1.776 |
| TIME_STOP | 0.456 | 0.638 | 0.817 |

AUC separating winners from stop-losers: 0.811 (15 min), 0.851 (30 min), 0.860 (full window).

> **Do not read those AUCs as skill.** A TARGET trade has MFE ≥ 2 R **by construction**, so this is
> largely a restatement of the outcome, not a prediction of it. The ex-ante separability question
> belongs to B1, which measured that the estate's own scorer does **not** order this pool
> (rank-1 −0.0525 R, breadth +0.0235 at t = 0.32).

### 8.2 The non-circular version — direction and spread separated by measurement

The barrier-free mark at the sealed 120-minute horizon: where price sat at the horizon relative to
the fill, **with no exit rule at all**. Reported on both quote bases, because the walker's own
transform offsets are stored per trade (`entry_off_r`, `exit_off_r`) so the restatement is exact
rather than inferred.

| basis | mean R/trade | t | CI95 |
|---|---:|---:|---|
| **raw archive basis** (no spread, no exit rule) | **+0.0301** | **3.18** | [+0.0116, +0.0486] |
| traded quote basis (buy ask, sell bid) | −0.1150 | −12.20 | [−0.1335, −0.0966] |
| difference = the transform | 0.1451 | | entry 0.0579 + exit 0.0872 |

**This independently reproduces Lane 2's directional edge (+0.0282 [+0.0098, +0.0462]) from a
different instrument** — a horizon mark versus a driftless barrier walk — to within 0.002 R.

> **The pool has a real, statistically solid, and economically irrelevant directional edge of
> +0.030 R/trade. It pays 0.287 R to express it. Cost is 9.5× the edge.**

### 8.3 Cross-test of `MAGNITUDE_PROGRAM_V1`'s conclusion — it generalises, and harder

`swarm/MAGNITUDE_PROGRAM_V1.md` found that a Donchian breakout raises MFE ~16 % **and** MAE ~15 %
on its best row, improving the ratio by 1.3 %, and concluded *"magnitude without direction expands
both tails."* Tested inside this corpus across **164 (family × symbol) cells with n ≥ 150**:

| statistic | value |
|---|---:|
| **corr(mean MFE, mean \|MAE\|) across cells** | **+0.963** |
| pooled MFE / \|MAE\| ratio | **0.904** |
| cells with ratio > 1 | 19.5 % |
| **corr(mean MFE level, mean net R)** | **−0.613** |
| corr(MFE/\|MAE\| ratio, mean net R) | +0.459 |

**The conclusion holds and is stronger here than where it was found.** At r = +0.963, favourable and
adverse travel in this pool are very nearly the same variable, and the pool travels **further
against than for** (ratio 0.904). The −0.613 correlation is the actionable part: **selecting
candidates for large excursion is actively counterproductive** — the cells that move most lose most.
Only the *ratio* correlates positively with money, and only 19.5 % of cells clear 1.0.

---

## 9. THE ACHIEVABLE HIT RATE — the second headline

The same walker, same fills, same 1 R stop, same clock, with the take-profit moved. The T = 2.0 row
reproduces the shipped book exactly (§2), so this is a controlled one-parameter sweep.

**Sealed 120-minute clock:**

| target | n | **hit rate** | **break-even needed** | **gap** | stop | time | mean net R | mean net $ |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.50 R | 122,424 | 54.77 % | 69.93 % | **−15.16 pp** | 34.98 % | 10.25 % | −0.2798 | −$560 |
| 0.75 R | 133,044 | 45.25 % | 57.84 % | −12.59 pp | 40.92 % | 13.83 % | −0.2675 | −$535 |
| 1.00 R | 138,901 | 38.03 % | 48.70 % | −10.67 pp | 45.12 % | 16.85 % | −0.2576 | −$515 |
| 1.25 R | 142,343 | 32.35 % | 41.53 % | −9.18 pp | 48.09 % | 19.56 % | −0.2486 | −$497 |
| 1.50 R | 144,409 | 27.78 % | 35.83 % | −8.05 pp | 50.30 % | 21.93 % | −0.2414 | −$483 |
| 1.75 R | 145,869 | 23.97 % | 31.22 % | −7.25 pp | 52.05 % | 23.98 % | −0.2382 | −$476 |
| **2.00 R (shipped)** | **146,736** | **20.95 %** | **27.43 %** | **−6.48 pp** | 53.30 % | 25.76 % | **−0.2321** | **−$464** |
| 2.50 R | 146,731 | 15.92 % | 21.44 % | −5.52 pp | 55.09 % | 28.99 % | −0.2287 | −$457 |
| 3.00 R | 146,735 | 12.36 % | 17.20 % | **−4.84 pp** | 56.23 % | 31.41 % | **−0.2271** | −$454 |

**On the barrier-resolved basis the shipped cell is 28.21 % achieved against 36.94 % required — a
shortfall of 8.73 pp.** That is the owner's "nine points", measured on 146,736 trades.

**24-hour horizon**, same sweep — the test of whether time buys the hit rate:

| target | hit rate | break-even | gap | mean net R |
|---:|---:|---:|---:|---:|
| 1.00 R | 45.73 % | 56.40 % | −10.67 pp | −0.2610 |
| **2.00 R** | **30.61 %** | **36.91 %** | **−6.30 pp** | −0.2344 |
| 3.00 R | 22.18 % | 26.84 % | −4.66 pp | −0.2313 |

> **A 12× longer clock buys 9.66 pp of hit rate at the 2 R target and raises the break-even by
> 9.48 pp. The gap closes by 0.18 pp.** Hit rate is not a free parameter — it is bound to
> break-even by the barrier geometry. This is the cleanest available refutation of "just get the hit
> rate up."

### 9.1 Answering the question as asked: is 41 % reachable?

**A 41 % hit rate is reachable — at a target of 0.897 R** (linear interpolation on the measured
ladder). **But break-even at that target is 52.46 %**, so arriving at 41 % there loses *more* money
than the shipped contract does (−0.2600 R interpolated, against −0.2321 at 2 R). **There is no target
level at
which the achievable hit rate meets its own break-even.** The best cell in the whole sweep is
T = 3.0 R at **−0.2271 R/trade**; the worst is T = 0.5 R at **−0.2798**. Across a 6× span of target
the total moves **0.0527 R/trade** — the target level is worth almost nothing.

### 9.2 Same-bar ambiguity, bracketed

At low targets, more bars touch both barriers, and the sealed convention censors them — which shrinks
`n` non-randomly and would flatter a tight target if read alone. Drop share: **16.57 % at T = 0.5**,
9.33 % at 0.75, 5.34 % at 1.0, 1.59 % at 1.5, **0.00 % at T ≥ 2.0**. Both bracketing arms are in
`F1_CENSUS.json`:

| target | pessimistic (ambiguity → STOP) | sealed | optimistic (ambiguity → TARGET) |
|---:|---:|---:|---:|
| 0.50 R | −0.4305 | −0.2798 | −0.1820 |
| 1.00 R | −0.3084 | −0.2576 | −0.2016 |
| 1.50 R | −0.2570 | −0.2414 | −0.2174 |
| 2.00 R | −0.2321 | −0.2321 | −0.2321 |

**The arms converge from T = 1.5 upward and diverge badly below 1.0.** Read the ladder only at
T ≥ 1.5; below that the censoring is doing too much of the work. **Even the fully optimistic arm at
every target is negative.**

### 9.3 Per family — nobody's target is wrong

| family | n | best T | net @ best T | net @ 2 R | gain |
|---|---:|---:|---:|---:|---:|
| `current_fvg_fill` | 60,907 | 2.50 | −0.1950 | −0.1976 | +0.0026 |
| `liquidity_sweep_reclaim` | 23,047 | 3.00 | −0.2804 | −0.2916 | +0.0112 |
| `displacement_continuation` | 20,736 | 3.00 | −0.1326 | −0.1365 | +0.0040 |
| `structural_distance_extreme` | 11,118 | 3.00 | −0.5430 | −0.5688 | **+0.0257** |
| `cross_asset_lead_lag` | 10,919 | 2.00 | −0.3240 | −0.3240 | +0.0000 |
| `current_ob_retest` | 7,603 | 3.00 | −0.1285 | −0.1347 | +0.0062 |
| `session_open_range_break` | 4,784 | 3.00 | −0.0929 | −0.0976 | +0.0047 |
| `current_breaker_re_entry` | 3,982 | 1.50 | −0.1861 | −0.1914 | +0.0053 |
| `volatility_compression_expansion` | 2,418 | 3.00 | −0.1123 | −0.1142 | +0.0019 |
| `regime_transition_break` | 1,222 | 1.00 | −0.0551 | −0.0640 | +0.0088 |

**Best available per-family retune: +0.0257 R/trade, on the worst family. Median gain +0.0050 R.
Nothing crosses zero.** Re-targeting is not a lever anywhere in this pool.

---

## 10. Cross-tabs

### 10.1 By family

| family | n | hit | stop | time | **net R** | mean MFE | mean MAE | losers ≥1.8R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `current_fvg_fill` | 60,907 | 23.93 % | 57.81 % | 18.27 % | −0.1976 | 1.129 | −0.966 | 3.03 % |
| `liquidity_sweep_reclaim` | 23,047 | 22.18 % | 58.71 % | 19.11 % | −0.2916 | 0.842 | −0.963 | 1.10 % |
| `displacement_continuation` | 20,736 | 12.37 % | 40.21 % | 47.42 % | −0.1365 | 0.765 | −0.765 | 0.52 % |
| `structural_distance_extreme` | 11,118 | 30.97 % | 68.04 % | 0.99 % | **−0.5688** | 0.781 | −1.228 | 1.49 % |
| `cross_asset_lead_lag` | 10,919 | 28.33 % | 62.66 % | 9.01 % | −0.3240 | 0.899 | −1.027 | 1.21 % |
| `current_ob_retest` | 7,603 | 11.77 % | 39.93 % | 48.30 % | −0.1347 | 0.838 | −0.768 | 0.72 % |
| `session_open_range_break` | 4,784 | 7.04 % | 28.47 % | 64.49 % | −0.0976 | 0.686 | −0.657 | 0.15 % |
| `current_breaker_re_entry` | 3,982 | 16.80 % | 47.89 % | 35.31 % | −0.1914 | 0.940 | −0.825 | 2.31 % |
| `volatility_compression_expansion` | 2,418 | 1.32 % | 11.62 % | 87.06 % | −0.1142 | 0.343 | −0.439 | 0.00 % |
| `regime_transition_break` | 1,222 | 1.55 % | 11.05 % | 87.40 % | **−0.0640** | 0.437 | −0.451 | 0.00 % |

**Note the inversion that matters**: `structural_distance_extreme` has the **highest hit rate**
(30.97 %) and the **worst net R** (−0.5688); `regime_transition_break` has the **lowest hit rate**
(1.55 %) and the **best net R** (−0.0640). Hit rate and profitability are negatively related across
families here, because a high hit rate is bought with a geometry that also stops out more.

### 10.2 Other axes — the uniformity is the finding

| axis | best cell | worst cell | any positive? |
|---|---|---|---|
| **symbol** (24) | GER40 −0.0643 | EURGBP −0.4616 | **0 of 24** |
| **session** (27, all of them) | `moonshot_h11_12` −0.1411 | `moonshot_h20_21` −0.8955 | **0 of 27** |
| **UTC hour** (24) | — | — | **0 of 24** |
| **weekday** (5) | — | — | **0 of 5** |
| **month** (5) | feb −0.1925 | jul −0.2663 | **0 of 5** |
| **side** (2) | LONG −0.2174 | SHORT −0.2463 | **0 of 2** |
| **order type** (2) | LIMIT −0.1907 | MARKET −0.2725 | **0 of 2** |
| **family** (10) | `regime_transition_break` −0.0640 | `structural_distance_extreme` −0.5688 | **0 of 10** |

### 10.3 Volatility regime

| axis | bucket | n | hit | net R | mean MFE |
|---|---|---:|---:|---:|---:|
| `atr14/atr50` | low / mid / **high** | 48,912 ea | 20.68 / 21.41 / 20.76 % | −0.2571 / −0.2523 / **−0.1869** | 0.884 / 0.961 / 0.963 |
| `vol 8/48` | low / mid / **high** | 48,912 ea | 21.45 / 21.23 / 20.15 % | −0.2639 / −0.2356 / **−0.1968** | 0.914 / 0.954 / 0.940 |
| **`risk/atr`** | **low** / mid / **high** | 48,912 ea | **29.38** / 23.08 / **10.38 %** | **−0.3407** / −0.2232 / **−0.1324** | 1.095 / 0.989 / 0.723 |

**`risk_over_atr` is by far the most informative axis, and it points the same way as everything
else.** Tight stops relative to volatility buy a 29.4 % hit rate and the **worst** net R; wide stops
give a 10.4 % hit rate and the **best**. This is Lane 2's stop-width lever visible in the
cross-section — and it confirms Lane 2's ceiling: the best regime tertile is still −0.1324 R.

### 10.4 The twelve positive cells, flagged not recommended

Of 164 (family × symbol) cells with n ≥ 150, **12 are net-positive.** The top four:
`current_breaker_re_entry × GER40` (+0.3443, n = 255), `current_ob_retest × GER40` (+0.1742,
n = 399), `current_ob_retest × AUDJPY` (+0.1354, n = 291), `current_ob_retest × NAS100` (+0.1209,
n = 304). **These are 12 winners out of 164 looks with no multiplicity correction, in a pool whose
mean cell is −0.2575.** At a 164-look family that is close to what noise produces. They are recorded
as leads for a lane that can gate them properly (`F1_SUPP.json → magnitude_cross_test.cells`); they
are **not** a recommendation, and three of the four sit on one symbol, which is the concentration
signature the estate has been burned by before.

---

## 11. Dollars

**Basis: 1 R = 2.00 % of the $100,000 account = $2,000** (`config/agent_config.yaml:23`
`risk_per_trade_pct: 2.0`; `:1363` `governor_static_initial_balance: 100000.0`). Half-Kelly
effective ~1.73 % = $1,730 (`:1316-1322`). Multiply/divide freely — everything below is linear.

| cohort | n | mean net R | **mean net $** | total net $ |
|---|---:|---:|---:|---:|
| **all fills** | 146,736 | −0.2321 | **−$464** | −$68.1 M |
| TARGET | 30,737 | +1.7034 | **+$3,407** | +$104.7 M |
| STOP | 78,207 | −1.1799 | **−$2,360** | −$184.6 M |
| TIME_STOP | 37,792 | +0.1551 | **+$310** | +$11.7 M |

**Cost per trade, in dollars: $526 all-in** — spread $243, commission $162, swap $81, slippage $40.
Against a measured directional edge of +0.0301 R = **+$60**. **The system pays $526 to place a $60
bet.** That one line is the whole census.

> **Framing the totals honestly.** 146,736 fills over 100 trading days is 1,467 trades/day; nobody
> trades that, and no account survives it. The **per-trade** dollars are the meaningful figures. A
> live book takes ~7 book-days/month (CLAUDE.md §4). And this is the **funnel candidate corpus, not
> the armed sleeve estate** — the four armed sleeves are a different population priced elsewhere.
> Nothing here restates any live economic figure.

---

## 12. The artifact

`f1_excursion/F1_TRADE_EXCURSION_CENSUS_V1.parquet` — **146,736 rows × 155 columns**, 58.6 MB zstd-9.
sha256 in `F1_ARTIFACT_MANIFEST.json`. One row per filled trade. Column groups:

| group | columns | notes |
|---|---|---|
| **identity** | `k`, `month`, `trading_day`, `symbol`, `family`, `order_type`, `side`, `session`, `utc_hour`, `weekday` | `k` is the occurrence key with the constant `candidate_occurrence_` prefix stripped — joins to the sealed corpus by `removeprefix`, matching `candidate_funnel_analysis.py:200-202` |
| **contract** | `entry_price`, `stop_price`, `target_price`, `fill_price`, `risk_price`, `stop_r`, `target_r`, `entry_slip_r`, `fill_at_open`, `sub_min`, `fill_min`, `horizon_min`, `fill_delay_min`, `first_gap_min`, `gapped`, `risk_over_atr`, `atr14_over_atr50`, `vol_8_over_48`, `risk_frac_entry` | `*_r` are R from the **fill**; `entry_slip_r > 0` means filled better than declared entry |
| **outcome** | `sealed_status`, `exit_kind`, `gross_r`, `cost_r`, `net_r`, `sealed_net_r`, `spread_r`, `slippage_r`, `swap_r`, `commission_r`, `exit_min`, `hold_min`, `exit_idx` | `net_r == sealed_net_r` to 0.0 on all 146,736 rows |
| **excursion** | `mfe_r`, `mae_r`, `t_mfe_min`, `t_mae_min`, `mfe_bar_idx`, `mae_bar_idx`, `mae_before_mfe`, `mfe_pre_exit_r`, `mae_pre_exit_r`, `giveback_r`, `mae_headroom_r`, `mfe_headroom_r` | `*_pre_exit_*` exclude the exit bar → path-unambiguous. **Read §7.1 before using `mae_before_mfe`.** |
| **barrier-free** | `mfe_full_r`, `mae_full_r`, `t_mfe_full_min`, `t_mae_full_min`, `close_full_r`, `close_full_raw_r`, `entry_off_r`, `exit_off_r`, `full_gapped`, `mfe{5,15,30,60}_r`, `mae{5,15,30,60}_r`, `mfe_ext_r`, `mae_ext_r`, `ext_bars` | measured **ignoring the exit rule** — the non-circular family. `close_full_raw_r` is the spread-free restatement |
| **near-miss** | `reach_l*` (10), `reachpre_l*` (10) | booleans at 0.25/0.5/0.75/1/1.25/1.5/1.75/1.8/1.9/2.0 R, fill frame. Entry frame = `mfe_r − entry_slip_r` |
| **path shape** | `p10` … `p100` | unrealised R at each decile of the holding period |
| **target ladder** | `t{0p5,0p75,1,1p25,1p5,1p75,2,2p5,3}_{kind,gross,hold}` and `_{kindE,grossE,holdE}` | 9 targets × 2 horizons (sealed 120 min, and 12× = 24 h). `t2_*` reproduces the shipped book exactly |

**Size caveat for whoever commits this.** At 58.6 MB it is well over the 5 MB inline-blob threshold
CLAUDE.md §8 flags (4.8 GB of the tree already sits in 280 such blobs). It should go to LFS or
through the cold-evidence pointer route (`b7_5_cold_evidence.py`), not inline.

---

## 13. Adversarial passes — what I refuted in my own work

1. **The near-miss ladder was in the wrong frame.** MFE is measured from the fill; the −1R/+2R
   contract is denominated from the declared entry. The first draft mixed them, which made
   "reached 2.0 R" read 0.19 % where it should have read 0.00 %. **Both frames are now reported
   throughout;** they differ by ≤ 3 pp and change no conclusion.
2. **I asserted a mechanism I had not measured.** I first attributed `mae_before_mfe = 98.4 %` and
   `mae_r < 0 always` to the entry spread landing MAE on bar 0. **That was wrong**: `mae_bar_idx == 0`
   in only 14.74 % of trades. The real mechanism is the exit barrier pinning the extremum to the
   exit bar (100.0 % for both TARGET and STOP). Corrected in §7.1, with the measurement.
3. **The ladder's low-target cells are censoring-driven and I bracketed them** rather than
   reporting the sealed arm alone (§9.2). Below T = 1.5 the pessimistic and optimistic arms differ
   by up to 0.25 R/trade.
4. **The give-back headline is hindsight** and I priced its achievable counterpart, which is worse
   than the shipped contract (§6).
5. **The winner/loser MFE AUC is largely circular** and is labelled as such (§8.1) rather than
   presented as separability.
6. **The direction-vs-spread split was an inference and is now a measurement** — I re-ran the walker
   to store the transform offsets per trade so `close_full_raw_r` is exact (§8.2).
7. **The 12 positive cells are 12 of 164 unadjusted looks** and are flagged, not recommended (§10.4).
8. **W0CAP's ladder disagrees with mine by 2×** and I traced why rather than ignoring it (§4.3).

**Known limitations, stated.** (a) The 24-hour ladder holds `deductible_cost_r` fixed while swap
scales with holding time — 20.0 % of fills carry nonzero swap, so that arm is **optimistic on cost**;
the sealed-clock ladder is essentially unaffected. (b) The extended arm treats M1 interval gaps as
unobserved time (Lane 2's declared deviation, unavoidable for any horizon crossing a session break);
the sealed 1× arm censors them exactly as the resolver does. (c) Intrabar ordering within one M1 bar
is unknowable, which is precisely what §4's pre-exit-bar convention and §9.2's bracket exist to
bound. (d) Everything is modelled M1 lifecycle, not broker fills.

---

## 14. What this means, and what would confirm it

**The label really is lossy — and restoring it does not find the money.** `terminal_net_r` collapses
a trade that ran to 1.9 R and a trade that died on entry into the same −1, and the ridge trains on
exactly that (`w21_score_feb_market_top_r2.py:308`, `[float(row.get("terminal_net_r") or 0.0) …]`,
which also maps every non-fill to 0.0). The census restores the discarded path in full. **The
restored path shows the discarded information was not hiding an edge**: 1.95 % near-miss, no
profitable target level, no profitable horizon, no profitable family/symbol/session/regime.

**Three things this census says are worth doing, in order:**

1. **Stop looking for the nine points in the exit.** Target level is worth ≤ 0.053 R across a 6×
   span; horizon is worth ≤ 0.0034 R (Lane 2); per-family retuning is worth ≤ 0.026 R. The exit is
   measured, bounded, and small. **Confirmation:** already complete — §9 and Lane 2 §4 agree.
2. **Price the entry, not the exit.** The pool's direction is +0.030 R and its cost is 0.287 R. The
   only two quantities with the right order of magnitude are the **spread** (0.145 R, half the bill)
   and **`risk_over_atr`** (the widest tertile is worth +0.208 R over the tightest, §10.3).
   **Confirmation:** a joint sweep of stop width × entry-cost band on this artifact, gated at the
   ratified rule (`RECORDED`, `CANDIDATE_BOOK_V1`, α = 0.10) — the artifact already carries every
   column that sweep needs.
3. **Test excursion-magnitude selection as a NEGATIVE filter.** corr(MFE level, net R) = **−0.613**
   across 164 cells. If that survives out-of-sample it is a usable ranking signal with the sign
   nobody expected. **Confirmation:** fit on Feb–May, test on Jun–Jul, both already in the artifact
   via the `month` column; the four never-funnel-read 2025 windows stay untouched.

**And one thing not to do.** Do not read §6's $105.9 M of give-back, or §4's 42 % of losers touching
0.5 R, as recoverable. Both are post-fill conditioning — true statements about where P&L sits, false
ones if read as achievable ex ante. The ladder in §9 is the honest counterpart, and it is negative
everywhere.

---

*Receipts: `f1_excursion/` — `f1_walk.py` (walker, fidelity §2), `f1_census.py` (aggregates),
`f1_supp.py` (reconciliation, adversarial, magnitude cross-test, dollars), `f1_artifact.py`
(artifact writer), `F1_CENSUS.json`, `F1_SUPP.json`, `F1_ARTIFACT_MANIFEST.json`,
`f1skips_{feb,apr,may,jun,jul}.json`. Nothing in this lane touched a live path, a broker, the VPS,
a config byte, or a decision-contract-bound file.*
