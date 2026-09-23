# K54 v2 — TIME / SESSION feature catalog

**Generated:** 2026-04-28T04:27:56.801302+00:00
**Module:** `research/ml_program/scripts/features/time_session.py`
**Stability source:** `_time_session_stability.json` (474 pre-Apr-2026 records: 345 F11 BOS hour-stamped + 129 trade-index DATE-only)
**Data cutoff:** ≤2026-04-28 23:59 UTC (Q1.2 hypothesis lock)

## Feature counts

- 2-KZ instruments (XAUUSD, GBPUSD, US30, US30_cash, NAS100, XAGUSD): **126** features.
- 3-KZ instruments (USDJPY, GBPJPY): **138** features (adds Tokyo KZ subfamily).
- Documented in DOCS: **138** (union; Tokyo subfamily only emits for 3-KZ symbols).

## Top-10 by stability |rho| (pre-Apr-2026 backfill)

| Rank | Feature | rho | n |
|---:|---|---:|---:|
| 1 | `t_kz_tokyo_abs_min_to_close` | +0.1923 | 105 |
| 2 | `t_kz_tokyo_signed_min_to_open` | -0.1913 | 105 |
| 3 | `t_kz_tokyo_signed_min_to_close` | -0.1913 | 105 |
| 4 | `t_kz_tokyo_abs_min_to_open` | +0.1913 | 105 |
| 5 | `t_kz_tokyo_min_to_next_open` | -0.1414 | 105 |
| 6 | `t_kz_tokyo_progress_pct` | -0.1345 | 105 |
| 7 | `t_kz_tokyo_active` | -0.1314 | 105 |
| 8 | `t_in_ny_pm_window` | +0.0952 | 474 |
| 9 | `t_kz_ny_first_15min` | -0.0919 | 474 |
| 10 | `t_kz_ny_first_30min` | -0.0919 | 474 |

**Note:** Tokyo KZ features rank highest but only on the n=105 USDJPY+GBPJPY subset. 
`t_in_ny_pm_window` and `t_is_first_m15_of_ny` are the strongest cross-instrument signals (n=474). 
Per Discipline ("don't drop based on stability") modeler keeps all features; this table is informational.

## Leakage self-check

All features in this family are computed from a *single timestamp* (the trade-entry candle close) 
and a *static calendar*. No future-window reads. Specific checks:

- **`t_kz_*_min_to_next_open` / `_close`**: positive distances to FUTURE events. The future event TIME 
  is calendar-known (KZ schedule is static config) — this is NOT a future-data peek; it's the same 
  category as "days until Christmas". OK.
- **`t_min_since_last_fill_*`**: caller responsibility. Module clamps and buckets, but DOES NOT compute 
  the underlying counter. Caller must ensure the supplied value reflects only fills that closed BEFORE 
  `ts` (the trade-entry candle). Documented in module docstring.
- **`t_bars_since_last_kz_open`**: same caller-responsibility note.
- **`t_session_transition_london_to_ny`**: window edges (london_end - 60, ny_start + 60) are static config. OK.
- **`t_is_last_3_trading_days_of_month`**: Mon-Fri counter to month-end. Pure calendar (no realized vol). OK.
- **`t_days_to_nearest_*` calendar features**: 100% calendar-derived. They CAN look forward in the calendar 
  ("days to NEXT NFP") which is fine — NFP date is statically known. OK.

**Sign convention review:** `t_kz_*_signed_min_to_open` is positive when the KZ open is 
LATER than `now` (future event), negative when already passed. `t_kz_*_signed_min_to_close` likewise. 
Track A trap explicitly avoided — counts past events as NEGATIVE, not as positive past-tense distances.

## Calendar source list

All calendars are STATIC — NO external feed, no news content, no sentiment.

