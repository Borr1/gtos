# KB4 — Volume / Auction Profile (Market Profile / TPO) layer  (track: VP)

Builder pass 2026-06-15. Executes Grand Vision sec II ("Volume/auction profile from M1/tick: value
area, POC, HVN/LVN ... NOT BUILT YET"). Doctrine held throughout: build & improve, never kill; map
WHERE/WHEN it works (per-cell, per-YEAR, per-SYMBOL, never an average-as-verdict); NO LOOKAHEAD
(prior-day profile only, closed M1 bars only, `geometry_lib.simulate` is the only labeler); FORWARD
HOLDOUT mandatory; HIGH ODDS only from CONFLUENCE; always report sample size; real cost `w1.cost_for`.

## THE ENGINE (reusable, importable) — `volume_profile.py`

A leak-free volume-by-price substrate built from M1 **tick volume** (the standard FX/CFD volume proxy;
all 24 core symbols carry it, median 27-195 ticks/min). Public API:

- `load_m1(sym) -> (times, bars)` — unions every `bridge_ftmo_m1_*` / `bridge_ftmo_ext_m1_*` month,
  deduped, ascending. Coverage is honest: **M1 starts 2024-01** (BTC 2024-08, ETH 2024-10) and runs
  to 2026-06 — ~2.4 years for the 24-symbol liquid core.
- `daily_profiles(sym, bin_atr_frac=0.03) -> (profiles_by_date, sorted_days)` — per-UTC-day
  volume-by-price. Bin width = `0.03 * (rolling-median of the PRIOR 20 days' ranges)` (leak-free
  resolution). Each M1 bar's volume is spread uniformly across the bins its H..L spans.
- `DayProfile`: `poc` (point-of-control), `vah`/`val` (70% value-area edges, expanded from POC by the
  heavier neighbour), `hvn` (high-volume nodes = acceptance/magnets), `lvn` (low-volume nodes/voids =
  rejection/fast-through), plus the raw histogram and day H/L. Tuned bin (frac 0.03 ~35 bins) gives
  median 3 HVN / 2 LVN per day, voids detectable on 545/629 days.
- `prior_profile_at(profiles, days, t)` — returns the profile of the most recent day **strictly
  before** `t.date()`. This is the only profile a decision at time `t` is allowed to see.
- `nearest_node_state(dp, price, atr)` — leak-free state vocab for a price vs a profile:
  `d_poc_atr` (signed dist to POC in ATR), `in_va`/`above_vah`/`below_val`, `near_lvn_atr`,
  `near_hvn_atr`, `at_lvn`/`at_hvn`/`at_poc`/`at_vah`/`at_val`.

**LEAK PROOF (ran):** over 3,714 GER40 H4 entries, `prior_profile_at` returned a profile whose day is
`>= t.date()` exactly **0 times**; every profile's range equals its own day's M1 H/L and its POC sits
inside that range. The layer cannot see the future of the day it trades.

## WHAT WAS MINED (forward odds via `simulate` on H4 entries)

Three auction hypotheses, raw first (`VP_mine_setups.py`), then confluence-gated (`VP_confluence.py`),
then a fair walk-forward verdict (`VP_walkforward.py`):
- **H1 rejection at LVN/void** — price trades into a prior-day void -> fade back toward value.
- **H2 gravitation to POC/HVN** — price far outside value -> revert toward POC.
- **H3 value-area-breakout** — close beyond prior-day VAH/VAL -> continuation vs failure (fade).

## HONEST RESULT 1: raw single-pattern auction averages are NEGATIVE — and that is the doctrine

Every standalone setup loses on BOTH train and forward, AND its invert ALSO loses (n=2k-30k):

| setup | TRAIN(24) R | FWD(25-26) R | invert FWD R |
|---|---|---|---|
| H1 void-reject (t3)        | -0.142 | -0.071 | -0.133 |
| H2 POC-grav (far1.0)       | -0.121 | -0.101 | -0.132 |
| H3 VA-break cont (2R)      | -0.098 | -0.125 |  —     |
| H3b VA-break fade (2R)     | -0.103 | -0.084 | -0.125 |

When a pattern AND its inverse both lose, the bulk average carries no directional edge — the loss is
the cost floor + the H4 random-entry drag on tens of thousands of indiscriminate entries. This is
EXACTLY "no averages as verdicts": the auction edge does not live in a raw pattern, it lives in
**cells + confluence**. (`VP_SETUP_MINE_RESULT.json`)

## HONEST RESULT 2: per-symbol + confluence narrows to a real European-index auction-reversion

Stacking the profile state with independent gates (`cs.vol_ratio`, `cs.autocorr`) and per-class
routing (`VP_confluence.py`), then verdicting under a FAIR chronological **walk-forward 55/45** split
(the calendar `<=2024` split is degenerate here — M1 only starts 2024, so >75% of trades land in
"forward"; WF gives both halves real n). A cell ships only if it is positive on BOTH WF halves, its
invert is opposite-signed, and `n_oos >= 40`.

**Cells that HOLD (`VP_WALKFORWARD_RESULT.json`):**

| cell | WF-TRAIN(55%) R (n) | WF-OOS(45%) R (n) | invert OOS R | per-CALENDAR-year R (n) |
|---|---|---|---|---|
| **EUidx_pocgrav_2.0_vr1.2** (GER40+UK100, >=2.0 ATR from POC, vol_ratio>=1.2 -> fade to POC, tgt=POC) | **+0.135** (186) | **+0.353** (155) | -0.361 | 2024 +0.218(111) / 2025 +0.051(128) / 2026 +0.483(102) |
| EUidx_pocgrav_2.0 (ungated, more freq) | +0.028 (674) | +0.120 (553) | -0.221 | 2024 +0.076 / 2025 -0.020 / 2026 +0.222 |
| UK100_pocgrav_2.0 (single sym) | +0.062 (316) | +0.138 (260) | -0.321 | 2024 +0.126 / 2025 -0.080 / 2026 +0.364 |
| crypto_vabreak_cont (fragile, see below) | +0.202 (207) | +0.010 (170) | -0.328 | 2024 +1.18(54) / 2025 -0.145(248) / 2026 +0.213(75) |

### Top edge (forward-validated): EUidx POC-gravitation, vol-gated
- **Mechanic:** when a European index (GER40/UK100) opens an H4 bar >= 2.0 ATR away from the PRIOR
  day's volume POC, while it is OUTSIDE the prior day's value area, in an elevated-vol regime
  (vol_ratio >= 1.2), fade back toward the POC (target = the POC, stop = 1.0 ATR). The auction logic:
  price stretched far from where volume was transacted, in a volatile state, reverts to value.
- **Confluence is what makes it:** profile-location (far + outside VA) x vol-regime (>=1.2) x class
  route (EU indices). Raw POC-grav without these gates is negative (Result 1). The vr>=1.2 gate alone
  lifts EU-pooled WF-OOS from +0.120 to +0.353 and the invert from -0.221 to -0.361.
- **Validation:** positive on BOTH chronological halves, invert cleanly opposite-signed (a directional
  edge, not survivorship), and positive in **all three calendar years** (2025 only +0.05 — the soft
  year). ~47 signal-days/yr, +79.9R total over the M1 window on the EU pair.

### Fragile / NOT shipped despite passing the WF gate
- **crypto_vabreak_cont** passes the mechanical WF gate but is carried almost entirely by 2024
  (+1.18, n=54); 2025 is -0.145 (n=248). Flag as 2024-regime-driven, NOT a clean ship — the crypto
  sleeve already owns continuation via the Donchian+autocorr carrier (KB2), so this adds nothing safe.
- **energy VA-fade** looked great on 2024 TRAIN (+0.27 to +0.33, n=42-142) but collapses forward
  (2025 -0.04, 2026 -0.40) and the invert flips positive forward -> a single-regime 2024 artifact.
  FALSIFIED, kept only as negative evidence. (This is the Wave-2 immune system working.)
- **US indices + JP225** POC-gravitation does NOT hold both halves (US is TRAIN-negative; the forward
  positivity is single-regime). Only the EUROPEAN indices carry the auction-reversion.

## Per-class summary (where the auction layer works vs not)
- **EU indices (GER40, UK100): the auction-reversion pocket.** POC is a genuine magnet; far+volatile
  excursions revert. Ships at breadth confidence.
- **US indices / JP225:** no both-sided edge — POC-gravitation is single-regime forward only.
- **Energy:** VA-fade is a 2024 artifact (falsified forward). No auction edge survives.
- **Metals / FX / JPY / crypto:** no auction setup clears the WF + invert + n gate as a clean add.
- **LVN/void rejection (H1) and POC magnet as a raw pattern:** negative everywhere — not an edge by
  themselves at H4 granularity; the void/HVN features remain useful as STATE inputs for confluence,
  not as standalone triggers.

## CORR-CHECK vs the existing book
The shipped EU-POC cell is a distinct mechanic (mean-reversion to volume POC) from the book's `idxrev`
sleeve (failed-breakout FADE on H4) and from every metals/crypto/energy carrier. Different trigger,
different timing -> additive breadth in the index class (which the book currently carries only as the
demoted conf-0.15 `idxrev`). It is at least as strong as those breadth sleeves AND positive on both WF
halves and all calendar years, so it is a cleaner index-class breadth source than `idxrev`.

## RECOMMENDATION (size-by-confidence, nothing deleted)
- **ADD `EUidx_pocgrav_2.0_vr1.2` as an index-class breadth sleeve at conf ~0.30-0.40** (above the
  conf-0.15 forward-only sleeves: it holds both WF halves and all calendar years; below the train-deep
  converts: its TRAIN is only the 2024 calendar year). Cap target at the POC (measured), stop 1.0 ATR.
- Keep the un-gated `EUidx_pocgrav_2.0` as the higher-frequency / lower-EV variant if more index
  frequency is wanted.
- Keep the falsified cells (energy VA-fade, US/JP POC-grav) as documented negative evidence, sized to
  zero — they are the immune system confirming the EU pocket is specific, not universal.
- HONEST data caveat to carry forward: this whole layer's TRAIN is the single 2024 calendar year
  (M1 depth). The walk-forward 55/45 is the fair holdout; treat conf accordingly until M1 history
  deepens (the bridge could export pre-2024 M1 for the core symbols in a later pass to lengthen TRAIN).

## FILES (track VP, all under the route dir)
- `volume_profile.py` — the reusable leak-free engine (load_m1, daily_profiles, DayProfile, POC/VA/
  HVN/LVN, prior_profile_at, nearest_node_state). Importable by any sleeve.
- `VP_mine_setups.py` -> `VP_SETUP_MINE_RESULT.json`, `VP_SETUP_PERSYM.json` (raw-pattern mine; shows
  averages are negative; per-symbol cells).
- `VP_confluence.py` -> `VP_CONFLUENCE_RESULT.json` (confluence-gated cells + per-symbol + invert).
- `VP_walkforward.py` -> `VP_WALKFORWARD_RESULT.json` (the FAIR verdict; the 4 cells that hold).
