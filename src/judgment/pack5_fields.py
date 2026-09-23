"""Instrument Edge PACK 5 — Chair-canon GBPJPY A+ Choice.

``sleeve.gbpjpy_a_plus_ready`` ∈ {a_plus, almost, blocked, null_state}.

On the Challenge writer the choice is the ask. An empty answer leaves it
unset. Off that writer the recorded conjuncts stay for research.
SHADOW only. Not an admit Choice. No new refuse walls.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fluid_gates import lookup
from .pack3_fields import (
    GBPJPY_FIXTURE_VECTORS as PACK3_GBPJPY_VECTORS,
    assemble_pack3_fields,
    gbpjpy_fixture,
    values_from_gbpjpy_fixture,
)
from .pack4_fields import (
    BOJ_BLOCK,
    CONJUNCTS,
    SETUP_GBPJPY,
    assemble_pack4_fields,
    pack4_values_from_gbpjpy_fixture,
    score_readiness,
)

SCHEMA = "gtos.judgment.aplus_pack5_fields.v0"
ORIGIN = "instrument_edge_pack5_20260918"
EDGE = "PACK 5"
STATE_PATH = "pack5_fields"
CHOICE_ID = "sleeve.gbpjpy_a_plus_ready"

PACK5_FIELD_IDS = (CHOICE_ID,)

A_PLUS = "a_plus"
ALMOST = "almost"
BLOCKED = "blocked"
NULL_STATE = "null_state"
CHOICE_ANSWERS = frozenset({A_PLUS, ALMOST, BLOCKED, NULL_STATE})
ADMIT_ANSWERS = frozenset({"admit", "abstain", "hard_refuse"})
NEVER_WRITE_QUESTIONS = frozenset({"admit"})
NEVER_WRITE_GATE_IDS = frozenset({"FLUID-ADM-007", "UB-AUTH-010"})
ALLOWED_FAMILIES = frozenset({"admit", "size", "news_window"})
TONE_BLOCK = frozenset({"risk_off"})

# Scout-locked observe wires. SHADOW. No new refuse walls.
# Scout names (left) may differ from PACK 3 field ids (SCOUT_TIER1_ALIASES).
SCOUT_TIER1_WIRES: dict[str, tuple[str, ...]] = {
    "sess.ldn_ny_overlap_vol": ("FLUID-ADM-004", "FLUID-SIZ-003"),
    "sess.london_open_eur_gbp_expand": ("FLUID-ADM-004", "FLUID-ADM-005", "FLUID-SIZ-003"),
    "sess.ny_cash_open_us30": ("FLUID-ADM-004", "FLUID-SIZ-003"),
    "corr.eur_gbp_usd_co_move": ("FLUID-ADM-002",),
    "corr.xau_vs_eur_proxy_usd": (),  # NO WIRE — alias of usd_proxy_vs_xau
    "corr.gbpjpy_risk_cross": ("FLUID-ADM-002",),
    "macro.boj_guidance_window": ("FLUID-NWS-002", "FLUID-NWS-004", "FLUID-SIZ-006"),
}

# Scout feature name → assembled PACK 3 / Chair field id. Observe only.
SCOUT_TIER1_ALIASES: dict[str, str | None] = {
    "sess.ldn_ny_overlap_vol": "sess.ldn_ny_overlap_vol",
    "sess.london_open_eur_gbp_expand": "london_open_eur_gbp_expand",
    "sess.ny_cash_open_us30": "ny_cash_open_us30",
    "corr.eur_gbp_usd_co_move": "corr.eur_gbp_usd_co_move",
    "corr.xau_vs_eur_proxy_usd": "usd_proxy_vs_xau",  # NO WIRE
    "corr.gbpjpy_risk_cross": "corr.gbpjpy_risk_cross",
    "macro.boj_guidance_window": "macro.boj_guidance_window",
}

# Scout packet is attach-name authority. In-repo copies are the committed
# canon when the Linux-box drop is absent (Windows VPS / sibling worktree).
REPO_ROOT = Path(__file__).resolve().parents[2]
_SCOUT_ABS_DROP = Path("/workspace/gtos/_scout_packets/SLEEVE_ATTACH_MAP.md")
_SCOUT_IN_REPO = REPO_ROOT / "gtos" / "_scout_packets" / "SLEEVE_ATTACH_MAP.md"
IN_REPO_CANON_PATH = REPO_ROOT / "judgment" / "astra" / "SLEEVE_ATTACH_MAP.md"


def resolve_scout_packet_path() -> Path:
    """First existing Scout/Chair attach map. Never invent a map."""
    for path in (_SCOUT_ABS_DROP, _SCOUT_IN_REPO, IN_REPO_CANON_PATH):
        if path.is_file():
            return path
    return _SCOUT_IN_REPO


SCOUT_PACKET_PATH = resolve_scout_packet_path()
SCOUT_ATTACH_NAMES = (
    CHOICE_ID,
    "gbpjpy_dual_leg",
    "tokyo_event",
    "london_fit",
)

# Chair-canon attach aliases (Scout SLEEVE_ATTACH_MAP).
ATTACH_ALIASES: dict[str, dict[str, Any]] = {
    "gbpjpy_dual_leg": {
        "equiv": "gate.cross_stack_gbpjpy",
    },
    "tokyo_event": {
        "split": ("gate.asia_jpy_act_ok", "gate.event_boj_window"),
    },
    "london_fit": {
        "split": ("sleeve.london_expand_eur_gbp", "gate.session_overlap_ok"),
    },
    "corr.xau_vs_eur_proxy_usd": {
        "alias_of": "usd_proxy_vs_xau",
        "wire": None,
    },
}

SLEEVE_ATTACH_MAP: dict[str, dict[str, Any]] = {
    SETUP_GBPJPY: {
        "setup_id": SETUP_GBPJPY,
        "symbol": "GBPJPY",
        "implemented": True,
        "status": "implemented",
        "choice": CHOICE_ID,
        "pack4_choice": "choice.gbpjpy_aplus_ready",
        "conjuncts": list(CONJUNCTS) + ["tone_ok"],
        "boj_block_buckets": sorted(BOJ_BLOCK),
        "tone_block": sorted(TONE_BLOCK),
        "aliases": dict(ATTACH_ALIASES),
        "state_paths": {
            "edge": EDGE,
            "schema": SCHEMA,
            "pack5": STATE_PATH,
            "aplus": "aplus.pack5_fields",
            "choice": f"{STATE_PATH}.fields.{CHOICE_ID}",
        },
        "never_admit": True,
        "never_refuse": True,
        "never_apply_size": True,
        "shadow_only": True,
        "scout_attach_names": list(SCOUT_ATTACH_NAMES),
        "scout_packet": str(SCOUT_PACKET_PATH),
        "in_repo_canon": str(IN_REPO_CANON_PATH),
        "freeze": "judgment/astra/GBPJPY_APLUS_FREEZE.md",
    },
}


def resolve_attach_name(name: str) -> dict[str, Any]:
    """Map a Scout attach name onto existing SHADOW fields. Never a refuse wall."""
    key = str(name or "").strip()
    if key == CHOICE_ID:
        return {
            "name": CHOICE_ID,
            "kind": "choice",
            "targets": (CHOICE_ID,),
            "shadow_only": True,
            "never_admit": True,
            "never_refuse": True,
            "never_apply_size": True,
            "authority": "scout_sleeve_attach_map",
        }
    alias = ATTACH_ALIASES.get(key)
    if key == "gbpjpy_dual_leg" and alias:
        return {
            "name": key,
            "kind": "equiv",
            "equiv": alias["equiv"],
            "targets": (alias["equiv"],),
            "shadow_only": True,
            "never_admit": True,
            "never_refuse": True,
            "never_apply_size": True,
            "authority": "scout_sleeve_attach_map",
        }
    if key in {"tokyo_event", "london_fit"} and alias:
        return {
            "name": key,
            "kind": "split",
            "split": alias["split"],
            "targets": alias["split"],
            "shadow_only": True,
            "never_admit": True,
            "never_refuse": True,
            "never_apply_size": True,
            "authority": "scout_sleeve_attach_map",
        }
    raise KeyError(name)


def resolve_gbpjpy_attach(
    *,
    pack2: Mapping[str, Any] | None = None,
    pack5_choice: str | None = None,
) -> dict[str, Any]:
    """Resolve Chair-canon Scout names against assembled PACK 2 fields. SHADOW."""
    fields = pack2.get("fields") if isinstance(pack2, Mapping) else {}
    if not isinstance(fields, Mapping):
        fields = {}
    names: dict[str, Any] = {}
    for name in SCOUT_ATTACH_NAMES:
        spec = resolve_attach_name(name)
        if spec["kind"] == "choice":
            names[name] = {
                **spec,
                "choice": pack5_choice,
                "assembled": pack5_choice in {A_PLUS, ALMOST, BLOCKED},
            }
            continue
        if spec["kind"] == "equiv":
            target = fields.get(spec["equiv"]) or {}
            names[name] = {
                **spec,
                "assembled": bool(target.get("assembled")),
                "value": target.get("value"),
                "source_field": spec["equiv"],
            }
            continue
        parts = {}
        for fid in spec["targets"]:
            part = fields.get(fid) or {}
            parts[fid] = {"assembled": bool(part.get("assembled")), "value": part.get("value")}
        names[name] = {
            **spec,
            "parts": parts,
            "assembled": bool(parts) and all(p["assembled"] for p in parts.values()),
        }
    return {
        "authority": "scout_sleeve_attach_map",
        "scout_packet": str(SCOUT_PACKET_PATH),
        "in_repo_canon": str(IN_REPO_CANON_PATH),
        "scout_packet_present": SCOUT_PACKET_PATH.is_file(),
        "shadow_only": True,
        "never_admit": True,
        "never_refuse": True,
        "never_apply_size": True,
        "names": names,
    }


def assert_scout_attach_authority() -> dict[str, Any]:
    """Scout lock: names resolve onto existing PACK 2 / PACK 5 fields. No admit."""
    from .pack2_fields import PACK2_FIELD_IDS

    bad: list[str] = []
    choice = resolve_attach_name(CHOICE_ID)
    if choice["kind"] != "choice" or choice["never_admit"] is not True or choice["shadow_only"] is not True:
        bad.append("choice_not_shadow")
    dual = resolve_attach_name("gbpjpy_dual_leg")
    if dual.get("equiv") != "gate.cross_stack_gbpjpy":
        bad.append("dual_leg")
    tokyo = resolve_attach_name("tokyo_event")
    if tokyo.get("split") != ("gate.asia_jpy_act_ok", "gate.event_boj_window"):
        bad.append("tokyo_event")
    london = resolve_attach_name("london_fit")
    if london.get("split") != ("sleeve.london_expand_eur_gbp", "gate.session_overlap_ok"):
        bad.append("london_fit")
    for name in ("gbpjpy_dual_leg", "tokyo_event", "london_fit"):
        for fid in resolve_attach_name(name)["targets"]:
            if fid not in PACK2_FIELD_IDS:
                bad.append(f"missing_pack2:{fid}")
            if fid in NEVER_WRITE_GATE_IDS or fid == "admit":
                bad.append(f"wrote_admit:{fid}")
    return {
        "ok": not bad,
        "bad": bad,
        "names": list(SCOUT_ATTACH_NAMES),
        "shadow_only": True,
        "never_admit": True,
        "never_refuse": True,
        "scout_packet_present": SCOUT_PACKET_PATH.is_file(),
        "authority": "scout_sleeve_attach_map",
    }

PACK5_FIELD_SPEC: dict[str, dict[str, Any]] = {
    CHOICE_ID: {
        "surface": "choice",
        "kind": "choice",
        "applies_setups": (SETUP_GBPJPY,),
        "applies_symbols": ("GBPJPY",),
        "families": ("admit", "size", "news_window"),
        "never_invent": ("DXY", "funding", "peer_ohlc", "boj_high", "tone_print"),
        "never_admit": True,
        "never_write_questions": tuple(sorted(NEVER_WRITE_QUESTIONS)),
        "never_write_gate_ids": tuple(sorted(NEVER_WRITE_GATE_IDS)),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003",)},
            {"question": "event_proximity", "ids": ("FLUID-NWS-001",)},
            {"question": "warsh_class", "ids": ("FLUID-NWS-004",)},
        ),
        "criteria": {
            A_PLUS: "The conjuncts on the card are the sleeve.",
            ALMOST: "Session is present and a required conjunct is not a block.",
            BLOCKED: "A conjunct on the card blocks the sleeve.",
            NULL_STATE: "Required conjuncts unassembled. Empty spine ≠ no BOJ.",
        },
        "role": "Chair-canon GBPJPY A+ Choice. SHADOW. Not admit.",
    },
}


def _norm_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper().replace(" ", "")


def field_applies(field_id: str, *, setup_id: str | None, symbol: str) -> bool:
    spec = PACK5_FIELD_SPEC[field_id]
    if setup_id and str(setup_id) in spec["applies_setups"]:
        return True
    return _norm_symbol(symbol) in {_norm_symbol(s) for s in spec["applies_symbols"]}


def pack5_gate_map() -> list[dict[str, Any]]:
    spec = PACK5_FIELD_SPEC[CHOICE_ID]
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
            "scout_tier1_wires": {k: list(v) for k, v in SCOUT_TIER1_WIRES.items()},
            "shadow_only": True,
            "never_refuse": True,
            "never_apply_size": True,
            "edge": EDGE,
        }
    ]


def assert_pack5_maps_existing_families() -> dict[str, Any]:
    bad: list[str] = []
    for row in pack5_gate_map():
        for q in row["gate_questions"]:
            if q in NEVER_WRITE_QUESTIONS:
                bad.append(f"wrote_question:{q}")
        for gid in row["gate_ids"]:
            if gid in NEVER_WRITE_GATE_IDS:
                bad.append(f"wrote_gate:{gid}")
            gate = lookup(gid)
            if gate is None:
                bad.append(f"missing:{gid}")
                continue
            if str(gate.get("family") or "") not in ALLOWED_FAMILIES:
                bad.append(f"family:{gid}:{gate.get('family')}")
        for answer in row["criteria"]:
            if answer in ADMIT_ANSWERS:
                bad.append(f"admit_answer:{answer}")
    for field_id, gids in SCOUT_TIER1_WIRES.items():
        for gid in gids:
            if lookup(gid) is None:
                bad.append(f"scout_missing:{field_id}:{gid}")
    return {"ok": not bad, "bad": bad, "never_admit": True, "edge": EDGE}


def assert_scout_tier1_observe_only() -> dict[str, Any]:
    """Scout lock: observe existing ADM/SIZ/NWS ids. No new refuse. No admit write."""
    bad: list[str] = []
    wired: list[str] = []
    for field_id, gids in SCOUT_TIER1_WIRES.items():
        if field_id not in SCOUT_TIER1_ALIASES:
            bad.append(f"alias_missing:{field_id}")
        if field_id == "corr.xau_vs_eur_proxy_usd":
            if gids:
                bad.append("xau_proxy_wired")
            continue
        if not gids:
            bad.append(f"empty_wire:{field_id}")
            continue
        for gid in gids:
            if gid in NEVER_WRITE_GATE_IDS:
                bad.append(f"wrote_gate:{field_id}:{gid}")
            gate = lookup(gid)
            if gate is None:
                bad.append(f"missing:{field_id}:{gid}")
                continue
            if str(gate.get("family") or "") not in ALLOWED_FAMILIES:
                bad.append(f"family:{field_id}:{gid}:{gate.get('family')}")
            if str(gate.get("question") or "") in NEVER_WRITE_QUESTIONS:
                bad.append(f"wrote_question:{field_id}:{gid}")
            if gate.get("refuse") is True:
                bad.append(f"refuse:{field_id}:{gid}")
            wired.append(gid)
    return {
        "ok": not bad,
        "bad": bad,
        "n_features": len(SCOUT_TIER1_WIRES),
        "n_wired": len(wired),
        "no_wire": ("corr.xau_vs_eur_proxy_usd",),
        "never_admit": True,
        "never_refuse": True,
        "shadow_only": True,
        "edge": "SCOUT_TIER1",
    }


_CHOICE_CACHE: dict[str, str | None] = {}
_CHOICE_LOCK = threading.Lock()


def _challenge() -> bool:
    try:
        from .state_choices import on_challenge
    except Exception:
        return False
    try:
        return bool(on_challenge())
    except Exception:
        return False


def _choice(
    qid: str,
    facts: dict[str, Any],
    criteria: dict[str, str],
    instructions: str,
) -> str | None:
    blob = json.dumps({"q": qid, "f": facts}, sort_keys=True, default=str)
    with _CHOICE_LOCK:
        if blob in _CHOICE_CACHE:
            return _CHOICE_CACHE[blob]
    try:
        from .jev_client import evaluate
        from .jev_questions import unique_highest
    except Exception:
        return None
    questions = {
        qid: {
            "type": "choice",
            "instructions": instructions,
            "criteria": {str(key): str(text) for key, text in criteria.items()},
        }
    }
    try:
        receipt = evaluate(
            {"facts": facts, "order_send": False, "flatten": False},
            questions=questions,
            merge_sleeve=False,
            model="jev-1.13.0",
        )
    except Exception:
        return None
    block = None
    if isinstance(receipt, dict):
        answers = receipt.get("answers")
        if isinstance(answers, dict):
            block = answers.get(qid)
    probs = block.get("probabilities") if isinstance(block, dict) else None
    try:
        picked = unique_highest(probs if isinstance(probs, dict) else None, tuple(criteria))
    except Exception:
        picked = None
    with _CHOICE_LOCK:
        _CHOICE_CACHE[blob] = picked
    return picked


def _tone(pack2: Mapping[str, Any] | None, supplied: Any) -> str:
    if supplied:
        return str(supplied).strip().lower()
    if not pack2:
        return "unassembled"
    fields = pack2.get("fields") if isinstance(pack2.get("fields"), Mapping) else {}
    bundle = (fields or {}).get("info.risk_on_off_bundle") or {}
    if not bundle.get("assembled"):
        return "unassembled"
    raw = bundle.get("value")
    if isinstance(raw, Mapping):
        raw = raw.get("tone") or raw.get("value")
    if raw is None:
        return "unassembled"
    return str(raw).strip().lower()


def score_a_plus(
    *,
    session_ok: bool | None,
    identity_ok: bool | None,
    agree: bool | None,
    dual_same: bool | None,
    boj_bucket: str,
    tone: str,
) -> dict[str, Any]:
    pack4 = score_readiness(
        session_ok=session_ok,
        identity_ok=identity_ok,
        agree=agree,
        dual_same=dual_same,
        boj_bucket=boj_bucket,
    )
    tone_ok = None if tone == "unassembled" else tone not in TONE_BLOCK
    conjuncts = {**pack4["conjuncts"], "tone_ok": tone_ok}
    if _challenge():
        picked = _choice(
            CHOICE_ID,
            {
                "session_ok": session_ok,
                "identity_ok": identity_ok,
                "agree": agree,
                "dual_same": dual_same,
                "boj_bucket": boj_bucket,
                "tone": tone,
                "tone_ok": tone_ok,
                "boj_clear": conjuncts.get("boj_clear"),
            },
            dict(PACK5_FIELD_SPEC[CHOICE_ID]["criteria"]),
            (
                "The conjuncts are on the card. "
                "The unique highest sleeve state is the decision. "
                "An empty answer or a tie leaves the choice unset. "
                "Do not admit. Do not send."
            ),
        )
        return {
            "type": "choice",
            "choice": picked,
            "fail_reason": None,
            "fail_conjunct": None,
            "conjuncts": conjuncts,
            "boj_bucket": boj_bucket,
            "tone": tone,
            "pack4_choice": pack4["choice"],
            "criteria": dict(PACK5_FIELD_SPEC[CHOICE_ID]["criteria"]),
            "never_admit": True,
            "never_refuse": True,
            "never_apply_size": True,
            "shadow_only": True,
            "invented": False,
            "edge": EDGE,
        }
    hard = (
        dual_same is False
        or identity_ok is False
        or conjuncts["boj_clear"] is False
        or tone_ok is False
    )
    if hard:
        if dual_same is False:
            reason, fail = "dual_split", "dual_same"
        elif identity_ok is False:
            reason, fail = "residual", "cross.identity_ok"
        elif conjuncts["boj_clear"] is False:
            reason, fail = "boj_bucket", "boj_clear"
        else:
            reason, fail = "tone_risk_off", "tone_ok"
        choice = BLOCKED
    elif all(
        bit is True
        for bit in (
            session_ok,
            identity_ok,
            agree,
            dual_same,
            conjuncts["boj_clear"],
            tone_ok,
        )
    ):
        choice, reason, fail = A_PLUS, None, None
    elif session_ok is True and pack4["choice"] != "unassembled":
        choice, reason, fail = ALMOST, "almost", None
    elif session_ok is True and tone_ok is None:
        choice, reason, fail = ALMOST, "tone_unassembled", "tone_ok"
    else:
        choice, reason, fail = NULL_STATE, "unassembled", None
    return {
        "type": "choice",
        "choice": choice,
        "fail_reason": reason,
        "fail_conjunct": fail,
        "conjuncts": conjuncts,
        "boj_bucket": boj_bucket,
        "tone": tone,
        "pack4_choice": pack4["choice"],
        "criteria": dict(PACK5_FIELD_SPEC[CHOICE_ID]["criteria"]),
        "never_admit": True,
        "never_refuse": True,
        "never_apply_size": True,
        "shadow_only": True,
        "invented": False,
        "edge": EDGE,
    }


def pack5_choice_assembled(pack5: Mapping[str, Any] | None) -> bool:
    if not pack5:
        return False
    fields = pack5.get("fields") if isinstance(pack5.get("fields"), Mapping) else {}
    row = (fields or {}).get(CHOICE_ID) or {}
    return bool(row.get("assembled"))


def assemble_pack5_fields(
    *,
    symbol: str,
    setup_id: str | None = None,
    pack2: Mapping[str, Any] | None = None,
    pack3: Mapping[str, Any] | None = None,
    pack4: Mapping[str, Any] | None = None,
    pack5_values: Mapping[str, Any] | None = None,
    session_named: str | None = None,
) -> dict[str, Any]:
    supplied = dict(pack5_values or {})
    if pack4 is None:
        pack4 = assemble_pack4_fields(
            symbol=symbol,
            setup_id=setup_id,
            pack3=pack3,
            pack4_values=supplied.get("pack4_values"),
            session_named=session_named,
        )
    applies = field_applies(CHOICE_ID, setup_id=setup_id, symbol=symbol)
    p4 = ((pack4.get("fields") or {}).get("choice.gbpjpy_aplus_ready") or {}) if applies else {}
    value = p4.get("value") if isinstance(p4.get("value"), Mapping) else {}
    conjuncts = value.get("conjuncts") if isinstance(value.get("conjuncts"), Mapping) else {}
    tone = _tone(pack2, supplied.get("tone"))
    scored = score_a_plus(
        session_ok=conjuncts.get("session_ok"),
        identity_ok=conjuncts.get("cross.identity_ok"),
        agree=conjuncts.get("agree"),
        dual_same=conjuncts.get("dual_same"),
        boj_bucket=p4.get("boj_bucket") or value.get("boj_bucket") or "unassembled",
        tone=tone,
    )
    assembled = applies and scored["choice"] in {A_PLUS, ALMOST, BLOCKED}
    row = {
        "id": CHOICE_ID,
        "surface": "choice",
        "kind": "choice",
        "applies": applies,
        "assembled": bool(applies and assembled),
        "value": scored if applies else None,
        "source": STATE_PATH if applies else "not_applicable",
        "invented": False,
        "shadow_only": True,
        "never_apply_size": True,
        "never_refuse": True,
        "never_admit": True,
        "never_write_questions": list(NEVER_WRITE_QUESTIONS),
        "never_write_gate_ids": list(NEVER_WRITE_GATE_IDS),
        "choice": scored["choice"] if applies else None,
        "fail_reason": scored["fail_reason"] if applies else None,
        "fail_conjunct": scored["fail_conjunct"] if applies else None,
        "conjuncts": scored["conjuncts"] if applies else None,
        "boj_bucket": scored["boj_bucket"] if applies else None,
        "tone": scored["tone"] if applies else None,
        "setup_id": setup_id,
        "edge": EDGE,
    }
    if not applies:
        row["assembled"] = False
        row["value"] = None
    fields = {CHOICE_ID: row}
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
        "ids": list(PACK5_FIELD_IDS),
        "fields": fields,
        "n_applies": int(applies),
        "n_assembled": int(row["assembled"]),
        "invented": False,
        "missing_fields": missing,
        "attach": SLEEVE_ATTACH_MAP.get(setup_id or SETUP_GBPJPY if applies else ""),
        "choice": row.get("choice"),
        "setup_id": setup_id,
        "aliases": dict(ATTACH_ALIASES),
        "scout_tier1_wires": {k: list(v) for k, v in SCOUT_TIER1_WIRES.items()},
        "attach_resolved": resolve_gbpjpy_attach(pack2=pack2, pack5_choice=row.get("choice"))
        if applies
        else None,
    }


def assert_pack5_t3_not_pack3_alias() -> dict[str, Any]:
    """PACK 5 t3 is pass-capable. PACK 3 t3 aliases t4 residual-fail."""
    p3 = PACK3_GBPJPY_VECTORS["t3"]
    p5 = PACK5_FIXTURE_VECTORS["t3"]
    ok = (
        p3.get("alias_of") == "t4"
        and float(p3["residual"]) == float(PACK3_GBPJPY_VECTORS["t4"]["residual"])
        and float(p5["residual"]) == 0.10
        and float(p5["london_expand"]) == 1.25
        and p5["tone"] == "neutral"
        and p5["expect"] == A_PLUS
        and p5.get("not_pack3_t3") is True
        and float(p5["residual"]) != float(p3["residual"])
    )
    return {
        "ok": ok,
        "pack3_t3_alias_of": p3.get("alias_of"),
        "pack3_t3_residual": p3.get("residual"),
        "pack5_t3_residual": p5.get("residual"),
        "pack5_t3_expect": p5.get("expect"),
        "edge": EDGE,
    }


def pack5_values_from_gbpjpy_fixture(vector: str | Mapping[str, Any]) -> dict[str, Any]:
    vec = dict(vector) if isinstance(vector, Mapping) else dict(_fixture(vector))
    return {"tone": vec.get("tone") or "neutral"}


def _from_pack3(vector_id: str, *, expect: str, expect_reason: str | None) -> dict[str, Any]:
    row = dict(gbpjpy_fixture(vector_id))
    row.pop("alias_of", None)
    row["tone"] = "neutral"
    row["expect"] = expect
    row["expect_reason"] = expect_reason
    row["pass_capable"] = expect == A_PLUS
    row["verdict"] = expect
    return row


# PACK 5 t3 is pass-capable (resid 0.10, expand 1.25, tone neutral).
# It is NOT PACK 3 t3, which aliases t4 residual-fail.
_T3 = {
    "id": "t3",
    "symbol": "GBPJPY",
    "verdict": A_PLUS,
    "fail_reason": None,
    "time_utc": "2026-01-15T07:30:00Z",
    "dual_leg_agree": True,
    "gbpusd_side": "long",
    "usdjpy_side": "long",
    "gbpjpy_side": "long",
    "residual": 0.10,
    "london_expand": 1.25,
    "corr.gbpjpy_risk_cross": "agree",
    "corr.eur_gbp_usd_co_move": True,
    "tone": "neutral",
    "expect": A_PLUS,
    "expect_reason": None,
    "pass_capable": True,
    "not_pack3_t3": True,
}

PACK5_FIXTURE_VECTORS: dict[str, dict[str, Any]] = {
    "t1": _from_pack3("t1", expect=A_PLUS, expect_reason=None),
    "t2": _from_pack3("t2", expect=BLOCKED, expect_reason="dual_split"),
    "t3": dict(_T3),
    "t4": _from_pack3("t4", expect=BLOCKED, expect_reason="residual"),
}


def _fixture(vector_id: str) -> dict[str, Any]:
    key = str(vector_id).lower()
    row = PACK5_FIXTURE_VECTORS.get(key)
    if row is None:
        raise KeyError(vector_id)
    return dict(row)


def encode_gbpjpy_a_plus(vector: str | Mapping[str, Any]) -> dict[str, Any]:
    vec = dict(vector) if isinstance(vector, Mapping) else _fixture(vector)
    as_of = datetime.strptime(str(vec["time_utc"]), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    pack3 = assemble_pack3_fields(
        symbol="GBPJPY",
        time_utc=as_of,
        pack3_values=values_from_gbpjpy_fixture(vec),
        news={"spine_empty": True, "events": []},
    )
    pack4 = assemble_pack4_fields(
        symbol="GBPJPY",
        setup_id=SETUP_GBPJPY,
        pack3=pack3,
        pack4_values=pack4_values_from_gbpjpy_fixture(vec),
        session_named="london",
    )
    pack5 = assemble_pack5_fields(
        symbol="GBPJPY",
        setup_id=SETUP_GBPJPY,
        pack3=pack3,
        pack4=pack4,
        pack5_values=pack5_values_from_gbpjpy_fixture(vec),
        session_named="london",
    )
    row = pack5["fields"][CHOICE_ID]
    return {
        "id": vec.get("id"),
        "symbol": "GBPJPY",
        "setup_id": SETUP_GBPJPY,
        "choice": row.get("choice"),
        "fail_reason": row.get("fail_reason"),
        "fail_conjunct": row.get("fail_conjunct"),
        "tone": row.get("tone"),
        "conjuncts": row.get("conjuncts"),
        "pack5": pack5,
        "never_admit": True,
        "never_refuse": True,
        "shadow_only": True,
        "edge": EDGE,
    }


def score_gbpjpy_a_plus_ready(vector: str | Mapping[str, Any]) -> dict[str, Any]:
    encoded = encode_gbpjpy_a_plus(vector)
    locked = PACK5_FIXTURE_VECTORS.get(str(encoded.get("id") or "").lower())
    expect = (locked["expect"], locked["expect_reason"]) if locked else None
    matches = expect is not None and encoded["choice"] == expect[0] and encoded["fail_reason"] == expect[1]
    return {**encoded, "expected_choice": expect[0] if expect else None, "matches_lock": matches}
