"""P0 hist-prove helpers — FIRE 1201 residual vs KEEP-win labels.

Challenge login 0 only. LABEL only. Never APPLY / place /
``order_send``. Residuals stay SHADOW-PARKED. KEEP wins must stay
preserved under stacked S15 + P0 bands.

Chair enable path is ``GTOS_JEV_FLUID_GATES_SHADOW=1`` alone.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .challenge import CHALLENGE_LOGIN
from .conf_gate import REVIEW_KEEP_TICKET, REVIEW_OFFHOURS_TICKET
from .flags import APPLY_ENV, SHADOW_ENV
from .s16_flags import APPLY_ENV as DIG_APPLY_ENV

FIRE1201_RECEIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "judgment"
    / "astra"
    / "lab"
    / "p0_warroom_shadow_prove"
    / "FIRE1201_HIST_PROVE_RECEIPT.json"
)

#: FIRE 1201 residual KEEP FS tickets (−2.14 R). SHADOW labels PARKED.
FIRE_1201_RESIDUAL_TICKETS = (REVIEW_KEEP_TICKET, REVIEW_OFFHOURS_TICKET)
FIRE_1201_RESIDUAL_R = {
    REVIEW_KEEP_TICKET: -1.2007,
    REVIEW_OFFHOURS_TICKET: -0.94,
}
FIRE_1201_RESIDUAL_R_SUM = -2.14

#: FIRE 1201 KEEP wins the UB stack must not flip. Headline +12.34 R
#: is the stacked CONF_GATE UB figure; prove is LABEL on these three.
FIRE_1201_KEEP_WIN_TICKETS = ("291816474", "293540988", "291794419")
FIRE_1201_KEEP_WIN_R = {
    "291816474": 1.87,
    "293540988": 2.962,
    "291794419": 3.02,
}
FIRE_1201_UB_WINS_PRESERVED_R = 12.34

AUTHORITY_SOURCE = "cf_d_bank"
ECHO_SOURCE = "s15_tape"

_TRUTHY = frozenset({"1", "true", "yes", "on"})

SAFE_RESIDUAL_DISPOSITIONS = frozenset({"REVIEW", "KEEP"})
SAFE_WIN_DISPOSITIONS = frozenset({"KEEP"})


def fire_1201_cohort(ticket: str | None) -> str | None:
    raw = str(ticket or "").strip()
    if raw in FIRE_1201_RESIDUAL_TICKETS:
        return "residual"
    if raw in FIRE_1201_KEEP_WIN_TICKETS:
        return "keep_win"
    return None


def row_source(tape_row: Mapping[str, Any] | None) -> str | None:
    """cf_d_bank carries STATE keep + tape band; S15 tape is an echo."""

    if not tape_row:
        return None
    if tape_row.get("bank_question") is not None:
        return AUTHORITY_SOURCE
    tape_id = str(tape_row.get("tape_id") or "")
    if tape_id.startswith("cf-d-bank-"):
        return AUTHORITY_SOURCE
    if tape_id.startswith("review-") or tape_id.startswith("fs-") or tape_id.startswith(
        "session-"
    ) or tape_id.startswith("event-") or tape_id.startswith("reject-"):
        return ECHO_SOURCE
    note = str(tape_row.get("note") or "")
    if note.startswith("chair_cf_d_bank_"):
        return AUTHORITY_SOURCE
    return None


def _env_on(value: str | None) -> bool:
    return str(value or "").strip().lower() in _TRUTHY


def load_fire1201_receipt(*, path: Path | str | None = None) -> dict[str, Any] | None:
    """Committed FIRE 1201 hist-prove receipt. Missing file ⇒ None."""

    target = Path(path) if path is not None else FIRE1201_RECEIPT_PATH
    if not target.is_file():
        return None
    return json.loads(target.read_text(encoding="utf-8"))


def hist_prove_allows_label_apply(
    *,
    path: Path | str | None = None,
    receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Optional LABEL APPLY only after hist-prove preserves KEEP wins.

    Hist-prove itself still refuses APPLY env (exit 2). This gate is the
    Chair path *after* that prove: LABEL draft only, never place, never
    hard-off KEEP research.
    """

    doc = dict(receipt) if receipt is not None else load_fire1201_receipt(path=path)
    if not doc:
        return {
            "allowed": False,
            "reason": "hist_prove_receipt_missing",
            "wins_preserved": False,
            "hard_off_keep_research": False,
        }
    wins = bool(doc.get("wins_preserved"))
    hard_off = bool(doc.get("hard_off_keep_research"))
    candidate = doc.get("research_candidate") or {}
    if isinstance(candidate, Mapping):
        hard_off = hard_off or bool(candidate.get("hard_off_keep_research"))
    if not wins:
        return {
            "allowed": False,
            "reason": "hist_prove_keep_wins_not_preserved",
            "wins_preserved": False,
            "hard_off_keep_research": hard_off,
        }
    if hard_off:
        return {
            "allowed": False,
            "reason": "hist_prove_hard_off_keep_research",
            "wins_preserved": True,
            "hard_off_keep_research": True,
        }
    from .place_apply import evaluate_place_apply

    unlocked = evaluate_place_apply(skip_hist=True, hist_prove={"allowed": True})
    return {
        "allowed": True,
        "reason": (
            "hist_prove_keep_wins_preserved_place_apply"
            if unlocked.allowed
            else "hist_prove_keep_wins_preserved_label_only"
        ),
        "wins_preserved": True,
        "hard_off_keep_research": False,
        "never_place": not unlocked.allowed,
        "never_remint": not unlocked.allowed,
        "never_flatten": not unlocked.allowed,
        "place_apply": unlocked.allowed,
        "place_apply_reason": unlocked.reason,
    }


