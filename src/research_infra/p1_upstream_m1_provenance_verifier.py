"""One-shot M1 provenance and partial-session gap proof for the P1 packet."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import stat
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from src.research_infra._p1_upstream_packet_expectations import _PRODUCTION_EXPECTATIONS


RESULT_USE_STATUS = "SOURCE_CONTROL_ONLY_NO_OUTCOME_READ"
EXPECTED_M1_ROWS = 2_188_895
EXPECTED_M15_BUCKETS = 147_690
BAR_KEYS = {"time", "time_utc", "symbol", "open", "high", "low", "close", "volume"}


class M1ProvenanceError(RuntimeError):
    """A bound M1 source or deterministic aggregation failed closed."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_json(payload: str | bytes, *, label: str) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        row: dict[str, Any] = {}
        for key, value in values:
            if key in row:
                raise M1ProvenanceError(f"duplicate_json_key:{label}:{key}")
            row[key] = value
        return row

    def constant(value: str) -> Any:
        raise M1ProvenanceError(f"nonfinite_json_constant:{label}:{value}")

    try:
        return json.loads(payload, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise M1ProvenanceError(f"invalid_json:{label}") from exc


def _utc(value: Any, *, label: str) -> datetime:
    text = str(value or "")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise M1ProvenanceError(f"invalid_timestamp:{label}:{value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise M1ProvenanceError(f"non_utc_timestamp:{label}:{value}")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _relative(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "//" in value:
        raise M1ProvenanceError(f"path_not_normalized:{label}:{value}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise M1ProvenanceError(f"path_not_relative_contained:{label}:{value}")
    return value


def _file(root: Path, relative: str, *, digest: str | None = None, size: int | None = None) -> Path:
    _relative(relative, label="bound_file")
    candidate = root
    for part in PurePosixPath(relative).parts:
        candidate = candidate / part
        mode = candidate.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise M1ProvenanceError(f"symlink_refused:{candidate}")
    if not stat.S_ISREG(candidate.lstat().st_mode):
        raise M1ProvenanceError(f"nonregular_refused:{candidate}")
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise M1ProvenanceError(f"path_outside_root:{candidate}") from exc
    if size is not None and candidate.stat().st_size != size:
        raise M1ProvenanceError(f"size_mismatch:{candidate}")
    if digest is not None and _sha256(candidate) != digest:
        raise M1ProvenanceError(f"sha256_mismatch:{candidate}")
    return candidate


def _number(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise M1ProvenanceError(f"numeric_type_invalid:{label}")
    result = float(value)
    if not math.isfinite(result):
        raise M1ProvenanceError(f"numeric_nonfinite:{label}")
    return result


def _validate_bar(row: Mapping[str, Any], *, symbol: str, minute_grid: int, label: str) -> datetime:
    if set(row) != BAR_KEYS or row.get("symbol") != symbol or row.get("time") != row.get("time_utc"):
        raise M1ProvenanceError(f"bar_schema_or_identity_invalid:{label}")
    timestamp = _utc(row["time_utc"], label=label)
    if timestamp.second or timestamp.microsecond or timestamp.minute % minute_grid:
        raise M1ProvenanceError(f"bar_grid_invalid:{label}")
    open_, high, low, close, volume = (_number(row[key], label=f"{label}:{key}") for key in ("open", "high", "low", "close", "volume"))
    if high < max(open_, close) or low > min(open_, close) or high < low or volume < 0:
        raise M1ProvenanceError(f"bar_geometry_invalid:{label}")
    return timestamp


def aggregate_m1_rows(rows: Sequence[Mapping[str, Any]], *, symbol: str) -> dict[datetime, dict[str, Any]]:
    """Aggregate strictly ordered, potentially sparse M1 bars without filling absent minutes."""

    buckets: dict[datetime, list[Mapping[str, Any]]] = defaultdict(list)
    previous: datetime | None = None
    for number, row in enumerate(rows, 1):
        timestamp = _validate_bar(row, symbol=symbol, minute_grid=1, label=f"m1:{symbol}:{number}")
        if previous is not None:
            if timestamp <= previous:
                raise M1ProvenanceError(f"m1_time_order_invalid:{symbol}:{number}")
        previous = timestamp
        buckets[timestamp.replace(minute=(timestamp.minute // 15) * 15)].append(row)
    if not buckets:
        raise M1ProvenanceError(f"m1_empty:{symbol}")
    output: dict[datetime, dict[str, Any]] = {}
    for bucket, members in sorted(buckets.items()):
        output[bucket] = {
            "time": _iso(bucket), "time_utc": _iso(bucket), "symbol": symbol,
            "open": float(members[0]["open"]), "high": max(float(row["high"]) for row in members),
            "low": min(float(row["low"]) for row in members), "close": float(members[-1]["close"]),
            "volume": sum(float(row["volume"]) for row in members),
        }
    return output


def verify_m1_m15_equivalence(
    derived_m15: Mapping[datetime, Mapping[str, Any]],
    bound_m15: Mapping[datetime, Mapping[str, Any]],
    *,
    source_label: str,
) -> None:
    """Require sparse M1 aggregation to equal independently bound M15 bars exactly."""

    if set(bound_m15) != set(derived_m15):
        raise M1ProvenanceError(f"m1_m15_bucket_domain_mismatch:{source_label}")
    for bucket, expected in derived_m15.items():
        if _canonical(bound_m15[bucket]) != _canonical(expected):
            raise M1ProvenanceError(f"m1_m15_ohlcv_mismatch:{source_label}:{_iso(bucket)}")


def _jsonl_gzip(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            row = _strict_json(line, label=f"{path}:{number}")
            if not isinstance(row, dict):
                raise M1ProvenanceError(f"row_not_object:{path}:{number}")
            rows.append(row)
    return rows


def _packet_payload(packet: Path, manifest: Mapping[str, Any], expected_root: str) -> dict[str, Mapping[str, Any]]:
    values = manifest.get("payload_files")
    if not isinstance(values, list):
        raise M1ProvenanceError("payload_descriptor_list_invalid")
    bindings: dict[str, Mapping[str, Any]] = {}
    observed: list[dict[str, Any]] = []
    for number, row in enumerate(values):
        if not isinstance(row, Mapping) or set(row) != {"path", "bytes", "sha256"}:
            raise M1ProvenanceError(f"payload_descriptor_invalid:{number}")
        relative = _relative(row["path"], label=f"payload:{number}")
        if relative in bindings:
            raise M1ProvenanceError(f"duplicate_payload_descriptor:{relative}")
        target = _file(packet, relative, digest=row["sha256"], size=row["bytes"])
        bindings[relative] = row
        observed.append({"path": relative, "bytes": target.stat().st_size, "sha256": _sha256(target)})
    root = hashlib.sha256(_canonical({"schema": "gtos.p1-upstream-packet-payload.v1", "files": sorted(observed, key=lambda row: row["path"])})).hexdigest()
    if root != expected_root or manifest.get("packet_payload_root_sha256") != expected_root:
        raise M1ProvenanceError("packet_payload_root_mismatch")
    return bindings


def _csv_m1(path: Path, *, symbol: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != ("time", "open", "high", "low", "close", "volume"):
            raise M1ProvenanceError(f"m1_csv_schema_invalid:{symbol}")
        for number, raw in enumerate(reader, 2):
            try:
                timestamp = _utc(raw["time"], label=f"m1_csv:{symbol}:{number}")
                row = {
                    "time": _iso(timestamp), "time_utc": _iso(timestamp), "symbol": symbol,
                    "open": float(raw["open"]), "high": float(raw["high"]),
                    "low": float(raw["low"]), "close": float(raw["close"]),
                    "volume": float(raw["volume"]),
                }
            except (TypeError, ValueError) as exc:
                raise M1ProvenanceError(f"m1_csv_numeric_invalid:{symbol}:{number}") from exc
            rows.append(row)
    return rows


def verify_m1_provenance(
    packet: Path,
    *,
    expected_manifest_sha256: str,
    expected_payload_root_sha256: str,
    expected_tested_source_commit: str,
) -> dict[str, Any]:
    expectations = _PRODUCTION_EXPECTATIONS
    manifest_path = _file(packet, "PACKET_MANIFEST.json", digest=expected_manifest_sha256)
    manifest = _strict_json(manifest_path.read_bytes(), label="packet_manifest")
    if (
        not isinstance(manifest, Mapping) or manifest.get("schema") != "gtos.p1-upstream-source-packet.v2"
        or manifest.get("tested_source_commit") != expected_tested_source_commit
    ):
        raise M1ProvenanceError("packet_manifest_identity_invalid")
    payload = _packet_payload(packet, manifest, expected_payload_root_sha256)
    packet_m15: dict[str, list[dict[str, Any]]] = {}
    packet_h1: dict[str, list[dict[str, Any]]] = {}
    partial_h1: set[tuple[str, datetime]] = set()
    for symbol in expectations.symbols:
        for timeframe, target in (("m15", packet_m15), ("h1", packet_h1)):
            relative = f"series/{symbol}.{timeframe}.jsonl.gz"
            if relative not in payload:
                raise M1ProvenanceError(f"packet_series_binding_missing:{relative}")
            target[symbol] = _jsonl_gzip(_file(packet, relative))
        counts = Counter(_utc(row["time_utc"], label=f"packet_m15:{symbol}").replace(minute=0) for row in packet_m15[symbol])
        partial_h1.update((symbol, hour) for hour, count in counts.items() if count != 4)

    total_rows = 0
    total_buckets = 0
    m1_hour_keys: set[tuple[str, datetime]] = set()
    manifest_hashes = dict(expectations.source_manifests)
    for relative in ("manifests/january_2026.json", "manifests/april_2026.json", "manifests/may_2026.json"):
        source_manifest = _strict_json(
            _file(expectations.source_root, relative, digest=manifest_hashes[relative]).read_bytes(),
            label=f"source_manifest:{relative}",
        )
        entries: dict[str, Mapping[str, Any]] = {}
        for entry in source_manifest.get("bar_sources") or []:
            if not isinstance(entry, Mapping) or entry.get("timeframe") != "M1":
                continue
            symbol = entry.get("symbol")
            if symbol not in expectations.symbols or symbol in entries:
                raise M1ProvenanceError(f"m1_source_symbol_invalid:{relative}:{symbol}")
            if entry.get("mapped_symbol") != symbol or entry.get("time_column_basis") != "true_utc" or entry.get("broker_clock_rule") != "new_york_plus_7" or entry.get("clock_conversion") != "broker_epoch_to_utc":
                raise M1ProvenanceError(f"m1_source_authority_invalid:{relative}:{symbol}")
            entries[str(symbol)] = entry
        if set(entries) != set(expectations.symbols):
            raise M1ProvenanceError(f"m1_source_domain_invalid:{relative}")
        for symbol in expectations.symbols:
            entry = entries[symbol]
            source_path = _file(expectations.source_root, _relative(entry["lane_relpath"], label=f"m1:{relative}:{symbol}"), digest=entry["sha256"])
            rows = _csv_m1(source_path, symbol=symbol)
            if isinstance(entry.get("row_count"), bool) or len(rows) != entry.get("row_count"):
                raise M1ProvenanceError(f"m1_source_row_count_mismatch:{relative}:{symbol}")
            if rows[0]["time_utc"] != entry.get("first_utc") or rows[-1]["time_utc"] != entry.get("last_utc"):
                raise M1ProvenanceError(f"m1_source_coverage_mismatch:{relative}:{symbol}")
            derived = aggregate_m1_rows(rows, symbol=symbol)
            packet_rows = {
                _utc(row["time_utc"], label=f"packet_m15:{symbol}"): row
                for row in packet_m15[symbol]
                if min(derived) <= _utc(row["time_utc"], label=f"packet_m15:{symbol}") <= max(derived)
            }
            verify_m1_m15_equivalence(derived, packet_rows, source_label=f"{relative}:{symbol}")
            total_rows += len(rows)
            total_buckets += len(derived)
            m1_hour_keys.update((symbol, bucket.replace(minute=0)) for bucket in derived)
    if total_rows != EXPECTED_M1_ROWS or total_buckets != EXPECTED_M15_BUCKETS:
        raise M1ProvenanceError(f"m1_denominator_mismatch:{total_rows}:{total_buckets}")

    referenced_partial: set[tuple[str, datetime]] = set()
    states = _jsonl_gzip(_file(packet, "states/predecision_market_state.jsonl.gz"))
    for state in states:
        symbol = state.get("symbol")
        bounds = state.get("h1_slice") or {}
        start, stop = bounds.get("h1_start"), bounds.get("h1_stop")
        if symbol not in packet_h1 or isinstance(start, bool) or isinstance(stop, bool) or not isinstance(start, int) or not isinstance(stop, int):
            raise M1ProvenanceError("state_h1_slice_invalid")
        referenced_partial.update(
            key for row in packet_h1[symbol][start:stop]
            if (key := (symbol, _utc(row["time_utc"], label=f"state_h1:{symbol}"))) in partial_h1
        )
    m1_proven = referenced_partial & m1_hour_keys
    source_only = referenced_partial - m1_proven
    if (
        len(partial_h1) != expectations.partial_h1_buckets
        or len(referenced_partial) != expectations.referenced_partial_h1_buckets
        or len(m1_proven) != 37 or len(source_only) != 9
        or any(hour.year != 2025 or hour.month != 12 for _, hour in source_only)
    ):
        raise M1ProvenanceError(
            f"partial_h1_gap_classification_mismatch:{len(partial_h1)}:{len(referenced_partial)}:{len(m1_proven)}:{len(source_only)}"
        )
    return {
        "schema": "gtos.p1-upstream-m1-provenance.v1",
        "status": "PASS", "packet_manifest_sha256": expected_manifest_sha256,
        "packet_payload_root_sha256": expected_payload_root_sha256,
        "tested_source_commit": expected_tested_source_commit,
        "m1_rows": total_rows, "m1_m15_buckets": total_buckets,
        "partial_h1_buckets": len(partial_h1),
        "referenced_partial_h1_buckets": len(referenced_partial),
        "m1_proven_referenced_partial_h1_buckets": len(m1_proven),
        "source_preserved_december_partial_h1_buckets": len(source_only),
        "execution_authority": False, "activation_authority": False,
        "result_bearing_science_executed": False, "broker_orders": 0,
        "result_use_status": RESULT_USE_STATUS,
    }


def _args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--expected-payload-root-sha256", required=True)
    parser.add_argument("--expected-tested-source-commit", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _args(argv)
    print(json.dumps(verify_m1_provenance(
        args.packet, expected_manifest_sha256=args.expected_manifest_sha256,
        expected_payload_root_sha256=args.expected_payload_root_sha256,
        expected_tested_source_commit=args.expected_tested_source_commit,
    ), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
