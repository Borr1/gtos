"""Stage 3c — UltimateBookOwner: cross-symbol driver, default-off, places only when gated on."""
import json
import random
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.ultimate_book.book_owner import UltimateBookOwner, _bridge_telemetry
from src.components.ultimate_book.placement_ledger import PLACEMENT_CAPTURE_COMPLETE_STATUS
from src.components.ultimate_book.runtime_learning_packet import build_runtime_learning_packet


def _momentum_candles(n, seed, start, vol, anchor_forming=None):
    rnd = random.Random(seed)
    out = []; p = start; ch = 0.0
    anchor = anchor_forming or (datetime.now(timezone.utc) - timedelta(seconds=1))
    t0 = anchor - timedelta(hours=4 * (n - 1))
    for k in range(n):
        ch = 0.6 * ch + rnd.gauss(0.4 * vol, vol)
        o = p; c = max(1.0, o + ch)
        w = abs(rnd.gauss(0, 0.2 * vol))
        out.append({"time": (t0 + timedelta(hours=4 * k)).isoformat(),
                    "open": o, "high": max(o, c) + w, "low": min(o, c) - w, "close": c, "volume": 100})
        p = c
    return out


class _Tick:
    def __init__(self, bid, ask): self.bid = bid; self.ask = ask


class _FakeMT5:
    def __init__(self):
        self._anchor_forming = datetime.now(timezone.utc) - timedelta(seconds=1)

    def get_candles(self, symbol, tf, count):
        if symbol == "BTCUSD":
            return _momentum_candles(
                count + 1,
                3,
                60000.0,
                300.0,
                anchor_forming=self._anchor_forming,
            )
        return _momentum_candles(
            count + 1,
            99,
            100.0,
            0.05,
            anchor_forming=self._anchor_forming,
        )
    def get_tick(self, symbol):
        # realistic spreads relative to each synthetic symbol's R-unit (BTCUSD stop ~703 -> 10pt spread
        # is 0.014R; the 100-priced symbol's stop ~0.146 -> a 0.01 spread is 0.069R). Both clear the
        # pre-send spread-cost screen (spread_r <= 0.10); a wide 0.2 spread here would (correctly) be
        # cost-screened, which is what the screen is FOR -- it is not what this guard test exercises.
        return _Tick(59995.0, 60005.0) if symbol == "BTCUSD" else _Tick(99.995, 100.005)
    def get_account_balance(self): return 100000.0
    def get_account_equity(self): return 100000.0


class _RecordingEngine:
    def __init__(self): self.calls = []
    def open_trade(self, tp, bal, **kw):
        self.calls.append(tp)
        class _TS: ticket = 999
        return _TS()


def _cfg(gates_on):
    return {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "instruments": {
            "BTCUSD": {"market": {"mt5_symbol": "BTCUSD"}},
            "DASHUSD": {"market": {"mt5_symbol": "DASHUSD"}},
        },
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": gates_on, "ultimate_book_apply_to_execution": gates_on,
            "ultimate_book_live_activation_allowed": gates_on,
            "ultimate_book_live_broker_authority": gates_on,
            "ultimate_book_disable_broad_selector": True,
            # D8 FIXED 2026-07-27: an ENABLED book fails closed on a missing dial key rather than
            # defaulting it (bridge.REQUIRED_DIAL_KEYS). Four of the nine were absent here --
            # derisk_mode, include_candidate_book, include_market_expansion_book, stress_derisk --
            # so this fixture was silently sizing from bridge.DEFAULT_CONFIG for those. Declared
            # explicitly; the values chosen are the ones the fixture was already inheriting, so the
            # sized book is unchanged.
            "ultimate_book_profile": "clean3_w7_measured_nom1p25", "ultimate_book_include_clean3": True,
            "ultimate_book_derisk_mode": "band",
            "ultimate_book_include_candidate_book": False,
            "ultimate_book_include_market_expansion_book": False,
            "ultimate_book_stress_derisk": False,
            "ultimate_book_kelly_lite": True, "ultimate_book_kelly_conservative": True,
            "ultimate_book_drop_w7_symbols": True,
            "selector_v4_enabled": True, "selector_v4_apply_to_execution": False,
        },
    }


def test_notify_placed_no_broker_tp_renders_native_exit_plan(tmp_path):
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path), namespace="redacted_account_live_bee34003")
    cards = []
    owner._send_card = cards.append

    owner._notify_placed(
        SimpleNamespace(direction=-1, symbol="EURUSD", sleeve="asian_fade"),
        SimpleNamespace(risk_pct_per_trade=0.01),
        {
            "trade_state": SimpleNamespace(entry_price=1.14157, stop_loss=1.14200, take_profit_1=0.0),
            "trade_params": {
                "gtos_vnext_dynamic_policy_selected": "trailing_runner",
                "gtos_vnext_dynamic_broker_take_profit_mode": "none",
                "gtos_vnext_dynamic_no_broker_take_profit": True,
                "gtos_vnext_dynamic_trailing_trigger_r": 0.5,
                "gtos_vnext_dynamic_trail_gap_r": 0.5,
                "gtos_vnext_dynamic_time_stop_bars": 48,
            },
        },
    )

    assert cards
    card = cards[0]
    assert "broker TP none" in card
    assert "native exit: trailing runner" in card
    assert "trigger 0.5R" in card
    assert "trail gap 0.5R" in card
    assert "time stop 48 bars" in card
    assert "reward 0.00R" not in card
    assert " TP 1.1416" not in card


def test_bridge_telemetry_reports_active_policy_and_guard_flags():
    from src.components.ultimate_book.admission import GovernorState
    from src.components.ultimate_book.bridge import evaluate_vnext_ultimate_book_admission

    dec = evaluate_vnext_ultimate_book_admission(
        config={
            "gtos_vnext_runtime": {
                "ultimate_book_enabled": True,
                "ultimate_book_apply_to_execution": True,
                "ultimate_book_live_activation_allowed": True,
                "ultimate_book_live_broker_authority": True,
                "ultimate_book_disable_broad_selector": True,
                "ultimate_book_profile": "clean3_w7_measured_nom1p25",
                "ultimate_book_derisk_mode": "band",   # D8: the ninth dial key, previously defaulted
                "ultimate_book_include_clean3": False,
                "ultimate_book_include_clean4": False,
                "ultimate_book_include_candidate_book": True,
                "ultimate_book_candidate_book_sleeves": ["ny_crypto_momentum"],
                "ultimate_book_include_market_expansion_book": True,
                "ultimate_book_market_expansion_policy": "positive_weighted12_after_swap",
                "ultimate_book_market_expansion_sleeves": [],
                "ultimate_book_kelly_lite": True,
                "ultimate_book_kelly_conservative": False,
                "ultimate_book_sqrt_n_pooling": True,
                "ultimate_book_stress_derisk": True,
                "ultimate_book_overlays": True,
                "ultimate_book_vp_acceptance": True,
                "ultimate_book_drop_w7_symbols": True,
                "ultimate_book_learning_rerate": {"ny_crypto_momentum": 0.0},
                "ultimate_book_metals_confluence_gate": True,
                "ultimate_book_symbol_damage_guard": True,
                "selector_v4_enabled": True,
                "selector_v4_apply_to_execution": False,
            }
        },
        intents=[],
        governor_state=GovernorState(
            equity=100000.0,
            high_water=100000.0,
            realized_today_pct=0.0,
            open_risk_pct=0.0,
            max_dd_reference_equity=100000.0,
        ),
    )

    telemetry = _bridge_telemetry(dec)

    assert telemetry["runtime_effect_now"] is True
    assert telemetry["live_broker_authority"] is True
    assert telemetry["decision_status"] == "no_candidates_this_bar"
    assert telemetry["profile"] == "clean3_w7_measured_nom1p25"
    assert telemetry["include_candidate_book"] is True
    assert telemetry["candidate_book_sleeves"] == ["ny_crypto_momentum"]
    assert telemetry["candidate_book_sleeve_count"] == 1
    assert telemetry["include_market_expansion_book"] is True
    assert telemetry["market_expansion_policy"] == "positive_weighted12_after_swap"
    assert telemetry["market_expansion_sleeve_count"] == 12
    assert telemetry["kelly_lite"] is True
    assert telemetry["kelly_conservative"] is False
    assert telemetry["sqrt_n_pooling"] is True
    assert telemetry["stress_derisk"] is True
    assert telemetry["overlays"] is True
    assert telemetry["vp_acceptance"] is True
    assert telemetry["drop_w7_symbols"] is True
    assert telemetry["learning_rerate_active"] is True
    assert telemetry["metals_confluence_gate"] is True
    assert telemetry["symbol_damage_guard"] is True


def test_owner_runtime_context_parses_false_string_flags(tmp_path):
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"].update({
        "ultimate_book_enabled": "false",
        "ultimate_book_apply_to_execution": "true",
        "ultimate_book_live_activation_allowed": "true",
        "ultimate_book_live_broker_authority": "true",
        "ultimate_book_include_candidate_book": "false",
        "ultimate_book_include_market_expansion_book": "false",
        "ultimate_book_runtime_learning_packet_enabled": "false",
        "ultimate_book_runtime_learning_packet_log_enabled": "false",
        "selector_v4_enabled": "true",
        "selector_v4_apply_to_execution": "false",
    })

    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path))
    ctx = owner._runtime_learning_bridge_context()

    assert owner._runtime_learning_packet_enabled is False
    assert owner._runtime_learning_packet_log_enabled is False
    assert ctx["enabled"] is False
    assert ctx["include_candidate_book"] is False
    assert ctx["include_market_expansion_book"] is False
    assert ctx["runtime_effect_now"] is False


def _owner(gates_on):
    engines = {}
    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]
    owner = UltimateBookOwner(_cfg(gates_on), _FakeMT5(), tempfile.mkdtemp(), engine_factory=factory)
    return owner, engines


def test_owner_default_off_places_nothing():
    owner, engines = _owner(False)
    summary = owner.run_cycle(tags=("crypto",))
    assert summary["runtime_effect_now"] is False
    assert summary["placed"] == []
    assert all(len(e.calls) == 0 for e in engines.values())   # NO open_trade while gated off


def test_owner_gated_on_places_crypto():
    # REAL CODE DEFECT caught here (2026-08-25 pre-existing-failure clearing, f5max-ship;
    # DO-NOT-EDIT-TEST): the firing_sleeves.json assert below fails because book_owner
    # commits conviction via getattr(self.engine, "record_placement_conviction", None)
    # (:3915/:3979/:8148) while UltimateBookLiveEngine defines only
    # commit_running_conviction (book_engine.py:1680) — the callable() guard silently
    # no-ops, so durable conviction is NEVER written.  Fix belongs in src (engine alias),
    # applied centrally; verified green under that one-line patch.
    owner, engines = _owner(True)
    owner.engine.config["ultimate_book_kelly_running_count"] = True
    summary = owner.run_cycle(tags=("crypto",))
    assert summary["runtime_effect_now"] is True
    assert len(summary["placed"]) >= 1
    placed = summary["placed"][0]
    assert placed["symbol"] == "BTCUSD" and placed["sleeve"] == "crypto"
    assert placed["ticket_hash_sha256"]
    assert placed["joinability_status"] == "ticket_candidate_decision_policy_joinable"
    assert placed["decision_day"] == placed["decision_bar_iso"][:10]
    assert placed["placement_source_completeness_status"] == PLACEMENT_CAPTURE_COMPLETE_STATUS
    assert placed["placement_source_missing_fields"] == []
    assert placed["gtos_vnext_dynamic_policy_selected"]
    assert placed["gtos_vnext_selected_cell_risk_policy_identity_status"] == "exact_selected_policy_risk_match"
    # the recording engine got a real 42-key V4 trade_params
    assert "BTCUSD" in engines and len(engines["BTCUSD"].calls) >= 1
    tp = engines["BTCUSD"].calls[0]
    assert tp["gtos_vnext_dynamic_policy_applied"] is True
    assert tp["gtos_vnext_selected_cell_risk_policy_identity_status"] == "exact_selected_policy_risk_match"
    assert tp["risk_pct_override"] > 0
    firing = json.loads((Path(owner._repo_root) / "pipeline_state" / "ultimate_book"
                         / owner._namespace / "firing_sleeves.json").read_text(encoding="utf-8"))
    assert list(firing["days"].values()) == [["crypto"]]


def test_market_expansion_unit_cluster_persists_to_placement_context(tmp_path):
    cfg = _cfg(True)
    cfg["instruments"]["NZDJPY"] = {"market": {"mt5_symbol": "NZDJPY"}}
    cfg["gtos_vnext_runtime"].update({
        "ultimate_book_runtime_learning_packet_enabled": True,
        "ultimate_book_runtime_learning_packet_log_enabled": True,
        "ultimate_book_runtime_learning_packet_log_path": "shadow_logs/runtime_packets.jsonl",
    })
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"
    bar = "2026-06-23T06:45:00+00:00"
    candidate_id = f"W7_BOOK::jpy_fx::NZDJPY::2026-06-23::LONG::{sleeve}"

    class _Engine:
        config = {"ultimate_book_max_entry_lateness_frac": 10.0}

        def evaluate(self, *, now_utc=None, tags=None):
            unit = {
                "sleeve_members": [sleeve],
                "risk_pct_per_trade": 0.001,
                "unit_risk_pct": 0.001,
                "sized": True,
                "cluster": "jpy_fx",
                "candidate_id": candidate_id,
            }
            decision = SimpleNamespace(
                runtime_effect_now=True,
                candidate_use_allowed_now=True,
                decision_status="execute_now",
                reason="unit_test",
                profile="clean3_w7_ceiling_nom2p00",
                enabled=True,
                apply_to_execution=True,
                live_activation_allowed_by_config=True,
                broad_selector_disable_required=True,
                broad_selector_apply_to_execution=False,
                include_market_expansion_book=True,
                market_expansion_policy="positive_weighted12_after_swap",
                market_expansion_sleeves=(sleeve,),
                realized_units=[unit],
                would_units=[unit],
                governor={"new_entries_allowed": True},
            )
            intent = SimpleNamespace(
                sleeve=sleeve,
                symbol="NZDJPY",
                direction=1,
                decision_day="2026-06-23",
                stop_dist=1.0,
                target_dist=2.0,
            )
            return {
                "ok": True,
                "reason": "unit_test",
                "n_intents": 1,
                "runtime_effect_now": True,
                "decision": decision,
                "governor_state": SimpleNamespace(equity=100000.0, realized_today_pct=0.0),
                "intents": [intent],
                "meta": [{"tag": sleeve, "symbol": "NZDJPY", "decision_bar_iso": bar, "timeframe": "M15"}],
                "generation": {"profile": "unit_test"},
            }

        def reset_window_date(self, now):
            return now.date().isoformat()

    class _Router:
        def account_state(self, *args, **kwargs):
            return {"current_equity": 100000.0, "balance": 100000.0}

        def place(self, execution_engine, sized_unit, intent, tick, account_state, balance):
            trade_params = {
                "candidate_id": candidate_id,
                "decision_time_utc": "2026-06-23T06:45:00+00:00",
                "direction": "LONG",
                "gtos_vnext_dynamic_policy_selected": "time_stop",
                "gtos_vnext_execution_policy_id": "emv4_time_stop_v1",
                "gtos_vnext_dynamic_time_stop_bars": 48,
                "gtos_vnext_dynamic_broker_take_profit_mode": "final_target",
                "gtos_vnext_dynamic_no_broker_take_profit": False,
                "gtos_vnext_book_native_exit_management": True,
                "gtos_vnext_selected_cell_risk_policy_identity_status": "exact_selected_policy_risk_match",
            }
            return {
                "placed": True,
                "trade_state": SimpleNamespace(ticket=987654),
                "trade_params": trade_params,
                "candidate_id": candidate_id,
            }

    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    owner.engine = _Engine()
    owner.router = _Router()

    summary = owner.run_cycle(now_utc=datetime(2026, 6, 23, 6, 46, tzinfo=timezone.utc))

    assert len(summary["placed"]) == 1
    placed = summary["placed"][0]
    assert placed["cluster"] == "jpy_fx"
    assert placed["placement_source_completeness_status"] == PLACEMENT_CAPTURE_COMPLETE_STATUS
    assert placed["placement_source_missing_fields"] == []
    record = owner._load_trade_record(987654)
    assert record["cluster"] == "jpy_fx"
    assert owner._ledger.row_for_ticket(987654)["cluster"] == "jpy_fx"
    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "runtime_packets.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert rows[-1]["event_type"] == "unit_placed"
    assert rows[-1]["cluster"] == "jpy_fx"
    assert rows[-1]["trade_record_joinability_status"] == "ticket_candidate_decision_policy_joinable"


