#!/usr/bin/env python3
"""Three-month postmortem — stage 6: occupancy cost + lifecycle shape (owner directive).

(a) OCCUPANCY: decision windows where the unconstrained top-ranked candidate was excluded
    because its symbol was occupied by an earlier selected position; what the blocked
    candidate went on to do, split by how the occupying position eventually died.
    IN-SAMPLE diagnostic: blocked candidates' outcomes are read post hoc.
(b) TIME-TO-TERMINAL + MFE: for the frozen rule's filled selected trades (and the
    near-selected pool for signal tables), the M1 max-favorable-excursion path from
    submission to terminal, and P(eventual TARGET | MFE < x by t) tables per family.
(c) EARLY-EXIT pricing on the selected set: exit at bar close when MFE < x at t minutes.
    Exit marks use the same BID tape; short exits add the recorded entry spread_r as the
    exit-side cost proxy. Approximation caveats recorded in the receipt.

Writes RECEIPTS/PM_LIFECYCLE_SHAPE_V1.json.
"""
from __future__ import annotations

import bisect
import gzip
import importlib.util
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

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
r3b = load_module("pm_shape_r3b", OA / "w21_score_aprmay_r3b.py")

FEB_RESULT = json.loads(
    (OA / "FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json").read_text()
)
APRMAY_RESULT = json.loads(
    (OA / "APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json").read_text()
)
PREREG = json.loads((OA / "APRIL_MAY_MARKET_TOP_CHOICE_PREREG_V1_6.json").read_text())

MFE_MINUTES = (60, 120, 180, 240)
MFE_FRACTIONS = (0.25, 0.50, 0.75)  # of the 2.0R generic target -> 0.5R, 1.0R, 1.5R MFE


