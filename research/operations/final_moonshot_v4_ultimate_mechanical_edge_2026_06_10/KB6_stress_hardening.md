# KB6 — Stress-harden the book: raise the binding 1.5x left-tail stress P(pass)

Track: **stress-hardening of the clean_3 deploy book**. Status: **improvement** (two
forward-validated, vol-matched de-risk overlays raise the binding 1.5x-stress P(pass) by
**+6.6 pts** (reactive-only, forward-clean) to **+11.0 pts** (full stack), while *raising*
Sharpe and holding base P(pass) at ~100% — nothing deleted, nothing de-levered).

Builder: `KB6_diagnose.py` (tail attribution), `KB6_mitigations.py` (single-overlay sweep),
`KB6_combine.py` (combinations + per-year/forward + 2-account deploy MC), shared
`KB6_stress_lib.py`. Machine results: `KB6_MITIGATIONS_RESULT.json`, `KB6_COMBINE_RESULT.json`.

**Engine = the LOCKED W2 MC** (`INTEG_portfolio_build_w2.mc_series`): block-bootstrap whole
cross-sectional days, BLOCK=5, N=20000, TARGET 8% / DAILY 5% / MAXDD 10%. **Every mitigation
is judged VOL-MATCHED** (each scaled series is gross-exposure-normalized by its own average
multiplier, then re-vol-matched to the W3 book std exactly as the deploy book is) — so a
mitigation can NEVER win by de-levering; the only thing compared is *where* risk sits in time.
Leak-free: every overlay multiplier on day `t` uses ONLY realized days `< t`.

**Baseline reproduction is exact** — clean_3 vol-matched: vol_scale 0.9481, Sharpe 0.1522,
stress **80.86% @1%** / **70.93% @1.5%**, matching `INTEG_W5_CLEAN3_DEPLOY.json` to 4 dp.

---

## 1. DIAGNOSIS — what concentrates the 1.5x left tail (WHERE/WHEN, no averages)

The stress inflates losing days ×1.5; the worst block-bootstrap paths are **runs of clustered
loss days** that compound into a >10% maxDD. Decomposition of clean_3 (1679 days):

| finding | evidence |
|---|---|
| **Crypto drives the deep tail** | On the **worst 5% of book-loss days (n=40), crypto = 49.4%** of the loss mass (metals_core 17.5%, energy_agri 15.3%). Crypto fires only 34 neg-days but each conf-weighted loss is ≈ **−0.93 unit-R** (0.85×−1.1R), the single deepest sleeve-day loss in the book. |
| **The tail is CLUSTERED, not single-day** | Failure mode is **100% maxDD, ~0% daily-breach**. The worst MC-failing paths are built from *consecutive* crypto loss days: **2025-11-06…11 (4 crypto −0.93 days in a week)** and **2026-04-23…28**, plus the lone **2025-06-13 −2.02 metals day**. Max consecutive book-loss run = 8 days; worst 5-day rolling sum (stressed) = −4.45 unit-R. |
| **Forward years carry the deepest single days** | per-year worst day: 2025 **−2.02**, 2026 **−1.08** vs ≤−1.09 in train years — the recent regime has the fattest individual left tail (deep-trend reversals), so the tail is forward-real, not a train artifact. |
| **High breadth is usually protective but not always** | breadth-5 days mean **+0.98R**; but a breadth-7 day can still print **−2.02** (broad adverse co-move). Co-firing helps the mean, not the deep tail. |

**Implication:** the tail is a **temporal-clustering** problem (de-risk the days *around*
clustered losses), NOT a per-trade-size problem. This is why the vol-target mitigation fails
(below) and the temporal overlays win.

---

## 2. MITIGATION SWEEP (single overlays, vol-matched, locked MC) — Δ stress-P(pass) vs baseline

