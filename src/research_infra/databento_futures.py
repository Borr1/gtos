"""Databento futures research helpers.

This module is intentionally isolated from live trading components. It loads
credentials from environment only, estimates billable size/cost before fetches,
and writes raw third-party data to ignored cache roots.
"""

from __future__ import annotations

import importlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DATABENTO_DATASET = "GLBX.MDP3"
DEFAULT_DATABENTO_SCHEMA = "trades"
DEFAULT_DATABENTO_SYMBOLS = "ES.v.0"
DEFAULT_DATABENTO_STYPE_IN = "continuous"
DEFAULT_DATABENTO_RAW_ROOT = Path("data/external/raw/databento")


class DatabentoSetupError(RuntimeError):
    """Raised when Databento tooling is unavailable or not configured."""


@dataclass(frozen=True)
class DatabentoRequest:
    dataset: str = DEFAULT_DATABENTO_DATASET
    schema: str = DEFAULT_DATABENTO_SCHEMA
    symbols: str | tuple[str, ...] = DEFAULT_DATABENTO_SYMBOLS
    start: str = ""
    end: str | None = None
    stype_in: str = DEFAULT_DATABENTO_STYPE_IN
    stype_out: str | None = None
    limit: int | None = None

    def to_api_kwargs(self) -> dict[str, Any]:
        if not self.start:
            raise ValueError("start is required for Databento time series requests")
        kwargs: dict[str, Any] = {
            "dataset": self.dataset,
            "schema": self.schema,
            "symbols": symbols_for_databento(self.symbols),
            "start": self.start,
            "stype_in": self.stype_in,
        }
        if self.end:
            kwargs["end"] = self.end
        if self.limit is not None:
            kwargs["limit"] = self.limit
        if self.stype_out:
            kwargs["stype_out"] = self.stype_out
        return kwargs


@dataclass(frozen=True)
class DatabentoEstimate:
    record_count: int
    billable_size_bytes: int
    cost_usd: float

    @property
    def billable_size_mb(self) -> float:
        return self.billable_size_bytes / 1_000_000


@dataclass(frozen=True)
class DatabentoFetchResult:
    output_path: str
    metadata_path: str
    estimate: DatabentoEstimate
    request: DatabentoRequest


def project_root_from(path: Path | None = None) -> Path:
    if path is not None:
        return path
    return Path(__file__).resolve().parents[2]


def load_databento_env(project_root: Path | None = None) -> None:
    """Load `.env` then `.env.local`, letting local values override."""

    root = project_root_from(project_root)
    try:  # pragma: no cover - import availability is environment-specific
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(root / ".env", override=False)
    load_dotenv(root / ".env.local", override=True)


def databento_env_status() -> dict[str, bool]:
    return {"DATABENTO_API_KEY": bool(os.getenv("DATABENTO_API_KEY"))}


def import_databento() -> Any:
    try:
        return importlib.import_module("databento")
    except ImportError as exc:  # pragma: no cover - covered by CLI checks
        raise DatabentoSetupError(
            "The `databento` package is not installed. Install requirements or run "
            "`pip install databento` in this environment."
        ) from exc


def historical_client(databento_module: Any | None = None) -> Any:
    if not os.getenv("DATABENTO_API_KEY"):
        raise DatabentoSetupError(
            "DATABENTO_API_KEY is missing. Add it to .env.local; the key is never "
            "committed."
        )
    db = databento_module or import_databento()
    return db.Historical()


def parse_symbols(value: str | list[str] | tuple[str, ...]) -> str | tuple[str, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(part.strip() for part in value if part.strip())
    stripped = value.strip()
    if stripped.upper() == "ALL_SYMBOLS":
        return "ALL_SYMBOLS"
    if "," in stripped:
        return tuple(part.strip() for part in stripped.split(",") if part.strip())
    return (stripped,)


def symbols_for_databento(symbols: str | tuple[str, ...]) -> str | list[str]:
    parsed = parse_symbols(symbols)
    if parsed == "ALL_SYMBOLS":
        return "ALL_SYMBOLS"
    return list(parsed)


def safe_slug(value: Any, max_len: int = 96) -> str:
    text = str(value)
    text = re.sub(r"[^A-Za-z0-9._=-]+", "_", text).strip("_")
    return (text or "none")[:max_len]


def request_output_path(
    request: DatabentoRequest,
    root: Path | str = DEFAULT_DATABENTO_RAW_ROOT,
) -> Path:
    output_root = Path(root)
    symbol_slug = safe_slug(
        "ALL_SYMBOLS"
        if request.symbols == "ALL_SYMBOLS"
        else "_".join(parse_symbols(request.symbols))
    )
    start_slug = safe_slug(request.start)
    end_slug = safe_slug(request.end or "open")
    limit_slug = f"limit{request.limit}" if request.limit is not None else "full"
    filename = (
        f"{request.dataset}.{request.schema}.{symbol_slug}."
        f"{start_slug}_{end_slug}.{limit_slug}.dbn.zst"
    )
    return output_root / safe_slug(request.dataset) / safe_slug(request.schema) / filename


def estimate_request(client: Any, request: DatabentoRequest) -> DatabentoEstimate:
    kwargs = request.to_api_kwargs()
    metadata = client.metadata
    return DatabentoEstimate(
        record_count=int(metadata.get_record_count(**kwargs)),
        billable_size_bytes=int(metadata.get_billable_size(**kwargs)),
        cost_usd=float(metadata.get_cost(**kwargs)),
    )


def dataset_status(client: Any, dataset: str = DEFAULT_DATABENTO_DATASET) -> dict[str, Any]:
    metadata = client.metadata
    return {
        "dataset": dataset,
        "schemas": metadata.list_schemas(dataset=dataset),
        "range": metadata.get_dataset_range(dataset=dataset),
        "unit_prices": metadata.list_unit_prices(dataset=dataset),
    }


def fetch_request(
    client: Any,
    request: DatabentoRequest,
    *,
    root: Path | str = DEFAULT_DATABENTO_RAW_ROOT,
    max_cost_usd: float = 0.25,
    force: bool = False,
) -> DatabentoFetchResult:
    estimate = estimate_request(client, request)
    if estimate.cost_usd > max_cost_usd:
        raise RuntimeError(
            f"Databento request cost estimate ${estimate.cost_usd:.6f} exceeds "
            f"--max-cost-usd ${max_cost_usd:.6f}. Narrow the request or raise "
            "the explicit cap."
        )

    output_path = request_output_path(request, root)
    metadata_path = output_path.with_suffix(output_path.suffix + ".meta.json")
    if output_path.exists() and not force:
        raise FileExistsError(f"output already exists: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    client.timeseries.get_range(**request.to_api_kwargs(), path=str(output_path))
    metadata_path.write_text(
        json.dumps(
            {
                "schema_version": "databento_futures_fetch_v1",
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                "request": asdict(request),
                "estimate": asdict(estimate),
                "output_path": str(output_path),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return DatabentoFetchResult(
        output_path=str(output_path),
        metadata_path=str(metadata_path),
        estimate=estimate,
        request=request,
    )


def estimate_to_dict(estimate: DatabentoEstimate) -> dict[str, Any]:
    payload = asdict(estimate)
    payload["billable_size_mb"] = estimate.billable_size_mb
    return payload
