"""Leftover fluid trading-decision ifs as a hierarchical tree.

Seats already loaded on the Challenge writer (gate / admission / size /
close, remaining_seats RS-*, exec_gov_news EXEC-*/news/governor, gold
priors/entry/exit, followthrough F5-MS-*) do **not** own these leftovers:
companion pause/cooldown/zero-risk, occupancy after a close (KEEP-one /
isolated re-entry), weekend embargo *judgment*, overlay
VP/damage/energy/impulse/session, Kelly/stress/coloss/voltilt/doomed-na/
lane-band/cluster-corr size bins, frontier-exit cell study, research
observe (selector packet / fill atom / wait-vs-trade / whiteboard).

Remaining packs own the occupancy subtree and the include-depth hops.
Do not dump a sibling 57-key gold catalog. Occupancy is a named seat,
not ``isolated_reentry_is_new`` from the gold tree.

Founder brief: Noul per **context chunk**, Score include-depth
hide/short/long/full, many TypeSafe calls from one intent, hierarchical
labels + log(n) tree. Not linear binary keep/drop. One completeness Noul
on *this* object. Do not Noul every tick because it is cheap. Do not
compact a Challenge session.

Code owns workflow (token digest, 2-stop COUNT, tags/$KILL, prop walls,
H8, FLATTEN.flag, occupancy keep-one, USDJPY HOLD, H4CAP, weekend-flat
close, never-widen, auto-BE OFF, 8pip, min-stop, retry cap, $150,
CALPRIME/Q1FLOOR dark, SEL-V4 research). TypeSafe owns the semantic
keep/route that used to be a static if.

This module does **not** edit ``jev_questions.py``, ``book_owner.py``,
``execution.py``, ``followthrough.py``, ``followthrough_ifs.py``,
``remaining_seats.py``, ``size_exit.py``, or ``gold_priors.py``.
Subtree questions live here. Dump through stacked
``evaluate(questions=..., merge_sleeve=False)``. Two reads from one
intent (include-depth, then the decision pack).

Research seats never place and never import ``selector_v4``.

Pin model ``jev-1.13.0``. Challenge book ``0`` / ``operator``.

Every decision this module returns, including every parameter, is the
System One value for that state. ``evaluate_decisions`` and
``post_questions`` ask through ``jev_client.evaluate`` (model
``jev-1.13.0``, ``merge_sleeve=False``, POST
https://api.typesafe.ai/v1/systemone). The return is only a Noul, a
Choice, or a Score. Prior outcomes are attached on that ask and the
return is stored for the next ask. An empty answer, a tie, or an error
leaves that return unset. A floor and a baseline are not a question.
This module does not send and does not flatten.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

try:
    from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS
except Exception:
    CHALLENGE_LOGIN = 0
    CHALLENGE_MAGIC = 0
    CHALLENGE_NS = "operator"

try:
    from .jev_questions import MODEL
except Exception:
    MODEL = "jev-1.13.0"

INCLUDE_DEPTH_LEVELS = ("hide", "short", "long", "full")
INCLUDE_DEPTH_CRITERIA = [
    "Hide this chunk — not needed for this fire's query",
    "Short summary of the named fields in this chunk",
    "Longer summary of the named fields in this chunk",
    "Include the whole named chunk",
]

SEATS = (
    "companion",
    "occupancy",
    "weekend",
    "overlay",
    "size_bins",
    "frontier",
    "research",
)
BRANCHES = ("observe", "size", "place")
MONEY_SEATS = ("companion", "occupancy", "weekend")

SEAT_CHUNKS: dict[str, tuple[str, ...]] = {
    "companion": ("snapshot", "cooldown", "zero_risk"),
    "occupancy": ("keep_one", "flat_clock", "already_placed"),
    "weekend": ("clock", "sleeve_weekend", "policy"),
    "overlay": ("vp_loc", "damage", "energy", "impulse", "session"),
    "size_bins": ("kelly", "stress", "coloss", "voltilt", "na", "lane", "cluster"),
    "frontier": ("geometry", "contract"),
    "research": ("packet", "fill_atom", "allocator", "whiteboard"),
}

BRANCH_SEATS: dict[str, tuple[str, ...]] = {
    "observe": ("companion", "weekend", "overlay", "frontier", "research"),
    "size": ("size_bins", "overlay"),
    "place": ("companion", "weekend"),
}

INTEGER_FACTS: tuple[str, ...] = (
    "token_digest_match",
    "two_stop_count",
    "named_surface",
    "prop_wall",
    "halt",
    "operator_flatten_flag",
    "occupancy_keep_one",
    "usdjpy_hold",
    "h4cap",
    "weekend_flat_close",
    "never_widen",
    "auto_be_off",
    "fx_dsp_8pip",
    "min_stop_ticks",
    "retry_cap",
    "tuition_150",
    "calprime_q1floor_dark",
    "sel_v4_research_never_place",
    "tags_kill",
    "h8_authority_does_not_flatten",
)

# Leftover IDs this unique PR converts. Do not claim remaining_seats
# already_placed / remint / restart / ac60 emit, exec_gov_news EXEC-*,
# gold seats, or followthrough F5-MS-* leftover.
CONVERTED_IFS: tuple[dict[str, str], ...] = (
    {
        "id": "UB-PLC-004",
        "was": "AI companion pause blocks place",
        "now": "Score companion_pause_fit; missing answers leave-orig, no extra place",
        "seat": "companion",
        "branch": "place",
    },
    {
        "id": "UB-PLC-005",
        "was": "AI companion cooldown_for reason skip",
        "now": "Score companion_cooldown_fit; integer cooldown clock stays",
        "seat": "companion",
        "branch": "observe",
    },
    {
        "id": "UB-PLC-008",
        "was": "AI companion zero-risk block",
        "now": "Score companion_zero_risk_fit; integer zero-risk still binds",
        "seat": "companion",
        "branch": "place",
    },
    {
        "id": "UB-PLC-OCC",
        "was": "already_placed_today skip / occupancy HOLD as remint intel",
        "now": "occupancy_after_close on THIS remaining pack; HOLD dead; keep-one integer; already-placed cannot lift",
        "seat": "occupancy",
        "branch": "observe",
    },
    {
        "id": "UB-PLC-007",
        "was": "weekend_entry_embargo when weekend policy on",
        "now": "Score weekend_carry overlay; integer Friday weekend-flat close stays",
        "seat": "weekend",
        "branch": "observe",
    },
    {
        "id": "UB-ADM-009",
        "was": "VP above_va drop",
        "now": "Noul vp_above_va; integer drop-list stays until named",
        "seat": "overlay",
        "branch": "observe",
    },
    {
        "id": "UB-ADM-012",
        "was": "QUARANTINE drop / RISK_REDUCE 0.5 tilt",
        "now": "Noul damage_consistency; integer QUARANTINE 0.0 still drops",
        "seat": "overlay",
        "branch": "observe",
    },
    {
        "id": "UB-ADM-ENERGY",
        "was": "drop illiquid energy HEATOIL/NATGAS when flag on",
        "now": "Noul energy_still_hurtful; integer drop-list today",
        "seat": "overlay",
        "branch": "observe",
    },
    {
        "id": "UB-ADM-OVERLAY-IMPULSE",
        "was": "overlay veto when leader impulse none/opposed",
        "now": "Score impulse_range; overlay stays default-off until named",
        "seat": "overlay",
        "branch": "size",
    },
    {
        "id": "UB-ADM-OVERLAY-SESSION",
        "was": "session overlay 1.15x at H4 8/12/16",
        "now": "Score overlay_session_hour; size-up cap stays envelope",
        "seat": "overlay",
        "branch": "size",
    },
    {
        "id": "UB-ADM-KELLY",
        "was": "KELLY_LITE_BINS vs HALF as dead numbers",
        "now": "Score kelly_bin_vs_tape; integer bins until named wire",
        "seat": "size_bins",
        "branch": "size",
    },
    {
        "id": "UB-ADM-STRESS",
        "was": "stress ladder shrinks size from loss streak",
        "now": "Score stress_streak; integer ladder until named; no extra headroom",
        "seat": "size_bins",
        "branch": "size",
    },
    {
        "id": "UB-ADM-COLOSS",
        "was": "coloss breaker trailing-5d neg fraction 0.57",
        "now": "Noul coloss_continuation; integer trip stays; do not move 0.57",
        "seat": "size_bins",
        "branch": "size",
    },
    {
        "id": "UB-ADM-VOLTILT",
        "was": "vr tilt on sub_xvol (--vol-level-tilt default OFF)",
        "now": "Score voltilt_vr; integer flag stays OFF; no extra PASS",
        "seat": "size_bins",
        "branch": "size",
    },
    {
        "id": "UB-ADM-NA-DOOMED",
        "was": "unplaced/doomed sleeve still increments Kelly na",
        "now": "Score na_doomed_honest; integer na monotone is physics",
        "seat": "size_bins",
        "branch": "size",
    },
    {
        "id": "UB-LANE-BAND",
        "was": "lane weight if outside [0.50,1.15] refuse",
        "now": "Score lane_inside_band; band is envelope; inside is fluid",
        "seat": "size_bins",
        "branch": "size",
    },
    {
        "id": "UB-ADM-CLUSTER-CORR",
        "was": "size units as independent instead of cluster members",
        "now": "Score cluster_corr_order; never invent a second unit",
        "seat": "size_bins",
        "branch": "size",
    },
    {
        "id": "UB-PLC-FRONTIER",
        "was": "frontier_exits 2R vs 5R vs 4R as arming if",
        "now": "Score frontier_cell_fit; arming is integer; never arm from this pack",
        "seat": "frontier",
        "branch": "observe",
    },
    {
        "id": "SEL-V4-002",
        "was": "selector packet floors 0.10/0.58/0.45 as cliffs",
        "now": "Score packet_quality observe; never place; never import selector_v4",
        "seat": "research",
        "branch": "observe",
    },
    {
        "id": "SEL-V4-FILL-F13",
        "was": "package_execution_fill_probability None as a mute if",
        "now": "Noul fillability; fail-closed missing provenance; observe only",
        "seat": "research",
        "branch": "observe",
    },
    {
        "id": "SCH-V4-ZERO",
        "was": "zero-trade competitor vs 0.35 floor as a mute if",
        "now": "wait_vs_trade named wait|trade|abstain; wait is first-class; never place",
        "seat": "research",
        "branch": "observe",
    },
    {
        "id": "PERM-006",
        "was": "whiteboard quality hard-actions as a mute if",
        "now": "Score whiteboard_session; integer hard actions stay; observe only",
        "seat": "research",
        "branch": "observe",
    },
)

FORBIDDEN_INSTRUCTION_TOKENS = ("jev", "system one", "choice")


def converted_ifs() -> tuple[dict[str, str], ...]:
    return CONVERTED_IFS


def converted_if_ids() -> tuple[str, ...]:
    return tuple(row["id"] for row in CONVERTED_IFS)


def seats_for_branch(branch: str, seats: Iterable[str] | None = None) -> tuple[str, ...]:
    if seats:
        named = tuple(s for s in seats if s in SEATS)
        if named:
            return named
    return BRANCH_SEATS.get(branch, ("companion",))


def hierarchical_labels(
    state: Mapping[str, Any] | None,
    *,
    seat: str,
    branch: str,
) -> dict[str, Any]:
    """book → fire → when → occupancy → ticket. Flat keys stay for compose."""
    st = dict(state or {})
    identity = dict(st.get("identity") or {})
    clock = dict(st.get("clock") or {})
    account = st.get("account") if isinstance(st.get("account"), Mapping) else {}
    occ = st.get("occupancy") if isinstance(st.get("occupancy"), Mapping) else {}
    keep = occ.get("keep_one") if isinstance(occ.get("keep_one"), Mapping) else {}
    already = occ.get("already_placed") if isinstance(occ.get("already_placed"), Mapping) else {}
    flat = occ.get("flat_clock") if isinstance(occ.get("flat_clock"), Mapping) else {}
    sleeve = identity.get("sleeve") or st.get("sleeve") or keep.get("sleeve") or "_"
    symbol = identity.get("symbol") or st.get("symbol") or keep.get("symbol") or "_"
    side = identity.get("side") or "_"
    day = identity.get("decision_day") or clock.get("decision_day") or "_"
    ticket = identity.get("ticket") or st.get("ticket") or keep.get("ticket") or "_"
    family = seat if seat in SEATS else "companion"
    occupancy_layer = {
        "hold_dead": occ.get("hold_dead") if "hold_dead" in occ else flat.get("hold_dead"),
        "keep_one": keep.get("occupied") if keep else occ.get("symbol_open"),
        "already_placed": (
            already.get("already_placed_today") if already else occ.get("already_placed_today")
        ),
        "minutes_since_flat": (
            flat.get("minutes_since_flat") if flat else occ.get("minutes_since_flat")
        ),
        "live_ticket": keep.get("ticket") or occ.get("live_open_ticket") or ticket,
    }
    book_layer = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "equity": account.get("equity") if isinstance(account, Mapping) else None,
        "to_pass": account.get("to_pass") if isinstance(account, Mapping) else None,
    }
    fire_layer = {
        "sleeve": sleeve,
        "symbol": symbol,
        "side": side,
        "family_node": family,
    }
    when_layer = {
        "decision_day": day,
        "as_of_utc": clock.get("as_of_utc"),
        "branch": branch,
    }
    return {
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "origin": identity.get("origin_organism") or "f5_challenge",
        "family_node": family,
        "sleeve": sleeve,
        "symbol": symbol,
        "side": side,
        "decision_day": day,
        "ticket": ticket,
        "subgoal": f"remaining_ifs:{family}:{branch}",
        "branch": branch,
        "seat": family,
        "model": MODEL,
        "occupancy": occupancy_layer,
        "layers": {
            "book": book_layer,
            "fire": fire_layer,
            "when": when_layer,
            "occupancy": occupancy_layer,
            "ticket": ticket,
        },
    }


def live_occupancy_chunks(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Named occupancy chunks for THIS hop. Not a 57-key gold catalog."""
    st = dict(state or {})
    occ_in = st.get("occupancy") if isinstance(st.get("occupancy"), Mapping) else {}
    keep = dict(occ_in.get("keep_one") or {}) if isinstance(occ_in.get("keep_one"), Mapping) else {}
    flat = dict(occ_in.get("flat_clock") or {}) if isinstance(occ_in.get("flat_clock"), Mapping) else {}
    already = (
        dict(occ_in.get("already_placed") or {})
        if isinstance(occ_in.get("already_placed"), Mapping)
        else {}
    )
    if occ_in.get("symbol_open") is False:
        keep["occupied"] = False
    elif occ_in.get("symbol_open") is True and "occupied" not in keep:
        keep["occupied"] = True
    if "symbol_open" not in flat and "occupied" in keep:
        flat["symbol_open"] = keep.get("occupied")
    if "minutes_since_flat" not in flat:
        flat["minutes_since_flat"] = occ_in.get("minutes_since_flat")
    if "hold_dead" not in flat and occ_in.get("hold_dead") is not None:
        flat["hold_dead"] = occ_in.get("hold_dead")
    if flat.get("isolated_reentry_minutes") is None and occ_in.get("isolated_reentry_minutes") is not None:
        flat["isolated_reentry_minutes"] = occ_in.get("isolated_reentry_minutes")
    if "already_placed_today" not in already and occ_in.get("already_placed_today") is not None:
        already["already_placed_today"] = occ_in.get("already_placed_today")
    if already.get("live_open_ticket") is None and occ_in.get("live_open_ticket") is not None:
        already["live_open_ticket"] = occ_in.get("live_open_ticket")
    if occ_in.get("already_placed_today") is False:
        already["already_placed_today"] = False
    tickets = st.get("never_flatten_tickets")
    return {
        "keep_one": keep,
        "flat_clock": flat,
        "already_placed": already,
        "hold": False,
        "hold_dead": flat.get("hold_dead") if "hold_dead" in flat else occ_in.get("hold_dead"),
        "symbol_open": keep.get("occupied") if "occupied" in keep else occ_in.get("symbol_open"),
        "already_placed_today": already.get("already_placed_today"),
        "minutes_since_flat": flat.get("minutes_since_flat"),
        "action": occ_in.get("action"),
        "two_stop_count": occ_in.get("two_stop_count"),
        "two_stop_is_integer": True,
        "live_open_ticket": already.get("live_open_ticket"),
        "isolated_reentry_minutes": flat.get("isolated_reentry_minutes"),
        "never_flatten_tickets": list(tickets) if tickets else None,
    }


