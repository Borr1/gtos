"""Session BD (B2063-B2072) -- OD-P2: the unit join key, by member agreement, never by a guess.

WHAT WAS FILED. Session P, `PACKET_EMITTER_CARRY.md` §3 and OD-P2: `single_member =
admission_members[0] if len(admission_members) == 1 else {}` (`book_owner.py:1506`) leaves the
join key null on every multi-member unit. `ultimate_book_intent_id` hashes seven fields; nulling
four collapsed 440 rows onto 65 ids. P's recommendation: *"yes, but as its own scoped change with
its own A/B"*, and *"the correct repair is to emit the members, not to guess a representative."*

THE TRAP P NAMED AND DID NOT SPRING. `_first_unit_sleeve` would attribute a whole unit to
`sleeve_members[0]`. It is inert only because `SizedUnit.sleeve_members` is a tuple and the guard
tests `isinstance(members, list)`; a JSON round-trip makes it a list and arms it. Widening that
`isinstance` is the obvious "fix" and it is the defect.

MEASURED, over the 99,112-packet live export, by replaying the real member rosters through the
production function (not a fixture):

    unit rows                : 985   (405 single-member, 277 multi-member, 303 with no roster)
    fields newly filled      : sleeve 276 | decision_bar_iso 277 | decision_day 277
                               timeframe 277 | direction 225 | symbol 0
    representative-guess     : fires on 277 rows, WRONG on 1

Two numbers there correct the framing the repair was filed under. P expected multi-sleeve units to
be the common case; exactly **1 of 277** multi-member units spans two sleeves. The common
multi-member unit is one sleeve on several symbols -- which is why `symbol` disagrees on all 277
and the agreement rule declines to emit it on every one. So the field the trap would corrupt is
the field the rule recovers almost completely, and the field that genuinely cannot be resolved is
refused by the same test. The trap's blast radius in THIS corpus is 1 row; that is not a bound on
tomorrow's, since it scales with sleeve count per cluster and the registry resolves 32.
"""
from __future__ import annotations

import dataclasses

from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.runtime_learning_packet import (
    _first_unit_sleeve,
    build_runtime_learning_packet,
)

_join = UltimateBookOwner._runtime_learning_unit_join_fields


def _m(sleeve, symbol, direction="LONG", day="2026-07-30", tf="H4"):
    return {
        "sleeve": sleeve,
        "symbol": symbol,
        "direction": direction,
        "decision_day": day,
        "decision_bar_iso": f"{day}T12:00:00+00:00",
        "timeframe": tf,
    }


# --------------------------------------------------------------------------------------------
# 1. The measured common case: one sleeve, several symbols
# --------------------------------------------------------------------------------------------


def test_one_sleeve_on_several_symbols_recovers_the_sleeve_and_refuses_the_symbol():
    """277 of 277 multi-member units in the live corpus have exactly this shape."""
    out = _join({}, [_m("metals_core", "XAUUSD"), _m("metals_core", "XAGUSD")])
    assert out["sleeve"] == "metals_core"
    assert out["direction"] == "LONG"
    assert out["decision_day"] == "2026-07-30"
    assert out["timeframe"] == "H4"
    assert "symbol" not in out, "a unit spanning two symbols has no single symbol"
    assert out["admission_unit_disagreed_fields"] == ["symbol"]
    assert out["admission_unit_join_status"] == "members_partially_agree"


def test_a_genuinely_mixed_sleeve_unit_gets_no_sleeve_at_all():
    """The 1-in-277 case. The representative-guess books this to `metals_core`; the rule refuses."""
    members = [_m("metals_core", "XAUUSD"), _m("metals_softband", "XAUUSD", direction="SHORT")]
    out = _join({}, members)
    assert "sleeve" not in out
    assert "direction" not in out
    assert set(out["admission_unit_disagreed_fields"]) == {"sleeve", "direction"}
    # ...and the roster is published, so a per-sleeve rollup can explode it honestly.
    assert out["admission_unit_sleeves"] == ["metals_core", "metals_softband"]


def test_the_roster_is_what_replaces_the_guess():
    out = _join({}, [_m("crypto", "BTCUSD"), _m("crypto", "ETHUSD"), _m("crypto", "SOLUSD")])
    assert out["admission_unit_sleeves"] == ["crypto"]
    assert out["sleeve"] == "crypto"


# --------------------------------------------------------------------------------------------
# 2. The booby trap, pinned so a future session neither trips over it nor "fixes" it
# --------------------------------------------------------------------------------------------


def test_the_representative_fallback_is_still_inert_on_a_tuple():
    """`_first_unit_sleeve`'s inertness is accidental. This test makes it observed."""
    assert _first_unit_sleeve({"sleeve_members": ("metals_core", "metals_softband")}) is None
    # ...and a JSON round-trip is what arms it. This is the one line of the trap.
    assert _first_unit_sleeve({"sleeve_members": ["metals_core", "metals_softband"]}) == "metals_core"


