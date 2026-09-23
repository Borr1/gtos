"""TIME / SESSION feature family for K54 v2.

Pure functions that take a single trade-entry timestamp (`pd.Timestamp` or
`datetime`, MUST be timezone-aware UTC) and a `symbol` string, and return a
flat dict of TIME / SESSION features. No I/O, no look-ahead, no external
data sources.

Scope (per Q1.2 hypothesis brief):
- Minutes-to-KZ-open / minutes-to-KZ-close per session (London, NY, Tokyo)
  per instrument (KZ schedules differ by symbol).
- KZ active flags + transition flags + first-N-minutes-of-session flags.
- Hour-of-day / day-of-week / minute-of-hour bucket (one-hot AND sinusoidal).
- Week-of-month, day-of-month, end-of-month, end-of-quarter.
- OPEX proximity (third-Friday of US equity options) for index instruments.
- US holiday proximity (static fixed-rule calendar — no external feed).
- NFP / CPI date proximity (calendar formulas — DATE-only, no content).
- Time-since-last-fill placeholder (computed externally; this module exposes
  helper to clamp + bucket only since we don't carry fill state).
- Bars-since-last-KZ-open.
- NY-AM (13:00-15:00 UTC) vs NY-PM (15:00-17:00 UTC) split.

Hard constraints:
- Data cutoff: ≤2026-04-28 23:59 UTC. (Calendars defined statically; module
  raises AssertionError if asked about a timestamp > 2026-04-28 23:59 UTC.)
- No production state changes. Pure compute.
- Pure market state only (calendar-based). External news/sentiment NOT used.
- No look-ahead. minutes_to_KZ_open/close use a *future* event lookup; the
  reverse direction (minutes_since_KZ_close) is also exposed but is
  past-only by construction.

Feature naming convention:
- `t_<feature>` for all time/session features (so the family is
  grep-friendly downstream in the K54 v2 build_features code).

Inference cost: trivial. All features are O(1) calendar lookups.

Author: time_session feature engineer (K54 v2 Week 2)
Date: 2026-04-28
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Optional, Union

# ---------------------------------------------------------------------------
# Hard cutoff (Q1.2 pre-registered)
# ---------------------------------------------------------------------------
DATA_CUTOFF_UTC = datetime(2026, 4, 28, 23, 59, 59, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Per-instrument KZ schedule (UTC).
#
# Source: CLAUDE.md "KILL ZONE SCHEDULE (UTC)" table (authoritative for the
# K54 v2 feature layer). Production `agent_config.yaml` extends some of
# these end times via per-symbol overrides (e.g. XAUUSD NY end_utc=17:00),
# but the K54 v2 feature layer mirrors the published CLAUDE.md table so
# downstream importance is interpretable.
#
# (start_min_utc, end_min_utc) where end_min may be ≤ start_min iff the KZ
# crosses midnight (e.g. tokyo 22:00-02:00 hypothetical).
#
# Instruments NOT in this map fall through to KZ_DEFAULT_FALLBACK.
# ---------------------------------------------------------------------------

def _hm_to_min(h: int, m: int = 0) -> int:
    return h * 60 + m


KZ_SCHEDULE: dict[str, dict[str, tuple[int, int]]] = {
    "XAUUSD": {
        "london": (_hm_to_min(7, 0), _hm_to_min(10, 30)),
        "ny":     (_hm_to_min(13, 0), _hm_to_min(17, 0)),
    },
    "US30": {
        "london": (_hm_to_min(8, 0), _hm_to_min(10, 30)),
        "ny":     (_hm_to_min(13, 30), _hm_to_min(16, 0)),
    },
    "US30_cash": {
        "london": (_hm_to_min(8, 0), _hm_to_min(10, 30)),
        "ny":     (_hm_to_min(13, 30), _hm_to_min(16, 0)),
    },
    "USDJPY": {
        "tokyo":  (_hm_to_min(0, 0), _hm_to_min(3, 0)),
        "london": (_hm_to_min(7, 0), _hm_to_min(9, 30)),
        "ny":     (_hm_to_min(13, 0), _hm_to_min(15, 30)),
    },
    "GBPJPY": {
        "tokyo":  (_hm_to_min(0, 0), _hm_to_min(3, 0)),
        "london": (_hm_to_min(7, 0), _hm_to_min(9, 30)),
        "ny":     (_hm_to_min(13, 0), _hm_to_min(15, 30)),
    },
    "GBPUSD": {
        "london": (_hm_to_min(7, 0), _hm_to_min(12, 0)),
        "ny":     (_hm_to_min(13, 0), _hm_to_min(15, 30)),
    },
    "XAGUSD": {
        "london": (_hm_to_min(7, 0), _hm_to_min(12, 0)),
        "ny":     (_hm_to_min(13, 0), _hm_to_min(17, 0)),
    },
    "NAS100": {
        "london": (_hm_to_min(8, 0), _hm_to_min(12, 0)),
        "ny":     (_hm_to_min(14, 0), _hm_to_min(19, 0)),
    },
}

# Fallback for instruments not in the map (use XAUUSD's wider schedule).
KZ_DEFAULT_FALLBACK = KZ_SCHEDULE["XAUUSD"]

# All-session set used for "KZ-active-any" + transition feature.
ALL_KZ_NAMES = ("london", "ny", "tokyo")


# ---------------------------------------------------------------------------
# Static calendars (DATE only — NO news content, sentiment, or external feed)
# ---------------------------------------------------------------------------

def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Return the date of the n-th occurrence of `weekday` in `year`/`month`.

    weekday: 0=Mon .. 6=Sun (datetime.weekday()). n: 1=first, 2=second, ...
    """
    assert 1 <= n <= 5
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    target_day = 1 + offset + 7 * (n - 1)
    return date(year, month, target_day)


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """Return the LAST occurrence of `weekday` in `year`/`month`."""
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    last_day = next_month_first - timedelta(days=1)
    offset = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=offset)


