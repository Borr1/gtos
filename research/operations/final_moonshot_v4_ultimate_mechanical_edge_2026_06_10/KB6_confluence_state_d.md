# KB6 — Cross-Layer Confluence RE-MINED under the deployed STATE_D exit

**Track:** Re-mine the KB5 cross-layer confluence winners (leader-impulse VETO, session/regime
stack, VP-acceptance) under the DEPLOYED `cs.exit_state_d` scale-out exit instead of fixed-3R,
materialize the survivors as leak-free per-day R streams, and corr-check vs the clean_3 deploy book.

**Verdict (one line):** The cross-layer winners *do* survive the real STATE_D exit (positive,
perm-significant, 2/2 forward years), but they are **high-corr SUBSETS of already-deployed fold
sleeves, not independent streams** — so the honest test is intra-sleeve size-up, and on the binding
constraint (vol-matched 1.5x stress MC) only **VP-acceptance is a net book improvement
(stress@1.5% 69.6% -> 74.8%)**; the leader-veto is a per-trade EV winner that is **book-pass-rate
negative** because its frequency cut shrinks diversification faster than its EV helps.

---

## 1. Method (leak-free, exit-honest)

- `KB6_confluence_state_d_miner.py` re-walks `substrate.build_states` (features index<=i) for the
  same 5 base cells as KB5, and labels **every** matched signal with BOTH:
  - `R3` = fixed-3R (`sub.outcome` -> `geometry_lib.simulate_detail`, the KB5 scoring basis), and
  - `Rd` = the deployed STATE_D scale-out (`compounding_sleeve.exit_state_d(B,i,d,sd,vr,cost)`).
