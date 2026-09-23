#!/usr/bin/env python3
"""Three-month postmortem — stage 2: regime-spine dials over the same source data.

Computes the wave-6 regime spine's dial statistics (src/research_infra/regime_spine/state.py,
verbatim build_frame) over the hold's own H4 and M15 series for the 24-symbol surface.
The series files span 2025-06-01 .. 2026-06-09; every bar at or after 2026-06-01T00:00Z is
dropped BEFORE framing so no June-2026 (never-read window) bar participates in anything.
All dial values are causal by construction (index <= i only).

Writes:
  RECEIPTS/PM_REGIME_MONTHS_V1.json    month x symbol-class x dial distributions (H4)
  CACHE/regime_m15_{symbol}.npz        per-symbol M15 arrays for decision-time joins
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

WT_NEW = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(WT_NEW))

from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.research_infra.regime_spine.state import build_frame  # noqa: E402

RECEIPTS = Path(__file__).resolve().parent
CACHE = Path("/private/tmp/w21-postmortem-cache-20260811")
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST = HOLD / (
    ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/"
    "manifests/february_2026.json"
)
CUTOFF = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)

MONTHS = {
    "jan": ("2026-01-01", "2026-02-01"),
    "feb": ("2026-02-01", "2026-03-01"),
    "april": ("2026-04-01", "2026-05-01"),
    "may": ("2026-05-01", "2026-06-01"),
}

#: The 24-symbol surface as named in the LANE_INPUTS_TRUE_UTC_V1 manifests.
SYMBOL_CLASS = {
    "XAUUSD": "metals", "XAGUSD": "metals",
    "BTCUSD": "crypto", "ETHUSD": "crypto",
    "UKOIL_cash": "energy", "USOIL_cash": "energy",
    "GER40": "index", "JP225": "index", "NAS100": "index",
    "SPX500": "index", "UK100": "index", "US30_cash": "index",
}


def classify(symbol: str) -> str:
    if symbol in SYMBOL_CLASS:
        return SYMBOL_CLASS[symbol]
    if symbol.endswith("JPY"):
        return "fx_jpy"
    if len(symbol) == 6 and symbol.isalpha():
        return "fx"
    return "other"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_series(entry):
    path = HOLD / entry["repo_relpath"]
    if sha256_file(path) != entry["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    times, bars = [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["time", "open", "high", "low", "close", "volume"]:
            raise ValueError(f"schema mismatch: {path}")
        for row in reader:
            at = dt.datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
            if at >= CUTOFF:
                break  # never-read discipline: nothing at/after 2026-06-01 participates
            times.append(at)
            bars.append(Bar(float(row["open"]), float(row["high"]),
                            float(row["low"]), float(row["close"])))
    if any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError(f"chronology violation: {path}")
    return times, bars


def frame_stats(values):
    known = [v for v in values if v is not None and np.isfinite(v)]
    if not known:
        return None
    known.sort()
    n = len(known)
    return {
        "n": n,
        "p25": round(known[n // 4], 4),
        "p50": round(known[n // 2], 4),
        "p75": round(known[(3 * n) // 4], 4),
        "mean": round(statistics.fmean(known), 4),
    }


def main() -> None:
    t0 = time.time()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    h4_entries = [e for e in manifest["bar_sources"] if e["timeframe"] == "H4"]
    m15_entries = [e for e in manifest["bar_sources"] if e["timeframe"] == "M15"]
    assert len(h4_entries) == 24 and len(m15_entries) == 24

    # ---- H4 month x class x dial distributions
    dials_by = defaultdict(lambda: defaultdict(list))  # (month, cls, dial) -> values
    symbols = []
    for entry in sorted(h4_entries, key=lambda e: e["symbol"]):
        symbol = entry["symbol"]
        symbols.append(symbol)
        times, bars = load_series(entry)
        frame = build_frame(symbol, 16388, bars, times)
        for i, at in enumerate(times):
            day = at.strftime("%Y-%m-%d")
            for month, (lo, hi) in MONTHS.items():
                if lo <= day < hi:
                    cls = classify(symbol)
                    for group in (cls, "ALL"):
                        dials_by[(month, group)]["vol_regime"].append(frame.vr_raw[i])
                        dials_by[(month, group)]["trend_slope50_atr"].append(frame.slope50[i])
                        dials_by[(month, group)]["trend_slope50_abs"].append(
                            abs(frame.slope50[i]) if frame.slope50[i] is not None else None
                        )
                        dials_by[(month, group)]["range_position_50"].append(frame.rng_pos[i])
                        dials_by[(month, group)]["compression_5_over_20"].append(frame.comp[i])
                        dials_by[(month, group)]["persistence_ac60"].append(frame.ac60_prim[i])
                    break
        print(json.dumps({"framed_h4": symbol, "bars": len(bars),
                          "t": round(time.time() - t0, 1)}), flush=True)

    months_out = {}
    for (month, group), dials in sorted(dials_by.items()):
        months_out.setdefault(month, {})[group] = {
            dial: frame_stats(values) for dial, values in sorted(dials.items())
        }

    # ---- M15 per-symbol arrays for decision-time joins
    for entry in sorted(m15_entries, key=lambda e: e["symbol"]):
        symbol = entry["symbol"]
        out = CACHE / f"regime_m15_{symbol.replace('.', '_')}.npz"
        if out.is_file():
            continue
        times, bars = load_series(entry)
        frame = build_frame(symbol, 15, bars, times)

        def arr(values):
            return np.asarray(
                [np.nan if v is None else float(v) for v in values], dtype=np.float64
            )

        np.savez_compressed(
            out,
            epoch=np.asarray([t.timestamp() for t in times], dtype=np.float64),
            vol_regime=arr(frame.vr_raw),
            slope20=arr(frame.slope20),
            slope50=arr(frame.slope50),
            slope100=arr(frame.slope100),
            rng_pos=arr(frame.rng_pos),
            comp=arr(frame.comp),
            ac60=arr(frame.ac60_prim),
            atr=arr(frame.atr),
        )
        print(json.dumps({"framed_m15": symbol, "bars": len(bars),
                          "t": round(time.time() - t0, 1)}), flush=True)

    receipt = {
        "schema": "gtos.wave21.postmortem.regime_months.v1",
        "status": "DEVELOPMENT_DIAGNOSTIC",
        "source": {
            "manifest": str(MANIFEST),
            "series_span_note": (
                "hold H4/M15 files span 2025-06-01..2026-06-09; bars >= 2026-06-01T00:00Z "
                "dropped before framing (never-read discipline). Dial values are causal "
                "(index <= i) per regime_spine.state.build_frame."
            ),
            "timeframe_for_month_tables": "H4",
        },
        "symbol_classes": {s: classify(s) for s in symbols},
        "months": months_out,
    }
    out = RECEIPTS / "PM_REGIME_MONTHS_V1.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"done": str(out), "t": round(time.time() - t0, 1)}), flush=True)


if __name__ == "__main__":
    main()
