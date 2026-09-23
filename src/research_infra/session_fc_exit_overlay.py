#!/usr/bin/env python3
"""Session FC: honest ex-ante broad-V4 exit-overlay analysis.

The tool is intentionally offline and fail-closed.  It reads only January 2026
development paths and the owner-mandated February 2026 attribution surface.  It
streams the CQ sidecar, authenticates every source it consumes, uses composite
identity keys, and writes compact diagnostic artifacts.  It has no broker,
activation, config, live-forward, March, or sealed-replay capability.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import random
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import numpy as np


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.research_infra.exit_overlay import (  # noqa: E402
    ExitOverlaySpec,
    ExitPathPoint,
    MICROSECONDS_PER_MINUTE,
    replay_signed_path,
    true_utc_tick_time_us,
)
from src.research_infra.lane_rematerialization import LaneInputRegistry  # noqa: E402
from src.research_infra.train_engine.guard import (  # noqa: E402
    PURPOSE_LANE_ITERATION,
)
from src.research_infra.training_lane.append_only import (  # noqa: E402
    atomic_write_json,
)


AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
HERE = AUDIT / "phase19/receipts"
OUT = REPO / "research/operations/wave19_sol_repair_2026_08_01/exit"
PROTOCOL_PATH = OUT / "OVERLAY_PROTOCOL.json"

FA_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
    "research/operations/wave19_broad_forensic_2026_08_01"
)
JAN_TRADES = FA_ROOT / "trades_jan/TRADES_JAN_TABLE.json"
FEB_TRADES = FA_ROOT / "trades_feb/TRADES_FEB_TABLE.json"
JAN_RESIDUAL = FA_ROOT / "funnel_jan/RESIDUAL_CHOICE_SET.json"

CQ_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-path-pools-20260801/"
    "docs/audits/fable5-vision-audit-20260725"
)
POOL_PATH = CQ_ROOT / "phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
SIDECAR_PATH = (
    CQ_ROOT
    / "phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
)
POOL_MANIFEST_PATH = CQ_ROOT / "phase18/receipts/CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json"

LANE_REGISTRY = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
    ".hermes/evidence/phase16/cj-rematerialization/"
    "LANE_INPUTS_TRUE_UTC_V1/LANE_INPUT_REGISTRY.json"
)

RESULTS_PATH = OUT / "OVERLAY_RESULTS.json"
NULLS_PATH = OUT / "NULL_CONTROLS.json"
EXECUTED_PATH = OUT / "EXECUTED_OVERLAY_REPLAY.json"
LOOKS_PATH = OUT / "LOOK_MANIFEST.json"

SCHEMA_RESULTS = "gtos.session_fc.exit_overlay.results.v1"
SCHEMA_NULLS = "gtos.session_fc.exit_overlay.null_controls.v1"
SCHEMA_EXECUTED = "gtos.session_fc.exit_overlay.executed_replay.v1"
SCHEMA_LOOKS = "gtos.session_fc.exit_overlay.look_manifest.v1"
EXPECTED_PROTOCOL_SCHEMA = "gtos-session-fc-exit-overlay-protocol-v1"
EXPECTED_POOL_ROWS = 27_658
EXPECTED_JAN_TRADES = 57
EXPECTED_FEB_TRADES = 58
HORIZON_MINUTES = 120
TOL = 1e-9
NULL_SEEDS = (1901, 1902, 1903)
ALLOWED_MONTHS = frozenset({"2026-01", "2026-02"})


class FCRefusal(RuntimeError):
    """Fail-closed evidence, boundary, or analysis violation."""


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


def parse_utc_us(value: Any) -> int:
    text = str(value or "").strip()
    require_allowed_month(text, context="timestamp_parse")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise FCRefusal(f"invalid_utc_timestamp:{value}") from exc
    if parsed.tzinfo is None:
        raise FCRefusal(f"naive_utc_timestamp:{value}")
    return int(round(parsed.astimezone(dt.timezone.utc).timestamp() * 1_000_000))


def iso_from_us(value: int | None) -> str | None:
    if value is None:
        return None
    return dt.datetime.fromtimestamp(value / 1_000_000, tz=dt.timezone.utc).isoformat()


def require_allowed_month(value: str, *, context: str) -> None:
    text = str(value or "")
    if text.startswith("2026-03"):
        raise FCRefusal(f"march_outcome_boundary_violation:{context}")
    if text.startswith("2026-") and text[:7] not in ALLOWED_MONTHS:
        raise FCRefusal(f"noncommissioned_month:{context}:{text[:7]}")


def native(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return native(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(key): native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [native(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_rooted_json(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    result = native(dict(payload))
    result["self_sha256"] = canonical_sha256(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, result, indent=1)
    return result


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise FCRefusal(f"invalid_jsonl:{path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise FCRefusal(f"nonobject_jsonl:{path}:{line_number}")
            yield row


def composite_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    side = str(row.get("side") or row.get("direction") or "").upper()
    key = (
        str(row.get("candidate_id") or ""),
        str(row.get("decision_time_utc") or ""),
        str(row.get("symbol") or ""),
        side,
    )
    if not all(key) or side not in {"LONG", "SHORT"}:
        raise FCRefusal(f"composite_identity_invalid:{key}")
    require_allowed_month(key[1], context="composite_identity")
    return key


def load_protocol() -> tuple[dict[str, Any], tuple[ExitOverlaySpec, ...], str]:
    digest = sha256_file(PROTOCOL_PATH)
    payload = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != EXPECTED_PROTOCOL_SCHEMA:
        raise FCRefusal("overlay_protocol_schema_drift")
    if payload.get("declared_before_new_path_outcome_read") is not True:
        raise FCRefusal("overlay_protocol_not_predeclared")
    if (payload.get("authority_boundaries") or {}).get("march_2026") != (
        "OUTCOME_UNREAD_AND_FORBIDDEN"
    ):
        raise FCRefusal("overlay_protocol_march_boundary_drift")
    family = payload.get("family") or {}
    cells = family.get("variants") or []
    if family.get("declared_family_size") != 40 or len(cells) != 40:
        raise FCRefusal("overlay_protocol_family_size_drift")
    specs = tuple(ExitOverlaySpec.from_protocol_cell(cell) for cell in cells)
    if len({spec.variant_id for spec in specs}) != 40:
        raise FCRefusal("overlay_protocol_duplicate_variant")
    return payload, specs, digest


@dataclass(frozen=True)
class SourceRecord:
    symbol: str
    timeframe: str
    logical_path: str
    path: Path
    sha256: str
    row_count: int


@dataclass(frozen=True)
class WindowAuthority:
    window_id: str
    window: tuple[str, str]
    registry_root_sha256: str
    manifest_path: Path
    manifest_root_sha256: str
    m1: Mapping[str, SourceRecord]
    ticks: Mapping[str, SourceRecord]


def safe_lane_path(relative: str) -> Path:
    root = LANE_REGISTRY.parent.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise FCRefusal(f"lane_source_escapes_registry:{relative}") from exc
    if not path.is_file():
        raise FCRefusal(f"lane_source_missing:{relative}")
    return path


def authenticate_window(window_id: str) -> WindowAuthority:
    if window_id not in {"january_2026", "february_2026"}:
        raise FCRefusal(f"window_not_commissioned:{window_id}")
    resolved = LaneInputRegistry(LANE_REGISTRY).resolve(
        window_id=window_id,
        purpose=PURPOSE_LANE_ITERATION,
    )
    manifest = dict(resolved.source_manifest)
    expected_window = (
        ("2026-01-01", "2026-01-31")
        if window_id == "january_2026"
        else ("2026-02-01", "2026-02-28")
    )
    if (
        tuple(manifest.get("window") or ()) != expected_window
        or manifest.get("window_id") != window_id
        or manifest.get("economic_outcomes_read") is not False
        or manifest.get("campaign_sealed") is not False
        or manifest.get("surface") != "VAL"
        or (manifest.get("clock") or {}).get("time_column_basis") != "true_utc"
        or manifest.get("march_source_only_disclosure") not in (None, {})
        or resolved.entry.get("campaign_sealed") is not False
    ):
        raise FCRefusal(f"lane_window_authority_invalid:{window_id}")

    m1: dict[str, SourceRecord] = {}
    ticks: dict[str, SourceRecord] = {}
    month = expected_window[0][:7].replace("-", "")
    for raw in manifest.get("bar_sources") or []:
        if raw.get("timeframe") != "M1" or month not in str(raw.get("source_family") or ""):
            continue
        symbol = str(raw.get("mapped_symbol") or raw.get("symbol") or "")
        logical = str(raw.get("lane_relpath") or "")
        if symbol in m1:
            raise FCRefusal(f"duplicate_m1_source:{window_id}:{symbol}")
        m1[symbol] = SourceRecord(
            symbol=symbol,
            timeframe="M1",
            logical_path=logical,
            path=safe_lane_path(logical),
            sha256=str(raw.get("sha256") or ""),
            row_count=int(raw.get("row_count") or 0),
        )
    for raw in manifest.get("tick_sources") or []:
        if raw.get("timeframe") != "TICK":
            continue
        if (
            raw.get("time_column_basis") != "true_utc"
            or raw.get("clock_conversion") != "broker_epoch_to_utc"
        ):
            raise FCRefusal(f"tick_clock_authority_invalid:{window_id}")
        symbol = str(raw.get("mapped_symbol") or raw.get("symbol") or "")
        logical = str(raw.get("lane_relpath") or "")
        if symbol in ticks:
            raise FCRefusal(f"duplicate_tick_source:{window_id}:{symbol}")
        ticks[symbol] = SourceRecord(
            symbol=symbol,
            timeframe="TICK",
            logical_path=logical,
            path=safe_lane_path(logical),
            sha256=str(raw.get("sha256") or ""),
            row_count=int(raw.get("row_count") or 0),
        )
    if len(m1) != 24 or len(ticks) != int(manifest.get("tick_symbol_count") or 0):
        raise FCRefusal(f"lane_source_inventory_invalid:{window_id}")
    return WindowAuthority(
        window_id=window_id,
        window=expected_window,
        registry_root_sha256=str(resolved.registry["registry_root_sha256"]),
        manifest_path=resolved.source_manifest_path,
        manifest_root_sha256=str(manifest["manifest_root_sha256"]),
        m1=m1,
        ticks=ticks,
    )


@dataclass(frozen=True)
class TickSeries:
    times_us: np.ndarray
    bid: np.ndarray
    ask: np.ndarray


@dataclass(frozen=True)
class M1Series:
    times_us: np.ndarray
    opens: np.ndarray
    highs: np.ndarray
    lows: np.ndarray
    closes: np.ndarray


def load_tick_series(record: SourceRecord) -> TickSeries:
    times = np.empty(record.row_count, dtype=np.int64)
    bid = np.empty(record.row_count, dtype=np.float64)
    ask = np.empty(record.row_count, dtype=np.float64)
    digest = hashlib.sha256()
    count = 0
    with record.path.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                digest.update(raw)
                continue
            digest.update(raw)
            if count >= record.row_count:
                raise FCRefusal(f"tick_rows_exceed_manifest:{record.logical_path}")
            try:
                row = json.loads(raw)
                times[count] = true_utc_tick_time_us(row)
                bid[count] = float(row["bid"])
                ask[count] = float(row["ask"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise FCRefusal(
                    f"tick_row_invalid:{record.logical_path}:{line_number}"
                ) from exc
            count += 1
    if count != record.row_count or digest.hexdigest() != record.sha256:
        raise FCRefusal(f"tick_source_binding_mismatch:{record.logical_path}")
    if np.any(times[1:] < times[:-1]) or not np.isfinite(bid).all() or not np.isfinite(ask).all():
        raise FCRefusal(f"tick_source_order_or_numeric_invalid:{record.logical_path}")
    return TickSeries(times_us=times, bid=bid, ask=ask)


def load_m1_series(record: SourceRecord) -> M1Series:
    if sha256_file(record.path) != record.sha256:
        raise FCRefusal(f"m1_source_binding_mismatch:{record.logical_path}")
    times: list[int] = []
    opens: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    with record.path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"time", "open", "high", "low", "close"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise FCRefusal(f"m1_columns_invalid:{record.logical_path}")
        for row_number, row in enumerate(reader, start=2):
            try:
                timestamp = parse_utc_us(row["time"])
                values = tuple(float(row[key]) for key in ("open", "high", "low", "close"))
            except (KeyError, TypeError, ValueError) as exc:
                raise FCRefusal(
                    f"m1_row_invalid:{record.logical_path}:{row_number}"
                ) from exc
            if (times and timestamp <= times[-1]) or values[2] > values[1] or not all(
                math.isfinite(value) for value in values
            ):
                raise FCRefusal(f"m1_order_or_numeric_invalid:{record.logical_path}:{row_number}")
            times.append(timestamp)
            opens.append(values[0])
            highs.append(values[1])
            lows.append(values[2])
            closes.append(values[3])
    if len(times) != record.row_count:
        raise FCRefusal(f"m1_row_count_mismatch:{record.logical_path}")
    return M1Series(
        times_us=np.asarray(times, dtype=np.int64),
        opens=np.asarray(opens, dtype=np.float64),
        highs=np.asarray(highs, dtype=np.float64),
        lows=np.asarray(lows, dtype=np.float64),
        closes=np.asarray(closes, dtype=np.float64),
    )


@dataclass(frozen=True)
class PathArrays:
    values: np.ndarray
    times_us: np.ndarray
    deadline_eligible: np.ndarray
    source_mode: str


def signed_values(prices: np.ndarray, *, entry: float, distance: float, side: str) -> np.ndarray:
    if side == "LONG":
        return (prices - entry) / distance
    if side == "SHORT":
        return (entry - prices) / distance
    raise FCRefusal(f"side_invalid:{side}")


def tick_path(
    series: TickSeries,
    *,
    decision_us: int,
    horizon_us: int,
    entry: float,
    stop: float,
    side: str,
    path_start_us: int | None = None,
) -> PathArrays | None:
    lower_bound = decision_us if path_start_us is None else int(path_start_us)
    if not decision_us <= lower_bound < horizon_us:
        raise FCRefusal("executed_path_start_outside_decision_horizon")
    start = int(np.searchsorted(series.times_us, lower_bound, side="right"))
    end = int(np.searchsorted(series.times_us, horizon_us, side="right"))
    if start >= end:
        return None
    distance = abs(entry - stop)
    quote = series.bid[start:end] if side == "LONG" else series.ask[start:end]
    values = signed_values(quote, entry=entry, distance=distance, side=side)
    times = series.times_us[start:end]
    return PathArrays(
        values=values,
        times_us=times,
        deadline_eligible=np.ones(len(values), dtype=np.bool_),
        source_mode="ORDERED_TICK",
    )


def normalized_m1_arrays(
    *,
    times_us: np.ndarray,
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    entry: float,
    stop: float,
    side: str,
    shuffled_seed: int | None = None,
) -> tuple[PathArrays, PathArrays]:
    distance = abs(entry - stop)
    if not math.isfinite(distance) or distance <= 0:
        raise FCRefusal("entry_stop_geometry_invalid")
    open_r = signed_values(opens, entry=entry, distance=distance, side=side)
    raw_high_r = signed_values(highs, entry=entry, distance=distance, side=side)
    raw_low_r = signed_values(lows, entry=entry, distance=distance, side=side)
    high_r = np.maximum(raw_high_r, raw_low_r)
    low_r = np.minimum(raw_high_r, raw_low_r)
    close_r = signed_values(closes, entry=entry, distance=distance, side=side)
    if shuffled_seed is not None:
        order = np.arange(len(times_us))
        random.Random(int(shuffled_seed)).shuffle(order)
        close_delta = close_r[order] - open_r[order]
        high_offset = high_r[order] - open_r[order]
        low_offset = low_r[order] - open_r[order]
        levels = np.concatenate(([0.0], np.cumsum(close_delta[:-1])))
        open_r = levels
        high_r = levels + high_offset
        low_r = levels + low_offset
        close_r = levels + close_delta
    repeated_times = np.repeat(times_us, 4)
    eligible = np.zeros(len(repeated_times), dtype=np.bool_)
    eligible[3::4] = True
    high_first = np.column_stack((open_r, high_r, low_r, close_r)).reshape(-1)
    low_first = np.column_stack((open_r, low_r, high_r, close_r)).reshape(-1)
    return (
        PathArrays(high_first, repeated_times, eligible, "M1_CONSERVATIVE"),
        PathArrays(low_first, repeated_times, eligible, "M1_CONSERVATIVE"),
    )


def sidecar_m1_paths(
    observations: Sequence[Mapping[str, Any]],
    *,
    entry: float,
    stop: float,
    side: str,
    shuffled_seed: int | None = None,
) -> tuple[PathArrays, PathArrays]:
    if not observations:
        raise FCRefusal("sidecar_observations_empty")
    times = np.fromiter(
        (parse_utc_us(row.get("time_utc")) for row in observations),
        dtype=np.int64,
        count=len(observations),
    )
    arrays = {
        key: np.fromiter(
            (float(row[key]) for row in observations),
            dtype=np.float64,
            count=len(observations),
        )
        for key in ("open", "high", "low", "close")
    }
    return normalized_m1_arrays(
        times_us=times,
        opens=arrays["open"],
        highs=arrays["high"],
        lows=arrays["low"],
        closes=arrays["close"],
        entry=entry,
        stop=stop,
        side=side,
        shuffled_seed=shuffled_seed,
    )


def series_m1_paths(
    series: M1Series,
    *,
    decision_us: int,
    horizon_us: int,
    entry: float,
    stop: float,
    side: str,
    shuffled_seed: int | None = None,
) -> tuple[PathArrays, PathArrays] | None:
    start = int(np.searchsorted(series.times_us, decision_us, side="right"))
    end = int(np.searchsorted(series.times_us, horizon_us, side="right"))
    if start >= end:
        return None
    return normalized_m1_arrays(
        times_us=series.times_us[start:end],
        opens=series.opens[start:end],
        highs=series.highs[start:end],
        lows=series.lows[start:end],
        closes=series.closes[start:end],
        entry=entry,
        stop=stop,
        side=side,
        shuffled_seed=shuffled_seed,
    )


def shuffled_tick_path(path: PathArrays, *, seed: int) -> PathArrays:
    if not len(path.values):
        return path
    increments = np.diff(np.concatenate(([0.0], path.values)))
    order = np.arange(len(increments))
    random.Random(int(seed)).shuffle(order)
    values = np.cumsum(increments[order])
    return PathArrays(values, path.times_us, path.deadline_eligible, "ORDERED_TICK_SHUFFLE")


@dataclass(frozen=True)
class FastReplay:
    gross_r: float
    net_r: float
    exit_reason: str
    exit_index: int
    exit_time_us: int
    exit_r: float
    partial_realized_r: float
    remaining_fraction: float
    trigger_touched: bool
    mfe_r: float
    protective_floor_r: float
    source_mode: str
    ambiguity: bool = False


def first_true(mask: np.ndarray, *, offset: int = 0) -> int | None:
    indices = np.flatnonzero(mask)
    return None if not len(indices) else int(indices[0]) + offset


def fast_replay_one(
    spec: ExitOverlaySpec,
    path: PathArrays,
    *,
    decision_us: int,
    cost_r: float,
) -> FastReplay:
    values = path.values
    if not len(values):
        raise FCRefusal("fast_replay_empty_path")
    stop_index = first_true(values <= spec.hard_stop_r + TOL)
    target_index = first_true(values >= spec.hard_target_r - TOL)
    deadline_index: int | None = None
    if spec.time_box_minutes is not None:
        deadline = decision_us + spec.time_box_minutes * MICROSECONDS_PER_MINUTE
        deadline_index = first_true(path.deadline_eligible & (path.times_us >= deadline))
    trigger_index = (
        first_true(values >= float(spec.trigger_r) - TOL)
        if spec.trigger_r is not None
        else None
    )

    floor_index: int | None = None
    floor_exit_r = spec.hard_stop_r
    floor_reason = "protective_floor"
    if trigger_index is not None and spec.move_stop_to_break_even:
        start = trigger_index + 1
        if start < len(values):
            floor_index = first_true(values[start:] <= TOL, offset=start)
            floor_exit_r = 0.0
            floor_reason = "break_even_floor"
    if trigger_index is not None and spec.giveback_gap_r is not None:
        start = trigger_index + 1
        if start < len(values):
            prior_mfe = np.maximum.accumulate(values[trigger_index:-1])
            floors = np.maximum(spec.hard_stop_r, prior_mfe - spec.giveback_gap_r)
            relative = first_true(values[start:] <= floors + TOL)
            if relative is not None:
                floor_index = start + relative
                floor_exit_r = float(floors[relative])
                floor_reason = "giveback_floor"

    candidates: list[tuple[int, int, str, float]] = [
        (len(values) - 1, 4, "horizon_terminal_mark", float(values[-1]))
    ]
    if stop_index is not None:
        candidates.append((stop_index, 0, "hard_stop", spec.hard_stop_r))
    if floor_index is not None:
        candidates.append((floor_index, 1, floor_reason, floor_exit_r))
    if deadline_index is not None:
        candidates.append(
            (
                deadline_index,
                2,
                "time_box",
                min(float(values[deadline_index]), float(spec.hard_target_r)),
            )
        )
    if target_index is not None:
        # The frozen protocol says an *earlier* target wins.  M1 path expansion
        # emits open/extrema/close at one timestamp, so an extrema touch at the
        # executable deadline timestamp is a collision, not an earlier event.
        # Move only that target's ordering index to the deadline index; stop and
        # floor events retain their actual path ordering and higher precedence.
        target_order_index = target_index
        if (
            deadline_index is not None
            and path.times_us[target_index] == path.times_us[deadline_index]
        ):
            target_order_index = deadline_index
        candidates.append(
            (target_order_index, 3, "hard_target", spec.hard_target_r)
        )
    exit_index, _, reason, exit_r = min(candidates, key=lambda item: (item[0], item[1]))

    trigger_touched = False
    partial_realized = 0.0
    remaining = 1.0
    if trigger_index is not None:
        trigger_touched = trigger_index < exit_index or (
            trigger_index == exit_index
            and reason in {"hard_target", "horizon_terminal_mark"}
        )
    if trigger_touched and spec.partial_fraction:
        partial_realized = spec.partial_fraction * float(spec.trigger_r)
        remaining -= spec.partial_fraction
    gross = partial_realized + remaining * float(exit_r)

    protective_floor = spec.hard_stop_r
    if trigger_touched and spec.move_stop_to_break_even:
        protective_floor = max(protective_floor, 0.0)
    if (
        trigger_touched
        and spec.giveback_gap_r is not None
    ):
        # Protective state is updated after an ordinary observation, including
        # the final horizon observation.  It is not updated after an observation
        # that closes at stop/floor/deadline/target.
        history_end = exit_index + int(reason == "horizon_terminal_mark")
        if history_end > trigger_index:
            prior_best = max(
                0.0,
                float(np.max(values[trigger_index:history_end])),
            )
            protective_floor = max(
                protective_floor,
                prior_best - spec.giveback_gap_r,
            )
    return FastReplay(
        gross_r=float(gross),
        net_r=float(gross - cost_r),
        exit_reason=reason,
        exit_index=exit_index,
        exit_time_us=int(path.times_us[exit_index]),
        exit_r=float(exit_r),
        partial_realized_r=float(partial_realized),
        remaining_fraction=float(remaining),
        trigger_touched=trigger_touched,
        mfe_r=max(0.0, float(np.max(values[: exit_index + 1]))),
        protective_floor_r=float(protective_floor),
        source_mode=path.source_mode,
    )


def replay_path_options(
    spec: ExitOverlaySpec,
    options: Sequence[PathArrays],
    *,
    decision_us: int,
    cost_r: float,
) -> FastReplay:
    results = tuple(
        fast_replay_one(spec, path, decision_us=decision_us, cost_r=cost_r)
        for path in options
    )
    selected = min(results, key=lambda result: (result.net_r, result.exit_reason))
    ambiguity = any(
        result.exit_reason != results[0].exit_reason
        or abs(result.gross_r - results[0].gross_r) > TOL
        for result in results[1:]
    )
    return dataclasses.replace(selected, ambiguity=ambiguity)


def verify_fast_path(specs: Sequence[ExitOverlaySpec]) -> dict[str, Any]:
    """Prove the NumPy formula agrees with the reference state machine."""

    rng = random.Random(3150)
    checked = 0
    for case in range(80):
        level = 0.0
        path_values: list[float] = []
        for _ in range(120):
            level += rng.uniform(-0.32, 0.34)
            path_values.append(level)
        # Deterministic excursions make every family primitive reachable while
        # the random walk varies ordering and ratchet history.
        if case % 4 == 0:
            path_values[9] = 0.55
            path_values[19] = -0.05
        elif case % 4 == 1:
            path_values[14] = 1.3
            path_values[24] = 0.7
        elif case % 4 == 2:
            path_values[34] = 2.1
        else:
            path_values[44] = -1.1
        values = np.asarray(path_values, dtype=np.float64)
        times = np.asarray(
            [
                1_000_000_000 + (index + 1) * MICROSECONDS_PER_MINUTE
                for index in range(120)
            ],
            dtype=np.int64,
        )
        eligible = np.ones(len(values), dtype=np.bool_)
        path = PathArrays(values, times, eligible, "FAST_EQUIVALENCE")
        points = tuple(
            ExitPathPoint(
                time_us=int(times[index]),
                signed_r=float(value),
                deadline_eligible=True,
                source_index=index,
            )
            for index, value in enumerate(values)
        )
        for spec in specs:
            cost = 0.137
            reference = replay_signed_path(
                spec,
                points,
                decision_time_us=1_000_000_000,
                cost_r=cost,
                source_mode="FAST_EQUIVALENCE",
            )
            fast = fast_replay_one(
                spec,
                path,
                decision_us=1_000_000_000,
                cost_r=cost,
            )
            if (
                reference.gross_r is None
                or abs(reference.gross_r - fast.gross_r) > 1e-10
                or abs(reference.net_r - fast.net_r) > 1e-10
                or reference.exit_reason != fast.exit_reason
                or reference.exit_time_us != fast.exit_time_us
                or reference.exit_source_index != fast.exit_index
                or abs(reference.exit_r_on_remaining - fast.exit_r) > 1e-10
                or abs(reference.partial_realized_r - fast.partial_realized_r) > 1e-10
                or abs(reference.remaining_fraction - fast.remaining_fraction) > 1e-10
                or reference.trigger_touched != fast.trigger_touched
                or abs(reference.mfe_r - fast.mfe_r) > 1e-10
                or abs(reference.protective_floor_r - fast.protective_floor_r) > 1e-10
            ):
                raise FCRefusal(
                    "fast_reference_mismatch:"
                    f"case={case}:variant={spec.variant_id}:"
                    f"reference={reference}:fast={fast}"
                )
            checked += 1
    return {
        "status": "PASS",
        "seed": 3150,
        "random_paths": 80,
        "variants": len(specs),
        "comparisons": checked,
        "reference": "src.research_infra.exit_overlay.replay_signed_path",
    }


@dataclass
class DatasetEvaluation:
    name: str
    variant_ids: tuple[str, ...]
    days: np.ndarray
    gross: np.ndarray
    net: np.ndarray
    ambiguity: np.ndarray
    source_modes: np.ndarray
    residual_mask: np.ndarray | None
    source_identity_gross: np.ndarray | None
    source_identity_net: np.ndarray | None
    exit_counts: tuple[Counter[str], ...]
    trigger_counts: np.ndarray
    records: list[dict[str, Any]]
    cases: list["PathCase"]
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class PathCase:
    key: tuple[str, str, str, str]
    decision_us: int
    entry_time_us: int
    horizon_us: int
    entry: float
    stop: float
    cost_r: float
    side: str
    source_mode: str
    actual_options: tuple[PathArrays, ...]
    flipped_options: tuple[PathArrays, ...]
    m1_raw: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None


def load_trade_rows(path: Path, *, expected: int, month: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("trades") or []
    if len(rows) != expected:
        raise FCRefusal(f"trade_table_count:{path}:{len(rows)}!={expected}")
    keys: set[tuple[str, str, str, str]] = set()
    for row in rows:
        key = composite_key(row)
        if key in keys:
            raise FCRefusal(f"trade_table_duplicate_composite_key:{key}")
        if not key[1].startswith(month):
            raise FCRefusal(f"trade_table_month_drift:{path}:{key[1]}")
        keys.add(key)
    return rows, {
        "path": str(path),
        "sha256": sha256_file(path),
        "rows": len(rows),
        "unique_composite_keys": len(keys),
    }


def load_tick_cache(authority: WindowAuthority) -> tuple[dict[str, TickSeries], list[dict[str, Any]]]:
    cache: dict[str, TickSeries] = {}
    bindings: list[dict[str, Any]] = []
    for symbol, record in sorted(authority.ticks.items()):
        cache[symbol] = load_tick_series(record)
        bindings.append(
            {
                "symbol": symbol,
                "timeframe": "TICK",
                "path": str(record.path),
                "logical_path": record.logical_path,
                "sha256": record.sha256,
                "rows": record.row_count,
                "authenticated": True,
            }
        )
    return cache, bindings


def _m1_slice_arrays(
    series: M1Series,
    *,
    path_start_us: int,
    horizon_us: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    start = int(np.searchsorted(series.times_us, path_start_us, side="right"))
    end = int(np.searchsorted(series.times_us, horizon_us, side="right"))
    if start >= end:
        return None
    return (
        series.times_us[start:end],
        series.opens[start:end],
        series.highs[start:end],
        series.lows[start:end],
        series.closes[start:end],
    )


def _m1_paths_from_raw(
    raw: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    *,
    entry: float,
    stop: float,
    side: str,
    shuffled_seed: int | None = None,
) -> tuple[PathArrays, PathArrays]:
    times, opens, highs, lows, closes = raw
    return normalized_m1_arrays(
        times_us=times,
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
        entry=entry,
        stop=stop,
        side=side,
        shuffled_seed=shuffled_seed,
    )


def build_executed_case(
    row: Mapping[str, Any],
    *,
    authority: WindowAuthority,
    tick_cache: Mapping[str, TickSeries],
    m1_cache: dict[str, M1Series],
    m1_bindings: list[dict[str, Any]],
) -> PathCase:
    key = composite_key(row)
    _, decision_text, symbol, side = key
    decision_us = parse_utc_us(decision_text)
    horizon_us = decision_us + HORIZON_MINUTES * MICROSECONDS_PER_MINUTE
    entry_time_text = str(row.get("entry_time_utc") or "")
    entry_time_us = parse_utc_us(entry_time_text)
    if not decision_us <= entry_time_us < horizon_us:
        raise FCRefusal(f"executed_entry_time_outside_decision_horizon:{key}")
    entry = float(row["entry_price"])
    stop = float(row["stop_loss"])
    cost = float(row["cost_r"])
    if not all(math.isfinite(value) for value in (entry, stop, cost)) or entry == stop or cost < 0:
        raise FCRefusal(f"executed_geometry_or_cost_invalid:{key}")
    opposite = "SHORT" if side == "LONG" else "LONG"
    if symbol in tick_cache:
        actual = tick_path(
            tick_cache[symbol],
            decision_us=decision_us,
            horizon_us=horizon_us,
            entry=entry,
            stop=stop,
            side=side,
            path_start_us=entry_time_us,
        )
        flipped = tick_path(
            tick_cache[symbol],
            decision_us=decision_us,
            horizon_us=horizon_us,
            entry=entry,
            stop=stop,
            side=opposite,
            path_start_us=entry_time_us,
        )
        if actual is not None and flipped is not None:
            return PathCase(
                key=key,
                decision_us=decision_us,
                entry_time_us=entry_time_us,
                horizon_us=horizon_us,
                entry=entry,
                stop=stop,
                cost_r=cost,
                side=side,
                source_mode="ORDERED_TICK",
                actual_options=(actual,),
                flipped_options=(flipped,),
                m1_raw=None,
            )

    record = authority.m1.get(symbol)
    if record is None:
        raise FCRefusal(f"executed_m1_source_missing:{authority.window_id}:{symbol}")
    if symbol not in m1_cache:
        m1_cache[symbol] = load_m1_series(record)
        m1_bindings.append(
            {
                "symbol": symbol,
                "timeframe": "M1",
                "path": str(record.path),
                "logical_path": record.logical_path,
                "sha256": record.sha256,
                "rows": record.row_count,
                "authenticated": True,
            }
        )
    raw = _m1_slice_arrays(
        m1_cache[symbol], path_start_us=entry_time_us, horizon_us=horizon_us
    )
    if raw is None:
        raise FCRefusal(f"executed_path_source_gap:{key}")
    return PathCase(
        key=key,
        decision_us=decision_us,
        entry_time_us=entry_time_us,
        horizon_us=horizon_us,
        entry=entry,
        stop=stop,
        cost_r=cost,
        side=side,
        source_mode="M1_CONSERVATIVE",
        actual_options=_m1_paths_from_raw(raw, entry=entry, stop=stop, side=side),
        flipped_options=_m1_paths_from_raw(raw, entry=entry, stop=stop, side=opposite),
        m1_raw=raw,
    )


def compact_replay(result: FastReplay) -> dict[str, Any]:
    return {
        "gross_r": round(result.gross_r, 10),
        "net_r": round(result.net_r, 10),
        "exit_reason": result.exit_reason,
        "exit_time_utc": iso_from_us(result.exit_time_us),
        "partial_realized_r": round(result.partial_realized_r, 10),
        "remaining_fraction": round(result.remaining_fraction, 10),
        "trigger_touched": result.trigger_touched,
        "source_mode": result.source_mode,
        "m1_ordering_ambiguous": result.ambiguity,
    }


def evaluate_executed(
    *,
    name: str,
    rows: Sequence[Mapping[str, Any]],
    specs: Sequence[ExitOverlaySpec],
    authority: WindowAuthority,
    tick_cache: Mapping[str, TickSeries],
) -> tuple[DatasetEvaluation, list[dict[str, Any]]]:
    n_rows = len(rows)
    n_variants = len(specs)
    gross = np.empty((n_rows, n_variants), dtype=np.float64)
    net = np.empty((n_rows, n_variants), dtype=np.float64)
    ambiguity = np.zeros((n_rows, n_variants), dtype=np.bool_)
    source_modes = np.empty(n_rows, dtype="U20")
    days = np.empty(n_rows, dtype="U10")
    source_identity_gross = np.full(n_rows, np.nan, dtype=np.float64)
    source_identity_net = np.full(n_rows, np.nan, dtype=np.float64)
    exit_counts = tuple(Counter() for _ in specs)
    trigger_counts = np.zeros(n_variants, dtype=np.int64)
    records: list[dict[str, Any]] = []
    cases: list[PathCase] = []
    m1_cache: dict[str, M1Series] = {}
    m1_bindings: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows):
        case = build_executed_case(
            row,
            authority=authority,
            tick_cache=tick_cache,
            m1_cache=m1_cache,
            m1_bindings=m1_bindings,
        )
        cases.append(case)
        source_modes[row_index] = case.source_mode
        days[row_index] = case.key[1][:10]
        if isinstance(row.get("gross_r"), (int, float)):
            source_identity_gross[row_index] = float(row["gross_r"])
        if isinstance(row.get("net_r"), (int, float)):
            source_identity_net[row_index] = float(row["net_r"])
        overlay_rows: dict[str, Any] = {}
        for variant_index, overlay in enumerate(specs):
            result = replay_path_options(
                overlay,
                case.actual_options,
                decision_us=case.decision_us,
                cost_r=case.cost_r,
            )
            gross[row_index, variant_index] = result.gross_r
            net[row_index, variant_index] = result.net_r
            ambiguity[row_index, variant_index] = result.ambiguity
            exit_counts[variant_index][result.exit_reason] += 1
            trigger_counts[variant_index] += int(result.trigger_touched)
            overlay_rows[overlay.variant_id] = compact_replay(result)
        records.append(
            {
                "candidate_id": case.key[0],
                "decision_time_utc": case.key[1],
                "entry_time_utc": iso_from_us(case.entry_time_us),
                "entry_delay_seconds": round(
                    (case.entry_time_us - case.decision_us) / 1_000_000.0, 6
                ),
                "path_eligibility": "strictly_after_recorded_entry_time",
                "symbol": case.key[2],
                "side": case.key[3],
                "cost_r": case.cost_r,
                "source_mode": case.source_mode,
                "source_identity_gross_r": (
                    float(row["gross_r"])
                    if isinstance(row.get("gross_r"), (int, float))
                    else None
                ),
                "source_identity_net_r": (
                    float(row["net_r"])
                    if isinstance(row.get("net_r"), (int, float))
                    else None
                ),
                "overlays": overlay_rows,
            }
        )
    diagnostics = {
        "rows": n_rows,
        "unique_composite_keys": len({case.key for case in cases}),
        "source_modes": dict(Counter(source_modes.tolist())),
        "entry_path_eligibility": "strictly_after_recorded_entry_time",
        "delayed_entry_rows": sum(
            case.entry_time_us > case.decision_us for case in cases
        ),
        "maximum_entry_delay_seconds": max(
            (case.entry_time_us - case.decision_us) / 1_000_000.0
            for case in cases
        ),
        "guarded_fallback_joins": 0,
        "ambiguous_or_duplicate_joins": 0,
    }
    return (
        DatasetEvaluation(
            name=name,
            variant_ids=tuple(spec.variant_id for spec in specs),
            days=days,
            gross=gross,
            net=net,
            ambiguity=ambiguity,
            source_modes=source_modes,
            residual_mask=None,
            source_identity_gross=source_identity_gross,
            source_identity_net=source_identity_net,
            exit_counts=exit_counts,
            trigger_counts=trigger_counts,
            records=records,
            cases=cases,
            diagnostics=diagnostics,
        ),
        m1_bindings,
    )


def pool_row_is_residual(row: Mapping[str, Any]) -> bool:
    return row.get("broker_pretrade_cost_executable") is True and str(
        row.get("selector_action") or ""
    ) in {"trade", "open-reduced-risk", "reduce-risk"}


def residual_choice_set_count(payload: Mapping[str, Any]) -> int:
    """Read the frozen FA residual-A count without weakening its schema."""

    arm_a = payload.get("A")
    if not isinstance(arm_a, Mapping):
        raise FCRefusal("residual_choice_set_A_missing")
    total = arm_a.get("total")
    if not isinstance(total, Mapping):
        raise FCRefusal("residual_choice_set_total_missing")
    count = total.get("n")
    if isinstance(count, bool) or not isinstance(count, int):
        raise FCRefusal("residual_choice_set_count_invalid")
    return count


def _validate_sidecar_pair(
    pool_row: Mapping[str, Any],
    sidecar: Mapping[str, Any],
) -> tuple[tuple[str, str, str, str], int, int]:
    expected = composite_key(pool_row)
    actual = composite_key(sidecar)
    if actual != expected:
        raise FCRefusal(f"pool_sidecar_composite_join_mismatch:{actual}!={expected}")
    if sidecar.get("schema") != "gtos-session-ck-ordered-path-sidecar-v1":
        raise FCRefusal(f"sidecar_schema_drift:{expected}")
    decision_us = parse_utc_us(expected[1])
    horizon_us = parse_utc_us(sidecar.get("horizon_end_utc"))
    if horizon_us != decision_us + HORIZON_MINUTES * MICROSECONDS_PER_MINUTE:
        raise FCRefusal(f"sidecar_horizon_drift:{expected}")
    observations = sidecar.get("ordered_path_observations")
    if not isinstance(observations, list) or not observations:
        raise FCRefusal(f"sidecar_observations_missing:{expected}")
    previous = decision_us
    for observation in observations:
        timestamp = parse_utc_us(observation.get("time_utc"))
        if timestamp <= previous or timestamp > horizon_us:
            raise FCRefusal(f"sidecar_observation_window_or_order:{expected}")
        previous = timestamp
    return expected, decision_us, horizon_us


def pool_paths(
    *,
    pool_row: Mapping[str, Any],
    sidecar: Mapping[str, Any],
    decision_us: int,
    horizon_us: int,
    tick_cache: Mapping[str, TickSeries],
    side_override: str | None = None,
    shuffle_seed: int | None = None,
) -> tuple[tuple[PathArrays, ...], str, bool]:
    symbol = str(pool_row["symbol"])
    side = str(side_override or pool_row["side"]).upper()
    entry = float(pool_row["entry_price"])
    stop = float(pool_row["stop_loss"])
    tick_pointer = sidecar.get("ordered_tick_source")
    if symbol in tick_cache and isinstance(tick_pointer, Mapping):
        record_pointer = tick_pointer
        if str(record_pointer.get("source_sha256") or "") == "":
            raise FCRefusal(f"sidecar_tick_pointer_hash_missing:{symbol}")
        path = tick_path(
            tick_cache[symbol],
            decision_us=decision_us,
            horizon_us=horizon_us,
            entry=entry,
            stop=stop,
            side=side,
        )
        if path is not None:
            if shuffle_seed is not None:
                path = shuffled_tick_path(path, seed=shuffle_seed)
            return (path,), path.source_mode, False
    options = sidecar_m1_paths(
        sidecar["ordered_path_observations"],
        entry=entry,
        stop=stop,
        side=side,
        shuffled_seed=shuffle_seed,
    )
    return options, "M1_CONSERVATIVE", bool(symbol in tick_cache and tick_pointer)


def evaluate_pool(
    *,
    specs: Sequence[ExitOverlaySpec],
    tick_cache: Mapping[str, TickSeries],
    pool_manifest: Mapping[str, Any],
) -> DatasetEvaluation:
    n_rows = int((pool_manifest.get("base_pool") or {}).get("rows") or 0)
    if n_rows != EXPECTED_POOL_ROWS:
        raise FCRefusal(f"pool_manifest_row_count:{n_rows}!={EXPECTED_POOL_ROWS}")
    n_variants = len(specs)
    gross = np.empty((n_rows, n_variants), dtype=np.float64)
    net = np.empty((n_rows, n_variants), dtype=np.float64)
    ambiguity = np.zeros((n_rows, n_variants), dtype=np.bool_)
    source_modes = np.empty(n_rows, dtype="U20")
    days = np.empty(n_rows, dtype="U10")
    residual_mask = np.zeros(n_rows, dtype=np.bool_)
    source_identity_net = np.full(n_rows, np.nan, dtype=np.float64)
    exit_counts = tuple(Counter() for _ in specs)
    trigger_counts = np.zeros(n_variants, dtype=np.int64)
    seen: set[tuple[str, str, str, str]] = set()
    tick_fallback = 0

    pool_iterator = iter_gzip_jsonl(POOL_PATH)
    sidecar_iterator = iter_gzip_jsonl(SIDECAR_PATH)
    source_inventory = pool_manifest.get("source_inventory") or {}
    for row_index in range(n_rows):
        try:
            pool_row = next(pool_iterator)
            sidecar = next(sidecar_iterator)
        except StopIteration as exc:
            raise FCRefusal(f"pool_or_sidecar_ended_early:{row_index}") from exc
        key, decision_us, horizon_us = _validate_sidecar_pair(pool_row, sidecar)
        if key in seen:
            raise FCRefusal(f"pool_duplicate_composite_key:{key}")
        seen.add(key)
        inventory = source_inventory.get(key[2]) or {}
        expected_m1 = inventory.get("m1") or {}
        if (
            str(sidecar.get("source_path") or "") != str(expected_m1.get("path") or "")
            or str(sidecar.get("source_sha256") or "")
            != str(expected_m1.get("sha256") or "")
        ):
            raise FCRefusal(f"sidecar_m1_binding_drift:{key}")
        expected_tick = inventory.get("tick")
        actual_tick = sidecar.get("ordered_tick_source")
        if expected_tick is None and actual_tick is not None:
            raise FCRefusal(f"sidecar_unexpected_tick_pointer:{key}")
        if expected_tick is not None:
            if not isinstance(actual_tick, Mapping) or (
                str(actual_tick.get("path") or "")
                != str(expected_tick.get("path") or "")
                or str(actual_tick.get("source_sha256") or "")
                != str(expected_tick.get("sha256") or "")
            ):
                raise FCRefusal(f"sidecar_tick_binding_drift:{key}")
        entry = float(pool_row["entry_price"])
        stop = float(pool_row["stop_loss"])
        cost = float(pool_row["cost_r"])
        if entry == stop or cost < 0 or not all(
            math.isfinite(value) for value in (entry, stop, cost)
        ):
            raise FCRefusal(f"pool_geometry_or_cost_invalid:{key}")
        options, mode, fell_back = pool_paths(
            pool_row=pool_row,
            sidecar=sidecar,
            decision_us=decision_us,
            horizon_us=horizon_us,
            tick_cache=tick_cache,
        )
        tick_fallback += int(fell_back)
        source_modes[row_index] = mode
        days[row_index] = key[1][:10]
        residual_mask[row_index] = pool_row_is_residual(pool_row)
        if isinstance(pool_row.get("opportunity_net_proxy_r"), (int, float)):
            source_identity_net[row_index] = float(pool_row["opportunity_net_proxy_r"])
        for variant_index, overlay in enumerate(specs):
            result = replay_path_options(
                overlay,
                options,
                decision_us=decision_us,
                cost_r=cost,
            )
            gross[row_index, variant_index] = result.gross_r
            net[row_index, variant_index] = result.net_r
            ambiguity[row_index, variant_index] = result.ambiguity
            exit_counts[variant_index][result.exit_reason] += 1
            trigger_counts[variant_index] += int(result.trigger_touched)
    try:
        extra_pool = next(pool_iterator)
    except StopIteration:
        extra_pool = None
    try:
        extra_sidecar = next(sidecar_iterator)
    except StopIteration:
        extra_sidecar = None
    if extra_pool is not None or extra_sidecar is not None:
        raise FCRefusal("pool_or_sidecar_has_extra_rows")
    residual_rows = int(np.sum(residual_mask))
    residual_expected = residual_choice_set_count(
        json.loads(JAN_RESIDUAL.read_text(encoding="utf-8"))
    )
    if residual_rows != residual_expected or residual_rows != 4509:
        raise FCRefusal(f"residual_choice_set_count:{residual_rows}!={residual_expected}")
    return DatasetEvaluation(
        name="january_pool",
        variant_ids=tuple(spec.variant_id for spec in specs),
        days=days,
        gross=gross,
        net=net,
        ambiguity=ambiguity,
        source_modes=source_modes,
        residual_mask=residual_mask,
        source_identity_gross=None,
        source_identity_net=source_identity_net,
        exit_counts=exit_counts,
        trigger_counts=trigger_counts,
        records=[],
        cases=[],
        diagnostics={
            "rows": n_rows,
            "unique_composite_keys": len(seen),
            "residual_choice_set_rows": residual_rows,
            "source_modes": dict(Counter(source_modes.tolist())),
            "tick_pointer_rows_falling_back_to_m1": tick_fallback,
            "guarded_fallback_joins": 0,
            "ambiguous_or_duplicate_joins": 0,
        },
    )


def sign_flip_p(values: Sequence[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    nonzero = array[np.abs(array) > 1e-12]
    if not len(nonzero):
        return {
            "p_one_sided": 1.0,
            "observed_mean": float(np.mean(array)) if len(array) else 0.0,
            "calendar_blocks": int(len(array)),
            "effective_nonzero_blocks": 0,
            "permutations": 1,
        }
    if len(nonzero) > 20:
        raise FCRefusal(f"sign_flip_block_count_exceeds_exact_limit:{len(nonzero)}")
    signed_sums = np.asarray([0.0], dtype=np.float64)
    for value in nonzero:
        signed_sums = np.concatenate((signed_sums + value, signed_sums - value))
    observed = float(np.mean(nonzero))
    permuted = signed_sums / len(nonzero)
    p_value = float(np.mean(permuted >= observed - 1e-12))
    return {
        "p_one_sided": p_value,
        "observed_mean": observed,
        "calendar_blocks": int(len(array)),
        "effective_nonzero_blocks": int(len(nonzero)),
        "permutations": int(len(permuted)),
    }


def bh_q_values(p_values: Sequence[float]) -> list[float]:
    m = len(p_values)
    if m != 40:
        raise FCRefusal(f"bh_family_denominator:{m}!=40")
    order = sorted(range(m), key=lambda index: (p_values[index], index))
    adjusted = [1.0] * m
    running = 1.0
    for rank_from_end, index in enumerate(reversed(order), start=1):
        rank = m - rank_from_end + 1
        candidate = min(1.0, float(p_values[index]) * m / rank)
        running = min(running, candidate)
        adjusted[index] = running
    return adjusted


def daily_values(
    values: np.ndarray,
    days: np.ndarray,
    dates: Sequence[str],
    *,
    aggregation: str,
) -> np.ndarray:
    result = np.zeros(len(dates), dtype=np.float64)
    for index, day in enumerate(dates):
        selected = values[days == day]
        if len(selected):
            result[index] = (
                float(np.sum(selected))
                if aggregation == "sum"
                else float(np.mean(selected))
            )
    return result


def metric_cell(
    dataset: DatasetEvaluation,
    *,
    variant_index: int,
    row_mask: np.ndarray,
    dates: Sequence[str],
    aggregation: str,
) -> dict[str, Any]:
    identity_index = dataset.variant_ids.index("V00_IDENTITY_CURRENT")
    net = dataset.net[row_mask, variant_index]
    gross = dataset.gross[row_mask, variant_index]
    identity_net = dataset.net[row_mask, identity_index]
    selected_days = dataset.days[row_mask]
    daily_net = daily_values(net, selected_days, dates, aggregation=aggregation)
    daily_identity = daily_values(
        identity_net, selected_days, dates, aggregation=aggregation
    )
    daily_delta = daily_net - daily_identity
    level_test = sign_flip_p(daily_net)
    improvement_test = sign_flip_p(daily_delta)
    mode_values = dataset.source_modes[row_mask].tolist()
    ambiguities = dataset.ambiguity[row_mask, variant_index]
    result = {
        "rows": int(len(net)),
        "dates": list(dates),
        "aggregation_unit": (
            "daily_sum_net_r" if aggregation == "sum" else "daily_mean_net_r_per_candidate"
        ),
        "total_gross_r": float(np.sum(gross)),
        "total_net_r": float(np.sum(net)),
        "mean_gross_r": float(np.mean(gross)) if len(gross) else None,
        "mean_net_r": float(np.mean(net)) if len(net) else None,
        "positive_rows": int(np.sum(net > 0.0)),
        "positive_share": float(np.mean(net > 0.0)) if len(net) else None,
        "identity_total_net_r": float(np.sum(identity_net)),
        "paired_improvement_total_net_r": float(np.sum(net - identity_net)),
        "paired_improvement_mean_net_r": (
            float(np.mean(net - identity_net)) if len(net) else None
        ),
        "daily_net_r": {
            day: float(value) for day, value in zip(dates, daily_net, strict=True)
        },
        "daily_paired_improvement_net_r": {
            day: float(value) for day, value in zip(dates, daily_delta, strict=True)
        },
        "level_test": level_test,
        "improvement_test": improvement_test,
        "source_modes": dict(Counter(mode_values)),
        "m1_ordering_ambiguity_rows": int(np.sum(ambiguities)),
        "rows_with_net_different_from_identity": int(
            np.sum(
                dataset.net[row_mask, variant_index]
                != dataset.net[row_mask, identity_index]
            )
        ),
        "trigger_touched_rows_full_dataset": int(dataset.trigger_counts[variant_index]),
        "exit_reasons_full_dataset": dict(dataset.exit_counts[variant_index]),
    }
    return result


def assign_family_q(
    cells: Mapping[str, dict[str, Any]],
    *,
    surface: str,
    variant_ids: Sequence[str],
) -> None:
    level_p = [float(cells[variant_id][surface]["level_test"]["p_one_sided"]) for variant_id in variant_ids]
    improvement_p = [
        float(cells[variant_id][surface]["improvement_test"]["p_one_sided"])
        for variant_id in variant_ids
    ]
    level_q = bh_q_values(level_p)
    improvement_q = bh_q_values(improvement_p)
    for index, variant_id in enumerate(variant_ids):
        cells[variant_id][surface]["level_test"]["q_bh_40"] = level_q[index]
        cells[variant_id][surface]["improvement_test"]["q_bh_40"] = improvement_q[index]


def identity_reproduction(
    dataset: DatasetEvaluation,
    *,
    tolerance: float = 1e-6,
) -> dict[str, Any]:
    identity_index = dataset.variant_ids.index("V00_IDENTITY_CURRENT")
    result: dict[str, Any] = {"tolerance_r": tolerance}
    for label, source, replayed in (
        ("gross", dataset.source_identity_gross, dataset.gross[:, identity_index]),
        ("net", dataset.source_identity_net, dataset.net[:, identity_index]),
    ):
        if source is None:
            continue
        valid = np.isfinite(source)
        deltas = replayed[valid] - source[valid]
        result[label] = {
            "comparable_rows": int(np.sum(valid)),
            "exact_within_tolerance": int(np.sum(np.abs(deltas) <= tolerance)),
            "mismatched_rows": int(np.sum(np.abs(deltas) > tolerance)),
            "max_abs_delta_r": float(np.max(np.abs(deltas))) if len(deltas) else None,
            "mean_delta_r": float(np.mean(deltas)) if len(deltas) else None,
            "sum_replayed_r": float(np.sum(replayed[valid])),
            "sum_source_r": float(np.sum(source[valid])),
        }
    return result


def build_january_cells(
    *,
    specs: Sequence[ExitOverlaySpec],
    executed: DatasetEvaluation,
    pool: DatasetEvaluation,
    train_dates: Sequence[str],
    holdout_dates: Sequence[str],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    cells: dict[str, dict[str, Any]] = {}
    executed_train = np.isin(executed.days, train_dates)
    executed_holdout = np.isin(executed.days, holdout_dates)
    pool_train = np.isin(pool.days, train_dates)
    pool_holdout = np.isin(pool.days, holdout_dates)
    if pool.residual_mask is None:
        raise FCRefusal("pool_residual_mask_missing")
    surfaces = (
        "january_executed_train",
        "january_executed_holdout",
        "january_residual_train",
        "january_residual_holdout",
        "january_full_pool_train",
        "january_full_pool_holdout",
    )
    for variant_index, overlay in enumerate(specs):
        cells[overlay.variant_id] = {
            "variant": dataclasses.asdict(overlay),
            "january_executed_train": metric_cell(
                executed,
                variant_index=variant_index,
                row_mask=executed_train,
                dates=train_dates,
                aggregation="sum",
            ),
            "january_executed_holdout": metric_cell(
                executed,
                variant_index=variant_index,
                row_mask=executed_holdout,
                dates=holdout_dates,
                aggregation="sum",
            ),
            "january_residual_train": metric_cell(
                pool,
                variant_index=variant_index,
                row_mask=pool_train & pool.residual_mask,
                dates=train_dates,
                aggregation="mean",
            ),
            "january_residual_holdout": metric_cell(
                pool,
                variant_index=variant_index,
                row_mask=pool_holdout & pool.residual_mask,
                dates=holdout_dates,
                aggregation="mean",
            ),
            "january_full_pool_train": metric_cell(
                pool,
                variant_index=variant_index,
                row_mask=pool_train,
                dates=train_dates,
                aggregation="mean",
            ),
            "january_full_pool_holdout": metric_cell(
                pool,
                variant_index=variant_index,
                row_mask=pool_holdout,
                dates=holdout_dates,
                aggregation="mean",
            ),
        }
    variant_ids = [spec.variant_id for spec in specs]
    for surface in surfaces:
        assign_family_q(cells, surface=surface, variant_ids=variant_ids)
    top_three = sorted(
        (spec.variant_id for spec in specs if spec.kind != "identity"),
        key=lambda variant_id: (
            -float(cells[variant_id]["january_executed_train"]["total_net_r"]),
            -float(
                cells[variant_id]["january_executed_train"][
                    "paired_improvement_total_net_r"
                ]
            ),
            variant_id,
        ),
    )[:3]
    return cells, top_three


def null_case_options(
    case: PathCase,
    *,
    control: str,
) -> tuple[PathArrays, ...]:
    if control == "SIDE_FLIP":
        return case.flipped_options
    if not control.startswith("SHUFFLE_"):
        raise FCRefusal(f"null_control_unknown:{control}")
    seed = int(control.split("_", 1)[1])
    if case.source_mode == "ORDERED_TICK":
        return (shuffled_tick_path(case.actual_options[0], seed=seed),)
    if case.m1_raw is None:
        raise FCRefusal(f"null_m1_raw_missing:{case.key}")
    return _m1_paths_from_raw(
        case.m1_raw,
        entry=case.entry,
        stop=case.stop,
        side=case.side,
        shuffled_seed=seed,
    )


def null_metric(
    *,
    variant_daily: np.ndarray,
    identity_daily: np.ndarray,
    aggregation: str,
) -> dict[str, Any]:
    delta = variant_daily - identity_daily
    return {
        "aggregation_unit": aggregation,
        "variant_daily": [float(value) for value in variant_daily],
        "identity_daily": [float(value) for value in identity_daily],
        "daily_improvement": [float(value) for value in delta],
        "variant_level": (
            float(np.sum(variant_daily))
            if aggregation == "daily_sum_net_r"
            else float(np.mean(variant_daily))
        ),
        "identity_level": (
            float(np.sum(identity_daily))
            if aggregation == "daily_sum_net_r"
            else float(np.mean(identity_daily))
        ),
        "improvement": (
            float(np.sum(delta))
            if aggregation == "daily_sum_net_r"
            else float(np.mean(delta))
        ),
        "improvement_test": sign_flip_p(delta),
    }


def executed_nulls(
    *,
    executed: DatasetEvaluation,
    identity: ExitOverlaySpec,
    selected: Sequence[ExitOverlaySpec],
    train_dates: Sequence[str],
) -> dict[str, Any]:
    date_index = {day: index for index, day in enumerate(train_dates)}
    controls = ("SIDE_FLIP", *(f"SHUFFLE_{seed}" for seed in NULL_SEEDS))
    output: dict[str, Any] = {spec.variant_id: {} for spec in selected}
    train_cases = [case for case in executed.cases if case.key[1][:10] in date_index]
    for control in controls:
        identity_daily = np.zeros(len(train_dates), dtype=np.float64)
        variant_daily = {
            spec.variant_id: np.zeros(len(train_dates), dtype=np.float64)
            for spec in selected
        }
        for case in train_cases:
            options = null_case_options(case, control=control)
            day_position = date_index[case.key[1][:10]]
            identity_result = replay_path_options(
                identity,
                options,
                decision_us=case.decision_us,
                cost_r=case.cost_r,
            )
            identity_daily[day_position] += identity_result.net_r
            for spec in selected:
                result = replay_path_options(
                    spec,
                    options,
                    decision_us=case.decision_us,
                    cost_r=case.cost_r,
                )
                variant_daily[spec.variant_id][day_position] += result.net_r
        for spec in selected:
            output[spec.variant_id][control] = null_metric(
                variant_daily=variant_daily[spec.variant_id],
                identity_daily=identity_daily,
                aggregation="daily_sum_net_r",
            )
    return output


def residual_nulls(
    *,
    identity: ExitOverlaySpec,
    selected: Sequence[ExitOverlaySpec],
    train_dates: Sequence[str],
    tick_cache: Mapping[str, TickSeries],
) -> dict[str, Any]:
    date_index = {day: index for index, day in enumerate(train_dates)}
    controls = ("SIDE_FLIP", *(f"SHUFFLE_{seed}" for seed in NULL_SEEDS))
    identity_sums = {
        control: np.zeros(len(train_dates), dtype=np.float64) for control in controls
    }
    variant_sums = {
        spec.variant_id: {
            control: np.zeros(len(train_dates), dtype=np.float64) for control in controls
        }
        for spec in selected
    }
    counts = np.zeros(len(train_dates), dtype=np.int64)
    pool_iterator = iter_gzip_jsonl(POOL_PATH)
    sidecar_iterator = iter_gzip_jsonl(SIDECAR_PATH)
    rows_seen = 0
    rows_used = 0
    for pool_row, sidecar in zip(pool_iterator, sidecar_iterator, strict=True):
        rows_seen += 1
        key, decision_us, horizon_us = _validate_sidecar_pair(pool_row, sidecar)
        day = key[1][:10]
        if day not in date_index or not pool_row_is_residual(pool_row):
            continue
        rows_used += 1
        day_position = date_index[day]
        counts[day_position] += 1
        side = key[3]
        opposite = "SHORT" if side == "LONG" else "LONG"
        for control in controls:
            if control == "SIDE_FLIP":
                options, _, _ = pool_paths(
                    pool_row=pool_row,
                    sidecar=sidecar,
                    decision_us=decision_us,
                    horizon_us=horizon_us,
                    tick_cache=tick_cache,
                    side_override=opposite,
                )
            else:
                options, _, _ = pool_paths(
                    pool_row=pool_row,
                    sidecar=sidecar,
                    decision_us=decision_us,
                    horizon_us=horizon_us,
                    tick_cache=tick_cache,
                    shuffle_seed=int(control.split("_", 1)[1]),
                )
            cost = float(pool_row["cost_r"])
            identity_result = replay_path_options(
                identity, options, decision_us=decision_us, cost_r=cost
            )
            identity_sums[control][day_position] += identity_result.net_r
            for spec in selected:
                result = replay_path_options(
                    spec, options, decision_us=decision_us, cost_r=cost
                )
                variant_sums[spec.variant_id][control][day_position] += result.net_r
    if rows_seen != EXPECTED_POOL_ROWS or np.any(counts == 0):
        raise FCRefusal(
            f"residual_null_stream_incomplete:seen={rows_seen}:counts={counts.tolist()}"
        )
    output: dict[str, Any] = {spec.variant_id: {} for spec in selected}
    for spec in selected:
        for control in controls:
            output[spec.variant_id][control] = null_metric(
                variant_daily=variant_sums[spec.variant_id][control] / counts,
                identity_daily=identity_sums[control] / counts,
                aggregation="daily_mean_net_r_per_candidate",
            )
    output["stream"] = {
        "pool_rows_seen": rows_seen,
        "residual_train_rows_used": rows_used,
        "daily_candidate_counts": {
            day: int(value) for day, value in zip(train_dates, counts, strict=True)
        },
    }
    return output


def concentration_check(metric: Mapping[str, Any]) -> dict[str, Any]:
    daily = np.asarray(
        list((metric.get("daily_paired_improvement_net_r") or {}).values()),
        dtype=np.float64,
    )
    total = float(np.sum(daily))
    leave_one_out = total - daily
    positive = daily[daily > 0]
    positive_sum = float(np.sum(positive))
    max_positive_share = (
        float(np.max(positive) / positive_sum) if positive_sum > 0 else None
    )
    return {
        "total_improvement_r": total,
        "leave_one_day_out_improvement_r": [float(value) for value in leave_one_out],
        "leave_one_day_out_all_positive": bool(np.all(leave_one_out > 0)),
        "positive_improvement_sum_r": positive_sum,
        "max_single_day_share_of_positive_improvement": max_positive_share,
        "no_single_day_exceeds_50_percent": bool(
            max_positive_share is not None and max_positive_share <= 0.5 + TOL
        ),
    }


def null_clean_check(
    *,
    actual_improvement: float,
    null_rows: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    comparisons = {
        control: {
            "null_improvement": float(row["improvement"]),
            "actual_strictly_greater": actual_improvement
            > float(row["improvement"]) + TOL,
        }
        for control, row in null_rows.items()
    }
    return {
        "actual_improvement": actual_improvement,
        "comparisons": comparisons,
        "passes": all(row["actual_strictly_greater"] for row in comparisons.values()),
    }


def build_gates(
    *,
    cells: Mapping[str, dict[str, Any]],
    top_three: Sequence[str],
    nulls: Mapping[str, Any],
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for variant_id in top_three:
        train = cells[variant_id]["january_executed_train"]
        holdout = cells[variant_id]["january_executed_holdout"]
        february = cells[variant_id]["february_executed_attribution"]
        residual_train = cells[variant_id]["january_residual_train"]
        residual_holdout = cells[variant_id]["january_residual_holdout"]
        concentration = concentration_check(train)
        executed_null = null_clean_check(
            actual_improvement=float(train["paired_improvement_total_net_r"]),
            null_rows=nulls["executed"][variant_id],
        )
        residual_null = null_clean_check(
            actual_improvement=float(residual_train["paired_improvement_mean_net_r"]),
            null_rows=nulls["residual"][variant_id],
        )
        executed_components = {
            "january_train_positive_level": float(train["total_net_r"]) > 0,
            "january_train_positive_improvement": float(
                train["paired_improvement_total_net_r"]
            )
            > 0,
            "january_train_q_improvement_lte_0p10": float(
                train["improvement_test"]["q_bh_40"]
            )
            <= 0.10,
            "january_holdout_positive_level": float(holdout["total_net_r"]) > 0,
            "january_holdout_positive_improvement": float(
                holdout["paired_improvement_total_net_r"]
            )
            > 0,
            "february_attribution_positive_level": float(february["total_net_r"]) > 0,
            "february_attribution_positive_improvement": float(
                february["paired_improvement_total_net_r"]
            )
            > 0,
            "leave_one_day_out_all_positive": concentration[
                "leave_one_day_out_all_positive"
            ],
            "no_single_day_exceeds_50_percent": concentration[
                "no_single_day_exceeds_50_percent"
            ],
            "null_clean": executed_null["passes"],
        }
        residual_components = {
            "january_train_positive_level": float(residual_train["mean_net_r"]) > 0,
            "january_train_positive_improvement": float(
                residual_train["paired_improvement_mean_net_r"]
            )
            > 0,
            "january_train_q_level_lte_0p10": float(
                residual_train["level_test"]["q_bh_40"]
            )
            <= 0.10,
            "january_train_q_improvement_lte_0p10": float(
                residual_train["improvement_test"]["q_bh_40"]
            )
            <= 0.10,
            "january_holdout_positive_level": float(residual_holdout["mean_net_r"]) > 0,
            "january_holdout_positive_improvement": float(
                residual_holdout["paired_improvement_mean_net_r"]
            )
            > 0,
            "null_clean": residual_null["passes"],
        }
        output[variant_id] = {
            "executed_gate_components": executed_components,
            "executed_persistence_gate_passes": all(executed_components.values()),
            "executed_concentration": concentration,
            "executed_null_clean": executed_null,
            "residual_gate_components": residual_components,
            "residual_persistence_gate_passes": all(residual_components.values()),
            "residual_null_clean": residual_null,
        }
    return output


def positivity_summary(
    *,
    cells: Mapping[str, Mapping[str, Any]],
    variant_ids: Sequence[str],
    top_three: Sequence[str],
) -> dict[str, Any]:
    def positive(surface: str, field: str, ids: Sequence[str]) -> list[str]:
        return [
            variant_id
            for variant_id in ids
            if isinstance(cells[variant_id].get(surface), Mapping)
            and isinstance(cells[variant_id][surface].get(field), (int, float))
            and float(cells[variant_id][surface][field]) > 0
        ]

    nonidentity = [variant_id for variant_id in variant_ids if variant_id != "V00_IDENTITY_CURRENT"]
    return {
        "january_executed_train_positive_variants": positive(
            "january_executed_train", "total_net_r", nonidentity
        ),
        "january_executed_holdout_positive_variants": positive(
            "january_executed_holdout", "total_net_r", nonidentity
        ),
        "february_frozen_positive_variants": positive(
            "february_executed_attribution", "total_net_r", top_three
        ),
        "january_residual_train_positive_variants": positive(
            "january_residual_train", "mean_net_r", nonidentity
        ),
        "january_residual_holdout_positive_variants": positive(
            "january_residual_holdout", "mean_net_r", nonidentity
        ),
    }


def check_heavy_slot() -> dict[str, Any]:
    output = subprocess.run(
        ["ps", "-axo", "pid=,command="],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout
    conflicts: list[dict[str, Any]] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        pid_text, _, command = stripped.partition(" ")
        if (
            "src.research_infra.train_engine.runner" in command
            and int(pid_text) != os.getpid()
        ):
            conflicts.append({"pid": int(pid_text), "command": command})
    if conflicts:
        raise FCRefusal(f"local_heavy_compute_slot_occupied:{conflicts}")
    return {
        "status": "ACQUIRED",
        "checked_at_utc": utc_now(),
        "conflicting_train_engine_processes": [],
    }


def validate_pool_bindings() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = json.loads(POOL_MANIFEST_PATH.read_text(encoding="utf-8"))
    if (
        manifest.get("schema") != "gtos-session-cq-path-complete-pool-v1"
        or manifest.get("march_2026_outcomes_read") is not False
        or manifest.get("february_2026_economics_read") is not False
        or int((manifest.get("base_pool") or {}).get("rows") or 0)
        != EXPECTED_POOL_ROWS
        or int((manifest.get("sidecar") or {}).get("rows") or 0)
        != EXPECTED_POOL_ROWS
    ):
        raise FCRefusal("cq_pool_manifest_boundary_or_count_invalid")
    actual_pool = sha256_file(POOL_PATH)
    actual_sidecar = sha256_file(SIDECAR_PATH)
    if actual_pool != (manifest.get("base_pool") or {}).get("sha256"):
        raise FCRefusal("cq_pool_hash_mismatch")
    if actual_sidecar != (manifest.get("sidecar") or {}).get("sha256"):
        raise FCRefusal("cq_sidecar_hash_mismatch")
    return manifest, [
        {
            "role": "january_full_pool",
            "path": str(POOL_PATH),
            "sha256": actual_pool,
            "rows": EXPECTED_POOL_ROWS,
            "authenticated": True,
        },
        {
            "role": "january_ordered_path_sidecar",
            "path": str(SIDECAR_PATH),
            "sha256": actual_sidecar,
            "rows": EXPECTED_POOL_ROWS,
            "observation_rows": int((manifest.get("sidecar") or {}).get("observation_rows") or 0),
            "authenticated": True,
        },
        {
            "role": "cq_pool_manifest",
            "path": str(POOL_MANIFEST_PATH),
            "sha256": sha256_file(POOL_MANIFEST_PATH),
            "authenticated": True,
        },
    ]


def valid_look_rows(
    *,
    specs: Sequence[ExitOverlaySpec],
    top_three: Sequence[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        rows.append(
            {
                "look_id": f"FC_OVERLAY_{spec.variant_id}",
                "look_type": "FORENSIC_DIAGNOSTIC",
                "billed": False,
                "variant_id": spec.variant_id,
                "january_surfaces": [
                    "executed_train",
                    "executed_holdout",
                    "residual_train",
                    "residual_holdout",
                    "full_pool_train",
                    "full_pool_holdout",
                ],
                "february_attribution_applied": True,
                "february_persistence_gate_role": spec.variant_id in top_three,
                "promotion_authority": False,
                "january_train_ranking_role": "TOP_THREE_FROZEN"
                if spec.variant_id in top_three
                else "FAMILY_COMPARATOR",
                "note": (
                    "February is owner_mandate_20260801 attribution only and has no fitting authority."
                    if spec.variant_id in top_three
                    else "January family cell; no March or live-forward outcome read."
                ),
            }
        )
    for variant_id in top_three:
        for control in ("SIDE_FLIP", *(f"SHUFFLE_{seed}" for seed in NULL_SEEDS)):
            rows.append(
                {
                    "look_id": f"FC_NULL_{variant_id}_{control}",
                    "look_type": "FORENSIC_DIAGNOSTIC",
                    "billed": False,
                    "variant_id": variant_id,
                    "null_control": control,
                    "surfaces": ["january_executed_train", "january_residual_train"],
                    "selection_authority": False,
                }
            )
    return rows


def look_rows(
    *,
    specs: Sequence[ExitOverlaySpec],
    top_three: Sequence[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Ledger valid and invalidated outcome evaluations without hiding reruns."""

    r0: list[dict[str, Any]] = []
    for row in valid_look_rows(specs=specs, top_three=())[: len(specs)]:
        r0.append(
            {
                **row,
                "look_id": f"FC_R0_SCHEMA_ABORT_{row['variant_id']}",
                "analysis_run_id": "FC_R0_SCHEMA_ABORT",
                "valid_for_final_result": False,
                "invalidated_reason": "residual_manifest_nested_count_schema_not_parsed",
                "february_attribution_applied": False,
                "february_persistence_gate_role": False,
                "january_surfaces": [
                    "executed_full_before_split",
                    "residual_and_full_pool_before_split",
                ],
                "note": "Run stopped before ranking, null controls, February, or result emission.",
            }
        )

    r1_top_three = (
        "V23_GB_T100_G010",
        "V29_TB_030",
        "V25_GB_T100_G030",
    )
    r1 = [
        {
            **row,
            "look_id": f"FC_R1_PREFILL_INVALID_{row['look_id']}",
            "analysis_run_id": "FC_R1_PREFILL_SEMANTICS_INVALIDATED",
            "valid_for_final_result": False,
            "invalidated_reason": "executed_exit_rules_observed_quotes_before_recorded_fill",
        }
        for row in valid_look_rows(specs=specs, top_three=r1_top_three)
    ]
    r2_top_three = (
        "V26_GB_T125_G010",
        "V27_GB_T125_G020",
        "V23_GB_T100_G010",
    )
    r2 = [
        {
            **row,
            "analysis_run_id": "FC_R2_ENTRY_ELIGIBLE_CORRECTED",
            "look_id": f"FC_R2_BROKER_EPOCH_INVALID_{row['look_id']}",
            "valid_for_final_result": False,
            "invalidated_reason": "raw_broker_time_msc_used_instead_of_lane_true_utc_timestamp",
        }
        for row in valid_look_rows(specs=specs, top_three=r2_top_three)
    ]
    final = [
        {
            **row,
            "analysis_run_id": "FC_R3_TRUE_UTC_ENTRY_ELIGIBLE",
            "valid_for_final_result": True,
            "invalidated_reason": None,
        }
        for row in valid_look_rows(specs=specs, top_three=top_three)
    ]
    runs = [
        {
            "analysis_run_id": "FC_R0_SCHEMA_ABORT",
            "status": "INVALIDATED_BEFORE_RESULT_EMISSION",
            "look_evaluation_events": len(r0),
            "reason": "The FA residual manifest stores A.total.n; the first analyzer version expected scalar A.total.",
            "outputs_emitted": False,
            "protocol_changed_after_outcome_read": False,
        },
        {
            "analysis_run_id": "FC_R1_PREFILL_SEMANTICS_INVALIDATED",
            "status": "INVALIDATED_AFTER_RESULT_EMISSION",
            "analysis_started_at_utc": "2026-08-01T04:17:04.168598+00:00",
            "look_evaluation_events": len(r1),
            "reason": "Identity audit exposed pre-fill quote eligibility on delayed executed entries.",
            "invalidated_physical_sha256": {
                "EXECUTED_OVERLAY_REPLAY.json": "1820a7dfa7cd30a2e8a095a17d1ab05eeda15f37569c7a490e70f71c1ccde3ef",
                "NULL_CONTROLS.json": "900e105acc5f5276cc65fd7d85cb35099b490c450c7a173abbdbd99b6c1d0852",
                "OVERLAY_RESULTS.json": "eea8e024927dd10e1a51c68d824eb78ee0349aad80ba1b1bf9cf1e13164803ad",
                "LOOK_MANIFEST.json": "920a99b473ea2e0850f20a38af9c4c84887afa42cf69a9bd732f437b9db5e187",
            },
            "protocol_changed_after_outcome_read": False,
        },
        {
            "analysis_run_id": "FC_R2_ENTRY_ELIGIBLE_CORRECTED",
            "status": "INVALIDATED_AFTER_RESULT_EMISSION",
            "analysis_started_at_utc": "2026-08-01T04:25:24.562688+00:00",
            "look_evaluation_events": len(r2),
            "reason": "The authenticated lane stores converted true UTC in ts_utc/time but preserves raw broker-wall time_msc; the analyzer incorrectly indexed ticks by time_msc.",
            "invalidated_physical_sha256": {
                "EXECUTED_OVERLAY_REPLAY.json": "f48f0dbf0dd0bd11dc1f5afeb0fa6e8989b62c8461c0b48789c394ee371558d3",
                "NULL_CONTROLS.json": "8a7be5bd6497654afa0a7c34b883db2d2efeee621d69f2d6595be56a8acfb4f0",
                "OVERLAY_RESULTS.json": "630d3e272edc2e80264e125c4a574de4fa89a12733c712c7a432ea16e3a9a1b6",
                "LOOK_MANIFEST.json": "04916cf8bc5e4529f0f06f5ddf221e9c08b7608ba9793ae19aa3eff762ded289",
            },
            "protocol_changed_after_outcome_read": False,
        },
        {
            "analysis_run_id": "FC_R3_TRUE_UTC_ENTRY_ELIGIBLE",
            "status": "VALID_FINAL",
            "look_evaluation_events": len(final),
            "reason": "Uses explicit lane-authoritative true UTC and paths strictly after recorded fill with the unchanged frozen cells.",
            "protocol_changed_after_outcome_read": False,
        },
    ]
    return [*r0, *r1, *r2, *final], runs


