# KB5 — Fold the 4 new Wave-4 sleeves into the book (true-corr MC)

Track: **fold_new_sleeves** (Wave-5 integrator). Builder pass 2026-06-15.
Engine: `KB5_fold_new_sleeves.py` -> `KB5_FOLD_RESULT.json`. Reuses the tested
materializers (`SUBSTRATE_corrcheck.materialize_cell`, `VP_confluence`/`volume_profile`,
`leadlag.mine_pair`) and the W3 true-corr + diversification-aware MC engine
(`INTEG_portfolio_build_w3` -> `INTEG_portfolio_build_w2.build_matrix/mc_series/joint_pass_mc`).

Doctrine: build & improve, never kill; map WHERE/WHEN; per-YEAR not averages; no lookahead
(features index<=i, `geometry_lib.simulate` forward-only labeler, real `w1.cost_for`); forward
holdout mandatory; size by confidence; additivity proven by TRUE daily-R correlation, not asserted.

---

## 0. Headline verdict

All 4 new Wave-4 sleeves pass the **independence** gate — every one is near-zero correlated to
the existing 8-sleeve W3 book (|corr vs combined| <= 0.049, max single-sleeve |corr| <= 0.056)
AND forward-positive. But **low correlation + positive EV is necessary, not sufficient.** The
portfolio-level vol-matched MC + per-sleeve ablation splits them:

- **3 CONFIRMED ADDITIVE -> FOLD:** `sub_xvol_pullback` (conf 0.45), `vp_euidx_pocgrav` (0.30),
  `sub_mid_dn_revert` (0.20). Together they lift the book's daily Sharpe **0.131 -> 0.146 (+12%)**,
  hold the unstressed P(pass) at book level (99.85%), and **preserve the adversarial 1.5x stress
  tail essentially intact** (81.8% vs book 82.6% @1%), adding **+205 low-corr trades/yr** in the
  index/EU-index/metals/energy/fx classes the core under-weights. **This is the deploy book.**
- **1 DROPPED (learning):** `leadlag_core` (conf 0.30). It passes correlation (+0.028) and is
  forward-positive (+0.16R), but it is **portfolio-DILUTIVE**: its per-trade Sharpe (0.119) is
  BELOW the book's, and at ~416 trades/yr / 28% win it injects a fat left tail that drags the
  1.5x-stress pass-rate from **82.6% -> 49.4%** at matched vol. Demote to breadth conf ~0.10 (a
  valid secondary book) or hold out entirely (the recommended deploy).

ETH double-count is real and handled: the BTC->ETH leadlag leg roughly **doubles** the
leadlag-vs-crypto correlation (+0.036 -> +0.090) because ETHUSD is already a crypto carrier.
`leadlag_core` was materialized **without the ETH leg**.

**Deploy rule:** fold the 3 clean sleeves AND drop the per-account risk multiplier by the
vol_scale (~0.93x for clean_3) so per-day risk stays identical to the current book — banking the
diversification credit as a higher unstressed P(pass) floor + deeper forward edge with no tail
cost. Daily-breach stays 0.000% at every tested size.

---

## 1. The 4 new sleeves — materialized leak-free streams (per-year, forward holdout)

| sleeve | conf | source | n | TRAIN EV (n) | FWD EV (n) | fwd win | ~tr/yr fwd | per-year forward |
|---|---|---|---|---|---|---|---|---|
| **sub_xvol_pullback** | 0.45 | substrate cell (metals/energy/index/fx) | 90 | +0.752 (39) | **+1.609 (51)** | 67% | ~26 | 2025:+2.13(30) 2026:+0.86(21) |
| **vp_euidx_pocgrav** | 0.30 | VP GER40+UK100 POC-grav far>=2.0 vr>=1.2 | 341 | +0.218 (111) | +0.242 (230) | 35% | ~115 | 2024:+0.22 2025:+0.05 2026:+0.48 |
| **leadlag_core** (no ETH) | 0.30 | leadlag GOLD core (idx spillover, US30->JPY, JPY rev) | 3115 | +0.100 (2282) | +0.161 (833) | 28% | ~416 | 2024:+0.04 2025:+0.25 2026:-0.03 |
| **sub_mid_dn_revert** | 0.20 | substrate cell (NY mid-vol dn revert long) | 398 | +0.088 (269) | +0.495 (129) | 40% | ~64 | 2024:+0.13 2025:+0.52 2026:+0.44 |

