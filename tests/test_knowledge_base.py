"""Tests for Component 5 — Knowledge Base."""

from __future__ import annotations

import json

import pytest

from src.components.knowledge_base import KnowledgeBase
from src.models.trade_models import (
    NoTradeRecord,
    NoTradeReasoning,
    PostmortemRecord,
    SessionManifest,
    TradeRecord,
)


@pytest.fixture
def kb(tmp_path):
    """Create a KnowledgeBase backed by a temporary directory."""
    return KnowledgeBase(base_path=str(tmp_path))


def _sample_trade(**overrides) -> TradeRecord:
    defaults = dict(
        trade_id="tr_2026-03-28_001",
        date="2026-03-28",
        day_of_week="Friday",
        direction="LONG",
        entry_price=3039.85,
        stop_loss=3033.50,
        take_profit_1=3048.10,
        setup_grade="A+",
        daily_bias="bullish",
        h4_aligned=True,
        liquidity_swept="asian_low",
        displacement_quality="strong",
        regime="trending_bullish",
        outcome="WIN",
        r_multiple=3.48,
        debate_confidence=82,
    )
    defaults.update(overrides)
    return TradeRecord(**defaults)


def _sample_no_trade() -> NoTradeRecord:
    return NoTradeRecord(
        record_id="nt_2026-03-27_0715",
        date="2026-03-27",
        candle_time="2026-03-27T07:15:00Z",
        reason="Daily structure ranging",
        reasoning=NoTradeReasoning(
            daily_bias="ranging",
            stopped_at_step=1,
            full_explanation="No directional conviction.",
        ),
    )


def _sample_session() -> SessionManifest:
    return SessionManifest(
        date="2026-03-28",
        day_of_week="Friday",
        session_start_utc="2026-03-28T06:45:00Z",
        session_end_utc="2026-03-28T09:30:00Z",
        api_calls_count=6,
        api_cost_estimate_usd=0.28,
    )


def _sample_postmortem() -> PostmortemRecord:
    return PostmortemRecord(
        trade_id="tr_2026-03-28_001",
        generated_at="2026-03-28T11:00:00Z",
        model_used="claude-sonnet-4-20250514",
        daily_bias_accuracy="correct",
        llm_score=88,
        summary="LONG after clean Asian low sweep.",
    )


# -------------------------------------------------------------------
# Write + Load round-trips
# -------------------------------------------------------------------

class TestWriteAndLoad:

    def test_write_and_load_trade(self, kb):
        trade = _sample_trade()
        trade_id = kb.write_trade(trade)
        assert trade_id.startswith("tr_2026-03-28_")

        loaded = kb.load_trade(trade_id)
        assert loaded is not None
        assert loaded.trade_id == trade_id
        assert loaded.direction == "LONG"
        assert loaded.outcome == "WIN"
        assert loaded.r_multiple == 3.48

    def test_write_and_load_no_trade(self, kb):
        record = _sample_no_trade()
        rid = kb.write_no_trade(record)
        assert rid == "nt_2026-03-27_0715"

        # Verify the file exists
        filepath = kb.base / "no_trades" / f"{rid}.yaml"
        assert filepath.exists()

    def test_write_and_load_session(self, kb):
        manifest = _sample_session()
        fname = kb.write_session_manifest(manifest)
        assert fname == "2026-03-28_session.json"

        loaded = kb.load_session("2026-03-28")
        assert loaded is not None
        assert loaded.day_of_week == "Friday"
        assert loaded.api_calls_count == 6

    def test_write_and_load_postmortem(self, kb):
        pm = _sample_postmortem()
        fname = kb.write_postmortem(pm)
        assert "pm_tr_2026-03-28_001" in fname

        loaded = kb.load_postmortem("tr_2026-03-28_001")
        assert loaded is not None
        assert loaded.llm_score == 88

    def test_load_nonexistent_returns_none(self, kb):
        assert kb.load_trade("tr_9999-01-01_001") is None
        assert kb.load_session("9999-01-01") is None
        assert kb.load_postmortem("tr_9999-01-01_001") is None


# -------------------------------------------------------------------
# Trade index
# -------------------------------------------------------------------

