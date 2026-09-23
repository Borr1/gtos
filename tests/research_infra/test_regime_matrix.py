"""Tests for ``src.research_infra.regime_matrix`` (A5).

Covered:

1. ``load_regime_index`` reads a 5-row synthetic JSONL and indexes 5 entries.
2. ``assign_regime_to_cand`` returns the correct regime when the CAND falls
   inside the H4 window, and ``UNTAGGED`` when the CAND is outside the
   freshness window or before any indexed row.
3. ``build_wr_matrix`` aggregates 30 synthetic CANDs across 2 instruments x
   2 regimes into 4 cells with correct n + WR.
4. Wilson 95% CI is hand-verified on (k=8, n=10) within a tight tolerance.
5. Cells with n < 10 are flagged ``LOW_N`` in the dataframe view; n=0
   regimes do not appear (no CANDs => no cell).
6. ``v2_direction`` takes priority over ``production_label`` when both
   are present and valid.
7. Empty-symbol H4 rows are skipped + counted in skip stats.
8. Stale H4 rows beyond the freshness window are not used for tagging.

All file IO is restricted to ``tmp_path`` per the conftest write-guard
contract.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research_infra.regime_matrix import (
    LOW_N_THRESHOLD,
    UNTAGGED,
    RegimeIndex,
    RegimeMatrix,
    _select_regime,
    assign_regime_to_cand,
    build_wr_matrix,
    load_regime_index,
    wilson_ci,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _h4_row(
    *,
    ts: str,
    symbol: str,
    v2: str = "bullish",
    prod: str | None = None,
    mode: str = "live_v2",
) -> dict:
    """Build a synthetic H4 structure-log row matching production schema."""
    return {
        "ts": ts,
        "logged_at": ts,
        "symbol": symbol,
        "timeframe": "H4",
        "v1_direction": "bullish",
        "v2_direction": v2,
        "counts": {"hh": 4, "hl": 5, "lh": 1, "ll": 0},
        "detector_version_config": "v2",
        "mode": mode,
        "production_label": prod if prod is not None else v2,
        "v2_score": 8,
        "v2_dead_zone": 2,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# load_regime_index
# ---------------------------------------------------------------------------


def test_load_regime_index_counts_h4_only(tmp_path: Path) -> None:
    """5 H4 rows + a few non-H4 rows -> 5 H4 entries indexed; non-H4 ignored."""
    log_path = tmp_path / "structure_log.jsonl"
    rows = [
        # 5 H4 rows for XAUUSD (sequential 4h windows)
        _h4_row(ts="2026-01-15T00:00:00Z", symbol="XAUUSD", v2="bullish"),
        _h4_row(ts="2026-01-15T04:00:00Z", symbol="XAUUSD", v2="bullish"),
        _h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="transitional"),
        _h4_row(ts="2026-01-15T12:00:00Z", symbol="XAUUSD", v2="bearish"),
        _h4_row(ts="2026-01-15T16:00:00Z", symbol="XAUUSD", v2="bearish"),
        # Noise: M15, H1, D1 — must be ignored.
        {**_h4_row(ts="2026-01-15T00:00:00Z", symbol="XAUUSD"), "timeframe": "M15"},
        {**_h4_row(ts="2026-01-15T00:00:00Z", symbol="XAUUSD"), "timeframe": "H1"},
        {**_h4_row(ts="2026-01-15T00:00:00Z", symbol="XAUUSD"), "timeframe": "D1"},
    ]
    _write_jsonl(log_path, rows)

    idx = load_regime_index(log_path)

    assert idx.h4_rows_indexed == 5
    assert idx.symbols() == ["XAUUSD"]
    # Internal sort + parallel-list invariant
    assert len(idx._timestamps["XAUUSD"]) == 5
    assert len(idx._entries["XAUUSD"]) == 5
    # Sorted ascending by ts
    ts_list = idx._timestamps["XAUUSD"]
    assert ts_list == sorted(ts_list)


def test_load_regime_index_skips_empty_symbol(tmp_path: Path) -> None:
    log_path = tmp_path / "structure_log.jsonl"
    rows = [
        _h4_row(ts="2026-01-15T00:00:00Z", symbol="XAUUSD", v2="bullish"),
        _h4_row(ts="2026-01-15T04:00:00Z", symbol="", v2="bullish"),  # skipped
        _h4_row(ts="2026-01-15T08:00:00Z", symbol="USDJPY", v2="bearish"),
    ]
    _write_jsonl(log_path, rows)

    idx = load_regime_index(log_path)

    assert idx.h4_rows_indexed == 2
    assert idx.h4_rows_skipped_no_symbol == 1
    assert idx.symbols() == ["USDJPY", "XAUUSD"]


def test_load_regime_index_handles_malformed_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "structure_log.jsonl"
    raw = (
        json.dumps(_h4_row(ts="2026-01-15T00:00:00Z", symbol="XAUUSD")) + "\n"
        + "this is not json\n"
        + json.dumps(_h4_row(ts="2026-01-15T04:00:00Z", symbol="XAUUSD")) + "\n"
        + "\n"  # blank line
        + json.dumps({"timeframe": "H4"}) + "\n"  # missing symbol
    )
    log_path.write_text(raw, encoding="utf-8")

    idx = load_regime_index(log_path)

    assert idx.h4_rows_indexed == 2  # 2 valid H4 rows
    assert idx.h4_rows_skipped_no_symbol == 1  # the bare-skeleton one


def test_load_regime_index_missing_file(tmp_path: Path) -> None:
    """Missing file returns an empty index, not an exception."""
    idx = load_regime_index(tmp_path / "does_not_exist.jsonl")
    assert idx.h4_rows_indexed == 0
    assert idx.symbols() == []


# ---------------------------------------------------------------------------
# _select_regime priority
# ---------------------------------------------------------------------------


def test_select_regime_v2_priority() -> None:
    """v2_direction wins over production_label when both are valid."""
    row = {"v2_direction": "bearish", "production_label": "bullish"}
    regime, src = _select_regime(row)
    assert regime == "bearish"
    assert src == "v2_direction"


def test_select_regime_falls_back_to_production() -> None:
    """When v2 is missing/invalid, production_label is used."""
    row = {"v2_direction": "", "production_label": "bullish"}
    regime, src = _select_regime(row)
    assert regime == "bullish"
    assert src == "production_label"


def test_select_regime_returns_none_when_both_missing() -> None:
    row = {}
    regime, _ = _select_regime(row)
    assert regime is None


# ---------------------------------------------------------------------------
# assign_regime_to_cand — H4 boundary alignment
# ---------------------------------------------------------------------------


def test_assign_regime_inside_window(tmp_path: Path) -> None:
    """CAND inside an H4 window's freshness range gets the regime tag."""
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bearish")],
    )
    idx = load_regime_index(log_path)
    # CAND 30 minutes after the H4 row -> tagged.
    cand = {"symbol": "XAUUSD", "candle_close_time": "2026-01-15T08:30:00Z"}
    assert assign_regime_to_cand(cand, idx) == "bearish"


