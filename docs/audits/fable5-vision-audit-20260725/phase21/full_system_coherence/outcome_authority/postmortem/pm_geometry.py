#!/usr/bin/env python3
"""Three-month postmortem — stage 4: family geometry walks on selected + near-selected.

Re-walks the SAME M1 lifecycle machinery the frozen rule was judged with
(candidate_funnel_analysis._lifecycle_row -> resolve_post_submission_m1_lifecycle, loaded
from the committed scorer chain) under alternative target/stop/horizon geometries, for the
candidates the frozen rule selected or nearly selected in the three open months.

IN-SAMPLE DIAGNOSTIC: geometry variants are evaluated after all three months' outcomes
were read. Nothing here chooses a geometry; it prices the question for the V2 spec.

Set definition (from the stage-1 window audit of the main policy):
  selected      the sealed rule's trades (Feb 106, Apr+May 67)
  near_selected top-ranked candidate of every abstained window (top_below_0p10 and
                top_limit_abstain) plus ranks 2-3 of traded windows, deduplicated,
                minus the selected set

Geometry variants (native entry, native direction, native expiry unless stated):
  native_recon  original prices — control; must reproduce the recorded lifecycle
  t1p0/t1p5/t3p0  target at 1.0/1.5/3.0 x native risk, native stop
  s0p75_t2      stop at 0.75 x native risk, target 2.0 x the NEW risk
  s1p5_t2       stop at 1.50 x native risk, target 2.0 x the NEW risk
  h2x           native prices, expiry extended to min(2x native span, last M1 bar);
                month-sliced M1 files make it physically impossible to read into
                March or June (never-read discipline preserved by construction)

Unit convention: every variant's gross/net R is in units of ITS OWN risk distance
(fixed-risk-cash sizing). Recorded deductible_cost_r scales by 1/stop_mult in new-R
units; the swap component's holding-time dependence is NOT re-modelled (stated caveat).

Writes RECEIPTS/PM_GEOMETRY_V1.json and CACHE/geometry_rows.jsonl.gz.
"""
from __future__ import annotations

import gzip
import importlib.util
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

WT_NEW = Path(__file__).resolve().parents[7]
RECEIPTS = Path(__file__).resolve().parent
OA = RECEIPTS.parent
CACHE = Path("/private/tmp/w21-postmortem-cache-20260811")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


log(stage="loading_module_chain")
r3b = load_module("pm_geo_r3b", OA / "w21_score_aprmay_r3b.py")
s2 = r3b.s2
m = r3b.r.m

from src.research_infra.walkforward.quote_side import (  # noqa: E402  (old worktree path)
    BarQuote,
    resolve_post_submission_m1_lifecycle,
)

FEB_RESULT = json.loads(
    (OA / "FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json").read_text()
)
APRMAY_RESULT = json.loads(
    (OA / "APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json").read_text()
)
PREREG = json.loads((OA / "APRIL_MAY_MARKET_TOP_CHOICE_PREREG_V1_6.json").read_text())

VARIANTS = ("native_recon", "t1p0", "t1p5", "t3p0", "s0p75_t2", "s1p5_t2", "h2x")


