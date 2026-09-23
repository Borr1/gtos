"""Independent persisted-byte verifier for the real-replay typed source cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping


MANIFEST_SCHEMA = "gtos.replay_acceleration.integrated_typed_partition.v1"
CACHE_SCHEMA = "gtos.replay_acceleration.integrated_typed_source_cache.v1"
ROW_SCHEMA = "gtos.replay_acceleration.ohlcv_time_f64.v1"
MAGIC = b"GTOSNR01"
HEADER = struct.Struct("<8sQ")
ROW = struct.Struct("<qddddd")
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
MANIFEST_FIELDS = frozenset(
    {
        "schema",
        "identity",
        "identity_root_sha256",
        "payload_sha256",
        "payload_byte_count",
        "row_count",
        "rows_root_sha256",
        "manifest_root_sha256",
    }
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def root(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def manifest_root(value: Mapping[str, Any]) -> str:
    projection = dict(value)
    projection.pop("manifest_root_sha256", None)
    return root(projection)


def decoded_row(symbol: str, packed: tuple[Any, ...]) -> dict[str, Any]:
    micros, open_value, high, low, close, volume = packed
    timestamp = (EPOCH + timedelta(microseconds=int(micros))).isoformat()
    return {
        "time": timestamp,
        "time_utc": timestamp,
        "symbol": symbol,
        "open": float(open_value),
        "high": float(high),
        "low": float(low),
        "close": float(close),
        "volume": float(volume),
    }


def verify_cache(
    *,
    cache_root: Path,
    expected_source_bundle_root: str,
    expected_config_projection_root: str,
) -> dict[str, Any]:
    cache_root = Path(cache_root)
    entries = sorted(path for path in cache_root.iterdir() if path.is_dir())
    partition_roots: list[str] = []
    total_rows = 0
    total_bytes = 0
    for entry in entries:
        if len(entry.name) != 64 or any(c not in "009abcdef" for c in entry.name):
            raise ValueError("typed_cache_entry_name_invalid")
        manifest_raw = (entry / "manifest.json").read_bytes()
        manifest = json.loads(manifest_raw)
        if (
            type(manifest) is not dict
            or set(manifest) != MANIFEST_FIELDS
            or manifest.get("schema") != MANIFEST_SCHEMA
            or manifest_raw != canonical_bytes(manifest) + b"\n"
            or manifest.get("manifest_root_sha256") != manifest_root(manifest)
            or (entry / "SEALED").read_bytes()
            != str(manifest.get("manifest_root_sha256")).encode("ascii") + b"\n"
        ):
            raise ValueError("typed_manifest_invalid")
        identity = manifest.get("identity")
        if (
            type(identity) is not dict
            or identity.get("schema") != CACHE_SCHEMA
            or identity.get("typed_row_schema") != ROW_SCHEMA
            or identity.get("source_bundle_root_sha256")
            != expected_source_bundle_root
            or identity.get("config_projection_root_sha256")
            != expected_config_projection_root
            or manifest.get("identity_root_sha256") != root(identity)
            or entry.name != root(identity)
        ):
            raise ValueError("typed_cache_identity_invalid")
        payload = (entry / "rows.bin").read_bytes()
        if (
            len(payload) < HEADER.size
            or manifest.get("payload_byte_count") != len(payload)
            or manifest.get("payload_sha256") != hashlib.sha256(payload).hexdigest()
        ):
            raise ValueError("typed_payload_identity_mismatch")
        magic, count = HEADER.unpack_from(payload, 0)
        if (
            magic != MAGIC
            or count != manifest.get("row_count")
            or len(payload) != HEADER.size + count * ROW.size
        ):
            raise ValueError("typed_payload_framing_mismatch")
        digest = hashlib.sha256(
            b"gtos.replay_acceleration.canonical_rows.v1\n"
        )
        offset = HEADER.size
        for _index in range(count):
            row = decoded_row(str(identity["symbol"]), ROW.unpack_from(payload, offset))
            offset += ROW.size
            digest.update(canonical_bytes(row))
            digest.update(b"\n")
        if digest.hexdigest() != manifest.get("rows_root_sha256"):
            raise ValueError("typed_rows_root_mismatch")
        accepted_root = identity.get("accepted_normalized_root_sha256")
        accepted_count = identity.get("accepted_normalized_row_count")
        if accepted_root is not None and accepted_root != digest.hexdigest():
            raise ValueError("typed_accepted_normalized_root_mismatch")
        if accepted_count is not None and accepted_count != count:
            raise ValueError("typed_accepted_normalized_count_mismatch")
        partition_roots.append(entry.name)
        total_rows += count
        total_bytes += len(payload)
    report_core = {
        "schema": "gtos.replay_acceleration.integrated_typed_source_verification.v1",
        "valid": True,
        "partition_count": len(entries),
        "row_count": total_rows,
        "payload_byte_count": total_bytes,
        "source_bundle_root_sha256": expected_source_bundle_root,
        "config_projection_root_sha256": expected_config_projection_root,
        "partition_set_root_sha256": root(partition_roots),
        "writer_implementation_imported": False,
        "legacy_normalizer_imported": False,
    }
    return {**report_core, "verification_root_sha256": root(report_core)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--expected-source-bundle-root", required=True)
    parser.add_argument("--expected-config-projection-root", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify_cache(
        cache_root=args.cache_root,
        expected_source_bundle_root=args.expected_source_bundle_root,
        expected_config_projection_root=args.expected_config_projection_root,
    )
    material = canonical_bytes(report) + b"\n"
    if args.output is not None:
        temporary = args.output.with_name(args.output.name + ".tmp")
        temporary.write_bytes(material)
        temporary.replace(args.output)
    else:
        print(material.decode("ascii"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