def _noul(qid: str, instructions: str, true_c: str, false_c: str) -> dict[str, Any]:
    del qid
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": true_c, "false": false_c},
    }


def _score(qid: str, instructions: str, criteria: list[str]) -> dict[str, Any]:
    del qid
    return {"type": "score", "instructions": instructions, "criteria": list(criteria)}


def _named(qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    del qid
    return {"type": "choice", "instructions": instructions, "criteria": dict(criteria)}


def _include_question(chunk: str) -> dict[str, Any]:
    return _score(
        f"include_{chunk}",
        (
            f"How much of the named `{chunk}` chunk does this fire's query need? "
            "hide / short / long / full. Query-aware — not a catalog dump."
        ),
        list(INCLUDE_DEPTH_CRITERIA),
    )


def _equity_to_pass_question() -> dict[str, Any]:
    """Hop-local money card. jev_client attach_account fills equity; never invent."""
    return _score(
        "equity_to_pass",
        (
            "Given this login's live equity, does THIS hop help that equity? "
            "A pass line does not limit this hop. "
            "The cash number is the returned score. Missing account stays empty."
        ),
        [
            "Cash outcome does not help this equity",
            "Ordinary versus this live equity",
            "Named cash outcome helps this equity",
        ],
    )


def completeness_noul_question(seat: str | None = None) -> dict[str, Any]:
    """One completeness Noul on THIS hop, not a generic leftover dump."""
    chunks = SEAT_CHUNKS.get(str(seat or ""), ())
    if chunks:
        named = ", ".join(chunks)
        hop = str(seat)
        instructions = (
            f"Do the named chunks for THIS {hop} hop ({named}) contain enough "
            "to judge THIS fire as-of clock.as_of_utc? One completeness Noul "
            "on this hop — not a leftover dump of every converted if, and not "
            "a Noul per tick."
        )
        true_c = f"Named {hop} chunks are present enough to judge this fire"
        false_c = f"A required named {hop} chunk is missing or unknown"
    else:
        instructions = (
            "Do the named leftover chunks for THIS hop contain enough to judge "
            "THIS fire as-of clock.as_of_utc? One completeness Noul on this "
            "object — not a Noul per tick or per converted if."
        )
        true_c = "Named leftover chunks are present enough to judge this fire"
        false_c = "A required named leftover chunk is missing or unknown"
    return _noul("remaining_state_sufficient", instructions, true_c, false_c)


def _companion_decision_questions() -> dict[str, Any]:
    return {
        "companion_pause_fit": _score(
            "companion_pause_fit",
            (
                "Given the named companion snapshot, is a pause still describing "
                "this fire, or has the snapshot gone stale versus the current "
                "tape? Integer occupancy keep-one stays. Do not invent a place."
            ),
            [
                "Named snapshot argues the fire is dead / paused",
                "Ordinary / mixed companion state",
                "Named snapshot still supports continuing the fire",
            ],
        ),
        "companion_cooldown_fit": _score(
            "companion_cooldown_fit",
            (
                "Is the named cooldown_for reason still the same setup, or has "
                "the window expired on this bar? Integer cooldown clock stays. "
                "Log range only."
            ),
            [
                "Named cooldown still binds this fire",
                "Ordinary / mixed cooldown",
                "Named cooldown is spent; setup is new",
            ],
        ),
        "companion_zero_risk_fit": _score(
            "companion_zero_risk_fit",
            (
                "Does named companion state still describe a zero-risk block, "
                "or is residual risk now on the tape? Integer zero-risk still "
                "binds. Do not invent a place."
            ),
            [
                "Named companion still says zero residual risk",
                "Ordinary / mixed",
                "Named residual risk is now on the tape",
            ],
        ),
        "companion_action": _named(
            "companion_action",
            (
                "Given THIS companion snapshot, cooldown, and zero-risk on "
                "THIS fire, yield the send, persist the integer companion "
                "path, or abstain? Occupancy keep-one stays integer. Do not "
                "own the send."
            ),
            {
                "yield": (
                    "THIS companion snapshot still pauses THIS fire; do not send"
                ),
                "persist": (
                    "THIS companion snapshot no longer blocks THIS fire; "
                    "integer occupancy keep-one still binds"
                ),
                "abstain": "Companion snapshot is unassembled; do not steer",
            },
        ),
        "equity_to_pass": _equity_to_pass_question(),
    }


def _weekend_decision_questions() -> dict[str, Any]:
    return {
        "weekend_carry": _score(
            "weekend_carry",
            (
                "Given broker clock and sleeve, is weekend carry a range on "
                "this bar, or is the integer embargo the whole trade? Friday "
                "weekend-flat close stays a clock fact. Do not invent a gap "
                "distribution."
            ),
            [
                "Named clock argues embargo / dead weekend carry",
                "Ordinary weekday; weekend policy idle",
                "Named sleeve still looks legal into the weekend",
            ],
        ),
        "weekend_entry": _named(
            "weekend_entry",
            (
                "Name embargo, allow, or abstain for THIS sleeve on THIS "
                "broker clock given weekend_carry. Friday close still flattens "
                "24/5 books. This hop does not own flatten."
            ),
            {
                "embargo": (
                    "THIS sleeve into THIS weekend clock is the whole trade; "
                    "do not enter"
                ),
                "allow": "THIS sleeve still looks legal on THIS broker clock",
                "abstain": "Clock or sleeve weekend policy is unassembled",
            },
        ),
        "equity_to_pass": _equity_to_pass_question(),
    }


def _occupancy_decision_questions() -> dict[str, Any]:
    return {
        "occupancy_after_close": _named(
            "occupancy_after_close",
            (
                "Given minutes since this symbol went flat, keep-one occupied, "
                "and the already-placed fact, name THIS occupancy after a close: "
                "reenter as a new named fire, keep_one while the symbol is still "
                "open, not_isolated while the flat is still short, first print "
                "with no prior close, or abstain. The minutes are the returned "
                "score for this decision. Occupancy HOLD is dead. "
                "2-stop COUNT stays an integer fact. Already-placed cannot lift."
            ),
            {
                "reenter": (
                    "Symbol has been flat long enough after a close that THIS is a new named fire"
                ),
                "keep_one": (
                    "Symbol still occupied; keep-one integer binds; do not send"
                ),
                "not_isolated": "Flat, but the gap is still short; do not name a new fire",
                "first": "No prior close on this symbol; not a re-entry",
                "abstain": "Occupancy unassembled; do not steer",
            },
        ),
        "equity_to_pass": _equity_to_pass_question(),
    }


def _overlay_decision_questions() -> dict[str, Any]:
    return {
        "vp_above_va": _noul(
            "vp_above_va",
            (
                "Is this VP print noise given named vp_loc (acceptance above "
                "value area), or a real acceptance? Integer drop-list stays "
                "until a named wire. Empty loc is not 'no VP'."
            ),
            "Named VP looks like noise versus value area",
            "Named VP still looks like acceptance, or loc is unassembled",
        ),
        "damage_consistency": _noul(
            "damage_consistency",
            (
                "Do named damage metrics still agree with a QUARANTINE drop "
                "or a RISK_REDUCE tilt? Integer QUARANTINE multiplier 0.0 "
                "still drops. This Noul is consistency, not a new surface."
            ),
            "Named damage still agrees with the integer action",
            "Named damage disagrees, or metrics are unassembled",
        ),
        "energy_still_hurtful": _noul(
            "energy_still_hurtful",
            (
                "After round-trip cost on HEATOIL_c / NATGAS_cash, is the "
                "named fill still +EV versus stop? Integer drop-list today. "
                "Do not invent a new energy surface."
            ),
            "Named energy cost still eats the stop",
            "Named energy still looks fillable after cost, or unassembled",
        ),
        "impulse_range": _score(
            "impulse_range",
            (
                "Given sub_xvol leader impulse (none / opposed / with), is "
                "the overlay veto a range on this bar? Overlay stays off "
                "until named. Do not invent headroom."
            ),
            [
                "Named impulse none/opposed; overlay veto still describes tape",
                "Ordinary / mixed impulse",
                "Named impulse with the fire; overlay veto looks stale",
            ],
        ),
        "overlay_session_hour": _score(
            "overlay_session_hour",
            (
                "Is H4 hour in {8,12,16} this sleeve's clean hour today, or "
                "is 1.15x just a clock? Size-up cap stays envelope. Score "
                "hour quality only."
            ),
            [
                "Named hour is dead for this sleeve",
                "Ordinary hour; overlay idle",
                "Named hour is this sleeve's clean window",
            ],
        ),
    }


def _size_bins_decision_questions() -> dict[str, Any]:
    return {
        "kelly_bin_vs_tape": _score(
            "kelly_bin_vs_tape",
            (
                "Does today's Kelly-lite bin (0.748 / 0.991 / 1.241 vs HALF) "
                "match named tape given n_active, or is the bin a dead "
                "number? Integer bins stay until a named wire. Running count "
                "monotone within the day is physics."
            ),
            [
                "Named bin fights the tape",
                "Ordinary / mixed",
                "Named bin still matches tape conviction",
            ],
        ),
        "stress_streak": _score(
            "stress_streak",
            (
                "Is the next book-day another loss given the named streak, "
                "or does today's tape argue the ladder is the wrong lever? "
                "Integer ladder until named. Do not invent headroom past "
                "the prop wall."
            ),
            [
                "Named streak still argues shrink",
                "Ordinary / mixed streak",
                "Named tape looks unlike the streak ladder",
            ],
        ),
        "coloss_continuation": _noul(
            "coloss_continuation",
            (
                "Is trailing-5d negative fraction still a cross-sleeve "
                "continuation at the fitted 0.57 trip? Integer trip stays. "
                "Do not move 0.57 from this pack."
            ),
            "Named co-loss still looks like continuation",
            "Named fraction disagrees, or path is unassembled",
        ),
        "voltilt_vr": _score(
            "voltilt_vr",
            (
                "Should size rise with named vol_ratio on sub_xvol, or is "
                "vr tilt an equity-path artifact? Integer --vol-level-tilt "
                "stays OFF. Missing answers = no extra PASS."
            ),
            [
                "Named vr tilt would fight risk-weighted efficiency",
                "Ordinary / mixed vr",
                "Named vr still orders size with vol_ratio",
            ],
        ),
        "na_doomed_honest": _score(
            "na_doomed_honest",
            (
                "Should running conviction na follow fired-and-placed "
                "sleeves, not doomed/unplaced emits? Integer na monotone is "
                "physics. Do not let doomed emits size the book."
            ),
            [
                "Named na is inflated by doomed/unplaced emits",
                "Ordinary / mixed count",
                "Named na follows fired-and-placed sleeves",
            ],
        ),
        "lane_inside_band": _score(
            "lane_inside_band",
            (
                "What weight inside the declared [0.50, 1.15] band matches "
                "E[R]/Var today? Band is envelope — outside is refuse. "
                "Inside is fluid. Do not jump size from this pack."
            ),
            [
                "Named posterior wants the low end of the band",
                "Ordinary / mid band",
                "Named posterior wants the ceiling of the band",
            ],
        ),
        "cluster_corr_order": _score(
            "cluster_corr_order",
            (
                "Are today's named cluster members still ~1 pairwise corr, "
                "and which unit deserves remaining headroom? Integer "
                "one-unit-day on W7 stays. Never invent a second unit."
            ),
            [
                "Named cluster is mixed; shed the weaker member",
                "Ordinary / unassembled cluster",
                "Named members still move as one unit",
            ],
        ),
    }


def _frontier_decision_questions() -> dict[str, Any]:
    return {
        "frontier_cell_fit": _score(
            "frontier_cell_fit",
            (
                "Given named stop/target geometry, does a 2R vs 5R vs 4R "
                "exit cell still match this sleeve's measured horizon, or "
                "is the cell a research contract the live book does not "
                "run? Arming is integer argv. This pack never arms "
                "frontier-exits."
            ),
            [
                "Named cell fights live contract / horizon",
                "Ordinary / mixed / unarmed",
                "Named cell still matches measured horizon",
            ],
        ),
    }


def _research_decision_questions() -> dict[str, Any]:
    return {
        "packet_quality": _score(
            "packet_quality",
            (
                "Given this research packet, how good is the candidate on "
                "named confluence / cost / lifecycle / geometry dimensions? "
                "The old cliffs are weights. "
                "Observe only. Never place. Never import the selector."
            ),
            [
                "Named packet looks weak on every axis",
                "Ordinary / mixed packet",
                "Named packet looks strong on confluence and geometry",
            ],
        ),
        "fillability": _noul(
            "fillability",
            (
                "Is the named fill atom provenance-complete (value + "
                "source_time + source_boundary) enough to judge fillability? "
                "Missing provenance fails closed. Do not mix an entry-quality "
                "heuristic into the execution-fill slot. Observe only."
            ),
            "Named fill atom is provenance-complete and fillable",
            "Provenance missing, or fill atom is unassembled",
        ),
        "wait_vs_trade": _named(
            "wait_vs_trade",
            (
                "Is the best named candidate better than doing nothing "
                "given the packets on this state? Wait is "
                "first-class. Observe only. Never place."
            ),
            {
                "wait": "Doing nothing still beats the named candidate",
                "trade": "Named candidate beats the wait competitor",
                "abstain": "State is thin; do not steer the allocator",
            },
        ),
        "whiteboard_session": _score(
            "whiteboard_session",
            (
                "Does named whiteboard quality still describe this "
                "symbol/session as untradeable on the broad path? Integer "
                "hard actions stay. Observe only — book send may never "
                "hit this path."
            ),
            [
                "Named whiteboard still says untradeable",
                "Ordinary / mixed / path idle",
                "Named whiteboard no longer blocks this session",
            ],
        ),
    }


_DECISION_BUILDERS = {
    "companion": _companion_decision_questions,
    "occupancy": _occupancy_decision_questions,
    "weekend": _weekend_decision_questions,
    "overlay": _overlay_decision_questions,
    "size_bins": _size_bins_decision_questions,
    "frontier": _frontier_decision_questions,
    "research": _research_decision_questions,
}


_BANNED_TEXT: tuple[str, ...] = ()


def _limit_key(name: Any) -> bool:
    del name
    return False


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    for token in _BANNED_TEXT:
        probe = token.replace(",", "").replace("_", "").lower()
        if probe in compact:
            return True
    return False


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _limit_key(key):
                continue
            out[str(key)] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub(item) for item in value)
    if isinstance(value, str) and _banned_text(value):
        return ""
    return value


