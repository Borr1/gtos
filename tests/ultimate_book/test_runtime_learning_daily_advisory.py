import json
from pathlib import Path

from scripts.build_runtime_learning_daily_advisory import (
    _build_requested_advisories,
    build_advisory,
)
from src.components.ultimate_book.runtime_learning_packet import (
    build_runtime_learning_packet,
    stable_hash,
)


def _rehash_packet(packet):
    material = dict(packet)
    material.pop("packet_hash_sha256", None)
    packet["packet_hash_sha256"] = stable_hash(material, prefix="runtime_learning_packet")
    return packet


def test_daily_advisory_writes_repair_ledger_for_legacy_missing_exit_order(tmp_path):
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="position_closed",
        ts="2026-06-24T10:00:00+00:00",
        outcome={
            "symbol": "XAUUSD",
            "sleeve": "metal_session_reversion",
            "candidate_id": "W7_BOOK::metal::XAUUSD",
            "ticket_hash_sha256": "ticket-hash",
            "placement_status": "position_closed",
            "exit_reconciliation_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
            "exit_reconciliation_missing_fields": [],
            "broker_exit_deal_hash_sha256": "deal-hash",
            "broker_exit_position_hash_sha256": "position-hash",
            "broker_realized_pnl": 12.5,
            "closed_at_utc": "2026-06-24T10:00:00+00:00",
        },
    )
    packet["exit_reconciliation_missing_fields"] = []
    packet["outcome"]["exit_reconciliation_missing_fields"] = []
    packet = _rehash_packet(packet)

    log_path = tmp_path / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(json.dumps(packet) + "\n", encoding="utf-8")

    advisory = build_advisory(
        tmp_path,
        "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
        "pipeline_state/ultimate_book/runtime_learning_advisory",
    )

    assert advisory["packet_validation_issue_count_after_legacy_normalization"] == 0
    assert advisory["packet_log_exists_at_source_read"] is True
    assert advisory["packet_log_line_count_at_source_read"] == 1
    assert advisory["packet_log_last_seen_created_at_utc"] is not None
    assert advisory["packet_log_last_seen_event_type"] == "position_closed"
    assert advisory["packet_event_type_counts_at_source_read"] == {"position_closed": 1}
    assert advisory["legacy_exit_order_missing_field_repair_count"] == 1
    assert advisory["deduped_closed_trade_count"] == 1
    repair_ledger = tmp_path / "pipeline_state" / "ultimate_book" / "runtime_learning_advisory" / "RUNTIME_LEARNING_PACKET_REPAIR_LEDGER.jsonl"
    repair = json.loads(repair_ledger.read_text(encoding="utf-8").splitlines()[0])
    assert repair["normalized_exit_reconciliation_missing_fields"] == ["broker_exit_order_ticket"]
    history_ledger = tmp_path / "pipeline_state" / "ultimate_book" / "runtime_learning_advisory" / "RUNTIME_LEARNING_PACKET_REPAIR_LEDGER_HISTORY.jsonl"
    history_rows = history_ledger.read_text(encoding="utf-8").splitlines()
    assert len(history_rows) == 1

    build_advisory(
        tmp_path,
        "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
        "pipeline_state/ultimate_book/runtime_learning_advisory",
    )

    assert len(history_ledger.read_text(encoding="utf-8").splitlines()) == 1


