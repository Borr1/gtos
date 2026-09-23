# Phase 3: MFE Time-Profile — 2026-04-04 10:19

## 3A: MFE Time-Profile
- Trades analyzed: 105 (64W / 41L)
- Peak MFE candle (winners): candle 12
- MFE at candle 4 (1hr): Winners=0.7263, Losers=0.2999

### Average MFE/MAE Profile (R-multiples)
| Candle | Winner MFE | Winner MAE | Loser MFE | Loser MAE |
|--------|-----------|-----------|----------|----------|
| 1 | 0.4116 | 0.3541 | 0.2144 | 0.4795 |
| 2 | 0.5514 | 0.5202 | 0.2821 | 0.774 |
| 3 | 0.6729 | 0.6407 | 0.2942 | 0.9555 |
| 4 | 0.7263 | 0.7843 | 0.2999 | 1.1105 |
| 5 | 0.7842 | 0.8301 | 0.3512 | 1.1997 |
| 6 | 0.9356 | 0.9432 | 0.3958 | 1.3559 |
| 7 | 0.9877 | 1.1321 | 0.435 | 1.8144 |
| 8 | 1.0735 | 1.3204 | 0.5182 | 2.2509 |
| 9 | 1.1626 | 1.4382 | 0.5378 | 2.4653 |
| 10 | 1.2315 | 1.8366 | 0.5421 | 2.8372 |
| 11 | 1.342 | 1.8957 | 0.5566 | 2.8507 |
| 12 | 1.4192 | 2.0375 | 0.5989 | 2.928 |

### BE Stop Optimization
| Trigger | Trades Hit | Winners Stopped | Losers Saved | Net R/Trade |
|---------|-----------|----------------|-------------|------------|
| 0.5R | 52 | 19 | 11 | -0.1952 |
| 0.75R | 41 | 11 | 6 | -0.1206 |
| 1.0R | 33 | 10 | 4 | -0.1349 |
| 1.25R | 25 | 5 | 2 | -0.1168 |
| 1.5R | 22 | 4 | 2 | -0.1111 |

## 3C: Feature Redundancy (Lasso)
- n=None, features=None
- CV accuracy (5-fold): None
- ⚠️ CV accuracy < 55%: model is noise

## 3D: Regime Analysis
- range_normal: n=72, WR=62.5%, mean_R=0.1521
- range_wide: n=33, WR=57.6%, mean_R=0.3173
- trend_ranging: n=18, WR=44.4%, mean_R=-0.0339
- trend_trending: n=87, WR=64.4%, mean_R=0.2532
- volatility_high_vol: n=85, WR=60.0%, mean_R=0.1754
- volatility_low_vol: n=20, WR=65.0%, mean_R=0.3255
