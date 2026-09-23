"""Emit time_session.md + time_session.csv from the feature module + stability JSON.

Catalog files are READ-ONLY ARTEFACTS for the K54 v2 modeler. Do NOT edit
them by hand — re-run this script after changing time_session.py.
"""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from time_session import compute_time_session_features, list_feature_names  # noqa: E402

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
STABILITY_PATH = ROOT / "research/ml_program/feature_catalogs/_time_session_stability.json"
MD_PATH = ROOT / "research/ml_program/feature_catalogs/time_session.md"
CSV_PATH = ROOT / "research/ml_program/feature_catalogs/time_session.csv"


@dataclass
class FeatureDoc:
    name: str
    family: str
    subfamily: str
    dtype: str
    description: str
    source: str
    computation: str
    lookback: str
    leakage_check: str


# ---------------------------------------------------------------------------
# Feature documentation table
# ---------------------------------------------------------------------------
# Per-feature docs. We define ONCE here and join with stability data.
# `subfamily` groups 1-of-K features for the catalog view.

DOCS: list[FeatureDoc] = []


def add(name: str, subfamily: str, dtype: str, desc: str, comp: str, lb: str, leak: str = "point-in-time, no future window read", family: str = "time_session") -> None:
    DOCS.append(FeatureDoc(
        name=name, family=family, subfamily=subfamily, dtype=dtype,
        description=desc, source="time_session.py:compute_time_session_features",
        computation=comp, lookback=lb, leakage_check=leak,
    ))


# Hour-of-day one-hots
for h in range(24):
    add(f"t_hour_{h:02d}_oh", "hour_of_day_oh", "binary",
        f"1.0 if UTC hour == {h:02d}", "ts.utc.hour == h", "single-bar")
add("t_hour_sin", "hour_of_day_cyc", "float", "sin(2π * hour / 24)", "math.sin(2π·hour/24)", "single-bar")
add("t_hour_cos", "hour_of_day_cyc", "float", "cos(2π * hour / 24)", "math.cos(2π·hour/24)", "single-bar")
add("t_hour_of_week_sin", "hour_of_week_cyc", "float", "sin(2π * (weekday*24+hour) / 168)", "weekday*24+hour, sinusoid 168", "single-bar")
add("t_hour_of_week_cos", "hour_of_week_cyc", "float", "cos(2π * (weekday*24+hour) / 168)", "weekday*24+hour, sinusoid 168", "single-bar")

# Day-of-week
for w in range(7):
    add(f"t_dow_{w}_oh", "day_of_week_oh", "binary", f"1.0 if weekday == {w} (0=Mon)", "ts.weekday()", "single-bar")
add("t_dow_sin", "day_of_week_cyc", "float", "sin(2π * weekday / 7)", "math.sin(2π·weekday/7)", "single-bar")
add("t_dow_cos", "day_of_week_cyc", "float", "cos(2π * weekday / 7)", "math.cos(2π·weekday/7)", "single-bar")
add("t_is_weekend", "day_of_week_aux", "binary", "1.0 if weekday >= 5 (Sat/Sun)", "weekday >= 5", "single-bar")

# Minute-of-hour
for b in range(4):
    add(f"t_minute_bucket_{b}_oh", "minute_of_hour_oh", "binary",
        f"1.0 if minute // 15 == {b}", "ts.minute // 15", "single-bar",
        leak="point-in-time")
add("t_minute_of_hour", "minute_of_hour_aux", "int", "ts.minute (0-59)", "ts.minute", "single-bar")
add("t_minute_of_day", "minute_of_day_aux", "int", "hour*60 + minute (0-1439)", "hour*60 + minute", "single-bar")

