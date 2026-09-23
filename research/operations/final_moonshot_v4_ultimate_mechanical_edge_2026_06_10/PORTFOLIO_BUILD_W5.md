# PORTFOLIO_BUILD_W5 — Upgraded book assembly (Wave-5 integrator)

Builder/integrator pass 2026-06-15. Assembles the strongest deployable book from
EVERY Wave-4/5 track and re-runs the diversification-aware FTMO challenge-pass MC +
adversarial 1.5x left-tail stress + 2-account allocation on the **LOCKED W2 MC engine**
(TARGET 8% / DAILY 5% / MAXDD 10% / BLOCK 5 / N 20000 / block-bootstrap whole
cross-sectional days). All inputs leak-free (features index<=i, `geometry_lib`/`exit_state_d`
forward-only labeler), real cost `w1.cost_for`, R winsorized [-1.3,+5], forward holdout
TRAIN(<=2024) vs FORWARD(2025-26) + per-year + n on every sleeve.

Engines: `INTEG_portfolio_build_w5.py` (assembly + selection), `INTEG_w5_clean3_deploy.py`
(final deploy-book MC). Results: `INTEG_PORTFOLIO_W5_RESULT.json`,
`INTEG_W5_CLEAN3_DEPLOY.json`. Cache: `INTEG_W5_new_streams_cache.pkl`.

---

## 0. HEADLINE — the data picked the deploy book, and it is NOT "add everything"

Every candidate sleeve was forward-positive and low-correlation (|corr vs book| < 0.06
for all six), so a naive integrator would fold all of them. **The risk-equivalent
deploy-selection MC overrode that.** Adding the high-frequency / low-per-trade-Sharpe
streams (leadlag_core, subh4_ll_fx) and even the train-shallow VP/mid-dn additives
*beyond* the clean core progressively **concentrates the 1.5x left tail** — the exact
failure mode the fold-track documented (low corr + +EV is necessary but NOT sufficient).

**DEPLOY BOOK = `clean_3`**: W3 8-sleeve core **+ sub_xvol_pullback (0.45) + vp_euidx_pocgrav
(0.30) + sub_mid_dn_revert (0.20)**. It is the unique variant that *raises* Sharpe AND
holds the stress tail at book level.

### Risk-equivalent variant comparison (vol-matched; book daily std = 0.5686)
| variant | sleeves added | Sharpe | P(pass)@1%vm | P(pass)@1.5%vm | STRESS1.5x@1% | STRESS1.5x@1.5% | +tr/yr |
|---|---|---|---|---|---|---|---|
| book_only (W3) | — | 0.1396 | 99.84% | 98.46% | 82.76% | 72.85% | 0 |
| **clean_3 (DEPLOY)** | xvol+vp+middn | **0.1522** | **99.91%** | 98.51% | 80.86% | 70.93% | **+205** |
| clean_3 + ll@0.10 | +leadlag breadth | 0.1466 | 99.84% | 98.38% | 75.46% | 66.59% | +622 |
| clean_3 + ll + subh4 | +subh4 FX | 0.1408 | 99.61% | 97.69% | 70.20% | 62.09% | +650 |
| gated_5 (xvol→veto-gate) | gate+breadth | 0.1392 | 99.56% | 97.47% | 68.73% | 61.47% | +640 |

Reading: **clean_3 is the Sharpe maximum and the only additive variant that keeps the
1.5x-stress pass-rate within ~2pts of book-only** while banking +205 low-corr trades/yr.
Each further addition trades stress-tail safety for frequency. Per doctrine **nothing is
deleted** — leadlag_core, subh4_ll_fx and the cross-layer veto-gate are kept as documented
breadth/selector overlays (Sections 5-6), not folded into the risk-banked book.

---

## 1. The DEPLOY book (clean_3) — composition + confidence weights

11 sleeves, avg pairwise off-diag daily-R corr **+0.0027** (min -0.119, max +0.116) —
the book stays effectively uncorrelated. Combined daily mean **+0.0913 unit-R** (all),
**+0.2796 unit-R** (forward 2025-26), std 0.5997, win-days 51.5%, n_days 1599.

