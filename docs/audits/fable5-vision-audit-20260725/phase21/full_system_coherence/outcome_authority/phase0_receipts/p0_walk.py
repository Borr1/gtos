#!/usr/bin/env python3
"""Phase 0 — inversion truth: the real inverted walk.

Reuses the committed frozen machinery byte-for-byte:

  * candidate rows: the sealed compact event sinks (``missed`` ledger), exactly the
    rows the frozen scorers read;
  * M1 sources + hour-aware spreads: ``w21_score_aprmay_r3b.load_m1_sources``, the
    same loader the sealed April/May and June/July reads used (hash-checked);
  * lifecycle resolution: ``resolve_post_submission_m1_lifecycle`` from
    ``src/research_infra/walkforward/quote_side.py`` — the labeler itself, unmodified.

Nothing analytical is re-derived here. The only new object is the *inverted order
contract*: same symbol, same submission instant, same expiry/horizon, same entry
price level, opposite direction, stop at the old target level, target at the old
stop level, and therefore an approved risk distance of 1.5x the original.

Two arms are walked for every candidate:

  ORIG  — the original contract, re-resolved. This is a CONTROL: its
          ``terminal_net_r`` must reproduce the sealed cache exactly.
  INV   — the inverted contract.

Costs. ``terminal_gross_r`` already carries the spread mechanically (entry on the
executable entry side, exits compared against the executable exit side), so the
deductible is only slippage + swap + commission, exactly as
``candidate_funnel_analysis._lifecycle_row`` does it. Those three are quoted in
units of the ORIGINAL risk distance, so the inverted deductible is the same price
amount over the larger inverted risk: ``deductible / risk_ratio``.
"""
from __future__ import annotations

import bisect
import gzip
import importlib.util
import json
import math
import os
import pickle
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
OA = WT / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST_DIR = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"
OUT = Path("/private/tmp/phase0-inversion")
sys.path.insert(0, str(WT))
sys.path.insert(0, str(OA))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


r3 = load_module("w21_score_aprmay_r3b_frozen", OA / "w21_score_aprmay_r3b.py")
s2 = r3.s2
r = r3.r
m = r.m  # candidate_funnel_analysis

from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from src.research_infra.walkforward.quote_side import (
    BarQuote,
    resolve_post_submission_m1_lifecycle,
)

LIMIT_FAMILIES = m.LIMIT_FAMILIES
MARKET_FAMILIES = (
    "structural_distance_extreme",
    "liquidity_sweep_reclaim",
    "cross_asset_lead_lag",
    "displacement_continuation",
    "session_open_range_break",
    "regime_transition_break",
    "volatility_compression_expansion",
)

PREREG = json.loads((OA / "JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1_3.json").read_text())
_TR = PREREG["training"]
_VAL = {w["window_id"]: w for w in PREREG["validation"]["windows"]}
WINDOWS = {
    "feb": ("february_2026", Path("/private/tmp/w21-market-top-feb-r2"),
            _TR["february_manifest_root_sha256"], _TR["february_days"]),
    "apr": ("april_2026", Path("/private/tmp/w21-market-top-aprmay-r3"),
            _TR["april_manifest_root_sha256"], _TR["april_days"]),
    "may": ("may_2026", Path("/private/tmp/w21-market-top-aprmay-r3"),
            _TR["may_manifest_root_sha256"], _TR["may_days"]),
    "jun": ("june_2026", Path("/private/tmp/w21-market-top-junjul-r4"),
            _VAL["june_2026"]["manifest_root_sha256"], _VAL["june_2026"]["days"]),
    "jul": ("july_2026", Path("/private/tmp/w21-market-top-junjul-r4"),
            _VAL["july_2026"]["manifest_root_sha256"], _VAL["july_2026"]["days"]),
}

T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def raw_rows_for(root: Path, day: str):
    summary = json.loads((root / day / "run_summary.json").read_text(encoding="utf-8"))
    sink = ReplayCompactEventSink.open_sealed(
        root=root / day / "compact_events",
        expected_authority_root_sha256=summary["authority_root_sha256"],
    )
    return list(sink.ledger("missed"))


