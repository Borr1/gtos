# KB7 — Un-cap winners + extend runner horizon (UNLEASH wave)

**Track question:** how much are the `[-1.3,+5]` net-R winsorization cap and the `maxbars=80`
force-close UNDERSTATING the right-skewed edge? Re-label all deploy sleeves with higher/no winsor
ceiling and extended maxbars; re-derive per-sleeve forward EV + the book MC under the un-capped
labels. Honest counter-check: confirm the cap is not hiding fat LOSSES.

**Headline verdict (forward-validated, book-MC-gated):** the cited cap is a MISDIAGNOSIS, and
acting on the *real* cap (the fixed target) is a NET NEGATIVE for this wave's objective.
1. The `+5` winsor **ceiling never binds** (0 of ~12k deploy trades reach +5). The `-1.3` floor
   never binds either — the structural stop is exactly `-1R`, so the cap is NOT hiding fat losses.
   The winsor number is dead weight; un-capping it is a literal no-op.
2. The real right-tail cap is the **FIXED TARGET geometry** (substrate 3R; metals/crypto/energy
   vol-banded 4/3/2.5R; leadlag 1.5/2R) + `maxbars` force-close.
3. Lifting targets DOES recover per-trade EV on the right-skewed sleeves (sub_xvol_pullback,
   sub_mid_dn_revert, subh4_ll_fx, crypto) — but it **lowers win-rate, raises variance, and at the
   LOCKED book MC it REDUCES P(pass), RAISES P(max-DD), CRATERS the 1.5x-stress pass-rate, and makes
   median days-to-pass SLOWER.** It is the wrong lever for "maximum growth-rate subject to FTMO".
4. metals_core and energy_agri are **already at their forward-optimal target** — higher targets
   monotonically DEGRADE their forward EV. The current geometry is honest there.

Per the doctrine: this verdict comes from the vol-matched challenge-pass + max-DD MC, not per-trade
EV. No lookahead (geometry_lib pessimistic exits on CLOSED bars), forward holdout, real cost,
per-year reporting throughout.

---

## 1. The cap-binding diagnostic (UNCAP_cap_binding_diag.py) — winsor is dead

Measured on the locked deploy streams (`INTEG_W3_streams_cache.pkl` + `INTEG_W5_new_streams_cache.pkl`):

| sleeve | n | max R | at +5 ceil | >=4R | at -1.3 floor |
|---|---|---|---|---|---|
| metals_core | 131 | 2.99 | 0 | 0 | 0 |
| metals_softband | 70 | 2.70 | 0 | 0 | 0 |
| crypto | 104 | 3.90 | 0 | 0 | 0 |
| energy_agri | 162 | 2.75 | 0 | 0 | 0 |
| idxrev | 6473 | 0.71 | 0 | 0 | 0 |
| fx_jpy / fx_jpy_ny | 530 / 197 | 2.39 | 0 | 0 | 0 |
| sub_xvol_pullback | 90 | 2.96 | 0 | 0 | 0 |
| vp_euidx_pocgrav | 341 | 4.81 | 0 | 3 | 0 |
| sub_mid_dn_revert | 398 | 2.96 | 0 | 0 | 0 |
| leadlag_core | 3115 | 3.94 | 0 | 0 | 0 |
| subh4_ll_fx | 357 | 3.89 | 0 | 0 | 0 |

**Zero trades anywhere reach the +5 ceiling or the -1.3 floor.** Code proof:
`geometry_lib.simulate/simulate_detail` return the raw R uncapped; the only ceiling that bites is the
`target_dist` (or `runner_R`) passed in. With fixed targets <= 4R, the realized R is bounded by the
target, far below +5. The "winsor caps the right tail" hypothesis is FALSE as stated.

## 2. Per-sleeve relabel under higher targets + extended maxbars (UNCAP_relabel_study[2].py)

