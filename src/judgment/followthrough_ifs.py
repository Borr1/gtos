"""Challenge follow-through leftover ifs as a hierarchical Jev tree.

Seats PRs 69/68/67/70, remaining-seats, exec/gov/news, gold-entry,
gold-priors (persist **0.00**), and gold-exit do not own: leftover-open
stay, fast-family takeoff, judgment RESCUE rebind, stale/orphan GTC,
preorder stop widen study, SL-class cooldown yield, chair
manage-file close, min-lot round-up EV, auto-BE log, owner leave-orig,
transient retry, sibling starve order, paid-cluster lesson.

Founder brief (Diogo / Appendix 3): nested labels + log(n) tree search,
Score include-depth (hide / short / long / full). Not linear binary
keep/drop. One completeness Noul on *this* object — not a Noul per tick
because Jev is cheap. Do not compact a Challenge session as forever-state.

Code owns workflow (H4CAP, USDJPY HOLD, 2-stop COUNT, keep-one, auto-BE
OFF, 8pip, min-stop, retry cap, weekend-flat, FLATTEN.flag, token digest,
CALPRIME/Q1FLOOR dark, SEL-V4 research). TypeSafe owns the semantic call
that used to be a flatten / rebind / cancel / yield / enroll *judgment*.

Every decision this module returns, including every parameter, is the
value System One returns for that state. One post:
``jev_client.evaluate`` (model ``jev-1.13.0``,
POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
The return is only a Noul, a Choice, or a Score. A Score may sit
between levels. Prior outcomes are attached on that ask. An empty
answer, a tie, or an error leaves the return unset. Account floor
and baseline are not a question. This module does not send and does
not flatten.

This module does **not** edit ``jev_questions.py``. Subtree questions
live here. After stacked unique files land, merge ``standalone=False``
into the one System One POST. Do not add a second LLM hop on the same
gold_state. Do not copy #77 persist 0.10. Persist APPLY stays 0.00.

Pin model ``jev-1.13.0``. Challenge book ``0`` / ``operator``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Iterable, Mapping

from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS
from .jev_questions import MODEL

INCLUDE_DEPTH_LEVELS = ("hide", "short", "long", "full")
INCLUDE_DEPTH_CRITERIA = [
    "Hide this chunk — not needed for this fire's query",
    "Short summary of the named fields in this chunk",
    "Longer summary of the named fields in this chunk",
    "Include the whole named chunk",
]

SEATS = (
    "leftover",
    "rescue",
    "pending",
    "cooldown",
    "chair",
    "size_physics",
    "sibling",
    "lesson",
)
BRANCHES = (
    "leftover",
    "rescue",
    "pending",
    "cooldown",
    "chair",
    "size",
    "sibling",
    "lesson",
)

SEAT_CHUNKS: dict[str, tuple[str, ...]] = {
    "leftover": ("leftover_open", "mfe_mae", "atlas"),
    "rescue": ("rescue_file", "candidate_id", "cost_dead"),
    "pending": ("pending_age", "gtc_level", "tape"),
    "cooldown": ("close_class", "age", "sibling_clock"),
    "chair": ("manage_file", "why_code", "authority"),
    "size_physics": ("lots", "stop_pips", "retry_count", "orig_sl"),
    "sibling": ("siblings_this_bar", "conviction"),
    "lesson": ("cluster_set", "nightly_body"),
}

BRANCH_SEATS: dict[str, tuple[str, ...]] = {
    "leftover": ("leftover",),
    "rescue": ("rescue",),
    "pending": ("pending",),
    "cooldown": ("cooldown",),
    "chair": ("chair",),
    "size": ("size_physics",),
    "sibling": ("sibling",),
    "lesson": ("lesson",),
}

# Integer walls this unique PR does **not** convert. Path/err stays code.
INTEGER_FACTS: tuple[str, ...] = (
    "h4_daily_unit_cap",
    "usdjpy_standing_hold",
    "two_stop_count",
    "occupancy_keep_one",
    "auto_be_off",
    "fx_dsp_8pip",
    "min_stop_ticks",
    "retry_cap",
    "weekend_flat",
    "operator_flatten_flag",
    "token_digest_match",
    "calprime_dark",
    "q1floor_dark",
    "sel_v4_research",
    "halt",
    "named_surface",
    "prop_wall",
    "never_widen",
)

# Converted IDs this unique PR owns. Do not claim remaining-seats already_placed
# / remint / restart / ac60, exec/gov/news place-modify-close, gold-exit
# geometries, or #77 persist 0.10.
CONVERTED_IFS: tuple[dict[str, str], ...] = (
    {
        "id": "F5-MS-OPENSTAY",
        "was": "leftover-open atlas stay: keep hold-to-orig vs manage flatten",
        "now": "Score leftover_stay; extra_flatten never; empty or error leaves the score unset",
        "seat": "leftover",
        "branch": "leftover",
    },
    {
        "id": "F5-MS-TAKEOFF",
        "was": "fast-family takeoff: displacement spent, level reached short of TP",
        "now": "Score takeoff_spent; Choice takeoff_label; do not own the close",
        "seat": "leftover",
        "branch": "leftover",
    },
    {
        "id": "F5-MS-RESCUE",
        "was": "judgment RESCUE rebinds a cost-dead intent to a fresh candidate_id",
        "now": "Choice rescue_action; empty or tie leaves the choice unset; Jev must not invent rescue",
        "seat": "rescue",
        "branch": "rescue",
    },
    {
        "id": "F5-MS-STALEPEND",
        "was": "stale/orphan GTC sweep",
        "now": "Score stale_pending; cancel is writer; empty or error leaves the score unset",
        "seat": "pending",
        "branch": "pending",
    },
    {
        "id": "F5-MS-STOPFLOOR",
        "was": "preorder widen stop vs refuse; 5-pip widen still fired; 8pip refuse",
        "now": "Score stop_floor_widen; integer 8pip stays; empty or error leaves the score unset",
        "seat": "size_physics",
        "branch": "size",
    },
    {
        "id": "F5-MS-COOLDOWN",
        "was": "after SL-class close: FX DSP majors wait 4h; metals/index 15m sibling",
        "now": "Noul isolated_after_window; integer window still binds; empty or error leaves the noul unset",
        "seat": "cooldown",
        "branch": "cooldown",
    },
    {
        "id": "F5-MS-MANAGECLOSE",
        "was": "chair manage-file close/tighten consume",
        "now": "Choice chair_manage_noun; writer consumes file; empty or tie leaves the choice unset",
        "seat": "chair",
        "branch": "chair",
    },
    {
        "id": "F5-MS-MINLOT",
        "was": "round up to broker min lot (BTC/XAU otherwise vanish at $150)",
        "now": "Score minlot_ev; integer min-lot still rounds; empty or error leaves the score unset",
        "seat": "size_physics",
        "branch": "size",
    },
    {
        "id": "F5-MS-AUTOBE",
        "was": "F5_AUTO_BE_ENABLED=False; trigger 1.5R; lock 0.05-0.20R",
        "now": "Score autobe_study; integer stays OFF; Jev must not enable BE",
        "seat": "size_physics",
        "branch": "size",
    },
    {
        "id": "UB-MGT-LEAVEORIG",
        "was": "owner breathe: keep orig SL vs software remint",
        "now": "Score leaveorig_fit; extra_remint_sl never; empty or error leaves the score unset",
        "seat": "size_physics",
        "branch": "size",
    },
    {
        "id": "F5-MS-RETRY",
        "was": "transient retry cap (FN 2026-08-04 oil storm)",
        "now": "Noul retry_tape_fresh; integer cap is physics; empty or error leaves the noul unset",
        "seat": "size_physics",
        "branch": "size",
    },
    {
        "id": "UB-PLC-SIBLING",
        "was": "sibling member starves a better member on the same bar",
        "now": "Choice sibling_pick; Score sibling_conviction; empty or tie leaves the return unset",
        "seat": "sibling",
        "branch": "sibling",
    },
    {
        "id": "F5-MS-PAIDCLUSTER",
        "was": "F5_PAID_CLUSTER_SLEEVES still includes dsp_bleed (Nightly body)",
        "now": "Score paid_cluster_lesson; extra_enroll never; empty or error leaves the score unset",
        "seat": "lesson",
        "branch": "lesson",
    },
)

_SNIPPETS: dict[str, str] = {
    "leftover": "hold-to-orig vs flatten; takeoff spent-displacement label; Jev does not flatten",
    "rescue": "bound RESCUE rebind vs invent; missing Jev no extra rebind",
    "pending": "orphan GTC still the intended level; cancel is writer",
    "cooldown": "SL-class wait window; integer 4h/15m; yield only when named isolated",
    "chair": "manage-file close/tighten noun; writer consumes; leave-orig when dark",
    "size_physics": "min-lot EV, stop widen study, auto-BE OFF, leave-orig SL, retry cap",
    "sibling": "same-bar sibling order; integer starve stays; no extra place when dark",
    "lesson": "Nightly paid-cluster lesson; never enroll from Jev",
}


def integer_facts() -> tuple[str, ...]:
    return INTEGER_FACTS


def integer_walls() -> tuple[str, ...]:
    """Named walls that stay code. Not a converted-if catalog."""
    return INTEGER_FACTS


def converted_ifs() -> tuple[dict[str, str], ...]:
    return CONVERTED_IFS


def converted_if_ids() -> tuple[str, ...]:
    return tuple(row["id"] for row in CONVERTED_IFS)


def directional_snippet(seat: str) -> str:
    return _SNIPPETS.get(str(seat or "").strip().lower(), "unnamed followthrough seat")


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
    seat: str = "leftover",
    branch: str = "leftover",
) -> dict[str, Any]:
    """Nested labels so a later tree-search can find this object. Not a transcript."""
    identity = dict((state or {}).get("identity") or {})
    clock = dict((state or {}).get("clock") or {})
    sl = str(identity.get("sleeve") or "")
    sy = str(identity.get("symbol") or "")
    origin_s = str(identity.get("origin_organism") or "f5_challenge")
    node = str(seat or "leftover")
    br = str(branch or "leftover")
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
        "subgoal": f"followthrough:{node}:{br}:{sl or 'none'}",
    }


def _noul(_qid: str, instructions: str, true_line: str, false_line: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": true_line, "false": false_line},
    }


def _score(_qid: str, instructions: str, criteria: list[str]) -> dict[str, Any]:
    return {"type": "score", "instructions": instructions, "criteria": criteria}


def _choice(_qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


def _include_question(chunk: str) -> dict[str, Any]:
    return _score(
        f"include_{chunk}",
        (
            f"How much of the named `{chunk}` chunk does this fire's query need? "
            "hide / short / long / full. The score you return is that depth. "
            "It may sit between the levels. An empty score leaves this return unset. "
            "Query-aware — not a catalog dump."
        ),
        list(INCLUDE_DEPTH_CRITERIA),
    )


def completeness_noul_question() -> dict[str, Any]:
    return _noul(
        "followthrough_state_sufficient",
        (
            "Do the named follow-through chunks for this fire (leftover_open/"
            "rescue_file/pending_age/manage_file/lots as this seat uses them) "
            "contain enough to judge as-of clock.as_of_utc? One completeness "
            "Noul on this object — not a Noul per tick or per converted if. "
            "An empty answer leaves this return unset. A missing answer is "
            "not an extra pass."
        ),
        "Named follow-through chunks are present enough to judge this fire",
        "A required named follow-through chunk is missing or unknown",
    )


def _leftover_decision_questions() -> dict[str, Any]:
    return {
        "leftover_stay": _score(
            "leftover_stay",
            (
                "Does this leftover-open ticket still have hold-to-orig edge "
                "given named atlas stay, MFE/MAE vs orig SL? The score you "
                "return is that edge. It may sit between the levels. "
                "An empty score leaves this return unset. "
                "Jev must not flatten. Live trades are not a stop."
            ),
            [
                "Named leftover is spent — observe-close, writer owns flatten",
                "Ordinary leftover / unassembled MFE",
                "Hold-to-orig still has edge — leave orig",
            ],
        ),
        "takeoff_spent": _score(
            "takeoff_spent",
            (
                "Has the fast-family displacement spent, with a named level "
                "reached short of TP? The score you return is that read. "
                "It may sit between the levels. An empty score leaves this "
                "return unset. Observe label. Do not own the close. "
                "Do not invent a flatten."
            ),
            [
                "Displacement spent / level reached short of TP",
                "Ordinary / unassembled takeoff",
                "Displacement still the same fire",
            ],
        ),
        "takeoff_label": _choice(
            "takeoff_label",
            (
                "LABEL only. Name the leftover/takeoff noun. Writer still "
                "prints. The unique highest probability is the decision. "
                "An empty answer or a tie leaves this return unset. "
                "Do not flatten. Criteria include time_stop."
            ),
            {
                "orig_stop": "Named leftover still rides orig SL",
                "time_stop": "Named leftover is a writer-horizon close candidate",
                "takeoff": "Named displacement spent short of TP",
                "leave_orig": "Hold-to-orig; do not flatten",
                "abstain": "Unassembled / do not steer",
            },
        ),
    }


def _rescue_decision_questions() -> dict[str, Any]:
    return {
        "rescue_action": _choice(
            "rescue_action",
            (
                "Given a bound RESCUE file + candidate_id, rebind a cost-dead "
                "intent, leave it, or abstain? Jev must not invent rescue. "
                "The unique highest probability is the decision. "
                "An empty answer or a tie leaves this return unset. "
                "Integer requires the bound file. Do not send an order."
            ),
            {
                "rebind": "Named bound RESCUE still the same thesis — draft rebind",
                "leave": "Named RESCUE is spent / wrong book — leave code-only",
                "abstain": "Unassembled / no bound file — do not invent rescue",
            },
        ),
        "isolated_reentry_is_new": _noul(
            "isolated_reentry_is_new",
            (
                "Is this rescued cost-dead intent a new named fire, not a "
                "remint of the spent ticket? Occupancy keep-one stays integer. "
                "An empty answer leaves this return unset. A missing answer "
                "is not an extra pass."
            ),
            "Named rescue is a new isolated fire",
            "Named rescue is a remint of the spent ticket, or unassembled",
        ),
    }


def _pending_decision_questions() -> dict[str, Any]:
    return {
        "stale_pending": _score(
            "stale_pending",
            (
                "Is an orphan/stale GTC still the intended level given age and "
                "tape vs decision price? The score you return is that read. "
                "It may sit between the levels. Integer sweep stays writer. "
                "Jev must not cancel. An empty score leaves this return unset."
            ),
            [
                "Stale / previous-session / restart GTC ghost",
                "Ordinary pending age",
                "Still the intended same-session level",
            ],
        ),
        "chase_toxicity": _score(
            "chase_toxicity",
            (
                "Would cancelling-and-restarting this pending be a chase? "
                "The score you return is that read. It may sit between the "
                "levels. An empty score leaves this return unset. "
                "Cancel is writer. Do not extra-cancel."
            ),
            [
                "Restart would chase named tape",
                "Ordinary / unassembled",
                "Pending is still the same setup",
            ],
        ),
    }


def _cooldown_decision_questions() -> dict[str, Any]:
    return {
        "isolated_after_window": _noul(
            "isolated_after_window",
            (
                "After an SL-class close, is this same-symbol continuation a "
                "new isolated fire once the integer window elapsed (FX DSP "
                "majors 4h; metals/index 15m sibling)? Integer window still "
                "binds. An empty answer leaves this return unset."
            ),
            "Named continuation is a new fire after the integer window",
            "Named continuation is still the spent ticket, or window not elapsed",
        ),
        "cooldown_fitness": _score(
            "cooldown_fitness",
            (
                "Given close_class, age, and sibling clock, how spent is this "
                "continuation? The score you return is that read. It may sit "
                "between the levels. Integer 4h/15m still wait in code. "
                "An empty score leaves this return unset."
            ),
            [
                "Still the spent ticket inside the integer window",
                "Ordinary / unassembled age",
                "Window elapsed and tape is a new fire",
            ],
        ),
    }


def _chair_decision_questions() -> dict[str, Any]:
    return {
        "chair_manage_noun": _choice(
            "chair_manage_noun",
            (
                "LABEL only. Name the chair manage-file action. Writer consumes "
                "the file. H8 if authority false. Jev must not be the flatten. "
                "The unique highest probability is the decision. "
                "An empty answer or a tie leaves this return unset. "
                "Criteria include time_stop."
            ),
            {
                "close": "Named manage-file is a close consume",
                "tighten": "Named manage-file is a SL tighten",
                "time_stop": "Named manage-file is a writer-horizon close",
                "leave_orig": "Hold orig; do not consume as flatten",
                "abstain": "Unassembled / no manage file",
            },
        ),
        "chair_beats_hold": _score(
            "chair_beats_hold",
            (
                "Does the named chair manage action beat hold-to-orig given "
                "why_code and MFE? The score you return is that read. It may "
                "sit between the levels. An empty score leaves this return "
                "unset. Observe. Writer still consumes. Jev does not flatten."
            ),
            [
                "Named manage action looks worse than hold-to-orig",
                "Ordinary / unassembled manage file",
                "Named manage action beats hold-to-orig",
            ],
        ),
    }


def _size_physics_decision_questions() -> dict[str, Any]:
    return {
        "minlot_ev": _score(
            "minlot_ev",
            (
                "Does rounding up to broker min lot (BTC/XAU otherwise vanish "
                "at $150) still have +EV after inflation? The score you return "
                "is that read. It may sit between the levels. Integer min-lot "
                "still rounds in code. An empty score leaves this return unset. "
                "Do not drop below min."
            ),
            [
                "Rounded-up lot looks -EV after inflation",
                "Ordinary / unassembled lots",
                "Rounded-up lot still has named +EV",
            ],
        ),
        "stop_floor_widen": _score(
            "stop_floor_widen",
            (
                "Would a preorder widen of the stop beat refuse, given named "
                "ATR/spread? The score you return is that read. It may sit "
                "between the levels. The integer 8pip refuse stays in code. "
                "A 5-pip widen still fired historically. An empty score leaves "
                "this return unset. Do not send an order."
            ),
            [
                "Widen looks worse than refuse, including at the integer 8pip refuse",
                "Ordinary / not DSP FX",
                "Named widen still has edge versus refuse",
            ],
        ),
        "autobe_study": _score(
            "autobe_study",
            (
                "Would a +1.5R auto-BE raise E[R] vs leave-orig? The score you "
                "return is that read. It may sit between the levels. Integer "
                "F5_AUTO_BE_ENABLED stays off in code. Auto-BE was the Verification "
                "loss. Jev must not enable BE. An empty score leaves this return unset."
            ),
            [
                "Auto-BE would cut the winner (Verification shape)",
                "Ordinary / unassembled MFE",
                "Named BE would raise E[R] — still do not enable from Jev",
            ],
        ),
        "leaveorig_fit": _score(
            "leaveorig_fit",
            (
                "Does keep-orig SL beat coded scale-out / auto-BE given sleeve "
                "and MFE? The score you return is that read. It may sit "
                "between the levels. F5 leave-orig is envelope. Jev must not "
                "remint SL. An empty score leaves this return unset."
            ),
            [
                "Coded remint looks better — still leave orig until writer",
                "Ordinary / unassembled live_sl",
                "Keep orig SL is the named better path",
            ],
        ),
        "retry_tape_fresh": _noul(
            "retry_tape_fresh",
            (
                "Is the Nth transient retry still a fillable tape (not the "
                "FN 2026-08-04 oil storm)? Integer retry cap is physics. "
                "Jev does not own the retry. An empty answer leaves this "
                "return unset."
            ),
            "Named reject looks transient — tape still fresh",
            "Named reject looks a storm / spent, or unassembled",
        ),
    }


def _sibling_decision_questions() -> dict[str, Any]:
    return {
        "sibling_pick": _choice(
            "sibling_pick",
            (
                "Given named siblings this bar, which member is the cluster's "
                "best fire? The unique highest probability is the decision. "
                "An empty answer or a tie leaves this return unset. "
                "Integer starve still stands in code. Do not invent a second "
                "ticket. Do not send an order."
            ),
            {
                "this_member": "Named this member is the cluster's best fire",
                "other_member": "A named sibling is better — starve this one",
                "abstain": "Unassembled siblings / do not extra-place",
            },
        ),
        "sibling_conviction": _score(
            "sibling_conviction",
            (
                "How much conviction does this member have versus named "
                "siblings on the same bar? The score you return is that "
                "conviction. It may sit between the levels. Integer keep-one "
                "stays in code. An empty score leaves this return unset. "
                "Do not send an order."
            ),
            [
                "Named sibling is stronger — this member starves",
                "Ordinary / unassembled siblings",
                "This member is the named stronger fire",
            ],
        ),
    }


def _lesson_decision_questions() -> dict[str, Any]:
    return {
        "paid_cluster_lesson": _score(
            "paid_cluster_lesson",
            (
                "Is the named Nightly cluster still the paying set on Challenge "
                "post-cut? The score you return is that lesson. It may sit "
                "between the levels. F5_PAID_CLUSTER_SLEEVES still lists bleed "
                "names. Score lesson for body nouns only. NEVER enroll from Jev. "
                "An empty score leaves this return unset."
            ),
            [
                "Named cluster is bleed / house-off — do not enroll",
                "Ordinary / unassembled Nightly body",
                "Named cluster is still the paying set — still do not enroll from Jev",
            ],
        ),
        "lesson_speak": _noul(
            "lesson_speak",
            (
                "Should this Nightly lesson be spoken as a draft? Enroll stays "
                "writer / owner. Jev must not enroll. An empty answer leaves "
                "this return unset."
            ),
            "Named lesson is speakable as a draft",
            "No named lesson, or enroll-shaped — stay silent",
        ),
    }


_DECISION_BUILDERS = {
    "leftover": lambda: _leftover_decision_questions(),
    "rescue": lambda: _rescue_decision_questions(),
    "pending": lambda: _pending_decision_questions(),
    "cooldown": lambda: _cooldown_decision_questions(),
    "chair": lambda: _chair_decision_questions(),
    "size_physics": lambda: _size_physics_decision_questions(),
    "sibling": lambda: _sibling_decision_questions(),
    "lesson": lambda: _lesson_decision_questions(),
}


def include_depth_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "leftover",
) -> dict[str, Any]:
    """Score include-depth for the chunks *this* fire uses. Not a catalog dump."""
    del state
    qs: dict[str, Any] = {}
    for seat in seats_for_branch(branch, seats):
        for chunk in SEAT_CHUNKS.get(seat, ()):
            qid = f"include_{chunk}"
            qs[qid] = _include_question(chunk)
            qs[f"{qid}_parameter"] = _parameter_block(qid)
    return qs


_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LIMIT_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "daily_loss_pct",
    "floor_room",
    "to_pass",
})
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "90K",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "110K",
)
_BANNED_QUESTION_IDS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "to_pass",
    "floor_room",
    "flatten_floor_usd",
    "daily_loss_pct",
})
_DROP = object()


def _limit_key(name: str) -> bool:
    token = str(name).strip().lower().replace("-", "_")
    if "baseline" in token or token in _LIMIT_KEYS:
        return True
    if "floor" in token and "widen" not in token:
        return True
    return False


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


# Span for this card. It expires when the card changes. Empty does not write one.
_SPAN_KEY: str | None = None
_SPAN_SCORE: float | None = None
_SPAN_NOW: float | None = None


def _card_key(value: Any) -> str:
    try:
        blob = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    except (TypeError, ValueError):
        blob = repr(value)
    return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()


def _span_for(key: str) -> float | None:
    if _SPAN_KEY != key:
        return None
    return _SPAN_SCORE


def _remember_span(key: str, score: float | None) -> None:
    global _SPAN_KEY, _SPAN_SCORE
    if _SPAN_KEY != key:
        _SPAN_KEY = key
        _SPAN_SCORE = None
    if score is not None and score > 0:
        _SPAN_SCORE = score


def _banned_number(number: float) -> bool:
    """A number leaves the card when it sits inside the returned span.

    No span does not drop the number.
    """

    span = _SPAN_NOW
    if span is None:
        return False
    return abs(number - 90000.0) < span or abs(number - 110000.0) < span


def _span_question() -> dict[str, Any]:
    return _score(
        "followthrough_number_span",
        (
            "The score you return is the span that decides whether a number "
            "leaves this card. An empty score leaves the span unset. "
            "Do not flatten. Do not send an order."
        ),
        list(_BETWEEN),
    )


def _scrub_state(value: Any) -> Any:
    """Drop account floor and baseline before an ask. Leave every other fact."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            cleaned = _scrub_state(item)
            if cleaned is _DROP:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        kept = []
        for item in value:
            cleaned = _scrub_state(item)
            if cleaned is not _DROP:
                kept.append(cleaned)
        return kept
    if isinstance(value, str):
        return _scrub_text(value)
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if _banned_number(float(value)):
            return _DROP
        return value
    return str(value)


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


