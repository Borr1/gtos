"""Deterministic, arm-neutral, file-backed replay preparation packs.

Prepared packs contain only immutable pre-decision market state and base
candidate material.  They never contain account, broker, portfolio, selector
factor, sizing-factor, fill, or outcome state.  The chronological reducer
consumes the records in their sealed order and keeps all mutable state private.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

from compression import zstd

from src.models.market_state_models import MarketStateObject


PACK_SCHEMA = "gtos.replay_acceleration.prepared_day_pack.v1"
WINDOW_SCHEMA = "gtos.replay_acceleration.prepared_window.v1"
MANIFEST_NAME = "PREPARED_DAY_PACK_MANIFEST.json"
SEALED_NAME = "SEALED"
FACTORIAL_RUNTIME_PREFIX = "b7_5_selection_sizing_factorial_"
FACTORIAL_HARNESS_KEY = "b7_5_selection_sizing_factorial_arm_binding"
FACTORIAL_SIZING_RUNTIME_KEYS = frozenset(
    {
        "scheduler_v4_best_trade_allocator_dynamic_budget_quality_gate_enabled",
    }
)
MAX_SHARD_BYTES = 128 * 1024 * 1024
DEFAULT_TARGET_RAW_SHARD_BYTES = 32 * 1024 * 1024
MAX_RECORD_BYTES = 128 * 1024 * 1024

_WINDOW_FIELDS = {
    "schema",
    "trading_day",
    "window_ordinal",
    "decision_time_utc",
    "calendar_no_session_breadth_guard",
    "symbols",
}
_SYMBOL_FIELDS = {
    "symbol",
    "status",
    "asof_row",
    "mso_payload",
    "candidates",
}
_BINDING_FIELDS = {
    "days",
    "symbols",
    "factor_neutral_config_root_sha256",
    "source_identity_root_sha256",
    "max_candidates_per_symbol_window",
}
_MANIFEST_FIELDS = {
    "schema",
    "status",
    "format",
    "compression",
    "max_shard_bytes",
    "max_record_bytes",
    "target_raw_shard_bytes",
    "bindings",
    "window_inventory",
    "record_count",
    "ordered_record_root_sha256",
    "shards",
    "pack_root_sha256",
}
_PREPARED_SYMBOL_STATUSES = frozenset(
    {"prepared", "source_skipped", "source_incomplete", "market_state_failed"}
)
_SKIPPED_RAW_DATA_STATUSES_BY_STATUS = {
    "source_skipped": frozenset(
        {
            "calendar_no_session_breadth_guard_day_skipped",
            "ftmo_verified_no_session_day_symbol_skipped",
        }
    ),
    "source_incomplete": frozenset(
        {
            "source_required_insufficient_live_timeframes",
        }
    ),
    "market_state_failed": frozenset(
        {
            "source_required_market_state_compute_failed",
            "source_required_market_state_failed",
        }
    ),
}
_POSTDECISION_FIELD_NAMES = frozenset(
    {
        "account",
        "account_balance",
        "account_equity",
        "account_state",
        "balance",
        "broker",
        "broker_state",
        "cash_pnl",
        "close_reason",
        "equity",
        "exit_price",
        "fill",
        "fill_id",
        "fill_price",
        "fill_time_utc",
        "filled_price",
        "fills",
        "mae",
        "mae_r",
        "mfe",
        "mfe_r",
        "open_positions",
        "pending_orders",
        "pnl",
        "realized_pnl",
        "reservation",
        "reservation_state",
        "terminal_r",
        "trade_result",
        "unrealized_pnl",
    }
)


class PreparedDayPackError(ValueError):
    """Stable fail-closed prepared-pack contract error."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _stable_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def _require_json_tree(value: Any, *, path: str = "$") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PreparedDayPackError(f"nonfinite_value:{path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_json_tree(item, path=f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise PreparedDayPackError(f"non_string_key:{path}")
            _require_json_tree(item, path=f"{path}.{key}")
        return
    raise PreparedDayPackError(
        f"non_json_prepared_value:{path}:{type(value).__name__}"
    )


def _parse_utc(value: Any, *, path: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise PreparedDayPackError(f"prepared_timestamp_invalid:{path}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise PreparedDayPackError(f"prepared_timestamp_invalid:{path}") from None
    if parsed.tzinfo is None:
        raise PreparedDayPackError(f"prepared_timestamp_invalid:{path}")
    return parsed.astimezone(timezone.utc)


def _validate_predecision_tree(
    value: Any,
    *,
    decision_time: datetime,
    path: str,
    parent_key: str | None = None,
) -> None:
    """Reject post-decision namespaces and timestamps beyond the decision."""

    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            child_path = f"{path}.{key}"
            if normalized in _POSTDECISION_FIELD_NAMES:
                raise PreparedDayPackError(
                    f"prepared_postdecision_field_forbidden:{child_path}"
                )
            if item is not None and (
                normalized.endswith("_utc")
                or normalized.endswith("_utc_by_timeframe")
                or normalized == "timestamp_utc"
            ):
                if item == "":
                    # Optional lifecycle timestamps use the producer's empty
                    # sentinel until the pre-decision event has occurred.
                    pass
                elif isinstance(item, str):
                    observed = _parse_utc(item, path=child_path)
                    if observed > decision_time:
                        raise PreparedDayPackError(
                            f"prepared_future_timestamp:{child_path}"
                        )
                elif isinstance(item, Mapping) and normalized.endswith(
                    "_utc_by_timeframe"
                ):
                    for timeframe, timestamp in item.items():
                        observed = _parse_utc(
                            timestamp,
                            path=f"{child_path}.{timeframe}",
                        )
                        if observed > decision_time:
                            raise PreparedDayPackError(
                                f"prepared_future_timestamp:{child_path}.{timeframe}"
                            )
            _validate_predecision_tree(
                item,
                decision_time=decision_time,
                path=child_path,
                parent_key=normalized,
            )
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]"
            if parent_key == "poi_source_candle_times" and item is not None:
                observed = _parse_utc(item, path=child_path)
                if observed > decision_time:
                    raise PreparedDayPackError(
                        f"prepared_future_timestamp:{child_path}"
                    )
            _validate_predecision_tree(
                item,
                decision_time=decision_time,
                path=child_path,
                parent_key=parent_key,
            )


def _validate_bindings(bindings: Mapping[str, Any]) -> dict[str, Any]:
    if set(bindings) != _BINDING_FIELDS:
        raise PreparedDayPackError("binding_fields_invalid")
    days = bindings.get("days")
    symbols = bindings.get("symbols")
    if (
        not isinstance(days, list)
        or not days
        or days != sorted(set(days))
        or not all(isinstance(day, str) and day for day in days)
    ):
        raise PreparedDayPackError("binding_days_invalid")
    if (
        not isinstance(symbols, list)
        or not symbols
        or len(symbols) != len(set(symbols))
        or not all(isinstance(symbol, str) and symbol for symbol in symbols)
    ):
        raise PreparedDayPackError("binding_symbols_invalid")
    if not _is_sha256(bindings.get("factor_neutral_config_root_sha256")):
        raise PreparedDayPackError("factor_neutral_config_root_invalid")
    if not _is_sha256(bindings.get("source_identity_root_sha256")):
        raise PreparedDayPackError("source_identity_root_invalid")
    limit = bindings.get("max_candidates_per_symbol_window")
    if limit is not None and (type(limit) is not int or limit < 0):
        raise PreparedDayPackError("candidate_window_limit_invalid")
    result = dict(bindings)
    _require_json_tree(result)
    return result


def _validate_record(
    record: Mapping[str, Any],
    *,
    bindings: Mapping[str, Any],
) -> dict[str, Any]:
    if set(record) != _WINDOW_FIELDS or record.get("schema") != WINDOW_SCHEMA:
        raise PreparedDayPackError("prepared_window_fields_invalid")
    day = record.get("trading_day")
    ordinal = record.get("window_ordinal")
    decision_time = record.get("decision_time_utc")
    if day not in bindings["days"]:
        raise PreparedDayPackError("prepared_window_day_unbound")
    if type(ordinal) is not int or ordinal < 0:
        raise PreparedDayPackError("prepared_window_ordinal_invalid")
    if not isinstance(decision_time, str) or not decision_time:
        raise PreparedDayPackError("prepared_window_time_invalid")
    parsed_decision_time = _parse_utc(
        decision_time,
        path="$.decision_time_utc",
    )
    guard = record.get("calendar_no_session_breadth_guard")
    if not isinstance(guard, Mapping) or type(guard.get("active")) is not bool:
        raise PreparedDayPackError("prepared_window_calendar_guard_invalid")
    symbols = record.get("symbols")
    if not isinstance(symbols, list):
        raise PreparedDayPackError("prepared_window_symbols_invalid")
    if [row.get("symbol") for row in symbols if isinstance(row, Mapping)] != bindings[
        "symbols"
    ]:
        raise PreparedDayPackError("prepared_window_symbol_order_invalid")
    for symbol_row in symbols:
        if not isinstance(symbol_row, Mapping) or set(symbol_row) != _SYMBOL_FIELDS:
            raise PreparedDayPackError("prepared_symbol_fields_invalid")
        status = symbol_row.get("status")
        asof_row = symbol_row.get("asof_row")
        candidates = symbol_row.get("candidates")
        mso_payload = symbol_row.get("mso_payload")
        if status not in _PREPARED_SYMBOL_STATUSES:
            raise PreparedDayPackError("prepared_symbol_status_invalid")
        if not isinstance(asof_row, Mapping):
            raise PreparedDayPackError("prepared_symbol_asof_row_invalid")
        if not isinstance(candidates, list):
            raise PreparedDayPackError("prepared_symbol_candidates_invalid")
        if status == "prepared":
            if not isinstance(mso_payload, Mapping):
                raise PreparedDayPackError("prepared_symbol_mso_missing")
            try:
                restored = MarketStateObject.model_validate(mso_payload)
            except Exception as exc:  # noqa: BLE001
                raise PreparedDayPackError("prepared_symbol_mso_invalid") from exc
            if restored.model_dump(mode="json") != dict(mso_payload):
                raise PreparedDayPackError("mso_round_trip_mismatch")
            if int(asof_row.get("candidate_count", -1)) != len(candidates):
                raise PreparedDayPackError("prepared_candidate_count_mismatch")
            if (
                asof_row.get("raw_data_status")
                != "live_equivalent_raw_data_built_and_mso_computed"
                or asof_row.get("decision_time_utc") != decision_time
                or mso_payload.get("timestamp_utc") != decision_time
            ):
                raise PreparedDayPackError("prepared_symbol_source_contract_invalid")
            for candidate in candidates:
                if (
                    not isinstance(candidate, Mapping)
                    or candidate.get("symbol") != symbol_row.get("symbol")
                    or not isinstance(candidate.get("candidate_id"), str)
                    or not candidate.get("candidate_id")
                    or (
                        candidate.get("decision_time_utc") is not None
                        and candidate.get("decision_time_utc") != decision_time
                    )
                ):
                    raise PreparedDayPackError(
                        "prepared_candidate_identity_invalid"
                    )
        else:
            if mso_payload is not None or candidates:
                raise PreparedDayPackError(
                    "skipped_symbol_contains_prepared_payload"
                )
            if (
                asof_row.get("raw_data_status")
                not in _SKIPPED_RAW_DATA_STATUSES_BY_STATUS[status]
                or asof_row.get("candidate_count") != 0
                or asof_row.get("decision_time_utc") != decision_time
            ):
                raise PreparedDayPackError("skipped_symbol_source_contract_invalid")
        _validate_predecision_tree(
            asof_row,
            decision_time=parsed_decision_time,
            path=f"$.symbols[{symbol_row.get('symbol')}].asof_row",
        )
        if mso_payload is not None:
            _validate_predecision_tree(
                mso_payload,
                decision_time=parsed_decision_time,
                path=f"$.symbols[{symbol_row.get('symbol')}].mso_payload",
            )
        _validate_predecision_tree(
            candidates,
            decision_time=parsed_decision_time,
            path=f"$.symbols[{symbol_row.get('symbol')}].candidates",
        )
    _validate_predecision_tree(
        guard,
        decision_time=parsed_decision_time,
        path="$.calendar_no_session_breadth_guard",
    )
    result = dict(record)
    _require_json_tree(result)
    return result


def _encode_record(
    record: Mapping[str, Any],
    *,
    bindings: Mapping[str, Any],
) -> tuple[dict[str, Any], bytes, str]:
    validated = _validate_record(record, bindings=bindings)
    canonical = _canonical_bytes(validated)
    if len(canonical) + 1 > MAX_RECORD_BYTES:
        raise PreparedDayPackError("prepared_record_too_large")
    return validated, canonical + b"\n", hashlib.sha256(canonical).hexdigest()


def _manifest_root_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "pack_root_sha256"}


def _flush_shard(
    *,
    root: Path,
    shard_index: int,
    raw: bytes,
    first_record_ordinal: int,
    last_record_ordinal: int,
    row_count: int,
) -> dict[str, Any]:
    if not raw or len(raw) > MAX_SHARD_BYTES:
        raise PreparedDayPackError("raw_shard_size_invalid")
    compressed = zstd.compress(raw, level=1)
    if not compressed or len(compressed) > MAX_SHARD_BYTES:
        raise PreparedDayPackError("compressed_shard_size_invalid")
    relative = Path("shards") / f"shard-{shard_index:05d}.jsonl.zst"
    path = root / relative
    path.write_bytes(compressed)
    return {
        "path": relative.as_posix(),
        "shard_index": shard_index,
        "row_count": row_count,
        "first_record_ordinal": first_record_ordinal,
        "last_record_ordinal": last_record_ordinal,
        "raw_bytes": len(raw),
        "compressed_bytes": len(compressed),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
    }


def seal_prepared_day_pack(
    *,
    output_dir: Path,
    records: Iterable[Mapping[str, Any]],
    bindings: Mapping[str, Any],
    encoding_worker_count: int = 1,
    target_raw_shard_bytes: int = DEFAULT_TARGET_RAW_SHARD_BYTES,
) -> dict[str, Any]:
    """Seal records without allowing worker scheduling to affect pack identity."""

    if type(encoding_worker_count) is not int or not 1 <= encoding_worker_count <= 4:
        raise PreparedDayPackError("encoding_worker_count_invalid")
    if (
        type(target_raw_shard_bytes) is not int
        or target_raw_shard_bytes < 1
        or target_raw_shard_bytes > MAX_SHARD_BYTES
    ):
        raise PreparedDayPackError("target_raw_shard_bytes_invalid")
    bound = _validate_bindings(bindings)
    root = Path(output_dir)
    if root.exists():
        raise PreparedDayPackError("prepared_pack_output_exists")
    root.mkdir(parents=True, exist_ok=False)
    (root / "shards").mkdir()

    def encode(row: Mapping[str, Any]) -> tuple[dict[str, Any], bytes, str]:
        return _encode_record(row, bindings=bound)

    executor: ThreadPoolExecutor | None = None
    if encoding_worker_count == 1:
        encoded: Iterator[tuple[dict[str, Any], bytes, str]] = (
            encode(row) for row in records
        )
    else:
        executor = ThreadPoolExecutor(max_workers=encoding_worker_count)
        encoded = executor.map(
            encode,
            records,
            buffersize=encoding_worker_count * 2,
        )

    record_hashes: list[str] = []
    window_inventory: list[dict[str, Any]] = []
    shards: list[dict[str, Any]] = []
    current = bytearray()
    current_first = 0
    current_rows = 0
    previous_key: tuple[int, int, str] | None = None
    day_positions = {day: index for index, day in enumerate(bound["days"])}
    try:
        for global_ordinal, (record, raw, record_hash) in enumerate(encoded):
            key = (
                day_positions[record["trading_day"]],
                int(record["window_ordinal"]),
                str(record["decision_time_utc"]),
            )
            if previous_key is not None and key <= previous_key:
                raise PreparedDayPackError("window_order_invalid")
            previous_key = key
            if current and len(current) + len(raw) > target_raw_shard_bytes:
                shards.append(
                    _flush_shard(
                        root=root,
                        shard_index=len(shards),
                        raw=bytes(current),
                        first_record_ordinal=current_first,
                        last_record_ordinal=global_ordinal - 1,
                        row_count=current_rows,
                    )
                )
                current = bytearray()
                current_first = global_ordinal
                current_rows = 0
            current.extend(raw)
            if len(current) > MAX_SHARD_BYTES:
                raise PreparedDayPackError("raw_shard_size_invalid")
            current_rows += 1
            record_hashes.append(record_hash)
            window_inventory.append(
                {
                    "record_ordinal": global_ordinal,
                    "trading_day": record["trading_day"],
                    "window_ordinal": record["window_ordinal"],
                    "decision_time_utc": record["decision_time_utc"],
                    "record_sha256": record_hash,
                }
            )
        if current:
            shards.append(
                _flush_shard(
                    root=root,
                    shard_index=len(shards),
                    raw=bytes(current),
                    first_record_ordinal=current_first,
                    last_record_ordinal=len(record_hashes) - 1,
                    row_count=current_rows,
                )
            )
    finally:
        if executor is not None:
            executor.shutdown(wait=True, cancel_futures=True)
    if not record_hashes:
        raise PreparedDayPackError("prepared_pack_empty")

    manifest: dict[str, Any] = {
        "schema": PACK_SCHEMA,
        "status": "SEALED",
        "format": "ordered_canonical_jsonl_shards",
        "compression": "zstd_level_1",
        "max_shard_bytes": MAX_SHARD_BYTES,
        "max_record_bytes": MAX_RECORD_BYTES,
        "target_raw_shard_bytes": target_raw_shard_bytes,
        "bindings": bound,
        "window_inventory": window_inventory,
        "record_count": len(record_hashes),
        "ordered_record_root_sha256": _stable_sha256(record_hashes),
        "shards": shards,
    }
    manifest["pack_root_sha256"] = _stable_sha256(
        _manifest_root_payload(manifest)
    )
    (root / MANIFEST_NAME).write_bytes(_canonical_bytes(manifest) + b"\n")
    (root / SEALED_NAME).write_text(
        f"{manifest['pack_root_sha256']}\n",
        encoding="ascii",
    )
    return manifest


def _factor_neutral_config_projection(config: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        raise PreparedDayPackError("config_not_mapping")
    projection = dict(config)
    runtime = projection.get("gtos_vnext_runtime")
    if isinstance(runtime, Mapping):
        projection["gtos_vnext_runtime"] = {
            str(key): value
            for key, value in runtime.items()
            if not str(key).startswith(FACTORIAL_RUNTIME_PREFIX)
            and str(key) not in FACTORIAL_SIZING_RUNTIME_KEYS
        }
    harness = projection.get("broad_live_as_if_replay_harness")
    if isinstance(harness, Mapping):
        projection["broad_live_as_if_replay_harness"] = {
            str(key): value
            for key, value in harness.items()
            if str(key) != FACTORIAL_HARNESS_KEY
        }
    _require_json_tree(projection)
    return projection


def factor_neutral_config_root(config: Mapping[str, Any]) -> str:
    """Hash config after excluding only the sealed factorial binding namespace."""

    return _stable_sha256(_factor_neutral_config_projection(config))


def source_identity_root(
    sources: Mapping[str, Mapping[str, Any]],
) -> str:
    """Bind the complete selected source identity without materializing rows."""

    projection: list[dict[str, Any]] = []
    for symbol in sorted(sources):
        timeframe_map = sources[symbol]
        if not isinstance(timeframe_map, Mapping):
            raise PreparedDayPackError("source_timeframe_map_invalid")
        for timeframe in sorted(timeframe_map):
            source = timeframe_map[timeframe]
            spec = getattr(source, "spec", None)
            source_sha256 = str(getattr(source, "sha256", "") or "")
            if spec is None or not _is_sha256(source_sha256):
                raise PreparedDayPackError("source_identity_invalid")
            day_counts = getattr(source, "day_counts", {})
            if not isinstance(day_counts, Mapping):
                raise PreparedDayPackError("source_day_counts_invalid")
            projection.append(
                {
                    "symbol": str(symbol),
                    "timeframe": str(timeframe),
                    "mapped_symbol": str(
                        getattr(spec, "mapped_symbol", "") or ""
                    ),
                    "path": str(getattr(spec, "path", "") or ""),
                    "selected_sha256": source_sha256,
                    "declared_sha256": str(
                        getattr(spec, "sha256", "") or ""
                    ),
                    "source_family": str(
                        getattr(spec, "source_family", "") or ""
                    ),
                    "source_broker": str(
                        getattr(spec, "source_broker", "") or ""
                    ),
                    "source_role": str(
                        getattr(spec, "source_role", "") or ""
                    ),
                    "source_truth_scope": str(
                        getattr(spec, "source_truth_scope", "") or ""
                    ),
                    "declared_row_count": getattr(spec, "row_count", None),
                    "day_counts": {
                        str(day): int(count)
                        for day, count in sorted(day_counts.items())
                    },
                    "selected_status": str(
                        getattr(source, "selected_status", "") or ""
                    ),
                    "min_required_rows_per_day": int(
                        getattr(source, "min_required_rows_per_day", 0) or 0
                    ),
                }
            )
    if not projection:
        raise PreparedDayPackError("source_identity_empty")
    _require_json_tree(projection)
    return _stable_sha256(projection)


def assert_no_factor_reads(
    reads: Iterable[str],
    *,
    factor_namespace_absent: bool = False,
) -> None:
    factor_path = f"gtos_vnext_runtime.{FACTORIAL_RUNTIME_PREFIX}"
    harness_factor_path = (
        "broad_live_as_if_replay_harness." f"{FACTORIAL_HARNESS_KEY}"
    )
    sizing_factor_paths = {
        f"gtos_vnext_runtime.{key}" for key in FACTORIAL_SIZING_RUNTIME_KEYS
    }
    forbidden = sorted(
        {
            str(path)
            for path in reads
            if (
                not factor_namespace_absent
                and str(path) in {"*", "gtos_vnext_runtime.*"}
            )
            or str(path).startswith(factor_path)
            or str(path).startswith(harness_factor_path)
            or str(path) in sizing_factor_paths
        }
    )
    if forbidden:
        raise PreparedDayPackError(
            "factor_read_detected:" + ",".join(forbidden)
        )


def build_campaign_prepared_day_pack(
    *,
    output_dir: Path,
    campaign: Any,
    config: Mapping[str, Any],
    sources: Mapping[str, Mapping[str, Any]],
    encoding_worker_count: int = 1,
    target_raw_shard_bytes: int = DEFAULT_TARGET_RAW_SHARD_BYTES,
    borrow_campaign_cache_owner: bool = False,
) -> dict[str, Any]:
    """Run the production immutable preparation boundary and seal its output."""

    from src.research_infra import (
        v4_timewarp_simulated_live_research_loop as timewarp,
    )
    from src.research_infra.replay_acceleration_candidate_boundary import (
        ReadTrackingDict,
    )

    if tuple(getattr(campaign, "days", ())) == ():
        raise PreparedDayPackError("prepared_campaign_days_empty")
    neutral_config = _factor_neutral_config_projection(config)
    neutral_root = _stable_sha256(neutral_config)
    selected_source_root = source_identity_root(sources)
    bindings = {
        "days": list(campaign.days),
        "symbols": list(timewarp.INCLUDED_SYMBOLS),
        "factor_neutral_config_root_sha256": neutral_root,
        "source_identity_root_sha256": selected_source_root,
        "max_candidates_per_symbol_window": (
            campaign.max_candidates_per_symbol_window
        ),
    }
    tracked_config = ReadTrackingDict(neutral_config)
    started = time.perf_counter()
    cache_owner = timewarp._OWNED_CAMPAIGN_EXACT_CACHES.get()
    if borrow_campaign_cache_owner and cache_owner is None:
        raise PreparedDayPackError("prepared_pack_cache_owner_missing")
    cache_scope = (
        nullcontext(cache_owner)
        if borrow_campaign_cache_owner
        else timewarp.own_campaign_exact_caches()
    )
    with cache_scope:
        exact_cache = timewarp.CampaignExactCache.from_config(tracked_config)
        # Construction authenticates the entire config and therefore performs
        # non-semantic serialization reads.  The preparation read audit starts
        # after that binding is complete.
        tracked_config.reads.clear()
        live_replay = timewarp.LiveReplayMode(
            sources,
            tracked_config,
            campaign_exact_cache=exact_cache,
        )
        decision_core = timewarp.V4DecisionCycleCore(
            config=tracked_config,
            sources=sources,
            candidate_evaluator=timewarp.evaluate_candidate_v4,
            scheduler_allocator=timewarp.materialize_scheduler_window,
        )
        assert_no_factor_reads(
            tracked_config.reads,
            factor_namespace_absent=True,
        )
        clock = timewarp.ReplayClock(campaign.days, sources)

        def prepared_records() -> Iterator[dict[str, Any]]:
            for day in campaign.days:
                decision_times = clock.decision_times_for_day(
                    day,
                    smoke_subset=campaign.run_smoke_subset,
                )
                if not decision_times:
                    raise PreparedDayPackError(
                        "prepared_campaign_window_inventory_empty"
                    )
                if decision_times != sorted(set(decision_times)):
                    raise PreparedDayPackError(
                        "prepared_campaign_window_inventory_invalid"
                    )
                for window_ordinal, asof in enumerate(decision_times):
                    record = timewarp.prepare_arm_neutral_replay_window(
                        campaign=campaign,
                        config=tracked_config,
                        sources=sources,
                        live_replay=live_replay,
                        decision_core=decision_core,
                        day=day,
                        asof=asof,
                        window_ordinal=window_ordinal,
                    )
                    assert_no_factor_reads(
                        tracked_config.reads,
                        factor_namespace_absent=True,
                    )
                    yield record

        manifest = seal_prepared_day_pack(
            output_dir=output_dir,
            records=prepared_records(),
            bindings=bindings,
            encoding_worker_count=encoding_worker_count,
            target_raw_shard_bytes=target_raw_shard_bytes,
        )
        factor_reads = sorted(tracked_config.reads)
        assert_no_factor_reads(
            factor_reads,
            factor_namespace_absent=True,
        )
        tracked_config.reads.clear()
        cache_audit = exact_cache.audit(tracked_config)
    wall_seconds = time.perf_counter() - started
    return {
        "schema": "gtos.replay_acceleration.prepared_day_pack_build.v1",
        "status": "SEALED_ARM_NEUTRAL_PREPARATION",
        "pack_root_sha256": manifest["pack_root_sha256"],
        "record_count": manifest["record_count"],
        "shard_count": len(manifest["shards"]),
        "raw_bytes": sum(row["raw_bytes"] for row in manifest["shards"]),
        "compressed_bytes": sum(
            row["compressed_bytes"] for row in manifest["shards"]
        ),
        "preparation_wall_seconds": wall_seconds,
        "factor_reads": factor_reads,
        "factor_reads_detected": False,
        "account_state_read": False,
        "broker_state_read": False,
        "broker_mutation_enabled": False,
        "live_authority_touched": False,
        "campaign_exact_cache_audit": cache_audit,
    }


class PreparedDayPackReader:
    """Authenticate a sealed pack and consume it in exact chronological order."""

    def __init__(
        self,
        root: Path,
        *,
        expected_pack_root_sha256: str | None = None,
    ):
        self.root = Path(root)
        manifest_path = self.root / MANIFEST_NAME
        sealed_path = self.root / SEALED_NAME
        if (
            not self.root.is_dir()
            or self.root.is_symlink()
            or not manifest_path.is_file()
            or manifest_path.is_symlink()
            or not sealed_path.is_file()
            or sealed_path.is_symlink()
        ):
            raise PreparedDayPackError("prepared_pack_not_sealed")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PreparedDayPackError("prepared_pack_manifest_invalid") from exc
        if not isinstance(manifest, Mapping) or set(manifest) != _MANIFEST_FIELDS:
            raise PreparedDayPackError("prepared_pack_manifest_fields_invalid")
        self.manifest = dict(manifest)
        if (
            self.manifest.get("schema") != PACK_SCHEMA
            or self.manifest.get("status") != "SEALED"
            or self.manifest.get("format") != "ordered_canonical_jsonl_shards"
            or self.manifest.get("compression") != "zstd_level_1"
            or self.manifest.get("max_shard_bytes") != MAX_SHARD_BYTES
            or self.manifest.get("max_record_bytes") != MAX_RECORD_BYTES
        ):
            raise PreparedDayPackError("prepared_pack_manifest_contract_invalid")
        expected_root = _stable_sha256(_manifest_root_payload(self.manifest))
        if self.manifest.get("pack_root_sha256") != expected_root:
            raise PreparedDayPackError("prepared_pack_root_mismatch")
        if expected_pack_root_sha256 is not None and (
            not _is_sha256(expected_pack_root_sha256)
            or expected_pack_root_sha256 != expected_root
        ):
            raise PreparedDayPackError("prepared_pack_external_root_mismatch")
        if sealed_path.read_text(encoding="ascii") != f"{expected_root}\n":
            raise PreparedDayPackError("prepared_pack_seal_mismatch")
        self.external_root_authenticated = expected_pack_root_sha256 is not None
        self.bindings = _validate_bindings(self.manifest.get("bindings") or {})
        self._validate_inventory_and_shards()
        self._records = self._iter_records()
        self._consumed = 0
        self._finished = False

    @property
    def pack_root_sha256(self) -> str:
        return str(self.manifest["pack_root_sha256"])

    def _validate_inventory_and_shards(self) -> None:
        inventory = self.manifest.get("window_inventory")
        shards = self.manifest.get("shards")
        record_count = self.manifest.get("record_count")
        if (
            not isinstance(inventory, list)
            or not inventory
            or type(record_count) is not int
            or record_count != len(inventory)
            or not isinstance(shards, list)
            or not shards
        ):
            raise PreparedDayPackError("prepared_pack_inventory_invalid")
        hashes: list[str] = []
        previous: tuple[int, int, str] | None = None
        day_positions = {
            day: index for index, day in enumerate(self.bindings["days"])
        }
        for ordinal, row in enumerate(inventory):
            if not isinstance(row, Mapping) or set(row) != {
                "record_ordinal",
                "trading_day",
                "window_ordinal",
                "decision_time_utc",
                "record_sha256",
            }:
                raise PreparedDayPackError("prepared_pack_inventory_row_invalid")
            if row.get("record_ordinal") != ordinal or not _is_sha256(
                row.get("record_sha256")
            ):
                raise PreparedDayPackError("prepared_pack_inventory_identity_invalid")
            try:
                key = (
                    day_positions[str(row["trading_day"])],
                    int(row["window_ordinal"]),
                    str(row["decision_time_utc"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise PreparedDayPackError("prepared_pack_inventory_key_invalid") from exc
            if previous is not None and key <= previous:
                raise PreparedDayPackError("prepared_pack_inventory_order_invalid")
            previous = key
            hashes.append(str(row["record_sha256"]))
        if self.manifest.get("ordered_record_root_sha256") != _stable_sha256(hashes):
            raise PreparedDayPackError("prepared_pack_record_root_mismatch")

        expected_files = {MANIFEST_NAME, SEALED_NAME}
        next_record = 0
        for shard_index, shard in enumerate(shards):
            if not isinstance(shard, Mapping) or set(shard) != {
                "path",
                "shard_index",
                "row_count",
                "first_record_ordinal",
                "last_record_ordinal",
                "raw_bytes",
                "compressed_bytes",
                "raw_sha256",
                "compressed_sha256",
            }:
                raise PreparedDayPackError("prepared_pack_shard_row_invalid")
            expected_relative = f"shards/shard-{shard_index:05d}.jsonl.zst"
            if (
                shard.get("path") != expected_relative
                or shard.get("shard_index") != shard_index
                or shard.get("first_record_ordinal") != next_record
                or type(shard.get("row_count")) is not int
                or shard["row_count"] <= 0
                or shard.get("last_record_ordinal")
                != next_record + shard["row_count"] - 1
                or type(shard.get("raw_bytes")) is not int
                or not 0 < shard["raw_bytes"] <= MAX_SHARD_BYTES
                or type(shard.get("compressed_bytes")) is not int
                or not 0 < shard["compressed_bytes"] <= MAX_SHARD_BYTES
                or not _is_sha256(shard.get("raw_sha256"))
                or not _is_sha256(shard.get("compressed_sha256"))
            ):
                raise PreparedDayPackError("prepared_pack_shard_identity_invalid")
            path = self.root / expected_relative
            if (
                not path.is_file()
                or path.is_symlink()
                or path.stat().st_size != shard["compressed_bytes"]
            ):
                raise PreparedDayPackError("prepared_pack_shard_file_invalid")
            if _file_sha256(path) != shard["compressed_sha256"]:
                raise PreparedDayPackError("compressed_sha256_mismatch")
            expected_files.add(expected_relative)
            next_record += shard["row_count"]
        if next_record != record_count:
            raise PreparedDayPackError("prepared_pack_shard_coverage_invalid")
        actual_files = {
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        if actual_files != expected_files:
            raise PreparedDayPackError("prepared_pack_file_inventory_invalid")

    def _iter_records(self) -> Iterator[dict[str, Any]]:
        inventory = self.manifest["window_inventory"]
        global_ordinal = 0
        for shard in self.manifest["shards"]:
            compressed = (self.root / shard["path"]).read_bytes()
            try:
                decompressor = zstd.ZstdDecompressor()
                raw = decompressor.decompress(
                    compressed,
                    max_length=int(shard["raw_bytes"]) + 1,
                )
            except (EOFError, zstd.ZstdError) as exc:
                raise PreparedDayPackError("prepared_pack_zstd_invalid") from exc
            if (
                len(raw) != shard["raw_bytes"]
                or not decompressor.eof
                or decompressor.unused_data
            ):
                raise PreparedDayPackError("prepared_pack_raw_size_mismatch")
            if hashlib.sha256(raw).hexdigest() != shard["raw_sha256"]:
                raise PreparedDayPackError("prepared_pack_raw_sha256_mismatch")
            lines = raw.splitlines(keepends=True)
            if len(lines) != shard["row_count"]:
                raise PreparedDayPackError("prepared_pack_shard_row_count_mismatch")
            for line in lines:
                if not line.endswith(b"\n") or len(line) > MAX_RECORD_BYTES:
                    raise PreparedDayPackError("prepared_pack_record_framing_invalid")
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise PreparedDayPackError("prepared_pack_record_json_invalid") from exc
                if not isinstance(record, Mapping):
                    raise PreparedDayPackError("prepared_pack_record_not_mapping")
                validated = _validate_record(record, bindings=self.bindings)
                record_hash = hashlib.sha256(
                    _canonical_bytes(validated)
                ).hexdigest()
                if record_hash != inventory[global_ordinal]["record_sha256"]:
                    raise PreparedDayPackError("prepared_pack_record_sha256_mismatch")
                global_ordinal += 1
                yield validated
        if global_ordinal != self.manifest["record_count"]:
            raise PreparedDayPackError("prepared_pack_record_count_mismatch")

    def assert_compatible(
        self,
        *,
        days: Sequence[str],
        symbols: Sequence[str],
        factor_neutral_config_root_sha256: str,
        source_identity_root_sha256: str,
        max_candidates_per_symbol_window: int | None,
    ) -> None:
        observed = {
            "days": list(days),
            "symbols": list(symbols),
            "factor_neutral_config_root_sha256": factor_neutral_config_root_sha256,
            "source_identity_root_sha256": source_identity_root_sha256,
            "max_candidates_per_symbol_window": max_candidates_per_symbol_window,
        }
        if _validate_bindings(observed) != self.bindings:
            raise PreparedDayPackError("prepared_pack_binding_mismatch")

    def next_window(
        self,
        *,
        trading_day: str,
        decision_time_utc: str,
        window_ordinal: int,
    ) -> dict[str, Any]:
        if self._finished:
            raise PreparedDayPackError("prepared_pack_already_finished")
        try:
            record = next(self._records)
        except StopIteration as exc:
            raise PreparedDayPackError("prepared_pack_exhausted_early") from exc
        expected = (trading_day, window_ordinal, decision_time_utc)
        actual = (
            record["trading_day"],
            record["window_ordinal"],
            record["decision_time_utc"],
        )
        if actual != expected:
            raise PreparedDayPackError("prepared_pack_consumer_order_mismatch")
        self._consumed += 1
        return record

    def finish(self) -> None:
        if self._finished:
            return
        try:
            next(self._records)
        except StopIteration:
            pass
        else:
            raise PreparedDayPackError("prepared_pack_not_fully_consumed")
        if self._consumed != self.manifest["record_count"]:
            raise PreparedDayPackError("prepared_pack_consumed_count_mismatch")
        self._finished = True
