"""K54 v2 — Joint-Model Scout: build unified feature matrix.

Loads the K54 v1 base trade population (439 F11 + 33 trade_index + 110
unified_csv = 582 rows) and computes all 1,219 catalog features at the
trade-entry candle close, organised by 6 families:

    structure (432) + volatility (270) + microstructure (187)
  + time_session (138) + liquidity (129) + regime (63)  =  1,219

Output: research/ml_program/scout/feature_matrix.parquet
        research/ml_program/scout/feature_matrix_meta.json

Discipline
----------
* Cutoff <= 2026-04-28 23:59 UTC enforced upfront (raise if any row exceeds).
* Per-trade BOS time / trade entry timestamp is the candle-close anchor.
* Tuple-keyed dedup (date, symbol, direction, framework, realized_r) per
  audit Section 8 #2; report effective n.
* Read-only OHLCV from data/historical_2026/{SYMBOL}_{TF}.csv.
* Force UTF-8 output everywhere.

NOT a validation gate. The Q1.2 holdout 2026-04-29 -> 2026-05-12 is NEVER
read by this script (data files end at 2026-04-24).
"""

from __future__ import annotations

import io
import json
import math
import sys
import warnings
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Force stdout UTF-8 (Windows cp1252 guard)
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

REPO_ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_DIR = REPO_ROOT / "research" / "ml_program" / "scout"
FEATURES_DIR = REPO_ROOT / "research" / "ml_program" / "scripts" / "features"
OHLCV_DIR = REPO_ROOT / "data" / "historical_2026"

DATA_CUTOFF = datetime(2026, 4, 28, 23, 59, 59, tzinfo=timezone.utc)
HOLDOUT_START = datetime(2026, 4, 29, 0, 0, 0, tzinfo=timezone.utc)

# Wire feature modules
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(FEATURES_DIR))

# Suppress noisy warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import structure  # noqa: E402
import volatility  # noqa: E402
import microstructure as microstr  # noqa: E402
import time_session as tsess  # noqa: E402
import liquidity as liq  # noqa: E402
import regime as regime_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_iso(s):
    if not isinstance(s, str) or not s.strip():
        return None
    raw = s.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        try:
            dt = datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _load_ohlcv(symbol: str) -> dict:
    """Load M15/H1/H4/D1 + M1 OHLCV for one symbol. Cached at module level."""
    cache_key = symbol.upper()
    if cache_key in _OHLCV_CACHE:
        return _OHLCV_CACHE[cache_key]
    out = {}
    sym = symbol
    # Symbol naming: US30_CASH on disk = US30_cash file
    fname = "US30_cash" if symbol.upper() == "US30_CASH" else symbol
    for tf in ("M15", "H1", "H4", "D1", "M1"):
        path = OHLCV_DIR / f"{fname}_{tf}.csv"
        if not path.exists():
            out[tf] = None
            continue
        df = pd.read_csv(path, parse_dates=["time"])
        if df.empty:
            out[tf] = None
            continue
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df = df.sort_values("time").reset_index(drop=True)
        out[tf] = df
    _OHLCV_CACHE[cache_key] = out
    return out


_OHLCV_CACHE = {}


def _ohlcv_to_candle_list(df) -> list:
    """Convert OHLCV DataFrame to Component-2 candle-list-of-dicts."""
    if df is None or df.empty:
        return []
    out = []
    for _, row in df.iterrows():
        ts_str = row["time"].strftime("%Y-%m-%dT%H:%M:%S")
        out.append({
            "time": ts_str,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row.get("volume", 0) or 0),
        })
    return out


_CANDLE_CACHE: dict = {}


def _get_candles_by_tf(symbol: str) -> dict:
    """Return cached candle-list dicts per TF for one symbol."""
    sym = symbol.upper()
    if sym in _CANDLE_CACHE:
        return _CANDLE_CACHE[sym]
    ohlcv = _load_ohlcv(symbol)
    out = {}
    for tf in ("M15", "H1", "H4", "D1"):
        out[tf] = _ohlcv_to_candle_list(ohlcv.get(tf))
    _CANDLE_CACHE[sym] = out
    return out


def _slice_df_until(df, ts):
    """Slice DatetimeIndex DataFrame to rows <= ts."""
    if df is None or df.empty:
        return df
    if not isinstance(df.index, pd.DatetimeIndex):
        return df.loc[df["time"] <= ts]
    return df.loc[df.index <= ts]


