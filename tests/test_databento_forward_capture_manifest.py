from __future__ import annotations

import json

from src.research_infra.databento_forward_capture import (
    append_databento_forward_request,
    build_databento_forward_request,
    build_nas100_default_request_set,
    request_cache_status,
)


def test_build_request_contains_required_cost_and_no_leak_fields():
    row = build_databento_forward_request(
        request_id="req_1",
        raw_symbol="NQ.v.0",
        schema="mbp-10",
        start_utc="2026-05-04T13:15:00+00:00",
        end_utc="2026-05-04T13:45:00+00:00",
        reason="candidate-centered depth window",
        expected_fields=["depth10_imbalance"],
        expected_cost_usd=0.12,
        cache_path="data/external/raw/databento/test.dbn.zst",
    )

    assert row["schema_version"] == "databento_forward_capture_request_v1"
    assert row["dataset"] == "GLBX.MDP3"
    assert row["actual_cost_usd"] is None
    assert row["expected_cost_usd"] == 0.12
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert "strictly before or at asof_cutoff_utc" in row["no_leak_usage_policy"]


def test_request_cache_status_distinguishes_missing_and_present(tmp_path):
    cache = tmp_path / "window.dbn.zst"
    row = build_databento_forward_request(
        request_id="req_1",
        raw_symbol="NQ.v.0",
        schema="trades",
        start_utc="2026-05-04T13:15:00+00:00",
        end_utc="2026-05-04T13:45:00+00:00",
        reason="candidate trades",
        expected_fields=["price"],
        cache_path=str(cache),
    )
    assert request_cache_status(row) == "CACHE_MISSING_READY_TO_FETCH"
    cache.write_bytes(b"cached")
    assert request_cache_status(row) == "CACHE_PRESENT"


def test_append_request_jsonl(tmp_path):
    path = tmp_path / "requests.jsonl"
    row = build_databento_forward_request(
        request_id="req_1",
        raw_symbol="NQ.v.0",
        schema="trades",
        start_utc="2026-05-04T13:15:00+00:00",
        end_utc="2026-05-04T13:45:00+00:00",
        reason="candidate trades",
        expected_fields=["price"],
    )
    append_databento_forward_request(row, path)

    parsed = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert parsed["request_id"] == "req_1"
    assert parsed["status"] == "DECLARED_NOT_FETCHED"


def test_nas100_default_request_set_has_mbp10_trades_and_targeted_mbo():
    rows = build_nas100_default_request_set(
        event_id="NAS100_20260504T1330_candidate_1",
        canonical_close_utc="2026-05-04T13:30:00+00:00",
        start_utc="2026-05-04T13:15:00+00:00",
        end_utc="2026-05-04T13:45:00+00:00",
    )

    schemas = {row["schema"] for row in rows}
    assert schemas == {"mbp-10", "trades", "mbo"}
    assert any(row["status"].startswith("DECLARED_DEFERRED") for row in rows)