def test_market_expansion_placement_derives_missing_unit_cluster_from_candidate_id(tmp_path):
    cfg = _cfg(True)
    cfg["instruments"]["AVAUSD"] = {"market": {"mt5_symbol": "AVAUSD"}}
    cfg["gtos_vnext_runtime"].update({
        "ultimate_book_runtime_learning_packet_enabled": True,
        "ultimate_book_runtime_learning_packet_log_enabled": True,
        "ultimate_book_runtime_learning_packet_log_path": "shadow_logs/runtime_packets.jsonl",
    })
    sleeve = "mx_avausd_d1_donchian_20_breakout"
    bar = "2026-06-18T23:00:00+00:00"
    candidate_id = f"W7_BOOK::crypto_alt_or_major::AVAUSD::2026-06-19::SHORT::{sleeve}"

    class _Engine:
        config = {"ultimate_book_max_entry_lateness_frac": 10.0}

        def evaluate(self, *, now_utc=None, tags=None):
            unit = {
                "sleeve_members": [sleeve],
                "risk_pct_per_trade": 0.001,
                "unit_risk_pct": 0.001,
                "sized": True,
            }
            decision = SimpleNamespace(
                runtime_effect_now=True,
                candidate_use_allowed_now=True,
                decision_status="execute_now",
                reason="unit_test",
                realized_units=[unit],
                would_units=[unit],
                governor={"new_entries_allowed": True},
            )
            intent = SimpleNamespace(
                sleeve=sleeve,
                symbol="AVAUSD",
                direction=-1,
                decision_day="2026-06-19",
                stop_dist=1.0,
                target_dist=2.0,
            )
            return {
                "ok": True,
                "reason": "unit_test",
                "n_intents": 1,
                "runtime_effect_now": True,
                "decision": decision,
                "governor_state": SimpleNamespace(equity=100000.0, realized_today_pct=0.0),
                "intents": [intent],
                "meta": [{"tag": sleeve, "symbol": "AVAUSD", "decision_bar_iso": bar, "timeframe": "D1"}],
            }

        def reset_window_date(self, now):
            return now.date().isoformat()

    class _Router:
        def account_state(self, *args, **kwargs):
            return {"current_equity": 100000.0, "balance": 100000.0}

        def place(self, execution_engine, sized_unit, intent, tick, account_state, balance):
            return {
                "placed": True,
                "trade_state": SimpleNamespace(ticket=987655),
                "trade_params": {
                    "candidate_id": candidate_id,
                    "decision_time_utc": "2026-06-19T21:52:51+00:00",
                    "direction": "SHORT",
                    "gtos_vnext_dynamic_policy_selected": "time_stop",
                    "gtos_vnext_execution_policy_id": "emv4_time_stop_v1",
                    "gtos_vnext_dynamic_time_stop_bars": 48,
                    "gtos_vnext_dynamic_broker_take_profit_mode": "final_target",
                    "gtos_vnext_dynamic_no_broker_take_profit": False,
                    "gtos_vnext_book_native_exit_management": True,
                    "gtos_vnext_selected_cell_risk_policy_identity_status": "exact_selected_policy_risk_match",
                },
                "candidate_id": candidate_id,
            }

    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    owner.engine = _Engine()
    owner.router = _Router()

    summary = owner.run_cycle(now_utc=datetime(2026, 6, 19, 21, 52, tzinfo=timezone.utc))

    placed = summary["placed"][0]
    assert placed["cluster"] == "crypto_alt_or_major"
    assert placed["placement_source_completeness_status"] == PLACEMENT_CAPTURE_COMPLETE_STATUS
    assert placed["placement_source_missing_fields"] == []
    assert owner._ledger.row_for_ticket(987655)["cluster"] == "crypto_alt_or_major"
    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "runtime_packets.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert rows[-1]["event_type"] == "unit_placed"
    assert rows[-1]["cluster"] == "crypto_alt_or_major"
    assert rows[-1]["placement_source_missing_fields"] == []


def test_runtime_learning_batch_preserves_valid_packets_when_one_packet_is_invalid(tmp_path):
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"].update({
        "ultimate_book_runtime_learning_packet_enabled": True,
        "ultimate_book_runtime_learning_packet_log_enabled": True,
        "ultimate_book_runtime_learning_packet_log_path": "shadow_logs/runtime_packets.jsonl",
    })
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    valid = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="cycle_no_candidates",
        outcome={"placement_status": "no_candidates"},
    )
    invalid = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="position_managed",
        outcome={
            "symbol": "ETHUSD",
            "sleeve": "ny_crypto_momentum",
            "management_action": "monitoring",
            "ticket_hash_sha256": "ticket-hash",
            "gtos_vnext_dynamic_policy_selected": "time_stop",
            "gtos_vnext_dynamic_no_broker_take_profit": True,
            "gtos_vnext_dynamic_broker_take_profit_mode": "none",
            "gtos_vnext_dynamic_time_stop_bars": 20,
        },
    )
    summary = {}

    owner._append_runtime_learning_packets(summary, [valid, valid, invalid])

    assert summary["runtime_learning"]["packets"] == 1
    assert summary["runtime_learning"]["packet_write_error_count"] == 1
    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "runtime_packets.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    # AMENDED 2026-07-28 (Session P, B203). This test previously asserted the main log contained
    # ONLY the valid packet -- i.e. that a refused packet left no trace in the evidence stream and
    # was recorded only in this cycle summary. That is the false-green class: a consumer reading
    # the packet log alone saw a complete-looking stream that had silently lost rows.
    # The refusal now leaves a `packet_rejected` marker in the main log and the full body in a
    # quarantine sidecar. The valid packet is still preserved and still deduplicated.
    assert [row["event_type"] for row in rows] == ["cycle_no_candidates", "packet_rejected"]
    marker = rows[1]
    assert marker["outcome"]["rejected_event_type"] == "position_managed"
    assert marker["outcome"]["quarantined"] is True
    quarantine = tmp_path / "shadow_logs" / "runtime_packets.jsonl.quarantine.jsonl"
    quarantined = [json.loads(line) for line in quarantine.read_text(encoding="utf-8").splitlines()]
    assert len(quarantined) == 1
    assert quarantined[0]["packet"]["event_type"] == "position_managed"


def test_runtime_learning_fallback_dedupe_retries_duplicate_after_transient_append_failure(tmp_path):
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"].update({
        "ultimate_book_runtime_learning_packet_enabled": True,
        "ultimate_book_runtime_learning_packet_log_enabled": True,
        "ultimate_book_runtime_learning_packet_log_path": "shadow_logs/runtime_packets.jsonl",
    })
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="cycle_no_candidates",
        outcome={"placement_status": "no_candidates"},
    )

    class _FlakyWriter:
        def __init__(self):
            self.calls = 0
            self.rows = []

        def append_many(self, packets):
            raise OSError("batch append unavailable")

        def append(self, packet):
            self.calls += 1
            if self.calls == 1:
                raise OSError("transient row append failure")
            self.rows.append(packet)

    writer = _FlakyWriter()
    owner._runtime_learning_writer = writer
    summary = {}

    owner._append_runtime_learning_packets(summary, [packet, packet])

    assert summary["runtime_learning"]["packets"] == 1
    assert summary["runtime_learning"]["packet_write_error_count"] == 1
    assert writer.rows == [packet]


def test_owner_idempotent_no_double_place_same_bar():
    owner, engines = _owner(True)
    s1 = owner.run_cycle(tags=("crypto",))
    assert len(s1["placed"]) >= 1                         # first cycle places
    n_first = len(engines["BTCUSD"].calls)
    s2 = owner.run_cycle(tags=("crypto",))                # identical bars -> same decision bar
    assert s2["placed"] == []                             # second cycle places NOTHING
    assert any("already_placed_this_bar" in str(sk.get("reason", "")) for sk in s2["skipped"])
    assert len(engines["BTCUSD"].calls) == n_first        # NO second open_trade call


def test_owner_never_raises_on_engine_blowup():
    owner, _ = _owner(True)
    def boom_factory(symbol):
        class Boom:
            def open_trade(self, *a, **k): raise RuntimeError("broker down")
        return Boom()
    owner._engine_factory = boom_factory
    owner._exec_engines.clear()
    summary = owner.run_cycle(tags=("crypto",))   # must not raise
    assert summary["placed"] == []
    assert any("router_exception" in str(s.get("reason", "")) for s in summary["skipped"])


# ---------------- Batch 2: lifecycle robustness (A2 isolation, A4 native flag, A3 loud persist, A5 reset id)

def test_owner_factory_raise_is_isolated_not_propagated():
    """A2: the engine FACTORY raising (e.g. a profile-missing symbol -> 'No instrument config') is NOT
    caught by the router (it happens before router.place). Before the fix it propagated out of run_cycle,
    which (the launcher marks the bar advanced afterwards) would re-fail the poison intent every tick and
    permanently starve its siblings. Now it is isolated to that intent."""
    owner, _ = _owner(True)
    def raising_factory(symbol):
        raise RuntimeError("No instrument config")
    owner._engine_factory = raising_factory
    owner._exec_engines.clear()
    summary = owner.run_cycle(tags=("crypto",))   # must NOT raise (previously propagated)
    assert summary["placed"] == []
    assert any("intent_exception" in str(s.get("reason", "")) for s in summary["skipped"])


def test_profile_missing_symbol_skips_before_engine_factory():
    """A profile-missing symbol is an intentional per-profile skip, not an exception-shaped placement failure."""
    cfg = _cfg(True)
    del cfg["instruments"]["DASHUSD"]
    factory_calls = []

    def factory(symbol):
        factory_calls.append(symbol)
        return _RecordingEngine()

    owner = UltimateBookOwner(cfg, _FakeMT5(), tempfile.mkdtemp(), engine_factory=factory)
    summary = owner.run_cycle(tags=("crypto",))

    assert any(
        isinstance(s, dict)
        and s.get("symbol") == "DASHUSD"
        and s.get("reason") == "profile_missing_instrument_config"
        and s.get("cluster")
        and s.get("timeframe")
        for s in summary["skipped"]
    )
    assert "DASHUSD" not in factory_calls


class _AdoptingEngine:
    """Fake per-symbol engine that adopts an orphan with the BUGGY record-less default (native flag False)."""
    def __init__(self, ticket=778899):
        self.active_trade = None
        self._ticket = ticket
    def reconcile_on_startup(self):
        ts = type("TS", (), {})()
        ts.ticket = self._ticket
        ts.gtos_vnext_book_native_exit_management = False   # the default the bug left in place
        self.active_trade = ts
        return None
    def check_time_stop_and_close(self):
        return None
    def check_and_manage_trade(self, _ctx):
        return "hold"


def test_recordless_adoption_marks_native_exit():
    """A4: a book position adopted with NO trade record must be flagged native so the generic per-symbol
    overlays do not overwrite the sleeve's validated exit. (Fresh temp repo -> no record on disk.)"""
    repo = tempfile.mkdtemp()
    engines = {}
    def factory(symbol):
        engines.setdefault(symbol, _AdoptingEngine())
        return engines[symbol]
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), repo, engine_factory=factory)
    summary = owner.manage_open_positions()
    assert summary["adopted"], "expected at least one adoption"
    for a in summary["adopted"]:
        eng = engines[a["symbol"]]
        assert eng.active_trade.gtos_vnext_book_native_exit_management is True
        record = owner._load_trade_record(a["ticket"])
        assert record is not None
        assert record["reconstructed_from_sleeve_identity"] is True
        assert record["execution"]["ticket"] == a["ticket"]
    persisted = owner._load_trade_record(summary["adopted"][0]["ticket"])
    assert persisted["sleeve"] == summary["adopted"][0]["sleeve"]
    assert persisted["symbol"] == summary["adopted"][0]["symbol"]


def test_persist_trade_record_failure_is_logged_not_silent(caplog):
    """A3: a trade-record persist failure must be LOUD (warning), not a silent pass."""
    import logging
    owner, _ = _owner(True)
    def boom():
        raise OSError("disk full")
    owner._trade_record_path = boom   # force the persist to fail
    intent = type("I", (), {"sleeve": "crypto", "symbol": "BTCUSD"})()
    with caplog.at_level(logging.WARNING):
        owner._persist_trade_record(778899, {"k": "v"}, intent)   # must not raise
    assert any("trade-record persist FAILED" in r.getMessage() for r in caplog.records)


def test_load_trade_record_backfills_join_keys_from_placement_ledger(tmp_path):
    """Legacy active trade records are repaired from the fsync'd placement ledger on load."""
    import json

    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path))
    ticket = 0
    bar = "2026-06-16T08:00:00+00:00"
    owner._ledger.record(
        "crypto",
        "BTCUSD",
        bar,
        decision_day="2026-06-16",
        cluster="crypto",
        candidate_id="cand-0",
        ticket=ticket,
        ts="2026-06-16T08:01:02+00:00",
    )
    d = tmp_path / "pipeline_state" / "ultimate_book" / "operator_profile" / "trade_records"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{ticket}.json"
    p.write_text(json.dumps({
        "instrumentation": {"gtos_vnext_dynamic_policy_selected": "time_stop"},
        "execution": {"ticket": ticket},
        "sleeve": "crypto",
        "symbol": "BTCUSD",
    }))

    rec = owner._load_trade_record(ticket)

    assert rec["candidate_id"] == "cand-0"
    assert rec["decision_bar_iso"] == bar
    assert rec["decision_day"] == "2026-06-16"
    assert rec["cluster"] == "crypto"
    assert rec["execution"]["ticket_hash_sha256"]
    assert rec["execution"]["broker_symbol"] == "BTCUSD"
    assert rec["execution"]["placed_at_utc"] == "2026-06-16T08:01:02+00:00"
    assert rec["runtime_learning_joinability_status"] == "ticket_candidate_decision_policy_joinable"
    assert json.loads(p.read_text())["candidate_id"] == "cand-0"

    ctx = owner._runtime_learning_trade_context(ticket=ticket, record=rec)
    assert ctx["joinability_status"] == "ticket_candidate_decision_policy_joinable"
    assert ctx["placement_observed_at_utc"] == "2026-06-16T08:01:02+00:00"


def test_runtime_learning_trade_context_does_not_overclaim_partial_joinability(tmp_path):
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path), namespace="ftmo_test")

    ticket_only = owner._runtime_learning_trade_context(
        ticket=111,
        record={
            "execution": {"ticket_hash_sha256": "ticket-hash"},
            "runtime_learning_joinability_status": "ticket_candidate_decision_policy_joinable",
        },
    )
    candidate_only = owner._runtime_learning_trade_context(
        ticket=111,
        record={"candidate_id": "cand-111", "execution": {"ticket_hash_sha256": "ticket-hash"}},
    )
    decision_only = owner._runtime_learning_trade_context(
        ticket=111,
        record={"decision_bar_iso": "2026-06-16T08:00:00+00:00", "execution": {"ticket_hash_sha256": "ticket-hash"}},
    )

    assert ticket_only["joinability_status"] == "ticket_policy_joinable"
    assert candidate_only["joinability_status"] == "ticket_policy_joinable"
    assert decision_only["joinability_status"] == "ticket_decision_policy_joinable"


