#!/usr/bin/env python3
"""Measure per-symbol, per-account quoted spread from the VPS tick archive.

Stage 1.1 (Session J). This is the **first** tool in the repository that reads
``/Users/borr/GTOSActive/vps-ticks-20260726/`` and computes a spread from it; the archive
was exported on 2026-07-26 and until now only its timebase sidecars had been written
(``scripts/declare_tick_export_timebase.py``). ``scripts/w7_live_forensics.py:66`` declares
``DEFAULT_TICK_ROOT`` and never dereferences it.

What it emits, and the two conventions it pins
----------------------------------------------
**Spread is emitted in PRICE UNITS, never in R.** The R conversion needs a stop distance,
which the archive does not carry (no bars, no ATR, no stop). Emitting price units is what
makes the number transferable to any stop geometry; ``src/costs`` does the division. This
is the same split the live engine already uses --
``broker_net_cost_engine.py:293-294`` computes ``spread_r = spread_price / sl_distance``.

**One crossing per round trip.** ``KB7_tick_truth.py:128`` derives the deployed
``TICK_SPREAD_FLOOR_R`` table as ``(half_spread * 2.0) / sd`` where ``half_spread =
(ask-bid)/2`` -- i.e. one full bid/ask crossing, not two. ``broker_net_cost_engine.py:294``
uses the identical convention. This tool emits ``ask - bid``, which is that same single
crossing, so its numbers are directly comparable to both.

Timebase
--------
The archive's ``time``/``time_msc`` columns are **broker server wall clock, not UTC**
(every file carries a ``.timebase.json`` saying so; finding F7). Session bucketing here
converts with ``src.utils.broker_clock.broker_epoch_to_utc`` and never trusts a ``_utc``
field name. Session bounds follow the repo's own H4 definition
(``wave1_structure_setups_ict.py:30-31``): Asia 00-07, London 08-15, NY 16-23, UTC.

Usage
-----
    python3 scripts/measure_tick_spreads.py -o <out.json> [--stride N] [--symbols ...]

``--stride`` samples every Nth tick. The median of a strided sample of a multi-million-row
series is stable to well under a tick; stride 1 is supported and simply slower.
"""

from __future__ import annotations

import argparse
import json
import sys
import time as _time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.utils.broker_clock import broker_epoch_to_utc, resolve_rule  # noqa: E402

DEFAULT_TICK_ROOT = Path("/Users/borr/GTOSActive/vps-ticks-20260726")
SCHEMA = "gtos.broker_truth.tick_spread_measurement.v1"

# Broker server name per archive subdirectory, as declared in the .timebase.json sidecars.
SERVER_BY_DIR = {"ftmo": "FTMO-Server3", "redacted_account": "redacted_account-Server 2"}
ACCOUNT_BY_DIR = {"ftmo": "FTMO", "redacted_account": "redacted_account"}

# UTC hour -> session, per wave1_structure_setups_ict.py:30-31.
SESSIONS = (("asia", 0, 8), ("london", 8, 16), ("ny", 16, 24))

PCTS = (5, 25, 50, 75, 90, 95, 99)


def _session_of(hours: np.ndarray) -> np.ndarray:
    out = np.empty(hours.shape, dtype=object)
    for name, lo, hi in SESSIONS:
        out[(hours >= lo) & (hours < hi)] = name
    return out


def _quantiles(values: np.ndarray) -> dict[str, float]:
    if values.size == 0:
        return {}
    qs = np.percentile(values, PCTS)
    return {f"p{p}": float(q) for p, q in zip(PCTS, qs)}


def _offset_seconds(sidecar: Path, server: str, sample_epoch: int) -> int:
    """Broker-wall -> UTC offset, resolved through broker_clock at a sampled instant.

    The archive window (2026-06-18..07-24) contains no US DST transition, so a single
    resolved offset is exact for the whole file. Asserted, not assumed: the caller
    re-resolves at the last epoch too and refuses the file if they disagree.
    """
    rule = resolve_rule(server)
    naive = datetime.fromtimestamp(sample_epoch, tz=timezone.utc).replace(tzinfo=None)
    true_utc = broker_epoch_to_utc(sample_epoch, rule)
    return int((naive.replace(tzinfo=timezone.utc) - true_utc).total_seconds())


