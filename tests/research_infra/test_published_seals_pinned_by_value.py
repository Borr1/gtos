"""The 18 restored published `spec_sha256` values, pinned BY VALUE. [Session AN, B1253]

THE HOLE THIS CLOSES, MEASURED
------------------------------
`test_candidate_family.py::test_the_seal_migration_is_documented_in_both_directions` names two
cohorts: 18 published seals RESTORED by the `_ABSENT_MEANS_UNCHANGED` repair and 10 (11 by
prefix count) BROKEN by it. The two halves are pinned **asymmetrically**, and only one of them
is safe:

* the BROKEN cohort is pinned by exact prefix (`assert any(s.startswith(pre) ...)`);
* the RESTORED cohort is pinned by **count only** — `assert len(seals) >= n`.

An adversarial pass over Session AN's own seal-honesty claim demonstrated the consequence rather
than arguing it: replacing all 18 restored seals with fabricated hashes ("garbage1".."garbage18")
in a temp copy of the five artifacts leaves that test **PASSING**. So a future session could
silently rewrite 18 published seals — the exact failure mode `_ABSENT_MEANS_UNCHANGED`'s own
docstring exists to make impossible — and the suite would stay green.

WHAT THIS TEST DOES AND DOES NOT CLAIM
--------------------------------------
It does **not** re-derive the seals. Three of the 18 already are re-derived, from live `GateSpec`
objects, by `test_candidate_family.py::test_AA_published_spec_seals_reproduce_again`; the drivers
for X, W and AG are not all importable and re-running the estate is not a unit test's job — the
same reason the count-only test gives.

What it claims is narrower and is the part that was missing: **these exact 64-hex strings are
still the ones those artifacts publish.** A regeneration that legitimately changes them has to
come here and say so, which is all the original repair ever asked for.

Snapshotted 2026-07-30 at commit `d140c00b2`, after the `spread_require_decidable` field landed —
so this file also records that adding that field moved none of them.
"""

from __future__ import annotations

import json
import pathlib

import pytest

AUD = pathlib.Path(__file__).resolve().parents[2] / "docs/audits/fable5-vision-audit-20260725"

#: Every published seal in the cohort `_RESTORED_BY_THE_REPAIR` names, by value.
#: The counts match that dict exactly: 7 + 3 + 3 + 3 + 2 = 18.
PUBLISHED = {
    "AA_ESTATE_WALK.json": (
        "1d80839bad1d5388b0220b670cb2145ca6ecd2ea1ed5a03e9f9400586db1866e",
        "67eca1b45432ac47e2dfab702a143cc8c0f0cfa43499ada8edbcce0629bb287e",
        "76342a060f9a267292cd3eb563c199faf3c0c21ba2b74c41d0fd3e6a1e7c5915",
        "959d45adbf052ce9e466d2133bd8e6a25fd6643acad604d671bc1f55226937ec",
        "a8c328985b70a353bc234072f2db012cde230e6de17114873a809640aedbfd82",
        "ab48be5403432bce5ca754aa000290680879a4387141077fc0111d9cce251f51",
        "d3df4c4386160d3a2bb6c9468886f1615cf6242fe73ac57a48a16ba034cd9652",
    ),
    "X_ESTATE_WALK.json": (
        "1fb29999438b69edcfa0cedf7ffda1a325845805943ceea28b699fca4ca12d8c",
        "613ad9157686d0b7f5c36c1d59e937ada4622720aaa48c3956161471682c7cee",
        "62aec9b4c0b9e63cfe6f19a9415ef017506a59bf6ccf93c5dbc46c72d7b67bc3",
    ),
    "X_STATE_D_SENSITIVITY.json": (
        "0f9e767c84fde0c3ffd07d58521a4e65dc6a509ac48a16e2ea801beb647cf7d8",
        "146f9361d797124c7ef77ff2e86f65b23336619bcb1aac0fc4be1727864e050d",
        "9f6322afb131eaae19bcf5b1c706ae7bbbfefd3775e153a244a597437c2e166e",
    ),
    "W_MX_PILOT.json": (
        "3ed0afa4589471fa66634aa334327f1f4b6d53aeca709f9af79fda0d80749eb2",
        "48cdb2edc4dfe999b8a7efb4f72b3f4b1f598da4aaf9a28ac25350edce5382ba",
        "d747ff1532f1487cb15abd323fc41246fd2309814b815d99948cf40fdf42b741",
    ),
    "W_NEGATIVE_CONTROLS.json": (
        "8edb7b674dc7a6116d938ca48839ff1bc8a6df72f08110061b3265d3e1987814",
        "c00835265cbf940146f6255beb0561b39eb5f7200a8c5f85210108c1e17d9193",
    ),
}


def _seals_in(path: pathlib.Path) -> set[str]:
    """Every 64-hex `spec_sha256` anywhere in the document.

    Deliberately the same traversal as `test_candidate_family._seals_in`, including its
    400-element list cap, so the two tests cannot disagree about what "published" means.
    """
    out: set[str] = set()

    def walk(o):
        if isinstance(o, dict):
            v = o.get("spec_sha256")
            if isinstance(v, str) and len(v) == 64:
                out.add(v)
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o[:400]:
                walk(x)

    walk(json.loads(path.read_text()))
    return out


@pytest.mark.parametrize("filename", sorted(PUBLISHED))
def test_every_restored_seal_is_still_published_by_value(filename):
    hits = list(AUD.glob(f"phase*/receipts/{filename}"))
    if not hits:
        pytest.skip(f"{filename} is not in this working tree")
    found = _seals_in(hits[0])
    missing = [s for s in PUBLISHED[filename] if s not in found]
    assert not missing, (
        f"{filename}: {len(missing)} of {len(PUBLISHED[filename])} published spec_sha256 "
        f"values are GONE — {[s[:12] + '…' for s in missing]}. Either the artifact was "
        f"regenerated (say so here and re-snapshot) or a change to `_ABSENT_MEANS_UNCHANGED` / "
        f"`GateSpec.canonical()` silently rewrote the estate's published seals, which is the "
        f"defect that field set exists to prevent."
    )


def test_the_cohort_size_matches_the_dict_it_mirrors():
    """18, and the same 18 the count-only test claims. If the two ever disagree, both are wrong."""
    from tests.research_infra.test_candidate_family import _RESTORED_BY_THE_REPAIR

    assert sum(len(v) for v in PUBLISHED.values()) == 18
    assert set(PUBLISHED) == set(_RESTORED_BY_THE_REPAIR)
    for fn, n in _RESTORED_BY_THE_REPAIR.items():
        assert len(PUBLISHED[fn]) == n, (
            f"{fn}: this file pins {len(PUBLISHED[fn])} seals and test_candidate_family "
            f"expects {n}")


def test_a_substituted_seal_would_be_caught():
    """The control that makes this test worth having, run against a fabricated hash.

    The count-only assertion survives substitution — that is the whole finding — so this file's
    assertion has to be shown NOT to. Checked directly on the predicate rather than by rewriting
    an artifact, because a test that mutates the audit tree is a worse idea than a narrow one.
    """
    real = PUBLISHED["AA_ESTATE_WALK.json"]
    fabricated = {("f" * 64)} | set(real[1:])          # one seal replaced
    assert [s for s in real if s not in fabricated] == [real[0]]
    # ...and the count-only form does not notice:
    assert len(fabricated) >= 7