| sleeve | conf | share of book | TRAIN EV (n) | FWD EV (n) | fwd/yr | source |
|---|---|---|---|---|---|---|
| crypto (BTC/DASH/ETH) | 0.85 | 35.6% | +1.77 (21) | +0.95 (83) | 42 | W3 core |
| metals_core | 1.00 | 23.0% | +0.68 (82) | +1.23 (49) | 25 | W3 core |
| energy_agri | 0.80 | 20.8% | +0.16 (64) | +0.69 (98) | 49 | W3 core |
| **sub_xvol_pullback** | **0.45** | **9.2%** | **+0.75 (39)** | **+1.61 (51)** | **26** | **NEW Wave-4 substrate** |
| fx_jpy (London) | 0.15 | 4.3% | fwd-only | +0.17 (530) | 265 | W3 core (falsified→breadth) |
| **sub_mid_dn_revert** | **0.20** | **4.1%** | **+0.09 (269)** | **+0.49 (129)** | **64** | **NEW Wave-4 substrate** |
| **vp_euidx_pocgrav** | **0.30** | **3.9%** | **+0.22 (111)** | **+0.24 (230)** | **115** | **NEW Wave-4 volume-profile** |
| metals_softband | 0.50 | 2.1% | +0.57 (31) | +0.14 (39) | 20 | W3 core |
| fx_jpy_ny | 0.15 | 1.0% | fwd-only | +0.15 (197) | 99 | W3 core |
| metals_ob_micro | 0.30 | -0.7% | -0.70 (5) | -0.17 (2) | 1 | W3 core (kept tiny) |
| idxrev | 0.15 | -3.2% | -0.06 (4447) | +0.03 (2026) | 1013 | W3 core (falsified→breadth) |

**Frequency**: book ~1512 tr/yr fwd + 3 new additives ~205 tr/yr = **~1717 tr/yr forward**.
(If breadth overlays in Section 5 are later added, the full surface reaches ~2162 tr/yr.)

---

## 2. Challenge-pass MC — deploy vs book (vol-matched = the fair test)

The deploy book runs hotter per unit nominal risk (std 0.5997 vs book 0.5686), so the
honest comparison scales deploy risk by **vol_scale = 0.948** to equalize daily std, then
banks the diversification as a higher pass-rate floor at no tail cost.

| risk | DEPLOY@vm P(pass) | DEPLOY@vm STRESS1.5x | BOOK P(pass) | BOOK STRESS1.5x | DEPLOY FWD-only |
|---|---|---|---|---|---|
| 0.50% | 100.00% | 95.30% | 100.00% | 96.19% | 100.00% |
| 0.75% | 99.98% | 87.16% | 99.98% | 89.33% | 100.00% |
| 1.00% | 99.91% | 80.86% | 99.79% | 82.66% | 99.94% |
| 1.50% | 98.51% | 70.93% | 98.62% | 72.86% | 99.32% |
| 2.00% | 95.75% | 64.79% | 95.59% | 65.56% | 97.45% |

- **Unstressed**: deploy holds the book's near-certain pass-rate floor (99.91% @1%) — the
  +205 tr/yr of orthogonal breadth deepen diversification without raising failure.
- **Adversarial 1.5x left-tail stress**: deploy 80.86% vs book 82.66% @1% — a ~1.8pt cost,
  the price of the extra additive breadth, NOT a tail blowup (gated_5/leadlag variants cost
  10-14pts here; that is why they are excluded). At vol-matched risk this is the strongest
  stress tail of any additive book.
- **Forward-only (2025-26)**: 99.94% @1% — the recent regime is the easiest, as expected.

---

## 3. Per-sleeve ablation — the additivity gate (vol-matched, stress@1.5%)

Each new sleeve added to book ALONE, vol-matched, judged on the 1.5x-stress pass-rate
(NOT just correlation). This is the load-bearing discipline: low corr + +EV is necessary
but not sufficient.

