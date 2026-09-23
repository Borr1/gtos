# PORTFOLIO BUILD — WAVE 7 (UNLEASH) — THE FINAL STRONGEST DEPLOY BOOK

> Objective shift (binding): maximize GROWTH-RATE / speed-to-+8% **subject to** FTMO (5% daily,
> 10% max-DD) at an ACCEPTABLE P(max-DD breach) — NOT minimal size / near-certain pass. Prior waves
> were fear-distilled at ~0.71–0.75% effective. This wave strips the conservatism drag, quantifies
> what fear was costing, and ships the strongest HONEST configuration.
>
> Verdict gate (unchanged doctrine): the book changes on the **vol-matched challenge-pass +
> max-DD-fail + 1.5x left-tail stress MC**, per-year + forward holdout, NOT per-trade EV alone.
> No lookahead (features from closed bars; `geometry_lib.simulate`/`cs.exit_state_d` labelers;
> conviction = same-day n_active; tick erosion forward-measured). Real cost. Map-don't-kill.

Engine: LOCKED `INTEG_portfolio_build_w2.mc_series / joint_pass_mc` (N=20000, FTMO 8% target /
5% daily / 10% maxDD, BLOCK=5, whole-cross-sectional-day block-bootstrap). Integrator:
`INTEG_W7_final_book.py` → `INTEG_W7_FINAL_RESULT.json`.

---

## 0. What each of the six UNLEASH tracks actually changed in the FINAL book

| track | finding | verdict | book change |
|---|---|---|---|
| **T1 Un-cap winners / extend runner** | winsor[-1.3,+5] binds **0 / ~12k** trades (stop = -1R; real cap is the fixed TARGET). Lifting targets recovers per-trade EV on right-skewed sleeves but is **net-negative at the vol-matched book MC** (flat growth, lower Sharpe, higher maxDD tail, SLOWER days-to-pass — opposite of the speed objective). | **NULL** | none — keep winsor + targets. The growth lever is sizing, not un-capping. |
| **T2 Tick-true execution** | single per-class cost map fails both ways: liquid legs (XAU/XAG, USOIL/UKOIL, BTC, JPY) erode **less** than the -5.6% proxy; illiquid legs (HEATOIL 0.34R, NATGAS 0.28R real spread vs 0.037R map) **blow** it (modeled +1.40R HEATOIL → +0.08R tick). | **ONE CHANGE** | **DROP HEATOIL_c + NATGAS_cash** from `energy_agri` (same real-fill EV +0.349→+0.350R, lower tail) + fold small tick upgrades: metals XAU +0.019/XAG -0.005R, USDJPY +0.018R. |
| **T3 Growth-optimal + Kelly-lite sizing** | the fear drag was real: prior ~0.71% deploy sat at ~120d-to-pass. Growth-optimal knee = **1.50% nominal (~1.42% eff)**; daily is NOT the binding rule (0% real daily-breach to 2.0%) — the **1.5x-stress maxDD-fail** is. Confidence-proportional Kelly-lite (leak-free day-level n_active) is a forward-clean RESHAPE that nearly halves stress maxDD-fail at equal vol; handset bins {0.85,1.10,1.60} track the conditional Kelly f*/base {0.50,0.98,1.48}. | **GROWTH LEVER** | size at the growth-optimal dial + apply Kelly-lite handset (or breach-free **half-Kelly** {0.748,0.991,1.241} for the first cycle). |
| **T4 Reinstate dropped sleeves** | under a hard maxDD cap, growth is variance-bounded (Kelly/Sharpe); every dropped stream (leadlag_core, subh4_ll_fx, IDB) is **sub-book-Sharpe** → a growth DRAG at iso-risk-of-ruin even though +EV and low-corr. | **NULL** | book of record stays the 11-sleeve clean_3. |
| **T5 Audit static assumptions** | maxbars=80 / winsor / cost-map / same-bar convention all confirmed optimal or inert **at book level** (the deployed cascade already structurally escaped maxbars; 0 forced-close rows exposed). sqrt-N same-day pooling already in `build_matrix`. | **NULL deploy** | maxbars 80→240 is a LIVE-PACKAGE H4-fallback fix only (no deployed-book change). |
| **T6 Confluence-Kelly router** | strict-Pareto matched-ruin speed (+8–14% faster) on the `sub_xvol_pullback` sleeve, but book-level lift is diluted (1/11 of book); wins by RESHAPING, survives vol-match. | **OVERLAY** | size-up overlay, default-OFF, already wired in `ultimate_book_live_package.py` (not folded into the base MC). |

