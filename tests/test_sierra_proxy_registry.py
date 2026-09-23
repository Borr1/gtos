from __future__ import annotations

from src.research_infra.sierra_proxy_registry import (
    CONTROL_ONLY,
    FUTURES_PROXY_TRANSFER,
    NO_REGISTERED_PROXY,
    SAME_MARKET_SOURCE_TRANSFER,
    SOURCE_DEFINITION_BLOCKED,
    VALIDATED_PROXY,
    registry_entry,
    registry_rows,
    sierra_proxy_by_symbol,
    sierra_source_status_by_symbol,
)


def test_registry_covers_required_proxy_classes_and_symbols():
    rows = {row["symbol"]: row for row in registry_rows()}
    classes = {row["proxy_class"] for row in rows.values()}

    assert {VALIDATED_PROXY, SAME_MARKET_SOURCE_TRANSFER, FUTURES_PROXY_TRANSFER, CONTROL_ONLY, SOURCE_DEFINITION_BLOCKED, NO_REGISTERED_PROXY} <= classes
    assert rows["NAS100"]["futures_symbol"] == "NQ.v.0"
    assert rows["NAS100"]["proxy_class"] == VALIDATED_PROXY
    assert rows["XAGUSD"]["proxy_class"] == SOURCE_DEFINITION_BLOCKED
    assert rows["GBPJPY"]["proxy_class"] == NO_REGISTERED_PROXY
    assert rows["EURUSD"]["futures_symbol"] == "6E.v.0"
    assert rows["EURUSD"]["proxy_class"] == FUTURES_PROXY_TRANSFER
    assert rows["GER40"]["proxy_class"] == NO_REGISTERED_PROXY
    assert rows["UK100"]["proxy_class"] == NO_REGISTERED_PROXY
    assert rows["CL"]["proxy_class"] == CONTROL_ONLY
    assert rows["ZN"]["control_only"] is True


def test_legacy_forward_capture_maps_are_derived_from_registry():
    proxies = sierra_proxy_by_symbol()
    statuses = sierra_source_status_by_symbol()

    assert proxies["NAS100"]["root"] == "NQM26-CME"
    assert proxies["GBPUSD"]["futures_symbol"] == "6B.v.0"
    assert "GBPJPY" not in proxies
    assert statuses["NAS100"]["allowed_use"] == "predecision_nq_mbp10_depth_context_shadow_only"
    assert statuses["GBPJPY"]["source_status"] == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    assert statuses["XAUUSD"]["proxy_class"] == SAME_MARKET_SOURCE_TRANSFER


def test_unknown_symbol_defaults_to_no_registered_proxy():
    entry = registry_entry("UNKNOWN_INDEX", "UNKNOWN_INDEX")

    assert entry.proxy_class == NO_REGISTERED_PROXY
    assert entry.source_status == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    assert entry.depth_interpretation_allowed is False
