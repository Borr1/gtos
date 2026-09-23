"""The prospective family declaration — `declared_family_size` read from an artifact.

WHY THIS FILE EXISTS
--------------------
`GateSpec.declared_family_size` (`spec.py:218`) is an `int | None` typed per call, and its
own docstring says so: *"It is on the caller's honour — there is no persistent trial ledger
in this repo — but declaring it makes the omission visible."* The gate then corrects at
`max(n_judged, declared_family_size)` (`gate.py:797`).

That honour system has produced three different bills for the same estate, all defensible
and none reconcilable:

    AA  `declared_family_size=69`   (`AA_ESTATE_WALK.json` -> runs.*.family.multiplicity)
    AD  `declared_family_size=69`   held at AA's value so q-values stay comparable
    AF  `declared_family_size=276`  246 member cells + 30 families in one sweep

and it is the single thing between `mx_btcusd` (raw p 0.0064) and a verdict: at <= 31 looks
it admits under BH alpha=0.20, at <= 8 under Bonferroni alpha=0.05, and at 276 its q is 1.0
(`SESSION_AF_FAMILY_EXPANSION_RESULT.md` section 4 and section 11).

The defect is not that the numbers differ. It is that **each was chosen after the looks were
taken**, so nothing stops the number being the one that produces the wanted answer. The fix
is not a bigger number — a bill nobody can justify is as unaccountable as a small one. The
fix is that the family is **named before the outcomes are read**, and the size is then a
*consequence* of that list rather than an input to the verdict.

THE ONE CLAIM THIS MODULE MAKES
-------------------------------
A multiplicity bill is a bill on **looks taken**, and a look taken cannot be un-taken.
Everything below follows from that sentence:

  * adding a member after the declaration RAISES the bill (a new look was taken);
  * withdrawing a member does NOT lower it (the look still happened);
  * the size is therefore monotone non-decreasing over a family's life -- a ratchet.

That is what removes the incentive to curate. Under a shrinking family, the cheapest way to
admit a candidate is to withdraw its unsuccessful siblings; under a ratchet there is no such
move, so a declaration can be *generous* without being self-defeating, which is what makes
declaring early rational.

WHAT THIS MODULE DOES NOT DO
----------------------------
It does not choose the family. `CANDIDATE_FAMILY_V1.json` is populated by enumeration from
artifacts that already exist -- survivors, banked exit improvements, admissible members --
and the *rule* (which family a candidate-book admission is corrected against) is Borhen's,
exactly as `SESSION_AF_FAMILY_EXPANSION_RESULT.md` section 11 filed it. This module makes
whichever rule he ratifies mechanical instead of typed, and makes the alternatives priceable
side by side (`sensitivity()`).

It also does not enforce. A caller can still pass `declared_family_size=8` by hand and the
gate will use it. What changes is that a verdict produced through `with_declared_family()`
carries the declaration's id and sha256 **in its seal**, so "which family was this corrected
against" stops being a question you have to ask the author.

THE SEAL IS NOT MOVED BY THIS CHANGE, DELIBERATELY
--------------------------------------------------
`GateSpec.canonical()` drops `declared_family_id` / `declared_family_sha256` when both are
None, so every spec authored before this module seals exactly as it did before and every
published `spec_sha256` in the estate still reproduces. The rule is defensible because a
field that is absent cannot have moved a verdict, and there is no value of either field whose
meaning coincides with None -- None is "no declaration was consulted", any string is "this
one was". `test_candidate_family.py` pins `DEFAULT_SPEC.seal()` to the literal sha it had
before this file existed so the migration cannot silently stop being seal-preserving.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

SCHEMA = "gtos.walkforward.candidate_family.v1"

REPO = Path(__file__).resolve().parents[3]
# Under `docs/` for the same reason `live_evidence.CALIBRATION_V2` is: `research/operations/`
# is sparse-checkout-excluded, so an artifact committed there can be absent from a working
# tree with `git status` clean (WAVE_8_WORKING_AGREEMENT section 4, "sparse-checkout lies").
DECLARATION_V1 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts/CANDIDATE_FAMILY_V1.json"
)
#: Session AL's amendment: CANDIDATE_BOOK_V1 32 -> 35 declared, 29 -> 32 looks taken, for the
#: three `sub_xvol_pullback` threshold cells it ran. It carries `supersedes: <V1>`.
DECLARATION_V2 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts/CANDIDATE_FAMILY_V2.json"
)

#: The declaration chain, oldest first. **Append to this when you publish a new declaration**
#: -- `DEFAULT_DECLARATION` is its last entry, and `test_candidate_family_chain.py` asserts
#: that each entry names its predecessor in `supersedes` and that the ratchet holds ACROSS
#: versions as well as within one.
#:
#: Why the chain is written down rather than discovered: for the EIGHT HOURS between AL
#: publishing V2 (f83ea9fc2, 2026-07-30 10:00:49 +0700) and this session (e391e330c, 18:00:27),
#: `DEFAULT_DECLARATION` still pointed at V1. No PRODUCTION or receipt caller noticed, because
#: every one of them passes an explicit path -- but two SHIPPED TESTS in
#: `test_candidate_family.py` read the default and pinned V1's 32/29 through it, so flipping the
#: pointer required re-pointing them at `DECLARATION_V1` by name. (Both sentences here were
#: wrong in the first draft: it said "four days", which is arithmetically impossible since V2's
#: own declaration_date is the same day, and "nothing broke, because every caller passed an
#: explicit path", which two tests refute. An adversarial pass caught both.) The default was
#: the SMALLER family, which is the permissive direction and therefore the exact failure mode
#: `CandidateFamilyError`'s docstring says every branch
#: must fail closed against. Globbing the receipts directories would have fixed it and
#: introduced a worse bug: a sparse-checkout-excluded declaration would silently change which
#: family the default resolves to, and this estate has been bitten by sparse checkout twice
#: (WAVE_6 §5, WAVE_8 §4). An explicit list cannot do that. Found by Session AP (B1350-B1399).
#:
#: **RE-OPENED AND NINE VERSIONS DEEP. Repaired 2026-07-31 by Session CC (B2204-B2206).**
#: The chain above stopped at V2 while ELEVEN declarations existed on disk in an unbroken
#: `supersedes` chain to V11, so `DEFAULT_DECLARATION` resolved `CANDIDATE_BOOK_V1` at
#: **35 declared / 32 looks against a true 53 / 50** — a 51 % under-bill, in the permissive
#: direction this module's every branch is supposed to fail closed against. Latent while every
#: caller passed an explicit path; live the moment `training_lane/graduation.py` had to resolve
#: "which declaration IS the ratchet".
#:
#: The reason it survived AP's fix is the part worth reading: **extending the chain would have
#: gone red.** `test_candidate_family_chain.py` asserts the head carries `ratified_rule`, and
#: V3 through V11 all dropped it — so Borhen's 2026-07-30 ratification of the sealed admission
#: rule lived only in V1/V2, two links behind the head, while the guard written to catch a
#: dropped rule could not fire because the pointer never moved past them. The stale pointer hid
#: the dropped rule; the dropped rule made moving the pointer expensive. Neither end shows the
#: other. The rule carry collided with Session CA's look declaration at the wave-14 train and
#: was renumbered per its own collision note: V12 is CA's (V11 + one look, vp_euidx_pocgrav
#: TAKEN, rule-blind like V3..V11); V13 (`phase14/receipts/cc_family_v13.py`) is V12's
#: membership with V2's rule carried forward — zero new members, zero new looks — and it is
#: what makes this list extendable again.
#:
#: `test_training_lane_protocol.py::test_no_declaration_on_disk_supersedes_the_chain_head`
#: now discovers declaration files and fails when one supersedes the head, so "somebody forgot
#: to append" is a red test rather than a quiet under-bill. Discovery is a TEST, never the
#: resolution: a sparse-checkout-excluded file must not be able to change what the default
#: resolves to (WAVE_6 section 5, WAVE_8 section 4).
DECLARATION_V3 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase10/receipts/CANDIDATE_FAMILY_V3.json"
)
DECLARATION_V4 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/CANDIDATE_FAMILY_V4.json"
)
DECLARATION_V5 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/CANDIDATE_FAMILY_V5.json"
)
DECLARATION_V6 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/CANDIDATE_FAMILY_V6.json"
)
DECLARATION_V7 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/CANDIDATE_FAMILY_V7.json"
)
DECLARATION_V8 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/CANDIDATE_FAMILY_V8.json"
)
DECLARATION_V9 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/CANDIDATE_FAMILY_V9.json"
)
DECLARATION_V10 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts/CANDIDATE_FAMILY_V10.json"
)
DECLARATION_V11 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts/CANDIDATE_FAMILY_V11.json"
)
#: Session CA's: V11's membership plus one declared-then-taken look (vp_euidx_pocgrav).
DECLARATION_V12 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts/CANDIDATE_FAMILY_V12.json"
)
#: V12's membership with V2's `ratified_rule` carried forward. Adds no member and no look.
DECLARATION_V13 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts/CANDIDATE_FAMILY_V13.json"
)
#: Session CH's prospective measurement bill. V14-V17 are CE's four P1-HIST looks;
#: V18-V25 are the committed-hour, ratified-hour, inverse-cheapest and five matched-random
#: entry-hour looks. Each successor was written by training_lane.graduation.graduate(), one
#: look at a time, before either gate opened an outcome.
DECLARATION_V14 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V14.json"
)
DECLARATION_V15 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V15.json"
)
DECLARATION_V16 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V16.json"
)
DECLARATION_V17 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V17.json"
)
DECLARATION_V18 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V18.json"
)
DECLARATION_V19 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V19.json"
)
DECLARATION_V20 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V20.json"
)
DECLARATION_V21 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V21.json"
)
DECLARATION_V22 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V22.json"
)
DECLARATION_V23 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V23.json"
)
DECLARATION_V24 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V24.json"
)
DECLARATION_V25 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V25.json"
)
#: V26 is Session CP's graduation (cp_true_utc_ny_metals_long_v1, 57->58 / 55->56). Session CQ
#: graduated in PARALLEL against V25 (its fork is preserved at phase18/receipts/
#: CQ_CANDIDATE_FAMILY_V26.json and its gate receipt cites that file); the fork is resolved at
#: V27, which is V26 plus CQ's cq_current_breaker_re_entry_inverted_5d_stop_0p25d
#: (58->59 / 56->57). Both bills are paid; neither look is dropped. Authored at wave-18
#: integration, 2026-08-01.
DECLARATION_V26 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase18/receipts/CANDIDATE_FAMILY_V26.json"
)
DECLARATION_V27 = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase18/receipts/CANDIDATE_FAMILY_V27.json"
)
DECLARATION_CHAIN = (
    DECLARATION_V1,
    DECLARATION_V2,
    DECLARATION_V3,
    DECLARATION_V4,
    DECLARATION_V5,
    DECLARATION_V6,
    DECLARATION_V7,
    DECLARATION_V8,
    DECLARATION_V9,
    DECLARATION_V10,
    DECLARATION_V11,
    DECLARATION_V12,
    DECLARATION_V13,
    DECLARATION_V14,
    DECLARATION_V15,
    DECLARATION_V16,
    DECLARATION_V17,
    DECLARATION_V18,
    DECLARATION_V19,
    DECLARATION_V20,
    DECLARATION_V21,
    DECLARATION_V22,
    DECLARATION_V23,
    DECLARATION_V24,
    DECLARATION_V25,
    DECLARATION_V26,
    DECLARATION_V27,
)
DEFAULT_DECLARATION = DECLARATION_CHAIN[-1]

#: Statuses a member row may carry. A withdrawn member keeps its row -- deleting the row is
#: what `high_water_size` exists to catch.
DECLARED = "declared"
WITHDRAWN = "withdrawn"
_STATUSES = (DECLARED, WITHDRAWN)

#: Which count a caller wants. `ALL_DECLARED` is the conservative default; `LOOKS_TAKEN`
#: drops members that never produced a trade and must be asked for by name (see
#: `Member.look_taken`).
ALL_DECLARED = "all_declared"
LOOKS_TAKEN = "looks_taken"


class CandidateFamilyError(Exception):
    """Raised on any structural defect. Every branch fails CLOSED.

    A malformed declaration must never degrade to a small family, because a small family is
    the permissive direction: it is the failure mode that admits a candidate the evidence
    does not support. So every check below raises rather than falling back to a default.
    """


@dataclass(frozen=True)
class Member:
    """One candidate, named. `basis` is why it belongs to the family, not how it performed.

    `look_taken` is the one field that can make a family cheaper, so it is the one that
    needs the tightest rule. It is False only for a member that **tested no hypothesis at
    all** — a sleeve with zero trades, hence no null, no p-value and no chance of admitting.
    Three of the live registry's 32 are in exactly that state (`mx_eu50_cash_*`,
    `mx_fra40_cash_*`, `vp_euidx_pocgrav`: `n_trades = 0`, verdict `NOT_EVALUABLE`,
    prescription `GENERATION`), and AA, AE and AF each independently omitted them rather
    than scoring them, for the same reason.

    Why the exclusion is legitimate rather than curation: whether a generator has bars and
    is wired is a property of the DATA AND THE CODE, decided before any return is seen. It
    is the same class of restriction as `GateSpec.coverage_policy="restrict_to_priced"`,
    whose own comment says why it does not bias an estimate — "which symbols are priceable is
    determined by what is in the tick archive, NOT by what those symbols earned."

    And it is not the default. `Family.effective_size()` counts every declared member;
    reading the cheaper number requires asking for it by name
    (`with_declared_family(..., basis=LOOKS_TAKEN)`), which then travels in the seal.
    """

    name: str
    source: str
    basis: str
    declared_at: str
    status: str = DECLARED
    withdrawn_at: Optional[str] = None
    withdrawn_reason: Optional[str] = None
    #: False == this member never produced a trade, so no hypothesis was tested.
    look_taken: bool = True
    #: Required when `look_taken` is False: the artifact and figure that establish it.
    no_look_evidence: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status not in _STATUSES:
            raise CandidateFamilyError(
                f"member {self.name!r}: status must be one of {_STATUSES}, got "
                f"{self.status!r}"
            )
        if not self.look_taken and not self.no_look_evidence:
            raise CandidateFamilyError(
                f"member {self.name!r} claims look_taken=False with no `no_look_evidence`. "
                f"That claim is the only edit in this artifact that can LOWER a bill, so it "
                f"must cite the artifact and the zero-trade figure that establish it."
            )
        if self.look_taken and self.no_look_evidence:
            raise CandidateFamilyError(
                f"member {self.name!r} carries `no_look_evidence` while look_taken is True"
            )
        if self.status == WITHDRAWN and not self.withdrawn_at:
            raise CandidateFamilyError(
                f"member {self.name!r} is withdrawn with no `withdrawn_at`. A withdrawal "
                f"that carries no date cannot be checked against the declaration date, "
                f"and a withdrawal is the only edit that could look like curation."
            )
        if self.status == DECLARED and self.withdrawn_at:
            raise CandidateFamilyError(
                f"member {self.name!r} carries `withdrawn_at` but status {DECLARED!r}"
            )
        _iso(self.declared_at, f"member {self.name!r}.declared_at")


@dataclass(frozen=True)
class Family:
    """One declared family. `effective_size` is the ratchet and is the only number the gate
    is entitled to read."""

    family_id: str
    purpose: str
    declaration_date: str
    members: tuple[Member, ...]
    #: The size floor, STORED. Redundant with `len(members)` while nothing is deleted --
    #: which is exactly why it is here. `len(members)` falls silently if a row is removed
    #: from the JSON; a stored floor turns that edit into a load-time refusal.
    high_water_size: int
    #: The same floor for the looks-taken count. Without it, flipping a member's
    #: `look_taken` to False after the fact would lower that bill silently, which is the
    #: same attack `high_water_size` blocks for row deletion.
    high_water_looks: int = 0
    #: Append-only amendment log. Every member whose `declared_at` post-dates the family's
    #: `declaration_date` must be accounted for by an entry here.
    history: tuple[dict, ...] = field(default_factory=tuple)
    note: str = ""

    def __post_init__(self) -> None:
        _iso(self.declaration_date, f"family {self.family_id!r}.declaration_date")
        if not self.members:
            raise CandidateFamilyError(f"family {self.family_id!r} declares no members")
        names = [m.name for m in self.members]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            raise CandidateFamilyError(
                f"family {self.family_id!r} repeats member(s) {dupes}. A repeated row would "
                f"inflate the bill without a look having been taken, which is the mirror "
                f"image of the defect this artifact closes."
            )
        if len(self.members) < self.high_water_size:
            raise CandidateFamilyError(
                f"family {self.family_id!r} carries {len(self.members)} member rows against "
                f"a stored high_water_size of {self.high_water_size}. Rows have been "
                f"DELETED. Withdrawal is expressed by status={WITHDRAWN!r}, which keeps the "
                f"row and keeps the bill; deleting a row lowers the bill for a look that was "
                f"already taken. Refusing rather than correcting, because the honest size "
                f"cannot be recovered from what is left."
            )
        n_looks = sum(1 for m in self.members if m.look_taken)
        if n_looks < self.high_water_looks:
            raise CandidateFamilyError(
                f"family {self.family_id!r} counts {n_looks} looks against a stored "
                f"high_water_looks of {self.high_water_looks}. A member's `look_taken` has "
                f"been flipped to False after the fact, which retracts a hypothesis that was "
                f"already tested."
            )
        # A member declared after the family opened is legitimate -- and it is the edit that
        # must be visible, because it is the one that raises the bill.
        late = [m.name for m in self.members
                if _iso(m.declared_at, m.name) > _iso(self.declaration_date, self.family_id)]
        if late:
            amended = {n for h in self.history for n in h.get("members_added", ())}
            unlogged = sorted(set(late) - amended)
            if unlogged:
                raise CandidateFamilyError(
                    f"family {self.family_id!r}: member(s) {unlogged} carry a declared_at "
                    f"after the family's declaration_date {self.declaration_date} and no "
                    f"`history` entry adds them. An undocumented late addition is "
                    f"indistinguishable from a member chosen once its outcome was known."
                )

    # -------------------------------------------------------------------------------
    def active(self) -> tuple[Member, ...]:
        """Members still in the book. This is the COMPOSITION, never the bill."""
        return tuple(m for m in self.members if m.status == DECLARED)

    def withdrawn(self) -> tuple[Member, ...]:
        return tuple(m for m in self.members if m.status == WITHDRAWN)

    def effective_size(self) -> int:
        """The conservative bill and the DEFAULT: every member ever declared, floored by
        the stored high-water mark.

        Deliberately NOT `len(self.active())`. See the module docstring -- a withdrawn
        member's look was still taken, and letting a withdrawal shrink the family makes
        "withdraw the siblings" the cheapest route to an admission.
        """
        return max(self.high_water_size, len(self.members))

    def looks_taken_size(self) -> int:
        """The narrower bill: members that actually tested a hypothesis.

        Ratcheted the same way, and never the default -- a caller must name this basis, and
        naming it puts it in the spec seal. See `Member.look_taken` for why a zero-trade
        member is an outcome-independent exclusion rather than curation.
        """
        return max(self.high_water_looks, sum(1 for m in self.members if m.look_taken))

    def size_for(self, basis: str) -> int:
        if basis == ALL_DECLARED:
            return self.effective_size()
        if basis == LOOKS_TAKEN:
            return self.looks_taken_size()
        raise CandidateFamilyError(
            f"unknown basis {basis!r}; expected one of {(ALL_DECLARED, LOOKS_TAKEN)}"
        )

    def no_look_members(self) -> tuple[Member, ...]:
        return tuple(m for m in self.members if not m.look_taken)

    def as_dict(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "purpose": self.purpose,
            "declaration_date": self.declaration_date,
            "high_water_size": self.high_water_size,
            "high_water_looks": self.high_water_looks,
            "effective_size": self.effective_size(),
            "looks_taken_size": self.looks_taken_size(),
            "n_active": len(self.active()),
            "n_withdrawn": len(self.withdrawn()),
            "n_no_look": len(self.no_look_members()),
            "members": [
                {k: v for k, v in m.__dict__.items() if v is not None} for m in self.members
            ],
            "history": list(self.history),
            "note": self.note,
        }


@dataclass(frozen=True)
class CandidateFamily:
    """A loaded declaration.

    TWO HASHES, AND THE SECOND ONE IS THE IDENTITY THAT MATTERS
    ----------------------------------------------------------
    `sha256` is over the FILE BYTES -- provenance, and it moves when anything in the document
    moves, including a comment.

    `membership_sha256` is over the CANONICAL MEMBERSHIP ONLY: per family, the sorted
    (name, status, look_taken) triples plus the two high-water floors. It is what
    `declared_family_id` carries, and it does NOT move when prose moves.

    The first draft used the file sha for the id, and that reproduced in this module the exact
    defect `spec.canonical()` exists to avoid -- its own comment says `notes` is excluded
    "deliberately: free-form commentary must not be able to change the seal, or every typo fix
    would read as a methodology change." Editing a `basis` string or adding a documentation key
    would have read as a different family. Caught when an adversarial pass forced a
    documentation edit and the id moved while the 32/29/276/298 sizes did not.
    """

    path: str
    sha256: str
    membership_sha256: str
    declaration_date: str
    families: dict[str, Family]
    freeze_rule: dict
    ratified_by: Optional[str] = None
    ratified_utc: Optional[str] = None

    def family(self, family_id: str) -> Family:
        try:
            return self.families[family_id]
        except KeyError:
            raise CandidateFamilyError(
                f"unknown family {family_id!r}; declared families are "
                f"{sorted(self.families)}"
            ) from None

    def effective_size(self, family_id: str, basis: str = ALL_DECLARED) -> int:
        return self.family(family_id).size_for(basis)

    def membership_of(self, family_id: str) -> str:
        """The canonical-membership hash for ONE family, so a change to family A cannot move
        family B's identity."""
        return _membership_hash({family_id: self.family(family_id)})

    def is_ratified(self) -> bool:
        """Whether an owner has signed the RULE (not the number).

        Unratified is the normal state for a declaration a session has just written, and it
        is not an error: the numbers are computable and comparable before anyone signs. What
        it means is that no verdict produced against it is an arming decision yet.
        """
        return bool(self.ratified_by)


