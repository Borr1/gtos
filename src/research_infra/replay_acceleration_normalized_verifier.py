"""Independent verifier for persisted normalized replay partitions.

This module is intentionally standard-library only.  It independently parses
persisted CSV source bytes, rebuilds legacy-normalized logical rows, and checks
the normalized cache without importing any writer or legacy normalizer code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import stat
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


SELECTION_SCHEMA = "gtos.replay_acceleration.slice_selection.v1"
SOURCE_BUNDLE_SCHEMA = "gtos.replay_acceleration.persisted_source_bundle.v1"
NORMALIZED_BUNDLE_SCHEMA = "gtos.replay_acceleration.normalized_bundle.v1"
NORMALIZED_MANIFEST_SCHEMA = "gtos.replay_acceleration.normalized_manifest.v1"
NORMALIZED_CASE_SCHEMA = "gtos.replay_acceleration.normalized_failure_case.v1"
VERIFIER_SCHEMA = "gtos.replay_acceleration.normalized_verification.v1"
NORMALIZED_ROW_SCHEMA = "gtos.replay_acceleration.normalized_rows_jsonl.v1"
EMPTY_CONFIG_ROOT = hashlib.sha256(b"{}").hexdigest()
LOGICAL_ORDER = {"D1": 0, "H4": 1, "H1": 2, "M15": 3, "M1": 4}
MANIFEST_FIELDS = {
    "schema",
    "identity",
    "identity_root_sha256",
    "payload_root_sha256",
    "payload_byte_count",
    "row_count",
    "normalized_rows_root_sha256",
    "manifest_root_sha256",
}


class NormalizedVerificationRejected(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise NormalizedVerificationRejected("normalized_payload_not_canonical") from None


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _valid_root(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(
        character in "009abcdef" for character in value
    )


def _load_canonical_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise NormalizedVerificationRejected(code) from None
    if type(value) is not dict or raw != _canonical_bytes(value) + b"\n":
        raise NormalizedVerificationRejected(code)
    return value


def _self_root(value: Mapping[str, Any], field: str, *, code: str) -> str:
    root = value.get(field)
    if not _valid_root(root):
        raise NormalizedVerificationRejected(code)
    core = {key: item for key, item in value.items() if key != field}
    if _sha256(_canonical_bytes(core)) != root:
        raise NormalizedVerificationRejected(code)
    return str(root)


def _safe_path(root: Path, relative: Any) -> Path:
    if type(relative) is not str or not relative:
        raise NormalizedVerificationRejected("normalized_path_invalid")
    base = root.resolve()
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise NormalizedVerificationRejected("normalized_path_invalid") from None
    return candidate


def _parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(text, pattern)
                break
            except ValueError:
                continue
        else:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_row_time(row: Mapping[str, Any]) -> datetime | None:
    for key in ("time_utc", "time", "timestamp", "datetime", "date"):
        if key in row and row.get(key) not in (None, ""):
            return _parse_utc(row.get(key))
    return None


def _compact_source_records(value: Any) -> tuple[float | str | None, dict[str, Any]]:
    if value in (None, ""):
        return None, {}
    if isinstance(value, (list, tuple, set)):
        material = json.dumps(list(value)[:5], sort_keys=True, default=str)
        return float(len(value)), {
            "source_records_compacted": True,
            "source_records_original_type": type(value).__name__,
            "source_records_original_count": len(value),
            "source_records_sample_hash_sha256": _sha256(material.encode()),
        }
    if isinstance(value, Mapping):
        keys = sorted(str(key) for key in value)
        return float(len(value)), {
            "source_records_compacted": True,
            "source_records_original_type": "mapping",
            "source_records_original_count": len(value),
            "source_records_sample_hash_sha256": _sha256(
                "\n".join(keys[:100]).encode()
            ),
            "source_records_key_sample": keys[:20],
        }
    try:
        return float(value), {}
    except (TypeError, ValueError):
        text = str(value)
    if len(text) > 128 or text[:1] in {"[", "{"}:
        return 0.0, {
            "source_records_compacted": True,
            "source_records_original_type": "text",
            "source_records_original_text_bytes": len(text.encode()),
            "source_records_original_hash_sha256": _sha256(text.encode()),
        }
    return text, {}


def _normalize_csv(payload: bytes, *, symbol: str) -> tuple[dict[str, Any], ...]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise NormalizedVerificationRejected("normalized_source_csv_invalid") from None
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        rows = list(reader)
    except csv.Error:
        raise NormalizedVerificationRejected("normalized_source_csv_invalid") from None
    output: list[dict[str, Any]] = []
    for row in rows:
        timestamp = _parse_row_time(row)
        if timestamp is None:
            continue
        normalized: dict[str, Any] = {
            "time": _iso(timestamp),
            "time_utc": _iso(timestamp),
            "symbol": symbol,
        }
        for key in ("open", "high", "low", "close", "volume"):
            try:
                normalized[key] = float(row.get(key, 0.0))
            except (TypeError, ValueError):
                normalized[key] = 0.0
            if not math.isfinite(normalized[key]):
                raise NormalizedVerificationRejected("normalized_numeric_nonfinite")
        for key in ("source_records", "num_trades", "bid_volume", "ask_volume"):
            if key not in row:
                continue
            if key == "source_records":
                compacted, metadata = _compact_source_records(row.get(key))
                if compacted is not None:
                    normalized[key] = compacted
                normalized.update(metadata)
                continue
            try:
                normalized[key] = float(row.get(key, 0.0))
            except (TypeError, ValueError):
                normalized[key] = row.get(key)
        output.append(normalized)
    return tuple(output)


def _aggregate_h1(
    rows: Iterable[Mapping[str, Any]], *, symbol: str
) -> tuple[dict[str, Any], ...]:
    buckets: dict[datetime, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        timestamp = _parse_row_time(row)
        if timestamp is None:
            continue
        bucket = timestamp.replace(minute=0, second=0, microsecond=0)
        buckets[bucket].append(row)
    output: list[dict[str, Any]] = []
    for bucket, items in sorted(buckets.items()):
        ordered = sorted(items, key=lambda item: _parse_row_time(item) or bucket)
        output.append(
            {
                "time": _iso(bucket),
                "time_utc": _iso(bucket),
                "symbol": symbol,
                "open": float(ordered[0].get("open") or 0.0),
                "high": max(float(row.get("high") or 0.0) for row in ordered),
                "low": min(float(row.get("low") or 0.0) for row in ordered),
                "close": float(ordered[-1].get("close") or 0.0),
                "volume": sum(float(row.get("volume") or 0.0) for row in ordered),
                "source_records": len(ordered),
            }
        )
    return tuple(output)


def _payload_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(_canonical_bytes(dict(row)) + b"\n" for row in rows)


def _rows_root(payload: bytes) -> str:
    return _sha256(b"gtos.replay_acceleration.normalized_rows.v1\n" + payload)


def _load_normalized_payload(path: Path) -> tuple[tuple[dict[str, Any], ...], bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        raise NormalizedVerificationRejected("normalized_payload_missing") from None
    if raw and not raw.endswith(b"\n"):
        raise NormalizedVerificationRejected("normalized_payload_not_canonical")
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines(keepends=True):
        if line == b"\n" or not line.endswith(b"\n"):
            raise NormalizedVerificationRejected("normalized_payload_not_canonical")
        try:
            value = json.loads(line)
        except (UnicodeError, json.JSONDecodeError):
            raise NormalizedVerificationRejected("normalized_payload_not_canonical") from None
        if type(value) is not dict or line != _canonical_bytes(value) + b"\n":
            raise NormalizedVerificationRejected("normalized_payload_not_canonical")
        rows.append(value)
    return tuple(rows), raw


def _load_sealed_bundle(
    *, bundle_dir: Path, manifest_path: Path | None = None, seal_path: Path | None = None
) -> tuple[dict[str, Any], str]:
    manifest = manifest_path or bundle_dir / "bundle.json"
    bundle = _load_canonical_json(manifest, code="normalized_bundle_invalid")
    if bundle.get("schema") != NORMALIZED_BUNDLE_SCHEMA:
        raise NormalizedVerificationRejected("normalized_bundle_invalid")
    root = _self_root(
        bundle, "normalized_bundle_root_sha256", code="normalized_bundle_invalid"
    )
    marker = seal_path or bundle_dir / "SEALED"
    try:
        raw = marker.read_bytes()
    except OSError:
        raise NormalizedVerificationRejected("normalized_bundle_unsealed") from None
    if raw != root.encode("ascii") + b"\n":
        raise NormalizedVerificationRejected("normalized_bundle_unsealed")
    return bundle, root


def _source_bundle(
    *, source_bundle_dir: Path, selection_path: Path
) -> tuple[dict[str, Any], dict[str, Any], str]:
    selection = _load_canonical_json(
        selection_path, code="normalized_selection_invalid"
    )
    if selection.get("schema") != SELECTION_SCHEMA:
        raise NormalizedVerificationRejected("normalized_selection_invalid")
    selection_root = _self_root(
        selection, "selection_root_sha256", code="normalized_selection_invalid"
    )
    source = _load_canonical_json(
        source_bundle_dir / "bundle.json", code="normalized_source_bundle_invalid"
    )
    if source.get("schema") != SOURCE_BUNDLE_SCHEMA:
        raise NormalizedVerificationRejected("normalized_source_bundle_invalid")
    source_root = _self_root(
        source, "bundle_root_sha256", code="normalized_source_bundle_invalid"
    )
    try:
        marker = (source_bundle_dir / "SEALED").read_bytes()
    except OSError:
        raise NormalizedVerificationRejected("normalized_source_bundle_unsealed") from None
    if marker != source_root.encode() + b"\n":
        raise NormalizedVerificationRejected("normalized_source_bundle_unsealed")
    if source.get("selection_root_sha256") != selection_root:
        raise NormalizedVerificationRejected("normalized_source_identity_mismatch")
    return selection, source, source_root


def _manifest(
    *, path: Path, entry: Mapping[str, Any], bundle: Mapping[str, Any]
) -> dict[str, Any]:
    manifest = _load_canonical_json(path, code="normalized_manifest_not_canonical")
    if set(manifest) != MANIFEST_FIELDS or manifest.get("schema") != NORMALIZED_MANIFEST_SCHEMA:
        raise NormalizedVerificationRejected("normalized_manifest_schema_mismatch")
    root = _self_root(
        manifest, "manifest_root_sha256", code="normalized_manifest_not_canonical"
    )
    identity = manifest.get("identity")
    if type(identity) is not dict:
        raise NormalizedVerificationRejected("normalized_manifest_schema_mismatch")
    if _sha256(_canonical_bytes(identity)) != manifest.get("identity_root_sha256"):
        raise NormalizedVerificationRejected("normalized_cache_identity_mismatch")
    checks = {
        "source_bundle_root_sha256": (
            bundle.get("source_bundle_root_sha256"),
            "normalized_source_identity_mismatch",
        ),
        "selection_root_sha256": (
            bundle.get("selection_root_sha256"),
            "normalized_source_identity_mismatch",
        ),
        "config_projection_root_sha256": (
            EMPTY_CONFIG_ROOT,
            "normalized_config_identity_mismatch",
        ),
        "normalized_row_schema": (
            NORMALIZED_ROW_SCHEMA,
            "normalized_manifest_schema_mismatch",
        ),
        "legacy_normalizer_file_sha256": (
            bundle.get("legacy_normalizer_file_sha256"),
            "normalized_code_identity_mismatch",
        ),
        "writer_file_sha256": (
            bundle.get("writer_file_sha256"),
            "normalized_code_identity_mismatch",
        ),
    }
    for field, (expected, code) in checks.items():
        if identity.get(field) != expected:
            raise NormalizedVerificationRejected(code)
    if identity != entry.get("identity"):
        for field in (
            "source_bundle_root_sha256",
            "selection_root_sha256",
            "source_payload_root_sha256",
            "source_logical_rows_root_sha256",
        ):
            if identity.get(field) != entry.get("identity", {}).get(field):
                raise NormalizedVerificationRejected("normalized_source_identity_mismatch")
        if identity.get("config_projection_root_sha256") != entry.get(
            "identity", {}
        ).get("config_projection_root_sha256"):
            raise NormalizedVerificationRejected("normalized_config_identity_mismatch")
        raise NormalizedVerificationRejected("normalized_code_identity_mismatch")
    if root != entry.get("manifest_root_sha256"):
        raise NormalizedVerificationRejected("normalized_manifest_identity_mismatch")
    return manifest


def _verify_value(
    *,
    bundle_dir: Path,
    bundle: Mapping[str, Any],
    bundle_root: str,
    source_bundle_dir: Path,
    source_bundle: Mapping[str, Any],
    source_root: str,
    selection: Mapping[str, Any],
    overrides: Mapping[str, Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    if bundle.get("source_bundle_root_sha256") != source_root:
        raise NormalizedVerificationRejected("normalized_source_identity_mismatch")
    if bundle.get("selection_root_sha256") != selection.get("selection_root_sha256"):
        raise NormalizedVerificationRejected("normalized_source_identity_mismatch")
    expected_cache_identity = _sha256(
        _canonical_bytes(
            {
                "source_bundle_root_sha256": source_root,
                "selection_root_sha256": selection.get("selection_root_sha256"),
                "legacy_normalizer_file_sha256": bundle.get(
                    "legacy_normalizer_file_sha256"
                ),
                "writer_file_sha256": bundle.get("writer_file_sha256"),
                "normalized_row_schema": NORMALIZED_ROW_SCHEMA,
                "config_projection_root_sha256": EMPTY_CONFIG_ROOT,
            }
        )
    )
    if bundle.get("cache_identity_root_sha256") != expected_cache_identity:
        raise NormalizedVerificationRejected("normalized_cache_identity_mismatch")

    entries = bundle.get("logical_partitions")
    if type(entries) is not list:
        raise NormalizedVerificationRejected("normalized_partition_schema_mismatch")
    expected_order = sorted(
        entries,
        key=lambda row: (
            str(row.get("symbol")),
            LOGICAL_ORDER.get(str(row.get("timeframe")), 99),
        ),
    )
    if entries != expected_order or [row.get("index") for row in entries] != list(
        range(len(entries))
    ):
        raise NormalizedVerificationRejected("normalized_partition_order_mismatch")

    physical_by_id = {
        str(row.get("partition_id")): row
        for row in source_bundle.get("physical_partitions") or ()
    }
    logical_by_key = {
        (str(row.get("symbol")), str(row.get("timeframe"))): row
        for row in source_bundle.get("logical_partitions") or ()
    }
    total_rows = 0
    symbols: set[str] = set()
    for entry in entries:
        partition_id = str(entry.get("partition_id") or "")
        override = (overrides or {}).get(partition_id, {})
        physical_id = str(entry.get("physical_partition_id") or "")
        physical = physical_by_id.get(physical_id)
        if physical is None:
            raise NormalizedVerificationRejected("normalized_source_identity_mismatch")
        source_legacy = _safe_path(source_bundle_dir, physical.get("legacy_path"))
        source_payload = _safe_path(source_bundle_dir, physical.get("payload_path"))
        try:
            legacy_bytes = source_legacy.read_bytes()
            source_bytes = source_payload.read_bytes()
        except OSError:
            raise NormalizedVerificationRejected("normalized_source_bytes_missing") from None
        if legacy_bytes != source_bytes or _sha256(source_bytes) != physical.get(
            "payload_root"
        ):
            raise NormalizedVerificationRejected("normalized_source_identity_mismatch")
        expected_rows = _normalize_csv(source_bytes, symbol=str(entry.get("symbol") or ""))
        if entry.get("transform") == "derived_h1_from_m15":
            expected_rows = _aggregate_h1(
                expected_rows, symbol=str(entry.get("symbol") or "")
            )
        elif entry.get("transform") != "direct_csv_normalization":
            raise NormalizedVerificationRejected("normalized_transform_invalid")

        payload_path = (
            Path(override["payload_path"])
            if override.get("payload_path")
            else _safe_path(bundle_dir, entry.get("payload_path"))
        )
        manifest_path = (
            Path(override["manifest_path"])
            if override.get("manifest_path")
            else _safe_path(bundle_dir, entry.get("manifest_path"))
        )
        actual_rows, raw = _load_normalized_payload(payload_path)
        if _sha256(raw) != entry.get("payload_root_sha256"):
            raise NormalizedVerificationRejected("normalized_payload_identity_mismatch")
        manifest = _manifest(path=manifest_path, entry=entry, bundle=bundle)
        if (
            manifest.get("payload_root_sha256") != _sha256(raw)
            or manifest.get("payload_byte_count") != len(raw)
            or manifest.get("row_count") != len(actual_rows)
            or manifest.get("normalized_rows_root_sha256") != _rows_root(raw)
        ):
            raise NormalizedVerificationRejected("normalized_payload_identity_mismatch")
        if actual_rows != expected_rows:
            actual_times = [str(row.get("time_utc") or row.get("time")) for row in actual_rows]
            if actual_times != sorted(actual_times):
                raise NormalizedVerificationRejected("normalized_row_order_mismatch")
            raise NormalizedVerificationRejected("legacy_normalized_rows_mismatch")
        source_logical = logical_by_key.get(
            (str(entry.get("symbol")), str(entry.get("timeframe")))
        )
        if source_logical is None or source_logical.get(
            "normalized_root_sha256"
        ) != entry.get("source_logical_rows_root_sha256"):
            raise NormalizedVerificationRejected("normalized_source_identity_mismatch")
        total_rows += len(actual_rows)
        symbols.add(str(entry.get("symbol")))

    barrier = bundle.get("cross_symbol_barrier")
    expected_barrier = {
        "sealed": True,
        "policy_execution_entered": False,
        "symbol_count": len(symbols),
        "symbols": sorted(symbols),
        "logical_partition_count": len(entries),
    }
    if barrier != expected_barrier:
        raise NormalizedVerificationRejected("normalized_cross_symbol_barrier_mismatch")
    return {
        "schema": VERIFIER_SCHEMA,
        "status": "VERIFIED",
        "normalized_bundle_root_sha256": bundle_root,
        "source_bundle_root_sha256": source_root,
        "selection_root_sha256": selection.get("selection_root_sha256"),
        "counts": {
            "symbols": len(symbols),
            "logical_partitions": len(entries),
            "normalized_rows": total_rows,
        },
        "writer_imported": False,
        "legacy_normalizer_imported": False,
        "policy_execution_entered": False,
    }


def verify_normalized_bundle(
    *, normalized_bundle_dir: Path, source_bundle_dir: Path, selection_path: Path
) -> dict[str, Any]:
    selection, source, source_root = _source_bundle(
        source_bundle_dir=Path(source_bundle_dir), selection_path=Path(selection_path)
    )
    bundle, bundle_root = _load_sealed_bundle(bundle_dir=Path(normalized_bundle_dir))
    return _verify_value(
        bundle_dir=Path(normalized_bundle_dir),
        bundle=bundle,
        bundle_root=bundle_root,
        source_bundle_dir=Path(source_bundle_dir),
        source_bundle=source,
        source_root=source_root,
        selection=selection,
    )


def verify_normalized_case(
    *, case_dir: Path, source_bundle_dir: Path, selection_path: Path
) -> dict[str, Any]:
    case_root = Path(case_dir)
    case = _load_canonical_json(
        case_root / "case.json", code="normalized_failure_case_invalid"
    )
    if case.get("schema") != NORMALIZED_CASE_SCHEMA:
        raise NormalizedVerificationRejected("normalized_failure_case_invalid")
    bundle_dir = Path(str(case.get("base_normalized_bundle_dir") or ""))
    manifest_override = case.get("bundle_manifest_override")
    bundle, bundle_root = _load_sealed_bundle(
        bundle_dir=bundle_dir,
        manifest_path=(
            _safe_path(case_root, manifest_override) if manifest_override else None
        ),
        seal_path=case_root / "SEALED",
    )
    raw_overrides = case.get("partition_overrides") or {}
    if type(raw_overrides) is not dict:
        raise NormalizedVerificationRejected("normalized_failure_case_invalid")
    overrides: dict[str, dict[str, str]] = {}
    for partition_id, values in raw_overrides.items():
        if type(partition_id) is not str or type(values) is not dict:
            raise NormalizedVerificationRejected("normalized_failure_case_invalid")
        converted: dict[str, str] = {}
        for key, relative in values.items():
            if key not in {"payload_path", "manifest_path"}:
                raise NormalizedVerificationRejected("normalized_failure_case_invalid")
            converted[key] = str(_safe_path(case_root, relative))
        overrides[partition_id] = converted
    selection, source, source_root = _source_bundle(
        source_bundle_dir=Path(source_bundle_dir), selection_path=Path(selection_path)
    )
    return _verify_value(
        bundle_dir=bundle_dir,
        bundle=bundle,
        bundle_root=bundle_root,
        source_bundle_dir=Path(source_bundle_dir),
        source_bundle=source,
        source_root=source_root,
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
    verify.add_argument("--normalized-bundle-dir", type=Path, required=True)
    verify.add_argument("--source-bundle-dir", type=Path, required=True)
    verify.add_argument("--selection", type=Path, required=True)
    verify.add_argument("--output", type=Path)
    case = subparsers.add_parser("verify-case")
    case.add_argument("--case-dir", type=Path, required=True)
    case.add_argument("--source-bundle-dir", type=Path, required=True)
    case.add_argument("--selection", type=Path, required=True)
    case.add_argument("--output", type=Path)
    return parser


def _main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "verify":
            result = verify_normalized_bundle(
                normalized_bundle_dir=args.normalized_bundle_dir,
                source_bundle_dir=args.source_bundle_dir,
                selection_path=args.selection,
            )
        else:
            result = verify_normalized_case(
                case_dir=args.case_dir,
                source_bundle_dir=args.source_bundle_dir,
                selection_path=args.selection,
            )
    except NormalizedVerificationRejected as exc:
        result = {"status": "REJECTED", "code": exc.code}
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 2
    if args.output:
        _write_receipt(args.output, result)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
