"""Placement idempotency ledger — each (sleeve, symbol, decision_bar) places AT MOST ONCE.

The live launcher ticks repeatedly (polling for new closed bars); without idempotency a book decision
could be placed many times within the same bar. This ledger is the hard guarantee: book_owner checks
`already_placed` before sending and `record`s after a confirmed placement. The book owner owns the
whole book in ONE process (enforced by the run_book single-instance pid-lock), so an in-memory set +
an fsync'd JSONL append is the design.

CROSS-PROCESS DEFENSE-IN-DEPTH: the primary single-process guarantee is the pid-lock. But if two
workers ever co-exist transiently (e.g. a restart race), the in-memory set loaded ONCE at __init__
would be a stale view and could let both place a NEW key. So `already_placed` now incrementally
RE-READS the on-disk ledger (only the bytes appended since last read) before answering, so a key that
the OTHER process just recorded is seen and de-duplicated. This is NOT a full inter-process mutex (a
true sub-millisecond simultaneous check-by-both before either records is still only stopped by the
pid-lock), but it closes the staggered-worker window the 2026-06-15 restart race exposed.

Fail-safe posture: a missing/corrupt ledger NEVER blocks evaluation (worst case a decision is
re-evaluated — the governor's open-risk cap and the broker's existing position still bound exposure).
A failed persist keeps the in-memory dedup for the process lifetime and logs loudly; the launcher also
only runs a cycle on a NEW decision bar, so redundant placement attempts are already minimized.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

REQUIRED_TICKET_PLACEMENT_FIELDS = (
    "sleeve",
    "symbol",
    "decision_bar_iso",
    "decision_day",
    "cluster",
    "candidate_id",
    "ticket",
    "ts",
)
PLACEMENT_CAPTURE_CONTRACT_VERSION = "ticket_candidate_decision_policy_context_v1"
PLACEMENT_CAPTURE_COMPLETE_STATUS = "complete_ticket_candidate_decision_policy_context"
PLACEMENT_CAPTURE_INCOMPLETE_STATUS = "missing_required_ticket_placement_context"


def missing_required_ticket_placement_fields(row: dict[str, Any]) -> list[str]:
    return [
        field
        for field in REQUIRED_TICKET_PLACEMENT_FIELDS
        if row.get(field) in (None, "")
    ]


def annotate_ticket_placement_completeness(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    missing = missing_required_ticket_placement_fields(out)
    out.setdefault("placement_capture_contract_version", PLACEMENT_CAPTURE_CONTRACT_VERSION)
    out["placement_source_missing_fields"] = missing
    out["placement_source_completeness_status"] = (
        PLACEMENT_CAPTURE_COMPLETE_STATUS if not missing else PLACEMENT_CAPTURE_INCOMPLETE_STATUS
    )
    return out


class PlacementLedger:
    def __init__(self, repo_root: str, namespace: str, cluster_resolver=None):
        self._dir = Path(repo_root) / "pipeline_state" / "ultimate_book" / namespace
        self._path = self._dir / "placed_decisions.jsonl"
        # sleeve -> correlation-cluster resolver (admission.cluster_of), so the one-unit-per-cluster-per-day
        # cap can be reconstructed from EVERY row (incl. pre-change rows that lack an explicit cluster).
        self._cluster_resolver = cluster_resolver
        # (cluster, YYYY-MM-DD) -> set of decision_bar_iso it placed on, for the per-(cluster,day) cap that
        # allows ALL members of the SAME bar's unit but blocks a LATER-bar same-cluster re-fire (COMP-2).
        self._cluster_bars: dict[tuple, set] = {}
        self._seen: set[tuple] = set()
        # (sleeve, symbol, YYYY-MM-DD) of every placement, for the per-DAY one-entry cap that enforces the
        # validated one-unit-per-sleeve-per-day model (sleeve-day-reentry-overrisk / COMP-2 same-sleeve):
        # crypto/idxrev are H4 sleeves that can re-fire on a LATER same-day bar after the first closed; the
        # bar-granular _seen would let that place a SECOND full-size unit beyond the validated daily risk.
        self._seen_day: set[tuple] = set()
        self._by_ticket: dict[int, tuple] = {}   # ticket -> (sleeve, symbol) for book-placed adoption recovery
        self._rows_by_ticket: dict[int, dict[str, Any]] = {}
        self._read_pos = 0   # bytes consumed so far (for the incremental cross-process refresh)
        self._load()

    @staticmethod
    def _key(sleeve, symbol, decision_bar_iso) -> tuple:
        return (str(sleeve), str(symbol), str(decision_bar_iso))

    @staticmethod
    def _day_key(sleeve, symbol, decision_day) -> tuple:
        # normalise to a YYYY-MM-DD date so a full decision-bar iso and a bare date both map to the same day.
        return (str(sleeve), str(symbol), str(decision_day or "")[:10])

    def _resolve_cluster(self, sleeve, cluster):
        if cluster:
            return str(cluster)
        if self._cluster_resolver is not None:
            try:
                c = self._cluster_resolver(sleeve)
                return str(c) if c else None
            except Exception:
                return None
        return None

    def _index_cluster(self, sleeve, cluster, decision_day, decision_bar_iso) -> None:
        c = self._resolve_cluster(sleeve, cluster)
        if not c:
            return
        key = (c, str(decision_day or "")[:10])
        self._cluster_bars.setdefault(key, set()).add(str(decision_bar_iso))

    def _ingest(self, fh) -> None:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if r.get("ticket") not in (None, "", 0):
                    r = annotate_ticket_placement_completeness(r)
                self._seen.add(self._key(r.get("sleeve"), r.get("symbol"), r.get("decision_bar_iso")))
                # day key: prefer the explicit decision_day; fall back to the bar iso's date (older rows).
                _day = r.get("decision_day") or r.get("decision_bar_iso")
                self._seen_day.add(self._day_key(r.get("sleeve"), r.get("symbol"), _day))
                self._index_cluster(r.get("sleeve"), r.get("cluster"), _day, r.get("decision_bar_iso"))
                tkt = r.get("ticket")
                if tkt not in (None, 0):
                    ticket_i = int(tkt)
                    self._by_ticket[ticket_i] = (str(r.get("sleeve")), str(r.get("symbol")))
                    self._rows_by_ticket[ticket_i] = dict(r)
            except Exception:
                continue   # skip a corrupt line; never block on the ledger

    def _load(self) -> None:
        try:
            if not self._path.exists():
                return
            with open(self._path, encoding="utf-8") as f:
                self._ingest(f)
                self._read_pos = f.tell()
        except Exception:
            log.warning("placement ledger load failed at %s; starting empty", self._path)

    def _refresh(self) -> None:
        """Cheap incremental re-read: if the file grew (another process appended), ingest only the new
        tail bytes. Never raises (a read error leaves the in-memory view intact)."""
        try:
            if not self._path.exists():
                return
            size = self._path.stat().st_size
            if size <= self._read_pos:
                return   # nothing new (or truncated/rotated -> keep current view)
            with open(self._path, encoding="utf-8") as f:
                f.seek(self._read_pos)
                self._ingest(f)
                self._read_pos = f.tell()
        except Exception:
            pass

    def already_placed(self, sleeve, symbol, decision_bar_iso) -> bool:
        self._refresh()   # catch a key the other (transient) worker just recorded before we place
        return self._key(sleeve, symbol, decision_bar_iso) in self._seen

    def already_placed_today(self, sleeve, symbol, decision_day) -> bool:
        """True if this (sleeve, symbol) ALREADY placed an order on `decision_day` (any bar). Enforces the
        validated one-unit-per-sleeve-per-day model: an H4 sleeve that re-fires on a later same-day bar
        (after its first position closed) must NOT place a second full-size unit. NEVER raises."""
        self._refresh()
        return self._day_key(sleeve, symbol, decision_day) in self._seen_day

    def cluster_placed_today_other_bar(self, cluster, decision_day, decision_bar_iso) -> bool:
        """True if this correlation CLUSTER already placed on a DIFFERENT bar of `decision_day` (COMP-2).
        Allows every member of the SAME bar's unit (admission's correlated unit places one order per member
        on one bar) but blocks a LATER-bar same-cluster re-fire that would stack a 2nd full correlated unit
        beyond the one-unit-per-cluster-per-day envelope the dial was certified on. NEVER raises."""
        self._refresh()
        if not cluster:
            return False
        bars = self._cluster_bars.get((str(cluster), str(decision_day or "")[:10]))
        if not bars:
            return False
        return any(b != str(decision_bar_iso) for b in bars)

    def sleeve_symbol_for_ticket(self, ticket) -> Optional[tuple]:
        """(sleeve, symbol) for a ticket the BOOK durably recorded placing, else None. Lets the owner
        adopt + manage its OWN ledger-recorded position even when a legacy / non-W7 broker comment blocks
        comment-routing (the GER40 'GoldAgent_OBRete' orphan: book-placed by vp_euidx, mislabelled by the
        pre-fix default comment, then unadoptable). NEVER raises."""
        self._refresh()
        try:
            return self._by_ticket.get(int(ticket))
        except (TypeError, ValueError):
            return None

    def row_for_ticket(self, ticket) -> Optional[dict[str, Any]]:
        """Full durable placement row for a book ticket, if known.

        Trade records are the policy authority, while the placement ledger is the idempotency authority.
        Keeping the ledger row indexed by ticket lets a restarted owner backfill legacy trade records with
        the exact decision bar/day/cluster/candidate identifiers that were already fsync'd at placement.
        """
        self._refresh()
        try:
            row = self._rows_by_ticket.get(int(ticket))
            return dict(row) if row is not None else None
        except (TypeError, ValueError):
            return None

    def record(self, sleeve, symbol, decision_bar_iso, *, candidate_id=None,
               ticket=None, ts: Optional[str] = None, decision_day=None, cluster=None,
               require_full_context: bool = False) -> dict[str, Any]:
        """Mark a decision placed. In-memory FIRST (dedups even if the disk write fails), then a
        durable fsync'd append so a launcher restart still sees it."""
        self._seen.add(self._key(sleeve, symbol, decision_bar_iso))
        self._seen_day.add(self._day_key(sleeve, symbol, decision_day or decision_bar_iso))
        resolved_cluster = self._resolve_cluster(sleeve, cluster)
        self._index_cluster(sleeve, resolved_cluster, decision_day or decision_bar_iso, decision_bar_iso)
        row = {"sleeve": sleeve, "symbol": symbol, "decision_bar_iso": decision_bar_iso,
               "decision_day": str(decision_day or decision_bar_iso or "")[:10],
               "cluster": resolved_cluster,
               "candidate_id": candidate_id, "ticket": ticket, "ts": ts}
        if ticket not in (None, "", 0):
            row = annotate_ticket_placement_completeness(row)
            missing = row.get("placement_source_missing_fields") or []
            if require_full_context and missing:
                log.error(
                    "placement ledger capture incomplete for ticket %s (%s/%s@%s): missing=%s",
                    ticket,
                    sleeve,
                    symbol,
                    decision_bar_iso,
                    ",".join(missing),
                )
        if ticket not in (None, 0):
            try:
                ticket_i = int(ticket)
                self._by_ticket[ticket_i] = (str(sleeve), str(symbol))   # in-memory ticket index too
                self._rows_by_ticket[ticket_i] = dict(row)
            except (TypeError, ValueError):
                pass
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
                f.flush()
                os.fsync(f.fileno())
                self._read_pos = f.tell()   # our own append is already in _seen; don't re-ingest it
        except Exception as e:
            log.error("placement ledger PERSIST FAILED for %s/%s@%s (%r); in-memory dedup holds for "
                      "this process but a restart could re-place — investigate disk/perms",
                      sleeve, symbol, decision_bar_iso, e)
        return dict(row)


__all__ = [
    "PLACEMENT_CAPTURE_COMPLETE_STATUS",
    "PLACEMENT_CAPTURE_CONTRACT_VERSION",
    "PLACEMENT_CAPTURE_INCOMPLETE_STATUS",
    "PlacementLedger",
    "REQUIRED_TICKET_PLACEMENT_FIELDS",
    "annotate_ticket_placement_completeness",
    "missing_required_ticket_placement_fields",
]
