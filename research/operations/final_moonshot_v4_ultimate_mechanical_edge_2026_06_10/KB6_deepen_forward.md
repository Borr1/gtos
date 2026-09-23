# KB6 — Deepen forward validation via more data (track: deepen_forward)

Builder pass 2026-06-15. Goal: close the remaining forward-only / short-window caveats by exporting
MORE bridge history for (1) pre-2024 M1 for the volume-profile core (GER40/UK100) to give
`vp_euidx_pocgrav` a real TRAIN side, and (2) deeper LTF that converts the sub-H4 lead-lag / IDB
overlays from forward-only to train-validated. Then re-validate train->forward and report which
caveats CLOSE vs remain HARD broker ceilings.

Doctrine held verbatim: build & improve, never kill (map WHERE/WHEN); per-YEAR/per-SYMBOL never
average-as-verdict; NO LOOKAHEAD (`prior_profile_at` / closed-bar features only; `geometry_lib.simulate`
the only labeler); FORWARD HOLDOUT mandatory (TRAIN<=2024 vs FORWARD 2025-26 + per-year + n);
distrust forward-only / single-regime positives; real `w1.cost_for`; winsorize netR [-1.3,+5];
size-by-confidence; delete nothing; verify supersets / clean union before merge.

## Bridge probe — TRUE earliest history the broker serves NOW (read-only `copy_rates_range`)

The broker serves DEEPER history than was on disk. Key floors (probed directly):

| symbol | M1 floor | M15 floor | H1 floor | what was on disk before |
|--------|----------|-----------|----------|-------------------------|
| GER40  | **2023-04-18** | **2018-03-26** | 2018-03 | M1 2024-01+, M15 2025-06+ |
| UK100  | **2023-04-11** | **2017-12-28** | 2017-12 | M1 2024-01+, M15 2025-06+ |
| US30   | 2023-05-19 | **2019-02-08** | 2019-02 | M1 2024-01+, M15 2025-06+ |
| EU50   | 2023-01-02 | 2021-01 | 2021-01 | M1 2024-01+ |
| SPX500 | 2023-05-10 | 2021-01 | 2021-01 | M1 2024-01+ |
| AUDJPY | 2023-09-29 | **2017-01-02** | 2014 | M15 2025-06+ |
| XAUUSD | 2023-08-07 | 2014-01-02 | **2014-01-02** | H1/M15 2025-06+ |
| XAGUSD | 2023-05-22 | 2014-01-02 | **2014-01-02** | H1/M15 2025-06+ |
| XAU/XAG EUR,AUD | 2023 | 2021-01-21 | 2021-01-21 | H1/M15 2025-06+ |
| BTC/ETH/DASH/alts | — | 2024-07/10 | 2024-07/10 | (hard ceiling, unchanged) |

So: index M1 reaches back to ~2023-04 (GER40/UK100), index M15 to 2017-2019, **XAU/XAG H1+M15 to
2014**, and AUDJPY M15 to 2017. M1 pre-2023 and crypto pre-2024-07 are HARD broker ceilings (a single
clamp bar is returned). This is exactly the new history the prior passes (KB2/KB3/KB4/KB5) lacked.

## Exports written (existing conventions: versioned dir, manifest.json, read_only=True, per-file sha256, 0 errors)

1. `data/mt5_research_exports/bridge_ftmo_m1_backfill_2023/` — 14 symbols (GER40/UK100/SPX500/NAS100/
   US30_cash/EU50_cash/FRA40/JP225/US2000/USDJPY/AUDJPY/GBPJPY/XAUUSD/XAGUSD) M1 for 2023 (broker-
   capped per floors above). 108 MB, 0 errors. The dir prefix `bridge_ftmo_m1_` means
   `volume_profile._m1_month_dirs()` AUTO-UNIONS it -> `vp.load_m1('GER40')` now serves 2023-04+
   (verified: 181-183 NEW pre-2024 trading days for GER40/UK100, 0 duplicate timestamps, clean union).
2. `data/mt5_research_exports/bridge_ftmo_metals_h1_backfill_2014_2025/` — XAU/XAG USD H1 2014-01+
   (11.4 yr, 67k bars each), XAU/XAG EUR/AUD H1 2021-01+. 13 MB, 0 errors. Clean seam to existing
   2025-06+ H1 (overlap_bars=0, 0 mismatch — deep export ends 2025-05-30, base starts 2025-06).
3. `data/mt5_research_exports/bridge_ftmo_idx_m15_backfill_2017_2025/` — GER40 M15 2018-03+, UK100
   2017-12+, US30 2019-02+, AUDJPY 2017-01+. 28 MB, 0 errors. 0 dup ts, strictly ascending,
   continuous coverage (GER40/UK100 M15 are sparse 2018-2020 and dense from 2021; US30 dense 2019+;
   AUDJPY dense 2017+ — TRAIN is effectively a multi-year cross-regime split, not a single year).

