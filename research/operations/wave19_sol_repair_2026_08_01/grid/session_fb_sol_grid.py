#!/usr/bin/env python3
"""Session FB full-family geometry and mechanism analyzer.

The January command authenticates and streams the committed CQ path sidecar,
strengthens its join to the full candidate/time/symbol/side composite, and then
evaluates the preregistered 198-cell grid over every denominator-eligible family
stratum.  The February command is deliberately separate: it refuses to run until
the January outputs exist and uses February only for frozen attribution
corroboration.  Neither command imports broker modules, mutates the iteration
ledger, launches replay, or reads March/live-forward outcomes.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


REPO = Path(__file__).resolve().parents[4]
GRID_DIR = Path(__file__).resolve().parent
PROTOCOL = GRID_DIR / "GRID_PROTOCOL.json"
CQ_TOOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase18/receipts/"
    "cq_path_pool_grid.py"
)


def _load_cq() -> Any:
    spec = importlib.util.spec_from_file_location("session_fb_cq_path_pool_grid", CQ_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_load_cq_tool:{CQ_TOOL}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


cq = _load_cq()

GRID_RESULTS = GRID_DIR / "GRID_FULL_RESULTS.json"
CLASSIFICATION = GRID_DIR / "FAMILY_CLASSIFICATION.json"
GROSS_DECOMP = GRID_DIR / "GROSS_DECOMP.json"
BREAKER = GRID_DIR / "BREAKER_REDERIVATION.json"
FEB_CORROBORATION = GRID_DIR / "FEB_CORROBORATION.json"
LOOK_MANIFEST = GRID_DIR / "LOOK_MANIFEST.json"

GRID_SCHEMA = "gtos.session_fb.sol_full_family_grid_results.v1"
CLASSIFICATION_SCHEMA = "gtos.session_fb.family_classification.v1"
GROSS_SCHEMA = "gtos.session_fb.gross_decomposition.v1"
BREAKER_SCHEMA = "gtos.session_fb.breaker_rederivation.v1"
FEB_SCHEMA = "gtos.session_fb.february_corroboration.v1"
LOOK_SCHEMA = "gtos.session_fb.look_manifest.v1"

SURFACE = "FORENSIC_DIAGNOSTIC"
FEB_LABEL = "owner_mandate_20260801"
PASS_ACTIONS = {"trade", "open-reduced-risk", "reduce-risk"}
TOL = 1e-9


class FBRefusal(RuntimeError):
    """Fail-closed evidence, boundary, or accounting violation."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).isoformat()


def repo_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO.resolve()).as_posix()