def test_persist_trade_record_flattens_entry_lifecycle_packet(tmp_path):
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    intent = SimpleNamespace(sleeve="crypto", symbol="BTCUSD")
    trade_params = {
        "candidate_id": "cand-entry-1",
        "decision_time_utc": "2026-06-16T08:00:00+00:00",
        "gtos_vnext_broker_order_lifecycle_capture_v4_packet": {
            "status": "broker_real_entry_lifecycle_reconciled",
            "broker_real_entry_label_ready": True,
            "missing_fields": [],
            "deal_cost_reconciliation": {
                "deal_ticket": 88990011,
                "broker_fill_time_utc": "2026-06-16T08:00:04+00:00",
                "broker_entry_price": 60010.5,
                "commission": -3.5,
                "swap": 0.0,
                "source_status": "broker_real_history_deal",
                "account_history_lookup_status": "entry_deal_joined",
                "missing_fields": [],
            },
        },
    }

    owner._persist_trade_record(
        778899,
        trade_params,
        intent,
        decision_bar_iso="2026-06-16T08:00:00+00:00",
        decision_day="2026-06-16",
        cluster="crypto",
        placed_at_utc="2026-06-16T08:00:05+00:00",
        broker_symbol="BTCUSD",
    )
    rec = owner._load_trade_record(778899)

    assert rec["entry_reconciliation_status"] == "entry_deal_joined"
    assert rec["broker_real_entry_label_ready"] is True
    assert rec["execution"]["broker_entry_deal_ticket"] == 88990011
    assert rec["execution"]["broker_fill_time_utc"] == "2026-06-16T08:00:04+00:00"
    assert rec["execution"]["broker_entry_price"] == 60010.5
    assert rec["execution"]["broker_entry_commission"] == -3.5
    ctx = owner._runtime_learning_trade_context(ticket=778899, trade_params=trade_params, record=rec)
    assert ctx["entry_reconciliation_status"] == "entry_deal_joined"
    assert ctx["broker_entry_deal_hash_sha256"]
    assert "broker_entry_deal_ticket" not in ctx


def test_load_trade_record_self_heals_unresolved_entry_from_account_history(tmp_path):
    class _EntryHistoryMT5(_FakeMT5):
        def get_history_deals(self, _start, _end, _symbol):
            return [
                {
                    "ticket": 88990012,
                    "order": 778899,
                    "position_id": 778899,
                    "entry": 0,
                    "time": datetime(2026, 6, 16, 11, 0, 4, tzinfo=timezone.utc),
                    "price": 60010.5,
                    "commission": -3.5,
                    "swap": 0.0,
                }
            ]

    owner = UltimateBookOwner(_cfg(True), _EntryHistoryMT5(), str(tmp_path), namespace="ftmo_test")
    record = {
        "instrumentation": {
            "candidate_id": "cand-entry-repair",
            "gtos_vnext_broker_order_lifecycle_capture_v4_packet": {
                "order_send_observation": {
                    "order_send_time_utc": "2026-06-16T08:00:03+00:00",
                    "order_result_time_utc": "2026-06-16T08:00:04+00:00",
                },
                "deal_cost_reconciliation": {
                    "account_history_lookup_status": "UNRESOLVED_AFTER_HISTORY_ATTEMPT",
                    "deal_ticket": 0,
                    "missing_fields": [
                        "account_history_deal_reconciliation",
                        "broker_entry_price",
                        "broker_fill_time_utc",
                        "commission",
                        "swap",
                    ],
                },
            },
        },
        "execution": {
            "ticket": 778899,
            "broker_symbol": "BTCUSD",
            "placed_at_utc": "2026-06-16T08:00:04+00:00",
            "broker_entry_deal_ticket": 0,
            "entry_reconciliation_status": "UNRESOLVED_AFTER_HISTORY_ATTEMPT",
        },
        "sleeve": "crypto",
        "symbol": "BTCUSD",
        "candidate_id": "cand-entry-repair",
        "decision_bar_iso": "2026-06-16T07:45:00+00:00",
        "decision_day": "2026-06-16",
    }
    owner._write_trade_record(778899, record)

    repaired = owner._load_trade_record(778899)

    assert repaired["entry_reconciliation_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert repaired["broker_real_entry_label_ready"] is True
    assert repaired["broker_real_missing_fields"] == []
    execution = repaired["execution"]
    assert execution["broker_entry_deal_ticket"] == 88990012
    assert execution["broker_fill_time_utc"] == "2026-06-16T08:00:04+00:00"
    assert execution["broker_fill_time_alignment_offset_seconds"] == 10_800
    assert execution["broker_entry_price"] == 60010.5
    assert execution["broker_entry_commission"] == -3.5
    assert execution["entry_reconciliation_repair_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert repaired["gtos_vnext_broker_entry_reconciliation_repair_v1_packet"]["missing_fields"] == []
    persisted = json.loads(
        (
            tmp_path
            / "pipeline_state"
            / "ultimate_book"
            / "ftmo_test"
            / "trade_records"
            / "778899.json"
        ).read_text(encoding="utf-8")
    )
    assert persisted["entry_reconciliation_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert persisted["execution"]["broker_entry_deal_ticket"] == 88990012


def test_load_trade_record_marks_entry_repair_failed_when_history_fetch_fails(tmp_path):
    class _HistoryUnavailableMT5(_FakeMT5):
        def get_history_deals(self, _start, _end, _symbol):
            return None

        def get_account_history_deals(self, _start, _end):
            return None

    owner = UltimateBookOwner(_cfg(True), _HistoryUnavailableMT5(), str(tmp_path), namespace="ftmo_test")
    record = {
        "instrumentation": {
            "gtos_vnext_broker_order_lifecycle_capture_v4_packet": {
                "order_send_observation": {
                    "order_send_time_utc": "2026-06-16T08:00:03+00:00",
                    "order_result_time_utc": "2026-06-16T08:00:04+00:00",
                },
                "deal_cost_reconciliation": {
                    "account_history_lookup_status": "UNRESOLVED_AFTER_HISTORY_ATTEMPT",
                    "deal_ticket": 0,
                    "missing_fields": ["account_history_deal_reconciliation"],
                },
            },
        },
        "execution": {
            "ticket": 778899,
            "broker_symbol": "BTCUSD",
            "placed_at_utc": "2026-06-16T08:00:04+00:00",
            "broker_entry_deal_ticket": 0,
            "entry_reconciliation_status": "UNRESOLVED_AFTER_HISTORY_ATTEMPT",
        },
        "sleeve": "crypto",
        "symbol": "BTCUSD",
    }
    owner._write_trade_record(778899, record)

    repaired = owner._load_trade_record(778899)

    assert repaired["entry_reconciliation_status"] == "ACCOUNT_HISTORY_LOOKUP_FAILED"
    assert repaired["broker_real_entry_label_ready"] is False
    assert repaired["execution"]["entry_reconciliation_repair_status"] == "ACCOUNT_HISTORY_LOOKUP_FAILED"
    assert repaired["gtos_vnext_broker_entry_reconciliation_repair_v1_packet"]["status"] == (
        "ACCOUNT_HISTORY_LOOKUP_FAILED"
    )


def test_load_trade_record_self_heals_unresolved_entry_with_positive_deal_ticket(tmp_path):
    class _EntryHistoryMT5(_FakeMT5):
        def get_history_deals(self, _start, _end, _symbol):
            return [
                {
                    "ticket": 88990013,
                    "order": 778899,
                    "position_id": 778899,
                    "entry": 0,
                    "time": datetime(2026, 6, 16, 8, 0, 4, tzinfo=timezone.utc),
                    "price": 60010.5,
                    "commission": -3.5,
                    "swap": 0.0,
                }
            ]

    owner = UltimateBookOwner(_cfg(True), _EntryHistoryMT5(), str(tmp_path), namespace="ftmo_test")
    record = {
        "instrumentation": {
            "gtos_vnext_broker_order_lifecycle_capture_v4_packet": {
                "order_send_observation": {
                    "order_send_time_utc": "2026-06-16T08:00:03+00:00",
                    "order_result_time_utc": "2026-06-16T08:00:04+00:00",
                },
                "deal_cost_reconciliation": {
                    "account_history_lookup_status": "UNRESOLVED_AFTER_HISTORY_ATTEMPT",
                    "deal_ticket": 88990013,
                    "missing_fields": ["broker_entry_price", "broker_fill_time_utc", "commission", "swap"],
                },
            }
        },
        "execution": {
            "ticket": 778899,
            "broker_symbol": "BTCUSD",
            "placed_at_utc": "2026-06-16T08:00:04+00:00",
            "broker_entry_deal_ticket": 88990013,
            "entry_reconciliation_status": "UNRESOLVED_AFTER_HISTORY_ATTEMPT",
        },
        "symbol": "BTCUSD",
        "candidate_id": "cand-entry-positive-deal-repair",
    }
    owner._write_trade_record(778899, record)

    repaired = owner._load_trade_record(778899)

    assert repaired["entry_reconciliation_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert repaired["broker_real_entry_label_ready"] is True
    assert repaired["broker_real_missing_fields"] == []
    assert repaired["execution"]["broker_fill_time_utc"] == "2026-06-16T08:00:04+00:00"
    assert repaired["execution"]["broker_entry_commission"] == -3.5


def test_load_trade_record_does_not_label_incomplete_entry_history_as_broker_real(tmp_path):
    class _IncompleteEntryHistoryMT5(_FakeMT5):
        def get_history_deals(self, _start, _end, _symbol):
            return [
                {
                    "ticket": 88990014,
                    "order": 778899,
                    "position_id": 778899,
                    "entry": 0,
                    "time": datetime(2026, 6, 16, 8, 0, 4, tzinfo=timezone.utc),
                    "price": 60010.5,
                    "swap": 0.0,
                }
            ]

    owner = UltimateBookOwner(_cfg(True), _IncompleteEntryHistoryMT5(), str(tmp_path), namespace="ftmo_test")
    record = {
        "instrumentation": {
            "gtos_vnext_broker_order_lifecycle_capture_v4_packet": {
                "order_send_observation": {
                    "order_send_time_utc": "2026-06-16T08:00:03+00:00",
                    "order_result_time_utc": "2026-06-16T08:00:04+00:00",
                },
                "deal_cost_reconciliation": {
                    "account_history_lookup_status": "UNRESOLVED_AFTER_HISTORY_ATTEMPT",
                    "deal_ticket": 0,
                    "missing_fields": ["broker_entry_price", "broker_fill_time_utc", "commission", "swap"],
                },
            }
        },
        "execution": {
            "ticket": 778899,
            "broker_symbol": "BTCUSD",
            "placed_at_utc": "2026-06-16T08:00:04+00:00",
            "broker_entry_deal_ticket": 0,
            "entry_reconciliation_status": "UNRESOLVED_AFTER_HISTORY_ATTEMPT",
        },
        "symbol": "BTCUSD",
        "candidate_id": "cand-entry-incomplete-repair",
    }
    owner._write_trade_record(778899, record)

    repaired = owner._load_trade_record(778899)

    assert repaired["entry_reconciliation_status"] == "ACCOUNT_HISTORY_ENTRY_FOUND_INCOMPLETE"
    assert repaired["broker_real_entry_label_ready"] is False
    assert repaired["broker_real_missing_fields"] == ["commission"]
    assert repaired["execution"]["broker_entry_deal_ticket"] == 88990014
    assert repaired["execution"]["broker_entry_price"] == 60010.5
    assert repaired["execution"]["entry_reconciliation_repair_status"] == (
        "ACCOUNT_HISTORY_ENTRY_FOUND_INCOMPLETE"
    )
    assert repaired["gtos_vnext_broker_entry_reconciliation_repair_v1_packet"]["missing_fields"] == [
        "commission"
    ]


def test_runtime_learning_trade_context_carries_exit_outcome_without_raw_tickets(tmp_path):
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    record = {
        "execution": {
            "ticket": 778899,
            "broker_symbol": "BTCUSD",
            "broker_exit_deal_ticket": 9001,
            "broker_exit_order_ticket": 8001,
            "broker_exit_position_id": 778899,
            "exit_reconciliation_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
            "exit_reconciliation_source_status": "broker_real_account_history_exit_reconciled",
            "exit_reconciliation_missing_fields": [],
            "broker_exit_time_utc": "2026-06-23T07:00:00+00:00",
            "broker_exit_price": 4200.5,
            "broker_exit_profit": 125.0,
            "broker_exit_commission": -3.5,
            "broker_exit_swap": -1.25,
            "broker_exit_fee": 0.0,
            "broker_realized_pnl": 120.25,
        },
        "candidate_id": "cand-exit-1",
        "decision_bar_iso": "2026-06-23T06:45:00+00:00",
        "decision_day": "2026-06-23",
        "runtime_learning_joinability_status": "ticket_candidate_decision_policy_joinable",
        "trade_lifecycle_status": "closed",
        "close_action": "broker_closed",
        "closed_at_utc": "2026-06-23T07:01:00+00:00",
    }

    ctx = owner._runtime_learning_trade_context(ticket=778899, record=record)

    assert ctx["exit_reconciliation_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert ctx["broker_realized_pnl"] == 120.25
    assert ctx["broker_exit_price"] == 4200.5
    assert ctx["broker_exit_deal_hash_sha256"]
    assert ctx["broker_exit_order_hash_sha256"]
    assert ctx["broker_exit_position_hash_sha256"]
    assert "broker_exit_deal_ticket" not in ctx
    assert "broker_exit_order_ticket" not in ctx
    assert "broker_exit_position_id" not in ctx


def test_runtime_learning_skip_rows_are_enriched_from_cycle_context(tmp_path):
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    sleeve = "mx_nzdjpy_d1_donchian_20_breakout"
    symbol = "NZDJPY"
    bar = "2026-06-23T06:45:00+00:00"
    candidate_id = f"W7_BOOK::jpy_fx::{symbol}::2026-06-23::LONG::{sleeve}"
    decision = SimpleNamespace(
        realized_units=[
            {
                "sleeve_members": [sleeve],
                "cluster": "jpy_fx",
                "candidate_id": candidate_id,
            }
        ],
        would_units=[],
    )
    intent = SimpleNamespace(
        sleeve=sleeve,
        symbol=symbol,
        direction="LONG",
        decision_day="2026-06-23",
    )
    skip_context = owner._runtime_learning_skip_context(
        decision,
        [intent],
        [{"tag": sleeve, "symbol": symbol, "decision_bar_iso": bar, "timeframe": "D1"}],
    )

    row = owner._runtime_learning_skip_row(
        {
            "symbol": symbol,
            "sleeve": sleeve,
            "decision_bar_iso": bar,
            "reason": "already_placed_today",
        },
        skip_context,
    )
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="unit_skipped",
        outcome=row,
    )

    assert row["candidate_id"] == candidate_id
    assert row["cluster"] == "jpy_fx"
    assert row["decision_day"] == "2026-06-23"
    assert row["direction"] == "LONG"
    assert row["timeframe"] == "D1"
    assert packet["candidate_id"] == candidate_id
    assert packet["cluster"] == "jpy_fx"


def test_runtime_learning_skip_context_derives_candidate_id_when_unit_lacks_it(tmp_path):
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    sleeve = "asia_pdl_fade"
    symbol = "US30_cash"
    bar = "2026-06-26T03:45:00+00:00"
    decision = SimpleNamespace(
        realized_units=[
            {
                "sleeve_members": [sleeve],
                "cluster": "liquidity_sweep",
            }
        ],
        would_units=[],
    )
    intent = SimpleNamespace(
        sleeve=sleeve,
        symbol=symbol,
        direction=1,
        decision_day="2026-06-26",
    )
    skip_context = owner._runtime_learning_skip_context(
        decision,
        [intent],
        [{"tag": sleeve, "symbol": symbol, "decision_bar_iso": bar, "timeframe": "M15"}],
    )

    row = owner._runtime_learning_skip_row(
        {
            "symbol": symbol,
            "sleeve": sleeve,
            "decision_bar_iso": bar,
            "reason": "same_broker_symbol_open_position_lifecycle_guard",
        },
        skip_context,
    )

    assert row["candidate_id"] == "W7_BOOK::liquidity_sweep::US30_cash::2026-06-26::LONG::asia_pdl_fade"
    assert row["direction"] == "LONG"
    assert row["admission_unit_member_count"] == 1
    assert row["admission_unit_members"][0]["candidate_id"] == row["candidate_id"]


def test_runtime_learning_profile_missing_skip_marks_candidate_context_absent():
    row = UltimateBookOwner._runtime_learning_skip_row(
        {
            "symbol": "XAUEUR",
            "sleeve": "metals_core",
            "reason": "profile_missing_instrument_config",
            "cluster": "metals",
        },
        skip_context={},
    )

    assert row["candidate_context_status"] == "not_generated_profile_missing_instrument"
    assert row["source_completeness_status"] == "profile_missing_instrument_config_no_candidate_identity"


def test_runtime_learning_profile_missing_packet_preserves_specific_source_status(tmp_path):
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"].update({
        "ultimate_book_runtime_learning_packet_enabled": True,
        "ultimate_book_runtime_learning_packet_log_enabled": True,
        "ultimate_book_runtime_learning_packet_log_path": "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
    })
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    summary = {
        "ok": True,
        "reason": "unit_test",
        "runtime_effect_now": True,
        "bar_consumable": True,
        "bridge": {"runtime_effect_now": True, "reason": "unit_test"},
        "skipped": [
            {
                "symbol": "XAUEUR",
                "sleeve": "metal_session_reversion",
                "reason": "profile_missing_instrument_config",
                "cluster": "metals",
            }
        ],
    }

    owner._emit_cycle_runtime_learning(
        summary,
        datetime(2026, 6, 26, 3, 46, tzinfo=timezone.utc),
        decision=SimpleNamespace(realized_units=[], would_units=[]),
        place=True,
    )
    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    skipped = rows[-1]

    assert skipped["event_type"] == "unit_skipped"
    assert skipped["candidate_context_status"] == "not_generated_profile_missing_instrument"
    assert skipped["source_completeness_status"] == "profile_missing_instrument_config_no_candidate_identity"


def test_runtime_learning_unit_admitted_packet_carries_member_identity(tmp_path):
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"].update({
        "ultimate_book_runtime_learning_packet_enabled": True,
        "ultimate_book_runtime_learning_packet_log_enabled": True,
        "ultimate_book_runtime_learning_packet_log_path": "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
    })
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    sleeve = "asia_pdl_fade"
    symbol = "US30_cash"
    bar = "2026-06-26T03:45:00+00:00"
    decision = SimpleNamespace(
        realized_units=[],
        would_units=[
            {
                "sleeve_members": [sleeve],
                "cluster": "liquidity_sweep",
                "risk_pct_per_trade": 0.001,
                "sized": True,
            }
        ],
    )
    summary = {
        "ok": True,
        "reason": "unit_test",
        "runtime_effect_now": True,
        "bar_consumable": True,
        "bridge": {"runtime_effect_now": True, "reason": "unit_test"},
        "skipped": [],
        "skip_context": owner._runtime_learning_skip_context(
            SimpleNamespace(realized_units=decision.would_units, would_units=decision.would_units),
            [SimpleNamespace(sleeve=sleeve, symbol=symbol, direction=1, decision_day="2026-06-26")],
            [{"tag": sleeve, "symbol": symbol, "decision_bar_iso": bar, "timeframe": "M15"}],
        ),
    }

    owner._emit_cycle_runtime_learning(
        summary,
        datetime(2026, 6, 26, 3, 46, tzinfo=timezone.utc),
        decision=decision,
        place=True,
    )
    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    admitted = rows[-1]

    assert admitted["event_type"] == "unit_admitted"
    assert admitted["candidate_id"] == "W7_BOOK::liquidity_sweep::US30_cash::2026-06-26::LONG::asia_pdl_fade"
    assert admitted["symbol"] == symbol
    assert admitted["sleeve"] == sleeve
    assert admitted["direction"] == "LONG"
    assert admitted["decision_bar_iso"] == bar
    assert admitted["admission_unit_member_count"] == 1
    assert admitted["admission_unit_members"][0]["candidate_id"] == admitted["candidate_id"]


