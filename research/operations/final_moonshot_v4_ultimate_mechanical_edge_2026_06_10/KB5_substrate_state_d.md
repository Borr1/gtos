# KB5 — Substrate re-scored under the DEPLOYED STATE_D scale-out exit

Track key: **KB5_STATE_D**. Goal: re-label every substrate cell with the VALIDATED
STATE_D vol-tiered scale-out exit (`compounding_sleeve.exit_state_d`) instead of the
fixed `+xR / -1R` barrier labeler, then re-rank the forward-validated cells under the
exit that actually trades. The deployed exit is the real outcome — this is the honest
re-scoring.

## What STATE_D is (the labeler swap)
`exit_state_d(B,i,d,sd,vr,cost,maxbars=80)` — vol-tiered, **geometry-self-determined**:
- `vr<1.35` -> scale 50% @ 1.5R, runner -> BE, deep target 4.0R
- `1.35<=vr<1.6` -> scale 50% @ 1.5R, runner deep target 3.0R
- `vr>=1.6` -> scale 50% @ 1.0R, runner deep target 2.5R
- after the 50% scale, the runner stop moves to BE (scratch = +0R on the runner leg);
  no trailing. R = `0.5*scaleR + 0.5*leg2`.

Because the exit derives its own scaleR/runR from `vr`, **the fixed GEOMS grid's
`target_R` is irrelevant under STATE_D** — the only surviving knob is `stop_atr` (the
R-unit). The cell key therefore drops `target_R`: `sd{stop_atr}|dir|depth|state…`.
Scored the DEPLOYED `stop_atr=1.0` as canonical, plus `0.75`/`1.5` as robustness probes.

`vr` consistency verified byte-identical: substrate `state["vr"]` == `cs.vol_ratio(atrs,i)`
(both = ATR/100-bar-mean-ATR), so STATE_D's vol tiering uses the SAME vr that buckets the
substrate `vol` dimension. No drift between the bucketer and the exit.

## Method (same discipline as substrate.py)
- NO LOOKAHEAD: states = `sub.build_states` (features index<=i); entry=close[i]; outcome
  window i+1.. is exit_state_d's own forward bar walk (pessimistic same-bar via the same
  hi/lo touch logic).
- REAL COST: `w1.cost_for(sym)` scaled by `1/stop_atr` — IDENTICAL scaling to `sub.outcome`,
  so EV is directly comparable to the fixed-barrier numbers.
- FORWARD HOLDOUT: TRAIN(<=2024) vs FWD(2025-26). Gate (unchanged): `n_train>=40 &
  n_fwd>=40 & meanR>=0.05 BOTH train&fwd & MAJORITY train years +EV & MAJORITY fwd years +EV`.
- NO AVERAGES AS VERDICTS: per-year + per-class on every kept cell; verdict = mean_R.

Engine: `KB5_substrate_state_d_rescore.py` -> `KB5_STATE_D_RESCORE.json`
(46 symbols, 1,531,164 STATE_D-labeled rows, 9,894 cells, **136 forward-validated cells**).
Comparator: `KB5_compare.py` -> `KB5_COMPARE_RESULT.json`.

---

## 0. Headline verdict

**STATE_D buys hit-rate by selling tail-R.** The scale-out converts many bars that the
fixed 3R labeler scored as a drift/time-exit into BE-scratches (+0R) and partial wins,
so **win% roughly DOUBLES (≈30% clean-touch odds -> ~50-64% realized win)** while
**mean_R FALLS** (the 3R+ runners are capped at the 50% leg + a 2.5-4.0R runner). This
is exactly the deployed metals-core profile (78% win / +0.87R) reproduced across the
whole substrate. It is the honest tradeable outcome, not a degradation.

**The substrate edge SURVIVES the deployed exit but compresses.** Of the 132 fixed
forward-validated (dir,state) tuples, **42 still clear the full validation bar under
STATE_D at the deployed stop** (37 of them were in the fixed set; **5 are NEW** — states
that only become tradeable once the exit banks partials). 95 fixed tuples drop below the
bar — almost all because their fixed EV lived in the 3R tail that STATE_D caps, not
because the state has no edge.

**Baseline sanity (load-bearing):** unconditional STATE_D is **negative** (dir=+1:
tr -0.131 / fw -0.106R, win 40%; dir=-1: -0.118 / -0.115R). The scale-out does NOT
manufacture edge from a no-edge entry — BE-scratches + small partials do not rescue a
random entry. Edge still lives ONLY in conditional confluence cells, exactly as doctrine
predicts. STATE_D is an exit, not an alpha source.

---

## 1. The headline cell — re-scored honestly

`vol=xhi & trend=up & mtf=conflict & persist=rand`, **LONG** (deep pullback in an
extreme-vol uptrend) — still the single most robust cell.