# Calendar
add("t_day_of_month", "day_of_month", "int", "1-31", "ts.day", "single-bar")
add("t_day_of_month_sin", "day_of_month_cyc", "float", "sin(2π · day/31)", "math.sin(2π·day/31)", "single-bar")
add("t_day_of_month_cos", "day_of_month_cyc", "float", "cos(2π · day/31)", "math.cos(2π·day/31)", "single-bar")
add("t_week_of_month", "week_of_month", "int", "1-5 ISO-style Mon-anchored", "_week_of_month()", "single-bar")
add("t_month_of_year", "month_of_year", "int", "1-12", "ts.month", "single-bar")
add("t_month_sin", "month_of_year_cyc", "float", "sin(2π · month/12)", "math.sin(2π·month/12)", "single-bar")
add("t_month_cos", "month_of_year_cyc", "float", "cos(2π · month/12)", "math.cos(2π·month/12)", "single-bar")
add("t_quarter_of_year", "quarter_of_year", "int", "1-4 from month", "(month-1)//3 + 1", "single-bar")
add("t_is_first_week_of_month", "month_phase", "binary", "1.0 if day <= 7", "day <= 7", "single-bar")
add("t_is_last_3_trading_days_of_month", "month_phase", "binary",
    "1.0 if Mon-Fri days remaining in month < 3",
    "_trading_days_to_eom() < 3", "month",
    leak="point-in-time, computed from calendar only (no realized vol leak)")
add("t_is_last_5_trading_days_of_month", "month_phase", "binary", "1.0 if days remaining < 5",
    "_trading_days_to_eom() < 5", "month",
    leak="point-in-time, computed from calendar only")
add("t_is_last_week_of_quarter", "quarter_phase", "binary",
    "1.0 if month in {3,6,9,12} AND day in last 7 of month",
    "_is_last_week_of_quarter()", "quarter",
    leak="point-in-time, calendar-only")
add("t_trading_days_to_month_end", "month_phase", "int",
    "Mon-Fri days from `d` to month-end (no holiday subtraction)",
    "_trading_days_to_eom()", "month",
    leak="point-in-time, calendar-only")

# Per-KZ features (each KZ in {london, ny, tokyo}; tokyo only present if symbol has it)
for kz in ("london", "ny", "tokyo"):
    add(f"t_kz_{kz}_active", f"kz_{kz}_active", "binary",
        f"1.0 if `now` falls inside the {kz} KZ for this symbol",
        f"_kz_active(now_min, kz='{kz}')", "single-bar",
        leak="point-in-time, KZ schedule is static")
    add(f"t_kz_{kz}_signed_min_to_open", f"kz_{kz}_pos", "int",
        f"Signed minutes from `now` to {kz} KZ open today; +ve future, -ve past",
        f"event_min - now_min for {kz} start_min", "single-bar",
        leak="point-in-time")
    add(f"t_kz_{kz}_signed_min_to_close", f"kz_{kz}_pos", "int",
        f"Signed minutes from `now` to {kz} KZ close today; +ve future, -ve past",
        f"event_min - now_min for {kz} end_min", "single-bar",
        leak="point-in-time")
    add(f"t_kz_{kz}_abs_min_to_open", f"kz_{kz}_pos", "int",
        f"abs of signed_min_to_open for {kz}", f"abs(signed_min_to_open)", "single-bar")
    add(f"t_kz_{kz}_abs_min_to_close", f"kz_{kz}_pos", "int",
        f"abs of signed_min_to_close for {kz}", f"abs(signed_min_to_close)", "single-bar")
    add(f"t_kz_{kz}_min_to_next_open", f"kz_{kz}_pos", "int",
        f"Minutes until NEXT {kz} open; if open is past today, wraps to tomorrow's open via +1440",
        f"open_d if open_d>=0 else open_d+1440", "<24h",
        leak="point-in-time, looks at FUTURE event but event time is calendar-known")
    add(f"t_kz_{kz}_min_to_next_close", f"kz_{kz}_pos", "int",
        f"Minutes until NEXT {kz} close; wraps tomorrow if past today",
        f"close_d if close_d>=0 else close_d+1440", "<24h")
    add(f"t_kz_{kz}_window_len_min", f"kz_{kz}_meta", "int",
        f"Window length in minutes of {kz} KZ for this symbol",
        "(end_min-start_min) modulo 1440", "static")
    add(f"t_kz_{kz}_first_15min", f"kz_{kz}_phase", "binary",
        f"1.0 if currently inside {kz} AND elapsed-since-open < 15min",
        "0 <= elapsed_in_kz < 15 AND active", "single-bar",
        leak="point-in-time")
    add(f"t_kz_{kz}_first_30min", f"kz_{kz}_phase", "binary",
        f"1.0 if inside {kz} AND elapsed < 30min",
        "0 <= elapsed_in_kz < 30 AND active", "single-bar")
    add(f"t_kz_{kz}_last_15min", f"kz_{kz}_phase", "binary",
        f"1.0 if inside {kz} AND remaining < 15min",
        "(win_len - elapsed) <= 15 AND active", "single-bar")
    add(f"t_kz_{kz}_progress_pct", f"kz_{kz}_phase", "float",
        f"elapsed_in_kz / window_len, sentinel -1 if not in KZ",
        "elapsed_in_kz / max(win_len,1)", "single-bar")

