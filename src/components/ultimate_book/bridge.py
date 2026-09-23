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

AUTHORITY GATES (matches the repo's established fail-closed-by-default authority gates; cite
`src/components/selector_v4.py::evaluate_selector_v4_admission` enabled/apply_to_execution/
live_activation_allowed and `config/agent_config.yaml` selector_v4_* lines 740-742):

    ultimate_book_enabled                 master flag for the standalone book engine (default false)
  AND ultimate_book_apply_to_execution    only true once broker-authority cleared (default false)
  AND ultimate_book_live_activation_allowed   third gate; runtime halt files are the physical control
  AND ultimate_book_live_broker_authority     explicit broker mutation authority (default false)

ALL FOUR must be true for any risk-bearing effect (runtime_effect_now=True). Otherwise the bridge
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

# Vendored into src (production must not import the research route dir, which the cleanup
# policy may archive/delete).
#
# D6 (SLEEVE_BOOK_DEFECT_REGISTER), corrected 2026-07-27. This comment used to claim admission.py is
# "a byte-identical copy of the route deploy module (ultimate_book_live_package.py)". IT IS NOT, and
# the claim misdirects: [MEASURED] admission.py is 1,741 lines against the route module's 1,330, and
# their SHA-256s differ. admission.py is a strict SUPERSET carrying 15 top-level names the route module
# has no equivalent for -- candidate_book_registry, market_expansion_registry,
# resolve_market_expansion_sleeves, compute_stress_derisk_state, _enforce_gross_open_risk_cap,
# _metals_confluence_pass, _learning_mult, A8_CONFLUENCE_SLEEVES, CANDIDATE_BOOK_PROFILE,
# MARKET_EXPANSION_PROFILE among them -- and its admit_and_size takes 9 parameters the route version
# does not.
#
# What is true: **admission.py is the live authority and the route module is its ancestor.** Parity is
# asserted on the SHARED NUMERIC CORE only (tests/ultimate_book/test_vendor_parity.py), not on the
# files. Anyone porting, auditing or fixing the sizing chain from the route copy would be working on
# code that has not been live since the candidate book and the market-expansion book were armed.
from . import admission as P
from .admission import (
    TradeIntent, GovernorState, GovernorLimits, DEFAULT_LIMITS,
    admit_and_size, filter_w7_dropped_symbols,
    ALLOCATION_PROFILES, CLEAN3_W7_FIRST_CYCLE_PROFILE,
)
from .runtime_learning_packet import (
    DEFAULT_LOG_PATH as RUNTIME_LEARNING_PACKET_DEFAULT_LOG_PATH,
    DEFAULT_REDACTION_POLICY as RUNTIME_LEARNING_PACKET_REDACTION_POLICY,
    SCHEMA_VERSION as RUNTIME_LEARNING_PACKET_SCHEMA_VERSION,
)

SCHEMA_VERSION = "ultimate_book_runtime_admission_v1"
COMPONENT = "ultimate_book"

