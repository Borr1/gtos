"""Independent persisted-byte verifier for the bounded replay source slice.

This module intentionally uses only the Python standard library.  It does not
import the slice writer, the immutable-cache implementation, or the legacy
source consumer.  The duplicate framing, normalization, canonicalization, and
root logic is deliberate: the proof must remain capable of falsifying the
writer rather than sharing its implementation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


SELECTION_SCHEMA = "gtos.replay_acceleration.slice_selection.v1"
BUNDLE_SCHEMA = "gtos.replay_acceleration.persisted_source_bundle.v1"
CASE_SCHEMA = "gtos.replay_acceleration.failure_case.v1"
MANIFEST_SCHEMA = "gtos.replay_acceleration.immutable_source_batch.v1"
SOURCE_BYTES_STAGE = "replay.source_bytes.v1"
CONFIG_PROJECTION_SCHEMA = "gtos.replay_acceleration.config_projection.v1"
VERIFIER_SCHEMA = "gtos.replay_acceleration.independent_verification.v1"
CSV_HEADER = ("time", "open", "high", "low", "close", "volume")
PHYSICAL_TIMEFRAME_ORDER = {"D1": 0, "H4": 1, "M15": 2, "M1": 3}
LOGICAL_TIMEFRAME_ORDER = {"D1": 0, "H4": 1, "H1": 2, "M15": 3, "M1": 4}
MANIFEST_FIELDS = frozenset(
    {
        "schema",
        "stage",
        "implementation_root",
        "source_identity_root",
        "source_path_root",
        "partition_root",
        "partition_symbol",
        "config_projection_root",
        "config_projection_keys",
        "payload_root",
        "byte_count",
        "record_count",
    }
)
BINDING_FIELDS = frozenset(MANIFEST_FIELDS - {"schema", "payload_root", "byte_count", "record_count"})


class VerificationRejected(RuntimeError):
    """Stable fail-closed structural rejection."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _canonical_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise VerificationRejected("noncanonical_value") from None
    return text.encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _valid_root(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(
        character in "009abcdef" for character in value
    )


def _load_canonical_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise VerificationRejected(code) from None
    if type(value) is not dict or raw != _canonical_bytes(value) + b"\n":
        raise VerificationRejected(code)
    return value


def _verify_self_root(value: Mapping[str, Any], field: str, *, code: str) -> str:
    root = value.get(field)
    if not _valid_root(root):
        raise VerificationRejected(code)
    core = {key: item for key, item in value.items() if key != field}
    if _sha256(_canonical_bytes(core)) != root:
        raise VerificationRejected(code)
    return str(root)


def _empty_projection_root() -> str:
    return _sha256(
        _canonical_bytes(
            {
                "schema": CONFIG_PROJECTION_SCHEMA,
                "keys": [],
                "values": [],
            }
        )
    )


def _safe_bundle_path(bundle_dir: Path, relative: Any) -> Path:
    if type(relative) is not str or not relative or os.path.isabs(relative):
        raise VerificationRejected("persisted_path_invalid")
    candidate = (bundle_dir / relative).resolve()
    root = bundle_dir.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise VerificationRejected("persisted_path_invalid") from None
    return candidate


def _parse_time(value: Any) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise VerificationRejected("canonical_row_time_invalid")
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise VerificationRejected("canonical_row_time_invalid") from None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _finite_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = 0.0
    if not math.isfinite(result):
        raise VerificationRejected("canonical_row_numeric_invalid")
    return result


def _normalize_csv_payload(payload: bytes, *, symbol: str) -> tuple[dict[str, Any], ...]:
    try:
        handle = io.TextIOWrapper(io.BytesIO(payload), encoding="utf-8", newline="")
        reader = csv.reader(handle, strict=True)
        header = tuple(next(reader))
        if header != CSV_HEADER:
            raise VerificationRejected("csv_header_mismatch")
        rows: list[dict[str, Any]] = []
        previous: datetime | None = None
        for raw in reader:
            if not raw:
                continue
            if len(raw) != len(CSV_HEADER):
                raise VerificationRejected("csv_row_width_mismatch")
            source = dict(zip(CSV_HEADER, raw, strict=True))
            timestamp = _parse_time(source["time"])
            if previous is not None and timestamp < previous:
                raise VerificationRejected("source_ordering_mismatch")
            previous = timestamp
            rows.append(
                {
                    "time": _iso(timestamp),
                    "time_utc": _iso(timestamp),
                    "symbol": symbol,
                    "open": _finite_float(source["open"]),
                    "high": _finite_float(source["high"]),
                    "low": _finite_float(source["low"]),
                    "close": _finite_float(source["close"]),
                    "volume": _finite_float(source["volume"]),
                }
            )
        return tuple(rows)
    except VerificationRejected:
        raise
    except (csv.Error, UnicodeError, StopIteration, ValueError):
        raise VerificationRejected("csv_framing_invalid") from None


def _rows_root(rows: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(b"gtos.replay_acceleration.canonical_rows.v1\n")
    for row in rows:
        digest.update(_canonical_bytes(dict(row)))
        digest.update(b"\n")
    return digest.hexdigest()


def _selected_day_rows(
    rows: Iterable[Mapping[str, Any]], selected_day: str
) -> tuple[dict[str, Any], ...]:
    return tuple(
        dict(row)
        for row in rows
        if _parse_time(row.get("time_utc") or row.get("time")).date().isoformat()
        == selected_day
    )


def _aggregate_h1(
    rows: Iterable[Mapping[str, Any]], *, symbol: str
) -> tuple[dict[str, Any], ...]:
    buckets: dict[datetime, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        timestamp = _parse_time(row.get("time_utc") or row.get("time"))
        bucket = timestamp.replace(minute=0, second=0, microsecond=0)
        buckets[bucket].append(row)
    output: list[dict[str, Any]] = []
    for bucket, items in sorted(buckets.items()):
        ordered = sorted(
            items,
            key=lambda item: _parse_time(item.get("time_utc") or item.get("time")),
        )
        output.append(
            {
                "time": _iso(bucket),
                "time_utc": _iso(bucket),
                "symbol": symbol,
                "open": _finite_float(ordered[0].get("open")),
                "high": max(_finite_float(row.get("high")) for row in ordered),
                "low": min(_finite_float(row.get("low")) for row in ordered),
                "close": _finite_float(ordered[-1].get("close")),
                "volume": sum(_finite_float(row.get("volume")) for row in ordered),
                "source_records": len(ordered),
            }
        )
    return tuple(output)


def _validate_selection(path: Path) -> dict[str, Any]:
    selection = _load_canonical_json(path, code="selection_receipt_invalid")
    if selection.get("schema") != SELECTION_SCHEMA:
        raise VerificationRejected("selection_receipt_invalid")
    _verify_self_root(
        selection,
        "selection_root_sha256",
        code="selection_receipt_invalid",
    )
    return selection


def _load_bundle(
    *,
    bundle_dir: Path,
    manifest_path: Path | None = None,
    sealed_path: Path | None = None,
) -> tuple[dict[str, Any], str]:
    manifest_file = manifest_path or bundle_dir / "bundle.json"
    bundle = _load_canonical_json(manifest_file, code="bundle_manifest_invalid")
    if bundle.get("schema") != BUNDLE_SCHEMA:
        raise VerificationRejected("bundle_schema_mismatch")
    root = _verify_self_root(
        bundle,
        "bundle_root_sha256",
        code="bundle_identity_mismatch",
    )
    marker = sealed_path or bundle_dir / "SEALED"
    try:
        marker_bytes = marker.read_bytes()
    except OSError:
        raise VerificationRejected("bundle_unsealed") from None
    if marker_bytes != root.encode("ascii") + b"\n":
        raise VerificationRejected("bundle_unsealed")
    return bundle, root


def _expected_cache_identity(bundle: Mapping[str, Any]) -> str:
    return _sha256(
        _canonical_bytes(
            {
                "selection_root_sha256": bundle.get("selection_root_sha256"),
                "accepted_cache_implementation_root": bundle.get(
                    "accepted_cache_implementation_root"
                ),
                "slice_code_identity_root": bundle.get("slice_code_identity_root"),
                "config_identity_root": bundle.get("config_identity_root"),
            }
        )
    )


def _verify_physical_entry(
    *,
    bundle_dir: Path,
    entry: Mapping[str, Any],
    selected_day: str,
    overrides: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    partition_id = str(entry.get("partition_id") or "")
    override = overrides.get(partition_id, {})
    legacy_path = (
        Path(override["legacy_path"])
        if override.get("legacy_path")
        else _safe_bundle_path(bundle_dir, entry.get("legacy_path"))
    )
    payload_path = (
        Path(override["payload_path"])
        if override.get("payload_path")
        else _safe_bundle_path(bundle_dir, entry.get("payload_path"))
    )
    manifest_path = (
        Path(override["manifest_path"])
        if override.get("manifest_path")
        else _safe_bundle_path(bundle_dir, entry.get("manifest_path"))
    )
    try:
        legacy = legacy_path.read_bytes()
        payload = payload_path.read_bytes()
    except OSError:
        raise VerificationRejected("persisted_bytes_missing") from None
    if legacy != payload:
        if len(payload) != int(entry.get("byte_count") or -1) or _sha256(payload) != entry.get(
            "payload_root"
        ):
            raise VerificationRejected("payload_identity_mismatch")
        raise VerificationRejected("legacy_content_bytes_mismatch")
    if _sha256(payload) != entry.get("payload_root") or len(payload) != entry.get(
        "byte_count"
    ):
        raise VerificationRejected("payload_identity_mismatch")

    manifest = _load_canonical_json(manifest_path, code="manifest_not_canonical")
    if set(manifest) != MANIFEST_FIELDS:
        raise VerificationRejected("manifest_schema_mismatch")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise VerificationRejected("manifest_schema_mismatch")
    binding = entry.get("binding")
    if type(binding) is not dict or set(binding) != BINDING_FIELDS:
        raise VerificationRejected("binding_schema_mismatch")
    for field in BINDING_FIELDS:
        if manifest.get(field) != binding.get(field):
            if field == "source_identity_root":
                raise VerificationRejected("source_identity_mismatch")
            if field in {"config_projection_root", "config_projection_keys"}:
                raise VerificationRejected("config_identity_mismatch")
            if field == "implementation_root":
                raise VerificationRejected("code_identity_mismatch")
            raise VerificationRejected("binding_identity_mismatch")
    if (
        manifest.get("stage") != SOURCE_BYTES_STAGE
        or manifest.get("config_projection_keys") != []
        or manifest.get("config_projection_root") != _empty_projection_root()
    ):
        raise VerificationRejected("config_identity_mismatch")
    manifest_bytes = manifest_path.read_bytes()
    if _sha256(manifest_bytes) != entry.get("batch_root"):
        raise VerificationRejected("manifest_identity_mismatch")
    if (
        manifest.get("payload_root") != _sha256(payload)
        or manifest.get("byte_count") != len(payload)
    ):
        raise VerificationRejected("payload_identity_mismatch")

    rows = _normalize_csv_payload(payload, symbol=str(entry.get("symbol") or ""))
    if manifest.get("record_count") != len(rows) or entry.get("record_count") != len(rows):
        raise VerificationRejected("record_count_mismatch")
    selected_rows = _selected_day_rows(rows, selected_day)
    checks = {
        "normalized_root_sha256": _rows_root(rows),
        "normalized_record_count": len(rows),
        "selected_day_root_sha256": _rows_root(selected_rows),
        "selected_day_record_count": len(selected_rows),
    }
    for field, actual in checks.items():
        if entry.get(field) != actual:
            raise VerificationRejected("canonical_structure_mismatch")
    return checks, rows


def _verify_bundle_value(
    *,
    bundle_dir: Path,
    bundle: Mapping[str, Any],
    bundle_root: str,
    selection: Mapping[str, Any],
    overrides: Mapping[str, Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    if bundle.get("selection_root_sha256") != selection.get("selection_root_sha256"):
        raise VerificationRejected("selection_binding_mismatch")
    if bundle.get("cache_identity_root") != _expected_cache_identity(bundle):
        raise VerificationRejected("stale_cache_identity_mismatch")
    selected_day = str(selection.get("selected_day") or "")
    physical = bundle.get("physical_partitions")
    logical = bundle.get("logical_partitions")
    if type(physical) is not list or type(logical) is not list:
        raise VerificationRejected("bundle_partition_schema_mismatch")
    expected_physical = sorted(
        physical,
        key=lambda row: (
            str(row.get("symbol")),
            PHYSICAL_TIMEFRAME_ORDER.get(str(row.get("physical_timeframe")), 99),
        ),
    )
    if physical != expected_physical or [row.get("index") for row in physical] != list(
        range(len(physical))
    ):
        raise VerificationRejected("partition_order_mismatch")
    expected_logical = sorted(
        logical,
        key=lambda row: (
            str(row.get("symbol")),
            LOGICAL_TIMEFRAME_ORDER.get(str(row.get("timeframe")), 99),
        ),
    )
    if logical != expected_logical or [row.get("index") for row in logical] != list(
        range(len(logical))
    ):
        raise VerificationRejected("partition_order_mismatch")

    parsed: dict[str, tuple[dict[str, Any], ...]] = {}
    physical_checks: dict[str, dict[str, Any]] = {}
    for entry in physical:
        partition_id = str(entry.get("partition_id") or "")
        if not partition_id or partition_id in parsed:
            raise VerificationRejected("partition_identity_duplicate")
        checks, rows = _verify_physical_entry(
            bundle_dir=bundle_dir,
            entry=entry,
            selected_day=selected_day,
            overrides=overrides or {},
        )
        parsed[partition_id] = rows
        physical_checks[partition_id] = checks

    rebuilt_logical: list[dict[str, Any]] = []
    for entry in logical:
        physical_id = str(entry.get("physical_partition_id") or "")
        rows = parsed.get(physical_id)
        if rows is None:
            raise VerificationRejected("logical_partition_source_missing")
        transform = entry.get("transform")
        if transform == "direct_csv_normalization":
            logical_rows = rows
        elif transform == "derived_h1_from_m15":
            logical_rows = _aggregate_h1(rows, symbol=str(entry.get("symbol") or ""))
        else:
            raise VerificationRejected("logical_transform_invalid")
        selected_rows = _selected_day_rows(logical_rows, selected_day)
        rebuilt = {
            "index": entry.get("index"),
            "symbol": entry.get("symbol"),
            "timeframe": entry.get("timeframe"),
            "physical_partition_id": physical_id,
            "transform": transform,
            "normalized_root_sha256": _rows_root(logical_rows),
            "normalized_record_count": len(logical_rows),
            "selected_day_root_sha256": _rows_root(selected_rows),
            "selected_day_record_count": len(selected_rows),
        }
        if dict(entry) != rebuilt:
            raise VerificationRejected("logical_partition_mismatch")
        rebuilt_logical.append(rebuilt)

    barrier = bundle.get("cross_symbol_barrier")
    symbols = sorted({str(row.get("symbol")) for row in logical})
    if type(barrier) is not dict or barrier != {
        "sealed": True,
        "policy_execution_entered": False,
        "symbol_count": len(symbols),
        "symbols": symbols,
        "physical_partition_count": len(physical),
        "logical_partition_count": len(logical),
    }:
        raise VerificationRejected("cross_symbol_barrier_mismatch")

    logical_root = _sha256(_canonical_bytes(rebuilt_logical))
    physical_root = _sha256(_canonical_bytes(physical_checks))
    return {
        "schema": VERIFIER_SCHEMA,
        "status": "VERIFIED",
        "bundle_root_sha256": bundle_root,
        "selection_root_sha256": selection.get("selection_root_sha256"),
        "roots": {
            "physical_recomputed": physical_root,
            "logical_recomputed": logical_root,
        },
        "counts": {
            "symbols": len(symbols),
            "physical_partitions": len(physical),
            "logical_partitions": len(logical),
            "persisted_byte_pairs_equal": len(physical),
        },
        "writer_imported": False,
        "cache_implementation_imported": False,
        "policy_execution_entered": False,
    }


def verify_bundle(*, bundle_dir: Path, selection_path: Path) -> dict[str, Any]:
    selection = _validate_selection(Path(selection_path))
    bundle, root = _load_bundle(bundle_dir=Path(bundle_dir))
    return _verify_bundle_value(
        bundle_dir=Path(bundle_dir),
        bundle=bundle,
        bundle_root=root,
        selection=selection,
    )


def verify_case(*, case_dir: Path, selection_path: Path) -> dict[str, Any]:
    case_root = Path(case_dir)
    case = _load_canonical_json(case_root / "case.json", code="failure_case_invalid")
    if case.get("schema") != CASE_SCHEMA:
        raise VerificationRejected("failure_case_invalid")
    bundle_dir = Path(str(case.get("base_bundle_dir") or ""))
    manifest_override = case.get("bundle_manifest_override")
    manifest_path = (
        _safe_bundle_path(case_root, manifest_override)
        if manifest_override
        else bundle_dir / "bundle.json"
    )
    bundle, root = _load_bundle(
        bundle_dir=bundle_dir,
        manifest_path=manifest_path,
        sealed_path=case_root / "SEALED",
    )
    raw_overrides = case.get("partition_overrides") or {}
    if type(raw_overrides) is not dict:
        raise VerificationRejected("failure_case_invalid")
    overrides: dict[str, dict[str, str]] = {}
    for partition_id, mapping in raw_overrides.items():
        if type(partition_id) is not str or type(mapping) is not dict:
            raise VerificationRejected("failure_case_invalid")
        converted: dict[str, str] = {}
        for key, relative in mapping.items():
            if key not in {"legacy_path", "payload_path", "manifest_path"}:
                raise VerificationRejected("failure_case_invalid")
            # Overrides live in the sealed case directory and were validated
            # there before they are handed to the persisted-byte verifier.
            override_path = _safe_bundle_path(case_root, relative)
            converted[key] = str(override_path)
        overrides[partition_id] = converted
    selection = _validate_selection(Path(selection_path))
    return _verify_bundle_value(
        bundle_dir=bundle_dir,
        bundle=bundle,
        bundle_root=root,
        selection=selection,
        overrides=overrides,
    )


def _write_receipt(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as handle:
        handle.write(_canonical_bytes(dict(value)) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--bundle-dir", type=Path, required=True)
    verify.add_argument("--selection", type=Path, required=True)
    verify.add_argument("--output", type=Path)
    case = subparsers.add_parser("verify-case")
    case.add_argument("--case-dir", type=Path, required=True)
    case.add_argument("--selection", type=Path, required=True)
    case.add_argument("--output", type=Path)
    return parser


def _main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "verify":
            result = verify_bundle(
                bundle_dir=args.bundle_dir,
                selection_path=args.selection,
            )
        else:
            result = verify_case(
                case_dir=args.case_dir,
                selection_path=args.selection,
            )
    except VerificationRejected as exc:
        result = {"schema": VERIFIER_SCHEMA, "status": "REJECTED", "code": exc.code}
        if args.output:
            _write_receipt(args.output, result)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 2
    if args.output:
        _write_receipt(args.output, result)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