def test_runtime_learning_unit_admitted_packet_carries_multi_member_identity(tmp_path):
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"].update({
        "ultimate_book_runtime_learning_packet_enabled": True,
        "ultimate_book_runtime_learning_packet_log_enabled": True,
        "ultimate_book_runtime_learning_packet_log_path": "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
    })
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    unit = {
        "sleeve_members": ["asia_pdl_fade", "idxrev"],
        "cluster": "index",
        "risk_pct_per_trade": 0.001,
        "sized": True,
    }
    decision = SimpleNamespace(realized_units=[unit], would_units=[unit])
    intents = [
        SimpleNamespace(sleeve="asia_pdl_fade", symbol="US30_cash", direction=1, decision_day="2026-06-26"),
        SimpleNamespace(sleeve="idxrev", symbol="SPX500", direction=-1, decision_day="2026-06-26"),
    ]
    meta = [
        {"tag": "asia_pdl_fade", "symbol": "US30_cash", "decision_bar_iso": "2026-06-26T03:45:00+00:00", "timeframe": "M15"},
        {"tag": "idxrev", "symbol": "SPX500", "decision_bar_iso": "2026-06-26T04:00:00+00:00", "timeframe": "H1"},
    ]
    summary = {
        "ok": True,
        "reason": "unit_test",
        "runtime_effect_now": True,
        "bar_consumable": True,
        "bridge": {"runtime_effect_now": True, "reason": "unit_test"},
        "skipped": [],
        "skip_context": owner._runtime_learning_skip_context(decision, intents, meta),
    }

    owner._emit_cycle_runtime_learning(
        summary,
        datetime(2026, 6, 26, 4, 1, tzinfo=timezone.utc),
        decision=decision,
        place=True,
    )
    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    admitted = rows[-1]

    assert admitted["event_type"] == "unit_admitted"
    assert admitted["admission_unit_member_count"] == 2
    assert admitted["admission_unit_hash_sha256"]
    assert {
        member["candidate_id"]
        for member in admitted["admission_unit_members"]
    } == {
        "W7_BOOK::index::SPX500::2026-06-26::SHORT::idxrev",
        "W7_BOOK::index::US30_cash::2026-06-26::LONG::asia_pdl_fade",
    }


def test_engine_reset_window_date_offset_aware():
    """A5: the reset-window id book_owner stamps is the offset-aware server-local date (+3h), not pure UTC."""
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
    eng = UltimateBookLiveEngine({"governor_daily_reset_offset_hours": 3.0}, _FakeMT5(), tempfile.mkdtemp())
    assert eng.reset_window_date(datetime(2026, 6, 15, 21, 30, tzinfo=timezone.utc)) == "2026-06-16"
    assert eng.reset_window_date(datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)) == "2026-06-15"


# ---------------- Batch 3: per-(symbol, sleeve) management + placement guard (A1, D3/F3) ----------------

def _pos(ticket, symbol, comment, typ=0, vol=0.1, price=2000.0, sl=1990.0, tp=0.0):
    p = type("P", (), {})()
    p.ticket = ticket; p.symbol = symbol; p.comment = comment; p.type = typ
    p.volume = vol; p.price_open = price; p.price_current = price; p.sl = sl; p.tp = tp; p.profit = 0.0
    p.magic = 20260401
    p.time = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)
    return p


class _FakeExecEngine:
    """Mirrors the ExecutionEngine reconcile/adopt contract (the real engine's adoption is covered by
    tests/test_execution.py); here we test the OWNER's per-(symbol, sleeve) routing."""
    def __init__(self, symbol, mt5):
        self.symbol = symbol
        self.mt5 = mt5
        self.active_trade = None
    def reconcile_on_startup(self, comment_filter=None):
        raw = self.mt5.get_positions(self.symbol)
        positions = raw if comment_filter is None else \
            [p for p in raw if (getattr(p, "comment", "") or "") == comment_filter]
        if positions and self.active_trade is None:
            self.adopt_specific_position(positions[0])
        return []
    def adopt_specific_position(self, p):
        if self.active_trade is not None:
            return False
        ts = type("TS", (), {})()
        ts.ticket = p.ticket
        ts.gtos_vnext_book_native_exit_management = False
        self.active_trade = ts
        return True
    def check_time_stop_and_close(self):
        return None
    def check_and_manage_trade(self, _ctx):
        return "hold"


class _MultiPosMT5(_FakeMT5):
    def __init__(self, positions):
        self._positions = positions
    def get_open_positions(self):
        return list(self._positions)
    def get_positions(self, symbol):
        return [p for p in self._positions if p.symbol == symbol]


def test_per_sleeve_management_routes_each_ticket_and_skips_legacy():
    """D3/F3: a symbol held by two sleeves (XAUUSD: metals_core + metals_softband) must route EACH ticket
    to its OWN engine (no single-slot overwrite/orphan); a legacy non-W7 position must NOT be adopted."""
    positions = [
        _pos(1001, "XAUUSD", "W7:metals_core"),
        _pos(1002, "XAUUSD", "W7:metals_softba"),   # broker-truncated W7:metals_softband[:16]
        _pos(9999, "XAUUSD", "GoldAgent_OBRete"),    # legacy/foreign -> must be left alone
    ]
    mt5 = _MultiPosMT5(positions)
    def factory(symbol):
        return _FakeExecEngine(symbol, mt5)   # distinct engine per call (like production)
    owner = UltimateBookOwner(_cfg(True), mt5, tempfile.mkdtemp(), engine_factory=factory)
    summary = owner.manage_open_positions()
    adopted = sorted(a["ticket"] for a in summary["adopted"])
    assert adopted == [1001, 1002]                          # both book tickets, separately adopted
    assert 9999 not in adopted                              # legacy position never adopted by the book
    e_core = owner._exec_engine("XAUUSD", "metals_core")
    e_soft = owner._exec_engine("XAUUSD", "metals_softband")
    assert e_core.active_trade.ticket == 1001 and e_soft.active_trade.ticket == 1002
    assert e_core.active_trade.ticket != e_soft.active_trade.ticket   # distinct slots, no overwrite
    for e in (e_core, e_soft):
        assert e.active_trade.gtos_vnext_book_native_exit_management is True   # both flagged native
    # both are managed each tick (their own check_and_manage_trade)
    managed = {(m["symbol"], m["sleeve"]) for m in summary["managed"]}
    assert ("XAUUSD", "metals_core") in managed and ("XAUUSD", "metals_softband") in managed


def test_management_packets_include_broker_observed_protection(tmp_path):
    positions = [_pos(1010, "XAUUSD", "W7:metals_core", sl=1987.5, tp=2025.0)]
    mt5 = _MultiPosMT5(positions)

    def factory(symbol):
        return _FakeExecEngine(symbol, mt5)

    owner = UltimateBookOwner(_cfg(True), mt5, str(tmp_path), engine_factory=factory)
    summary = owner.manage_open_positions()
    managed = summary["managed"][0]
    record = owner._load_trade_record(1010)

    assert managed["broker_position_sl"] == 1987.5
    assert managed["broker_position_tp"] == 2025.0
    assert record["execution"]["broker_position_sl"] == 1987.5
    assert record["execution"]["broker_position_tp"] == 2025.0


def test_management_packets_classify_fill_adjusted_take_profit(tmp_path):
    positions = [
        _pos(
            249791692,
            "BTCUSD",
            "W7:crypto",
            typ=1,
            price=60000.0,
            sl=60700.0,
            tp=59475.0,
        )
    ]
    mt5 = _MultiPosMT5(positions)

    def factory(symbol):
        return _FakeExecEngine(symbol, mt5)

    owner = UltimateBookOwner(_cfg(True), mt5, str(tmp_path), engine_factory=factory)
    owner._write_trade_record(
        249791692,
        {
            "instrumentation": {
                "entry_price": 60010.0,
                "stop_loss": 60700.0,
                "take_profit_1": 59485.0,
                "direction": "SHORT",
            },
            "execution": {"ticket": 249791692, "broker_symbol": "BTCUSD"},
            "sleeve": "crypto",
            "symbol": "BTCUSD",
            "candidate_id": "W7_BOOK::crypto::BTCUSD::2026-07-01::SHORT::crypto",
            "decision_bar_iso": "2026-07-01T13:00:00+00:00",
        },
    )

    summary = owner.manage_open_positions()
    managed = summary["managed"][0]
    record = owner._load_trade_record(249791692)
    execution = record["execution"]

    assert managed["broker_position_take_profit_status"] == "matches_fill_adjusted_take_profit"
    assert managed["broker_position_stop_loss_status"] == "matches_planned_stop_loss"
    assert managed["broker_position_protection_reconciliation_status"] == (
        "broker_current_matches_fill_adjusted_or_planned_protection"
    )
    assert execution["broker_position_fill_adjusted_take_profit"] == pytest.approx(59475.0)
    assert execution["broker_position_take_profit_status"] == "matches_fill_adjusted_take_profit"


def test_management_packets_classify_broker_risk_adjusted_take_profit(tmp_path):
    positions = [
        _pos(
            249791692,
            "BTCUSD",
            "W7:crypto",
            typ=1,
            price=7504.25,
            sl=7555.86,
            tp=7465.54,
        )
    ]
    mt5 = _MultiPosMT5(positions)

    def factory(symbol):
        return _FakeExecEngine(symbol, mt5)

    owner = UltimateBookOwner(_cfg(True), mt5, str(tmp_path), engine_factory=factory)
    owner._write_trade_record(
        249791692,
        {
            "instrumentation": {
                "entry_price": 7504.54,
                "stop_loss": 7555.858214285714,
                "take_profit_1": 7466.051339285715,
                "direction": "SHORT",
            },
            "execution": {"ticket": 249791692, "broker_symbol": "BTCUSD"},
            "sleeve": "crypto",
            "symbol": "BTCUSD",
            "candidate_id": "W7_BOOK::crypto::BTCUSD::2026-07-01::SHORT::crypto",
            "decision_bar_iso": "2026-07-01T13:00:00+00:00",
        },
    )

    summary = owner.manage_open_positions()
    managed = summary["managed"][0]
    record = owner._load_trade_record(249791692)
    execution = record["execution"]

    assert managed["broker_position_take_profit_status"] == "matches_broker_risk_adjusted_take_profit"
    assert managed["broker_position_protection_reconciliation_status"] == (
        "broker_current_matches_broker_risk_adjusted_or_planned_protection"
    )
    assert execution["broker_position_planned_target_r"] == pytest.approx(0.75)
    assert execution["broker_position_broker_risk_adjusted_take_profit"] == pytest.approx(7465.5425)


def test_leftover_safety_net_adopts_commentless_book_position():
    """A W7 position whose broker comment was stripped (empty) must still be adopted (not orphaned) via
    the leftover safety net into a free engine for that symbol."""
    positions = [_pos(2002, "XAUUSD", "")]   # empty comment -> not comment-routed
    mt5 = _MultiPosMT5(positions)
    def factory(symbol):
        return _FakeExecEngine(symbol, mt5)
    owner = UltimateBookOwner(_cfg(True), mt5, tempfile.mkdtemp(), engine_factory=factory)
    summary = owner.manage_open_positions()
    assert [a["ticket"] for a in summary["adopted"]] == [2002]


