"""The supersession register is enforced, not decorative.

Wrong numbers in this estate have cost real time repeatedly, and the reason is always the
same: a claim is refuted in a receipt nobody reads while the artifact that carries it goes
on saying the original thing. `phase20/forward/SUPERSEDED_CLAIMS_V1.json` is the index of
those claims; these tests make sure the annotations it points at actually exist at source,
so a future edit that strips one fails the build.

Deliberately NOT tested here: whether the superseding measurement is right. That is what
its own receipt is for. This file only enforces that the record is annotated where a
reader would look.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
REGISTER = REPO / "docs/audits/fable5-vision-audit-20260725/phase20/forward/SUPERSEDED_CLAIMS_V1.json"

ANNOTATION_KEY = "_RETRACTED_2026_08_07"

#: Files that must carry an in-source annotation, and the token that proves it is there.
#: Kept explicit rather than derived so that deleting a register row cannot also delete
#: the requirement.
REQUIRED_ANNOTATIONS: dict[str, str] = {
    "config/agent_config.yaml": "RETRACTED EVIDENCE, annotated 2026-08-07",
    "src/components/ultimate_book/sleeves/candidate_registry.py": "PROVENANCE WARNING, measured 2026-08-07",
    ".context/00_core/research_current_state.md": "PROVENANCE WARNING, measured 2026-08-07",
    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/r2/R2_RESULT_V1.json":
        "armed_sleeves_corrected_20260807",
    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/r1/r1_estate_rewalk.py":
        "CORRECTED 2026-08-07",
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_production_replacement_activation_2026_05_26/"
    "STAGE13_RETRACTION_2026-08-07.md": "the founding numbers for all ten broad families are SUPERSEDED",
    # The highest-dependency stale numbers in the estate: the mandatory root briefing stated
    # the armed set two different ways in one section, and both were wrong.
    "CLAUDE.md": "STOP — do not read the armed set out of this file",
    "scripts/rerate_book_from_live.py": "CORRECTED 2026-08-07",
}

#: CLAUDE.md carries more than one correction, and a single-token check would let the others
#: be stripped silently.
CLAUDE_MD_REQUIRED = (
    "STOP — do not read the armed set out of this file",
    "The armed set is FOUR on BOTH accounts",
    "src.safety.armed_set.armed_sleeves()",
    "THE ESTATE HAS NO STANDING ADMISSION",
)


def test_claude_md_carries_every_p4_correction() -> None:
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    missing = [t for t in CLAUDE_MD_REQUIRED if t not in text]
    assert missing == [], (
        f"CLAUDE.md lost {missing}. It is the mandatory root briefing: a stale armed set there "
        "is read by every session before anything else."
    )


def test_claude_md_does_not_reassert_a_superseded_armed_set_uncorrected() -> None:
    """The two stale statements are struck in place rather than deleted (CLAUDE.md section 10),
    so this checks they are struck -- carrying the strikethrough markers -- not that they are gone."""

    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    if "The armed set is exactly three sleeves" in text:
        assert "~~**The armed set is exactly three sleeves**" in text, (
            "the three-sleeve claim is present but no longer struck"
        )
    if "FIVE sleeves since 2026-07-31" in text:
        assert "~~FIVE sleeves since 2026-07-31" in text, (
            "the five-sleeve claim is present but no longer struck"
        )

STAGE13_DIR = (REPO / "research/science_program_2026_05/06_outcome_testing"
               / "vnext_moonshot_production_replacement_activation_2026_05_26")

STAGE13_ANNOTATED = (
    "VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_2026-05-26.json",
    "VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_SUMMARY_2026-05-26.json",
    "VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_2026-05-26.json",
    "VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_BRANCH_ORIGIN_AUDIT_SUMMARY_2026-05-26.json",
    "VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_SUMMARY_2026-05-26.json",
)


def _register() -> dict:
    return json.loads(REGISTER.read_text(encoding="utf-8"))


def test_the_register_exists_and_is_well_formed() -> None:
    doc = _register()
    assert doc["schema"] == "gtos-superseded-claims-v1"
    assert doc["claims"], "an empty supersession register is a lie of omission"
    for claim in doc["claims"]:
        assert claim["id"]
        assert claim["claim"]
        assert claim["carried_in"], f"{claim['id']} names no artifact"
        assert claim["superseded_by"], f"{claim['id']} names no replacement"
        assert claim.get("severity"), f"{claim['id']} is unranked"


def test_every_register_row_points_at_a_file_that_exists() -> None:
    """A register that cites a path nobody can open is the exact failure it exists to
    prevent -- see the CANDIDATE-BOOK-WEIGHT-PROVENANCE row, which is IN this register
    precisely because its own citation is unopenable.

    The invariant is TRACKED, not present-on-disk. This repository runs a sparse checkout
    (~20 % of tracked files materialised), so an on-disk test would report a legitimately
    sparse artifact as missing -- which is exactly what it did on first run, and is the
    difference between "we never had it" and "you have not checked it out".
    """

    import subprocess

    missing: list[str] = []
    for claim in _register()["claims"]:
        for ref in claim["carried_in"]:
            path = ref.split("#", 1)[0].split(":", 1)[0]
            if (REPO / path).exists():
                continue
            tracked = subprocess.run(["git", "cat-file", "-e", f"HEAD:{path}"],
                                     cwd=REPO, capture_output=True)
            if tracked.returncode != 0:
                missing.append(f"{claim['id']}: {path} (neither on disk nor tracked at HEAD)")
    assert missing == [], missing


@pytest.mark.parametrize("rel,token", sorted(REQUIRED_ANNOTATIONS.items()))
def test_the_annotation_is_still_at_source(rel: str, token: str) -> None:
    path = REPO / rel
    assert path.exists(), f"{rel} is gone; the annotation went with it"
    assert token in path.read_text(encoding="utf-8"), (
        f"{rel} no longer carries its supersession annotation ({token!r}). Wrong numbers "
        "without their retraction is the failure mode this register exists to prevent."
    )


@pytest.mark.parametrize("name", STAGE13_ANNOTATED)
def test_the_stage13_artifacts_carry_their_retraction_and_keep_their_values(name: str) -> None:
    """Two properties at once, because either alone is a different mistake: the retraction
    must be present (or a reader cites a refuted number) and the original values must be
    untouched (or we have rewritten history instead of annotating it -- CLAUDE.md section 10)."""

    doc = json.loads((STAGE13_DIR / name).read_text(encoding="utf-8"))
    ann = doc.get(ANNOTATION_KEY)
    assert ann, f"{name} lost its retraction annotation"
    assert "SUPERSEDED BY MEASUREMENT" in ann["status"]
    assert ann["register"].endswith("SUPERSEDED_CLAIMS_V1.json")

    # The originals, still present and still exactly what they were.
    if "PRODUCTION_SELECTOR_SUMMARY" in name:
        assert doc["broader_origin_selected_metrics"]["expectancy_r"] == 0.41278122349174634
    if "BROADER_ORIGIN_REPLAY_SUMMARY" in name:
        fam = doc["family_summary"]
        assert fam["structural_distance_extreme"]["activation_ready_dynamic_metrics"][
            "expectancy_r"] == 1.196255130294
        # And the finding this lane added: four of seven activated families negative at birth.
        activated = ("cross_asset_lead_lag", "displacement_continuation", "liquidity_sweep_reclaim",
                     "regime_transition_break", "session_open_range_break",
                     "structural_distance_extreme", "volatility_compression_expansion")
        negative = [f for f in activated
                    if fam[f]["activation_ready_dynamic_metrics"]["expectancy_r"] < 0]
        assert len(negative) == 4, negative


def test_the_stage13_headline_is_a_selection_not_a_population() -> None:
    """The arithmetic behind the retraction, recomputed rather than quoted: the published
    +0.41278 is over the SELECTED subset, and row-weighting the seven activated families in
    the same evidence gives a materially smaller number."""

    sel = json.loads((STAGE13_DIR / "VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_"
                      "SUMMARY_2026-05-26.json").read_text(encoding="utf-8"))
    rep = json.loads((STAGE13_DIR / "VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_"
                      "SUMMARY_2026-05-26.json").read_text(encoding="utf-8"))
    activated = ("cross_asset_lead_lag", "displacement_continuation", "liquidity_sweep_reclaim",
                 "regime_transition_break", "session_open_range_break",
                 "structural_distance_extreme", "volatility_compression_expansion")
    blocks = [rep["family_summary"][f]["activation_ready_dynamic_metrics"] for f in activated]
    rows = sum(b["performance_rows"] for b in blocks)
    total_r = sum(b["expectancy_r"] * b["performance_rows"] for b in blocks)
    pooled = total_r / rows

    assert rows == 307042
    assert pooled == pytest.approx(0.293508, abs=5e-7)
    assert sel["broader_origin_selected_metrics"]["expectancy_r"] - pooled == pytest.approx(
        0.119273, abs=5e-7)

    sdx = rep["family_summary"]["structural_distance_extreme"]["activation_ready_dynamic_metrics"]
    share = sdx["expectancy_r"] * sdx["performance_rows"] / total_r
    assert share == pytest.approx(0.709, abs=0.001), share
