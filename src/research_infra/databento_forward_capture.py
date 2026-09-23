"""Databento forward-capture request ledger helpers.

The ledger is declarative: it records targeted event-window requests before a
fetch. Fetching remains handled by `scripts/fetch_databento_manifest.py` or a
future active monitoring session with explicit approval/cost caps.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "databento_forward_capture_request_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

DEFAULT_DATASET = "GLBX.MDP3"
DEFAULT_STYPE_IN = "continuous"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_databento_forward_request(
    *,
    request_id: str,
    raw_symbol: str,
    schema: str,
    start_utc: str,
    end_utc: str,
    reason: str,
    expected_fields: list[str],
    expected_cost_usd: float | None = None,
    dataset: str = DEFAULT_DATASET,
    stype_in: str = DEFAULT_STYPE_IN,
    actual_cost_usd: float | None = None,
    cache_path: str | None = None,
    evidence_class: str = "FUTURES_PROXY_TRANSFER",
    status: str = "DECLARED_NOT_FETCHED",
    no_leak_usage_policy: str = "Use only features with timestamps strictly before or at asof_cutoff_utc; never use fetched window to both tune and validate.",
    source_event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now_iso(),
        "request_id": request_id,
        "dataset": dataset,
        "schema": schema,
        "raw_symbol": raw_symbol,
        "stype_in": stype_in,
        "start_utc": start_utc,
        "end_utc": end_utc,
        "reason": reason,
        "expected_fields": expected_fields,
        "expected_cost_usd": expected_cost_usd,
        "actual_cost_usd": actual_cost_usd,
        "cache_path": cache_path,
        "source_event_id": source_event_id,
        "no_leak_usage_policy": no_leak_usage_policy,
        "evidence_class": evidence_class,
        "promotion_verdict": PROMOTION_VERDICT,
        "status": status,
    }


def append_databento_forward_request(row: dict[str, Any], path: str | Path) -> None:
    """Append one request row. Never raises."""
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Databento forward request ledger append failed: %s", exc)


def request_cache_status(row: dict[str, Any]) -> str:
    cache_path = row.get("cache_path")
    if not cache_path:
        return "NO_CACHE_PATH_DECLARED"
    return "CACHE_PRESENT" if Path(cache_path).exists() else "CACHE_MISSING_READY_TO_FETCH"


def build_nas100_default_request_set(
    *,
    event_id: str,
    canonical_close_utc: str,
    start_utc: str,
    end_utc: str,
) -> list[dict[str, Any]]:
    """Return declared NAS100/NQ request rows for the active diagnostic branch."""
    return [
        build_databento_forward_request(
            request_id=f"{event_id}_nq_mbp10",
            raw_symbol="NQ.v.0",
            schema="mbp-10",
            start_utc=start_utc,
            end_utc=end_utc,
            reason="NAS100/NQ depth-thinness forward diagnostic around candidate/context window.",
            expected_fields=[
                "top10_bid_depth",
                "top10_ask_depth",
                "depth10_imbalance",
                "thin_depth10_rate",
                "max_bid_wall",
                "max_ask_wall",
            ],
            source_event_id=event_id,
        ),
        build_databento_forward_request(
            request_id=f"{event_id}_nq_trades",
            raw_symbol="NQ.v.0",
            schema="trades",
            start_utc=start_utc,
            end_utc=end_utc,
            reason="NAS100/NQ signed-flow and trade-intensity diagnostic around candidate/context window.",
            expected_fields=[
                "ts_event",
                "price",
                "size",
                "side_or_aggressor_proxy",
                "trade_count",
            ],
            source_event_id=event_id,
        ),
        build_databento_forward_request(
            request_id=f"{event_id}_nq_mbo_targeted",
            raw_symbol="NQ.v.0",
            schema="mbo",
            start_utc=start_utc,
            end_utc=end_utc,
            reason="Targeted declared MBO window only if MBP10 leaves an explicit queue/add-pull question.",
            expected_fields=[
                "order_id",
                "action",
                "side",
                "price",
                "size",
                "ts_event",
            ],
            source_event_id=event_id,
            status="DECLARED_DEFERRED_UNTIL_MBP10_UNANSWERED_QUEUE_QUESTION",
        ),
    ]