def _with_returns(questions: Mapping[str, Any], seats: tuple[str, ...]) -> dict[str, Any]:
    """Pair each decision with its parameter. A Choice also carries a threshold.

    Seat existence is a Noul. The loop bound is a Score. The bound is not
    used to drop a seat. Account floor and baseline are not questions.
    """

    out = dict(questions)
    for qid, block in list(questions.items()):
        if not isinstance(block, dict):
            continue
        kind = str(block.get("type") or "")
        if kind not in {"noul", "choice", "score"}:
            continue
        out[f"{qid}_parameter"] = _parameter_block(qid)
        if kind == "choice":
            out[f"{qid}_threshold"] = _threshold_block(qid)
    for seat in seats:
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
    out["followthrough_loop_bound"] = _score(
        "followthrough_loop_bound",
        (
            "How many of these follow-through decisions are in this fire? "
            "The score you return is that bound. It may sit between the levels. "
            "An empty score leaves the bound unset. "
            "Do not flatten. Do not send an order."
        ),
        [
            "no further decision on this fire",
            "the decisions named on this state",
            "the decisions still open on this fire",
        ],
    )
    return out


def decision_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "leftover",
    standalone: bool = True,
) -> dict[str, Any]:
    """Decision pack for this subtree. Completeness is one Noul when standalone.

    The parameter on each decision is a Score on this same pack. A Choice
    also asks its threshold. Nothing here fills a miss with a constant.
    """
    del state
    qs: dict[str, Any] = {}
    if standalone:
        qs["followthrough_state_sufficient"] = completeness_noul_question()
    named = seats_for_branch(branch, seats)
    for seat in named:
        qs.update(_DECISION_BUILDERS[seat]())
    return _with_returns(qs, named)


