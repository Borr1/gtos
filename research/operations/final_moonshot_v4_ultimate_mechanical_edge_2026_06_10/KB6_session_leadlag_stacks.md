# KB6 — Promote session-open lead-lag + session/DXY stacks as sleeves (track: session_leadlag_stacks)

Builder pass 2026-06-15. Task: take the Wave-5 validated session edges and promote them into
proper confidence-sized SLEEVES — materialize each as a leak-free per-day R stream, corr-check
vs the clean_3 deploy book, run the **vol-matched (risk-equivalent) ablation** on the LOCKED W2
MC engine, and judge each on the **1.5x left-tail STRESS pass-rate** (the binding constraint),
never per-trade EV alone. Additive only if it RAISES Sharpe AND does NOT concentrate the stress
tail AND is not a double-count of an existing sleeve. Fold the confirmed additives.

Engine: `KB6_session_stacks.py` (importable). Result map: `KB6_SESSION_STACKS_RESULT.json`.
Reuses `INTEG_portfolio_build_w2.mc_series/joint_pass_mc` (LOCKED), the clean_3 book streams
(`INTEG_W3_streams_cache.pkl` + `INTEG_W5_new_streams_cache.pkl` @ clean_3 conf), the leak-free
`KB5_leadlag_subh4.mine_pair` (M15 leader z-impulse, same-close entry, `geometry_lib.simulate`
labeler, real `w1.cost_for`) and the `confluence.probe_fvg` + KB5 `sess_active` condition.

clean_3 book baseline (the comparator): 1679 days, Sharpe **0.1522**, daily std 0.0570,
1.5x-stress pass-rate **79.73% @1% / 70.03% @1.5%**.

---

## 0. HEADLINE — ONE of three made it, and the data forced a sleeve REDESIGN

| candidate | as proposed | verdict | why |
|---|---|---|---|
| (1) sub-H4 session-open lead-lag | broad sleeve (FX core + index/cross) | **DILUTIVE → REDESIGNED** | the JPY-cross legs (27-31% win at fixed R) inject a fat 1.5x tail; the **genuine-lead subset is ADDITIVE** |
| (2) metals session-active stack (+0.99R) | standalone sleeve conf 0.50 | **OVERLAY ONLY (double-count)** | corr **+0.65** vs metals_core — it is the SAME metals-FVG population, not a new sleeve |
| (3) DXY→FX directional filter | sleeve / filter | **FILTER, not a sleeve** (too thin to deploy alone) | confirms KB5: only neutralizes a negative base; n=12 fwd on dollar-clean legs |

**DEPLOYABLE ADDITIVE (the deliverable): `session_leadlag_genuine` @ conf 0.15** — the genuine
cross-asset LEAD subset of the sub-H4 session-open family. The vol-matched ablation:
**Sharpe 0.1522 → 0.1586 (+0.0064), 1.5x-stress 79.73% → 82.24% @1% (+2.51pts), 70.03% →
72.06% @1.5% (+2.03pts)** — it raises BOTH the Sharpe AND the stress tail. corr vs book +0.053.
~195 tr/yr forward. It is the rare additive that *improves the binding constraint*, not just EV.

---

## 1. Sleeve (1) — sub-H4 session-open lead-lag: the broad sleeve is dilutive, the genuine-lead subset is additive

### 1a. The broad sleeve (as the track named it) is DILUTIVE at fixed R
Materialized the full KB5 session-leadlag family: deep-train FX core (USDJPY→EURJPY london_open
gold leg trN301/fwd+0.76 z4.85; USDJPY→GBPJPY ny_session; EURJPY→GBPJPY london_open) + the
forward-only index/cross legs, ETH held out (crypto double-count, corr to crypto −0.01 either way).

- broad `session_leadlag` conf 0.20: FWD +0.351R n869 (31% win), but vol-matched ablation
  **stress@1% 79.73% → 57.16% (−22.6pts)**, Sharpe 0.1522 → 0.1369. **DILUTIVE.**
- `session_leadlag_fxcore` (deep-train FX only) conf 0.20: even worse, **−24.3pts** stress@1%.
- Even shrinking to conf 0.05 still costs −2.5pts stress@1% for −0.0019 Sharpe.

This **confirms the PORTFOLIO_BUILD_W5 exclusion** (Section 6): the JPY-cross legs at 27-31% win
on a fixed-R barrier are deep-tail dilutive — low corr + +EV is necessary but NOT sufficient.

