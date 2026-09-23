# LANE 7 — COST AS THE LEVER

**Wave 21 outcome-authority swarm 2, 2026-08-11.** Receipts: `lane7_receipts/` (8 JSON, 12 scripts).

**Measurement only.** No live path, no config byte, no broker call, no VPS touch, no `src/` edit, no git
write. Confers no arming, sizing, promotion or activation authority.

Everything below carries `n`, an interval, and a named source. Where I refuted my own positive I say so
and leave the refutation in.

---

## 0. HEADLINE

> **The mandate's premise is confirmed to three decimals and its prescription is refuted.** Over
> 146,745 filled candidate occurrences across five sealed months, pre-cost gross is **−0.0188 R/fill**
> and all-in cost is **0.2133 R/fill**: cost is **91.9 %** of the loss. On the frozen rule's own 282
> sealed trades it is starker — **gross +32.04 R, cost 31.09 R, net +0.95 R. Cost consumed 97.0 % of
> everything the rule earned in five months.**
>
> **The recoverable amount is +3.1 R/month at the conservative bound and +3.7 to +5.1 R/month at the
> measured cost-veto floor** — several times the entire five-month net result (+0.954 R) — and it is
> available from an *ex-ante* quantity, so it is arithmetically certain in the
> way alpha is not. On the full candidate pool an ex-ante cost veto takes net from **−0.232 to −0.034
> R/fill, removing 85.3 % of the loss, while pre-cost gross does not degrade** (−0.0188 → +0.0022, CIs
> overlapping) — monotone across all ten cost deciles and stable in all five months under
> leave-one-month-out.
>
> **But no month turns positive, at any rung, and it cannot.** Pre-cost gross at the tightest envelope
> is **+0.00215 ± 0.0206** — statistically zero. Cost reduction drives the loss asymptotically to zero;
> it cannot manufacture a gain that is not there. *Halving a cost whose gross is zero yields zero, not
> profit.* That is the honest form of the mandate's arithmetic.
>
> **MARKET vs LIMIT — the verdict.** The question as posed does not exist in this estate: order type is
> a **perfect partition of `origin_family`**, not an execution choice. LIMIT ≡ the three POI families;
> MARKET ≡ the other seven; **no family emits both.** "Trade only when the top candidate is MARKET" is
> literally "never trade the three POI families." I then built the execution choice that does not
> exist, on 21,684 candidates and 300 M true ticks, and **passive execution is refuted at t = −18 to
> −29**: the spread it saves is **+0.0094 R**; the adverse selection it pays is **−0.0426 R/opportunity**.
> **The trades a resting limit misses are worth +0.627 ± 0.084 R each; the ones it catches are worth
> −0.254 ± 0.016.** Passive execution loses 4.5× what it saves.
>
> **And one instrument defect that moves the sealed record.** The spread model is **hour-flat for the
> cash indices while the tape is not** — UK100 modelled at 0.86–1.12 at *every* hour against a true
> range of 0.67 (h11) to 5.99 (h20). The frozen rule put **26.2 % of its trades in UK100**. Priced from
> the tape, **the sealed five-month record restates from +0.954 R to −6.090 R.** February's PASS
> survives (+14.168 → +14.062); June and July absorb the whole correction.

---

## 1. WHAT WAS MEASURED, AND THE CONTROL THAT LICENSES IT

| instrument | scope |
|---|---|
| candidate pool | 632,934 occurrences, 5 sealed months (`/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz`); 146,745 filled |
| price-bearing walk rows | 81,968 MARKET candidates with entry/stop/target (`/private/tmp/laneG-walk/lg_*.pkl.gz`) |
| tick archive | `/Users/borr/GTOSActive/vps-ticks-20260726/`, **61 files, 300,538,915 rows**, reduced to bid/ask minute OHLC |
| overlap used for the tick experiments | 21,684 MARKET candidates, FTMO, 2026-06-18…07-24 |
| sealed frozen-rule record | 290 selected / **282 resolved** across the three sealed reads |

**Correction to `CLAUDE.md` §4.** The tick export is **61 files / 300,538,915 rows**, not the recorded
"51 files … 263,894,769". The two manifests (`TICKS_MANIFEST.jsonl` V1 = 19 files, `TICKS_MANIFEST_V2.jsonl`
= 32 files) cover 51 of them; **ten files are in the directory and in neither manifest**. The
sha256-verified claim covers the 51, not the 61.

**The control.** I re-walked the MARKET arm from raw ticks with an independent harness
(`lane7_receipts/walk.py`) and compared it to the sealed labeller on the same keys: **98.9 % state
agreement on 19,694 resolved candidates** (labeller gross −0.15366, tick walk −0.16965 — the gap is
exactly the modelled-vs-true spread of §6). Nothing below is a disagreement about the walk.