def measure_file(path: Path, server: str, stride: int) -> dict:
    started = _time.time()
    spreads: list[np.ndarray] = []
    hours: list[np.ndarray] = []
    mids: list[np.ndarray] = []
    first_epoch = last_epoch = None
    n_raw = 0
    n_nonpositive = 0

    reader = pd.read_csv(
        path,
        usecols=["time", "bid", "ask"],
        dtype={"time": "int64", "bid": "float64", "ask": "float64"},
        chunksize=4_000_000,
    )
    for chunk in reader:
        n_raw += len(chunk)
        if first_epoch is None and len(chunk):
            first_epoch = int(chunk["time"].iloc[0])
        if len(chunk):
            last_epoch = int(chunk["time"].iloc[-1])
        if stride > 1:
            chunk = chunk.iloc[::stride]
        t = chunk["time"].to_numpy()
        bid = chunk["bid"].to_numpy()
        ask = chunk["ask"].to_numpy()
        sp = ask - bid
        ok = np.isfinite(sp) & (bid > 0) & (ask > 0)
        n_nonpositive += int((~(sp > 0) & ok).sum())
        ok &= sp > 0
        # float64 throughout: a float32 cast turns an exact 0.02 spread into
        # 0.019999999552965164 in the emitted artifact. Striding keeps this cheap.
        spreads.append(sp[ok])
        hours.append(t[ok])
        mids.append((ask[ok] + bid[ok]) / 2.0)

    if first_epoch is None:
        return {"error": "empty_file"}

    off_first = _offset_seconds(path, server, first_epoch)
    off_last = _offset_seconds(path, server, last_epoch)
    if off_first != off_last:
        # A DST transition inside the file would make a single offset wrong. Refuse rather
        # than silently mis-bucket; the fix is per-row conversion, not a guess.
        return {
            "error": "dst_transition_inside_file",
            "offset_seconds_first": off_first,
            "offset_seconds_last": off_last,
        }

    sp = np.concatenate(spreads) if spreads else np.array([], dtype="float32")
    tt = np.concatenate(hours) if hours else np.array([], dtype="int64")
    md = np.concatenate(mids) if mids else np.array([], dtype="float32")
    utc_hour = ((tt - off_first) // 3600) % 24

    rec: dict = {
        "rows_in_file": n_raw,
        "rows_sampled": int(sp.size),
        "stride": stride,
        "nonpositive_spread_rows_dropped": n_nonpositive,
        "broker_wall_first": datetime.fromtimestamp(first_epoch, tz=timezone.utc)
        .replace(tzinfo=None)
        .isoformat(),
        "broker_wall_last": datetime.fromtimestamp(last_epoch, tz=timezone.utc)
        .replace(tzinfo=None)
        .isoformat(),
        "utc_first": broker_epoch_to_utc(first_epoch, resolve_rule(server)).isoformat(),
        "utc_last": broker_epoch_to_utc(last_epoch, resolve_rule(server)).isoformat(),
        "broker_wall_to_utc_offset_seconds": off_first,
        "spread_price": _quantiles(sp),
        "spread_price_mean": float(sp.mean()) if sp.size else None,
        "mid_price_median": float(np.percentile(md, 50)) if md.size else None,
        "by_session": {},
        "elapsed_s": round(_time.time() - started, 1),
    }
    sess = _session_of(utc_hour)
    for name, _lo, _hi in SESSIONS:
        m = sess == name
        if not m.any():
            continue
        rec["by_session"][name] = {
            "rows_sampled": int(m.sum()),
            "spread_price": _quantiles(sp[m]),
        }
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tick-root", type=Path, default=DEFAULT_TICK_ROOT)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--symbols", nargs="*", default=None)
    args = ap.parse_args()

    out: dict = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "tick_root": str(args.tick_root),
        "stride": args.stride,
        "convention": {
            "spread": "ask - bid, in PRICE UNITS (one bid/ask crossing = one round trip, "
            "matching KB7_tick_truth.py:128 and broker_net_cost_engine.py:294)",
            "timebase": "archive time column is BROKER WALL CLOCK; converted via "
            "src.utils.broker_clock.broker_epoch_to_utc before session bucketing",
            "sessions_utc": {n: [lo, hi] for n, lo, hi in SESSIONS},
        },
        "accounts": {},
    }

    files = []
    for sub, server in SERVER_BY_DIR.items():
        d = args.tick_root / sub
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.csv.gz")):
            files.append((sub, server, p))

    for sub, server, path in files:
        # FTMO_GER40_cash_ticks_... -> GER40_cash
        stem = path.name.split("_ticks_")[0]
        symbol = stem.split("_", 1)[1] if "_" in stem else stem
        if args.symbols and symbol not in args.symbols:
            continue
        acct = ACCOUNT_BY_DIR[sub]
        print(f"[{acct}] {symbol} ...", flush=True)
        rec = measure_file(path, server, args.stride)
        rec["file"] = path.name
        rec["broker_server"] = server
        out["accounts"].setdefault(acct, {})[symbol] = rec
        print(
            f"[{acct}] {symbol}: rows={rec.get('rows_in_file')} "
            f"median_spread={rec.get('spread_price', {}).get('p50')} "
            f"({rec.get('elapsed_s')}s)",
            flush=True,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
