# MULTIYEAR POSITIVE PLAN — 2026-09-20

**Owner ask:** make system POSITIVE on **2–4 YEARS** of data — not n=60 Challenge week.
**Affinity law:** instrument×sleeve not portable by default. **place=false. CF PAUSED.** No NEWS invent.
**ts_ict:** 2026-09-20 13:43 ICT

---

## 1) Data needed

| Role | Path | Span | Notes |
|------|------|------|-------|
| **PRIMARY** | `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` | 2014-01-02 → 2026-06-17 (~12.45y, n≈293197) | Chair LOCK — expectancy source |
| PRIMARY FX companion | `/workspace/audit-merge/markets/tapes/EURUSD_M15.csv` | 2014-01-01 → 2026-06-17 | Available; not in today's XAU KEEP run |
| SECONDARY only | `research/warroom_20260920/multiyear/XAUUSD_M15_stitched_2022_2026.csv` | 2022-01 → 2026-04 | Swarm stitch — demoted |
| ABORT as expectancy | Challenge ~1mo hydrate / peer_multi ~1mo | ~weeks | Do not use for multiyear EV |

**Gaps:** EURGBP multiyear M15 missing on PRIMARY (blocks vss_fxcross today); geometry proxy ≠ live book fills; spread/slippage not modeled.

## 2) First pairings from Challenge affinity

| Rank | Pairing | Challenge | Why first | Today |
|------|---------|-----------|-----------|-------|
| 1 | XAUUSD×dsp_spring_close | n=1 sumR=+3.02 WR=1.0 KEEP | Non-toxic spring; KEEP win | **HOLD sumR PASS** |
| 2 | XAUUSD×dsp_expanding_up_staircase | n=1 sumR=+2.99 WR=1.0 KEEP | Expanding +EV; not toxic fold | **HOLD sumR PASS** |
| 3 | XAUUSD×dsp_three_fresh LONG win-path | n=2 sumR=+2.4 WR=0.5 | Subtype only — NOT three_bar fade shorts | **HOLD sumR PASS** (WR<40% monitor) |
| 4 | EURGBP×vss_fxcross_london | KEEP FX win | Family +EV on FX | **BLOCKED** (no multiyear EURGBP PRIMARY) |
| 5 | GBPJPY×sub_mid_dn_re | KEEP FX +2.96 | FX-only (XAU sub_mid was −EV) | NEXT |

**NEVER first:** INDEX×bleed, FX×xa_huge, XAU×three_bar fade shorts / walked_hi toxic / bleed.

## 3) Train / hold year split

| Split | Rule | On PRIMARY |
|-------|------|------------|
| TRAIN | ≤ 2021-12-31 | 2014–2021 (~8y) |
| HOLD | ≥ 2022-01-01 | 2022–2026-06 (~4.5y) |

**Justify:** Owner wants multi-year positivity. Long train before COVID/post-COVID regime; hold covers 2022–2026 including Challenge era as OOS — Challenge week is **not** the train set. Prior ≤2023/≥2024 short-stitch split demoted under Chair LOCK.

## 4) Success criteria

- **Owner gate (today):** HOLD `sumR > 0`
- **Proposed WR floor:** ≥ 40% (from KEEP tape: spring/expanding WR=1.0; three_fresh WR=0.5)
- Report both; do not hide WR when sumR passes.

## 5) Replay harness that exists

| Harness | Path | Role |
|---------|------|------|
| hist_prove S14/S15/S16 | `research/warroom_20260920/hist_prove_1008/` | Gate/prove (not sleeve EV) |
| ultimate_book sleeves | `_swarm_land_tip/extract/src/components/ultimate_book/sleeves/` | Live generators (not wired today) |
| learning_scoreboard | `close_loop/war_room_20260920/learning_scoreboard_60.jsonl` | Challenge affinity source |
| **Used today** | inline geometry-proxy on PRIMARY OHLC | structure stop + 3R TP or 32-bar time_stop MTM |

Fill honesty: **NOT** broker/book fills.

## 6) What can run TODAY vs blocked

### Ran today (PRIMARY tape)

| Pairing | TRAIN | HOLD | Owner gate |
|---------|-------|------|------------|
| `XAUUSD|dsp_spring_close` | n=2693 sumR=+24.90 WR=0.293 | n=1727 sumR=+54.44 WR=0.2907 | PASS |
| `XAUUSD|dsp_expanding_up_staircase` | n=2482 sumR=+25.56 WR=0.3626 | n=1454 sumR=+102.67 WR=0.3872 | PASS |
| `XAUUSD|dsp_three_fresh` | n=4295 sumR=-33.38 WR=0.3362 | n=2494 sumR=+155.51 WR=0.3545 | PASS |
| `XAUUSD|NEGCTRL_dsp_three_bar_fade_short` (NEGCTRL) | n=4317 sumR=+39.67 WR=0.3333 | n=2467 sumR=-192.92 WR=0.3085 | FAIL (expected) |

**Summary:** 3/3 primary KEEP candidates **PASS** HOLD sumR>0 on ~4.5y hold. Negctrl three_bar fade SHORT **FAILS** hold (sumR≈−193) — affinity toxic lesson holds.

### Blocked today

- EURGBP×vss_fxcross multiyear (no PRIMARY EURGBP M15)
- Live sleeve-generator parity / cost-true fills
- CF variants (PAUSED); place (false)

## Artifacts

- Plan MD: `close_loop/war_room_20260920/MULTIYEAR_POSITIVE_PLAN_20260920.md`
- Plan JSON: `close_loop/war_room_20260920/MULTIYEAR_POSITIVE_PLAN_20260920.json`
- Replay: `close_loop/war_room_20260920/MULTIYEAR_POSITIVE_REPLAY_XAU_PRIMARY_2014_2026_20260920.json`
- Join: `research/warroom_20260920/multiyear/`
- Affinity (unchanged): `INSTRUMENT_SLEEVE_AFFINITY_20260920.json`

## Affinity law honored

- Pairings taken from AFFINITY KEEP/positive cells only
- Toxic ports excluded from first candidates; fade-short run only as labeled NEGCTRL
- three_fresh = LONG win-path subtype, not family religion cage / not fade export
- No new CF variants; no place; no NEWS invent
