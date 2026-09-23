"""Spot-exact admission Choices for Challenge 0.

Each spot is one condition. The two criteria are the two sides of that
condition. The unique highest probability is the decision. An empty map
or a tie is not a decision, and this module does not put the old boolean
back. It does not label an unanswered hop.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Mapping

from .jev_questions import spot_question, unique_highest

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
MODEL = "jev-1.13.0"
_CACHE: dict[str, tuple[bool, str | None]] = {}
_PACK: dict[str, dict[str, Any]] = {}
last: dict[str, Any] = {}


def on_challenge() -> bool:
    """The live Challenge writer, or an explicit Challenge namespace."""
    ns = str(
        os.environ.get("GTOS_NAMESPACE") or os.environ.get("GTOS_BOOK_NAMESPACE") or ""
    ).strip()
    if ns == CHALLENGE_NS:
        return True
    argv = " ".join(sys.argv).replace("\\", "/").lower()
    return CHALLENGE_NS in argv and "run_book" in argv


# withhold is the side that used to be the true branch of the if.
SPOTS: dict[str, dict[str, Any]] = {
    "circuit_breaker_open": {
        "withhold": "circuit_open",
        "order": ("circuit_open", "circuit_is_a_switch"),
        "criteria": {
            "circuit_open": "The operator circuit breaker is open. Do not admit a new entry.",
            "circuit_is_a_switch": "The breaker is a switch fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: the operator circuit breaker reads open. "
            "Pick one option. Block a new entry only when circuit_open has the "
            "single highest probability."
        ),
    },
    "nan_state": {
        "withhold": "state_unreadable",
        "order": ("state_unreadable", "state_is_a_reading"),
        "criteria": {
            "state_unreadable": "Equity state is not a readable number. Do not admit a new entry.",
            "state_is_a_reading": "The reading is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: an equity, high-water, day, or open-risk reading is missing or not a number. "
            "Pick one option. Block only when state_unreadable is the single highest. "
        ),
    },
    "nonpositive_equity": {
        "withhold": "equity_not_positive",
        "order": ("equity_not_positive", "equity_is_a_fact"),
        "criteria": {
            "equity_not_positive": "Equity or high water is not positive. Do not admit a new entry.",
            "equity_is_a_fact": "The equity number is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: equity or high water is at or under zero. "
            "Pick one option. Block only when equity_not_positive is the single highest. "
        ),
    },
    "high_water_below_equity": {
        "withhold": "high_water_below",
        "order": ("high_water_below", "high_water_is_a_fact"),
        "criteria": {
            "high_water_below": "High water sits under equity. Do not admit a new entry.",
            "high_water_is_a_fact": "High water is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: recorded high water is below equity. "
            "Pick one option. Block only when high_water_below is the single highest. "
        ),
    },
    "negative_open_risk": {
        "withhold": "open_risk_negative",
        "order": ("open_risk_negative", "open_risk_is_a_fact"),
        "criteria": {
            "open_risk_negative": "Open risk prints negative. Do not admit a new entry.",
            "open_risk_is_a_fact": "Open risk is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: open risk percent is negative. "
            "Pick one option. Block only when open_risk_negative is the single highest. "
        ),
    },
    "soft_daily_stop": {
        "withhold": "soft_stop_reached",
        "order": ("soft_stop_reached", "day_pnl_is_a_fact"),
        "criteria": {
            "soft_stop_reached": "The soft daily stop is reached. Do not admit a new entry.",
            "day_pnl_is_a_fact": "Today's result is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: realized today is at or under the soft daily stop. "
            "Pick one option. Block only when soft_stop_reached is the single highest. "
        ),
    },
    "max_dd_limit": {
        "withhold": "max_dd_reached",
        "order": ("max_dd_reached", "drawdown_is_a_fact"),
        "criteria": {
            "max_dd_reached": "Drawdown is at the max-DD limit. Do not admit a new entry.",
            "drawdown_is_a_fact": "Drawdown is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: drawdown from the static reference is at the max-DD limit. "
            "Pick one option. Block only when max_dd_reached is the single highest. "
        ),
    },
    "max_dd_entry_buffer": {
        "withhold": "entry_buffer_reached",
        "order": ("entry_buffer_reached", "buffer_is_a_fact"),
        "criteria": {
            "entry_buffer_reached": "Drawdown is inside the entry buffer. Do not admit a new entry.",
            "buffer_is_a_fact": "The buffer reading is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: drawdown has reached the max-DD entry buffer. "
            "Pick one option. Block only when entry_buffer_reached is the single highest. "
        ),
    },
    "how_many_more": {
        "withhold": "count_caps",
        "order": ("count_caps", "another_can_send"),
        "criteria": {
            "count_caps": "The open risk on this state caps another ticket.",
            "another_can_send": "The open risk is a fact. Another ticket can still be sent.",
        },
        "instructions": (
            "How many more tickets can be sent is this choice. "
            "The fractions on this state are facts, not a cap. "
            "Pick one option. Cap another ticket only when count_caps is the single highest. "
            "An empty answer, a tie, or an error does not cap and does not mean zero more. "
        ),
    },
    "gross_risk_cap": {
        "withhold": "cap_exhausted",
        "order": ("cap_exhausted", "headroom_is_a_fact"),
        "criteria": {
            "cap_exhausted": "Gross open-risk headroom is exhausted. Do not admit a new entry.",
            "headroom_is_a_fact": "Headroom is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: remaining gross open-risk headroom is at or under zero. "
            "Pick one option. Block only when cap_exhausted is the single highest. "
        ),
    },
    "profit_target_protect": {
        "withhold": "protect_derisk",
        "order": ("protect_derisk", "gain_is_a_fact"),
        "criteria": {
            "protect_derisk": "The profit-target protect shrink applies to this new entry.",
            "gain_is_a_fact": "The gain versus the reference is a fact. Do not shrink for that reason.",
        },
        "instructions": (
            "Admission question: equity gain versus the static reference is at the profit-target protect. "
            "Pick one option. Shrink the new entry only when protect_derisk is the single highest. "
        ),
    },
    "governor": {
        "withhold": "block_new_entries",
        "order": ("block_new_entries", "governor_is_a_fact"),
        "criteria": {
            "block_new_entries": "New entries stay off.",
            "governor_is_a_fact": "The governor reading is a fact. New entries can still be admitted.",
        },
        "instructions": (
            "Governor question: the two sides of allow_new_entries being false. "
            "Pick one option. Block new entries only when block_new_entries is the "
            "single highest probability. An empty answer or a tie does not restore "
            "the boolean."
        ),
    },
    "derisk": {
        "withhold": "shrink_into_wall",
        "order": ("shrink_into_wall", "full_size"),
        "criteria": {
            "shrink_into_wall": "Shrink new-entry size into the max-DD wall.",
            "full_size": "The drawdown reading is a fact. Leave the size cap at full.",
        },
        "instructions": (
            "Derisk question: the two sides of shrinking size as equity approaches the wall. "
            "Pick one option. Shrink only when shrink_into_wall is the single highest "
            "probability. An empty answer or a tie does not restore the shrink. "
        ),
    },
    "ceiling_smooth": {
        "withhold": "ceiling_refuses",
        "order": ("ceiling_refuses", "pairing_is_a_fact"),
        "criteria": {
            "ceiling_refuses": "The ceiling profile is not on smooth defense. Do not admit a new entry.",
            "pairing_is_a_fact": "The profile and defense mode are facts. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: base risk is at the 2 percent ceiling and defense is not smooth. "
            "Pick one option. Refuse the book only when ceiling_refuses is the single highest. "
        ),
    },
    "w7_dropped_symbol": {
        "withhold": "symbol_dropped",
        "order": ("symbol_dropped", "symbol_is_the_fire"),
        "criteria": {
            "symbol_dropped": "This symbol is on the dropped energy list. Do not admit it.",
            "symbol_is_the_fire": "The symbol name is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: this intent's symbol is HEATOIL_c or NATGAS_cash. "
            "Pick one option. Drop it only when symbol_dropped is the single highest. "
        ),
    },
    "vp_acceptance": {
        "withhold": "not_above_va",
        "order": ("not_above_va", "vp_loc_is_a_fact"),
        "criteria": {
            "not_above_va": "vp_loc is not above_va on this sleeve. Do not admit the intent.",
            "vp_loc_is_a_fact": "vp_loc is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: this sub_mid_dn_revert intent is not tagged above_va. "
            "Pick one option. Drop it only when not_above_va is the single highest. "
        ),
    },
    "learning_rerate_gate": {
        "withhold": "learning_gate_drop",
        "order": ("learning_gate_drop", "learning_mult_is_a_fact"),
        "criteria": {
            "learning_gate_drop": "The learning multiplier is at zero. Do not admit the intent.",
            "learning_mult_is_a_fact": "The multiplier is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: the learning actuator multiplier for this sleeve is at or under zero. "
            "Pick one option. Drop the intent only when learning_gate_drop is the single highest. "
        ),
    },
    "policy_c_stand_down": {
        "withhold": "stand_down",
        "order": ("stand_down", "policy_c_is_a_fact"),
        "criteria": {
            "stand_down": "Policy C says stand down. Do not admit the intent.",
            "policy_c_is_a_fact": "The policy reading is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: policy C marked this intent stand_down. "
            "Pick one option. Drop it only when stand_down is the single highest. "
        ),
    },
    "metals_confluence": {
        "withhold": "confluence_failed",
        "order": ("confluence_failed", "k_count_is_a_fact"),
        "criteria": {
            "confluence_failed": "The metals K count failed. Do not admit the intent.",
            "k_count_is_a_fact": "The K count is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: this metals intent carries the confluence features and failed K of 4. "
            "Pick one option. Drop it only when confluence_failed is the single highest. "
        ),
    },
    "symbol_damage": {
        "withhold": "quarantine",
        "order": ("quarantine", "damage_is_a_fact"),
        "criteria": {
            "quarantine": "Symbol-damage quarantine is on. Do not admit the intent.",
            "damage_is_a_fact": "The damage reading is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: the symbol-damage multiplier for this symbol is at or under zero. "
            "Pick one option. Drop it only when quarantine is the single highest. "
        ),
    },
    "unknown_sleeve": {
        "withhold": "sleeve_unknown",
        "order": ("sleeve_unknown", "sleeve_is_the_fire"),
        "criteria": {
            "sleeve_unknown": "The sleeve is not in the active registry. Do not size the unit.",
            "sleeve_is_the_fire": "The sleeve name is a fact. The unit can still be sized.",
        },
        "instructions": (
            "Admission question: a member sleeve is absent from the active registry. "
            "Pick one option. Size the unit to zero only when sleeve_unknown is the single highest. "
        ),
    },
    "bad_direction": {
        "withhold": "direction_invalid",
        "order": ("direction_invalid", "direction_is_a_side"),
        "criteria": {
            "direction_invalid": "Direction is not long or short. Do not size the unit.",
            "direction_is_a_side": "Direction is a fact. The unit can still be sized.",
        },
        "instructions": (
            "Admission question: an intent direction is not +1 or -1. "
            "Pick one option. Size the unit to zero only when direction_invalid is the single highest. "
        ),
    },
    "nonpositive_stop": {
        "withhold": "stop_not_positive",
        "order": ("stop_not_positive", "stop_is_the_plan"),
        "criteria": {
            "stop_not_positive": "Stop distance is not positive. Do not size the unit.",
            "stop_is_the_plan": "Stop distance is a fact. The unit can still be sized.",
        },
        "instructions": (
            "Admission question: an intent stop distance is missing or not positive. "
            "Pick one option. Size the unit to zero only when stop_not_positive is the single highest. "
        ),
    },
    "bad_intra_size": {
        "withhold": "intra_size_invalid",
        "order": ("intra_size_invalid", "intra_size_is_a_fact"),
        "criteria": {
            "intra_size_invalid": "Intra size is missing or negative. Do not size the unit.",
            "intra_size_is_a_fact": "Intra size is a fact. The unit can still be sized.",
        },
        "instructions": (
            "Admission question: an intent intra size is missing or negative. "
            "Pick one option. Size the unit to zero only when intra_size_invalid is the single highest. "
        ),
    },
    "gross_cap_shed": {
        "withhold": "shed_unit",
        "order": ("shed_unit", "unit_stays"),
        "criteria": {
            "shed_unit": "This unit does not fit remaining gross headroom. Shed it.",
            "unit_stays": "Headroom is a fact. Keep the unit.",
        },
        "instructions": (
            "Admission question: this sized unit's risk is above remaining gross headroom. "
            "Pick one option. Shed it only when shed_unit is the single highest. "
        ),
    },
    "house_hard_off": {
        "withhold": "hard_off_stands",
        "order": ("hard_off_stands", "sleeve_is_the_fire"),
        "criteria": {
            "hard_off_stands": "This sleeve is house hard-off. Do not admit the candidate.",
            "sleeve_is_the_fire": "The hard-off tag is a fact. This candidate can still be admitted.",
        },
        "instructions": (
            "Admission question: family class is house hard-off, or the sleeve is on the hard-off list. "
            "Pick one option. Block only when hard_off_stands is the single highest. "
        ),
    },
    "admission": {
        "withhold": "not_this_candidate",
        "order": ("this_candidate", "not_this_candidate"),
        "criteria": {
            "this_candidate": "This candidate is admitted on this bar.",
            "not_this_candidate": "This candidate is not admitted on this bar.",
        },
        "instructions": (
            "Admission question: this candidate on this bar. "
            "Pick one option. Refuse only when not_this_candidate is the single highest. "
            "An empty answer or a tie does not refuse."
        ),
    },
    "unknown_profile": {
        "withhold": "profile_missing",
        "order": ("profile_missing", "profile_is_a_name"),
        "criteria": {
            "profile_missing": "This allocation profile is not on the book. Do not size a unit.",
            "profile_is_a_name": "The missing profile is a fact. Do not treat that name as a ban.",
        },
        "instructions": (
            "Admission question: the named allocation profile is not in the book. "
            "Pick one option. Refuse sizing only when profile_missing is the single highest. "
            "An empty answer or a tie does not refuse. A floor and a baseline are not a limit. "
        ),
    },
    "tick_untradeable": {
        "withhold": "floor_refuses",
        "order": ("floor_refuses", "floor_is_a_fact"),
        "criteria": {
            "floor_refuses": "The measured spread floor refuses this symbol.",
            "floor_is_a_fact": "The spread reading is a fact. This symbol can still be admitted.",
        },
        "instructions": (
            "Admission question: this symbol's measured round-trip floor, and whether it is on the dropped energy list. "
            "The recorded untradeable level on the card is a fact, not the decision. "
            "Pick one option. Refuse only when floor_refuses is the single highest. "
            "An empty answer or a tie does not refuse. "
        ),
    },
}


def _cache_key(spot: str, facts: Mapping[str, Any] | None) -> str:
    try:
        blob = json.dumps(facts or {}, sort_keys=True, default=str)
    except TypeError:
        blob = str(facts)
    return spot + "|" + blob


def withholds(spot: str, facts: Mapping[str, Any] | None = None) -> bool:
    """True only when this spot's withhold side is the unique highest probability.

    False means the old branch does not fire. Never raises.
    """
    global last
    spec = SPOTS.get(spot)
    row: dict[str, Any] = {
        "spot": spot,
        "withhold": None if spec is None else spec["withhold"],
        "choice": None,
        "probabilities": {},
        "probability_source": None,
        "blocks": False,
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "error": None,
    }
    if spec is None:
        row["error"] = "unknown_spot"
        last = row
        return False
    key = _cache_key(spot, facts)
    cached = _CACHE.get(key)
    if cached is not None:
        cached_choice = cached[1]
        row["blocks"] = cached[0]
        row["choice"] = cached_choice
        row["cache"] = True
        row["error"] = None if cached_choice else "no_unique_highest"
        last = row
        return cached[0]
    order = tuple(spec["order"])
    criteria = spec["criteria"]
    question = spot_question(spot, spec["instructions"], criteria)
    state = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "spot": spot,
        "model": MODEL,
        "facts": dict(facts or {}),
        "questions": question,
    }
    try:
        from .rung_choice import ask_choice

        hop = ask_choice(
            state,
            question_id=spot,
            instructions=spec["instructions"],
            criteria=criteria,
        ) or {}
    except Exception as exc:  # noqa: BLE001 — admission must not raise into the book
        hop = {"error": type(exc).__name__}
    if not isinstance(hop, dict):
        hop = {"error": "ask_not_a_dict"}
    source = hop.get("probability_source")
    probs_in = hop.get("probabilities") if isinstance(hop.get("probabilities"), dict) else {}
    probs: dict[str, float] = {}
    if source in {"distribution", "probabilities", "probs", "options"}:
        for name, val in probs_in.items():
            if str(name) not in criteria:
                continue
            try:
                probs[str(name)] = float(val)
            except (TypeError, ValueError):
                continue
    winner = unique_highest(probs or None, order)
    blocks = winner == spec["withhold"]
    row["choice"] = winner
    row["probabilities"] = probs
    row["probability_source"] = source if source in {"distribution", "probabilities", "probs", "options"} else None
    row["blocks"] = blocks
    row["error"] = None if winner else (hop.get("error") or "no_unique_highest")
    if hop.get("model"):
        row["model"] = hop.get("model")
    last = row
    _CACHE[key] = (blocks, winner)
    return blocks


def unique_side(spot: str, facts: Mapping[str, Any] | None = None) -> str | None:
    """The unique highest side. None on an empty hop, a tie, or an error."""
    withholds(spot, facts)
    picked = last.get("choice") if isinstance(last, dict) else None
    if not isinstance(picked, str) or not picked:
        return None
    return picked


def blocks(spot: str, facts: Mapping[str, Any] | None = None) -> bool:
    """Off Challenge the old branch stands. On Challenge only the withhold side stands."""
    if not on_challenge():
        return True
    return withholds(spot, facts)


def spot_block(spot: str) -> dict[str, Any] | None:
    """The choice block for a pack. None when the spot is not on this card."""
    spec = SPOTS.get(spot)
    if spec is None:
        return None
    return {
        "type": "choice",
        "instructions": spec["instructions"],
        "criteria": dict(spec["criteria"]),
        "order": tuple(spec["order"]),
    }


def _score_of(block: Any) -> float | None:
    """A score. A tie, an empty answer, or an error is unset."""
    if not isinstance(block, dict) or block.get("error") or block.get("tie") is True:
        return None
    probabilities = block.get("probabilities")
    if isinstance(probabilities, dict) and probabilities:
        try:
            if unique_highest(probabilities) is None:
                return None
        except Exception:
            return None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = None
    if isinstance(number, bool) or number is None:
        return None
    try:
        value = float(number)
    except (TypeError, ValueError):
        return None
    if value != value:
        return None
    return value


def _choice_of(block: Any, order: tuple[str, ...]) -> str | None:
    """The unique highest side. A tie or an empty map is unset."""
    if not isinstance(block, dict) or block.get("error") or block.get("tie") is True:
        return None
    source = block.get("probability_source")
    if source not in {"distribution", "probabilities", "probs", "options"}:
        return None
    probs_in = block.get("probabilities") if isinstance(block.get("probabilities"), dict) else {}
    allowed = set(order)
    probs: dict[str, float] = {}
    for name, val in probs_in.items():
        if str(name) not in allowed:
            continue
        try:
            probs[str(name)] = float(val)
        except (TypeError, ValueError):
            continue
    try:
        return unique_highest(probs or None, order)
    except Exception:
        return None


def ask_pack(
    facts: Mapping[str, Any] | None,
    questions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """One evaluate for this state.

    Each question returns a score or a choice. Empty, a tie, and an error
    leave that question unset. The same facts and questions reuse the pack.
    """
    card = dict(facts or {})
    spec: dict[str, Any] = {}
    for key, block in questions.items():
        if not isinstance(block, Mapping):
            continue
        kind = str(block.get("type") or "")
        if kind not in {"score", "choice"}:
            continue
        item: dict[str, Any] = {
            "type": kind,
            "instructions": str(block.get("instructions") or ""),
        }
        if kind == "choice" and isinstance(block.get("criteria"), Mapping):
            item["criteria"] = {str(name): str(text) for name, text in block["criteria"].items()}
            order = block.get("order")
            if isinstance(order, (list, tuple)):
                item["order"] = tuple(str(name) for name in order)
        spec[str(key)] = item
    key = _cache_key("pack", {"facts": card, "questions": spec})
    cached = _PACK.get(key)
    if cached is not None:
        return dict(cached)
    wire: dict[str, Any] = {}
    for qid, item in spec.items():
        block = {"type": item["type"], "instructions": item["instructions"]}
        if item["type"] == "choice":
            block["criteria"] = item.get("criteria") or {}
        wire[qid] = block
    state = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "model": MODEL,
        "facts": card,
    }
    try:
        from .jev_client import evaluate

        receipt = evaluate(state, questions=wire, merge_sleeve=False, model=MODEL) or {}
    except Exception as exc:  # noqa: BLE001 — a pack must not raise into the book
        receipt = {"error": type(exc).__name__, "answers": {}}
    if not isinstance(receipt, dict):
        receipt = {"error": "ask_not_a_dict", "answers": {}}
    answers = receipt.get("answers") if isinstance(receipt.get("answers"), dict) else {}
    out: dict[str, Any] = {}
    for qid, item in spec.items():
        block = answers.get(qid)
        if item["type"] == "score":
            out[qid] = _score_of(block)
        else:
            order = item.get("order") or tuple((item.get("criteria") or {}))
            out[qid] = _choice_of(block, tuple(order))
    _PACK[key] = dict(out)
    return dict(out)
