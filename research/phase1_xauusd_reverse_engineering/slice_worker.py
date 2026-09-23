"""Slice worker — walks a date range, computes MSO per M15 close, simulates
LONG+SHORT entries, labels by MFE/MAE over H1 horizon, writes features.parquet.

Invocation:
    python slice_worker.py --slice-id N --start YYYY-MM-DD --end YYYY-MM-DD \
        --out research/phase1_xauusd_reverse_engineering/slice_N/features.parquet

Self-contained: loads CSVs fresh, imports production `compute_market_state`
with detector_version=v1 forced via config override.

Pure CPU — no API calls.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time as _time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Optional

# Add project root to path — prefer env override (for running against main repo)
_THIS = Path(__file__).resolve()
_DEFAULT_ROOT = _THIS.parents[2]  # worktree root (research/phase1_.../slice_worker.py)
_PROJECT_ROOT = Path(os.environ.get("GTOS_PROJECT_ROOT", str(_DEFAULT_ROOT)))
sys.path.insert(0, str(_PROJECT_ROOT))

import numpy as np
import pandas as pd
import yaml

from scripts.historical_data_loader import (
    LOOKBACK,
    build_raw_data,
    compute_session_levels,
    parse_tradingview_csv,
)
from src.components.market_state import compute_market_state

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

M15_STEP = timedelta(minutes=15)
H1_HORIZONS = {"quick": 4, "primary": 12, "premium": 24, "anti": 8}
MAX_H1_FORWARD = 24  # drives label_unlabeled flag when insufficient forward data

# KZ windows (UTC) for XAUUSD per CLAUDE.md — used for KZ feature only, not a filter.
# We label ALL candles (trader could theoretically set up outside KZ), but kz label is a feature.
KZ_WINDOWS_XAUUSD = [
    ("london", 7, 0, 10, 30),
    ("ny", 13, 0, 17, 0),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_to_utc_dt(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def kz_label(dt: datetime, sym_windows=KZ_WINDOWS_XAUUSD) -> str:
    h, m = dt.hour, dt.minute
    for name, sh, sm, eh, em in sym_windows:
        start = sh * 60 + sm
        end = eh * 60 + em
        cur = h * 60 + m
        if start <= cur < end:
            return name
    return "deadzone"


def atr_rolling(candles: list[dict], window: int = 20) -> float:
    """Simple ATR over *window* bars from the end."""
    if len(candles) < window + 1:
        return 0.0
    trs = []
    for i in range(len(candles) - window, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        prev_c = candles[i - 1]["close"]
        trs.append(max(h - l, abs(h - prev_c), abs(l - prev_c)))
    return sum(trs) / len(trs)


def safe_min_touch(obs: list) -> int:
    return min((ob.touch_count for ob in obs), default=0)


def safe_max_touch(obs: list) -> int:
    return max((ob.touch_count for ob in obs), default=0)


# ---------------------------------------------------------------------------
# SL / label computation
# ---------------------------------------------------------------------------

def compute_sl_and_rdenom(
    close_price: float,
    direction: str,
    mso,
) -> tuple[Optional[float], Optional[float], str]:
    """Return (sl_price, r_denom, source) per label-spec:
    - direction=LONG  → SL at last opposing (=bearish from BUY view → actually
      a BULLISH OB in a bullish context; but spec says "opposing" OB.
      Production rule for a LONG is "last opposing OB far edge" — the last
      BEARISH candle before an upward break (i.e. the bullish-direction OB:
      a demand zone whose HIGH is the entry and LOW is the SL).
      → SL = nearest unmitigated bullish H1 OB's `low` (far edge from LONG
      entry at that OB's high).
    - direction=SHORT → SL = nearest unmitigated bearish H1 OB's `high`.
    - Fallback: 1 * ATR_14 (H1) below/above close.
    """
    h1_obs = mso.timeframes.get("H1")
    h1_atr = mso.timeframes["H1"].atr_14 if "H1" in mso.timeframes else 0.0

    if direction == "LONG":
        cand = [ob for ob in (h1_obs.order_blocks if h1_obs else [])
                if ob.type == "bullish" and not ob.mitigated and ob.low < close_price]
        if cand:
            # closest by distance of OB.high to close_price
            cand.sort(key=lambda ob: abs(close_price - ob.high))
            ob = cand[0]
            sl = ob.low
            r = close_price - sl
            if r > 0:
                return sl, r, "ob"
        if h1_atr > 0:
            return close_price - h1_atr, h1_atr, "atr_fallback"

    elif direction == "SHORT":
        cand = [ob for ob in (h1_obs.order_blocks if h1_obs else [])
                if ob.type == "bearish" and not ob.mitigated and ob.high > close_price]
        if cand:
            cand.sort(key=lambda ob: abs(close_price - ob.low))
            ob = cand[0]
            sl = ob.high
            r = sl - close_price
            if r > 0:
                return sl, r, "ob"
        if h1_atr > 0:
            return close_price + h1_atr, h1_atr, "atr_fallback"

    return None, None, "unlabeled"


def compute_mfe_mae(
    h1_forward: list[dict],
    entry: float,
    direction: str,
    r_denom: float,
    n_bars: int,
) -> tuple[float, float, int, int]:
    """Return (max_mfe_r, max_mae_r, i_mfe_first_2r, i_mae_first_1r).

    i_* = index of first H1 candle whose cum excursion crossed the level,
    or n_bars+1 if never. Pointers are in H1 bar indices (1-based from entry).
    """
    n = min(n_bars, len(h1_forward))
    max_mfe = 0.0
    max_mae = 0.0
    i_mfe_2r = n_bars + 1
    i_mae_1r = n_bars + 1

    for i in range(n):
        h = h1_forward[i]["high"]
        l = h1_forward[i]["low"]
        if direction == "LONG":
            fav = h - entry  # positive excursion (MFE)
            unf = entry - l  # negative excursion (MAE)
        else:  # SHORT
            fav = entry - l
            unf = h - entry
        fav_r = fav / r_denom
        unf_r = unf / r_denom
        if fav_r > max_mfe:
            max_mfe = fav_r
            if max_mfe >= 2.0 and i_mfe_2r > n_bars:
                i_mfe_2r = i + 1
        if unf_r > max_mae:
            max_mae = unf_r
            if max_mae >= 1.0 and i_mae_1r > n_bars:
                i_mae_1r = i + 1
    return max_mfe, max_mae, i_mfe_2r, i_mae_1r


def make_labels(
    h1_forward: list[dict],
    entry: float,
    direction: str,
    r_denom: float,
) -> dict:
    """Compute the 4 locked labels per spec.

    Label is 1 if favorable threshold is hit BEFORE adverse threshold, else 0.
    If we don't have enough H1 forward bars for a horizon, label is None.
    """
    labels = {}
    # For each horizon, walk bar-by-bar tracking first hit of each threshold
    horizons = H1_HORIZONS

    for name, h1n in horizons.items():
        if len(h1_forward) < h1n:
            labels[f"label_{name}"] = None
            labels[f"label_{name}_mfe"] = None
            labels[f"label_{name}_mae"] = None
            continue

        # Walk, track first hit of fav_target and first hit of adv_target
        if name == "primary":
            fav_t = 2.0
            adv_t = 1.0
            positive = "fav_before_adv"
        elif name == "quick":
            fav_t = 1.5
            adv_t = 1.0
            positive = "fav_before_adv"
        elif name == "premium":
            fav_t = 3.0
            adv_t = 1.0
            positive = "fav_before_adv"
        elif name == "anti":
            fav_t = 1.0
            adv_t = 1.0
            positive = "adv_before_fav"

        i_fav = None
        i_adv = None
        max_fav = 0.0
        max_adv = 0.0

        for i in range(h1n):
            bar = h1_forward[i]
            if direction == "LONG":
                fav = (bar["high"] - entry) / r_denom
                adv = (entry - bar["low"]) / r_denom
            else:
                fav = (entry - bar["low"]) / r_denom
                adv = (bar["high"] - entry) / r_denom
            # Intra-bar ambiguity: we do NOT know which extreme prints first.
            # Conservative disambiguation for primary / quick / premium
            # (label=1 = "win"): require the ADVERSE threshold to NOT be hit
            # in the same bar; if both are hit in the same bar, credit adverse
            # first (worst case for labeling a winner).
            if fav >= fav_t:
                # Check same-bar adverse hit
                if adv >= adv_t:
                    # Conservative: assume adverse first for WIN labels,
                    # fav first for ANTI (most conservative in both directions).
                    if positive == "fav_before_adv":
                        if i_adv is None:
                            i_adv = i
                    else:
                        if i_fav is None:
                            i_fav = i
                        if i_adv is None:
                            i_adv = i  # anti's adv threshold met too
                else:
                    if i_fav is None:
                        i_fav = i
            if adv >= adv_t and i_adv is None:
                i_adv = i
            max_fav = max(max_fav, fav)
            max_adv = max(max_adv, adv)
            # Early exit if both resolved
            if i_fav is not None and i_adv is not None:
                break

        # Resolve label per positive
        if positive == "fav_before_adv":
            # WIN if fav hit strictly before adv, or only fav hit at all
            if i_fav is not None and (i_adv is None or i_fav < i_adv):
                labels[f"label_{name}"] = 1
            else:
                labels[f"label_{name}"] = 0
        else:  # anti-pattern: 1 if adv hit before fav
            if i_adv is not None and (i_fav is None or i_adv < i_fav):
                labels[f"label_{name}"] = 1
            else:
                labels[f"label_{name}"] = 0

        labels[f"label_{name}_mfe"] = max_fav
        labels[f"label_{name}_mae"] = max_adv

    return labels


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extract_features(
    mso,
    direction: str,
    close_price: float,
    m15_candles: list[dict],
    h1_candles: list[dict],
    kz: str,
    dt: datetime,
    h1_atr_rolling20d: float,
) -> dict:
    tf = mso.timeframes
    d1 = tf.get("D1")
    h4 = tf.get("H4")
    h1 = tf.get("H1")
    m15 = tf.get("M15")

    def _dir(s):
        if s is None or s.direction == "insufficient_data":
            return "unk"
        return s.direction

    d1_dir = _dir(d1.structure) if d1 else "unk"
    h4_dir = _dir(h4.structure) if h4 else "unk"
    h1_dir = _dir(h1.structure) if h1 else "unk"
    m15_dir = _dir(m15.structure) if m15 else "unk"

    def _align(a, b):
        if a in ("unk", "transitional") or b in ("unk", "transitional"):
            return 0
        return int(a == b)

    d1_h4 = _align(d1_dir, h4_dir)
    h4_h1 = _align(h4_dir, h1_dir)
    h1_m15 = _align(h1_dir, m15_dir)

    # --- OBs ---
    h1_obs_all = h1.order_blocks if h1 else []
    h1_obs_unmit = [ob for ob in h1_obs_all if not ob.mitigated]
    h4_obs_unmit = [ob for ob in (h4.order_blocks if h4 else []) if not ob.mitigated]
    m15_obs_unmit = [ob for ob in (m15.order_blocks if m15 else []) if not ob.mitigated]

    # Opposing OB relative to direction — LONG expects bullish OB below as demand
    if direction == "LONG":
        opp = [ob for ob in h1_obs_unmit if ob.type == "bullish" and ob.low < close_price]
    else:
        opp = [ob for ob in h1_obs_unmit if ob.type == "bearish" and ob.high > close_price]

    opp.sort(key=lambda ob: abs(close_price - ((ob.high + ob.low) / 2)))
    nearest_opp = opp[0] if opp else None

    h1_atr = h1.atr_14 if h1 else 0.0

    opp_dist_pips = None
    opp_dist_atr = None
    opp_touch = None
    opp_causing = None
    opp_ob_age_bars = None
    if nearest_opp and h1_atr > 0:
        if direction == "LONG":
            opp_dist_pips = close_price - nearest_opp.high
        else:
            opp_dist_pips = nearest_opp.low - close_price
        opp_dist_atr = opp_dist_pips / h1_atr
        opp_touch = nearest_opp.touch_count
        opp_causing = nearest_opp.causing_event_type
        try:
            fdt = iso_to_utc_dt(nearest_opp.formation_time)
            opp_ob_age_bars = int((dt - fdt).total_seconds() // 3600)
        except Exception:
            opp_ob_age_bars = None

    # --- FVGs ---
    h1_fvgs_unfilled = [f for f in (h1.fair_value_gaps if h1 else []) if not f.filled]
    m15_fvgs_unfilled = [f for f in (m15.fair_value_gaps if m15 else []) if not f.filled]

    h1_fvg_within_1atr = 0
    if h1_atr > 0:
        for f in h1_fvgs_unfilled:
            mid = f.midpoint
            if abs(close_price - mid) / h1_atr < 1.0:
                h1_fvg_within_1atr = 1
                break

    # --- PD zone ---
    pd_zone = "unk"
    pd_dist_atr = None
    if h1 and h1.premium_discount:
        pd = h1.premium_discount
        if close_price > pd.premium_zone.bottom:
            pd_zone = "premium"
        elif close_price < pd.discount_zone.top:
            pd_zone = "discount"
        else:
            pd_zone = "equilibrium"
        if h1_atr > 0:
            pd_dist_atr = (close_price - pd.equilibrium_50) / h1_atr

    # --- Sweeps + pools ---
    sweeps_n20 = 0
    # detected_sweeps is list of LiquiditySweep with candle_index relative to
    # the M15 candle list that was in the MSO.
    cur_idx = len(m15_candles) - 1
    for s in mso.detected_sweeps:
        if s.candle_index >= cur_idx - 20:
            sweeps_n20 += 1

    # Nearest pool distances (same-side / opposite-side relative to direction)
    pools_same_dist_atr = None
    pools_opp_dist_atr = None
    m15_atr = m15.atr_14 if m15 else 0.0
    if m15_atr > 0:
        same_d = float("inf")
        opp_d = float("inf")
        for p in mso.liquidity_pools:
            if p.side == "high":
                d_ = abs(p.price - close_price) / m15_atr
                if direction == "LONG":
                    if p.price > close_price:
                        if d_ < same_d:
                            same_d = d_
                    else:
                        if d_ < opp_d:
                            opp_d = d_
                else:  # SHORT takes out highs in same direction
                    if p.price > close_price:
                        if d_ < opp_d:
                            opp_d = d_
                    else:
                        if d_ < same_d:
                            same_d = d_
            else:  # low
                d_ = abs(p.price - close_price) / m15_atr
                if direction == "SHORT":
                    if p.price < close_price:
                        if d_ < same_d:
                            same_d = d_
                    else:
                        if d_ < opp_d:
                            opp_d = d_
                else:  # LONG takes out lows in opp direction (recently swept)
                    if p.price < close_price:
                        if d_ < opp_d:
                            opp_d = d_
                    else:
                        if d_ < same_d:
                            same_d = d_
        pools_same_dist_atr = None if same_d == float("inf") else same_d
        pools_opp_dist_atr = None if opp_d == float("inf") else opp_d

    # --- Range pct last 20 ---
    range_pct_20 = None
    if len(m15_candles) >= 20:
        recent = m15_candles[-20:]
        hi = max(c["high"] for c in recent)
        lo = min(c["low"] for c in recent)
        mc = sum(c["close"] for c in recent) / 20
        if mc > 0:
            range_pct_20 = (hi - lo) / mc

    row = {
        # Bookkeeping
        "candle_time": dt.isoformat().replace("+00:00", "Z"),
        "hour_utc": dt.hour,
        "day_of_week": dt.weekday(),
        "kill_zone": kz,
        "direction": direction,
        "close_price": close_price,

        # Structure
        "d1_dir": d1_dir,
        "h4_dir": h4_dir,
        "h1_dir": h1_dir,
        "m15_dir": m15_dir,
        "d1_h4_aligned": d1_h4,
        "h4_h1_aligned": h4_h1,
        "h1_m15_aligned": h1_m15,
        "mtf_alignment_score": d1_h4 + h4_h1 + h1_m15,
        "h1_hh_count": h1.structure.hh_count if h1 else 0,
        "h1_hl_count": h1.structure.hl_count if h1 else 0,
        "h1_lh_count": h1.structure.lh_count if h1 else 0,
        "h1_ll_count": h1.structure.ll_count if h1 else 0,

        # OBs
        "h1_unmit_ob_count": len(h1_obs_unmit),
        "h1_opp_ob_present": int(nearest_opp is not None),
        "h1_opp_ob_dist_pips": opp_dist_pips,
        "h1_opp_ob_dist_atr": opp_dist_atr,
        "h1_opp_ob_touch": opp_touch,
        "h1_opp_ob_causing_event": opp_causing,
        "h1_opp_ob_age_hours": opp_ob_age_bars,
        "h1_ob_min_touch": safe_min_touch(h1_obs_unmit),
        "h1_ob_max_touch": safe_max_touch(h1_obs_unmit),
        "h4_unmit_ob_count": len(h4_obs_unmit),
        "m15_unmit_ob_count": len(m15_obs_unmit),

        # FVGs
        "h1_fvg_unfilled_count": len(h1_fvgs_unfilled),
        "m15_fvg_unfilled_count": len(m15_fvgs_unfilled),
        "h1_fvg_within_1atr": h1_fvg_within_1atr,

        # Volatility / context
        "m15_atr_14": m15_atr,
        "h1_atr_14": h1_atr,
        "d1_atr_14": d1.atr_14 if d1 else 0.0,
        "h1_atr_rolling_20d": h1_atr_rolling20d,
        "atr_regime": (h1_atr / h1_atr_rolling20d) if h1_atr_rolling20d > 0 else None,
        "session_vol_ratio": m15.session_vol_ratio if m15 else None,
        "range_pct_20": range_pct_20,

        # PD zone
        "pd_current_zone": pd_zone,
        "pd_dist_atr": pd_dist_atr,

        # Order flow proxies
        "m15_clv_current": m15.clv_current if m15 else None,
        "m15_clv_avg_5": m15.clv_avg_5 if m15 else None,
        "m15_bvc_buy_fraction": m15.bvc_buy_fraction if m15 else None,
        "m15_net_flow_5": m15.net_flow_5 if m15 else None,

        # Liquidity
        "sweeps_n20": sweeps_n20,
        "pool_same_side_dist_atr": pools_same_dist_atr,
        "pool_opp_side_dist_atr": pools_opp_dist_atr,
        "equal_highs_count": len(mso.equal_highs),
        "equal_lows_count": len(mso.equal_lows),
    }
    return row


# ---------------------------------------------------------------------------
# Worker main
# ---------------------------------------------------------------------------

def _h1_forward(
    h1_all: list[dict],
    m15_close_dt: datetime,
    n: int,
) -> list[dict]:
    """Return next up-to-n H1 candles whose open-time > m15_close_dt.
    MT5 H1 candles have 'time' equal to the bar's OPEN time; the bar closes
    1h later. We want candles whose CLOSE >= m15_close_dt, i.e. open >= m15_close_dt - 1h...
    But we're entering at m15_close_dt. The next H1 bar that can register MFE/MAE
    is the one whose open >= m15_close_dt (strictly the H1 bar that OPENS after
    our entry). Use open_time > m15_close_dt - 59min to include partially-
    overlapping bars conservatively. We'll use open >= m15_close_dt (simpler,
    skips the current partial bar).
    """
    out = []
    for c in h1_all:
        ct = iso_to_utc_dt(c["time"])
        if ct >= m15_close_dt:
            out.append(c)
            if len(out) >= n:
                break
    return out


def run_slice(args):
    t_start = _time.time()
    sym = args.symbol
    data_dir = Path(args.data_dir)

    # Load ALL CSVs
    all_candles = {}
    for tf in ("M15", "H1", "H4", "D1"):
        all_candles[tf] = parse_tradingview_csv(data_dir / f"{sym}_{tf}.csv")
    m15_all = all_candles["M15"]
    h1_all = all_candles["H1"]

    # Config
    with open(_PROJECT_ROOT / "config/agent_config.yaml") as f:
        cfg = yaml.safe_load(f)
    # FORCE detector_version=v1 for all MSO builds (spec requirement)
    cfg.setdefault("market_state", {})["detector_version"] = "v1"

    # Parse slice window
    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)

    # Pre-compute session_levels cache per date (they need full M15 history up to that date)
    # Also pre-compute H1 rolling ATR (20d = ~480 H1 bars ≈ 20*24)
    def rolling_h1_atr(h1_list, up_to_dt, window_days=20):
        # Use last 480 H1 bars before up_to_dt
        idx = 0
        for i, c in enumerate(h1_list):
            if iso_to_utc_dt(c["time"]) > up_to_dt:
                break
            idx = i + 1
        window_bars = window_days * 24
        lo = max(0, idx - window_bars)
        sub = h1_list[lo:idx]
        return atr_rolling(sub, window=min(len(sub) - 1, window_bars)) if len(sub) > 14 else 0.0

    # Collect M15 closes in window
    candles_in_slice = [
        c for c in m15_all
        if start <= iso_to_utc_dt(c["time"]) < end
    ]

    rows = []
    errors = 0
    unlabeled = 0
    walked = 0
    for i, candle in enumerate(candles_in_slice):
        walked += 1
        try:
            dt = iso_to_utc_dt(candle["time"])
            close_price = candle["close"]
            tgt_date = dt.date()

            # Build raw_data for this candle
            session_levels = compute_session_levels(m15_all, tgt_date)
            raw = build_raw_data(
                all_candles, tgt_date, candle["time"], session_levels,
                symbol=sym,
            )
            mso = compute_market_state(raw, cfg)

            # Sliced M15 candles available to MSO
            sliced_m15 = raw["candles"]["M15"]

            # Rolling H1 ATR
            h1_roll = rolling_h1_atr(h1_all, dt)

            # H1 forward bars for MFE/MAE
            h1_fwd = _h1_forward(h1_all, dt, MAX_H1_FORWARD)

            kz = kz_label(dt)

            # For each direction LONG, SHORT
            for direction in ("LONG", "SHORT"):
                sl, r_denom, src = compute_sl_and_rdenom(close_price, direction, mso)
                feats = extract_features(
                    mso, direction, close_price, sliced_m15,
                    h1_all, kz, dt, h1_roll,
                )
                feats["sl_source"] = src
                feats["sl_price"] = sl
                feats["r_denom"] = r_denom

                if src == "unlabeled" or r_denom is None or r_denom <= 0:
                    for name in H1_HORIZONS:
                        feats[f"label_{name}"] = None
                        feats[f"label_{name}_mfe"] = None
                        feats[f"label_{name}_mae"] = None
                    feats["unlabeled"] = 1
                    unlabeled += 1
                else:
                    labels = make_labels(h1_fwd, close_price, direction, r_denom)
                    feats.update(labels)
                    feats["unlabeled"] = 0

                rows.append(feats)
        except Exception as e:
            errors += 1
            # Emit a minimal error row so we can count
            rows.append({
                "candle_time": candle["time"],
                "direction": "ERROR",
                "error": str(e)[:200],
                "unlabeled": 1,
            })

    # Write parquet
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_parquet(out_path, index=False)

    # Summary
    t_end = _time.time()
    label_counts = {}
    for name in H1_HORIZONS:
        col = f"label_{name}"
        if col in df.columns:
            sub = df[df["unlabeled"] == 0] if "unlabeled" in df.columns else df
            positives = int((sub[col] == 1).sum())
            total = int(sub[col].notna().sum())
            label_counts[name] = {"positive": positives, "total_labeled": total,
                                   "rate": (positives / total) if total else None}

    summary = {
        "slice_id": args.slice_id,
        "symbol": sym,
        "start": args.start,
        "end": args.end,
        "candles_walked": walked,
        "rows_written": len(df),
        "errors": errors,
        "unlabeled_rows": unlabeled,
        "label_positive_rates": label_counts,
        "duration_sec": round(t_end - t_start, 1),
        "out_path": str(out_path),
    }
    print("SUMMARY_JSON_START")
    print(json.dumps(summary, indent=2, default=str))
    print("SUMMARY_JSON_END")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slice-id", required=True, type=int)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--symbol", default="XAUUSD")
    ap.add_argument("--data-dir", default=str(_PROJECT_ROOT / "data/historical_2026"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run_slice(args)
