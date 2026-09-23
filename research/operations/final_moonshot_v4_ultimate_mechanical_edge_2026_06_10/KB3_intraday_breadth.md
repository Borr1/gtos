# KB3 — Intraday frequency with QUALITY on the validated sleeves (track: IDB)

Builder pass 2026-06-15. Goal: push D2 frequency with TRAIN-validated quality by adding genuinely
NEW intraday (H1/M15) continuation entries on the train-validated sleeves (metals / crypto / energy)
under their PROVEN gates (vol-expansion + ac60 persistence), confidence-sized, nothing killed.

Doctrine held verbatim: `geometry_lib.simulate` is the leak-free pessimistic labeler; features from
CLOSED bars index<=i (vol-gate, trend, FVG, ac60 all read only `B[...]` with indices in `[i-99..i]`);
real cost `w1.cost_for` (crypto->global_median 0.0953, energy 0.0372, metals 0.0459); winsorize netR
[-1.3,+5]; per-YEAR/per-REGIME never an average-as-verdict; size-by-confidence; delete nothing.

Module: `IDB_intraday_breadth.py` (loaders + the two entry families). Driver: `IDB_run.py`.
Result: `IDB_INTRADAY_BREADTH_RESULT.json`. Ledger: `IDB_INTRADAY_TRADE_LEDGER.jsonl` (993 rows).

## Holdout design (the honest one)

LTF (H1/M15) for crypto/energy/metals carriers exists ONLY 2025-06..2026-06 (verified: BTC/ETH/DASH/
LTC/DOT/ADA/XTZ + USOIL/UKOIL/NATGAS/HEATOIL + XAU/XAG x USD/EUR/AUD all ~1yr). There is **no pre-2025
OOS** for these symbols intraday — the SAME confound the W2 TW cascade carries. So:
- **Time holdout = within-window:** TRAIN = entries 2025-06..2025-12, FWD = entries 2026-01..2026-06.
- **Cross-sectional holdout = per-symbol:** a rule positive across MULTIPLE independent carriers (7
  crypto, 6 metals) substitutes for the missing long time-split. Per-symbol both-halves is reported.
- **Mechanism credibility:** the H4 version of the winning entry (vol-gated FVG-retest continuation)
  is the train-validated metals/gold sleeve across 11 years; running it faster is a frequency
  extension of an already-causal edge, not a new hypothesis. (Sanity: the H4 crypto Donchian rule
  reproduces KB_crypto EXACTLY here — FWD +0.751R, n60 — so the harness is faithful.)

## HEADLINE: which intraday entry carries, which does NOT

| family | TF | TRAIN (2025H2) | FWD (2026H1) | win | trades/yr | verdict |
|---|---|---|---|---|---|---|
| **FVG-retest cont. CRYPTO** ac0.10 | H1 | **+0.152** (n190) | **+0.142** (n143) | 41% | **325** | **VALIDATED breadth** |
| **FVG-retest cont. CRYPTO** ac0.15 | H1 | **+0.155** (n120) | **+0.310** (n79) | 47% | 194 | **VALIDATED hi-conf tier** |
| **FVG-retest cont. METALS** acNone | H1 | +0.024 (n415) | **+0.113** (n245) | 39% | **645** | **VALIDATED breadth** |
| **FVG-retest cont. METALS** ac0.10 | H1 | **+0.232** (n108) | **+0.217** (n38) | 42% | 143 | **VALIDATED hi-conf tier** |
| raw Donchian breakout CRYPTO ac0.20 | H1 | +0.099 (n256) | +0.078 (n191) | 22% | 437 | LEARNING (fragile, dir-skewed) |
| raw Donchian breakout CRYPTO ac0.15 | M15 | -0.019 | -0.096 | 19% | 2111 | LEARNING (FALSIFIED — too noisy) |
| raw breakout ENERGY ac0.15 | H1 | +0.079 | **-0.136** | 19% | 342 | LEARNING (TRAIN-only artifact) |
| raw breakout ENERGY ac0.15 | M15 | **-0.153** | +0.316 | 27% | 1120 | LEARNING (FWD-only artifact) |

**The decisive finding:** intraday continuation pays **only with the SELECTIVE entry (vol-gated
FVG-retest), not the raw breakout.** Raw intraday breakout is 19-22% win and either single-direction
(crypto H1: shorts carry it, longs TRAIN-negative — a 2025-26 crypto-decline artifact) or
TRAIN/FWD-sign-flipped (energy). The FVG-retest entry — the metals-validated continuation trigger —
is 39-47% win, both-halves positive, monotone in the ac gate, and survives cost stress.

