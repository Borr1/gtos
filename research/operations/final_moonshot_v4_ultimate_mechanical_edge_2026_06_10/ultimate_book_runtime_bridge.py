"""ultimate_book_runtime_bridge.py — RUNTIME WIRING (DEFAULT-OFF). NO BROKER. NO ORDERS.

The runtime bridge from the standalone deploy book (`ultimate_book_live_package`) to the production
execution layer, mirroring the established repo pattern
`src/components/gtos_vnext_runtime.evaluate_vnext_selector_v4_admission`.

WHY THIS FILE (and not a production-src edit): per the go-live guardrails this prep work must NOT
silently change live behaviour. So the bridge LIVES IN THE ROUTE DIR as a default-off module that the
owner wires into `gtos_vnext_runtime` only at go-live (the staged config patch +
`STAGED_disable_broad_selector.patch` + `GOLIVE_runtime_wiring.md` document exactly how). This module
is import-safe, pure-decision, and performs NO network / NO MT5 / NO broker / NO order placement. It
turns a per-decision candidate stream into governor-gated, confidence + Kelly-lite sized risk%
intents, behind the repo TRIPLE-GATE, defaulting fully OFF.

TRIPLE-GATE (matches the repo's established fail-closed-by-default authority gates; cite
`src/components/selector_v4.py::evaluate_selector_v4_admission` enabled/apply_to_execution/
live_activation_allowed and `config/agent_config.yaml` selector_v4_* lines 740-742):

    ultimate_book_enabled                 master flag for the standalone book engine (default false)
  AND ultimate_book_apply_to_execution    only true once broker-authority cleared (default false)
  AND ultimate_book_live_activation_allowed   third gate; runtime halt files are the physical control

ALL THREE must be true for any risk-bearing effect (runtime_effect_now=True). Otherwise the bridge
returns a SHADOW decision: it still computes what it WOULD size (would_*), but emits zero realized
risk and candidate_use_allowed_now=False. This mirrors selector_v4's would_action / shadow pattern so
the owner can dry-run the book in production telemetry before any flip.

BROAD-SELECTOR REPLACEMENT INVARIANT: go-live is a REPLACEMENT, not an augmentation. The losing broad
V4 selector (-0.25R/fill native; ULTIMATE_GO_LIVE_DOSSIER.md) must be OFF when the book is live. This
bridge FAILS CLOSED if `ultimate_book_disable_broad_selector` is true (the default) AND the broad
selector is still apply-to-execution: it refuses to bear risk and reports the contradiction, so the
two selectors can never both reach execution. (The staged config patch flips
`selector_v4_apply_to_execution: false`; this guard is the belt-and-braces runtime assertion.)

WAVE-7 FINAL BOOK: clean_3 (11 sleeves) with HEATOIL_c+NATGAS_cash dropped (tick-true), Kelly-lite
conviction sizing, owner NOMINAL dial (1.25% first cycle half-Kelly -> 1.50% handset-Kelly after the
first account clears -> 2.00% ceiling). See ultimate_book_live_package CLEAN3_W7_*_PROFILE.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping, Sequence

import ultimate_book_live_package as P
from ultimate_book_live_package import (
    TradeIntent, GovernorState, GovernorLimits, DEFAULT_LIMITS,
    admit_and_size, filter_w7_dropped_symbols,
    ALLOCATION_PROFILES, CLEAN3_W7_FIRST_CYCLE_PROFILE,
)

SCHEMA_VERSION = "ultimate_book_runtime_admission_v1"
COMPONENT = "ultimate_book"

# Default config block (mirrors the staged config patch; all default-OFF). The production runtime
# reads these from config["gtos_vnext_runtime"]; this dict documents the keys + safe defaults and is
# used when a key is absent so a partial/missing config FAILS CLOSED (no accidental live effect).
DEFAULT_CONFIG: dict[str, Any] = {
    "ultimate_book_enabled": False,
    "ultimate_book_apply_to_execution": False,
    "ultimate_book_live_activation_allowed": False,
    "ultimate_book_disable_broad_selector": True,
    "ultimate_book_profile": CLEAN3_W7_FIRST_CYCLE_PROFILE,
    "ultimate_book_include_clean3": True,     # W7 final book = clean_3 (11 sleeves)
    "ultimate_book_include_clean4": False,
    "ultimate_book_overlays": False,
    "ultimate_book_vp_acceptance": False,
    "ultimate_book_stress_derisk": False,     # owner enables the reactive overlay after first clear
    "ultimate_book_kelly_lite": True,         # W7 conviction sizing
    "ultimate_book_kelly_conservative": True, # first cycle = half-Kelly (breach-free)
    "ultimate_book_drop_w7_symbols": True,    # drop HEATOIL_c+NATGAS_cash (tick-true)
}


def _bool(cfg: Mapping[str, Any], key: str) -> bool:
    return bool(cfg.get(key, DEFAULT_CONFIG[key]))


def _str(cfg: Mapping[str, Any], key: str) -> str:
    v = cfg.get(key, DEFAULT_CONFIG[key])
    return str(v) if v is not None else str(DEFAULT_CONFIG[key])


@dataclass
class UltimateBookAdmissionDecision:
    """Structured, JSON-serializable bridge decision. NO broker fields; nothing here places an order.

    runtime_effect_now      : True ONLY when the full triple-gate passes AND the broad selector is off.
    candidate_use_allowed_now : True ONLY when runtime_effect_now (downstream may act on sized risk%).
    would_new_entries_allowed / would_units : the SHADOW projection (what the book WOULD size now) even
                              when gated off, so the owner can dry-run in live telemetry pre-flip.
    realized_units          : the units actually emitted with non-zero risk (empty unless effect_now).
    """
    schema_version: str
    component: str
    enabled: bool
    apply_to_execution: bool
    live_activation_allowed_by_config: bool
    broad_selector_disable_required: bool
    broad_selector_apply_to_execution: bool
    runtime_effect_now: bool
    candidate_use_allowed_now: bool
    decision_status: str
    reason: str
    profile: str
    include_clean3: bool
    include_clean4: bool
    kelly_lite: bool
    kelly_conservative: bool
    stress_derisk: bool
    dropped_symbols: tuple[str, ...]
    n_candidates_in: int
    n_candidates_after_drop: int
    would_new_entries_allowed: bool
    would_total_risk_pct: float
    would_units: list[dict[str, Any]] = field(default_factory=list)
    realized_units: list[dict[str, Any]] = field(default_factory=list)
    governor: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _broad_selector_apply(root_config: Mapping[str, Any]) -> bool:
    """Read whether the proven-losing broad V4 selector is still apply-to-execution.

    The broad selector reaches execution only when BOTH selector_v4_enabled AND
    selector_v4_apply_to_execution are true (selector_v4.evaluate_selector_v4_admission). We treat it
    as 'still live' if both are set so the replacement-invariant guard is conservative (fail-closed).
    """
    cfg = (root_config or {}).get("gtos_vnext_runtime", {}) or {}
    return bool(cfg.get("selector_v4_enabled", False)) and bool(
        cfg.get("selector_v4_apply_to_execution", False)
    )


def evaluate_vnext_ultimate_book_admission(
    *,
    config: Mapping[str, Any] | None,
    intents: Sequence[TradeIntent],
    governor_state: GovernorState,
    account: str = "A",
    limits: GovernorLimits = DEFAULT_LIMITS,
) -> UltimateBookAdmissionDecision:
    """Evaluate the standalone deploy-book admission through the vNext runtime bridge (DEFAULT-OFF).

    Mirrors evaluate_vnext_selector_v4_admission: binds runtime config to the pure book authority so
    the config keys are production-code-owned, performs NO broker/account/order work, and is gated by
    the repo triple-gate. Returns an UltimateBookAdmissionDecision (JSON-serializable).

    Flow:
      1. Read the `ultimate_book_*` block from config["gtos_vnext_runtime"] (fail-closed defaults).
      2. Compute the SHADOW projection always (what the book would size) — leak-free, no broker.
      3. Replacement-invariant guard: if disable-broad is required but the broad selector is still
         apply-to-execution, FAIL CLOSED (refuse risk; report the contradiction).
      4. Triple-gate: realized risk is emitted ONLY when enabled AND apply_to_execution AND
         live_activation_allowed AND the broad selector is off. Otherwise shadow-only (zero risk).
    """
    root_config = dict(config or {})
    cfg = root_config.get("gtos_vnext_runtime", {}) or {}

    enabled = _bool(cfg, "ultimate_book_enabled")
    apply_to_execution = _bool(cfg, "ultimate_book_apply_to_execution")
    live_allowed = _bool(cfg, "ultimate_book_live_activation_allowed")
    disable_broad_required = _bool(cfg, "ultimate_book_disable_broad_selector")
    broad_apply = _broad_selector_apply(root_config)

    profile = _str(cfg, "ultimate_book_profile")
    include_clean3 = _bool(cfg, "ultimate_book_include_clean3")
    include_clean4 = _bool(cfg, "ultimate_book_include_clean4")
    overlays = _bool(cfg, "ultimate_book_overlays")
    vp_acceptance = _bool(cfg, "ultimate_book_vp_acceptance")
    stress_derisk = _bool(cfg, "ultimate_book_stress_derisk")
    kelly_lite = _bool(cfg, "ultimate_book_kelly_lite")
    kelly_conservative = _bool(cfg, "ultimate_book_kelly_conservative")
    drop_w7 = _bool(cfg, "ultimate_book_drop_w7_symbols")

    n_in = len(list(intents))
    kept, dropped = filter_w7_dropped_symbols(intents, enabled=drop_w7)

    def _decide(
        *, status: str, reason: str, effect_now: bool,
        shadow: dict[str, Any], realized: list[dict[str, Any]],
    ) -> UltimateBookAdmissionDecision:
        return UltimateBookAdmissionDecision(
            schema_version=SCHEMA_VERSION, component=COMPONENT,
            enabled=enabled, apply_to_execution=apply_to_execution,
            live_activation_allowed_by_config=live_allowed,
            broad_selector_disable_required=disable_broad_required,
            broad_selector_apply_to_execution=broad_apply,
            runtime_effect_now=effect_now,
            candidate_use_allowed_now=effect_now,
            decision_status=status, reason=reason,
            profile=profile, include_clean3=include_clean3, include_clean4=include_clean4,
            kelly_lite=kelly_lite, kelly_conservative=kelly_conservative, stress_derisk=stress_derisk,
            dropped_symbols=dropped, n_candidates_in=n_in, n_candidates_after_drop=len(kept),
            would_new_entries_allowed=bool(shadow.get("new_entries_allowed", False)),
            would_total_risk_pct=round(
                sum(float(u.get("unit_risk_pct", 0.0)) for u in shadow.get("units", [])), 8),
            would_units=shadow.get("units", []),
            realized_units=realized,
            governor=shadow.get("governor"),
        )

    # Unknown profile -> fail closed BEFORE computing anything risk-bearing.
    if profile not in ALLOCATION_PROFILES:
        empty = {"ok": False, "new_entries_allowed": False, "units": [], "governor": None}
        return _decide(status="fail_closed_unknown_profile", reason=f"unknown_profile:{profile}",
                       effect_now=False, shadow=empty, realized=[])

    # 2. SHADOW projection — what the book WOULD size right now (always computed; pure, no broker).
    shadow = admit_and_size(
        kept, governor_state, profile=profile, account=account, limits=limits,
        include_clean3=include_clean3, include_clean4=include_clean4,
        overlays=overlays, vp_acceptance=vp_acceptance,
        stress_derisk=stress_derisk, kelly_lite=kelly_lite, kelly_conservative=kelly_conservative,
    )

    # 3. Replacement-invariant guard (belt-and-braces; the staged patch is the primary control).
    if disable_broad_required and broad_apply:
        return _decide(
            status="fail_closed_broad_selector_still_live",
            reason="broad_selector_apply_to_execution_true_while_book_requires_disable",
            effect_now=False, shadow=shadow, realized=[])

    # 4. Triple-gate. Realized risk only when ALL gates pass (and broad selector clear, checked above).
    if not enabled:
        return _decide(status="shadow_book_disabled", reason="ultimate_book_disabled_by_config",
                       effect_now=False, shadow=shadow, realized=[])
    if not apply_to_execution:
        return _decide(status="shadow_apply_to_execution_off",
                       reason="ultimate_book_apply_to_execution_false", effect_now=False,
                       shadow=shadow, realized=[])
    if not live_allowed:
        return _decide(status="shadow_live_activation_not_allowed",
                       reason="ultimate_book_live_activation_allowed_false", effect_now=False,
                       shadow=shadow, realized=[])

    # All gates pass: the book bears risk. realized_units == the shadow sizing (governor already ran).
    realized = shadow.get("units", []) if shadow.get("new_entries_allowed") else []
    status = "admitted_book_authority" if realized else "blocked_by_governor"
    return _decide(status=status, reason=shadow.get("reason", "ok"),
                   effect_now=True, shadow=shadow, realized=realized)


def describe_bridge() -> dict[str, Any]:
    """Machine-readable description of the bridge wiring + config keys (for go-live audit)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "triple_gate": [
            "ultimate_book_enabled",
            "ultimate_book_apply_to_execution",
            "ultimate_book_live_activation_allowed",
        ],
        "replacement_invariant": {
            "disable_broad_key": "ultimate_book_disable_broad_selector",
            "broad_selector_keys": ["selector_v4_enabled", "selector_v4_apply_to_execution"],
            "fail_closed_when_both_live": True,
        },
        "default_config": DEFAULT_CONFIG,
        "w7_final_book": P.describe_book()["clean3"]["w7_final"],
        "no_broker": True, "no_orders": True, "no_network": True,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(describe_bridge(), indent=1, default=str))
