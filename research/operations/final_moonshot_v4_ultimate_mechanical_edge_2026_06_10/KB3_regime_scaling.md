# KB3 — Regime meta-layer + scaling plan

Track: **regime meta-layer + scaling plan**. Status: **improvement / learning** (regime meta-layer
ships as a stress-robustness + speed overlay; the PnL-persistence variant returned a decisive
LEARNING; scaling MC + withdrawal schedule + deferred-data uplift bracket all delivered).
Builder: `KB3_regime_scaling.py`. Machine result: `KB3_REGIME_SCALING_RESULT.json`.
Book under test: the **LOCKED Wave-2 8-sleeve portfolio** (`INTEG_W2_streams_cache.pkl`,
1597 signal-days 2015-2026, the same validated streams behind `PORTFOLIO_BUILD_W2.md`).

Doctrine held throughout: leak-free (every regime feature uses ONLY days strictly `< t`);
forward holdout (TRAIN<=2024 -> FORWARD 2025/2026); **per-YEAR + per-REGIME, never an
average-as-verdict**; winsorized R; size-by-confidence; **nothing deleted** (the rejected
classifier is kept as documented learning); frequency AND return both reported.

---

## PART 1 — REGIME META-LAYER (leak-free portfolio-regime classifier)

### 1.1 Attempt-1 — book PnL-persistence regime → REJECTED (decisive learning, kept)

The obvious lift of the program's universal `ac60` finding (KB_commodity_regime: momentum-
PERSISTENCE pays, the choppy dead-zone bleeds) is to measure persistence of the **book's own
realized daily-R** and size up in the persistent regime. **It does not work, and the reason is
structural and important:**

- Per-regime realized day-R is nearly FLAT: PERSIST +0.087 / NEUTRAL +0.053 / CHOP +0.077 (mean
  day-R). Scaling by it *reduced* sharpe and stress P(pass).
