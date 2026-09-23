#!/usr/bin/env python3
"""Regenerate AW's 83 B_TIME cells on CJ's true-UTC January pool.

The old cell declarations remain the comparison key. Membership is recomputed
from true-UTC timestamps and the session fields emitted by CJ's corrected
packs; no old label is shifted in place. CK proved the compact pool omits the
terminal-exit field needed to apply F31 row-exactly, so every new mean is
reported as a rigorous interval: the repaired cost-true proxy is the upper
edge, and charging F31 to every row is the conservative lower edge.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra import b7_5_diagnostic_pool as DP  # noqa: E402
from src.research_infra.train_engine import guard, lane  # noqa: E402
from src.research_infra.training_lane import DEFAULT_ITERATION_LEDGER  # noqa: E402


SCHEMA = "gtos.session_cp.true_utc_b_time_regeneration.v1"
MECHANISM = "true_utc_aw_b_time_regeneration"
MIN_TRAIN_ROWS = 200
MIN_HOLDOUT_ROWS = 100
MIN_HOLDOUT_POSITIVE_DAY_SHARE = 0.50

DEFAULT_AW_PROTOCOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
    / "AW_MINE_PROTOCOL_V1.json"
)
DEFAULT_AW_MAP = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
    / "AW_SEPARABILITY_MAP_V1.json"
)
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
DEFAULT_OUT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
    / "CP_TRUE_UTC_B_TIME_MAP_V1.json"
)


class BTimeRefusal(RuntimeError):
    """The requested regeneration is not the declared 83-cell comparison."""


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


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BTimeRefusal(f"object_required:{path}")
    return payload


def declared_b_time_cells(protocol: Mapping[str, Any]) -> list[dict[str, Any]]:
    cells = [
        dict(cell)
        for cell in protocol.get("cells") or ()
        if cell.get("axis_family") == "B_TIME" and cell.get("look_taken") is True
    ]
    ids = [str(cell.get("cell_id") or "") for cell in cells]
    if len(cells) != 83 or len(set(ids)) != 83 or any(not value for value in ids):
        raise BTimeRefusal(f"aw_b_time_family_not_exactly_83:{len(cells)}")
    return cells


def load_true_utc_frame(path: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    if not rows:
        raise BTimeRefusal("true_utc_pool_empty")
    frame = pd.DataFrame(rows)
    required = {
        "decision_time_utc",
        "opportunity_net_proxy_r",
        "utc_hour_bucket",
        "session_bucket",
        "authority_session",
        "route_session",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise BTimeRefusal(f"true_utc_pool_columns_missing:{missing}")
    timestamps = pd.to_datetime(frame["decision_time_utc"], utc=True, errors="coerce")
    if bool(timestamps.isna().any()):
        raise BTimeRefusal("true_utc_decision_timestamp_invalid")
    frame["trading_day"] = timestamps.dt.strftime("%Y-%m-%d")
    frame["decision_hour_utc"] = timestamps.dt.hour.astype(float)
    frame["decision_dow"] = timestamps.dt.dayofweek.astype(float)
    frame["decision_dom"] = timestamps.dt.day.astype(float)
    # `utc_hour_bucket` is the candidate's source-hour bucket, not necessarily
    # the later portfolio decision hour. Several source buckets can therefore
    # share one decision timestamp. Its corrected membership is bound by CJ's
    # regenerated pack/arm receipt; validate its complete 24-hour vocabulary,
    # never fabricate an equality to `decision_time_utc.hour`.
    hour_levels = set(frame["utc_hour_bucket"].dropna().astype(str))
    expected_levels = {f"h{hour:02d}_{(hour + 1) % 24:02d}" for hour in range(24)}
    if hour_levels != expected_levels or any(
        re.fullmatch(r"h(?:[01][0-9]|2[0-3])_(?:[01][0-9]|2[0-3])", level) is None
        for level in hour_levels
    ):
        raise BTimeRefusal(f"utc_hour_bucket_vocabulary_invalid:{sorted(hour_levels)}")
    values = pd.to_numeric(frame["opportunity_net_proxy_r"], errors="coerce")
    if bool(values.isna().any()) or not np.isfinite(values.to_numpy()).all():
        raise BTimeRefusal("true_utc_outcome_invalid")
    frame["repaired_cost_true_net_r_upper"] = values.astype(float)
    frame["repaired_cost_true_net_r_lower"] = (
        values.astype(float) + DP.F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW
    )
    return frame


def cell_mask(frame: pd.DataFrame, cell: Mapping[str, Any]) -> np.ndarray:
    axis = str(cell["axis"])
    if axis not in frame:
        raise BTimeRefusal(f"cell_axis_missing:{axis}")
    if cell.get("cut") == "level_wise":
        level = str(cell.get("level"))
        return (frame[axis].astype("object").map(
            lambda value: str(value) if value is not None else None
        ) == level).to_numpy()
    if cell.get("cut") != "train_tertiles":
        raise BTimeRefusal(f"unsupported_cell_cut:{cell.get('cut')}")
    values = pd.to_numeric(frame[axis], errors="coerce").to_numpy(dtype=float)
    lower, upper = cell.get("lower"), cell.get("upper")
    mask = ~np.isnan(values)
    if lower is not None:
        mask &= values > float(lower)
    if upper is not None:
        mask &= values <= float(upper)
    return mask


def describe_interval(frame: pd.DataFrame, mask: np.ndarray) -> dict[str, Any]:
    sub = frame[mask]
    n = int(len(sub))
    empty = {
        "n": n,
        "mean_r_upper": None,
        "mean_r_lower": None,
        "sum_r_upper": None,
        "sum_r_lower": None,
        "precision_upper": None,
        "precision_lower": None,
        "n_days": 0,
        "day_positive_frac_upper": None,
        "day_positive_frac_lower": None,
        "share_of_rows": None,
    }
    if not n:
        return empty
    upper = sub["repaired_cost_true_net_r_upper"].to_numpy(dtype=float)
    lower = sub["repaired_cost_true_net_r_lower"].to_numpy(dtype=float)
    upper_days = sub.groupby("trading_day")[
        "repaired_cost_true_net_r_upper"
    ].mean()
    lower_days = sub.groupby("trading_day")[
        "repaired_cost_true_net_r_lower"
    ].mean()
    return {
        "n": n,
        "mean_r_upper": round(float(upper.mean()), 8),
        "mean_r_lower": round(float(lower.mean()), 8),
        "sum_r_upper": round(float(upper.sum()), 6),
        "sum_r_lower": round(float(lower.sum()), 6),
        "precision_upper": round(float((upper > 0).mean()), 8),
        "precision_lower": round(float((lower > 0).mean()), 8),
        "n_days": int(len(upper_days)),
        "day_positive_frac_upper": round(float((upper_days > 0).mean()), 8),
        "day_positive_frac_lower": round(float((lower_days > 0).mean()), 8),
        "share_of_rows": round(n / len(frame), 8),
    }


def old_january_verdict(cell: Mapping[str, Any]) -> str:
    if cell.get("F1_train") is not True:
        return "F1_TRAIN"
    if cell.get("F2_holdout") is not True:
        return "F2_HOLDOUT"
    if cell.get("F3_holdout_stability") is not True:
        return "F3_HOLDOUT_BREADTH"
    return "JANUARY_SURVIVOR"


def interval_january_verdict(
    train: Mapping[str, Any], holdout: Mapping[str, Any]
) -> str:
    if int(train.get("n") or 0) < MIN_TRAIN_ROWS:
        return "F1_TRAIN_DENOMINATOR"
    if float(train["mean_r_upper"]) <= 0.0:
        return "F1_TRAIN"
    if float(train["mean_r_lower"]) <= 0.0:
        return "UNRESOLVED_F31_AT_F1"
    if int(holdout.get("n") or 0) < MIN_HOLDOUT_ROWS:
        return "F2_HOLDOUT_DENOMINATOR"
    if float(holdout["mean_r_upper"]) <= 0.0:
        return "F2_HOLDOUT"
    if float(holdout["mean_r_lower"]) <= 0.0:
        return "UNRESOLVED_F31_AT_F2"
    upper_share = float(holdout["day_positive_frac_upper"])
    lower_share = float(holdout["day_positive_frac_lower"])
    if upper_share < MIN_HOLDOUT_POSITIVE_DAY_SHARE:
        return "F3_HOLDOUT_BREADTH"
    if lower_share < MIN_HOLDOUT_POSITIVE_DAY_SHARE:
        return "UNRESOLVED_F31_AT_F3"
    return "JANUARY_SURVIVOR_ROBUST_TO_F31_BOUND"


def regenerate(
    *,
    aw_protocol_path: Path,
    aw_map_path: Path,
    pool_path: Path,
    pool_receipt_path: Path,
) -> dict[str, Any]:
    protocol = _json(aw_protocol_path)
    old_map = _json(aw_map_path)
    pool_receipt = _json(pool_receipt_path)
    cells = declared_b_time_cells(protocol)
    if old_map.get("protocol_sha256") != protocol.get("self_sha256"):
        raise BTimeRefusal("aw_map_protocol_binding_mismatch")
    if old_map.get("cells_sha256_recomputed") != stable_sha(protocol.get("cells")):
        raise BTimeRefusal("aw_declared_cell_digest_mismatch")
    old_by_id = {str(row.get("cell_id")): row for row in old_map.get("cells") or ()}
    missing_old = sorted(str(cell["cell_id"]) for cell in cells if cell["cell_id"] not in old_by_id)
    if missing_old:
        raise BTimeRefusal(f"aw_map_cells_missing:{missing_old}")

    frame = load_true_utc_frame(pool_path)
    if int(pool_receipt.get("diagnostic_scoreable_rows") or -1) != len(frame):
        raise BTimeRefusal("true_utc_pool_row_count_mismatch")
    train_days = [str(day) for day in protocol["split"]["train_days"]]
    holdout_days = [str(day) for day in protocol["split"]["holdout_days"]]
    declared_days = set(train_days) | set(holdout_days)
    observed_days = set(frame["trading_day"].astype(str).unique())
    if observed_days != declared_days:
        raise BTimeRefusal(
            "true_utc_day_membership_drift:"
            + json.dumps(
                {
                    "missing": sorted(declared_days - observed_days),
                    "unexpected": sorted(observed_days - declared_days),
                },
                sort_keys=True,
            )
        )
    train_frame = frame[frame["trading_day"].isin(train_days)]
    holdout_frame = frame[frame["trading_day"].isin(holdout_days)]

    rows: list[dict[str, Any]] = []
    transitions: collections.Counter[str] = collections.Counter()
    for cell in cells:
        cell_id = str(cell["cell_id"])
        old = old_by_id[cell_id]
        train = describe_interval(train_frame, cell_mask(train_frame, cell))
        holdout = describe_interval(holdout_frame, cell_mask(holdout_frame, cell))
        old_verdict = old_january_verdict(old)
        new_verdict = interval_january_verdict(train, holdout)
        transitions[f"{old_verdict}->{new_verdict}"] += 1
        rows.append(
            {
                "cell_id": cell_id,
                "axis": cell["axis"],
                "axis_family": "B_TIME",
                "cut": cell["cut"],
                "declared_cell": {
                    key: cell.get(key)
                    for key in ("level", "tertile", "lower", "upper")
                    if key in cell
                },
                "old_wrong_clock": {
                    "january_verdict": old_verdict,
                    "train": old.get("train"),
                    "holdout": old.get("holdout"),
                },
                "true_utc": {
                    "january_verdict": new_verdict,
                    "train": train,
                    "holdout": holdout,
                },
                "diff": {
                    "verdict_changed": old_verdict != new_verdict,
                    "train_n_delta": int(train["n"]) - int((old.get("train") or {}).get("n") or 0),
                    "holdout_n_delta": int(holdout["n"]) - int((old.get("holdout") or {}).get("n") or 0),
                },
            }
        )

    pool_hash = file_sha256(pool_path)
    core = {
        "schema": SCHEMA,
        "session": "CP",
        "blocks": "B2850-B2899",
        "status": "AW_B_TIME_REGENERATED_ON_TRUE_UTC_JANUARY",
        "cell_count": len(rows),
        "cell_ids_preserved_for_one_to_one_diff": True,
        "regeneration_not_relabel": (
            "decision_hour/day fields are re-derived from decision_time_utc; "
            "source-hour and session fields are consumed from CJ's true-UTC "
            "re-materialized packs rather than shifted in this tool"
        ),
        "split": {"train_days": train_days, "holdout_days": holdout_days},
        "outcome_contract": {
            "upper": "opportunity_net_proxy_r from CJ's repaired commission+swap arm",
            "lower": (
                "upper + F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW on every row; "
                "conservative because CK's compact projection lacks terminal-exit provenance"
            ),
            "f31_r_per_row_if_level_exit": DP.F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW,
            "row_exact_f31_available": False,
            "verdict_rule": (
                "pass requires both interval edges above zero; fail requires the upper "
                "edge non-positive; a straddle is explicitly unresolved"
            ),
            "comparison_scope": (
                "old AW net_r_aw versus true-UTC repaired-stack interval; metrics are not "
                "claimed as a clock-only causal delta"
            ),
        },
        "inputs": {
            "aw_protocol": str(aw_protocol_path.relative_to(REPO)),
            "aw_protocol_sha256": file_sha256(aw_protocol_path),
            "aw_map": str(aw_map_path.relative_to(REPO)),
            "aw_map_sha256": file_sha256(aw_map_path),
            "true_utc_pool": str(pool_path.relative_to(REPO)),
            "true_utc_pool_sha256": pool_hash,
            "true_utc_pool_receipt": str(pool_receipt_path.relative_to(REPO)),
            "true_utc_pool_receipt_sha256": file_sha256(pool_receipt_path),
            "true_utc_scoreable_rows": len(frame),
        },
        "verdict_transition_counts": dict(sorted(transitions.items())),
        "verdict_changed_cell_count": sum(
            int(row["diff"]["verdict_changed"]) for row in rows
        ),
        "cells": rows,
        "economic_outcomes_read": True,
        "surface": "VAL",
        "billed": False,
        "admission_or_graduation_claim": False,
        "march_2026_outcomes_read": False,
        "live_forward_test_read": False,
    }
    return {**core, "receipt_root_sha256": stable_sha(core)}


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def log_cell_looks(
    *, receipt: Mapping[str, Any], receipt_path: Path, ledger_path: Path
) -> list[dict[str, Any]]:
    receipt_ref = _repo_relative(receipt_path)
    if ledger_path.is_file():
        existing = []
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
            if len(existing) == int(receipt["cell_count"]):
                return existing
            raise BTimeRefusal(f"partial_existing_look_log:{len(existing)}")

    days = list(receipt["split"]["train_days"]) + list(
        receipt["split"]["holdout_days"]
    )
    authorization = guard.authorize_window(
        start=min(days),
        end=max(days),
        purpose=guard.PURPOSE_LANE_ITERATION,
        context="session_cp:true_utc_aw_b_time_regeneration",
        note="AW's 83 predeclared B_TIME cells regenerated on corrected January VAL rows.",
    )
    logged = []
    for row in receipt["cells"]:
        true_utc = row["true_utc"]
        logged.append(
            lane.log_look(
                authorization=authorization,
                spec={
                    "family": "AW_B_TIME_83_TRUE_UTC_REGENERATION",
                    "aw_cell_id": row["cell_id"],
                    "aw_declared_cell": row["declared_cell"],
                    "source_pool_sha256": receipt["inputs"]["true_utc_pool_sha256"],
                    "outcome_interval": receipt["outcome_contract"],
                },
                session="CP",
                verdict="evaluated",
                metric=true_utc["train"].get("mean_r_upper"),
                metric_name="true_utc_train_mean_repaired_cost_true_net_r_upper",
                note=(
                    f"Old={row['old_wrong_clock']['january_verdict']}; "
                    f"true-UTC={true_utc['january_verdict']}; unbilled VAL regeneration."
                ),
                receipt=receipt_ref,
                ledger_path=ledger_path,
                mechanism=MECHANISM,
                extra={
                    "cell_id": row["cell_id"],
                    "old_january_verdict": row["old_wrong_clock"]["january_verdict"],
                    "true_utc_january_verdict": true_utc["january_verdict"],
                    "f31_interval_bound": True,
                    "march_outcomes_read": False,
                },
            )
        )
    return logged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aw-protocol", type=Path, default=DEFAULT_AW_PROTOCOL)
    parser.add_argument("--aw-map", type=Path, default=DEFAULT_AW_MAP)
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--pool-receipt", type=Path, default=DEFAULT_POOL_RECEIPT)
    parser.add_argument("--iteration-ledger", type=Path, default=DEFAULT_ITERATION_LEDGER)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-log", action="store_true", help="tests only")
    args = parser.parse_args()
    if args.out.exists():
        raise BTimeRefusal(f"output_already_exists:{args.out}")
    receipt = regenerate(
        aw_protocol_path=args.aw_protocol.resolve(),
        aw_map_path=args.aw_map.resolve(),
        pool_path=args.pool.resolve(),
        pool_receipt_path=args.pool_receipt.resolve(),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    logged = [] if args.no_log else log_cell_looks(
        receipt=receipt,
        receipt_path=args.out,
        ledger_path=args.iteration_ledger,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "cell_count": receipt["cell_count"],
                "verdict_changed_cell_count": receipt["verdict_changed_cell_count"],
                "verdict_transition_counts": receipt["verdict_transition_counts"],
                "logged_looks": len(logged),
                "out": str(args.out),
            },
            indent=1,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