---

## RE-VALIDATION VERDICTS (TRAIN<=2024 -> FORWARD 2025/2026, per-year, per-symbol, leak-audited)

### 1) VP `EUidx_pocgrav` -> **CONVERTS to TRAIN-VALIDATED** (the headline win)
`KB6_revalidate_vp_euidx.py` re-runs the EXACT `VP_confluence.gen_signals` cell on the now-deeper M1.
With 2023 M1 the calendar TRAIN<=2024 split is no longer degenerate (KB4's reason for using a WF 55/45).

| cell | TRAIN<=2024 R (n) | FWD25 / FWD26 | FWD R (n) | invert FWD | per-CALENDAR-year |
|------|-------------------|---------------|-----------|------------|-------------------|
| **EUidx_pocgrav_2.0_vr1.2** (shipped) | **+0.214 (155)** | +0.051 / +0.483 | **+0.243 (230)** | **-0.408** | 2023 +0.202(44) / 2024 +0.218(111) / 2025 +0.051 / 2026 +0.483 |

- **Positive in ALL FOUR calendar years (2023,2024,2025,2026)**, both NEW train years strongly positive.
- Per-symbol BOTH-SIDE positive: GER40 TRAIN +0.199 / FWD +0.212 (n76/123); UK100 TRAIN +0.228 /
  FWD +0.277 (n79/107) — both carriers `both_pos=True`. Invert cleanly opposite (-0.408) = directional.
- **Permutation sign-null** (directionless null, same magnitude dist): TRAIN z=+1.56 (p=0.059),
  FWD z=+2.01 (p=0.022). The new train clears the directionless null at ~94%.
- **Vol-gate is the edge (confirmed on the new train year):** ungated `EUidx_pocgrav_2.0` is
  TRAIN-NEGATIVE (-0.039; 2023 -0.207); GER40-alone ungated is TRAIN -0.158 (2023 -0.427). The
  vr>=1.2 gate flips both to train-positive. `EUidx_pocgrav_2.5_vr1.2` also holds (TRAIN +0.054 /
  FWD +0.248). This HARDENS KB4's "confluence is what makes it" on real multi-year train data.
- **Leak audit:** 0 violations over ~4800 H4 entries/symbol; `prior_profile_at` never returns a
  profile dated >= entry day; 1086-1094 train entries genuinely use the NEW 2023 profiles.
- **VERDICT: KB4's honest caveat ("this whole layer's TRAIN is the single 2024 calendar year")
  CLOSES.** The shipped EU-POC cell now has a 2-year train (2023+2024), positive both train years,
  positive all 4 calendar years, invert-opposite, null-cleared. **Recommend upgrading its confidence
  from KB4's 0.30-0.40 to ~0.50-0.55** (still below the 11-yr deep-H4 metals core, but now
  multi-year-train-validated, not WF-only). Artifact: `KB6_VP_EUIDX_REVAL_RESULT.json`.

### 2) Sub-H4 lead-lag (M15) forward-only edges -> **2 CONVERT, the rest revealed FORWARD-ONLY** (the immune system)
`KB6_revalidate_leadlag_subh4.py` prepends the deep idx/AUDJPY M15 dir to the KB5 engine's
`_M15_DIRS` and re-runs the EXACT `mine_pair`/`split_stats`/`null_test`/`self_gated` on the
forward-only head edges — now with genuine TRAIN.

| edge (KB5 forward-only head) | TRAIN<=2024 R (n) | FWD R (n) | null z | leader_adds FWD | verdict |
|------------------------------|-------------------|-----------|--------|-----------------|---------|
| **GER40->UK100 [london] L2 z2 rev** | **+0.281 (191)** | **+0.446 (97)** | 1.29 | +0.090 | **CONVERTS — train+forward** (2022/2024 + 2025/2026 +) |
| **US30->USDJPY [ny_open] L4 z2 mom** | **+0.026 (390)** | **+0.283 (93)** | 2.08 | +0.022 | **CONVERTS (marginal train)** — corroborates KB4 H4 |
| US30->GER40 [ny_open] L8 z1.5 mom | -0.005 (316) | +0.324 (147) | **5.34** | **+0.379** | **STAYS forward-only** — train ~flat/neg; mechanism real fwd but not stationary |
| USDJPY->AUDJPY [london_ny] L8 z2.5 | -0.067 (840) | +0.523 (171) | 3.83 | **+0.855** | **STAYS forward-only** — train-neg 2017-2022; aggressive-config 2025-26 artifact |
| US30->AUDJPY [ny_open] rev | -0.118 (682) | +0.244 (148) | 2.76 | +0.393 | **STAYS forward-only** — train-negative |
| US30->GER40 / GER40->UK100 (z2 variants) | neg/thin | mixed | <1 | — | noisy, not validated |