def test_assign_regime_before_first_row(tmp_path: Path) -> None:
    """CAND before any indexed H4 row -> UNTAGGED."""
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bearish")],
    )
    idx = load_regime_index(log_path)
    cand = {"symbol": "XAUUSD", "candle_close_time": "2026-01-15T07:59:59Z"}
    assert assign_regime_to_cand(cand, idx) == UNTAGGED


def test_assign_regime_outside_freshness_window(tmp_path: Path) -> None:
    """CAND > freshness_hours after latest H4 row -> UNTAGGED.

    Freshness defaults to 6 hours; we use 7h+ delta and assert UNTAGGED.
    """
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T00:00:00Z", symbol="XAUUSD", v2="bullish")],
    )
    idx = load_regime_index(log_path)
    cand = {"symbol": "XAUUSD", "candle_close_time": "2026-01-15T07:00:01Z"}
    assert assign_regime_to_cand(cand, idx) == UNTAGGED


def test_assign_regime_picks_latest_at_or_before(tmp_path: Path) -> None:
    """Two H4 rows; CAND between them picks the earlier (older); CAND after second picks the second."""
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [
            _h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish"),
            _h4_row(ts="2026-01-15T12:00:00Z", symbol="XAUUSD", v2="bearish"),
        ],
    )
    idx = load_regime_index(log_path)
    # 11:00 -> latest at-or-before is 08:00 (bullish)
    early = {"symbol": "XAUUSD", "candle_close_time": "2026-01-15T11:00:00Z"}
    assert assign_regime_to_cand(early, idx) == "bullish"
    # 13:00 -> latest at-or-before is 12:00 (bearish)
    late = {"symbol": "XAUUSD", "candle_close_time": "2026-01-15T13:00:00Z"}
    assert assign_regime_to_cand(late, idx) == "bearish"


def test_assign_regime_unknown_symbol(tmp_path: Path) -> None:
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish")],
    )
    idx = load_regime_index(log_path)
    cand = {"symbol": "GBPJPY", "candle_close_time": "2026-01-15T09:00:00Z"}
    assert assign_regime_to_cand(cand, idx) == UNTAGGED