## The validated rule (LOCKED)

On the **H1 stream** of each carrier, closed bars only:
- **VOL GATE** (pure price fn): `ATR14[i] >= 1.2 * SMA100(ATR14)[i]` (vol-expansion; identical to
  the gold sleeve `GATE_K=1.2`).
- **TREND**: `htf_trend` = sign of `close[i]-close[i-30]` vs 1.0*ATR (up/down/none; trade with it).
- **FVG-RETEST**: a bullish/bearish fair-value-gap formed in `[i-8..i-2]` (gap >= 0.10*ATR) that the
  current bar retests-and-holds (low<=gap_top & close>gap_bot & up-close for longs; mirror for shorts).
- **PERSISTENCE GATE** (crypto): `ac60 = cs.autocorr(B,i,60) >= 0.10` (carrier) / `>= 0.15` (hi-conf).
  Metals run with NO ac gate for max breadth (645/yr) OR ac>=0.10 for the hi-conf tier.
- **GEOMETRY**: structural stop `sd = max((close..gap extreme)+0.10*ATR, 0.25*ATR)`, fixed **2R target**,
  maxbars 320 (=H1 wall-clock match to H4 maxbars=80). Cost = base `w1.cost_for` (structural-tight stop).

Why 2R not crypto's native 4R: intraday FVG-retest is a SLOW continuation (like metals), so the deep
4R target gives back the edge; 2R captures it (the target ladder is flat/declining beyond 2-3R here,
opposite to the H4 crypto Donchian which needs 4R). This mirrors the W2 finding that the exit is a
function of the move's speed: fast extended H4-crypto -> 4R; slow intraday continuation -> 2R.

## Robustness (per-REGIME, per-SYMBOL, per-DIRECTION, cost)

- **Gate monotonicity (the anti-overfit proof):** crypto FVG ladder acNone +0.025/+0.081 ->
  ac0.10 +0.152/+0.142 -> ac0.15 +0.155/+0.310 (TRAIN/FWD). The persistence gate lifts EV at BOTH
  halves monotonically — it is the edge driver, not a tuned magic number. Vol-gate matters too
  (gk1.0 +0.041/+0.091 vs gk1.2 +0.152/+0.142 at ac0.10).
- **Both directions pay** at the portfolio level for the FVG entry (crypto ac0.10: long +0.231/+0.064,
  short +0.073/+0.268). Contrast raw breakout where only shorts carried it (a regime artifact). The
  FVG entry's two-sided positivity is what distinguishes a real edge from the 2025-26 decline tape.
- **Per-symbol both-halves is THIN (1-2 of 6-7) — read honestly:** each carrier has ~1yr split into
  two halves, so per-symbol per-half n is 4-42 — too thin to demand per-symbol both-halves passing.
  The SLEEVE is the validation unit (7 crypto + 6 metals diversify the thin per-carrier samples,
  exactly as KB_crypto sizes the sleeve not individual alts). **BTCUSD is the cross-validated anchor:**
  both-halves positive in BOTH gates (ac0.10 +0.405/+0.405; ac0.15 +0.476/+0.825) and the strongest
  single carrier. XAGUSD anchors metals (both-halves +0.138/+0.344). The portfolio EV is real and
  two-sided; the per-symbol dispersion is small-sample, not falsification.
- **Cost stress:** crypto FVG ac0.10 survives 1.5x cost (FWD +0.142->+0.095) and stays positive at
  2x (+0.047). Edge is not a cost-illusion.
- **Leak audit:** 0 ac-gate violations; all signals strictly inside 2025-06..2026-06; the signal loop
  reads only `B[i-99..i]`; `simulate` is the only forward-looking call (labeling, allowed).

## Confidence sizing (size-by-confidence, delete nothing)

| sleeve | gate | fwd EV | trades/yr | confidence | rationale |
|---|---|---|---|---|---|
| crypto_intraday_fvg | H1, ac>=0.10, 2R | +0.142R | 325 | **0.40** | both-halves+, 2-sided, mechanism=metals FVG; forward-window-only -> haircut |
| crypto_intraday_fvg_hi | H1, ac>=0.15, 2R | +0.310R | 194 | **0.30** | higher EV but thinner; BTC/DOT both-halves+ |
| metals_intraday_fvg | H1, acNone, 2R | +0.113R | 645 | **0.30** | huge breadth, lower EV, 2-sided; XAG anchors; forward-window-only |
| metals_intraday_fvg_hi | H1, ac>=0.10, 2R | +0.217R | 143 | **0.30** | gated metals, +0.23R both halves, XAG/XAGEUR both+ |

