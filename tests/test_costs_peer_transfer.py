"""The signed energy-class peer transfer, and the four ways it must refuse.

WHAT THIS PINS, AND WHY IT IS A SEPARATE FILE FROM `test_costs_layer.py`
------------------------------------------------------------------------
`OD-AI-8` asked for one sentence: a stated energy-class peer transfer someone is willing to
sign, so `NATGAS.cash` stops being unpriceable and `energy_agri`'s FVG mechanism -- the
strongest pooled mean in AF's 30-family grid, on a sleeve trading real money -- can be
measured on its whole three-symbol class instead of two thirds of it.

The danger in saying yes to that is not the number. It is that a signed transfer looks
exactly like a measurement once it is inside a JSON artifact, and six months later nobody can
tell which is which. So the kind is deliberately its own thing:

  * it can never resolve to `MEASURED` -- `_check_peer_transfer_coverage`, tested twice here,
    once on the arithmetic path and once on the `Measure` path;
  * it cannot exist without a signer, a date, named source instruments and a rationale;
  * it cannot chain, and it cannot resolve to `unknown` (which is a refusal, not a schedule);
  * and the signature travels into `detail` and into `Measure.transferred_from`, so a reader
    who has only the output can still see it was transferred and from what.

Every assertion below is a property of the layer, not of the two records `AP` signed --
`test_signed_artifact_is_wired` is the only one that reads the shipped artifact, and it
reads it for its provenance rather than for a value.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path

import pytest

from src.costs.coverage import Coverage
from src.costs.model import (
    PEER_TRANSFER,
    PEER_TRANSFER_REQUIRED,
    PEER_TRANSFER_RESOLVABLE,
    BrokerTrueCosts,
    CostTruthError,
    commission_usd_per_lot,
    cost_r,
)

REPO = Path(__file__).resolve().parents[1]
SIGNED = (REPO / "docs/audits/fable5-vision-audit-20260725/phase10/receipts"
          / "ENERGY_CLASS_PEER_TRANSFER_V1.json")
COSTS_V1_2 = (REPO / "research/operations/broker_truth_layer_2026_07_30"
              / "BROKER_TRUE_COSTS_V1_2.json")

ENTRY = dt.datetime(2025, 3, 11, 12, 0, tzinfo=dt.timezone.utc)


def _transfer(**over) -> dict:
    t = {
        "resolved_kind": "per_lot",
        "value": 5.0,
        "from_account": "redacted_account",
        "from_symbols": ["UKOUSD", "USOUSD"],
        "from_coverage": "MEASURED",
        "authorized_by": "borhen (2026-07-30)",
        "rationale": "same instrument class, same schedule shape",
        "signed_utc": "2026-07-30T00:00:00Z",
    }
    t.update(over)
    return t


def _block(**over) -> dict:
    b = {
        "kind": PEER_TRANSFER,
        "coverage": "TRANSFERRED",
        "unit": "USD/lot round turn",
        "value": 5.0,
        "transferred_from": "redacted_account energy class (UKOUSD, USOUSD)",
        "provenance": "signed energy-class peer transfer",
        "transfer": _transfer(),
    }
    b.update(over)
    return b


def _rec(commission: dict | None = None) -> dict:
    """A minimal instrument record: only what the commission arithmetic reads."""
    return {
        "broker_path": "Commodities\\UKOIL.cash",
        "instrument_class": "energy",
        "commission": commission if commission is not None else _block(),
        "spec": {"trade_contract_size": 1000.0, "swap_long": -1.3, "swap_short": 0.23,
                 "swap_mode": 1, "swap_rollover3days": 5, "point": 0.001},
        "spread_price": {"coverage": "MEASURED", "provenance": "p",
                         "percentiles": {"p50": 0.06}, "mid_price_median": 3.16},
        "swap": {"coverage": "MEASURED", "provenance": "p", "swap_long": -1.3,
                 "swap_short": 0.23, "swap_mode": 1, "swap_rollover3days_weekday": 5},
        "slippage": {"coverage": "TRANSFERRED", "provenance": "p",
                     "transferred_from": "pooled W7 entry slippage, n=140",
                     "value_r": 0.0132},
        "usd_per_price_unit_per_lot": 1000.0,
    }


def _truth(rec: dict) -> BrokerTrueCosts:
    return BrokerTrueCosts({
        "version": "test",
        "accounts": {"FTMO": {"server": "FTMO-Server3", "instruments": {"UKOIL.cash": rec}}},
    })


class _InlineSlippage:
    """Component-isolation double (wave-21 routes slippage through the artifact
    model; this file tests the commission peer-transfer semantics, not slippage)."""

    def estimate(self, account: str, symbol: str):
        from src.costs.slippage_model import SlippageEstimate

        return SlippageEstimate(
            account=account,
            canonical_symbol=symbol,
            expected_adverse_price=0.0,
            coverage=Coverage.MEASURED,
            n=1,
            provenance="peer-transfer component-isolation double",
            detail={},
        )


def _price(rec: dict):
    return cost_r("UKOIL.cash", "FTMO", 24.0, sl_distance_price=0.10, entry_price=3.16,
                  entry_utc=ENTRY, side="LONG", costs=_truth(rec),
                  slippage_model=_InlineSlippage())


# --------------------------------------------------------------- the happy path


def test_peer_transfer_resolves_through_the_shared_arithmetic():
    """$5.00/lot over a 0.10 stop at 1000 USD/price-unit is 0.05 R -- the same formula
    `per_lot` uses, not a second copy of it."""
    usd, detail = commission_usd_per_lot(_rec(), entry_price=3.16)
    assert usd == pytest.approx(5.0)
    assert detail["kind"] == PEER_TRANSFER
    assert detail["resolved_kind"] == "per_lot"
    assert set(PEER_TRANSFER_REQUIRED) <= set(detail["peer_transfer"])
    assert detail["peer_transfer"]["emitted_coverage"] == "TRANSFERRED"


def test_notional_bp_resolution_uses_contract_size_and_price():
    """A transfer may resolve to `notional_bp`, and then it must go through the notional
    formula rather than being read as USD/lot. 6.5 bp x 1000 x 3.16 = 2.054."""
    rec = _rec(_block(transfer=_transfer(resolved_kind="notional_bp", value=6.5)))
    usd, detail = commission_usd_per_lot(rec, entry_price=3.16)
    assert usd == pytest.approx(6.5 / 1e4 * 1000.0 * 3.16)
    assert detail["resolved_kind"] == "notional_bp"


def test_the_signature_survives_into_the_measure_and_the_coverage_is_transferred():
    b = _price(_rec())
    assert b.commission_r.coverage is Coverage.TRANSFERRED
    assert b.commission_r.value == pytest.approx(0.05)
    assert "UKOUSD" in b.commission_r.transferred_from
    # The narrowed class band, not the default x0.5/x2 -- and it must say why.
    assert (b.commission_r.band_low, b.commission_r.band_high) == pytest.approx((0.0475, 0.0525))
    assert b.commission_r.band_provenance
    # And the total inherits the weakest term, so nothing built on it can read MEASURED.
    assert b.total_r.coverage is not Coverage.MEASURED
    sig = b.detail["commission"]["peer_transfer"]
    assert sig["authorized_by"] and sig["signed_utc"] and sig["rationale"]


# ------------------------------------------------------------- the refusals


def test_a_transfer_claiming_measured_is_refused():
    """The laundering guard. A transfer recorded as MEASURED is indistinguishable from an
    observation, which is the one thing the coverage system must never allow."""
    with pytest.raises(CostTruthError, match="must declare coverage TRANSFERRED"):
        commission_usd_per_lot(_rec(_block(coverage="MEASURED")), entry_price=3.16)


def test_a_transfer_claiming_measured_is_refused_on_the_measure_path_too():
    """Belt and braces: the guard fires from the full `cost_r` path as well, so a block that
    somehow reached construction without the arithmetic still cannot mint MEASURED."""
    rec = _rec(_block(coverage="MEASURED"))
    with pytest.raises(CostTruthError, match="must declare coverage TRANSFERRED"):
        _price(rec)


# ------------------------------------- coverage cannot be UPGRADED across the transfer
# Every test below exists because an adversarial pass over AP's own first version found the
# hole: `from_coverage` was presence-checked and never became a `Coverage`, so a transfer from
# a MODELLED peer emitted TRANSFERRED -- strength 2 -> 1, an upgrade -- and `from_coverage:
# "VIBES"` priced.


@pytest.mark.parametrize("src,emitted", [
    ("MEASURED", Coverage.TRANSFERRED),
    ("TRANSFERRED", Coverage.TRANSFERRED),
    ("MODELLED", Coverage.MODELLED),
])
def test_the_emitted_coverage_is_the_weakest_of_transferred_and_the_source(src, emitted):
    rec = _rec(_block(transfer=_transfer(from_coverage=src)))
    _, detail = commission_usd_per_lot(rec, entry_price=3.16)
    assert detail["peer_transfer"]["emitted_coverage"] == emitted.value
    assert _price(rec).commission_r.coverage is emitted


def test_a_transfer_from_a_modelled_peer_never_reads_stronger_than_its_source():
    """The upgrade, stated as the property it violates: `weakest()`'s 'class travels into every
    result computed from it'. TRANSFERRED is strength 1 and MODELLED is 2."""
    b = _price(_rec(_block(transfer=_transfer(from_coverage="MODELLED"))))
    assert b.commission_r.coverage is Coverage.MODELLED
    assert b.commission_r.coverage.strength >= Coverage.MODELLED.strength
    # And a MODELLED Measure cannot exist without owner+asof; the signature supplies both.
    assert b.commission_r.owner and b.commission_r.asof
    assert b.total_r.coverage is Coverage.MODELLED


