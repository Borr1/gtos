# KB7 — Reinstate dropped sleeves under GROWTH sizing (track: reinstate-sleeves, UNLEASH wave)

Builder pass 2026-06-15. **Objective shift held:** optimize for max growth-rate / speed-to-target
subject to FTMO (5% daily, 10% maxDD), not minimal size. Re-test the sleeves that were dropped at
W5/W6 for 1.5x-stress-tail reasons (`leadlag_core` full 8-config, `subh4_ll_fx`, and the never-MC'd
IDB intraday breadth) UNDER growth-optimal sizing + confidence-weighting + the un-capped labels +
the real deployed STATE_D exit. Test the highest-Sharpe leadlag subset only (US30→USDJPY, NAS↔SPX).
Reinstate the ones that genuinely ADD net speed/EV to the book (vol-matched challenge-pass + maxDD-fail).

Engine: `KB7_reinstate_sleeves.py` (parity-verified clones of `ll.mine_pair` / `SH.mine_pair` /
`IDB.fvg_retest` with the EXIT swapped to `cs.exit_state_d` and selectable winsor; folds each into the
locked `clean_3` day grid and runs the LOCKED W2 MC). Results: `KB7_REINSTATE_RESULT.json`,
`KB7_FINAL_FOLD_RESULT.json`.

## Method + parity (faithful re-label, leak-free)
- Re-labelers replicate the shipped gating EXACTLY (leader z-impulse z'd vs trailing window ending
  i−1; stop = 0.5·ATR; same session/regime/confirm gates), only the EXIT and winsor change.
- **Parity proof (fixed-R + winsor[-1.3,+5] reproduces the shipped streams):** `subh4_ll_fx` n=357
  FWD +0.760 (n56) byte-identical to `INTEG_W5_new_streams_cache.pkl`; `leadlag_full` FWD +0.1607
  (n833) identical (TRAIN n differs by 15 because STATE_D needs i≥100 for the vol-ratio vs i≥14 —
  harmless, drops only 2014 early bars); IDB crypto/metals reproduce the 333/660-row ledger exactly.
- Winsor variants tested: shipped `[-1.3,+5]` vs relaxed `[-1.3,+12]` (un-capped right tail).
- Verdict gate = the LOCKED, vol-matched challenge-pass MC + 1.5x left-tail STRESS + maxDD/ruin,
  vs the `clean_3` baseline at GROWTH sizes (0.75→2.0%). Per-year, never blended-only.

## A. HEADLINE — none of the dropped sleeves genuinely comes back; the drop was correct even under aggression

| candidate (FWD EV by exit) | fixed-R (native) | **STATE_D** | winsor [+5]→[+12] | folded-Sharpe vs base 0.1522 | folded stress@1% vs base 79.7% | verdict |
|---|---|---|---|---|---|---|
| `leadlag_full` (8-config) | +0.161 (n833) | **+0.019** | no change | 0.1474@0.10 / 0.1460@0.15 | 74.6% / 70.4% | **STAYS OUT** |
| `leadlag_hisharpe` (US30→JPY, NAS↔SPX) | +0.152 (n371) | **+0.031** | no change | 0.1463@0.15 → 0.1303@0.35 | 70.6% → 52.6% | **STAYS OUT** |
| `subh4_ll_fx` (USDJPY→EURJPY london) | +0.760 (n56) | **+0.332** | no change | 0.1455@0.15 / 0.1418@0.25 | 73.8% / 68.9% | **STAYS OUT** |
| `idb_crypto_fvg` H1 | +0.148 (n333) | +0.077 | no change | 0.1485@0.20 / 0.1465@0.30 | 77.4% / 75.8% | OUT (corr +0.098 crypto overlap) |
| **`idb_metals_fvg` H1** | **+0.057→+0.113 FWD** | +0.041 | no change | **0.1525@0.20 / 0.1521@0.30** | **78.8% / 78.4%** | **NEUTRAL micro-add (see C)** |

Two facts dominate, both robust to growth sizing:

1. **The STATE_D exit ACTIVELY BACKFIRES on every dropped sleeve** — it is the opposite of a lever.
   STATE_D on US30→USDJPY: 58% full_stop, **22% scratch_be (runner round-trips to breakeven), 20%
   win_runner → mean −0.026R** vs the fixed-2R target's +0.16R. The vol-tiered BE-runner is built for
   SLOW continuations (metals/crypto, structural stops, the move keeps going); a FAST cross-asset
   impulse on a TIGHT 0.5·ATR stop pops then mean-reverts, so the BE-stop scratches out exactly the
   right tail that a clean fixed 1.5–2R target banks. Win% rises 28%→43% while EV collapses — the
   classic "more frequent small wins, forfeited runners" signature. **The un-capped winsor [+12] makes
   ZERO difference** for all five (none reaches even +5 under either exit) → the right-tail cap was a
   non-binding "stale drag" here, not a real one.

2. **The fixed-R (native) fold at growth sizing CONFIRMS the W5/W6 drop, it does not overturn it.**
   `leadlag` and `subh4` lower BOTH Sharpe AND the 1.5x stress tail at every confidence weight — the
   high-Sharpe subset is no exception (it only delays the tail erosion, never reverses it). At its
   highest tested weight (0.35) the hi-Sharpe subset drives stress@1% from 79.7% to 52.6%.

## B. The highest-Sharpe leadlag subset (US30→USDJPY, NAS↔SPX) — specifically tested, specifically OUT
Per the brief, the index-spillover + Dow→yen subset (deepest n, null-clearing in KB4) was isolated as
its own sleeve `leadlag_hisharpe` (n=1387, TRAIN +0.154 / FWD +0.152, 27% win). It IS a higher
per-trade-Sharpe sub-book than the full 8-config — but at the BOOK level it is still tail-dilutive:
folded at 0.15 it gives Sharpe 0.1463 (< 0.1522) and stress@1% 70.6% (< 79.7%). The reason is
structural, not tuning: 27% win at fixed-R injects a fat left tail of clustered −1R losses on
correlated index/JPY days that the block-bootstrap MC (which preserves cross-sectional covariance)
penalizes. Trimming to the best 3 legs raises per-trade quality but cannot fix the fixed-R left-tail
shape. **It does not come back.** (W6 already folded the genuinely orthogonal slice — the M15
session-open `session_leadlag_genuine` cross-asset LEADs — as `clean_4`; that one passed because it is
session-open-gated and ~lag-free, a different population from this H4 spillover subset.)

## C. The one honest micro-add: `idb_metals_fvg` at native fixed-2R — but it is a WASH, not a growth lever
`idb_metals_fvg` (H1 vol-gated FVG-retest continuation, acNone, fixed 2R — the metals-validated
continuation entry run faster) is the only candidate that does not degrade the book:
- per-year honest: 2025H2 (TRAIN) +0.024 (n415) / 2026H1 (FWD) +0.113 (n245); 5/6 carriers positive
  (XAGUSD anchors +0.211, XAUUSD lone −0.127 — sleeve is the validation unit, n thin per carrier).
- corr vs `clean_3` = **−0.005** (true diversification), +330 tr/yr forward.
- folded @0.30, VOL-MATCHED (the fair test): Sharpe **0.1521 vs 0.1522** (flat), stress@1% **78.4% vs
  79.7%** (−1.3pt), median days-to-pass **85 → 85** (no speed gain), maxDD-fail 0.255% vs 0.215%
  (marginally worse). 0% daily-breach at every size.

**Verdict: NEUTRAL.** It banks orthogonal frequency but ZERO measurable speed/pass-rate improvement
and a small tail cost — it is not the growth lever the UNLEASH wave is hunting. Defensible ONLY as a
tiny breadth add (≤0.20, conf-haircut for forward-window-only data) IF the owner wants more
quality-gated decision instants for the compounding loop; it must NOT be sized as a speed accelerant.
`idb_crypto` is strictly worse (Sharpe 0.1485, corr +0.098 crypto overlap) → keep out.

## D. GROWTH-RATE / RUIN GUARDRAIL (quantified, the real binding constraint)
The growth objective is served by SIZE on the EXISTING `clean_3`, not by these sleeves. On `clean_3`
itself (vol-matched), the size→speed→risk curve:

| size | P(pass) | 1.5x-stress P(pass) | **P(maxDD breach)** | daily-breach | median days-to-pass | FWD P(pass) / days |
|---|---|---|---|---|---|---|
| 0.75% | 99.98% | 86.4% | 0.03% | 0% | 113 | 100.0% / 37 |
| 1.00% | 99.78% | 79.7% | 0.21% | 0% | 85 | 99.94% / 28 |
| 1.25% | 99.31% | 74.0% | 0.69% | 0% | 68 | 99.80% / 22 |
| 1.50% | 98.30% | 70.0% | 1.70% | 0% | 57 | 99.32% / 19 |
| 2.00% | 94.94% | 63.7% | **5.07%** | 0% | 43 | 97.45% / 14 |

Honest reading for the aggression mandate: **1.0–1.25% is the growth-optimal band** — P(maxDD breach)
stays ≤0.7%, daily-breach mechanically 0%, and median days-to-pass nearly HALVES (113→68) vs the
shipped conservative 0.75%. 1.5% is still defensible (P(breach) 1.7%, days 57). 2.0% is where the
guardrail bites (P(breach) 5.1% per attempt — unacceptable for a near-certain-pass posture). The
dropped sleeves add nothing to this curve; the speed comes from sizing the diversified book hotter,
which the locked MC already shows is FTMO-safe through ~1.5%.

## E. VERDICT (which come back, book impact)
1. **`leadlag_core` (full + highest-Sharpe subset): DO NOT reinstate.** Tail-dilutive at fixed-R even
   under growth sizing; STATE_D craters it (BE-runner scratches the right tail of fast impulses). The
   genuine orthogonal slice already shipped as `clean_4`'s `session_leadlag_genuine` (M15 session-open).
2. **`subh4_ll_fx`: DO NOT reinstate as a book sleeve.** +0.76R FWD but 38% win / n56 fixed-R is
   deep-tail dilutive at book scale; STATE_D halves its EV. Keep as the documented standalone
   small-size session edge (already its W5 disposition).
3. **`idb_crypto_fvg`: keep OUT** (crypto-sleeve overlap corr +0.098, Sharpe-dilutive).
4. **`idb_metals_fvg`: optional ≤0.20 breadth add at NATIVE fixed-2R** (NOT STATE_D) — Sharpe-neutral,
   corr −0.005, +330 orthogonal tr/yr, 0% daily-breach. It is a frequency/compounding-loop add, not a
   growth accelerant; the book impact is a wash on every verdict axis. Default recommendation: hold at
   conf 0.15 if folded; the deploy book stays `clean_4` otherwise.
5. **The actual growth lever is SIZE on `clean_3`/`clean_4` (1.0–1.25%), not these sleeves.** Quantified
   ruin guardrail above.

## KEY LEARNINGS (kept, nothing deleted)
- **STATE_D is exit-specific, not universal.** It is a SLOW-continuation exit (structural stop, runner
  keeps going). On FAST tight-stop signals (cross-asset impulse, intraday breakout) its BE-runner
  scratches the right tail and HALVES EV. Match the exit to the move's speed — the same R-space lesson
  as W2/KB3 (slow→scale/cap, fast→clean fixed target).
- **The "winsor [+5] caps winners" drag is NON-BINDING for these families** — none reaches +5 under any
  exit. Relaxing to [+12] changed nothing. (The drag is real only for the deep-runner metals/crypto
  CORE, not for these add-ons.)
- **Low corr + +EV is still necessary-not-sufficient under aggression.** Growth sizing did not rescue
  any sleeve the vol-matched 1.5x-stress ablation rejected at conservative sizing; the binding
  constraint is the cross-sectionally-clustered left tail, which size amplifies rather than diversifies.

## FILES
- `KB7_reinstate_sleeves.py` — parity-verified re-labelers (STATE_D + winsor variants) + fold MC harness.
- `KB7_REINSTATE_RESULT.json` — per-sleeve stats (fixed/STATE_D × winsor5/12) + corr + fold MC grids.
- `KB7_FINAL_FOLD_RESULT.json` — the recommended-fold growth-size grid (P(pass)/stress/maxDD/days/fwd).