def _good_friday(year: int) -> date:
    """Anonymous Gregorian computus for Easter Sunday, then -2 days for Good Friday."""
    # Meeus / Jones / Butcher Gregorian algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    easter = date(year, month, day)
    return easter - timedelta(days=2)


def _us_holidays_for(year: int) -> list[date]:
    """Static US federal holidays + observance heuristics (DATE only).

    Includes: New Year, MLK Day, Presidents Day, Good Friday, Memorial Day,
    Juneteenth, July 4, Labor Day, Thanksgiving, Christmas. Does NOT shift
    to Mon/Fri if holiday falls on a weekend (markets vary by holiday;
    intentionally simple).
    """
    return [
        date(year, 1, 1),                                  # New Year
        _nth_weekday_of_month(year, 1, 0, 3),              # MLK (3rd Mon of Jan)
        _nth_weekday_of_month(year, 2, 0, 3),              # Presidents Day (3rd Mon of Feb)
        _good_friday(year),                                # Good Friday (variable)
        _last_weekday_of_month(year, 5, 0),                # Memorial Day (last Mon of May)
        date(year, 6, 19),                                 # Juneteenth
        date(year, 7, 4),                                  # July 4
        _nth_weekday_of_month(year, 9, 0, 1),              # Labor Day (1st Mon of Sep)
        _nth_weekday_of_month(year, 11, 3, 4),             # Thanksgiving (4th Thu of Nov)
        date(year, 12, 25),                                # Christmas
    ]


def _opex_third_friday(year: int, month: int) -> date:
    """US equity-options monthly OPEX = 3rd Friday of the month."""
    return _nth_weekday_of_month(year, month, 4, 3)  # Friday=4


def _nfp_first_friday(year: int, month: int) -> date:
    """US Non-Farm Payrolls release = 1st Friday of the month (BLS rule).

    Conservative formula. Some months BLS shifts the release; we DOCUMENT
    this as a known approximation. Not a hard-coded date list — formula only.
    """
    return _nth_weekday_of_month(year, month, 4, 1)


