# PR #35 absorb — SHADOW only

**as_of:** 2026-09-20 ~14:07 ICT  
**PR:** https://github.com/Borr1/ai-trading-agent/pull/35  
**Agent:** bc-b44b47d7-0759-553b-88b5-7953a3208510  
**Branch:** `cursor/multiyear-xau-positive-v0-8510`  
**Title:** Multiyear XAU positive search V0 (train/hold)

## Chair facts
- Open PR · +3319/−0 · 12 files · tests 15 passed on agent VM
- Agent VM: Chair primary tape **absent** → scorecard `NOT_EVALUABLE` / `TRAIN_WINDOW_EMPTY` · `success_claimed: false` · fail-closed correct
- Old 2023/2024-split KEEP-book **+455 R superseded** — do not cite
- Affinity scope: **XAU spring / expanding style only** (no three_fresh, no metals_core, no US30/index bleed)
- Cost disclosure only — **cost never kill-gate**
- **Do not treat as APPLY** · never place · no NEWS invent · no src/ live path

## What ships (harness + docs)
- `scripts/research/multiyear_positive_v0.py` (`--bars` CLI)
- `scripts/research/xau_multiyear/` detectors / scorecard / stitch / walk
- `research/operations/xau_multiyear_positive_v0/MULTIYEAR_XAU_POSITIVE_V0_SCORECARD.{json,md}`
- Spring / expanding detectors only; Challenge KEEP untouched

## Chair box already ran the real tape
Primary `/workspace/audit-merge/markets/tapes/XAUUSD_M15.csv` (2014→2026) scored on-box:
- Artifact: `warroom_20260920/multiyear/MULTIYEAR_POSITIVE_V0.{md,json}`
- Spring primary HOLD sumR=**-56.93** → FAIL (1R/ATR harness)
- Expanding atrF1 HOLD +130 but TRAIN −203 → not multi-year consistent; expanding lane now **PARKED**

## Dig stance
Absorb as SHADOW research harness reference. Dig does not merge, arm APPLY, or place. Expanding WHY path stays PARKED; spring WHY autopsy continues on Chair PRIMARY blotter (`dsp_spring_close`).
