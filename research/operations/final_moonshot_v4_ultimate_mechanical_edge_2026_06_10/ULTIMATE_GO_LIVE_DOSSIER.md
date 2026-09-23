# ULTIMATE SYSTEM — GO-LIVE DOSSIER (Wave-7 UNLEASH growth-optimal refresh 2026-06-15)

> WAVE-7 (UNLEASH) UPDATE — supersedes the Wave-6 conservative-posture section below for SIZING and
> EXECUTION. The deploy BOOK is unchanged in spirit (the 11-sleeve clean_3 / 12-sleeve clean_4
> remains the edge), but Wave-7 (1) made execution **tick-true** (drop the two illiquid energy legs
> whose modeled EV was a cost-map artifact), (2) re-sized to the **growth-optimal dial** with
> confidence-proportional Kelly-lite, and (3) proved the prior ~0.71–0.75% effective deploy was a
> large fear drag. Build narrative + full MC: **`PORTFOLIO_BUILD_W7_FINAL.md`** →
> `INTEG_W7_FINAL_RESULT.json` (LOCKED engine). The Wave-6 sections (§1–§10) are retained as the
> book/overlay/deployability reference; read §0-W7 below FIRST for the current sizing posture.
>
> The core finding still stands — the EXISTING broad V4 selector loses live (-0.25R/fill native) and
> must be DISABLED. The gold sleeve is `metals_core`, one of eleven. Snapshot of record (book/parity):
> `INTEG_W6_FINAL_SNAPSHOT.json`; Wave-7 sizing/execution of record: `INTEG_W7_FINAL_RESULT.json`.

## 0-W7. WAVE-7 EXECUTIVE SUMMARY (the current go-live posture)

**The deployable product is the 11-sleeve `clean_3` book, tick-execution-corrected (HEATOIL+NATGAS
dropped), Kelly-lite conviction-sized, deployed at the GROWTH-OPTIMAL dial.** Objective: max
growth-rate s.t. FTMO (5% daily, 10% maxDD) at an acceptable P(maxDD breach) — NOT minimal size.

**What fear was costing (vs the prior conservative 0.75%):** at **1.50% nominal (1.13% eff)** the
book is **~1.8x faster to +8% (119→66 median days) and ~1.9x the monthly growth (1.36%→2.59%)** while
P(pass) stays **98.6%**, P(maxDD-breach) is only **1.41%**, and **real daily-breach is 0%**. The
binding constraint was never the daily rule (0% breach to 2.0% nominal) — it is the 1.5x-stress
maxDD-fail, which Kelly-lite cuts from 33.9% → ~20% at equal vol (forward-clean).

**Recommended dial:** first cycle **1.25% nominal half-Kelly** (daily-breach-free even under 1.5x
stress, P(pass) 99.4%, P(maxDD) 0.65%, ~1.5x faster); step to **1.50% handset Kelly + reactive
`stress_derisk` overlay** after the first account clears; hard ceiling **2.00%/account**.

| dial | nom | eff | P(pass) | P(maxDD) | str15 maxDD-fail | med days | monthly % | $/100k/mo |
|---|---|---|---|---|---|---|---|---|
| conservative (old) | 0.75% | 0.56% | 99.99% | 0.01% | 9.1% | 119 | 1.36% | $1,295 |
| **measured (1st cycle)** | **1.25%** | **0.94%** | **99.36%** | **0.65%** | **20.9%** | **79** | **2.16%** | **$2,158** |
| **growth-optimal** | **1.50%** | **1.13%** | **98.59%** | **1.41%** | **20.4%** | **66** | **2.59%** | **$2,590** |
| aggressive ceiling | 2.00% | 1.50% | 95.73% | 4.27% | 25.5% | 49 | 3.45% | $3,453 |

Tracks folded: T2 tick-true (drop HEATOIL+NATGAS), T3 Kelly-lite growth sizing. Tracks T1 (un-cap),
T4 (reinstate sleeves), T5 (static-audit) returned NULL deploy changes (each quantified — the winsor
is dead weight, dropped sleeves are sub-Sharpe growth drags, maxbars is a live-package-only fix). T6
(confluence router) stays a default-off size-up overlay. The deployable surface
`ultimate_book_live_package.py` (78 tests) already wires Kelly-lite + growth profiles, default-off.

