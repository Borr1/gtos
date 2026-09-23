#!/usr/bin/env python3
"""Three-month postmortem — stage 7: ranking health + decision-time-available guards.

The population completion tables (stage 3) showed April's tape completed at a near-normal
population rate while the rule's selections completed at 1/49. So the object under
autopsy is the RANKING, not the tape. This stage measures it and prices the two guards
that are actually decision-time available:

  1. CALIBRATION BY DECILE, per month: realized mean net of resolved eligible candidates
     by decile of the frozen ridge's own prediction. If the top decile's realized mean
     collapses in April, the ranking signal died — a measurable, monitorable quantity.
  2. SIGNED-TREND CONTRAST on the selected trades: direction x rs_slope50 (M15, closed
     bar). Prices whether entering against the local trend is what losers share.
  3. SD5 TRAILING BRAKE: stand down day D when the rule's own realized net over the
     prior k trading days of the scored sequence is below -x R. Uses only outcomes
     resolved before D (all lifecycle terminals are intraday; day D-1 outcomes are known
     by D). Variants (k, x) in {(5,2),(5,3),(10,3)}.
  4. SD6 ALIGNMENT FILTER: skip candidates with direction x rs_slope50 < threshold
     (candidate-level, closed-bar); thresholds {-0.5, -1.0}.

ALL IN-SAMPLE: every rule here was formulated after the April+May outcomes were read.
Writes RECEIPTS/PM_RANKING_HEALTH_V1.json.
"""
from __future__ import annotations

import gzip
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

RECEIPTS = Path(__file__).resolve().parent
OA = RECEIPTS.parent
CACHE = Path("/private/tmp/w21-postmortem-cache-20260811")
sys.path.insert(0, str(RECEIPTS))

FEB_RESULT = json.loads(
    (OA / "FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json").read_text()
)
APRMAY_RESULT = json.loads(
    (OA / "APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json").read_text()
)

T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def read_rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def state_of(row):
    return {
        "RESOLVED_NO_FILL": "NO_FILL",
        "RESOLVED_FILLED_TARGET": "TARGET",
        "RESOLVED_FILLED_STOP": "STOP",
        "RESOLVED_FILLED_TIME_STOP": "TIME_STOP",
    }.get(row["lifecycle_label_status"], "CENSORED")


def eligible(row):
    cost = row.get("cost_r")
    return bool(row.get("predecision_geometry_valid")) and cost is not None and cost <= 0.20


def net_of(row):
    value = row.get("terminal_net_r")
    return float(value) if value is not None else None


