# -*- coding: utf-8 -*-
"""Q-1 DLinear Baseline Gate (H-25, MASTER_BACKLOG Q-1).

Pre-registered hypothesis (BEFORE training):

    DLinear (Zeng et al. 2023 AAAI Oral) trained on GTOS K54 v1 17-feature
    canonical set + 30-bar M15 lookback achieves CPCV K=6/N=2 paired-fixed-HP
    mean AUC within +/-0.01 of canonical K54 v1 (CPCV mean 0.5286 per
    audit/canonical_v1_rerun.md).

    PASS = CPCV mean AUC >= 0.518.
    BORDERLINE = 0.518 - 0.528 (within -0.01 floor; below mid-anchor).
    FAIL = < 0.518.

Decision rule: PASS or BORDERLINE => Q2 sequence-model exploration GO
               FAIL              => NO-GO (shelve sequence-model track).

Architecture (Zeng et al. 2023):
    - Series Decomposition Block:
        trend_t  = MovingAvg(x, kernel=15) using AvgPool1d on the channel
                   dimension with reflect padding.
        season_t = x - trend_t
    - Two parallel Linear projections:
        out_t   = Linear(L=30 -> 1)(trend_t)    per channel
        out_s   = Linear(L=30 -> 1)(season_t)   per channel
        out     = out_t + out_s                 (channels x 1)
    - Pool channels and concatenate K54 v1 17-feature static head;
      project to a single binary logit. Sigmoid for probability.

Input construction (preserves spirit of the brief while making DLinear
trainable):
    - Per trade row, build a 30-bar M15 OHLCV lookback ENDING at the bar
      whose close occurs at or before __ts_close.
    - 17 per-bar feature channels = OHLCV + log-returns + rolling stats
      (matches DLinear's design as a multivariate time-series model).
    - Static 17-feature K54 v1 head (CANONICAL_FEATURES from
      models/k54_v1_canonical/run_canonical_v1_rerun.py) is concatenated
      AFTER the temporal pooling, so the model still sees the K54 v1
      categorical/numerical features the gate is comparing against.

Pool: 528-row scout cohort + 1798-row 2022-2023 backfill = 2,326 max trade rows
      (filtered to rows with sufficient OHLCV lookback coverage).
Methodology: Q1.3 protocol (paired fixed-HP CPCV K=6/N=2, purge 7d, embargo 1d,
DSR + B=1000 null-shuffle + PBO + cross-period).

Outputs:
    research/ml_program/experiments/q1_dlinear_baseline.md
    research/ml_program/experiments/q1_dlinear_results.json

Determinism: random_state=42 across numpy + torch.
Subscription-only (no Anthropic API calls). Reads only data <= 2026-04-28.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
import warnings
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_PARQUET = ROOT / "research/ml_program/scout/feature_matrix.parquet"
V1_FEATURES_FULL = ROOT / "research/ml_program/models/k54_v1_features_full.csv"
COHORT_2022_2023 = ROOT / "data/historical_2022_2023/trade_cohort.csv"

OUT_DIR = ROOT / "research/ml_program/experiments"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_MD = OUT_DIR / "q1_dlinear_baseline.md"
OUT_JSON = OUT_DIR / "q1_dlinear_results.json"

DATA_CUTOFF = pd.Timestamp("2026-04-28T23:59:59+00:00")
LOOKBACK_BARS = 30                     # per brief
M15_INTERVAL = pd.Timedelta(minutes=15)
LOOKBACK_WINDOW = LOOKBACK_BARS * M15_INTERVAL  # 7h30 of M15

# CPCV must match v2 / canonical v1
CPCV_K = 6
CPCV_N = 2
PURGE_DAYS = 7
EMBARGO_DAYS = 1
SEED = 42
N_NULL_SHUFFLES = 1000  # B=1000 per brief

# Anchor (canonical v1 CPCV mean from audit/canonical_v1_rerun.md):
K54_V1_ANCHOR = 0.5286

# DLinear HP grid (paired fixed-HP discipline per memory)
DLINEAR_HP_GRID = [
    {"kernel": k, "hidden": h, "lr": lr, "epochs": ep, "wd": wd}
    for k in (15, 25)
    for h in (32, 64)
    for lr in (1e-3, 5e-4)
    for ep in (40,)
    for wd in (1e-4, 1e-3)
]
# 2x2x2x1x2 = 16 combos (computationally tractable on CPU)

# K54 v1 canonical 17 features (from models/k54_v1_canonical/run_canonical_v1_rerun.py)
CANONICAL_NUM_FEATURES = [
    "hour_utc", "day_of_week", "counter_direction_flag",
    "ob_distance_atr", "ob_age_candles", "displacement_quality_score",
    "fvg_present", "touch_count", "ai_confidence", "walk_level_signal",
]
CANONICAL_CAT_FEATURES = [
    "framework", "instrument_class", "direction_long_short", "kill_zone",
    "setup_grade", "regime_tag", "cross_instrument_xau_dir",
]
CANONICAL_FEATURES = CANONICAL_NUM_FEATURES + CANONICAL_CAT_FEATURES
assert len(CANONICAL_FEATURES) == 17

# Per-instrument M15 OHLCV file map (best-source per data_inventory_audit.md).
# We build a unified per-instrument OHLCV by concatenating historical_2022_2023
# (where available, pre-2024) + historical (the long-history canonical files).
M15_FILES: dict[str, list[Path]] = {
    "XAUUSD":    [ROOT / "data/historical_2022_2023/XAUUSD_M15.csv",
                  ROOT / "data/historical/XAUUSD_M15.csv"],
    "XAGUSD":    [ROOT / "data/historical_2022_2023/XAGUSD_M15.csv",
                  ROOT / "data/XAGUSD_M15.csv"],
    "USDJPY":    [ROOT / "data/historical_2022_2023/USDJPY_M15.csv",
                  ROOT / "data/historical/USDJPY_M15.csv"],
    "GBPJPY":    [ROOT / "data/historical/GBPJPY_M15.csv"],   # already 2022 onward
    "GBPUSD":    [ROOT / "data/historical_2022_2023/GBPUSD_M15.csv",
                  ROOT / "data/historical/GBPUSD_M15.csv"],
    "US30_CASH": [ROOT / "data/historical/US30_cash_M15.csv"],  # already 2022 onward
    "NAS100":    [ROOT / "data/historical_2022_2023/NAS100_M15.csv",
                  ROOT / "data/NAS100_M15.csv"],
}

# Per-bar OHLCV-derived feature channel list (17 channels to match brief)
PER_BAR_CHANNELS = [
    "open", "high", "low", "close", "volume",          # 5
    "logret",                                          # 1
    "hl_range", "oc_range",                            # 2
    "rolling_mean_5", "rolling_std_5",                 # 2
    "rolling_mean_10", "rolling_std_10",               # 2
    "rolling_mean_30", "rolling_std_30",               # 2
    "logvol",                                          # 1
    "ret_z_30",                                        # 1
    "absret",                                          # 1
]
assert len(PER_BAR_CHANNELS) == 17, len(PER_BAR_CHANNELS)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# Data loading
# =====================================================================

def load_cohort_pool() -> pd.DataFrame:
    """Pool 528-row Q1.3 + 1,798-row 2022-2023 backfill into unified cohort."""
    # 1) Q1.3 cohort with K54 v1 features re-aligned by dedup_key
    df_q13 = pd.read_parquet(SCOUT_PARQUET)
    v1_raw = pd.read_csv(V1_FEATURES_FULL)
    v1_raw["date_only"] = v1_raw["date_iso"].astype(str).str[:10]
    v1_raw["dedup_key"] = list(zip(
        v1_raw["date_only"], v1_raw["symbol"], v1_raw["direction_long_short"],
        v1_raw["framework"], v1_raw["realized_r"].round(3),
    ))
    v1_dedup = v1_raw.drop_duplicates(subset="dedup_key", keep="first").copy()
    df_q13["dedup_key"] = list(zip(
        df_q13["__date"].astype(str).str[:10], df_q13["__symbol"],
        df_q13["__direction"], df_q13["__framework"],
        df_q13["__realized_r"].round(3),
    ))
    keys_df = pd.DataFrame({"dedup_key": df_q13["dedup_key"].tolist()})
    v1_aligned = keys_df.merge(v1_dedup, on="dedup_key", how="left")

    cohort_q13 = pd.DataFrame({
        "trade_id":   df_q13["__trade_id"].astype(str).values,
        "source":     df_q13["__source"].astype(str).values,
        "date_iso":   df_q13["__ts_close"].astype(str).values,
        "symbol":     df_q13["__symbol"].astype(str).values,
        "win_label":  df_q13["__win_label"].astype(int).values,
        "realized_r": df_q13["__realized_r"].astype(float).values,
        "cohort":     "q13",
    })
    for c in CANONICAL_FEATURES:
        if c in v1_aligned.columns:
            cohort_q13[c] = v1_aligned[c].values
        else:
            cohort_q13[c] = np.nan

    # 2) 2022-2023 backfill cohort (already has 17 K54 v1 features per row)
    df_22_23 = pd.read_csv(COHORT_2022_2023)
    cohort_22_23 = pd.DataFrame({
        "trade_id":   df_22_23["trade_id"].astype(str).values,
        "source":     df_22_23["source"].astype(str).values,
        "date_iso":   df_22_23["date_iso"].astype(str).values,
        "symbol":     df_22_23["symbol"].astype(str).values,
        "win_label":  df_22_23["win_label"].astype(int).values,
        "realized_r": df_22_23["realized_r"].astype(float).values,
        "cohort":     "backfill_22_23",
    })
    for c in CANONICAL_FEATURES:
        cohort_22_23[c] = df_22_23[c].values if c in df_22_23.columns else np.nan

    # 3) Concatenate; tag a unified date for sorting
    cohort = pd.concat([cohort_q13, cohort_22_23], ignore_index=True)
    cohort["__ts"] = pd.to_datetime(cohort["date_iso"], utc=True, errors="coerce")
    cohort = cohort.dropna(subset=["__ts"]).reset_index(drop=True)
    # Enforce data cutoff
    cohort = cohort[cohort["__ts"] <= DATA_CUTOFF].reset_index(drop=True)
    # Drop rows with missing labels
    cohort = cohort.dropna(subset=["win_label"]).reset_index(drop=True)
    cohort["win_label"] = cohort["win_label"].astype(int)

    print(f"[data] Pooled cohort: {len(cohort)} rows "
          f"({(cohort['cohort']=='q13').sum()} q13 + "
          f"{(cohort['cohort']=='backfill_22_23').sum()} backfill_22_23)")
    print(f"[data] By symbol: {cohort['symbol'].value_counts().to_dict()}")
    print(f"[data] Win rate: {cohort['win_label'].mean():.4f}")
    return cohort


def load_m15_ohlcv(symbol: str) -> pd.DataFrame | None:
    """Load + concatenate M15 OHLCV files for a symbol; return UTC-indexed."""
    paths = M15_FILES.get(symbol.upper())
    if paths is None:
        # Try US30 alias
        if symbol.upper() in ("US30", "US30_CASH", "US30CASH"):
            paths = M15_FILES.get("US30_CASH")
        else:
            return None
    if paths is None:
        return None
    frames = []
    for p in paths:
        if not p.exists():
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        # First column is time
        time_col = df.columns[0]
        df = df.rename(columns={time_col: "time"})
        # Standard 6-col OHLCV; some files have trailing extras; keep first 6
        keep = ["time", "open", "high", "low", "close", "volume"]
        for c in keep:
            if c not in df.columns:
                df[c] = np.nan
        df = df[keep].copy()
        df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
        df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
        frames.append(df)
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True).drop_duplicates("time", keep="last")
    out = out.sort_values("time").reset_index(drop=True).set_index("time")
    # Drop bars with non-finite close
    out = out[out["close"].notna() & (out["close"] > 0)]
    return out


def build_per_bar_features(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Compute the 17 per-bar feature channels."""
    df = ohlcv.copy()
    o, h, l, c, v = df["open"], df["high"], df["low"], df["close"], df["volume"].fillna(0)
    out = pd.DataFrame(index=df.index)
    out["open"] = o.astype(float)
    out["high"] = h.astype(float)
    out["low"] = l.astype(float)
    out["close"] = c.astype(float)
    out["volume"] = v.astype(float)
    logret = np.log(c / c.shift(1)).fillna(0.0)
    out["logret"] = logret
    out["hl_range"] = (h - l).astype(float).fillna(0.0)
    out["oc_range"] = (c - o).astype(float).fillna(0.0)
    out["rolling_mean_5"] = c.rolling(5, min_periods=1).mean().astype(float)
    out["rolling_std_5"] = c.rolling(5, min_periods=2).std().fillna(0.0).astype(float)
    out["rolling_mean_10"] = c.rolling(10, min_periods=1).mean().astype(float)
    out["rolling_std_10"] = c.rolling(10, min_periods=2).std().fillna(0.0).astype(float)
    out["rolling_mean_30"] = c.rolling(30, min_periods=1).mean().astype(float)
    out["rolling_std_30"] = c.rolling(30, min_periods=2).std().fillna(0.0).astype(float)
    out["logvol"] = np.log(v.clip(lower=1.0)).astype(float)
    rolling_std_30 = out["rolling_std_30"].replace(0, 1.0)
    out["ret_z_30"] = (logret / (rolling_std_30 / c).replace(0, 1.0)).fillna(0.0)
    out["absret"] = logret.abs().astype(float)
    out = out[PER_BAR_CHANNELS]
    return out