| mitigation | Sharpe | Δstress @0.75% | @1.00% | @1.50% | verdict |
|---|---|---|---|---|---|
| **(a) W3 breadth+drawdown regime overlay** | 0.1548 | **+5.1** | **+4.7** | **+5.8** | strong full-history; **forward-flat/slightly−** (caveat below) |
| **(d) 3-step daily de-risk ladder** (1.0/0.80/0.60) | **0.1554** | +3.5 | +3.0 | +3.0 | reactive, **forward-positive**, simplest to wire |
| **(b) co-loss circuit breaker** (W5/neg-frac≥0.57/×0.60) | 0.1554 | +4.8 | +3.9 | +4.5 | reactive, **forward-positive** |
| **(c) per-sleeve vol-target (crypto / top-3 cap)** | 0.1522 | +0.6 | −0.2 | +1.0 | **NULL — cap never binds (learning)** |

**(c) is a documented dead end.** Crypto's TRAIN per-sleeve std is **1.81** (inflated by a few
+3.87 winners), so even a `k=1.0×std` left-tail cap (−1.81) never clips the actual worst
crypto loss (−0.93). You cannot shrink crypto's tail with a static vol budget without also
shrinking the +EV that produced the wide std — and the tail isn't single fat days anyway, it's
the *clustering* of ordinary −0.93 days. **Lesson: tail-cap the TIME dimension, not the
per-sleeve size.** (A MAD-based cap was checked and is equally non-binding.)

The W3 regime overlay's lift on clean_3 (**+4.7 @1%**) is **~5× larger than the ~1pp it gave on
the W2 book** (KB3) — the three new breadth additives (xvol/vp/mid_dn) sharpen the breadth
signal the classifier keys on.

---

## 3. COMBINATIONS (vol-matched) — stacking the reactive de-riskers compounds the lift

| overlay | Sharpe | base@1% | **stress @1%** | Δ@1% | stress @1.5% | Δ@1.5% |
|---|---|---|---|---|---|---|
| BASELINE clean_3 | 0.1522 | 99.90% | 80.86% | — | 70.93% | — |
| regime | 0.1548 | 99.95% | 85.57% | +4.7 | 76.70% | +5.8 |
| **ladder+coloss (reactive-only, NO regime)** | **0.1564** | 99.92% | **87.48%** | **+6.6** | **77.60%** | **+6.7** |
| regime+ladder | 0.1567 | 99.96% | 89.34% | +8.5 | 79.19% | +8.3 |
| regime+coloss | 0.1567 | 99.97% | 89.13% | +8.3 | 80.50% | +9.6 |
| **regime+ladder+coloss (full stack)** | **0.1568** | 99.98% | **91.86%** | **+11.0** | **83.09%** | **+12.2** |

Full-stack **seed-robustness (5 seeds): 91.5–92.4% @1%, 82.8–83.3% @1.5%** — stable, not a
lucky seed. Base P(pass) and Sharpe both *improve* in every combo (de-risking clustered loss
days reallocates that risk into ACTIVE days → higher risk-adjusted return at matched gross).

---

## 4. FORWARD-HOLDOUT — the load-bearing distrust check (the regime piece is NOT forward-clean)

Per doctrine (distrust forward-only / full-history-only; demand per-year + forward), I split
the stress P(pass) onto the **forward 2025-26 window (n=382)** alone:

| overlay | FWD stress @1% | @1.5% | reads |
|---|---|---|---|
| **regime ALONE** | **−0.4** | **−0.9** | **forward-NEGATIVE** — its full-history lift leans on de-risking the deep *historical* tail; on the short forward window its drawdown-de-risk fires on the live deep-trend days and costs slightly (the exact caveat KB3 flagged). |
| ladder | +1.1 | +1.7 | forward-positive |
| co-loss | +1.7 | +2.8 | forward-positive |
| ladder+coloss | +2.0 | +3.5 | **forward-positive** |
| regime+ladder+coloss | +1.7 | +2.9 | **forward-positive** (reactive components carry the forward window) |

Per-year @1% stress: regime helps 2021/2024, hurts 2019/2020/2022/2023. The **reactive
de-riskers (ladder, co-loss) are positive on the forward window by construction** — they trim
size *after* a realized loss/co-loss spike, a mechanism that does not depend on a fitted regime
map and therefore generalizes. The regime classifier is a full-history optimizer that is
forward-flat at best.

