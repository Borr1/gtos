"""Validate ``SleeveBookPolicy`` against what the live book actually decided.

The evidence
------------
The W7 book ran live 2026-06-18 → 07-02 on both funded accounts and wrote
**99,112 runtime-learning packets** (`VPS_EXPORT_FINDINGS.md`;
``05_shadow_logs/ultimate_book_runtime_learning_packets.jsonl.gz``).  Each
packet carries a ``bridge`` block, and that block is unusually complete: it holds
the full flag set the cycle ran under, the ``governor`` decision, and both
``would_units`` and ``realized_units`` — the sized book itself
(``bridge.py:378-385``).

That makes an *exact* validation possible without reconstructing a single bar.
A unit's ``confidence`` is a function of the sleeve registry, the flags, the
Kelly day-count and the de-risk multiplier — not of price.  ``unit_risk_pct`` is
that confidence times the profile's nominal risk times the recorded governor
multiplier.  So every number in a recorded unit is predictable from the record
itself, and any disagreement is a port defect, a live defect, or an evidence gap.

Why the inputs are reconstructed rather than assumed
----------------------------------------------------
Three live inputs are machine-local state the export does not carry: the
governor's equity/open-risk, the persisted running-conviction count, and the
reactive de-risk state.  Each is *recoverable from its own recorded output*:

* ``governor.size_cap_multiplier`` inverts to a drawdown, hence an equity, under
  the recorded ``derisk_mode``.  The reconstruction is then checked — the policy's
  own governor output must equal the recorded one, field for field, or the row is
  classified ``EVIDENCE_GAP`` and excluded.

  **How much that check is worth, measured rather than asserted.** Adversarial
  mutation of the reconstruction shows it is NOT uniformly strong:
  ``size_cap_multiplier`` scaled by 0.9 is caught on 138 of 617 cycles (float
  round-trip residue, not semantics), and ``available_gross_risk_pct`` perturbed
  by +0.001 is caught on **zero** — because :func:`_state_reproducing_governor`
  sets the cap equal to the recorded headroom with zero open risk, so any
  recorded headroom reproduces itself by construction.  That is the one number
  the gross-cap shed consumes, so the headroom half of the recovery is an
  assumption, not a measurement, and is labelled as such here rather than in a
  footnote.  ``reason`` and ``allow_new_entries`` are genuinely checked.
* the Kelly count is recorded verbatim in the unit's own
  ``kelly_lite_na{N}_x{M}`` tag.
* the ladder/co-loss state is recorded in ``ladder_step{K}`` / ``coloss_breaker``.

Supplying a recorded value tests less than deriving it, so both are done and
reported separately: ``supplied`` mode isolates the sizing chain, and
``derive_n_active`` measures how often the per-cycle count the sizer would
compute on its own equals the count live actually used.  That difference is the
running-conviction divergence, quantified.

Fail-closed
-----------
A cycle that cannot be reconstructed is reported, not skipped.  ``ledger_pair``
writes two arm-shaped directories for
``replay_differential_harness.compare_arms``, which localises differences to row
and field and refuses to call anything equivalent it could not classify.  A
self-comparison of the policy side is the null control.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .core import AccountDayState, PolicyCandidate
from .sleeve_book import SleeveBookPolicy, _P

SCHEMA = "gtos.phase2.replay_policy.sleeve_book_validation.v1"

#: Packet event types that belong to a decision cycle.
CYCLE_EVENTS = frozenset(
    {"unit_admitted", "unit_skipped", "unit_shadow", "unit_placed", "cycle_no_candidates"}
)

_KELLY_TAG = re.compile(r"^kelly_lite_na(\d+)_x([0-9.]+)$")
_LADDER_TAG = re.compile(r"^ladder_step(\d+)$")

#: Unit fields compared.  ``tags`` is included deliberately: the audit trail is
#: where a wrong Kelly bin or a missing ladder step shows up as a *labelled*
#: difference instead of only as a number that happens to be close.
COMPARED_UNIT_FIELDS: tuple[str, ...] = (
    "cluster",
    "sleeve_members",
    "n_trades",
    "confidence",
    "risk_pct_per_trade",
    "unit_risk_pct",
    "sized",
    "reason",
    "overlays_applied",
)

#: Classifications.  Only ``MATCH`` supports the fidelity claim.
#:
#: ``PARTIAL_MATCH`` exists because the packet stream does not emit one packet per
#: intent: over the 884 cycles carrying ``would_units``, the distinct
#: ``(sleeve, symbol)`` count equals ``n_candidates_in`` on **332**, exceeds it on
#: **437** (adjacent re-emissions of one bar merge under an identical ``bridge``
#: digest) and falls short on **115** [MEASURED 2026-07-26].  A cycle whose intent
#: set is incomplete can be missing a whole unit through no fault of the policy,
#: so calling that a disagreement would be false, and calling it a match would be
#: unearned.  It gets its own class, and the fidelity claim is stated on ``MATCH``
#: over exact-recovery cycles.
MATCH = "MATCH"
PARTIAL_MATCH = "PARTIAL_MATCH"
PORT_OR_LIVE_DEFECT = "DISAGREEMENT"
EVIDENCE_GAP = "EVIDENCE_GAP"

#: A cycle whose recorded units carry two different Kelly day-counts.  That
#: cannot happen inside one ``size_correlated_units`` call for one day
#: (``admission.py:1166-1170`` resolves ``na`` once per ``decision_day``), so it
#: proves the cycle's intents spanned two day keys.  Measured on 12 cycles; see
#: the defect register.  Such a cycle cannot be replayed from a single supplied
#: count, so it is reported rather than compared.
MULTI_DAY_KELLY = "MULTI_DAY_KELLY_IN_ONE_CYCLE"


class ValidationError(ValueError):
    """The validation could not be performed, and refuses to report a number."""


# ---------------------------------------------------------------------------
# packet reading
# ---------------------------------------------------------------------------
def iter_packets(path: str | Path) -> Iterator[dict[str, Any]]:
    """Stream packets from a plain or gzipped JSONL export.

    Refuses a git-LFS pointer stub explicitly.  A 131-byte pointer parses as
    neither JSON nor an empty file, and reading one as "no packets" is this
    programme's signature failure mode (`WAVE_2_WORKING_AGREEMENT.md`).
    """

    path = Path(path)
    if not path.is_file():
        raise ValidationError(f"packet_source_absent:{path}")
    with open(path, "rb") as probe:
        head = probe.read(64)
    if head.startswith(b"version https://git-lfs"):
        raise ValidationError(f"packet_source_is_unhydrated_lfs_pointer:{path}")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:  # type: ignore[operator]
        for index, line in enumerate(handle):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                raise ValidationError(f"packet_row_invalid:{path}:{index}") from None
            if isinstance(row, dict):
                yield row


@dataclass
class Cycle:
    """One reconstructed ``book_engine.evaluate`` call."""

    cycle_id: str
    namespace: str
    created_at_utc: str
    bridge: Mapping[str, Any]
    packets: list[dict[str, Any]] = field(default_factory=list)

    @property
    def would_units(self) -> list[dict[str, Any]]:
        return [dict(u) for u in (self.bridge.get("would_units") or [])]

    @property
    def decision_days(self) -> list[str]:
        days = {str(p.get("decision_day"))[:10] for p in self.packets if p.get("decision_day")}
        return sorted(days)


def _cycle_key(packet: Mapping[str, Any]) -> str:
    """A stable id for the ``evaluate`` call a packet belongs to.

    One cycle writes one ``bridge`` snapshot onto every packet it emits, so the
    snapshot's digest plus the namespace and the emit minute identifies the
    cycle.  The digest covers ``would_units`` and ``governor``, which change
    between cycles whenever anything decided differently; two genuinely
    identical adjacent cycles would merge, and that is reported as a candidate
    count mismatch rather than hidden.
    """

    bridge = packet.get("bridge") or {}
    material = {
        key: bridge.get(key)
        for key in (
            "would_units",
            "realized_units",
            "governor",
            "n_candidates_in",
            "n_candidates_after_drop",
            "would_total_risk_pct",
            "decision_status",
            "dropped_symbols",
        )
    }
    digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]
    return f"{packet.get('namespace')}|{str(packet.get('created_at_utc'))[:16]}|{digest}"


def group_cycles(packets: Iterable[Mapping[str, Any]]) -> list[Cycle]:
    """Group packets into decision cycles, preserving first-seen order."""

    out: dict[str, Cycle] = {}
    for packet in packets:
        if packet.get("event_type") not in CYCLE_EVENTS:
            continue
        key = _cycle_key(packet)
        cycle = out.get(key)
        if cycle is None:
            cycle = Cycle(
                cycle_id=key,
                namespace=str(packet.get("namespace") or ""),
                created_at_utc=str(packet.get("created_at_utc") or ""),
                bridge=dict(packet.get("bridge") or {}),
            )
            out[key] = cycle
        cycle.packets.append(dict(packet))
    return list(out.values())


# ---------------------------------------------------------------------------
# input reconstruction
# ---------------------------------------------------------------------------
def config_from_bridge(
    bridge: Mapping[str, Any], *, base: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """The config block the cycle actually ran under, from its own record.

    This is the fidelity point.  Replaying the *current* YAML would measure
    today's dial against yesterday's decisions; the recorded flags are what the
    live worker used, so they are what the policy is given.  Keys the packet does
    not carry fall back to ``base`` (normally the committed config) and are
    reported by :func:`reconstruct_cycle` so a fallback can never pass unnoticed.
    """

    cfg = dict(base or {})
    mapping = {
        "ultimate_book_profile": "profile",
        "ultimate_book_include_clean3": "include_clean3",
        "ultimate_book_include_clean4": "include_clean4",
        "ultimate_book_include_candidate_book": "include_candidate_book",
        "ultimate_book_candidate_book_profile": "candidate_book_profile",
        "ultimate_book_candidate_book_sleeves": "candidate_book_sleeves",
        "ultimate_book_include_market_expansion_book": "include_market_expansion_book",
        "ultimate_book_market_expansion_profile": "market_expansion_profile",
        "ultimate_book_market_expansion_policy": "market_expansion_policy",
        "ultimate_book_market_expansion_sleeves": "market_expansion_sleeves",
        "ultimate_book_overlays": "overlays",
        "ultimate_book_vp_acceptance": "vp_acceptance",
        "ultimate_book_stress_derisk": "stress_derisk",
        "ultimate_book_kelly_lite": "kelly_lite",
        "ultimate_book_kelly_conservative": "kelly_conservative",
        "ultimate_book_kelly_running_count": "kelly_running_count",
        "ultimate_book_derisk_mode": "derisk_mode",
        "ultimate_book_sqrt_n_pooling": "sqrt_n_pooling",
        "ultimate_book_drop_w7_symbols": "drop_w7_symbols",
        "ultimate_book_metals_confluence_gate": "metals_confluence_gate",
        "ultimate_book_symbol_damage_guard": "symbol_damage_guard",
        "ultimate_book_enabled": "enabled",
        "ultimate_book_apply_to_execution": "apply_to_execution",
        "ultimate_book_live_activation_allowed": "live_activation_allowed_by_config",
        "ultimate_book_live_broker_authority": "live_broker_authority",
    }
    used_fallback: list[str] = []
    for cfg_key, bridge_key in mapping.items():
        if bridge_key in bridge and bridge.get(bridge_key) is not None:
            cfg[cfg_key] = bridge[bridge_key]
        elif cfg_key not in cfg:
            used_fallback.append(cfg_key)
    # The bridge records the resolved market-expansion allowlist, so replaying it
    # as an explicit allowlist reproduces the same registry without re-resolving
    # a named policy that may have moved.
    if bridge.get("market_expansion_sleeves"):
        cfg["ultimate_book_market_expansion_sleeves"] = list(
            bridge["market_expansion_sleeves"]
        )
        cfg["ultimate_book_market_expansion_policy"] = (
            _P.MARKET_EXPANSION_EXPLICIT_ALLOWLIST_POLICY
        )
    # The broad selector must read as OFF or the bridge's replacement invariant
    # fails the whole cycle closed (bridge.py:473-477). Live had it off; the
    # packet does not carry selector_v4_*, so this is asserted from the record's
    # own decision_status rather than guessed.
    cfg.setdefault("selector_v4_enabled", False)
    cfg.setdefault("selector_v4_apply_to_execution", False)
    cfg["_config_fallback_keys"] = used_fallback
    return cfg


def recorded_na_values(units: Sequence[Mapping[str, Any]]) -> list[int]:
    """Every distinct Kelly day-count the recorded units carry, ascending.

    More than one means the cycle's intents spanned more than one
    ``decision_day``; see :data:`MULTI_DAY_KELLY`.
    """

    values: set[int] = set()
    for unit in units:
        for tag in unit.get("overlays_applied") or ():
            match = _KELLY_TAG.match(str(tag))
            if match:
                values.add(int(match.group(1)))
    return sorted(values)


def _recorded_stress(units: Sequence[Mapping[str, Any]]) -> Any:
    """A ``StressDeriskState`` reproducing the recorded ladder/co-loss tags."""

    consecutive = 0
    neg_frac = 0.0
    for unit in units:
        for tag in unit.get("overlays_applied") or ():
            match = _LADDER_TAG.match(str(tag))
            if match:
                consecutive = max(consecutive, int(match.group(1)))
            elif str(tag) == "coloss_breaker":
                neg_frac = max(neg_frac, _P.COLOSS_NEG_FRAC)
    return _P.StressDeriskState(
        consecutive_loss_days=consecutive, trailing_neg_frac=neg_frac
    )


def _state_reproducing_governor(
    governor: Mapping[str, Any],
    *,
    derisk_mode: str,
    static_initial_balance: float = 100000.0,
) -> tuple[AccountDayState, Any]:
    """Invert the recorded governor decision into a state + limits that yield it.

    ``smooth`` mode is ``cap_mult = 1 - dd / max_dd_limit`` (``admission.py:1301``),
    so ``dd = max_dd_limit * (1 - cap_mult)`` and the equity follows from the
    static max-DD reference the live config pins
    (``governor_static_initial_balance: 100000.0``).  ``band`` mode inverts its
    own linear segment.  ``available_gross_risk_pct`` is reproduced by setting
    the cap to it with zero open risk, which is the only split of
    ``cap - open_risk`` the record determines — and it is exactly the split that
    makes the shedding step behave identically, since shedding reads only the
    available headroom (``admission.py:1325``).

    The result is *verified* by the caller, not trusted.
    """

    cap_mult = float(governor.get("size_cap_multiplier", 1.0) or 0.0)
    available = float(governor.get("available_gross_risk_pct", 0.0) or 0.0)
    limits_base = _P.GovernorLimits()
    max_dd = limits_base.max_dd_limit_pct
    if derisk_mode == "smooth":
        drawdown = max_dd * (1.0 - min(max(cap_mult, 0.0), 1.0))
    else:
        start = limits_base.derisk_start_dd_pct
        drawdown = (
            0.0
            if cap_mult >= 1.0
            else start + (1.0 - cap_mult) * max(1e-9, max_dd - start)
        )
    equity = static_initial_balance * (1.0 - drawdown)
    limits = _P.GovernorLimits(
        soft_daily_stop_pct=limits_base.soft_daily_stop_pct,
        hard_daily_limit_pct=limits_base.hard_daily_limit_pct,
        max_dd_limit_pct=max_dd,
        max_dd_entry_block_pct=getattr(limits_base, "max_dd_entry_block_pct", max_dd),
        derisk_start_dd_pct=limits_base.derisk_start_dd_pct,
        gross_open_risk_cap_pct=available,
        derisk_mode=derisk_mode,
        # Profit-target protect multiplies cap_mult again (admission.py:1310-1314).
        # Leaving it at 0 keeps the inversion single-valued; a cycle where live
        # had it active will fail governor verification and be reported as a gap
        # rather than silently mis-sized.
        profit_target_pct=0.0,
        profit_target_derisk_mult=getattr(
            limits_base, "profit_target_derisk_mult", 0.25
        ),
    )
    state = AccountDayState(
        equity=equity,
        high_water=static_initial_balance,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=static_initial_balance,
    )
    return state, limits


# ---------------------------------------------------------------------------
# per-cycle replay
# ---------------------------------------------------------------------------
@dataclass
class CycleResult:
    cycle_id: str
    namespace: str
    created_at_utc: str
    decision_day: str | None
    status: str
    detail: dict[str, Any] = field(default_factory=dict)
    policy_units: list[dict[str, Any]] = field(default_factory=list)
    live_units: list[dict[str, Any]] = field(default_factory=list)
    field_differences: list[dict[str, Any]] = field(default_factory=list)


def _direction_of(packet: Mapping[str, Any]) -> tuple[int, bool]:
    """Recover the trade side, and say whether it was actually recorded.

    It usually was not.  ``direction`` is ``None`` on **14,916 of 15,768**
    ``unit_*`` packets (94.6 %) and ``candidate_id`` — whose 5th slot carries
    ``LONG``/``SHORT`` — is present on only **699** [MEASURED 2026-07-26].
    ``build_runtime_learning_packet`` reads the side off the *intent*
    (``runtime_learning_packet.py:225``), and the cycle-summary emitter passes
    only ``outcome``, which has no direction field.  See the defect register.

    Side does not enter the risk arithmetic: ``size_correlated_units`` reads it
    once, to check ``direction in (1, -1)`` (``admission.py:1146-1147``), and
    never again.  So a recovered-or-defaulted side reproduces live's pass through
    that check exactly, and the returned flag lets the receipt state plainly that
    side itself is not being validated.
    """

    raw = packet.get("direction")
    if isinstance(raw, bool):
        raw = None
    if isinstance(raw, (int, float)) and int(raw) in (1, -1):
        return int(raw), True
    text = str(raw or "").strip().upper()
    if text in ("LONG", "BUY", "1", "+1"):
        return 1, True
    if text in ("SHORT", "SELL", "-1"):
        return -1, True
    candidate_id = str(packet.get("candidate_id") or "")
    parts = candidate_id.split("::")
    if len(parts) >= 5:
        token = parts[4].strip().upper()
        if token == "LONG":
            return 1, True
        if token == "SHORT":
            return -1, True
    # A third source, found by adversarial review after this function first
    # shipped reading only the two above: the side survives nested inside
    # ``outcome.admission_unit_members[]`` on 827 packets, and for 277 of them
    # that is the ONLY place it survives. Missing it defaulted those to +1 while
    # reporting the side as unrecorded.
    outcome = packet.get("outcome")
    if isinstance(outcome, Mapping):
        members = outcome.get("admission_unit_members")
        if isinstance(members, (list, tuple)):
            sleeve = packet.get("sleeve")
            symbol = packet.get("symbol")
            for member in members:
                if not isinstance(member, Mapping):
                    continue
                if sleeve and member.get("sleeve") not in (None, sleeve):
                    continue
                if symbol and member.get("symbol") not in (None, symbol):
                    continue
                token = str(member.get("direction") or "").strip().upper()
                if token in ("LONG", "BUY", "1", "+1"):
                    return 1, True
                if token in ("SHORT", "SELL", "-1"):
                    return -1, True
    return 1, False


def _candidates_from_cycle(cycle: Cycle) -> tuple[list[PolicyCandidate], dict[str, Any]]:
    """Rebuild the cycle's intent set from its own packets.

    Deduplicated on ``(sleeve, symbol, decision_day)`` because a cycle emits one
    packet per intent but a retry can emit two for the same intent, and the
    sizer's ``n_trades`` counts intents.  ``stop_dist`` is set to a positive
    sentinel: the packet does not carry it, and it does not enter the risk-percent
    arithmetic at all — it only has to be > 0 to clear the fail-closed check
    (``admission.py:1148``).  Lot conversion, which is where ``stop_dist``
    actually matters, is downstream of every number compared here.
    """

    seen: set[tuple[str, str, str]] = set()
    out: list[PolicyCandidate] = []
    sides_recorded = 0
    for packet in cycle.packets:
        sleeve = packet.get("sleeve")
        symbol = packet.get("symbol")
        day = str(packet.get("decision_day") or "")[:10]
        if not sleeve or not symbol or not day:
            continue
        key = (str(sleeve), str(symbol), day)
        if key in seen:
            continue
        seen.add(key)
        side, recorded = _direction_of(packet)
        sides_recorded += int(recorded)
        out.append(
            PolicyCandidate(
                sleeve=str(sleeve),
                symbol=str(symbol),
                direction=side,
                decision_day=day,
                stop_dist=1.0,
                decision_bar_iso=packet.get("decision_bar_iso"),
                timeframe=packet.get("timeframe"),
            )
        )
    return out, {
        "sides_recorded": sides_recorded,
        "sides_defaulted": len(out) - sides_recorded,
        "stop_dist": "sentinel_1.0_not_recorded_and_not_used_in_risk_pct",
    }


def _normalise(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [_normalise(v) for v in value]
    if isinstance(value, float):
        return round(value, 10)
    return value


def _compare_units(
    policy_units: Sequence[Mapping[str, Any]],
    live_units: Sequence[Mapping[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Align on ``(cluster, sleeve_members)`` and diff every compared field.

    Alignment is by identity rather than position because a missing or extra
    unit must show up as exactly that, not as a cascade of field differences on
    mis-paired rows.
    """

    def key(unit: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
        return (
            str(unit.get("cluster", "")),
            tuple(sorted(unit.get("sleeve_members") or ())),
        )

    def index(units: Sequence[Mapping[str, Any]]) -> dict[tuple[Any, ...], dict[str, Any]]:
        """Index by ``(cluster, members, occurrence)``.

        The occurrence counter is load-bearing.  Keying on ``(cluster, members)``
        alone made two units with the same key collapse to the last one, so a
        whole live unit could vanish with **zero** reported difference — a silent
        false MATCH.  Adversarial review demonstrated it and found one real cycle
        (``redacted_account_live_bee34003``, 2026-06-25T01:00) where live emits two
        ``index|idxrev`` units in one cycle, which is possible because the
        correlated-unit key is ``(decision_day, cluster)`` and that cycle spans
        two decision days.
        """

        seen: dict[tuple[str, tuple[str, ...]], int] = {}
        out: dict[tuple[Any, ...], dict[str, Any]] = {}
        for unit in units:
            base = key(unit)
            occurrence = seen.get(base, 0)
            seen[base] = occurrence + 1
            out[(*base, occurrence)] = dict(unit)
        return out

    left = index(policy_units)
    right = index(live_units)
    differences: list[dict[str, Any]] = []
    for unit_key in sorted(set(left) | set(right)):
        lhs = left.get(unit_key)
        rhs = right.get(unit_key)
        label = f"{unit_key[0]}|{'+'.join(unit_key[1])}"
        if unit_key[2]:
            label += f"#{unit_key[2]}"
        if lhs is None or rhs is None:
            differences.append(
                {
                    "unit": label,
                    "field": "__present__",
                    "policy": lhs is not None,
                    "live": rhs is not None,
                }
            )
            continue
        for name in COMPARED_UNIT_FIELDS:
            lv = _normalise(lhs.get(name))
            rv = _normalise(rhs.get(name))
            if lv != rv:
                differences.append(
                    {"unit": label, "field": name, "policy": lv, "live": rv}
                )
    return (MATCH if not differences else PORT_OR_LIVE_DEFECT), differences


def reconstruct_cycle(
    cycle: Cycle,
    *,
    base_config: Mapping[str, Any] | None = None,
    derive_n_active: bool = False,
    static_initial_balance: float = 100000.0,
) -> CycleResult:
    """Replay one cycle through ``SleeveBookPolicy`` and compare.

    ``derive_n_active=True`` withholds the recorded Kelly count so the sizer
    computes it from this cycle's own intents.  That measures the
    running-conviction divergence instead of assuming it away.
    """

    bridge = cycle.bridge
    days = cycle.decision_days
    day = days[0] if len(days) == 1 else None
    result = CycleResult(
        cycle_id=cycle.cycle_id,
        namespace=cycle.namespace,
        created_at_utc=cycle.created_at_utc,
        decision_day=day,
        status=EVIDENCE_GAP,
    )
    live_units = cycle.would_units
    result.live_units = live_units

    governor = bridge.get("governor")
    candidates, candidate_notes = _candidates_from_cycle(cycle)
    n_in = bridge.get("n_candidates_in")

    # A cycle that decided nothing is a real comparison, not a gap: live sized no
    # units, and a faithful policy must also size none.  Counting these as
    # evidence gaps would discard the 4,325 `cycle_no_candidates` cycles.
    #
    # It must be EARNED, though.  An earlier version returned MATCH here before
    # constructing the policy at all, which made 4,306 of 4,908 reported matches
    # free greens on a comparison that never ran — the exact failure this comment
    # used to warn against while the code below it committed it.  Adversarial
    # review caught it.  The policy is now actually invoked on the empty candidate
    # set and must produce no units; anything else is a disagreement.
    if not live_units and not candidates and not n_in:
        result.detail.update(
            {
                "kind": "empty_cycle",
                "n_candidates_in_recorded": n_in,
                "decision_status": bridge.get("decision_status"),
            }
        )
        try:
            empty_policy = SleeveBookPolicy(
                config_from_bridge(bridge, base=base_config), strict_config=False
            )
        except Exception as exc:  # noqa: BLE001
            result.detail["reason"] = f"policy_construction_failed:{exc}"
            return result
        empty_decision = empty_policy.decide(
            [],
            AccountDayState(
                equity=static_initial_balance,
                high_water=static_initial_balance,
                realized_today_pct=0.0,
                open_risk_pct=0.0,
                max_dd_reference_equity=static_initial_balance,
                account="A",
                namespace=cycle.namespace,
            ),
        )
        produced = [u.as_dict() for u in empty_decision.units]
        result.policy_units = produced
        if produced:
            result.status = PORT_OR_LIVE_DEFECT
            result.field_differences = [
                {
                    "unit": f"{u['cluster']}|{'+'.join(u['members'])}",
                    "field": "__present__",
                    "policy": True,
                    "live": False,
                }
                for u in produced
            ]
        else:
            result.status = MATCH
        return result

    if not isinstance(governor, Mapping):
        result.detail["reason"] = "governor_absent_from_record"
        return result
    if not live_units:
        # Live had candidates but sized nothing, or the packet predates the
        # would_units field. Either way there is no sized book to compare.
        result.detail["reason"] = (
            "candidates_present_but_no_would_units_in_record"
            if (candidates or n_in)
            else "no_would_units_in_record"
        )
        return result
    if len(days) != 1:
        # Multi-day or day-less cycles cannot have their Kelly day-key resolved
        # from the record, and guessing it would change the multiplier.
        result.detail["reason"] = f"decision_day_not_unique:{days}"
        return result
    if not candidates:
        result.detail["reason"] = "no_intents_recoverable_from_packets"
        return result

    cfg = config_from_bridge(bridge, base=base_config)
    fallback_keys = cfg.pop("_config_fallback_keys", [])
    derisk_mode = str(cfg.get("ultimate_book_derisk_mode") or "band")

    state, limits = _state_reproducing_governor(
        governor,
        derisk_mode=derisk_mode,
        static_initial_balance=static_initial_balance,
    )
    na_values = recorded_na_values(live_units)
    if len(na_values) > 1:
        # Two Kelly day-counts in one cycle: the intents spanned two day keys, so
        # no single supplied count can reproduce the cycle. Reported, not forced.
        result.status = MULTI_DAY_KELLY
        result.detail.update(
            {
                "reason": "multiple_kelly_day_counts_in_one_cycle",
                "recorded_na_values": na_values,
                "packet_decision_days": days,
                "live_units": [
                    {
                        "cluster": u.get("cluster"),
                        "sleeve_members": list(u.get("sleeve_members") or ()),
                        "overlays_applied": list(u.get("overlays_applied") or ()),
                    }
                    for u in live_units
                ],
            }
        )
        return result
    n_active_override = (
        None if derive_n_active or not na_values else {day: na_values[0]}
    )
    cycle_inputs: dict[str, Any] = {
        "limits": limits,
        "stress_state": _recorded_stress(live_units),
        "n_active_override": n_active_override,
    }
    state = AccountDayState(
        equity=state.equity,
        high_water=state.high_water,
        realized_today_pct=state.realized_today_pct,
        open_risk_pct=state.open_risk_pct,
        max_dd_reference_equity=state.max_dd_reference_equity,
        account="A",
        namespace=cycle.namespace,
        cycle=cycle_inputs,
    )

    try:
        policy = SleeveBookPolicy(cfg, strict_config=False)
    except Exception as exc:  # noqa: BLE001
        result.detail["reason"] = f"policy_construction_failed:{exc}"
        return result
    decision = policy.decide(candidates, state)

    # VERIFY the reconstruction before trusting anything downstream of it.
    produced = dict(decision.governor or {})
    governor_fields = (
        "allow_new_entries",
        "size_cap_multiplier",
        "available_gross_risk_pct",
        "reason",
    )
    governor_mismatch = {
        name: {"policy": produced.get(name), "live": governor.get(name)}
        for name in governor_fields
        if _normalise(produced.get(name)) != _normalise(governor.get(name))
    }
    result.detail.update(
        {
            "n_candidates_in_recorded": n_in,
            "n_intents_reconstructed": len(candidates),
            "recorded_na": na_values[0] if na_values else None,
            "n_active_mode": "derived" if derive_n_active else "supplied",
            "derisk_mode": derisk_mode,
            "config_fallback_keys": fallback_keys,
            "candidate_recovery": candidate_notes,
            "governor_reconstruction": (
                "verified" if not governor_mismatch else "failed"
            ),
        }
    )
    if governor_mismatch:
        result.detail["governor_mismatch"] = governor_mismatch
        result.detail["reason"] = "governor_reconstruction_unverified"
        return result

    policy_units = [u.as_dict() for u in decision.units]
    # Re-key the policy's units into the live field names so the comparison is
    # over the live schema, not the port's rename of it.
    renamed = [
        {
            "cluster": u["cluster"],
            "sleeve_members": list(u["members"]),
            "n_trades": u["n_trades"],
            "confidence": u["confidence"],
            "risk_pct_per_trade": u["risk_pct_per_trade"],
            "unit_risk_pct": u["unit_risk_pct"],
            "sized": u["sized"],
            "reason": u["reason"],
            "overlays_applied": list(u["tags"]),
        }
        for u in policy_units
    ]
    normalised_live = [
        {
            **{k: v for k, v in u.items() if k in COMPARED_UNIT_FIELDS},
            "sleeve_members": list(u.get("sleeve_members") or ()),
            "overlays_applied": list(u.get("overlays_applied") or ()),
        }
        for u in live_units
    ]
    result.policy_units = renamed
    result.live_units = normalised_live
    status, differences = _compare_units(renamed, normalised_live)
    result.field_differences = differences

    # Intent recovery decides which class a clean comparison lands in. It is
    # measured against the cycle's own recorded candidate count, never assumed.
    try:
        recovery = (
            "exact"
            if int(n_in) == len(candidates)
            else ("short" if int(n_in) > len(candidates) else "excess")
        )
    except (TypeError, ValueError):
        recovery = "unknown"
    result.detail["intent_recovery"] = recovery
    missing_only = [d for d in differences if d.get("field") == "__present__"]
    field_only = [d for d in differences if d.get("field") != "__present__"]
    if not differences:
        result.status = MATCH if recovery == "exact" else PARTIAL_MATCH
    elif field_only:
        # A field difference on a co-present unit is a real disagreement whatever
        # the recovery status: both sides had the unit and sized it differently.
        result.status = PORT_OR_LIVE_DEFECT
    elif recovery == "exact":
        # Units missing with a complete intent set has no benign explanation.
        result.status = PORT_OR_LIVE_DEFECT
    else:
        result.status = PARTIAL_MATCH
        result.detail["units_unmatched_attributed_to_intent_recovery"] = len(
            missing_only
        )
    return result


def validate(
    packet_path: str | Path,
    *,
    base_config: Mapping[str, Any] | None = None,
    namespaces: Sequence[str] | None = None,
    days: Sequence[str] | None = None,
    derive_n_active: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """Replay every reconstructable cycle and report.

    Returns a receipt.  Disagreements are **enumerated**, not summarised: a match
    rate hides the interesting rows, and the interesting rows are the deliverable.
    """

    cycles = group_cycles(iter_packets(packet_path))
    if namespaces:
        wanted = set(namespaces)
        cycles = [c for c in cycles if c.namespace in wanted]
    if days:
        wanted_days = set(days)
        cycles = [c for c in cycles if set(c.decision_days) & wanted_days]
    if limit is not None:
        cycles = cycles[: int(limit)]

    results = [
        reconstruct_cycle(
            c,
            base_config=base_config,
            derive_n_active=derive_n_active,
        )
        for c in cycles
    ]
    matched = [r for r in results if r.status == MATCH]
    partial = [r for r in results if r.status == PARTIAL_MATCH]
    disagreed = [r for r in results if r.status == PORT_OR_LIVE_DEFECT]
    gaps = [r for r in results if r.status == EVIDENCE_GAP]
    multi_day = [r for r in results if r.status == MULTI_DAY_KELLY]

    gap_reasons: dict[str, int] = {}
    for r in gaps:
        reason = str(r.detail.get("reason", "unclassified"))
        gap_reasons[reason] = gap_reasons.get(reason, 0) + 1

    field_counts: dict[str, int] = {}
    for r in disagreed + partial:
        for diff in r.field_differences:
            key = str(diff.get("field"))
            field_counts[key] = field_counts.get(key, 0) + 1

    compared_units = sum(len(r.live_units) for r in matched + partial + disagreed)
    exact_units = sum(len(r.live_units) for r in matched)
    return {
        "schema": SCHEMA,
        "packet_source": str(packet_path),
        "n_active_mode": "derived" if derive_n_active else "supplied",
        "filters": {
            "namespaces": list(namespaces or ()),
            "days": list(days or ()),
            "limit": limit,
        },
        "totals": {
            "cycles_grouped": len(cycles),
            "cycles_compared": len(matched) + len(partial) + len(disagreed),
            "cycles_matching_exact_recovery": len(matched),
            "cycles_matching_partial_recovery": len(partial),
            "cycles_disagreeing": len(disagreed),
            "cycles_multi_day_kelly": len(multi_day),
            "cycles_evidence_gap": len(gaps),
            "units_compared": compared_units,
            "units_compared_exact_recovery": exact_units,
            "field_differences": sum(field_counts.values()),
        },
        "evidence_gap_reasons": gap_reasons,
        "field_difference_counts": field_counts,
        "multi_day_kelly_cycles": [
            {
                "cycle_id": r.cycle_id,
                "namespace": r.namespace,
                "created_at_utc": r.created_at_utc,
                "detail": r.detail,
            }
            for r in multi_day
        ],
        "disagreements": [
            {
                "cycle_id": r.cycle_id,
                "namespace": r.namespace,
                "created_at_utc": r.created_at_utc,
                "decision_day": r.decision_day,
                "detail": r.detail,
                "differences": r.field_differences,
                "policy_units": r.policy_units,
                "live_units": r.live_units,
            }
            for r in disagreed
        ],
    }


# ---------------------------------------------------------------------------
# arm-shaped output for the differential harness
# ---------------------------------------------------------------------------
#: The role the ledgers are written as.  ``order`` is chosen because it is NOT in
#: ``task2.EXACT_ROLES`` (so the allowlist can classify a volatile clock field)
#: and because it has a measured-unique identity key contract, which is the
#: property identity alignment needs.
LEDGER_ROLE = "order"
IDENTITY_FIELD = "policy_unit_identity"


def _ledger_rows(results: Sequence[CycleResult], *, side: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        units = result.policy_units if side == "policy" else result.live_units
        for unit in units:
            identity = "|".join(
                [
                    result.namespace,
                    result.cycle_id,
                    str(unit.get("cluster", "")),
                    "+".join(sorted(unit.get("sleeve_members") or ())),
                ]
            )
            rows.append(
                {
                    IDENTITY_FIELD: identity,
                    "order_event_stage": "policy_decision",
                    "decision_day": result.decision_day,
                    "namespace": result.namespace,
                    **{k: unit.get(k) for k in COMPARED_UNIT_FIELDS},
                }
            )
    rows.sort(key=lambda r: r[IDENTITY_FIELD])
    return rows


def ledger_pair(
    results: Sequence[CycleResult],
    destination: str | Path,
    *,
    prefix: str = "SLEEVE_BOOK_POLICY_V1_S0R0",
) -> dict[str, Path]:
    """Write ``policy/`` and ``live/`` arm-shaped directories, plus a null control.

    The null control is a byte-identical copy of the policy side.  Comparing it
    against itself must return ``EQUIVALENT``; if it does not, the comparator or
    the serialisation is broken and no other verdict from this run means
    anything.
    """

    from src.research_infra import replay_acceleration_task2_semantic_acceptance as task2

    suffix = task2.ROLE_SUFFIXES[LEDGER_ROLE]
    destination = Path(destination)
    out: dict[str, Path] = {}
    sides = {
        "policy": _ledger_rows(results, side="policy"),
        "live": _ledger_rows(results, side="live"),
    }
    sides["null_control"] = list(sides["policy"])
    for side, rows in sides.items():
        arm_dir = destination / side
        arm_dir.mkdir(parents=True, exist_ok=True)
        path = arm_dir / f"{prefix}_{suffix}"
        with open(path, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        out[side] = arm_dir
    return out
