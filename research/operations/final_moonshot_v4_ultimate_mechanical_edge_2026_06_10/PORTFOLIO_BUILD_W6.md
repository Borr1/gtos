# PORTFOLIO BUILD — WAVE 6 (FINAL consolidation)

Builder + integrator track, 2026-06-15. Assemble the FINAL deploy book from the Wave-5 `clean_3`
base + every Wave-6 finding that survives the binding constraint, wire it all DEFAULT-OFF into the
deployable surface, and refresh the go-live dossier. Result-first, leak-free, forward-validated,
net of real cost. **The verdict gate is the diversification-aware challenge-pass MC + 1.5x left-tail
STRESS on a vol-matched (risk-equivalent) ablation — never per-trade EV alone.**

Snapshot of record: `INTEG_W6_FINAL_SNAPSHOT.json` (reproduced by `INTEG_W6_FINAL_SNAPSHOT.py`,
parity-gated against the locked artifacts). Module: `ultimate_book_live_package.py` schema v3.

---

## 0. What W6 changed vs the shipped W5 `clean_3` book

W5 shipped `clean_3` (11 sleeves) wired into the live package. W6 re-mined six candidate
improvements under the REAL exit (`cs.exit_state_d`) and the binding vol-matched 1.5x stress MC.
**Exactly ONE new sleeve folded, ONE new overlay folds default-on, ONE exit-honest refinement is
adopted, and three candidates were correctly REJECTED to overlay/intel.** Nothing was deleted.

| W6 candidate | verdict | binding-constraint evidence |
|---|---|---|
| **session_leadlag_genuine** (genuine cross-asset session-open LEADs) | **FOLD as sleeve → `clean_4`** | Sharpe 0.1522→**0.1586**, stress@1% **+2.51**, @1.5% **+2.03**, corr +0.053; the trimmed genuine-lead subset (broad set was −22pts) |
| **reactive ladder+coloss** temporal de-risk | **FOLD as default-on overlay** | stress@1% 80.86→**87.48** (+6.6), **forward-POSITIVE +2.0**, Sharpe →0.1564 |
| **full-stack regime+ladder+coloss** | **OPT-IN tier-2** | stress@1% →**91.86** (+11.0) but regime component forward-FLAT alone |
| **VP-acceptance** (`vp_loc=above_va`) refinement of `sub_mid_dn_revert` | **ADOPT (exit-honest def)** | STATE_D stress@1.5% 69.6→**74.8** (+5.2), only confluence overlay that lifts the tail |
| **leader_impulse_veto** | **OVERLAY only** (already wired) | +1.17R/trade but BOOK-pass NEGATIVE if folded (61% freq retention shrinks diversification) |
| **confluence-score router** | **REJECT as sizer → intel** | +0.20R mean but **ZERO stress lift** (flat 69.1% vs router 68.6–69.3%) |
| metals_sess_stack / dxy_bias | overlay / filter | 90%-same-trade double-count (corr +0.65) / n=12 fwd |

This is the doctrine in action three times over: a +EV sleeve was cut (broad leadlag, −22pts),
a +EV overlay was kept only as a size-up not a sleeve (leader-veto, frequency drag), and a +0.20R
router was rejected because mean ≠ left-tail survivability.

---

## 1. THE FINAL DEPLOY BOOK — `clean_4` (12 sleeves)

`clean_4` = the locked W3 8-sleeve core + 3 W4/5 additives (`clean_3`) + 1 W6 additive
(`session_leadlag_genuine`). avg pairwise off-diag daily-R corr **+0.0027** (clean_3); the W6 sleeve
adds an independent `leadlag` cluster at corr **+0.053** vs the book. Sharpe **0.1586** (clean_3
0.1522, book-only 0.1396). Re-vol-matched on the LOCKED W2 MC at **vol_scale 0.9873** (vs clean_3's
0.9481 — the extra orthogonal breadth lets the fair vol-match run slightly hotter, 0.74% vs 0.71%).

