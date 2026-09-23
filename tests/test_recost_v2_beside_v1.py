"""OD-AI-4 option C: V2 lives beside V1, and no tier or verdict moves between them.

WHY THIS FILE IS THE POINT OF OPTION C
--------------------------------------
`OD-AI-4` priced three options. **A** re-seals and takes ten citing documents stale in one
commit. **B** (what wave 8 did) leaves the artifacts sealed and publishes the drift. **C**
re-seals as a V2 beside V1 — and C is only worth having if it comes with a **claim**: that the
better MEASURED cost coverage changes no tier and no survivor/killed membership. A script that
prints that once is an anecdote; a test is the thing that notices when it stops being true.

So this file asserts, over whatever V1/V2 pair is on disk:

  1. **`book_days` reproduces in every cell.** A cost re-pricing cannot add or remove a day a
     sleeve traded, so this is the load-bearing control — if it ever fails, the trade set moved
     and the whole comparison is void rather than merely different.
  2. **No tier, and no survivor/killed membership, differs.** That is option C's claim.
  3. **V1 is byte-identical to its committed self.** The generators default to writing nowhere
     near the artifact of record and `--write-committed` is the only path to it; this asserts the
     outcome rather than trusting the flag.
  4. **redacted_account is untouched.** `8f6da5150` and `33d854189` extended the cost artifact on FTMO
     only, so redacted_account must reproduce exactly. It is the control that makes the drift a
     diagnosis rather than a guess.
  5. **The values DO move, and the artifact says so.** A reader who takes "no verdict changes" for
     "nothing changed" would quote V1 and V2 in one table. The delta receipt has to keep carrying
     the movement, in both directions.

Every test skips cleanly when the pair is absent, because `research/operations/` is outside the
sparse-checkout cone and a fresh worktree can legitimately lack it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
V1_DIR = REPO / "research/operations/w7_recost_2026_07_27"
V2_DIR = REPO / "research/operations/w7_recost_2026_07_30"
SB_V1, SB_V2 = V1_DIR / "SURVIVOR_BOOK_V1.json", V2_DIR / "SURVIVOR_BOOK_V2.json"
MC_V1, MC_V2 = V1_DIR / "MC_FIRM_TRUE_V1.json", V2_DIR / "MC_FIRM_TRUE_V2.json"
DELTA = (REPO / "docs/audits/fable5-vision-audit-20260725/phase10/receipts"
         / "AP_RECOST_V2_DELTA.json")

_PAIR = [SB_V1, SB_V2, MC_V1, MC_V2]
pytestmark = pytest.mark.skipif(
    not all(p.is_file() for p in _PAIR),
    reason="the V1/V2 recost pair is not in this working tree (research/operations/ is outside "
           "the sparse-checkout cone)")


def _load(p: Path) -> dict:
    return json.loads(p.read_text())


def _book_days(doc: dict) -> dict:
    """(account, variant, key) -> book_days, wherever the artifact records one."""
    out = {}
    for acct, ab in (doc.get("accounts") or {}).items():
        for var, vb in (ab.get("variants") or {}).items():
            if not isinstance(vb, dict):
                continue
            for k, v in vb.items():
                if isinstance(v, dict) and "book_days" in v:
                    out[(acct, var, k)] = v["book_days"]
            if "book_days" in vb:
                out[(acct, var, "__variant__")] = vb["book_days"]
        for sl, sb in (ab.get("sleeves") or {}).items():
            if isinstance(sb, dict) and "book_days" in sb:
                out[(acct, "sleeves", sl)] = sb["book_days"]
    return out


def _tiers(doc: dict) -> dict:
    out = {}
    for acct, ab in (doc.get("accounts") or {}).items():
        for sl, sb in (ab.get("sleeves") or {}).items():
            if isinstance(sb, dict) and "survivor_tier" in sb:
                out[f"{acct}/{sl}"] = sb["survivor_tier"]
        if "survivors" in ab:
            out[f"{acct}/__survivors__"] = sorted(ab["survivors"] or [])
        if "killed" in ab:
            out[f"{acct}/__killed__"] = sorted(ab["killed"] or [])
    return out


def _account_slice(doc: dict, acct: str) -> dict:
    return (doc.get("accounts") or {}).get(acct) or {}


# --------------------------------------------------------------- the two controls


def test_book_days_reproduces_in_every_cell():
    """The load-bearing control: a cost re-pricing cannot move the trade set."""
    b1, b2 = _book_days(_load(MC_V1)), _book_days(_load(MC_V2))
    assert b1, "no book_days found in MC_FIRM_TRUE_V1 — the extractor has drifted from the schema"
    keys = sorted(set(b1) | set(b2), key=str)
    bad = [(k, b1.get(k), b2.get(k)) for k in keys if b1.get(k) != b2.get(k)]
    assert not bad, (
        f"{len(bad)} of {len(keys)} book_days cells moved between V1 and V2. A cost re-pricing "
        f"cannot add or remove a day a sleeve traded, so this is not a 'different number' — the "
        f"comparison is VOID. First few: {bad[:5]}")


def test_no_tier_and_no_membership_changes_between_v1_and_v2():
    """This assertion IS option C. If it fails, C was the wrong option."""
    t1, t2 = _tiers(_load(SB_V1)), _tiers(_load(SB_V2))
    assert t1, "no survivor_tier / survivors / killed found in SURVIVOR_BOOK_V1"
    keys = sorted(set(t1) | set(t2))
    bad = [(k, t1.get(k), t2.get(k)) for k in keys if t1.get(k) != t2.get(k)]
    assert not bad, (
        f"OPTION C'S CLAIM HAS FAILED: {len(bad)} tier/membership keys differ between V1 and V2, "
        f"so the better cost coverage DOES move a verdict and the estate needs to know which. "
        f"Do not silence this test — publish the move. {bad}")


# --------------------------------------------------------------- V1 is the record


def test_v1_is_byte_identical_to_its_committed_self():
    """`build_survivor_book.py` once overwrote the artifact of record unconditionally, so running
    it to CHECK reproduction destroyed the thing being checked. Assert the outcome."""
    for p in (SB_V1, MC_V1):
        r = subprocess.run(["git", "show", f"HEAD:{p.relative_to(REPO)}"],
                           cwd=REPO, capture_output=True)
        if r.returncode != 0:
            pytest.skip(f"{p.name} is not tracked at HEAD in this tree")
        want = hashlib.sha256(r.stdout).hexdigest()
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        assert got == want, (
            f"{p.name} differs from its committed bytes. V1 is the artifact of record that ten "
            f"documents cite; restore it from git before doing anything else.")


def test_v2_declares_what_it_was_derived_from():
    v2 = _load(SB_V2)
    assert v2.get("generated_by"), "V2 must say what generated it"
    mc2 = _load(MC_V2)
    assert mc2.get("generated_by"), "V2 MC must say what generated it"
    assert _load(MC_V1).get("n_paths") == mc2.get("n_paths"), (
        "V1 and V2 must be compared at the SAME Monte Carlo resolution, or a sampling difference "
        "is indistinguishable from a pricing difference.")


# --------------------------------------------------------------- the redacted_account control


@pytest.mark.parametrize("v1,v2", [(SB_V1, SB_V2), (MC_V1, MC_V2)])
def test_redacted_account_reproduces_exactly(v1, v2):
    """FTMO-only cost extension -> redacted_account must be untouched. This is what makes the drift a
    diagnosis rather than a guess, and it is asserted per artifact."""
    a, b = _account_slice(_load(v1), "redacted_account"), _account_slice(_load(v2), "redacted_account")
    if not a:
        pytest.skip(f"{v1.name} carries no redacted_account account block")
    assert a == b, (
        f"{v2.name}'s redacted_account half differs from V1's. The cost extension (8f6da5150, "
        f"33d854189) touched FTMO only, so a redacted_account difference means something else moved "
        f"and the FTMO delta can no longer be attributed to the recost.")


# ------------------------------------------------- and the values DO move


@pytest.mark.skipif(not DELTA.is_file(), reason="delta receipt absent")
def test_the_delta_receipt_still_records_that_values_move():
    """A reader who takes "no verdict changes" for "nothing changed" quotes V1 and V2 in one
    table. The receipt has to keep saying that the numbers move, in both directions."""
    d = _load(DELTA)
    assert d["THE_CONTROL"]["holds"] is True
    assert d["THE_POINT_OF_OPTION_C"]["holds"] is True
    moved = d["WHAT_ACTUALLY_MOVED"]
    for half in ("survivor_book", "mc"):
        assert moved[half]["n_p_pass_leaves_in_the_published_sample"] > 0, (
            f"{half}: the receipt records no p_pass movement at all. Either the recost became a "
            f"no-op — in which case option C is pointless and B was right — or the diff walker "
            f"has stopped seeing the artifact.")
        assert moved[half]["max_abs_delta"] > 0
    assert moved["survivor_book"]["moves_in_both_directions"] is True, (
        "the recost is expected to reprice in BOTH directions; a one-directional delta suggests a "
        "systematic error rather than better coverage")
