#!/usr/bin/env python3
from __future__ import annotations

import bisect
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np

REPO = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
ROOT = Path("/private/tmp/w21-market-top-feb-r2")
RIDGE_SOURCE = Path("/private/tmp/w21_predecision_ridge.py")
RULE_PATH = REPO / (
    "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/"
    "outcome_authority/MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json"
)
OUTPUT = ROOT / "FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json"
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST = HOLD / (
    ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/"
    "manifests/february_2026.json"
)
sys.path.insert(0, str(REPO))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


r = load_module("w21_ridge_for_feb_validation", RIDGE_SOURCE)
from src.components import broader_origin_generators as bog
from src.components.ultimate_book.primitives import Bar
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from src.research_infra.walkforward.quote_side import spread_for


def canonical_hash(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def at(value: object) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return np.nan
    return result if math.isfinite(result) else np.nan


def load_m1_sources():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["manifest_root_sha256"] != (
        "955937e4f0c4c66ea95dcf52f1c3ac1a40b90e7c00411a9b1490e19a623e9148"
    ):
        raise ValueError("February manifest root changed")
    bundle = {}
    for entry in manifest["bar_sources"]:
        if entry["timeframe"] != "M1":
            continue
        path = HOLD / entry["repo_relpath"]
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"February M1 hash mismatch: {path}")
        times, bars = [], []
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["time", "open", "high", "low", "close", "volume"]:
                raise ValueError(f"February M1 schema mismatch: {path}")
            for row in reader:
                times.append(r.m._utc(row["time"]))
                bars.append(
                    Bar(
                        float(row["open"]),
                        float(row["high"]),
                        float(row["low"]),
                        float(row["close"]),
                    )
                )
        if len(times) != entry["row_count"] or any(
            left >= right for left, right in zip(times, times[1:])
        ):
            raise ValueError(f"February M1 chronology mismatch: {path}")
        spread_cache, spreads = {}, []
        for instant in times:
            hour = instant.replace(minute=0, second=0, microsecond=0)
            if hour not in spread_cache:
                spread_cache[hour] = spread_for(
                    entry["symbol"], hour, account="FTMO", band="mid"
                )
            spreads.append(spread_cache[hour])
        bundle[entry["symbol"]] = (
            SimpleNamespace(sha256=entry["sha256"]),
            tuple(times),
            tuple(bars),
            tuple(spreads),
        )
    if len(bundle) != 24:
        raise ValueError("February M1 symbol denominator is not 24")
    return manifest["manifest_root_sha256"], bundle


def feature_row(raw, label):
    when = at(raw["decision_time_utc"])
    family = str(raw["origin_family"])
    symbol = str(raw["symbol"])
    side = str(raw["side"]).upper()
    session = str(raw.get("session_bucket") or raw.get("session") or "unknown")
    fillability = raw.get("predecision_limit_fillability")
    fillability = fillability if isinstance(fillability, dict) else {}
    poi = raw.get("poi_state")
    poi = poi if isinstance(poi, dict) else {}
    source_features = raw.get("predecision_features")
    if not isinstance(source_features, dict) or set(source_features) != set(
        bog.PREDECISION_FEATURE_KEYS
    ):
        raise ValueError(
            f"predecision feature contract missing: {raw.get('candidate_occurrence_key')}"
        )
    risk = abs(number(raw.get("entry_price")) - number(raw.get("stop_loss")))
    atr = number(fillability.get("atr14"))
    entry = abs(number(raw.get("entry_price")))
    row = {
        "candidate_occurrence_key": label["candidate_occurrence_key"],
        "candidate_id": str(raw.get("candidate_id") or ""),
        "decision_window_id": label["decision_window_id"],
        "trading_day": label["trading_day"],
        "label_span_start_utc": label["label_span_start_utc"],
        "label_span_end_utc": label["label_span_end_utc"],
        "expiry_utc": str(raw["limit_first_expiry_utc"]),
        "lifecycle_label_status": label["lifecycle_label_status"],
        "cost_label_status": label["cost_label_status"],
        "terminal_net_r": label["terminal_net_r"],
        "deductible_cost_r": label["deductible_cost_r"],
        "predecision_geometry_valid": bool(label["predecision_geometry_valid"]),
        "symbol": symbol,
        "side": side,
        "origin_family": family,
        "utc_session": session,
        "proposed_order_type": r.m._order_type(raw),
        "utc_hour": f"{when.hour:02d}",
        "weekday": str(when.weekday()),
        "symbol_x_family": symbol + "|" + family,
        "family_x_session": family + "|" + session,
        "symbol_x_side": symbol + "|" + side,
        "poi_mitigation_status": str(
            raw.get("poi_mitigation_status")
            or poi.get("poi_mitigation_status")
            or "not_applicable"
        ),
        "limit_marketable_at_decision": str(
            bool(fillability.get("limit_marketable_at_decision"))
        ),
        "trend_state_m15": str(source_features.get("trend_state_m15") or "MISSING"),
        "trend_transition_flag": str(source_features.get("trend_transition_flag")),
        "cost_r": number(raw.get("cost_r")),
        "spread_r": number(raw.get("spread_r")),
        "expected_slippage_r": number(raw.get("expected_slippage_r")),
        "swap_cost_r": number(raw.get("swap_cost_r")),
        "commission_r": number(raw.get("commission_r")),
        "distance_to_limit_atr": number(fillability.get("distance_to_limit_atr")),
        "distance_to_limit_risk": number(fillability.get("distance_to_limit_risk")),
        "risk_over_atr": risk / atr
        if math.isfinite(risk) and math.isfinite(atr) and atr > 0
        else np.nan,
        "risk_fraction_of_entry": risk / entry
        if math.isfinite(risk) and math.isfinite(entry) and entry > 0
        else np.nan,
        "poi_age_hours": number(raw.get("poi_age_hours", poi.get("poi_age_hours"))),
        "poi_distance_to_midpoint_atr": number(raw.get("poi_distance_to_midpoint_atr")),
        "poi_distance_to_zone_atr": number(raw.get("poi_distance_to_zone_atr")),
        "poi_touch_count": number(raw.get("poi_touch_count", poi.get("poi_touch_count"))),
        "poi_max_mitigation_fraction": number(poi.get("poi_max_mitigation_fraction")),
        "poi_touch_episode_count": number(poi.get("poi_touch_episode_count")),
        "poi_overlap_bar_count": number(poi.get("poi_overlap_bar_count")),
        **{
            key: number(source_features.get(key))
            for key in bog.PREDECISION_FEATURE_KEYS
            if key not in {"trend_state_m15", "trend_transition_flag"}
        },
    }
    return row


