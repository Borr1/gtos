"""pbg_lib — substrate for the partial-bar generator (Session PB, wave 19).

Loads the true-UTC lane-hold bar CSVs, builds the exact `raw_data` the replay
builds (`v4_timewarp.raw_data_for_asof`), and drives the REAL production
generator `src.components.broader_origin_generators.generate_live_broader_origin_candidates`.

Two modes:

* ``close_only``  — decisions at each M15 bar close, the shipped contract.
* ``partial``     — decisions at minute k of the FORMING M15 bar, k in 1..14.
                    The forming bar is synthesised from that bar's own M1 bars
                    covering [t_open, t_open + k).  Nothing after the decision
                    instant is ever visible: the MSO is the one the engine holds
                    at the bar's OPEN (built from closed bars only), and the
                    D1/H4/H1 series are unchanged inside the bar.

Nothing here writes outside the receipts directory.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

REPO = Path(__file__).resolve().parents[6]
BARS = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars"
)
M15_DIR = BARS / "bridge_ftmo_m15_20250601_20260610"
H4D1_DIR = BARS / "deep_universe_h4d1_2014_2026"


def m1_dir(yyyymm: str) -> Path:
    return BARS / ("bridge_ftmo_m1_%s" % yyyymm)


SYMBOLS: tuple[str, ...] = tuple(
    sorted(p.name[: -len("_M15.csv")] for p in M15_DIR.glob("*_M15.csv"))
)

_TF_MIN = {"D1": 1440, "H4": 240, "H1": 60, "M15": 15, "M1": 1}

# the deep-universe H4/D1 export names five index/CFD symbols differently from
# the M15/M1 bridge exports.  Measured by directory listing, not assumed.
DEEP_NAME = {
    "GER40": "GER40_cash",
    "JP225": "JP225_cash",
    "NAS100": "US100_cash",
    "SPX500": "US500_cash",
    "UK100": "UK100_cash",
}


def deep_path(symbol: str, tf: str) -> Path:
    return H4D1_DIR / f"{DEEP_NAME.get(symbol, symbol)}_{tf}.csv"



# --------------------------------------------------------------------------- IO


def read_csv_bars(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", newline="") as fh:
        for row in csv.DictReader(fh):
            out.append(
                {
                    "time": row["time"],
                    "time_utc": row["time"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"] or 0.0),
                }
            )
    return out


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def aggregate_h1(m15_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build H1 bars from M15 bars.  M15 opens are :00/:15/:30/:45, so an H1 bar
    is the four M15 bars sharing an hour.  A partial hour still emits (that is
    what the broker's own H1 series does at a session edge)."""
    buckets: dict[datetime, list[dict[str, Any]]] = {}
    order: list[datetime] = []
    for row in m15_rows:
        ts = _parse(row["time_utc"])
        key = ts.replace(minute=0, second=0, microsecond=0)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(row)
    out: list[dict[str, Any]] = []
    for key in order:
        grp = buckets[key]
        out.append(
            {
                "time": key.isoformat(),
                "time_utc": key.isoformat(),
                "open": grp[0]["open"],
                "high": max(b["high"] for b in grp),
                "low": min(b["low"] for b in grp),
                "close": grp[-1]["close"],
                "volume": sum(b["volume"] for b in grp),
            }
        )
    return out


# ------------------------------------------------------------------- resolved sources


def build_sources(
    symbols: Iterable[str],
    *,
    h1_from_m15: bool = True,
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Return (sources_by_symbol, m15_rows_by_symbol)."""
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        ResolvedSource,
        SourceSpec,
    )

    sources: dict[str, dict[str, Any]] = {}
    m15_by_symbol: dict[str, list[dict[str, Any]]] = {}
    for sym in symbols:
        m15 = read_csv_bars(M15_DIR / f"{sym}_M15.csv")
        m15_by_symbol[sym] = m15
        per_tf: dict[str, Any] = {}
        payloads = {
            "M15": m15,
            "H4": read_csv_bars(H4D1_DIR / f"{sym}_H4.csv"),
            "D1": read_csv_bars(H4D1_DIR / f"{sym}_D1.csv"),
        }
        payloads["H1"] = aggregate_h1(m15) if h1_from_m15 else []
        for tf, rows in payloads.items():
            spec = SourceSpec(
                symbol=sym,
                mapped_symbol=sym,
                timeframe=tf,
                path=Path(f"pbg://{sym}/{tf}"),
                source_family="lane_inputs_true_utc_v1",
                source_broker="ftmo",
                source_role="research",
            )
            per_tf[tf] = ResolvedSource(
                spec=spec,
                rows=tuple(rows),
                rows_by_day={},
                sha256="pbg",
                day_counts={},
                selected_status="pbg",
                min_required_rows_per_day=0,
            )
        sources[sym] = per_tf
    return sources, m15_by_symbol


def load_m1(
    symbols: Iterable[str],
    months: Iterable[str],
    *,
    day: str | None = None,
) -> dict[str, dict[datetime, dict]]:
    """Return {symbol: {bar_open_dt: bar}} for the requested YYYYMM months.

    ``day`` restricts to that UTC calendar day (memory: a whole month of M1 for
    24 symbols is ~300 MB of dicts per worker; one day is ~15 MB)."""
    lo = hi = None
    if day is not None:
        lo = datetime.fromisoformat(day + "T00:00:00+00:00")
        hi = lo + timedelta(days=1)
    out: dict[str, dict[datetime, dict]] = {}
    for sym in symbols:
        acc: dict[datetime, dict] = {}
        for mm in months:
            p = m1_dir(mm) / f"{sym}_M1.csv"
            if not p.is_file():
                continue
            for row in read_csv_bars(p):
                ts = _parse(row["time_utc"])
                if lo is not None and not (lo <= ts < hi):
                    continue
                acc[ts] = row
        out[sym] = acc
    return out


# ------------------------------------------------------------------------- config


def load_replay_config() -> dict[str, Any]:
    from src.research_infra.v4_timewarp_simulated_live_research_loop import load_config

    return load_config(REPO / "config" / "agent_config.yaml")


# ------------------------------------------------------------------------- decisions


def synth_partial_m15(
    *,
    bar_open: datetime,
    m1_index: Mapping[datetime, Mapping[str, Any]],
    minutes: int,
) -> dict[str, Any] | None:
    """Forming M15 bar covering [bar_open, bar_open + minutes) from M1 bars.

    Returns None when no M1 bar exists in the window (the market has not traded
    yet inside this bar — there is nothing to decide on).
    """
    o = h = l = c = None
    vol = 0.0
    for i in range(minutes):
        b = m1_index.get(bar_open + timedelta(minutes=i))
        if b is None:
            continue
        if o is None:
            o = b["open"]
            h = b["high"]
            l = b["low"]
        else:
            h = max(h, b["high"])
            l = min(l, b["low"])
        c = b["close"]
        vol += b["volume"]
    if o is None:
        return None
    return {
        "time": bar_open.isoformat(),
        "time_utc": bar_open.isoformat(),
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "volume": vol,
    }
