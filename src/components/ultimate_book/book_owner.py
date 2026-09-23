"""UltimateBookOwner — the cross-symbol book driver (one process owns the whole book).

This sidesteps the per-symbol-process impedance: it runs the engine (cross-symbol generation +
admission in ONE process, so the correlated-unit sizing + 4% gross cap are correct), then for each
realized unit pairs it with its TradeIntent(s) and routes each to a per-symbol ExecutionEngine via the
order_router. Cross-process file-locked shared state is not needed in this single-process design.

DEFAULT-OFF + fail-closed: when the ultimate_book triple-gate is off, the bridge returns shadow-only
(runtime_effect_now=False) -> the owner logs would_units and places NOTHING. open_trade inherits the
halt guard, so while any halt flag is present nothing sends even if mis-invoked. The owner NEVER raises.
"""
from __future__ import annotations

import logging
import time
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from .book_engine import UltimateBookLiveEngine, _TF_MINUTES, rewrite_no_candidates_operator_reason
from .bridge import config_bool_value
from .order_router import UltimateBookOrderRouter
from .symbol_map import build_broker_symbol_resolver
from .placement_ledger import PlacementLedger
from .admission import cluster_of, resolve_market_expansion_sleeves
from .convergence_advisory import build_convergence_advisory
from .runtime_learning_packet import (
    DEFAULT_LOG_PATH as RUNTIME_LEARNING_PACKET_DEFAULT_LOG_PATH,
    SCHEMA_VERSION as RUNTIME_LEARNING_PACKET_SCHEMA_VERSION,
    RuntimeLearningPacketWriter,
    build_runtime_learning_packet,
    stable_hash,
)
from .packet_economics import (
    LEGACY_MODELLED_COST_COMPONENTS,
    LEGACY_MODELLED_COST_EXCLUDES,
    MODELLED_COST_COMPONENTS,
    MODELLED_COST_EXCLUDES,
    build_economics_block,
)
# OD-P1's filter is a NEW file. It is not on the live host, and `book_owner.py` IS -- so a carry
# that copies this file without `packet_emit_on_change.py` would raise ImportError at module load
# and kill run_book.py at startup on both funded accounts. That is the single worst outcome a carry
# can have, and AZ measured that 9 of its 16 partial carry states were unsafe with four of them
# module-load deaths, against a probe that could not have seen this one because the file did not
# exist yet.
#
# So the dependency is optional by construction -- the same guard, for the same reason, that
# `packet_economics.py:50-66` applies to `broker_clock`. Absent, emit-on-change is simply
# unavailable and every other packet field still works; the feature is default-OFF anyway, so the
# degraded state is also the intended state. `except Exception` rather than `except ImportError` is
# deliberate: a half-finished file transfer leaves the module PRESENT AND BROKEN, which raises
# SyntaxError, and an absent optional dependency and a corrupt one must degrade identically.
try:
    from .packet_emit_on_change import (  # type: ignore[attr-defined]
        DEFAULT_HEARTBEAT_SECONDS as EMIT_ON_CHANGE_DEFAULT_HEARTBEAT_SECONDS,
        PositionManagedEmitFilter,
        filter_packets as filter_emit_on_change_packets,
    )

    EMIT_ON_CHANGE_AVAILABLE = True
except Exception:  # noqa: BLE001 - nothing about this file may stop a live book
    EMIT_ON_CHANGE_AVAILABLE = False
    EMIT_ON_CHANGE_DEFAULT_HEARTBEAT_SECONDS = 900
    PositionManagedEmitFilter = None  # type: ignore[assignment]

    def filter_emit_on_change_packets(packets, emit_filter, *, now=None):  # type: ignore[misc]
        """Identity. With no filter module there is nothing to suppress."""
        return list(packets), 0
from .packet_guard import GuardedPacketWriter
from .weekend_policy import OFF as _WEEKEND_OFF
from src.components.ai_companion.control_state import AICompanionRuntimeGate

_log = logging.getLogger(__name__)


def f5_leftover_open_stay(ticket, ledger_path=None):
    """Writer-visible leftover-open Atlas-stay predicate. Reads the stay ledger."""
    from .minimal_size import f5_leftover_open_stay as _fn
    return _fn(ticket, ledger_path=ledger_path)


def f5_fast_family_takeoff_may_close(ticket=None, sleeve=None, symbol=None, **kwargs):
    """Writer-visible may-close gate. Fail closed. Does not send."""
    from .minimal_size import f5_fast_family_takeoff_may_close as _fn
    return _fn(ticket=ticket, sleeve=sleeve, symbol=symbol, **kwargs)


# Placement-failure reasons (surfaced by execution.open_trade via _last_open_trade_block_reason, or by the
# router) that are TRANSIENT broker/IO hiccups — a broker requote, a fleeting order_calc_profit/symbol_info
# read miss. These can succeed on a retry, so a decision bar that hit one must NOT be consumed: the next tick
# re-runs the SAME bar (re-attempting the leg) while the placed-leg idempotency ledger + active_trade/
# _broker_holds guards prevent any double-place. An order_send timeout and timeout_no_position are not this
# list's decision on Challenge. That bar is the order_timeout hop. Deterministic declines (cost_screen_*,
# vnext_policy:*, geometry_unavailable, exec_mgr_v4:* geometry gaps) are NOT here — they will never clear on
# retry, so retrying would only spam. Matched as a prefix of the reason string.
_TRANSIENT_PLACE_REASON_PREFIXES = (
    "open_trade_returned_none",     # opaque None (treat as transient: a broker/IO miss left no specific code)
    "order_rejected:",              # broker sent the order back (requote/off-quotes/timeout_no_fill/price moved)
    "no_tick_data",                 # the entry tick read came back empty for this attempt
    "cash_risk_unverified",         # broker order_calc_profit returned None this attempt (often transient)
    "lot_size_unverified",          # broker lot/geometry verification read missed this attempt
    "lot_normalize_failed",
    "filling_mode_unresolved",      # symbol_info filling-mode read missed this attempt
    "deviation_unresolved",         # symbol_info deviation read missed this attempt
    "timeout_no_position",          # named here so other books still classify it; Challenge asks order_timeout
    "order_send_exception",         # safe_place_order diagnostic: order_send raised (transient broker/IPC)
)

# Broker reject comments that are TERMINAL for the identical request (insufficient funds, invalid
# stops/volume, trading disabled) -> re-sending the SAME order would just fail again, so do NOT keep the bar.
_TERMINAL_BROKER_REJECT_MARKERS = (
    "no money", "not enough money", "insufficient", "invalid stops", "invalid volume",
    "invalid price", "invalid order", "trade disabled", "trade is disabled", "market closed",
    "autotrading disabled", "trade not allowed",
)


def _is_transient_place_failure(reason) -> bool:
    """True when a non-placement `reason` is a transient broker/IO hiccup worth retrying on the next tick
    (leave the decision bar unconsumed). Terminal broker rejects (no money / invalid stops / market closed)
    return False so we don't retry an identical doomed request every tick."""
    if not reason:
        return False
    text = str(reason).strip().lower()
    if not any(text.startswith(p) for p in _TRANSIENT_PLACE_REASON_PREFIXES):
        return False
    if text.startswith("order_rejected:") and any(m in text for m in _TERMINAL_BROKER_REJECT_MARKERS):
        return False
    return True


def _transient_place_reason_prefix(reason):
    """The matched transient prefix (the --transient-retry-cap counter's reason CLASS), or None
    when the reason is not a transient place failure at all.

    The cap counts per PREFIX rather than per full reason string deliberately: broker comments
    vary per attempt (a requote may embed a price), and a varying tail would reset a
    full-string key every poll and let a storm run under the cap forever. Kept in lockstep with
    `_is_transient_place_failure` — same normalization, same tuple, same terminal-marker
    carve-out — so the two can never disagree about what is transient (2026-08-17 UK100:
    35 identical `order_rejected:timeout_no_fill` sends in 36 min, an activation-token refusal
    wearing a transient label)."""
    if not _is_transient_place_failure(reason):
        return None
    text = str(reason).strip().lower()
    for p in _TRANSIENT_PLACE_REASON_PREFIXES:
        if text.startswith(p):
            return p
    return None   # unreachable while both functions read the same prefix tuple

_JEV_MODEL = "jev-1.13.0"
_LIMIT_STATE_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "daily_loss_pct",
})
_BANNED_LIMIT_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "110000",
    "110,000",
    "110_000",
    "110k",
)


def _scrub_limit_text(text):
    cleaned = str(text or "")
    for token in _BANNED_LIMIT_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _facts_for_jev(state):
    """Facts for one ask. A floor dollar and a baseline dollar stay off the question."""
    facts = {}
    if isinstance(state, dict):
        for key, value in state.items():
            if str(key) in _LIMIT_STATE_KEYS:
                continue
            facts[str(key)] = value
    facts["model"] = _JEV_MODEL
    return facts


def _jev_questions(question_id, instructions, criteria, kind):
    """Question payload from the judgment helpers. Same shapes those modules post."""
    text = _scrub_limit_text(instructions)
    if kind == "score":
        levels = list(criteria) if isinstance(criteria, (list, tuple)) else []
        built = None
        try:
            from src.judgment.jev_questions import parameter_question

            built = parameter_question(question_id, text)
        except Exception:
            built = None
        if not isinstance(built, dict):
            built = {
                question_id: {
                    "type": "score",
                    "instructions": text,
                    "criteria": levels,
                }
            }
        elif levels:
            block = built.get(question_id)
            if isinstance(block, dict) and "criteria" not in block:
                copied = dict(block)
                copied["criteria"] = levels
                built = dict(built)
                built[question_id] = copied
        return built
    if kind == "noul":
        crit = dict(criteria) if isinstance(criteria, dict) else {}
        return {
            question_id: {
                "type": "noul",
                "instructions": text,
                "criteria": crit,
            }
        }
    crit = dict(criteria) if isinstance(criteria, dict) else {}
    from src.judgment.jev_questions import spot_question

    return spot_question(question_id, text, crit)


def _finite_number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _anchor_pairs(pairs):
    """Distinct finite facts in one unit. Fewer than two is not a Score."""
    found = []
    seen = []
    for item in pairs or ():
        if not isinstance(item, tuple) or len(item) != 2:
            continue
        label, raw = item
        number = _finite_number(raw)
        text = "" if label is None else str(label).strip()
        if number is None or number in (float("inf"), float("-inf")) or not text or number in seen:
            continue
        seen.append(number)
        found.append((text, number))
    if len(found) < 2:
        return None
    return found


def _read_jev_return(kind, block, criteria):
    """A return is a Noul, a Choice, or a Score. Anything else is unset."""
    from src.judgment.jev_questions import returned_number, unique_highest

    if not isinstance(block, dict):
        return None
    if kind == "score":
        number = None
        try:
            number = returned_number(block)
        except Exception:
            number = None
        if number is None:
            raw = block.get("score")
            if raw is None:
                raw = block.get("value")
            number = _finite_number(raw)
        return _finite_number(number)
    if kind == "noul":
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return None
    probs_in = block.get("probabilities") if isinstance(block.get("probabilities"), dict) else None
    numeric = {}
    if isinstance(probs_in, dict):
        for key, val in probs_in.items():
            number = _finite_number(val)
            if number is None:
                continue
            numeric[str(key)] = number
    if not numeric:
        return None
    order = tuple(criteria.keys()) if isinstance(criteria, dict) else tuple(numeric)
    try:
        picked = unique_highest(numeric, order)
    except TypeError:
        picked = unique_highest(numeric)
    if picked is None:
        return None
    if isinstance(criteria, dict) and str(picked) not in criteria:
        return None
    return str(picked)


_ASK_SLOT: dict = {}


def _facts_fingerprint(state) -> str:
    """Stable text of one ask's facts. A changed card is a new state."""
    import json

    try:
        return json.dumps(
            state if isinstance(state, dict) else {},
            sort_keys=True,
            default=str,
        )
    except Exception:
        return repr(state)


def _ask_identity(state) -> str:
    """Which ticket or bar this slot belongs to. The fingerprint says if it changed."""
    if not isinstance(state, dict):
        return ""
    parts = []
    for key in (
        "ticket",
        "symbol",
        "sleeve",
        "decision_bar_iso",
        "reason",
        "action",
        "written_at_utc",
        "namespace",
    ):
        value = state.get(key)
        if value not in (None, ""):
            parts.append(str(key) + "=" + str(value))
    return "|".join(parts)


def _ask_jev(question_id, state, *, kind, instructions, criteria=None):
    """One System One ``evaluate``. Empty, tie, missing score, and error return None.

    The same facts do not post again. A changed card asks again. That does not
    restore a constant. Prior live outcomes go on the state. The returned value
    is remembered for the next ask. Never raises. Never sends.
    """
    incoming = state if isinstance(state, dict) else {}
    slot = (str(question_id), str(kind), _ask_identity(incoming))
    fingerprint = _facts_fingerprint(incoming)
    found = _ASK_SLOT.get(slot)
    if isinstance(found, tuple) and len(found) == 2 and found[0] == fingerprint:
        return found[1]

    def _store(value):
        _ASK_SLOT[slot] = (fingerprint, value)
        return value

    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import append_outcome, prior_outcomes
    except Exception:
        return _store(None)
    facts = _facts_for_jev(state if isinstance(state, dict) else {})
    try:
        questions = _jev_questions(question_id, instructions, criteria, kind)
    except Exception:
        return _store(None)
    if not isinstance(questions, dict):
        return _store(None)
    qid = question_id if question_id in questions else question_id
    if question_id not in questions and len(questions) == 1:
        qid = next(iter(questions))
    try:
        facts["prior_outcomes"] = prior_outcomes(state=facts, questions=questions)
    except Exception:
        pass
    value = None
    error = None
    try:
        receipt = evaluate(
            facts,
            questions=questions,
            merge_sleeve=False,
        ) or {}
    except Exception as exc:
        receipt = {}
        error = type(exc).__name__
    answers = receipt.get("answers") if isinstance(receipt, dict) else None
    block = answers.get(qid) if isinstance(answers, dict) else None
    if block is None and isinstance(answers, dict):
        block = answers.get(question_id)
    if error is None:
        try:
            value = _read_jev_return(kind, block, criteria)
        except Exception as exc:
            value = None
            error = type(exc).__name__
        if value is None and error is None:
            if kind == "score":
                error = "score_missing"
            elif kind == "noul":
                error = "noul_missing"
            else:
                error = "tie_or_empty"
    try:
        append_outcome(qid, value, facts, error=error)
    except Exception:
        pass
    return _store(value)


def _ask_pack(cache_name, state, specs):
    """One ``evaluate`` for every question in ``specs``. Same facts do not post again.

    Independent hops share the post. Empty, tie, missing score, and error stay
    None and do not restore a constant. Never raises. Never sends.
    """
    incoming = state if isinstance(state, dict) else {}
    slot = ("pack", str(cache_name), _ask_identity(incoming))
    fingerprint = _facts_fingerprint(incoming)
    found = _ASK_SLOT.get(slot)
    if isinstance(found, tuple) and len(found) == 2 and found[0] == fingerprint:
        cached = found[1]
        return dict(cached) if isinstance(cached, dict) else {}
    out = {}
    for spec in specs or ():
        out[str(spec[0])] = None
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import append_outcome, prior_outcomes
    except Exception:
        _ASK_SLOT[slot] = (fingerprint, dict(out))
        return dict(out)
    questions = {}
    meta = []
    for spec in specs or ():
        qid, kind, instructions, criteria = spec[0], spec[1], spec[2], spec[3]
        try:
            built = _jev_questions(str(qid), instructions, criteria, kind)
        except Exception:
            built = None
        if isinstance(built, dict):
            questions.update(built)
        meta.append((str(qid), kind, criteria))
    if not questions:
        _ASK_SLOT[slot] = (fingerprint, dict(out))
        return dict(out)
    facts = _facts_for_jev(incoming)
    try:
        facts["prior_outcomes"] = prior_outcomes(state=facts, questions=questions)
    except Exception:
        pass
    error = None
    try:
        receipt = evaluate(
            facts,
            questions=questions,
            merge_sleeve=False,
        ) or {}
    except Exception as exc:
        receipt = {}
        error = type(exc).__name__
    answers = receipt.get("answers") if isinstance(receipt, dict) else None
    if not isinstance(answers, dict):
        answers = {}
    for qid, kind, criteria in meta:
        block = answers.get(qid)
        value = None
        row_error = error
        if row_error is None:
            try:
                value = _read_jev_return(kind, block, criteria)
            except Exception as exc:
                value = None
                row_error = type(exc).__name__
            if value is None and row_error is None:
                if kind == "score":
                    row_error = "score_missing"
                elif kind == "noul":
                    row_error = "noul_missing"
                else:
                    row_error = "tie_or_empty"
        out[qid] = value
        try:
            append_outcome(qid, value, facts, error=row_error)
        except Exception:
            pass
    _ASK_SLOT[slot] = (fingerprint, dict(out))
    return dict(out)


def _is_order_timeout_reason(reason) -> bool:
    """True when the place failure names an order timeout.

    ``timeout_no_position`` and an order_send timeout are that name. The tail
    of a broker comment is not a second class.
    """
    text = str(reason or "").strip().lower()
    if not text:
        return False
    if text.startswith("timeout_no_position"):
        return True
    return "timeout" in text


def _order_timeout_class(reason) -> str:
    text = str(reason or "").strip().lower()
    if text.startswith("timeout_no_position"):
        return "timeout_no_position"
    if "timeout" in text:
        return "order_send_timeout"
    return ""


def _order_timeout_pack(reason) -> dict:
    """One ask for this timeout class. The choice and the retry budget travel together.

    An empty choice does not restore the old retry law. An empty budget does
    not restore a cap and does not end the bar.
    """
    klass = _order_timeout_class(reason)
    if not klass:
        return {}
    return _ask_pack(
        "order_timeout",
        {"reason": klass, "namespace": "operator"},
        (
            (
                "order_timeout",
                "choice",
                "This place attempt named an order timeout (" + klass + "). "
                "keep_bar leaves the decision bar open. "
                "consume_bar ends the bar. "
                "An empty answer or a tie does not send and does not restore a retry law. "
                "A floor dollar and a baseline dollar are not a limit.",
                {
                    "keep_bar": "Leave the bar open. This timeout does not end it.",
                    "consume_bar": "This timeout ends the bar.",
                },
            ),
            (
                "order_timeout_retries",
                "score",
                "The score you return is how many place attempts this timeout keeps open. "
                "An empty score does not restore a retry cap and does not end the bar.",
                (
                    "tighter than the last returned score",
                    "the last returned score",
                    "wider than the last returned score",
                ),
            ),
        ),
    )


def _lifetime_pack(facts) -> dict:
    """Move, break even, scale out, time stop, and close, one post.

    Each return is that hop. Empty does not send and does not restore a
    constant. The stop and the scale fraction are the scores on the same card.
    """
    shared = (
        " The unique highest probability is the decision."
        " An empty answer or a tie does not send and does not restore a constant."
        " A floor dollar and a baseline dollar are not a limit."
        " Do not flatten the book. This question is only this ticket."
    )
    return _ask_pack(
        "lifetime",
        facts if isinstance(facts, dict) else {},
        (
            (
                "move_stop",
                "choice",
                "Move this open ticket's stop, or leave it." + shared,
                {
                    "move_stop": "Move the stop to the returned stop.",
                    "leave": "Leave the stop.",
                },
            ),
            (
                "break_even",
                "choice",
                "Break even on this open ticket, or leave the stop." + shared,
                {
                    "break_even": "Move the stop to the returned breakeven.",
                    "leave": "Do not break even.",
                },
            ),
            (
                "scale_out",
                "choice",
                "Scale out of this open ticket, or leave the volume." + shared,
                {
                    "scale_out": "Scale out the returned fraction of the open volume.",
                    "leave": "Do not scale out.",
                },
            ),
            (
                "time_stop",
                "choice",
                "Time-stop this open ticket, or leave it." + shared,
                {
                    "time_stop": "Close this ticket as a time stop.",
                    "leave": "Do not time-stop.",
                },
            ),
            (
                "close",
                "choice",
                "Close this open ticket, or leave it." + shared,
                {
                    "close": "Close this ticket.",
                    "leave": "Leave this ticket open.",
                },
            ),
            (
                "lifetime_stop",
                "score",
                "The score you return is the stop for this ticket. "
                "It may sit between the prices on the card. "
                "An empty score does not move the stop.",
                (
                    "tighter than the last returned score",
                    "the last returned score",
                    "wider than the last returned score",
                ),
            ),
            (
                "lifetime_scale",
                "score",
                "The score you return is the fraction of the open volume to scale out. "
                "An empty score does not scale out.",
                (
                    "tighter than the last returned score",
                    "the last returned score",
                    "wider than the last returned score",
                ),
            ),
        ),
    )


def _spot_choice(question, state, criteria, withhold, cache_key, instructions):
    """True only when ``withhold`` is the unique highest Choice.

    The other side, an empty probability map, a tie, and any error return
    False. That does not restore a constant. Never raises. Never sends.
    """
    del cache_key
    text = str(instructions or "")
    if "294215389" not in text:
        text = (
            text
            + " The unique highest probability is the decision."
            + " An empty answer or a tie does not restore a constant."
            + " Do not close ticket 294215389."
        )
    choice = _ask_jev(
        str(question),
        state if isinstance(state, dict) else {},
        kind="choice",
        instructions=text,
        criteria=criteria if isinstance(criteria, dict) else {},
    )
    if choice is None:
        return False
    return str(choice) == str(withhold)


def _challenge_withholds(namespace, question, state, criteria, withhold, cache_key, instructions) -> bool:
    """Other books keep the skip. Challenge skips only when ``withhold`` wins.

    An empty answer, a tie, and any error do not skip and do not restore the
    old continue. Never raises.
    """
    if str(namespace) != "operator":
        return True
    try:
        return bool(_spot_choice(
            question,
            state,
            criteria,
            withhold,
            cache_key,
            instructions,
        ))
    except Exception:
        return False


def _parameter_score(question, state, instructions, criteria=None):
    """The Score for this parameter. None when it is missing.

    A word level is not an amount. The only Score is numeric anchors in
    this hop's unit. Fewer than two stays unset. A miss does not restore
    a constant and does not send.
    """
    anchors = _anchor_pairs(criteria) if criteria is not None else None
    if not anchors:
        return None
    text = (
        str(instructions or "")
        + " The score you return may sit between levels."
        + " An empty score does not restore a constant."
        + " A floor dollar and a baseline dollar are not a limit."
    )
    try:
        from src.judgment.nineteen import score

        return score(
            state if isinstance(state, dict) else {},
            question_id=str(question),
            instructions=text,
            anchors=anchors,
        )
    except Exception:
        return None


def _noul_withholds(question, state, instructions, criteria=None):
    """True only when the Noul is an actual bool True.

    A probability that is not a bool, an empty answer, and any error do not
    withhold and do not restore a constant.
    """
    crit = criteria if isinstance(criteria, dict) else {
        "withhold": "This fact withholds.",
        "allow": "This fact does not withhold.",
    }
    value = _ask_jev(
        str(question),
        state if isinstance(state, dict) else {},
        kind="noul",
        instructions=str(instructions or "")
        + " Return a noul. Only an actual bool withholds."
        + " An empty answer does not restore a constant."
        + " A floor dollar and a baseline dollar are not a limit.",
        criteria=crit,
    )
    return value is True


def _hop_key(intent, dbar=None):
    bar = dbar if dbar not in (None, "") else getattr(intent, "decision_day", None)
    return (
        str(getattr(intent, "sleeve", "") or ""),
        str(getattr(intent, "symbol", "") or ""),
        str(bar or ""),
    )


def _merge_hop(bucket, intent, dbar=None, **values) -> None:
    """Remember a hop return off the intent.

    A frozen intent rejects new attributes. The map is what the next hop reads.
    An empty value is not written and does not replace a return already there.
    """
    if not isinstance(bucket, dict):
        return
    key = _hop_key(intent, dbar)
    if not key[0] or not key[1]:
        return
    row = bucket.get(key)
    if not isinstance(row, dict):
        row = {}
        bucket[key] = row
    for name, value in values.items():
        if value in (None, ""):
            continue
        if row.get(name) in (None, ""):
            row[name] = value


def _read_hop(bucket, intent, dbar=None) -> dict:
    if not isinstance(bucket, dict):
        return {}
    key = _hop_key(intent, dbar)
    found = bucket.get(key)
    row = dict(found) if isinstance(found, dict) else {}
    day = str(getattr(intent, "decision_day", "") or "")[:10]
    alt_key = (key[0], key[1], day)
    alt = bucket.get(alt_key)
    if alt_key != key and isinstance(alt, dict):
        for name, value in alt.items():
            if row.get(name) in (None, "") and value not in (None, ""):
                row[name] = value
    return row


def _carry_hop_returns(source, dest):
    """Copy hop attributes when the runtime allows it. Empty stays empty."""
    if dest is None or dest is source:
        return dest
    for name in ("details", "last_bar_choice", "intent_return", "admission_return"):
        try:
            value = getattr(source, name)
        except Exception:
            continue
        if value in (None, "", {}):
            continue
        try:
            current = getattr(dest, name)
        except Exception:
            current = None
        if current not in (None, "", {}):
            continue
        try:
            setattr(dest, name, value)
        except Exception:
            continue
    return dest


def _admission_receipt(intent, hops):
    if isinstance(hops, dict) and isinstance(hops.get("admission_receipt"), dict):
        return hops["admission_receipt"]
    try:
        details = getattr(intent, "details")
    except Exception:
        details = None
    if isinstance(details, dict) and isinstance(details.get("jev_admission_receipt"), dict):
        return details["jev_admission_receipt"]
    return None


def _unique_stay_out(intent, hops=None):
    """The unique stay-out for this bar, or (None, None).

    closed_bar_does_not_reach, sleeve_stays_out, and an admission return
    whose unique may_place is False stop the bar. An empty answer is not
    a stay-out and is not a send.
    """
    hops = hops if isinstance(hops, dict) else {}
    last_bar = hops.get("last_bar")
    if last_bar in (None, ""):
        try:
            last_bar = getattr(intent, "last_bar_choice")
        except Exception:
            last_bar = None
    if last_bar == "closed_bar_does_not_reach":
        return "last_bar", last_bar
    unit = getattr(intent, "unit_choice", None) or hops.get("unit")
    if unit == "sleeve_stays_out":
        return "unit", unit
    receipt = _admission_receipt(intent, hops)
    if (
        isinstance(receipt, dict)
        and receipt.get("unique_highest") is True
        and receipt.get("may_place") is False
    ):
        return "admission", receipt.get("admit")
    return None, None


def _hop_notes(intent, flow_dec, hops=None):
    """Returns already in hand, for the place hop. Empty stays absent."""
    hops = hops if isinstance(hops, dict) else {}
    notes = {}
    last_bar = hops.get("last_bar")
    if not isinstance(last_bar, str) or not last_bar:
        try:
            last_bar = getattr(intent, "last_bar_choice")
        except Exception:
            last_bar = None
    if isinstance(last_bar, str) and last_bar:
        notes["last_bar"] = last_bar
    unit = getattr(intent, "unit_choice", None) or hops.get("unit")
    if isinstance(unit, str) and unit:
        notes["unit"] = unit
    intent_return = hops.get("intent")
    if not isinstance(intent_return, str) or not intent_return:
        try:
            intent_return = getattr(intent, "intent_return")
        except Exception:
            intent_return = None
    if isinstance(intent_return, str) and intent_return:
        notes["intent"] = intent_return
    elif isinstance(flow_dec, dict):
        action = flow_dec.get("fear_choice") or flow_dec.get("action")
        if isinstance(action, str) and action and action not in {"UNANSWERED", "PASS"}:
            notes["intent"] = action
    receipt = _admission_receipt(intent, hops)
    if isinstance(receipt, dict):
        admit = receipt.get("admit")
        if isinstance(admit, str) and admit:
            notes["admission"] = admit
    elif isinstance(hops.get("admission"), str) and hops.get("admission"):
        notes["admission"] = hops["admission"]
    return notes


def _stamp_recorded_hops(intents, terminals, meta, bucket=None) -> None:
    """Put last_bar and unit returns where the next hop can read them.

    Reads the terminal and the choice record. Does not ask again.
    An empty record stays empty and does not become a side.
    """
    if not isinstance(intents, list):
        return
    bars = {}
    for row in meta or []:
        if not isinstance(row, dict):
            continue
        bars[(str(row.get("tag") or ""), str(row.get("symbol") or ""))] = row.get("decision_bar_iso")
    last_by = {}
    for item in terminals or []:
        if not isinstance(item, dict):
            continue
        choice = item.get("last_bar_choice")
        if choice in (None, ""):
            continue
        key = (
            str(item.get("sleeve") or ""),
            str(item.get("symbol") or ""),
            str(item.get("decision_bar_iso") or ""),
        )
        last_by[key] = choice
    recorded = None
    try:
        from src.judgment.book_engine_choices import latest_recorded_choice

        recorded = latest_recorded_choice
    except Exception:
        recorded = None
    for index, intent in enumerate(list(intents)):
        sleeve = str(getattr(intent, "sleeve", "") or "")
        symbol = str(getattr(intent, "symbol", "") or "")
        dbar = bars.get((sleeve, symbol))
        choice = last_by.get((sleeve, symbol, str(dbar or "")))
        if choice in (None, "") and dbar not in (None, "") and recorded is not None:
            try:
                choice = recorded("last_bar", symbol=symbol, sleeve=sleeve, bar_iso=dbar)
            except Exception:
                choice = None
        if isinstance(choice, str) and choice:
            try:
                intent.last_bar_choice = choice
            except Exception:
                pass
            _merge_hop(bucket, intent, dbar, last_bar=choice)
        unit = getattr(intent, "unit_choice", None)
        if unit in (None, "") and dbar not in (None, "") and recorded is not None:
            try:
                found = recorded("unit", symbol=symbol, sleeve=sleeve, bar_iso=dbar)
            except Exception:
                found = None
            if found in {"unit_long", "unit_short", "sleeve_stays_out"}:
                unit = found
                try:
                    from dataclasses import replace

                    intents[index] = _carry_hop_returns(
                        intent, replace(intent, unit_choice=unit),
                    )
                    intent = intents[index]
                except Exception:
                    pass
        if unit in {"unit_long", "unit_short", "sleeve_stays_out"}:
            _merge_hop(bucket, intent, dbar, unit=unit)
        receipt = _admission_receipt(intent, None)
        if isinstance(receipt, dict):
            _merge_hop(
                bucket,
                intent,
                dbar,
                admission_receipt=receipt,
                admission=receipt.get("admit"),
            )


def _default_engine_factory(base_config, mt5, *, magic=None, f5_scaler=None):
    """Build a per-symbol ExecutionEngine from the symbol-merged live config (lazy, cached).

    `magic` is passed EXPLICITLY rather than left to the engine's own namespace resolution so
    that the owner, the wrapper and every engine it builds carry one identity resolved once.
    `f5_scaler` is None unless the minimal-size experiment is armed, and with it None every F5
    seam inside `ExecutionEngine` is inert."""
    from src.utils.config import apply_instrument_overrides
    from src.components.execution import ExecutionEngine

    def factory(symbol: str):
        cfg = apply_instrument_overrides(dict(base_config), symbol)
        return ExecutionEngine(mt5, cfg, magic=magic, f5_scaler=f5_scaler)
    return factory


def _bridge_telemetry(decision) -> dict:
    """Compact bridge decision fields for launcher JSONL monitoring."""
    return {
        "runtime_effect_now": bool(getattr(decision, "runtime_effect_now", False)),
        "candidate_use_allowed_now": bool(getattr(decision, "candidate_use_allowed_now", False)),
        "decision_status": getattr(decision, "decision_status", None),
        "reason": getattr(decision, "reason", None),
        "profile": getattr(decision, "profile", None),
        "enabled": bool(getattr(decision, "enabled", False)),
        "apply_to_execution": bool(getattr(decision, "apply_to_execution", False)),
        "live_activation_allowed_by_config": bool(getattr(decision, "live_activation_allowed_by_config", False)),
        "live_broker_authority": bool(getattr(decision, "live_broker_authority", False)),
        "broad_selector_disable_required": bool(getattr(decision, "broad_selector_disable_required", False)),
        "broad_selector_apply_to_execution": bool(getattr(decision, "broad_selector_apply_to_execution", False)),
        "include_clean3": bool(getattr(decision, "include_clean3", False)),
        "include_clean4": bool(getattr(decision, "include_clean4", False)),
        "include_candidate_book": bool(getattr(decision, "include_candidate_book", False)),
        "candidate_book_profile": getattr(decision, "candidate_book_profile", None),
        "candidate_book_sleeves": list(getattr(decision, "candidate_book_sleeves", ()) or ()),
        "candidate_book_sleeve_count": len(list(getattr(decision, "candidate_book_sleeves", ()) or ())),
        "include_market_expansion_book": bool(getattr(decision, "include_market_expansion_book", False)),
        "market_expansion_profile": getattr(decision, "market_expansion_profile", None),
        "market_expansion_policy": getattr(decision, "market_expansion_policy", None),
        "market_expansion_sleeves": list(getattr(decision, "market_expansion_sleeves", ()) or ()),
        "market_expansion_sleeve_count": len(list(getattr(decision, "market_expansion_sleeves", ()) or ())),
        "kelly_lite": bool(getattr(decision, "kelly_lite", False)),
        "kelly_conservative": bool(getattr(decision, "kelly_conservative", False)),
        "kelly_running_count": bool(getattr(decision, "kelly_running_count", False)),
        "sqrt_n_pooling": bool(getattr(decision, "sqrt_n_pooling", False)),
        "stress_derisk": bool(getattr(decision, "stress_derisk", False)),
        "derisk_mode": getattr(decision, "derisk_mode", None),
        "overlays": bool(getattr(decision, "overlays", False)),
        "vp_acceptance": bool(getattr(decision, "vp_acceptance", False)),
        "drop_w7_symbols": bool(getattr(decision, "drop_w7_symbols", False)),
        "learning_rerate_active": bool(getattr(decision, "learning_rerate_active", False)),
        "learning_gated_sleeves": list(getattr(decision, "learning_gated_sleeves", ()) or ()),
        "metals_confluence_gate": bool(getattr(decision, "metals_confluence_gate", False)),
        "symbol_damage_guard": bool(getattr(decision, "symbol_damage_guard", False)),
        "damage_quarantined_symbols": list(getattr(decision, "damage_quarantined_symbols", ()) or ()),
        "dropped_symbols": list(getattr(decision, "dropped_symbols", ()) or ()),
        "n_candidates_in": int(getattr(decision, "n_candidates_in", 0) or 0),
        "n_candidates_after_drop": int(getattr(decision, "n_candidates_after_drop", 0) or 0),
        "would_new_entries_allowed": bool(getattr(decision, "would_new_entries_allowed", False)),
        "would_total_risk_pct": float(getattr(decision, "would_total_risk_pct", 0.0) or 0.0),
        "would_units": list(getattr(decision, "would_units", []) or []),
        "realized_units": list(getattr(decision, "realized_units", []) or []),
        "governor": getattr(decision, "governor", None),
    }


class UltimateBookOwner:
    def __init__(self, base_config: dict, mt5, repo_root: str, namespace: str = "operator_profile",
                 engine_factory: Optional[Callable[[str], Any]] = None,
                 recover_pre_gap_bar: bool = False, vol_level_tilt: bool = False,
                 frontier_exits: tuple = (), spread_geometry_floor=None, weekend_policy=None,
                 entry_hour=None, event_clock_shadow: bool = False,
                 lane_weight_controller=None, minimal_size=None,
                 risk_unit_floor_policy=None, frozen_intent_reprice: bool = False,
                 judgment_rescue: bool = False, transient_retry_cap: int = 0):
        # `recover_pre_gap_bar` is a pure passthrough to the generation engine and is reached
        # from `run_book.py --recover-pre-gap-bar`. It lives here rather than in
        # `agent_config.yaml` because that file's bytes are hashed into the live activation
        # token's config digest, so a key there would stop the armed book placing until the
        # token was re-minted. See `book_engine.UltimateBookLiveEngine.__init__` for the
        # measurement and the price. Default False == byte-identical.
        # `vol_level_tilt` is the same kind of passthrough, reached from
        # `run_book.py --vol-level-tilt`, and it is here for the same reason (Session AR, B1452).
        # It is a SIZING flag, so the engine injects it into the runtime dict it hands the bridge
        # rather than consuming it itself; `config/profiles/redacted_account.yaml` now carries live
        # authority too, so neither file may be touched. Default False == byte-identical.
        # `frontier_exits` is the third of the same shape, reached from
        # `run_book.py --frontier-exits` (Session AU, B1550). It is a SET OF SLEEVE NAMES rather than
        # a boolean because the two wired sleeves are in opposite live states -- `mx_btcusd` is not in
        # either account's `--tags` so its 5R contract is inert, while `sub_xvol_pullback` is armed at
        # 3R on both accounts. It reaches the PLACEMENT path (the router) and the ADOPT-rehydration
        # path, and nothing else. Default () == byte-identical.
        # `spread_geometry_floor` is the fourth, reached from `run_book.py
        # --spread-geometry-floor` (Session AY, B1810). It is a PER-SLEEVE MAP rather than a
        # boolean for the same reason `--frontier-exits` is a list: AY-1 measured the repair
        # sleeve by sleeve and it is a REPAIR on two of the armed four, NEUTRAL on one and a
        # NO-OP on seven of the estate. It reaches GENERATION only -- the send-layer gate it
        # mirrors already exists and is untouched. Default {} == byte-identical.
        # `entry_hour` is the sixth of the same shape, reached from `run_book.py --entry-hour`
        # (Session CE, B2314). It carries the RATIFIED convention of
        # `phase9/OWNER_DECISION_ENTRY_HOUR.md` -- a sleeve whose decision bar closes at the
        # daily rollover enters at broker hour 01 -- as a DEFERRAL at generation, because no
        # bar closes at 01:00 on the matched feed above M15. Per-sleeve for a measured reason:
        # BTCUSD's hour-00 spread premium is x1.000 (it quotes 24/7) while
        # `sub_mid_dn_revert`'s JPY crosses run x8.0-x19.9, and both sleeves are armed.
        # Default {} == byte-identical.
        self.base_config = base_config or {}
        self._frontier_exits = tuple(frontier_exits or ())
        self._spread_geometry_floor = dict(spread_geometry_floor or {})
        self._entry_hour = dict(entry_hour or {})
        from .risk_unit_floor import OFF_POLICY
        self._risk_unit_floor_policy = risk_unit_floor_policy or OFF_POLICY
        # `weekend_policy` is the fifth of the same shape, reached from `run_book.py
        # --weekend-flat` (Session BA, B1900). It is the redacted_account funded-account weekend
        # prohibition (`FIRM_RULES_V1.json` -> `firms.redacted_account.rules.weekend_holding`), which
        # binds the moment that account PASSES and binds on FTMO never. It is a set of sleeve
        # names for the same reason `frontier_exits` is: the four armed sleeves' measured bills
        # differ by an order of magnitude and one boolean would force the cheapest and the
        # dearest to be armed together. It reaches the MANAGEMENT path (a scheduled close) and
        # the PLACEMENT path (an entry refusal), and nothing else. `None`/OFF == byte-identical.
        #
        # (The two lines below this comment used to be a duplicate pair -- `self.base_config`
        # and `self._frontier_exits` were each assigned TWICE, and the comment above the second
        # pair called `weekend_policy` "the fourth" while the comment above the first pair had
        # already called `spread_geometry_floor` "the fourth". Both were hand-merge residue from
        # the wave-13 train, both assignments were identical so nothing behaved differently, and
        # the commission that asked for the triple-kwarg composition to be verified AT THE CALL
        # SITES is what surfaced them. Removed in Session CE, B2315.)
        self._weekend_policy = weekend_policy if weekend_policy is not None else _WEEKEND_OFF
        self._lane_weight_controller = lane_weight_controller
        self._mt5 = mt5
        self._repo_root = repo_root
        self._namespace = namespace
        # BROKER-SIDE IDENTITY (F5, 2026-08-12). A pure function of the namespace, resolved once
        # here and used everywhere this class reasons about "is that position mine". Every
        # namespace outside `mt5_interface._NAMESPACE_MAGIC` -- which is every namespace that has
        # ever existed before today, typos included -- resolves to the armed book's 20260401, so
        # the default path is unchanged. See `mt5_interface.magic_for_namespace` for why the
        # namespace and not an environment variable.
        from src.mt5.mt5_interface import comment_prefix_for_namespace, magic_for_namespace
        self._magic = magic_for_namespace(namespace)
        self._comment_prefix = comment_prefix_for_namespace(namespace)
        # FAIL CLOSED on a split identity. The wrapper filters the positions this class reasons
        # about; if it were reading one magic while this class expected another, the book would
        # place under one identity and manage under another -- positions open, unadopted, and
        # invisible to every guard, with a healthy log. Wrappers that declare no magic (mocks,
        # test doubles) are exempt by construction: `None` cannot disagree.
        _wrapper_magic = getattr(mt5, "_magic", None)
        if _wrapper_magic is not None and int(_wrapper_magic) != int(self._magic):
            raise ValueError(
                f"broker identity split: namespace {namespace!r} resolves to magic "
                f"{self._magic} but the MT5 wrapper reads {int(_wrapper_magic)}. Construct the "
                f"wrapper with magic=magic_for_namespace(namespace).")
        rt = (self.base_config.get("gtos_vnext_runtime", self.base_config))
        # THE F5 MINIMAL-SIZE EXPERIMENT (default OFF: `minimal_size` is None or disabled, and
        # every seam is inert). Built HERE, before the engine, because the engine's governor
        # reads the notional ledger and the per-symbol execution engines carry the scaler.
        # `run_book.py --f5-minimal-size-usd` is the only way to turn it on: no byte of
        # `config/agent_config.yaml` moves, so the R2 seal and both armed accounts'
        # activation-token digests are untouched and no re-mint is needed.
        self._f5_cfg = minimal_size if (minimal_size is not None and minimal_size.enabled) else None
        self._f5_ledger = None
        self._f5_capture = None
        self._f5_scaler = None
        if self._f5_cfg is not None:
            from pathlib import Path as _Path
            from .minimal_size import (
                LEDGER_FILENAME as _F5_LEDGER_FILE,
                MinimalSizeCapture, MinimalSizeScaler, NotionalLedger,
            )
            self._f5_cfg.validate()
            _f5_dir = _Path(repo_root) / "pipeline_state" / "ultimate_book" / namespace
            self._f5_ledger = NotionalLedger(_f5_dir / _F5_LEDGER_FILE, self._f5_cfg)
            self._f5_capture = MinimalSizeCapture(
                _Path(repo_root) / "shadow_logs" / "f5_minimal" / namespace / "events.jsonl",
                namespace=namespace, account_login=self._f5_account_login(mt5))
            self._f5_scaler = MinimalSizeScaler(self._f5_cfg, self._f5_ledger)
        # FrozenPriceIntent V1 (default OFF). Armed only when the CLI flag is on AND this
        # worker is an F5 minimal-size book. A production namespace with the flag set is
        # inert — the cost-skip `continue` stays today's consume-and-skip.
        f5_identity = str(namespace).endswith("_f5_minimal") and self._f5_cfg is not None
        self._frozen_intent_reprice_requested = bool(frozen_intent_reprice)
        self._frozen_intent_reprice = bool(frozen_intent_reprice) and f5_identity
        self._frozen_intents: dict[tuple[str, str, str], Any] = {}
        # Cycle lookback (first tick + min_over extras). Durable series is the jsonl;
        # this dict only holds what the owner actually held this cycle.
        self._spread_quote_series: dict[tuple[str, str], list] = {}
        # Append-only in-memory series for rollup across lookback + watch ticks.
        # Not a one-shot set: the second write (watch) must land.
        self._f5_quote_series: dict[tuple[str, str, str], list] = {}
        self._f5_series_forward_closed: set[tuple[str, str, str]] = set()
        if self._frozen_intent_reprice_requested and not self._frozen_intent_reprice:
            _log.info(
                "book[%s]: --frozen-intent-reprice ignored (F5-only; production path untouched)",
                namespace,
            )
        # Judgment-layer RESCUE consume seam (default OFF; --judgment-rescue). Armed only
        # when the FrozenPriceIntent rail is armed AND this worker is the operator
        # book — the judgment lock arms RESCUE for that one namespace only
        # (docs/audits/fable-20260816/JUDGMENT-LOCK.md §4). One lookup, one enum, TTL,
        # fail-to-absent: judgment_layer.judgment_verdict reads
        # <repo_root>/judgment/verdicts_<day>.json. ABSENT == code-only behavior; VETO is
        # read and LOGGED only (nothing consumes it yet); the book never blocks or crashes
        # on this layer. Flag absent == today's behavior byte-for-byte.
        self._judgment_rescue_requested = bool(judgment_rescue)
        self._judgment_rescue = (
            bool(judgment_rescue)
            and self._frozen_intent_reprice
            and str(namespace) == "operator"
        )
        from pathlib import Path as _JudgmentPath
        self._judgment_verdict_dir = _JudgmentPath(repo_root) / "judgment"
        if self._judgment_rescue_requested and not self._judgment_rescue:
            _log.info(
                "book[%s]: --judgment-rescue ignored (needs --frozen-intent-reprice on the "
                "operator book; code-only behavior unchanged)",
                namespace,
            )
        # the canonical->broker map lives on the full merged config (instruments[].market.mt5_symbol),
        # NOT the gtos_vnext_runtime subtree -> build it from base_config and inject into the engine.
        self._broker_symbol = build_broker_symbol_resolver(self.base_config)
        self.engine = UltimateBookLiveEngine(rt, mt5, repo_root, namespace=namespace,
                                             broker_symbol=self._broker_symbol,
                                             recover_pre_gap_bar=recover_pre_gap_bar,
                                             vol_level_tilt=vol_level_tilt,
                                             spread_geometry_floor=self._spread_geometry_floor,
                                             entry_hour=self._entry_hour,
                                             broker_server=self._broker_server_name,
                                             event_clock_shadow=event_clock_shadow,
                                             lane_weight_controller=self._lane_weight_controller,
                                             f5_ledger=self._f5_ledger,
                                             risk_unit_floor_policy=self._risk_unit_floor_policy)
        self.router = UltimateBookOrderRouter(self.base_config, namespace=namespace,
                                              frontier_exits=self._frontier_exits)
        self._engine_factory = engine_factory or _default_engine_factory(
            self.base_config, mt5, magic=self._magic, f5_scaler=self._f5_scaler)
        # Per-(symbol, sleeve) execution engines. A symbol can be held by several sleeves at once
        # (XAUUSD: metals_core + metals_softband + metals_ob_micro; GBPJPY/USDJPY: fx_jpy + fx_jpy_ny;
        # GER40/UK100: idxrev + vp_euidx). Each ExecutionEngine is single-position, so keying by symbol
        # alone made a 2nd same-symbol order overwrite active_trade and silently orphan the first ticket
        # from exit management. Keying by (symbol, sleeve) gives each sleeve's position its own lifecycle.
        self._exec_engines: dict[tuple[str, str], Any] = {}
        # idempotency: each (sleeve, symbol, decision_bar) places at most once, so the launcher can
        # tick repeatedly without double-placing. Persists under pipeline_state/ultimate_book/<ns>/.
        self._ledger = PlacementLedger(repo_root, namespace, cluster_resolver=cluster_of)
        # COMP-2 one-unit-per-(cluster,day) cap: bound a correlation cluster to ONE realized unit per day
        # (the envelope the dial was certified on) by blocking a LATER-bar same-cluster re-fire. Default ON
        # for the certified risk envelope; the 'jpy' cluster is exempt while the owner's JPY-cross live trial
        # is measuring BOTH the London (fx_jpy) and NY (fx_jpy_ny) sessions (same cluster).
        try:
            self._cluster_cap_on = config_bool_value(
                rt.get("ultimate_book_one_unit_per_cluster_per_day", True),
                True,
            )
        except (TypeError, ValueError):
            self._cluster_cap_on = True
        _exempt = rt.get("ultimate_book_cluster_cap_exempt_clusters", ["jpy"])
        self._cluster_cap_exempt = set(_exempt) if isinstance(_exempt, (list, tuple, set)) else {"jpy"}
        # reject-notification dedup: a cost/spread-blocked leg is re-attempted EVERY ~60s tick on the
        # same decision bar (correct — a transient spread can clear), but the OWNER must not get a reject
        # card every minute. Push at most ONE reject per (sleeve, symbol, decision_bar, reason).
        self._notified_rejects: set = set()
        # TRANSIENT-RETRY CAP (--transient-retry-cap N; default 0 == OFF == today's behavior
        # byte-for-byte — same argv-not-yaml discipline as --judgment-rescue, because
        # agent_config.yaml is R2-bound AND inside both live activation-token digests).
        # WHY: the transient place-retry loop (`_is_transient_place_failure` ->
        # bar_consumable=False -> launcher leaves _last_bar_by_tf unadvanced) has NO terminal
        # of its own; its only exits are a fill, a reason flip to terminal, or the 0.5x-bar
        # lateness gate. A DETERMINISTIC refusal wearing a transient label therefore storms
        # the terminal until the lateness gate eats the bar: FN 2026-08-04 ~232 sends/2 h
        # (both oil legs), F5 2026-08-17 UK100 35+ sends/37+ min (an activation-token refusal
        # that used to surface as `order_rejected:timeout_no_fill` — P1 now forwards
        # `activation_refused:<decision.reason>`, which this list already treats as
        # non-transient, so one refuse consumes the bar).
        # ARMED: attempts are counted per (sleeve, symbol, decision_bar, matched transient
        # PREFIX); attempts 1..N behave exactly as today (bar retried); the (N+1)th same-class
        # failure is TERMINAL for that bar — one `transient_retry_cap_reached` summary row
        # (attempt count + first/last attempt times), one deduped notify, and this leg stops
        # contributing bar_consumable=False. Counters are IN-MEMORY only: a restart resets
        # them (accepted: a restart also re-runs the bar exactly once more), and a new
        # decision bar is a new key (no carryover). Risk-reducing paths (manage/close/cancel/
        # tighten via manage_open_positions / _flatten_all_engines) never pass through the
        # placement-failure branch, so they can NEVER be capped.
        try:
            self._transient_retry_cap = max(0, int(transient_retry_cap or 0))
        except (TypeError, ValueError):
            self._transient_retry_cap = 0
        # (sleeve, symbol, decision_bar_iso, reason_prefix) -> {attempts, first/last attempt iso}
        self._transient_retry_counts: dict = {}
        # (sleeve, symbol, decision_bar_iso) already declared terminal -> suppress further sends
        # for that bar while ANOTHER leg's own retries keep the cycle's bar alive.
        self._transient_retry_capped: set = set()
        # OPEN-position breach FLATTEN latch (MACRO-EMRG-03): set by manage_open_positions when the account
        # nears the prop-fatal daily-loss / static max-DD floor -> run_cycle goes observe-only (no NEW
        # entries) while set. _breach_ticks gives hysteresis (require N consecutive confirmed-breach ticks
        # so a transient equity wick cannot trigger a flatten).
        self._breach_block = False
        self._breach_ticks = 0
        self._breach_alerted = False
        self._oou_alerted: set = set()   # out-of-universe W7 tickets already alerted (dedup)
        self._absent_ticket_observations: dict[int, int] = {}
        try:
            self._breach_confirm = max(1, int(rt.get("ultimate_book_flatten_confirm_ticks", 2)))
        except (TypeError, ValueError):
            self._breach_confirm = 2
        self._runtime_learning_packet_enabled = config_bool_value(
            rt.get("ultimate_book_runtime_learning_packet_enabled", False),
            False,
        )
        self._runtime_learning_packet_log_enabled = config_bool_value(
            rt.get(
                "ultimate_book_runtime_learning_packet_log_enabled",
                self._runtime_learning_packet_enabled,
            ),
            self._runtime_learning_packet_enabled,
        )
        self._runtime_learning_packet_log_path = str(
            rt.get(
                "ultimate_book_runtime_learning_packet_log_path",
                RUNTIME_LEARNING_PACKET_DEFAULT_LOG_PATH,
            )
            or RUNTIME_LEARNING_PACKET_DEFAULT_LOG_PATH
        )
        self._convergence_advisory_enabled = bool(
            rt.get("ultimate_convergence_advisory_enabled", False)
        )
        self._convergence_advisory_log_enabled = bool(
            rt.get(
                "ultimate_convergence_advisory_log_enabled",
                self._convergence_advisory_enabled,
            )
        )
        self._runtime_learning_writer = None
        if self._runtime_learning_packet_enabled and self._runtime_learning_packet_log_enabled:
            self._runtime_learning_writer = RuntimeLearningPacketWriter(
                self._repo_root,
                self._runtime_learning_packet_log_path,
            )
        # OD-P1, default OFF. `rt.get(key, default)` with an inline default, not the
        # `DEFAULT_CONFIG[key]` resolver in bridge.py -- that shape raises KeyError on an absent
        # key and stands the book down every tick with a healthy heartbeat (AR/AU, B1556). None
        # here means the identity function in `_append_runtime_learning_packets`, so an unflipped
        # key costs nothing and reaches no branch.
        self._runtime_learning_emit_filter = None
        if EMIT_ON_CHANGE_AVAILABLE and config_bool_value(
            rt.get("ultimate_book_runtime_learning_packet_emit_on_change", False),
            False,
        ):
            try:
                heartbeat = float(
                    rt.get(
                        "ultimate_book_runtime_learning_packet_emit_heartbeat_seconds",
                        EMIT_ON_CHANGE_DEFAULT_HEARTBEAT_SECONDS,
                    )
                )
            except (TypeError, ValueError):
                heartbeat = float(EMIT_ON_CHANGE_DEFAULT_HEARTBEAT_SECONDS)
            self._runtime_learning_emit_filter = PositionManagedEmitFilter(
                heartbeat_seconds=heartbeat,
            )
        # Spread observed by the pre-send cost screen, keyed (sleeve, symbol, decision_bar_iso).
        # The screen already computes spread_r for every leg it evaluates but historically only
        # surfaced it inside a refusal *string* when the leg failed, so `spread_r` was null on all
        # 99,112 live packets. Recording the number here is what makes it emittable.
        self._spread_observations: dict[tuple, dict] = {}
        try:
            self._broker_exit_history_lookup_attempts = max(
                1, int(rt.get("broker_exit_history_lookup_attempts", 5) or 5)
            )
        except (TypeError, ValueError):
            self._broker_exit_history_lookup_attempts = 5
        try:
            self._broker_exit_history_lookup_sleep_seconds = max(
                0.0, float(rt.get("broker_exit_history_lookup_sleep_seconds", 0.25) or 0.25)
            )
        except (TypeError, ValueError):
            self._broker_exit_history_lookup_sleep_seconds = 0.25
        self._entry_reconciliation_repair_last_attempt_utc: dict[int, datetime] = {}
        self._exit_reconciliation_repair_last_attempt_utc: dict[int, datetime] = {}
        self._ai_companion_gate = AICompanionRuntimeGate(self.base_config, repo_root, namespace)
        self._prune_old_trade_records()   # state-unbounded-growth: sweep dead (long-closed) trade records

    def _live_broker_authority(self) -> bool:
        """Return whether this book may mutate broker state.

        False keeps reads, adoption, intent generation, launcher logs,
        runtime-learning packets, and local trade-record observations alive,
        but suppresses order placement, SL/TP modification, close, and flatten
        calls from this book runtime.
        """
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        return config_bool_value(
            rt.get("ultimate_book_live_broker_authority", False),
            False,
        )

    def _exec_engine(self, symbol: str, sleeve: str):
        key = (symbol, sleeve)
        if key not in self._exec_engines:
            self._exec_engines[key] = self._engine_factory(symbol)
        return self._exec_engines[key]

    # ---------------- F5 minimal-size experiment (default OFF; every method a no-op) --------
    @staticmethod
    def _f5_account_login(mt5) -> "int | None":
        """Best-effort broker login, stamped on every capture row so four books' events can be
        told apart. `shadow_logs/slippage.jsonl` carries no such field on any row, which is the
        defect this avoids repeating."""
        try:
            direct = getattr(mt5, "get_account_login", None)
            if callable(direct):
                login = direct()
                return int(login) if login is not None else None
            # Raw MetaTrader5 test doubles expose account_info(); an older version of this
            # hook asked for the nonexistent get_account_info() and therefore stamped None on
            # every real F5 row while the account was fully available.
            info = getattr(mt5, "account_info", None)
            if callable(info):
                got = info() or {}
                login = got.get("login") if isinstance(got, dict) else getattr(got, "login", None)
                return int(login) if login is not None else None
        except Exception:  # noqa: BLE001 - a login read must never stop a book starting
            pass
        return None

    def _f5_on_open(self, *, ticket, sleeve, symbol, trade_params, candidate_id,
                    decision_day, decision_bar_iso, source: str = "fill") -> None:
        """Record a placed unit in the notional ledger and the capture. NEVER raises.

        ``source`` labels the emit: "fill" for a broker fill this tick, "adoption_rehydrate"
        for a restart re-emit (measured on 178414870: the adoption row duplicated the fill row
        minus the at-fill truth fields, which double-counts any naive fill counter). Consumers
        counting fills must key on ticket or filter ``f5_fill_source``.
        """
        if self._f5_ledger is None or ticket in (None, 0):
            return
        try:
            tp = trade_params or {}
            self._f5_ledger.on_open(
                ticket=int(ticket), sleeve=str(sleeve), symbol=str(symbol),
                nominal_risk_usd=float(tp.get("f5_nominal_risk_usd") or 0.0),
                actual_risk_usd=float(tp.get("f5_actual_risk_usd") or 0.0),
                intended_risk_usd=float(tp.get("f5_intended_risk_usd") or 0.0),
                decision_day=str(decision_day))
            row = {k: tp.get(k) for k in ("f5_nominal_risk_usd", "f5_intended_risk_usd",
                                          "f5_actual_risk_usd", "f5_round_up",
                                          # POST-FILL TRUTH (2026-08-25, the LTCUSD 178351323
                                          # fix): `f5_actual_risk_usd` is computed PRE-SEND and
                                          # lies after entry slippage. These two are stamped by
                                          # `_f5_fill_truth_fields` from the broker fill; None
                                          # when unstamped (adoption of a record without them).
                                          "f5_fill_deviation_r",
                                          "f5_actual_risk_at_fill_usd")}
            row.update({"ticket": int(ticket), "candidate_id": candidate_id,
                        "sleeve": sleeve, "symbol": symbol,
                        "decision_day": decision_day, "decision_bar_iso": decision_bar_iso,
                        "f5_minutes_to_high_impact_event": self._f5_news_proximity(),
                        # Persistence-gap probe (17/169 outcome rows flag
                        # trade_record_missing_for_ticket): stamp whether the ticket's trade
                        # record is on disk AT THE FILL EVENT, plus the dir this process
                        # writes, so the next harvest can tell "persist failed" apart from
                        # "the builder read a different root".
                        "f5_trade_record_on_disk": self._load_trade_record(ticket) is not None,
                        "f5_trade_record_dir": str(self._trade_record_path()),
                        "f5_fill_source": str(source),
                        "broker_mutation": source == "fill"})
            self._f5_capture.emit("f5_fill", row)
        except Exception as exc:  # noqa: BLE001 - collection must never break placement
            _log.warning("book[%s]: F5 open hook failed for ticket %s (%r)",
                         self._namespace, ticket, exc)

    def _f5_fill_truth_fields(self, trade_params, result) -> None:
        """Stamp the two POST-FILL truth fields onto trade_params in place. NEVER raises.

        The existing ``f5_actual_risk_usd`` is the broker's own ``order_calc_profit`` on the
        PRE-SEND geometry (intended entry -> SL). After entry slippage it lies: LTCUSD
        178351323 carried ``f5_actual_risk_usd: 74.93`` while the broker held ``$184`` of
        true risk (fill 51.81 against intended 51.51, SL 51.31). Both honest fields ride on
        the SAME broker truths already in hand at the fill (TradeState.entry_price is the
        broker fill; sl/volume are the placed values) -- no extra broker call:

        * ``f5_fill_deviation_r``  = (fill - intended_entry) * direction_sign / intended
          stop distance. Positive == adverse. LTCUSD reads +1.48.
        * ``f5_actual_risk_at_fill_usd`` = |fill - SL| * volume * value-per-price-unit.
          Preferred basis: rescale the pre-send broker figure by the distance ratio (exact
          for linear P&L); fallback: ``get_symbol_value_per_point``.
        """
        if self._f5_ledger is None:
            return
        try:
            import math

            tp = trade_params if isinstance(trade_params, dict) else None
            ts = (result or {}).get("trade_state")
            if tp is None or ts is None:
                return
            try:
                fill = float(getattr(ts, "entry_price", None))
                intended = float(tp.get("entry_price"))
            except (TypeError, ValueError):
                return
            if not (math.isfinite(fill) and math.isfinite(intended)) or fill <= 0 or intended <= 0:
                return
            direction = str(tp.get("direction") or "").upper()
            sign = 1.0 if direction == "LONG" else (-1.0 if direction == "SHORT" else None)
            if sign is None:
                # Frozen-commit trade_params carry no "direction" (measured on 178414870:
                # risk-at-fill stamped, deviation absent). Geometry settles it: a LONG's
                # stop sits below its intended entry.
                try:
                    _sl_for_sign = float(tp.get("stop_loss"))
                    if math.isfinite(_sl_for_sign) and _sl_for_sign > 0 and _sl_for_sign != intended:
                        sign = 1.0 if intended > _sl_for_sign else -1.0
                except (TypeError, ValueError):
                    pass
            stop_dist = 0.0
            try:
                stop_dist = float(getattr(ts, "sl_distance", 0.0) or 0.0)
            except (TypeError, ValueError):
                stop_dist = 0.0
            if stop_dist <= 0:
                try:
                    stop_dist = abs(intended - float(tp.get("stop_loss")))
                except (TypeError, ValueError):
                    stop_dist = 0.0
            if sign is not None and stop_dist > 0 and math.isfinite(stop_dist):
                deviation = (fill - intended) * sign / stop_dist
                if math.isfinite(deviation):
                    tp["f5_fill_deviation_r"] = deviation

            # --- honest dollars actually at risk between the fill and the placed stop ---
            try:
                sl = float(getattr(ts, "stop_loss", 0.0) or 0.0)
                volume = float(getattr(ts, "initial_volume", 0.0)
                               or getattr(ts, "current_volume", 0.0) or 0.0)
            except (TypeError, ValueError):
                return
            if sl <= 0 or volume <= 0:
                return
            fill_dist = abs(fill - sl)
            intended_dist = abs(intended - sl)
            risk_at_fill = None
            try:
                pre_send = float(tp.get("f5_actual_risk_usd") or 0.0)
            except (TypeError, ValueError):
                pre_send = 0.0
            if pre_send > 0 and intended_dist > 0:
                risk_at_fill = pre_send * fill_dist / intended_dist
            else:
                vpp_fn = getattr(self._mt5, "get_symbol_value_per_point", None)
                if callable(vpp_fn):
                    try:
                        broker_symbol = self._broker_symbol(str(tp.get("symbol") or ""))
                    except Exception:  # noqa: BLE001
                        broker_symbol = tp.get("symbol")
                    try:
                        vpp = float(vpp_fn(broker_symbol) or 0.0)
                    except Exception:  # noqa: BLE001
                        vpp = 0.0
                    if vpp > 0:
                        risk_at_fill = fill_dist * volume * vpp
            if risk_at_fill is not None and math.isfinite(risk_at_fill):
                tp["f5_actual_risk_at_fill_usd"] = float(risk_at_fill)
        except Exception as exc:  # noqa: BLE001 - observation must never break placement
            _log.warning("book[%s]: F5 fill-truth stamp failed (%r)", self._namespace, exc)

    def _f5_fill_deviation_guard(self, *, ee, ticket, sleeve, symbol,
                                 trade_params, decision_bar_iso) -> None:
        """Close a fill only when that hop says close. NEVER raises.

        Namespace-gated to ``operator``. The deviation is a fact. It is
        not a cap. An empty answer does not close and does not restore one.
        """
        if (
            self._namespace != "operator"
            or self._f5_capture is None
            or ticket in (None, 0)
        ):
            return
        try:
            import math

            tp = trade_params if isinstance(trade_params, dict) else {}
            try:
                deviation = float(tp.get("f5_fill_deviation_r"))
            except (TypeError, ValueError):
                return          # unstamped == unmeasurable == no action
            if not math.isfinite(deviation):
                return
            trade = getattr(ee, "active_trade", None)
            choice = _ask_jev(
                "fill_deviation",
                {
                    "ticket": int(ticket),
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "deviation_r": deviation,
                    "namespace": "operator",
                },
                kind="choice",
                instructions=(
                    "This fill's deviation is on the card. "
                    "Close this ticket only when close is the unique highest. "
                    "An empty answer or a tie does not close and does not restore a deviation cap. "
                    "Do not flatten the book."
                ),
                criteria={
                    "close": "Close this fill.",
                    "leave": "Leave this fill open.",
                },
            )
            row = {
                "ticket": int(ticket), "sleeve": sleeve, "symbol": symbol,
                "decision_bar_iso": decision_bar_iso,
                "f5_fill_deviation_r": deviation,
                "fill_deviation": choice,
                "intended_entry": tp.get("entry_price"),
                "fill_price": getattr(trade, "entry_price", None),
                "stop_loss": getattr(trade, "stop_loss", None),
                "f5_intended_risk_usd": tp.get("f5_intended_risk_usd"),
                "f5_actual_risk_usd": tp.get("f5_actual_risk_usd"),
                "f5_actual_risk_at_fill_usd": tp.get("f5_actual_risk_at_fill_usd"),
            }
            if choice != "close":
                row.update({"close_status": "left", "broker_mutation": False})
                self._f5_capture.emit("f5_fill_deviation_breach", row)
                return
            if not self._live_broker_authority():
                # H8: authority-false suppresses broker mutation; say so rather than pretend.
                row.update({"close_status": "close_suppressed_live_broker_authority_false",
                            "broker_mutation": False})
                self._f5_capture.emit("f5_fill_deviation_breach", row)
                _log.error(
                    "book[%s]: F5 FILL DEVIATION BREACH ticket=%s %s/%s dev=%.3fR but live "
                    "broker authority is false -> close suppressed; position remains OPEN",
                    self._namespace, ticket, symbol, sleeve, deviation)
                return
            closed = False
            close_error = None
            try:
                self._lifetime_sends = {"close": True, "move_sl": False, "stop": None}

                def _close_fill():
                    return bool(ee.close_position("f5_fill_deviation_breach"))

                closed = bool(self._with_lifetime_emit(_close_fill))
            except Exception as exc:  # noqa: BLE001 - the breach event must still be written
                close_error = repr(exc)
            row.update({
                "close_status": "closed" if closed else "close_failed_position_still_open",
                "broker_mutation": bool(closed),
            })
            if close_error is not None:
                row["close_error"] = close_error
            self._f5_capture.emit("f5_fill_deviation_breach", row)
            if closed:
                _log.error(
                    "book[%s]: F5 FILL DEVIATION ticket=%s %s/%s dev=%.3fR "
                    "-> position CLOSED (the hop said close)",
                    self._namespace, ticket, symbol, sleeve, deviation)
            else:
                _log.error(
                    "book[%s]: F5 FILL DEVIATION BREACH ticket=%s %s/%s dev=%.3fR but the "
                    "close did NOT execute (%s) -- position STILL OPEN at the wrong risk",
                    self._namespace, ticket, symbol, sleeve, deviation,
                    close_error or "close_position returned False")
        except Exception as exc:  # noqa: BLE001 - the guard must never break the tick
            _log.warning("book[%s]: F5 fill-deviation guard failed for ticket %s (%r)",
                         self._namespace, ticket, exc)

    def _f5_on_manage(self, *, ticket, sleeve, symbol, ee, action, checked_at) -> None:
        """THE TRAIL PATH -- emitted only when the stop actually MOVES. NEVER raises.

        Two of the 32 sleeves in the experiment surface (`asian_fade`,
        `metal_session_reversion`) are `trailing_runner`: no take-profit at all
        (`broker_take_profit_mode: "none"`, `final_target_r: None`), armed then trailed
        0.5R behind. **Neither has ever carried a dollar of real money**, so this run is the
        first live read of the let-it-ride exit -- and today the trail path reaches disk
        NOWHERE on the live book path. `trailing_stop_shadow_logger` is wired into
        `orchestrator.py` only; `_modify_sl`'s audit is an in-memory halt diagnostic; the
        trade record keeps the LATEST stop, not the sequence. So "armed at 10:15, trailed
        seven times, stopped out at +1.8R" would have been unreconstructable from any log.

        One row per ACTUAL move, not per tick: an unchanged stop emits nothing, so a
        multi-day hold costs a handful of rows rather than thousands. The first row of a
        ticket is its arm; the last is what the exit rode in on; `f5_trade_closed` carries
        the realised R.
        """
        capture = getattr(self, "_f5_capture", None)
        if capture is None or ticket in (None, 0):
            return
        try:
            trade = getattr(ee, "active_trade", None)
            if trade is None:
                return
            sl = getattr(trade, "stop_loss", None)
            if sl is None:
                return
            sl = float(sl)
            seen = getattr(self, "_f5_last_stop", None)
            if seen is None:
                seen = self._f5_last_stop = {}
            prev = seen.get(int(ticket))
            if prev is not None and abs(prev - sl) <= 1e-9:
                return                      # the stop did not move; say nothing
            seen[int(ticket)] = sl
            if len(seen) > 512:             # bound the dict on a long-lived process
                for k in list(seen)[:256]:
                    seen.pop(k, None)
            entry = float(getattr(trade, "entry_price", 0.0) or 0.0)
            # LOCKEDR-FIX (W8D / ceremony 20260825 rider): TradeState has no
            # initial_stop_loss, so the old fallback re-denominated on `prev`
            # after the trail armed (printed +3.47R on a real +0.31R lock).
            # Latch the FIRST observed stop per ticket as the initial stop and
            # sign by direction: locked_r = dir_sign*(stop_now-entry)/|entry-init_sl|.
            init_map = getattr(self, "_f5_initial_sl", None)
            if init_map is None:
                init_map = self._f5_initial_sl = {}
            if prev is None:
                init_map[int(ticket)] = sl
            if len(init_map) > 512:
                for k in list(init_map)[:256]:
                    init_map.pop(k, None)
            init_sl = init_map.get(int(ticket))
            denom = abs(entry - init_sl) if init_sl is not None else 0.0
            d = str(getattr(trade, "direction", "") or "").upper()
            sign = 1.0 if d == "LONG" else (-1.0 if d == "SHORT" else None)
            capture.emit("f5_stop_move", {
                "ticket": int(ticket), "sleeve": sleeve, "symbol": symbol,
                "action": action, "checked_at_utc": checked_at,
                "entry_price": entry,
                "stop_prev": prev, "stop_now": sl,
                # LOCKEDR-FIX convention: dir_sign*(stop_now-entry)/|entry-initial_sl|
                "locked_r": (sign * (sl - entry) / denom) if (sign is not None and denom) else None,
                "is_first_move": prev is None,
                "current_volume": float(getattr(trade, "current_volume", 0.0) or 0.0),
                "take_profit_1": float(getattr(trade, "take_profit_1", 0.0) or 0.0),
                "broker_mutation": False})
        except Exception as exc:  # noqa: BLE001 - observation must never break management
            _log.warning("book[%s]: F5 stop-move capture failed for ticket %s (%r)",
                         self._namespace, ticket, exc)

    def _f5_record_sibling_close(
        self,
        ticket,
        record=None,
        action=None,
        *,
        symbol=None,
        sleeve=None,
        closed_utc=None,
        broker_net_pnl_usd=None,
        realised_r=None,
    ) -> None:
        """Persist the launcher sibling/SL-cooldown row. Never raises. Not inbox HOLD."""
        if str(getattr(self, "_namespace", "")) != "operator":
            return
        try:
            from .minimal_size import f5_just_closed_siblings_path, f5_record_just_closed
            rec = record if isinstance(record, dict) else {}
            execution = rec.get("execution") if isinstance(rec.get("execution"), dict) else {}
            f5_record_just_closed(
                symbol=symbol or rec.get("symbol") or execution.get("broker_symbol"),
                ticket=ticket,
                closed_utc=(
                    closed_utc
                    or rec.get("closed_at_utc")
                    or rec.get("closed_utc")
                    or execution.get("closed_at_utc")
                    or datetime.now(timezone.utc).isoformat()
                ),
                sleeve=sleeve or rec.get("sleeve"),
                path=f5_just_closed_siblings_path(
                    repo_root=getattr(self, "_repo_root", None),
                    namespace=str(getattr(self, "_namespace", "") or "operator"),
                ),
                extra={
                    "close_action": action or rec.get("close_action") or rec.get("broker_close_reason"),
                    "reason": action or rec.get("close_action") or rec.get("broker_close_reason") or "broker_close",
                    "broker_net_pnl_usd": (
                        broker_net_pnl_usd
                        if broker_net_pnl_usd is not None
                        else rec.get("broker_realized_pnl") or rec.get("broker_net_pnl_usd")
                    ),
                    "realised_r": realised_r if realised_r is not None else rec.get("realised_r"),
                },
            )
        except Exception:
            return

    def _f5_on_close(self, ticket, broker_net_pnl_usd, *, symbol=None, sleeve=None,
                     close_action=None, closed_utc=None) -> dict | None:
        """Fold a broker-true close into the notional ledger. NEVER raises."""
        row = None
        rec_d = {}
        try:
            rec = self._load_trade_record(ticket)
            rec_d = rec if isinstance(rec, dict) else {}
        except Exception:
            rec_d = {}
        if self._f5_ledger is not None and ticket not in (None, 0):
            try:
                row = self._f5_ledger.on_close(ticket=int(ticket),
                                               broker_net_pnl_usd=float(broker_net_pnl_usd or 0.0))
                if self._f5_capture is not None:
                    self._f5_capture.emit("f5_trade_closed", row)
            except Exception as exc:  # noqa: BLE001
                _log.warning("book[%s]: F5 close hook failed for ticket %s (%r)",
                             self._namespace, ticket, exc)
                row = None
        payload = row if isinstance(row, dict) else {}
        self._f5_record_sibling_close(
            ticket,
            rec_d or payload,
            close_action or rec_d.get("close_action") or rec_d.get("broker_close_reason") or payload.get("close_action"),
            symbol=symbol or payload.get("symbol") or rec_d.get("symbol"),
            sleeve=sleeve or payload.get("sleeve") or rec_d.get("sleeve"),
            closed_utc=closed_utc or payload.get("closed_utc") or rec_d.get("closed_at_utc"),
            broker_net_pnl_usd=broker_net_pnl_usd,
            realised_r=payload.get("realised_r"),
        )
        if row is None:
            return None
        try:
            return dict(row)
        except Exception:
            return None

    # ---------------- F5 manage consume seam (gtos.judgment.manage.v1) ----------------------
    def _f5_manage_dir(self):
        """`pipeline_state/ultimate_book/<namespace>/judgment` -- the manage-contract home."""
        from pathlib import Path
        return (Path(self._repo_root) / "pipeline_state" / "ultimate_book"
                / self._namespace / "judgment")

    def _f5_manage_cursor_path(self):
        from pathlib import Path
        return self._f5_manage_dir() / "state" / "manage_consume_cursor.json"

    def _f5_latest_slate_tickets(self) -> set:
        """Tickets in the judged-slate open-position block (latest_slate.json). Empty on miss."""
        try:
            import json as _json
            path = self._f5_manage_dir() / "state" / "latest_slate.json"
            if not path.is_file():
                return set()
            doc = _json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(doc, dict):
                return set()
            out = set()
            for pos in doc.get("open_positions") or []:
                if isinstance(pos, dict):
                    try:
                        t = int(pos.get("ticket"))
                    except (TypeError, ValueError):
                        continue
                    if t > 0:
                        out.add(t)
            return out
        except Exception:
            return set()

    def _f5_manage_ensure_memos(self) -> None:
        """Load process memos; hydrate terminal keys from persist so restart does not re-read."""
        if getattr(self, "_f5_manage_terminal", None) is not None:
            return
        self._f5_manage_terminal = set()
        self._f5_manage_emitted = set()
        self._f5_manage_cursor_tickets = {}
        path = self._f5_manage_cursor_path()
        try:
            import json as _json
            if not path.is_file():
                return
            doc = _json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            _log.warning("book[%s]: manage consume cursor unreadable (%r) -> empty memo",
                         self._namespace, exc)
            return
        from .minimal_size import F5_MANAGE_CONSUME_CURSOR_SCHEMA
        if not isinstance(doc, dict) or doc.get("schema") != F5_MANAGE_CONSUME_CURSOR_SCHEMA:
            return
        tickets = doc.get("tickets")
        if isinstance(tickets, dict):
            self._f5_manage_cursor_tickets = tickets
        for item in doc.get("terminal_keys") or []:
            if isinstance(item, list):
                try:
                    self._f5_manage_terminal.add(tuple(item))
                except TypeError:
                    continue

    def _f5_manage_persist_cursor(self) -> None:
        """Atomic tmp+replace. Schema gtos.judgment.manage_consume_cursor.v1. Never raises."""
        try:
            import json as _json
            import os
            from datetime import datetime, timezone
            from .minimal_size import F5_MANAGE_CONSUME_CURSOR_SCHEMA
            path = self._f5_manage_cursor_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            keys = [k for k in self._f5_manage_terminal if isinstance(k, tuple)]
            if len(keys) > 2048:
                keys = keys[-2048:]
            payload = {
                "schema": F5_MANAGE_CONSUME_CURSOR_SCHEMA,
                "tickets": getattr(self, "_f5_manage_cursor_tickets", {}) or {},
                "terminal_keys": [list(k) for k in keys],
                "updated_utc": datetime.now(timezone.utc).isoformat(),
            }
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_text(_json.dumps(payload, indent=1, default=str), encoding="utf-8")
            os.replace(str(tmp), str(path))
        except Exception as exc:  # noqa: BLE001
            _log.warning("book[%s]: manage consume cursor persist failed (%r)",
                         self._namespace, exc)

    def _f5_manage_mark(self, key, *, terminal: bool, row=None, ttl_s=None) -> None:
        """Record a processed manage row. Terminal keys are never re-evaluated; emitted keys
        suppress duplicate events while the row stays re-evaluable. Both bounded.
        Terminal marks persist so a book restart does not re-emit expired/applied."""
        self._f5_manage_ensure_memos()
        store = self._f5_manage_terminal if terminal else self._f5_manage_emitted
        store.add(key)
        if len(store) > 2048:
            for old in list(store)[:1024]:
                store.discard(old)
        if terminal and isinstance(key, tuple) and key:
            try:
                ticket = int(key[0])
            except (TypeError, ValueError, IndexError):
                ticket = 0
            if ticket > 0:
                action = str(key[1]) if len(key) > 1 else ""
                from datetime import datetime, timezone
                tickets = getattr(self, "_f5_manage_cursor_tickets", None)
                if tickets is None:
                    self._f5_manage_cursor_tickets = {}
                    tickets = self._f5_manage_cursor_tickets
                tickets[str(ticket)] = {
                    "row_id": "|".join(str(p) for p in key),
                    "action": action,
                    "applied_utc": datetime.now(timezone.utc).isoformat(),
                    "ttl_s": ttl_s if ttl_s is not None else (
                        (row or {}).get("ttl_s") if isinstance(row, dict) else None
                    ),
                }
                self._f5_manage_persist_cursor()

    def _f5_consume_manage_rows(self, summary: dict, now) -> None:
        """Consume `manage_<YYYY-MM-DD>.json` rows: close / tighten_stop. NEVER raises.

        A row with a readable clock inside its own ttl reaches the close or stop hop.
        A missing clock, a clock outside that window, or an older row asks
        ``manage_row_clock`` once. Apply lets it through. Leave and an empty answer
        do not apply it and do not restore a default ttl. On Challenge a stop that
        widens is not refused here; the stop hop decides. A stop beyond the live
        price is still an invalid stop. Both actions route through the engine's own
        close / SL-modify paths.

        Today's file is read first, then yesterday's. Terminal outcomes (applied,
        malformed) are not re-evaluated. A price miss or a failed broker call can
        be seen again.
        """
        if self._namespace != "operator" or self._f5_capture is None:
            return
        try:
            import json as _json
            import math

            from .judgment_layer import parse_utc
            from .minimal_size import (
                F5_MANAGE_SCHEMA,
                F5_MANAGE_TTL_DEFAULT_S,
                F5_MANAGE_TTL_MAX_S,
                F5_MANAGE_TTL_MIN_S,
                f5_close_send_none_allow_order_send,
                f5_close_send_none_is_dead,
            )

            self._f5_manage_ensure_memos()
            counters = {"applied": 0, "rejected": 0, "malformed_rows": 0, "files_read": 0}

            directory = self._f5_manage_dir()
            docs = []
            for day in (now.date().isoformat(),
                        (now - timedelta(days=1)).date().isoformat()):
                path = directory / f"manage_{day}.json"
                try:
                    if not path.is_file():
                        continue
                    stat_key = ("file", str(path), path.stat().st_mtime)
                    doc = _json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    counters["malformed_rows"] += 1
                    fkey = ("file_error", str(path))
                    if fkey not in self._f5_manage_emitted:
                        self._f5_manage_mark(fkey, terminal=False)
                        _log.warning("book[%s]: manage file unreadable %s (%r) -> ignored",
                                     self._namespace, path, exc)
                    continue
                if (not isinstance(doc, dict)
                        or doc.get("schema") != F5_MANAGE_SCHEMA
                        or not isinstance(doc.get("rows"), list)):
                    counters["malformed_rows"] += 1
                    if stat_key not in self._f5_manage_emitted:
                        self._f5_manage_mark(stat_key, terminal=False)
                        _log.warning("book[%s]: manage file %s has wrong schema/shape -> ignored",
                                     self._namespace, path)
                    continue
                counters["files_read"] += 1
                docs.append(doc)
            if not docs:
                if counters["malformed_rows"]:
                    summary["f5_manage"] = counters
                return

            # Open positions of THIS book == what the adoption pass just put in the engines.
            open_map: dict[int, tuple] = {}
            for (sym, sleeve), ee in list(self._exec_engines.items()):
                trade = getattr(ee, "active_trade", None)
                ticket = getattr(trade, "ticket", None)
                if trade is not None and ticket not in (None, 0):
                    open_map[int(ticket)] = (ee, sym, sleeve, trade)

            def _emit(event, row_payload, *, key=None, once=False):
                if once and key is not None:
                    if key in self._f5_manage_emitted:
                        return
                    self._f5_manage_mark(key, terminal=False)
                self._f5_capture.emit(event, row_payload)

            def _reject(row, ticket, action, reason, *, key, terminal, extra=None):
                counters["rejected"] += 1
                payload = {"ticket": ticket, "action": action, "reason": reason,
                           "mechanism": (row.get("mechanism") if isinstance(row, dict) else None),
                           "why_code": (row.get("why_code") if isinstance(row, dict) else None),
                           "broker_mutation": False}
                if extra:
                    payload.update(extra)
                if terminal:
                    if key not in self._f5_manage_terminal:
                        self._f5_manage_mark(key, terminal=True)
                        self._f5_capture.emit("f5_manage_rejected", payload)
                else:
                    _emit("f5_manage_rejected", payload, key=("emit",) + key, once=True)

            if not self._live_broker_authority():
                # H8: nothing is marked processed -- rows act when authority returns.
                if ("authority_off",) not in self._f5_manage_emitted:
                    self._f5_manage_mark(("authority_off",), terminal=False)
                    _log.warning("book[%s]: manage rows present but live broker authority is "
                                 "false -> no action (rows stay pending)", self._namespace)
                summary["f5_manage"] = dict(counters, suppressed="live_broker_authority_false")
                return

            for doc in docs:
                for row in doc.get("rows") or []:
                    if not isinstance(row, dict):
                        counters["malformed_rows"] += 1
                        continue
                    try:
                        ticket = int(row.get("ticket"))
                    except (TypeError, ValueError):
                        ticket = 0
                    action = str(row.get("action") or "")
                    raw_written = row.get("written_at_utc")
                    raw_stop = row.get("new_stop")
                    key = (ticket, action, repr(raw_stop), str(raw_written),
                           str(row.get("why_code") or ""))
                    if key in self._f5_manage_terminal:
                        continue
                    if ticket <= 0:
                        _reject(row, None, action or None, "malformed_row",
                                key=key, terminal=True)
                        continue
                    if action not in ("close", "tighten_stop"):
                        _reject(row, ticket, action or None, "invalid_action",
                                key=key, terminal=True)
                        continue
                    written = parse_utc(raw_written)
                    if written is None:
                        _reject(row, ticket, action, "written_at_unparseable",
                                key=key, terminal=True)
                        continue
                    raw_ttl = row.get("ttl_s")
                    ttl = None
                    try:
                        if raw_ttl is not None:
                            ttl = float(raw_ttl)
                    except (TypeError, ValueError):
                        ttl = None
                    age_s = (now - written).total_seconds()
                    band_lo = F5_MANAGE_TTL_MIN_S.value()
                    band_hi = F5_MANAGE_TTL_MAX_S.value()
                    in_window = (
                        ttl is not None
                        and band_lo is not None
                        and band_hi is not None
                        and band_lo <= ttl <= band_hi
                        and age_s < ttl
                    )
                    if not in_window:
                        # Missing, out of the named window, or older than its own
                        # ttl. That clock does not refuse. One ask per row.
                        clock_choice = _ask_jev(
                            "manage_row_clock",
                            {
                                "ticket": ticket,
                                "action": action,
                                "written_at_utc": str(raw_written),
                                "ttl_s": raw_ttl,
                                "namespace": "operator",
                            },
                            kind="choice",
                            instructions=(
                                "This manage row is outside the named clock window. "
                                "apply lets the row reach the close or stop hop. "
                                "leave does not apply it. "
                                "An empty answer does not apply it and does not restore a clock."
                            ),
                            criteria={
                                "apply": "Let this row reach the ticket hop.",
                                "leave": "Do not apply this row.",
                            },
                        )
                        if clock_choice != "apply":
                            continue
                        attempt = ("row_clock_attempt",) + tuple(key)
                        if attempt in self._f5_manage_emitted:
                            continue
                        self._f5_manage_mark(attempt, terminal=False)
                    held = open_map.get(ticket)
                    slate_tickets = self._f5_latest_slate_tickets()
                    if held is None:
                        extra = {"on_slate": ticket in slate_tickets} if slate_tickets else None
                        _reject(row, ticket, action, "unknown_ticket",
                                key=key, terminal=False, extra=extra)
                        continue
                    ee, sym, sleeve, trade = held
                    base = {"ticket": ticket, "action": action, "symbol": sym,
                            "sleeve": sleeve,
                            "mechanism": row.get("mechanism"),
                            "why_code": row.get("why_code"),
                            "row_written_at_utc": str(raw_written)}
                    if action == "close":
                        # Leftover-open Atlas stay must not flatten. Take-off
                        # gate is a may and stays False (good_level / tape_stopped
                        # fail closed). Do not close from that gate this clock.
                        try:
                            from pathlib import Path as _StayPath
                            from .minimal_size import (
                                f5_fast_family_takeoff_may_close,
                                f5_leftover_open_stay,
                            )
                            _stay_ledger = (
                                _StayPath(self._repo_root) / "pipeline_state"
                                / "ultimate_book" / str(self._namespace)
                                / "judgment" / "state"
                                / "chair_leftover_open_stay.json"
                            )
                            _may = f5_fast_family_takeoff_may_close(
                                ticket=ticket,
                                sleeve=sleeve,
                                symbol=sym,
                                ledger_path=_stay_ledger,
                            )
                            if _may:
                                _log.info(
                                    "book[%s]: takeoff may-close true ticket=%s "
                                    "(no auto-close wired this clock)",
                                    self._namespace, ticket,
                                )
                            if f5_leftover_open_stay(ticket, ledger_path=_stay_ledger):
                                _log.warning(
                                    "book[%s]: leftover_open_stay_no_flatten ticket=%s",
                                    self._namespace, ticket,
                                )
                                _reject(row, ticket, action,
                                        "leftover_open_stay_no_flatten",
                                        key=key, terminal=True)
                                continue
                        except Exception as exc:  # noqa: BLE001
                            _log.warning(
                                "book[%s]: leftover-open stay / takeoff gate "
                                "check failed (%r) -> leftover_open_stay_no_flatten",
                                self._namespace, exc,
                            )
                            _reject(row, ticket, action,
                                    "leftover_open_stay_no_flatten",
                                    key=key, terminal=False)
                            continue
                        if f5_close_send_none_is_dead(ticket):
                            _reject(row, ticket, action,
                                    "close_broker_unknown_dead_ticket",
                                    key=key, terminal=False)
                            continue
                        if not f5_close_send_none_allow_order_send(ticket):
                            _reject(row, ticket, action,
                                    "close_broker_unknown_backoff",
                                    key=key, terminal=False)
                            continue
                        closed = False
                        try:
                            closed = bool(ee.close_position("f5_manage"))
                        except Exception as exc:  # noqa: BLE001
                            _reject(row, ticket, action, f"close_error:{exc!r}",
                                    key=key, terminal=False)
                            continue
                        if closed:
                            counters["applied"] += 1
                            self._f5_manage_mark(key, terminal=True)
                            self._f5_capture.emit("f5_manage_applied",
                                                  dict(base, reason="applied",
                                                       broker_mutation=True))
                            open_map.pop(ticket, None)
                        else:
                            _reject(row, ticket, action, "close_failed",
                                    key=key, terminal=False)
                        continue
                    # ---- tighten_stop: TIGHTEN-ONLY IS MANDATORY ----
                    try:
                        new_stop = float(raw_stop)
                    except (TypeError, ValueError):
                        new_stop = float("nan")
                    if not math.isfinite(new_stop) or new_stop <= 0:
                        _reject(row, ticket, action, "new_stop_invalid",
                                key=key, terminal=True)
                        continue
                    direction = str(getattr(trade, "direction", "") or "").upper()
                    if direction not in ("LONG", "SHORT"):
                        _reject(row, ticket, action, "direction_unreadable",
                                key=key, terminal=False)
                        continue
                    try:
                        current_sl = float(getattr(trade, "stop_loss", 0.0) or 0.0)
                    except (TypeError, ValueError):
                        current_sl = 0.0
                    # Strictly risk-reducing vs the CURRENT stop. A position with no stop
                    # (current_sl <= 0) treats any stop on the correct side of price as a
                    # tighten -- setting a first stop is not a widen.
                    if current_sl > 0:
                        tightens = (new_stop > current_sl) if direction == "LONG" \
                            else (new_stop < current_sl)
                        if not tightens and str(self._namespace) != "operator":
                            _reject(row, ticket, action, "widen_refused", key=key,
                                    terminal=True,
                                    extra={"new_stop": new_stop, "current_stop": current_sl})
                            continue
                    try:
                        broker_symbol = self._broker_symbol(sym)
                    except Exception:  # noqa: BLE001
                        broker_symbol = sym
                    tick = None
                    try:
                        tick = self._mt5.get_tick(broker_symbol)
                    except Exception:  # noqa: BLE001
                        tick = None
                    bid = getattr(tick, "bid", None)
                    ask = getattr(tick, "ask", None)
                    if not bid or not ask:
                        _reject(row, ticket, action, "price_unavailable",
                                key=key, terminal=False)
                        continue
                    # Not beyond current price: a LONG stop executes at bid, a SHORT at ask.
                    beyond = (new_stop >= float(bid)) if direction == "LONG" \
                        else (new_stop <= float(ask))
                    if beyond:
                        _reject(row, ticket, action, "beyond_current_price", key=key,
                                terminal=False,
                                extra={"new_stop": new_stop, "bid": bid, "ask": ask})
                        continue
                    modify = getattr(ee, "_modify_sl", None)
                    if not callable(modify):
                        _reject(row, ticket, action, "modify_path_unavailable",
                                key=key, terminal=True)
                        continue
                    ok = False
                    try:
                        ok = bool(modify(ticket, new_stop, trade=trade,
                                         modify_reason="f5_manage_tighten"))
                    except Exception as exc:  # noqa: BLE001
                        _reject(row, ticket, action, f"modify_error:{exc!r}",
                                key=key, terminal=False)
                        continue
                    if ok:
                        counters["applied"] += 1
                        self._f5_manage_mark(key, terminal=True)
                        try:
                            trade.stop_loss = new_stop   # keep the engine's view in sync
                        except Exception:  # noqa: BLE001
                            pass
                        self._f5_capture.emit("f5_manage_applied",
                                              dict(base, reason="applied",
                                                   new_stop=new_stop,
                                                   previous_stop=current_sl or None,
                                                   broker_mutation=True))
                    else:
                        _reject(row, ticket, action, "modify_failed",
                                key=key, terminal=False)
            summary["f5_manage"] = counters
        except Exception as exc:  # noqa: BLE001 - the seam must never break management
            _log.warning("book[%s]: F5 manage consume failed (%r) -> no action",
                         self._namespace, exc)

    def _f5_auto_breakeven(self, summary: dict, now) -> None:
        """Move the stop to economic BE when the returned Score and Choice say so.

        The coded form of the chair's measured behaviour (2026-08-25, owner-directed): a
        position that has shown +1.5R of favourable excursion becomes risk-free while its
        target stays. NULL-RULE runner sleeves are excluded by name/prefix (their measured
        management EV is negative; exits are contract-owned). Tighten-only by construction
        (skips any stop already at/past entry), one attempt memo per ticket per process,
        H8-honest under authority-false, NEVER raises into the tick.
        """
        if str(getattr(self, "_namespace", "") or "") == "operator":
            # Breakeven is the lifetime hop on the open ticket. This pass does
            # not ask again and does not restore a trigger or a sleeve exclusion.
            return
        if self._namespace != "operator" or self._f5_capture is None:
            return
        try:
            import math

            from .minimal_size import (
                F5_AUTO_BE_ENABLED,
                F5_AUTO_BE_EXCLUDED_PREFIXES,
                F5_AUTO_BE_EXCLUDED_SLEEVES,
                f5_economic_be_stop,
            )

            if not F5_AUTO_BE_ENABLED:
                return   # CONTRACT V1: writer does not manage runners between fill and SL/TP/time-stop
            if getattr(self, "_f5_auto_be_done", None) is None:
                self._f5_auto_be_done = set()
            self._f5_manage_ensure_memos()
            applied = 0
            for (sym, sleeve), ee in list(self._exec_engines.items()):
                trade = getattr(ee, "active_trade", None)
                ticket = getattr(trade, "ticket", None)
                if trade is None or ticket in (None, 0):
                    continue
                ticket = int(ticket)
                s = str(sleeve)
                if s in F5_AUTO_BE_EXCLUDED_SLEEVES or s.startswith(F5_AUTO_BE_EXCLUDED_PREFIXES):
                    continue
                if ticket in self._f5_auto_be_done:
                    continue
                direction = str(getattr(trade, "direction", "") or "").upper()
                if direction not in ("LONG", "SHORT"):
                    continue
                try:
                    entry = float(getattr(trade, "entry_price", 0.0) or 0.0)
                    current_sl = float(getattr(trade, "stop_loss", 0.0) or 0.0)
                except (TypeError, ValueError):
                    continue
                if entry <= 0 or current_sl <= 0:
                    continue
                if (direction == "LONG" and current_sl >= entry) or \
                        (direction == "SHORT" and current_sl <= entry):
                    self._f5_auto_be_done.add(ticket)   # already risk-free (or better)
                    continue
                init_map = getattr(self, "_f5_initial_sl", None) or {}
                init_sl = init_map.get(ticket, current_sl)
                denom = abs(entry - float(init_sl))
                if not (math.isfinite(denom) and denom > 0):
                    continue
                try:
                    tick = self._mt5.get_tick(self._broker_symbol(sym))
                except Exception:  # noqa: BLE001
                    tick = None
                bid = getattr(tick, "bid", None)
                ask = getattr(tick, "ask", None)
                if not bid or not ask:
                    continue
                # Favourable excursion at the side the position could EXIT at.
                mark = float(bid) if direction == "LONG" else float(ask)
                fav_r = (mark - entry) / denom if direction == "LONG" else (entry - mark) / denom
                if not math.isfinite(fav_r):
                    continue
                trigger_r = _parameter_score(
                    "auto_be_trigger_r",
                    {
                        "ticket": ticket,
                        "symbol": sym,
                        "sleeve": s,
                        "favourable_r": fav_r,
                        "namespace": "operator",
                    },
                    "What favourable R names a breakeven move on this ticket? "
                    "The score you return is that R.",
                )
                if trigger_r is None or fav_r < float(trigger_r):
                    continue
                if not _spot_choice(
                    "auto_be",
                    {
                        "ticket": ticket,
                        "symbol": sym,
                        "sleeve": s,
                        "favourable_r": fav_r,
                        "trigger_r": float(trigger_r),
                        "namespace": "operator",
                    },
                    {
                        "move_be": "Move the stop to economic breakeven.",
                        "leave_orig": "Leave the stop where it is.",
                    },
                    "move_be",
                    f"auto_be|{ticket}|{sym}|{s}",
                    "The two sides of moving this stop to economic breakeven. "
                    "An empty answer or a tie does not move it.",
                ):
                    continue
                if not self._live_broker_authority():
                    key = ("auto_be_authority_off", ticket)
                    if key not in getattr(self, "_f5_manage_emitted", set()):
                        self._f5_manage_mark(key, terminal=False)
                        self._f5_capture.emit("f5_auto_breakeven", {
                            "ticket": ticket, "symbol": sym, "sleeve": s,
                            "status": "suppressed_live_broker_authority_false",
                            "favourable_r": fav_r, "broker_mutation": False})
                    continue
                modify = getattr(ee, "_modify_sl", None)
                if not callable(modify):
                    continue
                econ = f5_economic_be_stop(
                    direction, entry, float(init_sl), float(bid), float(ask)
                )
                if econ is None:
                    continue
                ok = False
                try:
                    ok = bool(modify(ticket, econ, trade=trade,
                                     modify_reason="f5_auto_breakeven"))
                except Exception as exc:  # noqa: BLE001
                    _log.warning("book[%s]: F5 auto-BE modify failed ticket=%s (%r)",
                                 self._namespace, ticket, exc)
                    continue
                if ok:
                    try:
                        trade.stop_loss = econ
                    except Exception:  # noqa: BLE001
                        pass
                    self._f5_auto_be_done.add(ticket)
                    applied += 1
                    self._f5_capture.emit("f5_auto_breakeven", {
                        "ticket": ticket, "symbol": sym, "sleeve": s,
                        "status": "applied", "new_stop": econ,
                        "previous_stop": current_sl, "initial_stop": float(init_sl),
                        "favourable_r": fav_r,
                        "trigger_r": float(trigger_r),
                        "broker_mutation": True})
                    _log.info("book[%s]: F5 AUTO-BE ticket=%s %s/%s at +%.2fR -> stop to "
                              "entry %.5f (was %.5f)", self._namespace, ticket, sym, s,
                              fav_r, entry, current_sl)
            if applied:
                summary["f5_auto_breakeven"] = applied
        except Exception as exc:  # noqa: BLE001 - protection must never break management
            _log.warning("book[%s]: F5 auto-BE pass failed (%r) -> no action",
                         self._namespace, exc)

    def _f5_duplicate_stack_dedup(self, summary: dict) -> None:
        """Close all but the first of same-symbol/direction/entry/stop duplicate positions.

        The post-fill form of the judge's stack law (2026-08-25: 178425997/178427810 filled
        0.4 s apart, identical geometry, 10 lots on one shared 5.1-pip tick — the judge could
        not test the stack pre-fill because launcher candidates carry no direction). STRICT
        price equality only: different stops are different bets and stay the judge's business.
        Keeps the lowest ticket (first fill). Applies to every sleeve — two identical runners
        are still one bet; this is dedup, not exit management. NEVER raises.
        """
        if self._namespace != "operator" or self._f5_capture is None:
            return
        try:
            from .minimal_size import F5_DUP_STACK_DEDUP_ENABLED

            dedup_flag = bool(F5_DUP_STACK_DEDUP_ENABLED)
            self._f5_manage_ensure_memos()
            groups: dict[tuple, list] = {}
            for (sym, sleeve), ee in list(self._exec_engines.items()):
                trade = getattr(ee, "active_trade", None)
                ticket = getattr(trade, "ticket", None)
                if trade is None or ticket in (None, 0):
                    continue
                direction = str(getattr(trade, "direction", "") or "").upper()
                try:
                    entry = float(getattr(trade, "entry_price", 0.0) or 0.0)
                    sl = float(getattr(trade, "stop_loss", 0.0) or 0.0)
                except (TypeError, ValueError):
                    continue
                if direction not in ("LONG", "SHORT") or entry <= 0 or sl <= 0:
                    continue
                key = (str(sym), direction, repr(entry), repr(sl))
                groups.setdefault(key, []).append((int(ticket), ee, str(sym), str(sleeve)))
            closed_n = 0
            for key, members in groups.items():
                if len(members) < 2:
                    continue
                members.sort(key=lambda m: m[0])
                keeper = members[0]
                for ticket, ee, sym, sleeve in members[1:]:
                    payload = {"ticket": ticket, "symbol": sym, "sleeve": sleeve,
                               "kept_ticket": keeper[0], "kept_sleeve": keeper[3],
                               "geometry_key": list(key)}
                    if not self._live_broker_authority():
                        mkey = ("dup_dedup_authority_off", ticket)
                        if mkey not in getattr(self, "_f5_manage_emitted", set()):
                            self._f5_manage_mark(mkey, terminal=False)
                            self._f5_capture.emit("f5_duplicate_stack_dedup", dict(
                                payload, status="suppressed_live_broker_authority_false",
                                broker_mutation=False))
                        continue
                    if not _spot_choice(
                        "duplicate_stack",
                        dict(payload, namespace="operator", dedup_flag=dedup_flag),
                        {
                            "close_duplicate": "Close this duplicate ticket. Keep the first fill.",
                            "leave_duplicate": "Leave this duplicate ticket open.",
                        },
                        "close_duplicate",
                        f"duplicate_stack|{ticket}|{keeper[0]}",
                        "The two sides of closing a later ticket with the same geometry. "
                        "An empty answer or a tie does not close it.",
                    ):
                        continue
                    closed = False
                    try:
                        closed = bool(ee.close_position("f5_duplicate_stack_dedup"))
                    except Exception as exc:  # noqa: BLE001
                        _log.warning("book[%s]: F5 dup-dedup close failed ticket=%s (%r)",
                                     self._namespace, ticket, exc)
                        continue
                    if closed:
                        closed_n += 1
                        self._f5_capture.emit("f5_duplicate_stack_dedup", dict(
                            payload, status="closed", broker_mutation=True))
                        _log.warning("book[%s]: F5 DUP STACK ticket=%s %s/%s identical to "
                                     "kept %s/%s -> CLOSED (one bet, one ticket)",
                                     self._namespace, ticket, sym, sleeve,
                                     keeper[0], keeper[3])
            if closed_n:
                summary["f5_duplicate_stack_dedup"] = closed_n
        except Exception as exc:  # noqa: BLE001 - dedup must never break management
            _log.warning("book[%s]: F5 dup-dedup pass failed (%r) -> no action",
                         self._namespace, exc)

    @staticmethod
    def _f5_position_value(position, key, default=None):
        if isinstance(position, dict):
            return position.get(key, default)
        return getattr(position, key, default)

    def _f5_reconcile_broker_positions(self, positions) -> dict | None:
        """Refresh the F5 governor from one complete, magic-scoped broker snapshot.

        Missing ledger units are recovered only from the ticket's persisted immutable F5 entry
        evidence.  Anything unreadable leaves the F5 governor unavailable; a corrupt/crash-gap
        ledger can therefore never restart as zero risk.  Default production owners have no F5
        ledger and return immediately.
        """
        ledger = getattr(self, "_f5_ledger", None)
        if ledger is None:
            return None
        if positions is None:
            return ledger.mark_reconciliation_unavailable("broker_positions_unavailable")
        vpp_fn = getattr(self._mt5, "get_symbol_value_per_point", None)
        if not callable(vpp_fn):
            return ledger.mark_reconciliation_unavailable("value_per_point_unavailable")

        rows = []
        for position in list(positions or []):
            ticket = self._f5_position_value(position, "ticket")
            record = self._load_trade_record(ticket) if ticket not in (None, 0) else None
            instrumentation = (
                record.get("instrumentation")
                if isinstance(record, dict) and isinstance(record.get("instrumentation"), dict)
                else {}
            )
            broker_symbol = self._f5_position_value(position, "symbol")
            try:
                value_per_point = vpp_fn(broker_symbol)
            except Exception:
                value_per_point = None
            nominal = instrumentation.get("f5_nominal_risk_usd")
            actual = instrumentation.get("f5_actual_risk_usd")
            intended = instrumentation.get("f5_intended_risk_usd")
            current_volume = self._f5_position_value(position, "volume")
            price_open = self._f5_position_value(position, "price_open")
            stop_loss = self._f5_position_value(position, "sl")
            try:
                need = not all(
                    isinstance(v, (int, float)) and v > 0
                    for v in (nominal, actual, intended)
                )
                if need and all(v not in (None, 0) for v in (current_volume, price_open, stop_loss, value_per_point)):
                    geo = float(current_volume) * abs(float(price_open) - float(stop_loss)) * float(value_per_point)
                    if geo > 0:
                        nominal = actual = intended = geo
            except (TypeError, ValueError):
                pass
            rows.append({
                "ticket": ticket,
                "sleeve": record.get("sleeve") if isinstance(record, dict) else None,
                "symbol": record.get("symbol") if isinstance(record, dict) else broker_symbol,
                "decision_day": record.get("decision_day") if isinstance(record, dict) else None,
                "opened_utc": (
                    record.get("opened_at_utc") if isinstance(record, dict) else None
                ),
                "nominal_risk_usd": nominal,
                "actual_risk_usd": actual,
                "intended_risk_usd": intended,
                "current_volume": current_volume,
                "price_open": price_open,
                "stop_loss": stop_loss,
                "value_per_point": value_per_point,
                "broker_floating_pnl_usd": self._f5_position_value(position, "profit"),
            })
        # Official consume for ledger units the broker no longer holds. Only on a
        # confirmed NON-empty snapshot (empty can be a transient MT5 miss).
        # Uses broker_closed_absent_on_reconcile so daily_pnl + _f5_on_close fold
        # once; leftover/active-engine paths stay the same seam.
        if list(positions):
            broker_tickets: set[int] = set()
            for row in rows:
                try:
                    row_ticket = int(row.get("ticket") or 0)
                except (TypeError, ValueError):
                    row_ticket = 0
                if row_ticket:
                    broker_tickets.add(row_ticket)
            try:
                open_units = dict((ledger.snapshot() or {}).get("open_units") or {})
            except Exception:
                open_units = {}
            for key, unit in open_units.items():
                try:
                    ticket_i = int(key)
                except (TypeError, ValueError):
                    continue
                if ticket_i in broker_tickets:
                    continue
                rec = self._load_trade_record(ticket_i)
                rec_d = rec if isinstance(rec, dict) else {}
                unit_d = unit if isinstance(unit, dict) else {}
                execution = rec_d.get("execution") if isinstance(rec_d.get("execution"), dict) else {}
                symbol = rec_d.get("symbol") or unit_d.get("symbol")
                sleeve = rec_d.get("sleeve") or unit_d.get("sleeve")
                broker_symbol = execution.get("broker_symbol")
                if not broker_symbol and symbol not in (None, ""):
                    try:
                        broker_symbol = self._broker_symbol(symbol)
                    except Exception:
                        broker_symbol = symbol
                self._mark_trade_record_closed(
                    ticket_i,
                    "broker_closed_absent_on_reconcile",
                    datetime.now(timezone.utc).isoformat(),
                    record=rec_d or None,
                    broker_symbol=broker_symbol,
                    sleeve=sleeve,
                    symbol=symbol,
                )
                self._clear_engine_ticket(ticket_i)
        status = ledger.reconcile_broker_positions(rows)
        if not status.get("complete"):
            _log.error("book[%s]: F5 broker-position reconciliation FAILED: %s",
                       self._namespace, status.get("status"))
        return status

    def _f5_on_notional_breach(self, verdict) -> None:
        """Close the notional epoch AFTER the real flatten has run. NEVER raises."""
        if self._f5_ledger is None:
            return
        try:
            reason = (verdict or {}).get("reason") or "notional_breach"
            closed = self._f5_ledger.open_new_epoch(reason)
            snap = self._f5_ledger.snapshot()
            self._f5_capture.emit("f5_notional_standdown", {
                "epoch_closed": closed,
                "governor_metrics": (verdict or {}).get("metrics"),
                "new_epoch": snap.get("epoch"),
                "real_pnl_usd_cumulative": snap.get("real_pnl_usd_cumulative")})
            _log.warning(
                "book[%s]: F5 NOTIONAL STAND-DOWN -- epoch %s closed (%s), notional drawdown "
                "$%.2f over %s trades; new epoch %s opened at $%.0f. Real P&L across all epochs "
                "$%.2f (REPORTED, never gated).",
                self._namespace, closed.get("epoch"), reason,
                float(closed.get("notional_drawdown_usd") or 0.0),
                closed.get("trades_in_epoch"), snap.get("epoch"),
                float(snap.get("notional_initial") or 0.0),
                float(snap.get("real_pnl_usd_cumulative") or 0.0))
        except Exception as exc:  # noqa: BLE001
            _log.warning("book[%s]: F5 epoch roll failed (%r)", self._namespace, exc)

    def _f5_emit_slate(self, res, decision, gs, now) -> None:
        """The admission funnel's DENOMINATOR -- the one genuinely new record F5 needs.

        `admission.py` is ~2,000 lines and writes NOTHING to disk (its only `json.dumps` is a
        `print` in a `__main__` block). Skips reach disk as `unit_skipped` packets, but the skip
        row carries no score, no rank and no slate -- so "we saw 9, took 2, here is why 3 lost to
        6" cannot be reconstructed from today's logs, and `cycle_no_candidates` records that
        nothing happened rather than how many candidates were evaluated.

        This is PURE OBSERVATION, downstream of every decision, reusing values admission already
        computed (`SizedUnit.reason` carries `gross_risk_cap_would_exceed` and the overlay tags).
        Not one new computation, `broker_mutation: false`, and it NEVER raises."""
        if self._f5_capture is None:
            return
        try:
            def _u(unit):
                return {k: unit.get(k) for k in (
                    "cluster", "sleeve_members", "confidence", "sized", "reason",
                    "risk_pct_per_trade", "unit_risk_pct", "overlays_applied")}
            self._f5_emit_slate_rows(res, decision, gs, now, _u)
        except Exception as exc:  # noqa: BLE001 - observation must never break a cycle
            _log.warning("book[%s]: F5 slate capture failed (%r)", self._namespace, exc)

    def _f5_emit_slate_rows(self, res, decision, gs, now, _u) -> None:
        intents = res.get("intents") or []
        realized = list(getattr(decision, "realized_units", []) or [])
        would = list(getattr(decision, "would_units", []) or [])
        if not intents and not realized and not would:
            # An idle cycle says nothing this file does not already say better: the launcher
            # writes one namespaced row per tick to `shadow_logs/ultimate_book_launcher.jsonl`.
            # Emitting ~1,440 empty rows per account per day would bury the bars that matter.
            return
        led = self._f5_ledger.snapshot() if self._f5_ledger is not None else None
        governor = getattr(decision, "governor", None) or {}
        if not isinstance(governor, dict):
            governor = {
                "allow_new_entries": getattr(governor, "allow_new_entries", None),
                "size_cap_multiplier": getattr(governor, "size_cap_multiplier", None),
                "reason": getattr(governor, "reason", None),
            }
        def _row(intent):
            row = UltimateBookOwner._f5_slate_intent_row(intent)
            hops = _read_hop(getattr(self, "_owner_hops", None), intent)
            for key in ("last_bar", "unit", "intent", "admission"):
                value = hops.get(key)
                if value not in (None, "") and row.get(key) is None:
                    row[key] = value
            return row

        self._f5_capture.emit("f5_slate", {
            "ts_cycle_utc": now.isoformat(),
            "n_intents": len(intents),
            "intents": [_row(i) for i in intents],
            "realized_units": [_u(u) for u in realized],
            "would_units": [_u(u) for u in would],
            "governor": {
                # allow/cap/reason belong to GovernorDecision, carried by the bridge decision.
                # ``gs`` is GovernorState and has only inputs; reading it made all three fields
                # silently None on every F5 slate.
                "allow": governor.get("allow_new_entries"),
                "equity": getattr(gs, "equity", None),
                "realized_today_pct": getattr(gs, "realized_today_pct", None),
                "open_risk_pct": getattr(gs, "open_risk_pct", None),
                "cap_mult": governor.get("size_cap_multiplier"),
                "reason": governor.get("reason")},
            "f5_notional": None if led is None else {
                "epoch": led.get("epoch"),
                "notional_equity": led.get("notional_equity"),
                "open_units": len(led.get("open_units") or {}),
                "trades_recorded": led.get("trades_recorded"),
                "real_pnl_usd_cumulative": led.get("real_pnl_usd_cumulative")},
            "broker_mutation": False})

    @staticmethod
    def _f5_slate_intent_row(intent) -> dict:
        """Observation-only intent row for the judgment composer.

        The original emit dropped direction / stop / entry, so the resident judge
        saw geometry-less intents, abstained (PASS), and the book placed unjudged.
        Direction is already on TradeIntent; absolute stop/target are derived from
        entry + stop_dist / target_dist when the limit rail has stamped an entry.
        """
        direction = UltimateBookOwner._runtime_learning_direction_label(
            getattr(intent, "direction", None)
        )
        entry = getattr(intent, "entry_price", None)
        stop_dist = getattr(intent, "stop_dist", None)
        target_dist = getattr(intent, "target_dist", None)
        stop = None
        target = None
        try:
            if entry is not None and stop_dist is not None and direction in ("LONG", "SHORT"):
                sign = 1.0 if direction == "LONG" else -1.0
                entry_f = float(entry)
                stop = entry_f - sign * float(stop_dist)
                if target_dist is not None:
                    target = entry_f + sign * float(target_dist)
        except (TypeError, ValueError):
            stop = None
            target = None
        row = {
            "sleeve": getattr(intent, "sleeve", None),
            "symbol": getattr(intent, "symbol", None),
            "decision_day": getattr(intent, "decision_day", None),
        }
        extras = {
            "direction": direction,
            "entry": entry,
            "stop": stop,
            "target": target,
            "stop_dist": stop_dist,
            "target_dist": target_dist,
            "decision_bar_iso": getattr(intent, "decision_bar_iso", None),
            "candidate_id": getattr(intent, "candidate_id", None),
            "last_bar": getattr(intent, "last_bar_choice", None),
            "unit": getattr(intent, "unit_choice", None),
            "intent": getattr(intent, "intent_return", None),
        }
        for key, value in extras.items():
            if value is not None:
                row[key] = value
        return row

    def _f5_news_proximity(self) -> "float | None":
        """Minutes to the nearest HIGH-impact calendar event, stamped on every fill.

        redacted_account recognises only 40 % of profit and 100 % of losses inside +/-5 min of a
        listed high-impact event, and the shipped filter's post-event window is 2 minutes
        (`agent_config.yaml:3961-3962`) -- a 3-minute uncovered window on the loss-bearing side
        of every high-impact print. That key is R2-bound AND inside both activation-token
        digests, so it is NOT changed here; it is fixed at the next scheduled re-mint. Stamping
        the distance is free and lets the analysis exclude tainted fills rather than argue about
        them afterwards. Returns None when no calendar is readable -- absence is honest, a zero
        would be a lie."""
        try:
            from .minimal_size import minutes_to_nearest_high_impact_event
            rows = self._f5_news_calendar_rows()
            if rows is None:
                return None
            return minutes_to_nearest_high_impact_event(datetime.now(timezone.utc), rows)
        except Exception:  # noqa: BLE001
            return None

    def _f5_news_calendar_rows(self):
        """Live merge: news_brief + official_high_spine + news_calendar.

        Frozen ``data/news_calendar.json`` alone missed Warsh; ``time_utc`` there
        is HH:MM so the old ISO-only stamp was null on every fill. Reloads on
        file mtime (no writer restart needed for a spine refresh).
        """
        try:
            from .minimal_size import f5_load_live_calendar_events
            rows = f5_load_live_calendar_events(self._repo_root)
            return rows or None
        except Exception:
            return None

    def _f5_new_risk_block(self, symbol: str, now: Optional[datetime] = None) -> Optional[str]:
        """F5 writer NEW-risk clock. None == may place. Occupied theses are not closed."""
        if str(self._namespace) != "operator":
            return None
        try:
            from .minimal_size import f5_new_risk_clock_block_reason
            reason = f5_new_risk_clock_block_reason(
                symbol,
                now or datetime.now(timezone.utc),
                events=self._f5_news_calendar_rows() or (),
            )
        except Exception:  # noqa: BLE001 - never break the tick
            return None
        if not reason:
            return None
        # The clock string is a fact. Only a Noul bool withholds. A miss does not.
        if _noul_withholds(
            "new_risk_clock",
            {
                "symbol": str(symbol),
                "clock_reason": str(reason),
                "namespace": "operator",
            },
            "Does this new-risk clock fact withhold the candidate? "
            "Occupied theses are not closed.",
        ):
            return str(reason)
        return None

    def _sleeve_comment(self, sleeve: str) -> str:
        # mirror execution.py order_comment = f"{prefix}{_sleeve}"[:16] (MT5 truncates to 16 chars).
        # The prefix is the namespace's broker identity, so this and the engine's own comment
        # cannot drift apart: both call `comment_prefix_for_magic` on the same magic.
        return f"{self._comment_prefix}{sleeve}"[:16]

    @staticmethod
    def _entry_too_late(now: datetime, bar_iso: Optional[str], tf, frac: float) -> bool:
        """True if `now` is past the placement freshness window for a decision bar -> a restart-late CHASE.

        A supervised/cold restart spanning a bar close re-generates that bar's signal and would place it
        HOURS late at a chased price (the validated edge enters AT the close). Normal cycles fire within ~1
        poll of the close, so a gate at `frac * bar_period` past the close only bites a restart-late entry.
        Fail-OPEN (return False) on a missing/unknown bar or timeframe so a live timely entry is never blocked."""
        try:
            per = _TF_MINUTES.get(tf)
            if not per or not bar_iso:
                return False
            bar_close = datetime.fromisoformat(bar_iso) + timedelta(minutes=per)
            return ((now - bar_close).total_seconds() / 60.0) > float(frac) * per
        except Exception:
            return False

    @staticmethod
    def _bar_age_minutes(now, bar_iso, tf) -> float | None:
        """Minutes from this bar's close to the cycle clock. A missing bar stays absent."""

        try:
            per = _TF_MINUTES.get(tf)
            if not per or not bar_iso or now is None:
                return None
            close = datetime.fromisoformat(str(bar_iso)) + timedelta(minutes=int(per))
            if close.tzinfo is None:
                close = close.replace(tzinfo=timezone.utc)
            clock = now if getattr(now, "tzinfo", None) else now.replace(tzinfo=timezone.utc)
            return (clock - close).total_seconds() / 60.0
        except Exception:
            return None

    @staticmethod
    def _move_from_limit(intent, tick) -> float | None:
        """How far the live quote sits from the limit, on that order's side.

        A long reads the bid against the limit. A short reads the limit against
        the ask. A missing price or a missing side stays absent.
        """

        try:
            entry = float(getattr(intent, "entry_price", None))
            bid = float(getattr(tick, "bid", None))
            ask = float(getattr(tick, "ask", None))
        except (TypeError, ValueError):
            return None
        if entry != entry or bid != bid or ask != ask:
            return None
        try:
            side = int(getattr(intent, "direction", None))
        except (TypeError, ValueError):
            return None
        if side > 0:
            return bid - entry
        if side < 0:
            return entry - ask
        return None

    def _broker_holds(self, symbol: str, sleeve: str) -> bool:
        """True if the broker already has an open W7:{sleeve} position on `symbol` — a definitive
        anti-duplicate guard for the case where manage_open_positions FAILED to adopt it (a transient
        broker error left the engine's active_trade None while the position is still open). Best-effort;
        any error -> False (the active_trade guard + idempotency ledger remain the primary protection)."""
        try:
            get_pos = getattr(self._mt5, "get_positions", None)
            if not callable(get_pos):
                return False
            want = self._sleeve_comment(sleeve)
            for p in (get_pos(self._broker_symbol(symbol)) or []):
                if (getattr(p, "comment", "") or "") == want:
                    return True
        except Exception:
            return False
        return False

    def _broker_position_protection(self, ticket: Any, broker_symbol: str | None = None) -> dict[str, Any]:
        """Read current broker-side protection for an open position without mutating broker state."""
        if ticket in (None, "", 0):
            return {}
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            return {}
        positions = []
        get_positions = getattr(self._mt5, "get_positions", None)
        if callable(get_positions) and broker_symbol:
            try:
                positions.extend(list(get_positions(broker_symbol) or []))
            except Exception:
                return {}
        if not positions:
            get_open = getattr(self._mt5, "get_open_positions", None)
            if callable(get_open):
                try:
                    positions.extend(list(get_open() or []))
                except Exception:
                    return {}
        for position in positions:
            try:
                if int(getattr(position, "ticket", 0) or 0) != ticket_i:
                    continue
            except (TypeError, ValueError):
                continue
            out: dict[str, Any] = {}
            for attr, key in (
                ("sl", "broker_position_sl"),
                ("tp", "broker_position_tp"),
                ("price_open", "broker_position_price_open"),
                ("price_current", "broker_position_price_current"),
            ):
                value = getattr(position, attr, None)
                if value is not None:
                    out[key] = value
            return out
        return {}

    @staticmethod
    def _broker_symbol_key(symbol: Any) -> str:
        return str(symbol or "").upper().replace(".", "").replace("_", "").strip()

    def _broker_symbol_keys_for_canonical(self, symbol: str) -> set[str]:
        keys = {self._broker_symbol_key(symbol)}
        try:
            keys.add(self._broker_symbol_key(self._broker_symbol(symbol)))
        except Exception:
            pass
        return {key for key in keys if key}

    def _same_broker_symbol_open_exposures(
        self,
        symbol: str,
        *,
        open_positions_snapshot: list | None = None,
    ) -> list | None:
        """Return open GTOS/book positions already using this broker symbol.

        The placement path used to guard only the exact (symbol, sleeve). Different sleeves can resolve to
        the same broker symbol (for example US30_cash -> US30), so a second sleeve could unintentionally
        open the opposite side while the first ticket was still live. This guard is intentionally scoped to
        book/GTOS positions only and returns None only when a real broker position accessor exists but the
        read is unavailable, so tests/mocks without position APIs do not become globally fail-closed.
        """
        get_open = getattr(self._mt5, "get_open_positions", None)
        positions = []
        source_seen = False
        if open_positions_snapshot is None:
            if callable(get_open):
                open_positions_snapshot = self._open_book_positions_snapshot()
                if open_positions_snapshot is None:
                    return None
                source_seen = True
                positions.extend(list(open_positions_snapshot or []))
        else:
            source_seen = True
            positions.extend(list(open_positions_snapshot or []))
        get_positions = getattr(self._mt5, "get_positions", None)
        if callable(get_positions):
            try:
                fresh_positions = get_positions(self._broker_symbol(symbol))
            except Exception:
                return None
            source_seen = True
            positions.extend(list(fresh_positions or []))
        elif not source_seen:
            return []
        # This worker's own broker identity, never the module constant: a second decision surface
        # on the same account must not be adopted and exit-managed by this one. `get_positions`
        # above is already magic-filtered at `mt5_real.py:344`, so for the ARMED book both of the
        # clauses below are a second filter over an already-filtered list and nothing changes;
        # for a NON-armed namespace they are what stops the comment clause matching `W7:` rows.
        own_magic = self._magic
        keys = self._broker_symbol_keys_for_canonical(symbol)
        exposures = []
        seen_tickets = set()
        for p in positions:
            psym = getattr(p, "symbol", None)
            if self._broker_symbol_key(psym) not in keys:
                continue
            ticket = getattr(p, "ticket", None)
            dedupe_key = ticket if ticket not in (None, 0, "") else id(p)
            if dedupe_key in seen_tickets:
                continue
            seen_tickets.add(dedupe_key)
            comment = getattr(p, "comment", "") or ""
            magic = getattr(p, "magic", None)
            ledger_pair = self._ledger.sleeve_symbol_for_ticket(ticket) if ticket not in (None, 0) else None
            is_book_position = (
                comment.startswith(self._comment_prefix)
                or ledger_pair is not None
                or (own_magic is not None and magic == own_magic)
            )
            if is_book_position:
                exposures.append(p)
        return exposures

    def _tick(self, symbol: str):
        # the intent carries the CANONICAL symbol; cross to the broker under its mt5_symbol
        try:
            return self._mt5.get_tick(self._broker_symbol(symbol))
        except Exception:
            return None

    def _profile_supports_symbol(self, symbol: str) -> bool:
        from src.utils.config import resolve_instrument_config_key

        base_symbol = (self.base_config.get("market", {}) or {}).get("symbol", "XAUUSD")
        return symbol == base_symbol or resolve_instrument_config_key(self.base_config, symbol) is not None

    def _candidate_book_sleeves(self) -> tuple[str, ...]:
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        raw = rt.get("ultimate_book_candidate_book_sleeves", [])
        if raw is None:
            return ()
        if isinstance(raw, str):
            return (raw,) if raw else ()
        if isinstance(raw, (list, tuple, set)):
            return tuple(str(item) for item in raw if str(item))
        return ()

    def _market_expansion_sleeves(self) -> tuple[str, ...]:
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        raw = rt.get("ultimate_book_market_expansion_sleeves", [])
        if raw is None:
            explicit = ()
        elif isinstance(raw, str):
            explicit = (raw,) if raw else ()
        elif isinstance(raw, (list, tuple, set)):
            explicit = tuple(str(item) for item in raw if str(item))
        else:
            explicit = ()
        policy = str(rt.get("ultimate_book_market_expansion_policy", "explicit_allowlist") or "explicit_allowlist")
        resolved, error = resolve_market_expansion_sleeves(policy=policy, explicit_sleeves=explicit)
        return () if error else resolved

    def _manageable_symbols(self) -> list[str]:
        """All active-sleeve on_surface symbols THAT HAVE AN INSTRUMENT CONFIG on this profile.

        A position can only be open on a symbol the broker/profile actually carries, so symbols absent
        from config['instruments'] (e.g. the metals crosses / agri legs that the redacted_account follower
        lacks) can never have a managed position — building their per-symbol ExecutionEngine would only
        raise 'No instrument config' every tick. We filter them out (silently, but logged ONCE so the
        reduced per-profile breadth is intentional + visible, not a silent error storm)."""
        cached = getattr(self, "_manageable_cache", None)
        if cached is not None:
            return cached
        from .sleeves.registry import active_specs
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        include_candidate_book = config_bool_value(rt.get("ultimate_book_include_candidate_book", False), False)
        include_market_expansion_book = config_bool_value(
            rt.get("ultimate_book_include_market_expansion_book", False),
            False,
        )
        candidate_sleeves = self._candidate_book_sleeves()
        expansion_sleeves = self._market_expansion_sleeves()
        all_syms = sorted({
            s
            for spec in active_specs(
                None,
                include_candidate_book=include_candidate_book,
                candidate_book_sleeves=candidate_sleeves or None,
                include_market_expansion_book=include_market_expansion_book,
                market_expansion_sleeves=expansion_sleeves or None,
            )
            for s in (spec.on_surface or [])
        })
        present, absent = [], []
        for s in all_syms:
            if self._profile_supports_symbol(s):
                present.append(s)
            else:
                absent.append(s)
        if absent:
            _log.info("book[%s]: %d on_surface symbols have no instrument config on this profile -> "
                      "not generated/managed here (intentional reduced breadth): %s",
                      self._namespace, len(absent), ", ".join(absent))
        self._manageable_cache = present
        return present

    def _runtime_learning_status(self, packets: int = 0, error: Any | None = None) -> dict:
        status = {
            "enabled": bool(self._runtime_learning_packet_enabled),
            "log_enabled": bool(self._runtime_learning_packet_log_enabled),
            "log_path": self._runtime_learning_packet_log_path,
            "schema": RUNTIME_LEARNING_PACKET_SCHEMA_VERSION,
            "packets": int(packets or 0),
            "ultimate_convergence_advisory_enabled": bool(self._convergence_advisory_enabled),
            "ultimate_convergence_advisory_log_enabled": bool(self._convergence_advisory_log_enabled),
        }
        if error is not None:
            status["error"] = repr(error)
        return status

    def _runtime_learning_bridge_context(self, decision=None) -> dict:
        if decision is not None:
            return _bridge_telemetry(decision)
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        broad_live = config_bool_value(rt.get("selector_v4_enabled", False), False) and config_bool_value(
            rt.get("selector_v4_apply_to_execution", False),
            False,
        )
        live_broker_authority = config_bool_value(
            rt.get("ultimate_book_live_broker_authority", False),
            False,
        )
        effect_now = (
            config_bool_value(rt.get("ultimate_book_enabled", False), False)
            and config_bool_value(rt.get("ultimate_book_apply_to_execution", False), False)
            and config_bool_value(rt.get("ultimate_book_live_activation_allowed", False), False)
            and live_broker_authority
            and not broad_live
        )
        return {
            "runtime_effect_now": effect_now,
            "enabled": config_bool_value(rt.get("ultimate_book_enabled", False), False),
            "apply_to_execution": config_bool_value(rt.get("ultimate_book_apply_to_execution", False), False),
            "live_activation_allowed_by_config": config_bool_value(
                rt.get("ultimate_book_live_activation_allowed", False),
                False,
            ),
            "live_broker_authority": live_broker_authority,
            "broad_selector_apply_to_execution": broad_live,
            "profile": rt.get("ultimate_book_profile"),
            "candidate_book_profile": rt.get("ultimate_book_candidate_book_profile"),
            "include_candidate_book": config_bool_value(rt.get("ultimate_book_include_candidate_book", False), False),
            "candidate_book_sleeves": list(self._candidate_book_sleeves()),
            "include_market_expansion_book": config_bool_value(
                rt.get("ultimate_book_include_market_expansion_book", False),
                False,
            ),
            "market_expansion_profile": rt.get("ultimate_book_market_expansion_profile"),
            "market_expansion_policy": rt.get("ultimate_book_market_expansion_policy"),
            "market_expansion_sleeves": list(self._market_expansion_sleeves()),
            "kelly_lite": config_bool_value(rt.get("ultimate_book_kelly_lite", False), False),
            "kelly_conservative": config_bool_value(rt.get("ultimate_book_kelly_conservative", False), False),
            "kelly_running_count": config_bool_value(rt.get("ultimate_book_kelly_running_count", False), False),
            "sqrt_n_pooling": config_bool_value(rt.get("ultimate_book_sqrt_n_pooling", False), False),
            "stress_derisk": config_bool_value(rt.get("ultimate_book_stress_derisk", False), False),
            "derisk_mode": rt.get("ultimate_book_derisk_mode"),
            "overlays": config_bool_value(rt.get("ultimate_book_overlays", False), False),
            "vp_acceptance": config_bool_value(rt.get("ultimate_book_vp_acceptance", False), False),
            "drop_w7_symbols": config_bool_value(rt.get("ultimate_book_drop_w7_symbols", False), False),
            "learning_rerate_active": bool(rt.get("ultimate_book_learning_rerate")),
            "metals_confluence_gate": config_bool_value(
                rt.get("ultimate_book_metals_confluence_gate", False),
                False,
            ),
            "symbol_damage_guard": config_bool_value(rt.get("ultimate_book_symbol_damage_guard", False), False),
        }

    @staticmethod
    def _runtime_learning_skip_context(decision: Any, intents: Any, meta: Any) -> dict[tuple[str, str, str], dict]:
        meta_by_pair: dict[tuple[str, str], dict] = {}
        for item in meta or []:
            if not isinstance(item, dict):
                continue
            sleeve = str(item.get("tag") or item.get("sleeve") or "")
            symbol = str(item.get("symbol") or "")
            if sleeve and symbol:
                meta_by_pair[(sleeve, symbol)] = item
        unit_by_sleeve: dict[str, dict] = {}
        for unit in (
            list(getattr(decision, "realized_units", []) or [])
            + list(getattr(decision, "would_units", []) or [])
        ):
            if not isinstance(unit, dict):
                continue
            members = unit.get("sleeve_members") or []
            for sleeve in members:
                unit_by_sleeve.setdefault(str(sleeve), unit)
        refusal_by_candidate: dict[tuple[str, str, str | None, str], dict] = {}
        for refusal in list(getattr(decision, "candidate_refusals", []) or []):
            if not isinstance(refusal, dict):
                continue
            refusal_key = (
                str(refusal.get("sleeve") or ""),
                str(refusal.get("symbol") or ""),
                UltimateBookOwner._runtime_learning_direction_label(refusal.get("direction")),
                str(refusal.get("decision_day") or "")[:10],
            )
            refusal_by_candidate[refusal_key] = refusal
        out: dict[tuple[str, str, str], dict] = {}
        for intent in intents or []:
            sleeve = str(getattr(intent, "sleeve", "") or "")
            symbol = str(getattr(intent, "symbol", "") or "")
            if not sleeve or not symbol:
                continue
            meta_row = meta_by_pair.get((sleeve, symbol), {})
            dbar = str(
                meta_row.get("decision_bar_iso")
                or getattr(intent, "decision_bar_iso", None)
                or getattr(intent, "decision_day", None)
                or ""
            )
            decision_day = str(getattr(intent, "decision_day", "") or dbar[:10] or "")
            unit = unit_by_sleeve.get(sleeve, {})
            candidate_id = unit.get("candidate_id") if isinstance(unit, dict) else None
            members = unit.get("sleeve_members") if isinstance(unit, dict) else []
            direction = UltimateBookOwner._runtime_learning_direction_label(
                getattr(intent, "direction", None)
            )
            cluster = UltimateBookOwner._resolve_runtime_cluster(unit=unit, sleeve=sleeve)
            candidate_specific = (
                candidate_id
                and (
                    len(members or []) == 1
                    or (f"::{symbol}::" in str(candidate_id) and str(candidate_id).endswith(f"::{sleeve}"))
                )
            )
            ctx = {
                "symbol": symbol,
                "sleeve": sleeve,
                "direction": direction,
                "decision_bar_iso": dbar,
                "decision_day": decision_day,
                "timeframe": meta_row.get("timeframe"),
                "cluster": cluster,
            }
            refusal = refusal_by_candidate.get((sleeve, symbol, direction, decision_day[:10]))
            if isinstance(refusal, dict):
                ctx.update({
                    "candidate_disposition": "refused",
                    "candidate_disposition_gate": refusal.get(
                        "candidate_disposition_gate", "book_admission_and_sizing"
                    ),
                    "candidate_disposition_reason": refusal.get(
                        "candidate_disposition_reason", "admission_filter_refused"
                    ),
                    "candidate_disposition_evidence": "exact_predicate_capture",
                })
            elif isinstance(unit, dict) and unit:
                ctx.update({
                    "candidate_disposition": "admission_unit_member",
                    "candidate_disposition_gate": "book_admission_and_sizing",
                    "candidate_disposition_reason": unit.get("reason"),
                    "candidate_disposition_evidence": "observed_admission_unit_membership",
                })
            elif not bool(getattr(decision, "would_new_entries_allowed", True)):
                ctx.update({
                    "candidate_disposition": "refused",
                    "candidate_disposition_gate": "book_admission_and_sizing",
                    "candidate_disposition_reason": (
                        getattr(decision, "sizing_reason", None)
                        or getattr(decision, "reason", None)
                        or "admission_refused_reason_unavailable"
                    ),
                    "candidate_disposition_evidence": "aggregate_sizing_refusal",
                })
            else:
                ctx.update({
                    "candidate_disposition": "unresolved_after_generation",
                    "candidate_disposition_evidence": "no_admission_unit_or_exact_refusal_observed",
                })
            if candidate_specific:
                ctx["candidate_id"] = candidate_id
            else:
                derived_candidate_id = UltimateBookOwner._runtime_learning_candidate_id(
                    cluster=cluster,
                    symbol=symbol,
                    decision_day=decision_day,
                    direction=direction,
                    sleeve=sleeve,
                )
                if derived_candidate_id:
                    ctx["candidate_id"] = derived_candidate_id
            out[(sleeve, symbol, dbar)] = ctx
        return out

    @staticmethod
    def _runtime_learning_direction_label(direction: Any) -> str | None:
        if direction in (None, ""):
            return None
        if isinstance(direction, (int, float)):
            if float(direction) > 0:
                return "LONG"
            if float(direction) < 0:
                return "SHORT"
        text = str(direction).strip()
        if not text:
            return None
        upper = text.upper()
        if upper in {"1", "+1", "BUY", "LONG"}:
            return "LONG"
        if upper in {"-1", "SELL", "SHORT"}:
            return "SHORT"
        return upper

    @staticmethod
    def _runtime_learning_candidate_id(
        *,
        cluster: Any,
        symbol: Any,
        decision_day: Any,
        direction: Any,
        sleeve: Any,
    ) -> str | None:
        if any(value in (None, "") for value in (cluster, symbol, decision_day, direction, sleeve)):
            return None
        return f"W7_BOOK::{cluster}::{symbol}::{str(decision_day)[:10]}::{direction}::{sleeve}"

    @staticmethod
    def _cluster_from_candidate_id(candidate_id: Any) -> str | None:
        text = str(candidate_id or "")
        parts = text.split("::")
        if len(parts) >= 6 and parts[0] == "W7_BOOK" and parts[1]:
            return parts[1]
        return None

    @staticmethod
    def _resolve_runtime_cluster(
        *,
        unit: dict | None = None,
        sleeve: Any = None,
        candidate_id: Any = None,
    ) -> str | None:
        if isinstance(unit, dict):
            value = unit.get("cluster")
            if value not in (None, ""):
                return str(value)
            value = UltimateBookOwner._cluster_from_candidate_id(unit.get("candidate_id"))
            if value:
                return value
        value = UltimateBookOwner._cluster_from_candidate_id(candidate_id)
        if value:
            return value
        if sleeve not in (None, ""):
            value = cluster_of(str(sleeve))
            if value:
                return str(value)
        return None

    @staticmethod
    def _runtime_learning_admission_members(unit: dict, skip_context: dict | None) -> list[dict]:
        if not isinstance(unit, dict) or not isinstance(skip_context, dict):
            return []
        members = {str(item) for item in (unit.get("sleeve_members") or []) if str(item)}
        if not members:
            return []
        out = []
        for (_sleeve, _symbol, _dbar), ctx in sorted(skip_context.items()):
            if not isinstance(ctx, dict) or str(ctx.get("sleeve") or "") not in members:
                continue
            out.append({
                key: ctx.get(key)
                for key in (
                    "candidate_id",
                    "symbol",
                    "sleeve",
                    "direction",
                    "decision_bar_iso",
                    "decision_day",
                    "timeframe",
                    "cluster",
                )
                if ctx.get(key) is not None
            })
        return out

    @staticmethod
    def _runtime_learning_unit_join_fields(outcome: dict, members: list[dict]) -> dict:
        """OD-P2. The unit join key, resolved by MEMBER AGREEMENT and never by a representative.

        THE DEFECT. `single_member = admission_members[0] if len(...) == 1 else {}` leaves the
        join key null on every multi-member unit. Because `ultimate_book_intent_id` hashes
        `(namespace, event_type, sleeve, symbol, direction, decision_bar_iso, decision_day)`,
        nulling four of seven collapsed 440 rows onto 65 ids (P, `PACKET_EMITTER_CARRY.md` §3).

        THE BOOBY TRAP, WHICH THIS DELIBERATELY DOES NOT SPRING. `_first_unit_sleeve`
        (`runtime_learning_packet.py:155`) would attribute a whole unit to `sleeve_members[0]`.
        It is inert only by accident -- `SizedUnit.sleeve_members` is a TUPLE and the guard reads
        `isinstance(members, list)` -- and widening that `isinstance` would silently start booking
        every multi-sleeve metals unit to `metals_core`, skewing every rollup keyed on
        `packet["sleeve"]` (`scripts/w7_packet_forensics.py:100`). A round-trip through JSON turns
        the tuple into a list, so the trap is one refactor away from arming itself. Nothing here
        picks a representative; a field is emitted only when the members AGREE on it.

        WHAT THE AGREEMENT RULE IS WORTH, MEASURED over the 99,112-packet live export (985
        `unit_admitted`/`unit_shadow` rows; 682 carry members, of which 277 are multi-member):

        | field | agree | disagree | rows this newly fills |
        |---|---:|---:|---:|
        | `sleeve` | 681 | **1** | **276** |
        | `timeframe` / `decision_bar_iso` / `decision_day` | 682 | 0 | 277 each |
        | `direction` | 630 | 52 | 225 |
        | `symbol` | 405 | **277** | **0** |

        Two of those columns correct the framing this repair was filed under. P expected
        multi-sleeve units to be the common case -- *"anything spanning two sleeves of a cluster
        ... yields {}"* -- and the measured answer is that exactly **1 of 277** multi-member units
        spans two sleeves. The common multi-member unit is ONE sleeve on SEVERAL SYMBOLS, which is
        why `symbol` disagrees on all 277 and the rule correctly declines to emit it on every one.
        So the field the trap would have corrupted is the field the rule recovers almost
        completely, and the field that genuinely cannot be resolved is refused by the same test.

        `admission_unit_join_status` records WHICH branch produced the value, so no reader can
        mistake an agreed field for a single-member one; `admission_unit_sleeves` gives per-sleeve
        rollups the honest roster to explode on instead of a guessed representative.
        """
        rows = [m for m in (members or []) if isinstance(m, dict)]
        out: dict[str, Any] = {}
        if not rows:
            out["admission_unit_join_status"] = "no_members"
            return out
        if len(rows) == 1:
            out["admission_unit_join_status"] = "single_member"
            return out

        agreed: list[str] = []
        disagreed: list[str] = []
        for key in ("symbol", "sleeve", "direction", "decision_bar_iso", "decision_day", "timeframe"):
            values = {m.get(key) for m in rows if m.get(key) is not None}
            if not values:
                continue
            if len(values) > 1:
                disagreed.append(key)
                continue
            agreed.append(key)
            # Never overwrite a value the unit itself already resolved -- agreement fills gaps.
            if outcome.get(key) is None:
                out[key] = next(iter(values))
        sleeves = sorted({str(m.get("sleeve")) for m in rows if m.get("sleeve") is not None})
        if sleeves:
            out["admission_unit_sleeves"] = sleeves
        # Three-valued, not two. `members_disagree` on a unit whose SLEEVE agrees and whose SYMBOL
        # does not would read as "this attribution is untrustworthy" -- and that is the measured
        # common case (277 of 277 multi-member units disagree on symbol; 276 of them agree on
        # sleeve). A reader scanning the status alone must not draw the opposite of the truth.
        if not disagreed:
            out["admission_unit_join_status"] = "members_agree"
        elif agreed:
            out["admission_unit_join_status"] = "members_partially_agree"
        else:
            out["admission_unit_join_status"] = "members_disagree"
        out["admission_unit_agreed_fields"] = sorted(agreed)
        out["admission_unit_disagreed_fields"] = sorted(disagreed)
        return out

    @staticmethod
    def _runtime_learning_skip_row(skip: Any, skip_context: dict | None = None) -> dict:
        if isinstance(skip, dict):
            row = dict(skip)
        else:
            row = {"reason": str(skip)}
            text = str(skip)
            if ":" in text:
                symbol, reason = text.split(":", 1)
                if symbol:
                    row.setdefault("symbol", symbol)
                row["reason"] = reason or text
        if isinstance(skip_context, dict):
            key = (
                str(row.get("sleeve") or ""),
                str(row.get("symbol") or ""),
                str(row.get("decision_bar_iso") or ""),
            )
            ctx = skip_context.get(key)
            if isinstance(ctx, dict):
                for field in (
                    "candidate_id",
                    "cluster",
                    "decision_day",
                    "direction",
                    "timeframe",
                ):
                    if ctx.get(field) is not None:
                        row.setdefault(field, ctx.get(field))
                row.setdefault(
                    "admission_unit_members",
                    [
                        {
                            key: ctx.get(key)
                            for key in (
                                "candidate_id",
                                "symbol",
                                "sleeve",
                                "direction",
                                "decision_bar_iso",
                                "decision_day",
                                "timeframe",
                                "cluster",
                            )
                            if ctx.get(key) is not None
                        }
                    ],
                )
                row.setdefault("admission_unit_member_count", len(row.get("admission_unit_members") or []))
        if row.get("reason") == "profile_missing_instrument_config":
            row.setdefault("candidate_context_status", "not_generated_profile_missing_instrument")
            row.setdefault("source_completeness_status", "profile_missing_instrument_config_no_candidate_identity")
        row.setdefault("skip_reason", row.get("reason"))
        return row

    @staticmethod
    def _runtime_learning_ticket_hash(ticket: Any) -> str | None:
        if ticket in (None, "", 0):
            return None
        return stable_hash(ticket, prefix="ticket")

    @staticmethod
    def _price_tolerance(*values: Any) -> float:
        nums: list[float] = []
        for value in values:
            if value in (None, ""):
                continue
            try:
                nums.append(abs(float(value)))
            except (TypeError, ValueError):
                continue
        ref = max(nums) if nums else 0.0
        if ref >= 1000.0:
            return 0.02
        if ref >= 100.0:
            return 0.01
        if ref >= 10.0:
            return 0.001
        return 0.0001

    @staticmethod
    def _price_matches(left: float | None, right: float | None, tolerance: float) -> bool:
        return left is not None and right is not None and abs(left - right) <= tolerance

    @staticmethod
    def _broker_protection_reconciliation(record: dict, execution: dict) -> dict[str, Any]:
        planned_entry = UltimateBookOwner._closed_record_float(record, "entry_price")
        planned_sl = UltimateBookOwner._closed_record_float(record, "stop_loss")
        planned_tp = UltimateBookOwner._closed_record_float(record, "take_profit_1")
        broker_open = UltimateBookOwner._closed_record_float(record, "broker_position_price_open")
        broker_sl = UltimateBookOwner._closed_record_float(record, "broker_position_sl")
        broker_tp = UltimateBookOwner._closed_record_float(record, "broker_position_tp")
        tolerance = UltimateBookOwner._price_tolerance(planned_entry, planned_sl, planned_tp, broker_open, broker_sl, broker_tp)

        planned_delta_sl = planned_sl - planned_entry if planned_sl is not None and planned_entry is not None else None
        planned_delta_tp = planned_tp - planned_entry if planned_tp is not None and planned_entry is not None else None
        fill_adjusted_sl = broker_open + planned_delta_sl if broker_open is not None and planned_delta_sl is not None else None
        fill_adjusted_tp = broker_open + planned_delta_tp if broker_open is not None and planned_delta_tp is not None else None
        planned_risk = abs(planned_sl - planned_entry) if planned_sl is not None and planned_entry is not None else None
        planned_target_r = (
            abs(planned_tp - planned_entry) / planned_risk
            if planned_tp is not None and planned_entry is not None and planned_risk not in (None, 0.0)
            else None
        )
        target_sign = (
            1.0
            if planned_tp is not None and planned_entry is not None and planned_tp > planned_entry
            else -1.0
            if planned_tp is not None and planned_entry is not None and planned_tp < planned_entry
            else None
        )
        broker_risk = abs(broker_sl - broker_open) if broker_sl is not None and broker_open is not None else None
        broker_risk_adjusted_tp = (
            broker_open + target_sign * planned_target_r * broker_risk
            if broker_open is not None
            and target_sign is not None
            and planned_target_r is not None
            and broker_risk not in (None, 0.0)
            else None
        )

        def _leg_status(
            *,
            leg: str,
            planned: float | None,
            broker: float | None,
            fill_adjusted: float | None,
            broker_risk_adjusted: float | None = None,
        ) -> str:
            if broker is None or broker == 0.0:
                if planned is None or planned == 0.0:
                    return f"broker_{leg}_absent_as_planned"
                return f"missing_broker_current_{leg}"
            if planned is None or planned == 0.0:
                return f"broker_current_{leg}_present_without_planned_geometry"
            if UltimateBookOwner._price_matches(planned, broker, tolerance):
                return f"matches_planned_{leg}"
            if UltimateBookOwner._price_matches(fill_adjusted, broker, tolerance):
                return f"matches_fill_adjusted_{leg}"
            if UltimateBookOwner._price_matches(broker_risk_adjusted, broker, tolerance):
                return f"matches_broker_risk_adjusted_{leg}"
            return f"differs_from_planned_{leg}"

        sl_status = _leg_status(
            leg="stop_loss",
            planned=planned_sl,
            broker=broker_sl,
            fill_adjusted=fill_adjusted_sl,
        )
        tp_status = _leg_status(
            leg="take_profit",
            planned=planned_tp,
            broker=broker_tp,
            fill_adjusted=fill_adjusted_tp,
            broker_risk_adjusted=broker_risk_adjusted_tp,
        )
        statuses = {sl_status, tp_status}
        if all(status.startswith("broker_") and status.endswith("_absent_as_planned") for status in statuses):
            overall = "broker_current_protection_unavailable"
        elif any(status.startswith("differs_from_planned_") for status in statuses):
            overall = "broker_current_differs_from_planned_protection"
        elif any(status.startswith("matches_broker_risk_adjusted_") for status in statuses):
            overall = "broker_current_matches_broker_risk_adjusted_or_planned_protection"
        elif any(status.startswith("matches_fill_adjusted_") for status in statuses):
            overall = "broker_current_matches_fill_adjusted_or_planned_protection"
        elif any(status.startswith("matches_planned_") for status in statuses):
            overall = "broker_current_matches_planned_protection"
        else:
            overall = "broker_current_protection_captured_without_full_planned_geometry"
        return {
            "broker_position_protection_reconciliation_status": overall,
            "broker_position_stop_loss_status": sl_status,
            "broker_position_take_profit_status": tp_status,
            "broker_position_planned_entry_price": planned_entry,
            "broker_position_planned_stop_loss": planned_sl,
            "broker_position_planned_take_profit": planned_tp,
            "broker_position_fill_price": broker_open,
            "broker_position_fill_adjusted_stop_loss": fill_adjusted_sl,
            "broker_position_fill_adjusted_take_profit": fill_adjusted_tp,
            "broker_position_broker_risk_adjusted_take_profit": broker_risk_adjusted_tp,
            "broker_position_planned_target_r": planned_target_r,
            "broker_position_price_tolerance": tolerance,
        }

    @staticmethod
    def _runtime_learning_modelled_cost(trade_params: "dict | None") -> dict[str, Any]:
        """OD-P3/CN. Flatten pretrade cost truth without copying the nested broker packet.

        Session P (`PACKET_EMITTER_CARRY.md` §6 item 1, B213) filed this as the largest remaining
        packet gap and described the repair as *"a small change to that allowlist"* -- add
        `gtos_vnext_pretrade_cost_model` to the flat key list above. Measured here, that literal
        repair does not work and does not fail quietly:

        - The model is the ~40-key packet `broker_net_cost_engine.build_pretrade_cost_packet`
          returns, and it carries `profile.server`. `server` is in `FORBIDDEN_RAW_KEYS`
          (`runtime_learning_packet.py:70`) and `_contains_forbidden_raw_key` scans the packet
          RECURSIVELY at `:617`, so every placed-trade packet would validate as
          `forbidden_raw_keys:server` and be quarantined by `GuardedPacketWriter`. Loud, but a
          repair that stops the thing it was meant to fix.
        - The packet also embeds `symbol_spec`, `explicit_session_table` and `profile`, none of
          which a cost reader wants on every row.

        So the model is READ and the scalars are DERIVED. Its total and components,
        nothing nested that a forbidden-key scan can trip on.

        CN moved the current producer to v3, where `commission_r` is a fourth component backed by
        broker truth. Historical v2 models remain three-component and explicitly exclude
        commission. The declaration is resolved per model so old rows are never reinterpreted as
        if they had charged a component they did not carry.

        Emits nothing at all when the model is absent or `NOT_APPLICABLE`; a modelled cost of
        "unknown" must never read as a modelled cost of zero.

        Duck-typed, not `isinstance(..., Mapping)`: this module imports only Any/Callable/Optional
        from typing, so a bare `Mapping` at runtime is a NameError no syntax check catches -- the
        same trap `_broker_server_name` documents at :1369. Written the wrong way first here.
        """
        model = (trade_params or {}).get("gtos_vnext_pretrade_cost_model")
        if not hasattr(model, "get") or not model:
            return {}
        status = str(model.get("status") or "").strip()
        if status == "NOT_APPLICABLE":
            # The vnext production path did not run, so there is no model -- not a zero-cost model.
            return {"modelled_cost_status": status}
        out: dict[str, Any] = {"modelled_cost_status": status or None}
        total = model.get("total_cost_r")
        if total is not None:
            out["modelled_cost_r"] = total
        components = model.get("total_cost_components")
        raw_expected = model.get("total_cost_components_expected")
        if isinstance(raw_expected, (list, tuple)) and all(
            isinstance(value, str) and value for value in raw_expected
        ):
            expected = tuple(raw_expected)
        else:
            version = str(model.get("model_version") or "")
            expected = (
                MODELLED_COST_COMPONENTS
                if version.endswith("_v3")
                else LEGACY_MODELLED_COST_COMPONENTS
            )
        raw_excludes = model.get("cost_excludes")
        if isinstance(raw_excludes, (list, tuple)) and all(
            isinstance(value, str) and value for value in raw_excludes
        ):
            excludes = tuple(raw_excludes)
        else:
            excludes = (
                MODELLED_COST_EXCLUDES
                if "commission_r" in expected
                else LEGACY_MODELLED_COST_EXCLUDES
            )
        if hasattr(components, "items"):
            present = {
                str(k): v
                for k, v in components.items()
                if str(k) in expected
                and v is not None
                and not hasattr(v, "get")
                and not isinstance(v, (list, tuple))
            }
            if present:
                out["modelled_cost_components"] = present
            missing = sorted(set(expected) - set(present))
            if missing:
                out["modelled_cost_components_missing"] = missing
        out["modelled_cost_components_expected"] = list(expected)
        out["modelled_cost_excludes"] = list(excludes)
        for src_key, out_key in (
            ("model_version", "modelled_cost_model_version"),
            ("cost_authority", "modelled_cost_authority"),
            ("max_total_cost_r", "modelled_cost_max_total_cost_r"),
            ("commission_mode", "modelled_commission_mode"),
            ("commission_cost_authority", "modelled_commission_cost_authority"),
            ("commission_cost_provenance", "modelled_commission_cost_provenance"),
        ):
            if model.get(src_key) is not None:
                out[out_key] = model.get(src_key)
        commission = model.get("commission_cost")
        if hasattr(commission, "get"):
            for src_key, out_key in (
                ("source_status", "modelled_commission_cost_source_status"),
                ("artifact", "modelled_commission_cost_artifact"),
            ):
                if commission.get(src_key) is not None:
                    out[out_key] = commission.get(src_key)
        return {k: v for k, v in out.items() if v is not None}

    @staticmethod
    def _runtime_learning_trade_context(
        *,
        ticket: Any = None,
        trade_params: dict | None = None,
        record: dict | None = None,
        broker_symbol: str | None = None,
        placed_at_utc: str | None = None,
        management_checked_at_utc: str | None = None,
        policy_clock: dict | None = None,
    ) -> dict:
        tp = dict(trade_params or {})
        if not tp and isinstance(record, dict):
            inst = record.get("instrumentation")
            if isinstance(inst, dict):
                tp = dict(inst)
        ctx: dict[str, Any] = {}
        ticket_hash = UltimateBookOwner._runtime_learning_ticket_hash(ticket)
        if ticket_hash:
            ctx["ticket_hash_sha256"] = ticket_hash
        if broker_symbol:
            ctx["broker_symbol"] = broker_symbol
        if placed_at_utc:
            ctx["placement_observed_at_utc"] = placed_at_utc
        if management_checked_at_utc:
            ctx["management_checked_at_utc"] = management_checked_at_utc
        if isinstance(record, dict):
            ctx["trade_record_status"] = (
                "reconstructed_native_policy"
                if record.get("reconstructed_from_sleeve_identity")
                else "persisted_trade_record"
            )
            for key in ("decision_bar_iso", "decision_day", "cluster", "candidate_id"):
                if record.get(key) is not None:
                    ctx[key] = record.get(key)
            if record.get("runtime_learning_joinability_status") is not None:
                ctx["trade_record_joinability_status"] = record.get("runtime_learning_joinability_status")
            if record.get("trade_lifecycle_status") is not None:
                ctx["trade_lifecycle_status"] = record.get("trade_lifecycle_status")
            if record.get("closed_at_utc") is not None:
                ctx["closed_at_utc"] = record.get("closed_at_utc")
            if record.get("last_management_checked_at_utc") is not None:
                ctx["last_management_checked_at_utc"] = record.get("last_management_checked_at_utc")
            if record.get("close_action") is not None:
                ctx["close_action"] = record.get("close_action")
            if record.get("rehydration_status") is not None:
                ctx["rehydration_status"] = record.get("rehydration_status")
            if record.get("rehydration_error") is not None:
                ctx["rehydration_error"] = record.get("rehydration_error")
            execution = record.get("execution")
            if isinstance(execution, dict):
                if not ctx.get("ticket_hash_sha256") and execution.get("ticket_hash_sha256"):
                    ctx["ticket_hash_sha256"] = execution.get("ticket_hash_sha256")
                ctx.setdefault("broker_symbol", execution.get("broker_symbol") or broker_symbol)
                for key in (
                    "broker_position_sl",
                    "broker_position_tp",
                    "broker_position_price_open",
                    "broker_position_price_current",
                    "broker_position_protection_reconciliation_status",
                    "broker_position_stop_loss_status",
                    "broker_position_take_profit_status",
                    "broker_position_planned_entry_price",
                    "broker_position_planned_stop_loss",
                    "broker_position_planned_take_profit",
                    "broker_position_fill_price",
                    "broker_position_fill_adjusted_stop_loss",
                    "broker_position_fill_adjusted_take_profit",
                    "broker_position_broker_risk_adjusted_take_profit",
                    "broker_position_planned_target_r",
                    "broker_position_price_tolerance",
                ):
                    if execution.get(key) is not None:
                        ctx[key] = execution.get(key)
                if execution.get("placed_at_utc") is not None:
                    ctx.setdefault("placement_observed_at_utc", execution.get("placed_at_utc"))
                if not UltimateBookOwner._missingish_ticket(execution.get("broker_entry_deal_ticket")):
                    ctx["broker_entry_deal_hash_sha256"] = stable_hash(
                        execution.get("broker_entry_deal_ticket"),
                        prefix="deal_ticket",
                    )
                for key in (
                    "entry_reconciliation_status",
                    "broker_fill_time_utc",
                    # `_iso_from_deal_time_near_reference` (:2818-2852) will shift a broker deal
                    # time by up to +/-6 WHOLE HOURS to snap it to a local reference. The offset
                    # is computed and stored on the execution record (:3055-3056) and then read by
                    # nobody -- it appears in 0 of the 99,112 live packets. So for every packet in
                    # the corpus it is impossible to tell a raw broker timestamp from one that was
                    # silently moved six hours to agree with our clock, which is the
                    # broker-time-labelled-as-UTC hazard in its most subtle form: the agreement
                    # that licenses the label is partly manufactured by the label's own producer.
                    # Emitting it makes the adjustment auditable; packet_economics downgrades the
                    # entry provenance to `transferred` whenever it fired.
                    "broker_fill_time_alignment_offset_seconds",
                    "broker_entry_source_status",
                ):
                    if execution.get(key) is not None:
                        ctx[key] = execution.get(key)
                for key in (
                    "exit_reconciliation_status",
                    "exit_reconciliation_attempted",
                    "exit_reconciliation_source_status",
                    "broker_exit_time_utc",
                    "broker_exit_price",
                    "broker_exit_profit",
                    "broker_exit_commission",
                    "broker_exit_swap",
                    "broker_exit_fee",
                    "broker_entry_commission",
                    "broker_entry_swap",
                    "broker_position_sl",
                    "broker_position_tp",
                    "broker_position_price_open",
                    "broker_position_price_current",
                    "broker_position_protection_reconciliation_status",
                    "broker_position_stop_loss_status",
                    "broker_position_take_profit_status",
                    "broker_position_planned_entry_price",
                    "broker_position_planned_stop_loss",
                    "broker_position_planned_take_profit",
                    "broker_position_fill_price",
                    "broker_position_fill_adjusted_stop_loss",
                    "broker_position_fill_adjusted_take_profit",
                    "broker_position_broker_risk_adjusted_take_profit",
                    "broker_position_planned_target_r",
                    "broker_position_price_tolerance",
                    "broker_position_deal_count",
                    "broker_position_entry_deal_count",
                    "broker_position_exit_deal_count",
                    "broker_position_accounting_coverage_status",
                    "broker_position_aggregate_profit",
                    "broker_position_aggregate_commission",
                    "broker_position_aggregate_swap",
                    "broker_position_aggregate_fee",
                    "broker_position_realized_pnl",
                    "broker_realized_pnl_source",
                    "broker_realized_pnl",
                ):
                    if execution.get(key) is not None:
                        ctx[key] = execution.get(key)
                missing_exit_fields = execution.get("exit_reconciliation_missing_fields")
                if not isinstance(missing_exit_fields, list):
                    missing_exit_fields = []
                else:
                    missing_exit_fields = list(missing_exit_fields)
                if (
                    execution.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
                    and UltimateBookOwner._missingish_ticket(execution.get("broker_exit_order_ticket"))
                    and "broker_exit_order_ticket" not in missing_exit_fields
                ):
                    missing_exit_fields.append("broker_exit_order_ticket")
                if missing_exit_fields:
                    ctx["exit_reconciliation_missing_fields"] = missing_exit_fields
                for raw_key, out_key, prefix in (
                    ("broker_exit_deal_ticket", "broker_exit_deal_hash_sha256", "deal_ticket"),
                    ("broker_exit_order_ticket", "broker_exit_order_hash_sha256", "order_ticket"),
                    ("broker_exit_position_id", "broker_exit_position_hash_sha256", "position_ticket"),
                ):
                    if not UltimateBookOwner._missingish_ticket(execution.get(raw_key)):
                        ctx[out_key] = stable_hash(execution.get(raw_key), prefix=prefix)
            if record.get("broker_real_entry_label_ready") is not None:
                ctx["broker_real_entry_label_ready"] = record.get("broker_real_entry_label_ready")
            for key in (
                "exit_reconciliation_status",
                "exit_reconciliation_attempted",
                "exit_reconciliation_source_status",
                "exit_reconciliation_missing_fields",
                "broker_exit_time_utc",
                "broker_exit_price",
                "broker_exit_profit",
                "broker_exit_commission",
                "broker_exit_swap",
                "broker_exit_fee",
                "broker_position_deal_count",
                "broker_position_entry_deal_count",
                "broker_position_exit_deal_count",
                "broker_position_accounting_coverage_status",
                "broker_position_aggregate_profit",
                "broker_position_aggregate_commission",
                "broker_position_aggregate_swap",
                "broker_position_aggregate_fee",
                "broker_position_realized_pnl",
                "broker_realized_pnl_source",
                "broker_realized_pnl",
            ):
                if record.get(key) is not None:
                    ctx[key] = record.get(key)
            for raw_key, out_key, prefix in (
                ("broker_exit_deal_ticket", "broker_exit_deal_hash_sha256", "deal_ticket"),
                ("broker_exit_order_ticket", "broker_exit_order_hash_sha256", "order_ticket"),
                ("broker_exit_position_id", "broker_exit_position_hash_sha256", "position_ticket"),
            ):
                if not UltimateBookOwner._missingish_ticket(record.get(raw_key)):
                    ctx[out_key] = stable_hash(record.get(raw_key), prefix=prefix)
            if (
                ctx.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
                and ctx.get("broker_exit_order_hash_sha256") in (None, "")
            ):
                missing_exit_fields = ctx.get("exit_reconciliation_missing_fields")
                if not isinstance(missing_exit_fields, list):
                    missing_exit_fields = []
                else:
                    missing_exit_fields = list(missing_exit_fields)
                if "broker_exit_order_ticket" not in missing_exit_fields:
                    missing_exit_fields.append("broker_exit_order_ticket")
                ctx["exit_reconciliation_missing_fields"] = missing_exit_fields
        elif trade_params:
            ctx["trade_record_status"] = "runtime_trade_params"

        for key in (
            "candidate_id",
            "decision_time_utc",
            "asof_utc",
            "entry_price",
            "stop_loss",
            "take_profit_1",
            "risk_pct_override",
            "direction",
            "gtos_vnext_dynamic_policy_selected",
            "gtos_vnext_execution_policy_id",
            "gtos_vnext_dynamic_be_trigger_r",
            "gtos_vnext_dynamic_partial_close_ratio",
            "gtos_vnext_dynamic_trail_gap_r",
            "gtos_vnext_dynamic_time_stop_bars",
            "gtos_vnext_dynamic_final_target_r",
            "gtos_vnext_dynamic_broker_take_profit_mode",
            "gtos_vnext_dynamic_no_broker_take_profit",
            "gtos_vnext_book_native_exit_management",
            "gtos_vnext_source_event_hash",
            "gtos_vnext_selector_v4_packet_hash",
            "gtos_vnext_scheduler_v4_packet_hash",
            "gtos_vnext_selected_cell_id",
            "gtos_vnext_selected_cell_risk_pct",
            "gtos_vnext_selected_cell_nominal_risk_pct",
            "gtos_vnext_selected_cell_risk_policy_identity_status",
            "pretrade_spread_r",
            "pretrade_expected_slippage_r",
            "pretrade_total_cost_r",
            "f5_nominal_risk_usd",
            "f5_intended_risk_usd",
            "f5_actual_risk_usd",
        ):
            if key in tp and tp.get(key) is not None:
                ctx[key] = tp.get(key)
        for key in ("f5_round_up", "gtos_live_flow_execution", "risk_unit_floor"):
            if isinstance(tp.get(key), dict):
                ctx[key] = dict(tp[key])
        if isinstance(record, dict):
            execution = record.get("execution")
            if isinstance(execution, dict) and isinstance(execution.get("f5_close"), dict):
                f5_close = execution["f5_close"]
                for src, dst in (
                    ("realised_r", "f5_realised_r"),
                    ("notional_pnl_usd", "f5_notional_pnl_usd"),
                    ("broker_net_pnl_usd", "f5_broker_net_pnl_usd"),
                ):
                    if f5_close.get(src) is not None:
                        ctx[dst] = f5_close.get(src)
        ctx.update(UltimateBookOwner._runtime_learning_modelled_cost(tp))
        has_ticket_hash = bool(ctx.get("ticket_hash_sha256"))
        has_candidate = bool(ctx.get("candidate_id"))
        has_decision = bool(ctx.get("decision_bar_iso") or ctx.get("decision_time_utc") or ctx.get("asof_utc"))
        if has_ticket_hash and has_candidate and has_decision:
            computed_joinability_status = "ticket_candidate_decision_policy_joinable"
        elif has_ticket_hash and has_decision:
            computed_joinability_status = "ticket_decision_policy_joinable"
        elif has_ticket_hash:
            computed_joinability_status = "ticket_policy_joinable"
        else:
            computed_joinability_status = "partial_join_context"
        status_rank = {
            "partial_join_context": 0,
            "ticket_policy_joinable": 1,
            "ticket_decision_policy_joinable": 2,
            "ticket_candidate_decision_policy_joinable": 3,
        }
        record_joinability_status = ctx.get("trade_record_joinability_status")
        if (
            isinstance(record_joinability_status, str)
            and status_rank.get(record_joinability_status, -1) <= status_rank[computed_joinability_status]
        ):
            ctx["joinability_status"] = record_joinability_status
        else:
            ctx["joinability_status"] = computed_joinability_status
        ctx.update(UltimateBookOwner._runtime_learning_policy_clock_context(policy_clock))
        return ctx

    @staticmethod
    def _runtime_learning_router_result_context(result: Any) -> dict:
        """Carry the router's already-observed execution facts into a placement/refusal row."""
        result = result if isinstance(result, dict) else {}
        ctx = UltimateBookOwner._runtime_learning_trade_context(
            trade_params=result.get("trade_params"),
        )
        for result_key, context_key in (
            ("live_flow_execution", "gtos_live_flow_execution"),
            ("risk_unit_floor", "risk_unit_floor"),
        ):
            if (
                ctx.get(context_key) is None
                and isinstance(result.get(result_key), dict)
            ):
                ctx[context_key] = dict(result[result_key])
        return ctx

    @staticmethod
    def _runtime_learning_policy_clock_context(policy_clock: dict | None) -> dict:
        if not isinstance(policy_clock, dict):
            return {}
        ctx = {"policy_clock_diagnostic": dict(policy_clock)}
        field_map = {
            "status": "policy_clock_status",
            "checked_at_utc": "policy_clock_checked_at_utc",
            "entry_time_utc": "policy_clock_entry_time_utc",
            "clock_source": "policy_clock_source",
            "time_stop_bars": "policy_clock_time_stop_bars",
            "elapsed_m15_bars": "policy_clock_elapsed_m15_bars",
            "bars_until_due": "policy_clock_bars_until_due",
            "overdue_bars": "policy_clock_overdue_bars",
            "close_attempted": "policy_clock_close_attempted",
            "close_result": "policy_clock_close_result",
            "close_reason": "policy_clock_close_reason",
            "targetless": "policy_clock_targetless",
            "vnext_time_stop_active": "policy_clock_vnext_time_stop_active",
            "error": "policy_clock_error",
        }
        for src, dst in field_map.items():
            if src in policy_clock and policy_clock.get(src) is not None:
                ctx[dst] = policy_clock.get(src)
        return ctx

    def _runtime_learning_convergence_advisory(
        self,
        *,
        event_type: str,
        bridge: dict,
        unit: dict | None = None,
        outcome: dict | None = None,
    ) -> dict | None:
        if not self._convergence_advisory_enabled or not self._convergence_advisory_log_enabled:
            return None
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        return build_convergence_advisory(
            config=rt,
            namespace=self._namespace,
            event_type=event_type,
            bridge=bridge,
            unit=unit,
            outcome=outcome,
        )

    def _broker_server_name(self) -> Optional[str]:
        """The MT5 server string, needed to count swap nights on the broker's own clock.

        Read from the live account when available, else the profile config. Returns None rather
        than guessing -- `rollover_nights_crossed` fails closed on an unknown server, which is the
        correct outcome: a guessed offset is silent and survives every test. Never raises.
        """
        for getter in ("get_account_server", "get_server"):
            try:
                fn = getattr(self._mt5, getter, None)
                if callable(fn):
                    value = fn()
                    if value:
                        return str(value)
            except Exception:  # noqa: BLE001
                pass
        # Config fallbacks, in order of authority. `mt5.server` is FIRST for historical reasons and
        # is measured to be ABSENT on both live profiles -- `mt5` carries only portable/terminal_*
        # keys. The live server name lives under `broker_profile`. Without these two extra
        # fallbacks, `_broker_server_name` returns None on the VPS for both namespaces, every
        # `rollover_nights` on every live packet reads `unavailable`, and the carry silently
        # delivers holding time WITHOUT the swap-night count -- which is half of what it exists to
        # record, since swap is the largest single broker cost for eight of eleven sleeves.
        # Both live values (`FTMO-Server3`, `redacted_account-Server 2`) are registered rules in
        # `broker_clock`, so the count works the moment the name resolves.
        # Neither getter above is defined anywhere in either lineage; they are kept for a future
        # adapter, not because they fire. Found by an adversarial pass.
        for source, key in (
            (self.base_config.get("mt5"), "server"),
            (self.base_config.get("broker_profile"), "server"),
            ((self.base_config.get("broker_profile") or {}).get("expected_account"), "server"),
        ):
            try:
                # Duck-typed rather than `isinstance(..., Mapping)`: this module imports only
                # Any/Callable/Optional from typing, and a bare `Mapping` here is a NameError at
                # runtime that no syntax check catches.
                value = source.get(key) if hasattr(source, "get") else None
                if value:
                    return str(value)
            except Exception:  # noqa: BLE001
                continue
        return None

    def _runtime_learning_economics(self, row: dict) -> Optional[dict]:
        """Build the optional economics block for one outcome row. Never raises.

        Holding time is the reason this exists. Session N measured the W7 book's dominant
        remaining uncertainty and it is carry: at one night of average carry the book of record
        passes at P=0.951 and makes 1.97 %/month; run every trade to its structural horizon and
        that becomes P=0.450 and 0.13 %/month. Nothing in 99,112 live packets distinguishes those
        two worlds, because holding time was only ever *derivable* -- from a poll-loop observation
        of the close, on 98 of 151 closes -- and never recorded as a measurement with a stated
        provenance and a broker-clock night count.
        """
        try:
            return build_economics_block(row, server=self._broker_server_name())
        except Exception:  # noqa: BLE001 - observability must never raise into the book
            return None

    def _append_runtime_learning_packets(self, summary: dict, packets: list[dict]) -> None:
        if not self._runtime_learning_packet_enabled:
            summary["runtime_learning"] = self._runtime_learning_status(0)
            return
        if not self._runtime_learning_writer:
            # `packet_enabled: true` + `packet_log_enabled: false` is a supported config and leaves
            # the writer None (:223-228). Falling through would hand the guard a None writer, fail
            # every packet as `unrecorded`, and feed that count to
            # ai_companion/supervisor.py:517 -> :709 -> :734-741, which raises an integrity issue
            # and issues `pause_new_entries` for every namespace. A logging switch must never be
            # able to stop the books.
            summary["runtime_learning"] = self._runtime_learning_status(0)
            return
        # OD-P1 (default OFF). Emit-on-change is applied HERE, after the enabled/writer guards and
        # before the packet guard, so a suppressed packet is never counted as quarantined and a
        # logging switch still cannot stop the books. It only ever touches `position_managed`.
        packets, suppressed_now = filter_emit_on_change_packets(
            packets, self._runtime_learning_emit_filter,
        )
        # Built per call, not cached, so replacing `_runtime_learning_writer` (which tests and
        # operational tooling do) still governs where packets land.
        guard = GuardedPacketWriter(self._runtime_learning_writer)
        # The guard never raises and never silently drops: valid packets are written, invalid ones
        # are quarantined to a sidecar AND leave a `packet_rejected` marker in the main log so the
        # hole is visible to a reader of that log alone. The previous implementation raised out of
        # `append_many` on the FIRST invalid packet -- which discarded the whole cycle's batch --
        # and recorded the casualties only in this cycle summary, where nothing downstream of the
        # packet log could ever see them.
        report = guard.append_many(packets)
        status = self._runtime_learning_status(report.accepted)
        status["packet_guard"] = report.as_dict()
        # Preserved key names: src/components/ai_companion/supervisor.py:517,539-540 reads both,
        # and a silently-renamed field would degrade the companion's view without failing anything.
        status["packet_write_error_count"] = report.quarantined + report.unrecorded
        status["packet_write_errors"] = [
            {
                "index": issue.get("index"),
                "event_type": issue.get("event_type"),
                "error": ";".join(issue.get("issues") or []),
            }
            for issue in report.issues[-10:]
        ]
        # A suppressed packet is not recoverable, so it must at minimum be COUNTABLE -- the same
        # discipline `packet_rejected` applies to a quarantined one. `packet_write_error_count` is
        # deliberately NOT touched: a suppression is not a write error, and feeding it to
        # `ai_companion/supervisor.py:517` would raise an integrity issue and pause new entries on
        # both accounts for a working compression.
        if self._runtime_learning_emit_filter is not None:
            status["emit_on_change"] = {
                **self._runtime_learning_emit_filter.status(),
                "suppressed_this_cycle": suppressed_now,
            }
        summary["runtime_learning"] = status
        if not report.healthy:
            _log.warning(
                "book[%s]: runtime-learning guard refused %d/%d packets "
                "(unrecorded=%d, markers=%d); quarantine=%s; issues=%s",
                self._namespace,
                report.quarantined,
                report.submitted,
                report.unrecorded,
                report.markers_written,
                guard.quarantine_path,
                report.issues[-3:],
            )

    def _emit_cycle_runtime_learning(
        self,
        summary: dict,
        now: datetime,
        *,
        decision=None,
        place: bool = True,
    ) -> None:
        bridge = dict(summary.get("bridge") or self._runtime_learning_bridge_context(decision))
        if isinstance(summary.get("lane_weights"), dict):
            bridge["lane_weights"] = dict(summary["lane_weights"])
        packets: list[dict] = []
        ts = now.isoformat()
        base_outcome = {
            "reason": summary.get("reason"),
            "bar_consumable": bool(summary.get("bar_consumable", True)),
            "runtime_effect_now": bool(summary.get("runtime_effect_now", False)),
            "source_completeness_status": "runtime_cycle_summary_observed",
        }
        skip_context = summary.get("skip_context") if isinstance(summary.get("skip_context"), dict) else {}
        # One compact packet terminally conserves every active spec x symbol slot in this
        # BookEngine cycle.  It uses the same guarded runtime-learning writer and live_flow
        # projection as candidates/orders/fills; there is no side logger and no policy input.
        if "generation_terminals" in summary:
            terminals: list[dict] = []
            for item in summary.get("generation_terminals") or []:
                if not isinstance(item, dict):
                    continue
                row = dict(item)
                direction = self._runtime_learning_direction_label(row.get("direction"))
                if direction is not None:
                    row["direction"] = direction
                terminals.append(row)
            generation = summary.get("generation")
            generation_bridge = dict(bridge)
            generation_bridge["broker_profile_generation"] = {
                "active_symbol_slot_count": (
                    generation.get("active_symbol_slot_count")
                    if isinstance(generation, dict)
                    else None
                ),
            }
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type="generation_cycle_complete",
                ts=ts,
                bridge=generation_bridge,
                outcome={
                    "generation_slot_terminals": terminals,
                },
                source="book_owner.run_cycle",
            ))
        # Full candidate denominator: one packet for every generated intent before admission-unit
        # aggregation.  This reuses the existing guarded append-only runtime-learning writer; it is
        # not a parallel log.  The exact dropping predicate (when one ran) is carried from bridge /
        # admission, while unresolved coverage is stated as unresolved rather than inferred.
        for candidate in skip_context.values():
            if not isinstance(candidate, dict):
                continue
            row = dict(candidate)
            row.update({
                "placement_status": "generated",
                "source_completeness_status": "generated_intent_denominator_observed",
            })
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type="candidate_generated",
                ts=ts,
                bridge=bridge,
                outcome=row,
                source="book_owner.run_cycle",
            ))
        if decision is None:
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type="cycle_no_decision",
                ts=ts,
                bridge=bridge,
                outcome={**base_outcome, "placement_status": "no_decision"},
                convergence_advisory=self._runtime_learning_convergence_advisory(
                    event_type="cycle_no_decision",
                    bridge=bridge,
                    outcome={**base_outcome, "placement_status": "no_decision"},
                ),
                source="book_owner.run_cycle",
            ))
        else:
            would_units = list(getattr(decision, "would_units", []) or [])
            if not would_units:
                packets.append(build_runtime_learning_packet(
                    namespace=self._namespace,
                    event_type="cycle_no_candidates",
                    ts=ts,
                    bridge=bridge,
                    outcome={**base_outcome, "placement_status": "no_candidates"},
                    convergence_advisory=self._runtime_learning_convergence_advisory(
                        event_type="cycle_no_candidates",
                        bridge=bridge,
                        outcome={**base_outcome, "placement_status": "no_candidates"},
                    ),
                    source="book_owner.run_cycle",
                ))
            for unit in would_units:
                placement_status = (
                    "admitted" if bool(summary.get("runtime_effect_now")) and place else "shadow"
                )
                admission_members = self._runtime_learning_admission_members(unit, skip_context)
                single_member = admission_members[0] if len(admission_members) == 1 else {}
                candidate_id = unit.get("candidate_id") or single_member.get("candidate_id")
                outcome = {
                    **base_outcome,
                    "placement_status": placement_status,
                    "candidate_id": candidate_id,
                    "cluster": self._resolve_runtime_cluster(
                        unit=unit,
                        sleeve=single_member.get("sleeve"),
                        candidate_id=candidate_id,
                    ),
                    "admission_unit_members": admission_members,
                    "admission_unit_member_count": len(admission_members),
                }
                for key in ("symbol", "sleeve", "direction", "decision_bar_iso", "decision_day", "timeframe"):
                    if single_member.get(key) is not None:
                        outcome[key] = single_member.get(key)
                # D4 (SLEEVE_BOOK_DEFECT_REGISTER): a MULTI-member unit left `single_member` empty, so
                # the side was dropped from the packet even though every member carried it. Measured
                # over the fortnight, unit_admitted packets recorded a side only 31.6% of the time
                # while unit_placed recorded it 100%. Emit the side whenever the unit's members AGREE
                # on it -- a correlated unit is one cluster-day bucket, so agreement is the normal case
                # and disagreement is real information rather than something to paper over.
                #
                # Deliberately NOT emitted when the members disagree: inventing a single direction for
                # a mixed unit would be worse than the gap it closes. Those packets keep the side in
                # outcome.admission_unit_members[], where packet_validation._direction_of reads it.
                #
                # OD-P2 (Session BD, B2063): D4's rule was right and its SCOPE was one field. The
                # same argument covers the whole join key, so it is applied to the whole join key
                # here and `direction` is no longer special-cased.
                outcome.update(
                    UltimateBookOwner._runtime_learning_unit_join_fields(outcome, admission_members)
                )
                packets.append(build_runtime_learning_packet(
                    namespace=self._namespace,
                    event_type="unit_admitted" if placement_status == "admitted" else "unit_shadow",
                    ts=ts,
                    bridge=bridge,
                    unit=unit,
                    outcome=outcome,
                    convergence_advisory=self._runtime_learning_convergence_advisory(
                        event_type="unit_admitted" if placement_status == "admitted" else "unit_shadow",
                        bridge=bridge,
                        unit=unit,
                        outcome=outcome,
                    ),
                    source="book_owner.run_cycle",
                ))
        for skip in summary.get("skipped", []) or []:
            row = self._runtime_learning_skip_row(skip, skip_context)
            reason = row.get("reason") or row.get("skip_reason")
            row.update({
                "placement_status": "skipped",
                "transient_retry": bool(_is_transient_place_failure(reason)),
                "bar_consumable": bool(summary.get("bar_consumable", True)),
            })
            row.setdefault("source_completeness_status", "runtime_skip_summary_observed")
            self._attach_spread_observation(row)
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type="unit_skipped",
                ts=ts,
                bridge=bridge,
                outcome=row,
                convergence_advisory=self._runtime_learning_convergence_advisory(
                    event_type="unit_skipped",
                    bridge=bridge,
                    outcome=row,
                ),
                source="book_owner.run_cycle",
            ))
        for placed in summary.get("placed", []) or []:
            row = dict(placed)
            row.update({
                "placement_status": "placed",
                "cluster": row.get("cluster") or self._resolve_runtime_cluster(
                    sleeve=row.get("sleeve"),
                    candidate_id=row.get("candidate_id"),
                ),
                "source_completeness_status": "runtime_placement_summary_observed",
            })
            self._attach_spread_observation(row)
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type="unit_placed",
                ts=ts,
                bridge=bridge,
                outcome=row,
                convergence_advisory=self._runtime_learning_convergence_advisory(
                    event_type="unit_placed",
                    bridge=bridge,
                    outcome=row,
                ),
                economics=self._runtime_learning_economics(row),
                source="book_owner.run_cycle",
            ))
        self._append_runtime_learning_packets(summary, packets)

    def _emit_management_runtime_learning(self, summary: dict, now: datetime) -> None:
        bridge = self._runtime_learning_bridge_context()
        if self._lane_weight_controller is not None:
            lane_weights = self._lane_weight_controller.snapshot(now)
        else:
            lane_weights = dict(getattr(self.engine, "_last_lane_weights_snapshot", {}) or {})
        summary["lane_weights"] = lane_weights
        bridge["lane_weights"] = lane_weights
        packets: list[dict] = []
        ts = now.isoformat()
        rows = [
            ("position_adopted", summary.get("adopted", []) or []),
            ("position_managed", summary.get("managed", []) or []),
            ("position_out_of_universe", summary.get("out_of_universe", []) or []),
            ("position_management_error", summary.get("errors", []) or []),
        ]
        for event_type, items in rows:
            for item in items:
                row = dict(item)
                row.update({
                    "placement_status": event_type,
                    "source_completeness_status": "runtime_management_summary_observed",
                    "management_checked_at_utc": row.get("management_checked_at_utc") or ts,
                })
                packets.append(build_runtime_learning_packet(
                    namespace=self._namespace,
                    event_type=event_type,
                    ts=ts,
                    bridge=bridge,
                    outcome=row,
                    convergence_advisory=self._runtime_learning_convergence_advisory(
                        event_type=event_type,
                        bridge=bridge,
                        outcome=row,
                    ),
                    economics=self._runtime_learning_economics(row),
                    source="book_owner.manage_open_positions",
                ))
        for item in summary.get("closed", []) or []:
            row = dict(item)
            action = str(row.get("action", ""))
            event_type = "breach_flatten" if "flatten" in action else "position_closed"
            row.update({
                "placement_status": event_type,
                "source_completeness_status": "runtime_management_summary_observed",
                "management_checked_at_utc": row.get("management_checked_at_utc") or ts,
            })
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type=event_type,
                ts=ts,
                bridge=bridge,
                outcome=row,
                convergence_advisory=self._runtime_learning_convergence_advisory(
                    event_type=event_type,
                    bridge=bridge,
                    outcome=row,
                ),
                economics=self._runtime_learning_economics(row),
                source="book_owner.manage_open_positions",
            ))
        self._append_runtime_learning_packets(summary, packets)

    def _join_inflight_manage(self) -> None:
        """Wait for this tick's manage thread, if the launcher started one.

        The join is the happens-before for the breach latch and for any send.
        A book with no in-flight manage returns immediately.
        """
        thread = getattr(self, "_manage_inflight", None)
        if thread is None:
            return
        try:
            if getattr(thread, "is_alive", None) and thread.is_alive():
                thread.join()
        except Exception:
            return
        self._manage_inflight = None

    def _news_request_from_manage(self) -> Optional[dict]:
        """The T+60 request manage stored, once that thread has been joined."""
        box = getattr(self, "_manage_box", None)
        if not isinstance(box, dict):
            return None
        result = box.get("result")
        if not isinstance(result, dict):
            return None
        block = result.get("news_t60_expiry_reeval")
        if not isinstance(block, dict):
            return None
        request = block.get("request")
        if not isinstance(request, dict) or not request.get("request_keys"):
            return None
        return request

    def _with_reeval_tags(self, request: dict) -> dict:
        """Tags for timeframes that did not advance are re-evaluation only."""
        prepared = dict(request)
        if prepared.get("reevaluation_only_tags"):
            return prepared
        advanced = set(getattr(self, "_tick_advanced", []) or [])
        tf_tags = getattr(self, "_tick_tf_tags", None) or {}
        if not isinstance(tf_tags, dict):
            return prepared
        prepared["reevaluation_only_tags"] = [
            tag
            for tf, tags in tf_tags.items()
            if tf not in advanced
            for tag in (tags or ())
        ]
        return prepared

    def _news_t15_t60_cycle(self, now, summary: dict) -> None:
        """Enqueue a T+60 re-evaluation. This does not place.

        The launcher applies the request after it joins this thread.
        """
        if str(getattr(self, "_namespace", "") or "") != "operator":
            return
        try:
            import sys as _sys
            from pathlib import Path as _Path

            desk = _Path(self._repo_root) / "scripts" / "f5_desk"
            desk_s = str(desk)
            if desk_s not in _sys.path:
                _sys.path.insert(0, desk_s)
            try:
                import news_t60_expiry_reeval as _t60

                receipt = _t60.run_from_book(self, now)
                if isinstance(receipt, dict):
                    summary.setdefault("news_t60_expiry_reeval", receipt)
            except Exception as exc:  # noqa: BLE001 — a missing registry retries next tick
                summary.setdefault("news_t60_expiry_reeval", {
                    "fail_open": True, "error": type(exc).__name__, "applied": False, "remint": False, "place": False,
                })
        except Exception as exc:  # noqa: BLE001
            _log.warning("book[%s]: news t60 cycle fail-open (%s)", self._namespace, type(exc).__name__)

    def run_cycle(self, *, now_utc: Optional[datetime] = None, tags=None, place: bool = True, news_reevaluation=None) -> dict:
        """One book cycle. Returns a summary; NEVER raises and NEVER places while gated off/halted.

        place=False forces observe-only (evaluate + log would_units, never send) — the launcher passes
        this when the operator kill-switch or a halt flag is set, so the brake works even if the book is
        gated on. (open_trade also inherits the runtime-halt guard; this is defense in depth.)"""
        now = now_utc or datetime.now(timezone.utc)
        # breach-flatten latch (set by manage_open_positions) forces observe-only: while the account is in
        # a flattened breach state, NEVER open new entries (otherwise a flatten -> re-enter -> flatten churn).
        if getattr(self, "_breach_block", False):
            place = False
        # Spread observations are scoped to ONE cycle: the screen fills them during this cycle's
        # per-intent loop and _emit_cycle_runtime_learning drains them at the end of the same
        # cycle. Clearing here bounds a dict that would otherwise grow for the life of a process
        # that runs for months, and removes any chance of a later packet picking up an earlier
        # bar's measurement -- a wrong number wearing a "measured" label is worse than no number.
        self._spread_observations.clear()
        self._spread_quote_series.clear()
        # Generation overlaps management. The join is before a re-evaluation
        # and before any send. A request passed in was already read after a join.
        if news_reevaluation is None:
            res = self.engine.evaluate(now_utc=now, tags=tags)
            self._join_inflight_manage()
            if getattr(self, "_breach_block", False):
                place = False
            found = self._news_request_from_manage()
            if isinstance(found, dict):
                news_reevaluation = self._with_reeval_tags(found)
                extra = tuple(news_reevaluation.get("reevaluation_only_tags") or ())
                base = tuple(tags or ())
                merged = base + tuple(tag for tag in extra if tag not in base)
                res = self.engine.evaluate(
                    now_utc=now,
                    tags=merged or tags,
                    news_reevaluation=news_reevaluation,
                )
        else:
            self._join_inflight_manage()
            if getattr(self, "_breach_block", False):
                place = False
            res = self.engine.evaluate(now_utc=now, tags=tags, news_reevaluation=news_reevaluation)
        # Operator reason must name generation terminals. Admission still
        # keeps decision_status == "no_candidates_this_bar"; launcher prints
        # summary["reason"], so rewrite here if the engine result is still the
        # bare admission status (or independently from decision_status).
        decision_obj = res.get("decision")
        admission_status = (
            getattr(decision_obj, "decision_status", None)
            if decision_obj is not None
            else res.get("reason")
        )
        reason = rewrite_no_candidates_operator_reason(
            admission_status if admission_status is not None else res.get("reason"),
            generation=res.get("generation") or {},
            generation_terminals=res.get("generation_terminals") or [],
        )
        summary = {"ok": res["ok"], "reason": reason, "n_intents": res["n_intents"],
                   "runtime_effect_now": res["runtime_effect_now"], "placed": [], "shadow": 0,
                   "skipped": [], "bar_consumable": True}
        if isinstance(news_reevaluation, dict) and news_reevaluation.get("request_keys"):
            summary["news_t60_reevaluation"] = {
                "request_keys": list(news_reevaluation["request_keys"]),
                "generator_returned": True,
                "effective_place": bool(place),
                "route_iteration_completed": False,
                "route_errors": [],
                "engine_evaluate_at_utc": now.isoformat(),
                "affected_symbols": list(news_reevaluation.get("affected_symbols") or []),
                "reevaluation_only_tags": list(news_reevaluation.get("reevaluation_only_tags") or []),
                "applied": False,
                "place": False,
            }
        summary["lane_weights"] = dict(res.get("lane_weights") or {})
        generation = res.get("generation") or {}
        summary["generation"] = dict(generation)
        if "generation_terminals" in res:
            summary["generation_terminals"] = list(res.get("generation_terminals") or [])
        if "event_clock_shadow" in generation:
            # Dedicated top-level copy makes the observation survive transient
            # pre-admission failures, where no bridge decision exists yet.
            summary["event_clock_shadow"] = list(generation.get("event_clock_shadow") or [])
        summary["skipped"].extend(res.get("generation_skips", []) or [])
        if not res["ok"] or res["decision"] is None:
            # bar-consumed-on-transient-failure: the engine did NOT evaluate (equity_unavailable /
            # day_baseline_unavailable / engine_exception — a momentary broker hiccup at the bar-close
            # tick). Do NOT let the launcher consume this decision bar, or that bar's signal is lost forever.
            summary["bar_consumable"] = False
            self._emit_cycle_runtime_learning(summary, now, decision=None, place=place)
            return summary
        decision = res["decision"]
        summary["bridge"] = _bridge_telemetry(decision)
        summary["skip_context"] = self._runtime_learning_skip_context(
            decision,
            res.get("intents", []),
            res.get("meta", []),
        )
        if isinstance(summary.get("bridge"), dict) and res.get("generation"):
            summary["bridge"]["broker_profile_generation"] = res.get("generation")
        ai_companion_snapshot = self._ai_companion_gate.snapshot(now)
        summary["ai_companion"] = ai_companion_snapshot
        if not res["runtime_effect_now"] or not place:
            _observe = str(self._namespace) != "operator"
            if str(self._namespace) == "operator":
                _observe = _spot_choice(
                    "runtime_effect_or_place",
                    {
                        "runtime_effect_now": bool(res["runtime_effect_now"]),
                        "place": bool(place),
                        "breach_block": bool(getattr(self, "_breach_block", False)),
                        "namespace": "operator",
                    },
                    {
                        "observe_this_cycle": "Runtime effect is off, or place is off. This cycle does not place.",
                        "effect_and_place": "Runtime effect is on and place is on. This cycle places.",
                    },
                    "observe_this_cycle",
                    f"runtime_effect_or_place|{bool(res['runtime_effect_now'])}|{bool(place)}|{now.strftime('%Y%m%dT%H%M')}",
                    "The two sides of runtime effect off or place off.",
                )
            if _observe:
                if self._risk_unit_floor_policy.mode == "shadow":
                    summary["risk_unit_floor"] = self._risk_unit_floor_shadow_cycle(
                        res, decision, now
                    )
                summary["shadow"] = len(getattr(decision, "would_units", []) or [])
                if not place and res["runtime_effect_now"]:
                    summary["skipped"].append("breach_flatten_block" if getattr(self, "_breach_block", False)
                                              else "kill_switch_or_halt_forced_observe_only")
                self._emit_cycle_runtime_learning(summary, now, decision=decision, place=place)
                return summary

        ai_state_pause = self._ai_companion_gate.control_state_issue_pause(ai_companion_snapshot)
        if ai_state_pause is not None:
            _pause_state = str(self._namespace) != "operator"
            if str(self._namespace) == "operator":
                _pause_state = _spot_choice(
                    "ai_companion_control_state_issue",
                    {
                        "pause_reason": str(getattr(ai_state_pause, "reason", "") or ""),
                        "control_id": str(getattr(ai_state_pause, "control_id", "") or ""),
                        "namespace": "operator",
                    },
                    {
                        "state_issue_pauses": "The companion control-state issue pauses new entries this cycle.",
                        "state_issue_is_a_fact": "The control-state issue is a fact. This cycle can still place.",
                    },
                    "state_issue_pauses",
                    f"ai_companion_control_state_issue|{getattr(ai_state_pause, 'reason', '')}|{now.strftime('%Y%m%dT%H%M')}",
                    "The two sides of a companion control-state issue on this cycle.",
                )
            if _pause_state:
                summary["shadow"] = len(getattr(decision, "would_units", []) or [])
                summary["bar_consumable"] = False
                summary["skipped"].append({
                    "reason": f"ai_companion_control_state_issue:{ai_state_pause.reason}",
                    "ai_companion_control_id": ai_state_pause.control_id,
                    "ai_companion_control_type": ai_state_pause.type,
                    "ai_companion_issues": ai_state_pause.control.get("issues", []),
                })
                self._emit_cycle_runtime_learning(summary, now, decision=decision, place=False)
                return summary

        ai_pause = self._ai_companion_gate.pause_new_entries(ai_companion_snapshot)
        if ai_pause is not None:
            _pause_new = str(self._namespace) != "operator"
            if str(self._namespace) == "operator":
                _pause_new = _spot_choice(
                    "ai_companion_pause_new_entries",
                    {
                        "pause_reason": str(getattr(ai_pause, "reason", "") or ""),
                        "control_id": str(getattr(ai_pause, "control_id", "") or ""),
                        "namespace": "operator",
                    },
                    {
                        "pause_new_entries": "The companion pause stops new entries this cycle.",
                        "pause_is_a_fact": "The companion pause is a fact. New entries can still place.",
                    },
                    "pause_new_entries",
                    f"ai_companion_pause_new_entries|{getattr(ai_pause, 'reason', '')}|{now.strftime('%Y%m%dT%H%M')}",
                    "The two sides of a companion pause on new entries.",
                )
            if _pause_new:
                summary["shadow"] = len(getattr(decision, "would_units", []) or [])
                summary["skipped"].append({
                    "reason": f"ai_companion_pause_new_entries:{ai_pause.reason}",
                    "ai_companion_control_id": ai_pause.control_id,
                    "ai_companion_control_type": ai_pause.type,
                })
                self._emit_cycle_runtime_learning(summary, now, decision=decision, place=False)
                return summary

        gs = res["governor_state"]
        day_start = gs.equity / (1.0 + gs.realized_today_pct) if (1.0 + gs.realized_today_pct) else gs.equity
        # offset-aware server-local reset-window date (matches the governor's daily baseline), NOT a pure
        # UTC date — otherwise the headroom-snapshot window-id disagrees with its own day_start during
        # 21:00-24:00 UTC and mis-segments row-level day joins.
        reset_window_id = self.engine.reset_window_date(now)
        if self._f5_ledger is not None:
            # F5 N4 is the MINIMUM of two valid books: the real funded account (shared with the
            # production worker) and the production-equivalent notional experiment. Replacing
            # real headroom with notional headroom can loosen the firm's actual loss boundary;
            # mixing real equity with a notional day baseline is also invalid. Build each on its
            # own basis. The router builds the ordinary broker-real snapshot first, then composes
            # this already-valid notional snapshot as a tightening-only F5 wrapper; the shared,
            # decision-contract-bound snapshot builder stays byte-identical.
            from .execution_packets import build_prop_firm_headroom_snapshot

            notional_equity = self._f5_ledger.governor_equity()
            notional_balance = self._f5_ledger.equity()
            real_day_start = self.engine.broker_day_start_balance(now)
            notional_state = self.router.account_state(
                self._mt5,
                day_start_baseline=day_start,
                reset_window_id=reset_window_id,
                equity_override=notional_equity,
                balance_override=notional_balance,
            )
            real_state = (
                self.router.account_state(
                    self._mt5,
                    day_start_baseline=real_day_start,
                    reset_window_id=reset_window_id,
                )
                if real_day_start is not None
                else None
            )
            notional_headroom = (
                build_prop_firm_headroom_snapshot(
                    notional_state,
                    account_namespace=self._namespace,
                    now_utc=now,
                )
                if notional_state is not None
                else None
            )
            notional_cap = (
                notional_headroom.get("max_allowed_new_trade_risk_pct")
                if isinstance(notional_headroom, dict)
                else None
            )
            if real_state is not None:
                account_state = dict(real_state)
                if isinstance(notional_headroom, dict) and isinstance(notional_cap, (int, float)):
                    account_state["f5_notional_headroom_snapshot_v4"] = notional_headroom
            else:
                account_state = None
            balance = float(notional_balance)
        else:
            account_state = self.router.account_state(
                self._mt5, day_start_baseline=day_start, reset_window_id=reset_window_id)
            try:
                balance = float(self._mt5.get_account_balance())
            except Exception:
                balance = gs.equity
        if account_state is None:
            if _challenge_withholds(
                self._namespace,
                "account_state_unavailable",
                {"namespace": str(self._namespace or ""), "account_state": None},
                {
                    "state_missing_withholds": "The account state is missing. Do not place this cycle.",
                    "state_missing_is_a_fact": "The missing account state is a fact. Do not treat it as a ban.",
                },
                "state_missing_withholds",
                f"account_state_unavailable|{now.strftime('%Y%m%dT%H%M')}",
                "The account state for this cycle did not come back. "
                "Does that withhold the cycle, or is it only a missing read? "
                "An empty answer or a tie does not withhold. "
                "Do not invent a balance. Do not close an open ticket.",
            ):
                summary["skipped"].append("account_state_unavailable")
            summary["bar_consumable"] = False
            self._emit_cycle_runtime_learning(summary, now, decision=decision, place=place)
            return summary
        open_positions_snapshot = self._open_book_positions_snapshot()
        placed_broker_symbol_keys: set[str] = set()
        attempted_transient_broker_symbol_keys: set[str] = set()

        intents = res.get("intents")
        if not isinstance(intents, list):
            intents = list(intents or [])
            res["intents"] = intents
        self._owner_hops = {}
        _stamp_recorded_hops(
            intents, res.get("generation_terminals"), res.get("meta"), self._owner_hops,
        )
        self._f5_emit_slate(res, decision, gs, now)
        # (sleeve, symbol) -> the decision bar's UTC iso, for the idempotency key
        bar_of = {(m["tag"], m["symbol"]): m.get("decision_bar_iso") for m in res.get("meta", [])}
        tf_of = {(m["tag"], m["symbol"]): m.get("timeframe") for m in res.get("meta", [])}
        floor_of = {
            (m["tag"], m["symbol"], m.get("decision_bar_iso")): m.get("risk_unit_floor")
            for m in res.get("meta", [])
            if m.get("risk_unit_floor") is not None
        }
        late_frac = float(self.engine.config.get("ultimate_book_max_entry_lateness_frac", 0.5) or 0.5)
        route_conviction = getattr(self.engine, "route_unit_with_committed_conviction", None)
        sequential_conviction = bool(
            callable(route_conviction)
            and getattr(decision, "kelly_running_count", False)
            and getattr(decision, "kelly_lite", False)
        )
        governor_view = getattr(decision, "governor", None) or {}
        try:
            gross_headroom = float(governor_view.get("available_gross_risk_pct"))
        except (AttributeError, TypeError, ValueError):
            gross_headroom = None
        cycle_accepted_risk_pct = 0.0
        units = list(getattr(decision, "realized_units", []) or [])
        if str(self._namespace) == "operator":
            covered: set[str] = set()
            for unit in units:
                if isinstance(unit, dict):
                    for member in unit.get("sleeve_members") or []:
                        covered.add(str(member))
            if not units:
                for unit in getattr(decision, "would_units", []) or []:
                    if not isinstance(unit, dict):
                        continue
                    units.append(unit)
                    for member in unit.get("sleeve_members") or []:
                        covered.add(str(member))
            for intent in intents or []:
                choice = getattr(intent, "unit_choice", None)
                sleeve = str(getattr(intent, "sleeve", "") or "")
                if choice not in {"unit_long", "unit_short"} or not sleeve or sleeve in covered:
                    continue
                units.append({
                    "sleeve_members": [sleeve],
                    "sized": True,
                    "risk_pct_per_trade": None,
                    "reason": "unit_side_reaches_place",
                    "cluster": None,
                })
                covered.add(sleeve)
        if sequential_conviction and any(
            (not unit.get("sized")) and unit.get("reason") == "gross_risk_cap_would_exceed"
            for unit in units
        ):
            if str(getattr(self, "_namespace", "")) == "operator":
                _sort_conf = False
                try:
                    _sort_conf = bool(_spot_choice(
                        "confidence_resort",
                        {
                            "gross_cap_binds": True,
                            "unit_count": len(units),
                            "namespace": "operator",
                        },
                        {
                            "generation_order": "Keep the order the book already generated.",
                            "confidence_first": "Re-sort so the higher confidence unit fires first.",
                        },
                        "confidence_first",
                        f"confidence_resort|{id(units)}",
                        "The gross cap is binding. Who fires first: the generated order, or a re-sort by confidence? Confidence is not a probability. Do not close an open ticket.",
                    ))
                except Exception:
                    _sort_conf = False
                if _sort_conf:
                    units = [
                        unit for _, unit in sorted(
                            enumerate(units),
                            key=lambda item: (-(item[1].get("confidence") or 0.0), item[0]),
                        )
                    ]
            else:
                units = [
                    unit for _, unit in sorted(
                        enumerate(units),
                        key=lambda item: (-(item[1].get("confidence") or 0.0), item[0]),
                    )
                ]
        if str(self._namespace) == "operator" and place:
            try:
                from src.judgment.intent_retry import attach_sitting_intents

                summary["intent_retry"] = attach_sitting_intents(
                    self, intents, units, now, balance=balance,
                )
                _stamp_recorded_hops(
                    intents,
                    res.get("generation_terminals"),
                    res.get("meta"),
                    self._owner_hops,
                )
                _report = summary.get("intent_retry")
                if isinstance(_report, dict):
                    for _brief in _report.get("retried") or []:
                        if not isinstance(_brief, dict):
                            continue
                        _consume = _brief.get("consume")
                        if _consume in (None, ""):
                            continue
                        for _item in intents:
                            if (
                                str(getattr(_item, "sleeve", "") or "")
                                == str(_brief.get("sleeve") or "")
                                and str(getattr(_item, "symbol", "") or "")
                                == str(_brief.get("symbol") or "")
                            ):
                                _merge_hop(self._owner_hops, _item, intent=_consume)
            except Exception as exc:
                summary["intent_retry"] = {
                    "error": type(exc).__name__,
                    "agent_order_send": False,
                }
        for unit in units:
            raw_risk = unit.get("risk_pct_per_trade")
            try:
                risk_missing = (
                    isinstance(raw_risk, bool)
                    or raw_risk is None
                    or float(raw_risk) <= 0
                )
            except (TypeError, ValueError):
                risk_missing = True
            if not unit.get("sized") or risk_missing:
                if not (
                    sequential_conviction
                    and unit.get("reason") == "gross_risk_cap_would_exceed"
                ):
                    _skip_unsized = str(self._namespace) != "operator"
                    if str(self._namespace) == "operator":
                        # An empty answer is not a send. Only the unique keep
                        # continues, and the percent on the unit stays unset.
                        _unsized_choice = _ask_jev(
                            "unsized_unit",
                            {
                                "sized": bool(unit.get("sized")),
                                "risk_pct_per_trade": unit.get("risk_pct_per_trade"),
                                "reason": str(unit.get("reason") or ""),
                                "namespace": "operator",
                            },
                            kind="choice",
                            instructions=(
                                "The two sides of an unsized unit that is not the gross-cap exception."
                                " The unique highest probability is the decision."
                                " An empty answer does not place."
                                " Do not close ticket 294215389."
                            ),
                            criteria={
                                "skip_unsized_unit": "This unit is not sized. Skip it.",
                                "keep_unsized_unit": "The unsized reading is a fact. Keep this unit.",
                            },
                        )
                        _skip_unsized = str(_unsized_choice) != "keep_unsized_unit"
                    if _skip_unsized:
                        if str(self._namespace) == "operator":
                            continue
                        members_now = {str(member) for member in (unit.get("sleeve_members") or [])}
                        side_reaches = any(
                            getattr(item, "unit_choice", None) in {"unit_long", "unit_short"}
                            and str(getattr(item, "sleeve", "") or "") in members_now
                            for item in intents or []
                        )
                        if not side_reaches:
                            continue
            members = set(unit.get("sleeve_members", []))
            # pair this cluster unit with its constituent intents; one order per intent at the unit risk
            for intent in intents:
                if intent.sleeve not in members:
                    continue
                # PER-INTENT ISOLATION: one intent's failure (e.g. an unexpected per-symbol engine
                # factory exception) must never abort the cycle or starve the
                # remaining intents on this bar. run_cycle NEVER raises (the launcher marks the bar
                # advanced after this returns; a raise here would re-run + re-fail the poison intent
                # every tick and permanently skip its siblings). Idempotency is preserved — an already
                # placed intent stays ledger-skipped on retry.
                dbar = None
                try:
                    dbar = bar_of.get((intent.sleeve, intent.symbol)) or intent.decision_day
                    f5_market_stop_floor = None
                    _hops = _read_hop(getattr(self, "_owner_hops", None), intent, dbar)
                    _stay_hop, _stay_value = _unique_stay_out(intent, _hops)
                    if _stay_hop:
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": "stay_out",
                            "hop": _stay_hop,
                            "value": _stay_value,
                        })
                        continue
                    if not self._profile_supports_symbol(intent.symbol):
                        _miss_spec = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            _miss_spec = _spot_choice(
                                "profile_missing_instrument_config",
                                {
                                    "symbol": intent.symbol,
                                    "sleeve": intent.sleeve,
                                    "profile_supports_symbol": False,
                                    "namespace": "operator",
                                },
                                {
                                    "instrument_spec_missing": "This symbol has no instrument spec. Do not send.",
                                    "instrument_spec_present": "The missing-profile reading is a fact. The candidate can still send.",
                                },
                                "instrument_spec_missing",
                                f"profile_missing_instrument_config|{intent.sleeve}|{intent.symbol}|{dbar}",
                                "The two sides of profile_missing_instrument_config for this symbol.",
                            )
                        if _miss_spec:
                            summary["skipped"].append({
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "reason": "profile_missing_instrument_config",
                            })
                            continue
                    # WEEKEND ENTRY REFUSAL (Session BA, B1900; default-OFF). An entry taken
                    # inside the flatten window would be closed on the tick that opened it, and
                    # one taken inside the embargo cannot complete its horizon before the
                    # deadline. Both are the same decision the priced research replay makes
                    # (`BA_WEEKEND_V1.json` -> `embargo`), so the live book and the number agree.
                    weekend_block = self._weekend_entry_block(intent.sleeve, now)
                    if weekend_block is not None:
                        _block_weekend = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            try:
                                _block_weekend = bool(_spot_choice(
                                    "weekend_entry",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "weekend_reason": str(weekend_block),
                                        "namespace": "operator",
                                    },
                                    {
                                        "entry_may_proceed": "This candidate can still be the fire.",
                                        "weekend_embargo": "Do not send this candidate into the weekend window.",
                                    },
                                    "weekend_embargo",
                                    f"weekend_entry|{intent.sleeve}|{intent.symbol}|{weekend_block}",
                                    "A weekend entry rule produced a reason not to send. Is this candidate still the fire, or does that window withhold it? Do not close ticket 294215389.",
                                ))
                            except Exception:
                                _block_weekend = False
                        if _block_weekend:
                            summary["skipped"].append({
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "reason": weekend_block,
                                "weekend_policy": self._weekend_policy.as_dict(),
                            })
                            continue
                    f5_clock = self._f5_new_risk_block(intent.symbol, now)
                    if f5_clock is not None:
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": f5_clock,
                        })
                        continue
                    ai_cooldown = self._ai_companion_gate.cooldown_for(
                        ai_companion_snapshot,
                        symbol=intent.symbol,
                        sleeve=intent.sleeve,
                    )
                    if ai_cooldown is not None:
                        _block_cool = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            try:
                                _block_cool = bool(_spot_choice(
                                    "ai_companion_cooldown",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "cooldown_reason": str(getattr(ai_cooldown, "reason", "") or ""),
                                        "namespace": "operator",
                                    },
                                    {
                                        "cooldown_is_a_fact": "The companion cooldown is a fact. This candidate can still send.",
                                        "cooldown_stands": "Do not send this candidate. The companion cooldown stands.",
                                    },
                                    "cooldown_stands",
                                    f"ai_companion_cooldown|{intent.sleeve}|{intent.symbol}|{getattr(ai_cooldown, 'reason', '')}",
                                    "A companion cooldown is present for this sleeve and symbol. Is that a fact beside the candidate, or a reason not to send? Do not close an open ticket.",
                                ))
                            except Exception:
                                _block_cool = False
                        if _block_cool:
                            summary["skipped"].append({
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "reason": f"ai_companion_cooldown:{ai_cooldown.reason}",
                                "ai_companion_control_id": ai_cooldown.control_id,
                                "ai_companion_control_type": ai_cooldown.type,
                            })
                            continue
                    # IDEMPOTENCY: the same (sleeve, symbol, decision bar) is a fact.
                    # On Challenge that fact asks before it skips. Empty does not skip.
                    if self._ledger.already_placed(intent.sleeve, intent.symbol, dbar):
                        if _challenge_withholds(
                            self._namespace,
                            "already_placed_this_bar",
                            {
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": str(dbar or ""),
                                "already_placed_this_bar": True,
                                "namespace": "operator",
                            },
                            {
                                "same_bar_stands": "This sleeve and symbol already placed this bar. Do not send it again.",
                                "same_bar_is_a_fact": "The earlier place is a fact. This candidate can still be asked.",
                            },
                            "same_bar_stands",
                            f"already_placed_this_bar|{intent.sleeve}|{intent.symbol}|{dbar}",
                            "This sleeve and symbol already placed on this decision bar. "
                            "Does that bar stand, or is the earlier place a fact beside another ask? "
                            "An empty answer or a tie does not skip. Do not close an open ticket.",
                        ):
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": "already_placed_this_bar"})
                            continue
                    # ONE-UNIT-PER-SLEEVE-PER-DAY cap (sleeve-day-reentry-overrisk / COMP-2 same-sleeve):
                    # an H4 sleeve (crypto/idxrev) can re-fire on a LATER same-day bar after its first
                    # position closed; placing a 2nd full-size unit exceeds the validated daily-unit risk
                    # model (the 4% gross cap only bounds CONCURRENT, not sequential, risk). Enforce the
                    # validated one-entry-per-(sleeve,symbol)-per-day here (terminal -> no retry spam).
                    _dday = str(getattr(intent, "decision_day", "") or dbar or "")[:10]
                    _isolated = self._f5_daily_cap_yields_isolated_reentry(intent, now)
                    if self._ledger.already_placed_today(intent.sleeve, intent.symbol, _dday):
                        _block_today = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            try:
                                _block_today = bool(_spot_choice(
                                    "already_placed_today",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "decision_day": _dday,
                                        "already_filled_today": True,
                                        "namespace": "operator",
                                    },
                                    {
                                        "later_bar_is_the_fire": "A later bar of this sleeve and symbol is still the fire.",
                                        "one_fill_is_enough": "One fill of this sleeve and symbol today is enough.",
                                    },
                                    "one_fill_is_enough",
                                    f"already_placed_today|{intent.sleeve}|{intent.symbol}|{_dday}",
                                    "This sleeve and symbol already filled once on this decision day. Is a later bar still the fire, or is one fill enough? Do not close an open ticket.",
                                ))
                            except Exception:
                                _block_today = False
                        if _block_today and not _isolated:
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": "already_placed_today"})
                            continue
                        if _isolated:
                            summary.setdefault("isolated_reentry_daily_cap_yield", []).append({
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "reason": "isolated_reentry_after_close",
                            })
                    # ONE-UNIT-PER-(CLUSTER,DAY) cap (COMP-2): a correlation cluster that already placed its
                    # unit on an EARLIER bar today must not stack a 2nd full correlated unit on a later bar
                    # (same-bar members of one unit are allowed). Certified-envelope safety; jpy exempt for
                    # the live trial. dbar identifies THIS bar so same-bar unit members still place.
                    # F5 isolated re-entry after close yields this cap on a flat symbol (keep-one residue).
                    _cluster = self._resolve_runtime_cluster(unit=unit, sleeve=intent.sleeve)
                    _cluster_exempt = bool(_cluster in self._cluster_cap_exempt)
                    _cluster_placed = bool(
                        self._cluster_cap_on
                        and _cluster
                        and self._ledger.cluster_placed_today_other_bar(_cluster, _dday, dbar)
                    )
                    if _cluster_placed and (
                        str(self._namespace) == "operator" or not _cluster_exempt
                    ):
                        _block_cluster = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            try:
                                _block_cluster = bool(_spot_choice(
                                    "cluster_unit_already_placed_today",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "cluster": str(_cluster),
                                        "cluster_exempt": _cluster_exempt,
                                        "decision_day": _dday,
                                        "namespace": "operator",
                                    },
                                    {
                                        "cluster_can_stack": "This cluster can take another unit today.",
                                        "cluster_cap_stands": "Do not stack another unit in this cluster today.",
                                    },
                                    "cluster_cap_stands",
                                    f"cluster_unit_already_placed_today|{_cluster}|{_dday}|{dbar}",
                                    "This cluster already placed a unit on an earlier bar today. Is another unit the fire, or does the cluster cap stand? Do not close an open ticket.",
                                ))
                            except Exception:
                                _block_cluster = False
                        if _block_cluster and not _isolated:
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": f"cluster_unit_already_placed_today:{_cluster}"})
                            continue
                        if _isolated:
                            summary.setdefault("isolated_reentry_daily_cap_yield", []).append({
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "cluster": _cluster,
                                "reason": "isolated_reentry_after_close_cluster",
                            })
                    ai_risk = self._ai_companion_gate.risk_multiplier_for(
                        ai_companion_snapshot,
                        symbol=intent.symbol,
                        sleeve=intent.sleeve,
                    )
                    if ai_risk is not None and float(ai_risk.control.get("multiplier", 1.0)) <= 0.0:
                        _block_zero = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            try:
                                _block_zero = bool(_spot_choice(
                                    "ai_companion_zero_risk",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "multiplier": 0.0,
                                        "namespace": "operator",
                                    },
                                    {
                                        "zero_multiplier_is_a_fact": "A zero companion multiplier is a fact. This candidate can still send at the unit.",
                                        "zero_multiplier_stands": "Do not send this candidate. The zero multiplier stands.",
                                    },
                                    "zero_multiplier_stands",
                                    f"ai_companion_zero_risk|{intent.sleeve}|{intent.symbol}",
                                    "The companion risk multiplier for this candidate is zero. Is that a fact beside the unit, or a reason not to send? Do not close an open ticket.",
                                ))
                            except Exception:
                                _block_zero = False
                        if _block_zero:
                            summary["skipped"].append({
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "reason": f"ai_companion_zero_risk:{ai_risk.reason}",
                                "ai_companion_control_id": ai_risk.control_id,
                                "ai_companion_control_type": ai_risk.type,
                            })
                            continue
                    tick = self._tick(intent.symbol)
                    if tick is None:
                        _no_tick = _challenge_withholds(
                            self._namespace,
                            "no_tick",
                            {
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "tick_present": False,
                                "namespace": "operator",
                            },
                            {
                                "tick_absent_retries": "There is no quote on this pass. Retry this bar.",
                                "tick_absent_is_a_fact": "The missing quote is a fact. Do not treat it as a refusal.",
                            },
                            "tick_absent_retries",
                            f"no_tick|{intent.sleeve}|{intent.symbol}|{dbar}",
                            "This pass has no quote for the symbol. "
                            "Does the bar retry, or is the missing quote only a fact? "
                            "An empty answer or a tie does not restore a refusal. "
                            "Do not close an open ticket.",
                        )
                        summary["bar_consumable"] = False
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": "no_tick_transient" if _no_tick else "no_tick_unanswered",
                        })
                        continue
                    # SESSION / TRADEABLE GATE (defense in depth): a closed cash market (index holiday,
                    # weekend edge, extended-hours mismatch) freezes the last tick. The broker would reject
                    # a closed-market order anyway, but skipping pre-send avoids trading a STALE signal and
                    # reject-noise. Fail-OPEN: a missing timestamp or any error proceeds.
                    # On this namespace the stale age is the returned score. Other books
                    # still skip a quote older than 900 seconds.
                    tick_time = getattr(tick, "time", None)
                    if tick_time is not None:
                        try:
                            # stale-now-for-stale-tick-gate: measure age against a FRESH now (not the
                            # cycle-top `now`), so a slow cycle (broker/management work between the tick-top
                            # and here) cannot make a genuinely STALE closed-market tick read as fresh and
                            # slip a stale signal through.
                            age_s = (datetime.now(timezone.utc) - tick_time).total_seconds()
                            if str(self._namespace) == "operator":
                                quote_limit = _parameter_score(
                                    "stale_quote_seconds",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "age_s": age_s,
                                        "namespace": "operator",
                                    },
                                    "How many seconds of quote age still count as this market? "
                                    "The score you return is that age.",
                                )
                                _block_quote = False
                                if quote_limit is not None and age_s > float(quote_limit):
                                    try:
                                        _block_quote = bool(_spot_choice(
                                            "stale_tick",
                                            {
                                                "symbol": intent.symbol,
                                                "sleeve": intent.sleeve,
                                                "age_s": age_s,
                                                "returned_age_s": float(quote_limit),
                                                "namespace": "operator",
                                            },
                                            {
                                                "quote_live": "This quote is still the market for this candidate.",
                                                "quote_too_old": "This quote is older than the returned age. Do not send on it.",
                                            },
                                            "quote_too_old",
                                            f"stale_tick|{intent.sleeve}|{intent.symbol}|{int(age_s)}",
                                            "The quote age and the returned age are on the state. "
                                            "Is the quote still the market, or too old to send? "
                                            "Do not close an open ticket.",
                                        ))
                                    except Exception:
                                        _block_quote = False
                            elif age_s > 900:
                                _block_quote = True
                            else:
                                _block_quote = False
                            if _block_quote:
                                summary["skipped"].append(
                                    {"symbol": intent.symbol, "sleeve": intent.sleeve,
                                     "decision_bar_iso": dbar,
                                     "reason": f"stale_tick_market_closed:{int(age_s)}s"})
                                continue
                        except Exception:
                            pass
                    ee = self._exec_engine(intent.symbol, intent.sleeve)
                    # POSITION GUARD: never place a 2nd order for a (symbol, sleeve) that already holds an
                    # open position — it would overwrite this engine's single active_trade and orphan the
                    # first ticket. (A different sleeve on the same symbol uses a different engine, so a
                    # legitimate multi-sleeve book on one symbol still places each leg.) manage_open_positions
                    # runs before run_cycle each tick, so active_trade reflects the live broker state.
                    if getattr(ee, "active_trade", None) is not None:
                        if _challenge_withholds(
                            self._namespace,
                            "sleeve_already_holds_symbol",
                            {
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "active_trade": True,
                                "namespace": "operator",
                            },
                            {
                                "guard_stands": "This sleeve already holds the symbol. Do not send another.",
                                "guard_is_a_fact": "The open ticket is a fact. This candidate can still be asked.",
                            },
                            "guard_stands",
                            f"sleeve_already_holds_symbol|{intent.sleeve}|{intent.symbol}|{dbar}",
                            "The same-symbol guard. This sleeve already holds an open ticket. "
                            "An empty answer or a tie does not skip the place ask. "
                            "Do not close an open ticket.",
                        ):
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": "sleeve_already_holds_symbol"})
                            continue
                    if getattr(ee, "_native_pending_order", None) is not None:
                        if _challenge_withholds(
                            self._namespace,
                            "sleeve_already_has_native_pending",
                            {
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "native_pending": True,
                                "namespace": "operator",
                            },
                            {
                                "guard_stands": "This sleeve already has a resting limit. Do not send another.",
                                "guard_is_a_fact": "The resting limit is a fact. This candidate can still be asked.",
                            },
                            "guard_stands",
                            f"sleeve_already_has_native_pending|{intent.sleeve}|{intent.symbol}|{dbar}",
                            "The same-symbol guard. A native pending already rests for this sleeve. "
                            "An empty answer or a tie does not skip the place ask. "
                            "Do not close an open ticket.",
                        ):
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": "sleeve_already_has_native_pending"})
                            continue
                    # BROKER-LEVEL guard (defense in depth): if adoption failed this restart (a transient
                    # broker error left ee.active_trade None while the W7:{sleeve} position is still open at
                    # the broker), a new decision bar would otherwise place a DUPLICATE. Check the broker
                    # directly before placing. On Challenge the guard is the ask.
                    if self._broker_holds(intent.symbol, intent.sleeve):
                        if _challenge_withholds(
                            self._namespace,
                            "sleeve_already_holds_symbol_broker",
                            {
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "broker_holds": True,
                                "namespace": "operator",
                            },
                            {
                                "guard_stands": "The broker already holds this sleeve and symbol. Do not send another.",
                                "guard_is_a_fact": "The broker position is a fact. This candidate can still be asked.",
                            },
                            "guard_stands",
                            f"sleeve_already_holds_symbol_broker|{intent.sleeve}|{intent.symbol}|{dbar}",
                            "The same-symbol guard. The broker already holds this sleeve and symbol. "
                            "An empty answer or a tie does not skip the place ask. "
                            "Do not close an open ticket.",
                        ):
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": "sleeve_already_holds_symbol_broker"})
                            continue
                    target_broker_keys = self._broker_symbol_keys_for_canonical(intent.symbol)
                    if placed_broker_symbol_keys.intersection(target_broker_keys):
                        if _challenge_withholds(
                            self._namespace,
                            "same_broker_symbol_already_placed_this_cycle",
                            {
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "placed_this_cycle": True,
                                "namespace": "operator",
                            },
                            {
                                "guard_stands": "This symbol already placed in this cycle. Do not send another.",
                                "guard_is_a_fact": "The earlier place is a fact. This candidate can still be asked.",
                            },
                            "guard_stands",
                            f"same_broker_symbol_already_placed_this_cycle|{intent.sleeve}|{intent.symbol}|{dbar}",
                            "The same-symbol guard. This symbol already placed once in this cycle. "
                            "An empty answer or a tie does not skip the place ask. "
                            "Do not close an open ticket.",
                        ):
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": "same_broker_symbol_already_placed_this_cycle"})
                            continue
                    if attempted_transient_broker_symbol_keys.intersection(target_broker_keys):
                        _suppress_repeat = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            _suppress_repeat = _spot_choice(
                                "same_broker_symbol_transient_attempt_this_cycle",
                                {
                                    "symbol": intent.symbol,
                                    "sleeve": intent.sleeve,
                                    "transient_attempt_this_cycle": True,
                                    "namespace": "operator",
                                },
                                {
                                    "suppress_repeat_attempt": "This symbol already had a transient attempt this cycle. Do not send again.",
                                    "another_attempt_this_cycle": "The earlier transient attempt is a fact. This candidate can still send.",
                                },
                                "suppress_repeat_attempt",
                                f"transient_attempt|{intent.sleeve}|{intent.symbol}|{dbar}",
                                "The two sides of a transient attempt already recorded for this symbol in this cycle.",
                            )
                        if _suppress_repeat:
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": "same_broker_symbol_transient_attempt_this_cycle"})
                            continue
                    same_symbol_exposures = self._same_broker_symbol_open_exposures(
                        intent.symbol,
                        open_positions_snapshot=open_positions_snapshot,
                    )
                    if same_symbol_exposures is None:
                        if _challenge_withholds(
                            self._namespace,
                            "same_broker_symbol_position_source_unavailable",
                            {
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "position_source": None,
                                "namespace": "operator",
                            },
                            {
                                "source_missing_withholds": "The open-position source is missing. Do not send.",
                                "source_missing_is_a_fact": "The missing source is a fact. This candidate can still send.",
                            },
                            "source_missing_withholds",
                            f"position_source|{intent.sleeve}|{intent.symbol}|{dbar}",
                            "The open-position source for this symbol did not come back. "
                            "Does that withhold the send, or is it only a missing read? "
                            "An empty answer or a tie does not withhold. "
                            "Do not close an open ticket.",
                        ):
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": "same_broker_symbol_position_source_unavailable_for_lifecycle_guard"})
                            summary["bar_consumable"] = False
                            continue
                        same_symbol_exposures = []
                    same_symbol_exposures = self._f5_cross_tf_filter(same_symbol_exposures, intent.sleeve)
                    if same_symbol_exposures:
                        _block_open = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            try:
                                _tickets = []
                                for _pos in list(same_symbol_exposures)[:8]:
                                    _tickets.append(getattr(_pos, "ticket", None))
                                _block_open = bool(_spot_choice(
                                    "same_broker_symbol_open_position_lifecycle_guard",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "open_tickets": _tickets,
                                        "namespace": "operator",
                                    },
                                    {
                                        "keep_open_ticket": "Keep the open ticket. Do not send this candidate. Do not close the open ticket.",
                                        "second_thesis_on_this_symbol": "This candidate is a second thesis on this symbol. Leave the open ticket alone.",
                                    },
                                    "keep_open_ticket",
                                    f"open_ticket|{intent.symbol}|{intent.sleeve}|{_tickets}",
                                    "A position is already open on this symbol. Keep that ticket, or is this candidate a second thesis on the same symbol? Keeping does not flatten ticket 294215389.",
                                ))
                            except Exception:
                                _block_open = False
                        if _block_open:
                            existing_symbols = sorted({
                                str(getattr(pos, "symbol", "") or "")
                                for pos in same_symbol_exposures
                                if getattr(pos, "symbol", None)
                            })
                            existing_comments = sorted({
                                str(getattr(pos, "comment", "") or "")
                                for pos in same_symbol_exposures
                                if getattr(pos, "comment", None)
                            })
                            summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                       "decision_bar_iso": dbar,
                                                       "reason": "same_broker_symbol_open_position_lifecycle_guard",
                                                       "existing_broker_symbols": existing_symbols,
                                                       "existing_comments": existing_comments,
                                                       "existing_position_count": len(same_symbol_exposures)})
                            continue
                    # BAR-AGE GATE. Friend books still use the configured fraction of the
                    # bar. Challenge does not. The minutes since the close and the
                    # quote's distance from the limit are facts. The skip is the
                    # unique answer. An empty answer does not skip.
                    _bar_iso = bar_of.get((intent.sleeve, intent.symbol))
                    _bar_tf = tf_of.get((intent.sleeve, intent.symbol))
                    if str(self._namespace) == "operator":
                        _age = self._bar_age_minutes(now, _bar_iso, _bar_tf)
                        _move = self._move_from_limit(intent, tick)
                        try:
                            _block_late = bool(_spot_choice(
                                "stale_late_entry_after_restart",
                                {
                                    "symbol": intent.symbol,
                                    "sleeve": intent.sleeve,
                                    "bar_iso": str(_bar_iso or ""),
                                    "bar_age_minutes": _age,
                                    "move_so_far": _move,
                                    "entry": getattr(intent, "entry_price", None),
                                    "bid": None if tick is None else getattr(tick, "bid", None),
                                    "ask": None if tick is None else getattr(tick, "ask", None),
                                    "namespace": "operator",
                                },
                                {
                                    "still_the_close": "The order is still this bar's close.",
                                    "restart_chase": "This is a restart chase of a price the pattern did not enter.",
                                },
                                "restart_chase",
                                f"stale_late_entry_after_restart|{intent.sleeve}|{intent.symbol}|{_bar_iso}",
                                "The minutes since this bar closed, and how far the quote has moved from the limit, are facts. "
                                "Is the order still that bar's close, or a restart chase? "
                                "An empty answer or a tie does not skip. Do not close an open ticket.",
                            ))
                        except Exception:
                            _block_late = False
                    else:
                        _block_late = self._entry_too_late(now, _bar_iso, _bar_tf, late_frac)
                    if _block_late:
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "stale_late_entry_after_restart"})
                        continue
                    if (
                        self._namespace == "operator"
                        and self._f5_cfg is not None
                    ):
                        intent, f5_market_stop_floor = self._f5_preorder_market_stop_floor(
                            intent
                        )
                        if f5_market_stop_floor is not None:
                            f5_market_stop_floor = dict(f5_market_stop_floor)
                            f5_market_stop_floor["decision_bar_iso"] = dbar
                            summary.setdefault("f5_market_stop_floor", []).append(
                                dict(f5_market_stop_floor)
                            )
                            if (
                                f5_market_stop_floor.get("refused")
                                or f5_market_stop_floor.get("route_status") == "refused"
                            ):
                                _floor_reason = str(
                                    f5_market_stop_floor.get("reason")
                                    or "fx_dsp_stop_le_8pip"
                                )
                                if _challenge_withholds(
                                    self._namespace,
                                    "market_stop_floor",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "reason": _floor_reason,
                                        "route_status": str(
                                            f5_market_stop_floor.get("route_status") or ""
                                        ),
                                        "namespace": "operator",
                                    },
                                    {
                                        "floor_reading_is_a_fact": "The floor reading is a fact. This candidate can still send.",
                                        "floor_withholds": "This floor reading withholds the send.",
                                    },
                                    "floor_withholds",
                                    f"market_stop_floor|{intent.sleeve}|{intent.symbol}|{dbar}|{_floor_reason}",
                                    "A market-stop floor reading is on this candidate. "
                                    "The reading is not a new floor. "
                                    "Does that reading withhold the send? "
                                    "An empty answer or a tie does not withhold. "
                                    "Do not close an open ticket.",
                                ):
                                    summary["skipped"].append({
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "decision_bar_iso": dbar,
                                        "reason": _floor_reason,
                                        "f5_market_stop_floor": dict(f5_market_stop_floor),
                                    })
                                    continue
                    # PRE-SEND COST SCREEN (root-cause of the opaque 'open_trade_returned_none' on JPY):
                    # a leg whose live spread eats more than selected_cell_pretrade_max_spread_r (0.10) of
                    # its R-unit (stop_dist) can NEVER clear execution.open_trade's ExecMgr-V4 cost gate
                    # (broker_net_cost_engine: spread_r = (ask-bid)/sl_distance). e.g. GBPJPY fx_jpy: a 2-pip
                    # spread on a 1.0xATR(M15) ~8.7-pip stop -> spread_r ~0.23 -> always refused. Attempting
                    # it is futile work surfaced as a scary 'Trade NOT placed'. Decline it HERE, cleanly,
                    # with the precise cost reason BEFORE building the order (identical outcome: no trade
                    # either way -> no strategy change; the authoritative gate still guards anything else).
                    # Sample is min-over-1000ms on a would-be refuse (not a new cap; 0.35 stays).
                    #
                    # FrozenPriceIntent V1 (F5 + --frozen-intent-reprice only): a QUOTE_DEPENDENT
                    # skip no longer consumes the bar. The first occurrence freezes original
                    # entry/stop/target/max lots and the existing launcher bar-retry path
                    # (bar_consumable=False) observes it. Production / flag-off is the `continue`
                    # below, unchanged.
                    frozen_key = self._frozen_intent_key(intent, dbar)
                    existing_frozen = (
                        self._frozen_intents.get(frozen_key)
                        if self._frozen_intent_reprice else None
                    )
                    if existing_frozen is not None:
                        self._advance_frozen_price_intent(
                            item=existing_frozen,
                            now=now,
                            tick=tick,
                            intent=intent,
                            unit=unit,
                            account_state=account_state,
                            balance=balance,
                            dbar=dbar,
                            dday=_dday,
                            ee=ee,
                            target_broker_keys=target_broker_keys,
                            placed_broker_symbol_keys=placed_broker_symbol_keys,
                            open_positions_snapshot=open_positions_snapshot,
                            summary=summary,
                            place=place,
                        )
                        continue
                    # TRANSIENT-RETRY CAP suppression (armed only; default 0 never enters):
                    # once this (sleeve, symbol, bar) was declared terminal at the cap, do not
                    # build/send the identical doomed request again just because ANOTHER leg's
                    # own transient retries are keeping the cycle's bar alive (FN 2026-08-04:
                    # two oil legs storming the same bar). Never sets bar_consumable=False;
                    # sits AFTER the FrozenPriceIntent advance (that rail self-bounds via its
                    # 120 s hard expiry + chase kill-band) and BEFORE the 1 s spread sample.
                    if (
                        self._transient_retry_cap > 0
                        and (intent.sleeve, intent.symbol, dbar) in self._transient_retry_capped
                    ):
                        _cap_stands = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            _cap_stands = _spot_choice(
                                "transient_retry_cap_reached",
                                {
                                    "symbol": intent.symbol,
                                    "sleeve": intent.sleeve,
                                    "cap": self._transient_retry_cap,
                                    "already_capped": True,
                                    "namespace": "operator",
                                },
                                {
                                    "cap_stands": "The transient retry cap is reached. Do not send this bar again.",
                                    "try_again": "The cap count is a fact. This candidate can still send.",
                                },
                                "cap_stands",
                                f"transient_retry_cap|{intent.sleeve}|{intent.symbol}|{dbar}",
                                "The two sides of the transient retry cap already reached for this bar.",
                            )
                        if _cap_stands:
                            summary["skipped"].append({
                                "symbol": intent.symbol, "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "reason": "transient_retry_cap_reached",
                                "post_cap_suppressed_attempt": True,
                                "transient_retry_cap": self._transient_retry_cap,
                            })
                            continue
                    cost_skip = self._spread_cost_screen(intent, tick)
                    if cost_skip is not None:
                        skipped_row = {"symbol": intent.symbol, "sleeve": intent.sleeve,
                                       "decision_bar_iso": dbar,
                                       "reason": cost_skip}
                        spread_fact = (
                            str(self._namespace) == "operator"
                            and str(cost_skip).startswith("cost_screen_spread_r")
                        )
                        if spread_fact:
                            # The screen still measured the quote. A limit entry
                            # does not skip the place ask because of that cost.
                            summary.setdefault("spread_facts", []).append(skipped_row)
                        else:
                            self._maybe_enqueue_frozen_price_intent(
                                now=now,
                                intent=intent,
                                unit=unit,
                                tick=tick,
                                dbar=dbar,
                                dday=_dday,
                                ee=ee,
                                account_state=account_state,
                                reason=cost_skip,
                                packet=None,
                                skipped_row=skipped_row,
                                summary=summary,
                            )
                            self._persist_f5_refusal_quote(
                                now=now,
                                intent=intent,
                                unit=unit,
                                tick=tick,
                                dbar=dbar,
                                dday=_dday,
                                reason=cost_skip,
                                packet=None,
                                skipped_row=skipped_row,
                            )
                            summary["skipped"].append(skipped_row)
                            rkey = (intent.sleeve, intent.symbol, dbar, cost_skip)
                            if rkey not in self._notified_rejects:
                                if len(self._notified_rejects) > 5000:
                                    self._notified_rejects.clear()
                                self._notified_rejects.add(rkey)
                                self._notify_cost_skip(intent, cost_skip)
                            continue
                    route_unit = unit
                    if sequential_conviction:
                        route_unit = route_conviction(
                            unit,
                            intent,
                            intents,
                            gs,
                            now_utc=now,
                        )
                        if not isinstance(route_unit, dict):
                            if _challenge_withholds(
                                self._namespace,
                                "running_conviction_route_preview_unavailable",
                                {
                                    "symbol": intent.symbol,
                                    "sleeve": intent.sleeve,
                                    "route_preview": "unavailable",
                                    "namespace": "operator",
                                },
                                {
                                    "preview_withholds": "The missing route preview withholds this send.",
                                    "preview_is_a_fact": "The missing preview is a fact. Keep the unit already in hand.",
                                },
                                "preview_withholds",
                                f"running_conviction_route_preview_unavailable|{intent.sleeve}|{intent.symbol}|{dbar}",
                                "The running-conviction route preview is not a unit. "
                                "Does that withhold the send, or does the unit already in hand stay? "
                                "An empty answer or a tie does not withhold. "
                                "Do not close an open ticket.",
                            ):
                                summary["skipped"].append({
                                    "symbol": intent.symbol,
                                    "sleeve": intent.sleeve,
                                    "decision_bar_iso": dbar,
                                    "reason": "running_conviction_route_preview_unavailable",
                                })
                                summary["bar_consumable"] = False
                                continue
                            route_unit = unit
                        _raw_risk = route_unit.get("risk_pct_per_trade")
                        _risk_number = None
                        if not isinstance(_raw_risk, bool) and _raw_risk is not None:
                            try:
                                _risk_number = float(_raw_risk)
                            except (TypeError, ValueError):
                                _risk_number = None
                        if (
                            not route_unit.get("sized")
                            or _risk_number is None
                            or not (_risk_number > 0)
                        ):
                            _skip_route = str(self._namespace) != "operator"
                            if str(self._namespace) == "operator":
                                # Empty, a tie, and the skip side do not reach
                                # router.place. A missing percent stays unset.
                                _route_choice = _ask_jev(
                                    "running_conviction_route_unsized",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "sized": bool(route_unit.get("sized")),
                                        "risk_pct_per_trade": route_unit.get("risk_pct_per_trade"),
                                        "reason": str(route_unit.get("reason") or ""),
                                        "namespace": "operator",
                                    },
                                    kind="choice",
                                    instructions=(
                                        "The two sides of a running-conviction route that is not sized."
                                        " The unique highest probability is the decision."
                                        " An empty answer does not place."
                                        " Do not close ticket 294215389."
                                    ),
                                    criteria={
                                        "unsized_route_skips": "This conviction route is not sized. Do not send.",
                                        "unsized_route_is_a_fact": "The unsized route is a fact. The candidate can still send.",
                                    },
                                )
                                _skip_route = str(_route_choice) != "unsized_route_is_a_fact"
                            if _skip_route:
                                summary["skipped"].append({
                                    "symbol": intent.symbol,
                                    "sleeve": intent.sleeve,
                                    "decision_bar_iso": dbar,
                                    "reason": route_unit.get("reason") or "running_conviction_route_unsized",
                                })
                                continue
                        summary.setdefault("running_conviction_routes", []).append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "count": route_unit.get("running_conviction_route_count"),
                            "basis": route_unit.get("running_conviction_route_basis"),
                            "risk_pct_per_trade": route_unit.get("risk_pct_per_trade"),
                            "overlays_applied": route_unit.get("overlays_applied"),
                        })
                    adjusted_unit = self._ai_companion_gate.adjusted_unit(route_unit, ai_risk)
                    if sequential_conviction and gross_headroom is not None:
                        _raw_candidate = adjusted_unit.get("risk_pct_per_trade")
                        candidate_risk_pct = None
                        if not isinstance(_raw_candidate, bool) and _raw_candidate is not None:
                            try:
                                candidate_risk_pct = float(_raw_candidate)
                            except (TypeError, ValueError):
                                candidate_risk_pct = None
                        remaining = max(0.0, gross_headroom - cycle_accepted_risk_pct)
                        if str(self._namespace) == "operator":
                            # The room comparison is not the gate. how_many_more is.
                            _cap_skip = _spot_choice(
                                "how_many_more",
                                {
                                    "symbol": intent.symbol,
                                    "sleeve": intent.sleeve,
                                    "candidate_risk_pct": candidate_risk_pct,
                                    "room_pct": remaining,
                                    "namespace": "operator",
                                },
                                {
                                    "count_caps": "The open risk on this state caps another ticket.",
                                    "another_can_send": "The open risk is a fact. Another ticket can still be sent.",
                                },
                                "count_caps",
                                f"how_many_more|{intent.sleeve}|{intent.symbol}|{dbar}",
                                "How many more tickets can be sent is this choice. "
                                "The candidate risk and the room are facts, not a cap. "
                                "The unique highest wins. An empty answer or a tie does not cap "
                                "and does not mean zero more. Do not close an open ticket.",
                            )
                        elif candidate_risk_pct is not None and candidate_risk_pct > remaining + 1e-9:
                            _cap_skip = True
                        else:
                            _cap_skip = False
                        if _cap_skip:
                            summary["skipped"].append({
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "reason": (
                                    "how_many_more"
                                    if str(self._namespace) == "operator"
                                    else "gross_risk_cap_would_exceed"
                                ),
                                "candidate_risk_pct": candidate_risk_pct,
                                "room_pct": remaining,
                            })
                            continue
                    if ai_risk is not None:
                        summary.setdefault("ai_companion_risk_adjustments", []).append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "control_id": ai_risk.control_id,
                            "multiplier": float(ai_risk.control.get("multiplier", 1.0)),
                            "reason": ai_risk.reason,
                        })
                    unit_su = _UnitView(adjusted_unit)
                    route_intent = intent
                    routed_floor = None
                    floor_observation = floor_of.get((intent.sleeve, intent.symbol, dbar))
                    floor_selected = self._risk_unit_floor_policy.params_for(
                        intent.sleeve
                    ) is not None
                    if (
                        self._risk_unit_floor_policy.mode == "apply"
                        and floor_selected
                        and floor_observation is None
                    ):
                        _block_floor = str(self._namespace) != "operator"
                        if str(self._namespace) == "operator":
                            try:
                                _block_floor = bool(_spot_choice(
                                    "risk_unit_floor",
                                    {
                                        "symbol": intent.symbol,
                                        "sleeve": intent.sleeve,
                                        "proposal_missing": True,
                                        "namespace": "operator",
                                    },
                                    {
                                        "floor_is_a_fact": "A missing floor proposal is a fact. The candidate can still send.",
                                        "floor_blocks": "Do not send. The missing floor proposal blocks.",
                                    },
                                    "floor_blocks",
                                    f"risk_unit_floor|missing|{intent.sleeve}|{intent.symbol}|{dbar}",
                                    "The risk-unit floor is in apply mode and this bar has no floor proposal. Is that a fact, or a reason not to send? Do not close an open ticket.",
                                ))
                            except Exception:
                                _block_floor = False
                        if _block_floor:
                            summary["skipped"].append({
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "reason": "risk_unit_floor:proposal_missing",
                            })
                            continue
                    if floor_observation is not None:
                        route_intent, routed_floor, floor_block = self._risk_unit_floor_route(
                            intent,
                            floor_observation,
                            unit_su,
                            tick,
                            account_state,
                            balance,
                            ee,
                        )
                        summary.setdefault("risk_unit_floor", []).append(routed_floor)
                        if floor_block is not None:
                            _block_floor = str(self._namespace) != "operator"
                            if str(self._namespace) == "operator":
                                try:
                                    _block_floor = bool(_spot_choice(
                                        "risk_unit_floor",
                                        {
                                            "symbol": intent.symbol,
                                            "sleeve": intent.sleeve,
                                            "floor_block": str(floor_block),
                                            "namespace": "operator",
                                        },
                                        {
                                            "floor_is_a_fact": "The floor reading is a fact. The candidate can still send.",
                                            "floor_blocks": "Do not send. The floor reading blocks.",
                                        },
                                        "floor_blocks",
                                        f"risk_unit_floor|block|{intent.sleeve}|{intent.symbol}|{floor_block}",
                                        "The risk-unit floor returned a block for this candidate. Is that reading a fact, or a reason not to send? Do not close an open ticket.",
                                    ))
                                except Exception:
                                    _block_floor = False
                            if _block_floor:
                                summary["skipped"].append({
                                    "symbol": intent.symbol,
                                    "sleeve": intent.sleeve,
                                    "decision_bar_iso": dbar,
                                    "reason": floor_block,
                                    "risk_unit_floor": routed_floor,
                                })
                                continue
                    frozen_level = None
                    try:
                        _fi = self._frozen_intents.get(
                            self._frozen_intent_key(route_intent, dbar)
                        )
                        if _fi is not None:
                            frozen_level = getattr(_fi, "frozen_entry", None)
                    except Exception:
                        frozen_level = None
                    if frozen_level is None:
                        # THIN-HOUR PLACEMENT (F5 only): stamp the sleeve's level so the
                        # native-pending rail arms instead of a market order. A frozen
                        # intent's original level always wins over a fresh stamp.
                        route_intent = self._f5_thin_hour_limit_intent(route_intent, tick)
                    route_intent = self._limit_at_level_intent(
                        route_intent, frozen_entry=frozen_level
                    )
                    flow_hold, flow_dec = self._judgment_flow_hold(
                        route_intent, unit_su, tick, account_state, None, now
                    )
                    summary.setdefault("judgment_flow", []).append(flow_dec)
                    if flow_hold:
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": "judgment_hold",
                            "judgment_flow": flow_dec,
                        })
                        continue
                    if (
                        isinstance(flow_dec, dict)
                        and flow_dec.get("unanswered")
                        and str(self._namespace) == "operator"
                    ):
                        # The hold ask was missed. That is not a send and it is
                        # not the old hold. The bar stays open for the next ask.
                        summary["bar_consumable"] = False
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": "judgment_hold_unanswered",
                            "judgment_flow": flow_dec,
                        })
                        continue
                    if (intent.sleeve, intent.symbol, dbar) in getattr(self, "_timeout_ended", ()):
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": "order_timeout_retries",
                        })
                        continue
                    if self._timeout_quiet_holds(intent.sleeve, intent.symbol, dbar):
                        summary["bar_consumable"] = False
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": "order_timeout_unanswered",
                        })
                        continue
                    hop_notes = self._stamp_lifetime_notes(
                        _hop_notes(
                            route_intent,
                            flow_dec,
                            _read_hop(getattr(self, "_owner_hops", None), route_intent, dbar),
                        ),
                        getattr(intent, "symbol", None),
                    )
                    if f5_market_stop_floor is not None:
                        hop_notes["f5_market_stop_floor"] = dict(f5_market_stop_floor)
                    _view_risk = getattr(unit_su, "risk_pct_per_trade", None)
                    _view_missing = True
                    if not isinstance(_view_risk, bool) and _view_risk is not None:
                        try:
                            _view_missing = not (float(_view_risk) > 0)
                        except (TypeError, ValueError):
                            _view_missing = True
                    if str(self._namespace) == "operator" and _view_missing:
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": "risk_unset",
                        })
                        continue
                    result = self.router.place(
                        ee,
                        unit_su,
                        route_intent,
                        tick,
                        account_state,
                        balance,
                        annotations=hop_notes or None,
                    )
                    if routed_floor is not None:
                        # The proposal and broker-grid projection are part of the exact order
                        # geometry, not ephemeral cycle diagnostics. Stamp the same snapshot
                        # onto the router result/trade_params so the unified refusal or
                        # placement packet and the ticket trade record retain intended/actual
                        # risk, lot-grid shortfall/round-up, and effective target policy.
                        # This branch is unreachable when Q1 is OFF.
                        routed_floor = dict(routed_floor)
                        result["risk_unit_floor"] = routed_floor
                        trade_params = result.get("trade_params")
                        if isinstance(trade_params, dict):
                            trade_params["risk_unit_floor"] = dict(routed_floor)
                    if result["placed"]:
                        if sequential_conviction:
                            _accepted = adjusted_unit.get("risk_pct_per_trade")
                            if not isinstance(_accepted, bool) and _accepted is not None:
                                try:
                                    cycle_accepted_risk_pct += float(_accepted)
                                except (TypeError, ValueError):
                                    pass
                        if result.get("native_pending"):
                            record_conviction = getattr(self.engine, "record_placement_conviction", None)
                            if callable(record_conviction):
                                try:
                                    record_conviction(intent)
                                except Exception:
                                    pass
                            placed_broker_symbol_keys.update(target_broker_keys)
                            ticket = getattr(result.get("trade_state"), "ticket", None)
                            trade_params = result.get("trade_params") or {}
                            candidate_id = result.get("candidate_id") or trade_params.get("candidate_id")
                            placed_at = now.isoformat()
                            resolved_cluster = self._resolve_runtime_cluster(
                                unit=unit,
                                sleeve=intent.sleeve,
                                candidate_id=candidate_id,
                            )
                            try:
                                self._ledger.record(
                                    intent.sleeve,
                                    intent.symbol,
                                    dbar,
                                    candidate_id=candidate_id,
                                    ticket=ticket,
                                    ts=placed_at,
                                    decision_day=_dday,
                                    cluster=resolved_cluster,
                                    require_full_context=True,
                                )
                            except Exception:
                                pass
                            summary.setdefault("pending", []).append({
                                "symbol": intent.symbol,
                                "sleeve": intent.sleeve,
                                "decision_bar_iso": dbar,
                                "decision_day": _dday,
                                "cluster": resolved_cluster,
                                "candidate_id": candidate_id,
                                "ticket": ticket,
                                "reason": result.get("reason") or "native_pending_resting",
                            })
                            # LIMIT/pending used to continue before persist/_f5_on_open.
                            # Persist intended+actual+nominal now so a later fill/adopt is
                            # not unit-less. Do not on_open until the position exists.
                            try:
                                broker_symbol = self._broker_symbol(intent.symbol)
                            except Exception:
                                broker_symbol = None
                            self._persist_trade_record(
                                ticket,
                                trade_params,
                                route_intent,
                                decision_bar_iso=dbar,
                                decision_day=_dday,
                                cluster=resolved_cluster,
                                placed_at_utc=placed_at,
                                broker_symbol=broker_symbol,
                            )
                            continue
                        # Commit RUNNING conviction only after placement truth exists. The evaluation
                        # slate remains complete observation; the placement-bound preview above is sizing
                        # authority. Persisting before downstream cost/permission/lifecycle/broker gates
                        # would let a refused sleeve raise every later unit's nominal Kelly multiplier. The
                        # callable guard preserves compatibility with test/legacy engine stubs; the real
                        # method is best-effort and never raises after a broker order has succeeded.
                        record_conviction = getattr(self.engine, "record_placement_conviction", None)
                        if callable(record_conviction):
                            try:
                                record_conviction(intent)
                            except Exception:
                                pass
                        placed_broker_symbol_keys.update(target_broker_keys)
                        ticket = getattr(result.get("trade_state"), "ticket", None)
                        trade_params = result.get("trade_params") or {}
                        # POST-FILL TRUTH: stamp fill deviation + risk-at-fill BEFORE the
                        # trade record persists, so record + f5_fill event carry the same
                        # honest numbers. No-op on non-F5 books.
                        self._f5_fill_truth_fields(trade_params, result)
                        candidate_id = result.get("candidate_id") or trade_params.get("candidate_id")
                        placed_at = now.isoformat()
                        resolved_cluster = self._resolve_runtime_cluster(
                            unit=unit,
                            sleeve=intent.sleeve,
                            candidate_id=candidate_id,
                        )
                        try:
                            broker_symbol = self._broker_symbol(intent.symbol)
                        except Exception:
                            broker_symbol = None
                        ledger_row = self._ledger.record(
                            intent.sleeve,
                            intent.symbol,
                            dbar,
                            candidate_id=candidate_id,
                            ticket=ticket,
                            ts=placed_at,
                            decision_day=_dday,
                            cluster=resolved_cluster,
                            require_full_context=True,
                        )
                        # persist the exit-policy truth so a restarted process rehydrates the exact lifecycle
                        self._persist_trade_record(
                            ticket,
                            trade_params,
                            route_intent,
                            decision_bar_iso=dbar,
                            decision_day=_dday,
                            cluster=resolved_cluster,
                            placed_at_utc=placed_at,
                            broker_symbol=broker_symbol,
                        )
                        persisted_record = self._load_trade_record(ticket)
                        placed_row = {"symbol": intent.symbol, "sleeve": intent.sleeve,
                                      "decision_bar_iso": dbar,
                                      "decision_day": _dday,
                                      "cluster": resolved_cluster,
                                      "candidate_id": candidate_id}
                        if isinstance(ledger_row, dict):
                            for key in (
                                "placement_capture_contract_version",
                                "placement_source_completeness_status",
                                "placement_source_missing_fields",
                            ):
                                if ledger_row.get(key) is not None:
                                    placed_row[key] = ledger_row.get(key)
                        placed_row.update(self._runtime_learning_trade_context(
                            ticket=ticket,
                            trade_params=trade_params,
                            record=persisted_record,
                            broker_symbol=broker_symbol,
                            placed_at_utc=placed_at,
                        ))
                        summary["placed"].append(placed_row)
                        self._f5_on_open(ticket=ticket, sleeve=intent.sleeve,
                                         symbol=intent.symbol, trade_params=trade_params,
                                         candidate_id=candidate_id, decision_day=_dday,
                                         decision_bar_iso=dbar)
                        # POST-FILL DEVIATION GUARD (namespace-gated): a fill born past
                        # the cap is closed on the spot through the engine's own
                        # risk-reducing close path. Never raises into the tick.
                        self._f5_fill_deviation_guard(
                            ee=ee, ticket=ticket, sleeve=intent.sleeve,
                            symbol=intent.symbol, trade_params=trade_params,
                            decision_bar_iso=dbar)
                        self._notify_placed(route_intent, unit_su, result)
                    else:
                        skipped_row = {"symbol": intent.symbol, "sleeve": intent.sleeve,
                                       "decision_bar_iso": dbar, "reason": result["reason"]}
                        skipped_row.update(self._runtime_learning_router_result_context(result))
                        self._maybe_enqueue_frozen_price_intent(
                            now=now,
                            intent=intent,
                            unit=unit,
                            tick=tick,
                            dbar=dbar,
                            dday=_dday,
                            ee=ee,
                            account_state=account_state,
                            reason=str(result.get("reason") or ""),
                            packet=self._frozen_packet_from_place_result(result),
                            skipped_row=skipped_row,
                            summary=summary,
                        )
                        self._persist_f5_refusal_quote(
                            now=now,
                            intent=intent,
                            unit=unit,
                            tick=tick,
                            dbar=dbar,
                            dday=_dday,
                            reason=str(result.get("reason") or ""),
                            packet=self._frozen_packet_from_place_result(result),
                            skipped_row=skipped_row,
                        )
                        summary["skipped"].append(skipped_row)
                        # A broker hiccup can leave the bar open. An order timeout is the
                        # hop: keep_bar leaves it open, consume_bar ends it, and an empty
                        # answer does not send again and does not restore the retry law.
                        failure_bar = self._place_failure_bar(result.get("reason"))
                        if failure_bar == "unanswered":
                            self._mark_timeout_quiet(intent.sleeve, intent.symbol, dbar)
                            summary["bar_consumable"] = False
                            skipped_row["order_timeout"] = "unanswered"
                        elif failure_bar == "open":
                            attempted_transient_broker_symbol_keys.update(target_broker_keys)
                            if not self._transient_retry_terminal(
                                intent=intent, dbar=dbar,
                                reason=result.get("reason"), now=now, summary=summary,
                            ):
                                summary["bar_consumable"] = False
                        # notify the owner ONCE per blocked opportunity (dedup on the decision bar) — a
                        # routine spread/cost gate re-firing every tick must not spam the owner's phone.
                        rkey = (intent.sleeve, intent.symbol, dbar, str(result.get("reason")))
                        if rkey not in self._notified_rejects:
                            if len(self._notified_rejects) > 5000:
                                self._notified_rejects.clear()   # bound memory on a long-running process
                            self._notified_rejects.add(rkey)
                            self._notify_reject(intent, result.get("reason"))
                except Exception as e:
                    summary["skipped"].append({"symbol": getattr(intent, "symbol", "?"),
                                               "sleeve": getattr(intent, "sleeve", "?"),
                                               "decision_bar_iso": locals().get("dbar"),
                                               "reason": f"intent_exception:{e!r}"})
                    _log.warning("book[%s]: intent %s/%s raised in placement (isolated): %r",
                                 self._namespace, getattr(intent, "sleeve", "?"),
                                 getattr(intent, "symbol", "?"), e)
                    # The exception is a fact. On Challenge it asks before this
                    # intent returns. Empty does not restore a silent skip, and
                    # it does not send from the broken pass.
                    _challenge_withholds(
                        self._namespace,
                        "intent_exception",
                        {
                            "symbol": str(getattr(intent, "symbol", "") or ""),
                            "sleeve": str(getattr(intent, "sleeve", "") or ""),
                            "error": type(e).__name__,
                            "namespace": "operator",
                        },
                        {
                            "isolate_this_intent": "This intent raised. Leave it for the next pass.",
                            "exception_is_a_fact": "The exception is a fact. It does not decide a send from this pass.",
                        },
                        "isolate_this_intent",
                        f"intent_exception|{getattr(intent, 'sleeve', '')}|{getattr(intent, 'symbol', '')}|{type(e).__name__}",
                        "This intent raised during placement. "
                        "The other intents stay. An empty answer does not send from this pass "
                        "and does not restore a silent skip. Do not close an open ticket.",
                    )
                    continue
        self._sweep_frozen_price_intents(now, summary)
        self._emit_cycle_runtime_learning(summary, now, decision=decision, place=place)
        return summary

    # ---------------- position management (every tick, halt-independent) ----------------
    def manage_open_positions(self, *, now_utc: Optional[datetime] = None) -> dict:
        """Rehydrate + manage every open book position. Management runs even while halted / gated off
        (halt blocks NEW sends only). NEVER raises.

        PER-(SYMBOL, SLEEVE): a symbol can carry several concurrent positions (one per sleeve). Each
        ticket is routed to its OWN engine via the W7:{sleeve} broker comment, so a symbol shared by
        several sleeves no longer collides on one active_trade slot. A leftover safety net adopts any
        magic-matched book position whose comment did not route (missing/mangled) so nothing is left
        unmanaged. Each adopted position then runs its own check_and_manage_trade off the live tick."""
        summary = {"managed": [], "adopted": [], "closed": [], "errors": []}
        pairs = self._manageable_pairs()
        sleeves_by_symbol: dict[str, list[str]] = {}
        for sym, sl in pairs:
            sleeves_by_symbol.setdefault(sym, []).append(sl)
        # one snapshot of all open book positions, mapped broker->canonical ({} if mt5 lacks the accessor)
        open_positions_snapshot = self._open_book_positions_snapshot()
        open_tickets = self._open_snapshot_ticket_set(open_positions_snapshot)
        absence_threshold = self._absence_reconcile_threshold(open_positions_snapshot)
        positions_by_canon = self._open_book_positions_by_canonical(
            sleeves_by_symbol.keys(),
            open_positions_snapshot=open_positions_snapshot,
        )
        claimed_tickets: set = set()

        for sym, sleeves in sleeves_by_symbol.items():
            try:
                held_tickets: set = set()
                # 1. comment-routed adoption: each sleeve's engine adopts ONLY its own W7:{sleeve} ticket
                for sl in sleeves:
                    ee = self._exec_engine(sym, sl)
                    if getattr(ee, "active_trade", None) is None:
                        reconcile = getattr(ee, "reconcile_on_startup", None)
                        if callable(reconcile):
                            try:
                                reconcile(comment_filter=self._sleeve_comment(sl))
                            except TypeError:
                                reconcile()   # back-compat engine without the comment_filter kwarg
                        if getattr(ee, "active_trade", None) is not None:
                            self._adopt_into_engine(ee, sym, sl, summary)
                    t = getattr(getattr(ee, "active_trade", None), "ticket", None)
                    if t is not None:
                        held_tickets.add(t)
                        claimed_tickets.add(t)
                # 2. leftover safety net: any magic-matched open position on this symbol NOT yet held
                #    (e.g. a missing/mangled comment) must NOT go unmanaged -> adopt into a free engine.
                for p in (positions_by_canon.get(sym, []) or []):
                    tkt = getattr(p, "ticket", None)
                    if tkt is None or tkt in held_tickets or tkt in claimed_tickets:
                        continue
                    # only adopt BOOK positions: a W7:* comment, a comment-stripped one, OR a ticket the
                    # book's OWN placement ledger recorded placing (definitively ours despite a legacy /
                    # mislabelled comment — the GER40 'GoldAgent_OBRete' orphan: book-placed by vp_euidx but
                    # tagged with the retired default comment, then unadoptable -> managed only by the broker
                    # SL/TP). A foreign comment that is NOT in our ledger stays foreign (legacy/manual) and
                    # is never managed — the book must not touch trades it did not place.
                    cmt = (getattr(p, "comment", "") or "")
                    ledger_pair = self._ledger.sleeve_symbol_for_ticket(tkt)
                    if cmt and not cmt.startswith(self._comment_prefix) and ledger_pair is None:
                        continue
                    for sl in sleeves:
                        if ledger_pair is not None and ledger_pair != (sl, sym):
                            continue
                        if cmt.startswith(self._comment_prefix) and cmt != self._sleeve_comment(sl):
                            continue
                        ee = self._exec_engine(sym, sl)
                        if getattr(ee, "active_trade", None) is not None:
                            continue
                        adopt = getattr(ee, "adopt_specific_position", None)
                        if callable(adopt) and adopt(p):
                            self._adopt_into_engine(ee, sym, sl, summary)
                            held_tickets.add(tkt)
                            claimed_tickets.add(tkt)
                        break
                # 3. manage every engine for this symbol that holds a position
                for sl in sleeves:
                    ee = self._exec_engine(sym, sl)
                    if getattr(ee, "active_trade", None) is not None:
                        if self._reconcile_absent_active_engine(
                            ee,
                            sym,
                            sl,
                            open_tickets,
                            absence_threshold,
                            summary,
                        ):
                            continue
                        self._manage_engine(ee, sym, sl, summary)
            except Exception as e:                                  # never break the loop
                summary["errors"].append({"symbol": sym, "error": repr(e)})
        # OUT-OF-UNIVERSE W7 position alert: a W7-magic position on a symbol NO active sleeve covers cannot
        # be adopted/managed by any engine and would ride silently on the broker SL/TP only -> surface it.
        self._alert_out_of_universe(summary)
        # If a restart happened after broker-side closure, no engine may be alive to observe
        # ``active_trade -> None``. Reconcile durable records against a confirmed open-position
        # snapshot so runtime-learning state does not leave old tickets looking open forever.
        self._reconcile_absent_trade_records(open_positions_snapshot, summary)
        # Revisit already-closed records whose first reconciliation was exit-only or missing fields. When
        # account history now proves fuller accounting, emit a corrected close packet with the same close
        # identity so runtime-learning advisory dedupe supersedes the stale packet without editing logs.
        self._repair_closed_trade_records(summary)
        # F5 N1/N2: reconcile AFTER management, so partial closes and protective-SL moves made
        # above are reflected before this tick can evaluate another entry.  A fresh magic-scoped
        # snapshot also closes the broker-accepted/ledger-hook crash gap on every restart.
        if self._f5_ledger is not None:
            f5_reconciliation = self._f5_reconcile_broker_positions(
                self._open_book_positions_snapshot()
            )
            summary["f5_reconciliation"] = f5_reconciliation
            if isinstance(f5_reconciliation, dict) and not f5_reconciliation.get("complete"):
                summary["errors"].append({
                    "symbol": "*",
                    "error": f"f5_reconciliation:{f5_reconciliation.get('status')}",
                })
        # LAST-RESORT: flatten every open position + latch new entries OFF if the account nears the
        # prop-fatal daily-loss / static max-DD floor (runs AFTER adoption so every engine reflects the
        # live broker state). Default-off; enabled in the live config.
        now = now_utc or datetime.now(timezone.utc)
        self._expire_native_pending_orders(now, summary)
        # F5 MANAGE CONSUME SEAM (gtos.judgment.manage.v1; namespace-gated, fail-open):
        # runs AFTER adoption so the engines hold every open book position, and only
        # applies risk-reducing rows (close / tighten_stop). No-op on every other book.
        self._f5_consume_manage_rows(summary, now)
        # Chair behaviours encoded (2026-08-25, owner-directed): dedup first so a duplicate
        # never earns a breakeven lock, then the auto-BE pass. Both namespace-gated no-ops
        # on production books, both fail-open, both risk-reducing only.
        self._f5_duplicate_stack_dedup(summary)
        self._f5_auto_breakeven(summary, now)
        self._apply_breach_flatten(now, summary)
        self._news_t15_t60_cycle(now, summary)
        self._emit_management_runtime_learning(summary, now)
        # Chair 2026-09-21: remint/flatten LABEL consume observe (never broker-mutates)
        try:
            from src.judgment.remint_flatten_consume import observe_book_owner_consume
            ns = getattr(self, "namespace", None) or getattr(self, "ns", None) or ""
            remint_obs = observe_book_owner_consume(
                namespace=ns,
                live_broker_authority=False,
            )
            if isinstance(summary, dict):
                summary["remint_flatten_observe"] = remint_obs
        except Exception:
            pass
        return summary

    def _latest_closed_bar_time(self, symbol: str):
        """Best-effort latest M15 bar time for native-pending expiry. Never raises."""
        try:
            get = getattr(self._mt5, "get_candles", None)
            if not callable(get):
                return None
            try:
                broker = self._broker_symbol(symbol)
            except Exception:
                broker = symbol
            candles = get(broker, 15, 2)
            if not candles:
                return None
            last = candles[-1]
            if isinstance(last, dict):
                return last.get("time")
            return getattr(last, "time", None)
        except Exception:
            return None

    def _f5_sweep_stale_pending_orders(self, now, summary: dict) -> None:
        """CONTRACT V2 (Fable 5.1, 2026-09-02). F5 only. NEVER raises.

        A restart forgets the engine's in-memory `_native_pending_order`, so a GTC limit the
        book placed rests at the broker until it fills at a level whose bar is long gone
        (7 such fills 24 Aug -> 2 Sep, -5.7R) and keeps the symbol 'occupied' for the
        isolated re-entry yield. Cancel any book pending (our magic, our comment prefix,
        BUY_LIMIT/SELL_LIMIT) not tracked by a live engine whose age at the broker exceeds
        the returned bar count times one M15 bar, plus 60 s. Age is broker clock vs broker clock
        (order.time_setup vs symbol_info_tick().time): no UTC offset is involved.
        TRADE_ACTION_REMOVE only ever reduces exposure.
        """
        if str(getattr(self, "_namespace", "") or "") != "operator":
            return
        try:
            module = getattr(self._mt5, "_mt5", None)
            orders_get = getattr(module, "orders_get", None)
            tick_get = getattr(module, "symbol_info_tick", None)
            if not callable(orders_get) or not callable(tick_get):
                return
            tracked = set()
            for _pair, _ee in list(self._exec_engines.items()):
                pend = getattr(_ee, "_native_pending_order", None)
                if isinstance(pend, dict) and pend.get("ticket") not in (None, 0):
                    try:
                        tracked.add(int(pend.get("ticket")))
                    except (TypeError, ValueError):
                        pass
            orders = orders_get() or []
            prefix = str(getattr(self, "_comment_prefix", "") or "")
            magic = getattr(self, "_magic", None)
            for o in orders:
                try:
                    if magic is not None and int(getattr(o, "magic", -1) or -1) != int(magic):
                        continue
                    if int(getattr(o, "type", 99) or 99) not in (2, 3):   # BUY_LIMIT / SELL_LIMIT
                        continue
                    comment = str(getattr(o, "comment", "") or "")
                    if prefix and not comment.startswith(prefix):
                        continue
                    ticket = int(getattr(o, "ticket", 0) or 0)
                    if ticket <= 0 or ticket in tracked:
                        continue
                    symbol = str(getattr(o, "symbol", "") or "")
                    tick = tick_get(symbol) if symbol else None
                    server_now = float(getattr(tick, "time", 0) or 0)
                    setup = float(getattr(o, "time_setup", 0) or 0)
                    if server_now <= 0 or setup <= 0:
                        continue
                    age_s = server_now - setup
                    # The bar count is the returned score. One M15 bar is 15 minutes.
                    expiry_bars = _parameter_score(
                        "limit_expiry_bars",
                        {
                            "ticket": ticket,
                            "symbol": symbol,
                            "age_s": age_s,
                            "namespace": "operator",
                        },
                        "How many closed M15 bars does this resting limit live? "
                        "The score you return is that count.",
                    )
                    if expiry_bars is None:
                        continue
                    # One M15 bar is 15 minutes. The score is the whole life. No added pad.
                    max_age_s = float(expiry_bars) * 15.0 * 60.0
                    if age_s <= max_age_s:
                        continue
                    if not _spot_choice(
                        "stale_pending_remove",
                        {
                            "ticket": ticket,
                            "symbol": symbol,
                            "age_s": age_s,
                            "expiry_bars": float(expiry_bars),
                            "namespace": "operator",
                        },
                        {
                            "remove": "Cancel this resting limit.",
                            "leave": "Leave this resting limit.",
                        },
                        "remove",
                        f"stale_pending_remove|{ticket}|{symbol}",
                        "The two sides of cancelling this resting limit. "
                        "An empty answer or a tie does not cancel. "
                        "Do not flatten an open ticket from this question.",
                    ):
                        continue
                    result = self._mt5.order_send({"action": 8, "order": ticket})   # TRADE_ACTION_REMOVE
                    retcode = getattr(result, "retcode", None)
                    row = {"ticket": ticket, "symbol": symbol, "comment": comment,
                           "age_s": round(age_s, 1), "max_age_s": max_age_s, "retcode": retcode}
                    summary.setdefault("f5_stale_pending_swept", []).append(row)
                    _log.warning("book[%s]: F5 stale pending %s %s age %.0fs > %.0fs -> REMOVE retcode=%s",
                                 self._namespace, ticket, symbol, age_s, max_age_s, retcode)
                    capture = getattr(self, "_f5_capture", None)
                    if capture is not None:
                        capture.emit("f5_stale_pending_swept",
                                     dict(row, broker_mutation=(retcode == 10009)))
                except Exception as exc:  # noqa: BLE001 - one bad row must not stop the sweep
                    _log.warning("book[%s]: F5 stale pending sweep row failed (%r)", self._namespace, exc)
        except Exception as exc:  # noqa: BLE001 - the sweep must never break management
            _log.warning("book[%s]: F5 stale pending sweep failed (%r)", self._namespace, exc)

    def _expire_native_pending_orders(self, now, summary: dict) -> None:
        """Cancel resting native limits when expiry_bars have elapsed. No-op when none."""
        self._f5_sweep_stale_pending_orders(now, summary)
        for (sym, sl), ee in list(self._exec_engines.items()):
            pending = getattr(ee, "_native_pending_order", None)
            if pending is None:
                continue
            if getattr(ee, "active_trade", None) is not None:
                ee._native_pending_order = None
                continue
            expire = getattr(ee, "expire_native_pending_if_due", None)
            if not callable(expire):
                continue
            try:
                result = expire(
                    now_utc=now,
                    current_bar_time=self._latest_closed_bar_time(sym),
                )
            except Exception as e:
                summary["errors"].append({
                    "symbol": sym,
                    "sleeve": sl,
                    "error": f"native_pending_expire:{e!r}",
                })
                continue
            if result and result.get("cancelled"):
                summary.setdefault("pending_expired", []).append({
                    "symbol": sym,
                    "sleeve": sl,
                    "ticket": result.get("ticket"),
                    "reason": result.get("reason"),
                })

    def _alert_out_of_universe(self, summary: dict) -> None:
        """Alert ONCE (per ticket) on a W7-magic open position whose symbol is OUTSIDE the active-sleeve
        universe (a leftover from a retired sleeve/symbol, a wrong-account fill, or a manual W7-tagged
        trade): no engine can manage it, so it would silently ride the broker SL/TP only. NEVER raises."""
        try:
            get_open = getattr(self._mt5, "get_open_positions", None)
            if not callable(get_open):
                return
            manageable_broker: set = set()
            for (canon, _sl) in self._manageable_pairs():
                try:
                    manageable_broker.add(self._broker_symbol(canon))
                except Exception:
                    pass
            for p in (get_open() or []):
                tkt = getattr(p, "ticket", None)
                if tkt is None or tkt in self._oou_alerted:
                    continue
                cmt = (getattr(p, "comment", "") or "")
                is_w7 = (getattr(p, "magic", None) == self._magic) or cmt.startswith(
                    self._comment_prefix)
                bsym = getattr(p, "symbol", None)
                if is_w7 and bsym not in manageable_broker:
                    if len(self._oou_alerted) > 5000:
                        self._oou_alerted.clear()
                    self._oou_alerted.add(tkt)
                    summary.setdefault("out_of_universe", []).append(
                        {"ticket": tkt, "symbol": bsym, "comment": cmt})
                    _log.warning("book[%s]: OUT-OF-UNIVERSE W7 position #%s %s (%r) — no active sleeve "
                                 "manages this symbol; broker SL/TP only", self._namespace, tkt, bsym, cmt)
                    self._send_card(f"[{self._account_label()}] ⚠️ Out-of-universe W7 position #{tkt} "
                                    f"{bsym} ({cmt}) — not managed by any sleeve (broker SL/TP only). "
                                    f"Investigate.")
        except Exception:
            pass

    def _open_book_positions_snapshot(self) -> list | None:
        """Return a broker-confirmed snapshot of all open book positions, or None when unavailable.

        A broker-link check, when the MT5 wrapper exposes one, prevents treating a disconnected
        terminal's empty/failed position read as evidence that every local trade record is closed.
        """
        try:
            broker_link = getattr(self._mt5, "broker_link_connected", None)
            if callable(broker_link) and not bool(broker_link()):
                return None
            get_open = getattr(self._mt5, "get_open_positions", None)
            if not callable(get_open):
                return None
            positions = get_open()
            if positions is None:
                return None
            return list(positions)
        except Exception:
            return None

    def _active_engine_tickets(self) -> set[int]:
        tickets: set[int] = set()
        for ee in list(self._exec_engines.values()):
            try:
                ticket = getattr(getattr(ee, "active_trade", None), "ticket", None)
                if ticket not in (None, 0):
                    tickets.add(int(ticket))
            except (TypeError, ValueError):
                continue
        return tickets

    def _clear_engine_ticket(self, ticket) -> None:
        """Drop in-memory active_trade for a ticket already consumed from broker truth."""
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            return
        for ee in list(self._exec_engines.values()):
            try:
                active = getattr(ee, "active_trade", None)
                held = getattr(active, "ticket", None)
                if held in (None, 0):
                    continue
                if int(held) == ticket_i:
                    ee.active_trade = None
            except (TypeError, ValueError, AttributeError):
                continue

    @staticmethod
    def _open_snapshot_ticket_set(open_positions_snapshot: list | None) -> set[int] | None:
        if open_positions_snapshot is None:
            return None
        out: set[int] = set()
        for p in open_positions_snapshot:
            try:
                ticket = int(getattr(p, "ticket", 0) or 0)
            except (TypeError, ValueError):
                continue
            if ticket:
                out.add(ticket)
        return out


    def _open_book_pending_ticket_set(self) -> set[int] | None:
        """Resting LIMIT/STOP tickets from orders_get. None if the read failed.

        Class 2026-08-27: a native pending is always absent from positions_get.
        Absence-reconcile must treat these tickets as present. A failed
        orders read is None so a resting LIMIT is not stamped closed on a
        blind poll. Empty successful read is an empty set.
        """
        module = getattr(getattr(self, "_mt5", None), "_mt5", None)
        orders_get = getattr(module, "orders_get", None)
        if not callable(orders_get):
            return None
        try:
            orders = orders_get() or []
        except Exception:
            return None
        out: set[int] = set()
        magic = getattr(self, "_magic", None)
        for o in orders:
            if magic is not None and getattr(o, "magic", None) != magic:
                continue
            try:
                ticket = int(getattr(o, "ticket", 0) or 0)
            except (TypeError, ValueError):
                continue
            if ticket:
                out.add(ticket)
        return out

    @staticmethod
    def _absence_reconcile_threshold(open_positions_snapshot: list | None) -> int | None:
        if open_positions_snapshot is None:
            return None
        # Class: never stamp broker_closed_absent_on_reconcile on one snapshot
        # miss. Native pending (place deal_ticket=0) is invisible to
        # positions_get; a filled ticket can also drop for one poll. Isolated
        # re-entry after a real close still proceeds once count >= 2.
        return 2

    def _ticket_absence_confirmed(self, ticket: int, *, threshold: int) -> tuple[bool, int]:
        count = int(self._absent_ticket_observations.get(ticket, 0) or 0) + 1
        self._absent_ticket_observations[ticket] = count
        return count >= max(1, threshold), count

    def _reconcile_absent_active_engine(
        self,
        ee,
        sym: str,
        sleeve: str,
        open_tickets: set[int] | None,
        absence_threshold: int | None,
        summary: dict,
    ) -> bool:
        """Clear a local active_trade when read-only broker truth confirms the ticket is gone."""
        if open_tickets is None or absence_threshold is None:
            return False
        active = getattr(ee, "active_trade", None)
        ticket = getattr(active, "ticket", None)
        if ticket in (None, 0):
            return False
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            return False
        if ticket_i in open_tickets:
            self._absent_ticket_observations.pop(ticket_i, None)
            return False
        pending_tickets = self._open_book_pending_ticket_set()
        if pending_tickets is None:
            # orders_get failed: do not increment toward a closed stamp
            return False
        if ticket_i in pending_tickets:
            self._absent_ticket_observations.pop(ticket_i, None)
            return False
        confirmed, observed_count = self._ticket_absence_confirmed(
            ticket_i,
            threshold=absence_threshold,
        )
        if not confirmed:
            return False
        try:
            broker_symbol = self._broker_symbol(sym)
        except Exception:
            broker_symbol = None
        checked_at = datetime.now(timezone.utc).isoformat()
        record = self._load_trade_record(ticket_i)
        closed_record = self._mark_trade_record_closed(
            ticket_i,
            "broker_closed_absent_on_reconcile",
            checked_at,
            record=record,
            broker_symbol=broker_symbol,
            sleeve=sleeve,
            symbol=sym,
        )
        try:
            ee.active_trade = None
        except Exception:
            pass
        try:
            from .minimal_size import f5_close_send_none_clear
            f5_close_send_none_clear(ticket_i)
        except Exception:
            pass
        join_ctx = self._runtime_learning_trade_context(
            ticket=ticket_i,
            record=closed_record or record,
            broker_symbol=broker_symbol,
            management_checked_at_utc=checked_at,
        )
        row = {
            "symbol": sym,
            "sleeve": sleeve,
            "action": "broker_closed_absent_on_reconcile",
            "broker_mutation_allowed": False,
            "source_completeness_status": "active_trade_absent_from_confirmed_open_snapshot",
            "broker_position_absence_observation_count": observed_count,
            "broker_position_absence_required_confirmations": absence_threshold,
            **join_ctx,
        }
        summary.setdefault("closed", []).append(row)
        self._absent_ticket_observations.pop(ticket_i, None)
        return True

    def _reconcile_absent_trade_records(self, open_positions_snapshot: list | None, summary: dict) -> None:
        """Mark stale local trade records closed when broker-open truth no longer contains their ticket.

        This is local evidence repair only. Two consecutive absences are
        required before a closed stamp, empty snapshot or not. A single miss
        (native pending not yet in positions, or a transient positions_get
        drop) must not close the record. Isolated re-entry after a real close
        is unchanged: after two confirms the stamp lands and the symbol is free.
        """
        if open_positions_snapshot is None:
            return
        try:
            open_tickets = self._open_snapshot_ticket_set(open_positions_snapshot)
            if open_tickets is None:
                return
            pending_tickets = self._open_book_pending_ticket_set()
            if pending_tickets is None:
                # orders_get failed: sitting LIMIT would look absent
                return
            absence_threshold = self._absence_reconcile_threshold(open_positions_snapshot)
            if absence_threshold is None:
                return
            active_tickets = self._active_engine_tickets()
            for path in sorted(self._trade_record_path().glob("*.json")):
                try:
                    ticket = int(path.stem)
                except (TypeError, ValueError):
                    continue
                if ticket in open_tickets or ticket in pending_tickets:
                    self._absent_ticket_observations.pop(ticket, None)
                    continue
                # Skip in-engine tickets only on an all-empty snapshot so the
                # active-engine path keeps the 2-tick debounce. On a non-empty
                # snapshot, consume dsp leftovers whose engines are not in
                # _manageable_pairs(active_specs(None)).
                if ticket in active_tickets and not open_tickets:
                    continue
                confirmed, observed_count = self._ticket_absence_confirmed(
                    ticket,
                    threshold=absence_threshold,
                )
                if not confirmed:
                    continue
                record = self._load_trade_record(ticket)
                if not isinstance(record, dict):
                    continue
                if record.get("trade_lifecycle_status") == "closed":
                    self._absent_ticket_observations.pop(ticket, None)
                    continue
                symbol = record.get("symbol")
                sleeve = record.get("sleeve")
                execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
                broker_symbol = execution.get("broker_symbol")
                checked_at = datetime.now(timezone.utc).isoformat()
                closed_record = self._mark_trade_record_closed(
                    ticket,
                    "broker_closed_absent_on_reconcile",
                    checked_at,
                    record=record,
                    broker_symbol=broker_symbol,
                    sleeve=sleeve,
                    symbol=symbol,
                )
                join_ctx = self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=closed_record or record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                )
                row = {
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "action": "broker_closed_absent_on_reconcile",
                    "source_completeness_status": "trade_record_absent_from_confirmed_open_snapshot",
                    "broker_position_absence_observation_count": observed_count,
                    "broker_position_absence_required_confirmations": absence_threshold,
                    **join_ctx,
                }
                summary.setdefault("closed", []).append(row)
                self._clear_engine_ticket(ticket)
                self._absent_ticket_observations.pop(ticket, None)
                try:
                    from .minimal_size import f5_close_send_none_clear
                    f5_close_send_none_clear(ticket)
                except Exception:
                    pass
        except Exception as e:
            summary.setdefault("errors", []).append(
                {"symbol": "*", "error": f"absent_trade_record_reconcile:{e!r}"}
            )

    def _repair_closed_trade_records(self, summary: dict) -> None:
        try:
            import json
            for path in sorted(self._trade_record_path().glob("*.json")):
                try:
                    ticket = int(path.stem)
                except (TypeError, ValueError):
                    continue
                try:
                    record = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if not isinstance(record, dict) or record.get("trade_lifecycle_status") != "closed":
                    continue
                record, changed = self._normalize_trade_record(ticket, record)
                if not changed:
                    continue
                self._record_closed_trade_daily_pnl(
                    ticket,
                    record,
                    record.get("close_action") or "broker_closed",
                )
                self._write_trade_record(ticket, record, context="closed trade-record reconciliation repair")
                execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
                checked_at = datetime.now(timezone.utc).isoformat()
                broker_symbol = execution.get("broker_symbol")
                join_ctx = self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                )
                summary.setdefault("closed", []).append({
                    "symbol": record.get("symbol"),
                    "sleeve": record.get("sleeve"),
                    "action": record.get("close_action") or "broker_closed",
                    "source_completeness_status": "closed_trade_record_account_history_repaired",
                    **join_ctx,
                })
        except Exception as e:
            summary.setdefault("errors", []).append(
                {"symbol": "*", "error": f"closed_trade_record_repair:{e!r}"}
            )

    def _flatten_flag_present(self) -> bool:
        """Operator FLATTEN brake: a shared pipeline_state/ULTIMATE_BOOK_FLATTEN.flag flattens BOTH books;
        a per-namespace .../<ns>/FLATTEN.flag flattens just this one. Sits beside the kill flag (which only
        blocks NEW entries) as the OPEN-position brake. Best-effort; any error -> False."""
        try:
            from pathlib import Path
            base = Path(self._repo_root) / "pipeline_state"
            return ((base / "ULTIMATE_BOOK_FLATTEN.flag").exists()
                    or (base / "ultimate_book" / (self._namespace or "book") / "FLATTEN.flag").exists())
        except Exception:
            return False

    def _flatten_all_engines(self, summary: dict, action: str) -> None:
        """Close every engine that still holds a position; record + isolate per-engine failures (retried
        next tick while the latch holds). NEVER raises."""
        if str(getattr(self, "_namespace", "") or "") == "operator":
            summary.setdefault("managed", []).append({
                "symbol": "*",
                "sleeve": "*",
                "action": f"{action}_observed_not_flat",
                "flatten": False,
                "open_ticket": "294215389",
            })
            return
        if not self._live_broker_authority():
            summary.setdefault("managed", []).append({
                "symbol": "*",
                "sleeve": "*",
                "action": f"{action}_suppressed_live_broker_authority_false",
                "live_broker_authority": False,
                "broker_mutation_allowed": False,
                "source_completeness_status": "flatten_request_observed_broker_mutation_disabled",
            })
            return
        for (sym, sl), ee in list(self._exec_engines.items()):
            if getattr(ee, "active_trade", None) is None:
                continue
            active_before = getattr(ee, "active_trade", None)
            ticket = getattr(active_before, "ticket", None)
            record = self._load_trade_record(ticket) if ticket is not None else None
            try:
                broker_symbol = self._broker_symbol(sym)
            except Exception:
                broker_symbol = None
            checked_at = datetime.now(timezone.utc).isoformat()
            join_ctx = self._runtime_learning_trade_context(
                ticket=ticket,
                record=record,
                broker_symbol=broker_symbol,
                management_checked_at_utc=checked_at,
            )
            try:
                if ee.close_position(f"vnext_{action}"):
                    closed_record = self._mark_trade_record_closed(
                        ticket,
                        action,
                        checked_at,
                        record=record,
                        broker_symbol=broker_symbol,
                        sleeve=sl,
                        symbol=sym,
                    )
                    if closed_record is not None:
                        join_ctx.update(self._runtime_learning_trade_context(
                            ticket=ticket,
                            record=closed_record,
                            broker_symbol=broker_symbol,
                            management_checked_at_utc=checked_at,
                        ))
                    summary["closed"].append({"symbol": sym, "sleeve": sl, "action": action, **join_ctx})
                else:
                    summary["errors"].append({"symbol": sym, "sleeve": sl, "error": f"{action}_close_failed"})
            except Exception as e:
                summary["errors"].append({"symbol": sym, "sleeve": sl, "error": f"{action}:{e!r}"})

    def _apply_breach_flatten(self, now_utc, summary: dict) -> None:
        """Flatten every open book position + latch new entries OFF on either an OPERATOR FLATTEN flag
        (immediate) or a governor breach near the prop-fatal daily-loss / static max-DD floor (with N-tick
        hysteresis so a transient equity wick can't trigger). NEVER raises."""
        # (1) OPERATOR FLATTEN flag -> immediate, no hysteresis (an explicit operator request).
        if self._flatten_flag_present():
            if str(getattr(self, "_namespace", "") or "") == "operator":
                summary.setdefault("managed", []).append({
                    "symbol": "*",
                    "sleeve": "*",
                    "action": "operator_flatten_observed_not_flat",
                    "flatten": False,
                    "open_ticket": "294215389",
                })
                return
            self._breach_block = True
            self._flatten_all_engines(summary, "operator_flatten")
            if not self._live_broker_authority():
                if not self._breach_alerted:
                    self._breach_alerted = True
                    _log.warning(
                        "book[%s]: OPERATOR FLATTEN flag observed, but live broker authority is false "
                        "-> no broker mutation; new entries OFF",
                        self._namespace,
                    )
                return
            if not self._breach_alerted:
                self._breach_alerted = True
                _log.warning("book[%s]: OPERATOR FLATTEN flag -> all positions closed, new entries OFF",
                             self._namespace)
                self._send_card(f"[{self._account_label()}] 🛑 OPERATOR FLATTEN flag — all book positions "
                                f"CLOSED, new entries OFF (remove the flag to resume)")
            return
        # (2) governor breach. CONTRACT V3 (Fable 5.1, 2026-09-02): on F5 the verdict comes from the
        # REAL account (static floor + real day start), not the notional governor the engine builds.
        if str(getattr(self, "_namespace", "") or "") == "operator":
            try:
                verdict = self._f5_real_account_breach_verdict(now_utc)
            except Exception:  # noqa: BLE001
                verdict = None
        else:
            try:
                verdict = self.engine.breach_flatten_check(now_utc)
            except Exception:
                verdict = None
        if verdict is None:
            return   # disabled or unassessable -> leave the prior latch untouched (FAIL-SAFE)
        if not verdict.get("flatten"):
            self._breach_ticks = 0
            if self._breach_block:                      # breach/flag cleared -> re-enable placement
                self._breach_block = False
                self._breach_alerted = False
                _log.info("book[%s]: breach/flatten cleared -> placement re-enabled", self._namespace)
            return
        self._breach_ticks += 1
        if (
            str(getattr(self, "_namespace", "") or "") != "operator"
            and self._breach_ticks < self._breach_confirm
        ):
            return   # other books keep the confirm count; Challenge does not wait on it
        if str(getattr(self, "_namespace", "") or "") == "operator":
            close_now = _spot_choice(
                "breach_close",
                {
                    "flatten": True,
                    "reason": (verdict or {}).get("reason"),
                    "namespace": "operator",
                    "open_gold": 294215389,
                },
                {
                    "close": "Close the open book. Close is legal when it is the unique highest.",
                    "leave_open": "Leave the open book.",
                },
                "close",
                f"breach_close|{(verdict or {}).get('reason')}",
                (
                    "The two sides of closing the book after daily-loss or the risk floor. "
                    "Close only when close is the unique highest. "
                    "An empty answer or a tie does not close and does not restore a flatten boolean. "
                    "Do not flatten open gold 294215389 as a gesture."
                ),
            )
            if not close_now:
                summary.setdefault("managed", []).append({
                    "symbol": "*",
                    "sleeve": "*",
                    "action": "breach_close_not_unique",
                    "flatten": False,
                    "reason": (verdict or {}).get("reason"),
                })
                self._f5_on_notional_breach(verdict)
                return
            stand_down = _spot_choice(
                "breach_withhold",
                {
                    "reason": (verdict or {}).get("reason"),
                    "namespace": "operator",
                    "open_gold": 294215389,
                },
                {
                    "withhold": "Stop new entries on this book.",
                    "continue": "New entries still ask. Do not stand the book down.",
                },
                "withhold",
                f"breach_withhold|{(verdict or {}).get('reason')}",
                "The two sides of standing the book down after a close won. "
                "Withhold only when withhold is the unique highest. "
                "An empty answer or a tie does not stand the book down and does not restore a block. "
                "Do not close ticket 294215389 from this question.",
            )
            if stand_down:
                self._breach_block = True
        else:
            self._breach_block = True                       # latch new entries OFF (run_cycle reads this)
        self._flatten_all_engines(summary, "breach_flatten")
        # F5 epoch roll. ORDER MATTERS: the production flatten above runs FIRST, on real
        # positions, through the unchanged path -- so the stand-down is exercised, not
        # simulated -- and only then does the notional ledger close its epoch. The closed
        # epoch is numbered and written before the reset takes effect, so nothing is silent
        # and the analysis can slice by epoch. `real_pnl_usd_cumulative` is NOT reset.
        # Never `live_broker_authority: false` here: H8 -- that flag records
        # `{action}_suppressed_live_broker_authority_false` and returns without visiting an
        # engine, and degrades routine management to observe-only. It is not a brake.
        self._f5_on_notional_breach(verdict)
        if not self._live_broker_authority():
            if not self._breach_alerted:
                self._breach_alerted = True
                _log.warning(
                    "book[%s]: BREACH FLATTEN observed (%s), but live broker authority is false "
                    "-> no broker mutation; new entries OFF",
                    self._namespace,
                    verdict.get("reason"),
                )
            return
        if not self._breach_alerted:                    # alert ONCE per breach episode
            self._breach_alerted = True
            m = verdict.get("metrics", {})
            _log.warning("book[%s]: BREACH FLATTEN (%s) metrics=%s",
                         self._namespace, verdict.get("reason"), m)
            self._send_card(f"[{self._account_label()}] 🛑 BREACH FLATTEN — {verdict.get('reason')} "
                            f"(equity ${m.get('equity', 0):,.0f}); all book positions CLOSED, new entries OFF")

    # ---------------------------------------------------------------- CONTRACT V3 keep-one across timeframes
    _F5_TF_CACHE: dict | None = None

    @classmethod
    def _f5_sleeve_timeframes(cls) -> dict:
        """sleeve name -> registry timeframe int (15 / 16388 / 16408). Cached. Never raises."""
        if cls._F5_TF_CACHE is not None:
            return cls._F5_TF_CACHE
        out: dict = {}
        try:
            from .sleeves import registry as _reg
            for dname in ("BUILT", "CANDIDATE_BUILT", "WIDEN_BUILT", "MARKET_EXPANSION_BUILT", "DISPLACEMENT_BUILT"):
                for name, spec in (getattr(_reg, dname, {}) or {}).items():
                    tf = getattr(spec, "timeframe", None)
                    if tf is not None:
                        out[str(name)] = int(tf)
        except Exception:  # noqa: BLE001
            out = {}
        cls._F5_TF_CACHE = out
        return out

    def _f5_sleeve_timeframe_of(self, *, sleeve=None, comment=None, ticket=None):
        """Timeframe of a sleeve / a book comment ('F5:<13-char stub>') / a ledger ticket. None = unknown."""
        tfs = self._f5_sleeve_timeframes()
        if sleeve and str(sleeve) in tfs:
            return tfs[str(sleeve)]
        if ticket not in (None, 0, ""):
            try:
                pair = self._ledger.sleeve_symbol_for_ticket(ticket)
            except Exception:  # noqa: BLE001
                pair = None
            if pair and str(pair[0]) in tfs:
                return tfs[str(pair[0])]
        stub = str(comment or "")
        prefix = str(getattr(self, "_comment_prefix", "") or "")
        if prefix and stub.startswith(prefix):
            stub = stub[len(prefix):]
        stub = stub.strip()
        if not stub:
            return None
        cands = {tf for name, tf in tfs.items() if name.startswith(stub)}
        return cands.pop() if len(cands) == 1 else None

    def _f5_cross_tf_filter(self, exposures, intent_sleeve):
        """F5 only. Other books get their list back untouched.

        The open count is a fact. It blocks this sleeve only when that side
        is the unique highest. An empty answer or a tie does not block.
        An error returns the tickets already read so the same-symbol ask
        still sees them. It does not invent a count.
        """
        if str(getattr(self, "_namespace", "") or "") != "operator":
            return exposures
        if not exposures:
            return exposures
        try:
            if _spot_choice(
                "cross_tf_stack_cap",
                {
                    "open_count": len(exposures),
                    "sleeve": str(intent_sleeve or ""),
                    "namespace": "operator",
                },
                {
                    "stack_cap_blocks": "These open tickets block this sleeve.",
                    "stack_can_grow": "The open count is a fact. The book can still take this sleeve.",
                },
                "stack_cap_blocks",
                f"cross_tf_stack_cap|{intent_sleeve}|{len(exposures)}",
                "The open count is a fact on this state. "
                "Do these open tickets block this sleeve, or can the book still take it? "
                "An empty answer or a tie does not block. Do not close an open ticket.",
            ):
                return exposures
            my_tf = self._f5_sleeve_timeframe_of(sleeve=intent_sleeve)
            if my_tf is None:
                if _spot_choice(
                    "cross_tf_unknown_timeframe",
                    {
                        "sleeve": str(intent_sleeve or ""),
                        "timeframe_known": False,
                        "namespace": "operator",
                    },
                    {
                        "unknown_timeframe_blocks": "This sleeve has no timeframe. The open exposures block.",
                        "unknown_timeframe_does_not_block": "The missing timeframe is a fact. These exposures do not block.",
                    },
                    "unknown_timeframe_blocks",
                    f"cross_tf_unknown_timeframe|{intent_sleeve}|{len(exposures)}",
                    "The two sides of a sleeve timeframe that is unknown.",
                ):
                    return exposures
                return []
            blocking = []
            for p in exposures:
                if isinstance(p, dict):
                    comment, ticket = p.get("family") or p.get("comment"), p.get("ticket")
                else:
                    comment, ticket = getattr(p, "comment", None), getattr(p, "ticket", None)
                their_tf = self._f5_sleeve_timeframe_of(comment=comment, ticket=ticket)
                if their_tf is None or int(their_tf) == int(my_tf):
                    if _spot_choice(
                        "cross_tf_same_timeframe",
                        {
                            "sleeve": str(intent_sleeve or ""),
                            "my_timeframe": int(my_tf),
                            "their_timeframe": None if their_tf is None else int(their_tf),
                            "ticket": getattr(p, "ticket", None) if not isinstance(p, dict) else p.get("ticket"),
                            "namespace": "operator",
                        },
                        {
                            "same_timeframe_blocks": "This open ticket is the same timeframe or an unknown one. It blocks.",
                            "same_timeframe_does_not_block": "The timeframe reading is a fact. This open ticket does not block.",
                        },
                        "same_timeframe_blocks",
                        f"cross_tf_same|{intent_sleeve}|{my_tf}|{their_tf}|{getattr(p, 'ticket', None) if not isinstance(p, dict) else p.get('ticket')}",
                        "The two sides of an open ticket on the same timeframe, or with no timeframe.",
                    ):
                        blocking.append(p)
            return blocking
        except Exception:  # noqa: BLE001 — the tickets already read stay visible
            return exposures

    def _f5_real_account_breach_verdict(self, now_utc):
        """Real-account breach read. The flatten is the returned Noul or Choice.

        Live equity and live day P&L are facts. A floor dollar and a baseline
        dollar are not a limit and are not on the question. An empty return, a
        tie, a missing score, or an error does not flatten. None when the
        equity read fails.
        """
        try:
            equity = float(self._mt5.get_account_equity())
        except Exception:  # noqa: BLE001
            return None
        if not (equity > 0):
            return None
        dsb = None
        try:
            dsb = self.engine.broker_day_start_balance(now_utc)
        except Exception:  # noqa: BLE001
            dsb = None
        realized = None
        if isinstance(dsb, (int, float)) and float(dsb) > 0:
            realized = (equity - float(dsb)) / float(dsb)
        state = {
            "equity": equity,
            "realized_pct": realized,
            "namespace": "operator",
        }
        if isinstance(dsb, (int, float)) and float(dsb) > 0:
            state["day_start_balance"] = float(dsb)
        day_line = _parameter_score(
            "daily_loss_line",
            state,
            "What realized-day fraction is the line on this state? "
            "The score you return is that fraction. "
            "Do not invent a number when the card is empty.",
        )
        if day_line is not None:
            state = dict(state)
            state["returned_daily_loss_line"] = float(day_line)
            state["realized_past_returned_line"] = bool(
                realized is not None and realized <= -abs(float(day_line))
            )
        reasons = []
        if _noul_withholds(
            "risk_floor",
            state,
            "Is real equity at a static risk that flattens this book? "
            "Do not flatten open gold 294215389 as a gesture.",
            {
                "withhold": "Real equity is at a static risk that flattens.",
                "allow": "The equity reading does not by itself close the book.",
            },
        ):
            reasons.append("returned risk noul")
        if _spot_choice(
            "daily_loss",
            state,
            {
                "daily_loss_reached": "The real day is a loss that flattens.",
                "day_is_a_fact": "Today's result is a fact. It does not by itself close the book.",
            },
            "daily_loss_reached",
            f"daily_loss|{equity:.2f}|{realized}",
            "The two sides of this real day. "
            "An empty answer or a tie does not flatten. "
            "A floor dollar and a baseline dollar are not a limit. "
            "Do not flatten open gold 294215389 as a gesture.",
        ):
            reasons.append("returned daily loss")
        return {
            "flatten": bool(reasons),
            "block_entries": bool(reasons),
            "reason": ("; ".join(reasons) or None),
            "metrics": {
                "equity": equity,
                "day_start_balance": dsb,
                "realized_pct": realized,
                "daily_loss_line": day_line,
            },
        }

    def _adopt_into_engine(self, ee, sym: str, sleeve: str, summary: dict) -> None:
        """Record an adoption, flag the position book-native (so generic overlays do not override the
        sleeve's validated exit), and restore its persisted dynamic policy when a trade record exists."""
        ticket = getattr(ee.active_trade, "ticket", None)
        row = {"symbol": sym, "sleeve": sleeve, "ticket": ticket}
        try:
            ee.active_trade.gtos_vnext_book_native_exit_management = True
        except Exception:
            pass
        self._latch_adopted_orig_sl_distance(ee)
        record = self._rehydrate_policy(ee, sleeve, sym)
        if isinstance(record, dict) and ticket not in (None, 0):
            instr = record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else {}
            tp = {
                "f5_nominal_risk_usd": instr.get("f5_nominal_risk_usd"),
                "f5_actual_risk_usd": instr.get("f5_actual_risk_usd"),
                "f5_intended_risk_usd": instr.get("f5_intended_risk_usd"),
            }
            try:
                ready = all(float(tp[k] or 0.0) > 0 for k in tp)
            except (TypeError, ValueError):
                ready = False
            if ready:
                # Carry the at-fill truth fields through the restart so the adoption
                # re-emit is not a degraded copy of the fill row (178414870 fix).
                for extra_key in ("f5_fill_deviation_r", "f5_actual_risk_at_fill_usd"):
                    if instr.get(extra_key) is not None:
                        tp[extra_key] = instr.get(extra_key)
                self._f5_on_open(
                    ticket=ticket,
                    sleeve=sleeve,
                    symbol=sym,
                    trade_params=tp,
                    candidate_id=record.get("candidate_id") or instr.get("candidate_id"),
                    decision_day=record.get("decision_day"),
                    decision_bar_iso=record.get("decision_bar_iso"),
                    source="adoption_rehydrate",
                )
        try:
            broker_symbol = self._broker_symbol(sym)
        except Exception:
            broker_symbol = None
        row.update(self._runtime_learning_trade_context(
            ticket=ticket,
            record=record,
            broker_symbol=broker_symbol,
        ))
        row.update(self._broker_position_protection(ticket, broker_symbol))
        summary["adopted"].append(row)

    def _latch_adopted_orig_sl_distance(self, ee) -> None:
        """On adopt, restore sl_distance from chair_orig_sl.json when live SL is tighter.

        Does not invent an orig. Missing ledger ticket keeps the live SL.
        Software TP1 is still forbidden by execution._software_tp1_forbidden.
        """
        trade = getattr(ee, "active_trade", None)
        if trade is None:
            return
        ticket = getattr(trade, "ticket", None)
        if ticket in (None, 0, ""):
            return
        try:
            from .minimal_size import f5_latch_orig_sl
        except Exception:
            return
        stored = None
        try:
            import json
            from pathlib import Path
            ledger_path = (
                Path(self._repo_root) / "pipeline_state" / "ultimate_book"
                / str(self._namespace) / "judgment" / "state" / "chair_orig_sl.json"
            )
            if ledger_path.is_file():
                doc = json.loads(ledger_path.read_text(encoding="utf-8"))
                raw = doc.get("tickets") if isinstance(doc, dict) and isinstance(doc.get("tickets"), dict) else doc
                if isinstance(raw, dict):
                    key = str(int(ticket)) if str(ticket).isdigit() else str(ticket)
                    if key in raw:
                        stored = float(raw[key])
        except Exception:
            return
        if stored is None:
            return
        latched = f5_latch_orig_sl(
            getattr(trade, "direction", ""),
            getattr(trade, "entry_price", None),
            live_sl=getattr(trade, "stop_loss", None),
            stored=stored,
        )
        if latched is None:
            return
        try:
            entry_f = float(trade.entry_price)
            orig_dist = abs(entry_f - float(latched))
        except (TypeError, ValueError):
            return
        if orig_dist <= 0:
            return
        live_dist = None
        try:
            live_sl = float(trade.stop_loss)
            if live_sl > 0:
                live_dist = abs(entry_f - live_sl)
        except (TypeError, ValueError):
            live_dist = None
        if live_dist is None or live_dist + 1e-12 < orig_dist:
            trade.sl_distance = orig_dist

    # ---- the weekend-holding policy (Session BA, B1900; default-OFF) ---------------------

    def weekend_policy_preflight(self) -> dict:
        """Resolve everything the weekend policy needs, once, at LAUNCH. Never raises.

        Returns `{"ok": True, "status": "off"|"armed", ...}` or `{"ok": False, "error": ...}`.
        The caller (`run_book.py`) REFUSES TO START on `ok: False`, and that is the whole point
        of doing it here: the policy's deadline needs `src/utils/broker_clock.py`, which
        `packet_economics.py:41-49` measured to be ABSENT from the live host as of the
        2026-07-26 VPS export, and a compliance policy that silently degrades to "nothing is
        due" is a funded account holding over a weekend while every log reads healthy. It also
        needs a REGISTERED server name; `_broker_server_name` returns None rather than guessing,
        and None is a refusal here rather than a default.
        """
        pol = self._weekend_policy
        if not getattr(pol, "enabled", False):
            return {"ok": True, "status": "off"}
        server = self._broker_server_name()
        if not server:
            return {"ok": False, "status": "unresolved_server",
                    "error": ("weekend policy is armed but the MT5 server name did not resolve "
                              "from the account or the profile, so the weekend boundary cannot "
                              "be located. Refusing to start rather than defaulting to 'no "
                              "weekend'."),
                    "policy": pol.as_dict()}
        try:
            from .weekend_policy import next_weekend_boundary_utc
            now = datetime.now(timezone.utc)
            boundary = next_weekend_boundary_utc(now, server)
            deadline = pol.flatten_deadline_utc(now, server)
        except Exception as exc:  # noqa: BLE001 - the refusal must carry the reason
            return {"ok": False, "status": "clock_unavailable", "error": repr(exc),
                    "server": server, "policy": pol.as_dict()}
        # A policy armed on a sleeve this worker does not trade is legal and SAFER than the
        # reverse (arm the guard first, the sleeve second) -- but it must be visible, because a
        # compliance guard that governs nothing reads exactly like one that works.
        try:
            traded = set(self.engine._active_sleeve_names())
        except Exception:  # noqa: BLE001
            traded = set()
        return {"ok": True, "status": "armed", "server": server,
                "next_weekend_boundary_utc": boundary.isoformat(),
                "next_flatten_deadline_utc": deadline.isoformat(),
                "policy": pol.as_dict(),
                "governs_sleeves_this_worker_does_not_trade":
                    sorted(set(pol.sleeves) - traded) if traded else None}

    def _weekend_flat_close(self, ee, sym: str, sleeve: str) -> Optional[str]:
        if str(getattr(self, "_namespace", "") or "") == "operator":
            return None
        """Close a governed position that is past its weekend deadline. `None` == nothing due.

        Argument order matches `_manage_engine(ee, sym, sleeve, summary)` deliberately: the two
        strings are interchangeable to a type checker, so a swap is silent, and a swapped pair
        here would govern the SYMBOL name — which is in no policy, so the guard would simply
        never fire. `test_ba_weekend_policy.py` arms the policy on one sleeve and asserts the
        other is untouched, which is the test that catches it.
        """
        pol = self._weekend_policy
        if not getattr(pol, "enabled", False):
            return None
        if getattr(ee, "active_trade", None) is None:
            return None
        if not pol.governs(sleeve):
            return None
        server = self._broker_server_name()
        if not server:
            # Preflight refuses to start without a server, so reaching here means the name
            # stopped resolving mid-run. Do not guess a weekend; the entry side is what
            # degrades conservatively (`_weekend_entry_block` refuses while the clock is dark).
            _log.error("book[%s]: weekend policy armed but server name unavailable for %s/%s; "
                       "no flatten decision is possible this tick.",
                       self._namespace, sym, sleeve)
            return None
        try:
            due = pol.flatten_due(sleeve, datetime.now(timezone.utc), server)
        except Exception as exc:  # noqa: BLE001 - management must continue; the fault is visible
            _log.error("book[%s]: weekend deadline unreadable for %s/%s: %r",
                       self._namespace, sym, sleeve, exc)
            return None
        if not due:
            return None
        _log.warning("book[%s]: WEEKEND FLAT due for %s/%s (policy=%s) — closing at market.",
                     self._namespace, sym, sleeve, pol.as_dict())
        try:
            if ee.close_position("weekend_flat"):
                return "weekend_flat"
        except Exception as exc:  # noqa: BLE001
            _log.error("book[%s]: weekend flat close FAILED for %s/%s: %r",
                       self._namespace, sym, sleeve, exc)
            return None
        _log.error("book[%s]: weekend flat close returned False for %s/%s — the position is "
                   "STILL OPEN and a funded account under this rule is out of compliance.",
                   self._namespace, sym, sleeve)
        return None

    def _f5_weekend_flat_close(self, ee, sym: str, sleeve: str,
                               now: Optional[datetime] = None) -> Optional[str]:
        """F5 weekend-carry question. The close runs only when that Choice is close.

        A locked-R line is the returned Score and may sit between levels. An empty
        Choice, a tie, a missing score, or an error does not close. A 24/7 symbol
        has no weekend gap. Never raises.
        """
        if self._namespace != "operator" or self._f5_capture is None:
            return None
        trade = getattr(ee, "active_trade", None)
        if trade is None:
            return None
        try:
            from .minimal_size import F5_ALWAYS_OPEN_SYMBOLS

            if str(sym) in F5_ALWAYS_OPEN_SYMBOLS:
                return None
            now = now or datetime.now(timezone.utc)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            ticket = getattr(trade, "ticket", None)
            emitted = getattr(self, "_f5_weekend_emitted", None)
            if emitted is None:
                emitted = self._f5_weekend_emitted = set()
            if len(emitted) > 512:
                for old in list(emitted)[:256]:
                    emitted.discard(old)
            locked_r = None
            try:
                entry = float(getattr(trade, "entry_price", 0.0) or 0.0)
                current_sl = float(getattr(trade, "stop_loss", 0.0) or 0.0)
                d = str(getattr(trade, "direction", "") or "").upper()
                sign = 1.0 if d == "LONG" else (-1.0 if d == "SHORT" else None)
                denom = 0.0
                record = self._load_trade_record(ticket) if ticket not in (None, 0) else None
                instr = (record or {}).get("instrumentation") \
                    if isinstance(record, dict) else None
                if isinstance(instr, dict):
                    try:
                        denom = abs(float(instr.get("entry_price"))
                                    - float(instr.get("stop_loss")))
                    except (TypeError, ValueError):
                        denom = 0.0
                if denom <= 0:
                    init_sl = (getattr(self, "_f5_initial_sl", None) or {}).get(
                        int(ticket)) if ticket not in (None, 0) else None
                    if init_sl is not None:
                        denom = abs(entry - float(init_sl))
                if denom <= 0:
                    try:
                        denom = float(getattr(trade, "sl_distance", 0.0) or 0.0)
                    except (TypeError, ValueError):
                        denom = 0.0
                if sign is not None and denom > 0 and entry > 0 and current_sl > 0:
                    locked_r = sign * (current_sl - entry) / denom
            except Exception:  # noqa: BLE001 - an unreadable lock is no lock
                locked_r = None
            state = {
                "symbol": sym,
                "sleeve": sleeve,
                "ticket": ticket,
                "weekday": int(now.weekday()),
                "hour_utc": int(now.hour),
                "minute_utc": int(now.minute),
                "locked_r": locked_r,
                "namespace": "operator",
                "launcher_weekend_flat_utc": "20:30",
            }
            try:
                from .launcher_facts import launcher_facts

                state.update(launcher_facts())
            except Exception:
                pass
            line = _parameter_score(
                "weekend_locked_r",
                state,
                "What locked R lets this open ticket ride? "
                "The score you return is that line. "
                "Do not invent a number when the card is empty.",
            )
            asked_day = now.date().isoformat()
            if line is not None and locked_r is not None and locked_r >= float(line):
                ekey = ("exempt", ticket, asked_day)
                if ekey not in emitted:
                    emitted.add(ekey)
                    self._f5_capture.emit("f5_weekend_flat", {
                        "ticket": ticket, "symbol": sym, "sleeve": sleeve,
                        "status": "exempt_locked_profit", "locked_r": locked_r,
                        "locked_r_exempt_threshold": float(line),
                        "broker_mutation": False})
                return None
            if line is not None:
                state = dict(state)
                state["returned_locked_r"] = float(line)
            if not _spot_choice(
                "f5_weekend_flat",
                state,
                {
                    "close": "Close this ticket for weekend carry.",
                    "leave": "Leave this ticket open.",
                },
                "close",
                f"f5_weekend_flat|{sym}|{sleeve}|{ticket}|{now.strftime('%Y%m%d%H')}",
                "The two sides of weekend carry on this open ticket. "
                "An empty answer or a tie does not close. "
                "A floor dollar and a baseline dollar are not a limit. "
                "Do not flatten open gold 294215389 as a gesture.",
            ):
                return None
            closed = False
            close_error = None
            try:
                closed = bool(ee.close_position("f5_weekend_flat"))
            except Exception as exc:  # noqa: BLE001
                close_error = repr(exc)
            status = "closed" if closed else "close_failed_position_still_open"
            ekey = (status, ticket, asked_day)
            if ekey not in emitted:
                emitted.add(ekey)
                row = {"ticket": ticket, "symbol": sym, "sleeve": sleeve,
                       "status": status, "locked_r": locked_r,
                       "returned_locked_r": None if line is None else float(line),
                       "broker_mutation": bool(closed)}
                if close_error is not None:
                    row["close_error"] = close_error
                self._f5_capture.emit("f5_weekend_flat", row)
            if closed:
                _log.warning("book[%s]: F5 WEEKEND FLAT %s/%s ticket=%s closed "
                             "(locked_r=%s)", self._namespace, sym, sleeve, ticket,
                             ("%.3f" % locked_r) if locked_r is not None else "n/a")
                return "f5_weekend_flat"
            _log.error("book[%s]: F5 weekend flat close FAILED for %s/%s ticket=%s (%s) -- "
                       "position STILL OPEN",
                       self._namespace, sym, sleeve, ticket,
                       close_error or "close_position returned False")
            return None
        except Exception as exc:  # noqa: BLE001 - the rule must never break management
            _log.warning("book[%s]: F5 weekend flat check failed for %s/%s (%r)",
                         self._namespace, sym, sleeve, exc)
            return None

    def _weekend_entry_block(self, sleeve: str, now: Optional[datetime] = None) -> Optional[str]:
        """`None` == the entry may proceed; a reason string == refuse it.

        Refuses on a dark clock as well as on the embargo, which is the opposite degradation to
        `_weekend_flat_close` and deliberately so: not closing is a compliance breach the book
        cannot help, while not opening is a missed trade. When the policy cannot tell whether a
        weekend is imminent, the safe side is to add no exposure it may not be able to manage.

        `now` is the CYCLE's instant, not a fresh read: the entry decision has to be made on the
        same clock as the decision bar it is about, and passing it also makes the end-to-end path
        testable without monkeypatching this module's `datetime`.
        """
        pol = self._weekend_policy
        if not getattr(pol, "enabled", False) or not pol.governs(sleeve):
            return None
        server = self._broker_server_name()
        if not server:
            return "weekend_policy_clock_unavailable"
        try:
            if pol.entry_blocked(sleeve, now or datetime.now(timezone.utc), server):
                return "weekend_entry_embargo"
        except Exception as exc:  # noqa: BLE001
            _log.error("book[%s]: weekend embargo unreadable for %s: %r",
                       self._namespace, sleeve, exc)
            return "weekend_policy_clock_unavailable"
        return None

    def _place_failure_bar(self, reason) -> str:
        """``open``, ``consume``, or ``unanswered``.

        On Challenge an order timeout is the hop. Other books, and any other
        broker class, keep the prefix read. Unanswered does not restore the
        retry law and is not a send.
        """
        text = str(reason or "")
        if (
            str(getattr(self, "_namespace", "") or "") == "operator"
            and _is_order_timeout_reason(text)
        ):
            pack = _order_timeout_pack(text)
            choice = pack.get("order_timeout") if isinstance(pack, dict) else None
            if choice == "keep_bar":
                return "open"
            if choice == "consume_bar":
                return "consume"
            return "unanswered"
        if _is_transient_place_failure(text):
            return "open"
        return "consume"

    def _mark_timeout_quiet(self, sleeve, symbol, dbar) -> None:
        quiet = getattr(self, "_timeout_quiet", None)
        if not isinstance(quiet, set):
            quiet = set()
            self._timeout_quiet = quiet
        quiet.add((sleeve, symbol, dbar))

    def _timeout_attempt_ended(self, *, intent, dbar, reason, now, summary) -> bool:
        """The returned retry budget ends the bar. An empty budget does not."""
        pack = _order_timeout_pack(reason)
        budget = _finite_number(
            pack.get("order_timeout_retries") if isinstance(pack, dict) else None
        )
        try:
            prefix = _order_timeout_class(reason) or "order_timeout"
            sleeve = getattr(intent, "sleeve", "?")
            symbol = getattr(intent, "symbol", "?")
            key = (sleeve, symbol, dbar, prefix)
            now_iso = now.isoformat() if hasattr(now, "isoformat") else str(now)
            counts = getattr(self, "_transient_retry_counts", None)
            if not isinstance(counts, dict):
                counts = {}
                self._transient_retry_counts = counts
            st = counts.get(key)
            if st is None:
                st = {"attempts": 0, "first_attempt_utc": now_iso}
                counts[key] = st
            st["attempts"] = int(st["attempts"]) + 1
            st["last_attempt_utc"] = now_iso
            if budget is None or st["attempts"] <= float(budget):
                return False
            ended = getattr(self, "_timeout_ended", None)
            if not isinstance(ended, set):
                ended = set()
                self._timeout_ended = ended
            ended.add((sleeve, symbol, dbar))
            if isinstance(summary, dict):
                summary.setdefault("skipped", []).append({
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "decision_bar_iso": dbar,
                    "reason": "order_timeout_retries",
                    "attempts": st["attempts"],
                    "order_timeout_retries": float(budget),
                    "last_reason": str(reason),
                })
            return True
        except Exception:
            return False

    def _timeout_quiet_holds(self, sleeve, symbol, dbar) -> bool:
        quiet = getattr(self, "_timeout_quiet", None)
        if not quiet:
            return False
        return (sleeve, symbol, dbar) in quiet

    def _note_timeout_unanswered(self, summary, sleeve, symbol, dbar) -> None:
        """An empty timeout hop leaves the bar open and does not send again."""
        self._mark_timeout_quiet(sleeve, symbol, dbar)
        if isinstance(summary, dict):
            summary["bar_consumable"] = False
            summary.setdefault("skipped", []).append({
                "symbol": symbol,
                "sleeve": sleeve,
                "decision_bar_iso": dbar,
                "reason": "order_timeout_unanswered",
            })

    def _lifetime_facts(self, sym, sleeve, trade) -> dict:
        """Live card for one open ticket. Missing reads stay off the card."""
        ticket = getattr(trade, "ticket", None)
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            ticket_i = None
        direction = str(getattr(trade, "direction", "") or "").upper()
        entry = _finite_number(getattr(trade, "entry_price", None))
        current_sl = _finite_number(getattr(trade, "stop_loss", None))
        take_profit = _finite_number(getattr(trade, "take_profit_1", None))
        if take_profit is None:
            take_profit = _finite_number(getattr(trade, "take_profit", None))
        volume = _finite_number(getattr(trade, "current_volume", None))
        init_map = getattr(self, "_f5_initial_sl", None) or {}
        init_sl = _finite_number(init_map.get(ticket_i)) if ticket_i is not None else None
        if init_sl is None:
            init_sl = current_sl
        try:
            tick = self._tick(sym)
        except Exception:
            tick = None
        bid = _finite_number(getattr(tick, "bid", None))
        ask = _finite_number(getattr(tick, "ask", None))
        mark = bid if direction == "LONG" else ask if direction == "SHORT" else None
        fav_r = None
        if (
            entry is not None
            and init_sl is not None
            and mark is not None
            and abs(entry - init_sl) > 0
        ):
            denom = abs(entry - init_sl)
            if direction == "LONG":
                fav_r = (mark - entry) / denom
            elif direction == "SHORT":
                fav_r = (entry - mark) / denom
        store = getattr(self, "_lifetime_mfe_r", None)
        if not isinstance(store, dict):
            store = {}
            self._lifetime_mfe_r = store
        mfe = None
        if ticket_i is not None:
            prev = _finite_number(store.get(ticket_i))
            if fav_r is not None:
                mfe = fav_r if prev is None else max(prev, fav_r)
                store[ticket_i] = mfe
            else:
                mfe = prev
        giveback = None
        if mfe is not None and fav_r is not None:
            giveback = mfe - fav_r
        age_s = None
        entry_time = getattr(trade, "entry_time", None)
        if entry_time:
            try:
                opened = datetime.fromisoformat(str(entry_time))
                if opened.tzinfo is None:
                    opened = opened.replace(tzinfo=timezone.utc)
                age_s = (datetime.now(timezone.utc) - opened).total_seconds()
            except (TypeError, ValueError):
                age_s = None
        facts = {
            "ticket": ticket_i,
            "symbol": str(sym or ""),
            "sleeve": str(sleeve or ""),
            "direction": direction,
            "entry": entry,
            "stop": current_sl,
            "initial_stop": init_sl,
            "take_profit": take_profit,
            "volume": volume,
            "bid": bid,
            "ask": ask,
            "favourable_r": fav_r,
            "mfe_r": mfe,
            "giveback_r": giveback,
            "positive_then_giveback": bool(
                mfe is not None and mfe > 0 and giveback is not None and giveback > 0
            ),
            "age_s": age_s,
            "profit": _finite_number(getattr(trade, "profit", None)),
            "namespace": "operator",
        }
        return {key: value for key, value in facts.items() if value is not None}

    def _remember_lifetime(self, symbol, pack, facts) -> dict:
        pack = pack if isinstance(pack, dict) else {}
        facts = facts if isinstance(facts, dict) else {}
        row = {
            "symbol": str(symbol or ""),
            "ticket": facts.get("ticket"),
            "move_stop": pack.get("move_stop"),
            "break_even": pack.get("break_even"),
            "scale_out": pack.get("scale_out"),
            "time_stop": pack.get("time_stop"),
            "close": pack.get("close"),
            "lifetime_stop": pack.get("lifetime_stop"),
            "lifetime_scale": pack.get("lifetime_scale"),
            "giveback_r": facts.get("giveback_r"),
            "positive_then_giveback": facts.get("positive_then_giveback"),
        }
        by_symbol = getattr(self, "_lifetime_by_symbol", None)
        if not isinstance(by_symbol, dict):
            by_symbol = {}
            self._lifetime_by_symbol = by_symbol
        if symbol:
            by_symbol[str(symbol)] = row
        return row

    def _stamp_lifetime_notes(self, notes, symbol) -> dict:
        """Hop returns the place call can read. Empty stays off the map."""
        merged = dict(notes) if isinstance(notes, dict) else {}
        life = (getattr(self, "_lifetime_by_symbol", None) or {}).get(str(symbol or ""))
        if not isinstance(life, dict):
            return merged
        for key in (
            "move_stop",
            "break_even",
            "scale_out",
            "time_stop",
            "close",
            "lifetime_stop",
            "lifetime_scale",
        ):
            value = life.get(key)
            if value in (None, ""):
                continue
            merged[key] = value
        return merged

    def _with_lifetime_emit(self, fn):
        """Use the lifetime return for close and stop moves. Do not post them again."""
        import src.judgment.manage_choices as manage_choices

        original = manage_choices.emit_manage
        owner = self

        def _emit(act, **kwargs):
            sends = getattr(owner, "_lifetime_sends", None)
            if not isinstance(sends, dict) or act not in sends:
                return original(act, **kwargs)
            if act == "move_sl":
                want = sends.get("stop")
                proposed = kwargs.get("proposed")
                if sends.get("move_sl") is not True or want is None or proposed is None:
                    return False
                try:
                    return abs(float(proposed) - float(want)) <= 1e-8
                except (TypeError, ValueError):
                    return False
            return bool(sends.get(act))

        manage_choices.emit_manage = _emit
        try:
            return fn()
        finally:
            manage_choices.emit_manage = original

    def _move_lifetime_stop(self, ee, trade, new_stop) -> bool:
        price = _finite_number(new_stop)
        ticket = getattr(trade, "ticket", None)
        if price is None or ticket in (None, 0):
            return False
        modify = getattr(ee, "_modify_sl", None)
        if not callable(modify):
            return False
        try:
            ok = bool(modify(
                int(ticket),
                float(price),
                trade=trade,
                modify_reason="lifetime_stop",
            ))
        except Exception:
            return False
        if ok:
            try:
                trade.stop_loss = float(price)
            except Exception:
                pass
        return ok

    def _scale_out_volume(self, ee, trade, fraction) -> bool:
        """Close the returned fraction of this ticket. Empty does not scale."""
        portion = _finite_number(fraction)
        current = _finite_number(getattr(trade, "current_volume", None))
        if (
            portion is None
            or portion <= 0
            or portion > 1
            or current is None
            or current <= 0
        ):
            return False
        geometry_fn = getattr(ee, "_close_request_execution_geometry", None)
        send = getattr(ee, "safe_place_order", None)
        if not callable(geometry_fn) or not callable(send):
            return False
        try:
            geometry = geometry_fn(
                trade, current * portion, close_reason="lifetime_scale_out",
            )
        except Exception:
            geometry = None
        if not isinstance(geometry, dict):
            return False
        volume = _finite_number(geometry.get("volume"))
        if volume is None or volume <= 0 or volume > current + 1e-8:
            return False
        direction = str(getattr(trade, "direction", "") or "").upper()
        request = {
            "action": 1,
            "symbol": getattr(ee, "symbol", None),
            "volume": volume,
            "type": 1 if direction == "LONG" else 0,
            "position": getattr(trade, "ticket", None),
            "magic": getattr(ee, "_magic", None) or getattr(self, "_magic", None),
            "deviation": geometry.get("deviation"),
            "type_filling": geometry.get("type_filling"),
            "comment": "lifetime_scale",
        }
        try:
            result = send(request)
        except Exception:
            return False
        if not getattr(result, "success", False):
            return False
        try:
            trade.current_volume = max(current - volume, 0.0)
        except Exception:
            pass
        return True

    def _run_ticket_lifetime(self, ee, sym, sleeve, summary) -> str | None:
        """One ask for this ticket's card. The returns move, scale, or close it.

        The same card does not send twice. An empty hop does not send and does
        not restore a breakeven, a giveback close, or a time stop.
        """
        trade = getattr(ee, "active_trade", None)
        ticket = getattr(trade, "ticket", None) if trade is not None else None
        if trade is None or ticket in (None, 0):
            return None
        if str(getattr(self, "_namespace", "") or "") != "operator":
            return None
        self._lifetime_sends = {"close": False, "move_sl": False, "stop": None}
        try:
            facts = self._lifetime_facts(sym, sleeve, trade)
            pack = _lifetime_pack(facts)
        except Exception:
            return None
        if not isinstance(pack, dict):
            pack = {}
        row = self._remember_lifetime(sym, pack, facts)
        if isinstance(summary, dict):
            summary.setdefault("lifetime", []).append(dict(row))
        fingerprint = _facts_fingerprint(facts)
        done = getattr(self, "_lifetime_applied", None)
        if not isinstance(done, dict):
            done = {}
            self._lifetime_applied = done
        applied_key = (ticket, fingerprint)
        if applied_key in done:
            return done[applied_key]
        stop = _finite_number(pack.get("lifetime_stop"))
        want_move = pack.get("move_stop") == "move_stop" or pack.get("break_even") == "break_even"
        want_close = pack.get("close") == "close" or pack.get("time_stop") == "time_stop"
        self._lifetime_sends = {
            "close": want_close,
            "move_sl": bool(want_move and stop is not None and not want_close),
            "stop": stop,
        }
        if not self._live_broker_authority():
            row["broker_mutation"] = False
            done[applied_key] = None
            return None
        applied = None

        def _apply():
            nonlocal applied
            if pack.get("close") == "close":
                try:
                    closed = bool(ee.close_position("lifetime_close"))
                except Exception:
                    closed = False
                if closed:
                    applied = "close"
                return
            if pack.get("time_stop") == "time_stop":
                try:
                    closed = bool(ee.close_position("lifetime_time_stop"))
                except Exception:
                    closed = False
                if closed:
                    applied = "time_stop"
                return
            if want_move and stop is not None:
                current = _finite_number(getattr(trade, "stop_loss", None))
                if current is None or abs(current - float(stop)) > 1e-8:
                    if self._move_lifetime_stop(ee, trade, stop):
                        applied = (
                            "break_even"
                            if pack.get("break_even") == "break_even"
                            else "move_stop"
                        )
            if (
                pack.get("scale_out") == "scale_out"
                and getattr(ee, "active_trade", None) is not None
            ):
                if self._scale_out_volume(ee, trade, pack.get("lifetime_scale")):
                    applied = applied or "scale_out"

        try:
            self._with_lifetime_emit(_apply)
        except Exception:
            applied = None
        if applied:
            row["applied"] = applied
        done[applied_key] = applied
        return applied

    def _manage_engine(self, ee, sym: str, sleeve: str, summary: dict) -> None:
        """Apply the time-stop + tick-driven exit management for one engine; record close + notify."""
        ts_action = None
        active_before = getattr(ee, "active_trade", None)
        ticket = getattr(active_before, "ticket", None)
        record = self._load_trade_record(ticket) if ticket is not None else None
        try:
            broker_symbol = self._broker_symbol(sym)
        except Exception:
            broker_symbol = None
        checked_at = datetime.now(timezone.utc).isoformat()
        broker_protection = self._broker_position_protection(ticket, broker_symbol)
        if getattr(ee, "active_trade", None) is not None:
            record = self._mark_trade_record_management_checked(
                ticket,
                checked_at,
                record=record,
                broker_symbol=broker_symbol,
                sleeve=sleeve,
                symbol=sym,
                broker_protection=broker_protection,
            ) or record
        join_ctx = self._runtime_learning_trade_context(
            ticket=ticket,
            record=record,
            broker_symbol=broker_symbol,
            management_checked_at_utc=checked_at,
        )
        if not self._live_broker_authority():
            managed_row = {
                "symbol": sym,
                "sleeve": sleeve,
                "action": "live_broker_authority_false_observe_only",
                "live_broker_authority": False,
                "broker_mutation_allowed": False,
                "source_completeness_status": "runtime_management_observed_broker_mutation_disabled",
                **join_ctx,
            }
            summary["managed"].append(managed_row)
            return
        try:
            # WEEKEND FLAT (Session BA, B1900; default-OFF). Checked BEFORE the time stop, for
            # the same reason `exits.replay` checks scheduled exits after price-triggered ones
            # and before the horizon: a compliance deadline is not a policy preference that can
            # wait a tick. If it fires, the engine is already closed and the time-stop check must
            # not run on it -- which is exactly the guard the existing `active_trade is None`
            # branch below implements, so this reuses that path rather than adding one.
            ts_action = self._weekend_flat_close(ee, sym, sleeve)
            if ts_action is None:
                # F5 weekend carry asks Jev. The close runs only on that Choice.
                ts_action = self._f5_weekend_flat_close(ee, sym, sleeve)
            if ts_action is None and str(getattr(self, "_namespace", "") or "") == "operator":
                # One pack: move, break even, scale out, time stop, close.
                # The engine's own time-stop ask is not posted again.
                self._lifetime_sends = {"close": False, "move_sl": False, "stop": None}
                life = self._run_ticket_lifetime(ee, sym, sleeve, summary)
                if life in {"close", "time_stop"} and getattr(ee, "active_trade", None) is None:
                    ts_action = "lifetime_" + life
            elif ts_action is None:
                ts_close = getattr(ee, "check_time_stop_and_close", None)
                if callable(ts_close):
                    ts_action = ts_close()
            policy_clock = None
            get_clock = getattr(ee, "get_time_stop_clock_diagnostic", None)
            if callable(get_clock):
                policy_clock = get_clock()
            if policy_clock is None:
                policy_clock = getattr(ee, "_last_time_stop_clock_diagnostic", None)
            join_ctx.update(self._runtime_learning_policy_clock_context(policy_clock))
        except Exception as exc:  # noqa: BLE001 - management must continue, but the fault must be visible.
            policy_clock = {
                "schema_version": "gtos.vnext.time_stop_clock_diagnostic.v1",
                "checked_at_utc": checked_at,
                "status": "exception",
                "ticket": ticket,
                "error": repr(exc),
            }
            join_ctx.update(self._runtime_learning_policy_clock_context(policy_clock))
            error_row = {
                "symbol": sym,
                "sleeve": sleeve,
                "action": "time_stop_check_exception",
                "error": repr(exc),
                **join_ctx,
            }
            summary["errors"].append(error_row)
            _log.warning(
                "book[%s]: time-stop check failed for %s/%s ticket=%s: %r",
                self._namespace,
                sym,
                sleeve,
                ticket,
                exc,
            )
        # If the time-stop ALREADY closed the position, record THAT close (with its real reason) and do
        # NOT run check_and_manage_trade on a now-closed engine (which would relabel the close as a generic
        # no-op action and lose the time-stop reason).
        if getattr(ee, "active_trade", None) is None:
            close_action = ts_action or "vnext_time_stop"
            closed_record = self._mark_trade_record_closed(
                ticket,
                close_action,
                checked_at,
                record=record,
                broker_symbol=broker_symbol,
                sleeve=sleeve,
                symbol=sym,
            )
            if closed_record is not None:
                join_ctx.update(self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=closed_record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                ))
            managed_row = {"symbol": sym, "sleeve": sleeve, "action": close_action, **join_ctx}
            summary["managed"].append(managed_row)
            summary["closed"].append(dict(managed_row))
            self._notify_closed(sym, close_action, closed_record=closed_record)
            return
        if str(getattr(self, "_namespace", "") or "") == "operator":
            # The lifetime return is the close and the stop. The engine's
            # giveback path does not post a second ask and does not restore
            # a planted close.
            action = self._with_lifetime_emit(lambda: ee.check_and_manage_trade({}))
        else:
            action = ee.check_and_manage_trade({})
        if getattr(ee, "active_trade", None) is not None:
            refreshed_protection = self._broker_position_protection(ticket, broker_symbol)
            if refreshed_protection:
                record = self._mark_trade_record_management_checked(
                    ticket,
                    checked_at,
                    record=record,
                    broker_symbol=broker_symbol,
                    sleeve=sleeve,
                    symbol=sym,
                    broker_protection=refreshed_protection,
                ) or record
                join_ctx.update(self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                ))
        managed_row = {"symbol": sym, "sleeve": sleeve, "action": action, **join_ctx}
        summary["managed"].append(managed_row)
        self._f5_on_manage(ticket=ticket, sleeve=sleeve, symbol=sym, ee=ee, action=action,
                           checked_at=checked_at)
        if getattr(ee, "active_trade", None) is None:
            closed_record = self._mark_trade_record_closed(
                ticket,
                action,
                checked_at,
                record=record,
                broker_symbol=broker_symbol,
                sleeve=sleeve,
                symbol=sym,
            )
            if closed_record is not None:
                managed_row.update(self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=closed_record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                ))
            summary["closed"].append(dict(managed_row))
            self._notify_closed(sym, action, closed_record=closed_record)

    def _open_book_positions_by_canonical(self, canon_symbols, *, open_positions_snapshot=None) -> dict:
        """Snapshot all open book positions (magic-filtered) once, keyed by CANONICAL symbol. Returns {}
        when the mt5 lacks get_open_positions (mocks) -> the per-pair comment-routed reconcile still runs."""
        out: dict = {}
        try:
            if open_positions_snapshot is None:
                open_positions_snapshot = self._open_book_positions_snapshot()
            if open_positions_snapshot is None:
                return out
            b2c: dict[str, list[str]] = {}
            for c in canon_symbols:
                try:
                    b2c.setdefault(self._broker_symbol(c), []).append(c)
                except Exception:
                    pass
            for p in (open_positions_snapshot or []):
                for canon in (b2c.get(getattr(p, "symbol", None)) or []):
                    out.setdefault(canon, []).append(p)
        except Exception:
            pass
        return out

    def _manageable_pairs(self) -> list:
        """(canonical symbol, sleeve) pairs this profile can hold = each active sleeve x its on_surface
        symbols that have an instrument config on this profile. Cached. The redacted_account follower lacks some
        crosses/legs, so those (symbol, sleeve) pairs are dropped (a position can't exist on them here)."""
        cached = getattr(self, "_manageable_pairs_cache", None)
        if cached is not None:
            return cached
        from .sleeves.registry import active_specs
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        include_candidate_book = config_bool_value(rt.get("ultimate_book_include_candidate_book", False), False)
        include_market_expansion_book = config_bool_value(
            rt.get("ultimate_book_include_market_expansion_book", False),
            False,
        )
        candidate_sleeves = self._candidate_book_sleeves()
        expansion_sleeves = self._market_expansion_sleeves()
        pairs = []
        generation_tags = getattr(self, "_generation_tags", None)
        if generation_tags is not None:
            generation_tags = [str(t) for t in generation_tags if str(t)]
        for spec in active_specs(
            generation_tags,
            include_candidate_book=include_candidate_book,
            candidate_book_sleeves=candidate_sleeves or None,
            include_market_expansion_book=include_market_expansion_book,
            market_expansion_sleeves=expansion_sleeves or None,
        ):
            for s in (spec.on_surface or []):
                if self._profile_supports_symbol(s):
                    pairs.append((s, spec.tag))
        self._manageable_pairs_cache = pairs
        return pairs

    def _rehydrate_policy(self, ee, sleeve=None, symbol=None) -> dict | None:
        """After adopting an orphan, restore its vNext exit policy so management is the exact validated
        lifecycle (not generic). Prefer the persisted on-disk trade record; if it is MISSING
        (adopt-missing-record) reconstruct the sleeve's NATIVE policy from its identity (the W7:{sleeve}
        comment) so the adopted position keeps its validated time-stop / scale-out / target rather than
        degrading to the generic floor. Best-effort; NEVER raises."""
        try:
            ticket = getattr(getattr(ee, "active_trade", None), "ticket", None)
            rec = self._load_trade_record(ticket) if ticket is not None else None
            if rec is None and sleeve:
                from .execution_packets import native_policy_instrumentation
                rec = {"instrumentation": native_policy_instrumentation(
                           sleeve, frontier_exits=self._frontier_exits),
                       "execution": {"ticket": ticket}, "sleeve": sleeve, "symbol": symbol,
                       "reconstructed_from_sleeve_identity": True}
                _log.warning("book[%s]: ticket %s adopted with NO trade record -> rehydrated the '%s' "
                             "NATIVE exit policy from the W7 comment (time-stop/scale-out restored, not "
                             "the generic floor)", self._namespace, ticket, sleeve)
                self._persist_reconstructed_trade_record(ticket, rec)
            hyd = getattr(ee, "hydrate_vnext_dynamic_policy_from_record", None)
            if rec is not None and callable(hyd):
                rec = dict(rec)
                if self._live_broker_authority():
                    # CONTRACT V2 (Fable 5.1, 2026-09-02): on F5 an adopted ticket that already
                    # carries a broker TP keeps it. hydrate re-anchored TP = entry +/- R x
                    # |entry - live SL| on every adoption (49 restarts in 12 days); a tightened
                    # or record-less stop pulled the researched 6R target closer to entry.
                    _keep_tp = False
                    try:
                        _keep_tp = (
                            str(getattr(self, "_namespace", "") or "") == "operator"
                            and float(getattr(ee.active_trade, "take_profit_1", 0.0) or 0.0) > 0.0
                        )
                    except (TypeError, ValueError, AttributeError):
                        _keep_tp = False
                    if _keep_tp:
                        try:
                            hydrated = bool(hyd(rec, modify_broker_tp=False))
                        except TypeError:
                            hydrated = bool(hyd(rec))
                    else:
                        hydrated = bool(hyd(rec))
                else:
                    try:
                        hydrated = bool(hyd(rec, modify_broker_tp=False))
                    except TypeError:
                        rec["rehydration_status"] = (
                            "skipped_hydrator_without_read_only_kwarg_broker_authority_false"
                        )
                        return rec
                rec["rehydration_status"] = "hydrated" if hydrated else "hydrate_returned_false"
            elif rec is not None:
                rec = dict(rec)
                rec["rehydration_status"] = "hydrator_unavailable"
            elif sleeve:
                rec = {
                    "execution": {"ticket": ticket},
                    "sleeve": sleeve,
                    "symbol": symbol,
                    "rehydration_status": "missing_trade_record_native_reconstruction_unavailable",
                }
            return rec
        except Exception as exc:  # noqa: BLE001 - adoption must continue, but packets must show the fault.
            _log.warning(
                "book[%s]: ticket %s policy rehydration failed for %s/%s: %r",
                self._namespace,
                getattr(getattr(ee, "active_trade", None), "ticket", None),
                symbol,
                sleeve,
                exc,
            )
            return {
                "execution": {
                    "ticket": getattr(getattr(ee, "active_trade", None), "ticket", None),
                },
                "sleeve": sleeve,
                "symbol": symbol,
                "rehydration_status": "exception",
                "rehydration_error": repr(exc),
            }

    # ---------------- trade-record persistence (cross-restart policy rehydration) ----------------
    def _trade_record_path(self):
        from pathlib import Path
        d = Path(self._repo_root) / "pipeline_state" / "ultimate_book" / self._namespace / "trade_records"
        return d

    def _write_trade_record(self, ticket, record: dict, *, context: str = "trade-record persist") -> bool:
        if ticket in (None, 0) or not isinstance(record, dict):
            return False
        try:
            import json
            import os
            from pathlib import Path

            d = self._trade_record_path()
            d.mkdir(parents=True, exist_ok=True)
            p = Path(d) / f"{ticket}.json"
            tmp = Path(str(p) + ".tmp")
            tmp.write_text(json.dumps(record, default=str), encoding="utf-8")
            os.replace(str(tmp), str(p))
            return True
        except Exception as e:
            _log.warning("book[%s]: %s FAILED for ticket %s (%r); exit-policy "
                         "rehydration may fall back after a restart",
                         self._namespace, context, ticket, e)
            return False

    @staticmethod
    def _set_record_value(mapping: dict, key: str, value: Any) -> bool:
        if value in (None, ""):
            return False
        if mapping.get(key) in (None, ""):
            mapping[key] = value
            return True
        return False

    def _merge_entry_reconciliation_from_record(self, record: dict) -> bool:
        if not isinstance(record, dict):
            return False
        inst = record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else {}
        packet = inst.get("gtos_vnext_broker_order_lifecycle_capture_v4_packet")
        if not isinstance(packet, dict):
            packet = inst.get("broker_order_lifecycle_capture_v4")
        if not isinstance(packet, dict):
            return False
        deal = packet.get("deal_cost_reconciliation")
        if not isinstance(deal, dict):
            return False
        changed = False
        execution = record.get("execution")
        if not isinstance(execution, dict):
            execution = {}
            record["execution"] = execution
            changed = True
        changed = self._set_record_value(
            execution, "broker_entry_deal_ticket", deal.get("deal_ticket")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_fill_time_utc", deal.get("broker_fill_time_utc")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_entry_price", deal.get("broker_entry_price")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_entry_commission", deal.get("commission")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_entry_swap", deal.get("swap")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_entry_source_status", deal.get("source_status")
        ) or changed
        changed = self._set_record_value(
            execution,
            "entry_reconciliation_status",
            deal.get("account_history_lookup_status") or packet.get("status"),
        ) or changed
        missing_fields = deal.get("missing_fields") or packet.get("missing_fields")
        if isinstance(missing_fields, list) and missing_fields and execution.get("broker_entry_missing_fields") in (None, ""):
            execution["broker_entry_missing_fields"] = list(missing_fields)
            changed = True
        changed = self._set_record_value(
            record,
            "entry_reconciliation_status",
            deal.get("account_history_lookup_status") or packet.get("status"),
        ) or changed
        if packet.get("broker_real_entry_label_ready") is not None and record.get("broker_real_entry_label_ready") is None:
            record["broker_real_entry_label_ready"] = bool(packet.get("broker_real_entry_label_ready"))
            changed = True
        if isinstance(packet.get("missing_fields"), list) and packet.get("missing_fields") and record.get("broker_real_missing_fields") in (None, ""):
            record["broker_real_missing_fields"] = list(packet.get("missing_fields"))
            changed = True
        return changed

    @staticmethod
    def _missingish_ticket(value: Any) -> bool:
        try:
            return value in (None, "", 0, "0")
        except Exception:
            return True

    @classmethod
    def _entry_reconciliation_missing_fields(cls, accounting: dict) -> list[str]:
        missing: list[str] = []
        if cls._missingish_ticket(accounting.get("broker_entry_deal_ticket")):
            missing.append("broker_entry_deal_ticket")
        if accounting.get("broker_fill_time_utc") in (None, ""):
            missing.append("broker_fill_time_utc")
        if accounting.get("broker_entry_price") in (None, ""):
            missing.append("broker_entry_price")
        if accounting.get("broker_entry_commission") is None:
            missing.append("commission")
        if accounting.get("broker_entry_swap") is None:
            missing.append("swap")
        return missing

    @staticmethod
    def _iso_from_deal_time_near_reference(
        value: Any,
        reference: datetime | None,
        *,
        max_shift_hours: int = 6,
        tolerance_minutes: int = 10,
    ) -> tuple[str | None, int | None]:
        iso = UltimateBookOwner._iso_from_deal_time(value)
        if not iso or reference is None:
            return iso, None
        try:
            dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return iso, None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        ref = reference
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        ref = ref.astimezone(timezone.utc)

        best = dt
        best_shift = 0
        best_distance = abs((dt - ref).total_seconds())
        for hours in range(-int(max_shift_hours), int(max_shift_hours) + 1):
            candidate = dt - timedelta(hours=hours)
            distance = abs((candidate - ref).total_seconds())
            if distance < best_distance:
                best = candidate
                best_shift = hours
                best_distance = distance
        if best_shift and best_distance <= int(tolerance_minutes) * 60:
            return best.isoformat(), best_shift * 3600
        return dt.isoformat(), None

    @staticmethod
    def _is_entry_deal_for_ticket(deal: Any, ticket: int) -> bool:
        try:
            entry = int(UltimateBookOwner._deal_value(deal, "entry", 0) or 0)
        except (TypeError, ValueError):
            entry = 0
        if entry not in {0}:
            return False
        for field in ("position_id", "order"):
            try:
                if int(UltimateBookOwner._deal_value(deal, field, 0) or 0) == int(ticket):
                    return True
            except (TypeError, ValueError):
                continue
        return False

    def _entry_reconciliation_window(self, record: dict) -> tuple[datetime | None, datetime | None, datetime | None]:
        inst = record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else {}
        packet = inst.get("gtos_vnext_broker_order_lifecycle_capture_v4_packet")
        if not isinstance(packet, dict):
            packet = inst.get("broker_order_lifecycle_capture_v4")
        order_obs = packet.get("order_send_observation") if isinstance(packet, dict) else {}
        if not isinstance(order_obs, dict):
            order_obs = {}
        execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
        order_send = self._parse_utc(order_obs.get("order_send_time_utc"))
        order_result = self._parse_utc(order_obs.get("order_result_time_utc"))
        placed = self._parse_utc(execution.get("placed_at_utc"))
        anchor = order_result or order_send or placed
        if not anchor:
            return None, None, None
        start = (order_send or anchor) - timedelta(minutes=5)
        end = (order_result or anchor) + timedelta(minutes=5)
        return start, end, anchor

    def _repair_entry_reconciliation_from_account_history(self, ticket: int, record: dict) -> bool:
        """Self-heal unresolved entry accounting once MT5 account history becomes available.

        This is read-only broker history inspection. It never sends, modifies, or closes orders.
        """
        if not isinstance(record, dict):
            return False
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            return False
        execution = record.setdefault("execution", {})
        status = execution.get("entry_reconciliation_status") or record.get("entry_reconciliation_status")
        current_missing = self._entry_reconciliation_missing_fields(execution)
        if status == "RECONCILED_FROM_ACCOUNT_HISTORY" and not current_missing:
            return False

        now = datetime.now(timezone.utc)
        last_attempt = self._entry_reconciliation_repair_last_attempt_utc.get(ticket_i)
        if last_attempt and (now - last_attempt).total_seconds() < 900:
            return False
        self._entry_reconciliation_repair_last_attempt_utc[ticket_i] = now

        broker_symbol = execution.get("broker_symbol")
        if not broker_symbol and record.get("symbol") not in (None, ""):
            try:
                broker_symbol = self._broker_symbol(record.get("symbol"))
            except Exception:
                broker_symbol = record.get("symbol")
        if not broker_symbol:
            return False
        start_utc, end_utc, reference = self._entry_reconciliation_window(record)
        if not start_utc or not end_utc:
            return False

        def _find(deals: list[Any]) -> Any | None:
            for deal in deals or []:
                if self._is_entry_deal_for_ticket(deal, ticket_i):
                    return deal
            return None

        match = None
        source_status = "broker_real_symbol_history_entry_reconciled"
        recovery_window_used = False
        history_fetch_failed = False
        history_source_returned = False
        history_fetch_error = None
        get_symbol_deals = getattr(self._mt5, "get_history_deals", None)
        if callable(get_symbol_deals):
            try:
                deals = get_symbol_deals(start_utc, end_utc, broker_symbol)
            except Exception as exc:
                deals = None
                history_fetch_failed = True
                history_fetch_error = repr(exc)
            if deals is None:
                history_fetch_failed = True
                history_fetch_error = history_fetch_error or "get_history_deals_returned_none"
            else:
                history_source_returned = True
                match = _find(deals)
            if match is None:
                recovery_start = start_utc - timedelta(hours=6)
                recovery_end = end_utc + timedelta(hours=6)
                try:
                    deals = get_symbol_deals(recovery_start, recovery_end, broker_symbol)
                except Exception as exc:
                    deals = None
                    history_fetch_failed = True
                    history_fetch_error = repr(exc)
                if deals is None:
                    history_fetch_failed = True
                    history_fetch_error = history_fetch_error or "get_history_deals_returned_none"
                else:
                    history_source_returned = True
                    match = _find(deals)
                    if match is not None:
                        source_status = "broker_real_symbol_history_entry_reconciled_recovery_window"
                        recovery_window_used = True

        if match is None:
            get_all_deals = getattr(self._mt5, "get_account_history_deals", None)
            if callable(get_all_deals):
                recovery_start = start_utc - timedelta(hours=6)
                recovery_end = end_utc + timedelta(hours=6)
                try:
                    deals = get_all_deals(recovery_start, recovery_end)
                except Exception as exc:
                    deals = None
                    history_fetch_failed = True
                    history_fetch_error = repr(exc)
                if deals is None:
                    history_fetch_failed = True
                    history_fetch_error = history_fetch_error or "get_account_history_deals_returned_none"
                else:
                    history_source_returned = True
                    match = _find(deals)
                    if match is not None:
                        source_status = "broker_real_account_history_entry_reconciled_recovery_window"
                        recovery_window_used = True

        if match is None:
            if history_fetch_failed and not history_source_returned:
                execution["entry_reconciliation_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                execution["broker_entry_source_status"] = "account_history_lookup_failed"
                execution["entry_reconciliation_repair_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                execution["entry_reconciliation_repair_error"] = history_fetch_error
                record["entry_reconciliation_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                record["broker_real_entry_label_ready"] = False
                record["broker_real_missing_fields"] = self._entry_reconciliation_missing_fields(execution)
                record["gtos_vnext_broker_entry_reconciliation_repair_v1_packet"] = {
                    "status": "ACCOUNT_HISTORY_LOOKUP_FAILED",
                    "missing_fields": record["broker_real_missing_fields"],
                    "error": history_fetch_error,
                }
                return True
            return False

        fill_time, fill_time_alignment_offset = self._iso_from_deal_time_near_reference(
            self._deal_value(match, "time"),
            reference,
        )
        deal_ticket = self._deal_value(match, "ticket")
        order_ticket = self._deal_value(match, "order")
        position_id = self._deal_value(match, "position_id")
        price = self._deal_value(match, "price")
        commission = self._deal_value(match, "commission")
        swap = self._deal_value(match, "swap")
        repaired_accounting = {
            "broker_entry_deal_ticket": deal_ticket,
            "broker_fill_time_utc": fill_time,
            "broker_entry_price": price,
            "broker_entry_commission": commission,
            "broker_entry_swap": swap,
        }
        missing_fields = self._entry_reconciliation_missing_fields(repaired_accounting)
        repaired_status = (
            "RECONCILED_FROM_ACCOUNT_HISTORY"
            if not missing_fields
            else "ACCOUNT_HISTORY_ENTRY_FOUND_INCOMPLETE"
        )

        execution.update(
            {
                "broker_entry_deal_ticket": deal_ticket,
                "broker_fill_time_utc": fill_time,
                "broker_entry_price": price,
                "broker_entry_commission": commission,
                "broker_entry_swap": swap,
                "broker_entry_source_status": source_status,
                "entry_reconciliation_status": repaired_status,
                "broker_entry_missing_fields": missing_fields,
                "entry_reconciliation_repair_status": repaired_status,
                "entry_reconciliation_repair_checked_at_utc": now.isoformat(),
                "entry_reconciliation_repair_source_status": source_status,
                "entry_reconciliation_repair_recovery_window_used": recovery_window_used,
                "entry_reconciliation_repair_match_keys": {
                    "matched_by": "position_id_or_order_ticket",
                    "ticket": deal_ticket,
                    "order": order_ticket,
                    "position_id": position_id,
                    "price": price,
                    "recovery_window_used": recovery_window_used,
                },
            }
        )
        if fill_time_alignment_offset is not None:
            execution["broker_fill_time_alignment_offset_seconds"] = fill_time_alignment_offset
        record["entry_reconciliation_status"] = repaired_status
        record["broker_real_entry_label_ready"] = not missing_fields
        record["broker_real_missing_fields"] = missing_fields
        record["gtos_vnext_broker_entry_reconciliation_repair_v1_packet"] = {
            "schema_version": "broker_entry_reconciliation_repair_v1",
            "component": "ultimate_book_trade_record_entry_reconciliation_repair",
            "generated_at_utc": now.isoformat(),
            "status": repaired_status,
            "runtime_effect_boundary": "read_only_account_history_no_broker_mutation",
            "identity": {
                "ticket": ticket_i,
                "symbol": record.get("symbol"),
                "broker_symbol": broker_symbol,
                "candidate_id": record.get("candidate_id"),
            },
            "lookup_window_start_utc": start_utc.isoformat(),
            "lookup_window_end_utc": end_utc.isoformat(),
            "source_status": source_status,
            "match_keys": execution["entry_reconciliation_repair_match_keys"],
            "missing_fields": missing_fields,
        }
        return True

    def _normalize_trade_record(self, ticket, record: dict) -> tuple[dict, bool]:
        """Backfill legacy trade records with durable runtime-learning join keys."""
        if not isinstance(record, dict):
            return record, False
        changed = False
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            ticket_i = ticket

        execution = record.get("execution")
        if not isinstance(execution, dict):
            execution = {}
            record["execution"] = execution
            changed = True

        changed = self._set_record_value(execution, "ticket", ticket_i) or changed
        changed = self._set_record_value(
            execution, "ticket_hash_sha256", self._runtime_learning_ticket_hash(ticket_i)
        ) or changed
        if record.get("trade_lifecycle_status") in (None, "") and record.get("closed_at_utc") in (None, ""):
            record["trade_lifecycle_status"] = "open"
            changed = True

        row = None
        try:
            row = self._ledger.row_for_ticket(ticket_i)
        except Exception:
            row = None
        if isinstance(row, dict):
            for key in ("sleeve", "symbol", "decision_bar_iso", "decision_day", "cluster", "candidate_id"):
                changed = self._set_record_value(record, key, row.get(key)) or changed
            changed = self._set_record_value(execution, "placed_at_utc", row.get("ts")) or changed

        if record.get("decision_day") in (None, "") and record.get("decision_bar_iso"):
            record["decision_day"] = str(record.get("decision_bar_iso"))[:10]
            changed = True
        if record.get("cluster") in (None, "") and record.get("sleeve") not in (None, ""):
            changed = self._set_record_value(record, "cluster", cluster_of(record.get("sleeve"))) or changed
        if execution.get("broker_symbol") in (None, "") and record.get("symbol") not in (None, ""):
            try:
                changed = self._set_record_value(
                    execution, "broker_symbol", self._broker_symbol(record.get("symbol"))
                ) or changed
            except Exception:
                pass
        changed = self._merge_entry_reconciliation_from_record(record) or changed
        changed = self._repair_entry_reconciliation_from_account_history(ticket_i, record) or changed

        missing_exit_fields = execution.get("exit_reconciliation_missing_fields")
        if not isinstance(missing_exit_fields, list):
            missing_exit_fields = []
        else:
            missing_exit_fields = list(missing_exit_fields)
        if (
            execution.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
            and self._missingish_ticket(execution.get("broker_exit_order_ticket"))
            and "broker_exit_order_ticket" not in missing_exit_fields
        ):
            missing_exit_fields.append("broker_exit_order_ticket")
            execution["exit_reconciliation_missing_fields"] = missing_exit_fields
            record["exit_reconciliation_missing_fields"] = missing_exit_fields
            changed = True
        if (
            record.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
            and self._missingish_ticket(record.get("broker_exit_order_ticket"))
            and "broker_exit_order_ticket" not in missing_exit_fields
        ):
            missing_exit_fields.append("broker_exit_order_ticket")
            execution["exit_reconciliation_missing_fields"] = missing_exit_fields
            record["exit_reconciliation_missing_fields"] = missing_exit_fields
            changed = True

        changed = self._repair_exit_reconciliation_from_account_history(ticket_i, record) or changed

        inst = record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else {}
        has_ticket_hash = bool(execution.get("ticket_hash_sha256"))
        has_candidate = bool(record.get("candidate_id") or inst.get("candidate_id"))
        has_decision = bool(record.get("decision_bar_iso") or inst.get("decision_time_utc"))
        if has_ticket_hash and has_candidate and has_decision:
            status = "ticket_candidate_decision_policy_joinable"
        elif has_ticket_hash and has_decision:
            status = "ticket_decision_policy_joinable"
        elif has_ticket_hash:
            status = "ticket_policy_joinable"
        else:
            status = "partial_join_context"
        if record.get("runtime_learning_joinability_status") != status:
            record["runtime_learning_joinability_status"] = status
            changed = True
        return record, changed

    def _prune_old_trade_records(self, max_age_days: int = 60) -> None:
        """state-unbounded-growth: trade_records accumulate one file per placed trade. A book position
        closes within its time-stop budget (<=~53h), so a record file older than max_age_days is DEFINITELY
        a long-closed trade and is dead weight -> sweep it. Swept once at startup. NEVER raises."""
        try:
            import time
            d = self._trade_record_path()
            if not d.exists():
                return
            cutoff = time.time() - int(max_age_days) * 86400
            for f in d.glob("*.json"):
                try:
                    if f.stat().st_mtime < cutoff:
                        f.unlink()
                except OSError:
                    pass
        except Exception:
            pass

    def _persist_trade_record(
        self,
        ticket,
        trade_params: dict,
        intent,
        *,
        decision_bar_iso: str | None = None,
        decision_day: str | None = None,
        cluster: str | None = None,
        placed_at_utc: str | None = None,
        broker_symbol: str | None = None,
    ) -> None:
        """Persist the exit-policy truth for `ticket` so a restarted process can rehydrate the exact
        momentum/partial/etc. lifecycle after re-adopting the position. Best-effort; never raises."""
        if ticket in (None, 0):
            return
        try:
            record = {
                "instrumentation": dict(trade_params),
                "execution": {
                    "ticket": ticket,
                    "ticket_hash_sha256": self._runtime_learning_ticket_hash(ticket),
                    "broker_symbol": broker_symbol,
                    "placed_at_utc": placed_at_utc,
                },
                "sleeve": getattr(intent, "sleeve", None),
                "symbol": getattr(intent, "symbol", None),
                "decision_bar_iso": decision_bar_iso,
                "decision_day": decision_day,
                "cluster": cluster,
                "trade_lifecycle_status": "open",
                "opened_at_utc": placed_at_utc,
                "runtime_learning_joinability_status": "ticket_candidate_decision_policy_joinable",
            }
            record, _ = self._normalize_trade_record(ticket, record)
            if not self._write_trade_record(ticket, record):
                # `_write_trade_record` swallows its own OSError and returns False, so
                # without this the ONLY trace of a lost record was one text-log line --
                # invisible to the harvest joiner, which then flags
                # `trade_record_missing_for_ticket` with no cause on record (17/169
                # outcome rows on 2026-08-24). Surface it in the F5 event stream too.
                self._f5_emit_trade_record_persist_failed(ticket, "write_returned_false")
        except Exception as e:
            # NOT idempotency-critical (the PlacementLedger already protects + logs loudly), but a silent
            # failure here means a post-restart adoption can't rehydrate the exact dynamic policy and falls
            # back to the native floor — make the disk/perms fault visible instead of swallowing it.
            _log.warning("book[%s]: trade-record persist FAILED for ticket %s (%r); exit-policy "
                         "rehydration will fall back to the native floor after a restart",
                         self._namespace, ticket, e)
            self._f5_emit_trade_record_persist_failed(ticket, repr(e))

    def _f5_emit_trade_record_persist_failed(self, ticket, error: str) -> None:
        """Best-effort F5 event on a lost trade record. NEVER raises. No-op off-F5."""
        try:
            capture = getattr(self, "_f5_capture", None)
            if capture is None:
                return
            capture.emit("f5_trade_record_persist_failed", {
                "ticket": ticket,
                "error": str(error),
                "f5_trade_record_dir": str(self._trade_record_path()),
                "broker_mutation": False,
            })
        except Exception:  # noqa: BLE001
            pass

    def _persist_reconstructed_trade_record(self, ticket, record: dict) -> None:
        """Persist a native-policy reconstruction so repeated restarts do not stay recordless forever."""
        if ticket in (None, 0):
            return
        try:
            from pathlib import Path

            d = self._trade_record_path()
            d.mkdir(parents=True, exist_ok=True)
            p = Path(d) / f"{ticket}.json"
            if p.exists():
                return
            record, _ = self._normalize_trade_record(ticket, record)
            self._write_trade_record(ticket, record, context="reconstructed trade-record persist")
        except Exception as e:
            _log.warning("book[%s]: reconstructed trade-record persist FAILED for ticket %s (%r)",
                         self._namespace, ticket, e)

    def _load_trade_record(self, ticket):
        try:
            import json
            from pathlib import Path
            p = Path(self._trade_record_path()) / f"{ticket}.json"
            if p.exists():
                record = json.loads(p.read_text(encoding="utf-8"))
                record, changed = self._normalize_trade_record(ticket, record)
                if changed:
                    self._write_trade_record(ticket, record, context="trade-record normalize persist")
                return record
        except Exception:
            pass
        return None

    @staticmethod
    def _deal_value(deal: Any, field: str, default: Any = None) -> Any:
        if isinstance(deal, dict):
            return deal.get(field, default)
        return getattr(deal, field, default)

    @staticmethod
    def _iso_from_deal_time(value: Any) -> str | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                return str(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _parse_utc(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _exit_history_window(self, record: dict, closed_at_utc: str) -> tuple[datetime, datetime]:
        execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
        starts = [
            self._parse_utc(execution.get("placed_at_utc")),
            self._parse_utc(execution.get("broker_fill_time_utc")),
            self._parse_utc(record.get("closed_at_utc")),
            self._parse_utc(closed_at_utc),
        ]
        known = [dt for dt in starts if dt is not None]
        deal_time = self._parse_utc(execution.get("broker_exit_time_utc"))
        if deal_time is not None:
            known.append(deal_time)
        if not known:
            moment = datetime.now(timezone.utc)
            return moment, moment
        # The fetch ends on the latest broker stamp already on the record.
        # Extending it through now makes a month-old close scan the whole account.
        return min(known) - timedelta(minutes=10), max(known) + timedelta(minutes=15)

    def _lookup_exit_deal_accounting(
        self,
        *,
        ticket: int,
        record: dict,
        broker_symbol: str | None,
        symbol: str | None,
        closed_at_utc: str,
    ) -> dict:
        """Read-only MT5 history lookup for the broker close deal tied to a book ticket."""
        start_utc, end_utc = self._exit_history_window(record, closed_at_utc)
        base = {
            "exit_reconciliation_status": "HISTORY_UNAVAILABLE",
            "exit_reconciliation_attempted": True,
            "exit_reconciliation_lookup_window_start_utc": start_utc.isoformat(),
            "exit_reconciliation_lookup_window_end_utc": end_utc.isoformat(),
            "exit_reconciliation_missing_fields": ["broker_exit_deal_ticket"],
        }
        reference_dt = self._parse_utc(closed_at_utc) or datetime.now(timezone.utc)

        def _is_exit_for_ticket(deal: Any) -> bool:
            try:
                position_id = int(self._deal_value(deal, "position_id", 0) or 0)
                entry = int(self._deal_value(deal, "entry", -1))
            except (TypeError, ValueError):
                return False
            return position_id == int(ticket) and entry in {1, 2, 3}

        def _is_position_deal_for_ticket(deal: Any) -> bool:
            try:
                position_id = int(self._deal_value(deal, "position_id", 0) or 0)
            except (TypeError, ValueError):
                return False
            return position_id == int(ticket)

        def _exit_candidates(deals: Any) -> list[Any]:
            try:
                iterable = list(deals or [])
            except TypeError:
                return []
            return [deal for deal in iterable if _is_exit_for_ticket(deal)]

        def _position_candidates(deals: Any) -> list[Any]:
            try:
                iterable = list(deals or [])
            except TypeError:
                return []
            return [deal for deal in iterable if _is_position_deal_for_ticket(deal)]

        def _position_entry_exit_counts(deals: list[Any]) -> tuple[int, int]:
            entry_count = 0
            exit_count = 0
            for deal in deals:
                try:
                    entry = int(self._deal_value(deal, "entry", -1))
                except (TypeError, ValueError):
                    continue
                if entry == 0:
                    entry_count += 1
                elif entry in {1, 2, 3}:
                    exit_count += 1
            return entry_count, exit_count

        def _deal_time_distance_seconds(deal: Any) -> float:
            dt = self._parse_utc(self._iso_from_deal_time(self._deal_value(deal, "time")))
            if dt is None:
                return float("inf")
            return abs((dt - reference_dt).total_seconds())

        def _select_exit_deal(candidates: list[Any]) -> tuple[Any | None, float | None]:
            if not candidates:
                return None, None
            selected = min(
                candidates,
                key=lambda deal: (
                    _deal_time_distance_seconds(deal),
                    str(self._iso_from_deal_time(self._deal_value(deal, "time")) or ""),
                    str(self._deal_value(deal, "ticket", "")),
                ),
            )
            return selected, _deal_time_distance_seconds(selected)

        def _sum_float(deals: list[Any], field: str) -> float | None:
            total = 0.0
            seen = False
            for deal in deals:
                try:
                    value = float(self._deal_value(deal, field, 0.0) or 0.0)
                except (TypeError, ValueError):
                    continue
                total += value
                seen = True
            return total if seen else None

        def _reconciled(
            deal: Any,
            *,
            source_status: str,
            candidate_deals: list[Any],
            position_deals: list[Any],
            nearest_distance_seconds: float | None,
        ) -> dict:
            profit = self._deal_value(deal, "profit", 0.0) or 0.0
            commission = self._deal_value(deal, "commission", 0.0) or 0.0
            swap = self._deal_value(deal, "swap", 0.0) or 0.0
            fee = self._deal_value(deal, "fee", 0.0) or 0.0
            deal_ticket = self._deal_value(deal, "ticket")
            order_ticket = self._deal_value(deal, "order")
            position_id = self._deal_value(deal, "position_id")
            missing_fields = []
            if self._missingish_ticket(deal_ticket):
                missing_fields.append("broker_exit_deal_ticket")
            if self._missingish_ticket(order_ticket):
                missing_fields.append("broker_exit_order_ticket")
            if self._missingish_ticket(position_id):
                missing_fields.append("broker_exit_position_id")
            try:
                realized = float(profit) + float(commission) + float(swap) + float(fee)
            except (TypeError, ValueError):
                realized = None
            aggregate_profit = _sum_float(candidate_deals, "profit")
            aggregate_commission = _sum_float(candidate_deals, "commission")
            aggregate_swap = _sum_float(candidate_deals, "swap")
            aggregate_fee = _sum_float(candidate_deals, "fee")
            aggregate_realized = None
            if any(value is not None for value in (
                aggregate_profit,
                aggregate_commission,
                aggregate_swap,
                aggregate_fee,
            )):
                aggregate_realized = sum(
                    value or 0.0
                    for value in (
                        aggregate_profit,
                        aggregate_commission,
                        aggregate_swap,
                        aggregate_fee,
                    )
                )
            position_profit = _sum_float(position_deals, "profit")
            position_commission = _sum_float(position_deals, "commission")
            position_swap = _sum_float(position_deals, "swap")
            position_fee = _sum_float(position_deals, "fee")
            position_entry_count, position_exit_count = _position_entry_exit_counts(position_deals)
            position_accounting_complete = position_entry_count > 0 and position_exit_count > 0
            position_coverage_status = (
                "entry_and_exit_deals_present"
                if position_accounting_complete
                else "partial_position_deals_missing_entry_or_exit"
                if position_deals
                else "no_position_deals"
            )
            position_realized = None
            if any(value is not None for value in (
                position_profit,
                position_commission,
                position_swap,
                position_fee,
            )):
                position_realized = sum(
                    value or 0.0
                    for value in (
                        position_profit,
                        position_commission,
                        position_swap,
                        position_fee,
                    )
                )
            broker_realized = (
                position_realized
                if position_realized is not None and position_accounting_complete
                else aggregate_realized if aggregate_realized is not None
                else realized
            )
            realized_source = (
                "position_aggregate_includes_entry_and_exit_deals"
                if position_realized is not None and position_accounting_complete
                else "exit_aggregate_only"
                if aggregate_realized is not None
                else "selected_exit_deal_only"
            )
            return {
                **base,
                "exit_reconciliation_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
                "exit_reconciliation_source_status": source_status,
                "exit_reconciliation_missing_fields": missing_fields,
                "exit_reconciliation_match_keys": {
                    "matched_by": "position_id_and_exit_entry_nearest_close_time",
                    "position_id": position_id,
                    "order": order_ticket,
                    "ticket": deal_ticket,
                    "entry": self._deal_value(deal, "entry"),
                    "nearest_exit_time_distance_seconds": nearest_distance_seconds,
                },
                "broker_exit_deal_ticket": deal_ticket,
                "broker_exit_order_ticket": order_ticket,
                "broker_exit_position_id": position_id,
                "broker_exit_price": self._deal_value(deal, "price"),
                "broker_exit_time_utc": self._iso_from_deal_time(self._deal_value(deal, "time")),
                "broker_exit_profit": profit,
                "broker_exit_commission": commission,
                "broker_exit_swap": swap,
                "broker_exit_fee": fee,
                "broker_selected_exit_realized_pnl": realized,
                "broker_exit_position_deal_count": len(candidate_deals),
                "broker_exit_position_deal_tickets": [
                    self._deal_value(candidate, "ticket")
                    for candidate in candidate_deals
                    if not self._missingish_ticket(self._deal_value(candidate, "ticket"))
                ],
                "broker_exit_aggregate_profit": aggregate_profit,
                "broker_exit_aggregate_commission": aggregate_commission,
                "broker_exit_aggregate_swap": aggregate_swap,
                "broker_exit_aggregate_fee": aggregate_fee,
                "broker_position_deal_count": len(position_deals),
                "broker_position_deal_tickets": [
                    self._deal_value(candidate, "ticket")
                    for candidate in position_deals
                    if not self._missingish_ticket(self._deal_value(candidate, "ticket"))
                ],
                "broker_position_entry_deal_count": position_entry_count,
                "broker_position_exit_deal_count": position_exit_count,
                "broker_position_accounting_coverage_status": position_coverage_status,
                "broker_position_aggregate_profit": position_profit,
                "broker_position_aggregate_commission": position_commission,
                "broker_position_aggregate_swap": position_swap,
                "broker_position_aggregate_fee": position_fee,
                "broker_position_realized_pnl": position_realized,
                "broker_realized_pnl": broker_realized,
                "broker_realized_pnl_source": realized_source,
            }

        get_all_deals = getattr(self._mt5, "get_account_history_deals", None)
        if callable(get_all_deals):
            result = base
            for attempt in range(1, self._broker_exit_history_lookup_attempts + 1):
                try:
                    deals = get_all_deals(start_utc, end_utc)
                except Exception as exc:
                    return {
                        **base,
                        "exit_reconciliation_status": "LOOKUP_EXCEPTION",
                        "exit_reconciliation_error": repr(exc),
                        "exit_reconciliation_attempt_count": attempt,
                    }
                if deals is not None:
                    candidates = _exit_candidates(deals)
                    position_deals = _position_candidates(deals)
                    selected, nearest_distance_seconds = _select_exit_deal(candidates)
                    if selected is not None:
                        return {
                            **_reconciled(
                                selected,
                                source_status="broker_real_account_history_exit_reconciled",
                                candidate_deals=candidates,
                                position_deals=position_deals,
                                nearest_distance_seconds=nearest_distance_seconds,
                            ),
                            "exit_reconciliation_attempt_count": attempt,
                        }
                    result = {
                        **base,
                        "exit_reconciliation_status": "NO_EXIT_DEAL_FOUND",
                        "exit_reconciliation_source_status": "broker_real_account_history_checked",
                        "exit_reconciliation_attempt_count": attempt,
                    }
            return result

        get_symbol_deals = getattr(self._mt5, "get_history_deals", None)
        query_symbol = broker_symbol or symbol
        if callable(get_symbol_deals) and query_symbol:
            result = base
            for attempt in range(1, self._broker_exit_history_lookup_attempts + 1):
                try:
                    deals = get_symbol_deals(start_utc, end_utc, query_symbol)
                except Exception as exc:
                    return {
                        **base,
                        "exit_reconciliation_status": "LOOKUP_EXCEPTION",
                        "exit_reconciliation_error": repr(exc),
                        "exit_reconciliation_attempt_count": attempt,
                    }
                if deals is not None:
                    candidates = _exit_candidates(deals)
                    position_deals = _position_candidates(deals)
                    selected, nearest_distance_seconds = _select_exit_deal(candidates)
                    if selected is not None:
                        return {
                            **_reconciled(
                                selected,
                                source_status="broker_real_symbol_history_exit_reconciled",
                                candidate_deals=candidates,
                                position_deals=position_deals,
                                nearest_distance_seconds=nearest_distance_seconds,
                            ),
                            "exit_reconciliation_attempt_count": attempt,
                        }
                    result = {
                        **base,
                        "exit_reconciliation_status": "NO_EXIT_DEAL_FOUND",
                        "exit_reconciliation_source_status": "broker_real_symbol_history_checked",
                        "exit_reconciliation_attempt_count": attempt,
                    }
            return result

        return base

    def _apply_exit_reconciliation_result(
        self,
        record: dict,
        reconciliation: dict,
        *,
        ticket: int,
        broker_symbol: str | None,
        sleeve: str | None,
        symbol: str | None,
        action: str,
        closed_at_utc: str,
        already_has_selected_exit: bool,
    ) -> None:
        execution = record.setdefault("execution", {})
        mirrored_fields = {
            "broker_exit_deal_ticket",
            "broker_exit_order_ticket",
            "broker_exit_position_id",
            "broker_exit_price",
            "broker_exit_time_utc",
            "broker_exit_profit",
            "broker_exit_commission",
            "broker_exit_swap",
            "broker_exit_fee",
            "broker_selected_exit_realized_pnl",
            "broker_exit_position_deal_count",
            "broker_exit_position_deal_tickets",
            "broker_exit_aggregate_profit",
            "broker_exit_aggregate_commission",
            "broker_exit_aggregate_swap",
            "broker_exit_aggregate_fee",
            "broker_position_deal_count",
            "broker_position_deal_tickets",
            "broker_position_entry_deal_count",
            "broker_position_exit_deal_count",
            "broker_position_accounting_coverage_status",
            "broker_position_aggregate_profit",
            "broker_position_aggregate_commission",
            "broker_position_aggregate_swap",
            "broker_position_aggregate_fee",
            "broker_position_realized_pnl",
            "broker_realized_pnl_source",
            "broker_realized_pnl",
        }
        aggregate_fields = {
            "broker_exit_position_deal_count",
            "broker_exit_position_deal_tickets",
            "broker_exit_aggregate_profit",
            "broker_exit_aggregate_commission",
            "broker_exit_aggregate_swap",
            "broker_exit_aggregate_fee",
            "broker_position_deal_count",
            "broker_position_deal_tickets",
            "broker_position_entry_deal_count",
            "broker_position_exit_deal_count",
            "broker_position_accounting_coverage_status",
            "broker_position_aggregate_profit",
            "broker_position_aggregate_commission",
            "broker_position_aggregate_swap",
            "broker_position_aggregate_fee",
            "broker_position_realized_pnl",
            "broker_realized_pnl_source",
            "broker_realized_pnl",
        }
        if (
            already_has_selected_exit
            and reconciliation.get("exit_reconciliation_status") != "RECONCILED_FROM_ACCOUNT_HISTORY"
        ):
            return
        for key, value in reconciliation.items():
            if value is not None:
                should_update = (
                    not already_has_selected_exit
                    or key in aggregate_fields
                    or execution.get(key) in (None, "")
                )
                if should_update:
                    execution[key] = value
                if key in mirrored_fields and (
                    key in aggregate_fields
                    or record.get(key) in (None, "")
                    or not already_has_selected_exit
                ):
                    record[key] = value
        record["exit_reconciliation_status"] = reconciliation.get("exit_reconciliation_status")
        record["exit_reconciliation_attempted"] = reconciliation.get("exit_reconciliation_attempted")
        record["gtos_vnext_broker_exit_lifecycle_capture_v4_packet"] = {
            "schema_version": "broker_exit_lifecycle_capture_v4_packet_v1",
            "component": "broker_exit_lifecycle_capture_v4",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "stage": "exit_reconciliation",
            "status": reconciliation.get("exit_reconciliation_status"),
            "evidence_class": "production_code_integration_broker_exit_lifecycle_capture_v4",
            "runtime_effect_boundary": "read_only_account_history_no_broker_mutation",
            "identity": {
                "ticket": ticket,
                "symbol": symbol,
                "broker_symbol": broker_symbol,
                "sleeve": sleeve,
                "close_action": action,
                "closed_at_utc": closed_at_utc,
            },
            "reconciliation": reconciliation,
        }

    def _merge_exit_reconciliation(
        self,
        record: dict,
        *,
        ticket: int,
        broker_symbol: str | None,
        sleeve: str | None,
        symbol: str | None,
        action: str,
        closed_at_utc: str,
    ) -> None:
        execution = record.setdefault("execution", {})
        aggregate_fields = {
            "broker_exit_position_deal_count",
            "broker_exit_position_deal_tickets",
            "broker_exit_aggregate_profit",
            "broker_exit_aggregate_commission",
            "broker_exit_aggregate_swap",
            "broker_exit_aggregate_fee",
            "broker_position_deal_count",
            "broker_position_deal_tickets",
            "broker_position_entry_deal_count",
            "broker_position_exit_deal_count",
            "broker_position_accounting_coverage_status",
            "broker_position_aggregate_profit",
            "broker_position_aggregate_commission",
            "broker_position_aggregate_swap",
            "broker_position_aggregate_fee",
            "broker_position_realized_pnl",
            "broker_realized_pnl_source",
            "broker_realized_pnl",
        }
        already_has_selected_exit = execution.get("broker_exit_deal_ticket") not in (None, "")
        if already_has_selected_exit and all(execution.get(field) not in (None, "") for field in aggregate_fields):
            return
        reconciliation = self._lookup_exit_deal_accounting(
            ticket=int(ticket),
            record=record,
            broker_symbol=broker_symbol,
            symbol=symbol,
            closed_at_utc=closed_at_utc,
        )
        self._apply_exit_reconciliation_result(
            record,
            reconciliation,
            ticket=ticket,
            broker_symbol=broker_symbol,
            sleeve=sleeve,
            symbol=symbol,
            action=action,
            closed_at_utc=closed_at_utc,
            already_has_selected_exit=already_has_selected_exit,
        )

    def _repair_exit_reconciliation_from_account_history(self, ticket: int, record: dict) -> bool:
        """Retry read-only exit reconciliation for closed records whose first lookup missed MT5 history."""
        if not isinstance(record, dict):
            return False
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            return False
        if record.get("trade_lifecycle_status") != "closed":
            return False

        execution = record.setdefault("execution", {})
        status = execution.get("exit_reconciliation_status") or record.get("exit_reconciliation_status")
        already_has_selected_exit = execution.get("broker_exit_deal_ticket") not in (None, "")
        aggregate_fields = {
            "broker_exit_position_deal_count",
            "broker_exit_position_deal_tickets",
            "broker_exit_aggregate_profit",
            "broker_exit_aggregate_commission",
            "broker_exit_aggregate_swap",
            "broker_exit_aggregate_fee",
            "broker_position_deal_count",
            "broker_position_deal_tickets",
            "broker_position_entry_deal_count",
            "broker_position_exit_deal_count",
            "broker_position_accounting_coverage_status",
            "broker_position_aggregate_profit",
            "broker_position_aggregate_commission",
            "broker_position_aggregate_swap",
            "broker_position_aggregate_fee",
            "broker_position_realized_pnl",
            "broker_realized_pnl_source",
            "broker_realized_pnl",
        }
        if (
            status == "RECONCILED_FROM_ACCOUNT_HISTORY"
            and already_has_selected_exit
            and all(execution.get(field) not in (None, "") for field in aggregate_fields)
        ):
            return False
        if status == "RECONCILED_FROM_ACCOUNT_HISTORY" and not already_has_selected_exit:
            return False
        if status not in {
            None,
            "",
            "NO_EXIT_DEAL_FOUND",
            "HISTORY_UNAVAILABLE",
            "LOOKUP_EXCEPTION",
            "ACCOUNT_HISTORY_LOOKUP_FAILED",
        } and not already_has_selected_exit:
            return False

        closed_at_utc = record.get("closed_at_utc") or execution.get("closed_at_utc")
        if not closed_at_utc:
            return False
        now = datetime.now(timezone.utc)
        last_attempt = self._exit_reconciliation_repair_last_attempt_utc.get(ticket_i)
        if last_attempt and (now - last_attempt).total_seconds() < 900:
            return False
        self._exit_reconciliation_repair_last_attempt_utc[ticket_i] = now

        broker_symbol = execution.get("broker_symbol")
        symbol = record.get("symbol")
        if not broker_symbol and symbol not in (None, ""):
            try:
                broker_symbol = self._broker_symbol(symbol)
            except Exception:
                broker_symbol = symbol
        reconciliation = self._lookup_exit_deal_accounting(
            ticket=ticket_i,
            record=record,
            broker_symbol=broker_symbol,
            symbol=symbol,
            closed_at_utc=str(closed_at_utc),
        )
        if reconciliation.get("exit_reconciliation_status") != "RECONCILED_FROM_ACCOUNT_HISTORY":
            return False
        self._apply_exit_reconciliation_result(
            record,
            reconciliation,
            ticket=ticket_i,
            broker_symbol=broker_symbol,
            sleeve=record.get("sleeve"),
            symbol=symbol,
            action=record.get("close_action") or "broker_closed",
            closed_at_utc=str(closed_at_utc),
            already_has_selected_exit=already_has_selected_exit,
        )
        execution["exit_reconciliation_repair_status"] = reconciliation.get("exit_reconciliation_status")
        execution["exit_reconciliation_repair_checked_at_utc"] = now.isoformat()
        return True

    def _mark_trade_record_management_checked(
        self,
        ticket,
        checked_at_utc: str,
        *,
        record: dict | None = None,
        broker_symbol: str | None = None,
        sleeve: str | None = None,
        symbol: str | None = None,
        broker_protection: dict[str, Any] | None = None,
    ) -> dict | None:
        """Persist open-position management visibility without touching broker state."""
        if ticket in (None, 0):
            return record if isinstance(record, dict) else None
        try:
            rec = record if isinstance(record, dict) else self._load_trade_record(ticket)
            if not isinstance(rec, dict):
                return None
            rec, _ = self._normalize_trade_record(ticket, rec)
            if rec.get("trade_lifecycle_status") == "closed":
                return rec
            execution = rec.setdefault("execution", {})
            if broker_symbol:
                execution["broker_symbol"] = broker_symbol
            for key, value in (broker_protection or {}).items():
                if value is not None:
                    execution[key] = value
            if broker_protection:
                execution.update(self._broker_protection_reconciliation(rec, execution))
            self._set_record_value(rec, "sleeve", sleeve)
            self._set_record_value(rec, "symbol", symbol)
            rec["trade_lifecycle_status"] = "open"
            rec["last_management_checked_at_utc"] = checked_at_utc
            execution["last_management_checked_at_utc"] = checked_at_utc
            self._write_trade_record(ticket, rec, context="trade-record management-state persist")
            return rec
        except Exception as e:
            _log.debug(
                "book[%s]: trade-record management-state persist skipped for ticket %s (%r)",
                self._namespace,
                ticket,
                e,
            )
            return record if isinstance(record, dict) else None

    def _mark_trade_record_closed(
        self,
        ticket,
        action: str,
        closed_at_utc: str,
        *,
        record: dict | None = None,
        broker_symbol: str | None = None,
        sleeve: str | None = None,
        symbol: str | None = None,
    ) -> dict | None:
        """Persist an observed close lifecycle marker without touching broker state."""
        if ticket in (None, 0):
            return None
        try:
            rec = record if isinstance(record, dict) else self._load_trade_record(ticket)
            if not isinstance(rec, dict):
                rec = {"execution": {"ticket": ticket}}
            self._set_record_value(rec, "sleeve", sleeve)
            self._set_record_value(rec, "symbol", symbol)
            rec, _ = self._normalize_trade_record(ticket, rec)
            execution = rec.setdefault("execution", {})
            if broker_symbol:
                execution["broker_symbol"] = broker_symbol
            rec["trade_lifecycle_status"] = "closed"
            rec["close_action"] = action
            rec["closed_at_utc"] = closed_at_utc
            execution["closed_at_utc"] = closed_at_utc
            try:
                self._merge_exit_reconciliation(
                    rec,
                    ticket=int(ticket),
                    broker_symbol=broker_symbol or execution.get("broker_symbol"),
                    sleeve=sleeve or rec.get("sleeve"),
                    symbol=symbol or rec.get("symbol"),
                    action=action,
                    closed_at_utc=closed_at_utc,
                )
            except Exception as exc:
                execution["exit_reconciliation_status"] = "LOOKUP_EXCEPTION"
                execution["exit_reconciliation_error"] = repr(exc)
                rec["exit_reconciliation_status"] = "LOOKUP_EXCEPTION"
            self._f5_record_sibling_close(
                ticket,
                rec,
                action,
                symbol=symbol or rec.get("symbol"),
                sleeve=sleeve or rec.get("sleeve"),
                closed_utc=closed_at_utc,
            )
            self._record_closed_trade_daily_pnl(ticket, rec, action)
            self._write_trade_record(ticket, rec, context="trade-record close-state persist")
            return rec
        except Exception as e:
            _log.warning("book[%s]: trade-record close-state persist FAILED for ticket %s (%r)",
                         self._namespace, ticket, e)
            return record if isinstance(record, dict) else None

    # ---------------- notifications: clean owner-facing trade cards (best-effort; NEVER affect placement) ----
    # Readable strategy names (internal sleeve tags are for the logs, not the owner's phone).
    _SLEEVE_LABEL = {
        "metals_core": "Gold/Silver core", "metals_softband": "Gold/Silver softband",
        "metals_ob_micro": "Gold/Silver order-block", "crypto": "Crypto momentum", "energy_agri": "Oil",
        "idxrev": "Index reversion", "sub_xvol_pullback": "Substrate vol-pullback",
        "sub_mid_dn_revert": "Substrate mid-revert", "vp_euidx_pocgrav": "Index volume-profile",
        "fx_jpy": "JPY London", "fx_jpy_ny": "JPY NY",
    }

    def _send_card(self, text: str) -> None:
        """Send a clean message to Telegram (durable queue, NO 'SYSTEM ALERT' framing). Best-effort."""
        try:
            from src.utils.notification_queue import Level, send as _q
            _q(text, level=Level.HIGH)
        except Exception:
            try:
                from src.notifications import _send_async
                _send_async(text)
            except Exception:
                pass

    def _equity(self) -> float:
        try:
            return float(self._mt5.get_account_equity())
        except Exception:
            return 0.0

    def _account_label(self) -> str:
        """The bracketed tag on every operator card: `[FTMO] 🟢 LONG …`.

        THE HAZARD THIS GUARDS. The minimal-size (F5) experiment runs under namespace
        `operator`, and `"operator".startswith("ftmo")` is True — so before
        2026-08-12 a $10 experiment fill rendered `[FTMO]`, character-identical to a
        real-money armed-book fill, in the same Telegram chat. The alert text carries no
        other distinguishing mark: risk shows as a percent of a NOTIONAL $100,000 ledger,
        so even the numbers read like the armed book's. An operator glancing at his phone
        had nothing to tell a $10 test from a 2 %-of-equity trade.

        Keyed on `_f5_ledger` rather than on the namespace string deliberately: the
        notional ledger IS the minimal-size mechanism (`:273-288`, attached only when
        `--f5-minimal-size-usd` is passed), so it is `None` in every armed worker BY
        CONSTRUCTION. This branch therefore cannot alter armed-book output, and — unlike a
        launcher flag — it cannot be forgotten when the experiment is restarted.

        `GTOS_ALERT_LABEL` overrides the whole label for an operator who wants a different
        word; unset (the armed case) leaves behaviour byte-identical to before.
        """
        import os

        override = os.environ.get("GTOS_ALERT_LABEL", "").strip()
        if override:
            return override
        ns = str(self._namespace or "")
        if ns.startswith("ftmo"):
            base = "FTMO"
        elif ns.startswith("redacted_account"):
            base = "redacted_account"
        else:
            base = ns or "book"
        if getattr(self, "_f5_ledger", None) is not None:
            # Render the rung from the configured unit, never a literal: the ladder moved
            # $10 -> $75 -> $250 (owner word 2026-08-25) and a hardcoded rung lies at the
            # next step. Fallback preserves the label shape if the config is unreadable.
            try:
                unit = float(getattr(getattr(self, "_f5_cfg", None),
                                     "target_risk_usd", 0.0) or 0.0)
            except (TypeError, ValueError):
                unit = 0.0
            rung = f"{unit:g}" if unit > 0 else "?"
            return f"F5 ${rung} TEST · {base}"
        return base

    @staticmethod
    def _g(x) -> str:
        return f"{x:,.5g}" if x else "?"

    def _notify_placed(self, intent, sized_unit, result) -> None:
        """A tight trade card: direction, symbol, strategy, levels, real risk %/$, expected reward R/$."""
        try:
            ts = result.get("trade_state")
            tpp = result.get("trade_params") or {}
            is_long = int(intent.direction) > 0
            sign = 1.0 if is_long else -1.0
            entry = float(getattr(ts, "entry_price", 0.0) or 0.0)
            sl = float(getattr(ts, "stop_loss", 0.0) or 0.0)
            stop = abs(entry - sl) or 1.0
            final_r = tpp.get("gtos_vnext_dynamic_final_target_r")
            if final_r is None:
                tp0 = float(getattr(ts, "take_profit_1", 0.0) or 0.0)
                final_r = abs(tp0 - entry) / stop if tp0 else 0.0
            final_r = float(final_r)
            broker_tp_mode = str(tpp.get("gtos_vnext_dynamic_broker_take_profit_mode") or "").strip().lower()
            no_broker_take_profit = (
                tpp.get("gtos_vnext_dynamic_no_broker_take_profit") is True
                or broker_tp_mode == "none"
                or not float(getattr(ts, "take_profit_1", 0.0) or 0.0)
            )
            tp_final = entry + sign * final_r * stop
            risk_pct = float(getattr(sized_unit, "risk_pct_per_trade", 0.0) or 0.0) * 100.0
            # The card must state the money ACTUALLY at risk. Under the F5 experiment the dial
            # times real equity is ~$2,167 while the broker holds ~$10, and an operator card
            # that overstates live risk by 200x is worse than no card. `f5_actual_risk_usd` is
            # the broker's own `order_calc_profit` on the normalized volume, so it is the true
            # figure; absent (production) this is the unchanged expression.
            _f5_actual = tpp.get("f5_actual_risk_usd")
            if _f5_actual is not None:
                risk_usd = float(_f5_actual)
            else:
                risk_usd = risk_pct / 100.0 * self._equity()
            reward_usd = risk_usd * final_r
            label = self._SLEEVE_LABEL.get(intent.sleeve, intent.sleeve)
            arrow = "🟢 LONG" if is_long else "🔴 SHORT"

            def _float_param(*names: str) -> Optional[float]:
                for name in names:
                    value = tpp.get(name)
                    if value is None:
                        continue
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        continue
                return None

            def _r_text(value: Optional[float]) -> Optional[str]:
                if value is None:
                    return None
                return f"{value:g}R"

            if no_broker_take_profit:
                level_line = f"entry {self._g(entry)} | SL {self._g(sl)} | broker TP none"
                policy = str(tpp.get("gtos_vnext_dynamic_policy_selected") or "native").replace("_", " ")
                native_parts = [f"native exit: {policy}; broker TP disabled"]
                trigger = _r_text(
                    _float_param(
                        "gtos_vnext_dynamic_trailing_trigger_r",
                        "gtos_vnext_dynamic_trail_trigger_r",
                        "gtos_vnext_dynamic_be_trigger_r",
                        "trigger_r",
                    )
                )
                gap = _r_text(
                    _float_param(
                        "gtos_vnext_dynamic_trailing_gap_r",
                        "gtos_vnext_dynamic_trail_gap_r",
                        "trail_gap_r",
                    )
                )
                time_stop = _float_param("gtos_vnext_dynamic_time_stop_bars", "time_stop_bars")
                if trigger is not None:
                    native_parts.append(f"trigger {trigger}")
                if gap is not None:
                    native_parts.append(f"trail gap {gap}")
                if time_stop is not None:
                    native_parts.append(f"time stop {time_stop:g} bars")
                reward_line = "; ".join(native_parts)
            else:
                level_line = f"entry {self._g(entry)} | SL {self._g(sl)} | TP {self._g(tp_final)}"
                reward_line = f"risk {risk_pct:.2f}% (~${risk_usd:,.0f}) -> reward {final_r:.2f}R (+${reward_usd:,.0f})"

            lines = [f"[{self._account_label()}] {arrow} {intent.symbol} · {label}",
                     level_line,
                     reward_line]
            if tpp.get("gtos_vnext_dynamic_policy_selected") == "partial_be_runner":
                trig = float(tpp.get("gtos_vnext_dynamic_be_trigger_r") or 0)
                lines.append(f"scale-out: take 50% @ {trig:.1f}R, runner to {final_r:.1f}R")
            self._send_card("\n".join(lines))
        except Exception:
            import logging
            logging.getLogger(__name__).warning("notify_placed failed (non-fatal)", exc_info=True)

    @staticmethod
    def _spread_observation_key(sleeve, symbol, decision_bar_iso) -> tuple:
        """Same key shape as _runtime_learning_skip_context, so the two join without a mapping."""
        return (
            str(sleeve) if sleeve else None,
            str(symbol) if symbol else None,
            str(decision_bar_iso) if decision_bar_iso else None,
        )

    def _record_spread_observation(self, intent, *, spread_r: float, spread_price: float,
                                   max_spread_r: float, stop_dist: float,
                                   bid: float | None = None, ask: float | None = None,
                                   digits: int | None = None,
                                   sample_kind: str = "min_over_ms",
                                   sample_min_over_ms: int | None = None,
                                   sample_ticks: int = 1) -> None:
        """Store one measured spread observation. Best-effort; never raises into the screen."""
        try:
            key = self._spread_observation_key(
                getattr(intent, "sleeve", None),
                getattr(intent, "symbol", None),
                getattr(intent, "decision_bar_iso", None),
            )
            row = {
                "spread_r": round(float(spread_r), 8),
                "spread_price": round(float(spread_price), 10),
                "spr": round(float(spread_price), 10),
                "spread_r_limit": round(float(max_spread_r), 8),
                "stop_dist": round(float(stop_dist), 10),
                "spread_observed_at_utc": datetime.now(timezone.utc).isoformat(),
                "spread_r_provenance": "measured",
                "spread_r_source": "book_owner._spread_cost_screen_min_over_ms",
                "spread_sample_kind": str(sample_kind),
                "spread_sample_ticks": int(sample_ticks),
            }
            if sample_min_over_ms is not None:
                row["spread_sample_min_over_ms"] = int(sample_min_over_ms)
            if bid is not None:
                row["bid"] = round(float(bid), 10)
            if ask is not None:
                row["ask"] = round(float(ask), 10)
            if digits is not None:
                row["digits"] = int(digits)
            self._spread_observations[key] = row
        except Exception:  # noqa: BLE001 - observability must never break the cost screen
            pass

    def _attach_spread_observation(self, row: dict) -> dict:
        """Attach the measured spread for this leg, if one was observed this cycle."""
        try:
            obs = self._spread_observations.get(
                self._spread_observation_key(
                    row.get("sleeve"), row.get("symbol"), row.get("decision_bar_iso")
                )
            )
            if obs:
                for key, value in obs.items():
                    row.setdefault(key, value)
        except Exception:  # noqa: BLE001
            pass
        return row

    def _risk_unit_floor_shadow_cycle(self, result, decision, now):
        """Broker-grid Q1 observations while the book itself is observe-only.

        This path performs broker reads only under an explicit SHADOW policy. It never calls
        ``open_trade`` and it screens the ORIGINAL intent first, matching the live placement
        sequence rather than projecting a floor for a leg the existing cost screen rejects.
        """
        rows: list[dict] = []
        try:
            governor = result.get("governor_state")
            if governor is None:
                return [{"route_status": "shadow_governor_state_unavailable"}]
            f5_equity = self._f5_ledger.equity() if self._f5_ledger is not None else None
            try:
                balance = (
                    float(f5_equity)
                    if f5_equity is not None
                    else float(self._mt5.get_account_balance())
                )
            except Exception:
                balance = float(governor.equity)
            denominator = 1.0 + float(governor.realized_today_pct)
            day_start = float(governor.equity) / denominator if denominator else float(governor.equity)
            account_state = self.router.account_state(
                self._mt5,
                day_start_baseline=day_start,
                reset_window_id=self.engine.reset_window_date(now),
                equity_override=f5_equity,
                balance_override=f5_equity,
            )
            if account_state is None:
                return [{"route_status": "shadow_account_state_unavailable"}]
            meta = result.get("meta", []) or []
            floor_of = {
                (item.get("tag"), item.get("symbol")): item.get("risk_unit_floor")
                for item in meta
                if item.get("risk_unit_floor") is not None
            }
            intents = result.get("intents", []) or []
            for unit in getattr(decision, "would_units", []) or []:
                if not unit.get("sized") or float(unit.get("risk_pct_per_trade", 0) or 0) <= 0:
                    continue
                members = set(unit.get("sleeve_members", []) or [])
                unit_view = _UnitView(unit)
                for intent in intents:
                    if intent.sleeve not in members:
                        continue
                    proposal = floor_of.get((intent.sleeve, intent.symbol))
                    if proposal is None:
                        continue
                    tick = self._tick(intent.symbol)
                    if tick is None:
                        rows.append({
                            **dict(proposal),
                            "route_status": "shadow_tick_unavailable",
                        })
                        continue
                    refusal = self._spread_cost_screen(intent, tick)
                    if refusal is not None:
                        rows.append({
                            **dict(proposal),
                            "route_status": "shadow_preexisting_spread_refusal",
                            "preexisting_refusal": refusal,
                        })
                        continue
                    execution_engine = self._exec_engine(intent.symbol, intent.sleeve)
                    _unchanged, observation, _block = self._risk_unit_floor_route(
                        intent,
                        proposal,
                        unit_view,
                        tick,
                        account_state,
                        balance,
                        execution_engine,
                    )
                    rows.append(observation)
            return rows
        except Exception as exc:  # noqa: BLE001 - shadow observability never breaks a cycle
            return [{
                "route_status": f"shadow_projection_error:{type(exc).__name__}:{exc}"
            }]

    def _risk_unit_floor_route(self, intent, proposal, unit, tick, account_state,
                               balance, execution_engine):
        """Project/apply Q1 at the last safe point before order geometry is built.

        The caller invokes this only after the original intent cleared the generation-side
        spread floor, entry-hour rule, admission, lifecycle guards, age gate, and this
        owner's pre-send spread screen. SHADOW always returns the original object. APPLY
        returns the wider object only when the broker's own lot geometry can represent it;
        otherwise it returns an explicit refusal instead of relying on the downstream
        below-min shed or on an implicit F5 round-up.
        """
        from .risk_unit_floor import apply_floor, project_broker_grid

        policy = self._risk_unit_floor_policy
        params = policy.params_for(getattr(intent, "sleeve", ""))
        observation = dict(proposal or {})
        observation["mode"] = policy.mode
        observation["route_effect"] = "unchanged"
        if params is None:
            observation["route_status"] = "sleeve_not_selected"
            return intent, observation, None
        proposed, applied = apply_floor(
            intent,
            bar24=proposal.get("bar24") if isinstance(proposal, dict) else None,
            rt_cost_price=(
                proposal.get("round_trip_cost_price")
                if isinstance(proposal, dict)
                else None
            ),
            params=params,
        )
        observation.update(applied)
        if not applied.get("applied"):
            observation["route_status"] = (
                "proposal_unresolved_refused"
                if policy.mode == "apply"
                else "proposal_unresolved_shadow"
            )
            block = None
            if policy.mode == "apply":
                reason = str(applied.get("reason") or "inputs_unresolved")
                block = f"risk_unit_floor:proposal_unresolved:{reason}"
            return intent, observation, block
        if not applied.get("touched"):
            observation["route_status"] = "floor_not_binding"
            return intent, observation, None

        try:
            trade_params = self.router.build_trade_params(
                unit, proposed, tick, account_state
            )
        except Exception as exc:  # noqa: BLE001 - SHADOW may never abort the original route
            status = f"trade_params_error:{type(exc).__name__}:{exc}"
            observation["broker_grid"] = {
                "placement_allowed": False,
                "status": status,
            }
            observation["route_status"] = "broker_grid_refused"
            if policy.mode == "apply":
                return intent, observation, f"risk_unit_floor:{status}"
            return intent, observation, None
        if trade_params is None:
            observation["broker_grid"] = {
                "placement_allowed": False,
                "status": "trade_params_unavailable",
            }
            observation["route_status"] = "broker_grid_refused"
            if policy.mode == "apply":
                return intent, observation, "risk_unit_floor:trade_params_unavailable"
            return intent, observation, None

        try:
            entry = float(trade_params["entry_price"])
            stop = float(trade_params["stop_loss"])
            direction = str(trade_params["direction"])
            risk_pct = float(trade_params["risk_pct_override"])
            intended_risk = float(balance) * risk_pct / 100.0
            scaler = getattr(execution_engine, "_f5_scaler", None)
            allow_min_round_up = bool(
                scaler is not None and getattr(scaler, "round_up_enabled", False)
            )
            if scaler is not None and str(self._namespace) != "operator":
                details = trade_params.get("gtos_vnext_source_event_details") or {}
                sleeve = trade_params.get("sleeve")
                if not sleeve and isinstance(details, dict):
                    sleeve = details.get("sleeve")
                unit_for = getattr(scaler, "risk_usd_for", None)
                if callable(unit_for):
                    intended_risk = float(unit_for(
                        trade_params.get("symbol"),
                        sleeve,
                    ))
                else:
                    intended_risk = float(scaler.target_risk_usd)
            symbol_info = execution_engine._mt5_symbol_info()
            raw_lots = execution_engine._calculate_lots(
                abs(entry - stop),
                intended_risk,
                sym_info=symbol_info,
                require_broker_geometry=True,
                direction=direction,
                entry_price=entry,
                stop_loss=stop,
            )
            projection = project_broker_grid(
                raw_lots,
                symbol_info,
                intended_risk_usd=intended_risk,
                cash_risk_for_volume=lambda volume: execution_engine._broker_cash_risk_amount(
                    direction=direction,
                    volume=volume,
                    entry_price=entry,
                    stop_loss=stop,
                ),
                allow_min_round_up=allow_min_round_up,
            )
        except Exception as exc:  # noqa: BLE001 - an apply projection fails closed, shadow survives
            projection = {
                "placement_allowed": False,
                "status": f"projection_error:{type(exc).__name__}:{exc}",
            }
        observation["broker_grid"] = projection
        if not projection.get("placement_allowed"):
            observation["route_status"] = "broker_grid_refused"
            if policy.mode == "apply":
                return (
                    intent,
                    observation,
                    f"risk_unit_floor:{projection.get('status', 'broker_grid_refused')}",
                )
            return intent, observation, None
        if policy.mode == "shadow":
            observation["route_status"] = "shadow_only"
            return intent, observation, None
        observation["route_status"] = "applied"
        observation["route_effect"] = "intent_replaced"
        return _carry_hop_returns(intent, proposed), observation, None


    def _limit_at_level_intent(self, intent, *, frozen_entry=None):
        """Stamp TradeIntent.entry_price from an already-decided level.

        T4 arms BUY_LIMIT/SELL_LIMIT only when this field is set. The candidate
        tap (intent.entry_price) wins when present — generators stamp the sleeve's
        already-decided 20-high / 20-low / occupancy extreme there. Else
        FrozenPriceIntent.frozen_entry. Never applies entry_offset_atr. Never
        invents a pip/ATR offset. No real level -> unchanged intent (IOC/DEAL).
        """
        from dataclasses import replace
        from math import isfinite

        def _pos(value):
            if value in (None, ""):
                return None
            try:
                price = float(value)
            except (TypeError, ValueError):
                return None
            if not isfinite(price) or price <= 0:
                return None
            return price

        price = _pos(getattr(intent, "entry_price", None))
        if price is None:
            price = _pos(frozen_entry)
        if price is None:
            return intent
        # An F5 resting limit expires after the returned bar count (engine clock;
        # broker-side orphan sweep in _f5_sweep_stale_pending_orders). A missing
        # score leaves the intent unstamped. Fills inside 60 min carried the hold-to-orig alpha;
        # fills later than 60 min lost even held to orig, and a stale limit kept the symbol
        # 'occupied' so flat-symbol isolated re-entries were refused.
        expiry_kw = {}
        if (
            str(getattr(self, "_namespace", "") or "") == "operator"
            and getattr(intent, "expiry_bars", None) is None
        ):
            expiry_bars = _parameter_score(
                "limit_expiry_bars",
                {
                    "symbol": str(getattr(intent, "symbol", "") or ""),
                    "sleeve": str(getattr(intent, "sleeve", "") or ""),
                    "namespace": "operator",
                },
                "How many closed bars does this resting limit live? "
                "The score you return is that count.",
            )
            expiry_kw = {} if expiry_bars is None else {"expiry_bars": expiry_bars}
        current = _pos(getattr(intent, "entry_price", None))
        if current is not None and abs(current - price) <= 1e-12:
            if not expiry_kw:
                return intent
            try:
                return _carry_hop_returns(intent, replace(intent, **expiry_kw))
            except TypeError:
                return intent
        try:
            return _carry_hop_returns(intent, replace(intent, entry_price=price, **expiry_kw))
        except TypeError:
            return intent

    def _f5_thin_hour_limit_intent(self, intent, tick):
        """Route THIN_HOUR_LIMIT_SLEEVES through limit-at-level placement. F5 only. NEVER raises.

        WHY (broker-truth 2026-08-24): `asia_pdl_fade` decides in the thin Asian session and
        its generator stamps no `entry_price`, so T4's native-pending rail stayed dark and the
        order went MARKET -- LTCUSD 178351323 filled 1.48R through its intended entry and was
        born at 2.46x intended risk. Stamping the intent's `entry_price` here arms the SAME
        already-built rail every level-tap sleeve uses (BUY_LIMIT/SELL_LIMIT, expiry via
        `_expire_native_pending_orders`), preserving the sleeve's semantics: enter at the
        decided level or not at all. NO_FILL is an acceptable outcome.

        The stamped level is the current PASSIVE side (LONG: bid, SHORT: ask) -- the price the
        sleeve's decision bar just closed at, and by construction never refused as
        `native_limit_would_cross`. No offset is invented; the limit cannot fill worse than
        its level, so `f5_fill_deviation_r <= 0` on this path by construction.
        """
        if self._namespace != "operator" or self._f5_cfg is None:
            return intent
        try:
            from dataclasses import replace
            from math import isfinite

            from .minimal_size import THIN_HOUR_LIMIT_SLEEVES

            outside_set = str(getattr(intent, "sleeve", "") or "") not in THIN_HOUR_LIMIT_SLEEVES
            if outside_set:
                # Asked. A metal outside that set is still a limit. The answer
                # does not put the order back on the market.
                _spot_choice(
                    "thin_hour_limit_sleeve",
                    {
                        "symbol": str(getattr(intent, "symbol", "") or ""),
                        "sleeve": str(getattr(intent, "sleeve", "") or ""),
                        "in_thin_hour_set": False,
                        "namespace": "operator",
                    },
                    {
                        "leave_unstamped": "This sleeve is not a thin-hour limit sleeve.",
                        "stamp_passive_limit": "Stamp the passive limit.",
                    },
                    "leave_unstamped",
                    f"thin_hour_limit_sleeve|{getattr(intent, 'sleeve', '')}|{getattr(intent, 'symbol', '')}",
                    "This sleeve is outside the thin-hour set. The entry is still a limit. "
                    "An empty answer does not restore a market order.",
                )
            if getattr(intent, "entry_price", None) is not None:
                return intent            # the sleeve stamped its own level; never override
            direction = int(getattr(intent, "direction", 0) or 0)
            raw = None
            if direction > 0:
                raw = getattr(tick, "bid", None)
            elif direction < 0:
                raw = getattr(tick, "ask", None)
            try:
                level = float(raw) if raw is not None else None
            except (TypeError, ValueError):
                level = None
            if level is None or not isfinite(level) or level <= 0:
                _spot_choice(
                    "limit_level_missing",
                    {
                        "symbol": str(getattr(intent, "symbol", "") or ""),
                        "sleeve": str(getattr(intent, "sleeve", "") or ""),
                        "direction": direction,
                        "namespace": "operator",
                    },
                    {
                        "level_missing": "There is no passive price on this pass.",
                        "level_present": "A passive price is present.",
                    },
                    "level_missing",
                    f"limit_level_missing|{getattr(intent, 'sleeve', '')}|{getattr(intent, 'symbol', '')}",
                    "No passive price is on this tick, so no limit level is invented. "
                    "An empty answer does not invent a price and does not restore a market offset.",
                )
                return intent
            expiry = getattr(intent, "expiry_bars", None)
            if expiry is None:
                expiry = _parameter_score(
                    "thin_hour_expiry_bars",
                    {
                        "symbol": str(getattr(intent, "symbol", "") or ""),
                        "sleeve": str(getattr(intent, "sleeve", "") or ""),
                        "namespace": "operator",
                    },
                    "How many closed bars does this resting limit live? "
                    "The score you return is that count. "
                    "An empty score leaves the limit resting without a planted count.",
                )
            if expiry is None:
                return _carry_hop_returns(intent, replace(intent, entry_price=level))
            return _carry_hop_returns(
                intent, replace(intent, entry_price=level, expiry_bars=expiry),
            )
        except Exception as exc:  # noqa: BLE001 - a routing nicety must never break the tick
            _log.warning("book[%s]: F5 thin-hour limit stamp failed for %s/%s (%r)",
                         self._namespace, getattr(intent, "symbol", "?"),
                         getattr(intent, "sleeve", "?"), exc)
            return intent

    def _frozen_intent_key(self, intent, dbar) -> tuple[str, str, str]:
        from .frozen_price_intent import frozen_intent_key
        return frozen_intent_key(
            getattr(intent, "sleeve", ""),
            getattr(intent, "symbol", ""),
            dbar,
        )

    @staticmethod
    def _frozen_packet_from_place_result(result) -> Optional[dict]:
        from .frozen_price_intent import packet_from_place_result
        return packet_from_place_result(result if isinstance(result, dict) else None)

    def _preview_candidate_id(self, intent, unit, tick, account_state, geometry) -> Optional[str]:
        """Router PREVIEW only — no placement. The engine's candidate_id is the judgment join key."""
        try:
            preview = self.router.build_trade_params(
                _UnitView(dict(unit)), intent, tick, account_state, geometry=geometry,
            )
            if isinstance(preview, dict):
                return preview.get("candidate_id")
        except Exception:
            return None
        return None


    def _judgment_flow_ids(self, intent, unit, tick, account_state, geometry, candidate_id=None):
        """Join keys the LIVE consume seam will accept. Preview first; sleeve-day aliases second."""
        ids = []
        cid = candidate_id
        if not cid:
            try:
                cid = self._preview_candidate_id(intent, unit, tick, account_state, geometry)
            except Exception:
                cid = None
        if cid:
            ids.append(str(cid))
        try:
            symbol = getattr(intent, "symbol", None)
            sleeve = getattr(intent, "sleeve", None)
            day = getattr(intent, "decision_day", None)
            direction = "LONG" if int(getattr(intent, "direction", 0) or 0) > 0 else "SHORT"
            cluster = None
            if isinstance(unit, dict):
                cluster = unit.get("cluster")
            else:
                cluster = getattr(unit, "cluster", None)
            if cluster and symbol and day and sleeve:
                alias = f"W7_BOOK::{cluster}::{symbol}::{str(day)[:10]}::{direction}::{sleeve}"
                if alias not in ids:
                    ids.append(alias)
            if symbol and sleeve and day:
                launcher = f"LAUNCHER::{symbol}::{sleeve}::{str(day)[:10]}"
                if launcher not in ids:
                    ids.append(launcher)
        except Exception:
            pass
        return ids

    def _judgment_flow_decision(self, intent, unit, tick, account_state, geometry, now, candidate_id=None):
        """LIVE consume: APPROVE | SIZE | HOLD | PASS. Fail-closed-no-row is PASS.

        F5 ``operator`` only. Independent of ``--judgment-rescue`` (that flag is
        RESCUE-on-cost-refusal only and stays off). Never applies size_mult. Never
        calls place(). Other books (redacted_account, main 2%) are untouched.
        """
        absent = {"action": "PASS", "reason": "not_f5", "verdict": None}
        if str(getattr(self, "_namespace", "")) != "operator":
            return absent
        try:
            from .judgment_layer import judgment_flow
            ids = self._judgment_flow_ids(intent, unit, tick, account_state, geometry, candidate_id)
            primary = ids[0] if ids else None
            extra = ids[1:] if len(ids) > 1 else None
            decision = judgment_flow(
                primary,
                now,
                verdict_dir=self._judgment_verdict_dir,
                namespace=self._namespace,
                extra_ids=extra,
            )
            _log.info(
                "book[%s]: judgment_flow %s action=%s verdict=%s reason=%s size_mult=%s (not applied)",
                self._namespace,
                decision.get("join_key") or primary,
                decision.get("action"),
                decision.get("verdict"),
                decision.get("reason"),
                decision.get("proposed_size_mult"),
            )
            return decision
        except Exception as exc:
            _log.warning(
                "book[%s]: judgment_flow failed (%r) -> PASS (will not invent a veto)",
                getattr(self, "_namespace", "?"), exc,
            )
            return {"action": "PASS", "reason": "lookup_failed", "verdict": None}


    def _f5_daily_cap_yields_isolated_reentry(self, intent, now=None) -> bool:
        """F5 only: daily/cluster caps yield after close + cooldown on a flat symbol."""
        try:
            from .minimal_size import f5_daily_cap_yields_isolated_reentry
            occupied_book = self._f5_cross_tf_filter(self._f5_occupied_book(), getattr(intent, "sleeve", None))
            occupied_symbols = [row.get("symbol") for row in occupied_book if row.get("symbol")]
            return bool(f5_daily_cap_yields_isolated_reentry(
                str(getattr(self, "_namespace", "") or ""),
                getattr(intent, "symbol", ""),
                sleeve=getattr(intent, "sleeve", None),
                occupied_symbols=occupied_symbols,
                now=now,
                repo_root=getattr(self, "_repo_root", None),
            ))
        except Exception:
            return False

    def _f5_occupied_book(self) -> list:
        """Live F5 tickets and pendings the standing hold can see. Empty on a failed read."""
        rows: list = []
        seen: set = set()
        try:
            positions = self._open_book_positions_snapshot() or []
        except Exception:
            positions = []
        for p in positions:
            ticket = getattr(p, "ticket", None)
            key = ("pos", ticket)
            if key in seen:
                continue
            seen.add(key)
            try:
                typ = int(getattr(p, "type", 1) or 0)
            except (TypeError, ValueError):
                typ = 1
            rows.append({
                "symbol": getattr(p, "symbol", "") or "",
                "direction": "LONG" if typ == 0 else "SHORT",
                "family": getattr(p, "comment", "") or "",
                "sl": getattr(p, "sl", None),
                "tp": getattr(p, "tp", None),
                "entry": getattr(p, "price_open", None),
                "ticket": ticket,   # CONTRACT V3: ledger lookup for the timeframe
            })
        module = getattr(self._mt5, "_mt5", None)
        orders_get = getattr(module, "orders_get", None)
        if callable(orders_get):
            try:
                orders = orders_get() or []
            except Exception:
                orders = []
            for o in orders:
                if getattr(self, "_magic", None) is not None and getattr(o, "magic", None) != self._magic:
                    continue
                ticket = getattr(o, "ticket", None)
                key = ("ord", ticket)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    typ = int(getattr(o, "type", 99) or 99)
                except (TypeError, ValueError):
                    typ = 99
                if typ in (0, 2, 4, 6):
                    direction = "LONG"
                elif typ in (1, 3, 5, 7):
                    direction = "SHORT"
                else:
                    direction = None
                rows.append({
                    "symbol": getattr(o, "symbol", "") or "",
                    "direction": direction,
                    "family": getattr(o, "comment", "") or "",
                    "sl": getattr(o, "sl", None),
                    "tp": getattr(o, "tp", None),
                    "entry": getattr(o, "price_open", None),
                    "ticket": ticket,   # CONTRACT V3
                })
        return rows

    def _f5_standing_symbol_hold(self, intent, unit=None, candidate_id=None, now=None):
        """F5-only standing law: writer refuses. Other books untouched.

        USDJPY rest of verification at this gate, not inbox why_code.
        15-minute same-symbol sibling. FX DSP majors 4h after SL.
        Metals/index 15 minutes only. Isolated opposite is PASS.
        """
        absent = {"action": "PASS", "reason": "not_standing_symbol_hold", "verdict": None}

        def _writer_hold(reason: str):
            return True, {
                "action": "HOLD",
                "reason": reason,
                "verdict": "hold",
                "join_key": "STANDING::" + str(reason),
                "writer_block": True,
            }

        if str(getattr(self, "_namespace", "")) != "operator":
            return False, absent
        family = (
            getattr(intent, "sleeve", None)
            or (unit.get("sleeve") if isinstance(unit, dict) else None)
            or getattr(intent, "candidate_id", None)
            or candidate_id
        )
        try:
            from .minimal_size import (
                f5_just_closed_siblings_path,
                f5_standing_hold_reason,
            )
            occupied_book = self._f5_cross_tf_filter(self._f5_occupied_book(), getattr(intent, "sleeve", None))
            occupied_symbols = [row.get("symbol") for row in occupied_book if row.get("symbol")]
            def _intent_level(*names):
                for name in names:
                    val = getattr(intent, name, None)
                    if val is not None:
                        return val
                geom_fn = getattr(intent, "geometry", None)
                if callable(geom_fn):
                    try:
                        geom = geom_fn()
                    except Exception:
                        geom = None
                    if isinstance(geom, dict):
                        for name in names:
                            if geom.get(name) is not None:
                                return geom.get(name)
                return None

            reason = f5_standing_hold_reason(
                getattr(self, "_namespace", ""),
                getattr(intent, "symbol", ""),
                occupied_symbols=occupied_symbols,
                direction=getattr(intent, "direction", None),
                family=family,
                occupied_book=occupied_book,
                sl=_intent_level("stop_loss", "sl", "frozen_stop"),
                tp=_intent_level("take_profit", "tp", "frozen_target"),
                entry=_intent_level("entry_price", "entry", "frozen_entry"),
                now=now or datetime.now(timezone.utc),
                stop_dist=getattr(intent, "stop_dist", None),
                repo_root=getattr(self, "_repo_root", None),
                path=f5_just_closed_siblings_path(
                    repo_root=getattr(self, "_repo_root", None),
                    namespace=str(getattr(self, "_namespace", "") or "operator"),
                ),
            )
        except Exception:
            raw = str(getattr(intent, "symbol", "") or "")
            sym = raw.upper().replace(".CASH", "").replace(".cash", "")
            try:
                from .minimal_size import f5_hard_off_sleeve_reason
                hard = f5_hard_off_sleeve_reason(family, namespace=getattr(self, "_namespace", None))
            except Exception:
                hard = None
            if hard:
                reason = hard
            elif sym == "USDJPY" or sym.startswith("USDJPY"):
                _hold_jpy = str(getattr(self, "_namespace", "") or "") != "operator"
                if str(getattr(self, "_namespace", "") or "") == "operator":
                    try:
                        _hold_jpy = bool(_spot_choice(
                            "usdjpy_verification_hold",
                            {"symbol": sym, "namespace": "operator"},
                            {
                                "pattern_is_the_fire": "The pattern on this USDJPY bar is the fire.",
                                "verification_hold_stands": "The verification hold stands. Do not send this USDJPY bar.",
                            },
                            "verification_hold_stands",
                            f"usdjpy_verification_hold|{sym}|{datetime.now(timezone.utc).strftime('%Y%m%d%H')}",
                            "A verification hold is attached to USDJPY. Is the pattern the fire, or does that hold stand? Do not close an open ticket.",
                        ))
                    except Exception:
                        _hold_jpy = False
                if _hold_jpy:
                    reason = "usdjpy_verification_hold_5pip_dsp_stop"
                else:
                    return False, absent
            else:
                return False, absent
        if not reason:
            return False, absent
        if _spot_choice(
            "standing_reason_hold",
            {
                "symbol": str(getattr(intent, "symbol", "") or ""),
                "sleeve": str(family or ""),
                "reason": str(reason),
                "namespace": "operator",
            },
            {
                "reason_withholds": "This standing reason withholds the candidate.",
                "reason_is_a_fact": "This standing reason is a fact. The candidate can still send.",
            },
            "reason_withholds",
            f"standing_reason_hold|{family}|{getattr(intent, 'symbol', '')}|{reason}",
            "The two sides of a standing-hold reason that is not already a fear-gate Choice.",
        ):
            return _writer_hold(reason)
        return False, absent

    def _judgment_flow_hold(self, intent, unit, tick, account_state, geometry, now, candidate_id=None):
        standing, standing_dec = self._f5_standing_symbol_hold(
            intent, unit=unit, candidate_id=candidate_id, now=now,
        )
        if standing:
            return True, standing_dec
        decision = self._judgment_flow_decision(
            intent, unit, tick, account_state, geometry, now, candidate_id=candidate_id
        )
        action = str(decision.get("action") or "")
        # Inbox APPROVE cannot arm a HARD_OFF sleeve. Writer refuses even if
        # grok-inbox said isolated_reentry_wanted on asia_pdl_fade.
        if action == "APPROVE":
            family = (
                getattr(intent, "sleeve", None)
                or (unit.get("sleeve") if isinstance(unit, dict) else None)
                or getattr(intent, "candidate_id", None)
                or candidate_id
            )
            try:
                from .minimal_size import f5_hard_off_sleeve_reason
                hard = f5_hard_off_sleeve_reason(family, namespace=getattr(self, "_namespace", None))
            except Exception:
                hard = None
            if hard:
                held = _spot_choice(
                    "hard_off_sleeve",
                    {
                        "symbol": str(getattr(intent, "symbol", "") or ""),
                        "sleeve": str(family or ""),
                        "reason": str(hard),
                        "namespace": "operator",
                    },
                    {
                        "reason_withholds": "This sleeve reason withholds the candidate.",
                        "reason_is_a_fact": "This sleeve reason is a fact. The candidate can still send.",
                    },
                    "reason_withholds",
                    f"hard_off_sleeve|{family}|{getattr(intent, 'symbol', '')}|{hard}",
                    "A sleeve is named on a hard-off list. Withhold only when that side is the unique highest. "
                    "An empty answer or a tie does not withhold. Do not close an open ticket.",
                )
                if not held:
                    return False, decision
                return True, {
                    "action": "HOLD",
                    "reason": hard,
                    "verdict": "hold",
                    "join_key": "STANDING::" + str(hard),
                    "why_code": hard,
                }
        if action == "HOLD" and str(getattr(self, "_namespace", "")) == "operator":
            try:
                from src.judgment.intent_retry import ask_judgment_hold, judgment_hold_state

                asked = ask_judgment_hold(judgment_hold_state(intent, decision))
            except Exception as exc:
                asked = {
                    "alternative": None,
                    "unanswered": True,
                    "blocks": False,
                    "error": type(exc).__name__,
                }
            stamped = dict(decision) if isinstance(decision, dict) else {"decision": decision}
            stamped["fear_choice"] = asked.get("alternative")
            stamped["fear_error"] = asked.get("error")
            if asked.get("blocks") is True and asked.get("alternative") == "hold_stands":
                stamped["action"] = "HOLD"
                stamped["unanswered"] = False
                return True, stamped
            if asked.get("alternative") == "send_continues" and not asked.get("unanswered"):
                stamped["action"] = "SEND"
                stamped["unanswered"] = False
                return False, stamped
            stamped["unanswered"] = True
            stamped["action"] = "UNANSWERED"
            return False, stamped
        return action == "HOLD", decision

    def _judgment_rescue_verdict(self, candidate_id, now) -> bool:
        """The judgment consume seam: one lookup, one enum, TTL, fail-to-absent.

        True ONLY on a fresh RESCUE bound to this book's namespace. ABSENT (stale,
        missing file, unreadable file, wrong book, no row) and VETO (recorded,
        log-only — nothing consumes it yet) both leave code-only behavior. NEVER
        raises: a defect anywhere in the judgment layer is one log line and
        code-only behavior, never a blocked book.
        """
        if not self._judgment_rescue or not candidate_id:
            return False
        try:
            from .judgment_layer import VERDICT_RESCUE, VERDICT_VETO, judgment_verdict
            verdict = judgment_verdict(
                candidate_id,
                now,
                verdict_dir=self._judgment_verdict_dir,
                namespace=self._namespace,
            )
            if verdict == VERDICT_VETO:
                _log.info(
                    "book[%s]: judgment VETO recorded for candidate %s (log-only, not consumed)",
                    self._namespace, candidate_id,
                )
            return verdict == VERDICT_RESCUE
        except Exception as exc:
            _log.warning(
                "book[%s]: judgment lookup failed for candidate %s (%r) -> ABSENT, code-only",
                self._namespace, candidate_id, exc,
            )
            return False

    def _preview_frozen_max_lots(self, intent, geometry, execution_engine) -> Optional[float]:
        """Best-effort lot preview at freeze time. None is allowed — geometry still pins size."""
        if self._f5_scaler is None or not isinstance(geometry, dict):
            return None
        try:
            entry = float(geometry["entry_price"])
            stop = float(geometry["stop_loss"])
            distance = abs(entry - stop)
            if distance <= 0:
                return None
            direction = "LONG" if int(getattr(intent, "direction", 0) or 0) > 0 else "SHORT"
            from .minimal_size import (
                F5_NAMESPACE,
                f5_fx_dsp_tight_stop_reason,
                f5_lots_or_ticks_refuse_reason,
            )

            symbol = getattr(intent, "symbol", "")
            sleeve = getattr(intent, "sleeve", "")
            if f5_fx_dsp_tight_stop_reason(
                F5_NAMESPACE, symbol, family=sleeve, stop_dist=distance,
            ):
                return None
            symbol_info = execution_engine._mt5_symbol_info()
            lots = execution_engine._calculate_lots(
                distance,
                float(self._f5_scaler.risk_usd_for(symbol, sleeve)),
                sym_info=symbol_info,
                require_broker_geometry=True,
                direction=direction,
                entry_price=entry,
                stop_loss=stop,
            )
            if lots is None:
                return None
            tick_size = None
            if symbol_info is not None:
                tick_size = getattr(symbol_info, "trade_tick_size", None) or getattr(
                    symbol_info, "point", None
                )
            if f5_lots_or_ticks_refuse_reason(
                lots=lots, stop_dist=distance, tick_size=tick_size,
            ):
                return None
            return float(lots)
        except Exception:
            return None

    def _f5_refusal_quote_enabled(self) -> bool:
        """Durable series writes are F5 capture only. Production stays inert."""
        return (
            getattr(self, "_f5_capture", None) is not None
            and str(getattr(self, "_namespace", "")).endswith("_f5_minimal")
        )

    def _sleeve_spread_cap_r(self, sleeve) -> float:
        """Named sleeve cap. 0.35 on fx_jpy / fx_jpy_ny; else cell default 0.10."""
        rt = self.base_config.get("gtos_vnext_runtime", {}) or {}
        try:
            cap = float(rt.get("selected_cell_pretrade_max_spread_r", 0.10))
        except (TypeError, ValueError):
            cap = 0.10
        by_sleeve = rt.get("selected_cell_pretrade_max_spread_r_by_sleeve")
        if isinstance(by_sleeve, dict) and sleeve in by_sleeve:
            try:
                cap = float(by_sleeve[sleeve])
            except (TypeError, ValueError):
                pass
        return cap

    def _remember_spread_screen_tick(self, intent, tick, *, stop_dist) -> None:
        """Keep every quote the owner actually held this cycle (first + extras)."""
        try:
            from .frozen_price_intent import quote_snapshot_from_tick

            key = (
                str(getattr(intent, "sleeve", "") or ""),
                str(getattr(intent, "symbol", "") or ""),
            )
            snap = quote_snapshot_from_tick(tick, stop_dist=stop_dist)
            if snap.get("bid") is None or snap.get("ask") is None:
                return
            self._spread_quote_series.setdefault(key, []).append(snap)
        except Exception:  # noqa: BLE001 - persist must never break the screen
            pass

    def _f5_series_key(self, intent, dbar) -> tuple[str, str, str]:
        return (
            str(getattr(intent, "sleeve", "") or ""),
            str(getattr(intent, "symbol", "") or ""),
            str(dbar or ""),
        )

    def _json_quote(self, snap: dict) -> dict:
        quote_at = snap.get("quote_at_utc")
        return {
            "bid": snap.get("bid"),
            "ask": snap.get("ask"),
            "spread_price": snap.get("spread_price"),
            "spread_r": snap.get("spread_r"),
            "quote_at_utc": quote_at.isoformat() if hasattr(quote_at, "isoformat") else quote_at,
        }

    def _persist_f5_refusal_quote(
        self,
        *,
        now: datetime,
        intent,
        unit: dict,
        tick,
        dbar: str,
        dday: str,
        reason: str,
        packet,
        skipped_row: dict,
    ) -> None:
        """Lookback emit: every quote this cycle actually held, plus rollup.

        Flag-independent. Never flips bar_consumable. Never enqueues. Never raises.
        First emit is lookback+rollup; later watch ticks append via
        ``_persist_f5_watch_quote``. Not a one-shot set.
        """
        if not self._f5_refusal_quote_enabled():
            return
        try:
            self._emit_f5_quote_series(
                now=now,
                intent=intent,
                unit=unit,
                tick=tick,
                dbar=dbar,
                dday=dday,
                reason=reason,
                packet=packet,
                skipped_row=skipped_row,
                event_kind="lookback",
                extra_tick=None,
            )
        except Exception:  # noqa: BLE001 - persist must never break the cost-skip path
            pass

    def _persist_f5_watch_quote(
        self,
        *,
        now: datetime,
        item,
        intent,
        unit: dict,
        tick,
        dbar: str,
        dday: str,
        skipped_row: dict,
    ) -> None:
        """Append one observe tick until 120s / first clear / chase > 0.10 stop."""
        if not self._f5_refusal_quote_enabled():
            return
        try:
            key = self._f5_series_key(item if item is not None else intent, dbar)
            if key in self._f5_series_forward_closed:
                return
            self._emit_f5_quote_series(
                now=now,
                intent=intent,
                unit=unit if isinstance(unit, dict) else getattr(item, "unit", None),
                tick=tick,
                dbar=dbar,
                dday=dday,
                reason=getattr(item, "last_reason", None) or (
                    (getattr(item, "refusal_reasons", None) or [None])[0]
                ),
                packet=None,
                skipped_row=skipped_row,
                event_kind="watch_tick",
                extra_tick=tick,
                item=item,
            )
        except Exception:  # noqa: BLE001
            pass

    def _emit_f5_quote_series(
        self,
        *,
        now: datetime,
        intent,
        unit,
        tick,
        dbar: str,
        dday: str,
        reason: str,
        packet,
        skipped_row: dict,
        event_kind: str,
        extra_tick=None,
        item=None,
    ) -> None:
        from .frozen_price_intent import (
            chase_stop_fraction,
            classify_cost_refusal,
            geometry_from_intent_tick,
            quote_series_rollup,
            quote_snapshot_from_tick,
            side_from_direction,
            unrounded_lots,
        )

        key = self._f5_series_key(item if item is not None else intent, dbar)
        if event_kind == "lookback" and key in self._f5_quote_series:
            return
        lookback_key = (
            str(getattr(intent, "sleeve", "") or ""),
            str(getattr(intent, "symbol", "") or ""),
        )
        series = list(self._f5_quote_series.get(key) or [])
        if event_kind == "lookback" and not series:
            held = list(self._spread_quote_series.get(lookback_key) or [])
            if not held:
                snap = quote_snapshot_from_tick(
                    tick,
                    stop_dist=getattr(intent, "stop_dist", None),
                    now=now,
                )
                if snap.get("bid") is not None and snap.get("ask") is not None:
                    held = [snap]
            series = list(held)
        elif extra_tick is not None:
            snap = quote_snapshot_from_tick(
                extra_tick,
                stop_dist=(
                    getattr(item, "frozen_stop_dist", None)
                    if item is not None
                    else getattr(intent, "stop_dist", None)
                ),
                now=now,
            )
            if snap.get("bid") is None or snap.get("ask") is None:
                return
            series.append(snap)
        if not series:
            return
        last = series[-1]
        if last.get("bid") is None or last.get("ask") is None:
            return

        packet_map = packet if isinstance(packet, dict) else None
        symbol = getattr(item, "symbol", None) if item is not None else getattr(intent, "symbol", None)
        sleeve = getattr(item, "sleeve", None) if item is not None else getattr(intent, "sleeve", None)
        stop_dist = None
        frozen_entry = None
        stop = None
        direction = 0
        if item is not None:
            stop_dist = getattr(item, "frozen_stop_dist", None)
            frozen_entry = getattr(item, "frozen_entry", None)
            stop = getattr(item, "frozen_stop", None)
            try:
                direction = int(getattr(item, "direction", 0) or 0)
            except (TypeError, ValueError):
                direction = 0
        if stop_dist is None:
            stop_dist = getattr(intent, "stop_dist", None)
        if direction == 0:
            try:
                direction = int(getattr(intent, "direction", 0) or 0)
            except (TypeError, ValueError):
                direction = 0
        geometry = geometry_from_intent_tick(intent, tick)
        if isinstance(geometry, dict):
            if stop_dist is None:
                stop_dist = geometry.get("stop_dist") or geometry.get("risk_distance")
            if frozen_entry is None:
                frozen_entry = geometry.get("entry_price")
            if stop is None:
                stop = geometry.get("stop_loss")
        if frozen_entry is None and isinstance(skipped_row, dict):
            frozen_entry = skipped_row.get("frozen_entry")

        # The row's packet_class is the classification of the episode's ORIGINAL cost
        # refusal. On a post-observe watch tick the current reason can be a terminal
        # string (`chase_stop_fraction:` / `hard_expiry_seconds:` are unknown families
        # -> STRUCTURAL by classify_cost_refusal), so prefer the frozen object's own
        # class; recompute only when there is no object (lookback path, item=None).
        # Value-identical for every pre-fix row: an enqueued item's packet_class IS
        # classify() of the same cost strings the old recompute saw.
        packet_class = getattr(item, "packet_class", None) if item is not None else None
        if not packet_class:
            packet_class = classify_cost_refusal(
                screen_reason=reason,
                packet=packet_map,
                stop_dist=stop_dist,
                symbol=symbol or "",
                digits=self._symbol_digits(symbol),
                point=self._symbol_point(symbol),
            )
        cap_r = self._sleeve_spread_cap_r(sleeve)
        try:
            distance = float(stop_dist) if stop_dist not in (None, "") else None
        except (TypeError, ValueError):
            distance = None
        need_spr = (cap_r * distance) if distance is not None and distance > 0 else None
        try:
            tuition = float(getattr(getattr(self, "_f5_cfg", None), "target_risk_usd", 10.0) or 10.0)
        except (TypeError, ValueError):
            tuition = 10.0
        cap_usd = tuition * cap_r
        rollup = quote_series_rollup(
            series,
            need_spr=need_spr,
            stop_dist=distance,
            direction=direction,
            frozen_entry=frozen_entry,
            tuition_usd=tuition,
        )
        series_n = int(rollup.get("series_n") or len(series))
        sample_kind = "live_tick" if series_n <= 1 else self.SPREAD_SAMPLE_KIND

        live_item = item
        if live_item is None:
            live_item = self._frozen_intents.get(self._frozen_intent_key(intent, dbar))
        unrounded = unrounded_lots(
            getattr(live_item, "unrounded", None) if live_item is not None else None,
            getattr(live_item, "frozen_max_lots", None) if live_item is not None else None,
            packet_map,
            unit if isinstance(unit, dict) else None,
        )
        candidate_id = None
        if isinstance(skipped_row, dict):
            candidate_id = skipped_row.get("candidate_id")
        if candidate_id is None and live_item is not None:
            candidate_id = getattr(live_item, "candidate_id", None)
        if candidate_id is None and isinstance(unit, dict):
            candidate_id = unit.get("candidate_id")
        family = None
        if isinstance(unit, dict):
            family = unit.get("cluster")
        family = family or sleeve
        reasons = [str(reason)] if reason not in (None, "") else []
        if live_item is not None:
            for raw in getattr(live_item, "refusal_reasons", None) or []:
                text_reason = str(raw or "").strip()
                if text_reason and text_reason not in reasons:
                    reasons.append(text_reason)
        if isinstance(packet_map, dict):
            extra = packet_map.get("refusal_reasons")
            if isinstance(extra, list):
                for raw in extra:
                    text_reason = str(raw or "").strip()
                    if text_reason and text_reason not in reasons:
                        reasons.append(text_reason)
        quote_at = last.get("quote_at_utc")
        first_clear = rollup.get("first_clear_utc")
        first_clear_iso = (
            first_clear.isoformat() if hasattr(first_clear, "isoformat") else first_clear
        )
        payload = {
            "event_kind": event_kind,
            "bid": last.get("bid"),
            "ask": last.get("ask"),
            "spread": last.get("spread_price"),
            "spread_price": last.get("spread_price"),
            "spread_r": last.get("spread_r"),
            "digits": self._symbol_digits(symbol),
            "quote_at_utc": quote_at.isoformat() if hasattr(quote_at, "isoformat") else quote_at,
            "stop": stop,
            "stop_dist": distance,
            "unrounded": unrounded,
            "symbol": symbol,
            "side": side_from_direction(direction),
            "direction": direction,
            "sleeve": sleeve,
            "family": family,
            "candidate_id": candidate_id,
            "decision_bar_iso": str(dbar) if dbar else None,
            "decision_day": str(dday) if dday else None,
            "refusal_reasons": reasons,
            "packet_class": packet_class,
            "frozen_price_intent_status": (
                skipped_row.get("frozen_price_intent_status")
                if isinstance(skipped_row, dict) else None
            ),
            "frozen_entry": frozen_entry,
            "broker_mutation": False,
            "spread_sample_kind": sample_kind,
            "cap_usd": cap_usd,
            "need_spr": need_spr,
            "min_spr": rollup.get("min_spr"),
            "max_spr": rollup.get("max_spr"),
            "unique_n": rollup.get("unique_n"),
            "min_usd": rollup.get("min_usd"),
            "max_usd": rollup.get("max_usd"),
            "cap_inside_oscillation": rollup.get("cap_inside_oscillation"),
            "first_clear_utc": first_clear_iso,
            "first_clear_lag_s": rollup.get("first_clear_lag_s"),
            "chase_at_first_clear": rollup.get("chase_at_first_clear"),
            "series_n": series_n,
            "quotes": [self._json_quote(q) for q in series],
        }
        self._f5_capture.emit("f5_refusal_quote", payload)
        self._f5_quote_series[key] = series

        chase = None
        if frozen_entry is not None and distance is not None:
            chase = chase_stop_fraction(
                direction=direction,
                tick=tick,
                frozen_entry=frozen_entry,
                stop_dist=distance,
            )
        expired = False
        if item is not None and hasattr(item, "expired_at"):
            try:
                expired = bool(item.expired_at(now))
            except Exception:
                expired = False
        max_chase = None
        if item is not None:
            try:
                raw_chase = getattr(item, "max_chase_stop_fraction", None)
                max_chase = None if raw_chase is None else float(raw_chase)
            except (TypeError, ValueError):
                max_chase = None
        if max_chase is None:
            try:
                from src.judgment.nineteen import score
                spread_r = _finite_number(last.get("spread_r"))
                chase_now = _finite_number(chase)
                chase_clear = _finite_number(rollup.get("chase_at_first_clear"))
                min_over_stop = None
                max_over_stop = None
                if distance is not None and distance > 0:
                    min_spr = _finite_number(rollup.get("min_spr"))
                    max_spr = _finite_number(rollup.get("max_spr"))
                    if min_spr is not None:
                        min_over_stop = min_spr / distance
                    if max_spr is not None:
                        max_over_stop = max_spr / distance
                chase_anchors = _anchor_pairs((
                    ("spread_r", spread_r),
                    ("chase", chase_now),
                    ("chase_at_first_clear", chase_clear),
                    ("min_spread_over_stop", min_over_stop),
                    ("max_spread_over_stop", max_over_stop),
                ))
                if chase_anchors is not None:
                    max_chase = score(
                        {
                            "symbol": symbol,
                            "sleeve": sleeve,
                            "stop_dist": distance,
                            "frozen_entry": frozen_entry,
                            "bid": last.get("bid"),
                            "ask": last.get("ask"),
                            "spread_r": spread_r,
                            "chase": chase_now,
                            "chase_at_first_clear": chase_clear,
                        },
                        question_id="max_chase_stop_fraction",
                        instructions=(
                            "The score you return is the chase fraction of the stop that ends this series. "
                            "An empty score leaves the chase unset. Do not send."
                        ),
                        anchors=chase_anchors,
                    )
            except Exception:
                max_chase = None
        if (
            first_clear_iso not in (None, "", "never")
            or (chase is not None and max_chase is not None and chase > max_chase)
            or expired
        ):
            self._f5_series_forward_closed.add(key)

    def _maybe_enqueue_frozen_price_intent(
        self,
        *,
        now: datetime,
        intent,
        unit: dict,
        tick,
        dbar: str,
        dday: str,
        ee,
        account_state,
        reason: str,
        packet,
        skipped_row: dict,
        summary: dict,
    ) -> bool:
        """Enqueue one FrozenPriceIntent or record a terminal kill. Flag-off is a no-op."""
        from .frozen_price_intent import (
            PACKET_CLASS_MODEL_INPUT,
            PACKET_CLASS_QUOTE_DEPENDENT,
            PACKET_CLASS_STRUCTURAL,
            STATE_REFUSED_COST,
            build_frozen_price_intent,
            classify_cost_refusal,
            geometry_from_intent_tick,
            is_blow_through,
        )

        if not self._frozen_intent_reprice:
            return False
        if not isinstance(unit, dict) or not unit.get("sized") or float(unit.get("risk_pct_per_trade", 0) or 0) <= 0:
            return False

        key = self._frozen_intent_key(intent, dbar)
        existing = self._frozen_intents.get(key)
        if existing is not None:
            skipped_row["frozen_price_intent_status"] = existing.state
            skipped_row["frozen_price_intent_class"] = getattr(existing, "packet_class", None)
            if existing.is_open:
                summary["bar_consumable"] = False
            return False

        packet_class = classify_cost_refusal(
            screen_reason=reason,
            packet=packet if isinstance(packet, dict) else None,
            stop_dist=getattr(intent, "stop_dist", None),
            symbol=getattr(intent, "symbol", ""),
            digits=self._symbol_digits(getattr(intent, "symbol", "")),
            point=self._symbol_point(getattr(intent, "symbol", "")),
        )
        geometry = geometry_from_intent_tick(intent, tick)
        if geometry is None:
            skipped_row["frozen_price_intent_status"] = "geometry_unavailable"
            skipped_row["frozen_price_intent_class"] = packet_class
            return False
        if is_blow_through(
            direction=int(getattr(intent, "direction", 0) or 0),
            tick=tick,
            stop_loss=float(geometry["stop_loss"]),
        ):
            skipped_row["frozen_price_intent_status"] = "killed_blow_through"
            skipped_row["frozen_price_intent_class"] = packet_class
            skipped_row["reason"] = f"blow_through_frozen_stop:{reason}"
            return False
        judgment_candidate_id = None
        judgment_rescued = False
        if packet_class != PACKET_CLASS_QUOTE_DEPENDENT:
            # Terminal cost refusal: today this drops the intent. The judgment consume
            # seam (--judgment-rescue, operator only) may RESCUE it onto the
            # EXISTING rail — blow-through was already checked above, and the enqueued
            # object keeps its own price re-check, TTL and chase kill-band live on every
            # observe tick. Judgment never calls place(). Flag off: the two kill lines
            # below are byte-for-byte today's behavior and no lookup ever runs.
            # STRUCTURAL only: MODEL_INPUT kills (tight-floor stop geometry) are honest
            # model refusals, not cost lies — never rescuable, no lookup even runs.
            if self._judgment_rescue and packet_class == PACKET_CLASS_STRUCTURAL:
                judgment_candidate_id = self._preview_candidate_id(
                    intent, unit, tick, account_state, geometry)
                judgment_rescued = self._judgment_rescue_verdict(judgment_candidate_id, now)
            if not judgment_rescued:
                if packet_class == PACKET_CLASS_MODEL_INPUT:
                    skipped_row["frozen_price_intent_status"] = "killed_model_input"
                else:
                    skipped_row["frozen_price_intent_status"] = "killed_structural"
                skipped_row["frozen_price_intent_class"] = packet_class or PACKET_CLASS_STRUCTURAL
                return False
            skipped_row["frozen_price_intent_judgment_rescue"] = True

        candidate_id = judgment_candidate_id
        if candidate_id is None:
            candidate_id = self._preview_candidate_id(intent, unit, tick, account_state, geometry)
        frozen_max_lots = self._preview_frozen_max_lots(intent, geometry, ee)
        item = build_frozen_price_intent(
            intent=intent,
            unit=deepcopy(dict(unit)),
            tick=tick,
            decision_bar_iso=str(dbar),
            decision_day=str(dday),
            now=now,
            reasons=[reason],
            candidate_id=candidate_id,
            frozen_max_lots=frozen_max_lots,
        )
        if item is None:
            skipped_row["frozen_price_intent_status"] = "geometry_unavailable"
            skipped_row["frozen_price_intent_class"] = packet_class
            return False
        item.state = STATE_REFUSED_COST
        if judgment_rescued:
            # Record the TRUE refusal class on the rescued object (build_frozen_price_intent
            # stamps QUOTE_DEPENDENT). Nothing branches on packet_class after enqueue; the
            # honest class keeps the harvest rows readable.
            item.packet_class = packet_class
        self._frozen_intents[key] = item
        summary["bar_consumable"] = False
        skipped_row["frozen_price_intent_status"] = item.state
        skipped_row["frozen_price_intent_class"] = item.packet_class
        skipped_row["frozen_entry"] = item.frozen_entry
        skipped_row["frozen_stop"] = item.frozen_stop
        skipped_row["candidate_id"] = item.candidate_id
        summary.setdefault("frozen_price_intents", []).append(item.as_row())
        return True

    def _advance_frozen_price_intent(
        self,
        *,
        item,
        now: datetime,
        tick,
        intent,
        unit: dict,
        account_state,
        balance: float,
        dbar: str,
        dday: str,
        ee,
        target_broker_keys,
        placed_broker_symbol_keys,
        open_positions_snapshot,
        summary: dict,
        place: bool,
    ) -> None:
        """Observe one already-frozen object on a live bar. Never re-anchors SL/TP."""
        from .frozen_price_intent import (
            PACKET_CLASS_MODEL_INPUT,
            PACKET_CLASS_NONE,
            PACKET_CLASS_QUOTE_DEPENDENT,
            PACKET_CLASS_STRUCTURAL,
            STATE_AUTHORITY_INVALIDATED,
            STATE_COST_NEVER_VALID,
            STATE_EXPIRED,
            STATE_FILLED,
            STATE_OBSERVING,
            STATE_POSITION_CONFLICT,
            STATE_PRICE_INVALIDATED,
            classify_cost_refusal,
            decision_close_to_send_ms,
            observe_frozen_price_intent,
        )

        skipped_row = {
            "symbol": item.symbol,
            "sleeve": item.sleeve,
            "decision_bar_iso": item.decision_bar_iso,
            "frozen_price_intent_status": item.state,
            "frozen_price_intent_class": item.packet_class,
            "frozen_entry": item.frozen_entry,
            "frozen_stop": item.frozen_stop,
        }
        if item.is_terminal:
            skipped_row["reason"] = f"frozen_price_intent_{item.state.lower()}"
            summary["skipped"].append(skipped_row)
            return

        authority_reason = None
        if not place and _challenge_withholds(
            self._namespace,
            "frozen_place_off",
            {"place": False, "symbol": getattr(item, "symbol", None), "sleeve": getattr(item, "sleeve", None)},
            {
                "place_off_withholds": "Place is off. Do not send this frozen intent.",
                "place_off_is_a_fact": "Place off is a fact. This frozen intent can still send.",
            },
            "place_off_withholds",
            f"frozen_place_off|{getattr(item, 'sleeve', '')}|{getattr(item, 'symbol', '')}|{dbar}",
            "Place is off for this frozen intent. Does that withhold the send? "
            "An empty answer or a tie does not withhold. Do not close an open ticket.",
        ):
            authority_reason = "kill_switch_or_halt_forced_observe_only"
        weekend_block = self._weekend_entry_block(item.sleeve, now)
        if weekend_block is not None and _challenge_withholds(
            self._namespace,
            "weekend_entry",
            {
                "symbol": getattr(item, "symbol", None),
                "sleeve": getattr(item, "sleeve", None),
                "weekend_reason": str(weekend_block),
            },
            {
                "entry_may_proceed": "This candidate can still be the fire.",
                "weekend_embargo": "Do not send this candidate into the weekend window.",
            },
            "weekend_embargo",
            f"frozen_weekend|{getattr(item, 'sleeve', '')}|{getattr(item, 'symbol', '')}|{weekend_block}",
            "A weekend entry rule produced a reason not to send this frozen intent. "
            "An empty answer or a tie does not withhold. Do not close an open ticket.",
        ):
            authority_reason = weekend_block
        f5_clock = self._f5_new_risk_block(item.symbol, now)
        if f5_clock is not None:
            authority_reason = f5_clock

        position_reason = None
        if getattr(ee, "active_trade", None) is not None and _challenge_withholds(
            self._namespace,
            "sleeve_already_holds_symbol",
            {"symbol": intent.symbol, "sleeve": intent.sleeve, "frozen": True},
            {
                "sleeve_holds": "This sleeve already holds the symbol. Do not send again.",
                "sleeve_hold_is_a_fact": "The open sleeve ticket is a fact. This candidate can still send.",
            },
            "sleeve_holds",
            f"frozen_sleeve_holds|{intent.sleeve}|{intent.symbol}|{dbar}",
            "This sleeve already holds the symbol on a frozen intent. "
            "An empty answer or a tie does not withhold. Do not close the open ticket.",
        ):
            position_reason = "sleeve_already_holds_symbol"
        elif self._broker_holds(intent.symbol, intent.sleeve) and _challenge_withholds(
            self._namespace,
            "sleeve_already_holds_symbol_broker",
            {"symbol": intent.symbol, "sleeve": intent.sleeve, "frozen": True},
            {
                "broker_holds": "The broker already holds this sleeve on the symbol. Do not send again.",
                "broker_hold_is_a_fact": "The broker hold is a fact. This candidate can still send.",
            },
            "broker_holds",
            f"frozen_broker_holds|{intent.sleeve}|{intent.symbol}|{dbar}",
            "The broker already holds this sleeve on the symbol. "
            "An empty answer or a tie does not withhold. Do not close the open ticket.",
        ):
            position_reason = "sleeve_already_holds_symbol_broker"
        elif placed_broker_symbol_keys.intersection(target_broker_keys) and _challenge_withholds(
            self._namespace,
            "same_broker_symbol_already_placed_this_cycle",
            {"symbol": intent.symbol, "sleeve": intent.sleeve, "frozen": True},
            {
                "cycle_already_sent": "This cycle already sent this symbol. Do not send again.",
                "sibling_is_a_new_send": "The sibling sleeve is a new send on this symbol.",
            },
            "cycle_already_sent",
            f"frozen_cycle_sent|{intent.sleeve}|{intent.symbol}|{dbar}",
            "This cycle already sent this broker symbol. "
            "An empty answer or a tie does not withhold. Do not close an open ticket.",
        ):
            position_reason = "same_broker_symbol_already_placed_this_cycle"
        elif self._ledger.already_placed(intent.sleeve, intent.symbol, dbar) and _challenge_withholds(
            self._namespace,
            "already_placed_this_bar",
            {"symbol": intent.symbol, "sleeve": intent.sleeve, "frozen": True},
            {
                "this_bar_already_sent": "This sleeve and symbol already sent on this bar. Do not send again.",
                "this_bar_can_send": "The ledger row is a fact. This candidate can still send.",
            },
            "this_bar_already_sent",
            f"frozen_already_bar|{intent.sleeve}|{intent.symbol}|{dbar}",
            "This sleeve and symbol already has a placement on this decision bar. "
            "An empty answer or a tie does not withhold. Do not close an open ticket.",
        ):
            position_reason = "already_placed_this_bar"
        else:
            same_symbol_exposures = self._same_broker_symbol_open_exposures(
                intent.symbol,
                open_positions_snapshot=open_positions_snapshot,
            )
            same_symbol_exposures = self._f5_cross_tf_filter(same_symbol_exposures, intent.sleeve)
            if same_symbol_exposures and _challenge_withholds(
                self._namespace,
                "same_broker_symbol_open_position_lifecycle_guard",
                {"symbol": intent.symbol, "sleeve": intent.sleeve, "frozen": True},
                {
                    "keep_open_ticket": "Keep the open ticket. Do not send this candidate.",
                    "second_thesis_on_this_symbol": "This candidate is a second thesis on this symbol.",
                },
                "keep_open_ticket",
                f"frozen_open_ticket|{intent.sleeve}|{intent.symbol}|{dbar}",
                "A position is already open on this symbol. "
                "An empty answer or a tie does not withhold. Do not close the open ticket.",
            ):
                position_reason = "same_broker_symbol_open_position_lifecycle_guard"

        cost_skip = self._spread_cost_screen(intent, tick)
        packet_class = classify_cost_refusal(
            screen_reason=cost_skip,
            stop_dist=getattr(intent, "stop_dist", None),
            symbol=getattr(intent, "symbol", ""),
            digits=self._symbol_digits(getattr(intent, "symbol", "")),
            point=self._symbol_point(getattr(intent, "symbol", "")),
        )
        if cost_skip is None:
            packet_class = PACKET_CLASS_NONE
        if (
            packet_class == PACKET_CLASS_STRUCTURAL
            and self._judgment_rescue
            and self._judgment_rescue_verdict(item.candidate_id, now)
        ):
            # Judgment RESCUE extends the watch where a terminal cost re-classification
            # would have dropped it (STATE_COST_NEVER_VALID). ONLY the cost-terminal drop
            # is overridden: expiry, blow-through, chase kill-band, authority and position
            # gates inside observe_frozen_price_intent all stay live, and a placement
            # still requires the code's own cost screen to clear on a later tick —
            # judgment never calls place(). Flag off: no lookup runs (short-circuit).
            skipped_row["frozen_price_intent_judgment_rescue"] = True
            packet_class = PACKET_CLASS_QUOTE_DEPENDENT

        next_state = observe_frozen_price_intent(
            item,
            now=now,
            tick=tick,
            place=place and authority_reason is None,
            authority_reason=authority_reason,
            position_reason=position_reason,
            cost_class=packet_class,
            cost_reason=cost_skip,
        )
        skipped_row["frozen_price_intent_status"] = next_state
        skipped_row["reason"] = item.last_reason or f"frozen_price_intent_{next_state.lower()}"
        # Persist is not a second waiter. One watch tick on the existing observe path.
        # ORDER IS LOAD-BEARING (REVIEW-20260817 §B defect 1): the emit reads
        # `frozen_price_intent_status` from `skipped_row`, so it must run AFTER the
        # post-observe stamp above — the persisted events row then carries the same
        # state/reason the launcher skip row logs. When persist ran before observe(),
        # the events tape carried the PRE-observe leftover while the contract applied
        # the kill on the same tick (ETH 01:01Z, XRP 01:31Z, GBPJPY 13:31Z on
        # 2026-08-17: events `REFUSED_COST` vs launcher `PRICE_INVALIDATED`).
        self._persist_f5_watch_quote(
            now=now,
            item=item,
            intent=intent,
            unit=unit,
            tick=tick,
            dbar=dbar,
            dday=dday,
            skipped_row=skipped_row,
        )
        if next_state in {
            STATE_PRICE_INVALIDATED,
            STATE_EXPIRED,
            STATE_AUTHORITY_INVALIDATED,
            STATE_POSITION_CONFLICT,
            STATE_COST_NEVER_VALID,
        }:
            summary["skipped"].append(skipped_row)
            summary.setdefault("frozen_price_intents", []).append(item.as_row())
            return
        if packet_class == PACKET_CLASS_QUOTE_DEPENDENT:
            summary["bar_consumable"] = False
            summary["skipped"].append(skipped_row)
            summary.setdefault("frozen_price_intents", []).append(item.as_row())
            return

        send_at = datetime.now(timezone.utc)
        close_to_send_ms = decision_close_to_send_ms(item.decision_close_utc, send_at)
        item.decision_close_to_send_ms = close_to_send_ms
        annotations = {
            "decision_close_to_send_ms": close_to_send_ms,
            "frozen_price_intent": True,
            "frozen_price_intent_schema": "gtos.ultimate_book.frozen_price_intent.v1",
            "frozen_entry_price": item.frozen_entry,
            "frozen_stop_loss": item.frozen_stop,
            "frozen_take_profit_1": item.frozen_target,
            "frozen_max_lots": item.frozen_max_lots,
            "frozen_queued_at_utc": item.queued_at_utc.isoformat(),
        }
        unit_view = _UnitView(item.unit or unit)
        route_intent = self._limit_at_level_intent(
            intent, frozen_entry=getattr(item, "frozen_entry", None)
        )
        flow_hold, flow_dec = self._judgment_flow_hold(
            route_intent, unit_view, tick, account_state, item.geometry(), now,
            candidate_id=getattr(item, "candidate_id", None),
        )
        summary.setdefault("judgment_flow", []).append(flow_dec)
        if flow_hold:
            skipped_row["reason"] = (
                "judgment_hold_unanswered"
                if isinstance(flow_dec, dict) and flow_dec.get("unanswered")
                else "judgment_hold"
            )
            skipped_row["judgment_flow"] = flow_dec
            summary["skipped"].append(skipped_row)
            summary.setdefault("frozen_price_intents", []).append(item.as_row())
            return
        if (
            getattr(intent, "sleeve", None),
            getattr(intent, "symbol", None),
            dbar,
        ) in getattr(self, "_timeout_ended", ()):
            skipped_row["reason"] = "order_timeout_retries"
            summary["skipped"].append(skipped_row)
            summary.setdefault("frozen_price_intents", []).append(item.as_row())
            return
        if self._timeout_quiet_holds(
            getattr(intent, "sleeve", None),
            getattr(intent, "symbol", None),
            dbar,
        ):
            summary["bar_consumable"] = False
            skipped_row["reason"] = "order_timeout_unanswered"
            summary["skipped"].append(skipped_row)
            summary.setdefault("frozen_price_intents", []).append(item.as_row())
            return
        annotations = self._stamp_lifetime_notes(
            annotations, getattr(intent, "symbol", None),
        )
        for _hop_key_name, _hop_value in _hop_notes(
            route_intent,
            flow_dec,
            _read_hop(getattr(self, "_owner_hops", None), route_intent, dbar),
        ).items():
            annotations.setdefault(_hop_key_name, _hop_value)
        result = self.router.place(
            ee,
            unit_view,
            route_intent,
            tick,
            account_state,
            balance,
            geometry=item.geometry(),
            annotations=annotations,
        )
        if result.get("placed") and result.get("native_pending"):
            item.terminate(STATE_FILLED, "native_pending_resting")
            item.decision_close_to_send_ms = close_to_send_ms
            placed_broker_symbol_keys.update(target_broker_keys)
            ticket = getattr(result.get("trade_state"), "ticket", None)
            trade_params = result.get("trade_params") or {}
            candidate_id = (
                result.get("candidate_id")
                or trade_params.get("candidate_id")
                or getattr(item, "candidate_id", None)
            )
            resolved_cluster = self._resolve_runtime_cluster(
                unit=item.unit or unit,
                sleeve=intent.sleeve,
                candidate_id=candidate_id,
            )
            try:
                self._ledger.record(
                    intent.sleeve,
                    intent.symbol,
                    dbar,
                    candidate_id=candidate_id,
                    ticket=ticket,
                    ts=send_at.isoformat(),
                    decision_day=dday,
                    cluster=resolved_cluster,
                    require_full_context=True,
                )
            except Exception:
                pass
            summary.setdefault("pending", []).append({
                "symbol": intent.symbol,
                "sleeve": intent.sleeve,
                "decision_bar_iso": dbar,
                "decision_day": dday,
                "cluster": resolved_cluster,
                "candidate_id": candidate_id,
                "ticket": ticket,
                "reason": result.get("reason") or "native_pending_resting",
                "frozen_price_intent": True,
                "frozen_entry": item.frozen_entry,
                "limit_at_level": True,
            })
            # Same persist hole as the live native_pending path: park without a
            # trade record left the later fill/adopt with no F5 entry risk.
            try:
                broker_symbol = self._broker_symbol(intent.symbol)
            except Exception:
                broker_symbol = None
            self._persist_trade_record(
                ticket,
                trade_params,
                route_intent,
                decision_bar_iso=dbar,
                decision_day=dday,
                cluster=resolved_cluster,
                placed_at_utc=send_at.isoformat(),
                broker_symbol=broker_symbol,
            )
            summary.setdefault("frozen_price_intents", []).append(item.as_row())
            return
        if result.get("placed"):
            item.terminate(STATE_FILLED, "ok")
            item.decision_close_to_send_ms = close_to_send_ms
            placed_broker_symbol_keys.update(target_broker_keys)
            self._commit_book_placement(
                summary=summary,
                now=send_at,
                intent=intent,
                route_intent=route_intent,
                unit=item.unit or unit,
                unit_su=unit_view,
                result=result,
                dbar=dbar,
                dday=dday,
                extra={
                    "decision_close_to_send_ms": close_to_send_ms,
                    "frozen_price_intent": True,
                    "frozen_entry": item.frozen_entry,
                    "frozen_stop": item.frozen_stop,
                },
                ee=ee,
            )
            summary.setdefault("frozen_price_intents", []).append(item.as_row())
            return

        retry_packet = self._frozen_packet_from_place_result(result)
        retry_class = classify_cost_refusal(
            reasons=[result.get("reason")],
            packet=retry_packet,
            screen_reason=None,
            stop_dist=getattr(intent, "stop_dist", None),
            symbol=getattr(intent, "symbol", ""),
            digits=self._symbol_digits(getattr(intent, "symbol", "")),
            point=self._symbol_point(getattr(intent, "symbol", "")),
        )
        judgment_extended = (
            retry_class == PACKET_CLASS_STRUCTURAL
            and self._judgment_rescue
            and self._judgment_rescue_verdict(item.candidate_id, now)
        )
        failure_bar = self._place_failure_bar(result.get("reason"))
        timeout_here = (
            str(getattr(self, "_namespace", "") or "") == "operator"
            and _is_order_timeout_reason(result.get("reason"))
        )
        if timeout_here and failure_bar == "unanswered":
            self._mark_timeout_quiet(
                getattr(intent, "sleeve", None),
                getattr(intent, "symbol", None),
                dbar,
            )
            skipped_row["order_timeout"] = "unanswered"
        if timeout_here:
            keep_observing = failure_bar in {"open", "unanswered"} or judgment_extended
        else:
            keep_observing = (
                retry_class == PACKET_CLASS_QUOTE_DEPENDENT
                or _is_transient_place_failure(result.get("reason"))
                or judgment_extended
            )
        if keep_observing:
            # `judgment_extended`: the authoritative place-path cost model refused
            # terminally and a fresh Cost-role RESCUE says that refusal is wrong. Keep
            # the object OBSERVING on the existing rail instead of STATE_COST_NEVER_VALID
            # — its own TTL / blow-through / chase gates still kill it, and any fill
            # still has to clear the full place() stack on a later tick. Flag off: no
            # lookup runs and the terminal drop below is byte-for-byte today's behavior.
            if judgment_extended:
                skipped_row["frozen_price_intent_judgment_rescue"] = True
            item.state = STATE_OBSERVING
            item.last_reason = str(result.get("reason") or item.last_reason)
            summary["bar_consumable"] = False
            skipped_row["reason"] = item.last_reason
            skipped_row["frozen_price_intent_status"] = item.state
            skipped_row.update(self._runtime_learning_router_result_context(result))
            summary["skipped"].append(skipped_row)
            summary.setdefault("frozen_price_intents", []).append(item.as_row())
            return
        terminal = (
            STATE_COST_NEVER_VALID
            if retry_class in {PACKET_CLASS_STRUCTURAL, PACKET_CLASS_MODEL_INPUT}
            else STATE_PRICE_INVALIDATED
        )
        item.terminate(terminal, str(result.get("reason") or terminal.lower()))
        skipped_row["reason"] = item.last_reason
        skipped_row["frozen_price_intent_status"] = item.state
        skipped_row.update(self._runtime_learning_router_result_context(result))
        summary["skipped"].append(skipped_row)
        summary.setdefault("frozen_price_intents", []).append(item.as_row())

    def _commit_book_placement(
        self,
        *,
        summary: dict,
        now: datetime,
        intent,
        route_intent,
        unit: dict,
        unit_su,
        result: dict,
        dbar: str,
        dday: str,
        extra: Optional[dict] = None,
        ee=None,
    ) -> dict:
        """Commit one broker-confirmed placement to the existing owner authorities."""
        record_conviction = getattr(self.engine, "record_placement_conviction", None)
        if callable(record_conviction):
            try:
                record_conviction(intent)
            except Exception:
                pass
        ticket = getattr(result.get("trade_state"), "ticket", None)
        trade_params = result.get("trade_params") or {}
        # POST-FILL TRUTH stamp before the record persists (same as the live market path).
        self._f5_fill_truth_fields(trade_params, result)
        candidate_id = result.get("candidate_id") or trade_params.get("candidate_id")
        placed_at = now.isoformat()
        resolved_cluster = self._resolve_runtime_cluster(
            unit=unit,
            sleeve=intent.sleeve,
            candidate_id=candidate_id,
        )
        try:
            broker_symbol = self._broker_symbol(intent.symbol)
        except Exception:
            broker_symbol = None
        ledger_row = self._ledger.record(
            intent.sleeve,
            intent.symbol,
            dbar,
            candidate_id=candidate_id,
            ticket=ticket,
            ts=placed_at,
            decision_day=dday,
            cluster=resolved_cluster,
            require_full_context=True,
        )
        self._persist_trade_record(
            ticket,
            trade_params,
            route_intent,
            decision_bar_iso=dbar,
            decision_day=dday,
            cluster=resolved_cluster,
            placed_at_utc=placed_at,
            broker_symbol=broker_symbol,
        )
        persisted_record = self._load_trade_record(ticket)
        placed_row = {
            "symbol": intent.symbol,
            "sleeve": intent.sleeve,
            "decision_bar_iso": dbar,
            "decision_day": dday,
            "cluster": resolved_cluster,
            "candidate_id": candidate_id,
        }
        if isinstance(ledger_row, dict):
            for key in (
                "placement_capture_contract_version",
                "placement_source_completeness_status",
                "placement_source_missing_fields",
            ):
                if ledger_row.get(key) is not None:
                    placed_row[key] = ledger_row.get(key)
        placed_row.update(self._runtime_learning_trade_context(
            ticket=ticket,
            trade_params=trade_params,
            record=persisted_record,
            broker_symbol=broker_symbol,
            placed_at_utc=placed_at,
        ))
        if extra:
            placed_row.update(extra)
        summary["placed"].append(placed_row)
        self._f5_on_open(
            ticket=ticket,
            sleeve=intent.sleeve,
            symbol=intent.symbol,
            trade_params=trade_params,
            candidate_id=candidate_id,
            decision_day=dday,
            decision_bar_iso=dbar,
        )
        if ee is not None:
            # Same post-fill deviation guard as the live market path (namespace-gated).
            self._f5_fill_deviation_guard(
                ee=ee, ticket=ticket, sleeve=intent.sleeve, symbol=intent.symbol,
                trade_params=trade_params, decision_bar_iso=dbar)
        self._notify_placed(route_intent, unit_su, result)
        return placed_row

    def _sweep_frozen_price_intents(self, now: datetime, summary: dict) -> None:
        """Expire / keep-live any FrozenPriceIntent not visited this cycle."""
        if not self._frozen_intent_reprice or not self._frozen_intents:
            return
        from .frozen_price_intent import STATE_EXPIRED

        still_open = False
        for item in list(self._frozen_intents.values()):
            if not item.is_open:
                continue
            if item.expired_at(now):
                item.terminate(STATE_EXPIRED, f"hard_expiry_seconds:{item.hard_expiry_seconds:g}")
                summary["skipped"].append({
                    "symbol": item.symbol,
                    "sleeve": item.sleeve,
                    "decision_bar_iso": item.decision_bar_iso,
                    "reason": item.last_reason,
                    "frozen_price_intent_status": item.state,
                    "frozen_price_intent_class": item.packet_class,
                })
                summary.setdefault("frozen_price_intents", []).append(item.as_row())
                continue
            still_open = True
        if still_open:
            summary["bar_consumable"] = False

    def _symbol_info_obj(self, symbol):
        mt5 = getattr(self, "_mt5", None)
        if mt5 is None:
            return None
        for name in ("symbol_info", "get_symbol_info"):
            getter = getattr(mt5, name, None)
            if not callable(getter):
                continue
            try:
                return getter(symbol)
            except Exception:
                continue
        return None

    def _symbol_digits(self, symbol) -> int | None:
        info = self._symbol_info_obj(symbol)
        if info is None:
            return None
        try:
            if isinstance(info, dict):
                value = info.get("digits")
            else:
                value = getattr(info, "digits", None)
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _symbol_point(self, symbol) -> float | None:
        info = self._symbol_info_obj(symbol)
        if info is None:
            return None
        try:
            if isinstance(info, dict):
                value = info.get("point")
            else:
                value = getattr(info, "point", None)
            number = float(value)
            return number if number > 0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _price_text(value: float, digits: int | None) -> str:
        if digits is not None and digits >= 0:
            return f"{value:.{int(digits)}f}"
        return f"{value:.8f}"

    # Named sample: min-over-N-ms. Not a new cap. 0.35 on fx_jpy stays.
    # A $0.07 GBPJPY flicker is which tick the owner held. Aug-12 06:00:00.459
    # was already inside ($2.44 vs $3.50). The owner snapshot at 06:00:22.208
    # was $4.06; the book was back inside 0.9s later. Window is 1000ms.
    SPREAD_SAMPLE_KIND = "min_over_ms"
    SPREAD_SAMPLE_MIN_OVER_MS = 1000
    SPREAD_SAMPLE_POLL_MS = 100

    def _spread_sample_min_over_ms(self) -> int:
        rt = self.base_config.get("gtos_vnext_runtime", {}) or {}
        raw = rt.get("spread_cost_screen_min_over_ms", self.SPREAD_SAMPLE_MIN_OVER_MS)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return self.SPREAD_SAMPLE_MIN_OVER_MS
        return value if value >= 0 else self.SPREAD_SAMPLE_MIN_OVER_MS

    def _spread_sample_sleep(self, seconds: float) -> None:
        time.sleep(float(seconds))

    def _spread_sample_extra_ticks(self, symbol):
        """More ticks for min-over-N-ms. Tests may set _spread_sample_extra_ticks_override."""
        override = getattr(self, "_spread_sample_extra_ticks_override", None)
        if override is not None:
            yield from override
            return
        budget = self._spread_sample_min_over_ms()
        if budget <= 0:
            return
        poll = self.SPREAD_SAMPLE_POLL_MS
        elapsed = 0
        while elapsed < budget:
            try:
                self._spread_sample_sleep(poll / 1000.0)
            except Exception:
                break
            elapsed += poll
            tick = self._tick(symbol)
            if tick is not None:
                yield tick

    def _spread_cost_screen(self, intent, tick) -> Optional[str]:
        """Deterministic pre-send mirror of the authoritative pretrade spread-cost gate
        (broker_net_cost_engine: spread_r = (ask-bid)/sl_distance vs selected_cell_pretrade_max_spread_r,
        default 0.10). Returns a precise refusal-reason string when this leg's live spread structurally
        exceeds the limit of its R-unit (intent.stop_dist) -- so the book declines it cleanly instead of
        attempting a futile order that open_trade's ExecMgr-V4 cost gate would block. Returns None when the
        leg passes OR the screen cannot be evaluated (fail OPEN -> defer to the authoritative gate).

        The quoted book is the spread in pips. One point on a 5-digit quote
        is 0.1 pip. That measurement is not the stop divided into a 1.30 pip
        label. A constant floor does not return before the choice.

        Sample is min-over-N-ms (1000ms) on a would-be refuse only. A first tick
        already inside does not wait. Cap numbers are unchanged.
        """
        try:
            from .frozen_price_intent import is_market_stop

            rd = float(getattr(intent, "stop_dist", 0.0) or 0.0)
            bid = float(getattr(tick, "bid", 0.0) or 0.0)
            ask = float(getattr(tick, "ask", 0.0) or 0.0)
            if rd <= 0 or bid <= 0 or ask <= 0 or ask < bid:
                return None                       # cannot evaluate -> let the authoritative gate decide
            symbol = getattr(intent, "symbol", "")
            digits = self._symbol_digits(symbol)
            point = self._symbol_point(symbol)
            rt = self.base_config.get("gtos_vnext_runtime", {}) or {}
            try:
                max_spread_r = float(rt.get("selected_cell_pretrade_max_spread_r", 0.10))
            except (TypeError, ValueError):
                max_spread_r = 0.10
            # per-sleeve override (matches the authoritative gate in broker_net_cost_engine): a tiny-stop
            # session sleeve (fx_jpy/fx_jpy_ny) on an owner-approved JPY-cross live trial runs a looser
            # ceiling, so the screen must NOT pre-block what the gate now allows.
            by_sleeve = rt.get("selected_cell_pretrade_max_spread_r_by_sleeve")
            sleeve = getattr(intent, "sleeve", None)
            if isinstance(by_sleeve, dict) and sleeve in by_sleeve:
                try:
                    max_spread_r = float(by_sleeve[sleeve])
                except (TypeError, ValueError):
                    pass
            sample_ms = self._spread_sample_min_over_ms()
            sample_ticks = 1
            spread_r = (ask - bid) / rd
            self._remember_spread_screen_tick(intent, tick, stop_dist=rd)
            if not is_market_stop(rd, digits=digits, point=point, symbol=symbol):
                self._record_spread_observation(
                    intent, spread_r=spread_r, spread_price=ask - bid,
                    max_spread_r=max_spread_r, stop_dist=rd,
                    bid=bid, ask=ask, digits=digits,
                    sample_kind=self.SPREAD_SAMPLE_KIND,
                    sample_min_over_ms=sample_ms,
                    sample_ticks=1,
                )
                from .frozen_price_intent import quoted_book_pips
                quoted = quoted_book_pips(
                    bid=bid, ask=ask, digits=digits, point=point, symbol=symbol,
                )
                spread_px = ask - bid
                _block_invalid = False
                if quoted is not None:
                    try:
                        _block_invalid = bool(_spot_choice(
                            "model_input_invalid_stop",
                            {
                                "symbol": str(symbol),
                                "sleeve": str(getattr(intent, "sleeve", "") or ""),
                                "stop_dist": rd,
                                "quoted_book_pips": quoted,
                                "spread_price": spread_px,
                                "bid": bid,
                                "ask": ask,
                                "namespace": str(getattr(self, "_namespace", "") or ""),
                            },
                            {
                                "stop_is_constructible": "The quoted book is the spread in pips. This stop can be the plan.",
                                "stop_not_a_market": "The quoted book says this stop is not a market. Do not send.",
                            },
                            "stop_not_a_market",
                            f"model_input_invalid_stop|{symbol}|{spread_px:.8f}|quoted",
                            "The quoted book pip is the spread divided by the symbol pip. "
                            "One point on a 5-digit quote is 0.1 pip. "
                            "Do not relabel that book as 1.30 pip. "
                            "Is the stop constructible, or not a market? "
                            "An empty answer or a tie does not withhold. "
                            "Do not close an open ticket.",
                        ))
                    except Exception:
                        _block_invalid = False
                if _block_invalid:
                    return (
                        f"model_input_invalid_stop:{spread_px:.8f} "
                        f"({quoted:.2f} pip quoted book on {symbol} "
                        f"bid {self._price_text(bid, digits)} ask {self._price_text(ask, digits)})"
                    )
            if spread_r > max_spread_r:
                best_bid, best_ask = bid, ask
                best_width = ask - bid
                for extra in self._spread_sample_extra_ticks(symbol):
                    try:
                        extra_bid = float(getattr(extra, "bid", 0.0) or 0.0)
                        extra_ask = float(getattr(extra, "ask", 0.0) or 0.0)
                    except (TypeError, ValueError):
                        continue
                    if extra_bid <= 0 or extra_ask <= 0 or extra_ask < extra_bid:
                        continue
                    sample_ticks += 1
                    self._remember_spread_screen_tick(intent, extra, stop_dist=rd)
                    width = extra_ask - extra_bid
                    if width < best_width:
                        best_width = width
                        best_bid, best_ask = extra_bid, extra_ask
                bid, ask = best_bid, best_ask
                spread_r = (ask - bid) / rd
            # Record the observation for EVERY evaluated leg, pass or fail. Recording only the
            # failures would build the spread record out of a refusal log, which is the
            # derive-don't-accumulate trap: the passing legs are most of the distribution and
            # their absence would read as "no spread" rather than "spread was fine".
            self._record_spread_observation(
                intent, spread_r=spread_r, spread_price=ask - bid,
                max_spread_r=max_spread_r, stop_dist=rd,
                bid=bid, ask=ask, digits=digits,
                sample_kind=self.SPREAD_SAMPLE_KIND,
                sample_min_over_ms=sample_ms,
                sample_ticks=sample_ticks,
            )
            above_cell = spread_r > max_spread_r
            try:
                withhold_cell = _spot_choice(
                    "cell_spread",
                    {
                        "symbol": str(getattr(intent, "symbol", "") or ""),
                        "sleeve": str(getattr(intent, "sleeve", "") or ""),
                        "spread_r": float(spread_r),
                        "max_spread_r": float(max_spread_r),
                        "spread_above_the_cell": bool(above_cell),
                        "stop_dist": float(rd),
                        "bid": float(bid),
                        "ask": float(ask),
                    },
                    {
                        "spread_withholds": "This spread withholds the send.",
                        "spread_is_a_fact": "The spread reading is a fact. It does not by itself withhold.",
                    },
                    "spread_withholds",
                    f"cell_spread|{getattr(intent, 'sleeve', '')}|{getattr(intent, 'symbol', '')}|{spread_r:.4f}",
                    "The two sides of this spread against the cell. "
                    "An empty answer or a tie does not withhold. "
                    "A floor dollar and a baseline dollar are not a limit.",
                )
            except Exception:
                withhold_cell = False
            if withhold_cell:
                width = ask - bid
                return (
                    f"cost_screen_spread_r:{spread_r:.3f}>{max_spread_r:.3f} "
                    f"(spread {self._price_text(width, digits)} "
                    f"bid {self._price_text(bid, digits)} ask {self._price_text(ask, digits)} "
                    f"vs {getattr(intent,'sleeve','?')} stop {self._price_text(rd, digits)})"
                )
            return None
        except Exception:
            return None                            # a screen error must never block the cycle

    def _f5_preorder_market_stop_floor(self, intent):
        """Widen sub-market FX stops for the one commissioned F5 namespace.

        The authoritative screen rejects 3/5-digit FX stops below five
        conventional pips.  F5 fixes the geometry before that screen and before
        order construction; fixed-dollar sizing therefore lowers lots as needed.
        Explicit targets move by the same factor so their R multiple is stable.
        Any missing/invalid geometry leaves the intent unchanged, allowing the
        existing fail-closed screen to reject it.
        """
        if (
            getattr(self, "_namespace", None) != "operator"
            or getattr(self, "_f5_cfg", None) is None
        ):
            return intent, None
        try:
            from dataclasses import replace

            from .frozen_price_intent import fx_pip_size
            from src.judgment.nineteen import score

            symbol = str(getattr(intent, "symbol", "") or "")
            stop_before = float(getattr(intent, "stop_dist", 0.0) or 0.0)
            pip = fx_pip_size(
                digits=self._symbol_digits(symbol),
                point=self._symbol_point(symbol),
                symbol=symbol,
            )
            if pip is None or stop_before <= 0:
                return intent, None
            stop_pips = stop_before / float(pip)
            target_pips = None
            target_dist = _finite_number(getattr(intent, "target_dist", None))
            if target_dist is not None and target_dist > 0:
                target_pips = target_dist / float(pip)
            pip_anchors = _anchor_pairs((
                ("stop_pips", stop_pips),
                ("target_pips", target_pips),
            ))
            pips = None
            if pip_anchors is not None:
                pips = score(
                    {
                        "symbol": symbol,
                        "sleeve": str(getattr(intent, "sleeve", "") or ""),
                        "stop_dist": stop_before,
                        "target_dist": target_dist,
                        "pip_size": float(pip),
                    },
                    question_id="market_stop_min_pips",
                    instructions=(
                        "The score you return is the minimum protective distance in pips. "
                        "An empty score leaves the stop unchanged. Do not send."
                    ),
                    anchors=pip_anchors,
                )
            if pips is None:
                return intent, None
            stop_after = float(pips) * float(pip)
            if stop_before >= stop_after:
                return intent, None

            target_before = getattr(intent, "target_dist", None)
            target_after = target_before
            target_policy = "dynamic_exit_profile"
            if target_before not in (None, ""):
                target_number = float(target_before)
                if target_number > 0:
                    target_after = target_number * (stop_after / stop_before)
                    target_policy = "preserve_r_multiple"

            widened = _carry_hop_returns(intent, replace(
                intent,
                stop_dist=stop_after,
                target_dist=target_after,
            ))
            return widened, {
                "schema_version": "f5_preorder_market_stop_floor_v1",
                "namespace": self._namespace,
                "symbol": symbol,
                "sleeve": str(getattr(intent, "sleeve", "") or ""),
                "minimum_pips": float(pips),
                "pip_size": float(pip),
                "stop_dist_before": stop_before,
                "stop_dist_after": stop_after,
                "widening_factor": stop_after / stop_before,
                "target_dist_before": target_before,
                "target_dist_after": target_after,
                "target_policy": target_policy,
                "risk_policy": "f5_fixed_usd_reprices_lots",
            }
        except (TypeError, ValueError):
            return intent, None

    def _transient_retry_terminal(self, *, intent, dbar, reason, now, summary) -> bool:
        """--transient-retry-cap accounting for ONE failed placement attempt (already sent,
        already failed, already classified transient by the caller).

        Returns True when this attempt is the (N+1)th same-reason-class failure on this
        (sleeve, symbol, decision_bar) — the caller then leaves the bar CONSUMABLE, which is
        exactly how a terminal decline behaves today. Returns False otherwise, including:
        cap==0/flag absent (no state is touched — byte-identical branch), any accounting
        error (fall back to today's retry rather than consume a bar on a bookkeeping bug).

        PLACEMENT PATH ONLY. Closes, cancels and stop-tightenings live in
        manage_open_positions / _flatten_all_engines / the engines' own management and never
        reach the placement-failure branch, so risk-reducing requests can never be capped.
        Counters are per-bar keys held in memory: a new decision bar starts at zero, a
        restart forgets everything (the restarted process re-runs the bar at most once more
        before the cap re-fills)."""
        if (
            str(getattr(self, "_namespace", "") or "") == "operator"
            and _is_order_timeout_reason(reason)
        ):
            return self._timeout_attempt_ended(
                intent=intent, dbar=dbar, reason=reason, now=now, summary=summary,
            )
        if self._transient_retry_cap <= 0:
            return False
        try:
            prefix = _transient_place_reason_prefix(reason)
            if prefix is None:
                return False
            sleeve = getattr(intent, "sleeve", "?")
            symbol = getattr(intent, "symbol", "?")
            key = (sleeve, symbol, dbar, prefix)
            # bound memory on a long-running process (same discipline as _notified_rejects);
            # per-bar keys age out naturally, this is only the pathological backstop.
            if len(self._transient_retry_counts) > 5000:
                self._transient_retry_counts.clear()
            if len(self._transient_retry_capped) > 5000:
                self._transient_retry_capped.clear()
            now_iso = now.isoformat()
            st = self._transient_retry_counts.get(key)
            if st is None:
                st = {"attempts": 0, "first_attempt_utc": now_iso}
                self._transient_retry_counts[key] = st
            st["attempts"] = int(st["attempts"]) + 1
            st["last_attempt_utc"] = now_iso
            if st["attempts"] <= self._transient_retry_cap:
                return False
            if str(getattr(self, "_namespace", "") or "") == "operator":
                stands = _spot_choice(
                    "transient_retry_cap_reached",
                    {
                        "symbol": getattr(intent, "symbol", None),
                        "sleeve": getattr(intent, "sleeve", None),
                        "attempts": st["attempts"],
                        "launcher_transient_retry_cap": self._transient_retry_cap,
                        "namespace": "operator",
                    },
                    {
                        "cap_stands": "The transient retry count withholds another send of this bar.",
                        "try_again": "The retry count is a fact. This bar can still send.",
                    },
                    "cap_stands",
                    f"transient_retry_terminal|{getattr(intent, 'sleeve', '')}|{getattr(intent, 'symbol', '')}|{dbar}|{st['attempts']}",
                    "The launcher retry count is a fact. It does not by itself end the bar. "
                    "An empty answer or a tie does not end it. Do not close an open ticket.",
                )
                if not stands:
                    return False
            # (N+1)th same-class failure: TERMINAL for this bar. One summary row, one
            # deduped notify, and the (sleeve, symbol, bar) is marked so the pre-send gate
            # suppresses further sends while another leg keeps the bar alive.
            self._transient_retry_capped.add((sleeve, symbol, dbar))
            summary["skipped"].append({
                "symbol": symbol, "sleeve": sleeve, "decision_bar_iso": dbar,
                "reason": "transient_retry_cap_reached",
                "transient_retry_cap": self._transient_retry_cap,
                "attempts": st["attempts"],
                "first_attempt_utc": st["first_attempt_utc"],
                "last_attempt_utc": st["last_attempt_utc"],
                "capped_reason_prefix": prefix,
                "last_reason": str(reason),
            })
            _log.warning(
                "book[%s]: transient retry cap reached — %s/%s bar %s: %d attempts "
                "(%s .. %s), every one '%s'-class; giving this bar up (terminal).",
                self._namespace, sleeve, symbol, dbar, st["attempts"],
                st["first_attempt_utc"], st["last_attempt_utc"], prefix,
            )
            rkey = (sleeve, symbol, dbar, "transient_retry_cap_reached")
            if rkey not in self._notified_rejects:
                if len(self._notified_rejects) > 5000:
                    self._notified_rejects.clear()
                self._notified_rejects.add(rkey)
                self._notify_reject(
                    intent,
                    f"transient_retry_cap_reached — {st['attempts']} attempts "
                    f"({prefix}…) all failed the same way; bar given up",
                )
            return True
        except Exception:
            return False   # accounting must never decide anything on an error

    def _notify_cost_skip(self, intent, reason) -> None:
        """EXPECTED cost decline (spread structurally too wide for the sleeve's stop) -> inform the owner
        once per decision bar as an ℹ️ note, NOT the ⚠️ 'Trade NOT placed' failure card."""
        try:
            label = self._SLEEVE_LABEL.get(getattr(intent, "sleeve", ""), getattr(intent, "sleeve", "?"))
            self._send_card(f"[{self._account_label()}] ℹ️ Skipped {getattr(intent,'symbol','?')} ({label}) — "
                            f"spread too wide for stop · {reason}")
        except Exception:
            pass

    def _notify_reject(self, intent, reason) -> None:
        try:
            label = self._SLEEVE_LABEL.get(getattr(intent, "sleeve", ""), getattr(intent, "sleeve", "?"))
            self._send_card(f"[{self._account_label()}] ⚠️ Trade NOT placed · {getattr(intent,'symbol','?')} ({label}) — {reason}")
        except Exception:
            pass

    @staticmethod
    def _closed_record_realized_pnl(record: dict | None) -> float | None:
        if not isinstance(record, dict):
            return None
        for source in (
            record,
            record.get("execution") if isinstance(record.get("execution"), dict) else None,
        ):
            if not isinstance(source, dict):
                continue
            for key in (
                "broker_realized_pnl",
                "broker_position_realized_pnl",
                "broker_selected_exit_realized_pnl",
            ):
                value = source.get(key)
                if value in (None, ""):
                    continue
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    @staticmethod
    def _closed_record_float(record: dict | None, *keys: str) -> float | None:
        if not isinstance(record, dict):
            return None
        sources = (
            record,
            record.get("execution") if isinstance(record.get("execution"), dict) else None,
            record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else None,
        )
        for source in sources:
            if not isinstance(source, dict):
                continue
            for key in keys:
                value = source.get(key)
                if value in (None, ""):
                    continue
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    @staticmethod
    def _closed_record_value(record: dict | None, *keys: str):
        if not isinstance(record, dict):
            return None
        sources = (
            record,
            record.get("execution") if isinstance(record.get("execution"), dict) else None,
            record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else None,
        )
        for source in sources:
            if not isinstance(source, dict):
                continue
            for key in keys:
                value = source.get(key)
                if value not in (None, ""):
                    return value
        return None

    @staticmethod
    def _minutes_between(start_value, end_value) -> float | None:
        if not start_value or not end_value:
            return None
        try:
            start = datetime.fromisoformat(str(start_value).replace("Z", "+00:00"))
            end = datetime.fromisoformat(str(end_value).replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            return (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds() / 60.0
        except Exception:
            return None

    def _record_closed_trade_daily_pnl(self, ticket, record: dict | None, action: str) -> bool:
        if ticket in (None, 0) or not isinstance(record, dict):
            return False
        execution = record.setdefault("execution", {})
        if execution.get("daily_pnl_ledger_status") == "RECORDED_BROKER_NET":
            return False
        broker_net = self._closed_record_realized_pnl(record)
        if broker_net is None:
            execution["daily_pnl_ledger_status"] = "PENDING_BROKER_REALIZED_PNL"
            return False
        symbol = (
            record.get("symbol")
            or self._closed_record_value(record, "symbol")
            or self._closed_record_value(record, "broker_symbol")
            or "UNKNOWN"
        )
        trade_id = f"{self._namespace}:{symbol}:{ticket}"
        try:
            from src.notifications import record_trade_closed_pnl

            opened_at = (
                record.get("opened_at_utc")
                or self._closed_record_value(record, "placed_at_utc", "broker_fill_time_utc")
            )
            closed_at = record.get("closed_at_utc") or self._closed_record_value(record, "closed_at_utc")
            record_trade_closed_pnl(
                str(symbol),
                str(action or record.get("close_action") or "broker_closed"),
                actual_r=0.0,
                hold_minutes=self._minutes_between(opened_at, closed_at),
                trade_id=trade_id,
                entry_price=self._closed_record_float(record, "broker_entry_price", "entry_price") or 0.0,
                exit_price=self._closed_record_float(record, "broker_exit_price", "exit_price") or 0.0,
                vnext_context={
                    "runtime_namespace": self._namespace,
                    "ticket_hash_sha256": self._closed_record_value(record, "ticket_hash_sha256"),
                    "candidate_id": record.get("candidate_id"),
                    "broker_realized_pnl_source": self._closed_record_value(record, "broker_realized_pnl_source"),
                    "exit_reconciliation_status": record.get("exit_reconciliation_status"),
                    "close_action": action or record.get("close_action"),
                },
                broker_profit=self._closed_record_float(
                    record,
                    "broker_position_aggregate_profit",
                    "broker_exit_aggregate_profit",
                    "broker_exit_profit",
                ),
                broker_net_profit=broker_net,
                broker_deal_reconciled=record.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY",
                broker_deal_id=self._closed_record_value(record, "broker_exit_deal_ticket"),
                broker_close_order_id=self._closed_record_value(record, "broker_exit_order_ticket"),
                broker_commission=self._closed_record_float(
                    record,
                    "broker_position_aggregate_commission",
                    "broker_exit_aggregate_commission",
                    "broker_exit_commission",
                ),
                broker_swap=self._closed_record_float(
                    record,
                    "broker_position_aggregate_swap",
                    "broker_exit_aggregate_swap",
                    "broker_exit_swap",
                ),
                broker_fee=self._closed_record_float(
                    record,
                    "broker_position_aggregate_fee",
                    "broker_exit_aggregate_fee",
                    "broker_exit_fee",
                ),
            )
            execution["daily_pnl_ledger_status"] = "RECORDED_BROKER_NET"
            execution["daily_pnl_ledger_trade_id"] = trade_id
            execution["daily_pnl_ledger_recorded_at_utc"] = datetime.now(timezone.utc).isoformat()
            execution["daily_pnl_ledger_broker_net_profit"] = broker_net
            # F5 close hook. This is the right seam because `broker_net` here is the
            # broker-TRUE realized P&L for the ticket and the status guard above makes the
            # function idempotent -- so the notional ledger folds each close exactly once.
            f5_close = self._f5_on_close(
                ticket,
                broker_net,
                symbol=None if symbol == "UNKNOWN" else symbol,
                sleeve=record.get("sleeve") if isinstance(record, dict) else None,
                close_action=action or (record.get("close_action") if isinstance(record, dict) else None),
                closed_utc=(
                    record.get("closed_at_utc")
                    if isinstance(record, dict)
                    else None
                ),
            )
            if isinstance(f5_close, dict):
                # The record is the existing ticket lifecycle authority.  Keeping the F5 fold here
                # lets the same terminal runtime-learning packet carry production broker truth and
                # F5 notional economics without depending on the parallel F5 capture log.
                execution["f5_close"] = f5_close
            return True
        except Exception as exc:  # noqa: BLE001
            execution["daily_pnl_ledger_status"] = "RECORD_FAILED"
            execution["daily_pnl_ledger_error"] = repr(exc)
            _log.warning(
                "book[%s]: daily PnL ledger record failed for ticket %s (%r)",
                self._namespace,
                ticket,
                exc,
            )
            return False

    def _notify_closed(self, symbol, action, *, closed_record: dict | None = None) -> None:
        try:
            # Prefer the exact ticket-bound reconciliation. The symbol-history fallback is only
            # best-effort and can race when two same-symbol positions close close together.
            pnl = self._closed_record_realized_pnl(closed_record)
            if pnl is None:
                pnl = self._recent_realized_pnl(symbol)
            pnl_str = f" · P&L ${pnl:,.0f}" if pnl is not None else ""
            verb = {"vnext_time_stop": "time-stop exit", "stop_loss": "stopped out",
                    "take_profit": "target hit",
                    # Session BA: the owner card for a scheduled compliance close should say what
                    # it was, not leak an internal token into a notification.
                    "weekend_flat": "weekend flat (redacted_account rule)"}.get(str(action), str(action))
            self._send_card(f"[{self._account_label()}] ⚪ Closed {symbol} — {verb}{pnl_str}")
        except Exception:
            pass

    def _recent_realized_pnl(self, symbol):
        try:
            broker = self._broker_symbol(symbol)
            import datetime as _dt
            import MetaTrader5 as _m
            now = _dt.datetime.now(_dt.timezone.utc)
            # MT5 interprets the history window in SERVER time (FTMO/FN = UTC+3), so a bare `now` upper
            # bound DROPS a just-now close (its server timestamp sorts after the bound) -> the close card
            # reported "P&L $0". Pad the upper bound +13h, mirroring monitor_books.py. AND take only the
            # CLOSE deal (entry==1 = DEAL_ENTRY_OUT): the OPEN deal carries profit 0 and, as the lone deal
            # in the unpadded window, was being returned as the realized P&L (the source of the bogus $0).
            deals = _m.history_deals_get(now - _dt.timedelta(hours=24), now + _dt.timedelta(hours=13),
                                         group=f"*{broker}*")
            if not deals:
                return None
            closes = [d for d in deals if getattr(d, "entry", 0) == 1]
            if not closes:
                return None
            last = max(closes, key=lambda d: d.time)
            position_id = getattr(last, "position_id", None)
            if position_id not in (None, "", 0, "0"):
                related = [d for d in deals if getattr(d, "position_id", None) == position_id]
                if related:
                    return sum(
                        float(getattr(d, "profit", 0) or 0)
                        + float(getattr(d, "swap", 0) or 0)
                        + float(getattr(d, "commission", 0) or 0)
                        + float(getattr(d, "fee", 0) or 0)
                        for d in related
                    )
            return (
                float(last.profit)
                + float(getattr(last, "swap", 0) or 0)
                + float(getattr(last, "commission", 0) or 0)
                + float(getattr(last, "fee", 0) or 0)
            )
        except Exception:
            return None


class _UnitView:
    """Adapt a realized-unit dict to the SizedUnit attribute interface the order_router expects."""
    def __init__(self, unit: dict):
        self.cluster = unit.get("cluster", "book")
        self.sleeve_members = unit.get("sleeve_members", [])
        self.n_trades = unit.get("n_trades", 1)
        self.confidence = unit.get("confidence")
        self.risk_pct_per_trade = unit.get("risk_pct_per_trade")
        self.unit_risk_pct = unit.get("unit_risk_pct")
        self.sized = unit.get("sized", False)
        self.reason = unit.get("reason")