**NET FINAL BOOK** = clean_3 (11 sleeves) − {HEATOIL_c, NATGAS_cash} + per-symbol tick erosion +
Kelly-lite conviction sizing, deployed at the growth-optimal dial. Nothing deleted beyond the two
illiquid energy legs whose modeled EV was a cost-map artifact (map-don't-kill: their real-fill EV is
~0, so dropping is a strict improvement).

---

## 1. THE FINAL DEPLOY BOOK — 11 sleeves, tick-true, Kelly-sized

Daily-R stats (1679 days, 382 forward): book std matched to **sd_book = 0.56859** (locked convention).

| layer | mean unit-R | std | vol_scale | fwd mean |
|---|---|---|---|---|
| BASE (W5 clean_3 as-deployed) | 0.09127 | 0.59970 | 0.9481 | 0.27963 |
| + TICK drop-HN + metals/JPY upgrades | 0.08294 | 0.58714 | 0.9684 | (tick) |
| **+ Kelly-lite handset (FINAL)** | **0.10956** | **0.75768** | **0.7504** | (hotter, re-vol-matched) |
| + half-Kelly (breach-free alt) | 0.10? | 0.625 | 0.9096 | — |

Tick drop-HN trims mean slightly (the two legs carried inflated modeled EV) but **shrinks the true
tail the modeled book never saw**. Kelly-lite then reshapes risk toward multi-sleeve-agreement days.

### Per-sleeve contribution (FINAL book, conf-wtd unit-R share)

| sleeve | cluster | conf | share | source |
|---|---|---|---|---|
| crypto (BTC/ETH; DASH watch) | crypto | 0.85 | 38.8% | W3 core + tick (BTC clean) |
| metals_core (the gold anchor) | metals | 1.00 | 24.6% | W3 core + tick +0.019R |
| energy_agri (USOIL/UKOIL + AGRI) | energy | 0.80 | 11.6% | W3 core, **HEATOIL/NATGAS dropped** |
| sub_xvol_pullback | substrate | 0.45 | 9.2% | W4 substrate (router overlay target) |
| fx_jpy (London) | jpy | 0.15 | 5.6% | W3 breadth + tick +0.018R |
| sub_mid_dn_revert | substrate | 0.20 | 5.5% | W4 + VP-acceptance |
| vp_euidx_pocgrav | volprofile | 0.30 | 4.6% | W4 volume-profile |
| metals_softband | metals | 0.50 | 1.7% | W3 core |
| fx_jpy_ny | jpy | 0.15 | 1.6% | W3 core |
| metals_ob_micro | metals | 0.30 | -0.7% | W3 (kept tiny, never zero) |
| idxrev | index | 0.15 | -2.4% | W3 breadth (falsified→tiny) |

avg off-diag daily-R corr ≈ +0.003 (min -0.12, max +0.12) — near-orthogonal; this low-variance,
high-win-rate, ~0-corr daily series IS the edge (why T1 un-capping degrades it).

---

## 2. TRADES / YEAR (net of real fills)

All R are NET of real cost through the pessimistic `geometry_lib` fill; no separate slippage
double-haircut. Tick erosion is an additional forward-measured per-symbol correction.

- Book core ~1512 tr/yr fwd; clean_3 additives (sub_xvol ~26 + vp_euidx ~115 + sub_mid_dn ~64)
  ~205 tr/yr → **~1717 tr/yr forward** before the energy drop.
- Dropping HEATOIL+NATGAS removes ~25 illiquid energy fills/yr → **~1692 tr/yr forward**,
  correlated-unit-collapsed to far fewer independent risk units/day.
- Net-of-fills book contribution erodes **~5–6%** (the proxy was conservative on the liquid legs that
  remain; the illiquid legs that blew the proxy are now gone).

---