# Default config block (mirrors the staged config patch; all default-OFF). The production runtime
# reads these from config["gtos_vnext_runtime"]; this dict documents the keys + safe defaults and is
# used when a key is absent so a partial/missing config FAILS CLOSED (no accidental live effect).
#
# D8 CAVEAT, added 2026-07-27: "fails closed" is true of the AUTHORITY keys (every gate defaults
# False) and NOT of the DIAL keys. ultimate_book_profile below is the 1.25% first-cycle profile while
# live runs the 2.00% ceiling, and derisk_mode below is "band" while live runs "smooth" -- so a caller
# that fell back to these would silently size at 62% of the live dial, or trip the ceiling interlock,
# with no error. The values are kept as DOCUMENTATION of the first-cycle shape; the nine keys in
# REQUIRED_DIAL_KEYS are now refused-if-absent by evaluate_vnext_ultimate_book_admission when the book
# is enabled, so nothing can fall back to them on a live-shaped config.
DEFAULT_CONFIG: dict[str, Any] = {
    "ultimate_book_enabled": False,
    "ultimate_book_apply_to_execution": False,
    "ultimate_book_live_activation_allowed": False,
    "ultimate_book_live_broker_authority": False,
    "ultimate_book_disable_broad_selector": True,
    "ultimate_book_profile": CLEAN3_W7_FIRST_CYCLE_PROFILE,
    "ultimate_book_include_clean3": True,     # W7 final book = clean_3 (11 sleeves)
    "ultimate_book_include_clean4": False,
    "ultimate_book_include_candidate_book": False,
    "ultimate_book_candidate_book_profile": P.CANDIDATE_BOOK_PROFILE,
    "ultimate_book_candidate_book_sleeves": [],  # optional allowlist; [] => all executable candidates
    "ultimate_book_include_market_expansion_book": False,
    "ultimate_book_market_expansion_profile": P.MARKET_EXPANSION_PROFILE,
    "ultimate_book_market_expansion_policy": P.MARKET_EXPANSION_EXPLICIT_ALLOWLIST_POLICY,
    "ultimate_book_market_expansion_sleeves": [],  # required allowlist when include=true; [] => fail closed
    "ultimate_book_overlays": False,
    "ultimate_book_vp_acceptance": False,
    "ultimate_book_stress_derisk": False,     # owner enables the reactive overlay after first clear
    "ultimate_book_kelly_lite": True,         # W7 conviction sizing
    "ultimate_book_kelly_conservative": True, # first cycle = half-Kelly (breach-free)
    "ultimate_book_derisk_mode": "band",
    "ultimate_book_sqrt_n_pooling": False,    # record W7 sqrt-N same-sleeve pooling when owner-armed
    "ultimate_book_drop_w7_symbols": True,    # drop HEATOIL_c+NATGAS_cash (tick-true)
    "ultimate_book_kelly_running_count": False,  # leak-free RUNNING per-day n_active (recovers the
    #                                              validated full-day Kelly convention; engine-gated)
    # L5 LEARNING ACTUATOR (default-off): owner-armed {sleeve: confidence_multiplier} map from
    # learning_actuator.rerate_book on the deep-history every-split evidence (L1 adjudication). Empty
    # {} => no-op (the live edge_reconciler stays brake-only). GATE=0.0 drops; bounded tilt otherwise.
    "ultimate_book_learning_rerate": {},
    # A8 metals entry-quality confluence gate (default-off): drops metals intents that CARRY the
    # confluence features and fail K=3-of-4; featureless intents admit-as-today (deploy-phase arms it).
    "ultimate_book_metals_confluence_gate": False,
    # WAVE-11 vol-LEVEL sizing tilt (default-off; Session AR). clamp(vr/2.0, 0.80, 1.20) on
    # `sub_xvol_pullback` intents — a net ~7.5 % de-risk whose size-up is reserved for the most
    # expanded fifth of the sleeve's firing range. THE DEFAULT BELONGS HERE AND NOWHERE ELSE:
    # `_bool` resolves an absent key against THIS dict, so a flag read without a default entry
    # raises KeyError inside `evaluate`, which the engine catches as `engine_exception` — i.e. the
    # armed book would have stood down every tick, silently, with a healthy heartbeat. Caught by
    # `test_ar_vol_level_tilt.py::test_the_launcher_flag_reaches_the_bridge_without_a_config_byte`
    # on its first run. The live value is set by `run_book.py --vol-level-tilt` injecting the key
    # into the in-memory runtime dict, NEVER by a byte of any YAML.
    "ultimate_book_vol_level_tilt": False,
    # S1 per-symbol damage-memory kill switch (default-off): QUARANTINE/RISK_REDUCE a symbol that did real
    # damage over the trailing realized window (broker-real metrics supplied by the runtime). Owner-armed.
    "ultimate_book_symbol_damage_guard": False,
    # Runtime-learning packet ledger (observation-only): append-only JSONL packets for every generated,
    # shadowed, skipped, placed, adopted, managed, closed, or flattened book unit. It changes no broker
    # state and hashes raw broker/account identifiers before writing.
    "ultimate_book_runtime_learning_packet_enabled": False,
    "ultimate_book_runtime_learning_packet_log_enabled": False,
    "ultimate_book_runtime_learning_packet_log_path": RUNTIME_LEARNING_PACKET_DEFAULT_LOG_PATH,
    "ultimate_book_runtime_learning_packet_schema": RUNTIME_LEARNING_PACKET_SCHEMA_VERSION,
    "ultimate_book_runtime_learning_redaction_policy": RUNTIME_LEARNING_PACKET_REDACTION_POLICY,
    # Convergence advisory telemetry (default-off): attaches V3/V4/CP281/vNext reservoir summaries and
    # per-packet join keys to runtime-learning packets. Observation-only; never execution authority.
    "ultimate_convergence_advisory_enabled": False,
    "ultimate_convergence_advisory_log_enabled": False,
    "ultimate_convergence_advisory_apply_to_execution": False,
    "ultimate_convergence_advisory_schema": "ultimate_convergence_advisory_v1",
    "ultimate_convergence_advisory_checkpoint_path": (
        "research/operations/final_moonshot_ultimate_system_convergence_2026_06_19"
    ),
}


