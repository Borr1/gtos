# B6 — THE REGIME OVERLAY, HARDENED

**Breakthrough lane 6. Commissioned to turn the estate's only out-of-sample predictive finding into
a deployable book and a pre-registered read. The hardening killed it.**

Swarm-2 breakthrough lane, 2026-08-11. Read-only. No `src/`, no config, no broker, no VPS, no git write.
Population: `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` — 632,934 candidate
occurrences, 84,721 eligible∩filled. Code and receipts: `b6_regime_overlay/`.

---

## 0. THE ANSWER, UP FRONT

**Lane 6's regime × family interaction overlay is a lookahead artifact. It does not survive the
requirement that its features be knowable at the decision instant, and the failure is total, not
marginal.**

| | OOS Spearman | p |
|---|---:|---:|
| Lane 6 as published (M6, regime + interactions) — **reproduced exactly** | **+0.1539** | 4.12e-05 |
| same model, train-only standardisation (scaler leak removed) | +0.1539 | 4.11e-05 |
| **same model, regime features lagged one day (causal at day open)** | **−0.0432** | 0.252 |
| same model, causal trailing-24h regime, trades at hour ≥ 12 only | −0.0171 | 0.682 |
| **control**: non-causal whole-day regime on that *same* hour ≥ 12 trade subset | **+0.1003** | 0.0159 |

The published overlay's regime state is the **median over every eligible candidate on the trading
day**, including candidates generated hours *after* the trade being predicted. Removing that — and
only that — moves the result from 3.9-sigma positive to indistinguishable from zero. The
standardisation leak (a global `StandardScaler` fit on all rows including future ones) turns out to
be innocent: it costs 0.0000 of the rho.

**Consequences that bind immediately:**

1. **The A+B book (+0.0394 R/trade, +149.7 R, 3/4 months) is built on the artifact.** Its gate A is
   this model's prediction. Re-measured in section 4 below.
2. **The long-only weakness is explained by the artifact, not by the four months' market
   direction.** Section 5. This changes the answer to the lane's centre-of-gravity question.
3. **The pre-registration must not spend a 2025 window on this object.** What replaces it is in
   section 8; the four never-read 2025 windows remain unread and unspent by this lane.

Everything below is the evidence, the reversal measurements, and what was built in its place.

---

## 1. REPRODUCTION — EXACT

Before touching anything, Lane 6's result was rebuilt from the cache with independent code
(`b6_core.py`, `panel.py`, `repro.py`).

**Population identity.** eligible∩filled per month, mean `net_r`: feb 18,585 / −0.0614;
apr 15,470 / −0.1009; may 15,274 / −0.0903; jun 19,253 / −0.1070; jul 16,139 / −0.1064;
pooled 84,721 / −0.09277. Identical to Lane 6's stated baselines and to the sealed
`POOL_ANSWERS.eligible_pool_baseline`.

**Panel.** 948 family-days after the 20-day momentum warm-up; 10 families; 97 days; **704
out-of-sample** family-days after the 25-day minimum training window — Lane 6's counts exactly.

**Ablation, reproduced** (`receipts/repro.json`):

| arm | features | OOS ρ | p | Lane 6 published ρ |
|---|---|---:|---:|---:|
| M0 | family identity only | −0.0455 | 0.228 | −0.0455 |
| M1 | family + momentum | −0.0051 | 0.892 | −0.0051 |
| M2 | family + regime, additive | −0.0703 | 0.062 | −0.0703 |
| M3 | family + regime + interactions | +0.1379 | 0.000243 | +0.1379 |
| M4 | full (+ momentum) | +0.1462 | 9.9e-05 | +0.1462 |
| M5 | regime only | −0.0389 | 0.303 | −0.0388 |
| **M6** | **regime + interactions only** | **+0.1539** | **4.12e-05** | **+0.1539** |
| M7 | momentum only | +0.0017 | 0.964 | +0.0017 |