---

## 5. 2-ACCOUNT DEPLOY MC under the overlay (the real go-live decision)

Both accounts trade the full clean_3 book (diversification is WITHIN each account), vol-matched
effective sizes, regime overlay applied:

| config | P(both) base | **P(both) STRESS** base→regime |
|---|---|---|
| **balanced 0.71%/0.71%** | 99.99% → 100.00% | **70.30% → 77.36% (+7.1)** |
| conservative 0.47%/0.47% | 100.00% → 100.00% | **79.51% → 86.99% (+7.5)** |
| staggered 0.95%/0.71% | 99.88% → 99.93% | 59.97% → 67.02% (+7.1) |

The balanced 2-account stress P(both) — the single most binding deploy number — rises **+7.1
pts** under the regime overlay and proportionally more under the full stack. 0% daily-breach is
preserved at all sizes (de-risking only lowers exposure on bad days).

---

## 6. RECOMMENDATION — the most stress-robust deployable allocation

**Allocation: keep the clean_3 11-sleeve deploy book unchanged** (nothing deleted, no sleeve
re-weighted — the W5 selection stands). **Add a leak-free, default-on TEMPORAL de-risk
overlay.** Two tiers, by owner risk appetite:

1. **PRIMARY (forward-clean, recommended for the first live cycle):**
   **ladder+coloss reactive overlay** — 3-step daily ladder (after 1/2+ consecutive book-loss
   days, size next day ×0.80 / ×0.60; reset on a green day) ∧ co-loss circuit breaker (when the
   trailing-5-day cross-sleeve negative-firing fraction ≥ 0.57, size that day ×0.60). No regime
   classifier → no fit risk. **Stress @1% 80.86%→87.48% (+6.6), forward-positive (+2.0 @1%),
   Sharpe 0.1522→0.1564, base ~100%.**

2. **AGGRESSIVE (max full-history stress robustness, once the first account clears):**
   add the **W3 breadth+drawdown regime overlay** on top → full stack. **Stress @1%
   80.86%→91.86% (+11.0), @1.5% +12.2, forward-positive (+1.7 @1%), Sharpe 0.1568.** Caveat:
   the regime component's marginal value is full-history, not forward — deploy it only after the
   reactive layer is proven live, and re-validate it as the forward window lengthens.

**The mitigation that works: temporal de-risking after realized loss-clustering** (ladder +
co-loss breaker), optionally regime-concentration on top. **The mitigation that does NOT work:
per-sleeve static vol-targeting** (the tail is clustered ordinary losses, not single fat days).

Sizing-by-confidence is preserved (the overlay is a day-level size multiplier on top of the
fixed sleeve confidence weights). All overlays are wired as multipliers in `KB6_combine.py`
(`regime_mults`, `ladder_mults`, `coloss_mults`) ready to port into the live sizer.

---

## 7. Next steps (build queue)

1. **Wire the ladder+coloss overlay into the live sizer** as a default-on day-level multiplier
   alongside the clean_3 sleeve weights; regenerate the go-live dossier at balanced
   0.71%/0.71% with the overlay-on stress numbers.
2. **Re-validate the regime overlay as the forward window grows** (it is forward-flat today;
   if 2026-27 data confirms the breadth separation forward, promote tier-2 to default).
3. **Tune the co-loss threshold on a rolling basis** — it currently uses a fixed neg-frac 0.57;
   a trailing-quantile trigger may capture the forward-clean lift with fewer false de-risks.

### FILES
- `KB6_stress_lib.py` — clean_3 matrix reconstruction + locked-MC grid helper.
- `KB6_diagnose.py` / (console) — tail attribution (crypto 49% of worst-day mass; clustering).
- `KB6_mitigations.py` + `KB6_MITIGATIONS_RESULT.json` — single-overlay vol-matched sweep.
- `KB6_combine.py` + `KB6_COMBINE_RESULT.json` — combinations, per-year, forward-holdout,
  2-account deploy MC under the overlay.