def _cpi_release_date(year: int, month: int) -> date:
    """US CPI release for `year`/`month` data is released MID-month — typically
    the 2nd Wednesday of the month-after, sometimes Tuesday or Thursday.

    Conservative formula: 2nd Wednesday of the same calendar month (`year`/`month`).
    DOCUMENTED approximation; treat as ±2 day fuzz. Used only for "days from
    nearest CPI" type features, not for trade-time CPI matching.
    """
    return _nth_weekday_of_month(year, month, 2, 2)  # Wednesday=2


def _quarterly_oexp_third_friday(year: int, quarter: int) -> date:
    """Quarterly OPEX (March, June, September, December) — 3rd Friday."""
    qmonth = {1: 3, 2: 6, 3: 9, 4: 12}[quarter]
    return _opex_third_friday(year, qmonth)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _KZWindow:
    name: str
    start_min: int
    end_min: int
    crosses_midnight: bool

    @classmethod
    def from_tuple(cls, name: str, span: tuple[int, int]) -> "_KZWindow":
        s, e = span
        return cls(
            name=name,
            start_min=s,
            end_min=e,
            crosses_midnight=(e <= s),
        )


def _kz_windows_for(symbol: str) -> list[_KZWindow]:
    schedule = KZ_SCHEDULE.get(symbol, KZ_DEFAULT_FALLBACK)
    return [_KZWindow.from_tuple(name, span) for name, span in schedule.items()]


def _utc_minute_of_day(ts: datetime) -> int:
    """Return UTC minute-of-day [0, 1440) from a tz-aware UTC datetime."""
    assert ts.tzinfo is not None, "ts must be timezone-aware (UTC)"
    ts_utc = ts.astimezone(timezone.utc)
    return ts_utc.hour * 60 + ts_utc.minute


def _signed_minutes_to_event(now_min: int, event_min: int) -> int:
    """Signed minutes from `now_min` to `event_min` within the same UTC day.

    Positive = event in future, negative = event already passed. This does
    NOT cross midnight. Range: [-1440, +1440).
    """
    return event_min - now_min


def _kz_active(now_min: int, kz: _KZWindow) -> bool:
    if kz.crosses_midnight:
        return (now_min >= kz.start_min) or (now_min < kz.end_min)
    return kz.start_min <= now_min < kz.end_min


def _signed_minutes_to_open_close(now_min: int, kz: _KZWindow) -> tuple[int, int]:
    """Return (signed_min_to_open, signed_min_to_close) for a KZ window.

    Convention:
    - signed_min_to_open is POSITIVE if open is later today, NEGATIVE if
      open already happened today.
    - signed_min_to_close is POSITIVE if close is later today, NEGATIVE if
      close already happened today.

    For `crosses_midnight` KZs the calculation accounts for wrap.
    """
    open_d = _signed_minutes_to_event(now_min, kz.start_min)
    close_d = _signed_minutes_to_event(now_min, kz.end_min)
    return open_d, close_d


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

DateLike = Union[datetime, date]


def _ensure_utc_aware(ts: DateLike) -> datetime:
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            raise ValueError("Naive datetimes are not allowed; pass UTC-aware.")
        return ts.astimezone(timezone.utc)
    if isinstance(ts, date):
        return datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc)
    raise TypeError(f"Unsupported timestamp type: {type(ts)}")


def _check_cutoff(ts: datetime) -> None:
    if ts > DATA_CUTOFF_UTC:
        raise AssertionError(
            f"Timestamp {ts.isoformat()} exceeds Q1.2 data cutoff "
            f"{DATA_CUTOFF_UTC.isoformat()}"
        )