def _walk(raw, sources, *, inverted: bool):
    """Resolve one candidate under the original or the inverted contract."""
    symbol = str(raw["symbol"])
    source, times, bars, spreads = sources[symbol]
    submission = m._utc(str(raw["decision_time_utc"]))
    expiry = m._utc(str(raw["limit_first_expiry_utc"]))
    start = max(0, bisect.bisect_right(times, submission) - 1)
    end = min(len(times), bisect.bisect_left(times, expiry) + 1)
    entry = float(raw["entry_price"])
    stop = float(raw["stop_loss"])
    target = float(raw["take_profit_1"])
    direction = 1 if str(raw["side"]).upper() == "LONG" else -1
    order_type = m._order_type(raw)
    if inverted:
        direction, stop, target = -direction, target, stop
    risk = abs(entry - stop)
    return resolve_post_submission_m1_lifecycle(
        bars[start:end],
        m1_open_times_utc=times[start:end],
        direction=direction,
        proposed_order_type=order_type,
        submission_or_ack_time_utc=submission,
        expiry_utc=expiry,
        required_horizon_utc=expiry,
        approved_entry_price=entry,
        approved_stop_price=stop,
        approved_target_price=target,
        approved_risk_distance=risk,
        m1_price_basis=BarQuote.BID,
        spread_by_bar=spreads[start:end],
        source_interval_verified=True,
        symbol_spec_hash_sha256=m.SPEC_SHA256,
        spread_source_hash_sha256=m.SPREAD_SHA256,
    )


def candidate_record(raw, sources):
    """Both arms plus the entry-timing diagnostic, for one candidate."""
    symbol = str(raw["symbol"])
    source, times, bars, spreads = sources[symbol]
    entry = float(raw["entry_price"])
    stop = float(raw["stop_loss"])
    target = float(raw["take_profit_1"])
    risk = abs(entry - stop)
    risk_inv = abs(entry - target)
    direction = 1 if str(raw["side"]).upper() == "LONG" else -1
    deductible = sum(
        float(raw.get(field) or 0.0)
        for field in ("expected_slippage_r", "swap_cost_r", "commission_r")
    )
    orig = _walk(raw, sources, inverted=False)
    inv = _walk(raw, sources, inverted=True)

    def arm(res, risk_unit):
        status = res.lifecycle_label_status
        gross = (
            float(res.terminal_gross_r)
            if status.startswith("RESOLVED_FILLED_")
            else None
        )
        ded = deductible * (risk / risk_unit) if risk_unit > 0 else None
        detail = res.detail or {}
        return {
            "status": status,
            "state": res.terminal_state,
            "gross": gross,
            "net": None if gross is None else gross - ded,
            "deductible": ded,
            "fill_price": res.modelled_fill_price,
            "fill_time": res.modelled_fill_time_utc,
            "terminal_time": res.terminal_time_utc,
            "fill_convention": detail.get("fill_price_convention"),
            "censor_reason": res.censor_reason,
        }

    # entry-timing diagnostic: tape drift from the decision instant (submission-bar
    # open) to the modelled fill instant (successor-bar open), signed against the
    # ORIGINAL direction and expressed in original risk units.
    submission = m._utc(str(raw["decision_time_utc"]))
    idx = next(
        (
            i
            for i, opened in enumerate(times)
            if opened <= submission < opened + __import__("datetime").timedelta(minutes=1)
        ),
        None,
    )
    drift = None
    if idx is not None and idx + 1 < len(times):
        drift = direction * (bars[idx + 1].o - bars[idx].o) / risk if risk > 0 else None

    return {
        "key": str(raw["canonical_replay_candidate_instance_key"]),
        "day": str(raw["trading_day"]),
        "symbol": symbol,
        "family": str(raw["origin_family"]),
        "side": str(raw["side"]).upper(),
        "session": str(raw.get("session_bucket") or raw.get("session") or "unknown"),
        "window": str(raw["decision_window_id"]),
        "decision_utc": str(raw["decision_time_utc"]),
        "order_type": m._order_type(raw),
        "risk_price": risk,
        "risk_price_inv": risk_inv,
        "entry_price": entry,
        "spread_r": float(raw.get("spread_r") or 0.0),
        "slippage_r": float(raw.get("expected_slippage_r") or 0.0),
        "commission_r": float(raw.get("commission_r") or 0.0),
        "swap_r": float(raw.get("swap_cost_r") or 0.0),
        "cost_r": float(raw.get("cost_r") or 0.0),
        "orig": arm(orig, risk),
        "inv": arm(inv, risk_inv),
        "entry_drift_r_orig_dir": drift,
    }


