"""Leftover execution / governor / cluster / news / F5 fire-path as a tree.

Seats PRs 69/68/67/70 and the remaining-seats worker do not own: place /
modify / close judgments in ``execution.py``, governor derisk, cluster
corr (not already_placed), news T−15/T+60 cycle, F5 fire-path fitness.

Founder brief (Diogo / Appendix 3): nested labels + log(n) tree search,
Score include-depth (hide / short / long / full). Not linear binary
keep/drop. One completeness Noul on *this* object — not a Noul per tick
because Jev is cheap. Do not compact a Challenge session as forever-state.

Code owns workflow (halt, token digest, 2-stop COUNT, named surface, prop
wall, occupancy keep-one, never-widen, $150, HIGH window constants, dead
21–00Z / Friday 16Z clock, min-stop ticks, 8pip refuse). TypeSafe owns
the semantic call that used to be a send/modify/cancel/derisk *judgment*.

This module does **not** edit ``jev_questions.py``. Subtree questions
live here. After PRs 69/68/67 land, merge ``standalone=False`` into the
one System One POST. Do not add a second LLM hop on the same gold_state.

Pin model ``jev-1.13.0``. Challenge book ``0`` / ``operator``.

Every decision this module returns, including every parameter, is the
System One value for that state. ``evaluate_decisions`` asks once through
``jev_client.evaluate`` (model ``jev-1.13.0``, ``merge_sleeve=False``,
POST https://api.typesafe.ai/v1/systemone). The return is only a Noul, a
Choice, or a Score. Prior outcomes are attached on that ask. An empty
answer, a tie, or an error leaves that return unset. A floor and a
baseline are not a question. This module does not send and does not flatten.
"""

from __future__ import annotations

import json
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

SEATS = ("exec", "governor", "cluster", "news", "f5_fire")
BRANCHES = ("place", "modify", "close", "observe", "derisk", "cycle")

# Query-aware chunks. Only the seat's used chunks enter the question set.
SEAT_CHUNKS: dict[str, tuple[str, ...]] = {
    "exec": ("tick", "geometry", "pending", "harvest", "close_receipt"),
    "governor": ("equity", "dd_wall", "derisk", "stress"),
    "cluster": ("occupancy", "corr", "peers"),
    "news": ("spine", "high_window", "cycle"),
    "f5_fire": ("clock", "limit", "freeze", "thin", "stop_floor"),
}

# Branch overlay: place dumps exec+f5_fire; cycle dumps news; etc.
BRANCH_SEATS: dict[str, tuple[str, ...]] = {
    "place": ("exec", "f5_fire"),
    "modify": ("exec",),
    "close": ("exec",),
    "observe": ("exec", "cluster"),
    "derisk": ("governor",),
    "cycle": ("news",),
}

INTEGER_FACTS: tuple[str, ...] = (
    "token_digest_match",
    "two_stop_count",
    "named_surface",
    "prop_wall",
    "halt",
    "operator_flatten_flag",
    "occupancy_keep_one",
    "never_widen",
    "tuition_150",
    "high_window_t15_t60_constants",
    "dead_21_00z_clock",
    "friday_16z_clock",
    "min_stop_ticks",
    "fx_dsp_8pip",
    "governor_walls",
    "software_tp1_forbidden",
)