def _question_ok(spec: Mapping[str, Any]) -> bool:
    kind = str(spec.get("type") or "")
    if kind not in {"noul", "choice", "score"}:
        return False
    try:
        blob = json.dumps(spec)
    except (TypeError, ValueError):
        return False
    if _banned_text(blob):
        return False
    low = blob.lower()
    return "floor" not in low and "baseline" not in low


def _kept_questions(questions: Mapping[str, Any]) -> dict[str, Any]:
    kept: dict[str, Any] = {}
    for key, spec in questions.items():
        if _limit_key(key) or not isinstance(spec, Mapping):
            continue
        if not _question_ok(spec):
            continue
        kept[str(key)] = dict(spec)
    return kept


_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)


def _sidecar(qid: str) -> bool:
    return qid.endswith("_parameter") or qid.endswith("_threshold")


def _parameter_block(qid: str) -> dict[str, Any]:
    return _score(
        f"{qid}_parameter",
        (
            "The score you return is the parameter for this decision. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "Do not flatten. Do not send an order."
        ),
        list(_BETWEEN),
    )


def _threshold_block(qid: str) -> dict[str, Any]:
    return _score(
        f"{qid}_threshold",
        (
            "The score you return is the threshold for this decision. "
            "It may sit between the levels. "
            "An empty score leaves the threshold unset. "
            "Do not flatten. Do not send an order."
        ),
        list(_BETWEEN),
    )


