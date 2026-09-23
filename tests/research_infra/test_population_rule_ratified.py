"""The ratified population rule is RECORDED, and its conditions travel with it.

Borhen ratified AN's recommendation on 2026-07-30 ("my explicit approval to go as proposed and
recommended on all the decisions"). This pin does for the population rule what
test_candidate_family.py does for the admission rule: a re-generation of the artifact that drops
or alters the ratification is a red test, not a silent regression.
"""
import json
import pathlib

ARTIFACT = pathlib.Path(__file__).resolve().parents[2] / (
    "docs/audits/fable5-vision-audit-20260725/phase10/receipts/POPULATION_RULE_V1.json"
)


def _rule():
    return json.loads(ARTIFACT.read_text())["ratified_rule"]


def test_ratified_population_is_recorded():
    assert _rule()["population"] == "RECORDED"


def test_ratification_names_the_owner_and_the_date():
    r = _rule()
    assert "Borhen" in r["ratified_by"]
    assert r["ratified_utc"].startswith("2026-07-30")


def test_the_band_condition_travels_with_the_admission():
    conditions = " ".join(_rule()["conditions"])
    assert "band travels with the admission" in conditions
    assert "band_high" in conditions


def test_the_admission_cell_is_5r_and_sizing_uses_recent_folds():
    conditions = " ".join(_rule()["conditions"])
    assert "target_5R is the admission cell" in conditions
    assert "recent folds" in conditions


def test_rejected_alternatives_are_recorded_with_reasons():
    alts = _rule()["rejected_alternatives"]
    assert set(alts) == {"DECIDABLE", "BOTH", "ALL_ERAS", "tau_cost_range_criterion"}
    assert all(len(v) > 20 for v in alts.values())
