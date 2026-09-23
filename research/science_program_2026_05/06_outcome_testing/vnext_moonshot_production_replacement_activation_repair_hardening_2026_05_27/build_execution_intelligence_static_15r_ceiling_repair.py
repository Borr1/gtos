from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE = "2026-05-27"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
STAGE04_SUMMARY = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json"
SELECTED_MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_SELECTED_TRADE_SHARD_MANIFEST_{DATE}.jsonl"
OUT_DIR = ROUTE_DIR / "ei15r"
SUMMARY = OUT_DIR / "summary.json"
DENOM_STEM = OUT_DIR / "denominator_reconciliation"
WINNERS_STEM = OUT_DIR / "winner_leftover_move"
LOSERS_STEM = OUT_DIR / "loser_mitigation"
BES_STEM = OUT_DIR / "be_classification"
DYNAMIC_STEM = OUT_DIR / "dynamic_exit_counterfactual"
RUNTIME_STEM = OUT_DIR / "runtime_surface_gap"
UPGRADE_STEM = OUT_DIR / "replay_scoring_upgrade"
DENOM_MANIFEST = OUT_DIR / "denominator_reconciliation.manifest.jsonl"
WINNERS_MANIFEST = OUT_DIR / "winner_leftover_move.manifest.jsonl"
LOSERS_MANIFEST = OUT_DIR / "loser_mitigation.manifest.jsonl"
BES_MANIFEST = OUT_DIR / "be_classification.manifest.jsonl"
DYNAMIC_MANIFEST = OUT_DIR / "dynamic_exit_counterfactual.manifest.jsonl"
RUNTIME_MANIFEST = OUT_DIR / "runtime_surface_gap.manifest.jsonl"
UPGRADE_MANIFEST = OUT_DIR / "replay_scoring_upgrade.manifest.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"
DEFAULT_SHARD_ROWS = 100_000

POLICIES = (
    "fixed_1_5r",
    "be_after_trigger",
    "trailing_runner",
    "partial_be_runner",
    "hold_to_structure",
    "early_cut_if_no_progress",
    "volatility_session_expansion",
    "momentum_exhaustion",
    "liquidity_sweep_exit",
    "m1_tick_path_exit",
    "time_stop",
    "condition_router",
)
HISTORICAL_COST_MISSING_FIELDS = (
    "spread_r_at_order_send",
    "slippage_r_at_fill",
    "commission",
    "swap",
    "account_history_deal_reconciliation",
    "order_modify_retcode",
    "close_order_retcode",
)
LOCAL_M1_MANIFESTS = (
    "data/mt5_research_exports/phase3_rescue_all_m1_m5_chunk1_after_maxbars/manifest.json",
    "data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1/manifest.json",
    "data/mt5_research_exports/vnext_full_stage04_expanded_m1_m5_readonly_2026_05_24/manifest.json",
    "data/mt5_research_exports/phase3_v2b_forward_20260401_20260502_readonly/manifest.json",
    "data/mt5_research_exports/phase3_v2b_forward_20260501_readonly/manifest.json",
)
LOCAL_TICK_ROOT = Path("data/ticks")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