Eight of eight arms match to four decimal places. The reproduction is not in question; what follows
is not a failure to reproduce.

---

## 2. THE CAUSALITY LADDER

Each rung removes exactly one thing a deployed model could not know, holding everything else fixed
(`ladder.py`, `receipts/ladder.json`). All rungs use the same 704 out-of-sample family-days.

| rung | OOS ρ (M6) | p | Δ R/trade | months + | OOS ρ (M3) | p |
|---|---:|---:|---:|---:|---:|---:|
| L0 Lane 6 exact — global scaler, same-day regime | **+0.1539** | 4.1e-05 | +0.0745 | 4/4 | +0.1379 | 0.00024 |
| L1 + train-only standardisation | +0.1539 | 4.1e-05 | +0.0715 | 4/4 | +0.1377 | 0.00025 |
| **L2 + regime lagged one day (causal at day open)** | **−0.0432** | 0.252 | −0.0024 | 2/4 | −0.0001 | 0.999 |
| L3 + wider causal regime block (13 dials) | −0.0362 | 0.337 | −0.0170 | 1/4 | +0.0030 | 0.937 |
| L4 + trailing level/change state (37 dials) | −0.0651 | 0.084 | +0.0114 | 3/4 | −0.0383 | 0.310 |

**The scaler is innocent and the regime timing is everything.** L0→L1 costs 0.0000 ρ. L1→L2 costs
0.1971 ρ — the entire finding and then some. Widening the causal feature block (L3, L4) does not
recover it; four extra specifications were spent trying.

---

## 3. THE AS-OF CURVE — WHERE THE INFORMATION LIVES

The lag-1 test could in principle be unfair: a whole trading day is a long lag, and a deployed
system could know the day's regime *so far*. So the regime was rebuilt as a **trailing 24-hour
median over eligible candidates strictly before a cutoff instant** (day, h:00 UTC), and the panel
restricted to trades at **hour ≥ h** — so every feature strictly precedes every trade it scores.
The control is the identical trade subset scored by Lane 6's whole-day regime (`asof.py`,
`receipts/asof_curve.json`).

| cutoff | causal trailing-24h ρ | p | non-causal whole-day ρ (same trades) | p |
|---|---:|---:|---:|---:|
| h ≥ 0 | −0.0581 | 0.194 | +0.1539 | 4.1e-05 |
| h ≥ 2 | +0.0114 | 0.764 | +0.1292 | 0.00062 |
| h ≥ 4 | −0.0184 | 0.630 | +0.1450 | 0.00014 |
| h ≥ 6 | +0.0401 | 0.299 | +0.1606 | 2.9e-05 |
| h ≥ 8 | −0.0081 | 0.838 | +0.1215 | 0.0021 |
| h ≥ 10 | −0.0230 | 0.571 | +0.1018 | 0.0118 |
| h ≥ 12 | −0.0171 | 0.682 | +0.1003 | 0.0159 |
| h ≥ 14 | −0.0130 | 0.775 | +0.1349 | 0.0030 |
| h ≥ 16 | +0.0422 | 0.470 | +0.0186 | 0.750 |

**Nine cutoffs, nine nulls on the causal side** (|ρ| ≤ 0.058, every p ≥ 0.19), against a non-causal
control that stays significant on the same trades down to h ≥ 14 — where the causal window already
contains the whole of that day's morning and the only remaining difference is *the afternoon that
has not happened yet*.

The mechanism is not obscure. The day-level dials are medians over the set of candidates the day
produced, and **which candidates a day produces is determined by the price path that day**. A
violent afternoon prints more displacement candidates with high body/ATR and moves the day's median;
the outcomes of trades taken into that afternoon depend on the same path. The whole-day median is
therefore a partially-realised summary of the future, and the family × regime interaction is the
model's way of reading it.