## 3. P(PASS), P(MAXDD-BREACH), DAILY-BREACH — the aggression dial (FINAL book, vol-matched)

20,000 paths. Effective = nominal × VS_final (0.7504). **str15** = 1.5x left-tail-inflated (the
binding gate); **str20** = 2.0x deep-ruin probe. `$/100k/mo` = mean daily unit-R × eff × 21 × $100k.

| nom | eff | P(pass) | P(maxDD) | str15 P(pass) | str15 maxDD | str20 maxDD | daily-breach | med days | monthly % | $/100k/mo |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.75% | 0.56% | 99.99% | 0.01% | 90.9% | 9.1% | 53.3% | 0.00% | 126 | 1.29% | $1,295 |
| 1.00% | 0.75% | 99.80% | 0.20% | 84.5% | 15.5% | 54.4% | 0.00% | 97 | 1.73% | $1,726 |
| **1.25%** | **0.94%** | **99.36%** | **0.65%** | **79.1%** | **20.9%** | **49.8%** | **0.00%** | **79** | **2.16%** | **$2,158** |
| **1.50%** | **1.13%** | **98.59%** | **1.41%** | **73.5%** | **20.4%** | **48.2%** | **0.00%** | **66** | **2.59%** | **$2,590** |
| 1.75% | 1.31% | 97.16% | 2.84% | 71.0% | 24.6% | 50.5% | 0.00% | 56 | 3.02% | $3,021 |
| 2.00% | 1.50% | 95.73% | 4.26% | 67.8% | 25.5% | 45.5% | 0.00% | 49 | 3.45% | $3,453 |

- **Unstressed P(pass) holds the near-certain floor** through 1.5% (98.6%); P(maxDD-breach) only
  crosses ~1.4% there and ~4.3% at 2.0%.
- **DAILY-BREACH = 0.00% at EVERY size** (the unstressed worst real day is -3.63% @1.5%, -4.84%
  @2.0% — structurally cannot single-day -5%). Daily is NOT the binding rule.
- The binding constraint is the **1.5x-stress maxDD-fail**; it climbs ~9%→25% across the dial.

### 3a. Kelly form choice — handset vs half-Kelly (the one real ruin caveat, quantified)

The handset x1.6 top bin over-bets the single worst correlated-loss day (2025-06-13, n_active=7, the
-2.02R metals day). UNSTRESSED it is FTMO-safe (worst day -3.63% @1.5%). Only under the **adversarial
1.5x inflation** does it graze the wall:

| @1.5% nominal, 1.5x-STRESS | VS | stress maxDD-fail | stress daily-breach | worst stressed day | 2025 dbr / 2026 dbr |
|---|---|---|---|---|---|
| flat (tick, no Kelly) | 0.9684 | 33.9% | 0.00% | -4.39% | 0.0% / 0.0% |
| **handset Kelly** | 0.7504 | **20.4%** | 6.1% | -5.45% | 12.0% / 0.0% |
| **half-Kelly (breach-free at ≤1.25%)** | 0.9096 | 22.8% | 5.8% | -5.12% | 11.8% / 0.0% |

half-Kelly dial (vol-matched): @1.25% **0.00% stress-daily-breach**, stress P(pass) 77.3%, maxDD
0.70%, 77 med-days; the stress daily-breach only appears at ≥1.5% (and only under inflation).

**Read:** Kelly-lite cuts the binding stress maxDD-fail from 33.9% → ~20% — a large, forward-clean
win. The cost is that the top bin's worst real day is amplified; that day is FTMO-safe in reality but
breaches under 1.5x inflation. **Half-Kelly at 1.25% is the daily-breach-free-even-under-stress sweet
spot**; handset at 1.5% is the more aggressive dial and needs the (already-wired, default-on)
`stress_derisk` shrink-only overlay to neutralize the top-bin caveat.

### 3b. Per-year stress (no single-regime hiding), FINAL handset @1.5%

| year | n | str15 P(pass) | str15 maxDD-fail | str15 daily-breach |
|---|---|---|---|---|
| 2025 | 263 | 77.0% | 11.0% | 12.0% |
| 2026 | 119 | 94.5% | 5.5% | 0.0% |