| Calendar | Source | Confidence | Documented in |
|---|---|---|---|
| US federal holidays | Hard-coded fixed-rule list (New Year, MLK 3rd Mon Jan, Presidents 3rd Mon Feb, Good Friday via Meeus computus, Memorial last Mon May, Juneteenth Jun 19, July 4, Labor 1st Mon Sep, Thanksgiving 4th Thu Nov, Christmas Dec 25) | High; weekend-shifts NOT modeled | `time_session.py:_us_holidays_for` |
| Monthly OPEX | 3rd Friday of each month (US equity options) | High — fixed by CBOE rule | `time_session.py:_opex_third_friday` |
| Quarterly OPEX | 3rd Friday of Mar/Jun/Sep/Dec | High | `time_session.py:_quarterly_oexp_third_friday` |
| NFP release | 1st Friday of each month (BLS rule) | **Medium** — BLS shifts release for some months (e.g. holidays). Flagged as approximation. | `time_session.py:_nfp_first_friday` |
| CPI release | 2nd Wednesday of each month | **Low-Medium** — actual release floats Tue/Wed/Thu mid-month. Flagged ±2d fuzz. | `time_session.py:_cpi_release_date` |
| KZ schedule | CLAUDE.md "KILL ZONE SCHEDULE (UTC)" table; per-symbol overrides in `agent_config.yaml` (XAUUSD/XAGUSD NY end_utc=17:00, NAS100 special). | High | `time_session.py:KZ_SCHEDULE` |

**Approximation handling:** Features built from medium/low-confidence calendars (NFP/CPI) emit 
ONLY `days_to_*` quantitative features and never claim "NFP day = today" with high conviction. The 
modeler is expected to learn that ±2d windows around the formula are the meaningful zone, not ±0d.

## Subfamily index (count per subfamily)

| Subfamily | Feature count |
|---|---:|
| `cpi_proximity` | 4 |
| `day_of_month` | 1 |
| `day_of_month_cyc` | 2 |
| `day_of_week_aux` | 1 |
| `day_of_week_cyc` | 2 |
| `day_of_week_oh` | 7 |
| `holiday_proximity` | 5 |
| `hour_of_day_cyc` | 2 |
| `hour_of_day_oh` | 24 |
| `hour_of_week_cyc` | 2 |
| `kz_london_active` | 1 |
| `kz_london_meta` | 1 |
| `kz_london_phase` | 4 |
| `kz_london_pos` | 6 |
| `kz_ny_active` | 1 |
| `kz_ny_meta` | 1 |
| `kz_ny_phase` | 4 |
| `kz_ny_pos` | 6 |
| `kz_summary` | 2 |
| `kz_summary_oh` | 4 |
| `kz_tokyo_active` | 1 |
| `kz_tokyo_meta` | 1 |
| `kz_tokyo_phase` | 4 |
| `kz_tokyo_pos` | 6 |
| `minute_of_day_aux` | 1 |
| `minute_of_hour_aux` | 1 |
| `minute_of_hour_oh` | 4 |
| `month_of_year` | 1 |
| `month_of_year_cyc` | 2 |
| `month_phase` | 4 |
| `nfp_proximity` | 5 |
| `ny_split` | 3 |
| `opex_proximity` | 6 |
| `qopex_proximity` | 3 |
| `quarter_of_year` | 1 |
| `quarter_phase` | 1 |
| `session_transition` | 2 |
| `since_last_fill` | 7 |
| `since_last_kz` | 2 |
| `week_of_month` | 1 |
| `year_phase_cyc` | 2 |
| **TOTAL** | **138** |

## Per-feature documentation

Stability column: Spearman rank correlation between feature value and realized R, on pre-Apr-2026 
F11 BOS records (n=345, hour-stamped) UNIONED with trade-index records (n=129, DATE-only @ KZ-default 
hour). N is per-feature (Tokyo subfamily features only see USDJPY+GBPJPY, n=105). Empty cells = 
constant-in-backfill (e.g. minute-of-hour always = 0 in F11 hour-stamped data; live data will vary).