def _pair_parameters(questions: Mapping[str, Any]) -> dict[str, Any]:
    """Each decision carries its parameter. A Choice also carries a threshold."""

    out = dict(questions)
    for qid, block in list(questions.items()):
        if _sidecar(str(qid)) or not isinstance(block, Mapping):
            continue
        kind = str(block.get("type") or "")
        if kind not in {"noul", "choice", "score"}:
            continue
        out[f"{qid}_parameter"] = _parameter_block(str(qid))
        if kind == "choice":
            out[f"{qid}_threshold"] = _threshold_block(str(qid))
    return _kept_questions(out)


def _with_returns(questions: Mapping[str, Any], seats: tuple[str, ...]) -> dict[str, Any]:
    """Pair parameters, ask which seat exists, and ask the loop bound.

    The bound is a Score on this pack. It does not remove a seat.
    """

    out = _pair_parameters(questions)
    for seat in seats:
        if _limit_key(seat):
            continue
        qid = f"component_{seat}"
        out[qid] = _noul(
            qid,
            (
                f"Does the `{seat}` component exist on this state? "
                "Only an actual bool says whether it exists. "
                "An empty answer leaves existence unset. "
                "Do not flatten. Do not send an order."
            ),
            "This component exists on this state",
            "This component does not exist on this state",
        )
        out[f"{qid}_parameter"] = _parameter_block(qid)
    out["remaining_ifs_loop_bound"] = _score(
        "remaining_ifs_loop_bound",
        (
            "How many of these decisions are in this fire? "
            "The score you return is that bound. It may sit between the levels. "
            "An empty score leaves the bound unset. "
            "The bound does not remove a seat. "
            "Do not flatten. Do not send an order."
        ),
        [
            "no further decision on this fire",
            "the decisions named on this state",
            "the decisions still open on this fire",
        ],
    )
    return _kept_questions(out)