class PlainJsonlShardWriter:
    """Write every logical row to uncompressed JSONL shards plus a manifest."""

    def __init__(
        self,
        *,
        ledger_name: str,
        stem: Path,
        manifest_path: Path,
        max_rows_per_shard: int = DEFAULT_SHARD_ROWS,
    ) -> None:
        self.ledger_name = ledger_name
        self.stem = stem
        self.manifest_path = manifest_path
        self.max_rows_per_shard = max_rows_per_shard
        self._handle = None
        self._shard_index = 0
        self._rows_in_shard = 0
        self._current_path: Path | None = None
        self.total_rows = 0
        self.entries: list[dict[str, Any]] = []

    def reset(self) -> None:
        if self.manifest_path.exists():
            self.manifest_path.unlink()
        for path in sorted(self.manifest_path.parent.glob(f"{self.stem.name}.part-*.jsonl")):
            path.unlink()

    def _open_next(self) -> None:
        self._current_path = self.manifest_path.parent / (
            f"{self.stem.name}.part-{self._shard_index:06d}.jsonl"
        )
        self._handle = self._current_path.open("w", encoding="utf-8", newline="\n")
        self._rows_in_shard = 0
        self._shard_index += 1

    def _close_current(self) -> None:
        if self._handle is None or self._current_path is None:
            return
        self._handle.close()
        self._handle = None
        entry = {
            "ledger_name": self.ledger_name,
            "shard_index": len(self.entries),
            "path": rel(self._current_path),
            "row_count": self._rows_in_shard,
            "size_bytes": self._current_path.stat().st_size,
            "sha256": sha256_file(self._current_path),
            "format": "plain_jsonl",
            "compressed": False,
        }
        self.entries.append(entry)
        self._current_path = None

    def write(self, payload: dict[str, Any]) -> None:
        if self._handle is None:
            self._open_next()
        if self._rows_in_shard >= self.max_rows_per_shard:
            self._close_current()
            self._open_next()
        assert self._handle is not None
        self._handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
        self._rows_in_shard += 1
        self.total_rows += 1

    def close(self) -> None:
        self._close_current()
        with self.manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
            for entry in self.entries:
                handle.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")

    def meta(self) -> dict[str, Any]:
        return {
            "manifest_path": rel(self.manifest_path),
            "manifest_sha256": sha256_file(self.manifest_path),
            "manifest_size_bytes": self.manifest_path.stat().st_size,
            "row_count": self.total_rows,
            "shard_count": len(self.entries),
            "shards_size_bytes": sum(int(entry["size_bytes"]) for entry in self.entries),
            "plain_jsonl_shards": True,
            "compressed": False,
            "max_rows_per_shard": self.max_rows_per_shard,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonl_rows(path: Path) -> Iterable[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def selected_rows() -> Iterable[dict[str, Any]]:
    for manifest_row in jsonl_rows(SELECTED_MANIFEST):
        shard = REPO_ROOT / manifest_row["path"]
        for row in jsonl_rows(shard):
            yield row


def selected_row_id(row: dict[str, Any]) -> str:
    return str(
        row.get("order_intent_id")
        or row.get("dedupe_key")
        or row.get("candidate_id")
        or hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    )


def norm_time(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).replace("T", " ").replace("Z", "")
    if "+" in text:
        text = text.split("+", 1)[0]
    if "." in text:
        text = text.split(".", 1)[0]
    return text.strip()


def norm_date(value: Any) -> str | None:
    text = norm_time(value)
    if not text or len(text) < 10:
        return None
    return text[:10]


def float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        parsed = float(value)
        if math.isnan(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def int_or_none(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


class CsvCache:
    def __init__(self) -> None:
        self.rows: dict[str, list[dict[str, Any]]] = {}
        self.time_index: dict[str, dict[str, int]] = {}
        self.sha: dict[str, str] = {}

    def load(self, source_path: str | None) -> list[dict[str, Any]]:
        if not source_path:
            return []
        if source_path in self.rows:
            return self.rows[source_path]
        path = REPO_ROOT / source_path
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                rows.append(
                    {
                        "time": norm_time(raw.get("time")),
                        "open": float(raw["open"]),
                        "high": float(raw["high"]),
                        "low": float(raw["low"]),
                        "close": float(raw["close"]),
                    }
                )
        self.rows[source_path] = rows
        self.time_index[source_path] = {str(row["time"]): idx for idx, row in enumerate(rows)}
        self.sha[source_path] = sha256_file(path)
        return rows

    def index_for_time(self, source_path: str | None, time_value: Any) -> int | None:
        if not source_path:
            return None
        self.load(source_path)
        key = norm_time(time_value)
        if not key:
            return None
        return self.time_index.get(source_path, {}).get(key)


class M1AvailabilityIndex:
    def __init__(self) -> None:
        self.sources_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.time_sets: dict[str, set[str]] = {}
        self.sha: dict[str, str] = {}
        self.searched_manifests: list[str] = []
        for manifest_rel in LOCAL_M1_MANIFESTS:
            manifest_path = REPO_ROOT / manifest_rel
            if not manifest_path.exists():
                continue
            self.searched_manifests.append(manifest_rel)
            manifest = read_json(manifest_path)
            for key, meta in (manifest.get("files") or {}).items():
                if str(meta.get("timeframe") or "").upper() != "M1":
                    continue
                source_path = str(meta.get("path") or "").replace("\\", "/")
                if not source_path:
                    continue
                symbol = str(meta.get("file_symbol") or meta.get("mt5_symbol") or key.rsplit("_", 1)[0])
                record = {
                    "symbol": symbol,
                    "path": source_path,
                    "manifest_path": manifest_rel,
                    "first": norm_time(meta.get("first")),
                    "last": norm_time(meta.get("last")),
                    "rows": meta.get("rows"),
                    "gap_count": meta.get("gap_count"),
                    "max_gap_seconds": meta.get("max_gap_seconds"),
                }
                self.sources_by_symbol[symbol].append(record)
        for records in self.sources_by_symbol.values():
            records.sort(key=lambda item: (str(item.get("first") or ""), str(item.get("last") or "")))

    def _load_times(self, source_path: str) -> set[str]:
        if source_path in self.time_sets:
            return self.time_sets[source_path]
        path = REPO_ROOT / source_path
        times: set[str] = set()
        if path.exists():
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for raw in reader:
                    time_key = norm_time(raw.get("time"))
                    if time_key:
                        times.add(time_key)
            self.sha[source_path] = sha256_file(path)
        self.time_sets[source_path] = times
        return times

    def lookup(self, symbol: Any, time_value: Any) -> dict[str, Any]:
        time_key = norm_time(time_value)
        symbol_key = str(symbol or "")
        base = {
            "m1_lookup_time_utc": time_key,
            "m1_source_search_manifests": self.searched_manifests,
            "m1_source_path": None,
            "m1_source_sha256": None,
            "m1_source_manifest_path": None,
            "m1_source_first_utc": None,
            "m1_source_last_utc": None,
            "m1_source_rows": None,
            "m1_source_gap_count": None,
            "m1_exact_entry_minute_present": False,
        }
        if not time_key:
            return {**base, "m1_availability_status": "not_searched_no_entry_or_source_time"}
        records = self.sources_by_symbol.get(symbol_key) or []
        if not records:
            return {**base, "m1_availability_status": "local_m1_source_not_found_for_symbol_after_manifest_search"}
        in_range: list[dict[str, Any]] = []
        for record in records:
            first = record.get("first")
            last = record.get("last")
            if (not first or time_key >= first) and (not last or time_key <= last):
                in_range.append(record)
        if not in_range:
            first_last = [
                f"{record.get('path')}[{record.get('first')}..{record.get('last')}]"
                for record in records
            ]
            return {
                **base,
                "m1_availability_status": "local_m1_source_present_but_entry_time_outside_coverage",
                "m1_source_coverage_candidates": first_last,
            }
        for record in in_range:
            source_path = str(record["path"])
            if time_key in self._load_times(source_path):
                return {
                    **base,
                    "m1_availability_status": "local_m1_bar_available_for_entry_minute",
                    "m1_source_path": source_path,
                    "m1_source_sha256": self.sha.get(source_path),
                    "m1_source_manifest_path": record.get("manifest_path"),
                    "m1_source_first_utc": record.get("first"),
                    "m1_source_last_utc": record.get("last"),
                    "m1_source_rows": record.get("rows"),
                    "m1_source_gap_count": record.get("gap_count"),
                    "m1_exact_entry_minute_present": True,
                }
        record = in_range[0]
        return {
            **base,
            "m1_availability_status": "local_m1_source_manifest_covers_entry_time_but_exact_minute_missing",
            "m1_source_path": record.get("path"),
            "m1_source_sha256": self.sha.get(str(record.get("path") or "")),
            "m1_source_manifest_path": record.get("manifest_path"),
            "m1_source_first_utc": record.get("first"),
            "m1_source_last_utc": record.get("last"),
            "m1_source_rows": record.get("rows"),
            "m1_source_gap_count": record.get("gap_count"),
        }


class TickAvailabilityIndex:
    def __init__(self) -> None:
        self.paths_by_symbol_date: dict[tuple[str, str], str] = {}
        self.symbols: set[str] = set()
        self.sha: dict[str, str] = {}
        root = REPO_ROOT / LOCAL_TICK_ROOT
        if not root.exists():
            return
        for symbol_dir in root.iterdir():
            if not symbol_dir.is_dir():
                continue
            self.symbols.add(symbol_dir.name)
            for path in symbol_dir.glob("*.parquet"):
                self.paths_by_symbol_date[(symbol_dir.name, path.stem)] = rel(path)

    def lookup(self, symbol: Any, time_value: Any) -> dict[str, Any]:
        symbol_key = str(symbol or "")
        date_key = norm_date(time_value)
        base = {
            "tick_lookup_date_utc": date_key,
            "tick_source_path": None,
            "tick_source_sha256": None,
            "tick_source_search_root": rel(REPO_ROOT / LOCAL_TICK_ROOT),
        }
        if not date_key:
            return {**base, "tick_availability_status": "not_searched_no_entry_or_source_time"}
        if symbol_key not in self.symbols:
            return {**base, "tick_availability_status": "local_tick_source_symbol_absent_after_data_ticks_search"}
        source_path = self.paths_by_symbol_date.get((symbol_key, date_key))
        if not source_path:
            return {**base, "tick_availability_status": "local_tick_source_date_absent_after_data_ticks_search"}
        if source_path not in self.sha:
            self.sha[source_path] = sha256_file(REPO_ROOT / source_path)
        return {
            **base,
            "tick_availability_status": "local_tick_parquet_available_for_entry_date",
            "tick_source_path": source_path,
            "tick_source_sha256": self.sha[source_path],
        }


def collect_source_record_index() -> dict[str, dict[str, Any]]:
    needed: dict[str, set[str]] = defaultdict(set)
    for row in selected_rows():
        shard = row.get("source_shard_path")
        candidate_id = row.get("candidate_id")
        if shard and candidate_id:
            needed[str(shard)].add(str(candidate_id))

    index: dict[str, dict[str, Any]] = {}
    for shard, candidate_ids in sorted(needed.items()):
        path = REPO_ROOT / shard
        if not path.exists():
            continue
        remaining = set(candidate_ids)
        for source_row in jsonl_rows(path):
            cid = str(source_row.get("candidate_id") or source_row.get("row_id") or "")
            if cid in remaining:
                index[cid] = source_row
                remaining.discard(cid)
                if not remaining:
                    break
    return index


def source_path_from(row: dict[str, Any], source_record: dict[str, Any] | None) -> tuple[str | None, str | None]:
    if row.get("source_path"):
        return str(row.get("source_path")), str(row.get("source_sha256") or "")
    source_record = source_record or {}
    for container_key in ("bar_close_m15_path", "asof_source_contract"):
        container = source_record.get(container_key) or {}
        if container.get("source_path"):
            return str(container.get("source_path")), str(container.get("source_sha256") or "")
    if source_record.get("source_path"):
        return str(source_record.get("source_path")), str(source_record.get("source_sha256") or "")
    return None, None


def source_fields_from(row: dict[str, Any], source_record: dict[str, Any] | None, csv_rows: list[dict[str, Any]], idx: int | None) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    source_record = source_record or {}
    if isinstance(source_record.get("source_fields"), dict):
        fields.update(source_record.get("source_fields") or {})
    if idx is not None and 0 <= idx < len(csv_rows):
        start14 = max(0, idx - 13)
        start50 = max(0, idx - 49)
        atr14 = sum(r["high"] - r["low"] for r in csv_rows[start14 : idx + 1]) / max(1, idx + 1 - start14)
        atr50 = sum(r["high"] - r["low"] for r in csv_rows[start50 : idx + 1]) / max(1, idx + 1 - start50)
        current = csv_rows[idx]
        fields.setdefault("atr14", atr14)
        fields.setdefault("atr50", atr50)
        fields.setdefault("atr14_atr50_ratio", atr14 / atr50 if atr50 else None)
        fields.setdefault("body_atr14", abs(current["close"] - current["open"]) / atr14 if atr14 else None)
        fields.setdefault("range_atr14", (current["high"] - current["low"]) / atr14 if atr14 else None)
        if idx >= 20:
            prior = csv_rows[idx - 20 : idx]
            prior_high = max(r["high"] for r in prior)
            prior_low = min(r["low"] for r in prior)
            if current["high"] > prior_high and current["close"] < prior_high:
                fields.setdefault("sweep_direction", "swept_prior_20_high_reclaimed_below")
            elif current["low"] < prior_low and current["close"] > prior_low:
                fields.setdefault("sweep_direction", "swept_prior_20_low_reclaimed_above")
            delta = current["close"] - csv_rows[idx - 20]["close"]
            fields.setdefault("trend_state_20", "up" if delta > 0 else "down" if delta < 0 else "flat")
    return fields


def entry_touch_index(
    *,
    csv_rows: list[dict[str, Any]],
    start_idx: int | None,
    entry: float,
    max_bars: int = 200,
) -> tuple[int | None, str | None, int | None]:
    if start_idx is None or start_idx < 0 or start_idx >= len(csv_rows):
        return None, "source_row_index_out_of_range", None
    for idx in range(start_idx, min(len(csv_rows), start_idx + max_bars)):
        bar = csv_rows[idx]
        if bar["low"] <= entry <= bar["high"]:
            return idx, None, idx - start_idx
    return None, "entry_price_not_touched_in_source_window", None


def path_arrays(
    *,
    csv_rows: list[dict[str, Any]],
    start_idx: int,
    entry: float,
    stop: float,
    side: str,
    max_bars: int = 200,
) -> tuple[list[dict[str, Any]], str | None]:
    if start_idx is None or start_idx < 0 or start_idx >= len(csv_rows):
        return [], "source_row_index_out_of_range"
    sl_distance = abs(entry - stop)
    if sl_distance <= 0:
        return [], "invalid_zero_sl_distance"
    out: list[dict[str, Any]] = []
    for rel_idx, bar in enumerate(csv_rows[start_idx : min(len(csv_rows), start_idx + max_bars)]):
        if side == "LONG":
            high_r = (bar["high"] - entry) / sl_distance
            low_r = (bar["low"] - entry) / sl_distance
            close_r = (bar["close"] - entry) / sl_distance
        else:
            high_r = (entry - bar["low"]) / sl_distance
            low_r = (entry - bar["high"]) / sl_distance
            close_r = (entry - bar["close"]) / sl_distance
        out.append(
            {
                "i": rel_idx,
                "time": bar["time"],
                "max_r": high_r,
                "min_r": low_r,
                "close_r": close_r,
            }
        )
    return out, None


def result(
    policy: str,
    *,
    status: str,
    final_r: float | None,
    exit_reason: str | None,
    exit_time: str | None,
    mfe: float | None,
    mae: float | None,
    same_bar: bool = False,
    trace: dict[str, Any] | None = None,
    missing: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "policy_name": policy,
        "simulation_status": status,
        "gross_r": round(final_r, 6) if final_r is not None else None,
        "net_r": None,
        "cost_r": None,
        "cost_status": "missing_historical_live_cost_lifecycle_fields",
        "exit_reason": exit_reason,
        "exit_time_utc": exit_time,
        "mfe_r": round(mfe, 6) if mfe is not None else None,
        "mae_r": round(mae, 6) if mae is not None else None,
        "same_bar_ambiguity": same_bar,
        "transition_trace": trace or {},
        "missing_fields": missing or list(HISTORICAL_COST_MISSING_FIELDS),
    }


def simulate_target_stop(path: list[dict[str, Any]], policy: str, target_r: float, stop_r: float = -1.0) -> dict[str, Any]:
    mfe = -10**9
    mae = 10**9
    for bar in path:
        mfe = max(mfe, bar["max_r"])
        mae = min(mae, bar["min_r"])
        target_hit = bar["max_r"] >= target_r
        stop_hit = bar["min_r"] <= stop_r
        if target_hit and stop_hit:
            return result(policy, status="simulated_m15_conservative_same_bar", final_r=stop_r, exit_reason="stop_first_same_bar_conservative", exit_time=bar["time"], mfe=mfe, mae=mae, same_bar=True, trace={"target_r": target_r, "stop_r": stop_r, "bar_index": bar["i"]})
        if stop_hit:
            return result(policy, status="simulated_m15", final_r=stop_r, exit_reason="stop_loss", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"target_r": target_r, "stop_r": stop_r, "bar_index": bar["i"]})
        if target_hit:
            return result(policy, status="simulated_m15", final_r=target_r, exit_reason="final_target", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"target_r": target_r, "stop_r": stop_r, "bar_index": bar["i"]})
    last = path[-1] if path else {"close_r": None, "time": None}
    return result(policy, status="simulated_m15_path_end", final_r=last["close_r"], exit_reason="path_end_mark_to_market", exit_time=last["time"], mfe=mfe if path else None, mae=mae if path else None, trace={"target_r": target_r, "stop_r": stop_r})


def simulate_be(path: list[dict[str, Any]]) -> dict[str, Any]:
    mfe = -10**9
    mae = 10**9
    be_active = False
    trigger_time = None
    for bar in path:
        mfe = max(mfe, bar["max_r"])
        mae = min(mae, bar["min_r"])
        if not be_active:
            stop_hit = bar["min_r"] <= -1.0
            trigger_hit = bar["max_r"] >= 1.0
            target_hit = bar["max_r"] >= 1.5
            if stop_hit and (trigger_hit or target_hit):
                return result("be_after_trigger", status="simulated_m15_conservative_same_bar", final_r=-1.0, exit_reason="stop_first_same_bar_conservative", exit_time=bar["time"], mfe=mfe, mae=mae, same_bar=True, trace={"be_trigger_r": 1.0, "final_target_r": 1.5, "bar_index": bar["i"]})
            if stop_hit:
                return result("be_after_trigger", status="simulated_m15", final_r=-1.0, exit_reason="stop_loss", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"be_trigger_r": 1.0, "final_target_r": 1.5, "bar_index": bar["i"]})
            if target_hit:
                return result("be_after_trigger", status="simulated_m15", final_r=1.5, exit_reason="final_target_after_tp1_same_bar", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"be_trigger_r": 1.0, "final_target_r": 1.5, "bar_index": bar["i"]})
            if trigger_hit:
                be_active = True
                trigger_time = bar["time"]
        else:
            stop_hit = bar["min_r"] <= 0.0
            target_hit = bar["max_r"] >= 1.5
            if stop_hit and target_hit:
                return result("be_after_trigger", status="simulated_m15_conservative_same_bar", final_r=0.0, exit_reason="breakeven_stop_same_bar_target_ambiguous", exit_time=bar["time"], mfe=mfe, mae=mae, same_bar=True, trace={"be_trigger_time_utc": trigger_time, "bar_index": bar["i"]})
            if target_hit:
                return result("be_after_trigger", status="simulated_m15", final_r=1.5, exit_reason="final_target", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"be_trigger_time_utc": trigger_time, "bar_index": bar["i"]})
            if stop_hit:
                return result("be_after_trigger", status="simulated_m15", final_r=0.0, exit_reason="breakeven_stop", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"be_trigger_time_utc": trigger_time, "bar_index": bar["i"]})
    last = path[-1] if path else {"close_r": None, "time": None}
    return result("be_after_trigger", status="simulated_m15_path_end", final_r=last["close_r"], exit_reason="path_end_mark_to_market", exit_time=last["time"], mfe=mfe if path else None, mae=mae if path else None, trace={"be_trigger_time_utc": trigger_time})


