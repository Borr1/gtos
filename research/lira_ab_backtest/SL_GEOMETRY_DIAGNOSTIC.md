# LIRA SHORT-SL Geometry Diagnostic

Tests DP4 extension hypothesis: LIRA places XAUUSD SHORT SLs more correctly than V3 (which DP4 found misplaced 2/3 SHORTs in xauusd_s7 — one wrong-side, one tight-sweep).

## Coverage: LIRA=54 CANDs / A2=37 CANDs

- Both produced CAND at same (slice, candle, direction): 28
- LIRA-only CANDs: 26
- A2-only CANDs: 9

## Per-slice CAND coverage

| Slice | Common | LIRA-only | A2-only | LIRA SHORT (WIN) | A2 SHORT (WIN) |
|---|---:|---:|---:|---:|---:|
| usdjpy_s1 | 5 | 3 | 1 | 0 (0) | 0 (0) |
| usdjpy_s2 | 1 | 8 | 5 | 1 (0) | 0 (0) |
| usdjpy_s3 | 7 | 6 | 0 | 0 (0) | 0 (0) |
| usdjpy_s4 | 4 | 5 | 1 | 0 (0) | 0 (0) |
| xauusd_s2 | 1 | 0 | 0 | 0 (0) | 0 (0) |
| xauusd_s3 | 5 | 3 | 0 | 0 (0) | 0 (0) |
| xauusd_s5 | 2 | 0 | 1 | 0 (0) | 1 (0) |
| xauusd_s7 | 2 | 1 | 1 | 3 (2) | 3 (2) |
| xauusd_s8 | 1 | 0 | 0 | 0 (0) | 0 (0) |

## SL-placement divergence (common CANDs, |SL_lira - SL_a2| / entry > 0.5%)

| Slice | Time | Dir | Entry | SL_LIRA | SL_A2 | Delta | LIRA outcome | A2 outcome |
|---|---|---|---:|---:|---:|---:|---|---|
| xauusd_s3 | 2026-01-30T13:15:00Z | LONG | 4832.49000 | 4804.07000 | 4796.07000 | 8.00000 (0.17%) | LOSS | LOSS |
| usdjpy_s3 | 2026-03-02T07:00:00Z | LONG | 155.19000 | 154.90500 | 156.14500 | 1.24000 (0.80%) | UNFILLED | WIN |
| xauusd_s7 | 2026-03-27T07:00:00Z | SHORT | 4511.32000 | 4528.55000 | 4533.80000 | 5.25000 (0.12%) | WIN | WIN |
| usdjpy_s3 | 2026-02-26T00:15:00Z | LONG | 155.80000 | 155.51800 | 154.91700 | 0.60100 (0.39%) | WIN | UNFILLED |
| xauusd_s2 | 2026-01-27T07:00:00Z | LONG | 5078.62000 | 5061.22000 | 5052.65000 | 8.57000 (0.17%) | LOSS | LOSS |
| xauusd_s3 | 2026-02-03T08:00:00Z | LONG | 4824.97000 | 4799.00000 | 4779.52000 | 19.48000 (0.40%) | WIN | WIN |
| usdjpy_s2 | 2026-02-05T00:00:00Z | LONG | 156.74000 | 156.50800 | 156.30700 | 0.20100 (0.13%) | WIN | WIN |
| xauusd_s3 | 2026-01-30T08:00:00Z | LONG | 5094.12000 | 5069.27000 | 5056.33000 | 12.94000 (0.25%) | LOSS | WIN |
| xauusd_s3 | 2026-02-03T14:00:00Z | LONG | 4824.97000 | 4800.37000 | 4787.27000 | 13.10000 (0.27%) | WIN | WIN |

## Outcome divergence (same setup, different outcome)

| Slice | Time | Dir | LIRA outcome | LIRA R | A2 outcome | A2 R |
|---|---|---|---|---:|---|---:|
| usdjpy_s3 | 2026-03-02T07:00:00Z | LONG | UNFILLED | +0.00 | WIN | +1.50 |
| usdjpy_s3 | 2026-02-26T00:15:00Z | LONG | WIN | +1.50 | UNFILLED | +0.00 |
| xauusd_s3 | 2026-01-30T08:00:00Z | LONG | LOSS | -1.00 | WIN | +1.50 |

## XAUUSD SHORT detail (DP4 hypothesis target)

- LIRA XAUUSD SHORT CANDs: 3
- A2 XAUUSD SHORT CANDs: 4

### LIRA XAUUSD SHORTs

| Slice | Time | Entry | SL | TP1 | Outcome | R |
|---|---|---:|---:|---:|---|---:|
| xauusd_s7 | 2026-03-23T08:00:00Z | 4349.89 | 4396.61 | 4279.73 | WIN | +1.50 |
| xauusd_s7 | 2026-03-25T07:00:00Z | 4984.70 | 4995.82 | 4968.03 | UNFILLED | +0.00 |
| xauusd_s7 | 2026-03-27T07:00:00Z | 4511.32 | 4528.55 | 4485.47 | WIN | +1.50 |

### A2 XAUUSD SHORTs (V3 baseline)

| Slice | Time | Entry | SL | TP1 | Outcome | R |
|---|---|---:|---:|---:|---|---:|
| xauusd_s5 | 2026-03-03T13:15:00Z | 5305.78 | 5343.82 | 5248.63 | UNFILLED | +0.00 |
| xauusd_s7 | 2026-03-23T08:00:00Z | 4349.89 | 4397.43 | 4278.55 | WIN | +1.50 |
| xauusd_s7 | 2026-03-25T07:15:00Z | 4984.70 | 5006.82 | 4951.52 | UNFILLED | +0.00 |
| xauusd_s7 | 2026-03-27T07:00:00Z | 4524.05 | 4533.80 | 4509.43 | WIN | +1.50 |
