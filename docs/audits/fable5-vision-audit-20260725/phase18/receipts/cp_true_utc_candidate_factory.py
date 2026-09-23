#!/usr/bin/env python3
"""Declare and mine Session CP's true-UTC time-conditioned policy family.

`declare` is data-free: it writes the complete 1,092-cell family before any
conditional outcome is evaluated. `mine` reads only the protocol's January
TRAIN dates, logs every declared look, and reports robust survivors under the
row-exact-current-cost / conservative-F31 interval. It never evaluates March,
live-forward TEST, or the January holdout outcomes.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra import b7_5_diagnostic_pool as DP  # noqa: E402
from src.research_infra.train_engine import guard, lane  # noqa: E402
from src.research_infra.training_lane import DEFAULT_ITERATION_LEDGER  # noqa: E402
from src.research_infra.training_lane.iteration_ledger import (  # noqa: E402
    candidate_id as iteration_candidate_id,
    spec_digest,
)


PROTOCOL_SCHEMA = "gtos.session_cp.true_utc_candidate_factory_protocol.v1"
RESULT_SCHEMA = "gtos.session_cp.true_utc_candidate_factory_result.v1"
MECHANISM = "true_utc_time_conditioned_policy_factory"
MIN_TRAIN_ROWS = 200
MIN_TRAIN_DAYS = 10
MIN_POSITIVE_DAY_SHARE = 0.60

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
DEFAULT_PROTOCOL = HERE / "CP_TRUE_UTC_CANDIDATE_FACTORY_PROTOCOL_V1.json"
DEFAULT_RESULT = HERE / "CP_TRUE_UTC_CANDIDATE_FACTORY_RESULT_V1.json"
DEFAULT_POOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools"
    / "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
DEFAULT_POOL_RECEIPT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts"
    / "CJ_RECLOCKED_POOL_S0R0_V1.json"
)

TRAIN_DAYS = (
    "2026-01-02",
    "2026-01-05",
    "2026-01-06",
    "2026-01-07",
    "2026-01-08",
    "2026-01-09",
    "2026-01-12",
    "2026-01-13",
    "2026-01-14",
    "2026-01-15",
    "2026-01-16",
    "2026-01-19",
    "2026-01-20",
)
HOLDOUT_DAYS_NOT_EVALUATED = (
    "2026-01-21",
    "2026-01-22",
    "2026-01-23",
    "2026-01-26",
    "2026-01-27",
    "2026-01-28",
    "2026-01-29",
    "2026-01-30",
)

ASSET_GROUPS = {
    "fx": (
        "AUDJPY", "AUDUSD", "CHFJPY", "EURGBP", "EURJPY", "EURUSD",
        "GBPJPY", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
    ),
    "indices": ("GER40", "JP225", "NAS100", "SPX500", "UK100", "US30_cash"),
    "metals": ("XAGUSD", "XAUUSD"),
    "crypto": ("BTCUSD", "ETHUSD"),
    "energy": ("UKOIL_cash", "USOIL_cash"),
}


class FactoryRefusal(RuntimeError):
    """The declaration, source, or look ledger failed closed."""


def stable_sha(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def predicate(field: str, op: str, value: Any) -> dict[str, Any]:
    return {"field": field, "op": op, "value": value}


def _condition(condition_id: str, *predicates: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "condition_id": condition_id,
        "all": [dict(item) for item in predicates],
    }


def time_predicates() -> list[dict[str, Any]]:
    result = [
        {
            "time_id": f"source_hour_{hour:02d}",
            "all": [
                predicate(
                    "utc_hour_bucket",
                    "eq",
                    f"h{hour:02d}_{(hour + 1) % 24:02d}",
                )
            ],
        }
        for hour in range(24)
    ]
    result.extend(
        {
            "time_id": f"route_session_{session}",
            "all": [predicate("route_session", "eq", session)],
        }
        for session in ("tokyo", "london", "ny", "off_configured_session")
    )
    return result


def conditioning_predicates() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = [
        _condition("direction_LONG", predicate("direction", "eq", "LONG")),
        _condition("direction_SHORT", predicate("direction", "eq", "SHORT")),
        _condition(
            "broker_cost_executable",
            predicate("broker_pretrade_cost_executable", "eq", True),
        ),
    ]
    for group, symbols in ASSET_GROUPS.items():
        result.append(_condition(f"asset_{group}", predicate("symbol", "in", list(symbols))))
        for direction in ("LONG", "SHORT"):
            result.append(
                _condition(
                    f"asset_{group}__direction_{direction}",
                    predicate("symbol", "in", list(symbols)),
                    predicate("direction", "eq", direction),
                )
            )
    for ceiling in (0.10, 0.25, 0.50, 1.00):
        tag = f"{ceiling:.2f}".replace(".", "p")
        result.append(
            _condition(
                f"executable_cost_lte_{tag}",
                predicate("broker_pretrade_cost_executable", "eq", True),
                predicate("cost_r", "lte", ceiling),
            )
        )
    for floor in (0.0, 0.5, 1.0):
        tag = f"{floor:.1f}".replace(".", "p")
        result.append(
            _condition(
                f"candidate_ev_gte_{tag}",
                predicate("candidate_ev_r", "gte", floor),
            )
        )
    for floor in (0.50, 0.75):
        tag = f"{floor:.2f}".replace(".", "p")
        result.append(
            _condition(
                f"fill_probability_gte_{tag}",
                predicate("fill_probability", "gte", floor),
            )
        )
    for ceiling in (0.10, 0.25, 0.50, 1.00):
        cost_tag = f"{ceiling:.2f}".replace(".", "p")
        for floor in (0.0, 0.5, 1.0):
            ev_tag = f"{floor:.1f}".replace(".", "p")
            result.append(
                _condition(
                    f"executable_cost_lte_{cost_tag}__candidate_ev_gte_{ev_tag}",
                    predicate("broker_pretrade_cost_executable", "eq", True),
                    predicate("cost_r", "lte", ceiling),
                    predicate("candidate_ev_r", "gte", floor),
                )
            )
    ids = [row["condition_id"] for row in result]
    if len(result) != 39 or len(set(ids)) != 39:
        raise FactoryRefusal(f"conditioning_family_not_39:{len(result)}")
    return result


def declared_cells() -> list[dict[str, Any]]:
    cells = []
    for time_rule in time_predicates():
        for condition in conditioning_predicates():
            cell_id = f"{time_rule['time_id']}__{condition['condition_id']}"
            cells.append(
                {
                    "cell_id": cell_id,
                    "time": time_rule,
                    "condition": condition,
                    "look_taken": True,
                    "policy_action": "admit_if_all_pretrade_predicates_match",
                }
            )
    if len(cells) != 1092 or len({cell["cell_id"] for cell in cells}) != 1092:
        raise FactoryRefusal(f"declared_family_not_1092:{len(cells)}")
    return cells


def build_protocol(*, declared_utc: str | None = None) -> dict[str, Any]:
    cells = declared_cells()
    core = {
        "schema": PROTOCOL_SCHEMA,
        "session": "CP",
        "blocks": "B2850-B2899",
        "declared_utc": declared_utc or dt.datetime.now(dt.timezone.utc).isoformat(),
        "declared_before_conditional_outcome_evaluation": True,
        "question": (
            "Does corrected source-hour or route-session membership become a robust "
            "positive admission policy when crossed with a fixed, pretrade-implementable "
            "direction, asset, broker-cost, candidate-EV, or fill condition?"
        ),
        "substrate": {
            "pool": (
                "phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
            ),
            "clock": "true_utc",
            "arm": "S0R0",
            "surface": "VAL",
            "train_days": list(TRAIN_DAYS),
            "holdout_days_reserved_not_evaluated_by_factory": list(
                HOLDOUT_DAYS_NOT_EVALUATED
            ),
            "march_outcomes": "FORBIDDEN_AND_UNREAD",
            "live_forward_test": "FORBIDDEN_EXCEPT_VETO_AND_UNREAD",
        },
        "family_construction": {
            "time_predicate_count": 28,
            "conditioning_predicate_count": 39,
            "cross_product": "28 x 39",
            "declared_look_count": len(cells),
            "selection_from_outcomes": False,
            "implementability": (
                "Every predicate is known before order admission: corrected source hour, "
                "route session, symbol/asset, direction, broker cost executability and "
                "cost R, candidate EV, or fill probability."
            ),
        },
        "train_gate": {
            "minimum_rows": MIN_TRAIN_ROWS,
            "minimum_days": MIN_TRAIN_DAYS,
            "minimum_positive_day_share": MIN_POSITIVE_DAY_SHARE,
            "mean_r": "lower interval edge > 0",
            "precision": "lower interval edge > 0.50",
            "all_required": True,
            "survivor_disposition": (
                "graduate exactly once to CANDIDATE_BOOK_V1 all-declared and run the "
                "frozen B_balanced alpha 0.10 gate on RECORDED eras"
            ),
        },
        "outcome_interval": {
            "upper": "opportunity_net_proxy_r on CJ commission+swap repaired arm",
            "lower": (
                "upper + F31 charge on every row; conservative because compact CK "
                "projection lacks terminal-exit provenance"
            ),
            "f31_r_per_row": DP.F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW,
            "pass_must_be_robust_to_interval": True,
        },
        "cells": cells,
        "billed": False,
        "billing_rule": (
            "All TRAIN looks are unbilled; each actual survivor graduates once through "
            "training_lane.graduate, which alone moves the family ratchet."
        ),
        "admission_claim": False,
    }
    return {**core, "protocol_root_sha256": stable_sha(core)}


def _apply_predicate(frame: pd.DataFrame, rule: Mapping[str, Any]) -> np.ndarray:
    field = str(rule["field"])
    if field not in frame:
        raise FactoryRefusal(f"predicate_field_missing:{field}")
    op, value = str(rule["op"]), rule.get("value")
    series = frame[field]
    if op == "eq":
        return (series == value).to_numpy()
    if op == "in":
        return series.isin(list(value)).to_numpy()
    numeric = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    valid = ~np.isnan(numeric)
    if op == "lte":
        return valid & (numeric <= float(value))
    if op == "gte":
        return valid & (numeric >= float(value))
    raise FactoryRefusal(f"predicate_op_unknown:{op}")


def cell_mask(frame: pd.DataFrame, cell: Mapping[str, Any]) -> np.ndarray:
    mask = np.ones(len(frame), dtype=bool)
    for group in (cell["time"], cell["condition"]):
        for rule in group["all"]:
            mask &= _apply_predicate(frame, rule)
    return mask


def _load_rows(path: Path) -> pd.DataFrame:
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    frame = pd.DataFrame(rows)
    needed = {
        "decision_time_utc", "opportunity_net_proxy_r", "utc_hour_bucket",
        "route_session", "direction", "symbol", "broker_pretrade_cost_executable",
        "cost_r", "candidate_ev_r", "fill_probability",
    }
    missing = sorted(needed - set(frame))
    if missing:
        raise FactoryRefusal(f"pool_fields_missing:{missing}")
    timestamps = pd.to_datetime(frame["decision_time_utc"], utc=True, errors="coerce")
    if bool(timestamps.isna().any()):
        raise FactoryRefusal("decision_time_invalid")
    frame["trading_day"] = timestamps.dt.strftime("%Y-%m-%d")
    return frame


def describe_train(frame: pd.DataFrame, mask: np.ndarray) -> dict[str, Any]:
    sub = frame[mask]
    n = int(len(sub))
    if not n:
        return {
            "n": 0, "n_days": 0, "mean_r_upper": None, "mean_r_lower": None,
            "precision_upper": None, "precision_lower": None,
            "positive_day_share_upper": None, "positive_day_share_lower": None,
        }
    upper = pd.to_numeric(sub["opportunity_net_proxy_r"], errors="coerce")
    if bool(upper.isna().any()) or not np.isfinite(upper.to_numpy()).all():
        raise FactoryRefusal("train_outcome_invalid")
    lower = upper + DP.F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW
    upper_days = pd.DataFrame(
        {"day": sub["trading_day"].to_numpy(), "r": upper.to_numpy()}
    ).groupby("day")["r"].mean()
    lower_days = pd.DataFrame(
        {"day": sub["trading_day"].to_numpy(), "r": lower.to_numpy()}
    ).groupby("day")["r"].mean()
    return {
        "n": n,
        "n_days": int(len(upper_days)),
        "mean_r_upper": round(float(upper.mean()), 8),
        "mean_r_lower": round(float(lower.mean()), 8),
        "precision_upper": round(float((upper > 0).mean()), 8),
        "precision_lower": round(float((lower > 0).mean()), 8),
        "positive_day_share_upper": round(float((upper_days > 0).mean()), 8),
        "positive_day_share_lower": round(float((lower_days > 0).mean()), 8),
    }


def train_gate(metrics: Mapping[str, Any]) -> tuple[bool, dict[str, bool]]:
    checks = {
        "minimum_rows": int(metrics.get("n") or 0) >= MIN_TRAIN_ROWS,
        "minimum_days": int(metrics.get("n_days") or 0) >= MIN_TRAIN_DAYS,
        "mean_positive_at_f31_lower_bound": (
            metrics.get("mean_r_lower") is not None
            and float(metrics["mean_r_lower"]) > 0.0
        ),
        "precision_above_half_at_f31_lower_bound": (
            metrics.get("precision_lower") is not None
            and float(metrics["precision_lower"]) > 0.50
        ),
        "positive_day_breadth_at_f31_lower_bound": (
            metrics.get("positive_day_share_lower") is not None
            and float(metrics["positive_day_share_lower"]) >= MIN_POSITIVE_DAY_SHARE
        ),
    }
    return all(checks.values()), checks


def candidate_spec(protocol: Mapping[str, Any], cell: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "family": "CP_TRUE_UTC_TIME_CONDITIONED_POLICY_V1",
        "protocol_root_sha256": protocol["protocol_root_sha256"],
        "cell_id": cell["cell_id"],
        "time": cell["time"],
        "condition": cell["condition"],
        "policy_action": cell["policy_action"],
        "source_arm": "CJ_RECLOCKED_S0R0_V7",
        "train_days": list(TRAIN_DAYS),
        "outcome_interval": protocol["outcome_interval"],
    }


def mine(
    *, protocol_path: Path, pool_path: Path, pool_receipt_path: Path
) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("schema") != PROTOCOL_SCHEMA:
        raise FactoryRefusal("protocol_schema_invalid")
    core = dict(protocol)
    observed_root = core.pop("protocol_root_sha256", None)
    if observed_root != stable_sha(core):
        raise FactoryRefusal("protocol_root_mismatch")
    if len(protocol.get("cells") or ()) != 1092:
        raise FactoryRefusal("protocol_family_size_drift")
    receipt = json.loads(pool_receipt_path.read_text(encoding="utf-8"))
    frame = _load_rows(pool_path)
    if len(frame) != int(receipt.get("diagnostic_scoreable_rows") or -1):
        raise FactoryRefusal("pool_receipt_count_mismatch")
    train = frame[frame["trading_day"].isin(TRAIN_DAYS)].copy()
    if set(train["trading_day"].unique()) != set(TRAIN_DAYS):
        raise FactoryRefusal("train_days_incomplete")

    results = []
    reasons: collections.Counter[str] = collections.Counter()
    for cell in protocol["cells"]:
        metrics = describe_train(train, cell_mask(train, cell))
        survives, checks = train_gate(metrics)
        spec = candidate_spec(protocol, cell)
        cid = iteration_candidate_id(mechanism=MECHANISM, sleeve="", spec=spec)
        failed = next((name for name, passed in checks.items() if not passed), "SURVIVOR")
        reasons[failed] += 1
        results.append(
            {
                "cell_id": cell["cell_id"],
                "candidate_id": cid,
                "spec_digest": spec_digest(spec),
                "spec": spec,
                "train": metrics,
                "checks": checks,
                "train_survivor": survives,
                "first_failed_check": failed,
                "holdout_outcome": "NOT_EVALUATED_BY_FACTORY",
            }
        )
    survivors = [row for row in results if row["train_survivor"]]
    result_core = {
        "schema": RESULT_SCHEMA,
        "session": "CP",
        "blocks": "B2850-B2899",
        "status": (
            "TRAIN_SURVIVORS_REQUIRE_GRADUATION_AND_RECORDED_GATE"
            if survivors
            else "NO_TRUE_UTC_TIME_CONDITIONED_TRAIN_SURVIVOR"
        ),
        "protocol": str(protocol_path.relative_to(REPO)),
        "protocol_sha256": file_sha256(protocol_path),
        "protocol_root_sha256": protocol["protocol_root_sha256"],
        "pool": str(pool_path.relative_to(REPO)),
        "pool_sha256": file_sha256(pool_path),
        "pool_receipt": str(pool_receipt_path.relative_to(REPO)),
        "pool_receipt_sha256": file_sha256(pool_receipt_path),
        "declared_look_count": len(results),
        "train_scoreable_rows": len(train),
        "train_days": list(TRAIN_DAYS),
        "holdout_days_not_evaluated": list(HOLDOUT_DAYS_NOT_EVALUATED),
        "first_failed_check_counts": dict(sorted(reasons.items())),
        "train_survivor_count": len(survivors),
        "survivor_candidate_ids": [row["candidate_id"] for row in survivors],
        "results": results,
        "surface": "VAL",
        "billed": False,
        "admission_or_graduation_claim": False,
        "march_2026_outcomes_read": False,
        "live_forward_test_read": False,
        "holdout_outcomes_evaluated": False,
    }
    return {**result_core, "receipt_root_sha256": stable_sha(result_core)}


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def log_results(
    *, result: Mapping[str, Any], result_path: Path, ledger_path: Path
) -> list[dict[str, Any]]:
    receipt_ref = _repo_relative(result_path)
    existing = []
    if ledger_path.is_file():
        with ledger_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if (
                    row.get("session") == "CP"
                    and row.get("mechanism") == MECHANISM
                    and row.get("receipt") == receipt_ref
                ):
                    existing.append(row)
    if existing:
        if len(existing) == int(result["declared_look_count"]):
            return existing
        raise FactoryRefusal(f"partial_existing_look_log:{len(existing)}")

    authorization = guard.authorize_window(
        start=min(TRAIN_DAYS),
        end=max(TRAIN_DAYS),
        purpose=guard.PURPOSE_LANE_ITERATION,
        context="session_cp:true_utc_candidate_factory",
        note="All 1,092 cells were committed before conditional TRAIN evaluation.",
    )
    logged = []
    for item in result["results"]:
        row = lane.log_look(
            authorization=authorization,
            spec=item["spec"],
            session="CP",
            verdict=(
                "not_evaluable"
                if not item["checks"]["minimum_rows"]
                or not item["checks"]["minimum_days"]
                else "evaluated"
            ),
            metric=item["train"].get("mean_r_lower"),
            metric_name="train_mean_repaired_cost_true_net_r_f31_lower_bound",
            note=(
                f"Declared true-UTC cell; first_failed={item['first_failed_check']}; "
                f"train_survivor={item['train_survivor']}; unbilled VAL look."
            ),
            receipt=receipt_ref,
            ledger_path=ledger_path,
            mechanism=MECHANISM,
            extra={
                "cell_id": item["cell_id"],
                "train_survivor": item["train_survivor"],
                "first_failed_check": item["first_failed_check"],
                "march_outcomes_read": False,
            },
        )
        if row["candidate_id"] != item["candidate_id"]:
            raise FactoryRefusal("logged_candidate_identity_drift")
        logged.append(row)
    return logged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("declare", "mine"))
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--pool-receipt", type=Path, default=DEFAULT_POOL_RECEIPT)
    parser.add_argument("--iteration-ledger", type=Path, default=DEFAULT_ITERATION_LEDGER)
    parser.add_argument("--out", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--no-log", action="store_true", help="tests only")
    args = parser.parse_args()
    if args.stage == "declare":
        if args.protocol.exists():
            raise FactoryRefusal(f"protocol_already_exists:{args.protocol}")
        protocol = build_protocol()
        args.protocol.parent.mkdir(parents=True, exist_ok=True)
        args.protocol.write_text(
            json.dumps(protocol, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "protocol": str(args.protocol),
            "declared_look_count": len(protocol["cells"]),
            "protocol_root_sha256": protocol["protocol_root_sha256"],
            "conditional_outcomes_evaluated": False,
        }, indent=1, sort_keys=True))
        return 0

    if args.out.exists():
        raise FactoryRefusal(f"result_already_exists:{args.out}")
    result = mine(
        protocol_path=args.protocol.resolve(),
        pool_path=args.pool.resolve(),
        pool_receipt_path=args.pool_receipt.resolve(),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    logged = [] if args.no_log else log_results(
        result=result, result_path=args.out, ledger_path=args.iteration_ledger
    )
    print(json.dumps({
        "status": result["status"],
        "declared_look_count": result["declared_look_count"],
        "logged_look_count": len(logged),
        "train_survivor_count": result["train_survivor_count"],
        "first_failed_check_counts": result["first_failed_check_counts"],
        "out": str(args.out),
    }, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
