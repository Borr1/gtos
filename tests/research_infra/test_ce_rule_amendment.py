"""Session CE (B2330-B2334) — the incubation registry's rule-amendment path.

OD-HISTORICAL-FIRST §1 obliges the estate to restate any rule whose binding clock is a live
fill count measured in months. `mx_btcusd`'s promotion rule is the first instance, and there
was no way to change an incubant's rules without either resetting its history (`register()`
refuses a duplicate id, deliberately) or hand-writing a row (which `_transition` then refuses
at arming, also deliberately).

An amendment path is a HOLE in the wall that pre-registration is. These tests are mostly about
the price the hole charges: both directions together, an owner ceremony, a stated reason, the
superseded ids, and — the one that matters — the LIVE RECORD at the moment of amendment, so a
reader can tell a restatement made on a virgin stream from one made after the fills were
visible.
"""
from __future__ import annotations

import json

import pytest

from src.research_infra.training_lane.incubation import (
    Incubant, IncubationRefusal, IncubationRegistry, OwnerCeremony, PreRegisteredRule,
)

CER = OwnerCeremony(decided_by="Borhen", decided_utc="2026-07-31T12:00:00+00:00",
                    receipt="phase15/CE_PROMOTION_HISTORICAL_FIRST.md")
VIRGIN = {"fills": 0, "cumulative_net_r": 0.0,
          "as_of_utc": "2026-07-31T12:00:00+00:00"}


def _rule(rid, kind="stop", when="2026-07-31T00:00:00+00:00"):
    return PreRegisteredRule(
        rule_id=rid, what=f"the {kind} condition", class_="RISK_BOUND_not_inference",
        action="remove from --tags (owner ceremony)" if kind == "stop" else "propose promotion",
        threshold=-12.375 if kind == "stop" else 30,
        basis="phase14/receipts/CA_MX_INCUBATION_V1.json", pre_registered_utc=when,
        why_not_inference="bounds what the owner pays to find out; it does not test an edge")


def _incubant(i=0):
    return Incubant(
        incubant_id=f"inc_{i}", sleeve=f"sleeve_{i}", account="FTMO", proposed_weight=0.025,
        evidence="phase14/receipts/TEST.json", admission_basis="GRADUATED",
        graduation_record="phase9 admission",
        stop_rules=(_rule(f"S{i}", "stop"),), promotion_rules=(_rule(f"P{i}", "promote"),),
        proposed_by="test")


@pytest.fixture()
def reg(tmp_path):
    return IncubationRegistry(tmp_path / "INC.jsonl", session="CE",
                              now_utc="2026-07-31T12:00:00+00:00")


@pytest.fixture()
def armed(reg):
    reg.register(_incubant(0))
    reg.arm("inc_0", CER)
    return reg


# ------------------------------------------------------------------ the happy path


def test_an_amendment_replaces_the_rules_without_moving_the_state(armed):
    row = armed.amend_rules(
        "inc_0", CER, live_record=VIRGIN,
        stop_rules=(_rule("S0", "stop"),),
        promotion_rules=(_rule("P1-HIST", "promote"),),
        supersedes=["P0"],
        reason="OD-HISTORICAL-FIRST §1: the old rule's binding clock was a live fill count")
    assert row["state"] == "ARMED", "an amendment is not a transition"
    assert row["transition"] == "ARMED->ARMED (amend_rules)"
    assert row["row_kind"] == "incubation_rule_amendment"
    assert [r["rule_id"] for r in row["promotion_rules"]] == ["P1-HIST"]
    assert row["supersedes_rule_ids"] == ["P0"]
    # and the fold sees it
    assert armed.state()["inc_0"]["promotion_rules"][0]["rule_id"] == "P1-HIST"
    assert armed.state()["inc_0"]["state"] == "ARMED"


def test_the_history_survives_because_the_file_is_append_only(armed):
    armed.amend_rules("inc_0", CER, live_record=VIRGIN,
                      stop_rules=(_rule("S0", "stop"),),
                      promotion_rules=(_rule("P1-HIST", "promote"),),
                      supersedes=["P0"], reason="restated")
    rows = armed.rows()
    assert [r["transition"] for r in rows] == [
        "register", "PROPOSED->ARMED", "ARMED->ARMED (amend_rules)"]
    # the ORIGINAL rule is still readable — which is the point of amending rather than editing
    assert rows[0]["promotion_rules"][0]["rule_id"] == "P0"


def test_an_amended_incubant_can_still_be_promoted_on_the_new_rule(armed):
    armed.amend_rules("inc_0", CER, live_record=VIRGIN,
                      stop_rules=(_rule("S0", "stop"),),
                      promotion_rules=(_rule("P1-HIST", "promote"),),
                      supersedes=["P0"], reason="restated")
    row = armed.promote("inc_0", CER, met_rule="P1-HIST", to_weight=0.05)
    assert row["state"] == "PROMOTED" and row["met_rule"] == "P1-HIST"


# ------------------------------------------------- the live record, which is the whole point