def at(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def attach_regime(rows):
    from pm_analysis import RegimeLookup

    lookup = RegimeLookup()
    for row in rows:
        joined = lookup.at_decision(row["symbol"], row["decision_time_utc"])
        if joined is None:
            continue
        joined.pop("closed_bar_margin_s", None)
        for key, value in joined.items():
            row[f"rs_{key}"] = value


# ---------------------------------------------------------------- 1. calibration
def calibration(rows_by_month, preds):
    out = {}
    for month, tag in (("jan", None), ("feb", "feb"), ("april", "aprmay"), ("may", "aprmay")):
        if tag is None:
            continue
        rows = [
            row for row in rows_by_month[month]
            if eligible(row) and state_of(row) != "CENSORED"
        ]
        pairs = [
            (preds[tag].get(row["candidate_occurrence_key"]), row)
            for row in rows
        ]
        pairs = [(p, row) for p, row in pairs if p is not None]
        pairs.sort(key=lambda item: item[0])
        n = len(pairs)
        deciles = []
        for d in range(10):
            chunk = pairs[(d * n) // 10:((d + 1) * n) // 10]
            nets = [net_of(row) or 0.0 for _p, row in chunk]
            deciles.append({
                "decile": d + 1,
                "n": len(chunk),
                "pred_lo": round(chunk[0][0], 4) if chunk else None,
                "pred_hi": round(chunk[-1][0], 4) if chunk else None,
                "realized_mean_net_r": round(statistics.fmean(nets), 4) if nets else None,
                "target_rate": round(
                    sum(state_of(row) == "TARGET" for _p, row in chunk) / len(chunk), 4
                ) if chunk else None,
            })
        top = [p for p, _row in pairs if p >= 0.10]
        top_rows = [(p, row) for p, row in pairs if p >= 0.10]
        out[month] = {
            "n_resolved_eligible": n,
            "deciles": deciles,
            "predicted_ge_0p10": {
                "n": len(top),
                "realized_mean_net_r": round(
                    statistics.fmean(net_of(row) or 0.0 for _p, row in top_rows), 4
                ) if top_rows else None,
                "mean_predicted": round(statistics.fmean(top), 4) if top else None,
            },
        }
        log(calibration=month, n=n)
    return out


# ---------------------------------------------------------------- 2. signed trend
def signed_trend_contrast(rows_by_month):
    by_key = {}
    for month in ("feb", "april", "may"):
        for row in rows_by_month[month]:
            by_key[row["candidate_occurrence_key"]] = row
    out = {}
    for group, sealed in (
        ("feb_selected", FEB_RESULT["selected_candidates"]),
        ("aprmay_selected", APRMAY_RESULT["selected_candidates"]),
    ):
        buckets = {"aligned_ge_0": [], "against_0_to_1": [], "against_gt_1": []}
        for compact in sealed:
            row = by_key.get(compact["candidate_occurrence_key"])
            if row is None or row.get("rs_slope50") is None:
                continue
            direction = 1 if str(row["side"]).upper() == "LONG" else -1
            signed = direction * float(row["rs_slope50"])
            value = net_of(row)
            if value is None:
                continue
            if signed >= 0:
                buckets["aligned_ge_0"].append(value)
            elif signed >= -1.0:
                buckets["against_0_to_1"].append(value)
            else:
                buckets["against_gt_1"].append(value)
        out[group] = {
            name: {
                "n": len(values),
                "net_r_sum": round(sum(values), 3),
                "mean": round(statistics.fmean(values), 4) if values else None,
                "positive": sum(1 for value in values if value > 0),
            }
            for name, values in buckets.items()
        }
    return out


# ---------------------------------------------------------------- 3+4 replays
def replay(rows, preds, *, keep=lambda row: True, standdown_days=frozenset()):
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
    active, selected = {}, []
    for candidates in ordered:
        decision_at = min(at(row["label_span_start_utc"]) for _, row in candidates)
        active = {sym: end for sym, end in active.items() if end > decision_at}
        day = candidates[0][1]["trading_day"]
        if day in standdown_days:
            continue
        available = [
            (pred, -float(row["cost_r"]), row["candidate_occurrence_key"], row)
            for pred, row in candidates
            if row["symbol"] not in active and keep(row)
        ]
        if not available:
            continue
        pred, _neg, _key, row = max(available, key=lambda item: item[:3])
        if pred < 0.10 or row["proposed_order_type"] != "MARKET":
            continue
        selected.append(dict(row, predicted_net_r=pred))
        active[row["symbol"]] = at(row["label_span_end_utc"] or row["limit_first_expiry_utc"])
    return selected


def summarize(selected, all_days):
    resolved = [row for row in selected if state_of(row) != "CENSORED"]
    censored = [row for row in selected if state_of(row) == "CENSORED"]
    actual = sum(net_of(row) or 0.0 for row in resolved)
    worst = actual + sum(-1.0 - float(row["deductible_cost_r"]) for row in censored)
    by_day = defaultdict(float)
    for row in resolved:
        by_day[row["trading_day"]] += net_of(row) or 0.0
    series = [by_day.get(day, 0.0) for day in all_days]
    cum = np.cumsum(series) if series else np.asarray([])
    max_dd = float(np.max(np.maximum.accumulate(cum) - cum)) if len(cum) else 0.0
    return {
        "selected": len(selected),
        "actual_net_r": round(actual, 3),
        "worst_case_net_r": round(worst, 3),
        "outcomes": dict(sorted(Counter(state_of(row) for row in selected).items())),
        "max_drawdown_r": round(max_dd, 3),
        "positive_days": sum(1 for value in series if value > 0),
        "negative_days": sum(1 for value in series if value < 0),
    }


def trailing_brake(rows_by_month, preds):
    """SD5: sequential day loop per scored sequence; stand down when the frozen rule's
    realized net over the prior k TRADING days (of the same sequence) < -x."""
    sequences = {
        "feb": (("feb",), "feb"),
        "aprmay": (("april", "may"), "aprmay"),
    }
    sealed_day_net = {}
    for result in (FEB_RESULT, APRMAY_RESULT):
        for day, record in result["days"].items():
            sealed_day_net[day] = record["policies"]["market_top_abstain"]["portfolio"][
                "actual_net_r"
            ]
    out = {}
    for seq_name, (months, tag) in sequences.items():
        rows = [
            row for month in months for row in rows_by_month[month] if eligible(row)
        ]
        days = sorted({row["trading_day"] for row in rows})
        for k, x in ((5, 2.0), (5, 3.0), (10, 3.0)):
            stood, kept_days = set(), []
            for i, day in enumerate(days):
                window = days[max(0, i - k):i]
                trailing = sum(sealed_day_net.get(d, 0.0) for d in window)
                if trailing < -x:
                    stood.add(day)
                else:
                    kept_days.append(day)
            selected = replay(rows, preds[tag], standdown_days=stood)
            summary = summarize(selected, days)
            summary["stood_down_days"] = sorted(stood)
            out[f"{seq_name}_SD5_k{k}_x{x:g}"] = summary
        log(trailing_brake=seq_name)
    return out


def alignment_filter(rows_by_month, preds):
    out = {}
    for month, tag in (("feb", "feb"), ("april", "aprmay"), ("may", "aprmay")):
        rows = [row for row in rows_by_month[month] if eligible(row)]
        days = sorted({row["trading_day"] for row in rows})
        for threshold in (-0.5, -1.0):
            def keep(row, threshold=threshold):
                slope = row.get("rs_slope50")
                if slope is None:
                    return True
                direction = 1 if str(row["side"]).upper() == "LONG" else -1
                return direction * float(slope) >= threshold
            selected = replay(rows, preds[tag], keep=keep)
            out[f"{month}_SD6_signed_slope_ge_{threshold:g}"] = summarize(selected, days)
        log(alignment=month)
    return out


def main() -> None:
    rows_by_month = {}
    for month in ("feb", "april", "may"):
        rows_by_month[month] = read_rows(CACHE / f"rows_{month}.jsonl.gz")
        attach_regime(rows_by_month[month])
        log(loaded=month)
    preds = {}
    for tag in ("feb", "aprmay"):
        preds[tag] = {}
        for record in read_rows(CACHE / f"predictions_{tag}.jsonl.gz"):
            preds[tag][record["key"]] = float(record["pred"])

    receipt = {
        "schema": "gtos.wave21.postmortem.ranking_health.v1",
        "status": "IN_SAMPLE_DEVELOPMENT_DIAGNOSTIC_AFTER_ALL_READS",
        "calibration_by_decile": calibration(rows_by_month, preds),
        "signed_trend_contrast_selected": signed_trend_contrast(rows_by_month),
        "trailing_brake_SD5": trailing_brake(rows_by_month, preds),
        "alignment_filter_SD6": alignment_filter(rows_by_month, preds),
        "notes": [
            "SD5 uses only prior trading days' realized nets of the frozen rule itself; "
            "every lifecycle terminal in these windows resolves the same day, so the "
            "trailing sum is decision-time available at day open",
            "SD6 uses the M15 closed-bar slope50 at decision (leakage audit in "
            "PM_AUTOPSY_V1.json); thresholds chosen AFTER seeing the loser contrast — "
            "in-sample by construction",
        ],
    }
    (RECEIPTS / "PM_RANKING_HEALTH_V1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    log(done=True)


if __name__ == "__main__":
    main()
