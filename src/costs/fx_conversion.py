"""Date-indexed cash-to-R FX conversion from the captured D1 archive."""

from __future__ import annotations

import bisect
import gzip
import io
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from src.costs.artifact_authority import (
    CostInputAuthorityError,
    DEFAULT_COST_INPUTS_MANIFEST,
    verify_cost_input,
)
from src.costs.coverage import Coverage
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive

__all__ = [
    "DEFAULT_FX_ARTIFACT",
    "FxConversionError",
    "FxRate",
    "HistoricalFxRates",
    "load_historical_fx",
]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_FX_ARTIFACT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/cost/HISTORICAL_FX_D1_V1.json.gz"
)


class FxConversionError(RuntimeError):
    """The captured FX series cannot decide the requested conversion."""


@dataclass(frozen=True)
class FxRate:
    currency: str
    profit_currency_per_usd: float
    source_pair: str
    source_broker_date: str
    source_completed_utc: str
    entry_broker_date: str
    staleness_days: int
    coverage: Coverage
    provenance: str
    artifact_sha256: str | None = None
    manifest_sha256: str | None = None


class HistoricalFxRates:
    def __init__(
        self,
        doc: dict,
        source: Path | None = None,
        *,
        artifact_sha256: str | None = None,
        manifest_path: Path | None = None,
        manifest_sha256: str | None = None,
    ):
        if doc.get("schema") != "gtos.costs.historical_fx_d1.v2":
            raise FxConversionError(f"unsupported historical FX schema {doc.get('schema')!r}")
        self.doc = doc
        self.source = source
        self.artifact_sha256 = artifact_sha256
        self.manifest_path = manifest_path
        self.manifest_sha256 = manifest_sha256
        self.coverage = Coverage(doc["coverage"])
        self.max_staleness_seconds = int(doc["max_staleness_seconds"])

    def rate_at(self, currency: str, entry_utc: datetime, *, server: str) -> FxRate:
        if entry_utc.tzinfo is None:
            raise FxConversionError(
                "entry_utc must be timezone-aware for historical FX conversion; a naive "
                "timestamp has no decidable broker trading date"
            )
        block = (self.doc.get("series") or {}).get(currency)
        if block is None:
            raise FxConversionError(
                f"no historical FX conversion series for profit currency {currency!r}; "
                "capture its USD cross before pricing this commission"
            )
        broker_day = utc_to_broker_naive(entry_utc, resolve_rule(server)).date()
        rows = block.get("rows") or []
        completed = [int(r[0]) for r in rows]
        entry_ts = entry_utc.timestamp()
        # Strictly earlier: a close stamped at exactly entry time was not available
        # before the decision and therefore cannot price it.
        pos = bisect.bisect_left(completed, entry_ts) - 1
        if pos < 0:
            raise FxConversionError(
                f"historical FX {block['source_pair']} begins {block['first_broker_date']}, "
                f"after requested broker date {broker_day}; NOT_EVALUABLE"
            )
        completed_ts, source_ordinal, raw_rate = rows[pos]
        staleness_seconds = entry_ts - int(completed_ts)
        if staleness_seconds > self.max_staleness_seconds:
            raise FxConversionError(
                f"historical FX {block['source_pair']} is stale by "
                f"{staleness_seconds / 86400.0:.3f} days at {entry_utc.isoformat()} "
                f"(limit {self.max_staleness_seconds / 86400.0:g}); NOT_EVALUABLE"
            )
        rate = float(raw_rate)
        if not math.isfinite(rate) or rate <= 0:
            raise FxConversionError(
                f"historical FX {block['source_pair']} emitted invalid rate {raw_rate!r}"
            )
        source_day = datetime.fromordinal(int(source_ordinal)).date().isoformat()
        source_completed_utc = datetime.fromtimestamp(
            int(completed_ts), tz=timezone.utc
        ).isoformat()
        return FxRate(
            currency=currency,
            profit_currency_per_usd=rate,
            source_pair=block["source_pair"],
            source_broker_date=source_day,
            source_completed_utc=source_completed_utc,
            entry_broker_date=broker_day.isoformat(),
            staleness_days=int(staleness_seconds // 86400),
            coverage=self.coverage,
            provenance=(
                f"{self.source or DEFAULT_FX_ARTIFACT}:{block['source_pair']} "
                f"D1 close {source_day}, completed_utc="
                f"{source_completed_utc}; "
                f"source sha256 {block['source_sha256']}"
                + (
                    f"; compact artifact sha256 {self.artifact_sha256}; manifest "
                    f"{self.manifest_path} sha256 {self.manifest_sha256}"
                    if self.artifact_sha256 is not None
                    else ""
                )
            ),
            artifact_sha256=self.artifact_sha256,
            manifest_sha256=self.manifest_sha256,
        )


@lru_cache(maxsize=4)
def _parse_verified(
    path_str: str,
    manifest_path_str: str,
    manifest_sha256: str,
    artifact_sha256: str,
    data: bytes,
) -> HistoricalFxRates:
    try:
        with gzip.open(io.BytesIO(data), "rt") as fh:
            doc = json.load(fh)
    except (gzip.BadGzipFile, EOFError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise FxConversionError(
            f"manifest-bound historical FX input at {path_str} is not valid gzip JSON"
        ) from exc
    return HistoricalFxRates(
        doc,
        source=Path(path_str),
        artifact_sha256=artifact_sha256,
        manifest_path=Path(manifest_path_str),
        manifest_sha256=manifest_sha256,
    )


def load_historical_fx(
    path: Path | str | None = None,
    *,
    manifest_path: Path | str | None = None,
    authority_root: Path | str | None = None,
) -> HistoricalFxRates:
    """Load only bytes currently matching the cost-input manifest.

    Verification runs before the parse cache lookup.  A file accepted on one call and
    modified before the next therefore fails closed instead of returning the retained
    object for its old pathname.
    """

    try:
        verified = verify_cost_input(
            "historical_fx",
            path=path,
            manifest_path=manifest_path or DEFAULT_COST_INPUTS_MANIFEST,
            authority_root=authority_root,
        )
    except CostInputAuthorityError as exc:
        raise FxConversionError(str(exc)) from exc
    return _parse_verified(
        str(verified.path),
        str(verified.manifest_path),
        verified.manifest_sha256,
        verified.sha256,
        verified.data,
    )
