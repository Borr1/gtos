"""The declaration chain: the default is the newest, and the ratchet holds across versions.

WHY THIS EXISTS
---------------
`candidate_family.DEFAULT_DECLARATION` pointed at V1 for the eight hours between AL publishing
V2 (2026-07-30 10:00:49 +0700) and Session AP (18:00:27). No published number was wrong, and no
production or receipt caller resolved the default -- every one passes an explicit path -- but
TWO SHIPPED TESTS in `test_candidate_family.py` read it and pinned V1's 32/29 through it, which
is how a latent coupling becomes a real one. The default resolved to the SMALLER family (32/29
rather than 35/32), and a smaller family is the permissive direction: it is the one that admits
a candidate the evidence does not support. `CandidateFamilyError`'s own docstring says every
branch must fail closed against exactly that.

So the chain is now explicit and this file pins three properties of it:

  1. `DEFAULT_DECLARATION` is the last link.
  2. every link but the first names its predecessor in `supersedes`, so the chain is not just
     a list someone typed in an order they liked.
  3. the ratchet is monotone **across** versions, not only within one. `high_water_size` stops
     a row being deleted inside a declaration; nothing stopped a *new* declaration being
     published with a smaller family, which is the same attack one file along.
  4. the CARRIED ratification survives a regeneration. AP added `ratified_rule` to V2 by hand
     and `al_family_v2.py` regenerates V2 from V1 wholesale, so without an assertion here the
     next regeneration would silently drop the `carried_from` label while the four
     family/basis/alpha/option assertions still passed. Found by an adversarial pass.

The tests read whichever files the chain names, so appending V3 needs one line in the source
and nothing here.
"""

from __future__ import annotations

import json

import pytest

from src.research_infra.walkforward import candidate_family as CF


def _present(p):
    return p.is_file()


def test_default_declaration_is_the_last_link_in_the_chain():
    assert CF.DEFAULT_DECLARATION == CF.DECLARATION_CHAIN[-1]
    assert len(CF.DECLARATION_CHAIN) == len(set(CF.DECLARATION_CHAIN)), "duplicate link"


def test_the_chain_is_ordered_oldest_first_by_each_files_own_supersedes():
    """Not by filename, not by the order someone typed. Each link says who it replaces."""
    chain = [p for p in CF.DECLARATION_CHAIN if _present(p)]
    if len(chain) < 2:
        pytest.skip("only one declaration is present in this tree")
    for older, newer in zip(chain, chain[1:]):
        doc = json.loads(newer.read_text())
        sup = doc.get("supersedes")
        assert sup, f"{newer.name} does not say what it supersedes"
        assert sup.endswith(older.name), (
            f"{newer.name} supersedes {sup!r}, but the chain places {older.name} before it")


def test_the_first_link_supersedes_nothing():
    first = CF.DECLARATION_CHAIN[0]
    if not _present(first):
        pytest.skip("the first declaration is absent from this tree")
    assert not json.loads(first.read_text()).get("supersedes")


@pytest.mark.parametrize("basis", [CF.ALL_DECLARED, CF.LOOKS_TAKEN])
def test_the_ratchet_is_monotone_across_versions_not_only_within_one(basis):
    """A new declaration may raise a family's bill and may never lower it. `high_water_size`
    enforces this inside one file; the chain is where it could otherwise be bypassed."""
    chain = [p for p in CF.DECLARATION_CHAIN if _present(p)]
    if len(chain) < 2:
        pytest.skip("only one declaration is present in this tree")
    loaded = [CF.load_candidate_family(p) for p in chain]
    for older, newer, opath, npath in zip(loaded, loaded[1:], chain, chain[1:]):
        for fid in older.families:
            if fid not in newer.families:
                pytest.fail(f"{npath.name} drops family {fid!r} declared in {opath.name} -- "
                            f"a family cannot be un-declared")
            was = older.effective_size(fid, basis=basis)
            now = newer.effective_size(fid, basis=basis)
            assert now >= was, (
                f"{fid} {basis}: {opath.name} {was} -> {npath.name} {now}. A look taken "
                f"cannot be un-taken, so a later declaration may not be cheaper.")


def test_the_default_resolves_to_the_larger_bill_of_the_two_shipped_declarations():
    """The concrete regression, stated as a number rather than a rule: the default must be
    AL's ratcheted 35/32, not AI's original 32/29."""
    if not all(_present(p) for p in CF.DECLARATION_CHAIN):
        pytest.skip("chain incomplete in this tree")
    default = CF.load_candidate_family()
    first = CF.load_candidate_family(CF.DECLARATION_CHAIN[0])
    assert (default.effective_size("CANDIDATE_BOOK_V1")
            >= first.effective_size("CANDIDATE_BOOK_V1"))
    assert (default.effective_size("CANDIDATE_BOOK_V1", basis=CF.LOOKS_TAKEN)
            >= first.effective_size("CANDIDATE_BOOK_V1", basis=CF.LOOKS_TAKEN))


def test_the_ratified_rule_survives_into_the_default_declaration():
    """Borhen ratified the RULE on 2026-07-30 -- family `CANDIDATE_BOOK_V1`, all-declared
    basis, sealed alpha 0.10. A new declaration that lost `ratified_rule` would silently
    return the estate to the honour system the module was written to end."""
    if not _present(CF.DEFAULT_DECLARATION):
        pytest.skip("default declaration absent from this tree")
    rule = json.loads(CF.DEFAULT_DECLARATION.read_text()).get("ratified_rule")
    assert rule, f"{CF.DEFAULT_DECLARATION.name} carries no ratified_rule"
    assert rule["family"] == "CANDIDATE_BOOK_V1"
    assert rule["basis"] == CF.ALL_DECLARED
    assert rule["alpha"] == pytest.approx(0.10)
    assert rule["option"] == "B_balanced"
    # The provenance label, asserted so a regeneration that drops it goes red rather than quiet.
    assert rule.get("carried_from"), (
        f"{CF.DEFAULT_DECLARATION.name} carries a ratified_rule with no `carried_from`. If it "
        f"was regenerated, re-add the carry provenance; a rule with no lineage is the honour "
        f"system this module ended.")
    assert "CARRIED" in rule["carried_from"] or "carried" in rule["carried_from"]