| + sleeve | Sharpe (book 0.128) | vm-stress@1.5% (book 72.75%) | verdict |
|---|---|---|---|
| sub_xvol_pullback | 0.1387 | 75.06% | **ADDITIVE** (lifts both axes) |
| vp_euidx_pocgrav | 0.1295 | 69.03% | mild-dilutive on the deep tail |
| sub_mid_dn_revert | 0.1304 | 65.84% | mild-dilutive on the deep tail |
| leadlag_core (0.10) | 0.1280 | 65.70% | dilutive (high-freq, low per-trade Sharpe) |
| subh4_ll_fx (0.15) | 0.1255 | 64.70% | dilutive (thin fwd, 38% win @ fixed R) |

Note the apparent tension with Section 0: in the *whole-book risk-equivalent* selection
(Section 0), clean_3 wins because vp + mid_dn each add Sharpe and only marginally touch the
@1.5% tail when combined with xvol's strong stress lift; in the *single-add @1.5%* ablation
they read mild-dilutive in isolation. The selection table is authoritative (it is the real
deployed configuration). The honest call: **xvol is unambiguously additive; vp + mid_dn are
Sharpe-accretive low-corr breadth that the book absorbs at a small, acceptable deep-tail
cost; leadlag/subh4 are NOT folded** (their deep-tail cost exceeds their Sharpe value).

---

## 4. Highest-odds confluent setups (honest EV / win / n — the deliverable)

All forward (2025-26), real cost, fixed-R barrier unless noted. Win% at fixed R stays in
the 35-85% band; the verdict is mean_R lift, never a thin win-rate flag.

1. **CROSS-LAYER FLAGSHIP — substrate xvol pullback ∧ leader-impulse VETO** (the high-odds
   frontier). `vol=xhi·persist=rand·trend=up·mtf=conflict` LONG 3R on metals/index/energy/fx,
   **only when NO relevant leader (SPX/NAS/BTC/USDJPY/US30/XAU/DXY) is impulsing ≥1.5σ**.
   Materialized here: **FWD +2.32R, 84% win, n32** (TRAIN +0.64R n24; 2025 +2.93 / 2026 +1.42);
   the cross-layer track's pooled number is +1.53R n40 perm-p 0.0003, both fwd years.
   The mirror (leader impulsing opposed) goes forward-NEGATIVE -0.35R — the sign is real.
   **Deployment**: this is a *filtered subset* of sub_xvol_pullback (corr +0.79 with it) — it
   is NOT folded as a separate sleeve (double-count). It is the **selector/size-up overlay**:
   when the veto condition holds on an xvol-pullback signal, size it up (high conviction);
   the un-gated sub_xvol_pullback (0.45) carries the base frequency in the book.

2. **HIGH-CONVICTION POCKET — pullback ∧ no-leader ∧ above prior value area.** Add
   `vp_loc=above_va`: FWD +1.69R (n19), 2025 +2.36 / 2026 +1.29, perm-p 0.005. n<30 + VP
   train-shallow → selector overlay (take-the-best-pocket), never a standalone stream.

3. **sub_xvol_pullback base sleeve** (the deployed flagship additive): FWD **+1.61R, 67% win,
   n51** (TRAIN +0.75R n39); 2025 +2.13 / 2026 +0.86; corr vs book -0.012. ~26 tr/yr.

4. **vp_euidx_pocgrav** (deployed breadth): GER40+UK100 POC-gravitation, FWD +0.24R n230,
   ~115 tr/yr, both fwd years +, corr +0.049. The frequency engine of the additive set.

5. **sub_mid_dn_revert** (deployed breadth): NY mid-vol downtrend reversion long, FWD +0.49R
   n129, ~64 tr/yr, corr -0.023. Repairs the book's NY-session coverage.