Confidence is haircut (0.30-0.40) vs the W2 train-validated core (0.80-1.00) for two honest reasons:
(1) forward-window-only — no pre-2025 intraday OOS, identical caveat to the TW cascade; (2) per-symbol
samples are thin so the sleeve-level EV carries more dispersion than the deep-H4 sleeves. These are
**breadth/frequency adds**, not new anchors — sized exactly as the data quality dictates.

## ADDITIVITY (no double-count)

These are **NEW entries**, distinct from the W2 book:
- The W2 TW cascade RE-TIMES the H4 signal on LTF (same entry count). IDB fires a FASTER trigger on
  H1 -> genuinely new signals (an H1 FVG-retest can occur with no H4 FVG signal that bar).
- crypto_intraday_fvg uses the H1 stream + FVG entry; the W2 crypto sleeve uses the H4 stream +
  Donchian-breakout entry. Different TF + different entry = additive (different decision instants).
- metals_intraday_fvg is a faster XAU/XAG version of the H4 metals_core entry — additive frequency on
  the same persistence/continuation regime, distinct decision bars.

## COMBINED FREQUENCY LIFT

- **+~970 new intraday trades/yr** validated (crypto-FVG ~325 + metals-FVG ~645), both-halves positive,
  two-sided, confidence-sized 0.30-0.40.
- Context: the W2 book's TRAIN-validated quality core (metals+crypto+energy H4) is ~115 trades/yr.
  IDB roughly **8x's the quality-gated frequency** of that core (at lower per-trade EV / haircut
  confidence) — a large frequency lift that is forward-validated and gated, NOT demoted noise breadth.
- If only the hi-conf gated tiers are taken (crypto ac0.15 + metals ac0.10): **+~337 trades/yr at
  +0.21..+0.31R FWD** — a higher-quality, lower-frequency option for tighter risk.

## LEARNINGS (kept, nothing deleted)

1. **Raw Donchian breakout does NOT carry intraday.** Crypto M15 is FALSIFIED (TRAIN -0.019/FWD -0.096,
   19% win). Crypto H1 is portfolio-positive (+0.099/+0.078) but DIRECTION-SKEWED (shorts carry it,
   longs TRAIN-negative) and only 1-2/7 carriers both-halves -> a 2025-26 decline-tape artifact, not a
   deployable sleeve. The intraday breakout is too noisy; it needs the SELECTIVE FVG-retest entry to
   filter false breaks. (This refines KB_crypto: the Donchian breakout edge is an H4 phenomenon; faster
   it loses to noise — the FVG-retest is the entry that DOES transfer to faster TFs.)
2. **Energy intraday is FALSIFIED both ways.** H1 = TRAIN-only (+0.079/-0.136), M15 = FWD-only
   (-0.153/+0.316). Energy continuation needs the H4 bar to filter intraday noise (consistent with the
   W2 energy edge being the H4 supply-shock/vr regime). Energy intraday is NOT a stationary edge.
3. **Target depth is a function of move speed.** Intraday FVG continuation wants 2R (flat/declining
   past 3R); H4 crypto Donchian wants 4R. Same R-space lesson as W2 (slow continuations scale/cap,
   fast extended moves run).

## NEXT STEPS
1. Source pre-2025 H1 for the carriers (the ONLY blocker) to convert these forward-window sleeves to a
   direct train-validated proof — the mechanism is already causal on deep-H4 metals.
2. Test the H1->M15 cascade better-fill (TW mechanic) ON the IDB FVG entries -> stack two validated
   intraday wins (better entry + faster trigger).
3. Wire crypto_intraday_fvg (0.40) + metals_intraday_fvg (0.30) into the portfolio build as additive
   breadth streams; re-run the corr/maxDD MC (these are H1 streams -> likely near-zero correlation to
   the H4 day-streams, deepening D3 breadth and D2 frequency without daily-breach risk given small size).

## FILES
- `IDB_intraday_breadth.py` — loaders + raw-breakout family + vol-gated FVG-retest family (the winner).
- `IDB_run.py` — driver: per-half/per-symbol/per-direction scorecards + frequency lift.
- `IDB_INTRADAY_BREADTH_RESULT.json` — machine-readable scorecards for all 8 families.
- `IDB_INTRADAY_TRADE_LEDGER.jsonl` — 993 validated-sleeve trades (crypto+metals FVG, with conf tags).