**Which feature carries it** (`receipts/dial_ablation.json`, leave-one-out on the non-causal arm):
dropping `trendshare` — the share of that day's eligible candidates in a *strong* trend state —
takes ρ from **+0.1447 to −0.0373**, Δ −0.1820. Every other dial is worth ≤ 0.0074. `trendshare`
alone, with its ten family interactions, is worth **−0.0550**: the artifact is not one feature, it
is *the day's realised trendiness* read jointly with which family is trading. Continuation families
win on days that trended and reversion families win on days that did not, and the whole-day median
tells the model which kind of day it was before the day is over.

---

## 4. THE BOOK, RE-MEASURED

`book.py`, `receipts/book_causal.json`. Identical construction to Lane 6 §6 — gate A = family-day
prediction > 0, gate B = `cost_r` ≤ the cheapest tercile of strictly prior data — changing only the
gate's information set.

| rule | n | R/trade | se (day) | 95 % CI (day-boot) | P(≤0) | months + |
|---|---:|---:|---:|---|---:|---:|
| ALL (control) | 58,949 | −0.10199 | 0.00908 | [−0.1194, −0.0842] | 1.0000 | 0/4 |
| B cost only | 20,247 | −0.05108 | 0.01432 | [−0.0784, −0.0233] | 0.9998 | 0/4 |
| **A+B, published gate (same-day regime)** | 3,798 | **+0.03941** | — | — | 0.218 | 3/4 |
| **A+B, causal gate (lag-1 regime)** | 2,638 | **−0.04184** | 0.04118 | [−0.1273, +0.0373] | **0.8490** | 2/4 |
| A regime only, causal | 7,863 | −0.11019 | 0.02658 | [−0.1607, −0.0575] | 1.0000 | 0/4 |

**The causal regime gate is worse than no gate at all** (−0.1102 against a −0.1020 control). The
+0.0394 R/trade, +149.7 R book does not exist once the gate is restricted to information that
precedes the trade.

---

## 5. THE SHORT-LEG VERDICT — THE LANE'S CENTRE OF GRAVITY

The mandate names this the single measurement that decides whether the overlay is a real edge or a
bull-market artifact, and Lane 6 §7.2 says it requires a window containing a sustained down-move.
**It does not. The five sealed months already answer it, and the answer is the opposite of the
published one.**

### 5.1 A direction index the cache can support

There are no prices in the cache, so a daily direction index was built from the bar-derived trend
states it does carry: per symbol per day, (share of candidates in `strong_up`/`up`) − (share in
`strong_down`/`down`), averaged over the eight index symbols (`direction.py`,
`receipts/daily_direction_index.csv`). **It validates against the pool's own realised LONG − SHORT
drift at Spearman +0.627 over 100 days** (four alternative constructions land +0.556…+0.583; the
index-symbol version is the strongest and was taken).

**The window is not a one-way market. 40 of 100 days carry a negative direction index.** What the
five months lack is a sustained *multi-week* drawdown, which is a statement about path, not about
whether shorts were ever tested.

### 5.2 The pool is direction-conditional, and symmetrically so

Eligible∩filled pool, by quintile of the daily direction index (`receipts/direction_window.json`):

| quintile | days | dir index | LONG net | SHORT net | L − S | LONG dirinfo | SHORT dirinfo |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q0 most **down** | 20 | −0.377 | −0.22367 | **+0.02115** | −0.2448 | −0.11416 | **+0.12891** |
| Q1 | 20 | −0.128 | −0.12368 | −0.06042 | −0.0633 | −0.01474 | +0.05141 |
| Q2 | 20 | +0.093 | −0.09717 | −0.11744 | +0.0203 | +0.01828 | −0.00525 |
| Q3 | 20 | +0.256 | −0.04342 | −0.11320 | +0.0698 | +0.06576 | −0.00305 |
| Q4 most **up** | 20 | +0.496 | **+0.09149** | −0.21919 | +0.3107 | +0.20052 | −0.10971 |

