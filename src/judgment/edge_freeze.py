"""Edge FREEZE — both sleeve.*_ready Choices.

Authority: ``GBPJPY_APLUS_FREEZE.md`` + ``XAU_DSP_SHAKEOUT_EVENT_GAP.md``.
Documented in ``APLUS_SLEEVES_ON_GATES.md``. SHADOW only. Not admit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
GBPJPY_FREEZE = REPO_ROOT / "judgment" / "astra" / "GBPJPY_APLUS_FREEZE.md"
XAU_FREEZE = REPO_ROOT / "judgment" / "astra" / "XAU_DSP_SHAKEOUT_EVENT_GAP.md"
APLUS_DOC = REPO_ROOT / "judgment" / "astra" / "APLUS_SLEEVES_ON_GATES.md"

GBPJPY_READY = "sleeve.gbpjpy_a_plus_ready"
XAU_READY = "sleeve.xau_dsp_shakeout_a_plus_ready"
READY_ANSWERS = frozenset({"a_plus", "almost", "blocked", "null_state"})
NEVER_WRITE_QUESTIONS = frozenset({"admit"})
NEVER_WRITE_GATE_IDS = frozenset({"FLUID-ADM-007", "UB-AUTH-010"})

READY_CHOICES: tuple[dict[str, Any], ...] = (
    {
        "choice": GBPJPY_READY,
        "edge": "PACK 5",
        "freeze": GBPJPY_FREEZE,
        "answers": READY_ANSWERS,
        "never_admit": True,
        "never_refuse": True,
        "shadow_only": True,
        "doc_section": "§11",
    },
    {
        "choice": XAU_READY,
        "edge": "PACK 6",
        "freeze": XAU_FREEZE,
        "answers": READY_ANSWERS,
        "never_admit": True,
        "never_refuse": True,
        "shadow_only": True,
        "n_in": 3,
        "doc_section": "§12",
    },
)


def assert_edge_freeze() -> dict[str, Any]:
    """Pin both frozen Choices to modules + freeze docs + APLUS. No admit."""
    from .pack5_fields import (
        CHOICE_ANSWERS as PACK5_ANSWERS,
        CHOICE_ID as PACK5_CHOICE,
        NEVER_WRITE_GATE_IDS as PACK5_GATES,
        NEVER_WRITE_QUESTIONS as PACK5_QS,
        pack5_gate_map,
    )
    from .pack6_fields import (
        CHOICE_ANSWERS as PACK6_ANSWERS,
        CHOICE_ID as PACK6_CHOICE,
        N_IN,
        NEVER_WRITE_GATE_IDS as PACK6_GATES,
        NEVER_WRITE_QUESTIONS as PACK6_QS,
        pack6_gate_map,
    )

    bad: list[str] = []
    if PACK5_CHOICE != GBPJPY_READY:
        bad.append(f"pack5_choice:{PACK5_CHOICE}")
    if PACK6_CHOICE != XAU_READY:
        bad.append(f"pack6_choice:{PACK6_CHOICE}")
    if PACK5_ANSWERS != READY_ANSWERS:
        bad.append("pack5_answers")
    if PACK6_ANSWERS != READY_ANSWERS:
        bad.append("pack6_answers")
    if PACK5_QS != NEVER_WRITE_QUESTIONS or PACK6_QS != NEVER_WRITE_QUESTIONS:
        bad.append("wrote_question")
    if PACK5_GATES != NEVER_WRITE_GATE_IDS or PACK6_GATES != NEVER_WRITE_GATE_IDS:
        bad.append("wrote_gate")
    if N_IN != 3:
        bad.append(f"n_in:{N_IN}")
    for row in (*pack5_gate_map(), *pack6_gate_map()):
        if "admit" in row.get("gate_questions", []):
            bad.append(f"gate_question_admit:{row.get('field')}")
        for gid in row.get("gate_ids", []):
            if gid in NEVER_WRITE_GATE_IDS:
                bad.append(f"gate_id:{gid}")
        if not row.get("never_admit"):
            bad.append(f"admit_open:{row.get('field')}")
        if set(row.get("criteria") or {}) & {"admit", "abstain", "hard_refuse"}:
            bad.append(f"admit_answer:{row.get('field')}")
    for path in (GBPJPY_FREEZE, XAU_FREEZE, APLUS_DOC):
        if not path.is_file():
            bad.append(f"missing:{path}")
    if GBPJPY_FREEZE.is_file() and GBPJPY_READY not in GBPJPY_FREEZE.read_text(encoding="utf-8"):
        bad.append("gbpjpy_freeze_choice")
    if XAU_FREEZE.is_file() and XAU_READY not in XAU_FREEZE.read_text(encoding="utf-8"):
        bad.append("xau_freeze_choice")
    if APLUS_DOC.is_file():
        aplus = APLUS_DOC.read_text(encoding="utf-8")
        for cid in (GBPJPY_READY, XAU_READY):
            if cid not in aplus:
                bad.append(f"aplus_missing:{cid}")
        if "Not an admit Choice" not in aplus:
            bad.append("aplus_missing_no_admit")
    return {
        "ok": not bad,
        "bad": bad,
        "choices": (GBPJPY_READY, XAU_READY),
        "answers": sorted(READY_ANSWERS),
        "never_admit": True,
        "never_refuse": True,
        "shadow_only": True,
        "n_in": 3,
        "edge": "FREEZE",
    }
