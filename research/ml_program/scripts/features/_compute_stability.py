"""One-shot script: compute stability scores (Spearman rank correlation
between feature value and realized R) for the time_session feature family.

Outputs JSON file `research/ml_program/feature_catalogs/_time_session_stability.json`
that the catalog markdown / csv reads to populate the stability column.

Discipline:
- Pre-2026-04 data ONLY (cutoff 2026-04-01 UTC) per Q1.2 brief.
- F11 BOS records (hour-level bos_time) used for hour-sensitive features.
- Trade-index records (DATE-only) used as fallback at 13:00 UTC NY-default
  (only DATE-axis features are meaningful for these rows; hour-axis features
  computed for them are flagged in the catalog as "trade-index-DATE-only").
- 7 instruments (XAUUSD/GBPJPY/GBPUSD/USDJPY/US30_cash/NAS100/XAGUSD).
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev
from typing import Iterable

# Make local feature module importable without installing
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from time_session import compute_time_session_features  # noqa: E402

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
F11_PATH = ROOT / "research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl"
TRADE_INDEX_PATH = ROOT / "knowledge_base/index/_trade_index.json"
OUT_PATH = ROOT / "research/ml_program/feature_catalogs/_time_session_stability.json"

CUTOFF_ISO = "2026-04-01T00:00:00+00:00"  # pre-Apr-2026 only for stability


def load_f11_records() -> list[dict]:
    out: list[dict] = []
    with open(F11_PATH) as f:
        for line in f:
            rec = json.loads(line)
            ob = rec.get("ob_retest", {})
            r = ob.get("realized_r")
            if r is None:
                continue
            bos_time_str = rec["bos"]["bos_time"]
            if bos_time_str >= CUTOFF_ISO:
                continue
            out.append({
                "ts_iso": bos_time_str,
                "symbol": rec["bos"]["symbol"],
                "realized_r": float(r),
                "src": "f11",
            })
    return out


KZ_DEFAULT_HOUR = {"london": 8, "ny": 14, "tokyo": 1, "asia": 1, "asian": 1}


def load_trade_index_records() -> list[dict]:
    with open(TRADE_INDEX_PATH) as f:
        data = json.load(f)
    out: list[dict] = []
    for t in data["trades"]:
        if t.get("r_multiple") is None:
            continue
        d = t.get("date", "")
        if d == "" or d >= "2026-04-01":
            continue
        kz = (t.get("kill_zone") or "ny").lower()
        h = KZ_DEFAULT_HOUR.get(kz, 14)
        ts_iso = f"{d}T{h:02d}:00:00+00:00"
        out.append({
            "ts_iso": ts_iso,
            "symbol": t.get("symbol", "XAUUSD"),
            "realized_r": float(t["r_multiple"]),
            "src": "trade_index",
        })
    return out


def spearman(x: list[float], y: list[float]) -> tuple[float, int]:
    """Return (spearman_rho, n_used). Uses average ranks for ties."""
    assert len(x) == len(y)
    paired = [(xi, yi) for xi, yi in zip(x, y)
              if xi is not None and yi is not None
              and not (isinstance(xi, float) and math.isnan(xi))
              and not (isinstance(yi, float) and math.isnan(yi))]
    n = len(paired)
    if n < 5:
        return float("nan"), n
    xs = [p[0] for p in paired]
    ys = [p[1] for p in paired]
    rx = _rank_avg(xs)
    ry = _rank_avg(ys)
    if stdev(rx) == 0 or stdev(ry) == 0:
        return 0.0, n
    mx = mean(rx)
    my = mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    sx = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)))
    sy = math.sqrt(sum((ry[i] - my) ** 2 for i in range(n)))
    if sx * sy == 0:
        return 0.0, n
    return num / (sx * sy), n


def _rank_avg(vals: list[float]) -> list[float]:
    indexed = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and vals[indexed[j + 1]] == vals[indexed[i]]:
            j += 1
        avg_rank = (i + j) / 2 + 1  # 1-based
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg_rank
        i = j + 1
    return ranks


def main() -> None:
    f11 = load_f11_records()
    ti = load_trade_index_records()
    # Patch 2: tuple-keyed dedup (date, symbol, round(realized_r, 3)) — F11 first
    # priority. Naive `f11 + ti` over-counted records that appear in both sources
    # (same underlying trade with different ts representations: F11 minute-precise
    # bos_time vs trade_index DATE+KZ-default-hour).
    seen: set[tuple[str, str, float]] = set()
    all_recs: list[dict] = []
    for src in (f11, ti):
        for r in src:
            ts_obj = datetime.fromisoformat(r["ts_iso"])
            date_str = ts_obj.date().isoformat()
            key = (date_str, r["symbol"], round(float(r["realized_r"]), 3))
            if key in seen:
                continue
            seen.add(key)
            all_recs.append(r)
    print(f"F11 records: {len(f11)}, trade-index records: {len(ti)}, dedup total: {len(all_recs)}")

    feature_columns: defaultdict[str, list[float]] = defaultdict(list)
    rs: list[float] = []
    for rec in all_recs:
        ts = datetime.fromisoformat(rec["ts_iso"])
        feats = compute_time_session_features(
            ts,
            rec["symbol"],
            bars_since_last_kz_open=None,  # unknown for backfill
            minutes_since_last_fill=None,
        )
        rs.append(rec["realized_r"])
        for name, val in feats.items():
            feature_columns[name].append(float(val))

    # Pad columns with NaN for any feature missing in a row (some symbols
    # have tokyo, others don't — we want the union)
    n = len(rs)
    for name, col in feature_columns.items():
        if len(col) < n:
            col.extend([float("nan")] * (n - len(col)))

    out_records = []
    for name in sorted(feature_columns):
        col = feature_columns[name]
        # Skip features that are constant across the population (can't rank)
        nonnan = [v for v in col if not math.isnan(v)]
        if len(set(nonnan)) <= 1:
            out_records.append({
                "feature": name,
                "stability_spearman_rho": None,
                "stability_n": len(nonnan),
                "note": "constant_or_all_nan",
            })
            continue
        rho, npaired = spearman(col, rs)
        out_records.append({
            "feature": name,
            "stability_spearman_rho": rho if not math.isnan(rho) else None,
            "stability_n": npaired,
        })

    summary = {
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_total": n,
        "n_f11": len(f11),
        "n_trade_index": len(ti),
        "cutoff_iso_exclusive": CUTOFF_ISO,
        "stability_method": "spearman rank correlation, feature_value vs realized_r",
        "stability_population": "pre-2026-04 F11 BOS + trade-index, 7 instruments",
        "feature_count": len(out_records),
        "features": out_records,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote {OUT_PATH}")
    # Quick top-5 print
    valid = [r for r in out_records if r.get("stability_spearman_rho") is not None]
    valid.sort(key=lambda r: abs(r["stability_spearman_rho"]), reverse=True)
    print("Top-5 |rho|:")
    for r in valid[:5]:
        print(f"  {r['feature']}: rho={r['stability_spearman_rho']:+.4f} (n={r['stability_n']})")


if __name__ == "__main__":
    main()
