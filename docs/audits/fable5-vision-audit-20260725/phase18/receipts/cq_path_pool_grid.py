#!/usr/bin/env python3
"""Session CQ: materialize true-UTC paths and answer CK's frozen grid exactly.

This is an offline research tool.  It authenticates CJ's January lane registry
under ``LANE_ITERATION``, joins CJ's compact S0R0 pool to content-bound M1 paths,
and retains an authenticated tick pointer for every symbol with ordered ticks.
The analyzer uses the tick sequence where present and CK's declared conservative
same-M1-bar rule otherwise.  It never imports a broker module, reads a live
account, opens February economics, or resolves any March source/outcome surface.

The path sidecar obeys ``CK_POOL_PATH_CONTRACT_V1``:

* one row per compact-pool row;
* unique ``(arm_id, candidate_id, decision_time_utc)`` join keys;
* strictly increasing true-UTC M1 observations through 120 minutes; and
* a source hash (plus an ordered-tick hash/pointer where that stronger source
  exists).

Every geometry cell is emitted.  There is no top-N truncation.  ``--commit-looks``
appends one binding geometry look per cell, with named strata carried inside that
look, plus the three declared mechanism measurements. All rows are Session CQ /
VAL / unbilled and idempotent by look id.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import numpy as np


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.lane_rematerialization import (  # noqa: E402
    LaneInputRegistry,
    LaneRematerializationError,
)
from src.components.current_breaker_re_entry_repair import (  # noqa: E402
    STOP_DISTANCE_D as BREAKER_STOP_DISTANCE_D,
    TARGET_DISTANCE_D as BREAKER_TARGET_DISTANCE_D,
    TRANSFORM_ID as BREAKER_TRANSFORM_ID,
    apply_current_breaker_re_entry_repair,
)
from src.research_infra.train_engine.guard import (  # noqa: E402
    PURPOSE_LANE_ITERATION,
)
from src.research_infra.training_lane.append_only import (  # noqa: E402
    atomic_write_json,
    read_rows,
)
from src.research_infra.training_lane.iteration_ledger import (  # noqa: E402
    DEFAULT_ITERATION_LEDGER,
    IterationLedger,
)


AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
HERE = AUDIT / "phase18/receipts"
DEFAULT_PROTOCOL = AUDIT / "phase16/receipts/CK_MECHANISM_PROTOCOL_V1.json"
DEFAULT_CONTRACT = AUDIT / "phase16/receipts/CK_POOL_PATH_CONTRACT_V1.json"
DEFAULT_POOL = AUDIT / "phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
DEFAULT_SIDECAR = HERE / "pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
DEFAULT_POOL_MANIFEST = HERE / "CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json"
DEFAULT_GRID = HERE / "CQ_FROZEN_99_CELL_GRID_V1.json"
DEFAULT_LOOKS = HERE / "CQ_LOOK_MANIFEST_V1.json"
DEFAULT_LOOK_RECEIPT = HERE / "CQ_LOOK_LEDGER_RECEIPT_V1.json"
DEFAULT_REPAIR_TRADES = HERE / "pools/CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz"
DEFAULT_REPAIR_RECEIPT = HERE / "CQ_CURRENT_BREAKER_REPAIR_V1.json"
BROKER_TRUE_COSTS_MATERIALIZED = (
    AUDIT
    / "phase17/activation_carry_live_cost_truth/files/BROKER_TRUE_COSTS_V1.json"
)
BROKER_TRUE_COSTS_CANONICAL = (
    "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"
)

EXPECTED_PROTOCOL_SHA256 = "8c641a360cf3f1c995bbfd239bba78728b22343d8510511684d2cdd42bef9df3"
EXPECTED_BROKER_TRUE_COSTS_SHA256 = (
    "bde450876421bcd0ae0f087e6bfd149838d6fb22a9b6f1cb45e63e3fb28a69bd"
)
EXPECTED_PATH_CONTRACT_SCHEMA = "gtos-session-ck-pool-path-contract-v1"
SIDECAR_SCHEMA = "gtos-session-ck-ordered-path-sidecar-v1"
POOL_MANIFEST_SCHEMA = "gtos-session-cq-path-complete-pool-v1"
GRID_SCHEMA = "gtos-session-cq-frozen-grid-v1"
LOOK_SCHEMA = "gtos-session-cq-look-manifest-v1"
REPAIR_SCHEMA = "gtos-session-cq-current-breaker-repair-v1"
REPAIR_TRADE_SCHEMA = "gtos-session-cq-current-breaker-repair-trade-v1"
ENGINE_VERSION = "gtos.session_cq.path_complete_grid.v1"
RUN_ID = "CQ_PATH_COMPLETE_GRID_V1"
ARM_ID = "S0R0"
WINDOW_ID = "january_2026"
HORIZON_MINUTES = 120
REPAIR_SLEEVE = "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"
INF_INDEX = np.iinfo(np.int32).max
TOL = 1e-9

# CJ's S0R0 replay is FTMO-profiled. These are the canonical-to-broker crossings
# on that replay surface; identity is correct for the other 16 symbols. The map
# is explicit here so CQ does not consume a token-bound profile byte.
FTMO_BROKER_SYMBOLS = {
    "GER40": "GER40.cash",
    "JP225": "JP225.cash",
    "NAS100": "US100.cash",
    "SPX500": "US500.cash",
    "UK100": "UK100.cash",
    "UKOIL_cash": "UKOIL.cash",
    "US30_cash": "US30.cash",
    "USOIL_cash": "USOIL.cash",
}


class CQRefusal(RuntimeError):
    """Fail-closed CQ evidence or contract violation."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _utc_now() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).isoformat()


