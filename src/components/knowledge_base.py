"""Component 5 — Knowledge Base (Memory System).

Three-layer retrieval system:
  Layer 1: Structured query (index files, stats, patterns)
  Layer 2: Compressed insights (YAML)
  Layer 3: Vector similarity (LanceDB)

Also handles trade logging, statistics computation, and insight distillation.
"""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Any, List, Optional

from src.models.market_state_models import MarketStateObject
from src.models.trade_models import (
    NoTradeRecord,
    PostmortemRecord,
    SessionManifest,
    TradeRecord,
)
from src.utils.file_io import atomic_write, load_json, load_yaml


_SUBDIRS = [
    "pipeline_state", "sessions", "trades", "no_trades",
    "postmortems", "journals/daily", "journals/weekly",
    "insights", "statistics", "patterns", "rules",
    "index", "vectordb", "meta",
]


class KnowledgeBase:
    """File-based storage and retrieval layer for the trading agent."""

    def __init__(self, base_path: str = "knowledge_base/", config: Optional[dict] = None) -> None:
        self.base = Path(base_path)
        self.config = config or {}
        self._ensure_dirs()

    # ------------------------------------------------------------------
    # Directory management
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        for sub in _SUBDIRS:
            (self.base / sub).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    def write_trade(self, trade: TradeRecord) -> str:
        """Write a TradeRecord to trades/tr_YYYY-MM-DD_NNN.yaml.

        Auto-increments NNN based on existing files for that date.
        Returns the trade_id.
        """
        date_str = trade.date
        existing = sorted(glob.glob(
            str(self.base / "trades" / f"tr_{date_str}_*.yaml")
        ))
        next_n = len(existing) + 1
        trade_id = f"tr_{date_str}_{next_n:03d}"
        trade.trade_id = trade_id

        filepath = self.base / "trades" / f"{trade_id}.yaml"
        atomic_write(filepath, trade.model_dump(mode="json"))
        self.update_trade_index(trade)
        return trade_id

    def write_no_trade(self, record: NoTradeRecord) -> str:
        """Write a NoTradeRecord to no_trades/nt_YYYY-MM-DD_HHMM.yaml."""
        filepath = self.base / "no_trades" / f"{record.record_id}.yaml"
        atomic_write(filepath, record.model_dump(mode="json"))
        return record.record_id

    def write_session_manifest(self, manifest: SessionManifest) -> str:
        """Write a SessionManifest to sessions/YYYY-MM-DD_session.json."""
        filename = f"{manifest.date}_session.json"
        filepath = self.base / "sessions" / filename
        atomic_write(filepath, manifest.model_dump(mode="json"))
        return filename

    def write_postmortem(self, postmortem: PostmortemRecord) -> str:
        """Write a PostmortemRecord to postmortems/pm_{trade_id}.yaml."""
        filename = f"pm_{postmortem.trade_id}.yaml"
        filepath = self.base / "postmortems" / filename
        atomic_write(filepath, postmortem.model_dump(mode="json"))
        return filename

    def write_pipeline_state(self, filename: str, data: dict) -> None:
        """Write ephemeral pipeline state (overwritten each candle)."""
        filepath = self.base / "pipeline_state" / filename
        atomic_write(filepath, data)

    # ------------------------------------------------------------------
    # Load methods
    # ------------------------------------------------------------------

    def load_trade(self, trade_id: str) -> Optional[TradeRecord]:
        filepath = self.base / "trades" / f"{trade_id}.yaml"
        data = load_yaml(filepath)
        if not data:
            return None
        return TradeRecord.model_validate(data)

    def load_session(self, date: str) -> Optional[SessionManifest]:
        filepath = self.base / "sessions" / f"{date}_session.json"
        data = load_json(filepath)
        if not data:
            return None
        return SessionManifest.model_validate(data)

    def load_postmortem(self, trade_id: str) -> Optional[PostmortemRecord]:
        filepath = self.base / "postmortems" / f"pm_{trade_id}.yaml"
        data = load_yaml(filepath)
        if not data:
            return None
        return PostmortemRecord.model_validate(data)

    # ------------------------------------------------------------------
    # Trade index
    # ------------------------------------------------------------------

    def get_last_n_trades(self, n: int = 10) -> List[dict]:
        """Return the last *n* entries from the trade index."""
        index = load_json(self.base / "index" / "_trade_index.json")
        trades = index.get("trades", [])
        return trades[-n:]

    def update_trade_index(self, trade: TradeRecord) -> None:
        """Append a lightweight summary to index/_trade_index.json."""
        filepath = self.base / "index" / "_trade_index.json"
        index = load_json(filepath)
        if "trades" not in index:
            index["trades"] = []

        entry = {
            "trade_id": trade.trade_id,
            "date": trade.date,
            "outcome": trade.outcome,
            "r_multiple": trade.r_multiple,
            "setup_grade": trade.setup_grade,
            "direction": trade.direction,
            "day_of_week": trade.day_of_week,
            "liquidity_swept": trade.liquidity_swept,
            "displacement_quality": trade.displacement_quality,
            "debate_confidence": trade.debate_confidence,
        }
        index["trades"].append(entry)
        atomic_write(filepath, index)

    # ------------------------------------------------------------------
    # Rolling statistics
    # ------------------------------------------------------------------

    def load_rolling_stats(self) -> dict:
        return load_json(self.base / "statistics" / "rolling_stats.json")

    def update_rolling_stats(self, trade: TradeRecord) -> None:
        """Recalculate rolling statistics after a completed trade."""
        filepath = self.base / "statistics" / "rolling_stats.json"
        stats = load_json(filepath)

        # Initialize defaults
        stats.setdefault("total_trades", 0)
        stats.setdefault("wins", 0)
        stats.setdefault("losses", 0)
        stats.setdefault("breakeven", 0)
        stats.setdefault("gross_profit_r", 0.0)
        stats.setdefault("gross_loss_r", 0.0)
        stats.setdefault("consecutive_losses", 0)
        stats.setdefault("max_consecutive_losses", 0)
        stats.setdefault("condition_breakdown", {})

        stats["total_trades"] += 1
        r = trade.r_multiple or 0.0

        if trade.outcome == "WIN":
            stats["wins"] += 1
            stats["gross_profit_r"] += r
            stats["consecutive_losses"] = 0
        elif trade.outcome == "LOSS":
            stats["losses"] += 1
            stats["gross_loss_r"] += abs(r)
            stats["consecutive_losses"] += 1
            stats["max_consecutive_losses"] = max(
                stats["max_consecutive_losses"],
                stats["consecutive_losses"],
            )
        else:
            stats["breakeven"] += 1
            stats["consecutive_losses"] = 0

        total = stats["total_trades"]
        stats["win_rate"] = stats["wins"] / total if total else 0.0

        avg_winner_r = stats["gross_profit_r"] / stats["wins"] if stats["wins"] else 0.0
        avg_loser_r = stats["gross_loss_r"] / stats["losses"] if stats["losses"] else 0.0
        stats["avg_winner_r"] = round(avg_winner_r, 3)
        stats["avg_loser_r"] = round(avg_loser_r, 3)

        stats["expectancy"] = round(
            (stats["win_rate"] * avg_winner_r)
            - ((1 - stats["win_rate"]) * avg_loser_r),
            3,
        )
        stats["profit_factor"] = round(
            stats["gross_profit_r"] / max(stats["gross_loss_r"], 0.01),
            3,
        )

        # Condition-level tracking
        parts = [
            trade.day_of_week or "unknown",
            trade.liquidity_swept or "unknown",
            trade.displacement_quality or "unknown",
        ]
        condition_key = "_".join(parts)
        cond = stats["condition_breakdown"].setdefault(
            condition_key, {"wins": 0, "losses": 0, "total": 0}
        )
        cond["total"] += 1
        if trade.outcome == "WIN":
            cond["wins"] += 1
        elif trade.outcome == "LOSS":
            cond["losses"] += 1

        atomic_write(filepath, stats)

    # ------------------------------------------------------------------
    # Insights / patterns / regime
    # ------------------------------------------------------------------

    def load_insights(self) -> dict:
        return load_yaml(self.base / "insights" / "current_insights.yaml")

    def load_failure_patterns(self) -> dict:
        return load_json(self.base / "patterns" / "failure_patterns.json")

    def load_regime(self) -> dict:
        return load_json(self.base / "statistics" / "regime_analysis.json")

    # ------------------------------------------------------------------
    # Three-layer context assembly
    # ------------------------------------------------------------------

    def assemble_layer1_context(self) -> dict:
        """Layer 1: structured query — last trades, stats, patterns, regime."""
        trade_index = load_json(self.base / "index" / "_trade_index.json")
        rolling_stats = self.load_rolling_stats()
        failure_patterns = self.load_failure_patterns()
        regime = self.load_regime()
        pending = load_yaml(self.base / "rules" / "pending_reviews.yaml")

        return {
            "last_10_trades": trade_index.get("trades", [])[-10:],
            "rolling_stats": rolling_stats,
            "active_failure_patterns": failure_patterns.get("active_patterns", failure_patterns.get("active", [])),
            "current_regime": regime.get("current_regime", "unknown"),
            "pending_reviews": pending.get("items", []),
        }

    def assemble_layer2_context(self) -> dict:
        """Layer 2: compressed insights (full YAML, small enough for prompt)."""
        return self.load_insights()

    # ------------------------------------------------------------------
    # Rules initialization
    # ------------------------------------------------------------------

    def initialize_rules(self) -> None:
        """Create default rule files if they don't exist."""
        rules_dir = self.base / "rules"
        active = rules_dir / "active_rules.yaml"
        base = rules_dir / "base_rules.yaml"
        mod_log = rules_dir / "rule_modifications_log.yaml"
        pending = rules_dir / "pending_reviews.yaml"

        default_rules = {
            "version": 1,
            "rules": {
                "max_risk_pct": 2.0,
                "max_daily_losses": 2,
                "min_rr": 1.5,
                "max_spread_cents": 100,
                "session_start_utc": "07:00",
                "session_end_utc": "09:30",
                "debate_required": False,
                "min_debate_confidence": 50,
            },
        }

        if not active.exists():
            atomic_write(active, default_rules)
        if not base.exists():
            atomic_write(base, default_rules)
        if not mod_log.exists():
            atomic_write(mod_log, {"modifications": []})
        if not pending.exists():
            atomic_write(pending, {"items": []})

    # ------------------------------------------------------------------
    # Vector store (Layer 3 — LanceDB)
    # ------------------------------------------------------------------

    def initialize_vectordb(self) -> None:
        """Connect to LanceDB and create the 'trades' table if needed.

        Loads the sentence-transformers embedding model on first call.
        """
        import lancedb
        from sentence_transformers import SentenceTransformer

        self._lancedb = lancedb.connect(str(self.base / "vectordb"))
        retrieval_cfg = self._retrieval_config()
        embedding_model = retrieval_cfg.get("embedding_model", "all-MiniLM-L6-v2")
        self._embed_model = SentenceTransformer(embedding_model)

        existing = self._lancedb.table_names()
        # table_names() may return a list or a ListTablesResponse
        existing_names = list(getattr(existing, "tables", existing))
        if "trades" not in existing_names:
            # Seed with an empty-ish sentinel row then delete it.
            # LanceDB needs at least one row to infer the schema.
            seed = [{
                "trade_id": "__seed__",
                "vector": [0.0] * 384,
                "text_summary": "",
                "outcome": "",
                "r_multiple": 0.0,
                "setup_grade": "",
                "direction": "",
                "day_of_week": "",
                "liquidity_type": "",
                "displacement_quality": "",
                "regime": "",
                "date": "",
                "daily_bias": "",
                "h4_aligned": False,
                "debate_confidence": 0,
                "postmortem_summary": "",
            }]
            tbl = self._lancedb.create_table("trades", seed)
            tbl.delete('trade_id = "__seed__"')
        self._lance_table = self._lancedb.open_table("trades")

    @staticmethod
    def format_trade_summary(trade: TradeRecord) -> str:
        """Generate text summary used for embedding."""
        aligned = "aligned" if trade.h4_aligned else "conflicting"
        r_str = f"{trade.r_multiple:.1f}" if trade.r_multiple is not None else "0.0"
        return (
            f"{trade.date} | {trade.direction} | "
            f"{trade.daily_bias or 'unknown'} Daily {aligned} H4 | "
            f"{trade.liquidity_swept or 'unknown'} sweep "
            f"{trade.displacement_quality or 'unknown'} | "
            f"{trade.displacement_quality or 'unknown'} displacement | "
            f"{trade.day_of_week} | "
            f"{trade.regime or 'unknown'} regime | "
            f"{trade.setup_grade} grade | "
            f"{trade.outcome or 'unknown'} {r_str}R"
        )

    @staticmethod
    def format_current_conditions(market_state: MarketStateObject) -> str:
        """Generate text summary of current market conditions for similarity query."""
        d1 = market_state.timeframes.get("D1")
        h4 = market_state.timeframes.get("H4")

        daily_dir = d1.structure.direction if d1 else "unknown"
        h4_dir = h4.structure.direction if h4 else "unknown"
        aligned = "aligned" if (d1 and h4 and d1.structure.direction == h4.structure.direction) else "conflicting"

        # Sweep description from detected sweeps
        if market_state.detected_sweeps:
            first_sweep = market_state.detected_sweeps[0]
            sweep_desc = f"{first_sweep.pool.type} {first_sweep.sweep_type}"
        else:
            sweep_desc = "no sweep"

        # Displacement from M15 structure events
        m15 = market_state.timeframes.get("M15")
        if m15 and m15.structure_events:
            disp_events = [e for e in m15.structure_events if e.displacement_present]
            if disp_events:
                ratio = disp_events[-1].displacement_ratio
                if ratio >= 2.0:
                    disp_desc = "strong displacement"
                elif ratio >= 1.5:
                    disp_desc = "medium displacement"
                else:
                    disp_desc = "weak displacement"
            else:
                disp_desc = "no displacement"
        else:
            disp_desc = "no displacement"

        from datetime import datetime, timezone
        day_name = datetime.now(timezone.utc).strftime("%A")

        return (
            f"{daily_dir} Daily {aligned} H4 | "
            f"{sweep_desc} | "
            f"{disp_desc} | "
            f"{day_name}"
        )

    def embed_trade(self, trade: TradeRecord, postmortem: PostmortemRecord) -> None:
        """Embed a completed trade into LanceDB."""
        text = self.format_trade_summary(trade)
        vector = self._embed_model.encode(text).tolist()

        row = {
            "trade_id": trade.trade_id,
            "vector": vector,
            "text_summary": text,
            "outcome": trade.outcome or "",
            "r_multiple": trade.r_multiple or 0.0,
            "setup_grade": trade.setup_grade,
            "direction": trade.direction,
            "day_of_week": trade.day_of_week,
            "liquidity_type": trade.liquidity_swept or "",
            "displacement_quality": trade.displacement_quality or "",
            "regime": trade.regime or "",
            "date": trade.date,
            "daily_bias": trade.daily_bias or "",
            "h4_aligned": trade.h4_aligned if trade.h4_aligned is not None else False,
            "debate_confidence": trade.debate_confidence or 0,
            "postmortem_summary": postmortem.summary or "",
        }
        self._lance_table.add([row])

    def _retrieval_config(self, config: Optional[dict] = None) -> dict[str, Any]:
        """Return runtime retrieval config, tolerating absent or partial config."""
        source = config if config is not None else self.config
        if not isinstance(source, dict):
            return {}
        retrieval = source.get("retrieval", {})
        return retrieval if isinstance(retrieval, dict) else {}

    def find_similar_setups(
        self,
        market_state: MarketStateObject,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
        config: Optional[dict] = None,
        low_similarity_action: Optional[str] = None,
    ) -> List[dict]:
        """Query LanceDB for similar historical setups.

        Production config excludes weak historical parallels before prompt
        assembly so Layer 3 can mechanically narrow AI context.
        """
        retrieval_cfg = self._retrieval_config(config)
        resolved_top_k = int(
            top_k if top_k is not None else retrieval_cfg.get("similar_setups_top_k", 5)
        )
        resolved_top_k = max(0, resolved_top_k)
        if resolved_top_k == 0:
            return []

        resolved_min_similarity = float(
            min_similarity
            if min_similarity is not None
            else retrieval_cfg.get("min_similarity_threshold", 0.50)
        )
        action = str(
            low_similarity_action
            or retrieval_cfg.get("low_similarity_action", "annotate")
        ).lower()
        if action not in {"annotate", "exclude"}:
            action = "annotate"
        max_candidates = int(retrieval_cfg.get("max_search_candidates", resolved_top_k * 4))
        search_limit = (
            max(resolved_top_k, max_candidates)
            if action == "exclude"
            else resolved_top_k
        )

        text = self.format_current_conditions(market_state)
        query_vector = self._embed_model.encode(text).tolist()

        try:
            results = self._lance_table.search(query_vector).limit(search_limit).to_list()
        except Exception:
            return []

        similar: List[dict] = []
        low_similarity_seen = 0
        for r in results:
            sim = round(1 - r.get("_distance", 1.0), 2)
            if sim < resolved_min_similarity and action == "exclude":
                low_similarity_seen += 1
                continue
            entry = {
                "trade_id": r["trade_id"],
                "similarity_score": sim,
                "outcome": r["outcome"],
                "r_multiple": r["r_multiple"],
                "setup_grade": r["setup_grade"],
                "text_summary": r["text_summary"],
                "postmortem_summary": r["postmortem_summary"],
            }
            if sim < resolved_min_similarity:
                entry["note"] = f"Low similarity ({sim}) — interpret with caution"
            similar.append(entry)
            if len(similar) >= resolved_top_k:
                break
        if not similar and results and action == "exclude":
            return [{
                "note": (
                    "No historical setups met Layer 3 similarity threshold; "
                    "omitting weak parallels from AI context"
                ),
                "min_similarity_threshold": resolved_min_similarity,
                "raw_candidate_count": len(results),
                "low_similarity_rows_excluded": low_similarity_seen,
            }]
        return similar

    def assemble_layer3_context(
        self,
        market_state: MarketStateObject,
        config: Optional[dict] = None,
    ) -> List[dict]:
        """Layer 3 wrapper — handles empty vectordb gracefully."""
        if not hasattr(self, "_lance_table"):
            return [{"note": "Vector store not initialized"}]
        try:
            count = self._lance_table.count_rows()
        except Exception:
            count = 0
        if count == 0:
            return [{"note": "No historical trades in vector store yet"}]
        return self.find_similar_setups(market_state, config=config)

    def assemble_full_context(
        self,
        market_state: MarketStateObject,
        config: Optional[dict] = None,
    ) -> dict:
        """Combine all three retrieval layers into a single context block."""
        return {
            "layer1": self.assemble_layer1_context(),
            "layer2": self.assemble_layer2_context(),
            "layer3": self.assemble_layer3_context(market_state, config=config),
        }