def seat_subtree_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "leftover",
    standalone: bool = True,
) -> dict[str, Any]:
    """One subtree: include-depth Scores + decision pack. Merge later ask_together."""
    qs = include_depth_questions(state, seats=seats, branch=branch)
    qs.update(decision_questions(state, seats=seats, branch=branch, standalone=standalone))
    return qs


def intent_packs(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "leftover",
    standalone: bool = True,
) -> dict[str, dict[str, Any]]:
    """Two TypeSafe *reads* from one intent (include-depth, then decision)."""
    return {
        "include_depth": include_depth_questions(state, seats=seats, branch=branch),
        "decision": decision_questions(
            state, seats=seats, branch=branch, standalone=standalone
        ),
    }


def ignore_if(question_id: str, state: Mapping[str, Any] | None) -> bool:
    """Query-aware compression. Unassembled ≠ a vote. Ignore-if is compose-side."""
    st = dict(state or {})
    qid = str(question_id or "")
    identity = dict(st.get("identity") or {})
    facts = dict(st.get("facts") or {})
    leftover = dict(st.get("leftover") or st.get("position") or {})
    rescue = dict(st.get("rescue") or {})
    pending = dict(st.get("pending") or {})
    chair = dict(st.get("chair") or st.get("manage") or {})
    cooldown = dict(st.get("cooldown") or {})
    size = dict(st.get("size") or st.get("execution") or {})
    siblings = st.get("siblings")
    lesson = dict(st.get("lesson") or {})
    if qid in {"leftover_stay", "takeoff_spent", "takeoff_label"}:
        return leftover in (None, False, {}) and not facts.get("leftover_open")
    if qid in {"rescue_action", "isolated_reentry_is_new"}:
        return not (rescue.get("file") or facts.get("rescue_file") or identity.get("candidate_id"))
    if qid in {"stale_pending", "chase_toxicity"}:
        return pending in (None, False, {}) and not facts.get("pending_age")
    if qid in {"isolated_after_window", "cooldown_fitness"}:
        return cooldown in (None, False, {}) and facts.get("close_class") is None
    if qid in {"chair_manage_noun", "chair_beats_hold"}:
        return not (chair.get("file") or facts.get("manage_file"))
    if qid in {"minlot_ev", "stop_floor_widen", "autobe_study", "leaveorig_fit", "retry_tape_fresh"}:
        return size in (None, False, {}) and not facts
    if qid in {"sibling_pick", "sibling_conviction"}:
        return siblings in (None, False, {}, [])
    if qid in {"paid_cluster_lesson", "lesson_speak"}:
        return lesson in (None, False, {}) and not facts.get("nightly_body")
    return False