@pytest.mark.parametrize("bad", ["VIBES", "measured-ish", "OK", "1", "  "])
def test_an_unparseable_from_coverage_is_refused_not_defaulted(bad):
    with pytest.raises(CostTruthError):
        commission_usd_per_lot(_rec(_block(transfer=_transfer(from_coverage=bad))),
                               entry_price=3.16)


def test_from_coverage_is_case_and_whitespace_tolerant_but_nothing_else():
    _, detail = commission_usd_per_lot(
        _rec(_block(transfer=_transfer(from_coverage="  measured "))), entry_price=3.16)
    assert detail["peer_transfer"]["emitted_coverage"] == "TRANSFERRED"


# --------------------- the kind is a COMMISSION construct and nothing else
# Second hole the same pass found: `_resolve_peer_transfer` was reachable only from
# `commission_usd_per_lot`, so a `kind: "peer_transfer"` block in the spread, swap or slippage
# slot carried NONE of the eight required fields and priced end to end.


@pytest.mark.parametrize("slot", ["spread_price", "swap"])
def test_peer_transfer_is_refused_in_every_non_commission_slot(slot):
    rec = _rec()
    rec[slot] = {**rec[slot], "kind": PEER_TRANSFER, "coverage": "TRANSFERRED",
                 "transferred_from": "whoever"}
    with pytest.raises(CostTruthError, match="valid in the `commission` slot only"):
        _price(rec)


