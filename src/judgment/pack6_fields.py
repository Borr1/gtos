"""Instrument Edge PACK 6 — XAU DSP shakeout A+ PROVE_SEED.

``sleeve.xau_dsp_shakeout_a_plus_ready`` SHADOW Choice.

On the Challenge writer the mute and the sleeve choice are one ask.
An empty answer leaves both unset. Off that writer the recorded
prove-seed comparison stays. Not an admit Choice.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Mapping

from .fluid_gates import lookup

REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA = "gtos.judgment.aplus_pack6_fields.v0"
ORIGIN = "instrument_edge_pack6_prove_seed_20260918"
EDGE = "PACK 6"
STATE_PATH = "pack6_fields"
CHOICE_ID = "sleeve.xau_dsp_shakeout_a_plus_ready"
SETUP_XAU = "xau_dsp_shakeout"
SEED_TICKET = 293611741

PACK6_FIELD_IDS = (CHOICE_ID,)

A_PLUS = "a_plus"
ALMOST = "almost"
BLOCKED = "blocked"
NULL_STATE = "null_state"
CHOICE_ANSWERS = frozenset({A_PLUS, ALMOST, BLOCKED, NULL_STATE})
ADMIT_ANSWERS = frozenset({"admit", "abstain", "hard_refuse"})
NEVER_WRITE_QUESTIONS = frozenset({"admit"})
NEVER_WRITE_GATE_IDS = frozenset({"FLUID-ADM-007", "UB-AUTH-010"})
ALLOWED_FAMILIES = frozenset({"admit", "size", "news_window"})

BOJ_WARSH = frozenset({"boj", "warsh", "fomc", "nfp", "cpi", "boe", "guidance_live", "print"})
BOJ_PRINT_GUIDANCE = frozenset({"print", "guidance_live"})
MUTE_CLOSE_ABS = 60
MUTE_FILL_LO = -90
MUTE_FILL_HI = 60
WARSH_T60 = 60
N_IN = 3
PROVE_SEED_IDS = ("S0", "S1", "S2", "S3", "S4", "S5")
REVISED_IDS = ("S0", "S1", "S2", "S3", "S4", "S5", "S6")
REVISED_MUTE_LOCK = "close∈boj/warsh T±60 OR fill∈T−90..T+60"
HONESTY = "prove_seed_n_in_3"

SLEEVE_ATTACH_MAP: dict[str, dict[str, Any]] = {
    SETUP_XAU: {
        "setup_id": SETUP_XAU,
        "symbol": "XAUUSD",
        "implemented": True,
        "status": "implemented",
        "choice": CHOICE_ID,
        "prove_seed": True,
        "seed_ticket": SEED_TICKET,
        "n_in": N_IN,
        "honesty": HONESTY,
        "prove_seed_ids": list(PROVE_SEED_IDS),
        "revised_ids": list(REVISED_IDS),
        "revised_mute": REVISED_MUTE_LOCK,
        "fill_in_any_high_alone_mutes": False,
        "hypothesis_mute": "boj∈{print,guidance_live} OR Warsh T±60",
        "state_paths": {
            "edge": EDGE,
            "schema": SCHEMA,
            "pack6": STATE_PATH,
            "aplus": "aplus.pack6_fields",
            "choice": f"{STATE_PATH}.fields.{CHOICE_ID}",
        },
        "never_admit": True,
        "never_refuse": True,
        "never_apply_size": True,
        "shadow_only": True,
        "freeze": "judgment/astra/XAU_DSP_SHAKEOUT_EVENT_GAP.md",
    },
}

PACK6_FIELD_SPEC: dict[str, dict[str, Any]] = {
    CHOICE_ID: {
        "surface": "choice",
        "kind": "choice",
        "applies_setups": (SETUP_XAU,),
        "applies_symbols": ("XAUUSD",),
        "families": ("admit", "size", "news_window"),
        "never_invent": ("DXY", "funding", "peer_ohlc", "boj_high"),
        "never_admit": True,
        "never_write_questions": tuple(sorted(NEVER_WRITE_QUESTIONS)),
        "never_write_gate_ids": tuple(sorted(NEVER_WRITE_GATE_IDS)),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "event_proximity", "ids": ("FLUID-NWS-001",)},
            {"question": "high_in_f5_window", "ids": ("FLUID-NWS-002",)},
            {"question": "warsh_class", "ids": ("FLUID-NWS-004",)},
            {"question": "event_size", "ids": ("FLUID-SIZ-006",)},
        ),
        "criteria": {
            A_PLUS: "The structure on the card is the sleeve and the event does not mute it.",
            ALMOST: "The structure is present and the event is not assembled.",
            BLOCKED: "The event mutes this sleeve, or the seed state blocks it.",
            NULL_STATE: "Event or structure is not assembled.",
        },
        "role": "XAU DSP shakeout A+ PROVE_SEED. SHADOW. Not admit.",
    },
}


def _norm_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper().replace(" ", "")


def field_applies(field_id: str, *, setup_id: str | None, symbol: str) -> bool:
    spec = PACK6_FIELD_SPEC[field_id]
    if setup_id and str(setup_id) in spec["applies_setups"]:
        return True
    return _norm_symbol(symbol) in {_norm_symbol(s) for s in spec["applies_symbols"]} and str(
        setup_id or ""
    ).startswith("xau_dsp")


def pack6_gate_map() -> list[dict[str, Any]]:
    spec = PACK6_FIELD_SPEC[CHOICE_ID]
    return [
        {
            "field": CHOICE_ID,
            "surface": spec["surface"],
            "kind": spec["kind"],
            "families": list(spec["families"]),
            "gate_questions": [g["question"] for g in spec["gate_inputs"]],
            "gate_ids": [gid for g in spec["gate_inputs"] for gid in g["ids"]],
            "never_admit": True,
            "never_write_questions": list(spec["never_write_questions"]),
            "never_write_gate_ids": list(spec["never_write_gate_ids"]),
            "criteria": dict(spec["criteria"]),
            "shadow_only": True,
            "never_refuse": True,
            "never_apply_size": True,
            "n_in": N_IN,
            "edge": EDGE,
        }
    ]


def assert_pack6_maps_existing_families() -> dict[str, Any]:
    bad: list[str] = []
    for row in pack6_gate_map():
        if "admit" in row["gate_questions"]:
            bad.append("wrote_question:admit")
        for gid in row["gate_ids"]:
            if gid in NEVER_WRITE_GATE_IDS:
                bad.append(f"wrote_gate:{gid}")
            gate = lookup(gid)
            if gate is None:
                bad.append(f"missing:{gid}")
            elif str(gate.get("family") or "") not in ALLOWED_FAMILIES:
                bad.append(f"family:{gid}:{gate.get('family')}")
        for answer in row["criteria"]:
            if answer in ADMIT_ANSWERS:
                bad.append(f"admit_answer:{answer}")
    return {"ok": not bad, "bad": bad, "never_admit": True, "n_in": N_IN}


_ASK_CACHE: dict[str, dict[str, Any]] = {}
_ASK_LOCK = threading.Lock()


def _challenge() -> bool:
    try:
        from .state_choices import on_challenge
    except Exception:
        return False
    try:
        return bool(on_challenge())
    except Exception:
        return False


def _pack6_ask(facts: dict[str, Any]) -> dict[str, Any]:
    """One post: the mute noul and the sleeve choice. Empty leaves both unset."""
    blob = json.dumps(facts, sort_keys=True, default=str)
    with _ASK_LOCK:
        cached = _ASK_CACHE.get(blob)
    if cached is not None:
        return dict(cached)
    missed = {"mute": None, "choice": None}
    try:
        from .jev_client import evaluate
        from .jev_questions import unique_highest
    except Exception:
        return dict(missed)
    choice_id = CHOICE_ID
    mute_id = "pack6.event_mute"
    criteria = dict(PACK6_FIELD_SPEC[CHOICE_ID]["criteria"])
    questions = {
        mute_id: {
            "type": "noul",
            "instructions": (
                "Does this event mute the sleeve? "
                "The event class and the minute distances are facts. "
                "An empty answer leaves the mute unset. Do not send."
            ),
            "criteria": {
                "true": "The event mutes the sleeve.",
                "false": "The event does not mute the sleeve.",
            },
        },
        choice_id: {
            "type": "choice",
            "instructions": (
                "The structure and the event are on the card. "
                "The unique highest sleeve state is the decision. "
                "An empty answer or a tie leaves the choice unset. "
                "Do not admit. Do not send."
            ),
            "criteria": {str(key): str(text) for key, text in criteria.items()},
        },
    }
    try:
        receipt = evaluate(
            {"facts": facts, "order_send": False, "flatten": False},
            questions=questions,
            merge_sleeve=False,
            model="jev-1.13.0",
        )
    except Exception:
        return dict(missed)
    answers = receipt.get("answers") if isinstance(receipt, dict) else None
    if not isinstance(answers, dict):
        answers = {}
    mute_block = answers.get(mute_id) if isinstance(answers.get(mute_id), dict) else {}
    mute = mute_block.get("noul") if isinstance(mute_block, dict) else None
    if mute is not True and mute is not False:
        mute = None
    choice_block = answers.get(choice_id) if isinstance(answers.get(choice_id), dict) else {}
    probs = choice_block.get("probabilities") if isinstance(choice_block, dict) else None
    try:
        picked = unique_highest(probs if isinstance(probs, dict) else None, tuple(criteria))
    except Exception:
        picked = None
    row = {"mute": mute, "choice": picked}
    with _ASK_LOCK:
        _ASK_CACHE[blob] = dict(row)
    return row


def hypothesis_mute(
    *,
    event_class: str | None = None,
    fill_mins: int | None = None,
    close_mins: int | None = None,
) -> dict[str, Any]:
    """Mute hypothesis. On Challenge the noul is the return."""
    if _challenge():
        got = _pack6_ask(
            {
                "event_class": event_class,
                "fill_mins": fill_mins,
                "close_mins": close_mins,
            }
        )
        return {"mute": got.get("mute"), "reason": None, "hypothesis": "pack6"}
    klass = str(event_class or "").strip().lower()
    if klass in BOJ_PRINT_GUIDANCE:
        return {
            "mute": True,
            "reason": "boj_print_or_guidance_live",
            "hypothesis": "pack6_prove_seed",
        }
    mins = close_mins if close_mins is not None else fill_mins
    if klass == "warsh" and mins is not None and abs(int(mins)) <= WARSH_T60:
        return {
            "mute": True,
            "reason": "warsh_t60",
            "hypothesis": "pack6_prove_seed",
        }
    return {"mute": False, "reason": None, "hypothesis": "pack6_prove_seed"}


def event_mute(
    *,
    fill_mins: int | None = None,
    close_mins: int | None = None,
    event_class: str | None = None,
    fill_in_any_high: bool = False,
) -> dict[str, Any]:
    """Window mute. On Challenge the noul is the return. Empty does not mute."""
    if _challenge():
        got = _pack6_ask(
            {
                "event_class": event_class,
                "fill_mins": fill_mins,
                "close_mins": close_mins,
                "fill_in_any_high": bool(fill_in_any_high),
            }
        )
        return {
            "mute": got.get("mute"),
            "reason": None,
            "fill_in_any_high": bool(fill_in_any_high),
            "fill_in_any_high_alone_mutes": None,
        }
    hyp = hypothesis_mute(
        event_class=event_class,
        fill_mins=fill_mins,
        close_mins=close_mins,
    )
    if hyp["mute"] and hyp["reason"] == "boj_print_or_guidance_live":
        return {
            "mute": True,
            "reason": hyp["reason"],
            "fill_in_any_high": bool(fill_in_any_high),
            "fill_in_any_high_alone_mutes": False,
            "hypothesis": hyp["hypothesis"],
        }
    klass = str(event_class or "").strip().lower()
    warshish = klass in BOJ_WARSH
    if close_mins is not None and warshish and abs(int(close_mins)) <= MUTE_CLOSE_ABS:
        return {
            "mute": True,
            "reason": "close_in_boj_warsh_t60",
            "fill_in_any_high": bool(fill_in_any_high),
            "fill_in_any_high_alone_mutes": False,
        }
    if fill_mins is not None and warshish and MUTE_FILL_LO <= int(fill_mins) <= MUTE_FILL_HI:
        return {
            "mute": True,
            "reason": "fill_in_boj_warsh_t90_t60",
            "fill_in_any_high": bool(fill_in_any_high),
            "fill_in_any_high_alone_mutes": False,
        }
    return {
        "mute": False,
        "reason": None,
        "fill_in_any_high": bool(fill_in_any_high),
        "fill_in_any_high_alone_mutes": False,
    }


def score_shakeout(
    *,
    structure_ok: bool | None,
    fill_mins: int | None = None,
    close_mins: int | None = None,
    event_class: str | None = None,
    fill_in_any_high: bool = False,
    seed_blocked: bool = False,
) -> dict[str, Any]:
    if _challenge():
        got = _pack6_ask(
            {
                "structure_ok": structure_ok,
                "fill_mins": fill_mins,
                "close_mins": close_mins,
                "event_class": event_class,
                "fill_in_any_high": bool(fill_in_any_high),
                "seed_blocked": bool(seed_blocked),
            }
        )
        return {
            "type": "choice",
            "choice": got.get("choice"),
            "fail_reason": None,
            "mute": {
                "mute": got.get("mute"),
                "reason": None,
                "fill_in_any_high": bool(fill_in_any_high),
                "fill_in_any_high_alone_mutes": None,
            },
            "structure_ok": structure_ok,
            "criteria": dict(PACK6_FIELD_SPEC[CHOICE_ID]["criteria"]),
            "never_admit": True,
            "never_refuse": True,
            "never_apply_size": True,
            "shadow_only": True,
            "invented": False,
            "edge": EDGE,
        }
    mute = event_mute(
        fill_mins=fill_mins,
        close_mins=close_mins,
        event_class=event_class,
        fill_in_any_high=fill_in_any_high,
    )
    if seed_blocked or mute["mute"]:
        choice = BLOCKED
        reason = "seed_s0" if seed_blocked and not mute["mute"] else mute["reason"] or "seed_s0"
    elif structure_ok is True and not mute["mute"]:
        choice, reason = A_PLUS, None
    elif structure_ok is True and event_class is None:
        choice, reason = ALMOST, "event_unassembled"
    else:
        choice, reason = NULL_STATE, "unassembled"
    return {
        "type": "choice",
        "choice": choice,
        "fail_reason": reason,
        "mute": mute,
        "structure_ok": structure_ok,
        "criteria": dict(PACK6_FIELD_SPEC[CHOICE_ID]["criteria"]),
        "never_admit": True,
        "never_refuse": True,
        "never_apply_size": True,
        "shadow_only": True,
        "invented": False,
        "n_in": N_IN,
        "edge": EDGE,
    }


# S0 = live ticket 293611741. Fill 2026-09-18T01:45:50Z.
# Named Warsh 15 min after fill → fill ∈ T−90..T+60 → mute → blocked.
# S4: FILL_IN_ANY_HIGH alone, event not boj/warsh → not mute.
_S0 = {
    "id": "S0",
    "ticket": SEED_TICKET,
    "symbol": "XAUUSD",
    "sleeve": "dsp_shakeout_holds_run_lows",
    "fill_utc": "2026-09-18T01:45:50Z",
    "structure_ok": True,
    "event_class": "warsh",
    "fill_mins": -15,
    "close_mins": None,
    "fill_in_any_high": True,
    "seed_blocked": False,
    "expect": BLOCKED,
    "expect_reason": "fill_in_boj_warsh_t90_t60",
    "in_n": True,
}
_S1 = {
    "id": "S1",
    "symbol": "XAUUSD",
    "structure_ok": True,
    "event_class": None,
    "fill_mins": None,
    "close_mins": None,
    "fill_in_any_high": False,
    "expect": A_PLUS,
    "expect_reason": None,
    "in_n": True,
}
_S2 = {
    "id": "S2",
    "symbol": "XAUUSD",
    "structure_ok": True,
    "event_class": "other_high",
    "fill_mins": 180,
    "close_mins": 180,
    "fill_in_any_high": False,
    "expect": A_PLUS,
    "expect_reason": None,
    "in_n": True,
}
_S3 = {
    "id": "S3",
    "symbol": "XAUUSD",
    "structure_ok": None,
    "event_class": None,
    "fill_mins": None,
    "close_mins": None,
    "fill_in_any_high": False,
    "expect": NULL_STATE,
    "expect_reason": "unassembled",
    "in_n": False,
}
_S4 = {
    "id": "S4",
    "symbol": "XAUUSD",
    "structure_ok": True,
    "event_class": "other_high",
    "fill_mins": 10,
    "close_mins": None,
    "fill_in_any_high": True,
    "expect": A_PLUS,
    "expect_reason": None,
    "in_n": False,
    "note": "FILL_IN_ANY_HIGH alone does not mute",
}
_S5 = {
    "id": "S5",
    "symbol": "XAUUSD",
    "structure_ok": True,
    "event_class": "boj",
    "fill_mins": None,
    "close_mins": 20,
    "fill_in_any_high": False,
    "expect": BLOCKED,
    "expect_reason": "close_in_boj_warsh_t60",
    "in_n": False,
}
_S6 = {
    "id": "S6",
    "symbol": "XAUUSD",
    "structure_ok": True,
    "event_class": "fomc",
    "fill_mins": -40,
    "close_mins": None,
    "fill_in_any_high": False,
    "expect": BLOCKED,
    "expect_reason": "fill_in_boj_warsh_t90_t60",
    "in_n": False,
}

XAU_SHAKEOUT_FIXTURES: dict[str, dict[str, Any]] = {
    "S0": dict(_S0),
    "S1": dict(_S1),
    "S2": dict(_S2),
    "S3": dict(_S3),
    "S4": dict(_S4),
    "S5": dict(_S5),
    "S6": dict(_S6),
}


def shakeout_fixture(vector_id: str) -> dict[str, Any]:
    row = XAU_SHAKEOUT_FIXTURES.get(str(vector_id).upper())
    if row is None:
        raise KeyError(vector_id)
    return dict(row)


def score_xau_dsp_shakeout(vector: str | Mapping[str, Any]) -> dict[str, Any]:
    vec = shakeout_fixture(vector) if isinstance(vector, str) else dict(vector)
    scored = score_shakeout(
        structure_ok=vec.get("structure_ok"),
        fill_mins=vec.get("fill_mins"),
        close_mins=vec.get("close_mins"),
        event_class=vec.get("event_class"),
        fill_in_any_high=bool(vec.get("fill_in_any_high")),
        seed_blocked=bool(vec.get("seed_blocked")),
    )
    matches = scored["choice"] == vec.get("expect") and scored["fail_reason"] == vec.get("expect_reason")
    return {
        "id": vec.get("id"),
        "ticket": vec.get("ticket"),
        "symbol": "XAUUSD",
        "setup_id": SETUP_XAU,
        "choice": scored["choice"],
        "fail_reason": scored["fail_reason"],
        "mute": scored["mute"],
        "expected_choice": vec.get("expect"),
        "expected_fail_reason": vec.get("expect_reason"),
        "matches_lock": matches,
        "in_n": bool(vec.get("in_n")),
        "n_in": N_IN,
        "honesty": HONESTY,
        "never_admit": True,
        "never_refuse": True,
        "shadow_only": True,
        "edge": EDGE,
    }


def assemble_pack6_fields(
    *,
    symbol: str,
    setup_id: str | None = None,
    pack6_values: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    supplied = dict(pack6_values or {})
    applies = field_applies(CHOICE_ID, setup_id=setup_id, symbol=symbol)
    if supplied.get("fixture"):
        scored = score_xau_dsp_shakeout(supplied["fixture"])
        payload = {
            "type": "choice",
            "choice": scored["choice"],
            "fail_reason": scored["fail_reason"],
            "mute": scored["mute"],
            "ticket": scored.get("ticket"),
            "never_admit": True,
            "never_refuse": True,
            "n_in": N_IN,
            "edge": EDGE,
        }
    else:
        payload = score_shakeout(
            structure_ok=supplied.get("structure_ok"),
            fill_mins=supplied.get("fill_mins"),
            close_mins=supplied.get("close_mins"),
            event_class=supplied.get("event_class"),
            fill_in_any_high=bool(supplied.get("fill_in_any_high")),
            seed_blocked=bool(supplied.get("seed_blocked")),
        )
    assembled = applies and payload["choice"] in {A_PLUS, ALMOST, BLOCKED}
    row = {
        "id": CHOICE_ID,
        "surface": "choice",
        "kind": "choice",
        "applies": applies,
        "assembled": bool(applies and assembled),
        "value": payload if applies else None,
        "source": STATE_PATH if applies else "not_applicable",
        "invented": False,
        "shadow_only": True,
        "never_apply_size": True,
        "never_refuse": True,
        "never_admit": True,
        "never_write_questions": list(NEVER_WRITE_QUESTIONS),
        "never_write_gate_ids": list(NEVER_WRITE_GATE_IDS),
        "choice": payload["choice"] if applies else None,
        "fail_reason": payload.get("fail_reason") if applies else None,
        "setup_id": setup_id,
        "n_in": N_IN,
        "honesty": HONESTY,
        "edge": EDGE,
    }
    if not applies:
        row["assembled"] = False
        row["value"] = None
    missing = [f"{STATE_PATH}.{CHOICE_ID}"] if applies and not row["assembled"] else []
    return {
        "schema": SCHEMA,
        "origin": ORIGIN,
        "edge": EDGE,
        "state_path": STATE_PATH,
        "shadow_only": True,
        "never_apply_size": True,
        "never_refuse": True,
        "never_admit": True,
        "n": 1,
        "ids": list(PACK6_FIELD_IDS),
        "fields": {CHOICE_ID: row},
        "n_applies": int(applies),
        "n_assembled": int(row["assembled"]),
        "invented": False,
        "missing_fields": missing,
        "attach": SLEEVE_ATTACH_MAP.get(SETUP_XAU) if applies else None,
        "choice": row.get("choice"),
        "setup_id": setup_id,
        "n_in": N_IN,
        "honesty": HONESTY,
        "seed_ticket": SEED_TICKET,
        "prove_seed_ids": list(PROVE_SEED_IDS),
        "revised_ids": list(REVISED_IDS),
        "revised_mute": REVISED_MUTE_LOCK,
        "fill_in_any_high_alone_mutes": (
            payload.get("mute", {}).get("fill_in_any_high_alone_mutes")
            if isinstance(payload.get("mute"), dict)
            else None
        ),
    }


PROVE_SEED_FIXTURES: dict[str, dict[str, Any]] = {
    vec_id: dict(XAU_SHAKEOUT_FIXTURES[vec_id]) for vec_id in PROVE_SEED_IDS
}

HYPOTHESIS_MUTE_LOCK = "boj∈{print,guidance_live} OR Warsh T±60"
LAND_NOTE = "judgment/astra/lab/wires/HOST_APLUS_SLEEVES_LAND.md"
XAU_FREEZE_DOC = "judgment/astra/XAU_DSP_SHAKEOUT_EVENT_GAP.md"


def _repo_doc(rel: str) -> Path:
    """Repo-root path so utf-8 reads do not depend on cwd."""
    return REPO_ROOT / rel


def assert_pack6_prove_seed() -> dict[str, Any]:
    """Pin PROVE_SEED S0–S5, S0=293611741 blocked, n_in=3 honesty. No admit."""
    bad: list[str] = []
    if PROVE_SEED_IDS != ("S0", "S1", "S2", "S3", "S4", "S5"):
        bad.append(f"prove_seed_ids:{PROVE_SEED_IDS}")
    if "S6" in PROVE_SEED_IDS:
        bad.append("s6_in_prove_seed")
    if N_IN != 3:
        bad.append(f"n_in:{N_IN}")
    if HONESTY != "prove_seed_n_in_3":
        bad.append(f"honesty:{HONESTY}")
    if SEED_TICKET != 293611741:
        bad.append(f"ticket:{SEED_TICKET}")
    attach = SLEEVE_ATTACH_MAP[SETUP_XAU]
    if attach.get("n_in") != N_IN or attach.get("honesty") != HONESTY:
        bad.append("attach_honesty")
    if attach.get("never_admit") is not True:
        bad.append("admit_open")
    if attach.get("hypothesis_mute") != HYPOTHESIS_MUTE_LOCK:
        bad.append(f"hypothesis_mute:{attach.get('hypothesis_mute')}")
    if list(attach.get("prove_seed_ids") or []) != list(PROVE_SEED_IDS):
        bad.append("attach_ids")
    if set(PROVE_SEED_FIXTURES) != set(PROVE_SEED_IDS):
        bad.append("fixtures")
    in_n = [vec_id for vec_id in PROVE_SEED_IDS if XAU_SHAKEOUT_FIXTURES[vec_id]["in_n"]]
    if in_n != ["S0", "S1", "S2"]:
        bad.append(f"in_n:{in_n}")
    s0 = score_xau_dsp_shakeout("S0")
    if s0.get("ticket") != SEED_TICKET or s0.get("choice") != BLOCKED:
        bad.append("s0")
    if s0.get("fail_reason") != "fill_in_boj_warsh_t90_t60":
        bad.append(f"s0_reason:{s0.get('fail_reason')}")
    for vec_id in PROVE_SEED_IDS:
        scored = score_xau_dsp_shakeout(vec_id)
        if not scored["matches_lock"]:
            bad.append(f"lock:{vec_id}")
        if scored.get("never_admit") is not True:
            bad.append(f"admit:{vec_id}")
    print_m = hypothesis_mute(event_class="print")
    guid_m = hypothesis_mute(event_class="guidance_live")
    warsh_m = hypothesis_mute(event_class="warsh", fill_mins=-15)
    if not print_m["mute"] or print_m["reason"] != "boj_print_or_guidance_live":
        bad.append("hyp_print")
    if not guid_m["mute"] or guid_m["reason"] != "boj_print_or_guidance_live":
        bad.append("hyp_guidance")
    if not warsh_m["mute"] or warsh_m["reason"] != "warsh_t60":
        bad.append("hyp_warsh")
    ev_print = event_mute(event_class="print")
    if not ev_print["mute"] or ev_print["reason"] != "boj_print_or_guidance_live":
        bad.append("event_print")
    ev_guid = event_mute(event_class="guidance_live")
    if not ev_guid["mute"] or ev_guid["reason"] != "boj_print_or_guidance_live":
        bad.append("event_guidance")
    ev_s0 = event_mute(event_class="warsh", fill_mins=-15, fill_in_any_high=True)
    if ev_s0.get("reason") != "fill_in_boj_warsh_t90_t60":
        bad.append(f"s0_event:{ev_s0.get('reason')}")
    mapped = assert_pack6_maps_existing_families()
    if not mapped["ok"]:
        bad.append(f"families:{mapped['bad']}")
    land = _repo_doc(LAND_NOTE)
    freeze = _repo_doc(XAU_FREEZE_DOC)
    if not land.is_file():
        bad.append("missing_land")
    else:
        text = land.read_text(encoding="utf-8")
        for needle in ("n_in=3", "S0/S1/S2", "293611741", "print", "guidance_live", "Warsh"):
            if needle not in text:
                bad.append(f"land:{needle}")
    if not freeze.is_file():
        bad.append("missing_freeze")
    else:
        text = freeze.read_text(encoding="utf-8")
        for needle in ("n_in=3", "293611741", CHOICE_ID, "S0", "S1", "S2"):
            if needle not in text:
                bad.append(f"freeze:{needle}")
    return {
        "ok": not bad,
        "bad": bad,
        "choice": CHOICE_ID,
        "prove_seed_ids": list(PROVE_SEED_IDS),
        "in_n": in_n,
        "n_in": N_IN,
        "honesty": HONESTY,
        "seed_ticket": SEED_TICKET,
        "hypothesis_mute": HYPOTHESIS_MUTE_LOCK,
        "never_admit": True,
        "shadow_only": True,
        "edge": EDGE,
    }


def assert_pack6_revised_mute() -> dict[str, Any]:
    """Pin revised window mute on S0–S6. Prefer close, then fill. FILL_IN_ANY_HIGH alone is not mute."""
    bad: list[str] = []
    if tuple(XAU_SHAKEOUT_FIXTURES) != REVISED_IDS:
        bad.append(f"revised_ids:{tuple(XAU_SHAKEOUT_FIXTURES)}")
    if "S6" not in XAU_SHAKEOUT_FIXTURES:
        bad.append("missing_s6")
    attach = SLEEVE_ATTACH_MAP[SETUP_XAU]
    if list(attach.get("revised_ids") or []) != list(REVISED_IDS):
        bad.append("attach_revised_ids")
    if attach.get("revised_mute") != REVISED_MUTE_LOCK:
        bad.append(f"attach_mute:{attach.get('revised_mute')}")
    if attach.get("fill_in_any_high_alone_mutes") is not False:
        bad.append("attach_fill_in_any_high")
    if attach.get("never_admit") is not True or attach.get("prove_seed") is not True:
        bad.append("attach_flags")
    in_n = [vec_id for vec_id, row in XAU_SHAKEOUT_FIXTURES.items() if row.get("in_n")]
    if in_n != ["S0", "S1", "S2"] or N_IN != 3:
        bad.append(f"honesty:{in_n}:{N_IN}")
    for vec_id in REVISED_IDS:
        scored = score_xau_dsp_shakeout(vec_id)
        if not scored["matches_lock"]:
            bad.append(f"lock:{vec_id}")
        if scored.get("never_admit") is not True:
            bad.append(f"admit:{vec_id}")
    s0 = score_xau_dsp_shakeout("S0")
    if s0.get("ticket") != SEED_TICKET or s0.get("fail_reason") != "fill_in_boj_warsh_t90_t60":
        bad.append(f"s0:{s0.get('fail_reason')}")
    s4 = event_mute(fill_mins=10, event_class="other_high", fill_in_any_high=True)
    if s4["mute"] or s4["fill_in_any_high_alone_mutes"] or score_xau_dsp_shakeout("S4")["choice"] != A_PLUS:
        bad.append("s4_fill_in_any_high")
    s5 = score_xau_dsp_shakeout("S5")
    if s5.get("fail_reason") != "close_in_boj_warsh_t60":
        bad.append(f"s5:{s5.get('fail_reason')}")
    s6 = score_xau_dsp_shakeout("S6")
    if s6.get("choice") != BLOCKED or s6.get("fail_reason") != "fill_in_boj_warsh_t90_t60":
        bad.append(f"s6:{s6.get('fail_reason')}")
    if event_mute(fill_in_any_high=True)["mute"]:
        bad.append("fill_in_any_high_alone")
    prefer = event_mute(event_class="warsh", fill_mins=-15, close_mins=20)
    if prefer.get("reason") != "close_in_boj_warsh_t60":
        bad.append(f"prefer_close:{prefer.get('reason')}")
    seed = assert_pack6_prove_seed()
    if not seed["ok"]:
        bad.append(f"prove_seed:{seed['bad']}")
    land = _repo_doc(LAND_NOTE)
    freeze = _repo_doc(XAU_FREEZE_DOC)
    if land.is_file():
        text = land.read_text(encoding="utf-8")
        for needle in ("S0–S6", "S6", "FILL_IN_ANY_HIGH", "T−90..T+60", "T±60"):
            if needle not in text:
                bad.append(f"land:{needle}")
    else:
        bad.append("missing_land")
    if freeze.is_file():
        text = freeze.read_text(encoding="utf-8")
        for needle in ("S6", "FILL_IN_ANY_HIGH", "fill_in_boj_warsh_t90_t60"):
            if needle not in text:
                bad.append(f"freeze:{needle}")
    else:
        bad.append("missing_freeze")
    return {
        "ok": not bad,
        "bad": bad,
        "choice": CHOICE_ID,
        "revised_ids": list(REVISED_IDS),
        "revised_mute": REVISED_MUTE_LOCK,
        "fill_in_any_high_alone_mutes": False,
        "prefer_close": True,
        "n_in": N_IN,
        "honesty": HONESTY,
        "never_admit": True,
        "shadow_only": True,
        "prove_seed": True,
        "edge": EDGE,
    }