L − S runs monotonically from **−0.245 to +0.311** — a 0.556 R swing — and **on the most-down
quintile the SHORT leg is the positive one**. The short side is not structurally dead; it is
conditionally alive, in exactly the way the long side is.

### 5.3 On the causally clean cost gate, the short leg is the best cell in the exercise

The ex-ante cost gate (cheapest prior-data quartile, walk-forward — no regime overlay of any kind),
split by day-direction tercile (`receipts/final_profile.json`):

| tercile | n | all | LONG | SHORT |
|---|---:|---:|---:|---:|
| Q0 most down | 7,073 | −0.01632 | −0.13742 | **+0.10787** |
| Q1 | 5,968 | −0.04468 | −0.02830 | −0.06080 |
| Q2 most up | 6,604 | −0.04591 | **+0.11043** | −0.17991 |

**Cost-gated SHORT on down-direction days: +0.10787 R/trade, n = 3,492, 95 % day-block CI
[+0.0169, +0.1941], P(≤0) = 0.0118.** That is the only positive, bootstrap-significant cell this
lane measured, and it is a short-leg cell.

### 5.4 Why Lane 6 saw a long-only edge

`attribution.py`, `receipts/attribution.json`. The published A+B reproduces exactly here
(n = 3,798, +0.03941; LONG +0.08629 / SHORT −0.00601).

- **The gate lands on trending days, and the trending days in the selected set skew up.** A+B's
  trade-weighted direction index is **+0.165** against **+0.062** for all out-of-sample days;
  `corr(A+B trades that day, direction index) = +0.332, p = 0.0047`.
- **Inside the down-direction tercile the same A+B books SHORT +0.1263 and LONG −0.2125.** The legs
  swap, exactly as the pool's do.
- Decomposing A+B against its own same-day same-side control: composition explains 22 % of the
  +0.1414 gap and a within-day within-side residual of **+0.1108** explains the rest — the artifact
  is mostly *family selection given the day*, which is what a whole-day trendiness read buys.

**Verdict: the short leg was never flat. It was pooled across a set of days whose direction skewed
up because the artifact selected them.** No 2025 window is needed to establish this, and the
proposal to spend one on it is withdrawn.

### 5.5 What the archive can and cannot do

Asked directly, because the mandate ordered the measurement extended backwards over every available
drawdown. Bars for 2018 Q4, 2020 Q1 and 2022 **do** exist on this machine
(`/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/deep_universe_*`):
2022 at full symbol surface, 2020 Q1 and 2018 Q4 for FX, metals, crypto, `US2000_cash` and (from
2019-02) `US30_cash` — **NAS100/SPX500/UK100/JP225 do not exist before 2021-01-21**.

**The extension is nonetheless blocked, and at the label layer rather than the bar layer: no M1 bars
exist anywhere on this machine before 2023, and no ticks before 2025-10.** The sealed reads' outcome
labels are a modelled M1 lifecycle, so a pre-2023 window cannot carry a label comparable to any
sealed window; a 2018/2020/2022 read would be measuring a different quantity. `WINDOWS` in
`src/research_infra/lane_rematerialization.py:209` declares nothing before `june_2025`, and
`LANE_EXTENSION_WINDOW_IDS` gates what may be added.

So the only feasible drawdown test at the estate's own label standard is a 2025 window — and §5.2–5.4
mean none needs to be spent to answer the short-leg question.

---

## 6. WHAT WAS BUILT IN ITS PLACE — THE REVERSAL MEASUREMENT AND THE NEAREST VARIANT

The mandate forbids a negative without the measurement that would reverse it and the nearest
constructive variant. §5.2 hands over both: the pool's expectancy swings 0.556 R with the day's
direction, so **if the day's direction is predictable ex ante, a causal side overlay exists where
the causal family overlay did not.**

### 6.1 Daily direction is predictable — with the opposite sign to the obvious one