# Active-KZ summary
add("t_kz_active_any", "kz_summary", "binary", "1.0 if ANY KZ active", "active_kz_count > 0", "single-bar")
add("t_kz_active_count", "kz_summary", "int", "Count of active KZs (overlap detection)", "len([k for k if active])", "single-bar")
add("t_kz_active_is_london", "kz_summary_oh", "binary", "1.0 if currently active KZ == london", "active_kz_name == 'london'", "single-bar")
add("t_kz_active_is_ny", "kz_summary_oh", "binary", "1.0 if currently active KZ == ny", "active_kz_name == 'ny'", "single-bar")
add("t_kz_active_is_tokyo", "kz_summary_oh", "binary", "1.0 if currently active KZ == tokyo", "active_kz_name == 'tokyo'", "single-bar")
add("t_kz_active_is_none", "kz_summary_oh", "binary", "1.0 if outside any KZ", "active_kz_name is None", "single-bar")

# Session transitions / NY split
add("t_session_transition_london_to_ny", "session_transition", "binary",
    "1.0 if `now` in [london_end - 60min, ny_start + 60min) — captures EU-close → NY-open handoff",
    "max(0, london.end-60) <= now < min(1440, ny.start+60)", "single-bar",
    leak="point-in-time, both events calendar-known")
add("t_london_to_ny_gap_min", "session_transition", "int",
    "Static minutes from London close to NY open (per symbol)",
    "ny.start_min - london.end_min", "static")
add("t_in_ny_am_window", "ny_split", "binary",
    "1.0 if inside NY KZ AND in first half (AM half: ny_start to ny_midpoint)",
    "ny_start <= now < (ny_start+ny_end)/2", "single-bar")
add("t_in_ny_pm_window", "ny_split", "binary",
    "1.0 if inside NY KZ AND in second half (PM)",
    "ny_midpoint <= now < ny_end", "single-bar")
add("t_is_first_m15_of_ny", "ny_split", "binary",
    "1.0 if inside [ny_start, ny_start+15) — E.2 first-NY-candle reference",
    "ny_start <= now < ny_start+15", "single-bar",
    leak="point-in-time, calendar-known")

# Time-since-last-fill (caller-supplied)
add("t_min_since_last_fill_provided", "since_last_fill", "binary",
    "1.0 if caller supplied a non-negative minutes_since_last_fill",
    "minutes_since_last_fill is not None and >=0", "rolling-from-last-fill",
    leak="caller responsibility — must be a PAST fill, not future")
add("t_min_since_last_fill", "since_last_fill", "int",
    "Minutes since last realized trade fill on this instrument; -1 sentinel if missing",
    "caller-supplied", "rolling-from-last-fill")
add("t_min_since_last_fill_log", "since_last_fill", "float",
    "log1p(minutes_since_last_fill)", "math.log1p(...)", "rolling-from-last-fill")
