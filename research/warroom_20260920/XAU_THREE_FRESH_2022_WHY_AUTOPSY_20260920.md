# XAU Expanding 2022 WHY Autopsy — 2026-09-20

**Generated:** 2026-09-20 13:51 ICT (Asia/Bangkok)
**Mode:** SHADOW · research_only · `ready_for_key_fx: false` · `graduate_to_admit: false` · keyfx/fx: **paused**
**Owner LAW:** cost framing forbidden — this is idea/context WHY, not a cost-stress pack.

## 1. Plain-English idea

dsp_three_fresh_like = LONG after three consecutive fresh lower lows (>0.15 ATR), ≥2 down closes, volume not dead. Plain-English: buy the inventory flush / expanding liquidation when gold dumps hard on M15, expecting a hold-positive reclaim rather than a new trend short.

**Mechanism:** M15 expanding lower-lows reads as short-term liquidation. The LONG bet is that the flush *completes* and gold reclaims, rather than cascading into a new leg down.

**A-priori failure modes:** (1) cascade continues (H4 trend_down / vol_shock), (2) flush is mid-range noise, (3) event/vol shock runs structure stops.

## 2. Who decided / context trail (research park)

- Affinity scorecard (SHADOW) defined three_fresh-like a-priori from dig soft priors — not fit on hold years.
- Expanding harden pack froze session=ALL, atr_regime=atr_mid, horizon=32, expand_filter=ALL on train≤2020 only.
- Chair HOLD: research_only; ready_for_key_fx=false; no KEYFX; no admit.
- Owner LAW: cost is never the issue — this autopsy does not use cost-stress kill framing.
- 2022 is the fragile year of interest (lowest avg among recent positive years on frozen sleeve) → WHY autopsy.

**Explicitly not claimed:** Not an edge declaration; Not admit / place / host-mesh; Not KEYFX-ready; Not a cost-survivor graduation story

## 3. Freeze under study (locked)

| field | value |
|---|---|
| family | `dsp_three_fresh_like` |
| session | `ALL` |
| atr_regime | `atr_mid` |
| horizon_bars | `32` |
| expand_filter | `ALL` |
| M15 tape | `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` |
| H4 tape | `/workspace/instrument-edge/hydrate_deep_xau_20260920/XAUUSD_H4.csv` (~22y) |

## 4. 2022 losers vs winners (counts as evidence, not graduation)

Loser tag: `R_net_meas = R_raw − 0.05 < 0` (measurement label only).

| bucket | n | avg R_raw | sum R_raw | avg R_net_meas | sum R_net_meas |
|---|--:|----------:|----------:|---------------:|---------------:|
| 2022 all | 285 | 0.078165 | 22.2771 | 0.028165 | 8.0271 |
| losers (net<0) | 256 | -0.497496 | -127.3589 | -0.547496 | -140.1589 |
| winners (net≥0) | 29 | 5.159859 | 149.6359 | 5.109859 | 148.1859 |
| losers raw R<0 | 252 | -0.505764 | -127.4525 | — | — |

Sample for H4 jsonl: `{'sampled': True, 'n_all': 256, 'n_included': 80, 'n_large_all': 53, 'n_large_kept': 53, 'n_rest_sampled': 27, 'large_threshold_R_raw': -0.75, 'seed': 20260920, 'rule': 'all R_raw<=-0.75 + random sample of rest to cap 80'}`

## 5. H4 regime join — does it separate losers?

**Regime rules (deterministic):**
- `vol_shock`: ATR14 percentile vs trailing ~2y ≥ 0.90 (priority)
- `trend_up`: close > SMA50 > SMA200 AND SMA50 slope(20)>0
- `trend_down`: close < SMA50 < SMA200 AND SMA50 slope(20)<0
- `range`: else; flag `expanding_atr` if ATR ≥ 1.25× median(100)

**h4_helps:** **False**
- winner n=29 < 40 — loser-vs-winner share deltas are noisy; do not treat share separation as decisive
- share_delta trend_down: L=0.293 W=0.4138 delta=-0.1208 (n_los=75, n_win=12)
- loser avg_R_raw nearly flat across regimes (max |cell−all|=0.0278 < 0.10) — H4 tags do not explain loser severity

### 2022 loser vs winner regime mix