## 0. Executive summary

The deployable product is **`clean_4`**: the locked Wave-3 8-sleeve core **+ 3 data-chosen Wave-4/5
additives** (`sub_xvol_pullback` 0.45, `vp_euidx_pocgrav` 0.30, `sub_mid_dn_revert` 0.20) **+ 1
Wave-6 additive** (`session_leadlag_genuine` 0.15, genuine cross-asset session-open leads), deployed
at the **vol-matched effective 0.71-0.74%/unit** with validated **confluence size-up overlays**
(leader-impulse veto, session-active stack) AND a **reactive temporal stress de-risk overlay**
(ladder+coloss, default-on recommended). Every sleeve is forward-validated (TRAIN ≤2024 / FWD 2025-26
+ per-year + n), leak-free (features index≤i, `geometry_lib.simulate` / `cs.exit_state_d` labeler),
and **net of real cost** (`w1.cost_for(sym)`). The book is structurally incapable of a single-day
FTMO breach at any sane size (0% daily-breach, worst day -2.02% @1%).

The binding constraint was never per-trade EV — it was the **diversification-aware challenge-pass MC
+ 1.5x left-tail stress on a vol-matched (risk-equivalent) ablation**. That gate chose `clean_4` over
"add everything": of six Wave-6 candidates, ONE new sleeve folded, ONE overlay folds default-on, ONE
exit-honest refinement is adopted, and THREE were correctly rejected (broad leadlag -22pts;
leader-veto folded-as-sleeve is book-pass-negative; the confluence router has +0.20R mean but ZERO
stress lift). Diversification banks as a **higher pass-rate floor**, not bigger bets. Nothing deleted.

Remaining blocker to live is **RUNTIME / BROKER AUTHORITY**, not strategy (per CLAUDE.md first
unresolved proofs). The deployable surface is `ultimate_book_live_package.py` (pure decision/sizing/
governor library, schema v3, default-off, zero broker authority, **69 passing tests**).

## 1. THE FINAL DEPLOY BOOK — `clean_4` (12 sleeves)

`clean_4` = `clean_3` (source `INTEG_W5_CLEAN3_DEPLOY.json`, reproduced byte-identically) + the ONE
Wave-6 additive sleeve. Confidence weights are parity-checked against the artifacts by
`assert_clean3_parity()` (PASS) and `assert_confidence_parity()` (PASS); the full consolidation is
parity-gated by `INTEG_W6_FINAL_SNAPSHOT.py` (parity_ok=True).

clean_3 avg off-diag daily-R corr **+0.0027** (min -0.119, max +0.116); the W6 sleeve adds an
independent `leadlag` cluster at corr **+0.053** vs the book. **Sharpe 0.1586** (clean_3 0.1522,
book-only 0.1396 → each additive raises Sharpe). Re-vol-matched at vol_scale **0.9873** (clean_3 0.9481).