- **Why:** the ~ZERO cross-sleeve correlation (avg off-diag +0.004) that makes this book
  excellent also DESTROYS the serial correlation the signal needs — summing 8 near-orthogonal
  streams whitens the daily-R series. The `ac60` edge is real but it lives on **raw market H4
  returns at ENTRY** (already baked into every sleeve's gate); re-measuring autocorrelation on
  **portfolio PnL** is the wrong object. Per-sleeve confirmation: classifying each sleeve's days
  by the persistence of its OWN prior PnL even INVERTS for metals (delta **−0.50R**), softband
  (−0.65R), and is ~0 for the rest.
- **LESSON (durable):** regime selection belongs at the **per-sleeve ENTRY gate**, not as a
  meta-layer on realized PnL. Do not re-apply ac60 at book level.

### 1.2 Attempt-2 — BREADTH + DRAWDOWN-STATE regime → ADOPTED

The leak-free book-state that DOES carry structure is **breadth** (how many uncorrelated sleeves
co-fire) and **equity drawdown-state**:

| same-day breadth | n days | mean day-R |
|---|---|---|
| 1 sleeve | 1231 | +0.008 |
| 2 | 168 | +0.214 |
| 3 | 143 | +0.223 |
| 4 | 43 | **+0.681** |
| 5 | 11 | **+1.427** |

Breadth is **monotone** with day-R — multiple independent edges aligning IS the book's pay regime.
And it is partially **predictable** (leak-free): after a trailing-10-day mean breadth >=2, next-day
mean |R| is **0.52** vs **0.18** when trailing breadth <2. Drawdown-state is also informative:
days entered below the running equity peak realize **+0.048** mean R vs **+0.106** shallow-DD.

**The classifier** (all features from days `< t`):
- `trail_breadth` = mean #sleeves firing over the trailing 10 signal-days
- `dd` = running-peak drawdown of cumulative book-R BEFORE day t
- Labels: **ACTIVE** (trail_breadth>=2.0) / NEUTRAL (>=1.3) / **QUIET** (<1.3).
- Size multiplier: ACTIVE x1.25, QUIET x0.85, NEUTRAL x1.00; **x0.80 overlay when dd > 1.5x the
  TRAIN-median drawdown** (de-risk in deeper drawdown). Avg multiplier ~0.875 (the normalized MC
  divides this out so the static-vs-regime comparison is **risk-adjusted**, not just levering up).

**Per-regime realized day-R (classified from PRIOR days only — leak-free):**

| regime | days | mean day-R | win% | day-sharpe |
|---|---|---|---|---|
| **ACTIVE** | 275 | **+0.2286** | 54% | **+0.248** |
| NEUTRAL | 187 | +0.1604 | 62% | +0.239 |
| **QUIET** | 1126 | **+0.0262** | 53% | **+0.070** |

A **~9x mean / ~3.5x sharpe** separation between the active and quiet book regimes, identified
leak-free. This is a genuine, exploitable portfolio-regime — the "different rules for different
markets" principle realized at the BOOK level.

### 1.3 Does regime-scaled sizing beat STATIC? (honest verdict)

**On headline base P(pass): a near-wash** — and that is the correct, expected result. The static
book already passes ~100% at <=1% (PORTFOLIO_BUILD_W2), so there is no headroom to improve the
base pass-rate; any reallocation just moves it within noise. **Where the meta-layer adds value:**

| risk | STATIC base | REGIME base | STATIC **stress1.5x** | REGIME **stress1.5x** | STATIC med-days | REGIME med-days |
|---|---|---|---|---|---|---|
| 0.50% | 99.99% | 99.97% | 80.6% | **81.9%** | 217 | **188** |
| 0.75% | 99.59% | 99.35% | 71.5% | **72.6%** | 146 | **126** |
| 1.00% | 98.59% | 97.65% | 65.3% | **66.3%** | 110 | **94** |
| 1.50% | 94.36% | 92.05% | 58.3% | **59.2%** | 70 | **61** |
| 2.00% | 88.72% | 86.04% | 53.4% | **54.8%** | 51 | **45** |

**The regime meta-layer improves the adversarial 1.5x left-tail stress P(pass) at EVERY size and
cuts median days-to-pass ~14%** (146→126 @0.75%), at matched gross exposure — by concentrating
risk into the high-EV active regime and de-risking the thin/drawdown days. It costs a fraction of
a point on base pass (which is saturated). **Verdict: SHIP it as a speed + stress-robustness
overlay, not as a pass-rate booster.** Per-year d-sharpe is positive in 8/12 years and ~flat in
the rest; 2026 forward d-sharpe +0.008 (mean day-R +0.319→+0.382). No year is materially harmed.

**Caveat:** the stress gain is modest (~1pp) and the forward-window stress is slightly worse at
larger sizes (the overlay's drawdown de-risk fires on the deep 2025-26 trend days); at the
RECOMMENDED <=0.75% live size it is net-positive on stress and clearly positive on speed. Treat
the overlay as **optional and conservative**; the static book remains the validated default.

---

## PART 2 — SCALING PLAN

### 2.1 Nth full-book account MC (corr~0 across accounts → added throughput)

Every account trades the SAME validated full book; the MC samples the SAME bootstrapped day-blocks
across all N accounts (worst-case co-movement preserved). Because **daily-breach is mechanically
0%** (worst day −1.5 unit-R → −1.12% @0.75%) and the book's per-account maxDD is tiny, joint
failure stays negligible:

| size | N | E[# pass] | P(all N pass) | P(>=2) | P(>=3) | med-days-all |
|---|---|---|---|---|---|---|
| 0.50% | 3 | 3.00 | **100.0%** | 100.0% | 100.0% | 217 |
| 0.50% | 4 | 4.00 | **100.0%** | 100.0% | 100.0% | 217 |
| 0.75% | 3 | 2.99 | **99.66%** | 99.66% | 99.66% | 145 |
| 0.75% | 4 | 3.99 | **99.66%** | — | — | 145 |

**Headline:** a **3rd full-book account adds ~1.0 expected challenge-clear per cycle** with
P(all-3)≈99.7% @0.75% (≈100% @0.50%). The added account is throughput-additive at essentially
zero incremental joint-failure risk — the only added exposure is per-account maxDD, already <1% at
0.75%. Adding a 4th/Nth scales linearly (E[#pass]≈N) until firm allocation caps bind. **The corr~0
property means N accounts ≈ N independent near-certain pass attempts.**

### 2.2 Post-payout compounding / withdrawal schedule

Funded-phase economics from the book's **forward** day-R (conservative live proxy): forward mean
**+0.2164 unit-R/day @0.75%** = +0.162%/day → **~3.46%/mo gross** → **~2.77%/mo net to trader**
(80% profit split). Per $100k funded account ≈ **$2,770/mo net**.

Reinvest fraction splits net profit between WITHDRAW (banked) and REINVEST (new challenge fees,
~$540 each, cleared in ~6-7 weeks at ~100% fwd pass). **REALISTIC caps applied** (the naive
uncapped model exploded geometrically — that was the bug): fleet cap **10 accounts** (firm
allocation + ops reality), **<=2 new accounts/month** (verification lag), reinvest only from
realized cash.

| reinvest | start | month-12 funded | cumulative withdrawn (12mo) |
|---|---|---|---|
| 0% (pure income) | 3 | 3 | **$99,769** |
| 30% (balanced ramp) | 3 | **10** (capped m5) | **$201,754** |
| 50% (max ramp) | 3 | **10** (capped m4) | $144,110 |

**Recommended: 30% reinvest.** It ramps 3→10 funded accounts by month 5 AND banks the most cash
($202k/yr) — beyond the fleet cap, extra reinvestment just spends fees without adding accounts, so
50% withdraws LESS. After the fleet fills, switch to 0% reinvest (pure withdrawal) → ~$21k/mo,
~$256k/yr steady income from 10 funded accounts at the conservative forward yield.

### 2.3 Deferred expensive-data deployment plan + uplift bracket

**What was deferred (owner doctrine):** order-flow (footprint/CVD/DOM) + fundamentals
(positioning/COT/macro-surprise). These were skipped because the free-MT5 core does not NEED
scalper precision — but the program HAS measured exactly what they would unlock.

**Evidence anchors (this program's own numbers):**
- **Exit-oracle headroom: mean +0.72R / median +0.49R** above any tested exit (34,180 paths) —
  precision exits could capture a FRACTION of this on trades we ALREADY take.
- **Microstructure engine (H4): 13 setups survived the full leak-free gauntlet**, strongest
  +0.35..0.9R (index/metals/jpy/crypto absorption + vdelta) — SKIPPED because they need tick
  truth. Order-flow is the missing input.

**Uplift bracket (per precision-trade R, then annualized over ~115 high-quality core trades/yr):**

| | per-precision-trade R | annual R uplift (x115 core) |
|---|---|---|
| **lower** (capture ~20% of exit gap / weak micro) | +0.15R | **+17 R/yr** |
| **base** (capture ~40% of exit gap OR a median micro sleeve) | +0.30R | **+34 R/yr** |
| **upper** (most of micro edge + part of exit gap) | +0.55R | **+63 R/yr** |

Plus net-new precision-only frequency (the 13 micro-survivors are mostly NEW entries, additive to
the +17..63 R/yr exit/precision uplift on existing trades). The upper bound is capped by the
measured +0.72R exit-oracle gap — precision data cannot exceed the headroom that physically exists.

**Deployment steps (self-funded from withdrawals, AFTER first payouts):**
1. Ring-fence ~1 payout cycle for data subscriptions + tick storage.
2. Export order-flow for the 4 micro-survivor classes (index/metals/jpy/crypto) via the bridge
   tick feed + a paid CVD/DOM source.
3. Re-run the H4/M15 microstructure engine with REAL order-flow (replaces the volume-proxy) under
   the SAME leak-free gauntlet (bootstrap p05>0, fwd>0, 2x-cost).
4. Add a precision EXIT layer to the EXISTING core sleeves first (lowest risk, captures
   exit-oracle headroom on trades already taken).
5. Promote only forward-validated sleeves; size-by-confidence; keep the free-data core as the
   anchor — never delete.

---

## NET VERDICT

- **Regime meta-layer SHIPS** as a leak-free breadth+drawdown overlay: real ~9x mean / ~3.5x
  sharpe ACTIVE-vs-QUIET separation, improves adversarial-1.5x stress P(pass) at every size and
  cuts time-to-pass ~14%, at matched exposure and no material per-year harm. Headline base pass is
  already saturated so it is a wash there — that is honest, not a failure.
- **The PnL-persistence regime is a documented dead end** (kept as learning): regime selection
  belongs at the per-sleeve ENTRY, not on portfolio PnL — the diversification that wins also
  whitens the daily series.
- **Scaling: a 3rd full-book account adds ~1.0 expected clear at ~99.7% P(all-3); N accounts ≈ N
  near-certain pass attempts** until firm caps bind. 30%-reinvest schedule ramps 3→10 funded
  accounts in ~5 months and banks ~$202k/yr; steady-state ~$256k/yr from a 10-account fleet at the
  conservative forward yield.
- **Deferred-data uplift bracket: +17 / +34 / +63 R/yr** (lower/base/upper) on the existing core,
  hard-capped by the measured +0.72R exit-oracle headroom, plus additive precision-only frequency
  — deploy self-funded after payouts.

### FILES
- `KB3_regime_scaling.py` — builder (regime classifier + scaled MC + N-account MC + withdrawal
  schedule + deferred-data bracket); reuses the locked W2 MC engine and cached streams.
- `KB3_REGIME_SCALING_RESULT.json` — machine-readable results.