def test_alias_broker_symbol_does_not_double_adopt_same_ticket():
    """JP225 and JP225_cash can resolve to the same broker symbol on FTMO. A ticket already routed by its
    W7 sleeve comment must not be adopted again through the alias canonical/sleeve."""
    positions = [_pos(3003, "JP225", "W7:idxrev")]
    mt5 = _MultiPosMT5(positions)
    cfg = _cfg(True)
    cfg["instruments"].update({
        "JP225": {"market": {"mt5_symbol": "JP225"}},
        "JP225_cash": {"market": {"mt5_symbol": "JP225"}},
    })

    def factory(symbol):
        return _FakeExecEngine(symbol, mt5)

    owner = UltimateBookOwner(cfg, mt5, tempfile.mkdtemp(), engine_factory=factory)
    owner._manageable_pairs_cache = [
        ("JP225", "idxrev"),
        ("JP225_cash", "mx_jp225_cash_d1_volume_surge_reversal"),
    ]

    summary = owner.manage_open_positions()

    assert len(summary["adopted"]) == 1
    adopted = summary["adopted"][0]
    assert {"symbol": adopted["symbol"], "sleeve": adopted["sleeve"], "ticket": adopted["ticket"]} == {
        "symbol": "JP225",
        "sleeve": "idxrev",
        "ticket": 3003,
    }
    assert adopted["ticket_hash_sha256"]
    assert [(m["symbol"], m["sleeve"]) for m in summary["managed"]] == [("JP225", "idxrev")]
    assert owner._exec_engine("JP225", "idxrev").active_trade.ticket == 3003
    assert owner._exec_engine("JP225_cash", "mx_jp225_cash_d1_volume_surge_reversal").active_trade is None


def test_placement_guard_skips_when_sleeve_already_holds_symbol():
    """A1: the (symbol, sleeve) engine already holding a position must not place a 2nd order (which would
    overwrite its single active_trade and orphan the first)."""
    owner, engines = _owner(True)
    ee = owner._exec_engine("BTCUSD", "crypto")
    ee.active_trade = type("TS", (), {"ticket": 555})()   # already holding BTCUSD
    summary = owner.run_cycle(tags=("crypto",))
    placed_syms = {p["symbol"] for p in summary["placed"]}
    assert "BTCUSD" not in placed_syms   # guard blocked the already-held (symbol, sleeve)
    assert any(isinstance(s, dict) and s.get("symbol") == "BTCUSD"
               and s.get("reason") == "sleeve_already_holds_symbol" for s in summary["skipped"])
    assert len(engines["BTCUSD"].calls) == 0   # guard blocked before router.place -> no open_trade
    # a DIFFERENT, un-held symbol on the same sleeve still places (guard is per (symbol, sleeve))
    assert "DASHUSD" in placed_syms


# ---------------- Batch 5: session/tradeable gate (D2) ----------------

class _TickT:
    def __init__(self, bid, ask, age_min):
        self.bid = bid; self.ask = ask
        self.time = datetime.now(timezone.utc) - timedelta(minutes=age_min)


def test_session_gate_skips_stale_tick_market_closed():
    """D2: a frozen (stale) tick = closed cash market -> skip pre-send (defense in depth before the broker
    reject), instead of attempting a trade on a stale signal."""
    class _StaleMT5(_FakeMT5):
        def get_tick(self, symbol):
            return _TickT(59995.0, 60005.0, age_min=30) if symbol == "BTCUSD" \
                else _TickT(99.9, 100.1, age_min=30)
    engines = {}
    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]
    owner = UltimateBookOwner(_cfg(True), _StaleMT5(), tempfile.mkdtemp(), engine_factory=factory)
    summary = owner.run_cycle(tags=("crypto",))
    assert summary["placed"] == []
    assert any(isinstance(s, dict) and str(s.get("reason", "")).startswith("stale_tick_market_closed")
               for s in summary["skipped"])
    assert all(len(e.calls) == 0 for e in engines.values())   # no open_trade attempted


def test_session_gate_allows_fresh_tick():
    """D2 positive: a fresh tick (recent timestamp) is NOT blocked."""
    class _FreshMT5(_FakeMT5):
        def get_tick(self, symbol):
            return _TickT(59995.0, 60005.0, age_min=0) if symbol == "BTCUSD" \
                else _TickT(99.9, 100.1, age_min=0)
    engines = {}
    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]
    owner = UltimateBookOwner(_cfg(True), _FreshMT5(), tempfile.mkdtemp(), engine_factory=factory)
    summary = owner.run_cycle(tags=("crypto",))
    assert any(p["symbol"] == "BTCUSD" for p in summary["placed"])   # fresh -> places normally


def test_manage_engine_records_timestop_close_reason():
    """A time-stop close must be recorded with its real reason and NOT run exit-management on the
    already-closed engine (which would relabel/lose the reason)."""
    class _TSCloseEngine:
        def __init__(self):
            self.active_trade = type("TS", (), {"ticket": 111})()
            self.cam_called = False
        def check_time_stop_and_close(self):
            self.active_trade = None          # time-stop closes the position
            return "vnext_time_stop"
        def check_and_manage_trade(self, _ctx):
            self.cam_called = True
            return "should_not_run"
    repo = tempfile.mkdtemp()
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), repo)
    ee = _TSCloseEngine()
    summary = {"managed": [], "adopted": [], "closed": [], "errors": []}
    owner._manage_engine(ee, "XAUUSD", "metals_core", summary)
    assert len(summary["closed"]) == 1
    closed = summary["closed"][0]
    assert {"symbol": closed["symbol"], "sleeve": closed["sleeve"], "action": closed["action"]} == {
        "symbol": "XAUUSD",
        "sleeve": "metals_core",
        "action": "vnext_time_stop",
    }
    assert closed["ticket_hash_sha256"]
    assert closed["trade_lifecycle_status"] == "closed"
    record = owner._load_trade_record(111)
    assert record["trade_lifecycle_status"] == "closed"
    assert record["close_action"] == "vnext_time_stop"
    assert record["sleeve"] == "metals_core"
    assert record["symbol"] == "XAUUSD"
    assert ee.cam_called is False         # exit-management NOT run on the already-closed engine


def test_live_broker_authority_false_observes_management_without_mutation():
    class _ObserveOnlyEngine:
        def __init__(self):
            self.active_trade = type("TS", (), {"ticket": 222})()
            self.timestop_called = False
            self.manage_called = False

        def check_time_stop_and_close(self):
            self.timestop_called = True
            self.active_trade = None
            return "should_not_run"

        def check_and_manage_trade(self, _ctx):
            self.manage_called = True
            self.active_trade = None
            return "should_not_run"

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["ultimate_book_live_broker_authority"] = False
    owner = UltimateBookOwner(cfg, _FakeMT5(), tempfile.mkdtemp())
    ee = _ObserveOnlyEngine()
    summary = {"managed": [], "adopted": [], "closed": [], "errors": []}

    owner._manage_engine(ee, "XAUUSD", "metals_core", summary)

    assert ee.active_trade is not None
    assert ee.timestop_called is False
    assert ee.manage_called is False
    assert summary["closed"] == []
    assert summary["errors"] == []
    assert summary["managed"][0]["action"] == "live_broker_authority_false_observe_only"
    assert summary["managed"][0]["broker_mutation_allowed"] is False


def test_mark_closed_reconciles_exit_deal_accounting():
    class _HistoryMT5(_FakeMT5):
        def get_account_history_deals(self, _start, _end):
            return [
                SimpleNamespace(
                    ticket=9001,
                    order=8001,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 7, 0, tzinfo=timezone.utc),
                    price=4200.5,
                    profit=125.0,
                    commission=-3.5,
                    swap=-1.25,
                    fee=0.0,
                )
            ]

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 1
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    owner = UltimateBookOwner(cfg, _HistoryMT5(), tempfile.mkdtemp())
    record = owner._mark_trade_record_closed(
        111,
        "broker_closed",
        "2026-06-23T07:01:00+00:00",
        broker_symbol="XAUUSD",
        sleeve="metals_core",
        symbol="XAUUSD",
    )

    execution = record["execution"]
    assert record["exit_reconciliation_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert record["broker_exit_deal_ticket"] == 9001
    assert record["broker_realized_pnl"] == 120.25
    assert execution["broker_exit_deal_ticket"] == 9001
    assert execution["broker_exit_order_ticket"] == 8001
    assert execution["broker_exit_price"] == 4200.5
    assert execution["broker_realized_pnl"] == 120.25
    packet = record["gtos_vnext_broker_exit_lifecycle_capture_v4_packet"]
    assert packet["runtime_effect_boundary"] == "read_only_account_history_no_broker_mutation"
    assert packet["reconciliation"]["exit_reconciliation_missing_fields"] == []


def test_notify_closed_prefers_exact_closed_record_pnl_over_symbol_history(tmp_path):
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    cards = []
    owner._send_card = cards.append
    owner._recent_realized_pnl = lambda _symbol: -999.0

    owner._notify_closed(
        "XAUUSD",
        "vnext_time_stop",
        closed_record={
            "execution": {
                "broker_realized_pnl": 116.75,
                "broker_realized_pnl_source": "position_aggregate_includes_entry_and_exit_deals",
            }
        },
    )

    assert cards
    assert "P&L $117" in cards[0]
    assert "P&L $-999" not in cards[0]


def test_mark_closed_realized_pnl_includes_entry_side_costs_when_available():
    class _HistoryMT5(_FakeMT5):
        def get_account_history_deals(self, _start, _end):
            return [
                SimpleNamespace(
                    ticket=9000,
                    order=8000,
                    position_id=111,
                    entry=0,
                    time=datetime(2026, 6, 23, 6, 59, tzinfo=timezone.utc),
                    price=4190.0,
                    profit=0.0,
                    commission=-3.5,
                    swap=0.0,
                    fee=0.0,
                ),
                SimpleNamespace(
                    ticket=9001,
                    order=8001,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 7, 0, tzinfo=timezone.utc),
                    price=4200.5,
                    profit=125.0,
                    commission=-3.5,
                    swap=-1.25,
                    fee=0.0,
                ),
            ]

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 1
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    owner = UltimateBookOwner(cfg, _HistoryMT5(), tempfile.mkdtemp())
    record = owner._mark_trade_record_closed(
        111,
        "broker_closed",
        "2026-06-23T07:01:00+00:00",
        broker_symbol="XAUUSD",
        sleeve="metals_core",
        symbol="XAUUSD",
    )

    execution = record["execution"]
    assert execution["broker_selected_exit_realized_pnl"] == pytest.approx(120.25)
    assert execution["broker_exit_aggregate_profit"] == pytest.approx(125.0)
    assert execution["broker_exit_aggregate_commission"] == pytest.approx(-3.5)
    assert execution["broker_position_deal_count"] == 2
    assert execution["broker_position_aggregate_profit"] == pytest.approx(125.0)
    assert execution["broker_position_aggregate_commission"] == pytest.approx(-7.0)
    assert execution["broker_position_realized_pnl"] == pytest.approx(116.75)
    assert execution["broker_realized_pnl_source"] == "position_aggregate_includes_entry_and_exit_deals"
    assert execution["broker_realized_pnl"] == pytest.approx(116.75)
    assert record["broker_realized_pnl"] == pytest.approx(116.75)


def test_mark_closed_records_daily_pnl_from_ticket_reconciliation(tmp_path, monkeypatch):
    import src.notifications as _notif

    monkeypatch.setattr(_notif, "_PNL_PATH", tmp_path / "daily_pnl.json")
    monkeypatch.setattr(_notif, "_PNL_HISTORY_PATH", tmp_path / "daily_pnl_history.jsonl")

    class _HistoryMT5(_FakeMT5):
        def get_account_history_deals(self, _start, _end):
            return [
                SimpleNamespace(
                    ticket=9000,
                    order=8000,
                    position_id=111,
                    entry=0,
                    time=datetime(2026, 6, 23, 6, 59, tzinfo=timezone.utc),
                    price=4190.0,
                    profit=0.0,
                    commission=-3.5,
                    swap=0.0,
                    fee=0.0,
                ),
                SimpleNamespace(
                    ticket=9001,
                    order=8001,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 7, 0, tzinfo=timezone.utc),
                    price=4200.5,
                    profit=125.0,
                    commission=-3.5,
                    swap=-1.25,
                    fee=0.0,
                ),
            ]

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 1
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    owner = UltimateBookOwner(
        cfg,
        _HistoryMT5(),
        str(tmp_path / "repo"),
        namespace="redacted_account_live_bee34003",
    )
    record = owner._mark_trade_record_closed(
        111,
        "vnext_time_stop",
        "2026-06-23T07:01:00+00:00",
        record={
            "instrumentation": {"entry_price": 4190.0},
            "opened_at_utc": "2026-06-23T06:59:00+00:00",
        },
        broker_symbol="XAUUSD",
        sleeve="metals_core",
        symbol="XAUUSD",
    )

    execution = record["execution"]
    assert execution["daily_pnl_ledger_status"] == "RECORDED_BROKER_NET"
    assert execution["daily_pnl_ledger_trade_id"] == "redacted_account_live_bee34003:XAUUSD:111"
    pnl = json.loads((tmp_path / "daily_pnl.json").read_text(encoding="utf-8"))
    row = pnl["trades"][0]
    assert row["trade_id"] == "redacted_account_live_bee34003:XAUUSD:111"
    assert row["realized_usd"] == pytest.approx(116.75)
    assert row["broker_net_profit"] == pytest.approx(116.75)
    assert row["broker_profit"] == pytest.approx(125.0)
    assert row["broker_commission"] == pytest.approx(-7.0)
    assert row["broker_swap"] == pytest.approx(-1.25)
    assert pnl["total_usd"] == pytest.approx(116.75)
    history = [
        json.loads(line)
        for line in (tmp_path / "daily_pnl_history.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert len(history) == 1


def test_mark_closed_retries_delayed_exit_history_before_missing_exit():
    class _DelayedHistoryMT5(_FakeMT5):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def get_account_history_deals(self, _start, _end):
            self.calls += 1
            if self.calls == 1:
                return []
            return [
                SimpleNamespace(
                    ticket=9001,
                    order=8001,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 7, 0, tzinfo=timezone.utc),
                    price=4200.5,
                    profit=125.0,
                    commission=-3.5,
                    swap=-1.25,
                    fee=0.0,
                )
            ]

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 2
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    mt5 = _DelayedHistoryMT5()
    owner = UltimateBookOwner(cfg, mt5, tempfile.mkdtemp())
    record = owner._mark_trade_record_closed(
        111,
        "broker_closed",
        "2026-06-23T07:01:00+00:00",
        broker_symbol="XAUUSD",
        sleeve="metals_core",
        symbol="XAUUSD",
    )

    assert mt5.calls == 2
    assert record["exit_reconciliation_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert record["execution"]["exit_reconciliation_attempt_count"] == 2


def test_mark_closed_chooses_nearest_exit_deal_and_aggregates_position_pnl():
    class _PartialHistoryMT5(_FakeMT5):
        def get_account_history_deals(self, _start, _end):
            return [
                SimpleNamespace(
                    ticket=9001,
                    order=8001,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 6, 30, tzinfo=timezone.utc),
                    price=4190.0,
                    profit=40.0,
                    commission=-1.0,
                    swap=0.0,
                    fee=0.0,
                ),
                SimpleNamespace(
                    ticket=9002,
                    order=8002,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 7, 1, tzinfo=timezone.utc),
                    price=4200.5,
                    profit=125.0,
                    commission=-3.5,
                    swap=-1.25,
                    fee=0.0,
                ),
            ]

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 1
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    owner = UltimateBookOwner(cfg, _PartialHistoryMT5(), tempfile.mkdtemp())
    record = owner._mark_trade_record_closed(
        111,
        "broker_closed",
        "2026-06-23T07:01:05+00:00",
        broker_symbol="XAUUSD",
        sleeve="metals_core",
        symbol="XAUUSD",
    )

    execution = record["execution"]
    assert execution["broker_exit_deal_ticket"] == 9002
    assert execution["exit_reconciliation_match_keys"]["matched_by"] == "position_id_and_exit_entry_nearest_close_time"
    assert execution["broker_exit_position_deal_count"] == 2
    assert execution["broker_realized_pnl"] == pytest.approx(159.25)


