"""Shadow-only external data-feed infrastructure for Phase 3.

This module is intentionally not wired into the live orchestrator. It provides
the common cache, validation, parser, and as-of join primitives needed for the
free-feed sprint without changing trading decisions.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional
import xml.etree.ElementTree as ET


SCHEMA_VERSION = "external_feeds_v1"
DEFAULT_EXTERNAL_DATA_ROOT = Path("data/external")
_SLUG_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_NORMALIZED_FILE_RE = re.compile(
    r"^(?P<table>.+)_(?P<fetched_at>\d{8}T\d{6}Z)\.jsonl$"
)


class ExternalFeedError(Exception):
    """Base error for external-feed infrastructure."""


class ExternalFeedSchemaError(ExternalFeedError):
    """Raised when feed rows do not match the expected schema."""


class ExternalFeedFetchError(ExternalFeedError):
    """Raised when a source fetch fails."""


@dataclass(frozen=True)
class RawArtifact:
    """Metadata for one immutable raw source artifact."""

    source: str
    name: str
    path: str
    checksum_sha256: str
    size_bytes: int
    fetched_at_utc: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "name": self.name,
            "path": self.path,
            "checksum_sha256": self.checksum_sha256,
            "size_bytes": self.size_bytes,
            "fetched_at_utc": self.fetched_at_utc.isoformat(),
        }


@dataclass
class FeedStatus:
    """Freshness/status metadata for one source."""

    source: str
    status: str
    status_key: Optional[str] = None
    fetched_at_utc: Optional[datetime] = None
    latest_observation_utc: Optional[datetime] = None
    latest_publication_utc: Optional[datetime] = None
    next_expected_update_utc: Optional[datetime] = None
    row_count: int = 0
    checksum_sha256: Optional[str] = None
    schema_version: str = SCHEMA_VERSION
    message: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def status_id(self) -> str:
        return (
            safe_slug(self.source)
            if not self.status_key
            else f"{safe_slug(self.source)}:{safe_slug(self.status_key)}"
        )

    def to_dict(self) -> dict[str, Any]:
        def dt(value: Optional[datetime]) -> Optional[str]:
            return value.isoformat() if value else None

        return {
            "source": self.source,
            "status_key": self.status_key,
            "status_id": self.status_id,
            "status": self.status,
            "fetched_at_utc": dt(self.fetched_at_utc),
            "latest_observation_utc": dt(self.latest_observation_utc),
            "latest_publication_utc": dt(self.latest_publication_utc),
            "next_expected_update_utc": dt(self.next_expected_update_utc),
            "row_count": self.row_count,
            "checksum_sha256": self.checksum_sha256,
            "schema_version": self.schema_version,
            "message": self.message,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FeedStatus":
        return cls(
            source=str(payload["source"]),
            status=str(payload["status"]),
            status_key=(
                str(payload["status_key"]) if payload.get("status_key") else None
            ),
            fetched_at_utc=_optional_utc(payload.get("fetched_at_utc")),
            latest_observation_utc=_optional_utc(
                payload.get("latest_observation_utc")
            ),
            latest_publication_utc=_optional_utc(
                payload.get("latest_publication_utc")
            ),
            next_expected_update_utc=_optional_utc(
                payload.get("next_expected_update_utc")
            ),
            row_count=int(payload.get("row_count") or 0),
            checksum_sha256=payload.get("checksum_sha256"),
            schema_version=str(payload.get("schema_version") or SCHEMA_VERSION),
            message=str(payload.get("message") or ""),
            extra=dict(payload.get("extra") or {}),
        )


@dataclass(frozen=True)
class SourceSpec:
    """Configuration for validating and joining one external source."""

    name: str
    cadence: str
    required_fields: tuple[str, ...]
    join_time_field: str = "published_at_utc"
    symbol_field: str = "gtos_symbol"
    group_field: Optional[str] = None
    env_vars: tuple[str, ...] = ()
    shadow_only: bool = True


SOURCE_REGISTRY: dict[str, SourceSpec] = {
    "cftc_cot": SourceSpec(
        name="cftc_cot",
        cadence="weekly",
        required_fields=(
            "source",
            "report_type",
            "report_date",
            "published_at_utc",
            "gtos_symbol",
        ),
        group_field="report_type",
        env_vars=("SOCRATA_APP_TOKEN", "SOCRATA_TOKEN", "SOCRATA_API_KEY", "SOCRATA_API"),
    ),
    "fred": SourceSpec(
        name="fred",
        cadence="series_specific",
        required_fields=("source", "series_id", "observation_date", "value"),
        group_field="series_id",
        env_vars=("FRED_API_KEY",),
    ),
    "wgc": SourceSpec(
        name="wgc",
        cadence="weekly_or_monthly",
        required_fields=(
            "source",
            "dataset",
            "observation_date",
            "published_at_utc",
            "gtos_symbol",
        ),
        group_field="dataset",
        env_vars=("WGC_GOLDHUB_EMAIL",),
    ),
    "lbma_calendar": SourceSpec(
        name="lbma_calendar",
        cadence="business_day",
        required_fields=("source", "metal", "fix_name", "fix_time_utc", "gtos_symbol"),
        join_time_field="fix_time_utc",
    ),
    "flashalpha_gex": SourceSpec(
        name="flashalpha_gex",
        cadence="daily",
        required_fields=("source", "proxy_symbol", "as_of_utc"),
        join_time_field="as_of_utc",
        env_vars=("FLASHALPHA_API_KEY",),
    ),
}


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | date | str) -> datetime:
    """Normalize a date/datetime/ISO string to aware UTC.

    Naive datetimes are treated as UTC. Date-only values become midnight UTC.
    """

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, dt_time.min)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise ValueError("empty datetime string")
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            parsed = datetime.combine(date.fromisoformat(raw), dt_time.min)
    else:
        raise TypeError(f"unsupported datetime value: {type(value)!r}")

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _optional_utc(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    return ensure_utc(str(value))


def date_to_utc(value: date | str) -> datetime:
    """Convert a date-like value to midnight UTC."""

    if isinstance(value, str):
        value = date.fromisoformat(value)
    return datetime.combine(value, dt_time.min, tzinfo=timezone.utc)


def fred_daily_market_publication_utc(observation_date: date | str) -> datetime:
    """Conservative availability model for daily FRED market series.

    FRED real-time/vintage data is richer than a simple date lag, but the Phase 3
    daily market bundle uses rates, USD, and vol proxies where a next-UTC-day
    availability rule avoids same-day lookahead without requiring per-series
    release calendars.
    """

    if isinstance(observation_date, str):
        observation_date = date.fromisoformat(observation_date)
    return datetime.combine(
        observation_date + timedelta(days=1),
        dt_time.min,
        tzinfo=timezone.utc,
    )


_CFTC_CATCHUP_RELEASE_DATES: dict[str, str] = {
    # CFTC 2025 shutdown catch-up schedule. Report dates not listed here use the
    # normal Friday 3:30 p.m. Eastern publication model.
    "2025-09-30": "2025-11-19",
    "2025-10-07": "2025-11-21",
    "2025-10-14": "2025-11-25",
    "2025-10-21": "2025-12-02",
    "2025-10-28": "2025-12-05",
    "2025-11-04": "2025-12-09",
    "2025-11-10": "2025-12-12",
    "2025-11-18": "2025-12-16",
    "2025-11-25": "2025-12-19",
    "2025-12-02": "2025-12-23",
    "2025-12-09": "2025-12-30",
    "2025-12-16": "2026-01-06",
    "2025-12-23": "2026-01-09",
    "2025-12-30": "2026-01-13",
    "2026-01-06": "2026-01-16",
    "2026-01-13": "2026-01-20",
    "2026-01-20": "2026-01-23",
}


def cftc_publication_utc(report_date: date | str) -> datetime:
    """Return CFTC COT publication availability in UTC."""

    if isinstance(report_date, str):
        report_date = date.fromisoformat(report_date)
    release_date = date.fromisoformat(
        _CFTC_CATCHUP_RELEASE_DATES.get(
            report_date.isoformat(),
            _next_friday(report_date).isoformat(),
        )
    )
    eastern_offset_hours = -4 if is_us_dst(release_date) else -5
    local_release = datetime.combine(
        release_date,
        dt_time(hour=15, minute=30),
    )
    return (local_release - timedelta(hours=eastern_offset_hours)).replace(
        tzinfo=timezone.utc
    )


def _next_friday(day: date) -> date:
    return day + timedelta(days=(4 - day.weekday()) % 7)


def safe_slug(value: str) -> str:
    """Return a path-safe slug while preserving readability."""

    slug = _SLUG_RE.sub("_", value.strip())
    slug = slug.strip("._")
    if not slug:
        raise ValueError("slug cannot be empty")
    return slug


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _coerce_json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


class ExternalFeedStore:
    """Filesystem cache for raw, normalized, status, and feature artifacts."""

    def __init__(
        self,
        root: str | Path = DEFAULT_EXTERNAL_DATA_ROOT,
        schema_version: str = SCHEMA_VERSION,
    ) -> None:
        self.root = Path(root)
        self.schema_version = schema_version

    def raw_dir(self, source: str) -> Path:
        return self.root / "raw" / safe_slug(source)

    def normalized_dir(self, source: str) -> Path:
        return self.root / "normalized" / safe_slug(source)

    def feature_dir(self, symbol: str) -> Path:
        return self.root / "features" / safe_slug(symbol.upper())

    def status_dir(self) -> Path:
        return self.root / "status"

    def write_raw(
        self,
        source: str,
        name: str,
        data: bytes | str,
        *,
        fetched_at_utc: Optional[datetime] = None,
    ) -> RawArtifact:
        fetched_at = fetched_at_utc or utc_now()
        payload = data.encode("utf-8") if isinstance(data, str) else data
        target = self.raw_dir(source) / safe_slug(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        artifact = RawArtifact(
            source=safe_slug(source),
            name=safe_slug(name),
            path=str(target),
            checksum_sha256=sha256_bytes(payload),
            size_bytes=len(payload),
            fetched_at_utc=fetched_at,
        )
        meta_path = target.with_suffix(target.suffix + ".meta.json")
        meta_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return artifact

    def write_normalized_rows(
        self,
        source: str,
        table: str,
        rows: Iterable[Mapping[str, Any]],
        *,
        fetched_at_utc: Optional[datetime] = None,
    ) -> Path:
        fetched_at = fetched_at_utc or utc_now()
        target = (
            self.normalized_dir(source)
            / f"{safe_slug(table)}_{fetched_at:%Y%m%dT%H%M%SZ}.jsonl"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                payload = {
                    str(key): _coerce_json_value(value)
                    for key, value in dict(row).items()
                }
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return target

    def read_jsonl(self, path: str | Path) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    def latest_normalized_paths(self, source: str) -> list[Path]:
        """Return the latest normalized JSONL file per source table."""

        source_dir = self.normalized_dir(source)
        if not source_dir.exists():
            return []

        latest_by_table: dict[str, tuple[datetime, Path]] = {}
        for path in source_dir.glob("*.jsonl"):
            match = _NORMALIZED_FILE_RE.match(path.name)
            if not match:
                continue
            fetched_at = datetime.strptime(
                match.group("fetched_at"), "%Y%m%dT%H%M%SZ"
            ).replace(tzinfo=timezone.utc)
            table = match.group("table")
            current = latest_by_table.get(table)
            if current is None or fetched_at > current[0]:
                latest_by_table[table] = (fetched_at, path)

        return [
            path
            for _, path in sorted(
                latest_by_table.values(),
                key=lambda item: str(item[1]),
            )
        ]

    def read_latest_normalized_rows(self, source: str) -> list[dict[str, Any]]:
        """Read the latest normalized rows for every table under a source."""

        rows: list[dict[str, Any]] = []
        for path in self.latest_normalized_paths(source):
            rows.extend(self.read_jsonl(path))
        return rows

    def write_feature_snapshot(
        self,
        symbol: str,
        candle_close_utc: datetime | str,
        snapshot: Mapping[str, Any],
    ) -> Path:
        candle_close = ensure_utc(candle_close_utc)
        target = self.feature_dir(symbol) / f"{candle_close:%Y%m%dT%H%M%SZ}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True, default=json_default),
            encoding="utf-8",
        )
        return target

    def write_status(self, status: FeedStatus) -> Path:
        target = self._status_path(status.source, status.status_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(status.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return target

    def read_status(
        self,
        source: str,
        status_key: Optional[str] = None,
    ) -> Optional[FeedStatus]:
        path = self._status_path(source, status_key)
        if not path.exists():
            return None
        return FeedStatus.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_statuses(self, source: Optional[str] = None) -> list[FeedStatus]:
        if not self.status_dir().exists():
            return []
        statuses = [
            FeedStatus.from_dict(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(self.status_dir().glob("*.json"))
        ]
        if source is None:
            return statuses
        wanted = safe_slug(source)
        return [status for status in statuses if safe_slug(status.source) == wanted]

    def _status_path(self, source: str, status_key: Optional[str] = None) -> Path:
        name = safe_slug(source)
        if status_key:
            name = f"{name}__{safe_slug(status_key)}"
        return self.status_dir() / f"{name}.json"


def validate_required_fields(
    rows: Iterable[Mapping[str, Any]],
    required_fields: Iterable[str],
    *,
    source: str = "external_feed",
) -> list[dict[str, Any]]:
    """Validate required fields and return rows as plain dictionaries."""

    normalized = [dict(row) for row in rows]
    required = tuple(required_fields)
    if not normalized:
        raise ExternalFeedSchemaError(f"{source}: no rows to validate")
    for idx, row in enumerate(normalized):
        missing = [field for field in required if field not in row]
        if missing:
            raise ExternalFeedSchemaError(
                f"{source}: row {idx} missing required fields {missing}"
            )
    return normalized


def select_asof_row(
    rows: Iterable[Mapping[str, Any]],
    candle_close_utc: datetime | str,
    *,
    symbol: Optional[str] = None,
    time_field: str = "published_at_utc",
    symbol_field: str = "gtos_symbol",
) -> Optional[dict[str, Any]]:
    """Select the latest row whose publication/as-of time is not in the future."""

    candle_close = ensure_utc(candle_close_utc)
    selected: Optional[tuple[datetime, datetime, dict[str, Any]]] = None
    wanted_symbol = symbol.upper() if symbol else None

    for raw_row in rows:
        row = dict(raw_row)
        if wanted_symbol and row.get(symbol_field) not in (None, "", wanted_symbol):
            continue
        if time_field not in row:
            continue
        try:
            asof = ensure_utc(row[time_field])
        except (TypeError, ValueError):
            continue
        if asof > candle_close:
            continue
        observation_time = _row_observation_time(row, fallback=asof)
        if (
            selected is None
            or asof > selected[0]
            or (asof == selected[0] and observation_time > selected[1])
        ):
            selected = (asof, observation_time, row)

    return selected[2] if selected else None


def _row_observation_time(
    row: Mapping[str, Any],
    *,
    fallback: datetime,
) -> datetime:
    for field in (
        "observation_date",
        "report_date",
        "fix_time_utc",
        "as_of_utc",
        "trading_date_london",
    ):
        value = row.get(field)
        if value in (None, ""):
            continue
        try:
            return ensure_utc(value)
        except (TypeError, ValueError):
            continue
    return fallback


def build_feature_snapshot(
    *,
    symbol: str,
    candle_close_utc: datetime | str,
    source_rows: Mapping[str, Iterable[Mapping[str, Any]]],
    source_specs: Mapping[str, SourceSpec] = SOURCE_REGISTRY,
) -> dict[str, Any]:
    """Build a flat shadow feature snapshot from source row collections."""

    candle_close = ensure_utc(candle_close_utc)
    snapshot: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "symbol": symbol.upper(),
        "candle_close_utc": candle_close.isoformat(),
    }
    for source, rows in sorted(source_rows.items()):
        spec = source_specs.get(
            source,
            SourceSpec(name=source, cadence="unknown", required_fields=()),
        )
        prefix = safe_slug(source)
        materialized_rows = [dict(row) for row in rows]

        if spec.group_field:
            grouped: dict[str, list[dict[str, Any]]] = {}
            for row in materialized_rows:
                group_value = row.get(spec.group_field)
                if group_value in (None, ""):
                    continue
                grouped.setdefault(str(group_value), []).append(row)

            any_selected = False
            for group_value, group_rows in sorted(grouped.items()):
                group_prefix = f"{prefix}__{safe_slug(group_value)}"
                selected = select_asof_row(
                    group_rows,
                    candle_close,
                    symbol=symbol,
                    time_field=spec.join_time_field,
                    symbol_field=spec.symbol_field,
                )
                if selected is None:
                    snapshot[f"{group_prefix}__available"] = False
                    continue
                any_selected = True
                _append_snapshot_fields(snapshot, group_prefix, selected)
            snapshot[f"{prefix}__available"] = any_selected
            continue

        selected = select_asof_row(
            materialized_rows,
            candle_close,
            symbol=symbol,
            time_field=spec.join_time_field,
            symbol_field=spec.symbol_field,
        )
        if selected is None:
            snapshot[f"{prefix}__available"] = False
            continue

        _append_snapshot_fields(snapshot, prefix, selected)
    return snapshot


def _append_snapshot_fields(
    snapshot: dict[str, Any],
    prefix: str,
    selected: Mapping[str, Any],
) -> None:
    snapshot[f"{prefix}__available"] = True
    for key, value in selected.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            snapshot[f"{prefix}__{key}"] = value
        elif isinstance(value, (datetime, date)):
            snapshot[f"{prefix}__{key}"] = value.isoformat()


@dataclass(frozen=True)
class HttpResponse:
    """Minimal HTTP response abstraction for testable fetchers."""

    status_code: int
    content: bytes
    headers: Mapping[str, str]
    url: str

    def json(self) -> Any:
        return json.loads(self.content.decode("utf-8"))

    def text(self) -> str:
        return self.content.decode("utf-8")


class UrllibHttpClient:
    """Small urllib-based HTTP client with retry/backoff."""

    def __init__(
        self,
        *,
        user_agent: str = "GTOS-external-feeds/1.0",
        retries: int = 2,
        backoff_seconds: float = 0.5,
    ) -> None:
        self.user_agent = user_agent
        self.retries = retries
        self.backoff_seconds = backoff_seconds

    def get(
        self,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        timeout: int = 30,
    ) -> HttpResponse:
        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(dict(headers))

        last_error: Optional[BaseException] = None
        for attempt in range(self.retries + 1):
            try:
                request = urllib.request.Request(url, headers=request_headers)
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    content = response.read()
                    return HttpResponse(
                        status_code=int(response.status),
                        content=content,
                        headers=dict(response.headers.items()),
                        url=url,
                    )
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code not in (429, 500, 502, 503, 504):
                    break
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
            if attempt < self.retries:
                time.sleep(self.backoff_seconds * (2 ** attempt))

        raise ExternalFeedFetchError(f"GET failed for {url}: {last_error}") from last_error


class FredFeed:
    """FRED API URL builder and parser."""

    OBSERVATIONS_ENDPOINT = (
        "https://api.stlouisfed.org/fred/series/observations"
    )

    @staticmethod
    def build_observations_url(
        series_id: str,
        api_key: str,
        *,
        start_date: Optional[str | date] = None,
        end_date: Optional[str | date] = None,
    ) -> str:
        params: dict[str, str] = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
        }
        if start_date:
            params["observation_start"] = (
                start_date if isinstance(start_date, str) else start_date.isoformat()
            )
        if end_date:
            params["observation_end"] = (
                end_date if isinstance(end_date, str) else end_date.isoformat()
            )
        return f"{FredFeed.OBSERVATIONS_ENDPOINT}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def parse_observations(
        payload: Mapping[str, Any],
        *,
        series_id: str,
        fetched_at_utc: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        fetched_at = fetched_at_utc or utc_now()
        rows: list[dict[str, Any]] = []
        for observation in payload.get("observations", []):
            raw_value = observation.get("value")
            value = None if raw_value in (None, "", ".") else float(raw_value)
            obs_date = str(observation["date"])
            published_at = fred_daily_market_publication_utc(obs_date)
            rows.append(
                {
                    "source": "fred",
                    "series_id": series_id,
                    "observation_date": obs_date,
                    "published_at_utc": published_at.isoformat(),
                    "value": value,
                    "realtime_start": observation.get("realtime_start"),
                    "realtime_end": observation.get("realtime_end"),
                    "fetched_at_utc": fetched_at.isoformat(),
                    "publication_time_model": "observation_date_plus_1d_utc",
                }
            )
        return rows

    def __init__(
        self,
        store: ExternalFeedStore,
        http_client: Optional[UrllibHttpClient] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.store = store
        self.http_client = http_client or UrllibHttpClient()
        self.env = env or os.environ

    def fetch_series(
        self,
        series_id: str,
        *,
        api_key: Optional[str] = None,
        start_date: Optional[str | date] = None,
        end_date: Optional[str | date] = None,
    ) -> list[dict[str, Any]]:
        key = api_key or self.env.get("FRED_API_KEY")
        if not key:
            raise ExternalFeedFetchError("FRED_API_KEY is required")
        fetched_at = utc_now()
        url = self.build_observations_url(
            series_id,
            key,
            start_date=start_date,
            end_date=end_date,
        )
        response = self.http_client.get(url)
        self.store.write_raw(
            "fred",
            f"{safe_slug(series_id)}_{fetched_at:%Y%m%dT%H%M%SZ}.json",
            response.content,
            fetched_at_utc=fetched_at,
        )
        rows = self.parse_observations(
            response.json(),
            series_id=series_id,
            fetched_at_utc=fetched_at,
        )
        if rows:
            self.store.write_normalized_rows(
                "fred",
                f"{safe_slug(series_id)}_observations",
                rows,
                fetched_at_utc=fetched_at,
            )
        if rows:
            latest_obs = max(date_to_utc(row["observation_date"]) for row in rows)
            latest_pub = max(ensure_utc(row["published_at_utc"]) for row in rows)
            self.store.write_status(
                FeedStatus(
                    source="fred",
                    status_key=safe_slug(series_id.upper()),
                    status="fresh",
                    fetched_at_utc=fetched_at,
                    latest_observation_utc=latest_obs,
                    latest_publication_utc=latest_pub,
                    row_count=len(rows),
                    message=f"Fetched {series_id}",
                    extra={"series_id": series_id.upper()},
                )
            )
        return rows


class FlashAlphaGexFeed:
    """FlashAlpha GEX request builder and parser."""

    ENDPOINT = "https://lab.flashalpha.com/v1/exposure/gex/{symbol}"

    @staticmethod
    def build_request(
        symbol: str,
        api_key: str,
        *,
        expiration: Optional[str | date] = None,
    ) -> tuple[str, dict[str, str]]:
        url = FlashAlphaGexFeed.ENDPOINT.format(symbol=safe_slug(symbol.upper()))
        if expiration:
            expiration_value = (
                expiration if isinstance(expiration, str) else expiration.isoformat()
            )
            url = f"{url}?{urllib.parse.urlencode({'expiration': expiration_value})}"
        return (url, {"X-Api-Key": api_key})

    @staticmethod
    def parse_gex(
        payload: Mapping[str, Any],
        *,
        proxy_symbol: str,
        gtos_symbol: Optional[str] = None,
        expiration: Optional[str | date] = None,
        fetched_at_utc: Optional[datetime] = None,
    ) -> dict[str, Any]:
        fetched_at = fetched_at_utc or utc_now()

        def wall_strike(name: str) -> Optional[float]:
            value = payload.get(name)
            if isinstance(value, Mapping):
                value = value.get("strike")
            return None if value in (None, "") else float(value)

        as_of = (
            payload.get("as_of")
            or payload.get("timestamp")
            or payload.get("updated_at")
            or fetched_at.isoformat()
        )
        return {
            "source": "flashalpha_gex",
            "proxy_symbol": proxy_symbol.upper(),
            "gtos_symbol": gtos_symbol.upper() if gtos_symbol else "",
            "expiration": (
                expiration if isinstance(expiration, str)
                else expiration.isoformat() if expiration else None
            ),
            "as_of_utc": ensure_utc(str(as_of)).isoformat(),
            "underlying_price": _float_or_none(payload.get("underlying_price")),
            "net_gex": _float_or_none(payload.get("net_gex")),
            "net_gex_label": payload.get("net_gex_label"),
            "gamma_flip": _float_or_none(payload.get("gamma_flip")),
            "call_wall": wall_strike("call_wall"),
            "put_wall": wall_strike("put_wall"),
            "fetched_at_utc": fetched_at.isoformat(),
        }

    def __init__(
        self,
        store: ExternalFeedStore,
        http_client: Optional[UrllibHttpClient] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.store = store
        self.http_client = http_client or UrllibHttpClient()
        self.env = env or os.environ

    def fetch_gex(
        self,
        proxy_symbol: str,
        *,
        gtos_symbol: Optional[str] = None,
        expiration: Optional[str | date] = None,
        api_key: Optional[str] = None,
    ) -> dict[str, Any]:
        key = api_key or self.env.get("FLASHALPHA_API_KEY")
        if not key:
            raise ExternalFeedFetchError("FLASHALPHA_API_KEY is required")
        fetched_at = utc_now()
        url, headers = self.build_request(
            proxy_symbol,
            key,
            expiration=expiration,
        )
        response = self.http_client.get(url, headers=headers)
        self.store.write_raw(
            "flashalpha_gex",
            f"{safe_slug(proxy_symbol.upper())}_{fetched_at:%Y%m%dT%H%M%SZ}.json",
            response.content,
            fetched_at_utc=fetched_at,
        )
        row = self.parse_gex(
            response.json(),
            proxy_symbol=proxy_symbol,
            gtos_symbol=gtos_symbol,
            expiration=expiration,
            fetched_at_utc=fetched_at,
        )
        self.store.write_normalized_rows(
            "flashalpha_gex",
            f"{safe_slug(proxy_symbol.upper())}_gex",
            [row],
            fetched_at_utc=fetched_at,
        )
        self.store.write_status(
            FeedStatus(
                source="flashalpha_gex",
                status_key=safe_slug(
                    "_".join(
                        str(part)
                        for part in (
                            proxy_symbol.upper(),
                            (gtos_symbol or "").upper(),
                            row.get("expiration") or "no_expiration",
                        )
                        if part
                    )
                ),
                status="fresh",
                fetched_at_utc=fetched_at,
                latest_publication_utc=ensure_utc(row["as_of_utc"]),
                row_count=1,
                message=f"Fetched {proxy_symbol.upper()} GEX proxy",
                extra={
                    "proxy_symbol": proxy_symbol.upper(),
                    "gtos_symbol": (gtos_symbol or "").upper(),
                    "expiration": row.get("expiration"),
                },
            )
        )
        return row


class CftcCotFeed:
    """CFTC COT Socrata URL builder and normalizer."""

    DISAGG_COMBINED = "kh3c-gbw2"
    DISAGG_FUTURES_ONLY = "72hh-3qpy"
    TFF_FUTURES_ONLY = "gpe5-46if"
    RESOURCE_ENDPOINT = "https://publicreporting.cftc.gov/resource/{dataset}.json"

    def __init__(
        self,
        store: ExternalFeedStore,
        http_client: Optional[UrllibHttpClient] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.store = store
        self.http_client = http_client or UrllibHttpClient()
        self.env = env or os.environ

    @staticmethod
    def build_socrata_url(
        dataset_id: str,
        *,
        select: Optional[str] = None,
        where: Optional[str] = None,
        order: Optional[str] = None,
        limit: int = 50_000,
    ) -> str:
        params: dict[str, str] = {"$limit": str(limit)}
        if select:
            params["$select"] = select
        if where:
            params["$where"] = where
        if order:
            params["$order"] = order
        return (
            CftcCotFeed.RESOURCE_ENDPOINT.format(dataset=safe_slug(dataset_id))
            + "?"
            + urllib.parse.urlencode(params)
        )

    @staticmethod
    def parse_rows(
        payload: Iterable[Mapping[str, Any]],
        *,
        report_type: str,
        contract_map: Mapping[str, str],
        fetched_at_utc: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        fetched_at = fetched_at_utc or utc_now()
        rows: list[dict[str, Any]] = []
        for raw in payload:
            code = str(
                _first(
                    raw,
                    "cftc_contract_market_code",
                    "cftc_contract_market_code_quotes",
                    "cftc_commodity_code",
                )
                or ""
            ).strip()
            gtos_symbol = contract_map.get(code)
            if not gtos_symbol:
                continue
            report_date = _first(
                raw,
                "report_date_as_yyyy_mm_dd",
                "report_date_as_yyyy_mm_dd",
                "report_date_as_yyyy_mm_dd_",
                "report_date",
            )
            if not report_date:
                continue
            normalized_report_date = str(report_date)[:10]
            published_at = cftc_publication_utc(normalized_report_date)
            managed_long = _int_or_none(
                _first(raw, "m_money_positions_long_all", "noncomm_positions_long_all")
            )
            managed_short = _int_or_none(
                _first(raw, "m_money_positions_short_all", "noncomm_positions_short_all")
            )
            producer_long = _int_or_none(raw.get("prod_merc_positions_long_all"))
            producer_short = _int_or_none(raw.get("prod_merc_positions_short_all"))
            swap_long = _int_or_none(raw.get("swap_positions_long_all"))
            swap_short = _int_or_none(
                _first(raw, "swap__positions_short_all", "swap_positions_short_all")
            )
            leveraged_long = _int_or_none(raw.get("lev_money_positions_long_all"))
            leveraged_short = _int_or_none(raw.get("lev_money_positions_short_all"))
            asset_mgr_long = _int_or_none(raw.get("asset_mgr_positions_long"))
            asset_mgr_short = _int_or_none(raw.get("asset_mgr_positions_short"))

            rows.append(
                {
                    "source": "cftc_cot",
                    "report_type": report_type,
                    "report_date": normalized_report_date,
                    "published_at_utc": published_at.isoformat(),
                    "market_name": _first(
                        raw, "market_and_exchange_names", "market_and_exchange_name"
                    ),
                    "cftc_contract_market_code": code,
                    "gtos_symbol": gtos_symbol,
                    "open_interest": _int_or_none(
                        _first(raw, "open_interest_all", "open_interest")
                    ),
                    "managed_money_long": managed_long,
                    "managed_money_short": managed_short,
                    "managed_money_spread": _int_or_none(
                        raw.get("m_money_positions_spread_all")
                    ),
                    "managed_money_net": _subtract(managed_long, managed_short),
                    "producer_merchant_net": _subtract(producer_long, producer_short),
                    "swap_dealer_net": _subtract(swap_long, swap_short),
                    "leveraged_funds_net": _subtract(leveraged_long, leveraged_short),
                    "asset_manager_net": _subtract(asset_mgr_long, asset_mgr_short),
                    "fetched_at_utc": fetched_at.isoformat(),
                    "publication_time_model": "cftc_release_schedule_1530_et",
                }
            )
        return rows

    def fetch_dataset(
        self,
        *,
        dataset_id: str,
        report_type: str,
        contract_map: Mapping[str, str],
        where: Optional[str] = None,
        limit: int = 50_000,
    ) -> list[dict[str, Any]]:
        fetched_at = utc_now()
        url = self.build_socrata_url(
            dataset_id,
            where=where,
            order="report_date_as_yyyy_mm_dd DESC",
            limit=limit,
        )
        headers = {}
        token = _env_first(
            self.env,
            "SOCRATA_APP_TOKEN",
            "SOCRATA_TOKEN",
            "SOCRATA_API_KEY",
            "SOCRATA_API",
        )
        if token:
            headers["X-App-Token"] = token
        response = self.http_client.get(url, headers=headers or None)
        self.store.write_raw(
            "cftc_cot",
            f"{safe_slug(report_type)}_{fetched_at:%Y%m%dT%H%M%SZ}.json",
            response.content,
            fetched_at_utc=fetched_at,
        )
        rows = self.parse_rows(
            response.json(),
            report_type=report_type,
            contract_map=contract_map,
            fetched_at_utc=fetched_at,
        )
        if rows:
            self.store.write_normalized_rows(
                "cftc_cot",
                report_type,
                rows,
                fetched_at_utc=fetched_at,
            )
            for contract_code, gtos_symbol in sorted(contract_map.items()):
                contract_rows = [
                    row
                    for row in rows
                    if row.get("cftc_contract_market_code") == contract_code
                    and row.get("gtos_symbol") == gtos_symbol
                ]
                if not contract_rows:
                    continue
                latest_report = max(
                    date_to_utc(row["report_date"]) for row in contract_rows
                )
                latest_pub = max(
                    ensure_utc(row["published_at_utc"]) for row in contract_rows
                )
                self.store.write_status(
                    FeedStatus(
                        source="cftc_cot",
                        status_key=safe_slug(
                            f"{report_type}_{contract_code}_{gtos_symbol}"
                        ),
                        status="fresh",
                        fetched_at_utc=fetched_at,
                        latest_observation_utc=latest_report,
                        latest_publication_utc=latest_pub,
                        row_count=len(contract_rows),
                        message=(
                            f"Fetched {report_type} {contract_code}->{gtos_symbol}"
                        ),
                        extra={
                            "report_type": report_type,
                            "cftc_contract_market_code": contract_code,
                            "gtos_symbol": gtos_symbol,
                        },
                    )
                )
        return rows


class SimpleXlsxWorkbook:
    """Tiny XLSX reader for source workbooks without adding runtime deps."""

    XLSX_NS = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
    }

    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self._shared_strings: Optional[list[str]] = None
        self._sheet_paths: Optional[dict[str, str]] = None

    @classmethod
    def from_file(cls, path: str | Path) -> "SimpleXlsxWorkbook":
        return cls(Path(path).read_bytes())

    def sheet_names(self) -> list[str]:
        return list(self._paths().keys())

    def rows(self, sheet_name: str) -> list[list[Any]]:
        paths = self._paths()
        if sheet_name not in paths:
            raise ExternalFeedSchemaError(f"xlsx: sheet not found: {sheet_name}")
        with zipfile.ZipFile(io.BytesIO(self.payload)) as workbook:
            root = ET.fromstring(workbook.read(paths[sheet_name]))

        rows: list[list[Any]] = []
        for raw_row in root.findall(
            "main:sheetData/main:row",
            self.XLSX_NS,
        ):
            values: list[Any] = []
            for cell in raw_row.findall("main:c", self.XLSX_NS):
                column_idx = _xlsx_column_index(cell.attrib.get("r", ""))
                if column_idx is None:
                    continue
                while len(values) <= column_idx:
                    values.append(None)
                values[column_idx] = self._cell_value(cell)
            rows.append(values)
        return rows

    def dimensions(self) -> dict[str, str]:
        dimensions: dict[str, str] = {}
        with zipfile.ZipFile(io.BytesIO(self.payload)) as workbook:
            for sheet_name, path in self._paths().items():
                root = ET.fromstring(workbook.read(path))
                dimension = root.find("main:dimension", self.XLSX_NS)
                dimensions[sheet_name] = (
                    dimension.attrib.get("ref", "") if dimension is not None else ""
                )
        return dimensions

    def _paths(self) -> dict[str, str]:
        if self._sheet_paths is not None:
            return self._sheet_paths
        with zipfile.ZipFile(io.BytesIO(self.payload)) as workbook:
            workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
            relationships_root = ET.fromstring(
                workbook.read("xl/_rels/workbook.xml.rels")
            )
        relationships = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in relationships_root.findall(
                "pkgrel:Relationship",
                self.XLSX_NS,
            )
        }
        sheet_paths: dict[str, str] = {}
        for sheet in workbook_root.findall("main:sheets/main:sheet", self.XLSX_NS):
            rel_id = sheet.attrib[
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            ]
            target = relationships[rel_id].lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            sheet_paths[str(sheet.attrib["name"])] = target
        self._sheet_paths = sheet_paths
        return sheet_paths

    def _strings(self) -> list[str]:
        if self._shared_strings is not None:
            return self._shared_strings
        with zipfile.ZipFile(io.BytesIO(self.payload)) as workbook:
            if "xl/sharedStrings.xml" not in workbook.namelist():
                self._shared_strings = []
                return self._shared_strings
            root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
        strings: list[str] = []
        for shared_item in root.findall("main:si", self.XLSX_NS):
            text = "".join(
                node.text or ""
                for node in shared_item.findall(".//main:t", self.XLSX_NS)
            )
            strings.append(text)
        self._shared_strings = strings
        return strings

    def _cell_value(self, cell: ET.Element) -> Any:
        cell_type = cell.attrib.get("t")
        if cell_type == "s":
            value = cell.find("main:v", self.XLSX_NS)
            if value is None or value.text in (None, ""):
                return None
            return self._strings()[int(value.text)]
        if cell_type == "inlineStr":
            return "".join(
                node.text or ""
                for node in cell.findall(".//main:t", self.XLSX_NS)
            )
        if cell_type == "b":
            value = cell.find("main:v", self.XLSX_NS)
            return bool(int(value.text or "0")) if value is not None else None

        value = cell.find("main:v", self.XLSX_NS)
        if value is None or value.text in (None, ""):
            return None
        return _coerce_xlsx_scalar(value.text)


class WgcGoldhubImport:
    """Operator-assisted WGC Goldhub CSV importer.

    WGC account access and export terms are operator-controlled, so this importer
    normalizes a CSV that the operator has already downloaded into the shadow
    cache. It intentionally does not automate WGC login or scrape Goldhub pages.
    """

    HEADER_ALIASES: dict[str, tuple[str, ...]] = {
        "observation_date": (
            "observation_date",
            "date",
            "month",
            "period",
            "as_of",
            "as of",
        ),
        "published_at_utc": (
            "published_at_utc",
            "published_at",
            "publication_date",
            "published date",
            "release_date",
            "release date",
        ),
        "region": ("region", "fund_region", "fund region", "country"),
        "flow_tonnes": (
            "flow_tonnes",
            "flow tonnes",
            "flows_tonnes",
            "flows tonnes",
            "tonnes",
            "tonnes_change",
            "tonnes change",
            "change tonnes",
        ),
        "flow_usd_mn": (
            "flow_usd_mn",
            "flow usd mn",
            "flows_usd_mn",
            "flows usd mn",
            "fund flows us$mn",
            "fund flows usd mn",
            "usd mn",
        ),
        "holdings_tonnes": (
            "holdings_tonnes",
            "holdings tonnes",
            "total holdings",
            "total holdings tonnes",
            "tonnes held",
        ),
        "assets_usd_mn": (
            "assets_usd_mn",
            "assets usd mn",
            "aum_usd_mn",
            "aum usd mn",
            "assets us$mn",
        ),
    }

    @classmethod
    def parse_csv_text(
        cls,
        text: str,
        *,
        dataset: str,
        source_name: str = "",
        default_gtos_symbol: str = "XAUUSD",
        fetched_at_utc: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        fetched_at = fetched_at_utc or utc_now()
        reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
        if not reader.fieldnames:
            raise ExternalFeedSchemaError("wgc: CSV header row is required")

        header_lookup = {_normalize_header(name): name for name in reader.fieldnames}
        rows: list[dict[str, Any]] = []
        for raw_row in reader:
            if not any(str(value or "").strip() for value in raw_row.values()):
                continue
            raw_observation_date = cls._field(raw_row, header_lookup, "observation_date")
            if not str(raw_observation_date or "").strip():
                continue
            observation_date = _parse_wgc_date(raw_observation_date)
            raw_publication = cls._field(raw_row, header_lookup, "published_at_utc")
            published_at = (
                ensure_utc(_parse_wgc_date(raw_publication))
                if str(raw_publication or "").strip()
                else fetched_at
            )
            rows.append(
                {
                    "source": "wgc",
                    "dataset": safe_slug(dataset),
                    "observation_date": observation_date.isoformat(),
                    "published_at_utc": published_at.isoformat(),
                    "gtos_symbol": default_gtos_symbol.upper(),
                    "region": cls._text_or_none(
                        cls._field(raw_row, header_lookup, "region")
                    ),
                    "flow_tonnes": _number_or_none(
                        cls._field(raw_row, header_lookup, "flow_tonnes")
                    ),
                    "flow_usd_mn": _number_or_none(
                        cls._field(raw_row, header_lookup, "flow_usd_mn")
                    ),
                    "holdings_tonnes": _number_or_none(
                        cls._field(raw_row, header_lookup, "holdings_tonnes")
                    ),
                    "assets_usd_mn": _number_or_none(
                        cls._field(raw_row, header_lookup, "assets_usd_mn")
                    ),
                    "source_file": source_name,
                    "fetched_at_utc": fetched_at.isoformat(),
                }
            )

        return validate_required_fields(
            rows,
            SOURCE_REGISTRY["wgc"].required_fields,
            source="wgc",
        )

    @classmethod
    def _field(
        cls,
        row: Mapping[str, Any],
        header_lookup: Mapping[str, str],
        canonical: str,
    ) -> Any:
        for alias in cls.HEADER_ALIASES[canonical]:
            original_header = header_lookup.get(_normalize_header(alias))
            if original_header:
                return row.get(original_header)
        return None

    @staticmethod
    def _text_or_none(value: Any) -> Optional[str]:
        text = str(value or "").strip()
        return text or None

    def __init__(self, store: ExternalFeedStore) -> None:
        self.store = store

    def import_csv_file(
        self,
        path: str | Path,
        *,
        dataset: str,
        default_gtos_symbol: str = "XAUUSD",
    ) -> list[dict[str, Any]]:
        source_path = Path(path)
        if source_path.suffix.lower() != ".csv":
            raise ExternalFeedSchemaError("wgc: only CSV imports are supported")
        fetched_at = utc_now()
        payload = source_path.read_bytes()
        self.store.write_raw(
            "wgc",
            f"{safe_slug(source_path.stem)}_{fetched_at:%Y%m%dT%H%M%SZ}.csv",
            payload,
            fetched_at_utc=fetched_at,
        )
        rows = self.parse_csv_text(
            payload.decode("utf-8-sig"),
            dataset=dataset,
            source_name=source_path.name,
            default_gtos_symbol=default_gtos_symbol,
            fetched_at_utc=fetched_at,
        )
        self.store.write_normalized_rows(
            "wgc",
            safe_slug(dataset),
            rows,
            fetched_at_utc=fetched_at,
        )
        latest_obs = max(date_to_utc(row["observation_date"]) for row in rows)
        latest_pub = max(ensure_utc(row["published_at_utc"]) for row in rows)
        self.store.write_status(
            FeedStatus(
                source="wgc",
                status_key=safe_slug(dataset),
                status="fresh",
                fetched_at_utc=fetched_at,
                latest_observation_utc=latest_obs,
                latest_publication_utc=latest_pub,
                row_count=len(rows),
                message=f"Imported WGC {dataset} from {source_path.name}",
                extra={"dataset": safe_slug(dataset), "source_file": source_path.name},
            )
        )
        return rows

    def import_file(
        self,
        path: str | Path,
        *,
        dataset: str,
        default_gtos_symbol: str = "XAUUSD",
    ) -> list[dict[str, Any]]:
        suffix = Path(path).suffix.lower()
        if suffix == ".csv":
            return self.import_csv_file(
                path,
                dataset=dataset,
                default_gtos_symbol=default_gtos_symbol,
            )
        if suffix == ".xlsx":
            return self.import_xlsx_file(
                path,
                dataset=dataset,
                default_gtos_symbol=default_gtos_symbol,
            )
        raise ExternalFeedSchemaError(f"wgc: unsupported import type {suffix!r}")

    def import_xlsx_file(
        self,
        path: str | Path,
        *,
        dataset: str,
        default_gtos_symbol: str = "XAUUSD",
    ) -> list[dict[str, Any]]:
        if dataset not in {"gold_etf_flows", "gold_demand_trends"}:
            raise ExternalFeedSchemaError(
                "wgc: XLSX import supports gold_etf_flows or gold_demand_trends"
            )
        source_path = Path(path)
        fetched_at = utc_now()
        payload = source_path.read_bytes()
        self.store.write_raw(
            "wgc",
            f"{safe_slug(source_path.stem)}_{fetched_at:%Y%m%dT%H%M%SZ}.xlsx",
            payload,
            fetched_at_utc=fetched_at,
        )
        workbook = SimpleXlsxWorkbook(payload)
        if dataset == "gold_etf_flows":
            rows = self.parse_gold_etf_xlsx(
                workbook,
                source_name=source_path.name,
                default_gtos_symbol=default_gtos_symbol,
                fetched_at_utc=fetched_at,
            )
        else:
            rows = self.parse_gold_demand_trends_xlsx(
                workbook,
                source_name=source_path.name,
                default_gtos_symbol=default_gtos_symbol,
                fetched_at_utc=fetched_at,
            )
        self.store.write_normalized_rows(
            "wgc",
            safe_slug(dataset),
            rows,
            fetched_at_utc=fetched_at,
        )
        latest_obs = max(date_to_utc(row["observation_date"]) for row in rows)
        latest_pub = max(ensure_utc(row["published_at_utc"]) for row in rows)
        self.store.write_status(
            FeedStatus(
                source="wgc",
                status_key=safe_slug(dataset),
                status="fresh",
                fetched_at_utc=fetched_at,
                latest_observation_utc=latest_obs,
                latest_publication_utc=latest_pub,
                row_count=len(rows),
                message=(
                    f"Imported WGC {dataset} workbook from {source_path.name}; "
                    f"sheets={len(workbook.sheet_names())}"
                ),
                extra={
                    "dataset": safe_slug(dataset),
                    "source_file": source_path.name,
                    "sheets": workbook.sheet_names(),
                    "dimensions": workbook.dimensions(),
                },
            )
        )
        return rows

    @classmethod
    def parse_gold_demand_trends_xlsx(
        cls,
        workbook: SimpleXlsxWorkbook,
        *,
        source_name: str,
        default_gtos_symbol: str = "XAUUSD",
        fetched_at_utc: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        fetched_at = fetched_at_utc or utc_now()
        rows: list[dict[str, Any]] = []
        table_units = {
            "Gold Balance": "tonnes",
            "Jewellery": "tonnes",
            "Bar and Coin": "tonnes",
            "Consumer per Capita": "grams_per_capita",
            "Gold Prices": "price",
            "India Supply": "tonnes",
        }
        for sheet_name, unit in table_units.items():
            if sheet_name not in workbook.sheet_names():
                continue
            rows.extend(
                cls._parse_gdt_wide_table(
                    workbook.rows(sheet_name),
                    sheet_name=sheet_name,
                    unit=unit,
                    source_name=source_name,
                    default_gtos_symbol=default_gtos_symbol,
                    fetched_at_utc=fetched_at,
                )
            )
        if "ETFs" in workbook.sheet_names():
            rows.extend(
                cls._parse_gdt_etfs_sheet(
                    workbook.rows("ETFs"),
                    source_name=source_name,
                    default_gtos_symbol=default_gtos_symbol,
                    fetched_at_utc=fetched_at,
                )
            )
        if not rows:
            raise ExternalFeedSchemaError("wgc: no GDT rows parsed")
        return validate_required_fields(
            rows,
            SOURCE_REGISTRY["wgc"].required_fields,
            source="wgc",
        )

    @classmethod
    def _parse_gdt_wide_table(
        cls,
        rows: list[list[Any]],
        *,
        sheet_name: str,
        unit: str,
        source_name: str,
        default_gtos_symbol: str,
        fetched_at_utc: datetime,
    ) -> list[dict[str, Any]]:
        if len(rows) < 3:
            return []
        header = rows[1]
        output: list[dict[str, Any]] = []
        for row in rows[2:]:
            category = str(_cell(row, 1) or "").strip()
            if not category:
                continue
            for column_idx, period_label in enumerate(header):
                if column_idx <= 1:
                    continue
                period = _parse_gdt_period(period_label)
                if period is None:
                    continue
                value = _number_or_none(_cell(row, column_idx))
                if value is None:
                    continue
                output.append(
                    cls._wgc_row(
                        dataset=_wgc_dataset(
                            "gold_demand_trends",
                            sheet_name,
                            category,
                            period["frequency"],
                        ),
                        observation_date=period["observation_date"],
                        published_at=fetched_at_utc,
                        default_gtos_symbol=default_gtos_symbol,
                        region=category,
                        source_name=source_name,
                        source_sheet=sheet_name,
                        fetched_at_utc=fetched_at_utc,
                        flow_tonnes=value if unit == "tonnes" else None,
                        flow_usd_mn=None,
                        holdings_tonnes=None,
                        assets_usd_mn=None,
                        extra={
                            "table": sheet_name,
                            "category": category,
                            "period_label": str(period_label),
                            "frequency": period["frequency"],
                            "unit": unit,
                            "value": value,
                        },
                    )
                )
        return output

    @classmethod
    def _parse_gdt_etfs_sheet(
        cls,
        rows: list[list[Any]],
        *,
        source_name: str,
        default_gtos_symbol: str,
        fetched_at_utc: datetime,
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for row in rows[2:]:
            fund = str(_cell(row, 1) or "").strip()
            if fund:
                holdings = _number_or_none(_cell(row, 3))
                if holdings is not None:
                    output.append(
                        cls._wgc_row(
                            dataset=_wgc_dataset("gold_demand_trends", "etfs", fund),
                            observation_date=date(2026, 3, 31),
                            published_at=fetched_at_utc,
                            default_gtos_symbol=default_gtos_symbol,
                            region=str(_cell(row, 2) or "").strip() or "Global",
                            source_name=source_name,
                            source_sheet="ETFs",
                            fetched_at_utc=fetched_at_utc,
                            flow_tonnes=None,
                            flow_usd_mn=None,
                            holdings_tonnes=holdings,
                            assets_usd_mn=None,
                            extra={
                                "table": "ETFs",
                                "category": fund,
                                "unit": "tonnes",
                                "value": holdings,
                                "yoy_pct_change": _number_or_none(_cell(row, 4)),
                            },
                        )
                    )
            taxonomy = str(_cell(row, 7) or "").strip()
            for column_idx in range(8, min(len(row), 13)):
                value = _number_or_none(_cell(row, column_idx))
                if not taxonomy or value is None:
                    continue
                period = _parse_gdt_period(_cell(rows[1], column_idx))
                if period is None:
                    continue
                output.append(
                    cls._wgc_row(
                        dataset=_wgc_dataset(
                            "gold_demand_trends",
                            "etf_region_aum",
                            taxonomy,
                        ),
                        observation_date=period["observation_date"],
                        published_at=fetched_at_utc,
                        default_gtos_symbol=default_gtos_symbol,
                        region=taxonomy,
                        source_name=source_name,
                        source_sheet="ETFs",
                        fetched_at_utc=fetched_at_utc,
                        flow_tonnes=None,
                        flow_usd_mn=None,
                        holdings_tonnes=value,
                        assets_usd_mn=None,
                        extra={
                            "table": "ETFs",
                            "category": taxonomy,
                            "period_label": str(_cell(rows[1], column_idx)),
                            "frequency": period["frequency"],
                            "unit": "tonnes",
                            "value": value,
                        },
                    )
                )
        return output

    @classmethod
    def parse_gold_etf_xlsx(
        cls,
        workbook: SimpleXlsxWorkbook,
        *,
        source_name: str,
        default_gtos_symbol: str = "XAUUSD",
        fetched_at_utc: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        fetched_at = fetched_at_utc or utc_now()
        required_sheets = {
            "Periods Legend",
            "Key Tables by fund",
            "Charts Data",
        }
        missing = required_sheets.difference(workbook.sheet_names())
        if missing:
            raise ExternalFeedSchemaError(f"wgc: missing sheets {sorted(missing)}")

        periods = cls._parse_periods(workbook.rows("Periods Legend"))
        rows: list[dict[str, Any]] = []
        rows.extend(
            cls._parse_gold_etf_key_tables(
                workbook.rows("Key Tables by fund"),
                periods=periods,
                source_name=source_name,
                default_gtos_symbol=default_gtos_symbol,
                fetched_at_utc=fetched_at,
            )
        )
        rows.extend(
            cls._parse_gold_etf_charts_data(
                workbook.rows("Charts Data"),
                source_name=source_name,
                default_gtos_symbol=default_gtos_symbol,
                fetched_at_utc=fetched_at,
            )
        )
        return validate_required_fields(
            rows,
            SOURCE_REGISTRY["wgc"].required_fields,
            source="wgc",
        )

    @staticmethod
    def _parse_periods(rows: list[list[Any]]) -> dict[str, dict[str, date]]:
        periods: dict[str, dict[str, date]] = {}
        for row in rows:
            if len(row) < 4:
                continue
            title = str(_cell(row, 1) or "").strip()
            if not title or title.lower() == "title":
                continue
            try:
                periods[title] = {
                    "start": _excel_serial_to_date(_cell(row, 2)),
                    "end": _excel_serial_to_date(_cell(row, 3)),
                }
            except (TypeError, ValueError, ExternalFeedSchemaError):
                continue
        return periods

    @classmethod
    def _parse_gold_etf_key_tables(
        cls,
        rows: list[list[Any]],
        *,
        periods: Mapping[str, Mapping[str, date]],
        source_name: str,
        default_gtos_symbol: str,
        fetched_at_utc: datetime,
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        if len(rows) < 4:
            return output
        period_blocks = (
            {"label_col": 1, "region_col": 1, "aum_col": 2, "flow_usd_col": 3, "holdings_col": 4, "flow_tonnes_col": 5, "demand_pct_col": 6},
            {"label_col": 8, "region_col": 8, "aum_col": 9, "flow_usd_col": 10, "holdings_col": 11, "flow_tonnes_col": 12, "demand_pct_col": 13},
            {"label_col": 15, "region_col": 15, "aum_col": 16, "flow_usd_col": 17, "holdings_col": 18, "flow_tonnes_col": 19, "demand_pct_col": 20},
        )
        valid_regions = {
            "North America",
            "Europe",
            "Asia",
            "Other",
            "Total",
            "Global inflows / Positive Demand",
            "Global outflows / Negative Demand",
        }
        for block in period_blocks:
            period_label = str(_cell(rows[0], block["label_col"]) or "").strip()
            if not period_label:
                continue
            period = periods.get(period_label, {})
            observation_date = period.get("end") or _parse_wgc_date(period_label)
            period_start = period.get("start")
            for row in rows[3:10]:
                region = str(_cell(row, block["region_col"]) or "").strip()
                if region not in valid_regions:
                    continue
                aum_bn = _number_or_none(_cell(row, block["aum_col"]))
                output.append(
                    cls._wgc_row(
                        dataset=_wgc_dataset("gold_etf_flows", period_label, region),
                        observation_date=observation_date,
                        published_at=fetched_at_utc,
                        default_gtos_symbol=default_gtos_symbol,
                        region=region,
                        source_name=source_name,
                        source_sheet="Key Tables by fund",
                        fetched_at_utc=fetched_at_utc,
                        flow_tonnes=_number_or_none(
                            _cell(row, block["flow_tonnes_col"])
                        ),
                        flow_usd_mn=_number_or_none(
                            _cell(row, block["flow_usd_col"])
                        ),
                        holdings_tonnes=_number_or_none(
                            _cell(row, block["holdings_col"])
                        ),
                        assets_usd_mn=None if aum_bn is None else aum_bn * 1000.0,
                        extra={
                            "period_label": period_label,
                            "period_start_date": (
                                period_start.isoformat() if period_start else None
                            ),
                            "period_end_date": observation_date.isoformat(),
                            "demand_pct_of_holdings": _number_or_none(
                                _cell(row, block["demand_pct_col"])
                            ),
                        },
                    )
                )
        return output

    @classmethod
    def _parse_gold_etf_charts_data(
        cls,
        rows: list[list[Any]],
        *,
        source_name: str,
        default_gtos_symbol: str,
        fetched_at_utc: datetime,
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        regions = (
            ("North America", 1, 10),
            ("Europe", 2, 11),
            ("Asia", 3, 12),
            ("Other", 4, 13),
        )
        for row in rows[2:]:
            serial = _cell(row, 0)
            if serial in (None, ""):
                continue
            try:
                observation_date = _excel_serial_to_date(serial)
            except (TypeError, ValueError, ExternalFeedSchemaError):
                continue
            gold_price = _number_or_none(_cell(row, 5))
            regional_rows: list[dict[str, Any]] = []
            for region, usd_col, tonnes_col in regions:
                flow_usd = _number_or_none(_cell(row, usd_col))
                flow_tonnes = _number_or_none(_cell(row, tonnes_col))
                regional_row = cls._wgc_row(
                    dataset=_wgc_dataset("gold_etf_flows_monthly", region),
                    observation_date=observation_date,
                    published_at=fetched_at_utc,
                    default_gtos_symbol=default_gtos_symbol,
                    region=region,
                    source_name=source_name,
                    source_sheet="Charts Data",
                    fetched_at_utc=fetched_at_utc,
                    flow_tonnes=flow_tonnes,
                    flow_usd_mn=None if flow_usd is None else flow_usd / 1_000_000.0,
                    holdings_tonnes=None,
                    assets_usd_mn=None,
                    extra={"gold_price_usd_oz": gold_price},
                )
                regional_rows.append(regional_row)
                output.append(regional_row)

            flow_tonnes_total = _sum_optional(
                row.get("flow_tonnes") for row in regional_rows
            )
            flow_usd_total = _sum_optional(
                row.get("flow_usd_mn") for row in regional_rows
            )
            output.append(
                cls._wgc_row(
                    dataset="gold_etf_flows_monthly_total",
                    observation_date=observation_date,
                    published_at=fetched_at_utc,
                    default_gtos_symbol=default_gtos_symbol,
                    region="Total",
                    source_name=source_name,
                    source_sheet="Charts Data",
                    fetched_at_utc=fetched_at_utc,
                    flow_tonnes=flow_tonnes_total,
                    flow_usd_mn=flow_usd_total,
                    holdings_tonnes=None,
                    assets_usd_mn=None,
                    extra={"gold_price_usd_oz": gold_price},
                )
            )
        return output

    @staticmethod
    def _wgc_row(
        *,
        dataset: str,
        observation_date: date,
        published_at: datetime,
        default_gtos_symbol: str,
        region: str,
        source_name: str,
        source_sheet: str,
        fetched_at_utc: datetime,
        flow_tonnes: Optional[float],
        flow_usd_mn: Optional[float],
        holdings_tonnes: Optional[float],
        assets_usd_mn: Optional[float],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        row = {
            "source": "wgc",
            "dataset": safe_slug(dataset),
            "observation_date": observation_date.isoformat(),
            "published_at_utc": published_at.isoformat(),
            "gtos_symbol": default_gtos_symbol.upper(),
            "region": region,
            "flow_tonnes": flow_tonnes,
            "flow_usd_mn": flow_usd_mn,
            "holdings_tonnes": holdings_tonnes,
            "assets_usd_mn": assets_usd_mn,
            "source_file": source_name,
            "source_sheet": source_sheet,
            "fetched_at_utc": fetched_at_utc.isoformat(),
        }
        if extra:
            row.update({key: value for key, value in extra.items() if value is not None})
        return row


class LbmaFixCalendar:
    """Deterministic LBMA AM/PM fix calendar feature generator."""

    FIX_TIMES_BY_METAL = {
        "gold": {
            "AM": dt_time(hour=10, minute=30),
            "PM": dt_time(hour=15, minute=0),
        },
        "silver": {
            "DAILY": dt_time(hour=12, minute=0),
        },
        "platinum": {
            "AM": dt_time(hour=9, minute=45),
            "PM": dt_time(hour=14, minute=0),
        },
        "palladium": {
            "AM": dt_time(hour=9, minute=45),
            "PM": dt_time(hour=14, minute=0),
        },
    }
    GTOS_SYMBOL_BY_METAL = {
        "gold": "XAUUSD",
        "silver": "XAGUSD",
    }

    @classmethod
    def generate(
        cls,
        start_date: date | str,
        end_date: date | str,
        *,
        metals: Iterable[str] = ("gold",),
    ) -> list[dict[str, Any]]:
        if isinstance(start_date, str):
            start = date.fromisoformat(start_date)
        else:
            start = start_date
        if isinstance(end_date, str):
            end = date.fromisoformat(end_date)
        else:
            end = end_date
        if end < start:
            raise ValueError("end_date must be >= start_date")

        rows: list[dict[str, Any]] = []
        current = start
        requested_metals = [metal.lower() for metal in metals]
        unsupported = [
            metal for metal in requested_metals if metal not in cls.FIX_TIMES_BY_METAL
        ]
        if unsupported:
            raise ValueError(f"unsupported LBMA metals: {unsupported}")
        while current <= end:
            if current.weekday() < 5:
                for metal in requested_metals:
                    for fix_name, local_time in cls.FIX_TIMES_BY_METAL[metal].items():
                        local_dt = datetime.combine(current, local_time)
                        offset_hours = 1 if is_london_bst(current) else 0
                        fix_utc = (local_dt - timedelta(hours=offset_hours)).replace(
                            tzinfo=timezone.utc
                        )
                        rows.append(
                            {
                                "source": "lbma_calendar",
                                "metal": metal.lower(),
                                "gtos_symbol": cls.GTOS_SYMBOL_BY_METAL.get(
                                    metal.lower(), ""
                                ),
                                "fix_name": fix_name,
                                "fix_time_london": local_time.isoformat(timespec="minutes"),
                                "fix_time_utc": fix_utc.isoformat(),
                                "trading_date_london": current.isoformat(),
                                "uk_us_dst_misalignment": (
                                    is_london_bst(current) != is_us_dst(current)
                                ),
                            }
                        )
            current += timedelta(days=1)
        return rows


def is_london_bst(day: date) -> bool:
    """Return whether London is in BST at LBMA fix times for the date."""

    start = _last_weekday_of_month(day.year, 3, weekday=6)
    end = _last_weekday_of_month(day.year, 10, weekday=6)
    return start <= day < end


def is_us_dst(day: date) -> bool:
    """Return whether New York is in daylight time for the date."""

    start = _nth_weekday_of_month(day.year, 3, weekday=6, n=2)
    end = _nth_weekday_of_month(day.year, 11, weekday=6, n=1)
    return start <= day < end


def external_feed_env_status(
    env: Optional[Mapping[str, str]] = None,
    source_specs: Mapping[str, SourceSpec] = SOURCE_REGISTRY,
) -> dict[str, dict[str, bool]]:
    """Report which optional credentials are present without exposing values."""

    lookup = env or os.environ
    result: dict[str, dict[str, bool]] = {}
    for source, spec in sorted(source_specs.items()):
        result[source] = {
            env_var: bool(str(lookup.get(env_var, "")).strip())
            for env_var in spec.env_vars
        }
    return result


def _last_weekday_of_month(year: int, month: int, *, weekday: int) -> date:
    if month == 12:
        current = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        current = date(year, month + 1, 1) - timedelta(days=1)
    while current.weekday() != weekday:
        current -= timedelta(days=1)
    return current


def _nth_weekday_of_month(year: int, month: int, *, weekday: int, n: int) -> date:
    current = date(year, month, 1)
    while current.weekday() != weekday:
        current += timedelta(days=1)
    return current + timedelta(days=7 * (n - 1))


def _first(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def _env_first(env: Mapping[str, str], *keys: str) -> str:
    for key in keys:
        value = str(env.get(key, "")).strip()
        if value:
            return value
    return ""


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _cell(row: list[Any], idx: int) -> Any:
    return row[idx] if idx < len(row) else None


def _excel_serial_to_date(value: Any) -> date:
    if value in (None, ""):
        raise ExternalFeedSchemaError("empty Excel date serial")
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and not re.fullmatch(r"\d+(\.\d+)?", value.strip()):
        return _parse_wgc_date(value)
    serial = int(float(value))
    if serial <= 0:
        raise ExternalFeedSchemaError(f"invalid Excel date serial {value!r}")
    return date(1899, 12, 30) + timedelta(days=serial)


def _wgc_dataset(*parts: str) -> str:
    return safe_slug("_".join(safe_slug(part.lower()) for part in parts if part))


def _parse_gdt_period(value: Any) -> Optional[dict[str, Any]]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)) and 1900 <= int(value) <= 2100:
        year = int(value)
        return {
            "frequency": "annual",
            "observation_date": date(year, 12, 31),
        }
    label = str(value).strip()
    if re.fullmatch(r"\d{4}", label):
        year = int(label)
        return {
            "frequency": "annual",
            "observation_date": date(year, 12, 31),
        }
    match = re.fullmatch(r"Q([1-4])['’](\d{2})", label)
    if not match:
        return None
    quarter = int(match.group(1))
    year = 2000 + int(match.group(2))
    month = quarter * 3
    return {
        "frequency": "quarterly",
        "observation_date": _last_day_of_month(year, month),
    }


def _sum_optional(values: Iterable[Any]) -> Optional[float]:
    total = 0.0
    found = False
    for value in values:
        number = _number_or_none(value)
        if number is None:
            continue
        found = True
        total += number
    return total if found else None


def _xlsx_column_index(cell_reference: str) -> Optional[int]:
    match = re.match(r"([A-Z]+)", cell_reference or "")
    if not match:
        return None
    idx = 0
    for char in match.group(1):
        idx = idx * 26 + ord(char) - ord("A") + 1
    return idx - 1


def _coerce_xlsx_scalar(value: str) -> Any:
    raw = value.strip()
    if raw == "":
        return None
    try:
        number = float(raw)
    except ValueError:
        return raw
    if number.is_integer():
        return int(number)
    return number


def _parse_wgc_date(value: Any) -> date:
    raw = str(value or "").strip()
    if not raw:
        raise ExternalFeedSchemaError("wgc: empty date value")

    if re.fullmatch(r"\d{4}-\d{2}", raw):
        year, month = (int(part) for part in raw.split("-", 1))
        return _last_day_of_month(year, month)
    if re.fullmatch(r"\d{4}", raw):
        return date(int(raw), 12, 31)

    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%b-%Y",
        "%d %b %Y",
        "%b %d %Y",
        "%B %d %Y",
    ):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass

    for fmt in ("%b-%y", "%b %y", "%b-%Y", "%b %Y", "%B %Y"):
        try:
            parsed = datetime.strptime(raw, fmt).date()
            return _last_day_of_month(parsed.year, parsed.month)
        except ValueError:
            pass

    raise ExternalFeedSchemaError(f"wgc: unsupported date value {raw!r}")


def _last_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, month, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _number_or_none(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    raw = str(value).strip().replace(",", "").replace("%", "")
    if raw.lower() in {"", "-", "—", "▲", "▼", "n/a", "na", "nan", "null"}:
        return None
    if raw.startswith("(") and raw.endswith(")"):
        raw = "-" + raw[1:-1]
    return float(raw)


def _float_or_none(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    return float(value)


def _int_or_none(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    return int(float(value))


def _subtract(left: Optional[int], right: Optional[int]) -> Optional[int]:
    if left is None or right is None:
        return None
    return left - right


def rows_to_csv(rows: Iterable[Mapping[str, Any]]) -> str:
    """Serialize rows to CSV for lightweight exports."""

    materialized = [dict(row) for row in rows]
    if not materialized:
        return ""
    fieldnames = sorted({key for row in materialized for key in row})
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in materialized:
        writer.writerow({key: _coerce_json_value(row.get(key)) for key in fieldnames})
    return buffer.getvalue()