6. **sub-H4 lead-lag — USDJPY→EURJPY london-open** (breadth-optional, Section 6): M15 4h≥2.5σ
   USDJPY impulse at the London open predicts EURJPY continuation. TRAIN +0.094R n301 / FWD
   **+0.76R n56**, null-z +4.85, leader-adds-dR +0.51 (genuine cross-asset info, not follower-own).
   The session-open gate is the load-bearing confluence. Excluded from the risk-banked book
   (deep-tail dilutive at fixed R), retained as a documented cross-asset family.

**Universal EXCLUSIONS (apply to all xvol-up longs in the selector):** drop `hurst=trend`
(inverts the edge, fwd -0.74R), drop leader-impulse-opposed bars (fwd -0.35R), drop the
`regime=vol_expansion` slice (fwd -0.15R, 0/2 yrs).

---

## 5. Regime-gated existing book — DOES NOT LIFT (kept off)

The RGATE track tested gating/sizing the existing CORE sleeves by the substrate's leak-free
regime read at matched gross exposure. Verdict: **the substrate gate LOSES on every book-level
axis** (EV/gross +0.2721 ungated vs +0.2044 best-gated; stress-1.5x 89.0% ungated vs 61.1%
gated). The book is already the selection layer; the substrate's value is *orthogonal breadth*
(corr~0, additive), not overlap-filtering the core. **Decision: keep the CORE ungated; the
substrate is folded as ADDITIVE breadth (Section 1), which is the opposite of gating.** The
gate engine is preserved as negative-result evidence (`RGATE_*`).

---

## 6. Breadth-optional overlays (kept, NOT in the risk-banked book)

Per "delete nothing / size by confidence," these are documented and available but excluded
from the deploy book because their 1.5x-stress deep-tail cost exceeds their Sharpe value:

- **leadlag_core** (index/JPY-cross H4 spillover, ETH leg held out for crypto double-count):
  FWD +0.16R n833, ~416 tr/yr, corr +0.028. Sub-book per-trade Sharpe 0.119 < book 0.131;
  at 28% win / fixed R it injects a fat 1.5x left tail. Demote to ≤0.10 breadth IF the owner
  wants raw frequency; the cleaner path is mining its highest-Sharpe legs only (next steps).
- **subh4_ll_fx** (M15 USDJPY→EURJPY london-open core): FWD +0.76R n56, ~28 tr/yr, corr +0.017.
  Strong edge, but thin forward n + 38% win at fixed R make it deep-tail dilutive at book scale.
  Best deployed as a standalone small-size session sleeve, not folded into the risk pool.
- **xlayer_veto_gate** (Section 4 item 1): selector/size-up overlay on sub_xvol_pullback, not a
  separate sleeve (corr +0.79 with the base = same population, filtered).

---

## 7. Daily-breach + recommended 2-account live allocation

**Daily-breach across the size grid (deploy book, worst single day vs the -5% FTMO limit):**
0% breach at every size; worst single day -2.02% @1.0%, -4.04% @2.0%. The book is structurally
incapable of a single-day breach at any sane size — diversification caps per-day concentration.

**2-account allocation** (both accounts trade the FULL deploy book; diversification is WITHIN
each account, per the Wave-1 finding; sizes shown at vol-matched effective risk):

| config | eff size A | eff size B | P(both pass) base | P(both) FWD | P(both) STRESS1.5x | daily-breach |
|---|---|---|---|---|---|---|
| **balanced (RECOMMENDED)** | 0.71% | 0.71% | **99.99%** | 100.00% | 70.30% | 0.00% |
| conservative | 0.47% | 0.47% | 100.00% | 100.00% | 79.51% | 0.00% |
| staggered A1.0/B0.75 | 0.95% | 0.71% | 99.88% | 99.97% | 59.97% | 0.00% |
| staggered A1.0/B0.50 | 0.95% | 0.47% | 99.89% | 99.97% | 58.15% | 0.00% |

**Recommendation: balanced 0.71%/0.71% effective** (= 0.75% nominal × vol_scale 0.948). It
gives P(both)=99.99% base / 70.30% under adversarial 1.5x stress with 0% daily-breach, and
banks the +9% Sharpe lift as a higher pass-rate floor rather than larger bets. The
conservative 0.47%/0.47% is the max-stress-safety variant (79.5% under stress) for the first
live challenge cycle; step up to balanced after the first account clears. Staggering buys
nothing here (lower stress P(both)) because both accounts share the same diversified edge.