def test_a_zero_fill_amendment_is_marked_as_made_on_a_virgin_record(armed):
    row = armed.amend_rules("inc_0", CER, live_record=VIRGIN,
                            stop_rules=(_rule("S0", "stop"),),
                            promotion_rules=(_rule("P1", "promote"),),
                            supersedes=["P0"], reason="restated")
    assert row["amended_on_a_virgin_record"] is True
    assert "no live record this could have been fitted to" in row["amendment_integrity_note"]


def test_a_non_zero_fill_amendment_is_recorded_as_such_and_not_refused(armed):
    """Not refused — a mis-derived rule has to be fixable at any point. Not invisible either."""
    row = armed.amend_rules("inc_0", CER,
                            live_record={"fills": 41, "cumulative_net_r": -3.2},
                            stop_rules=(_rule("S0", "stop"),),
                            promotion_rules=(_rule("P1", "promote"),),
                            supersedes=["P0"], reason="restated")
    assert row["amended_on_a_virgin_record"] is False
    assert "COULD have been fitted to the live stream" in row["amendment_integrity_note"]
    assert row["live_record_at_amendment"]["fills"] == 41


@pytest.mark.parametrize("bad", [None, {}, {"fills": 0}, {"cumulative_net_r": 0.0}, "none"])
def test_an_amendment_without_a_complete_live_record_is_refused(armed, bad):
    with pytest.raises(IncubationRefusal) as exc:
        armed.amend_rules("inc_0", CER, live_record=bad,
                          stop_rules=(_rule("S0", "stop"),),
                          promotion_rules=(_rule("P1", "promote"),),
                          supersedes=["P0"], reason="restated")
    assert exc.value.reason == "amendment_live_record_missing"


# ------------------------------------------------------------------------ the refusals


def test_a_one_sided_amendment_is_refused(armed):
    """Replacing only the promotion side is the shape of a threshold loosened to fit."""
    with pytest.raises(IncubationRefusal) as exc:
        armed.amend_rules("inc_0", CER, live_record=VIRGIN,
                          promotion_rules=(_rule("P1", "promote"),),
                          supersedes=["P0"], reason="restated")
    assert exc.value.reason == "amendment_one_sided"
    with pytest.raises(IncubationRefusal) as exc:
        armed.amend_rules("inc_0", CER, live_record=VIRGIN,
                          stop_rules=(_rule("S0", "stop"),),
                          supersedes=["S0"], reason="restated")
    assert exc.value.reason == "amendment_one_sided"


def test_an_amendment_without_a_reason_is_refused(armed):
    with pytest.raises(IncubationRefusal) as exc:
        armed.amend_rules("inc_0", CER, live_record=VIRGIN,
                          stop_rules=(_rule("S0", "stop"),),
                          promotion_rules=(_rule("P1", "promote"),),
                          supersedes=["P0"], reason="")
    assert exc.value.reason == "amendment_reason_missing"


def test_an_unknown_incubant_cannot_be_amended(reg):
    with pytest.raises(IncubationRefusal) as exc:
        reg.amend_rules("nope", CER, live_record=VIRGIN,
                        stop_rules=(_rule("S", "stop"),),
                        promotion_rules=(_rule("P", "promote"),), reason="x")
    assert exc.value.reason == "unknown_incubant"


@pytest.mark.parametrize("terminal", ["promote", "pull"])
def test_a_finished_lane_cannot_have_its_rules_rewritten(armed, terminal):
    """A promoted or stopped incubant's thresholds ARE the record of why it moved."""
    getattr(armed, terminal)("inc_0", CER)
    with pytest.raises(IncubationRefusal) as exc:
        armed.amend_rules("inc_0", CER, live_record=VIRGIN,
                          stop_rules=(_rule("S", "stop"),),
                          promotion_rules=(_rule("P", "promote"),), reason="x")
    assert exc.value.reason == "amendment_after_the_lane"


def test_an_amendment_still_validates_every_rule(armed):
    """`PreRegisteredRule` refuses a threshold with no basis; the amendment path must not be a
    way around that."""
    with pytest.raises(IncubationRefusal) as exc:
        PreRegisteredRule(rule_id="P1", what="x", class_="ECONOMIC", action="y",
                          threshold=1, basis="", pre_registered_utc="2026-07-31T00:00:00+00:00")
    assert exc.value.reason == "rule_incomplete"


def test_the_amendment_row_is_valid_json_on_one_line(armed, tmp_path):
    armed.amend_rules("inc_0", CER, live_record=VIRGIN,
                      stop_rules=(_rule("S0", "stop"),),
                      promotion_rules=(_rule("P1", "promote"),),
                      supersedes=["P0"], reason="restated")
    lines = [ln for ln in (tmp_path / "INC.jsonl").read_text().splitlines() if ln.strip()]
    assert len(lines) == 3
    for ln in lines:
        json.loads(ln)


def test_capacity_is_unchanged_by_an_amendment(armed):
    before = armed.capacity()
    armed.amend_rules("inc_0", CER, live_record=VIRGIN,
                      stop_rules=(_rule("S0", "stop"),),
                      promotion_rules=(_rule("P1", "promote"),),
                      supersedes=["P0"], reason="restated")
    assert armed.capacity() == before