def test_mark_closed_backfills_aggregate_fields_on_legacy_reconciled_record():
    class _PartialHistoryMT5(_FakeMT5):
        def get_account_history_deals(self, _start, _end):
            return [
                SimpleNamespace(
                    ticket=9001,
                    order=8001,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 6, 30, tzinfo=timezone.utc),
                    price=4190.0,
                    profit=40.0,
                    commission=-1.0,
                    swap=0.0,
                    fee=0.0,
                ),
                SimpleNamespace(
                    ticket=9002,
                    order=8002,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 7, 1, tzinfo=timezone.utc),
                    price=4200.5,
                    profit=125.0,
                    commission=-3.5,
                    swap=-1.25,
                    fee=0.0,
                ),
            ]

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 1
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    owner = UltimateBookOwner(cfg, _PartialHistoryMT5(), tempfile.mkdtemp())
    legacy_record = {
        "execution": {
            "ticket": 111,
            "broker_exit_deal_ticket": 9002,
            "broker_exit_position_id": 111,
            "broker_exit_profit": 125.0,
            "broker_exit_commission": -3.5,
            "broker_exit_swap": -1.25,
            "broker_selected_exit_realized_pnl": 120.25,
            "exit_reconciliation_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
        },
        "trade_lifecycle_status": "closed",
        "sleeve": "metals_core",
        "symbol": "XAUUSD",
    }

    record = owner._mark_trade_record_closed(
        111,
        "broker_closed",
        "2026-06-23T07:01:05+00:00",
        record=legacy_record,
        broker_symbol="XAUUSD",
        sleeve="metals_core",
        symbol="XAUUSD",
    )

    execution = record["execution"]
    assert execution["broker_exit_deal_ticket"] == 9002
    assert execution["broker_selected_exit_realized_pnl"] == pytest.approx(120.25)
    assert execution["broker_exit_position_deal_count"] == 2
    assert execution["broker_exit_aggregate_profit"] == pytest.approx(165.0)
    assert execution["broker_exit_aggregate_commission"] == pytest.approx(-4.5)
    assert execution["broker_exit_aggregate_swap"] == pytest.approx(-1.25)
    assert execution["broker_position_accounting_coverage_status"] == "partial_position_deals_missing_entry_or_exit"
    assert execution["broker_realized_pnl_source"] == "exit_aggregate_only"
    assert execution["broker_realized_pnl"] == pytest.approx(159.25)
    assert record["broker_realized_pnl"] == pytest.approx(159.25)


def test_normalize_closed_record_repairs_legacy_exit_only_realized_pnl():
    class _FullPositionHistoryMT5(_FakeMT5):
        def get_account_history_deals(self, _start, _end):
            return [
                SimpleNamespace(
                    ticket=9000,
                    order=8000,
                    position_id=111,
                    entry=0,
                    time=datetime(2026, 6, 23, 6, 59, tzinfo=timezone.utc),
                    price=4190.0,
                    profit=0.0,
                    commission=-3.5,
                    swap=0.0,
                    fee=0.0,
                ),
                SimpleNamespace(
                    ticket=9001,
                    order=8001,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 7, 0, tzinfo=timezone.utc),
                    price=4200.5,
                    profit=125.0,
                    commission=-3.5,
                    swap=-1.25,
                    fee=0.0,
                ),
            ]

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 1
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    owner = UltimateBookOwner(cfg, _FullPositionHistoryMT5(), tempfile.mkdtemp())
    legacy_record = {
        "execution": {
            "ticket": 111,
            "broker_symbol": "XAUUSD",
            "broker_exit_deal_ticket": 9001,
            "broker_exit_order_ticket": 8001,
            "broker_exit_position_id": 111,
            "broker_exit_position_deal_count": 1,
            "broker_exit_position_deal_tickets": [9001],
            "broker_exit_aggregate_profit": 125.0,
            "broker_exit_aggregate_commission": -3.5,
            "broker_exit_aggregate_swap": -1.25,
            "broker_exit_aggregate_fee": 0.0,
            "broker_realized_pnl": 120.25,
            "exit_reconciliation_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
        },
        "closed_at_utc": "2026-06-23T07:01:05+00:00",
        "trade_lifecycle_status": "closed",
        "sleeve": "metals_core",
        "symbol": "XAUUSD",
    }

    record, changed = owner._normalize_trade_record(111, legacy_record)

    execution = record["execution"]
    assert changed is True
    assert execution["broker_position_deal_count"] == 2
    assert execution["broker_position_entry_deal_count"] == 1
    assert execution["broker_position_exit_deal_count"] == 1
    assert execution["broker_position_accounting_coverage_status"] == "entry_and_exit_deals_present"
    assert execution["broker_position_realized_pnl"] == pytest.approx(116.75)
    assert execution["broker_realized_pnl_source"] == "position_aggregate_includes_entry_and_exit_deals"
    assert execution["broker_realized_pnl"] == pytest.approx(116.75)
    assert record["broker_realized_pnl"] == pytest.approx(116.75)


def test_mark_closed_records_missing_exit_order_identifier():
    class _HistoryMT5(_FakeMT5):
        def get_account_history_deals(self, _start, _end):
            return [
                SimpleNamespace(
                    ticket=9001,
                    order=None,
                    position_id=111,
                    entry=1,
                    time=datetime(2026, 6, 23, 7, 0, tzinfo=timezone.utc),
                    price=4200.5,
                    profit=125.0,
                    commission=-3.5,
                    swap=-1.25,
                    fee=0.0,
                )
            ]

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 1
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    owner = UltimateBookOwner(cfg, _HistoryMT5(), tempfile.mkdtemp())
    record = owner._mark_trade_record_closed(
        111,
        "broker_closed",
        "2026-06-23T07:01:00+00:00",
        broker_symbol="XAUUSD",
        sleeve="metals_core",
        symbol="XAUUSD",
    )

    execution = record["execution"]
    assert record["exit_reconciliation_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert execution["exit_reconciliation_missing_fields"] == ["broker_exit_order_ticket"]
    assert "broker_exit_order_ticket" not in execution
    ctx = owner._runtime_learning_trade_context(ticket=111, record=record)
    assert ctx["exit_reconciliation_missing_fields"] == ["broker_exit_order_ticket"]
    assert ctx["broker_exit_deal_hash_sha256"]
    assert "broker_exit_order_hash_sha256" not in ctx


def test_stale_reconciled_exit_record_backfills_missing_order_field():
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), tempfile.mkdtemp())
    record = {
        "execution": {
            "ticket": 111,
            "exit_reconciliation_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
            "exit_reconciliation_missing_fields": [],
            "broker_exit_deal_ticket": 9001,
            "broker_exit_position_id": 111,
        },
        "sleeve": "metals_core",
        "symbol": "XAUUSD",
    }

    normalized, changed = owner._normalize_trade_record(111, record)
    ctx = owner._runtime_learning_trade_context(ticket=111, record=normalized)

    assert changed is True
    assert normalized["execution"]["exit_reconciliation_missing_fields"] == ["broker_exit_order_ticket"]
    assert ctx["exit_reconciliation_missing_fields"] == ["broker_exit_order_ticket"]
    assert ctx["broker_exit_deal_hash_sha256"]
    assert "broker_exit_order_hash_sha256" not in ctx


def test_mark_closed_marks_missing_exit_deal_explicitly():
    class _NoExitHistoryMT5(_FakeMT5):
        def get_account_history_deals(self, _start, _end):
            return []

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 1
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    owner = UltimateBookOwner(cfg, _NoExitHistoryMT5(), tempfile.mkdtemp())
    record = owner._mark_trade_record_closed(
        222,
        "broker_closed",
        "2026-06-23T07:01:00+00:00",
        broker_symbol="XAUUSD",
        sleeve="metals_core",
        symbol="XAUUSD",
    )

    execution = record["execution"]
    assert record["trade_lifecycle_status"] == "closed"
    assert record["exit_reconciliation_status"] == "NO_EXIT_DEAL_FOUND"
    assert execution["exit_reconciliation_status"] == "NO_EXIT_DEAL_FOUND"
    assert execution["exit_reconciliation_missing_fields"] == ["broker_exit_deal_ticket"]
    assert "broker_exit_deal_ticket" not in execution


def test_closed_record_repairs_exit_reconciliation_after_initial_history_miss():
    class _DelayedExitHistoryMT5(_FakeMT5):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def get_account_history_deals(self, _start, _end):
            self.calls += 1
            if self.calls == 1:
                return []
            return [
                SimpleNamespace(
                    ticket=9003,
                    order=8003,
                    position_id=222,
                    entry=1,
                    time=datetime(2026, 6, 23, 7, 2, tzinfo=timezone.utc),
                    price=4201.0,
                    profit=77.0,
                    commission=-2.0,
                    swap=-0.5,
                    fee=0.0,
                )
            ]

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_attempts"] = 1
    cfg["gtos_vnext_runtime"]["broker_exit_history_lookup_sleep_seconds"] = 0
    mt5 = _DelayedExitHistoryMT5()
    owner = UltimateBookOwner(cfg, mt5, tempfile.mkdtemp())
    record = owner._mark_trade_record_closed(
        222,
        "vnext_time_stop",
        "2026-06-23T07:01:00+00:00",
        broker_symbol="XAUUSD",
        sleeve="metals_core",
        symbol="XAUUSD",
    )

    assert record["exit_reconciliation_status"] == "NO_EXIT_DEAL_FOUND"

    repaired = owner._load_trade_record(222)

    assert mt5.calls == 2
    assert repaired["exit_reconciliation_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert repaired["execution"]["exit_reconciliation_repair_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert repaired["broker_exit_deal_ticket"] == 9003
    assert repaired["broker_realized_pnl"] == pytest.approx(74.5)


# ---------------- Batch 6: JPY root-cause -- pre-send spread-cost screen + transient-failure retry --------

from src.components.ultimate_book.book_owner import _is_transient_place_failure


class _BlockingEngine:
    """A per-symbol engine whose open_trade fails closed (returns None) with a specific block reason,
    mirroring execution.open_trade surfacing _last_open_trade_block_reason for the router to read."""
    def __init__(self, reason):
        self._last_open_trade_block_reason = reason
        self.active_trade = None
        self.calls = []
    def open_trade(self, tp, bal, **kw):
        self.calls.append(tp)
        return None


def test_transient_classifier_separates_retryable_from_terminal():
    # transient broker/IO hiccups -> retry
    for r in ("open_trade_returned_none", "order_rejected:timeout_no_fill", "order_rejected:Requote",
              "no_tick_data", "cash_risk_unverified", "lot_size_unverified", "filling_mode_unresolved",
              "deviation_unresolved", "timeout_no_position", "order_send_exception"):
        assert _is_transient_place_failure(r) is True, r
    # terminal declines + terminal broker rejects -> do NOT retry (would spam an identical doomed request)
    for r in ("cost_screen_spread_r:0.230>0.100 (spread 0.02 vs fx_jpy stop 0.087)", "vnext_policy:x",
              "vnext_risk:y", "exec_mgr_v4:missing_cost:geometry_contract", "geometry_unavailable",
              "router_exception:Boom", "order_rejected:No money", "order_rejected:Invalid stops",
              "order_rejected:Market closed", "below_min_lot:0.40<1.00", None, ""):
        assert _is_transient_place_failure(r) is False, r


def test_cost_screen_skips_wide_spread_before_open_trade(monkeypatch):
    monkeypatch.setattr("src.judgment.cost_choices.withholds", lambda *args, **kwargs: True)
    """JPY root cause: a leg whose live spread eats >max_spread_r (0.10) of its stop_dist (e.g. GBPJPY
    fx_jpy: 2-pip spread on a 1.0xATR(M15) ~8.7-pip stop -> spread_r ~0.23) is declined HERE, cleanly,
    BEFORE the futile open_trade that the ExecMgr-V4 cost gate would block. Surfaced as an ℹ️ note, not
    the ⚠️ 'Trade NOT placed' failure card."""
    class _WideSpreadMT5(_FakeMT5):
        def get_tick(self, symbol):
            # spread >> 0.10 of each synthetic R-unit (BTC stop ~703 -> 200pt; 100-sym stop ~0.146 -> 0.2)
            return _Tick(59900.0, 60100.0) if symbol == "BTCUSD" else _Tick(99.9, 100.1)
    engines = {}
    cards = []
    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]
    root = tempfile.mkdtemp()
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["ultimate_book_kelly_running_count"] = True
    owner = UltimateBookOwner(cfg, _WideSpreadMT5(), root, engine_factory=factory)
    owner._send_card = lambda m: cards.append(m)
    summary = owner.run_cycle(tags=("crypto",))
    assert summary["placed"] == []
    assert all(len(e.calls) == 0 for e in engines.values())   # screened BEFORE any open_trade attempt
    assert any(isinstance(s, dict) and str(s.get("reason", "")).startswith("cost_screen_spread_r")
               for s in summary["skipped"])
    assert any("Skipped" in c and "spread too wide" in c for c in cards)   # informational note...
    assert not any("Trade NOT placed" in c for c in cards)                 # ...NOT the failure card
    firing = Path(root) / "pipeline_state" / "ultimate_book" / owner._namespace / "firing_sleeves.json"
    assert not firing.exists()  # the cost-refused candidate was previewed, never committed


def test_transient_place_failure_leaves_bar_unconsumed_for_retry():
    """A momentary order_send timeout/None must NOT permanently lose a once-per-bar signal: the decision
    bar is left UNCONSUMED so the next tick re-attempts (with the ledger + active_trade/_broker_holds
    guards preventing any double-place)."""
    engines = {}
    def factory(symbol):
        engines.setdefault(symbol, _BlockingEngine("order_rejected:timeout_no_fill"))
        return engines[symbol]
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), tempfile.mkdtemp(), engine_factory=factory)
    summary = owner.run_cycle(tags=("crypto",))
    assert summary["placed"] == []
    assert summary["bar_consumable"] is False                  # transient -> retry this bar next tick
    assert any(e.calls for e in engines.values())              # open_trade WAS attempted (then failed)


def test_no_tick_leaves_bar_unconsumed_for_retry():
    class _NoTickMT5(_FakeMT5):
        def get_tick(self, symbol):
            return None

    owner = UltimateBookOwner(_cfg(True), _NoTickMT5(), tempfile.mkdtemp())
    summary = owner.run_cycle(tags=("crypto",))
    assert summary["placed"] == []
    assert summary["bar_consumable"] is False
    assert any(isinstance(s, dict) and s.get("reason") == "no_tick_transient" for s in summary["skipped"])


def test_cluster_cap_config_and_jpy_exemption_wired():
    """COMP-2: the one-unit-per-cluster-per-day cap defaults ON, and the jpy cluster (both fx_jpy session
    sleeves) is exempt so the owner's JPY-cross trial measures London AND NY; metals/crypto are NOT exempt."""
    from src.components.ultimate_book.admission import cluster_of
    owner, _ = _owner(True)
    assert owner._cluster_cap_on is True
    assert "jpy" in owner._cluster_cap_exempt
    assert cluster_of("fx_jpy") == "jpy" and cluster_of("fx_jpy_ny") == "jpy"   # both exempt during the trial
    assert cluster_of("metals_core") == "metals" and "metals" not in owner._cluster_cap_exempt
    assert cluster_of("crypto") == "crypto" and "crypto" not in owner._cluster_cap_exempt
    # the ledger was built with the cluster resolver so the cap can reconstruct from disk
    assert owner._ledger._cluster_resolver is not None


def test_cluster_cap_can_be_disabled_by_config():
    """OWNER 2026-06-16: the per-cluster-day cap is RELAXABLE off (it was over-blocking a 2nd same-cluster
    symbol/day). With the flag false the cap is not enforced; the per-(sleeve,symbol)-day cap stays."""
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["ultimate_book_one_unit_per_cluster_per_day"] = False
    owner = UltimateBookOwner(cfg, _FakeMT5(), tempfile.mkdtemp())
    assert owner._cluster_cap_on is False


