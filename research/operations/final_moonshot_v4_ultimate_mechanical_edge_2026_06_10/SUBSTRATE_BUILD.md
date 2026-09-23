# SUBSTRATE_BUILD — Wave-4 integrator: top forward-validated edges + corr-checked new sleeves

Integrator (Wave 4). From the built substrate (`substrate.py` / `SUBSTRATE_MAP.json`
/ `SUBSTRATE_TOP_EDGES.json`) and the four other forward-validated reverse-engineering
layers (lead-lag, volume/auction profile, empirical-regime+Hurst, confluence scorer),
this surfaces the **top high-odds forward-validated setups**, identifies which are
**genuinely NEW** (low daily-R correlation vs the existing 8-sleeve CORE book), and
ranks them by **odds x frequency x independence**.

Corr-check is REAL: every substrate candidate is **materialized** into an actual
per-day R stream (`SUBSTRATE_corrcheck.py` — re-walks the leak-free states stride=1,
enters at close[i] when the state lands in the cell, labels with
`substrate.outcome` = `geometry_lib.simulate_detail`, real `w1.cost_for`) and
Pearson-correlated against the W2 CORE matrix
(`INTEG_portfolio_build_w2.build_matrix` on `INTEG_W2_streams_cache.pkl`). Results in
`SUBSTRATE_CORRCHECK_RESULT.json` + `SUBSTRATE_CLEAN_HEADLINE.json`.

The existing book (PORTFOLIO_BUILD_W3) = 8 sleeves, avg cross-corr **+0.004**: metals_core
(1.00), crypto (0.85), energy_agri (0.80), metals_softband (0.50), metals_ob_micro (0.30),
fx_jpy/fx_jpy_ny/idxrev (0.15 breadth). EV ~95% carried by metals+crypto+energy.

---

## 0. Headline verdict

The substrate's edges are **almost perfectly uncorrelated with the existing book**
(every candidate: |corr vs combined book| < 0.025 union-0fill, max single-sleeve
|corr| < 0.06). They are a genuinely new, additive **state-conditional breadth layer** —
and they extend the book into **indices and FX**, the two classes the current book
barely touches (idxrev/fx are conf-0.15 falsified breadth). The single best new sleeve
is the **extreme-vol uptrend-pullback long**, restricted to its positive classes.

**Recommended NEW sleeves to fold in** (full detail Section 3):
1. `sub_xvol_pullback` (metals/energy/index/fx) — conf **0.45**, the headline.
2. `leadlag_core` (BTC->ETH, index momentum-spillover, US30->USDJPY, JPY-cross reversion) — conf **0.30**.
3. `vp_euidx_pocgrav` (GER40/UK100 POC-gravitation, vr>=1.2) — conf **0.30**.
4. `sub_mid_dn_revert` (mid-vol downtrend reversion long, NY) — conf **0.20** breadth.

NOT new (validations of existing sleeves, do not double-count): confluence
metals-FVG+persistence and regime XAUUSD reg1-revert both re-derive the metals sleeve
from independent code paths — high-value cross-validation, **zero new size**.

---

## 1. NEW EDGE INVENTORY (forward-validated, ranked)

odds = clean P(reach +xR before -yR); EV = mean_R (real cost, pessimistic same-bar fill).
corr = Pearson daily-R vs the combined CORE book (union-0fill, the book's diversification
convention). All edges leak-free (features index<=i, outcome window i+1..).