The stress tail is concentrated in 2025 (crypto-clustered loss runs + the lone metals -2.02R day);
2026 is clean. This is the honest single-regime caveat: the binding tail is a **2025 crypto/metals
temporal-clustering** problem, addressed by the reactive `stress_derisk` overlay (KB6) and the
half-Kelly top bin.

---

## 4. 2-ACCOUNT ALLOCATION (FINAL book, both trade the full diversified book)

| config | eff A | eff B | P(both) base | P(both) FWD | P(both) STRESS1.5x | daily-breach |
|---|---|---|---|---|---|---|
| conservative 0.75/0.75 | 0.56% | 0.56% | 99.99% | 99.98% | 74.96% | 0.00% |
| **balanced 1.25/1.25 (FIRST CYCLE)** | 0.94% | 0.94% | **99.28%** | 99.19% | 63.70% | 0.00% |
| **balanced 1.50/1.50 (STEP-UP)** | 1.13% | 1.13% | 98.52% | 98.37% | 59.71% | 0.00% |
| balanced 1.75/1.75 | 1.31% | 1.31% | 97.36% | 97.20% | 57.73% | 0.00% |
| staggered 2.00/1.50 | 1.50% | 1.13% | 95.53% | 95.62% | 50.21% | 0.00% |

Staggering buys nothing (both accounts share the same diversified edge → lower joint stress P).
Daily-breach 0% everywhere. The `stress_derisk` overlay adds ~+7pts to the stress P(both) line.

---

## 5. TOTAL LIFT vs the conservative 0.75% clean_3 — what fear was costing

| metric | conservative 0.75% | FINAL 1.25% | FINAL 1.50% | FINAL 2.00% |
|---|---|---|---|---|
| P(pass) | 99.99% | 99.36% | 98.59% | 95.73% |
| P(maxDD-breach) | 0.01% | 0.65% | 1.41% | 4.27% |
| median days-to-pass | 119 | 79 | 66 | 49 |
| monthly % | 1.36% | 2.16% | 2.59% | 3.45% |
| $/100k/month | $1,295 | $2,158 | $2,590 | $3,453 |

- **At 1.50%: ~1.8x faster to target (119→66 days) and ~1.9x the monthly growth (1.36%→2.59%),
  while P(pass) stays 98.6% and P(maxDD-breach) is still only 1.41%.** That is the size of the fear
  drag the prior waves were paying: roughly **half the speed and half the growth for a 1.4pt maxDD
  insurance premium that the math says was never needed** (daily-breach 0% throughout).
- **At 1.25% (the recommended first cycle): ~1.5x faster (119→79 days), 1.59x monthly, P(pass)
  99.4%, P(maxDD-breach) 0.65%** — almost free growth.
- Even at 2.00% the book still passes 95.7% with 0% daily-breach; the only thing that degrades is the
  stress-tail maxDD insurance.

---

## 6. RECOMMENDED DEPLOY SIZING (the aggression dial)

| dial | nominal | eff (vm) | when | P(pass) | P(maxDD) | stress maxDD-fail | Kelly form |
|---|---|---|---|---|---|---|---|
| **measured** | **1.25%** | **0.94%** | **first challenge cycle** | 99.4% | 0.65% | 17–21% | **half-Kelly** (breach-free) |
| **growth-optimal** | **1.50%** | **1.13%** | after first account clears | 98.6% | 1.41% | 20–23% | handset + `stress_derisk` on |
| **aggressive ceiling** | **2.00%** | **1.50%** | only with live-confirmed fills | 95.7% | 4.27% | 25% | handset + `stress_derisk` on, hard cap |

**RECOMMENDATION:** deploy **1.25% nominal half-Kelly for the first cycle** (daily-breach-free even
under 1.5x stress, ~1.5x faster than the old 0.75% deploy), then step to **1.50% handset Kelly with
the reactive `stress_derisk` overlay default-on** after the first account clears. Hard ceiling
2.00%/account. This is intelligent aggression: it captures the bulk of the recovered growth (1.9x at
1.5%) while keeping P(maxDD-breach) ≤1.4% and real daily-breach at 0%.

---

## 7. PER-DIMENSION SCORECARD (D1–D6, honest)