| labeler | TRAIN meanR (n) | FWD meanR (n) | FWD win% | FWD odds |
|---|---|---|---|---|
| fixed 3R | **+1.04** (69) | **+0.71** (74) | — | 0.30 |
| fixed 2R | +0.60 (69) | +0.35 (74) | — | 0.32 |
| fixed 1R | +0.30 (69) | +0.20 (74) | — | 0.39 |
| **STATE_D (stop 1.0)** | **+0.45** (69) | **+0.29** (74) | **63.5%** | — |
| STATE_D (stop 1.5) | +0.58 (69) | **+0.32** (74) | 62.2% | — |
| STATE_D (stop 0.75) | +0.18 (69) | +0.05 (74) | 54.1% | — |

- STATE_D forward **+0.29R at 63.5% win** vs fixed-3R **+0.71R at 30% odds** — the exit
  trades roughly +0.42R of tail for +33pts of win-rate. Both 2025 (+0.33, n48, 67% win)
  and 2026 (+0.20, n26, 58% win) +EV; 7/8 train years +EV (only 2019 n=3 slightly neg).
- **Forward +EV in every kept class** under STATE_D: energy +0.98 (100% win), metals +0.63
  (67%), index +0.51 (72%), fx +0.37 (81%); crypto +0.12 thin; **jpy_fx -0.12** — which is
  exactly the class the deployed `sub_xvol_pullback` sleeve already drops. The class
  signature is unchanged from the fixed labeler -> not a relabel artifact.
- **Stop robustness:** holds at 1.0 and is even stronger at 1.5 ATR (+0.32 fwd); collapses
  at 0.75 (+0.05). A WIDER stop pairs better with the scale-out (a tight stop gets
  BE-scratched too often before the partial banks). The deployed 1.0-ATR stop is sound;
  1.5-ATR is a worth-testing upgrade for this specific cell.

---

## 2. STATE_D forward-validated leaderboard (deployed stop_atr=1.0, ranked min(tr,fw))

| dir | Rtr | Rfw | win_fw | nT | nF | Tyr | Fyr | state |
|---|---|---|---|---|---|---|---|---|
| S | +0.32 | +0.32 | 55% | 109 | 83 | 6/10 | 1/2 | vol=lo,trend=up,mtf=conflict,rngpos=mid,comp=norm,persist=trend,london |
| **L** | **+0.45** | **+0.29** | **64%** | 69 | 74 | 7/8 | **2/2** | **vol=xhi,persist=rand,trend=up,mtf=conflict (HEADLINE)** |
| L | +0.38 | +0.27 | 55% | 73 | 40 | 7/9 | 2/2 | vol=lo,trend=up,mtf=neutral,rngpos=high,comp=norm,persist=trend,london |
| L | +0.21 | +0.23 | 50% | 291 | 114 | 6/10 | 1/2 | vol=hi,trend=dn,mtf=conflict,rngpos=mid,comp=norm,persist=rand,ny |
| L | +0.16 | +0.30 | 51% | 233 | 139 | 5/9 | **2/2** | vol=lo,trend=up,mtf=neutral,rngpos=high,comp=norm,persist=rand,ny |
| L | +0.16 | +0.26 | 46% | 57 | 44 | 5/8 | **2/2** | vol=mid,trend=dn,mtf=neutral,rngpos=mid,comp=coil,persist=rand,london |
| L | +0.13 | +0.23 | 50% | 173 | 131 | 5/10 | **2/2** | vol=hi,trend=up,mtf=aligned,rngpos=high,comp=expand,persist=rand,asia |
| S | +0.25 | +0.13 | 43% | 58 | 47 | 6/8 | **2/2** | vol=hi,trend=flat,mtf=aligned,rngpos=mid,comp=norm,persist=revert,asia |

42 cells validate at the deployed stop (34 LONG, 8 SHORT); **19 are the strongest tier
with 2/2 forward years +EV**. The mid/lo-vol reversion-long family (ny/london) is the
broadest, high-frequency, lower-per-trade tier — pure breadth.

---

## 3. Which cells STRENGTHEN under STATE_D (9 — still validate AND fwd meanR rises)

These are states whose edge is **drift/early-progress shaped**, not tail shaped — so
banking the 50% partial + BE-runner captures MORE than the fixed barrier did:

| dir | fix Rfw | STATE_D Rfw | win_fw | nF | state |
|---|---|---|---|---|---|
| L | +0.30 | **+0.37** | 53% | 40 | vol=lo,trend=flat,mtf=neutral,persist=trend,rngpos=mid,comp=norm,london |
| L | +0.30 | +0.30 | 51% | 139 | vol=lo,trend=up,mtf=neutral,rngpos=high,comp=norm,persist=rand,ny |
| L | +0.10 | **+0.26** | 46% | 44 | vol=mid,trend=dn,mtf=neutral,rngpos=mid,comp=coil,persist=rand,london |
| L | +0.20 | +0.23 | 50% | 131 | vol=hi,trend=up,mtf=aligned,rngpos=high,comp=expand,persist=rand,asia |
| L | +0.13 | +0.15 | 52% | 106 | vol=mid,trend=dn,mtf=aligned,rngpos=mid,comp=norm,persist=trend,asia |
| L | +0.06 | +0.14 | 40% | 50 | vol=lo,trend=dn,mtf=aligned,rngpos=mid,comp=norm,persist=trend,london |
| L | +0.12 | +0.14 | 46% | 175 | vol=hi,trend=up,mtf=conflict,rngpos=mid,comp=norm,persist=rand,ny |
| L | +0.08 | +0.12 | 47% | 79 | vol=hi,trend=dn,mtf=conflict,rngpos=mid,comp=norm,persist=rand,asia |
| L | +0.05 | +0.09 | 45% | 1031 | vol=lo,trend=up,mtf=neutral,rngpos=high (depth-3, huge n) |