# ---------------------------------------------------------------------------
# Trade population loader (mirror of K54 v1 builder, with tuple-keyed dedup)
# ---------------------------------------------------------------------------

INSTRUMENT_CLASS_MAP = {
    "XAUUSD": "metals", "XAGUSD": "metals",
    "US30_cash": "indices", "US30": "indices",
    "NAS100": "indices", "GER40": "indices", "UK100": "indices",
    "USDJPY": "fx", "GBPJPY": "fx", "GBPUSD": "fx", "EURUSD": "fx",
}
KILL_ZONE_HOUR = {"london": 8, "ny": 14, "tokyo": 1, "asia": 1, "asian": 1}


def _normalize_direction(raw):
    s = str(raw or "").strip().upper()
    if s in ("LONG", "BUY"):
        return "LONG"
    if s in ("SHORT", "SELL"):
        return "SHORT"
    return None


def _kz_from_hour(h: int) -> str:
    if 7 <= h < 12: return "london"
    if 13 <= h < 17: return "ny"
    if 0 <= h < 4: return "tokyo"
    return "other"


def load_trades() -> list[dict]:
    """Load + dedupe trades from F11 + trade_index + unified_csv.

    Returns list of unified dicts each with:
        trade_id, source, symbol, direction, framework,
        ts_close (datetime UTC), realized_r, win_label,
        kill_zone, hour_utc, day_of_week,
        entry_price (float or NaN; F11 only)
    """
    rows: list[dict] = []

    # F11
    f11_path = REPO_ROOT / "research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl"
    if f11_path.exists():
        for line in f11_path.open(encoding="utf-8"):
            line = line.strip()
            if not line: continue
            try: rec = json.loads(line)
            except: continue
            bos = rec.get("bos") or {}
            ob = rec.get("ob_retest") or {}
            r = ob.get("realized_r")
            if r is None: continue
            direction = _normalize_direction(bos.get("direction"))
            if direction is None: continue
            bos_time = _parse_iso(bos.get("bos_time"))
            if bos_time is None: continue
            sym = str(bos.get("symbol", "")).upper()
            entry_price = ob.get("entry")
            try:
                entry_price = float(entry_price) if entry_price is not None else math.nan
            except (TypeError, ValueError):
                entry_price = math.nan
            rows.append({
                "trade_id": ob.get("bos_id") or f"{sym}|{bos.get('bos_time')}|f11",
                "source": "f11_mechanical",
                "symbol": sym,
                "direction": direction,
                "framework": "ob_retest",
                "ts_close": bos_time,
                "realized_r": float(r),
                "win_label": 1 if float(r) > 0 else 0,
                "kill_zone": _kz_from_hour(bos_time.hour),
                "hour_utc": bos_time.hour,
                "day_of_week": bos_time.weekday(),
                "entry_price": entry_price,
                "instrument_class": INSTRUMENT_CLASS_MAP.get(sym, "other"),
            })

    # Trade index
    ti_path = REPO_ROOT / "knowledge_base/index/_trade_index.json"
    if ti_path.exists():
        try:
            ti = json.loads(ti_path.read_text(encoding="utf-8"))
        except Exception:
            ti = {}
        for rec in ti.get("trades", []) if isinstance(ti, dict) else []:
            r = rec.get("r_multiple")
            if r is None: continue
            direction = _normalize_direction(rec.get("direction"))
            if direction is None: continue
            sym = str(rec.get("symbol", "")).upper()
            ts = _parse_iso(rec.get("date") or "")
            kz = str(rec.get("kill_zone", "")).strip().lower() or "other"
            hour = KILL_ZONE_HOUR.get(kz, ts.hour if ts else -1)
            # If ts is date-only (no hour), promote to KZ-canonical hour
            if ts is not None and ts.hour == 0 and ts.minute == 0 and kz != "other" and kz in KILL_ZONE_HOUR:
                ts = ts.replace(hour=KILL_ZONE_HOUR[kz])
            if ts is None: continue
            rows.append({
                "trade_id": rec.get("trade_id", f"ti|{rec.get('date')}|{sym}"),
                "source": "trade_index",
                "symbol": sym,
                "direction": direction,
                "framework": str(rec.get("framework", "")).lower() or "ob_retest",
                "ts_close": ts,
                "realized_r": float(r),
                "win_label": 1 if float(r) > 0 else 0,
                "kill_zone": kz,
                "hour_utc": ts.hour,
                "day_of_week": ts.weekday(),
                "entry_price": math.nan,
                "instrument_class": INSTRUMENT_CLASS_MAP.get(sym, "other"),
            })

    # Unified CSV
    csv_path = REPO_ROOT / "research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv"
    if csv_path.exists():
        import csv as _csv
        with csv_path.open(encoding="utf-8") as fh:
            for rec in _csv.DictReader(fh):
                try:
                    r = float(rec.get("r_multiple", "") or "")
                except (TypeError, ValueError):
                    continue
                direction = _normalize_direction(rec.get("direction"))
                if direction is None: continue
                sym = str(rec.get("symbol", "")).upper()
                ts = _parse_iso(rec.get("date") or "")
                kz = str(rec.get("kill_zone", "")).strip().lower() or "other"
                if ts is not None and ts.hour == 0 and ts.minute == 0 and kz in KILL_ZONE_HOUR:
                    ts = ts.replace(hour=KILL_ZONE_HOUR[kz])
                if ts is None: continue
                rows.append({
                    "trade_id": rec.get("trade_id", f"uni|{rec.get('date')}|{sym}"),
                    "source": "unified_csv",
                    "symbol": sym,
                    "direction": direction,
                    "framework": str(rec.get("framework", "")).lower() or "ob_retest",
                    "ts_close": ts,
                    "realized_r": r,
                    "win_label": 1 if r > 0 else 0,
                    "kill_zone": kz,
                    "hour_utc": ts.hour,
                    "day_of_week": ts.weekday(),
                    "entry_price": math.nan,
                    "instrument_class": INSTRUMENT_CLASS_MAP.get(sym, "other"),
                })

    # Tuple-keyed dedup per audit Section 8 #2:
    # (date_str, symbol, direction, framework, realized_r)
    seen: set = set()
    deduped: list[dict] = []
    # Source priority: F11 first (richest geometry)
    src_pri = {"f11_mechanical": 0, "trade_index": 1, "unified_csv": 2}
    rows_sorted = sorted(rows, key=lambda r: (src_pri.get(r["source"], 9), r["trade_id"]))
    for r in rows_sorted:
        date_str = r["ts_close"].strftime("%Y-%m-%d")
        key = (date_str, r["symbol"], r["direction"], r["framework"],
               round(r["realized_r"], 3))
        if key in seen: continue
        seen.add(key)
        deduped.append(r)

    deduped.sort(key=lambda r: (r["ts_close"], r["symbol"], r["trade_id"]))

    # Cutoff guard
    for r in deduped:
        if r["ts_close"] > DATA_CUTOFF:
            raise ValueError(f"trade {r['trade_id']} ts_close {r['ts_close']} > DATA_CUTOFF")
        if r["ts_close"] >= HOLDOUT_START:
            raise ValueError(f"trade {r['trade_id']} hits holdout window")

    return deduped