`sidebuild.py`, `receipts/side_overlay.json`. The direction index is **anti-persistent**:

| lag / trailing window | Spearman vs today | p |
|---|---:|---:|
| lag 1 | **−0.2804** | 0.0049 |
| trailing-2 mean | **−0.3888** | **0.0001** |
| trailing-3 mean | −0.2742 | 0.0063 |
| trailing-5 mean | −0.2646 | 0.0085 |
| trailing-20 mean | −0.1472 | 0.166 |

Sign-agreement between the trailing-2 state and today is **0.398** — i.e. a 60.2 % *contrarian* hit
rate. So the momentum-side rule ("trade the side that has been working") is the wrong sign, and it
measures that way: at the same cost quantile (q = 0.33) the momentum side books dirinfo **−0.0050**
and the contrarian side **+0.0290**.

### 6.2 The contrarian side overlay, measured honestly

`contrarian.py`, `receipts/contrarian.json`. Walk-forward, gate computed from strictly prior days.

| rule | n | net R/trade | dirinfo | P(≤0) | months + |
|---|---:|---:|---:|---:|---:|
| pool (control) | 84,721 | −0.09277 | +0.01752 | — | 0/5 |
| contrarian K=1 | 41,082 | −0.07298 | +0.03811 | 1.000 | 1/5 |
| contrarian K=2 | 40,809 | −0.07778 | +0.03350 | 1.000 | 0/5 |
| cost gate q=0.25 alone | 19,645 | −0.03488 | +0.01695 | 1.000 | 1/5 |
| **contrarian K=2 × cost q=0.25** | 9,527 | **−0.02239** | +0.02943 | 0.804 | 1/5 |
| momentum K=2 × cost q=0.33 (wrong-sign control) | 13,936 | −0.06364 | −0.00502 | 0.996 | 0/5 |

**The contrarian side rule roughly doubles the pool's pre-cost directional information**
(+0.0335 against +0.0175) and its wrong-sign control goes negative, which is the A/B that says the
effect is directional and not a sampling accident. **It still does not reach a positive book**:
−0.0224 R/trade, closing 76 % of the pool's gap and stopping — the same place Lane 6's score × cost
composite stopped (−0.0230, 75 %), reached by a different road.

**The ceiling, stated.** A perfect same-day direction call (oracle, not deployable) takes the pool
from −0.09277 to **−0.01745** — worth **+0.0753 R/trade**. *Even a perfect daily direction call does
not make this pool profitable.* Direction is a real lever and it is not a large enough one, and that
is a more useful number than any of the conditional cells above.

### 6.3 Cross-sectional variant, for completeness

Per-symbol trailing direction (24 symbols rather than one index) was tested at K ∈ {1,2,3,5,10} and
is uniformly worse than the pooled index version (best net −0.0958, dirinfo +0.0150). The signal is
market-level, not symbol-level.

---

## 7. COMPOSITION WITH THE OTHER LANES' COMPONENTS

`compose.py`, `receipts/compose.json`. Built on the eligible∩**resolved** population — 336,430 rows,
fill rate 0.2518 (MARKET 1.000, LIMIT 0.148) — where the economic outcome of *proposing* a candidate
is `net_r` with 0 for no-fill. E[outcome] = **−0.02336**.

Four arms on one walk-forward protocol (expanding window, refit daily, train-only standardisation,
25-day minimum), so the components are directly comparable:

| arm | OOS ρ | top-decile R/trade | top-decile 95 % CI | P(≤0) |
|---|---:|---:|---|---:|
| all resolved (control) | — | −0.02502 | — | — |
| **L3-shape**: direct ridge on E[net over all proposals] | +0.1321 | **+0.00117** | — | — |
| **L2-shape**: P(fill) × E[net \| fill], two-stage | +0.1455 | −0.00249 | [−0.0142, +0.0092] | 0.664 |
| L2-shape **+ causal regime block** | +0.1140 | **−0.02372** | [−0.0363, −0.0111] | 0.9998 |
| L2-shape + non-causal regime block (the artifact) | +0.1210 | −0.00872 | [−0.0254, +0.0091] | 0.853 |