# =====================================================================
# Per-trade tensor construction
# =====================================================================

def build_lookback_tensors(
    cohort: pd.DataFrame, ohlcv_by_symbol: dict[str, pd.DataFrame],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.Series]:
    """Build (n, 30, 17) per-bar tensor + (n, 17) static head + (n,) labels.

    Returns:
        X_seq:   (n_kept, 30, 17) float32
        X_head:  (n_kept, 17)     float32   # K54 v1 canonical features encoded
        y:       (n_kept,)        int       # win_label
        keep:    pd.Series boolean mask in cohort row order
    """
    n = len(cohort)
    X_seq = np.zeros((n, LOOKBACK_BARS, len(PER_BAR_CHANNELS)), dtype=np.float32)
    X_head = np.zeros((n, len(CANONICAL_FEATURES)), dtype=np.float32)
    y = cohort["win_label"].astype(int).values
    keep = np.zeros(n, dtype=bool)

    # Build feature-cache per symbol
    feat_cache: dict[str, pd.DataFrame] = {}
    for sym, ohlcv in ohlcv_by_symbol.items():
        if ohlcv is None or len(ohlcv) == 0:
            continue
        feat_cache[sym] = build_per_bar_features(ohlcv)

    # Encode static head once, vectorized
    head = pd.DataFrame(index=cohort.index)
    for c in CANONICAL_NUM_FEATURES:
        head[c] = pd.to_numeric(cohort[c], errors="coerce").fillna(-1).astype(float)
    for c in CANONICAL_CAT_FEATURES:
        col = cohort[c]
        if col.dtype.kind in "fc":
            vals = col.fillna("__missing__").astype(str)
        else:
            vals = col.fillna("__missing__").astype(str)
        codes = vals.astype("category").cat.codes
        head[c] = codes.astype(float)
    X_head = head[CANONICAL_FEATURES].values.astype(np.float32)

    # Per-row 30-bar lookback
    miss_no_data = 0
    miss_short = 0
    for i in range(n):
        sym = str(cohort["symbol"].iloc[i]).upper()
        # normalize symbol aliases
        if sym in ("US30", "US30CASH"):
            sym = "US30_CASH"
        feats = feat_cache.get(sym)
        if feats is None or len(feats) == 0:
            miss_no_data += 1
            continue
        ts = cohort["__ts"].iloc[i]
        if pd.isna(ts):
            miss_no_data += 1
            continue
        # Ensure tz-aware UTC
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        # Pick the lookback window: bars whose index <= ts
        sub = feats.loc[feats.index <= ts]
        if len(sub) < LOOKBACK_BARS:
            miss_short += 1
            continue
        window = sub.iloc[-LOOKBACK_BARS:].values.astype(np.float32)
        X_seq[i] = window
        keep[i] = True

    print(f"[lookback] kept {keep.sum()}/{n} rows  "
          f"(skipped: no_data={miss_no_data}, short={miss_short})")
    return X_seq[keep], X_head[keep], y[keep], pd.Series(keep, index=cohort.index)