**The accounting, established by reading rather than assuming.** `candidate_funnel_analysis.py:164-176`:
`net = gross − (expected_slippage_r + swap_cost_r + commission_r)`. **Spread is priced into the walked
path and is never deducted again.** And spread is only *paid* by one arm — proved on stop exits, where
theory is exact:

| arm | n | mean gross at a stop | reads as |
|---|---:|---:|---|
| LIMIT LONG | 20,715 | **−1.00142** | fills at its own level, pays no spread |
| LIMIT SHORT | 19,438 | **−1.00054** | same |
| MARKET LONG | 16,614 | −1.11466 | crosses the spread |
| MARKET SHORT | 21,440 | −0.99002 | crosses, asymmetrically (BID basis) |

LIMIT targets realise **+2.00115 / +2.00150** against a 2R order. So `precost = gross + spread_r` holds
for MARKET and is **wrong for LIMIT**. A first pass that applied it to both produced a pooled pre-cost
gross of +0.0309; the correct figure is **−0.0188**. That correction is carried through everything below.

---

## 2. (A) THE COST DECOMPOSITION

**146,745 fills, five months.** `lane7_receipts/A_COST_DECOMPOSITION_V1.json`.

| quantity | R/fill | CI95 | total R |
|---|---:|---|---:|
| pre-cost gross | **−0.01878** | [−0.0248, −0.0127] | −2,755 |
| all-in cost | **0.21332** | — | 31,303 |
| **net** | **−0.23209** | [−0.2384, −0.2258] | **−34,059** |

| component | R/fill | share of cost | total R |
|---|---:|---:|---:|
| spread (paid, MARKET only) | 0.07164 | 33.6 % | 10,512 |
| **commission** | **0.08108** | **38.0 %** | **11,897** |
| swap | 0.04060 | 19.0 % | 5,958 |
| slippage (flat 0.02) | 0.02000 | 9.4 % | 2,935 |

**Commission is the largest line, and it is an instrument choice, not a market condition.** BTCUSD alone
burns **4,161 R at 0.3984 R/fill**; ETHUSD 2,087 R at 0.2561. Eight symbols pay **zero** commission
(GER40, JP225, NAS100, SPX500, UK100, UKOIL_cash, US30_cash, USOIL_cash).

### 2.1 By family — an 8× cost range that gross does not track

| family | order type | n | cost | pre-cost gross ± CI95 | net | total cost R |
|---|---|---:|---:|---:|---:|---:|
| `structural_distance_extreme` | MARKET | 11,118 | **0.5783** | +0.0095 ± 0.0240 | −0.5688 | 6,429 |
| `cross_asset_lead_lag` | MARKET | 10,919 | 0.3562 | **+0.0322 ± 0.0243** | −0.3240 | 3,889 |
| `liquidity_sweep_reclaim` | MARKET | 23,049 | 0.2888 | −0.0028 ± 0.0158 | −0.2916 | **6,657** |
| `current_fvg_fill` | LIMIT | 60,911 | 0.1501 | −0.0475 ± 0.0101 | −0.1976 | 9,142 |
| `displacement_continuation` | MARKET | 20,737 | 0.1454 | +0.0089 ± 0.0140 | −0.1366 | 3,015 |
| `current_breaker_re_entry` | LIMIT | 3,982 | 0.1392 | −0.0523 ± 0.0354 | −0.1914 | 554 |
| `session_open_range_break` | MARKET | 4,785 | 0.1178 | +0.0202 ± 0.0252 | −0.0977 | 564 |
| `current_ob_retest` | LIMIT | 7,603 | **0.0979** | −0.0368 ± 0.0232 | **−0.1347** | 744 |
| `volatility_compression_expansion` | MARKET | 2,419 | 0.0909 | −0.0234 ± 0.0216 | −0.1142 | 220 |
| `regime_transition_break` | MARKET | 1,222 | **0.0725** | +0.0085 ± 0.0327 | **−0.0640** | 89 |

**Cost varies 8× across families; pre-cost gross varies within its own noise.** That is the whole lever
in one table.

### 2.2 By hour — the 4.3× band, and the hours that are both cheap and positive

MARKET fills only (the arm that pays spread):

| UTC hour | cost | pre-cost gross ± CI95 | net |
|---|---:|---:|---:|
| 07 | 0.2136 | **+0.0576 ± 0.0310** | −0.1559 |
| 06 | 0.2524 | **+0.0467 ± 0.0347** | −0.2056 |
| 10 | 0.2716 | +0.0484 ± 0.0489 | −0.2232 |
| 09 | 0.2355 | +0.0414 ± 0.0413 | −0.1942 |
| 08 | **0.2019** | −0.0135 ± 0.0289 | −0.2154 |
| 14 | 0.2394 | +0.0326 ± 0.0288 | −0.2068 |
| … | | | |
| 19 | 0.5335 | −0.0242 | −0.5577 |
| 20 | 0.6632 | −0.2714 | −0.9346 |
| **21** | **0.9216** | +0.0905 | **−0.8312** |

