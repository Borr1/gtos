# KB3 — Apply the D4 miner harvest to the book (Wave-3 upgrade)

Track: **D4 harvest integration.** Date 2026-06-15. Goal: take the forward-validated proposals
from `IMPROVEMENT_PROPOSALS.json` + `KB2_learning_miner.md`, RE-VALIDATE each (train+forward,
per-year) on the DEPLOYED cascade fill stream (apples-to-apples with what actually ships), keep
what holds at the **book level**, return the LEARNING for what doesn't, then re-run the portfolio
MC on the upgraded book.

Doctrine held: per-YEAR / per-SYMBOL (never averages-as-verdict); forward holdout (train<=2024 ->
2025/2026); winsorize R[-1.3,+5]; real `w1.cost_for` scaled by stop tightness; leak-free features
(index<=i); SIZE BY CONFIDENCE, delete nothing (falsified buckets demoted to small size, kept).

Builders: `INTEG_portfolio_build_w3.py` (upgraded integrator, re-uses the W2 true-corr +
diversification MC + 2-account engine), `KB3_revalidate_metals.py` (per-sleeve re-validation),
`KB3_ablation.py` (book-level which-item-helps decomposition).
Results: `INTEG_PORTFOLIO_W3_RESULT.json`, `KB3_REVALIDATE_METALS_RESULT.json`,
`KB3_ABLATION_RESULT.json`. The W2 baseline (`INTEG_PORTFOLIO_W2_RESULT.json`) is preserved intact.

---

## 1. The critical methodology: per-sleeve EV is NOT the book verdict

Every harvest item is individually train+forward-positive on per-trade EV (the miner proved that).
But the OWNER GOAL is the FTMO challenge-pass MC of the COMBINED book. The first naive full-harvest
integration RAISED per-sleeve EV yet **LOWERED** book P(pass) everywhere and CRATERED stress P(pass)
by ~14pp — because two items inject tail variance the diversified-day MC and the 1.5x left-tail
stress punish. The fix was an ABLATION (`KB3_ablation.py`): turn each item on alone, measure the
BOOK verdict, keep only what beats baseline at the book level. This is the doctrine working exactly
as intended — improve, don't ship a per-trade-EV win that loses the real objective.

Ablation @1.0% (combined MC, 8k paths; baseline = W2 book):

| item (alone over W2) | combined mean | fwd mean | worst day | P(pass) all | P(pass) fwd | **P STRESS 1.5x** | verdict |
|---|---|---|---|---|---|---|---|
| **W2 baseline** | +0.0767 | +0.2372 | -1.49 | 0.999 | 1.000 | **0.800** | — |
| + EXEC_COMBO exit | +0.0815 | +0.2337 | -1.91 | 0.998 | 0.999 | **0.811** | **KEEP** (+EV, +stress) |
| + ETH ac>=0.20 x1.5 tier | +0.0825 | +0.2501 | -1.49 | 0.999 | 1.000 | **0.818** | **KEEP** (best fwd mean) |
| + body<=0.374/0.431 conf-size | +0.0740 | +0.2354 | -1.47 | 0.999 | 1.000 | **0.813** | **KEEP** (+stress) |
| + vr-size 1.0/0.75/0.5 | +0.0751 | +0.2325 | -1.47 | 0.999 | 0.999 | 0.799 | **KEEP** (risk-neutral; marginal) |
| **+ ETH ac floor 0.15->0.10** | +0.0699 | +0.2159 | -1.49 | 0.983 | 0.992 | **0.641** | **REJECT -> learning** |
| +vrsize+body+ethtier (no floor) | +0.0769 | +0.2434 | -1.47 | 0.999 | 0.999 | **0.824** | the winner |

The ETH ac-floor lowering is the SOLE source of the degradation: the ac in [0.10,0.20) band is
+0.016R train (n9), both fwd years roughly flat — per-sleeve "positive both years" but at crypto's
conf 0.85 it adds ~20 low-quality trades/yr whose tail the stress amplifies (-16pp). **Kept ETH at
ac>=0.15** and instead sized UP only the ac>=0.20 hi-conviction tier.

---