def standardize_seq(X_seq: np.ndarray, train_idx: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-channel mean/std fit on train rows (across n*L flattened); applied
    in-place. Per-instance normalization is done inside the model."""
    flat_train = X_seq[train_idx].reshape(-1, X_seq.shape[-1])
    mu = flat_train.mean(axis=0)
    sigma = flat_train.std(axis=0)
    sigma = np.where(sigma > 1e-9, sigma, 1.0)
    Xn = ((X_seq - mu) / sigma).astype(np.float32)
    return Xn, mu, sigma


def standardize_head(X_head: np.ndarray, train_idx: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mu = X_head[train_idx].mean(axis=0)
    sigma = X_head[train_idx].std(axis=0)
    sigma = np.where(sigma > 1e-9, sigma, 1.0)
    Xn = ((X_head - mu) / sigma).astype(np.float32)
    return Xn, mu, sigma


# =====================================================================
# DLinear model
# =====================================================================

class _MovingAvg(nn.Module):
    """DLinear's moving-average (trend) component (Zeng et al. 2023)."""
    def __init__(self, kernel_size: int):
        super().__init__()
        self.kernel_size = kernel_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, L, C); average across L per channel with reflect padding
        # Reproduce reference impl: pad first/last by (k-1)//2 with reflect
        pad = (self.kernel_size - 1) // 2
        # Permute to (B, C, L) for AvgPool1d
        xp = x.permute(0, 2, 1)
        # Reflect pad
        front = xp[:, :, :1].repeat(1, 1, pad)
        back  = xp[:, :, -1:].repeat(1, 1, pad)
        xp_padded = torch.cat([front, xp, back], dim=-1)
        avg = F.avg_pool1d(xp_padded, kernel_size=self.kernel_size, stride=1)
        return avg.permute(0, 2, 1)  # back to (B, L, C)


