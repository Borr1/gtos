"""``InertPolicy`` — a second implementation, so N > 1 is real.

The amendment `FULL_VISION_PLAN.md:201-204` asks for a core hosting **N** policy
modules.  A core with exactly one implementation is not demonstrably general: it
is indistinguishable from that implementation's own call signature, and the next
policy discovers the interface was shaped around the first.

This is the cheapest possible second implementation.  It admits nothing and
sizes nothing, which makes it useful for three concrete jobs beyond proving the
protocol is implementable twice:

* **A null control.** Comparing a policy against ``InertPolicy`` over a window
  measures how much the policy did at all, which is the sanity check that a
  "zero disagreements" result is not zero-because-nothing-ran.
* **A do-nothing baseline.** ``FULL_VISION_PLAN.md`` requires each family to
  beat a baseline; "no trades" is the floor every policy must clear.
* **A shape for gated-off policies.** A policy whose gates are all closed
  behaves like this, so tooling that handles ``InertPolicy`` handles the
  shadow-mode case without a special path.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .core import AccountDayState, PolicyCandidate, PolicyDecision


class InertPolicy:
    """Admits nothing.  Records what it was offered."""

    def __init__(self, policy_id: str = "inert", reason: str = "inert_policy") -> None:
        self._policy_id = str(policy_id)
        self._reason = str(reason)

    @property
    def policy_id(self) -> str:
        return self._policy_id

    def describe(self) -> Mapping[str, Any]:
        return {"policy_id": self._policy_id, "kind": "inert", "reason": self._reason}

    def decide(
        self,
        candidates: Sequence[PolicyCandidate],
        state: AccountDayState,
    ) -> PolicyDecision:
        return PolicyDecision(
            policy_id=self._policy_id,
            new_entries_allowed=False,
            reason=self._reason,
            diagnostics={
                "n_candidates_in": len(candidates),
                # Recorded so a null-control run can prove the candidates
                # reached it — an inert policy that saw nothing and an inert
                # policy that declined everything are different facts.
                "sleeves_offered": sorted({c.sleeve for c in candidates}),
                "account": state.account,
                "namespace": state.namespace,
            },
        )