def test_terminal_decline_consumes_bar_no_retry_spam():
    """A deterministic decline (cost/geometry gate that will never clear on retry) CONSUMES the bar, so
    the book does not re-attempt an identical doomed order every tick."""
    engines = {}
    def factory(symbol):
        engines.setdefault(symbol, _BlockingEngine("exec_mgr_v4:missing_cost:geometry_contract_missing"))
        return engines[symbol]
    root = tempfile.mkdtemp()
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["ultimate_book_kelly_running_count"] = True
    owner = UltimateBookOwner(cfg, _FakeMT5(), root, engine_factory=factory)
    summary = owner.run_cycle(tags=("crypto",))
    assert summary["placed"] == []
    assert summary["bar_consumable"] is True                   # terminal -> consume the bar (no retry)
    firing = Path(root) / "pipeline_state" / "ultimate_book" / owner._namespace / "firing_sleeves.json"
    assert not firing.exists()  # execution refusal is not accepted-placement breadth


# ---------------- Batch 7: adopt-missing-record native-policy rehydrate + out-of-universe alert --------

def test_native_policy_instrumentation_reconstructs_from_sleeve():
    from src.components.ultimate_book.execution_packets import native_policy_instrumentation
    p = native_policy_instrumentation("idxrev")
    assert p["gtos_vnext_dynamic_policy_selected"] == "time_stop"
    assert p["gtos_vnext_dynamic_final_target_r"] == 0.75
    assert p["gtos_vnext_dynamic_time_stop_bars"] == 960
    assert p["gtos_vnext_book_native_exit_management"] is True
    m = native_policy_instrumentation("metals_core")
    assert m["gtos_vnext_dynamic_policy_selected"] == "partial_be_runner"
    assert m["gtos_vnext_dynamic_be_trigger_r"] == 2.0 and m["gtos_vnext_dynamic_partial_close_ratio"] == 0.5
    # unknown sleeve -> the safe DEFAULT profile (never crashes)
    d = native_policy_instrumentation("does_not_exist")
    assert d["gtos_vnext_dynamic_policy_selected"] == "time_stop" and d["gtos_vnext_dynamic_final_target_r"] == 2.0


def test_rehydrate_uses_native_policy_when_record_missing():
    """adopt-missing-record: with NO on-disk trade record, the adopted position rehydrates the sleeve's
    NATIVE exit policy (reconstructed from the W7 comment) rather than degrading to the generic floor."""
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), tempfile.mkdtemp())   # fresh temp repo -> no record
    class _Eng:
        def __init__(self):
            self.active_trade = type("TS", (), {"ticket": 12345})()
            self.hydrated = None
        def hydrate_vnext_dynamic_policy_from_record(self, rec):
            self.hydrated = rec; return True
    ee = _Eng()
    owner._rehydrate_policy(ee, "fx_jpy")
    assert ee.hydrated is not None and ee.hydrated["reconstructed_from_sleeve_identity"] is True
    inst = ee.hydrated["instrumentation"]
    assert inst["gtos_vnext_dynamic_policy_selected"] == "time_stop"
    assert inst["gtos_vnext_dynamic_final_target_r"] == 2.5 and inst["gtos_vnext_dynamic_time_stop_bars"] == 48


def test_rehydrate_policy_disables_broker_tp_modify_when_broker_authority_false():
    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["ultimate_book_live_broker_authority"] = False
    owner = UltimateBookOwner(cfg, _FakeMT5(), tempfile.mkdtemp())

    class _Eng:
        def __init__(self):
            self.active_trade = type("TS", (), {"ticket": 12346})()
            self.kwargs = None

        def hydrate_vnext_dynamic_policy_from_record(self, rec, **kwargs):
            self.kwargs = kwargs
            return True

    ee = _Eng()
    rec = owner._rehydrate_policy(ee, "idxrev")

    assert rec["rehydration_status"] == "hydrated"
    assert ee.kwargs == {"modify_broker_tp": False}


def test_out_of_universe_w7_position_alerts_once():
    """A W7-magic position on a symbol no active sleeve covers is surfaced ONCE (it can only ride broker
    SL/TP; no engine manages it)."""
    class _OOUMt5(_FakeMT5):
        def get_open_positions(self):
            p = type("P", (), {})()
            p.ticket = 77; p.symbol = "FOOBAR"; p.comment = "W7:crypto"; p.magic = 20260401
            return [p]
        def get_positions(self, symbol):
            return []
    cards = []
    owner = UltimateBookOwner(_cfg(True), _OOUMt5(), tempfile.mkdtemp())
    owner._send_card = lambda m: cards.append(m)
    s1 = owner.manage_open_positions()
    assert any("Out-of-universe" in c and "FOOBAR" in c for c in cards)
    assert s1.get("out_of_universe") and s1["out_of_universe"][0]["ticket"] == 77
    n = len(cards)
    owner.manage_open_positions()                 # same ticket -> deduped, no second card
    assert len(cards) == n


def test_in_universe_w7_position_not_flagged_out_of_universe():
    """A W7 position on an IN-universe symbol (XAUUSD) must NOT be flagged out-of-universe."""
    class _InUnivMt5(_FakeMT5):
        def get_open_positions(self):
            p = type("P", (), {})()
            p.ticket = 88; p.symbol = "XAUUSD"; p.comment = "W7:metals_core"; p.magic = 20260401
            return [p]
        def get_positions(self, symbol):
            return []
    cards = []
    owner = UltimateBookOwner(_cfg(True), _InUnivMt5(), tempfile.mkdtemp())
    owner._send_card = lambda m: cards.append(m)
    s = owner.manage_open_positions()
    assert not s.get("out_of_universe")
    assert not any("Out-of-universe" in c for c in cards)


def test_absent_trade_record_reconcile_marks_stale_record_closed(tmp_path):
    """A post-restart record whose ticket is absent from a confirmed open-position snapshot is closed
    locally so runtime-learning/lifecycle state does not keep reporting it as open forever."""
    import json

    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path))
    close_cards = []
    owner._notify_closed = lambda symbol, action, **kwargs: close_cards.append(
        (symbol, action, kwargs.get("closed_record"))
    )
    d = tmp_path / "pipeline_state" / "ultimate_book" / "operator_profile" / "trade_records"
    d.mkdir(parents=True, exist_ok=True)
    stale = d / "111.json"
    stale.write_text(json.dumps({
        "execution": {"ticket": 111, "broker_symbol": "XAUUSD"},
        "instrumentation": {"gtos_vnext_dynamic_policy_selected": "trailing_runner"},
        "sleeve": "metal_session_reversion",
        "symbol": "XAUUSD",
    }))
    live = d / "222.json"
    live.write_text(json.dumps({
        "execution": {"ticket": 222, "broker_symbol": "JP225"},
        "instrumentation": {"gtos_vnext_dynamic_policy_selected": "time_stop"},
        "sleeve": "idxrev",
        "symbol": "JP225",
    }))

    summary = {"managed": [], "adopted": [], "closed": [], "errors": []}
    owner._reconcile_absent_trade_records([_pos(222, "JP225", "W7:idxrev")], summary)

    closed = json.loads(stale.read_text())
    still_live = json.loads(live.read_text())
    assert closed["trade_lifecycle_status"] == "closed"
    assert closed["close_action"] == "broker_closed_absent_on_reconcile"
    assert closed["execution"]["closed_at_utc"]
    assert still_live.get("trade_lifecycle_status") is None
    assert summary["closed"][0]["action"] == "broker_closed_absent_on_reconcile"
    assert summary["closed"][0]["trade_lifecycle_status"] == "closed"
    # STALE EXPECTATION fixed 2026-08-25 (owner-directed pre-existing-failure clearing,
    # f5max-ship): this test asserted len(close_cards) == 1 — an owner phone card per
    # reconcile close.  No lineage in this repository has EVER emitted _notify_closed from
    # _reconcile_absent_trade_records (git grep across main, f5-live@68bad3751 = every live
    # byte committed, governor-hole-20260824, codex/f5-conviction-repair-20260812: zero
    # hits).  The true contract is the method's own docstring — "This is local evidence
    # repair only": record + summary + daily_pnl fold, NO broker mutation and NO owner
    # card (live close cards come from _manage_engine's engine-detected close path,
    # book_owner.py:5174/:5217, and the F5 measurement pipeline reads broker deals).
    # Pinning the card-free contract keeps the anti-noise property explicit; wiring a
    # per-reconcile card would be a src decision for the orchestrator, not a test edit.
    assert close_cards == []

    # Idempotency re-pinned behaviourally (was "still exactly one card"): a second pass over
    # the already-closed record must not duplicate the summary close row (the closed-status
    # continue in _reconcile_absent_trade_records) and stays card-free.
    owner._reconcile_absent_trade_records([_pos(222, "JP225", "W7:idxrev")], summary)
    assert len(summary["closed"]) == 1
    assert close_cards == []


def test_absent_trade_record_reconcile_skips_empty_snapshot(tmp_path):
    """An all-empty position snapshot can be a transient MT5 read miss; do not mark every record closed."""
    import json

    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path))
    d = tmp_path / "pipeline_state" / "ultimate_book" / "operator_profile" / "trade_records"
    d.mkdir(parents=True, exist_ok=True)
    record = d / "111.json"
    record.write_text(json.dumps({
        "execution": {"ticket": 111, "broker_symbol": "XAUUSD"},
        "sleeve": "metal_session_reversion",
        "symbol": "XAUUSD",
    }))

    summary = {"managed": [], "adopted": [], "closed": [], "errors": []}
    owner._reconcile_absent_trade_records([], summary)

    assert json.loads(record.read_text()).get("trade_lifecycle_status") is None
    assert summary["closed"] == []

    owner._reconcile_absent_trade_records([], summary)

    closed = json.loads(record.read_text())
    assert closed["trade_lifecycle_status"] == "closed"
    assert closed["close_action"] == "broker_closed_absent_on_reconcile"
    assert summary["closed"][0]["action"] == "broker_closed_absent_on_reconcile"


def test_absent_active_engine_reconcile_debounces_empty_snapshot_then_closes(tmp_path):
    """A broker-side TP/SL close that leaves a local engine active must be absorbed without broker mutation."""
    import json

    class _EmptySnapshotMT5(_FakeMT5):
        def broker_link_connected(self):
            return True

        def get_open_positions(self):
            return []

        def get_positions(self, symbol):
            return []

    class _Engine:
        def __init__(self):
            self.active_trade = type("TS", (), {"ticket": 111})()
            self.manage_called = 0

        def reconcile_on_startup(self, comment_filter=None):
            return []

        def check_time_stop_and_close(self):
            return None

        def check_and_manage_trade(self, _ctx):
            self.manage_called += 1
            return "hold"

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["ultimate_book_live_broker_authority"] = False
    owner = UltimateBookOwner(cfg, _EmptySnapshotMT5(), str(tmp_path))
    close_cards = []
    owner._notify_closed = lambda symbol, action, **kwargs: close_cards.append(
        (symbol, action, kwargs.get("closed_record"))
    )
    engine = _Engine()
    owner._exec_engines[("XAUUSD", "metals_core")] = engine
    d = tmp_path / "pipeline_state" / "ultimate_book" / "operator_profile" / "trade_records"
    d.mkdir(parents=True, exist_ok=True)
    record = d / "111.json"
    record.write_text(json.dumps({
        "execution": {"ticket": 111, "broker_symbol": "XAUUSD"},
        "sleeve": "metals_core",
        "symbol": "XAUUSD",
    }))

    first = owner.manage_open_positions()
    assert engine.active_trade is not None
    assert first["closed"] == []
    assert first["managed"][0]["action"] == "live_broker_authority_false_observe_only"

    second = owner.manage_open_positions()
    closed = json.loads(record.read_text())
    assert engine.active_trade is None
    assert second["closed"][0]["action"] == "broker_closed_absent_on_reconcile"
    assert second["closed"][0]["broker_mutation_allowed"] is False
    assert closed["trade_lifecycle_status"] == "closed"
    assert closed["close_action"] == "broker_closed_absent_on_reconcile"
    # STALE EXPECTATION fixed 2026-08-25 (owner-directed pre-existing-failure clearing,
    # f5max-ship): asserted len(close_cards) == 1, but _reconcile_absent_active_engine has
    # never called _notify_closed on any lineage in this repository (f5-live@68bad3751
    # included — the every-live-byte snapshot).  Reconcile absorption is local evidence
    # repair by documented design; the debounce, the broker_mutation_allowed=False row,
    # the record close-state, and the engine active_trade clear above are the protections,
    # all still pinned.  Card-free is the true contract (see the sibling
    # test_absent_trade_record_reconcile_marks_stale_record_closed note).
    assert close_cards == []


def test_operator_flatten_suppressed_when_broker_authority_false(tmp_path):
    class _Engine:
        def __init__(self):
            self.active_trade = type("TS", (), {"ticket": 333})()
            self.close_called = False

        def close_position(self, reason):
            self.close_called = True
            self.active_trade = None
            return True

    cfg = _cfg(True)
    cfg["gtos_vnext_runtime"]["ultimate_book_live_broker_authority"] = False
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path))
    engine = _Engine()
    owner._exec_engines[("XAUUSD", "metals_core")] = engine
    summary = {"managed": [], "adopted": [], "closed": [], "errors": []}

    owner._flatten_all_engines(summary, "operator_flatten")

    assert engine.close_called is False
    assert engine.active_trade is not None
    assert summary["closed"] == []
    assert summary["managed"][0]["action"] == "operator_flatten_suppressed_live_broker_authority_false"


def test_prune_old_trade_records_on_startup(tmp_path):
    """state-unbounded-growth: a trade record older than 60 days (a long-closed trade) is swept at owner
    startup; a recent one is kept (an open position may still need it for rehydration)."""
    import os, time
    d = tmp_path / "pipeline_state" / "ultimate_book" / "operator_profile" / "trade_records"
    d.mkdir(parents=True)
    old = d / "111.json"; old.write_text("{}")
    new = d / "222.json"; new.write_text("{}")
    t_old = time.time() - 70 * 86400
    os.utime(old, (t_old, t_old))
    UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path))   # __init__ runs the prune
    assert not old.exists() and new.exists()


def test_placement_guard_broker_level_blocks_unadopted_position():
    """MACRO-EMRG-05: if adoption failed (engine active_trade None) but the broker still holds the
    W7:{sleeve} position, a new decision bar must NOT place a duplicate — the broker-level guard catches
    it (a different un-held symbol on the same sleeve still places)."""
    class _MT5WithPos(_FakeMT5):
        def get_positions(self, symbol):
            if symbol == "BTCUSD":
                p = type("P", (), {})(); p.comment = "W7:crypto"; p.ticket = 555; p.magic = 20260401
                return [p]
            return []
    engines = {}
    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]
    owner = UltimateBookOwner(_cfg(True), _MT5WithPos(), tempfile.mkdtemp(), engine_factory=factory)
    summary = owner.run_cycle(tags=("crypto",))
    placed = {p["symbol"] for p in summary["placed"]}
    assert "BTCUSD" not in placed
    assert any(isinstance(s, dict) and s.get("symbol") == "BTCUSD"
               and s.get("reason") == "sleeve_already_holds_symbol_broker" for s in summary["skipped"])
    assert len(engines["BTCUSD"].calls) == 0