| sleeve | cluster | conf | share | TRAIN EV (n) | FWD EV (n) | fwd/yr | source |
|---|---|---|---|---|---|---|---|
| crypto | crypto | 0.85 | 35.6% | +1.77 (21) | +0.95 (83) | 42 | W3 core |
| metals_core (the gold anchor) | metals | 1.00 | 23.0% | +0.68 (82) | +1.23 (49) | 25 | W3 core |
| energy_agri | energy | 0.80 | 20.8% | +0.16 (64) | +0.69 (98) | 49 | W3 core |
| **sub_xvol_pullback** | **substrate** | **0.45** | **9.2%** | **+0.75 (39)** | **+1.61 (51)** | **26** | **W4 substrate** |
| fx_jpy (London) | jpy | 0.15 | 4.3% | fwd-only | +0.17 (530) | 265 | W3 core (falsified→breadth) |
| **sub_mid_dn_revert** (W6: VP-acc def) | **substrate** | **0.20** | **4.1%** | **+0.09 (269)** | **+0.49 (129)** | **64→33** | **W4 + W6 exit-honest** |
| **vp_euidx_pocgrav** | **volprofile** | **0.30** | **3.9%** | **+0.22 (111)** | **+0.24 (230)** | **115** | **W4 volume-profile** |
| metals_softband | metals | 0.50 | 2.1% | +0.57 (31) | +0.14 (39) | 20 | W3 core |
| fx_jpy_ny | jpy | 0.15 | 1.0% | fwd-only | +0.15 (197) | 99 | W3 core |
| metals_ob_micro | metals | 0.30 | -0.7% | -0.70 (5) | -0.17 (2) | 1 | W3 core (kept tiny) |
| idxrev | index | 0.15 | -3.2% | -0.06 (4447) | +0.03 (2026) | 1013 | W3 core (falsified→breadth) |
| **session_leadlag_genuine** | **leadlag** | **0.15** | **NEW** | **fwd-only** | **+0.46 (390)** | **195** | **NEW W6 cross-asset lead** |

**Nothing is deleted**: the two data_depth-falsified core sleeves (`fx_jpy`, `idxrev`) are demoted to
0.15 breadth, never zero. `metals_ob_micro` is kept tiny. The integrator chose every additive by the
vol-matched stress gate, not corr alone. The W6 sleeve is the TRIMMED genuine cross-asset session-open
LEAD subset (US30→GER40/USDJPY/AUDJPY ny_open + USDJPY→AUDJPY london_ny, null-cleared z3.09-4.66); the
broad session-leadlag set incl. JPY-cross legs was DILUTIVE (-22pts stress) and is EXCLUDED.

## 2. TRADES / YEAR (net of fills) and FREQUENCY

All R are NET of real cost (`w1.cost_for`) through the pessimistic `geometry_lib` fill — these ARE
net-of-fills numbers, no separate slippage haircut is double-applied.

- Book core: **~1512 tr/yr** forward.
- clean_3 additives: sub_xvol_pullback ~26 + vp_euidx_pocgrav ~115 + sub_mid_dn_revert ~64 = **~205 tr/yr**.
- clean_3 DEPLOY subtotal: **~1717 tr/yr forward**.
- W6 session_leadlag_genuine: **~195 tr/yr** (forward-only since 2025-06).
- **`clean_4` DEPLOY total: ~1912 tr/yr forward** (correlated-unit-collapsed to far fewer
  independent risk units/day). Net-of-fills book contribution erodes only **5.61%** (W3 exec-realism).

## 3. P(PASS) — challenge-pass MC (vol-matched = the fair test)

20,000 paths, FTMO 8% target / 5% daily / 10% maxDD, BLOCK=5, whole-cross-sectional-day
block-bootstrap (preserves true cross-sleeve covariance). Deploy risk × **vol_scale 0.9481** so daily
std == book-only; diversification then banks as a higher pass-rate floor.

| risk | DEPLOY@vm P(pass) | DEPLOY@vm STRESS1.5x | BOOK P(pass) | BOOK STRESS1.5x | DEPLOY FWD-only |
|---|---|---|---|---|---|
| 0.50% | 100.00% | 95.30% | 100.00% | 96.19% | 100.00% |
| 0.71% (≈0.75% nom) | 99.98% | 87.16% | 99.98% | 89.33% | 100.00% |
| 1.00% | 99.91% | 80.86% | 99.79% | 82.66% | 99.94% |
| 1.50% | 98.51% | 70.93% | 98.62% | 72.86% | 99.32% |
| 2.00% | 95.75% | 64.79% | 95.59% | 65.56% | 97.45% |

- **Unstressed**: deploy holds the book's near-certain pass floor (99.91% @1%); the +205 tr/yr of
  orthogonal breadth deepen diversification without raising failure.
- **Adversarial 1.5x left-tail STRESS** (the binding constraint): deploy 80.86% vs book 82.66% @1% —
  a ~1.8pt cost, the price of the additive breadth, NOT a tail blowup. (The excluded leadlag/gate
  variants cost 10-14pts here — that is exactly why they were cut.)

