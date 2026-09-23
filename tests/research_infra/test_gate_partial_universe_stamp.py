"""The PARTIAL UNIVERSE stamp must name the refusal the cost layer actually gave.

WHY THIS TEST EXISTS
--------------------
`gate.py`'s `restrict_to_priced` branch used to assert *"Broker truth has no measured spread
for {syms}"* for every refusal, while the real reason sat in `SleeveCoverage.unpriced_reasons`
and was surfaced only on the below-floor branch. That sentence is what a reader repairs
against, and it cost a session a draft: AF §3.3's first version routed `NATGAS.cash` to a
spread capture on the strength of it. `NATGAS.cash`'s spread was already MEASURED; the
refusals were an unresolved broker symbol and `commission.kind = 'unknown'`.

So the property is: **the stamp quotes the layer, it does not guess.** A refusal about
commission must not read as a refusal about spread. Asserted behaviourally, on three
genuinely different refusal causes, rather than by grepping the source for a substring.
"""

from __future__ import annotations

import datetime as dt

import pytest

from src.costs.model import BrokerTrueCosts
from src.research_infra.walkforward import TradeRecord, run_gate
from src.research_infra.walkforward.family import FamilyMember, fidelity_scope
from src.research_infra.walkforward.options import OPTIONS

ENTRY0 = dt.datetime(2025, 1, 6, 12, 0, tzinfo=dt.timezone.utc)

# Wave-21 note: symbol identity now resolves ONLY through the live-profile
# symbol authority (membership in a truth artifact grants nothing), so the
# old synthetic GOOD/BAD/ABSENT names stopped exercising these branches --
# the whole sleeve became unpriceable before any refusal could be named.
# The fixtures now use real declared FTMO names with the SAME synthetic
# records: EURUSD (priceable: declared + slippage-sampled), GBPUSD (the refusal
# under test), and XAUUSD (declared in the authority but absent from the
# truth doc). The wave-21 slippage model prices only its reconciled sample
# set, so fixture symbols must come from it.

#: `gate.py`'s fidelity gate refuses any sleeve with no record, before cost coverage is ever
#: reached -- so a probe sleeve has to be registered exactly the way AF's own gate registers
#: its family cells. `energy_agri` is the real parent of the family this test was written for.
_MEMBER = FamilyMember(
    member="mxf_probe_good_h4", mechanism_key="probe", mechanism="h4_probe", parent_sleeve="energy_agri",
    symbol="EURUSD", broker_symbol="EURUSD", timeframe=16388, asset_class="energy",
    is_authored_cell=True, profile_supported=True)


def _instrument(*, commission: dict) -> dict:
    return {
        "broker_path": "Commodities\\X",
        "instrument_class": "energy",
        "commission": commission,
        "spec": {"trade_contract_size": 100.0, "swap_long": -1.0, "swap_short": -1.0,
                 "swap_mode": 1, "swap_rollover3days": 5, "point": 0.001},
        "spread_price": {"coverage": "MEASURED", "provenance": "p",
                         "percentiles": {"p50": 0.05}, "mid_price_median": 50.0},
        "swap": {"coverage": "MEASURED", "provenance": "p", "swap_long": -1.0,
                 "swap_short": -1.0, "swap_mode": 1, "swap_rollover3days_weekday": 5},
        "slippage": {"coverage": "MEASURED", "provenance": "p", "value_r": 0.01},
        "usd_per_price_unit_per_lot": 100.0,
    }


PRICEABLE = _instrument(commission={"kind": "per_lot", "value": 5.0, "coverage": "MEASURED",
                                    "provenance": "measured, n=3", "n_round_turns": 3})
UNKNOWN_COMMISSION = _instrument(
    commission={"kind": "unknown", "value": None, "coverage": "MODELLED",
                "owner": "o", "asof": "2026-07-27", "provenance": "no deal rows"})


def _truth(instruments: dict) -> BrokerTrueCosts:
    return BrokerTrueCosts({"version": "test",
                            "accounts": {"FTMO": {"server": "FTMO-Server3",
                                                  "instruments": instruments}}})


def _trades(sleeve: str, sym: str, n: int, *, start: dt.datetime, r_gross: float):
    """n trades on distinct days, so the daily panel has n observations."""
    out = []
    for i in range(n):
        e = start + dt.timedelta(days=3 * i)
        out.append(TradeRecord(
            sleeve=sleeve, symbol=sym, entry_utc=e, exit_utc=e + dt.timedelta(hours=8),
            direction=1, sl_distance_price=1.0, entry_price=50.0,
            r_gross=r_gross + 0.01 * (i % 5)))
    return out


def _run(instruments: dict, syms: tuple[str, ...], *, good: str, bad: str):
    """A one-sleeve run whose trades split across a priceable and an unpriceable symbol."""
    sleeve = "mxf_probe_good_h4"
    trades = (_trades(sleeve, good, 40, start=ENTRY0, r_gross=0.5)
              + _trades(sleeve, bad, 10, start=ENTRY0 + dt.timedelta(days=1), r_gross=0.5))
    spec = OPTIONS["C_exploratory"].with_(
        spec_id="stamp_probe", declared_family_size=1,
        sleeve_symbol_allowlist={sleeve: syms})
    with fidelity_scope([_MEMBER], pooled=False):
        res = run_gate({sleeve: trades}, spec, costs=_truth(instruments),
                       server="FTMO-Server3")
    return res.verdicts[sleeve]