def run_analysis() -> int:
    started = utc_now()
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=REPO,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    if branch != "phase19/sol-exit":
        raise FCRefusal(f"wrong_branch:{branch}")
    heavy_slot = check_heavy_slot()
    protocol, specs, protocol_sha = load_protocol()
    fast_verification = verify_fast_path(specs)
    pool_manifest, source_bindings = validate_pool_bindings()
    jan_rows, jan_trade_binding = load_trade_rows(
        JAN_TRADES, expected=EXPECTED_JAN_TRADES, month="2026-01"
    )
    feb_rows, feb_trade_binding = load_trade_rows(
        FEB_TRADES, expected=EXPECTED_FEB_TRADES, month="2026-02"
    )
    source_bindings.extend(
        [
            {"role": "january_executed_table", **jan_trade_binding},
            {"role": "february_executed_table", **feb_trade_binding},
            {
                "role": "january_residual_definition",
                "path": str(JAN_RESIDUAL),
                "sha256": sha256_file(JAN_RESIDUAL),
                "authenticated": True,
            },
            {
                "role": "overlay_protocol",
                "path": str(PROTOCOL_PATH),
                "sha256": protocol_sha,
                "authenticated": True,
            },
        ]
    )

    january_authority = authenticate_window("january_2026")
    january_ticks, january_tick_bindings = load_tick_cache(january_authority)
    source_bindings.extend(january_tick_bindings)
    january_executed, january_m1_bindings = evaluate_executed(
        name="january_executed",
        rows=jan_rows,
        specs=specs,
        authority=january_authority,
        tick_cache=january_ticks,
    )
    source_bindings.extend(january_m1_bindings)
    january_pool = evaluate_pool(
        specs=specs,
        tick_cache=january_ticks,
        pool_manifest=pool_manifest,
    )

    base_pool = pool_manifest["base_pool"]
    train_dates = tuple(base_pool["train_dates"])
    holdout_dates = tuple(base_pool["holdout_dates"])
    cells, top_three = build_january_cells(
        specs=specs,
        executed=january_executed,
        pool=january_pool,
        train_dates=train_dates,
        holdout_dates=holdout_dates,
    )
    spec_by_id = {spec.variant_id: spec for spec in specs}
    selected_specs = tuple(spec_by_id[variant_id] for variant_id in top_three)
    identity = spec_by_id["V00_IDENTITY_CURRENT"]

    nulls = {
        "executed": executed_nulls(
            executed=january_executed,
            identity=identity,
            selected=selected_specs,
            train_dates=train_dates,
        ),
        "residual": residual_nulls(
            identity=identity,
            selected=selected_specs,
            train_dates=train_dates,
            tick_cache=january_ticks,
        ),
    }
    del january_ticks

    february_authority = authenticate_window("february_2026")
    february_ticks, february_tick_bindings = load_tick_cache(february_authority)
    source_bindings.extend(february_tick_bindings)
    # The full family is applied only after January freezes ``top_three``.
    # February remains owner-mandated attribution with no ranking, threshold,
    # family-expansion, or implementation authority.
    february_specs = tuple(specs)
    february_executed, february_m1_bindings = evaluate_executed(
        name="february_executed_owner_mandate_20260801",
        rows=feb_rows,
        specs=february_specs,
        authority=february_authority,
        tick_cache=february_ticks,
    )
    source_bindings.extend(february_m1_bindings)
    del february_ticks

    february_dates = tuple(sorted(set(february_executed.days.tolist())))
    february_mask = np.ones(len(february_executed.days), dtype=np.bool_)
    for variant_index, overlay in enumerate(february_specs):
        cells[overlay.variant_id]["february_executed_attribution"] = metric_cell(
            february_executed,
            variant_index=variant_index,
            row_mask=february_mask,
            dates=february_dates,
            aggregation="sum",
        )
        cells[overlay.variant_id]["february_executed_attribution"]["authority"] = (
            "owner_mandate_20260801_defect_attribution_only_not_fitting"
        )
    gates = build_gates(cells=cells, top_three=top_three, nulls=nulls)
    persistent = [
        variant_id
        for variant_id in top_three
        if gates[variant_id]["executed_persistence_gate_passes"]
    ]
    positivity = positivity_summary(
        cells=cells,
        variant_ids=[spec.variant_id for spec in specs],
        top_three=top_three,
    )
    implementation = {
        "persistent_null_clean_executed_variants": persistent,
        "action": (
            "IMPLEMENT_NAMED_DEFAULT_OFF_CANDIDATE"
            if persistent
            else "KEEP_GENERIC_DEFAULT_OFF_OVERLAY_ABSTRACTION"
        ),
        "implemented_surface": "src/research_infra/exit_overlay.py",
        "runtime_default": "OFF_NO_RUNTIME_INTEGRATION",
        "promotion_or_activation": False,
        "family_status": "CONTINUE_REPAIR_NOT_ABANDONED",
        "next_bounded_family_if_no_persistent_cell": {
            "name": "FC2_ENTRY_STATE_CONDITIONAL_EXIT_OVERLAY",
            "cap": 24,
            "ex_ante_inputs_only": [
                "entry_time_cost_r_band",
                "entry_time_session_bucket",
                "entry_time_volatility_band",
                "entry_time_source_mode",
            ],
            "frozen_reuse": "same January split, February attribution boundary, full-cost partial accounting, and null suite",
            "prohibited": [
                "future_mfe",
                "postentry_outcome_fitting",
                "March_2026",
                "live_forward_outcomes",
            ],
        },
    }

    executed_payload = write_rooted_json(
        EXECUTED_PATH,
        {
            "schema": SCHEMA_EXECUTED,
            "session": "FC",
            "surface": "FORENSIC_DIAGNOSTIC",
            "billed": False,
            "protocol_sha256": protocol_sha,
            "january": {
                "selection_role": "TRAIN_AND_HOLDOUT",
                "diagnostics": january_executed.diagnostics,
                "identity_reproduction": identity_reproduction(january_executed),
                "records": january_executed.records,
            },
            "february": {
                "authority": "owner_mandate_20260801_defect_attribution_only_not_fitting",
                "applied_variants": [spec.variant_id for spec in february_specs],
                "diagnostics": february_executed.diagnostics,
                "identity_reproduction": identity_reproduction(february_executed),
                "records": february_executed.records,
            },
            "boundaries": {
                "march_2026_outcomes_read": False,
                "live_forward_outcomes_read": False,
                "broker_or_vps_mutation": False,
                "activation_or_config_change": False,
            },
        },
    )
    null_payload = write_rooted_json(
        NULLS_PATH,
        {
            "schema": SCHEMA_NULLS,
            "session": "FC",
            "surface": "FORENSIC_DIAGNOSTIC",
            "billed": False,
            "selected_on": "january_first_13_ordered_trading_days_executed_book_only",
            "selected_variants": top_three,
            "controls": ["SIDE_FLIP", *(f"SHUFFLE_{seed}" for seed in NULL_SEEDS)],
            "executed": nulls["executed"],
            "residual": nulls["residual"],
            "gate_interpretation": {
                variant_id: {
                    "executed": gates[variant_id]["executed_null_clean"],
                    "residual": gates[variant_id]["residual_null_clean"],
                }
                for variant_id in top_three
            },
        },
    )
    results_payload = write_rooted_json(
        RESULTS_PATH,
        {
            "schema": SCHEMA_RESULTS,
            "session": "FC",
            "generated_at_utc": utc_now(),
            "source_head": repo_head(),
            "surface": "FORENSIC_DIAGNOSTIC",
            "billed": False,
            "protocol_sha256": protocol_sha,
            "family_denominator": 40,
            "train_dates": train_dates,
            "holdout_dates": holdout_dates,
            "february_authority": "owner_mandate_20260801_defect_attribution_only_not_fitting",
            "top_three_frozen_from_january_train": top_three,
            "cells": cells,
            "gates": gates,
            "positivity": positivity,
            "implementation": implementation,
            "identity_reproduction": {
                "january_executed": identity_reproduction(january_executed),
                "january_full_pool_opportunity_proxy": identity_reproduction(january_pool),
                "february_executed": identity_reproduction(february_executed),
            },
            "population_diagnostics": {
                "january_executed": january_executed.diagnostics,
                "january_pool": january_pool.diagnostics,
                "february_executed": february_executed.diagnostics,
            },
            "fast_path_verification": fast_verification,
            "analyzer_corrections": [
                {
                    "issue": "Delayed executed entries initially admitted pre-fill path observations.",
                    "repair": "Executed tick and M1 paths now begin strictly after entry_time_utc while retaining the frozen decision-plus-120-minute horizon.",
                },
                {
                    "issue": "The true-UTC lane preserves raw broker-wall time_msc alongside converted ts_utc/time; the analyzer initially used the wrong field.",
                    "repair": "Tick indexing now requires agreeing explicit ts_utc/time fields and never treats time_msc as UTC.",
                },
            ],
            "correction_invariants": {
                "protocol_cells_thresholds_splits_and_costs_changed": False,
                "invalidated_runs_ledgered_in": "LOOK_MANIFEST.json",
            },
            "boundaries": {
                "march_2026_outcomes_read": False,
                "live_forward_outcomes_read": False,
                "february_fitted": False,
                "full_replay_started": False,
                "broker_or_vps_mutation": False,
                "promotion_or_activation": False,
            },
            "residual_unknowns": [
                "M1 fallback cells remain conservative bar-order diagnostics, not bid/ask headline execution truth.",
                "The two-window executed sample is small; null-clean persistence is required and does not establish live expectancy.",
                "Full-pool results include cost-untradeable rows and cannot authorize or veto the executed overlay.",
                "No March or live-forward outcome was read, so challenge and runtime persistence remain unknown.",
            ],
        },
    )

    source_bindings.extend(
        [
            {
                "role": "january_lane_registry",
                "path": str(LANE_REGISTRY),
                "sha256": sha256_file(LANE_REGISTRY),
                "registry_root_sha256": january_authority.registry_root_sha256,
                "authenticated": True,
            },
            {
                "role": "january_source_manifest",
                "path": str(january_authority.manifest_path),
                "sha256": sha256_file(january_authority.manifest_path),
                "manifest_root_sha256": january_authority.manifest_root_sha256,
                "authenticated": True,
            },
            {
                "role": "february_source_manifest",
                "path": str(february_authority.manifest_path),
                "sha256": sha256_file(february_authority.manifest_path),
                "manifest_root_sha256": february_authority.manifest_root_sha256,
                "authenticated": True,
            },
        ]
    )
    looks, analysis_runs = look_rows(specs=specs, top_three=top_three)
    valid_looks = [row for row in looks if row["valid_for_final_result"]]
    distinct_hypotheses = {
        (str(row["variant_id"]), str(row.get("null_control") or "OVERLAY"))
        for row in looks
    }
    write_rooted_json(
        LOOKS_PATH,
        {
            "schema": SCHEMA_LOOKS,
            "session": "FC",
            "generated_at_utc": utc_now(),
            "analysis_started_at_utc": started,
            "surface": "FORENSIC_DIAGNOSTIC",
            "billed": False,
            "branch": branch,
            "source_head": repo_head(),
            "protocol_sha256": protocol_sha,
            "heavy_compute_slot": heavy_slot,
            "join_contract": {
                "primary_key": [
                    "candidate_id",
                    "decision_time_utc",
                    "symbol",
                    "side_or_direction",
                ],
                "candidate_id_alone_used": False,
                "guarded_fallback_rule_available": True,
                "guarded_fallback_joins_used": 0,
                "ambiguous_or_duplicate_joins": 0,
                "failure_mode": "FAIL_CLOSED",
            },
            "source_bindings": source_bindings,
            "source_binding_count": len(source_bindings),
            "outputs": [
                {
                    "path": str(EXECUTED_PATH),
                    "sha256": sha256_file(EXECUTED_PATH),
                    "self_sha256": executed_payload["self_sha256"],
                },
                {
                    "path": str(NULLS_PATH),
                    "sha256": sha256_file(NULLS_PATH),
                    "self_sha256": null_payload["self_sha256"],
                },
                {
                    "path": str(RESULTS_PATH),
                    "sha256": sha256_file(RESULTS_PATH),
                    "self_sha256": results_payload["self_sha256"],
                },
            ],
            "analysis_runs": analysis_runs,
            "looks": looks,
            "look_count": len(looks),
            "valid_final_look_count": len(valid_looks),
            "distinct_look_hypothesis_count": len(distinct_hypotheses),
            "authority_boundaries": {
                "march_2026_outcomes_read": False,
                "live_forward_outcomes_read": False,
                "february_fitted": False,
                "broker_live_authority": False,
                "broker_mutation_enabled": False,
                "activation_or_config_change": False,
            },
        },
    )
    print(
        json.dumps(
            {
                "status": "COMPLETE",
                "top_three": top_three,
                "persistent": persistent,
                "results": str(RESULTS_PATH),
                "nulls": str(NULLS_PATH),
                "executed": str(EXECUTED_PATH),
                "looks": str(LOOKS_PATH),
            },
            indent=2,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("self-check", help="verify protocol and fast/reference equivalence")
    subparsers.add_parser("run", help="run the frozen sidecar analysis and write artifacts")
    args = parser.parse_args()
    _, specs, _ = load_protocol()
    if args.command == "self-check":
        print(json.dumps(verify_fast_path(specs), indent=2))
        return 0
    return run_analysis()


if __name__ == "__main__":
    raise SystemExit(main())