**Which lane's component does the work: neither lane 6's.** The regime block subtracts value in
both forms — as a causal block it takes the top-decile book from −0.0025 to −0.0237, and even the
artifact form subtracts, because inside a composed statistic the fill/cost model already spans what
the whole-day trendiness read was proxying. The two structures **overlap and then interfere**; they
do not add.

The component that works is the fill-and-cost half. The L2-shape statistic's top decile is
−0.00249 against a −0.02502 control — **90 % of the propose-population's gap closed, at ρ = +0.1455
over 247,300 out-of-sample rows** — and the simpler L3-shape direct ridge is the only arm that
crosses zero at all (+0.00117), though neither is significant. That is the honest read: **stack the
regime interaction and you lose; the decision statistic that matters is fill probability crossed
with cost.**

---

## 8. THE DEPLOYMENT, DESIGNED AS A PAIRED CONTRAST

`paired.py`, `receipts/paired.json`. Lane 6 measured that the absolute test needs 474 days and the
paired contrast 64; Lane 4 reached the same conclusion independently. Both are right about the
*shape* and both were pricing the wrong object. Here is every candidate priced the same way —
treatment minus control, same days, same universe, one bit varied:

| contrast | days | paired mean/day | sd | t | P(≤0) | days for 80 % power (α = 0.10) |
|---|---:|---:|---:|---:|---:|---:|
| **B6-P3 ex-ante cost gate vs ungated** | 99 | **+0.04786** | 0.1363 | **+3.50** | **0.0003** | **36** |
| B6-P2 contrarian side vs full universe | 99 | +0.01295 | 0.1499 | +0.86 | 0.193 | 604 |
| B6-P1 contrarian side within cost-gated universe | 99 | +0.01322 | 0.2071 | +0.64 | 0.260 | 1,106 |
| L6 A+B non-causal overlay (the artifact) | 49 | +0.03444 | 0.3559 | +0.68 | 0.252 | 481 |
| **B6-P4 causal regime overlay (lag-1)** | 44 | **−0.06614** | 0.3570 | −1.23 | 0.896 | ∞ |
| B6-P0 momentum side (wrong-sign control) | 99 | +0.00247 | 0.2034 | +0.12 | 0.450 | 30,577 |

**Only one object is both causally clean and cheap enough to resolve: the ex-ante cost gate, at 36
trading days.** Note how badly the artifact prices even on its own terms — 481 days paired, because
its day-to-day dispersion (sd 0.356) is 2.6× the cost gate's. A finding whose paired sd is that
large was never going to be resolved by one window regardless of whether it was real.

### 8.1 The protocol, specified to run

- **Held fixed**: eligibility predicate (`predecision_geometry_valid ∧ finite(cost_r) ∧ cost_r ≤ 0.20`);
  family and symbol surface; fixed risk per trade; cost basis as sealed; exit contract as walked;
  and the day set — **both arms score the same days**.
- **Varies**: one bit — whether the cost gate is applied.
- **Statistic**: `d_t = mean(net_r | treatment, day t) − mean(net_r | control, day t)`.
- **Primary bar**: `mean(d_t) > 0`, one-sided day-block bootstrap, α = 0.10, 4,000 resamples.
- **Days needed**: 36 at α = 0.10, 49 at α = 0.05, both at 80 % power.
- **Mandatory secondaries**: S1 the short leg's absolute mean on bottom-tercile direction days
  (sealed-data value +0.10787); S2 the long leg on top-tercile days (+0.11043); S3 the direction
  symmetry table itself.
