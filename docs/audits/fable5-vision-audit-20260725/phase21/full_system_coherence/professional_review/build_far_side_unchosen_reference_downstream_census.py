#!/usr/bin/env python3
"""Census predecision closes far side of the unchosen 1.5R reference."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
LEDGERS = (
    (
        Path("/private/tmp/wave21-minimal-repair-20251028-875037f1b-r4/harness_wave21_minimal_repair_20251028_875037f1b_r4_stage_ledger.jsonl.gz"),
        "89762595a78e7d81003a2595c08e39d9dffb6d0c4bed2c2d0e7970bcbb4a7991",
    ),
    (
        Path("/private/tmp/wave21-minimal-repair-20251103-875037f1b-r1/harness_wave21_minimal_repair_20251103_875037f1b_r1_stage_ledger.jsonl.gz"),
        "db84b4d7137b6da9d60741abca4ff069152a73dc89fc0e4243f82329e82711d8",
    ),
    (
        Path("/private/tmp/wave21-minimal-repair-20251107-875037f1b-r1/harness_wave21_minimal_repair_20251107_875037f1b_r1_stage_ledger.jsonl.gz"),
        "e135d297cee9631eec76d322a9864a3011941987151940d9b4d69dc4a9a9e835",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_predecision_module() -> Any:
    path = ROOT / "build_predecision_packet.py"
    spec = importlib.util.spec_from_file_location("wave21_predecision_packet", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("predecision_module_load_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    pre = load_predecision_module()
    population, receipts, _bindings = pre.load_candidate_population()
    loader = pre.CausalSourceLoader(receipts)
    far_side_reference: set[str] = set()
    candidate_action: Counter[str] = Counter()
    candidate_intent: Counter[str] = Counter()
    family: Counter[str] = Counter()
    day: Counter[str] = Counter()
    for row in population:
        if not str(row["origin_family"]).startswith("current_"):
            continue
        observables = row["_row"].get("observables") or {}
        config = receipts[str(row["day"])]["inputs"]["effective_config_payload"]
        unchosen_reference_rr = float((config.get("risk") or {})["min_rr"])
        entry = float(observables["entry_price"])
        stop = float(observables["stop_loss"])
        risk = abs(entry - stop)
        unchosen_reference_price = (
            entry + unchosen_reference_rr * risk
            if row["side"] == "LONG"
            else entry - unchosen_reference_rr * risk
        )
        asof = pre.parse_utc(str(row["decision_time_utc"]))
        source = loader.source(str(row["day"]), str(row["symbol"]), "M15")
        closed = pre.timewarp.closed_bar_rows_until(
            source.rows, timeframe="M15", asof=asof, max_rows=1
        )
        current = float(closed[-1]["close"])
        far_side = (
            current >= unchosen_reference_price
            if row["side"] == "LONG"
            else current <= unchosen_reference_price
        )
        if not far_side:
            continue
        key = str(row["occurrence_key"])
        far_side_reference.add(key)
        candidate_action[str(observables.get("raw_selector_action"))] += 1
        candidate_intent[str(observables.get("scheduler_materialization_action_intent"))] += 1
        family[str(row["origin_family"])] += 1
        day[str(row["day"])] += 1

    ordered: set[str] = set()
    final_action: Counter[str] = Counter()
    final_order_status: Counter[str] = Counter()
    miss_reason: Counter[str] = Counter()
    terminal_outcome: Counter[str] = Counter()
    ledger_bindings: list[dict[str, str]] = []
    terminal_row_count = 0
    for path, expected_sha in LEDGERS:
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            raise ValueError(f"retained_ledger_sha_mismatch:{path}:{expected_sha}:{actual_sha}")
        ledger_bindings.append({"path": str(path), "sha256": actual_sha})
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                identity = row.get("identity") or {}
                key = identity.get("canonical_replay_candidate_instance_key")
                if key not in far_side_reference:
                    continue
                if row.get("stage") == "oracle":
                    ordered.add(str(key))
                if row.get("stage") == "missed":
                    terminal_row_count += 1
                    observables = row.get("observables") or {}
                    final_action[str(observables.get("selector_action"))] += 1
                    final_order_status[str(observables.get("order_status"))] += 1
                    miss_reason[str(observables.get("miss_reason"))] += 1
                    terminal_outcome[str(observables.get("terminal_outcome"))] += 1
    if terminal_row_count + len(ordered) != len(far_side_reference):
        raise ValueError(
            f"far_side_unchosen_reference_terminal_conservation_failed:{len(far_side_reference)}:"
            f"{terminal_row_count}:{len(ordered)}"
        )
    risk_bearing = {"trade", "reduce-risk", "open-reduced-risk"}
    body = {
        "schema": "gtos.wave21.professional_review.far_side_unchosen_reference_downstream_census.v2",
        "freeze_receipt_root_sha256": "58605fef5f13dd5bf8d11c9af99db7761ee651fc78ba1cfb21fe0d1564437226",
        "policy_arm": "retained_875037f1b_0p20R_all_three_days",
        "ledger_bindings": ledger_bindings,
        "definition": "predecision_close_far_side_of_unchosen_1p5R_reference",
        "semantic_boundary": (
            "the 1.5R reference is inherited risk.min_rr and explicitly UNCHOSEN, not a "
            "source-owned thesis target; a resting LIMIT can remain physically fillable after "
            "the predecision close moves to the far side"
        ),
        "current_origin_candidate_occurrence_count": sum(
            str(row["origin_family"]).startswith("current_") for row in population
        ),
        "predecision_close_far_side_of_unchosen_1p5R_reference_count": len(far_side_reference),
        "by_family": dict(sorted(family.items())),
        "by_day": dict(sorted(day.items())),
        "candidate_raw_selector_action_counts": dict(sorted(candidate_action.items())),
        "candidate_raw_selector_risk_bearing_count": sum(
            count for action, count in candidate_action.items() if action in risk_bearing
        ),
        "candidate_scheduler_materialization_intent_counts": dict(
            sorted(candidate_intent.items())
        ),
        "candidate_risk_intent_new_or_replace_count": sum(
            candidate_intent[action] for action in ("new_position", "replace_pending")
        ),
        "terminal_missed_row_count": terminal_row_count,
        "terminal_effective_selector_action_counts": dict(sorted(final_action.items())),
        "terminal_order_status_counts": dict(sorted(final_order_status.items())),
        "ordered_occurrence_count": len(ordered),
        "miss_reason_counts": dict(sorted(miss_reason.items())),
        "counterfactual_terminal_outcome_counts": dict(sorted(terminal_outcome.items())),
        "interpretation": (
            "measured exposure only: zero orders followed for heterogeneous unrelated miss reasons; "
            "there is no far-side-specific refusal, expiry, re-arm, or downstream cancellation guard"
        ),
        "objective_candidate_invalidity_proved": False,
        "causal_downstream_containment_proved": False,
        "uses_outcome_fields_for_far_side_reference_definition": False,
        "uses_downstream_fields_for_terminal_census": True,
    }
    result = {**body, "census_root_sha256": stable_sha256(body)}
    path = ROOT / "FAR_SIDE_UNCHOSEN_REFERENCE_DOWNSTREAM_CENSUS.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
