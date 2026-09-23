# Data Inventory Manifest
**Generated:** 2026-04-07  
**Owner:** Operations (Dorra)  
**Purpose:** Ground truth for all agents — do not work from assumptions, reference this first.

---

## 1. Historical Price Data (`data/historical/`)

| File | Rows | First Date | Last Date |
|------|------|-----------|----------|
| GBPJPY_D1.csv | 3,000 | 2014-09-10 | 2026-04-03 |
| GBPJPY_H1.csv | 20,000 | 2023-01-16 | 2026-04-03 |
| GBPJPY_H4.csv | 10,000 | 2019-10-30 | 2026-04-03 |
| GBPJPY_M15.csv | 99,999 | 2022-03-28 | 2026-04-03 |
| GBPUSD_D1.csv | 3,000 | 2014-09-09 | 2026-04-02 |
| GBPUSD_H1.csv | 20,000 | 2023-01-16 | 2026-04-03 |
| GBPUSD_H4.csv | 10,000 | 2019-10-30 | 2026-04-03 |
| GBPUSD_M15.csv | 50,000 | 2024-03-31 | 2026-04-03 |
| NZDUSD_D1.csv | 3,000 | 2014-09-10 | 2026-04-03 |
| NZDUSD_H1.csv | 20,000 | 2023-01-16 | 2026-04-03 |
| NZDUSD_H4.csv | 10,000 | 2019-10-30 | 2026-04-03 |
| NZDUSD_M15.csv | 99,999 | 2022-03-28 | 2026-04-03 |
| US30_cash_D1.csv | 1,828 | 2019-02-07 | 2026-04-02 |
| US30_cash_H1.csv | 20,000 | 2022-11-10 | 2026-04-03 |
| US30_cash_H4.csv | 10,000 | 2019-10-15 | 2026-04-03 |
| US30_cash_M15.csv | 99,999 | 2022-01-06 | 2026-04-03 |
| USDJPY_D1.csv | 3,000 | 2014-09-09 | 2026-04-02 |
| USDJPY_H1.csv | 20,000 | 2023-01-16 | 2026-04-03 |
| USDJPY_H4.csv | 10,000 | 2019-10-30 | 2026-04-03 |
| USDJPY_M15.csv | 50,000 | 2024-03-31 | 2026-04-03 |
| XAUUSD_D1.csv | 772 | 2023-04-03 | 2026-03-30 |
| XAUUSD_H1.csv | 14,716 | 2023-10-02 | 2026-03-30 |
| XAUUSD_H4.csv | 4,629 | 2023-03-31 | 2026-03-30 |
| XAUUSD_M1.csv | 99,999 | 2025-12-18 | 2026-04-02 |
| XAUUSD_M15.csv | 47,142 | 2024-04-01 | 2026-03-30 |
| XAUUSD_M5.csv | 99,999 | 2024-10-29 | 2026-04-02 |

**NOTE — XAUUSD gap:** `data/historical/XAUUSD_H1.csv` ends 2026-03-30. `data/XAUUSD_H1.csv` (main) has only 200 rows from 2026-03-23. Primary XAUUSD instrument has a thin recent data gap post-March 30.

---

## 2. Main `data/` Directory (recent/supplemental)

| File | Rows | First Date | Last Date |
|------|------|-----------|----------|
| DXY_D1.csv | 515 | 2024-02-29 | 2026-04-02 |
| EURUSD_D1.csv | 586 | 2024-01-02 | 2026-04-03 |
| EURUSD_H1.csv | 13,976 | 2024-01-02 | 2026-04-03 |
| EURUSD_H4.csv | 3,502 | 2024-01-02 | 2026-04-03 |
| EURUSD_M15.csv | 55,864 | 2024-01-02 | 2026-04-03 |
| EURUSD_M5.csv | 90,000 | 2025-01-16 | 2026-04-03 |
| GBPUSD_D1.csv | 3,000 | 2014-09-09 | 2026-04-02 |
| GBPUSD_H1.csv | 20,000 | 2023-01-16 | 2026-04-03 |
| GBPUSD_H4.csv | 10,000 | 2019-10-30 | 2026-04-03 |
| GBPUSD_M15.csv | 50,000 | 2024-03-31 | 2026-04-03 |
| GBPUSD_M5.csv | 300 | 2026-04-02 | 2026-04-03 |
| NAS100_D1.csv | 545 | 2024-01-02 | 2026-04-03 |
| NAS100_H1.csv | 12,348 | 2024-01-02 | 2026-04-03 |
| NAS100_H4.csv | 3,239 | 2024-01-02 | 2026-04-03 |
| NAS100_M15.csv | 49,215 | 2024-01-02 | 2026-04-02 |
| NAS100_M5.csv | 90,000 | 2024-10-24 | 2026-04-03 |
| XAGUSD_D1.csv | 583 | 2024-01-02 | 2026-04-02 |
| XAGUSD_H1.csv | 13,471 | 2024-01-02 | 2026-04-02 |
| XAGUSD_H4.csv | 3,495 | 2024-01-02 | 2026-04-02 |
| XAGUSD_M15.csv | 53,789 | 2024-01-02 | 2026-04-02 |
| XAGUSD_M5.csv | 90,000 | 2024-12-31 | 2026-04-02 |
| XAUUSD_D1.csv | 60 | 2026-01-09 | 2026-04-02 |
| XAUUSD_H1.csv | 200 | 2026-03-23 | 2026-04-02 |
| XAUUSD_H4.csv | 120 | 2026-03-06 | 2026-04-02 |
| XAUUSD_M15.csv | 700 | 2026-03-24 | 2026-04-02 |
| XAUUSD_M5.csv | 300 | 2026-04-01 | 2026-04-02 |
| economic_calendar.csv | 31 | 2026-04-01 | 2026-05-27 |

