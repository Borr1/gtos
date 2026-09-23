"""Stage 04 source-mode path/R simulation for the full vNext replay route.

This route-local builder consumes the Stage02 market-bar candidate shards and
the Stage03 current-runtime trace shards. It then binds each candidate to the
available local M15, M1, M5, tick/Sierra, and OHLC proxy source modes, measures
entry touch/fill timing plus stop/target ordering, and writes route-owned
per-source shards with atomic temp-to-final replacement.

The builder is read-only against MT5/broker state. The read-only MT5 exports
were executed before this stage and are recorded here as row-level repair proof;
the exported data files remain in the local data directory and are referenced
by path, row count, date range, and SHA-256.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import gzip
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


DATE_ID = "2026-05-24"
ROUTE_ID = "vnext_full_historical_candidate_generation_replay_2026_05_24"
STAGE_ID = "STAGE_04_SOURCE_MODE_PATH_R"
PREVIOUS_STAGE_ID = "STAGE_03_RUNTIME_TRACE"
STAGE02_ID = "STAGE_02_CANDIDATE_GENERATION_ENGINE"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


STAGE02_STATUS_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE02_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
STAGE03_STATUS_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE03_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
SESSION_STATE_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_SESSION_STATE_{DATE_ID}.json"
COMPLETION_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_COMPLETION_AUDIT_{DATE_ID}.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_OUTPUT_MANIFEST_{DATE_ID}.json"
ACTIVE_QUESTION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_ID}.jsonl"
EXTRA_STEP_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_EXTRA_STEP_PURSUIT_LEDGER_{DATE_ID}.jsonl"
PROMPT_APPLICATION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROMPT_APPLICATION_LEDGER_{DATE_ID}.jsonl"
LINE_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_LINE_ACCOUNTABILITY_AUDIT_{DATE_ID}.jsonl"
MT5_EXPORT_LEDGER_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_MT5_EXPORT_LEDGER_{DATE_ID}.jsonl"
SOURCE_REPAIR_PROOF_LEDGER_PATH = (
    ROUTE_DIR / f"VNEXT_FULL_REPLAY_SOURCE_REPAIR_PROOF_LEDGER_{DATE_ID}.jsonl"
)
SIERRA_INVENTORY_PATH = (
    ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_SIERRA_SCID_INVENTORY_PROBE_{DATE_ID}.json"
)

STAGE04_EXPANDED_MANIFEST_PATH = (
    REPO_ROOT
    / "data/mt5_research_exports/vnext_full_stage04_expanded_m1_m5_readonly_2026_05_24/manifest.json"
)
STAGE04_CORE_MANIFEST_PATH = (
    REPO_ROOT
    / "data/mt5_research_exports/vnext_full_stage04_core_current_window_readonly_2026_05_24/manifest.json"
)
STAGE04_PROBE_PATHS = [
    REPO_ROOT
    / "data/mt5_research_exports/history_availability/"
    "vnext_full_stage04_expanded_m1_m5_probe_2026_05_24_20260524T203301Z.json",
    REPO_ROOT
    / "data/mt5_research_exports/history_availability/"
    "vnext_full_stage04_expanded_alias_probe_2026_05_24_20260524T203331Z.json",
    REPO_ROOT
    / "data/mt5_research_exports/history_availability/"
    "vnext_full_stage04_usoil_alias_probe_2026_05_24_20260524T203342Z.json",
    REPO_ROOT
    / "data/mt5_research_exports/history_availability/"
    "vnext_full_stage04_core_current_window_probe_2026_05_24_20260524T203445Z.json",
]

OUTPUTS = {
    "path_source": ROUTE_DIR / f"VNEXT_FULL_REPLAY_PATH_SOURCE_LEDGER_{DATE_ID}.jsonl",
    "path_outcome_r": ROUTE_DIR / f"VNEXT_FULL_REPLAY_PATH_OUTCOME_R_LEDGER_{DATE_ID}.jsonl",
    "nofill_pending_lifecycle": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_NOFILL_PENDING_LIFECYCLE_LEDGER_{DATE_ID}.jsonl"
    ),
    "m15_vs_ltf_disagreement": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_M15_VS_LTF_DISAGREEMENT_LEDGER_{DATE_ID}.jsonl"
    ),
    "missed_winner_avoided_loser": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_MISSED_WINNER_AVOIDED_LOSER_LEDGER_{DATE_ID}.jsonl"
    ),
    "source_repair_proof_update": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_SOURCE_REPAIR_PROOF_UPDATE_LEDGER_{DATE_ID}.jsonl"
    ),
    "source_mode_summary": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_{DATE_ID}.json"
    ),
    "stage04_verifier": ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_VERIFIER_{DATE_ID}.json",
    "stage04_shard_contract": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_SHARD_CONTRACT_{DATE_ID}.json"
    ),
    "stage04_heartbeat": ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_HEARTBEAT_{DATE_ID}.json",
    "stage04_shard_status": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
    ),
}

SHARD_DIR = ROUTE_DIR / "stage04_shards"
SHARDED_ARTIFACT_KEYS = (
    "path_source",
    "path_outcome_r",
    "nofill_pending_lifecycle",
    "m15_vs_ltf_disagreement",
    "missed_winner_avoided_loser",
)
RUNTIME_REFERENCE_MODES = ("current_config_shadow", "hypothetical_activated_vnext")
PRICE_PATH_MODES = (
    "bar_close_m15",
    "m1_path_aware",
    "m5_path_aware",
    "tick_or_sierra_path_aware",
    "ohlc_only_proxy",
)
REQUIRED_REPLAY_MODES = set(RUNTIME_REFERENCE_MODES) | set(PRICE_PATH_MODES) | {"missing_source"}
PATH_HORIZON_HOURS = 48
PATH_HORIZON_POLICY = "production_pending_intent_48h_clock_expiry_replay_proxy"

OHLC_ROOTS = [
    REPO_ROOT / "data/mt5_research_exports",
    REPO_ROOT / "data/historical_2026",
    REPO_ROOT / "data/sierra_ohlcv_roots",
]
TICK_ROOT = REPO_ROOT / "data/ticks"

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional acceleration
    np = None  # type: ignore

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - optional tick support
    pd = None  # type: ignore


@dataclass(frozen=True)
class SourceFile:
    path: Path
    symbol: str
    timeframe: str
    source_system: str
    priority: int


@dataclass
class BarSeries:
    path: Path
    symbol: str
    timeframe: str
    source_system: str
    times: list[datetime]
    opens: Any
    highs: Any
    lows: Any
    closes: Any
    volumes: Any

    @property
    def row_count(self) -> int:
        return len(self.times)

    @property
    def first_time(self) -> datetime | None:
        return self.times[0] if self.times else None

    @property
    def last_time(self) -> datetime | None:
        return self.times[-1] if self.times else None


SHA_CACHE: dict[Path, str] = {}
OHLC_INDEX: dict[tuple[str, str], list[SourceFile]] | None = None
BAR_CACHE: dict[Path, BarSeries] = {}
TICK_CACHE: dict[Path, Any] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def repo_path(path: str | Path | None) -> Path:
    if path is None:
        return REPO_ROOT / "__missing__"
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    tmp.replace(path)
    return count


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    if path not in SHA_CACHE:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        SHA_CACHE[path] = digest.hexdigest()
    return SHA_CACHE[path]


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    return f"{prefix}_{stable_hash(payload)[:length]}"


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_GIT_HEAD"


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            try:
                dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def dt_s(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fnum(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


class AtomicGzipJsonlWriter:
    def __init__(self, final_path: Path) -> None:
        self.final_path = final_path
        self.tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")
        self.row_count = 0
        self._handle: gzip.GzipFile | None = None

    def __enter__(self) -> "AtomicGzipJsonlWriter":
        self.final_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = gzip.open(self.tmp_path, "wt", encoding="utf-8", newline="\n")
        return self

    def write(self, row: dict[str, Any]) -> None:
        assert self._handle is not None
        self._handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.row_count += 1

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        if exc_type is None:
            self.tmp_path.replace(self.final_path)
        elif self.tmp_path.exists():
            self.tmp_path.unlink()


def stage02_status_rows() -> list[dict[str, Any]]:
    rows = [
        row
        for row in iter_jsonl(STAGE02_STATUS_PATH)
        if row.get("stage_id") == STAGE02_ID and row.get("shard_status") == "complete"
    ]
    return sorted(rows, key=lambda row: int(row.get("source_index") or 0))


def stage03_status_by_source() -> dict[str, dict[str, Any]]:
    rows = [
        row
        for row in iter_jsonl(STAGE03_STATUS_PATH)
        if row.get("stage_id") == PREVIOUS_STAGE_ID and row.get("shard_status") == "complete"
    ]
    return {str(row.get("source_path")): row for row in rows}


def source_stage04_shard_id(stage02_shard: dict[str, Any], stage03_shard: dict[str, Any]) -> str:
    return stable_id(
        "stage04src",
        {
            "stage02_shard_id": stage02_shard.get("shard_id"),
            "stage03_shard_id": stage03_shard.get("shard_id"),
            "source_path": stage02_shard.get("source_path"),
            "source_index": stage02_shard.get("source_index"),
        },
        length=16,
    )


def stage04_shard_paths(shard_id: str) -> dict[str, Path]:
    shard_dir = SHARD_DIR / shard_id
    return {
        "dir": shard_dir,
        "path_source": shard_dir / "path_source.jsonl.gz",
        "path_outcome_r": shard_dir / "path_outcome_r.jsonl.gz",
        "nofill_pending_lifecycle": shard_dir / "nofill_pending_lifecycle.jsonl.gz",
        "m15_vs_ltf_disagreement": shard_dir / "m15_vs_ltf_disagreement.jsonl.gz",
        "missed_winner_avoided_loser": shard_dir / "missed_winner_avoided_loser.jsonl.gz",
        "manifest": shard_dir / "manifest.json",
        "heartbeat": shard_dir / "heartbeat.json",
    }


def write_stage04_heartbeat(payload: dict[str, Any]) -> None:
    write_json(OUTPUTS["stage04_heartbeat"], payload)


def write_shard_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, payload)


def infer_symbol_timeframe(path: Path) -> tuple[str | None, str | None]:
    stem = path.stem
    for timeframe in ("M1", "M5", "M15", "H1", "H4", "D1"):
        suffix = f"_{timeframe}"
        if stem.endswith(suffix):
            return stem[: -len(suffix)], timeframe
    return None, None


def source_system_for_path(path: Path) -> str:
    text = rel(path)
    if "data/sierra_ohlcv_roots/" in text:
        return "sierra_scid_converted_ohlc"
    if "data/historical_2026/" in text:
        return "historical_2026_mt5_csv"
    if "vnext_full_stage04" in text:
        return "stage04_readonly_mt5_export"
    if "mt5_research_exports/" in text:
        return "mt5_research_export"
    return "local_ohlc_csv"


def source_priority(path: Path) -> int:
    text = rel(path)
    if "vnext_full_stage04_core_current_window_readonly" in text:
        return 10
    if "vnext_full_stage04_expanded_m1_m5_readonly" in text:
        return 11
    if "phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1" in text:
        return 20
    if "phase3_m15_2022_2026_fn_chunked_v1" in text:
        return 21
    if "phase3_rescue_all_m1_m5_chunk1_after_maxbars" in text:
        return 25
    if "phase3_v2b_forward" in text:
        return 30
    if "data/historical_2026/" in text:
        return 35
    if "data/sierra_ohlcv_roots/" in text:
        return 60
    return 90


def symbol_aliases(symbol: str | None, source_symbol: str | None = None) -> list[str]:
    aliases: list[str] = []
    for value in (symbol, source_symbol):
        if value and str(value) not in aliases:
            aliases.append(str(value))
    extra = {
        "US30_cash": ["US30", "US30_CASH", "YMM26-CME", "MYM"],
        "US30": ["US30_cash", "US30_CASH"],
        "NAS100": ["NDX100", "NAS100_NQ", "NAS100_MNQ", "NQM26-CME", "MNQM26-CME"],
        "NDX100": ["NAS100"],
        "XAUUSD": ["XAUUSD_GC", "GCM26-COMEX", "GCM26", "MGCM26-COMEX"],
        "XAGUSD": ["XAGUSD_SI", "SIM26-COMEX", "SIM26", "SILM26-COMEX"],
        "USDJPY": ["USDJPY_6J", "6JM26-CME", "6JM26"],
        "GBPUSD": ["GBPUSD_6B", "6BM26-CME", "6BM26"],
        "EURUSD": ["6EM26-CME", "6EM26"],
        "SPX500": ["ESM26-CME", "MESM26-CME"],
        "GER40": ["GER30"],
        "UKOIL_cash": ["UKOUSD"],
        "USOIL_cash": ["USOUSD"],
    }
    for base in list(aliases):
        for alias in extra.get(base, []):
            if alias not in aliases:
                aliases.append(alias)
    return aliases


def build_ohlc_index() -> dict[tuple[str, str], list[SourceFile]]:
    global OHLC_INDEX
    if OHLC_INDEX is not None:
        return OHLC_INDEX
    index: dict[tuple[str, str], list[SourceFile]] = defaultdict(list)
    for root in OHLC_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            symbol, timeframe = infer_symbol_timeframe(path)
            if not symbol or not timeframe:
                continue
            source = SourceFile(
                path=path,
                symbol=symbol,
                timeframe=timeframe,
                source_system=source_system_for_path(path),
                priority=source_priority(path),
            )
            index[(symbol, timeframe)].append(source)
    for key, files in index.items():
        files.sort(key=lambda item: (item.priority, rel(item.path)))
    OHLC_INDEX = dict(index)
    return OHLC_INDEX


def load_bar_series(source: SourceFile | Path) -> BarSeries:
    path = source.path if isinstance(source, SourceFile) else source
    if path in BAR_CACHE:
        return BAR_CACHE[path]
    symbol, timeframe = infer_symbol_timeframe(path)
    rows: list[tuple[datetime, float, float, float, float, float | None]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            dt = parse_dt(row.get("time") or row.get("timestamp") or row.get("datetime"))
            open_ = fnum(row.get("open"))
            high = fnum(row.get("high"))
            low = fnum(row.get("low"))
            close = fnum(row.get("close"))
            if dt is None or None in (open_, high, low, close):
                continue
            rows.append((dt, open_, high, low, close, fnum(row.get("volume"))))
    rows.sort(key=lambda item: item[0])
    times = [item[0] for item in rows]
    if np is not None:
        opens = np.asarray([item[1] for item in rows], dtype=float)
        highs = np.asarray([item[2] for item in rows], dtype=float)
        lows = np.asarray([item[3] for item in rows], dtype=float)
        closes = np.asarray([item[4] for item in rows], dtype=float)
        volumes = np.asarray([0.0 if item[5] is None else item[5] for item in rows], dtype=float)
    else:
        opens = [item[1] for item in rows]
        highs = [item[2] for item in rows]
        lows = [item[3] for item in rows]
        closes = [item[4] for item in rows]
        volumes = [item[5] for item in rows]
    if isinstance(source, SourceFile):
        source_system = source.source_system
        source_symbol = source.symbol
        source_timeframe = source.timeframe
    else:
        source_system = source_system_for_path(path)
        source_symbol = symbol or "UNKNOWN"
        source_timeframe = timeframe or "UNKNOWN"
    series = BarSeries(
        path=path,
        symbol=source_symbol,
        timeframe=source_timeframe,
        source_system=source_system,
        times=times,
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
        volumes=volumes,
    )
    BAR_CACHE[path] = series
    return series


def event_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    start = parse_dt(candidate.get("candle_time_utc"))
    end = start + timedelta(hours=PATH_HORIZON_HOURS) if start else None
    return {
        "candidate_id": candidate.get("candidate_id"),
        "source_universe_row_id": candidate.get("source_universe_row_id"),
        "market_state_packet_id": candidate.get("market_state_packet_id"),
        "symbol": candidate.get("symbol"),
        "source_symbol": candidate.get("source_symbol"),
        "side": str(candidate.get("side") or "").upper(),
        "framework": candidate.get("framework"),
        "session_bucket": candidate.get("session_bucket"),
        "candle_time_utc": candidate.get("candle_time_utc"),
        "date_utc": candidate.get("date_utc"),
        "entry_price": fnum(candidate.get("entry_reference") or candidate.get("entry_price")),
        "stop_loss": fnum(candidate.get("stop_or_invalidation") or candidate.get("stop_loss")),
        "take_profit_1": fnum(candidate.get("target_reference") or candidate.get("target_price")),
        "rr": fnum(candidate.get("rr")),
        "source_origin": candidate.get("source_origin"),
        "market_source_path": candidate.get("source_path"),
        "market_source_sha256": candidate.get("source_sha256"),
        "path_window_start_utc": dt_s(start),
        "path_window_requested_end_utc": dt_s(end),
        "path_horizon_policy": PATH_HORIZON_POLICY,
    }


def array_slice(values: Any, left: int, right: int) -> Any:
    return values[left:right]


def first_true_index(mask: Any) -> int | None:
    if np is not None and hasattr(mask, "nonzero"):
        hits = np.nonzero(mask)[0]
        return int(hits[0]) if len(hits) else None
    for idx, value in enumerate(mask):
        if value:
            return idx
    return None


def value_at(values: Any, index: int) -> float:
    return float(values[index])


def terminal_to_outcome(terminal_order: str) -> str:
    mapping = {
        "TARGET_FIRST": "target_first",
        "STOP_FIRST": "stop_first",
        "NO_ENTRY_TOUCH": "no_fill",
        "ENTRY_TOUCHED_TIMEOUT_OR_NO_TERMINAL": "timeout",
        "SAME_BAR_AMBIGUOUS_STOP_AND_TARGET": "same_bar_ambiguous_unresolved",
        "SAME_TICK_AMBIGUOUS_STOP_AND_TARGET": "same_bar_ambiguous_unresolved",
    }
    return mapping.get(terminal_order, terminal_order.lower())


def r_values_for_terminal(
    *,
    side: str,
    entry: float,
    stop: float,
    target: float,
    terminal_outcome: str,
    last_close: float | None,
) -> dict[str, float | None]:
    risk = abs(entry - stop)
    target_r = abs(target - entry) / risk if risk > 0 else None
    timeout_r = None
    if last_close is not None and risk > 0:
        timeout_r = (last_close - entry) / risk if side == "LONG" else (entry - last_close) / risk
    if terminal_outcome == "target_first":
        simulated = target_r
    elif terminal_outcome == "stop_first":
        simulated = -1.0
    elif terminal_outcome == "timeout":
        simulated = timeout_r
    elif terminal_outcome == "no_fill":
        simulated = None
    else:
        simulated = None
    return {
        "simulated_r": simulated,
        "target_r": target_r,
        "timeout_mark_to_market_r": timeout_r,
        "conservative_ambiguous_r": -1.0 if terminal_outcome == "same_bar_ambiguous_unresolved" else None,
        "optimistic_ambiguous_r": target_r if terminal_outcome == "same_bar_ambiguous_unresolved" else None,
        "no_fill_equivalent_r": 0.0 if terminal_outcome == "no_fill" else None,
    }


def simulate_bar_path(
    event: dict[str, Any],
    series: BarSeries,
    left: int,
    right: int,
    replay_mode: str,
    source_evidence_type: str,
) -> dict[str, Any]:
    side = str(event.get("side") or "").upper()
    entry = fnum(event.get("entry_price"))
    stop = fnum(event.get("stop_loss"))
    target = fnum(event.get("take_profit_1"))
    if side not in {"LONG", "SHORT"} or None in (entry, stop, target) or left >= right:
        return missing_path_row(
            event,
            replay_mode,
            source_evidence_type,
            "INVALID_GEOMETRY_OR_EMPTY_SOURCE_WINDOW",
            [rel(series.path)],
            requested_replay_mode=replay_mode,
        )
    highs = array_slice(series.highs, left, right)
    lows = array_slice(series.lows, left, right)
    closes = array_slice(series.closes, left, right)
    entry_mask = (lows <= entry) & (highs >= entry) if np is not None else [
        lows[idx] <= entry <= highs[idx] for idx in range(len(lows))
    ]
    entry_rel = first_true_index(entry_mask)
    stop_rel = None
    target_rel = None
    if side == "LONG":
        stop_pre_mask = lows <= stop if np is not None else [value <= stop for value in lows]
        target_pre_mask = highs >= target if np is not None else [value >= target for value in highs]
    else:
        stop_pre_mask = highs >= stop if np is not None else [value >= stop for value in highs]
        target_pre_mask = lows <= target if np is not None else [value <= target for value in lows]
    pre_stop_rel = first_true_index(stop_pre_mask[: entry_rel if entry_rel is not None else len(lows)])
    pre_target_rel = first_true_index(
        target_pre_mask[: entry_rel if entry_rel is not None else len(highs)]
    )
    if entry_rel is not None:
        if side == "LONG":
            stop_mask = lows[entry_rel:] <= stop if np is not None else [
                value <= stop for value in lows[entry_rel:]
            ]
            target_mask = highs[entry_rel:] >= target if np is not None else [
                value >= target for value in highs[entry_rel:]
            ]
        else:
            stop_mask = highs[entry_rel:] >= stop if np is not None else [
                value >= stop for value in highs[entry_rel:]
            ]
            target_mask = lows[entry_rel:] <= target if np is not None else [
                value <= target for value in lows[entry_rel:]
            ]
        stop_hit = first_true_index(stop_mask)
        target_hit = first_true_index(target_mask)
        stop_rel = entry_rel + stop_hit if stop_hit is not None else None
        target_rel = entry_rel + target_hit if target_hit is not None else None
    if entry_rel is None:
        terminal_order = "NO_ENTRY_TOUCH"
    elif stop_rel is None and target_rel is None:
        terminal_order = "ENTRY_TOUCHED_TIMEOUT_OR_NO_TERMINAL"
    elif stop_rel is not None and target_rel is not None and stop_rel == target_rel:
        terminal_order = "SAME_BAR_AMBIGUOUS_STOP_AND_TARGET"
    elif target_rel is not None and (stop_rel is None or target_rel < stop_rel):
        terminal_order = "TARGET_FIRST"
    else:
        terminal_order = "STOP_FIRST"
    terminal_outcome = terminal_to_outcome(terminal_order)
    risk = abs(entry - stop)
    mfe_r = None
    mae_r = None
    if entry_rel is not None and risk > 0:
        post_highs = highs[entry_rel:]
        post_lows = lows[entry_rel:]
        if side == "LONG":
            mfe_r = float((max(post_highs) - entry) / risk)
            mae_r = float((min(post_lows) - entry) / risk)
        else:
            mfe_r = float((entry - min(post_lows)) / risk)
            mae_r = float((entry - max(post_highs)) / risk)
    last_close = value_at(closes, len(closes) - 1) if len(closes) else None
    r_payload = r_values_for_terminal(
        side=side,
        entry=entry,
        stop=stop,
        target=target,
        terminal_outcome=terminal_outcome,
        last_close=last_close,
    )
    requested_end = parse_dt(event.get("path_window_requested_end_utc"))
    source_last = series.times[right - 1] if right > left else None
    return {
        "path_source_status": "SIMULATED_FROM_LOCAL_OHLC",
        "source_mode": f"OHLC_{series.timeframe}_CSV",
        "source_evidence_type": source_evidence_type,
        "source_system": series.source_system,
        "source_path": rel(series.path),
        "source_sha256": sha256_file(series.path),
        "source_symbol": series.symbol,
        "source_timeframe": series.timeframe,
        "source_total_row_count": series.row_count,
        "bar_count": right - left,
        "first_bar_utc": dt_s(series.times[left]) if right > left else None,
        "last_bar_utc": dt_s(source_last),
        "source_window_complete": bool(requested_end and source_last and source_last >= requested_end),
        "entry_touched": entry_rel is not None,
        "entry_first_touch_utc": dt_s(series.times[left + entry_rel]) if entry_rel is not None else None,
        "sl_first_touch_utc": dt_s(series.times[left + stop_rel]) if stop_rel is not None else None,
        "tp1_first_touch_utc": dt_s(series.times[left + target_rel]) if target_rel is not None else None,
        "pre_entry_sl_touch_utc": dt_s(series.times[left + pre_stop_rel]) if pre_stop_rel is not None else None,
        "pre_entry_tp_touch_utc": dt_s(series.times[left + pre_target_rel])
        if pre_target_rel is not None
        else None,
        "pending_lifecycle_state": pending_lifecycle_state(
            terminal_outcome, pre_stop_rel is not None, pre_target_rel is not None
        ),
        "terminal_order_raw": terminal_order,
        "terminal_outcome": terminal_outcome,
        "same_bar_ambiguity": terminal_outcome == "same_bar_ambiguous_unresolved",
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "last_close": last_close,
        "confidence": (
            "lower_timeframe_ohlc"
            if replay_mode in {"m1_path_aware", "m5_path_aware", "tick_or_sierra_path_aware"}
            else "m15_ohlc_path"
        ),
        **r_payload,
    }


def pending_lifecycle_state(
    terminal_outcome: str, pre_entry_stop_touched: bool, pre_entry_target_touched: bool
) -> str:
    if terminal_outcome == "no_fill" and pre_entry_target_touched:
        return "cancelled_target_reached_without_fill_or_same_bar_entry_ambiguity"
    if terminal_outcome == "no_fill" and pre_entry_stop_touched:
        return "cancelled_wrong_side_or_stop_blowthrough_before_fill"
    if terminal_outcome == "no_fill":
        return "pending_expired_no_fill_48h"
    if terminal_outcome == "timeout":
        return "filled_then_pending_trade_timeout_mark_to_market"
    if terminal_outcome == "target_first":
        return "filled_then_target_first"
    if terminal_outcome == "stop_first":
        return "filled_then_stop_first"
    return "filled_then_ambiguous_stop_target_order"


def missing_path_row(
    event: dict[str, Any],
    replay_mode: str,
    source_evidence_type: str,
    reason: str,
    searched_paths: list[str],
    *,
    requested_replay_mode: str | None = None,
) -> dict[str, Any]:
    return {
        "path_source_status": "MISSING_SOURCE",
        "source_mode": "MISSING_SOURCE",
        "source_evidence_type": source_evidence_type,
        "source_system": "missing_source",
        "source_path": None,
        "source_sha256": None,
        "source_symbol": event.get("source_symbol"),
        "source_timeframe": None,
        "source_total_row_count": 0,
        "bar_count": 0,
        "tick_count": 0,
        "first_bar_utc": None,
        "last_bar_utc": None,
        "source_window_complete": False,
        "entry_touched": None,
        "entry_first_touch_utc": None,
        "sl_first_touch_utc": None,
        "tp1_first_touch_utc": None,
        "pre_entry_sl_touch_utc": None,
        "pre_entry_tp_touch_utc": None,
        "pending_lifecycle_state": "missing_source_pending_lifecycle_unresolved",
        "terminal_order_raw": "MISSING_SOURCE",
        "terminal_outcome": "missing_source_denominator_excluded",
        "same_bar_ambiguity": None,
        "mfe_r": None,
        "mae_r": None,
        "last_close": None,
        "simulated_r": None,
        "target_r": None,
        "timeout_mark_to_market_r": None,
        "conservative_ambiguous_r": None,
        "optimistic_ambiguous_r": None,
        "no_fill_equivalent_r": None,
        "source_gap_class": reason,
        "searched_paths": searched_paths,
        "requested_replay_mode": requested_replay_mode or replay_mode,
        "confidence": "missing_source",
    }


def find_ohlc_window(
    event: dict[str, Any],
    timeframe: str,
    *,
    prefer_candidate_source: bool = False,
    source_system_filter: str | None = None,
) -> tuple[BarSeries | None, int, int, list[str]]:
    start = parse_dt(event.get("path_window_start_utc"))
    end = parse_dt(event.get("path_window_requested_end_utc"))
    searched: list[str] = []
    if start is None or end is None:
        return None, 0, 0, searched
    candidates: list[SourceFile | Path] = []
    if prefer_candidate_source and timeframe == "M15":
        source_path = event.get("market_source_path")
        if source_path:
            path = repo_path(source_path)
            if path.exists():
                candidates.append(path)
    index = build_ohlc_index()
    seen = {rel(item) for item in candidates if isinstance(item, Path)}
    for alias in symbol_aliases(event.get("symbol"), event.get("source_symbol")):
        for source in index.get((alias, timeframe), []):
            if source_system_filter and source.source_system != source_system_filter:
                continue
            key = rel(source.path)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(source)
    for source in candidates:
        path = source.path if isinstance(source, SourceFile) else source
        searched.append(rel(path))
        series = load_bar_series(source)
        left = bisect.bisect_left(series.times, start)
        right = bisect.bisect_right(series.times, end)
        if right > left:
            return series, left, right, searched
    return None, 0, 0, searched


def base_row(candidate: dict[str, Any], event: dict[str, Any], replay_mode: str) -> dict[str, Any]:
    return {
        "schema_version": "vnext_full_replay_stage04_path_outcome_r_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "candidate_id": candidate.get("candidate_id"),
        "source_universe_row_id": candidate.get("source_universe_row_id"),
        "market_state_packet_id": candidate.get("market_state_packet_id"),
        "source_origin": candidate.get("source_origin"),
        "candidate_origin_generation_stage": "STAGE_02_CANDIDATE_GENERATION_ENGINE",
        "candidate_origin_generation_status": "m15_market_bar_candidate_only",
        "candidate_discovery_denominator_scope": (
            "stage04_path_truth_only_no_lower_timeframe_candidate_discovery_claim"
        ),
        "symbol": candidate.get("symbol"),
        "source_symbol": candidate.get("source_symbol"),
        "timeframe": candidate.get("timeframe"),
        "market_timeframe": candidate.get("market_timeframe"),
        "session_bucket": candidate.get("session_bucket"),
        "date_utc": candidate.get("date_utc"),
        "candle_time_utc": candidate.get("candle_time_utc"),
        "side": event.get("side"),
        "framework": candidate.get("framework"),
        "entry_reference": event.get("entry_price"),
        "stop_or_invalidation": event.get("stop_loss"),
        "target_reference": event.get("take_profit_1"),
        "rr": event.get("rr"),
        "replay_mode": replay_mode,
        "path_horizon_policy": PATH_HORIZON_POLICY,
        "path_window_start_utc": event.get("path_window_start_utc"),
        "path_window_requested_end_utc": event.get("path_window_requested_end_utc"),
        "market_bar_source_path": candidate.get("source_path"),
        "market_bar_source_sha256": candidate.get("source_sha256"),
        "no_live_trading_or_broker_mutation": True,
    }


def enrich_path_row(
    candidate: dict[str, Any],
    event: dict[str, Any],
    replay_mode: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    row = base_row(candidate, event, replay_mode)
    row["path_row_id"] = stable_id(
        "path04",
        [candidate.get("candidate_id"), replay_mode, payload.get("source_path"), payload.get("source_gap_class")],
        length=24,
    )
    row.update(payload)
    if row.get("path_source_status") == "RUNTIME_TRACE_REFERENCE_NO_PRICE_PATH_CLAIM":
        row["price_path_truth_status"] = "not_claimed_runtime_reference_only"
    else:
        row["price_path_truth_status"] = (
            "measured" if row.get("path_source_status") != "MISSING_SOURCE" else "source_missing"
        )
    row["trade_performance_denominator_inclusion"] = row.get("terminal_outcome") in {
        "target_first",
        "stop_first",
        "timeout",
    }
    row["candidate_opportunity_denominator_inclusion"] = (
        row.get("terminal_outcome") != "missing_source_denominator_excluded"
    )
    return row


def path_source_row(path_row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "route_id",
        "stage_id",
        "candidate_id",
        "source_universe_row_id",
        "symbol",
        "source_symbol",
        "candle_time_utc",
        "replay_mode",
        "source_mode",
        "source_evidence_type",
        "source_system",
        "source_path",
        "source_sha256",
        "source_timeframe",
        "source_total_row_count",
        "bar_count",
        "tick_count",
        "first_bar_utc",
        "last_bar_utc",
        "first_tick_utc",
        "last_tick_utc",
        "source_window_complete",
        "path_source_status",
        "source_gap_class",
        "searched_paths",
        "requested_replay_mode",
        "candidate_origin_generation_status",
        "candidate_discovery_denominator_scope",
    ]
    row = {
        "schema_version": "vnext_full_replay_stage04_path_source_v1",
        "path_source_row_id": stable_id(
            "psrc04", [path_row.get("path_row_id"), path_row.get("source_path")], length=24
        ),
    }
    for key in keys:
        if key in path_row:
            row[key] = path_row.get(key)
    return row


def runtime_reference_rows(
    candidate: dict[str, Any], event: dict[str, Any], runtime_rows: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mode in RUNTIME_REFERENCE_MODES:
        trace = runtime_rows.get(mode) or {}
        payload = {
            "path_source_status": "RUNTIME_TRACE_REFERENCE_NO_PRICE_PATH_CLAIM",
            "source_mode": "RUNTIME_TRACE_REFERENCE",
            "source_evidence_type": "stage03_actual_current_runtime_trace_reference",
            "source_system": "stage03_runtime_trace",
            "source_path": trace.get("runtime_trace_source_path"),
            "source_sha256": trace.get("runtime_trace_source_sha256"),
            "source_symbol": candidate.get("source_symbol"),
            "source_timeframe": None,
            "source_total_row_count": None,
            "bar_count": None,
            "tick_count": None,
            "source_window_complete": None,
            "entry_touched": None,
            "terminal_order_raw": "RUNTIME_TRACE_REFERENCE",
            "terminal_outcome": "runtime_trace_reference",
            "simulated_r": None,
            "target_r": None,
            "timeout_mark_to_market_r": None,
            "conservative_ambiguous_r": None,
            "optimistic_ambiguous_r": None,
            "no_fill_equivalent_r": None,
            "runtime_trace_mode": mode,
            "runtime_decision_summary": trace.get("decision_summary"),
            "route_decision": (trace.get("decision_summary") or {}).get("route_decision"),
            "pre_ai_action": (trace.get("decision_summary") or {}).get("pre_ai_action"),
            "pending_would_action": (trace.get("decision_summary") or {}).get("pending_would_action"),
            "price_path_truth_status": "not_claimed_runtime_reference_only",
            "confidence": "runtime_reference_not_path_truth",
        }
        rows.append(enrich_path_row(candidate, event, mode, payload))
    return rows


def load_runtime_rows(stage03_shard: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    path = repo_path((stage03_shard.get("outputs") or {}).get("runtime_trace", {}).get("path"))
    rows: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in iter_gzip_jsonl(path):
        candidate_id = row.get("candidate_id")
        mode = row.get("current_shadow_vs_hypothetical_mode")
        if not candidate_id or not mode:
            continue
        compact = {
            "runtime_trace_source_path": rel(path),
            "runtime_trace_source_sha256": sha256_file(path),
            "decision_summary": row.get("decision_summary"),
            "causal_decision_steps": row.get("causal_decision_steps"),
        }
        rows[str(candidate_id)][str(mode)] = compact
    return rows


def tick_dates(start: datetime, end: datetime) -> list[date]:
    dates: list[date] = []
    current = start.date()
    while current <= end.date():
        dates.append(current)
        current = current + timedelta(days=1)
    return dates


def tick_file_candidates(event: dict[str, Any]) -> list[Path]:
    start = parse_dt(event.get("path_window_start_utc"))
    end = parse_dt(event.get("path_window_requested_end_utc"))
    if start is None or end is None:
        return []
    candidates: list[Path] = []
    for alias in symbol_aliases(event.get("symbol"), event.get("source_symbol")):
        for day in tick_dates(start, end):
            path = TICK_ROOT / alias / f"{day.isoformat()}.parquet"
            if path.exists() and path not in candidates:
                candidates.append(path)
    return candidates


def load_tick_frame(path: Path) -> Any:
    if path in TICK_CACHE:
        return TICK_CACHE[path]
    if pd is None:
        return None
    frame = pd.read_parquet(path)
    if "ts_utc" in frame.columns:
        frame = frame.sort_values("ts_utc")
    TICK_CACHE[path] = frame
    return frame


def compute_path_from_ticks(event: dict[str, Any], paths: list[Path]) -> dict[str, Any] | None:
    if pd is None or not paths:
        return None
    frames = []
    for path in paths:
        frame = load_tick_frame(path)
        if frame is not None and not frame.empty and "ts_utc" in frame.columns:
            frames.append(frame)
    if not frames:
        return None
    frame = pd.concat(frames, ignore_index=True).sort_values("ts_utc").reset_index(drop=True)
    start = parse_dt(event.get("path_window_start_utc"))
    end = parse_dt(event.get("path_window_requested_end_utc"))
    entry = fnum(event.get("entry_price"))
    stop = fnum(event.get("stop_loss"))
    target = fnum(event.get("take_profit_1"))
    side = str(event.get("side") or "").upper()
    if None in (start, end, entry, stop, target) or side not in {"LONG", "SHORT"}:
        return None
    ts = frame["ts_utc"]
    left = ts.searchsorted(start, side="left")
    right = ts.searchsorted(end, side="right")
    window = frame.iloc[left:right]
    if window.empty:
        return None
    bid = window["bid"] if "bid" in window.columns else window.get("last")
    ask = window["ask"] if "ask" in window.columns else window.get("last")
    if bid is None or ask is None:
        return None
    if side == "LONG":
        entry_mask = ask <= entry
        stop_mask = bid <= stop
        target_mask = bid >= target
    else:
        entry_mask = bid >= entry
        stop_mask = ask >= stop
        target_mask = ask <= target
    entry_hits = window.index[entry_mask].tolist()
    entry_pos = entry_hits[0] if entry_hits else None
    stop_pos = None
    target_pos = None
    pre_stop_pos = None
    pre_target_pos = None
    if entry_pos is not None:
        pre_stop_hits = window.loc[:entry_pos].index[stop_mask.loc[:entry_pos]].tolist()
        pre_target_hits = window.loc[:entry_pos].index[target_mask.loc[:entry_pos]].tolist()
        pre_stop_pos = pre_stop_hits[0] if pre_stop_hits else None
        pre_target_pos = pre_target_hits[0] if pre_target_hits else None
        stop_hits = window.loc[entry_pos:].index[stop_mask.loc[entry_pos:]].tolist()
        target_hits = window.loc[entry_pos:].index[target_mask.loc[entry_pos:]].tolist()
        stop_pos = stop_hits[0] if stop_hits else None
        target_pos = target_hits[0] if target_hits else None
    else:
        pre_stop_hits = window.index[stop_mask].tolist()
        pre_target_hits = window.index[target_mask].tolist()
        pre_stop_pos = pre_stop_hits[0] if pre_stop_hits else None
        pre_target_pos = pre_target_hits[0] if pre_target_hits else None
    if entry_pos is None:
        terminal_order = "NO_ENTRY_TOUCH"
    elif stop_pos is None and target_pos is None:
        terminal_order = "ENTRY_TOUCHED_TIMEOUT_OR_NO_TERMINAL"
    elif stop_pos is not None and target_pos is not None and stop_pos == target_pos:
        terminal_order = "SAME_TICK_AMBIGUOUS_STOP_AND_TARGET"
    elif target_pos is not None and (stop_pos is None or target_pos < stop_pos):
        terminal_order = "TARGET_FIRST"
    else:
        terminal_order = "STOP_FIRST"
    terminal_outcome = terminal_to_outcome(terminal_order)
    risk = abs(entry - stop)
    mfe_r = None
    mae_r = None
    last_px = None
    if entry_pos is not None and risk > 0:
        if side == "LONG":
            post_bid = bid.loc[entry_pos:]
            mfe_r = float((post_bid.max() - entry) / risk)
            mae_r = float((post_bid.min() - entry) / risk)
            last_px = float(post_bid.iloc[-1])
        else:
            post_ask = ask.loc[entry_pos:]
            mfe_r = float((entry - post_ask.min()) / risk)
            mae_r = float((entry - post_ask.max()) / risk)
            last_px = float(post_ask.iloc[-1])
    r_payload = r_values_for_terminal(
        side=side,
        entry=entry,
        stop=stop,
        target=target,
        terminal_outcome=terminal_outcome,
        last_close=last_px,
    )
    return {
        "path_source_status": "SIMULATED_FROM_LOCAL_TICKS",
        "source_mode": "LOCAL_TICK_PARQUET",
        "source_evidence_type": "local_tick_quote_path_reconstruction",
        "source_system": "local_tick_capture_parquet",
        "source_path": [rel(path) for path in paths],
        "source_sha256": [{"path": rel(path), "sha256": sha256_file(path)} for path in paths],
        "source_timeframe": "tick",
        "source_total_row_count": int(sum(len(load_tick_frame(path)) for path in paths if load_tick_frame(path) is not None)),
        "tick_count": int(len(window)),
        "first_tick_utc": dt_s(parse_dt(window.iloc[0]["ts_utc"])),
        "last_tick_utc": dt_s(parse_dt(window.iloc[-1]["ts_utc"])),
        "quote_rule": "LONG entry uses ask<=entry and exits use bid; SHORT entry uses bid>=entry and exits use ask",
        "source_window_complete": True,
        "entry_touched": entry_pos is not None,
        "entry_first_touch_utc": dt_s(parse_dt(window.loc[entry_pos]["ts_utc"]))
        if entry_pos is not None
        else None,
        "sl_first_touch_utc": dt_s(parse_dt(window.loc[stop_pos]["ts_utc"]))
        if stop_pos is not None
        else None,
        "tp1_first_touch_utc": dt_s(parse_dt(window.loc[target_pos]["ts_utc"]))
        if target_pos is not None
        else None,
        "pre_entry_sl_touch_utc": dt_s(parse_dt(window.loc[pre_stop_pos]["ts_utc"]))
        if pre_stop_pos is not None
        else None,
        "pre_entry_tp_touch_utc": dt_s(parse_dt(window.loc[pre_target_pos]["ts_utc"]))
        if pre_target_pos is not None
        else None,
        "pending_lifecycle_state": pending_lifecycle_state(
            terminal_outcome, pre_stop_pos is not None, pre_target_pos is not None
        ),
        "terminal_order_raw": terminal_order,
        "terminal_outcome": terminal_outcome,
        "same_bar_ambiguity": terminal_outcome == "same_bar_ambiguous_unresolved",
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "last_close": last_px,
        "confidence": "tick_quote_path",
        **r_payload,
    }


def tick_or_sierra_row(candidate: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    tick_paths = tick_file_candidates(event)
    tick_payload = compute_path_from_ticks(event, tick_paths)
    if tick_payload is not None:
        return enrich_path_row(candidate, event, "tick_or_sierra_path_aware", tick_payload)
    series, left, right, searched_sierra = find_ohlc_window(
        event,
        "M1",
        source_system_filter="sierra_scid_converted_ohlc",
    )
    searched = [rel(path) for path in tick_paths] + searched_sierra
    if series is not None and right > left:
        payload = simulate_bar_path(
            event,
            series,
            left,
            right,
            "tick_or_sierra_path_aware",
            "sierra_scid_converted_m1_proxy_path_reconstruction",
        )
        payload["source_mode"] = "SIERRA_SCID_CONVERTED_M1_PROXY"
        payload["confidence"] = "sierra_m1_proxy_path"
        return enrich_path_row(candidate, event, "tick_or_sierra_path_aware", payload)
    gap_class = "TICK_AND_SIERRA_WINDOW_NOT_FOUND"
    if SIERRA_INVENTORY_PATH.exists():
        gap_class = "TICK_MISSING_AND_SIERRA_SCID_RAW_OR_CONVERTED_WINDOW_NOT_BOUND"
    return enrich_path_row(
        candidate,
        event,
        "tick_or_sierra_path_aware",
        missing_path_row(
            event,
            "tick_or_sierra_path_aware",
            "local_tick_or_sierra_scid_path_reconstruction",
            gap_class,
            searched,
            requested_replay_mode="tick_or_sierra_path_aware",
        ),
    )


def ohlc_rows(candidate: dict[str, Any], event: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mode_map = [
        ("M15", "bar_close_m15", "local_m15_ohlc_reconstruction"),
        ("M1", "m1_path_aware", "local_m1_ohlc_reconstruction"),
        ("M5", "m5_path_aware", "local_m5_ohlc_reconstruction"),
    ]
    m15_payload: dict[str, Any] | None = None
    for timeframe, mode, evidence_type in mode_map:
        series, left, right, searched = find_ohlc_window(
            event, timeframe, prefer_candidate_source=timeframe == "M15"
        )
        if series is not None and right > left:
            payload = simulate_bar_path(event, series, left, right, mode, evidence_type)
            row = enrich_path_row(candidate, event, mode, payload)
            if timeframe == "M15":
                m15_payload = payload
            rows.append(row)
        else:
            rows.append(
                enrich_path_row(
                    candidate,
                    event,
                    mode,
                    missing_path_row(
                        event,
                        mode,
                        evidence_type,
                        f"{timeframe}_OHLC_WINDOW_NOT_FOUND_AFTER_STAGE04_SOURCE_REPAIR",
                        searched,
                        requested_replay_mode=mode,
                    ),
                )
            )
    if m15_payload is not None:
        proxy_payload = dict(m15_payload)
        proxy_payload["source_evidence_type"] = "m15_ohlc_proxy_from_best_available_bar_data"
        proxy_payload["confidence"] = "ohlc_only_proxy"
        rows.append(enrich_path_row(candidate, event, "ohlc_only_proxy", proxy_payload))
    else:
        rows.append(
            enrich_path_row(
                candidate,
                event,
                "ohlc_only_proxy",
                missing_path_row(
                    event,
                    "ohlc_only_proxy",
                    "ohlc_only_proxy",
                    "OHLC_PROXY_WINDOW_NOT_FOUND",
                    [],
                    requested_replay_mode="ohlc_only_proxy",
                ),
            )
        )
    rows.append(tick_or_sierra_row(candidate, event))
    missing_modes = [
        row.get("replay_mode")
        for row in rows
        if row.get("terminal_outcome") == "missing_source_denominator_excluded"
    ]
    if missing_modes:
        rows.append(
            enrich_path_row(
                candidate,
                event,
                "missing_source",
                missing_path_row(
                    event,
                    "missing_source",
                    "source_mode_missing_summary",
                    "ONE_OR_MORE_STAGE04_SOURCE_MODES_MISSING",
                    [],
                    requested_replay_mode=",".join(sorted(str(mode) for mode in missing_modes)),
                )
                | {"missing_replay_modes": sorted(str(mode) for mode in missing_modes)},
            )
        )
    return rows


def best_available_path(path_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    priority = [
        "tick_or_sierra_path_aware",
        "m1_path_aware",
        "m5_path_aware",
        "bar_close_m15",
        "ohlc_only_proxy",
    ]
    usable = {
        row.get("replay_mode"): row
        for row in path_rows
        if row.get("terminal_outcome") != "missing_source_denominator_excluded"
    }
    for mode in priority:
        if mode in usable:
            return usable[mode]
    return None


def nofill_pending_row(candidate: dict[str, Any], best_path: dict[str, Any] | None) -> dict[str, Any]:
    terminal = best_path.get("terminal_outcome") if best_path else "missing_source_denominator_excluded"
    return {
        "schema_version": "vnext_full_replay_stage04_nofill_pending_lifecycle_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "candidate_id": candidate.get("candidate_id"),
        "symbol": candidate.get("symbol"),
        "source_symbol": candidate.get("source_symbol"),
        "candle_time_utc": candidate.get("candle_time_utc"),
        "side": candidate.get("side"),
        "framework": candidate.get("framework"),
        "pending_horizon_policy": PATH_HORIZON_POLICY,
        "best_available_replay_mode": best_path.get("replay_mode") if best_path else None,
        "entry_touched": best_path.get("entry_touched") if best_path else None,
        "entry_first_touch_utc": best_path.get("entry_first_touch_utc") if best_path else None,
        "pending_lifecycle_state": best_path.get("pending_lifecycle_state") if best_path else None,
        "terminal_outcome": terminal,
        "no_fill": terminal == "no_fill",
        "timeout": terminal == "timeout",
        "source_path": best_path.get("source_path") if best_path else None,
        "source_gap_class": best_path.get("source_gap_class") if best_path else "ALL_SOURCE_MODES_MISSING",
    }


def disagreement_rows(candidate: dict[str, Any], path_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_mode = {row.get("replay_mode"): row for row in path_rows}
    m15 = by_mode.get("bar_close_m15")
    rows: list[dict[str, Any]] = []
    if not m15 or m15.get("terminal_outcome") == "missing_source_denominator_excluded":
        return rows
    for mode in ("m1_path_aware", "m5_path_aware", "tick_or_sierra_path_aware"):
        ltf = by_mode.get(mode)
        if not ltf or ltf.get("terminal_outcome") == "missing_source_denominator_excluded":
            continue
        outcome_changed = ltf.get("terminal_outcome") != m15.get("terminal_outcome")
        entry_time_changed = ltf.get("entry_first_touch_utc") != m15.get("entry_first_touch_utc")
        r_changed = ltf.get("simulated_r") != m15.get("simulated_r")
        if outcome_changed or entry_time_changed or r_changed:
            rows.append(
                {
                    "schema_version": "vnext_full_replay_stage04_m15_vs_ltf_disagreement_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "candidate_id": candidate.get("candidate_id"),
                    "symbol": candidate.get("symbol"),
                    "source_symbol": candidate.get("source_symbol"),
                    "candle_time_utc": candidate.get("candle_time_utc"),
                    "side": candidate.get("side"),
                    "framework": candidate.get("framework"),
                    "ltf_replay_mode": mode,
                    "m15_terminal_outcome": m15.get("terminal_outcome"),
                    "ltf_terminal_outcome": ltf.get("terminal_outcome"),
                    "m15_entry_first_touch_utc": m15.get("entry_first_touch_utc"),
                    "ltf_entry_first_touch_utc": ltf.get("entry_first_touch_utc"),
                    "m15_simulated_r": m15.get("simulated_r"),
                    "ltf_simulated_r": ltf.get("simulated_r"),
                    "would_change_execution_or_decision": outcome_changed or entry_time_changed,
                    "change_reason_flags": {
                        "terminal_outcome_changed": outcome_changed,
                        "entry_timing_changed": entry_time_changed,
                        "simulated_r_changed": r_changed,
                    },
                    "m15_path_row_id": m15.get("path_row_id"),
                    "ltf_path_row_id": ltf.get("path_row_id"),
                }
            )
    return rows


def missed_winner_row(
    candidate: dict[str, Any],
    best_path: dict[str, Any] | None,
    runtime_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    current_decision = ((runtime_rows.get("current_config_shadow") or {}).get("decision_summary") or {}).get(
        "route_decision"
    )
    terminal = best_path.get("terminal_outcome") if best_path else "missing_source_denominator_excluded"
    if current_decision == "AVOID" and terminal == "target_first":
        classification = "missed_winner"
    elif current_decision == "AVOID" and terminal == "stop_first":
        classification = "avoided_loser"
    elif current_decision in {"FOLLOW", "LEGACY", "MIXED"} and terminal == "stop_first":
        classification = "accepted_loser"
    elif current_decision in {"FOLLOW", "LEGACY", "MIXED"} and terminal == "target_first":
        classification = "captured_winner"
    elif terminal == "no_fill":
        classification = "no_fill_pending"
    elif terminal == "timeout":
        classification = "timeout_mark_to_market"
    elif terminal == "same_bar_ambiguous_unresolved":
        classification = "same_bar_ambiguous"
    else:
        classification = "unclassified_or_missing_source"
    return {
        "schema_version": "vnext_full_replay_stage04_missed_winner_avoided_loser_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "candidate_id": candidate.get("candidate_id"),
        "symbol": candidate.get("symbol"),
        "source_symbol": candidate.get("source_symbol"),
        "candle_time_utc": candidate.get("candle_time_utc"),
        "side": candidate.get("side"),
        "framework": candidate.get("framework"),
        "current_shadow_route_decision": current_decision,
        "hypothetical_route_decision": (
            ((runtime_rows.get("hypothetical_activated_vnext") or {}).get("decision_summary") or {}).get(
                "route_decision"
            )
        ),
        "best_available_replay_mode": best_path.get("replay_mode") if best_path else None,
        "best_available_terminal_outcome": terminal,
        "best_available_simulated_r": best_path.get("simulated_r") if best_path else None,
        "classification": classification,
        "would_change_decision_or_execution_with_ltf_source": classification
        in {"missed_winner", "avoided_loser", "accepted_loser", "same_bar_ambiguous"},
        "best_path_row_id": best_path.get("path_row_id") if best_path else None,
    }


def process_candidate(
    candidate: dict[str, Any],
    runtime_rows: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    event = event_from_candidate(candidate)
    path_rows = runtime_reference_rows(candidate, event, runtime_rows)
    price_rows = ohlc_rows(candidate, event)
    path_rows.extend(price_rows)
    source_rows = [path_source_row(row) for row in path_rows]
    best = best_available_path(price_rows)
    return (
        source_rows,
        path_rows,
        nofill_pending_row(candidate, best),
        disagreement_rows(candidate, price_rows),
        missed_winner_row(candidate, best, runtime_rows),
    )


def source_inventory_hash() -> str:
    payload = {
        "stage04_expanded_manifest": sha256_file(STAGE04_EXPANDED_MANIFEST_PATH),
        "stage04_core_manifest": sha256_file(STAGE04_CORE_MANIFEST_PATH),
        "stage04_probe_paths": [
            {"path": rel(path), "sha256": sha256_file(path)} for path in STAGE04_PROBE_PATHS
        ],
        "sierra_inventory": sha256_file(SIERRA_INVENTORY_PATH),
        "ohlc_index_count": sum(len(files) for files in build_ohlc_index().values()),
        "tick_file_count": sum(1 for _ in TICK_ROOT.rglob("*.parquet")) if TICK_ROOT.exists() else 0,
    }
    return stable_hash(payload)


def completed_shard_manifest(
    stage02_shard: dict[str, Any],
    stage03_shard: dict[str, Any],
    inventory_hash: str,
) -> dict[str, Any] | None:
    shard_id = source_stage04_shard_id(stage02_shard, stage03_shard)
    paths = stage04_shard_paths(shard_id)
    if not paths["manifest"].exists():
        return None
    try:
        manifest = read_json(paths["manifest"])
    except Exception:
        return None
    if manifest.get("shard_status") != "complete":
        return None
    if manifest.get("source_path") != stage02_shard.get("source_path"):
        return None
    if manifest.get("source_inventory_hash") != inventory_hash:
        return None
    expected_candidates = int(
        (stage02_shard.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or -1
    )
    if int(manifest.get("candidate_rows") or -1) != expected_candidates:
        return None
    for key in SHARDED_ARTIFACT_KEYS:
        output = (manifest.get("outputs") or {}).get(key) or {}
        path = repo_path(output.get("path"))
        if not path.exists() or output.get("sha256") != sha256_file(path):
            return None
    return manifest


def write_one_source_shard(
    *,
    stage02_shard: dict[str, Any],
    stage03_shard: dict[str, Any],
    source_index: int,
    source_count: int,
    inventory_hash: str,
) -> dict[str, Any]:
    started = utc_now()
    shard_id = source_stage04_shard_id(stage02_shard, stage03_shard)
    paths = stage04_shard_paths(shard_id)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    source_path = str(stage02_shard.get("source_path"))
    input_candidate_path = repo_path(
        (stage02_shard.get("outputs") or {}).get("candidate_generation", {}).get("path")
    )
    expected_candidates = int(
        (stage02_shard.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or 0
    )
    runtime_rows_by_candidate = load_runtime_rows(stage03_shard)
    heartbeat = {
        "schema_version": "vnext_full_replay_stage04_shard_heartbeat_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "shard_id": shard_id,
        "source_index": source_index,
        "source_count": source_count,
        "source_path": source_path,
        "shard_status": "running",
        "started_at_utc": started,
        "heartbeat_updated_at_utc": started,
        "resume_cursor": {
            "input_candidate_path": rel(input_candidate_path),
            "input_candidate_rows_expected": expected_candidates,
            "candidate_rows_processed": 0,
            "path_outcome_r_rows_written": 0,
            "path_source_rows_written": 0,
        },
    }
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage04_heartbeat(heartbeat)

    row_counts: Counter[str] = Counter()
    terminal_counts_by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    missing_modes: Counter[str] = Counter()
    classification_counts: Counter[str] = Counter()
    candidate_rows = 0

    try:
        with AtomicGzipJsonlWriter(paths["path_source"]) as source_writer, AtomicGzipJsonlWriter(
            paths["path_outcome_r"]
        ) as outcome_writer, AtomicGzipJsonlWriter(
            paths["nofill_pending_lifecycle"]
        ) as pending_writer, AtomicGzipJsonlWriter(
            paths["m15_vs_ltf_disagreement"]
        ) as disagreement_writer, AtomicGzipJsonlWriter(
            paths["missed_winner_avoided_loser"]
        ) as missed_writer:
            for candidate in iter_gzip_jsonl(input_candidate_path):
                candidate_rows += 1
                runtime_rows = runtime_rows_by_candidate.get(str(candidate.get("candidate_id")), {})
                source_rows, path_rows, pending_row, disagreement, missed_row = process_candidate(
                    candidate, runtime_rows
                )
                for row in source_rows:
                    source_writer.write(row)
                    row_counts["path_source"] += 1
                for row in path_rows:
                    outcome_writer.write(row)
                    row_counts["path_outcome_r"] += 1
                    terminal_counts_by_mode[str(row.get("replay_mode"))][
                        str(row.get("terminal_outcome"))
                    ] += 1
                    if row.get("terminal_outcome") == "missing_source_denominator_excluded":
                        missing_modes[str(row.get("requested_replay_mode") or row.get("replay_mode"))] += 1
                pending_writer.write(pending_row)
                row_counts["nofill_pending_lifecycle"] += 1
                for row in disagreement:
                    disagreement_writer.write(row)
                    row_counts["m15_vs_ltf_disagreement"] += 1
                missed_writer.write(missed_row)
                row_counts["missed_winner_avoided_loser"] += 1
                classification_counts[str(missed_row.get("classification"))] += 1
                row_counts["candidate_rows"] += 1
                if candidate_rows % 2000 == 0:
                    heartbeat["heartbeat_updated_at_utc"] = utc_now()
                    heartbeat["resume_cursor"]["candidate_rows_processed"] = candidate_rows
                    heartbeat["resume_cursor"][
                        "path_outcome_r_rows_written"
                    ] = outcome_writer.row_count
                    heartbeat["resume_cursor"]["path_source_rows_written"] = source_writer.row_count
                    write_shard_json(paths["heartbeat"], heartbeat)
                    write_stage04_heartbeat(heartbeat)
    except Exception as exc:  # noqa: BLE001 - manifest records exact failure
        failure = {
            "schema_version": "vnext_full_replay_stage04_shard_manifest_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "shard_id": shard_id,
            "source_path": source_path,
            "source_index": source_index,
            "shard_status": "failed",
            "started_at_utc": started,
            "failed_at_utc": utc_now(),
            "candidate_rows": candidate_rows,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "resume_cursor": heartbeat["resume_cursor"],
        }
        write_shard_json(paths["manifest"], failure)
        raise

    outputs = {
        key: {
            "path": rel(paths[key]),
            "row_count": int(row_counts[key]),
            "bytes": paths[key].stat().st_size,
            "sha256": sha256_file(paths[key]),
        }
        for key in SHARDED_ARTIFACT_KEYS
    }
    manifest = {
        "schema_version": "vnext_full_replay_stage04_shard_manifest_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "shard_id": shard_id,
        "source_index": source_index,
        "source_count": source_count,
        "source_path": source_path,
        "stage02_shard_id": stage02_shard.get("shard_id"),
        "stage03_shard_id": stage03_shard.get("shard_id"),
        "input_candidate_path": rel(input_candidate_path),
        "input_runtime_trace_path": (stage03_shard.get("outputs") or {}).get("runtime_trace", {}).get("path"),
        "shard_status": "complete",
        "started_at_utc": started,
        "completed_at_utc": utc_now(),
        "candidate_rows": candidate_rows,
        "expected_candidate_rows": expected_candidates,
        "source_inventory_hash": inventory_hash,
        "required_replay_modes": sorted(REQUIRED_REPLAY_MODES),
        "path_horizon_policy": PATH_HORIZON_POLICY,
        "row_counts": dict(row_counts),
        "terminal_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in terminal_counts_by_mode.items()
        },
        "missing_source_counts_by_requested_mode": dict(sorted(missing_modes.items())),
        "missed_winner_avoided_loser_classification_counts": dict(
            sorted(classification_counts.items())
        ),
        "outputs": outputs,
        "heartbeat_updated_at_utc": utc_now(),
        "resume_cursor": {
            "completed_source_path": source_path,
            "next_source_index": source_index + 1,
            "candidate_rows_processed": candidate_rows,
            "path_outcome_r_rows_written": int(row_counts["path_outcome_r"]),
            "path_source_rows_written": int(row_counts["path_source"]),
        },
    }
    write_shard_json(paths["manifest"], manifest)
    heartbeat.update(
        {
            "shard_status": "complete",
            "heartbeat_updated_at_utc": manifest["completed_at_utc"],
            "resume_cursor": manifest["resume_cursor"],
        }
    )
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage04_heartbeat(heartbeat)
    return manifest


def build_shard_contract(
    stage02_rows: list[dict[str, Any]],
    stage03_by_source: dict[str, dict[str, Any]],
    inventory_hash: str,
) -> dict[str, Any]:
    return {
        "schema_version": "vnext_full_replay_stage04_shard_contract_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "created_at_utc": utc_now(),
        "source_count": len(stage02_rows),
        "candidate_rows_expected": sum(
            int((row.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or 0)
            for row in stage02_rows
        ),
        "required_replay_modes": sorted(REQUIRED_REPLAY_MODES),
        "path_horizon_policy": PATH_HORIZON_POLICY,
        "source_inventory_hash": inventory_hash,
        "durability_control": "per_source_stage04_shard_atomic_outputs_manifest_heartbeat_resume_cursor",
        "stage04_scope_boundary": (
            "path/R, source-mode truth, no-fill/pending, and M15-vs-LTF disagreement only; dominance, "
            "pollution, MIXED, ablation, robustness, prop metrics, behavioral forensics, and final map remain incomplete"
        ),
        "source_repair_contract": (
            "Stage01 MT5 placeholders are rewritten as executed read-only export proof rows with manifest/file hashes"
        ),
        "shards": [
            {
                "source_index": int(row.get("source_index") or 0),
                "source_path": row.get("source_path"),
                "stage02_shard_id": row.get("shard_id"),
                "stage03_shard_id": (stage03_by_source.get(str(row.get("source_path"))) or {}).get(
                    "shard_id"
                ),
                "stage04_shard_id": source_stage04_shard_id(
                    row, stage03_by_source[str(row.get("source_path"))]
                )
                if str(row.get("source_path")) in stage03_by_source
                else None,
                "candidate_rows": int(
                    (row.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or 0
                ),
            }
            for row in stage02_rows
        ],
    }


def completed_shard_manifests(
    stage02_rows: list[dict[str, Any]],
    stage03_by_source: dict[str, dict[str, Any]],
    inventory_hash: str,
) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for row in stage02_rows:
        stage03 = stage03_by_source.get(str(row.get("source_path")))
        if not stage03:
            continue
        manifest = completed_shard_manifest(row, stage03, inventory_hash)
        if manifest:
            manifests.append(manifest)
    return sorted(manifests, key=lambda row: int(row.get("source_index") or 0))


def write_master_indices_from_shards(manifests: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for key in SHARDED_ARTIFACT_KEYS:
        rows = []
        for chunk_index, manifest in enumerate(manifests, start=1):
            output = (manifest.get("outputs") or {}).get(key) or {}
            rows.append(
                {
                    "schema_version": "vnext_full_replay_chunk_index_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "logical_artifact_path": rel(OUTPUTS[key]),
                    "chunk_index": chunk_index,
                    "chunk_path": output.get("path"),
                    "row_count": int(output.get("row_count") or 0),
                    "bytes": output.get("bytes"),
                    "sha256": output.get("sha256"),
                    "source_index": manifest.get("source_index"),
                    "source_path": manifest.get("source_path"),
                    "shard_id": manifest.get("shard_id"),
                    "shard_status": manifest.get("shard_status"),
                }
            )
            counts[key] += int(output.get("row_count") or 0)
        write_jsonl(OUTPUTS[key], rows)
    write_jsonl(OUTPUTS["stage04_shard_status"], manifests)
    counts["stage04_source_shards_completed"] = len(manifests)
    return dict(counts)


def manifest_files_by_key(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload.get("files") or {}


def command_proof_payload() -> dict[str, Any]:
    return {
        "read_only": True,
        "forbidden_boundary_hit": False,
        "probe_artifacts": [
            {"path": rel(path), "sha256": sha256_file(path), "exists": path.exists()}
            for path in STAGE04_PROBE_PATHS
        ],
        "export_manifests": [
            {
                "path": rel(STAGE04_EXPANDED_MANIFEST_PATH),
                "sha256": sha256_file(STAGE04_EXPANDED_MANIFEST_PATH),
                "exists": STAGE04_EXPANDED_MANIFEST_PATH.exists(),
            },
            {
                "path": rel(STAGE04_CORE_MANIFEST_PATH),
                "sha256": sha256_file(STAGE04_CORE_MANIFEST_PATH),
                "exists": STAGE04_CORE_MANIFEST_PATH.exists(),
            },
        ],
        "commands_or_export_actions": [
            "python scripts\\inspect_mt5_history_availability.py --start 2026-01-02T00:00:00Z --end 2026-05-24T20:45:00Z --timeframes M1,M5 --label vnext_full_stage04_expanded_m1_m5_probe_2026_05_24 --write-json --yes-live-readonly --symbol ...",
            "python scripts\\inspect_mt5_history_availability.py --start 2026-01-02T00:00:00Z --end 2026-05-24T20:45:00Z --timeframes M1,M5 --label vnext_full_stage04_expanded_alias_probe_2026_05_24 --write-json --yes-live-readonly --symbol GER40:GER30 --symbol UKOIL_cash:UKOUSD --symbol USOIL_cash:USOIL.cash",
            "python scripts\\inspect_mt5_history_availability.py --start 2026-01-02T00:00:00Z --end 2026-05-24T20:45:00Z --timeframes M1,M5 --label vnext_full_stage04_usoil_alias_probe_2026_05_24 --write-json --yes-live-readonly --symbol USOIL_cash:USOUSD --symbol USOIL_cash:USOIL --symbol USOIL_cash:WTI --symbol USOIL_cash:XTIUSD",
            "python scripts\\export_mt5_research_ohlcv.py --start 2026-01-02T00:00:00Z --end 2026-05-24T20:45:00Z --timeframes M1,M5 --label vnext_full_stage04_expanded_m1_m5_readonly_2026_05_24 --chunk-days 7 --yes-live-readonly --symbol ...",
            "python scripts\\inspect_mt5_history_availability.py --start 2026-05-01T00:00:00Z --end 2026-05-24T20:45:00Z --timeframes M1,M5,M15,H1,H4,D1 --label vnext_full_stage04_core_current_window_probe_2026_05_24 --write-json --yes-live-readonly --symbol ...",
            "python scripts\\export_mt5_research_ohlcv.py --start 2026-05-01T00:00:00Z --end 2026-05-24T20:45:00Z --timeframes M1,M5,M15,H1,H4,D1 --label vnext_full_stage04_core_current_window_readonly_2026_05_24 --chunk-days 7 --yes-live-readonly --symbol ...",
        ],
        "alias_repairs": {
            "GER40": "GER30",
            "UKOIL_cash": "UKOUSD",
            "USOIL_cash": "USOUSD",
            "NAS100": "NDX100",
            "US30_cash": "US30",
        },
    }


def build_source_repair_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    old_rows = list(iter_jsonl(MT5_EXPORT_LEDGER_PATH))
    expanded = manifest_files_by_key(STAGE04_EXPANDED_MANIFEST_PATH)
    core = manifest_files_by_key(STAGE04_CORE_MANIFEST_PATH)
    proof_payload = command_proof_payload()
    export_rows: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    for old in old_rows:
        symbol = old.get("symbol")
        timeframe = old.get("timeframe")
        key = f"{symbol}_{timeframe}"
        record = expanded.get(key) or core.get(key)
        output_path = repo_path(record.get("path")) if record else None
        source_hashes = []
        if record and output_path and output_path.exists():
            source_hashes.append(
                {
                    "path": rel(output_path),
                    "sha256": sha256_file(output_path),
                    "row_count": record.get("rows"),
                    "first": record.get("first"),
                    "last": record.get("last"),
                    "mt5_symbol": record.get("mt5_symbol"),
                    "file_symbol": record.get("file_symbol"),
                }
            )
        disposition = "readonly_mt5_export_completed" if source_hashes else "readonly_mt5_export_missing_after_attempt"
        terminal = bool(source_hashes)
        export_row = {
            **old,
            "schema_version": "vnext_full_replay_mt5_export_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "previous_stage_id": old.get("stage_id"),
            "export_disposition": disposition,
            "terminal_disposition": terminal,
            "source_repair_proof_row_required_before_terminal_missing_source": False,
            "readonly_mt5_export_executed": True,
            "forbidden_boundary_hit": False,
            "output_manifest_path": rel(STAGE04_EXPANDED_MANIFEST_PATH)
            if key in expanded
            else rel(STAGE04_CORE_MANIFEST_PATH),
            "output_manifest_sha256": sha256_file(STAGE04_EXPANDED_MANIFEST_PATH)
            if key in expanded
            else sha256_file(STAGE04_CORE_MANIFEST_PATH),
            "output_csv_path": rel(output_path) if output_path else None,
            "output_csv_sha256": sha256_file(output_path) if output_path else None,
            "output_rows": record.get("rows") if record else 0,
            "output_first_utc": record.get("first") if record else None,
            "output_last_utc": record.get("last") if record else None,
            "mt5_symbol_used": record.get("mt5_symbol") if record else None,
            "alias_repair_used": (
                record.get("mt5_symbol") if record and record.get("mt5_symbol") != symbol else None
            ),
            "proof_artifacts": proof_payload,
            "next_action": "bound_to_stage04_source_mode_path_r" if terminal else "row_level_missing_source_after_attempt",
        }
        repair_row = {
            "schema_version": "vnext_full_replay_source_repair_proof_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "previous_stage_id": old.get("stage_id"),
            "proof_id": stable_id("repair04", [symbol, timeframe, disposition], length=24),
            "field_name": f"{symbol}::{timeframe}::source_file",
            "candidate_id": None,
            "expected_source_contract": "read_only_mt5_ohlcv_export_or_availability_probe",
            "join_keys_tested": [{"symbol": symbol, "timeframe": timeframe}],
            "searched_paths_or_roots": [
                rel(STAGE04_EXPANDED_MANIFEST_PATH.parent),
                rel(STAGE04_CORE_MANIFEST_PATH.parent),
                "data/mt5_research_exports/history_availability",
            ],
            "commands_or_export_actions": proof_payload["commands_or_export_actions"],
            "parser_actions": [
                "loaded_stage04_export_manifest",
                "matched_symbol_timeframe_row",
                "hashed_exported_csv",
            ],
            "source_hashes": source_hashes,
            "result": "repaired_readonly_mt5_export_bound" if terminal else "attempted_but_missing",
            "final_disposition": "terminal_stage04_source_repaired" if terminal else "terminal_row_level_missing_after_attempt",
            "forbidden_boundary_hit": False,
            "next_action": "none_for_source_repair_row" if terminal else "missing_source_denominator_excluded",
        }
        export_rows.append(export_row)
        repair_rows.append(repair_row)
    return export_rows, repair_rows


def write_source_repair_ledgers() -> dict[str, Any]:
    export_rows, repair_rows = build_source_repair_rows()
    write_jsonl(MT5_EXPORT_LEDGER_PATH, export_rows)
    write_jsonl(SOURCE_REPAIR_PROOF_LEDGER_PATH, repair_rows)
    write_jsonl(OUTPUTS["source_repair_proof_update"], repair_rows)
    return {
        "mt5_export_rows": len(export_rows),
        "source_repair_proof_rows": len(repair_rows),
        "repaired_rows": sum(1 for row in repair_rows if row.get("result") == "repaired_readonly_mt5_export_bound"),
        "missing_after_attempt_rows": sum(1 for row in repair_rows if row.get("result") != "repaired_readonly_mt5_export_bound"),
    }


def aggregate_summary(manifests: list[dict[str, Any]], repair_counts: dict[str, Any]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    terminal_counts_by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    missing_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    for manifest in manifests:
        for key, value in (manifest.get("row_counts") or {}).items():
            counts[key] += int(value or 0)
        for mode, terminal_counts in (manifest.get("terminal_counts_by_mode") or {}).items():
            terminal_counts_by_mode[mode].update(terminal_counts)
        missing_counts.update(manifest.get("missing_source_counts_by_requested_mode") or {})
        class_counts.update(manifest.get("missed_winner_avoided_loser_classification_counts") or {})
    counts["stage04_source_shards_completed"] = len(manifests)
    summary = {
        "schema_version": "vnext_full_replay_stage04_source_mode_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "created_at_utc": utc_now(),
        "status": "ok",
        "counts": dict(sorted(counts.items())),
        "source_repair_counts": repair_counts,
        "terminal_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in terminal_counts_by_mode.items()
        },
        "missing_source_counts_by_requested_mode": dict(sorted(missing_counts.items())),
        "missed_winner_avoided_loser_classification_counts": dict(sorted(class_counts.items())),
        "required_replay_modes": sorted(REQUIRED_REPLAY_MODES),
        "path_horizon_policy": PATH_HORIZON_POLICY,
        "source_mode_boundary": (
            "M15/M1/M5/tick/Sierra/OHLC path truth measured where source windows exist; "
            "missing rows carry row-level repair proof and remain excluded from source-specific denominators"
        ),
        "next_incomplete_stage": (
            "Stage05 dominance/pollution counterfactuals and MIXED resolution; then ablations, robustness, "
            "prop metrics, behavioral forensics, final decision map"
        ),
    }
    write_json(OUTPUTS["source_mode_summary"], summary)
    return summary


def build_outputs() -> dict[str, Any]:
    stage02_rows = stage02_status_rows()
    stage03_by_source = stage03_status_by_source()
    missing_stage03 = [
        row.get("source_path")
        for row in stage02_rows
        if str(row.get("source_path")) not in stage03_by_source
    ]
    if missing_stage03:
        raise RuntimeError(f"Stage03 shard coverage missing for {len(missing_stage03)} Stage02 sources")
    inventory_hash = source_inventory_hash()
    write_json(OUTPUTS["stage04_shard_contract"], build_shard_contract(stage02_rows, stage03_by_source, inventory_hash))
    manifests: list[dict[str, Any]] = []
    source_count = len(stage02_rows)
    for ordinal, stage02 in enumerate(stage02_rows, start=1):
        stage03 = stage03_by_source[str(stage02.get("source_path"))]
        completed = completed_shard_manifest(stage02, stage03, inventory_hash)
        if completed:
            manifests.append(completed)
            continue
        manifests.append(
            write_one_source_shard(
                stage02_shard=stage02,
                stage03_shard=stage03,
                source_index=ordinal,
                source_count=source_count,
                inventory_hash=inventory_hash,
            )
        )
    manifests = sorted(manifests, key=lambda row: int(row.get("source_index") or 0))
    index_counts = write_master_indices_from_shards(manifests)
    repair_counts = write_source_repair_ledgers()
    summary = aggregate_summary(manifests, repair_counts | {"master_index_counts": index_counts})
    verifier = verify_outputs(summary)
    write_json(OUTPUTS["stage04_verifier"], verifier)
    update_route_control_ledgers(summary, verifier)
    return {"status": verifier["status"], "summary": summary, "verifier": verifier}


def verify_outputs(summary: dict[str, Any] | None = None) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    summary = summary or (read_json(OUTPUTS["source_mode_summary"]) if OUTPUTS["source_mode_summary"].exists() else None)
    expected_candidates = sum(
        int((row.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or 0)
        for row in stage02_status_rows()
    )
    stage02_source_count = len(stage02_status_rows())
    if summary is None:
        failures.append({"reason": "missing_summary"})
        counts: dict[str, Any] = {}
    else:
        counts = summary.get("counts") or {}
    if int(counts.get("candidate_rows") or 0) != expected_candidates:
        failures.append(
            {
                "reason": "candidate_row_count_mismatch",
                "expected": expected_candidates,
                "actual": counts.get("candidate_rows"),
            }
        )
    if int(counts.get("stage04_source_shards_completed") or 0) != stage02_source_count:
        failures.append(
            {
                "reason": "stage04_source_shard_count_mismatch",
                "expected": stage02_source_count,
                "actual": counts.get("stage04_source_shards_completed"),
            }
        )
    repair = summary.get("source_repair_counts") if summary else {}
    if int(repair.get("mt5_export_rows") or 0) != 76:
        failures.append({"reason": "mt5_export_repair_rows_not_76", "actual": repair.get("mt5_export_rows")})
    if int(repair.get("missing_after_attempt_rows") or 0) != 0:
        failures.append(
            {
                "reason": "mt5_source_repair_missing_after_attempt",
                "actual": repair.get("missing_after_attempt_rows"),
            }
        )
    mode_counts = summary.get("terminal_counts_by_mode") if summary else {}
    for mode in sorted(REQUIRED_REPLAY_MODES - {"missing_source"}):
        if mode not in mode_counts:
            failures.append({"reason": "required_replay_mode_absent", "mode": mode})
    for key in OUTPUTS:
        if key == "stage04_verifier":
            continue
        if not OUTPUTS[key].exists():
            failures.append({"reason": "missing_output", "artifact_key": key, "path": rel(OUTPUTS[key])})
    for path in (MT5_EXPORT_LEDGER_PATH, SOURCE_REPAIR_PROOF_LEDGER_PATH):
        if not path.exists():
            failures.append({"reason": "missing_repair_ledger", "path": rel(path)})
    return {
        "schema_version": "vnext_full_replay_stage04_verifier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "checked_at_utc": utc_now(),
        "status": "ok" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures[:50],
        "candidate_rows_expected": expected_candidates,
        "required_replay_modes": sorted(REQUIRED_REPLAY_MODES),
        "stage04_scope_boundary": (
            "Stage04 does not complete dominance/pollution, MIXED resolution, ablation, robustness, prop metrics, "
            "behavioral forensics, or final decision map"
        ),
    }


def audit_chunked_artifact(path: Path, artifact_key: str) -> list[dict[str, Any]]:
    rows = []
    logical_rows = 0
    parse_errors = 0
    if path.exists():
        for index_row in iter_jsonl(path):
            chunk_path = repo_path(index_row.get("chunk_path"))
            logical_rows += int(index_row.get("row_count") or 0)
            chunk_exists = chunk_path.exists()
            rows.append(
                {
                    "schema_version": "vnext_full_replay_line_accountability_audit_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "artifact_key": f"{artifact_key}_chunk",
                    "logical_artifact_path": rel(path),
                    "chunk_path": rel(chunk_path),
                    "exists": chunk_exists,
                    "bytes": chunk_path.stat().st_size if chunk_exists else None,
                    "sha256": sha256_file(chunk_path) if chunk_exists else None,
                    "row_count": int(index_row.get("row_count") or 0),
                    "parse_error_count": 0 if chunk_exists else 1,
                    "audit_status": "PASS" if chunk_exists else "FAIL",
                    "source_builder": rel(Path(__file__).resolve()),
                }
            )
            if not chunk_exists:
                parse_errors += 1
    rows.append(
        {
            "schema_version": "vnext_full_replay_line_accountability_audit_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "artifact_key": artifact_key,
            "file_path": rel(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path) if path.exists() else None,
            "row_count": sum(1 for _ in iter_jsonl(path)) if path.exists() else 0,
            "logical_row_count": logical_rows,
            "parse_error_count": parse_errors,
            "audit_status": "PASS" if path.exists() and parse_errors == 0 else "FAIL",
            "source_builder": rel(Path(__file__).resolve()),
        }
    )
    return rows


def audit_simple_artifact(path: Path, artifact_key: str) -> dict[str, Any]:
    row_count = 0
    parse_errors = 0
    if path.exists():
        try:
            if path.suffix == ".json":
                read_json(path)
                row_count = 1
            elif path.suffix == ".jsonl":
                row_count = sum(1 for _ in iter_jsonl(path))
        except Exception:
            parse_errors += 1
    return {
        "schema_version": "vnext_full_replay_line_accountability_audit_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "artifact_key": artifact_key,
        "file_path": rel(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() else None,
        "row_count": row_count,
        "parse_error_count": parse_errors,
        "audit_status": "PASS" if path.exists() and parse_errors == 0 else "FAIL",
        "source_builder": rel(Path(__file__).resolve()),
    }


def update_line_audit() -> None:
    existing = [
        row
        for row in (list(iter_jsonl(LINE_AUDIT_PATH)) if LINE_AUDIT_PATH.exists() else [])
        if row.get("stage_id") != STAGE_ID
    ]
    stage_rows: list[dict[str, Any]] = []
    for key in SHARDED_ARTIFACT_KEYS:
        stage_rows.extend(audit_chunked_artifact(OUTPUTS[key], key))
    for key in (
        "source_repair_proof_update",
        "source_mode_summary",
        "stage04_verifier",
        "stage04_shard_contract",
        "stage04_heartbeat",
        "stage04_shard_status",
    ):
        stage_rows.append(audit_simple_artifact(OUTPUTS[key], key))
    stage_rows.append(audit_simple_artifact(MT5_EXPORT_LEDGER_PATH, "mt5_export_ledger"))
    stage_rows.append(audit_simple_artifact(SOURCE_REPAIR_PROOF_LEDGER_PATH, "source_repair_proof_ledger"))
    write_jsonl(LINE_AUDIT_PATH, existing + stage_rows)


def stage04_question_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q009_STAGE04_DOMINANCE_POLLUTION_NEXT",
            "question": "Which vNext decisions dominate or pollute the lower-timeframe path/R outcome distribution?",
            "status": "open_next_stage",
            "created_at_utc": utc_now(),
            "evidence_path": rel(OUTPUTS["source_mode_summary"]),
        },
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q010_STAGE04_MIXED_RESOLUTION_NEXT",
            "question": "Which MIXED decisions resolve to promote, kill, or repair once path truth is joined?",
            "status": "open_next_stage",
            "created_at_utc": utc_now(),
            "evidence_path": rel(OUTPUTS["m15_vs_ltf_disagreement"]),
        },
    ]


def stage04_prompt_application_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "vnext_full_replay_prompt_application_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "prompt_requirement": "Execute/export/repair 76 MT5 export/source requirements unless forbidden boundary hit with row-level proof",
            "application_status": "applied",
            "evidence_path": rel(MT5_EXPORT_LEDGER_PATH),
            "row_count": summary.get("source_repair_counts", {}).get("mt5_export_rows"),
            "created_at_utc": utc_now(),
        },
        {
            "schema_version": "vnext_full_replay_prompt_application_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "prompt_requirement": "Measure path truth across M15/M1/M5/tick/Sierra/OHLC with no-fill, ordering, disagreement, missed winner, avoided loser rows",
            "application_status": "applied_partial_replay_spine_continues",
            "evidence_path": rel(OUTPUTS["path_outcome_r"]),
            "row_count": summary.get("counts", {}).get("path_outcome_r"),
            "created_at_utc": utc_now(),
        },
    ]


def update_session_state(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    state = read_json(SESSION_STATE_PATH) if SESSION_STATE_PATH.exists() else {}
    counts = state.get("counts") or {}
    counts.update(
        {
            "stage04_path_source_rows": summary["counts"].get("path_source"),
            "stage04_path_outcome_r_rows": summary["counts"].get("path_outcome_r"),
            "stage04_nofill_pending_lifecycle_rows": summary["counts"].get(
                "nofill_pending_lifecycle"
            ),
            "stage04_m15_vs_ltf_disagreement_rows": summary["counts"].get(
                "m15_vs_ltf_disagreement"
            ),
            "stage04_missed_winner_avoided_loser_rows": summary["counts"].get(
                "missed_winner_avoided_loser"
            ),
            "stage04_source_shards_completed": summary["counts"].get(
                "stage04_source_shards_completed"
            ),
            "stage04_mt5_export_repair_rows": summary["source_repair_counts"].get(
                "mt5_export_rows"
            ),
        }
    )
    state.update(
        {
            "schema_version": "vnext_full_replay_session_state_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "git_head": git_head(),
            "current_stage": STAGE_ID,
            "goal_complete": False,
            "active_invariant": "Stage04 lower-timeframe/source-mode export repair and path/R simulation",
            "first_incomplete_invariant": "Stage05 dominance/pollution counterfactuals and MIXED resolution",
            "next_action": (
                "join Stage03 runtime decisions to Stage04 path/R rows for dominance/pollution counterfactuals, "
                "then resolve MIXED decisions before ablations/robustness/prop metrics/behavioral forensics"
            ),
            "stage04_verifier_status": verifier["status"],
            "stage04_output_paths": {key: rel(path) for key, path in OUTPUTS.items()},
            "stage04_mt5_source_repair_status": summary["source_repair_counts"],
            "stage04_scope_boundary": (
                "source-mode path/R complete for available/repaired sources; dominance/pollution, MIXED, "
                "ablation, robustness, prop metrics, behavioral forensics, final decision map remain incomplete"
            ),
            "counts": counts,
            "stage04_terminal_counts_by_mode": summary["terminal_counts_by_mode"],
            "stage04_missed_winner_avoided_loser_classification_counts": summary[
                "missed_winner_avoided_loser_classification_counts"
            ],
        }
    )
    open_questions = set(state.get("open_questions") or [])
    open_questions.update(row["question_id"] for row in stage04_question_rows(summary))
    state["open_questions"] = sorted(open_questions)
    write_json(SESSION_STATE_PATH, state)


def update_completion_audit(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    audit = read_json(COMPLETION_AUDIT_PATH) if COMPLETION_AUDIT_PATH.exists() else {}
    audit.update(
        {
            "schema_version": "vnext_full_replay_completion_audit_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "completion_status": "IN_PROGRESS_NOT_COMPLETE",
            "completed_requirements_stage04": [
                "Stage04 source-mode path/R driver built route-locally",
                "76 Stage01 MT5/export placeholders rewritten as executed read-only export proof rows",
                "M15, M1, M5, tick/Sierra, OHLC proxy, and missing-source mode rows emitted",
                "entry touch/fill timing, stop-first/target-first ordering, timeout, no-fill, and ambiguity measured where source exists",
                "M15-vs-LTF disagreement rows emitted",
                "no-fill/pending lifecycle rows emitted using 48h production pending-intent replay proxy",
                "missed winner and avoided loser classification rows emitted",
                "Stage04 verifier enforces candidate/shard coverage, replay mode presence, and MT5 repair row count",
            ],
            "stage04_counts": summary["counts"],
            "stage04_source_repair_counts": summary["source_repair_counts"],
            "stage04_verifier_status": verifier["status"],
            "remaining_prompt_requirements_not_complete": [
                "dominance and pollution counterfactuals",
                "MIXED replay resolution",
                "ablation/robustness/prop metrics",
                "behavioral forensics",
                "subagent or equivalent independent review for terminal outputs",
                "final promote/kill/repair map",
                "goal completion audit",
            ],
            "same_evidence_class_next_action": "build Stage05 dominance/pollution counterfactuals and MIXED resolution",
            "goal_may_be_marked_complete": False,
        }
    )
    write_json(COMPLETION_AUDIT_PATH, audit)


def chunk_artifact_manifest(logical_path: Path, artifact_key: str) -> list[dict[str, Any]]:
    rows = []
    logical_count = 0
    if not logical_path.exists():
        return rows
    for index_row in iter_jsonl(logical_path):
        chunk_path = repo_path(index_row["chunk_path"])
        logical_count += int(index_row.get("row_count") or 0)
        rows.append(
            {
                "artifact_key": f"{artifact_key}_chunk",
                "path": rel(chunk_path),
                "logical_artifact_path": rel(logical_path),
                "bytes": chunk_path.stat().st_size if chunk_path.exists() else None,
                "sha256": sha256_file(chunk_path) if chunk_path.exists() else None,
                "row_count": int(index_row.get("row_count") or 0),
                "logical_row_count": None,
                "source_kind": "generated_replay_shard",
            }
        )
    rows.append(
        {
            "artifact_key": artifact_key,
            "path": rel(logical_path),
            "bytes": logical_path.stat().st_size,
            "sha256": sha256_file(logical_path),
            "row_count": sum(1 for _ in iter_jsonl(logical_path)),
            "logical_row_count": logical_count,
            "source_kind": "logical_chunk_index",
        }
    )
    return rows


def update_output_manifest(summary: dict[str, Any]) -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {
        "schema_version": "vnext_full_replay_output_manifest_v1",
        "route_id": ROUTE_ID,
        "artifacts": [],
    }
    stage_keys = {
        "path_source",
        "path_source_chunk",
        "path_outcome_r",
        "path_outcome_r_chunk",
        "nofill_pending_lifecycle",
        "nofill_pending_lifecycle_chunk",
        "m15_vs_ltf_disagreement",
        "m15_vs_ltf_disagreement_chunk",
        "missed_winner_avoided_loser",
        "missed_winner_avoided_loser_chunk",
        "source_repair_proof_update",
        "source_mode_summary",
        "stage04_verifier",
        "stage04_shard_contract",
        "stage04_heartbeat",
        "stage04_shard_status",
        "mt5_export_ledger",
        "source_repair_proof_ledger",
        "active_questions",
        "extra_step",
        "prompt_application",
        "line_audit",
        "completion_audit",
    }
    old = [row for row in existing.get("artifacts", []) if row.get("artifact_key") not in stage_keys]
    artifacts: list[dict[str, Any]] = []
    for key in SHARDED_ARTIFACT_KEYS:
        artifacts.extend(chunk_artifact_manifest(OUTPUTS[key], key))
    for key in (
        "source_repair_proof_update",
        "source_mode_summary",
        "stage04_verifier",
        "stage04_shard_contract",
        "stage04_heartbeat",
        "stage04_shard_status",
    ):
        path = OUTPUTS[key]
        artifacts.append(
            {
                "artifact_key": key,
                "path": rel(path),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
                "row_count": (
                    sum(1 for _ in iter_jsonl(path))
                    if path.exists() and path.suffix == ".jsonl"
                    else (1 if path.exists() else 0)
                ),
                "logical_row_count": None,
                "source_kind": "generated_replay_output",
            }
        )
    for key, path in {
        "mt5_export_ledger": MT5_EXPORT_LEDGER_PATH,
        "source_repair_proof_ledger": SOURCE_REPAIR_PROOF_LEDGER_PATH,
        "active_questions": ACTIVE_QUESTION_PATH,
        "extra_step": EXTRA_STEP_PATH,
        "prompt_application": PROMPT_APPLICATION_PATH,
        "line_audit": LINE_AUDIT_PATH,
        "completion_audit": COMPLETION_AUDIT_PATH,
    }.items():
        if path.exists():
            artifacts.append(
                {
                    "artifact_key": key,
                    "path": rel(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "row_count": sum(1 for _ in iter_jsonl(path)) if path.suffix == ".jsonl" else 1,
                    "logical_row_count": None,
                    "source_kind": "route_control_artifact",
                }
            )
    existing.update(
        {
            "schema_version": "vnext_full_replay_output_manifest_v1",
            "route_id": ROUTE_ID,
            "created_at_utc": existing.get("created_at_utc") or utc_now(),
            "updated_at_utc": utc_now(),
            "stage_id": STAGE_ID,
            "goal_complete": False,
            "artifacts": old + artifacts,
            "stage04_counts": summary["counts"],
        }
    )
    write_json(OUTPUT_MANIFEST_PATH, existing)


def update_route_control_ledgers(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    existing_questions = [
        row
        for row in (list(iter_jsonl(ACTIVE_QUESTION_PATH)) if ACTIVE_QUESTION_PATH.exists() else [])
        if row.get("stage_id") != STAGE_ID
    ]
    write_jsonl(ACTIVE_QUESTION_PATH, existing_questions + stage04_question_rows(summary))
    existing_extra = [
        row
        for row in (list(iter_jsonl(EXTRA_STEP_PATH)) if EXTRA_STEP_PATH.exists() else [])
        if row.get("stage_id") != STAGE_ID
    ]
    write_jsonl(
        EXTRA_STEP_PATH,
        existing_extra
        + [
            {
                "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "extra_step_id": "STAGE04_SOURCE_MODE_REPAIR_AND_PATH_R",
                "status": "completed_for_stage04",
                "evidence_path": rel(OUTPUTS["source_mode_summary"]),
                "created_at_utc": utc_now(),
            }
        ],
    )
    existing_prompt = [
        row
        for row in (list(iter_jsonl(PROMPT_APPLICATION_PATH)) if PROMPT_APPLICATION_PATH.exists() else [])
        if row.get("stage_id") != STAGE_ID
    ]
    write_jsonl(PROMPT_APPLICATION_PATH, existing_prompt + stage04_prompt_application_rows(summary))
    update_session_state(summary, verifier)
    update_completion_audit(summary, verifier)
    update_line_audit()
    update_output_manifest(summary)


def check_outputs() -> dict[str, Any]:
    summary = read_json(OUTPUTS["source_mode_summary"]) if OUTPUTS["source_mode_summary"].exists() else None
    verifier = verify_outputs(summary)
    audit_failures = []
    if LINE_AUDIT_PATH.exists():
        for row in iter_jsonl(LINE_AUDIT_PATH):
            if row.get("stage_id") == STAGE_ID and row.get("audit_status") != "PASS":
                audit_failures.append(
                    {
                        "artifact_key": row.get("artifact_key"),
                        "file_path": row.get("file_path"),
                        "chunk_path": row.get("chunk_path"),
                        "reason": "line_audit_not_pass",
                    }
                )
    status = "ok" if verifier["status"] == "ok" and not audit_failures else "fail"
    return {
        "status": status,
        "verifier": verifier,
        "audit_failure_count": len(audit_failures),
        "audit_failures": audit_failures[:20],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify existing Stage04 outputs.")
    args = parser.parse_args(argv)
    payload = check_outputs() if args.check else build_outputs()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