**Hour 21 UTC costs 4.3× the cheapest hour** (0.9216 vs 0.2019) and its spread alone is 0.7587 R.

### 2.3 Addressable vs structural

| | R/fill | basis |
|---|---:|---|
| **structural** — the minimum spread+commission of the cheapest instrument at its best hour | ~0.036 | decile-0 mean cost, 14,675 fills |
| **addressable** — everything above that | **0.177** | 0.2133 − 0.036 |
| share of total cost that is a *choice* | **83 %** | |

The 83 % is addressable because `cost_r` is a **generation-time field** — it exists in the candidate row
before any outcome. Every restriction below is implementable at decision time.

---

## 3. (B) MARKET vs LIMIT — THE BIGGEST SINGLE QUESTION

`lane7_receipts/B_MARKET_VS_LIMIT_V1.json`.

### 3.1 The question does not exist as posed

| origin_family | order type |
|---|---|
| `current_fvg_fill`, `current_ob_retest`, `current_breaker_re_entry` | **LIMIT** (550,966 candidates) |
| the other seven | **MARKET** (81,968 candidates) |

**The partition is perfect: no family emits both.** So the frozen rule's "trade only when the top
candidate is MARKET, abstain on LIMIT" is not an execution policy — it is a **family exclusion**. You
cannot convert a MARKET candidate to a LIMIT one without changing the generator's entry anchor. That
correction should be carried into any future statement of the rule.

### 3.2 The two arms as they actually stand

| | n filled | fill rate | spread paid | comm+swap+slip | pre-cost gross ± CI95 | **net ± CI95** |
|---|---:|---:|---:|---:|---:|---:|
| MARKET | 74,249 | 0.906 of all | 0.14159 | 0.13940 | **+0.00844** [+0.0002, +0.0167] | **−0.27254** [−0.2811, −0.2640] |
| LIMIT | 72,496 | **0.157 of resolved** | 0.00000 | 0.14401 | **−0.04666** [−0.0557, −0.0376] | **−0.19067** [−0.1998, −0.1815] |

**The rule chose the arm with the higher gross and the much higher cost, and it is the worse arm net by
0.082 R/fill.** LIMIT's non-fill count is **388,912** — 84.3 % of resolved LIMIT candidates never fill.
That is the entire risk of passive execution, and it is already in the data.

### 3.3 How the labeller models LIMIT fills — it says so itself

`src/research_infra/walkforward/quote_side.py:1014` stamps every passive fill
**`MODELLED_FROM_OPTIMISTIC_LIMIT_TOUCH_NOT_QUEUE_OR_BROKER_FILL`**, and
`first_resting_limit_touch` (`:504-534`) documents its own limit: *"the first observed eligibility
event, not an execution: no queue/depth/order-event evidence is present."* A **single correct-side
touch** counts as a fill: no through-trade requirement, no queue priority, no partial fill.

**I priced that optimism from ticks.** Requiring the tape to penetrate the level by one spread instead
of merely touching it moves the k=0 fill rate **0.932 → 0.876** and the conditional gross **−0.245 →
−0.331 R**, i.e. **the touch model is worth +0.087 R/fill of unearned optimism.** *This is measured on
the MARKET families executed passively, not on the real LIMIT families — see §8 for what would settle
it there.*

### 3.4 The true fill statistics, and adverse selection measured directly

21,684 MARKET candidates, true FTMO ticks. A limit rested at the signal-bar close (`k = 0`) — strictly
better than the market fill by construction, since market pays the far side:

| | TOUCH model | THROUGH-by-one-spread model |
|---|---:|---:|
| fill rate | 0.9321 | 0.8759 |
| MARKET gross on the **filled** subset | −0.25431 ± 0.01567 | −0.29878 ± 0.01565 |
| MARKET gross on the **non-filled** subset | **+0.62723 ± 0.08368** | **+0.54211 ± 0.05861** |
| entry improvement on the *same* trades | **+0.00936** | **−0.03262** |
| opportunity cost of the misses | **−0.04258 R/opportunity** | **−0.06725 R/opportunity** |

> **The trades a resting limit does not get are worth +0.627 R each. The ones it gets are worth −0.254.**
> A **+0.88 R** gap. Adverse selection is not a subtlety in this estate — it is the dominant term, and it
> is **4.5× larger than the spread the limit saves**.

Under the honest queue model the entry improvement itself goes **negative** (−0.0326): you only fill
when the tape runs through you, so you are adversely selected *at the fill* as well as *in the sample*.

### 3.5 The constructive variant, built and refuted

The obvious repair is **peg-then-cross**: rest passively for W minutes, then take the market — 100 %
participation, so no misses, and the spread is captured on whatever fills. Paired per candidate:

| arm | passive share | paired Δ vs market | t |
|---|---:|---:|---:|
| peg 1 min then cross [TOUCH] | 0.623 | **−0.06423 ± 0.00556** | **−22.65** |
| peg 3 min [TOUCH] | 0.722 | −0.06436 ± 0.00645 | −19.55 |
| peg 10 min [TOUCH] | 0.819 | −0.07747 ± 0.00846 | −17.95 |
| peg 1 min [THROUGH] | 0.434 | −0.07903 ± 0.00558 | −27.76 |
| peg 10 min [THROUGH] | 0.686 | −0.13422 ± 0.00907 | −28.99 |

**Every window, both fill models, loses at 18–29 sigma.** And I tested and **refuted the obvious
explanation**: pure signal decay is *not* the mechanism — the price advantage of acting at once rather
than W minutes later is **+0.0045 ± 0.0051 R at 1 min** and never exceeds +0.0064 at any W out to 20.
The loss is selection at the fill, decomposed:

| fill mode at W=1 | n | paired Δ |
|---|---:|---:|
| PASSIVE (filled at the better price) | 13,516 | **−0.06331 ± 0.00744** |
| CROSS (limit missed, took the market) | 8,168 | −0.06575 ± 0.00813 |

**Even the trades that fill at a strictly better price do worse.** For a long, price coming down to your
limit *is* the bearish information; you buy the dip and the dip continues. That is the finding.

### 3.6 Risk-normalised passive ladder — the last defence, also refuted

Resting deeper (k > 0) makes a stop lose only (1−k) R and a target win (2+k) R, which flatters raw R.
Normalising so a stop is exactly −1 R and size scales 1/(1−k):

| arm | fill rate | **net R per opportunity** | Δ vs market |
|---|---:|---:|---:|
| MARKET (tick-true) | 1.000 | −0.34961 ± 0.0165 | — |
| LIMIT k=0.00 TOUCH | 0.932 | −0.35418 | −0.0046 |
| LIMIT k=0.10 TOUCH | 0.890 | −0.34796 | +0.0017 |
| LIMIT k=0.25 TOUCH | 0.814 | −0.36365 | −0.0141 |
| LIMIT k=0.50 TOUCH | 0.697 | −0.42201 | −0.0724 |
| every THROUGH arm | 0.644–0.876 | −0.402 to −0.490 | −0.053 to −0.140 |

**Best case is indistinguishable from zero at k = 0.10 (+0.0017 ± 0.017); everything else loses.**

**Verdict (B): passive execution is refuted as a cost lever on this estate.** *(a) The measurement that
would reverse it:* a candidate population whose non-fill subset is **not** worth more than its fill
subset — i.e. mean-reverting entries rather than momentum entries. The three POI families are exactly
that shape and their real prices were never walked (§8). *(b) The nearest unrefuted constructive
variant:* `current_ob_retest` — the cheapest thing in the estate at **0.0979 R cost and −0.1347 R net**,
already passive, already the best net of any family, and currently **excluded by the frozen rule**.

---

## 4. (C) THE COST-MINIMAL EXECUTION ENVELOPE

`lane7_receipts/C_COST_ENVELOPE_V1.json`.

### 4.1 The finding that makes cost reduction free

Ex-ante cost deciles (`cost_r` is a generation-time field, known before the outcome):

| decile | n | cost | **pre-cost gross ± CI95** | net |
|---:|---:|---:|---:|---:|
| 0 | 14,675 | 0.0363 | **+0.0080 ± 0.0154** | **−0.0283** |
| 1 | 14,674 | 0.0480 | −0.0153 ± 0.0182 | −0.0633 |
| 3 | 14,674 | 0.0728 | −0.0443 ± 0.0191 | −0.1171 |
| 5 | 14,674 | 0.1192 | −0.0318 ± 0.0197 | −0.1509 |
| 7 | 14,675 | 0.2505 | −0.0225 ± 0.0204 | −0.2730 |
| 9 | 14,675 | **0.8700** | **+0.0064 ± 0.0211** | **−0.8636** |

**Net tracks cost 1:1 across a 24× cost range. Pre-cost gross is flat and the *cheapest* decile is the
most positive.** The cost-cutting capture rate is therefore ≈ 100 % at the hour level (WLS slope of
pre-cost gross on cost, hour cells: **−0.179**, i.e. cheap hours are *better*) and 85 % at the symbol
level (slope **+0.150** — expensive symbols do carry a little more gross, so cutting 1 R of symbol cost
gives back 0.15 R of gross).

### 4.2 The ladder, leave-one-month-out

Thresholds fit on four months, applied to the fifth. No outcome is used to choose anything.