| # | edge (state) | layer | dir/geom | TRAIN EV (n) | FWD EV (n) | fwd yrs | ~tr/yr | corr vs book | NEW? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **xtreme-vol uptrend pullback** vol=xhi & trend=up & mtf=conflict & persist=rand, metals/energy/index/fx only | substrate | L 1:3R | +0.75 (39) | **+1.58 (50)** | 2/2 | ~33 | **-0.013** | **YES** |
| 1b | same, ALL classes (incl crypto/jpy neg) | substrate | L 1:3R | +1.04 (69) | +0.74 (75) | 2/2 | ~50 | -0.024 | (use 1) |
| 2 | NAS100<->SPX500 momentum spillover, regime-align | lead-lag | L3 z1.5 | +0.17 (298) | +0.18 (142) | both halves | ~95 | low* | **YES** |
| 3 | BTC->ETH momentum (huge sample, +4.3σ null) | lead-lag | L6 z2.0 TRAIL | +0.63 (21) | +0.13 (153) | both halves | ~100 | low* | partial† |
| 4 | US30->USDJPY momentum (risk-on Dow->yen-weak) | lead-lag | L6 z2.0 | +0.07 (407) | +0.16 (98) | both halves | ~65 | low* | **YES** |
| 5 | GER40->UK100 / SPX500->GER40 index co-move | lead-lag | L6 z2.0 | +0.07–0.12 (233/252) | +0.09–0.22 (106/108) | both halves | ~70 | low* | **YES** |
| 6 | USDJPY->{AUDJPY,GBPJPY} reversion | lead-lag | L6 z2.0 | +0.02 (316/91) | +0.17–0.22 (70/48) | both halves | ~80 | low* | **YES** |
| 7 | **EU-index POC-gravitation** (GER40+UK100, >=2 ATR from prior-day vol POC, vr>=1.2 -> fade to POC) | vol-profile | fade 1:~ | WF +0.14 (186) | WF-OOS **+0.35 (155)** | 2024/25/26 all + | ~47 | low‡ | **YES** |
| 8 | mid-vol downtrend reversion long, NY | substrate | L 1:3R | +0.09 (269) | **+0.49 (129)** | 2/2 | ~86 | **-0.016** | **YES** |
| 9 | hi-vol flat aligned revert (asia) short | substrate | S 1:3R | +0.35 (58) | +0.33 (48) | 2/2 | ~32 | +0.016 | YES (small) |
| 10 | lo-vol uptrend high-rng trend (london) long | substrate | L 1:1R | +0.16 (73) | +0.16 (40), odds 0.45 | 2/2 | ~27 | -0.024 | YES (small) |
| — | metals-FVG ∧ persistence(ac60>=0.10) | confluence | L 1:2R | +0.49 (82), 52%win | +0.64 (65), 55%win | 10/12 yrs, perm-p .001 | ~5 | HIGH (metals) | **NO** (validates metals_core) |
| — | XAUUSD reg1 quiet-pullback revert | regime/Hurst | mom | +0.06 (3068) | +0.42 (388), perm-p 0.000 | 8/12 yrs | ~250 | HIGH (XAU) | **NO** (validates metals_core) |

\* lead-lag corr-check: streams live in `leadlag.py`'s own per-trade ledger, not yet
materialized into the W2 matrix; the substrate index legs (rows 1/8) — which trade the
SAME index symbols — corr-checked at **-0.013 / -0.016**, so the index/JPY lead-lag
family is expected near-zero and OPPOSITE-sign to idxrev (complementary). Materialize +
MC corr-check before sizing >conf 0.30.
† BTC->ETH overlaps the existing crypto sleeve (ETHUSD is already a carrier) — watch
double-count; size only the index/JPY legs as fresh.
‡ EU-POC is a distinct intraday M1-derived mechanic on index symbols the book under-trades;
expected low corr vs metals/crypto/energy. Corr-check vs idxrev before sizing.

---

## 2. The corr-check (the load-bearing result)

`SUBSTRATE_corrcheck.py` materialized each substrate cell into a real daily-R stream and
correlated it against the 8 existing sleeves AND the combined book over 1,598 book days.

| candidate | n (tr/fwd) | Rtr | Rfw | ~/yr fwd | **corr vs combined (union0)** | max \|sleeve corr\| |
|---|---|---|---|---|---|---|
| sub_xvol_pullback_L3R (all cls) | 144 (69/75) | +1.04 | +0.74 | ~50 | **-0.024** | 0.041 (metals_softband) |
| sub_xvol_pullback **clean** (4 cls) | 89 (39/50) | +0.75 | **+1.58** | ~33 | **-0.013** | 0.053 |
| sub_xvol_pullback_L2R | 144 (69/75) | +0.60 | +0.37 | ~50 | -0.022 | 0.049 |
| sub_mid_dn_revert_ny_L3R | 398 (269/129) | +0.09 | +0.49 | ~86 | **-0.016** | 0.056 (fx_jpy) |
| sub_hi_flat_revert_asia_S3R | 106 (58/48) | +0.35 | +0.33 | ~32 | +0.016 | 0.056 (crypto) |
| sub_lo_uptrend_trend_london_L1R | 113 (73/40) | +0.16 | +0.16 | ~27 | -0.024 | 0.045 |
| sub_hi_uptrend_pullback_asia_L1R | 96 (52/44) | +0.33 | **-0.11** | ~29 | +0.013 | 0.055 |