# Leftover IDs this unique PR converts. Do not claim PR67 BE/trail/scale/
# flatten, PR68 admit, PR69 gate, PR70 sleeve cliffs, remaining-seats
# already_placed / remint / restart / ac60 emit.
CONVERTED_IFS: tuple[dict[str, str], ...] = (
    {
        "id": "EXEC-SL-FRESH",
        "was": "if fresh entry crossed decision SL: abort, no chase",
        "now": "integer refuse wrong-side; Score sl_fresh_fitness for chase-vs-wait",
        "seat": "exec",
        "branch": "place",
    },
    {
        "id": "EXEC-PRETRADE-MGR",
        "was": "execution_manager_v4.should_block → abort send",
        "now": "integer fatal reasons stay; Score pretrade_mgr_quality overlays",
        "seat": "exec",
        "branch": "place",
    },
    {
        "id": "EXEC-F5-NATIVE",
        "was": "native broker LIMIT vs internal poll then MARKET",
        "now": "Choice native_limit_vs_market; integer occupancy / would-cross stay",
        "seat": "exec",
        "branch": "place",
    },
    {
        "id": "EXEC-PENDING-TTL",
        "was": "restore 24h / previous UTC-day KZ / 48h expire ifs",
        "now": "integer TTL; Score pending_still_same_setup",
        "seat": "exec",
        "branch": "modify",
    },
    {
        "id": "EXEC-HARVEST",
        "was": "software harvest / momentum pullback / abort-streak overlays",
        "now": "Score harvest_observe; default leave-orig; Jev does not flatten",
        "seat": "exec",
        "branch": "observe",
    },
    {
        "id": "EXEC-J46TP",
        "was": "J46/J49 overwrite broker TP to 6R",
        "now": "Score j46_tp_fit overlay; do not revive 6R as live law",
        "seat": "exec",
        "branch": "place",
    },
    {
        "id": "EXEC-CLOSENONE",
        "was": "close-send-None backoff / skip as a mute if",
        "now": "Choice close_none_label; integer backoff stays",
        "seat": "exec",
        "branch": "close",
    },
    {
        "id": "EXEC-SL-NEVERWIDEN",
        "was": "modify SL never widens (integer)",
        "now": "integer never-widen stays; Score never_widen_pressure log only",
        "seat": "exec",
        "branch": "modify",
    },
    {
        "id": "F5-MS-FILLDEV",
        "was": "0.5R fill-deviation close",
        "now": "Score fill_deviation_observe; Jev must not own the close",
        "seat": "exec",
        "branch": "close",
    },
    {
        "id": "UB-ADM-004",
        "was": "soft daily −3% / max-DD as a mute wall",
        "now": "integer walls still block; Score wall_pressure log only",
        "seat": "governor",
        "branch": "derisk",
    },
    {
        "id": "UB-ADM-DERISK",
        "was": "band vs smooth cap_mult ifs",
        "now": "integer cap_mult computes; Score derisk_tilt overlay; missing → unchanged",
        "seat": "governor",
        "branch": "derisk",
    },
    {
        "id": "F5-MS-GOVREADY",
        "was": "governor ready fail-closed if unreadable",
        "now": "integer fail-closed; Noul governor_ready consistency",
        "seat": "governor",
        "branch": "derisk",
    },
    {
        "id": "UB-ADM-STRESS",
        "was": "stress_derisk ladder / coloss breaker ifs",
        "now": "Noul stress_continue + coloss_same_bet; integers still size",
        "seat": "governor",
        "branch": "derisk",
    },
    {
        "id": "F5-BO-OCCUPANCY-CORR",
        "was": "occupancy HOLD as intelligence",
        "now": "Noul cluster_same_dir; Choice action_scope; never occupancy HOLD",
        "seat": "cluster",
        "branch": "observe",
    },
    {
        "id": "F5-MS-OPPLOCK",
        "was": "same-symbol opposite lock if",
        "now": "Score opposite_lock; keep-one integer stays",
        "seat": "cluster",
        "branch": "observe",
    },
    {
        "id": "F5-MS-EURGBPSTACK",
        "was": "same-currency DSP stack if",
        "now": "Score eurgbp_stack + Noul speak_hold",
        "seat": "cluster",
        "branch": "observe",
    },
    {
        "id": "NEWS-F5",
        "was": "HIGH in T−15..T+60 as a mute cancel if",
        "now": "Noul event_proximity on the named spine; missing feed is context",
        "seat": "news",
        "branch": "cycle",
    },
    {
        "id": "F5-MS-NEWSCYCLE",
        "was": "host cancel T−15 / reeval T+60 ifs",
        "now": "Choice news_cycle; unique highest probability; missing feed is context",
        "seat": "news",
        "branch": "cycle",
    },
    {
        "id": "F5-JEV-008",
        "was": "dead 21–00Z / Friday 16Z as a judgment if",
        "now": "clock facts stay in state; Score fire_window fitness only",
        "seat": "f5_fire",
        "branch": "place",
    },
    {
        "id": "F5-MS-LIMITEXP",
        "was": "resting limit ≤4 closed M15 expire if",
        "now": "integer 4-bar COUNT; Score limit_expiry whether still same thesis",
        "seat": "f5_fire",
        "branch": "place",
    },
    {
        "id": "F5-MS-FROZEN",
        "was": "frozen intent reprice if",
        "now": "Score frozen_reprice; integer TTL stays",
        "seat": "f5_fire",
        "branch": "place",
    },
    {
        "id": "F5-MS-THINASIA",
        "was": "thin-hour crypto/Asia PDL routes limit if",
        "now": "Score thin_asia; Jev does not own the route",
        "seat": "f5_fire",
        "branch": "place",
    },
    {
        "id": "F5-MS-MINSTOP",
        "was": "min-stop lots/ticks refuse if",
        "now": "integer min-stop stays; Score minstop_fit log",
        "seat": "f5_fire",
        "branch": "place",
    },
    {
        "id": "F5-MS-8PIP",
        "was": "dsp cash-FX stop ≤8 pip → 0 lots",
        "now": "integer 8pip stays; Score pip8_fit log",
        "seat": "f5_fire",
        "branch": "place",
    },
)

