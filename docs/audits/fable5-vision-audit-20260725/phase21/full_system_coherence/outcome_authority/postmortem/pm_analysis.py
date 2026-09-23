#!/usr/bin/env python3
"""Three-month postmortem — stage 3: April autopsy + family scope.

Everything here is a DEVELOPMENT DIAGNOSTIC computed after the February PASS and the
April+May REJECT were read. Nothing is a frozen rule; every stand-down replay is
in-sample by construction and labeled so in the receipts.

Inputs: stage-1 caches (rows, predictions, window audits), stage-2 regime arrays,
both sealed result JSONs. Outputs:
  RECEIPTS/PM_AUTOPSY_V1.json
  RECEIPTS/PM_FAMILY_SCOPE_V1.json
"""
from __future__ import annotations

import bisect
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

WT_NEW = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(WT_NEW))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pm_regime import classify  # noqa: E402

RECEIPTS = Path(__file__).resolve().parent
OA = RECEIPTS.parent
CACHE = Path("/private/tmp/w21-postmortem-cache-20260811")

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


def month_of(row):
    return row["month"]


def state_of(row):
    status = row["lifecycle_label_status"]
    mapping = {
        "RESOLVED_NO_FILL": "NO_FILL",
        "RESOLVED_FILLED_TARGET": "TARGET",
        "RESOLVED_FILLED_STOP": "STOP",
        "RESOLVED_FILLED_TIME_STOP": "TIME_STOP",
    }
    if status in mapping:
        return mapping[status]
    return "CENSORED"


def eligible(row):
    cost = row.get("cost_r")
    return bool(row.get("predecision_geometry_valid")) and cost is not None and cost <= 0.20


def net_of(row):
    value = row.get("terminal_net_r")
    return float(value) if value is not None else None


# ---------------------------------------------------------------- regime join
class RegimeLookup:
    def __init__(self):
        self._by_symbol = {}

    def _load(self, symbol):
        if symbol not in self._by_symbol:
            data = np.load(CACHE / f"regime_m15_{symbol.replace('.', '_')}.npz")
            self._by_symbol[symbol] = {k: data[k] for k in data.files}
        return self._by_symbol[symbol]

    def at_decision(self, symbol, when_iso):
        """Dial values at the last M15 bar CLOSED at or before the decision instant.

        Bar open times are stored; a bar is closed once open+15m <= decision. The margin
        is returned so the leakage audit can assert closed-bar-only globally.
        """
        arrays = self._load(symbol)
        when = datetime.fromisoformat(str(when_iso).replace("Z", "+00:00")).timestamp()
        i = int(np.searchsorted(arrays["epoch"], when - 900.0, side="right")) - 1
        if i < 0:
            return None
        margin = (when - 900.0) - float(arrays["epoch"][i])
        out = {
            key: (None if math.isnan(float(arrays[key][i])) else float(arrays[key][i]))
            for key in ("vol_regime", "slope20", "slope50", "rng_pos", "comp", "ac60")
        }
        out["closed_bar_margin_s"] = margin
        return out


# ---------------------------------------------------------------- tables
def completion_cell(rows):
    states = Counter(state_of(row) for row in rows)
    filled = states["TARGET"] + states["STOP"] + states["TIME_STOP"]
    nets = [net_of(row) for row in rows if row.get("cost_label_status") == "COMPLETE"]
    nets = [value for value in nets if value is not None]
    return {
        "eligible": len(rows),
        "no_fill": states["NO_FILL"],
        "filled": filled,
        "target": states["TARGET"],
        "stop": states["STOP"],
        "time_stop": states["TIME_STOP"],
        "censored": states["CENSORED"],
        "target_rate_of_filled": round(states["TARGET"] / filled, 4) if filled else None,
        "time_stop_rate_of_filled": round(states["TIME_STOP"] / filled, 4) if filled else None,
        "net_r_sum": round(sum(nets), 3),
        "net_r_mean": round(statistics.fmean(nets), 4) if nets else None,
    }