- **Disclosed, not gated**: the absolute R/trade of both arms — **which is negative** (−0.0349
  treatment, −0.0912 control). This is a component claim, not a book. No arming follows.

### 8.2 Staging — and the window that is not spent

1. **Stage 1: the forward shadow.** Already deployed, already refitting daily, costs no scarce data
   and needs 36 scored days. **If the primary bar fails here, stop.**
2. **Stage 2, conditional on stage 1 clearing**: spend exactly one never-funnel-read 2025 window,
   chosen on a criterion declared in advance and readable from bars alone — of june / august /
   september / december 2025, the one with the largest peak-to-trough drawdown of the equal-weighted
   index proxy from D1 closes, ties to the earliest start. The drawdown criterion is retained from
   Lane 6 because it is what makes S1 informative; it is a price-path read and consumes no outcome.
3. **Never**: no arming, no live authority, no sizing change follows from either stage.

**Lane 6's own recommendation — spend one 2025 window on the family × regime overlay — is revoked.**
The four never-read 2025 windows are untouched by this lane.

The pre-registration is `B6_REGIME_OVERLAY_PREREG_V1.json`, canonical
`payload_sha256 27017bc742ec35f81f47813db41c32c9eea8b29e1847f5da4526905d2e6a4b5e`
(sha256 over the sorted, separator-normalised payload with `payload_sha256` removed — the estate's
existing convention, `make_junjul_prereg.py:31-35`), with 33 bindings covering every script, every
receipt and all five cache files.

---

## 9. MULTIPLICITY, DECLARED

| stage | looks |
|---|---:|
| inherited from Lane 6 | 22 |
| causality ladder (5 rungs × 2 arms) | 10 |
| as-of cutoffs (9 hours × causal/non-causal) | 18 |
| three-way past/future/whole (3 cutoffs × 3) | 9 |
| dial ablation (9 leave-one-out + 8 keep-one) | 17 |
| direction-index constructions | 5 |
| side overlay (6 K × 2 granularities × 2 signs) | 24 |
| contrarian × cost quantile grid | 9 |
| composed-statistic arms | 4 |
| paired contrasts reported | 8 |
| **declared total** | **126** |

**Nothing in this lane carries an admission claim**, and no retrospective cell above may be cited as
a result. The pre-registered object is one look going forward.

**One claim here is not multiplicity-limited, and it is the important one.** The revocation of the
Lane 6 overlay is not a p-value: it is a demonstrated causality violation — the model's features are
computed from data that does not exist when it trades, and removing that single property removes the
entire effect. That holds at any α.

---

## 10. CORRECTIONS THIS LANE OFFERS TO THE STANDING RECORD

1. **`LANE_6_POSITIVE_RESIDUE_AND_REGIME_V1.md` §0.2, §4, §7 — "family expectancy IS predictable out
   of sample… ρ = +0.1539 (p = 4×10⁻⁵)… positive in 4 of 4 OOS months… significant against four
   independent nulls."** Reproduced exactly and then **refuted as an artifact**: the regime block is
   a whole-day aggregate over candidates the trade cannot see. Causal ρ = −0.0432 (p 0.25). The four
   nulls in §4.4 are all *label* permutations — they permute days or families and correctly find the
   day×family mapping is real. **None of them tests whether the features precede the outcome**, which
   is the axis the finding fails on. A permutation null cannot detect a lookahead that is present in
   both the observed data and every permutation of it.
