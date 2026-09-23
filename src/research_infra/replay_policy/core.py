"""The ``Policy`` interface and the decision core that hosts N of them.

Why this file exists
--------------------
`FULL_VISION_PLAN.md:201-204` amends the first audit's ``gtos.core`` design:
the core hosts **N policy modules behind one ``Policy`` interface**, forced by
F1 (`SECOND_AUDIT.md:89-148`) — two decision stacks exist, the sealed replay
measures one, `live_system_of_record.md` declares the other, and no replay
harness exercises the book at all (`AUDIT_STATE.md:203`).  With policy-plural,
"replay measures the thing that trades" holds for either OD-1 outcome.

No prior art: there was no ``Policy`` ABC/Protocol, no ``gtos.core``, and no
Clock/Broker/Sink port module anywhere in ``src/`` or ``scripts/`` before this
file [VERIFIED 2026-07-26].  The interface below is therefore defined here, and
`BroadV4Policy` — extracted from the monolith's evaluator/allocator/finalizer
(`FULL_VISION_PLAN.md:209-210`) — is expected to implement the same protocol.

The data contract
-----------------
Two shapes, on purpose, because the live book has two:

``PolicyCandidate``   pre-size.  What a signal generator emits.
``PolicyAllocation``  post-size.  Carries ``(symbol, side, entry, stop, size,
                      provenance)`` — the trade-intent contract OD-1's addendum
                      fixes for the portfolio layer (`FULL_VISION_PLAN.md:66-69`)
                      so two structurally different signal families can share
                      one gross-risk budget, one governor, one exposure view.

``size`` is expressed as **risk percent of the sizing basis**, not lots.  That
is the live book's own unit (``SizedUnit.risk_pct_per_trade``,
``admission.py:941-951``) and it is deliberate: lot conversion is broker- and
profile-specific, happens downstream in the order router, and E1d measured that
replay "never computes a lot quantity at all" (`AUDIT_STATE.md:97-99`).  A
policy that returned lots would be claiming a fidelity it does not have.

``PolicyUnit`` is retained alongside the allocations because the sleeve book's
risk semantics are *unit*-level, not trade-level: same-cluster same-day
candidates collapse into ONE correlated risk unit whose worst-case simultaneous
stop is the budgeted amount, split across members (``admission.py:1119-1203``).
Flattening that to per-trade sizes alone would discard the correlation structure
the governor's gross cap actually binds on.  A policy with no unit structure
returns one unit per allocation.

What this module deliberately does not do
-----------------------------------------
It performs no arithmetic on risk.  Every number in a ``PolicyDecision`` comes
from the policy implementation, which for ``SleeveBookPolicy`` means it comes
from the live decision path itself.  The core aligns, records and compares; it
never re-derives.  That is the whole basis of the fidelity claim.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

SCHEMA = "gtos.phase2.replay_policy.v1"


class PolicyError(ValueError):
    """A policy could not produce a decision, and refuses to guess one."""


# ---------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PolicyCandidate:
    """One pre-size candidate.  Superset of the live ``TradeIntent``.

    ``sleeve`` is the live book's provenance field and is kept under that name
    rather than generalised, because it is the registry key the confidence
    weight and the correlation cluster are both resolved from
    (``admission.py:1122,1165``).  A policy with no sleeve concept puts its own
    strategy id here; the field means "which component of this policy fired".

    ``stop_dist`` is a PRICE distance and must be > 0 — the live sizer fails the
    whole cluster-day unit closed on a non-positive stop
    (``admission.py:1148-1149``), which is behaviour a faithful port reproduces.

    ``decision_day`` is a *day key*, and which day key it is matters: see
    ``docs/audits/fable5-vision-audit-20260725/phase2/DAY_KEYS_IN_THE_LIVE_BOOK.md``.
    For the sleeve book it is the signal bar's **UTC** date
    (``bar_provider.py:86-88``), which is not the same day as either the sleeve's
    own session grouping or the account's daily-loss reset window.
    """

    sleeve: str
    symbol: str
    direction: int
    decision_day: str
    stop_dist: float
    target_dist: float | None = None
    intra_size: float = 1.0
    entry_ref: float | None = None
    decision_bar_iso: str | None = None
    timeframe: int | None = None
    # advisory, leak-free facts the live overlays read (``admission.py:838-853``)
    ll_impulse: str | None = None
    decision_hour: int | None = None
    vp_loc: str | None = None
    features: Mapping[str, Any] = field(default_factory=dict)

    def provenance(self, policy_id: str) -> dict[str, Any]:
        return {
            "policy_id": policy_id,
            "sleeve": self.sleeve,
            "decision_day": self.decision_day,
            "decision_bar_iso": self.decision_bar_iso,
            "timeframe": self.timeframe,
        }


@dataclass(frozen=True)
class AccountDayState:
    """The account facts a policy may read, and nothing else.

    Mirrors the live ``GovernorState`` (``admission.py:1187-1198``) field for
    field, so ``SleeveBookPolicy`` can hand it straight through without
    reinterpreting anything.  ``max_dd_reference_equity`` of 0.0 means "fall
    back to the trailing high-water", which is the live back-compat rule.

    ``account`` is the allocation-profile side (``"A"``/``"B"``), NOT the
    account identity — the live book keys per-unit risk off it
    (``admission.py:1400``).  ``namespace`` carries the identity, and the two are
    distinct: both live workers run side ``"A"`` under different namespaces
    (``run_book_supervisor.ps1:86-87``).

    ``cycle`` carries the per-cycle facts the *live* engine derives from broker
    I/O — the reactive de-risk state read from closed deals
    (``book_engine.py:124-162``), the persisted running-conviction count
    (``:756-784``), the joint daily gross-cap tightening (``:587-605``).  A
    replay must supply them or it is not replaying the same book.  They live
    here rather than in the policy's constructor because they change every
    cycle, and they are an opaque mapping rather than typed fields because they
    are policy-specific: a policy reads its own keys and ignores the rest.
    """

    equity: float
    high_water: float
    realized_today_pct: float
    open_risk_pct: float
    operator_circuit_breaker: bool = False
    max_dd_reference_equity: float = 0.0
    account: str = "A"
    namespace: str | None = None
    cycle: Mapping[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# outputs
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PolicyUnit:
    """One correlated risk unit as the policy sized it."""

    cluster: str
    members: tuple[str, ...]
    n_trades: int
    confidence: float
    risk_pct_per_trade: float
    unit_risk_pct: float
    sized: bool
    reason: str
    tags: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyAllocation:
    """One post-size trade intent: ``(symbol, side, entry, stop, size, provenance)``."""

    symbol: str
    side: int
    entry: float | None
    stop_dist: float
    size_risk_pct: float
    unit_index: int
    admitted: bool
    reason: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyDecision:
    """What one policy decided on one set of candidates.

    ``new_entries_allowed`` is the governor gate; ``authority`` is separate and
    records whether the decision would have borne real risk.  They are not the
    same question and conflating them is how a shadow run reads as a live one:
    on the live book path ``live_activation_allowed=false`` *suppresses
    placement* while on the V4 path the same flag name *disables a rejection
    gate* — "one flag name, two contradictory meanings"
    (`AUDIT_STATE.md:204-206`).
    """

    policy_id: str
    new_entries_allowed: bool
    reason: str
    units: tuple[PolicyUnit, ...] = ()
    allocations: tuple[PolicyAllocation, ...] = ()
    governor: Mapping[str, Any] | None = None
    authority: Mapping[str, Any] = field(default_factory=dict)
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    @property
    def total_risk_pct(self) -> float:
        return sum(u.unit_risk_pct for u in self.units if u.sized)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "policy_id": self.policy_id,
            "new_entries_allowed": self.new_entries_allowed,
            "reason": self.reason,
            "total_risk_pct": round(self.total_risk_pct, 8),
            "units": [u.as_dict() for u in self.units],
            "allocations": [a.as_dict() for a in self.allocations],
            "governor": dict(self.governor) if self.governor is not None else None,
            "authority": dict(self.authority),
            "diagnostics": dict(self.diagnostics),
        }


# ---------------------------------------------------------------------------
# the interface
# ---------------------------------------------------------------------------
@runtime_checkable
class Policy(Protocol):
    """One decision policy.  The core hosts N of these.

    ``decide`` is the whole contract.  Candidate *generation* is deliberately
    not part of it: the two policy families generate incomparably (daily
    statistical sleeves vs intraday M15 geometry candidates,
    `FULL_VISION_PLAN.md:64-66`) and OD-1's addendum fixes the merge point at
    the portfolio level, not the signal level.  A policy that also generates
    exposes that separately — ``SleeveBookPolicy.generate_from_bars`` — so the
    core never has to know how candidates were produced.

    ``decide`` must be pure with respect to the broker and total with respect to
    its inputs: it returns a ``PolicyDecision`` whose ``new_entries_allowed`` is
    False rather than raising, because the live book "NEVER breaks the live
    path" (``book_engine.py:717``) and a port that raises where the original
    fails closed is not a port.
    """

    @property
    def policy_id(self) -> str: ...

    def describe(self) -> Mapping[str, Any]:
        """Configuration and provenance, for the receipt.  No side effects."""
        ...

    def decide(
        self,
        candidates: Sequence[PolicyCandidate],
        state: AccountDayState,
    ) -> PolicyDecision: ...


class DecisionCore:
    """Hosts N policies and runs each on the same inputs.

    This is the "one decision core" of the amendment.  It is deliberately thin:
    it holds no risk logic, and its only real job is to guarantee that every
    hosted policy sees **identical** candidates and identical account state, so
    that any difference between two policies' decisions is attributable to the
    policies rather than to their inputs.  That guarantee is what makes a
    broad-vs-book comparison meaningful.

    It does not choose between policies.  "broad-only", "W7-only" and
    "combined-at-weights" are configurations to be replayed and compared before
    any freeze (`FULL_VISION_PLAN.md:73-76`); picking one is an owner decision,
    and a core that silently picked would be making it.
    """

    def __init__(self, policies: Sequence[Policy]) -> None:
        ids = [p.policy_id for p in policies]
        if not ids:
            raise PolicyError("decision_core_requires_at_least_one_policy")
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            # Two policies under one id would make the per-policy results
            # unattributable, which defeats the point of hosting both.
            raise PolicyError(f"duplicate_policy_id:{','.join(duplicates)}")
        self._policies: tuple[Policy, ...] = tuple(policies)

    @property
    def policy_ids(self) -> tuple[str, ...]:
        return tuple(p.policy_id for p in self._policies)

    def describe(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "policies": {p.policy_id: dict(p.describe()) for p in self._policies},
        }

    def decide_all(
        self,
        candidates: Sequence[PolicyCandidate],
        state: AccountDayState,
    ) -> dict[str, PolicyDecision]:
        """Run every hosted policy on one immutable input set.

        The candidates are frozen into a tuple before the first policy sees
        them, so a policy that mutated the sequence could not change what the
        next one is asked to decide.
        """

        frozen = tuple(candidates)
        out: dict[str, PolicyDecision] = {}
        for policy in self._policies:
            out[policy.policy_id] = policy.decide(frozen, state)
        return out
