"""Challenge close tape for Jev-everywhere.

Every decision on a tape row, including every parameter, is the System One
return for that state. One call: ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False``. That call POSTs
https://api.typesafe.ai/v1/systemone. Questions are only Noul, Choice, or
Score. Prior outcomes are attached on the ask, and the return is stored
for the next ask.

An empty answer, a tie, a missing score, or an error leaves that field
unset. Floor and baseline are not a question. Subclass names, hard-off
markers, and the two CF study identities are a menu on the state.
Membership in that menu is not a verdict.

This module does not send. Judge code cannot send. No live bars are read
here. A missing tape helper leaves that source empty.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0
SCHEMA = "gtos.judgment.close_state.v0"

# Tape subclass names are a menu. The name does not select a close.
TAPE_SUBCLASSES = (
    "fs_half_still_losing",
    "session_cut_loss",
    "event_gap_shadow",
    "full_size_loss",
    "review_keep_offhours_false_structure",
    "ok_win",
    "cost_avoided_by_reject",
)

# Marker strings are facts. They do not force an admit.
HARD_MARKERS = ("idxrev", "orb_", "bleed", "xa_huge", "mx_us30", "US30")

_EXIT_ORDER = ("tp", "orig_stop", "time_stop", "manual_other")
_REASON_ORDER = ("tp", "sl", "time_stop", "other")
_SIDE_ORDER = ("long", "short")
_NOUL_ORDER = ("true", "false")
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)

_NEXT_CRITERIA = {
    "HOLD": "Hold this close on the tape.",
    "ABSTAIN": "Abstain this close.",
    "ESCALATE_CHAIR": "Escalate this close to the chair.",
    "BLOCKED": "This close is blocked.",
    "LABEL": "Label this close and leave it.",
    "RESEARCH": "Send this close to research.",
}
_ADMIT_CRITERIA = {
    "admit": "Named tape still supports admit.",
    "abstain": "Named state is thin or mixed.",
    "hard_refuse": "Named tape argues against the fire.",
}
_USAGE_CRITERIA = {
    "cheap_label": "A cheap label is enough for this close.",
    "chair_read": "This close needs a chair read.",
    "browser_scout": "This close needs a browser scout.",
    "deep_reason": "This close needs a deep reason.",
    "defer": "Defer this close.",
}
_DONE_CRITERIA = {
    "DONE": "This close walk is done.",
    "CONTINUE": "This close walk continues.",
    "BLOCKED": "This close walk is blocked.",
}
_QUEUE_CRITERIA = {
    "research": "Queue this close to research.",
    "write": "Queue this close to write.",
    "review": "Queue this close to review.",
    "none": "This close has no queue lane.",
}
_SCOPE_CRITERIA = {
    "audit_only": "The action scope is audit only.",
    "block_sibling_prefills": "The action scope blocks sibling prefills.",
}
_FAMILY_CRITERIA = {
    "spring": "Chair CF family spring.",
    "vss": "Chair CF family vss.",
    "sub": "Chair CF family sub.",
    "expand": "Chair CF family expand.",
    "other": "Some other named family.",
    "unknown": "The family is unnamed.",
}
_ALLOW_CRITERIA = {
    "allow": "This sleeve is allowed on the tape.",
    "shadow": "This sleeve stays in shadow.",
}
_SIZE_X_CRITERIA = {
    "SIZE_X_CONF_SHADOW": "Size times confidence wears the shadow label.",
    "size_x_conf_named": "Size times confidence wears the named label.",
}
_COST_CRITERIA = {
    "COST_FS": "The cost band is full size.",
    "cost_band_named": "The cost band is the named band.",
}
_EXIT_CRITERIA = {
    "tp": "The close exited at the target.",
    "orig_stop": "The close exited at the original stop.",
    "time_stop": "The close exited on a time stop.",
    "manual_other": "The close exited some other way.",
}
_REASON_CRITERIA = {
    "tp": "The close reason is the target.",
    "sl": "The close reason is the stop.",
    "time_stop": "The close reason is the time stop.",
    "other": "The close reason is some other reason.",
}
_SIDE_CRITERIA = {
    "long": "The unnamed side is long.",
    "short": "The unnamed side is short.",
}
_SESSION_CRITERIA = {
    "london": "London session.",
    "ny": "New York session.",
    "asia": "Asia session.",
    "asia_london_pre": "Asia into London pre session.",
    "off_hours": "Off hours.",
    "unnamed": "The session is unnamed.",
}
_DIRECTION_CRITERIA = {
    "trend_up": "The tape direction is up.",
    "unclear": "The tape direction is unclear.",
    "other": "The tape direction is some other direction.",
}
_RESIDUAL_CRITERIA = {
    "envelope_hard_off": "A hard-off marker is on this state. The marker list is a fact.",
    "state_insufficient": "The completeness fact says the state is not sufficient.",
    "last_refusal": "A named last refusal on this state is cost or other.",
    "injected": "An admit choice is present and the envelope is open.",
    "unanswered": "No admit choice is present and no hard-off marker applies.",
}
_G4_CRITERIA = {
    "APPLY_CUT_0_5": "G4 applies and this family is not keep. Label only.",
    "KEEP_EXEMPT": "Keep family while G4 applies.",
    "NOT_APPLICABLE": "G4 does not apply on this state.",
}
_G6_CRITERIA = {
    "APPLY_CUT_0_75": "A named London, New York, or Asia session, and not keep. Label only.",
    "KEEP_EXEMPT": "Keep family in a cut session.",
    "LEAVE_ALONE": "Asia into London pre, or off hours.",
    "NOT_APPLICABLE": "The session is unnamed or empty.",
}

_CHOICE_SPECS: tuple[tuple[str, str, Mapping[str, str]], ...] = (
    ("next_gate", "Which next gate does this close wear?", _NEXT_CRITERIA),
    ("admit", "Does this close admit, abstain, or hard-refuse?", _ADMIT_CRITERIA),
    ("usage_seat", "Which usage seat does this close wear?", _USAGE_CRITERIA),
    ("completion_advisory", "Is this close walk done, continuing, or blocked?", _DONE_CRITERIA),
    ("queue_lane", "Which queue lane does this close wear?", _QUEUE_CRITERIA),
    ("action_scope", "What action scope does this close wear?", _SCOPE_CRITERIA),
    ("sleeve_family", "Which CF family does this sleeve wear?", _FAMILY_CRITERIA),
    ("sleeve_allow", "Is this sleeve allowed or in shadow?", _ALLOW_CRITERIA),
    ("size_x_conf", "Which size-times-confidence label does this close wear?", _SIZE_X_CRITERIA),
    ("cost_band", "Which cost band does this close wear?", _COST_CRITERIA),
    ("exit_class", "Which exit class does this close wear?", _EXIT_CRITERIA),
    ("close_reason", "Which close reason does this close wear?", _REASON_CRITERIA),
    ("side", "When the tape names no side, is this close long or short?", _SIDE_CRITERIA),
    ("session", "Which session does this close wear?", _SESSION_CRITERIA),
    ("tape_direction", "Which tape direction does this close wear?", _DIRECTION_CRITERIA),
    ("admit_residual", "Which residual admit label does this close wear?", _RESIDUAL_CRITERIA),
    ("chair_soft_g4", "Which chair G4 soft label does this close wear?", _G4_CRITERIA),
    ("chair_soft_g6", "Which chair G6 soft label does this close wear?", _G6_CRITERIA),
)

_NOUL_SPECS: tuple[tuple[str, str, str, str], ...] = (
    (
        "evidence_enough",
        "Is the evidence on this close enough?",
        "The evidence on this close is enough.",
        "The evidence on this close is not enough.",
    ),
    (
        "corr_hold",
        "Does correlation hold on this close?",
        "Correlation holds on this close.",
        "Correlation does not hold on this close.",
    ),
    (
        "surface_ok",
        "Is the surface on this close ok?",
        "The surface on this close is ok.",
        "The surface on this close is not ok.",
    ),
    (
        "toxic_family",
        "Is this family toxic on this close?",
        "This family is toxic on this close.",
        "This family is not toxic on this close.",
    ),
    (
        "event_stamped",
        "Is this close event-stamped?",
        "This close is event-stamped.",
        "This close is not event-stamped.",
    ),
    (
        "shortlist_needed",
        "Does this close need a shortlist?",
        "This close needs a shortlist.",
        "This close does not need a shortlist.",
    ),
    (
        "state_sufficient",
        "Is this state sufficient for the close?",
        "This state is sufficient for the close.",
        "This state is not sufficient for the close.",
    ),
    (
        "speak_hold",
        "Does this close speak a hold?",
        "This close speaks a hold.",
        "This close does not speak a hold.",
    ),
    (
        "cf_d_keep",
        "Does CF D keep this close?",
        "CF D keeps this close.",
        "CF D does not keep this close.",
    ),
    (
        "remint_toxic",
        "Is remint toxic on this close?",
        "Remint is toxic on this close.",
        "Remint is not toxic on this close.",
    ),
    (
        "prefill_hold_would_help",
        "Would a prefill hold have helped this close?",
        "A prefill hold would have helped this close.",
        "A prefill hold would not have helped this close.",
    ),
    (
        "chair_soft_g8",
        "Does chair G8 block same-sleeve reentry on this close?",
        "Chair G8 blocks same-sleeve reentry on this close.",
        "Chair G8 does not block same-sleeve reentry on this close.",
    ),
    (
        "everywhere_present",
        "Does the everywhere-tape component exist for this close?",
        "The everywhere-tape component exists for this close.",
        "The everywhere-tape component does not exist for this close.",
    ),
)

_SCORE_SPECS: tuple[tuple[str, str], ...] = (
    ("urgency", "the urgency parameter"),
    ("sleeve_fit", "the sleeve-fit parameter"),
    ("geometry_quality", "the geometry-quality parameter"),
    ("size_label", "the size-label parameter"),
    ("hold_strength", "the hold-strength parameter"),
    ("lesson", "the lesson parameter"),
    ("cf_d_score", "the CF D parameter"),
    ("hold_hours", "the hold hours"),
    ("swap", "the swap parameter"),
    ("everywhere_threshold", "the threshold"),
    ("everywhere_loop", "the loop bound"),
    ("everywhere_parameter", "the everywhere-tape parameter"),
    ("tape_mark_1", "the first tape-direction parameter"),
    ("tape_mark_2", "the second tape-direction parameter"),
    ("tape_mark_3", "the third tape-direction parameter"),
    ("close_ret_1", "the one-bar close return parameter"),
    ("close_ret_5bar", "the five-bar close return parameter"),
    ("vol_ratio", "the volume-ratio parameter"),
    ("htf_slope_norm", "the higher-timeframe slope parameter"),
    ("mom_20_atr", "the twenty-bar momentum parameter"),
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
_SKIP_PARTS = ("floor", "baseline")
_UNSET = (
    "An empty answer or a tie leaves it unset. This question does not send."
)

# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []
_DROP = object()



def _card_var():
    var = globals().get("_OBSERVE_CARD")
    if var is None:
        import contextvars

        var = contextvars.ContextVar("observe_card_" + __name__, default=None)
        globals()["_OBSERVE_CARD"] = var
    return var


def _bind_card(state):
    """The card whose facts may anchor an amount. A miss binds nothing."""

    try:
        from collections.abc import Mapping
    except Exception:
        return None
    card = state if isinstance(state, Mapping) else None
    return _card_var().set(card)


def _bound_card():
    try:
        return _card_var().get()
    except Exception:
        return None


_ORDINAL_WIDTH: dict[str, int] = {}
_AMOUNT_UNIT: dict[str, str] = {}
_ORDINAL_WORDS = ("none", "trace", "small", "modest", "notable", "heavy")
_PRICE_KEYS = {
    "entry",
    "stop",
    "target",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
    "open",
    "high",
    "low",
    "close",
    "limit_price",
}
_MONEY_KEYS = {
    "equity",
    "balance",
    "open_pnl",
    "profit",
    "day_start_balance",
    "day_start_equity",
    "realized_closed_profit",
    "day_equity",
    "broker_net",
    "mean_net",
    "realized",
}
_SKIP_WALK = {
    "prior_outcomes",
    "questions",
    "answers",
    "probabilities",
    "criteria",
    "instructions",
}


def _anchor_finite(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    banned = globals().get("_banned_number")
    if callable(banned):
        try:
            if banned(number):
                return None
        except Exception:
            return None
    return number


def _label_ok(text: str) -> bool:
    if not text or not str(text).strip():
        return False
    sample = str(text)
    for name, bad in (
        ("_limit_key", True),
        ("_banned_text", True),
        ("_blocked_text", True),
        ("_text_banned", True),
        ("_skip_key", True),
    ):
        fn = globals().get(name)
        if not callable(fn):
            continue
        try:
            if bool(fn(sample)) is bad:
                return False
        except Exception:
            return False
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            if scrub(sample) is None:
                return False
        except Exception:
            return False
    ok = globals().get("_question_text_ok")
    if callable(ok):
        try:
            if not ok(sample):
                return False
        except Exception:
            return False
    return True


def _amount_unit(qid: str, text: str = "") -> str | None:
    """The unit this score returns. None means the score is an ordinal."""

    name = str(qid).lower()
    if name.endswith("_hour") or name.endswith("_hours"):
        return "hours"
    if "minute" in name and not name.endswith("_parameter"):
        return "minutes"
    tokens = name.replace(".", "_").split("_")
    if (
        "lot" in tokens
        or "lots" in tokens
        or name.endswith("_lot")
        or name.endswith("_lots")
        or name.endswith("min_lot")
    ):
        return "lots"
    if "persist" in name or name.endswith("_weight"):
        return "weight"
    if "ceiling" in name:
        return "size"
    if "concurrent" in name:
        return "count"
    if name.endswith("_net") or "broker_net" in name:
        return "money"
    if (
        "prob" in name
        or ".p_" in name
        or "p_time" in name
        or "p_positive" in name
    ):
        return "probability"
    if (
        "plan_r" in name
        or "mean_r" in name
        or name.endswith("_r")
        or "predicted_e_r" in name
    ):
        return "r"
    if "fitness" in name or name.endswith("_fit"):
        return None
    if "expected_" in name:
        return "count"
    tail = name.rsplit(".", 1)[-1]
    tail_tokens = tail.split("_")
    if (
        tail.endswith("_loop")
        or tail.endswith("_loop_bound")
        or tail == "loop"
        or "retry" in tail_tokens
        or "walk_depth" in tail
        or "posts" in tail_tokens
        or "min_n" in tail
        or tail.endswith("_count")
        or tail.endswith("_n")
    ):
        return "count"
    if "window" in name:
        return "window"
    if "threshold" in name:
        return "price"
    blob = name + "\n" + str(text).lower()
    if "stop or target" in blob or "the stop" in blob or "the target" in blob:
        return "price"
    if "e[r]" in blob or "mean r" in blob:
        return "r"
    if "broker net" in blob:
        return "money"
    if "the lot " in blob or blob.rstrip(".").endswith("the lot"):
        return "lots"
    if "fluid count" in blob or "envelope count" in blob or "promotion count" in blob:
        return "count"
    if "how many" in blob:
        return "count"
    if name.startswith("a1_") and name.endswith("_parameter"):
        return "price"
    return None


def _is_ordinal(qid: str) -> bool:
    """True when this id was built as words, or no amount unit is known."""

    key = str(qid)
    if key in _AMOUNT_UNIT:
        return False
    if key in _ORDINAL_WIDTH:
        return True
    return _amount_unit(key, "") is None


def _key_unit(name: str, unit: str) -> bool:
    low = str(name).lower()
    if unit == "price":
        return low in _PRICE_KEYS
    if unit == "hours":
        return low == "hour" or low.endswith("_hour") or low.endswith("_hours")
    if unit == "minutes":
        return low == "minute" or low.endswith("_minute") or low.endswith("_minutes") or low.endswith("_min")
    if unit == "seconds":
        return "second" in low or low in {"age_s", "seconds_until_cycle"}
    if unit == "lots":
        return low in {"volume", "volume_min", "volume_step", "lot", "lots", "min_lot"} or low.endswith("_lot") or low.endswith("_lots")
    if unit == "r":
        return low.endswith("_r") or low in {"plan_r", "locked_r", "mean_r"}
    if unit == "weight":
        return low == "weight" or low.endswith("_weight")
    if unit == "money":
        return low in _MONEY_KEYS
    if unit == "probability":
        return "prob" in low or low.startswith("p_") or "p_time" in low or "p_positive" in low
    if unit == "count":
        return low in {"n", "asked", "step_index"} or low.startswith("n_") or low.endswith("_count") or low.endswith("_len") or low.endswith("_posts")
    if unit == "multiple":
        return low.endswith("_mult") or low.endswith("_multiple")
    return False


def _walk_pairs(state, unit: str) -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []

    def walk(blob, depth: int) -> None:
        if depth > 4 or not isinstance(blob, dict):
            return
        for key, value in blob.items():
            name = str(key)
            if name in _SKIP_WALK or name.startswith("_"):
                continue
            if not _label_ok(name):
                continue
            if isinstance(value, dict):
                walk(value, depth + 1)
                continue
            if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
                if unit == "count":
                    found.append((f"the count of {name} named on this card", float(len(value))))
                continue
            if unit == "count" and not _key_unit(name, unit):
                continue
            if unit != "count" and not _key_unit(name, unit):
                continue
            number = _anchor_finite(value)
            if number is None:
                continue
            found.append((f"the {name} named on this card", number))

    if isinstance(state, dict):
        walk(state, 0)
    return found


def _distinct(pairs) -> int:
    seen = []
    for _label, value in pairs:
        if value not in seen:
            seen.append(value)
    return len(seen)


def _anchors_for(state, unit: str) -> list[tuple[str, float]]:
    card = state if isinstance(state, dict) else {}
    if unit == "count":
        extra = []
        try:
            from .jev_questions import count_anchors

            extra = list(count_anchors(card) or [])
        except Exception:
            try:
                from src.judgment.jev_questions import count_anchors

                extra = list(count_anchors(card) or [])
            except Exception:
                extra = []
        return list(extra) + _walk_pairs(card, "count")
    if unit == "money":
        extra = []
        try:
            from .jev_questions import usd_anchors

            extra = list(usd_anchors(card) or [])
        except Exception:
            try:
                from src.judgment.jev_questions import usd_anchors

                extra = list(usd_anchors(card) or [])
            except Exception:
                extra = []
        return list(extra) + _walk_pairs(card, "money")
    if unit == "minutes":
        extra = []
        try:
            from .jev_questions import minute_anchors

            extra = list(minute_anchors(card) or [])
        except Exception:
            try:
                from src.judgment.jev_questions import minute_anchors

                extra = list(minute_anchors(card) or [])
            except Exception:
                extra = []
        return list(extra) + _walk_pairs(card, "minutes")
    if unit == "size":
        lots = _walk_pairs(card, "lots")
        multiples = _walk_pairs(card, "multiple")
        try:
            from .jev_questions import mult_anchors

            multiples = list(mult_anchors(card) or []) + multiples
        except Exception:
            try:
                from src.judgment.jev_questions import mult_anchors

                multiples = list(mult_anchors(card) or []) + multiples
            except Exception:
                pass
        if _distinct(lots) >= 2:
            return lots
        if _distinct(multiples) >= 2:
            return multiples
        return []
    if unit == "window":
        minutes = _walk_pairs(card, "minutes")
        seconds = _walk_pairs(card, "seconds")
        if _distinct(minutes) >= 2:
            return minutes
        return seconds
    return _walk_pairs(card, unit)


def _custom_words(words) -> bool:
    """A scale of words is an ordinal. The generic parameter menu is not."""

    if not words:
        return False
    texts = []
    numeric = 0
    for item in words:
        text = str(item).strip()
        if not text:
            continue
        try:
            float(text)
            numeric += 1
        except (TypeError, ValueError):
            pass
        texts.append(text)
    if len(texts) < 2 or numeric == len(texts):
        return False
    generic = {
        ("none", "trace", "small", "modest", "notable", "heavy"),
        (
            "below the levels on this state",
            "between the levels on this state",
            "above the levels on this state",
        ),
    }
    return tuple(texts) not in generic


def _word_levels(words) -> list[str]:
    if not words:
        return list(_ORDINAL_WORDS)
    texts = []
    numeric = 0
    for item in words:
        text = str(item).strip()
        if not text:
            continue
        try:
            float(text)
            numeric += 1
        except (TypeError, ValueError):
            pass
        texts.append(text)
    if texts and numeric == len(texts):
        return [item for item in _ORDINAL_WORDS if _label_ok(item)]
    kept = [item for item in texts if _label_ok(item)]
    if len(kept) >= 2:
        return kept
    return [item for item in _ORDINAL_WORDS if _label_ok(item)]


def _jev_amount(qid, text, anchors):
    try:
        from .jev_questions import amount_question

        return amount_question(qid, text, anchors)
    except Exception:
        from src.judgment.jev_questions import amount_question

        return amount_question(qid, text, anchors)


def _jev_ordinal(qid, text, levels):
    try:
        from .jev_questions import ordinal_question

        return ordinal_question(qid, text, levels)
    except Exception:
        from src.judgment.jev_questions import ordinal_question

        return ordinal_question(qid, text, levels)


def _shape_score(qid: str, instructions: str, words=None, *, wrapped: bool = True):
    """An amount posts only with two anchors. An ordinal keeps its words."""

    text = str(instructions or "").strip()
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            cleaned = scrub(text)
        except Exception:
            return {}
        if not isinstance(cleaned, str) or not cleaned.strip():
            return {}
        text = cleaned.strip()
    if not text or not _label_ok(text):
        return {}
    unit = None if _custom_words(words) else _amount_unit(qid, text)
    try:
        if unit is None:
            built = _jev_ordinal(qid, text, _word_levels(words))
        else:
            anchors = [
                (label, value)
                for label, value in _anchors_for(_bound_card(), unit)
                if _label_ok(label)
            ]
            built = _jev_amount(qid, text, anchors)
    except Exception:
        return {}
    row = built.get(str(qid)) if isinstance(built, dict) else None
    if not isinstance(row, dict):
        return {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        row.pop(key, None)
    criteria = row.get("criteria")
    if not isinstance(criteria, list) or len(criteria) < 2:
        return {}
    if unit is None:
        _ORDINAL_WIDTH[str(qid)] = len(criteria)
        _AMOUNT_UNIT.pop(str(qid), None)
    else:
        _AMOUNT_UNIT[str(qid)] = unit
        _ORDINAL_WIDTH.pop(str(qid), None)
    row["type"] = "score"
    row["instructions"] = text
    if wrapped:
        return {str(qid): row}
    return row


def _ordinal_read(block, qid: str):
    """Nearest word. The index is not an amount. A miss stays unset."""

    width = _ORDINAL_WIDTH.get(str(qid))
    if not isinstance(width, int) or width < 2:
        criteria = block.get("criteria") if isinstance(block, dict) else None
        if isinstance(criteria, list) and len(criteria) >= 2:
            width = len(criteria)
        else:
            probs = block.get("probabilities") if isinstance(block, dict) else None
            if isinstance(probs, dict) and len(probs) >= 2:
                width = len(probs)
    if not isinstance(width, int) or width < 2:
        return None
    try:
        from .jev_questions import ordinal_index
    except Exception:
        try:
            from src.judgment.jev_questions import ordinal_index
        except Exception:
            return None
    try:
        return ordinal_index(block, width)
    except Exception:
        return None

def _limit_key(name: str) -> bool:
    token = str(name).strip().lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED_TEXT)


def _scrub_text(value: str) -> str | None:
    if _banned_text(value) or any(part in value.lower() for part in _SKIP_PARTS):
        return None
    return value


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before the ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name) or name in {"system_one_answers", "everywhere_answers"}:
                continue
            cleaned = _scrub(item)
            if cleaned is _DROP:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        kept = []
        for item in value:
            cleaned = _scrub(item)
            if cleaned is not _DROP:
                kept.append(cleaned)
        return kept
    if isinstance(value, str):
        cleaned = _scrub_text(value)
        if cleaned is None:
            return _DROP
        return cleaned
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if _banned_text(format(value, ".10g")):
            return _DROP
        return value
    return str(value)


def _number(value: Any) -> float | None:
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
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        number = _number(val)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision. A miss is not zero."""

    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if probabilities[name] == best]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
    """The choice is the unique highest probability. A bare label is not a choice."""

    if not order or not isinstance(block, dict) or block.get("error"):
        return None, {}
    probabilities = _probabilities(block)
    kept = {name: probabilities[name] for name in order if name in probabilities}
    local = _unique(kept, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(kept or None, order)
    except Exception:
        picked = local
    if local is None or picked is None or str(picked) != local or str(picked) not in order:
        return None, kept
    return str(picked), kept


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if block is True or block is False:
        return block
    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        value = block.get("noul") if "noul" in block else block.get("Noul")
        if value is None:
            return None
        if value is True or value is False:
            return value
        return _number(value)
    picked, _kept = _choice(block, _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any, qid: str | None = None) -> float | None:
    """The parameter is the returned score. A missing score stays missing."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))


    if not isinstance(block, dict) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _number(returned_number(block))
    except Exception:
        raw = block.get("score")
        if raw is None:
            raw = block.get("value")
        return _number(raw)


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions) or ""
    cleaned = {
        str(key): str(val)
        for key, val in criteria.items()
        if _scrub_text(str(key)) is not None and _scrub_text(str(val)) is not None
    }
    if len(cleaned) < 2:
        return {}
    block: dict[str, Any] = {}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, cleaned)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        block = {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    block["type"] = "choice"
    block["instructions"] = text
    block["criteria"] = cleaned
    return {qid: block}


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    """Amount anchors from this card. An ordinal keeps its words."""
    return _shape_score(qid, instructions, None, wrapped=True)



def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    yes_text = _scrub_text(yes)
    no_text = _scrub_text(no)
    text = _scrub_text(instructions)
    if yes_text is None or no_text is None or text is None:
        return {}
    return {
        qid: {
            "type": "noul",
            "instructions": text,
            "criteria": {"true": yes_text, "false": no_text},
        }
    }


def _cf_d_order() -> tuple[str, ...]:
    """CF D option ids, when that menu can be imported. The menu is not the pick.

    A missing menu leaves the choice unset. Exit classes are not substituted.
    """

    try:
        from .cf_d import CHOICE_IDS
    except Exception:
        return ()
    names: list[str] = []
    for item in CHOICE_IDS:
        token = str(item).strip()
        if token and _scrub_text(token) is not None and not _limit_key(token):
            names.append(token)
    if len(names) >= 2:
        return tuple(names)
    return ()


def _questions() -> tuple[dict[str, Any], dict[str, tuple[str, ...]]]:
    """One pack. Types are noul, choice, or score."""

    orders: dict[str, tuple[str, ...]] = {}
    pack: dict[str, Any] = {}
    for qid, text, criteria in _CHOICE_SPECS:
        built = _choice_question(
            qid,
            f"{text} The option with the single highest probability is the decision. {_UNSET}",
            criteria,
        )
        block = built.get(qid)
        if isinstance(block, dict) and isinstance(block.get("criteria"), dict):
            orders[qid] = tuple(str(key) for key in block["criteria"])
            pack.update(built)
        else:
            orders[qid] = ()
    cf_order = _cf_d_order()
    cf_criteria = {name: f"{name} is the CF D choice on this tape." for name in cf_order}
    built = _choice_question(
        "cf_d_choice",
        f"Which CF D choice does this close wear? The option with the single highest probability is the decision. {_UNSET}",
        cf_criteria,
    )
    block = built.get("cf_d_choice")
    if isinstance(block, dict) and isinstance(block.get("criteria"), dict):
        orders["cf_d_choice"] = tuple(str(key) for key in block["criteria"])
        pack.update(built)
    else:
        orders["cf_d_choice"] = ()
    for qid, text, yes, no in _NOUL_SPECS:
        built = _noul_question(
            qid,
            f"{text} The noul you return is that answer. An empty noul leaves it unset. This question does not send.",
            yes,
            no,
        )
        if built:
            orders[qid] = _NOUL_ORDER
            pack.update(built)
        else:
            orders[qid] = ()
    for qid, noun in _SCORE_SPECS:
        built = _score_question(
            qid,
            (
                f"The score you return is {noun} for this close. "
                "It may sit between the levels on this state. "
                "An empty score leaves it unset. "
                "This question does not send."
            ),
        )
        if built:
            pack.update(built)
    return pack, orders


def _pack_ok(questions: Mapping[str, Any]) -> bool:
    allowed = {"noul", "choice", "score"}
    if not questions:
        return False
    for qid, block in questions.items():
        if _limit_key(str(qid)):
            return False
        if not isinstance(block, dict) or str(block.get("type") or "") not in allowed:
            return False
        try:
            text = json.dumps(block, default=str).lower()
        except Exception:
            return False
        if any(part in text for part in _SKIP_PARTS) or _banned_text(text):
            return False
    return True


def _side_fact(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if text in {"buy", "long"}:
        return "long"
    if text in {"sell", "short"}:
        return "short"
    return None


def _gold(row: Mapping[str, Any]) -> dict[str, Any]:
    raw = row.get("gold_state")
    if not isinstance(raw, Mapping):
        return {}
    return {str(key): item for key, item in raw.items()}


def _identity(row: Mapping[str, Any]) -> dict[str, Any]:
    ident = _gold(row).get("identity")
    if not isinstance(ident, Mapping):
        return {}
    return {str(key): item for key, item in ident.items()}


def _ticket(row: Mapping[str, Any]) -> str | None:
    raw = row.get("ticket")
    if raw in (None, ""):
        raw = _identity(row).get("ticket")
    if raw in (None, ""):
        return None
    return str(raw)


def _symbol(row: Mapping[str, Any]) -> str | None:
    raw = _identity(row).get("symbol")
    if raw in (None, ""):
        raw = row.get("symbol")
    if raw in (None, ""):
        return None
    return str(raw)


def _subclass_fact(row: Mapping[str, Any]) -> str | None:
    raw = row.get("subclass")
    if raw in (None, ""):
        raw = _identity(row).get("s15_subclass")
    if raw in (None, ""):
        return None
    return str(raw)


def _flag(value: Any) -> bool | None:
    if value is True or value is False:
        return value
    return None


def _state(row: Mapping[str, Any]) -> dict[str, Any]:
    ident = _identity(row)
    gold = _scrub(_gold(row))
    if not isinstance(gold, dict):
        gold = {}
    login = row.get("login")
    if login in (None, ""):
        login = CHALLENGE_LOGIN
    body: dict[str, Any] = {
        "model": MODEL,
        "login": login,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "tape_id": row.get("tape_id"),
        "ticket": _ticket(row),
        "subclass": _subclass_fact(row),
        "subclass_menu": list(TAPE_SUBCLASSES),
        "hard_markers": list(HARD_MARKERS),
        "note": row.get("note"),
        "g4_applies": _flag(row.get("g4_applies")),
        "symbol": _symbol(row),
        "side": _side_fact(ident.get("side") if ident.get("side") not in (None, "") else row.get("side")),
        "sleeve": None if ident.get("sleeve") in (None, "") else str(ident.get("sleeve")),
        "cf_d_exit": None if ident.get("cf_d_exit") in (None, "") else str(ident.get("cf_d_exit")),
        "gold_state": gold,
        "identity": {
            "login": login,
            "ns": CHALLENGE_NS,
            "magic": CHALLENGE_MAGIC,
            "ticket": _ticket(row),
            "symbol": _symbol(row),
            "sleeve": None if ident.get("sleeve") in (None, "") else str(ident.get("sleeve")),
        },
    }
    cleaned = _scrub(body)
    state = cleaned if isinstance(cleaned, dict) else {}
    state["model"] = MODEL
    state["login"] = login
    state["ns"] = CHALLENGE_NS
    state["magic"] = CHALLENGE_MAGIC
    return state


def _local_priors() -> list[dict[str, Any]]:
    return [dict(item) for item in _LOCAL_OUTCOMES]


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = _local_priors()
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _field_ids(orders: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
    choice_ids = tuple(qid for qid, _text, _criteria in _CHOICE_SPECS) + ("cf_d_choice",)
    noul_ids = tuple(qid for qid, _text, _yes, _no in _NOUL_SPECS)
    score_ids = tuple(qid for qid, _noun in _SCORE_SPECS)
    del orders
    return choice_ids + noul_ids + score_ids


def _remember(state: Mapping[str, Any], row: Mapping[str, Any], orders: Mapping[str, tuple[str, ...]]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    error = row.get("error")
    err = None if error in (None, "") else str(error)
    pairs = tuple((qid, row.get(qid)) for qid in _field_ids(orders))
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value in pairs:
            _LOCAL_OUTCOMES.append({
                "spot": key,
                "value": value,
                "error": None if value is not None else err,
            })
        return
    for key, value in pairs:
        try:
            append_outcome(key, value, logged, error=None if value is not None else err)
        except Exception:
            _LOCAL_OUTCOMES.append({
                "spot": key,
                "value": value,
                "error": None if value is not None else err,
            })


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    call = evaluate_fn
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    receipt = call(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    return receipt if isinstance(receipt, dict) else {"error": "evaluate_not_a_dict", "answers": {}}


def _stamp(row: dict[str, Any]) -> dict[str, Any]:
    """Identity and the closed send mark. These are the module, not an answer."""

    row["model"] = row.get("model") or MODEL
    row["api_url"] = API_URL
    row["login"] = row.get("login") if row.get("login") not in (None, "") else CHALLENGE_LOGIN
    row["ns"] = CHALLENGE_NS
    row["magic"] = CHALLENGE_MAGIC
    row["place"] = False
    row["never_broker_send"] = True
    row["broker_effect"] = False
    return row


def _blank(error: str | None, orders: Mapping[str, tuple[str, ...]]) -> dict[str, Any]:
    row: dict[str, Any] = {qid: None for qid in _field_ids(orders)}
    row["probabilities"] = {}
    row["error"] = error
    row["model"] = MODEL
    return _stamp(row)


def _read(
    answers: Mapping[str, Any],
    error: str | None,
    orders: Mapping[str, tuple[str, ...]],
) -> dict[str, Any]:
    row: dict[str, Any] = {}
    probabilities: dict[str, dict[str, float]] = {}
    for qid, _text, _criteria in _CHOICE_SPECS:
        picked, probs = _choice(answers.get(qid), orders.get(qid) or ())
        row[qid] = picked
        if probs:
            probabilities[qid] = probs
    picked, probs = _choice(answers.get("cf_d_choice"), orders.get("cf_d_choice") or ())
    row["cf_d_choice"] = picked
    if probs:
        probabilities["cf_d_choice"] = probs
    for qid, _text, _yes, _no in _NOUL_SPECS:
        row[qid] = _noul(answers.get(qid))
    for qid, _noun in _SCORE_SPECS:
        row[qid] = _score(answers.get(qid), qid)
    row["probabilities"] = probabilities
    row["error"] = error
    row["model"] = MODEL
    return _stamp(row)


def _echo(row: dict[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    row["ticket"] = state.get("ticket")
    row["subclass"] = state.get("subclass")
    row["symbol"] = state.get("symbol")
    row["sleeve"] = state.get("sleeve")
    row["side_fact"] = state.get("side")
    row["g4_applies"] = state.get("g4_applies")
    if state.get("login") not in (None, ""):
        row["login"] = state.get("login")
    return row


def inject_everywhere_answers(
    row: Mapping[str, Any] | None = None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """The System One return for this tape row. A miss leaves the field unset.

    Does not send.
    """

    state = _state(row if isinstance(row, Mapping) else {})
    try:
        questions, orders = _questions()
    except Exception as exc:
        card = _blank(type(exc).__name__, {})
        _remember(state, card, {})
        return _echo(card, state)
    if not _pack_ok(questions):
        card = _blank("question_rejected", orders)
        _remember(state, card, orders)
        return _echo(card, state)
    _attach_priors(state, questions)
    try:
        receipt = _post(state, questions, evaluate_fn)
    except Exception as exc:
        card = _blank(type(exc).__name__, orders)
        _remember(state, card, orders)
        return _echo(card, state)
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    if not answers:
        card = _blank(None if error in (None, "") else str(error), orders)
    else:
        card = _read(answers, None if error in (None, "") else str(error), orders)
    if receipt.get("model"):
        card["model"] = receipt.get("model")
    _remember(state, card, orders)
    return _echo(card, state)


def close_state_from_row(
    row: Mapping[str, Any] | None,
    *,
    answers: Mapping[str, Any] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any] | None:
    """Close card for this ticket. Exit, reason, hours, and swap are the return."""

    source = row if isinstance(row, Mapping) else {}
    ticket = _ticket(source)
    if ticket is None:
        return None
    decided = answers if isinstance(answers, Mapping) else inject_everywhere_answers(source, evaluate_fn=evaluate_fn)
    exit_class = decided.get("exit_class")
    if exit_class not in _EXIT_ORDER:
        exit_class = None
    close_reason = decided.get("close_reason")
    if close_reason not in _REASON_ORDER:
        close_reason = None
    side = _side_fact(_identity(source).get("side"))
    if side is None:
        side = _side_fact(source.get("side"))
    if side is None and decided.get("side") in _SIDE_ORDER:
        side = str(decided.get("side"))
    return {
        "schema": SCHEMA,
        "close": {
            "ticket": ticket,
            "symbol": _symbol(source),
            "side": side,
            "exit_class_raw": exit_class,
            "close_reason_raw": close_reason,
            "subclass": _subclass_fact(source),
            "hold_hours": _number(decided.get("hold_hours")),
            "swap": _number(decided.get("swap")),
        },
        "deals": [{"deal_id": ticket, "entry": "out"}],
    }


def _cf_priority_identity_rows() -> list[dict[str, Any]]:
    """Chair CF study identities. The sleeve and the ticket are facts."""

    extra: list[dict[str, Any]] = []

    def add(*, tape_id: str, ticket: str, sleeve: str, symbol: str, side: str, note: str) -> None:
        cid = f"challenge:{CHALLENGE_LOGIN}:{ticket}:{sleeve}:{side}"
        extra.append(
            {
                "tape_id": tape_id,
                "login": CHALLENGE_LOGIN,
                "ticket": ticket,
                "subclass": None,
                "g4_applies": None,
                "note": note,
                "gold_state": {
                    "identity": {
                        "sleeve": sleeve,
                        "symbol": symbol,
                        "side": side,
                        "candidate_id": cid,
                        "ticket": ticket,
                        "login": CHALLENGE_LOGIN,
                        "ns": CHALLENGE_NS,
                    }
                },
            }
        )

    add(
        tape_id="cf-expand-01",
        ticket="cfexp01",
        sleeve="dsp_expand_range",
        symbol="XAUUSD",
        side="long",
        note="chair_cf_priority_sleeve_family_expand",
    )
    add(
        tape_id="cf-wide-01",
        ticket="cfwide01",
        sleeve="dsp_wide_london",
        symbol="XAUUSD",
        side="short",
        note="chair_cf_contrast_dsp_wide_not_allow",
    )
    return extra


def _load_rows(loader: Callable[[], Any]) -> list[dict[str, Any]]:
    try:
        loaded = loader()
    except Exception:
        return []
    if not isinstance(loaded, (list, tuple)):
        return []
    return [dict(item) for item in loaded if isinstance(item, Mapping)]


def _s15_rows() -> list[dict[str, Any]]:
    def load() -> Any:
        from .s15_tape import s15_historical_tape_rows

        return s15_historical_tape_rows()

    return _load_rows(load)


def _bank_rows() -> list[dict[str, Any]]:
    def load() -> Any:
        from .cf_d import question_bank_rows

        return question_bank_rows()

    return _load_rows(load)


def _ticket_subclass(ticket: str) -> str | None:
    """Historical subclass label, when that table can be imported. Not a verdict."""

    try:
        from .conf_gate import TICKET_SUBCLASS
    except Exception:
        return None
    if not isinstance(TICKET_SUBCLASS, Mapping):
        return None
    raw = TICKET_SUBCLASS.get(str(ticket))
    if raw in (None, ""):
        return None
    return str(raw)


def everywhere_historical_close_rows(
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> list[dict[str, Any]]:
    """S15 rows, CF study identities, and the CF D bank. One ask per row."""

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in _s15_rows() + _cf_priority_identity_rows() + _bank_rows():
        ticket = raw.get("ticket")
        if not ticket or str(ticket) in seen:
            continue
        seen.add(str(ticket))
        subclass = raw.get("subclass") or _ticket_subclass(str(ticket))
        gold = dict(raw.get("gold_state") or {})
        ident = dict(gold.get("identity") or {})
        ident["ticket"] = str(ticket)
        if subclass:
            ident["s15_subclass"] = subclass
        g4 = raw.get("g4_applies") if isinstance(raw.get("g4_applies"), bool) else None
        if g4 is not None:
            ident["g4_applies"] = g4
        gold["identity"] = ident
        packed = {**raw, "subclass": subclass, "gold_state": gold, "ticket": str(ticket), "g4_applies": g4}
        decided = inject_everywhere_answers(packed, evaluate_fn=evaluate_fn)
        login = raw.get("login")
        if login in (None, ""):
            login = CHALLENGE_LOGIN
        rows.append(
            {
                "tape_id": raw.get("tape_id"),
                "login": login,
                "ticket": str(ticket),
                "subclass": subclass,
                "g4_applies": g4,
                "note": raw.get("note"),
                "gold_state": gold,
                "close_state": close_state_from_row(packed, answers=decided),
                "everywhere_answers": decided,
            }
        )
    return rows
