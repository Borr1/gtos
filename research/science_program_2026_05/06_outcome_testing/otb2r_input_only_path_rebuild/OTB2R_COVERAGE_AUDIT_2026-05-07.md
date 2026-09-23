# OTB2R Coverage Audit - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

Every included path window must be bound either to an explicit sanitized input-only path-order row whose coverage window reaches path_end_utc, or to a local M1/M5/M15/H1 OHLC file whose timestamp coverage spans path_start_utc through path_end_utc. Otherwise the row is blocked.

## Coverage Modes

| Mode | Rows |
| --- | --- |
| EXPLICIT_INPUT_ONLY_PATH_ORDER_ROW_COVERAGE_VALID | 86 |

## Records By Symbol

| Symbol | Rows |
| --- | --- |
| GBPJPY | 6 |
| NAS100 | 17 |
| US30_cash | 1 |
| USDJPY | 1 |
| XAGUSD | 54 |
| XAUUSD | 7 |

Blocked rows: `0`