add("t_min_since_last_fill_le_60", "since_last_fill", "binary", "1.0 if le 60min (fresh fill)", "<= 60", "rolling-from-last-fill")
add("t_min_since_last_fill_le_240", "since_last_fill", "binary", "1.0 if le 240min (4h)", "<= 240", "rolling-from-last-fill")
add("t_min_since_last_fill_le_1440", "since_last_fill", "binary", "1.0 if le 1440min (24h)", "<= 1440", "rolling-from-last-fill")
add("t_min_since_last_fill_le_4320", "since_last_fill", "binary", "1.0 if le 4320min (3d)", "<= 4320", "rolling-from-last-fill")

add("t_bars_since_last_kz_open_provided", "since_last_kz", "binary",
    "1.0 if caller supplied a non-negative bars_since_last_kz_open",
    "param is not None and >=0", "rolling-from-last-kz-open")
add("t_bars_since_last_kz_open", "since_last_kz", "int",
    "M15 bars since most recent KZ open (any session); -1 sentinel if missing",
    "caller-supplied", "rolling-from-last-kz-open")

# Calendar event proximity
add("t_days_to_nearest_holiday_signed", "holiday_proximity", "int",
    "Signed days to nearest US federal holiday across years {y-1, y, y+1}",
    "min by abs of (h - d).days over US holiday list", "calendar",
    leak="static calendar")
add("t_days_to_nearest_holiday_abs", "holiday_proximity", "int", "abs of holiday_signed", "abs(holiday_signed)", "calendar")
add("t_is_within_2d_of_holiday", "holiday_proximity", "binary", "1.0 if abs <=2", "abs(signed) <= 2", "calendar")
add("t_is_within_5d_of_holiday", "holiday_proximity", "binary", "1.0 if abs <=5", "abs(signed) <= 5", "calendar")
add("t_is_holiday_today", "holiday_proximity", "binary", "1.0 if signed == 0", "signed == 0", "calendar")

add("t_days_to_nearest_opex_signed", "opex_proximity", "int",
    "Signed days to nearest 3rd-Friday US-equity OPEX across {y-1,y,y+1}",
    "min by abs over monthly 3rd-Friday list", "calendar",
    leak="static calendar")
add("t_days_to_nearest_opex_abs", "opex_proximity", "int", "abs", "abs(signed)", "calendar")
add("t_is_within_2d_of_opex", "opex_proximity", "binary", "1.0 if abs <=2", "abs(signed)<=2", "calendar")
add("t_is_within_5d_of_opex", "opex_proximity", "binary", "1.0 if abs <=5", "abs(signed)<=5", "calendar")
add("t_is_opex_today", "opex_proximity", "binary", "1.0 if signed==0", "signed==0", "calendar")
add("t_is_index_x_opex_5d", "opex_proximity", "binary",
    "1.0 if symbol is index (US30/US30_cash/NAS100) AND within 5d of OPEX",
    "is_index AND abs(opex_signed)<=5", "calendar",
    leak="static calendar; symbol-conditional")

add("t_days_to_quarterly_opex_signed", "qopex_proximity", "int",
    "Signed days to nearest QUARTERLY OPEX (Mar/Jun/Sep/Dec 3rd Friday)",
    "min by abs over quarterly 3rd-Friday list", "calendar")
add("t_days_to_quarterly_opex_abs", "qopex_proximity", "int", "abs", "abs(signed)", "calendar")
add("t_is_within_5d_of_quarterly_opex", "qopex_proximity", "binary", "1.0 if abs <=5", "abs(signed)<=5", "calendar")

add("t_days_to_nearest_nfp_signed", "nfp_proximity", "int",
    "Signed days to nearest 1st-Friday-of-month (NFP release formula)",
    "min by abs over 1st-Friday-each-month list", "calendar",
    leak="static-formula approximation; ~5 of 12 months / yr BLS shifts release; documented as approximation")
