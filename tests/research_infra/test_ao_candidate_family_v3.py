"""Session AO (B1303): what CANDIDATE_FAMILY_V3 adds, and that the raise did not kill the
estate's one admission.

The generic ratchet guard (`test_candidate_family_v2_ratchet.py`) is parametrized over every
declaration in the tree, so V3 already inherits superset / monotone / logged-addition checks.
What it cannot check is the CONTENT of this particular amendment, and content is what a silent
fifth addition would change. Same shape as
`test_v2_adds_exactly_the_three_al_threshold_variants`.

The last assertion is the one worth having: a session that raises a multiplicity bill can kill
somebody else's admission, and AO's raise is 4 slots out of the 55 AL §8.7 measured as
`mx_btcusd`'s BH headroom. If a later amendment takes it past 90 the estate loses its only
admitted candidate, so the arithmetic is pinned rather than trusted.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra.walkforward import candidate_family as CF

REPO = Path(__file__).resolve().parents[2]
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
V2 = AUD / "phase9/receipts/CANDIDATE_FAMILY_V2.json"
V3 = AUD / "phase10/receipts/CANDIDATE_FAMILY_V3.json"

#: `mx_btcusd @ target_5R` on RECORDED@mid. AL's headline, reproduced independently by AO's
#: power-pool solo control (`BTC_POWER_POOL_V1.json` -> controls.solo_reproduces_AL).
BTC_P_RAW = 0.0010998900109989002
ALPHA = 0.10


def test_v3_adds_exactly_ao_s_three_conditioning_cells_and_one_pool():
    prev = CF.load_candidate_family(V2)
    cur = CF.load_candidate_family(V3)
    new = sorted({m.name for m in cur.family("CANDIDATE_BOOK_V1").members}
                 - {m.name for m in prev.family("CANDIDATE_BOOK_V1").members})
    assert new == [
        "fam_ao_btc_power_pool_crypto_d1",
        "thr_asia_pdl_fade_persistence_revert",
        "thr_sub_xvol_pullback_comp_coil",
        "thr_sub_xvol_pullback_rngpos_mid",
    ], new
    assert cur.effective_size("CANDIDATE_BOOK_V1") == 39
    assert cur.effective_size("CANDIDATE_BOOK_V1", CF.LOOKS_TAKEN) == 36
    for fid in ("MECHANISM_CROSS_V1", "ESTATE_UNION_V1"):
        assert cur.membership_of(fid) == prev.membership_of(fid), fid
    assert cur.membership_of("CANDIDATE_BOOK_V1") != prev.membership_of("CANDIDATE_BOOK_V1")


def test_v3_declares_supersession_and_the_ratchet_guard_can_see_it():
    doc = json.loads(V3.read_text())
    assert doc["supersedes"] == str(V2.relative_to(REPO))
    assert (REPO / doc["supersedes"]).is_file()
    # the generic guard globs `phase*/receipts/CANDIDATE_FAMILY_V*.json`; V3 must be found by it
    found = sorted(p.name for p in AUD.glob("phase*/receipts/CANDIDATE_FAMILY_V*.json"))
    assert "CANDIDATE_FAMILY_V3.json" in found, found


def test_ao_s_price_is_stated_and_arithmetically_right():
    fam = CF.load_candidate_family(V3).family("CANDIDATE_BOOK_V1")
    entry = next(h for h in fam.history if "fam_ao_btc_power_pool_crypto_d1"
                 in (h.get("members_added") or ()))
    price = entry.get("price_stated_up_front") or ""
    m = fam.effective_size()
    assert f"{ALPHA / m:.6f}" in price, (m, price[:200])
    assert f"{2 * ALPHA / m:.6f}" in price
    # and the looks-taken basis is priced too, because mixing the two bases is the error
    # AL §6.3 had to correct
    ml = fam.looks_taken_size()
    assert f"{ALPHA / ml:.6f}" in price, (ml, price[:200])


def test_every_ao_member_carries_a_basis_that_says_why_not_how_it_did():
    """`Member.basis` is "why it belongs to the family, not how it performed". An AO row citing
    a p-value would mean the declaration was written after the result, which is the whole thing
    the prospective declaration exists to prevent."""
    fam = CF.load_candidate_family(V3).family("CANDIDATE_BOOK_V1")
    ao = [m for m in fam.members if m.name in {
        "fam_ao_btc_power_pool_crypto_d1", "thr_asia_pdl_fade_persistence_revert",
        "thr_sub_xvol_pullback_comp_coil", "thr_sub_xvol_pullback_rngpos_mid"}]
    assert len(ao) == 4
    for m in ao:
        assert "Session AO" in m.basis, m.name
        assert m.look_taken is True and m.no_look_evidence is None, m.name
        assert m.status == CF.DECLARED, m.name
        # no outcome language: a declaration that quotes its own result is retrospective
        low = m.basis.lower()
        for banned in ("p_raw", "p 0.0", "admits", "admitted", "r/day", "q_value"):
            assert banned not in low, (m.name, banned)


@pytest.mark.parametrize("declaration,expected_admits", [(V2, True), (V3, True)])
def test_the_raise_does_not_kill_the_estate_s_one_admission(declaration, expected_admits):
    """`mx_btcusd @ target_5R` must still clear BH rank 1 at the raised bill, and the headroom
    left has to be visible so the next amendment can be priced before it is made."""
    m = CF.load_candidate_family(declaration).effective_size("CANDIDATE_BOOK_V1")
    assert (BTC_P_RAW <= ALPHA / m) is expected_admits, (m, ALPHA / m, BTC_P_RAW)
    if declaration == V3:
        largest = CF.max_size_that_admits(BTC_P_RAW, ALPHA)
        assert largest == 90, largest          # AL §8.7's measured headroom, reproduced
        assert m == 39 and largest - m == 51, (m, largest)
        # the Bonferroni half, which AL measured as the tighter one
        assert CF.max_size_that_admits(BTC_P_RAW, 0.05) == 45
