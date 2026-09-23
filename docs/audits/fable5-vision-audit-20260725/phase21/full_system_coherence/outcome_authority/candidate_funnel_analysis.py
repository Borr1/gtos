#!/usr/bin/env python3
"""Score the frozen Wave 21 candidate funnel from raw M1 outcomes.

This is intentionally one direct analysis path: full occurrence denominator,
native MARKET/LIMIT intent, causal M1 lifecycle, the existing two-stage
Jeffreys count estimator, and one portfolio choice per decision window.
"""

from __future__ import annotations

import argparse
import bisect
import datetime as dt
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.components.ultimate_book.primitives import Bar
from src.costs.spread_model import load_spread_model
from src.research_infra.lane_rematerialization import (
    RAW_CAMPAIGN_REGISTRY_PATH,
    resolve_registered_raw_campaign_window,
)
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from src.research_infra.walkforward.quote_side import (
    BarQuote,
    resolve_post_submission_m1_lifecycle,
    spread_for,
)

FIT_PATH = REPO / (
    "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/"
    "probability_truth/probability_truth_analysis.py"
)
FIT_SPEC = importlib.util.spec_from_file_location("wave21_probability_truth", FIT_PATH)
assert FIT_SPEC is not None and FIT_SPEC.loader is not None
fit = importlib.util.module_from_spec(FIT_SPEC)
FIT_SPEC.loader.exec_module(fit)