| regime | loser n | loser share | winner n | winner share | Δ (L−W) | avg R_raw losers |
|---|--:|----------:|--:|---:|--------:|---:|
| trend_down | 75 | 0.293 | 12 | 0.4138 | -0.1208 | -0.498534 |
| trend_up | 54 | 0.2109 | 4 | 0.1379 | 0.073 | -0.46973 |
| range | 123 | 0.4805 | 12 | 0.4138 | 0.0667 | -0.508814 |
| vol_shock | 4 | 0.0156 | 1 | 0.0345 | -0.0189 | -0.504826 |

### Top WHY clusters (losers by H4 regime)

| tag | n | share | avg R_raw |
|---|--:|------:|----------:|
| range | 123 | 0.4805 | -0.508814 |
| trend_down | 75 | 0.293 | -0.498534 |
| trend_up | 54 | 0.2109 | -0.46973 |
| vol_shock | 4 | 0.0156 | -0.504826 |

### With expanding_atr flag

| tag | n | share | avg R_raw |
|---|--:|------:|----------:|
| range | 118 | 0.4609 | -0.50866 |
| trend_down | 61 | 0.2383 | -0.519859 |
| trend_up | 41 | 0.1602 | -0.474322 |
| trend_down+expanding_atr | 14 | 0.0547 | -0.405616 |
| trend_up+expanding_atr | 13 | 0.0508 | -0.455246 |
| range+expanding_atr | 5 | 0.0195 | -0.512455 |
| vol_shock+expanding_atr | 4 | 0.0156 | -0.504826 |

### vs other years (all frozen trades)

| year | n | n_losers | avg R_raw | regime mix (share) |
|-----:|--:|---------:|----------:|---|
| 2021 | 234 | 197 | 0.282072 | trend_up=0.2009, trend_down=0.2137, range=0.5684, vol_shock=0.0171 |
| 2022 | 285 | 256 | 0.078165 | trend_up=0.2035, trend_down=0.3053, range=0.4737, vol_shock=0.0175 |
| 2023 | 228 | 206 | -0.026054 | trend_up=0.2939, trend_down=0.1667, range=0.5088, vol_shock=0.0307 |
| 2020 | 212 | 177 | 0.260485 | trend_up=0.1981, trend_down=0.0849, range=0.2972, vol_shock=0.4198 |
| 2024 | 239 | 213 | 0.179905 | trend_up=0.2845, trend_down=0.0669, range=0.3556, vol_shock=0.2929 |

## 6. Idea validity verdict

**idea_validity: `regime-conditional`**

- Within 2022, H4 does not cleanly separate losers from winners: loser mean R is flat across regimes (max severity gap 0.0278), and winner n=29 is too thin for reliable share contrasts. The one notable share delta (trend_down: winners over-index vs losers) runs opposite the naive 'cascade invalidates LONG flush' story.
- Year-level: 2022 all-trades richer in trend_down (0.3053 vs 2021 0.2137; 2023=0.1667). Idea may be mildly regime-sensitive at the year mix level, but 2023 has LESS trend_down and worse avg_R — so trend_down alone does not explain fragility. Soft regime-conditional, not invalidated.
- Do not graduate, admit, or start KEYFX from this autopsy. Research park only.

**Uncertainty:** H4 tags are coarse (4 buckets). Small n in some cells. No claim that fixing regime filters would improve the idea — that would be a new fit. 2022 path dependence (macro gold year) not fully captured by SMA/ATR tags.

## 7. Pack locks

```
research_only: true
ready_for_key_fx: false
graduate_to_admit: false
keyfx: paused
fx: paused
cost_framing: forbidden_by_owner_law
idea_validity: regime-conditional
h4_helps: false
```

## Artifacts

- `/workspace/instrument-edge/packs/XAU_EXPANDING_2022_WHY_AUTOPSY_20260920.json`
- `/workspace/instrument-edge/packs/XAU_EXPANDING_2022_WHY_AUTOPSY_20260920.md`
- `/workspace/instrument-edge/packs/XAU_EXPANDING_2022_LOSERS_H4JOIN_20260920.jsonl`
- repro: `/workspace/instrument-edge/packs/xau_expanding_2022_why_autopsy_20260920.py`

Repro: `python3 /workspace/instrument-edge/packs/xau_expanding_2022_why_autopsy_20260920.py`
