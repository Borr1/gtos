"""The fidelity register must agree with the measurement it claims to transcribe.

Session K's register was hand-transcribed from a prose table, and two of its twelve rows
carried the wrong structural class as a result. This binds the numbers to the machine-
readable receipt instead, so a future edit to either side shows up as a failure rather than
as a quietly wrong ceiling on a sleeve that is about to be judged.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from src.research_infra.walkforward.fidelity import (
    _CLASS_TOTALS,
    _MEASURED,
    FidelityBasis,
    FidelityClass,
)

RECEIPT = pathlib.Path(
    "docs/audits/fable5-vision-audit-20260725/phase5/receipts/Y_K1B_LINEAGE.json")

#: The arms the receipt must contain, in order.
MAINLINE, DEPLOYED = "mainline", "vps_redacted_host"


@pytest.fixture(scope="module")
def arms():
    if not RECEIPT.is_file():
        pytest.skip(f"{RECEIPT} absent (sparse checkout?)")
    doc = json.loads(RECEIPT.read_text())
    return {a["lineage"]: a for a in doc["arms"]}, doc


def test_receipt_carries_both_arms_over_the_same_cycles(arms):
    by_lineage, _ = arms
    assert set(by_lineage) == {MAINLINE, DEPLOYED}
    assert by_lineage[MAINLINE]["cycles"] == by_lineage[DEPLOYED]["cycles"] == 2640
    # live's own counter is a property of the record, not of the port
    assert by_lineage[MAINLINE]["counter_total"] == by_lineage[DEPLOYED]["counter_total"] == 706


def test_the_mainline_arm_reproduces_K1s_published_numbers(arms):
    """K1_GATE_RECEIPT.md sections 3.1-3.2, rebuilt from the sealed packet export rather
    than from the wave-3 scratchpad it was originally computed in (which no longer exists)."""
    a = arms[0][MAINLINE]
    assert (a["count_agree"], a["count_total"]) == (2282, 2640)
    assert round(a["count_pct"], 2) == 86.44
    assert (a["over"], a["over_sum"]) == (160, 201)
    assert (a["under"], a["under_sum"]) == (198, 265)
    assert (a["live_named"], a["port"]) == (383, 585)
    assert (a["agreed"], a["live_only"], a["port_only"]) == (200, 182, 385)


def test_the_lineage_switch_recovers_every_first_of_day_intent(arms):
    _, doc = arms
    cross = doc["cross"]
    assert (cross["a"], cross["b"]) == (MAINLINE, DEPLOYED)
    assert cross["live_only_a"] == 182 and cross["live_only_b"] == 7
    assert len(cross["recovered_by_b"]) == 175
    assert cross["newly_missed_by_b"] == []
    assert cross["recovered_by_sleeve"] == {
        "asia_pdl_fade": 81, "asian_fade": 38, "metal_session_reversion": 22,
        "orb_crypto_london": 13, "ny_crypto_momentum": 11,
        "liq_asia_up_low_metal": 5, "kz_london_crypto_low": 5,
    }


def test_the_residual_is_confined_to_two_lineage_invariant_sleeves(arms):
    """The 7 that remain are `idxrev` and `mx_avausd_*`, whose source is IDENTICAL across
    the two lineages — so they are genuine port-vs-live differences, not clock artefacts."""
    _, doc = arms
    still = {s for s, *_ in doc["cross"]["still_missed"]}
    assert still == {"idxrev", "mx_avausd_d1_donchian_20_breakout"}
    assert doc["cross"]["still_missed_by_sleeve"] == {
        "idxrev": 5, "mx_avausd_d1_donchian_20_breakout": 2}


#: Source identical across the two lineages, so the shim does not touch them. Their
#: agreeing across the arms is close to TAUTOLOGICAL — a refuter said so and was right; it
#: proves determinism and that no state leaks between arms, not specificity.
_SOURCE_IDENTICAL = {
    "idxrev", "vol_compression",
    "mx_nzdjpy_d1_donchian_20_breakout", "mx_avausd_d1_donchian_20_breakout",
    "mx_btcusd_d1_donchian_20_breakout", "mx_cadjpy_d1_volume_surge_reversal",
    "mx_ethusd_d1_donchian_20_breakout",
}

#: Source DIFFERS across the lineages — `fx_jpy._to_server_local` swapped the EU DST
#: calendar for the measured US one — and the shim DOES swap them. They agree across the
#: arms because the difference is inert inside this window: both calendars read +3 for the
#: whole of 2026-06-18..07-24. That is a falsifiable prediction, and it is the real
#: specificity control.
_SHIMMED_BUT_INERT_IN_WINDOW = {"fx_jpy", "fx_jpy_ny"}


def test_source_identical_sleeves_agree_across_the_arms(arms):
    """Determinism and no cross-arm state leakage. Near-tautological on its own."""
    by_lineage, _ = arms
    a, b = by_lineage[MAINLINE]["per_sleeve"], by_lineage[DEPLOYED]["per_sleeve"]
    assert _SOURCE_IDENTICAL <= set(a) and _SOURCE_IDENTICAL <= set(b)
    for name in sorted(_SOURCE_IDENTICAL):
        assert a[name] == b[name], f"{name} moved under a shim that does not touch it"


def test_a_shimmed_sleeve_whose_change_is_inert_in_window_does_not_move(arms):
    """The specificity control that is NOT tautological: these two ARE swapped by the shim,
    and they still agree — because the EU/US DST calendars coincide across the whole K1-b
    window. A shim that perturbed more than the clock would break this."""
    by_lineage, doc = arms
    a, b = by_lineage[MAINLINE]["per_sleeve"], by_lineage[DEPLOYED]["per_sleeve"]
    assert _SHIMMED_BUT_INERT_IN_WINDOW <= set(by_lineage[DEPLOYED]["swapped"]) | {"fx_jpy_ny"}
    assert "fx_jpy" in by_lineage[DEPLOYED]["swapped"]
    for name in sorted(_SHIMMED_BUT_INERT_IN_WINDOW):
        assert a[name] == b[name], f"{name} moved on a calendar difference that is inert here"


def test_every_other_sleeve_that_was_shimmed_did_move(arms):
    by_lineage, _ = arms
    a, b = by_lineage[MAINLINE]["per_sleeve"], by_lineage[DEPLOYED]["per_sleeve"]
    exempt = _SOURCE_IDENTICAL | _SHIMMED_BUT_INERT_IN_WINDOW | {
        # produced no LIVE intent on either arm, so there is nothing to move
        "vss_fxcross_london_up_low",
    }
    moved = [n for n in sorted(set(a) | set(b)) if n not in exempt]
    assert moved, "the partition exempted everything; the control has stopped testing"
    for name in moved:
        assert a.get(name) != b.get(name), f"{name} is registered as shifted but did not move"


@pytest.mark.parametrize("sleeve", sorted(_MEASURED))
def test_every_measured_row_matches_the_arm_it_claims(arms, sleeve):
    by_lineage, _ = arms
    cls, basis, agreed, live_only, k1, port_only = _MEASURED[sleeve]
    arm = DEPLOYED if basis is FidelityBasis.MEASURED_LINEAGE_MATCHED else MAINLINE
    row = by_lineage[arm]["per_sleeve"][sleeve]
    assert (row["agreed"], row["live_only"], row["port_only"]) == (agreed, live_only, port_only)
    if k1 is not None:
        m = by_lineage[MAINLINE]["per_sleeve"][sleeve]
        assert (m["agreed"], m["live_only"]) == k1


def test_precision_is_carried_and_is_a_lower_bound(arms):
    """`live_recall` alone was the headline until a refuter pointed out it has no precision
    term. Both now travel in the stamp, with the reason precision is uninterpretable at
    identity level: `fx_jpy` has the BEST recall in K's table and the WORST precision here,
    and its source is identical in both lineages — nothing about it degraded, live stopped
    naming."""
    from src.research_infra.walkforward.fidelity import fidelity_for
    fx = fidelity_for("fx_jpy")
    assert fx.live_recall == 1.0
    assert fx.precision is not None and fx.precision < 0.40
    stamp = fidelity_for("asia_pdl_fade").ceiling_stamp(0.50)
    assert "identity precision" in stamp and "LOWER BOUND" in stamp
    assert "SCOPE:" in stamp and "38 summer days" in stamp


def test_class_totals_are_the_sum_of_their_members(arms):
    by_lineage, _ = arms
    for cls, (agreed, live_only) in _CLASS_TOTALS.items():
        members = [(s, row[1]) for s, row in _MEASURED.items() if row[0] is cls]
        got_a = got_l = 0
        for name, basis in members:
            arm = DEPLOYED if basis is FidelityBasis.MEASURED_LINEAGE_MATCHED else MAINLINE
            row = by_lineage[arm]["per_sleeve"][name]
            got_a += row["agreed"]
            got_l += row["live_only"]
        if cls is FidelityClass.PER_BAR:
            # K's per-bar class total also carries the four one-intent mx_* sleeves that
            # are TRANSFERRED rather than listed in _MEASURED.
            extra = ["mx_avausd_d1_donchian_20_breakout", "mx_btcusd_d1_donchian_20_breakout",
                     "mx_cadjpy_d1_volume_surge_reversal", "mx_ethusd_d1_donchian_20_breakout"]
            for name in extra:
                row = by_lineage[MAINLINE]["per_sleeve"][name]
                got_a += row["agreed"]
                got_l += row["live_only"]
        assert (got_a, got_l) == (agreed, live_only), f"{cls.value} totals drifted"