def write_json(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    return cq._write_rooted_json(path, payload)


def validate_rooted_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = payload.pop("self_sha256", None)
    actual = canonical_sha256(payload)
    if expected != actual:
        raise FBRefusal(f"rooted_json_hash_invalid:{path}:{actual}!={expected}")
    payload["self_sha256"] = expected
    return payload


def load_protocol() -> dict[str, Any]:
    payload = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if payload.get("schema") != "gtos.session_fb.sol_full_family_grid_protocol.v1":
        raise FBRefusal("grid_protocol_schema_invalid")
    boundary = payload.get("evidence_boundary") or {}
    if (
        boundary.get("march_2026_outcomes") != "UNREAD_AND_FORBIDDEN"
        or boundary.get("live_forward_outcomes") != "UNREAD_AND_FORBIDDEN"
        or boundary.get("billed") is not False
    ):
        raise FBRefusal("grid_protocol_boundary_invalid")
    geometry = payload.get("geometry") or {}
    if (
        len(geometry.get("target_distance_in_D") or []) != 11
        or len(geometry.get("stop_distance_in_D") or []) != 9
        or geometry.get("orientations") != ["as_declared", "inverted"]
    ):
        raise FBRefusal("grid_protocol_geometry_invalid")
    return payload


def resolve_input(spec: Mapping[str, Any]) -> Path:
    path = Path(str(spec["path"]))
    return path if path.is_absolute() else REPO / path


def verify_bound_file(spec: Mapping[str, Any], *, key: str) -> Path:
    path = resolve_input(spec)
    if not path.is_file():
        raise FBRefusal(f"bound_input_missing:{key}:{path}")
    actual = sha256_file(path)
    if actual != spec.get("sha256"):
        raise FBRefusal(f"bound_input_drift:{key}:{actual}!={spec.get('sha256')}")
    return path


def normalize_side(row: Mapping[str, Any]) -> str:
    seen = []
    for field in ("side", "direction"):
        value = str(row.get(field) or "").strip().upper()
        if value:
            seen.append(value)
    if not seen or any(value not in {"LONG", "SHORT"} for value in seen):
        raise FBRefusal(f"side_or_direction_invalid:{seen}")
    if len(set(seen)) != 1:
        raise FBRefusal(f"side_direction_disagreement:{seen}")
    return seen[0]


def normalized_utc(value: Any) -> str:
    return cq._iso(cq._parse_utc(value))


def composite_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    candidate_id = str(row.get("candidate_id") or "")
    symbol = str(row.get("symbol") or "")
    if not candidate_id or not symbol:
        raise FBRefusal("composite_key_missing_candidate_or_symbol")
    return (
        candidate_id,
        normalized_utc(row.get("decision_time_utc")),
        symbol,
        normalize_side(row),
    )


def validate_composite_sidecar(
    pool_rows: Sequence[Mapping[str, Any]], sidecar_path: Path
) -> dict[str, Any]:
    """Prove the stronger Session-FB join while retaining CQ's row ordering."""

    pool_keys = [composite_key(row) for row in pool_rows]
    if len(pool_keys) != len(set(pool_keys)):
        raise FBRefusal("january_pool_composite_key_not_unique")
    candidate_counts = Counter(key[0] for key in pool_keys)
    sidecar_keys: set[tuple[str, str, str, str]] = set()
    sidecar_rows = 0
    with gzip.open(sidecar_path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("arm_id") != "S0R0":
                raise FBRefusal(f"sidecar_arm_invalid:{line_number}")
            key = composite_key(row)
            if key in sidecar_keys:
                raise FBRefusal(f"sidecar_composite_key_duplicate:{line_number}:{key}")
            if sidecar_rows >= len(pool_keys):
                raise FBRefusal("sidecar_has_more_rows_than_pool")
            if key != pool_keys[sidecar_rows]:
                raise FBRefusal(
                    f"sidecar_composite_alignment_mismatch:{line_number}:{key}!={pool_keys[sidecar_rows]}"
                )
            sidecar_keys.add(key)
            sidecar_rows += 1
    if sidecar_rows != len(pool_keys) or sidecar_keys != set(pool_keys):
        raise FBRefusal(
            f"sidecar_composite_coverage_mismatch:{sidecar_rows}!={len(pool_keys)}"
        )
    duplicate_ids = {key: count for key, count in candidate_counts.items() if count > 1}
    return {
        "normalized_key_fields": [
            "candidate_id",
            "decision_time_utc_as_utc_iso",
            "symbol",
            "side_or_direction_upper",
        ],
        "pool_rows": len(pool_keys),
        "pool_unique_composite_keys": len(set(pool_keys)),
        "sidecar_rows": sidecar_rows,
        "sidecar_unique_composite_keys": len(sidecar_keys),
        "aligned_in_pool_order": True,
        "key_sets_identical": True,
        "candidate_ids_with_multiplicity": len(duplicate_ids),
        "rows_whose_candidate_id_is_not_unique": sum(duplicate_ids.values()),
        "candidate_id_duplicate_excess_rows": sum(
            count - 1 for count in duplicate_ids.values()
        ),
        "candidate_id_alone_used_as_join": False,
    }


def iter_gzip_json(path: Path) -> Iterable[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise FBRefusal(f"invalid_jsonl:{path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise FBRefusal(f"non_object_jsonl:{path}:{line_number}")
            yield row


def recorded_arrays(rows: Sequence[Mapping[str, Any]]) -> dict[str, np.ndarray]:
    net = np.asarray([float(row["opportunity_net_proxy_r"]) for row in rows])
    cost = np.asarray([float(row["cost_r"]) for row in rows])
    gross = net + cost
    if not (np.isfinite(net).all() and np.isfinite(cost).all()):
        raise FBRefusal("recorded_economics_nonfinite")
    return {"gross": gross, "cost": cost, "net": net}


def residual_masks(rows: Sequence[Mapping[str, Any]]) -> dict[str, np.ndarray]:
    a = np.asarray(
        [
            row.get("broker_pretrade_cost_executable") is True
            and str(row.get("selector_action") or "") in PASS_ACTIONS
            for row in rows
        ],
        dtype=bool,
    )
    b = np.asarray(
        [
            row.get("scheduler_materialization_status")
            == "scheduler_option_materialized"
            for row in rows
        ],
        dtype=bool,
    )
    return {"A_EXECUTABLE_SELECTOR_PASS": a, "B_SCHEDULER_MATERIALIZED": b}


def economic_metrics(
    arrays: Mapping[str, np.ndarray], mask: np.ndarray, *, total_n: int
) -> dict[str, Any]:
    index = np.flatnonzero(mask)
    n = len(index)
    return {
        "n": n,
        "row_share": n / total_n if total_n else None,
        "gross_sum_r": float(np.sum(arrays["gross"][index])),
        "gross_mean_r": float(np.mean(arrays["gross"][index])) if n else None,
        "cost_sum_r": float(np.sum(arrays["cost"][index])),
        "cost_mean_r": float(np.mean(arrays["cost"][index])) if n else None,
        "net_sum_r": float(np.sum(arrays["net"][index])),
        "net_mean_r": float(np.mean(arrays["net"][index])) if n else None,
        "positive_net_rows": int(np.count_nonzero(arrays["net"][index] > 0)),
        "positive_net_share": float(np.mean(arrays["net"][index] > 0)) if n else None,
    }


def build_populations(
    rows: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray]:
    families = np.asarray([str(row.get("origin_family") or "") for row in rows], dtype="U96")
    directions = np.asarray([normalize_side(row) for row in rows], dtype="U5")
    if np.any(families == ""):
        raise FBRefusal("origin_family_missing")
    family_min = int(protocol["eligibility"]["family_minimum_full_n"])
    interaction_min = int(
        protocol["eligibility"]["family_x_direction_minimum_full_n"]
    )
    populations: list[dict[str, Any]] = []
    for family in sorted(set(families.tolist())):
        mask = families == family
        populations.append(
            {
                "population_id": f"family:{family}",
                "kind": "family",
                "family": family,
                "direction": None,
                "mask": mask,
                "n": int(mask.sum()),
                "minimum_n": family_min,
                "eligible": int(mask.sum()) >= family_min,
            }
        )
        for direction in ("LONG", "SHORT"):
            cell = np.logical_and(mask, directions == direction)
            if not cell.any():
                continue
            populations.append(
                {
                    "population_id": f"family_direction:{family}|{direction}",
                    "kind": "family_direction",
                    "family": family,
                    "direction": direction,
                    "mask": cell,
                    "n": int(cell.sum()),
                    "minimum_n": interaction_min,
                    "eligible": int(cell.sum()) >= interaction_min,
                }
            )
    return populations, families, directions


def census_rows(
    rows: Sequence[Mapping[str, Any]],
    populations: Sequence[Mapping[str, Any]],
    arrays: Mapping[str, np.ndarray],
    residual: Mapping[str, np.ndarray],
) -> list[dict[str, Any]]:
    result = []
    residual_a_n = int(residual["A_EXECUTABLE_SELECTOR_PASS"].sum())
    residual_b_n = int(residual["B_SCHEDULER_MATERIALIZED"].sum())
    for population in populations:
        mask = np.asarray(population["mask"], dtype=bool)
        base = economic_metrics(arrays, mask, total_n=len(rows))
        a_mask = np.logical_and(mask, residual["A_EXECUTABLE_SELECTOR_PASS"])
        b_mask = np.logical_and(mask, residual["B_SCHEDULER_MATERIALIZED"])
        a = economic_metrics(arrays, a_mask, total_n=max(residual_a_n, 1))
        b = economic_metrics(arrays, b_mask, total_n=max(residual_b_n, 1))
        result.append(
            {
                **{key: population[key] for key in (
                    "population_id",
                    "kind",
                    "family",
                    "direction",
                    "n",
                    "minimum_n",
                    "eligible",
                )},
                "full_pool": base,
                "residual_A_executable_selector_pass": a,
                "residual_B_scheduler_materialized": b,
            }
        )
    return result


def geometry_vectors(
    summary: Mapping[str, np.ndarray],
    target_position: int,
    stop_position: int,
    target_d: float,
    stop_d: float,
    costs: np.ndarray,
) -> dict[str, np.ndarray]:
    target_index = summary["target_index"][:, target_position]
    stop_index = summary["stop_index"][:, stop_position]
    target_hit = target_index < stop_index
    stop_hit = stop_index < target_index
    ambiguous = np.logical_and(
        target_index == stop_index, target_index != cq.INF_INDEX
    )
    horizon = np.logical_and(
        target_index == cq.INF_INDEX, stop_index == cq.INF_INDEX
    )
    if not np.all(target_hit | stop_hit | ambiguous | horizon):
        raise FBRefusal("grid_outcome_partition_invalid")
    gross = np.where(
        target_hit,
        target_d / stop_d,
        np.where(
            np.logical_or(stop_hit, ambiguous),
            -1.0,
            summary["terminal_signed_d"] / stop_d,
        ),
    )
    optimistic_gross = np.where(ambiguous, target_d / stop_d, gross)
    net = gross - costs / stop_d
    outcome = np.full(len(gross), "HORIZON", dtype="U12")
    outcome[target_hit] = "TARGET"
    outcome[stop_hit] = "STOP"
    outcome[ambiguous] = "AMBIGUOUS"
    return {
        "gross": gross,
        "optimistic_gross": optimistic_gross,
        "net": net,
        "outcome": outcome,
        "ambiguous": ambiguous,
    }


def cell_verdict(splits: Mapping[str, Mapping[str, Any]]) -> str:
    if splits["TRAIN"]["n"] == 0 or splits["HOLDOUT"]["n"] == 0:
        return "NOT_EVALUABLE_EMPTY_CHRONOLOGICAL_SPLIT"
    return cq._cell_verdict(splits)


def classify_orientation_leaders(
    declared: Mapping[str, Any], inverted: Mapping[str, Any]
) -> str:
    def persistent_net(leader: Mapping[str, Any]) -> bool:
        splits = leader["splits"]
        return (
            float(splits["TRAIN"]["mean_net_r"]) > 0
            and float(splits["HOLDOUT"]["mean_net_r"]) > 0
        )

    def persistent_gross(leader: Mapping[str, Any]) -> bool:
        splits = leader["splits"]
        return (
            float(splits["TRAIN"]["mean_gross_r"]) > 0
            and float(splits["HOLDOUT"]["mean_gross_r"]) > 0
        )

    if persistent_net(declared):
        return "PERSISTENT_AS_DECLARED_REPAIR"
    if persistent_net(inverted):
        return "ANTI_PREDICTIVE_INVERTIBLE"
    if persistent_gross(declared) or persistent_gross(inverted):
        return "GROSS_POSITIVE_COST_KILLED"
    gross_values = [
        float(leader["splits"][split]["mean_gross_r"])
        for leader in (declared, inverted)
        for split in ("TRAIN", "HOLDOUT")
    ]
    if all(value <= 0 for value in gross_values):
        return "DEAD_UNDER_BOTH_ORIENTATIONS"
    return "NOISE"


def make_cell_id(orientation: str, target_d: float, stop_d: float) -> str:
    return f"{orientation}|target_{target_d:g}D|stop_{stop_d:g}D"


def run_grid(
    *,
    rows: Sequence[Mapping[str, Any]],
    populations: Sequence[Mapping[str, Any]],
    masks: Mapping[str, np.ndarray],
    summaries: Mapping[str, Mapping[str, np.ndarray]],
    costs: np.ndarray,
    targets: np.ndarray,
    stops: np.ndarray,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
    eligible = [population for population in populations if population["eligible"]]
    cells: list[dict[str, Any]] = []
    candidates: dict[str, dict[str, list[dict[str, Any]]]] = {
        str(population["population_id"]): {
            "as_declared": [],
            "inverted": [],
        }
        for population in eligible
    }
    for orientation in ("as_declared", "inverted"):
        summary = summaries[orientation]
        for target_position, target_d_raw in enumerate(targets):
            target_d = float(target_d_raw)
            for stop_position, stop_d_raw in enumerate(stops):
                stop_d = float(stop_d_raw)
                vectors = geometry_vectors(
                    summary,
                    target_position,
                    stop_position,
                    target_d,
                    stop_d,
                    costs,
                )
                full_splits = {
                    split: cq._metrics(
                        gross=vectors["gross"],
                        net=vectors["net"],
                        optimistic_gross=vectors["optimistic_gross"],
                        outcome=vectors["outcome"],
                        ambiguous=vectors["ambiguous"],
                        mask=split_mask,
                    )
                    for split, split_mask in masks.items()
                }
                population_results: dict[str, Any] = {}
                cell_id = make_cell_id(orientation, target_d, stop_d)
                for population in eligible:
                    population_id = str(population["population_id"])
                    population_mask = np.asarray(population["mask"], dtype=bool)
                    splits = {
                        split: cq._metrics(
                            gross=vectors["gross"],
                            net=vectors["net"],
                            optimistic_gross=vectors["optimistic_gross"],
                            outcome=vectors["outcome"],
                            ambiguous=vectors["ambiguous"],
                            mask=np.logical_and(split_mask, population_mask),
                        )
                        for split, split_mask in masks.items()
                    }
                    verdict = cell_verdict(splits)
                    population_results[population_id] = {
                        "verdict": verdict,
                        "splits": splits,
                    }
                    candidates[population_id][orientation].append(
                        {
                            "cell_id": cell_id,
                            "orientation": orientation,
                            "target_distance_D": target_d,
                            "stop_distance_D": stop_d,
                            "verdict": verdict,
                            "splits": splits,
                        }
                    )
                cells.append(
                    {
                        "cell_id": cell_id,
                        "surface": SURFACE,
                        "billed": False,
                        "orientation": orientation,
                        "target_distance_D": target_d,
                        "stop_distance_D": stop_d,
                        "reward_to_risk": target_d / stop_d,
                        "same_bar_primary_rule": "conservative_stop",
                        "full_pool": {"splits": full_splits},
                        "populations": population_results,
                    }
                )
    if len(cells) != 198:
        raise FBRefusal(f"grid_cell_count:{len(cells)}!=198")

    leaders: dict[str, dict[str, dict[str, Any]]] = {}
    for population_id, orientations in candidates.items():
        leaders[population_id] = {}
        for orientation, values in orientations.items():
            ranked = sorted(
                values,
                key=lambda cell: (
                    -float(cell["splits"]["TRAIN"]["mean_net_r"]),
                    float(cell["target_distance_D"]),
                    float(cell["stop_distance_D"]),
                    str(cell["cell_id"]),
                ),
            )
            selected = dict(ranked[0])
            selected["selection_rule"] = "TRAIN mean net descending; frozen tie-breaks"
            selected["persistent_net_positive_cells_descriptive"] = sum(
                cell["verdict"] == "PERSISTENT_NET_POSITIVE" for cell in values
            )
            selected["persistent_gross_positive_cost_vetoed_cells_descriptive"] = sum(
                cell["verdict"] == "PERSISTENT_GROSS_POSITIVE_COST_VETOED"
                for cell in values
            )
            leaders[population_id][orientation] = selected
    return cells, leaders


def leader_vector(
    leader: Mapping[str, Any],
    summaries: Mapping[str, Mapping[str, np.ndarray]],
    costs: np.ndarray,
    targets: np.ndarray,
    stops: np.ndarray,
) -> np.ndarray:
    target_position = int(
        np.flatnonzero(targets == float(leader["target_distance_D"]))[0]
    )
    stop_position = int(
        np.flatnonzero(stops == float(leader["stop_distance_D"]))[0]
    )
    return geometry_vectors(
        summaries[str(leader["orientation"])],
        target_position,
        stop_position,
        float(leader["target_distance_D"]),
        float(leader["stop_distance_D"]),
        costs,
    )["net"]


def max_t_control(
    *,
    rows: Sequence[Mapping[str, Any]],
    populations: Sequence[Mapping[str, Any]],
    leaders: Mapping[str, Mapping[str, Mapping[str, Any]]],
    masks: Mapping[str, np.ndarray],
    summaries: Mapping[str, Mapping[str, np.ndarray]],
    costs: np.ndarray,
    targets: np.ndarray,
    stops: np.ndarray,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    population_by_id = {
        str(population["population_id"]): population for population in populations
    }
    candidates: list[dict[str, Any]] = []
    for population_id, by_orientation in leaders.items():
        population = population_by_id[population_id]
        breaker = population["family"] == "current_breaker_re_entry"
        for orientation, leader in by_orientation.items():
            train_positive = float(leader["splits"]["TRAIN"]["mean_net_r"]) > 0
            if breaker or train_positive:
                vector = leader_vector(leader, summaries, costs, targets, stops)
                train = masks["TRAIN"]
                pop_train = np.logical_and(
                    train, np.asarray(population["mask"], dtype=bool)
                )
                baseline = float(np.mean(vector[train]))
                observed = float(np.mean(vector[pop_train]) - baseline)
                candidates.append(
                    {
                        "leader_id": f"{population_id}|{orientation}",
                        "population_id": population_id,
                        "kind": population["kind"],
                        "family": population["family"],
                        "direction": population["direction"],
                        "cell_id": leader["cell_id"],
                        "orientation": orientation,
                        "vector": vector,
                        "baseline_train_mean_net_r": baseline,
                        "observed_population_train_mean_net_r": float(
                            np.mean(vector[pop_train])
                        ),
                        "observed_train_lift_r": observed,
                        "population_train_n": int(pop_train.sum()),
                    }
                )
    if not candidates:
        raise FBRefusal("max_t_has_no_candidate_leaders")

    joint_labels = np.asarray(
        [f"{row['origin_family']}|{normalize_side(row)}" for row in rows], dtype="U110"
    )
    levels = sorted(set(joint_labels.tolist()))
    level_to_code = {level: position for position, level in enumerate(levels)}
    codes = np.asarray([level_to_code[level] for level in joint_labels], dtype=np.int32)
    family_codes: dict[str, np.ndarray] = {}
    for population in populations:
        family = str(population["family"])
        if family not in family_codes:
            family_codes[family] = np.asarray(
                [
                    level_to_code[level]
                    for level in levels
                    if level.startswith(f"{family}|")
                ],
                dtype=np.int32,
            )
    candidate_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        candidate_groups[str(candidate["population_id"])].append(candidate)

    days = np.asarray([str(row["decision_time_utc"])[:10] for row in rows], dtype="U10")
    train_indices_by_day = [
        np.flatnonzero(np.logical_and(masks["TRAIN"], days == day))
        for day in sorted(set(days[masks["TRAIN"]].tolist()))
    ]
    rng = np.random.default_rng(seed)
    null_max = np.empty(draws, dtype=np.float64)
    for draw in range(draws):
        shuffled = codes.copy()
        for indices in train_indices_by_day:
            shuffled[indices] = rng.permutation(codes[indices])
        draw_max = -math.inf
        for population_id, group in candidate_groups.items():
            population = population_by_id[population_id]
            if population["kind"] == "family":
                permuted_population = np.isin(
                    shuffled, family_codes[str(population["family"])]
                )
            else:
                level = f"{population['family']}|{population['direction']}"
                permuted_population = shuffled == level_to_code[level]
            permuted_train = np.logical_and(masks["TRAIN"], permuted_population)
            if not permuted_train.any():
                raise FBRefusal(f"max_t_empty_permuted_population:{population_id}")
            for candidate in group:
                lift = float(
                    np.mean(candidate["vector"][permuted_train])
                    - candidate["baseline_train_mean_net_r"]
                )
                draw_max = max(draw_max, lift)
        null_max[draw] = draw_max

    reported = []
    for candidate in candidates:
        observed = float(candidate["observed_train_lift_r"])
        p_value = float((1 + np.count_nonzero(null_max >= observed)) / (draws + 1))
        reported.append(
            {
                key: value
                for key, value in candidate.items()
                if key != "vector"
            }
            | {
                "familywise_maxT_p": p_value,
                "alpha": 0.05,
                "familywise_significant": p_value <= 0.05,
            }
        )
    return {
        "schema": "gtos.session_fb.within_day_fixed_leader_max_t.v1",
        "surface": SURFACE,
        "billed": False,
        "seed": seed,
        "draws": draws,
        "resolution_floor": 1 / (draws + 1),
        "unit": "UTC TRAIN decision day",
        "randomization": "joint origin_family x direction labels permuted within day",
        "statistic": "one-sided fixed-leader population TRAIN mean-net lift over the same-cell full TRAIN baseline",
        "selection_control_boundary": (
            "max-T spans fixed TRAIN leaders; untouched HOLDOUT controls geometry selection"
        ),
        "candidate_leaders": reported,
        "null": {
            "mean": float(np.mean(null_max)),
            "sd": float(np.std(null_max, ddof=1)),
            "q95": float(np.quantile(null_max, 0.95)),
            "min": float(np.min(null_max)),
            "max": float(np.max(null_max)),
        },
    }


def decomposition_rows(
    rows: Sequence[Mapping[str, Any]], arrays: Mapping[str, np.ndarray]
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        groups[(str(row["origin_family"]), normalize_side(row))].append(index)
    total_gross = float(np.sum(arrays["gross"]))
    total_deficit = -total_gross
    result = []
    for (family, direction), indices_raw in sorted(groups.items()):
        indices = np.asarray(indices_raw, dtype=np.int64)
        gross_sum = float(np.sum(arrays["gross"][indices]))
        result.append(
            {
                "population_id": f"family_direction:{family}|{direction}",
                "family": family,
                "direction": direction,
                "n": len(indices),
                "row_share": len(indices) / len(rows),
                "gross_sum_r": gross_sum,
                "gross_mean_r": float(np.mean(arrays["gross"][indices])),
                "cost_sum_r": float(np.sum(arrays["cost"][indices])),
                "cost_mean_r": float(np.mean(arrays["cost"][indices])),
                "net_sum_r": float(np.sum(arrays["net"][indices])),
                "net_mean_r": float(np.mean(arrays["net"][indices])),
                "gross_deficit_contribution_r": -gross_sum,
                "share_of_signed_total_gross_deficit": (
                    (-gross_sum / total_deficit) if total_deficit else None
                ),
            }
        )
    return result


def assert_decomposition_identity(
    arrays: Mapping[str, np.ndarray], rows: Sequence[Mapping[str, Any]], label: str
) -> dict[str, Any]:
    return {
        "label": label,
        "rows": len(rows),
        "gross_sum_r": float(np.sum(arrays["gross"])),
        "cost_sum_r": float(np.sum(arrays["cost"])),
        "net_sum_r": float(np.sum(arrays["net"])),
        "gross_minus_cost_equals_net_max_abs": float(
            np.max(np.abs(arrays["gross"] - arrays["cost"] - arrays["net"]))
        ),
        "identity_within_1e_9": bool(
            np.max(np.abs(arrays["gross"] - arrays["cost"] - arrays["net"]))
            <= TOL
        ),
    }


def residual_surface_report(
    *,
    rows: Sequence[Mapping[str, Any]],
    arrays: Mapping[str, np.ndarray],
    residual: Mapping[str, np.ndarray],
) -> dict[str, Any]:
    families = np.asarray([str(row["origin_family"]) for row in rows], dtype="U96")
    result: dict[str, Any] = {}
    for name, surface_mask in residual.items():
        total = economic_metrics(arrays, surface_mask, total_n=len(rows))
        by_family = []
        for family in sorted(set(families.tolist())):
            mask = np.logical_and(surface_mask, families == family)
            metrics = economic_metrics(
                arrays, mask, total_n=max(int(surface_mask.sum()), 1)
            )
            by_family.append({"family": family, **metrics})
        negative = sorted(
            [row for row in by_family if float(row["net_sum_r"]) < 0],
            key=lambda row: float(row["net_sum_r"]),
        )
        positive = sorted(
            [row for row in by_family if float(row["net_sum_r"]) > 0],
            key=lambda row: -float(row["net_sum_r"]),
        )
        result[name] = {
            "total": total,
            "surface_net_negative": bool(float(total["net_sum_r"]) < 0),
            "negative_family_drivers": negative,
            "positive_family_offsets": positive,
            "all_families": by_family,
        }
    return result


def classification_payload(
    *,
    populations: Sequence[Mapping[str, Any]],
    leaders: Mapping[str, Mapping[str, Mapping[str, Any]]],
    max_t: Mapping[str, Any],
) -> dict[str, Any]:
    p_by_leader = {
        str(row["leader_id"]): row
        for row in max_t["candidate_leaders"]
    }
    classifications = []
    null_clean = []
    for population in populations:
        population_id = str(population["population_id"])
        base = {
            key: population[key]
            for key in (
                "population_id",
                "kind",
                "family",
                "direction",
                "n",
                "minimum_n",
                "eligible",
            )
        }
        if not population["eligible"]:
            classifications.append(
                base
                | {
                    "classification": "NOT_EVALUABLE_BELOW_PREREGISTERED_DENOMINATOR",
                    "orientation_leaders": None,
                    "null_clean_repair": False,
                }
            )
            continue
        by_orientation = leaders[population_id]
        classification = classify_orientation_leaders(
            by_orientation["as_declared"], by_orientation["inverted"]
        )
        leader_report: dict[str, Any] = {}
        population_null_clean = False
        for orientation, leader in by_orientation.items():
            leader_id = f"{population_id}|{orientation}"
            max_t_row = p_by_leader.get(leader_id)
            splits = leader["splits"]
            persistent = (
                float(splits["TRAIN"]["mean_net_r"]) > 0
                and float(splits["HOLDOUT"]["mean_net_r"]) > 0
                and float(splits["FULL"]["mean_net_r"]) > 0
            )
            clean = bool(
                persistent
                and max_t_row is not None
                and float(max_t_row["familywise_maxT_p"]) <= 0.05
            )
            population_null_clean = population_null_clean or clean
            leader_report[orientation] = dict(leader) | {
                "maxT_control": max_t_row,
                "persistent_train_holdout_full_net_positive": persistent,
                "null_clean_repair": clean,
            }
            if clean:
                null_clean.append(
                    {
                        "population_id": population_id,
                        "family": population["family"],
                        "direction": population["direction"],
                        "classification": classification,
                        "orientation": orientation,
                        "cell_id": leader["cell_id"],
                        "familywise_maxT_p": max_t_row["familywise_maxT_p"],
                    }
                )
        classifications.append(
            base
            | {
                "classification": classification,
                "orientation_leaders": leader_report,
                "null_clean_repair": population_null_clean,
            }
        )
    unique_repairs: dict[tuple[str, str, str], dict[str, Any]] = {}
    for repair in null_clean:
        key = (
            str(repair["family"]),
            str(repair["orientation"]),
            str(repair["cell_id"]),
        )
        record = unique_repairs.setdefault(
            key,
            {
                "family": repair["family"],
                "orientation": repair["orientation"],
                "cell_id": repair["cell_id"],
                "classification": repair["classification"],
                "familywise_maxT_p": repair["familywise_maxT_p"],
                "supporting_population_ids": [],
                "supporting_directions": [],
            },
        )
        record["supporting_population_ids"].append(repair["population_id"])
        if repair["direction"] is not None:
            record["supporting_directions"].append(repair["direction"])
    unique_null_clean = []
    for record in unique_repairs.values():
        record["supporting_population_ids"] = sorted(
            set(record["supporting_population_ids"])
        )
        record["supporting_directions"] = sorted(
            set(record["supporting_directions"])
        )
        unique_null_clean.append(record)
    unique_null_clean.sort(
        key=lambda row: (str(row["family"]), str(row["orientation"]), str(row["cell_id"]))
    )
    return {
        "population_classifications": classifications,
        "null_clean_repairs": null_clean,
        "unique_null_clean_repair_candidates": unique_null_clean,
        "counts": dict(Counter(row["classification"] for row in classifications)),
        "counts_by_kind": {
            kind: dict(
                Counter(
                    row["classification"]
                    for row in classifications
                    if row["kind"] == kind
                )
            )
            for kind in ("family", "family_direction")
        },
    }


def build_look_manifest(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    logical_looks = []
    evaluation_count = 0
    for cell in cells:
        population_cells = []
        for population_id, result in cell["populations"].items():
            evaluation_count += 1
            population_cells.append(
                {
                    "population_id": population_id,
                    "surface": SURFACE,
                    "billed": False,
                    "verdict": result["verdict"],
                    "train_mean_net_r": result["splits"]["TRAIN"]["mean_net_r"],
                    "holdout_mean_net_r": result["splits"]["HOLDOUT"]["mean_net_r"],
                    "full_mean_net_r": result["splits"]["FULL"]["mean_net_r"],
                }
            )
        spec = {
            "orientation": cell["orientation"],
            "target_distance_D": cell["target_distance_D"],
            "stop_distance_D": cell["stop_distance_D"],
        }
        logical_looks.append(
            {
                "look_id": canonical_sha256(
                    {"session": "FB", "kind": "family_geometry", **spec}
                )[:20],
                "kind": "family_geometry",
                "surface": SURFACE,
                "billed": False,
                "spec": spec,
                "cell_id": cell["cell_id"],
                "population_cells": population_cells,
                "receipt": repo_path(GRID_RESULTS),
            }
        )
    if len(logical_looks) != 198:
        raise FBRefusal(f"look_manifest_geometry_count:{len(logical_looks)}!=198")
    return {
        "schema": LOOK_SCHEMA,
        "generated_at_utc": utc_now(),
        "source_head": repo_head(),
        "surface": SURFACE,
        "billed": False,
        "master_iteration_ledger_appended": False,
        "multiplicity_rule": (
            "one look per orientation x target x stop; family populations are declared strata"
        ),
        "logical_geometry_looks": len(logical_looks),
        "population_cell_evaluations": evaluation_count,
        "all_population_cells_forensic_diagnostic": True,
        "all_population_cells_billed_false": True,
        "permutation_draws_are_one_control_procedure": True,
        "promotion_authority": False,
        "activation_authority": False,
        "looks": logical_looks,
    }


def january_command(registry_path: Path | None = None) -> dict[str, Any]:
    protocol = load_protocol()
    inputs = protocol["inputs"]
    pool_path = verify_bound_file(inputs["january_pool"], key="january_pool")
    sidecar_path = verify_bound_file(
        inputs["january_ordered_path_sidecar"], key="january_ordered_path_sidecar"
    )
    manifest_path = verify_bound_file(
        inputs["path_pool_manifest"], key="path_pool_manifest"
    )
    verify_bound_file(inputs["frozen_ck_protocol"], key="frozen_ck_protocol")
    verify_bound_file(inputs["frozen_path_contract"], key="frozen_path_contract")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if registry_path is None:
        registry_path = Path(manifest["lane_authority"]["registry_path"])

    rows, pool_meta = cq.load_pool_rows(pool_path)
    if len(rows) != int(inputs["january_pool"]["rows"]):
        raise FBRefusal("january_pool_row_count_drift")
    composite = validate_composite_sidecar(rows, sidecar_path)
    arrays = recorded_arrays(rows)
    residual = residual_masks(rows)
    populations, families, directions = build_populations(rows, protocol)
    census = census_rows(rows, populations, arrays, residual)
    masks, split_meta = cq._split_masks(rows)

    targets = np.asarray(
        protocol["geometry"]["target_distance_in_D"], dtype=np.float64
    )
    stops = np.asarray(
        protocol["geometry"]["stop_distance_in_D"], dtype=np.float64
    )
    summaries, sidecar_validation = cq.load_path_summaries(
        pool_rows=rows,
        sidecar_path=sidecar_path,
        targets=targets,
        stops=stops,
    )
    authority = cq.authenticate_lane_registry(registry_path)
    _, tick_sources = cq.source_records(authority)
    tick_resolution = cq.apply_tick_priority(
        summaries=summaries,
        pool_rows=rows,
        tick_sources=tick_sources,
        targets=targets,
        stops=stops,
    )
    costs, cost_reprice = cq._broker_true_cost_vector(
        rows, masks, np.zeros(len(rows), dtype=bool)
    )
    if int(cost_reprice["unpriced_rows"]) != 0:
        raise FBRefusal("broker_true_cost_rows_unpriced")

    cells, leaders = run_grid(
        rows=rows,
        populations=populations,
        masks=masks,
        summaries=summaries,
        costs=costs,
        targets=targets,
        stops=stops,
    )
    max_t = max_t_control(
        rows=rows,
        populations=populations,
        leaders=leaders,
        masks=masks,
        summaries=summaries,
        costs=costs,
        targets=targets,
        stops=stops,
        draws=int(protocol["breaker_and_null_control"]["draws"]),
        seed=int(protocol["breaker_and_null_control"]["seed"]),
    )
    classified = classification_payload(
        populations=populations, leaders=leaders, max_t=max_t
    )

    source_modes = summaries["as_declared"]["source_mode"]
    path_resolution = {
        "ordered_tick_rows": int(np.sum(source_modes == "ORDERED_TICK")),
        "m1_conservative_rows": int(np.sum(source_modes == "M1_CONSERVATIVE")),
        "all_rows_resolved": bool(np.all(source_modes != "")),
        "tick_resolution": tick_resolution,
    }
    grid_result = write_json(
        GRID_RESULTS,
        {
            "schema": GRID_SCHEMA,
            "generated_at_utc": utc_now(),
            "source_head": repo_head(),
            "protocol": repo_path(PROTOCOL),
            "protocol_sha256": sha256_file(PROTOCOL),
            "surface": SURFACE,
            "billed": False,
            "march_2026_outcomes_read": False,
            "live_forward_outcomes_read": False,
            "february_2026_economics_read": False,
            "broker_or_vps_accessed": False,
            "replay_launched": False,
            "base_pool": pool_meta,
            "composite_join": composite,
            "chronological_split": split_meta,
            "family_count": len(set(families.tolist())),
            "direction_count": len(set(directions.tolist())),
            "all_population_count": len(populations),
            "eligible_population_count": sum(
                bool(population["eligible"]) for population in populations
            ),
            "census": census,
            "path_resolution": path_resolution,
            "sidecar_validation": sidecar_validation,
            "broker_true_cost_reprice": cost_reprice,
            "reported_cells": len(cells),
            "every_declared_cell_reported": len(cells) == 198,
            "cells": cells,
        },
    )

    classification = write_json(
        CLASSIFICATION,
        {
            "schema": CLASSIFICATION_SCHEMA,
            "generated_at_utc": utc_now(),
            "source_head": repo_head(),
            "surface": SURFACE,
            "billed": False,
            "selection": "TRAIN_ONLY",
            "persistence": "HOLDOUT_ONLY_AFTER_TRAIN_LEADER_FIXED",
            "classification_precedence": protocol["classification"]["precedence"],
            "max_T_control": max_t,
            **classified,
            "grid_receipt": {
                "path": repo_path(GRID_RESULTS),
                "self_sha256": grid_result["self_sha256"],
            },
        },
    )

    jan_decomp_rows = decomposition_rows(rows, arrays)
    group_gross_sum = sum(float(row["gross_sum_r"]) for row in jan_decomp_rows)
    if not math.isclose(
        group_gross_sum, float(np.sum(arrays["gross"])), rel_tol=0.0, abs_tol=TOL
    ):
        raise FBRefusal("january_group_gross_decomposition_mismatch")
    gross = write_json(
        GROSS_DECOMP,
        {
            "schema": GROSS_SCHEMA,
            "generated_at_utc": utc_now(),
            "source_head": repo_head(),
            "surface": SURFACE,
            "billed": False,
            "january": {
                "identity": assert_decomposition_identity(arrays, rows, "january_2026"),
                "family_x_direction": jan_decomp_rows,
                "family_x_direction_gross_sum_r": group_gross_sum,
                "sum_matches_full_pool_within_1e_9": True,
                "residual_choice_surfaces": residual_surface_report(
                    rows=rows, arrays=arrays, residual=residual
                ),
            },
            "february": {
                "status": "PENDING_FROZEN_CORROBORATION_COMMAND",
                "selection_authority": False,
            },
        },
    )

    p_by_id = {
        str(row["leader_id"]): row for row in max_t["candidate_leaders"]
    }
    breaker_populations = []
    comparator_id = "inverted|target_5D|stop_0.25D"
    comparator = next(cell for cell in cells if cell["cell_id"] == comparator_id)
    for population in populations:
        if population["family"] != "current_breaker_re_entry":
            continue
        population_id = str(population["population_id"])
        entry: dict[str, Any] = {
            key: population[key]
            for key in (
                "population_id",
                "kind",
                "family",
                "direction",
                "n",
                "minimum_n",
                "eligible",
            )
        }
        if population["eligible"]:
            entry["orientation_leaders"] = {
                orientation: dict(leader)
                | {
                    "maxT_control": p_by_id.get(f"{population_id}|{orientation}")
                }
                for orientation, leader in leaders[population_id].items()
            }
            entry["cq_5D_target_0p25D_stop_comparator"] = comparator[
                "populations"
            ][population_id]
            source_mask = np.asarray(population["mask"], dtype=bool)
            entry["path_source_modes"] = {
                mode: int(np.sum(np.logical_and(source_mask, source_modes == mode)))
                for mode in ("ORDERED_TICK", "M1_CONSERVATIVE")
            }
        breaker_populations.append(entry)
    breaker = write_json(
        BREAKER,
        {
            "schema": BREAKER_SCHEMA,
            "generated_at_utc": utc_now(),
            "source_head": repo_head(),
            "surface": SURFACE,
            "billed": False,
            "clock": "true_utc",
            "breaker_populations": breaker_populations,
            "fixed_leader_within_day_max_T": max_t,
            "null_clean_repairs": [
                row
                for row in classified["null_clean_repairs"]
                if row["family"] == "current_breaker_re_entry"
            ],
            "cq_comparator_cell_id": comparator_id,
            "existing_default_off_transform": (
                "src/components/current_breaker_re_entry_repair.py"
            ),
            "promotion_authority": False,
            "activation_authority": False,
        },
    )
    looks = write_json(LOOK_MANIFEST, build_look_manifest(cells))
    return {
        "status": "JANUARY_FULL_FAMILY_GRID_COMPLETE",
        "grid": grid_result["self_sha256"],
        "classification": classification["self_sha256"],
        "gross_decomposition": gross["self_sha256"],
        "breaker": breaker["self_sha256"],
        "looks": looks["self_sha256"],
        "eligible_populations": grid_result["eligible_population_count"],
        "null_clean_repairs": len(classified["null_clean_repairs"]),
        "unique_null_clean_repair_candidates": len(
            classified["unique_null_clean_repair_candidates"]
        ),
    }


def february_command() -> dict[str, Any]:
    protocol = load_protocol()
    january_grid = validate_rooted_json(GRID_RESULTS)
    classification = validate_rooted_json(CLASSIFICATION)
    gross = validate_rooted_json(GROSS_DECOMP)
    if (
        january_grid.get("february_2026_economics_read") is not False
        or gross.get("february", {}).get("status")
        != "PENDING_FROZEN_CORROBORATION_COMMAND"
    ):
        raise FBRefusal("february_command_january_anchor_invalid")
    feb_spec = protocol["inputs"]["february_pool"]
    feb_path = verify_bound_file(feb_spec, key="february_pool")
    rows = list(iter_gzip_json(feb_path))
    if len(rows) != int(feb_spec["rows"]):
        raise FBRefusal(f"february_row_count:{len(rows)}!={feb_spec['rows']}")
    for index, row in enumerate(rows):
        decision = normalized_utc(row.get("decision_time_utc"))
        if decision.startswith("2026-03"):
            raise FBRefusal(f"march_outcome_forbidden:{index}:{decision}")
        if not decision.startswith("2026-02"):
            raise FBRefusal(f"non_february_row:{index}:{decision}")
        normalize_side(row)

    net = np.asarray([float(row["opportunity_net_proxy_r"]) for row in rows])
    cost = np.asarray([float(row["cost_r"]) for row in rows])
    gross_primary = np.asarray([float(row["opportunity_gross_r"]) for row in rows])
    if not (
        np.isfinite(net).all()
        and np.isfinite(cost).all()
        and np.isfinite(gross_primary).all()
    ):
        raise FBRefusal("february_economics_nonfinite")
    gross_crosscheck = net + cost
    crosscheck_delta = gross_primary - gross_crosscheck
    arrays = {"gross": gross_primary, "cost": cost, "net": net}
    decomp = decomposition_rows(rows, arrays)
    group_sum = sum(float(row["gross_sum_r"]) for row in decomp)
    if not math.isclose(
        group_sum, float(np.sum(gross_primary)), rel_tol=0.0, abs_tol=TOL
    ):
        raise FBRefusal("february_group_gross_decomposition_mismatch")

    jan_rows = {
        str(row["population_id"]): row
        for row in gross["january"]["family_x_direction"]
    }
    class_rows = {
        str(row["population_id"]): row
        for row in classification["population_classifications"]
    }
    corroboration = []
    for row in decomp:
        population_id = str(row["population_id"])
        january = jan_rows.get(population_id)
        frozen_class = class_rows.get(population_id)
        january_gross = (
            float(january["gross_mean_r"]) if january is not None else None
        )
        february_gross = float(row["gross_mean_r"])
        corroboration.append(
            {
                **row,
                "january_n": january.get("n") if january else 0,
                "january_gross_mean_r": january_gross,
                "january_classification": (
                    frozen_class.get("classification")
                    if frozen_class
                    else "JANUARY_POPULATION_ABSENT"
                ),
                "gross_sign_corroborates_january": (
                    None
                    if january_gross is None
                    else bool(
                        np.sign(january_gross) == np.sign(february_gross)
                        or (january_gross == 0 and february_gross == 0)
                    )
                ),
            }
        )

    provenance_counts = Counter(
        str(row.get("pretrade_cost_packet_status") or "__MISSING__") for row in rows
    )
    flat_default_symbols = {"UKOIL_cash", "USOIL_cash", "GER40"}
    feb_payload = write_json(
        FEB_CORROBORATION,
        {
            "schema": FEB_SCHEMA,
            "generated_at_utc": utc_now(),
            "source_head": repo_head(),
            "label": FEB_LABEL,
            "surface": "ATTRIBUTION_ONLY_USED_ONCE_VAL",
            "selection_authority": False,
            "geometry_selection_performed": False,
            "january_rules_changed": False,
            "march_2026_outcomes_read": False,
            "live_forward_outcomes_read": False,
            "pool": {
                "path": repo_path(feb_path),
                "sha256": sha256_file(feb_path),
                "rows": len(rows),
            },
            "gross_primary_field": "opportunity_gross_r",
            "gross_crosscheck": {
                "formula": "opportunity_net_proxy_r + cost_r",
                "max_abs_delta_r": float(np.max(np.abs(crosscheck_delta))),
                "mismatch_rows_above_1e_9": int(
                    np.count_nonzero(np.abs(crosscheck_delta) > TOL)
                ),
            },
            "identity": assert_decomposition_identity(arrays, rows, "february_2026"),
            "family_x_direction": corroboration,
            "family_x_direction_gross_sum_r": group_sum,
            "sum_matches_full_pool_within_1e_9": True,
            "gross_sign_concordance": {
                "comparable_cells": sum(
                    row["gross_sign_corroborates_january"] is not None
                    for row in corroboration
                ),
                "same_sign_cells": sum(
                    row["gross_sign_corroborates_january"] is True
                    for row in corroboration
                ),
                "opposite_sign_cells": sum(
                    row["gross_sign_corroborates_january"] is False
                    for row in corroboration
                ),
            },
            "known_cost_provenance_limits": {
                "pretrade_cost_packet_status_counts": dict(
                    sorted(provenance_counts.items())
                ),
                "flat_default_symbol_rows": sum(
                    str(row.get("symbol")) in flat_default_symbols for row in rows
                ),
                "flat_default_symbols": sorted(flat_default_symbols),
                "interpretation": (
                    "gross attribution is primary; February net/cost values are contextual and "
                    "cannot repair the already identified provenance defects"
                ),
            },
            "frozen_january_receipts": {
                "grid": january_grid["self_sha256"],
                "classification": classification["self_sha256"],
                "gross_decomposition_before_february": gross["self_sha256"],
            },
        },
    )

    gross_without_hash = dict(gross)
    gross_without_hash.pop("self_sha256", None)
    gross_without_hash["generated_at_utc"] = utc_now()
    gross_without_hash["february"] = {
        "status": "ATTRIBUTION_CORROBORATION_COMPLETE",
        "label": FEB_LABEL,
        "selection_authority": False,
        "identity": assert_decomposition_identity(arrays, rows, "february_2026"),
        "family_x_direction": decomp,
        "family_x_direction_gross_sum_r": group_sum,
        "sum_matches_full_pool_within_1e_9": True,
        "receipt": {
            "path": repo_path(FEB_CORROBORATION),
            "self_sha256": feb_payload["self_sha256"],
        },
    }
    updated_gross = write_json(GROSS_DECOMP, gross_without_hash)
    return {
        "status": "FEBRUARY_ATTRIBUTION_CORROBORATION_COMPLETE",
        "label": FEB_LABEL,
        "february": feb_payload["self_sha256"],
        "gross_decomposition": updated_gross["self_sha256"],
        "rows": len(rows),
    }


def verify_command() -> dict[str, Any]:
    required = [
        GRID_RESULTS,
        CLASSIFICATION,
        GROSS_DECOMP,
        BREAKER,
        FEB_CORROBORATION,
        LOOK_MANIFEST,
    ]
    payloads = {path.name: validate_rooted_json(path) for path in required}
    grid = payloads[GRID_RESULTS.name]
    looks = payloads[LOOK_MANIFEST.name]
    feb = payloads[FEB_CORROBORATION.name]
    checks = {
        "grid_cells_198": grid.get("reported_cells") == 198,
        "all_cells_reported": grid.get("every_declared_cell_reported") is True,
        "composite_join_complete": (
            grid.get("composite_join", {}).get("key_sets_identical") is True
        ),
        "logical_looks_198": looks.get("logical_geometry_looks") == 198,
        "all_cells_forensic": looks.get(
            "all_population_cells_forensic_diagnostic"
        )
        is True,
        "all_cells_unbilled": looks.get("all_population_cells_billed_false") is True,
        "february_attribution_only": (
            feb.get("label") == FEB_LABEL
            and feb.get("selection_authority") is False
            and feb.get("geometry_selection_performed") is False
        ),
        "february_primary_decomposition_closes": (
            feb.get("sum_matches_full_pool_within_1e_9") is True
        ),
        "february_net_cost_crosscheck_is_rounding_bounded": (
            float(feb.get("gross_crosscheck", {}).get("max_abs_delta_r", math.inf))
            <= 1e-8
        ),
        "march_unread": all(
            payload.get("march_2026_outcomes_read", False) is False
            for payload in payloads.values()
        ),
        "live_forward_unread": all(
            payload.get("live_forward_outcomes_read", False) is False
            for payload in payloads.values()
        ),
    }
    if not all(checks.values()):
        raise FBRefusal(f"final_output_verification_failed:{checks}")
    return {
        "status": "VERIFIED",
        "checks": checks,
        "outputs": {
            name: {
                "path": repo_path(GRID_DIR / name),
                "self_sha256": payload["self_sha256"],
                "file_sha256": sha256_file(GRID_DIR / name),
            }
            for name, payload in payloads.items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    january = sub.add_parser("january", help="run the preregistered January grid")
    january.add_argument("--lane-input-registry", type=Path)
    sub.add_parser(
        "february", help="apply frozen January labels to February attribution only"
    )
    sub.add_parser("verify", help="validate all rooted outputs and boundaries")
    args = parser.parse_args()
    if args.command == "january":
        result = january_command(args.lane_input_registry)
    elif args.command == "february":
        result = february_command()
    else:
        result = verify_command()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
