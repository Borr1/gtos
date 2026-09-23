"""Tests for knowledge base seeding and KB context injection."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from scripts.seed_knowledge_base import (
    build_trade_index,
    compute_rolling_stats,
    build_failure_patterns,
    extract_gold_trades,
    extract_gbpusd_trades,
    generate_insights,
    seed_knowledge_base,
)
from src.prompts import primary_analyzer_prompt


# Isolation fixture — test_seed_from_real_data at lines 286-287 opens
# Path("knowledge_base_backtest/analysis/system_improvements_data_20260403.json")
# and Path("knowledge_base_backtest/analysis/gbpusd_batch_deep_analysis_data_20260403.json")
# with hardcoded relative paths. Under chdir(tmp_path) those paths will not exist
# in the tmp tree — the test's existing pytest.skip() guard (line 288-289) handles
# this gracefully, so no test that touched live knowledge_base_backtest/ will do so now.
@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_gold_trades():
    return [
        {"trade_id": "g1", "date": "2025-01-01", "symbol": "XAUUSD",
         "direction": "LONG", "kill_zone": "ny", "grade": None,
         "framework": "ob_retest", "outcome": "WIN", "r_multiple": 1.5,
         "exit_type": "TP1"},
        {"trade_id": "g2", "date": "2025-01-02", "symbol": "XAUUSD",
         "direction": "LONG", "kill_zone": "london", "grade": None,
         "framework": "ob_retest", "outcome": "LOSS", "r_multiple": -1.0,
         "exit_type": "SL"},
        {"trade_id": "g3", "date": "2025-01-03", "symbol": "XAUUSD",
         "direction": "SHORT", "kill_zone": "ny", "grade": None,
         "framework": "ob_retest", "outcome": "WIN", "r_multiple": 0.5,
         "exit_type": "TIMEOUT"},
    ]


@pytest.fixture
def sample_gbpusd_trades():
    return [
        {"trade_id": "gb1", "date": "2025-01-04", "symbol": "GBPUSD",
         "direction": "LONG", "kill_zone": "london", "grade": "A+",
         "framework": "ob_retest", "outcome": "WIN", "r_multiple": 1.5,
         "exit_type": "CLOSED_TP1"},
        {"trade_id": "gb2", "date": "2025-01-05", "symbol": "GBPUSD",
         "direction": "SHORT", "kill_zone": "ny", "grade": "A",
         "framework": "ob_retest", "outcome": "LOSS", "r_multiple": -1.0,
         "exit_type": "SL"},
    ]


@pytest.fixture
def sample_trade_index(sample_gold_trades, sample_gbpusd_trades):
    return build_trade_index(sample_gold_trades, sample_gbpusd_trades)


# ── Test: Build Trade Index ───────────────────────────────────────────


class TestBuildTradeIndex:
    def test_count_matches_input(self, sample_gold_trades, sample_gbpusd_trades):
        idx = build_trade_index(sample_gold_trades, sample_gbpusd_trades)
        assert idx["trade_count"] == len(sample_gold_trades) + len(sample_gbpusd_trades)
        assert len(idx["trades"]) == 5

    def test_structure(self, sample_trade_index):
        assert "version" in sample_trade_index
        assert "trades" in sample_trade_index
        assert "trade_count" in sample_trade_index
        for t in sample_trade_index["trades"]:
            assert "trade_id" in t
            assert "date" in t
            assert "symbol" in t
            assert "outcome" in t
            assert "r_multiple" in t

    def test_sorted_by_date(self, sample_trade_index):
        dates = [t["date"] for t in sample_trade_index["trades"]]
        assert dates == sorted(dates)


# ── Test: Rolling Stats ──────────────────────────────────────────────


class TestRollingStats:
    def test_wr_calculation(self):
        """3 wins, 2 losses → WR = 0.6. Exact math check."""
        trades = [
            {"outcome": "WIN", "r_multiple": 1.5, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "WIN", "r_multiple": 1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "LOSS", "r_multiple": -1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "WIN", "r_multiple": 0.5, "symbol": "X", "kill_zone": "london", "grade": None},
            {"outcome": "LOSS", "r_multiple": -1.0, "symbol": "X", "kill_zone": "london", "grade": None},
        ]
        idx = {"trades": trades}
        stats = compute_rolling_stats(idx)
        assert stats["overall"]["win_rate"] == 0.6
        assert stats["overall"]["n"] == 5

    def test_expectancy_calculation(self):
        """Known R values → exact expectancy."""
        trades = [
            {"outcome": "WIN", "r_multiple": 2.0, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "LOSS", "r_multiple": -1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "WIN", "r_multiple": 1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
        ]
        idx = {"trades": trades}
        stats = compute_rolling_stats(idx)
        # Expected: (2.0 + -1.0 + 1.0) / 3 = 0.6667
        assert abs(stats["overall"]["expectancy"] - 0.6667) < 0.001

    def test_by_instrument(self, sample_trade_index):
        stats = compute_rolling_stats(sample_trade_index)
        assert "XAUUSD" in stats["by_instrument"]
        assert "GBPUSD" in stats["by_instrument"]
        assert stats["by_instrument"]["XAUUSD"]["n"] == 3
        assert stats["by_instrument"]["GBPUSD"]["n"] == 2

    def test_profit_factor(self):
        trades = [
            {"outcome": "WIN", "r_multiple": 3.0, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "LOSS", "r_multiple": -1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
        ]
        idx = {"trades": trades}
        stats = compute_rolling_stats(idx)
        # PF = 3.0 / 1.0 = 3.0
        assert stats["overall"]["profit_factor"] == 3.0

    def test_max_consecutive_losses(self):
        trades = [
            {"outcome": "WIN", "r_multiple": 1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "LOSS", "r_multiple": -1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "LOSS", "r_multiple": -1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "LOSS", "r_multiple": -1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
            {"outcome": "WIN", "r_multiple": 1.0, "symbol": "X", "kill_zone": "ny", "grade": None},
        ]
        idx = {"trades": trades}
        stats = compute_rolling_stats(idx)
        assert stats["overall"]["max_consecutive_losses"] == 3


# ── Test: Failure Patterns ───────────────────────────────────────────


class TestFailurePatterns:
    def test_patterns_built(self, sample_trade_index):
        fp = build_failure_patterns(sample_trade_index)
        assert "active_patterns" in fp
        assert len(fp["active_patterns"]) > 0
        for p in fp["active_patterns"]:
            assert "pattern_id" in p
            assert "description" in p
            assert "severity" in p
            assert "evidence" in p


# ── Test: Insights YAML ──────────────────────────────────────────────


class TestInsightsYAML:
    def test_yaml_parseable(self, sample_trade_index):
        stats = compute_rolling_stats(sample_trade_index)
        fp = build_failure_patterns(sample_trade_index)
        yaml_str = generate_insights(stats, fp)

        # Must be valid YAML
        parsed = yaml.safe_load(yaml_str)
        assert parsed is not None
        assert "summary" in parsed
        assert "last_10" in parsed
        assert "cautions" in parsed
        assert parsed["summary"]["total_trades"] == 5


# ── Test: KB Context Assembly ────────────────────────────────────────


class TestKBContextAssembly:
    def test_assembly_from_files(self, tmp_path):
        """Assemble KB context from files on disk, verify structure."""
        from src.components.knowledge_base import KnowledgeBase

        kb = KnowledgeBase(base_path=str(tmp_path))
        kb.initialize_rules()

        # Write test trade index
        (tmp_path / "index" / "_trade_index.json").write_text(json.dumps({
            "trades": [
                {"trade_id": "t1", "date": "2025-01-01", "outcome": "WIN", "r_multiple": 1.5},
            ],
        }))
        # Write rolling stats
        (tmp_path / "statistics" / "rolling_stats.json").write_text(json.dumps({
            "overall": {"n": 1, "win_rate": 1.0, "expectancy": 1.5},
        }))
        # Write failure patterns
        (tmp_path / "patterns" / "failure_patterns.json").write_text(json.dumps({
            "active_patterns": [
                {"pattern_id": "fp1", "description": "Test pattern", "severity": "HIGH"},
            ],
        }))

        ctx = kb.assemble_layer1_context()
        assert "last_10_trades" in ctx
        assert "rolling_stats" in ctx
        assert "active_failure_patterns" in ctx
        assert len(ctx["active_failure_patterns"]) == 1

    def test_empty_graceful(self, tmp_path):
        """No KB files → empty dict, no crash."""
        from src.components.knowledge_base import KnowledgeBase

        kb = KnowledgeBase(base_path=str(tmp_path))
        # assemble_layer1_context should not crash with empty files
        ctx = kb.assemble_layer1_context()
        assert isinstance(ctx, dict)
        assert ctx.get("last_10_trades") == []


# ── Test: Prompt KB Context Injection ────────────────────────────────


class TestPromptKBInjection:
    @pytest.fixture
    def sample_mso(self):
        from tests.test_knowledge_base import _make_bullish_mso
        return _make_bullish_mso()

    def test_prompt_includes_kb_context(self, sample_mso):
        """Build prompt with kb_context, verify context appears."""
        kb_context = {
            "layer1": {
                "rolling_stats": {
                    "overall": {"n": 60, "win_rate": 0.62, "expectancy": 0.45, "profit_factor": 2.5},
                },
                "last_10_trades": [
                    {"outcome": "WIN", "r_multiple": 1.5},
                    {"outcome": "LOSS", "r_multiple": -1.0},
                ],
                "active_failure_patterns": [
                    {"description": "Narrow Asian range has 33% WR", "severity": "HIGH"},
                ],
            },
            "layer2": {},
        }
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, kb_context, "2026-04-05T07:30:00Z",
        )
        assert "System Context" in msg
        assert "60 trades" in msg
        assert "62% WR" in msg
        assert "Narrow Asian range" in msg
        assert "Dynamic Market Data" in msg

    def test_prompt_without_kb_context(self, sample_mso):
        """Build prompt with empty kb_context, verify no crash, no empty section."""
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, {}, "2026-04-05T07:30:00Z",
        )
        assert isinstance(msg, str)
        assert "System Context" not in msg
        assert "Dynamic Market Data" in msg

    def test_prompt_with_none_kb_context(self, sample_mso):
        """Build prompt with None kb_context, verify no crash."""
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, None, "2026-04-05T07:30:00Z",
        )
        assert isinstance(msg, str)
        assert "Dynamic Market Data" in msg


# ── Test: Full Seeding Pipeline ──────────────────────────────────────


class TestFullSeedingPipeline:
    def test_seed_from_real_data(self):
        """Verify seeding from actual source files produces 60 trades."""
        gold_src = Path("knowledge_base_backtest/analysis/system_improvements_data_20260403.json")
        gbp_src = Path("knowledge_base_backtest/analysis/gbpusd_batch_deep_analysis_data_20260403.json")
        if not gold_src.exists() or not gbp_src.exists():
            pytest.skip("Source data files not available")

        gold = extract_gold_trades(gold_src)
        gbp = extract_gbpusd_trades(gbp_src)
        assert len(gold) == 18
        assert len(gbp) == 42

        idx = build_trade_index(gold, gbp)
        assert idx["trade_count"] == 60

        stats = compute_rolling_stats(idx)
        assert stats["overall"]["n"] == 60
        assert 0 < stats["overall"]["win_rate"] < 1