DEVELOPMENT_DAYS = fit.DEVELOPMENT_DAYS
LIMIT_FAMILIES = frozenset(
    {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
)
MAX_COST_R = 0.20
MIN_EXPECTED_NET_R = 0.10
SPEC_PATH = REPO / "src/costs/SYMBOL_AUTHORITY_V1.json"
SPEC_SHA256 = hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest()
SPREAD_MODEL = load_spread_model()
SPREAD_SHA256 = SPREAD_MODEL.artifact_sha256
UTC = dt.timezone.utc


def _utc(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() != dt.timedelta(0):
        raise ValueError(f"not aware UTC: {value!r}")
    return parsed.astimezone(UTC)


def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _occurrence(row: Mapping[str, Any]) -> str:
    key = str(row.get("canonical_replay_candidate_instance_key") or "")
    if not key.startswith("candidate_occurrence_") or len(key) != 85:
        raise ValueError("compact row lacks a valid candidate occurrence")
    return key


def _order_type(row: Mapping[str, Any]) -> str:
    return "LIMIT" if row.get("origin_family") in LIMIT_FAMILIES else "MARKET"


def _parse_run(value: str) -> tuple[str, Path, str]:
    parts = value.split("=", 2)
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("run must be DAY=COMPACT_ROOT=AUTHORITY_SHA256")
    day, root, authority = parts
    if len(authority) != 64 or any(char not in "009abcdef" for char in authority):
        raise argparse.ArgumentTypeError("run authority must be lowercase sha256")
    return day, Path(root), authority


def _source_bundle(day: str):
    window = "october_2025" if day.startswith("2025-10") else "november_2025"
    inputs = resolve_registered_raw_campaign_window(
        registry_path=RAW_CAMPAIGN_REGISTRY_PATH,
        window_id=window,
    )
    sources = inputs.load_raw_campaign_sources(days=(day,))
    inputs.validate_raw_campaign_sources(days=(day,), sources=sources)
    converted = {}
    for symbol, frames in sources.items():
        source = frames["M1"]
        times = tuple(_utc(str(row["time_utc"])) for row in source.rows)
        bars = tuple(
            Bar(
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
            )
            for row in source.rows
        )
        by_hour: dict[dt.datetime, float] = {}
        spreads = []
        for at in times:
            hour = at.replace(minute=0, second=0, microsecond=0)
            if hour not in by_hour:
                by_hour[hour] = spread_for(
                    symbol, hour, account="FTMO", band="mid"
                )
            spreads.append(by_hour[hour])
        converted[symbol] = (source, times, bars, tuple(spreads))
    return str(inputs.source_manifest["manifest_root_sha256"]), converted


def _lifecycle_row(
    source_row: Mapping[str, Any],
    *,
    manifest_root: str,
    sources: Mapping[str, tuple],
) -> dict[str, Any]:
    key = _occurrence(source_row)
    symbol = str(source_row["symbol"])
    source, times, bars, spreads = sources[symbol]
    submission = _utc(str(source_row["decision_time_utc"]))
    expiry = _utc(str(source_row["limit_first_expiry_utc"]))
    start = max(0, bisect.bisect_right(times, submission) - 1)
    end = min(len(times), bisect.bisect_left(times, expiry) + 1)
    entry = float(source_row["entry_price"])
    stop = float(source_row["stop_loss"])
    target = float(source_row["take_profit_1"])
    risk = abs(entry - stop)
    order_type = _order_type(source_row)
    lifecycle = resolve_post_submission_m1_lifecycle(
        bars[start:end],
        m1_open_times_utc=times[start:end],
        direction=1 if str(source_row["side"]).upper() == "LONG" else -1,
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
        symbol_spec_hash_sha256=SPEC_SHA256,
        spread_source_hash_sha256=SPREAD_SHA256,
    )
    deductible = sum(
        float(source_row.get(field) or 0.0)
        for field in ("expected_slippage_r", "swap_cost_r", "commission_r")
    )
    if lifecycle.lifecycle_label_status == "RESOLVED_NO_FILL":
        cost_status, gross, net, label_end = (
            "NOT_APPLICABLE_NO_FILL", None, None, expiry
        )
    elif lifecycle.lifecycle_label_status.startswith("RESOLVED_FILLED_"):
        gross = float(lifecycle.terminal_gross_r)
        cost_status, net = "COMPLETE", gross - deductible
        label_end = _utc(str(lifecycle.terminal_time_utc))
    else:
        cost_status, gross, net, label_end = (
            "INCOMPLETE_OTHER_EXPLICIT_REASON", None, None, None
        )
    geometry = {
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk": risk,
        "submission": submission.isoformat(),
        "expiry_and_horizon": expiry.isoformat(),
    }
    return {
        "candidate_occurrence_key": key,
        "row_key": key,
        "trading_day": str(source_row["trading_day"]),
        "evidence_class": fit.PRIMARY_EVIDENCE_CLASS,
        "proposed_order_type": order_type,
        "origin_family": str(source_row["origin_family"]),
        "utc_session": str(
            source_row.get("session_bucket") or source_row.get("session") or "unknown"
        ),
        # The compact transport retains the already-validated occurrence but not the
        # producer fingerprint preimage. The digest suffix is an analysis identity only.
        "candidate_source_safe_fingerprint_sha256": key.removeprefix(
            "candidate_occurrence_"
        ),
        "proposed_order_policy_hash_sha256": _hash(
            {"occurrence": key, "order_type": order_type}
        ),
        "geometry_contract_hash_sha256": _hash(geometry),
        "arm_id": "CANONICAL_NATIVE_POLICY_COST_0P20_EV_0P10",
        "source_manifest_hash_sha256": manifest_root,
        "source_m1_sha256": source.sha256,
        "lifecycle_label_status": lifecycle.lifecycle_label_status,
        "cost_label_status": cost_status,
        "terminal_gross_r": gross,
        "terminal_net_r": net,
        "label_span_status": "measured" if label_end else "censored",
        "label_span_start_utc": submission.isoformat(),
        "label_span_end_utc": label_end.isoformat() if label_end else None,
        "label_available_utc": label_end.isoformat() if label_end else None,
        "decision_window_id": str(source_row["decision_window_id"]),
        "symbol": symbol,
        "side": str(source_row["side"]),
        "cost_r": float(source_row["cost_r"]),
        "spread_r": float(source_row["spread_r"]),
        "deductible_cost_r": deductible,
        "risk_reward_ratio": float(source_row["risk_reward_ratio"]),
        "predecision_geometry_valid": submission < expiry and risk > 0,
        "censor_reason": lifecycle.censor_reason,
    }


def _load_rows(runs: Sequence[tuple[str, Path, str]]) -> tuple[list[dict], dict]:
    rows, seen, coverage = [], set(), {}
    for day, root, authority in runs:
        sink = ReplayCompactEventSink.open_sealed(
            root=root, expected_authority_root_sha256=authority
        )
        compact = list(sink.ledger("missed"))
        manifest_root, sources = _source_bundle(day)
        converted = [
            _lifecycle_row(row, manifest_root=manifest_root, sources=sources)
            for row in compact
        ]
        for row in converted:
            key = row["candidate_occurrence_key"]
            if key in seen:
                raise ValueError(f"duplicate occurrence across days: {key}")
            seen.add(key)
        rows.extend(converted)
        coverage[day] = {
            "all_occurrences": len(compact),
            "lifecycle_status_counts": dict(
                sorted(Counter(row["lifecycle_label_status"] for row in converted).items())
            ),
        }
    return rows, coverage


def _select(
    rows: Sequence[Mapping[str, Any]],
    tables: Mapping,
) -> list[dict[str, Any]]:
    by_window: dict[str, tuple] = {}
    for row in rows:
        if not row["predecision_geometry_valid"] or row["cost_r"] > MAX_COST_R:
            continue
        prediction = fit._predict(tables, row)
        expected = prediction["expected_modelled_net_r_given_resolved"]
        if (
            prediction["expected_net_status"] != "EVALUATED_EXPECTED_NET"
            or expected is None
            or float(expected) < MIN_EXPECTED_NET_R
        ):
            continue
        item = (float(expected), -row["cost_r"], row["candidate_occurrence_key"], row)
        window = row["decision_window_id"]
        if window not in by_window or item[:3] > by_window[window][:3]:
            by_window[window] = item
    return [dict(item[3], predicted_net_r=item[0]) for _, item in sorted(by_window.items())]


def _selection_result(selected: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    resolved = [row for row in selected if fit._state(row) is not None]
    censored = [row for row in selected if fit._state(row) is None]
    ordering = {
        "CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING",
        "CENSORED_ORDERING_AMBIGUITY",
    }
    unbounded = [row for row in censored if row["lifecycle_label_status"] not in ordering]
    resolved_net = sum(float(row.get("terminal_net_r") or 0.0) for row in resolved)
    lower_bound = resolved_net + sum(
        -1.0 - float(row["deductible_cost_r"])
        for row in censored
        if row["lifecycle_label_status"] in ordering
    )
    return {
        "selected": len(selected),
        "resolved": len(resolved),
        "censored": len(censored),
        "unbounded_source_or_geometry_censors": len(unbounded),
        "predicted_net_r": sum(float(row["predicted_net_r"]) for row in selected),
        "resolved_net_r": resolved_net,
        "worst_case_net_r": lower_bound if not unbounded else None,
        "families": dict(sorted(Counter(row["origin_family"] for row in selected).items())),
        "order_types": dict(sorted(Counter(row["proposed_order_type"] for row in selected).items())),
        "censor_reasons": dict(
            sorted(Counter(row.get("censor_reason") or row["lifecycle_label_status"] for row in censored).items())
        ),
    }


def _development_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_day = defaultdict(list)
    for row in rows:
        by_day[row["trading_day"]].append(row)
    folds = []
    for name, train_days, test_day in fit.FROZEN_DEVELOPMENT_FOLDS:
        train = [
            row
            for day in train_days
            for row in by_day[day]
            if fit._state(row) is not None
        ]
        selected = _select(by_day[test_day], fit._tables(train))
        folds.append({"fold": name, "test_day": test_day, **_selection_result(selected)})
    pooled = {
        field: sum(fold[field] for fold in folds)
        for field in (
            "selected", "resolved", "censored",
            "unbounded_source_or_geometry_censors",
            "predicted_net_r", "resolved_net_r",
        )
    }
    pooled["worst_case_net_r"] = (
        sum(float(fold["worst_case_net_r"]) for fold in folds)
        if all(fold["worst_case_net_r"] is not None for fold in folds)
        else None
    )
    return {"folds": folds, "pooled": pooled}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development-run", action="append", type=_parse_run, required=True)
    parser.add_argument("--decision-run", action="append", type=_parse_run, default=[])
    args = parser.parse_args()
    development_days = tuple(day for day, _root, _sha in args.development_run)
    if development_days != DEVELOPMENT_DAYS:
        parser.error(f"development runs must be exactly {DEVELOPMENT_DAYS!r}")
    development_rows, development_coverage = _load_rows(args.development_run)
    report: dict[str, Any] = {
        "schema": "gtos.wave21.candidate_funnel_analysis.v1",
        "rule": {
            "max_cost_r": MAX_COST_R,
            "min_expected_net_r": MIN_EXPECTED_NET_R,
            "max_candidates_per_decision_window": 1,
            "rank": "expected_net_desc_then_cost_asc_then_occurrence_key_desc",
        },
        "development_coverage": development_coverage,
        "development": _development_report(development_rows),
    }
    if args.decision_run:
        decision_rows, decision_coverage = _load_rows(args.decision_run)
        tables = fit._tables(
            [row for row in development_rows if fit._state(row) is not None]
        )
        by_day = defaultdict(list)
        for row in decision_rows:
            by_day[row["trading_day"]].append(row)
        day_results = {
            day: _selection_result(_select(rows, tables))
            for day, rows in sorted(by_day.items())
        }
        pass_days = all(
            result["worst_case_net_r"] is not None
            and result["worst_case_net_r"] > 0
            for result in day_results.values()
        )
        pooled_lower = (
            sum(float(result["worst_case_net_r"]) for result in day_results.values())
            if all(result["worst_case_net_r"] is not None for result in day_results.values())
            else None
        )
        report["decision_coverage"] = decision_coverage
        report["decision_days"] = day_results
        report["decision"] = {
            "pooled_worst_case_net_r": pooled_lower,
            "disposition": (
                "ACTIVATION_CANDIDATE_ECONOMIC_GATE_PASSED_NOT_LIVE_AUTHORITY"
                if pass_days and pooled_lower is not None and pooled_lower > 0
                else "PROMISING_NOT_DEPLOYABLE"
                if pooled_lower is not None and pooled_lower > 0
                else "REJECT"
                if pooled_lower is not None
                else "NOT_EVALUABLE"
            ),
        }
    report["payload_sha256"] = _hash(report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