def _number(value: Any) -> float | None:
    """A returned number. Booleans, blanks, and non-finite values stay empty."""

    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _number(value)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique_local(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability already on the return. A tie is unset."""

    if not numeric:
        return None
    names = order or tuple(numeric)
    best: str | None = None
    best_p: float | None = None
    tied = False
    for name in names:
        if name not in numeric:
            continue
        p = numeric[name]
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if tied or best is None:
        return None
    return best


def _choice_value(block: Any, order: tuple[str, ...]) -> str | None:
    """The choice is the unique highest probability. A label alone is unset."""

    if not isinstance(block, Mapping) or not order:
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "choice":
        return None
    allowed = set(order)
    numeric = {key: value for key, value in _probabilities(block).items() if key in allowed}
    local = _unique_local(numeric, order)
    try:
        from .jev_questions import unique_highest
    except Exception:
        return local if local in allowed else None
    try:
        picked = unique_highest(numeric, order)
    except Exception:
        return None
    if picked is None or str(picked) not in allowed:
        return None
    return str(picked)


def _score_local(raw: Mapping[str, Any]) -> float | None:
    """Read the returned score. Do not snap it to a level index."""

    if raw.get("error"):
        return None
    if "score" in raw and raw.get("score") is not None:
        return _number(raw.get("score"))
    noul = raw.get("noul")
    if noul is not None and not isinstance(noul, bool):
        return _number(noul)
    numeric = _probabilities(raw)
    if not numeric:
        return None
    winner = _unique_local(numeric, tuple(numeric))
    if winner is None:
        return None
    return numeric[winner]


def _score_value(raw: Any) -> float | None:
    """The parameter is the returned score. A tie leaves it unset."""

    if not isinstance(raw, Mapping):
        return _number(raw)
    kind = raw.get("type")
    if kind is not None and str(kind).strip().lower() != "score":
        return None
    try:
        from .jev_questions import returned_number
    except Exception:
        return _score_local(raw)
    try:
        return _number(returned_number(raw))
    except Exception:
        return None


def _noul_value(raw: Any) -> bool | float | None:
    """A Noul stays a bool or a probability. Missing stays missing."""

    if raw is True or raw is False:
        return raw
    if not isinstance(raw, Mapping):
        return _number(raw)
    kind = raw.get("type")
    if kind is not None and str(kind).strip().lower() != "noul":
        return None
    if "noul" in raw:
        value = raw.get("noul")
    elif "Noul" in raw:
        value = raw.get("Noul")
    else:
        return None
    if value is True or value is False:
        return value
    return _number(value)


def _read_row(
    qid: str,
    block: Mapping[str, Any],
    answers: Mapping[str, Any],
) -> dict[str, Any]:
    kind = str(block.get("type") or "")
    raw = answers.get(qid)
    threshold = None
    if kind == "choice":
        criteria = block.get("criteria") if isinstance(block.get("criteria"), Mapping) else {}
        value: Any = _choice_value(raw, tuple(str(key) for key in criteria))
        threshold = _score_value(answers.get(f"{qid}_threshold"))
        parameter = _score_value(answers.get(f"{qid}_parameter"))
    elif kind == "noul":
        value = _noul_value(raw)
        parameter = _score_value(answers.get(f"{qid}_parameter"))
    elif kind == "score":
        value = _score_value(raw)
        parameter = _score_value(answers.get(f"{qid}_parameter"))
    else:
        value = None
        parameter = None
    return {"value": value, "parameter": parameter, "threshold": threshold}


def _plain_value(qid: str, block: Mapping[str, Any], answers: Mapping[str, Any]) -> Any:
    raw = answers.get(qid)
    kind = str(block.get("type") or "")
    if kind == "choice":
        criteria = block.get("criteria") if isinstance(block.get("criteria"), Mapping) else {}
        return _choice_value(raw, tuple(str(key) for key in criteria))
    if kind == "noul":
        return _noul_value(raw)
    if kind == "score":
        return _score_value(raw)
    return None


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes
    except Exception:
        state["prior_outcomes"] = []
        return
    try:
        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(state: Mapping[str, Any], decisions: Mapping[str, Any], error: str | None) -> None:
    """The return is the next ask's history. A miss is stored as a miss."""

    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    for key, value in decisions.items():
        try:
            append_outcome(
                str(key),
                value,
                state,
                error=None if value is not None else error,
            )
        except Exception:
            return


def _miss(error: str | None, answers: Mapping[str, Any], key: str) -> bool:
    return bool(error) and key not in answers


def include_depth_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "observe",
) -> dict[str, Any]:
    """Score include-depth for the chunks *this* fire uses. Not a catalog dump."""
    del state
    qs: dict[str, Any] = {}
    for seat in seats_for_branch(branch, seats):
        for chunk in SEAT_CHUNKS.get(seat, ()):
            if _limit_key(chunk):
                continue
            qs[f"include_{chunk}"] = _include_question(chunk)
    return _pair_parameters(_kept_questions(qs))


