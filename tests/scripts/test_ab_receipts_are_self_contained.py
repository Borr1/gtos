"""An A/B that is not committed did not happen — and a receipt that cannot be checked is not a receipt.

`receipts/WAVE2_INTEGRATION_AB.md` established the first half as a standing rule: the wave-2 A/B was
genuinely run, lived in a scratchpad, and to the next reader therefore did not exist. The third review's
adversarial pass recorded that as a missing receipt, correctly.

This file is the second half, which the rule as written did not cover. A receipt that *references*
`/tmp/before.json` is exactly as unverifiable as no receipt at all, because that file is gone by the time
anyone reads it. So the enforceable form of the rule is: **a committed A/B receipt must embed the
captures it was derived from**, and `scripts/pytest_failset.py receipt` emits exactly that.

Scoped deliberately to receipts produced by the tool. Older hand-written receipts predate it and are
grandfathered by name below, so the exemption list is visible and shrinking rather than implicit.
"""
from __future__ import annotations

import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
RECEIPT_FENCE = "gtos-ab-receipt-v1"

#: A/B receipts that `pytest_failset.py receipt` did not produce, each listed by name with the reason,
#: so the exemption is visible rather than implicit. Regenerating one through the tool removes it.
#:
#: Two kinds now. The first predates the tool. The second is a receipt the tool COULD NOT have
#: produced, and saying so in the receipt is the whole of the exemption: `R1_AB.md` records that the
#: full-suite capture at `8dd9b07c0` came back `parse_complete: false` / `usable_as_baseline: false`
#: ("recovered 0 ids but pytest reported 94"), so a diff on it would have been a diff on nothing, and
#: that the branch had concurrent writers mid-session. It states its scope, its method (BEFORE produced
#: by physically reverting the change, restore verified byte-identical) and its command. That is a
#: stronger artifact than a machine block over an unusable capture, and refusing it would have taught
#: the next reader to fabricate one.
#:
#: Standing note, 2026-08-12: the owner retired the per-change A/B ritual ("dont do ab testing anymore
#: ... we can just run the tests once in the end when merging everything"). This test is kept because
#: it protects the receipts that already exist; it is not a reason to produce new ones.
_GRANDFATHERED = {
    "docs/audits/fable5-vision-audit-20260725/receipts/WAVE2_INTEGRATION_AB.md",
    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/r1/R1_AB.md",
}

#: A receipt exempted for un-parseable captures must SAY so. Prose that just asserts cleanliness is
#: what this file exists to refuse, and the exemption must not become a way back in.
_MUST_STATE_WHY = {
    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/r1/R1_AB.md": (
        "usable_as_baseline", "parse_complete",
    ),
}

_AB_RECEIPT_NAME = re.compile(r"(_AB|_ab)\.md$")


def _candidate_receipts() -> list[pathlib.Path]:
    """Markdown under a receipts/ directory whose name marks it as an A/B receipt."""
    return sorted(
        p for p in REPO.rglob("*.md")
        if "receipts" in p.parts
        and ".git" not in p.parts
        and _AB_RECEIPT_NAME.search(p.name)
    )


def test_the_receipt_scanner_finds_receipts_at_all():
    """Positive control. Every assertion below is vacuous if this list is empty."""
    found = _candidate_receipts()
    assert found, "no A/B receipts found; the scanner cannot see what it searches for"


def test_every_ab_receipt_embeds_its_captures():
    """The rule. Prose saying "we ran it and it was clean" must not pass as evidence."""
    offenders = []
    for p in _candidate_receipts():
        rel = p.relative_to(REPO).as_posix()
        if rel in _GRANDFATHERED:
            continue
        if RECEIPT_FENCE not in p.read_text(encoding="utf-8"):
            offenders.append(rel)
    assert not offenders, (
        "A/B receipt(s) with no embedded capture block — unverifiable once the scratchpad is gone:\n"
        + "\n".join(f"  {o}" for o in offenders)
        + "\n\nRegenerate with: python3 scripts/pytest_failset.py receipt <before.json> <after.json> "
          "-o <receipt.md>"
    )


def test_embedded_blocks_parse_and_are_internally_consistent():
    """An embedded block that does not match its own prose is a new place to hide a wrong number."""
    checked = 0
    for p in _candidate_receipts():
        text = p.read_text(encoding="utf-8")
        if RECEIPT_FENCE not in text:
            continue
        blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.S)
        payloads = [json.loads(b) for b in blocks if RECEIPT_FENCE in b]
        assert payloads, f"{p.name}: fence present but no parseable JSON block"
        for d in payloads:
            assert d["bad_before"] == len(d["bad_before_nodeids"]), f"{p.name}: before count mismatch"
            assert d["bad_after"] == len(d["bad_after_nodeids"]), f"{p.name}: after count mismatch"
            # Regressed and fixed must be derivable from the two node-id sets, not asserted separately.
            b, a = set(d["bad_before_nodeids"]), set(d["bad_after_nodeids"])
            assert sorted(a - b) == d["regressed"], f"{p.name}: regressed set is not derivable"
            assert sorted(b - a) == d["fixed"], f"{p.name}: fixed set is not derivable"
            assert d["before"]["commit"] and d["after"]["commit"], f"{p.name}: missing commit"
            checked += 1
    assert checked, "no embedded block was checked; this test proved nothing"


def test_an_exempted_receipt_states_why_the_tool_could_not_produce_it():
    """The exemption is not a hole: a receipt that claims it could not be machine-generated
    has to name the evidence for that claim inside itself."""
    for rel, required in _MUST_STATE_WHY.items():
        path = REPO / rel
        assert path.is_file(), f"{rel} is exempted but does not exist"
        text = path.read_text(encoding="utf-8")
        missing = [token for token in required if token not in text]
        assert not missing, (
            f"{rel} is exempted from embedding its captures but does not say why; "
            f"missing: {missing}"
        )


def test_the_grandfather_list_shrinks_and_never_grows():
    """A stale exemption is itself a false-green: it reports a known gap that is already closed."""
    stale = []
    for rel in sorted(_GRANDFATHERED):
        p = REPO / rel
        if not p.exists():
            stale.append(f"{rel} (no longer exists)")
        elif RECEIPT_FENCE in p.read_text(encoding="utf-8"):
            stale.append(f"{rel} (now embeds its captures)")
    assert not stale, "grandfather list is stale; remove: " + ", ".join(stale)
