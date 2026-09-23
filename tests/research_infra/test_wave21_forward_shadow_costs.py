"""Forward-shadow cost authority: live-vs-replay parity and startup preflight.

Why this file exists
--------------------
The lane's first VPS deployment ran a full session INERT: 88 candidates per
cycle, 88 refused, `eligibility_reason: cost_incomplete_fail_closed`,
`cost_refusal_reason: pretrade_packet_incomplete_component_sum`, and a startup
banner, heartbeat and packet writer that all read perfectly healthy.  The
single failing component was commission (`commission_r: null`,
`commission_cost_source_status: "source_gap"`); spread, slippage and swap were
all captured, and the live quote chain was fine.

Root cause was **not** a live-date source gap in the conversion.  The engine's
commission path (`broker_net_cost_engine._commission_cost_packet` ->
`costs.model.commission_usd_per_lot_for_packet`) consumes only the fitted
schedule, the symbol spec and the candidate's own stop distance; it never
consumes a D1 close.  It failed because
`research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json`
was not materialised in the shadow clone, `commission_usd_per_lot_for_packet`
swallows `CostTruthError` and returns `None` by contract, and the four-component
rule then correctly refuses -- silently, per candidate, forever.

So the guards here are the two the defect asked for:

1. **Parity** -- the live path and the replay path produce the *same number*
   for the *same trade*, on real sealed-February candidates.
2. **Preflight** -- a cost authority that can price nothing is a startup
   error, not 88 silent refusals.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra import v4_timewarp_simulated_live_research_loop as tw
from src.research_infra.wave21_forward_shadow.runner_config import (
    build_decision_config,
    load_shadow_config,
)
from src.research_infra.wave21_forward_shadow.shadow_costs import (
    CostAuthorityError,
    preflight_cost_authority,
    stamp_live_pretrade_cost,
)

REPO = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence"
    / "outcome_authority/forward_shadow/FEBRUARY_COST_PARITY_FIXTURE_V1.json"
)
SHADOW_CONFIG = REPO / "config/wave21_forward_shadow.yaml"

# Fields the two cost call sites consume from a candidate.
CONSUMED = (
    "candidate_id",
    "symbol",
    "side",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "risk_reward_ratio",
    "expected_slippage_r",
)


@pytest.fixture(scope="module")
def decision_config():
    runner_config = load_shadow_config(SHADOW_CONFIG, repo_root=REPO)
    config, _ = build_decision_config(runner_config, load_config=tw.load_config)
    return config


@pytest.fixture(scope="module")
def february():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _candidate(row: dict) -> dict:
    return {key: row.get(key) for key in CONSUMED}


def _quote(row: dict, asof: str, *, half_width: float = 0.0001) -> dict:
    mid = float(row["entry_price"])
    return {
        "bid": mid * (1.0 - half_width),
        "ask": mid * (1.0 + half_width),
        "time_utc": asof,
        "stale_seconds": 0.0,
    }


class TestFebruaryCommissionParity:
    """The acceptance criterion: same trade, same number, both paths."""

    def test_fixture_is_real_sealed_february(self, february):
        assert february["trading_day"] == "2026-02-03"
        assert february["row_count"] == len(february["rows"]) == 63
        # a real generated population, not a hand-written table
        assert len({row["symbol"] for row in february["rows"]}) >= 15

    def test_live_commission_equals_replay_commission(self, decision_config, february):
        """Live-sourced == replay-sourced commission, exactly, per candidate.

        Not `approx`: both call sites reach the same engine with the same
        inputs, so any difference at all is a real divergence in how one of
        them assembles `trade_params` / `symbol_info` / `broker_symbol` /
        `sl_distance` -- which is precisely what this pins.
        """

        asof = february["decision_time_utc"]
        checked = 0
        for row in february["rows"]:
            candidate = _candidate(row)
            live = stamp_live_pretrade_cost(
                candidate,
                config=decision_config,
                live_quote=_quote(row, asof),
                asof_utc=asof,
            )
            replay = tw.broker_calibrated_replay_cost_packet(
                candidate=candidate,
                config=decision_config,
                path_sources=None,
                risk_pct=0.0,
                asof_utc=asof,
            )
            assert live["commission_r"] is not None, (
                f"{row['symbol']}: live commission is None -- the broker-truth "
                "schedule did not resolve"
            )
            assert live["commission_r"] == replay.get("commission_r"), (
                f"{row['symbol']} {row['candidate_id']}: live "
                f"{live['commission_r']!r} != replay {replay.get('commission_r')!r}"
            )
            checked += 1
        assert checked == 63

    def test_live_commission_reproduces_sealed_february_value(
        self, decision_config, february
    ):
        """The number is also the one the sealed February run recorded."""

        asof = february["decision_time_utc"]
        for row in february["rows"]:
            live = stamp_live_pretrade_cost(
                _candidate(row),
                config=decision_config,
                live_quote=_quote(row, asof),
                asof_utc=asof,
            )
            assert live["commission_r"] == row["observed_commission_r"], (
                f"{row['symbol']}: {live['commission_r']!r} != sealed "
                f"{row['observed_commission_r']!r}"
            )

    @pytest.mark.parametrize("half_width", [0.00005, 0.01, 0.05])
    def test_commission_is_independent_of_the_live_quote(
        self, decision_config, february, half_width
    ):
        """Commission is a property of the trade, not of the predecision quote.

        This is why the live and replay paths CAN agree exactly despite
        sourcing their quotes from different places, and it is the property
        that would break first if commission ever grew a quote dependency.
        """

        asof = february["decision_time_utc"]
        for row in february["rows"]:
            live = stamp_live_pretrade_cost(
                _candidate(row),
                config=decision_config,
                live_quote=_quote(row, asof, half_width=half_width),
                asof_utc=asof,
            )
            assert live["commission_r"] == row["observed_commission_r"]

    def test_commission_never_consumes_the_dated_fx_archive(
        self, decision_config, february, monkeypatch
    ):
        """The lane's commission must stay date-free, or it goes inert again.

        `costs.model`'s dated machinery — `cost_r()` and the captured-D1
        `load_historical_fx()` — is reachable from this package but is NOT on
        this path: `broker_net_cost_engine` imports only
        `commission_usd_per_lot_for_packet` and `rollover_nights`.  That is the
        whole reason a live forward date prices fine.  If a future change routes
        the shadow's commission through the dated path, every live decision
        after the archive's last captured day becomes a source gap and the lane
        silently stops measuring — the exact failure this file exists for.
        """

        import src.costs.fx_conversion as fx_conversion
        import src.costs.model as costs_model

        calls = {"cost_r": 0, "historical_fx": 0}

        def _forbidden_cost_r(*args, **kwargs):
            calls["cost_r"] += 1
            raise AssertionError("shadow commission must not call cost_r()")

        def _forbidden_fx(*args, **kwargs):
            calls["historical_fx"] += 1
            raise AssertionError("shadow commission must not read the FX archive")

        monkeypatch.setattr(costs_model, "cost_r", _forbidden_cost_r)
        monkeypatch.setattr(fx_conversion, "load_historical_fx", _forbidden_fx)

        asof = february["decision_time_utc"]
        resolved = 0
        for row in february["rows"]:
            live = stamp_live_pretrade_cost(
                _candidate(row),
                config=decision_config,
                live_quote=_quote(row, asof),
                asof_utc=asof,
            )
            resolved += live["commission_r"] is not None
        assert resolved == 63
        assert calls == {"cost_r": 0, "historical_fx": 0}

    def test_forward_dated_decision_resolves_commission(
        self, decision_config, february
    ):
        """A live forward date is not a commission source gap.

        The lane's first deployment was read as "the captured archive ends
        before today, so the conversion has no source".  It does not: the
        schedule is date-free.  A date-dependent regression here would make
        the lane inert again on the next live day.
        """

        row = february["rows"][0]
        forward = "2027-03-01T14:00:00+00:00"
        live = stamp_live_pretrade_cost(
            _candidate(row),
            config=decision_config,
            live_quote=_quote(row, forward),
            asof_utc=forward,
        )
        assert live["commission_r"] == row["observed_commission_r"]
        assert live["packet"]["commission_cost_source_status"] == "captured"


class TestRefusedPacketDiagnostics:
    """A refused packet must name the field that refused it."""

    def test_complete_packet_carries_commission_provenance(
        self, decision_config, february
    ):
        row = february["rows"][0]
        asof = february["decision_time_utc"]
        live = stamp_live_pretrade_cost(
            _candidate(row),
            config=decision_config,
            live_quote=_quote(row, asof),
            asof_utc=asof,
        )
        packet = live["packet"]
        assert packet["commission_missing_fields"] == []
        assert packet["commission_usd_per_lot_round_turn"] is not None
        assert packet["commission_server"]

    def test_missing_schedule_is_named_not_merely_source_gap(
        self, decision_config, february, monkeypatch
    ):
        """Reproduces the deployed failure and asserts it is now diagnosable.

        Before this, the only machine-readable symptom was
        `commission_cost_source_status: "source_gap"`, which is equally
        consistent with a missing stop distance or a missing tick spec.  It
        cost a forensic trace to tell those apart from a log.
        """

        import src.components.broker_net_cost_engine as engine

        monkeypatch.setattr(
            engine, "commission_usd_per_lot_for_packet", lambda *a, **k: None
        )
        row = february["rows"][0]
        asof = february["decision_time_utc"]
        live = stamp_live_pretrade_cost(
            _candidate(row),
            config=decision_config,
            live_quote=_quote(row, asof),
            asof_utc=asof,
        )
        # the deployed signature, exactly
        assert live["complete"] is False
        assert live["refusal_reason"] == "pretrade_packet_incomplete_component_sum"
        assert live["commission_r"] is None
        assert live["packet"]["status"] == "REFUSED"
        assert live["packet"]["commission_cost_source_status"] == "source_gap"
        # ...and the part that is new: it says WHICH field
        assert live["packet"]["commission_missing_fields"] == [
            "broker_true_commission_schedule_or_required_entry_price"
        ]
        # the other three components stayed captured, as they did on the VPS
        assert live["spread_r"] is not None
        assert live["expected_slippage_r"] is not None
        assert live["packet"]["swap_cost_source_status"] == "captured"

    def test_no_component_is_defaulted_when_one_is_missing(
        self, decision_config, february, monkeypatch
    ):
        """The fail-closed rule itself: never default, never zero."""

        import src.components.broker_net_cost_engine as engine

        monkeypatch.setattr(
            engine, "commission_usd_per_lot_for_packet", lambda *a, **k: None
        )
        row = february["rows"][0]
        asof = february["decision_time_utc"]
        live = stamp_live_pretrade_cost(
            _candidate(row),
            config=decision_config,
            live_quote=_quote(row, asof),
            asof_utc=asof,
        )
        # None, not 0.0 — a zeroed component is the F38 defect, and it would
        # sum to a plausible-looking total instead of refusing.
        assert live["cost_r"] is None
        assert live["commission_r"] is None
        assert live["packet"]["total_cost_r"] is None
        assert live["packet"]["total_cost_components"]["commission_r"] is None


class TestCostAuthorityPreflight:
    """A lane that can price nothing must not start."""

    def test_preflight_passes_on_the_live_surface(self, decision_config):
        report = preflight_cost_authority(
            config=decision_config, symbols=tuple(tw.GTOS_24_SYMBOL_SURFACE)
        )
        assert report["status"] == "ok"
        assert report["account"] == "FTMO"
        assert report["symbols_checked"] == 24
        assert report["commission_resolvable_symbols"] == 24
        assert report["commission_unresolvable_symbols"] == []
        assert report["artifact_present"] is True
        assert report["spread_model_status"] == "loaded"
        assert report["spread_model_sha256"]

    def test_missing_spread_model_refuses_startup(self, decision_config, monkeypatch):
        """Deploy 1's failure mode, also moved to startup.

        Without this the spread model's absence stays invisible until the first
        would-be order is stamped, then raises mid-cycle out of
        `shadow_lifecycle._authority_hashes()`.
        """

        import src.costs.spread_model as spread_model

        monkeypatch.setattr(
            spread_model, "DEFAULT_MODEL", Path("/nonexistent/SPREAD_MODEL_V1.json")
        )
        with pytest.raises(CostAuthorityError) as excinfo:
            preflight_cost_authority(config=decision_config, symbols=("EURUSD",))
        message = str(excinfo.value)
        assert "spread model is unavailable" in message
        assert "spread_model_2026_07_29" in message

    def test_missing_broker_truth_artifact_refuses_startup(
        self, decision_config, monkeypatch
    ):
        """The deployed defect, as a startup error instead of a silent lane."""

        import src.costs.model as costs_model

        # `str(Path(...))`, not the POSIX literal: this suite is meant to run on
        # the Windows host too (runbook §2), where `str()` of this path renders
        # with backslashes and a literal comparison would never match.
        absent = Path("/nonexistent/BROKER_TRUE_COSTS_V1.json")
        monkeypatch.setattr(costs_model, "DEFAULT_ARTIFACT", absent)
        with pytest.raises(CostAuthorityError) as excinfo:
            preflight_cost_authority(
                config=decision_config, symbols=tuple(tw.GTOS_24_SYMBOL_SURFACE)
            )
        message = str(excinfo.value)
        # actionable: names the count, the remedy, and the symptom it prevents
        assert "0 of 24" in message
        assert "broker_truth_layer_2026_07_27" in message
        assert "pretrade_packet_incomplete_component_sum" in message
        # ...and names the path the cost layer will ACTUALLY read, resolved at
        # call time. Binding it at import made this line report the healthy
        # default path while the lane was reading a different one.
        assert str(absent) in message
        assert "present:  False" in message

    def test_unresolvable_account_refuses_startup(self, decision_config):
        config = dict(decision_config)
        config["broker_profile"] = {"server": "NotARegisteredBroker-Server9"}
        with pytest.raises(CostAuthorityError) as excinfo:
            preflight_cost_authority(config=config, symbols=("EURUSD",))
        assert "cannot resolve a broker-truth account" in str(excinfo.value)

    def test_partial_surface_is_reported_not_refused(self, decision_config):
        """One unpriceable symbol is a partial lane, not a dead one."""

        report = preflight_cost_authority(
            config=decision_config, symbols=("EURUSD", "NOT_A_SYMBOL")
        )
        assert report["status"] == "partial"
        assert report["commission_unresolvable_symbols"] == ["NOT_A_SYMBOL"]
        assert report["commission_resolvable_symbols"] == 1


class TestRunnerRefusesInertStartup:
    """The guard end-to-end: the runner, not just the helper, must refuse."""

    @staticmethod
    def _runner_config(tmp_path):
        runner_config = load_shadow_config(SHADOW_CONFIG, repo_root=REPO)
        # never touch the real namespace; the preflight fires before the state
        # directory is claimed, and this keeps that true if the order changes
        runner_config.namespace_dir = tmp_path / "funnel_shadow"
        runner_config.models_dir = tmp_path / "models"
        return runner_config

    def test_runner_start_refuses_when_nothing_is_priceable(
        self, tmp_path, monkeypatch
    ):
        pytest.importorskip("sklearn")
        pytest.importorskip("pydantic")
        runner_module = pytest.importorskip(
            "src.research_infra.wave21_forward_shadow_runner"
        )
        import src.costs.model as costs_model

        monkeypatch.setattr(
            costs_model,
            "DEFAULT_ARTIFACT",
            Path("/nonexistent/BROKER_TRUE_COSTS_V1.json"),
        )

        class _NoMT5:
            def copy_rates_from_pos(self, *a, **k):  # pragma: no cover - unused
                raise AssertionError("startup must fail before any market read")

            def symbol_info_tick(self, *a, **k):  # pragma: no cover - unused
                raise AssertionError("startup must fail before any market read")

        with pytest.raises(CostAuthorityError):
            runner_module.ForwardShadowRunner(
                self._runner_config(tmp_path), mt5_module=_NoMT5()
            )
        # and it refused before creating its namespace
        assert not (tmp_path / "funnel_shadow").exists()

    def test_runner_starts_and_reports_ok_when_priceable(self, tmp_path):
        pytest.importorskip("sklearn")
        pytest.importorskip("pydantic")
        runner_module = pytest.importorskip(
            "src.research_infra.wave21_forward_shadow_runner"
        )

        class _NoMT5:
            def copy_rates_from_pos(self, *a, **k):
                return []

            def symbol_info_tick(self, *a, **k):
                return None

        runner = runner_module.ForwardShadowRunner(
            self._runner_config(tmp_path), mt5_module=_NoMT5()
        )
        assert runner.cost_preflight["status"] == "ok"
        assert runner.cost_preflight["commission_resolvable_symbols"] == len(
            runner.symbols
        )