class _SeriesDecomp(nn.Module):
    def __init__(self, kernel_size: int):
        super().__init__()
        self.moving_avg = _MovingAvg(kernel_size)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        trend = self.moving_avg(x)
        season = x - trend
        return season, trend


class DLinearClassifier(nn.Module):
    """DLinear adapted for binary classification.

    - Series decomposition (kernel) -> trend + seasonal
    - Two parallel Linear(L -> 1) per channel: pool 30 bars to 1
    - Concat (channels) + static K54 v1 head -> sigmoid logit
    - Per-instance instance-normalization on the temporal axis (Kim et al.
      2022 RevIN-lite) for distribution-shift robustness.
    """
    def __init__(self, lookback: int, n_channels: int, n_static: int,
                 hidden: int, kernel: int):
        super().__init__()
        self.lookback = lookback
        self.n_channels = n_channels
        self.n_static = n_static
        self.decomp = _SeriesDecomp(kernel)

        # Per-channel linear (L -> 1) shared across channels (channel-shared
        # is a common DLinear variant; reduces parameter count)
        self.linear_trend = nn.Linear(lookback, 1, bias=True)
        self.linear_season = nn.Linear(lookback, 1, bias=True)

        # Head MLP: pool from (channels) + static -> hidden -> 1
        self.head_mlp = nn.Sequential(
            nn.Linear(n_channels + n_static, hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, 1),
        )

    def forward(self, x_seq: torch.Tensor, x_head: torch.Tensor) -> torch.Tensor:
        # Per-instance instance-normalization (mean/std along L, per channel)
        mu = x_seq.mean(dim=1, keepdim=True)
        sigma = x_seq.std(dim=1, keepdim=True) + 1e-5
        x_seq_n = (x_seq - mu) / sigma  # (B, L, C)
        season, trend = self.decomp(x_seq_n)
        # Linear over L axis: input shape (B, C, L)
        season_t = season.permute(0, 2, 1)  # (B, C, L)
        trend_t = trend.permute(0, 2, 1)    # (B, C, L)
        out_s = self.linear_season(season_t).squeeze(-1)  # (B, C)
        out_t = self.linear_trend(trend_t).squeeze(-1)    # (B, C)
        pooled = out_s + out_t  # (B, C)
        z = torch.cat([pooled, x_head], dim=1)
        logit = self.head_mlp(z).squeeze(-1)  # (B,)
        return logit