## 4. STRESS — the verdict gate

Every book change was judged on the **vol-matched 1.5x-stress pass-rate**, never per-trade EV alone.
Per-sleeve single-add ablation (book + ONE new sleeve, vol-matched, stress@1.5%, book 72.75%):

| + sleeve | Sharpe (book 0.128) | vm-stress@1.5% | verdict |
|---|---|---|---|
| sub_xvol_pullback | 0.1387 | 75.06% | **ADDITIVE** (lifts both axes) |
| vp_euidx_pocgrav | 0.1295 | 69.03% | mild-dilutive solo, Sharpe-accretive in combo → kept |
| sub_mid_dn_revert | 0.1304 | 65.84% | mild-dilutive solo, Sharpe-accretive in combo → kept |
| leadlag_core (0.10) | 0.1280 | 65.70% | dilutive → EXCLUDED |
| subh4_ll_fx (0.15) | 0.1255 | 64.70% | dilutive → EXCLUDED |

In the whole-book risk-equivalent selection, `clean_3` is the Sharpe maximum AND the only additive
variant that keeps the @1.5% stress tail within ~2pts of book-only. The selection table is
authoritative (it is the deployed configuration).

### 4a. WAVE-6 stress-hardening (the binding constraint, RAISED)

The 1.5x left tail is a **temporal-clustering** problem: crypto = **49.4%** of the worst-5%-loss-day
mass; failing MC paths are runs of conf-weighted −0.93 crypto days (2025-11-06…11, 2026-04-23…28)
plus the lone −2.02 metals day (2025-06-13). Static per-sleeve vol-target is NULL (cap never binds).
Two W6 changes RAISE the binding constraint (both default-off, owner flips):

1. **The W6 sleeve raises the stress floor.** clean_4 (clean_3 + session_leadlag_genuine) lifts
   stress@1% **80.86% → 82.24%** and @1.5% **70.93% → 72.06%** — additive breadth that improves the
   binding constraint, not just survives it (the broad leadlag set was −22pts and was excluded).

2. **Reactive temporal de-risk overlay** (leak-free, uses only realized days < t):

   | overlay | Sharpe | stress@1% | Δ@1% | stress@1.5% | FWD Δ@1% | tier |
   |---|---|---|---|---|---|---|
   | clean_3 baseline | 0.1522 | 80.86% | — | 70.93% | — | — |
   | ladder only | 0.1554 | 83.87% | +3.0 | 73.98% | +1.1 | leg |
   | coloss only | 0.1554 | 84.78% | +3.9 | 75.46% | +1.7 | leg |
   | **reactive ladder+coloss (DEFAULT-ON)** | **0.1564** | **87.48%** | **+6.6** | **77.60%** | **+2.0** | **1** |
   | full stack regime+ladder+coloss | 0.1568 | 91.86% | +11.0 | 83.09% | +1.7 | 2 (opt-in) |

   **Tier-1 reactive is forward-clean** (positive on the 2025-26 holdout by construction). **Tier-2's
   regime component is forward-FLAT alone** → opt-in only after the reactive layer is proven live.
   Wired as a day-level multiplier ON TOP of fixed sleeve confidence (sizing-by-confidence preserved);
   it ONLY ever shrinks size (floor 0.60). Combined 87.48% is the builder Section-3 result; the cached
   `KB6_COMBINE_RESULT.json` reproduces the individual legs (83.87 / 84.78) + the regime stacks.

3. **Exit-honesty correction + VP-acceptance.** The shipped `clean_3` scored `sub_*` at fixed 1:3R,
   but runtime is STATE_D scale-out (~2.5pts lower headroom: fixed-3R 72.1% → exit-honest 69.6%
   @1.5%). The W6 **VP-acceptance** refinement of `sub_mid_dn_revert` (`vp_loc=above_va`, 16%-retention
   noise-cut) RECOVERS and exceeds that: STATE_D stress@1.5% **69.6% → 74.8%** (+5.2), Sharpe
   0.148 → 0.151, flat 2/2 forward years. Adopted as the exit-honest `sub_mid_dn_revert` definition
   (`vp_acceptance=True`). It is the ONLY confluence overlay that LIFTS the stress tail — the
   leader-veto folded-as-sleeve and the confluence router both FAIL this gate (see §6).