def decision_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "observe",
    standalone: bool = True,
) -> dict[str, Any]:
    """Decision pack for this subtree. Completeness is one Noul on THIS hop."""
    del state
    named = seats_for_branch(branch, seats)
    qs: dict[str, Any] = {}
    if standalone:
        hop = named[0] if len(named) == 1 else None
        qs["remaining_state_sufficient"] = completeness_noul_question(hop)
    for seat in named:
        qs.update(_DECISION_BUILDERS[seat]())
    return _with_returns(_kept_questions(qs), named)


def seat_subtree_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "observe",
    standalone: bool = True,
) -> dict[str, Any]:
    """One subtree: include-depth Scores + decision pack."""
    qs = include_depth_questions(state, seats=seats, branch=branch)
    qs.update(decision_questions(state, seats=seats, branch=branch, standalone=standalone))
    return _kept_questions(qs)


def intent_packs(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "observe",
    standalone: bool = True,
) -> dict[str, dict[str, Any]]:
    """Two TypeSafe reads from one intent (include-depth, then decision)."""
    return {
        "include_depth": include_depth_questions(state, seats=seats, branch=branch),
        "decision": decision_questions(
            state, seats=seats, branch=branch, standalone=standalone
        ),
    }


def ignore_if(question_id: str, state: Mapping[str, Any] | None) -> bool | None:
    """No local skip.

    The questions stay on the ask. Empty, thin, or unassembled state does
    not vote and does not restore a skip.
    """
    del question_id, state
    return None