- **The decisive learning:** the deep M15 SEPARATES the two real cross-regime sub-H4 edges
  (GER40->UK100 London co-move; US30->USDJPY NY-open) from the single-regime forward artifacts.
  US30->GER40 and USDJPY->AUDJPY have HUGE forward null-z (5.34, 3.83) and big leader-adds, so the
  2025-26 mechanism is genuine — but their multi-year TRAIN is flat/negative, so they are NOT
  train-validated cores. KB5 published them as top forward-only edges; this pass confirms they STAY
  forward-only (keep as breadth/low-confidence, do NOT size as stationary).
- **Data honesty:** GER40/UK100 M15 are sparse 2018-2020, dense from 2021 -> the GER40->UK100 TRAIN
  is effectively 2021/2022-2024 (covers the 2022 bear + 2023 chop + 2024 trend = real cross-regime).
  US30/AUDJPY are dense from 2019/2017. Union is leak-clean (0 dups, ascending, 0 seam mismatch).
- **VERDICT: KB5's "index/AUDJPY M15 followers are forward-only (trN=0)" caveat CLOSES** — they now
  have a real TRAIN. 2 of the head forward-only edges convert (GER40->UK100, US30->USDJPY); the
  others are revealed as single-regime forward edges (kept, sized as breadth, not promoted).
  Artifact: `KB6_LEADLAG_SUBH4_REVAL_RESULT.json`.

### 3) IDB metals intraday FVG sleeve -> **FALSIFIED as a train edge** (deep H1 corrects the WF-only positive)
`KB6_revalidate_idb_metals.py` repoints the IDB metals carriers to the deep XAU/XAG H1 (2014-01+) and
re-runs the EXACT `IDB.fvg_retest_signals` entry, replacing KB3's WITHIN-WINDOW split (TRAIN=2025H2,
FWD=2026H1 — both actually inside the forward tape) with a REAL TRAIN<=2024 split.

| IDB metals tier | TRAIN<=2024 R (n) | FWD25 / FWD26 | FWD R (n) | per-year (recent train) |
|-----------------|-------------------|---------------|-----------|-------------------------|
| metals_intraday_fvg (acNone) | **-0.036 (4010)** | +0.036 / +0.113 | +0.057 (883) | 2022 -0.034 / 2023 -0.083 / 2024 -0.153 |
| metals_intraday_fvg_hi (ac>=0.10) | **-0.038 (961)** | +0.118 / +0.217 | +0.140 (172) | 2022 +0.133 / 2023 -0.088 / 2024 -0.217 |

- **TRAIN<=2024 is NEGATIVE (both tiers), and NEGATIVE in the most recent comparable train years
  (2023, 2024).** Negative in 7 of 11 train years for the breadth tier. The forward number reproduces
  in sign (+0.06/+0.14), but KB3's "metals_intraday_fvg +0.113R both halves" was a **2025-26
  single-regime positive** that the WITHIN-window holdout (structurally unable to see pre-2025) could
  not detect. On real 11-year H1, the entry does not carry a train edge.
- Per-symbol: only XAGUSD-hi and XAGAUD-hi are both-side positive (and thin); XAUUSD is TRAIN+FWD
  negative. No clean cross-sectional both-side support on the deep train.
- Clean union (deep H1 ends 2025-05, base starts 2025-06; overlap_bars=0, 0 mismatch). Cost
  class-correct (XAU/XAG 0.0459).
- **VERDICT: the IDB metals sleeve's caveat CLOSES with the honest finding that it is NOT
  train-validated** — same single-regime pattern the data-depth track keeps finding (fx_jpy, idxrev,
  energy-VA-fade). **Recommend dropping metals_intraday_fvg from conf 0.30 to ~0.10-0.15** (forward-
  window breadth only, train-falsified), keeping it (delete nothing) as documented negative evidence.
  The CRYPTO IDB-FVG tier remains forward-window-only by HARD broker ceiling (crypto H1 2024-07+),
  unchanged. Artifact: `KB6_IDB_METALS_REVAL_RESULT.json`.

---

## SUMMARY — caveat status after this track