def test_assign_regime_missing_time_falls_through_to_candle_time(tmp_path: Path) -> None:
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish")],
    )
    idx = load_regime_index(log_path)
    # No candle_close_time but candle_time present -> still tagged.
    cand = {"symbol": "XAUUSD", "candle_time": "2026-01-15T09:00:00Z"}
    assert assign_regime_to_cand(cand, idx) == "bullish"


def test_assign_regime_no_time_field(tmp_path: Path) -> None:
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish")],
    )
    idx = load_regime_index(log_path)
    cand = {"symbol": "XAUUSD"}  # no time at all
    assert assign_regime_to_cand(cand, idx) == UNTAGGED


# ---------------------------------------------------------------------------
# build_wr_matrix — 30 CANDs x 2 instruments x 2 regimes
# ---------------------------------------------------------------------------


def test_build_wr_matrix_30_cands(tmp_path: Path) -> None:
    """30 synthetic CANDs spread across 2 instruments x 2 regimes -> 4 cells."""
    log_path = tmp_path / "structure_log.jsonl"
    # Two rows per instrument: one bullish window at 08:00, one bearish at 16:00.
    rows = [
        _h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish"),
        _h4_row(ts="2026-01-15T16:00:00Z", symbol="XAUUSD", v2="bearish"),
        _h4_row(ts="2026-01-15T08:00:00Z", symbol="USDJPY", v2="bullish"),
        _h4_row(ts="2026-01-15T16:00:00Z", symbol="USDJPY", v2="bearish"),
    ]
    _write_jsonl(log_path, rows)
    idx = load_regime_index(log_path)

    cands: list[dict] = []
    # XAUUSD bullish: 8 CANDs, 5 wins (R values: +1.5, +1.5, +1.5, +1.5, +1.5, -1, -1, -1)
    for i in range(5):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": 1.5,
            }
        )
    for i in range(3):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": -1.0,
            }
        )
    # XAUUSD bearish: 7 CANDs, 2 wins
    for i in range(2):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T17:00:00Z",
                "r_multiple": 2.0,
            }
        )
    for i in range(5):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T17:00:00Z",
                "r_multiple": -1.0,
            }
        )
    # USDJPY bullish: 10 CANDs, 7 wins
    for i in range(7):
        cands.append(
            {
                "symbol": "USDJPY",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": 1.0,
            }
        )
    for i in range(3):
        cands.append(
            {
                "symbol": "USDJPY",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": -1.0,
            }
        )
    # USDJPY bearish: 5 CANDs, 1 win
    for i in range(1):
        cands.append(
            {
                "symbol": "USDJPY",
                "candle_close_time": "2026-01-15T17:00:00Z",
                "r_multiple": 1.5,
            }
        )
    for i in range(4):
        cands.append(
            {
                "symbol": "USDJPY",
                "candle_close_time": "2026-01-15T17:00:00Z",
                "r_multiple": -1.0,
            }
        )

    assert len(cands) == 30

    matrix = build_wr_matrix(cands, idx)

    # 4 cells exactly
    assert len(matrix.cells) == 4
    assert matrix.total_cands == 30
    assert matrix.untagged_count == 0

    # n per cell
    assert matrix.cell_count("XAUUSD", "bullish") == 8
    assert matrix.cell_count("XAUUSD", "bearish") == 7
    assert matrix.cell_count("USDJPY", "bullish") == 10
    assert matrix.cell_count("USDJPY", "bearish") == 5

    # WR per cell
    assert matrix.cells[("XAUUSD", "bullish")]["wr"] == pytest.approx(5 / 8)
    assert matrix.cells[("XAUUSD", "bearish")]["wr"] == pytest.approx(2 / 7)
    assert matrix.cells[("USDJPY", "bullish")]["wr"] == pytest.approx(7 / 10)
    assert matrix.cells[("USDJPY", "bearish")]["wr"] == pytest.approx(1 / 5)


def test_build_wr_matrix_skips_unrealised_cands(tmp_path: Path) -> None:
    """CANDs with no numeric r_multiple are excluded from the matrix."""
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish")],
    )
    idx = load_regime_index(log_path)

    cands = [
        {
            "symbol": "XAUUSD",
            "candle_close_time": "2026-01-15T09:00:00Z",
            "r_multiple": 1.5,
        },
        {
            "symbol": "XAUUSD",
            "candle_close_time": "2026-01-15T09:00:00Z",
            "r_multiple": None,  # missing outcome
        },
        {
            "symbol": "XAUUSD",
            "candle_close_time": "2026-01-15T09:00:00Z",
            # no r_multiple key at all
        },
    ]

    matrix = build_wr_matrix(cands, idx)
    assert matrix.total_cands == 1
    assert matrix.cell_count("XAUUSD", "bullish") == 1