def dedup_first(rows):
    """One row per candidate_id: the earliest occurrence (persistent candidates re-offer
    for hundreds of windows; occurrence-level sums overweight them)."""
    best = {}
    for row in rows:
        cid = row.get("candidate_id") or row["candidate_occurrence_key"]
        key = (row["label_span_start_utc"], row["candidate_occurrence_key"])
        if cid not in best or key < best[cid][0]:
            best[cid] = (key, row)
    return [row for _key, row in best.values()]


def completion_tables(rows_by_month):
    out = {}
    for month, rows in rows_by_month.items():
        el = [row for row in rows if eligible(row)]
        ded = dedup_first(el)
        cell = {
            "occurrence_level": completion_cell(el),
            "candidate_dedup_first": completion_cell(ded),
            "by_family": {},
            "by_symbol_class": {},
            "by_family_x_class": {},
        }
        for fam in sorted({row["origin_family"] for row in el}):
            fam_rows = [row for row in el if row["origin_family"] == fam]
            cell["by_family"][fam] = completion_cell(fam_rows)
            cell["by_family"][fam]["dedup"] = completion_cell(dedup_first(fam_rows))
        for cls in sorted({classify(row["symbol"]) for row in el}):
            cls_rows = [row for row in el if classify(row["symbol"]) == cls]
            cell["by_symbol_class"][cls] = completion_cell(cls_rows)
        for fam in sorted({row["origin_family"] for row in el}):
            for cls in sorted({classify(row["symbol"]) for row in el}):
                sub = [
                    row for row in el
                    if row["origin_family"] == fam and classify(row["symbol"]) == cls
                ]
                if len(sub) >= 50:
                    cell["by_family_x_class"][f"{fam}|{cls}"] = completion_cell(sub)
        out[month] = cell
        log(completion_table=month, eligible=len(el))
    return out


# ---------------------------------------------------------------- separator scan
FEATURES = (
    # regime spine dials at the last closed M15 bar before decision
    "rs_vol_regime", "rs_slope50", "rs_rng_pos", "rs_comp", "rs_ac60",
    # frozen predecision features already on the row (closed-bar by construction)
    "atr14_over_atr50", "close_to_close_vol_8_over_48", "compression_ratio_prior_bar",
    "trigger_bar_range_atr", "trigger_bar_body_atr", "risk_over_atr",
    "close_position_in_lookback_range", "bars_since_session_open",
    "stop_distance_atr", "target_distance_atr", "sweep_depth_atr",
    "session_open_range_width_atr", "dist_to_prior_high20_atr", "dist_to_prior_low20_atr",
)