# ---------------------------------------------------------------------------
# Per-symbol pre-built indices (volatility + regime) for cheap lookup
# ---------------------------------------------------------------------------

def _df_to_dt_index(df):
    """Make a copy with DatetimeIndex on 'time'."""
    if df is None or df.empty:
        return df
    out = df.copy()
    out.index = pd.DatetimeIndex(out["time"], tz="UTC")
    out.index.name = "time"
    out = out.drop(columns=["time"])
    return out


_VOL_CACHE: dict = {}


def _vol_full_for_symbol(symbol: str):
    """Compute full volatility-feature DataFrame for a symbol, indexed by M15.
    Cached per-symbol (one-time cost ~1-2s per symbol)."""
    global _VOL_SCHEMA_NAMES
    sym = symbol.upper()
    if sym in _VOL_CACHE:
        return _VOL_CACHE[sym]
    ohlcv = _load_ohlcv(symbol)
    df_m15 = _df_to_dt_index(ohlcv.get("M15"))
    df_h1 = _df_to_dt_index(ohlcv.get("H1"))
    df_h4 = _df_to_dt_index(ohlcv.get("H4"))
    if df_m15 is None or df_m15.empty:
        _VOL_CACHE[sym] = None
        return None
    out = volatility.compute_all_features(df_m15=df_m15, df_h1=df_h1, df_h4=df_h4)
    _VOL_CACHE[sym] = out
    if not _VOL_SCHEMA_NAMES and out is not None and out.shape[1] > 0:
        _VOL_SCHEMA_NAMES = list(out.columns)
    return out


_VOL_SCHEMA_NAMES: list = []  # populated lazily once any symbol has a vol DataFrame

