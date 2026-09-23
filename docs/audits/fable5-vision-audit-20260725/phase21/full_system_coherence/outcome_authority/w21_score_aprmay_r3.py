#!/usr/bin/env python3
"""April+May 2026 read of the frozen MARKET-top-choice rule (prereg APRMAY_V1).

Thin driver: every analytical function (feature_row, load_day, select, summary,
compact_selected, the ridge module) is imported byte-identically from the COMMITTED
February r2 scorer. This file adds only: per-window M1 source loading, the February
training extension (prequential continuation), the two-window day loop, and the
prereg's gates + family-robustness classification. No model, feature, selection,
threshold, or gate parameter differs from MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
OA = WT / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
R2_SCORER = OA / "w21_score_feb_market_top_r2.py"
PREREG_PATH = OA / "APRIL_MAY_MARKET_TOP_CHOICE_PREREG_V1.json"
FEB_ROOT = Path("/private/tmp/w21-market-top-feb-r2")
NEW_ROOT = Path("/private/tmp/w21-market-top-aprmay-r3")
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST_DIR = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"
OUTPUT = NEW_ROOT / "APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


s2 = load_module("w21_score_feb_r2_frozen", R2_SCORER)
r = s2.r  # the frozen ridge module loaded by the r2 scorer


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


def load_m1_sources(manifest_path: Path, expected_root: str):
    """Parameterized copy of the r2 loader (r2 hardcodes February's manifest)."""
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
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"M1 hash mismatch: {path}")
        times, bars = [], []
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["time", "open", "high", "low", "close", "volume"]:
                raise ValueError(f"M1 schema mismatch: {path}")
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
            raise ValueError(f"M1 chronology mismatch: {path}")
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
        raise ValueError("M1 symbol denominator is not 24")
    return manifest["manifest_root_sha256"], bundle


def main() -> None:
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    prereg_core = dict(prereg)
    claimed = prereg_core.pop("payload_sha256")
    if canonical_hash(prereg_core) != claimed:
        raise ValueError("frozen prereg payload mismatch")

    windows = prereg["validation"]["windows"]
    all_days = []
    for window in windows:
        all_days.extend((window["window_id"], day) for day in window["days"])
    missing = [d for _w, d in all_days if not (NEW_ROOT / d / "run_summary.json").is_file()]
    if missing:
        raise ValueError(f"candidate roots missing: {missing}")

    # Training bootstrap: Oct/Nov development + January + February (prequential continuation).
    initial, january = r.load_all()
    training = r.resolved_eligible(initial)
    for day, _authority in r.j.JAN_RUNS:
        training.extend(r.resolved_eligible(january[day]))
    feb_manifest_root, feb_sources = load_m1_sources(
        MANIFEST_DIR / "february_2026.json",
        prereg["bindings"]["february_manifest_root_sha256"],
    )
    feb_days = prereg["training"]["february_days"]
    old_root = s2.ROOT
    s2.ROOT = FEB_ROOT
    try:
        for day in feb_days:
            _raw, rows, _summary = s2.load_day(day, feb_manifest_root, feb_sources)
            training.extend(r.resolved_eligible(rows))
    finally:
        s2.ROOT = old_root
    print(json.dumps({"training_rows": len(training)}), flush=True)

    window_sources = {}
    for window in windows:
        window_sources[window["window_id"]] = load_m1_sources(
            MANIFEST_DIR / f"{window['window_id']}.json",
            window["manifest_root_sha256"],
        )

    from collections import Counter, defaultdict

    day_results, selected_by_policy, population = {}, defaultdict(list), Counter()
    s2.ROOT = NEW_ROOT
    try:
        for window_id, day in all_days:
            manifest_root, sources = window_sources[window_id]
            raw_rows, rows, run_summary = s2.load_day(day, manifest_root, sources)
            test = r.eligible(rows)
            # Stand-down days (full market holidays) carry zero eligible rows; an
            # empty frame has no columns and predict would crash. No candidates
            # means no selection — skip the fit/predict, keep the day recorded.
            if test:
                model = r.make_model()
                train_y = np.asarray(
                    [float(row.get("terminal_net_r") or 0.0) for row in training],
                    dtype=float,
                )
                model.fit(
                    r.frame(training), train_y, ridge__sample_weight=r.weights(training)
                )
                predictions = model.predict(r.frame(test))
            else:
                predictions = []
            policies = {}
            for policy in ("market_top_abstain", "mixed", "market_rerank"):
                chosen, dispositions = s2.select(test, predictions, policy=policy)
                policies[policy] = {
                    "dispositions": dispositions,
                    "portfolio": s2.summary(chosen),
                }
                selected_by_policy[policy].extend(chosen)
            day_results[day] = {
                "window_id": window_id,
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
            training.extend(r.resolved_eligible(rows))
            print(
                json.dumps(
                    {"scored": day, "main": policies["market_top_abstain"]["portfolio"]},
                    sort_keys=True,
                ),
                flush=True,
            )
    finally:
        s2.ROOT = old_root

    pooled = {policy: s2.summary(rows) for policy, rows in selected_by_policy.items()}
    main_days = [
        day_results[day]["policies"]["market_top_abstain"]["portfolio"]
        for _w, day in all_days
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
    per_month = {}
    for window in windows:
        wdays = set(window["days"])
        rows_w = [
            row
            for row in selected_by_policy["market_top_abstain"]
            if row["trading_day"] in wdays
        ]
        per_month[window["window_id"]] = s2.summary(rows_w)

    net_by_family = pooled_main.get("net_by_family") or {}
    top_family = max(net_by_family, key=net_by_family.get) if net_by_family else None
    ex_top = (
        round(pooled_main["worst_case_net_r"] - net_by_family[top_family], 6)
        if top_family
        else None
    )
    family_robustness = {
        "top_contributing_family": top_family,
        "pooled_worst_case_net_r": pooled_main["worst_case_net_r"],
        "pooled_worst_case_net_r_excluding_top_family": ex_top,
        "classification": (
            "FAMILY_ROBUST"
            if ex_top is not None and ex_top > 0
            else f"FAMILY_SPECIFIC_EDGE:{top_family}"
        ),
    }
    gates = {
        "minimum_resolved_selected_trades": pooled_main["resolved"] >= 40,
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
        "schema": "gtos.wave21.april_may_market_top_choice_validation_result.v1",
        "status": "COMPLETE_FROZEN_PREREG_VALIDATION",
        "prereg_path": str(PREREG_PATH),
        "prereg_payload_sha256": claimed,
        "candidate_root": str(NEW_ROOT),
        "days": day_results,
        "population": dict(population),
        "pooled": pooled,
        "per_month": per_month,
        "family_robustness": family_robustness,
        "selected_candidates": [
            s2.compact_selected(row) for row in selected_by_policy["market_top_abstain"]
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
        "W21_APRMAY_RESULT="
        + json.dumps(
            {
                "path": str(OUTPUT),
                "payload_sha256": report["payload_sha256"],
                "decision": report["decision"],
                "family_robustness": family_robustness,
                "main": {
                    k: pooled_main.get(k)
                    for k in (
                        "selected",
                        "resolved",
                        "actual_net_r",
                        "worst_case_net_r",
                        "positive_active_days",
                        "negative_active_days",
                    )
                },
                "gates": gates,
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