| caveat (forward-only / short-window)        | deep data sourced              | status now |
|---------------------------------------------|--------------------------------|-----------|
| VP `EUidx_pocgrav` TRAIN = 2024 only        | GER40/UK100 M1 2023-04+        | **CLOSED — CONVERTS train-validated** (TRAIN +0.214R, all 4 yrs +, invert -0.41, null FWD z+2.0) |
| Sub-H4 leadlag index/AUDJPY M15 forward-only| GER40/UK100/US30/AUDJPY M15 2017-19+ | **CLOSED — 2 CONVERT** (GER40->UK100 TR+0.281/FWD+0.446; US30->USDJPY TR+0.026/FWD+0.283); rest revealed forward-only |
| IDB metals intraday FVG (WF-only positive)  | XAU/XAG H1 2014-01+ (11.4yr)   | **CLOSED — FALSIFIED as train edge** (TRAIN -0.036R, neg 2022/23/24) -> demote conf |
| IDB crypto intraday FVG forward-only        | none (crypto H1 2024-07 ceiling)| **STILL OPEN — hard broker ceiling** |
| Index/crypto M1 pre-2023                     | none (M1 clamps pre-2023)      | **STILL OPEN — hard broker ceiling** |

Net: **3 short-window/forward-only caveats CLOSE** (VP EU-POC converts to a real multi-year train
edge; 2 sub-H4 leadlag edges convert; IDB metals is honestly falsified as a train edge and demoted).
The remaining open items (crypto intraday, index M1 pre-2023) are HARD broker ceilings — a single
clamp bar is returned, so no deeper data exists to export; they can only unblock if the broker adds
history (re-probe periodically).

## Recommended book / scorecard updates (size-by-confidence, nothing deleted)
1. **VP `EUidx_pocgrav_2.0_vr1.2`: upgrade conf 0.30-0.40 -> ~0.50-0.55** — now multi-year-train-
   validated (2023+2024 both +), all 4 calendar years +, invert-opposite, null-cleared. Cap target at
   POC, stop 1.0 ATR (unchanged geometry). It is a cleaner index-class breadth source than the demoted
   `idxrev` fade (conf 0.15) and now carries a real train, not just a WF holdout.
2. **Sub-H4 leadlag: promote GER40->UK100 [london_open L2 z2 rev] and US30->USDJPY [ny_open L4 z2 mom]
   from forward-only to train-validated** (low-mid confidence ~0.30-0.35; session-gated, M15). Keep
   US30->GER40 / USDJPY->AUDJPY / US30->AUDJPY as forward-only BREADTH (conf ~0.15) with the explicit
   note that their multi-year train is flat/negative despite strong forward null-z — real mechanism,
   not stationary; do not size as cores.
3. **IDB `metals_intraday_fvg`: demote conf 0.30 -> ~0.10-0.15** (train-falsified on deep H1; keep as
   documented negative evidence / tiny forward-window breadth). IDB crypto unchanged (hard ceiling).
4. Mark crypto-intraday and pre-2023 index M1 as HARD source ceilings in the scorecard.

## Data now in repo (exact)
- `bridge_ftmo_m1_backfill_2023/` (14 M1 symbols, 2023; auto-unioned by `volume_profile.load_m1`)
- `bridge_ftmo_metals_h1_backfill_2014_2025/` (6 metals H1, 2014/2021-2025)
- `bridge_ftmo_idx_m15_backfill_2017_2025/` (GER40/UK100/US30/AUDJPY M15, 2017/2018/2019-2025)

## Scripts (track-prefixed) + result artifacts
- `KB6_revalidate_vp_euidx.py` -> `KB6_VP_EUIDX_REVAL_RESULT.json`
- `KB6_revalidate_leadlag_subh4.py` -> `KB6_LEADLAG_SUBH4_REVAL_RESULT.json`
- `KB6_revalidate_idb_metals.py` -> `KB6_IDB_METALS_REVAL_RESULT.json`
- `KB6_m1_2023_export.log`, `KB6_metals_h1_export.log`, `KB6_idx_m15_export.log` (export run logs)

## Next steps (for the loop)
1. Wire the conf upgrades into the portfolio build (VP EU-POC 0.50-0.55; leadlag GER40->UK100 +
   US30->USDJPY ~0.30-0.35) and re-run the diversification-aware challenge-pass MC + 1.5x left-tail
   stress on the VOL-MATCHED ablation (per doctrine, verdict any book change on stress pass-rate).
2. Apply the IDB metals demotion (0.10-0.15) and the leadlag forward-only demotions in the scorecard.
3. Re-probe the broker periodically for crypto pre-2024-07 H1 and index pre-2023 M1 (the only remaining
   unblock for those two hard ceilings).
4. Optionally export the remaining index M15 (SPX500/NAS100 from 2021) to give the NAS100<->SPX500
   sub-H4 momentum-spillover edges a deeper M15 train too (left for a follow-up; H4 already train-
   validated those in KB4).