## 5. ALLOCATION — recommended 2-account live config

Both accounts trade the FULL deploy book (diversification is WITHIN each account, per the Wave-1
finding). Sizes shown at vol-matched **effective** risk. **Daily-breach = 0% at every size**; worst
single day -2.02% @1.0%, -4.04% @2.0% — structurally incapable of a single-day -5% breach at any sane
size (diversification caps per-day concentration).

| config | eff size A | eff size B | P(both) base | P(both) FWD | P(both) STRESS1.5x | + reactive overlay |
|---|---|---|---|---|---|---|
| **balanced (RECOMMENDED)** `clean3_balanced_eff0p71` | 0.71% | 0.71% | **99.99%** | 100.00% | 70.30% | **→ 77.36% (+7.1)** |
| conservative `clean3_conservative_eff0p47` | 0.47% | 0.47% | 100.00% | 100.00% | 79.51% | **→ 86.99% (+7.5)** |
| clean_4 balanced `clean4_balanced_eff0p74` | 0.74% | 0.74% | 99.98% | 100.00% | 72.34% | (reactive lift applies) |
| clean_4 conservative `clean4_conservative_eff0p49` | 0.49% | 0.49% | 100.00% | 100.00% | 80.10% | (reactive lift applies) |
| staggered A1.0/B0.75 | 0.95% | 0.71% | 99.88% | 99.97% | 59.97% | → 67.02% (+7.1) |

(All daily-breach = 0.00% at every size.) **[SUPERSEDED BY §0-W7]** The Wave-6 conservative
recommendation (0.47–0.49% eff first cycle) was the fear-distilled posture. **Wave-7 growth-optimal
recommendation: first cycle 1.25% nominal (0.94% eff) half-Kelly; step to 1.50% (1.13% eff) handset
Kelly + reactive overlay; ceiling 2.00%.** 2-account FINAL: balanced 1.25/1.25 → P(both) 99.28%
base / 63.7% stress; balanced 1.50/1.50 → 98.52% / 59.7%; conservative 0.75/0.75 → 99.99% / 75.0%.
Daily-breach 0% at every size. Staggering still buys nothing (shared edge). See `INTEG_W7_FINAL_RESULT.json`.

## 6. CONFLUENCE OVERLAYS — validated size-up selectors (wired, default-off)

Per "size by confidence, delete nothing": two INDEPENDENT, positively-signed confluence conditions
are wired as **size-up selectors on their base sleeves** (NOT separate sleeves — the leader-veto
subset has corr +0.79 with `sub_xvol_pullback` = same population filtered → double-count). Applied
multiplicatively, capped at `OVERLAY_SIZEUP_MAX = 1.75` so the unit can never exceed the worst-case
risk cap.

1. **leader_impulse_veto** (1.5x on `sub_xvol_pullback`): size up when NO relevant cross-asset leader
   (SPX/NAS/BTC/USDJPY/US30/XAU/DXY) is impulsing ≥1.5σ (`ll_impulse=none`). Base FWD +0.71R → veto
   cell **+1.53R pooled, perm-p 0.0003, both fwd years**; the mirror (leader opposed) is forward
   -0.35R — the sign is real. (Sized at 1.5x, not the raw 2.16x R-ratio, to stay governor-safe.)
2. **session_active_stack** (1.15x on `sub_xvol_pullback`, `sub_mid_dn_revert`): size up when the H4
   decision bar hour ∈ {8,12,16} (London open .. NY) — an independent directional-follow-through
   family (KB5 `c_session_active`).