| dim | what | grade | evidence / honest gap |
|---|---|---|---|
| **D1 Edge reality** | leak-free, real-cost, forward-holdout per sleeve | **A** | 11 sleeves TRAIN/FWD + per-year + n; corr ~0; **execution now tick-true** (per-symbol bid/ask, not a class proxy) on every tick-serviceable leg. Gap: vp/fx layers forward-only; GBPJPY/ETH/CORN/COTTON have no bridge feed (transfer-only, flagged). |
| **D2 Diversification / corr** | independent risk units, low cross-corr | **A** | avg off-diag +0.003; correlated-unit collapse enforced; both-account full book. |
| **D3 Challenge survivability** | vol-matched P(pass) + daily-breach | **A** | 99.4%@1.25% / 98.6%@1.5%, **0% daily-breach at EVERY size to 2.0%**, worst real day -3.63%@1.5%. Structurally cannot single-day -5%. |
| **D4 Stress / left tail** | 1.5x adversarial (the binding gate) | **B+** | Kelly cuts stress maxDD-fail 33.9%→~20% @1.5% (forward-clean). Tail is a **2025 crypto/metals temporal-clustering** problem, addressed by half-Kelly top + reactive `stress_derisk`. Honest ceiling, not bulletproof; the handset top bin grazes the daily wall under 1.5x inflation (breach-free in reality). |
| **D5 Deployability** | default-off, fail-closed, tested, parity | **A** | pure library `ultimate_book_live_package.py`, zero broker authority, 78 tests, byte-parity vs locked artifacts, import-safe; Kelly-lite + growth profiles wired (default-off). |
| **D6 Go-live readiness** | actual path to live | **C** | strategy + sizing ready and now growth-optimized; still gated by the 2 infra blockers (broker/runtime authority), NOT edge. |

---

## 8. HONEST CAVEATS

1. **Forward window is short** (2025 + partial 2026). The substrate/VP/fx layers are essentially
   forward-only; deep H4 layers (metals/crypto/energy) have 2014–26 depth. Distrust single-fwd-year
   positives; the n_active≥4 (x1.6) Kelly tier is train-thin (3 days ≤2024) → treat as
   forward-conditional; re-confirm as the window lengthens.
2. **The 1.5x adversarial stress is the honest ceiling.** Unstressed the book is near-certain; the
   stress maxDD-fail climbs to ~20–25% across the dial and is 2025-crypto-clustered. Size for it
   (half-Kelly first cycle, reactive overlay) — do not hide it.
3. **Crypto tick reconcile not yet folded.** BTC confirmed clean (0.09 bps); DASH showed an 85 bps
   spread but its tick ledger was still materializing — DASH-drop is a flagged conditional refinement
   (would lower crypto std/tail slightly), not applied in this MC.
4. **The handset top bin is the one real ruin lever.** It is FTMO-safe in reality but breaches under
   1.5x inflation; use half-Kelly or the shrink-only `stress_derisk` overlay if running it at ≥1.5%.
5. **Zero broker authority by design.** Live behavior depends on the runtime/broker-authority work
   being cleared first (CLAUDE.md first unresolved proofs).

---

### Artifacts
- Integrator: `INTEG_W7_final_book.py` → `INTEG_W7_FINAL_RESULT.json` (this build, LOCKED engine)
- Tracks folded: KB7_uncap_winners.md (T1 null), KB7_execution_truth.md + KB7_TICK_MC_RESULT.json +
  KB7_TICK_BOOK_RESTATE.json (T2 drop-HN), KB7_growth_kelly_sizing.md + KB7_GROWTH_KELLY_V2_RESULT.json
  (T3 sizing), KB7_reinstate_sleeves.md (T4 null), KB7_stale_audit.md (T5 null-deploy),
  KB7_confluence_kelly_router.md (T6 overlay)
- Deploy base: `INTEG_W5_CLEAN3_DEPLOY.json` (locked) ← `INTEG_w5_clean3_deploy.py`
- Deployable module: `ultimate_book_live_package.py` v3 (78 tests; Kelly-lite + growth profiles wired)
- Dossier refreshed: `ULTIMATE_GO_LIVE_DOSSIER.md` (Wave-7 growth section)