def test_build_wr_matrix_untagged_counted(tmp_path: Path) -> None:
    """CANDs that miss an H4 window land in UNTAGGED + counted on the matrix."""
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish")],
    )
    idx = load_regime_index(log_path)

    cands = [
        # tagged
        {
            "symbol": "XAUUSD",
            "candle_close_time": "2026-01-15T09:00:00Z",
            "r_multiple": 1.5,
        },
        # untagged: stale (>6h)
        {
            "symbol": "XAUUSD",
            "candle_close_time": "2026-01-15T20:00:00Z",
            "r_multiple": -1.0,
        },
    ]
    matrix = build_wr_matrix(cands, idx)

    assert matrix.total_cands == 2
    assert matrix.untagged_count == 1
    assert matrix.cell_count("XAUUSD", "bullish") == 1
    assert matrix.cell_count("XAUUSD", UNTAGGED) == 1


# ---------------------------------------------------------------------------
# Wilson CI hand-verification
# ---------------------------------------------------------------------------


def test_wilson_ci_k8_n10() -> None:
    """k=8, n=10 -> Wilson 95% CI ~ (0.4439, 0.9479).

    Hand computation::

        p = 0.8, z = 1.95996
        z^2 = 3.84146
        denom = 1 + z^2/n = 1 + 0.384146 = 1.384146
        center = (0.8 + 0.192073) / 1.384146 = 0.71641
        margin = z * sqrt(0.16/10 + z^2/(4*100)) / denom
               = 1.95996 * sqrt(0.016 + 0.0096037) / 1.384146
               = 1.95996 * sqrt(0.0256037) / 1.384146
               = 1.95996 * 0.160012 / 1.384146
               = 0.22657
        lo = 0.71641 - 0.22657 = 0.48984
        hi = 0.71641 + 0.22657 = 0.94298

    We allow a 1e-3 absolute tolerance for the floating-point arithmetic.
    """
    lo, hi = wilson_ci(8, 10)
    assert lo == pytest.approx(0.48984, abs=1e-3)
    assert hi == pytest.approx(0.94298, abs=1e-3)
    # Sanity: interval is centred above 0.5 (since p=0.8) and lies in [0,1].
    assert 0.0 <= lo < hi <= 1.0
    assert 0.5 < (lo + hi) / 2 < 0.9


def test_wilson_ci_zero_observations() -> None:
    """n=0 -> maximally uninformative interval (0, 1)."""
    assert wilson_ci(0, 0) == (0.0, 1.0)


def test_wilson_ci_p0_and_p1() -> None:
    """Boundary cases: p=0 (k=0, n=10) and p=1 (k=10, n=10)."""
    lo0, hi0 = wilson_ci(0, 10)
    assert lo0 == 0.0
    assert 0.27 < hi0 < 0.31  # known: Wilson(0/10, 95%) hi ~= 0.2775
    lo1, hi1 = wilson_ci(10, 10)
    assert hi1 == 1.0
    assert 0.69 < lo1 < 0.73


def test_wilson_ci_k_out_of_range() -> None:
    with pytest.raises(ValueError):
        wilson_ci(-1, 10)
    with pytest.raises(ValueError):
        wilson_ci(11, 10)


# ---------------------------------------------------------------------------
# Low-n flagging
# ---------------------------------------------------------------------------


def test_low_n_flagging_dataframe(tmp_path: Path) -> None:
    """Cells with n < LOW_N_THRESHOLD have low_n=True in the dataframe view."""
    log_path = tmp_path / "structure_log.jsonl"
    rows = [
        _h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish"),
        _h4_row(ts="2026-01-15T16:00:00Z", symbol="XAUUSD", v2="bearish"),
    ]
    _write_jsonl(log_path, rows)
    idx = load_regime_index(log_path)

    # bullish: 12 CANDs (>= threshold)
    # bearish: 4 CANDs (< threshold) -> LOW_N
    cands = []
    for _ in range(12):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": 1.0,
            }
        )
    for _ in range(4):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T17:00:00Z",
                "r_multiple": -1.0,
            }
        )

    matrix = build_wr_matrix(cands, idx)
    df = matrix.to_dataframe()
    rows_by_regime = {r["regime"]: r for r in df}
    assert rows_by_regime["bullish"]["low_n"] is False
    assert rows_by_regime["bearish"]["low_n"] is True
    # threshold boundary: exactly LOW_N_THRESHOLD-1 -> low_n
    assert LOW_N_THRESHOLD == 10