def _vol_lookup(symbol: str, ts_close: datetime) -> dict:
    """Return volatility features at the M15 candle <= ts_close.
    For trades outside OHLCV coverage, return NaN-filled schema to keep
    the feature matrix rectangular.
    """
    global _VOL_SCHEMA_NAMES
    full = _vol_full_for_symbol(symbol)
    if full is None or full.empty:
        return {f"vol__{c}": math.nan for c in _VOL_SCHEMA_NAMES}
    # cache schema names from first non-empty result
    if not _VOL_SCHEMA_NAMES:
        _VOL_SCHEMA_NAMES = list(full.columns)
    # asof backward
    target = pd.Timestamp(ts_close).tz_convert("UTC") if pd.Timestamp(ts_close).tz is not None else pd.Timestamp(ts_close, tz="UTC")
    sub = full.loc[full.index <= target]
    if sub.empty:
        return {f"vol__{c}": math.nan for c in _VOL_SCHEMA_NAMES}
    row = sub.iloc[-1]
    return {f"vol__{c}": (float(row[c]) if pd.notna(row[c]) else math.nan) for c in full.columns}


# ---------------------------------------------------------------------------
# Microstructure (call per-row; subset to non-tick features for scout)
# ---------------------------------------------------------------------------

NON_TICK_MICRO_NAMES = None  # populated lazy


def _micro_lookup(symbol: str, ts_close: datetime) -> dict:
    """Microstructure features. Tick parquets not loaded -> tick features = NaN."""
    global NON_TICK_MICRO_NAMES
    if NON_TICK_MICRO_NAMES is None:
        # Use all 187 features; tick-required emit NaN sentinels (per module docstring)
        NON_TICK_MICRO_NAMES = list(microstr.FEATURE_NAMES)

    ohlcv = _load_ohlcv(symbol)
    df_m15 = _df_to_dt_index(ohlcv.get("M15"))
    df_h1 = _df_to_dt_index(ohlcv.get("H1"))
    df_h4 = _df_to_dt_index(ohlcv.get("H4"))
    df_m1 = _df_to_dt_index(ohlcv.get("M1"))

    # Slice each up to ts (the module also slices, but explicit slice keeps memory bounded)
    target = pd.Timestamp(ts_close, tz="UTC") if pd.Timestamp(ts_close).tz is None else pd.Timestamp(ts_close).tz_convert("UTC")
    df_m15_s = df_m15.loc[df_m15.index <= target] if df_m15 is not None else None
    df_h1_s = df_h1.loc[df_h1.index <= target] if df_h1 is not None else None
    df_h4_s = df_h4.loc[df_h4.index <= target] if df_h4 is not None else None
    df_m1_s = df_m1.loc[df_m1.index <= target] if df_m1 is not None else None

    if df_m15_s is None or df_m15_s.empty:
        return {f"micro__{n}": math.nan for n in NON_TICK_MICRO_NAMES}

    try:
        out = microstr.compute_microstructure_features(
            df_m15=df_m15_s.reset_index().rename(columns={"time":"time"}),
            df_m1=df_m1_s.reset_index().rename(columns={"time":"time"}) if df_m1_s is not None else pd.DataFrame(columns=["time","open","high","low","close","volume"]),
            df_h1=df_h1_s.reset_index().rename(columns={"time":"time"}) if df_h1_s is not None else pd.DataFrame(columns=["time","open","high","low","close","volume"]),
            df_h4=df_h4_s.reset_index().rename(columns={"time":"time"}) if df_h4_s is not None else pd.DataFrame(columns=["time","open","high","low","close","volume"]),
            ts_close=ts_close,
            symbol=symbol,
            tick_df=None,
            feature_names=NON_TICK_MICRO_NAMES,
        )
        # out is single-row DataFrame indexed by ts_close
        row = out.iloc[0]
        return {f"micro__{c}": (float(row[c]) if pd.notna(row[c]) else math.nan) for c in row.index}
    except ValueError as e:
        # ts_close >= cutoff -> shouldn't happen post pre-filter
        return {f"micro__{n}": math.nan for n in NON_TICK_MICRO_NAMES}
    except Exception as e:
        warnings.warn(f"micro {symbol}@{ts_close}: {type(e).__name__}: {e}")
        return {f"micro__{n}": math.nan for n in NON_TICK_MICRO_NAMES}


# ---------------------------------------------------------------------------
# Liquidity helper
# ---------------------------------------------------------------------------