class TestTradeIndex:

    def test_trade_index_update(self, kb):
        t1 = _sample_trade(date="2026-03-28", outcome="WIN", r_multiple=3.0)
        t2 = _sample_trade(date="2026-03-28", outcome="LOSS", r_multiple=-1.0)
        kb.write_trade(t1)
        kb.write_trade(t2)

        last = kb.get_last_n_trades(10)
        assert len(last) == 2
        assert last[0]["outcome"] == "WIN"
        assert last[1]["outcome"] == "LOSS"

    def test_get_last_n_returns_tail(self, kb):
        for i in range(5):
            t = _sample_trade(
                date=f"2026-03-{20 + i:02d}",
                outcome="WIN" if i % 2 == 0 else "LOSS",
                r_multiple=float(i),
            )
            kb.write_trade(t)

        last2 = kb.get_last_n_trades(2)
        assert len(last2) == 2
        # Should be the last two entries
        assert last2[0]["r_multiple"] == 3.0
        assert last2[1]["r_multiple"] == 4.0

    def test_auto_increment_trade_id(self, kb):
        t1 = _sample_trade(date="2026-04-01")
        t2 = _sample_trade(date="2026-04-01")
        t3 = _sample_trade(date="2026-04-01")

        id1 = kb.write_trade(t1)
        id2 = kb.write_trade(t2)
        id3 = kb.write_trade(t3)

        assert id1 == "tr_2026-04-01_001"
        assert id2 == "tr_2026-04-01_002"
        assert id3 == "tr_2026-04-01_003"

    def test_auto_increment_different_dates(self, kb):
        t1 = _sample_trade(date="2026-04-01")
        t2 = _sample_trade(date="2026-04-02")

        id1 = kb.write_trade(t1)
        id2 = kb.write_trade(t2)

        assert id1 == "tr_2026-04-01_001"
        assert id2 == "tr_2026-04-02_001"


# -------------------------------------------------------------------
# Rolling statistics
# -------------------------------------------------------------------

class TestRollingStats:

    def test_rolling_stats_update(self, kb):
        win = _sample_trade(outcome="WIN", r_multiple=3.0)
        win.trade_id = kb.write_trade(win)
        kb.update_rolling_stats(win)

        stats = kb.load_rolling_stats()
        assert stats["total_trades"] == 1
        assert stats["wins"] == 1
        assert stats["losses"] == 0
        assert stats["win_rate"] == 1.0
        assert stats["gross_profit_r"] == 3.0

    def test_rolling_stats_after_loss(self, kb):
        win = _sample_trade(outcome="WIN", r_multiple=3.0)
        loss = _sample_trade(outcome="LOSS", r_multiple=-1.0, date="2026-03-29")

        win.trade_id = kb.write_trade(win)
        kb.update_rolling_stats(win)
        loss.trade_id = kb.write_trade(loss)
        kb.update_rolling_stats(loss)

        stats = kb.load_rolling_stats()
        assert stats["total_trades"] == 2
        assert stats["wins"] == 1
        assert stats["losses"] == 1
        assert stats["win_rate"] == 0.5
        assert stats["gross_loss_r"] == 1.0
        # Expectancy = 0.5 * 3.0 - 0.5 * 1.0 = 1.0
        assert abs(stats["expectancy"] - 1.0) < 0.01

    def test_rolling_stats_consecutive_losses(self, kb):
        for i in range(3):
            loss = _sample_trade(
                outcome="LOSS",
                r_multiple=-1.0,
                date=f"2026-04-{10 + i:02d}",
            )
            loss.trade_id = kb.write_trade(loss)
            kb.update_rolling_stats(loss)

        stats = kb.load_rolling_stats()
        assert stats["consecutive_losses"] == 3
        assert stats["max_consecutive_losses"] == 3

    def test_rolling_stats_condition_breakdown(self, kb):
        trade = _sample_trade(
            day_of_week="Tuesday",
            liquidity_swept="asian_low",
            displacement_quality="strong",
            outcome="WIN",
            r_multiple=3.0,
        )
        trade.trade_id = kb.write_trade(trade)
        kb.update_rolling_stats(trade)

        stats = kb.load_rolling_stats()
        key = "Tuesday_asian_low_strong"
        assert key in stats["condition_breakdown"]
        assert stats["condition_breakdown"][key]["total"] == 1
        assert stats["condition_breakdown"][key]["wins"] == 1

    def test_rolling_stats_profit_factor(self, kb):
        # 2 wins of 3R each, 1 loss of 1R
        for i, (outcome, r) in enumerate([("WIN", 3.0), ("WIN", 3.0), ("LOSS", -1.0)]):
            t = _sample_trade(outcome=outcome, r_multiple=r, date=f"2026-04-{10+i:02d}")
            t.trade_id = kb.write_trade(t)
            kb.update_rolling_stats(t)

        stats = kb.load_rolling_stats()
        # profit_factor = 6.0 / 1.0 = 6.0
        assert abs(stats["profit_factor"] - 6.0) < 0.01


# -------------------------------------------------------------------
# Layer 1 context
# -------------------------------------------------------------------