2. **Lane 6 §0.3 / §6 — the A+B book (+0.0394 R/trade, +149.7 R, 3/4 months, "the only positive book
   in this whole exercise").** With a causal gate the same construction books **−0.0418 R/trade,
   P(≤0) = 0.849**. It should not be described as a hypothesis with a pulse; it should be withdrawn.
3. **Lane 6 §6.2 Check 3 / §7.2 — "the overlay's entire edge sits in the LONG leg… four months is
   not enough to tell 'the overlay only works long' from 'these four months happened not to reward
   shorts'… the measurement that settles it is a window containing a sustained down-move."**
   **Refuted from inside the sealed data, at no cost.** 40 of 100 days carry a negative direction
   index; the pool's L − S swings −0.245 → +0.311 across direction quintiles; the cost-gated SHORT
   leg on down-direction days is **+0.10787, P(≤0) = 0.0118**. The short leg is direction-conditional,
   not flat, and the pooled flatness is a composition effect of the artifact's own day selection.
4. **New — the estate's replay labels have a hard floor at 2023.** No M1 bars exist on this machine
   before 2023 and no ticks before 2025-10, so no pre-2023 window can carry an outcome label
   comparable to a sealed window. Any future proposal to "extend the measurement backwards over
   2018/2020/2022" is blocked at the label layer even though the bars are present for 2022 and
   partially present for 2018/2020. Worth recording before someone budgets a session for it.
5. **New, methodological, and general to this programme** — every walk-forward artifact in the estate
   should be checked for **contemporaneous aggregate features**. The defect here is not a coding
   slip: the training protocol was correct (expanding window, strictly prior days, daily refit,
   sample weights) and the *feature construction* was the leak. Day-level medians, day-level shares
   and day-level counts computed over "all candidates that day" are future-bearing for every trade
   that day except the last. The cheap standing check is the one in `asof.py`: rebuild the feature
   from a trailing window that ends at the decision instant, and see whether the result survives.

---

## 11. RECEIPTS

`b6_regime_overlay/` — every number above is reproducible from these.

| file | contents |
|---|---|
| `b6_core.py`, `panel.py`, `schema.py` | master frame, population identity, causal panel builder, walk-forward ridge with train-only scaling, day-clustered SE and day-block bootstrap |
| `repro.py`, `receipts/repro.json` | §1 — exact reproduction of Lane 6's eight-arm ablation |
| `ladder.py`, `receipts/ladder.json` | §2 — the causality ladder, M6 and M3 |
| `asof.py`, `receipts/asof_curve.json` | §3 — trailing-24h causal regime at nine cutoffs, with the non-causal control on identical trade subsets |
| `threeway.py`, `receipts/threeway.json` | §3 — past-only / future-only / whole-day decomposition at three cutoffs |
| `book.py`, `receipts/book_causal.json`, `receipts/dial_ablation.json` | §4 — A+B under both gates; the leave-one-out and keep-one dial ablation |
| `direction.py`, `receipts/direction_window.json`, `receipts/daily_direction_index.csv` | §5.1–5.2 — the direction index, its validation, the quintile tables |
| `attribution.py`, `receipts/attribution.json` | §5.4 — the long-only attribution and the day×side decomposition |
| `sidebuild.py`, `receipts/side_overlay.json` | §6.1, §6.3 — persistence, momentum-side overlay, oracle ceiling, per-symbol variant |
| `contrarian.py`, `receipts/contrarian.json` | §6.2 — contrarian side rule × cost gate, with the wrong-sign control |
| `compose.py`, `receipts/compose.json` | §7 — P(fill) × E[net\|fill], the L3-shape selector, and the regime block's incremental value |
| `paired.py`, `receipts/paired.json` | §8 — every paired contrast and its power |
| `final_profile.py`, `receipts/final_profile.json` | §5.3, §8.1 — the cost gate profiled by side and direction tercile; the restated short-leg secondary |
| `../B6_REGIME_OVERLAY_PREREG_V1.json` | §8.2 — the pre-registration, `payload_sha256 27017bc7…` |

Population identity was verified before anything else was computed: eligible∩filled per month
18,585 / 15,470 / 15,274 / 19,253 / 16,139 at means −0.0614 / −0.1009 / −0.0903 / −0.1070 / −0.1064,
pooled 84,721 at −0.09277 — matching the sealed `POOL_ANSWERS.eligible_pool_baseline` and Lane 6.
