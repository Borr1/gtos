"""Repair remaining structural/FVG source rows from local tick-derived OHLC.

This is a research-only materialization pass. It consumes committed action-queue
rows plus local tick parquet files, derives decision-time H1/M15 structural
sources from bid OHLC up to the candidate decision time, and recomputes only the
remaining swing-protected and standalone-FVG scorer rows. It does not append to
shadow logs and does not change live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq
import yaml


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.market_state import _build_timeframe_state
from src.research_infra.live_mechanical_shadow import (
    build_strategy_outcome_rows,
    latest_ltf_for_candidate_asof,
    latest_path_rows_by_candidate,
    latest_structural_metadata_by_candidate,
    merge_structural_metadata_candidate,
    read_jsonl,
)


DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_ACTION_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_LEDGER_2026-05-17.jsonl"
INPUT_STRATEGY_FOLLOW = Path("shadow_logs/strategy_follow_candidates.jsonl")
INPUT_PATH_FOLLOW = Path("shadow_logs/candidate_path_follow.jsonl")
INPUT_LTF_PATH_ORDER = Path("shadow_logs/candidate_ltf_path_order.jsonl")
INPUT_STRUCTURAL_METADATA = Path("shadow_logs/live_structural_strategy_metadata.jsonl")
INPUT_CONFIG = Path("config/agent_config.yaml")
INPUT_TICKS_ROOT = Path("data/ticks")

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

TARGET_SOURCE_DECISIONS = {
    "SOURCE_CAPTURE_REQUIRED_FOR_SWING_PROTECTED_STOP_SCORER",
    "SOURCE_CAPTURE_REQUIRED_FOR_STANDALONE_FVG_SCORER",
}
SWING_STRATEGY = "V2_STRUCT_SWING_PROTECTED"
FVG_STRATEGIES = {"V2_STRUCT_FVG_MID_EDGE", "V3_FVG_ONLY_RESCUE_RISK_BANK"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_utc(value: Any) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = parse_utc(row.get("created_at_utc"))
        previous = parse_utc(latest.get(cid, {}).get("created_at_utc"))
        if current >= previous:
            latest[cid] = row
    return latest


def latest_path_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("candidate_id") or ""): row
        for row in latest_path_rows_by_candidate(rows)
        if row.get("candidate_id")
    }


def model_dump(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    try:
        return value.model_dump(mode="json")
    except Exception:
        pass
    if isinstance(value, dict):
        return {str(key): model_dump(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [model_dump(item) for item in value]
    return str(value)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


class TickOhlcSource:
    def __init__(self, ticks_root: Path) -> None:
        self.ticks_root = ticks_root
        self._cache: dict[str, pd.DataFrame] = {}
        self.consumed_files: set[Path] = set()
        self.load_status: dict[str, str] = {}

    def _load_symbol(self, symbol: str) -> pd.DataFrame:
        if symbol in self._cache:
            return self._cache[symbol]
        symbol_dir = self.ticks_root / symbol
        frames: list[pd.DataFrame] = []
        if not symbol_dir.exists():
            self.load_status[symbol] = "TICK_SYMBOL_DIR_MISSING"
            out = pd.DataFrame(columns=["ts_utc", "bid"])
            self._cache[symbol] = out
            return out
        for path in sorted(symbol_dir.glob("*.parquet")):
            try:
                table = pq.read_table(path, columns=["ts_utc", "bid"])
                frames.append(table.to_pandas())
                self.consumed_files.add(path)
            except Exception:
                continue
        if not frames:
            self.load_status[symbol] = "NO_READABLE_TICK_PARQUETS"
            out = pd.DataFrame(columns=["ts_utc", "bid"])
            self._cache[symbol] = out
            return out
        out = pd.concat(frames, ignore_index=True)
        out = out[out["bid"].notna()].sort_values("ts_utc")
        self.load_status[symbol] = "TICK_PARQUETS_LOADED"
        self._cache[symbol] = out
        return out

    def ohlc(
        self,
        *,
        symbol: str,
        decision_time: datetime,
        timeframe: str,
        lookback_bars: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        minutes = {"H1": 60, "M15": 15}[timeframe]
        start = decision_time - timedelta(minutes=lookback_bars * minutes + 3 * 24 * 60)
        df = self._load_symbol(symbol)
        if df.empty:
            return [], {"source_status": self.load_status.get(symbol, "NO_TICK_ROWS")}
        window = df[(df["ts_utc"] >= start) & (df["ts_utc"] < decision_time)]
        if window.empty:
            return [], {"source_status": "NO_TICK_ROWS_IN_DECISION_WINDOW"}
        series = window.set_index("ts_utc")["bid"]
        rule = {"H1": "1h", "M15": "15min"}[timeframe]
        ohlc = series.resample(rule, label="left", closed="left").ohlc().dropna()
        counts = series.resample(rule, label="left", closed="left").count().reindex(ohlc.index).fillna(0)
        ohlc = ohlc[ohlc.index + pd.Timedelta(minutes=minutes) <= decision_time]
        counts = counts.reindex(ohlc.index).fillna(0)
        if len(ohlc) > lookback_bars:
            ohlc = ohlc.iloc[-lookback_bars:]
            counts = counts.iloc[-lookback_bars:]
        candles = [
            {
                "time": ts.isoformat(),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(counts.loc[ts]),
            }
            for ts, row in ohlc.iterrows()
        ]
        return candles, {
            "source_status": "TICK_DERIVED_BID_OHLC_CAPTURED" if candles else "NO_CLOSED_TICK_OHLC_BARS",
            "timeframe": timeframe,
            "bars": len(candles),
            "lookback_bars_requested": lookback_bars,
            "lookback_complete": len(candles) >= lookback_bars,
            "first_bar_utc": candles[0]["time"] if candles else None,
            "last_bar_utc": candles[-1]["time"] if candles else None,
            "price_source": "bid",
            "no_leak_status": "TICKS_FILTERED_STRICTLY_BEFORE_DECISION_TIME",
        }


class StructuralDeriver:
    def __init__(self, config: dict[str, Any], tick_source: TickOhlcSource) -> None:
        self.config = config
        self.tick_source = tick_source
        self.base_data = config.get("data") or {}

    def _instrument(self, symbol: str) -> dict[str, Any]:
        return (self.config.get("instruments") or {}).get(symbol) or {}

    def _lookback(self, symbol: str, timeframe: str) -> int:
        instrument = self._instrument(symbol)
        return int(
            (((instrument.get("data") or {}).get("lookback") or {}).get(timeframe))
            or ((self.base_data.get("lookback") or {}).get(timeframe))
            or {"H1": 168, "M15": 672}[timeframe]
        )

    def _min_bars(self, symbol: str, timeframe: str) -> int:
        instrument = self._instrument(symbol)
        return int(
            (((instrument.get("data") or {}).get("swing_detection_min_bars") or {}).get(timeframe))
            or ((self.base_data.get("swing_detection_min_bars") or {}).get(timeframe))
            or 2
        )

    def _fvg_min_gap(self, symbol: str, timeframe: str) -> float:
        instrument = self._instrument(symbol)
        return float(
            (((instrument.get("data") or {}).get("fvg_min_gap") or {}).get(timeframe))
            or ((self.base_data.get("fvg_min_gap") or {}).get(timeframe))
            or 0.0
        )

    def derive(self, candidate: dict[str, Any]) -> dict[str, Any]:
        symbol = str(candidate.get("symbol") or "")
        decision_time = parse_utc(candidate.get("decision_time_utc"))
        h1_setup = candidate.get("h1_setup") if isinstance(candidate.get("h1_setup"), dict) else {}
        trade_parameters = (
            candidate.get("trade_parameters") if isinstance(candidate.get("trade_parameters"), dict) else {}
        )

        states: dict[str, Any] = {}
        provenance: dict[str, Any] = {}
        for timeframe in ("H1", "M15"):
            candles, source = self.tick_source.ohlc(
                symbol=symbol,
                decision_time=decision_time,
                timeframe=timeframe,
                lookback_bars=self._lookback(symbol, timeframe),
            )
            provenance[timeframe] = source
            if len(candles) < 20:
                states[timeframe] = None
                source["analysis_status"] = "INSUFFICIENT_TICK_DERIVED_BARS_FOR_STRUCTURE"
                continue
            states[timeframe] = _build_timeframe_state(
                candles,
                min_bars=self._min_bars(symbol, timeframe),
                fvg_min_gap=self._fvg_min_gap(symbol, timeframe),
                tf_name=timeframe,
            )
            source["analysis_status"] = "MARKET_STATE_REPLAYED_FROM_TICK_DERIVED_OHLC"

        def fvgs(timeframe: str) -> list[dict[str, Any]]:
            state = states.get(timeframe)
            return [model_dump(item) for item in (getattr(state, "fair_value_gaps", []) if state else [])]

        def protected_swing(timeframe: str) -> dict[str, Any] | None:
            state = states.get(timeframe)
            swing = getattr(getattr(state, "structure", None), "protected_swing", None) if state else None
            return model_dump(swing) if swing is not None else None

        h1_fvgs = fvgs("H1")
        m15_fvgs = fvgs("M15")
        h1_swing = protected_swing("H1")
        m15_swing = protected_swing("M15")

        return {
            "standalone_fvg_entry_geometry": {
                "source_status": (
                    "TICK_DERIVED_DECISION_TIME_SOURCE_CAPTURED"
                    if h1_fvgs or m15_fvgs
                    else "TICK_DERIVED_NO_FVG_GEOMETRY_PRESENT"
                ),
                "candidate_h1_poi_type": h1_setup.get("poi_type"),
                "candidate_h1_poi_price_level": h1_setup.get("poi_price_level"),
                "candidate_entry_price": trade_parameters.get("entry_price"),
                "h1_fair_value_gaps": h1_fvgs,
                "m15_fair_value_gaps": m15_fvgs,
                "tick_ohlc_source_provenance": provenance,
            },
            "swing_protected_lock_level": {
                "source_status": (
                    "TICK_DERIVED_DECISION_TIME_SOURCE_CAPTURED"
                    if h1_swing or m15_swing
                    else "TICK_DERIVED_NO_PROTECTED_SWING_PRESENT"
                ),
                "h1_protected_swing": h1_swing,
                "m15_protected_swing": m15_swing,
                "tick_ohlc_source_provenance": provenance,
            },
            "tick_structural_source_derivation_provenance": provenance,
        }


def merge_tick_derived_fields(candidate: dict[str, Any], derived: dict[str, Any]) -> dict[str, Any]:
    out = dict(candidate)
    structural = out.get("decision_time_structural_fields")
    structural = dict(structural) if isinstance(structural, dict) else {}
    fields = dict(structural.get("fields") or {})
    for field in ("standalone_fvg_entry_geometry", "swing_protected_lock_level"):
        payload = derived.get(field)
        current = fields.get(field)
        current_status = current.get("source_status") if isinstance(current, dict) else None
        if current in (None, "", [], {}) or current_status in {None, "", "SOURCE_NOT_CAPTURED"}:
            fields[field] = payload
    statuses = dict(structural.get("field_statuses") or {})
    for field, payload in fields.items():
        if isinstance(payload, dict):
            statuses[field] = payload.get("source_status") or statuses.get(field)
    structural.update(
        {
            "capture_status": "TICK_DERIVED_STRUCTURAL_SOURCE_REPAIR_APPLIED",
            "source": "tick_parquet_bid_ohlc_replay",
            "fields": fields,
            "field_statuses": statuses,
            "tick_structural_source_derivation_provenance": derived.get(
                "tick_structural_source_derivation_provenance"
            ),
            "no_leak_status": "TICKS_FILTERED_STRICTLY_BEFORE_DECISION_TIME",
        }
    )
    out["decision_time_structural_fields"] = structural
    return out


def implementation_decision(row: dict[str, Any]) -> tuple[str, str, str]:
    strategy_id = str(row.get("strategy_id") or "")
    status = str(row.get("strategy_status") or "")
    proxy = safe_float(row.get("strategy_proxy_r"))
    if status.startswith("SCORED_SWING_PROTECTED"):
        if proxy is None:
            return (
                "IMPLEMENT_DEFAULT_OFF",
                "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_SCORER_WITH_AMBIGUITY_EXCLUSION",
                "TICK_DERIVED_SOURCE_REPAIR_AMBIGUITY_EXCLUDED",
            )
        return (
            "IMPLEMENT_DEFAULT_OFF",
            "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_PATH_SCORER_NOW",
            "TICK_DERIVED_SOURCE_REPAIR_COMPUTED_PROXY",
        )
    if status.startswith("SCORED_STANDALONE_FVG"):
        if proxy is None:
            return (
                "IMPLEMENT_DEFAULT_OFF",
                "IMPLEMENT_DEFAULT_OFF_STANDALONE_FVG_POI_SCORER_WITH_AMBIGUITY_EXCLUSION",
                "TICK_DERIVED_SOURCE_REPAIR_AMBIGUITY_EXCLUDED",
            )
        return (
            "IMPLEMENT_DEFAULT_OFF",
            "IMPLEMENT_DEFAULT_OFF_STANDALONE_FVG_POI_PATH_SCORER_NOW",
            "TICK_DERIVED_SOURCE_REPAIR_COMPUTED_PROXY",
        )
    if status.startswith("KILLED_"):
        return "KILL", str(row.get("branch_decision") or "KILL_ROW_AFTER_TICK_DERIVED_SOURCE_REPAIR"), "TICK_DERIVED_SOURCE_REPAIR_KILLED"
    if status.startswith("REDESIGN_"):
        return "REDESIGN", str(row.get("branch_decision") or "REDESIGN_REQUIRED_AFTER_TICK_DERIVED_SOURCE_REPAIR"), "TICK_DERIVED_SOURCE_REPAIR_REDESIGN_REQUIRED"
    return "SOURCE_REPAIR", str(row.get("branch_decision") or "SOURCE_CAPTURE_STILL_REQUIRED_AFTER_TICK_DERIVED_REPLAY"), "TICK_DERIVED_SOURCE_REPAIR_NOT_COMPUTABLE"


def proxy_delta(before: Any, after: Any) -> float | None:
    before_value = safe_float(before)
    after_value = safe_float(after)
    if after_value is None:
        return None
    if before_value is None:
        return round(after_value, 8)
    return round(after_value - before_value, 8)


def scorer_row_for(
    *,
    source_row: dict[str, Any],
    candidates: dict[str, dict[str, Any]],
    paths: dict[str, dict[str, Any]],
    ltf_rows: list[dict[str, Any]],
    structural_metadata: dict[str, dict[str, Any]],
    deriver: StructuralDeriver,
    generated: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    cid = str(source_row.get("candidate_id") or "")
    strategy_id = str(source_row.get("strategy_id") or "")
    candidate = candidates.get(cid)
    path_row = paths.get(cid)
    if not candidate or not path_row:
        return None, None
    enriched = merge_structural_metadata_candidate(candidate, structural_metadata.get(cid))
    derived = deriver.derive(enriched)
    enriched = merge_tick_derived_fields(enriched, derived)
    ltf_row = latest_ltf_for_candidate_asof(enriched, path_row, ltf_rows)
    for row in build_strategy_outcome_rows(enriched, path_row, ltf_row=ltf_row, created_at_utc=generated):
        if row.get("strategy_id") == strategy_id:
            return row, derived
    return None, derived


def proxy_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [safe_float(row.get("after_proxy_r")) for row in rows]
    numeric = [value for value in values if value is not None]
    total = round(sum(numeric), 8)
    return {
        "numeric_proxy_rows": len(numeric),
        "proxy_r_sum": total,
        "proxy_r_mean": round(total / len(numeric), 8) if numeric else None,
    }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_ACTION_LEDGER)
    target_ids = {
        str(row.get("candidate_id") or "")
        for row in source_rows
        if row.get("implementation_decision") in TARGET_SOURCE_DECISIONS
    }
    candidates = {
        cid: row
        for cid, row in latest_by_candidate(read_jsonl(INPUT_STRATEGY_FOLLOW)).items()
        if cid in target_ids
    }
    paths = {
        cid: row
        for cid, row in latest_path_by_candidate(read_jsonl(INPUT_PATH_FOLLOW)).items()
        if cid in target_ids
    }
    ltf_rows = [row for row in read_jsonl(INPUT_LTF_PATH_ORDER) if str(row.get("candidate_id") or "") in target_ids]
    structural_metadata = latest_structural_metadata_by_candidate(
        [row for row in read_jsonl(INPUT_STRUCTURAL_METADATA) if str(row.get("candidate_id") or "") in target_ids]
    )
    config = yaml.safe_load(INPUT_CONFIG.read_text(encoding="utf-8"))
    tick_source = TickOhlcSource(INPUT_TICKS_ROOT)
    deriver = StructuralDeriver(config, tick_source)

    out: list[dict[str, Any]] = []
    target_rows_before = 0
    target_repaired = 0
    missing_required_inputs: Counter[str] = Counter()
    by_strategy: Counter[str] = Counter()
    by_symbol: Counter[str] = Counter()
    target_statuses: Counter[str] = Counter()
    target_decisions: Counter[str] = Counter()
    target_actions: Counter[str] = Counter()
    tick_statuses: Counter[str] = Counter()

    for idx, row in enumerate(source_rows, start=1):
        if row.get("implementation_decision") not in TARGET_SOURCE_DECISIONS:
            unchanged = dict(row)
            unchanged["tick_structural_derivation_repair_status"] = "NOT_TARGET_ROW"
            out.append(unchanged)
            continue

        target_rows_before += 1
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        by_strategy[strategy_id] += 1
        by_symbol[str(row.get("symbol") or "")] += 1
        scorer, derived = scorer_row_for(
            source_row=row,
            candidates=candidates,
            paths=paths,
            ltf_rows=ltf_rows,
            structural_metadata=structural_metadata,
            deriver=deriver,
            generated=generated,
        )
        new = dict(row)
        new["source_line_no"] = row.get("source_line_no") or idx
        new["before_action_class"] = row.get("action_class")
        new["before_implementation_decision"] = row.get("implementation_decision")
        new["before_branch_decision"] = row.get("branch_decision")
        new["before_proxy_r"] = row.get("after_proxy_r") if "after_proxy_r" in row else row.get("before_proxy_r")
        new["generated_utc"] = generated
        new["safe_flags"] = SAFE_FLAGS
        new["no_promotion"] = True
        new["no_live_behavior"] = True
        new["no_shadow_log_append"] = True
        new["exact_r"] = None
        if derived:
            provenance = derived.get("tick_structural_source_derivation_provenance") or {}
            new["tick_structural_source_derivation_provenance"] = provenance
            for tf_status in provenance.values():
                if isinstance(tf_status, dict):
                    tick_statuses[str(tf_status.get("source_status") or "UNKNOWN")] += 1
        if scorer is None:
            missing_required_inputs["missing_candidate_or_path_or_scorer"] += 1
            new.update(
                {
                    "action_class": "SOURCE_REPAIR",
                    "implementation_decision": "SOURCE_CAPTURE_REQUIRED_AFTER_TICK_STRUCTURAL_DERIVATION_INPUT_MISSING",
                    "coverage_status": "PRESERVED_WITH_EXACT_SOURCE_REQUIREMENT",
                    "current_action": "REPAIR_MISSING_CANDIDATE_PATH_OR_SCORER_INPUT",
                    "next_action": "REPAIR_MISSING_CANDIDATE_PATH_OR_SCORER_INPUT",
                    "tick_structural_derivation_repair_status": "INPUT_MISSING",
                    "proxy_r_delta": None,
                }
            )
            out.append(new)
            continue

        action, decision, repair_status = implementation_decision(scorer)
        target_repaired += 1 if action != "SOURCE_REPAIR" else 0
        target_statuses[str(scorer.get("strategy_status") or "")] += 1
        target_decisions[decision] += 1
        target_actions[action] += 1
        proxy = safe_float(scorer.get("strategy_proxy_r"))
        new.update(
            {
                "action_class": action,
                "implementation_decision": decision,
                "coverage_status": repair_status,
                "current_action": decision,
                "next_action": decision,
                "tick_structural_derivation_repair_status": repair_status,
                "after_strategy_status": scorer.get("strategy_status"),
                "after_score_status": scorer.get("score_status"),
                "after_outcome_status": scorer.get("outcome_status"),
                "after_proxy_r": proxy,
                "proxy_r_delta": proxy_delta(row.get("before_proxy_r"), proxy),
                "outcome_source": scorer.get("outcome_source"),
                "scoring_boundary": scorer.get("scoring_boundary"),
                "branch_decision": scorer.get("branch_decision"),
                "decision_evidence": scorer.get("decision_evidence"),
                "implementation_candidate": scorer.get("implementation_candidate"),
                "primitive_family": "tick_derived_structural_source_repair",
                "source_artifact": "data/ticks/{SYMBOL}/{YYYY-MM-DD}.parquet",
            }
        )
        for field in (
            "standalone_fvg_source_status",
            "standalone_fvg_selected_poi_type_source_status",
            "standalone_fvg_poi_status",
            "standalone_fvg_poi_type",
            "standalone_fvg_entry_price",
            "standalone_fvg_poi_price_level",
            "standalone_fvg_entry_inside_gap",
            "standalone_fvg_poi_price_inside_gap",
            "standalone_fvg_matching_gap_timeframes",
            "standalone_fvg_poi_matching_gap_timeframes",
            "swing_protected_source_status",
            "swing_protected_stop_status",
            "swing_protected_stop_side",
            "swing_protected_stop_loss",
            "swing_protected_match_timeframe",
            "swing_protected_match_price",
            "swing_protected_match_type",
            "swing_protected_match_time_utc",
            "swing_protected_stop_distance_price",
            "swing_protected_compatible_swing_count",
            "swing_protected_type_mismatches",
        ):
            if field in scorer:
                new[field] = scorer.get(field)
        out.append(new)

    consumed_tick_files = [
        {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(tick_source.consumed_files)
    ]
    summary = {
        "route_id": ROUTE_ID,
        "evidence_class": "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR",
        "generated_utc": generated,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": (
            "This plate derives decision-time structural/FVG source fields from local bid-tick parquet "
            "OHLC up to each candidate decision time. It is a proxy/source-repair materialization, not "
            "broker actual-R, not a production selector, and not a promotion dossier."
        ),
        "rows": len(out),
        "target_rows_before": target_rows_before,
        "target_rows_converted_out_of_source_repair": target_repaired,
        "target_rows_remaining_source_repair": target_rows_before - target_repaired,
        "before_proxy": proxy_stats(source_rows),
        "after_proxy": proxy_stats(out),
        "proxy_delta": {
            "numeric_proxy_rows_delta": proxy_stats(out)["numeric_proxy_rows"] - proxy_stats(source_rows)["numeric_proxy_rows"],
            "proxy_r_sum_delta": round(proxy_stats(out)["proxy_r_sum"] - proxy_stats(source_rows)["proxy_r_sum"], 8),
        },
        "exact_r_rows": 0,
        "target_statuses": dict(sorted(target_statuses.items())),
        "target_implementation_decisions": dict(sorted(target_decisions.items())),
        "target_action_classes": dict(sorted(target_actions.items())),
        "target_rows_by_strategy": dict(sorted(by_strategy.items())),
        "target_rows_by_symbol": dict(sorted(by_symbol.items())),
        "tick_source_statuses": dict(sorted(tick_statuses.items())),
        "missing_required_inputs": dict(sorted(missing_required_inputs.items())),
        "consumed_tick_file_count": len(consumed_tick_files),
        "consumed_tick_files": consumed_tick_files,
        "input_rows": len(source_rows),
        "output_rows": len(out),
        "action_counts_before": dict(sorted(Counter(row.get("action_class") for row in source_rows).items())),
        "action_counts_after": dict(sorted(Counter(row.get("action_class") for row in out).items())),
        "source_repair_decisions_after": {
            str(decision): count
            for decision, count in sorted(Counter(row.get("implementation_decision") for row in out).items())
            if str(decision).startswith("SOURCE_CAPTURE_REQUIRED")
            or str(decision).startswith("SOURCE_REPAIR_REQUIRED")
        },
        "plate_decision": "TICK_STRUCTURAL_DERIVATION_REPAIRS_REMAINING_SWING_AND_FVG_SOURCE_ROWS",
        "implementation_decision": (
            "KEEP_DEFAULT_OFF_TICK_DERIVED_SWING_PROTECTED_AND_STANDALONE_FVG_PROXY_SCORERS; "
            "KILL_NON_PROTECTED_SWING_ROWS; KEEP_EXACT_BROKER_R_AND_PROMOTION_BLOCKED"
        ),
    }
    return out, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    paths = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    return {
        "route_id": ROUTE_ID,
        "evidence_class": "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR",
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in paths
        ],
        "inputs": [
            {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in [
                INPUT_ACTION_LEDGER,
                INPUT_STRATEGY_FOLLOW,
                INPUT_PATH_FOLLOW,
                INPUT_LTF_PATH_ORDER,
                INPUT_STRUCTURAL_METADATA,
                INPUT_CONFIG,
            ]
            if path.exists()
        ],
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": summary["claim_boundary"],
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    manifest = build_manifest(summary)
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