def read_rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def at(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def candidate_sets():
    selected = {
        "feb": [s["candidate_occurrence_key"] for s in FEB_RESULT["selected_candidates"]],
        "aprmay": [
            s["candidate_occurrence_key"] for s in APRMAY_RESULT["selected_candidates"]
        ],
    }
    near = {"feb": set(), "aprmay": set()}
    for tag in ("feb", "aprmay"):
        chosen = set(selected[tag])
        for record in read_rows(CACHE / f"window_audit_{tag}.jsonl.gz"):
            top3 = record.get("top3") or []
            if record["disposition"] in ("top_below_0p10", "top_limit_abstain") and top3:
                near[tag].add(top3[0]["key"])
            elif record["disposition"] == "trade":
                for item in top3[1:]:
                    near[tag].add(item["key"])
        near[tag] -= chosen
    return selected, {tag: sorted(keys) for tag, keys in near.items()}


def geometry_for(variant, entry, stop, target, direction, risk):
    """Returns (stop', target', stop_mult) for a variant; None values keep native."""
    if variant == "native_recon" or variant == "h2x":
        return stop, target, 1.0
    if variant.startswith("t"):
        mult = {"t1p0": 1.0, "t1p5": 1.5, "t3p0": 3.0}[variant]
        return stop, entry + direction * mult * risk, 1.0
    if variant == "s0p75_t2":
        new_risk = 0.75 * risk
        return entry - direction * new_risk, entry + direction * 2.0 * new_risk, 0.75
    if variant == "s1p5_t2":
        new_risk = 1.5 * risk
        return entry - direction * new_risk, entry + direction * 2.0 * new_risk, 1.5
    raise ValueError(variant)


def walk(row, sources, variant):
    symbol = row["symbol"]
    source, times, bars, spreads = sources[symbol]
    submission = at(row["decision_time_utc"])
    expiry = at(row["limit_first_expiry_utc"])
    if variant == "h2x":
        expiry = min(
            submission + 2 * (expiry - submission),
            times[-1] + timedelta(minutes=1),
        )
    direction = 1 if str(row["side"]).upper() == "LONG" else -1
    entry = float(row["entry_price"])
    stop0 = float(row["stop_loss"])
    target0 = float(row["take_profit_1"])
    risk0 = abs(entry - stop0)
    stop, target, stop_mult = geometry_for(variant, entry, stop0, target0, direction, risk0)
    risk = abs(entry - stop)
    import bisect as _bisect

    start = max(0, _bisect.bisect_right(times, submission) - 1)
    end = min(len(times), _bisect.bisect_left(times, expiry) + 1)
    lifecycle = resolve_post_submission_m1_lifecycle(
        bars[start:end],
        m1_open_times_utc=times[start:end],
        direction=direction,
        proposed_order_type=row["proposed_order_type"],
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
    deductible = float(row["deductible_cost_r"]) / stop_mult
    status = lifecycle.lifecycle_label_status
    gross = (
        float(lifecycle.terminal_gross_r)
        if status.startswith("RESOLVED_FILLED_")
        else None
    )
    net = gross - deductible if gross is not None else None
    hold_minutes = None
    if status.startswith("RESOLVED_FILLED_") and lifecycle.terminal_time_utc:
        hold_minutes = (at(str(lifecycle.terminal_time_utc)) - submission).total_seconds() / 60
    return {
        "variant": variant,
        "status": status,
        "gross_r": gross,
        "net_r": net,
        "stop_mult": stop_mult,
        "hold_minutes": hold_minutes,
    }


def summarize(records):
    filled = [r for r in records if r["status"].startswith("RESOLVED_FILLED_")]
    states = Counter(r["status"].removeprefix("RESOLVED_FILLED_") for r in filled)
    nets = [r["net_r"] for r in filled if r["net_r"] is not None]
    return {
        "n": len(records),
        "filled": len(filled),
        "no_fill": sum(1 for r in records if r["status"] == "RESOLVED_NO_FILL"),
        "censored": sum(1 for r in records if r["status"].startswith("CENSORED")),
        "target": states.get("TARGET", 0),
        "stop": states.get("STOP", 0),
        "time_stop": states.get("TIME_STOP", 0),
        "net_r_sum": round(sum(nets), 3),
        "net_r_mean": round(statistics.fmean(nets), 4) if nets else None,
    }


def main() -> None:
    selected, near = candidate_sets()
    rows_by_key = {}
    month_of_key = {}
    for month in ("feb", "april", "may"):
        for row in read_rows(CACHE / f"rows_{month}.jsonl.gz"):
            key = row["candidate_occurrence_key"]
            rows_by_key[key] = row
            month_of_key[key] = month
    log(sets=True, selected=sum(len(v) for v in selected.values()),
        near=sum(len(v) for v in near.values()))

    windows = PREREG["validation"]["windows"]
    bindings = {
        "feb": ("february_2026.json", PREREG["bindings"]["february_manifest_root_sha256"]),
        "april": ("april_2026.json", next(w["manifest_root_sha256"] for w in windows
                                          if w["window_id"] == "april_2026")),
        "may": ("may_2026.json", next(w["manifest_root_sha256"] for w in windows
                                      if w["window_id"] == "may_2026")),
    }

    all_keys = set()
    for tag in ("feb", "aprmay"):
        all_keys.update(selected[tag])
        all_keys.update(near[tag])
    missing = [k for k in all_keys if k not in rows_by_key]
    if missing:
        raise ValueError(f"{len(missing)} keys missing from caches")

    selected_set = {k for tag in selected for k in selected[tag]}
    out_rows = []
    control_mismatch = []
    rr_values = Counter()
    for month in ("feb", "april", "may"):
        month_keys = sorted(k for k in all_keys if month_of_key[k] == month)
        if not month_keys:
            continue
        manifest_name, expected_root = bindings[month]
        _root, sources = r3b.load_m1_sources(r3b.MANIFEST_DIR / manifest_name, expected_root)
        log(bundle=month, keys=len(month_keys))
        for key in month_keys:
            row = rows_by_key[key]
            rr = row.get("risk_reward_ratio")
            rr_values[round(float(rr), 2) if rr is not None else None] += 1
            for variant in VARIANTS:
                result = walk(row, sources, variant)
                if variant == "native_recon":
                    recorded = row["lifecycle_label_status"]
                    if result["status"] != recorded or (
                        result["net_r"] is not None
                        and row.get("terminal_net_r") is not None
                        and abs(result["net_r"] - float(row["terminal_net_r"])) > 1e-9
                    ):
                        control_mismatch.append(
                            {"key": key, "recorded": recorded,
                             "recomputed": result["status"],
                             "net_recorded": row.get("terminal_net_r"),
                             "net_recomputed": result["net_r"]}
                        )
                out_rows.append({
                    "key": key,
                    "month": month,
                    "set": "selected" if key in selected_set else "near_selected",
                    "family": row["origin_family"],
                    "symbol": row["symbol"],
                    "order_type": row["proposed_order_type"],
                    **result,
                })
        del sources
        log(walked=month, rows=len(out_rows))

    with gzip.open(CACHE / "geometry_rows.jsonl.gz", "wt") as fh:
        for rec in out_rows:
            fh.write(json.dumps(
                {k: (None if isinstance(v, float) and not math.isfinite(v) else v)
                 for k, v in rec.items()}, sort_keys=True) + "\n")

    tables = {}
    for set_name in ("selected", "near_selected", "both"):
        rows = [r for r in out_rows if set_name == "both" or r["set"] == set_name]
        per = {}
        for scope_name, scope in (
            ("all_three_months", lambda r: True),
            ("feb", lambda r: r["month"] == "feb"),
            ("april", lambda r: r["month"] == "april"),
            ("may", lambda r: r["month"] == "may"),
        ):
            scoped = [r for r in rows if scope(r)]
            per[scope_name] = {
                variant: summarize([r for r in scoped if r["variant"] == variant])
                for variant in VARIANTS
            }
        by_family = {}
        for family in sorted({r["family"] for r in rows}):
            fam_rows = [r for r in rows if r["family"] == family]
            by_family[family] = {
                variant: summarize([r for r in fam_rows if r["variant"] == variant])
                for variant in VARIANTS
            }
        tables[set_name] = {"per_scope": per, "by_family": by_family}

    receipt = {
        "schema": "gtos.wave21.postmortem.geometry.v1",
        "status": "IN_SAMPLE_DEVELOPMENT_DIAGNOSTIC_AFTER_ALL_READS_NOT_A_CHOSEN_GEOMETRY",
        "unit_convention": (
            "each variant's R is in units of its own risk distance (fixed-risk-cash "
            "sizing); deductible scales 1/stop_mult; swap holding-time dependence not "
            "re-modelled"
        ),
        "variants": list(VARIANTS),
        "set_sizes": {
            "selected": sum(len(v) for v in selected.values()),
            "near_selected": sum(len(v) for v in near.values()),
        },
        "native_risk_reward_ratio_distribution": {
            str(k): v for k, v in sorted(rr_values.items(), key=lambda kv: str(kv[0]))
        },
        "control": {
            "native_recon_mismatches": len(control_mismatch),
            "examples": control_mismatch[:10],
        },
        "tables": tables,
    }
    (RECEIPTS / "PM_GEOMETRY_V1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    log(done=True, control_mismatches=len(control_mismatch))


if __name__ == "__main__":
    main()
