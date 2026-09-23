"""
STREAM 1: Liquidity Sweep Atlas
Analyzes session-level liquidity sweeps across XAUUSD and GBPUSD.
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from collections import defaultdict
import os

BASE = "/Users/borr/Documents/trading/gold-agent"
OUTPUT = f"{BASE}/knowledge_base_backtest/analysis/microstructure_stream1_sweeps_20260405.json"

# --- CONFIG ---
INSTRUMENTS = {
    "XAUUSD": {
        "file": f"{BASE}/data/historical/XAUUSD_M15.csv",
        "min_sweep_dist": 3.0,       # $3 minimum sweep distance
        "pip_mult": 1.0,             # dollars
        "unit": "$",
    },
    "GBPUSD": {
        "file": f"{BASE}/data/historical/GBPUSD_M15.csv",
        "min_sweep_dist": 0.00015,   # 1.5 pips
        "pip_mult": 10000,           # to convert to pips
        "unit": "pips",
    },
}

ASIAN_START, ASIAN_END = 0, 7       # 00:00 - 06:45 UTC (candles with hour < 7)
LONDON_START, LONDON_END = 7, 12   # 07:00 - 11:45 UTC
NY_START, NY_END = 13, 17          # 13:00 - 16:45 UTC

DOW_NAMES = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}


def load_data(path):
    df = pd.read_csv(path, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)
    df["date"] = df["time"].dt.date
    df["hour"] = df["time"].dt.hour
    df["dow"] = df["time"].dt.dayofweek
    return df


def compute_session_levels(df):
    """For each trading day, compute Asian range, PDH, PDL, ADR."""
    daily = []
    dates = sorted(df["date"].unique())

    daily_hl = df.groupby("date").agg(
        day_high=("high", "max"),
        day_low=("low", "min")
    ).reset_index()
    daily_hl = daily_hl.sort_values("date").reset_index(drop=True)
    daily_hl["daily_range"] = daily_hl["day_high"] - daily_hl["day_low"]
    daily_hl["adr_20"] = daily_hl["daily_range"].rolling(20, min_periods=10).mean()

    daily_dict = daily_hl.set_index("date").to_dict("index")

    for i, d in enumerate(dates):
        day_df = df[df["date"] == d]
        asian = day_df[(day_df["hour"] >= ASIAN_START) & (day_df["hour"] < ASIAN_END)]

        if len(asian) < 2:
            continue

        asian_h = asian["high"].max()
        asian_l = asian["low"].min()
        asian_width = asian_h - asian_l

        if i == 0:
            continue
        prev_date = dates[i - 1]
        if prev_date not in daily_dict:
            continue

        pdh = daily_dict[prev_date]["day_high"]
        pdl = daily_dict[prev_date]["day_low"]

        adr_20 = daily_dict.get(d, {}).get("adr_20", None)
        if adr_20 is None or adr_20 == 0 or np.isnan(adr_20):
            adr_20 = daily_dict.get(prev_date, {}).get("adr_20", None)
        if adr_20 is None or adr_20 == 0 or np.isnan(adr_20):
            asian_pct_adr = None
        else:
            asian_pct_adr = (asian_width / adr_20) * 100

        daily.append({
            "date": str(d),
            "dow": DOW_NAMES.get(day_df["dow"].iloc[0], "?"),
            "asian_h": round(float(asian_h), 5),
            "asian_l": round(float(asian_l), 5),
            "asian_width": round(float(asian_width), 5),
            "pdh": round(float(pdh), 5),
            "pdl": round(float(pdl), 5),
            "adr_20": round(float(adr_20), 5) if adr_20 and not np.isnan(adr_20) else None,
            "asian_pct_adr": round(float(asian_pct_adr), 2) if asian_pct_adr is not None else None,
        })

    return daily


def detect_sweeps(df, session_levels, min_dist):
    """Scan London and NY candles for sweeps of session levels."""
    all_sweeps = []
    levels_map = {sl["date"]: sl for sl in session_levels}

    for date_str, sl in levels_map.items():
        d = pd.Timestamp(date_str).date()
        day_df = df[df["date"] == d].copy()
        if day_df.empty:
            continue

        asian_h = sl["asian_h"]
        asian_l = sl["asian_l"]
        pdh = sl["pdh"]
        pdl = sl["pdl"]

        levels = {
            "asian_h": asian_h,
            "asian_l": asian_l,
            "pdh": pdh,
            "pdl": pdl,
        }

        for kz_name, kz_start, kz_end in [("london", LONDON_START, LONDON_END),
                                            ("ny", NY_START, NY_END)]:
            kz_df = day_df[(day_df["hour"] >= kz_start) & (day_df["hour"] < kz_end)]
            if kz_df.empty:
                continue

            kz_start_time = kz_df["time"].iloc[0]

            for idx_pos, (idx, row) in enumerate(kz_df.iterrows()):
                candle_open = row["open"]
                candle_close = row["close"]
                candle_high = row["high"]
                candle_low = row["low"]
                candle_body_top = max(candle_open, candle_close)
                candle_body_bot = min(candle_open, candle_close)

                for level_name, level_val in levels.items():
                    sweep_above = level_name in ("asian_h", "pdh")

                    if sweep_above:
                        if candle_high > level_val + min_dist:
                            wick_dist = candle_high - level_val
                            if candle_body_top <= level_val:
                                sweep_type = "rejection"
                            else:
                                sweep_type = "breakout"

                            next_dir = None
                            next_idx = idx_pos + 1
                            if next_idx < len(kz_df):
                                next_row = kz_df.iloc[next_idx]
                                if next_row["close"] > next_row["open"]:
                                    next_dir = "up"
                                elif next_row["close"] < next_row["open"]:
                                    next_dir = "down"
                                else:
                                    next_dir = "flat"

                            mins_into_kz = (row["time"] - kz_start_time).total_seconds() / 60

                            all_sweeps.append({
                                "date": date_str,
                                "dow": sl["dow"],
                                "sweep_time": str(row["time"]),
                                "level_swept": level_name,
                                "level_value": round(float(level_val), 5),
                                "sweep_type": sweep_type,
                                "wick_distance": round(float(wick_dist), 5),
                                "kz": kz_name,
                                "mins_into_kz": round(float(mins_into_kz), 1),
                                "next_candle_dir": next_dir,
                            })
                    else:
                        if candle_low < level_val - min_dist:
                            wick_dist = level_val - candle_low
                            if candle_body_bot >= level_val:
                                sweep_type = "rejection"
                            else:
                                sweep_type = "breakout"

                            next_dir = None
                            next_idx = idx_pos + 1
                            if next_idx < len(kz_df):
                                next_row = kz_df.iloc[next_idx]
                                if next_row["close"] > next_row["open"]:
                                    next_dir = "up"
                                elif next_row["close"] < next_row["open"]:
                                    next_dir = "down"
                                else:
                                    next_dir = "flat"

                            mins_into_kz = (row["time"] - kz_start_time).total_seconds() / 60

                            all_sweeps.append({
                                "date": date_str,
                                "dow": sl["dow"],
                                "sweep_time": str(row["time"]),
                                "level_swept": level_name,
                                "level_value": round(float(level_val), 5),
                                "sweep_type": sweep_type,
                                "wick_distance": round(float(wick_dist), 5),
                                "kz": kz_name,
                                "mins_into_kz": round(float(mins_into_kz), 1),
                                "next_candle_dir": next_dir,
                            })

    return all_sweeps


def deduplicate_sweeps(sweeps):
    """Keep only first sweep per level/kz/day."""
    seen = set()
    deduped = []
    for s in sorted(sweeps, key=lambda x: x["sweep_time"]):
        key = (s["date"], s["kz"], s["level_swept"])
        if key not in seen:
            seen.add(key)
            deduped.append(s)
    return deduped


def build_frequency_tables(sweeps):
    """Level | Total Sweeps | Rejection % | Breakout % | Avg Time (mins into KZ)"""
    tables = {}
    for group_key in ["by_level", "by_level_kz", "by_level_dow"]:
        tables[group_key] = {}

    for s in sweeps:
        level = s["level_swept"]
        kz = s["kz"]
        dow = s["dow"]
        stype = s["sweep_type"]
        mins = s["mins_into_kz"]

        for key_name, key_val in [("by_level", level),
                                   ("by_level_kz", f"{level}_{kz}"),
                                   ("by_level_dow", f"{level}_{dow}")]:
            if key_val not in tables[key_name]:
                tables[key_name][key_val] = {"total": 0, "rejection": 0, "breakout": 0, "mins_sum": 0}
            tables[key_name][key_val]["total"] += 1
            tables[key_name][key_val][stype] += 1
            tables[key_name][key_val]["mins_sum"] += mins

    for table_name, table in tables.items():
        for k, v in table.items():
            t = v["total"]
            v["rejection_pct"] = round(v["rejection"] / t * 100, 1) if t > 0 else 0
            v["breakout_pct"] = round(v["breakout"] / t * 100, 1) if t > 0 else 0
            v["avg_mins_into_kz"] = round(v["mins_sum"] / t, 1) if t > 0 else 0
            del v["mins_sum"]

    return tables


def analyze_sweep_sequencing(sweeps, session_levels):
    """Double sweeps, full range sweeps, sweep counts per day."""
    day_kz = defaultdict(list)
    for s in sweeps:
        day_kz[(s["date"], s["kz"])].append(s)

    day_all = defaultdict(list)
    for s in sweeps:
        day_all[s["date"]].append(s)

    total_days = len(session_levels)

    double_asian = 0
    double_asian_times = []
    for (d, kz), swps in day_kz.items():
        levels_hit = {s["level_swept"] for s in swps}
        if "asian_h" in levels_hit and "asian_l" in levels_hit:
            double_asian += 1
            h_time = min(s["sweep_time"] for s in swps if s["level_swept"] == "asian_h")
            l_time = min(s["sweep_time"] for s in swps if s["level_swept"] == "asian_l")
            t1 = pd.Timestamp(h_time)
            t2 = pd.Timestamp(l_time)
            diff_mins = abs((t2 - t1).total_seconds()) / 60
            double_asian_times.append(diff_mins)

    full_range = 0
    full_range_times = []
    for d, swps in day_all.items():
        levels_hit = {s["level_swept"] for s in swps}
        if "pdh" in levels_hit and "pdl" in levels_hit:
            full_range += 1
            h_time = min(s["sweep_time"] for s in swps if s["level_swept"] == "pdh")
            l_time = min(s["sweep_time"] for s in swps if s["level_swept"] == "pdl")
            t1 = pd.Timestamp(h_time)
            t2 = pd.Timestamp(l_time)
            diff_mins = abs((t2 - t1).total_seconds()) / 60
            full_range_times.append(diff_mins)

    sweep_counts = defaultdict(int)
    for d in {sl["date"] for sl in session_levels}:
        n = len(day_all.get(d, []))
        sweep_counts[n] += 1

    zero_pct = round(sweep_counts.get(0, 0) / total_days * 100, 1) if total_days > 0 else 0
    one_pct = round(sweep_counts.get(1, 0) / total_days * 100, 1) if total_days > 0 else 0
    two_plus = sum(v for k, v in sweep_counts.items() if k >= 2)
    two_plus_pct = round(two_plus / total_days * 100, 1) if total_days > 0 else 0

    kz_sessions_with_asian_h = len(set((s["date"], s["kz"]) for s in sweeps if s["level_swept"] == "asian_h"))

    return {
        "total_days_analyzed": total_days,
        "double_asian_sweep": {
            "count": double_asian,
            "pct_of_kz_sessions_with_asian_h": round(double_asian / kz_sessions_with_asian_h * 100, 1) if kz_sessions_with_asian_h > 0 else 0,
            "avg_time_between_mins": round(np.mean(double_asian_times), 1) if double_asian_times else None,
            "sample_size": len(double_asian_times),
        },
        "full_range_sweep_pdh_pdl": {
            "count": full_range,
            "pct_of_days": round(full_range / total_days * 100, 1) if total_days > 0 else 0,
            "avg_time_between_mins": round(np.mean(full_range_times), 1) if full_range_times else None,
            "sample_size": len(full_range_times),
        },
        "daily_sweep_distribution": {
            "zero_sweeps_pct": zero_pct,
            "one_sweep_pct": one_pct,
            "two_plus_sweeps_pct": two_plus_pct,
            "zero_sweeps_count": sweep_counts.get(0, 0),
            "one_sweep_count": sweep_counts.get(1, 0),
            "two_plus_count": two_plus,
            "detail": {str(k): v for k, v in sorted(sweep_counts.items())},
        },
    }


def analyze_post_sweep_behavior(df, sweeps, session_levels, pip_mult, min_dist):
    """
    After rejection sweeps, measure:
    - Max Favorable Excursion (MFE) in reversal direction
    - Net move (close of last candle in window vs level)
    - Win rate (net reversal > 0)
    - 1x Asian range hit rate
    """
    levels_map = {sl["date"]: sl for sl in session_levels}
    rejection_sweeps = [s for s in sweeps if s["sweep_type"] == "rejection"]

    # Collectors: key -> timeframe -> list of (mfe, net_move)
    results_by_level = defaultdict(lambda: defaultdict(lambda: {"mfe": [], "net": []}))
    results_by_kz = defaultdict(lambda: defaultdict(lambda: {"mfe": [], "net": []}))
    results_by_level_kz = defaultdict(lambda: defaultdict(lambda: {"mfe": [], "net": []}))

    # Expanded timeframes for more granularity
    timeframes = {"30min": 2, "1hr": 4, "2hr": 8, "3hr": 12}
    asian_range_hits = defaultdict(lambda: {"count": 0, "total": 0})

    # Also track by early vs late in KZ
    results_by_timing = defaultdict(lambda: defaultdict(lambda: {"mfe": [], "net": []}))

    for s in rejection_sweeps:
        sweep_time = pd.Timestamp(s["sweep_time"])
        d = pd.Timestamp(s["date"]).date()

        # Use full df not just day_df, so we can look forward across midnight if needed
        day_df = df[df["date"] == d]
        if day_df.empty:
            continue

        mask = day_df["time"] == sweep_time
        if mask.sum() == 0:
            continue
        sweep_idx = day_df[mask].index[0]
        sweep_pos = day_df.index.get_loc(sweep_idx)

        level_name = s["level_swept"]
        level_val = s["level_value"]
        is_high_sweep = level_name in ("asian_h", "pdh")

        sl = levels_map.get(s["date"])
        if sl is None:
            continue
        asian_width = sl["asian_width"]

        # Timing: early (first 60 min) vs late (after 60 min) in KZ
        timing_key = "early" if s["mins_into_kz"] <= 60 else "late"

        for tf_name, n_candles in timeframes.items():
            end_pos = sweep_pos + n_candles
            if end_pos >= len(day_df):
                continue
            future_slice = day_df.iloc[sweep_pos + 1: end_pos + 1]
            if future_slice.empty:
                continue

            last_close = future_slice.iloc[-1]["close"]

            if is_high_sweep:
                # Reversal direction = down
                mfe = level_val - future_slice["low"].min()
                net_move = level_val - last_close  # positive = closed below level (good)
            else:
                # Reversal direction = up
                mfe = future_slice["high"].max() - level_val
                net_move = last_close - level_val  # positive = closed above level (good)

            mfe_conv = mfe * pip_mult if pip_mult != 1.0 else mfe
            net_conv = net_move * pip_mult if pip_mult != 1.0 else net_move

            for collector, key in [
                (results_by_level, level_name),
                (results_by_kz, s["kz"]),
                (results_by_level_kz, f"{level_name}_{s['kz']}"),
                (results_by_timing, f"{level_name}_{timing_key}"),
            ]:
                collector[key][tf_name]["mfe"].append(mfe_conv)
                collector[key][tf_name]["net"].append(net_conv)

        # 1x Asian range reversal within 3hr
        end_pos_3h = sweep_pos + 12
        if end_pos_3h < len(day_df) and asian_width > 0:
            future_3h = day_df.iloc[sweep_pos + 1: end_pos_3h + 1]
            if not future_3h.empty:
                if is_high_sweep:
                    reversal = level_val - future_3h["low"].min()
                else:
                    reversal = future_3h["high"].max() - level_val

                key = f"{level_name}_{s['kz']}"
                asian_range_hits[key]["total"] += 1
                if reversal >= asian_width:
                    asian_range_hits[key]["count"] += 1

    def summarize(data_dict):
        result = {}
        for group, tfs in data_dict.items():
            result[group] = {}
            for tf, vals in tfs.items():
                mfe_arr = np.array(vals["mfe"])
                net_arr = np.array(vals["net"])
                n = len(mfe_arr)
                if n == 0:
                    continue
                result[group][tf] = {
                    "avg_mfe": round(float(np.mean(mfe_arr)), 2),
                    "median_mfe": round(float(np.median(mfe_arr)), 2),
                    "avg_net_move": round(float(np.mean(net_arr)), 2),
                    "median_net_move": round(float(np.median(net_arr)), 2),
                    "net_positive_pct": round(float((net_arr > 0).sum() / n * 100), 1),
                    "sample_size": n,
                }
        return result

    ar_hits = {}
    for key, v in asian_range_hits.items():
        ar_hits[key] = {
            "total": v["total"],
            "hit_1x_asian_range": v["count"],
            "pct": round(v["count"] / v["total"] * 100, 1) if v["total"] > 0 else 0,
        }

    return {
        "by_level": summarize(results_by_level),
        "by_kz": summarize(results_by_kz),
        "by_level_kz": summarize(results_by_level_kz),
        "by_timing": summarize(results_by_timing),
        "asian_range_reversal_within_3hr": ar_hits,
        "total_rejection_sweeps": len(rejection_sweeps),
    }


def run():
    all_results = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "instruments": list(INSTRUMENTS.keys()),
            "date_range": {},
            "total_days": {},
            "notes": {
                "sweep_definition": "Wick extends beyond level by minimum distance; rejection = body closes back inside level; breakout = body closes beyond",
                "min_sweep_distance": {"XAUUSD": "$3", "GBPUSD": "1.5 pips"},
                "session_times_utc": {"asian": "00:00-07:00", "london": "07:00-12:00", "ny": "13:00-17:00"},
                "deduplication": "First sweep per level/kz/day only",
                "post_sweep_mfe": "Max Favorable Excursion = best price in reversal direction during window",
                "post_sweep_net": "Net move = close of last candle in window vs level value; positive = reversal direction",
            }
        },
        "sweep_summary": {},
        "sweep_sequencing": {},
        "post_sweep_behavior": {},
        "daily_data": {},
    }

    for inst, cfg in INSTRUMENTS.items():
        print(f"\n{'='*60}")
        print(f"Processing {inst}")
        print(f"{'='*60}")

        df = load_data(cfg["file"])
        print(f"  Loaded {len(df)} candles, {df['date'].nunique()} unique days")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

        all_results["metadata"]["date_range"][inst] = {
            "start": str(df["date"].min()),
            "end": str(df["date"].max()),
        }

        # 1A: Session levels
        session_levels = compute_session_levels(df)
        print(f"  Computed session levels for {len(session_levels)} days")
        all_results["metadata"]["total_days"][inst] = len(session_levels)

        # Asian range stats
        asian_widths = [sl["asian_width"] for sl in session_levels if sl["asian_width"] > 0]
        asian_pcts = [sl["asian_pct_adr"] for sl in session_levels if sl["asian_pct_adr"] is not None]
        print(f"  Asian range: avg width = {np.mean(asian_widths):.4f}, median = {np.median(asian_widths):.4f}")
        if asian_pcts:
            print(f"  Asian range as %ADR: avg = {np.mean(asian_pcts):.1f}%, median = {np.median(asian_pcts):.1f}%")

        # 1B: Sweep detection
        raw_sweeps = detect_sweeps(df, session_levels, cfg["min_sweep_dist"])
        print(f"  Raw sweeps detected: {len(raw_sweeps)}")
        sweeps = deduplicate_sweeps(raw_sweeps)
        print(f"  Deduplicated sweeps (first per level/kz/day): {len(sweeps)}")

        rejections = len([s for s in sweeps if s["sweep_type"] == "rejection"])
        breakouts = len([s for s in sweeps if s["sweep_type"] == "breakout"])
        print(f"  Rejections: {rejections}, Breakouts: {breakouts}")

        # 1C: Frequency tables
        freq_tables = build_frequency_tables(sweeps)
        all_results["sweep_summary"][inst] = freq_tables

        print(f"\n  --- Frequency by Level ---")
        for level, stats in sorted(freq_tables["by_level"].items()):
            print(f"    {level}: {stats['total']} sweeps | Rejection {stats['rejection_pct']}% | Breakout {stats['breakout_pct']}% | Avg {stats['avg_mins_into_kz']}min into KZ")

        print(f"\n  --- Frequency by Level + KZ ---")
        for key, stats in sorted(freq_tables["by_level_kz"].items()):
            print(f"    {key}: {stats['total']} sweeps | Rej {stats['rejection_pct']}% | Bkout {stats['breakout_pct']}%")

        # 1D: Sequencing
        seq = analyze_sweep_sequencing(sweeps, session_levels)
        all_results["sweep_sequencing"][inst] = seq
        print(f"\n  --- Sweep Sequencing ---")
        print(f"    Double Asian sweep: {seq['double_asian_sweep']['count']} ({seq['double_asian_sweep']['pct_of_kz_sessions_with_asian_h']}% of sessions w/ Asian H sweep)")
        if seq['double_asian_sweep']['avg_time_between_mins'] is not None:
            print(f"    Avg time between double sweeps: {seq['double_asian_sweep']['avg_time_between_mins']} min")
        print(f"    Full range PDH+PDL sweep: {seq['full_range_sweep_pdh_pdl']['count']} ({seq['full_range_sweep_pdh_pdl']['pct_of_days']}% of days)")
        print(f"    Days with 0 sweeps: {seq['daily_sweep_distribution']['zero_sweeps_pct']}% ({seq['daily_sweep_distribution']['zero_sweeps_count']})")
        print(f"    Days with 1 sweep: {seq['daily_sweep_distribution']['one_sweep_pct']}% ({seq['daily_sweep_distribution']['one_sweep_count']})")
        print(f"    Days with 2+ sweeps: {seq['daily_sweep_distribution']['two_plus_sweeps_pct']}% ({seq['daily_sweep_distribution']['two_plus_count']})")

        # 1E: Post-sweep behavior
        post = analyze_post_sweep_behavior(df, sweeps, session_levels, cfg["pip_mult"], cfg["min_sweep_dist"])
        all_results["post_sweep_behavior"][inst] = post
        unit = cfg["unit"]
        print(f"\n  --- Post-Sweep Behavior (n={post['total_rejection_sweeps']} rejection sweeps) ---")
        print(f"  By Level (MFE = max favorable excursion, Net = close-based):")
        for level, tfs in sorted(post["by_level"].items()):
            print(f"    {level}:")
            for tf in ["30min", "1hr", "2hr", "3hr"]:
                if tf in tfs and tfs[tf]["sample_size"] > 0:
                    d = tfs[tf]
                    print(f"      {tf}: MFE avg {d['avg_mfe']}{unit} | Net avg {d['avg_net_move']}{unit} | Net+ve {d['net_positive_pct']}% | n={d['sample_size']}")

        print(f"\n  By Timing (early <= 60min vs late > 60min into KZ):")
        for key, tfs in sorted(post["by_timing"].items()):
            print(f"    {key}:")
            for tf in ["1hr", "3hr"]:
                if tf in tfs and tfs[tf]["sample_size"] > 0:
                    d = tfs[tf]
                    print(f"      {tf}: MFE {d['avg_mfe']}{unit} | Net {d['avg_net_move']}{unit} | Net+ve {d['net_positive_pct']}% | n={d['sample_size']}")

        print(f"\n  --- 1x Asian Range Reversal within 3hr ---")
        for key, v in sorted(post["asian_range_reversal_within_3hr"].items()):
            print(f"    {key}: {v['pct']}% ({v['hit_1x_asian_range']}/{v['total']})")

        # Store daily data
        daily_data = []
        sweeps_by_date = defaultdict(list)
        for s in sweeps:
            sweeps_by_date[s["date"]].append(s)

        for sl in session_levels:
            entry = dict(sl)
            entry["sweeps"] = sweeps_by_date.get(sl["date"], [])
            daily_data.append(entry)

        all_results["daily_data"][inst] = daily_data

    # Save
    with open(OUTPUT, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n\nResults saved to {OUTPUT}")
    print(f"File size: {os.path.getsize(OUTPUT) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    run()