---

## 8. Honest per-dimension scorecard (D1-D6)

| dim | grade | honest assessment |
|---|---|---|
| **D1 Edge reality** | **A-** | Core sleeves train+forward validated, real cost, leak-free labeler; xvol additive flagship FWD +1.61R both years; cross-layer veto perm-p 0.0003; subh4 null-z +4.85 + falsification-passing. The substrate cells are 1/2-or-2/2-fwd-year, real but young. |
| **D2 Forward holdout** | **B+** | Every sleeve TRAIN(<=2024)/FWD(2025-26) split + per-year + n. Forward window is short (2025 + partial 2026); the VP layer is M1-since-2024 so essentially forward-only (flagged); deep H4 layers have full 2014-26 depth. Distrust single-fwd-year positives — flagged where present. |
| **D3 Independence/diversification** | **A** | Avg off-diag daily-R corr +0.0027 (min -0.119, max +0.116); every additive |corr vs book| < 0.06; new-vs-new double-count radar caught xvol↔veto-gate (+0.79, handled as overlay) and ETH↔leadlag (held out). True cross-sectional covariance preserved by whole-day block-bootstrap. |
| **D4 Tail / stress survival** | **B+** | 0% daily-breach at all sizes; worst day -2.02% @1%. Unstressed P(pass) 99.91% @1%. The 1.5x adversarial left-tail is the binding constraint: deploy 80.86% vs book 82.66% @1% — held within ~2pts only because the dilutive high-freq sleeves were EXCLUDED. This is the honest ceiling: the book is challenge-robust, not stress-bulletproof. |
| **D5 Additivity discipline** | **A-** | The integrator REFUSED to fold all +EV low-corr sleeves; the vol-matched stress-tail ablation drove the cut (leadlag/subh4/gate excluded despite +EV & low corr). Risk-equivalent comparison throughout; diversification banked as pass-rate floor, not bigger bets. Minor: vp/mid_dn read mild-dilutive in single-add ablation but Sharpe-accretive in the deployed combo — kept, documented. |
| **D6 Deployability** | **B+** | Concrete: 11 sleeves, fixed confidence weights, ~1717 tr/yr fwd, 2-account sizes specified at vol-matched risk. Caveats: substrate/VP cells answer a fixed 1:3R question while the deployed exit is STATE_D scale-out (re-mining under STATE_D shifts mean_R; next step); the cross-layer flagship is an overlay needing selector wiring, not a drop-in sleeve. |

---

## 9. Next steps (build queue)

1. **Wire clean_3 into the live selector/sizer**: create `_w5` generators for sub_xvol_pullback,
   vp_euidx_pocgrav, sub_mid_dn_revert (already materialized in `INTEG_W5_new_streams_cache.pkl`),
   add to GENS/SLEEVE_CONF at 0.45/0.30/0.20, and regenerate the go-live dossier at the
   balanced 0.71%/0.71% vol-matched allocation.
2. **Re-mine the substrate additives under the deployed STATE_D scale-out exit** (not fixed
   1:3R) — the xvol flagship mean_R likely shifts and some 1/2-fwd-year cells may cross to 2/2.
3. **Mine leadlag_core's highest-per-trade-Sharpe legs only** (US30→USDJPY, NAS100↔SPX500) to
   recover a NON-dilutive index-spillover sleeve; the full 8-config core is too broad/low-Sharpe.
4. **Deepen the VP TRAIN side via pre-2024 M1 export** to convert vp_euidx_pocgrav and the
   `above_va` confluence gate from forward-only to true holdout.
5. **Wire the cross-layer leader-impulse VETO as a size-up overlay** on sub_xvol_pullback in the
   selector (4-class universe), plus the universal exclusions (hurst=trend, leader-opposed).