def occupancy_pack_ids(state: Mapping[str, Any] | None = None) -> tuple[str, ...]:
    """~6 IDs. Not the gold catalog ``isolated_reentry_is_new``."""
    packs = intent_packs(state, seats=("occupancy",), branch="observe", standalone=True)
    return tuple(packs["include_depth"]) + tuple(packs["decision"])


def noul_question_ids(questions: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(k for k, v in questions.items() if isinstance(v, dict) and v.get("type") == "noul")


def instruction_bodies(questions: Mapping[str, Any] | None = None) -> list[str]:
    """Instruction + criteria text only (not JSON type keys)."""
    qs = questions if questions is not None else seat_subtree_questions({}, standalone=True)
    bodies: list[str] = []
    for payload in qs.values():
        if not isinstance(payload, dict):
            continue
        ins = payload.get("instructions")
        if isinstance(ins, str):
            bodies.append(ins)
        criteria = payload.get("criteria")
        if isinstance(criteria, list):
            bodies.extend(str(item) for item in criteria)
        elif isinstance(criteria, dict):
            bodies.extend(str(v) for v in criteria.values())
    return bodies


def body_mentions_forbidden(questions: Mapping[str, Any] | None = None) -> list[str]:
    hits: list[str] = []
    for text in instruction_bodies(questions):
        lowered = text.lower()
        for token in FORBIDDEN_INSTRUCTION_TOKENS:
            if token in lowered:
                hits.append(token)
    return hits


def pack_payload(
    state: Mapping[str, Any],
    *,
    seats: Iterable[str] | None = None,
    branch: str = "observe",
    standalone: bool = True,
    model: str = MODEL,
) -> dict[str, Any]:
    """Pack-only payload. Uses ``questions=`` this subtree.

    Does not POST. Later merge sets ``standalone=False`` and folds into
    the one gold POST. Remaining packs pass ``merge_sleeve=False``.
    """
    scrubbed = _scrub(dict(state or {}))
    if not isinstance(scrubbed, dict):
        scrubbed = {}
    qs = seat_subtree_questions(
        scrubbed, seats=seats, branch=branch, standalone=standalone
    )
    seat = seats_for_branch(branch, seats)[0]
    labels = hierarchical_labels(scrubbed, seat=seat, branch=branch)
    return {
        "state": scrubbed,
        "model": model,
        "ask_together": True,
        "questions": qs,
        "labels": labels,
        "merge_sleeve": False,
        "never_noul_every_tick": True,
    }


def highest_probability_choice(block: Any) -> str | None:
    """The choice is the unique highest probability. A tie or a bare label is unset."""
    if not isinstance(block, Mapping):
        return None
    probs = block.get("probabilities")
    if isinstance(probs, Mapping) and probs:
        order = tuple(str(key) for key in probs)
    else:
        order = ()
    return _choice_value(block, order)


def choice_alternative(block: Any) -> dict[str, Any]:
    """Named alternative plus the probability map that selected it."""
    probs: dict[str, float] = {}
    confidence = None
    if isinstance(block, Mapping):
        raw = block.get("probabilities")
        if isinstance(raw, Mapping):
            for key, value in raw.items():
                try:
                    probs[str(key)] = float(value)
                except (TypeError, ValueError):
                    continue
        if block.get("confidence") is not None:
            try:
                confidence = float(block["confidence"])
            except (TypeError, ValueError):
                confidence = None
    return {
        "choice": highest_probability_choice(block),
        "probabilities": probs,
        "confidence": confidence,
    }


def _chair_wake_paths() -> tuple[Path, ...]:
    repo = Path(__file__).resolve().parents[2]
    state = repo / "pipeline_state" / "ultimate_book" / "operator" / "judgment" / "state"
    host = Path(r"host-local\redacted_host\repo") / "pipeline_state" / "ultimate_book" / "operator" / "judgment" / "state"
    return (
        state / "chair_wake.json",
        host / "chair_wake.json",
        state / "equity_wire_post.json",
        host / "equity_wire_post.json",
    )


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def measured_account_card(state: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Measured Challenge card. Never invent equity. chair_wake wins over a string login."""
    st = dict(state or {})
    existing = st.get("account") if isinstance(st.get("account"), Mapping) else None
    if (
        isinstance(existing, Mapping)
        and existing.get("present") is True
        and _float_or_none(existing.get("equity")) is not None
    ):
        card = dict(existing)
        card["invented"] = False
        return {str(key): item for key, item in card.items() if not _limit_key(key)}
    raw: dict[str, Any] | None = None
    for path in _chair_wake_paths():
        try:
            if not path.is_file():
                continue
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(loaded, dict) and _float_or_none(loaded.get("equity")) is not None:
            raw = loaded
            break
    if raw is None:
        return None
    equity = float(raw["equity"])
    balance = _float_or_none(raw.get("balance"))
    open_pnl = _float_or_none(raw.get("open_pnl") if raw.get("open_pnl") is not None else raw.get("profit"))
    to_pass = _float_or_none(raw.get("to_pass"))
    return {
        "schema": "gtos.judgment.equity_frame.v1",
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "present": True,
        "source": "chair_wake",
        "reason": None,
        "equity": equity,
        "balance": balance,
        "open_pnl": open_pnl,
        "to_pass": to_pass,
        "day_equity": equity,
        "pass_line": None,
        "cash_unit_usd": None,
        "never_enlarge_because_to_pass": False,
        "invented": False,
    }


def _prepare_hop_state(state: Mapping[str, Any] | None) -> dict[str, Any]:
    st = dict(state or {})
    identity = dict(st.get("identity") or {})
    identity.setdefault("login", CHALLENGE_LOGIN)
    identity.setdefault("ns", CHALLENGE_NS)
    st["identity"] = identity
    card = measured_account_card(st)
    if card is not None:
        st["account"] = card
    elif not isinstance(st.get("account"), Mapping):
        st.pop("account", None)
    news = dict(st.get("news") or {})
    events = list(news.get("events") or [])
    news["mill_url"] = None
    news["invented"] = False
    news.setdefault("NEWS_PROTOCOL_APPLIED", False)
    if events:
        news["spine_empty"] = False
        news["events"] = events
    else:
        news.setdefault("spine_empty", True)
        news.setdefault("events", [])
    st["news"] = news
    return st


def post_questions(
    state: Mapping[str, Any] | None,
    questions: Mapping[str, Any],
    *,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """One POST through ``jev_client.evaluate`` for these questions.

    Prior outcomes are attached on that ask. The return is stored for the
    next ask. An empty answer, a tie, or an error leaves that field unset.
    This does not read a key and does not send.
    """

    payload = _scrub(_prepare_hop_state(state))
    if not isinstance(payload, dict):
        payload = {}
    pack = _pair_parameters(dict(questions or {}))
    _attach_priors(payload, pack)
    error: str | None = None
    receipt: Any = {}
    call = None
    try:
        from .jev_client import evaluate as call
    except Exception as exc:
        error = type(exc).__name__
        call = None
    if call is not None:
        try:
            receipt = call(
                payload,
                questions=pack,
                timeout_s=timeout_s,
                merge_sleeve=False,
                model=MODEL,
            )
        except Exception as exc:
            error = type(exc).__name__
            receipt = {}
    if not isinstance(receipt, dict):
        error = error or "evaluate_not_a_dict"
        receipt = {}
    raw_answers = receipt.get("answers")
    answers = raw_answers if isinstance(raw_answers, dict) else {}
    if error is None and receipt.get("ok") is not True:
        skipped = receipt.get("error") or receipt.get("skipped") or "empty"
        error = str(skipped)
    history: dict[str, Any] = {}
    for qid, block in pack.items():
        if not isinstance(block, Mapping):
            continue
        if _miss(None if answers else error, answers, qid):
            history[qid] = None
        else:
            history[qid] = _plain_value(qid, block, answers)
    _remember(payload, history, None if answers else error)
    out = dict(receipt)
    out.pop("key_source", None)
    out.pop("key_fingerprint", None)
    out["ok"] = bool(receipt.get("ok") is True and bool(answers))
    out["answers"] = answers
    out["model"] = receipt.get("model") or MODEL
    out["posted"] = bool(receipt.get("ok") is True)
    out["missing_jev"] = False
    if not answers:
        out["error"] = error
        out["skipped"] = receipt.get("skipped") if receipt.get("skipped") is not None else error
    return out


def _evaluate_decisions(
    state: Mapping[str, Any] | None,
    *,
    seats: Iterable[str] | None,
    branch: str,
    standalone: bool,
    ask: Callable[..., Any] | None,
) -> dict[str, Any]:
    questions = seat_subtree_questions(
        state, seats=seats, branch=branch, standalone=standalone
    )
    payload = _scrub(_prepare_hop_state(state))
    if not isinstance(payload, dict):
        payload = {}
    payload["model"] = MODEL
    seat = next(iter(seats_for_branch(branch, seats)), "companion")
    payload["labels"] = hierarchical_labels(payload, seat=seat, branch=branch)
    _attach_priors(payload, questions)
    call = ask
    error: str | None = None
    receipt: Any = {}
    if call is None:
        try:
            from .jev_client import evaluate as call
        except Exception as exc:
            error = type(exc).__name__
            call = None
    if call is not None:
        try:
            receipt = call(payload, questions=questions, merge_sleeve=False, model=MODEL)
        except Exception as exc:
            error = type(exc).__name__
            receipt = {}
    if not isinstance(receipt, dict):
        if error is None:
            error = "evaluate_not_a_dict"
        receipt = {}
    raw_answers = receipt.get("answers")
    answers = raw_answers if isinstance(raw_answers, dict) else {}
    if not answers and error is None:
        error = str(receipt.get("error") or receipt.get("skipped") or "empty")
    elif answers and error is None and receipt.get("ok") is False:
        error = str(receipt.get("error") or receipt.get("skipped") or "post_failed")
    named = seats_for_branch(branch, seats)
    decisions: dict[str, Any] = {}
    history: dict[str, Any] = {}
    for qid, block in questions.items():
        if _sidecar(qid) or qid == "remaining_ifs_loop_bound" or qid.startswith("component_"):
            continue
        if not isinstance(block, Mapping):
            continue
        if _miss(error, answers, qid):
            row = {"value": None, "parameter": None, "threshold": None}
        else:
            row = _read_row(qid, block, answers)
        decisions[qid] = row
        history[qid] = row.get("value")
        history[f"{qid}_parameter"] = row.get("parameter")
        if f"{qid}_threshold" in questions:
            history[f"{qid}_threshold"] = row.get("threshold")
    components: dict[str, Any] = {}
    for seat_name in named:
        qid = f"component_{seat_name}"
        if _miss(error, answers, qid):
            present = None
        else:
            present = _noul_value(answers.get(qid))
        param_id = f"{qid}_parameter"
        if _miss(error, answers, param_id):
            parameter = None
        else:
            parameter = _score_value(answers.get(param_id))
        components[seat_name] = {"exists": present, "parameter": parameter}
        history[qid] = present
        history[param_id] = parameter
    bound_id = "remaining_ifs_loop_bound"
    if _miss(error, answers, bound_id):
        loop_bound = None
    else:
        loop_bound = _score_value(answers.get(bound_id))
    history[bound_id] = loop_bound
    _remember(payload, history, error if error else None)
    return {
        "model": MODEL,
        "branch": branch,
        "decisions": decisions,
        "components": components,
        "loop_bound": loop_bound,
        "error": error if error else None,
    }


def evaluate_decisions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "observe",
    standalone: bool = True,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One System One ask for this state.

    Each choice, noul, threshold, and parameter is that return. Seat
    existence is the component Noul. The loop bound is the Score for how
    many decisions are in this fire, and it does not remove a seat. An
    empty answer, a tie, or an error leaves that return unset. This does
    not send and does not flatten.
    """

    try:
        return _evaluate_decisions(
            state,
            seats=seats,
            branch=branch,
            standalone=standalone,
            ask=ask,
        )
    except Exception as exc:
        return {
            "model": MODEL,
            "branch": str(branch or ""),
            "decisions": {},
            "components": {},
            "loop_bound": None,
            "error": type(exc).__name__,
        }