_SNIPPETS: dict[str, str] = {
    "exec": "send-tick SL, native LIMIT vs MARKET, harvest observe, close-None label",
    "governor": "prop walls integer; wall_pressure / derisk_tilt Scores; governor_ready Noul",
    "cluster": "corr same-dir / action_scope — never occupancy HOLD as intelligence",
    "news": "news_cycle Choice; unique highest probability; missing feed is context",
    "f5_fire": "dead-window fitness, 4-bar expiry, frozen reprice, thin Asia, min-stop, 8pip",
}


def integer_facts() -> tuple[str, ...]:
    return INTEGER_FACTS


def converted_ifs() -> tuple[dict[str, str], ...]:
    return CONVERTED_IFS


def directional_snippet(seat: str) -> str:
    """Two-layer catalog: a short line so a model can *suggest* the seat exists."""
    return _SNIPPETS.get(str(seat or "").strip().lower(), "unnamed leftover seat")


def seats_for_branch(branch: str, seats: Iterable[str] | None = None) -> tuple[str, ...]:
    if seats:
        named = tuple(s for s in seats if s in SEATS)
        if named:
            return named
    mapped = BRANCH_SEATS.get(str(branch or "").strip().lower())
    if mapped:
        return mapped
    return SEATS


def hierarchical_labels(
    state: Mapping[str, Any] | None = None,
    *,
    seat: str = "exec",
    branch: str = "place",
) -> dict[str, Any]:
    """Nested labels so a later tree-search can find this object. Not a transcript."""
    identity = dict((state or {}).get("identity") or {})
    clock = dict((state or {}).get("clock") or {})
    sl = str(identity.get("sleeve") or "")
    sy = str(identity.get("symbol") or "")
    origin_s = str(identity.get("origin_organism") or "f5_challenge")
    node = str(seat or "exec")
    br = str(branch or "place")
    return {
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "origin": origin_s,
        "family_node": node,
        "sleeve": sl,
        "symbol": sy,
        "side": identity.get("side"),
        "as_of_utc": clock.get("as_of_utc"),
        "decision_day": identity.get("decision_day") or clock.get("decision_day"),
        "ticket": identity.get("ticket"),
        "branch": br,
        "subgoal": f"exec_gov_news:{node}:{br}:{sl or 'none'}",
    }


def _noul(_qid: str, instructions: str, true_line: str, false_line: str) -> dict[str, Any]:
    text = str(instructions).strip()
    if "leaves the answer unset" not in text:
        text = (
            f"{text} The noul you return is this answer. "
            "An empty noul leaves the answer unset."
        )
    return {
        "type": "noul",
        "instructions": text,
        "criteria": {"true": true_line, "false": false_line},
    }


def _score(_qid: str, instructions: str, criteria: list[str]) -> dict[str, Any]:
    text = str(instructions).strip()
    if "may sit between the levels" not in text:
        text = (
            f"{text} The score you return is the parameter for this state. "
            "It may sit between the levels. An empty score leaves the parameter unset."
        )
    return {"type": "score", "instructions": text, "criteria": list(criteria)}


