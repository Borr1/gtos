import json
from datetime import datetime, timezone
from types import SimpleNamespace

from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.runtime_learning_packet import (
    RuntimeLearningPacketWriter,
    build_runtime_learning_packet,
    validate_runtime_learning_packet,
)


def _raw_key_seen(value, raw_key):
    if isinstance(value, dict):
        return any(k == raw_key or _raw_key_seen(v, raw_key) for k, v in value.items())
    if isinstance(value, list):
        return any(_raw_key_seen(v, raw_key) for v in value)
    return False


def test_runtime_learning_packet_hashes_ticket_and_account_identifiers():
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="unit_placed",
        bridge={"runtime_effect_now": True, "market_expansion_policy": "positive_weighted12_after_swap"},
        unit={"sleeve_members": ["ny_crypto_momentum"], "risk_pct_per_trade": 0.001},
        outcome={
            "ticket": 123456,
            "account_login": "0",
            "server": "Broker-Live",
            "password": "secret",
            "symbol": "BTCUSD",
            "sleeve": "ny_crypto_momentum",
            "placement_status": "placed",
        },
    )

    ok, issues = validate_runtime_learning_packet(packet)

    assert ok, issues
    assert not _raw_key_seen(packet, "ticket")
    assert not _raw_key_seen(packet, "account_login")
    assert packet["outcome"]["ticket_hash_sha256"]
    assert packet["outcome"]["account_login_hash_sha256"]
    assert packet["outcome"]["password_redacted"] is True
    assert packet["broker_runtime_change_status"] is False


def test_runtime_learning_validator_rejects_raw_broker_identifiers():
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="unit_placed",
        outcome={"symbol": "BTCUSD", "sleeve": "ny_crypto_momentum", "placement_status": "placed"},
    )
    packet["ticket"] = 123456

    ok, issues = validate_runtime_learning_packet(packet)

    assert ok is False
    assert any(issue.startswith("forbidden_raw_keys") for issue in issues)


def test_runtime_learning_validator_rejects_unknown_event_type_and_hash_drift():
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="unit_placed",
        outcome={"symbol": "BTCUSD", "sleeve": "ny_crypto_momentum", "placement_status": "placed"},
    )
    packet["event_type"] = "unexpected_event"

    ok, issues = validate_runtime_learning_packet(packet)

    assert ok is False
    assert "unknown_event_type:unexpected_event" in issues
    assert "source_event_hash_mismatch" in issues
    assert "packet_hash_mismatch" in issues


def test_runtime_learning_admission_reason_is_not_a_skip_reason():
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="unit_admitted",
        unit={"sleeve_members": ["ny_crypto_momentum"], "candidate_id": "cand-1"},
        outcome={
            "symbol": "BTCUSD",
            "sleeve": "ny_crypto_momentum",
            "placement_status": "admitted",
            "reason": "ultimate_book_admitted",
        },
    )

    ok, issues = validate_runtime_learning_packet(packet)

    assert ok, issues
    assert packet["skip_reason"] is None
    assert packet["decision_reason"] == "ultimate_book_admitted"
    assert packet["admission_reason"] == "ultimate_book_admitted"


def test_runtime_learning_packet_accepts_convergence_advisory():
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="unit_shadow",
        bridge={"runtime_effect_now": False, "market_expansion_policy": "positive_weighted12_after_swap"},
        unit={"sleeve_members": ["ny_crypto_momentum"], "candidate_id": "cand-1"},
        outcome={
            "symbol": "BTCUSD",
            "sleeve": "ny_crypto_momentum",
            "placement_status": "shadow",
            "candidate_id": "cand-1",
        },
        convergence_advisory={
            "schema_version": "ultimate_convergence_advisory_v1",
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
            "join_keys": {"sleeve": "ny_crypto_momentum", "symbol": "BTCUSD"},
            "reservoirs": {
                "selector_v3_source_bound_proxy": {
                    "rows": 289917,
                    "total_r": 286137.784349529,
                    "runtime_use": "expert_signal_reservoir_not_direct_live_authority",
                }
            },
        },
    )

    ok, issues = validate_runtime_learning_packet(packet)

    assert ok, issues
    advisory = packet["ultimate_convergence_advisory"]
    assert advisory["direct_execution_authority"] is False
    assert advisory["broker_runtime_change_status"] is False
    assert advisory["reservoirs"]["selector_v3_source_bound_proxy"]["rows"] == 289917


def test_runtime_learning_writer_appends_jsonl(tmp_path):
    writer = RuntimeLearningPacketWriter(tmp_path, "shadow_logs/runtime_packets.jsonl")
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="cycle_no_candidates",
        bridge={"runtime_effect_now": False},
        outcome={"placement_status": "no_candidates"},
    )

    assert writer.append_many([packet]) == 1

    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "runtime_packets.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows) == 1
    assert rows[0]["schema_version"] == "ultimate_book_runtime_learning_packet_v1"


