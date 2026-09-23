#!/usr/bin/env python3
"""A2-verify lane FC — stage 1: independent raw-data extraction.

Independent of FC's code: this script re-derives every input FC's executed
books consumed, from RAW artifacts only:
  - FA Phase-1 trade tables (Jan 57 / Feb 58) — anchored back to the raw lane
    LANE_TRADE_TABLE.jsonl ledgers and the raw pools on the composite key
    (candidate_id, decision_time_utc, symbol, side).
  - CJ lane tick jsonl files (true-UTC text fields) and M1 CSVs, sha256-verified
    against the CJ lane manifests (raw upstream evidence, not Sol receipts).

February is read for ATTRIBUTION ONLY under owner_mandate_20260801 — it is not
a fitting surface.  No March 2026 path, no live-forward (2026-07-29+) outcome
is touched: consumed months are asserted to be 2026-01 / 2026-02 only.

Memory: tick files are streamed line-by-line with a minute-prefix prefilter;
only in-window rows are parsed.  Peak well under 1.5 GB.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

SCRATCH = Path(
    "/private/tmp/claude-501/-Users-borr-GTOSActive-worktrees-wave19-broad-forensic-20260801/"
    "90d4ce63-5eb8-4f7a-bb2a-3c9361ea36ce/scratchpad"
)
OUT_DIR = SCRATCH / "fc_verify"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FA_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
    "research/operations/wave19_broad_forensic_2026_08_01"
)
JAN_TRADES = FA_ROOT / "trades_jan/TRADES_JAN_TABLE.json"
FEB_TRADES = FA_ROOT / "trades_feb/TRADES_FEB_TABLE.json"

JAN_LANE_TABLE = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/"
    "fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl"
)
FEB_LANE_TABLE = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/"
    "fable5-vision-audit-20260725/phase18/receipts/CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl"
)

LANE_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
MANIFESTS = {
    "2026-01": LANE_ROOT / "manifests/january_2026.json",
    "2026-02": LANE_ROOT / "manifests/february_2026.json",
}

US_PER_MIN = 60_000_000
ALLOWED_MONTHS = {"2026-01", "2026-02"}


def parse_us(text: str) -> int:
    t = str(text).strip()
    if t[:7] not in ALLOWED_MONTHS:
        raise SystemExit(f"month_boundary_violation:{t[:7]}")
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    d = dt.datetime.fromisoformat(t)
    if d.tzinfo is None:
        raise SystemExit(f"naive timestamp {text}")
    return int(round(d.astimezone(dt.timezone.utc).timestamp() * 1_000_000))


def load_trades(path: Path, month: str, expected: int) -> list[dict]:
    payload = json.loads(path.read_text())
    trades = payload["trades"]
    assert len(trades) == expected, (path, len(trades))
    keys = set()
    for t in trades:
        side = str(t.get("side") or t.get("direction")).upper()
        assert side in ("LONG", "SHORT")
        k = (t["candidate_id"], parse_us(t["decision_time_utc"]), t["symbol"], side)
        assert t["decision_time_utc"][:7] == month
        assert k not in keys, k
        keys.add(k)
        t["_key"] = k
        t["_decision_us"] = k[1]
        t["_entry_us"] = parse_us(t["entry_time_utc"])
        t["_horizon_us"] = k[1] + 120 * US_PER_MIN
        assert k[1] <= t["_entry_us"] < t["_horizon_us"]
    return trades


def anchor_to_lane(trades: list[dict], lane_path: Path, label: str) -> dict:
    """Anchor the FA table to the raw lane trade ledger on the composite key."""
    lane_rows = []
    for line in lane_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "candidate_id" in row and row.get("row_kind") != "meta":
            lane_rows.append(row)
    by_key = {}
    for r in lane_rows:
        side = str(r.get("direction") or r.get("side")).upper()
        k = (r["candidate_id"], parse_us(r["decision_time_utc"]), r["symbol"], side)
        assert k not in by_key
        by_key[k] = r
    matched = 0
    field_mismatches = []
    for t in trades:
        r = by_key.get(t["_key"])
        if r is None:
            field_mismatches.append({"key": [str(x) for x in t["_key"]], "issue": "missing_in_lane"})
            continue
        matched += 1
        for f in ("entry_price", "cost_r", "net_r", "entry_time_utc"):
            a, b = t.get(f), r.get(f)
            if isinstance(a, float) and isinstance(b, float):
                if abs(a - b) > 1e-9:
                    field_mismatches.append({"key": t["_key"][0], "field": f, "fa": a, "lane": b})
            elif f == "entry_time_utc":
                if parse_us(a) != parse_us(b):
                    field_mismatches.append({"key": t["_key"][0], "field": f, "fa": a, "lane": b})
            elif a != b and not (a is None and b is None):
                field_mismatches.append({"key": t["_key"][0], "field": f, "fa": a, "lane": b})
    return {
        "label": label,
        "lane_path": str(lane_path),
        "lane_trade_rows": len(lane_rows),
        "fa_rows_matched_in_lane": matched,
        "field_mismatches": field_mismatches,
    }


def anchor_to_pool(trades: list[dict], pool_path: Path, label: str) -> dict:
    """Anchor stop_loss / entry_price / cost_r to the raw pool rows (streamed)."""
    import gzip

    wanted = {t["_key"]: t for t in trades}
    found = {}
    with gzip.open(pool_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            side = str(row.get("side") or row.get("direction") or "").upper()
            try:
                k = (row["candidate_id"], parse_us(row["decision_time_utc"]), row["symbol"], side)
            except Exception:
                continue
            if k in wanted and k not in found:
                found[k] = {
                    "stop_loss": row.get("stop_loss"),
                    "entry_price": row.get("entry_price"),
                    "cost_r": row.get("cost_r"),
                }
    mismatches = []
    for k, t in wanted.items():
        p = found.get(k)
        if p is None:
            mismatches.append({"key": k[0], "issue": "missing_in_pool"})
            continue
        for f in ("stop_loss", "entry_price", "cost_r"):
            a, b = t.get(f), p.get(f)
            if isinstance(a, float) and isinstance(b, float):
                if abs(a - b) > 1e-9:
                    mismatches.append({"key": k[0], "field": f, "fa": a, "pool": b})
            elif a != b:
                mismatches.append({"key": k[0], "field": f, "fa": a, "pool": b})
    return {
        "label": label,
        "pool_path": str(pool_path),
        "keys_found_in_pool": len(found),
        "keys_wanted": len(wanted),
        "mismatches": mismatches,
    }


def manifest_sources(month: str):
    m = json.loads(MANIFESTS[month].read_text())
    ym = month.replace("-", "")
    assert m["window_id"] in ("january_2026", "february_2026")
    assert m["economic_outcomes_read"] is False
    assert (m.get("clock") or {}).get("time_column_basis") == "true_utc"
    ticks, m1 = {}, {}
    for r in m.get("tick_sources") or []:
        if r.get("timeframe") != "TICK":
            continue
        assert r.get("time_column_basis") == "true_utc"
        assert r.get("clock_conversion") == "broker_epoch_to_utc"
        sym = r.get("mapped_symbol") or r.get("symbol")
        ticks[sym] = r
    for r in m.get("bar_sources") or []:
        if r.get("timeframe") != "M1" or ym not in str(r.get("source_family") or ""):
            continue
        sym = r.get("mapped_symbol") or r.get("symbol")
        m1[sym] = r
    return ticks, m1


def scan_tick_file(record: dict, windows: list[tuple[int, int]], label: str):
    """Stream one raw tick jsonl: sha256 the whole file, extract in-window rows."""
    path = LANE_ROOT / record["lane_relpath"]
    minute_keys = set()
    for lo, hi in windows:
        m = (lo // US_PER_MIN) * US_PER_MIN
        while m <= hi:
            minute_keys.add(
                dt.datetime.fromtimestamp(m / 1e6, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M").encode()
            )
            m += US_PER_MIN
    digest = hashlib.sha256()
    times, bids, asks = [], [], []
    needle = b'"ts_utc":"'
    nlen = len(needle)
    kept = 0
    disagreements = 0
    with path.open("rb") as fh:
        for raw in fh:
            digest.update(raw)
            i = raw.find(needle)
            if i < 0:
                continue
            if raw[i + nlen : i + nlen + 16] not in minute_keys:
                continue
            row = json.loads(raw)
            ts = parse_us(row["ts_utc"])
            if "time" in row and row["time"] not in (None, ""):
                if parse_us(row["time"]) != ts:
                    disagreements += 1
                    continue
            ok = False
            for lo, hi in windows:
                if lo < ts <= hi:
                    ok = True
                    break
            if not ok:
                continue
            times.append(ts)
            bids.append(float(row["bid"]))
            asks.append(float(row["ask"]))
            kept += 1
    sha = digest.hexdigest()
    assert sha == record["sha256"], f"tick sha mismatch {label}: {sha} != {record['sha256']}"
    t = np.asarray(times, dtype=np.int64)
    assert disagreements == 0, f"ts_utc/time disagreement rows in {label}: {disagreements}"
    assert np.all(t[1:] >= t[:-1]), f"tick order violation {label}"
    return {
        "times": t,
        "bid": np.asarray(bids, dtype=np.float64),
        "ask": np.asarray(asks, dtype=np.float64),
        "sha256": sha,
        "rows_kept": kept,
        "path": str(path),
    }


def load_m1_csv(record: dict, label: str):
    import csv

    path = LANE_ROOT / record["lane_relpath"]
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    sha = digest.hexdigest()
    assert sha == record["sha256"], f"m1 sha mismatch {label}"
    times, o, h, l, c = [], [], [], [], []
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ts = parse_us(row["time"])
            vals = (float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]))
            assert not times or ts > times[-1]
            assert vals[2] <= vals[1]
            times.append(ts)
            o.append(vals[0])
            h.append(vals[1])
            l.append(vals[2])
            c.append(vals[3])
    assert len(times) == record["row_count"], (label, len(times), record["row_count"])
    return {
        "times": np.asarray(times, dtype=np.int64),
        "open": np.asarray(o),
        "high": np.asarray(h),
        "low": np.asarray(l),
        "close": np.asarray(c),
        "sha256": sha,
        "path": str(path),
    }


def main() -> int:
    print("[stage1] loading trade tables", flush=True)
    jan = load_trades(JAN_TRADES, "2026-01", 57)
    feb = load_trades(FEB_TRADES, "2026-02", 58)

    anchors = {
        "january_lane": anchor_to_lane(jan, JAN_LANE_TABLE, "january"),
        "february_lane": anchor_to_lane(feb, FEB_LANE_TABLE, "february"),
    }
    print("[stage1] lane anchors:", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'field_mismatches'} | {'n_field_mismatches': len(v['field_mismatches'])} for k, v in anchors.items()}), flush=True)

    JAN_POOL = Path(
        "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/"
        "fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
    )
    FEB_POOL = Path(
        "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/"
        "fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
    )
    anchors["january_pool"] = anchor_to_pool(jan, JAN_POOL, "january")
    print("[stage1] jan pool anchor done", flush=True)
    anchors["february_pool"] = anchor_to_pool(feb, FEB_POOL, "february")
    print("[stage1] feb pool anchor done (ATTRIBUTION-ONLY read under owner_mandate_20260801)", flush=True)

    bindings = []
    for month, trades in (("2026-01", jan), ("2026-02", feb)):
        ticks, m1 = manifest_sources(month)
        tick_syms = {t["symbol"] for t in trades if t["symbol"] in ticks}
        m1_syms = {t["symbol"] for t in trades if t["symbol"] not in ticks}
        print(f"[stage1] {month}: tick syms {sorted(tick_syms)}, m1 syms {sorted(m1_syms)}", flush=True)
        for sym in sorted(tick_syms):
            windows = [
                (t["_entry_us"], t["_horizon_us"]) for t in trades if t["symbol"] == sym
            ]
            res = scan_tick_file(ticks[sym], windows, f"{month}:{sym}")
            np.savez_compressed(
                OUT_DIR / f"tick_{month}_{sym}.npz",
                times=res["times"], bid=res["bid"], ask=res["ask"],
            )
            bindings.append({"month": month, "symbol": sym, "timeframe": "TICK",
                             "path": res["path"], "sha256": res["sha256"],
                             "rows_kept": res["rows_kept"], "verified_vs_manifest": True})
            print(f"[stage1] {month} {sym}: kept {res['rows_kept']} tick rows, sha OK", flush=True)
        for sym in sorted(m1_syms):
            assert sym in m1, f"no M1 source for {sym} in {month}"
            res = load_m1_csv(m1[sym], f"{month}:{sym}")
            np.savez_compressed(
                OUT_DIR / f"m1_{month}_{sym}.npz",
                times=res["times"], open=res["open"], high=res["high"],
                low=res["low"], close=res["close"],
            )
            bindings.append({"month": month, "symbol": sym, "timeframe": "M1",
                             "path": res["path"], "sha256": res["sha256"],
                             "verified_vs_manifest": True})
            print(f"[stage1] {month} {sym}: M1 loaded, sha OK", flush=True)

    (OUT_DIR / "anchors.json").write_text(json.dumps(anchors, indent=1, default=str))
    (OUT_DIR / "bindings.json").write_text(json.dumps(bindings, indent=1))
    print("[stage1] DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
