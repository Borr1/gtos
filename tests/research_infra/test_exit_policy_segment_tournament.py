"""Tests for the segment exit-policy tournament + frozen segment table.

Synthetic world: GBPJPY (jpy_fx) trades are constructed as long-MFE winners
so a trailing challenger demonstrably beats the incumbent momentum cap; a
thin EURUSD (fx) segment stays on the incumbent. All fixtures live under
``tmp_path`` (hand-built M1 CSVs + oracle/candidate ledgers) — no production
paths are touched.
"""

from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

from src.research.dynamic_execution_policy import PolicySpec
from src.research.moonshot_segment_exit_policy_table import (
    GLOBAL_DEFAULT_FALLBACK_LEVEL,
    load_segment_policy_table,
    resolve_segment_policy,
)
from src.research_infra.ultimate_exit_policy_segment_tournament import (
    DEFAULT_POLICY_GRID,
    INCUMBENT_POLICY_ID,
    PARAMS_FIDELITY_EXACT,
    POLICY_SPEC_SUPPORTS_ABORT,
    SCHEMA_VERSION,
    build_path_dataset,
    default_grid,
    main,
    run_tournament,
    select_segment_policies,
)

POLICY_SPEC_FIELD_NAMES = {spec_field.name for spec_field in fields(PolicySpec)}

WINNER_DAYS = ("2026-05-06", "2026-05-07", "2026-05-08", "2026-05-11")
GBPJPY_ENTRY = 100.0
GBPJPY_STOP = 99.0
EURUSD_ENTRY = 1.10
EURUSD_STOP = 1.09