def test_stamp_names_a_commission_refusal_as_a_commission_refusal():
    v = _run({"EURUSD": PRICEABLE, "GBPUSD": UNKNOWN_COMMISSION}, ("EURUSD", "GBPUSD"),
             good="EURUSD", bad="GBPUSD")
    ur = v.universe_restriction
    assert ur, "the run did not restrict; the fixture no longer exercises the branch"
    assert ur["dropped_symbols"] == ["GBPUSD"]
    joined = " ".join(ur["unpriced_reasons"])
    assert "commission" in joined.lower(), ur["unpriced_reasons"]
    assert "commission" in ur["stamp"].lower()
    # The regression: it must NOT claim a spread problem when spread is measured.
    assert "no measured spread" not in ur["stamp"]


def test_stamp_names_a_missing_instrument_as_a_missing_instrument():
    """The refusal `NATGAS_cash` actually hit: the symbol is not in the artifact at all,
    because the profile had no instrument contract to resolve it through."""
    v = _run({"EURUSD": PRICEABLE}, ("EURUSD", "XAUUSD"), good="EURUSD", bad="XAUUSD")
    ur = v.universe_restriction
    assert ur and ur["dropped_symbols"] == ["XAUUSD"]
    joined = " ".join(ur["unpriced_reasons"]).lower()
    assert "no broker truth" in joined, ur["unpriced_reasons"]
    assert "no broker truth" in ur["stamp"].lower()
    assert "no measured spread" not in ur["stamp"]


def test_stamp_names_a_genuine_spread_gap_too():
    """The counterpart: when the refusal IS about spread, the stamp still says so -- the fix
    is 'quote the layer', not 'stop mentioning spread'."""
    no_spread = _instrument(commission={"kind": "per_lot", "value": 5.0,
                                        "coverage": "MEASURED", "provenance": "p"})
    no_spread["spread_price"] = None
    v = _run({"EURUSD": PRICEABLE, "GBPUSD": no_spread}, ("EURUSD", "GBPUSD"), good="EURUSD", bad="GBPUSD")
    ur = v.universe_restriction
    assert ur and ur["dropped_symbols"] == ["GBPUSD"]
    assert "spread" in " ".join(ur["unpriced_reasons"]).lower()
    assert "spread" in ur["stamp"].lower()


def test_the_reasons_are_carried_on_the_gate_row_as_well_as_the_stamp():
    """A reader parsing the artifact should not have to regex the prose."""
    v = _run({"EURUSD": PRICEABLE, "GBPUSD": UNKNOWN_COMMISSION}, ("EURUSD", "GBPUSD"),
             good="EURUSD", bad="GBPUSD")
    row = v.gates["cost_coverage"]
    assert row["restricted"] is True
    assert row["unpriced_reasons"], row
    assert sum(row["unpriced_reasons"].values()) == 10


def test_a_fully_priced_sleeve_carries_no_restriction_and_no_stamp():
    sleeve = "mxf_probe_good_h4"
    trades = _trades(sleeve, "EURUSD", 50, start=ENTRY0, r_gross=0.5)
    spec = OPTIONS["C_exploratory"].with_(
        spec_id="stamp_probe_clean", declared_family_size=1,
        sleeve_symbol_allowlist={sleeve: ("EURUSD",)})
    with fidelity_scope([_MEMBER], pooled=False):
        res = run_gate({sleeve: trades}, spec, costs=_truth({"EURUSD": PRICEABLE}),
                       server="FTMO-Server3")
    v = res.verdicts[sleeve]
    assert v.gates["cost_coverage"]["pass"] is True
    assert not v.gates["cost_coverage"].get("restricted")
    assert v.universe_restriction in (None, {})
    assert not any("PARTIAL UNIVERSE" in r for r in v.reasons)


@pytest.mark.parametrize("policy", ["refuse"])
def test_the_below_floor_branch_still_reports_reasons(policy):
    """The branch that was already correct must stay correct."""
    sleeve = "mxf_probe_good_h4"
    trades = (_trades(sleeve, "EURUSD", 10, start=ENTRY0, r_gross=0.5)
              + _trades(sleeve, "GBPUSD", 40, start=ENTRY0 + dt.timedelta(days=1), r_gross=0.5))
    spec = OPTIONS["C_exploratory"].with_(
        spec_id="stamp_probe_refuse", declared_family_size=1, coverage_policy=policy,
        sleeve_symbol_allowlist={sleeve: ("EURUSD", "GBPUSD")})
    with fidelity_scope([_MEMBER], pooled=False):
        res = run_gate({sleeve: trades}, spec,
                       costs=_truth({"EURUSD": PRICEABLE, "GBPUSD": UNKNOWN_COMMISSION}),
                       server="FTMO-Server3")
    v = res.verdicts[sleeve]
    assert v.gates["cost_coverage"]["pass"] is False
    assert any("cost_coverage_below_floor" in r and "commission" in r.lower()
               for r in v.reasons), v.reasons