| rung | n | breadth | cost | **pre-cost gross** | **net** | per-month net |
|---|---:|---:|---:|---:|---:|---|
| L0 all fills | 146,745 | 100.0 % | 0.2133 | −0.0188 | **−0.2321** | −.193 −.221 −.244 −.237 −.266 |
| L1 drop hours 16–21 | 126,839 | 86.4 % | 0.1906 | −0.0160 | −0.2067 | −.181 −.191 −.223 −.205 −.233 |
| L2 + favourable-carry side | 63,465 | 43.2 % | 0.1755 | −0.0130 | −0.1885 | −.172 −.140 −.206 −.208 −.213 |
| L3 + cost ≤ OOS median | 35,633 | 24.3 % | 0.0601 | −0.0151 | −0.0752 | −.056 −.058 −.098 −.076 −.090 |
| L4 + cost ≤ OOS p25 | 18,285 | 12.5 % | 0.0446 | −0.0056 | −0.0503 | −.021 −.119 −.030 −.036 −.056 |
| **L5 + cost ≤ OOS p10** | 7,428 | **5.1 %** | **0.0364** | **+0.0022** | **−0.0342** | −.009 −.095 −.046 −.005 −.024 |

**Cost −83 %. Net +0.198 R/fill, 85.3 % of the loss removed. Pre-cost gross does not degrade.** The
price is breadth: 100 % → 5.1 % of fills. **L4 is the recommended operating point** — 12.5 % of breadth
retained for 78 % of the saving, and it is the last rung where every month is within a whisker.

**Both sides priced.** At L4 the estate keeps 18,285 of 146,745 opportunities. If the goal were R/month
rather than R/trade, L4 removes 87.5 % of the trade count to remove 78 % of the cost — a losing trade
*if there were positive gross to preserve*. There is not, which is exactly why it wins here.

**Adversarial check on my own positive.** The one rung that misbehaves is L4/L5 in **April**
(−0.119 / −0.095 against a −0.221 baseline at L0 — better, but the worst of the five). April is also the
month whose expensive half had *positive* pre-cost gross (+0.0255). If a future month looks like April,
the veto's value halves. It does not reverse in any month measured.

---

## 5. (D) SLIPPAGE AND THE STOP-FILL ASYMMETRY

`lane7_receipts/D_SLIPPAGE_AND_STOP_FILLS_V1.json`.

**`expected_slippage_r` is the constant 0.02 on all 632,934 rows — no dispersion, no symbol, no hour, no
side.** Measured against 11,370 tick-walked stops:

| quantity | value |
|---|---:|
| gap at the **open** of the triggering minute (the true stop slippage) | **+0.06045 R** mean, median 0.0000, p90 0.0000, **p99 +1.45192** |
| fraction of stops that gap at all | **9.32 %** |
| maximum penetration *inside* the triggering minute | +0.29453 mean, +2.55559 p99 |
| stop share of fills | 0.5243 |
| **expected slippage on the stop leg alone** | **0.06045 × 0.5243 = 0.03169 R/fill** |
| charged | **0.02000 R/fill on every fill** |

> **The model is optimistic on the stop leg by ≥ 0.0117 R/fill (≥ 58 % too low), and simultaneously
> over-charges the target leg — a target is a resting limit exit and pays no slippage at all.** The two
> errors do not cancel: the target leg is 20.9 % of fills at −0.02 (over-charge, worth +0.0042) against
> a stop leg under-charge of −0.0117.

The distribution is the point: **90.7 % of stops fill exactly at the stop and 9.3 % gap, with a p99 of
+1.45 R.** A flat 0.02 gets the mean roughly half right and the tail entirely wrong.

**Where the gaps are.** By symbol: GBPJPY +0.1150, USDJPY +0.1133, CHFJPY +0.0847, EURGBP +0.0831,
NZDUSD +0.0818 — **the JPY crosses and the thin FX**. By hour: **h21 +0.9306, h20 +0.2747**, h12
+0.1231, everything 08–15 at 0.015–0.031. The tail lives in the rollover window, which §2.2 already
flags as the 4.3× cost hour. Two independent instruments point at the same six hours.

---

## 6. THE SPREAD MODEL IS WRONG WHERE IT MATTERS, AND IT MOVES THE SEALED RECORD

`lane7_receipts/G_SPREAD_MODEL_TRUTH_AND_RESTATEMENT_V1.json`.

**The defect: the model is hour-flat for the cash indices; the tape is not.**

UK100, modelled vs true spread by UTC hour (price units):

| hour | 00 | 03 | 05 | 07 | 11 | 14 | 16 | 19 | 20 | 22 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **modelled** | 0.897 | 0.876 | 0.871 | 0.871 | 0.866 | 0.871 | 0.871 | 0.858 | 0.941 | 1.116 |
| **true (tape)** | 4.187 | 3.969 | 3.995 | 0.794 | 0.673 | 0.759 | 1.527 | 1.502 | **5.993** | 5.190 |
| ratio | **4.67** | **4.53** | **4.59** | 0.91 | 0.78 | 0.87 | 1.75 | 1.75 | **6.37** | **4.65** |