# D8: the keys whose ABSENCE changes the sized book. Deliberately identical to
# SleeveBookPolicy.DIAL_KEYS (src/research_infra/replay_policy/sleeve_book.py) so the live bridge and
# the replay policy cannot disagree about what a complete dial is. Kept as an explicit tuple rather
# than derived from DEFAULT_CONFIG: DEFAULT_CONFIG's job is to DOCUMENT safe defaults for the ~30
# non-dial keys, and deriving this from it would silently re-admit any key someone later adds there.
REQUIRED_DIAL_KEYS: tuple[str, ...] = (
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


def config_bool_value(value: Any, default: bool = False) -> bool:
    """Parse runtime boolean config defensively.

    YAML normally gives native booleans, but supervisor/env/config overlays can
    arrive as strings. Python's raw bool("false") is True, so parse known text
    forms explicitly and fall back to the supplied default on unknown values.
    """
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "n", "off", "disabled"}:
        return False
    return bool(default)


def config_safety_flag(cfg: Mapping[str, Any], key: str, *, default_when_absent: bool) -> bool:
    """Resolve an operator SAFETY flag, failing toward protection.

    ``config_bool_value`` resolves an unrecognised value to the caller's
    default. That is right for an *authority* gate — unknown means no authority
    — and wrong for a *safety* flag, where the same rule silently disarms the
    protection. A typo in the operator's circuit breaker must not be the reason
    the book keeps trading.

    Absent key -> the documented default (so existing configs are unchanged).
    Present but unparseable -> ARMED, and the operator can see it in the
    resulting behaviour rather than not seeing it at all.
    """

    if key not in cfg:
        return bool(default_when_absent)
    value = cfg.get(key)
    if value is None:
        return bool(default_when_absent)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "n", "off", "disabled"}:
        return False
    return True


def _bool(cfg: Mapping[str, Any], key: str) -> bool:
    return config_bool_value(cfg.get(key, DEFAULT_CONFIG[key]), DEFAULT_CONFIG[key])


def _str(cfg: Mapping[str, Any], key: str) -> str:
    v = cfg.get(key, DEFAULT_CONFIG[key])
    return str(v) if v is not None else str(DEFAULT_CONFIG[key])


def _str_tuple(cfg: Mapping[str, Any], key: str) -> tuple[str, ...]:
    raw = cfg.get(key, DEFAULT_CONFIG[key])
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw,) if raw else ()
    if not isinstance(raw, Sequence):
        return ()
    return tuple(str(item) for item in raw if str(item))


