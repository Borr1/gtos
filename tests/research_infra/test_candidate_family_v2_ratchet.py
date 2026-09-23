"""The ratchet across a FILE SUCCESSION, which the loader cannot see. Session AL (B1153).

`candidate_family.py` enforces a ratchet WITHIN one declaration: `high_water_size` turns a deleted
member row into a load-time refusal, and `high_water_looks` does the same for a retracted look. It
has never guarded the other route to a smaller bill, and that route is the easy one: publish a NEW
declaration file with fewer members and point the driver at it. The loader reads one file and has
no predecessor to compare against, so there is nothing there to refuse.

Session AL had to supersede V1 (its four size assertions in `test_candidate_family.py` mean an
in-place edit reads as four defects rather than as an intended raise), which is exactly the
operation that opens the hole. So the guard lands with the first succession that needs it, and it
is generic: every `CANDIDATE_FAMILY_V*.json` in the audit tree must be a superset of every
declaration it says it `supersedes`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra.walkforward import candidate_family as CF

REPO = Path(__file__).resolve().parents[2]
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
V1 = AUD / "phase8/receipts/CANDIDATE_FAMILY_V1.json"
V2 = AUD / "phase9/receipts/CANDIDATE_FAMILY_V2.json"


def _declarations() -> list[Path]:
    return sorted(p for p in AUD.glob("phase*/receipts/CANDIDATE_FAMILY_V*.json"))


def test_every_declaration_in_the_tree_loads():
    found = _declarations()
    assert found, "no CANDIDATE_FAMILY_V*.json found in the audit tree"
    for p in found:
        CF.load_candidate_family(p)          # raises CandidateFamilyError on any defect


@pytest.mark.parametrize("path", _declarations(), ids=lambda p: p.name)
def test_a_successor_is_a_superset_of_what_it_supersedes(path: Path):
    """`supersedes` is a claim about lineage, and lineage in a ratchet means superset."""
    doc = json.loads(path.read_text())
    rel = doc.get("supersedes")
    if not rel:
        pytest.skip(f"{path.name} supersedes nothing")
    prev_path = REPO / rel
    assert prev_path.is_file(), f"{path.name} supersedes {rel}, which is not on disk"
    prev = CF.load_candidate_family(prev_path)
    cur = CF.load_candidate_family(path)

    for fid in prev.families:
        assert fid in cur.families, (
            f"{path.name} dropped family {fid!r} that {prev_path.name} declared. Dropping a "
            f"family is the file-level form of deleting a member row.")
        a, b = prev.family(fid), cur.family(fid)
        gone = sorted({m.name for m in a.members} - {m.name for m in b.members})
        assert not gone, (
            f"{path.name} family {fid!r} dropped member(s) {gone}. A withdrawal is expressed by "
            f"status='withdrawn', which keeps the row and keeps the bill.")
        assert b.effective_size() >= a.effective_size(), (
            f"{path.name} family {fid!r} declares {b.effective_size()} against "
            f"{prev_path.name}'s {a.effective_size()}. A successor may only RAISE the bill.")
        assert b.looks_taken_size() >= a.looks_taken_size(), (
            f"{path.name} family {fid!r} counts {b.looks_taken_size()} looks against "
            f"{prev_path.name}'s {a.looks_taken_size()}")
        assert b.high_water_size >= a.high_water_size, (
            f"{path.name} family {fid!r} lowered high_water_size, which would re-open row "
            f"deletion for the successor")


def test_v2_adds_exactly_the_three_al_threshold_variants():
    """The measured content of AL's amendment, so a silent fourth addition is a red line."""
    prev = CF.load_candidate_family(V1)
    cur = CF.load_candidate_family(V2)
    new = sorted({m.name for m in cur.family("CANDIDATE_BOOK_V1").members}
                 - {m.name for m in prev.family("CANDIDATE_BOOK_V1").members})
    assert new == [
        "thr_sub_xvol_pullback_vr14_s100_ac010",
        "thr_sub_xvol_pullback_vr14_s125_ac015",
        "thr_sub_xvol_pullback_vr14_s150_ac015",
    ]
    assert cur.effective_size("CANDIDATE_BOOK_V1") == 35
    assert cur.effective_size("CANDIDATE_BOOK_V1", CF.LOOKS_TAKEN) == 32
    # The other two families must be untouched -- an amendment to one family must not move
    # another's identity, which is why `with_declared_family` hashes membership per family.
    for fid in ("MECHANISM_CROSS_V1", "ESTATE_UNION_V1"):
        assert cur.membership_of(fid) == prev.membership_of(fid)
    assert cur.membership_of("CANDIDATE_BOOK_V1") != prev.membership_of("CANDIDATE_BOOK_V1")


def test_every_late_addition_is_logged_in_history():
    """The loader only checks `declared_at > declaration_date`. AL's members carry the SAME date
    as the amended declaration, so the loader's check does not fire -- and the amendment must
    still be logged, or the ratchet's audit trail is decorative."""
    cur = CF.load_candidate_family(V2)
    fam = cur.family("CANDIDATE_BOOK_V1")
    logged = {n for h in fam.history for n in (h.get("members_added") or ())}
    prev = {m.name for m in CF.load_candidate_family(V1).family("CANDIDATE_BOOK_V1").members}
    added = {m.name for m in fam.members} - prev
    assert added and added <= logged, f"unlogged addition(s): {sorted(added - logged)}"


def test_the_price_of_the_amendment_is_stated_and_arithmetically_right():
    """A `history` entry that raises a bill must say what the raise costs, and the number in it
    must be the number the gate will use."""
    cur = CF.load_candidate_family(V2)
    fam = cur.family("CANDIDATE_BOOK_V1")
    entry = next(h for h in fam.history if h.get("members_added"))
    price = entry.get("price_stated_up_front") or ""
    m = fam.effective_size()
    assert f"{0.10 / m:.6f}" in price, (
        f"the stated rank-1 threshold does not match alpha/m at m={m}")
    assert f"{0.20 / m:.6f}" in price