def test_summary_picks_best_and_worst_excluding_low_n(tmp_path: Path) -> None:
    """Summary's best/worst regime ranking ignores LOW_N cells."""
    log_path = tmp_path / "structure_log.jsonl"
    rows = [
        _h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish"),
        _h4_row(ts="2026-01-15T16:00:00Z", symbol="XAUUSD", v2="bearish"),
        _h4_row(ts="2026-01-15T08:00:00Z", symbol="USDJPY", v2="bullish"),
    ]
    _write_jsonl(log_path, rows)
    idx = load_regime_index(log_path)

    cands = []
    # XAUUSD bullish: 10 CANDs, 9 wins (90%) — eligible for ranking
    for _ in range(9):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": 1.0,
            }
        )
    cands.append(
        {
            "symbol": "XAUUSD",
            "candle_close_time": "2026-01-15T09:00:00Z",
            "r_multiple": -1.0,
        }
    )
    # XAUUSD bearish: 5 CANDs (LOW_N) -> excluded from ranking
    for _ in range(5):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T17:00:00Z",
                "r_multiple": -1.0,
            }
        )
    # USDJPY bullish: 10 CANDs, 3 wins (30%) — eligible for ranking
    for _ in range(3):
        cands.append(
            {
                "symbol": "USDJPY",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": 1.0,
            }
        )
    for _ in range(7):
        cands.append(
            {
                "symbol": "USDJPY",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": -1.0,
            }
        )

    matrix = build_wr_matrix(cands, idx)
    summary = matrix.summary()

    # Only 'bullish' has any non-LOW_N cells; bearish (n=5) is excluded.
    assert summary["best_regime"] == "bullish"
    assert summary["worst_regime"] == "bullish"
    assert summary["best_avg_wr"] == pytest.approx((0.9 + 0.3) / 2)


def test_summary_excludes_untagged_from_ranking(tmp_path: Path) -> None:
    """UNTAGGED bucket must NOT be considered a regime in best/worst ranking.

    Build a matrix where the UNTAGGED bucket has the worst WR (0%) but is
    fully populated (n>=10). The summary should still pick a real regime
    as 'worst', not UNTAGGED — UNTAGGED is a coverage bookkeeping bucket,
    not a market regime.
    """
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish")],
    )
    idx = load_regime_index(log_path)

    cands = []
    # XAUUSD bullish: n=10, WR=80%
    for _ in range(8):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": 1.0,
            }
        )
    for _ in range(2):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-15T09:00:00Z",
                "r_multiple": -1.0,
            }
        )
    # XAUUSD UNTAGGED: n=10, WR=0% (all losses; outside freshness window)
    for _ in range(10):
        cands.append(
            {
                "symbol": "XAUUSD",
                "candle_close_time": "2026-01-16T20:00:00Z",  # >>6h after H4 row
                "r_multiple": -1.0,
            }
        )

    matrix = build_wr_matrix(cands, idx)
    summary = matrix.summary()

    # Even though UNTAGGED has the worst WR (0%) it must NOT be the worst
    # regime — only real regimes are ranked.
    assert summary["best_regime"] == "bullish"
    assert summary["worst_regime"] == "bullish"  # only one real regime
    assert "bullish" in summary["regime_avg_wr"]
    assert UNTAGGED in summary["regime_avg_wr"]  # still tracked in averages
    # UNTAGGED's WR is 0% but it's excluded from the (best, worst) tuple.
    assert summary["regime_avg_wr"][UNTAGGED] == 0.0


def test_to_dataframe_handles_empty_matrix() -> None:
    """An empty matrix yields an empty dataframe + null summary fields."""
    matrix = RegimeMatrix()
    assert matrix.to_dataframe() == []
    summary = matrix.summary()
    assert summary["best_regime"] is None
    assert summary["worst_regime"] is None
    assert summary["wr_delta_pp"] is None
    assert summary["untagged_fraction"] is None


# ---------------------------------------------------------------------------
# Type / argument validation
# ---------------------------------------------------------------------------


def test_regime_index_lookup_naive_datetime_treated_as_utc(tmp_path: Path) -> None:
    """Naive datetime arguments are interpreted as UTC by lookup."""
    log_path = tmp_path / "structure_log.jsonl"
    _write_jsonl(
        log_path,
        [_h4_row(ts="2026-01-15T08:00:00Z", symbol="XAUUSD", v2="bullish")],
    )
    idx = load_regime_index(log_path)
    naive = datetime(2026, 1, 15, 9, 0, 0)
    aware = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    assert idx.lookup("XAUUSD", naive) == idx.lookup("XAUUSD", aware)
