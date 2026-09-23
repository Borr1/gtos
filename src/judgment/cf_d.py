"""Chair CF D primary soft policy — shadow compose on ``jev_fluid_gate_v1``.

Challenge 0, n=60, 2026-09-20 13:16 ICT:

    CF_D = +11.1678 R
    = F+G soft (KEEP full; FS half; session×0.75 nonkeep losses)
      + stand_down×0 when miss=false_structure AND NOT KEEP signature

KEEP is exempt (even on false_structure). CF D KEEP = house spring/vss
**or** family ``sub_mid``. Do **not** add expand. Do **not** change
``CHALLENGE_KEEP_FAMILIES``. Writer house locks stay.

Ablation order: miss › size › family › session › conf.

``LEGACY_religion_index_crypto_xa_0`` stays revoked — stand_down is a
miss compose, not an INDEX/CRYPTO/xa size0 religion.

Labels only. Never place / order_send / remint / flatten.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .cf_priority import (
    RELIGION_INDEX_CRYPTO_XA_SIZE0,
    classify_conf_shadow,
    classify_sleeve_family,
    label_cf_priority,
    religion_index_crypto_xa_size0,
)
from .chair_enforce import is_keep_family
from .challenge import CHALLENGE_HARD_OFF_FAMILIES, CHALLENGE_KEEP_FAMILIES, CHALLENGE_LOGIN
from .conf_gate import TICKET_SUBCLASS

STEAL = "JEV_EVERYWHERE_CF_D"
SCHEMA = "gtos.judgment.cf_d.v1"
REPORT_SCHEMA = "gtos.jev.cf_D.v1"
BANK_SCHEMA = "gtos.jev.question_bank_from_tape.v1"

CHOICE_IDS = (
    "A_STAND_DOWN",
    "B_SIZE_HALF",
    "C_SIZE_TRIM",
    "D_FULL",
    "E_KEEP_CAP",
)

SIZE_BY_CHOICE = {
    "A_STAND_DOWN": 0.0,
    "B_SIZE_HALF": 0.5,
    "C_SIZE_TRIM": 0.75,
    "D_FULL": 1.0,
    "E_KEEP_CAP": 1.0,
}

#: Chair 2026-09-20 — compose attribution order.
ABLATION_ORDER = ("miss", "size", "family", "session", "conf")

#: House KEEP (spring/vss) plus CF D ``sub_mid``. Expand is allow, not KEEP.
CF_D_KEEP_FAMILIES = frozenset({"spring", "vss_fxcross", "sub_mid"})

MISS_LABELS = (
    "false_structure",
    "event_gap",
    "session_cut",
    "ok_win",
    "unknown",
)

MISS_BY_SUBCLASS = {
    "fs_half_still_losing": "false_structure",
    "review_keep_offhours_false_structure": "false_structure",
    "full_size_loss": "false_structure",
    "event_gap_shadow": "event_gap",
    "session_cut_loss": "session_cut",
    "ok_win": "ok_win",
}

LAB_DIR = (
    Path(__file__).resolve().parents[2] / "judgment" / "astra" / "lab" / "jev_cf_d_bank"
)
BANK_PATH = LAB_DIR / "QUESTION_BANK_0.json"
REPORT_PATH = LAB_DIR / "CF_D_REPORT.json"

BANK_SYMBOL_BY_TICKET = {
    "291758207": "XAUUSD",
    "291789105": "EURUSD",
    "291087142": "EURGBP",
    "291383082": "XAUUSD",
    "293611741": "XAUUSD",
    "293332188": "XAUUSD",
    "291794419": "XAUUSD",
    "291816474": "EURGBP",
    "293540988": "EURUSD",
    "293128383": "XAUUSD",
}

BANK_SIDE_BY_TICKET = {
    "291758207": "short",
    "291789105": "long",
    "291087142": "short",
    "291383082": "long",
    "293611741": "long",
    "293332188": "long",
    "291794419": "long",
    "291816474": "short",
    "293540988": "short",
    "293128383": "short",
}


def classify_miss(
    *,
    subclass: str | None = None,
    miss: str | None = None,
) -> str:
    """Map a tape miss or S15 subclass onto the CF D miss axis."""

    raw = str(miss or "").strip()
    if raw in MISS_LABELS:
        return raw
    mapped = MISS_BY_SUBCLASS.get(str(subclass or "").strip())
    if mapped:
        return mapped
    return "unknown"


def is_cf_d_keep(
    *,
    sleeve: str | None = None,
    family: str | None = None,
    keep_flag: bool | None = None,
) -> bool:
    """CF D KEEP signature. Does not mutate house ``CHALLENGE_KEEP_FAMILIES``."""

    if keep_flag is True:
        return True
    if keep_flag is False:
        return False
    if is_keep_family(sleeve):
        return True
    fam = family or classify_sleeve_family(sleeve)
    return fam in CF_D_KEEP_FAMILIES


def _named_session(gold_state: Mapping[str, Any] | None, session: str | None) -> str | None:
    if session:
        return str(session)
    if not gold_state:
        return None
    pack = gold_state.get("sessions")
    if isinstance(pack, Mapping) and pack.get("named") is not None:
        return str(pack.get("named"))
    return None


def _identity_flag(gold_state: Mapping[str, Any] | None, key: str) -> Any:
    if not gold_state:
        return None
    ident = gold_state.get("identity")
    if isinstance(ident, Mapping) and key in ident:
        return ident.get(key)
    return None


def score_cf_d(choice: str, *, outcome: str | None = None, keep: bool = False) -> float:
    """Higher score → more willing to admit / full size. Label only."""

    if choice == "A_STAND_DOWN":
        return 0.08
    if choice == "B_SIZE_HALF":
        return 0.32
    if choice == "C_SIZE_TRIM":
        return 0.48
    if choice == "E_KEEP_CAP":
        if str(outcome or "").upper() == "WIN":
            return 0.96
        if keep:
            return 0.62
        return 0.62
    return 0.80


def noul_tags(
    *,
    asset: str | None,
    sleeve: str | None,
    family: str,
    session: str | None,
    miss: str,
    keep: bool,
    outcome: str | None,
    cost_band: str | None,
    conf_gate_band: str | None,
    role: str | None = None,
) -> tuple[str, ...]:
    tags = [
        f"ASSET:{asset or 'UNK'}",
        f"SLEEVE:{sleeve or ''}",
        f"FAMILY:{family}",
        f"SESSION:{session or ''}",
        f"MISS:{miss}",
        f"KEEP:{keep}",
    ]
    if outcome:
        tags.append(f"OUTCOME:{outcome}")
    if cost_band:
        tags.append(f"COST:{cost_band}")
    if conf_gate_band:
        tags.append(f"CONF:{conf_gate_band}")
    if role:
        tags.append(f"ROLE:{role}")
    return tuple(tags)


@dataclass(frozen=True)
class CfDCompose:
    """Chair CF D SHADOW pack. ``broker_effect`` is always False."""

    choice: str
    size_factor: float
    miss: str
    keep: bool
    family: str
    session: str | None
    conf_shadow: str | None
    decided_by: str
    ablation: tuple[dict[str, Any], ...]
    score: float
    outcome: str | None
    religion_index_crypto_xa_size0: bool
    broker_effect: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "steal": STEAL,
            "choice": self.choice,
            "size_factor": self.size_factor,
            "miss": self.miss,
            "keep": self.keep,
            "family": self.family,
            "session": self.session,
            "conf_shadow": self.conf_shadow,
            "decided_by": self.decided_by,
            "ablation_order": list(ABLATION_ORDER),
            "ablation": [dict(step) for step in self.ablation],
            "score": self.score,
            "outcome": self.outcome,
            "house_keep_families_untouched": list(CHALLENGE_KEEP_FAMILIES),
            "cf_d_keep_families": sorted(CF_D_KEEP_FAMILIES),
            "hard_off_families_untouched": list(CHALLENGE_HARD_OFF_FAMILIES),
            "religion_index_crypto_xa_size0": False,
            "religion_index_crypto_xa_size0_revoked": True,
            "label_only": True,
            "never_place": True,
            "never_apply_size": True,
            "broker_effect": False,
        }


def _ablation_steps(
    *,
    miss: str,
    keep: bool,
    conf_shadow: str | None,
) -> tuple[tuple[dict[str, Any], ...], str, str]:
    """Walk miss › size › family › session › conf. First fire wins."""

    steps: list[dict[str, Any]] = []

    miss_fires = miss == "false_structure" and not keep
    steps.append(
        {
            "axis": "miss",
            "fires": miss_fires,
            "choice": "A_STAND_DOWN" if miss_fires else None,
            "note": (
                "keep_exempt_from_stand_down"
                if miss == "false_structure" and keep
                else ("fs_nonkeep_stand_down" if miss_fires else "not_false_structure")
            ),
        }
    )

    # F+G FS half is absorbed by miss stand_down. KEEP stays full.
    size_would = miss == "false_structure" and not keep
    steps.append(
        {
            "axis": "size",
            "fires": False,
            "choice": "B_SIZE_HALF" if size_would else None,
            "note": (
                "absorbed_by_miss_stand_down"
                if size_would
                else ("keep_full_no_fs_half" if miss == "false_structure" and keep else "no_fs_half")
            ),
        }
    )

    family_fires = keep
    steps.append(
        {
            "axis": "family",
            "fires": family_fires,
            "choice": "E_KEEP_CAP" if family_fires else None,
            "note": "keep_signature_exempt" if family_fires else "not_keep",
        }
    )

    session_fires = miss == "session_cut" and not keep
    steps.append(
        {
            "axis": "session",
            "fires": session_fires,
            "choice": "C_SIZE_TRIM" if session_fires else None,
            "note": "session_cut_nonkeep" if session_fires else "no_session_cut",
        }
    )

    conf_fires = (not keep) and (
        miss == "event_gap" or conf_shadow in {"CONF_GATE_STRICT", "CONF_GATE_EVENT"}
    )
    steps.append(
        {
            "axis": "conf",
            "fires": conf_fires,
            "choice": "B_SIZE_HALF" if conf_fires else None,
            "note": "conf_or_event_half" if conf_fires else "conf_not_binding",
        }
    )

    assert tuple(step["axis"] for step in steps) == ABLATION_ORDER
    for step in steps:
        if step["fires"] and step["choice"] in CHOICE_IDS:
            return tuple(steps), str(step["choice"]), str(step["axis"])
    return tuple(steps), "D_FULL", "size"


def compose_cf_d(
    *,
    gold_state: Mapping[str, Any] | None = None,
    sleeve: str | None = None,
    subclass: str | None = None,
    miss: str | None = None,
    keep_flag: bool | None = None,
    session: str | None = None,
    outcome: str | None = None,
    s15_band: str | None = None,
    family: str | None = None,
) -> CfDCompose:
    """Primary soft-policy compose. Code owns the choice. Never APPLY."""

    assert religion_index_crypto_xa_size0(sleeve=sleeve) is False
    assert RELIGION_INDEX_CRYPTO_XA_SIZE0 is False

    ident_miss = _identity_flag(gold_state, "cf_d_miss")
    ident_keep = _identity_flag(gold_state, "cf_d_keep")
    ident_outcome = _identity_flag(gold_state, "cf_d_outcome")
    ident_family = _identity_flag(gold_state, "cf_d_family")
    ident_sleeve = None
    ident_ticket = None
    if gold_state and isinstance(gold_state.get("identity"), Mapping):
        ident_sleeve = gold_state["identity"].get("sleeve")
        ident_ticket = gold_state["identity"].get("ticket")
        if subclass is None:
            subclass = gold_state["identity"].get("s15_subclass")
    if subclass is None and ident_ticket and str(ident_ticket) in TICKET_SUBCLASS:
        subclass = TICKET_SUBCLASS[str(ident_ticket)]

    resolved_sleeve = sleeve or (str(ident_sleeve) if ident_sleeve else None)
    resolved_family = family or (str(ident_family) if ident_family else classify_sleeve_family(resolved_sleeve))
    resolved_miss = classify_miss(
        subclass=subclass,
        miss=miss or (str(ident_miss) if ident_miss else None),
    )
    if keep_flag is not None:
        resolved_keep = bool(keep_flag)
    elif ident_keep is not None:
        resolved_keep = bool(ident_keep)
    else:
        resolved_keep = is_cf_d_keep(sleeve=resolved_sleeve, family=resolved_family)
    resolved_session = _named_session(gold_state, session)
    resolved_outcome = outcome or (str(ident_outcome) if ident_outcome else None)

    cf = label_cf_priority(
        gold_state=gold_state,
        sleeve=resolved_sleeve,
        subclass=subclass,
        s15_band=s15_band,
    )
    conf_shadow = cf.conf_shadow or classify_conf_shadow(
        subclass=subclass,
        sleeve=resolved_sleeve,
        allow=cf.sleeve_allow,
        s15_band=s15_band,
    )

    ablation, choice, decided_by = _ablation_steps(
        miss=resolved_miss,
        keep=resolved_keep,
        conf_shadow=conf_shadow,
    )
    return CfDCompose(
        choice=choice,
        size_factor=SIZE_BY_CHOICE[choice],
        miss=resolved_miss,
        keep=resolved_keep,
        family=resolved_family,
        session=resolved_session,
        conf_shadow=conf_shadow,
        decided_by=decided_by,
        ablation=ablation,
        score=score_cf_d(choice, outcome=resolved_outcome, keep=resolved_keep),
        outcome=resolved_outcome,
        religion_index_crypto_xa_size0=False,
    )


def load_cf_d_report(path: Path | None = None) -> dict[str, Any]:
    target = path if path is not None else REPORT_PATH
    if not target.is_file():
        return {
            "schema": REPORT_SCHEMA,
            "CF_D_sum_R": 11.1678,
            "place": False,
            "religion": False,
            "note": "cf_d_report_missing_constants_only",
        }
    return json.loads(target.read_text(encoding="utf-8"))


def load_question_bank(path: Path | None = None) -> dict[str, Any]:
    target = path if path is not None else BANK_PATH
    if not target.is_file():
        return {
            "schema": BANK_SCHEMA,
            "login": int(CHALLENGE_LOGIN),
            "n_questions": 0,
            "questions": [],
            "place": False,
        }
    return json.loads(target.read_text(encoding="utf-8"))


def chair_choice_for_bank_tape(tape: Mapping[str, Any]) -> CfDCompose:
    """Chair CF D answer for one bank tape row (not the F+G-era train hint)."""

    return compose_cf_d(
        sleeve=str(tape.get("sleeve") or "") or None,
        family=str(tape.get("family") or "") or None,
        miss=str(tape.get("miss") or "") or None,
        keep_flag=bool(tape.get("keep")),
        session=str(tape.get("session") or "") or None,
        outcome=str(tape.get("outcome") or "") or None,
        s15_band=str(tape.get("conf_gate_band") or "") or None,
    )


def question_bank_rows() -> list[dict[str, Any]]:
    """Ten Chair bank tickets as historical gold_state rows. No live bars."""

    from .s14_tape import _answers as _s14_answers
    from .s14_tape import gold_state as s14_gold_state

    bank = load_question_bank()
    rows: list[dict[str, Any]] = []
    for raw in bank.get("questions") or []:
        if not isinstance(raw, Mapping):
            continue
        tape = raw.get("tape") if isinstance(raw.get("tape"), Mapping) else {}
        ticket = str(raw.get("ticket") or "")
        if not ticket:
            continue
        sleeve = str(tape.get("sleeve") or "")
        family = str(tape.get("family") or classify_sleeve_family(sleeve))
        session = str(tape.get("session") or "off_hours")
        asset = str(tape.get("asset") or "")
        symbol = BANK_SYMBOL_BY_TICKET.get(ticket)
        if not symbol:
            symbol = "XAUUSD" if asset == "XAU" else "EURUSD"
        side = BANK_SIDE_BY_TICKET.get(ticket, "long")
        miss = classify_miss(miss=str(tape.get("miss") or "") or None)
        subclass = {
            "false_structure": "fs_half_still_losing",
            "event_gap": "event_gap_shadow",
            "session_cut": "session_cut_loss",
            "ok_win": "ok_win",
        }.get(miss)
        cid = f"challenge:{CHALLENGE_LOGIN}:{ticket}:{sleeve or family}:{side}"
        gold = s14_gold_state(
            sleeve=sleeve or family,
            symbol=symbol,
            side=side,
            candidate_id=cid,
            close_ret_1=0.008 if str(tape.get("outcome")) == "WIN" else -0.012,
            close_ret_5bar=0.02 if str(tape.get("outcome")) == "WIN" else -0.028,
            vol_ratio=0.95,
            htf_slope_norm=0.6 if str(tape.get("outcome")) == "WIN" else -0.6,
            mom_20_atr=0.4 if str(tape.get("outcome")) == "WIN" else -0.4,
            session=session,
            spine_empty=miss != "event_gap",
            events=(
                [{"source": "stamped", "stamped": True, "proximity": True, "ticket": ticket}]
                if miss == "event_gap"
                else []
            ),
        )
        ident = dict(gold.get("identity") or {})
        ident.update(
            {
                "ticket": ticket,
                "s15_subclass": subclass,
                "cf_d_miss": miss,
                "cf_d_keep": bool(tape.get("keep")),
                "cf_d_family": family,
                "cf_d_outcome": tape.get("outcome"),
                "cf_d_R": tape.get("R"),
                "cf_d_exit": tape.get("exit"),
                "cf_d_cost_band": tape.get("cost_band"),
                "cf_d_conf_gate_band": tape.get("conf_gate_band"),
                "cf_d_asset": asset,
                "cf_d_role": raw.get("role"),
            }
        )
        gold["identity"] = ident
        composed = chair_choice_for_bank_tape(tape)
        rows.append(
            {
                "tape_id": f"cf-d-bank-{ticket}",
                "login": CHALLENGE_LOGIN,
                "ticket": ticket,
                "subclass": subclass,
                "g4_applies": False,
                "note": f"chair_cf_d_bank_{raw.get('role')}",
                "gold_state": gold,
                "system_one_answers": _s14_answers(
                    "trend_up" if str(tape.get("outcome")) == "WIN" else "trend_down",
                    0.86 if bool(tape.get("keep")) else 0.62,
                    0.22,
                    0.70,
                ),
                "bank_question": dict(raw),
                "cf_d_expected": composed.as_dict(),
            }
        )
    return rows