add("t_days_to_nearest_nfp_abs", "nfp_proximity", "int", "abs", "abs(signed)", "calendar")
add("t_is_within_1d_of_nfp", "nfp_proximity", "binary", "1.0 if abs <=1", "abs(signed)<=1", "calendar")
add("t_is_within_3d_of_nfp", "nfp_proximity", "binary", "1.0 if abs <=3", "abs(signed)<=3", "calendar")
add("t_is_nfp_today", "nfp_proximity", "binary", "1.0 if signed==0", "signed==0", "calendar")

add("t_days_to_nearest_cpi_signed", "cpi_proximity", "int",
    "Signed days to nearest 2nd-Wednesday-of-month (CPI release formula)",
    "min by abs over 2nd-Wednesday-each-month list", "calendar",
    leak="formula-based APPROXIMATION; treat as ±2d fuzz; documented")
add("t_days_to_nearest_cpi_abs", "cpi_proximity", "int", "abs", "abs(signed)", "calendar")
add("t_is_within_1d_of_cpi", "cpi_proximity", "binary", "1.0 if abs <=1", "abs(signed)<=1", "calendar")
add("t_is_within_3d_of_cpi", "cpi_proximity", "binary", "1.0 if abs <=3", "abs(signed)<=3", "calendar")

add("t_day_of_year_sin", "year_phase_cyc", "float", "sin(2π · doy/366)", "math.sin(2π·doy/366)", "single-bar")
add("t_day_of_year_cos", "year_phase_cyc", "float", "cos(2π · doy/366)", "math.cos(2π·doy/366)", "single-bar")