def load_m1_sources_band(manifest_path: Path, expected_root: str, band: str):
    """r3.load_m1_sources with the spread BAND parameterized.

    Identical to the frozen loader (same manifest, same per-file sha256 check, same
    schema and chronology checks, same 24-symbol denominator) except that
    ``spread_for`` is called with ``band`` instead of the hardcoded ``"mid"``. Used
    only to bracket the spread term; the headline walk is ``mid``.
    """
    import csv
    from types import SimpleNamespace

    from src.components.ultimate_book.primitives import Bar
    from src.research_infra.walkforward.quote_side import spread_for

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["manifest_root_sha256"] != expected_root:
        raise ValueError(f"manifest root changed: {manifest_path}")
    bundle = {}
    for entry in manifest["bar_sources"]:
        if entry["timeframe"] != "M1":
            continue
        path = HOLD / entry["repo_relpath"]
        if r3.sha256_file(path) != entry["sha256"]:
            raise ValueError(f"M1 hash mismatch: {path}")
        times, bars = [], []
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["time", "open", "high", "low", "close", "volume"]:
                raise ValueError(f"M1 schema mismatch: {path}")
            for row in reader:
                times.append(m._utc(row["time"]))
                bars.append(
                    Bar(float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]))
                )
        if len(times) != entry["row_count"] or any(
            left >= right for left, right in zip(times, times[1:])
        ):
            raise ValueError(f"M1 chronology mismatch: {path}")
        cache, spreads = {}, []
        for instant in times:
            hour = instant.replace(minute=0, second=0, microsecond=0)
            if hour not in cache:
                cache[hour] = spread_for(entry["symbol"], hour, account="FTMO", band=band)
            spreads.append(cache[hour])
        bundle[entry["symbol"]] = (
            SimpleNamespace(sha256=entry["sha256"]),
            tuple(times),
            tuple(bars),
            tuple(spreads),
        )
    if len(bundle) != 24:
        raise ValueError("M1 symbol denominator is not 24")
    return manifest["manifest_root_sha256"], bundle


def run_month(month: str, *, families=None, limit_days=None):
    window_id, root, expected_root, days = WINDOWS[month]
    band = os.environ.get("P0_SPREAD_BAND", "mid")
    if band == "mid":
        root_sha, sources = r3.load_m1_sources(
            MANIFEST_DIR / f"{window_id}.json", expected_root
        )
    else:
        root_sha, sources = load_m1_sources_band(
            MANIFEST_DIR / f"{window_id}.json", expected_root, band
        )
    log(stage="m1_loaded", month=month, symbols=len(sources))
    if limit_days:
        days = days[:limit_days]
    keep = set(families) if families else None
    records = []
    for day in days:
        raws = raw_rows_for(root, day)
        n = 0
        for raw in raws:
            family = str(raw["origin_family"])
            if keep is not None and family not in keep:
                continue
            records.append(candidate_record(raw, sources))
            n += 1
        log(stage="day", month=month, day=day, kept=n, total=len(raws))
    del sources
    return records


def main():
    months = sys.argv[1].split(",") if len(sys.argv) > 1 else list(WINDOWS)
    fam = os.environ.get("P0_FAMILIES")
    families = fam.split(",") if fam else MARKET_FAMILIES
    limit_days = int(os.environ.get("P0_LIMIT_DAYS") or 0) or None
    for month in months:
        records = run_month(month, families=families, limit_days=limit_days)
        path = OUT / f"walk_{month}.pkl.gz"
        with gzip.open(path, "wb") as fh:
            pickle.dump(records, fh, protocol=5)
        log(stage="month_written", month=month, n=len(records), path=str(path))


if __name__ == "__main__":
    main()
