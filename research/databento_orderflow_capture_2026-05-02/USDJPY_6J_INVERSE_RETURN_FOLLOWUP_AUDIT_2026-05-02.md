# USDJPY 6J Inverse-Return Follow-Up Audit

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Registration verdict: `NO_PROXY_MAP_ACTIVATION`

## Synthesis

The expanded 6J/USDJPY inverse-return follow-up is strongly supportive but still not a strict proxy-map activation. Eight of nine windows clear the 0.85 correlation floor and all windows clear directional agreement, but 2026-04-27 remains below the strict floor.

## Decision Readout

- Status: `REVIEW_REMAINS_OPEN_SINGLE_WEAK_WINDOW`
- Windows: 9
- Correlation pass count/rate: 8 / 0.888889
- Min zero-lag corr: 0.825301
- Min directional agreement: 0.928977
- All best lag zero: True
- Timestamp policy all passed: True
- Weak windows: ['2026-04-27T07:00_2026-04-27T16:59']
- Estimated Databento cost USD: $0.260652

## Window Audit

| Window | Shift | Expected shift | Corr | Directional | Best lag | Corr pass |
|---|---:|---:|---:|---:|---:|---:|
| 2026-04-23T07:00_2026-04-23T16:59 | -180 | -180 | 0.856882 | 0.928977 | 0 | True |
| 2026-04-24T07:00_2026-04-24T16:59 | -180 | -180 | 0.903693 | 0.963173 | 0 | True |
| 2026-04-27T07:00_2026-04-27T16:59 | -180 | -180 | 0.825301 | 0.936232 | 0 | False |
| 2026-01-22T07:00_2026-01-22T16:59 | -120 | -120 | 0.889929 | 0.938424 | 0 | True |
| 2026-02-12T07:00_2026-02-12T16:59 | -120 | -120 | 0.966368 | 0.969512 | 0 | True |
| 2026-03-06T07:00_2026-03-06T16:59 | -120 | -120 | 0.962777 | 0.972540 | 0 | True |
| 2026-03-09T07:00_2026-03-09T16:59 | -180 | -180 | 0.940532 | 0.962882 | 0 | True |
| 2026-03-16T07:00_2026-03-16T16:59 | -180 | -180 | 0.904779 | 0.962353 | 0 | True |
| 2026-04-02T07:00_2026-04-02T16:59 | -180 | -180 | 0.906600 | 0.955381 | 0 | True |

## Answered Questions

- 6J/USDJPY inverse-return alignment is directionally stable across the tested dates.
- The date-aware -120/-180 MT5 timestamp policy is supported by all tested 6J windows.
- The original weak 2026-04-27 window did not disappear under a larger sample.
- USDJPY should remain outside the research orderflow proxy map unless a stricter future audit passes or a new pre-registered robust gate is adopted.

## Ambiguity Ledger

- This is price-transfer validation only, not an orderflow alpha test.
- One weak window blocks strict activation even though the broader sample is supportive.
- Continuous futures roll behavior is sampled but not fully proven for all future dates.
- M1 return alignment does not prove tick-level or broker-fill equivalence.

## Opened Questions

1. Was 2026-04-27 weak because of broker CFD conditions, futures roll/basis behavior, or local MT5 data quality?
2. Should a future USDJPY proxy gate require all windows above 0.85 or allow a robust pass-rate rule registered before label use?
3. Can USDJPY orderflow features be useful diagnostically even before proxy-map activation?

## Next Steps

1. Keep USDJPY out of FUTURES_PROXY_MAP for now.
2. If USDJPY becomes important, register a robust transfer-gate protocol before any more label-aware feature analysis.
3. Do not use 6J depth/heatmap semantics for USDJPY until price-transfer activation is explicitly passed.