| sleeve | cluster | conf | share | TRAIN EV (n) | FWD EV (n) | fwd/yr | source |
|---|---|---|---|---|---|---|---|
| crypto | crypto | 0.85 | 35.6% | +1.77 (21) | +0.95 (83) | 42 | W3 core |
| metals_core (gold anchor) | metals | 1.00 | 23.0% | +0.68 (82) | +1.23 (49) | 25 | W3 core |
| energy_agri | energy | 0.80 | 20.8% | +0.16 (64) | +0.69 (98) | 49 | W3 core |
| **sub_xvol_pullback** | substrate | 0.45 | 9.2% | +0.75 (39) | +1.61 (51) | 26 | W4 substrate |
| fx_jpy (London) | jpy | 0.15 | 4.3% | fwd-only | +0.17 (530) | 265 | W3 (falsified→breadth) |
| **sub_mid_dn_revert** (W6: VP-acc def) | substrate | 0.20 | 4.1% | +0.09 (269) | +0.49 (129) | 64→33 | W4 + W6 exit-honest |
| **vp_euidx_pocgrav** | volprofile | 0.30 | 3.9% | +0.22 (111) | +0.24 (230) | 115 | W4 volume-profile |
| metals_softband | metals | 0.50 | 2.1% | +0.57 (31) | +0.14 (39) | 20 | W3 core |
| fx_jpy_ny | jpy | 0.15 | 1.0% | fwd-only | +0.15 (197) | 99 | W3 core |
| metals_ob_micro | metals | 0.30 | -0.7% | -0.70 (5) | -0.17 (2) | 1 | W3 core (kept tiny) |
| idxrev | index | 0.15 | -3.2% | -0.06 (4447) | +0.03 (2026) | 1013 | W3 (falsified→breadth) |
| **session_leadlag_genuine** | **leadlag** | **0.15** | **NEW** | **fwd-only** | **+0.46 (390)** | **195** | **W6 cross-asset lead** |

Nothing deleted. The two data_depth-falsified core sleeves (`fx_jpy`, `idxrev`) stay at 0.15 breadth.

---

## 2. TRADES / YEAR (net of fills)

All R are NET of real cost (`w1.cost_for`) through the pessimistic `geometry_lib` fill — no separate
slippage haircut is double-applied. Net-of-fills book contribution erodes only **5.61%**
(modeled 103.03 → net 97.25 conf-wtd unit-R/yr; W3 exec-realism, `INTEG_GOLIVE_SNAPSHOT_RESULT.json`).

- clean_3 deploy total: **~1717 tr/yr** forward.
- W6 session_leadlag_genuine: **~195 tr/yr** (forward-only since 2025-06).
- **`clean_4` DEPLOY total: ~1912 tr/yr forward** (correlated-unit-collapsed to far fewer independent
  risk units/day).

---

## 3. P(PASS) — challenge-pass MC, vol-matched (the fair test)

LOCKED W2 engine: 20,000 paths, BLOCK=5, whole-cross-sectional-day block-bootstrap (preserves true
cross-sleeve covariance), FTMO 8% / 5% daily / 10% maxDD. Deploy risk × vol_scale so daily
std == book-only; diversification banks as a higher pass-rate FLOOR, not bigger bets.

| risk | clean_3 P(pass) | clean_3 STRESS1.5x | clean_4 folded STRESS@1% | FWD-only P(pass) |
|---|---|---|---|---|
| 0.50% | 100.00% | 95.30% | — | 100.00% |
| 0.71/0.74% (≈0.75% nom) | 99.98% | 87.16% | — | 100.00% |
| 1.00% | 99.91% | 80.86% | **82.24%** | 99.94% |
| 1.50% | 98.51% | 70.93% | (72.06% @1.5%) | 99.32% |
| 2.00% | 95.75% | 64.79% | — | 97.45% |

Unstressed P(pass) holds the near-certain floor (99.91% @1%). The W6 sleeve RAISES the stress floor
(clean_4 stress@1% 82.24% vs clean_3 80.86%) — additive breadth that improves the binding constraint.

---

## 4. STRESS — the binding constraint, hardened (the verdict gate)

The 1.5x left tail is a **temporal-clustering** problem: crypto = **49.4%** of the worst-5%-loss-day
mass; failing MC paths are runs of conf-weighted −0.93 crypto days (2025-11-06…11, 2026-04-23…28)
plus the lone −2.02 metals day (2025-06-13). Static per-sleeve vol-target is NULL (cap never binds).
The fix is a leak-free **reactive temporal de-risk** multiplier (uses only realized days < t):

| overlay | Sharpe | stress@1% | Δ@1% | stress@1.5% | FWD Δ@1% | tier |
|---|---|---|---|---|---|---|
| `clean_3` baseline | 0.1522 | 80.86% | — | 70.93% | — | — |
| ladder only | 0.1554 | 83.87% | +3.0 | 73.98% | +1.1 | (leg) |
| coloss only | 0.1554 | 84.78% | +3.9 | 75.46% | +1.7 | (leg) |
| **reactive ladder+coloss (DEFAULT-ON)** | **0.1564** | **87.48%** | **+6.6** | **77.60%** | **+2.0** | **1** |
| full stack regime+ladder+coloss | 0.1568 | 91.86% | +11.0 | 83.09% | +1.7 | 2 (opt-in) |

**Tier-1 reactive is forward-clean** (positive on the 2025-26 holdout by construction — it trims size
after a realized loss/co-loss spike, no fitted regime). **Tier-2's regime component is forward-FLAT
alone** (a full-history optimizer; KB3 caveat confirmed) → opt-in only after the reactive layer is
proven live. Wired as a day-level multiplier ON TOP of fixed sleeve confidence (sizing-by-confidence
preserved); it ONLY ever shrinks size (floor 0.60).