class _FakeMT5:
    def get_account_balance(self):
        return 100000.0

    def get_account_equity(self):
        return 100000.0


class _FakeEngine:
    config = {}

    def evaluate(self, *, now_utc=None, tags=None):
        decision = SimpleNamespace(
            runtime_effect_now=False,
            candidate_use_allowed_now=False,
            decision_status="shadow_apply_to_execution_off",
            reason="ultimate_book_apply_to_execution_false",
            profile="clean3_w7_ceiling_nom2p00",
            enabled=True,
            apply_to_execution=False,
            live_activation_allowed_by_config=True,
            broad_selector_disable_required=True,
            broad_selector_apply_to_execution=False,
            include_candidate_book=True,
            candidate_book_profile="runtime_executable_native_exit_v2",
            candidate_book_sleeves=("ny_crypto_momentum",),
            include_market_expansion_book=True,
            market_expansion_profile="default_off_market_expansion_d1_target2_v1",
            market_expansion_policy="positive_weighted12_after_swap",
            market_expansion_sleeves=("BTCUSD",),
            kelly_lite=True,
            kelly_conservative=True,
            sqrt_n_pooling=False,
            stress_derisk=True,
            overlays=False,
            vp_acceptance=False,
            drop_w7_symbols=True,
            learning_rerate_active=False,
            learning_gated_sleeves=(),
            metals_confluence_gate=True,
            symbol_damage_guard=True,
            damage_quarantined_symbols=(),
            dropped_symbols=(),
            n_candidates_in=1,
            n_candidates_after_drop=1,
            would_new_entries_allowed=True,
            would_total_risk_pct=0.001,
            would_units=[
                {
                    "sleeve_members": ["ny_crypto_momentum"],
                    "risk_pct_per_trade": 0.001,
                    "unit_risk_pct": 0.001,
                    "sized": True,
                    "cluster": "crypto",
                }
            ],
            realized_units=[],
            governor={"new_entries_allowed": True},
        )
        return {
            "ok": True,
            "reason": "shadow_apply_to_execution_off",
            "n_intents": 1,
            "runtime_effect_now": False,
            "decision": decision,
        }

    def reset_window_date(self, now):
        return now.date().isoformat()


def test_book_owner_shadow_cycle_writes_runtime_learning_packet(tmp_path):
    cfg = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": False,
            "ultimate_book_live_activation_allowed": True,
            "ultimate_book_runtime_learning_packet_enabled": True,
            "ultimate_book_runtime_learning_packet_log_enabled": True,
            "ultimate_book_runtime_learning_packet_log_path": "shadow_logs/runtime_packets.jsonl",
            "selector_v4_enabled": True,
            "selector_v4_apply_to_execution": False,
        },
    }
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    owner.engine = _FakeEngine()

    summary = owner.run_cycle(now_utc=datetime(2026, 6, 18, tzinfo=timezone.utc), tags=("ny_crypto_momentum",))

    assert summary["runtime_learning"]["packets"] == 1
    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "runtime_packets.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert rows[0]["event_type"] == "unit_shadow"
    assert rows[0]["sleeve"] == "ny_crypto_momentum"
    assert rows[0]["broker_runtime_change_status"] is False


def test_book_owner_shadow_cycle_writes_convergence_advisory_when_enabled(tmp_path):
    cfg = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": False,
            "ultimate_book_live_activation_allowed": True,
            "ultimate_book_runtime_learning_packet_enabled": True,
            "ultimate_book_runtime_learning_packet_log_enabled": True,
            "ultimate_book_runtime_learning_packet_log_path": "shadow_logs/runtime_packets.jsonl",
            "ultimate_convergence_advisory_enabled": True,
            "ultimate_convergence_advisory_log_enabled": True,
            "ultimate_convergence_advisory_apply_to_execution": False,
            "selector_v4_enabled": True,
            "selector_v4_apply_to_execution": False,
        },
    }
    owner = UltimateBookOwner(cfg, _FakeMT5(), str(tmp_path), namespace="ftmo_test")
    owner.engine = _FakeEngine()

    summary = owner.run_cycle(now_utc=datetime(2026, 6, 18, tzinfo=timezone.utc), tags=("ny_crypto_momentum",))

    assert summary["runtime_learning"]["packets"] == 1
    rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "runtime_packets.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    advisory = rows[0]["ultimate_convergence_advisory"]
    assert advisory["schema_version"] == "ultimate_convergence_advisory_v1"
    assert advisory["direct_execution_authority"] is False
    assert advisory["broker_runtime_change_status"] is False
    assert advisory["reservoirs"]["selector_v3_source_bound_proxy"]["total_r"] == 286137.784349529
    assert advisory["join_keys"]["sleeve"] == "ny_crypto_momentum"
