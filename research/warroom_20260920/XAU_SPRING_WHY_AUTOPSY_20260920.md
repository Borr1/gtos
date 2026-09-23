# XAU Spring (dsp_spring_close) WHY Autopsy — 2026-09-20

**Generated:** 2026-09-20 ~14:07 ICT (Asia/Bangkok)  
**Mode:** SHADOW · research_only · `place: false` · `ready_for_key_fx: false` · `graduate_to_admit: false`  
**Lane:** PRIMARY multiyear spring — **NOT expanding** (expanding harden/V3 PARKED)  
**Owner LAW:** cost never kill-gate · instrument×sleeve affinity · no NEWS invent · no APPLY

## 1. Plain-English idea

`dsp_spring_close` = LONG after M15 spring: price sweeps a prior swing low then closes back above it (failed breakdown / completed inventory flush). Next-open entry bets reclaim continuation.

**Mechanism:** Sweep-then-reclaim traps breakdown shorts; the LONG is that the flush *finished*.

**A-priori failure modes:** (1) cascade continues (true breakdown), (2) mid-range noise / stop-hunt reverse, (3) vol_shock runs structure stop, (4) bear-trap years where springs fail systematically.

## 2. Tape / freeze

| field | value |
|---|---|
| sleeve | `dsp_spring_close` |
| symbol | `XAUUSD` |
| M15 PRIMARY | `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` |
| blotter | `multiyear/blotter_PRIMARY_XAUUSD_dsp_spring_close.jsonl` (n=4420) |
| fill_model | geometry_proxy_ohlc_touch_no_broker_fill |
| H4 join | `/workspace/instrument-edge/hydrate_deep_xau_20260920/XAUUSD_H4.csv` |
| expanding | PARKED — not resumed |

## 3. Headline numbers (PRIMARY blotter)

| split | n | WR | sumR | avgR |
|---|--:|---:|-----:|-----:|
| **overall** | 4420 | 0.292 | **+79.35** | +0.0180 |
| train ≤2021 | 2693 | 0.293 | +24.90 | +0.0092 |
| **hold ≥2022** | 1727 | 0.291 | **+54.44** | +0.0315 |

Exits all: `orig_stop` 3050 · `orig_tp` 920 · `time_stop` 450  
Losers ~97.5% are `orig_stop` at −1R; winners ~71% `orig_tp` at +3R (asymmetric book — idea validity is year/regime, not cost).

**Cross-ref V0 1R harness** (`MULTIYEAR_POSITIVE_V0`): spring HOLD sumR=**−56.93** / TRAIN −147 → FAIL under 1R/ATR filter. Different R model; both agree **not promote-ready**.

## 4. Year table (fragile = avgR ≤ 0)

| year | n | WR | avgR | sumR | fragile |
|-----:|--:|---:|-----:|-----:|:-------:|
| 2014 | 300 | 0.273 | −0.121 | −36.39 | Y |
| 2015 | 342 | 0.310 | +0.009 | +3.15 | |
| 2016 | 324 | 0.290 | −0.009 | −2.81 | Y |
| 2017 | 299 | 0.308 | +0.131 | +39.07 | |
| 2018 | 360 | 0.278 | −0.032 | −11.40 | Y |
| 2019 | 328 | 0.287 | −0.007 | −2.35 | Y |
| 2020 | 329 | 0.328 | +0.142 | +46.70 | |
| **2021** | 411 | 0.275 | −0.027 | **−11.06** | Y |
| **2022** | 430 | 0.256 | −0.061 | **−26.25** | Y |
| 2023 | 409 | 0.318 | +0.161 | +65.76 | |
| 2024 | 358 | 0.299 | +0.037 | +13.35 | |
| 2025 | 360 | 0.306 | +0.067 | +24.12 | |
| **2026** | 170 | 0.265 | −0.133 | **−22.54** | Y |

Fragile years: **2014, 2016, 2018, 2019, 2021, 2022, 2026**  
Worst by sumR: 2014 (−36.4) · 2022 (−26.3) · 2026 (−22.5) · 2018 (−11.4) · 2021 (−11.1)  
Best: 2023 (+65.8) · 2020 (+46.7) · 2017 (+39.1) · 2025 (+24.1)

Hold is net positive (+54.4) **despite** 2022 and 2026 fragility — winners in 2023–2025 carry the book. Idea is **not** multi-year-stable year-by-year.

## 5. WHY on fragile hold / loser years

### Exit structure (idea validity)
- Losers dominated by **orig_stop** (2021: 96.6% of losers; 2022: 98.1%) — springs that fail reverse through the reclaim low.
- Winners need **orig_tp (+3R)** or positive time_stop; low WR (~29%) means the book survives only when winners are large.
- This is **structure-stop failure**, not a cost story.

### 2021 (affinity-known fragile)
- n=411 · sumR=−11.06 · losers n=298
- Loser sessions: NY 118 / London 90 / Asia 73 / Off 17 — **NY heaviest count**, not a single-session kill
- H4 join: **h4_helps=false** (share deltas all |Δ|<0.04; loser avgR flat across regimes)

### 2022 (worst hold year)
- n=430 · sumR=−26.25 · WR 0.256 (lowest recent) · losers n=320
- Loser sessions: NY 128 / Asia 89 / London 78 / Off 25
- H4 join: **h4_helps=false** (largest Δ trend_up losers +0.069 — not decisive; loser severity flat ~−0.98R across regimes)

### 2026 (partial year, fragile)
- n=170 · sumR=−22.54 · avgR=−0.133 — treat as incomplete + caution, not a kill alone

**WHY cluster (research):** Fragile years fail because **reclaim is a trap** (stop-out rate ↑, WR ↓); H4 trend/vol tags do **not** cleanly separate losers from winners on 2021/2022. No promote-ready pre-entry H4 gate from this join.

## 6. Affinity stance (research stamp)

| field | value |
|---|---|
| instrument×sleeve | `XAUUSD` × `dsp_spring_close` |
| affinity | **KEEP_RESEARCH** |
| ready_for_key_fx | **false** |
| place | **false** |
| note | Hold net + on PRIMARY managed blotter, but year fragility (esp. 2022/2026) + V0 1R FAIL → deepen WHY, do not promote. Cost never kill-gate. |

Does **not** flip affinity to KILL — sleeve paid in strong years (2020/2023/2025); affinity law keeps the pairing for research, questions promote not existence.

## 7. Verdict

- Spring PRIMARY blotter: overall/hold **sumR > 0**, but **fragile years real** → idea validity incomplete.
- V0 1R harness: spring HOLD **FAIL**.
- H4 regime join on 2021/2022 losers: **does not help**.
- Expanding remains **PARKED**.
- **Monday-ready: NO** · APPLY unset · no place · no NEWS invent.

## Artifacts
- `XAU_SPRING_WHY_AUTOPSY_20260920.json` (full tables + H4 join)
- Blotter: `multiyear/blotter_PRIMARY_XAUUSD_dsp_spring_close.jsonl`
- Cross: `multiyear/MULTIYEAR_POSITIVE_V0.*` · affinity scorecard · `PR35_SHADOW_ABSORB.md`

Numbers from on-box PRIMARY blotter. Never fabricated. place=false.
