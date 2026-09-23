"""V4U ordered-path hydration planning and local oracle execution.

This module is read-only with respect to market/broker sources. It streams the
Wave4R ordered-path gap ledger, joins candidate microscope rows for as-of
geometry, indexes local M1/tick evidence, and only uses post-asof path data for
replay labels.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from src.research_infra.wave4r_replay_microstructure import (
    infer_ordered_path_from_local_files,
    parse_utc,
)


GZIP_MAGIC = b"\x1f\x8b"
MISSING_ORDERED_PATH_STATUS = "ordered_touch_times_missing"
DATE_RE = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})")
YEAR_RE = re.compile(r"^(?P<year>20\d{2})$")
TIMEFRAME_RE = re.compile(r"^(?P<symbol>.+)_(?P<timeframe>M1|M5|M15|M30|H1|H4|D1)\.csv$", re.I)
MT5_BINARY_CACHE_LABELS = {
    "mt5_hcc_m1_packed_year_cache_candidate",
    "mt5_hc_m1_cache_candidate",
    "mt5_tick_binary_cache_candidate",
}
OWNER_AUTHORIZED_PATH_OVERRIDE_SCOPE = (
    "ordered_price_path_only_not_broker_order_lifecycle_truth"
)
VALID_MT5_EXPORT_SOURCE_LABEL = "ftmo_owner_authorized_m1_ltf_path_override"
VALID_MT5_TICK_EXPORT_SOURCE_LABEL = "ftmo_owner_authorized_tick_ltf_path_override"

SESSION_WINDOWS_UTC = {
    "TOKYO_BROAD": ("00:00", "07:00"),
    "LONDON_BROAD": ("07:00", "13:00"),
    "NY_BROAD": ("13:00", "18:00"),
    "OFF_KZ_BROAD": ("18:00", "24:00"),
}

SAFE_DECISION_KEYS = {
    "candidate_id",
    "path_row_id",
    "symbol",
    "asof_utc",
    "session",
    "session_source",
    "framework",
    "side",
    "entry_reference",
    "stop_or_invalidation",
    "configured_target_r",
    "source_status",
    "source_completeness",
    "source_path",
    "source_sha256",
    "packet_hash",
    "selector_action",
    "scheduler_action",
    "same_symbol_action",
}

FORBIDDEN_DECISION_PATH_KEYS = {
    "target_first_touch_utc",
    "stop_first_touch_utc",
    "entry_first_touch_utc",
    "exit_time_utc",
    "mfe_r",
    "mae_r",
    "terminal_outcome",
    "current_v4_proxy_r",
    "promoted_router_total_replay_r",
    "live_current_total_r",
    "be_after_trigger_total_replay_r",
    "source_gaps",
}


@dataclass(frozen=True)
class IndexedSourceFile:
    path: str
    source_kind: str
    source_label: str
    eligible_for_ordered_path_truth: bool
    symbol: str | None
    date: str | None
    date_min: str | None
    date_max: str | None
    timeframe: str | None
    row_count: int | None
    row_count_status: str
    sha256: str | None
    first_time_utc: str | None
    last_time_utc: str | None
    corrupt_quarantine: bool
    source_provenance_status: str
    source_broker: str | None
    source_role: str | None
    source_truth_scope: str | None
    replaces_missing_frozen_path_source: bool | None
    not_redacted_account_native: bool | None
    source_server: str | None
    source_account_login: str | None
    source_manifest_path: str | None
    source_manifest_sha256: str | None
    handoff_requirement_id: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceIndex:
    files_by_key: Mapping[tuple[str, str], tuple[IndexedSourceFile, ...]]
    rejected_by_key: Mapping[tuple[str, str], tuple[IndexedSourceFile, ...]]
    rejected_by_symbol: Mapping[str, tuple[IndexedSourceFile, ...]]
    inventory_rows: tuple[IndexedSourceFile, ...]
    summary: Mapping[str, Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    opener = gzip.open if _is_gzip(path) else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if isinstance(row, dict):
                yield row


def _is_gzip(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(2) == GZIP_MAGIC
    except OSError:
        return False


def _json_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def date_from_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    match = DATE_RE.search(str(value))
    return match.group("date") if match else None


def derive_session_from_asof(asof_utc: str | None) -> str:
    parsed = parse_utc(asof_utc)
    if parsed is None:
        return "SESSION_UNKNOWN_CLOCK_GAP"
    hour = parsed.hour
    if 0 <= hour < 7:
        return "TOKYO_BROAD"
    if 7 <= hour < 13:
        return "LONDON_BROAD"
    if 13 <= hour < 18:
        return "NY_BROAD"
    return "OFF_KZ_BROAD"


def session_window_bounds(asof_utc: str, session: str | None) -> tuple[str, str, str]:
    asof = parse_utc(asof_utc)
    if asof is None:
        return asof_utc, asof_utc, "missing_asof_utc"
    session_key = str(session or "").strip().upper() or derive_session_from_asof(asof_utc)
    if session_key not in SESSION_WINDOWS_UTC:
        session_key = derive_session_from_asof(asof_utc)
    start_hhmm, end_hhmm = SESSION_WINDOWS_UTC.get(session_key, ("00:00", "24:00"))
    start = _combine_hhmm(asof, start_hhmm)
    end = _combine_hhmm(asof, end_hhmm)
    if end <= start:
        end += timedelta(days=1)
    if asof >= end:
        end = datetime.combine(asof.date(), time.max, tzinfo=timezone.utc).replace(microsecond=0)
    request_start = asof
    request_end = end if end > asof else asof + timedelta(minutes=1)
    return request_start.isoformat(), request_end.isoformat(), "session_clock_derived_from_broad_replay_bucket"


def _combine_hhmm(anchor: datetime, hhmm: str) -> datetime:
    if hhmm == "24:00":
        return datetime.combine(anchor.date(), time.min, tzinfo=timezone.utc) + timedelta(days=1)
    hour, minute = [int(part) for part in hhmm.split(":", 1)]
    return datetime.combine(anchor.date(), time(hour, minute), tzinfo=timezone.utc)


def index_source_roots(source_roots: Iterable[Path]) -> SourceIndex:
    eligible_by_key: dict[tuple[str, str], list[IndexedSourceFile]] = defaultdict(list)
    rejected_by_key: dict[tuple[str, str], list[IndexedSourceFile]] = defaultdict(list)
    rejected_by_symbol: dict[str, list[IndexedSourceFile]] = defaultdict(list)
    inventory: list[IndexedSourceFile] = []
    source_kind_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    provenance_status_counts: Counter[str] = Counter()
    eligible_file_count = 0
    corrupt_count = 0

    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.name.startswith("."):
                continue
            if path.suffix.lower() not in {".csv", ".jsonl", ".parquet", ".hcc", ".hc", ".tkc"} and path.name.lower() != "ticks.dat":
                continue
            source = classify_source_file(path)
            if source is None:
                continue
            inventory.append(source)
            source_kind_counts[source.source_kind] += 1
            label_counts[source.source_label] += 1
            provenance_status_counts[source.source_provenance_status] += 1
            if source.corrupt_quarantine:
                corrupt_count += 1
            if source.eligible_for_ordered_path_truth:
                eligible_file_count += 1
            date_keys = list(_source_dates_for_index(source))
            if (
                not source.eligible_for_ordered_path_truth
                and source.symbol
                and source.source_label in MT5_BINARY_CACHE_LABELS
            ):
                rejected_by_symbol[canonical_symbol(source.symbol)].append(source)
            for date_key in date_keys:
                key = (canonical_symbol(source.symbol), date_key)
                if source.eligible_for_ordered_path_truth:
                    eligible_by_key[key].append(source)
                else:
                    rejected_by_key[key].append(source)

    summary = {
        "source_roots_checked": [str(root) for root in source_roots],
        "inventory_file_count": len(inventory),
        "eligible_m1_tick_file_count": eligible_file_count,
        "ineligible_or_proxy_file_count": len(inventory) - eligible_file_count,
        "corrupt_quarantine_file_count": corrupt_count,
        "source_kind_counts": dict(sorted(source_kind_counts.items())),
        "source_label_counts": dict(sorted(label_counts.items())),
        "source_provenance_status_counts": dict(sorted(provenance_status_counts.items())),
    }
    return SourceIndex(
        files_by_key={key: tuple(value) for key, value in eligible_by_key.items()},
        rejected_by_key={key: tuple(value) for key, value in rejected_by_key.items()},
        rejected_by_symbol={key: tuple(value) for key, value in rejected_by_symbol.items()},
        inventory_rows=tuple(inventory),
        summary=summary,
    )


def classify_source_file(path: Path) -> IndexedSourceFile | None:
    source_kind, label, eligible, timeframe = _source_kind_and_label(path)
    if source_kind is None:
        return None
    provenance = _default_source_provenance()
    if _is_mt5_research_export_path(path):
        if timeframe == "M1":
            provenance = _mt5_export_source_provenance(
                path=path,
                expected_schema="mt5_research_ohlcv_export_v1",
                expected_timeframe="M1",
                expected_export_tool="scripts/export_mt5_research_ohlcv.py",
            )
            source_kind = "mt5_research_export_m1"
            if provenance["source_provenance_status"] == "valid_owner_authorized_path_override":
                label = VALID_MT5_EXPORT_SOURCE_LABEL
                eligible = True
            else:
                label = "mt5_research_export_m1_missing_or_invalid_path_override_provenance"
                eligible = False
        elif source_kind == "tick":
            provenance = _mt5_export_source_provenance(
                path=path,
                expected_schema="mt5_research_tick_export_v1",
                expected_timeframe="TICK",
                expected_export_tool="scripts/export_mt5_research_ticks.py",
            )
            source_kind = "mt5_research_export_tick"
            if provenance["source_provenance_status"] == "valid_owner_authorized_path_override":
                label = VALID_MT5_TICK_EXPORT_SOURCE_LABEL
                eligible = True
            else:
                label = "mt5_research_export_tick_missing_or_invalid_path_override_provenance"
                eligible = False
    symbol = _symbol_from_path(path)
    date = date_from_value(path.name)
    date_min, date_max = _cache_date_bounds(path, source_kind)
    corrupt = "_corrupt_quarantine" in {part.lower() for part in path.parts}
    if corrupt:
        row_count, row_count_status, first_time, last_time = (
            None,
            "corrupt_quarantine_skipped_without_parse",
            None,
            None,
        )
    else:
        row_count, row_count_status, first_time, last_time = _summarize_source_file(path, source_kind)
    if date is None:
        date = date_from_value(first_time)
    date_min = date_min or date_from_value(first_time) or date
    date_max = date_max or date_from_value(last_time) or date
    sha_value = _file_sha256(path) if path.exists() else None
    return IndexedSourceFile(
        path=str(path),
        source_kind=source_kind,
        source_label=label,
        eligible_for_ordered_path_truth=eligible,
        symbol=symbol,
        date=date,
        date_min=date_min,
        date_max=date_max,
        timeframe=timeframe,
        row_count=row_count,
        row_count_status=row_count_status,
        sha256=sha_value,
        first_time_utc=first_time,
        last_time_utc=last_time,
        corrupt_quarantine=corrupt,
        source_provenance_status=str(provenance["source_provenance_status"]),
        source_broker=provenance.get("source_broker"),
        source_role=provenance.get("source_role"),
        source_truth_scope=provenance.get("source_truth_scope"),
        replaces_missing_frozen_path_source=provenance.get(
            "replaces_missing_frozen_path_source"
        ),
        not_redacted_account_native=provenance.get("not_redacted_account_native"),
        source_server=provenance.get("source_server"),
        source_account_login=provenance.get("source_account_login"),
        source_manifest_path=provenance.get("source_manifest_path"),
        source_manifest_sha256=provenance.get("source_manifest_sha256"),
        handoff_requirement_id=provenance.get("handoff_requirement_id"),
    )


def _source_kind_and_label(path: Path) -> tuple[str | None, str | None, bool, str | None]:
    parts = {part.lower() for part in path.parts}
    name = path.name
    suffix = path.suffix.lower()
    timeframe_match = TIMEFRAME_RE.match(name)
    timeframe = timeframe_match.group("timeframe").upper() if timeframe_match else None
    corrupt = "_corrupt_quarantine" in parts
    if corrupt:
        if "ticks" in parts:
            return "tick_corrupt_quarantine", "corrupt_quarantine_not_ordered_path_truth", False, timeframe
        if "m1" in parts or timeframe == "M1":
            return "m1_corrupt_quarantine", "corrupt_quarantine_not_ordered_path_truth", False, timeframe
        return "corrupt_quarantine", "corrupt_quarantine_not_ordered_path_truth", False, timeframe
    if suffix == ".hcc" and YEAR_RE.match(path.stem):
        return (
            "mt5_hcc_m1_packed_year_cache",
            "mt5_hcc_m1_packed_year_cache_candidate",
            False,
            "M1_PACKED_YEAR",
        )
    if suffix == ".hc":
        cache_tf = path.stem.upper()
        if cache_tf == "M1":
            return "mt5_hc_m1_cache", "mt5_hc_m1_cache_candidate", False, "M1"
        return (
            "mt5_hc_non_m1_cache",
            "mt5_hc_non_m1_cache_not_ordered_path_truth",
            False,
            cache_tf,
        )
    if name.lower() == "ticks.dat" or suffix == ".tkc":
        return "mt5_tick_binary_cache", "mt5_tick_binary_cache_candidate", False, "TICK_BINARY"
    if "ticks" in parts:
        return "tick", "local_tick_ltf_ordered_path_candidate", True, timeframe
    if "m1" in parts or timeframe == "M1":
        return "m1", "local_m1_ltf_ordered_path_candidate", True, timeframe or "M1"
    if timeframe == "M15" or path.name.upper().endswith("_M15.CSV"):
        return "m15_proxy", "proxy_m15_context_not_ordered_path_truth", False, "M15"
    if "mt5_research_exports" in parts:
        return "mt5_research_export_non_ltf", "mt5_research_export_not_m1_or_tick_truth", False, timeframe
    return None, None, False, timeframe


def _symbol_from_path(path: Path) -> str | None:
    match = TIMEFRAME_RE.match(path.name)
    if match:
        return canonical_symbol(match.group("symbol"))
    if path.suffix.lower() in {".hcc", ".hc"}:
        parts = [part for part in path.parts if part]
        if path.suffix.lower() == ".hcc" and len(parts) >= 2:
            return canonical_symbol(parts[-2])
        if path.suffix.lower() == ".hc" and len(parts) >= 3 and parts[-2].lower() == "cache":
            return canonical_symbol(parts[-3])
    if path.name.lower() == "ticks.dat" and path.parent.name:
        return canonical_symbol(path.parent.name)
    parent = path.parent.name
    if parent and not DATE_RE.fullmatch(parent) and parent.lower() not in {"m1", "ticks", "cache"}:
        return canonical_symbol(parent)
    return None


def _cache_date_bounds(path: Path, source_kind: str) -> tuple[str | None, str | None]:
    if source_kind == "mt5_hcc_m1_packed_year_cache":
        match = YEAR_RE.match(path.stem)
        if match:
            year = match.group("year")
            return f"{year}-01-01", f"{year}-12-31"
    return None, None


def _summarize_source_file(path: Path, source_kind: str) -> tuple[int | None, str, str | None, str | None]:
    suffix = path.suffix.lower()
    if (
        suffix in {".hcc", ".hc", ".tkc"}
        or path.name.lower() == "ticks.dat"
        or (
            source_kind.startswith("mt5_")
            and not source_kind.startswith("mt5_research_export_")
        )
    ):
        return None, "binary_cache_not_parsed_requires_parser_or_readonly_export", None, None
    try:
        if suffix == ".csv":
            return _summarize_csv(path)
        if suffix == ".jsonl":
            return _summarize_jsonl(path)
        if suffix == ".parquet":
            return _summarize_parquet(path)
    except Exception as exc:  # pragma: no cover - defensive metadata path.
        return None, f"metadata_parse_error:{type(exc).__name__}", None, None
    return None, f"unsupported_for_{source_kind}", None, None


def _summarize_csv(path: Path) -> tuple[int, str, str | None, str | None]:
    count = 0
    first_time: str | None = None
    last_time: str | None = None
    with path.open("r", encoding="utf-8", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            count += 1
            ts = _row_time_text(row)
            if ts:
                first_time = first_time or ts
                last_time = ts
    return count, "counted", first_time, last_time


def _summarize_jsonl(path: Path) -> tuple[int, str, str | None, str | None]:
    count = 0
    first_time: str | None = None
    last_time: str | None = None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            count += 1
            row = json.loads(text)
            if isinstance(row, Mapping):
                ts = _row_time_text(row)
                if ts:
                    first_time = first_time or ts
                    last_time = ts
    return count, "counted", first_time, last_time


def _summarize_parquet(path: Path) -> tuple[int | None, str, str | None, str | None]:
    try:
        import pyarrow.parquet as pq  # type: ignore
    except Exception:
        return None, "parquet_reader_unavailable", None, None
    parquet_file = pq.ParquetFile(path)
    return parquet_file.metadata.num_rows, "counted_from_parquet_metadata", None, None


def _row_time_text(row: Mapping[str, Any]) -> str | None:
    for key in ("ts_utc", "time_utc", "time", "timestamp_utc"):
        if row.get(key) not in (None, ""):
            return _normalize_time_text(row.get(key))
    return None


def _normalize_time_text(value: Any) -> str | None:
    parsed = parse_utc(value)
    return parsed.isoformat() if parsed else (str(value) if value not in (None, "") else None)


def _is_mt5_research_export_path(path: Path) -> bool:
    return "mt5_research_exports" in {part.lower() for part in path.parts}


def _default_source_provenance() -> dict[str, Any]:
    return {
        "source_provenance_status": "not_required_for_non_mt5_research_export_path",
        "source_broker": None,
        "source_role": None,
        "source_truth_scope": None,
        "replaces_missing_frozen_path_source": None,
        "not_redacted_account_native": None,
        "source_server": None,
        "source_account_login": None,
        "source_manifest_path": None,
        "source_manifest_sha256": None,
        "handoff_requirement_id": None,
    }


def _mt5_export_source_provenance(
    *,
    path: Path,
    expected_schema: str,
    expected_timeframe: str,
    expected_export_tool: str,
) -> dict[str, Any]:
    payload = _default_source_provenance()
    manifest_path = _mt5_export_manifest_path(path)
    payload["source_manifest_path"] = str(manifest_path)
    if not manifest_path.exists():
        payload["source_provenance_status"] = "invalid_mt5_export_manifest_missing"
        return payload
    payload["source_manifest_sha256"] = _file_sha256(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        payload["source_provenance_status"] = f"invalid_mt5_export_manifest_parse_error:{type(exc).__name__}"
        return payload
    if not isinstance(manifest, Mapping):
        payload["source_provenance_status"] = "invalid_mt5_export_manifest_not_object"
        return payload
    account = manifest.get("account") if isinstance(manifest.get("account"), Mapping) else {}
    provenance = (
        manifest.get("source_provenance")
        if isinstance(manifest.get("source_provenance"), Mapping)
        else {}
    )
    file_entry = _manifest_file_entry(manifest=manifest, path=path)
    payload.update(
        {
            "source_broker": _string_or_none(provenance.get("source_broker")),
            "source_role": _string_or_none(provenance.get("source_role")),
            "source_truth_scope": _string_or_none(provenance.get("source_truth_scope")),
            "replaces_missing_frozen_path_source": bool(
                provenance.get("replaces_missing_frozen_path_source")
            ),
            "not_redacted_account_native": bool(provenance.get("not_redacted_account_native")),
            "source_server": _string_or_none(
                (file_entry or {}).get("source_server") or account.get("server")
            ),
            "source_account_login": _string_or_none(
                (file_entry or {}).get("source_account_login") or account.get("login")
            ),
            "handoff_requirement_id": _string_or_none(
                provenance.get("handoff_requirement_id")
            ),
        }
    )
    failures: list[str] = []
    if manifest.get("schema_version") != expected_schema:
        failures.append("schema_version")
    if payload["source_broker"] != "FTMO":
        failures.append("source_broker=FTMO")
    if payload["source_role"] != "owner_authorized_path_override":
        failures.append("source_role=owner_authorized_path_override")
    if payload["source_truth_scope"] != OWNER_AUTHORIZED_PATH_OVERRIDE_SCOPE:
        failures.append(f"source_truth_scope={OWNER_AUTHORIZED_PATH_OVERRIDE_SCOPE}")
    if payload["replaces_missing_frozen_path_source"] is not True:
        failures.append("replaces_missing_frozen_path_source=true")
    if payload["not_redacted_account_native"] is not True:
        failures.append("not_redacted_account_native=true")
    if provenance.get("broker_lifecycle_truth_satisfied") is not False:
        failures.append("broker_lifecycle_truth_satisfied=false")
    if provenance.get("asof_decision_truth_satisfied") is not False:
        failures.append("asof_decision_truth_satisfied=false")
    if not payload["handoff_requirement_id"]:
        failures.append("handoff_requirement_id")
    elif str(payload["handoff_requirement_id"]) not in str(path):
        failures.append("handoff_requirement_id_path_match")
    if not payload["source_server"]:
        failures.append("source_server")
    if not payload["source_account_login"]:
        failures.append("source_account_login")
    if file_entry is None:
        failures.append("manifest_file_entry")
    else:
        if str(file_entry.get("timeframe") or "").upper() != expected_timeframe:
            failures.append("file_timeframe")
        actual_sha = _file_sha256(path)
        if not file_entry.get("sha256"):
            failures.append("file_sha256")
        elif str(file_entry.get("sha256")) != actual_sha:
            failures.append("file_sha256_match")
        row_count = file_entry.get("row_count")
        if row_count is None:
            failures.append("row_count")
        else:
            try:
                if int(row_count) <= 0:
                    failures.append("row_count_positive")
            except (TypeError, ValueError):
                failures.append("row_count_integer")
        if file_entry.get("export_tool") != expected_export_tool:
            failures.append("export_tool")
    payload["source_provenance_status"] = (
        "valid_owner_authorized_path_override"
        if not failures
        else "invalid_mt5_export_path_override:" + ",".join(sorted(set(failures)))
    )
    return payload


def _mt5_export_manifest_path(path: Path) -> Path:
    for parent in (path.parent, *path.parents):
        candidate = parent / "manifest.json"
        if candidate.exists():
            return candidate
        if parent.name == "mt5_research_exports":
            break
    return path.parent / "manifest.json"


def _manifest_file_entry(*, manifest: Mapping[str, Any], path: Path) -> Mapping[str, Any] | None:
    files = manifest.get("files")
    if not isinstance(files, Mapping):
        return None
    for key, value in files.items():
        if not isinstance(value, Mapping):
            continue
        entry_path = value.get("path")
        if entry_path and Path(str(entry_path)).name == path.name:
            return value
        if str(key).upper() == path.stem.upper():
            return value
    return None


def _string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _source_dates_for_index(source: IndexedSourceFile) -> Iterable[str]:
    if not source.symbol:
        return []
    if source.date:
        return [source.date]
    if not source.date_min or not source.date_max:
        return []
    try:
        start = datetime.fromisoformat(source.date_min).date()
        end = datetime.fromisoformat(source.date_max).date()
    except ValueError:
        return []
    dates: list[str] = []
    cursor = start
    while cursor <= end:
        dates.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return dates


def collect_missing_ordered_rows(ordered_path_ledger: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(ordered_path_ledger):
        status = row.get("ordered_path_source_status") or row.get("source_status")
        if status == MISSING_ORDERED_PATH_STATUS:
            rows.append(dict(row))
    return rows


def load_candidate_lookup(candidate_ledger: Path, candidate_ids: set[str]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(candidate_ledger):
        cid = str(row.get("candidate_id") or "")
        if cid in candidate_ids:
            lookup[cid] = dict(row)
            if len(lookup) == len(candidate_ids):
                break
    return lookup


def build_rolling_hydration_oracle(
    *,
    ordered_path_ledger: Path,
    candidate_ledger: Path,
    source_roots: Iterable[Path],
    scratch_root: Path,
    run_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    generated = utc_now_iso()
    run = run_id or f"v4u_ordered_path_hydration_{generated.replace(':', '').replace('-', '')}"
    scratch_run_root = scratch_root / run
    scratch_run_root.mkdir(parents=True, exist_ok=True)
    scratch_created = True
    scratch_file_count_peak = 0

    source_index = index_source_roots(tuple(source_roots))
    ordered_rows = collect_missing_ordered_rows(ordered_path_ledger)
    candidate_ids = {str(row.get("candidate_id") or "") for row in ordered_rows if row.get("candidate_id")}
    candidate_lookup = load_candidate_lookup(candidate_ledger, candidate_ids)

    output_rows: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    source_label_counts: Counter[str] = Counter()
    cache_label_counts: Counter[str] = Counter()
    session_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    window_ids: set[str] = set()
    matched_window_ids: set[str] = set()
    cache_candidate_window_ids: set[str] = set()
    exact_requirements: dict[tuple[str, str, str], dict[str, Any]] = {}

    try:
        for ordered_row in ordered_rows:
            cid = str(ordered_row.get("candidate_id") or "")
            candidate = candidate_lookup.get(cid, {})
            row = build_hydration_row(
                ordered_row=ordered_row,
                candidate_row=candidate,
                source_index=source_index,
                scratch_run_root=scratch_run_root,
            )
            output_rows.append(row)
            counters["missing_ordered_path_rows_processed"] += 1
            counters[f"coverage_status:{row['coverage_status']}"] += 1
            counters[f"oracle_status:{row['oracle_status']}"] += 1
            counters[f"mt5_binary_cache_status:{row['mt5_binary_cache_status']}"] += 1
            counters[f"geometry_status:{row['geometry_status']}"] += 1
            if row["candidate_join_status"] == "joined":
                counters["candidate_rows_joined"] += 1
            else:
                counters["candidate_rows_missing"] += 1
            if row["decision_leakage_keys"]:
                counters["decision_packet_leakage_rows"] += 1
            session_counts[str(row["session"])] += 1
            symbol_counts[str(row["symbol"])] += 1
            window_ids.add(str(row["window_id"]))
            if row["matched_sources"]:
                matched_window_ids.add(str(row["window_id"]))
            for source in row["matched_sources"]:
                source_label_counts[str(source.get("source_label"))] += 1
            for source in row["rejected_sources"]:
                source_label_counts[str(source.get("source_label"))] += 1
            if row["mt5_binary_cache_candidates"]:
                cache_candidate_window_ids.add(str(row["window_id"]))
                for source in row["mt5_binary_cache_candidates"]:
                    cache_label_counts[str(source.get("source_label"))] += 1
            if not row["matched_sources"]:
                req_key = (str(row["symbol"]), str(row["date"]), str(row["session"]))
                req = exact_requirements.setdefault(
                    req_key,
                    {
                        "symbol": row["symbol"],
                        "date": row["date"],
                        "session": row["session"],
                        "required_source": "broker-native_or_mt5_exported_M1_or_tick_window",
                        "candidate_rows": 0,
                        "sample_candidate_ids": [],
                        "sample_window_ids": [],
                        "export_command_templates": row["export_command_templates"],
                        "cache_command_templates": row["cache_command_templates"],
                        "mt5_binary_cache_candidate_labels": [],
                        "mt5_binary_cache_candidate_paths": [],
                    },
                )
                req["candidate_rows"] += 1
                if len(req["sample_candidate_ids"]) < 5:
                    req["sample_candidate_ids"].append(row["candidate_id"])
                if len(req["sample_window_ids"]) < 5:
                    req["sample_window_ids"].append(row["window_id"])
                for source in row["mt5_binary_cache_candidates"]:
                    label = str(source.get("source_label") or "")
                    path = str(source.get("path") or "")
                    if label and label not in req["mt5_binary_cache_candidate_labels"]:
                        req["mt5_binary_cache_candidate_labels"].append(label)
                    if path and len(req["mt5_binary_cache_candidate_paths"]) < 5 and path not in req["mt5_binary_cache_candidate_paths"]:
                        req["mt5_binary_cache_candidate_paths"].append(path)
            scratch_file_count_peak = max(scratch_file_count_peak, _count_files(scratch_run_root))
    finally:
        if scratch_run_root.exists():
            shutil.rmtree(scratch_run_root)

    report = {
        "schema_version": "v4u_ordered_path_rolling_hydration_oracle_v1",
        "generated_at_utc": generated,
        "run_id": run,
        "source_boundary": (
            "read_only_local_m1_tick_oracle_no_broker_mutation_no_future_path_decision_inputs"
        ),
        "ordered_path_ledger": str(ordered_path_ledger),
        "candidate_ledger": str(candidate_ledger),
        "source_index_summary": source_index.summary,
        "metrics": {
            "ordered_touch_missing_rows": len(ordered_rows),
            "candidate_ids_required": len(candidate_ids),
            "candidate_rows_joined": counters["candidate_rows_joined"],
            "candidate_rows_missing": counters["candidate_rows_missing"],
            "rolling_window_count": len(window_ids),
            "rolling_windows_with_eligible_ltf": len(matched_window_ids),
            "rolling_windows_without_eligible_ltf": len(window_ids) - len(matched_window_ids),
            "rolling_windows_with_mt5_binary_cache_candidate": len(cache_candidate_window_ids),
            "decision_packet_leakage_rows": counters["decision_packet_leakage_rows"],
            "exact_requirement_groups": len(exact_requirements),
            "coverage_status_counts": _counter_prefix(counters, "coverage_status:"),
            "oracle_status_counts": _counter_prefix(counters, "oracle_status:"),
            "mt5_binary_cache_status_counts": _counter_prefix(counters, "mt5_binary_cache_status:"),
            "geometry_status_counts": _counter_prefix(counters, "geometry_status:"),
            "session_counts": dict(sorted(session_counts.items())),
            "symbol_counts": dict(sorted(symbol_counts.items())),
            "source_label_counts_seen_in_rows": dict(sorted(source_label_counts.items())),
            "mt5_binary_cache_label_counts_seen_in_rows": dict(sorted(cache_label_counts.items())),
        },
        "scratch_cleanup": {
            "scratch_root": str(scratch_root),
            "scratch_run_root": str(scratch_run_root),
            "scratch_created": scratch_created,
            "scratch_file_count_peak": scratch_file_count_peak,
            "scratch_exists_after_cleanup": scratch_run_root.exists(),
            "cleanup_status": "deleted" if not scratch_run_root.exists() else "delete_failed",
        },
        "exact_source_requirements": sorted(
            exact_requirements.values(),
            key=lambda item: (str(item["date"]), str(item["session"]), str(item["symbol"])),
        ),
        "verdict": {
            "local_or_package_ltf_rows_converted_to_ordered_path_truth": _counter_prefix(
                counters,
                "oracle_status:",
            ).get("resolved", 0),
            "remaining_rows_requiring_ltf_or_tick_source": _counter_prefix(
                counters,
                "coverage_status:",
            ).get("eligible_ltf_missing", 0),
            "rows_with_mt5_binary_cache_candidate_requiring_parser_or_export": _counter_prefix(
                counters,
                "mt5_binary_cache_status:",
            ).get("cache_candidate_requires_parser_or_readonly_export", 0),
            "proxy_sources_used_as_broker_native_truth": 0,
            "decision_packet_future_path_leakage_rows": counters["decision_packet_leakage_rows"],
        },
    }
    return report, output_rows


def build_hydration_row(
    *,
    ordered_row: Mapping[str, Any],
    candidate_row: Mapping[str, Any],
    source_index: SourceIndex,
    scratch_run_root: Path,
) -> dict[str, Any]:
    cid = str(ordered_row.get("candidate_id") or candidate_row.get("candidate_id") or "")
    symbol = canonical_symbol(candidate_row.get("symbol") or ordered_row.get("symbol"))
    asof_utc = str(candidate_row.get("asof_utc") or ordered_row.get("asof_utc") or "")
    date_key = date_from_value(asof_utc) or "DATE_MISSING"
    session, session_source = _row_session(candidate_row, asof_utc)
    request_start, request_end, window_source = session_window_bounds(asof_utc, session)
    target_r = _float(ordered_row.get("configured_target_r") or candidate_row.get("configured_target_r") or 2.0)
    geometry = _geometry(candidate_row, target_r)
    decision_packet = _decision_safe_packet(
        ordered_row=ordered_row,
        candidate_row=candidate_row,
        session=session,
        session_source=session_source,
        configured_target_r=target_r,
    )
    leakage_keys = sorted(set(decision_packet) & FORBIDDEN_DECISION_PATH_KEYS)
    window_payload = {
        "symbol": symbol,
        "date": date_key,
        "session": session,
        "request_start_utc": request_start,
        "request_end_utc": request_end,
        "window_source": window_source,
        "path_usage_boundary": (
            "post_decision_path_allowed_only_for_replay_labels_fillability_mfe_mae_milestones"
        ),
    }
    window_id = _json_hash(window_payload)[:24]
    matched = _matched_sources(source_index, symbol, date_key)
    rejected = _rejected_sources(source_index, symbol, date_key)
    cache_candidates = _mt5_binary_cache_candidates(rejected)
    cache_status = (
        "cache_candidate_requires_parser_or_readonly_export"
        if cache_candidates
        else "no_mt5_binary_cache_candidate"
    )
    oracle_result: dict[str, Any] | None = None
    oracle_status = "not_run_no_eligible_ltf_source"
    scratch_artifacts: list[dict[str, Any]] = []
    if matched and geometry["geometry_status"] == "geometry_ready":
        scratch_artifacts, oracle_result = _run_local_oracle_for_row(
            scratch_run_root=scratch_run_root,
            window_id=window_id,
            matched_sources=matched,
            request_start=request_start,
            request_end=request_end,
            geometry=geometry,
            asof_utc=asof_utc,
        )
        oracle_status = str(oracle_result.get("status") if oracle_result else "source_gap")
    elif matched:
        oracle_status = "not_run_geometry_gap"

    return {
        "schema_version": "v4u_ordered_path_rolling_oracle_row_v1",
        "candidate_id": cid,
        "path_row_id": ordered_row.get("path_row_id") or candidate_row.get("path_row_id"),
        "symbol": symbol,
        "date": date_key,
        "session": session,
        "session_source": session_source,
        "window_id": window_id,
        "candidate_join_status": "joined" if candidate_row else "candidate_row_missing",
        "asof_decision_packet": decision_packet,
        "decision_leakage_keys": leakage_keys,
        "post_decision_replay_window": window_payload,
        "coverage_status": "eligible_ltf_available" if matched else "eligible_ltf_missing",
        "matched_sources": [source.as_dict() for source in matched],
        "rejected_sources": [source.as_dict() for source in rejected],
        "mt5_binary_cache_status": cache_status,
        "mt5_binary_cache_candidates": [source.as_dict() for source in cache_candidates],
        "geometry_status": geometry["geometry_status"],
        "geometry": geometry,
        "scratch_artifacts": scratch_artifacts,
        "oracle_status": oracle_status,
        "oracle_result": oracle_result,
        "export_command_templates": _export_commands(symbol, request_start, request_end),
        "cache_command_templates": _cache_commands(symbol, date_key, request_start, request_end),
        "source_boundary": {
            "decision_boundary": "asof_decision_packet_excludes_future_path_and_result_fields",
            "replay_boundary": (
                "oracle_result_fields_are_post_decision_replay_labels_not_selector_inputs"
            ),
            "broker_real_boundary": "no_broker_order_deal_cost_slippage_or_cash_truth_claim",
            "proxy_boundary": "m15_or_proxy_sources_are_rejected_for_ordered_path_truth",
            "mt5_binary_cache_boundary": (
                "hcc_hc_tkc_ticks_dat_are_recoverable_cache_candidates_only_until "
                "parsed_or_exported_into_hashed_m1_or_tick_rows"
            ),
        },
    }


def _row_session(row: Mapping[str, Any], asof_utc: str) -> tuple[str, str]:
    for key in ("session", "session_name", "session_bucket", "origin_session"):
        if row.get(key):
            return str(row[key]).upper(), f"candidate_row_{key}"
    return derive_session_from_asof(asof_utc), "derived_from_asof_utc_hour"


def _decision_safe_packet(
    *,
    ordered_row: Mapping[str, Any],
    candidate_row: Mapping[str, Any],
    session: str,
    session_source: str,
    configured_target_r: float | None,
) -> dict[str, Any]:
    combined = {**dict(ordered_row), **dict(candidate_row)}
    combined["session"] = session
    combined["session_source"] = session_source
    combined["configured_target_r"] = configured_target_r
    return {key: combined.get(key) for key in sorted(SAFE_DECISION_KEYS) if combined.get(key) is not None}


def _geometry(row: Mapping[str, Any], target_r: float | None) -> dict[str, Any]:
    side = str(row.get("side") or "").upper()
    entry = _float(row.get("entry_reference") or row.get("entry_price"))
    stop = _float(row.get("stop_or_invalidation") or row.get("stop_price"))
    if side not in {"LONG", "BUY", "SHORT", "SELL"} or entry is None or stop is None or target_r is None:
        return {
            "geometry_status": "geometry_gap",
            "side": side,
            "entry_price": entry,
            "stop_price": stop,
            "target_r": target_r,
            "target_price": None,
            "source_gaps": ["side_entry_stop_or_target_r_missing"],
        }
    risk = abs(entry - stop)
    if risk <= 0:
        return {
            "geometry_status": "geometry_gap",
            "side": side,
            "entry_price": entry,
            "stop_price": stop,
            "target_r": target_r,
            "target_price": None,
            "source_gaps": ["entry_stop_risk_distance_missing_or_zero"],
        }
    if side in {"LONG", "BUY"}:
        target = entry + target_r * risk
    else:
        target = entry - target_r * risk
    return {
        "geometry_status": "geometry_ready",
        "side": side,
        "entry_price": entry,
        "stop_price": stop,
        "target_r": target_r,
        "target_price": target,
        "risk_distance": risk,
        "source_gaps": [],
    }


def _matched_sources(source_index: SourceIndex, symbol: str, date_key: str) -> tuple[IndexedSourceFile, ...]:
    sources = source_index.files_by_key.get((canonical_symbol(symbol), date_key), ())
    return tuple(sorted(sources, key=lambda src: (0 if src.source_kind == "tick" else 1, src.path)))


def _rejected_sources(source_index: SourceIndex, symbol: str, date_key: str) -> tuple[IndexedSourceFile, ...]:
    direct = list(source_index.rejected_by_key.get((canonical_symbol(symbol), date_key), ()))
    for alias in _cache_symbol_aliases(symbol):
        direct.extend(source_index.rejected_by_symbol.get(alias, ()))
        if alias == canonical_symbol(symbol):
            continue
        direct.extend(source_index.rejected_by_key.get((alias, date_key), ()))
    seen: set[str] = set()
    unique: list[IndexedSourceFile] = []
    for source in direct:
        if source.path in seen:
            continue
        seen.add(source.path)
        unique.append(source)
    return tuple(unique)


def _mt5_binary_cache_candidates(
    rejected_sources: tuple[IndexedSourceFile, ...],
) -> tuple[IndexedSourceFile, ...]:
    return tuple(
        source
        for source in rejected_sources
        if source.source_label in MT5_BINARY_CACHE_LABELS
    )


def _cache_symbol_aliases(symbol: str) -> tuple[str, ...]:
    canonical = canonical_symbol(symbol)
    aliases = {
        "NAS100": ("NAS100", "NDX100", "US100.CASH", "USTEC"),
        "US30_CASH": ("US30_CASH", "US30", "US30.CASH"),
        "GER40": ("GER40", "GER40.CASH", "GER30"),
        "JP225": ("JP225", "JP225.CASH"),
        "SPX500": ("SPX500", "US500.CASH", "SP500M"),
        "UK100": ("UK100", "UK100.CASH"),
        "UKOIL_CASH": ("UKOIL_CASH", "UKOIL.CASH", "UKOUSD"),
        "USOIL_CASH": ("USOIL_CASH", "USOIL.CASH", "USOUSD"),
    }
    return tuple(canonical_symbol(value) for value in aliases.get(canonical, (canonical,)))


def _run_local_oracle_for_row(
    *,
    scratch_run_root: Path,
    window_id: str,
    matched_sources: tuple[IndexedSourceFile, ...],
    request_start: str,
    request_end: str,
    geometry: Mapping[str, Any],
    asof_utc: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    window_root = scratch_run_root / window_id
    window_root.mkdir(parents=True, exist_ok=True)
    m1_path: Path | None = None
    tick_path: Path | None = None
    artifacts: list[dict[str, Any]] = []
    for source in matched_sources:
        path = Path(source.path)
        if source.source_kind in {"tick", "mt5_research_export_tick"} and tick_path is None:
            rows = _load_window_rows(path, request_start, request_end)
            tick_path = window_root / "ticks.jsonl"
            _write_jsonl(tick_path, rows)
            artifacts.append(_artifact_payload("tick", tick_path, len(rows), source))
        elif source.source_kind in {"m1", "mt5_research_export_m1"} and m1_path is None:
            rows = _load_window_rows(path, request_start, request_end)
            m1_path = window_root / "m1.csv"
            _write_csv(m1_path, rows)
            artifacts.append(_artifact_payload("m1", m1_path, len(rows), source))
    result = infer_ordered_path_from_local_files(
        m1_path=m1_path,
        tick_path=tick_path,
        side=str(geometry["side"]),
        entry_price=float(geometry["entry_price"]),
        stop_price=float(geometry["stop_price"]),
        target_price=float(geometry["target_price"]),
        asof_utc=asof_utc,
    ).as_dict()
    shutil.rmtree(window_root)
    return artifacts, result


def _load_window_rows(path: Path, request_start: str, request_end: str) -> list[dict[str, Any]]:
    start = parse_utc(request_start)
    end = parse_utc(request_end)
    if start is None or end is None:
        return []
    suffix = path.suffix.lower()
    if suffix == ".csv":
        rows = []
        with path.open("r", encoding="utf-8", newline="", errors="replace") as handle:
            for row in csv.DictReader(handle):
                ts = parse_utc(_row_time_text(row))
                if ts is not None and start <= ts <= end:
                    rows.append(dict(row))
        return rows
    if suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                row = json.loads(text)
                if isinstance(row, Mapping):
                    ts = parse_utc(_row_time_text(row))
                    if ts is not None and start <= ts <= end:
                        rows.append(dict(row))
        return rows
    if suffix == ".parquet":
        return _load_parquet_window_rows(path, start, end)
    return []


def _load_parquet_window_rows(path: Path, start: datetime, end: datetime) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq  # type: ignore
    except Exception:
        return []
    table = pq.read_table(path)
    rows = table.to_pylist()
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        ts = parse_utc(_row_time_text(row))
        if ts is not None and start <= ts <= end:
            out.append(dict(row))
    return out


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row.keys()}) or ["time_utc"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def _artifact_payload(kind: str, path: Path, row_count: int, source: IndexedSourceFile) -> dict[str, Any]:
    return {
        "kind": kind,
        "scratch_path": str(path),
        "row_count": row_count,
        "sha256": _file_sha256(path),
        "source_path": source.path,
        "source_sha256": source.sha256,
        "source_label": source.source_label,
        "scratch_deleted_after_oracle": True,
    }


def _export_commands(symbol: str, start: str, end: str) -> list[dict[str, Any]]:
    return [
        {
            "tool": "scripts/inspect_mt5_history_availability.py",
            "command": (
                "python3 scripts/inspect_mt5_history_availability.py "
                f"--start {start} --end {end} --symbol {symbol}:{symbol} "
                "--timeframes M1 --write-json --yes-live-readonly"
            ),
            "read_only": True,
            "purpose": "probe M1 availability before export",
        },
        {
            "tool": "scripts/inspect_mt5_tick_availability.py",
            "command": (
                "python3 scripts/inspect_mt5_tick_availability.py "
                f"--window {symbol}_{date_from_value(start) or 'window'}:{start}:{end} "
                f"--symbol {symbol}:{symbol} --write-json --yes-live-readonly"
            ),
            "read_only": True,
            "purpose": "probe tick availability before export",
        },
        {
            "tool": "scripts/export_mt5_research_ohlcv.py",
            "command": (
                "python3 scripts/export_mt5_research_ohlcv.py "
                f"--start {start} --end {end} --symbol {symbol}:{symbol} "
                "--timeframes M1 --label v4u_ordered_path_window --yes-live-readonly"
            ),
            "read_only": True,
            "purpose": "export M1 bars only for the needed replay window",
        },
    ]


def _cache_commands(symbol: str, date_key: str, start: str, end: str) -> list[dict[str, Any]]:
    return [
        {
            "tool": "src/research_infra/v4u_ordered_path_hydration.py",
            "command": (
                "index MT5 Bases binary cache roots for "
                f"{symbol} {date_key}; if hcc/hc/ticks.dat exists, parse or export "
                f"only {start} through {end} into hashed M1/tick rows before oracle use"
            ),
            "read_only": True,
            "purpose": "bind local MT5 cache recoverability without treating binary cache as ordered path truth",
        },
        {
            "tool": "scripts/export_mt5_research_ohlcv.py",
            "command": (
                "python3 scripts/export_mt5_research_ohlcv.py "
                f"--start {start} --end {end} --symbol {symbol}:{symbol} "
                "--timeframes M1 --label v4u_ordered_path_window_cache_backfill --yes-live-readonly"
            ),
            "read_only": True,
            "purpose": "materialize cache/server history as M1 CSV when binary parser authority is absent",
        },
    ]


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _counter_prefix(counter: Counter[str], prefix: str) -> dict[str, int]:
    return {
        key.removeprefix(prefix): int(value)
        for key, value in sorted(counter.items())
        if key.startswith(prefix)
    }


def _count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file())


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")


def append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(row), sort_keys=True) + "\n")