def _liq_lookup(symbol: str, ts_close: datetime, side: str, current_price: float) -> dict:
    """Build liquidity features for one trade row."""
    candles_by_tf = _get_candles_by_tf(symbol)

    # Build anchor index per TF: last candle with time <= ts_close
    target_str = ts_close.strftime("%Y-%m-%dT%H:%M:%S")
    anchor_idx_by_tf = {}
    sliced_candles_by_tf = {}
    for tf in ("M15", "H1", "H4"):
        full = candles_by_tf.get(tf, [])
        if not full:
            sliced_candles_by_tf[tf] = []
            anchor_idx_by_tf[tf] = -1
            continue
        # Find last index whose time <= target_str
        # Linear scan with break
        idx = -1
        for i, c in enumerate(full):
            ct = c["time"].replace("Z", "").replace("+00:00", "")
            if ct <= target_str:
                idx = i
            else:
                break
        if idx < 0:
            sliced_candles_by_tf[tf] = []
            anchor_idx_by_tf[tf] = -1
        else:
            sliced_candles_by_tf[tf] = full[: idx + 1]
            anchor_idx_by_tf[tf] = idx

    if not math.isfinite(current_price):
        # Fall back to last close on M15
        m15 = sliced_candles_by_tf.get("M15", [])
        if m15:
            current_price = float(m15[-1]["close"])
        else:
            current_price = 0.0

    side_norm = side if side in ("LONG", "SHORT") else "LONG"
    try:
        feats = liq.extract_liquidity_features(
            sliced_candles_by_tf, anchor_idx_by_tf,
            instrument=symbol, side=side_norm, current_price=float(current_price),
        )
        return {f"liq__{k}": (float(v) if v is not None and not (isinstance(v, float) and math.isnan(v)) else math.nan)
                for k, v in feats.items()}
    except Exception as e:
        warnings.warn(f"liq {symbol}@{ts_close}: {type(e).__name__}: {e}")
        # Synthesize NaN row with canonical names
        names = liq.feature_names()
        return {f"liq__{n}": math.nan for n in names}


# ---------------------------------------------------------------------------
# Time/Session helper
# ---------------------------------------------------------------------------

def _tsess_lookup(symbol: str, ts_close: datetime) -> dict:
    feats = tsess.compute_time_session_features(ts_close, symbol)
    return {f"ts__{k}": (float(v) if v is not None and not (isinstance(v, float) and math.isnan(v)) else math.nan)
            for k, v in feats.items()}


# ---------------------------------------------------------------------------
# Regime helper (single shared context)
# ---------------------------------------------------------------------------

_REGIME_CTX = None


def _regime_lookup(symbol: str, ts_close: datetime, side: str) -> dict:
    global _REGIME_CTX
    if _REGIME_CTX is None:
        _REGIME_CTX = regime_mod.RegimeFeatureContext()
    feats = regime_mod.compute_regime_features(symbol, ts_close, side, ctx=_REGIME_CTX)
    return {f"reg__{k}": (float(v) if v is not None and not (isinstance(v, float) and math.isnan(v)) else math.nan)
            for k, v in feats.items()}


# ---------------------------------------------------------------------------
# Structure helper (per-row Component-2)
# ---------------------------------------------------------------------------