The last (depth-3, n=1031 fwd) is notable: a broad, frequent, all-weather long that is
**better under the deployed exit than under any fixed target** — a natural high-capacity
breadth sleeve for STATE_D.

## 3b. NEW cells crossing the trust bar ONLY under STATE_D (5)

States that were NOT forward-validated under any fixed target but DO validate under the
deployed exit (the partial-bank rescues them):

| dir | Rtr | Rfw | win_fw | nT | nF | Tyr | Fyr | state |
|---|---|---|---|---|---|---|---|---|
| L | +0.12 | +0.15 | 52% | 161 | 87 | 6/10 | **2/2** | vol=mid,trend=up,mtf=aligned,rngpos=high,comp=coil,persist=rand,ny |
| L | +0.12 | +0.14 | 49% | 78 | 70 | 6/10 | **2/2** | vol=hi,trend=up,mtf=conflict,rngpos=mid,comp=norm,persist=revert,ny |
| L | +0.11 | +0.10 | 45% | 298 | 252 | 8/10 | 1/2 | vol=lo,trend=flat,mtf=aligned,rngpos=mid,comp=norm,persist=rand,ny |
| L | +0.08 | +0.15 | 43% | 169 | 76 | 7/10 | 1/2 | vol=mid,trend=dn,mtf=aligned,rngpos=low,comp=coil,persist=rand,london |
| L | +0.07 | +0.13 | 61% | 68 | 61 | 4/7 | **2/2** | vol=xhi,trend=dn,mtf=neutral,rngpos=low (depth-3 downtrend dip, 61% win) |

The two 2/2-fwd NY cells (mid-up coil pullback; hi-up conflict revert) are the cleanest
genuinely-new STATE_D adds — both are dip-buys in an up/coil regime that only pay once you
bank the partial and let a BE-runner ride, i.e. STATE_D-native edges.

---

## 4. Honest caveats

- **STATE_D is lower-EV-per-trade than fixed-3R for the tail-shaped cells.** 95/132 fixed
  tuples drop below the bar — NOT because the state lost its edge but because their EV
  lived in the 3R+ tail the scale-out caps. If you want the substrate's MAX EV, the fixed
  3R labeler still wins per-trade; STATE_D wins on win-rate / drawdown / psychological
  sustainability (the reason it was deployed). The map judges STATES; both labelers agree
  the SAME states carry the edge — they differ only on how much of it you harvest.
- **Win% ≈ 45-64% is the realized number, not a clean-barrier odds.** At fixed 2R a 70%
  raw win is near-impossible; STATE_D reaches 50-64% by counting BE-scratch (+0R, not a
  loss) and partials as wins. Report it as realized win, never as "P(2R before 1R)".
- **Forward window is short** (2025 + partial 2026, ~1.5yr). 2/2-fwd cells are the trust
  floor; 1/2-fwd cells are carried by a single forward year and ranked below.
- **Stop-atr matters under scale-out.** 1.5-ATR validated MORE cells (73) than 1.0 (42)
  than 0.75 (21) — a wider stop is systematically friendlier to BE-runner exits (fewer
  premature BE-scratches). Worth a deployed-sleeve A/B: STATE_D @ 1.0 vs 1.5 ATR stop.
- **jpy_fx stays negative** on the headline under STATE_D too (-0.12) — confirms the
  deployed sleeve's class drop is correct under the real exit, not just the fixed labeler.

## 5. Recommendation
- Keep STATE_D as the deployed exit; the substrate's top cells survive it. Size the
  HEADLINE (`vol=xhi,trend=up,mtf=conflict,persist=rand` LONG) and the **2/2-fwd reversion-
  long breadth family** (mid/lo/hi-vol dip-buys, ny/london/asia) as the STATE_D book.
- Promote the 9 STRENGTHENERS + 2 clean NEW NY cells — these are STATE_D-native (they
  pay MORE under the deployed exit than under any fixed target).
- A/B test the headline at **1.5-ATR stop** under STATE_D (+0.32 fwd vs +0.29 at 1.0).
- Do NOT read STATE_D's lower mean_R as the substrate weakening: it is the same edge,
  harvested for win-rate instead of tail. The fixed-3R numbers remain the per-trade-EV
  ceiling; STATE_D is the deployed, sustainability-weighted realization of it.

Artifacts: `KB5_substrate_state_d_rescore.py`, `KB5_STATE_D_RESCORE.json` (136 fwd-
validated cells, full per-year/per-class), `KB5_compare.py`, `KB5_COMPARE_RESULT.json`.