def _choice(_qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    text = str(instructions).strip()
    if "unique highest probability" not in text:
        text = (
            f"{text} The choice is the unique highest probability. "
            "An empty answer or a tie leaves the choice unset."
        )
    return {"type": "choice", "instructions": text, "criteria": dict(criteria)}


def _include_question(chunk: str) -> dict[str, Any]:
    return _score(
        f"include_{chunk}",
        (
            f"How much of the named `{chunk}` chunk does this fire's query need? "
            "hide / short / long / full. Query-aware — not a catalog dump."
        ),
        list(INCLUDE_DEPTH_CRITERIA),
    )


def completeness_noul_question() -> dict[str, Any]:
    return _noul(
        "exec_state_sufficient",
        (
            "Do the named leftover chunks for this fire (tick/geometry/equity/"
            "news/clock as this seat uses them) contain enough to judge as-of "
            "clock.as_of_utc? One completeness Noul on this object — not a Noul "
            "per tick or per converted if. Empty news spine is not 'no HIGH'."
        ),
        "Named leftover chunks are present enough to judge this fire",
        "A required named leftover chunk is missing or unknown",
    )


def _exec_decision_questions(branch: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if branch in {"place", "observe"}:
        out["sl_fresh_fitness"] = _score(
            "sl_fresh_fitness",
            (
                "Did price already invalidate stop geometry between decision tick "
                "and send tick? 0 = geometry dead / chase; 1 = ordinary drift; "
                "2 = still the same setup. Integer still refuses a wrong-side SL. "
                "Do not re-anchor."
            ),
            [
                "Send-tick already crossed the decision SL — chase",
                "Ordinary drift; geometry still the same setup",
                "Fresh tick still agrees with the decision SL",
            ],
        )
        out["pretrade_mgr_quality"] = _score(
            "pretrade_mgr_quality",
            (
                "Does Execution Manager V4 still describe a runnable send given "
                "named pretrade cost, pending age, and geometry? Integer fatal "
                "reasons still abort. This Score does not invent a send."
            ),
            [
                "Named pretrade state argues the send is dead",
                "Ordinary / mixed pretrade",
                "Named pretrade still supports the send",
            ],
        )
        out["native_limit_vs_market"] = _choice(
            "native_limit_vs_market",
            (
                "Given would-cross, occupancy, and named cost, rest a broker "
                "LIMIT or take MARKET now? Integer occupancy keep-one stays. "
                "Do not own the rest — name the route."
            ),
            {
                "native_limit": "Rest a native broker LIMIT",
                "market": "Take MARKET now",
                "abstain": "State is thin; do not steer the route",
            },
        )
        out["j46_tp_fit"] = _score(
            "j46_tp_fit",
            (
                "Given named stop distance, is a 6R broker target the right "
                "barrier versus this sleeve's measured RR, or does a nearer/"
                "farther barrier raise E[R] after cost? Historical J46 overlay "
                "only. Do not revive 6R as live Challenge law. F5 software TP1 "
                "forbid stays integer."
            ),
            [
                "6R fights named tape / time-stop",
                "Ordinary / unassembled RR",
                "6R fits named sleeve RR",
            ],
        )
    if branch in {"modify", "observe"}:
        out["pending_still_same_setup"] = _score(
            "pending_still_same_setup",
            (
                "Is a restored/aged software limit still the same-session thesis "
                "given age, kill-zone, and 48h? Integer TTL still expires. "
                "Score whether it is still the same setup, not a restart chase."
            ),
            [
                "Stale / previous-session / restart chase",
                "Ordinary pending age",
                "Still the same-session thesis",
            ],
        )
        out["never_widen_pressure"] = _score(
            "never_widen_pressure",
            (
                "Would a named SL modify widen risk versus the broker SL? "
                "Integer never-widen still refuses. This Score is log / include "
                "depth, not a loosen."
            ),
            [
                "Named modify would widen",
                "Ordinary / no modify",
                "Named modify tightens or leaves orig",
            ],
        )
        out["harvest_observe"] = _score(
            "harvest_observe",
            (
                "LABEL / observe only. Does named MFE/MAE / abort-streak look "
                "like a harvest versus leave-orig? Do not flatten. Do not remint."
            ),
            [
                "Named giveback / abort argues observe-close",
                "Ordinary hold",
                "Clean runner — leave orig",
            ],
        )
    if branch in {"close", "observe"}:
        out["close_none_label"] = _choice(
            "close_none_label",
            (
                "LABEL only. Name a close-send-None. Integer backoff / skip "
                "stays. Do not invent a flatten."
            ),
            {
                "retry": "Named close-send-None looks transient — retry later",
                "skip": "Named close-send-None looks spent — skip this cycle",
                "unknown": "Unassembled / do not steer",
            },
        )
        out["fill_deviation_observe"] = _score(
            "fill_deviation_observe",
            (
                "Observe only. Does a named 0.5R born-wrong fill match tape, or "
                "is the cliff noise? This hop must not own the close. Writer "
                "flatten stays integer when armed."
            ),
            [
                "Named fill is born-wrong versus stop",
                "Ordinary / unassembled fill",
                "Fill still agrees with named geometry",
            ],
        )
    return out


def _governor_decision_questions() -> dict[str, Any]:
    return {
        "governor_ready": _noul(
            "governor_ready",
            (
                "Is the governor snapshot readable enough to size (N1/N2 "
                "integrity)? Consistency only. Integer still fail-closes when "
                "unreadable. Do not loosen a wall."
            ),
            "Governor snapshot is readable",
            "Governor snapshot is missing or contradictory",
        ),
        "wall_pressure": _score(
            "wall_pressure",
            (
                "How close is named equity to the prop daily / max-DD walls? "
                "Log only. Integers still block at −3% / −10% / entry buffer. "
                "This hop must not loosen a wall."
            ),
            [
                "At or through a named wall",
                "Ordinary headroom",
                "Far from named walls",
            ],
        ),
        "derisk_tilt": _score(
            "derisk_tilt",
            (
                "Does named drawdown argue a size overlay on top of the integer "
                "band/smooth cap_mult? A skip receipt leaves integer cap_mult "
                "unchanged. Cannot raise size past the integer cap."
            ),
            [
                "Named DD argues a haircut overlay",
                "Ordinary — leave integer cap_mult",
                "Named state supports full integer size",
            ],
        ),
        "stress_continue": _noul(
            "stress_continue",
            (
                "Given named prior-day stress facts, should the stress ladder "
                "keep shrinking new risk? Integer ladder still computes. This "
                "is a continue/ease overlay, not a refuse."
            ),
            "Named stress still argues continue-derisk",
            "Named stress is ordinary or missing",
        ),
        "coloss_same_bet": _noul(
            "coloss_same_bet",
            (
                "Is this fire the same-bet as a named coloss / cluster already "
                "on the book? Occupancy keep-one stays integer. This Noul is "
                "corr, not occupancy HOLD."
            ),
            "Named same-bet / coloss cluster",
            "Not the same bet, or unassembled",
        ),
    }


def _cluster_decision_questions() -> dict[str, Any]:
    return {
        "cluster_same_dir": _noul(
            "cluster_same_dir",
            (
                "Are named open units the same-direction same-cluster bet as "
                "this fire? Occupancy keep-one is SCRIPT, not this answer. "
                "Never draft occupancy HOLD as intelligence."
            ),
            "Named cluster is same-dir same-bet",
            "No named same-dir cluster, or unassembled",
        ),
        "action_scope": _choice(
            "action_scope",
            (
                "Given named corr, what is the intelligence action? "
                "hold_corr is a *corr* HOLD draft. Never occupancy HOLD. "
                "Never already_placed_today (remaining-seats owns that)."
            ),
            {
                "hold_corr": "Draft a correlation HOLD (not occupancy)",
                "size_down": "Tilt size down versus the named cluster",
                "allow": "Named corr does not argue HOLD",
                "abstain": "Unassembled / do not steer",
            },
        ),
        "speak_hold": _noul(
            "speak_hold",
            (
                "Should a named corr HOLD be spoken as a draft? Inbox occupancy "
                "HOLD stays demoted to script. Do not HOLD a legal 15m reprint "
                "as remint."
            ),
            "Named corr HOLD is speakable as a draft",
            "No named corr HOLD, or occupancy-only",
        ),
        "opposite_lock": _score(
            "opposite_lock",
            (
                "Does a named same-symbol opposite position lock this fire? "
                "Keep-one integer stays. Score the lock; do not invent a second "
                "ticket."
            ),
            [
                "Named opposite lock is live",
                "Ordinary / no opposite",
                "Named book is clear of opposite",
            ],
        ),
        "eurgbp_stack": _score(
            "eurgbp_stack",
            (
                "Does a named EUR/GBP same-currency DSP stack argue against "
                "this fire? Integer drop-lists stay. This Score is corr, not a "
                "new surface."
            ),
            [
                "Named EUR/GBP stack is the same bet",
                "Ordinary / unassembled peers",
                "Named stack is independent",
            ],
        ),
    }


def _news_decision_questions() -> dict[str, Any]:
    return {
        "event_proximity": _noul(
            "event_proximity",
            (
                "Is a named HIGH in news.events inside the code window "
                "news.window_pre_min before the print through news.window_post_min "
                "after it? news.feed is context. 'no feed' means the spine file "
                "was not on disk. It does not answer this question."
            ),
            "A named HIGH is inside that window",
            "Named events are present and none are inside that window",
        ),
        "calendar_honest": _noul(
            "calendar_honest",
            (
                "Does news.feed name a calendar already on disk, with "
                "news.events taken from that file and news.invented false? "
                "Consistency only."
            ),
            "The named file supplied the events",
            "There is no on-disk feed, or the events were not read from it",
        ),
        "news_cycle": _choice(
            "news_cycle",
            (
                "For this Challenge as-of, what is the news action? Use "
                "news.feed, news.events, news.nearest, news.inside_window, and "
                "the code window news.window_pre_min / news.window_post_min. "
                "news.feed equal to 'no feed' is context. It does not select "
                "an alternative. Do not invent a mill URL. An open gold ticket "
                "is not closed by this question."
            ),
            {
                "cancel_t15": (
                    "A named HIGH for this fire sits inside the pre window. "
                    "Cancel pending for that print."
                ),
                "reeval_t60": (
                    "A named HIGH for this fire sits inside the post window. "
                    "Reevaluate. Do not auto-cancel."
                ),
                "hold": (
                    "The named calendar does not call for cancel or reevaluate "
                    "on this fire."
                ),
                "abstain": (
                    "Cancel, reevaluate, and hold are each a worse description "
                    "of this as-of than standing aside."
                ),
            },
        ),
    }


def _f5_decision_questions() -> dict[str, Any]:
    return {
        "fire_window": _score(
            "fire_window",
            (
                "Is this the sleeve's clean hour, or merely 'not the dead "
                "clock'? Dead window 21–00Z and Friday 16Z stay CLOCK FACTS in "
                "state. Score fitness; do not invent a second clock."
            ),
            [
                "Dead window / Friday cutoff / wrong hour for this sleeve",
                "Ordinary session",
                "Sleeve's clean hour",
            ],
        ),
        "limit_expiry": _score(
            "limit_expiry",
            (
                "Is a resting native LIMIT still the same thesis given closed "
                "M15 age? Integer 4-bar COUNT still expires. Score whether the "
                "limit is still the fire, not a GTC occupant."
            ),
            [
                "Stale GTC / past 4 closed M15",
                "Ordinary pending age",
                "Still the same-session limit thesis",
            ],
        ),
        "frozen_reprice": _score(
            "frozen_reprice",
            (
                "Does a frozen intent still deserve its original price, or has "
                "tape moved enough that a reprice would be a chase? Integer TTL "
                "stays. Do not own the reprice."
            ),
            [
                "Frozen price is a chase versus named tape",
                "Ordinary / unassembled freeze",
                "Frozen price still is the thesis",
            ],
        ),
        "thin_asia": _score(
            "thin_asia",
            (
                "Does named Asia / thin-hour crypto tape argue wait-as-limit "
                "versus take-market (LTCUSD fill-dev lesson)? Integer thin-hour "
                "route stays. This hop does not own the route."
            ),
            [
                "Thin-book fill-deviation likely",
                "Ordinary Asia hour",
                "Named depth still supports the fire",
            ],
        ),
        "minstop_fit": _score(
            "minstop_fit",
            (
                "Does named stop distance fit broker min-stop / lots-or-ticks, "
                "or is the integer refuse the whole trade? Integer min-stop "
                "stays. Log Score only."
            ),
            [
                "Named stop is at or under the integer min-stop",
                "Ordinary stop versus min",
                "Named stop is comfortably above min",
            ],
        ),
        "pip8_fit": _score(
            "pip8_fit",
            (
                "Does a named cash-FX DSP stop sit at/under 8 pip? Integer "
                "8pip → 0 lots stays. Log Score only. Do not invent a new "
                "surface."
            ),
            [
                "Named stop ≤ 8 pip on DSP FX",
                "Ordinary / not DSP FX",
                "Named stop is above the integer 8 pip",
            ],
        ),
    }


_DECISION_BUILDERS = {
    "exec": _exec_decision_questions,
    "governor": lambda branch=None: _governor_decision_questions(),
    "cluster": lambda branch=None: _cluster_decision_questions(),
    "news": lambda branch=None: _news_decision_questions(),
    "f5_fire": lambda branch=None: _f5_decision_questions(),
}

_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "110000",
    "110,000",
    "110_000",
    "110k",
)


def _limit_key(name: Any) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


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
    out["exec_gov_news_loop_bound"] = _score(
        "exec_gov_news_loop_bound",
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


def include_depth_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "place",
) -> dict[str, Any]:
    """Score include-depth for the chunks *this* fire uses. Not a catalog dump."""
    del state  # query-aware via seat/branch, not a session compact
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
    branch: str = "place",
    standalone: bool = True,
) -> dict[str, Any]:
    """Decision pack for this subtree. Completeness is one Noul when standalone."""
    qs: dict[str, Any] = {}
    if standalone:
        qs["exec_state_sufficient"] = completeness_noul_question()
    for seat in seats_for_branch(branch, seats):
        builder = _DECISION_BUILDERS[seat]
        if seat == "exec":
            qs.update(builder(branch))
        else:
            qs.update(builder())
        # The seat menu names which questions are on this ask.
        # Unassembled news still asks event_proximity.
    return _with_returns(_kept_questions(qs), seats_for_branch(branch, seats))


