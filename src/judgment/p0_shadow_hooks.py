"""P0 unwired SHADOW hooks on the Challenge fluid-gate sidecar.

FIRE 1404 ICT 2026-09-20. Challenge login 0 only.

Stamps ``warroom_shadow`` beside the existing ``jev_fluid_gate_v1`` admit
row. ``apply`` is **always False**. Never place / remint / flatten /
``order_send``. Never invent ``NEWS_PROTOCOL``. Never set
``GTOS_JEV_FLUID_GATES_APPLY`` or ``GTOS_DIG_MULTI_STAGE_GUARD_APPLY``.

KEEP signature is read from **STATE**, not from a sleeve-name allowlist.
Affinity is instrument × sleeve on the row — no global rule. Cost is
disclosure only (PR35): never a kill-gate. Expanding harden / V3 stays
PARKED (no third feature).

Hist labels still lack numeric confidence (FIRE 1201). Band floors are
SHADOW labels only — they must not flip APPLY.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .challenge import CHALLENGE_LOGIN, account_surface
from .conf_gate import REVIEW_KEEP_TICKET, classify_s15_subclass
from .flags import APPLY_ENV
from .s16_flags import APPLY_ENV as DIG_APPLY_ENV

SCHEMA = "gtos.judgment.warroom_shadow.v1"
STEAL = "P0_UNWIRED_SHADOW_HOOK_STUBS"
NAMESPACE = "gtos.astra.jev_trial.warroom_shadow.v1"

WEIGHTS_PATH = (
    Path(__file__).resolve().parents[2]
    / "judgment"
    / "astra"
    / "conf_gate_band_weights_shadow.json"
)
STUBS_PATH = (
    Path(__file__).resolve().parents[2]
    / "judgment"
    / "astra"
    / "p0_unwired_shadow_hook_stubs.json"
)

BAND_SHORT = {
    "CONF_GATE_STRICT": "STRICT",
    "CONF_GATE_SESSION": "SESSION",
    "CONF_GATE_EVENT": "EVENT",
    "CONF_GATE_REVIEW": "REVIEW",
    "CONF_GATE_KEEP": "KEEP",
    "STRICT": "STRICT",
    "SESSION": "SESSION",
    "EVENT": "EVENT",
    "REVIEW": "REVIEW",
    "KEEP": "KEEP",
}

S15_BAND_PRIORITY = ("STRICT", "SESSION", "EVENT", "REVIEW")

MISS_BY_SUBCLASS = {
    "fs_half_still_losing": "false_structure",
    "review_keep_offhours_false_structure": "false_structure",
    "full_size_loss": "false_structure",
    "event_gap_shadow": "event_gap",
    "session_cut_loss": "session_cut",
    "ok_win": "ok_win",
}

REVIEW_KEEP_CHOICES = ("REVIEW_KEEP", "FAMILY_LOSER", "UNSURE")
FS_MISS_CHOICES = ("STAND_DOWN", "KEEP_EXEMPT", "NOT_FS")
SIZE_INTENT_CHOICES = ("STAND_DOWN", "HALF", "TRIM", "FULL", "KEEP_CAP")


def load_band_weights(path: Path | None = None) -> dict[str, Any]:
    target = path if path is not None else WEIGHTS_PATH
    if not target.is_file():
        return {
            "schema": "gtos.warroom.conf_gate_band_weights_shadow.v1",
            "fire": "1201",
            "login": CHALLENGE_LOGIN,
            "apply": False,
            "numeric_conf_on_hist_labels": False,
            "do_not_flip_apply": True,
            "bands": {},
        }
    doc = json.loads(target.read_text(encoding="utf-8"))
    doc["apply"] = False
    doc["do_not_flip_apply"] = True
    return doc


def load_hook_stubs(path: Path | None = None) -> dict[str, Any]:
    target = path if path is not None else STUBS_PATH
    if not target.is_file():
        return {
            "schema": "gtos.dig.p0_unwired_shadow_hook_stubs.v1",
            "apply": False,
            "hooks": {},
        }
    doc = json.loads(target.read_text(encoding="utf-8"))
    doc["apply"] = False
    return doc


def _as_mapping(obj: Any) -> Mapping[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, Mapping):
        return obj
    as_dict = getattr(obj, "as_dict", None)
    if callable(as_dict):
        out = as_dict()
        if isinstance(out, Mapping):
            return out
    return {}


def _identity(gold_state: Mapping[str, Any] | None) -> dict[str, Any]:
    if not gold_state:
        return {}
    ident = gold_state.get("identity")
    return dict(ident) if isinstance(ident, Mapping) else {}


def _chair_pack(gold_state: Mapping[str, Any] | None, regime: Any) -> dict[str, Any]:
    if gold_state:
        chair = gold_state.get("chair")
        if isinstance(chair, Mapping):
            return dict(chair)
    if regime is None:
        return {}
    chair_obj = getattr(regime, "chair", None)
    if chair_obj is not None:
        return _as_mapping(chair_obj)
    pack = _as_mapping(regime)
    nested = pack.get("chair")
    return dict(nested) if isinstance(nested, Mapping) else {}


def _boolish(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"1", "true", "yes", "on"}:
            return True
        if raw in {"0", "false", "no", "off"}:
            return False
    return None


def keep_signature_from_state(
    gold_state: Mapping[str, Any] | None = None,
    *,
    regime: Any = None,
) -> dict[str, Any]:
    """KEEP signature from STATE fields only — never a name allowlist.

    Affinity is the instrument × sleeve pair on this row. Missing STATE
    ⇒ ``present=False``, noul 0.0. A sleeve named ``spring`` without a
    STATE keep field is **not** KEEP here.
    """

    ident = _identity(gold_state)
    chair = _chair_pack(gold_state, regime)
    instrument = str(ident.get("symbol") or ident.get("instrument") or "") or None
    sleeve = str(ident.get("sleeve") or "") or None

    source = None
    present = False
    noul = 0.0
    note = "keep_signature_unset_no_state_field"

    raw_sig = ident.get("keep_signature")
    if raw_sig is None:
        raw_sig = ident.get("keep_sig")
    if isinstance(raw_sig, Mapping):
        flag = _boolish(raw_sig.get("present") if "present" in raw_sig else raw_sig.get("keep"))
        try:
            noul_val = float(raw_sig.get("noul"))
        except (TypeError, ValueError):
            noul_val = None
        if flag is not None:
            present = flag
            noul = noul_val if noul_val is not None else (1.0 if flag else 0.0)
            source = "identity.keep_signature"
            note = "keep_signature_from_identity_state"
        elif noul_val is not None:
            present = noul_val >= 0.5
            noul = noul_val
            source = "identity.keep_signature.noul"
            note = "keep_signature_from_identity_noul"
    else:
        flag = _boolish(raw_sig)
        if flag is not None:
            present = flag
            noul = 1.0 if flag else 0.0
            source = "identity.keep_signature"
            note = "keep_signature_from_identity_state"

    if source is None:
        flag = _boolish(ident.get("cf_d_keep"))
        if flag is not None:
            present = flag
            noul = 1.0 if flag else 0.0
            source = "identity.cf_d_keep"
            note = "keep_signature_from_identity_cf_d_keep"

    if source is None:
        flag = _boolish(chair.get("keep_family"))
        if flag is not None:
            present = flag
            noul = 1.0 if flag else 0.0
            source = "chair.keep_family"
            note = "keep_signature_from_chair_state_stamp"

    if source is None and gold_state:
        flag = _boolish(gold_state.get("keep_signature"))
        if flag is not None:
            present = flag
            noul = 1.0 if flag else 0.0
            source = "gold_state.keep_signature"
            note = "keep_signature_from_gold_state"

    noul = max(0.0, min(1.0, float(noul)))
    return {
        "present": present,
        "noul": noul,
        "source": source,
        "note": note,
        "name_allowlist_used": False,
        "affinity": {
            "instrument": instrument,
            "sleeve": sleeve,
            "pair": (
                f"{instrument}×{sleeve}"
                if instrument and sleeve
                else None
            ),
            "global_rule": False,
        },
        "login": CHALLENGE_LOGIN,
    }


def _s15_short_band(cost: Any, gold_state: Mapping[str, Any] | None) -> str | None:
    pack = _as_mapping(cost)
    raw = pack.get("conf_gate_band")
    if not raw and gold_state:
        ident = _identity(gold_state)
        raw = ident.get("cf_d_conf_gate_band") or ident.get("conf_gate_band")
    if raw is None:
        return None
    return BAND_SHORT.get(str(raw).strip().upper())


def _ticket_of(gold_state: Mapping[str, Any] | None, cost: Any) -> str | None:
    ident = _identity(gold_state)
    if ident.get("ticket") is not None:
        return str(ident.get("ticket"))
    pack = _as_mapping(cost)
    if pack.get("ticket") is not None:
        return str(pack.get("ticket"))
    return None


def _miss_of(gold_state: Mapping[str, Any] | None, cost: Any) -> str:
    ident = _identity(gold_state)
    raw = ident.get("cf_d_miss")
    if raw:
        return str(raw)
    subclass = ident.get("s15_subclass")
    pack = _as_mapping(cost)
    subclass = subclass or pack.get("subclass")
    mapped = MISS_BY_SUBCLASS.get(str(subclass or "").strip())
    if mapped:
        return mapped
    if gold_state is not None:
        resolved = classify_s15_subclass(
            stake="sleeve_admit",
            ticket=_ticket_of(gold_state, cost),
            subclass=str(subclass) if subclass else None,
            gold_state=gold_state,
        )
        mapped = MISS_BY_SUBCLASS.get(str(resolved or "").strip())
        if mapped:
            return mapped
    return "unknown"


def _outcome_of(gold_state: Mapping[str, Any] | None) -> str | None:
    ident = _identity(gold_state)
    raw = ident.get("cf_d_outcome") or ident.get("outcome")
    return str(raw) if raw else None


def _explicit_size_intent(gold_state: Mapping[str, Any] | None) -> str | None:
    ident = _identity(gold_state)
    raw = ident.get("size_intent") or ident.get("cf_d_size_intent")
    if raw is None:
        return None
    token = str(raw).strip().upper()
    aliases = {
        "A_STAND_DOWN": "STAND_DOWN",
        "B_SIZE_HALF": "HALF",
        "C_SIZE_TRIM": "TRIM",
        "D_FULL": "FULL",
        "E_KEEP_CAP": "KEEP_CAP",
        "STAND_DOWN": "STAND_DOWN",
        "HALF": "HALF",
        "TRIM": "TRIM",
        "FULL": "FULL",
        "KEEP_CAP": "KEEP_CAP",
    }
    return aliases.get(token)


def conf_gate_band_disposition(
    *,
    s15_band: str | None,
    keep_present: bool,
) -> str | None:
    """STRICT/SESSION/EVENT/REVIEW from S15; KEEP when STATE keep and no S15 cut."""

    if s15_band in S15_BAND_PRIORITY:
        return s15_band
    if keep_present:
        return "KEEP"
    return None


def choice_keep_review_win_vs_family_loser(
    *,
    keep_present: bool,
    ticket: str | None,
    outcome: str | None,
    miss: str,
    s15_band: str | None,
) -> dict[str, Any]:
    """P0_KEEP_REVIEW_WIN_VS_FAMILY_LOSER — Choice. Cost is not a kill-gate."""

    out = (outcome or "").strip().upper()
    if keep_present and (
        str(ticket or "") == REVIEW_KEEP_TICKET
        or out == "WIN"
        or s15_band == "REVIEW"
    ):
        choice = "REVIEW_KEEP"
        note = "keep_state_review_or_win"
    elif (not keep_present) and (miss == "false_structure" or out == "LOSS"):
        choice = "FAMILY_LOSER"
        note = "nonkeep_family_loser_or_fs"
    else:
        choice = "UNSURE"
        note = "not_review_keep_and_not_family_loser"
    return {
        "id": "P0_KEEP_REVIEW_WIN_VS_FAMILY_LOSER",
        "role": "Choice",
        "choice": choice,
        "allowed": list(REVIEW_KEEP_CHOICES),
        "note": note,
        "apply": False,
        "cost_kill_gate": False,
    }


def choice_cfd_miss_false_structure(*, keep_present: bool, miss: str) -> dict[str, Any]:
    """P0_CFD_MISS_FALSE_STRUCTURE — Choice. CF D miss axis, STATE keep."""

    if miss == "false_structure" and not keep_present:
        choice, note = "STAND_DOWN", "fs_nonkeep_stand_down"
    elif miss == "false_structure" and keep_present:
        choice, note = "KEEP_EXEMPT", "fs_keep_exempt_from_stand_down"
    else:
        choice, note = "NOT_FS", "not_false_structure"
    return {
        "id": "P0_CFD_MISS_FALSE_STRUCTURE",
        "role": "Choice",
        "choice": choice,
        "allowed": list(FS_MISS_CHOICES),
        "miss": miss,
        "note": note,
        "apply": False,
    }


def choice_cfd_size_intent(
    *,
    keep_present: bool,
    miss: str,
    explicit: str | None,
) -> dict[str, Any]:
    """P0_CFD_SIZE_INTENT — Choice. Label only; never APPLY size."""

    if explicit in SIZE_INTENT_CHOICES:
        choice, note = explicit, "size_intent_from_state"
    elif miss == "false_structure" and not keep_present:
        choice, note = "STAND_DOWN", "fs_nonkeep_size_zero_label"
    elif miss == "false_structure" and keep_present:
        choice, note = "KEEP_CAP", "fs_keep_full_label"
    elif miss == "session_cut" and not keep_present:
        choice, note = "TRIM", "session_cut_nonkeep_trim_label"
    elif miss == "event_gap" and not keep_present:
        choice, note = "HALF", "event_gap_nonkeep_half_label"
    elif keep_present:
        choice, note = "KEEP_CAP", "keep_state_full_label"
    else:
        choice, note = "FULL", "default_full_label"
    return {
        "id": "P0_CFD_SIZE_INTENT",
        "role": "Choice",
        "choice": choice,
        "allowed": list(SIZE_INTENT_CHOICES),
        "note": note,
        "apply": False,
        "never_apply_size": True,
    }


def noul_cfd_sleeve_family_keep_sig(keep: Mapping[str, Any]) -> dict[str, Any]:
    """P0_CFD_SLEEVE_FAMILY_KEEP_SIG — Noul. STATE keep, affinity pair."""

    return {
        "id": "P0_CFD_SLEEVE_FAMILY_KEEP_SIG",
        "role": "Noul",
        "noul": float(keep.get("noul") or 0.0),
        "present": bool(keep.get("present")),
        "source": keep.get("source"),
        "note": keep.get("note"),
        "name_allowlist_used": False,
        "affinity": dict(keep.get("affinity") or {}),
        "apply": False,
    }


@dataclass(frozen=True)
class WarroomShadow:
    """Cycle-log sidecar. ``apply`` is hardcoded False."""

    payload: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        out = dict(self.payload)
        out["apply"] = False
        out["broker_effect"] = False
        out["never_place"] = True
        return out


def compose_warroom_shadow(
    *,
    gold_state: Mapping[str, Any] | None = None,
    regime: Any = None,
    cost: Any = None,
    stake: str = "sleeve_admit",
) -> WarroomShadow:
    """Build the P0 SHADOW pack. APPLY is refused even if Chair later NAMEs it."""

    weights = load_band_weights()
    stubs = load_hook_stubs()
    ident = _identity(gold_state)
    keep = keep_signature_from_state(gold_state, regime=regime)
    s15_band = _s15_short_band(cost, gold_state)
    ticket = _ticket_of(gold_state, cost)
    miss = _miss_of(gold_state, cost)
    outcome = _outcome_of(gold_state)
    disposition = conf_gate_band_disposition(
        s15_band=s15_band,
        keep_present=bool(keep["present"]),
    )
    floor = None
    bands = weights.get("bands") if isinstance(weights.get("bands"), Mapping) else {}
    if disposition and isinstance(bands.get(disposition), Mapping):
        floor = bands[disposition].get("conf_floor")

    keep_review = choice_keep_review_win_vs_family_loser(
        keep_present=bool(keep["present"]),
        ticket=ticket,
        outcome=outcome,
        miss=miss,
        s15_band=s15_band,
    )
    fs_miss = choice_cfd_miss_false_structure(
        keep_present=bool(keep["present"]),
        miss=miss,
    )
    size_intent = choice_cfd_size_intent(
        keep_present=bool(keep["present"]),
        miss=miss,
        explicit=_explicit_size_intent(gold_state),
    )
    keep_noul = noul_cfd_sleeve_family_keep_sig(keep)

    payload = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "steal": STEAL,
        "mode": "shadow_log_only",
        "login": CHALLENGE_LOGIN,
        "account_surface": account_surface(),
        "apply": False,
        "apply_env_read": APPLY_ENV,
        "apply_env_set": False,
        "dig_apply_env": DIG_APPLY_ENV,
        "dig_apply_env_set": False,
        "broker_effect": False,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_order_send": True,
        "news_protocol": "stamps_only_never_invent",
        "cost_kill_gate": False,
        "numeric_conf_on_hist_labels": False,
        "do_not_flip_apply": True,
        "fire_1201_floors_shadow_only": True,
        "expanding_harden_v3": "PARKED",
        "stake": stake,
        "ticket": ticket,
        "miss": miss,
        "s15_conf_gate_band": s15_band,
        "conf_gate_band_disposition": disposition,
        "conf_floor": floor,
        "keep_signature": keep,
        "research_armed_tags": list(
            ident.get("research_armed_tags")
            or (gold_state or {}).get("research_armed_tags")
            or []
        ),
        "research_overlay": dict(ident.get("research_overlay") or {}),
        "P0_KEEP_REVIEW_WIN_VS_FAMILY_LOSER": keep_review,
        "P0_CFD_MISS_FALSE_STRUCTURE": fs_miss,
        "P0_CFD_SIZE_INTENT": size_intent,
        "P0_CFD_SLEEVE_FAMILY_KEEP_SIG": keep_noul,
        "hooks_pack": {
            "schema": stubs.get("schema"),
            "apply": False,
        },
        "weights_pack": {
            "schema": weights.get("schema"),
            "fire": weights.get("fire"),
            "apply": False,
            "numeric_conf_on_hist_labels": False,
        },
    }
    return WarroomShadow(payload=payload)
