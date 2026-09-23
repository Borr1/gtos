# Historical OHLC GTOS Replay Branch System Transfer No-Fill Avoid/Retest Join

Generated UTC: `2026-05-16T15:17:01Z`

Branch system-transfer confirmed no-fill avoid/retest join packet only. It preserves every 1,984 avoid-filter branch row and every 6,112 retest-redesign/source-confidence row by joining them back to the 386 branch system-transfer denominator on route, target/stop contract, and entry variant. It computes lower-level fillability/no-fill pressure and implementation implications, but does not change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Branch summary rows: `386`
- Avoid join rows: `1984`
- Retest-redesign join rows: `6112`
- Source-confidence join rows: `6112`
- Branches with avoid+retest context: `144`
- Branches with retest-only context: `32`
- Branches without direct no-fill context: `210`
