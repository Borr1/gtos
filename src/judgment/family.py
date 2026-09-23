"""Current book-config family tags. Config, not religion — re-evaluate with complete state.

These labels describe the **2026-09-16 host surface** (OWNER_BRIEF). They are
inputs to gold_state / shadow compose. They do not invent a new choke list and
they do not lift a live cut.
"""

from __future__ import annotations

HARD_OFF_FAMILIES = ("bleed", "orb_crypto", "idxrev", "xa_huge", "xa_second_rth", "kz_london_crypto_low", "mx_us30")
KEEP_FAMILIES = ("spring", "vss")
STUDY_PREFIXES = (
    "dsp_two_bar",
    "dsp_three_bar",
    "dsp_three_fre",
    "dsp_expanding",
    "dsp_wide_down",
    "dsp_walked",
)
STARVE_PREFIXES = ("sub_mid",)
APLUS_PREFIXES = ("aplus_", "a_plus_")
APLUS_ORIGIN = "aplus_research"
A_PLUS_PREFIXES = APLUS_PREFIXES


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def hard_off_family(sleeve: str, symbol: str = "") -> str | None:
    sl = _norm(sleeve)
    if sl.startswith(APLUS_PREFIXES):
        return None
    sy = _norm(symbol).replace(".", "_")
    if sy.startswith("us30") or sl.startswith("mx_us30"):
        return "mx_us30"
    if "bleed" in sl:
        return "bleed"
    if sl.startswith("orb_") or "crypto" in sl or sl.startswith("kz_london"):
        return "orb_crypto"
    if "idxrev" in sl:
        return "idxrev"
    if sl.startswith("xa_huge") or sl.startswith("xa_second_rth"):
        return "xa_huge" if sl.startswith("xa_huge") else "xa_second_rth"
    return None


def keep_family(sleeve: str) -> bool:
    sl = _norm(sleeve)
    return sl.startswith("dsp_spring") or sl.startswith("vss")


def is_aplus_family(sleeve: str, *, origin: str = "") -> bool:
    sl = _norm(sleeve)
    return sl.startswith(APLUS_PREFIXES) or origin == APLUS_ORIGIN


def family_class_for(
    sleeve: str,
    *,
    symbol: str = "",
    origin: str = "f5_challenge",
) -> str:
    sl = _norm(sleeve)
    # A+ setups are first-class study sleeves on the Challenge gate pipe.
    # They must not inherit W7 ``w7_sleeve`` or F5 hard-off substrings.
    if is_aplus_family(sl, origin=origin) or any(sl.startswith(p) for p in A_PLUS_PREFIXES):
        return "a_plus_study"
    # F5 hard-off tags are current Challenge book config, not W7 law.
    # W7 armed ``crypto`` must not inherit orb_crypto from the substring.
    if origin == "w7_ultimate_book":
        return "w7_metals" if sl.startswith("metals_") else "w7_sleeve"
    if sl.startswith("metals_"):
        return "w7_metals"
    if any(sl.startswith(p) for p in A_PLUS_PREFIXES):
        return "a_plus_study"
    if keep_family(sl):
        return "house_keep"
    if hard_off_family(sl, symbol):
        return "house_hard_off"
    if any(sl.startswith(p) for p in STUDY_PREFIXES):
        return "study"
    if any(sl.startswith(p) for p in STARVE_PREFIXES):
        return "starve_watch"
    if sl:
        return "other_tagged"
    return "unknown"