def _repo_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _native(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_native(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _write_rooted_json(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    result = _native(dict(payload))
    result["self_sha256"] = _canonical_sha256(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, result, indent=1)
    return result


def _parse_utc(value: Any) -> dt.datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise CQRefusal(f"invalid_utc_timestamp:{value}") from exc
    if parsed.tzinfo is None:
        raise CQRefusal(f"naive_utc_timestamp:{value}")
    return parsed.astimezone(dt.timezone.utc)


def _iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat()


def _epoch_us(value: dt.datetime) -> int:
    return int(round(value.timestamp() * 1_000_000))


def _require_january(value: str, *, context: str) -> None:
    if value.startswith("2026-02"):
        raise CQRefusal(f"february_economics_forbidden:{context}:{value}")
    if value.startswith("2026-03"):
        raise CQRefusal(f"march_outcomes_forbidden:{context}:{value}")
    if not value.startswith("2026-01"):
        raise CQRefusal(f"non_january_surface:{context}:{value}")


def load_protocol(path: Path = DEFAULT_PROTOCOL) -> dict[str, Any]:
    digest = _sha256_file(path)
    if digest != EXPECTED_PROTOCOL_SHA256:
        raise CQRefusal(
            f"frozen_protocol_drift:{digest}!={EXPECTED_PROTOCOL_SHA256}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    geometry = payload.get("geometry") or {}
    if geometry.get("cell_count_per_orientation") != 99:
        raise CQRefusal("frozen_protocol_cell_count_not_99")
    if geometry.get("orientations") != ["as_declared", "inverted"]:
        raise CQRefusal("frozen_protocol_orientation_drift")
    if payload.get("march_2026") != "OUTCOME_UNREAD_AND_FORBIDDEN":
        raise CQRefusal("frozen_protocol_march_boundary_drift")
    return payload


def load_path_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != EXPECTED_PATH_CONTRACT_SCHEMA:
        raise CQRefusal("ck_path_contract_schema_invalid")
    sidecar = payload.get("sidecar_contract") or {}
    if sidecar.get("schema") != SIDECAR_SCHEMA:
        raise CQRefusal("ck_sidecar_contract_schema_invalid")
    required = {
        "arm_id",
        "candidate_id",
        "decision_time_utc",
        "horizon_end_utc",
        "source_sha256",
        "ordered_path_observations",
    }
    if not required.issubset(set(sidecar.get("row_fields") or [])):
        raise CQRefusal("ck_sidecar_contract_required_fields_drift")
    return payload


@dataclass(frozen=True)
class LaneAuthority:
    registry_path: Path
    registry_root_sha256: str
    manifest_path: Path
    manifest_root_sha256: str
    manifest: Mapping[str, Any]
    pack_count: int


def authenticate_lane_registry(path: Path) -> LaneAuthority:
    """Authenticate CJ's external read-only January estate under LANE_ITERATION."""

    resolved = LaneInputRegistry(path).resolve(
        window_id=WINDOW_ID,
        purpose=PURPOSE_LANE_ITERATION,
    )
    manifest = dict(resolved.source_manifest)
    if (
        resolved.window.start != "2026-01-01"
        or resolved.window.end != "2026-01-31"
        or resolved.entry.get("surface") != "VAL"
        or resolved.entry.get("campaign_sealed") is not False
        or manifest.get("economic_outcomes_read") is not False
        or manifest.get("window_id") != WINDOW_ID
        or manifest.get("window") != ["2026-01-01", "2026-01-31"]
        or manifest.get("time_column_basis") == "broker_wall_clock"
        or (manifest.get("clock") or {}).get("time_column_basis") != "true_utc"
    ):
        raise CQRefusal("january_lane_authority_boundary_invalid")
    if manifest.get("march_source_only_disclosure") not in (None, {}):
        raise CQRefusal("january_manifest_contains_march_disclosure")
    return LaneAuthority(
        registry_path=resolved.registry_path,
        registry_root_sha256=str(resolved.registry["registry_root_sha256"]),
        manifest_path=resolved.source_manifest_path,
        manifest_root_sha256=str(manifest["manifest_root_sha256"]),
        manifest=manifest,
        pack_count=len(resolved.pack_roots),
    )


def _iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CQRefusal(f"invalid_jsonl:{path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise CQRefusal(f"non_object_jsonl:{path}:{line_number}")
            yield row


def load_pool_rows(path: Path = DEFAULT_POOL) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = list(_iter_gzip_jsonl(path))
    if not rows:
        raise CQRefusal("compact_pool_empty")
    required = {
        "candidate_id",
        "decision_time_utc",
        "symbol",
        "side",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "cost_r",
        "opportunity_net_proxy_r",
        "origin_family",
    }
    missing = sorted(required - set(rows[0]))
    if missing:
        raise CQRefusal(f"compact_pool_required_fields_missing:{','.join(missing)}")
    keys: set[tuple[str, str, str]] = set()
    days: set[str] = set()
    for index, row in enumerate(rows):
        decision = str(row.get("decision_time_utc") or "")
        _require_january(decision, context=f"pool_row_{index}")
        days.add(decision[:10])
        key = (ARM_ID, str(row.get("candidate_id") or ""), decision)
        if not key[1] or key in keys:
            raise CQRefusal(f"compact_pool_join_key_invalid_or_duplicate:{key}")
        keys.add(key)
        try:
            entry = float(row["entry_price"])
            stop = float(row["stop_loss"])
            float(row["take_profit_1"])
            float(row["cost_r"])
            float(row["opportunity_net_proxy_r"])
        except (TypeError, ValueError) as exc:
            raise CQRefusal(f"compact_pool_numeric_invalid:{key}") from exc
        if not all(math.isfinite(value) for value in (entry, stop)) or entry == stop:
            raise CQRefusal(f"compact_pool_geometry_invalid:{key}")
    if len(days) != 21:
        raise CQRefusal(f"compact_pool_trading_day_count:{len(days)}!=21")
    return rows, {
        "path": _repo_path(path),
        "sha256": _sha256_file(path),
        "rows": len(rows),
        "unique_join_keys": len(keys),
        "dates": sorted(days),
        "train_dates": sorted(days)[:13],
        "holdout_dates": sorted(days)[13:],
    }


@dataclass(frozen=True)
class SourceRecord:
    symbol: str
    timeframe: str
    logical_path: str
    path: Path
    sha256: str
    row_count: int


def _safe_lane_path(authority: LaneAuthority, relative: str) -> Path:
    root = authority.registry_path.parent.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise CQRefusal(f"lane_source_escapes_registry_root:{relative}") from exc
    if not path.is_file():
        raise CQRefusal(f"lane_source_missing:{relative}")
    return path


def source_records(authority: LaneAuthority) -> tuple[dict[str, SourceRecord], dict[str, SourceRecord]]:
    m1: dict[str, SourceRecord] = {}
    tick: dict[str, SourceRecord] = {}
    for raw in authority.manifest.get("bar_sources") or []:
        if raw.get("timeframe") != "M1" or raw.get("source_family") != "bridge_ftmo_m1_202601":
            continue
        symbol = str(raw.get("mapped_symbol") or raw.get("symbol") or "")
        logical = str(raw.get("lane_relpath") or "")
        record = SourceRecord(
            symbol=symbol,
            timeframe="M1",
            logical_path=logical,
            path=_safe_lane_path(authority, logical),
            sha256=str(raw.get("sha256") or ""),
            row_count=int(raw.get("row_count") or 0),
        )
        if symbol in m1:
            raise CQRefusal(f"duplicate_january_m1_source:{symbol}")
        m1[symbol] = record
    for raw in authority.manifest.get("tick_sources") or []:
        if raw.get("timeframe") != "TICK":
            continue
        symbol = str(raw.get("mapped_symbol") or raw.get("symbol") or "")
        logical = str(raw.get("lane_relpath") or "")
        record = SourceRecord(
            symbol=symbol,
            timeframe="TICK",
            logical_path=logical,
            path=_safe_lane_path(authority, logical),
            sha256=str(raw.get("sha256") or ""),
            row_count=int(raw.get("row_count") or 0),
        )
        if symbol in tick:
            raise CQRefusal(f"duplicate_january_tick_source:{symbol}")
        tick[symbol] = record
    if len(m1) != 24:
        raise CQRefusal(f"january_m1_source_count:{len(m1)}!=24")
    manifest_tick_count = int(authority.manifest.get("tick_symbol_count") or 0)
    if len(tick) != manifest_tick_count:
        raise CQRefusal(
            f"january_tick_source_count:{len(tick)}!={manifest_tick_count}"
        )
    for record in [*m1.values(), *tick.values()]:
        digest = _sha256_file(record.path)
        if digest != record.sha256:
            raise CQRefusal(
                f"lane_source_hash_mismatch:{record.logical_path}:{digest}!={record.sha256}"
            )
    return m1, tick


@dataclass(frozen=True)
class M1Series:
    times: tuple[dt.datetime, ...]
    observations: tuple[dict[str, Any], ...]


def load_m1(record: SourceRecord) -> M1Series:
    times: list[dt.datetime] = []
    observations: list[dict[str, Any]] = []
    with record.path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = {"time", "open", "high", "low", "close"}
        if not expected.issubset(set(reader.fieldnames or [])):
            raise CQRefusal(f"m1_columns_invalid:{record.logical_path}")
        for row_number, row in enumerate(reader, start=2):
            timestamp = _parse_utc(row["time"])
            if times and timestamp <= times[-1]:
                raise CQRefusal(
                    f"m1_time_not_strict:{record.logical_path}:{row_number}"
                )
            try:
                observation = {
                    "time_utc": _iso(timestamp),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                }
            except (TypeError, ValueError) as exc:
                raise CQRefusal(
                    f"m1_numeric_invalid:{record.logical_path}:{row_number}"
                ) from exc
            if not all(math.isfinite(float(observation[key])) for key in ("open", "high", "low", "close")):
                raise CQRefusal(f"m1_nonfinite:{record.logical_path}:{row_number}")
            if observation["low"] > observation["high"]:
                raise CQRefusal(f"m1_range_invalid:{record.logical_path}:{row_number}")
            times.append(timestamp)
            observations.append(observation)
    if len(times) != record.row_count:
        raise CQRefusal(
            f"m1_row_count_mismatch:{record.logical_path}:{len(times)}!={record.row_count}"
        )
    return M1Series(tuple(times), tuple(observations))


def slice_observations(
    series: M1Series,
    *,
    decision: dt.datetime,
    horizon: dt.datetime,
) -> tuple[dict[str, Any], ...]:
    # The source oracle queries strictly after as-of.  The CK contract permits
    # at-or-after; strict-after is the stronger no-lookahead choice.
    start = bisect.bisect_right(series.times, decision)
    end = bisect.bisect_right(series.times, horizon)
    rows = series.observations[start:end]
    if not rows:
        raise CQRefusal(
            f"path_source_empty_for_candidate:{_iso(decision)}:{_iso(horizon)}"
        )
    previous: dt.datetime | None = None
    for row in rows:
        timestamp = _parse_utc(row["time_utc"])
        if timestamp <= decision or timestamp > horizon:
            raise CQRefusal("path_observation_outside_candidate_horizon")
        if previous is not None and timestamp <= previous:
            raise CQRefusal("path_observation_times_not_strict")
        previous = timestamp
    return rows


class _DeterministicGzipWriter:
    def __init__(self, path: Path):
        self.path = path
        self.temp_path: Path | None = None
        self.raw: io.BufferedWriter | None = None
        self.gzip_handle: gzip.GzipFile | None = None
        self.text: io.TextIOWrapper | None = None

    def __enter__(self) -> io.TextIOWrapper:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        os.close(fd)
        self.temp_path = Path(temp)
        self.raw = self.temp_path.open("wb")
        self.gzip_handle = gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=self.raw,
            compresslevel=6,
            mtime=0,
        )
        self.text = io.TextIOWrapper(self.gzip_handle, encoding="utf-8", newline="\n")
        return self.text

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        try:
            if self.text is not None:
                self.text.close()
        finally:
            if self.raw is not None and not self.raw.closed:
                self.raw.close()
        if self.temp_path is None:
            return
        if exc_type is None:
            os.replace(self.temp_path, self.path)
        else:
            self.temp_path.unlink(missing_ok=True)


def build_sidecar(
    *,
    registry_path: Path,
    pool_path: Path = DEFAULT_POOL,
    sidecar_path: Path = DEFAULT_SIDECAR,
    manifest_path: Path = DEFAULT_POOL_MANIFEST,
) -> dict[str, Any]:
    load_protocol()
    contract = load_path_contract()
    authority = authenticate_lane_registry(registry_path)
    pool_rows, pool_meta = load_pool_rows(pool_path)
    m1_sources, tick_sources = source_records(authority)
    missing_symbols = sorted({str(row["symbol"]) for row in pool_rows} - set(m1_sources))
    if missing_symbols:
        raise CQRefusal(f"pool_symbols_without_m1:{','.join(missing_symbols)}")

    # The output contract preserves base-pool order. Keep only the compact M1
    # series in memory and stream projected rows directly to deterministic gzip;
    # retaining every expanded observation dict would make the sidecar itself the
    # peak-memory object.
    series_by_symbol: dict[str, M1Series] = {}
    observation_count = 0
    min_observations: int | None = None
    max_observations = 0
    tick_pointer_rows = 0
    source_inventory: dict[str, Any] = {}
    for symbol in sorted(m1_sources):
        source = m1_sources[symbol]
        series_by_symbol[symbol] = load_m1(source)
        source_inventory[symbol] = {
            "m1": {
                "path": source.logical_path,
                "sha256": source.sha256,
                "rows": source.row_count,
            },
            "tick": (
                {
                    "path": tick_sources[symbol].logical_path,
                    "sha256": tick_sources[symbol].sha256,
                    "rows": tick_sources[symbol].row_count,
                }
                if symbol in tick_sources
                else None
            ),
        }
    sidecar_rows = 0
    with _DeterministicGzipWriter(sidecar_path) as handle:
        for row in pool_rows:
            symbol = str(row["symbol"])
            source = m1_sources[symbol]
            series = series_by_symbol[symbol]
            decision = _parse_utc(row["decision_time_utc"])
            horizon = decision + dt.timedelta(minutes=HORIZON_MINUTES)
            observations = slice_observations(
                series,
                decision=decision,
                horizon=horizon,
            )
            count = len(observations)
            observation_count += count
            min_observations = count if min_observations is None else min(min_observations, count)
            max_observations = max(max_observations, count)
            tick = tick_sources.get(symbol)
            if tick is not None:
                tick_pointer_rows += 1
            projected = {
                "schema": SIDECAR_SCHEMA,
                "arm_id": ARM_ID,
                "candidate_id": str(row["candidate_id"]),
                "decision_time_utc": _iso(decision),
                "horizon_end_utc": _iso(horizon),
                "symbol": symbol,
                "side": str(row["side"]).upper(),
                "source_timeframe": "M1",
                "source_path": source.logical_path,
                "source_sha256": source.sha256,
                "ordered_tick_source": (
                    {
                        "timeframe": "TICK",
                        "path": tick.logical_path,
                        "source_sha256": tick.sha256,
                        "row_count": tick.row_count,
                        "selection_rule": "ordered_tick_priority_over_m1",
                    }
                    if tick is not None
                    else None
                ),
                "ordered_path_observations": list(observations),
            }
            handle.write(
                json.dumps(
                    projected,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            )
            sidecar_rows += 1

    if sidecar_rows != len(pool_rows):
        raise CQRefusal("sidecar_projection_incomplete")

    manifest = _write_rooted_json(
        manifest_path,
        {
            "schema": POOL_MANIFEST_SCHEMA,
            "generated_at_utc": _utc_now(),
            "source_head": _repo_head(),
            "surface": "VAL",
            "billed": False,
            "campaign_sealed": False,
            "march_2026_outcomes_read": False,
            "february_2026_economics_read": False,
            "broker_live_authority": False,
            "broker_mutation_enabled": False,
            "arm_id": ARM_ID,
            "window": ["2026-01-01", "2026-01-31"],
            "horizon_minutes": HORIZON_MINUTES,
            "path_contract": _repo_path(DEFAULT_CONTRACT),
            "path_contract_sha256": _sha256_file(DEFAULT_CONTRACT),
            "path_contract_self_sha256": contract.get("self_sha256"),
            "protocol": _repo_path(DEFAULT_PROTOCOL),
            "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
            "base_pool": pool_meta,
            "sidecar": {
                "path": _repo_path(sidecar_path),
                "sha256": _sha256_file(sidecar_path),
                "schema": SIDECAR_SCHEMA,
                "rows": sidecar_rows,
                "unique_join_keys": sidecar_rows,
                "observation_rows": observation_count,
                "min_observations_per_candidate": min_observations,
                "max_observations_per_candidate": max_observations,
                "tick_pointer_rows": tick_pointer_rows,
            },
            "lane_authority": {
                "registry_path": str(authority.registry_path),
                "registry_root_sha256": authority.registry_root_sha256,
                "source_manifest_path": str(authority.manifest_path),
                "source_manifest_root_sha256": authority.manifest_root_sha256,
                "pack_count": authority.pack_count,
                "purpose": PURPOSE_LANE_ITERATION,
                "clock_rule": (authority.manifest.get("clock") or {}).get(
                    "broker_clock_rule"
                ),
                "time_column_basis": "true_utc",
                "external_estate_boundary": "machine_local_read_only",
            },
            "source_inventory": source_inventory,
            "invariants": {
                "one_sidecar_row_per_pool_row": sidecar_rows == len(pool_rows),
                "unique_join_key": True,
                "strictly_increasing_observation_times": True,
                "first_observation_strictly_after_decision": True,
                "last_observation_at_or_before_120_minute_horizon": True,
                "all_source_hashes_authenticated": True,
                "ordered_tick_priority_content_bound_where_available": True,
            },
            "status": "PATH_COMPLETE_POOL_MATERIALIZED",
        },
    )
    return manifest


@dataclass
class PathSummary:
    target_index: np.ndarray
    stop_index: np.ndarray
    target_time_us: np.ndarray
    stop_time_us: np.ndarray
    terminal_signed_d: float
    terminal_time_us: int
    recorded_target_index: int
    recorded_stop_index: int
    recorded_target_time_us: int
    recorded_stop_time_us: int
    source_mode: str


def _first_index(running: np.ndarray, threshold: float) -> int:
    position = int(np.searchsorted(running, threshold - TOL, side="left"))
    return INF_INDEX if position >= len(running) else position


def _times_for_indices(indices: np.ndarray, times_us: np.ndarray) -> np.ndarray:
    result = np.full(len(indices), -1, dtype=np.int64)
    valid = indices != INF_INDEX
    result[valid] = times_us[indices[valid]]
    return result


def summarize_ohlc_path(
    *,
    observations: Sequence[Mapping[str, Any]],
    entry: float,
    base_distance: float,
    side: str,
    targets: np.ndarray,
    stops: np.ndarray,
    recorded_target_d: float,
) -> PathSummary:
    if base_distance <= 0 or not observations:
        raise CQRefusal("ohlc_path_invalid_geometry_or_empty")
    high = np.fromiter((float(row["high"]) for row in observations), dtype=np.float64)
    low = np.fromiter((float(row["low"]) for row in observations), dtype=np.float64)
    close = float(observations[-1]["close"])
    side_key = side.upper()
    if side_key == "LONG":
        favorable = (high - entry) / base_distance
        adverse = (entry - low) / base_distance
        terminal = (close - entry) / base_distance
    elif side_key == "SHORT":
        favorable = (entry - low) / base_distance
        adverse = (high - entry) / base_distance
        terminal = (entry - close) / base_distance
    else:
        raise CQRefusal(f"invalid_side:{side}")
    running_favorable = np.maximum.accumulate(favorable)
    running_adverse = np.maximum.accumulate(adverse)
    times_us = np.fromiter(
        (_epoch_us(_parse_utc(row["time_utc"])) for row in observations),
        dtype=np.int64,
    )
    target_index = np.searchsorted(running_favorable, targets - TOL, side="left")
    stop_index = np.searchsorted(running_adverse, stops - TOL, side="left")
    target_index = np.where(target_index >= len(observations), INF_INDEX, target_index).astype(
        np.int32
    )
    stop_index = np.where(stop_index >= len(observations), INF_INDEX, stop_index).astype(
        np.int32
    )
    recorded_target_index = _first_index(running_favorable, recorded_target_d)
    recorded_stop_index = _first_index(running_adverse, 1.0)
    return PathSummary(
        target_index=target_index,
        stop_index=stop_index,
        target_time_us=_times_for_indices(target_index, times_us),
        stop_time_us=_times_for_indices(stop_index, times_us),
        terminal_signed_d=float(terminal),
        terminal_time_us=int(times_us[-1]),
        recorded_target_index=recorded_target_index,
        recorded_stop_index=recorded_stop_index,
        recorded_target_time_us=(
            -1 if recorded_target_index == INF_INDEX else int(times_us[recorded_target_index])
        ),
        recorded_stop_time_us=(
            -1 if recorded_stop_index == INF_INDEX else int(times_us[recorded_stop_index])
        ),
        source_mode="M1_CONSERVATIVE",
    )


@dataclass(frozen=True)
class TickSeries:
    times_us: np.ndarray
    bid: np.ndarray
    ask: np.ndarray


def load_ticks(record: SourceRecord) -> TickSeries:
    times = np.empty(record.row_count, dtype=np.int64)
    bid = np.empty(record.row_count, dtype=np.float64)
    ask = np.empty(record.row_count, dtype=np.float64)
    count = 0
    with record.path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                times[count] = int(row["time_msc"]) * 1000
                bid[count] = float(row["bid"])
                ask[count] = float(row["ask"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise CQRefusal(
                    f"tick_row_invalid:{record.logical_path}:{line_number}"
                ) from exc
            count += 1
            if count > record.row_count:
                raise CQRefusal(f"tick_row_count_exceeds_manifest:{record.logical_path}")
    if count != record.row_count:
        raise CQRefusal(
            f"tick_row_count_mismatch:{record.logical_path}:{count}!={record.row_count}"
        )
    if np.any(times[1:] < times[:-1]):
        raise CQRefusal(f"tick_time_order_invalid:{record.logical_path}")
    if not np.isfinite(bid).all() or not np.isfinite(ask).all():
        raise CQRefusal(f"tick_nonfinite:{record.logical_path}")
    return TickSeries(times, bid, ask)


def summarize_tick_path(
    *,
    series: TickSeries,
    decision: dt.datetime,
    horizon: dt.datetime,
    entry: float,
    base_distance: float,
    side: str,
    targets: np.ndarray,
    stops: np.ndarray,
    recorded_target_d: float,
) -> PathSummary | None:
    start = int(np.searchsorted(series.times_us, _epoch_us(decision), side="right"))
    end = int(np.searchsorted(series.times_us, _epoch_us(horizon), side="right"))
    if start >= end:
        return None
    side_key = side.upper()
    if side_key == "LONG":
        prices = series.bid[start:end]
        signed = (prices - entry) / base_distance
    elif side_key == "SHORT":
        prices = series.ask[start:end]
        signed = (entry - prices) / base_distance
    else:
        raise CQRefusal(f"invalid_tick_side:{side}")
    running_favorable = np.maximum.accumulate(signed)
    running_adverse = np.maximum.accumulate(-signed)
    times_us = series.times_us[start:end]
    target_index = np.searchsorted(running_favorable, targets - TOL, side="left")
    stop_index = np.searchsorted(running_adverse, stops - TOL, side="left")
    target_index = np.where(target_index >= len(signed), INF_INDEX, target_index).astype(np.int32)
    stop_index = np.where(stop_index >= len(signed), INF_INDEX, stop_index).astype(np.int32)
    recorded_target_index = _first_index(running_favorable, recorded_target_d)
    recorded_stop_index = _first_index(running_adverse, 1.0)
    return PathSummary(
        target_index=target_index,
        stop_index=stop_index,
        target_time_us=_times_for_indices(target_index, times_us),
        stop_time_us=_times_for_indices(stop_index, times_us),
        terminal_signed_d=float(signed[-1]),
        terminal_time_us=int(times_us[-1]),
        recorded_target_index=recorded_target_index,
        recorded_stop_index=recorded_stop_index,
        recorded_target_time_us=(
            -1 if recorded_target_index == INF_INDEX else int(times_us[recorded_target_index])
        ),
        recorded_stop_time_us=(
            -1 if recorded_stop_index == INF_INDEX else int(times_us[recorded_stop_index])
        ),
        source_mode="ORDERED_TICK",
    )


def _empty_summary_arrays(rows: int, targets: int, stops: int) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for orientation in ("as_declared", "inverted"):
        result[orientation] = {
            "target_index": np.full((rows, targets), INF_INDEX, dtype=np.int32),
            "stop_index": np.full((rows, stops), INF_INDEX, dtype=np.int32),
            "target_time_us": np.full((rows, targets), -1, dtype=np.int64),
            "stop_time_us": np.full((rows, stops), -1, dtype=np.int64),
            "terminal_signed_d": np.full(rows, np.nan, dtype=np.float64),
            "terminal_time_us": np.full(rows, -1, dtype=np.int64),
            "recorded_target_index": np.full(rows, INF_INDEX, dtype=np.int32),
            "recorded_stop_index": np.full(rows, INF_INDEX, dtype=np.int32),
            "recorded_target_time_us": np.full(rows, -1, dtype=np.int64),
            "recorded_stop_time_us": np.full(rows, -1, dtype=np.int64),
            "source_mode": np.full(rows, "", dtype="U16"),
        }
    return result


def _assign_summary(target: dict[str, Any], index: int, summary: PathSummary) -> None:
    target["target_index"][index] = summary.target_index
    target["stop_index"][index] = summary.stop_index
    target["target_time_us"][index] = summary.target_time_us
    target["stop_time_us"][index] = summary.stop_time_us
    target["terminal_signed_d"][index] = summary.terminal_signed_d
    target["terminal_time_us"][index] = summary.terminal_time_us
    target["recorded_target_index"][index] = summary.recorded_target_index
    target["recorded_stop_index"][index] = summary.recorded_stop_index
    target["recorded_target_time_us"][index] = summary.recorded_target_time_us
    target["recorded_stop_time_us"][index] = summary.recorded_stop_time_us
    target["source_mode"][index] = summary.source_mode


def load_path_summaries(
    *,
    pool_rows: Sequence[Mapping[str, Any]],
    sidecar_path: Path,
    targets: np.ndarray,
    stops: np.ndarray,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    summaries = _empty_summary_arrays(len(pool_rows), len(targets), len(stops))
    sidecar_count = 0
    source_modes: dict[str, int] = {}
    sidecar_iterator = _iter_gzip_jsonl(sidecar_path)
    for index, pool_row in enumerate(pool_rows):
        try:
            sidecar = next(sidecar_iterator)
        except StopIteration as exc:
            raise CQRefusal(f"sidecar_ended_early:{index}") from exc
        sidecar_count += 1
        expected_key = (
            ARM_ID,
            str(pool_row["candidate_id"]),
            _iso(_parse_utc(pool_row["decision_time_utc"])),
        )
        actual_key = (
            str(sidecar.get("arm_id") or ""),
            str(sidecar.get("candidate_id") or ""),
            str(sidecar.get("decision_time_utc") or ""),
        )
        if actual_key != expected_key:
            raise CQRefusal(f"sidecar_join_mismatch:{index}:{actual_key}!={expected_key}")
        decision = _parse_utc(actual_key[2])
        horizon = _parse_utc(sidecar.get("horizon_end_utc"))
        if horizon != decision + dt.timedelta(minutes=HORIZON_MINUTES):
            raise CQRefusal(f"sidecar_horizon_mismatch:{actual_key}")
        observations = sidecar.get("ordered_path_observations")
        if not isinstance(observations, list) or not observations:
            raise CQRefusal(f"sidecar_observations_missing:{actual_key}")
        previous: dt.datetime | None = None
        for observation in observations:
            if not isinstance(observation, Mapping):
                raise CQRefusal(f"sidecar_observation_invalid:{actual_key}")
            timestamp = _parse_utc(observation.get("time_utc"))
            if timestamp <= decision or timestamp > horizon:
                raise CQRefusal(f"sidecar_observation_window_invalid:{actual_key}")
            if previous is not None and timestamp <= previous:
                raise CQRefusal(f"sidecar_observation_order_invalid:{actual_key}")
            previous = timestamp
        entry = float(pool_row["entry_price"])
        stop = float(pool_row["stop_loss"])
        base_distance = abs(entry - stop)
        recorded_target_d = abs(float(pool_row["take_profit_1"]) - entry) / base_distance
        declared_side = str(pool_row["side"]).upper()
        for orientation, side in (
            ("as_declared", declared_side),
            ("inverted", "SHORT" if declared_side == "LONG" else "LONG"),
        ):
            summary = summarize_ohlc_path(
                observations=observations,
                entry=entry,
                base_distance=base_distance,
                side=side,
                targets=targets,
                stops=stops,
                recorded_target_d=recorded_target_d,
            )
            _assign_summary(summaries[orientation], index, summary)
            source_modes[summary.source_mode] = source_modes.get(summary.source_mode, 0) + 1
    try:
        extra = next(sidecar_iterator)
    except StopIteration:
        extra = None
    if extra is not None:
        raise CQRefusal("sidecar_has_extra_rows")
    if sidecar_count != len(pool_rows):
        raise CQRefusal("sidecar_row_count_mismatch")
    return summaries, {
        "rows": sidecar_count,
        "source_modes_before_tick_override": source_modes,
    }


def apply_tick_priority(
    *,
    summaries: dict[str, dict[str, Any]],
    pool_rows: Sequence[Mapping[str, Any]],
    tick_sources: Mapping[str, SourceRecord],
    targets: np.ndarray,
    stops: np.ndarray,
) -> dict[str, Any]:
    rows_by_symbol: dict[str, list[int]] = {}
    for index, row in enumerate(pool_rows):
        symbol = str(row["symbol"])
        if symbol in tick_sources:
            rows_by_symbol.setdefault(symbol, []).append(index)
    overridden = 0
    fallback = 0
    per_symbol: dict[str, Any] = {}
    for symbol in sorted(rows_by_symbol):
        record = tick_sources[symbol]
        series = load_ticks(record)
        symbol_overridden = 0
        symbol_fallback = 0
        for index in rows_by_symbol[symbol]:
            row = pool_rows[index]
            decision = _parse_utc(row["decision_time_utc"])
            horizon = decision + dt.timedelta(minutes=HORIZON_MINUTES)
            entry = float(row["entry_price"])
            base_distance = abs(entry - float(row["stop_loss"]))
            recorded_target_d = abs(float(row["take_profit_1"]) - entry) / base_distance
            declared_side = str(row["side"]).upper()
            row_used_tick = True
            for orientation, side in (
                ("as_declared", declared_side),
                ("inverted", "SHORT" if declared_side == "LONG" else "LONG"),
            ):
                summary = summarize_tick_path(
                    series=series,
                    decision=decision,
                    horizon=horizon,
                    entry=entry,
                    base_distance=base_distance,
                    side=side,
                    targets=targets,
                    stops=stops,
                    recorded_target_d=recorded_target_d,
                )
                if summary is None:
                    row_used_tick = False
                    break
                _assign_summary(summaries[orientation], index, summary)
            if row_used_tick:
                overridden += 1
                symbol_overridden += 1
            else:
                fallback += 1
                symbol_fallback += 1
        per_symbol[symbol] = {
            "pool_rows": len(rows_by_symbol[symbol]),
            "ordered_tick_rows": symbol_overridden,
            "m1_fallback_rows": symbol_fallback,
            "source_path": record.logical_path,
            "source_sha256": record.sha256,
            "source_rows": record.row_count,
        }
        del series
    return {
        "ordered_tick_rows": overridden,
        "m1_fallback_rows_on_tick_symbols": fallback,
        "per_symbol": per_symbol,
    }


def _split_masks(pool_rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    days = np.asarray([str(row["decision_time_utc"])[:10] for row in pool_rows], dtype="U10")
    unique = sorted(set(days.tolist()))
    if len(unique) != 21:
        raise CQRefusal(f"grid_trading_day_count:{len(unique)}!=21")
    train_dates = unique[:13]
    holdout_dates = unique[13:]
    return {
        "TRAIN": np.isin(days, np.asarray(train_dates, dtype="U10")),
        "HOLDOUT": np.isin(days, np.asarray(holdout_dates, dtype="U10")),
        "FULL": np.ones(len(pool_rows), dtype=bool),
    }, {"dates": unique, "train_dates": train_dates, "holdout_dates": holdout_dates}


def _metrics(
    *,
    gross: np.ndarray,
    net: np.ndarray,
    optimistic_gross: np.ndarray,
    outcome: np.ndarray,
    ambiguous: np.ndarray,
    mask: np.ndarray,
) -> dict[str, Any]:
    selected = np.flatnonzero(mask)
    if not len(selected):
        return {
            "n": 0,
            "mean_gross_r": None,
            "mean_net_r": None,
            "mean_optimistic_gross_r": None,
            "ambiguity_contribution_gross_r_per_row": None,
            "outcomes": {},
            "ambiguous_rows": 0,
            "ambiguous_share": None,
        }
    labels, counts = np.unique(outcome[selected], return_counts=True)
    mean_gross = float(np.mean(gross[selected]))
    optimistic = float(np.mean(optimistic_gross[selected]))
    return {
        "n": int(len(selected)),
        "mean_gross_r": mean_gross,
        "mean_net_r": float(np.mean(net[selected])),
        "mean_optimistic_gross_r": optimistic,
        "ambiguity_contribution_gross_r_per_row": optimistic - mean_gross,
        "outcomes": {str(label): int(count) for label, count in zip(labels, counts)},
        "ambiguous_rows": int(ambiguous[selected].sum()),
        "ambiguous_share": float(ambiguous[selected].mean()),
    }


def _cell_verdict(splits: Mapping[str, Mapping[str, Any]]) -> str:
    train = splits["TRAIN"]
    holdout = splits["HOLDOUT"]
    train_net = float(train["mean_net_r"])
    holdout_net = float(holdout["mean_net_r"])
    train_gross = float(train["mean_gross_r"])
    holdout_gross = float(holdout["mean_gross_r"])
    if train_net > 0 and holdout_net > 0:
        return "PERSISTENT_NET_POSITIVE"
    if train_net > 0 and holdout_net <= 0:
        return "TRAIN_ONLY_NET_POSITIVE"
    if train_net <= 0 and holdout_net > 0:
        return "HOLDOUT_ONLY_NET_POSITIVE"
    if train_gross > 0 and holdout_gross > 0:
        return "PERSISTENT_GROSS_POSITIVE_COST_VETOED"
    return "NET_NEGATIVE_BOTH_SPLITS"


def _recorded_metrics(
    pool_rows: Sequence[Mapping[str, Any]],
    masks: Mapping[str, np.ndarray],
    population: np.ndarray,
    *,
    repriced_costs: np.ndarray | None = None,
) -> dict[str, Any]:
    recorded_net = np.asarray(
        [float(row["opportunity_net_proxy_r"]) for row in pool_rows]
    )
    recorded_cost = np.asarray([float(row["cost_r"]) for row in pool_rows])
    gross = recorded_net + recorded_cost
    cost = recorded_cost if repriced_costs is None else repriced_costs
    if len(cost) != len(pool_rows):
        raise CQRefusal("repriced_cost_vector_length_mismatch")
    net = gross - cost
    result: dict[str, Any] = {}
    for split, split_mask in masks.items():
        mask = np.logical_and(split_mask, population)
        selected = np.flatnonzero(mask)
        result[split] = {
            "n": int(len(selected)),
            "mean_gross_r": float(np.mean(gross[selected])) if len(selected) else None,
            "mean_net_r": float(np.mean(net[selected])) if len(selected) else None,
            "gross_sum_r": float(np.sum(gross[selected])) if len(selected) else 0.0,
            "net_sum_r": float(np.sum(net[selected])) if len(selected) else 0.0,
            "mean_cost_r": float(np.mean(cost[selected])) if len(selected) else None,
        }
    return result


def _broker_true_cost_vector(
    pool_rows: Sequence[Mapping[str, Any]],
    masks: Mapping[str, np.ndarray],
    liquidity_mask: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Independently reprice CJ commission through CN's exact cost call chain.

    CJ V7 says ``commission_broker_true_gated`` was active, but its compact rows
    retained ``commission_r`` without the newer provenance field. Recomputing all
    27,658 rows establishes whether that number is actually broker-true before it
    is used by the grid or the named liquidity-reclaim conclusion.
    """

    from src.costs.model import (  # local import keeps this offline tool narrow
        BrokerTrueCosts,
        CostTruthError,
        _usd_per_price_unit_per_lot,
        commission_usd_per_lot,
    )

    digest = _sha256_file(BROKER_TRUE_COSTS_MATERIALIZED)
    if digest != EXPECTED_BROKER_TRUE_COSTS_SHA256:
        raise CQRefusal(
            "broker_true_cost_artifact_drift:"
            f"{digest}!={EXPECTED_BROKER_TRUE_COSTS_SHA256}"
        )
    truth = BrokerTrueCosts(
        json.loads(BROKER_TRUE_COSTS_MATERIALIZED.read_text(encoding="utf-8")),
        source=BROKER_TRUE_COSTS_MATERIALIZED,
    )
    recorded_costs = np.asarray(
        [float(row["cost_r"]) for row in pool_rows], dtype=np.float64
    )
    recorded_commission = np.asarray(
        [float(row.get("commission_r") or 0.0) for row in pool_rows],
        dtype=np.float64,
    )
    broker_true_commission = np.empty(len(pool_rows), dtype=np.float64)
    coverage: dict[str, int] = {}
    mapped_symbols: dict[str, str] = {}
    for index, row in enumerate(pool_rows):
        canonical = str(row["symbol"])
        broker_symbol = FTMO_BROKER_SYMBOLS.get(canonical, canonical)
        mapped_symbols[canonical] = broker_symbol
        try:
            record = truth.instrument("FTMO", broker_symbol)
            commission_usd, detail = commission_usd_per_lot(
                record, float(row["entry_price"])
            )
            usd_per_price_unit = _usd_per_price_unit_per_lot(record)
        except CostTruthError as exc:
            raise CQRefusal(
                f"broker_true_commission_unpriced:{canonical}:{exc}"
            ) from exc
        stop_distance = abs(float(row["entry_price"]) - float(row["stop_loss"]))
        if stop_distance <= 0:
            raise CQRefusal(f"broker_true_commission_zero_stop:{index}")
        broker_true_commission[index] = float(commission_usd) / (
            stop_distance * float(usd_per_price_unit)
        )
        coverage_key = str((detail or {}).get("coverage") or record["commission"]["coverage"])
        coverage[coverage_key] = coverage.get(coverage_key, 0) + 1

    delta = broker_true_commission - recorded_commission
    repriced_costs = recorded_costs + delta
    identity = bool(np.array_equal(broker_true_commission, recorded_commission))

    def population_summary(mask: np.ndarray) -> dict[str, Any]:
        selected = np.flatnonzero(mask)
        gross = np.asarray(
            [
                float(pool_rows[i]["opportunity_net_proxy_r"])
                + float(pool_rows[i]["cost_r"])
                for i in selected
            ],
            dtype=np.float64,
        )
        old_net = gross - recorded_costs[selected]
        new_net = gross - repriced_costs[selected]
        return {
            "n": int(len(selected)),
            "recorded_mean_net_r": float(np.mean(old_net)) if len(selected) else None,
            "broker_true_mean_net_r": float(np.mean(new_net)) if len(selected) else None,
            "mean_net_delta_r": float(np.mean(new_net - old_net)) if len(selected) else None,
            "recorded_commission_mean_r": (
                float(np.mean(recorded_commission[selected])) if len(selected) else None
            ),
            "broker_true_commission_mean_r": (
                float(np.mean(broker_true_commission[selected])) if len(selected) else None
            ),
        }

    liquidity_splits = {
        split: population_summary(np.logical_and(mask, liquidity_mask))
        for split, mask in masks.items()
    }
    report = {
        "status": (
            "CJ_COMMISSION_EXACTLY_MATCHES_CN_BROKER_TRUE_REPRICE"
            if identity
            else "CJ_COMMISSION_REPLACED_BY_CN_BROKER_TRUE_REPRICE"
        ),
        "account": "FTMO",
        "rows_repriced": len(pool_rows),
        "unpriced_rows": 0,
        "exact_identity_rows": int(np.sum(delta == 0.0)),
        "nonidentity_rows": int(np.sum(delta != 0.0)),
        "max_abs_commission_delta_r": float(np.max(np.abs(delta))),
        "mean_commission_delta_r": float(np.mean(delta)),
        "coverage_rows": dict(sorted(coverage.items())),
        "canonical_to_broker_symbols": dict(sorted(mapped_symbols.items())),
        "token_bound_config_bytes_read": False,
        "cost_call_chain": (
            "src.costs.model.commission_usd_per_lot + "
            "_usd_per_price_unit_per_lot over stop distance"
        ),
        "cost_model_sha256": _sha256_file(REPO / "src/costs/model.py"),
        "cn_live_engine_sha256": _sha256_file(
            REPO / "src/components/broker_net_cost_engine.py"
        ),
        "canonical_artifact": BROKER_TRUE_COSTS_CANONICAL,
        "materialized_identical_artifact": _repo_path(
            BROKER_TRUE_COSTS_MATERIALIZED
        ),
        "artifact_sha256": digest,
        "liquidity_sweep_reclaim_long_splits": liquidity_splits,
    }
    return repriced_costs, report


def _cost_components(
    pool_rows: Sequence[Mapping[str, Any]], mask: np.ndarray
) -> dict[str, Any]:
    fields = (
        "spread_r",
        "commission_r",
        "commission_r_broker_true_measured",
        "swap_cost_r",
        "expected_slippage_r",
    )
    selected = np.flatnonzero(mask)
    result: dict[str, Any] = {}
    for field in fields:
        values = np.asarray(
            [
                float(pool_rows[index].get(field) or 0.0)
                for index in selected
            ],
            dtype=np.float64,
        )
        result[field] = {
            "n": int(len(values)),
            "nonzero": int(np.count_nonzero(np.abs(values) > TOL)),
            "mean_r": float(np.mean(values)) if len(values) else None,
            "sum_r": float(np.sum(values)) if len(values) else 0.0,
        }
    residuals = []
    for index in selected:
        row = pool_rows[index]
        component_sum = sum(
            float(row.get(field) or 0.0)
            for field in ("spread_r", "commission_r", "swap_cost_r", "expected_slippage_r")
        )
        residuals.append(float(row["cost_r"]) - component_sum)
    residual = np.asarray(residuals, dtype=np.float64)
    result["cost_minus_cn_four_terms"] = {
        "max_abs_r": float(np.max(np.abs(residual))) if len(residual) else None,
        "mean_r": float(np.mean(residual)) if len(residual) else None,
    }
    return result


def _iso_from_epoch_us(value: int) -> str:
    if value < 0:
        raise CQRefusal(f"negative_exit_epoch_us:{value}")
    epoch = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    return _iso(epoch + dt.timedelta(microseconds=int(value)))


def _repair_candidate_input(row: Mapping[str, Any]) -> dict[str, Any]:
    """Project CJ's row to fields available when the generator makes its decision.

    The compact pool also carries post-decision economic labels. Passing the whole row
    through the production transform would not move its output, but retaining those fields
    beside a candidate would blur the source boundary this repair is meant to make explicit.
    """

    fields = (
        "candidate_id",
        "symbol",
        "side",
        "direction",
        "origin_family",
        "framework",
        "route_family",
        "setup_family",
        "bucket_source_family",
        "decision_time_utc",
        "decision_timeframe",
        "market_timeframe",
        "session_bucket",
        "authority_session",
        "kill_zone",
        "route_session",
        "utc_hour_bucket",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "policy_target_r",
        "raw_target_r",
        "risk_per_trade_pct",
        "effective_order_type",
    )
    projected = {field: row.get(field) for field in fields if field in row}
    projected["source_fields"] = {
        "source_candidate_id": str(row["candidate_id"]),
        "source_decision_time_utc": str(row["decision_time_utc"]),
        "source_arm_id": ARM_ID,
    }
    return projected


def _select_breaker_repair_cell(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    eligible = [
        dict(cell)
        for cell in cells
        if cell["populations"]["CURRENT_BREAKER_RE_ENTRY"]["verdict"]
        == "PERSISTENT_NET_POSITIVE"
    ]
    if not eligible:
        raise CQRefusal("current_breaker_repair_has_no_persistent_positive_cell")
    selected = sorted(
        eligible,
        key=lambda cell: (
            -float(
                cell["populations"]["CURRENT_BREAKER_RE_ENTRY"]["splits"]["TRAIN"][
                    "mean_net_r"
                ]
            ),
            str(cell["orientation"]),
            float(cell["target_distance_D"]),
            float(cell["stop_distance_D"]),
        ),
    )[0]
    if not (
        selected["orientation"] == "inverted"
        and float(selected["target_distance_D"]) == BREAKER_TARGET_DISTANCE_D
        and float(selected["stop_distance_D"]) == BREAKER_STOP_DISTANCE_D
    ):
        raise CQRefusal(
            "production_breaker_transform_does_not_match_selected_cell:"
            f"{selected['cell_id']}"
        )
    return selected


def materialize_breaker_repair(
    *,
    pool_rows: Sequence[Mapping[str, Any]],
    summaries: Mapping[str, Mapping[str, Any]],
    masks: Mapping[str, np.ndarray],
    costs: np.ndarray,
    cells: Sequence[Mapping[str, Any]],
    targets: np.ndarray,
    stops: np.ndarray,
    output_path: Path = DEFAULT_REPAIR_TRADES,
    receipt_path: Path = DEFAULT_REPAIR_RECEIPT,
) -> dict[str, Any]:
    """Carry the winning declared cell into an exact, gate-ready TradeRecord surface."""

    selected = _select_breaker_repair_cell(cells)
    orientation = str(selected["orientation"])
    target_d = float(selected["target_distance_D"])
    stop_d = float(selected["stop_distance_D"])
    target_position = int(np.flatnonzero(targets == target_d)[0])
    stop_position = int(np.flatnonzero(stops == stop_d)[0])
    summary = summaries[orientation]
    target_indices = summary["target_index"][:, target_position]
    stop_indices = summary["stop_index"][:, stop_position]
    target_times = summary["target_time_us"][:, target_position]
    stop_times = summary["stop_time_us"][:, stop_position]
    breaker = np.asarray(
        [str(row.get("origin_family") or "") == "current_breaker_re_entry" for row in pool_rows],
        dtype=bool,
    )
    selected_indices = np.flatnonzero(breaker)
    outcomes: dict[str, int] = {}
    source_modes: dict[str, int] = {}
    split_counts = {"TRAIN": 0, "HOLDOUT": 0}
    unique_join_keys: set[tuple[str, str]] = set()
    transformed_ids: set[str] = set()
    gross_values: list[float] = []
    grid_cost_values: list[float] = []
    grid_net_values: list[float] = []
    split_gross = {"TRAIN": [], "HOLDOUT": [], "FULL": []}
    split_net = {"TRAIN": [], "HOLDOUT": [], "FULL": []}

    with _DeterministicGzipWriter(output_path) as handle:
        for index in selected_indices:
            pool_row = pool_rows[int(index)]
            target_index = int(target_indices[index])
            stop_index = int(stop_indices[index])
            if target_index < stop_index:
                outcome = "TARGET"
                exit_us = int(target_times[index])
                gross_r = target_d / stop_d
            elif stop_index < target_index:
                outcome = "STOP"
                exit_us = int(stop_times[index])
                gross_r = -1.0
            elif target_index != INF_INDEX:
                outcome = "AMBIGUOUS_CONSERVATIVE_STOP"
                exit_us = int(stop_times[index])
                gross_r = -1.0
            else:
                outcome = "HORIZON"
                exit_us = int(summary["terminal_time_us"][index])
                gross_r = float(summary["terminal_signed_d"][index]) / stop_d

            decision = _parse_utc(pool_row["decision_time_utc"])
            exit_utc = _parse_utc(_iso_from_epoch_us(exit_us))
            if not (
                decision < exit_utc <= decision + dt.timedelta(minutes=HORIZON_MINUTES)
            ):
                raise CQRefusal(
                    "repair_exit_outside_frozen_horizon:"
                    f"{pool_row['candidate_id']}:{decision}:{exit_utc}"
                )
            repaired = apply_current_breaker_re_entry_repair(
                _repair_candidate_input(pool_row), enabled=True
            )
            entry = float(repaired["entry_price"])
            stop = float(repaired["stop_loss"])
            sl_distance = abs(entry - stop)
            if not math.isclose(
                sl_distance,
                abs(float(pool_row["entry_price"]) - float(pool_row["stop_loss"])) * stop_d,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise CQRefusal("repair_transform_stop_distance_mismatch")
            grid_cost_r = float(costs[index]) / stop_d
            grid_net_r = gross_r - grid_cost_r
            split = "TRAIN" if bool(masks["TRAIN"][index]) else "HOLDOUT"
            broker_symbol = FTMO_BROKER_SYMBOLS.get(
                str(pool_row["symbol"]), str(pool_row["symbol"])
            )
            source_mode = str(summary["source_mode"][index])
            trade = {
                "schema": REPAIR_TRADE_SCHEMA,
                "sleeve": REPAIR_SLEEVE,
                "source_arm_id": ARM_ID,
                "source_candidate_id": str(pool_row["candidate_id"]),
                "repaired_candidate_id": str(repaired["candidate_id"]),
                "decision_split": split,
                "symbol": str(pool_row["symbol"]),
                "broker_symbol": broker_symbol,
                "entry_utc": _iso(decision),
                "exit_utc": _iso(exit_utc),
                "direction": 1 if str(repaired["side"]) == "LONG" else -1,
                "side": str(repaired["side"]),
                "entry_price": entry,
                "sl_distance_price": sl_distance,
                "stop_loss": stop,
                "take_profit_1": float(repaired["take_profit_1"]),
                "r_gross": gross_r,
                "grid_cost_r": grid_cost_r,
                "grid_net_r": grid_net_r,
                "outcome": outcome,
                "path_source_mode": source_mode,
                "candidate_transform_id": BREAKER_TRANSFORM_ID,
                "candidate": repaired,
                "features": {
                    "source_candidate_id": str(pool_row["candidate_id"]),
                    "candidate_transform_id": BREAKER_TRANSFORM_ID,
                    "path_source_mode": source_mode,
                    "exit_reason": outcome,
                    "decision_split": split,
                },
            }
            handle.write(
                json.dumps(trade, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                + "\n"
            )
            join_key = (str(pool_row["candidate_id"]), _iso(decision))
            if join_key in unique_join_keys:
                raise CQRefusal(f"duplicate_repair_join_key:{join_key}")
            unique_join_keys.add(join_key)
            transformed_ids.add(str(repaired["candidate_id"]))
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
            source_modes[source_mode] = source_modes.get(source_mode, 0) + 1
            split_counts[split] += 1
            gross_values.append(gross_r)
            grid_cost_values.append(grid_cost_r)
            grid_net_values.append(grid_net_r)
            split_gross[split].append(gross_r)
            split_gross["FULL"].append(gross_r)
            split_net[split].append(grid_net_r)
            split_net["FULL"].append(grid_net_r)

    selected_metrics = selected["populations"]["CURRENT_BREAKER_RE_ENTRY"]["splits"]
    materialized_metrics: dict[str, Any] = {}
    for split in ("TRAIN", "HOLDOUT", "FULL"):
        materialized_metrics[split] = {
            "n": len(split_net[split]),
            "mean_gross_r": float(np.mean(split_gross[split])),
            "mean_grid_cost_r": float(
                np.mean(
                    [
                        grid_cost_values[position]
                        for position, source_index in enumerate(selected_indices)
                        if split == "FULL" or bool(masks[split][source_index])
                    ]
                )
            ),
            "mean_net_r": float(np.mean(split_net[split])),
        }
        if not (
            materialized_metrics[split]["n"] == int(selected_metrics[split]["n"])
            and math.isclose(
                materialized_metrics[split]["mean_gross_r"],
                float(selected_metrics[split]["mean_gross_r"]),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            and math.isclose(
                materialized_metrics[split]["mean_net_r"],
                float(selected_metrics[split]["mean_net_r"]),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            raise CQRefusal(f"repair_materialization_metric_mismatch:{split}")

    receipt = _write_rooted_json(
        receipt_path,
        {
            "schema": REPAIR_SCHEMA,
            "generated_at_utc": _utc_now(),
            "source_head": _repo_head(),
            "surface": "VAL",
            "billed": False,
            "march_2026_outcomes_read": False,
            "february_2026_economics_read": False,
            "selection_rule": (
                "Among all predeclared CURRENT_BREAKER_RE_ENTRY cells net-positive on both "
                "TRAIN and HOLDOUT, maximize TRAIN mean net R; break ties by orientation, "
                "target distance, then stop distance."
            ),
            "eligible_persistent_net_positive_cells": sum(
                cell["populations"]["CURRENT_BREAKER_RE_ENTRY"]["verdict"]
                == "PERSISTENT_NET_POSITIVE"
                for cell in cells
            ),
            "selected_cell_id": selected["cell_id"],
            "selected_cell": {
                "orientation": orientation,
                "target_distance_D": target_d,
                "stop_distance_D": stop_d,
                "reward_to_risk": target_d / stop_d,
                "verdict": selected["populations"]["CURRENT_BREAKER_RE_ENTRY"]["verdict"],
                "grid_metrics": selected_metrics,
            },
            "candidate_transform": {
                "id": BREAKER_TRANSFORM_ID,
                "sleeve": REPAIR_SLEEVE,
                "implementation": "src/components/current_breaker_re_entry_repair.py",
                "entry_rule": "fixed",
                "orientation": "inverted",
                "target_distance_D": BREAKER_TARGET_DISTANCE_D,
                "stop_distance_D": BREAKER_STOP_DISTANCE_D,
                "runtime_default": "off",
                "outcome_fields_enter_transform": False,
            },
            "trade_records": {
                "path": _repo_path(output_path),
                "sha256": _sha256_file(output_path),
                "rows": len(selected_indices),
                "unique_source_join_keys": len(unique_join_keys),
                "unique_transformed_candidate_ids": len(transformed_ids),
                "split_counts": split_counts,
                "outcomes": dict(sorted(outcomes.items())),
                "path_source_modes": dict(sorted(source_modes.items())),
                "materialized_metrics": materialized_metrics,
            },
            "invariants": {
                "all_rows_current_breaker_re_entry": True,
                "same_entry_and_decision_time": True,
                "all_exits_strictly_after_entry_and_within_120_minutes": True,
                "production_transform_used_for_every_candidate": True,
                "materialized_metrics_match_selected_grid_cell": True,
                "broker_module_imported": False,
                "token_bound_config_bytes_read": False,
            },
            "status": "REPAIR_CANDIDATE_MATERIALIZED_FOR_RATIFIED_GATE",
        },
    )
    return receipt


def analyze_grid(
    *,
    registry_path: Path,
    pool_path: Path = DEFAULT_POOL,
    sidecar_path: Path = DEFAULT_SIDECAR,
    pool_manifest_path: Path = DEFAULT_POOL_MANIFEST,
    grid_path: Path = DEFAULT_GRID,
    looks_path: Path = DEFAULT_LOOKS,
    commit_looks: bool = False,
) -> dict[str, Any]:
    protocol = load_protocol()
    load_path_contract()
    authority = authenticate_lane_registry(registry_path)
    m1_sources, tick_sources = source_records(authority)
    del m1_sources  # The committed sidecar is the M1 authority during analysis.
    pool_rows, pool_meta = load_pool_rows(pool_path)
    pool_manifest = json.loads(pool_manifest_path.read_text(encoding="utf-8"))
    if (
        pool_manifest.get("schema") != POOL_MANIFEST_SCHEMA
        or pool_manifest.get("self_sha256")
        != _canonical_sha256(
            {key: value for key, value in pool_manifest.items() if key != "self_sha256"}
        )
        or (pool_manifest.get("base_pool") or {}).get("sha256") != pool_meta["sha256"]
        or (pool_manifest.get("sidecar") or {}).get("sha256") != _sha256_file(sidecar_path)
        or (pool_manifest.get("lane_authority") or {}).get("registry_root_sha256")
        != authority.registry_root_sha256
    ):
        raise CQRefusal("path_pool_manifest_or_binding_invalid")

    targets = np.asarray(protocol["geometry"]["target_distance_in_D"], dtype=np.float64)
    stops = np.asarray(protocol["geometry"]["stop_distance_in_D"], dtype=np.float64)
    if len(targets) * len(stops) != 99:
        raise CQRefusal("frozen_grid_dimensions_invalid")
    summaries, sidecar_validation = load_path_summaries(
        pool_rows=pool_rows,
        sidecar_path=sidecar_path,
        targets=targets,
        stops=stops,
    )
    tick_resolution = apply_tick_priority(
        summaries=summaries,
        pool_rows=pool_rows,
        tick_sources=tick_sources,
        targets=targets,
        stops=stops,
    )
    for orientation in protocol["geometry"]["orientations"]:
        if not np.isfinite(summaries[orientation]["terminal_signed_d"]).all():
            raise CQRefusal(f"terminal_close_missing:{orientation}")

    masks, split_meta = _split_masks(pool_rows)
    origins = np.asarray([str(row.get("origin_family") or "") for row in pool_rows], dtype="U64")
    sides = np.asarray([str(row.get("side") or "").upper() for row in pool_rows], dtype="U8")
    populations = {
        "FULL_POOL": np.ones(len(pool_rows), dtype=bool),
        "CURRENT_BREAKER_RE_ENTRY": origins == "current_breaker_re_entry",
        "LIQUIDITY_SWEEP_RECLAIM_LONG": np.logical_and(
            origins == "liquidity_sweep_reclaim", sides == "LONG"
        ),
    }
    costs, broker_true_reprice = _broker_true_cost_vector(
        pool_rows,
        masks,
        populations["LIQUIDITY_SWEEP_RECLAIM_LONG"],
    )
    cells: list[dict[str, Any]] = []
    for orientation in protocol["geometry"]["orientations"]:
        summary = summaries[orientation]
        for target_position, target_d in enumerate(targets):
            target_index = summary["target_index"][:, target_position]
            for stop_position, stop_d in enumerate(stops):
                stop_index = summary["stop_index"][:, stop_position]
                target_hit = target_index < stop_index
                stop_hit = stop_index < target_index
                ambiguous = np.logical_and(
                    target_index == stop_index,
                    target_index != INF_INDEX,
                )
                horizon = np.logical_and(
                    target_index == INF_INDEX,
                    stop_index == INF_INDEX,
                )
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
                outcome = np.full(len(pool_rows), "HORIZON", dtype="U12")
                outcome[target_hit] = "TARGET"
                outcome[stop_hit] = "STOP"
                outcome[ambiguous] = "AMBIGUOUS"
                if not np.all(target_hit | stop_hit | ambiguous | horizon):
                    raise CQRefusal("grid_outcome_partition_invalid")
                population_results: dict[str, Any] = {}
                for population_name, population_mask in populations.items():
                    splits = {
                        split: _metrics(
                            gross=gross,
                            net=net,
                            optimistic_gross=optimistic_gross,
                            outcome=outcome,
                            ambiguous=ambiguous,
                            mask=np.logical_and(split_mask, population_mask),
                        )
                        for split, split_mask in masks.items()
                    }
                    population_results[population_name] = {
                        "verdict": _cell_verdict(splits),
                        "splits": splits,
                    }
                cells.append(
                    {
                        "cell_id": (
                            f"{orientation}|target_{target_d:g}D|stop_{stop_d:g}D"
                        ),
                        "orientation": orientation,
                        "target_distance_D": float(target_d),
                        "stop_distance_D": float(stop_d),
                        "reward_to_risk": float(target_d / stop_d),
                        "same_bar_primary_rule": "conservative_stop",
                        "populations": population_results,
                    }
                )
    if len(cells) != 198:
        raise CQRefusal(f"frozen_grid_output_count:{len(cells)}!=198")

    best: dict[str, Any] = {}
    for population_name in populations:
        by_orientation: dict[str, Any] = {}
        for orientation in protocol["geometry"]["orientations"]:
            subset = [cell for cell in cells if cell["orientation"] == orientation]
            ranked = sorted(
                subset,
                key=lambda cell: (
                    -float(
                        cell["populations"][population_name]["splits"]["TRAIN"][
                            "mean_net_r"
                        ]
                    ),
                    float(cell["target_distance_D"]),
                    float(cell["stop_distance_D"]),
                ),
            )
            selected = ranked[0]
            by_orientation[orientation] = {
                "best_train_cell_id": selected["cell_id"],
                "verdict": selected["populations"][population_name]["verdict"],
                "splits": selected["populations"][population_name]["splits"],
                "persistent_net_positive_cells": sum(
                    cell["populations"][population_name]["verdict"]
                    == "PERSISTENT_NET_POSITIVE"
                    for cell in subset
                ),
                "persistent_gross_positive_cost_vetoed_cells": sum(
                    cell["populations"][population_name]["verdict"]
                    == "PERSISTENT_GROSS_POSITIVE_COST_VETOED"
                    for cell in subset
                ),
            }
        best[population_name] = by_orientation

    all_rows = populations["FULL_POOL"]
    breaker = populations["CURRENT_BREAKER_RE_ENTRY"]
    without_breaker = np.logical_and(all_rows, ~breaker)
    suppression = {
        "declared_repair": "suppress_current_breaker_re_entry",
        "before": _recorded_metrics(pool_rows, masks, all_rows),
        "after": _recorded_metrics(pool_rows, masks, without_breaker),
    }
    suppression["verdict"] = (
        "SURVIVES_OUT_OF_CELL"
        if suppression["after"]["TRAIN"]["mean_net_r"] > 0
        and suppression["after"]["HOLDOUT"]["mean_net_r"] > 0
        else "DOES_NOT_SURVIVE_OUT_OF_CELL"
    )
    liquidity_mask = populations["LIQUIDITY_SWEEP_RECLAIM_LONG"]
    liquidity = {
        "population": "liquidity_sweep_reclaim × LONG",
        "recorded_geometry_broker_true": _recorded_metrics(
            pool_rows,
            masks,
            liquidity_mask,
            repriced_costs=costs,
        ),
        "cost_components_full": _cost_components(pool_rows, liquidity_mask),
        "commission_reprice": broker_true_reprice,
    }

    declared = summaries["as_declared"]
    recorded_ambiguous = np.logical_and(
        declared["recorded_target_index"] == declared["recorded_stop_index"],
        declared["recorded_target_index"] != INF_INDEX,
    )
    source_mode = declared["source_mode"]
    ambiguity = {
        "n_rows": len(pool_rows),
        "ambiguous_rows": int(recorded_ambiguous.sum()),
        "frequency": float(recorded_ambiguous.mean()),
        "prior_bound": [0.0, 0.1191],
        "bound_status": "RETIRED_BY_PATH_COMPLETE_MEASUREMENT",
        "ordered_tick_rows": int(np.sum(source_mode == "ORDERED_TICK")),
        "m1_conservative_rows": int(np.sum(source_mode == "M1_CONSERVATIVE")),
        "by_source_mode": {
            mode: {
                "rows": int(np.sum(source_mode == mode)),
                "ambiguous_rows": int(
                    np.logical_and(recorded_ambiguous, source_mode == mode).sum()
                ),
                "frequency": float(
                    recorded_ambiguous[source_mode == mode].mean()
                )
                if np.any(source_mode == mode)
                else None,
            }
            for mode in sorted(set(source_mode.tolist()))
        },
    }

    repair_receipt = materialize_breaker_repair(
        pool_rows=pool_rows,
        summaries=summaries,
        masks=masks,
        costs=costs,
        cells=cells,
        targets=targets,
        stops=stops,
    )

    result = _write_rooted_json(
        grid_path,
        {
            "schema": GRID_SCHEMA,
            "generated_at_utc": _utc_now(),
            "source_head": _repo_head(),
            "surface": "VAL",
            "billed": False,
            "graduation_authority": "NONE_FILE_ONLY",
            "march_2026_outcomes_read": False,
            "february_2026_economics_read": False,
            "broker_live_authority": False,
            "broker_mutation_enabled": False,
            "arm_id": ARM_ID,
            "protocol": _repo_path(DEFAULT_PROTOCOL),
            "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
            "path_pool_manifest": _repo_path(pool_manifest_path),
            "path_pool_manifest_sha256": _sha256_file(pool_manifest_path),
            "base_pool": pool_meta,
            "sidecar_validation": sidecar_validation,
            "lane_authority": {
                "registry_path": str(authority.registry_path),
                "registry_root_sha256": authority.registry_root_sha256,
                "source_manifest_root_sha256": authority.manifest_root_sha256,
                "purpose": PURPOSE_LANE_ITERATION,
            },
            "split": split_meta,
            "tick_resolution": tick_resolution,
            "cells_per_orientation": 99,
            "orientations": list(protocol["geometry"]["orientations"]),
            "reported_cells": len(cells),
            "every_declared_cell_reported": len(cells) == 198,
            "cells": cells,
            "best_train_cells": best,
            "current_breaker_suppression": suppression,
            "liquidity_sweep_reclaim_long_broker_true": liquidity,
            "broker_true_commission_reprice": broker_true_reprice,
            "first_touch_ambiguity": ambiguity,
            "repair_gate": {
                "rule": (
                    "A repair cell must be net-positive on both TRAIN and HOLDOUT; "
                    "only then may it proceed to CANDIDATE_BOOK_V1 / B_balanced / "
                    "alpha 0.10 on RECORDED eras."
                ),
                "current_breaker_persistent_positive_cells": sum(
                    cell["populations"]["CURRENT_BREAKER_RE_ENTRY"]["verdict"]
                    == "PERSISTENT_NET_POSITIVE"
                    for cell in cells
                ),
                "suppression_verdict": suppression["verdict"],
                "candidate_transform_warranted": bool(
                    any(
                        cell["populations"]["CURRENT_BREAKER_RE_ENTRY"]["verdict"]
                        == "PERSISTENT_NET_POSITIVE"
                        for cell in cells
                    )
                    or suppression["verdict"] == "SURVIVES_OUT_OF_CELL"
                ),
                "selected_cell_id": repair_receipt["selected_cell_id"],
                "candidate_transform_id": BREAKER_TRANSFORM_ID,
                "candidate_transform_runtime_default": "off",
                "candidate_trade_records": repair_receipt["trade_records"],
                "candidate_receipt": _repo_path(DEFAULT_REPAIR_RECEIPT),
                "candidate_receipt_self_sha256": repair_receipt["self_sha256"],
                "candidate_receipt_file_sha256": _sha256_file(DEFAULT_REPAIR_RECEIPT),
            },
            "status": "FROZEN_GRID_EXACTLY_ANSWERED",
        },
    )
    looks = make_looks(result, split_meta)
    look_manifest = _write_rooted_json(
        looks_path,
        {
            "schema": LOOK_SCHEMA,
            "generated_at_utc": _utc_now(),
            "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
            "grid": _repo_path(grid_path),
            "grid_self_sha256": result["self_sha256"],
            "n_looks": len(looks),
            "looks": looks,
        },
    )
    ledger_receipt = None
    if commit_looks:
        ledger_receipt = _write_rooted_json(
            DEFAULT_LOOK_RECEIPT,
            log_looks(looks),
        )
        if not ledger_receipt["all_expected_present"]:
            raise CQRefusal("cq_look_ledger_incomplete")
        if (
            ledger_receipt["billed_true_rows"]
            or ledger_receipt["non_val_rows"]
            or ledger_receipt["february_rows"]
            or ledger_receipt["march_rows"]
        ):
            raise CQRefusal("cq_look_ledger_surface_or_billing_violation")
    return {
        "grid": _repo_path(grid_path),
        "grid_self_sha256": result["self_sha256"],
        "look_manifest": _repo_path(looks_path),
        "look_manifest_self_sha256": look_manifest["self_sha256"],
        "n_looks": len(looks),
        "logged": ledger_receipt is not None,
        "ledger_receipt_self_sha256": (
            ledger_receipt["self_sha256"] if ledger_receipt else None
        ),
        "repair_receipt": _repo_path(DEFAULT_REPAIR_RECEIPT),
        "repair_receipt_self_sha256": repair_receipt["self_sha256"],
        "repair_trades_sha256": repair_receipt["trade_records"]["sha256"],
        "repair_gate": result["repair_gate"],
        "first_touch_ambiguity": result["first_touch_ambiguity"],
        "liquidity_sweep_reclaim_long_full": result[
            "liquidity_sweep_reclaim_long_broker_true"
        ]["recorded_geometry_broker_true"]["FULL"],
    }


def _look_id(kind: str, spec: Mapping[str, Any]) -> str:
    return _canonical_sha256({"session": "CQ", "kind": kind, "spec": spec})[:20]


def make_looks(result: Mapping[str, Any], split_meta: Mapping[str, Any]) -> list[dict[str, Any]]:
    looks: list[dict[str, Any]] = []
    days = list(split_meta["dates"])
    for cell in result["cells"]:
        # CK's binding accounting rule is one look per arm x orientation x
        # geometry cell. Population strata are reported measurements of that
        # declared look, not three silently multiplied hypotheses.
        full = cell["populations"]["FULL_POOL"]
        spec = {
            "kind": "frozen_geometry",
            "arm": ARM_ID,
            "orientation": cell["orientation"],
            "target_distance_D": cell["target_distance_D"],
            "stop_distance_D": cell["stop_distance_D"],
        }
        looks.append(
            {
                "look_id": _look_id("frozen_geometry", spec),
                "kind": "frozen_geometry",
                "arm": ARM_ID,
                "spec": spec,
                "verdict": "evaluated",
                "metric": full["splits"]["FULL"]["mean_net_r"],
                "metric_name": "full_mean_net_r",
                "note": full["verdict"],
                "extra": {
                    "cell_id": cell["cell_id"],
                    "populations": cell["populations"],
                },
                "days": days,
                "receipt": _repo_path(DEFAULT_GRID),
            }
        )
    for kind, spec, metric, metric_name, note, extra in (
        (
            "current_breaker_suppression",
            {"repair": "suppress_current_breaker_re_entry", "arm": ARM_ID},
            result["current_breaker_suppression"]["after"]["FULL"]["mean_net_r"],
            "post_suppression_full_mean_net_r",
            result["current_breaker_suppression"]["verdict"],
            result["current_breaker_suppression"],
        ),
        (
            "liquidity_sweep_reclaim_long_broker_true",
            {"population": "liquidity_sweep_reclaim × LONG", "arm": ARM_ID},
            result["liquidity_sweep_reclaim_long_broker_true"][
                "recorded_geometry_broker_true"
            ]["FULL"]["mean_net_r"],
            "broker_true_full_mean_net_r",
            "CN four-term broker-true repricing",
            result["liquidity_sweep_reclaim_long_broker_true"],
        ),
        (
            "first_touch_ambiguity",
            {"geometry": "recorded", "arm": ARM_ID},
            result["first_touch_ambiguity"]["frequency"],
            "exact_ambiguity_frequency",
            "CK 0-11.91% bound retired",
            result["first_touch_ambiguity"],
        ),
    ):
        looks.append(
            {
                "look_id": _look_id(kind, spec),
                "kind": kind,
                "arm": ARM_ID,
                "spec": {"kind": kind, **spec},
                "verdict": "evaluated",
                "metric": metric,
                "metric_name": metric_name,
                "note": note,
                "extra": extra,
                "days": days,
                "receipt": _repo_path(DEFAULT_GRID),
            }
        )
    identifiers = [look["look_id"] for look in looks]
    if len(identifiers) != len(set(identifiers)):
        raise CQRefusal("duplicate_cq_look_ids")
    expected = 198 + 3
    if len(looks) != expected:
        raise CQRefusal(f"cq_look_count:{len(looks)}!={expected}")
    return looks


def log_looks(looks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ledger_path = Path(DEFAULT_ITERATION_LEDGER)
    before = read_rows(ledger_path)
    existing = {
        str((row.get("extra") or {}).get("look_id"))
        for row in before
        if row.get("session") == "CQ" and isinstance(row.get("extra"), dict)
    }
    ledger = IterationLedger(ledger_path, session="CQ", run_id=RUN_ID)
    written: list[str] = []
    skipped: list[str] = []
    mechanism_by_kind = {
        "frozen_geometry": "true_utc_path_complete_geometry",
        "current_breaker_suppression": "current_breaker_re_entry_repair",
        "liquidity_sweep_reclaim_long_broker_true": "liquidity_sweep_reclaim_cost_truth",
        "first_touch_ambiguity": "true_utc_first_touch_ambiguity",
    }
    for look in looks:
        identifier = str(look["look_id"])
        if identifier in existing:
            skipped.append(identifier)
            continue
        ledger.record(
            mechanism=mechanism_by_kind[str(look["kind"])],
            sleeve=str(look["arm"]),
            spec=dict(look["spec"]),
            days=list(look["days"]),
            engine_version=ENGINE_VERSION,
            verdict=str(look["verdict"]),
            metric=look["metric"],
            metric_name=str(look["metric_name"]),
            note=str(look["note"]),
            receipt=str(look["receipt"]),
            extra={"look_id": identifier, **dict(look["extra"])},
        )
        written.append(identifier)
        existing.add(identifier)
    after = read_rows(ledger_path)
    cq_rows = [row for row in after if row.get("session") == "CQ"]
    present = {
        str((row.get("extra") or {}).get("look_id"))
        for row in cq_rows
        if isinstance(row.get("extra"), dict)
    }
    return {
        "schema": "gtos-session-cq-look-ledger-receipt-v1",
        "generated_at_utc": _utc_now(),
        "ledger": _repo_path(ledger_path),
        "ledger_sha256": _sha256_file(ledger_path),
        "expected_looks": len(looks),
        "written_this_run": len(written),
        "idempotently_skipped": len(skipped),
        "session_cq_rows_after": len(cq_rows),
        "all_expected_present": all(str(look["look_id"]) in present for look in looks),
        "billed_true_rows": sum(bool(row.get("billed")) for row in cq_rows),
        "non_val_rows": sum(str(row.get("surface")) != "VAL" for row in cq_rows),
        "february_rows": sum(
            any(str(day).startswith("2026-02") for day in (row.get("date_span") or []))
            for row in cq_rows
        ),
        "march_rows": sum(
            any(str(day).startswith("2026-03") for day in (row.get("date_span") or []))
            for row in cq_rows
        ),
        "written_look_ids": written,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="materialize the path-complete S0R0 sidecar")
    build.add_argument("--lane-input-registry", type=Path, required=True)
    build.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    build.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    build.add_argument("--manifest", type=Path, default=DEFAULT_POOL_MANIFEST)
    analyze = sub.add_parser("analyze", help="answer every frozen cell from the sidecar")
    analyze.add_argument("--lane-input-registry", type=Path, required=True)
    analyze.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    analyze.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    analyze.add_argument("--manifest", type=Path, default=DEFAULT_POOL_MANIFEST)
    analyze.add_argument("--grid", type=Path, default=DEFAULT_GRID)
    analyze.add_argument("--looks", type=Path, default=DEFAULT_LOOKS)
    analyze.add_argument("--commit-looks", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        result = build_sidecar(
            registry_path=args.lane_input_registry,
            pool_path=args.pool,
            sidecar_path=args.sidecar,
            manifest_path=args.manifest,
        )
        output = {
            "manifest": _repo_path(args.manifest),
            "manifest_self_sha256": result["self_sha256"],
            "sidecar": result["sidecar"],
            "status": result["status"],
        }
    else:
        output = analyze_grid(
            registry_path=args.lane_input_registry,
            pool_path=args.pool,
            sidecar_path=args.sidecar,
            pool_manifest_path=args.manifest,
            grid_path=args.grid,
            looks_path=args.looks,
            commit_looks=args.commit_looks,
        )
    print(json.dumps(_native(output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
