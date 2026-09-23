"""OD-P1 -- emit-on-change for `position_managed`, with a declared state contract.

Session BD (B2073-B2085). Default OFF; nothing here runs until a config key is flipped.

WHY THE STATE CONTRACT IS THE DELIVERABLE AND THE PERCENTAGE IS NOT

P's OD-P1 quotes a single figure -- *"drops 76.05 % of the stream"* -- and recommends the change
with a 15-minute heartbeat. The change is **irreversible for the window in which it runs**:
packets not emitted are not recoverable, ever, and the corpus is the only live evidence the
programme has. So the number that decides it had better be a property of the design and not of
an unstated choice.

Measured over the 99,112-packet export, the SAME stream compresses by anything from 0.94 % to
96.72 % depending only on which fields count as state:

    state contract                          drop % of position_managed    of whole stream
    ------------------------------------    --------------------------    ---------------
    none (every field is state)                             0.94 %              0.74 %
    top-level `*_checked_at_utc` excluded                  40.14 %             31.87 %
    RECURSIVE `*_checked_at_utc` excluded                  96.72 %             76.79 %

The third line reproduces P's 76.05 % to within 0.7 pp, so P's contract was the recursive one --
but it was never written down, and the obvious implementation is the second line. **A top-level
exclusion list under-delivers by 2.4x while looking deployed**, because `policy_clock_diagnostic`
is a nested dict that embeds its own `checked_at_utc` (59.7 % of rows, 100 % churn). That is the
whole gap between the two, and it is one key one level down.

THE CONTRACT, stated so it can be argued with:

    A `position_managed` packet is a REPEAT if its outcome is byte-identical to the previously
    emitted outcome for the same position AFTER removing every key named `checked_at_utc` or
    ending in `_checked_at_utc`, at any depth.

Those keys are observation instants -- when we looked -- not observations. The measured churn on
`position_managed` is bimodal and the rule falls in the gap: four fields at 100 % churn (all of
them `*_checked_at_utc`, one of them nested), two at 4.86 % (`policy_clock_bars_until_due`,
`policy_clock_elapsed_m15_bars` -- the real bar clock advancing), and every one of the other 98
at or below 0.46 %. There is nothing in between to argue about.

WHAT IS LOST, AND WHAT IS NOT

Suppressed packets are gone. But a suppressed packet is by construction identical to one that was
kept, so what a reader loses is not the state -- it is the *count* of how long the state held. So
every emitted packet carries `emit_on_change_suppressed_before` (how many repeats preceded it) and
`emit_on_change_unchanged_seconds`, which makes the run length recoverable from the compressed log
alone. The cycle summary carries the running total, the same way `packet_rejected` makes a
quarantined packet visible to a reader of the main log.

FAIL OPEN, ALWAYS. Any error decides "emit". A filter that fails closed silently stops the
evidence stream on two funded accounts, which is precisely the failure this module must not have.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from .runtime_learning_packet import stable_hash

_HOP: dict[tuple, dict[str, float | None]] = {}


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _scores(
    cache_key: tuple,
    facts: dict,
    questions: dict[str, str],
    anchors: dict | None = None,
) -> dict[str, float | None]:
    """One nineteen.score per question. Fewer than two anchors does not post."""
    if cache_key in _HOP:
        return dict(_HOP[cache_key])
    payload = {
        str(key): value
        for key, value in dict(facts or {}).items()
        if str(key) not in {"denominator", "other"}
    }
    levels = anchors if isinstance(anchors, dict) else {}
    out = {str(qid): None for qid in questions}
    ask = None
    try:
        from src.judgment.nineteen import score as ask
    except Exception:
        ask = None
    if ask is not None:
        for qid, text in questions.items():
            try:
                out[str(qid)] = _finite(
                    ask(
                        payload,
                        question_id=str(qid),
                        instructions=str(text),
                        anchors=levels.get(str(qid)),
                    )
                )
            except Exception:
                out[str(qid)] = None
    _HOP[cache_key] = dict(out)
    return out

# The only event type this may ever touch. `position_closed`, `breach_flatten`,
# `position_adopted`, `position_management_error` and every `unit_*` event are terminal or
# rare, carry the outcomes the programme is actually measuring, and are never suppressed.
FILTERED_EVENT_TYPE = "position_managed"

DEFAULT_HEARTBEAT_SECONDS = 900  # 15 min, P's recommendation, matched to the measured M15 idle
DEFAULT_STATE_TTL_SECONDS = 86_400  # evict a position not seen for a day; bounds the state dict

STATE_CONTRACT_ID = "position_managed_emit_on_change_v1_recursive_checked_at"


def _is_observation_instant(key: str) -> bool:
    """`checked_at_utc` or `*_checked_at_utc`, which is WHEN WE LOOKED, not what we saw.

    A named rule rather than a hand-picked list, so a new `foo_checked_at_utc` is covered on the
    day it is added. Measured: this rule covers exactly the four 100 %-churn fields on
    `position_managed` (`management_checked_at_utc`, `last_management_checked_at_utc`,
    `policy_clock_checked_at_utc`, and `policy_clock_diagnostic.checked_at_utc`) and nothing else.
    """
    return key == "checked_at_utc" or key.endswith("_checked_at_utc")


def strip_observation_instants(value: Any) -> Any:
    """Recursively drop observation instants. RECURSIVELY is the load-bearing word.

    A top-level-only version of this function compresses the measured corpus by 40.14 % instead of
    96.72 % -- it looks deployed and delivers 2.4x less -- because `policy_clock_diagnostic`
    embeds a `checked_at_utc` one level down.
    """
    if isinstance(value, dict):
        return {
            k: strip_observation_instants(v)
            for k, v in sorted(value.items())
            if not _is_observation_instant(str(k))
        }
    if isinstance(value, (list, tuple)):
        return [strip_observation_instants(v) for v in value]
    return value


def state_digest(outcome: Any) -> str:
    """A stable serialisation of the substantive state of one `position_managed` outcome."""
    return json.dumps(strip_observation_instants(outcome or {}), sort_keys=True, default=str)


def _parse_iso(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class PositionManagedEmitFilter:
    """Decide whether one `position_managed` packet is a repeat. Never raises; fails open.

    Not persisted. A process restart emits the first packet for every open position, which is
    correct -- a fresh process has not established that anything is unchanged.
    """

    def __init__(
        self,
        *,
        heartbeat_seconds: float = DEFAULT_HEARTBEAT_SECONDS,
        state_ttl_seconds: float = DEFAULT_STATE_TTL_SECONDS,
    ) -> None:
        offered_heartbeat = _finite(heartbeat_seconds)
        offered_ttl = _finite(state_ttl_seconds)
        second_levels = []
        if offered_heartbeat is not None:
            second_levels.append(("the offered heartbeat in seconds on this state", offered_heartbeat))
        if offered_ttl is not None:
            second_levels.append(("the offered unseen-position age in seconds on this state", offered_ttl))
        bounds = _scores(
            ("emit_filter", offered_heartbeat, offered_ttl),
            {
                "offered_heartbeat_seconds": offered_heartbeat,
                "offered_state_ttl_seconds": offered_ttl,
            },
            {
                "heartbeat_seconds": (
                    "The score you return is how many seconds of an unchanged position_managed "
                    "state still force one emit. An empty score does not force a heartbeat. Do not send."
                ),
                "state_ttl_seconds": (
                    "The score you return is how many seconds an unseen position stays in the emit filter. "
                    "An empty score does not evict on a clock. Do not send."
                ),
            },
            {
                "heartbeat_seconds": second_levels,
                "state_ttl_seconds": second_levels,
            },
        )
        heartbeat = bounds.get("heartbeat_seconds")
        ttl = bounds.get("state_ttl_seconds")
        self._heartbeat = None if heartbeat is None or heartbeat < 0 else float(heartbeat)
        self._ttl = None if ttl is None or ttl < 0 else float(ttl)
        # key -> {digest, last_emit_at, suppressed_since_emit, last_seen_at}
        self._state: dict[str, dict[str, Any]] = {}
        self.suppressed_total = 0
        self.heartbeat_total = 0

    # -- identity ------------------------------------------------------------------------

    @staticmethod
    def position_key(packet: dict) -> str | None:
        """The position a packet is about. None means "cannot tell" -- which means emit."""
        outcome = packet.get("outcome") if hasattr(packet.get("outcome"), "get") else {}
        for source in (outcome, packet):
            for field in ("ticket_hash_sha256", "ultimate_book_intent_id"):
                value = source.get(field)
                if value not in (None, ""):
                    return f"{field}:{value}"
        sleeve, symbol = outcome.get("sleeve"), outcome.get("symbol")
        if sleeve and symbol:
            return f"sleeve_symbol:{sleeve}/{symbol}"
        return None

    # -- decision ------------------------------------------------------------------------

    def decide(self, packet: dict, *, now: datetime | None = None) -> tuple[bool, dict[str, Any]]:
        """Return (emit, annotations). `annotations` are merged into an EMITTED packet's outcome."""
        try:
            return self._decide(packet, now)
        except Exception:  # noqa: BLE001 - a filter fault must never stop the evidence stream
            return True, {"emit_on_change_status": "filter_error_emitted"}

    def _decide(self, packet: dict, now: datetime | None) -> tuple[bool, dict[str, Any]]:
        if packet.get("event_type") != FILTERED_EVENT_TYPE:
            return True, {}
        key = self.position_key(packet)
        if key is None:
            # An unidentifiable position cannot be shown to be unchanged.
            return True, {"emit_on_change_status": "emitted_unidentifiable_position"}

        at = now or _parse_iso(packet.get("created_at_utc")) or datetime.now(timezone.utc)
        self._evict(at)
        digest = state_digest(packet.get("outcome"))
        prior = self._state.get(key)

        if prior is None or prior.get("digest") != digest:
            suppressed = int(prior.get("suppressed_since_emit", 0)) if prior else 0
            held = self._held_seconds(prior, at)
            self._state[key] = {
                "digest": digest,
                "last_emit_at": at,
                "suppressed_since_emit": 0,
                "last_seen_at": at,
            }
            return True, self._annotate("emitted_state_changed", suppressed, held)

        prior["last_seen_at"] = at
        last_emit = prior.get("last_emit_at")
        if self._heartbeat and last_emit is not None and (at - last_emit).total_seconds() >= self._heartbeat:
            suppressed = int(prior.get("suppressed_since_emit", 0))
            held = self._held_seconds(prior, at)
            prior["last_emit_at"] = at
            prior["suppressed_since_emit"] = 0
            self.heartbeat_total += 1
            return True, self._annotate("emitted_heartbeat", suppressed, held)

        prior["suppressed_since_emit"] = int(prior.get("suppressed_since_emit", 0)) + 1
        self.suppressed_total += 1
        return False, {}

    @staticmethod
    def _held_seconds(prior: dict | None, at: datetime) -> float | None:
        if not prior:
            return None
        last_emit = prior.get("last_emit_at")
        if last_emit is None:
            return None
        return round((at - last_emit).total_seconds(), 3)

    @staticmethod
    def _annotate(status: str, suppressed: int, held: float | None) -> dict[str, Any]:
        """What makes the compression countable rather than merely smaller."""
        out: dict[str, Any] = {
            "emit_on_change_status": status,
            "emit_on_change_state_contract": STATE_CONTRACT_ID,
            "emit_on_change_suppressed_before": suppressed,
        }
        if held is not None:
            out["emit_on_change_unchanged_seconds"] = held
        return out

    def _evict(self, at: datetime) -> None:
        if not self._ttl:
            return
        cutoff = at - timedelta(seconds=self._ttl)
        stale = [k for k, v in self._state.items() if v.get("last_seen_at") is not None and v["last_seen_at"] < cutoff]
        for k in stale:
            self._state.pop(k, None)

    # -- observability -------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        return {
            "state_contract": STATE_CONTRACT_ID,
            "heartbeat_seconds": self._heartbeat,
            "tracked_positions": len(self._state),
            "suppressed_total": self.suppressed_total,
            "heartbeat_total": self.heartbeat_total,
        }