def _write_m1_csv(m1_root: Path, symbol: str, rows: list[tuple[str, float, float, float, float]]) -> None:
    month_dir = m1_root / "bridge_ftmo_m1_202605"
    month_dir.mkdir(parents=True, exist_ok=True)
    lines = ["time,open,high,low,close,volume"]
    for time_text, open_p, high_p, low_p, close_p in rows:
        lines.append(f"{time_text},{open_p},{high_p},{low_p},{close_p},10")
    (month_dir / f"{symbol}_M1.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _winner_bars(trading_day: str) -> list[tuple[str, float, float, float, float]]:
    """One pre-fill bar then 13 climbing bars: +0.5R per bar up to +6.5R MFE
    with tiny 0.1R pullbacks (a long MFE run the incumbent 2.0R cap truncates)."""

    bars = [
        (
            f"{trading_day} 09:55:00",
            GBPJPY_ENTRY - 0.2,
            GBPJPY_ENTRY - 0.1,
            GBPJPY_ENTRY - 0.3,
            GBPJPY_ENTRY - 0.2,
        )
    ]
    for index in range(13):
        high = GBPJPY_ENTRY + 0.5 * (index + 1)
        bars.append(
            (
                f"{trading_day} 10:{index:02d}:00",
                round(high - 0.08, 6),
                round(high, 6),
                round(high - 0.1, 6),
                round(high - 0.05, 6),
            )
        )
    return bars


def _loser_bars(trading_day: str) -> list[tuple[str, float, float, float, float]]:
    return [
        (
            f"{trading_day} 10:00:00",
            EURUSD_ENTRY - 0.001,
            EURUSD_ENTRY + 0.001,
            EURUSD_ENTRY - 0.012,
            EURUSD_ENTRY - 0.011,
        )
    ]


def _oracle_row(
    candidate_id: str,
    symbol: str,
    trading_day: str,
    *,
    entry: float,
    stop: float,
    counterfactual: bool = False,
    fill_status: str | None = None,
) -> dict:
    row = {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "trading_day": trading_day,
        "side": "LONG",
        "fill_time_utc": f"{trading_day}T10:00:00+00:00",
        "entry_price": entry,
        "fill_price": entry,
        "stop_price": stop,
    }
    if fill_status is not None:
        row["fill_status"] = fill_status
    elif counterfactual:
        row["fill_status"] = "not_sent_risk_rejected"
        row["counterfactual_fill_status"] = "filled_from_ordered_m1_path"
    else:
        row["fill_status"] = "filled_from_ordered_m1_path"
    return row


def _candidate_row(candidate_id: str, symbol: str, origin_family: str, session_bucket: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "origin_family": origin_family,
        "session_bucket": session_bucket,
    }


def _write_ledgers(route_dir: Path, trading_day: str, oracle_rows: list[dict], candidate_rows: list[dict]) -> None:
    route_dir.mkdir(parents=True, exist_ok=True)
    token = trading_day.replace("-", "")
    oracle_path = route_dir / f"ULTIMATE_ROLLING_DYNAMIC_{token}_ORDERED_PATH_ORACLE_LEDGER.jsonl"
    candidate_path = route_dir / f"ULTIMATE_ROLLING_DYNAMIC_{token}_CANDIDATE_MICROSCOPE_LEDGER.jsonl"
    oracle_path.write_text(
        "\n".join(json.dumps(row) for row in oracle_rows) + "\n", encoding="utf-8"
    )
    candidate_path.write_text(
        "\n".join(json.dumps(row) for row in candidate_rows) + "\n", encoding="utf-8"
    )


def _build_winner_world(tmp_path: Path) -> tuple[Path, Path]:
    """GBPJPY 12 long-MFE winners over 4 days (one counterfactual fill),
    EURUSD 2 thin losers on day 1, one XAUUSD fill without an M1 file, and
    one never-filled row."""

    route_dir = tmp_path / "route"
    m1_root = tmp_path / "m1"

    gbpjpy_bars: list[tuple[str, float, float, float, float]] = []
    for trading_day in WINNER_DAYS:
        gbpjpy_bars.extend(_winner_bars(trading_day))
    _write_m1_csv(m1_root, "GBPJPY", gbpjpy_bars)
    _write_m1_csv(m1_root, "EURUSD", _loser_bars(WINNER_DAYS[0]))

    for day_index, trading_day in enumerate(WINNER_DAYS):
        oracle_rows = []
        candidate_rows = []
        for trade_index in range(3):
            candidate_id = f"gj_{day_index}_{trade_index}"
            oracle_rows.append(
                _oracle_row(
                    candidate_id,
                    "GBPJPY",
                    trading_day,
                    entry=GBPJPY_ENTRY,
                    stop=GBPJPY_STOP,
                    counterfactual=(day_index == 0 and trade_index == 2),
                )
            )
            candidate_rows.append(
                _candidate_row(candidate_id, "GBPJPY", "liquidity_sweep_reclaim", "london")
            )
        if day_index == 0:
            for trade_index in range(2):
                candidate_id = f"eu_{trade_index}"
                oracle_rows.append(
                    _oracle_row(
                        candidate_id,
                        "EURUSD",
                        trading_day,
                        entry=EURUSD_ENTRY,
                        stop=EURUSD_STOP,
                    )
                )
                candidate_rows.append(
                    _candidate_row(candidate_id, "EURUSD", "fvg_fill", "ny")
                )
            oracle_rows.append(
                _oracle_row(
                    "xa_0",
                    "XAUUSD",
                    trading_day,
                    entry=2400.0,
                    stop=2390.0,
                )
            )
            candidate_rows.append(
                _candidate_row("xa_0", "XAUUSD", "ob_retest", "ny")
            )
            oracle_rows.append(
                _oracle_row(
                    "nf_0",
                    "GBPJPY",
                    trading_day,
                    entry=GBPJPY_ENTRY,
                    stop=GBPJPY_STOP,
                    fill_status="not_filled_in_post_asof_m1_path",
                )
            )
            candidate_rows.append(
                _candidate_row("nf_0", "GBPJPY", "liquidity_sweep_reclaim", "london")
            )
        _write_ledgers(route_dir, trading_day, oracle_rows, candidate_rows)
    return route_dir, m1_root


def _build_thin_world(tmp_path: Path) -> tuple[Path, Path]:
    route_dir = tmp_path / "thin_route"
    m1_root = tmp_path / "thin_m1"
    trading_day = WINNER_DAYS[0]
    _write_m1_csv(m1_root, "EURUSD", _loser_bars(trading_day))
    oracle_rows = []
    candidate_rows = []
    for trade_index in range(2):
        candidate_id = f"thin_{trade_index}"
        oracle_rows.append(
            _oracle_row(candidate_id, "EURUSD", trading_day, entry=EURUSD_ENTRY, stop=EURUSD_STOP)
        )
        candidate_rows.append(_candidate_row(candidate_id, "EURUSD", "fvg_fill", "ny"))
    _write_ledgers(route_dir, trading_day, oracle_rows, candidate_rows)
    return route_dir, m1_root


def test_default_grid_contract() -> None:
    grid = default_grid()
    assert grid is DEFAULT_POLICY_GRID
    by_id = {entry.policy_id: entry for entry in grid}
    assert len(by_id) == len(grid)

    incumbent = by_id[INCUMBENT_POLICY_ID]
    assert incumbent.family == "momentum"
    assert incumbent.spec.trailing_trigger_r == 1.0
    assert incumbent.spec.trailing_gap_r == 0.4
    assert incumbent.spec.final_target_r == 2.0

    families = {entry.family for entry in grid}
    assert families == {"momentum", "trailing", "fixed_target", "be_only"}
    # Curated base grid (V2 sub-1R trail extension: 6 triggers x 6 gaps x 3
    # caps); the abort cross phase adds more at runtime.
    assert 100 <= len(grid) <= 220
    # The sub-1R payoff region (exit-oracle finding) must stay sampled.
    assert any(
        entry.spec.trailing_trigger_r == 0.25 and entry.spec.trailing_gap_r == 0.15
        for entry in grid
        if entry.family == "trailing"
    )
    # PolicySpec carries the abort primitives in the current tree.
    assert POLICY_SPEC_SUPPORTS_ABORT is True


def test_build_path_dataset_joins_segments_and_counts_missing_m1(tmp_path: Path) -> None:
    route_dir, m1_root = _build_winner_world(tmp_path)
    dataset = build_path_dataset([route_dir], m1_root=m1_root)

    assert dataset.counters["filled_rows"] == 14  # 11 GBPJPY + 2 EURUSD + 1 XAUUSD
    assert dataset.counters["counterfactual_filled_rows"] == 1
    assert dataset.counters["not_filled_rows"] == 1
    assert dataset.counters["m1_file_missing"] == 1  # XAUUSD has no CSV
    assert len(dataset.missing_m1_files) == 1
    assert "XAUUSD_M1.csv" in dataset.missing_m1_files[0]

    assert len(dataset.rows) == 14
    symbols = {row.symbol for row in dataset.rows}
    assert symbols == {"GBPJPY", "EURUSD"}
    assert sum(1 for row in dataset.rows if row.row_kind == "counterfactual_filled") == 1

    gbpjpy = [row for row in dataset.rows if row.symbol == "GBPJPY"]
    assert all(row.asset_class == "jpy_fx" for row in gbpjpy)
    assert all(row.origin_family == "liquidity_sweep_reclaim" for row in gbpjpy)
    assert all(row.session_bucket == "london" for row in gbpjpy)
    # Pre-fill 09:55 bar is excluded; 13 post-fill bars remain.
    assert all(len(row.observations) == 13 for row in gbpjpy)
    assert all(row.observations[0].time_utc.endswith("10:00:00") for row in gbpjpy)


def test_tournament_promotes_trailing_in_winner_leaf_segment(tmp_path: Path) -> None:
    route_dir, m1_root = _build_winner_world(tmp_path)
    dataset = build_path_dataset([route_dir], m1_root=m1_root)
    results = run_tournament(dataset.rows)

    # Abort cross phase ran against the best base specs.
    assert any(policy_id.count("__abort_") for policy_id in results.policies)

    table = select_segment_policies(results, min_leaf_n=10, min_days=3)
    assert table["schema_version"] == SCHEMA_VERSION
    assert table["default_policy"]["policy_id"] == INCUMBENT_POLICY_ID
    assert table["broker_operation"] is False
    assert table["paid_api_or_vendor_call"] is False

    leaf_id = "leaf|jpy_fx|liquidity_sweep_reclaim|london"
    leaf = next(row for row in table["segments"] if row["segment_id"] == leaf_id)
    assert leaf["promoted"] is True
    assert leaf["family"] == "trailing"
    assert leaf["n_trades"] == 12
    assert leaf["n_days"] == 4
    assert leaf["corrected_p"] < 0.10
    assert leaf["incumbent_delta_r_per_trade"] > 3.0
    assert leaf["params"]["trailing_trigger_r"] is not None
    assert leaf["params"]["trailing_gap_r"] is not None
    # Evidence/deployment geometry contract: every promoted row is stamped
    # exact_params_required and carries the FULL tested PolicySpec field map.
    assert leaf["params_fidelity"] == PARAMS_FIDELITY_EXACT
    assert set(leaf["params"]) == POLICY_SPEC_FIELD_NAMES
    assert table["params_fidelity_contract"] == PARAMS_FIDELITY_EXACT
    assert set(table["policy_spec_fields"]) == POLICY_SPEC_FIELD_NAMES
    promoted_rows = [row for row in table["segments"] if row["promoted"]]
    assert promoted_rows
    assert all(
        row["params_fidelity"] == PARAMS_FIDELITY_EXACT for row in promoted_rows
    )
    assert all(set(row["params"]) == POLICY_SPEC_FIELD_NAMES for row in promoted_rows)

    thin_leaf_id = "leaf|fx|fvg_fill|ny"
    thin_leaf = next(row for row in table["segments"] if row["segment_id"] == thin_leaf_id)
    assert thin_leaf["promoted"] is False
    assert thin_leaf["policy_id"] == INCUMBENT_POLICY_ID
    assert "params_fidelity" not in thin_leaf
    assert any(reason.startswith("insufficient_") for reason in thin_leaf["reasons"])


def test_select_segment_policies_is_deterministic(tmp_path: Path) -> None:
    route_dir, m1_root = _build_winner_world(tmp_path)
    dataset = build_path_dataset([route_dir], m1_root=m1_root)
    results = run_tournament(dataset.rows)
    table_a = select_segment_policies(results, min_leaf_n=10, min_days=3)
    table_b = select_segment_policies(results, min_leaf_n=10, min_days=3)
    assert table_a == table_b


def test_promoted_table_roundtrips_through_loader_and_resolver(tmp_path: Path) -> None:
    route_dir, m1_root = _build_winner_world(tmp_path)
    dataset = build_path_dataset([route_dir], m1_root=m1_root)
    results = run_tournament(dataset.rows)
    table = select_segment_policies(results, min_leaf_n=10, min_days=3)

    out_path = tmp_path / "table.json"
    out_path.write_text(json.dumps(table, indent=2, sort_keys=True), encoding="utf-8")
    loaded = load_segment_policy_table(out_path)
    assert loaded["table_sha256"]

    resolution = resolve_segment_policy(
        loaded,
        asset_class="jpy_fx",
        origin_family="liquidity_sweep_reclaim",
        session_bucket="london",
    )
    assert resolution["promoted"] is True
    assert resolution["fallback_level"] == "leaf"
    assert resolution["family"] == "trailing"
    assert resolution["params"]["trailing_gap_r"] is not None
    # The resolver propagates the geometry-fidelity stamp and the full tested
    # PolicySpec field map for downstream exact-param consumption.
    assert resolution["params_fidelity"] == PARAMS_FIDELITY_EXACT
    assert set(resolution["params"]) == POLICY_SPEC_FIELD_NAMES
    assert resolution["table_sha256"] == loaded["table_sha256"]


def test_thin_world_falls_back_to_incumbent_default(tmp_path: Path) -> None:
    route_dir, m1_root = _build_thin_world(tmp_path)
    dataset = build_path_dataset([route_dir], m1_root=m1_root)
    results = run_tournament(dataset.rows)
    table = select_segment_policies(results)  # production floors: 40 trades / 6 days

    assert table["segments"], "thin world must still record unpromoted rows"
    assert all(row["promoted"] is False for row in table["segments"])
    assert all(row["policy_id"] == INCUMBENT_POLICY_ID for row in table["segments"])
    assert all(row["reasons"] for row in table["segments"])

    out_path = tmp_path / "thin_table.json"
    out_path.write_text(json.dumps(table, indent=2, sort_keys=True), encoding="utf-8")
    loaded = load_segment_policy_table(out_path)
    resolution = resolve_segment_policy(
        loaded, asset_class="fx", origin_family="fvg_fill", session_bucket="ny"
    )
    assert resolution["promoted"] is False
    assert resolution["policy_id"] == INCUMBENT_POLICY_ID
    assert resolution["fallback_level"] == GLOBAL_DEFAULT_FALLBACK_LEVEL
    assert resolution["params"]["trailing_trigger_r"] == 1.0
    assert resolution["params"]["final_target_r"] == 2.0


def test_cli_main_writes_table_with_source_manifest(tmp_path: Path, capsys) -> None:
    route_dir, m1_root = _build_winner_world(tmp_path)
    out_path = tmp_path / "cli_table.json"
    exit_code = main(
        [
            "--route-dir",
            str(route_dir),
            "--out",
            str(out_path),
            "--m1-root",
            str(m1_root),
            "--min-leaf-n",
            "10",
            "--min-days",
            "3",
        ]
    )
    assert exit_code == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary["path_rows"] == 14
    assert summary["filled_rows"] == 14
    assert summary["counterfactual_filled_rows"] == 1
    assert summary["m1_file_missing_rows"] == 1
    assert summary["segments_promoted"] >= 1
    assert summary["broker_operation"] is False

    loaded = load_segment_policy_table(out_path)
    assert loaded["schema_version"] == SCHEMA_VERSION
    manifest_files = loaded["source_manifest"]["files"]
    assert len(manifest_files) == 8  # 4 days x (oracle + candidate)
    assert all(len(entry["sha256"]) == 64 for entry in manifest_files)
    assert loaded["dataset_counters"]["m1_file_missing"] == 1
    assert loaded["missing_m1_files"]
