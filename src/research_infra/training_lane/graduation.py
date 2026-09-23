"""CC-3 — the graduation biller: the ONE point at which the family ratchet moves.

    iteration on TRAIN/VAL   ->  logged, unbilled            (iteration_ledger)
    graduation to the gate   ->  exactly one look, billed     (HERE, and nowhere else)
    the sealed gate itself   ->  FROZEN                       (walkforward/, untouched)

WHAT "ATOMIC" MEANS HERE, HONESTLY
-----------------------------------
Two files move: the family declaration (the bill) and the graduation ledger (the receipt). No
filesystem makes two files move together, so this is not claimed. What IS guaranteed:

  * the declaration is replaced with `os.replace` after being **loaded back and validated**, so
    a reader never sees a prefix of it and never sees a declaration that fails its own loader;
  * the bill is paid BEFORE the receipt is written, so a crash in between leaves the estate
    OVER-billed, never under-billed — the safe direction, and the only one worth choosing;
  * `graduate()` is **idempotent**. Called again for a candidate already in the family, it does
    not re-bill: it finds the paid bill and emits the missing receipt. So the crash above is
    repaired by re-running the same call, not by hand-editing a declaration.

A ratchet that could be paid twice by a retry is not a ratchet, and one whose retry path
requires a human editing JSON is a ratchet that gets edited.

WHAT IS REFUSED, AND WHY EACH REFUSAL IS THE FAIL-CLOSED DIRECTION
------------------------------------------------------------------
  `provenance_missing`         no iteration-ledger row names this candidate. An unlogged
                               candidate has no searchable history, so its bill of one look is
                               a claim nobody can check. The sibling ledger is a PREREQUISITE
                               for billing, which is what stops it being a bypass.
  `provenance_touches_test`    any provenance row that touched TEST. `sealed_holdout`
                               semantics: a confirmation on data you selected on is not a
                               confirmation. Checked on the row's stamped `test_days`, not on
                               its `surface` label alone, so a mislabelled row cannot pass.
  `provenance_spec_mismatch`   the spec being graduated appears in no logged look. The thing
                               going to the gate must be a thing that was looked at.
  `declaration_lost_the_rule`  the declaration carries no `ratified_rule`. Billing against a
                               declaration that has dropped Borhen's sealed rule is how the
                               estate silently returns to the honour system — and it is not
                               hypothetical: V3 through V11 all dropped it (B2204).
  `unknown_family`             the family id is not declared. No fallback, no default family;
                               `CandidateFamilyError`'s own docstring says a small family is
                               the permissive direction.

WHAT THIS MODULE DOES NOT DO
----------------------------
It does not run the gate, score anything, or decide an admission. It hands
`GraduationRecord.apply_to_spec()` a `GateSpec` carrying the resolved declaration, and the
frozen gate does the rest. Nothing here changes what it takes to admit.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from ..walkforward import candidate_family as CF
from .append_only import append_row, atomic_write_json, read_rows
from .iteration_ledger import DEFAULT_ITERATION_LEDGER, IterationLedger

__all__ = [
    "DEFAULT_GRADUATION_LEDGER",
    "GRADUATION_SCHEMA",
    "Candidate",
    "GraduationRecord",
    "GraduationRefusal",
    "graduate",
]

GRADUATION_SCHEMA = "gtos.training_lane.graduation_record.v1"

REPO = Path(__file__).resolve().parents[3]
_RECEIPTS = REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts"
DEFAULT_GRADUATION_LEDGER = _RECEIPTS / "TRAINING_LANE_GRADUATION_LEDGER.jsonl"
#: Successor declarations are written beside the wave's other receipts, numbered by the
#: graduation sequence rather than by hand.
DEFAULT_DECLARATION_DIR = _RECEIPTS


class GraduationRefusal(RuntimeError):
    """A candidate was refused graduation. `reason` is the machine-readable code."""

    def __init__(self, reason: str, message: str, *, detail: Any = None) -> None:
        super().__init__(f"{reason}: {message}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Candidate:
    """What is being sent to the sealed gate.

    `candidate_id` is the join key into the iteration ledger — the value
    `iteration_ledger.candidate_id(...)` returned while the candidate was being iterated. If it
    does not match a logged look, graduation is refused, which is the whole mechanism.
    """

    candidate_id: str
    name: str
    sleeve: str
    spec_digest: str
    basis: str
    source: str
    proposed_by: str
    note: str = ""

    def __post_init__(self) -> None:
        missing = [
            k for k in ("candidate_id", "name", "sleeve", "spec_digest", "basis", "source",
                        "proposed_by")
            if not getattr(self, k)
        ]
        if missing:
            raise GraduationRefusal(
                "candidate_incomplete",
                f"candidate is missing {missing}. `basis` and `source` are the family member "
                f"row's own required fields — a member the declaration cannot explain is a "
                f"member nobody can audit.",
                detail=missing,
            )


@dataclass(frozen=True)
class GraduationRecord:
    """The receipt the sealed gate consumes. `apply_to_spec` is the wiring."""

    candidate: Candidate
    family_id: str
    basis: str
    declaration_path: str
    declared_family_id: str
    declared_family_sha256: str
    declared_family_size: int
    looks_taken_size: int
    billed_looks: int
    graduated_at: str
    provenance: dict
    ratified_rule: dict
    session: str = ""
    blocks: str = ""
    superseded_declaration: str = ""
    idempotent_completion: bool = False
    extra: dict = field(default_factory=dict)

    def apply_to_spec(self, spec: Any):
        """`GateSpec` -> a copy whose multiplicity bill is this graduation's declaration.

        Delegates to `candidate_family.with_declared_family`, which is the estate's existing
        resolver — the gate stays a pure function of its spec and this module adds no second
        way to set a family size.
        """
        return CF.with_declared_family(
            spec, self.family_id, basis=self.basis, declaration=self.declaration_path
        )

    def as_dict(self) -> dict:
        d = {
            "schema": GRADUATION_SCHEMA,
            "row_kind": "graduation",
            "graduated_at": self.graduated_at,
            "session": self.session,
            "blocks": self.blocks,
            "candidate_id": self.candidate.candidate_id,
            "member_name": self.candidate.name,
            "sleeve": self.candidate.sleeve,
            "spec_digest": self.candidate.spec_digest,
            "family_id": self.family_id,
            "basis": self.basis,
            "declaration_path": self.declaration_path,
            "superseded_declaration": self.superseded_declaration,
            "declared_family_id": self.declared_family_id,
            "declared_family_sha256": self.declared_family_sha256,
            "declared_family_size": self.declared_family_size,
            "looks_taken_size": self.looks_taken_size,
            "billed_looks": self.billed_looks,
            "idempotent_completion": self.idempotent_completion,
            "provenance": self.provenance,
            "ratified_rule": {
                k: self.ratified_rule.get(k)
                for k in ("family", "basis", "alpha", "option", "ratified_by", "ratified_utc")
            },
            "admission_rule_note": (
                "The sealed gate is FROZEN. This record sets only the multiplicity bill; the "
                "population rule (RECORDED with AN's conditions), the alpha, the band column "
                "and the chronological fold table are unchanged by the training lane."
            ),
        }
        if self.extra:
            d["extra"] = self.extra
        return d


# ---------------------------------------------------------------------------------------------
def _provenance_summary(rows: Sequence[dict], candidate: Candidate) -> dict:
    spans = [r.get("date_span") or [] for r in rows if r.get("date_span")]
    lo = min((s[0] for s in spans if s), default=None)
    hi = max((s[-1] for s in spans if s), default=None)
    surfaces = sorted({str(r.get("surface")) for r in rows if r.get("surface")})
    disclosures = sorted({d for r in rows for d in (r.get("disclosures") or [])})
    gaps = sorted({g for r in rows for g in (r.get("acknowledged_gaps") or [])})
    return {
        "iteration_ledger_rows": len(rows),
        "look_span": [lo, hi],
        "surfaces_touched": surfaces,
        "engine_versions": sorted({str(r.get("engine_version")) for r in rows}),
        "spec_digests_looked_at": sorted({str(r.get("spec_digest")) for r in rows}),
        "graduating_spec_digest": candidate.spec_digest,
        "verdicts": sorted({str(r.get("verdict")) for r in rows}),
        "sessions": sorted({str(r.get("session")) for r in rows}),
        "run_ids": sorted({str(r.get("run_id")) for r in rows}),
        "disclosures": disclosures,
        "acknowledged_gaps": gaps,
        "test_days_seen": sorted({d for r in rows
                                  for d in ((r.get("surface_stamp") or {}).get("test_days") or [])}),
        "clean_of_test": True,
        "note": (
            "Every look above was unbilled. This graduation bills exactly one, and it is the "
            "only bill the candidate's whole search history incurs."
        ),
    }


def _next_declaration_path(out_dir: Path, current: Path) -> Path:
    """`CANDIDATE_FAMILY_V<n+1>.json`, numbered from the current head's own name so the chain
    stays readable. Refuses to overwrite: a successor that lands on an existing file would
    silently rewrite somebody's declaration."""
    stem = current.stem
    n = 0
    if "_V" in stem:
        tail = stem.rsplit("_V", 1)[-1]
        if tail.isdigit():
            n = int(tail)
    candidate = out_dir / f"CANDIDATE_FAMILY_V{n + 1}.json"
    bump = n + 1
    while candidate.exists():
        bump += 1
        candidate = out_dir / f"CANDIDATE_FAMILY_V{bump}.json"
    return candidate