def noul_question_ids(questions: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(k for k, v in questions.items() if isinstance(v, dict) and v.get("type") == "noul")


def pack_payload(
    state: Mapping[str, Any],
    *,
    seats: Iterable[str] | None = None,
    branch: str = "leftover",
    standalone: bool = True,
    model: str = MODEL,
) -> dict[str, Any]:
    """Pack-only body for this subtree. The decision call is ``evaluate_followthrough_ifs``.

    Account floor and baseline are removed before the body is returned.
    Path/err stays code — never raises into a fire path.
    """
    qs = _clean_questions(seat_subtree_questions(
        state, seats=seats, branch=branch, standalone=standalone
    ))
    qs.update(_span_question())
    named = seats_for_branch(branch, seats)
    global _SPAN_NOW
    card = dict(state or {})
    _SPAN_NOW = _span_for(_card_key(card))
    try:
        scrubbed = _scrub_state(card)
    finally:
        _SPAN_NOW = None
    return {
        "state": scrubbed,
        "model": model,
        "questions": qs,
        "ask_together": True,
        "merge_sleeve": False,
        "labels": hierarchical_labels(
            state, seat=next(iter(named), "leftover"), branch=branch
        ),
    }


def _clean_questions(questions: Mapping[str, Any]) -> dict[str, Any]:
    """Keep Noul, Choice, and Score. Drop an account floor or baseline question."""

    out: dict[str, Any] = {}
    for qid, block in questions.items():
        name = str(qid).strip().lower()
        if name in _BANNED_QUESTION_IDS or _limit_key(name):
            continue
        if not isinstance(block, dict):
            continue
        kind = str(block.get("type") or "").lower()
        if kind not in {"noul", "choice", "score"}:
            continue
        copied = dict(block)
        copied["type"] = kind
        if "instructions" in copied:
            copied["instructions"] = _scrub_text(str(copied["instructions"]))
        criteria = copied.get("criteria")
        if isinstance(criteria, Mapping):
            copied["criteria"] = {
                str(key): _scrub_text(str(text)) for key, text in criteria.items()
            }
        elif isinstance(criteria, list):
            copied["criteria"] = [_scrub_text(str(item)) for item in criteria]
        for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
            copied.pop(key, None)
        out[str(qid)] = copied
    return out


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    if _banned_number(number):
        return None
    return number


def _sidecar(qid: str) -> bool:
    return qid.endswith("_parameter") or qid.endswith("_threshold")


def _choice_value(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "choice":
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return None
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _finite(val)
        if number is None:
            continue
        numeric[name] = number
    if not numeric:
        return None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(numeric), order)
    except Exception:
        picked = None
    if picked is None or str(picked) not in order:
        return None
    return str(picked)


def _score_value(block: Any) -> float | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "score":
        return None
    number = None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = None
    return _finite(number)


def _noul_value(block: Any) -> bool | float | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "noul":
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
        state["prior_outcomes"] = loaded if loaded is not None else []
    except Exception:
        state["prior_outcomes"] = []


def _remember(state: Mapping[str, Any], qid: str, value: Any, error: str | None) -> None:
    try:
        from .jev_questions import append_outcome

        append_outcome(qid, value, state, error=error)
    except Exception:
        return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> tuple[dict[str, Any], str | None]:
    """One System One evaluate. Empty and error leave the answers unset."""

    _attach_priors(state, questions)
    state["model"] = MODEL
    try:
        call = evaluate_fn
        if call is None:
            from .jev_client import evaluate as call
        receipt = call(
            state,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:
        return {}, type(exc).__name__
    if not isinstance(receipt, dict):
        return {}, "evaluate_not_a_dict"
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        err = receipt.get("error") or receipt.get("skipped") or "empty"
        return {}, str(err)
    error = None
    if receipt.get("ok") is False:
        error = str(receipt.get("error") or receipt.get("skipped") or "post_failed")
    return answers, error


def _criteria_order(block: Mapping[str, Any]) -> tuple[str, ...]:
    criteria = block.get("criteria")
    if isinstance(criteria, Mapping):
        return tuple(str(key) for key in criteria)
    return ()


def _read_decision(
    qid: str,
    block: Mapping[str, Any],
    answers: Mapping[str, Any],
    questions: Mapping[str, Any],
) -> dict[str, Any]:
    kind = str(block.get("type") or "")
    raw = answers.get(qid)
    threshold = None
    if kind == "choice":
        value: Any = _choice_value(raw, _criteria_order(block))
        threshold = _score_value(answers.get(f"{qid}_threshold"))
        parameter = _score_value(answers.get(f"{qid}_parameter"))
    elif kind == "noul":
        value = _noul_value(raw)
        parameter = _score_value(answers.get(f"{qid}_parameter"))
    elif kind == "score":
        value = _score_value(raw)
        if f"{qid}_parameter" in questions:
            parameter = _score_value(answers.get(f"{qid}_parameter"))
        else:
            parameter = value
    else:
        value = None
        parameter = None
    return {"value": value, "parameter": parameter, "threshold": threshold}


def _remember_row(
    state: Mapping[str, Any],
    qid: str,
    row: Mapping[str, Any],
    error: str | None,
    questions: Mapping[str, Any],
) -> None:
    fields = [(qid, row.get("value"), "unset" if row.get("value") is None else None)]
    if f"{qid}_parameter" in questions:
        fields.append((
            f"{qid}_parameter",
            row.get("parameter"),
            "score_missing" if row.get("parameter") is None else None,
        ))
    if f"{qid}_threshold" in questions:
        fields.append((
            f"{qid}_threshold",
            row.get("threshold"),
            "score_missing" if row.get("threshold") is None else None,
        ))
    for key, value, miss in fields:
        _remember(state, key, value, error or miss)


def evaluate_followthrough_ifs(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "leftover",
    standalone: bool = True,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Ask this subtree once. Every decision, including every parameter, is that return.

    One ``jev_client.evaluate`` for model ``jev-1.13.0``
    (POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
    Questions are only a Noul, a Choice, or a Score. Prior outcomes are
    attached on the ask, and the return is stored for the next ask.
    An empty answer, a tie, or an error leaves that return unset.
    The loop bound does not drop a seat. This module does not send and
    does not flatten.
    """

    named = seats_for_branch(branch, seats)
    try:
        questions = _clean_questions(seat_subtree_questions(
            state, seats=seats, branch=branch, standalone=standalone
        ))
        questions.update(_span_question())
        global _SPAN_NOW
        card = dict(state or {})
        card_key = _card_key(card)
        _SPAN_NOW = _span_for(card_key)
        try:
            posted = _scrub_state(card)
        finally:
            _SPAN_NOW = None
        if not isinstance(posted, dict):
            posted = {}
        posted.pop("prior_outcomes", None)
        posted["model"] = MODEL
        answers, error = _post(posted, questions, evaluate_fn)
    except Exception as exc:
        return {
            "model": MODEL,
            "decisions": {},
            "components": {seat: {"exists": None, "parameter": None} for seat in named},
            "loop_bound": None,
            "error": type(exc).__name__,
        }
    decisions: dict[str, Any] = {}
    components: dict[str, Any] = {
        seat: {"exists": None, "parameter": None} for seat in named
    }
    for qid, block in questions.items():
        if _sidecar(qid) or qid == "followthrough_loop_bound":
            continue
        if qid.startswith("component_"):
            seat = qid[len("component_"):]
            present = None if error and not answers else _noul_value(answers.get(qid))
            if error and qid not in answers:
                present = None
            parameter = _score_value(answers.get(f"{qid}_parameter"))
            if error and f"{qid}_parameter" not in answers:
                parameter = None
            components[seat] = {"exists": present, "parameter": parameter}
            _remember(posted, qid, present, error if present is None else None)
            _remember(
                posted,
                f"{qid}_parameter",
                parameter,
                error if parameter is None else None,
            )
            continue
        if not isinstance(block, dict):
            continue
        row = _read_decision(qid, block, answers, questions)
        if error and qid not in answers:
            row = {"value": None, "parameter": None, "threshold": None}
        decisions[qid] = row
        _remember_row(
            posted,
            qid,
            row,
            error if row.get("value") is None else None,
            questions,
        )
    loop_bound = _score_value(answers.get("followthrough_loop_bound"))
    if error and "followthrough_loop_bound" not in answers:
        loop_bound = None
    span = _score_value(answers.get("followthrough_number_span"))
    if error and "followthrough_number_span" not in answers:
        span = None
    _remember_span(card_key, span)
    _remember(
        posted,
        "followthrough_loop_bound",
        loop_bound,
        error if loop_bound is None else None,
    )
    return {
        "model": MODEL,
        "decisions": decisions,
        "components": components,
        "loop_bound": loop_bound,
        "number_span": span,
        "error": error,
    }