def test_daily_advisory_enriches_closed_packet_from_repaired_trade_record(tmp_path):
    packet = build_runtime_learning_packet(
        namespace="redacted_account_live_bee34003",
        event_type="position_closed",
        ts="2026-06-26T00:00:08+00:00",
        outcome={
            "symbol": "JP225_cash",
            "sleeve": "mx_jp225_cash_d1_volume_surge_reversal",
            "candidate_id": "W7_BOOK::indices_context::JP225_cash::2026-06-24::SHORT::mx_jp225_cash_d1_volume_surge_reversal",
            "ticket_hash_sha256": "ticket-hash",
            "placement_status": "position_closed",
            "close_action": "vnext_time_stop",
            "closed_at_utc": "2026-06-26T00:00:08+00:00",
            "exit_reconciliation_status": "NO_EXIT_DEAL_FOUND",
            "exit_reconciliation_missing_fields": ["broker_exit_deal_ticket"],
            "trade_lifecycle_status": "closed",
        },
    )
    packet = _rehash_packet(packet)

    log_path = tmp_path / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(json.dumps(packet) + "\n", encoding="utf-8")

    record_path = (
        tmp_path
        / "pipeline_state"
        / "ultimate_book"
        / "redacted_account_live_bee34003"
        / "trade_records"
        / "248203894.json"
    )
    record_path.parent.mkdir(parents=True)
    record_path.write_text(
        json.dumps(
            {
                "trade_lifecycle_status": "closed",
                "execution": {
                    "ticket_hash_sha256": "ticket-hash",
                    "closed_at_utc": "2026-06-26T00:00:08+00:00",
                    "exit_reconciliation_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
                    "exit_reconciliation_attempted": True,
                    "exit_reconciliation_source_status": "broker_real_account_history_exit_reconciled",
                    "exit_reconciliation_missing_fields": ["broker_exit_order_ticket"],
                    "broker_exit_profit": 2.9,
                    "broker_exit_swap": -0.79,
                    "broker_exit_commission": 0.0,
                    "broker_entry_commission": 0.0,
                    "broker_entry_swap": 0.0,
                    "broker_position_realized_pnl": 2.11,
                    "broker_realized_pnl_source": "position_aggregate_includes_entry_and_exit_deals",
                    "broker_realized_pnl": 2.11,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    advisory = build_advisory(
        tmp_path,
        "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
        "pipeline_state/ultimate_book/runtime_learning_advisory",
    )

    assert advisory["closed_trade_record_enrichment_count"] == 1
    assert advisory["closed_trade_pnl_captured_count"] == 1
    assert advisory["closed_trade_pnl_missing_after_enrichment_count"] == 0
    assert advisory["daily_sleeve_outcomes"] == [
        {
            "day": "2026-06-26",
            "namespace": "redacted_account_live_bee34003",
            "sleeve": "mx_jp225_cash_d1_volume_surge_reversal",
            "closed_trade_count": 1,
            "broker_realized_pnl_captured_count": 1,
            "broker_realized_pnl_sum": 2.11,
            "broker_realized_pnl_mean": 2.11,
            "win_count": 1,
            "loss_count": 0,
            "flat_count": 0,
            "learning_application_status": "advisory_only_owner_gated_no_live_rerate_mutation",
        }
    ]


def test_daily_advisory_counts_legacy_nonterminal_broker_realized_pnl(tmp_path):
    packet = build_runtime_learning_packet(
        namespace="redacted_account_live_bee34003",
        event_type="position_managed",
        ts="2026-06-29T15:59:53+00:00",
        outcome={
            "symbol": "ETHUSD",
            "sleeve": "ny_crypto_momentum",
            "management_action": "broker_closed",
            "ticket_hash_sha256": "ticket-hash",
        },
    )
    packet["created_at_utc"] = "2026-06-29T15:59:53+00:00"
    packet["broker_realized_pnl"] = -66.18
    packet = _rehash_packet(packet)

    log_path = tmp_path / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(json.dumps(packet) + "\n", encoding="utf-8")

    advisory = build_advisory(
        tmp_path,
        "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
        "pipeline_state/ultimate_book/runtime_learning_advisory",
    )

    assert advisory["packet_validation_issue_count_after_legacy_normalization"] == 0
    assert advisory["legacy_nonterminal_broker_realized_pnl_normalized_count"] == 1
    assert advisory["future_nonterminal_broker_realized_pnl_issue_count"] == 0
    assert advisory["legacy_nonterminal_broker_realized_pnl_examples"][0]["fields"] == ["broker_realized_pnl"]


def test_daily_advisory_streams_packet_log_without_full_read_text(tmp_path, monkeypatch):
    packet = build_runtime_learning_packet(
        namespace="ftmo_test",
        event_type="cycle_no_candidates",
        ts="2026-06-24T10:00:00+00:00",
        outcome={"placement_status": "no_candidates"},
    )
    packet = _rehash_packet(packet)

    log_path = tmp_path / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"
    log_path.parent.mkdir(parents=True)
    with log_path.open("w", encoding="utf-8") as handle:
        for _ in range(3):
            handle.write(json.dumps(packet) + "\n")

    original_read_text = Path.read_text

    def fail_packet_log_read_text(self, *args, **kwargs):
        if self == log_path:
            raise AssertionError("packet log must be streamed, not fully materialized")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_packet_log_read_text)

    advisory = build_advisory(
        tmp_path,
        "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
        "pipeline_state/ultimate_book/runtime_learning_advisory",
    )

    assert advisory["packet_row_count"] == 3
    assert advisory["packet_processing_row_count_after_hash_dedupe"] == 1
    assert advisory["packet_duplicate_hash_deduped_count"] == 2
    assert advisory["packet_processing_order"] == (
        "single_pass_source_stream_deduped_by_packet_hash;"
        "closed_identity_selects_max_created_at_utc_then_source_line"
    )
    assert advisory["packet_log_line_count_at_source_read"] == 3
    assert advisory["packet_log_last_seen_event_type"] == "cycle_no_candidates"
    assert advisory["packet_event_type_counts_at_source_read"] == {"cycle_no_candidates": 3}
    assert advisory["packet_parse_error_count"] == 0


def test_daily_advisory_keeps_latest_chronological_close_without_sorting_all_rows(tmp_path):
    def close_packet(created_at, pnl):
        return build_runtime_learning_packet(
            namespace="ftmo_test",
            event_type="position_closed",
            ts=created_at,
            outcome={
                "symbol": "XAUUSD",
                "sleeve": "metals_core",
                "candidate_id": "candidate-same",
                "ticket_hash_sha256": "ticket-same",
                "placement_status": "position_closed",
                "closed_at_utc": "2026-08-13T10:00:00+00:00",
                "broker_realized_pnl": pnl,
            },
        )

    later = close_packet("2026-08-13T10:02:00+00:00", 12.0)
    earlier = close_packet("2026-08-13T10:01:00+00:00", -99.0)
    path = tmp_path / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"
    path.parent.mkdir(parents=True)
    # Deliberately reverse chronological source order. The streaming path must
    # preserve the former sorted-last-wins result without retaining every row.
    path.write_text(json.dumps(later) + "\n" + json.dumps(earlier) + "\n", encoding="utf-8")

    advisory = build_advisory(
        tmp_path,
        "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
        "pipeline_state/ultimate_book/runtime_learning_advisory",
    )

    assert advisory["deduped_closed_trade_count"] == 1
    assert advisory["daily_sleeve_outcomes"][0]["broker_realized_pnl_sum"] == 12.0


def test_supervised_builder_consumes_an_external_experiment_repo(tmp_path):
    primary = tmp_path / "primary"
    experiment = tmp_path / "experiment"
    for root, namespace in ((primary, "main"), (experiment, "operator")):
        packet = build_runtime_learning_packet(
            namespace=namespace,
            event_type="cycle_no_candidates",
            ts="2026-08-13T10:00:00+00:00",
            outcome={"placement_status": "no_candidates"},
        )
        path = root / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(packet) + "\n", encoding="utf-8")

    args = type("Args", (), {
        "packet_log_path": "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
        "output_dir": "pipeline_state/ultimate_book/runtime_learning_advisory",
        "additional_repo_root": str(experiment),
        "additional_packet_log_path": None,
        "additional_output_dir": None,
    })()
    import scripts.build_runtime_learning_daily_advisory as module
    original = module.REPO_ROOT
    module.REPO_ROOT = primary
    try:
        built = _build_requested_advisories(args)
    finally:
        module.REPO_ROOT = original

    assert len(built) == 2
    assert [item["summary"]["packet_row_count"] for item in built] == [1, 1]
    for root in (primary, experiment):
        assert (
            root
            / "pipeline_state"
            / "ultimate_book"
            / "runtime_learning_advisory"
            / "RUNTIME_LEARNING_DAILY_ADVISORY.json"
        ).exists()
