"""GTOS Phase 1 research-infra cost tracker.

Per-call cost tracking wrapper for Anthropic API consumption during the
Phase 2-4 research backtests. Provides:

  - typed CostEntry / CostReport surfaces,
  - persistent JSONL audit log (atomic append + fsync),
  - run-tagged aggregation reading the JSONL back,
  - configurable in-process budget alerts (callback fires when a tagged
    aggregate crosses a USD threshold).

This is RESEARCH infrastructure ONLY. It does NOT modify the production
trading path (``src/llm_backend.py`` / ``src/components/primary_analyzer.py``)
and does NOT enforce ``config.budget.monthly_cap_usd`` — that's an existing
production knob this layer purposely does not touch (per T0.2 brief). The
$50-60 Anthropic-billing balance is the hard cap; CEO disabled
auto-reload (memory ``project_anthropic_billing_auto_reload_disabled``).
This tracker is the audit + early-warning layer above that hard cap.

Usage convention
----------------
``run_tag`` is the audit-grouping key — every research backtest task should
pick a stable tag of the form ``phase1_<task_id>`` (e.g.
``phase1_a1_dumb_baseline``). Aggregating by tag answers "how much did
task A1 cost?" without scanning unrelated logs.

Threading
---------
``log_call`` uses a module-level ``threading.Lock`` plus an ``open(.., 'a')
+ flush + os.fsync`` sequence so concurrent log calls in a single process
do not interleave bytes mid-line. Cross-process safety is provided by POSIX
``O_APPEND`` semantics (Linux/macOS) — JSONL lines are atomic up to PIPE_BUF
on those platforms; Windows uses the file lock and serializes via the
in-process mutex (cross-PID writers on Windows must coordinate externally).

Pricing source
--------------
Pricing values in ``PRICING_USD_PER_MTOK`` reflect Anthropic's public
pricing as cited in the T0.2 brief on 2026-04-26. WebFetch verification
against ``https://claude.com/pricing`` was attempted but blocked by tool
policy in the build run; the constants below carry a clear "as-of 2026-04"
marker so a reviewer can re-verify with one diff. **If Anthropic publishes
revised rates, update ``PRICING_USD_PER_MTOK`` in a separate commit and
re-run the cost-report regression.**
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Pricing table
# ============================================================================
#
# Pricing values: USD per MILLION tokens, as-of 2026-04 (cited in T0.2 brief
# 2026-04-26). Cache pricing is NOT discounted by the batch API. Update this
# table when Anthropic publishes revised pricing — keep the "as-of" date in
# the comment so historical JSONL rows can be reconciled with the rates that
# were in effect when they were written.

PRICING_USD_PER_MTOK: Dict[str, Dict[str, float]] = {
    # Sonnet 4.6 — current production primary model (2026-04).
    "claude-sonnet-4-6": {
        "input": 3.00,
        "output": 15.00,
        "cache_write_5m": 3.75,
        "cache_write_1h": 6.00,
        "cache_read": 0.30,
    },
    # Opus 4.7 — research / heavy-effort runs (2026-04).
    "claude-opus-4-7": {
        "input": 15.00,
        "output": 75.00,
        "cache_write_5m": 18.75,
        "cache_write_1h": 30.00,
        "cache_read": 1.50,
    },
    # Haiku 4.5 — cost-optimization candidate for cheap classification tasks.
    "claude-haiku-4-5": {
        "input": 1.00,
        "output": 5.00,
        "cache_write_5m": 1.25,
        "cache_write_1h": 2.00,
        "cache_read": 0.10,
    },
}

# Batch API discount: 50% off input + output. Cache pricing UNCHANGED.
# (Anthropic batch API pricing as-of 2026-04.)
BATCH_DISCOUNT_INPUT_OUTPUT: float = 0.50

# Cache TTL literal — kept as a string so JSONL rows are self-describing
# and cross-language consumers (e.g. a future R / Julia analysis script)
# don't need to import a Python enum to interpret the field.
CacheTTL = Literal["5m", "1h", "none"]


# ============================================================================
# Typed surfaces
# ============================================================================


@dataclass(frozen=True)
class CostEntry:
    """One API call's usage + computed cost.

    Frozen because once the JSONL row is written, downstream consumers
    must see the same data the writer recorded — mutation here would
    drift from the on-disk audit trail.
    """

    timestamp_iso: str
    run_tag: str
    custom_id: str
    model: str
    is_batch: bool
    cache_ttl: str  # CacheTTL literal at runtime; str at the type system
    usage: Dict[str, int]
    cost_usd_breakdown: Dict[str, float]
    cost_usd_total: float

    def to_jsonl_row(self) -> str:
        """Render this entry as a single JSONL line (no trailing newline)."""
        return json.dumps(
            {
                "timestamp_iso": self.timestamp_iso,
                "run_tag": self.run_tag,
                "custom_id": self.custom_id,
                "model": self.model,
                "is_batch": self.is_batch,
                "cache_ttl": self.cache_ttl,
                "usage": self.usage,
                "cost_usd_breakdown": self.cost_usd_breakdown,
                "cost_usd_total": self.cost_usd_total,
            },
            ensure_ascii=False,
            sort_keys=False,
        )

    @classmethod
    def from_jsonl_row(cls, raw: str) -> "CostEntry":
        d = json.loads(raw)
        return cls(
            timestamp_iso=d["timestamp_iso"],
            run_tag=d["run_tag"],
            custom_id=d.get("custom_id", ""),
            model=d["model"],
            is_batch=bool(d.get("is_batch", False)),
            cache_ttl=d.get("cache_ttl", "none"),
            usage=dict(d.get("usage", {})),
            cost_usd_breakdown=dict(d.get("cost_usd_breakdown", {})),
            cost_usd_total=float(d["cost_usd_total"]),
        )


@dataclass
class CostReport:
    """Aggregate of CostEntries for a single run_tag (and optional time slice)."""

    run_tag: str
    n_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cache_read_tokens: int
    total_cache_write_tokens: int
    total_usd: float
    per_model: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    start_iso: Optional[str] = None
    end_iso: Optional[str] = None


# ============================================================================
# Errors
# ============================================================================


class UnknownModelError(KeyError):
    """Raised when ``log_call`` receives a ``model`` not present in the
    pricing table.

    Silent fallback would mask cost-attribution bugs (a typo in a research
    script's model_id could route an Opus run to the Haiku price column);
    the audit trail must fail loudly.
    """


# ============================================================================
# Pricing math (pure)
# ============================================================================


def _pricing_for(model: str, pricing_table: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    if model not in pricing_table:
        known = ", ".join(sorted(pricing_table.keys())) or "(empty pricing table)"
        raise UnknownModelError(
            f"Unknown model {model!r} — not in pricing table. "
            f"Known: {known}. "
            f"Add this model to PRICING_USD_PER_MTOK with its "
            f"per-million-token rates before logging calls."
        )
    return pricing_table[model]


def _normalize_usage(usage: Dict[str, Any]) -> Dict[str, int]:
    """Pull the four token counts the cost math cares about; coerce to ints.

    Accepts the Anthropic SDK's native ``usage`` shape:
        - input_tokens
        - output_tokens
        - cache_read_input_tokens
        - cache_creation_input_tokens (5-minute TTL by default)

    Optional fields preserved if present:
        - cache_creation.ephemeral_5m_input_tokens
        - cache_creation.ephemeral_1h_input_tokens
    """

    def _coerce(val: Any) -> int:
        try:
            return int(val) if val is not None else 0
        except (TypeError, ValueError):
            return 0

    return {
        "input_tokens": _coerce(usage.get("input_tokens")),
        "output_tokens": _coerce(usage.get("output_tokens")),
        "cache_read_input_tokens": _coerce(usage.get("cache_read_input_tokens")),
        "cache_creation_input_tokens": _coerce(usage.get("cache_creation_input_tokens")),
    }


def compute_cost(
    *,
    model: str,
    usage: Dict[str, Any],
    is_batch: bool,
    cache_ttl: str,
    pricing_table: Dict[str, Dict[str, float]] = PRICING_USD_PER_MTOK,
) -> Tuple[Dict[str, float], float, Dict[str, int]]:
    """Compute the four-component cost breakdown for one API call.

    Returns
    -------
    (breakdown, total, normalized_usage)
        ``breakdown`` keys: ``input``, ``output``, ``cache_write``, ``cache_read``.
        ``total`` = sum(breakdown.values()).
        ``normalized_usage`` echoes the four cost-relevant token counts
        used in the math (so the JSONL row is self-explanatory).

    Raises
    ------
    UnknownModelError if ``model`` is not in ``pricing_table``.
    ValueError if ``cache_ttl`` is not one of "5m"/"1h"/"none".
    """
    if cache_ttl not in ("5m", "1h", "none"):
        raise ValueError(
            f"cache_ttl must be '5m', '1h', or 'none'; got {cache_ttl!r}"
        )

    pricing = _pricing_for(model, pricing_table)
    norm = _normalize_usage(usage)

    # Per-MTok → per-token: divide the table value by 1_000_000.
    PER_TOKEN = 1_000_000.0

    # Input / output: discounted under the batch API.
    discount = BATCH_DISCOUNT_INPUT_OUTPUT if is_batch else 1.0
    input_cost = (norm["input_tokens"] * pricing["input"] / PER_TOKEN) * discount
    output_cost = (norm["output_tokens"] * pricing["output"] / PER_TOKEN) * discount

    # Cache write: priced by TTL; "none" → zero (no cache_creation tokens).
    if cache_ttl == "5m":
        write_rate = pricing["cache_write_5m"]
    elif cache_ttl == "1h":
        write_rate = pricing["cache_write_1h"]
    else:  # "none"
        write_rate = 0.0
    cache_write_cost = norm["cache_creation_input_tokens"] * write_rate / PER_TOKEN

    # Cache read: same rate regardless of TTL or batch.
    cache_read_cost = norm["cache_read_input_tokens"] * pricing["cache_read"] / PER_TOKEN

    breakdown = {
        "input": round(input_cost, 8),
        "output": round(output_cost, 8),
        "cache_write": round(cache_write_cost, 8),
        "cache_read": round(cache_read_cost, 8),
    }
    total = round(sum(breakdown.values()), 8)
    return breakdown, total, norm


# ============================================================================
# Tracker
# ============================================================================


# Module-level lock guards concurrent in-process appends. Path-specific
# locking is unnecessary because the file open()/write/fsync sequence
# is already serial under this lock; cross-process writers should set
# ``CostTracker(log_path=...)`` to disjoint paths or coordinate externally.
_LOG_LOCK = threading.Lock()


class CostTracker:
    """Append-only cost log + run-tagged aggregation + budget alerts.

    Each ``log_call`` resolves the cost, writes one JSONL row, and
    (if a budget alert is registered for the row's ``run_tag``) re-aggregates
    that tag and fires the callback when the threshold is crossed.

    The aggregator reads the JSONL back rather than maintaining an in-memory
    cumulative — this is the audit-of-record discipline. The cost of one
    aggregation read is dwarfed by the API latency of the call that
    triggered it (log lines are ~300 bytes; 10k calls is ~3 MB).
    """

    def __init__(
        self,
        log_path: Path | str = Path("shadow_logs/research_cost.jsonl"),
        pricing_table: Dict[str, Dict[str, float]] = PRICING_USD_PER_MTOK,
    ):
        self.log_path = Path(log_path)
        self.pricing_table = pricing_table
        # Budget alerts keyed by run_tag → (threshold_usd, callback, fired_flag)
        # ``fired`` flips True the first time the threshold is crossed so the
        # callback isn't re-fired on every subsequent log_call.
        self._budgets: Dict[str, Tuple[float, Callable[[CostReport], None], List[bool]]] = {}
        self._budget_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def log_call(
        self,
        model: str,
        usage: Dict[str, Any],
        run_tag: str,
        custom_id: str = "",
        is_batch: bool = False,
        cache_ttl: str = "none",
    ) -> CostEntry:
        """Compute cost for one API call, persist it, and check budgets.

        Args:
            model: Model id matching a key in ``self.pricing_table``.
                Unknown models raise ``UnknownModelError`` — there is no
                silent fallback (a typo would mis-attribute cost).
            usage: Dict-like view of the SDK ``usage`` block. Accepts
                ``input_tokens``, ``output_tokens``,
                ``cache_read_input_tokens``, ``cache_creation_input_tokens``.
                Missing keys are treated as 0; non-numeric values coerced
                to 0 with no warning (research-infra fail-open).
            run_tag: Aggregation key. Convention: ``phase1_<task_id>``.
            custom_id: Optional cross-system correlation id (e.g. batch
                API custom_id, or candidate_id from primary_analyzer).
            is_batch: True for batch-API calls (50% input/output discount).
            cache_ttl: "5m" / "1h" / "none". Affects cache_write rate.

        Returns:
            The constructed CostEntry (already persisted).

        Raises:
            UnknownModelError: model not in pricing_table.
            ValueError: cache_ttl not one of "5m"/"1h"/"none".
            OSError: parent directory not writeable / disk full / etc.
                (research-infra; failures must surface, not be swallowed.)
        """
        breakdown, total, norm_usage = compute_cost(
            model=model,
            usage=usage,
            is_batch=is_batch,
            cache_ttl=cache_ttl,
            pricing_table=self.pricing_table,
        )

        entry = CostEntry(
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            run_tag=run_tag,
            custom_id=custom_id,
            model=model,
            is_batch=is_batch,
            cache_ttl=cache_ttl,
            usage=norm_usage,
            cost_usd_breakdown=breakdown,
            cost_usd_total=total,
        )

        self._append_jsonl(entry)
        self._check_budget(run_tag)
        return entry

    def _append_jsonl(self, entry: CostEntry) -> None:
        """Atomically append ``entry`` as one JSONL line.

        Sequence:
          1. Acquire module lock (serializes in-process writers).
          2. Ensure parent dir exists.
          3. open('a', encoding='utf-8'), write line + '\\n', flush().
          4. os.fsync(fd) so a process kill doesn't lose the row.
          5. Close (context manager).
        """
        line = entry.to_jsonl_row() + "\n"
        with _LOG_LOCK:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except (OSError, AttributeError):  # noqa: BLE001
                    # Some test filesystems (and pytest tmpfs on some CI runners)
                    # don't support fsync. The flush above plus the close are
                    # sufficient for unit-test atomicity; production runs on
                    # disk-backed paths where fsync succeeds.
                    pass

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def _iter_entries(self) -> Iterable[CostEntry]:
        if not self.log_path.exists():
            return
        with open(self.log_path, "r", encoding="utf-8") as f:
            for ln, raw in enumerate(f, start=1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    yield CostEntry.from_jsonl_row(raw)
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    logger.warning(
                        "cost_tracker: skipped malformed JSONL row at %s:%d (%s)",
                        self.log_path,
                        ln,
                        exc,
                    )
                    continue

    def aggregate(
        self,
        run_tag: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> CostReport:
        """Aggregate persisted CostEntries matching ``run_tag``.

        Args:
            run_tag: Filter — only rows whose ``run_tag`` exactly matches.
            since: Inclusive lower bound on ``timestamp_iso``. Pass a
                timezone-aware ``datetime``; naive datetimes are treated
                as UTC.
            until: Exclusive upper bound (same parse rules).

        Returns:
            CostReport with totals + per-model breakdown.
        """
        since_aware = _ensure_aware(since)
        until_aware = _ensure_aware(until)

        n_calls = 0
        total_input = 0
        total_output = 0
        total_cache_read = 0
        total_cache_write = 0
        total_usd = 0.0
        per_model: Dict[str, Dict[str, Any]] = {}
        first_iso: Optional[str] = None
        last_iso: Optional[str] = None

        for entry in self._iter_entries():
            if entry.run_tag != run_tag:
                continue
            try:
                ts = datetime.fromisoformat(entry.timestamp_iso)
            except ValueError:
                logger.warning(
                    "cost_tracker: skipping row with unparseable "
                    "timestamp_iso=%r in %s",
                    entry.timestamp_iso,
                    self.log_path,
                )
                continue
            ts_aware = ts if ts.tzinfo is not None else ts.replace(tzinfo=timezone.utc)

            if since_aware is not None and ts_aware < since_aware:
                continue
            if until_aware is not None and ts_aware >= until_aware:
                continue

            n_calls += 1
            total_input += int(entry.usage.get("input_tokens", 0))
            total_output += int(entry.usage.get("output_tokens", 0))
            total_cache_read += int(entry.usage.get("cache_read_input_tokens", 0))
            total_cache_write += int(entry.usage.get("cache_creation_input_tokens", 0))
            total_usd += float(entry.cost_usd_total)

            mb = per_model.setdefault(
                entry.model,
                {
                    "n_calls": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cache_read_tokens": 0,
                    "total_cache_write_tokens": 0,
                    "total_usd": 0.0,
                },
            )
            mb["n_calls"] += 1
            mb["total_input_tokens"] += int(entry.usage.get("input_tokens", 0))
            mb["total_output_tokens"] += int(entry.usage.get("output_tokens", 0))
            mb["total_cache_read_tokens"] += int(entry.usage.get("cache_read_input_tokens", 0))
            mb["total_cache_write_tokens"] += int(entry.usage.get("cache_creation_input_tokens", 0))
            mb["total_usd"] += float(entry.cost_usd_total)

            if first_iso is None or entry.timestamp_iso < first_iso:
                first_iso = entry.timestamp_iso
            if last_iso is None or entry.timestamp_iso > last_iso:
                last_iso = entry.timestamp_iso

        # Round per-model + total at the end so we don't accumulate float
        # rounding error inside the loop.
        for mb in per_model.values():
            mb["total_usd"] = round(mb["total_usd"], 6)

        return CostReport(
            run_tag=run_tag,
            n_calls=n_calls,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_cache_read_tokens=total_cache_read,
            total_cache_write_tokens=total_cache_write,
            total_usd=round(total_usd, 6),
            per_model=per_model,
            start_iso=first_iso,
            end_iso=last_iso,
        )

    # ------------------------------------------------------------------
    # Budget alerts
    # ------------------------------------------------------------------

    def set_budget_alert(
        self,
        run_tag: str,
        budget_usd: float,
        callback: Callable[[CostReport], None],
    ) -> None:
        """Register a budget alert for ``run_tag``.

        The first ``log_call`` whose post-aggregate ``total_usd`` exceeds
        ``budget_usd`` invokes ``callback(report)``. The callback fires
        AT MOST ONCE per registration — re-registering with a higher
        threshold resets the fired flag.

        ``callback`` runs synchronously on the logging thread. Exceptions
        raised by the callback ARE re-raised (the caller asked for an
        in-process budget signal; swallowing the exception would defeat
        the alert).
        """
        if budget_usd <= 0:
            raise ValueError(f"budget_usd must be > 0; got {budget_usd!r}")
        with self._budget_lock:
            self._budgets[run_tag] = (float(budget_usd), callback, [False])

    def clear_budget_alert(self, run_tag: str) -> None:
        with self._budget_lock:
            self._budgets.pop(run_tag, None)

    def _check_budget(self, run_tag: str) -> None:
        """Re-aggregate ``run_tag`` and fire the callback if threshold crossed."""
        with self._budget_lock:
            entry = self._budgets.get(run_tag)
        if entry is None:
            return
        threshold, callback, fired_flag = entry
        if fired_flag[0]:
            return  # already alerted for this tag

        report = self.aggregate(run_tag)
        if report.total_usd >= threshold:
            # Set the flag BEFORE invoking — if the callback raises, the
            # alert still won't re-fire on the next log call (caller can
            # clear_budget_alert to reset).
            with self._budget_lock:
                fired_flag[0] = True
            callback(report)


# ============================================================================
# Helpers
# ============================================================================


def _ensure_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Coerce a naive datetime to UTC; pass through tz-aware unchanged."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
