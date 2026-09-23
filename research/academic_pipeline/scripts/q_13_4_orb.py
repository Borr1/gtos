"""
Q-13.4 Opening Range Breakout (ORB) on XAUUSD M15
=================================================
Local-only ($0 API) analysis asking whether an ORB signal carries edge on
XAUUSD beyond what kill-zone time-filtering already provides.

Pre-registered hypothesis (stated BEFORE looking at data, recorded in
`research/academic_pipeline/results/Q-13_4_orb.md` under "Hypotheses"):

    H0: 6-candle continuation WR is ~50% both inside and outside the London
        and NY kill zones. Expected reversal-back-into-OR rate >= 55% within
        12 candles. Expected kill-zone-close mean R <= 0 or |t| < 1.96.
    H1 (PROMOTE): n >= 20 ORB events per KZ AND continuation WR >= 55% with
        Wilson_lo > 55% AND Bonferroni-corrected p < 0.025 (k=2).

Flag: report Pearson r(OR_range, ATR14_H1). If > 0.8 the signal is not
independent from contemporaneous volatility.

Data: data/historical_2026/XAUUSD_M15.csv (Jan 2 - Apr 10 2026, 6420 M15 bars).

Method:
  Opening range = first 4 M15 candles of each trading day inside each
  kill zone (London 07:00-10:30, NY 13:00-17:00 — hours applied directly
  to broker timestamps, matching q_14_non_zone.py convention).
  ORB signal = first M15 candle in that KZ to CLOSE strictly outside
  [OR_low, OR_high]. LONG if close > OR_high, SHORT if close < OR_low.
  Outcomes tracked per event:
    - 6-candle continuation (signed close vs signal close, in trade direction)
    - Reversal back into OR within 12 candles (any touch of OR band)
    - 1R first-touch (R = OR_range; SL = 1R adverse from signal close)
    - R at kill-zone close (hold-to-kz-end)
  Out-of-KZ bucket: on days where no in-KZ breakout occurred, look at the
  first close-outside-OR in the 12 M15 bars AFTER kill-zone end. Same OR.

Stats:
  Wilson 95% CI. Two-sided exact binomial vs 0.50. Bonferroni k=2.
  Pearson r for ATR confound check. One-sample t-test on kz-close R.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
M15_CSV = ROOT / "data" / "historical_2026" / "XAUUSD_M15.csv"
OUT_MD = ROOT / "research" / "academic_pipeline" / "results" / "Q-13_4_orb.md"


# ---------------------------------------------------------------------------
# Constants — kill-zone hours (broker time, matching q_14_non_zone.py)
# ---------------------------------------------------------------------------
# London: 07:00-10:30 -> use 07:00-10:30 inclusive of 10:30 candle
# NY:     13:00-17:00 -> use 13:00-17:00 inclusive of 17:00 candle
KZ_HOURS = {
    "london": {"start": (7, 0), "end": (10, 30)},
    "ny":     {"start": (13, 0), "end": (17, 0)},
}

CONT_HORIZON = 6     # 6 M15 candles forward for continuation WR
REVERSAL_WINDOW = 12  # 12 M15 candles forward to detect return-into-OR
POST_KZ_WINDOW = 12   # bars after KZ end for out-of-KZ bucket
ATR_HOURS = 14        # ATR period on H1


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------
def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def binom_test_p(wins: int, n: int, p0: float = 0.50) -> float:
    if n == 0:
        return 1.0

    def logC(n_, k_):
        return (math.lgamma(n_ + 1) - math.lgamma(k_ + 1) - math.lgamma(n_ - k_ + 1))

    def pmf(k_):
        return math.exp(logC(n, k_) + k_ * math.log(p0) + (n - k_) * math.log(1 - p0))

    obs = pmf(wins)
    p_total = 0.0
    for k in range(n + 1):
        pk = pmf(k)
        if pk <= obs + 1e-15:
            p_total += pk
    return min(1.0, p_total)


def sign_test_p(diffs: list[float]) -> float:
    """Two-sided sign test: count positives vs negatives, ignore zeros."""
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    if n == 0:
        return 1.0
    return binom_test_p(max(pos, neg), n, p0=0.5)


def mean_std(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return (0.0, 0.0)
    m = sum(xs) / len(xs)
    if len(xs) < 2:
        return (m, 0.0)
    v = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return (m, math.sqrt(v))


def pearson_r(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 3 or len(xs) != len(ys):
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def t_stat_one_sample(xs: list[float]) -> tuple[float, float]:
    """Returns (t, approx two-sided p via normal approx for n >= 20, else t, nan)."""
    if len(xs) < 2:
        return (0.0, float("nan"))
    m, s = mean_std(xs)
    if s == 0:
        return (0.0, 1.0)
    t = m / (s / math.sqrt(len(xs)))
    # Normal approx two-sided p (good enough for n>=20; report raw t otherwise)
    if len(xs) >= 20:
        # 1 - Phi(|t|)  *  2
        z = abs(t)
        # Abramowitz & Stegun 26.2.17
        b1 = 0.319381530
        b2 = -0.356563782
        b3 = 1.781477937
        b4 = -1.821255978
        b5 = 1.330274429
        p_coef = 0.2316419
        pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
        t_ = 1.0 / (1.0 + p_coef * z)
        poly = b1 * t_ + b2 * t_**2 + b3 * t_**3 + b4 * t_**4 + b5 * t_**5
        one_tail = pdf * poly
        p_two = 2.0 * one_tail
        return (t, min(1.0, max(0.0, p_two)))
    return (t, float("nan"))


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------
def load_m15(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
            rows.append({
                "ts": ts,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })
    rows.sort(key=lambda r: r["ts"])
    return rows


# ---------------------------------------------------------------------------
# H1 ATR(14) lookup
# ---------------------------------------------------------------------------
def build_h1_atr(m15: list[dict[str, Any]], period: int = ATR_HOURS) -> dict[datetime, float]:
    """Aggregate M15 -> H1 bars, compute 14-hour true-range ATR. Return dict
    keyed on H1 start timestamp."""
    h1_bars: dict[datetime, dict[str, float]] = {}
    for bar in m15:
        key = bar["ts"].replace(minute=0, second=0, microsecond=0)
        if key not in h1_bars:
            h1_bars[key] = {
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
            }
        else:
            h1_bars[key]["high"] = max(h1_bars[key]["high"], bar["high"])
            h1_bars[key]["low"] = min(h1_bars[key]["low"], bar["low"])
            h1_bars[key]["close"] = bar["close"]
    keys = sorted(h1_bars.keys())
    atrs: dict[datetime, float] = {}
    trs: list[float] = []
    prev_close: float | None = None
    for k in keys:
        b = h1_bars[k]
        if prev_close is None:
            tr = b["high"] - b["low"]
        else:
            tr = max(
                b["high"] - b["low"],
                abs(b["high"] - prev_close),
                abs(b["low"] - prev_close),
            )
        trs.append(tr)
        if len(trs) >= period:
            atr = sum(trs[-period:]) / period
            atrs[k] = atr
        prev_close = b["close"]
    return atrs


# ---------------------------------------------------------------------------
# Time/KZ helpers
# ---------------------------------------------------------------------------
def in_kz(ts: datetime, kz: str) -> bool:
    sh, sm = KZ_HOURS[kz]["start"]
    eh, em = KZ_HOURS[kz]["end"]
    t = ts.time()
    start = t.replace(hour=0, minute=0, second=0, microsecond=0).replace(hour=sh, minute=sm)
    end = t.replace(hour=0, minute=0, second=0, microsecond=0).replace(hour=eh, minute=em)
    return start <= t <= end


def kz_end_ts(day: datetime, kz: str) -> datetime:
    eh, em = KZ_HOURS[kz]["end"]
    return day.replace(hour=eh, minute=em, second=0, microsecond=0)


def kz_start_ts(day: datetime, kz: str) -> datetime:
    sh, sm = KZ_HOURS[kz]["start"]
    return day.replace(hour=sh, minute=sm, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# ORB event construction
# ---------------------------------------------------------------------------
def build_orb_events(
    m15: list[dict[str, Any]],
    atrs_h1: dict[datetime, float],
) -> list[dict[str, Any]]:
    """For each (day, kz) pair build:
      - OR = high/low of first 4 M15 candles inside KZ
      - in-KZ ORB event: first subsequent close-outside-OR within KZ
      - out-KZ ORB event (same OR): first close-outside-OR in 12 M15 bars AFTER KZ end
    """
    # Index bars by (date, kz) for quick access
    by_day_kz: dict[tuple[datetime.date, str], list[dict[str, Any]]] = defaultdict(list)
    for b in m15:
        for kz in ("london", "ny"):
            if in_kz(b["ts"], kz):
                by_day_kz[(b["ts"].date(), kz)].append(b)

    # Build fast lookup: date -> list of all M15 bars that day (sorted)
    by_day: dict[datetime.date, list[dict[str, Any]]] = defaultdict(list)
    for b in m15:
        by_day[b["ts"].date()].append(b)

    events: list[dict[str, Any]] = []
    days_with_or = defaultdict(int)

    for (d, kz), kz_bars in sorted(by_day_kz.items()):
        # Need at least 4 OR candles + at least 1 follow-up candle in KZ
        if len(kz_bars) < 5:
            continue
        kz_bars.sort(key=lambda b: b["ts"])
        or_bars = kz_bars[:4]
        or_high = max(b["high"] for b in or_bars)
        or_low = min(b["low"] for b in or_bars)
        or_range = or_high - or_low
        if or_range <= 0:
            continue
        days_with_or[kz] += 1

        # in-KZ ORB: first close-outside within remaining kz bars
        in_event = _first_close_outside(kz_bars[4:], or_high, or_low)
        # Build full forward-series from the day's M15 bars for outcome walks
        day_bars = by_day[d]
        day_bars.sort(key=lambda b: b["ts"])

        # Also need next-day bars if we need bars beyond midnight (rare for these KZs)
        next_day_bars = by_day.get(d + timedelta(days=1), [])
        extended = day_bars + next_day_bars

        # H1 ATR at OR window start (use the H1 hour of OR_bar[0])
        or_h1_key = or_bars[0]["ts"].replace(minute=0, second=0, microsecond=0)
        atr14 = atrs_h1.get(or_h1_key, float("nan"))

        kz_end = kz_end_ts(or_bars[0]["ts"], kz)

        if in_event is not None:
            ev = _finalize_event(
                signal_bar=in_event["bar"],
                bars_after=_bars_after(extended, in_event["bar"]["ts"]),
                or_high=or_high,
                or_low=or_low,
                direction=in_event["dir"],
                kz_end=kz_end,
                atr14_h1=atr14,
                bucket="in_kz",
                day=d,
                kz=kz,
            )
            events.append(ev)

        # out-of-KZ ORB: first close-outside in 12 bars AFTER kz_end
        post_kz_bars = [b for b in extended if b["ts"] > kz_end][:POST_KZ_WINDOW]
        out_event = _first_close_outside(post_kz_bars, or_high, or_low)
        if out_event is not None:
            ev = _finalize_event(
                signal_bar=out_event["bar"],
                bars_after=_bars_after(extended, out_event["bar"]["ts"]),
                or_high=or_high,
                or_low=or_low,
                direction=out_event["dir"],
                kz_end=kz_end,
                atr14_h1=atr14,
                bucket="out_kz",
                day=d,
                kz=kz,
            )
            events.append(ev)

    return events, dict(days_with_or)


def _first_close_outside(
    bars: list[dict[str, Any]], or_high: float, or_low: float
) -> dict[str, Any] | None:
    for b in bars:
        if b["close"] > or_high:
            return {"bar": b, "dir": "long"}
        if b["close"] < or_low:
            return {"bar": b, "dir": "short"}
    return None


def _bars_after(sorted_bars: list[dict[str, Any]], ts: datetime) -> list[dict[str, Any]]:
    return [b for b in sorted_bars if b["ts"] > ts]


def _finalize_event(
    *,
    signal_bar: dict[str, Any],
    bars_after: list[dict[str, Any]],
    or_high: float,
    or_low: float,
    direction: str,
    kz_end: datetime,
    atr14_h1: float,
    bucket: str,
    day: datetime.date,
    kz: str,
) -> dict[str, Any]:
    sig_close = signal_bar["close"]
    or_range = or_high - or_low

    # 6-candle continuation
    cont_win = None
    if len(bars_after) >= CONT_HORIZON:
        fwd_close = bars_after[CONT_HORIZON - 1]["close"]
        if direction == "long":
            cont_win = 1 if fwd_close > sig_close else 0
        else:
            cont_win = 1 if fwd_close < sig_close else 0

    # Reversal back into OR within 12 candles
    rev = 0
    for b in bars_after[:REVERSAL_WINDOW]:
        # Any bar whose range touches the OR band counts
        if b["low"] <= or_high and b["high"] >= or_low:
            rev = 1
            break

    # 1R first-touch (R = or_range); walk bar by bar
    tp = sig_close + or_range if direction == "long" else sig_close - or_range
    sl = sig_close - or_range if direction == "long" else sig_close + or_range
    one_r_outcome = None  # 1=TP hit, 0=SL hit, None=neither within KZ window (use 12-bar)
    one_r_window = bars_after[:REVERSAL_WINDOW]  # same 12-bar window for consistency
    for b in one_r_window:
        hit_tp = b["high"] >= tp if direction == "long" else b["low"] <= tp
        hit_sl = b["low"] <= sl if direction == "long" else b["high"] >= sl
        if hit_tp and hit_sl:
            # Both in same bar — conservative: call it SL
            one_r_outcome = 0
            break
        if hit_tp:
            one_r_outcome = 1
            break
        if hit_sl:
            one_r_outcome = 0
            break

    # R at kill-zone close (for in-KZ events only — out-of-KZ has no kz_end reference)
    kz_close_r = None
    if bars_after:
        # Find the last bar at or before kz_end
        kz_last = None
        for b in bars_after:
            if b["ts"] <= kz_end:
                kz_last = b
            else:
                break
        if kz_last is not None and or_range > 0:
            pnl = (kz_last["close"] - sig_close) if direction == "long" else (sig_close - kz_last["close"])
            kz_close_r = pnl / or_range

    return {
        "day": day,
        "kz": kz,
        "bucket": bucket,
        "direction": direction,
        "signal_ts": signal_bar["ts"],
        "signal_close": sig_close,
        "or_high": or_high,
        "or_low": or_low,
        "or_range": or_range,
        "atr14_h1": atr14_h1,
        "cont_win": cont_win,
        "reversal": rev,
        "one_r_outcome": one_r_outcome,
        "kz_close_r": kz_close_r,
        "bars_to_breakout": None,  # set by caller if wanted
    }


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------
def agg_counts(events: list[dict[str, Any]], days_with_or: dict) -> list[dict[str, Any]]:
    rows = []
    for kz in ("london", "ny"):
        for bucket in ("in_kz", "out_kz"):
            evs = [e for e in events if e["kz"] == kz and e["bucket"] == bucket]
            rows.append({
                "kz": kz,
                "bucket": bucket,
                "days_with_or": days_with_or.get(kz, 0),
                "events": len(evs),
            })
    return rows


def agg_continuation(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for kz in ("london", "ny"):
        for bucket in ("in_kz", "out_kz"):
            evs = [e for e in events if e["kz"] == kz and e["bucket"] == bucket and e["cont_win"] is not None]
            wins = sum(e["cont_win"] for e in evs)
            n = len(evs)
            wr = wins / n if n > 0 else 0.0
            lo, hi = wilson_ci(wins, n)
            p_raw = binom_test_p(wins, n, p0=0.50) if n > 0 else 1.0
            p_bonf = min(1.0, p_raw * 2)
            flag = ""
            if n >= 20 and lo > 0.55 and p_bonf < 0.025:
                flag = "PROMOTE-candidate"
            elif n >= 20 and wr < 0.55 and hi < 0.60:
                flag = "KILL-candidate"
            rows.append({
                "kz": kz, "bucket": bucket, "n": n, "wins": wins,
                "wr": wr, "lo": lo, "hi": hi, "p_raw": p_raw, "p_bonf": p_bonf,
                "flag": flag,
            })
    return rows


def agg_reversal(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for kz in ("london", "ny"):
        for bucket in ("in_kz", "out_kz"):
            evs = [e for e in events if e["kz"] == kz and e["bucket"] == bucket]
            revs = sum(e["reversal"] for e in evs)
            n = len(evs)
            rr = revs / n if n > 0 else 0.0
            lo, hi = wilson_ci(revs, n)
            rows.append({"kz": kz, "bucket": bucket, "n": n, "revs": revs, "rr": rr, "lo": lo, "hi": hi})
    return rows


def agg_kzr(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for kz in ("london", "ny"):
        for bucket in ("in_kz", "out_kz"):
            evs = [e for e in events if e["kz"] == kz and e["bucket"] == bucket and e["kz_close_r"] is not None]
            xs = [e["kz_close_r"] for e in evs]
            m, s = mean_std(xs)
            t, p = t_stat_one_sample(xs)
            rows.append({"kz": kz, "bucket": bucket, "n": len(xs), "mean": m, "sd": s, "t": t, "p": p})
    return rows


def agg_1r(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for kz in ("london", "ny"):
        for bucket in ("in_kz", "out_kz"):
            evs = [e for e in events if e["kz"] == kz and e["bucket"] == bucket and e["one_r_outcome"] is not None]
            wins = sum(1 for e in evs if e["one_r_outcome"] == 1)
            hits = len(evs)
            wr = wins / hits if hits > 0 else 0.0
            lo, hi = wilson_ci(wins, hits)
            rows.append({"kz": kz, "bucket": bucket, "wins": wins, "hits": hits, "wr": wr, "lo": lo, "hi": hi})
    return rows


def agg_paired_vs_notrade(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for kz in ("london", "ny"):
        evs = [e for e in events if e["kz"] == kz and e["bucket"] == "in_kz" and e["kz_close_r"] is not None]
        xs = [e["kz_close_r"] for e in evs]
        if not xs:
            rows.append({"kz": kz, "n": 0, "mean": 0.0, "frac_pos": 0.0, "p": 1.0})
            continue
        m, _ = mean_std(xs)
        pos = sum(1 for x in xs if x > 0)
        p = sign_test_p(xs)  # vs 0 baseline
        rows.append({"kz": kz, "n": len(xs), "mean": m, "frac_pos": pos / len(xs), "p": p})
    return rows


def agg_atr_confound(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for kz in ("london", "ny"):
        for bucket in ("in_kz", "out_kz"):
            evs = [
                e for e in events
                if e["kz"] == kz and e["bucket"] == bucket and not math.isnan(e["atr14_h1"])
            ]
            xs = [e["or_range"] for e in evs]
            ys = [e["atr14_h1"] for e in evs]
            r = pearson_r(xs, ys)
            flag = "confound" if abs(r) > 0.8 else ""
            rows.append({"kz": kz, "bucket": bucket, "n": len(evs), "r": r, "flag": flag})
    return rows


def agg_in_vs_out(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Paired within (day, kz): when both in-KZ and out-KZ ORB events exist,
    compare continuation WR."""
    rows = []
    for kz in ("london", "ny"):
        # index by day -> {bucket: event}
        by_day: dict[Any, dict[str, dict[str, Any]]] = defaultdict(dict)
        for e in events:
            if e["kz"] != kz or e["cont_win"] is None:
                continue
            by_day[e["day"]][e["bucket"]] = e
        paired = [d for d, m in by_day.items() if "in_kz" in m and "out_kz" in m]
        if not paired:
            rows.append({"kz": kz, "n": 0, "in_wr": 0.0, "out_wr": 0.0, "delta": 0.0})
            continue
        in_wins = sum(by_day[d]["in_kz"]["cont_win"] for d in paired)
        out_wins = sum(by_day[d]["out_kz"]["cont_win"] for d in paired)
        n = len(paired)
        in_wr = in_wins / n
        out_wr = out_wins / n
        rows.append({"kz": kz, "n": n, "in_wr": in_wr, "out_wr": out_wr, "delta": in_wr - out_wr})
    return rows


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------
def fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def render(
    counts, cont, rev, kzr, oneR, paired, atr, in_out, events,
) -> dict[str, str]:
    # Counts
    lines = []
    for r in counts:
        # bars-to-breakout average per bucket
        sub = [e for e in events if e["kz"] == r["kz"] and e["bucket"] == r["bucket"]]
        # Use indices of bars_after — cheap approx: from signal_ts vs OR first bar
        # (We did not persist this per event — omit and print "-")
        lines.append(
            f"| {r['kz']} | {r['bucket']} | {r['days_with_or']} | {r['events']} | - |"
        )
    TABLE_COUNTS = "\n".join(lines)

    # Continuation
    lines = []
    for r in cont:
        lines.append(
            f"| {r['kz']} | {r['bucket']} | {r['n']} | {r['wins']} | "
            f"{fmt_pct(r['wr'])} | {fmt_pct(r['lo'])} | {fmt_pct(r['hi'])} | "
            f"{r['p_raw']:.4f} | {r['p_bonf']:.4f} | {r['flag']} |"
        )
    TABLE_CONT = "\n".join(lines)

    # Reversal
    lines = []
    for r in rev:
        lines.append(
            f"| {r['kz']} | {r['bucket']} | {r['n']} | {r['revs']} | "
            f"{fmt_pct(r['rr'])} | {fmt_pct(r['lo'])} | {fmt_pct(r['hi'])} |"
        )
    TABLE_REV = "\n".join(lines)

    # KZR
    lines = []
    for r in kzr:
        p = "n/a" if (isinstance(r["p"], float) and math.isnan(r["p"])) else f"{r['p']:.4f}"
        lines.append(
            f"| {r['kz']} | {r['bucket']} | {r['n']} | "
            f"{r['mean']:+.3f} | {r['sd']:.3f} | {r['t']:+.2f} | {p} |"
        )
    TABLE_KZR = "\n".join(lines)

    # 1R
    lines = []
    for r in oneR:
        lines.append(
            f"| {r['kz']} | {r['bucket']} | {r['hits']} | {r['wins']} | {r['hits']} | "
            f"{fmt_pct(r['wr'])} | {fmt_pct(r['lo'])} | {fmt_pct(r['hi'])} |"
        )
    TABLE_1R = "\n".join(lines)

    # Paired vs no-trade
    lines = []
    for r in paired:
        lines.append(
            f"| {r['kz']} | {r['n']} | {r['mean']:+.3f} | "
            f"{fmt_pct(r['frac_pos'])} | {r['p']:.4f} |"
        )
    TABLE_PAIRED = "\n".join(lines)

    # ATR confound
    lines = []
    for r in atr:
        lines.append(
            f"| {r['kz']} | {r['bucket']} | {r['n']} | {r['r']:+.3f} | {r['flag']} |"
        )
    TABLE_ATR = "\n".join(lines)

    # In vs Out
    lines = []
    for r in in_out:
        lines.append(
            f"| {r['kz']} | {r['n']} | {fmt_pct(r['in_wr'])} | "
            f"{fmt_pct(r['out_wr'])} | {r['delta']*100:+.1f}pp |"
        )
    TABLE_INOUT = "\n".join(lines)

    return {
        "{TABLE_COUNTS}": TABLE_COUNTS,
        "{TABLE_CONT}": TABLE_CONT,
        "{TABLE_REV}": TABLE_REV,
        "{TABLE_KZR}": TABLE_KZR,
        "{TABLE_1R}": TABLE_1R,
        "{TABLE_PAIRED}": TABLE_PAIRED,
        "{TABLE_ATR}": TABLE_ATR,
        "{TABLE_INOUT}": TABLE_INOUT,
    }