def simulate_partial(path: list[dict[str, Any]]) -> dict[str, Any]:
    be = simulate_be(path)
    if be["gross_r"] is None:
        return {**be, "policy_name": "partial_be_runner"}
    if max((bar["max_r"] for bar in path), default=-999) < 1.0:
        fixed = simulate_target_stop(path, "partial_be_runner", 1.5)
        return fixed
    remainder = float(be["gross_r"])
    final_r = 0.5 * 1.0 + 0.5 * remainder
    return {**be, "policy_name": "partial_be_runner", "gross_r": round(final_r, 6), "exit_reason": "partial_50_at_1r_then_" + str(be["exit_reason"]), "transition_trace": {**be["transition_trace"], "partial_exit_r": 1.0, "partial_fraction": 0.5}}


def simulate_trailing(path: list[dict[str, Any]]) -> dict[str, Any]:
    mfe = -10**9
    mae = 10**9
    trail = -1.0
    active = False
    for bar in path:
        mfe = max(mfe, bar["max_r"])
        mae = min(mae, bar["min_r"])
        if bar["min_r"] <= trail:
            return result("trailing_runner", status="simulated_m15", final_r=trail, exit_reason="trailing_stop", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"trail_r": trail, "bar_index": bar["i"]})
        if mfe >= 1.0:
            active = True
            trail = max(trail, mfe - 0.5, 0.0)
        if bar["max_r"] >= 3.0:
            return result("trailing_runner", status="simulated_m15", final_r=3.0, exit_reason="runner_cap_target", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"trail_active": active, "bar_index": bar["i"]})
    last = path[-1] if path else {"close_r": None, "time": None}
    return result("trailing_runner", status="simulated_m15_path_end", final_r=last["close_r"], exit_reason="path_end_mark_to_market", exit_time=last["time"], mfe=mfe if path else None, mae=mae if path else None, trace={"trail_active": active, "trail_r": trail})