The model is **right inside the London cash session (0.78–0.91) and 4.5–6.4× too small outside it.**
GER40 has the identical shape (2.63–2.72× in hours 00–05; 0.93–0.97 in 07–14). **SPX500, NAS100,
US30_cash and JP225 are correct at every hour (0.93–1.06)** — so this is a defect in two symbols, not a
systematic bias, and the correct four validate the method.

**Adversarial check, and it changed my answer.** My first pass compared *mean* tick spread to the model
and produced a −14.9 R restatement. UK100's spread is bimodal (median 0.85, mean 2.11), so the mean
overstated it. Redone **hour-conditionally, against the model as it is actually applied**, the
correction is **+7.04 R, not +15.8 R**. The finding survives; its size does not. Both passes are in the
receipt.

### 6.1 The restatement

| | as sealed | at tape-true spreads |
|---|---:|---:|
| pre-cost gross | +32.04 R | +32.04 R |
| cost paid | 31.09 R | **38.13 R** |
| **net, five months, 282 trades** | **+0.954 R** | **−6.090 R** |

| month | n | sealed | tape-true | extra cost |
|---|---:|---:|---:|---:|
| 2026-02 | 105 | +14.168 | **+14.062** | 0.106 |
| 2026-04 | 49 | −7.742 | −7.736 | −0.006 |
| 2026-05 | 17 | +5.130 | +5.135 | −0.005 |
| 2026-06 | 45 | +3.964 | **+1.176** | 2.787 |
| 2026-07 | 66 | −14.566 | **−18.727** | 4.161 |

**February's PASS survives intact.** The correction lands on June and July, which is exactly the window
where the tick archive gives *direct* evidence (Jun+Jul sealed −10.602 → tape-true **−17.550**);
Feb/Apr/May move by less than 0.11 R combined. **7.081 of the 7.04 R sits in UK100**, which is **26.2 %
of the rule's trades** — the rule concentrated a quarter of its book in the one symbol its cost model
under-prices 2.5×.

At the pool level the same correction is modest — **+0.00933 R/fill, 3.3 % of total cost, 693 R over
74,249 MARKET fills** — because UK100 and GER40 are only 8.6 % of the pool. **It is large on the traded
record and small on the pool, and that difference is itself the finding: selection concentrated the
book into the defect.**

---

## 7. (E) BROKER/INSTRUMENT ARBITRAGE AND (F) SWAP

### 7.1 (E) The two accounts should not trade the same instruments

True tick spreads, both hosts, identical window. `lane7_receipts/E_BROKER_INSTRUMENT_ARBITRAGE_V1.json`.

| cheaper on **redacted_account** | ratio FN/FTMO | cheaper on **FTMO** | ratio FN/FTMO |
|---|---:|---|---:|
| CHFJPY | **0.69** | **BTCUSD** | **19.72** |
| EURJPY | 0.88 | USDCHF | 1.99 |
| GBPJPY | 0.88 | JP225 | 1.95 |
| ETHUSD | 0.89 | USDJPY | 1.72 |
| NZDUSD | 0.89 | EURGBP | 1.67 |
| USOIL | 0.92 | EURUSD | 1.46 |
| USDCAD | 0.94 | XAUUSD | 1.28 |
| AUDJPY | 0.96 | GER40 | 1.15 |
| UK100 | 0.96 | US500, US30, NAS100, XAGUSD, GBPUSD, AUDUSD, NZDJPY, UKOIL | 1.04–1.14 |

> **Of 25 shared instruments, ZERO are within 2 % of each other. Sixteen are cheaper on FTMO, nine on
> redacted_account.** Both books currently trade the same four sleeves on the same instruments.
>
> **The single largest item in the estate: BTCUSD is 19.72× more expensive on redacted_account in relative
> spread (22.86 vs 1.15 price units on a ~62,700 mid).** BTCUSD is also the pool's #1 cost burner
> (5,441 R) and carries the estate's highest commission (0.3984 R/fill). **Any crypto exposure belongs
> on FTMO; any JPY-cross exposure belongs on redacted_account.**

The recommendation is therefore **yes: the two accounts should trade different instrument sets**, and
the split is measured per instrument above. *This is a cost statement only — it does not price the
diversification value of running the same book twice, which is a separate owner question.*

### 7.2 (F) Swap is one-sided, and the side is nearly free to choose

`lane7_receipts/F_SWAP_CROSS_SECTION_V1.json`. **80.0 % of fills pay zero swap** — the charge is
concentrated entirely on the negative-carry side, and for most symbols the favourable side is exactly
0.0000:

| symbol | swap LONG | swap SHORT | favourable side |
|---|---:|---:|---|
| USDJPY | **0.00000** | 0.14032 | LONG |
| USOIL_cash | **0.00000** | 0.13025 | LONG |
| UKOIL_cash | **0.00000** | 0.11372 | LONG |
| USDCHF | **0.00000** | 0.09088 | LONG |
| AUDJPY | **0.00000** | 0.08892 | LONG |
| UK100 | 0.08407 | **0.00000** | SHORT |
| US30_cash | **0.00000** | 0.07254 | LONG |
| SPX500 | 0.07658 | 0.00838 | SHORT |
| EURGBP | 0.07290 | **0.00000** | SHORT |
| BTCUSD | 0.09305 | 0.10947 | LONG (both charged) |

| | n | swap | all-in cost | **pre-cost gross ± CI95** | net |
|---|---:|---:|---:|---:|---:|
| adverse-carry side | 73,835 | 0.06655 | 0.24233 | −0.02301 ± 0.00863 | −0.26534 |
| **favourable-carry side** | 72,910 | **0.01432** | **0.18393** | **−0.01449 ± 0.00868** | **−0.19842** |

**Restricting to the favourable-carry side saves 0.0584 R/fill (65.7 % of all swap) and the pre-cost
gross is, if anything, better on the side you keep** (+0.0085, within noise). It costs 49.7 % of
breadth. Swap concentrates by session exactly where §2.2 and §5 already point: `moonshot_h20_21` 0.2320,
`h14_15` 0.2250, `h19_20` 0.2146 against 0.0000 for every session ending before 12 UTC.

---

## 8. (G) THE PROGRAM, AND THE HEADLINE QUESTION

`lane7_receipts/H_PROGRAM_AND_HEADLINE_V1.json`. The frozen rule trades **56.4/month** and earns
**+6.408 R/month gross** against **6.217 R/month of modelled cost** (7.626 tape-true).

The steps are **cumulative rungs of one ladder, not additive independent items** — each "net gain" is
the marginal move from the rung above it, measured per fill on the pool.

| # | change | marginal gain, R/fill (pool) | breadth cost | what would prove it wrong |
|---|---|---:|---|---|
| **1** | **Make the cash-index spread model hour-conditional (UK100, GER40).** An accounting repair, not a saving: it moves the sealed 5-month record **+0.954 → −6.090 R** and June/July **+3.964 / −14.566 → +1.176 / −18.727** | 0 (repair) | none | a second tick capture showing UK100 hours 00–05 at the modelled 0.87 |
| **2** | **Drop UTC hours 16–21.** Cost 0.2133 → 0.1906; h21 alone is 0.9216 R/fill and gaps stops 0.93 R | **+0.0254** | 13.6 % | nothing — the effect is in the model *and* the tape *and* the stop gaps |
| **3** | **Favourable-carry side only.** Swap 0.0666 → 0.0143 | **+0.0182** | 43 % cumulative | a symbol whose adverse-carry side carries gross exceeding its swap; none at n = 146,745 |
| **4** | **Ex-ante cost veto at the OOS median.** Cost 0.1755 → 0.0601 | **+0.1133** | 76 % cumulative | a month where the cheap half is worse than the expensive half — has not happened in 5/5 |
| **5** | **Tighten the veto to the OOS 25th percentile.** Cost 0.0601 → 0.0446 | **+0.0250** | 87.5 % cumulative | as #4; April is the weakest month and still improves |
| **6** | **Route crypto to FTMO, JPY crosses to redacted_account.** BTCUSD FN/FTMO relative spread 19.72× | not separable from #4 on this population; BTCUSD alone burns 4,161 R at 0.3984 R/fill | none — a venue choice | a commission/spread schedule change on either host |
| **7** | **Replace the flat 0.02 slippage with the measured stop-conditional value.** | 0 — it makes published net **worse** by ≥ 0.0117 R/fill | none | a tick capture showing stop gaps below 0.02 R |

**Cumulative #2→#5: +0.1818 R/fill, 85 % of the loss.**

Scaled to the frozen rule's own book — 56.4 trades/month at a mean cost of **0.1102 R** modelled /
**0.1352 R** tape-true (the rule already selects cheaper-than-pool trades, so it has captured about half
of this already):

| bound | modelled | tape-true |
|---|---:|---:|
| conservative — simply halve the rule's cost | **+3.11 R/mo** | **+3.81 R/mo** |
| cost-veto to the pool p25 floor (0.0446) | **+3.70 R/mo** | **+5.11 R/mo** |
| cost-veto to the cheapest-decile floor (0.0363) | +4.17 R/mo | +5.58 R/mo |

**Recoverable: +3.1 R/month at the conservative bound, +3.7 to +5.1 R/month at the measured cost-veto
floor — against a sealed five-month total result of +0.954 R.** The lever is worth several times the
entire result it would be applied to.

### 8.1 The headline question, answered

> **What is the five-month record under the full cost-minimal policy, and does any month turn positive?**

**No — and the reason is structural, not a failure of the policy.**