def load_day(day, manifest_root, sources):
    summary = json.loads((ROOT / day / "run_summary.json").read_text(encoding="utf-8"))
    sink = ReplayCompactEventSink.open_sealed(
        root=ROOT / day / "compact_events",
        expected_authority_root_sha256=summary["authority_root_sha256"],
    )
    raw_rows = list(sink.ledger("missed"))
    rows = [
        feature_row(
            raw,
            r.m._lifecycle_row(raw, manifest_root=manifest_root, sources=sources),
        )
        for raw in raw_rows
    ]
    return raw_rows, rows, summary


def select(rows, predictions, *, policy):
    by_window = defaultdict(list)
    for row, prediction in zip(rows, predictions):
        by_window[row["decision_window_id"]].append((float(prediction), row))
    ordered = sorted(
        by_window.values(),
        key=lambda values: (
            min(at(row["label_span_start_utc"]) for _, row in values),
            values[0][1]["decision_window_id"],
        ),
    )
    active, selected, dispositions = {}, [], Counter()
    for candidates in ordered:
        decision_at = min(at(row["label_span_start_utc"]) for _, row in candidates)
        active = {symbol: end for symbol, end in active.items() if end > decision_at}
        available = [
            (prediction, -float(row["cost_r"]), row["candidate_occurrence_key"], row)
            for prediction, row in candidates
            if row["symbol"] not in active
            and (policy != "market_rerank" or row["proposed_order_type"] == "MARKET")
        ]
        if not available:
            dispositions["no_available_candidate"] += 1
            continue
        prediction, _neg_cost, _key, row = max(available, key=lambda item: item[:3])
        if prediction < r.m.MIN_EXPECTED_NET_R:
            dispositions["top_below_0p10"] += 1
            continue
        if policy == "market_top_abstain" and row["proposed_order_type"] != "MARKET":
            dispositions["top_limit_abstain"] += 1
            continue
        dispositions["trade"] += 1
        chosen = dict(row, predicted_net_r=prediction)
        selected.append(chosen)
        active[row["symbol"]] = at(row["label_span_end_utc"] or row["expiry_utc"])
    return selected, dict(sorted(dispositions.items()))


def summary(selected):
    resolved = [row for row in selected if r.m.fit._state(row) is not None]
    censored = [row for row in selected if r.m.fit._state(row) is None]
    actual = sum(float(row.get("terminal_net_r") or 0.0) for row in resolved)
    worst = actual + sum(-1.0 - float(row["deductible_cost_r"]) for row in censored)
    return {
        **r.selection_summary(selected),
        "worst_case_net_r": round(worst, 6),
        "sides": dict(sorted(Counter(row["side"] for row in selected).items())),
        "sessions": dict(sorted(Counter(row["utc_session"] for row in selected).items())),
    }


def compact_selected(row):
    result = r.compact_candidate(row)
    result["lifecycle_label_status"] = row["lifecycle_label_status"]
    result["cost_label_status"] = row["cost_label_status"]
    result["deductible_cost_r"] = float(row["deductible_cost_r"])
    return result


