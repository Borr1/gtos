"""Futures-to-CFD mapping diagnostics for orderflow research.

This module is research-only. It does not import or mutate live trading
components. It evaluates whether CME futures prices can act as signal sources
for broker CFD symbols by measuring one-minute alignment, basis, return
correlation, lead/lag, beta, and directional agreement.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


DEFAULT_PAIR_MAP: tuple[tuple[str, str], ...] = (
    ("GC.v.0", "XAUUSD"),
    ("NQ.v.0", "NAS100"),
    ("YM.v.0", "US30_cash"),
    ("ES.v.0", "US30_cash"),
)
SUPPORTED_RETURN_TRANSFORMS = {"direct", "inverse_return"}


@dataclass(frozen=True)
class MappingPair:
    futures_symbol: str
    mt5_symbol: str
    return_transform: str = "direct"


@dataclass(frozen=True)
class PairDiagnostics:
    futures_symbol: str
    mt5_symbol: str
    aligned_minutes: int
    futures_minutes: int
    mt5_minutes: int
    start_utc: str | None
    end_utc: str | None
    basis_mean: float | None
    basis_std: float | None
    basis_min: float | None
    basis_max: float | None
    basis_z_abs_p95: float | None
    zero_lag_return_corr: float | None
    best_lag_minutes: int | None
    best_lag_corr: float | None
    beta_mt5_per_futures: float | None
    directional_agreement: float | None
    futures_volume_sum: float | None
    futures_trade_count_sum: int | None
    return_transform: str = "direct"


def parse_pair(value: str) -> MappingPair:
    if ":" not in value:
        raise ValueError(f"pair must be FUTURES:MT5[:RETURN_TRANSFORM], got {value!r}")
    parts = [part.strip() for part in value.split(":")]
    if len(parts) not in (2, 3):
        raise ValueError(f"pair must be FUTURES:MT5[:RETURN_TRANSFORM], got {value!r}")
    transform = parts[2] if len(parts) == 3 else "direct"
    if transform not in SUPPORTED_RETURN_TRANSFORMS:
        raise ValueError(
            f"unsupported return transform {transform!r}; expected one of {sorted(SUPPORTED_RETURN_TRANSFORMS)}"
        )
    return MappingPair(parts[0], parts[1], transform)


def default_pairs() -> list[MappingPair]:
    return [MappingPair(fut, mt5) for fut, mt5 in DEFAULT_PAIR_MAP]


def load_mt5_m1(
    symbol: str,
    *,
    data_dir: Path | str = Path("data/historical_2026"),
    start: str | None = None,
    end: str | None = None,
    time_shift_minutes: int = 0,
) -> pd.DataFrame:
    path = Path(data_dir) / f"{symbol}_M1.csv"
    if not path.exists():
        raise FileNotFoundError(f"MT5 M1 CSV not found: {path}")
    df = pd.read_csv(path)
    required = {"time", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing columns: {sorted(missing)}")
    df["minute"] = pd.to_datetime(df["time"], utc=True)
    if time_shift_minutes:
        df["minute"] = df["minute"] + pd.to_timedelta(time_shift_minutes, unit="min")
    df = df.set_index("minute").sort_index()
    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    if start:
        df = df[df.index >= pd.Timestamp(start, tz="UTC")]
    if end:
        df = df[df.index < pd.Timestamp(end, tz="UTC")]
    return df


def load_databento_trades(paths: Iterable[Path | str]) -> pd.DataFrame:
    import databento as db  # Local import keeps unit tests dependency-light.

    frames: list[pd.DataFrame] = []
    for path in paths:
        store = db.DBNStore.from_file(str(path))
        df = store.to_df()
        if df.empty:
            continue
        if "ts_event" not in df.columns:
            raise ValueError(f"Databento DBN missing ts_event: {path}")
        if "symbol" not in df.columns:
            raise ValueError(
                f"Databento DBN missing symbol metadata: {path}. "
                "Use continuous symbols or request symbol mapping metadata."
            )
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=0, ignore_index=False)


def aggregate_futures_m1(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    required = {"ts_event", "symbol", "price", "size"}
    missing = required - set(trades.columns)
    if missing:
        raise ValueError(f"Databento trades missing columns: {sorted(missing)}")

    df = trades.copy()
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
    df["minute"] = df["ts_event"].dt.floor("min")
    df["symbol"] = df["symbol"].astype(str)
    df["signed_size"] = 0.0
    if "side" in df.columns:
        side = df["side"].astype(str).str.upper()
        df.loc[side == "B", "signed_size"] = df.loc[side == "B", "size"].astype(float)
        df.loc[side == "A", "signed_size"] = -df.loc[side == "A", "size"].astype(float)

    grouped = df.groupby(["symbol", "minute"], sort=True)
    out = grouped.agg(
        open=("price", "first"),
        high=("price", "max"),
        low=("price", "min"),
        close=("price", "last"),
        volume=("size", "sum"),
        trade_count=("price", "size"),
        signed_volume=("signed_size", "sum"),
    )
    return out.reset_index().set_index("minute").sort_index()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(value) or np.isinf(value):
        return None
    return value


def _ret(series: pd.Series) -> pd.Series:
    return series.pct_change().replace([np.inf, -np.inf], np.nan)


def _apply_return_transform(returns: pd.Series, transform: str) -> pd.Series:
    if transform == "direct":
        return returns
    if transform == "inverse_return":
        return -returns
    raise ValueError(f"unsupported return transform: {transform}")


def _corr(a: pd.Series, b: pd.Series) -> float | None:
    joined = pd.concat([a, b], axis=1).dropna()
    if len(joined) < 3:
        return None
    if joined.iloc[:, 0].std() == 0 or joined.iloc[:, 1].std() == 0:
        return None
    return _safe_float(joined.iloc[:, 0].corr(joined.iloc[:, 1]))


def diagnose_pair(
    futures_m1: pd.DataFrame,
    mt5_m1: pd.DataFrame,
    pair: MappingPair,
    *,
    max_lag_minutes: int = 5,
) -> PairDiagnostics:
    fut = futures_m1[futures_m1["symbol"] == pair.futures_symbol].copy()
    mt5 = mt5_m1.copy()
    futures_minutes = int(len(fut))
    mt5_minutes = int(len(mt5))
    if fut.empty or mt5.empty:
        return PairDiagnostics(
            futures_symbol=pair.futures_symbol,
            mt5_symbol=pair.mt5_symbol,
            aligned_minutes=0,
            futures_minutes=futures_minutes,
            mt5_minutes=mt5_minutes,
            start_utc=None,
            end_utc=None,
            basis_mean=None,
            basis_std=None,
            basis_min=None,
            basis_max=None,
            basis_z_abs_p95=None,
            zero_lag_return_corr=None,
            best_lag_minutes=None,
            best_lag_corr=None,
            beta_mt5_per_futures=None,
            directional_agreement=None,
            futures_volume_sum=None,
            futures_trade_count_sum=None,
            return_transform=pair.return_transform,
        )

    joined = fut.add_prefix("fut_").join(mt5.add_prefix("mt5_"), how="inner")
    aligned = int(len(joined))
    if aligned == 0:
        return PairDiagnostics(
            futures_symbol=pair.futures_symbol,
            mt5_symbol=pair.mt5_symbol,
            aligned_minutes=0,
            futures_minutes=futures_minutes,
            mt5_minutes=mt5_minutes,
            start_utc=None,
            end_utc=None,
            basis_mean=None,
            basis_std=None,
            basis_min=None,
            basis_max=None,
            basis_z_abs_p95=None,
            zero_lag_return_corr=None,
            best_lag_minutes=None,
            best_lag_corr=None,
            beta_mt5_per_futures=None,
            directional_agreement=None,
            futures_volume_sum=None,
            futures_trade_count_sum=None,
            return_transform=pair.return_transform,
        )

    basis_mean = None
    basis_std = None
    basis_min = None
    basis_max = None
    basis_z_abs_p95 = None
    if pair.return_transform == "direct":
        basis = joined["mt5_close"] - joined["fut_close"]
        basis_mean = _safe_float(basis.mean())
        basis_std = _safe_float(basis.std())
        basis_min = _safe_float(basis.min())
        basis_max = _safe_float(basis.max())
        if basis_std and basis_std > 0:
            basis_z_abs_p95 = _safe_float(((basis - basis.mean()) / basis_std).abs().quantile(0.95))

    fut_ret = _apply_return_transform(_ret(joined["fut_close"]), pair.return_transform)
    mt5_ret = _ret(joined["mt5_close"])
    zero_corr = _corr(fut_ret, mt5_ret)

    lag_corrs: dict[int, float | None] = {}
    for lag in range(-max_lag_minutes, max_lag_minutes + 1):
        lag_corrs[lag] = _corr(fut_ret.shift(lag), mt5_ret)
    valid_lags = {lag: corr for lag, corr in lag_corrs.items() if corr is not None}
    best_lag = None
    best_corr = None
    if valid_lags:
        best_lag, best_corr = max(
            valid_lags.items(),
            key=lambda item: abs(item[1]),
        )

    beta = None
    joined_ret = pd.concat([fut_ret.rename("fut"), mt5_ret.rename("mt5")], axis=1).dropna()
    if len(joined_ret) >= 3 and joined_ret["fut"].var() > 0:
        beta = _safe_float(joined_ret["mt5"].cov(joined_ret["fut"]) / joined_ret["fut"].var())

    directional_agreement = None
    nonzero = joined_ret[(joined_ret["fut"] != 0) & (joined_ret["mt5"] != 0)]
    if len(nonzero) > 0:
        directional_agreement = _safe_float(
            (np.sign(nonzero["fut"]) == np.sign(nonzero["mt5"])).mean()
        )

    return PairDiagnostics(
        futures_symbol=pair.futures_symbol,
        mt5_symbol=pair.mt5_symbol,
        aligned_minutes=aligned,
        futures_minutes=futures_minutes,
        mt5_minutes=mt5_minutes,
        start_utc=joined.index.min().isoformat(),
        end_utc=joined.index.max().isoformat(),
        basis_mean=basis_mean,
        basis_std=basis_std,
        basis_min=basis_min,
        basis_max=basis_max,
        basis_z_abs_p95=basis_z_abs_p95,
        zero_lag_return_corr=zero_corr,
        best_lag_minutes=best_lag,
        best_lag_corr=_safe_float(best_corr),
        beta_mt5_per_futures=beta,
        directional_agreement=directional_agreement,
        futures_volume_sum=_safe_float(joined["fut_volume"].sum()),
        futures_trade_count_sum=int(joined["fut_trade_count"].sum()),
        return_transform=pair.return_transform,
    )


def write_mapping_report(
    diagnostics: list[PairDiagnostics],
    *,
    output_path: Path | str,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": "futures_cfd_mapping_report_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": inputs,
        "diagnostics": [asdict(item) for item in diagnostics],
        "synthesis": {
            "summary": (
                "This report measures futures-to-CFD transfer quality only. "
                "It does not promote orderflow features into live trading."
            ),
            "interpretation_rules": [
                "High zero-lag/lead-lag return correlation supports futures as a signal proxy.",
                "Stable basis supports level mapping; unstable basis favors event concurrence.",
                "Raw basis is not meaningful for cross-index pairs such as ES->US30_cash; use return metrics there.",
            ],
            "ambiguities": [
                "MT5 M1 timestamps are treated as UTC per existing historical loader convention.",
                "Databento trade side is used only for aggregate signed-volume diagnostics, not promotion.",
                "One-day or shorter samples are feasibility diagnostics, not evidence of durable transfer.",
            ],
            "next_steps": [
                "Run on multiple non-overlapping kill-zone/event windows.",
                "Add MT5 tick-parquet alignment for spread/slippage and sub-minute lead-lag.",
                "Only fetch mbp/mbo depth windows after trades-level transfer is acceptable.",
            ],
        },
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