def _structure_lookup(symbol: str, ts_close: datetime) -> dict:
    candles_by_tf = _get_candles_by_tf(symbol)
    if not any(candles_by_tf.values()):
        return {}
    ts_str = ts_close.strftime("%Y-%m-%dT%H:%M:%S")
    df = structure.build_structure_features([ts_str], candles_by_tf)
    if df.empty:
        return {}
    row = df.iloc[0]
    return {f"struct__{c}": (float(row[c]) if pd.notna(row[c]) else math.nan) for c in df.columns}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    SCOUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[scout] cwd={Path.cwd()}", flush=True)
    print("[scout] loading trades...", flush=True)
    trades = load_trades()
    print(f"[scout] effective n after dedup: {len(trades)}", flush=True)

    # By-source summary
    src_counter = defaultdict(int)
    sym_counter = defaultdict(int)
    for t in trades:
        src_counter[t["source"]] += 1
        sym_counter[t["symbol"]] += 1
    print(f"[scout] by_source={dict(src_counter)}", flush=True)
    print(f"[scout] by_symbol={dict(sym_counter)}", flush=True)

    # Pre-build volatility cache per symbol
    print("[scout] pre-building volatility cache per symbol...", flush=True)
    for sym in sym_counter.keys():
        _vol_full_for_symbol(sym)
        print(f"  vol cached: {sym}  cols={_VOL_CACHE[sym].shape[1] if _VOL_CACHE[sym] is not None else 'NONE'}", flush=True)

    # Compute features per row
    print("[scout] computing features per trade...", flush=True)
    n_total = len(trades)
    rows: list[dict] = []
    log_every = max(1, n_total // 30)

    for i, t in enumerate(trades):
        sym = t["symbol"]
        ts = t["ts_close"]
        side = t["direction"]
        entry_px = t["entry_price"]

        # For trade_index/unified_csv rows, current_price is NaN -> M15 last close fallback
        current_price = entry_px

        feats: dict = {}

        # 1. Volatility
        feats.update(_vol_lookup(sym, ts))

        # 2. Microstructure (no tick parquets -> tick features NaN)
        feats.update(_micro_lookup(sym, ts))

        # 3. Time/Session
        try:
            feats.update(_tsess_lookup(sym, ts))
        except Exception as e:
            warnings.warn(f"tsess {sym}@{ts}: {type(e).__name__}: {e}")

        # 4. Liquidity
        feats.update(_liq_lookup(sym, ts, side, current_price))

        # 5. Regime
        try:
            feats.update(_regime_lookup(sym, ts, side))
        except Exception as e:
            warnings.warn(f"regime {sym}@{ts}: {type(e).__name__}: {e}")

        # 6. Structure (slowest; 432 features per row)
        try:
            feats.update(_structure_lookup(sym, ts))
        except Exception as e:
            warnings.warn(f"struct {sym}@{ts}: {type(e).__name__}: {e}")

        # Add trade metadata + label
        feats["__trade_id"] = t["trade_id"]
        feats["__source"] = t["source"]
        feats["__symbol"] = sym
        feats["__direction"] = side
        feats["__framework"] = t["framework"]
        feats["__instrument_class"] = t["instrument_class"]
        feats["__date"] = ts.strftime("%Y-%m-%d")
        feats["__ts_close"] = ts.isoformat()
        feats["__hour_utc"] = t["hour_utc"]
        feats["__day_of_week"] = t["day_of_week"]
        feats["__kill_zone"] = t["kill_zone"]
        feats["__realized_r"] = t["realized_r"]
        feats["__win_label"] = t["win_label"]

        rows.append(feats)

        if (i + 1) % log_every == 0 or i + 1 == n_total:
            print(f"[scout] {i+1}/{n_total} rows  ({sym} @ {ts})", flush=True)

    df = pd.DataFrame(rows)
    print(f"[scout] feature matrix shape: {df.shape}", flush=True)

    # Separate metadata + features
    meta_cols = [c for c in df.columns if c.startswith("__")]
    feat_cols = [c for c in df.columns if not c.startswith("__")]
    print(f"[scout] meta_cols={len(meta_cols)} feat_cols={len(feat_cols)}", flush=True)

    # Save parquet (preferred); fallback CSV
    out_pq = SCOUT_DIR / "feature_matrix.parquet"
    try:
        df.to_parquet(out_pq, index=False)
        print(f"[scout] wrote {out_pq}", flush=True)
    except Exception as e:
        print(f"[scout] parquet failed ({e}); writing CSV", flush=True)
        out_csv = SCOUT_DIR / "feature_matrix.csv"
        df.to_csv(out_csv, index=False, encoding="utf-8")
        out_pq = out_csv

    # Meta
    meta = {
        "n_rows": int(df.shape[0]),
        "n_features_total": int(len(feat_cols)),
        "by_family": {
            "structure": sum(1 for c in feat_cols if c.startswith("struct__")),
            "volatility": sum(1 for c in feat_cols if c.startswith("vol__")),
            "microstructure": sum(1 for c in feat_cols if c.startswith("micro__")),
            "time_session": sum(1 for c in feat_cols if c.startswith("ts__")),
            "liquidity": sum(1 for c in feat_cols if c.startswith("liq__")),
            "regime": sum(1 for c in feat_cols if c.startswith("reg__")),
        },
        "by_source": dict(src_counter),
        "by_symbol": dict(sym_counter),
        "out_path": str(out_pq),
        "data_cutoff_utc": DATA_CUTOFF.isoformat(),
        "holdout_start_utc": HOLDOUT_START.isoformat(),
    }
    (SCOUT_DIR / "feature_matrix_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(f"[scout] meta: {json.dumps(meta, indent=2)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
