#!/usr/bin/env python3
"""Build the compact, hash-bound inputs used by the Wave-21 cost layer.

This is an offline evidence transform.  It reads only the already captured VPS export
and bar archive; it does not connect to MT5, a broker, or the network.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _repo() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "src" / "costs").is_dir() and (parent / "config").is_dir():
            return parent
    raise RuntimeError("repository root not found")


REPO = _repo()
sys.path.insert(0, str(REPO))

from src.costs.symbols import (  # noqa: E402
    DEFAULT_SYMBOL_AUTHORITY_MANIFEST,
    PROFILE_PATHS,
    ProfileSymbolAuthority,
    canonical_symbol_for_account,
)
from src.utils.broker_clock import (  # noqa: E402
    broker_epoch_to_utc,
    broker_naive_to_utc,
    resolve_rule,
)

DEFAULT_BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
DEFAULT_SLIPPAGE = Path(
    "/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/"
    "slippage_runtime.jsonl"
)
HERE = Path(__file__).resolve().parent
DEFAULT_FX_OUT = HERE / "HISTORICAL_FX_D1_V1.json.gz"
DEFAULT_SLIPPAGE_OUT = HERE / "SLIPPAGE_PRICE_V1.json"
DEFAULT_MANIFEST_OUT = HERE / "COST_INPUTS_MANIFEST_V1.json"

# profit currency -> (source pair, whether pair must be inverted to obtain
# profit-currency per USD).  This is the mapping independently exercised by M4.
FX_SERIES = {
    "JPY": ("USDJPY", False),
    "CAD": ("USDCAD", False),
    "CHF": ("USDCHF", False),
    "EUR": ("EURUSD", True),
    "GBP": ("GBPUSD", True),
    "AUD": ("AUDUSD", True),
    "NZD": ("NZDUSD", True),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")


def _write_json_gz(path: Path, doc: dict) -> None:
    raw = (json.dumps(doc, separators=(",", ":"), sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, mtime=0) as gz:
            gz.write(raw)


def build_fx(bars_root: Path) -> dict:
    series: dict[str, dict] = {}
    for currency, (symbol, invert) in FX_SERIES.items():
        path = bars_root / f"FTMO_{symbol}_D1.csv.gz"
        sidecar = Path(str(path) + ".timebase.json")
        if not path.is_file() or not sidecar.is_file():
            raise FileNotFoundError(f"missing FX source or timebase sidecar: {path}")
        tb = json.loads(sidecar.read_text())
        if tb.get("timebase") != "broker_server_wall_clock" or not tb.get("broker"):
            raise ValueError(f"{sidecar}: undeclared broker wall-clock source")
        rule = resolve_rule(tb["broker"])
        rows: list[list[float | int]] = []
        first_true = last_true = None
        with gzip.open(path, "rt", newline="") as fh:
            for row in csv.DictReader(fh):
                close = float(row["close"])
                if not math.isfinite(close) or close <= 0:
                    continue
                epoch = float(row["time"])
                # Retain the broker trading date for provenance, but key runtime lookup to
                # the bar's true completion instant. Run every raw epoch through the
                # registered historical rule so a mislabeled/unsupported calendar fails.
                wall = datetime.fromtimestamp(epoch, tz=timezone.utc)
                true_utc = broker_epoch_to_utc(epoch, rule)
                first_true = first_true or true_utc
                last_true = true_utc
                rate = (1.0 / close) if invert else close
                # A D1 `close` is not known at its bar-open date. Bind it to the
                # following broker-wall midnight (the bar's completion instant),
                # converted with the historical server rule. Runtime uses a strict
                # completion_utc < entry_utc lookup, preventing same-day lookahead.
                completion_wall = wall.replace(tzinfo=None) + timedelta(days=1)
                completion_utc = broker_naive_to_utc(completion_wall, rule)
                rows.append([
                    int(completion_utc.timestamp()),
                    wall.date().toordinal(),
                    rate,
                ])
        if not rows:
            raise ValueError(f"{path}: no finite positive closes")
        if any(a[0] >= b[0] for a, b in zip(rows, rows[1:])):
            raise ValueError(f"{path}: D1 completion instants are not strictly increasing")
        series[currency] = {
            "source_pair": symbol,
            "rate_unit": f"{currency}_per_USD",
            "source_sha256": _sha256(path),
            "timebase_sha256": _sha256(sidecar),
            "broker_clock_rule": rule.name,
            "first_broker_date": datetime.fromordinal(int(rows[0][1])).date().isoformat(),
            "last_broker_date": datetime.fromordinal(int(rows[-1][1])).date().isoformat(),
            "first_bar_open_true_utc": first_true.isoformat() if first_true else None,
            "last_bar_open_true_utc": last_true.isoformat() if last_true else None,
            "first_completed_utc": datetime.fromtimestamp(
                int(rows[0][0]), tz=timezone.utc
            ).isoformat(),
            "last_completed_utc": datetime.fromtimestamp(
                int(rows[-1][0]), tz=timezone.utc
            ).isoformat(),
            "n": len(rows),
            "rows": rows,
        }
    return {
        "schema": "gtos.costs.historical_fx_d1.v2",
        "coverage": "TRANSFERRED",
        "coverage_basis": (
            "strictly latest captured FTMO D1 bar whose broker-clock completion instant "
            "precedes entry_utc; daily close is transferred, never interpolated"
        ),
        "max_staleness_seconds": 7 * 86400,
        "series": series,
    }


def _account(row: dict) -> str | None:
    profile = ((row.get("pretrade_cost_model") or {}).get("profile") or {})
    name = str(profile.get("profile_name") or "")
    broker = str(profile.get("broker") or "").lower()
    if name.startswith("ftmo") or broker == "ftmo":
        return "FTMO"
    if name == "redacted_account" or broker == "redacted_account":
        return "redacted_account"
    return None


def build_slippage(
    path: Path, *, symbol_authority: ProfileSymbolAuthority | None = None
) -> dict:
    samples: dict[tuple[str, str], list[tuple[float, str, str]]] = defaultdict(list)
    rejected: Counter[str] = Counter()
    total = 0
    with path.open() as fh:
        for line in fh:
            total += 1
            row = json.loads(line)
            if row.get("slippage_event_type") != "entry":
                rejected["not_entry_event"] += 1
                continue
            if row.get("account_history_lookup_status") != "RECONCILED_FROM_ACCOUNT_HISTORY":
                rejected["not_history_reconciled"] += 1
                continue
            account = _account(row)
            canonical = (
                canonical_symbol_for_account(
                    account,
                    str(row.get("symbol") or ""),
                    authority=symbol_authority,
                )
                if account is not None
                else None
            )
            if account is None or canonical is None:
                rejected["unresolved_account_or_profile_symbol"] += 1
                continue
            try:
                directional = float(row["slippage_directional"])
                entry = float(row["executed_entry_price"])
                stop = float(row["executed_stop_price"])
            except (KeyError, TypeError, ValueError):
                rejected["missing_numeric_geometry"] += 1
                continue
            if not all(math.isfinite(x) for x in (directional, entry, stop)) or entry == stop:
                rejected["invalid_numeric_geometry"] += 1
                continue
            if row.get("executed_entry_price_status") != "CAPTURED" or row.get(
                "executed_stop_price_status"
            ) != "CAPTURED":
                rejected["geometry_not_captured"] += 1
                continue
            samples[(account, canonical)].append(
                (directional, str(row.get("symbol")), str(row.get("broker_fill_time_utc") or row["ts"]))
            )

    records: dict[str, dict[str, dict]] = {"FTMO": {}, "redacted_account": {}}
    for (account, canonical), vals in sorted(samples.items()):
        directional = [v[0] for v in vals]
        # Costs are positive: favourable fills are not booked as a credit.  This is
        # the observed adverse-only mean, not max(0, signed_mean), so an all-favourable
        # sample remains an observed zero with its n and dates visible.
        adverse = [max(0.0, v) for v in directional]
        records[account][canonical] = {
            "coverage": "MEASURED",
            "n": len(vals),
            "expected_adverse_price": math.fsum(adverse) / len(adverse),
            "signed_mean_price": statistics.fmean(directional),
            "observed_symbols": sorted({v[1] for v in vals}),
            "first_fill_utc": min(v[2] for v in vals),
            "last_fill_utc": max(v[2] for v in vals),
            "estimator": "mean(max(0, slippage_directional_price)) over reconciled entries",
        }
    return {
        "schema": "gtos.costs.slippage_price.v1",
        "source": str(path),
        "source_sha256": _sha256(path),
        "source_rows": total,
        "accepted_rows": sum(len(v) for v in samples.values()),
        "rejected_rows": dict(sorted(rejected.items())),
        "records": records,
        "profile_symbol_authority": {
            account: {"path": str(profile.relative_to(REPO)), "sha256": _sha256(profile)}
            for account, profile in sorted(PROFILE_PATHS.items())
        },
        "capture_requirement": (
            "one or more broker-history-reconciled entry fills with requested price, "
            "executed entry and executed stop for the exact account/profile symbol"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bars-root", type=Path, default=DEFAULT_BARS)
    parser.add_argument("--slippage", type=Path, default=DEFAULT_SLIPPAGE)
    parser.add_argument("--fx-out", type=Path, default=DEFAULT_FX_OUT)
    parser.add_argument("--slippage-out", type=Path, default=DEFAULT_SLIPPAGE_OUT)
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_MANIFEST_OUT)
    parser.add_argument(
        "--symbol-authority-out", type=Path, default=DEFAULT_SYMBOL_AUTHORITY_MANIFEST
    )
    args = parser.parse_args()

    symbol_authority = {
        "schema": "gtos.costs.symbol_authority.v1",
        "profiles": {
            account: {"path": str(path.relative_to(REPO)), "sha256": _sha256(path)}
            for account, path in sorted(PROFILE_PATHS.items())
        },
    }
    _write_json(args.symbol_authority_out, symbol_authority)
    fx = build_fx(args.bars_root)
    # Bootstrap from the symbol manifest just written, rather than requiring an older
    # COST_INPUTS_MANIFEST to exist before its own outputs can be rebuilt.
    injected_symbol_authority = ProfileSymbolAuthority(
        args.symbol_authority_out,
        PROFILE_PATHS,
        profile_root=REPO,
    )
    slippage = build_slippage(
        args.slippage, symbol_authority=injected_symbol_authority
    )
    _write_json_gz(args.fx_out, fx)
    _write_json(args.slippage_out, slippage)
    manifest = {
        "schema": "gtos.phase21.cost_inputs_manifest.v1",
        "result_use_status": "OFFLINE_COST_INPUT_ONLY_NO_BROKER_OR_LIVE_MUTATION",
        "outputs": {
            "historical_fx": {"path": str(args.fx_out.relative_to(REPO)), "sha256": _sha256(args.fx_out)},
            "slippage_price": {
                "path": str(args.slippage_out.relative_to(REPO)),
                "sha256": _sha256(args.slippage_out),
            },
            "symbol_authority": {
                "path": str(args.symbol_authority_out.relative_to(REPO)),
                "sha256": _sha256(args.symbol_authority_out),
            },
        },
        "source_scope": {
            "fx_pairs": sorted(FX_SERIES),
            "slippage_accepted_rows": slippage["accepted_rows"],
            "slippage_account_symbol_cells": sum(len(v) for v in slippage["records"].values()),
            "profile_symbol_authority": {
                account: {"path": str(path.relative_to(REPO)), "sha256": _sha256(path)}
                for account, path in sorted(PROFILE_PATHS.items())
            },
        },
    }
    _write_json(args.manifest_out, manifest)
    print(json.dumps(manifest, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