class TestLayerContext:

    def test_assemble_layer1_context(self, kb):
        # Seed some data
        trade = _sample_trade()
        trade.trade_id = kb.write_trade(trade)
        kb.update_rolling_stats(trade)
        kb.initialize_rules()

        ctx = kb.assemble_layer1_context()
        assert "last_10_trades" in ctx
        assert "rolling_stats" in ctx
        assert "active_failure_patterns" in ctx
        assert "current_regime" in ctx
        assert "pending_reviews" in ctx
        assert len(ctx["last_10_trades"]) == 1

    def test_assemble_layer2_empty(self, kb):
        """Layer 2 returns empty dict when no insights file exists."""
        ctx = kb.assemble_layer2_context()
        assert ctx == {}


# -------------------------------------------------------------------
# Pipeline state (ephemeral)
# -------------------------------------------------------------------

class TestPipelineState:

    def test_pipeline_state_overwrite(self, kb):
        kb.write_pipeline_state("test.json", {"version": 1})
        kb.write_pipeline_state("test.json", {"version": 2})

        data = json.loads(
            (kb.base / "pipeline_state" / "test.json").read_text()
        )
        assert data["version"] == 2


# -------------------------------------------------------------------
# Atomic write integrity
# -------------------------------------------------------------------

class TestAtomicWrite:

    def test_atomic_write_integrity(self, kb):
        """Write completes fully — no partial files left behind."""
        trade = _sample_trade()
        trade.trade_id = kb.write_trade(trade)

        # No .tmp files should remain
        import glob as g
        tmp_files = g.glob(str(kb.base / "**" / "*.tmp"), recursive=True)
        assert tmp_files == []

        # The actual file should exist and be valid YAML
        loaded = kb.load_trade(trade.trade_id)
        assert loaded is not None


# -------------------------------------------------------------------
# Rules initialization
# -------------------------------------------------------------------

class TestRulesInit:

    def test_initialize_rules(self, kb):
        kb.initialize_rules()
        assert (kb.base / "rules" / "active_rules.yaml").exists()
        assert (kb.base / "rules" / "base_rules.yaml").exists()
        assert (kb.base / "rules" / "rule_modifications_log.yaml").exists()
        assert (kb.base / "rules" / "pending_reviews.yaml").exists()

    def test_initialize_rules_idempotent(self, kb):
        kb.initialize_rules()
        # Modify active_rules
        from src.utils.file_io import atomic_write
        active = kb.base / "rules" / "active_rules.yaml"
        atomic_write(active, {"version": 99, "rules": {}})

        # Re-init should NOT overwrite
        kb.initialize_rules()
        from src.utils.file_io import load_yaml
        data = load_yaml(active)
        assert data["version"] == 99


# ===================================================================
# Vector store (LanceDB) tests
# ===================================================================

def _sample_postmortem(trade_id: str = "tr_2026-03-28_001",
                       summary: str = "Clean setup.",
                       llm_score: float = 88) -> PostmortemRecord:
    return PostmortemRecord(
        trade_id=trade_id,
        generated_at="2026-03-28T11:00:00Z",
        model_used="claude-sonnet-4-20250514",
        summary=summary,
        llm_score=llm_score,
    )


def _make_varied_trades():
    """Return 5 (TradeRecord, PostmortemRecord) pairs with varying conditions."""
    configs = [
        dict(
            date="2026-03-24", day_of_week="Monday", direction="LONG",
            daily_bias="bullish", h4_aligned=True,
            liquidity_swept="asian_low", displacement_quality="strong",
            regime="trending_bullish", setup_grade="A+",
            outcome="WIN", r_multiple=3.5,
            pm_summary="LONG Asian low sweep Monday strong disp, clean win.",
        ),
        dict(
            date="2026-03-25", day_of_week="Tuesday", direction="LONG",
            daily_bias="bullish", h4_aligned=True,
            liquidity_swept="asian_low", displacement_quality="medium",
            regime="trending_bullish", setup_grade="B+",
            outcome="LOSS", r_multiple=-1.0,
            pm_summary="Medium displacement insufficient, stopped out.",
        ),
        dict(
            date="2026-03-26", day_of_week="Wednesday", direction="SHORT",
            daily_bias="bearish", h4_aligned=True,
            liquidity_swept="pdh", displacement_quality="strong",
            regime="trending_bearish", setup_grade="A",
            outcome="WIN", r_multiple=4.0,
            pm_summary="SHORT PDH sweep Wed bearish, strong displacement, hit TP3.",
        ),
        dict(
            date="2026-03-27", day_of_week="Thursday", direction="LONG",
            daily_bias="bullish", h4_aligned=False,
            liquidity_swept="equal_lows", displacement_quality="weak",
            regime="ranging", setup_grade="C",
            outcome="LOSS", r_multiple=-1.0,
            pm_summary="Weak displacement in ranging regime, SL hit.",
        ),
        dict(
            date="2026-03-28", day_of_week="Friday", direction="LONG",
            daily_bias="bullish", h4_aligned=True,
            liquidity_swept="asian_low", displacement_quality="strong",
            regime="trending_bullish", setup_grade="A+",
            outcome="WIN", r_multiple=4.2,
            pm_summary="Friday Asian low sweep strong disp bullish, full TP run.",
        ),
    ]
    pairs = []
    for i, cfg in enumerate(configs, 1):
        pm_summary = cfg.pop("pm_summary")
        t = _sample_trade(**cfg)
        t.trade_id = f"tr_{cfg['date']}_{i:03d}"
        pm = _sample_postmortem(t.trade_id, pm_summary)
        pairs.append((t, pm))
    return pairs