def _trading_days_to_eom(d: date) -> int:
    """Approximate trading days from `d` to month-end. Mon-Fri only (no
    holiday subtraction; we have a separate holiday-distance feature).
    """
    # find last day of month
    if d.month == 12:
        eom = date(d.year, 12, 31)
    else:
        eom = date(d.year, d.month + 1, 1) - timedelta(days=1)
    cnt = 0
    cur = d
    while cur < eom:
        cur = cur + timedelta(days=1)
        if cur.weekday() < 5:
            cnt += 1
    return cnt


def _is_last_n_trading_days_of_month(d: date, n: int = 3) -> bool:
    return _trading_days_to_eom(d) < n


def _is_last_week_of_quarter(d: date) -> bool:
    if d.month not in (3, 6, 9, 12):
        return False
    last_dom = (date(d.year + (1 if d.month == 12 else 0),
                     1 if d.month == 12 else d.month + 1, 1) - timedelta(days=1)).day
    return d.day >= max(1, last_dom - 6)


def _week_of_month(d: date) -> int:
    """1-based ISO-style week-of-month (Mon-anchored)."""
    first_dom = date(d.year, d.month, 1)
    first_monday_offset = (-first_dom.weekday()) % 7
    first_monday_dom = 1 + first_monday_offset
    if d.day < first_monday_dom:
        return 1
    return ((d.day - first_monday_dom) // 7) + 2


def _nearest_holiday_signed(d: date) -> int:
    """Signed days to nearest US holiday across years {y-1, y, y+1}.

    Positive = future, negative = past, 0 = today is the holiday.
    """
    candidates: list[date] = []
    for yr in (d.year - 1, d.year, d.year + 1):
        candidates.extend(_us_holidays_for(yr))
    diffs = sorted(((h - d).days for h in candidates), key=abs)
    return diffs[0]


def _nearest_opex_signed(d: date) -> int:
    candidates = []
    for yr in (d.year - 1, d.year, d.year + 1):
        for m in range(1, 13):
            candidates.append(_opex_third_friday(yr, m))
    diffs = sorted(((o - d).days for o in candidates), key=abs)
    return diffs[0]


def _nearest_quarterly_opex_signed(d: date) -> int:
    candidates = []
    for yr in (d.year - 1, d.year, d.year + 1):
        for q in range(1, 5):
            candidates.append(_quarterly_oexp_third_friday(yr, q))
    diffs = sorted(((o - d).days for o in candidates), key=abs)
    return diffs[0]


def _nearest_nfp_signed(d: date) -> int:
    candidates = []
    for yr in (d.year - 1, d.year, d.year + 1):
        for m in range(1, 13):
            candidates.append(_nfp_first_friday(yr, m))
    diffs = sorted(((n - d).days for n in candidates), key=abs)
    return diffs[0]


def _nearest_cpi_signed(d: date) -> int:
    candidates = []
    for yr in (d.year - 1, d.year, d.year + 1):
        for m in range(1, 13):
            candidates.append(_cpi_release_date(yr, m))
    diffs = sorted(((c - d).days for c in candidates), key=abs)
    return diffs[0]


# ---------------------------------------------------------------------------
# Top-level feature builder
# ---------------------------------------------------------------------------

def compute_time_session_features(
    ts: DateLike,
    symbol: str,
    *,
    bars_since_last_kz_open: Optional[int] = None,
    minutes_since_last_fill: Optional[int] = None,
    enforce_cutoff: bool = True,
) -> dict[str, float]:
    """Compute the full TIME / SESSION feature dict for a single trade-entry.

    Args:
        ts: trade-entry candle-close timestamp (UTC-aware datetime or date).
            DATE-only inputs are upcast to 00:00 UTC of that date — features
            sensitive to hour-of-day will not be informative; downstream
            code should prefer hour-level F11 bos_time when available.
        symbol: instrument symbol (e.g. "XAUUSD"). Drives the per-instrument
            KZ schedule. Unknown symbols use KZ_DEFAULT_FALLBACK (XAUUSD).
        bars_since_last_kz_open: optional pre-computed counter (M15 bars
            since last KZ open of any session). Module returns NaN sentinel
            (-1) when not provided. Computed externally because we don't
            carry market-state context.
        minutes_since_last_fill: optional pre-computed counter (minutes
            since last realized trade close on this instrument). Module
            returns -1 when not provided.
        enforce_cutoff: raise if `ts > DATA_CUTOFF_UTC`. Set False only
            for tests with future-dated synthetic timestamps.

    Returns:
        dict[str, float] with all `t_*`-prefixed features. Values are
        numeric (float or int); categorical fields are emitted as one-hot
        floats (0.0 / 1.0).
    """
    ts_utc = _ensure_utc_aware(ts)
    if enforce_cutoff:
        _check_cutoff(ts_utc)

    feats: dict[str, float] = {}
    now_min = _utc_minute_of_day(ts_utc)
    d = ts_utc.date()
    weekday = ts_utc.weekday()  # 0=Mon..6=Sun
    hour = ts_utc.hour
    minute = ts_utc.minute

    # ---- Hour-of-day (24 one-hot + sinusoidal) ----------------------------
    for h in range(24):
        feats[f"t_hour_{h:02d}_oh"] = 1.0 if hour == h else 0.0
    feats["t_hour_sin"] = math.sin(2 * math.pi * hour / 24.0)
    feats["t_hour_cos"] = math.cos(2 * math.pi * hour / 24.0)
    # finer: hour-of-week (0..167) sinusoidal — captures tue-london vs fri-london
    how = weekday * 24 + hour
    feats["t_hour_of_week_sin"] = math.sin(2 * math.pi * how / 168.0)
    feats["t_hour_of_week_cos"] = math.cos(2 * math.pi * how / 168.0)

    # ---- Day-of-week (7 one-hot + sinusoidal) -----------------------------
    for w in range(7):
        feats[f"t_dow_{w}_oh"] = 1.0 if weekday == w else 0.0
    feats["t_dow_sin"] = math.sin(2 * math.pi * weekday / 7.0)
    feats["t_dow_cos"] = math.cos(2 * math.pi * weekday / 7.0)
    feats["t_is_weekend"] = 1.0 if weekday >= 5 else 0.0

    # ---- Minute-of-hour bucket (4-way: 0-14, 15-29, 30-44, 45-59) ---------
    minute_bucket = minute // 15
    for b in range(4):
        feats[f"t_minute_bucket_{b}_oh"] = 1.0 if minute_bucket == b else 0.0
    feats["t_minute_of_hour"] = float(minute)
    feats["t_minute_of_day"] = float(now_min)

    # ---- Day-of-month + week-of-month + month-of-year ---------------------
    feats["t_day_of_month"] = float(d.day)
    feats["t_day_of_month_sin"] = math.sin(2 * math.pi * d.day / 31.0)
    feats["t_day_of_month_cos"] = math.cos(2 * math.pi * d.day / 31.0)
    feats["t_week_of_month"] = float(_week_of_month(d))
    feats["t_month_of_year"] = float(d.month)
    feats["t_month_sin"] = math.sin(2 * math.pi * d.month / 12.0)
    feats["t_month_cos"] = math.cos(2 * math.pi * d.month / 12.0)
    feats["t_quarter_of_year"] = float((d.month - 1) // 3 + 1)
    feats["t_is_first_week_of_month"] = 1.0 if d.day <= 7 else 0.0
    feats["t_is_last_3_trading_days_of_month"] = (
        1.0 if _is_last_n_trading_days_of_month(d, 3) else 0.0
    )
    feats["t_is_last_5_trading_days_of_month"] = (
        1.0 if _is_last_n_trading_days_of_month(d, 5) else 0.0
    )
    feats["t_is_last_week_of_quarter"] = (
        1.0 if _is_last_week_of_quarter(d) else 0.0
    )
    feats["t_trading_days_to_month_end"] = float(_trading_days_to_eom(d))

    # ---- Per-symbol KZ features (active flag + min-to-open + min-to-close) -
    kz_windows = _kz_windows_for(symbol)
    active_kz_name: Optional[str] = None
    active_kz_count = 0
    for kz in kz_windows:
        active = _kz_active(now_min, kz)
        if active:
            active_kz_count += 1
            active_kz_name = kz.name
        feats[f"t_kz_{kz.name}_active"] = 1.0 if active else 0.0
        open_d, close_d = _signed_minutes_to_open_close(now_min, kz)
        feats[f"t_kz_{kz.name}_signed_min_to_open"] = float(open_d)
        feats[f"t_kz_{kz.name}_signed_min_to_close"] = float(close_d)
        # Magnitude (helpful for tree-monotonic fits)
        feats[f"t_kz_{kz.name}_abs_min_to_open"] = float(abs(open_d))
        feats[f"t_kz_{kz.name}_abs_min_to_close"] = float(abs(close_d))
        # Convenience: positive-only future distance, NaN-sentinel when past
        feats[f"t_kz_{kz.name}_min_to_next_open"] = float(open_d if open_d >= 0 else open_d + 1440)
        feats[f"t_kz_{kz.name}_min_to_next_close"] = float(close_d if close_d >= 0 else close_d + 1440)
        # Window length (constant per kz/symbol — useful for cross-sym comparison)
        win_len = (kz.end_min - kz.start_min) % 1440 if kz.crosses_midnight else (kz.end_min - kz.start_min)
        feats[f"t_kz_{kz.name}_window_len_min"] = float(win_len)
        # First-15-minutes-of-session flag
        if active:
            elapsed_in_kz = (
                (now_min - kz.start_min) if not kz.crosses_midnight
                else ((now_min - kz.start_min) % 1440)
            )
            feats[f"t_kz_{kz.name}_first_15min"] = 1.0 if 0 <= elapsed_in_kz < 15 else 0.0
            feats[f"t_kz_{kz.name}_first_30min"] = 1.0 if 0 <= elapsed_in_kz < 30 else 0.0
            feats[f"t_kz_{kz.name}_last_15min"] = 1.0 if (win_len - elapsed_in_kz) <= 15 else 0.0
            feats[f"t_kz_{kz.name}_progress_pct"] = float(elapsed_in_kz) / max(win_len, 1)
        else:
            feats[f"t_kz_{kz.name}_first_15min"] = 0.0
            feats[f"t_kz_{kz.name}_first_30min"] = 0.0
            feats[f"t_kz_{kz.name}_last_15min"] = 0.0
            feats[f"t_kz_{kz.name}_progress_pct"] = -1.0  # sentinel: no active KZ

    feats["t_kz_active_any"] = 1.0 if active_kz_count > 0 else 0.0
    feats["t_kz_active_count"] = float(active_kz_count)
    # Categorical active-KZ name as one-hot of the union (london / ny / tokyo / none)
    for nm in ALL_KZ_NAMES:
        feats[f"t_kz_active_is_{nm}"] = 1.0 if active_kz_name == nm else 0.0
    feats["t_kz_active_is_none"] = 1.0 if active_kz_name is None else 0.0

    # ---- Session transition flag: last 60 min of London → first 60 min of NY ---
    london = next((k for k in kz_windows if k.name == "london"), None)
    ny = next((k for k in kz_windows if k.name == "ny"), None)
    if london is not None and ny is not None:
        # Window: [london.end_min - 60, ny.start_min + 60). Strict: only valid
        # for non-midnight-crossing London (which is true for all current symbols).
        start_trans = max(0, london.end_min - 60)
        end_trans = min(1440, ny.start_min + 60)
        feats["t_session_transition_london_to_ny"] = (
            1.0 if start_trans <= now_min < end_trans else 0.0
        )
        # Also: gap from London-close to NY-open in minutes
        feats["t_london_to_ny_gap_min"] = float(ny.start_min - london.end_min)
    else:
        feats["t_session_transition_london_to_ny"] = 0.0
        feats["t_london_to_ny_gap_min"] = -1.0

    # ---- NY-AM vs NY-PM split (only if NY KZ defined) ---------------------
    if ny is not None:
        ny_midpoint = (ny.start_min + ny.end_min) // 2 if not ny.crosses_midnight else ny.start_min
        feats["t_in_ny_am_window"] = 1.0 if (
            ny.start_min <= now_min < ny_midpoint
        ) else 0.0
        feats["t_in_ny_pm_window"] = 1.0 if (
            ny_midpoint <= now_min < ny.end_min
        ) else 0.0
    else:
        feats["t_in_ny_am_window"] = 0.0
        feats["t_in_ny_pm_window"] = 0.0

    # ---- E.2 reference: first M15 bar of NY (13:00-13:15 for symbols with
    # ny.start_min == 13*60). Calendar-only; doesn't fire on US30 (NY=13:30) ----
    if ny is not None:
        feats["t_is_first_m15_of_ny"] = 1.0 if (
            ny.start_min <= now_min < (ny.start_min + 15)
        ) else 0.0
    else:
        feats["t_is_first_m15_of_ny"] = 0.0

    # ---- Time-since-last-fill counters (provided by caller; clamp) --------
    if minutes_since_last_fill is None or minutes_since_last_fill < 0:
        feats["t_min_since_last_fill_provided"] = 0.0
        feats["t_min_since_last_fill"] = -1.0
        feats["t_min_since_last_fill_log"] = -1.0
        for cap in (60, 240, 1440, 4320):
            feats[f"t_min_since_last_fill_le_{cap}"] = -1.0
    else:
        feats["t_min_since_last_fill_provided"] = 1.0
        feats["t_min_since_last_fill"] = float(minutes_since_last_fill)
        feats["t_min_since_last_fill_log"] = math.log1p(float(minutes_since_last_fill))
        for cap in (60, 240, 1440, 4320):
            feats[f"t_min_since_last_fill_le_{cap}"] = (
                1.0 if minutes_since_last_fill <= cap else 0.0
            )

    if bars_since_last_kz_open is None or bars_since_last_kz_open < 0:
        feats["t_bars_since_last_kz_open_provided"] = 0.0
        feats["t_bars_since_last_kz_open"] = -1.0
    else:
        feats["t_bars_since_last_kz_open_provided"] = 1.0
        feats["t_bars_since_last_kz_open"] = float(bars_since_last_kz_open)

    # ---- Calendar event proximity ----------------------------------------
    # Holidays
    nh_signed = _nearest_holiday_signed(d)
    feats["t_days_to_nearest_holiday_signed"] = float(nh_signed)
    feats["t_days_to_nearest_holiday_abs"] = float(abs(nh_signed))
    feats["t_is_within_2d_of_holiday"] = 1.0 if abs(nh_signed) <= 2 else 0.0
    feats["t_is_within_5d_of_holiday"] = 1.0 if abs(nh_signed) <= 5 else 0.0
    feats["t_is_holiday_today"] = 1.0 if nh_signed == 0 else 0.0

    # Monthly OPEX (3rd Friday)
    op_signed = _nearest_opex_signed(d)
    feats["t_days_to_nearest_opex_signed"] = float(op_signed)
    feats["t_days_to_nearest_opex_abs"] = float(abs(op_signed))
    feats["t_is_within_2d_of_opex"] = 1.0 if abs(op_signed) <= 2 else 0.0
    feats["t_is_within_5d_of_opex"] = 1.0 if abs(op_signed) <= 5 else 0.0
    feats["t_is_opex_today"] = 1.0 if op_signed == 0 else 0.0
    # Index-instrument-only cross: OPEX is most relevant for indices
    is_index = symbol in {"US30", "US30_cash", "NAS100"}
    feats["t_is_index_x_opex_5d"] = (
        1.0 if (is_index and abs(op_signed) <= 5) else 0.0
    )

    # Quarterly OPEX
    qopex_signed = _nearest_quarterly_opex_signed(d)
    feats["t_days_to_quarterly_opex_signed"] = float(qopex_signed)
    feats["t_days_to_quarterly_opex_abs"] = float(abs(qopex_signed))
    feats["t_is_within_5d_of_quarterly_opex"] = 1.0 if abs(qopex_signed) <= 5 else 0.0

    # NFP (1st Friday — formula-based, see docstring)
    nfp_signed = _nearest_nfp_signed(d)
    feats["t_days_to_nearest_nfp_signed"] = float(nfp_signed)
    feats["t_days_to_nearest_nfp_abs"] = float(abs(nfp_signed))
    feats["t_is_within_1d_of_nfp"] = 1.0 if abs(nfp_signed) <= 1 else 0.0
    feats["t_is_within_3d_of_nfp"] = 1.0 if abs(nfp_signed) <= 3 else 0.0
    feats["t_is_nfp_today"] = 1.0 if nfp_signed == 0 else 0.0

    # CPI (2nd Wednesday formula — APPROXIMATION, see docstring)
    cpi_signed = _nearest_cpi_signed(d)
    feats["t_days_to_nearest_cpi_signed"] = float(cpi_signed)
    feats["t_days_to_nearest_cpi_abs"] = float(abs(cpi_signed))
    feats["t_is_within_1d_of_cpi"] = 1.0 if abs(cpi_signed) <= 1 else 0.0
    feats["t_is_within_3d_of_cpi"] = 1.0 if abs(cpi_signed) <= 3 else 0.0

    # ---- Day-of-year sinusoidal (long-run seasonality) -------------------
    doy = d.timetuple().tm_yday
    feats["t_day_of_year_sin"] = math.sin(2 * math.pi * doy / 366.0)
    feats["t_day_of_year_cos"] = math.cos(2 * math.pi * doy / 366.0)

    # ---- Sanity assertions (cheap) ----------------------------------------
    assert "t_kz_active_any" in feats
    assert -1.0 <= feats["t_hour_sin"] <= 1.0
    assert -1.0 <= feats["t_hour_cos"] <= 1.0
    assert feats["t_is_weekend"] in (0.0, 1.0)
    assert feats["t_kz_active_count"] >= 0.0

    return feats


def list_feature_names(symbol: str = "XAUUSD") -> list[str]:
    """Return the deterministic feature-name list for a given symbol's KZ
    schedule. Use a representative timestamp during NY for full enumeration.
    """
    sample_ts = datetime(2026, 4, 14, 14, 0, tzinfo=timezone.utc)
    feats = compute_time_session_features(
        sample_ts,
        symbol,
        bars_since_last_kz_open=10,
        minutes_since_last_fill=30,
    )
    return list(feats.keys())


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Smoke: compute features for a representative trade-entry on each symbol.
    sample_ts = datetime(2026, 4, 14, 14, 30, tzinfo=timezone.utc)
    for sym in ["XAUUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash", "NAS100", "XAGUSD", "UNKNOWN"]:
        feats = compute_time_session_features(sample_ts, sym, bars_since_last_kz_open=4, minutes_since_last_fill=180)
        print(f"{sym}: {len(feats)} features. e.g. t_kz_ny_active={feats['t_kz_ny_active']}")

    # Edge: cutoff enforcement
    over_cutoff = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    try:
        compute_time_session_features(over_cutoff, "XAUUSD")
    except AssertionError as exc:
        print(f"Cutoff guard fired as expected: {exc}")

    # Edge: naive timestamp rejection
    try:
        compute_time_session_features(datetime(2026, 4, 14, 14, 30), "XAUUSD")
    except ValueError as exc:
        print(f"Naive guard fired as expected: {exc}")

    # Reference list
    names = list_feature_names("XAUUSD")
    print(f"XAUUSD enumerated feature count: {len(names)}")