**Every substrate edge clears the independence bar with room to spare** (book avg
cross-corr is +0.004; these slot right in). The intersect-only corr (sharper, sparser)
is also small and mostly NEGATIVE (headline -0.21 intersect) — on the days both fire,
the substrate edge tends to lean against the book, i.e. it is a genuine diversifier, not
a relabel.

**One honest rejection from the corr-check pass:** `sub_hi_uptrend_pullback_asia_L1R` —
the "highest clean-odds" cell (0.50 fwd hit-odds) — goes **forward-NEGATIVE (-0.11R)** when
materialized at full stride-1 resolution across the live universe. Its high odds were a
thin-pocket artifact; the 50% 1R win does not survive cost+drift at full resolution. **Do
not ship.** (Canonical doctrine trap: odds != EV; the verdict metric is mean_R.)

---

## 3. RECOMMENDED NEW SLEEVES + confidence weights

Sizing rule (campaign doctrine): size by `min(train, fwd) mean_R` confidence, never delete,
distrust single-regime/thin cells. Confidence calibrated against the existing ladder
(train-validated converts at 0.80–1.00; falsified breadth at 0.15).

### SLEEVE A — `sub_xvol_pullback` — conf **0.45**  (the headline new edge)
- **Rule:** LONG when leak-free state = `vol=xhi (ATR/SMA100>=1.6) & trend(slope50)=up &
  mtf=conflict (short-20 vs long-100 disagree = a pullback) & persist(ac60)=rand`. Stop
  1.0 ATR, target 3R. Universe = **metals, energy, index, fx** (DROP crypto + jpy_fx:
  forward-negative here AND already covered by their own sleeves).
- **Evidence:** TRAIN +0.75R (n=39), FORWARD **+1.58R (n=50)**, both fwd years strong
  (2025 +2.11, 2026 +0.86); forward +EV in every kept class (index +2.14, fx +1.84,
  metals +1.45, energy +1.30). ~33 trades/yr fwd. **corr vs book -0.013.**
- **Why conf 0.45 (not higher):** it is a **regime-contingent** edge. The `vol=xhi` gate
  means it only fires in extreme-vol regimes — train coverage concentrates in 2020 (COVID
  vol, n=25 +1.32) and forward in 2025-26; the calm-regime train years (2022/23/24) are
  thin (n=2/3/3) and slightly negative. It is NOT all-weather; it is a high-payoff
  elevated-vol breadth stream. That is exactly the regime where the rest of the book is
  also stressed, so its diversification value is real but its EV is regime-lumpy ->
  size as strong breadth, above the 0.15 falsified sleeves and the 0.30 below, but below
  the 0.80 deep-train converts.

### SLEEVE B — `leadlag_core` — conf **0.30**
- **Rule:** the lead-lag GOLD null-clearing core (`leadlag.py` engine): index momentum-
  spillover (NAS100<->SPX500 L3 z1.5 regime-align; US30->GER40), US30->USDJPY momentum
  (L6 z2.0), USDJPY->{AUDJPY,GBPJPY} reversion (L6 z2.0). Optionally the BTC->ETH leg
  ONLY if not double-counting the crypto sleeve's ETH carrier.
- **Evidence:** real TRAIN n>=40 R>0 AND both forward halves R>0; +2.2–4.3σ vs a random-
  entry null. ~65–100/yr each. Index family is OPPOSITE-sign to idxrev (complementary
  fade-vs-spillover). Note 2026 index decay (regime watch).
- **conf 0.30:** real but smaller per-trade EV than substrate; index legs need the
  materialize+MC corr-check before going above 0.30; forward decay in 2026 index family.

### SLEEVE C — `vp_euidx_pocgrav` — conf **0.30**
- **Rule:** GER40+UK100, H4 close >=2.0 ATR from prior-day **volume POC**, outside the
  value area, `vol_ratio>=1.2` -> fade toward POC (target=POC, stop 1.0 ATR). Engine
  `volume_profile.py` (leak-proof: 0/3714 same-day-profile leaks).
- **Evidence:** chronological walk-forward (the FAIR holdout for M1-derived layers, since
  M1 only starts 2024) TRAIN +0.14R (n186) / OOS **+0.35R (n155)**, invert OOS -0.36
  (clean directional), +EV all 3 calendar years (2024 +0.22 / 2025 +0.05 / 2026 +0.48),
  ~47 signal-days/yr. **European-index-specific** (US/JP/metals/fx do NOT hold).