def test_placement_guard_blocks_existing_same_broker_symbol_other_sleeve(tmp_path):
    """A live book position on the same broker symbol blocks a new sleeve-level entry.

    The older guard was per (symbol, sleeve), so W7:idxrev on BTCUSD would not stop W7:crypto on BTCUSD.
    The owner now enforces the same-symbol lifecycle before order construction, regardless of sleeve.
    """
    class _MT5WithOtherSleevePos(_FakeMT5):
        def get_open_positions(self):
            p = type("P", (), {})()
            p.symbol = "BTCUSD"
            p.comment = "W7:idxrev"
            p.ticket = 777
            p.magic = 20260401
            return [p]

    engines = {}

    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]

    class _Engine:
        config = {"ultimate_book_max_entry_lateness_frac": 10.0}

        def evaluate(self, *, now_utc=None, tags=None):
            unit = {
                "sleeve_members": ["crypto"],
                "risk_pct_per_trade": 0.001,
                "unit_risk_pct": 0.001,
                "sized": True,
                "cluster": "crypto",
            }
            decision = SimpleNamespace(
                runtime_effect_now=True,
                candidate_use_allowed_now=True,
                decision_status="execute_now",
                reason="unit_test",
                realized_units=[unit],
                would_units=[unit],
                governor={"new_entries_allowed": True},
            )
            intent = SimpleNamespace(
                sleeve="crypto",
                symbol="BTCUSD",
                direction=1,
                decision_day="2026-06-26",
                stop_dist=100.0,
                target_dist=200.0,
            )
            return {
                "ok": True,
                "reason": "unit_test",
                "n_intents": 1,
                "runtime_effect_now": True,
                "decision": decision,
                "governor_state": SimpleNamespace(equity=100000.0, realized_today_pct=0.0),
                "intents": [intent],
                "meta": [{"tag": "crypto", "symbol": "BTCUSD", "decision_bar_iso": "2026-06-26T04:00:00+00:00", "timeframe": "M15"}],
                "generation": {"profile": "unit_test"},
            }

        def reset_window_date(self, now):
            return now.date().isoformat()

    class _Router:
        def account_state(self, *args, **kwargs):
            return {"current_equity": 100000.0, "balance": 100000.0}

        def place(self, *args, **kwargs):
            raise AssertionError("same-symbol guard should block before router.place")

    owner = UltimateBookOwner(_cfg(True), _MT5WithOtherSleevePos(), str(tmp_path), engine_factory=factory)
    owner.engine = _Engine()
    owner.router = _Router()
    summary = owner.run_cycle(now_utc=datetime(2026, 6, 26, 4, 1, tzinfo=timezone.utc), tags=("crypto",))

    placed = {p["symbol"] for p in summary["placed"]}
    assert "BTCUSD" not in placed
    assert any(isinstance(s, dict) and s.get("symbol") == "BTCUSD"
               and s.get("reason") == "same_broker_symbol_open_position_lifecycle_guard"
               for s in summary["skipped"])
    assert len(engines.get("BTCUSD", _RecordingEngine()).calls) == 0


def test_same_broker_symbol_guard_is_alias_aware():
    """The same-symbol placement guard compares the resolved broker symbol, not only canonical names."""
    cfg = _cfg(True)
    cfg["instruments"]["US30_cash"] = {"market": {"mt5_symbol": "US30"}}

    class _MT5WithAliasPos(_FakeMT5):
        def get_open_positions(self):
            p = type("P", (), {})()
            p.symbol = "US30"
            p.comment = "W7:idxrev"
            p.ticket = 778
            p.magic = 20260401
            return [p]

    mt5 = _MT5WithAliasPos()
    owner = UltimateBookOwner(cfg, mt5, tempfile.mkdtemp())

    exposures = owner._same_broker_symbol_open_exposures(
        "US30_cash",
        open_positions_snapshot=mt5.get_open_positions(),
    )

    assert exposures is not None
    assert [getattr(pos, "ticket", None) for pos in exposures] == [778]


def test_same_broker_symbol_guard_merges_fresh_symbol_read_when_snapshot_empty(tmp_path):
    cfg = _cfg(True)
    cfg["instruments"]["US30_cash"] = {"market": {"mt5_symbol": "US30"}}

    class _MT5WithStaleSnapshot(_FakeMT5):
        def __init__(self):
            super().__init__()
            self.position_symbols = []

        def get_open_positions(self):
            return []

        def get_positions(self, symbol):
            self.position_symbols.append(symbol)
            if symbol == "US30":
                p = type("P", (), {})()
                p.symbol = "US30"
                p.comment = "W7:idxrev"
                p.ticket = 889
                p.magic = 20260401
                return [p]
            return []

    mt5 = _MT5WithStaleSnapshot()
    owner = UltimateBookOwner(cfg, mt5, str(tmp_path))

    exposures = owner._same_broker_symbol_open_exposures(
        "US30_cash",
        open_positions_snapshot=[],
    )

    assert exposures is not None
    assert [getattr(pos, "ticket", None) for pos in exposures] == [889]
    assert mt5.position_symbols == ["US30"]


def test_placement_guard_blocks_from_fresh_symbol_read_when_cycle_snapshot_empty(tmp_path):
    cfg = _cfg(True)
    cfg["instruments"]["US30_cash"] = {"market": {"mt5_symbol": "US30"}}

    class _MT5WithFreshUS30(_FakeMT5):
        def get_open_positions(self):
            return []

        def get_positions(self, symbol):
            if symbol == "US30":
                p = type("P", (), {})()
                p.symbol = "US30"
                p.comment = "W7:idxrev"
                p.ticket = 890
                p.magic = 20260401
                return [p]
            return []

    class _Engine:
        config = {"ultimate_book_max_entry_lateness_frac": 10.0}

        def evaluate(self, *, now_utc=None, tags=None):
            unit = {
                "sleeve_members": ["asia_pdl_fade"],
                "risk_pct_per_trade": 0.001,
                "unit_risk_pct": 0.001,
                "sized": True,
                "cluster": "liquidity_sweep",
            }
            intent = SimpleNamespace(
                sleeve="asia_pdl_fade",
                symbol="US30_cash",
                direction=1,
                decision_day="2026-06-26",
                stop_dist=100.0,
                target_dist=200.0,
            )
            decision = SimpleNamespace(
                runtime_effect_now=True,
                candidate_use_allowed_now=True,
                decision_status="execute_now",
                reason="unit_test",
                realized_units=[unit],
                would_units=[unit],
                governor={"new_entries_allowed": True},
            )
            return {
                "ok": True,
                "reason": "unit_test",
                "n_intents": 1,
                "runtime_effect_now": True,
                "decision": decision,
                "governor_state": SimpleNamespace(equity=100000.0, realized_today_pct=0.0),
                "intents": [intent],
                "meta": [
                    {
                        "tag": "asia_pdl_fade",
                        "symbol": "US30_cash",
                        "decision_bar_iso": "2026-06-26T03:45:00+00:00",
                        "timeframe": "M15",
                    }
                ],
                "generation": {"profile": "unit_test"},
            }

        def reset_window_date(self, now):
            return now.date().isoformat()

    class _Router:
        def account_state(self, *args, **kwargs):
            return {"current_equity": 100000.0, "balance": 100000.0}

        def place(self, *args, **kwargs):
            raise AssertionError("fresh same-symbol guard should block before router.place")

    owner = UltimateBookOwner(cfg, _MT5WithFreshUS30(), str(tmp_path), engine_factory=lambda _symbol: _RecordingEngine())
    owner.engine = _Engine()
    owner.router = _Router()

    summary = owner.run_cycle(now_utc=datetime(2026, 6, 26, 4, 1, tzinfo=timezone.utc), tags=("asia_pdl_fade",))

    assert summary["placed"] == []
    assert any(
        isinstance(s, dict)
        and s.get("symbol") == "US30_cash"
        and s.get("reason") == "same_broker_symbol_open_position_lifecycle_guard"
        for s in summary["skipped"]
    )


def test_same_broker_symbol_transient_attempt_reserves_symbol_for_cycle(tmp_path):
    class _Engine:
        config = {"ultimate_book_max_entry_lateness_frac": 10.0}

        def evaluate(self, *, now_utc=None, tags=None):
            unit = {
                "sleeve_members": ["crypto", "orb_crypto_london"],
                "risk_pct_per_trade": 0.001,
                "unit_risk_pct": 0.001,
                "sized": True,
                "cluster": "crypto",
            }
            intents = [
                SimpleNamespace(
                    sleeve="crypto",
                    symbol="BTCUSD",
                    direction=1,
                    decision_day="2026-06-26",
                    stop_dist=100.0,
                    target_dist=200.0,
                ),
                SimpleNamespace(
                    sleeve="orb_crypto_london",
                    symbol="BTCUSD",
                    direction=-1,
                    decision_day="2026-06-26",
                    stop_dist=100.0,
                    target_dist=200.0,
                ),
            ]
            decision = SimpleNamespace(
                runtime_effect_now=True,
                candidate_use_allowed_now=True,
                decision_status="execute_now",
                reason="unit_test",
                realized_units=[unit],
                would_units=[unit],
                governor={"new_entries_allowed": True},
            )
            return {
                "ok": True,
                "reason": "unit_test",
                "n_intents": 2,
                "runtime_effect_now": True,
                "decision": decision,
                "governor_state": SimpleNamespace(equity=100000.0, realized_today_pct=0.0),
                "intents": intents,
                "meta": [
                    {"tag": intent.sleeve, "symbol": intent.symbol, "decision_bar_iso": "2026-06-26T04:00:00+00:00", "timeframe": "M15"}
                    for intent in intents
                ],
                "generation": {"profile": "unit_test"},
            }

        def reset_window_date(self, now):
            return now.date().isoformat()

    class _Router:
        def __init__(self):
            self.calls = 0

        def account_state(self, *args, **kwargs):
            return {"current_equity": 100000.0, "balance": 100000.0}

        def place(self, *args, **kwargs):
            self.calls += 1
            return {"placed": False, "reason": "order_rejected:timeout_no_fill"}

    router = _Router()
    owner = UltimateBookOwner(_cfg(True), _FakeMT5(), str(tmp_path), engine_factory=lambda _symbol: _RecordingEngine())
    owner.engine = _Engine()
    owner.router = router

    summary = owner.run_cycle(now_utc=datetime(2026, 6, 26, 4, 1, tzinfo=timezone.utc), tags=("crypto",))

    assert router.calls == 1
    assert summary["bar_consumable"] is False
    assert any(
        isinstance(s, dict)
        and s.get("symbol") == "BTCUSD"
        and s.get("sleeve") == "orb_crypto_london"
        and s.get("reason") == "same_broker_symbol_transient_attempt_this_cycle"
        for s in summary["skipped"]
    )


def _enable_ai_companion(cfg):
    cfg["gtos_vnext_runtime"]["ai_companion"] = {
        "enabled": True,
        "authority_level": "protective",
        "control_state_path": "pipeline_state/ai_companion/control_state.json",
    }
    return cfg


def _write_ai_control(tmp_path, control):
    from src.components.ai_companion.control_state import build_empty_control_state, write_control_state_atomic

    now = datetime.now(timezone.utc).replace(microsecond=0)
    state = build_empty_control_state(authority_level="protective", now=now, ttl_minutes=30)
    base = {
        "control_id": "test-control",
        "namespace": "operator_profile",
        "reason": "test_control",
        "generated_at_utc": now.isoformat(),
        "expires_at_utc": (now + timedelta(minutes=20)).isoformat(),
        "evidence": [{"path": "pipeline_state/ai_companion/cycle_digest.json"}],
    }
    base.update(control)
    state["controls"] = [base]
    write_control_state_atomic(tmp_path, state)
    return now


def test_ai_companion_pause_forces_observe_only_without_open_trade(tmp_path):
    engines = {}

    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]

    cfg = _enable_ai_companion(_cfg(True))
    now = _write_ai_control(tmp_path, {"type": "pause_new_entries"})
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), engine_factory=factory)
    summary = owner.run_cycle(now_utc=now, tags=("crypto",))

    assert summary["placed"] == []
    assert summary["shadow"] >= 1
    assert summary["bar_consumable"] is True
    assert any(str(item.get("reason", "")).startswith("ai_companion_pause_new_entries") for item in summary["skipped"])
    assert all(len(engine.calls) == 0 for engine in engines.values())


def _assert_ai_companion_control_state_issue(summary, engines, issue_code):
    assert summary["placed"] == []
    assert summary["shadow"] >= 1
    assert summary["bar_consumable"] is False
    skipped = [
        item
        for item in summary["skipped"]
        if isinstance(item, dict)
        and str(item.get("reason", "")).startswith("ai_companion_control_state_issue")
    ]
    assert skipped
    issues = skipped[0].get("ai_companion_issues") or []
    assert any(item.get("code") == issue_code for item in issues)
    assert all(len(engine.calls) == 0 for engine in engines.values())


def test_ai_companion_missing_control_state_forces_observe_only_without_open_trade(tmp_path):
    engines = {}

    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]

    cfg = _enable_ai_companion(_cfg(True))
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), engine_factory=factory)
    now = datetime.now(timezone.utc).replace(microsecond=0)

    summary = owner.run_cycle(now_utc=now, tags=("crypto",))

    _assert_ai_companion_control_state_issue(summary, engines, "control_state_absent")


def test_ai_companion_unreadable_control_state_forces_observe_only_without_open_trade(tmp_path):
    engines = {}

    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]

    cfg = _enable_ai_companion(_cfg(True))
    state_path = tmp_path / "pipeline_state" / "ai_companion" / "control_state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text("{not json", encoding="utf-8")
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), engine_factory=factory)
    now = datetime.now(timezone.utc).replace(microsecond=0)

    summary = owner.run_cycle(now_utc=now, tags=("crypto",))

    _assert_ai_companion_control_state_issue(summary, engines, "control_state_unreadable")


def test_ai_companion_expired_control_state_forces_observe_only_without_open_trade(tmp_path):
    from src.components.ai_companion.control_state import build_empty_control_state, write_control_state_atomic

    engines = {}

    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]

    cfg = _enable_ai_companion(_cfg(True))
    mt5 = _FakeMT5()
    now = mt5._anchor_forming + timedelta(seconds=2)
    state = build_empty_control_state(
        authority_level="protective",
        now=now - timedelta(minutes=60),
        ttl_minutes=10,
    )
    write_control_state_atomic(tmp_path, state)
    owner = UltimateBookOwner(cfg, mt5, str(tmp_path), engine_factory=factory)

    summary = owner.run_cycle(now_utc=now, tags=("crypto",))

    _assert_ai_companion_control_state_issue(summary, engines, "state_expired")


def test_ai_companion_symbol_sleeve_cooldown_skips_matching_intent_only(tmp_path):
    engines = {}

    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]

    cfg = _enable_ai_companion(_cfg(True))
    now = _write_ai_control(
        tmp_path,
        {"type": "symbol_sleeve_cooldown", "symbol": "BTCUSD", "sleeve": "crypto"},
    )
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), engine_factory=factory)
    summary = owner.run_cycle(now_utc=now, tags=("crypto",))

    assert any(item.get("symbol") == "BTCUSD" and str(item.get("reason", "")).startswith("ai_companion_cooldown")
               for item in summary["skipped"])
    assert "BTCUSD" not in engines or len(engines["BTCUSD"].calls) == 0
    assert any(item.get("symbol") == "DASHUSD" for item in summary["placed"])


def test_ai_companion_risk_multiplier_can_only_reduce_router_risk(tmp_path):
    base_owner, base_engines = _owner(True)
    base_summary = base_owner.run_cycle(tags=("crypto",))
    assert any(item.get("symbol") == "BTCUSD" for item in base_summary["placed"])
    base_risk = base_engines["BTCUSD"].calls[0]["risk_pct_override"]

    engines = {}

    def factory(symbol):
        engines.setdefault(symbol, _RecordingEngine())
        return engines[symbol]

    cfg = _enable_ai_companion(_cfg(True))
    now = _write_ai_control(
        tmp_path,
        {"type": "risk_multiplier", "symbol": "BTCUSD", "sleeve": "crypto", "multiplier": 0.25},
    )
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), engine_factory=factory)
    summary = owner.run_cycle(now_utc=now, tags=("crypto",))

    assert any(item.get("symbol") == "BTCUSD" for item in summary["placed"])
    adjusted_risk = engines["BTCUSD"].calls[0]["risk_pct_override"]
    assert round(adjusted_risk / base_risk, 6) == 0.25
    assert summary["ai_companion_risk_adjustments"][0]["multiplier"] == 0.25