def graduate(
    candidate: Candidate,
    *,
    family_id: str = "CANDIDATE_BOOK_V1",
    basis: str = CF.ALL_DECLARED,
    iteration_ledger: str | Path = DEFAULT_ITERATION_LEDGER,
    declaration: str | Path | None = None,
    out_declaration: str | Path | None = None,
    graduation_ledger: str | Path = DEFAULT_GRADUATION_LEDGER,
    declared_at: str = "",
    session: str = "",
    blocks: str = "",
    why: str = "",
) -> GraduationRecord:
    """Bill exactly one look to the family ratchet and emit the gate's record.

    Refuses on missing provenance, on any TEST consumption in that provenance, on a spec that
    was never looked at, and on a declaration that has lost the ratified rule. Idempotent: a
    second call for an already-billed candidate completes the receipt rather than re-billing.
    """
    at = declared_at or dt.datetime.now(tz=dt.timezone.utc).date().isoformat()
    led = IterationLedger(iteration_ledger)

    # -- 1. provenance must exist ----------------------------------------------------------
    rows = led.provenance_for(candidate.candidate_id)
    if not rows:
        raise GraduationRefusal(
            "provenance_missing",
            f"no iteration-ledger row names candidate_id {candidate.candidate_id!r} in "
            f"{led.path}. A candidate with no logged search history cannot graduate: the bill "
            f"of one look is a claim about a search nobody can inspect. Log the looks "
            f"(IterationLedger.record) and graduate again.",
            detail={"ledger": str(led.path), "candidate_id": candidate.candidate_id},
        )

    # -- 2. provenance must be clean of TEST ------------------------------------------------
    leaked = sorted({
        d for r in rows for d in ((r.get("surface_stamp") or {}).get("test_days") or [])
    })
    mislabelled = [r for r in rows if str(r.get("surface")) == "TEST"]
    if leaked or mislabelled:
        raise GraduationRefusal(
            "provenance_touches_test",
            f"candidate {candidate.name!r} has provenance on {len(leaked)} TEST day(s) "
            f"({leaked[:5]}) across {len(mislabelled) or len(rows)} row(s). TEST is March 2026, "
            f"every blackout, and the live forward stream — a confirmation on data the "
            f"candidate was selected on is not a confirmation (sealed_holdout semantics). "
            f"Fail closed.",
            detail={"test_days": leaked},
        )

    # -- 3. the spec being graduated must be one that was looked at -------------------------
    looked = {str(r.get("spec_digest")) for r in rows}
    if candidate.spec_digest not in looked:
        raise GraduationRefusal(
            "provenance_spec_mismatch",
            f"the spec being graduated (digest {candidate.spec_digest[:12]}...) appears in none "
            f"of the {len(rows)} logged look(s) for this candidate, which cover "
            f"{sorted(d[:12] for d in looked)}. The thing sent to the gate must be a thing that "
            f"was looked at.",
            detail={"graduating": candidate.spec_digest, "looked_at": sorted(looked)},
        )

    # -- 4. load the ratchet head -----------------------------------------------------------
    decl_path = Path(declaration) if declaration else CF.DEFAULT_DECLARATION
    fam = CF.load_candidate_family(decl_path)
    if family_id not in fam.families:
        raise GraduationRefusal(
            "unknown_family",
            f"family {family_id!r} is not declared in {decl_path.name}; declared families are "
            f"{sorted(fam.families)}. There is no default family and no fallback — a smaller "
            f"family is the permissive direction.",
            detail={"declared": sorted(fam.families)},
        )
    raw = json.loads(decl_path.read_text(encoding="utf-8"))
    rule = raw.get("ratified_rule") or {}
    if not rule:
        raise GraduationRefusal(
            "declaration_lost_the_rule",
            f"{decl_path.name} carries no `ratified_rule`. Billing against a declaration that "
            f"has dropped Borhen's sealed admission rule returns the estate to the honour "
            f"system. This is not hypothetical: CANDIDATE_FAMILY V3 through V11 all dropped it "
            f"(B2204). Carry the rule forward, then graduate.",
            detail={"declaration": str(decl_path)},
        )

    prov = _provenance_summary(rows, candidate)

    # -- 5. already billed? complete the receipt, do not re-bill ----------------------------
    existing = next(
        (m for m in fam.family(family_id).members if m.name == candidate.name), None
    )
    if existing is not None:
        prior = [
            r for r in read_rows(graduation_ledger)
            if "_unparseable" not in r
            and r.get("member_name") == candidate.name
            and r.get("family_id") == family_id
        ]
        record = _record(
            candidate, family_id, basis, decl_path, fam, at, prov, rule,
            session=session, blocks=blocks, billed=0, idempotent=True,
            superseded="", why=why or "already a declared member; bill already paid",
        )
        if not prior:
            append_row(graduation_ledger, record.as_dict())
        return record

    # -- 6. bill exactly one look -----------------------------------------------------------
    doc = copy.deepcopy(raw)
    f = doc["families"][family_id]
    before_size = int(f["high_water_size"])
    before_looks = int(f.get("high_water_looks") or 0)
    f["members"] = list(f.get("members") or []) + [{
        "name": candidate.name,
        "source": candidate.source,
        "basis": candidate.basis,
        "declared_at": at,
        "status": CF.DECLARED,
        "look_taken": True,
        "graduated_by": session or candidate.proposed_by,
        "graduation_candidate_id": candidate.candidate_id,
        "graduation_spec_digest": candidate.spec_digest,
    }]
    f["high_water_size"] = before_size + 1
    f["high_water_looks"] = before_looks + 1
    f["history"] = list(f.get("history") or []) + [{
        "at": at,
        "by": session or candidate.proposed_by,
        "members_added": [candidate.name],
        "size": {"before": before_size, "after": before_size + 1},
        "looks": {"before": before_looks, "after": before_looks + 1},
        "why": (
            why or f"graduation to the sealed gate; {len(rows)} unbilled TRAIN/VAL looks "
            f"precede it, billed as exactly one."
        ),
        "billed_by": "src/research_infra/training_lane/graduation.py::graduate",
        "provenance": {
            "iteration_ledger": str(Path(iteration_ledger)),
            "candidate_id": candidate.candidate_id,
            "n_looks": len(rows),
            "look_span": prov["look_span"],
            "surfaces_touched": prov["surfaces_touched"],
        },
    }]
    doc["declaration_date"] = at
    doc["supersedes"] = str(decl_path.relative_to(REPO)) if decl_path.is_relative_to(REPO) else str(decl_path)
    doc["superseded_because"] = (
        f"training-lane graduation of {candidate.name!r} — one look billed to {family_id} "
        f"(size {before_size} -> {before_size + 1}, looks {before_looks} -> {before_looks + 1})."
    )
    doc["declared_by"] = session or candidate.proposed_by
    doc["generated_by"] = "src/research_infra/training_lane/graduation.py::graduate"
    doc.pop("self_sha256", None)

    out_path = (
        Path(out_declaration) if out_declaration
        else _next_declaration_path(DEFAULT_DECLARATION_DIR, decl_path)
    )
    # Write, LOAD BACK, then replace. A declaration that fails its own loader would stop the
    # estate's billing entirely, and `load_candidate_family` has no fallback by design.
    pending = out_path.with_suffix(out_path.suffix + ".pending")
    atomic_write_json(pending, doc)
    try:
        reloaded = CF.load_candidate_family(pending)
        new_size = reloaded.effective_size(family_id, basis=basis)
        old_size = fam.effective_size(family_id, basis=basis)
        if new_size < old_size:
            raise CF.CandidateFamilyError(
                f"successor declaration bills {new_size} against {old_size}; a look taken "
                f"cannot be un-taken"
            )
        os.replace(pending, out_path)
    except BaseException:
        try:
            pending.unlink()
        except OSError:
            pass
        raise

    final = CF.load_candidate_family(out_path)
    record = _record(
        candidate, family_id, basis, out_path, final, at, prov, rule,
        session=session, blocks=blocks, billed=1, idempotent=False,
        superseded=str(decl_path), why=why,
    )
    # Bill first, receipt second — see the module docstring on what "atomic" means here.
    append_row(graduation_ledger, record.as_dict())
    return record


def _record(candidate, family_id, basis, path, fam, at, prov, rule, *, session, blocks,
            billed, idempotent, superseded, why) -> GraduationRecord:
    suffix = "" if basis == CF.ALL_DECLARED else f"@{basis}"
    mh = fam.membership_of(family_id)
    return GraduationRecord(
        candidate=candidate,
        family_id=family_id,
        basis=basis,
        declaration_path=str(path),
        declared_family_id=f"{mh[:12]}:{family_id}{suffix}",
        declared_family_sha256=fam.sha256,
        declared_family_size=fam.effective_size(family_id, basis=basis),
        looks_taken_size=fam.family(family_id).looks_taken_size(),
        billed_looks=billed,
        graduated_at=at,
        provenance=prov,
        ratified_rule=rule,
        session=session,
        blocks=blocks,
        superseded_declaration=superseded,
        idempotent_completion=idempotent,
        extra=({"why": why} if why else {}),
    )