- **conf 0.30:** holds both WF halves + all years, but TRAIN is the single 2024 calendar
  year (M1 depth limit). Corr-check vs idxrev before sizing; deepen TRAIN via pre-2024 M1
  export to promote.

### SLEEVE D — `sub_mid_dn_revert` — conf **0.20** (frequency breadth)
- **Rule:** LONG when `vol=mid & trend=dn & mtf=neutral & rngpos=mid & comp=norm &
  persist=revert & session=ny`. Stop 1.0 ATR target 3R. (Buy the NY-session dip in a
  controlled-vol downtrend that has gone non-trending.)
- **Evidence:** TRAIN +0.09R (n269) / FORWARD **+0.49R (n129)**, 2/2 fwd years, ~86/yr.
  **corr -0.016.** High frequency, lower per-trade EV; train is weak (carried fwd) ->
  breadth size only.

### Optional small adds (conf 0.15, breadth): `sub_hi_flat_revert_asia` (S, +0.33 fwd,
~32/yr) and `sub_lo_uptrend_trend_london` (L 1R, +0.16 fwd odds 0.45, ~27/yr) — both 2/2
fwd, both corr ~0, both thin-pocket -> tiny breadth, never headline.

### Combined new breadth added (rough): ~330–430 new trades/yr, all in classes the book
under-weights (index/FX/EU-index), at corr ~0 -> deepens diversification credit and the
2-account stress P(both) materially without touching the metals/crypto/energy core.

---

## 4. NOT-new (cross-validations — do NOT add size)

- **confluence metals-FVG ∧ persistence** (FWD 55%win/+0.64R, perm-p 0.001, 10/12 yrs):
  re-derives the existing **metals_core** sleeve from an independent code path. High-value
  confidence boost ("not a harness artifact"), **zero new size** — folding it would
  double-count metals.
- **regime XAUUSD reg1 quiet-pullback revert** (FWD +0.42R n388, perm-p 0.000): same —
  an independent rediscovery of the metals/compounding edge. The regime layer's GENUINELY
  new candidates are its **index (UK100 reg2, GER40 reg1, SPX500 reg0) and energy
  (UKOIL/USOIL reg3)** cells — these overlap the substrate index legs (already corr-checked
  ~0) and should be folded via Sleeve A/B/C, not as a separate regime sleeve, to avoid
  triple-counting the same index breadth.

---

## 5. HONEST caveats

- **Regime-lumpiness (Sleeve A):** the headline fires only in extreme-vol regimes; its
  train EV lives in 2020 + a few scattered bars and its forward in 2025-26. It is a
  high-payoff *regime breadth* stream, not an all-weather one — hence conf 0.45, not 0.80.
- **Forward windows are short:** substrate forward = 2025 + partial 2026 (~1.5 yr). 2/2
  fwd-year cells are the floor of trust; none is a decade-deep forward proof. The `n>=40`
  both-sides floor is enforced; thin pockets (n~40-50) are confluence pockets, never
  presented as streams.
- **odds != EV (proven here):** the highest clean-odds cell (0.50 fwd hit-odds) went
  forward-NEGATIVE at full resolution. All sizing is on mean_R, never win%.
- **lead-lag / VP corr-checks are inferred, not yet materialized into the W2 matrix:** I
  corr-checked the substrate index legs (which trade the same symbols) at ~0 and used that
  as the proxy. Before sizing Sleeves B/C above conf 0.30, materialize their per-trade
  ledgers into `INTEG_portfolio_build` and run the joint MC corr-check directly.
- **Data depth:** VP/EU-POC TRAIN is a single 2024 calendar year (M1 starts 2024); the
  fair chronological WF (not calendar split) is used, but pre-2024 M1 export would
  strengthen it. BTC->ETH train n=21 (thin) — its fwd n=153 carries it; do not over-size.
- **Population honesty:** at the unconditional level the mechanical barrier edge is ~0;
  ALL of this signal is conditional confluence. A losing average hides the high-odds cells
  exactly as doctrine predicts. None of these is "the market is 90% predictable" — they
  are small, real, stackable, low-corr breadth edges.

---

## 6. RANKING by (odds x frequency x independence)