def _make_bullish_mso():
    """Build a minimal MarketStateObject that looks like a bullish Asian low sweep."""
    from src.models.market_state_models import (
        DataQuality, LiquidityPool, LiquiditySweep, MarketStateObject,
        SessionLevels, StructureAnalysis, StructureEvent, TimeframeState,
    )
    bullish_struct = StructureAnalysis(direction="bullish", hh_count=3, hl_count=3)
    m15_state = TimeframeState(
        structure=bullish_struct,
        structure_events=[
            StructureEvent(
                type="BOS", direction="bullish",
                level_broken=3050.0, close_price=3055.0,
                candle_index=10, time="2026-03-28T07:30:00Z",
                displacement_present=True, displacement_ratio=2.4,
            ),
        ],
    )
    pool = LiquidityPool(type="asian_low", price=3038.50, side="low")
    sweep = LiquiditySweep(
        pool=pool, sweep_type="sweep",
        wick_extreme=3037.0, body_close=3039.0,
        candle_index=8, time="2026-03-28T07:15:00Z",
    )
    return MarketStateObject(
        timestamp_utc="2026-03-28T07:30:00Z",
        timeframes={
            "D1": TimeframeState(structure=bullish_struct),
            "H4": TimeframeState(structure=bullish_struct),
            "H1": TimeframeState(structure=bullish_struct),
            "M15": m15_state,
        },
        session_levels=SessionLevels(
            asian_high=3045.0, asian_low=3038.50, pdh=3052.0, pdl=3030.0,
        ),
        liquidity_pools=[pool],
        detected_sweeps=[sweep],
        data_quality=DataQuality(
            all_timeframes_complete=True, spread_normal=True,
            mt5_connected=True, timestamp_utc="2026-03-28T07:30:00Z",
        ),
    )


class _FakeEmbeddingModel:
    def encode(self, _text):
        class _Vector(list):
            def tolist(self):
                return list(self)

        return _Vector([0.1] * 384)


class _FakeSearch:
    def __init__(self, table):
        self.table = table

    def limit(self, n):
        self.table.last_limit = n
        return self

    def to_list(self):
        return list(self.table.rows)


class _FakeLanceTable:
    def __init__(self, rows):
        self.rows = rows
        self.last_limit = None

    def search(self, _query_vector):
        return _FakeSearch(self)

    def count_rows(self):
        return len(self.rows)


def _fake_vector_row(trade_id: str, distance: float) -> dict:
    return {
        "trade_id": trade_id,
        "_distance": distance,
        "outcome": "WIN",
        "r_multiple": 1.5,
        "setup_grade": "A",
        "text_summary": f"{trade_id} summary",
        "postmortem_summary": f"{trade_id} postmortem",
    }