def rank_auc(values, flags):
    """AUC of value for flag via tie-averaged rank statistic; None-safe."""
    pairs = [(v, f) for v, f in zip(values, flags) if v is not None and math.isfinite(v)]
    if not any(f for _v, f in pairs) or all(f for _v, f in pairs):
        return None
    values_arr = np.asarray([v for v, _f in pairs], dtype=float)
    flags_arr = np.asarray([bool(f) for _v, f in pairs])
    order = values_arr.argsort(kind="mergesort")
    ranked = np.empty(len(values_arr), dtype=float)
    ranked[order] = np.arange(1, len(values_arr) + 1, dtype=float)
    # tie-average
    sorted_vals = values_arr[order]
    i = 0
    while i < len(sorted_vals):
        j = i
        while j < len(sorted_vals) and sorted_vals[j] == sorted_vals[i]:
            j += 1
        ranked[order[i:j]] = (i + j + 1) / 2
        i = j
    n_pos = int(flags_arr.sum())
    n_neg = len(flags_arr) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    auc = (ranked[flags_arr].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    return round(float(auc), 4), n_pos, n_neg


def attach_regime(rows, lookup):
    audit = {"joined": 0, "missing": 0, "min_margin_s": None}
    for row in rows:
        joined = lookup.at_decision(row["symbol"], row["decision_time_utc"])
        if joined is None:
            audit["missing"] += 1
            continue
        margin = joined.pop("closed_bar_margin_s")
        if audit["min_margin_s"] is None or margin < audit["min_margin_s"]:
            audit["min_margin_s"] = margin
        for key, value in joined.items():
            row[f"rs_{key}"] = value
        audit["joined"] += 1
    return audit


def separator_scan(rows_by_month):
    """Per month: AUC of each named decision-time feature for (a) TARGET among filled,
    (b) net>0 among complete. Population-level, occurrence-weighted. IN-SAMPLE."""
    out = {}
    for month, rows in rows_by_month.items():
        el = [row for row in rows if eligible(row)]
        filled = [row for row in el if state_of(row) in ("TARGET", "STOP", "TIME_STOP")]
        complete = [row for row in filled if row.get("cost_label_status") == "COMPLETE"]
        month_out = {"n_filled": len(filled), "features": {}}
        for feature in FEATURES:
            values = [row.get(feature) for row in filled]
            flags = [state_of(row) == "TARGET" for row in filled]
            target_auc = rank_auc(values, flags)
            values_c = [row.get(feature) for row in complete]
            flags_c = [(net_of(row) or 0.0) > 0 for row in complete]
            pos_auc = rank_auc(values_c, flags_c)
            month_out["features"][feature] = {
                "auc_target_completion": target_auc[0] if target_auc else None,
                "auc_positive_net": pos_auc[0] if pos_auc else None,
            }
        out[month] = month_out
        log(separator_scan=month, filled=len(filled))
    return out


# ---------------------------------------------------------------- stand-down replay
def at(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def replay_selection(rows, predictions_by_key, *, keep):
    """The frozen main-policy selection loop over filtered candidates.
    Reproduces s2.select(policy='market_top_abstain') semantics; `keep(row)` is the
    stand-down overlay applied at candidate level BEFORE ranking."""
    by_window = defaultdict(list)
    for row in rows:
        pred = predictions_by_key.get(row["candidate_occurrence_key"])
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
    dispositions = Counter()
    for candidates in ordered:
        decision_at = min(at(row["label_span_start_utc"]) for _, row in candidates)
        active = {sym: end for sym, end in active.items() if end > decision_at}
        available = [
            (pred, -float(row["cost_r"]), row["candidate_occurrence_key"], row)
            for pred, row in candidates
            if row["symbol"] not in active and keep(row)
        ]
        if not available:
            dispositions["no_available_candidate"] += 1
            continue
        pred, _neg, _key, row = max(available, key=lambda item: item[:3])
        if pred < 0.10:
            dispositions["top_below_0p10"] += 1
            continue
        if row["proposed_order_type"] != "MARKET":
            dispositions["top_limit_abstain"] += 1
            continue
        dispositions["trade"] += 1
        selected.append(dict(row, predicted_net_r=pred))
        active[row["symbol"]] = at(row["label_span_end_utc"] or row["limit_first_expiry_utc"])
    return selected, dict(sorted(dispositions.items()))


def portfolio(selected):
    resolved = [row for row in selected if state_of(row) in ("TARGET", "STOP", "TIME_STOP", "NO_FILL")]
    censored = [row for row in selected if state_of(row) == "CENSORED"]
    actual = sum(net_of(row) or 0.0 for row in resolved)
    worst = actual + sum(-1.0 - float(row["deductible_cost_r"]) for row in censored)
    by_day = defaultdict(float)
    for row in resolved:
        by_day[row["trading_day"]] += net_of(row) or 0.0
    days = sorted(by_day)
    series = [round(by_day[d], 4) for d in days]
    cum = np.cumsum(series) if series else np.asarray([])
    max_dd = float(np.max(np.maximum.accumulate(cum) - cum)) if len(cum) else 0.0
    return {
        "selected": len(selected),
        "resolved": len(resolved),
        "censored": len(censored),
        "actual_net_r": round(actual, 4),
        "worst_case_net_r": round(worst, 4),
        "outcomes": dict(sorted(Counter(state_of(row) for row in selected).items())),
        "families": dict(sorted(Counter(row["origin_family"] for row in selected).items())),
        "positive_days": int(sum(1 for value in series if value > 0)),
        "negative_days": int(sum(1 for value in series if value < 0)),
        "max_drawdown_r_daily_close": round(max_dd, 4),
    }


def stand_down_grid(rows_by_month):
    """Fixed, named overlay rules. All IN-SAMPLE (chosen after both reads)."""
    rules = {
        "frozen_baseline": lambda row: True,
        "SD1_vol_regime_m15_lt_0p80": lambda row: not (
            row.get("rs_vol_regime") is not None and row["rs_vol_regime"] < 0.80
        ),
        "SD2_vol_regime_m15_lt_0p90": lambda row: not (
            row.get("rs_vol_regime") is not None and row["rs_vol_regime"] < 0.90
        ),
        "SD3_sorb_only_vol_lt_0p90": lambda row: not (
            row["origin_family"] == "session_open_range_break"
            and row.get("rs_vol_regime") is not None
            and row["rs_vol_regime"] < 0.90
        ),
        "SD4_family_scope_lsr_only": lambda row: row["origin_family"]
        == "liquidity_sweep_reclaim",
    }
    preds = {}
    for tag in ("feb", "aprmay"):
        preds[tag] = {}
        for rec in read_rows(CACHE / f"predictions_{tag}.jsonl.gz"):
            preds[tag][rec["key"]] = float(rec["pred"])
    out = {}
    for month, tag in (("feb", "feb"), ("april", "aprmay"), ("may", "aprmay")):
        rows = [row for row in rows_by_month[month] if eligible(row)]
        month_out = {}
        for name, keep in rules.items():
            selected, dispositions = replay_selection(rows, preds[tag], keep=keep)
            month_out[name] = {"portfolio": portfolio(selected), "dispositions": dispositions}
        sealed = {
            "feb": FEB_RESULT["pooled"]["market_top_abstain"],
            "april": APRMAY_RESULT["per_month"]["april_2026"],
            "may": APRMAY_RESULT["per_month"]["may_2026"],
        }[month]
        month_out["baseline_vs_sealed"] = {
            "selected_mine": month_out["frozen_baseline"]["portfolio"]["selected"],
            "selected_sealed": sealed["selected"],
            "actual_net_r_mine": month_out["frozen_baseline"]["portfolio"]["actual_net_r"],
            "actual_net_r_sealed": sealed["actual_net_r"],
        }
        out[month] = month_out
        log(stand_down=month)
    return out


# ---------------------------------------------------------------- family scope
def day_series(rows):
    by_day = defaultdict(float)
    for row in rows:
        value = net_of(row)
        if value is not None:
            by_day[row["trading_day"]] += value
    return {day: round(value, 4) for day, value in sorted(by_day.items())}


def family_scope(rows_by_month):
    months = ("octnov", "jan", "feb", "april", "may")
    families = sorted(
        {row["origin_family"] for rows in rows_by_month.values() for row in rows}
    )
    out = {"note": "eligible occurrences; dedup = one row per candidate_id at first occurrence",
           "families": {}}
    for fam in families:
        fam_out = {}
        for month in months:
            rows = [
                row for row in rows_by_month[month]
                if eligible(row) and row["origin_family"] == fam
            ]
            if not rows:
                continue
            ded = dedup_first(rows)
            ded_complete = [row for row in ded if row.get("cost_label_status") == "COMPLETE"]
            series = day_series(ded_complete)
            values = list(series.values())
            fam_out[month] = {
                "occurrences_eligible": len(rows),
                "dedup_candidates": len(ded),
                "dedup": completion_cell(ded),
                "dedup_day_series": series,
                "dedup_positive_days": sum(1 for value in values if value > 0),
                "dedup_negative_days": sum(1 for value in values if value < 0),
                "dedup_net_by_symbol_class": {
                    cls: round(
                        sum(
                            net_of(row) or 0.0
                            for row in ded_complete
                            if classify(row["symbol"]) == cls
                        ),
                        3,
                    )
                    for cls in sorted({classify(row["symbol"]) for row in ded_complete})
                },
                "dedup_top_symbols": dict(
                    Counter(row["symbol"] for row in ded).most_common(6)
                ),
            }
        out["families"][fam] = fam_out
        log(family=fam)
    return out


# ---------------------------------------------------------------- selected-trade join
def selected_join(rows_by_month, lookup):
    """Sealed selected trades joined to decision-time features; winners/losers contrast."""
    by_key = {}
    for month in ("feb", "april", "may"):
        for row in rows_by_month[month]:
            by_key[row["candidate_occurrence_key"]] = row
    groups = {
        "feb_selected": [s["candidate_occurrence_key"] for s in FEB_RESULT["selected_candidates"]],
        "aprmay_selected": [
            s["candidate_occurrence_key"] for s in APRMAY_RESULT["selected_candidates"]
        ],
    }
    contrast = {}
    per_trade = []
    for group, keys in groups.items():
        rows = [by_key[k] for k in keys if k in by_key]
        missing = len(keys) - len(rows)
        for row in rows:
            per_trade.append({
                "group": group,
                "key": row["candidate_occurrence_key"],
                "month": row["month"],
                "trading_day": row["trading_day"],
                "family": row["origin_family"],
                "symbol": row["symbol"],
                "symbol_class": classify(row["symbol"]),
                "state": state_of(row),
                "net_r": net_of(row),
                **{f: row.get(f) for f in FEATURES},
            })
        def med(feature, subset):
            values = [row.get(feature) for row in subset]
            values = [v for v in values if v is not None and math.isfinite(v)]
            return round(statistics.median(values), 4) if values else None
        winners = [row for row in rows if (net_of(row) or 0.0) > 0]
        losers = [row for row in rows if (net_of(row) or 0.0) <= 0 and state_of(row) != "CENSORED"]
        contrast[group] = {
            "n": len(rows), "missing_join": missing,
            "winners": len(winners), "losers": len(losers),
            "feature_medians": {
                f: {"winners": med(f, winners), "losers": med(f, losers), "all": med(f, rows)}
                for f in FEATURES
            },
        }
    return contrast, per_trade


def main() -> None:
    rows_by_month = {}
    for month in ("octnov", "jan", "feb", "april", "may"):
        rows_by_month[month] = read_rows(CACHE / f"rows_{month}.jsonl.gz")
        log(loaded_cache=month, rows=len(rows_by_month[month]))

    lookup = RegimeLookup()
    join_audit = {}
    for month in ("jan", "feb", "april", "may"):
        join_audit[month] = attach_regime(rows_by_month[month], lookup)
        log(regime_join=month, **join_audit[month])

    completion = completion_tables(rows_by_month)
    separators = separator_scan(
        {m: rows_by_month[m] for m in ("jan", "feb", "april", "may")}
    )
    contrast, per_trade = selected_join(rows_by_month, lookup)
    stand_down = stand_down_grid(rows_by_month)
    scope = family_scope(rows_by_month)

    autopsy = {
        "schema": "gtos.wave21.postmortem.autopsy.v1",
        "status": "IN_SAMPLE_DEVELOPMENT_DIAGNOSTIC_AFTER_BOTH_READS_NOT_A_RULE",
        "leakage_audit": {
            "regime_join": join_audit,
            "note": "regime features are the last M15 bar with open+15m <= decision time; "
                    "min closed-bar margins above are in seconds and must be >= 0",
        },
        "completion_tables": completion,
        "separator_scan_in_sample": separators,
        "selected_trade_contrast": contrast,
        "stand_down_replays_in_sample": stand_down,
    }
    (RECEIPTS / "PM_AUTOPSY_V1.json").write_text(
        json.dumps(autopsy, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with gzip.open(RECEIPTS / "PM_SELECTED_TRADES_JOINED_V1.jsonl.gz", "wt") as fh:
        for rec in per_trade:
            clean = {
                k: (None if isinstance(v, float) and not math.isfinite(v) else v)
                for k, v in rec.items()
            }
            fh.write(json.dumps(clean, sort_keys=True) + "\n")

    scope_receipt = {
        "schema": "gtos.wave21.postmortem.family_scope.v1",
        "status": "DEVELOPMENT_DIAGNOSTIC_OPEN_MONTHS_ONLY",
        **scope,
    }
    (RECEIPTS / "PM_FAMILY_SCOPE_V1.json").write_text(
        json.dumps(scope_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    log(done=True)


if __name__ == "__main__":
    main()
