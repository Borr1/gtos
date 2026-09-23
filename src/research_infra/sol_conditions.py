"""Wave-19 true-UTC condition diagnostics with a hard January/February freeze.

The module reads compact pool rows as a stream and retains only typed labels,
identities, and ten declared cell memberships.  ``jan`` is the only command
that ranks cells.  ``feb`` refuses to run unless the January selection artifact
is tracked, clean, and byte-identical to ``HEAD``.

Every emitted result is FORENSIC_DIAGNOSTIC, billed false, and carries no
promotion or activation authority.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import math
import random
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


EVIDENCE_BOUNDARY = {
    "evidence_class": "FORENSIC_DIAGNOSTIC",
    "billed": False,
    "promotion_authority": False,
    "activation_authority": False,
    "march_2026_outcomes_read": False,
    "live_forward_outcomes_read": False,
}

AXIS_ORDER = (
    "family_direction_session",
    "family_hour",
    "family",
    "direction",
    "session",
    "utc_hour",
    "symbol_class",
    "kill_zone",
    "route_session",
    "day_of_week",
)

AXIS_FIELDS: dict[str, tuple[str, ...]] = {
    "family_direction_session": ("family", "direction", "session"),
    "family_hour": ("family", "utc_hour"),
    "family": ("family",),
    "direction": ("direction",),
    "session": ("session",),
    "utc_hour": ("utc_hour",),
    "symbol_class": ("symbol_class",),
    "kill_zone": ("kill_zone",),
    "route_session": ("route_session",),
    "day_of_week": ("day_of_week",),
}


@dataclass(frozen=True)
class CellSpec:
    index: int
    axis: str
    values: tuple[str, ...]

    @property
    def level(self) -> dict[str, str]:
        return dict(zip(AXIS_FIELDS[self.axis], self.values, strict=True))

    @property
    def cell_id(self) -> str:
        terms = "|".join(
            f"{name}={value}"
            for name, value in zip(AXIS_FIELDS[self.axis], self.values, strict=True)
        )
        return f"{self.axis}|{terms}"

    def to_json(self) -> dict[str, Any]:
        return {"cell_id": self.cell_id, "axis": self.axis, "level": self.level}


@dataclass
class CompactPool:
    identities: list[str]
    days: list[str]
    splits: list[str]
    symbols: list[str]
    gross: np.ndarray
    net: np.ndarray
    cost: np.ndarray
    slippage: np.ndarray
    members: list[list[int]]

    @property
    def rows(self) -> int:
        return len(self.identities)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.write_text(rendered, encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def load_protocol(path: Path) -> dict[str, Any]:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    if protocol.get("schema") != "gtos.wave19.sol_conditions_protocol.v1":
        raise ValueError(f"unexpected_protocol_schema:{protocol.get('schema')}")
    if protocol.get("declared_before_new_outcome_analysis") is not True:
        raise ValueError("protocol_not_declared_before_analysis")
    if protocol["permutation_inference"]["permutations"] != 999:
        raise ValueError("permutation_count_drift")
    return protocol


def build_cells(protocol: Mapping[str, Any]) -> list[CellSpec]:
    levels = protocol["declared_levels"]
    axis_values: dict[str, Iterable[tuple[str, ...]]] = {
        "family_direction_session": itertools.product(
            levels["family"], levels["direction"], levels["session"]
        ),
        "family_hour": itertools.product(levels["family"], levels["utc_hour"]),
        "family": ((value,) for value in levels["family"]),
        "direction": ((value,) for value in levels["direction"]),
        "session": ((value,) for value in levels["session"]),
        "utc_hour": ((value,) for value in levels["utc_hour"]),
        "symbol_class": ((value,) for value in levels["symbol_class"]),
        "kill_zone": ((value,) for value in levels["kill_zone"]),
        "route_session": ((value,) for value in levels["route_session"]),
        "day_of_week": ((value,) for value in levels["day_of_week"]),
    }
    cells: list[CellSpec] = []
    # Preserve the protocol's declaration order, not AXIS_ORDER's canonical
    # alias precedence.
    declaration_axes = [item["axis"] for item in protocol["cell_space"]["construction"]]
    for axis in declaration_axes:
        for values in axis_values[axis]:
            cells.append(CellSpec(index=len(cells), axis=axis, values=tuple(values)))
    expected = int(protocol["cell_space"]["declared_cells_total"])
    if len(cells) != expected:
        raise ValueError(f"declared_cell_count_drift:{len(cells)}!={expected}")
    if len({cell.cell_id for cell in cells}) != len(cells):
        raise ValueError("duplicate_declared_cell_id")
    return cells


def _symbol_class_map(protocol: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for group, symbols in protocol["symbol_class_map"].items():
        for symbol in symbols:
            if symbol in result:
                raise ValueError(f"symbol_in_multiple_classes:{symbol}")
            result[symbol] = group
    return result


def _parse_day(value: Any) -> tuple[str, str]:
    text = str(value or "").strip()
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"decision_time_not_utc:{text}")
    day = parsed.date().isoformat()
    weekday = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")[
        parsed.weekday()
    ]
    return day, weekday


def row_axes(row: Mapping[str, Any], protocol: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    direction = str(row.get("direction") or "").strip().upper()
    side = str(row.get("side") or "").strip().upper()
    if direction not in protocol["declared_levels"]["direction"]:
        raise ValueError(f"undeclared_direction:{direction}")
    if side and side != direction:
        raise ValueError(f"side_direction_disagreement:{side}:{direction}")
    day, weekday = _parse_day(row.get("decision_time_utc"))
    del day
    family = str(row.get("origin_family") or "").strip()
    session = str(row.get("session_bucket") or "").strip()
    utc_hour = str(row.get("utc_hour_bucket") or "").strip()
    kill_zone = str(row.get("kill_zone") or "").strip()
    route_session = str(row.get("route_session") or "").strip()
    symbol = str(row.get("symbol") or "").strip()
    symbol_class = _symbol_class_map(protocol).get(symbol)
    if symbol_class is None:
        raise ValueError(f"undeclared_symbol:{symbol}")
    scalars = {
        "family": family,
        "direction": direction,
        "session": session,
        "utc_hour": utc_hour,
        "symbol_class": symbol_class,
        "kill_zone": kill_zone,
        "route_session": route_session,
        "day_of_week": weekday,
    }
    for name, value in scalars.items():
        if value not in protocol["declared_levels"][name]:
            raise ValueError(f"undeclared_level:{name}:{value}")
    return {
        "family_direction_session": (family, direction, session),
        "family_hour": (family, utc_hour),
        **{name: (value,) for name, value in scalars.items()},
    }


def _finite_float(row: Mapping[str, Any], field: str, identity: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"missing_or_invalid_metric:{field}:{identity}") from exc
    if not math.isfinite(value):
        raise ValueError(f"nonfinite_metric:{field}:{identity}")
    return value


def load_compact_pool(
    protocol: Mapping[str, Any],
    cells: Sequence[CellSpec],
    *,
    window: str,
    gross_identity_tolerance_r: float = 1e-9,
) -> CompactPool:
    contract = protocol["inputs"][window]
    path = Path(contract["path"])
    actual_sha = sha256_file(path)
    if actual_sha != contract["sha256"]:
        raise ValueError(f"{window}_sha256_mismatch:{actual_sha}")

    lookup = {(cell.axis, cell.values): cell.index for cell in cells}
    members: list[list[int]] = [[] for _ in cells]
    identities: list[str] = []
    seen: set[str] = set()
    days: list[str] = []
    splits: list[str] = []
    symbols: list[str] = []
    gross: list[float] = []
    net: list[float] = []
    cost: list[float] = []
    slippage: list[float] = []
    train_dates = set(protocol["split"]["train_dates"])
    holdout_dates = set(protocol["split"]["holdout_dates"])

    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            row = json.loads(line)
            day, _weekday = _parse_day(row.get("decision_time_utc"))
            direction = str(row.get("direction") or "").strip().upper()
            identity_parts = (
                str(row.get("candidate_id") or "").strip(),
                str(row.get("decision_time_utc") or "").strip(),
                str(row.get("symbol") or "").strip(),
                direction,
            )
            if not all(identity_parts):
                raise ValueError(f"incomplete_composite_identity:{window}:{line_number}")
            identity = json.dumps(identity_parts, separators=(",", ":"))
            if identity in seen:
                raise ValueError(f"duplicate_composite_identity:{identity}")
            seen.add(identity)

            net_value = _finite_float(row, "opportunity_net_proxy_r", identity)
            cost_value = _finite_float(row, "cost_r", identity)
            gross_value = net_value + cost_value
            if row.get("opportunity_gross_r") is not None:
                recorded_gross = _finite_float(row, "opportunity_gross_r", identity)
                if abs(recorded_gross - gross_value) > gross_identity_tolerance_r:
                    raise ValueError(
                        f"gross_identity_mismatch:{identity}:{recorded_gross}:{gross_value}"
                    )
            slip_value = _finite_float(row, "expected_slippage_r", identity)

            if window == "january":
                if day in train_dates:
                    split = "TRAIN"
                elif day in holdout_dates:
                    split = "HOLDOUT"
                else:
                    raise ValueError(f"january_date_outside_frozen_split:{day}")
            else:
                if not day.startswith("2026-02-"):
                    raise ValueError(f"february_row_outside_window:{day}")
                split = "FEBRUARY"

            row_index = len(identities)
            axes = row_axes(row, protocol)
            for axis, values in axes.items():
                try:
                    members[lookup[(axis, values)]].append(row_index)
                except KeyError as exc:
                    raise ValueError(f"row_cell_not_declared:{axis}:{values}") from exc
            identities.append(identity)
            days.append(day)
            splits.append(split)
            symbols.append(identity_parts[2])
            gross.append(gross_value)
            net.append(net_value)
            cost.append(cost_value)
            slippage.append(slip_value)

    expected_rows = int(contract["rows"])
    if len(identities) != expected_rows:
        raise ValueError(f"{window}_row_count_mismatch:{len(identities)}!={expected_rows}")
    if window == "january":
        if splits.count("TRAIN") != protocol["split"]["expected_train_rows"]:
            raise ValueError("january_train_row_count_drift")
        if splits.count("HOLDOUT") != protocol["split"]["expected_holdout_rows"]:
            raise ValueError("january_holdout_row_count_drift")
    return CompactPool(
        identities=identities,
        days=days,
        splits=splits,
        symbols=symbols,
        gross=np.asarray(gross, dtype=np.float64),
        net=np.asarray(net, dtype=np.float64),
        cost=np.asarray(cost, dtype=np.float64),
        slippage=np.asarray(slippage, dtype=np.float64),
        members=members,
    )


def _indices_for_split(pool: CompactPool, indices: Iterable[int], split: str) -> np.ndarray:
    return np.asarray([index for index in indices if pool.splits[index] == split], dtype=np.int64)


def describe(pool: CompactPool, indices: Sequence[int] | np.ndarray) -> dict[str, Any]:
    idx = np.asarray(indices, dtype=np.int64)
    if idx.size == 0:
        return {
            "n": 0,
            "unique_composite_identities": 0,
            "day_count": 0,
            "gross_sum_r": 0.0,
            "gross_mean_r": None,
            "gross_positive_share": None,
            "gross_day_positive_share": None,
            "net_sum_r": 0.0,
            "net_mean_r": None,
            "net_positive_share": None,
            "net_day_positive_share": None,
            "cost_sum_r": 0.0,
            "cost_mean_r": None,
        }
    gross = pool.gross[idx]
    net = pool.net[idx]
    cost = pool.cost[idx]
    day_gross: dict[str, float] = {}
    day_net: dict[str, float] = {}
    for row_index in idx.tolist():
        day = pool.days[row_index]
        day_gross[day] = day_gross.get(day, 0.0) + float(pool.gross[row_index])
        day_net[day] = day_net.get(day, 0.0) + float(pool.net[row_index])
    return {
        "n": int(idx.size),
        "unique_composite_identities": int(idx.size),
        "day_count": len(day_gross),
        "gross_sum_r": float(np.sum(gross)),
        "gross_mean_r": float(np.mean(gross)),
        "gross_positive_share": float(np.mean(gross > 0.0)),
        "gross_day_positive_share": float(
            np.mean(np.asarray(list(day_gross.values())) > 0.0)
        ),
        "net_sum_r": float(np.sum(net)),
        "net_mean_r": float(np.mean(net)),
        "net_positive_share": float(np.mean(net > 0.0)),
        "net_day_positive_share": float(
            np.mean(np.asarray(list(day_net.values())) > 0.0)
        ),
        "cost_sum_r": float(np.sum(cost)),
        "cost_mean_r": float(np.mean(cost)),
    }


def _membership_structure(
    pool: CompactPool,
    cells: Sequence[CellSpec],
    protocol: Mapping[str, Any],
) -> tuple[dict[int, dict[str, Any]], list[int]]:
    minimum = int(protocol["cell_space"]["minimum_train_rows"])
    precedence = {axis: index for index, axis in enumerate(AXIS_ORDER)}
    metadata: dict[int, dict[str, Any]] = {}
    groups: dict[str, list[int]] = {}
    eligible_count = 0
    for cell in cells:
        train_indices = _indices_for_split(pool, pool.members[cell.index], "TRAIN")
        eligible = train_indices.size >= minimum
        item: dict[str, Any] = {
            "train_n": int(train_indices.size),
            "eligible": bool(eligible),
            "membership_sha256": None,
            "canonical": False,
            "alias_of": None,
            "aliases": [],
        }
        if eligible:
            eligible_count += 1
            digest = hashlib.sha256()
            for identity in sorted(pool.identities[index] for index in train_indices.tolist()):
                digest.update(identity.encode("utf-8"))
                digest.update(b"\n")
            membership_sha = digest.hexdigest()
            item["membership_sha256"] = membership_sha
            groups.setdefault(membership_sha, []).append(cell.index)
        metadata[cell.index] = item

    expected_eligible = int(
        protocol["cell_space"]["feature_only_expectations"][
            "eligible_cells_before_alias_collapse"
        ]
    )
    if eligible_count != expected_eligible:
        raise ValueError(f"eligible_cell_count_drift:{eligible_count}!={expected_eligible}")

    canonical_indices: list[int] = []
    for group in groups.values():
        ordered = sorted(
            group,
            key=lambda index: (precedence[cells[index].axis], cells[index].cell_id),
        )
        canonical = ordered[0]
        canonical_indices.append(canonical)
        aliases = [cells[index].cell_id for index in ordered[1:]]
        metadata[canonical]["canonical"] = True
        metadata[canonical]["aliases"] = aliases
        for alias in ordered[1:]:
            metadata[alias]["alias_of"] = cells[canonical].cell_id
    canonical_indices.sort(key=lambda index: cells[index].cell_id)
    expected_unique = int(
        protocol["cell_space"]["feature_only_expectations"]["unique_eligible_partitions"]
    )
    if len(canonical_indices) != expected_unique:
        raise ValueError(
            f"unique_partition_count_drift:{len(canonical_indices)}!={expected_unique}"
        )
    return metadata, canonical_indices


def _average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=np.float64)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + end - 1) / 2.0 + 1.0
        start = end
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    xa = np.asarray(x, dtype=np.float64)
    ya = np.asarray(y, dtype=np.float64)
    if xa.size < 2 or ya.size != xa.size:
        return None
    xr = _average_ranks(xa)
    yr = _average_ranks(ya)
    if np.std(xr) == 0.0 or np.std(yr) == 0.0:
        return None
    return float(np.corrcoef(xr, yr)[0, 1])


def _day_groups(days: Sequence[str]) -> tuple[np.ndarray, list[np.ndarray]]:
    unique = sorted(set(days))
    lookup = {day: index for index, day in enumerate(unique)}
    codes = np.asarray([lookup[day] for day in days], dtype=np.int64)
    groups = [np.where(codes == index)[0] for index in range(len(unique))]
    return codes, groups


def _permutation_index(size: int, groups: Sequence[np.ndarray], seed: int) -> np.ndarray:
    result = np.arange(size, dtype=np.int64)
    rng = random.Random(seed)
    for group in groups:
        shuffled = group.tolist()
        rng.shuffle(shuffled)
        result[group] = np.asarray(shuffled, dtype=np.int64)
    return result


def _day_means(values: np.ndarray, day_codes: np.ndarray) -> np.ndarray:
    counts = np.bincount(day_codes)
    sums = np.bincount(day_codes, weights=values)
    return sums[day_codes] / counts[day_codes]


def _studentized_day_centered(
    values: np.ndarray,
    day_means: np.ndarray,
    indices: np.ndarray,
) -> float:
    residual = values[indices] - day_means[indices]
    if residual.size < 2:
        return -math.inf
    std = float(np.std(residual, ddof=1))
    if not math.isfinite(std) or std <= 0.0:
        return -math.inf
    return float(math.sqrt(residual.size) * float(np.mean(residual)) / std)


def _eta_squared(values: np.ndarray, row_indices: np.ndarray, groups: np.ndarray) -> float:
    selected = values[row_indices]
    if selected.size < 2 or len(np.unique(groups)) < 2:
        return -math.inf
    counts = np.bincount(groups)
    sums = np.bincount(groups, weights=selected)
    means = sums / counts
    grand = float(np.mean(selected))
    ss_between = float(np.sum(counts * np.square(means - grand)))
    ss_total = float(np.sum(np.square(selected - grand)))
    if ss_total <= 0.0:
        return -math.inf
    return ss_between / ss_total


def _axis_grouping(
    pool: CompactPool,
    cells: Sequence[CellSpec],
    metadata: Mapping[int, Mapping[str, Any]],
    train_position: Mapping[int, int],
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for axis in AXIS_ORDER:
        row_indices: list[int] = []
        group_codes: list[int] = []
        eligible_cells = [
            cell
            for cell in cells
            if cell.axis == axis and metadata[cell.index]["eligible"]
        ]
        for group_code, cell in enumerate(eligible_cells):
            for global_index in pool.members[cell.index]:
                if global_index in train_position:
                    row_indices.append(train_position[global_index])
                    group_codes.append(group_code)
        result[axis] = (
            np.asarray(row_indices, dtype=np.int64),
            np.asarray(group_codes, dtype=np.int64),
        )
    return result


def permutation_inference(
    pool: CompactPool,
    cells: Sequence[CellSpec],
    metadata: Mapping[int, Mapping[str, Any]],
    canonical_indices: Sequence[int],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    permutations = int(protocol["permutation_inference"]["permutations"])
    seed = int(protocol["permutation_inference"]["seed"])
    train_global = np.asarray(
        [index for index, split in enumerate(pool.splits) if split == "TRAIN"],
        dtype=np.int64,
    )
    train_position = {global_index: pos for pos, global_index in enumerate(train_global.tolist())}
    train_days = [pool.days[index] for index in train_global.tolist()]
    train_day_codes, train_day_groups = _day_groups(train_days)
    train_values = {
        "gross": pool.gross[train_global],
        "net": pool.net[train_global],
    }
    canonical_local: dict[int, np.ndarray] = {
        cell_index: np.asarray(
            [train_position[index] for index in pool.members[cell_index] if index in train_position],
            dtype=np.int64,
        )
        for cell_index in canonical_indices
    }
    day_means = {
        basis: _day_means(values, train_day_codes)
        for basis, values in train_values.items()
    }
    observed_cells: dict[str, dict[int, float]] = {
        basis: {
            cell_index: _studentized_day_centered(
                values, day_means[basis], canonical_local[cell_index]
            )
            for cell_index in canonical_indices
        }
        for basis, values in train_values.items()
    }
    axis_groups = _axis_grouping(pool, cells, metadata, train_position)
    observed_axes: dict[str, dict[str, float]] = {
        basis: {
            axis: _eta_squared(values, *axis_groups[axis])
            for axis in AXIS_ORDER
        }
        for basis, values in train_values.items()
    }

    null_cell_max = np.empty(permutations, dtype=np.float64)
    null_axis_max = np.empty(permutations, dtype=np.float64)
    for permutation_index in range(1, permutations + 1):
        perm = _permutation_index(
            len(train_global), train_day_groups, seed + permutation_index
        )
        cell_max = -math.inf
        axis_max = -math.inf
        for basis, values in train_values.items():
            permuted = values[perm]
            for cell_index in canonical_indices:
                statistic = _studentized_day_centered(
                    permuted, day_means[basis], canonical_local[cell_index]
                )
                cell_max = max(cell_max, statistic)
            for axis in AXIS_ORDER:
                statistic = _eta_squared(permuted, *axis_groups[axis])
                axis_max = max(axis_max, statistic)
        null_cell_max[permutation_index - 1] = cell_max
        null_axis_max[permutation_index - 1] = axis_max

    cell_results: dict[str, dict[str, Any]] = {"gross": {}, "net": {}}
    for basis in ("gross", "net"):
        for cell_index in canonical_indices:
            observed = observed_cells[basis][cell_index]
            p_value = (1 + int(np.sum(null_cell_max >= observed))) / (permutations + 1)
            cell_results[basis][cells[cell_index].cell_id] = {
                "studentized_day_centered_statistic": observed,
                "max_t_fwer_p": p_value,
            }

    axis_results: dict[str, dict[str, Any]] = {"gross": {}, "net": {}}
    for basis in ("gross", "net"):
        for axis in AXIS_ORDER:
            observed = observed_axes[basis][axis]
            p_value = (1 + int(np.sum(null_axis_max >= observed))) / (permutations + 1)
            axis_results[basis][axis] = {
                "eta_squared": observed,
                "max_adjusted_p": p_value,
                "indistinguishable_from_within_day_noise": p_value > 0.1,
            }

    holdout_global = np.asarray(
        [index for index, split in enumerate(pool.splits) if split == "HOLDOUT"],
        dtype=np.int64,
    )
    holdout_position = {
        global_index: pos for pos, global_index in enumerate(holdout_global.tolist())
    }
    holdout_days = [pool.days[index] for index in holdout_global.tolist()]
    _holdout_day_codes, holdout_day_groups = _day_groups(holdout_days)
    rank_cells = [
        cell_index
        for cell_index in canonical_indices
        if any(index in holdout_position for index in pool.members[cell_index])
    ]
    holdout_local = {
        cell_index: np.asarray(
            [
                holdout_position[index]
                for index in pool.members[cell_index]
                if index in holdout_position
            ],
            dtype=np.int64,
        )
        for cell_index in rank_cells
    }
    train_local_for_rank = [canonical_local[index] for index in rank_cells]
    train_rank_means = {
        basis: np.asarray(
            [float(np.mean(train_values[basis][indices])) for indices in train_local_for_rank]
        )
        for basis in ("gross", "net")
    }
    holdout_values = {
        "gross": pool.gross[holdout_global],
        "net": pool.net[holdout_global],
    }
    holdout_rank_means = {
        basis: np.asarray(
            [
                float(np.mean(values[holdout_local[index]]))
                for index in rank_cells
            ]
        )
        for basis, values in holdout_values.items()
    }
    observed_rho = {
        basis: spearman(train_rank_means[basis], holdout_rank_means[basis])
        for basis in ("gross", "net")
    }
    null_rank_max = np.empty(permutations, dtype=np.float64)
    for permutation_index in range(1, permutations + 1):
        perm = _permutation_index(
            len(holdout_global), holdout_day_groups, seed + permutation_index
        )
        rhos: list[float] = []
        for basis, values in holdout_values.items():
            permuted = values[perm]
            means = np.asarray(
                [float(np.mean(permuted[holdout_local[index]])) for index in rank_cells]
            )
            rho = spearman(train_rank_means[basis], means)
            rhos.append(-math.inf if rho is None else rho)
        null_rank_max[permutation_index - 1] = max(rhos)
    rank_results: dict[str, Any] = {}
    for basis in ("gross", "net"):
        observed = observed_rho[basis]
        rank_results[basis] = {
            "rho": observed,
            "max_adjusted_one_sided_p": None
            if observed is None
            else (1 + int(np.sum(null_rank_max >= observed))) / (permutations + 1),
        }

    return {
        "schema": "gtos.wave19.sol_rank_persistence.v1",
        **EVIDENCE_BOUNDARY,
        "generated_at_utc": utc_now(),
        "permutations": permutations,
        "seed": seed,
        "canonical_cells": len(canonical_indices),
        "rank_cells_with_holdout": len(rank_cells),
        "rank_spearman": rank_results,
        "cell_max_t": cell_results,
        "axis_variance": axis_results,
        "null_max_summary": {
            "cell_statistic": _quantile_summary(null_cell_max),
            "axis_eta_squared": _quantile_summary(null_axis_max),
            "rank_rho": _quantile_summary(null_rank_max),
        },
    }


def _quantile_summary(values: np.ndarray) -> dict[str, float]:
    return {
        "min": float(np.min(values)),
        "p50": float(np.quantile(values, 0.5)),
        "p90": float(np.quantile(values, 0.9)),
        "p95": float(np.quantile(values, 0.95)),
        "p99": float(np.quantile(values, 0.99)),
        "max": float(np.max(values)),
    }


def _cost_width_summary(pool: CompactPool, indices: Sequence[int]) -> dict[str, Any]:
    idx = np.asarray(indices, dtype=np.int64)
    costs = pool.cost[idx]
    slippage = pool.slippage[idx]
    all_cost_width = np.maximum(1.0, costs / 0.15)
    denominators = 0.15 - slippage
    scalable = np.maximum(0.0, costs - slippage)
    fixed_width = np.full(costs.shape, np.inf, dtype=np.float64)
    valid_denominator = denominators > 0.0
    np.divide(
        scalable,
        denominators,
        out=fixed_width,
        where=valid_denominator,
    )
    fixed_width[valid_denominator] = np.maximum(
        1.0, fixed_width[valid_denominator]
    )

    def width_summary(values: np.ndarray) -> dict[str, Any]:
        finite = values[np.isfinite(values)]
        return {
            "infinite_rows": int(np.sum(~np.isfinite(values))),
            "p50": None if finite.size == 0 else float(np.quantile(finite, 0.5)),
            "p90": None if finite.size == 0 else float(np.quantile(finite, 0.9)),
            "p95": None if finite.size == 0 else float(np.quantile(finite, 0.95)),
            "p99": None if finite.size == 0 else float(np.quantile(finite, 0.99)),
            "max": None if finite.size == 0 else float(np.max(finite)),
        }

    return {
        "n": int(idx.size),
        "current_cost_mean_r": float(np.mean(costs)),
        "current_cost_quantiles_r": {
            "p50": float(np.quantile(costs, 0.5)),
            "p90": float(np.quantile(costs, 0.9)),
            "p95": float(np.quantile(costs, 0.95)),
            "p99": float(np.quantile(costs, 0.99)),
            "max": float(np.max(costs)),
        },
        "share_cost_at_or_below_0p15r": float(np.mean(costs <= 0.15)),
        "required_width_multiple_all_costs_scale": width_summary(all_cost_width),
        "required_width_multiple_fixed_slippage": width_summary(fixed_width),
        "mean_gross_minus_0p15r": float(np.mean(pool.gross[idx]) - 0.15),
        "arithmetic_only": True,
        "path_outcomes_recomputed": False,
    }


def _repo_root(protocol_path: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=protocol_path.parent,
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip())


def analyze_january(protocol_path: Path) -> dict[str, Path]:
    protocol_path = protocol_path.resolve()
    protocol = load_protocol(protocol_path)
    cells = build_cells(protocol)
    pool = load_compact_pool(protocol, cells, window="january")
    metadata, canonical_indices = _membership_structure(pool, cells, protocol)
    inference = permutation_inference(pool, cells, metadata, canonical_indices, protocol)
    train_floor = int(protocol["cell_space"]["minimum_train_rows"])
    holdout_floor = int(protocol["cell_space"]["minimum_holdout_rows_for_repair"])

    cell_rows: list[dict[str, Any]] = []
    metrics: dict[int, dict[str, Any]] = {}
    for cell in cells:
        train_idx = _indices_for_split(pool, pool.members[cell.index], "TRAIN")
        holdout_idx = _indices_for_split(pool, pool.members[cell.index], "HOLDOUT")
        train = describe(pool, train_idx)
        holdout = describe(pool, holdout_idx)
        metrics[cell.index] = {"TRAIN": train, "HOLDOUT": holdout}
        meta = metadata[cell.index]
        row = {
            **cell.to_json(),
            "look_taken": bool(meta["eligible"] and meta["canonical"]),
            "train_eligible": bool(meta["eligible"]),
            "canonical": bool(meta["canonical"]),
            "alias_of": meta["alias_of"],
            "aliases": meta["aliases"],
            "train_membership_sha256": meta["membership_sha256"],
            "splits": {"TRAIN": train, "HOLDOUT": holdout},
            "persistent_gross_positive": bool(
                train["n"] >= train_floor
                and holdout["n"] >= holdout_floor
                and train["gross_mean_r"] is not None
                and train["gross_mean_r"] > 0.0
                and holdout["gross_mean_r"] is not None
                and holdout["gross_mean_r"] > 0.0
            ),
            "persistent_net_positive": bool(
                train["n"] >= train_floor
                and holdout["n"] >= holdout_floor
                and train["net_mean_r"] is not None
                and train["net_mean_r"] > 0.0
                and holdout["net_mean_r"] is not None
                and holdout["net_mean_r"] > 0.0
            ),
        }
        if row["look_taken"]:
            row["inference"] = {
                basis: inference["cell_max_t"][basis][cell.cell_id]
                for basis in ("gross", "net")
            }
        else:
            row["inference"] = None
        cell_rows.append(row)

    protocol_sha = sha256_file(protocol_path)
    repo = _repo_root(protocol_path)
    common = {
        **EVIDENCE_BOUNDARY,
        "generated_at_utc": utc_now(),
        "source_head": git_head(repo),
        "protocol": str(protocol_path.relative_to(repo)),
        "protocol_sha256": protocol_sha,
        "january_source_sha256": protocol["inputs"]["january"]["sha256"],
        "february_2026_outcomes_read": False,
    }
    cell_map = {
        "schema": "gtos.wave19.sol_cell_map_january.v1",
        **common,
        "rows": pool.rows,
        "split_counts": {
            "TRAIN": pool.splits.count("TRAIN"),
            "HOLDOUT": pool.splits.count("HOLDOUT"),
        },
        "declared_cells": len(cells),
        "eligible_cells_before_alias_collapse": sum(
            bool(item["eligible"]) for item in metadata.values()
        ),
        "canonical_eligible_cells": len(canonical_indices),
        "cells": cell_rows,
    }

    rankings: dict[str, list[int]] = {}
    for basis in ("gross", "net"):
        key = f"{basis}_mean_r"
        rankings[basis] = sorted(
            canonical_indices,
            key=lambda index: (-metrics[index]["TRAIN"][key], cells[index].cell_id),
        )
    top_ids = {
        basis: [cells[index].cell_id for index in ordered[:20]]
        for basis, ordered in rankings.items()
    }
    selection_digest = hashlib.sha256(canonical_json_bytes(top_ids)).hexdigest()
    selected_indices = sorted(set(rankings["gross"][:20] + rankings["net"][:20]))
    selected_cells: dict[str, Any] = {}
    for index in selected_indices:
        cell = cells[index]
        selected_cells[cell.cell_id] = {
            **cell.to_json(),
            "aliases": metadata[index]["aliases"],
            "train_membership_sha256": metadata[index]["membership_sha256"],
            "january": metrics[index],
            "inference": {
                basis: inference["cell_max_t"][basis][cell.cell_id]
                for basis in ("gross", "net")
            },
        }
    frozen = {
        "schema": "gtos.wave19.sol_frozen_january_selections.v1",
        **common,
        "selection_surface": "JANUARY_TRAIN_ONLY",
        "selection_digest": selection_digest,
        "cutoffs": [5, 10, 20],
        "rankings": top_ids,
        "cells": selected_cells,
        "february_selection_allowed": False,
        "must_be_committed_before_february": True,
    }

    frontier_rows: list[dict[str, Any]] = []
    for index in canonical_indices:
        train = metrics[index]["TRAIN"]
        holdout = metrics[index]["HOLDOUT"]
        if not (
            train["n"] >= train_floor
            and holdout["n"] >= holdout_floor
            and train["gross_mean_r"] > 0.0
            and holdout["gross_mean_r"] > 0.0
        ):
            continue
        full_indices = pool.members[index]
        frontier_rows.append(
            {
                **cells[index].to_json(),
                "aliases": metadata[index]["aliases"],
                "january": metrics[index],
                "cost_width_burden_full_january": _cost_width_summary(
                    pool, full_indices
                ),
                "february_transfer": "PENDING_FROZEN_TRANSFER",
            }
        )
    frontier = {
        "schema": "gtos.wave19.sol_gross_positive_frontier.v1",
        **common,
        "definition": protocol["gross_positive_frontier"]["membership"],
        "cost_cap_r": 0.15,
        "arithmetic_only": True,
        "path_outcomes_recomputed": False,
        "frontier_cells": frontier_rows,
    }

    axis_summary: dict[str, Any] = {}
    for axis in AXIS_ORDER:
        axis_cells = [cell for cell in cells if cell.axis == axis]
        canonical_axis_cells = [index for index in canonical_indices if cells[index].axis == axis]
        axis_summary[axis] = {
            "declared_cells": len(axis_cells),
            "observed_train_cells": sum(metadata[cell.index]["train_n"] > 0 for cell in axis_cells),
            "eligible_train_cells": sum(metadata[cell.index]["eligible"] for cell in axis_cells),
            "canonical_look_cells": len(canonical_axis_cells),
            "train_gross_positive_cells": sum(
                metrics[index]["TRAIN"]["gross_mean_r"] > 0.0
                for index in canonical_axis_cells
            ),
            "train_net_positive_cells": sum(
                metrics[index]["TRAIN"]["net_mean_r"] > 0.0
                for index in canonical_axis_cells
            ),
            "persistent_gross_positive_cells": sum(
                next(row for row in cell_rows if row["cell_id"] == cells[index].cell_id)[
                    "persistent_gross_positive"
                ]
                for index in canonical_axis_cells
            ),
            "persistent_net_positive_cells": sum(
                next(row for row in cell_rows if row["cell_id"] == cells[index].cell_id)[
                    "persistent_net_positive"
                ]
                for index in canonical_axis_cells
            ),
            "variance": {
                basis: inference["axis_variance"][basis][axis]
                for basis in ("gross", "net")
            },
            "permutation_invariant_within_day": axis == "day_of_week",
        }
    negative = {
        "schema": "gtos.wave19.sol_negative_space.v1",
        **common,
        "status": "JANUARY_COMPLETE_FEBRUARY_PENDING",
        "axis_summary": axis_summary,
        "persistent_gross_positive_cells": len(frontier_rows),
        "persistent_net_positive_cells": sum(
            bool(row["persistent_net_positive"] and row["look_taken"])
            for row in cell_rows
        ),
        "condition_survivors": "PENDING_FROZEN_FEBRUARY_TRANSFER",
        "missing_feature_boundary": protocol["repair_decision"]["if_none"],
        "day_of_week_caveat": "Within-day permutations cannot move a day-level label across weekdays. A p-value of 1 for day_of_week means this test is permutation-invariant, not that multiple-week day effects were disproved.",
    }

    look_manifest = {
        "schema": "gtos.wave19.sol_look_manifest.v1",
        **common,
        "declared_cells": len(cells),
        "january_cell_split_observations": len(cells) * 2,
        "eligible_cells_before_alias_collapse": sum(
            bool(item["eligible"]) for item in metadata.values()
        ),
        "canonical_inferential_looks": len(canonical_indices),
        "permutation_draws": 999,
        "billed_looks": 0,
        "cells": [
            {
                "cell_id": row["cell_id"],
                "look_taken": row["look_taken"],
                "train_eligible": row["train_eligible"],
                "alias_of": row["alias_of"],
                "train_n": row["splits"]["TRAIN"]["n"],
                "holdout_n": row["splits"]["HOLDOUT"]["n"],
            }
            for row in cell_rows
        ],
        "february_transfer": "PENDING_COMMITTED_JANUARY_FREEZE",
    }

    output_dir = protocol_path.parent
    outputs = {
        "CELL_MAP_JAN.json": cell_map,
        "RANK_PERSISTENCE.json": inference,
        "FROZEN_JAN_SELECTIONS.json": frozen,
        "GROSS_POSITIVE_FRONTIER.json": frontier,
        "NEGATIVE_SPACE.json": negative,
        "LOOK_MANIFEST.json": look_manifest,
    }
    paths: dict[str, Path] = {}
    for name, value in outputs.items():
        path = output_dir / name
        write_json(path, value)
        paths[name] = path
    return paths


def _assert_committed_file(repo: Path, path: Path, *, label: str) -> None:
    relative = str(path.relative_to(repo))
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", relative], cwd=repo
    ).returncode
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", relative], cwd=repo
    ).returncode
    if unstaged != 0 or staged != 0:
        raise ValueError(f"{label}_not_clean")
    committed = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    if hashlib.sha256(committed).hexdigest() != sha256_file(path):
        raise ValueError(f"{label}_not_identical_to_head")


def _assert_committed_freeze(repo: Path, path: Path) -> None:
    _assert_committed_file(repo, path, label="frozen_january_selection")


def load_feb_gross_reconciliation(
    path: Path,
    *,
    protocol_sha256: str,
    frozen_selection_sha256: str,
    february_source_sha256: str,
) -> dict[str, Any]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "gtos.wave19.sol_feb_gross_identity_reconciliation.v1":
        raise ValueError("unexpected_feb_gross_reconciliation_schema")
    expected = {
        "original_protocol_sha256": protocol_sha256,
        "frozen_january_selection_sha256": frozen_selection_sha256,
        "february_source_sha256": february_source_sha256,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ValueError(f"feb_gross_reconciliation_binding_mismatch:{field}")
    if receipt.get("condition_aggregates_read_before_reconciliation") is not False:
        raise ValueError("feb_gross_reconciliation_postdates_condition_analysis")
    census = receipt["identity_residual_census"]
    repair = receipt["bounded_repair"]
    tolerance = float(repair["identity_tolerance_r"])
    if int(census["rows"]) != 24239:
        raise ValueError("feb_gross_reconciliation_row_count_drift")
    if int(census["rows_over_5e_9"]) != 0:
        raise ValueError("feb_gross_reconciliation_has_out_of_bound_rows")
    if tolerance != 5e-9 or float(census["max_abs_r"]) > tolerance:
        raise ValueError("feb_gross_reconciliation_tolerance_not_bounded")
    if repair.get("gross_metric_unchanged") != "opportunity_net_proxy_r + cost_r":
        raise ValueError("feb_gross_reconciliation_changed_metric")
    if repair.get("february_selection_allowed") is not False:
        raise ValueError("feb_gross_reconciliation_selection_boundary_missing")
    return receipt


def _union_indices(pool: CompactPool, cell_indices: Iterable[int]) -> np.ndarray:
    rows: set[int] = set()
    for cell_index in cell_indices:
        rows.update(pool.members[cell_index])
    return np.asarray(sorted(rows), dtype=np.int64)


def transfer_february(protocol_path: Path) -> dict[str, Path]:
    protocol_path = protocol_path.resolve()
    protocol = load_protocol(protocol_path)
    repo = _repo_root(protocol_path)
    frozen_path = protocol_path.parent / "FROZEN_JAN_SELECTIONS.json"
    _assert_committed_freeze(repo, frozen_path)
    frozen_sha = sha256_file(frozen_path)
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if frozen.get("schema") != "gtos.wave19.sol_frozen_january_selections.v1":
        raise ValueError("unexpected_frozen_selection_schema")
    if frozen.get("february_selection_allowed") is not False:
        raise ValueError("february_selection_boundary_missing")

    reconciliation_path = protocol_path.parent / "FEB_GROSS_IDENTITY_RECONCILIATION.json"
    _assert_committed_file(
        repo,
        reconciliation_path,
        label="feb_gross_identity_reconciliation",
    )
    reconciliation = load_feb_gross_reconciliation(
        reconciliation_path,
        protocol_sha256=sha256_file(protocol_path),
        frozen_selection_sha256=frozen_sha,
        february_source_sha256=protocol["inputs"]["february"]["sha256"],
    )

    cells = build_cells(protocol)
    cell_by_id = {cell.cell_id: cell for cell in cells}
    pool = load_compact_pool(
        protocol,
        cells,
        window="february",
        gross_identity_tolerance_r=float(
            reconciliation["bounded_repair"]["identity_tolerance_r"]
        ),
    )
    transferred_ids = sorted(
        set(frozen["rankings"]["gross"] + frozen["rankings"]["net"])
    )
    defect_symbols = set(
        protocol["february_transfer"]["known_cost_integrity_sensitivity"]["symbols"]
    )
    per_cell: dict[str, Any] = {}
    for cell_id in transferred_ids:
        cell = cell_by_id[cell_id]
        primary_indices = np.asarray(pool.members[cell.index], dtype=np.int64)
        sensitivity_indices = np.asarray(
            [index for index in primary_indices.tolist() if pool.symbols[index] not in defect_symbols],
            dtype=np.int64,
        )
        touches_defect = any(
            pool.symbols[index] in defect_symbols for index in primary_indices.tolist()
        )
        per_cell[cell_id] = {
            **cell.to_json(),
            "primary": describe(pool, primary_indices),
            "cost_integrity_sensitivity": describe(pool, sensitivity_indices),
            "touches_known_cost_default_symbols": touches_defect,
        }

    top_k: dict[str, Any] = {}
    for basis in ("gross", "net"):
        ranking = frozen["rankings"][basis]
        top_k[basis] = {}
        for cutoff in (5, 10, 20):
            selected = ranking[:cutoff]
            selected_indices = [cell_by_id[cell_id].index for cell_id in selected]
            union = _union_indices(pool, selected_indices)
            sensitivity = np.asarray(
                [index for index in union.tolist() if pool.symbols[index] not in defect_symbols],
                dtype=np.int64,
            )
            top_k[basis][str(cutoff)] = {
                "cell_ids": selected,
                "cell_results": {cell_id: per_cell[cell_id] for cell_id in selected},
                "union_primary": describe(pool, union),
                "union_cost_integrity_sensitivity": describe(pool, sensitivity),
                "union_counts_each_composite_identity_once": True,
            }

    train_floor = int(protocol["cell_space"]["minimum_train_rows"])
    holdout_floor = int(protocol["cell_space"]["minimum_holdout_rows_for_repair"])
    feb_floor = int(protocol["cell_space"]["minimum_february_rows_for_repair"])
    survivors: list[dict[str, Any]] = []
    failures: dict[str, list[str]] = {}
    for cell_id in transferred_ids:
        january = frozen["cells"][cell_id]["january"]
        infer = frozen["cells"][cell_id]["inference"]
        feb = per_cell[cell_id]
        reasons: list[str] = []
        if january["TRAIN"]["n"] < train_floor:
            reasons.append("train_n_below_floor")
        if january["HOLDOUT"]["n"] < holdout_floor:
            reasons.append("holdout_n_below_floor")
        if feb["primary"]["n"] < feb_floor:
            reasons.append("february_n_below_floor")
        for split in ("TRAIN", "HOLDOUT"):
            for basis in ("gross", "net"):
                if january[split][f"{basis}_mean_r"] is None or january[split][
                    f"{basis}_mean_r"
                ] <= 0.0:
                    reasons.append(f"{split.lower()}_{basis}_not_positive")
        for basis in ("gross", "net"):
            if feb["primary"][f"{basis}_mean_r"] is None or feb["primary"][
                f"{basis}_mean_r"
            ] <= 0.0:
                reasons.append(f"february_{basis}_not_positive")
            if infer[basis]["max_t_fwer_p"] > 0.1:
                reasons.append(f"train_{basis}_max_t_not_significant")
        if feb["touches_known_cost_default_symbols"]:
            sensitivity = feb["cost_integrity_sensitivity"]
            if sensitivity["n"] < feb_floor:
                reasons.append("february_cost_sensitivity_n_below_floor")
            if sensitivity["net_mean_r"] is None or sensitivity["net_mean_r"] <= 0.0:
                reasons.append("february_cost_sensitivity_net_not_positive")
        reasons = sorted(set(reasons))
        failures[cell_id] = reasons
        if not reasons:
            survivors.append(
                {
                    "cell_id": cell_id,
                    "january": january,
                    "inference": infer,
                    "february": feb,
                }
            )

    transfer = {
        "schema": "gtos.wave19.sol_february_transfer.v1",
        **EVIDENCE_BOUNDARY,
        "february_2026_outcomes_read": True,
        "generated_at_utc": utc_now(),
        "source_head": git_head(repo),
        "protocol_sha256": sha256_file(protocol_path),
        "frozen_selection_sha256": frozen_sha,
        "gross_identity_reconciliation_sha256": sha256_file(reconciliation_path),
        "gross_identity_tolerance_r": reconciliation["bounded_repair"][
            "identity_tolerance_r"
        ],
        "selection_digest": frozen["selection_digest"],
        "provenance": "owner_mandate_20260801",
        "february_source_sha256": protocol["inputs"]["february"]["sha256"],
        "rows": pool.rows,
        "selection_or_retuning_on_february": False,
        "transferred_unique_cells": len(transferred_ids),
        "top_k": top_k,
        "per_cell": per_cell,
        "condition_survivors": survivors,
        "condition_survivor_count": len(survivors),
        "failure_reasons": failures,
    }
    transfer_path = protocol_path.parent / "FEB_TRANSFER.json"
    write_json(transfer_path, transfer)

    frontier_path = protocol_path.parent / "GROSS_POSITIVE_FRONTIER.json"
    frontier_before_sha = sha256_file(frontier_path)
    frontier = json.loads(frontier_path.read_text(encoding="utf-8"))
    for row in frontier["frontier_cells"]:
        row["february_transfer"] = per_cell.get(
            row["cell_id"],
            {"status": "NOT_IN_FROZEN_TOP_20_TRANSFER"},
        )
    frontier["february_2026_outcomes_read"] = True
    frontier["january_frontier_sha256_before_february"] = frontier_before_sha
    frontier["february_source_sha256"] = protocol["inputs"]["february"]["sha256"]
    write_json(frontier_path, frontier)

    negative_path = protocol_path.parent / "NEGATIVE_SPACE.json"
    negative = json.loads(negative_path.read_text(encoding="utf-8"))
    negative["february_2026_outcomes_read"] = True
    negative["status"] = (
        "CONDITION_SURVIVOR_FOUND_DEFAULT_OFF_ONLY"
        if survivors
        else "NO_EXISTING_CONDITION_SURVIVED_DISCIPLINE"
    )
    negative["condition_survivors"] = survivors
    negative["condition_survivor_count"] = len(survivors)
    negative["next_action"] = (
        protocol["repair_decision"]["if_survivor"]
        if survivors
        else protocol["repair_decision"]["if_none"]
    )
    write_json(negative_path, negative)

    manifest_path = protocol_path.parent / "LOOK_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["february_2026_outcomes_read"] = True
    manifest["february_transfer"] = {
        "selection_digest": frozen["selection_digest"],
        "unique_cells": len(transferred_ids),
        "rank_families": 2,
        "cutoffs": [5, 10, 20],
        "selection_or_retuning": False,
        "provenance": "owner_mandate_20260801",
    }
    write_json(manifest_path, manifest)
    return {
        "FEB_TRANSFER.json": transfer_path,
        "GROSS_POSITIVE_FRONTIER.json": frontier_path,
        "NEGATIVE_SPACE.json": negative_path,
        "LOOK_MANIFEST.json": manifest_path,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("jan", "feb"))
    parser.add_argument("--protocol", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    outputs = (
        analyze_january(args.protocol)
        if args.stage == "jan"
        else transfer_february(args.protocol)
    )
    print(
        json.dumps(
            {
                "stage": args.stage,
                "outputs": {
                    name: {"path": str(path), "sha256": sha256_file(path)}
                    for name, path in outputs.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
