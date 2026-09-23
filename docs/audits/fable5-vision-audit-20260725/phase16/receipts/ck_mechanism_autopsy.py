#!/usr/bin/env python3
"""Session CK: zero-replay mechanism autopsy over CD's committed repaired pools.

The committed compact pools do not contain the ordered path payload claimed by the
commission.  This program therefore has two deliberately separate products:

* exact measurements that the 78 committed columns really identify (the recorded
  geometry, entry taxonomy, and endpoint-order diagnostics); and
* strict row-wise bounds for every predeclared geometry/direction cell.

It never opens a replay artifact, prepared-day pack, tick file, broker module, config, or
March outcome.  ``--commit-looks`` appends every declared look to the training-lane
iteration ledger as Session CK / VAL / unbilled, idempotently by ``extra.look_id``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.training_lane.append_only import (  # noqa: E402
    atomic_write_json,
    read_rows,
)
from src.research_infra.training_lane.iteration_ledger import (  # noqa: E402
    DEFAULT_ITERATION_LEDGER,
    IterationLedger,
)

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase16/receipts"
PROTOCOL = HERE / "CK_MECHANISM_PROTOCOL_V1.json"
CONTRACT_OUT = HERE / "CK_POOL_PATH_CONTRACT_V1.json"
MAP_OUT = HERE / "CK_MECHANISM_MAP_V1.json"
LOOK_MANIFEST_OUT = HERE / "CK_LOOK_MANIFEST_V1.json"
LOOK_RECEIPT_OUT = HERE / "CK_LOOK_LEDGER_RECEIPT_V1.json"

EXPECTED_PROTOCOL_SHA256 = "8c641a360cf3f1c995bbfd239bba78728b22343d8510511684d2cdd42bef9df3"
ENGINE_VERSION = "gtos.session_ck.committed_pool_partial_id.v1"
RUN_ID = "CK_MECHANISM_AUTOPSY_V1"
TOL = 1e-9

EXACT_PATH_FIELDS = (
    "ordered_path_observations",
    "path_observations",
    "path_rows",
    "observations",
)
AMBIGUITY_FIELDS = (
    "same_bar_ambiguity",
    "target_first_touch_utc",
    "stop_first_touch_utc",
    "path_ambiguity_status",
    "ambiguity_resolution",
)
SOURCE_OUTCOME_FIELDS = (
    "opportunity_gross_r",
    "opportunity_close_reason",
    "terminal_outcome",
    "counterfactual_order_close_time_utc",
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha_obj(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _utc_now() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).isoformat()


def _native(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_native(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _write_sealed(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    out = _native(dict(payload))
    out["self_sha256"] = _sha_obj(out)
    atomic_write_json(path, out, indent=1)
    return out


def _repo_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True, check=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def load_protocol() -> dict[str, Any]:
    got = _sha256_file(PROTOCOL)
    if got != EXPECTED_PROTOCOL_SHA256:
        raise SystemExit(
            f"protocol drift: {got} != declared {EXPECTED_PROTOCOL_SHA256}; refuse outcome read"
        )
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def _normal(value: Any) -> str:
    if value is None:
        return "__MISSING__"
    try:
        if pd.isna(value):
            return "__MISSING__"
    except (TypeError, ValueError):
        pass
    text = str(value)
    return text if text else "__MISSING__"


def _normal_series(series: pd.Series) -> pd.Series:
    return series.map(_normal)


def _partition_signature(series: pd.Series) -> str:
    codes, uniques = pd.factorize(_normal_series(series), sort=False)
    return hashlib.sha256(
        np.asarray(codes, dtype=np.int32).tobytes() + str(len(uniques)).encode()
    ).hexdigest()


def _read_pool(spec: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = REPO / spec["path"]
    got_sha = _sha256_file(path)
    if got_sha != spec["sha256"]:
        raise SystemExit(f"input drift for {path}: {got_sha} != {spec['sha256']}")

    rows: list[dict[str, Any]] = []
    column_sets: set[tuple[str, ...]] = set()
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            rows.append(row)
            column_sets.add(tuple(sorted(row)))
    if len(rows) != int(spec["rows"]):
        raise SystemExit(f"row-count drift for {path}: {len(rows)} != {spec['rows']}")
    if len(column_sets) != 1:
        raise SystemExit(f"row schema is not stable in {path}: {len(column_sets)} variants")
    columns = set(column_sets.pop())
    if len(columns) != int(spec["columns"]):
        raise SystemExit(f"column-count drift for {path}: {len(columns)} != {spec['columns']}")

    required = {
        "candidate_id", "decision_time_utc", "entry_price", "stop_loss", "take_profit_1",
        "policy_target_r", "cost_r", "opportunity_net_proxy_r",
    }
    missing = sorted(required - columns)
    if missing:
        raise SystemExit(f"required committed columns absent from {path}: {missing}")

    frame = pd.DataFrame(rows)
    frame["arm_id"] = spec["arm"]
    frame["decision_ts"] = pd.to_datetime(frame["decision_time_utc"], utc=True, errors="raise")
    frame["trading_day"] = frame["decision_ts"].dt.date.astype(str)
    if frame["trading_day"].str.startswith("2026-03").any():
        raise SystemExit("March 2026 outcome encountered; Session CK refuses to read it")
    if not frame["trading_day"].str.startswith("2026-01").all():
        raise SystemExit(f"non-January row in {spec['arm']}")

    for name in (
        "entry_price", "stop_loss", "take_profit_1", "policy_target_r", "cost_r",
        "opportunity_net_proxy_r",
    ):
        frame[name] = pd.to_numeric(frame[name], errors="coerce")
    bad_numeric = frame[
        ["entry_price", "stop_loss", "take_profit_1", "policy_target_r", "cost_r",
         "opportunity_net_proxy_r"]
    ].isna().any(axis=1)
    if bad_numeric.any():
        raise SystemExit(f"{spec['arm']} has {int(bad_numeric.sum())} rows missing required numerics")

    frame["base_distance"] = (frame["entry_price"] - frame["stop_loss"]).abs()
    if (frame["base_distance"] <= 0).any():
        raise SystemExit(f"{spec['arm']} has zero-width stop geometry")
    frame["recorded_target_distance"] = (
        (frame["take_profit_1"] - frame["entry_price"]).abs() / frame["base_distance"]
    )
    frame["recorded_gross_r"] = frame["opportunity_net_proxy_r"] + frame["cost_r"]
    target = np.isclose(
        frame["recorded_gross_r"].to_numpy(float),
        frame["policy_target_r"].to_numpy(float), atol=TOL, rtol=0,
    )
    stop = np.isclose(frame["recorded_gross_r"].to_numpy(float), -1.0, atol=TOL, rtol=0)
    frame["recorded_terminal_class"] = np.where(target, "target", np.where(stop, "stop", "other"))

    dates = sorted(frame["trading_day"].unique().tolist())
    if len(dates) != 21:
        raise SystemExit(f"{spec['arm']} has {len(dates)} trading dates, expected 21")
    meta = {
        "arm": spec["arm"],
        "path": spec["path"],
        "sha256": got_sha,
        "rows": len(frame),
        "columns": sorted(columns),
        "n_columns": len(columns),
        "dates": dates,
        "train_dates": dates[:13],
        "holdout_dates": dates[13:],
        "exact_path_fields_present": sorted(columns.intersection(EXACT_PATH_FIELDS)),
        "ambiguity_fields_present": sorted(columns.intersection(AMBIGUITY_FIELDS)),
        "source_outcome_fields_present": sorted(columns.intersection(SOURCE_OUTCOME_FIELDS)),
    }
    return frame, meta


def load_inputs(protocol: dict[str, Any]) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    frames: dict[str, pd.DataFrame] = {}
    metas: list[dict[str, Any]] = []
    for spec in protocol["inputs"]:
        frame, meta = _read_pool(spec)
        frames[spec["arm"]] = frame
        metas.append(meta)
    all_columns = set.intersection(*(set(m["columns"]) for m in metas))
    required_exact = set(EXACT_PATH_FIELDS)
    required_ambiguity = set(AMBIGUITY_FIELDS)
    contract = {
        "schema": "gtos-session-ck-pool-path-contract-v1",
        "generated_at_utc": _utc_now(),
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "inputs": metas,
        "common_columns": sorted(all_columns),
        "exact_geometry_available": bool(all_columns.intersection(required_exact)),
        "exact_same_bar_frequency_available": bool(
            "same_bar_ambiguity" in all_columns
            or {"target_first_touch_utc", "stop_first_touch_utc"}.issubset(all_columns)
        ),
        "missing_exact_path_alternatives": sorted(required_exact - all_columns),
        "missing_ambiguity_fields": sorted(required_ambiguity - all_columns),
        "omitted_source_outcome_fields": sorted(set(SOURCE_OUTCOME_FIELDS) - all_columns),
        "verdict": "EXACT_REPRICING_NOT_IDENTIFIED_FROM_COMMITTED_POOLS",
        "effect": (
            "CK-1/CK-2 arbitrary-grid cells and CK-3 exact ambiguity frequency cannot be "
            "computed from these committed bytes. The map emits only recorded-geometry exact "
            "values, logical bounds, and explicitly labelled sensitivities."
        ),
        "sidecar_contract": {
            "schema": "gtos-session-ck-ordered-path-sidecar-v1",
            "join_key": ["arm_id", "candidate_id", "decision_time_utc"],
            "row_fields": [
                "arm_id", "candidate_id", "decision_time_utc", "horizon_end_utc",
                "source_sha256", "ordered_path_observations",
            ],
            "observation_fields": ["time_utc", "open", "high", "low", "close"],
            "required_invariants": [
                "one sidecar row per committed pool row",
                "unique join key",
                "strictly increasing observation times",
                "first observation at or after entry decision",
                "last observation at or before the source 120-minute horizon",
                "content-bound source_sha256",
            ],
            "status": "SPECIFIED_NOT_MATERIALIZED",
            "materialization_rule": "Commit the sidecar before rerunning this analyzer; no replay is required if the original ordered path payload still exists.",
        },
    }
    return frames, contract


def _split_masks(frame: pd.DataFrame, meta: dict[str, Any]) -> dict[str, np.ndarray]:
    day = frame["trading_day"].to_numpy(str)
    train = np.isin(day, np.asarray(meta["train_dates"], dtype=str))
    holdout = np.isin(day, np.asarray(meta["holdout_dates"], dtype=str))
    return {"TRAIN": train, "HOLDOUT": holdout, "FULL": np.ones(len(frame), dtype=bool)}


def _mean(values: np.ndarray, mask: np.ndarray) -> float | None:
    subset = values[mask]
    return float(np.mean(subset)) if len(subset) else None


def _bound_metrics(
    lower: np.ndarray, upper: np.ndarray, exact: np.ndarray, masks: dict[str, np.ndarray]
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for split, mask in masks.items():
        n = int(mask.sum())
        lo = _mean(lower, mask)
        hi = _mean(upper, mask)
        out[split] = {
            "n": n,
            "exact_rows": int(np.logical_and(exact, mask).sum()),
            "exact_share": float(np.logical_and(exact, mask).sum() / n) if n else None,
            "mean_net_lower": lo,
            "mean_net_upper": hi,
            "bound_width": (hi - lo) if lo is not None and hi is not None else None,
        }
    return out


def geometry_cell(
    frame: pd.DataFrame, masks: dict[str, np.ndarray], *, target_d: float,
    stop_d: float, orientation: str,
) -> dict[str, Any]:
    cost = frame["cost_r"].to_numpy(float)
    gross = frame["recorded_gross_r"].to_numpy(float)
    g = frame["recorded_target_distance"].to_numpy(float)
    klass = frame["recorded_terminal_class"].to_numpy(str)
    target = klass == "target"
    stop = klass == "stop"

    gross_lower = np.full(len(frame), -1.0, dtype=float)
    gross_upper = np.full(len(frame), target_d / stop_d, dtype=float)
    exact = np.zeros(len(frame), dtype=bool)
    sensitivity_lower = gross_lower.copy()
    sensitivity_upper = gross_upper.copy()
    sensitivity_exact = exact.copy()

    if orientation == "as_declared":
        original = np.isclose(stop_d, 1.0, atol=TOL, rtol=0) & np.isclose(
            g, target_d, atol=TOL, rtol=0
        )
        direct_target = target & (target_d <= g + TOL) & (stop_d >= 1.0 - TOL)
        direct_stop = stop & (target_d >= g - TOL) & (stop_d <= 1.0 + TOL)
        for mask, value in (
            (direct_target, target_d / stop_d),
            (direct_stop, -1.0),
        ):
            gross_lower[mask] = value
            gross_upper[mask] = value
            exact[mask] = True
        gross_lower[original] = gross[original]
        gross_upper[original] = gross[original]
        exact[original] = True
        sensitivity_lower = gross_lower.copy()
        sensitivity_upper = gross_upper.copy()
        sensitivity_exact = exact.copy()
    elif orientation == "inverted":
        mapped_stop = target & (target_d >= 1.0 - TOL) & (stop_d <= g + TOL)
        gross_lower[mapped_stop] = -1.0
        gross_upper[mapped_stop] = -1.0
        exact[mapped_stop] = True

        sensitivity_lower = gross_lower.copy()
        sensitivity_upper = gross_upper.copy()
        sensitivity_exact = exact.copy()
        mapped_target_if_no_ambiguity = (
            stop & (target_d <= 1.0 + TOL) & (stop_d >= g - TOL)
        )
        value = target_d / stop_d
        sensitivity_lower[mapped_target_if_no_ambiguity] = value
        sensitivity_upper[mapped_target_if_no_ambiguity] = value
        sensitivity_exact[mapped_target_if_no_ambiguity] = True
    else:
        raise ValueError(f"unknown orientation {orientation}")

    new_cost = cost / stop_d
    lower = gross_lower - new_cost
    upper = gross_upper - new_cost
    sensitivity_lower = sensitivity_lower - new_cost
    sensitivity_upper = sensitivity_upper - new_cost
    splits = _bound_metrics(lower, upper, exact, masks)
    sensitivity = _bound_metrics(
        sensitivity_lower, sensitivity_upper, sensitivity_exact, masks
    )
    full = splits["FULL"]
    if full["exact_rows"] == full["n"]:
        classification = (
            "EXACT_NET_POSITIVE" if full["mean_net_lower"] > 0
            else "EXACT_NET_NEGATIVE" if full["mean_net_upper"] < 0
            else "EXACT_NET_ZERO"
        )
    elif full["mean_net_lower"] > 0:
        classification = "DEFINITIVELY_NET_POSITIVE"
    elif full["mean_net_upper"] < 0:
        classification = "DEFINITIVELY_NET_NEGATIVE"
    else:
        classification = "NOT_IDENTIFIED"
    return {
        "target_distance_D": target_d,
        "stop_distance_D": stop_d,
        "reward_to_risk": target_d / stop_d,
        "orientation": orientation,
        "classification": classification,
        "splits": splits,
        "inverted_zero_ambiguity_sensitivity": sensitivity if orientation == "inverted" else None,
    }


def _row_metrics(frame: pd.DataFrame, mask: np.ndarray) -> dict[str, Any]:
    n = int(mask.sum())
    if not n:
        return {
            "n": 0, "n_days": 0, "mean_gross_r": None, "mean_net_r": None,
            "gross_sum_r": 0.0, "net_sum_r": 0.0, "day_positive_share_gross": None,
        }
    gross = frame.loc[mask, "recorded_gross_r"].to_numpy(float)
    net = frame.loc[mask, "opportunity_net_proxy_r"].to_numpy(float)
    days = frame.loc[mask, "trading_day"].to_numpy(str)
    day_sums = pd.Series(gross).groupby(days).sum()
    return {
        "n": n,
        "n_days": int(day_sums.size),
        "mean_gross_r": float(np.mean(gross)),
        "mean_net_r": float(np.mean(net)),
        "gross_sum_r": float(np.sum(gross)),
        "net_sum_r": float(np.sum(net)),
        "day_positive_share_gross": float((day_sums > 0).mean()) if len(day_sums) else None,
    }


def _pool_summary(frame: pd.DataFrame, masks: dict[str, np.ndarray]) -> dict[str, Any]:
    terminal_counts = frame["recorded_terminal_class"].value_counts().to_dict()
    g = frame["recorded_target_distance"].to_numpy(float)
    return {
        "splits": {name: _row_metrics(frame, mask) for name, mask in masks.items()},
        "terminal_counts": {str(k): int(v) for k, v in sorted(terminal_counts.items())},
        "recorded_target_distance": {
            "min": float(np.min(g)), "max": float(np.max(g)),
            "unique_rounded_9dp": sorted({round(float(v), 9) for v in g}),
        },
        "policy_target_vs_price_geometry_mismatch_rows": int((
            ~np.isclose(g, frame["policy_target_r"].to_numpy(float), atol=TOL, rtol=0)
        ).sum()),
    }


def _ambiguity_bounds(frame: pd.DataFrame) -> dict[str, Any]:
    klass = frame["recorded_terminal_class"].to_numpy(str)
    possible = klass == "stop"
    n = len(frame)
    target_r = frame["policy_target_r"].to_numpy(float)
    max_gain = float(np.sum((target_r[possible] + 1.0)) / n)
    gross_mean = float(frame["recorded_gross_r"].mean())
    return {
        "n_rows": n,
        "exact_frequency_available": False,
        "possible_ambiguous_rows_lower": 0,
        "possible_ambiguous_rows_upper": int(possible.sum()),
        "frequency_lower": 0.0,
        "frequency_upper": float(possible.mean()),
        "worst_case_gross_improvement_r_per_row": max_gain,
        "recorded_gross_r_per_row": gross_mean,
        "could_worst_case_cover_recorded_gross_deficit": bool(gross_mean + max_gain >= 0),
        "interpretation": (
            "The exact frequency is absent. Every ambiguity is hidden among conservative "
            "stop terminals, so zero through all recorded stops are the identified bounds."
        ),
    }


def _endpoint_direction(frame: pd.DataFrame) -> dict[str, Any]:
    klass = frame["recorded_terminal_class"].to_numpy(str)
    binary = np.isin(klass, ["target", "stop"])
    source_target = klass[binary] == "target"
    g = frame.loc[binary, "recorded_target_distance"].to_numpy(float)
    cost = frame.loc[binary, "cost_r"].to_numpy(float)
    source_gross = frame.loc[binary, "recorded_gross_r"].to_numpy(float)
    source_net = frame.loc[binary, "opportunity_net_proxy_r"].to_numpy(float)
    inverted_gross_zero_ambiguity = np.where(source_target, -1.0, 1.0 / g)
    inverted_net_zero_ambiguity = inverted_gross_zero_ambiguity - cost / g
    inverted_net_all_stops_ambiguous = np.full(len(g), -1.0) - cost / g
    stop_gain = (1.0 + 1.0 / g)[~source_target]
    base_total = float(np.sum(inverted_net_all_stops_ambiguous))
    ordinary_share_needed = (
        float(-base_total / np.sum(stop_gain)) if np.sum(stop_gain) > 0 else None
    )
    return {
        "cut": "recorded_terminal_class in {target, stop}; declared before outcomes",
        "n": int(binary.sum()),
        "coverage": float(binary.mean()),
        "source_target_rows": int(source_target.sum()),
        "source_stop_rows": int((~source_target).sum()),
        "source_target_rate": float(source_target.mean()),
        "source_mean_gross_r": float(np.mean(source_gross)),
        "source_mean_net_r": float(np.mean(source_net)),
        "inverted_zero_ambiguity_mean_gross_r": float(np.mean(inverted_gross_zero_ambiguity)),
        "inverted_zero_ambiguity_mean_net_r": float(np.mean(inverted_net_zero_ambiguity)),
        "inverted_all_source_stops_ambiguous_mean_net_r": float(
            np.mean(inverted_net_all_stops_ambiguous)
        ),
        "source_stop_ordinary_share_needed_for_inverted_net_positive": ordinary_share_needed,
        "inverted_net_positive_possible_even_at_zero_ambiguity": bool(
            ordinary_share_needed is not None and ordinary_share_needed < 1.0
        ),
        "source_stop_ambiguity_share_ceiling_for_inverted_net_positive": (
            max(0.0, 1.0 - ordinary_share_needed)
            if ordinary_share_needed is not None and ordinary_share_needed < 1.0 else None
        ),
        "status": "SENSITIVITY_NOT_FULL_POOL_VERDICT",
    }


def _loss_contribution(frame: pd.DataFrame, mask: np.ndarray) -> float | None:
    gross = frame["recorded_gross_r"].to_numpy(float)
    denom = float(np.sum(gross[gross < 0]))
    return float(np.sum(gross[mask]) / denom) if denom else None


def _cell_metrics(
    frames: dict[str, pd.DataFrame], metas: dict[str, dict[str, Any]],
    predicates: dict[str, np.ndarray],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for arm, frame in frames.items():
        mask = predicates[arm]
        splits = _split_masks(frame, metas[arm])
        out[arm] = {
            name: _row_metrics(frame, np.logical_and(mask, split_mask))
            for name, split_mask in splits.items()
        }
        out[arm]["FULL"]["loss_contribution_vs_all_negative_gross"] = _loss_contribution(
            frame, mask
        )
        out[arm]["FULL"]["row_share"] = float(mask.mean())
    return out


def _axis_null(
    frame: pd.DataFrame, meta: dict[str, Any], axis: str, labels_all: np.ndarray,
    eligible: list[str], rng: np.random.Generator, permutations: int,
) -> dict[str, Any]:
    masks = _split_masks(frame, meta)
    train = masks["TRAIN"]
    holdout = masks["HOLDOUT"]
    labels = labels_all[train]
    outcomes = frame.loc[train, "recorded_gross_r"].to_numpy(float)
    days = frame.loc[train, "trading_day"].to_numpy(str)
    baseline = float(np.mean(outcomes))
    levels = sorted(set(labels.tolist()))
    lookup = {level: i for i, level in enumerate(levels)}
    codes = np.asarray([lookup[v] for v in labels], dtype=np.int32)
    counts = np.bincount(codes, minlength=len(levels))
    eligible_codes = np.asarray([lookup[v] for v in eligible if v in lookup], dtype=np.int32)
    if len(eligible_codes) < 2:
        return {
            "axis": axis, "status": "NOT_EVALUABLE", "reason": "fewer than two eligible levels",
            "eligible_levels": eligible, "permutations": 0,
        }
    sums = np.bincount(codes, weights=outcomes, minlength=len(levels))
    means = sums / counts
    lifts = means[eligible_codes] - baseline
    winner_pos = int(np.argmax(np.abs(lifts)))
    driver_code = int(eligible_codes[winner_pos])
    driver = levels[driver_code]
    observed = float(abs(lifts[winner_pos]))

    day_indices = [np.flatnonzero(days == day) for day in sorted(set(days.tolist()))]
    null = np.empty(permutations, dtype=float)
    shuffled = codes.copy()
    for i in range(permutations):
        for idx in day_indices:
            shuffled[idx] = rng.permutation(codes[idx])
        perm_sums = np.bincount(shuffled, weights=outcomes, minlength=len(levels))
        perm_means = perm_sums / counts
        null[i] = float(np.max(np.abs(perm_means[eligible_codes] - baseline)))
    p = float((1 + np.count_nonzero(null >= observed)) / (permutations + 1))

    train_y = frame.loc[train, "recorded_gross_r"].to_numpy(float)
    holdout_y = frame.loc[holdout, "recorded_gross_r"].to_numpy(float)
    holdout_baseline = float(np.mean(holdout_y))
    level_tests = []
    for code in eligible_codes:
        level = levels[int(code)]
        level_train = labels_all[train] == level
        level_holdout = labels_all[holdout] == level
        level_train_lift = float(np.mean(train_y[level_train]) - baseline)
        level_holdout_lift = (
            float(np.mean(holdout_y[level_holdout]) - holdout_baseline)
            if level_holdout.any() else None
        )
        level_tests.append({
            "level": level,
            "train_lift": level_train_lift,
            "holdout_lift": level_holdout_lift,
            "train_row_share": float(level_train.mean()),
            "familywise_maxT_p": float(
                (1 + np.count_nonzero(null >= abs(level_train_lift)))
                / (permutations + 1)
            ),
        })

    driver_train = labels_all[train] == driver
    driver_holdout = labels_all[holdout] == driver
    train_lift = float(np.mean(train_y[driver_train]) - baseline)
    holdout_lift = (
        float(np.mean(holdout_y[driver_holdout]) - holdout_baseline)
        if driver_holdout.any() else None
    )
    driver_share = float(driver_train.mean())
    concentrated = bool(p <= 0.05 and observed >= 0.10 and driver_share >= 0.05)
    persistent = bool(
        concentrated and holdout_lift is not None
        and np.sign(holdout_lift) == np.sign(train_lift)
        and abs(holdout_lift) >= 0.5 * abs(train_lift)
    )
    return {
        "axis": axis,
        "status": "EVALUATED",
        "eligible_levels": eligible,
        "observed_max_abs_lift": observed,
        "driver_level": driver,
        "driver_train_lift": train_lift,
        "driver_holdout_lift": holdout_lift,
        "driver_train_row_share": driver_share,
        "permutations": permutations,
        "empirical_p": p,
        "null_mean": float(np.mean(null)),
        "null_sd": float(np.std(null, ddof=1)),
        "null_q95": float(np.quantile(null, 0.95)),
        "null_max": float(np.max(null)),
        "level_familywise_tests": level_tests,
        "concentrated": concentrated,
        "persistent": persistent,
    }


def taxonomy_map(
    frames: dict[str, pd.DataFrame], metas: dict[str, dict[str, Any]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    primary_arm = protocol["primary_arm"]
    primary = frames[primary_arm]
    primary_masks = _split_masks(primary, metas[primary_arm])
    train = primary_masks["TRAIN"]
    holdout = primary_masks["HOLDOUT"]
    declared_axes = protocol["taxonomy"]["categorical_axes"] + protocol["taxonomy"]["context_control_axes"]
    absent = [axis for axis in declared_axes if axis not in primary.columns]
    if absent:
        raise SystemExit(f"declared taxonomy columns absent: {absent}")

    signature_owner: dict[str, str] = {}
    aliases: dict[str, list[str]] = defaultdict(list)
    canonical_axes: list[str] = []
    for axis in declared_axes:
        sig = _partition_signature(primary.loc[train, axis])
        if sig in signature_owner:
            aliases[signature_owner[sig]].append(axis)
        else:
            signature_owner[sig] = axis
            aliases[axis] = []
            canonical_axes.append(axis)

    cells: list[dict[str, Any]] = []
    axis_eligible: dict[str, list[str]] = {}
    null_targets: list[tuple[str, np.ndarray, list[str]]] = []
    for axis in canonical_axes:
        all_values = sorted(set().union(*(
            set(_normal_series(frame[axis]).tolist()) for frame in frames.values()
        )))
        eligible: list[str] = []
        for level in all_values:
            n_train = int((_normal_series(primary.loc[train, axis]) == level).sum())
            n_holdout = int((_normal_series(primary.loc[holdout, axis]) == level).sum())
            is_eligible = n_train >= 200 and n_holdout >= 100
            if is_eligible:
                eligible.append(level)
            predicates = {
                arm: (_normal_series(frame[axis]).to_numpy(str) == level)
                for arm, frame in frames.items()
            }
            cell = {
                "kind": "level",
                "axis": axis,
                "aliases": aliases[axis],
                "level": level,
                "cell_id": f"{axis}=={level}",
                "rank_eligible": is_eligible,
                "primary_train_n": n_train,
                "primary_holdout_n": n_holdout,
                "per_arm": _cell_metrics(frames, metas, predicates),
            }
            cells.append(cell)
        axis_eligible[axis] = eligible
        null_targets.append((axis, _normal_series(primary[axis]).to_numpy(str), eligible))

    for left, right in protocol["taxonomy"]["interactions"]:
        if left not in primary.columns or right not in primary.columns:
            raise SystemExit(f"declared interaction fields absent: {left}, {right}")
        left_values = _normal_series(primary[left]).to_numpy(str)
        right_values = _normal_series(primary[right]).to_numpy(str)
        pair_labels = np.asarray(
            [f"{left}=={lv} && {right}=={rv}" for lv, rv in zip(left_values, right_values)],
            dtype=str,
        )
        pairs = sorted(set(zip(left_values[train], right_values[train])))
        eligible_interaction_levels: list[str] = []
        for lv, rv in pairs:
            primary_pred = (left_values == lv) & (right_values == rv)
            n_train = int(np.logical_and(primary_pred, train).sum())
            n_holdout = int(np.logical_and(primary_pred, holdout).sum())
            if n_train < 200 or n_holdout < 100:
                continue
            eligible_interaction_levels.append(
                f"{left}=={lv} && {right}=={rv}"
            )
            predicates = {}
            for arm, frame in frames.items():
                predicates[arm] = (
                    (_normal_series(frame[left]).to_numpy(str) == lv)
                    & (_normal_series(frame[right]).to_numpy(str) == rv)
                )
            cells.append({
                "kind": "interaction",
                "axis": f"{left}__X__{right}",
                "left_axis": left, "left_level": lv,
                "right_axis": right, "right_level": rv,
                "cell_id": f"{left}=={lv} && {right}=={rv}",
                "rank_eligible": True,
                "primary_train_n": n_train,
                "primary_holdout_n": n_holdout,
                "per_arm": _cell_metrics(frames, metas, predicates),
            })
        null_targets.append((
            f"{left}__X__{right}", pair_labels, eligible_interaction_levels
        ))

    eligible_cells = [c for c in cells if c["rank_eligible"]]
    ranked = sorted(
        eligible_cells,
        key=lambda c: c["per_arm"][primary_arm]["TRAIN"]["mean_gross_r"],
        reverse=True,
    )
    rng = np.random.default_rng(int(protocol["concentration_null"]["seed"]))
    nulls = []
    for axis, labels, eligible in null_targets:
        nulls.append(_axis_null(
            primary, metas[primary_arm], axis, labels, eligible, rng,
            int(protocol["concentration_null"]["permutations"]),
        ))

    negative_both = sum(
        c["per_arm"][primary_arm]["TRAIN"]["mean_gross_r"] < 0
        and c["per_arm"][primary_arm]["HOLDOUT"]["mean_gross_r"] < 0
        for c in eligible_cells
    )
    negative_both_share = negative_both / len(eligible_cells) if eligible_cells else 0.0
    persistent_axes = [n["axis"] for n in nulls if n.get("persistent")]
    if persistent_axes:
        loss_shape = "CONCENTRATED_AND_PERSISTENT"
    elif negative_both_share >= 0.90:
        loss_shape = "UNIFORM_BY_PREDECLARED_RULE"
    else:
        loss_shape = "MIXED"
    return {
        "primary_arm": primary_arm,
        "canonical_axes": canonical_axes,
        "alias_groups": dict(aliases),
        "cells": cells,
        "ranked_eligible_cell_ids": [c["cell_id"] for c in ranked],
        "top_20": [
            {
                "rank": i + 1,
                "cell_id": c["cell_id"],
                "kind": c["kind"],
                "train": c["per_arm"][primary_arm]["TRAIN"],
                "holdout": c["per_arm"][primary_arm]["HOLDOUT"],
                "full": c["per_arm"][primary_arm]["FULL"],
            }
            for i, c in enumerate(ranked[:20])
        ],
        "eligible_cells": len(eligible_cells),
        "eligible_gross_positive_train": sum(
            c["per_arm"][primary_arm]["TRAIN"]["mean_gross_r"] > 0 for c in eligible_cells
        ),
        "eligible_gross_positive_both_train_holdout": sum(
            c["per_arm"][primary_arm]["TRAIN"]["mean_gross_r"] > 0
            and c["per_arm"][primary_arm]["HOLDOUT"]["mean_gross_r"] > 0
            for c in eligible_cells
        ),
        "eligible_negative_both": negative_both,
        "eligible_negative_both_share": negative_both_share,
        "concentration_nulls": nulls,
        "persistent_concentrated_axes": persistent_axes,
        "loss_shape": loss_shape,
    }


def build_map(
    frames: dict[str, pd.DataFrame], contract: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, Any]:
    metas = {m["arm"]: m for m in contract["inputs"]}
    target_grid = [float(x) for x in protocol["geometry"]["target_distance_in_D"]]
    stop_grid = [float(x) for x in protocol["geometry"]["stop_distance_in_D"]]
    geometry: list[dict[str, Any]] = []
    arm_summaries: dict[str, Any] = {}
    ambiguity: dict[str, Any] = {}
    endpoint_direction: dict[str, Any] = {}
    for arm, frame in frames.items():
        masks = _split_masks(frame, metas[arm])
        arm_summaries[arm] = _pool_summary(frame, masks)
        ambiguity[arm] = _ambiguity_bounds(frame)
        endpoint_direction[arm] = _endpoint_direction(frame)
        for orientation in protocol["geometry"]["orientations"]:
            for target_d in target_grid:
                for stop_d in stop_grid:
                    row = geometry_cell(
                        frame, masks, target_d=target_d, stop_d=stop_d,
                        orientation=orientation,
                    )
                    row["arm"] = arm
                    geometry.append(row)

    best: dict[str, Any] = {}
    for arm in frames:
        best[arm] = {}
        for orientation in protocol["geometry"]["orientations"]:
            subset = [g for g in geometry if g["arm"] == arm and g["orientation"] == orientation]
            exact = [g for g in subset if g["splits"]["FULL"]["exact_rows"] == g["splits"]["FULL"]["n"]]
            best[arm][orientation] = {
                "exact_cells": len(exact),
                "exact_net_positive_cells": sum(
                    g["classification"] == "EXACT_NET_POSITIVE" for g in exact
                ),
                "best_exact": max(
                    exact, key=lambda g: g["splits"]["FULL"]["mean_net_lower"], default=None
                ),
                "best_lower_bound": max(
                    subset, key=lambda g: g["splits"]["FULL"]["mean_net_lower"]
                ),
                "best_upper_bound": max(
                    subset, key=lambda g: g["splits"]["FULL"]["mean_net_upper"]
                ),
                "definitively_net_positive_cells": sum(
                    g["classification"] == "DEFINITIVELY_NET_POSITIVE" for g in subset
                ),
                "definitively_net_negative_cells": sum(
                    g["classification"] == "DEFINITIVELY_NET_NEGATIVE" for g in subset
                ),
                "not_identified_cells": sum(g["classification"] == "NOT_IDENTIFIED" for g in subset),
            }

    taxonomy = taxonomy_map(frames, metas, protocol)
    return {
        "schema": "gtos-session-ck-mechanism-map-v1",
        "generated_at_utc": _utc_now(),
        "source_head": _repo_head(),
        "protocol": str(PROTOCOL.relative_to(REPO)),
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "surface": "VAL",
        "billed": False,
        "graduation": "NONE_FILE_ONLY",
        "march_2026": "OUTCOME_UNREAD",
        "replay_runs": 0,
        "path_contract_verdict": contract["verdict"],
        "arm_summaries": arm_summaries,
        "geometry": geometry,
        "geometry_summary": best,
        "first_touch_ambiguity_bounds": ambiguity,
        "binary_endpoint_direction_diagnostic": endpoint_direction,
        "taxonomy": taxonomy,
    }


def _look_id(kind: str, spec: dict[str, Any]) -> str:
    return _sha_obj({"session": "CK", "kind": kind, "spec": spec})[:20]


def make_looks(
    result: dict[str, Any], contract: dict[str, Any], protocol: dict[str, Any]
) -> list[dict[str, Any]]:
    dates = {m["arm"]: m["dates"] for m in contract["inputs"]}
    looks: list[dict[str, Any]] = []

    def add(
        kind: str, arm: str, spec: dict[str, Any], verdict: str, metric: float | None,
        metric_name: str, note: str, extra: dict[str, Any], receipt: Path = MAP_OUT,
    ) -> None:
        full_spec = {"kind": kind, "arm": arm, **spec}
        looks.append({
            "look_id": _look_id(kind, full_spec),
            "kind": kind,
            "arm": arm,
            "spec": full_spec,
            "verdict": verdict,
            "metric": metric,
            "metric_name": metric_name,
            "note": note,
            "extra": extra,
            "days": dates[arm],
            "receipt": str(receipt.relative_to(REPO)),
        })

    primary = protocol["primary_arm"]
    add(
        "path_contract", primary, {"protocol_sha256": EXPECTED_PROTOCOL_SHA256},
        "not_evaluable", None, "", contract["verdict"],
        {"missing_exact_path_alternatives": contract["missing_exact_path_alternatives"],
         "missing_ambiguity_fields": contract["missing_ambiguity_fields"]}, CONTRACT_OUT,
    )
    for cell in result["geometry"]:
        full = cell["splits"]["FULL"]
        identified = cell["classification"] != "NOT_IDENTIFIED"
        add(
            "geometry", cell["arm"],
            {"orientation": cell["orientation"], "target_distance_D": cell["target_distance_D"],
             "stop_distance_D": cell["stop_distance_D"]},
            "evaluated" if identified else "not_evaluable",
            full["mean_net_lower"], "mean_net_lower_bound",
            cell["classification"],
            {"classification": cell["classification"], "splits": cell["splits"],
             "zero_ambiguity_sensitivity": cell["inverted_zero_ambiguity_sensitivity"]},
        )
    for arm, row in result["first_touch_ambiguity_bounds"].items():
        add(
            "first_touch_ambiguity", arm, {"rule": "committed_pool_identified_bound"},
            "not_evaluable", row["frequency_upper"], "ambiguity_frequency_upper_bound",
            "exact frequency omitted by compact-pool projection",
            row,
        )
    for arm, row in result["binary_endpoint_direction_diagnostic"].items():
        add(
            "binary_endpoint_direction", arm,
            {"cut": "recorded_terminal_class in {target,stop}",
             "mirror": "target_distance=1; stop_distance=recorded_G"},
            "evaluated", row["inverted_zero_ambiguity_mean_net_r"],
            "conditional_inverted_net_r_per_binary_row",
            row["status"], row,
        )

    for cell in result["taxonomy"]["cells"]:
        for arm, metrics in cell["per_arm"].items():
            eligible = bool(cell["rank_eligible"])
            add(
                "taxonomy", arm,
                {"cell_id": cell["cell_id"], "cell_kind": cell["kind"]},
                "evaluated" if eligible else "not_evaluable",
                metrics["TRAIN"]["mean_gross_r"], "train_mean_gross_r",
                "rank eligible" if eligible else "below predeclared rank floor",
                {"rank_eligible": eligible, "metrics": metrics},
            )
    for null in result["taxonomy"]["concentration_nulls"]:
        add(
            "taxonomy_concentration_null", primary, {"axis": null["axis"]},
            "evaluated" if null["status"] == "EVALUATED" else "not_evaluable",
            null.get("empirical_p"), "within_day_permutation_empirical_p",
            null["status"], null,
        )
    ids = [look["look_id"] for look in looks]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate Session CK look ids")
    return looks


def log_looks(looks: list[dict[str, Any]]) -> dict[str, Any]:
    before_rows = read_rows(DEFAULT_ITERATION_LEDGER)
    existing = {
        str(row.get("extra", {}).get("look_id"))
        for row in before_rows
        if row.get("session") == "CK" and isinstance(row.get("extra"), dict)
    }
    ledger = IterationLedger(DEFAULT_ITERATION_LEDGER, session="CK", run_id=RUN_ID)
    written: list[str] = []
    skipped: list[str] = []
    for look in looks:
        if look["look_id"] in existing:
            skipped.append(look["look_id"])
            continue
        mechanism = {
            "geometry": "b7_5_geometry",
            "path_contract": "b7_5_path_contract",
            "first_touch_ambiguity": "b7_5_first_touch_bias",
            "binary_endpoint_direction": "b7_5_direction",
            "taxonomy": "b7_5_entry_taxonomy",
            "taxonomy_concentration_null": "b7_5_taxonomy_null",
        }[look["kind"]]
        ledger.record(
            mechanism=mechanism,
            sleeve=look["arm"],
            spec=look["spec"],
            days=look["days"],
            engine_version=ENGINE_VERSION,
            verdict=look["verdict"],
            metric=look["metric"],
            metric_name=look["metric_name"],
            note=look["note"],
            receipt=look["receipt"],
            extra={"look_id": look["look_id"], **look["extra"]},
        )
        written.append(look["look_id"])
        existing.add(look["look_id"])
    after_rows = read_rows(DEFAULT_ITERATION_LEDGER)
    ck_rows = [r for r in after_rows if r.get("session") == "CK"]
    return {
        "schema": "gtos-session-ck-look-ledger-receipt-v1",
        "generated_at_utc": _utc_now(),
        "ledger": str(Path(DEFAULT_ITERATION_LEDGER).relative_to(REPO)),
        "ledger_sha256": _sha256_file(Path(DEFAULT_ITERATION_LEDGER)),
        "expected_looks": len(looks),
        "written_this_run": len(written),
        "idempotently_skipped": len(skipped),
        "session_ck_rows_after": len(ck_rows),
        "all_expected_present": all(
            look["look_id"] in {
                str(r.get("extra", {}).get("look_id")) for r in ck_rows
                if isinstance(r.get("extra"), dict)
            }
            for look in looks
        ),
        "surface_counts": dict(pd.Series([r.get("surface") for r in ck_rows]).value_counts()),
        "billed_true_rows": sum(bool(r.get("billed")) for r in ck_rows),
        "march_rows": sum(
            any(str(day).startswith("2026-03") for day in r.get("surface_stamp", {}).get("test_days", []))
            for r in ck_rows
        ),
        "written_look_ids": written,
    }


def run(*, commit_looks: bool) -> dict[str, Any]:
    protocol = load_protocol()
    frames, contract = load_inputs(protocol)
    contract = _write_sealed(CONTRACT_OUT, contract)
    result = _write_sealed(MAP_OUT, build_map(frames, contract, protocol))
    looks = make_looks(result, contract, protocol)
    manifest = _write_sealed(LOOK_MANIFEST_OUT, {
        "schema": "gtos-session-ck-look-manifest-v1",
        "generated_at_utc": _utc_now(),
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "n_looks": len(looks),
        "looks": looks,
    })
    ledger_receipt = None
    if commit_looks:
        ledger_receipt = _write_sealed(LOOK_RECEIPT_OUT, log_looks(looks))
        if not ledger_receipt["all_expected_present"]:
            raise SystemExit("not all Session CK looks landed in the canonical iteration ledger")
        if ledger_receipt["billed_true_rows"] or ledger_receipt["march_rows"]:
            raise SystemExit("Session CK ledger invariant failed")
    return {
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "contract_verdict": contract["verdict"],
        "map": str(MAP_OUT.relative_to(REPO)),
        "map_sha256": result["self_sha256"],
        "look_manifest_sha256": manifest["self_sha256"],
        "n_looks": len(looks),
        "logged": ledger_receipt is not None,
        "ledger_receipt_sha256": ledger_receipt["self_sha256"] if ledger_receipt else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--commit-looks", action="store_true",
        help="append every look to the canonical iteration ledger (idempotent)",
    )
    args = parser.parse_args()
    print(json.dumps(run(commit_looks=args.commit_looks), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
