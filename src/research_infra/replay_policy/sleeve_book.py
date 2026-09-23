"""``SleeveBookPolicy`` — the live ``ultimate_book`` W7 book, behind ``Policy``.

The one design decision that matters
------------------------------------
This module **re-implements no arithmetic**.  It converts the core's data
contract into the live book's own types, calls
``ultimate_book.bridge.evaluate_vnext_ultimate_book_admission`` — the exact
function ``book_engine.py:741-746`` calls in production — and converts the
result back.

That is deliberate, and it is the whole point.  `SESSION_H` asks for the live
semantics "exactly, including the parts that look wrong", because a policy that
silently improved on the book would stop being a measurement of the book and
would reopen F1 rather than close it.  A hand-port of ~450 lines of sizing
arithmetic *cannot* be exactly faithful for long: the live code changes (it
changed twice in the week this was written — B29 Part 1, B56/B58) and a copy
drifts silently.  Delegation makes fidelity structural instead of clerical, and
it converts the fidelity question from "did I copy 40 constants correctly?" into
the far smaller and answerable "what does the adapter have to supply that live
gets from the broker?".

Those supplied inputs are the entire divergence surface, they are enumerated in
``ADAPTER_DIVERGENCES`` below, and every one of them is reported in the
decision's ``diagnostics`` so a receipt cannot claim fidelity while silently
missing one.  This is the "replay does not measure the live system" problem (H7)
reduced from a whole architecture to a list of six inputs.

What is *not* delegated, and why
--------------------------------
1. **Placement gates.** ``book_owner.py:1564-1749`` applies fifteen further
   per-intent gates after sizing (ledger idempotency, the one-unit-per-cluster
   cap, tick staleness, spread screen, lateness).  Those are *placement*, not
   *decision*, and they need a broker tick and a durable ledger.  The policy
   exposes them separately (``PLACEMENT_GATES``) and does not pretend to apply
   them; ``validation.py`` compares against ``would_units``, which is the live
   book's own pre-placement decision, so the comparison is like-for-like.
2. **Candidate generation.** ``generate_from_bars`` calls the live sleeve
   generators, but it is not part of the ``Policy`` protocol — see ``core.py``.
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from .core import (
    AccountDayState,
    PolicyAllocation,
    PolicyCandidate,
    PolicyDecision,
    PolicyError,
    PolicyUnit,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    # Import the live package as ``src.components.ultimate_book`` so this is the
    # SAME module object the production engine imports, not a second copy under
    # a different name with its own module-level DEFAULT_LIMITS.
    sys.path.insert(0, str(_REPO_ROOT))

from src.components.ultimate_book import admission as _P  # noqa: E402
from src.components.ultimate_book.bridge import (  # noqa: E402
    DEFAULT_CONFIG as _BRIDGE_DEFAULT_CONFIG,
    evaluate_vnext_ultimate_book_admission,
)

POLICY_ID = "sleeve_book_w7"

#: Every input the live engine derives from broker I/O that this adapter must be
#: given.  Each is a place a replay can silently differ from live, so each is
#: named, and ``decide()`` records whether it was supplied.
ADAPTER_DIVERGENCES: tuple[tuple[str, str], ...] = (
    (
        "limits",
        "GovernorLimits, including derisk_mode and the joint daily gross-cap "
        "tightening the engine computes from realized daily loss "
        "(book_engine.py:549-605). Absent => the config block's own limits, with "
        "no daily tightening.",
    ),
    (
        "stress_state",
        "StressDeriskState from 192h of closed broker deals "
        "(book_engine.py:124-162). Absent => neutral (no de-risk), which is what "
        "live does on a mock broker but NOT what live does on the real one.",
    ),
    (
        "n_active_override",
        "Persisted running per-day distinct-firing-sleeve count "
        "(running_conviction_state.py:60-82). Absent => the per-cycle count only, "
        "which under-sizes relative to live whenever a day spans cycles.",
    ),
    (
        "symbol_damage_metrics",
        "Trailing realized per-symbol damage metrics. Absent => guard inert. "
        "NOTE: the live engine never passes these either "
        "(book_engine.py:741-746), so absent IS live-faithful.",
    ),
    (
        "open_risk_pct",
        "Sum of worst-case-stop risk over open broker positions "
        "(book_engine.py:619-652). Replay must model open positions to get the "
        "4% gross cap to bind at the same point.",
    ),
    (
        "day_start_balance",
        "Reconstructed start-of-reset-window balance, which sets "
        "realized_today_pct (governor_state.py:172-212). Its day boundary is the "
        "ACCOUNT's reset rule, not UTC and not the decision day.",
    ),
)

#: The post-decision placement gates this policy does NOT apply, in live order.
#: Listed so a caller can see exactly what a decision-level comparison omits.
PLACEMENT_GATES: tuple[str, ...] = (
    "profile_missing_instrument_config",
    "ai_companion_cooldown",
    "already_placed_this_bar",
    "already_placed_today",
    "cluster_unit_already_placed_today",
    "ai_companion_zero_risk",
    "no_tick_transient",
    "stale_tick_market_closed",
    "sleeve_already_holds_symbol",
    "sleeve_already_holds_symbol_broker",
    "same_broker_symbol_already_placed_this_cycle",
    "same_broker_symbol_attempted_transient_this_cycle",
    "same_broker_symbol_open_position_lifecycle_guard",
    "stale_late_entry_after_restart",
    "spread_cost_screen",
)


def _to_trade_intent(candidate: PolicyCandidate) -> Any:
    """``PolicyCandidate`` -> the live ``TradeIntent``.

    Feature fields are passed through by name because the A8 metals confluence
    gate reads them off the intent (``admission.py:1095-1096``); an unknown
    feature key is dropped rather than passed, since ``TradeIntent`` is frozen
    with a fixed field set and a stray kwarg would raise where live would not.
    """

    kwargs: dict[str, Any] = {
        "sleeve": candidate.sleeve,
        "symbol": candidate.symbol,
        "direction": candidate.direction,
        "decision_day": candidate.decision_day,
        "stop_dist": candidate.stop_dist,
        "target_dist": candidate.target_dist,
        "intra_size": candidate.intra_size,
        "ll_impulse": candidate.ll_impulse,
        "decision_hour": candidate.decision_hour,
        "vp_loc": candidate.vp_loc,
    }
    allowed = set(getattr(_P.TradeIntent, "__dataclass_fields__", {}))
    for key, value in (candidate.features or {}).items():
        if key in allowed and key not in kwargs:
            kwargs[key] = value
    return _P.TradeIntent(**{k: v for k, v in kwargs.items() if k in allowed})


def _governor_state(state: AccountDayState) -> Any:
    return _P.GovernorState(
        equity=state.equity,
        high_water=state.high_water,
        realized_today_pct=state.realized_today_pct,
        open_risk_pct=state.open_risk_pct,
        operator_circuit_breaker=state.operator_circuit_breaker,
        max_dd_reference_equity=state.max_dd_reference_equity,
    )


def _unit_from_live(raw: Mapping[str, Any]) -> PolicyUnit:
    return PolicyUnit(
        cluster=str(raw.get("cluster", "")),
        members=tuple(raw.get("sleeve_members", ()) or ()),
        n_trades=int(raw.get("n_trades", 0) or 0),
        confidence=float(raw.get("confidence", 0.0) or 0.0),
        risk_pct_per_trade=float(raw.get("risk_pct_per_trade", 0.0) or 0.0),
        unit_risk_pct=float(raw.get("unit_risk_pct", 0.0) or 0.0),
        sized=bool(raw.get("sized", False)),
        reason=str(raw.get("reason", "")),
        tags=tuple(raw.get("overlays_applied", ()) or ()),
    )


class SleeveBookPolicy:
    """The live W7 sleeve book as a ``Policy``.

    Parameters
    ----------
    config:
        The ``gtos_vnext_runtime`` block, i.e. the merged profile+base config the
        live worker runs on — **not** ``bridge.DEFAULT_CONFIG``.  This matters:
        the bridge defaults differ from the live YAML on two safety-critical
        keys (``ultimate_book_profile`` 1.25 % vs live 2.00 %, ``bridge.py:72``;
        ``derisk_mode`` ``"band"`` vs live ``"smooth"``, ``bridge.py:87``), so a
        replay that fell back to them would size a different book and would
        trip the ceiling interlock.  ``strict_config=True`` refuses a config
        that is missing the keys that decide the dial, rather than defaulting
        them.
    account:
        The allocation-profile side.  The live engine hard-wires ``"A"``
        (``book_engine.py:75``, never overridden by ``book_owner.py:151-152``),
        so ``"A"`` is the faithful value for both live namespaces.
    """

    #: Keys whose absence changes the sized book.  Checked under strict_config.
    DIAL_KEYS: tuple[str, ...] = (
        "ultimate_book_profile",
        "ultimate_book_derisk_mode",
        "ultimate_book_include_clean3",
        "ultimate_book_include_candidate_book",
        "ultimate_book_include_market_expansion_book",
        "ultimate_book_kelly_lite",
        "ultimate_book_kelly_conservative",
        "ultimate_book_stress_derisk",
        "ultimate_book_drop_w7_symbols",
    )

    #: Keys that CHANGE the sized book but whose ABSENCE does not, so `strict_config` must not
    #: require them -- every existing caller predates them and their off-value IS the live book.
    #: They are still reported by `describe()`: a replay that armed one of these and described
    #: itself identically to one that did not would be an audit-trail hole, which is exactly the
    #: silent-improvement failure this module exists to avoid.
    REPORTED_ONLY_KEYS: tuple[str, ...] = (
        "ultimate_book_vol_level_tilt",   # WAVE-11 vol-level sizing tilt (Session AR)
    )

    def __init__(
        self,
        config: Mapping[str, Any],
        *,
        account: str = "A",
        strict_config: bool = True,
        policy_id: str = POLICY_ID,
    ) -> None:
        if not isinstance(config, Mapping):
            raise PolicyError("sleeve_book_config_must_be_a_mapping")
        if strict_config:
            missing = [k for k in self.DIAL_KEYS if k not in config]
            if missing:
                raise PolicyError(
                    "sleeve_book_config_missing_dial_keys:" + ",".join(missing)
                )
        self._config = dict(config)
        self._account = str(account)
        self._policy_id = str(policy_id)

    # -- Policy protocol ---------------------------------------------------
    @property
    def policy_id(self) -> str:
        return self._policy_id

    def describe(self) -> Mapping[str, Any]:
        """Configuration and provenance.  Reports the dial, not a summary of it."""

        return {
            "policy_id": self._policy_id,
            "kind": "ultimate_book_w7",
            "delegates_to": (
                "src.components.ultimate_book.bridge."
                "evaluate_vnext_ultimate_book_admission"
            ),
            "account": self._account,
            "dial": {k: self._config.get(k)
                     for k in (self.DIAL_KEYS + self.REPORTED_ONLY_KEYS)},
            "adapter_divergences": [name for name, _ in ADAPTER_DIVERGENCES],
            "placement_gates_not_applied": list(PLACEMENT_GATES),
            "day_key": "bar_provider.decision_day_of (signal bar UTC date)",
        }

    def decide(
        self,
        candidates: Sequence[PolicyCandidate],
        state: AccountDayState,
    ) -> PolicyDecision:
        """Delegate to the live decision path and map the result back.

        Never raises: the live book "NEVER breaks the live path"
        (``book_engine.py:717``), so an adapter failure fails closed with a
        reason instead of propagating.
        """

        cycle = dict(state.cycle or {})
        intents = [_to_trade_intent(c) for c in candidates]
        limits = cycle.get("limits")
        supplied = {
            "limits": limits is not None,
            "stress_state": cycle.get("stress_state") is not None,
            "n_active_override": cycle.get("n_active_override") is not None,
            "symbol_damage_metrics": cycle.get("symbol_damage_metrics") is not None,
        }
        try:
            decision = evaluate_vnext_ultimate_book_admission(
                config={"gtos_vnext_runtime": self._config},
                intents=intents,
                governor_state=_governor_state(state),
                account=self._account,
                limits=limits if limits is not None else self._limits_from_config(),
                n_active_override=cycle.get("n_active_override"),
                stress_state=cycle.get("stress_state"),
                symbol_damage_metrics=cycle.get("symbol_damage_metrics"),
            )
        except Exception as exc:  # noqa: BLE001 — see docstring
            return PolicyDecision(
                policy_id=self._policy_id,
                new_entries_allowed=False,
                reason=f"adapter_failed_closed:{type(exc).__name__}:{exc}",
                diagnostics={"cycle_inputs_supplied": supplied},
            )
        return self._to_policy_decision(decision, candidates, supplied)

    # -- helpers -----------------------------------------------------------
    def _limits_from_config(self) -> Any:
        """``GovernorLimits`` from the config block.

        Mirrors ``book_engine._governor_limits`` (``:549-585``) for the fields
        the config carries, and deliberately does NOT apply the joint daily
        tightening (``:587-605``) — that needs the live realized daily loss, so
        a caller who wants it passes ``limits`` explicitly.  Reproducing it here
        from a guess would be the silent-improvement failure this module exists
        to avoid.
        """

        cfg = self._config
        base = _P.GovernorLimits()

        def _f(key: str, default: float) -> float:
            try:
                value = cfg.get(key, default)
                return float(default if value is None else value)
            except (TypeError, ValueError):
                return float(default)

        mode = cfg.get("ultimate_book_derisk_mode", base.derisk_mode)
        return _P.GovernorLimits(
            soft_daily_stop_pct=_f(
                "ultimate_book_soft_daily_stop_pct", base.soft_daily_stop_pct
            ),
            hard_daily_limit_pct=base.hard_daily_limit_pct,
            max_dd_limit_pct=base.max_dd_limit_pct,
            max_dd_entry_block_pct=_f(
                "ultimate_book_max_dd_entry_block_pct",
                getattr(base, "max_dd_entry_block_pct", base.max_dd_limit_pct),
            ),
            derisk_start_dd_pct=_f(
                "ultimate_book_derisk_start_dd_pct", base.derisk_start_dd_pct
            ),
            gross_open_risk_cap_pct=_f(
                "ultimate_book_gross_open_risk_cap_pct", base.gross_open_risk_cap_pct
            ),
            derisk_mode=str(mode) if mode is not None else base.derisk_mode,
            profit_target_pct=_f(
                "ultimate_book_profit_target_pct", getattr(base, "profit_target_pct", 0.0)
            ),
            profit_target_derisk_mult=_f(
                "ultimate_book_profit_target_derisk_mult",
                getattr(base, "profit_target_derisk_mult", 0.25),
            ),
        )

    def _to_policy_decision(
        self,
        decision: Any,
        candidates: Sequence[PolicyCandidate],
        supplied: Mapping[str, bool],
    ) -> PolicyDecision:
        """Map ``UltimateBookAdmissionDecision`` -> ``PolicyDecision``.

        ``would_units`` is used as the decision, and ``realized_units`` is
        recorded in ``authority``.  That split is load-bearing: on the live book
        path the third gate *suppresses placement* while still computing the
        full sizing, so ``realized_units`` is empty in shadow mode and
        ``would_units`` is the decision the book made.  Reading
        ``realized_units`` as "the decision" would make every shadow cycle look
        like a no-op, which is exactly how the W7 fortnight's ~99k packets would
        read as an empty book.
        """

        raw = decision.to_dict() if hasattr(decision, "to_dict") else dict(decision)
        would = [dict(u) for u in (raw.get("would_units") or [])]
        realized = [dict(u) for u in (raw.get("realized_units") or [])]
        units = tuple(_unit_from_live(u) for u in would)

        allocations: list[PolicyAllocation] = []
        for index, unit in enumerate(units):
            members = set(unit.members)
            for candidate in candidates:
                if candidate.sleeve not in members:
                    continue
                allocations.append(
                    PolicyAllocation(
                        symbol=candidate.symbol,
                        side=candidate.direction,
                        entry=candidate.entry_ref,
                        stop_dist=candidate.stop_dist,
                        size_risk_pct=unit.risk_pct_per_trade,
                        unit_index=index,
                        admitted=unit.sized and unit.risk_pct_per_trade > 0.0,
                        reason=unit.reason,
                        provenance=candidate.provenance(self._policy_id),
                    )
                )

        # ``reason`` must say why the BOOK decided what it decided, so it reads the
        # governor's own reason when the governor ran.  The bridge overwrites the
        # top-level reason with the *gate* reason whenever a gate blocks
        # (``bridge.py:480-506``), which is a statement about authority, not about
        # sizing: a locally-gated config would report
        # ``ultimate_book_live_activation_allowed_false`` on a cycle whose real
        # decision was ``soft_daily_stop_reached``.  On the live account all four
        # gates were open, so the two coincide — every recorded packet carries the
        # governor reason — and this keeps that true off the live host too.  The
        # gate reason is preserved verbatim in ``authority``.
        governor = raw.get("governor") or None
        bridge_reason = str(raw.get("reason", ""))
        reason = str((governor or {}).get("reason") or bridge_reason)
        # ``governor is None`` with no units is the signature of a refusal that
        # happened BEFORE the governor ran — the 2.0 %-ceiling smooth interlock
        # (``admission.py:1407-1424``) or an unknown profile (``:1396-1398``).
        # The live decision object carries no field for the sizing layer's own
        # reason once a gate has overwritten the top-level one, so that reason is
        # genuinely unavailable rather than merely unread; the flag lets a caller
        # separate "the governor blocked" from "the dial refused to arm".
        refused_before_governor = governor is None and not would
        return PolicyDecision(
            policy_id=self._policy_id,
            new_entries_allowed=bool(raw.get("would_new_entries_allowed", False)),
            reason=reason,
            units=units,
            allocations=tuple(allocations),
            governor=governor,
            authority={
                "bridge_reason": bridge_reason,
                "decision_status": raw.get("decision_status"),
                "runtime_effect_now": bool(raw.get("runtime_effect_now", False)),
                "enabled": raw.get("enabled"),
                "apply_to_execution": raw.get("apply_to_execution"),
                "live_activation_allowed_by_config": raw.get(
                    "live_activation_allowed_by_config"
                ),
                "live_broker_authority": raw.get("live_broker_authority"),
                "realized_unit_count": len(realized),
            },
            diagnostics={
                "cycle_inputs_supplied": dict(supplied),
                "sizing_refused_before_governor": refused_before_governor,
                "n_candidates_in": raw.get("n_candidates_in"),
                "n_candidates_after_drop": raw.get("n_candidates_after_drop"),
                "dropped_symbols": list(raw.get("dropped_symbols") or ()),
                "profile": raw.get("profile"),
                "derisk_mode": raw.get("derisk_mode"),
                "kelly_lite": raw.get("kelly_lite"),
                "kelly_conservative": raw.get("kelly_conservative"),
                "kelly_running_count": raw.get("kelly_running_count"),
                "stress_derisk": raw.get("stress_derisk"),
                "include_clean3": raw.get("include_clean3"),
                "include_candidate_book": raw.get("include_candidate_book"),
                "include_market_expansion_book": raw.get(
                    "include_market_expansion_book"
                ),
                "metals_confluence_gate": raw.get("metals_confluence_gate"),
                "would_total_risk_pct": raw.get("would_total_risk_pct"),
                "live_would_units": would,
            },
        )

    # -- generation (NOT part of the Policy protocol) -----------------------
    def active_sleeves(self) -> dict[str, Any]:
        """The effective sleeve registry this dial resolves to.

        Delegates to the live resolvers, so the count is measured rather than
        asserted.  Under the live dial this is 8 core + 9 candidate + 12
        market-expansion sleeves, and *none* of them comes from
        ``ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`` — that file
        is a different, shadow-only registry with zero overlap; see the defect
        register.
        """

        cfg = self._config

        def _b(key: str) -> bool:
            return bool(cfg.get(key, _BRIDGE_DEFAULT_CONFIG.get(key, False)))

        registry = dict(
            _P.effective_registry(
                include_clean3=_b("ultimate_book_include_clean3"),
                include_clean4=_b("ultimate_book_include_clean4"),
            )
        )
        if _b("ultimate_book_include_candidate_book"):
            allow = tuple(cfg.get("ultimate_book_candidate_book_sleeves") or ()) or None
            registry.update(_P.candidate_book_registry(allow))
        if _b("ultimate_book_include_market_expansion_book"):
            sleeves, error = _P.resolve_market_expansion_sleeves(
                policy=str(cfg.get("ultimate_book_market_expansion_policy") or ""),
                explicit_sleeves=tuple(
                    cfg.get("ultimate_book_market_expansion_sleeves") or ()
                ),
            )
            if not error and sleeves:
                registry.update(_P.market_expansion_registry(sleeves))
        return registry

    def confidence_of(self, sleeve: str) -> float:
        """This dial's confidence weight for one sleeve, from the live registry."""

        return _P.confidence_for(sleeve, self.active_sleeves())

    def cluster_of(self, sleeve: str) -> str | None:
        return _P.cluster_of(sleeve, self.active_sleeves())

    def as_dict(self) -> dict[str, Any]:
        return {"describe": dict(self.describe()), "config": dict(self._config)}


def live_governor_limits_asdict(limits: Any) -> dict[str, Any]:
    """``GovernorLimits`` -> dict, for receipts."""

    return asdict(limits)