@pytest.mark.parametrize("slot", ["spread_price", "swap"])
def test_an_unsigned_peer_transfer_in_another_slot_cannot_price_either(slot):
    """The exact shape the refuter priced: the kind, no signature at all."""
    rec = _rec()
    rec[slot] = {**rec[slot], "kind": PEER_TRANSFER, "coverage": "TRANSFERRED",
                 "transferred_from": "whoever", "provenance": "trust me"}
    with pytest.raises(CostTruthError):
        _price(rec)


def test_a_peer_transfer_in_the_slippage_slot_is_structurally_inert():
    """Wave-21 successor of the slippage-slot refusal: slippage now resolves ONLY
    through the artifact-bound SlippageModel, so the record's slippage slot is never
    read. A peer-transfer block planted there cannot price, cannot alter the
    breakdown, and cannot leak its coverage -- stronger than the old refusal, which
    only guaranteed a message. Poisoned and clean records must price identically."""
    clean = _price(_rec())
    rec = _rec()
    rec["slippage"] = {"kind": PEER_TRANSFER, "coverage": "TRANSFERRED",
                      "transferred_from": "whoever", "provenance": "trust me"}
    poisoned = _price(rec)
    assert poisoned.slippage_r.value == clean.slippage_r.value == 0.0
    assert poisoned.slippage_r.coverage is Coverage.MEASURED
    assert "peer-transfer component-isolation double" in poisoned.slippage_r.provenance
    assert poisoned.total_r.value == pytest.approx(clean.total_r.value)
    assert poisoned.commission_r.value == pytest.approx(clean.commission_r.value)


@pytest.mark.parametrize("field", PEER_TRANSFER_REQUIRED)
def test_every_required_signature_field_is_required(field):
    t = _transfer()
    t.pop(field)
    with pytest.raises(CostTruthError, match="missing"):
        commission_usd_per_lot(_rec(_block(transfer=t)), entry_price=3.16)


@pytest.mark.parametrize("field", [f for f in PEER_TRANSFER_REQUIRED
                                   if f not in ("value", "from_symbols")])
def test_a_blank_signature_field_is_not_a_signature(field):
    with pytest.raises(CostTruthError, match="missing"):
        commission_usd_per_lot(_rec(_block(transfer=_transfer(**{field: "   "}))),
                               entry_price=3.16)


@pytest.mark.parametrize("syms", [[], "UKOUSD", [""], None, ["UKOUSD", 7]])
def test_from_symbols_must_name_instruments(syms):
    with pytest.raises(CostTruthError):
        commission_usd_per_lot(_rec(_block(transfer=_transfer(from_symbols=syms))),
                               entry_price=3.16)


@pytest.mark.parametrize("kind", ["unknown", PEER_TRANSFER, "per_share", ""])
def test_a_transfer_cannot_resolve_to_a_refusal_or_to_itself(kind):
    assert kind not in PEER_TRANSFER_RESOLVABLE
    with pytest.raises(CostTruthError):
        commission_usd_per_lot(_rec(_block(transfer=_transfer(resolved_kind=kind))),
                               entry_price=3.16)