**Exit-honesty correction (W6).** The shipped `clean_3` scored `sub_*` at fixed 1:3R, but runtime is
STATE_D scale-out. Under STATE_D the book's stress headroom is ~2.5pts lower (fixed-3R 72.1% →
exit-honest 69.6% @1.5%). The W6 **VP-acceptance** refinement of `sub_mid_dn_revert`
(`vp_loc=above_va`, a 16%-retention noise-cut) RECOVERS that and more: STATE_D stress@1.5%
**69.6% → 74.8%** (+5.2), Sharpe 0.148 → 0.151, flat 2/2 forward years (2025 +0.56 / 2026 +0.59). It
is adopted as the exit-honest `sub_mid_dn_revert` definition (default-off `vp_acceptance=True`).

---

## 5. ALLOCATION — recommended 2-account live config

Both accounts trade the full deploy book (diversification is WITHIN each account). Sizes at
vol-matched **effective** risk. **Daily-breach = 0% at every size**; worst single day −2.02% @1%.

| config | eff A | eff B | P(both) base | P(both) FWD | P(both) STRESS1.5x | + reactive overlay |
|---|---|---|---|---|---|---|
| **balanced (RECOMMENDED)** clean3 0.71% | 0.71% | 0.71% | 99.99% | 100.00% | 70.30% | **→ 77.36% (+7.1)** |
| conservative clean3 0.47% | 0.47% | 0.47% | 100.00% | 100.00% | 79.51% | **→ 86.99% (+7.5)** |
| clean_4 balanced 0.74% | 0.74% | 0.74% | 99.98% | 100.00% | 72.34% | (reactive lift applies) |
| clean_4 conservative 0.49% | 0.49% | 0.49% | 100.00% | 100.00% | 80.10% | (reactive lift applies) |

**Recommendation: first live cycle on conservative 0.47–0.49% effective + reactive overlay default-on**
(2-account stress P(both) ~87%); step up to balanced 0.71–0.74% after the first account clears.
Staggering (A1.0/B0.75) buys nothing (lower stress P(both)) — both accounts share the same edge.

---

## 6. HIGHEST-ODDS CONFLUENT SETUPS (size by confidence, delete nothing)

High odds = confluence of INDEPENDENT, positively-signed conditions (φ + perm-null + per-year + n).
The deployable, train+fwd-validated confluence pockets:

1. **xvol pullback × leader-impulse VETO** — `sub_xvol_pullback` long when NO cross-asset leader is
   impulsing ≥1.5σ (`ll_impulse=none`). Base FWD +0.71R → **+1.53R pooled, perm-p 0.0003, 2/2 yrs**;
   mirror (leader opposed) forward −0.35R. Wired as a 1.5x size-up SELECTOR (not a sleeve — corr +0.79
   with the base = double-count; +1.17R/trade but folding it shrinks diversification). **Highest odds.**
2. **xvol pullback × veto × liq_align=aligned** (KB6 frontier 2) — adds the liquidity sweep+reclaim
   3rd gate: FWD **+1.73R (n23), TRAIN +0.58R (n20), perm-p 0.001** — train+fwd-positive on BOTH
   sides (a better-evidenced 3rd gate than the original above_va). Live-monitoring conviction tag.
3. **xvol_dn_aligned_london × vol_expansion × liq_align** — FWD **+1.62R (n28), TRAIN +0.25R (n49),
   perm-p 0.000**. Candidate high-conviction selector pocket.
4. **mid_dn_revert × VP-acceptance** (`above_va`) — the adopted exit-honest definition (§4).
5. **session-active stack** (H4 hour ∈ {8,12,16}) — 1.15x size-up on substrate sleeves.

---

## 7. DEPLOYABLE SURFACE (what production wires to) — `ultimate_book_live_package.py` v3

Pure decision/sizing/governor library. NO network, NO MT5, NO broker, NO order placement. All W6
additions are **DEFAULT-OFF** behind owner-flipped flags:

- `include_clean4=True` → adds `session_leadlag_genuine` (implies clean_3); profiles
  `clean4_balanced_eff0p74` (recommended) / `clean4_conservative_eff0p49`.
- `vp_acceptance=True` → exit-honest noise-cut of `sub_mid_dn_revert` (drops non-`above_va`).
- `stress_derisk=True` + `stress_state` (realized prior-day facts) → reactive ladder+coloss day-level
  multiplier (TIER-1, recommended default-on); `StressDeriskState`, `stress_derisk_multiplier()`.
- TradeIntent gained leak-free `vp_loc`. `describe_book()` → schema **v3** with a `clean4` block
  (sleeve, vp_acceptance, stress overlays, router documented-disabled, profiles).