def read_rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def at(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def state_of(row):
    status = row["lifecycle_label_status"]
    return {
        "RESOLVED_NO_FILL": "NO_FILL",
        "RESOLVED_FILLED_TARGET": "TARGET",
        "RESOLVED_FILLED_STOP": "STOP",
        "RESOLVED_FILLED_TIME_STOP": "TIME_STOP",
    }.get(status, "CENSORED")


def eligible(row):
    cost = row.get("cost_r")
    return bool(row.get("predecision_geometry_valid")) and cost is not None and cost <= 0.20


def net_of(row):
    value = row.get("terminal_net_r")
    return float(value) if value is not None else None


# ---------------------------------------------------------------- (a) occupancy
def occupancy_replay(rows, preds):
    """Frozen main-policy loop, additionally recording the unconstrained top of every
    window and whether same-symbol occupancy blocked it."""
    by_window = defaultdict(list)
    for row in rows:
        pred = preds.get(row["candidate_occurrence_key"])
        if pred is None:
            continue
        by_window[row["decision_window_id"]].append((pred, row))
    ordered = sorted(
        by_window.values(),
        key=lambda values: (
            min(at(row["label_span_start_utc"]) for _, row in values),
            values[0][1]["decision_window_id"],
        ),
    )
    active, owner = {}, {}
    selected = []
    blocked = []
    for candidates in ordered:
        decision_at = min(at(row["label_span_start_utc"]) for _, row in candidates)
        active = {sym: end for sym, end in active.items() if end > decision_at}
        owner = {sym: rec for sym, rec in owner.items() if sym in active}
        ranked_all = sorted(
            ((pred, -float(row["cost_r"]), row["candidate_occurrence_key"], row)
             for pred, row in candidates),
            reverse=True,
        )
        unc_pred, _c, _k, unc_row = ranked_all[0]
        available = [item for item in ranked_all if item[3]["symbol"] not in active]
        if (
            unc_row["symbol"] in active
            and unc_pred >= 0.10
            and unc_row["proposed_order_type"] == "MARKET"
        ):
            blocked.append({
                "window": unc_row["decision_window_id"],
                "trading_day": unc_row["trading_day"],
                "candidate_id": unc_row.get("candidate_id") or unc_row["candidate_occurrence_key"],
                "key": unc_row["candidate_occurrence_key"],
                "family": unc_row["origin_family"],
                "symbol": unc_row["symbol"],
                "pred": round(unc_pred, 4),
                "blocked_state": state_of(unc_row),
                "blocked_net": net_of(unc_row),
                "occupier_key": owner.get(unc_row["symbol"], {}).get("key"),
                "occupier_state": owner.get(unc_row["symbol"], {}).get("state"),
            })
        if not available:
            continue
        pred, _neg, _key, row = available[0]
        if pred < 0.10 or row["proposed_order_type"] != "MARKET":
            continue
        selected.append(row)
        end = at(row["label_span_end_utc"] or row["limit_first_expiry_utc"])
        active[row["symbol"]] = end
        owner[row["symbol"]] = {"key": row["candidate_occurrence_key"], "state": state_of(row)}
    return selected, blocked


def occupancy_tables(blocked):
    by_occupier = defaultdict(lambda: {"windows": 0, "dedup": {}})
    for record in blocked:
        cell = by_occupier[record["occupier_state"] or "UNKNOWN"]
        cell["windows"] += 1
        cid = record["candidate_id"]
        if cid not in cell["dedup"]:
            cell["dedup"][cid] = record
    out = {}
    for occ_state, cell in sorted(by_occupier.items()):
        ded = list(cell["dedup"].values())
        nets = [record["blocked_net"] for record in ded if record["blocked_net"] is not None]
        out[occ_state] = {
            "blocked_windows": cell["windows"],
            "blocked_distinct_candidates": len(ded),
            "blocked_candidates_net_r_sum_dedup": round(sum(nets), 3),
            "blocked_candidates_positive": sum(1 for value in nets if value > 0),
            "blocked_candidates_negative": sum(1 for value in nets if value < 0),
            "blocked_target_completions": sum(
                1 for record in ded if record["blocked_state"] == "TARGET"
            ),
        }
    return out


# ---------------------------------------------------------------- (b)+(c) MFE walks
def mfe_walk(row, sources):
    """MFE/MAE path in native-R from submission to recorded terminal on the month M1 tape.
    Approximation: excursions measured against the approved entry price on the BID tape;
    fill microstructure not re-modelled (stated caveat)."""
    symbol = row["symbol"]
    _src, times, bars, _spreads = sources[symbol]
    submission = at(row["decision_time_utc"])
    terminal = at(row["label_span_end_utc"]) if row.get("label_span_end_utc") else None
    if terminal is None:
        return None
    direction = 1 if str(row["side"]).upper() == "LONG" else -1
    entry = float(row["entry_price"])
    risk = abs(entry - float(row["stop_loss"]))
    if risk <= 0:
        return None
    start = bisect.bisect_right(times, submission)
    end = min(len(times), bisect.bisect_left(times, terminal) + 1)
    if start >= end:
        return None
    mfe_at = {}
    running = -math.inf
    closes_at = {}
    for i in range(start, end):
        bar = bars[i]
        favorable = (bar.h - entry) if direction == 1 else (entry - bar.l)
        running = max(running, favorable / risk)
        minutes = (times[i] - submission).total_seconds() / 60
        for t in MFE_MINUTES:
            if minutes <= t:
                mfe_at[t] = running
                closes_at[t] = (i, (bar.c - entry) * direction / risk)
    minutes_total = (terminal - submission).total_seconds() / 60
    return {
        "mfe_at": {str(t): (None if t not in mfe_at else round(mfe_at[t], 4))
                   for t in MFE_MINUTES},
        "mark_at": {str(t): (None if t not in closes_at else round(closes_at[t][1], 4))
                    for t in MFE_MINUTES},
        "minutes_to_terminal": round(minutes_total, 1),
    }


def main() -> None:
    rows_by_month = {}
    rows_by_key = {}
    for month in ("feb", "april", "may"):
        rows_by_month[month] = read_rows(CACHE / f"rows_{month}.jsonl.gz")
        for row in rows_by_month[month]:
            rows_by_key[row["candidate_occurrence_key"]] = row
    preds = {}
    for tag in ("feb", "aprmay"):
        preds[tag] = {}
        for rec in read_rows(CACHE / f"predictions_{tag}.jsonl.gz"):
            preds[tag][rec["key"]] = float(rec["pred"])

    # ---- (a) occupancy
    sealed_selected = {
        "feb": [s["candidate_occurrence_key"] for s in FEB_RESULT["selected_candidates"]],
        "aprmay": [
            s["candidate_occurrence_key"] for s in APRMAY_RESULT["selected_candidates"]
        ],
    }
    occupancy = {}
    for month, tag in (("feb", "feb"), ("april", "aprmay"), ("may", "aprmay")):
        rows = [row for row in rows_by_month[month] if eligible(row)]
        selected, blocked = occupancy_replay(rows, preds[tag])
        expected = [k for k in sealed_selected[tag] if rows_by_key[k]["month"] == month]
        assert [row["candidate_occurrence_key"] for row in selected] == expected, (
            f"occupancy replay diverged from sealed selection: {month}"
        )
        occupancy[month] = {
            "blocked_top_windows": len(blocked),
            "by_occupier_terminal_state": occupancy_tables(blocked),
        }
        log(occupancy=month, blocked=len(blocked))

    # ---- (b)/(c) lifecycle shape on selected + near-selected
    geometry_rows = read_rows(CACHE / "geometry_rows.jsonl.gz")
    native_by_key = {}
    for record in geometry_rows:
        if record["variant"] == "native_recon":
            native_by_key.setdefault(record["key"], record)
    windows = PREREG["validation"]["windows"]
    bindings = {
        "feb": ("february_2026.json", PREREG["bindings"]["february_manifest_root_sha256"]),
        "april": ("april_2026.json", next(w["manifest_root_sha256"] for w in windows
                                          if w["window_id"] == "april_2026")),
        "may": ("may_2026.json", next(w["manifest_root_sha256"] for w in windows
                                      if w["window_id"] == "may_2026")),
    }
    selected_set = {k for tag in sealed_selected for k in sealed_selected[tag]}

    shape_rows = []
    for month in ("feb", "april", "may"):
        month_keys = [
            key for key in native_by_key
            if key in rows_by_key and rows_by_key[key]["month"] == month
        ]
        manifest_name, expected_root = bindings[month]
        _root, sources = r3b.load_m1_sources(r3b.MANIFEST_DIR / manifest_name, expected_root)
        for key in month_keys:
            row = rows_by_key[key]
            if state_of(row) not in ("TARGET", "STOP", "TIME_STOP"):
                continue
            walked = mfe_walk(row, sources)
            if walked is None:
                continue
            shape_rows.append({
                "key": key,
                "set": "selected" if key in selected_set else "near_selected",
                "month": month,
                "family": row["origin_family"],
                "state": state_of(row),
                "net": net_of(row),
                "deductible": float(row["deductible_cost_r"]),
                "spread_r": row.get("spread_r"),
                **walked,
            })
        del sources
        log(shape_walked=month, rows=len(shape_rows))

    # (b) time-to-terminal + P(TARGET | MFE < x by t) per family
    shape_tables = {}
    for scope_name, scope_rows in (
        ("selected", [r for r in shape_rows if r["set"] == "selected"]),
        ("selected_plus_near", shape_rows),
    ):
        per_family = {}
        for family in sorted({r["family"] for r in scope_rows}):
            fam = [r for r in scope_rows if r["family"] == family]
            by_state = {}
            for state in ("TARGET", "STOP", "TIME_STOP"):
                sub = [r["minutes_to_terminal"] for r in fam if r["state"] == state]
                if sub:
                    sub.sort()
                    by_state[state] = {
                        "n": len(sub),
                        "p25_min": round(sub[len(sub) // 4], 1),
                        "p50_min": round(sub[len(sub) // 2], 1),
                        "p75_min": round(sub[(3 * len(sub)) // 4], 1),
                    }
            signal = {}
            for t in MFE_MINUTES:
                for frac in MFE_FRACTIONS:
                    threshold = 2.0 * frac
                    known = [r for r in fam if r["mfe_at"][str(t)] is not None]
                    below = [r for r in known if r["mfe_at"][str(t)] < threshold]
                    above = [r for r in known if r["mfe_at"][str(t)] >= threshold]
                    if len(known) >= 20 and below and above:
                        signal[f"t{t}_below_{frac}"] = {
                            "n_below": len(below),
                            "target_rate_below": round(
                                sum(r["state"] == "TARGET" for r in below) / len(below), 4
                            ),
                            "target_rate_above": round(
                                sum(r["state"] == "TARGET" for r in above) / len(above), 4
                            ),
                            "mean_net_below": round(
                                statistics.fmean(r["net"] for r in below), 4
                            ),
                            "mean_net_above": round(
                                statistics.fmean(r["net"] for r in above), 4
                            ),
                        }
            per_family[family] = {"time_to_terminal_by_state": by_state,
                                  "mfe_signal": signal}
        shape_tables[scope_name] = per_family

    # (c) early-exit pricing on the SELECTED set
    early_exit = {}
    for t in MFE_MINUTES:
        for frac in MFE_FRACTIONS:
            threshold = 2.0 * frac
            per_month = {}
            for month in ("feb", "april", "may"):
                sub = [r for r in shape_rows if r["set"] == "selected" and r["month"] == month]
                native_total, ruled_total, exited = 0.0, 0.0, 0
                for r in sub:
                    native_total += r["net"]
                    mfe = r["mfe_at"][str(t)]
                    mark = r["mark_at"][str(t)]
                    if (
                        mfe is not None and mark is not None
                        and r["minutes_to_terminal"] > t
                        and mfe < threshold
                    ):
                        exit_cost = r["deductible"] + (r.get("spread_r") or 0.0)
                        ruled_total += mark - exit_cost
                        exited += 1
                    else:
                        ruled_total += r["net"]
                per_month[month] = {
                    "native_net_r": round(native_total, 3),
                    "rule_net_r": round(ruled_total, 3),
                    "delta_r": round(ruled_total - native_total, 3),
                    "n_exited": exited,
                    "n": len(sub),
                }
            early_exit[f"exit_if_mfe_lt_{frac}_of_target_at_{t}min"] = per_month

    receipt = {
        "schema": "gtos.wave21.postmortem.lifecycle_shape.v1",
        "status": "IN_SAMPLE_DEVELOPMENT_DIAGNOSTIC_AFTER_ALL_READS",
        "caveats": [
            "MFE measured against approved entry price on the month's BID M1 tape; fill "
            "microstructure and intrabar ordering not re-modelled",
            "early-exit marks price the exit at the M1 bar close on the same tape, "
            "charging the recorded deductible plus the entry spread_r as exit-side proxy",
            "blocked-candidate outcomes are read post hoc; occupancy deltas are not a "
            "tradable claim, they price the occupancy rule's cost",
        ],
        "occupancy": occupancy,
        "lifecycle_shape": shape_tables,
        "early_exit_pricing_selected": early_exit,
    }
    (RECEIPTS / "PM_LIFECYCLE_SHAPE_V1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    log(done=True)


if __name__ == "__main__":
    main()