**Correlation/context pairs available:** EURUSD, DXY, XAGUSD, NAS100 — useful for institutional flow analysis.

---

## 3. Raw / Archive Data

| Dir | File | Rows | First Date | Last Date |
|-----|------|------|-----------|----------|
| data/raw/ | XAUUSD_D1.csv | 245 | 2024-07-01 | 2025-09-30 |
| data/raw/ | XAUUSD_H1.csv | 5,757 | 2024-07-01 | 2025-09-30 |
| data/raw/ | XAUUSD_H4.csv | 1,454 | 2024-07-01 | 2025-09-30 |
| data/raw/ | XAUUSD_M15.csv | 22,346 | 2024-07-01 | 2025-09-30 |
| data/old_hf_backup/ | XAUUSD_D1.csv | 245 | 2024-07-01 | 2025-09-30 |
| data/old_hf_backup/ | XAUUSD_H1.csv | 5,757 | 2024-07-01 | 2025-09-30 |
| data/old_hf_backup/ | XAUUSD_H4.csv | 1,454 | 2024-07-01 | 2025-09-30 |
| data/old_hf_backup/ | XAUUSD_M15.csv | 22,346 | 2024-07-01 | 2025-09-30 |

`raw/` and `old_hf_backup/` are identical — same rows, same date range. Both are superseded by `data/historical/`.

---

## 4. Live Session Data (`knowledge_base/`)

### 4a. Backtest Sessions (`knowledge_base/sessions/`)
- **Total files:** 436 JSON files
- **Coverage:**
  - GBPUSD: 201 session files (2024-01-25 → present)
  - US30_cash: 121 session files
  - USDJPY: 114 session files
- **MISSING:** No session files for XAUUSD, GBPJPY — these pairs have no backtest session history in the KB.

### 4b. Live Session Summaries (`knowledge_base/live_sessions/`)
- **Total files:** 9 JSON files, all dated 2026-04-06
- **Coverage:**
  - GBPJPY: Tokyo, London, NY sessions
  - GBPUSD: London, NY sessions
  - USDJPY: Tokyo, London, NY sessions
  - XAUUSD: London session only
- **MISSING:** XAUUSD Tokyo, XAUUSD NY; US30 all sessions for 2026-04-06

### 4c. Other KB Directories
| Directory | Files | Status |
|-----------|-------|--------|
| trades/ | 0 | EMPTY |
| live_evaluations/ | 0 | EMPTY |
| no_trades/ | 0 | EMPTY |
| postmortems/ | 0 | EMPTY |
| insights/ | 0 | EMPTY |
| journals/ | 0 | EMPTY |
| logs/ | 0 | EMPTY |

---

## 5. Analysis & Research Outputs

| File | Description |
|------|-------------|
| analysis/prescreen_kill_details.json | Prescreen filter audit |
| analysis/prescreen_killed_dates.csv | Killed trade dates |
| analysis/prescreen_loosening_report.md | Filter loosening analysis |
| decomposition_raw_results.json | Decomposition backtest raw |
| enhanced_inverted_analysis_results.json | Inverted TP/SL analysis |
| inverted_tp_sl_analysis_results.json | TP/SL inversion test |
| intra_candle_execution_results.json | Intra-candle execution test |
| exports/reasoning_text_mining_findings.json | Text mining research |
| exports/multi_instrument/screening_results/*.json | Multi-instrument screening (13 pairs) |
| exports/mt5_data_dump/hourly_volatility_profile.json | Hourly volatility by session |
| exports/mt5_data_dump/trade_entry_spreads.json | FTMO spread check |
| backtest.log | Main backtest log |
| batch_backtest.log | Batch backtest log |

---

## 6. Critical Gaps — Action Required

| Gap | Impact | Priority |
|-----|--------|----------|
| XAUUSD session KB empty (no sessions/ files) | Cannot do session-based analysis on primary instrument | HIGH |
| US30 live sessions missing 2026-04-06 | Live data incomplete for WF-1 start | HIGH |
| XAUUSD NY/Tokyo live sessions missing | Incomplete session coverage for Apr 6 | MEDIUM |
| trades/, live_evaluations/, postmortems/ all empty | No trade-level outcome data in KB | HIGH |
| XAUUSD historical ends 2026-03-30 (data/historical/) | 7-day gap in primary instrument | MEDIUM |

---

## Rules for All Agents
1. **All XAUUSD analysis must use `data/historical/XAUUSD_*.csv`** — the `data/XAUUSD_*.csv` files are thin (60-200 rows max).
2. **Session analysis (GBPUSD, US30, USDJPY) can use `knowledge_base/sessions/`** — 436 files available.
3. **Do not reference `data/raw/` or `data/old_hf_backup/`** — superseded and limited to 2025-09-30.
4. **Correlation instruments available:** DXY (daily), EURUSD (M5–D1), XAGUSD (M5–D1), NAS100 (M5–D1).
5. **No fabricated data.** If a file doesn't exist in this manifest, it does not exist.