def test_the_repair_does_not_depend_on_the_trap_being_inert():
    """Feed the join rule a JSON-round-tripped unit -- the shape that arms `_first_unit_sleeve`.

    The agreement rule reads `admission_unit_members`, not `sleeve_members`, so its answer is the
    same either way. That independence is the point: the repair must not be one refactor away
    from booking a mixed unit to its alphabetically-first sleeve.
    """
    members = [_m("metals_core", "XAUUSD"), _m("metals_softband", "XAUUSD", direction="SHORT")]
    assert "sleeve" not in _join({}, members)
    assert "sleeve" not in _join({}, [dict(m) for m in members])


def test_sized_unit_sleeve_members_is_still_a_tuple():
    """If this ever becomes a list, `_first_unit_sleeve` arms itself and the trap is live."""
    from src.components.ultimate_book.admission import SizedUnit

    field = {f.name: f for f in dataclasses.fields(SizedUnit)}.get("sleeve_members")
    assert field is not None
    assert "tuple" in str(field.type).lower(), (
        f"SizedUnit.sleeve_members is now {field.type!r}; _first_unit_sleeve is no longer inert"
    )


# --------------------------------------------------------------------------------------------
# 3. Agreement fills gaps, never overwrites
# --------------------------------------------------------------------------------------------


def test_a_value_the_unit_already_resolved_is_never_overwritten():
    out = _join({"sleeve": "already_known"}, [_m("crypto", "BTCUSD"), _m("crypto", "ETHUSD")])
    assert "sleeve" not in out, "agreement must fill gaps, not relabel a resolved field"


def test_single_member_and_no_member_units_are_labelled_and_left_alone():
    assert _join({}, [_m("crypto", "BTCUSD")]) == {"admission_unit_join_status": "single_member"}
    assert _join({}, []) == {"admission_unit_join_status": "no_members"}
    assert _join({}, None) == {"admission_unit_join_status": "no_members"}


def test_a_field_absent_from_every_member_is_not_invented():
    members = [
        {"sleeve": "crypto", "symbol": "BTCUSD"},
        {"sleeve": "crypto", "symbol": "ETHUSD"},
    ]
    out = _join({}, members)
    assert "direction" not in out
    assert "timeframe" not in out
    assert "direction" not in out["admission_unit_agreed_fields"]
    assert "direction" not in out["admission_unit_disagreed_fields"]


def test_non_dict_members_do_not_raise():
    out = _join({}, [_m("crypto", "BTCUSD"), "not-a-dict", None])
    assert out["admission_unit_join_status"] == "single_member"


# --------------------------------------------------------------------------------------------
# 4. The status word cannot say the opposite of the truth
# --------------------------------------------------------------------------------------------


def test_partial_agreement_is_not_reported_as_disagreement():
    """A unit whose sleeve agrees and whose symbol does not is the MAJORITY case in the corpus.

    Reporting it as `members_disagree` would tell a reader the attribution is untrustworthy on
    277 of 277 rows where the sleeve is in fact clean on 276.
    """
    out = _join({}, [_m("metals_core", "XAUUSD"), _m("metals_core", "XAGUSD")])
    assert out["admission_unit_join_status"] == "members_partially_agree"
    assert "sleeve" in out["admission_unit_agreed_fields"]


def test_total_disagreement_is_reported_as_disagreement():
    members = [
        {"sleeve": "a", "symbol": "X", "direction": "LONG"},
        {"sleeve": "b", "symbol": "Y", "direction": "SHORT"},
    ]
    out = _join({}, members)
    assert out["admission_unit_join_status"] == "members_disagree"
    assert out["admission_unit_agreed_fields"] == []


def test_full_agreement_is_reported_as_agreement():
    out = _join({}, [_m("crypto", "BTCUSD"), _m("crypto", "BTCUSD")])
    assert out["admission_unit_join_status"] == "members_agree"
    assert out["admission_unit_disagreed_fields"] == []


# --------------------------------------------------------------------------------------------
# 5. The point of the whole repair: distinct ids
# --------------------------------------------------------------------------------------------


def test_recovering_the_sleeve_un_collapses_the_intent_id():
    """440 rows onto 65 ids was the symptom. Two units differing only by sleeve must differ by id."""
    def _packet(members):
        outcome = {"placement_status": "admitted", "admission_unit_members": members}
        outcome.update(_join(outcome, members))
        return build_runtime_learning_packet(
            namespace="operator_profile", event_type="unit_admitted", outcome=outcome,
        )

    a = _packet([_m("crypto", "BTCUSD"), _m("crypto", "ETHUSD")])
    b = _packet([_m("energy_agri", "BTCUSD"), _m("energy_agri", "ETHUSD")])
    assert a["sleeve"] == "crypto" and b["sleeve"] == "energy_agri"
    assert a["ultimate_book_intent_id"] != b["ultimate_book_intent_id"]
