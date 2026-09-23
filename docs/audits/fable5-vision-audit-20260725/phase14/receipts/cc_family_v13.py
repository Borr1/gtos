"""CANDIDATE_FAMILY_V13 — the rule carry, renumbered at the wave-14 train.

THE COLLISION THIS FILE'S OWN PREDECESSOR PREDICTED
---------------------------------------------------
Session CC's `cc_family_v12.py` (git history; removed at the train, its docstring carried the
whole B2204-B2206 measurement) built V11's membership + V2's `ratified_rule` and named the
collision in advance: Session CA was commissioned to declare looks before gating and might
publish its own `CANDIDATE_FAMILY_V12.json` in the same wave. CA did (one look: converting
`vp_euidx_pocgrav` from declared-not-taken to TAKEN, `CANDIDATE_BOOK_V1` 50 -> 51 looks,
`ESTATE_UNION_V1` 295 -> 296; ZERO new members). Per CC's own collision note — "renumber THIS
one; it adds zero members and zero looks, so re-parenting is a one-line supersedes change with
no arithmetic to redo" — CA's declaration keeps the V12 number (first merged) and the rule
carry becomes V13, parented on CA's V12.

WHAT V13 IS, EXACTLY
--------------------
  * **membership-identical to V12 (CA's)**, family for family, member for member, look for
    look, both high-water marks unchanged. This carry declares NO hypothesis and takes NO look.
  * **carries `ratified_rule` byte-identical from V2** (Borhen's 2026-07-30 ratification:
    `CANDIDATE_BOOK_V1`, all-declared basis, sealed `B_balanced` alpha 0.10), across the
    nine-version gap CC measured: V3 through V11 all dropped `ratified_rule` while
    `DECLARATION_CHAIN` still pointed at V2 — the stale pointer hid the dropped rule and the
    dropped rule made moving the pointer expensive (B2204-B2206). CA's V12 restored the chain's
    membership head but not the rule (it predates CC's finding); V13 closes both.
  * `supersedes` V12, with `supersedes_sha256`, so the chain stays a chain and the head — the
    declaration `graduation.py` bills against — again carries the rule the guard asserts.

Re-runnable and deterministic: every field is read from V12 or V2, none is transcribed.

    python3 docs/audits/fable5-vision-audit-20260725/phase14/receipts/cc_family_v13.py
"""

from __future__ import annotations

import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
AUDIT = HERE.parents[1]
V2 = AUDIT / "phase9/receipts/CANDIDATE_FAMILY_V2.json"
V12 = HERE / "CANDIDATE_FAMILY_V12.json"
OUT = HERE / "CANDIDATE_FAMILY_V13.json"


def _rel(p: pathlib.Path) -> str:
    return str(p.relative_to(AUDIT.parents[2]))


def build() -> dict:
    v2 = json.loads(V2.read_text(encoding="utf-8"))
    v12 = json.loads(V12.read_text(encoding="utf-8"))

    families = json.loads(json.dumps(v12["families"]))  # deep copy, untouched

    rule = json.loads(json.dumps(v2["ratified_rule"]))
    rule["carried_from"] = (
        f"{_rel(V2)} -> ratified_rule, byte-identical apart from this label. CARRIED, not "
        f"re-ratified: a session cannot ratify, and the ratchet does not touch the rule. "
        f"RE-CARRIED 2026-07-31 by Session CC (B2204-B2206) across a NINE-VERSION GAP (V3..V11 "
        f"all dropped `ratified_rule` while DECLARATION_CHAIN pointed at V2 — a 51% under-bill "
        f"in the permissive direction), then RENUMBERED V12 -> V13 at the wave-14 train because "
        f"Session CA's look declaration took the V12 number first, exactly as CC's collision "
        f"note predicted. Original label preserved below."
    )
    rule["carried_from_original"] = v2["ratified_rule"]["carried_from"]

    doc = {
        "schema": v12["schema"],
        "declaration_date": "2026-07-31",
        "declared_by": (
            "Session CC (wave 14, blocks B2200-B2249) — the training-lane protocol machinery; "
            "renumbered V12 -> V13 by the orchestrator at the wave-14 train per CC's own "
            "collision note. This declaration adds NO member and NO look; it exists to put the "
            "ratified rule back on the head of the chain and to give the graduation biller a "
            "head to write successors of."
        ),
        "generated_by": _rel(pathlib.Path(__file__).resolve()),
        "supersedes": _rel(V12),
        "supersedes_sha256": hashlib.sha256(V12.read_bytes()).hexdigest(),
        "superseded_because": (
            "V12 (Session CA's) is membership-correct — V11 plus CA's one declared-then-taken "
            "look on vp_euidx_pocgrav — and rule-blind, like V3..V11 before it (CA's session "
            "ran before CC's finding merged). Without this carry the chain head would again "
            "fail the ratified-rule guard, which is the exact two-guard cover CC measured: the "
            "stale pointer hid the dropped rule and the dropped rule made moving the pointer "
            "expensive. V13 is V12's membership plus V2's rule."
        ),
        "families": families,
        "freeze_rule": v12.get("freeze_rule", {}),
        "ratified_rule": rule,
        "ratified_by": v12.get("ratified_by"),
        "ratified_utc": v12.get("ratified_utc"),
        "what_is_being_ratified": v12.get("what_is_being_ratified"),
        "membership_identity_claim": (
            "Every family, every member row, every look state, both high-water marks are "
            "copied from V12 unmodified. `_membership_hash` over V13 therefore equals "
            "`_membership_hash` over V12, which "
            "tests/research_infra/test_training_lane_protocol.py::"
            "test_v13_is_membership_identical_to_v12 asserts by computing both."
        ),
        "training_lane_note": (
            "The training lane (ratified 2026-07-31) bills the family at ONE point only: "
            "graduation to the sealed gate, via "
            "`src/research_infra/training_lane/graduation.py`. Iteration on TRAIN/VAL is "
            "logged and unbilled. Nothing in that lane changes this rule, this alpha, or this "
            "family — it changes how cheaply a candidate can be searched for before it arrives."
        ),
    }
    return doc


def main() -> None:
    doc = build()
    blob = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False)
    doc["self_sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    fam = doc["families"]["CANDIDATE_BOOK_V1"]
    print(f"wrote {OUT}")
    print(f"  CANDIDATE_BOOK_V1  high_water_size={fam['high_water_size']} "
          f"high_water_looks={fam['high_water_looks']} members={len(fam['members'])}")
    print(f"  families={sorted(doc['families'])}")
    print(f"  ratified_rule.family={doc['ratified_rule']['family']} "
          f"alpha={doc['ratified_rule']['alpha']} option={doc['ratified_rule']['option']}")


if __name__ == "__main__":
    main()
