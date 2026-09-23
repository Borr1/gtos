#!/usr/bin/env python3
"""Outcome-aware downstream census; never used to validate setup quality."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
RUNS = (
    {
        "day": "2025-10-28",
        "arm": "selector_0p45R_treatment_rejected",
        "policy_status": "rejected_treatment_not_retained_policy",
        "ledger": Path("/private/tmp/wave21-minimal-repair-20251028-8762e0480-r1/harness_wave21_minimal_repair_20251028_8762e0480_r1_stage_ledger.jsonl.gz"),
        "ledger_sha256": "42447828cfa2c9ad87e67c9d47b467462193506625f3b75fae820f6d83bb6d0f",
        "receipt": Path("/private/tmp/wave21-minimal-repair-20251028-8762e0480-r1/harness_wave21_minimal_repair_20251028_8762e0480_r1_run_receipt.json"),
        "receipt_sha256": "a8fdf898db33cf5f7152a67e84ef1c44f3a75c2d2d8cb6365b0c64cb053c5dbc",
    },
    {
        "day": "2025-11-03",
        "arm": "selector_0p20R_retained_plus_f3ae_xau_scheduler_repair",
        "policy_status": "retained_policy_downstream_repair_diagnostic",
        "ledger": Path("/private/tmp/wave21-minimal-repair-20251103-f3ae1a210-r1/harness_wave21_minimal_repair_20251103_f3ae1a210_r1_stage_ledger.jsonl.gz"),
        "ledger_sha256": "13db8265ae9568ac1b1bfa402a81d772e3e0ec44ef1338d56426bd81555c0189",
        "receipt": Path("/private/tmp/wave21-minimal-repair-20251103-f3ae1a210-r1/harness_wave21_minimal_repair_20251103_f3ae1a210_r1_run_receipt.json"),
        "receipt_sha256": "bab8a715e3a783da4a6da287b1ca6282e27c0da874fae6b4fe02d79ba3612ef0",
    },
    {
        "day": "2025-11-07",
        "arm": "selector_0p45R_treatment_rejected",
        "policy_status": "rejected_treatment_not_retained_policy",
        "ledger": Path("/private/tmp/wave21-minimal-repair-20251107-8762e0480-r1/harness_wave21_minimal_repair_20251107_8762e0480_r1_stage_ledger.jsonl.gz"),
        "ledger_sha256": "6fc486eea31955fa9324e388016b13df85f7c2652b956388aabfd30fdfce88c7",
        "receipt": Path("/private/tmp/wave21-minimal-repair-20251107-8762e0480-r1/harness_wave21_minimal_repair_20251107_8762e0480_r1_run_receipt.json"),
        "receipt_sha256": "cbdb196bcefbf3e2c999b5bf5a4d18bd030ca36e3a97258d7c3440562535e499",
    },
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


def occurrence_key(row: Mapping[str, Any]) -> str | None:
    identity = row.get("identity") or {}
    key = identity.get("canonical_replay_candidate_instance_key")
    if key:
        return str(key)
    candidate_id = identity.get("candidate_id")
    decision_time = identity.get("decision_time_utc")
    if candidate_id and decision_time:
        return f"{candidate_id}@@{decision_time}"
    return None


def load_predecision_module() -> Any:
    path = ROOT / "build_predecision_packet.py"
    spec = importlib.util.spec_from_file_location("wave21_predecision_packet", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("predecision_module_load_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def far_side_unchosen_reference_projection(
    candidate: Mapping[str, Any],
    *,
    day: str,
    receipt: Mapping[str, Any],
    loader: Any,
    predecision: Any,
) -> dict[str, Any]:
    identity = candidate.get("identity") or {}
    family = str(identity.get("origin_family") or "")
    if not family.startswith("current_"):
        return {"status": "not_current_framework_candidate"}
    observables = candidate.get("observables") or {}
    entry = float(observables["entry_price"])
    stop = float(observables["stop_loss"])
    side = str(identity.get("side") or "")
    unchosen_reference_rr = float(
        (receipt["inputs"]["effective_config_payload"].get("risk") or {})["min_rr"]
    )
    risk = abs(entry - stop)
    unchosen_reference_price = (
        entry + unchosen_reference_rr * risk
        if side == "LONG"
        else entry - unchosen_reference_rr * risk
    )
    asof = datetime.fromisoformat(str(identity["decision_time_utc"]).replace("Z", "+00:00"))
    if asof.tzinfo is None:
        asof = asof.replace(tzinfo=timezone.utc)
    source = loader.source(day, str(identity["symbol"]), "M15")
    closed = predecision.timewarp.closed_bar_rows_until(
        source.rows, timeframe="M15", asof=asof, max_rows=1
    )
    current = float(closed[-1]["close"])
    far_side = (
        current >= unchosen_reference_price
        if side == "LONG"
        else current <= unchosen_reference_price
    )
    return {
        "status": (
            "predecision_close_far_side_of_unchosen_1p5R_reference"
            if far_side
            else "predecision_close_not_far_side_of_unchosen_1p5R_reference"
        ),
        "latest_closed_m15_price": current,
        "unchosen_1p5r_reference_price": unchosen_reference_price,
        "unchosen_reference_rr": unchosen_reference_rr,
        "objective_candidate_invalidity_proved": False,
        "uses_outcome_fields": False,
    }


def project_ordered(
    *,
    run: Mapping[str, Any],
    key: str,
    rows: list[Mapping[str, Any]],
    account_rows_by_order: Mapping[str, list[Mapping[str, Any]]],
    receipt: Mapping[str, Any],
    loader: Any,
    predecision: Any,
) -> dict[str, Any]:
    by_stage: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stage[str(row.get("stage"))].append(row)
    candidate = by_stage["candidate"][0]
    candidate_o = candidate.get("observables") or {}
    oracle = by_stage["oracle"][0]
    oracle_o = oracle.get("observables") or {}
    orders = sorted(by_stage["order"], key=lambda row: int(row.get("stage_row_ordinal") or 0))
    order_ids = sorted(
        {
            str((row.get("identity") or {}).get("simulated_order_id"))
            for row in orders
            if (row.get("identity") or {}).get("simulated_order_id")
        }
    )
    account_events = [
        {
            "identity": row.get("identity"),
            "observables": row.get("observables"),
        }
        for order_id in order_ids
        for row in account_rows_by_order.get(order_id, [])
    ]
    trade = by_stage.get("trade", [None])[0]
    trade_o = (trade or {}).get("observables") or {}
    exit_row = by_stage.get("exit", [None])[0]
    exit_o = (exit_row or {}).get("observables") or {}
    identity = candidate.get("identity") or {}
    result = {
        "schema": "gtos.wave21.professional_review.outcome_diagnostic_ordered.v2",
        "arm": run["arm"],
        "policy_status": run["policy_status"],
        "identity": {
            "occurrence_key": key,
            "decision_time_utc": identity.get("decision_time_utc"),
            "symbol": identity.get("symbol"),
            "origin_family": identity.get("origin_family"),
            "side": identity.get("side"),
            "session": identity.get("route_session"),
        },
        "predecision": {
            "raw_selector_action": candidate_o.get("raw_selector_action"),
            "effective_selector_action": candidate_o.get("selector_action"),
            "entry_price": candidate_o.get("entry_price"),
            "stop_loss": candidate_o.get("stop_loss"),
            "take_profit_1": candidate_o.get("take_profit_1"),
            "risk_reward_ratio": candidate_o.get("risk_reward_ratio"),
            "risk_pct": candidate_o.get("risk_pct"),
            "risk_decision": candidate_o.get("risk_decision"),
            "expected_cost_r": candidate_o.get("expected_cost_r"),
            "broker_pretrade_cost_r": candidate_o.get("broker_pretrade_cost_r"),
            "current_poi_far_side_unchosen_reference": far_side_unchosen_reference_projection(
                candidate,
                day=str(run["day"]),
                receipt=receipt,
                loader=loader,
                predecision=predecision,
            ),
        },
        "order": {
            "order_stage_row_count": len(orders),
            "simulated_order_ids": order_ids,
            "statuses": [(row.get("observables") or {}).get("order_status") for row in orders],
            "fill_statuses": [(row.get("observables") or {}).get("fill_status") for row in orders],
            "fill_times_utc": [(row.get("observables") or {}).get("fill_time_utc") for row in orders],
        },
        "oracle": {
            "terminal_outcome": oracle_o.get("terminal_outcome"),
            "fill_status": oracle_o.get("fill_status"),
            "path_source": oracle_o.get("path_source"),
        },
        "trade": {
            "present": trade is not None,
            "gross_r": trade_o.get("gross_r"),
            "net_r": trade_o.get("net_r"),
            "pnl_cash": trade_o.get("pnl_cash"),
            "close_reason": trade_o.get("close_reason"),
        },
        "exit": {
            "present": exit_row is not None,
            "gross_r": exit_o.get("gross_r"),
            "net_proxy_r": exit_o.get("net_proxy_r"),
            "total_execution_cost_r": exit_o.get("total_execution_cost_r"),
            "close_side_all_in_cost_status": exit_o.get("close_side_all_in_cost_status"),
        },
        "account": {
            "join_status": "joined_by_simulated_order_id" if account_events else "NOT_EVALUABLE_no_account_join",
            "event_count": len(account_events),
            "events": account_events,
        },
        "claim_boundary": {
            "outcome_aware_cohort": True,
            "setup_quality_validation_allowed": False,
            "broker_fill_truth": False,
            "post_lifecycle_all_in_cost_complete": False,
        },
    }
    result["row_root_sha256"] = stable_sha256(result)
    return result


def project_promising_reject(run: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    identity = row.get("identity") or {}
    observables = row.get("observables") or {}
    result = {
        "schema": "gtos.wave21.professional_review.outcome_diagnostic_promising_reject.v1",
        "arm": run["arm"],
        "policy_status": run["policy_status"],
        "identity": {
            "occurrence_key": occurrence_key(row),
            "decision_time_utc": identity.get("decision_time_utc"),
            "symbol": identity.get("symbol"),
            "origin_family": identity.get("origin_family"),
            "side": identity.get("side"),
            "session": identity.get("route_session"),
        },
        "raw_selector_action": observables.get("raw_selector_action"),
        "effective_selector_action": observables.get("selector_action"),
        "scheduler_materialization_action_intent": observables.get(
            "scheduler_materialization_action_intent"
        ),
        "miss_reason": observables.get("miss_reason"),
        "terminal_outcome": observables.get("terminal_outcome"),
        "entry_price": observables.get("entry_price"),
        "stop_loss": observables.get("stop_loss"),
        "take_profit_1": observables.get("take_profit_1"),
        "risk_reward_ratio": observables.get("risk_reward_ratio"),
        "expected_cost_r": observables.get("expected_cost_r"),
        "broker_pretrade_cost_r": observables.get("broker_pretrade_cost_r"),
        "interpretation": "counterfactual_target_path_for_unordered_candidate_not_realized_trade",
        "setup_quality_validation_allowed": False,
    }
    result["row_root_sha256"] = stable_sha256(result)
    return result


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> None:
    predecision = load_predecision_module()
    receipts: dict[str, dict[str, Any]] = {}
    bindings: list[dict[str, Any]] = []
    all_rows_by_run: dict[str, list[dict[str, Any]]] = {}
    for run in RUNS:
        for path_key, sha_key in (("ledger", "ledger_sha256"), ("receipt", "receipt_sha256")):
            actual = sha256_file(Path(run[path_key]))
            if actual != run[sha_key]:
                raise ValueError(f"diagnostic_binding_mismatch:{run[path_key]}:{run[sha_key]}:{actual}")
        receipt = json.loads(Path(run["receipt"]).read_text())
        receipts[str(run["day"])] = receipt
        bindings.append(
            {
                "day": run["day"],
                "arm": run["arm"],
                "policy_status": run["policy_status"],
                "ledger_path": str(run["ledger"]),
                "ledger_sha256": run["ledger_sha256"],
                "receipt_path": str(run["receipt"]),
                "receipt_sha256": run["receipt_sha256"],
            }
        )
        with gzip.open(Path(run["ledger"]), "rt", encoding="utf-8") as handle:
            all_rows_by_run[str(run["day"])] = [json.loads(line) for line in handle]
    loader = predecision.CausalSourceLoader(receipts)

    ordered_rows: list[dict[str, Any]] = []
    promising_rows: list[dict[str, Any]] = []
    per_arm: list[dict[str, Any]] = []
    for run in RUNS:
        rows = all_rows_by_run[str(run["day"])]
        by_occurrence: dict[str, list[dict[str, Any]]] = defaultdict(list)
        accounts_by_order: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            key = occurrence_key(row)
            if key:
                by_occurrence[key].append(row)
            if row.get("stage") == "account":
                order_id = (row.get("identity") or {}).get("simulated_order_id")
                if order_id:
                    accounts_by_order[str(order_id)].append(row)
            if (
                row.get("stage") == "missed"
                and (row.get("observables") or {}).get("terminal_outcome")
                == "target_reached_before_stop"
            ):
                promising_rows.append(project_promising_reject(run, row))
        ordered_keys = sorted(
            key
            for key, occurrence_rows in by_occurrence.items()
            if any(row.get("stage") == "oracle" for row in occurrence_rows)
        )
        for key in ordered_keys:
            ordered_rows.append(
                project_ordered(
                    run=run,
                    key=key,
                    rows=by_occurrence[key],
                    account_rows_by_order=accounts_by_order,
                    receipt=receipts[str(run["day"])],
                    loader=loader,
                    predecision=predecision,
                )
            )
        arm_promising = [row for row in promising_rows if row["arm"] == run["arm"]]
        # The same arm label occurs twice, so bind by source day as well.
        arm_promising = [
            row
            for row in arm_promising
            if str((row.get("identity") or {}).get("decision_time_utc") or "").startswith(str(run["day"]))
        ]
        arm_ordered = [
            row
            for row in ordered_rows
            if str((row.get("identity") or {}).get("decision_time_utc") or "").startswith(str(run["day"]))
        ]
        per_arm.append(
            {
                "day": run["day"],
                "arm": run["arm"],
                "policy_status": run["policy_status"],
                "ordered_occurrence_count": len(arm_ordered),
                "filled_trade_count": sum(row["trade"]["present"] for row in arm_ordered),
                "ordered_terminal_outcome_counts": dict(
                    sorted(Counter(row["oracle"]["terminal_outcome"] for row in arm_ordered).items())
                ),
                "promising_reject_count": len(arm_promising),
            }
        )

    ordered_path = ROOT / "OUTCOME_DIAGNOSTIC_ORDERED_34.jsonl"
    promising_path = ROOT / "OUTCOME_DIAGNOSTIC_PROMISING_REJECTS_540.jsonl"
    write_jsonl(ordered_path, ordered_rows)
    write_jsonl(promising_path, promising_rows)
    if len(ordered_rows) != 34 or len(promising_rows) != 540:
        raise ValueError(f"diagnostic_census_count_mismatch:{len(ordered_rows)}:{len(promising_rows)}")
    summary_body = {
        "schema": "gtos.wave21.professional_review.outcome_diagnostic_census.v2",
        "claim_boundary": {
            "explicitly_outcome_aware": True,
            "mixed_policy_cross_arm_pool": True,
            "pooled_economics_interpretation_allowed": False,
            "setup_quality_validation_allowed": False,
            "broker_fill_truth": False,
            "post_lifecycle_all_in_cost_complete": False,
        },
        "bindings": bindings,
        "ordered": {
            "path": ordered_path.name,
            "sha256": sha256_file(ordered_path),
            "occurrence_count": len(ordered_rows),
            "filled_trade_count": sum(row["trade"]["present"] for row in ordered_rows),
            "terminal_outcome_counts": dict(
                sorted(Counter(row["oracle"]["terminal_outcome"] for row in ordered_rows).items())
            ),
            "family_counts": dict(
                sorted(Counter(row["identity"]["origin_family"] for row in ordered_rows).items())
            ),
            "current_poi_far_side_unchosen_reference_status_counts": dict(
                sorted(
                    Counter(
                        row["predecision"]["current_poi_far_side_unchosen_reference"]["status"]
                        for row in ordered_rows
                    ).items()
                )
            ),
            "account_join_status_counts": dict(
                sorted(Counter(row["account"]["join_status"] for row in ordered_rows).items())
            ),
            "close_side_all_in_cost_status_counts": dict(
                sorted(Counter(row["exit"]["close_side_all_in_cost_status"] for row in ordered_rows).items())
            ),
        },
        "promising_rejects": {
            "definition": "all_missed_stage_occurrences_with_counterfactual_terminal_outcome_target_reached_before_stop",
            "path": promising_path.name,
            "sha256": sha256_file(promising_path),
            "occurrence_count": len(promising_rows),
            "family_counts": dict(
                sorted(Counter(row["identity"]["origin_family"] for row in promising_rows).items())
            ),
            "raw_selector_action_counts": dict(
                sorted(Counter(row["raw_selector_action"] for row in promising_rows).items())
            ),
            "interpretation": "complete_counterfactual_census_not_realized_trades_not_setup_validation",
        },
        "per_arm": per_arm,
    }
    summary = {**summary_body, "summary_root_sha256": stable_sha256(summary_body)}
    (ROOT / "OUTCOME_DIAGNOSTIC_CENSUS_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