All leak-free (features index<=i, outcome window i+1.., real cost, R winsorized [-1.3,+5]).
`sub_xvol_pullback` is the regime-lumpy flagship: train EV concentrates in 2020 (COVID vol,
n=25 +1.31) and calm train years (2022-24) are thin & slightly negative — a high-payoff
**elevated-vol breadth** stream, hence conf 0.45 not higher. `leadlag_core` 2026 leg is flat-to-
slightly-negative (index-spillover regime decay, the documented KB4 watch) — carried at conf 0.30.

---

## 2. TRUE cross-sleeve daily-R correlation (the load-bearing additivity proof)

Each new sleeve materialized into a real daily-R stream and Pearson-correlated vs each of the 8
W3 sleeves AND the combined book (union-0fill, the book's diversification convention) over 1,599
book days. The existing W3 book avg off-diag corr is +0.005.

| new sleeve | corr vs combined (union0) | corr vs combined (intersect) | max \|single-sleeve corr\| | top sleeve corrs |
|---|---|---|---|---|
| sub_xvol_pullback | **-0.012** | -0.207 | 0.049 | metals_softband -0.049, idxrev +0.026 |
| vp_euidx_pocgrav | **+0.049** | +0.077 | 0.053 | idxrev +0.053, crypto +0.035 |
| leadlag_core (no ETH) | **+0.028** | +0.040 | 0.038 | fx_jpy_ny +0.038, crypto +0.036 |
| sub_mid_dn_revert | **-0.023** | -0.066 | 0.056 | fx_jpy -0.056, energy_agri +0.040 |

**Every sleeve clears the independence bar with huge room** (gate |corr|<0.10; all <=0.049).
sub_xvol_pullback's intersect corr is strongly NEGATIVE (-0.21) — on days both fire it leans
AGAINST the book = a true diversifier, not a relabel. **Folded book avg off-diag corr stays
+0.0025** (essentially unchanged from the book's +0.005), confirming the additions don't cluster.

### ETH double-count (the explicit watch)
| leadlag variant | corr vs crypto sleeve | fwd EV |
|---|---|---|
| leadlag_core **without** ETH leg | **+0.036** | +0.161 |
| leadlag_core **with** ETH leg | +0.090 | (inflated) |

The BTC->ETH leg ~doubles the crypto correlation (ETHUSD is already a crypto carrier). **Shipped
without ETH** — index-spillover + US30->USDJPY + USDJPY->{AUDJPY,GBPJPY} reversion only.
(Index-spillover is opposite-sign to the idxrev FADE sleeve = complementary regime coverage,
visible as the +0.05/-0.03 idxrev cross-corrs.)

---

## 3. Additivity verdict & the upgraded book

**Correlation gate (independence):** all 4 pass (|corr vs combined|<0.10, all forward-positive).
**Portfolio gate (vol-matched Sharpe + 1.5x tail, Sections 4-5):** 3 pass, leadlag_core fails.
-> **FOLD 3** (`sub_xvol_pullback`, `vp_euidx_pocgrav`, `sub_mid_dn_revert`); **DROP leadlag_core**
(or demote to breadth conf 0.10). Nothing went forward-negative; nothing was deleted as evidence.

**Per-sleeve contribution (when all-4 folded, conf-wtd unit-R total, share of book):**
crypto 33% / metals_core 21% / energy_agri 19% / **sub_xvol_pullback 9% [NEW]** /
leadlag_core 7% [dropped] / fx_jpy 4% / **sub_mid_dn_revert 4% [NEW]** /
**vp_euidx_pocgrav 4% [NEW]** / metals_softband 2% / fx_jpy_ny 1% / metals_ob_micro -1% /
idxrev -3%. The 3 KEPT sleeves contribute **~17% of total conf-wtd edge** while metals/crypto/
energy core carries ~73% — the intended breadth-layer profile.

**Frequency:** book ~1512/yr fwd **+ clean_3 ~205/yr = deploy book ~1717/yr** fwd
(vp ~115/yr, sub_mid_dn ~64/yr, xvol ~26/yr). [leadlag_core would have added ~416/yr but is
dropped; clean3_ll010 secondary book = ~2134/yr if its tail cost is accepted.]

**Daily-breach:** 0.000% at every size 0.5-2.0% (worst single day -4.34% at 2.0% risk, inside
the -5% limit). Mechanical daily limit is safe at all tested sizes.

---

## 4. Challenge-pass MC — the sizing nuance (FAIR test = vol-matched)

Diversification-aware MC (block-bootstrap whole day-rows, 20k paths, 8% tgt / 5% daily / 10%
maxDD). Two comparisons: **same nominal `risk`** (book vs folded-full-4) and **risk-equivalent
vol-matched** (folded risk x0.793 so daily std == book). Daily-vol facts:
book mean +0.0700 std 0.535 sharpe **0.131** ; folded-4 mean +0.0908 std 0.675 sharpe **0.135**.

| risk | P(pass) FOLDED4 | P(pass) BOOK | FOLDED4 @volmatch | STRESS1.5x FOLDED4@vm | STRESS1.5x BOOK |
|---|---|---|---|---|---|
| 0.50% | 99.97% | 100.0% | 100.0% | 62.4% | 96.3% |
| 1.00% | 98.32% | 99.84% | 99.33% | 54.1% | 82.6% |
| 1.50% | 93.17% | 98.55% | 96.75% | 51.5% | 72.3% |
| 2.00% | 87.06% | 95.48% | 92.21% | 48.4% | 65.5% |

- **FORWARD-only MC: folded4 >= book at every size** (e.g. 2.0%: 97.82% vs 97.25%) — the new
  sleeves help the regime that actually matters going forward.
- **Unstressed, vol-matched: folded4 ~= book** (99.33% vs 99.84% @1%) — risk-adjusted neutral-to-
  positive (folded Sharpe 0.135 > book 0.131).
- **The honest catch: even VOL-MATCHED, the folded-4 1.5x left-tail STRESS is materially worse**
  (54% vs 83% @1%). Folding 4 +EV streams (esp. a high-frequency low-win one) raises the
  *frequency* and *depth* of mildly-negative days; the 1.5x inflation chains them in the
  block-bootstrap. This is real negative-skew tail risk, not a pure sizing illusion -> the
  ablation below isolates the cause.

---

## 5. Per-sleeve ablation (vol-matched) — the decisive test

Book + ONE new sleeve at a time, vol-matched, 1.5x-stress P(pass) @1.0% (book-only = **82.6%**),
plus the marginal daily Sharpe (book = 0.1310):

| + sleeve | marginal Sharpe | vm-stress@1.0% | verdict |
|---|---|---|---|
| **+ sub_xvol_pullback** | **0.1423** | **87.0%** | ADDITIVE (lifts Sharpe AND stress survival) |
| **+ sub_mid_dn_revert** | 0.1338 | 76.5% | ADDITIVE (lifts Sharpe; mild stress drag) |
| **+ vp_euidx_pocgrav** | 0.1328 | 80.5% | ADDITIVE (lifts Sharpe; ~neutral stress) |
| + leadlag_core | **0.1193** | **49.4%** | **DILUTIVE — the tail-variance injector** |

**This is the load-bearing result.** Three of the four sleeves are cleanly additive even under
the adversarial stress — they raise the book's risk-adjusted return and (for xvol) its tail
survival. **`leadlag_core` is dilutive at portfolio level**: its per-trade Sharpe (0.119) is
BELOW the book's, and at ~416 trades/yr / 28% win it injects a fat left tail that drags the
stress pass-rate from 82.6% to 49.4% at matched vol. This is the *same* failure mode the W3 book
documented when it rejected loosening the crypto ac-floor ("a low-persistence high-frequency band
injects tail variance at conf 0.85"). The correlation gate (|corr|<0.10) said "fold all 4"; the
portfolio-level tail test overrules it for leadlag.

---

## 6. Confirmed-additive vs dropped (learning)

**CONFIRMED ADDITIVE (fold in):**
1. `sub_xvol_pullback` conf 0.45 — the flagship; corr -0.012, +1.61R fwd, raises book Sharpe
   0.131->0.142 AND stress 82.6->87.0%. The best risk-improving add in the campaign.
2. `vp_euidx_pocgrav` conf 0.30 — corr +0.049, +0.24R fwd, all-3-years +, raises Sharpe, stress-
   neutral. Clean EU-index breadth in a class the core ignores.
3. `sub_mid_dn_revert` conf 0.20 — corr -0.023, +0.50R fwd 2/2 yrs, raises Sharpe; mild stress
   drag (76.5%) -> keep at breadth conf 0.20, not higher.

**DROPPED / DEMOTED (learning):**
4. `leadlag_core` conf 0.30 -> **DEMOTE to breadth conf ~0.10 or HOLD OUT.** It passes the
   correlation independence gate (+0.028) and is forward-positive (+0.16R), but it is **portfolio-
   DILUTIVE**: sub-book per-trade Sharpe (0.119) + very high frequency (416/yr, 28% win) = a fat
   1.5x-stress left tail (vm-stress 49.4% vs book 82.6%). LEARNING: **low correlation + positive EV
   is necessary but NOT sufficient for additivity — a low-Sharpe high-frequency sleeve diversifies
   the MEAN but concentrates the TAIL.** Size it tiny (breadth) or not at all; never at conf 0.30.
   - ETH leg separately HELD OUT: it doubles the leadlag-vs-crypto corr (+0.036->+0.090, ETHUSD
     already a crypto carrier) — a genuine double-count, correctly excluded.

**DEPLOY BOOK (the recommendation):** vol-matched comparison of 4 candidate books on the same day grid:

| book | daily Sharpe | vol_scale | P(pass)@1%vm | STRESS1.5x@1%vm | STRESS1.5x@1.5%vm | new tr/yr |
|---|---|---|---|---|---|---|
| book_only (current W3) | 0.1310 | 1.000 | 99.84% | 82.6% | 72.3% | +0 |
| full_4 (fold all) | 0.1346 | 0.793 | 99.33% | 54.1% | 51.5% | +622 |
| **clean_3 (xvol+vp+mid_dn, drop leadlag)** | **0.1464** | 0.926 | **99.85%** | **81.8%** | **71.5%** | **+205** |
| clean3_ll010 (3 clean + leadlag@0.10) | 0.1466 | 0.905 | 99.89% | 77.0% | 67.8% | +622 |

**WINNER = `clean_3`.** It delivers the biggest risk-adjusted lift (Sharpe 0.131->0.146, +12%),
holds unstressed P(pass) at book level (99.85%), and **preserves the adversarial 1.5x stress tail
essentially intact** (81.8% vs book 82.6% @1%; 71.5% vs 72.3% @1.5%) while adding +205 clean
low-corr trades/yr in index/EU-index/metals/energy/fx. `full_4` is strictly worse on the tail
(leadlag drags stress to 54%). `clean3_ll010` (leadlag demoted to conf 0.10) recovers the full
+622 tr/yr and a hair more Sharpe but sacrifices ~5pts of stress survival — a valid secondary
choice only if frequency is explicitly wanted; otherwise leadlag stays out.

**Universal deploy rule (both books):** fold the additive sleeves AND drop each account's risk
multiplier by the vol_scale (~0.79x for the full-4, milder for clean-3) so per-day risk stays
identical to the current book — this banks the diversification credit as a higher unstressed
P(pass) floor and a deeper forward edge, without letting the hotter book inflate the stress tail.
Daily-breach stays 0.000% at every tested size (worst day -4.34% @2.0%, inside -5%).

---

## FILES
- `KB5_fold_new_sleeves.py` — materialize-4-sleeves + true-corr + fold + diversification MC + vol-matched + ablation (reusable).
- `KB5_FOLD_RESULT.json` — full per-sleeve stats, corr matrix, fold contribution, all MC tables.
- Upstream: `SUBSTRATE_corrcheck.py`/`SUBSTRATE_CORRCHECK_RESULT.json`, `VP_WALKFORWARD_RESULT.json`,
  `LEADLAG_EDGES.json`, `KB4_*.md`, `SUBSTRATE_BUILD.md`. Corr/MC engine: `INTEG_portfolio_build_w3.py` (on `INTEG_W3_streams_cache.pkl`).