**Highest-odds confluent pockets** (confluence of INDEPENDENT, positively-signed conditions — φ +
perm-null + per-year + n): (1) **xvol pullback × leader-veto** = +1.53R fwd perm-p 0.0003 2/2 yrs
(the deployed 1.5x size-up); (2) **xvol pullback × veto × liq_align=aligned** = FWD +1.73R (n23),
TRAIN +0.58R (n20), perm-p 0.001 — train+fwd-positive on BOTH sides (KB6 frontier-2; a better-evidenced
3rd gate than above_va; live-monitoring conviction tag); (3) **xvol_dn_aligned_london × vol_expansion
× liq_align** = FWD +1.62R (n28), TRAIN +0.25R (n49), perm-p 0.000; (4) **mid_dn_revert × VP-acceptance**
(the adopted exit-honest def, §4a).

**Documented but EXCLUDED / not-folded** (kept as breadth/intel, deep-tail cost exceeds value):
- `leadlag_core` (index/JPY H4 spillover), `subh4_ll_fx` (USDJPY→EURJPY London, FWD +0.76R n56 but
  38% win at fixed R) — dilutive; the GENUINE cross-asset lead subset IS folded as `session_leadlag_genuine` (§1).
- **leader-veto folded AS A SLEEVE**: +1.17R/trade, 87.5% win, but BOOK-pass NEGATIVE
  (vm-stress@1.5% 69.6% → 67.9%) — its 61% frequency retention shrinks diversification faster than EV
  helps. Stays a SIZE-UP overlay, never a column (the exact "never per-trade EV alone" trap).
- **confluence-score router (REJECTED as sizer)**: +0.20R forward mean lift but **ZERO stress lift**
  (flat 69.1% vs router 68.6–69.3%; flagship-only 77.0% vs 76.7%) — it concentrates size into
  high-variance pockets, buying mean not left-tail survivability. The strong gates (veto, liq) are
  forward-only on non-flagship bases, so a no-lookahead sign-learner anti-selects them. Kept as
  live-monitoring intel (`describe_book().clean4.confluence_router.wired = False`).
- `metals_sess_stack` (90%-same-trade double-count of metals_core, corr +0.65) → size-up overlay only;
  `dxy_bias` (n=12 fwd, no train) → confidence-nudge filter only.

**Universal exclusions** (applied in the selector to all xvol-up longs): drop `hurst=trend` (inverts,
fwd -0.74R), drop leader-impulse-opposed bars (fwd -0.35R), drop `regime=vol_expansion` (fwd -0.15R).

## 7. DEPLOYABLE SURFACE (what production wires to)

`ultimate_book_live_package.py` — pure decision/sizing/governor library. NO network, NO MT5, NO
broker, NO order placement. It turns per-sleeve candidate intents into confidence-weighted,
correlated-risk-unit-governed, fail-closed sizing decisions.

- `describe_book()` → machine-readable book (8 core locked + `clean3` block + `clean4` block: the W6
  sleeve, vp_acceptance, stress de-risk overlays, router documented-disabled, profiles). schema
  `ultimate_book_live_package_v3`.
- `admit_and_size(intents, state, profile=..., include_clean4=True, overlays=True, vp_acceptance=True,
  stress_derisk=True, stress_state=...)` → governor gate then correlated-unit sizing with overlay
  size-up + reactive day-level de-risk. **ALL upgrade flags default OFF** (owner flips at go-live);
  default surface is the locked 8-sleeve book. `include_clean4` implies clean_3.
- FAIL-CLOSED governors: soft daily-stop -3% (hard -5% never approached), max-DD de-risk band 7-10%,
  gross open-risk cap 4%, outer operator circuit-breaker, any missing/contradictory state → size 0.
- W6 reactive de-risk (`stress_derisk_multiplier`) is leak-free (realized days < t only) and ONLY
  shrinks size (floor 0.60); VP-acceptance drops non-`above_va` `sub_mid_dn_revert` intents.
- ALL outcome labeling routes through `geometry_lib.simulate` (leak-free, R winsorized [-1.3,+5]).
- **Tests: 69 passing** (`test_ultimate_book_live_package.py`) — registry/parity, correlated-unit
  sizing, fail-closed governor, leak-free labeling, clean_3/clean_4 default-off + sizing + parity,
  confluence overlays, W6 sleeve (independent cluster), VP-acceptance noise-cut, reactive stress
  de-risk (ladder/coloss/floor/only-shrinks/off-by-default), router-disabled, vol-matched profiles,
  import-safety (zero heavy deps on the deployable path, checked in a clean subprocess).