def main() -> None:
    rule = json.loads(RULE_PATH.read_text(encoding="utf-8"))
    rule_core = dict(rule)
    claimed = rule_core.pop("payload_sha256")
    if canonical_hash(rule_core) != claimed:
        raise ValueError("frozen rule payload mismatch")
    days = list(rule["validation"]["days_in_order"])
    missing = [day for day in days if not (ROOT / day / "run_summary.json").is_file()]
    if missing:
        raise ValueError(f"February candidate roots missing: {missing}")

    initial, january = r.load_all()
    training = r.resolved_eligible(initial)
    for day, _authority in r.j.JAN_RUNS:
        training.extend(r.resolved_eligible(january[day]))
    manifest_root, sources = load_m1_sources()

    day_results, selected_by_policy, population = {}, defaultdict(list), Counter()
    unique_ids, repeated_by_family = Counter(), Counter()
    for day in days:
        raw_rows, rows, run_summary = load_day(day, manifest_root, sources)
        model = r.make_model()
        train_y = np.asarray(
            [float(row.get("terminal_net_r") or 0.0) for row in training], dtype=float
        )
        model.fit(r.frame(training), train_y, ridge__sample_weight=r.weights(training))
        test = r.eligible(rows)
        predictions = model.predict(r.frame(test))
        policies = {}
        for policy in ("market_top_abstain", "mixed", "market_rerank"):
            chosen, dispositions = select(test, predictions, policy=policy)
            policies[policy] = {
                "dispositions": dispositions,
                "portfolio": summary(chosen),
            }
            selected_by_policy[policy].extend(chosen)
        day_results[day] = {
            "authority_root_sha256": run_summary["authority_root_sha256"],
            "occurrences": len(rows),
            "eligible_occurrences": len(test),
            "policies": policies,
        }
        population["occurrences"] += len(rows)
        population["eligible_occurrences"] += len(test)
        population["resolved_eligible_occurrences"] += sum(
            r.m.fit._state(row) is not None for row in test
        )
        population["positive_resolved_occurrences"] += sum(
            r.m.fit._state(row) is not None
            and float(row.get("terminal_net_r") or 0.0) > 0
            for row in test
        )
        for raw in raw_rows:
            candidate_id = str(raw.get("candidate_id") or "")
            unique_ids[candidate_id] += 1
            if candidate_id:
                repeated_by_family[str(raw.get("origin_family"))] += 1
        training.extend(r.resolved_eligible(rows))
        print(
            json.dumps(
                {
                    "scored": day,
                    "main": policies["market_top_abstain"]["portfolio"],
                },
                sort_keys=True,
            ),
            flush=True,
        )

    pooled = {policy: summary(rows) for policy, rows in selected_by_policy.items()}
    main_days = [
        day_results[day]["policies"]["market_top_abstain"]["portfolio"]
        for day in days
    ]
    active = [row for row in main_days if row["selected"] > 0]
    pooled_main = pooled["market_top_abstain"]
    pooled_main.update(
        positive_active_days=sum(row["worst_case_net_r"] > 0 for row in active),
        negative_active_days=sum(row["worst_case_net_r"] < 0 for row in active),
        flat_active_days=sum(row["worst_case_net_r"] == 0 for row in active),
        no_trade_days=sum(row["selected"] == 0 for row in main_days),
        worst_day_r=min(row["worst_case_net_r"] for row in main_days),
        best_day_r=max(row["worst_case_net_r"] for row in main_days),
    )
    gates = {
        "minimum_resolved_selected_trades": pooled_main["resolved"] >= 20,
        "pooled_worst_case_complete_modelled_net_r_strictly_positive": pooled_main[
            "worst_case_net_r"
        ]
        > 0,
        "positive_active_days_exceed_negative_active_days": pooled_main[
            "positive_active_days"
        ]
        > pooled_main["negative_active_days"],
    }
    report = {
        "schema": "gtos.wave21.market_top_choice_validation_result.v1",
        "status": "COMPLETE_FROZEN_RULE_VALIDATION",
        "rule_path": str(RULE_PATH),
        "rule_payload_sha256": claimed,
        "candidate_root": str(ROOT),
        "candidate_root_days": days,
        "source_manifest_root_sha256": manifest_root,
        "population": {
            **dict(population),
            "unique_candidate_ids": len(unique_ids),
            "repeated_decision_occurrences": sum(
                count - 1 for candidate_id, count in unique_ids.items() if candidate_id and count > 1
            ),
            "max_occurrences_per_candidate_id": max(unique_ids.values()),
        },
        "days": day_results,
        "pooled": pooled,
        "selected_candidates": [
            compact_selected(row) for row in selected_by_policy["market_top_abstain"]
        ],
        "gates": gates,
        "decision": "PASS" if all(gates.values()) else "REJECT",
    }
    report["payload_sha256"] = canonical_hash(report)
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        "W21_FEB_RESULT="
        + json.dumps(
            {
                "path": str(OUTPUT),
                "payload_sha256": report["payload_sha256"],
                "decision": report["decision"],
                "main": pooled_main,
                "gates": gates,
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
