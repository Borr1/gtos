from __future__ import annotations

import os

import pytest

from src.research_infra import databento_futures as mod


class _FakeMetadata:
    def __init__(self, *, cost: float = 0.01) -> None:
        self.cost = cost

    def get_record_count(self, **kwargs):
        self.last_count_kwargs = kwargs
        return 123

    def get_billable_size(self, **kwargs):
        self.last_size_kwargs = kwargs
        return 4567

    def get_cost(self, **kwargs):
        self.last_cost_kwargs = kwargs
        return self.cost

    def list_schemas(self, dataset):
        return ["trades", "mbo"]

    def get_dataset_range(self, dataset):
        return {"start": "2017-05-01T00:00:00Z", "end": "2026-05-01T00:00:00Z"}

    def list_unit_prices(self, dataset):
        return [{"mode": "historical", "unit_prices": {"trades": 1.0}}]


class _FakeTimeseries:
    def __init__(self) -> None:
        self.calls = []

    def get_range(self, **kwargs):
        self.calls.append(kwargs)
        path = kwargs.get("path")
        if path:
            with open(path, "wb") as fh:
                fh.write(b"dbn")
        return object()


class _FakeClient:
    def __init__(self, *, cost: float = 0.01) -> None:
        self.metadata = _FakeMetadata(cost=cost)
        self.timeseries = _FakeTimeseries()


def test_parse_symbols_preserves_all_symbols():
    assert mod.parse_symbols("ALL_SYMBOLS") == "ALL_SYMBOLS"
    assert mod.symbols_for_databento("ALL_SYMBOLS") == "ALL_SYMBOLS"


def test_parse_symbols_splits_comma_list():
    assert mod.parse_symbols("ES.v.0,NQ.v.0, GC.v.0") == (
        "ES.v.0",
        "NQ.v.0",
        "GC.v.0",
    )


def test_request_kwargs_include_limit_and_continuous_stype():
    request = mod.DatabentoRequest(
        symbols=("ES.v.0",),
        start="2026-04-24T00:30",
        end="2026-04-24T00:40",
        limit=100,
    )
    assert request.to_api_kwargs() == {
        "dataset": "GLBX.MDP3",
        "schema": "trades",
        "symbols": ["ES.v.0"],
        "start": "2026-04-24T00:30",
        "end": "2026-04-24T00:40",
        "stype_in": "continuous",
        "limit": 100,
    }


def test_estimate_calls_metadata_methods():
    client = _FakeClient(cost=0.02)
    request = mod.DatabentoRequest(
        symbols="ALL_SYMBOLS",
        stype_in="raw_symbol",
        start="2026-04-24T00:30",
        end="2026-05-01T23:30",
        limit=100,
    )
    estimate = mod.estimate_request(client, request)
    assert estimate.record_count == 123
    assert estimate.billable_size_bytes == 4567
    assert estimate.cost_usd == 0.02
    assert client.metadata.last_cost_kwargs["symbols"] == "ALL_SYMBOLS"


def test_fetch_blocks_when_cost_exceeds_cap(tmp_path):
    client = _FakeClient(cost=10.0)
    request = mod.DatabentoRequest(start="2026-04-24T00:30", limit=100)
    with pytest.raises(RuntimeError, match="exceeds --max-cost-usd"):
        mod.fetch_request(client, request, root=tmp_path, max_cost_usd=0.25)
    assert client.timeseries.calls == []


def test_fetch_writes_raw_file_and_metadata_under_root(tmp_path):
    client = _FakeClient(cost=0.01)
    request = mod.DatabentoRequest(start="2026-04-24T00:30", limit=100)
    result = mod.fetch_request(client, request, root=tmp_path, max_cost_usd=0.25)
    assert result.output_path.endswith(".dbn.zst")
    assert result.metadata_path.endswith(".meta.json")
    assert os.path.exists(result.output_path)
    assert os.path.exists(result.metadata_path)
    assert client.timeseries.calls[0]["path"] == result.output_path


def test_dataset_status_is_secret_free():
    payload = mod.dataset_status(_FakeClient(), dataset="GLBX.MDP3")
    assert payload["dataset"] == "GLBX.MDP3"
    assert "schemas" in payload
    assert "DATABENTO_API_KEY" not in str(payload)