At the tightest envelope the pool goes **−0.2321 → −0.0342 R/fill**, removing **85.3 %** of the loss.
Every one of the five months stays negative: **−0.0085, −0.0954, −0.0456, −0.0052, −0.0241.** June and
February come within a hundredth of a unit of zero and stop there.

The reason is in one number: **pre-cost gross at the tightest envelope is +0.00215 ± 0.0206.**
Statistically zero. Cost reduction is a subtraction from a subtraction — it drives the loss to zero
asymptotically and cannot cross it.

> **The mandate's arithmetic is right and its conclusion needs one more clause. "If cost is 100 % of the
> loss then halving cost halves the loss" is true and I have measured it: cost is 91.9 % of the pool's
> loss and 97.0 % of the frozen rule's gross. But the terminal value of a complete cost-minimisation
> program on this estate is E[net] → 0⁻, not E[net] > 0. Cost is the whole loss, so cost is the whole
> lever — and the lever's full travel ends exactly at break-even.**
>
> **That is not a reason to skip the program.** It is worth **+3.0 R/month**, it is the only quantity in
> this estate that is knowable before the trade, and it converts a −0.232 R/fill machine into a −0.034
> R/fill machine. **Any gross edge that is ever found is worth 6.8× more inside the cheap envelope than
> outside it**, because the same absolute edge survives a 0.036 R toll and dies under a 0.213 R one.
> Build the envelope first; it is the multiplier on everything that comes after.

---

## 9. WHAT WOULD REVERSE EACH NEGATIVE HERE

Per the mandate, no refutation without its reversal condition and its nearest constructive variant.

| finding | the measurement that would reverse it | nearest unrefuted constructive variant |
|---|---|---|
| passive execution loses (§3.5) | a population whose **non-fill** subset is worth *less* than its fill subset — mean-reverting entries, not momentum. Tested only on the seven MARKET families | **walk the three POI families' real prices.** They are already passive, `current_ob_retest` is the cheapest and best-net family in the estate (0.0979 cost, −0.1347 net) and the frozen rule excludes it. Their prices are **not** in `lg_*.pkl.gz` — this needs one generation re-export and is the single highest-value follow-up in this lane |
| no month turns positive under cost minimisation (§8.1) | a pre-cost gross that is reliably > +0.04 R/fill in some identifiable cell. The cheapest decile is +0.0080 ± 0.0154 and `cross_asset_lead_lag` is +0.0322 ± 0.0243 — the two places to look | **`cross_asset_lead_lag` inside the cheap envelope**: the only family with a pre-cost gross whose CI excludes zero, currently paying 0.3562 R of cost against it. Cost-veto it and the gross survives while the toll falls |
| the cash-session veto (my own proposal, refuted) | I proposed refusing cash indices outside their cash session. **Priced at tape-true cost it loses: out-of-session net −0.1749 ± 0.0219 vs in-session −0.3016 ± 0.0093.** Out-of-session index trades are *better* despite the wider spread | the narrower true prescription: **fix the model's accounting** (#1), do not veto the trades |
| the cost veto on the 282 sealed trades | at n = 282 the veto ladder is noise — arms range +7.22 R to −5.77 R and the per-month sign flips. Lane G already established all five monthly verdicts are indistinguishable from zero (p 0.14–0.64) | the **pool** is the right evidence surface (146,745 fills, monotone over ten deciles, stable over five months); the 282-trade record is the right *decision* surface and is underpowered to confirm or refute it. Do not quote the +7.22 R arm |

---

## 10. FINDINGS THAT SHOULD PROPAGATE

1. **Order type is a family partition, not an execution choice.** Any future statement of the frozen
   rule should say "excludes the three POI families", because that is what it does.
2. **The tick export is 61 files / 300,538,915 rows**, not 51 / 263,894,769 as `CLAUDE.md` §4 records;
   ten files are in neither manifest and are therefore outside the sha256-verified claim.
3. **`precost = gross + spread_r` is valid for MARKET only.** Applying it to LIMIT rows inflates pooled
   pre-cost gross from −0.0188 to +0.0309 and reverses its sign.
4. **The spread model is hour-flat for UK100 and GER40 and is 4.5–6.4× low outside the London cash
   session.** SPX500/NAS100/US30/JP225 are correct. The sealed five-month frozen-rule record is
   **+0.954 R at the model and −6.090 R at the tape.**
5. **`expected_slippage_r` is a flat 0.02 constant.** The measured stop leg alone is 0.0317 R/fill;
   90.7 % of stops fill exactly and 9.3 % gap with a p99 of +1.45 R.
6. **Commission is 38.0 % of all cost** and is an instrument-and-venue choice; eight symbols pay zero.
7. **Zero of 25 shared instruments price within 2 % across the two brokers.**

---

*Lane 7. All figures reproducible from `lane7_receipts/*.py` against the sources named in §1.*