### 1b. The GENUINE-LEAD subset is the additive sleeve (REDESIGN)
The drag is the deep-train JPY-cross legs (low per-trade Sharpe). Restricting to the **genuine
cross-asset LEADS** — the KB5 Section-C legs where the leader carries the edge (leader-adds-dR
+0.26..+0.77, follower's own move flat/negative) and BOTH forward years are positive:

| leg | session | FWD R (n) | win | 2025 / 2026 | KB5 null-z |
|---|---|---|---|---|---|
| US30→GER40 | ny_open (TRAIL) | +0.300 (101) | 45% | +0.14 / +0.41 | +4.66 |
| USDJPY→AUDJPY | london_ny | +0.552 (126) | 33% | +0.73 / +0.30 | +4.57 |
| US30→USDJPY | ny_open | +0.525 (61) | 33% | +0.25 / +0.68 | +3.92 |
| US30→AUDJPY | ny_open (rev) | +0.465 (102) | 32% | +0.51 / +0.43 | +3.09 |
| **COMBINED** | — | **+0.460 (390)** | **36%** | **+0.48 / +0.44** | all cleared |

- **Vol-matched ablation (the verdict): Sharpe +0.0064, stress@1% +2.51pts, stress@1.5%
  +2.03pts — ADDITIVE on BOTH axes.** corr vs clean_3 book **+0.053** (union-0) / +0.036
  (intersect). ~195 tr/yr forward. Conf **0.15** (forward-only M15 since 2025 → single forward
  regime → smaller size; the H4 relationship is KB4-train-validated, the sub-H4 timing is
  null-cleared but young).
- Why this slice survives where the broad sleeve fails: higher per-trade quality (the index/
  AUDJPY session-open spillover is a cleaner directional edge than the JPY-cross continuation),
  all-legs-both-years-positive, and it is orthogonal index/cross session-open breadth that
  *deepens* diversification rather than re-betting the book's existing exposure.

**HONEST CAVEAT (D2):** forward-only (no deep M15 TRAIN for index/cross — they start 2025-06).
Two forward years, both positive, null-cleared, leader-adds-dR>0. Needs a third forward year to
graduate to deep-deploy grade. Sized small (0.15) for exactly this reason.

---

## 2. Sleeve (2) — metals session-active stack: real cell, but a DOUBLE-COUNT (overlay, not a sleeve)

Reproduced the KB5 headline cell EXACTLY: FVG probe over metals gated by
`persistence ∧ vol_expand ∧ sess_active` → **TRAIN +0.481R (n55), FWD +0.992R (n39), 67% win,
both fwd years positive (2025 +1.40 n20, 2026 +0.56 n19), perm-p 0.0003**. The edge is real.

**But it is NOT a new sleeve — it is the SAME population the book already trades:**
- corr **+0.65** (union-0) / **+0.76** (intersect) vs `metals_core`; +0.27 vs the whole clean_3 book.
- **63 of 70 entries (90%) share the exact (symbol, date) with the existing metals book**
  (metals_core/softband/ob_micro). 49 of its 53 active days overlap metals_core days.
- The vol-matched ablation reads "ADDITIVE" (Sharpe +0.0014, stress@1% +1.6pts) — but that lift
  comes from RE-WEIGHTING metals days the book already holds (folding it as a separate column
  double-counts the same trades and inflates metals concentration). **Rejected as a sleeve under
  the double-count discipline (|corr vs a single book sleeve| ≥ 0.30).**

**Deployable form = SIZE-UP SELECTOR OVERLAY on metals_core**, not a sleeve. When
`persist ∧ vol_expand ∧ sess_active` all fire on a metals FVG signal, size that metals trade up:
metals_core entries WITH the flag = **ALL +0.948R (n104) vs WITHOUT +0.654R (n27), +0.293R lift**;
TRAIN side +0.872 (flag) vs −0.008 (no-flag) — a genuine quality discriminator. Forward the
already-elite metals_core base is so strong that the flagged subset (+1.07R n40) doesn't beat the
tiny unflagged forward pocket (+1.98R n9), so the overlay is a TRAIN-validated conviction tag with
a positive (not outperforming) forward level. **Wire it as a confidence multiplier inside the
metals_core sleeve, identical to how the cross-layer leader-VETO is wired onto sub_xvol_pullback —
not as a separate risk-banked column.**

---

## 3. Sleeve (3) — DXY→FX directional filter: a FILTER, not a sleeve (confirms KB5)

The KB5 condition `dxy_bias` (synthetic DXY proxy, return-corr +0.993 to real DXY, leak-free) is a
directional FILTER. Tested two ways:

- **As a standalone FX base** (fvg/sweep over fx+jpy_fx, dxy-agree only): forward +0.005R (sweep)
  / −0.10R (fvg) — it only NEUTRALIZES a losing base, never makes it a winner. Cannot be a
  positive-EV sleeve. Exactly the KB5 verdict.
- **As an OVERLAY on the dollar-clean leadlag legs** (USDJPY-follower legs; JPY-crosses have no
  clean dollar sign so the filter is undefined): dxy-AGREE FWD +0.969R (n12) vs DISAGREE +0.314R
  (n42) → **+0.655R forward filter lift**. The SIGN is right (agree > disagree), confirming the
  dollar lead is real, **but n=12 forward (2025 −0.40 n7 / 2026 +2.89 n5) is far too thin and has
  no train data** — not deployable as a sleeve or a hard gate.

**Verdict:** keep `dxy_bias` as a documented confidence-multiplier (a tie-up nudge) on dollar-clean
FX entries, never a standalone sleeve and never a hard filter at this sample depth. Revisit when a
third forward year of M15 index/cross data exists.

---

## 4. What to fold (the deliverable)

1. **FOLD `session_leadlag_genuine` @ conf 0.15** — the genuine cross-asset session-open LEAD
   sleeve (US30→GER40/USDJPY/AUDJPY ny_open, USDJPY→AUDJPY london_ny). Vol-matched ADDITIVE on
   both axes (Sharpe +0.0064; **1.5x-stress +2.51pts @1% / +2.03pts @1.5%**), corr +0.053,
   ~195 tr/yr forward, both fwd years +. This is the new clean_3 → **clean_4** additive.
2. **WIRE `metals_sess_stack` as a SIZE-UP OVERLAY on metals_core** (not a sleeve) — flag =
   `persist ∧ vol_expand ∧ sess_active`, +0.29R conviction lift, perm-p 0.0003. Same overlay
   pattern as the cross-layer leader-VETO on sub_xvol_pullback.
3. **KEEP `dxy_bias` as an FX confidence-multiplier** (not a sleeve, not a hard gate) — sign
   confirmed, sample too thin to size.
4. **DROP** the broad `session_leadlag` (incl. JPY-cross legs) and `session_leadlag_fxcore` from
   the risk-banked book — deep-tail dilutive at fixed R (−22..−24pts stress@1%). Retained as
   documented breadth-only overlays per "delete nothing."

The data again refused "add everything": of three proposed promotions, exactly one folds as a
sleeve, one becomes an overlay (double-count), one stays a filter (too thin) — and the one that
folds had to be REDESIGNED (trim the dilutive JPY-cross legs) to pass the binding stress constraint.

---

## 5. Honest scorecard

| dim | grade | assessment |
|---|---|---|
| D1 Edge reality | B+ | genuine-lead legs all null-cleared (z 3.09-4.66) + leader-adds-dR>0.25 + both-fwd-years+; metals cell perm-p 0.0003. |
| D2 Forward holdout | B- | the additive sleeve is **forward-only** (M15 index/cross 2025+), single forward regime (2 yrs). H4 relationship is KB4-train-validated; sized small (0.15) for this. |
| D3 Independence | A | corr +0.053 vs book; double-count radar CAUGHT metals_sess_stack (+0.65 vs metals_core → overlay) and ETH (held out). |
| D4 Tail/stress | A- | the fold IMPROVES the binding 1.5x-stress tail (+2.5pts @1%) — the rare additive that helps, not just survives, the stress constraint. |
| D5 Additivity discipline | A | refused the broad sleeve (dilutive), refused metals as a sleeve (double-count), refused DXY as a sleeve (too thin); vol-matched stress drove every cut; redesigned the survivor to a clean subset. |
| D6 Deployability | B+ | concrete: one new sleeve @0.15 + one selector overlay + one confidence-multiplier, all on the locked engine. Next: re-run the full clean_4 deploy MC + 2-account allocation with this sleeve added, and re-test the genuine legs under the deployed STATE_D scale-out exit (fixed-R here understates a 36%-win continuation sleeve). |

## Files
- `KB6_session_stacks.py` — materializers (`gen_session_leadlag_genuine`, `gen_metals_sess_stack`,
  `gen_session_leadlag_dxy_filtered`), corr-check, vol-matched ablation, double-count gate, fold.
- `KB6_SESSION_STACKS_RESULT.json` — full per-sleeve stats, corr, DXY filter split, metals overlap,
  ablation verdicts, folded-additive MC.
