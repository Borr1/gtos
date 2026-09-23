# FREQTRADE PAIRLIST — LICENSE_REVIEW only

**as_of:** 2026-09-20T19:00:14+07:00 (ICT+7)  
**steal:** `STEAL-FREQTRADE-PAIRLIST-RANK`  
**repo:** https://github.com/freqtrade/freqtrade  
**license:** **GPL-3.0** → `LICENSE_REVIEW`  
**absorb_code:** **false**  
**place:** false  
**schema twin:** `FREQTRADE_PAIRLIST_LICENSE_REVIEW_20260920.json`  
**CL copies:** `…/FREQTRADE_PAIRLIST_LICENSE_REVIEW_DIG_20260920.{md,json}`

## Hard rule
- Do **NOT** absorb freqtrade code into GTOS / Challenge live.
- Dig does **not** vendor the GPL tree.
- Chair must **not** copy pairlist plugin source into Challenge live.

## Pattern note (idea only — OK)
Handlers → alive-universe **Score ranker** idea:
- `VolumePairList` — rank by quote volume
- `PerformanceFilter` — rank/filter by recent trade performance
- `CrossMarketPairList` — presence across markets

Map (existing wire names only):
- **Choice** → `PR29-ALIVE-MENU` (rebuild alive inventory)
- **Score** → `CL-JEV-SESSION` (session fitness × pair liquidity rank)

Affinity: `crypto|*_session_sleeve` — per cell. Clean-room reimplement under MIT-clean GTOS only after Chair LICENSE_REVIEW pass.

## Dig idle
`absorb_code:false` confirmed. Pattern note only. No place. No live_armed_set edit.