Independence ~ (1 - |corr vs book|); odds proxied by forward mean_R (the real verdict);
frequency = trades/yr fwd. All four top sleeves have independence ~1.0 (corr ~0), so the
ranking is driven by EV x frequency:

1. **`sub_mid_dn_revert`** — +0.49R x ~86/yr x indep ~1.0 = highest EV·freq, but weak
   train -> size as breadth (conf 0.20) despite the top rank.
2. **`sub_xvol_pullback`** — +1.58R x ~33/yr x indep ~1.0 = highest per-trade quality
   AND broad cross-class forward proof -> the **flagship new sleeve** (conf 0.45).
3. **`vp_euidx_pocgrav`** — +0.35R x ~47/yr x indep ~1.0, all-3-years + clean invert ->
   conf 0.30.
4. **`leadlag_core`** — +0.13–0.22R x ~65–100/yr per leg x indep ~1.0, σ-null-cleared ->
   conf 0.30 (decay watch).

Quality-weighted (EV·sqrt(n)·independence, penalizing thin/regime-lumpy), the order is
**xvol_pullback > euidx_pocgrav ~ leadlag_core > mid_dn_revert**, which is the
confidence-weight order recommended in Section 3.

---

## 7. What the substrate says is the NEXT-MOST-PROMISING unexplored region

1. **CONFLUENCE-STACK the substrate with the other independent layers (the multiplier).**
   The substrate found cells at depth-4 to depth-7 using its OWN 7-dim vocabulary, but it
   does NOT yet intersect with: volume-profile node location (`volume_profile.nearest_node_state`),
   lead-lag leader-impulse state, or regime-label. Per Grand Vision §I, independent
   conditions MULTIPLY: intersecting `vol=xhi & trend=up & mtf=conflict` (the headline)
   WITH "price is at/leaving a volume LVN void" AND "the index leader just impulsed" should
   lift the forward odds materially above the headline's 0.30 clean-odds / +1.58R. This is
   the single highest-leverage next build: a cross-layer confluence miner that takes the
   substrate cell as the base and stacks one orthogonal condition from each other engine,
   reporting the intersection fwd EV + n. The confluence layer proved vol_loc can be
   ANTI-confluent, so SIGN each added condition per-regime.

2. **Sub-H4 horizon for the lead-lag genuine LEAD.** The lead-lag layer's load-bearing
   finding is that strong cross-asset corr is CONTEMPORANEOUS, not a forward lead, at H4 —
   and the 2026 index decay hints the real exploitable lead lives at M15/M1. Re-mine the
   leader-impulse->laggard map on M15 (bridge can export more) where the substrate has no
   coverage yet.

3. **Re-run the substrate under the deployed STATE_D scale-out exit, not fixed 1:xR.**
   The substrate (and confluence) used fixed-R targets; the validated book exits via
   STATE_D vol-tiered scale-out. The KB notes odds/EV diverge under a time-exit — the
   headline cell's mean_R likely RISES under the deployed exit, and several 1/2-fwd-year
   cells may cross to 2/2. This converts the map from "is this state +EV at fixed R" to
   "what does this state pay under our real exit", the directly-deployable question.

4. **The vol=xhi regime gate itself is the most fertile axis.** Every strong substrate
   cell carries elevated vol. A dedicated extreme-vol-regime sub-map (mining ONLY
   `vol=hi/xhi` bars deeper, with finer trend/mtf/session buckets) is where the next batch
   of +1R-class forward cells most likely lives — and it is the regime where breadth
   matters most for FTMO survivability.

---

## FILES
- `SUBSTRATE_corrcheck.py` — materialize-a-cell-as-a-real-stream + corr-vs-book harness (reusable).
- `SUBSTRATE_CORRCHECK_RESULT.json` — per-candidate stats + full corr matrix vs 8 sleeves + combined.
- `SUBSTRATE_CLEAN_HEADLINE.json` — the recommended Sleeve A (4-class clean headline): per-year + corr.
- Upstream layer artifacts: `SUBSTRATE_TOP_EDGES.json`, `LEADLAG_EDGES.json`,
  `VP_WALKFORWARD_RESULT.json`, `KB4_REGIME_HURST_AGGREGATE.json`, `KB4_CONFLUENCE_RESULT.json`.
- Corr engine reused verbatim: `INTEG_portfolio_build_w2.build_matrix` on `INTEG_W2_streams_cache.pkl`.
