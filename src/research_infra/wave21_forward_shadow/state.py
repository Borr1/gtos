"""Append-only logs + idempotent restart state for the forward-shadow runner.

Everything the runner knows is reconstructable from its own JSONL logs:

  * ``decision_packets/YYYY-MM-DD.jsonl`` — one row per decision window with
    every candidate's consumed raw fields, features, prediction, disposition;
  * ``would_be_orders.jsonl`` — one row per selected would-be trade;
  * ``order_outcomes.jsonl`` — one row per FINAL modelled resolution (plus
    optional provisional probes, flagged);
  * ``heartbeat.jsonl`` — one row per cycle.

Resume: open orders = would-be orders without a final outcome row.  Occupancy
= open orders (end = expiry upper bound) plus resolved orders whose occupancy
end is still in the future.  Restart therefore never re-trades an occupied
symbol and never double-opens a tracked order; and because M1 history is
fetchable retroactively, an outage window's pending orders still resolve to
the same modelled terminal after restart.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

from src.research_infra.wave21_forward_shadow.shadow_lifecycle import WouldBeOrder

DECISION_PACKET_DIRNAME = "decision_packets"
WOULD_BE_ORDERS_FILENAME = "would_be_orders.jsonl"
ORDER_OUTCOMES_FILENAME = "order_outcomes.jsonl"
HEARTBEAT_FILENAME = "heartbeat.jsonl"


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # A torn tail line from a hard kill is tolerated (append-only,
                # last line only); anything else in the file is intact JSON.
                continue


class ShadowState:
    def __init__(self, namespace_dir: Path):
        self.namespace_dir = Path(namespace_dir)
        self.decision_packet_dir = self.namespace_dir / DECISION_PACKET_DIRNAME
        self.would_be_orders_path = self.namespace_dir / WOULD_BE_ORDERS_FILENAME
        self.order_outcomes_path = self.namespace_dir / ORDER_OUTCOMES_FILENAME
        self.heartbeat_path = self.namespace_dir / HEARTBEAT_FILENAME

    # -- writes -----------------------------------------------------------
    def write_decision_packet(self, packet: Mapping[str, Any]) -> None:
        day = str(packet.get("trading_day") or "unknown-day")
        _append_jsonl(self.decision_packet_dir / f"{day}.jsonl", packet)

    def write_would_be_order(self, order: WouldBeOrder, *, context: Mapping[str, Any]) -> None:
        _append_jsonl(
            self.would_be_orders_path,
            {
                "schema": "gtos.wave21.forward_shadow.would_be_order.v1",
                **order.to_json(),
                **dict(context),
            },
        )

    def write_order_outcome(
        self, order: WouldBeOrder, resolution: Mapping[str, Any]
    ) -> None:
        _append_jsonl(
            self.order_outcomes_path,
            {
                "schema": "gtos.wave21.forward_shadow.order_outcome.v1",
                "candidate_occurrence_key": order.candidate_occurrence_key,
                "decision_window_id": order.decision_window_id,
                "symbol": order.symbol,
                "origin_family": order.origin_family,
                "lanes": list(order.lanes),
                "scoped_lsr_selected": "scoped_lsr" in order.lanes,
                **dict(resolution),
            },
        )

    def write_heartbeat(self, payload: Mapping[str, Any]) -> None:
        _append_jsonl(self.heartbeat_path, payload)

    # -- resume -----------------------------------------------------------
    def load_open_orders(self) -> list[WouldBeOrder]:
        final_keys = {
            str(row.get("candidate_occurrence_key"))
            for row in _iter_jsonl(self.order_outcomes_path)
            if row.get("final") is True
        }
        open_orders: dict[str, WouldBeOrder] = {}
        for row in _iter_jsonl(self.would_be_orders_path):
            key = str(row.get("candidate_occurrence_key") or "")
            if not key or key in final_keys:
                continue
            try:
                open_orders[key] = WouldBeOrder.from_json(row)
            except (KeyError, TypeError, ValueError):
                continue
        return list(open_orders.values())

    def load_occupancy(
        self, *, now_utc: datetime, lane: str = "general"
    ) -> dict[str, datetime]:
        """Rebuild one lane's symbol occupancy (research strict semantics).

        Orders logged before the dual-lane schema carry no ``lanes`` key and
        count as ``general``.
        """

        occupancy: dict[str, datetime] = {}
        outcomes_by_key: dict[str, dict[str, Any]] = {}
        for row in _iter_jsonl(self.order_outcomes_path):
            if row.get("final") is True:
                outcomes_by_key[str(row.get("candidate_occurrence_key"))] = row
        for row in _iter_jsonl(self.would_be_orders_path):
            key = str(row.get("candidate_occurrence_key") or "")
            symbol = str(row.get("symbol") or "")
            lanes = row.get("lanes") or ["general"]
            if not key or not symbol or lane not in lanes:
                continue
            outcome = outcomes_by_key.get(key)
            if outcome is not None:
                end_text = outcome.get("occupancy_end_utc") or row.get("expiry_utc")
            else:
                end_text = row.get("expiry_utc")
            try:
                end = datetime.fromisoformat(str(end_text).replace("Z", "+00:00"))
            except ValueError:
                continue
            if end.tzinfo is None:
                continue
            end = end.astimezone(timezone.utc)
            if end > now_utc:
                prior = occupancy.get(symbol)
                occupancy[symbol] = max(prior, end) if prior else end
        return occupancy

    def processed_window_ids(self, *, trading_day: str) -> set[str]:
        """Window ids already logged for a day (idempotent cycle skip)."""

        path = self.decision_packet_dir / f"{trading_day}.jsonl"
        return {
            str(row.get("decision_window_id"))
            for row in _iter_jsonl(path)
            if row.get("decision_window_id")
        }