def simulate_early_cut(path: list[dict[str, Any]]) -> dict[str, Any]:
    mfe = -10**9
    mae = 10**9
    for bar in path:
        mfe = max(mfe, bar["max_r"])
        mae = min(mae, bar["min_r"])
        if bar["i"] >= 4 and mfe < 0.5 and bar["min_r"] <= -0.5:
            return result("early_cut_if_no_progress", status="simulated_m15", final_r=-0.5, exit_reason="early_cut_no_progress", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"bar_index": bar["i"], "required_progress_r": 0.5})
        if bar["min_r"] <= -1.0 or bar["max_r"] >= 1.5:
            break
    base = simulate_target_stop(path, "early_cut_if_no_progress", 1.5)
    base["transition_trace"] = {**base["transition_trace"], "early_cut_checked": True}
    return base


def simulate_momentum(path: list[dict[str, Any]]) -> dict[str, Any]:
    mfe = -10**9
    mae = 10**9
    active = False
    for bar in path:
        mfe = max(mfe, bar["max_r"])
        mae = min(mae, bar["min_r"])
        if bar["min_r"] <= -1.0 and not active:
            return result("momentum_exhaustion", status="simulated_m15", final_r=-1.0, exit_reason="stop_loss", exit_time=bar["time"], mfe=mfe, mae=mae)
        if mfe >= 1.0:
            active = True
        if active and bar["min_r"] <= max(0.0, mfe - 0.4):
            exit_r = max(0.0, mfe - 0.4)
            return result("momentum_exhaustion", status="simulated_m15", final_r=exit_r, exit_reason="momentum_exhaustion_pullback", exit_time=bar["time"], mfe=mfe, mae=mae, trace={"pullback_from_mfe_r": 0.4})
        if bar["max_r"] >= 2.0:
            return result("momentum_exhaustion", status="simulated_m15", final_r=2.0, exit_reason="momentum_runner_cap", exit_time=bar["time"], mfe=mfe, mae=mae)
    last = path[-1] if path else {"close_r": None, "time": None}
    return result("momentum_exhaustion", status="simulated_m15_path_end", final_r=last["close_r"], exit_reason="path_end_mark_to_market", exit_time=last["time"], mfe=mfe if path else None, mae=mae if path else None)