def apply_env_refused(*, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Chair path refuses APPLY / Dig APPLY. SHADOW-only."""

    import os

    env = environ if environ is not None else os.environ
    apply_on = _env_on(env.get(APPLY_ENV))
    dig_on = _env_on(env.get(DIG_APPLY_ENV))
    shadow_on = _env_on(env.get(SHADOW_ENV))
    return {
        "shadow_env": SHADOW_ENV,
        "shadow_env_set": shadow_on,
        "apply_env": APPLY_ENV,
        "apply_env_set": apply_on,
        "dig_apply_env": DIG_APPLY_ENV,
        "dig_apply_env_set": dig_on,
        "refused": bool(apply_on or dig_on),
        "refuse_reason": (
            "apply_env_set"
            if apply_on
            else ("dig_apply_env_set" if dig_on else None)
        ),
    }


def stacked_band_row(
    *,
    ticket: str,
    tape_row: Mapping[str, Any],
    pack: Mapping[str, Any],
) -> dict[str, Any] | None:
    """One LABEL row for a FIRE 1201 ticket. ``apply`` is always false."""

    cohort = fire_1201_cohort(ticket)
    if cohort is None:
        return None
    source = row_source(tape_row) or "unknown"
    disposition = pack.get("conf_gate_band_disposition")
    s15_band = pack.get("s15_conf_gate_band")
    keep_sig = pack.get("P0_CFD_SLEEVE_FAMILY_KEEP_SIG") or pack.get("keep_signature") or {}
    miss = pack.get("P0_CFD_MISS_FALSE_STRUCTURE") or {}
    size = pack.get("P0_CFD_SIZE_INTENT") or {}
    review = pack.get("P0_KEEP_REVIEW_WIN_VS_FAMILY_LOSER") or {}
    keep_present = bool(keep_sig.get("present"))
    miss_choice = miss.get("choice")
    size_choice = size.get("choice")
    review_choice = review.get("choice")
    apply_true = pack.get("apply") is True
    hard_off_label = miss_choice == "STAND_DOWN" and not keep_present
    r_value = (
        FIRE_1201_RESIDUAL_R.get(ticket)
        if cohort == "residual"
        else FIRE_1201_KEEP_WIN_R.get(ticket)
    )
    wins_preserved_row = bool(
        cohort == "keep_win"
        and source == AUTHORITY_SOURCE
        and disposition in SAFE_WIN_DISPOSITIONS
        and size_choice == "KEEP_CAP"
        and miss_choice != "STAND_DOWN"
        and apply_true is False
        and keep_present
    )
    residual_parked_row = bool(
        cohort == "residual"
        and source == AUTHORITY_SOURCE
        and disposition in SAFE_RESIDUAL_DISPOSITIONS
        and miss_choice == "KEEP_EXEMPT"
        and apply_true is False
        and keep_present
        and hard_off_label is False
    )
    return {
        "ticket": ticket,
        "login": CHALLENGE_LOGIN,
        "cohort": cohort,
        "source": source,
        "authority": source == AUTHORITY_SOURCE,
        "tape_id": tape_row.get("tape_id"),
        "R": r_value,
        "s15_conf_gate_band": s15_band,
        "conf_gate_band_disposition": disposition,
        "stacked_bands": [s15_band, disposition],
        "keep_present": keep_present,
        "keep_noul": keep_sig.get("noul"),
        "name_allowlist_used": bool(keep_sig.get("name_allowlist_used")),
        "miss_choice": miss_choice,
        "size_intent": size_choice,
        "review_keep_choice": review_choice,
        "apply": False,
        "hard_off": False if residual_parked_row or wins_preserved_row else hard_off_label,
        "wins_preserved_row": wins_preserved_row,
        "residual_parked_row": residual_parked_row,
        "label_only": True,
        "cost_kill_gate": False,
        "news_invent": False,
    }


def _authority_rows(rows: list[Mapping[str, Any]], cohort: str) -> list[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if row.get("cohort") == cohort and row.get("source") == AUTHORITY_SOURCE
    ]


def research_candidate_from_rows(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """EMPTY unless a thin durable SHADOW fact appears that does not hard-off KEEP.

    Confirmation that KEEP wins stay KEEP and residuals stay REVIEW/KEEP_EXEMPT
    is the parked FIRE 1201 label, not a new candidate. S15-tape echoes
    without STATE keep are the existing P0 law (STATE, not name).
    """

    authority_wins = _authority_rows(rows, "keep_win")
    authority_resid = _authority_rows(rows, "residual")
    wins_ok = bool(authority_wins) and all(r.get("wins_preserved_row") for r in authority_wins)
    resid_ok = bool(authority_resid) and all(r.get("residual_parked_row") for r in authority_resid)
    if wins_ok and resid_ok:
        return {
            "status": "EMPTY",
            "hard_off_keep_research": False,
            "note": (
                "no thin durable SHADOW observation beyond parked FIRE 1201 "
                "labels; KEEP wins preserved; residuals REVIEW/KEEP_EXEMPT; "
                "do not hard-off KEEP research"
            ),
        }
    return {
        "status": "EMPTY",
        "hard_off_keep_research": False,
        "note": (
            "no candidate that hard-offs KEEP research; incomplete or "
            "echo-only rows stay LABEL; expanding/spring harden PARKED"
        ),
    }


def summarize_fire_1201(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Disposition counts vs residual / KEEP-win tickets. LABEL only."""

    authority_wins = _authority_rows(rows, "keep_win")
    authority_resid = _authority_rows(rows, "residual")
    win_dispositions = Counter(
        str(r.get("conf_gate_band_disposition") or "NONE") for r in authority_wins
    )
    residual_dispositions = Counter(
        str(r.get("conf_gate_band_disposition") or "NONE") for r in authority_resid
    )
    echo_dispositions = Counter(
        str(r.get("conf_gate_band_disposition") or "NONE")
        for r in rows
        if r.get("source") == ECHO_SOURCE
    )
    seen_wins = {str(r.get("ticket")) for r in authority_wins}
    seen_resid = {str(r.get("ticket")) for r in authority_resid}
    wins_preserved = bool(
        set(FIRE_1201_KEEP_WIN_TICKETS) <= seen_wins
        and all(r.get("wins_preserved_row") for r in authority_wins)
        and all(r.get("apply") is False for r in authority_wins)
    )
    residual_parked = bool(
        set(FIRE_1201_RESIDUAL_TICKETS) <= seen_resid
        and all(r.get("residual_parked_row") for r in authority_resid)
        and all(r.get("apply") is False for r in authority_resid)
    )
    candidate = research_candidate_from_rows(rows)
    return {
        "schema": "gtos.judgment.p0_fire1201_hist_prove.v1",
        "login": CHALLENGE_LOGIN,
        "label_only": True,
        "apply": False,
        "do_not_flip_apply": True,
        "fire": "1201",
        "ub_wins_preserved_R_headline": FIRE_1201_UB_WINS_PRESERVED_R,
        "residual_R_sum": FIRE_1201_RESIDUAL_R_SUM,
        "residual_tickets": list(FIRE_1201_RESIDUAL_TICKETS),
        "keep_win_tickets": list(FIRE_1201_KEEP_WIN_TICKETS),
        "authority_source": AUTHORITY_SOURCE,
        "echo_source": ECHO_SOURCE,
        "n_authority_keep_wins": len(authority_wins),
        "n_authority_residuals": len(authority_resid),
        "disposition_counts": {
            "keep_win": dict(win_dispositions),
            "residual": dict(residual_dispositions),
            "s15_echo": dict(echo_dispositions),
        },
        "tickets": list(rows),
        "wins_preserved": wins_preserved,
        "residual_shadow_parked": residual_parked,
        "residual_not_hard_off": residual_parked,
        "hard_off_keep_research": False,
        "research_candidate": candidate,
        "expanding_harden_v3": "PARKED",
        "gbpjpy_sub_mid_dig_geometry": "PARKED",
        "cost_kill_gate": False,
        "news_invent": False,
        "never_place": True,
    }