- R-unit consistency: substrate `stop_atr=1.0` so `sd = 1.0*atr`; STATE_D uses the SAME `sd=atr`
  as its 1R unit and raw `w1.cost_for` (substrate's cost is scaled by 1/stop_atr = raw here).
  Both labels are in the same R-unit (1R = 1 ATR) and same cost basis; only the exit differs.
- Orthogonal tags (VP node-location, regime, leader z-impulse, liquidity sweep) are the EXACT
  leak-free extractors from `KB5_cross_layer_miner` (prior-day VP, train-fit regime, same-close
  leader z). FORWARD HOLDOUT (TRAIN<=2024 / FWD 2025-26) + per-YEAR + n-gate + phi + 2000-perm null.

Artifacts: `KB6_CONFLUENCE_STATE_D_RESULT.json` (full per-condition both-label table),
`KB6_CONFLUENCE_STATE_D_RAW.json` (labelled signals), `KB6_OVERLAY_CORRCHECK_RESULT.json`
(materialized overlay corr vs clean_3 book), `KB6_OVERLAY_PASSRATE_RESULT.json` (binding-constraint MC).

## 2. The exit shrinks the right tail — base cells lose ~half their mean R

The scale-out books 50% at scaleR and runs the rest to a BE-stopped deep target. It caps the right
tail that fixed-3R was paying, so EVERY base cell's mean R falls (but win-rate rises sharply):

| base cell | fixed-3R fwd EV | STATE_D fwd EV | STATE_D win% |
|---|---|---|---|
| xvol_up_pullback_L3R | +0.712 | **+0.286** | (base) |
| xvol_up_conflict_L3R | +0.203 | **+0.037** | |
| xvol_up_conflict_mid_L3R | +0.193 | **+0.034** | |
| mid_dn_revert_ny_L3R | +0.469 | **+0.277** | |

This is why a confluence overlay must be **re-verified** under STATE_D: the broad bases are barely
positive under the real exit; the edge now lives almost entirely in the high-odds sub-cells.

## 3. The cross-layer winners SURVIVE STATE_D (lift halves but stays positive + significant)

Forward (2025-26), STATE_D-labelled, vs the STATE_D base of the same cell:

| overlay | base fwd EV | cond fwd EV (n) | win% | fwd lift | perm-p | fwd yrs |
|---|---|---|---|---|---|---|
| xvol_pullback x **leader-veto** (ll_align=none) | +0.286 | **+0.809** (40) | 87.5% | +0.523 | 0.000 | 2025:+0.72 / 2026:+0.97 |
| xvol_conflict x leader-veto | +0.037 | +0.433 (63) | 69.8% | +0.396 | 0.0005 | 2025:+0.27 / 2026:+0.68 |
| xvol_conflict_mid x leader-veto | +0.034 | +0.458 (62) | 71.0% | +0.424 | 0.000 | 2025:+0.31 / 2026:+0.68 |
| mid_dn_revert x **VP-acceptance** (vp_loc=above_va) | +0.277 | **+0.566** (49) | 57.1% | +0.289 | 0.0465 | 2025:+0.56 / 2026:+0.59 |
| xvol_conflict x VP-acceptance | +0.037 | +0.279 (41) | 63.4% | +0.242 | 0.0495 | 2025:+0.46 / 2026:+0.20 |
| xvol_conflict x vp_poc_side=above_poc | +0.037 | +0.255 (42) | 64.3% | +0.218 | 0.059 | 2025:+0.49 / 2026:+0.16 |

Reading: the **leader-veto** is the cleanest survivor (perm-p ~0, lift +0.40-0.52R, both fwd years
strongly positive). VP-acceptance survives but its perm-p drifts to the ~0.05 edge under STATE_D
(the exit absorbs some of the VP edge), and the xvol-conflict x VP cells go marginal (perm-p ~0.06).

## 4. Corr-check: the survivors are SUBSETS of deployed sleeves, NOT independent streams

Materialized each survivor as a STATE_D per-day R stream and corr-checked vs the clean_3 deploy
book (8 base sleeves + sub_xvol_pullback + vp_euidx_pocgrav + sub_mid_dn_revert):

| overlay | corr vs COMBINED book (u0 / intersect) | corr vs PARENT sleeve (u0 / intersect) |
|---|---|---|
| veto_xvol_pullback | +0.104 / +0.42 | sub_xvol_pullback **+0.41 / +0.70** |
| veto_xvol_conflict | +0.036 / +0.07 | sub_xvol_pullback **+0.30 / +0.68** |
| veto_xvol_conflict_mid | +0.043 / +0.15 | sub_xvol_pullback **+0.25 / +0.70** |
| vpacc_mid_dn_revert | +0.101 / +0.34 | sub_mid_dn_revert **+0.37 / -** |

The combined-book corr is low (good), but the **parent-sleeve intersect corr is 0.68-0.70** for the
leader-veto and 0.37 for VP-acceptance. These overlays trade the same days as deployed sleeves —
they are **size-up SELECTORS inside an existing sleeve, not new diversifiers.** Folding them as new
additive columns would double-count. The correct test is intra-sleeve replacement / re-weight.

## 5. BINDING CONSTRAINT — vol-matched challenge-pass + 1.5x left-tail stress (LOCKED W2 MC)

`KB6_overlay_passrate_test.py`, all books on the same day grid, vol-matched to the exit-honest
`deploy_sd` daily std, 1.5x left-tail stress, `W2.mc_series` (8% tgt / 5% daily / 10% maxDD):

| book | sharpe | stress@1.0%vm | **stress@1.5%vm** | P@1%fwd |
|---|---|---|---|---|
| deploy_3R (as shipped, fixed-3R scoring) | 0.1558 | 81.0% | 72.1% | 99.97% |
| deploy_sd (exit-honest: sub_* re-labelled STATE_D) | 0.1480 | 79.4% | **69.6%** | 99.94% |
| veto_replace (swap sub_xvol_pullback -> leader-veto subset) | 0.1460 | 77.8% | **67.9%** (worse) | 99.92% |
| **vpacc_replace** (swap sub_mid_dn_revert -> VP-acc subset) | 0.1510 | 84.3% | **74.8% (best)** | 99.92% |
| both_replace | 0.1489 | 83.7% | 74.0% | 99.94% |
| veto_overlay (+0.20 size-up tilt) | 0.1495 | 79.6% | 70.3% | 99.97% |

Two exit-honesty facts and one decision:

1. **Exit honesty costs ~2.5 pts of stress headroom.** The shipped book was scored at fixed-3R; its
   real STATE_D exit earns less right-tail, so stress@1.5% is 69.6% not 72.1%. (Both >> the
   deployed clean_3 stress15 floor of ~73% in the dossier; the difference is scoring basis, and
   the deploy book's own `mc_book_stress` 1.5% is 72.9% — consistent.)
2. **Leader-veto is per-trade EV-positive but BOOK pass-rate NEGATIVE.** It lifts the xvol sleeve's
   STATE_D fwd EV +0.77R -> +1.17R/trade, but retention is 61% (33/yr -> 21/yr). The lost trades
   shrink the sleeve's diversification contribution faster than the EV gain helps, so vol-matched
   stress@1.5% falls 69.6% -> 67.9%. This is exactly the trap the doctrine names: never per-trade
   EV alone. **Do not size up the book via the leader-veto.**
3. **VP-acceptance is the real size-up winner.** Swapping the sprawling low-EV `sub_mid_dn_revert`
   (84/yr @ +0.28R) for its VP-acceptance subset (33/yr @ +0.57R, flat 2/2 fwd years) lifts
   vol-matched stress@1.5% to **74.8% (+5.2 pts over exit-honest, +2.7 over even the as-shipped 3R
   book)** and Sharpe 0.148 -> 0.151. It cuts the noise, not the signal.

## 6. STATE_D-honest overlay numbers (the deliverable)

| overlay | STATE_D fwd EV/trade | fwd win% | ~trades/yr | retention | parent corr (intersect) | verdict |
|---|---|---|---|---|---|---|
| leader-veto (xvol_up_pullback) | **+1.17R** | 87.5% | ~21 | 61% | 0.70 | per-trade winner, **book stress-NEGATIVE** — keep as intel, do not size up |
| leader-veto (xvol_conflict / mid) | +0.43-0.46R | 70-71% | ~42 | ~46% | 0.68-0.70 | survives, low combined-corr, but same book-frequency drag |
| **VP-acceptance (mid_dn_revert)** | **+0.57R** | 57.1% | ~33 | 16% | 0.37 | **SIZE-UP WINNER: book stress@1.5% 69.6% -> 74.8%, Sharpe +0.003** |
| VP-acceptance / poc (xvol_conflict) | +0.26-0.28R | 63-64% | ~28 | ~27% | (subset of xvol) | marginal (perm-p ~0.05-0.06); hold |

## 7. Recommendation

- **Adopt VP-acceptance as the `sub_mid_dn_revert` sleeve definition** (`vp_loc=above_va` selector,
  STATE_D exit). It is the only overlay that improves the binding constraint at risk-equivalence:
  vol-matched 1.5x stress pass-rate 69.6% -> **74.8%**, Sharpe 0.148 -> 0.151, with flat forward
  years (2025 +0.56R, 2026 +0.59R) and low parent corr (0.37). This is a clean noise-cut size-up.
- **Do NOT promote the leader-veto into the deployed book.** It is a genuine per-trade alpha
  (+1.17R/trade, 87.5% win) and should be retained as live-monitoring intelligence / a confidence
  tag, but as a book change it is stress-pass-rate negative because the frequency cut dominates.
  It is a SELECTOR inside `sub_xvol_pullback`, corr 0.70 with its parent — not a new diversifier.
- **Exit-honesty note for the dossier:** the shipped clean_3 book scored its substrate sleeves at
  fixed-3R; the runtime exit is STATE_D, which is ~2.5 pts lower on stress@1.5% headroom. The book
  still passes comfortably, but the dossier number should cite the STATE_D-honest 69.6% (or the
  VP-acceptance-upgraded 74.8%), not the fixed-3R 72.1%.

**Independence / high-odds confluence honesty:** the leader-veto and VP-acceptance both clear
perm-null and 2/2 forward years, but they are NOT independent of the deployed book (parent corr
0.37-0.70) — they are within-sleeve refinements. The high-odds claim holds at the trade level; the
diversification (book) claim does not. Sized by the binding constraint, only VP-acceptance earns
a book change.