## 2. Per-item re-validation (train+forward, per-year) — `KB3_revalidate_metals.py`

All on the DEPLOYED metals_core cascade entries (H1->M15 better-fill), n=131 (TRAIN 82 / FWD 49).

| item | TRAIN ev | 2025 | 2026 | FWD ev | verdict |
|---|---|---|---|---|---|
| M0 STATE_D (deployed baseline) | +0.482 | +1.321 | +1.014 | +1.164 | — |
| **M2 EXEC_COMBO exit** | **+0.679** | +1.250 | +1.220 | **+1.235** | **KEEP** train-validated, both fwd yrs +, 2026 +1.01->+1.22 |
| M1 vr-size (size-wtd EV/unit) | +0.502 | — | — | **+1.288** | **KEEP** confidence-size, monotone, delete nothing |
| M3 body<=0.374 KEEP bucket | +0.721 | +1.593 | +1.529 | +1.555 | KEEP-as-size (100% win, both yrs +) |
| M3 body>0.374 DROP bucket | +0.254 | +0.940 | **-1.046** | +0.278 | demote to x0.5 (2026 NEG) — kept small |
| **STACK combo+vrsize+body (size-wtd)** | **+0.768** | — | — | **+1.594** | **+0.43R/trade vs deployed** |
| LOC vr<=1.281 + combo (miner's +2.28) | +1.083 | +1.998 | +2.709 | **+2.309** | the localization reproduces (+2.31R, 94% win, n16) |

metals_softband body<=0.431 (size-wtd): baseline FWD +0.170 -> KEEP bucket **+0.601** (both yrs +);
DROP bucket FWD -0.178 (both yrs neg) -> x0.5. Confidence-size, delete nothing.

ETH carrier (raw H4 stream): ac>=0.15 FWD +0.414 but **2026 NEGATIVE -0.951 (n4)**; ac>=0.10 FWD
+0.322 both yrs + but DILUTES the book (see §1). ac>=0.20 hi-conviction: TRAIN +2.145 / 2025 +2.663
(2026 n=1 only -> sized x1.5, not larger; train+2025 justify the tier, 2026 too thin to lean on).

Carried-from-W2 items, RE-VALIDATED here:
- **energy supply-shock vr>=2 runR=4**: TRAIN +0.641->**+0.749**, 2025 +0.143->**+0.241**, 2026
  +0.985->**+1.115** — both fwd yrs improve. runR=5 is fwd-mixed, runR=6 has a NEGATIVE 2025; runR=4
  is the robust sweet spot. **CONFIRMED.**
- **gated NY-JPY 2nd session**: 2025 +0.097 / 2026 +0.228 (both fwd yrs +); pure-FX control NEGATIVE
  both years (2025 -0.041 / 2026 -0.210) — edge is JPY-specific, not a generic session artifact.
  **CONFIRMED.**

---

## 3. The Wave-3 book (`INTEG_portfolio_build_w3.py`) — what shipped

metals_core: EXEC_COMBO exit (scale 50% @2.0R, vol-banded profit-lock 0.25/0.5/0.75, target
4.0/3.0/2.5) on the SAME cascade entries; vr-size 1.0/0.75/0.5; body<=0.374 small-bar -> full conf,
big-body -> x0.5. metals_softband: body<=0.431 conf-size. crypto: ETH ac>=0.20 x1.5 hi-conviction
tier (kept ac>=0.15 floor). energy runR=4 + NY-JPY carried & re-validated. Confidence WEIGHTS
unchanged (harvest acts purely via per-trade `intra_size` + exit policy). Frequency unchanged
(~1512 trades/yr fwd) — the harvest is exit/sizing, not new entries.

### Upgraded combined MC: W2 -> W3 (20k paths)

| risk/unit | P(pass) all W2->W3 | P(pass) fwd W2->W3 | **P STRESS1.5x W2->W3** |
|---|---|---|---|
| 0.50% | 100.00% -> 100.00% | 100.00% -> 100.00% | 94.36% -> **96.07%** (+1.71pp) |
| 0.75% | 99.97% -> 99.99% | 100.00% -> 100.00% | 86.16% -> **88.99%** (+2.83pp) |
| 1.00% | 99.85% -> 99.84% | 99.96% -> 99.92% | 79.66% -> **82.76%** (+3.10pp) |
| 1.50% | 98.06% -> 98.46% (+0.40) | 99.27% -> 99.18% | 70.50% -> **72.85%** (+2.35pp) |
| 2.00% | 94.66% -> 95.52% (+0.86) | 97.65% -> 97.30% | 64.68% -> **65.46%** (+0.78pp) |

- **Combined daily mean unit-R: +0.0767 -> +0.0794** (forward +0.2372 -> **+0.2428**). Higher EV.
- **Stress 1.5x P(pass) improves at EVERY size** — the hardest gate, and the headline win. The
  combo's deeper-but-locked runner + the ETH hi-conviction tier raise EV faster than they raise the
  left tail (worst day -1.49 -> -1.70 but offset by the +EV; best day +4.40 -> +5.34).
- All-history P(pass) improves where it matters for survivability (1.5/2.0%); saturated at the low
  end. Forward P(pass) within MC noise of an already-99.7%+ surface.

### 2-account live allocation (both trade FULL diversified book)

| allocation | base P(both) W2->W3 | STRESS1.5x P(both) W2->W3 |
|---|---|---|
| **balanced 0.75/0.75 (recommended)** | 99.92% -> **99.99%** | 74.72% -> **79.00%** (+4.3pp) |
| conservative 0.50/0.50 (capital-protect) | 100.00% -> 100.00% | 83.66% -> **88.17%** (+4.5pp) |
| staggered 1.00/0.50 | 99.70% -> 99.88% | 63.33% -> 68.49% |
| staggered 1.00/0.75 | 99.70% -> 99.88% | 64.68% -> 68.97% |

Daily-breach remains mathematically 0% across 0.5-2.0% (worst single day -3.40% @2.0% vs -5% limit).

---

## 4. Verdict + learnings

**SHIP the Wave-3 book.** The D4 harvest, applied with book-level discipline, makes the book both
higher-EV (combined mean +0.0767 -> +0.0794, fwd +0.2372 -> +0.2428) AND more stress-robust (1.5x
stress P(pass) up +1.7..+3.1pp at every size; balanced 2-account stress 74.7% -> 79.0%) at unchanged
frequency. Recommended live config unchanged: **both FTMO accounts, full 8-sleeve book, 0.75%/0.75%
balanced** (conservative 0.50%/0.50% for max survivability).

LEARNINGS (kept, not killed):
- **ETH ac-floor 0.15->0.10 is a per-sleeve win but a BOOK loss.** Both fwd years are positive in
  isolation, but the low-persistence ac[0.10,0.20) band injects tail variance at conf 0.85 that the
  1.5x stress punishes (-16pp). The honest action is to KEEP ac>=0.15 as the carrier and size up the
  ac>=0.20 tier — which is exactly where the EV concentrates (TRAIN +2.15 / 2025 +2.66). Re-test the
  ac>=0.20 tier size when more 2026+ ETH LTF data arrives (currently 2026 n=1).
- **vr-size is risk-neutral, not EV-additive, at the book level** (stress 0.800 -> 0.799). It
  reduces the high-vol/big-body core's contribution (correct risk control) but doesn't raise P(pass)
  on its own; kept because it is the miner's monotone localization and stacks cleanly with combo.
- **runR=4 is the energy shock ceiling**: runR=5/6 push deeper train EV but break forward (runR=6
  has a NEGATIVE 2025). The deepest train target is NOT the most forward-robust.

## Artifacts
- `INTEG_portfolio_build_w3.py` — Wave-3 integrator (W2 + revalidated harvest)
- `INTEG_PORTFOLIO_W3_RESULT.json` / `INTEG_W3_streams_cache.pkl` — upgraded book results + streams
- `KB3_revalidate_metals.py` / `KB3_REVALIDATE_METALS_RESULT.json` — per-sleeve re-validation
- `KB3_ablation.py` / `KB3_ABLATION_RESULT.json` — book-level which-item-helps decomposition
- W2 baseline preserved unmodified: `INTEG_PORTFOLIO_W2_RESULT.json`, `INTEG_portfolio_build_w2.py`