Re-replayed identical leak-free entries across target ceilings {base, 6, 8, 12, none} x maxbars
{1x, 2x, 3x} + let-run trail variants. Per-year forward (FWD = 2025+2026):

**metals_core (n=131, FWD MFE median 2.71R; only 8/49 reach 6R, 3 reach 8R):** the 4R target is
already at/above the runner sweet spot. Forward EV MONOTONICALLY DEGRADES with higher targets:
- T4 (deploy): **+0.807R fwd** (43% win) — the optimum
- T6: +0.669 | T8: +0.299 | T12/none: -0.071 (2026 craters to -0.876)
- best trail (arm2/gap1): +0.745 (67% win) — close, not better. **No recovery; cap is not understating.**

**energy_agri (n=402, FWD MFE median 1.51R; 24 reach 8R, all concentrated in 2026):**
- T4 (deploy): **+0.508R fwd** — the optimum
- T6: +0.249 | T8: +0.077 | T12/none: negative. Higher targets help 2026 (+1.52->+1.76) but crater
  2025 (+0.06->-0.42); net forward NEGATIVE. **No forward recovery.**

**crypto carrier (n=36; FWD n=23, 2026 only n=4):** T6_mb2x +0.460 -> **+0.596R fwd (+0.14R)**.
Real but tiny and sample-starved (2026 negative, n=4). Marginal.

**sub_xvol_pullback (n=90, FWD MFE median 4.32R; 24/51 reach 8R — strongly right-skewed):**
- T3 (deploy): +1.609R fwd (67% win)
- **T6_mb1x: +2.468R fwd (+0.86R, +53%)**, both fwd years up (2025 +2.13->+3.60, 2026 +0.85). Per-trade
  Sharpe 0.855->0.895 — the ONE sleeve where the target genuinely understated the edge.

**sub_mid_dn_revert (n=398, FWD MFE median 4.66R; 18 reach 12R):**
- T3 (deploy): +0.495R fwd | **T12_mb2x: +1.222R fwd (+0.73R)**, both fwd years up (2025 +1.24, 2026
  +1.20). BUT TRAIN goes NEGATIVE (-0.232) and win-rate collapses 40%->20%.

**subh4_ll_fx (n=357, FWD MFE median 11.04R(!), 24/56 reach 12R):**
- T4 (deploy): +0.760R fwd | **T12_mb2x: +1.903R fwd (+1.14R, +150%)** — BUT TRAIN flat (+0.026),
  2026 NEGATIVE (-1.115, n=11), all EV on 2025 (n=45). Single-regime, forward-concentrated,
  win-rate 38%->23%. Classic right-tail over-fit trap; not trustworthy.

Universal pattern: higher targets trade win-rate + Sharpe for a fatter, lumpier right tail.

## 3. Book-level verdict on the LOCKED MC engine (UNCAP_book_mc.py) — the un-cap HURTS

clean_3 deploy book (11 sleeves), vol-matched, `mc_series` N=20000, 8%tgt/5%daily/10%maxDD/block5.
Swapped relabeled streams into the right-skewed sleeves, kept every entry/date identical.

| variant | sharpe | fwd daily mean | P(pass)@1% | P(maxDD)@1.5% | stress@1% | med_days@1% |
|---|---|---|---|---|---|---|
| **baseline (current targets)** | **0.1522** | +0.27963 | **99.90%** | **1.49%** | **80.86%** | **89** |
| xvol->T6 only (best-case isolated) | 0.1502 | +0.28851 | 99.83% | 1.77% | 80.04% | 91 |
| Policy A (xvol T6 + mid T8) | 0.1299 | +0.28013 | 99.40% | 3.77% | 67.26% | 100 |
| Policy B (xvol T6 + mid T12 mb2x) | 0.1189 | +0.27512 | 98.68% | 5.87% | 59.07% | 107 |