| Feature | Subfamily | dtype | rho | n | Description |
|---|---|---|---:|---:|---|
| `t_hour_00_oh` | hour_of_day_oh | binary | -0.0265 | 474 | 1.0 if UTC hour == 00 |
| `t_hour_01_oh` | hour_of_day_oh | binary | 0.0415 | 474 | 1.0 if UTC hour == 01 |
| `t_hour_02_oh` | hour_of_day_oh | binary | 0.0221 | 474 | 1.0 if UTC hour == 02 |
| `t_hour_03_oh` | hour_of_day_oh | binary | 0.0835 | 474 | 1.0 if UTC hour == 03 |
| `t_hour_04_oh` | hour_of_day_oh | binary | 0.0060 | 474 | 1.0 if UTC hour == 04 |
| `t_hour_05_oh` | hour_of_day_oh | binary | 0.0374 | 474 | 1.0 if UTC hour == 05 |
| `t_hour_06_oh` | hour_of_day_oh | binary | -0.0559 | 474 | 1.0 if UTC hour == 06 |
| `t_hour_07_oh` | hour_of_day_oh | binary | 0.0002 | 474 | 1.0 if UTC hour == 07 |
| `t_hour_08_oh` | hour_of_day_oh | binary | -0.0508 | 474 | 1.0 if UTC hour == 08 |
| `t_hour_09_oh` | hour_of_day_oh | binary | -0.0023 | 474 | 1.0 if UTC hour == 09 |
| `t_hour_10_oh` | hour_of_day_oh | binary | 0.0113 | 474 | 1.0 if UTC hour == 10 |
| `t_hour_11_oh` | hour_of_day_oh | binary | -0.0183 | 474 | 1.0 if UTC hour == 11 |
| `t_hour_12_oh` | hour_of_day_oh | binary | 0.0570 | 474 | 1.0 if UTC hour == 12 |
| `t_hour_13_oh` | hour_of_day_oh | binary | -0.0829 | 474 | 1.0 if UTC hour == 13 |
| `t_hour_14_oh` | hour_of_day_oh | binary | -0.0539 | 474 | 1.0 if UTC hour == 14 |
| `t_hour_15_oh` | hour_of_day_oh | binary | 0.0125 | 474 | 1.0 if UTC hour == 15 |
| `t_hour_16_oh` | hour_of_day_oh | binary | 0.0657 | 474 | 1.0 if UTC hour == 16 |
| `t_hour_17_oh` | hour_of_day_oh | binary | 0.0860 | 474 | 1.0 if UTC hour == 17 |
| `t_hour_18_oh` | hour_of_day_oh | binary | -0.0716 | 474 | 1.0 if UTC hour == 18 |
| `t_hour_19_oh` | hour_of_day_oh | binary | -0.0319 | 474 | 1.0 if UTC hour == 19 |
| `t_hour_20_oh` | hour_of_day_oh | binary | 0.0004 | 474 | 1.0 if UTC hour == 20 |
| `t_hour_21_oh` | hour_of_day_oh | binary | 0.0372 | 474 | 1.0 if UTC hour == 21 |
| `t_hour_22_oh` | hour_of_day_oh | binary | -0.0321 | 474 | 1.0 if UTC hour == 22 |
| `t_hour_23_oh` | hour_of_day_oh | binary | -0.0030 | 474 | 1.0 if UTC hour == 23 |
| `t_hour_sin` | hour_of_day_cyc | float | -0.0280 | 474 | sin(2π * hour / 24) |
| `t_hour_cos` | hour_of_day_cyc | float | 0.0491 | 474 | cos(2π * hour / 24) |
| `t_hour_of_week_sin` | hour_of_week_cyc | float | 0.0665 | 474 | sin(2π * (weekday*24+hour) / 168) |
| `t_hour_of_week_cos` | hour_of_week_cyc | float | 0.0714 | 474 | cos(2π * (weekday*24+hour) / 168) |
| `t_dow_0_oh` | day_of_week_oh | binary | -0.0004 | 474 | 1.0 if weekday == 0 (0=Mon) |
| `t_dow_1_oh` | day_of_week_oh | binary | 0.0437 | 474 | 1.0 if weekday == 1 (0=Mon) |
| `t_dow_2_oh` | day_of_week_oh | binary | 0.0635 | 474 | 1.0 if weekday == 2 (0=Mon) |
| `t_dow_3_oh` | day_of_week_oh | binary | -0.0791 | 474 | 1.0 if weekday == 3 (0=Mon) |
| `t_dow_4_oh` | day_of_week_oh | binary | -0.0290 | 474 | 1.0 if weekday == 4 (0=Mon) |
| `t_dow_5_oh` | day_of_week_oh | binary |  | 474 | 1.0 if weekday == 5 (0=Mon) |
| `t_dow_6_oh` | day_of_week_oh | binary |  | 474 | 1.0 if weekday == 6 (0=Mon) |
| `t_dow_sin` | day_of_week_cyc | float | 0.0662 | 474 | sin(2π * weekday / 7) |
| `t_dow_cos` | day_of_week_cyc | float | 0.0515 | 474 | cos(2π * weekday / 7) |
| `t_is_weekend` | day_of_week_aux | binary |  | 474 | 1.0 if weekday >= 5 (Sat/Sun) |
| `t_minute_bucket_0_oh` | minute_of_hour_oh | binary |  | 474 | 1.0 if minute // 15 == 0 |
| `t_minute_bucket_1_oh` | minute_of_hour_oh | binary |  | 474 | 1.0 if minute // 15 == 1 |
| `t_minute_bucket_2_oh` | minute_of_hour_oh | binary |  | 474 | 1.0 if minute // 15 == 2 |
| `t_minute_bucket_3_oh` | minute_of_hour_oh | binary |  | 474 | 1.0 if minute // 15 == 3 |
| `t_minute_of_hour` | minute_of_hour_aux | int |  | 474 | ts.minute (0-59) |
| `t_minute_of_day` | minute_of_day_aux | int | -0.0118 | 474 | hour*60 + minute (0-1439) |
| `t_day_of_month` | day_of_month | int | -0.0014 | 474 | 1-31 |
| `t_day_of_month_sin` | day_of_month_cyc | float | -0.0143 | 474 | sin(2π · day/31) |
| `t_day_of_month_cos` | day_of_month_cyc | float | -0.0501 | 474 | cos(2π · day/31) |
| `t_week_of_month` | week_of_month | int | 0.0123 | 474 | 1-5 ISO-style Mon-anchored |
| `t_month_of_year` | month_of_year | int | 0.0192 | 474 | 1-12 |
| `t_month_sin` | month_of_year_cyc | float | 0.0667 | 474 | sin(2π · month/12) |
| `t_month_cos` | month_of_year_cyc | float | -0.0243 | 474 | cos(2π · month/12) |
| `t_quarter_of_year` | quarter_of_year | int | -0.0313 | 474 | 1-4 from month |
| `t_is_first_week_of_month` | month_phase | binary | -0.0336 | 474 | 1.0 if day <= 7 |
| `t_is_last_3_trading_days_of_month` | month_phase | binary | -0.0684 | 474 | 1.0 if Mon-Fri days remaining in month < 3 |
| `t_is_last_5_trading_days_of_month` | month_phase | binary | -0.0387 | 474 | 1.0 if days remaining < 5 |
| `t_is_last_week_of_quarter` | quarter_phase | binary | 0.0197 | 474 | 1.0 if month in {3,6,9,12} AND day in last 7 of month |
| `t_trading_days_to_month_end` | month_phase | int | 0.0162 | 474 | Mon-Fri days from `d` to month-end (no holiday subtraction) |
| `t_kz_london_active` | kz_london_active | binary | -0.0588 | 474 | 1.0 if `now` falls inside the london KZ for this symbol |
| `t_kz_london_signed_min_to_open` | kz_london_pos | int | 0.0086 | 474 | Signed minutes from `now` to london KZ open today; +ve future, -ve past |
| `t_kz_london_signed_min_to_close` | kz_london_pos | int | 0.0304 | 474 | Signed minutes from `now` to london KZ close today; +ve future, -ve past |
| `t_kz_london_abs_min_to_open` | kz_london_pos | int | 0.0306 | 474 | abs of signed_min_to_open for london |
| `t_kz_london_abs_min_to_close` | kz_london_pos | int | 0.0517 | 474 | abs of signed_min_to_close for london |
| `t_kz_london_min_to_next_open` | kz_london_pos | int | -0.0384 | 474 | Minutes until NEXT london open; if open is past today, wraps to tomorrow's open via +1440 |
| `t_kz_london_min_to_next_close` | kz_london_pos | int | 0.0178 | 474 | Minutes until NEXT london close; wraps tomorrow if past today |
| `t_kz_london_window_len_min` | kz_london_meta | int | 0.0411 | 474 | Window length in minutes of london KZ for this symbol |
| `t_kz_london_first_15min` | kz_london_phase | binary | -0.0457 | 474 | 1.0 if currently inside london AND elapsed-since-open < 15min |
| `t_kz_london_first_30min` | kz_london_phase | binary | -0.0457 | 474 | 1.0 if inside london AND elapsed < 30min |
| `t_kz_london_last_15min` | kz_london_phase | binary |  | 474 | 1.0 if inside london AND remaining < 15min |
| `t_kz_london_progress_pct` | kz_london_phase | float | -0.0671 | 474 | elapsed_in_kz / window_len, sentinel -1 if not in KZ |
| `t_kz_ny_active` | kz_ny_active | binary | -0.0117 | 474 | 1.0 if `now` falls inside the ny KZ for this symbol |
| `t_kz_ny_signed_min_to_open` | kz_ny_pos | int | 0.0080 | 474 | Signed minutes from `now` to ny KZ open today; +ve future, -ve past |
| `t_kz_ny_signed_min_to_close` | kz_ny_pos | int | 0.0113 | 474 | Signed minutes from `now` to ny KZ close today; +ve future, -ve past |
| `t_kz_ny_abs_min_to_open` | kz_ny_pos | int | 0.0405 | 474 | abs of signed_min_to_open for ny |
| `t_kz_ny_abs_min_to_close` | kz_ny_pos | int | -0.0081 | 474 | abs of signed_min_to_close for ny |
| `t_kz_ny_min_to_next_open` | kz_ny_pos | int | 0.0070 | 474 | Minutes until NEXT ny open; if open is past today, wraps to tomorrow's open via +1440 |
| `t_kz_ny_min_to_next_close` | kz_ny_pos | int | -0.0215 | 474 | Minutes until NEXT ny close; wraps tomorrow if past today |
| `t_kz_ny_window_len_min` | kz_ny_meta | int | -0.0279 | 474 | Window length in minutes of ny KZ for this symbol |
| `t_kz_ny_first_15min` | kz_ny_phase | binary | -0.0919 | 474 | 1.0 if currently inside ny AND elapsed-since-open < 15min |
| `t_kz_ny_first_30min` | kz_ny_phase | binary | -0.0919 | 474 | 1.0 if inside ny AND elapsed < 30min |
| `t_kz_ny_last_15min` | kz_ny_phase | binary |  | 474 | 1.0 if inside ny AND remaining < 15min |
| `t_kz_ny_progress_pct` | kz_ny_phase | float | 0.0126 | 474 | elapsed_in_kz / window_len, sentinel -1 if not in KZ |
| `t_kz_tokyo_active` | kz_tokyo_active | binary | -0.1314 | 105 | 1.0 if `now` falls inside the tokyo KZ for this symbol |
| `t_kz_tokyo_signed_min_to_open` | kz_tokyo_pos | int | -0.1913 | 105 | Signed minutes from `now` to tokyo KZ open today; +ve future, -ve past |
| `t_kz_tokyo_signed_min_to_close` | kz_tokyo_pos | int | -0.1913 | 105 | Signed minutes from `now` to tokyo KZ close today; +ve future, -ve past |
| `t_kz_tokyo_abs_min_to_open` | kz_tokyo_pos | int | 0.1913 | 105 | abs of signed_min_to_open for tokyo |
| `t_kz_tokyo_abs_min_to_close` | kz_tokyo_pos | int | 0.1923 | 105 | abs of signed_min_to_close for tokyo |
| `t_kz_tokyo_min_to_next_open` | kz_tokyo_pos | int | -0.1414 | 105 | Minutes until NEXT tokyo open; if open is past today, wraps to tomorrow's open via +1440 |
| `t_kz_tokyo_min_to_next_close` | kz_tokyo_pos | int | 0.0295 | 105 | Minutes until NEXT tokyo close; wraps tomorrow if past today |
| `t_kz_tokyo_window_len_min` | kz_tokyo_meta | int |  | 105 | Window length in minutes of tokyo KZ for this symbol |
| `t_kz_tokyo_first_15min` | kz_tokyo_phase | binary | -0.0750 | 105 | 1.0 if currently inside tokyo AND elapsed-since-open < 15min |
| `t_kz_tokyo_first_30min` | kz_tokyo_phase | binary | -0.0750 | 105 | 1.0 if inside tokyo AND elapsed < 30min |
| `t_kz_tokyo_last_15min` | kz_tokyo_phase | binary |  | 105 | 1.0 if inside tokyo AND remaining < 15min |
| `t_kz_tokyo_progress_pct` | kz_tokyo_phase | float | -0.1345 | 105 | elapsed_in_kz / window_len, sentinel -1 if not in KZ |
| `t_kz_active_any` | kz_summary | binary | -0.0416 | 474 | 1.0 if ANY KZ active |
| `t_kz_active_count` | kz_summary | int | -0.0416 | 474 | Count of active KZs (overlap detection) |
| `t_kz_active_is_london` | kz_summary_oh | binary | -0.0588 | 474 | 1.0 if currently active KZ == london |
| `t_kz_active_is_ny` | kz_summary_oh | binary | -0.0117 | 474 | 1.0 if currently active KZ == ny |
| `t_kz_active_is_tokyo` | kz_summary_oh | binary | 0.0549 | 474 | 1.0 if currently active KZ == tokyo |
| `t_kz_active_is_none` | kz_summary_oh | binary | 0.0416 | 474 | 1.0 if outside any KZ |
| `t_session_transition_london_to_ny` | session_transition | binary | -0.0332 | 474 | 1.0 if `now` in [london_end - 60min, ny_start + 60min) — captures EU-close → NY-open handoff |
| `t_london_to_ny_gap_min` | session_transition | int | -0.0340 | 474 | Static minutes from London close to NY open (per symbol) |
| `t_in_ny_am_window` | ny_split | binary | -0.0853 | 474 | 1.0 if inside NY KZ AND in first half (AM half: ny_start to ny_midpoint) |
| `t_in_ny_pm_window` | ny_split | binary | 0.0952 | 474 | 1.0 if inside NY KZ AND in second half (PM) |
| `t_is_first_m15_of_ny` | ny_split | binary | -0.0919 | 474 | 1.0 if inside [ny_start, ny_start+15) — E.2 first-NY-candle reference |
| `t_min_since_last_fill_provided` | since_last_fill | binary |  | 474 | 1.0 if caller supplied a non-negative minutes_since_last_fill |
| `t_min_since_last_fill` | since_last_fill | int |  | 474 | Minutes since last realized trade fill on this instrument; -1 sentinel if missing |
| `t_min_since_last_fill_log` | since_last_fill | float |  | 474 | log1p(minutes_since_last_fill) |
| `t_min_since_last_fill_le_60` | since_last_fill | binary |  | 474 | 1.0 if le 60min (fresh fill) |
| `t_min_since_last_fill_le_240` | since_last_fill | binary |  | 474 | 1.0 if le 240min (4h) |
| `t_min_since_last_fill_le_1440` | since_last_fill | binary |  | 474 | 1.0 if le 1440min (24h) |
| `t_min_since_last_fill_le_4320` | since_last_fill | binary |  | 474 | 1.0 if le 4320min (3d) |
| `t_bars_since_last_kz_open_provided` | since_last_kz | binary |  | 474 | 1.0 if caller supplied a non-negative bars_since_last_kz_open |
| `t_bars_since_last_kz_open` | since_last_kz | int |  | 474 | M15 bars since most recent KZ open (any session); -1 sentinel if missing |
| `t_days_to_nearest_holiday_signed` | holiday_proximity | int | 0.0309 | 474 | Signed days to nearest US federal holiday across years {y-1, y, y+1} |
| `t_days_to_nearest_holiday_abs` | holiday_proximity | int | 0.0008 | 474 | abs of holiday_signed |
| `t_is_within_2d_of_holiday` | holiday_proximity | binary | -0.0016 | 474 | 1.0 if abs <=2 |
| `t_is_within_5d_of_holiday` | holiday_proximity | binary | -0.0190 | 474 | 1.0 if abs <=5 |
| `t_is_holiday_today` | holiday_proximity | binary | 0.0386 | 474 | 1.0 if signed == 0 |
| `t_days_to_nearest_opex_signed` | opex_proximity | int | 0.0569 | 474 | Signed days to nearest 3rd-Friday US-equity OPEX across {y-1,y,y+1} |
| `t_days_to_nearest_opex_abs` | opex_proximity | int | -0.0422 | 474 | abs |
| `t_is_within_2d_of_opex` | opex_proximity | binary | -0.0060 | 474 | 1.0 if abs <=2 |
| `t_is_within_5d_of_opex` | opex_proximity | binary | 0.0406 | 474 | 1.0 if abs <=5 |
| `t_is_opex_today` | opex_proximity | binary | -0.0061 | 474 | 1.0 if signed==0 |
| `t_is_index_x_opex_5d` | opex_proximity | binary | 0.0512 | 474 | 1.0 if symbol is index (US30/US30_cash/NAS100) AND within 5d of OPEX |
| `t_days_to_quarterly_opex_signed` | qopex_proximity | int | -0.0558 | 474 | Signed days to nearest QUARTERLY OPEX (Mar/Jun/Sep/Dec 3rd Friday) |
| `t_days_to_quarterly_opex_abs` | qopex_proximity | int | -0.0673 | 474 | abs |
| `t_is_within_5d_of_quarterly_opex` | qopex_proximity | binary | 0.0827 | 474 | 1.0 if abs <=5 |
| `t_days_to_nearest_nfp_signed` | nfp_proximity | int | 0.0005 | 474 | Signed days to nearest 1st-Friday-of-month (NFP release formula) |
| `t_days_to_nearest_nfp_abs` | nfp_proximity | int | 0.0361 | 474 | abs |
| `t_is_within_1d_of_nfp` | nfp_proximity | binary | -0.0751 | 474 | 1.0 if abs <=1 |
| `t_is_within_3d_of_nfp` | nfp_proximity | binary | -0.0224 | 474 | 1.0 if abs <=3 |
| `t_is_nfp_today` | nfp_proximity | binary | -0.0062 | 474 | 1.0 if signed==0 |
| `t_days_to_nearest_cpi_signed` | cpi_proximity | int | -0.0756 | 474 | Signed days to nearest 2nd-Wednesday-of-month (CPI release formula) |
| `t_days_to_nearest_cpi_abs` | cpi_proximity | int | -0.0042 | 474 | abs |
| `t_is_within_1d_of_cpi` | cpi_proximity | binary | -0.0008 | 474 | 1.0 if abs <=1 |
| `t_is_within_3d_of_cpi` | cpi_proximity | binary | -0.0319 | 474 | 1.0 if abs <=3 |
| `t_day_of_year_sin` | year_phase_cyc | float | 0.0763 | 474 | sin(2π · doy/366) |
| `t_day_of_year_cos` | year_phase_cyc | float | -0.0130 | 474 | cos(2π · doy/366) |

## Inference cost

All features are O(1) constant-time calendar / arithmetic computations. No I/O, no model calls, 
no rolling-window aggregations. Per-trade feature compute time on commodity laptop: <1ms.

## Provenance

- **Module:** `research/ml_program/scripts/features/time_session.py`
- **Stability driver:** `research/ml_program/scripts/features/_compute_stability.py`
- **Catalog emitter (this file):** `research/ml_program/scripts/features/_emit_catalog.py`
- **KZ schedule reference:** `CLAUDE.md` + `config/agent_config.yaml`
- **Outcome data (stability):** `research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl`, `knowledge_base/index/_trade_index.json`