---

## F. INDEPENDENT CONFIRMATION — iso-risk-of-ruin SPEED test (second pass, 2026-06-15 04:0x)

A second builder pass re-ran the question through a different lens — **iso-P(maxDD-fail) speed**
(for each book find the largest size holding P(maxDD-fail) ≤ a fixed budget, then compare median
days-to-target) — using clean_4 (clean_3 + `session_leadlag_genuine`) as the base and the cached
deep-H4 leadlag subsets. It reaches the **identical verdict** by an orthogonal route, confirming
the drop is correct under aggression and is not an artifact of the vol-matched stress lens.

Artifacts: `KB7_growth_mc.py`/`KB7_GROWTH_MC_RESULT.json`, `KB7_iso_risk.py`/`KB7_ISO_RISK_RESULT.json`,
`KB7_build_leadlag_subsets.py`/`KB7_leadlag_subsets.json`, `KB7_leadlag_stated.py`,
`KB7_final_check.py`/`KB7_FINAL_CHECK_RESULT.json`, `KB7_fwd_check.py`, `KB7_materialize_idb.py`.

**Per-leg H4 leadlag (deep, leak-free):** NAS100→SPX500 EV +0.173/Sh 0.093 (TRAIN +0.171, FWD +0.176);
SPX500→NAS100 +0.200/0.092 (TRAIN +0.233); the full 8-leg sleeve EV +0.116/**Sh 0.058**; best subset
`leadlag_top4` (NAS↔SPX + GER40→UK100 + SPX500→GER40) EV +0.155/**Sh 0.077** (TRAIN +0.156, FWD +0.152,
5/6 pos-yr). The task-named NAS↔SPX+US30→USDJPY subset = EV +0.149/Sh 0.072. **Every subset is below
book-Sharpe ~0.16** — that is the entire story.

**Iso-ruin speed (the decisive growth comparison), all-history MC @ P(maxDD-fail)≤2%:**

| book | max size | median days | meanR |
|---|---|---|---|
| clean4_base | 1.6% | **52** | 0.0963 |
| +leadlag_top4@0.30 | 1.2% | 62 | 0.1023 |
| +leadlag_top4@0.45 | 0.9% | 76 | 0.1060 |
| +subh4_ll_fx@0.30 | 1.2% | 69 | 0.0913 |
| +idb_crypto@0.30 | 1.5% | 55 | 0.0947 |

Same ordering at the 5% budget (base 39d → top4@0.45 56d) and the tight 0.5% budget (base 69d →
top4@0.30 82d). **Under 1.5x STRESS the leadlag books cannot hold even a 2% maxDD-fail budget at any
size in [0.3%,5%]** (the binding tail). FORWARD-only (2025-26, where leadlag EV is strongest) @ 2%
budget: base 14d @2.0% vs +leadlag_top4@0.45 17d @1.4%; `subh4_ll_fx@0.30` is the only candidate that
matches base speed (14d) — it is the most orthogonal (corr +0.017) and deep-train FX-validated, so it
is the strongest *intelligence* keep, but it is speed-NEUTRAL, not an accelerant.

**Mechanism (why growth sizing doesn't rescue them):** leadlag is a **fat-LEFT-tail lottery** — 27%
win, median trade −1.06R (the stop), winners run to max +3.94R. Adding it raises daily mean but adds
left-tail variance faster, and the FTMO maxDD cap binds on left-tail variance, so iso-ruin forces a
size cut larger than the mean gain → net slower. STATE_D / wider stop raise win% (36→45%) but NOT
EV/Sharpe (the entry edge is just thin). Winsor cap confirmed non-binding (max winner +3.94R). idb_metals
deep TRAIN reproduced **negative** (−0.038, acNone & ac0.10) — falsified, matching W6.

**Same conclusion, two lenses:** the growth lever is higher-Sharpe CORE EV (exit-oracle headroom,
metals low-vol +2.02R localization) and SIZE on clean_4 at 1.0–1.25%, not more sub-Sharpe breadth.