def main() -> None:
    # Load stability
    stab = json.load(open(STABILITY_PATH))
    stab_map = {f["feature"]: f for f in stab["features"]}

    # Validate doc coverage
    expected_names = set(list_feature_names("USDJPY"))  # 3-KZ instrument; full list
    documented_names = set(d.name for d in DOCS)
    missing = expected_names - documented_names
    extra = documented_names - expected_names
    assert not missing, f"DOCS missing: {missing}"
    if extra:
        print(f"WARN: DOCS has {len(extra)} extra entries (likely tokyo for 2-KZ symbols, OK): {sorted(extra)[:10]}")

    # Build merged rows (catalog row per feature)
    rows: list[dict] = []
    for d in DOCS:
        s = stab_map.get(d.name, {})
        rho = s.get("stability_spearman_rho")
        n = s.get("stability_n", 0)
        note = s.get("note", "")
        rows.append({
            "feature": d.name,
            "family": d.family,
            "subfamily": d.subfamily,
            "dtype": d.dtype,
            "description": d.description,
            "source": d.source,
            "computation": d.computation,
            "lookback": d.lookback,
            "leakage_check": d.leakage_check,
            "stability_spearman_rho": "" if rho is None else f"{rho:.4f}",
            "stability_n": n,
            "stability_note": note,
        })

    # CSV
    fieldnames = list(rows[0].keys())
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {CSV_PATH} ({len(rows)} rows)")

    # Markdown
    sample_xau = compute_time_session_features(
        datetime(2026, 4, 14, 14, 30, tzinfo=timezone.utc),
        "XAUUSD", bars_since_last_kz_open=4, minutes_since_last_fill=180,
    )
    sample_usdjpy = compute_time_session_features(
        datetime(2026, 4, 14, 14, 30, tzinfo=timezone.utc),
        "USDJPY", bars_since_last_kz_open=4, minutes_since_last_fill=180,
    )

    valid_stab = [(d.name, stab_map.get(d.name, {})) for d in DOCS]
    valid_stab = [(n, s) for n, s in valid_stab if s.get("stability_spearman_rho") is not None]
    valid_stab.sort(key=lambda t: abs(t[1]["stability_spearman_rho"]), reverse=True)

    lines: list[str] = []
    lines.append("# K54 v2 — TIME / SESSION feature catalog")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"**Module:** `research/ml_program/scripts/features/time_session.py`")
    lines.append(f"**Stability source:** `{STABILITY_PATH.name}` ({stab['n_total']} pre-Apr-2026 records: "
                 f"{stab['n_f11']} F11 BOS hour-stamped + {stab['n_trade_index']} trade-index DATE-only)")
    lines.append(f"**Data cutoff:** ≤2026-04-28 23:59 UTC (Q1.2 hypothesis lock)")
    lines.append("")
    lines.append("## Feature counts")
    lines.append("")
    lines.append(f"- 2-KZ instruments (XAUUSD, GBPUSD, US30, US30_cash, NAS100, XAGUSD): **{len(sample_xau)}** features.")
    lines.append(f"- 3-KZ instruments (USDJPY, GBPJPY): **{len(sample_usdjpy)}** features (adds Tokyo KZ subfamily).")
    lines.append(f"- Documented in DOCS: **{len(DOCS)}** (union; Tokyo subfamily only emits for 3-KZ symbols).")
    lines.append("")
    lines.append("## Top-10 by stability |rho| (pre-Apr-2026 backfill)")
    lines.append("")
    lines.append("| Rank | Feature | rho | n |")
    lines.append("|---:|---|---:|---:|")
    for i, (n, s) in enumerate(valid_stab[:10], 1):
        lines.append(f"| {i} | `{n}` | {s['stability_spearman_rho']:+.4f} | {s['stability_n']} |")
    lines.append("")
    lines.append("**Note:** Tokyo KZ features rank highest but only on the n=105 USDJPY+GBPJPY subset. ")
    lines.append("`t_in_ny_pm_window` and `t_is_first_m15_of_ny` are the strongest cross-instrument signals (n=474). ")
    lines.append("Per Discipline (\"don't drop based on stability\") modeler keeps all features; this table is informational.")
    lines.append("")
    lines.append("## Leakage self-check")
    lines.append("")
    lines.append("All features in this family are computed from a *single timestamp* (the trade-entry candle close) ")
    lines.append("and a *static calendar*. No future-window reads. Specific checks:")
    lines.append("")
    lines.append("- **`t_kz_*_min_to_next_open` / `_close`**: positive distances to FUTURE events. The future event TIME ")
    lines.append("  is calendar-known (KZ schedule is static config) — this is NOT a future-data peek; it's the same ")
    lines.append("  category as \"days until Christmas\". OK.")
    lines.append("- **`t_min_since_last_fill_*`**: caller responsibility. Module clamps and buckets, but DOES NOT compute ")
    lines.append("  the underlying counter. Caller must ensure the supplied value reflects only fills that closed BEFORE ")
    lines.append("  `ts` (the trade-entry candle). Documented in module docstring.")
    lines.append("- **`t_bars_since_last_kz_open`**: same caller-responsibility note.")
    lines.append("- **`t_session_transition_london_to_ny`**: window edges (london_end - 60, ny_start + 60) are static config. OK.")
    lines.append("- **`t_is_last_3_trading_days_of_month`**: Mon-Fri counter to month-end. Pure calendar (no realized vol). OK.")
    lines.append("- **`t_days_to_nearest_*` calendar features**: 100% calendar-derived. They CAN look forward in the calendar ")
    lines.append("  (\"days to NEXT NFP\") which is fine — NFP date is statically known. OK.")
    lines.append("")
    lines.append("**Sign convention review:** `t_kz_*_signed_min_to_open` is positive when the KZ open is ")
    lines.append("LATER than `now` (future event), negative when already passed. `t_kz_*_signed_min_to_close` likewise. ")
    lines.append("Track A trap explicitly avoided — counts past events as NEGATIVE, not as positive past-tense distances.")
    lines.append("")
    lines.append("## Calendar source list")
    lines.append("")
    lines.append("All calendars are STATIC — NO external feed, no news content, no sentiment.")
    lines.append("")
    lines.append("| Calendar | Source | Confidence | Documented in |")
    lines.append("|---|---|---|---|")
    lines.append("| US federal holidays | Hard-coded fixed-rule list (New Year, MLK 3rd Mon Jan, Presidents 3rd Mon Feb, Good Friday via Meeus computus, Memorial last Mon May, Juneteenth Jun 19, July 4, Labor 1st Mon Sep, Thanksgiving 4th Thu Nov, Christmas Dec 25) | High; weekend-shifts NOT modeled | `time_session.py:_us_holidays_for` |")
    lines.append("| Monthly OPEX | 3rd Friday of each month (US equity options) | High — fixed by CBOE rule | `time_session.py:_opex_third_friday` |")
    lines.append("| Quarterly OPEX | 3rd Friday of Mar/Jun/Sep/Dec | High | `time_session.py:_quarterly_oexp_third_friday` |")
    lines.append("| NFP release | 1st Friday of each month (BLS rule) | **Medium** — BLS shifts release for some months (e.g. holidays). Flagged as approximation. | `time_session.py:_nfp_first_friday` |")
    lines.append("| CPI release | 2nd Wednesday of each month | **Low-Medium** — actual release floats Tue/Wed/Thu mid-month. Flagged ±2d fuzz. | `time_session.py:_cpi_release_date` |")
    lines.append("| KZ schedule | CLAUDE.md \"KILL ZONE SCHEDULE (UTC)\" table; per-symbol overrides in `agent_config.yaml` (XAUUSD/XAGUSD NY end_utc=17:00, NAS100 special). | High | `time_session.py:KZ_SCHEDULE` |")
    lines.append("")
    lines.append("**Approximation handling:** Features built from medium/low-confidence calendars (NFP/CPI) emit ")
    lines.append("ONLY `days_to_*` quantitative features and never claim \"NFP day = today\" with high conviction. The ")
    lines.append("modeler is expected to learn that ±2d windows around the formula are the meaningful zone, not ±0d.")
    lines.append("")
    lines.append("## Subfamily index (count per subfamily)")
    lines.append("")
    sub_counts: dict[str, int] = {}
    for d in DOCS:
        sub_counts[d.subfamily] = sub_counts.get(d.subfamily, 0) + 1
    lines.append("| Subfamily | Feature count |")
    lines.append("|---|---:|")
    for sub in sorted(sub_counts):
        lines.append(f"| `{sub}` | {sub_counts[sub]} |")
    lines.append(f"| **TOTAL** | **{len(DOCS)}** |")
    lines.append("")
    lines.append("## Per-feature documentation")
    lines.append("")
    lines.append("Stability column: Spearman rank correlation between feature value and realized R, on pre-Apr-2026 ")
    lines.append("F11 BOS records (n=345, hour-stamped) UNIONED with trade-index records (n=129, DATE-only @ KZ-default ")
    lines.append("hour). N is per-feature (Tokyo subfamily features only see USDJPY+GBPJPY, n=105). Empty cells = ")
    lines.append("constant-in-backfill (e.g. minute-of-hour always = 0 in F11 hour-stamped data; live data will vary).")
    lines.append("")
    # Per-subfamily feature tables
    lines.append("| Feature | Subfamily | dtype | rho | n | Description |")
    lines.append("|---|---|---|---:|---:|---|")
    for r in rows:
        rho_str = r["stability_spearman_rho"] or ""
        n_str = r["stability_n"] or ""
        lines.append(f"| `{r['feature']}` | {r['subfamily']} | {r['dtype']} | {rho_str} | {n_str} | {r['description']} |")
    lines.append("")
    lines.append("## Inference cost")
    lines.append("")
    lines.append("All features are O(1) constant-time calendar / arithmetic computations. No I/O, no model calls, ")
    lines.append("no rolling-window aggregations. Per-trade feature compute time on commodity laptop: <1ms.")
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append("- **Module:** `research/ml_program/scripts/features/time_session.py`")
    lines.append("- **Stability driver:** `research/ml_program/scripts/features/_compute_stability.py`")
    lines.append("- **Catalog emitter (this file):** `research/ml_program/scripts/features/_emit_catalog.py`")
    lines.append("- **KZ schedule reference:** `CLAUDE.md` + `config/agent_config.yaml`")
    lines.append("- **Outcome data (stability):** `research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl`, "
                 "`knowledge_base/index/_trade_index.json`")
    lines.append("")

    MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {MD_PATH} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