- **Replay-vs-module parity**: `INTEG_w5_clean3_deploy.py` reproduces `INTEG_W5_CLEAN3_DEPLOY.json`
  byte-identically; the module parity-checks confidence weights + vol_scale + 11-sleeve book against
  that artifact (PASS); `INTEG_W6_FINAL_SNAPSHOT.py` is parity-gated (parity_ok=True).

## 8. GO-LIVE CHECKLIST (the actual remaining work)

1. **DISABLE the broad incumbent selector + scheduler.** The native V4 selector loses live
   (-0.25R/fill, -113.4R over 454 fills, negative every month — confirms hard-halt history). Go-live
   is a NARROW REPLACEMENT: run ONLY the `clean_3` book rules through the new sizing surface, NOT an
   augmentation of the existing selection. Restrict the live universe to the 11-sleeve symbol set;
   remove any stale 24/46-symbol broad surface from config.
2. **WIRE the deploy book (default-off → owner flip).** Production calls `admit_and_size(...,
   include_clean4=True, overlays=True, vp_acceptance=True, stress_derisk=True, stress_state=...,
   profile="clean4_conservative_eff0p49")` for the first cycle. Per-sleeve generators
   (sub_xvol_pullback / vp_euidx_pocgrav / sub_mid_dn_revert / session_leadlag_genuine) emit
   `TradeIntent`s with leak-free `ll_impulse` + `decision_hour` + `vp_loc` tags so the overlays +
   VP-acceptance fire correctly; the runtime feeds `StressDeriskState` (consecutive-loss / trailing
   neg-frac from realized prior days) for the reactive de-risk. clean_3 generators are materialized in
   `INTEG_W5_new_streams_cache.pkl` (reproduced by `INTEG_portfolio_build_w5.py`); the W6 sleeve is the
   genuine cross-asset lead subset (`KB6_session_stacks.py`).
3. **SIZE at the vol-matched effective risk.** First challenge cycle: conservative 0.47%/0.47%
   (stress 79.5%). After the first account clears: balanced 0.71%/0.71% (P(both) 99.99% base).
   Correlated-risk-unit sizing collapses same-day same-cluster sleeves to ONE unit; gross open-risk
   cap 4%; outer circuit-breaker armed.
4. **CLEAR THE RUNTIME / BROKER-AUTHORITY BLOCKER** (per CLAUDE.md first unresolved proofs): hard-halt
   row-level forensic join, V3-vs-live authority-gap audit, dual-broker architecture audit,
   production-return dossier — so go-live is NOT a revert to pre-halt weak behavior. This is the real
   gate, not strategy.
5. **DEPLOY small on ONE challenge account; scale only on live confirmation.** Verify live fills match
   the pessimistic `geometry_lib` labeler before stepping size or adding the second account.

## 8a. PER-DIMENSION SCORECARD (D1–D6, honest — Wave-7 refresh)