def _rerate_map(cfg: Mapping[str, Any]) -> "dict[str, float] | None":
    """Read the owner-armed learning-rerate map (default-off). Returns a clean {sleeve: float} dict or
    None (no-op). Fail-safe: a malformed entry is skipped (never raises, never silently sizes up)."""
    raw = cfg.get("ultimate_book_learning_rerate", DEFAULT_CONFIG["ultimate_book_learning_rerate"])
    if not isinstance(raw, Mapping) or not raw:
        return None
    out: dict[str, float] = {}
    for k, v in raw.items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out or None


@dataclass
class UltimateBookAdmissionDecision:
    """Structured, JSON-serializable bridge decision. NO broker fields; nothing here places an order.

    runtime_effect_now      : True ONLY when all authority gates pass AND the broad selector is off.
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
    live_broker_authority: bool
    broad_selector_disable_required: bool
    broad_selector_apply_to_execution: bool
    runtime_effect_now: bool
    candidate_use_allowed_now: bool
    decision_status: str
    reason: str
    profile: str
    include_clean3: bool
    include_clean4: bool
    include_candidate_book: bool
    candidate_book_profile: str
    candidate_book_sleeves: tuple[str, ...]
    include_market_expansion_book: bool
    market_expansion_profile: str
    market_expansion_policy: str
    market_expansion_sleeves: tuple[str, ...]
    kelly_lite: bool
    kelly_conservative: bool
    kelly_running_count: bool
    sqrt_n_pooling: bool
    stress_derisk: bool
    derisk_mode: str
    overlays: bool
    vp_acceptance: bool
    drop_w7_symbols: bool
    learning_rerate_active: bool
    learning_gated_sleeves: tuple[str, ...]
    metals_confluence_gate: bool
    symbol_damage_guard: bool
    damage_quarantined_symbols: tuple[str, ...]
    dropped_symbols: tuple[str, ...]
    n_candidates_in: int
    n_candidates_after_drop: int
    would_new_entries_allowed: bool
    would_total_risk_pct: float
    would_units: list[dict[str, Any]] = field(default_factory=list)
    realized_units: list[dict[str, Any]] = field(default_factory=list)
    governor: dict[str, Any] | None = None
    # D11 (SLEEVE_BOOK_DEFECT_REGISTER): why the SIZING refused, independently of why the GATE refused.
    # admit_and_size can refuse before the governor ever runs -- the 2.0%-ceiling smooth interlock
    # (admission.py:1407-1424) or an unknown profile (:1396-1398) -- and returns that reason in the
    # shadow dict. Before this field the gate branches overwrote the top-level `reason` with the gate's
    # reason and the shadow's reason was carried nowhere, so a config with a closed third gate AND an
    # uncertified dial reported only `ultimate_book_live_activation_allowed_false`. The fact that the
    # book WOULD HAVE REFUSED ANYWAY was unobservable. It is the difference between "we are not armed"
    # and "we are not armed AND the dial is uncertified".
    #
    # On the live host all four gates were open, so the recorded fortnight lost nothing. It bites on
    # any non-live replay of a gated config -- i.e. exactly what SleeveBookPolicy does, which worked
    # around it with a `sizing_refused_before_governor` diagnostic inferred from `governor is None`
    # with no units. That inference is no longer necessary.
    sizing_reason: str | None = None
    # Ordered, per-candidate refusals captured by the exact dropping predicate that ran.  These
    # rows are observation-only and make the generated-intent denominator reconstructable.
    candidate_refusals: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _broad_selector_apply(root_config: Mapping[str, Any]) -> bool:
    """Read whether the proven-losing broad V4 selector is still apply-to-execution.

    The broad selector reaches execution only when BOTH selector_v4_enabled AND
    selector_v4_apply_to_execution are true (selector_v4.evaluate_selector_v4_admission). We treat it
    as 'still live' if both are set so the replacement-invariant guard is conservative (fail-closed).
    """
    cfg = (root_config or {}).get("gtos_vnext_runtime", {}) or {}
    return config_bool_value(cfg.get("selector_v4_enabled", False), False) and config_bool_value(
        cfg.get("selector_v4_apply_to_execution", False),
        False,
    )


def evaluate_vnext_ultimate_book_admission(
    *,
    config: Mapping[str, Any] | None,
    intents: Sequence[TradeIntent],
    governor_state: GovernorState,
    account: str = "A",
    limits: GovernorLimits = DEFAULT_LIMITS,
    n_active_override: "Mapping[str, int] | None" = None,
    n_active_override_authoritative: bool = False,
    stress_state: "Any | None" = None,
    symbol_damage_metrics: "Mapping[str, Any] | None" = None,
    cycle_taken: float | None = 0.0,
    book_open_risk_pct: float | None = None,
    apply_book_open_risk: bool = False,
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
    live_broker_authority = _bool(cfg, "ultimate_book_live_broker_authority")
    disable_broad_required = _bool(cfg, "ultimate_book_disable_broad_selector")
    broad_apply = _broad_selector_apply(root_config)

    profile = _str(cfg, "ultimate_book_profile")
    include_clean3 = _bool(cfg, "ultimate_book_include_clean3")
    include_clean4 = _bool(cfg, "ultimate_book_include_clean4")
    include_candidate_book = _bool(cfg, "ultimate_book_include_candidate_book")
    candidate_book_profile = _str(cfg, "ultimate_book_candidate_book_profile")
    candidate_book_sleeves = _str_tuple(cfg, "ultimate_book_candidate_book_sleeves")
    include_market_expansion_book = _bool(cfg, "ultimate_book_include_market_expansion_book")
    market_expansion_profile = _str(cfg, "ultimate_book_market_expansion_profile")
    market_expansion_policy = _str(cfg, "ultimate_book_market_expansion_policy")
    configured_market_expansion_sleeves = _str_tuple(cfg, "ultimate_book_market_expansion_sleeves")
    market_expansion_sleeves, market_expansion_policy_error = P.resolve_market_expansion_sleeves(
        policy=market_expansion_policy,
        explicit_sleeves=configured_market_expansion_sleeves,
    )
    overlays = _bool(cfg, "ultimate_book_overlays")
    vp_acceptance = _bool(cfg, "ultimate_book_vp_acceptance")
    stress_derisk = _bool(cfg, "ultimate_book_stress_derisk")
    kelly_lite = _bool(cfg, "ultimate_book_kelly_lite")
    kelly_conservative = _bool(cfg, "ultimate_book_kelly_conservative")
    kelly_running_count = _bool(cfg, "ultimate_book_kelly_running_count")
    derisk_mode = _str(cfg, "ultimate_book_derisk_mode")
    sqrt_n_pooling = _bool(cfg, "ultimate_book_sqrt_n_pooling")
    drop_w7 = _bool(cfg, "ultimate_book_drop_w7_symbols")
    learning_rerate = _rerate_map(cfg)
    metals_confluence_gate = _bool(cfg, "ultimate_book_metals_confluence_gate")
    # WAVE-11 vol-level sizing tilt (Session AR). Read from the runtime block like every other
    # flag, but the LIVE path never sets it in `agent_config.yaml`: `book_engine` injects the key
    # into the in-memory dict it hands this function when `run_book.py --vol-level-tilt` is set,
    # so the file's bytes -- and therefore the activation token's config digest -- are untouched.
    # A research driver sets it in its own runtime dict. Same key, one mechanism, no config byte.
    vol_level_tilt = _bool(cfg, "ultimate_book_vol_level_tilt")
    symbol_damage_guard = _bool(cfg, "ultimate_book_symbol_damage_guard")

    input_intents = list(intents)
    n_in = len(input_intents)
    kept, dropped = filter_w7_dropped_symbols(input_intents, enabled=drop_w7)
    kept_object_ids = {id(intent) for intent in kept}
    candidate_refusals = [
        {
            "sleeve": intent.sleeve,
            "symbol": intent.symbol,
            "direction": intent.direction,
            "decision_day": intent.decision_day,
            "candidate_disposition": "refused",
            "candidate_disposition_gate": "book_admission_and_sizing",
            "candidate_disposition_reason": "w7_tick_true_symbol_drop",
        }
        for intent in input_intents
        if id(intent) not in kept_object_ids
    ]

    def _decide(
        *, status: str, reason: str, effect_now: bool,
        shadow: dict[str, Any], realized: list[dict[str, Any]],
    ) -> UltimateBookAdmissionDecision:
        return UltimateBookAdmissionDecision(
            schema_version=SCHEMA_VERSION, component=COMPONENT,
            enabled=enabled, apply_to_execution=apply_to_execution,
            live_activation_allowed_by_config=live_allowed,
            live_broker_authority=live_broker_authority,
            broad_selector_disable_required=disable_broad_required,
            broad_selector_apply_to_execution=broad_apply,
            runtime_effect_now=effect_now,
            candidate_use_allowed_now=effect_now,
            decision_status=status, reason=reason,
            profile=profile, include_clean3=include_clean3, include_clean4=include_clean4,
            include_candidate_book=include_candidate_book, candidate_book_profile=candidate_book_profile,
            candidate_book_sleeves=candidate_book_sleeves,
            include_market_expansion_book=include_market_expansion_book,
            market_expansion_profile=market_expansion_profile,
            market_expansion_policy=market_expansion_policy,
            market_expansion_sleeves=market_expansion_sleeves,
            kelly_lite=kelly_lite, kelly_conservative=kelly_conservative,
            kelly_running_count=kelly_running_count, sqrt_n_pooling=sqrt_n_pooling,
            stress_derisk=stress_derisk,
            derisk_mode=derisk_mode,
            overlays=overlays, vp_acceptance=vp_acceptance, drop_w7_symbols=drop_w7,
            learning_rerate_active=bool(shadow.get("learning_rerate_active", False)),
            learning_gated_sleeves=tuple(shadow.get("learning_gated_sleeves", []) or ()),
            metals_confluence_gate=bool(shadow.get("metals_confluence_gate", metals_confluence_gate)),
            symbol_damage_guard=bool(shadow.get("symbol_damage_guard", symbol_damage_guard)),
            damage_quarantined_symbols=tuple(shadow.get("damage_quarantined_symbols", []) or ()),
            dropped_symbols=dropped, n_candidates_in=n_in, n_candidates_after_drop=len(kept),
            would_new_entries_allowed=bool(shadow.get("new_entries_allowed", False)),
            would_total_risk_pct=round(
                sum(float(u.get("unit_risk_pct", 0.0)) for u in shadow.get("units", [])), 8),
            would_units=shadow.get("units", []),
            realized_units=realized,
            governor=shadow.get("governor"),
            # D11: preserve the SIZING refusal reason even when a gate branch overwrites `reason`.
            # None when sizing was never attempted (the pre-sizing fail-closed branches below pass an
            # empty shadow), which is itself the honest answer: there is no sizing verdict to report.
            sizing_reason=shadow.get("reason") or None,
            candidate_refusals=list(candidate_refusals),
        )

    # D8 (SLEEVE_BOOK_DEFECT_REGISTER): fail closed on a MISSING DIAL KEY rather than defaulting it.
    # DEFAULT_CONFIG disagrees with the live YAML on the two keys that decide the dial --
    # ultimate_book_profile defaults to CLEAN3_W7_FIRST_CYCLE_PROFILE (1.25%) where live runs
    # clean3_w7_ceiling_nom2p00 (2.00%), and derisk_mode defaults to "band" where live runs "smooth".
    # Those two are exactly the pair the ceiling interlock checks (admission.py:1407-1413), so a caller
    # falling back to the defaults would either size the book at 62% of the live dial or fail the whole
    # book closed -- and would not be told which. Refusal beats a mis-sized book.
    #
    # Scoped to enabled=True on purpose: a disabled book already bears zero risk, and forcing a
    # missing-key refusal there would convert every partial-config caller into a failure without
    # protecting anything. SleeveBookPolicy applies the same nine-key list unconditionally
    # (strict_config=True); this is the live-path half of the same rule.
    if enabled:
        missing_dial_keys = [k for k in REQUIRED_DIAL_KEYS if k not in cfg]
        if missing_dial_keys:
            empty = {"ok": False, "new_entries_allowed": False, "units": [], "governor": None}
            return _decide(
                status="fail_closed_missing_dial_keys",
                reason="missing_dial_keys:" + ",".join(missing_dial_keys),
                effect_now=False, shadow=empty, realized=[])

    # Unknown profile -> fail closed BEFORE computing anything risk-bearing.
    if profile not in ALLOCATION_PROFILES:
        empty = {"ok": False, "new_entries_allowed": False, "units": [], "governor": None}
        return _decide(status="fail_closed_unknown_profile", reason=f"unknown_profile:{profile}",
                       effect_now=False, shadow=empty, realized=[])
    if include_candidate_book and candidate_book_profile != P.CANDIDATE_BOOK_PROFILE:
        empty = {"ok": False, "new_entries_allowed": False, "units": [], "governor": None}
        return _decide(
            status="fail_closed_unknown_candidate_book_profile",
            reason=f"unknown_candidate_book_profile:{candidate_book_profile}",
            effect_now=False,
            shadow=empty,
            realized=[],
        )
    if include_candidate_book and candidate_book_sleeves:
        known_candidates = set(P.candidate_book_registry()) | set(P.widen_registry())
        unknown = sorted(set(candidate_book_sleeves) - known_candidates)
        if unknown:
            empty = {"ok": False, "new_entries_allowed": False, "units": [], "governor": None}
            return _decide(
                status="fail_closed_unknown_candidate_book_sleeves",
                reason=f"unknown_candidate_book_sleeves:{','.join(unknown)}",
                effect_now=False,
                shadow=empty,
                realized=[],
            )
    if include_market_expansion_book and market_expansion_profile != P.MARKET_EXPANSION_PROFILE:
        empty = {"ok": False, "new_entries_allowed": False, "units": [], "governor": None}
        return _decide(
            status="fail_closed_unknown_market_expansion_profile",
            reason=f"unknown_market_expansion_profile:{market_expansion_profile}",
            effect_now=False,
            shadow=empty,
            realized=[],
        )
    if include_market_expansion_book and market_expansion_policy_error:
        empty = {"ok": False, "new_entries_allowed": False, "units": [], "governor": None}
        status = "fail_closed_unknown_market_expansion_policy"
        if market_expansion_policy_error.startswith("market_expansion_policy_sleeve_mismatch"):
            status = "fail_closed_market_expansion_policy_sleeve_mismatch"
        return _decide(
            status=status,
            reason=market_expansion_policy_error,
            effect_now=False,
            shadow=empty,
            realized=[],
        )
    if include_market_expansion_book and not market_expansion_sleeves:
        empty = {"ok": False, "new_entries_allowed": False, "units": [], "governor": None}
        return _decide(
            status="fail_closed_market_expansion_requires_explicit_sleeves",
            reason="market_expansion_allowlist_empty",
            effect_now=False,
            shadow=empty,
            realized=[],
        )
    if include_market_expansion_book and market_expansion_sleeves:
        known_expansion = set(P.market_expansion_registry(market_expansion_sleeves))
        unknown = sorted(set(market_expansion_sleeves) - known_expansion)
        if unknown:
            empty = {"ok": False, "new_entries_allowed": False, "units": [], "governor": None}
            return _decide(
                status="fail_closed_unknown_market_expansion_sleeves",
                reason=f"unknown_market_expansion_sleeves:{','.join(unknown)}",
                effect_now=False,
                shadow=empty,
                realized=[],
            )

    # 2. SHADOW projection — what the book WOULD size right now (always computed; pure, no broker).
    from src.judgment.apply_size import ROOM_FACT_KEYS
    room_facts = {
        key: root_config.get(key)
        for key in ROOM_FACT_KEYS
        if root_config.get(key) not in (None, "") and key != "equity"
    }
    shadow = admit_and_size(
        kept, governor_state, profile=profile, account=account, limits=limits,
        include_clean3=include_clean3, include_clean4=include_clean4,
        include_candidate_book=include_candidate_book,
        candidate_book_sleeves=candidate_book_sleeves or None,
        include_market_expansion_book=include_market_expansion_book,
        market_expansion_sleeves=market_expansion_sleeves or None,
        overlays=overlays, vp_acceptance=vp_acceptance,
        stress_derisk=stress_derisk, kelly_lite=kelly_lite, kelly_conservative=kelly_conservative,
        sqrt_n_pooling=sqrt_n_pooling,
        n_active_override=n_active_override,
        n_active_override_authoritative=n_active_override_authoritative,
        stress_state=stress_state,
        learning_rerate=learning_rerate, metals_confluence_gate=metals_confluence_gate,
        symbol_damage_metrics=symbol_damage_metrics, symbol_damage_guard=symbol_damage_guard,
        vol_level_tilt=vol_level_tilt,
        candidate_refusal_sink=candidate_refusals,
        cycle_taken=cycle_taken,
        book_open_risk_pct=book_open_risk_pct,
        apply_book_open_risk=apply_book_open_risk,
        account_equity=root_config.get("account_equity"),
        launcher_usd=root_config.get("launcher_usd"),
        room_facts=room_facts,
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
    if not live_broker_authority:
        return _decide(status="shadow_live_broker_authority_false",
                       reason="ultimate_book_live_broker_authority_false", effect_now=False,
                       shadow=shadow, realized=[])

    # All gates pass: the book bears risk. realized_units == the shadow sizing (governor already ran).
    new_allowed = bool(shadow.get("new_entries_allowed"))
    realized = shadow.get("units", []) if new_allowed else []
    if realized:
        status = "admitted_book_authority"
    elif not new_allowed:
        status = "blocked_by_governor"          # governor actually braked NEW entries
    else:
        status = "no_candidates_this_bar"       # governor ALLOWED; there were simply no signals
    decision = _decide(status=status, reason=shadow.get("reason", "ok"),
                   effect_now=True, shadow=shadow, realized=realized)
    # A1 / Alive living-tissue log (default-off). Never changes the decision.
    # Gate on env BEFORE import — do not pay judgment import on the live fire path.
    # HOST_APPLY_ALIVE / PR#10 b117c2339 mapped site UB-AUTH-010 after final _decide.
    import os as _jev_os
    _jev_shadow = (
        str(_jev_os.environ.get("GTOS_JEV_A1_LOG", "")).strip().lower() in {"1", "true", "yes"}
        or str(_jev_os.environ.get("GTOS_JEV_ALIVE_SHADOW", "")).strip().lower() in {"1", "true", "yes"}
    )
    if _jev_shadow:
        try:
            from src.judgment.a1_log import maybe_observe_ub_auth_010
            maybe_observe_ub_auth_010(decision, config)
        except Exception:
            pass
    return decision


def describe_bridge() -> dict[str, Any]:
    """Machine-readable description of the bridge wiring + config keys (for go-live audit)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "triple_gate": [
            "ultimate_book_enabled",
            "ultimate_book_apply_to_execution",
            "ultimate_book_live_activation_allowed",
            "ultimate_book_live_broker_authority",
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
