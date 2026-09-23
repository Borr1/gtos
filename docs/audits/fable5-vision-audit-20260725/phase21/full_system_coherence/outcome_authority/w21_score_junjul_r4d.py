#!/usr/bin/env python3
"""June+July 2026 read of the frozen MARKET-top-choice rule under BAR-3
(prereg JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1; owner ratification 2026-08-11,
recorded verbatim in BAR3_RATIFICATION_20260811.md: "yes proceed as proposed
and recommended with bar-3").

Thin driver over committed frozen machinery — nothing analytical is new here:

  * model / features / eligibility / general selection / summary: the committed
    February r2 scorer, loaded byte-identically through the committed AprMay r3b
    scorer (which is how the sealed April+May result loaded it);
  * scoped-family replay (the primary deployable object, Option B) and its
    portfolio shape: ``pm_analysis.replay_selection`` / ``pm_analysis.portfolio``
    imported verbatim from the committed postmortem — the exact code that priced
    Option B's SD4 record (+7.93 / +0.45 / +1.10);
  * pass-bar arithmetic: ``pm_bars`` functions imported verbatim (bootstrap seed
    20260811 / n 20000 are that module's frozen constants). BAR-3 gates replicate
    ``pm_bars.main``'s ``bar3`` dict exactly; BAR-1 and BAR-2 are computed and
    REPORTED, not used.

Training is the prequential continuation: Oct/Nov development + January +
February + April + May (all previously read), then day-by-day through June/July.

The one schema adapter (documented in the prereg): r2 rows carry the limit
expiry under ``expiry_utc`` (built from raw ``limit_first_expiry_utc`` at the r2
scorer's row constructor), while ``pm_analysis.replay_selection`` reads
``limit_first_expiry_utc``; rows handed to the scoped replay are aliased
``dict(row, limit_first_expiry_utc=row["expiry_utc"])``. Every other key is
shared, and the resolved/censored classification of the two stacks was proved
identical by the postmortem's §0 reproduction.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
OA = WT / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
R3_SCORER = OA / "w21_score_aprmay_r3b.py"
PM_ANALYSIS = OA / "postmortem/pm_analysis.py"
PM_BARS = OA / "postmortem/pm_bars.py"
RULE_PATH = OA / "MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json"
PREREG_PATH = OA / "JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1_3.json"
FEB_ROOT = Path("/private/tmp/w21-market-top-feb-r2")
APRMAY_ROOT = Path("/private/tmp/w21-market-top-aprmay-r3")
NEW_ROOT = Path("/private/tmp/w21-market-top-junjul-r4")
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST_DIR = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"
OUTPUT = NEW_ROOT / "JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json"
LSR = "liquidity_sweep_reclaim"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


r3 = load_module("w21_score_aprmay_r3b_frozen", R3_SCORER)
s2 = r3.s2
r = r3.r
pm = load_module("pm_analysis_frozen", PM_ANALYSIS)
pmb = load_module("pm_bars_frozen", PM_BARS)


def canonical_hash(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_bindings(prereg: dict) -> None:
    """Every imported analytical file must match the sha the prereg froze."""
    bound = prereg["bindings"]
    checks = {
        "aprmay_r3b_scorer_sha256": R3_SCORER,
        "feb_r2_scorer_sha256": r3.R2_SCORER,
        "pm_analysis_sha256": PM_ANALYSIS,
        "pm_bars_sha256": PM_BARS,
        "generator_sha256": OA / "w21_generate_day_r2b.py",
    }
    for key, path in checks.items():
        actual = sha256_file(path)
        if actual != bound[key]:
            raise ValueError(f"binding drift: {key}: {actual} != {bound[key]}")
    rule = json.loads(RULE_PATH.read_text(encoding="utf-8"))
    rule_core = dict(rule)
    claimed = rule_core.pop("payload_sha256")
    if canonical_hash(rule_core) != claimed or claimed != bound["rule_v1_1_payload_sha256"]:
        raise ValueError("frozen rule payload mismatch")


def main() -> None:
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    prereg_core = dict(prereg)
    claimed = prereg_core.pop("payload_sha256")
    if canonical_hash(prereg_core) != claimed:
        raise ValueError("frozen prereg payload mismatch")
    verify_bindings(prereg)

    windows = prereg["validation"]["windows"]
    all_days = []
    for window in windows:
        all_days.extend((window["window_id"], day) for day in window["days"])
    missing = [d for _w, d in all_days if not (NEW_ROOT / d / "run_summary.json").is_file()]
    if missing:
        raise ValueError(f"candidate roots missing: {missing}")

    # Training bootstrap: Oct/Nov development + January + February + April + May
    # (prequential continuation — every prior read, in read order).
    initial, january = r.load_all()
    training = r.resolved_eligible(initial)
    for day, _authority in r.j.JAN_RUNS:
        training.extend(r.resolved_eligible(january[day]))

    tr = prereg["training"]
    feb_root_sha, feb_sources = r3.load_m1_sources(
        MANIFEST_DIR / "february_2026.json", tr["february_manifest_root_sha256"]
    )
    old_root = s2.ROOT
    s2.ROOT = FEB_ROOT
    try:
        for day in tr["february_days"]:
            _raw, rows, _summary = s2.load_day(day, feb_root_sha, feb_sources)
            training.extend(r.resolved_eligible(rows))
    finally:
        s2.ROOT = old_root
    del feb_sources

    for month_key, days_key in (("april", "april_days"), ("may", "may_days")):
        root_sha, sources = r3.load_m1_sources(
            MANIFEST_DIR / f"{month_key}_2026.json",
            tr[f"{month_key}_manifest_root_sha256"],
        )
        s2.ROOT = APRMAY_ROOT
        try:
            for day in tr[days_key]:
                _raw, rows, _summary = s2.load_day(day, root_sha, sources)
                training.extend(r.resolved_eligible(rows))
        finally:
            s2.ROOT = old_root
        del sources
    print(json.dumps({"training_rows": len(training)}), flush=True)

    window_sources = {}
    for window in windows:
        window_sources[window["window_id"]] = r3.load_m1_sources(
            MANIFEST_DIR / f"{window['window_id']}.json", window["manifest_root_sha256"]
        )

    from collections import Counter, defaultdict

    keep_lsr = lambda row: row["origin_family"] == LSR  # noqa: E731 — SD4's keep
    day_results = {}
    selected_by_policy = defaultdict(list)
    scoped_selected = []
    scoped_dispositions = Counter()
    population = Counter()
    s2.ROOT = NEW_ROOT
    try:
        for window_id, day in all_days:
            manifest_root, sources = window_sources[window_id]
            raw_rows, rows, run_summary = s2.load_day(day, manifest_root, sources)
            test = r.eligible(rows)
            # Stand-down days carry zero eligible rows; an empty frame has no
            # columns and predict would crash. No candidates means no selection.
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
            predictions_by_key = {
                row["candidate_occurrence_key"]: float(pred)
                for row, pred in zip(test, predictions)
            }
            aliased = [
                dict(row, limit_first_expiry_utc=row["expiry_utc"]) for row in test
            ]
            day_scoped, day_scoped_disp = pm.replay_selection(
                aliased, predictions_by_key, keep=keep_lsr
            )
            scoped_selected.extend(day_scoped)
            scoped_dispositions.update(day_scoped_disp)
            day_results[day] = {
                "window_id": window_id,
                "authority_root_sha256": run_summary["authority_root_sha256"],
                "occurrences": len(rows),
                "eligible_occurrences": len(test),
                "policies": policies,
                "scoped_lsr": {
                    "dispositions": day_scoped_disp,
                    "portfolio": pm.portfolio(day_scoped),
                },
            }
            population["occurrences"] += len(rows)
            population["eligible_occurrences"] += len(test)
            population["resolved_eligible_occurrences"] += sum(
                r.m.fit._state(row) is not None for row in test
            )
            training.extend(r.resolved_eligible(rows))
            print(
                json.dumps(
                    {
                        "scored": day,
                        "main": policies["market_top_abstain"]["portfolio"],
                        "scoped_lsr_selected": len(day_scoped),
                    },
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
    scoped_per_month = {}
    for window in windows:
        wdays = set(window["days"])
        rows_w = [
            row
            for row in selected_by_policy["market_top_abstain"]
            if row["trading_day"] in wdays
        ]
        per_month[window["window_id"]] = s2.summary(rows_w)
        scoped_w = [row for row in scoped_selected if row["trading_day"] in wdays]
        scoped_per_month[window["window_id"]] = pm.portfolio(scoped_w)

    # --- pass-bar arithmetic, verbatim shapes from pm_bars ---------------------
    ws = pmb.window_stats({"days": day_results, "pooled": pooled})

    bar1_gates = {
        "resolved_ge_40": ws["pooled_resolved"] >= 40,
        "pooled_worst_case_gt_0": ws["pooled_worst_case_net_r"] > 0,
        "positive_gt_negative_active_days": (
            (ws["positive_active_days"] or 0) > (ws["negative_active_days"] or 0)
        ),
    }
    bar2_gates = {
        "bootstrap_p05_pooled_sum_gt_0": ws["bootstrap_day_resample"]["pooled_sum_p05"] > 0,
        "discipline_beats_mixed_worst_case": ws["discipline_minus_mixed_worst_case_r"] > 0,
        "max_drawdown_le_8r": ws["max_drawdown_r_daily_worst_case"] <= 8.0,
        "resolved_ge_40": ws["pooled_resolved"] >= 40,
    }

    historical_lsr, historical_all_positive, _population = pmb.lsr_scope_stability()
    month_lsr = {
        window["window_id"]: float(
            (per_month[window["window_id"]].get("net_by_family") or {}).get(LSR, 0.0)
        )
        for window in windows
    }
    window_lsr_net = float((pooled_main.get("net_by_family") or {}).get(LSR, 0.0))
    bar3_gates = {
        "discipline_beats_mixed_worst_case": ws["discipline_minus_mixed_worst_case_r"] > 0,
        "pooled_worst_case_gt_minus_2r": ws["pooled_worst_case_net_r"] > -2.0,
        "scoped_family_lsr_positive_in_window": window_lsr_net > 0,
        "scoped_family_rule_selected_lsr_positive_every_scored_month": (
            historical_all_positive
            and all(value > 0 for value in month_lsr.values())
        ),
    }
    decision = "PASS" if all(bar3_gates.values()) else "REJECT"

    net_by_family = pooled_main.get("net_by_family") or {}
    top_family = max(net_by_family, key=net_by_family.get) if net_by_family else None
    ex_top = (
        round(pooled_main["worst_case_net_r"] - net_by_family[top_family], 6)
        if top_family
        else None
    )
    report = {
        "schema": "gtos.wave21.june_july_market_top_choice_validation_result.v1",
        "status": "COMPLETE_FROZEN_PREREG_VALIDATION",
        "prereg_path": str(PREREG_PATH),
        "prereg_payload_sha256": claimed,
        "candidate_root": str(NEW_ROOT),
        "days": day_results,
        "population": dict(population),
        "pooled": pooled,
        "per_month": per_month,
        "primary_deployable_object_forward_record": {
            "object": f"scoped rule ∘ {LSR} (Option B, SD4 replay semantics)",
            "pooled": pm.portfolio(scoped_selected),
            "per_month": scoped_per_month,
            "dispositions": dict(sorted(scoped_dispositions.items())),
            "selected": [s2.compact_selected(row) for row in scoped_selected],
        },
        "family_robustness": {
            "top_contributing_family": top_family,
            "pooled_worst_case_net_r": pooled_main["worst_case_net_r"],
            "pooled_worst_case_net_r_excluding_top_family": ex_top,
            "classification": (
                "FAMILY_ROBUST"
                if ex_top is not None and ex_top > 0
                else f"FAMILY_SPECIFIC_EDGE:{top_family}"
            ),
        },
        "selected_candidates": [
            s2.compact_selected(row) for row in selected_by_policy["market_top_abstain"]
        ],
        "window_stats": ws,
        "gate_inputs": {
            "historical_lsr_rule_selected_net_by_month": historical_lsr,
            "historical_all_positive": historical_all_positive,
            "window_month_lsr_rule_selected_net": month_lsr,
            "window_pooled_lsr_rule_selected_net": window_lsr_net,
        },
        "reported_not_used": {
            "BAR_1_strict_positivity": {
                "gates": bar1_gates,
                "verdict": "PASS" if all(bar1_gates.values()) else "REJECT",
            },
            "BAR_2_bootstrap_ci_skill_drawdown": {
                "gates": bar2_gates,
                "verdict": "PASS" if all(bar2_gates.values()) else "REJECT",
                "bootstrap": ws["bootstrap_day_resample"],
            },
        },
        "gates": bar3_gates,
        "decision_standard": "BAR_3_relative_skill_scoped_family",
        "decision": decision,
    }
    report["payload_sha256"] = canonical_hash(report)
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        "W21_JUNJUL_RESULT="
        + json.dumps(
            {
                "path": str(OUTPUT),
                "payload_sha256": report["payload_sha256"],
                "decision": report["decision"],
                "gates": bar3_gates,
                "scoped_pooled": report["primary_deployable_object_forward_record"]["pooled"],
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
                "reported_not_used": {
                    "BAR_1": report["reported_not_used"]["BAR_1_strict_positivity"]["verdict"],
                    "BAR_2": report["reported_not_used"]["BAR_2_bootstrap_ci_skill_drawdown"]["verdict"],
                },
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