def seat_subtree_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "place",
    standalone: bool = True,
) -> dict[str, Any]:
    """One subtree: include-depth Scores + decision pack. Merge later ask_together."""
    qs = include_depth_questions(state, seats=seats, branch=branch)
    qs.update(decision_questions(state, seats=seats, branch=branch, standalone=standalone))
    return _kept_questions(qs)


def intent_packs(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "place",
    standalone: bool = True,
) -> dict[str, dict[str, Any]]:
    """Two TypeSafe *reads* from one intent (include-depth, then decision).

    Founder: many TypeSafe calls from one high-level job. Do not second-LLM-hop
    the same gold_state through another model. Compose may consume either the
    combined subtree or these two packs.
    """
    return {
        "include_depth": include_depth_questions(state, seats=seats, branch=branch),
        "decision": decision_questions(
            state, seats=seats, branch=branch, standalone=standalone
        ),
    }


def ignore_if(question_id: str, state: Mapping[str, Any] | None) -> bool | None:
    """No local skip.

    The questions stay on the ask. A missing feed stays in state. Empty,
    thin, or unassembled state does not vote and does not restore a skip.
    """
    del question_id, state
    return None


def noul_question_ids(questions: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(k for k, v in questions.items() if isinstance(v, dict) and v.get("type") == "noul")


def pack_payload(
    state: Mapping[str, Any],
    *,
    seats: Iterable[str] | None = None,
    branch: str = "place",
    standalone: bool = True,
    model: str = MODEL,
) -> dict[str, Any]:
    """Question body for this subtree. The ask is ``evaluate_decisions``.

    Listing these keys does not post. ``merge_sleeve`` stays false so a
    later post sends this subtree only.
    """
    qs = seat_subtree_questions(
        state, seats=seats, branch=branch, standalone=standalone
    )
    scrubbed = _scrub(dict(state or {}))
    if not isinstance(scrubbed, dict):
        scrubbed = {}
    seat = next(iter(seats_for_branch(branch, seats)), "exec")
    return {
        "state": scrubbed,
        "model": model,
        "questions": qs,
        "ask_together": True,
        "merge_sleeve": False,
        "labels": hierarchical_labels(scrubbed, seat=seat, branch=branch),
    }


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
        if best_p is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
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


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

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
    payload = _scrub(dict(state or {}))
    if not isinstance(payload, dict):
        payload = {}
    payload["model"] = MODEL
    seat = next(iter(seats_for_branch(branch, seats)), "exec")
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
        error = receipt.get("error") or receipt.get("skipped") or "empty"
    elif answers and error is None and receipt.get("ok") is False:
        error = str(receipt.get("error") or receipt.get("skipped") or "post_failed")
    named = seats_for_branch(branch, seats)
    decisions: dict[str, Any] = {}
    history: dict[str, Any] = {}
    for qid, block in questions.items():
        if _sidecar(qid) or qid == "exec_gov_news_loop_bound" or qid.startswith("component_"):
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
    bound_id = "exec_gov_news_loop_bound"
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
    branch: str = "place",
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