| dim | what | grade | evidence / honest gap |
|---|---|---|---|
| **D1 Edge reality** | leak-free, real-cost, forward-holdout per sleeve | **A** | 11 sleeves TRAIN/FWD + per-year + n-gated; corr ~0; **execution now TICK-TRUE** (per-symbol bid/ask, not a class proxy) on every tick-serviceable leg; illiquid cost-map artifacts (HEATOIL/NATGAS) dropped. Gap: vp/fx layers forward-only; GBPJPY/ETH/CORN/COTTON no bridge feed (transfer-only, flagged). |
| **D2 Diversification / corr** | independent risk units, low cross-corr | **A** | avg off-diag +0.003; correlated-unit collapse enforced; both-account full book. |
| **D3 Challenge survivability** | vol-matched P(pass) + daily-breach | **A** | 99.4%@1.25% / 98.6%@1.5%, **0% daily-breach at EVERY size to 2.0%**, worst real day −3.63%@1.5%; structurally cannot single-day −5%. |
| **D4 Stress / left tail** | 1.5x adversarial, the binding gate | **B+** | Kelly-lite cuts stress maxDD-fail 33.9%→~20% @1.5% (forward-clean); tail is a 2025 crypto/metals temporal-clustering problem, addressed by half-Kelly top + reactive `stress_derisk`. Handset top bin grazes the daily wall under 1.5x inflation (breach-free in reality). Honest ceiling, not bulletproof. |
| **D5 Deployability** | default-off, fail-closed, tested, parity | **A** | pure library, zero broker authority, **78 tests**, byte-parity vs locked artifacts, import-safe; Kelly-lite + growth profiles wired (default-off). |
| **D6 Go-live readiness** | actual path to live | **C** | strategy + growth-optimal sizing ready; gated by the 2 infra blockers (§8.1, §8.4), NOT edge. |

## 9. HONEST CAVEATS (size for these, do not hide them)

1. **Forward window is short** (2025 + partial 2026). The VP layer is M1-since-2024 → essentially
   forward-only (flagged); deep H4 layers (metals/crypto/energy) have full 2014-26 depth. Distrust
   single-fwd-year positives; the substrate cells are 1/2-or-2/2-fwd-year — real but young.
2. **The substrate/VP additives answer a fixed 1:3R question** while the deployed exit is STATE_D
   scale-out; re-mining under STATE_D will shift their mean_R (next-step §10).
3. **The 1.5x adversarial stress is the honest ceiling**: 80.86% @1% — the book is challenge-robust,
   not stress-bulletproof. Held within ~2pts of book ONLY because the dilutive high-freq sleeves were
   excluded.
4. **The deploy surface has zero broker authority by design**; live behavior depends on the
   runtime/broker-authority work in §8.4 being done first.

## 10. NEXT STEPS (build queue, post-deploy hardening)

1. Re-mine the substrate additives + the cross-layer flagship under the deployed STATE_D scale-out
   exit (not fixed 1:3R) — the xvol flagship mean_R likely shifts; some 1/2-fwd-year cells may cross
   to 2/2.
2. Mine `leadlag_core`'s highest-per-trade-Sharpe legs only (US30→USDJPY, NAS100↔SPX500) to recover a
   non-dilutive index-spillover sleeve.
3. Deepen the VP TRAIN side via pre-2024 M1 export to convert `vp_euidx_pocgrav` + the `above_va`
   confluence pocket from forward-only to true holdout.

---
### Artifacts
- FINAL snapshot of record: `INTEG_W6_FINAL_SNAPSHOT.json` ← `INTEG_W6_FINAL_SNAPSHOT.py` (parity-gated)
- Deploy book base: `INTEG_W5_CLEAN3_DEPLOY.json` (locked) ← `INTEG_w5_clean3_deploy.py`
- Assembly/selection: `INTEG_portfolio_build_w5.py` → `INTEG_PORTFOLIO_W5_RESULT.json`
- Deployable module: `ultimate_book_live_package.py` v3 (+ `test_ultimate_book_live_package.py`, 69 tests)
- W6 evidence: `KB6_SESSION_STACKS_RESULT.json` (clean_4 sleeve), `KB6_COMBINE_RESULT.json` +
  `KB6_stress_hardening.md` (reactive overlay), `KB6_OVERLAY_PASSRATE_RESULT.json` +
  `KB6_confluence_state_d.md` (VP-acceptance), `KB6_ROUTER_RESULT.json` (router-rejected),
  `KB6_DEEP_STACKS_RESULT.json` + `KB6_confluence_frontier_2.md` (liq_align pockets)
- Confluence evidence: `KB5_FRONTIER.json`, `KB5_cross_layer_miner.py`, `KB5_condition_families.py`
- Build narrative: `PORTFOLIO_BUILD_W6.md` (current), `PORTFOLIO_BUILD_W5.md`, `SUBSTRATE_BUILD.md`,
  `KB6_wire_final_book.md`
