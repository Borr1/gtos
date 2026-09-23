# GTOS research infrastructure (Phase 1)
"""Model routing layer for Phase 1 research code.

Background
----------
Phase 1 of the GTOS research program (see
``.context/02_session_handoffs/RESEARCH_PROGRAM_KICKOFF.md``) will run many
ad-hoc analysis scripts: decay diagnostics, regime classification studies,
metadata extraction passes, summary aggregations. Without a centralized
router, each script tends to pick its own model — which is both expensive
and inconsistent. Worse, an inattentive script could accidentally route a
*trading-decision* MSO evaluation through a cheaper model, silently
degrading edge quality.

This module pins the contract:

* **Trading-decision (MSO gate) calls MUST use Sonnet 4.6 effort=max.**
  Empirical evidence (memory ``project_opus_vs_sonnet_p2c.md``):
  CR 38% vs Opus 19%, WR 69.6% vs 60.9%, 4.4× cheaper than Opus. The
  router refuses to let any caller override this entry — attempting to
  do so raises :class:`RouterMisconfigurationError` immediately.
* **Non-trading research tasks** (regime classification, metadata
  extraction, decay analysis prep, summary/aggregation) default to
  Haiku 4.5 with appropriate effort settings.
* **Unknown task types** are NOT silently defaulted; callers must opt in
  to the ``"other"`` task type explicitly to use the conservative Sonnet
  4.6 effort=high fallback.

Scope discipline
----------------
This module is *additive only*. It does not modify
``src/components/primary_analyzer.py`` or ``config/agent_config.yaml`` —
the live trading pipeline continues to read its model pin from
``ai.primary_model`` / ``ai.primary_effort``. The router is consumed only
by research scripts under ``scripts/research/`` and offline analysis
tooling.

Dry-run mode
------------
``ModelRouter(dry_run=True).route(task_type)`` returns the *intended*
``(model_id, effort)`` tuple but logs a ``[DRY-RUN]`` warning indicating
that a live wrapper would have called the returned model. The caller
(harness around ``route()``) is responsible for honoring dry-run by
skipping the live API call — this module never makes API calls itself.

A/B validation gate
-------------------
Before production-routing any task type to Haiku, run the 50-eval A/B
harness in ``scripts/research/haiku_quality_check.py`` against the
fixture set under ``scripts/research/fixtures/`` and confirm the
agreement rate vs Sonnet meets the threshold documented in
``src/research_infra/README.md``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal, Mapping, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Task taxonomy
# ---------------------------------------------------------------------------

#: Closed taxonomy of research-LLM call categories.
#:
#: ``trading_decision``
#:     The MSO-gate call (Component 3A primary analyzer). MUST use
#:     Sonnet 4.6 effort=max. The router rejects any override of this
#:     entry — see :class:`RouterMisconfigurationError`.
#: ``regime_classification``
#:     Labeling H4-swing regime windows (range / trending / etc.) given
#:     features. Haiku is currently a candidate target pending the
#:     50-eval A/B gate.
#: ``metadata_extraction``
#:     Pulling structured fields out of free-text rationale, postmortem
#:     notes, etc. (e.g. "did the model cite XAU D1 direction?").
#: ``decay_analysis``
#:     Summarising/labeling time-sliced trade-outcome cohorts during
#:     decay-diagnostic studies (Phase 1A).
#: ``summary_aggregation``
#:     Aggregating multi-document or multi-trade summaries (e.g.
#:     monthly-decay-monitor narrative, council-output digests).
#: ``other``
#:     Conservative escape hatch. Callers must opt in explicitly.
TaskType = Literal[
    "trading_decision",
    "regime_classification",
    "metadata_extraction",
    "decay_analysis",
    "summary_aggregation",
    "other",
]

#: Authoritative tuple of valid TaskType values. Used to validate
#: routing-table keys + caller-supplied task types.
VALID_TASK_TYPES: tuple[TaskType, ...] = (
    "trading_decision",
    "regime_classification",
    "metadata_extraction",
    "decay_analysis",
    "summary_aggregation",
    "other",
)

# ---------------------------------------------------------------------------
# Model identifiers
# ---------------------------------------------------------------------------

#: Sonnet 4.6 — the production trading-decision model.
#:
#: This must match ``ai.primary_model`` in ``config/agent_config.yaml``.
#: Do not "version-pin" this string to a dated snapshot ID without
#: simultaneously updating the production config — the empirical
#: validation (CR 38%, WR 69.6%) was performed on the alias, and the
#: model_pin layer in ``src/components/model_pin.py`` is responsible for
#: pinning to a specific snapshot at call time.
MODEL_SONNET_4_6: str = "claude-sonnet-4-6"

#: Haiku 4.5 — the cheaper research target.
#:
#: Pinned to the dated snapshot used in early-Phase-1 cost estimates so
#: that A/B test results stay reproducible across model alias updates.
MODEL_HAIKU_4_5: str = "claude-haiku-4-5-20251001"

# ---------------------------------------------------------------------------
# Routing table
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoutingDecision:
    """Result of a routing lookup.

    Attributes
    ----------
    model_id:
        Anthropic model alias / snapshot identifier (e.g.
        ``"claude-sonnet-4-6"`` or ``"claude-haiku-4-5-20251001"``).
    effort:
        Extended-thinking effort level. Validated values used in the
        trading pipeline are ``"low"``, ``"medium"``, ``"high"``,
        ``"max"``. The router does not enforce the closed set — that's
        the caller's responsibility — but the default routing table only
        emits these four values.
    """

    model_id: str
    effort: str


#: Default routing table.
#:
#: ``trading_decision`` is the immutable entry; constructing a
#: :class:`ModelRouter` with a routing table that overrides this entry
#: raises :class:`RouterMisconfigurationError`.
DEFAULT_ROUTING_TABLE: Mapping[TaskType, RoutingDecision] = {
    "trading_decision": RoutingDecision(MODEL_SONNET_4_6, "max"),
    "regime_classification": RoutingDecision(MODEL_HAIKU_4_5, "high"),
    "metadata_extraction": RoutingDecision(MODEL_HAIKU_4_5, "medium"),
    "decay_analysis": RoutingDecision(MODEL_HAIKU_4_5, "high"),
    "summary_aggregation": RoutingDecision(MODEL_HAIKU_4_5, "medium"),
    "other": RoutingDecision(MODEL_SONNET_4_6, "high"),
}

#: The canonical, immutable trading-decision routing entry. Any custom
#: routing table whose ``trading_decision`` value does not match this
#: tuple is rejected at construction time.
_IMMUTABLE_TRADING_DECISION: RoutingDecision = DEFAULT_ROUTING_TABLE[
    "trading_decision"
]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RouterMisconfigurationError(ValueError):
    """Raised when a routing table tampers with the immutable
    ``trading_decision`` entry, omits required keys, or contains
    unknown task types.

    This is a hard-fail by design: a silent default would let a research
    script accidentally route a trading-decision call through Haiku,
    which would silently degrade edge quality.
    """


class UnknownTaskTypeError(ValueError):
    """Raised when :meth:`ModelRouter.route` is called with a value not
    in :data:`VALID_TASK_TYPES`.

    The router never falls back to a default for unknown task types —
    the caller must explicitly request ``"other"`` to use the
    conservative Sonnet fallback.
    """


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


class ModelRouter:
    """Routes research-LLM calls to the appropriate (model, effort) pair.

    Parameters
    ----------
    routing_table:
        Optional override mapping. If provided, it must (a) cover every
        :data:`VALID_TASK_TYPES` key, (b) contain only valid task types,
        and (c) preserve the immutable ``trading_decision`` entry
        bit-exact. Any deviation raises
        :class:`RouterMisconfigurationError`.

        ``None`` (default) and an empty mapping both fall back to
        :data:`DEFAULT_ROUTING_TABLE`.
    dry_run:
        When ``True``, :meth:`route` still returns the intended
        ``RoutingDecision`` but logs a ``[DRY-RUN]`` warning. The
        *caller* (the harness wrapping ``route()``) is responsible for
        actually skipping the live API call — this module never makes
        API calls itself.

    Raises
    ------
    RouterMisconfigurationError
        If ``routing_table`` is malformed (missing keys, unknown task
        types, or trading_decision tampering).

    Notes
    -----
    The router is intentionally tiny: it owns the (model, effort) lookup
    and nothing else. Token-budget enforcement, cost tracking, retry/timeout
    semantics, and dry-run skipping all live in the caller / wrapper layer
    so this module stays trivially testable + free of external deps.
    """

    def __init__(
        self,
        routing_table: Optional[Mapping[TaskType, RoutingDecision]] = None,
        dry_run: bool = False,
    ) -> None:
        # Empty dict is treated identically to None — a no-op override.
        if routing_table is None or len(routing_table) == 0:
            self._table: Mapping[TaskType, RoutingDecision] = dict(
                DEFAULT_ROUTING_TABLE
            )
        else:
            # validate_table raises on any defect — fail fast before any
            # call can reach .route().
            self.validate_table(routing_table)
            self._table = dict(routing_table)
        self._dry_run = bool(dry_run)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, task_type: TaskType) -> tuple[str, str]:
        """Return ``(model_id, effort)`` for the given task type.

        Parameters
        ----------
        task_type:
            One of :data:`VALID_TASK_TYPES`.

        Returns
        -------
        tuple[str, str]
            ``(model_id, effort)`` per the active routing table.

        Raises
        ------
        UnknownTaskTypeError
            If ``task_type`` is not in :data:`VALID_TASK_TYPES`. The
            router never falls back silently.

        Notes
        -----
        In dry-run mode this still returns the intended routing tuple
        but logs a ``[DRY-RUN]`` warning. Honoring dry-run (i.e. NOT
        making the live API call) is the caller's responsibility — the
        harness wrapping ``route()`` should check ``router.dry_run``
        and short-circuit accordingly.
        """
        if task_type not in VALID_TASK_TYPES:
            raise UnknownTaskTypeError(
                f"Unknown task_type {task_type!r}. "
                f"Valid values: {VALID_TASK_TYPES}. "
                "Pass 'other' explicitly if you want the conservative "
                "Sonnet 4.6 effort=high fallback."
            )

        decision = self._table[task_type]
        if self._dry_run:
            logger.warning(
                "[DRY-RUN] Router would route task_type=%r to "
                "model=%r effort=%r — caller is responsible for "
                "skipping the live API call.",
                task_type,
                decision.model_id,
                decision.effort,
            )
        return (decision.model_id, decision.effort)

    @property
    def dry_run(self) -> bool:
        """``True`` if the router was constructed in dry-run mode."""
        return self._dry_run

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_table(
        table: Mapping[TaskType, RoutingDecision],
    ) -> None:
        """Validate a candidate routing table.

        Raises :class:`RouterMisconfigurationError` if any of the
        following hold:

        * ``trading_decision`` is missing or its value does not match
          the immutable ``Sonnet 4.6 effort=max`` entry bit-exact;
        * any required :data:`VALID_TASK_TYPES` key is missing;
        * any key is not a valid :data:`TaskType`;
        * any value is not a :class:`RoutingDecision` instance.

        Returns ``None`` on success.
        """
        if not isinstance(table, Mapping):
            raise RouterMisconfigurationError(
                f"routing_table must be a Mapping, got {type(table).__name__}"
            )

        # 1. Immutable trading_decision — checked FIRST so a tampered
        #    routing table raises with the specific tampering message
        #    rather than a generic missing-key error.
        if "trading_decision" not in table:
            raise RouterMisconfigurationError(
                "routing_table must include 'trading_decision' "
                "(the immutable MSO-gate entry — Sonnet 4.6 effort=max)."
            )
        td = table["trading_decision"]
        if not isinstance(td, RoutingDecision):
            raise RouterMisconfigurationError(
                "routing_table['trading_decision'] must be a "
                f"RoutingDecision, got {type(td).__name__}"
            )
        if (
            td.model_id != _IMMUTABLE_TRADING_DECISION.model_id
            or td.effort != _IMMUTABLE_TRADING_DECISION.effort
        ):
            raise RouterMisconfigurationError(
                "routing_table['trading_decision'] is IMMUTABLE: must "
                f"be {_IMMUTABLE_TRADING_DECISION!r} (Sonnet 4.6 "
                "effort=max). Allowing this to drift would silently "
                "degrade trading edge — see memory "
                "project_opus_vs_sonnet_p2c.md."
            )

        # 2. Unknown task types
        unknown = [k for k in table.keys() if k not in VALID_TASK_TYPES]
        if unknown:
            raise RouterMisconfigurationError(
                f"routing_table contains unknown task_type(s): "
                f"{unknown}. Valid values: {VALID_TASK_TYPES}."
            )

        # 3. Missing required keys
        missing = [k for k in VALID_TASK_TYPES if k not in table]
        if missing:
            raise RouterMisconfigurationError(
                f"routing_table is missing required task_type(s): "
                f"{missing}. All of {VALID_TASK_TYPES} must be present."
            )

        # 4. Value-type sanity (other than trading_decision, already
        #    checked)
        for key, value in table.items():
            if key == "trading_decision":
                continue
            if not isinstance(value, RoutingDecision):
                raise RouterMisconfigurationError(
                    f"routing_table[{key!r}] must be a RoutingDecision, "
                    f"got {type(value).__name__}"
                )


__all__ = [
    "DEFAULT_ROUTING_TABLE",
    "MODEL_HAIKU_4_5",
    "MODEL_SONNET_4_6",
    "ModelRouter",
    "RouterMisconfigurationError",
    "RoutingDecision",
    "TaskType",
    "UnknownTaskTypeError",
    "VALID_TASK_TYPES",
]