class TestVectorDB:
    @pytest.fixture(autouse=True)
    def _patch_sentence_transformer(self, monkeypatch):
        import sentence_transformers

        monkeypatch.setattr(
            sentence_transformers,
            "SentenceTransformer",
            lambda _model_name: _FakeEmbeddingModel(),
        )

    def test_vectordb_initialization(self, kb):
        kb.initialize_vectordb()
        assert hasattr(kb, "_lance_table")
        assert hasattr(kb, "_embed_model")
        # Table should exist (even if empty after seed deletion)
        names = kb._lancedb.table_names()
        assert "trades" in list(getattr(names, "tables", names))

    def test_embed_and_retrieve(self, kb):
        kb.initialize_vectordb()
        pairs = _make_varied_trades()

        for trade, pm in pairs:
            kb.embed_trade(trade, pm)

        # Query with conditions similar to the bullish Asian low sweep trades
        mso = _make_bullish_mso()
        results = kb.find_similar_setups(mso, top_k=3)

        assert len(results) >= 1
        # The most similar should be one of the bullish Asian low sweep trades
        top = results[0]
        assert top["trade_id"] in (
            pairs[0][0].trade_id,   # Monday bullish asian_low strong
            pairs[4][0].trade_id,   # Friday bullish asian_low strong
        )
        assert "similarity_score" in top
        assert "outcome" in top

    def test_similarity_scoring(self, kb):
        kb.initialize_vectordb()
        pairs = _make_varied_trades()
        for trade, pm in pairs:
            kb.embed_trade(trade, pm)

        mso = _make_bullish_mso()
        results = kb.find_similar_setups(mso, top_k=5)

        for r in results:
            # Similarity should be a float
            assert isinstance(r["similarity_score"], float)

        # Results should be in descending order of similarity (ascending distance)
        scores = [r["similarity_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_layer3_retrieval_excludes_low_similarity_when_configured(self, tmp_path):
        config = {
            "retrieval": {
                "similar_setups_top_k": 2,
                "min_similarity_threshold": 0.75,
                "low_similarity_action": "exclude",
                "max_search_candidates": 4,
            }
        }
        kb = KnowledgeBase(base_path=str(tmp_path), config=config)
        kb._embed_model = _FakeEmbeddingModel()
        kb._lance_table = _FakeLanceTable([
            _fake_vector_row("high_1", 0.10),
            _fake_vector_row("low_1", 0.55),
            _fake_vector_row("high_2", 0.20),
            _fake_vector_row("low_2", 0.30),
        ])

        results = kb.find_similar_setups(_make_bullish_mso())

        assert [row["trade_id"] for row in results] == ["high_1", "high_2"]
        assert all(row["similarity_score"] >= 0.75 for row in results)
        assert kb._lance_table.last_limit == 4

    def test_layer3_retrieval_annotates_low_similarity_by_default(self, tmp_path):
        kb = KnowledgeBase(base_path=str(tmp_path))
        kb._embed_model = _FakeEmbeddingModel()
        kb._lance_table = _FakeLanceTable([
            _fake_vector_row("low_1", 0.55),
        ])

        results = kb.find_similar_setups(
            _make_bullish_mso(),
            top_k=1,
            min_similarity=0.75,
        )

        assert results[0]["trade_id"] == "low_1"
        assert results[0]["similarity_score"] == 0.45
        assert "note" in results[0]

    def test_assemble_full_context_uses_configured_layer3_filter(self, tmp_path):
        config = {
            "retrieval": {
                "similar_setups_top_k": 1,
                "min_similarity_threshold": 0.85,
                "low_similarity_action": "exclude",
                "max_search_candidates": 2,
            }
        }
        kb = KnowledgeBase(base_path=str(tmp_path), config=config)
        kb.initialize_rules()
        kb._embed_model = _FakeEmbeddingModel()
        kb._lance_table = _FakeLanceTable([
            _fake_vector_row("low_1", 0.20),
            _fake_vector_row("high_1", 0.05),
        ])

        ctx = kb.assemble_full_context(_make_bullish_mso(), config=config)

        assert [row["trade_id"] for row in ctx["layer3"]] == ["high_1"]
        assert kb._lance_table.last_limit == 2

    def test_empty_vectordb_query(self, kb):
        kb.initialize_vectordb()
        # No trades embedded — should return empty gracefully
        mso = _make_bullish_mso()
        results = kb.assemble_layer3_context(mso)
        assert isinstance(results, list)
        # Should have a note about no data
        if results:
            assert any("note" in r for r in results)

    def test_format_trade_summary(self, kb):
        trade = _sample_trade()
        text = kb.format_trade_summary(trade)
        assert "2026-03-28" in text
        assert "LONG" in text
        assert "bullish" in text
        assert "aligned" in text
        assert "asian_low" in text
        assert "strong" in text
        assert "Friday" in text
        assert "A+" in text
        assert "WIN" in text
        assert "3.5" in text  # r_multiple

    def test_format_current_conditions(self, kb):
        mso = _make_bullish_mso()
        text = kb.format_current_conditions(mso)
        assert "bullish" in text
        assert "aligned" in text
        assert "asian_low" in text
        assert "displacement" in text

    def test_assemble_full_context(self, kb):
        kb.initialize_vectordb()
        kb.initialize_rules()
        mso = _make_bullish_mso()
        ctx = kb.assemble_full_context(mso)
        assert "layer1" in ctx
        assert "layer2" in ctx
        assert "layer3" in ctx
