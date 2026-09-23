"""The two unprotected sizing surfaces: profile overlays and account currency.

Why this file exists
--------------------
`SECOND_AUDIT.md` §3.5 records that sizing is otherwise genuinely well tested —
`tests/test_limit_order_flow.py:1357-1434` carries hand-computed lot volumes
through both the broker-geometry and tick-value branches — and names exactly two
gaps: **profile-overlay multipliers** and **account-currency conversion**.

Those two gaps matter because live position size is a product of two things
that disagree independently:

1. **The profile overlay.** Replay sizes from `config/profiles/ftmo.yaml`
   (`agent_config.yaml:3160`); live sizes from `config/profiles/redacted_account.yaml`.
2. **The broker's own contract spec.** Measured on the 2026-07-25 server export
   (`VPS_EXPORT_FINDINGS.md` V4): of the 19 instruments in the comparison, 18 are
   present at both brokers and **all 18 differ**.

So a replay lot and a live lot for the same signal can diverge by the product of
two factors, neither of which any test previously pinned.

Every expected number below is **hand-computed from the geometry stated in the
test**, and every broker spec is read from the real export rather than assumed.

`config/profiles/ftmo.yaml` and `config/agent_config.yaml` are SHA-bound by the
R2 decision contract (`CLAUDE.md` H1). These tests **read** them; they never
write.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import yaml

from src.components.execution import ExecutionEngine


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "config" / "profiles"
# Vendored 2026-07-26 at integration review. This previously pointed at an absolute
# path inside the machine-local VPS export, so on any other checkout the five tests
# below skipped silently --- and V4 (18 of 19 shared symbols carry differing contract
# specs) is the evidence Gate G1b's fourth attribution axis rests on. 12 KB is cheap
# insurance against a finding that quietly stops being tested. The export copy is kept
# as the fallback so the file's provenance stays visible.
BROKER_SPEC_COMPARISON = (
    ROOT / "research" / "operations" / "vps_broker_truth_2026_07_26"
    / "BROKER_SYMBOL_SPEC_COMPARISON.json"
)
_BROKER_SPEC_EXPORT_FALLBACK = Path(
    "/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/"
    "BROKER_SYMBOL_SPEC_COMPARISON.json"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ftmo_instruments() -> dict:
    return yaml.safe_load((PROFILES / "ftmo.yaml").read_text())["instruments"]


@pytest.fixture(scope="module")
def redacted_account_instruments() -> dict:
    return yaml.safe_load((PROFILES / "redacted_account.yaml").read_text())["instruments"]


@pytest.fixture(scope="module")
def broker_spec() -> dict:
    for candidate in (BROKER_SPEC_COMPARISON, _BROKER_SPEC_EXPORT_FALLBACK):
        if candidate.is_file():
            return json.loads(candidate.read_text())
    # The vendored copy is tracked, so reaching here means the repository is
    # incomplete rather than the machine being a different one. Fail, do not skip:
    # a silent skip is how V4 would stop being tested without anyone noticing.
    raise AssertionError(
        f"broker spec comparison missing at {BROKER_SPEC_COMPARISON} (tracked) and at "
        f"{_BROKER_SPEC_EXPORT_FALLBACK} (machine-local export fallback)."
    )


def _engine(symbol: str, risk_pct: float) -> ExecutionEngine:
    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(ask=25000.0, bid=24999.0)
    mt5.get_history_deals.return_value = []
    return ExecutionEngine(
        mt5,
        {"market": {"symbol": symbol}, "risk": {"risk_per_trade_pct": risk_pct}},
    )


def _symbol_info(**overrides) -> SimpleNamespace:
    info = SimpleNamespace(
        trade_tick_size=0.01,
        trade_tick_value=0.01,
        volume_min=0.01,
        volume_step=0.01,
        volume_max=1000.0,
        filling_mode=3,
        spread=10,
    )
    for key, value in overrides.items():
        setattr(info, key, value)
    return info


def _lots_from_tick_geometry(symbol, *, sl_distance, risk_amount, tick_size, tick_value):
    """Drive the REAL `_calculate_lots` tick-value branch (execution.py:9194-9207).

    `direction`/`entry_price`/`stop_loss` are deliberately not supplied, so the
    broker `order_calc_profit` branch is not taken and the tick-value fallback —
    the branch that carries no currency conversion — is what runs.
    """
    engine = _engine(symbol, 1.0)
    return engine._calculate_lots(
        sl_distance,
        risk_amount,
        sym_info=_symbol_info(trade_tick_size=tick_size, trade_tick_value=tick_value),
    )


# ---------------------------------------------------------------------------
# 1. The profile overlay divergence, pinned with its direction stated
# ---------------------------------------------------------------------------

class TestProfileOverlayDivergence:
    """`CLAUDE.md` §4 records NAS100 2x and US30_cash 0.5x. Pin which way round.

    Measured, and the direction is the thing worth pinning because the bare
    ratios read either way:

        NAS100     replay(FTMO) 0.50 %  vs  live(FN) 0.25 %  ->  replay is 2x live
        US30_cash  replay(FTMO) 1.00 %  vs  live(FN) 2.00 %  ->  replay is 0.5x live

    So `CLAUDE.md`'s "2x / 0.5x" is **replay relative to live**. Stated inverted
    it is exactly wrong, and a reader has no way to tell from the ratios alone.
    """

    @pytest.mark.parametrize("symbol,ftmo_pct,fn_pct,replay_over_live", [
        ("NAS100", 0.5, 0.25, 2.0),
        ("US30_cash", 1.0, 2.0, 0.5),
    ])
    def test_risk_pct_divergence_and_its_direction(
        self, ftmo_instruments, redacted_account_instruments,
        symbol, ftmo_pct, fn_pct, replay_over_live,
    ):
        measured_ftmo = ftmo_instruments[symbol]["risk"]["risk_per_trade_pct"]
        measured_fn = redacted_account_instruments[symbol]["risk"]["risk_per_trade_pct"]
        assert measured_ftmo == ftmo_pct
        assert measured_fn == fn_pct
        assert measured_ftmo / measured_fn == pytest.approx(replay_over_live)

    @pytest.mark.parametrize("symbol", ["NAS100", "US30_cash"])
    def test_contract_size_and_tick_value_also_diverge_ten_fold(
        self, ftmo_instruments, redacted_account_instruments, symbol,
    ):
        """The overlay divergence is NOT only the risk dial.

        Both profiles also carry the broker's own contract geometry, and it
        differs by 10x on both symbols — in the OPPOSITE direction to NAS100's
        risk dial. So the two factors partly cancel on one symbol and compound
        on the other, which is precisely why neither can be reasoned about alone.
        """
        ftmo_market = ftmo_instruments[symbol]["market"]
        fn_market = redacted_account_instruments[symbol]["market"]

        assert ftmo_market["contract_size"] == 1.0
        assert fn_market["contract_size"] == 10.0
        assert ftmo_market["trade_tick_value"] == 0.01
        assert fn_market["trade_tick_value"] == 0.1

        # And they are not even the same broker symbol.
        assert ftmo_market["mt5_symbol"] != fn_market["mt5_symbol"]

    def test_the_two_factors_compose_into_a_single_live_vs_replay_size_ratio(
        self, ftmo_instruments, redacted_account_instruments,
    ):
        """The number that actually matters: lots(replay) / lots(live).

        Hand-computed for NAS100, equity 100,000, SL distance 50.00 points.

          replay (FTMO): risk = 0.50 % x 100,000 = 500.00
                         ticks = 50.00 / 0.01 = 5,000
                         cash/lot = 5,000 x 0.01 = 50.00
                         lots = 500.00 / 50.00 = 10.00

          live   (FN):   risk = 0.25 % x 100,000 = 250.00
                         ticks = 50.00 / 0.01 = 5,000
                         cash/lot = 5,000 x 0.10 = 500.00
                         lots = 250.00 / 500.00 = 0.50

        Ratio = 20x. The 2x risk-dial divergence and the 10x tick-value
        divergence COMPOUND here rather than cancelling.
        """
        equity = 100_000.0
        sl_distance = 50.00

        ftmo_market = ftmo_instruments["NAS100"]["market"]
        fn_market = redacted_account_instruments["NAS100"]["market"]

        replay_lots = _lots_from_tick_geometry(
            "NAS100",
            sl_distance=sl_distance,
            risk_amount=equity * ftmo_instruments["NAS100"]["risk"]["risk_per_trade_pct"] / 100,
            tick_size=ftmo_market["trade_tick_size"],
            tick_value=ftmo_market["trade_tick_value"],
        )
        live_lots = _lots_from_tick_geometry(
            "NAS100",
            sl_distance=sl_distance,
            risk_amount=equity * redacted_account_instruments["NAS100"]["risk"]["risk_per_trade_pct"] / 100,
            tick_size=fn_market["trade_tick_size"],
            tick_value=fn_market["trade_tick_value"],
        )

        assert replay_lots == pytest.approx(10.00, abs=1e-9)
        assert live_lots == pytest.approx(0.50, abs=1e-9)
        assert replay_lots / live_lots == pytest.approx(20.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 2. The broker contract specs, from the real export
# ---------------------------------------------------------------------------

class TestBrokerContractSpecsDiffer:
    """Measured on the 2026-07-25 VPS export, not assumed."""

    def test_every_shared_symbol_differs(self, broker_spec):
        rows = broker_spec["comparison"]
        shared = [r for r in rows if r["status"] not in
                  ("absent_on_redacted_account", "absent_on_ftmo")]
        differing = [r for r in shared if r["status"] == "differs"]

        assert len(rows) == 19
        assert len(shared) == 18
        # Not "18 of 19" — 18 of the 19 rows are shared, and ALL 18 of those
        # differ. Zero shared symbols are identical.
        assert len(differing) == 18
        assert [r["instrument"] for r in shared if r["status"] != "differs"] == []

    def test_contract_size_differs_on_the_index_cfds_and_ethusd(self, broker_spec):
        differing_on_contract_size = sorted(
            r["instrument"] for r in broker_spec["comparison"]
            if r["status"] == "differs"
            and "trade_contract_size" in r["differing_fields"]
        )
        assert differing_on_contract_size == [
            "ETHUSD", "GER40.cash", "UK100.cash",
            "US100.cash", "US30.cash", "US500.cash",
        ]

    def test_the_index_cfds_all_move_the_same_way_and_ethusd_moves_the_other(
        self, broker_spec,
    ):
        """Direction matters: ETHUSD is the one that inverts.

        Five index CFDs: FTMO 1.0 -> redacted_account 10.0.
        ETHUSD:          FTMO 10.0 -> redacted_account 1.0.

        A blanket "redacted_account contracts are 10x" rule would size ETHUSD 100x
        wrong. That is the value of pinning direction per symbol.
        """
        by_instrument = {
            r["instrument"]: r["differing_fields"]["trade_contract_size"]
            for r in broker_spec["comparison"]
            if r["status"] == "differs"
            and "trade_contract_size" in r["differing_fields"]
        }
        for index_cfd in ("GER40.cash", "UK100.cash", "US100.cash",
                          "US30.cash", "US500.cash"):
            assert by_instrument[index_cfd] == {"ftmo": 1.0, "redacted_account": 10.0}

        assert by_instrument["ETHUSD"] == {"ftmo": 10.0, "redacted_account": 1.0}

    def test_jp225_differs_in_quantisation_as_well(self, broker_spec):
        fields = next(
            r["differing_fields"] for r in broker_spec["comparison"]
            if r["instrument"] == "JP225.cash"
        )
        assert fields["digits"] == {"ftmo": 2, "redacted_account": 0}
        assert fields["point"] == {"ftmo": 0.01, "redacted_account": 1.0}
        assert fields["trade_tick_size"] == {"ftmo": 0.01, "redacted_account": 1.0}
        # Notably NOT trade_contract_size — JP225 is not in that set.
        assert "trade_contract_size" not in fields


# ---------------------------------------------------------------------------
# 3. Account currency — the surface, and what actually protects it
# ---------------------------------------------------------------------------

class TestAccountCurrencyConversion:
    """JP225 is the concrete case: the two brokers disagree on the base currency.

    `currency_base` is `JPY` at FTMO and `USD` at redacted_account for the same index.
    That is what an account-currency conversion defect would look like in the
    wild, and the export shows it is not hypothetical.
    """

    def test_the_two_brokers_disagree_on_jp225_base_currency(self, broker_spec):
        fields = next(
            r["differing_fields"] for r in broker_spec["comparison"]
            if r["instrument"] == "JP225.cash"
        )
        assert fields["currency_base"] == {"ftmo": "JPY", "redacted_account": "USD"}

    def test_tick_value_alone_is_a_misleading_comparand(self, broker_spec):
        """The invariant that actually holds, and the trap that does not.

        FTMO's JP225 `trade_tick_value` is 0.00061024..., redacted_account's is 0.06 —
        a ~98x divergence that looks alarming. But tick VALUE and tick SIZE
        diverge together, and the economically meaningful quantity is
        cash-risk-per-lot, which agrees to under 2 %:

          FTMO: 100.0 price units / 0.01 tick = 10,000 ticks
                10,000 x 0.0006102435482000867 = 6.102435 cash/lot
          FN:   100.0 price units / 1.00 tick =    100 ticks
                   100 x 0.06                 = 6.000000 cash/lot

        So comparing `trade_tick_value` across brokers is meaningless on its
        own. This test exists to stop a future reader "fixing" a 98x
        discrepancy that is not one.
        """
        fields = next(
            r["differing_fields"] for r in broker_spec["comparison"]
            if r["instrument"] == "JP225.cash"
        )
        ftmo_tick_value = fields["trade_tick_value"]["ftmo"]
        fn_tick_value = fields["trade_tick_value"]["redacted_account"]
        ftmo_tick_size = fields["trade_tick_size"]["ftmo"]
        fn_tick_size = fields["trade_tick_size"]["redacted_account"]

        # The alarming-looking ratio.
        assert fn_tick_value / ftmo_tick_value == pytest.approx(98.3, rel=0.01)

        sl_distance = 100.0
        risk_amount = 610.24

        ftmo_lots = _lots_from_tick_geometry(
            "JP225", sl_distance=sl_distance, risk_amount=risk_amount,
            tick_size=ftmo_tick_size, tick_value=ftmo_tick_value,
        )
        fn_lots = _lots_from_tick_geometry(
            "JP225", sl_distance=sl_distance, risk_amount=risk_amount,
            tick_size=fn_tick_size, tick_value=fn_tick_value,
        )

        assert ftmo_lots == pytest.approx(610.24 / 6.102435482000867, abs=1e-6)
        assert fn_lots == pytest.approx(610.24 / 6.0, abs=1e-6)
        # Under 2 % apart, against a 98x raw tick-value divergence.
        assert abs(ftmo_lots / fn_lots - 1.0) < 0.02

    def test_the_tick_value_branch_applies_no_currency_conversion(self):
        """Stated as a measurement, because the absence is the point.

        `_calculate_lots` has three branches (`execution.py:9160-9222`):
        broker `order_calc_profit`, a tick-value fallback, and a naive
        contract-size fallback whose own comment says it is "correct for
        USD-quoted instruments".

        **Only the broker branch is currency-correct**, because
        `order_calc_profit` returns account-currency profit by construction.
        The tick-value branch multiplies raw metadata and converts nothing —
        so `lots` is exactly `risk_amount / (sl_distance/tick_size x tick_value)`
        with no FX term anywhere. This test pins that exact arithmetic, so a
        future change that quietly introduces (or needs) a conversion fails here.
        """
        lots = _lots_from_tick_geometry(
            "JP225", sl_distance=100.0, risk_amount=610.24,
            tick_size=0.01, tick_value=0.0006102435482000867,
        )
        ticks = 100.0 / 0.01
        cash_risk_per_lot = ticks * 0.0006102435482000867
        assert lots == pytest.approx(610.24 / cash_risk_per_lot, abs=1e-12)

    def test_selected_cell_sizing_fails_closed_rather_than_using_the_naive_branch(self):
        """The real protection, and it is a refusal rather than a conversion.

        With `require_broker_geometry=True` and no broker `order_calc_profit`,
        `_calculate_lots` returns `None` instead of falling through to the
        currency-naive branches (`execution.py:9183-9192`). That refusal — not
        any conversion step — is what keeps a JPY-quoted instrument from being
        sized off USD-shaped metadata on the live path.
        """
        engine = _engine("JP225", 1.0)
        engine.mt5._mt5 = SimpleNamespace(
            symbol_info=lambda _s: _symbol_info(),
            order_calc_profit=lambda *a, **k: None,
        )

        lots = engine._calculate_lots(
            100.0, 610.24,
            sym_info=_symbol_info(trade_tick_size=0.01, trade_tick_value=0.00061),
            require_broker_geometry=True,
            direction="LONG",
            entry_price=39000.0,
            stop_loss=38900.0,
        )

        assert lots is None
        assert engine._last_lot_sizing_diagnostic["status"] == (
            "broker_order_calc_profit_required_unavailable"
        )
        assert engine._last_lot_sizing_diagnostic["method"] == "none"

    def test_without_the_flag_it_silently_falls_back_to_the_naive_branch(self):
        """The companion measurement, and the reason the flag is load-bearing.

        Same inputs, `require_broker_geometry=False`: a number comes back, from
        metadata that carries no currency information. The refusal above is the
        only thing standing between the live path and this.
        """
        engine = _engine("JP225", 1.0)
        engine.mt5._mt5 = SimpleNamespace(
            symbol_info=lambda _s: _symbol_info(),
            order_calc_profit=lambda *a, **k: None,
        )

        lots = engine._calculate_lots(
            100.0, 610.24,
            sym_info=_symbol_info(trade_tick_size=0.01, trade_tick_value=0.00061),
            require_broker_geometry=False,
            direction="LONG",
            entry_price=39000.0,
            stop_loss=38900.0,
        )

        assert lots is not None
        assert engine._last_lot_sizing_diagnostic["method"] == "tick_value_legacy_fallback"
