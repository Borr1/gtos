"""Instrument Edge PACK 4 — SLEEVE_ATTACH_MAP + GBPJPY A+ readiness Choice.

Chair lock 2026-09-18. SHADOW only. First Choice is GBPJPY A+ readiness:

    session_ok ∧ cross.identity_ok ∧ agree ∧ dual_same
    ∧ boj_bucket ∉ {print, guidance_live}

TypeSafe Choice. Not an admit Choice. Does not write FLUID-ADM-007 /
UB-AUTH-010 / ``admit_choice``. Encodes Pack 3 fixtures t1 / t2 / t4.

No new fluid gates. No new refuse walls. No APPLY. ENV-US30 stays integer OFF.
Do not invent DXY, funding, peer OHLC, or a BOJ HIGH.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .fluid_gates import lookup
from .pack3_fields import (
    GBPJPY_FIXTURE_VECTORS,
    RESID_CAP,
    assemble_pack3_fields,
    gbpjpy_fixture,
    in_london_open,
    score_gbpjpy_fixture,
    values_from_gbpjpy_fixture,
)

SCHEMA = "gtos.judgment.aplus_pack4_fields.v0"
ORIGIN = "instrument_edge_pack4_20260918"
EDGE = "PACK 4"
STATE_PATH = "pack4_fields"

CHOICE_ID = "choice.gbpjpy_aplus_ready"
SETUP_GBPJPY = "gbpjpy_london_session_sweep"

PACK4_FIELD_IDS = (CHOICE_ID,)

CHOICE_READY = "ready"
CHOICE_NOT_READY = "not_ready"
CHOICE_UNASSEMBLED = "unassembled"
CHOICE_ANSWERS = frozenset({CHOICE_READY, CHOICE_NOT_READY, CHOICE_UNASSEMBLED})
ADMIT_ANSWERS = frozenset({"admit", "abstain", "hard_refuse"})

CONJUNCTS = ("session_ok", "cross.identity_ok", "agree", "dual_same", "boj_clear")
BOJ_BUCKETS = ("print", "guidance_live", "guidance_away", "none", "unassembled")
BOJ_BLOCK = frozenset({"print", "guidance_live"})
NEVER_WRITE_QUESTIONS = frozenset({"admit"})
NEVER_WRITE_GATE_IDS = frozenset({"FLUID-ADM-007", "UB-AUTH-010"})
ALLOWED_FAMILIES = frozenset({"admit", "size", "news_window"})

# Closed SLEEVE_ATTACH_MAP. GBPJPY is the first implemented Choice.
# Other catalog sleeves stay named stubs — not-applicable, not invented.
_STUB_NOTE = "PACK 4 first Choice is GBPJPY only. Named stub; not-applicable."


def _attach_row(
    *,
    setup_id: str,
    symbol: str,
    implemented: bool,
    choice: str | None,
    conjuncts: tuple[str, ...] = (),
    boj_block_buckets: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "setup_id": setup_id,
        "symbol": symbol,
        "implemented": implemented,
        "status": "implemented" if implemented else "not_applicable",
        "choice": choice,
        "conjuncts": list(conjuncts),
        "boj_block_buckets": list(boj_block_buckets),
        "state_paths": {
            "edge": EDGE,
            "schema": SCHEMA,
            "pack4": STATE_PATH,
            "aplus": "aplus.pack4_fields",
            "choice": f"{STATE_PATH}.fields.{choice}" if choice else None,
        },
        "never_admit": True,
        "never_refuse": True,
        "never_apply_size": True,
        "shadow_only": True,
        "note": None if implemented else _STUB_NOTE,
    }


SLEEVE_ATTACH_MAP: dict[str, dict[str, Any]] = {
    SETUP_GBPJPY: _attach_row(
        setup_id=SETUP_GBPJPY,
        symbol="GBPJPY",
        implemented=True,
        choice=CHOICE_ID,
        conjuncts=CONJUNCTS,
        boj_block_buckets=tuple(sorted(BOJ_BLOCK)),
    ),
    "xau_london_ob_retest": _attach_row(
        setup_id="xau_london_ob_retest",
        symbol="XAUUSD",
        implemented=False,
        choice=None,
    ),
    "eurusd_ny_ob_retest": _attach_row(
        setup_id="eurusd_ny_ob_retest",
        symbol="EURUSD",
        implemented=False,
        choice=None,
    ),
    "usdjpy_tokyo_asia_fade": _attach_row(
        setup_id="usdjpy_tokyo_asia_fade",
        symbol="USDJPY",
        implemented=False,
        choice=None,
    ),
    "xau_dsp_shakeout": _attach_row(
        setup_id="xau_dsp_shakeout",
        symbol="XAUUSD",
        implemented=False,
        choice=None,
    ),
}

PACK4_FIELD_SPEC: dict[str, dict[str, Any]] = {
    CHOICE_ID: {
        "surface": "choice",
        "kind": "choice",
        "applies_setups": (SETUP_GBPJPY,),
        "applies_symbols": ("GBPJPY",),
        "families": ("admit", "size", "news_window"),
        "never_invent": ("DXY", "funding", "peer_ohlc", "boj_high"),
        "never_admit": True,
        "never_write_questions": tuple(sorted(NEVER_WRITE_QUESTIONS)),
        "never_write_gate_ids": tuple(sorted(NEVER_WRITE_GATE_IDS)),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "event_proximity", "ids": ("FLUID-NWS-001",)},
            {"question": "warsh_class", "ids": ("FLUID-NWS-004",)},
            {"question": "event_size", "ids": ("FLUID-SIZ-006",)},
        ),
        "criteria": {
            CHOICE_READY: (
                "session_ok ∧ cross.identity_ok ∧ agree ∧ dual_same "
                "∧ boj_bucket not in {print, guidance_live}"
            ),
            CHOICE_NOT_READY: "A named conjunct failed (dual_split before residual)",
            CHOICE_UNASSEMBLED: "A required conjunct is unassembled. Empty spine ≠ no BOJ.",
        },
        "role": (
            "GBPJPY A+ readiness Choice on Edge PACK 4. SHADOW. "
            "Maps onto session / flow / news as inputs. Never an admit Choice."
        ),
    },
}


def _norm_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper().replace(" ", "")


def sleeve_attach(setup_id: str | None) -> dict[str, Any] | None:
    if not setup_id:
        return None
    row = SLEEVE_ATTACH_MAP.get(str(setup_id))
    return dict(row) if row else None


def field_applies(field_id: str, *, setup_id: str | None, symbol: str) -> bool:
    spec = PACK4_FIELD_SPEC[field_id]
    setups = {str(s) for s in spec["applies_setups"]}
    if setup_id and str(setup_id) in setups:
        return True
    want = {_norm_symbol(s) for s in spec["applies_symbols"]}
    return _norm_symbol(symbol) in want


def pack4_gate_map() -> list[dict[str, Any]]:
    rows = []
    for field_id in PACK4_FIELD_IDS:
        spec = PACK4_FIELD_SPEC[field_id]
        rows.append(
            {
                "field": field_id,
                "surface": spec["surface"],
                "kind": spec["kind"],
                "families": list(spec["families"]),
                "applies_setups": list(spec["applies_setups"]),
                "applies_symbols": list(spec["applies_symbols"]),
                "gate_questions": [g["question"] for g in spec["gate_inputs"]],
                "gate_ids": [gid for g in spec["gate_inputs"] for gid in g["ids"]],
                "never_invent": list(spec["never_invent"]),
                "never_admit": True,
                "never_write_questions": list(spec["never_write_questions"]),
                "never_write_gate_ids": list(spec["never_write_gate_ids"]),
                "criteria": dict(spec["criteria"]),
                "role": spec["role"],
                "shadow_only": True,
                "never_refuse": True,
                "never_apply_size": True,
                "edge": EDGE,
            }
        )
    return rows


def assert_pack4_maps_existing_families() -> dict[str, Any]:
    """PACK 4 gate ids must already exist in ADM / SIZ / NWS and must not write admit."""
    bad: list[str] = []
    for row in pack4_gate_map():
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
            fam = str(gate.get("family") or "")
            if fam not in ALLOWED_FAMILIES:
                bad.append(f"family:{gid}:{fam}")
            if gate.get("class") not in {"fluid", "envelope"}:
                bad.append(f"class:{gid}")
        for answer in row["criteria"]:
            if answer in ADMIT_ANSWERS:
                bad.append(f"admit_answer:{answer}")
    return {
        "ok": not bad,
        "bad": bad,
        "n": len(PACK4_FIELD_IDS),
        "families": sorted(ALLOWED_FAMILIES),
        "never_admit": True,
        "edge": EDGE,
    }


def _pack3_field(pack3: Mapping[str, Any] | None, field_id: str) -> dict[str, Any]:
    if not pack3:
        return {}
    fields = pack3.get("fields") if isinstance(pack3.get("fields"), Mapping) else {}
    row = fields.get(field_id) if isinstance(fields, Mapping) else None
    return dict(row) if isinstance(row, Mapping) else {}


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    if isinstance(value, str):
        low = value.strip().lower()
        if low in {"true", "yes", "1", "agree", "same", "pass", "ok"}:
            return True
        if low in {"false", "no", "0", "disagree", "split", "fail", "dual_split"}:
            return False
    return None


def _session_ok(pack3: Mapping[str, Any] | None, *, session_named: str | None) -> bool | None:
    london = _pack3_field(pack3, "london_open_eur_gbp_expand")
    value = london.get("value") if isinstance(london.get("value"), Mapping) else {}
    if london.get("assembled") and "in_window" in value:
        return bool(value.get("in_window"))
    if session_named == "london" and pack3 and pack3.get("time_utc"):
        try:
            as_of = datetime.strptime(str(pack3["time_utc"]), "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            return in_london_open(as_of)
        except (TypeError, ValueError):
            return None
    return None


def _identity_ok(pack3: Mapping[str, Any] | None) -> bool | None:
    cross = _pack3_field(pack3, "corr.gbpjpy_risk_cross")
    value = cross.get("value") if isinstance(cross.get("value"), Mapping) else {}
    klass = value.get("residual_class")
    if klass is None:
        return None
    return str(klass) == "pass"


def _agree(pack3: Mapping[str, Any] | None) -> bool | None:
    cross = _pack3_field(pack3, "corr.gbpjpy_risk_cross")
    value = cross.get("value") if isinstance(cross.get("value"), Mapping) else {}
    risk = _as_bool(value.get("agree")) if cross.get("assembled") else None
    co = _pack3_field(pack3, "corr.eur_gbp_usd_co_move")
    co_move = _as_bool(co.get("value")) if co.get("assembled") else None
    known = [bit for bit in (risk, co_move) if bit is not None]
    if not known:
        return None
    return all(known)


def _dual_same(pack3: Mapping[str, Any] | None) -> bool | None:
    cross = _pack3_field(pack3, "corr.gbpjpy_risk_cross")
    value = cross.get("value") if isinstance(cross.get("value"), Mapping) else {}
    if not cross.get("assembled"):
        return None
    return _as_bool(value.get("dual_leg_agree"))


def classify_boj_bucket(
    pack3: Mapping[str, Any] | None,
    *,
    supplied: str | None = None,
) -> str:
    """Named BOJ timing bucket. Empty spine stays unassembled. Never invent."""
    if supplied:
        raw = str(supplied).strip().lower()
        if raw in BOJ_BUCKETS:
            return raw
    boj = _pack3_field(pack3, "macro.boj_guidance_window")
    if not boj.get("assembled"):
        return "unassembled"
    named = boj.get("named_boj")
    in_win = boj.get("value")
    event = " ".join(str(boj.get(k) or "") for k in ("event",)).lower()
    if not named:
        return "none"
    if in_win:
        if any(token in event for token in ("outlook", "guidance", "minutes")):
            return "guidance_live"
        return "print"
    return "guidance_away"


def _boj_clear(bucket: str) -> bool | None:
    if bucket == "unassembled":
        return None
    return bucket not in BOJ_BLOCK


def score_readiness(
    *,
    session_ok: bool | None,
    identity_ok: bool | None,
    agree: bool | None,
    dual_same: bool | None,
    boj_bucket: str,
) -> dict[str, Any]:
    """SHADOW scorer. Dual-split before residual. Never admit. Never refuse."""
    boj_clear = _boj_clear(boj_bucket)
    conjuncts = {
        "session_ok": session_ok,
        "cross.identity_ok": identity_ok,
        "agree": agree,
        "dual_same": dual_same,
        "boj_clear": boj_clear,
    }
    # Pack 3 fail order: dual_split first, then residual. Then the rest.
    if dual_same is False:
        choice, reason, fail_conjunct = CHOICE_NOT_READY, "dual_split", "dual_same"
    elif identity_ok is False:
        choice, reason, fail_conjunct = CHOICE_NOT_READY, "residual", "cross.identity_ok"
    elif agree is False:
        choice, reason, fail_conjunct = CHOICE_NOT_READY, "agree", "agree"
    elif session_ok is False:
        choice, reason, fail_conjunct = CHOICE_NOT_READY, "session", "session_ok"
    elif boj_clear is False:
        choice, reason, fail_conjunct = CHOICE_NOT_READY, "boj_bucket", "boj_clear"
    elif any(bit is None for bit in conjuncts.values()):
        choice, reason, fail_conjunct = CHOICE_UNASSEMBLED, "unassembled", None
    else:
        choice, reason, fail_conjunct = CHOICE_READY, None, None
    return {
        "type": "choice",
        "choice": choice,
        "fail_reason": reason,
        "fail_conjunct": fail_conjunct,
        "conjuncts": conjuncts,
        "boj_bucket": boj_bucket,
        "boj_block_buckets": sorted(BOJ_BLOCK),
        "criteria": dict(PACK4_FIELD_SPEC[CHOICE_ID]["criteria"]),
        "never_admit": True,
        "never_refuse": True,
        "never_apply_size": True,
        "shadow_only": True,
        "invented": False,
        "edge": EDGE,
    }


def _row(
    field_id: str,
    *,
    applies: bool,
    assembled: bool,
    value: Any,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    spec = PACK4_FIELD_SPEC[field_id]
    packed = {
        "id": field_id,
        "surface": spec["surface"],
        "kind": spec["kind"],
        "applies": applies,
        "assembled": bool(applies and assembled),
        "value": value if applies else None,
        "source": STATE_PATH if applies else "not_applicable",
        "invented": False,
        "shadow_only": True,
        "never_apply_size": True,
        "never_refuse": True,
        "never_admit": True,
        "never_write_questions": list(spec["never_write_questions"]),
        "never_write_gate_ids": list(spec["never_write_gate_ids"]),
        "families": list(spec["families"]),
        "gate_questions": [g["question"] for g in spec["gate_inputs"]],
        "gate_ids": [gid for g in spec["gate_inputs"] for gid in g["ids"]],
        "never_invent": list(spec["never_invent"]),
        "edge": EDGE,
    }
    if extra:
        packed.update(extra)
    if not applies:
        packed["assembled"] = False
        packed["value"] = None
    return packed


def assemble_pack4_fields(
    *,
    symbol: str,
    setup_id: str | None = None,
    pack3: Mapping[str, Any] | None = None,
    pack4_values: Mapping[str, Any] | None = None,
    session_named: str | None = None,
) -> dict[str, Any]:
    """Assemble Edge PACK 4. Missing Pack 3 peers / empty spine stay visible."""
    supplied = dict(pack4_values or {})
    attach = sleeve_attach(setup_id) or sleeve_attach(SETUP_GBPJPY if _norm_symbol(symbol) == "GBPJPY" else "")
    applies = field_applies(CHOICE_ID, setup_id=setup_id, symbol=symbol)
    session_ok = _session_ok(pack3, session_named=session_named)
    identity_ok = _identity_ok(pack3)
    agree = _agree(pack3)
    dual_same = _dual_same(pack3)
    if "session_ok" in supplied:
        session_ok = _as_bool(supplied.get("session_ok"))
    if "cross.identity_ok" in supplied or "identity_ok" in supplied:
        identity_ok = _as_bool(supplied.get("cross.identity_ok", supplied.get("identity_ok")))
    if "agree" in supplied:
        agree = _as_bool(supplied.get("agree"))
    if "dual_same" in supplied:
        dual_same = _as_bool(supplied.get("dual_same"))
    bucket = classify_boj_bucket(pack3, supplied=supplied.get("boj_bucket"))
    scored = score_readiness(
        session_ok=session_ok,
        identity_ok=identity_ok,
        agree=agree,
        dual_same=dual_same,
        boj_bucket=bucket,
    )
    assembled = applies and scored["choice"] in {CHOICE_READY, CHOICE_NOT_READY}
    fields = {
        CHOICE_ID: _row(
            CHOICE_ID,
            applies=applies,
            assembled=assembled,
            value=scored if applies else None,
            extra={
                "choice": scored["choice"] if applies else None,
                "fail_reason": scored["fail_reason"] if applies else None,
                "fail_conjunct": scored["fail_conjunct"] if applies else None,
                "conjuncts": scored["conjuncts"] if applies else None,
                "boj_bucket": bucket if applies else None,
                "setup_id": (attach or {}).get("setup_id") or setup_id,
            },
        )
    }
    missing = [
        f"{STATE_PATH}.{fid}"
        for fid in PACK4_FIELD_IDS
        if fields[fid]["applies"] and not fields[fid]["assembled"]
    ]
    return {
        "schema": SCHEMA,
        "origin": ORIGIN,
        "edge": EDGE,
        "state_path": STATE_PATH,
        "shadow_only": True,
        "never_apply_size": True,
        "never_refuse": True,
        "never_admit": True,
        "n": len(PACK4_FIELD_IDS),
        "ids": list(PACK4_FIELD_IDS),
        "fields": fields,
        "n_applies": sum(1 for fid in PACK4_FIELD_IDS if fields[fid]["applies"]),
        "n_assembled": sum(1 for fid in PACK4_FIELD_IDS if fields[fid]["assembled"]),
        "invented": False,
        "missing_fields": missing,
        "families": sorted(ALLOWED_FAMILIES),
        "attach": attach,
        "choice": fields[CHOICE_ID].get("choice"),
        "setup_id": (attach or {}).get("setup_id") or setup_id,
    }


def pack4_choice_assembled(pack4: Mapping[str, Any] | None) -> bool:
    if not pack4:
        return False
    fields = pack4.get("fields") if isinstance(pack4.get("fields"), Mapping) else {}
    row = (fields or {}).get(CHOICE_ID) or {}
    return bool(row.get("assembled"))


def pack4_values_from_gbpjpy_fixture(vector: str | Mapping[str, Any]) -> dict[str, Any]:
    """Fixture encode defaults boj_bucket to none so t1 can be ready.

    Empty live spine stays unassembled. Fixtures are not a live spine.
    """
    vec = gbpjpy_fixture(vector) if isinstance(vector, str) else dict(vector)
    return {
        "boj_bucket": vec.get("boj_bucket") or "none",
    }


def encode_gbpjpy_fixture(vector: str | Mapping[str, Any]) -> dict[str, Any]:
    """Encode a locked Pack 3 GBPJPY vector through the PACK 4 readiness Choice."""
    vec = gbpjpy_fixture(vector) if isinstance(vector, str) else dict(vector)
    try:
        as_of = datetime.strptime(str(vec["time_utc"]), "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except (TypeError, ValueError, KeyError):
        as_of = datetime(2026, 1, 15, 7, 30, tzinfo=timezone.utc)
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
    pack3_score = score_gbpjpy_fixture(vec)
    row = pack4["fields"][CHOICE_ID]
    return {
        "id": vec.get("id"),
        "symbol": "GBPJPY",
        "setup_id": SETUP_GBPJPY,
        "choice": row.get("choice"),
        "fail_reason": row.get("fail_reason"),
        "fail_conjunct": row.get("fail_conjunct"),
        "conjuncts": row.get("conjuncts"),
        "boj_bucket": row.get("boj_bucket"),
        "expected_pack3_verdict": vec.get("verdict"),
        "expected_pack3_fail_reason": vec.get("fail_reason"),
        "pack3_matches_lock": pack3_score.get("matches_lock"),
        "pack3": pack3,
        "pack4": pack4,
        "shadow_only": True,
        "never_admit": True,
        "never_refuse": True,
        "never_apply_size": True,
        "invented": False,
        "edge": EDGE,
        "state_path": STATE_PATH,
    }


def score_gbpjpy_aplus_ready(vector: str | Mapping[str, Any]) -> dict[str, Any]:
    """SHADOW Choice scorer for locked t1 / t2 / t4. Never admit. Never refuse."""
    encoded = encode_gbpjpy_fixture(vector)
    vec_id = str(encoded.get("id") or "").lower()
    expect = {
        "t1": (CHOICE_READY, None, None),
        "t2": (CHOICE_NOT_READY, "dual_split", "dual_same"),
        "t4": (CHOICE_NOT_READY, "residual", "cross.identity_ok"),
        "t3": (CHOICE_NOT_READY, "residual", "cross.identity_ok"),
    }.get(vec_id)
    matches = (
        expect is not None
        and encoded["choice"] == expect[0]
        and encoded["fail_reason"] == expect[1]
        and encoded["fail_conjunct"] == expect[2]
    )
    return {
        **encoded,
        "expected_choice": expect[0] if expect else None,
        "expected_fail_reason": expect[1] if expect else None,
        "expected_fail_conjunct": expect[2] if expect else None,
        "matches_lock": matches,
        "fixture_vectors": sorted(k for k in GBPJPY_FIXTURE_VECTORS if k in {"t1", "t2", "t4"}),
    }
