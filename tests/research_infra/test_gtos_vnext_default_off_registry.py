from __future__ import annotations

from src.research_infra.gtos_vnext_default_off_registry import (
    GTOSVNextDefaultOffRegistry,
    build_event_from_registry_row,
    summarize_event_validation,
    summarize_default_off_registry,
    validate_event_source,
)


def _row(row_id: str, **fields):
    base = {
        "vnext_matrix_row_id": row_id,
        "source_name": "unit",
        "evidence_family": "unit_family",
        "source_row_id": f"source-{row_id}",
        "system_surface": "default_off_surface",
        "implementation_action": "REGISTER_DEFAULT_OFF",
        "r_evidence_class": "PROXY_R",
        "r_metrics": {"proxy_score": {"sum": 0.15}},
    }
    base.update(fields)
    return base


def test_registry_matches_rows_whose_required_scope_is_subset_of_event() -> None:
    registry = GTOSVNextDefaultOffRegistry(
        [
            _row("r1", symbol="XAUUSD", market_timeframe="M15", side="LONG"),
            _row("r2", symbol="XAUUSD", action_class="avoid_filter"),
            _row("r3", symbol="USDJPY", market_timeframe="M15"),
        ]
    )

    matches = registry.match_event(
        {
            "broker_symbol": "XAUUSD",
            "timeframe": "M15",
            "selected_side": "LONG",
            "action_class": "avoid_filter",
        }
    )

    assert [match["vnext_matrix_row_id"] for match in matches] == ["r1", "r2"]
    assert all(match["runtime_candidate_use_permitted"] is False for match in matches)
    assert all(match["runtime_score_allowed"] is False for match in matches)


def test_catalog_only_rows_do_not_match_every_event() -> None:
    registry = GTOSVNextDefaultOffRegistry(
        [
            _row("catalog_only"),
            _row("scoped", source_component="registry_scorer_module", proxy_r_class="STRONG_POSITIVE_PROXY_R"),
        ]
    )

    matches = registry.match_event(
        {
            "source_component": "registry_scorer_module",
            "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
        }
    )

    assert [match["vnext_matrix_row_id"] for match in matches] == ["scoped"]


def test_self_check_marks_scoped_rows_pass_and_catalog_rows_catalog_only() -> None:
    registry = GTOSVNextDefaultOffRegistry(
        [
            _row("catalog_only"),
            _row("scoped", symbol_family="US30_YM_FAMILY", route_session="london_core"),
        ]
    )

    self_checks = registry.build_self_check_rows()
    summary = summarize_default_off_registry(registry, self_checks)

    assert [row["self_check_status"] for row in self_checks] == [
        "CATALOG_ONLY_NO_EVENT_SCOPE",
        "PASS_SELF_MATCH_FOUND",
    ]
    assert summary["input_registry_rows"] == 2
    assert summary["callable_event_match_rows"] == 1
    assert summary["self_check_status_counts"] == {
        "CATALOG_ONLY_NO_EVENT_SCOPE": 1,
        "PASS_SELF_MATCH_FOUND": 1,
    }


def test_event_builder_uses_nonempty_registry_dimensions_only() -> None:
    row = _row(
        "r1",
        symbol="",
        source_symbol="XAGUSD",
        route_session="ny_core",
        action_class="follow_rule",
    )

    assert build_event_from_registry_row(row) == {
        "source_symbol": "XAGUSD",
        "route_session": "ny_core",
        "action_class": "follow_rule",
    }


def test_event_source_validation_rolls_up_all_rows_without_runtime_effect(tmp_path) -> None:
    source = tmp_path / "events.jsonl"
    source.write_text(
        "\n".join(
            [
                '{"symbol":"XAUUSD","timeframe":"M15","selected_side":"LONG"}',
                '{"symbol":"USDJPY","timeframe":"M15","selected_side":"SHORT"}',
                '{"symbol":"XAUUSD","timeframe":"M15","selected_side":"LONG"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    registry = GTOSVNextDefaultOffRegistry(
        [
            _row("xau", symbol="XAUUSD", market_timeframe="M15", side="LONG"),
            _row("jpy", symbol="USDJPY", market_timeframe="M15", side="SHORT"),
        ]
    )

    source_summary, rollup_rows = validate_event_source(registry, source, repo=tmp_path)
    summary = summarize_event_validation([source_summary], rollup_rows)

    assert source_summary["source_rows"] == 3
    assert source_summary["matched_event_rows"] == 3
    assert source_summary["registry_match_rows"] == 3
    assert source_summary["event_scope_rollup_rows"] == 2
    assert summary["source_rows_total"] == 3
    assert summary["event_scope_rollup_rows"] == 2
    assert all(row["runtime_candidate_use_permitted"] is False for row in rollup_rows)
    assert all(row["source_row_hashes_sha256"] for row in rollup_rows)