def test_a_transfer_with_no_transfer_block_is_refused():
    b = _block()
    b.pop("transfer")
    with pytest.raises(CostTruthError, match="needs a `transfer` block"):
        commission_usd_per_lot(_rec(b), entry_price=3.16)


def test_an_unnamed_transferred_source_is_refused_not_defaulted():
    """The hole AP closed. `_measure_from` used to substitute "unnamed class peer" for a
    missing `transferred_from`, which is `Measure.__post_init__`'s own refusal reopened one
    layer up. 353 of 353 TRANSFERRED blocks in both shipped artifacts name a source, so
    nothing depended on the default."""
    b = _block()
    b.pop("transferred_from")
    with pytest.raises(CostTruthError, match="must name `transferred_from`"):
        _price(_rec(b))


def test_unknown_is_still_refused_and_says_f38():
    """The behaviour OD-AI-8 exists because of, unchanged: adding a signed kind must not
    soften the refusal for an unsigned one."""
    with pytest.raises(CostTruthError, match="UNKNOWN, not zero"):
        commission_usd_per_lot(
            _rec({"kind": "unknown", "value": None, "coverage": "MODELLED",
                  "owner": "x", "asof": "y", "provenance": "p"}), entry_price=3.16)


# --------------------------------------------------- the artifact that was signed


@pytest.mark.skipif(not SIGNED.is_file(), reason="signature artifact absent from this tree")
def test_signed_artifact_is_wired():
    """The two records AP signed are readable, self-describing, and priceable -- and the
    source they name is MEASURED on the account they name."""
    doc = json.loads(SIGNED.read_text())
    assert doc["authorized_by"].startswith("borhen")
    assert doc["kind"] == PEER_TRANSFER
    assert doc["instruments"], "a signature that signs nothing"
    for sym, block in doc["instruments"].items():
        assert block["kind"] == PEER_TRANSFER, sym
        assert block["coverage"] == "TRANSFERRED", sym
        t = block["transfer"]
        assert not [k for k in PEER_TRANSFER_REQUIRED if not t.get(k)], sym
        assert t["resolved_kind"] in PEER_TRANSFER_RESOLVABLE, sym


@pytest.mark.skipif(not COSTS_V1_2.is_file(), reason="V1_2 absent from this tree")
def test_v1_2_prices_natgas_and_leaves_v1_1_alone():
    """The point of writing V1_2 beside V1_1: the signed records price, and nothing else in
    the artifact moved. The second half is asserted by the generator's own manifest, which
    this reads rather than recomputes."""
    from src.costs.model import load_broker_true_costs

    costs = load_broker_true_costs(COSTS_V1_2)
    b = cost_r("NATGAS.cash", "FTMO", 24.0, sl_distance_price=0.10, entry_price=3.16,
               entry_utc=ENTRY, side="LONG", spread_band="mid", costs=costs)
    assert b.commission_r.coverage is Coverage.TRANSFERRED
    assert b.commission_r.value > 0
    doc = json.loads(COSTS_V1_2.read_text())
    prov = doc["derived_from"]
    assert prov["base"].endswith("BROKER_TRUE_COSTS_V1_1.json")
    assert prov["records_changed"] == sorted(prov["records_changed"])
    assert prov["records_unchanged_verified"] is True


def test_v1_1_itself_still_refuses_natgas():
    """The control that makes the whole exercise honest: the base artifact is untouched, so
    every published AF number still reproduces against it."""
    from src.costs.model import load_broker_true_costs

    v11 = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
    if not v11.is_file():  # sparse-checkout can hide it; the claim is about V1_1, not the tree
        pytest.skip("V1_1 absent from this tree (sparse checkout)")
    # Wave-21 tightened symbol identity: authority membership is checked before the
    # record's own unknown-kind refusal, so V1_1's natgas now refuses one gate
    # earlier ("not in that broker's quotable universe ... unpriced, not free")
    # instead of reaching the F38 "UNKNOWN, not zero" text. Still a refusal;
    # still not a price.
    with pytest.raises(CostTruthError, match="unpriced, not free"):
        cost_r("NATGAS.cash", "FTMO", 24.0, sl_distance_price=0.10, entry_price=3.16,
               entry_utc=ENTRY, side="LONG", spread_band="mid",
               costs=load_broker_true_costs(v11))


def test_deep_copy_of_a_signed_block_does_not_mutate_the_source_record():
    """`commission_usd_per_lot` recurses with a synthetic record; it must not write the
    resolved kind back into the artifact's own dict, or the second read of the same
    instrument would see `per_lot` and lose the signature."""
    rec = _rec()
    before = copy.deepcopy(rec["commission"])
    commission_usd_per_lot(rec, entry_price=3.16)
    assert rec["commission"] == before