# ---------------------------------------------------------------------------
# Verdict synthesis (rule-based, applying pre-registered thresholds)
# ---------------------------------------------------------------------------
def synthesize_verdict(cont, rev, kzr, paired, atr, in_out) -> tuple[str, str]:
    promote = []
    kill = []
    defer = []
    confound_flag = any(r["flag"] == "confound" for r in atr)

    # Primary: London, NY continuation in_kz
    primary_cells = [r for r in cont if r["bucket"] == "in_kz"]
    for r in primary_cells:
        if r["n"] < 20:
            defer.append(f"{r['kz']}: underpowered (n={r['n']} < 20)")
        elif r["lo"] > 0.55 and r["p_bonf"] < 0.025:
            promote.append(f"{r['kz']}: WR={fmt_pct(r['wr'])} Wilson_lo={fmt_pct(r['lo'])} p_bonf={r['p_bonf']:.4f}")
        elif r["wr"] < 0.55 and r["hi"] < 0.60:
            kill.append(f"{r['kz']}: WR={fmt_pct(r['wr'])} Wilson_hi={fmt_pct(r['hi'])} — below pre-registered bar")
        else:
            defer.append(f"{r['kz']}: WR={fmt_pct(r['wr'])} CI=[{fmt_pct(r['lo'])}, {fmt_pct(r['hi'])}] — in defer band")

    # Reversal rate (secondary, but pre-registered)
    high_reversal = []
    for r in rev:
        if r["bucket"] == "in_kz" and r["rr"] > 0.55 and r["n"] >= 20:
            high_reversal.append(f"{r['kz']} in_kz reversal rate={fmt_pct(r['rr'])}")

    # Kill-zone-close R t-test
    kzr_negative = []
    for r in kzr:
        if r["bucket"] == "in_kz" and r["n"] >= 20:
            if r["mean"] <= 0 or (isinstance(r["p"], float) and not math.isnan(r["p"]) and abs(r["t"]) < 1.96):
                kzr_negative.append(f"{r['kz']}: mean R={r['mean']:+.3f} t={r['t']:+.2f}")

    verdict_body = []
    if promote:
        headline = "**PROMOTE-candidate**"
        verdict_body.append("Pre-registered PROMOTE threshold MET in at least one kill zone:")
        for msg in promote:
            verdict_body.append(f"  - {msg}")
    elif kill:
        headline = "**KILL**"
        verdict_body.append("Pre-registered KILL threshold met:")
        for msg in kill:
            verdict_body.append(f"  - {msg}")
    else:
        headline = "**DEFER**"
        verdict_body.append("Neither PROMOTE nor KILL threshold met:")
        for msg in defer:
            verdict_body.append(f"  - {msg}")

    if high_reversal:
        verdict_body.append("")
        verdict_body.append("**Reversal rate supports prior (fade > ride):**")
        for m in high_reversal:
            verdict_body.append(f"  - {m}")

    if kzr_negative:
        verdict_body.append("")
        verdict_body.append("**Kill-zone-close R not significantly positive:**")
        for m in kzr_negative:
            verdict_body.append(f"  - {m}")

    if confound_flag:
        verdict_body.append("")
        verdict_body.append(
            "**Volatility confound flag raised** — OR_range correlates > 0.80 "
            "with H1 ATR(14) in at least one bucket. ORB signal is NOT independent "
            "from contemporaneous volatility on this sample."
        )

    # In/out compare
    for r in in_out:
        if r["n"] >= 5:
            verdict_body.append("")
            verdict_body.append(
                f"**{r['kz']}** paired in-KZ vs out-KZ (n={r['n']} days where both "
                f"events exist): in-KZ WR {fmt_pct(r['in_wr'])} vs out-KZ WR "
                f"{fmt_pct(r['out_wr'])} (delta {r['delta']*100:+.1f}pp)."
            )

    text = headline + "\n\n" + "\n".join(verdict_body)

    # Next steps
    next_steps = []
    if headline.strip("*") == "DEFER":
        next_steps.append(
            "1. Extend historical window backward (pre-2026) to get n >= 50 events "
            "per bucket before re-running. 3.3 months is not enough to rule out a "
            "modest edge."
        )
        next_steps.append(
            "2. Before any promotion, compare ORB continuation WR against an "
            "ATR-matched random-direction null to rule out the volatility confound."
        )
        next_steps.append(
            "3. Shadow-log only (no production action). ORB is a ride-the-impulse "
            "policy and directly conflicts with the validated fade-the-cascade OB-retest "
            "edge."
        )
    elif headline.strip("*") == "KILL":
        next_steps.append(
            "1. Do not pursue ORB as an additional entry mechanism. Data is consistent "
            "with the pre-registered null."
        )
        next_steps.append(
            "2. Close the hypothesis. Keep the existing T7 C-gate + OB retest policy."
        )
    else:
        next_steps.append(
            "1. Before any deployment, re-validate on a 12+ month out-of-sample "
            "historical window and compute an ATR-matched bootstrap null."
        )
        next_steps.append(
            "2. Run shadow-log mode live for 60+ trading days before any policy change; "
            "ORB conflicts in direction with the validated OB-retest edge and must be "
            "compared against it trade-by-trade before coexistence is allowed."
        )

    next_steps.append(
        "4. If ORB is ever pursued, schema must record `entry_time` and the OR "
        "identifier alongside any logged trade so the analysis can be re-run on "
        "live data without further proxies."
    )

    return text, "\n".join(next_steps)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"[Q-13.4] Loading M15 data from {M15_CSV}")
    m15 = load_m15(M15_CSV)
    print(f"[Q-13.4] Loaded {len(m15)} M15 candles")

    print(f"[Q-13.4] Building H1 ATR({ATR_HOURS}) lookup")
    atrs = build_h1_atr(m15, ATR_HOURS)
    print(f"[Q-13.4] ATR entries: {len(atrs)}")

    print("[Q-13.4] Constructing ORB events")
    events, days_with_or = build_orb_events(m15, atrs)
    print(f"[Q-13.4] ORB events total: {len(events)}")

    counts = agg_counts(events, days_with_or)
    cont = agg_continuation(events)
    rev = agg_reversal(events)
    kzr = agg_kzr(events)
    oneR = agg_1r(events)
    paired = agg_paired_vs_notrade(events)
    atr = agg_atr_confound(events)
    in_out = agg_in_vs_out(events)

    tables = render(counts, cont, rev, kzr, oneR, paired, atr, in_out, events)
    verdict, next_steps = synthesize_verdict(cont, rev, kzr, paired, atr, in_out)

    template = OUT_MD.read_text(encoding="utf-8")
    for k, v in tables.items():
        template = template.replace(k, v)
    template = template.replace("{VERDICT}", verdict)
    template = template.replace("{NEXT_STEPS}", next_steps)
    OUT_MD.write_text(template, encoding="utf-8")
    print(f"[Q-13.4] Wrote results to {OUT_MD}")


if __name__ == "__main__":
    main()