def filter_packets(
    packets: list[dict],
    emit_filter: "PositionManagedEmitFilter | None",
    *,
    now: datetime | None = None,
) -> tuple[list[dict], int]:
    """Apply the filter to a cycle's packets. Returns (kept, suppressed_this_cycle).

    With no filter this is the identity function, which is what default-off means.
    """
    if emit_filter is None:
        return list(packets), 0
    kept: list[dict] = []
    suppressed = 0
    for packet in packets:
        try:
            emit, annotations = emit_filter.decide(packet, now=now)
        except Exception:  # noqa: BLE001
            emit, annotations = True, {}
        if not emit:
            suppressed += 1
            continue
        if annotations and hasattr(packet.get("outcome"), "get"):
            # The packet builder hashes the entire packet before this filter runs.  Any
            # annotation therefore changes the hash material and must be followed by a new
            # hash before GuardedPacketWriter validates it.  Without this step, enabling the
            # filter quarantines every annotated heartbeat/state-change packet.
            original_outcome = dict(packet["outcome"])
            original_hash = packet.get("packet_hash_sha256")
            try:
                packet["outcome"].update(annotations)
                if original_hash not in (None, ""):
                    material = dict(packet)
                    material.pop("packet_hash_sha256", None)
                    packet["packet_hash_sha256"] = stable_hash(
                        material,
                        prefix="runtime_learning_packet",
                    )
            except Exception:  # noqa: BLE001 - annotation failure must fail open
                packet["outcome"] = original_outcome
                if original_hash is None:
                    packet.pop("packet_hash_sha256", None)
                else:
                    packet["packet_hash_sha256"] = original_hash
        kept.append(packet)
    return kept, suppressed