def simulate_policies(path: list[dict[str, Any]], fields: dict[str, Any], source_record: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not path:
        missing = ["source_path", "source_row_index", "ordered_m15_path"]
        return {policy: result(policy, status="not_replayable_missing_source", final_r=None, exit_reason=None, exit_time=None, mfe=None, mae=None, missing=missing) for policy in POLICIES}
    outputs = {
        "fixed_1_5r": simulate_target_stop(path, "fixed_1_5r", 1.5),
        "be_after_trigger": simulate_be(path),
        "trailing_runner": simulate_trailing(path),
        "partial_be_runner": simulate_partial(path),
        "hold_to_structure": simulate_target_stop(path, "hold_to_structure", 2.5),
        "early_cut_if_no_progress": simulate_early_cut(path),
        "momentum_exhaustion": simulate_momentum(path),
        "time_stop": result("time_stop", status="simulated_m15", final_r=path[min(32, len(path) - 1)]["close_r"], exit_reason="time_stop_32_m15_bars", exit_time=path[min(32, len(path) - 1)]["time"], mfe=max(bar["max_r"] for bar in path), mae=min(bar["min_r"] for bar in path), trace={"time_stop_bars": 32}),
    }
    ratio = float_or_none(fields.get("atr14_atr50_ratio")) or 1.0
    expansion_target = 2.0 if ratio >= 1.2 else 1.5
    outputs["volatility_session_expansion"] = simulate_target_stop(path, "volatility_session_expansion", expansion_target)
    outputs["volatility_session_expansion"]["transition_trace"] = {**outputs["volatility_session_expansion"]["transition_trace"], "atr14_atr50_ratio": ratio, "target_r": expansion_target}
    if fields.get("sweep_direction"):
        sweep = simulate_target_stop(path, "liquidity_sweep_exit", 1.0)
        sweep["transition_trace"] = {**sweep["transition_trace"], "sweep_direction": fields.get("sweep_direction")}
        outputs["liquidity_sweep_exit"] = sweep
    else:
        outputs["liquidity_sweep_exit"] = result("liquidity_sweep_exit", status="not_applicable_no_asof_sweep_state", final_r=None, exit_reason=None, exit_time=None, mfe=max(bar["max_r"] for bar in path), mae=min(bar["min_r"] for bar in path), missing=["asof_liquidity_sweep_state"])
    condition = (source_record or {}).get("condition_router_projection") or {}
    if condition.get("available") and condition.get("selected_policy_final_r") is not None:
        outputs["condition_router"] = result("condition_router", status="simulated_from_prior_condition_router_projection", final_r=float_or_none(condition.get("selected_policy_final_r")), exit_reason=f"condition_router_selected_{condition.get('selected_policy')}", exit_time=None, mfe=max(bar["max_r"] for bar in path), mae=min(bar["min_r"] for bar in path), trace={"selector_condition_key": condition.get("selector_condition_key"), "selected_policy": condition.get("selected_policy")})
    else:
        outputs["condition_router"] = result("condition_router", status="not_replayable_missing_condition_router_projection", final_r=None, exit_reason=None, exit_time=None, mfe=max(bar["max_r"] for bar in path), mae=min(bar["min_r"] for bar in path), missing=["condition_router_projection", "chrono_oof_cell_policy_for_row"])
    outputs["m1_tick_path_exit"] = result("m1_tick_path_exit", status="not_replayable_missing_ordered_m1_tick_source", final_r=None, exit_reason=None, exit_time=None, mfe=max(bar["max_r"] for bar in path), mae=min(bar["min_r"] for bar in path), missing=["m1_or_tick_source_path", "m1_or_tick_source_sha256", "ordered_tick_sequence"])
    return outputs


def runtime_support(policy: str) -> dict[str, Any]:
    support = {
        "be_after_trigger": (
            "implemented_live_vnext_selected_policy",
            "src/components/execution.py::SUPPORTED_VNEXT_DYNAMIC_EXECUTION_POLICIES",
            "tests/test_limit_order_flow.py::test_broader_origin_pending_fill_opens_trade_with_vnext_be_after_trigger_not_j46_j49",
        ),
        "partial_be_runner": (
            "implemented_live_vnext_selected_policy",
            "src/components/execution.py::set_limit_intent/check_limit_fill/_execute_tp1_partial/_execute_tp2_partial",
            "tests/test_limit_order_flow.py::test_vnext_partial_be_runner_pending_fill_uses_router_decision_and_lifecycle",
        ),
        "trailing_runner": (
            "implemented_live_vnext_selected_policy",
            "src/components/execution.py::set_limit_intent/check_limit_fill/_manage_vnext_trailing_runner/_execute_vnext_dynamic_final_close",
            "tests/test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router",
        ),
        "momentum_exhaustion": (
            "implemented_live_vnext_selected_policy",
            "src/components/execution.py::set_limit_intent/check_limit_fill/_manage_vnext_momentum_exhaustion/_execute_vnext_dynamic_final_close",
            "tests/test_limit_order_flow.py::test_vnext_momentum_exhaustion_pending_fill_closes_on_pullback_from_router",
        ),
        "time_stop": (
            "implemented_live_vnext_selected_policy",
            "src/components/execution.py::check_time_stop_and_close",
            "tests/test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count",
        ),
        "fixed_1_5r": (
            "baseline_supported_not_moonshot_execution_proof",
            "src/components/execution.py::open_trade",
            "tests/test_limit_order_flow.py",
        ),
    }
    status, surface, test = support.get(policy, ("not_implemented_activation_blocked", "src/components/execution.py", None))
    implemented = status.startswith("implemented_live")
    return {
        "runtime_surface": surface,
        "current_support_status": status,
        "test_evidence": test,
        "missing_code_path": None if implemented else "src/components/execution.py::check_and_manage_trade policy-specific branch",
        "required_test": test or f"tests/test_execution_intelligence_static_15r_ceiling_repair.py::test_runtime_gap_{policy}",
        "rollback_knob": "gtos_vnext_runtime.moonshot_dynamic_execution_router_apply_to_execution",
        "activation_blocker": None if implemented else "requires ordered LTF/tick path, live cost/deal lifecycle, prop replay, and guarded execution code before activation",
        "runtime_supported_now": implemented,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_stage04 = read_json(STAGE04_SUMMARY)
    source_records = collect_source_record_index()
    csv_cache = CsvCache()
    m1_index = M1AvailabilityIndex()
    tick_index = TickAvailabilityIndex()
    counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    policy_replayable_counts: Counter[str] = Counter()
    policy_status_counts: Counter[str] = Counter()
    policy_total_gross_r: defaultdict[str, float] = defaultdict(float)
    replay_class_counts: Counter[str] = Counter()
    missing_field_counts: Counter[str] = Counter()
    m1_availability_counts: Counter[str] = Counter()
    tick_availability_counts: Counter[str] = Counter()
    dynamic_rows = 0
    writers = {
        "denominator_reconciliation_ledger": PlainJsonlShardWriter(
            ledger_name="denominator_reconciliation_ledger",
            stem=DENOM_STEM,
            manifest_path=DENOM_MANIFEST,
        ),
        "winner_leftover_move_ledger": PlainJsonlShardWriter(
            ledger_name="winner_leftover_move_ledger",
            stem=WINNERS_STEM,
            manifest_path=WINNERS_MANIFEST,
        ),
        "loser_mitigation_ledger": PlainJsonlShardWriter(
            ledger_name="loser_mitigation_ledger",
            stem=LOSERS_STEM,
            manifest_path=LOSERS_MANIFEST,
        ),
        "be_classification_ledger": PlainJsonlShardWriter(
            ledger_name="be_classification_ledger",
            stem=BES_STEM,
            manifest_path=BES_MANIFEST,
        ),
        "dynamic_exit_counterfactual_ledger": PlainJsonlShardWriter(
            ledger_name="dynamic_exit_counterfactual_ledger",
            stem=DYNAMIC_STEM,
            manifest_path=DYNAMIC_MANIFEST,
        ),
        "runtime_surface_gap_ledger": PlainJsonlShardWriter(
            ledger_name="runtime_surface_gap_ledger",
            stem=RUNTIME_STEM,
            manifest_path=RUNTIME_MANIFEST,
        ),
        "replay_scoring_upgrade_ledger": PlainJsonlShardWriter(
            ledger_name="replay_scoring_upgrade_ledger",
            stem=UPGRADE_STEM,
            manifest_path=UPGRADE_MANIFEST,
        ),
    }
    for writer in writers.values():
        writer.reset()
    try:
        for row in selected_rows():
            counts["selected_rows"] += 1
            static_r = float(row.get("r_multiple") or 0.0)
            if static_r > 0:
                counts["winners"] += 1
            elif static_r < 0:
                counts["losers"] += 1
            else:
                counts["breakevens"] += 1
            rid = selected_row_id(row)
            source_record = source_records.get(str(row.get("candidate_id") or ""))
            source_path, source_sha = source_path_from(row, source_record)
            csv_rows = csv_cache.load(source_path) if source_path else []
            source_idx = int_or_none(row.get("source_row_index"))
            if source_idx is None and source_record:
                source_idx = int_or_none(source_record.get("source_row_index"))
            if source_idx is None and source_record:
                source_idx = csv_cache.index_for_time(
                    source_path,
                    source_record.get("candle_time_utc") or source_record.get("decision_time_utc"),
                )
            entry_price = float(row["entry_price"])
            stop_price = float(row["stop_or_invalidation"])
            entry_idx, entry_issue, delayed_fill_bars = entry_touch_index(
                csv_rows=csv_rows,
                start_idx=source_idx,
                entry=entry_price,
            )
            if entry_idx is None:
                path = []
                path_issue = entry_issue or "entry_price_not_touched_in_source_window"
            else:
                path, path_issue = path_arrays(
                    csv_rows=csv_rows,
                    start_idx=entry_idx,
                    entry=entry_price,
                    stop=stop_price,
                    side=str(row.get("side") or ""),
                )
            source_time = (
                csv_rows[source_idx]["time"]
                if source_idx is not None and 0 <= source_idx < len(csv_rows)
                else None
            )
            entry_time = (
                csv_rows[entry_idx]["time"]
                if entry_idx is not None and 0 <= entry_idx < len(csv_rows)
                else source_time
            )
            m1_lookup = m1_index.lookup(row.get("symbol"), entry_time)
            tick_lookup = tick_index.lookup(row.get("symbol"), entry_time)
            m1_availability_counts[str(m1_lookup.get("m1_availability_status"))] += 1
            tick_availability_counts[str(tick_lookup.get("tick_availability_status"))] += 1
            source_fields = source_fields_from(row, source_record, csv_rows, source_idx)
            policy_results = simulate_policies(path, source_fields, source_record)
            m1_policy = policy_results.get("m1_tick_path_exit")
            if m1_policy and (
                m1_lookup.get("m1_exact_entry_minute_present")
                or tick_lookup.get("tick_source_path")
            ):
                m1_policy["simulation_status"] = (
                    "not_replayable_ordered_m1_tick_sequence_not_materialized_from_available_source"
                )
                m1_policy["missing_fields"] = [
                    "ordered_m1_or_tick_sequence",
                    "intrabar_bid_ask_spread_sequence",
                    "intrabar_order_modify_close_retcode_sequence",
                ]
                m1_policy["transition_trace"] = {
                    **(m1_policy.get("transition_trace") or {}),
                    "m1_source_path": m1_lookup.get("m1_source_path"),
                    "tick_source_path": tick_lookup.get("tick_source_path"),
                    "m1_availability_status": m1_lookup.get("m1_availability_status"),
                    "tick_availability_status": tick_lookup.get("tick_availability_status"),
                }
            replay_class = "replayable_from_asof_m15_ohlc_path" if path else f"non_replayable_{path_issue or 'missing_source_context'}"
            replay_class_counts[replay_class] += 1
            denom_row = {
                "selected_row_id": rid,
                "candidate_id": row.get("candidate_id"),
                "selector_component": row.get("selector_component"),
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "framework": row.get("framework"),
                "origin_family": row.get("origin_family"),
                "side": row.get("side"),
                "static_stage04_r": static_r,
                "replay_class": replay_class,
                "non_replayable_reason": None if path else path_issue or "missing_source_context",
                "source_path": source_path,
                "source_sha256": source_sha or csv_cache.sha.get(source_path or ""),
                "source_row_index": source_idx,
                "source_time_utc": source_time,
                "entry_type": "limit_delayed_fill" if delayed_fill_bars and delayed_fill_bars > 0 else "market_or_immediate_limit_fill",
                "entry_timing": "source_entry_touch_bar" if entry_idx is not None else "entry_touch_not_found",
                "entry_touch_source_row_index": entry_idx,
                "entry_touch_time_utc": entry_time,
                "delayed_fill_bars": delayed_fill_bars,
                "limit_fill_status": "filled_on_source_entry_touch" if entry_idx is not None else "no_fill_in_source_window",
                "fill_status": row.get("fill_status") or ("filled_on_source_entry_touch" if entry_idx is not None else "not_filled"),
                "selected_policy": row.get("selected_policy"),
                "cost_status": row.get("cost_bucket"),
                **m1_lookup,
                **tick_lookup,
            }
            writers["denominator_reconciliation_ledger"].write(denom_row)
            fixed = policy_results["fixed_1_5r"]
            be = policy_results["be_after_trigger"]
            if static_r > 0:
                winner_row = {
                    **denom_row,
                    "mfe_r": fixed.get("mfe_r"),
                    "mae_r": fixed.get("mae_r"),
                    "leftover_after_1_5r": max(0.0, float(fixed.get("mfe_r") or 0.0) - 1.5) if fixed.get("mfe_r") is not None else None,
                    "time_to_1_5r": fixed.get("exit_time_utc") if fixed.get("gross_r") == 1.5 else None,
                    "post_target_giveback_r": None,
                    "same_bar_ambiguity": fixed.get("same_bar_ambiguity"),
                    "source_mode": "OHLC_M15_CSV",
                }
                writers["winner_leftover_move_ledger"].write(winner_row)
            elif static_r < 0:
                loser_row = {
                    **denom_row,
                    "mfe_before_stop_r": fixed.get("mfe_r"),
                    "mae_r": fixed.get("mae_r"),
                    "time_to_stop": fixed.get("exit_time_utc") if str(fixed.get("exit_reason") or "").startswith("stop") else None,
                    "time_to_0_5r": None,
                    "time_to_1r": be.get("transition_trace", {}).get("be_trigger_time_utc"),
                    "earlier_exit_saved_r": (policy_results["early_cut_if_no_progress"].get("gross_r") or -1.0) - static_r if policy_results["early_cut_if_no_progress"].get("gross_r") is not None else None,
                    "invalidation_shift_saved_r": None,
                    "no_fill_saved_r": 1.0,
                    "delayed_entry_saved_r": None,
                    "path_aware_management_saved_r": max((policy_results["trailing_runner"].get("gross_r") or -1.0) - static_r, (be.get("gross_r") or -1.0) - static_r),
                    "mitigation_class": "mitigable_after_positive_excursion" if (fixed.get("mfe_r") or 0) >= 0.5 else "direct_loss_no_positive_excursion",
                    "same_bar_ambiguity": fixed.get("same_bar_ambiguity"),
                }
                writers["loser_mitigation_ledger"].write(loser_row)
            else:
                fixed_r = fixed.get("gross_r")
                be_r = be.get("gross_r")
                if fixed.get("same_bar_ambiguity") or be.get("same_bar_ambiguity"):
                    be_class = "same_bar_ambiguous"
                elif fixed_r is not None and fixed_r < 0 and (be_r or 0) >= 0:
                    be_class = "saved_loser"
                elif fixed_r is not None and fixed_r > 0 and (be_r or 0) <= 0:
                    be_class = "killed_winner"
                elif (fixed.get("mfe_r") or 0) >= 1.5:
                    be_class = "missed_winner"
                else:
                    be_class = "true_scratch"
                be_row = {
                    **denom_row,
                    "be_classification": be_class,
                    "be_trigger_r": 1.0,
                    "mfe_after_be_r": be.get("mfe_r"),
                    "mae_after_be_r": be.get("mae_r"),
                    "fixed_policy_r": fixed_r,
                    "be_policy_r": be_r,
                    "classification_reason": f"fixed={fixed_r} be={be_r} exit={be.get('exit_reason')}",
                    "same_bar_ambiguity": be.get("same_bar_ambiguity"),
                }
                writers["be_classification_ledger"].write(be_row)
            m1_or_tick_source_available = bool(
                m1_lookup.get("m1_exact_entry_minute_present") or tick_lookup.get("tick_source_path")
            )
            missing_fields = set(HISTORICAL_COST_MISSING_FIELDS)
            if any(item.get("same_bar_ambiguity") for item in policy_results.values()):
                if m1_or_tick_source_available:
                    missing_fields.add("ordered_m1_or_tick_sequence_for_same_bar_resolution")
                else:
                    missing_fields.add("ordered_m1_or_tick_path_for_same_bar")
            for policy_name in POLICIES:
                item = policy_results[policy_name]
                policy_counts[policy_name] += 1
                policy_status_counts[f"{policy_name}:{item.get('simulation_status')}"] += 1
                if item.get("gross_r") is not None:
                    policy_replayable_counts[policy_name] += 1
                    policy_total_gross_r[policy_name] += float(item["gross_r"])
                dynamic_rows += 1
                support = runtime_support(policy_name)
                source_blocker = None
                if str(item.get("simulation_status") or "").startswith(("not_", "not_applicable")):
                    source_blocker = ",".join(str(field) for field in item.get("missing_fields") or []) or item.get("simulation_status")
                dyn = {
                    **denom_row,
                    "policy_name": policy_name,
                    "policy_params": item.get("transition_trace"),
                    "asof_features_used": sorted(k for k in source_fields.keys() if k in {"atr14", "atr50", "atr14_atr50_ratio", "body_atr14", "range_atr14", "sweep_direction", "trend_state_20"}),
                    "forbidden_future_features_used": [],
                    "transition_trace": item.get("transition_trace"),
                    "exit_reason": item.get("exit_reason"),
                    "exit_time_utc": item.get("exit_time_utc"),
                    "gross_r": item.get("gross_r"),
                    "net_r": item.get("net_r"),
                    "cost_r": item.get("cost_r"),
                    "cost_status": item.get("cost_status"),
                    "commission_status": "ACCOUNT_HISTORY_REQUIRED_AT_LIVE_FILL_CLOSE",
                    "spread_status": "MISSING_HISTORICAL_ORDER_SEND_SPREAD",
                    "slippage_status": "MISSING_HISTORICAL_FILL_SLIPPAGE",
                    "source_completeness": (
                        "m15_ohlc_path_present_m1_or_tick_source_available_cost_lifecycle_missing"
                        if path and m1_or_tick_source_available
                        else "m15_ohlc_path_present_cost_lifecycle_missing"
                        if path
                        else "source_path_missing_or_unusable"
                    ),
                    "source_blocker": source_blocker,
                    "non_replayable_reason": None if path else path_issue or "missing_source_context",
                    "runtime_supported_now": bool(support["runtime_supported_now"]),
                    "order_modify_lifecycle_status": "historical_replay_no_live_order_modify" if policy_name in {"be_after_trigger", "partial_be_runner", "trailing_runner", "momentum_exhaustion"} else "not_required_for_policy_or_missing_runtime",
                    "close_order_lifecycle_status": "historical_replay_no_live_close_order" if policy_name != "fixed_1_5r" else "broker_static_tp_or_sl_path",
                    "fill_lifecycle_status": "entry_touch_replayed_from_ohlc_no_broker_fill_id" if path else "no_replayable_fill",
                    "prop_account_impact_status": "gross_r_only_net_cost_blocked",
                    "simulation_status": item.get("simulation_status"),
                    "same_bar_ambiguity": item.get("same_bar_ambiguity"),
                    "prop_account_delta_pct_gross": round((item.get("gross_r") or 0.0) * float(row.get("risk_per_trade_pct_current") or 0.0), 6) if item.get("gross_r") is not None else None,
                }
                writers["dynamic_exit_counterfactual_ledger"].write(dyn)
                runtime_row = {
                    **denom_row,
                    "policy_name": policy_name,
                    "source_support_status": item.get("simulation_status"),
                    "source_blocker": source_blocker,
                    "runtime_surface": support["runtime_surface"],
                    "current_support_status": support["current_support_status"],
                    "runtime_supported_now": bool(support["runtime_supported_now"]),
                    "test_evidence": support["test_evidence"],
                    "missing_code_path": support["missing_code_path"],
                    "required_test": support["required_test"],
                    "rollback_knob": support["rollback_knob"],
                    "activation_blocker": support["activation_blocker"],
                }
                writers["runtime_surface_gap_ledger"].write(runtime_row)
                for field in item.get("missing_fields") or ():
                    missing_fields.add(str(field))
            for field in missing_fields:
                missing_field_counts[field] += 1
            upgrade_row = {
                **denom_row,
                "missing_fields_after_source_search": sorted(missing_fields),
                "exact_missing_source_paths": [source_path] if source_path else [],
                "available_m1_source_path": m1_lookup.get("m1_source_path"),
                "available_m1_source_sha256": m1_lookup.get("m1_source_sha256"),
                "available_tick_source_path": tick_lookup.get("tick_source_path"),
                "available_tick_source_sha256": tick_lookup.get("tick_source_sha256"),
                "m1_source_absence_proof": (
                    None
                    if m1_lookup.get("m1_exact_entry_minute_present")
                    else {
                        "status": m1_lookup.get("m1_availability_status"),
                        "searched_manifests": m1_lookup.get("m1_source_search_manifests"),
                        "lookup_time_utc": m1_lookup.get("m1_lookup_time_utc"),
                    }
                ),
                "tick_source_absence_proof": (
                    None
                    if tick_lookup.get("tick_source_path")
                    else {
                        "status": tick_lookup.get("tick_availability_status"),
                        "search_root": tick_lookup.get("tick_source_search_root"),
                        "lookup_date_utc": tick_lookup.get("tick_lookup_date_utc"),
                    }
                ),
                "upgrade_reason": "activation_grade_net_execution_replay_requires_live_or_ordered_lower_timeframe_fields",
            }
            writers["replay_scoring_upgrade_ledger"].write(upgrade_row)
    finally:
        for writer in writers.values():
            writer.close()

    output_meta = {key: writer.meta() for key, writer in writers.items()}
    policy_metrics = {}
    fixed_total = policy_total_gross_r.get("fixed_1_5r", 0.0)
    fixed_count = policy_replayable_counts.get("fixed_1_5r", 0)
    fixed_expectancy = fixed_total / fixed_count if fixed_count else None
    for policy in POLICIES:
        count = policy_replayable_counts.get(policy, 0)
        total = policy_total_gross_r.get(policy, 0.0)
        expectancy = total / count if count else None
        policy_metrics[policy] = {
            "replayable_rows_with_gross_r": count,
            "gross_r_sum": round(total, 6),
            "gross_r_expectancy": round(expectancy, 9) if expectancy is not None else None,
            "delta_expectancy_vs_fixed_1_5r": (
                round(expectancy - fixed_expectancy, 9)
                if expectancy is not None and fixed_expectancy is not None
                else None
            ),
        }
    implemented_policy_metrics = {
        policy: metrics
        for policy, metrics in policy_metrics.items()
        if runtime_support(policy)["runtime_supported_now"]
    }
    best_implemented = None
    if implemented_policy_metrics:
        best_implemented = max(
            implemented_policy_metrics.items(),
            key=lambda item: item[1]["gross_r_expectancy"]
            if item[1]["gross_r_expectancy"] is not None
            else float("-inf"),
        )
    verdict = {
        "baseline_policy": "fixed_1_5r",
        "fixed_1_5r_role": "baseline_comparator_and_fail_closed_fallback_only_not_live_default",
        "baseline_replayable_rows": fixed_count,
        "baseline_gross_r_sum": round(fixed_total, 6),
        "baseline_gross_r_expectancy": round(fixed_expectancy, 9) if fixed_expectancy is not None else None,
        "best_implemented_policy": best_implemented[0] if best_implemented else None,
        "best_implemented_gross_r_expectancy": (
            best_implemented[1]["gross_r_expectancy"] if best_implemented else None
        ),
        "best_implemented_delta_expectancy_vs_fixed_1_5r": (
            best_implemented[1]["delta_expectancy_vs_fixed_1_5r"] if best_implemented else None
        ),
        "production_policy_selection_mode": "condition_asof_displacement_v1_dynamic_router",
        "production_policy_is_single_global_style": False,
        "implemented_live_policy_set": sorted(implemented_policy_metrics),
        "launch_router_policy_set": [
            "momentum_exhaustion",
            "partial_be_runner",
        ],
        "gross_replay_policy_ranking_is_diagnostic_not_a_single_launch_policy": True,
        "net_r_verdict": "blocked_until_live_cost_slippage_commission_swap_and_deal_reconciliation_are_captured",
    }
    summary = {
        "schema_version": "execution_intelligence_static_15r_ceiling_repair_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "completed_execution_intelligence_static_15r_replay_layer",
        "stage04_selected_denominator": summary_stage04["selector_counts"]["combined_selected_rows"],
        "selected_rows_processed": counts["selected_rows"],
        "winner_rows": counts["winners"],
        "loser_rows": counts["losers"],
        "breakeven_rows": counts["breakevens"],
        "dynamic_policy_rows": dynamic_rows,
        "policy_counts": dict(sorted(policy_counts.items())),
        "policy_replayable_counts": dict(sorted(policy_replayable_counts.items())),
        "policy_status_counts": dict(sorted(policy_status_counts.items())),
        "policy_metrics": policy_metrics,
        "dynamic_layer_verdict": verdict,
        "replay_class_counts": dict(sorted(replay_class_counts.items())),
        "missing_field_counts": dict(sorted(missing_field_counts.items())),
        "m1_availability_status_counts": dict(sorted(m1_availability_counts.items())),
        "tick_availability_status_counts": dict(sorted(tick_availability_counts.items())),
        "m1_source_search_manifests": m1_index.searched_manifests,
        "tick_source_search_root": rel(REPO_ROOT / LOCAL_TICK_ROOT),
        "cost_lifecycle_truth": "gross_r_only_historical_replay_net_r_blocked_until live spread/slippage/commission/swap/deal lifecycle captured",
        "static_ceiling_not_terminal": True,
        "ledger_output_format": "uncompressed_plain_jsonl_shards_with_manifest",
        "outputs": output_meta,
    }
    write_json(SUMMARY, summary)
    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "execution_intelligence_static_15r_replay_layer_built",
            "generated_at_utc": summary["generated_at_utc"],
            "route_id": ROUTE_ID,
            "selected_rows": counts["selected_rows"],
            "dynamic_policy_rows": dynamic_rows,
            "status": summary["status"],
        },
    )
    print(json.dumps({"status": summary["status"], "selected_rows": counts["selected_rows"], "dynamic_policy_rows": dynamic_rows}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
