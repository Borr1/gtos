"""Independent verifier for the Wave 20 P1 upstream source packet.

The verifier intentionally reimplements packet hashing, time parsing, closed
bar slicing, H1 aggregation, identity projection, and generator conformance.
It imports only the bound pure market-state and candidate-generator modules.
"""

from __future__ import annotations

import argparse
import ast
import bisect
import copy
import csv
import gzip
import hashlib
import io
import json
import math
import os
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import yaml

from src.research_infra._p1_upstream_packet_expectations import (
    _PRODUCTION_EXPECTATIONS,
    _PacketExpectations,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TOTAL = _PRODUCTION_EXPECTATIONS.total
EXPECTED_WINDOWS = dict(_PRODUCTION_EXPECTATIONS.window_counts)
WINDOWS = dict(_PRODUCTION_EXPECTATIONS.windows)
RESULT_USE_STATUS = "SOURCE_CONTROL_ONLY_NO_OUTCOME_READ"
EXPECTED_HN_TESTED_SOURCE_COMMIT = _PRODUCTION_EXPECTATIONS.source_parent
EXPECTED_REUSED_CANDIDATE_IDS = _PRODUCTION_EXPECTATIONS.reused_candidate_ids
EXPECTED_ROWS_UNDER_REUSED_CANDIDATE_IDS = _PRODUCTION_EXPECTATIONS.rows_under_reused_candidate_ids
FIXED_BREAKER_MEMBER_CANONICAL_SHA256 = "0de66ebe5b67e7b3352d98624acb50c69ab116b1c46d58c422b887e5583a650f"
EXPECTED_SOURCE_ROOT = _PRODUCTION_EXPECTATIONS.source_root
EXPECTED_SYMBOLS = _PRODUCTION_EXPECTATIONS.symbols
POOL_BINDINGS = (
    ("january", "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz", "ee920fb0e28713f28cf85322d6b6494beef07c27235db9e6ba59dd6e5097fc8f", 5_696_917),
    ("april", "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz", "d587e99ebdbc0f56b3501719e05dfec45902e9013ee8c32392e344bc51c9e4d9", 5_504_482),
    ("may", "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz", "1bba6662644d0424ff5a360f987ddd81bb1b0f176b7547b6626853d166cb5633", 4_600_824),
)
ALLOWED_POOL_FIELDS = {
    "candidate_id", "symbol", "side", "direction", "decision_time_utc",
    "kill_zone", "origin_family", "framework", "route_family",
}
GENERATOR_SHA256 = _PRODUCTION_EXPECTATIONS.generator_sha256
MARKET_STATE_SHA256 = _PRODUCTION_EXPECTATIONS.market_state_sha256
BASE_CONFIG_SHA256 = "175f6b3bc1a692a5c5add776845281ee92fad71e11074e0a3f38d72a619eff7d"
FTMO_PROFILE_SHA256 = "ae9312e6c5c8e6b05f8e5eb5f9490166c44a1a3279b4eff5df10c3da2921e2b8"

EXPECTED_REPO_AUTHORITIES = {
    path: (sha256, size)
    for path, sha256, size in _PRODUCTION_EXPECTATIONS.repo_authorities
}
EXPECTED_SOURCE_MANIFEST_SHA256 = dict(_PRODUCTION_EXPECTATIONS.source_manifests)
B0_BREAKER_ROUTE_BINDING = {
    "commit": "11594419a197e278263565ac7677ecfc3e317c31",
    "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/B0_BREAKER_ROUTE.json",
    "bytes": 3_482,
    "sha256": "4befaece894d3c8f05f6d8ab1d3abb4a25e0646cac9a2ea491614b9a1adeaeef",
    "json_pointer": "/candidate/family_member_record",
    "canonicalization": "json_sort_keys_compact_utf8_no_trailing_newline",
}
EXPECTED_EVIDENCE_LINEAGE = {
    label: (commit, parent)
    for label, commit, parent, _ in _PRODUCTION_EXPECTATIONS.evidence_lineage
}
EXPECTED_EVIDENCE_ARTIFACTS = dict(_PRODUCTION_EXPECTATIONS.evidence_artifacts)
SERIES_DESCRIPTOR_KEYS = {
    "path", "bytes", "sha256", "row_count", "first_utc", "last_utc",
    "time_column_basis", "timeframe_minutes",
}
MANIFEST_KEYS = {
    "activation_authority", "asof_contract",
    "commissioned_source_payload_count", "coverage", "execution_authority",
    "external_packet_immutable", "generator", "immutable_evidence_authorities",
    "packet_directory_name", "packet_payload_root_sha256",
    "packet_tooling", "payload_files", "repo_authorities",
    "result_bearing_science_executed", "result_use_status", "route_identity",
    "schema", "series", "source_manifests", "source_root",
    "status", "tested_source_commit", "timebase_authority",
}
SERIES_ROW_KEYS = {"time", "time_utc", "symbol", "open", "high", "low", "close", "volume"}
STATE_KEYS = {
    "state_id", "symbol", "decision_time_utc", "m15_slice", "h1_slice",
    "m15_atr_14", "h1_breaker_blocks", "h1_breaker_blocks_sha256",
    "uses_outcome_fields", "state_sha256",
}
M15_SLICE_KEYS = {"m15_start", "m15_stop", "m15_count", "first_open_utc", "last_open_utc", "last_close_utc"}
H1_SLICE_KEYS = {"h1_start", "h1_stop", "h1_count", "first_open_utc", "last_open_utc", "last_close_utc"}
BREAKER_KEYS = {
    "zone_high", "zone_low", "direction", "original_ob_direction",
    "formation_time", "mitigation_time", "causing_event", "is_retested",
}
IDENTITY_ROW_KEYS = {
    "identity", "window", "state_id", "symbol", "decision_time_utc", "kill_zone",
    "origin_family", "framework", "route_family", "m15_series_path",
    "h1_series_path", "m15_slice", "h1_slice", "generator_match_count",
    "uses_outcome_fields", "identity_slice_sha256",
}
IDENTITY_KEYS = {"candidate_id", "symbol", "side", "decision_time_utc"}


class VerificationError(RuntimeError):
    """Packet or independent-reconstruction mismatch."""


def strict_json_loads(payload: str | bytes, *, label: str) -> Any:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in pairs:
            if key in output:
                raise VerificationError(f"duplicate_json_key:{label}:{key}")
            output[key] = value
        return output

    def reject_constant(value: str) -> Any:
        raise VerificationError(f"nonfinite_json_constant:{label}:{value}")

    try:
        return json.loads(payload, object_pairs_hook=pairs_hook, parse_constant=reject_constant)
    except UnicodeDecodeError as exc:
        raise VerificationError(f"invalid_json_utf8:{label}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(f"invalid_json:{label}:{exc.lineno}:{exc.colno}") from exc


def _exact_keys(value: Any, expected: set[str], *, label: str, reason: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        observed = sorted(value) if isinstance(value, Mapping) else type(value).__name__
        raise VerificationError(f"{reason}:{label}:{observed}")
    return value


def _strict_int(value: Any, *, label: str, reason: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise VerificationError(f"{reason}:{label}")
    return value


def _strict_number(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise VerificationError(f"series_numeric_type_invalid:{label}")
    number = float(value)
    if not math.isfinite(number):
        raise VerificationError(f"series_numeric_nonfinite:{label}")
    return number


def _strict_text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise VerificationError(f"text_type_invalid:{label}")
    return value


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def normalized_relative_path(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "//" in value:
        raise VerificationError(f"payload_path_not_normalized:{label}:{value}")
    pure = PurePosixPath(value)
    if pure.is_absolute():
        raise VerificationError(f"absolute_payload_path:{label}:{value}")
    if any(part in {"", ".", ".."} for part in pure.parts):
        if ".." in pure.parts:
            raise VerificationError(f"payload_path_traversal:{label}:{value}")
        raise VerificationError(f"payload_path_not_normalized:{label}:{value}")
    if pure.as_posix() != value:
        raise VerificationError(f"payload_path_not_normalized:{label}:{value}")
    return value


def packet_inventory(root: Path) -> tuple[set[str], set[str]]:
    if root.is_symlink():
        raise VerificationError(f"packet_symlink_refused:{root}")
    if not root.is_dir():
        raise VerificationError(f"packet_root_not_directory:{root}")
    files: set[str] = set()
    directories: set[str] = {"."}
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in list(dirnames):
            path = current_path / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise VerificationError(f"packet_symlink_refused:{path}")
            if not stat.S_ISDIR(mode):
                raise VerificationError(f"packet_nonregular_refused:{path}")
            directories.add(path.relative_to(root).as_posix())
        for name in filenames:
            path = current_path / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise VerificationError(f"packet_symlink_refused:{path}")
            if not stat.S_ISREG(mode):
                raise VerificationError(f"packet_nonregular_refused:{path}")
            files.add(path.relative_to(root).as_posix())
    return files, directories


def require_exact_packet_inventory(observed: set[str], expected: set[str]) -> None:
    if observed != expected:
        raise VerificationError(
            f"packet_file_inventory_mismatch:missing={sorted(expected-observed)}:extra={sorted(observed-expected)}"
        )


def contained_regular_file(root: Path, relative: str, *, label: str) -> Path:
    normalized_relative_path(relative, label=label)
    candidate = root
    for part in PurePosixPath(relative).parts:
        candidate = candidate / part
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError as exc:
            raise VerificationError(f"missing_file:{candidate}") from exc
        if stat.S_ISLNK(mode):
            raise VerificationError(f"packet_symlink_refused:{candidate}")
    if not stat.S_ISREG(candidate.lstat().st_mode):
        raise VerificationError(f"packet_nonregular_refused:{candidate}")
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    except ValueError as exc:
        raise VerificationError(f"packet_outside_root:{candidate}") from exc
    return candidate


def validate_file_descriptor(value: Any, *, label: str) -> dict[str, Any]:
    row = dict(_exact_keys(value, {"path", "bytes", "sha256"}, label=label, reason="descriptor_schema_invalid"))
    row["path"] = normalized_relative_path(row["path"], label=label)
    if _strict_int(row["bytes"], label=label, reason="descriptor_bytes_type_invalid") < 0:
        raise VerificationError(f"descriptor_bytes_negative:{label}")
    if not _is_sha256(row["sha256"]):
        raise VerificationError(f"descriptor_sha256_invalid:{label}")
    return row


def validate_series_row(
    value: Any, *, symbol: str, minutes: int, label: str
) -> datetime:
    row = _exact_keys(value, SERIES_ROW_KEYS, label=label, reason="series_schema_invalid")
    _strict_text(row["time"], label=f"{label}:time")
    _strict_text(row["time_utc"], label=f"{label}:time_utc")
    if row["time"] != row["time_utc"]:
        raise VerificationError(f"series_time_duplicate_mismatch:{label}")
    if row["symbol"] != symbol:
        raise VerificationError(f"series_symbol_mismatch:{symbol}:{label}")
    timestamp = utc(row["time_utc"], label)
    if timestamp.second != 0 or timestamp.microsecond != 0 or timestamp.minute % minutes:
        raise VerificationError(f"series_grid_invalid:{label}")
    open_, high, low, close, volume = (
        _strict_number(row[field], label=f"{label}:{field}")
        for field in ("open", "high", "low", "close", "volume")
    )
    if high < max(open_, close) or low > min(open_, close) or high < low:
        raise VerificationError(f"series_ohlc_geometry_invalid:{label}")
    if volume < 0:
        raise VerificationError(f"series_volume_negative:{label}")
    return timestamp


def validate_state_schema(value: Any, *, label: str) -> Mapping[str, Any]:
    row = _exact_keys(value, STATE_KEYS, label=label, reason="state_schema_invalid")
    for key in ("state_id", "symbol", "decision_time_utc", "h1_breaker_blocks_sha256", "state_sha256"):
        _strict_text(row[key], label=f"{label}:{key}")
    if row["uses_outcome_fields"] is not False:
        raise VerificationError(f"state_outcome_flag_invalid:{label}")
    for prefix, keys in (("m15", M15_SLICE_KEYS), ("h1", H1_SLICE_KEYS)):
        slice_row = _exact_keys(row[f"{prefix}_slice"], keys, label=f"{label}:{prefix}_slice", reason="state_slice_schema_invalid")
        start = _strict_int(slice_row[f"{prefix}_start"], label=f"{label}:{prefix}:start", reason="state_slice_type_invalid")
        stop = _strict_int(slice_row[f"{prefix}_stop"], label=f"{label}:{prefix}:stop", reason="state_slice_type_invalid")
        count = _strict_int(slice_row[f"{prefix}_count"], label=f"{label}:{prefix}:count", reason="state_slice_type_invalid")
        if start < 0 or stop <= start or count != stop - start:
            raise VerificationError(f"state_slice_bounds_invalid:{label}:{prefix}")
        timestamps = [
            utc(slice_row[key], f"{label}:{prefix}:{key}")
            for key in ("first_open_utc", "last_open_utc", "last_close_utc")
        ]
        if any(iso(timestamp) != slice_row[key] for timestamp, key in zip(timestamps, ("first_open_utc", "last_open_utc", "last_close_utc"))):
            raise VerificationError(f"state_slice_timestamp_not_canonical:{label}:{prefix}")
    if isinstance(row["m15_atr_14"], bool) or not isinstance(row["m15_atr_14"], (int, float)) or not math.isfinite(float(row["m15_atr_14"])):
        raise VerificationError(f"state_atr_type_invalid:{label}")
    if not isinstance(row["h1_breaker_blocks"], list):
        raise VerificationError(f"state_breakers_type_invalid:{label}")
    for number, breaker in enumerate(row["h1_breaker_blocks"]):
        block = _exact_keys(breaker, BREAKER_KEYS, label=f"{label}:breaker:{number}", reason="breaker_schema_invalid")
        high = _strict_number(block["zone_high"], label=f"{label}:breaker:{number}:zone_high")
        low = _strict_number(block["zone_low"], label=f"{label}:breaker:{number}:zone_low")
        if high < low:
            raise VerificationError(f"breaker_geometry_invalid:{label}:{number}")
        for key in ("direction", "original_ob_direction", "formation_time", "mitigation_time", "causing_event"):
            _strict_text(block[key], label=f"{label}:breaker:{number}:{key}")
        if block["direction"] not in {"bullish", "bearish"} or block["original_ob_direction"] not in {"bullish", "bearish"}:
            raise VerificationError(f"breaker_direction_invalid:{label}:{number}")
        for key in ("formation_time", "mitigation_time"):
            timestamp = utc(block[key], f"{label}:breaker:{number}:{key}")
            if iso(timestamp) != block[key]:
                raise VerificationError(f"breaker_timestamp_not_canonical:{label}:{number}:{key}")
        if not isinstance(block["is_retested"], bool):
            raise VerificationError(f"breaker_retested_type_invalid:{label}:{number}")
    return row


def validate_identity_schema(value: Any, *, label: str) -> Mapping[str, Any]:
    row = _exact_keys(value, IDENTITY_ROW_KEYS, label=label, reason="identity_schema_invalid")
    identity = _exact_keys(row["identity"], IDENTITY_KEYS, label=f"{label}:identity", reason="identity_key_schema_invalid")
    for key in IDENTITY_KEYS:
        _strict_text(identity[key], label=f"{label}:identity:{key}")
    for key in ("window", "state_id", "symbol", "decision_time_utc", "kill_zone", "origin_family", "framework", "route_family", "m15_series_path", "h1_series_path", "identity_slice_sha256"):
        _strict_text(row[key], label=f"{label}:{key}")
    if isinstance(row["generator_match_count"], bool) or not isinstance(row["generator_match_count"], int):
        raise VerificationError(f"generator_multiplicity_type_invalid:{label}")
    if row["generator_match_count"] != 1:
        raise VerificationError(f"generator_multiplicity_invalid:{label}")
    if row["uses_outcome_fields"] is not False:
        raise VerificationError(f"identity_outcome_flag_invalid:{label}")
    for key in ("m15_slice", "h1_slice"):
        bounds = row[key]
        if (
            not isinstance(bounds, list) or len(bounds) != 2
            or any(isinstance(item, bool) or not isinstance(item, int) for item in bounds)
        ):
            raise VerificationError(f"identity_slice_type_invalid:{label}:{key}")
        if bounds[0] < 0 or bounds[1] <= bounds[0]:
            raise VerificationError(f"identity_slice_bounds_invalid:{label}:{key}")
    normalized_relative_path(row["m15_series_path"], label=f"{label}:m15_series_path")
    normalized_relative_path(row["h1_series_path"], label=f"{label}:h1_series_path")
    return row


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path, digest: str, size: int | None = None) -> None:
    if path.is_symlink():
        raise VerificationError(f"symlink_file_refused:{path}")
    if not path.is_file() or not stat.S_ISREG(path.lstat().st_mode):
        raise VerificationError(f"missing_file:{path}")
    if size is not None and path.stat().st_size != size:
        raise VerificationError(f"size_mismatch:{path}")
    if file_hash(path) != digest:
        raise VerificationError(f"sha256_mismatch:{path}")


def utc(value: Any, label: str) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise VerificationError(f"invalid_timestamp:{label}:{value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise VerificationError(f"naive_timestamp:{label}:{value}")
    if parsed.utcoffset() != timedelta(0):
        raise VerificationError(f"non_utc_timestamp:{label}:{value}")
    return parsed.astimezone(timezone.utc)


def iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise VerificationError("naive_datetime")
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def envelope(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **dict(payload),
        "execution_authority": False,
        "activation_authority": False,
        "result_bearing_science_executed": False,
        "result_use_status": RESULT_USE_STATUS,
    }


def _scan_value_end(text: str, start: int) -> int:
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        raise VerificationError("pool_json_value_missing")
    opening = text[index]
    if opening == '"':
        escaped = False
        index += 1
        while index < len(text):
            character = text[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                return index + 1
            index += 1
        raise VerificationError("pool_json_string_unterminated")
    if opening in "[{":
        stack = [opening]
        index += 1
        in_string = False
        escaped = False
        while index < len(text) and stack:
            character = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
            elif character == '"':
                in_string = True
            elif character in "[{":
                stack.append(character)
            elif character in "]}":
                expected = "[" if character == "]" else "{"
                if not stack or stack.pop() != expected:
                    raise VerificationError("pool_json_container_mismatch")
            index += 1
        if stack:
            raise VerificationError("pool_json_container_unterminated")
        return index
    while index < len(text) and text[index] not in ",}":
        index += 1
    return index


def project_pool_control_json(text: str, *, label: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    index = 0
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text) or text[index] != "{":
        raise VerificationError(f"pool_row_not_object:{label}")
    index += 1
    output: dict[str, Any] = {}
    seen: set[str] = set()
    while True:
        while index < len(text) and text[index].isspace():
            index += 1
        if index < len(text) and text[index] == "}":
            index += 1
            break
        try:
            key, key_end = decoder.raw_decode(text, index)
        except json.JSONDecodeError as exc:
            raise VerificationError(f"pool_json_key_invalid:{label}") from exc
        if not isinstance(key, str) or key in seen:
            raise VerificationError(f"duplicate_json_key:{label}:{key}")
        seen.add(key)
        index = key_end
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != ":":
            raise VerificationError(f"pool_json_colon_missing:{label}:{key}")
        start = index + 1
        end = _scan_value_end(text, start)
        if key in ALLOWED_POOL_FIELDS:
            output[key] = strict_json_loads(text[start:end], label=f"{label}:{key}")
        index = end
        while index < len(text) and text[index].isspace():
            index += 1
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index < len(text) and text[index] == "}":
            index += 1
            break
        raise VerificationError(f"pool_json_separator_invalid:{label}")
    if text[index:].strip():
        raise VerificationError(f"pool_json_trailing_data:{label}")
    return output


def commissioned_domain() -> dict[tuple[str, str, str, str], dict[str, str]]:
    output: dict[tuple[str, str, str, str], dict[str, str]] = {}
    counts: Counter[str] = Counter()
    candidate_counts: Counter[str] = Counter()
    for window, relative, digest, size in POOL_BINDINGS:
        path = REPO_ROOT / relative
        require_file(path, digest, size)
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                row = project_pool_control_json(line, label=f"{relative}:{line_number}")
                if set(row) != ALLOWED_POOL_FIELDS:
                    raise VerificationError(f"pool_projection_missing_fields:{relative}:{line_number}")
                if any(not isinstance(row[field], str) or not row[field] for field in ALLOWED_POOL_FIELDS):
                    raise VerificationError(f"pool_control_type_invalid:{relative}:{line_number}")
                decision = utc(row["decision_time_utc"], "decision_time_utc")
                if not WINDOWS[window][0] <= decision.date().isoformat() <= WINDOWS[window][1]:
                    raise VerificationError(f"pool_window_mismatch:{relative}:{line_number}")
                side = str(row["side"]).upper()
                if side != str(row["direction"]).upper():
                    raise VerificationError(f"pool_side_mismatch:{relative}:{line_number}")
                key = (str(row["candidate_id"]), str(row["symbol"]), side, iso(decision))
                if key in output:
                    raise VerificationError(f"pool_duplicate_identity:{key}")
                output[key] = {
                    "window": window,
                    "kill_zone": str(row["kill_zone"]),
                    "origin_family": str(row["origin_family"]),
                    "framework": str(row["framework"]),
                    "route_family": str(row["route_family"]),
                }
                counts[window] += 1
                candidate_counts[key[0]] += 1
    if len(output) != EXPECTED_TOTAL or dict(counts) != EXPECTED_WINDOWS:
        raise VerificationError(f"commissioned_domain_count_mismatch:{len(output)}:{dict(counts)}")
    reused = sum(count > 1 for count in candidate_counts.values())
    rows_under_reuse = sum(count for count in candidate_counts.values() if count > 1)
    if (
        reused != EXPECTED_REUSED_CANDIDATE_IDS
        or rows_under_reuse != EXPECTED_ROWS_UNDER_REUSED_CANDIDATE_IDS
    ):
        raise VerificationError(
            f"candidate_id_reuse_mismatch:ids={reused}:rows={rows_under_reuse}"
        )
    return output


def jsonl_gzip(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            row = strict_json_loads(line, label=f"{path}:{line_number}")
            if not isinstance(row, dict):
                raise VerificationError(f"packet_row_not_object:{path}:{line_number}")
            rows.append(row)
    return rows


def independently_aggregate_h1(m15_rows: Sequence[Mapping[str, Any]], symbol: str) -> list[dict[str, Any]]:
    buckets: dict[datetime, list[Mapping[str, Any]]] = defaultdict(list)
    for row in m15_rows:
        timestamp = utc(row["time_utc"], "m15.time_utc")
        buckets[timestamp.replace(minute=0, second=0, microsecond=0)].append(row)
    output: list[dict[str, Any]] = []
    for bucket in sorted(buckets):
        rows = sorted(buckets[bucket], key=lambda row: utc(row["time_utc"], "m15.time_utc"))
        output.append({
            "time": iso(bucket),
            "time_utc": iso(bucket),
            "symbol": symbol,
            "open": float(rows[0]["open"]),
            "high": max(float(row["high"]) for row in rows),
            "low": min(float(row["low"]) for row in rows),
            "close": float(rows[-1]["close"]),
            "volume": sum(float(row["volume"]) for row in rows),
        })
    return output


def canonical_jsonl_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(canonical(dict(row)) + b"\n" for row in rows)


def deterministic_jsonl_gzip_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    raw = io.BytesIO()
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    text = io.TextIOWrapper(compressed, encoding="utf-8", newline="\n")
    for row in rows:
        text.write(canonical(dict(row)).decode("utf-8"))
        text.write("\n")
    text.flush()
    text.detach()
    compressed.close()
    return raw.getvalue()


def runtime_audit_refusal(event: str, arguments: tuple[Any, ...]) -> str | None:
    if (
        event in {"subprocess.Popen", "os.system", "os.popen", "pty.spawn"}
        or event.startswith("os.exec")
        or event.startswith("os.spawn")
        or event.startswith("os.posix_spawn")
    ):
        return f"runtime_subprocess_or_exec_forbidden:{event}"
    if event.startswith("socket.") and event not in {"socket.gethostname"}:
        return f"runtime_network_forbidden:{event}"
    if event in {
        "os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.symlink", "os.link",
        "os.chmod", "os.truncate", "os.utime", "os.chdir", "os.putenv", "os.unsetenv",
    }:
        return f"runtime_filesystem_or_environment_mutation_forbidden:{event}"
    if event == "import" and arguments:
        module = str(arguments[0])
        if (
            module == "MetaTrader5" or module.startswith("src.mt5")
            or module.startswith("src.components.execution")
            or module.startswith("src.components.orchestrator")
        ):
            return f"runtime_live_import_forbidden:{module}"
    if event == "open" and len(arguments) >= 3:
        mode = arguments[1]
        flags = arguments[2]
        if isinstance(mode, str) and any(token in mode for token in ("w", "a", "x", "+")):
            return "runtime_write_forbidden:open"
        if isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            return "runtime_write_forbidden:open"
    return None


def install_runtime_audit_guard() -> None:
    def guard(event: str, arguments: tuple[Any, ...]) -> None:
        refusal = runtime_audit_refusal(event, arguments)
        if refusal is not None:
            raise VerificationError(refusal)

    sys.addaudithook(guard)


def independent_atr(candles: Sequence[Mapping[str, Any]], period: int = 14) -> float:
    if len(candles) < 2:
        return 0.0
    ranges = [
        max(
            float(candles[index]["high"]) - float(candles[index]["low"]),
            abs(float(candles[index]["high"]) - float(candles[index - 1]["close"])),
            abs(float(candles[index]["low"]) - float(candles[index - 1]["close"])),
        )
        for index in range(1, len(candles))
    ]
    if len(ranges) < period:
        return sum(ranges) / len(ranges)
    result = sum(ranges[:period]) / period
    for value in ranges[period:]:
        result = (result * (period - 1) + value) / period
    return result


def independent_breaker_projection(
    candles: Sequence[Mapping[str, Any]], *, min_bars: int, dead_zone_divisor: int
) -> list[dict[str, Any]]:
    swings: list[dict[str, Any]] = []
    for index in range(min_bars, len(candles) - min_bars):
        if all(
            float(candles[index]["high"]) > float(candles[index-offset]["high"])
            and float(candles[index]["high"]) > float(candles[index+offset]["high"])
            for offset in range(1, min_bars + 1)
        ):
            swings.append({"index": index, "type": "high", "price": float(candles[index]["high"]), "time": candles[index]["time"]})
        if all(
            float(candles[index]["low"]) < float(candles[index-offset]["low"])
            and float(candles[index]["low"]) < float(candles[index+offset]["low"])
            for offset in range(1, min_bars + 1)
        ):
            swings.append({"index": index, "type": "low", "price": float(candles[index]["low"]), "time": candles[index]["time"]})
    swings.sort(key=lambda row: int(row["index"]))
    highs = [row for row in swings if row["type"] == "high"]
    lows = [row for row in swings if row["type"] == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return []
    hh = sum(float(highs[i]["price"]) > float(highs[i-1]["price"]) for i in range(1, len(highs)))
    ll = sum(float(lows[i]["price"]) < float(lows[i-1]["price"]) for i in range(1, len(lows)))
    hl = sum(float(lows[i]["price"]) > float(lows[i-1]["price"]) for i in range(1, len(lows)))
    lh = sum(float(highs[i]["price"]) < float(highs[i-1]["price"]) for i in range(1, len(highs)))
    score = hh + hl - lh - ll
    threshold = max(2, min(len(highs) - 1, len(lows) - 1) // max(1, dead_zone_divisor))
    if score > threshold:
        direction, protected = "bullish", lows[-1]
    elif score < -threshold:
        direction, protected = "bearish", highs[-1]
    else:
        direction, protected = "transitional", None

    avg_body = sum(abs(float(row["close"]) - float(row["open"])) for row in candles[-20:]) / min(20, len(candles))
    events: list[dict[str, Any]] = []
    broken_levels: set[float] = set()
    choch_fired = False
    for index, candle in enumerate(candles):
        if direction == "bullish":
            recent = next((row for row in reversed(swings) if row["type"] == "high" and int(row["index"]) < index), None)
            if recent and float(candle["close"]) > float(recent["price"]) and float(recent["price"]) not in broken_levels:
                broken_levels.add(float(recent["price"]))
                events.append({"type": "BOS", "direction": "bullish", "index": index})
        elif direction == "bearish":
            recent = next((row for row in reversed(swings) if row["type"] == "low" and int(row["index"]) < index), None)
            if recent and float(candle["close"]) < float(recent["price"]) and float(recent["price"]) not in broken_levels:
                broken_levels.add(float(recent["price"]))
                events.append({"type": "BOS", "direction": "bearish", "index": index})
        if protected is not None and not choch_fired and index > int(protected["index"]):
            if direction == "bullish" and float(candle["close"]) < float(protected["price"]):
                choch_fired = True
                events.append({"type": "CHoCH", "direction": "bearish", "index": index})
            elif direction == "bearish" and float(candle["close"]) > float(protected["price"]):
                choch_fired = True
                events.append({"type": "CHoCH", "direction": "bullish", "index": index})

    order_blocks: list[dict[str, Any]] = []
    seen: set[int] = set()
    for event in events:
        break_index = int(event["index"])
        wanted_bearish = event["direction"] == "bullish"
        for index in range(break_index - 1, max(break_index - 10, -1), -1):
            if index < 0:
                break
            candle = candles[index]
            opposing = (
                float(candle["close"]) < float(candle["open"])
                if wanted_bearish else float(candle["close"]) > float(candle["open"])
            )
            if not opposing:
                continue
            if index in seen:
                break
            seen.add(index)
            block_type = "bullish" if wanted_bearish else "bearish"
            mitigated = any(
                float(candles[k]["low"]) <= float(candle["high"])
                if block_type == "bullish"
                else float(candles[k]["high"]) >= float(candle["low"])
                for k in range(break_index + 1, len(candles))
            )
            order_blocks.append({
                "type": block_type, "high": float(candle["high"]), "low": float(candle["low"]),
                "formation_time": candle["time"], "causing_index": break_index,
                "mitigated": mitigated, "causing_event": event["type"],
            })
            break

    output: list[dict[str, Any]] = []
    for block in order_blocks:
        if not block["mitigated"]:
            continue
        mitigation_index: int | None = None
        for index in range(int(block["causing_index"]) + 1, len(candles)):
            close = float(candles[index]["close"])
            if (block["type"] == "bullish" and close < float(block["low"])) or (
                block["type"] == "bearish" and close > float(block["high"])
            ):
                mitigation_index = index
                break
        if mitigation_index is None:
            continue
        breaker_direction = "bearish" if block["type"] == "bullish" else "bullish"
        retested = any(
            (
                float(candles[index]["low"]) <= float(block["high"])
                and float(candles[index]["close"]) >= float(block["low"])
            ) if breaker_direction == "bullish" else (
                float(candles[index]["high"]) >= float(block["low"])
                and float(candles[index]["close"]) <= float(block["high"])
            )
            for index in range(mitigation_index + 1, len(candles))
        )
        output.append({
            "zone_high": block["high"], "zone_low": block["low"],
            "direction": breaker_direction, "original_ob_direction": block["type"],
            "formation_time": block["formation_time"],
            "mitigation_time": candles[mitigation_index]["time"],
            "causing_event": block["causing_event"], "is_retested": retested,
        })
    return output


def independent_closed_slice(
    rows: Sequence[Mapping[str, Any]], decision: datetime, minutes: int, lookback: int
) -> tuple[int, int]:
    times = [utc(row["time_utc"], "series.time_utc") for row in rows]
    if times != sorted(times) or len(times) != len(set(times)):
        raise VerificationError("series_time_order_or_uniqueness_invalid")
    closes = [timestamp + timedelta(minutes=minutes) for timestamp in times]
    return independent_closed_slice_from_closes(closes, decision, lookback)


def independent_closed_slice_from_closes(
    closes: Sequence[datetime], decision: datetime, lookback: int
) -> tuple[int, int]:
    if decision.tzinfo is None or decision.utcoffset() is None:
        raise VerificationError("naive_decision_timestamp")
    stop = bisect.bisect_right(closes, decision)
    start = max(0, stop - lookback)
    if stop <= start or closes[stop - 1] > decision:
        raise VerificationError("postdecision_or_empty_slice")
    return start, stop


def _merge_generation_config() -> dict[str, Any]:
    base_path = REPO_ROOT / "config/agent_config.yaml"
    profile_path = REPO_ROOT / "config/profiles/operator_profile.yaml"
    require_file(base_path, BASE_CONFIG_SHA256)
    require_file(profile_path, FTMO_PROFILE_SHA256)
    base = yaml.safe_load(base_path.read_text()) or {}
    profile = yaml.safe_load(profile_path.read_text()) or {}
    output = copy.deepcopy(base)
    instruments = copy.deepcopy(profile.get("instruments") or {})
    for symbol, base_row in (base.get("instruments") or {}).items():
        if not isinstance(base_row, Mapping):
            continue
        row = instruments.setdefault(symbol, {})
        for key, value in base_row.items():
            if key == "market" and isinstance(value, Mapping):
                market = copy.deepcopy(row.get("market") or {})
                market.update(copy.deepcopy(value))
                row["market"] = market
            elif key == "risk" and isinstance(value, Mapping):
                risk = copy.deepcopy(row.get("risk") or {})
                for risk_key, risk_value in value.items():
                    risk.setdefault(risk_key, copy.deepcopy(risk_value))
                row["risk"] = risk
            elif key not in row:
                row[key] = copy.deepcopy(value)
    output["instruments"] = instruments
    output.setdefault("market_state", {})["side_effect_writes_enabled"] = False
    output["market_state"]["structure_shadow_log_enabled"] = False
    output.setdefault("gtos_vnext_runtime", {})[
        "phase18_current_breaker_re_entry_repair_enabled"
    ] = False
    return output


def _symbol_config(config: Mapping[str, Any], symbol: str) -> dict[str, Any]:
    output = copy.deepcopy(dict(config))
    market = output.setdefault("market", {})
    market["symbol"] = symbol
    market["mt5_symbol"] = str(
        ((output.get("instruments") or {}).get(symbol) or {}).get("market", {}).get("mt5_symbol")
        or symbol
    )
    return output


def _raw(symbol: str, decision: datetime, m15: Sequence[Mapping[str, Any]], h1: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "timestamp_utc": iso(decision),
        "candles": {"D1": [], "H4": [], "H1": list(h1), "M15": list(m15)},
        "session_levels": {},
        "data_quality": {
            "all_timeframes_complete": False,
            "spread_normal": False,
            "mt5_connected": False,
            "timestamp_utc": iso(decision),
        },
        "candle_open_utc": str(m15[-1]["time_utc"]),
        "candle_close_utc": iso(utc(m15[-1]["time_utc"], "m15.time_utc") + timedelta(minutes=15)),
    }


def _breaker_projection(mso: Any) -> list[dict[str, Any]]:
    fields = (
        "zone_high", "zone_low", "direction", "original_ob_direction",
        "formation_time", "mitigation_time", "causing_event", "is_retested",
    )
    return [
        {field: getattr(breaker, field) for field in fields}
        for breaker in mso.timeframes["H1"].breaker_blocks
    ]


def _git_show_bytes(commit: str, path: str) -> bytes:
    if len(commit) != 40 or any(character not in "009abcdef" for character in commit):
        raise VerificationError(f"git_commit_invalid:{commit}")
    normalized_relative_path(path, label="git_evidence_path")
    try:
        return subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise VerificationError(f"git_evidence_read_failed:{commit}:{path}") from exc


def _verify_descriptor_set(
    values: Any, *, expected_paths: set[str], root: Path, label: str
) -> dict[str, dict[str, Any]]:
    if not isinstance(values, list):
        raise VerificationError(f"descriptor_list_type_invalid:{label}")
    output: dict[str, dict[str, Any]] = {}
    for number, value in enumerate(values):
        row = validate_file_descriptor(value, label=f"{label}:{number}")
        path = row["path"]
        if path in output:
            raise VerificationError(f"duplicate_descriptor:{label}:{path}")
        candidate = contained_regular_file(root, path, label=f"{label}:{path}")
        require_file(candidate, row["sha256"], row["bytes"])
        output[path] = row
    if set(output) != expected_paths:
        raise VerificationError(
            f"descriptor_path_set_mismatch:{label}:missing={sorted(expected_paths-set(output))}:extra={sorted(set(output)-expected_paths)}"
        )
    return output


def _require_false_flags(row: Mapping[str, Any], fields: Sequence[str], *, label: str) -> None:
    for field in fields:
        if row.get(field) is not False:
            raise VerificationError(f"{label}_boundary_invalid:{field}")


def _validate_u4_u11_documents(
    *,
    u4: Mapping[str, Any],
    u11: Mapping[str, Any],
    adapter_bytes: bytes,
    adapter_binding: Mapping[str, Any],
    b0_bytes: bytes,
) -> dict[str, Any]:
    _require_false_flags(u4, (
        "activation_authority", "execution_authority", "result_bearing_science_executed",
        "broker_contacted", "runtime_or_production_contacted",
        "secret_or_account_identity_fields_included",
    ), label="u4")
    if (
        u4.get("schema") != "gtos.p1-inert-profile-symbol-snapshot.v1"
        or u4.get("status") != "U4_CLOSED_INERT_PROFILE_SYMBOL_SNAPSHOT_BOUND"
        or u4.get("tested_source_commit") != EXPECTED_HN_TESTED_SOURCE_COMMIT
        or u4.get("symbol_count") != 24
        or u4.get("symbol_domain") != list(EXPECTED_SYMBOLS)
        or u4.get("result_use_status") != RESULT_USE_STATUS
    ):
        raise VerificationError("u4_identity_or_domain_invalid")
    expected_u5 = {
        "broker_volume_min_max_step_are_mechanical_constraints_not_selected_size": True,
        "owner_risk_or_allocation_invented": False,
        "research_volume_selected": False,
        "status": "NOT_EVALUABLE_OWNER_INPUT_REQUIRED",
    }
    if u4.get("u5_volume_owner_risk") != expected_u5:
        raise VerificationError("u5_owner_input_boundary_invalid")
    profiles = u4.get("profiles")
    roles = {
        "operator_profile": "FTMO_RESEARCH_SOURCE_CONTROL_ECONOMIC_AND_MECHANICAL_INPUT_ONLY_NO_RESULT_COMPUTED",
        "redacted_account": "MECHANICAL_SYMBOL_GEOMETRY_ONLY_NEVER_ECONOMIC_VERDICT",
    }
    if not isinstance(profiles, Mapping) or set(profiles) != set(roles):
        raise VerificationError("u4_profile_set_invalid")
    for name, role in roles.items():
        profile = profiles[name]
        if (
            not isinstance(profile, Mapping) or profile.get("profile_name") != name
            or profile.get("role") != role or set(profile.get("symbols") or {}) != set(EXPECTED_SYMBOLS)
        ):
            raise VerificationError(f"u4_profile_role_or_domain_invalid:{name}")
    expected_sources = {
        path: {"path": path, "sha256": EXPECTED_REPO_AUTHORITIES[path][0], "bytes": EXPECTED_REPO_AUTHORITIES[path][1]}
        for path in ("config/agent_config.yaml", "config/profiles/operator_profile.yaml", "config/profiles/redacted_account.yaml")
    }
    source_rows = u4.get("source_bindings")
    if not isinstance(source_rows, list) or {row.get("path"): row for row in source_rows if isinstance(row, Mapping)} != expected_sources:
        raise VerificationError("u4_source_binding_mismatch")

    _require_false_flags(
        u11, ("activation_authority", "execution_authority", "result_bearing_science_executed"),
        label="u11",
    )
    if (
        u11.get("schema") != "gtos.p1-inert-route-parameter-bundle.v1"
        or u11.get("status") != "U11_CLOSED_HASH_BOUND_INERT_ROUTE_PARAMETERS"
        or u11.get("tested_source_commit") != EXPECTED_HN_TESTED_SOURCE_COMMIT
        or u11.get("result_use_status") != RESULT_USE_STATUS
    ):
        raise VerificationError("u11_identity_or_source_invalid")
    account_scope = {
        "ftmo": "ONLY_LATER_ECONOMIC_SCOPE",
        "redacted_account": "MECHANICAL_ONLY_NEVER_ECONOMIC_VERDICT",
        "owner_risk_or_allocation": "NOT_EVALUABLE_OWNER_INPUT_REQUIRED",
    }
    if u11.get("account_scope") != account_scope:
        raise VerificationError("u11_account_scope_invalid")
    route = u11.get("route_identity")
    expected_route = {
        "candidate": "cq_current_breaker_re_entry_inverted_5d_stop_0p25d",
        "candidate_count": 1, "candidate_family": "CANDIDATE_BOOK_V1_V27",
        "denominator_rows": EXPECTED_TOTAL, "fixed_disposition": "ADMIT_UNCHANGED_NOT_ACTIVATION",
        "identity_fields": ["candidate_id", "symbol", "side", "decision_time_utc"],
        "origin_family": "current_breaker_re_entry", "threshold_or_branch_rule_changed": False,
        "windows": {name: list(bounds) for name, bounds in WINDOWS.items()},
    }
    if route != expected_route:
        raise VerificationError("u11_route_identity_invalid")
    module_rows = u11.get("module_bindings")
    if not isinstance(module_rows, list):
        raise VerificationError("u11_module_bindings_invalid")
    modules: dict[str, Mapping[str, Any]] = {}
    for row in module_rows:
        if not isinstance(row, Mapping) or not _is_sha256(row.get("sha256")):
            raise VerificationError("u11_module_binding_invalid")
        module_path = normalized_relative_path(row.get("path"), label="u11_module")
        if module_path in modules or row.get("match") is not True or row.get("observed_sha256") != row.get("sha256"):
            raise VerificationError(f"u11_module_identity_invalid:{module_path}")
        modules[module_path] = row
    for module_path in ("src/components/orchestrator.py", "src/components/execution.py"):
        if modules.get(module_path, {}).get("import_policy") != "REFERENCE_ONLY_NEVER_IMPORT":
            raise VerificationError(f"u11_reference_policy_invalid:{module_path}")
    router_path = "src/research/moonshot_default_off_policy_router.py"
    runtime_path = "src/components/gtos_vnext_runtime.py"
    router = u11.get("router") or {}
    scheduler = u11.get("scheduler") or {}
    if router.get("path") != router_path or router.get("sha256") != modules.get(router_path, {}).get("sha256"):
        raise VerificationError("u11_legacy_router_binding_invalid")
    if runtime_path not in modules:
        raise VerificationError("u11_runtime_reference_missing")
    if scheduler.get("authority") != "CAPTURE_ONLY" or scheduler.get("may_select_rank_suppress_or_size") is not False:
        raise VerificationError("u11_scheduler_boundary_invalid")
    hde, hdf = u11.get("hde") or {}, u11.get("hdf") or {}
    hde_paths = ("src/components/broker_net_cost_engine.py", "src/research_infra/train_engine/decision_semantics.py", "src/research_infra/train_engine/repairs.py")
    hde_refs = dict(zip(hde_paths, (hde.get("cost_engine_sha256"), hde.get("decision_semantics_sha256"), hde.get("repair_sha256"))))
    if hde.get("executed_in_hn") is not False or any(modules.get(module_path, {}).get("sha256") != digest for module_path, digest in hde_refs.items()):
        raise VerificationError("u11_hde_reference_invalid")
    hdf_path = "src/research_infra/exit_overlay.py"
    if hdf.get("executed_in_hn") is not False or hdf.get("sha256") != modules.get(hdf_path, {}).get("sha256"):
        raise VerificationError("u11_hdf_reference_invalid")

    if len(adapter_bytes) != adapter_binding.get("bytes") or hashlib.sha256(adapter_bytes).hexdigest() != adapter_binding.get("sha256"):
        raise VerificationError("u11_adapter_blob_mismatch")
    adapter_tree = ast.parse(adapter_bytes, filename=str(adapter_binding.get("path") or "adapter"))
    callables = {node.name for node in ast.walk(adapter_tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    required_callables = {
        "source_bound_candidate_generator", "inert_admit_unchanged_router", "evaluate_inert_permission",
        "inert_scheduler_capture", "scheduler_capture_only", "source_bound_fill_projection",
        "project_hde_cost", "project_hdf_exit", "project_hdf_m1_exit", "run_complete_path_shadow",
    }
    if not required_callables.issubset(callables):
        raise VerificationError(f"u11_adapter_callable_set_incomplete:{sorted(required_callables-callables)}")
    if len(b0_bytes) != B0_BREAKER_ROUTE_BINDING["bytes"] or hashlib.sha256(b0_bytes).hexdigest() != B0_BREAKER_ROUTE_BINDING["sha256"]:
        raise VerificationError("b0_binding_bytes_mismatch")
    b0 = strict_json_loads(b0_bytes, label="b0_breaker_route")
    if canonical_hash(b0["candidate"]["family_member_record"]) != FIXED_BREAKER_MEMBER_CANONICAL_SHA256:
        raise VerificationError("b0_canonical_member_hash_mismatch")
    return {
        "u4_status": "U4_EXACT_ARTIFACT_AND_ROLE_BOUND",
        "u5_status": "NOT_EVALUABLE_OWNER_INPUT_REQUIRED",
        "u11_status": "U11_REPAIRED_ADAPTER_AND_REFERENCES_BOUND",
        "adapter": dict(adapter_binding), "required_adapter_callables": sorted(required_callables),
        "legacy_router_reference": {"path": router_path, "sha256": modules[router_path]["sha256"], "import_policy": "REFERENCE_ONLY_NEVER_IMPORT"},
        "runtime_reference": {"path": runtime_path, "sha256": modules[runtime_path]["sha256"], "import_policy": "REFERENCE_ONLY_NEVER_IMPORT"},
        "hde_reference_hashes": hde_refs,
        "hdf_reference": {"path": hdf_path, "sha256": modules[hdf_path]["sha256"]},
        "b0_breaker_route_binding": dict(B0_BREAKER_ROUTE_BINDING),
        "family_member_record_canonical_sha256": FIXED_BREAKER_MEMBER_CANONICAL_SHA256,
        "account_roles": account_scope,
    }


def validate_u4_and_repair_u11(
    expected_tested_source_commit: str,
    *,
    adapter_binding: Mapping[str, Any],
    _git_reader: Any = _git_show_bytes,
) -> dict[str, Any]:
    hn_commit = EXPECTED_EVIDENCE_LINEAGE["hn_evidence_closeout"][0]
    paths = {
        "u4": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_INERT_PROFILE_SYMBOL_SNAPSHOT.json",
        "u11": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_INERT_ROUTE_PARAMETER_BUNDLE.json",
    }
    expected_artifacts = {path: (digest, size) for path, digest, size in EXPECTED_EVIDENCE_ARTIFACTS["hn_evidence_closeout"]}
    documents: dict[str, Mapping[str, Any]] = {}
    for label, artifact_path in paths.items():
        payload = _git_reader(hn_commit, artifact_path)
        digest, size = expected_artifacts[artifact_path]
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
            raise VerificationError(f"{label}_artifact_bytes_mismatch")
        documents[label] = strict_json_loads(payload, label=f"hn_{label}")
    adapter_path = str(adapter_binding.get("path") or "")
    controls = _validate_u4_u11_documents(
        u4=documents["u4"], u11=documents["u11"],
        adapter_bytes=_git_reader(expected_tested_source_commit, adapter_path),
        adapter_binding=adapter_binding,
        b0_bytes=_git_reader(B0_BREAKER_ROUTE_BINDING["commit"], B0_BREAKER_ROUTE_BINDING["path"]),
    )
    for row in documents["u11"].get("module_bindings") or []:
        payload = _git_reader(expected_tested_source_commit, row["path"])
        if len(payload) != row["bytes"] or hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise VerificationError(f"u11_tested_source_module_mismatch:{row['path']}")
    return controls


def validate_manifest(
    manifest: Any,
    *,
    expected_payload_root_sha256: str,
    expected_tested_source_commit: str,
    _expectations: _PacketExpectations = _PRODUCTION_EXPECTATIONS,
    _authority_git_reader: Any = _git_show_bytes,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    row = _exact_keys(manifest, MANIFEST_KEYS, label="manifest", reason="manifest_schema_invalid")
    if row["schema"] != "gtos.p1-upstream-source-packet.v2" or row["status"] != "FROZEN":
        raise VerificationError("manifest_identity_invalid")
    if row["tested_source_commit"] != expected_tested_source_commit:
        raise VerificationError("manifest_tested_source_commit_mismatch")
    parents = subprocess.run(
        ["git", "show", "-s", "--format=%P", expected_tested_source_commit], cwd=REPO_ROOT,
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.decode().strip().split()
    if parents != [_expectations.source_parent]:
        raise VerificationError(f"tested_source_parent_mismatch:{parents}")
    if row["packet_payload_root_sha256"] != expected_payload_root_sha256:
        raise VerificationError("manifest_expected_payload_root_mismatch")
    expected_name = f"p1-source-packet-sha256-{expected_payload_root_sha256}"
    if row["packet_directory_name"] != expected_name or row["source_root"] != _expectations.source_root.as_posix():
        raise VerificationError("manifest_packet_or_source_identity_mismatch")
    if row["external_packet_immutable"] is not True:
        raise VerificationError("manifest_external_immutable_invalid")
    _require_false_flags(
        row, ("execution_authority", "activation_authority", "result_bearing_science_executed"),
        label="manifest",
    )
    if row["result_use_status"] != RESULT_USE_STATUS or row["commissioned_source_payload_count"] != _expectations.source_payload_count:
        raise VerificationError("manifest_source_or_result_boundary_invalid")

    route = _exact_keys(
        row["route_identity"], {
            "candidate", "candidate_family", "origin_family", "transform_id", "identity_fields",
            "denominator_rows", "windows", "disposition", "family_member_record_canonical_sha256",
            "b0_breaker_route_binding",
        }, label="manifest:route_identity", reason="manifest_route_schema_invalid",
    )
    expected_route = {
        "candidate": "cq_current_breaker_re_entry_inverted_5d_stop_0p25d",
        "candidate_family": "CANDIDATE_BOOK_V1_V27", "origin_family": "current_breaker_re_entry",
        "transform_id": "cq_current_breaker_inverted_target_5d_stop_0p25d_v1",
        "identity_fields": ["candidate_id", "symbol", "side", "decision_time_utc"],
        "denominator_rows": _expectations.total,
        "windows": {name: list(bounds) for name, bounds in _expectations.windows},
        "disposition": "ADMIT_UNCHANGED_NOT_ACTIVATION",
        "family_member_record_canonical_sha256": FIXED_BREAKER_MEMBER_CANONICAL_SHA256,
    }
    for key, expected in expected_route.items():
        if route[key] != expected:
            raise VerificationError(f"manifest_route_value_mismatch:{key}")
    b0_binding = _exact_keys(
        route["b0_breaker_route_binding"], set(B0_BREAKER_ROUTE_BINDING),
        label="manifest:b0_binding", reason="b0_binding_schema_invalid",
    )
    if dict(b0_binding) != B0_BREAKER_ROUTE_BINDING:
        raise VerificationError("b0_binding_identity_mismatch")
    b0_bytes = _git_show_bytes(B0_BREAKER_ROUTE_BINDING["commit"], B0_BREAKER_ROUTE_BINDING["path"])
    if len(b0_bytes) != B0_BREAKER_ROUTE_BINDING["bytes"] or hashlib.sha256(b0_bytes).hexdigest() != B0_BREAKER_ROUTE_BINDING["sha256"]:
        raise VerificationError("b0_binding_bytes_mismatch")
    if canonical_hash(strict_json_loads(b0_bytes, label="b0")["candidate"]["family_member_record"]) != FIXED_BREAKER_MEMBER_CANONICAL_SHA256:
        raise VerificationError("b0_canonical_member_hash_mismatch")

    coverage_keys = {
        "activation_authority", "candidate_ids_reused", "duplicate_composite_identities",
        "duplicate_generator_matches", "execution_authority", "h1_lookback", "identity_matches",
        "identity_rows", "minimum_closed_m15_bars", "out_of_window_rows", "postdecision_reads",
        "predecision_state_count", "required_minimum_closed_m15_bars",
        "result_bearing_science_executed", "result_use_status", "rows_under_reused_candidate_ids",
        "schema", "source_multiplicity_by_symbol", "status", "unique_composite_identities",
        "unmatched_identities", "window_counts",
    }
    coverage = _exact_keys(row["coverage"], coverage_keys, label="manifest:coverage", reason="coverage_schema_invalid")
    fixed_counts = {
        "candidate_ids_reused": _expectations.reused_candidate_ids,
        "rows_under_reused_candidate_ids": _expectations.rows_under_reused_candidate_ids,
        "identity_rows": _expectations.total, "identity_matches": _expectations.total,
        "unique_composite_identities": _expectations.total,
        "predecision_state_count": _expectations.state_count,
        "duplicate_composite_identities": 0, "duplicate_generator_matches": 0,
        "unmatched_identities": 0, "postdecision_reads": 0, "out_of_window_rows": 0,
    }
    for key, expected in fixed_counts.items():
        if coverage[key] != expected or isinstance(coverage[key], bool):
            raise VerificationError(f"coverage_value_mismatch:{key}")
    if coverage["window_counts"] != dict(_expectations.window_counts):
        raise VerificationError("coverage_window_counts_mismatch")
    if coverage["schema"] != "gtos.p1-upstream-source-coverage.v1" or coverage["status"] != "COMPLETE":
        raise VerificationError("coverage_identity_invalid")
    if (
        coverage["minimum_closed_m15_bars"] != _expectations.m15_lookback
        or coverage["required_minimum_closed_m15_bars"] != _expectations.minimum_closed_m15
        or coverage["h1_lookback"] != _expectations.h1_lookback
    ):
        raise VerificationError("coverage_lookback_value_mismatch")
    multiplicity = coverage["source_multiplicity_by_symbol"]
    if not isinstance(multiplicity, Mapping) or set(multiplicity) != set(_expectations.symbols):
        raise VerificationError("coverage_symbol_domain_mismatch")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in multiplicity.values()) or sum(multiplicity.values()) != _expectations.total:
        raise VerificationError("coverage_source_multiplicity_invalid")
    _require_false_flags(
        coverage, ("execution_authority", "activation_authority", "result_bearing_science_executed"),
        label="coverage",
    )
    if coverage["result_use_status"] != RESULT_USE_STATUS:
        raise VerificationError("coverage_result_use_invalid")
    asof = _exact_keys(
        row["asof_contract"], {"close_tolerance_seconds", "h1_bar_close_minutes", "h1_lookback", "m15_bar_close_minutes", "m15_lookback", "postdecision_reads_allowed"},
        label="manifest:asof", reason="asof_schema_invalid",
    )
    if asof != {
        "close_tolerance_seconds": 0, "h1_bar_close_minutes": 60,
        "h1_lookback": _expectations.h1_lookback, "m15_bar_close_minutes": 15,
        "m15_lookback": _expectations.m15_lookback, "postdecision_reads_allowed": False,
    }:
        raise VerificationError("asof_contract_value_mismatch")

    payload_values = row["payload_files"]
    if not isinstance(payload_values, list) or len(payload_values) != _expectations.payload_count:
        raise VerificationError("manifest_payload_count_invalid")
    payload_rows: list[dict[str, Any]] = []
    seen_payload: set[str] = set()
    for number, value in enumerate(payload_values):
        descriptor = validate_file_descriptor(value, label=f"payload:{number}")
        if descriptor["path"] in seen_payload:
            raise VerificationError(f"duplicate_payload_descriptor:{descriptor['path']}")
        seen_payload.add(descriptor["path"])
        payload_rows.append(descriptor)

    expected_repo = {path: (digest, size) for path, digest, size in _expectations.repo_authorities}
    repo = _verify_descriptor_set(
        row["repo_authorities"], expected_paths=set(expected_repo), root=_expectations.repo_root,
        label="repo_authorities",
    )
    for path, (digest, size) in expected_repo.items():
        if repo[path]["sha256"] != digest or repo[path]["bytes"] != size:
            raise VerificationError(f"repo_authority_binding_mismatch:{path}")
    generator = _exact_keys(
        row["generator"], {"path", "sha256", "market_state_path", "market_state_sha256", "h1_aggregation_reference_path", "h1_aggregation_reference_sha256", "transitive_authority"},
        label="manifest:generator", reason="generator_schema_invalid",
    )
    transitive: dict[str, dict[str, Any]] = {}
    if not isinstance(generator["transitive_authority"], list):
        raise VerificationError("transitive_authority_type_invalid")
    for number, value in enumerate(generator["transitive_authority"]):
        descriptor = validate_file_descriptor(value, label=f"transitive:{number}")
        if descriptor["path"] in transitive:
            raise VerificationError(f"duplicate_transitive_descriptor:{descriptor['path']}")
        transitive[descriptor["path"]] = descriptor
    if set(transitive) != set(_expectations.transitive_paths) or any(transitive[path] != repo[path] for path in transitive):
        raise VerificationError("transitive_repo_binding_mismatch")

    expected_manifests = dict(_expectations.source_manifests)
    source_manifests = _verify_descriptor_set(
        row["source_manifests"], expected_paths=set(expected_manifests), root=_expectations.source_root,
        label="source_manifests",
    )
    if any(source_manifests[path]["sha256"] != digest for path, digest in expected_manifests.items()):
        raise VerificationError("source_manifest_binding_mismatch")
    tooling = _verify_descriptor_set(
        row["packet_tooling"], expected_paths=set(_expectations.tooling_paths),
        root=_expectations.repo_root, label="packet_tooling",
    )
    for path in _expectations.source_commit_bound_paths:
        descriptor = tooling[path] if path in tooling else repo[path]
        committed = _git_show_bytes(expected_tested_source_commit, path)
        if len(committed) != descriptor["bytes"] or hashlib.sha256(committed).hexdigest() != descriptor["sha256"]:
            raise VerificationError(f"tested_source_blob_mismatch:{path}")
    expected_generator = {
        "path": _expectations.generator_path, "sha256": _expectations.generator_sha256,
        "market_state_path": _expectations.market_state_path,
        "market_state_sha256": _expectations.market_state_sha256,
        "h1_aggregation_reference_path": _expectations.h1_reference_path,
        "h1_aggregation_reference_sha256": _expectations.h1_reference_sha256,
    }
    for key, expected in expected_generator.items():
        if generator[key] != expected:
            raise VerificationError(f"generator_binding_mismatch:{key}")
    timebase = _exact_keys(
        row["timebase_authority"], {"time_column_basis", "broker_clock_rule", "conversion_function", "conversion_code_sha256"},
        label="manifest:timebase", reason="timebase_schema_invalid",
    )
    if timebase != {
        "time_column_basis": "true_utc", "broker_clock_rule": "new_york_plus_7",
        "conversion_function": "src.utils.broker_clock.broker_epoch_to_utc",
        "conversion_code_sha256": _expectations.timebase_sha256,
    }:
        raise VerificationError("timebase_authority_mismatch")

    lineage = {label: (commit, parent, role) for label, commit, parent, role in _expectations.evidence_lineage}
    artifact_sets = dict(_expectations.evidence_artifacts)
    authorities = row["immutable_evidence_authorities"]
    if not isinstance(authorities, Mapping) or set(authorities) != set(lineage):
        raise VerificationError("evidence_authority_set_mismatch")
    for label, authority_value in authorities.items():
        authority = _exact_keys(
            authority_value, {"commit", "parent", "one_parent_verified", "artifacts", "implementation_ancestry_role"},
            label=f"evidence:{label}", reason="evidence_schema_invalid",
        )
        commit, parent, role = lineage[label]
        if authority["one_parent_verified"] is not True or authority["implementation_ancestry_role"] != role or (authority["commit"], authority["parent"]) != (commit, parent):
            raise VerificationError(f"evidence_identity_or_role_invalid:{label}")
        observed_parents = subprocess.run(
            ["git", "show", "-s", "--format=%P", commit], cwd=REPO_ROOT, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.decode().strip().split()
        if observed_parents != [parent]:
            raise VerificationError(f"evidence_parent_mismatch:{label}")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, expected_tested_source_commit], cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False,
        ).returncode == 0
        if ancestor is not role.startswith("SOURCE_ANCESTOR_"):
            raise VerificationError(f"evidence_ancestry_role_mismatch:{label}")
        expected_artifacts = [{"path": path, "sha256": digest, "bytes": size} for path, digest, size in artifact_sets[label]]
        if authority["artifacts"] != expected_artifacts:
            raise VerificationError(f"evidence_artifact_set_mismatch:{label}")
        for artifact in expected_artifacts:
            blob = _git_show_bytes(commit, artifact["path"])
            if len(blob) != artifact["bytes"] or hashlib.sha256(blob).hexdigest() != artifact["sha256"]:
                raise VerificationError(f"evidence_artifact_mismatch:{label}:{artifact['path']}")

    adapter_path = "docs/audits/fable5-vision-audit-20260725/phase20/receipts/wave20_complete_path_shadow.py"
    authority_controls = validate_u4_and_repair_u11(
        expected_tested_source_commit,
        adapter_binding=tooling[adapter_path],
        _git_reader=_authority_git_reader,
    )
    return payload_rows, repo, authority_controls


def validate_series_descriptor(
    value: Any, *, symbol: str, timeframe: str, payload: Mapping[str, Mapping[str, Any]]
) -> Mapping[str, Any]:
    row = _exact_keys(
        value, SERIES_DESCRIPTOR_KEYS, label=f"series:{symbol}:{timeframe}",
        reason="series_descriptor_schema_invalid",
    )
    minutes = 15 if timeframe == "M15" else 60
    expected_path = f"series/{symbol}.{timeframe.lower()}.jsonl.gz"
    if row["path"] != expected_path or row["timeframe_minutes"] != minutes:
        raise VerificationError(f"series_descriptor_identity_mismatch:{symbol}:{timeframe}")
    if row["time_column_basis"] != "true_utc":
        raise VerificationError(f"series_timebase_invalid:{symbol}:{timeframe}")
    if isinstance(row["row_count"], bool) or not isinstance(row["row_count"], int) or row["row_count"] <= 0:
        raise VerificationError(f"series_row_count_type_invalid:{symbol}:{timeframe}")
    descriptor = validate_file_descriptor(
        {key: row[key] for key in ("path", "bytes", "sha256")},
        label=f"series:{symbol}:{timeframe}",
    )
    if payload.get(expected_path) != descriptor:
        raise VerificationError(f"series_payload_binding_mismatch:{symbol}:{timeframe}")
    first = utc(row["first_utc"], f"series:{symbol}:{timeframe}:first")
    last = utc(row["last_utc"], f"series:{symbol}:{timeframe}:last")
    if first >= last or iso(first) != row["first_utc"] or iso(last) != row["last_utc"]:
        raise VerificationError(f"series_descriptor_time_invalid:{symbol}:{timeframe}")
    return row


def load_bound_source_m15() -> dict[str, list[dict[str, Any]]]:
    window_paths = (
        "manifests/january_2026.json",
        "manifests/april_2026.json",
        "manifests/may_2026.json",
    )
    authorities: list[dict[str, Mapping[str, Any]]] = []
    binding_fields = (
        "symbol", "mapped_symbol", "timeframe", "lane_relpath", "sha256",
        "row_count", "first_utc", "last_utc", "time_column_basis",
        "broker_clock_rule", "clock_conversion", "source_snapshot_name",
    )
    source_manifest_keys = {
        "bar_source_count", "bar_sources", "bar_symbol_count", "broker_live_authority",
        "broker_mutation_enabled", "campaign_sealed", "clock", "economic_outcomes_read",
        "evidence_class", "lane_root_repo_relpath", "manifest_root_sha256",
        "march_source_only_disclosure", "path_binding", "schema", "status", "surface",
        "tick_gap_count", "tick_gaps", "tick_sources", "tick_symbol_count", "window",
        "window_id",
    }
    expected_disclosures = {
        "january_2026": None,
        "april_2026": (
            "April static-bar lookback mechanically includes March source rows; no March pack, "
            "candidate outcome, ledger, result, or economics is read or emitted."
        ),
        "may_2026": None,
    }
    expected_window_ids = {
        "manifests/january_2026.json": "january_2026",
        "manifests/april_2026.json": "april_2026",
        "manifests/may_2026.json": "may_2026",
    }
    for relative in window_paths:
        path = contained_regular_file(EXPECTED_SOURCE_ROOT, relative, label=f"source_manifest:{relative}")
        require_file(path, EXPECTED_SOURCE_MANIFEST_SHA256[relative])
        manifest = strict_json_loads(path.read_bytes(), label=f"source_manifest:{relative}")
        manifest = _exact_keys(
            manifest, source_manifest_keys, label=f"source_manifest:{relative}",
            reason="source_manifest_schema_invalid",
        )
        if manifest["schema"] != "gtos.lane.rematerialization.source_manifest.v1" or manifest["status"] != "LANE_TRUE_UTC_SOURCE_AUTHORITY_VALID":
            raise VerificationError(f"source_manifest_identity_invalid:{relative}")
        if manifest["window_id"] != expected_window_ids[relative]:
            raise VerificationError(f"source_manifest_window_identity_invalid:{relative}")
        for flag in ("economic_outcomes_read", "broker_live_authority", "broker_mutation_enabled"):
            if manifest.get(flag) is not False:
                raise VerificationError(f"source_manifest_boundary_invalid:{relative}:{flag}")
        if manifest["march_source_only_disclosure"] != expected_disclosures[manifest["window_id"]]:
            raise VerificationError(f"source_manifest_march_disclosure_invalid:{relative}")
        rows = manifest.get("bar_sources")
        if not isinstance(rows, list):
            raise VerificationError(f"source_manifest_bar_sources_invalid:{relative}")
        entries: dict[str, Mapping[str, Any]] = {}
        for number, entry in enumerate(rows):
            if not isinstance(entry, Mapping) or entry.get("timeframe") != "M15":
                continue
            symbol = entry.get("symbol")
            if symbol not in EXPECTED_SYMBOLS or symbol in entries:
                raise VerificationError(f"source_m15_symbol_invalid:{relative}:{number}:{symbol}")
            if entry.get("mapped_symbol") != symbol or entry.get("time_column_basis") != "true_utc":
                raise VerificationError(f"source_m15_identity_invalid:{relative}:{symbol}")
            entries[str(symbol)] = entry
        if set(entries) != set(EXPECTED_SYMBOLS):
            raise VerificationError(f"source_m15_symbol_domain_mismatch:{relative}")
        authorities.append(entries)
    baseline = authorities[0]
    for entries in authorities[1:]:
        for symbol in EXPECTED_SYMBOLS:
            if {key: baseline[symbol].get(key) for key in binding_fields} != {
                key: entries[symbol].get(key) for key in binding_fields
            }:
                raise VerificationError(f"cross_window_m15_authority_mismatch:{symbol}")

    output: dict[str, list[dict[str, Any]]] = {}
    for symbol in EXPECTED_SYMBOLS:
        entry = baseline[symbol]
        relative = normalized_relative_path(entry.get("lane_relpath"), label=f"source_m15:{symbol}")
        path = contained_regular_file(EXPECTED_SOURCE_ROOT, relative, label=f"source_m15:{symbol}")
        expected_sha256 = entry.get("sha256")
        if not _is_sha256(expected_sha256):
            raise VerificationError(f"source_m15_sha256_invalid:{symbol}")
        require_file(path, expected_sha256)
        expected_rows = _strict_int(entry.get("row_count"), label=f"source_m15:{symbol}", reason="source_m15_row_count_type_invalid")
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != ("time", "open", "high", "low", "close", "volume"):
                raise VerificationError(f"source_m15_schema_invalid:{symbol}")
            for line_number, raw in enumerate(reader, 2):
                try:
                    timestamp = utc(raw["time"], f"source_m15:{symbol}:{line_number}")
                    row = {
                        "time": iso(timestamp), "time_utc": iso(timestamp), "symbol": symbol,
                        "open": float(raw["open"]), "high": float(raw["high"]),
                        "low": float(raw["low"]), "close": float(raw["close"]),
                        "volume": float(raw["volume"]),
                    }
                except (TypeError, ValueError) as exc:
                    raise VerificationError(f"source_m15_numeric_invalid:{symbol}:{line_number}") from exc
                validate_series_row(row, symbol=symbol, minutes=15, label=f"source_m15:{symbol}:{line_number}")
                rows.append(row)
        if len(rows) != expected_rows:
            raise VerificationError(f"source_m15_row_count_mismatch:{symbol}")
        if rows[0]["time_utc"] != entry.get("first_utc") or rows[-1]["time_utc"] != entry.get("last_utc"):
            raise VerificationError(f"source_m15_coverage_mismatch:{symbol}")
        output[symbol] = rows
    return output


def expected_slice_metadata(
    rows: Sequence[Mapping[str, Any]], bounds: tuple[int, int], *, prefix: str, minutes: int
) -> dict[str, Any]:
    start, stop = bounds
    return {
        f"{prefix}_start": start,
        f"{prefix}_stop": stop,
        f"{prefix}_count": stop - start,
        "first_open_utc": rows[start]["time_utc"],
        "last_open_utc": rows[stop - 1]["time_utc"],
        "last_close_utc": iso(utc(rows[stop - 1]["time_utc"], f"{prefix}.last") + timedelta(minutes=minutes)),
    }


def verify_packet(
    packet: Path,
    *,
    full_generator: bool = True,
    expected_manifest_sha256: str,
    expected_payload_root_sha256: str,
    expected_tested_source_commit: str,
    _expectations: _PacketExpectations = _PRODUCTION_EXPECTATIONS,
    _source_m15_loader: Any = None,
    _domain_loader: Any = None,
    _authority_git_reader: Any = _git_show_bytes,
) -> dict[str, Any]:
    if full_generator and _expectations is not _PRODUCTION_EXPECTATIONS:
        raise VerificationError("full_generator_requires_production_expectations")
    if not _is_sha256(expected_manifest_sha256) or not _is_sha256(expected_payload_root_sha256):
        raise VerificationError("expected_trust_anchor_invalid")
    if len(expected_tested_source_commit) != 40 or any(character not in "009abcdef" for character in expected_tested_source_commit):
        raise VerificationError("expected_tested_source_commit_invalid")
    files, directories = packet_inventory(packet)
    manifest_path = contained_regular_file(packet, "PACKET_MANIFEST.json", label="packet_manifest")
    if file_hash(manifest_path) != expected_manifest_sha256:
        raise VerificationError("packet_manifest_sha256_mismatch")
    manifest = strict_json_loads(manifest_path.read_bytes(), label="packet_manifest")
    payload_files, _repo, authority_controls = validate_manifest(
        manifest, expected_payload_root_sha256=expected_payload_root_sha256,
        expected_tested_source_commit=expected_tested_source_commit,
        _expectations=_expectations, _authority_git_reader=_authority_git_reader,
    )
    payload = {row["path"]: row for row in payload_files}
    require_exact_packet_inventory(files, {"PACKET_MANIFEST.json", *payload})
    if directories != {".", "series", "states"}:
        raise VerificationError(f"packet_directory_inventory_mismatch:{sorted(directories)}")
    observed_descriptors: list[dict[str, Any]] = []
    for relative, binding in sorted(payload.items()):
        target = contained_regular_file(packet, relative, label=f"payload:{relative}")
        require_file(target, binding["sha256"], binding["bytes"])
        observed_descriptors.append({"path": relative, "bytes": target.stat().st_size, "sha256": file_hash(target)})
    root = canonical_hash({"schema": "gtos.p1-upstream-packet-payload.v1", "files": observed_descriptors})
    if root != expected_payload_root_sha256 or root != manifest["packet_payload_root_sha256"]:
        raise VerificationError("packet_payload_root_mismatch")
    if packet.name != f"p1-source-packet-sha256-{root}":
        raise VerificationError("packet_directory_content_address_mismatch")

    symbols = _expectations.symbols
    series_manifest = manifest["series"]
    if not isinstance(series_manifest, Mapping) or set(series_manifest) != set(symbols):
        raise VerificationError("packet_symbol_domain_invalid")
    series: dict[str, dict[str, list[dict[str, Any]]]] = {}
    closes_by_symbol: dict[str, dict[str, list[datetime]]] = {}
    partial_h1_keys: set[tuple[str, datetime]] = set()
    for symbol in symbols:
        timeframes = _exact_keys(
            series_manifest[symbol], {"M15", "H1"}, label=f"series:{symbol}",
            reason="series_timeframe_schema_invalid",
        )
        rows_by_timeframe: dict[str, list[dict[str, Any]]] = {}
        timestamps_by_timeframe: dict[str, list[datetime]] = {}
        for timeframe, minutes in (("M15", 15), ("H1", 60)):
            descriptor = validate_series_descriptor(
                timeframes[timeframe], symbol=symbol, timeframe=timeframe, payload=payload
            )
            target = contained_regular_file(packet, descriptor["path"], label=f"series:{symbol}:{timeframe}")
            rows = jsonl_gzip(target)
            if len(rows) != descriptor["row_count"]:
                raise VerificationError(f"series_row_count_mismatch:{symbol}:{timeframe}")
            timestamps = [
                validate_series_row(row, symbol=symbol, minutes=minutes, label=f"{symbol}:{timeframe}:{number}")
                for number, row in enumerate(rows, 1)
            ]
            if timestamps != sorted(timestamps) or len(timestamps) != len(set(timestamps)):
                raise VerificationError(f"series_time_order_or_uniqueness_invalid:{symbol}:{timeframe}")
            if any(
                (later - earlier).total_seconds() <= 0
                or int((later - earlier).total_seconds()) % (minutes * 60)
                for earlier, later in zip(timestamps, timestamps[1:])
            ):
                raise VerificationError(f"series_gap_grid_invalid:{symbol}:{timeframe}")
            if rows[0]["time_utc"] != descriptor["first_utc"] or rows[-1]["time_utc"] != descriptor["last_utc"]:
                raise VerificationError(f"series_descriptor_coverage_mismatch:{symbol}:{timeframe}")
            rows_by_timeframe[timeframe] = rows
            timestamps_by_timeframe[timeframe] = timestamps
        buckets = Counter(timestamp.replace(minute=0) for timestamp in timestamps_by_timeframe["M15"])
        partial_h1_keys.update((symbol, bucket) for bucket, count in buckets.items() if count != 4)
        derived_h1 = independently_aggregate_h1(rows_by_timeframe["M15"], symbol)
        h1_path = contained_regular_file(packet, timeframes["H1"]["path"], label=f"series:{symbol}:H1:bytes")
        if derived_h1 != rows_by_timeframe["H1"]:
            raise VerificationError(f"h1_aggregation_mismatch:{symbol}")
        if canonical_jsonl_bytes(derived_h1) != gzip.decompress(h1_path.read_bytes()):
            raise VerificationError(f"h1_byte_derivation_mismatch:{symbol}")
        if deterministic_jsonl_gzip_bytes(derived_h1) != h1_path.read_bytes():
            raise VerificationError(f"h1_gzip_byte_derivation_mismatch:{symbol}")
        series[symbol] = rows_by_timeframe
        closes_by_symbol[symbol] = {
            "M15": [timestamp + timedelta(minutes=15) for timestamp in timestamps_by_timeframe["M15"]],
            "H1": [timestamp + timedelta(minutes=60) for timestamp in timestamps_by_timeframe["H1"]],
        }

    source_m15 = (_source_m15_loader or load_bound_source_m15)()
    if set(source_m15) != set(symbols):
        raise VerificationError("source_m15_symbol_domain_mismatch")
    for symbol in symbols:
        if source_m15[symbol] != series[symbol]["M15"]:
            raise VerificationError(f"packet_m15_source_mismatch:{symbol}")
        m15_path = contained_regular_file(packet, f"series/{symbol}.m15.jsonl.gz", label=f"source_m15_bytes:{symbol}")
        if deterministic_jsonl_gzip_bytes(source_m15[symbol]) != m15_path.read_bytes():
            raise VerificationError(f"packet_m15_source_byte_mismatch:{symbol}")
    if len(partial_h1_keys) != _expectations.partial_h1_buckets:
        raise VerificationError(f"partial_h1_denominator_mismatch:{len(partial_h1_keys)}")
    coverage = strict_json_loads(
        contained_regular_file(packet, "SOURCE_COVERAGE.json", label="source_coverage").read_bytes(),
        label="source_coverage",
    )
    if coverage != manifest["coverage"]:
        raise VerificationError("source_coverage_manifest_mismatch")

    states = jsonl_gzip(contained_regular_file(packet, "states/predecision_market_state.jsonl.gz", label="states"))
    states_by_id: dict[str, dict[str, Any]] = {}
    for number, raw_state in enumerate(states, 1):
        row = validate_state_schema(raw_state, label=f"state:{number}")
        if not _is_sha256(row["state_sha256"]) or not _is_sha256(row["h1_breaker_blocks_sha256"]):
            raise VerificationError(f"state_sha256_shape_invalid:{number}")
        material = dict(row)
        state_hash = material.pop("state_sha256")
        if state_hash != canonical_hash(material):
            raise VerificationError(f"state_hash_mismatch:{row['state_id']}")
        if row["h1_breaker_blocks_sha256"] != canonical_hash(row["h1_breaker_blocks"]):
            raise VerificationError(f"state_breaker_hash_mismatch:{row['state_id']}")
        if row["state_id"] in states_by_id:
            raise VerificationError(f"duplicate_state_id:{row['state_id']}")
        states_by_id[str(row["state_id"])] = dict(row)
    if len(states_by_id) != _expectations.state_count:
        raise VerificationError(f"state_denominator_mismatch:{len(states_by_id)}")

    index_rows = jsonl_gzip(contained_regular_file(packet, "identity_to_slice.jsonl.gz", label="identity_index"))
    domain = (_domain_loader or commissioned_domain)()
    index_by_identity: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    by_decision: dict[datetime, list[tuple[tuple[str, str, str, str], dict[str, Any]]]] = defaultdict(list)
    source_multiplicity: Counter[str] = Counter()
    for number, raw_index in enumerate(index_rows, 1):
        row = validate_identity_schema(raw_index, label=f"identity:{number}")
        if not _is_sha256(row["identity_slice_sha256"]):
            raise VerificationError(f"identity_sha256_shape_invalid:{number}")
        material = dict(row)
        row_hash = material.pop("identity_slice_sha256")
        if row_hash != canonical_hash(material):
            raise VerificationError(f"identity_slice_hash_mismatch:{number}")
        identity = row["identity"]
        key = (identity["candidate_id"], identity["symbol"], identity["side"], identity["decision_time_utc"])
        if key in index_by_identity or key not in domain:
            raise VerificationError(f"duplicate_or_uncommissioned_packet_identity:{key}")
        if row["symbol"] != key[1] or row["decision_time_utc"] != key[3]:
            raise VerificationError(f"identity_duplicate_field_mismatch:{key}")
        if key[1] not in symbols or key[2] not in {"LONG", "SHORT"}:
            raise VerificationError(f"identity_symbol_or_side_invalid:{key}")
        decision = utc(key[3], f"identity:{number}:decision")
        if iso(decision) != key[3]:
            raise VerificationError(f"identity_timestamp_not_canonical:{key}")
        expected_state_id = "state_" + canonical_hash({"symbol": key[1], "decision_time_utc": key[3]})[:24]
        if row["state_id"] != expected_state_id:
            raise VerificationError(f"identity_state_id_mismatch:{key}")
        if row["m15_series_path"] != f"series/{key[1]}.m15.jsonl.gz" or row["h1_series_path"] != f"series/{key[1]}.h1.jsonl.gz":
            raise VerificationError(f"identity_series_path_mismatch:{key}")
        for field in ("window", "kill_zone", "origin_family", "framework", "route_family"):
            if row[field] != domain[key][field]:
                raise VerificationError(f"identity_control_mismatch:{key}:{field}")
        index_by_identity[key] = dict(row)
        by_decision[decision].append((key, dict(row)))
        source_multiplicity[key[1]] += 1
    if set(index_by_identity) != set(domain) or len(index_by_identity) != _expectations.total:
        raise VerificationError(f"identity_domain_mismatch:{len(index_by_identity)}:{len(domain)}")
    if dict(sorted(source_multiplicity.items())) != manifest["coverage"]["source_multiplicity_by_symbol"]:
        raise VerificationError("source_multiplicity_mismatch")

    referenced_states: set[str] = set()
    referenced_partial_h1_keys: set[tuple[str, datetime]] = set()
    structural_slices: dict[tuple[datetime, str], tuple[tuple[int, int], tuple[int, int]]] = {}
    postdecision_reads = 0
    for decision, decision_rows in sorted(by_decision.items()):
        rows_by_symbol: dict[str, list[tuple[tuple[str, str, str, str], dict[str, Any]]]] = defaultdict(list)
        for key, row in decision_rows:
            rows_by_symbol[key[1]].append((key, row))
        for symbol, targets in rows_by_symbol.items():
            m15_slice = independent_closed_slice_from_closes(
                closes_by_symbol[symbol]["M15"], decision, _expectations.m15_lookback
            )
            h1_slice = independent_closed_slice_from_closes(
                closes_by_symbol[symbol]["H1"], decision, _expectations.h1_lookback
            )
            if m15_slice[1] - m15_slice[0] < _expectations.minimum_closed_m15 or h1_slice[1] - h1_slice[0] < _expectations.h1_lookback:
                raise VerificationError(f"insufficient_warmup:{symbol}:{iso(decision)}")
            structural_slices[(decision, symbol)] = (m15_slice, h1_slice)
            state_ids = {row["state_id"] for _, row in targets}
            if len(state_ids) != 1:
                raise VerificationError(f"mixed_state_id:{symbol}:{iso(decision)}")
            state_id = next(iter(state_ids))
            referenced_states.add(state_id)
            packet_state = states_by_id.get(state_id)
            if packet_state is None or packet_state["symbol"] != symbol or packet_state["decision_time_utc"] != iso(decision):
                raise VerificationError(f"referenced_state_identity_mismatch:{state_id}")
            expected_m15 = expected_slice_metadata(series[symbol]["M15"], m15_slice, prefix="m15", minutes=15)
            expected_h1 = expected_slice_metadata(series[symbol]["H1"], h1_slice, prefix="h1", minutes=60)
            if packet_state["m15_slice"] != expected_m15 or packet_state["h1_slice"] != expected_h1:
                raise VerificationError(f"state_slice_metadata_mismatch:{state_id}")
            for key, row in targets:
                if row["m15_slice"] != list(m15_slice) or row["h1_slice"] != list(h1_slice):
                    raise VerificationError(f"identity_slice_index_mismatch:{key}")
            referenced_partial_h1_keys.update(
                key for item in series[symbol]["H1"][h1_slice[0]:h1_slice[1]]
                if (key := (symbol, utc(item["time_utc"], f"referenced_h1:{symbol}"))) in partial_h1_keys
            )
            if closes_by_symbol[symbol]["M15"][m15_slice[1] - 1] > decision or closes_by_symbol[symbol]["H1"][h1_slice[1] - 1] > decision:
                postdecision_reads += 1
    if referenced_states != set(states_by_id):
        raise VerificationError(f"state_reference_partition_mismatch:{len(referenced_states)}:{len(states_by_id)}")
    if postdecision_reads:
        raise VerificationError(f"postdecision_state_read:{postdecision_reads}")

    state_recompute_mismatches = 0
    independent_atr_matches = 0
    independent_breaker_matches = 0
    generator_matches = 0
    if full_generator:
        require_file(REPO_ROOT / _expectations.generator_path, _expectations.generator_sha256)
        require_file(REPO_ROOT / _expectations.market_state_path, _expectations.market_state_sha256)
        sys.dont_write_bytecode = True
        install_runtime_audit_guard()
        from src.components.broader_origin_generators import generate_live_broader_origin_candidates
        from src.components.market_state import compute_market_state

        config = _merge_generation_config()
        min_bars = int(config["data"]["swing_detection_min_bars"]["H1"])
        dead_zone_divisor = int(config["market_state"]["v2_dead_zone_divisor"])
        for decision_number, (decision, decision_rows) in enumerate(sorted(by_decision.items()), 1):
            raw_by_symbol: dict[str, dict[str, Any]] = {}
            for symbol in symbols:
                m15_slice = independent_closed_slice_from_closes(closes_by_symbol[symbol]["M15"], decision, _expectations.m15_lookback)
                h1_slice = independent_closed_slice_from_closes(closes_by_symbol[symbol]["H1"], decision, _expectations.h1_lookback)
                raw_by_symbol[symbol] = _raw(
                    symbol, decision, series[symbol]["M15"][m15_slice[0]:m15_slice[1]],
                    series[symbol]["H1"][h1_slice[0]:h1_slice[1]],
                )
            rows_by_symbol: dict[str, list[tuple[tuple[str, str, str, str], dict[str, Any]]]] = defaultdict(list)
            for key, row in decision_rows:
                rows_by_symbol[key[1]].append((key, row))
            cross_asset = {"raw_data_by_symbol": raw_by_symbol}
            for symbol, targets in sorted(rows_by_symbol.items()):
                kill_zones = {row["kill_zone"] for _, row in targets}
                if len(kill_zones) != 1:
                    raise VerificationError(f"mixed_kill_zones:{symbol}:{iso(decision)}")
                symbol_config = _symbol_config(config, symbol)
                mso = compute_market_state(raw_by_symbol[symbol], symbol_config)
                generated = generate_live_broader_origin_candidates(
                    raw_by_symbol[symbol], mso, symbol_config, symbol, next(iter(kill_zones)),
                    cross_asset_raw_data=cross_asset, now_utc=decision,
                )
                generated_keys = Counter((
                    str(candidate.get("candidate_id")), str(candidate.get("symbol")),
                    str(candidate.get("side")).upper(), str(candidate.get("origin_family")),
                    str(candidate.get("framework")), str(candidate.get("kill_zone")),
                ) for candidate in generated)
                m15_slice, h1_slice = structural_slices[(decision, symbol)]
                packet_state = states_by_id[targets[0][1]["state_id"]]
                independent_atr_value = independent_atr(raw_by_symbol[symbol]["candles"]["M15"])
                independent_breakers = independent_breaker_projection(
                    raw_by_symbol[symbol]["candles"]["H1"], min_bars=min_bars,
                    dead_zone_divisor=dead_zone_divisor,
                )
                if packet_state["m15_atr_14"] == independent_atr_value == mso.timeframes["M15"].atr_14:
                    independent_atr_matches += 1
                else:
                    state_recompute_mismatches += 1
                if packet_state["h1_breaker_blocks"] == independent_breakers == _breaker_projection(mso):
                    independent_breaker_matches += 1
                else:
                    state_recompute_mismatches += 1
                for key, row in targets:
                    expected = (key[0], key[1], key[2], row["origin_family"], row["framework"], row["kill_zone"])
                    if generated_keys[expected] != 1:
                        raise VerificationError(f"generator_identity_mismatch:{key}:matches={generated_keys[expected]}")
                    generator_matches += 1
            if decision_number % 500 == 0:
                print(json.dumps({"verification_progress_decision_groups": decision_number, "generator_matches": generator_matches, "referenced_states": len(referenced_states)}, sort_keys=True), file=sys.stderr, flush=True)
    if state_recompute_mismatches:
        raise VerificationError(f"state_reconstruction_failed:{state_recompute_mismatches}")
    if full_generator and (
        generator_matches != _expectations.total
        or independent_atr_matches != len(states_by_id)
        or independent_breaker_matches != len(states_by_id)
        or len(referenced_partial_h1_keys) != _expectations.referenced_partial_h1_buckets
    ):
        raise VerificationError(
            f"full_recompute_count_invalid:generator={generator_matches}:atr={independent_atr_matches}:"
            f"breakers={independent_breaker_matches}:partial_h1={len(referenced_partial_h1_keys)}"
        )
    return envelope({
        "schema": "gtos.p1-upstream-packet-independent-verification.v2",
        "status": "PASS" if full_generator else "STRUCTURAL_ONLY_NOT_TERMINAL",
        "packet_path": packet.as_posix(), "packet_manifest_sha256": file_hash(manifest_path),
        "packet_payload_root_sha256": root, "tested_source_commit": expected_tested_source_commit,
        "payload_file_count": len(payload_files), "symbols": len(series),
        "m15_source_rows": sum(len(rows) for rows in source_m15.values()),
        "partial_h1_buckets_preserved": len(partial_h1_keys),
        "referenced_partial_h1_buckets": len(referenced_partial_h1_keys),
        "h1_aggregation_mismatches": 0, "identity_rows": len(index_by_identity),
        "unique_composite_identities": len(index_by_identity),
        "commissioned_domain_matches": len(index_by_identity), "state_rows": len(states_by_id),
        "independent_atr_matches": independent_atr_matches if full_generator else None,
        "independent_breaker_matches": independent_breaker_matches if full_generator else None,
        "state_recompute_mismatches": state_recompute_mismatches,
        "postdecision_reads": postdecision_reads,
        "generator_matches": generator_matches if full_generator else None,
        "full_generator_verification": full_generator, **authority_controls,
    })


def _args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--skip-full-generator", action="store_true")
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--expected-payload-root-sha256", required=True)
    parser.add_argument("--expected-tested-source-commit", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _args(argv)
    result = verify_packet(
        args.packet,
        full_generator=not args.skip_full_generator,
        expected_manifest_sha256=args.expected_manifest_sha256,
        expected_payload_root_sha256=args.expected_payload_root_sha256,
        expected_tested_source_commit=args.expected_tested_source_commit,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