Every un-cap policy is strictly worse on the metrics that decide this wave's objective:
- **Forward growth-rate (daily mean) is FLAT** (+0.2796 -> +0.2801 best case). The recovered per-trade
  R does not translate into book-level growth, because the new variance is vol-matched back out.
- **Speed-to-target gets WORSE**: median days-to-pass @1% goes 89 -> 91 -> 100 -> 107. The lumpier
  series compounds SLOWER, not faster — the opposite of the UNLEASH objective.
- **P(max-DD breach) RISES** (the one real guardrail): @1.5% 1.49% -> up to 5.87%; @2% 4.25% -> 10.85%.
- **1.5x-stress pass-rate craters**: @1% 80.86% -> 59.07%.

Even the single cleanest swap (sub_xvol T6 only, both-fwd-years-positive, better per-trade Sharpe) is
a wash-to-negative at the book: +3% forward growth bought with higher max-DD, lower stress, slower
days. Not worth it.

## 4. Why uncapping fails the growth objective (mechanism)

The MC compounds resampled whole-day rows and vol-matches each book to the same daily std. Growth
rate ~ (mean / variance) under compounding, and the FTMO max-DD constraint penalizes the left/lumpy
tail. Lifting a fixed target converts many +2-3R high-probability winners into a few +6-12R lottery
tickets with more give-backs and lower hit-rate. That raises raw mean a little but raises variance
MORE, so vol-matched mean (the growth-relevant quantity) is flat-to-down and the max-DD tail worsens.
The deploy book's edge is its HIGH WIN-RATE / LOW-VARIANCE daily series and ~0 cross-sleeve corr;
un-capping degrades exactly that property. The right-skew the targets "chop" is real but it is NOT
free growth under the FTMO constraint — it is variance the vol-match gives straight back.

## 5. Recommendation (honest, ship-or-not)

**Do NOT change the winsor or raise targets in the deploy book.** Specifically:
- Keep `metals_core` 4/3/2.5R and `energy_agri` 4R — they are at their forward optimum.
- Keep `sub_xvol_pullback` 3R, `sub_mid_dn_revert` 3R, `subh4_ll_fx` 1.5/2R, `crypto` 4R — the
  per-trade EV recovered by higher targets does not survive the book max-DD/speed gate.
- The `wins()` `[-1.3,+5]` winsor can stay (it is harmless; it only protects against a hypothetical
  stitch spike) — but it is NOT a binding edge constraint and removing it would change nothing.

**The honest growth lever is NOT the cap.** Other UNLEASH tracks (sizing toward ~1.5%/unit;
correlated-risk-unit relaxation; the breadth/drawdown speed overlay from KB3 that cut days-to-pass
~14% at matched exposure) move the speed-to-target needle; un-capping winners moves it backwards.

**One genuinely-positive micro-finding to hand off (not deployed here):** `sub_xvol_pullback` is
strongly right-skewed (MFE median 4.32R, 24/51 fwd trades reach 8R) and a T6 target gives it a better
STANDALONE per-trade Sharpe (0.895 vs 0.855) with both fwd years up. If a future wave runs this sleeve
in an ISOLATED higher-allocation account (where its variance is not vol-matched against the low-var
book), the right tail could be worth harvesting. Inside the diversified clean_3 book it is not.

## Artifacts
- `UNCAP_cap_binding_diag.py` — proves winsor non-binding (reads locked caches).
- `UNCAP_relabel_study.py` / `UNCAP_RELABEL_RESULT.json` — metals_core, crypto, energy, sub_xvol relabel grid + MFE.
- `UNCAP_relabel_study2.py` / `UNCAP_RELABEL_RESULT2.json` — subh4_ll_fx, sub_mid_dn_revert relabel grid + MFE.
- `UNCAP_book_mc.py` / `UNCAP_BOOK_MC_RESULT.json` — book-level LOCKED MC verdict (baseline vs Policy A/B).
- `UNCAP_relabel_streams.pkl` — cached relabeled per-trade streams.