def _train_one_dlinear(
    X_seq_tr: np.ndarray, X_head_tr: np.ndarray, y_tr: np.ndarray,
    X_seq_iv: np.ndarray, X_head_iv: np.ndarray, y_iv: np.ndarray,
    hp: dict, seed: int = SEED,
) -> tuple[DLinearClassifier, float]:
    """Train DLinear with early stopping on inner validation; return best
    model + best inner-val AUC."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cpu")  # subscription-only; CPU is fine for n<3k
    model = DLinearClassifier(
        lookback=LOOKBACK_BARS, n_channels=X_seq_tr.shape[-1],
        n_static=X_head_tr.shape[-1], hidden=hp["hidden"], kernel=hp["kernel"],
    ).to(device)
    opt = torch.optim.AdamW(
        model.parameters(), lr=hp["lr"], weight_decay=hp["wd"],
    )
    bce = nn.BCEWithLogitsLoss()
    Xs_tr = torch.from_numpy(X_seq_tr).float().to(device)
    Xh_tr = torch.from_numpy(X_head_tr).float().to(device)
    yt = torch.from_numpy(y_tr.astype(np.float32)).to(device)
    Xs_iv = torch.from_numpy(X_seq_iv).float().to(device)
    Xh_iv = torch.from_numpy(X_head_iv).float().to(device)
    yi = y_iv.astype(np.float32)

    bs = max(8, len(y_tr) // 8)
    best_auc = -1.0
    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    patience = 8
    no_improve = 0

    for epoch in range(hp["epochs"]):
        model.train()
        perm = np.random.permutation(len(y_tr))
        for k in range(0, len(perm), bs):
            idx = perm[k:k+bs]
            opt.zero_grad()
            logit = model(Xs_tr[idx], Xh_tr[idx])
            loss = bce(logit, yt[idx])
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            iv_logit = model(Xs_iv, Xh_iv).cpu().numpy()
        iv_prob = 1.0 / (1.0 + np.exp(-iv_logit))
        if len(np.unique(yi)) >= 2:
            try:
                auc_iv = roc_auc_score(yi, iv_prob)
            except Exception:
                auc_iv = 0.5
        else:
            auc_iv = 0.5
        if auc_iv > best_auc + 1e-6:
            best_auc = float(auc_iv)
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                break
    model.load_state_dict(best_state)
    return model, best_auc


def _predict_dlinear(model: DLinearClassifier, X_seq: np.ndarray,
                     X_head: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        Xs = torch.from_numpy(X_seq).float()
        Xh = torch.from_numpy(X_head).float()
        logit = model(Xs, Xh).cpu().numpy()
    return 1.0 / (1.0 + np.exp(-logit))


# =====================================================================
# CPCV scaffolding (matches v2 / canonical v1 exactly)
# =====================================================================

def time_indexed_folds(dates: pd.Series, k: int) -> list[np.ndarray]:
    sort_idx = np.argsort(dates.values)
    fold_size = len(sort_idx) // k
    folds: list[np.ndarray] = []
    for i in range(k):
        start = i * fold_size
        end = (i + 1) * fold_size if i < k - 1 else len(sort_idx)
        folds.append(sort_idx[start:end])
    return folds


def cpcv_paths(folds: list[np.ndarray], n: int) -> list[tuple[list[int], list[int]]]:
    k = len(folds)
    paths = []
    for test_combo in combinations(range(k), n):
        train_combo = [i for i in range(k) if i not in test_combo]
        paths.append((train_combo, list(test_combo)))
    return paths


def purge_embargo(
    train_idx: np.ndarray, test_idx_groups: list[np.ndarray],
    dates: pd.Series, purge_days: int, embargo_days: int,
) -> np.ndarray:
    train_dates = pd.to_datetime(dates.iloc[train_idx])
    keep_mask = pd.Series(True, index=train_idx)
    for tg in test_idx_groups:
        test_dates = pd.to_datetime(dates.iloc[tg])
        t_min = test_dates.min() - pd.Timedelta(days=purge_days)
        t_max = test_dates.max() + pd.Timedelta(days=embargo_days)
        in_zone = (train_dates >= t_min) & (train_dates <= t_max)
        keep_mask = keep_mask & ~in_zone.values
    return train_idx[keep_mask.values]


def calibrate(p_iv: np.ndarray, y_iv: np.ndarray, p_te: np.ndarray) -> np.ndarray:
    if len(np.unique(y_iv)) < 2:
        return p_te
    cal = LogisticRegression(max_iter=1000, C=1.0)
    cal.fit(p_iv.reshape(-1, 1), y_iv)
    return cal.predict_proba(p_te.reshape(-1, 1))[:, 1]


def safe_auc(y: np.ndarray, p: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    try:
        return float(roc_auc_score(y, p))
    except Exception:
        return float("nan")


# =====================================================================
# Statistics: B=1000 null shuffle, PBO, DSR, CPCV-honest SE
# =====================================================================

def b1000_null_shuffle(y_all: np.ndarray, p_all: np.ndarray, B: int = N_NULL_SHUFFLES) -> tuple[float, float]:
    """B=1000 label-permutation null. Returns (observed_auc, p_null)."""
    rng = np.random.default_rng(SEED)
    obs = safe_auc(y_all, p_all)
    if not math.isfinite(obs):
        return obs, float("nan")
    n_ge = 0
    for _ in range(B):
        y_perm = rng.permutation(y_all)
        a = safe_auc(y_perm, p_all)
        if math.isfinite(a) and a >= obs:
            n_ge += 1
    return obs, (n_ge + 1) / (B + 1)


def deflated_sharpe(diff_mean: float, diff_std: float, n_paths: int,
                    n_trials: int) -> float:
    """Approx DSR p-value (Bailey-Lopez de Prado 2014). Treat per-path AUC
    diffs as IS Sharpe ratios over n_paths; n_trials = HP grid size."""
    if diff_std <= 0 or n_paths < 2:
        return float("nan")
    sr = diff_mean / diff_std
    # Expected max IS Sharpe under null with n_trials independent trials
    gamma = 0.5772
    e_max = math.sqrt(2 * math.log(max(n_trials, 2))) * (1 - gamma) + \
            gamma * math.sqrt(2 * math.log(max(n_trials, 2)) - 2)
    z_dsr = (sr - e_max) * math.sqrt(n_paths - 1)
    p = 1.0 - stats.norm.cdf(z_dsr)
    return float(p)


def pbo_compute(per_hp_path_aucs: dict[int, list[float]]) -> float:
    """Probability of Backtest Overfitting (Bailey et al. 2017). Standard CSCV
    procedure on the (n_paths x n_trials) AUC matrix."""
    n_hp = len(per_hp_path_aucs)
    n_paths = len(next(iter(per_hp_path_aucs.values())))
    M = np.array([per_hp_path_aucs[h] for h in range(n_hp)])  # (n_hp, n_paths)
    # Generate combinations of half-folds (subset / complement)
    if n_paths < 4 or n_hp < 4:
        return float("nan")
    half = n_paths // 2
    rng = np.random.default_rng(SEED)
    n_tr = 200  # bounded number of CSCV trials
    fails = 0
    valid = 0
    all_idx = list(range(n_paths))
    for _ in range(n_tr):
        subset = sorted(rng.choice(all_idx, size=half, replace=False))
        complement = [i for i in all_idx if i not in subset]
        is_means = M[:, subset].mean(axis=1)
        oos_means = M[:, complement].mean(axis=1)
        if not (np.isfinite(is_means).any() and np.isfinite(oos_means).any()):
            continue
        h_star = int(np.nanargmax(is_means))
        # Rank h_star's OOS performance
        oos_h = oos_means[h_star]
        rank = np.sum(oos_means >= oos_h)
        n = len(oos_means)
        if n <= 1:
            continue
        rel_rank = rank / n
        # logit
        rel_rank = max(min(rel_rank, 1 - 1e-6), 1e-6)
        logit = math.log(rel_rank / (1 - rel_rank))
        if logit < 0:
            fails += 1
        valid += 1
    return float(fails / max(valid, 1))


def cpcv_honest_se(diffs: np.ndarray, rho: float = 0.6429) -> tuple[float, float, float]:
    """Training-overlap-weighted SE per audit/statistical_reevaluation.md.

    SE_cpcv_honest = sqrt(var(diffs)/n * (1 + (n-1)*rho))
    Returns (se, t, p_two_sided).
    """
    n = len(diffs)
    var = float(np.nanvar(diffs, ddof=1))
    se = math.sqrt(var / n * (1 + (n - 1) * rho))
    if se == 0 or not math.isfinite(se):
        return float("nan"), float("nan"), float("nan")
    t = float(np.nanmean(diffs)) / se
    p = 2 * (1 - stats.norm.cdf(abs(t)))
    return se, t, p


# =====================================================================
# Main pipeline
# =====================================================================

def main() -> None:
    t0 = time.time()
    print(f"[start] {utc_now()}")

    # 1) Pool cohort
    cohort = load_cohort_pool()
    n_total = len(cohort)

    # 2) Load OHLCV per symbol
    ohlcv_by_symbol: dict[str, pd.DataFrame] = {}
    for sym in cohort["symbol"].unique():
        ohlcv = load_m15_ohlcv(sym)
        ohlcv_by_symbol[sym] = ohlcv
        if ohlcv is None:
            print(f"  [ohlcv] {sym}: MISSING -- rows from this symbol will be dropped")
        else:
            print(f"  [ohlcv] {sym}: {len(ohlcv)} bars, {ohlcv.index.min()} to {ohlcv.index.max()}")

    # 3) Build lookback tensors + static head
    X_seq, X_head, y, keep = build_lookback_tensors(cohort, ohlcv_by_symbol)
    cohort_kept = cohort[keep.values].reset_index(drop=True)
    n_kept = len(cohort_kept)
    print(f"[cohort] kept {n_kept}/{n_total}; win rate {y.mean():.4f}")

    # 4) Sort by date (CPCV time-indexed folds require sort)
    dates = cohort_kept["__ts"]

    # 5) CPCV scaffolding
    folds = time_indexed_folds(dates, CPCV_K)
    paths = cpcv_paths(folds, CPCV_N)
    n_paths = len(paths)
    print(f"[cpcv] K={CPCV_K} N={CPCV_N} -> {n_paths} paths")

    # 6) Per-HP per-path OOS AUC (paired-fixed-HP discipline)
    print(f"[hp] grid size = {len(DLINEAR_HP_GRID)}")
    hp_path_aucs: dict[int, list[float]] = {h: [] for h in range(len(DLINEAR_HP_GRID))}

    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(
            train_idx_raw, test_groups_list, dates, PURGE_DAYS, EMBARGO_DAYS,
        )

        # Inner train/val split by date (last 1/8)
        train_dates = dates.iloc[train_idx]
        sort_perm = np.argsort(train_dates.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(20, len(train_sorted) // 8)
        inner_val = train_sorted[-n_inner:]
        inner_train = train_sorted[:-n_inner]

        # Per-channel standardization on inner_train only
        Xs_norm, mu_s, sigma_s = standardize_seq(X_seq, inner_train)
        Xh_norm, mu_h, sigma_h = standardize_head(X_head, inner_train)

        Xs_tr = Xs_norm[inner_train]; Xh_tr = Xh_norm[inner_train]; y_tr = y[inner_train]
        Xs_iv = Xs_norm[inner_val];   Xh_iv = Xh_norm[inner_val];   y_iv = y[inner_val]
        Xs_te = Xs_norm[test_idx];    Xh_te = Xh_norm[test_idx];    y_te = y[test_idx]

        for hp_idx, hp in enumerate(DLINEAR_HP_GRID):
            try:
                model, _ = _train_one_dlinear(
                    Xs_tr, Xh_tr, y_tr, Xs_iv, Xh_iv, y_iv, hp, seed=SEED,
                )
                p_iv = _predict_dlinear(model, Xs_iv, Xh_iv)
                p_te = _predict_dlinear(model, Xs_te, Xh_te)
                p_te_cal = calibrate(p_iv, y_iv, p_te)
                a = safe_auc(y_te, p_te_cal)
            except Exception as e:
                print(f"  [hp={hp_idx} path={path_idx}] ERROR {e}")
                a = float("nan")
            hp_path_aucs[hp_idx].append(a)

        elapsed = time.time() - t0
        print(f"  [path {path_idx+1}/{n_paths}] done t={elapsed:.0f}s")

    # 7) Paired fixed-HP selection: pick HP with best mean OOS AUC across paths
    hp_means = np.array([np.nanmean(hp_path_aucs[h]) for h in range(len(DLINEAR_HP_GRID))])
    best_hp_idx = int(np.nanargmax(hp_means))
    best_hp = DLINEAR_HP_GRID[best_hp_idx]
    cpcv_paths_aucs = np.array(hp_path_aucs[best_hp_idx])
    cpcv_mean_auc = float(np.nanmean(cpcv_paths_aucs))
    cpcv_std_auc = float(np.nanstd(cpcv_paths_aucs, ddof=1))
    print(f"[fixed-hp] selected idx={best_hp_idx} {best_hp}")
    print(f"[fixed-hp] CPCV mean AUC = {cpcv_mean_auc:.4f}  std={cpcv_std_auc:.4f}")

    # 8) Re-train at fixed HP per path; collect predictions for B=1000 + DeLong-style stats
    fixed_aucs: list[float] = []
    fixed_diffs_vs_anchor: list[float] = []   # vs K54 v1 anchor (constant)
    fixed_pred_all: list[np.ndarray] = []
    fixed_y_all: list[np.ndarray] = []

    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(
            train_idx_raw, test_groups_list, dates, PURGE_DAYS, EMBARGO_DAYS,
        )
        train_dates = dates.iloc[train_idx]
        sort_perm = np.argsort(train_dates.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(20, len(train_sorted) // 8)
        inner_val = train_sorted[-n_inner:]
        inner_train = train_sorted[:-n_inner]

        Xs_norm, _, _ = standardize_seq(X_seq, inner_train)
        Xh_norm, _, _ = standardize_head(X_head, inner_train)

        Xs_tr = Xs_norm[inner_train]; Xh_tr = Xh_norm[inner_train]; y_tr = y[inner_train]
        Xs_iv = Xs_norm[inner_val];   Xh_iv = Xh_norm[inner_val];   y_iv = y[inner_val]
        Xs_te = Xs_norm[test_idx];    Xh_te = Xh_norm[test_idx];    y_te = y[test_idx]

        model, _ = _train_one_dlinear(
            Xs_tr, Xh_tr, y_tr, Xs_iv, Xh_iv, y_iv, best_hp, seed=SEED,
        )
        p_iv = _predict_dlinear(model, Xs_iv, Xh_iv)
        p_te = _predict_dlinear(model, Xs_te, Xh_te)
        p_te_cal = calibrate(p_iv, y_iv, p_te)
        a = safe_auc(y_te, p_te_cal)
        fixed_aucs.append(a)
        fixed_diffs_vs_anchor.append(a - K54_V1_ANCHOR)
        fixed_pred_all.append(p_te_cal)
        fixed_y_all.append(y_te)

    cpcv_paths_arr = np.array(fixed_aucs)
    cpcv_mean_auc_fixed = float(np.nanmean(cpcv_paths_arr))
    cpcv_std_auc_fixed = float(np.nanstd(cpcv_paths_arr, ddof=1))
    delta = cpcv_mean_auc_fixed - K54_V1_ANCHOR

    # 9) B=1000 null-shuffle on combined predictions
    p_all = np.concatenate(fixed_pred_all)
    y_all = np.concatenate(fixed_y_all)
    obs_auc, p_null = b1000_null_shuffle(y_all, p_all, B=N_NULL_SHUFFLES)

    # 10) DSR
    diffs = np.array(fixed_diffs_vs_anchor)
    dsr_p = deflated_sharpe(
        diff_mean=float(np.nanmean(diffs)),
        diff_std=float(np.nanstd(diffs, ddof=1)),
        n_paths=len(diffs), n_trials=len(DLINEAR_HP_GRID),
    )

    # 11) PBO
    pbo = pbo_compute(hp_path_aucs)

    # 12) CPCV-honest SE
    se_cpcv, t_cpcv, p_cpcv = cpcv_honest_se(diffs)

    # 13) Cross-period sensitivity: re-train+test on 2022-2023 -> 2024-2026 split
    cohort_dates = cohort_kept["__ts"]
    is_2026 = cohort_dates >= pd.Timestamp("2024-01-01T00:00:00+00:00")
    train_xp = np.where(~is_2026)[0]   # 2022-2023
    test_xp = np.where(is_2026)[0]     # 2024-2026
    if len(train_xp) >= 100 and len(test_xp) >= 50:
        # inner val: last 1/8 of train (by date)
        train_sorted_xp = train_xp[np.argsort(cohort_dates.iloc[train_xp].values)]
        n_inner_xp = max(20, len(train_sorted_xp) // 8)
        inner_val_xp = train_sorted_xp[-n_inner_xp:]
        inner_train_xp = train_sorted_xp[:-n_inner_xp]
        Xs_norm_xp, _, _ = standardize_seq(X_seq, inner_train_xp)
        Xh_norm_xp, _, _ = standardize_head(X_head, inner_train_xp)

        model_xp, _ = _train_one_dlinear(
            Xs_norm_xp[inner_train_xp], Xh_norm_xp[inner_train_xp], y[inner_train_xp],
            Xs_norm_xp[inner_val_xp], Xh_norm_xp[inner_val_xp], y[inner_val_xp],
            best_hp, seed=SEED,
        )
        p_iv_xp = _predict_dlinear(model_xp, Xs_norm_xp[inner_val_xp], Xh_norm_xp[inner_val_xp])
        p_te_xp = _predict_dlinear(model_xp, Xs_norm_xp[test_xp], Xh_norm_xp[test_xp])
        p_te_xp_cal = calibrate(p_iv_xp, y[inner_val_xp], p_te_xp)
        cross_period_auc = safe_auc(y[test_xp], p_te_xp_cal)
        cross_period_n_train = int(len(inner_train_xp))
        cross_period_n_test = int(len(test_xp))
    else:
        cross_period_auc = float("nan")
        cross_period_n_train = int(len(train_xp))
        cross_period_n_test = int(len(test_xp))

    # 14) Verdict
    if cpcv_mean_auc_fixed >= 0.528:
        verdict = "PASS"
    elif cpcv_mean_auc_fixed >= 0.518:
        verdict = "BORDERLINE"
    else:
        verdict = "FAIL"

    # 15) Persist results
    results = {
        "cpcv_mean_auc": cpcv_mean_auc_fixed,
        "cpcv_paths": [float(a) for a in cpcv_paths_arr.tolist()],
        "k54_v1_anchor": K54_V1_ANCHOR,
        "delta": delta,
        "DSR_p": dsr_p,
        "PBO": pbo,
        "B1000_null_p": p_null,
        "B1000_null_obs_auc_combined": obs_auc,
        "cross_period_auc": cross_period_auc,
        "cross_period_n_train": cross_period_n_train,
        "cross_period_n_test": cross_period_n_test,
        "verdict": verdict,
        "selected_hp": best_hp,
        "selected_hp_idx": best_hp_idx,
        "n_kept": int(n_kept),
        "n_total_pool": int(n_total),
        "win_rate": float(y.mean()),
        "cpcv_K": CPCV_K,
        "cpcv_N": CPCV_N,
        "n_paths": int(n_paths),
        "purge_days": PURGE_DAYS,
        "embargo_days": EMBARGO_DAYS,
        "lookback_bars": LOOKBACK_BARS,
        "n_static_features": len(CANONICAL_FEATURES),
        "n_per_bar_channels": len(PER_BAR_CHANNELS),
        "hp_grid_size": len(DLINEAR_HP_GRID),
        "cpcv_honest_SE": se_cpcv,
        "cpcv_honest_t": t_cpcv,
        "cpcv_honest_p_two_sided": p_cpcv,
        "cpcv_std_auc_fixed_hp": cpcv_std_auc_fixed,
        "elapsed_seconds": float(time.time() - t0),
        "computed_at": utc_now(),
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[done] wrote {OUT_JSON}")
    print(json.dumps({k: v for k, v in results.items() if k not in ("cpcv_paths",)}, indent=2, default=str))


if __name__ == "__main__":
    main()