- The confluence-score router is described as `wired: False` (intel only) — it has NO stress lift.
- **Tests: 52 → 69, all pass.** Parity gates intact: `assert_clean3_parity()` PASS,
  `assert_confidence_parity()` PASS, `INTEG_W6_FINAL_SNAPSHOT.py` parity_ok=True.

---

## 8. PER-DIMENSION SCORECARD (D1–D6, honest)

| dim | what | grade | evidence / honest gap |
|---|---|---|---|
| **D1 Edge reality** | leak-free, real-cost, forward-holdout per-sleeve | **A−** | 12 sleeves all TRAIN/FWD + per-year + n-gated; corr ~0; net-of-fills erosion only 5.6%. Gap: 3 layers are forward-only (vp, session_leadlag_genuine since 2025-06, fx breadth). |
| **D2 Diversification / corr** | independent risk units, low cross-corr | **A** | avg off-diag +0.0027, leadlag cluster +0.053; correlated-unit collapse enforced; balanced 2-account both-book. |
| **D3 Challenge survivability** | vol-matched P(pass) + daily-breach | **A** | P(pass) 99.91%@1%, 0% daily-breach all sizes, worst day −2.02%@1%; structurally incapable of single-day −5%. |
| **D4 Stress / left tail** | 1.5x adversarial, binding gate | **B+** | clean_4 stress@1% 82.24%, reactive overlay → 87.48% (fwd +2.0). Honest ceiling: 1.5x@1.5% ~72–78%; crypto-clustered tail is real, not bulletproof. |
| **D5 Deployability** | default-off, fail-closed, tested, parity | **A** | pure library, zero broker authority, 69 tests, byte-parity vs locked artifacts, import-safe (zero heavy deps). |
| **D6 Go-live readiness** | actual path to live | **C** | strategy + sizing ready; **2 blockers**: (1) disable broad incumbent selector+scheduler, (2) runtime/broker-authority proof. D6 is gated by infra, not edge. |

---

## 9. GO-LIVE READINESS — ready vs the 2 blockers

**READY:** the deploy book (`clean_4`, 12 sleeves, parity-locked), confidence weights, vol-matched
allocation profiles, fail-closed governors (soft daily-stop −3%, max-DD de-risk 7–10%, gross-risk cap
4%, outer circuit-breaker), confluence overlays, reactive stress de-risk, leak-free labeler, 69 tests.

**BLOCKER 1 — DISABLE the broad incumbent selector + scheduler.** The native V4 selector loses live
(−0.25R/fill, −113.4R over 454 fills, negative every month). Go-live is a NARROW REPLACEMENT: run
ONLY the `clean_4` rules through the new sizing surface; restrict the live universe to the deploy
symbol set; remove the stale 24/46-symbol broad surface from config.

**BLOCKER 2 — RUNTIME / BROKER AUTHORITY** (per CLAUDE.md first unresolved proofs): hard-halt
row-level forensic join, V3-vs-live authority-gap audit, dual-broker architecture audit,
production-return dossier. This is the real gate, not strategy. The deploy surface has zero broker
authority by design.

---

## 10. HONEST CAVEATS

1. Forward window is short (2025 + partial 2026); vp + session_leadlag_genuine + fx breadth are
   forward-only. Distrust single-fwd-year positives; graduate when a 3rd forward year exists.
2. The reactive overlay's combined 87.48%@1% is the builder's documented Section-3 result; the cached
   `KB6_COMBINE_RESULT.json` carries the individual ladder (83.87) and coloss (84.78) legs + the
   regime stacks reproducibly. The full-stack 91.86% leans partly on the forward-flat regime piece.
3. The 1.5x adversarial stress is the honest ceiling — challenge-robust, not stress-bulletproof.
4. Zero broker authority by design; live behavior depends on Blocker 2.

---

### Artifacts
- Snapshot of record: `INTEG_W6_FINAL_SNAPSHOT.json` ← `INTEG_W6_FINAL_SNAPSHOT.py` (parity-gated)
- Deployable module: `ultimate_book_live_package.py` v3 (+ `test_ultimate_book_live_package.py`, 69 tests)
- Dossier: `ULTIMATE_GO_LIVE_DOSSIER.md`
- W6 evidence: `KB6_SESSION_STACKS_RESULT.json`, `KB6_COMBINE_RESULT.json` + `KB6_stress_hardening.md`,
  `KB6_OVERLAY_PASSRATE_RESULT.json` + `KB6_confluence_state_d.md`, `KB6_ROUTER_RESULT.json`,
  `KB6_DEEP_STACKS_RESULT.json` + `KB6_confluence_frontier_2.md`
- Base book: `INTEG_W5_CLEAN3_DEPLOY.json`, `PORTFOLIO_BUILD_W5.md`, `KB6_wire_final_book.md`