# ------------------------------------------------------------------------------------
def _iso(s: str, what: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        raise CandidateFamilyError(f"{what}: {s!r} is not an ISO date") from None


def _membership_hash(families: dict) -> str:
    """sha256 over membership and the floors ONLY -- never over prose.

    Included: family id, declaration date, both high-water floors, and per member the
    (name, status, look_taken) triple. Excluded: `purpose`, `basis`, `source`, `note`,
    `provenance`, `history` text, every `no_look_evidence` string -- everything a reader can
    improve without changing which hypotheses were declared.
    """
    blob = {
        fid: {
            "declaration_date": f.declaration_date,
            "high_water_size": f.high_water_size,
            "high_water_looks": f.high_water_looks,
            "members": sorted((m.name, m.status, bool(m.look_taken)) for m in f.members),
        }
        for fid, f in sorted(families.items())
    }
    return hashlib.sha256(
        json.dumps(blob, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _member(d: dict) -> Member:
    missing = [k for k in ("name", "source", "basis", "declared_at") if not d.get(k)]
    if missing:
        raise CandidateFamilyError(f"member row {d!r} is missing {missing}")
    return Member(
        name=str(d["name"]), source=str(d["source"]), basis=str(d["basis"]),
        declared_at=str(d["declared_at"]), status=str(d.get("status", DECLARED)),
        withdrawn_at=(str(d["withdrawn_at"]) if d.get("withdrawn_at") else None),
        withdrawn_reason=(str(d["withdrawn_reason"]) if d.get("withdrawn_reason") else None),
        look_taken=bool(d.get("look_taken", True)),
        no_look_evidence=(str(d["no_look_evidence"]) if d.get("no_look_evidence") else None),
    )


def load_candidate_family(path: str | Path | None = None) -> CandidateFamily:
    """Read and validate a declaration. Raises `CandidateFamilyError` on any defect.

    There is no fallback and no default family. A caller who cannot read the declaration
    must not silently get a smaller bill.
    """
    p = Path(path) if path else DEFAULT_DECLARATION
    try:
        raw = p.read_bytes()
    except OSError as e:
        raise CandidateFamilyError(f"cannot read declaration at {p}: {e}") from None
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        raise CandidateFamilyError(f"declaration at {p} is not valid JSON: {e}") from None
    if d.get("schema") != SCHEMA:
        raise CandidateFamilyError(
            f"declaration at {p} carries schema {d.get('schema')!r}, expected {SCHEMA!r}"
        )
    decl_date = str(d.get("declaration_date", ""))
    _iso(decl_date, "declaration_date")
    fams_raw = d.get("families") or {}
    if not fams_raw:
        raise CandidateFamilyError(f"declaration at {p} declares no families")
    fams = {}
    for fid, f in fams_raw.items():
        members = tuple(_member(m) for m in (f.get("members") or ()))
        hw = f.get("high_water_size")
        if hw is None:
            raise CandidateFamilyError(
                f"family {fid!r} has no `high_water_size`. It is the stored floor that makes "
                f"a deleted member row detectable; without it the ratchet is unenforceable."
            )
        fams[fid] = Family(
            family_id=str(fid), purpose=str(f.get("purpose", "")),
            declaration_date=str(f.get("declaration_date", decl_date)),
            members=members, high_water_size=int(hw),
            high_water_looks=int(f.get("high_water_looks") or 0),
            history=tuple(f.get("history") or ()), note=str(f.get("note", "")),
        )
    return CandidateFamily(
        path=str(p), sha256=hashlib.sha256(raw).hexdigest(),
        membership_sha256=_membership_hash(fams),
        declaration_date=decl_date, families=fams,
        freeze_rule=dict(d.get("freeze_rule") or {}),
        ratified_by=(d.get("ratified_by") or None),
        ratified_utc=(d.get("ratified_utc") or None),
    )


def with_declared_family(spec, family_id: str, *, basis: str = ALL_DECLARED,
                         declaration: str | Path | None = None,
                         loaded: CandidateFamily | None = None):
    """`GateSpec` -> a copy whose multiplicity bill comes from the declaration.

    Sets three fields: the size the gate arithmetic reads, and the declaration's id and
    sha256, which the seal then carries. Resolution happens HERE rather than inside
    `run_gate` on purpose -- the gate stays a pure function of its spec, so a result's seal
    fully determines the correction that produced it, with no run-time file read in between.

    `basis` defaults to the conservative count. The narrower `LOOKS_TAKEN` basis is named in
    the resolved `declared_family_id`, so a verdict cannot quietly be produced against the
    cheaper number: the id reads `<sha12>:<family_id>@looks_taken` and appears in the seal,
    in `family.multiplicity` and in every `significance` gate note.
    """
    fam = loaded if loaded is not None else load_candidate_family(declaration)
    f = fam.family(family_id)
    suffix = "" if basis == ALL_DECLARED else f"@{basis}"
    # The id carries the PER-FAMILY membership hash, not the file's: a change to another
    # family, or to any prose anywhere, must not move this family's identity. The file sha
    # still travels in `declared_family_sha256` for provenance.
    mh = fam.membership_of(family_id)
    return spec.with_(
        declared_family_size=f.size_for(basis),
        declared_family_id=f"{mh[:12]}:{family_id}{suffix}",
        declared_family_sha256=fam.sha256,
    )


def sensitivity(p_raw: float, sizes, *, alphas=(0.05, 0.10, 0.20),
                methods=("benjamini_hochberg", "bonferroni")) -> list[dict]:
    """Would this p-value admit, at each (family size, alpha, method)?

    This is the table that lets an owner ratify a RULE instead of a number: it prices every
    candidate stopping point at once, so the choice is made against the whole surface rather
    than against the one cell that happens to be favourable.

    A single sleeve's q under both corrections, with `m - 1` siblings carried at p = 1.0,
    reduces to the same comparison: `p_raw <= alpha / m` for Bonferroni, and for
    Benjamini-Hochberg the smallest p in a family whose other members are all 1.0 is rejected
    exactly when `p_raw <= alpha / m` too (its BH threshold is `1 * alpha / m`). They coincide
    HERE and only here -- with real sibling p-values BH is the weaker bill -- so both are
    reported and labelled rather than one being quoted as "the" answer.
    """
    out = []
    for m in sizes:
        m = int(m)
        if m < 1:
            raise CandidateFamilyError(f"family size must be >= 1, got {m}")
        for a in alphas:
            for meth in methods:
                thr = a / m  # see the docstring: identical for both at k = 1
                out.append({
                    "family_size": m, "alpha": a, "multiplicity": meth,
                    "threshold": thr, "p_raw": p_raw,
                    "admits": bool(p_raw <= thr),
                    "q_value_single": min(1.0, p_raw * m),
                })
    return out


def max_size_that_admits(p_raw: float, alpha: float) -> int:
    """The largest family a p-value survives at `alpha`: floor(alpha / p_raw).

    Reported so the sensitivity table has a closed-form spine rather than only a grid, and
    so a reader can see the answer for a size the grid does not happen to contain.
    """
    if p_raw <= 0:
        raise CandidateFamilyError("p_raw must be > 0")
    return int(alpha / p_raw)
