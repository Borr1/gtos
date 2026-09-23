"""F8 — H1-2026 baseline reconstruction from agent_*.log files.

Parses the production agent logs (``logs/agent_*.log`` in the project
root, or ``knowledge_base/logs/agent_*_demo.log`` in this codebase) and
emits JSONL evaluation records that match the
``knowledge_base/live_evaluations/`` schema as closely as possible.

Why this exists
===============
B7 (commit ``9611c58``) computed AI hallucination rates over the
April-2026 corpus that lives in ``knowledge_base/live_evaluations/``
and ``knowledge_base/trade_records/``. Both directories start at
2026-04-06. The H1→H2 hallucination delta needed by the K54 handoff
cannot be computed without an earlier baseline.

This script extracts the baseline that lives in the agent logs:

* Each "Processing candle" line begins one evaluation cycle.
* Each subsequent log line in the same cycle carries one piece of the
  evaluation (deterministic bias, align-score, pre-screen verdict,
  AI-cited entry/SL/TP from primary_analyzer warnings, L2 verifier
  AI=X / MSO=Y mismatches, proximity-shadow distances, etc.).
* The cycle ends at the next "Processing candle" line (or end-of-file).

The reconstructed records are written to
``knowledge_base/live_evaluations_h1_reconstructed/{SYMBOL}/{DATE}.jsonl``
— a SEPARATE directory so we never contaminate the canonical
``live_evaluations/`` corpus.

Hard rules
----------
* **No AI / Anthropic API calls.** Pure regex + struct join.
* **Read-only inputs.** ``logs/`` and ``knowledge_base/logs/`` and
  ``knowledge_base/live_evaluations/`` are read-only.
* **No production-code dependencies.** This file does not import from
  ``src/components/`` (production trading code).
* **Dedup.** Records that already exist in canonical
  ``live_evaluations/`` are skipped — the canonical record always wins.
  Dedup key: ``(symbol, candle_time_minute_utc)``.
* **Never fabricate.** Fields we cannot extract stay ``None``; rate
  aggregations downstream tolerate this.

Schema divergence vs ``live_evaluations``
-----------------------------------------
The reconstructed JSONL keeps the same flat shape but adds two
provenance fields and may have ``None`` for many fields the canonical
corpus carries (e.g., ``daily_bias_confidence``, ``confidence_score``).

Reconstructed-only fields:

* ``record_source`` — always ``"agent_log_reconstructed"``.
* ``log_file`` — relative path of the source log (debug provenance).

Reconstructed-only **AI-cited prices** are stitched into a synthetic
``overall_reasoning`` string so the existing B7 ``parse_ai_prices``
path picks them up. Format::

    "Reconstructed from agent log. AI cited entry 4777.43000 SL 4762.14000 TP 4800.36500. Displacement AI=4.50 MSO=3.60. PROXIMITY: dist_atr=1.62."

Note this synthetic string is intentionally bland so regex
patterns in :mod:`src.research_infra.hallucination_measurement` pick
up the prices without false positives.

CLI
---
::

    python scripts/research/reconstruct_h1_evaluations.py \\
        --logs-dir C:/Users/MSI/Documents/ai-trading-agent/logs \\
        --output knowledge_base/live_evaluations_h1_reconstructed \\
        [--start 2026-01-01] [--end 2026-04-05] [--dry-run]

If ``--logs-dir`` does not contain ``agent_*.log`` files, falls back to
``knowledge_base/logs/`` (same project, alternate location).

Per memory ``feedback_worktree_gitignore_invisibility``, the canonical
``logs/`` directory is gitignored — pass an absolute path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Set, Tuple

# Make project root importable when invoked directly.
_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default reconstruction window (per F8 brief): everything before
# live_evaluations/ starts (2026-04-06). Override via --start/--end.
DEFAULT_START: str = "2026-01-01"
DEFAULT_END: str = "2026-04-05"

#: Recognized symbol stems in agent log filenames.
KNOWN_SYMBOLS: Tuple[str, ...] = (
    "XAUUSD",
    "XAGUSD",
    "US30_cash",
    "US30",
    "NAS100",
    "USDJPY",
    "GBPJPY",
    "GBPUSD",
    "EURUSD",
    "EURJPY",
)

#: Filename patterns we recognize. Both ``logs/agent_<SYMBOL>.log`` (live)
#: and ``knowledge_base/logs/agent_<SYMBOL>_demo.log`` (preserved) are
#: scanned. The capture group is the symbol stem.
LOG_FILENAME_RE = re.compile(
    r"^agent_(?P<symbol>[A-Z][A-Za-z0-9_]*?)(?:_demo|_mock)?\.log$"
)

# ---------------------------------------------------------------------------
# Log-line regexes
# ---------------------------------------------------------------------------
#
# Each agent log line has the form:
#
#     YYYY-MM-DD HH:MM:SS,mmm LEVEL [logger.name] message...
#
# We anchor on the timestamp prefix and dispatch on the logger name
# to extract structured fields.
#

LINE_PREFIX_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(?P<ms>\d{3}) "
    r"(?P<level>[A-Z]+) "
    r"\[(?P<logger>[^\]]+)\] "
    r"(?P<msg>.*)$"
)

PROCESSING_CANDLE_RE = re.compile(r"Processing candle .*?\b(?P<kz>london|ny|tokyo|asian)\b KZ", re.IGNORECASE)
ALIGN_SCORE_RE = re.compile(
    r"Align score: (?P<score>\d)/(?P<total>\d)\s+(?P<bias>bullish|bearish|ranging|transitional)"
)
DETERMINISTIC_BIAS_RE = re.compile(
    r"Deterministic bias:\s*(?P<bias>bullish|bearish|ranging|transitional)\s*\(source=(?P<source>[^)]+)\)"
)
PRE_SCREEN_FAIL_RE = re.compile(r"Pre-screen FAILED:\s*(?P<reason>.+)$")
PRE_AI_GATE_RE = re.compile(r"Pre-AI gate skip:\s*(?P<reason>.+)$")
TP1_PLACEMENT_RE = re.compile(
    r"TP1 placement warning:.*?\(entry=(?P<entry>[\d.]+),\s*SL=(?P<sl>[\d.]+),\s*TP1=(?P<tp1>[\d.]+)\)"
)
DISPLACEMENT_MISMATCH_RE = re.compile(
    r"Displacement ratio mismatch:\s*AI=(?P<ai>[\d.]+)\s+MSO=(?P<mso>[\d.]+)"
)
L2_VERIFICATION_FAIL_RE = re.compile(
    r"L2 verification FAILED:\s*(?P<rule>\w+).*?SL\s+(?P<sl>[\d.]+)\s+is NOT (?:below|above)\s+OB\s+(?:low|high)\s+(?P<ob>[\d.]+)"
)
PROXIMITY_SHADOW_RE = re.compile(
    r"PROXIMITY_SHADOW:.*?proximity=(?P<prox>\w+)\s+dist_atr=(?P<dist>[\d.]+)"
)
TRADE_RECORD_RE = re.compile(
    r"Trade record saved:.*[\\/](?P<symbol>[A-Z][A-Za-z0-9_]*?)[\\/](?P<filename>\d{4}-\d{2}-\d{2}_(?P<kz>\w+)_(?P<hhmm>\d{4})\.json)"
)
CONFIDENCE_RE = re.compile(
    r"Confidence:\s*grade=(?P<grade>\w+)\s+price_levels=(?P<lvls>\d+)\s+hesitation=(?P<hes>\d+)\s+multiplier=(?P<mult>[\d.]+)"
)
MALFORMED_RE = re.compile(r"Malformed response")
HTTP_ANTHROPIC_RE = re.compile(r'POST https://api\.anthropic\.com/v1/messages "HTTP/1\.1 (?P<status>\d+)')
SHADOW_DA_RE = re.compile(r"Shadow DA:\s*max_risk=(?P<risk>\d+)%")

# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class CandleEval:
    """One evaluation cycle — partially-reconstructed.

    Maps loosely to one ``live_evaluations`` JSONL record. ``None``
    fields signal "could not extract".
    """

    symbol: str
    candle_time: str  # ISO-8601 minute UTC
    log_file: str
    kill_zone: Optional[str] = None
    daily_bias_direction: Optional[str] = None
    daily_bias_source: Optional[str] = None
    align_score: Optional[int] = None
    align_total: Optional[int] = None
    pre_screen_fail: Optional[str] = None
    pre_ai_skip: Optional[str] = None
    ai_called: bool = False
    ai_http_status: Optional[int] = None
    malformed_responses: int = 0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    displacement_ai: Optional[float] = None
    displacement_mso: Optional[float] = None
    l2_fail_rule: Optional[str] = None
    l2_sl_value: Optional[float] = None
    l2_ob_value: Optional[float] = None
    proximity: Optional[str] = None
    dist_atr: Optional[float] = None
    confidence_grade: Optional[str] = None
    confidence_multiplier: Optional[float] = None
    confidence_price_levels: Optional[int] = None
    trade_record_path: Optional[str] = None

    @property
    def has_useful_signal(self) -> bool:
        """Return True if this cycle carries something B7 can use.

        A useful signal requires EITHER an AI call OR pre-screen failure
        (which is metadata about the eval). Pure noise (just bootstrap
        log lines) is filtered out.
        """
        return any(
            (
                self.ai_called,
                self.entry_price is not None,
                self.stop_loss is not None,
                self.l2_fail_rule is not None,
                self.displacement_ai is not None,
                self.pre_screen_fail is not None,
                self.pre_ai_skip is not None,
                self.proximity is not None,
                self.confidence_grade is not None,
            )
        )

    @property
    def has_ai_prices(self) -> bool:
        return self.entry_price is not None or self.stop_loss is not None

    def derive_decision(self) -> str:
        """Coarse decision proxy.

        We cannot recover the canonical AI ``decision`` field from the
        log alone (it lives in the AI response JSON which is not
        logged). We derive it as best we can:

        * If AI was called and entry+SL+TP1 were emitted → CANDIDATE.
        * If AI was called but no trade params surfaced → NO_TRADE.
        * If pre-screen failed → NO_TRADE (gate killed before AI).
        * If pre-AI gate skipped → NO_TRADE.
        * Else → UNKNOWN.
        """
        if self.entry_price is not None and self.stop_loss is not None:
            return "CANDIDATE"
        if self.ai_called:
            return "NO_TRADE"
        if self.pre_screen_fail or self.pre_ai_skip:
            return "NO_TRADE"
        return "UNKNOWN"

    def synth_overall_reasoning(self) -> str:
        """Build a synthetic ``overall_reasoning`` string.

        We embed AI-cited prices in a format that
        :func:`hallucination_measurement._extract_text_prices` will
        pattern-match, so downstream B7 picks them up without us
        needing to alter the parser.
        """
        parts: List[str] = ["Reconstructed from agent log."]
        if self.entry_price is not None:
            parts.append(f"Price at {self.entry_price:.5f}.")
        if self.stop_loss is not None:
            parts.append(f"SL placed at {self.stop_loss:.5f}.")
        if self.take_profit_1 is not None:
            parts.append(f"TP1 at {self.take_profit_1:.5f}.")
        if self.l2_sl_value is not None and self.l2_ob_value is not None:
            parts.append(
                f"L2 verification noted SL {self.l2_sl_value:.5f} relative to "
                f"OB at {self.l2_ob_value:.5f}-{self.l2_ob_value:.5f}."
            )
        if self.displacement_ai is not None and self.displacement_mso is not None:
            parts.append(
                f"Displacement AI={self.displacement_ai:.2f} MSO={self.displacement_mso:.2f}."
            )
        if self.dist_atr is not None:
            parts.append(f"Proximity dist_atr={self.dist_atr:.2f}.")
        return " ".join(parts)

    def to_jsonl_dict(self) -> Dict[str, Any]:
        """Serialize as a JSONL dict matching live_evaluations schema."""
        candle_dt = _parse_ts(self.candle_time)
        timestamp_iso = self.candle_time
        if candle_dt is not None:
            timestamp_iso = candle_dt.isoformat().replace("+00:00", "+00:00")

        # Derive a kill-zone label that matches the canonical labels
        # ('london'/'ny'/'tokyo' lower-case) — preserve None when unknown.
        kz = (self.kill_zone or "").lower() or None

        # daily_bias_direction matches canonical labels (bullish/bearish/ranging).
        # 'transitional' is mapped to 'ranging' to align with v1 labels.
        bias = self.daily_bias_direction
        if bias == "transitional":
            bias = "ranging"

        rec: Dict[str, Any] = {
            "timestamp": timestamp_iso,
            "candle_time": self.candle_time,
            "symbol": self.symbol,
            "kill_zone": kz,
            "decision": self.derive_decision(),
            "daily_bias_direction": bias,
            "daily_bias_confidence": None,
            "h4_aligned": None,
            "h1_poi_identified": None if self.pre_ai_skip != "no_unmitigated_h1_pois" else False,
            "h1_poi_type": "none" if self.pre_ai_skip == "no_unmitigated_h1_pois" else None,
            "h1_zone": None,
            "h1_fib_pct": 0.0,
            "h1_causing_event": None,
            "sweep_detected": None,
            "sweep_type": None,
            "sweep_quality": None,
            "m15_choch": None,
            "m15_displacement_quality": None,
            "m15_displacement_ratio": (
                self.displacement_ai if self.displacement_ai is not None else 0.0
            ),
            "setup_grade": None,
            "confidence_score": None,
            "framework": None,
            "session_memory_count": None,
            "align_score": self.align_score,
            "spread": None,
            "candle_index_in_kz": None,
            "no_trade_reason": self.pre_screen_fail or self.pre_ai_skip or self.l2_fail_rule,
            "wait_reason": None,
            "reasoning_word_count": None,
            "reasoning_price_count": None,
            "overall_reasoning": self.synth_overall_reasoning(),
            # Reconstructed-only provenance fields
            "record_source": "agent_log_reconstructed",
            "log_file": self.log_file,
            "reconstructed_l2_fail_rule": self.l2_fail_rule,
            "reconstructed_proximity": self.proximity,
            "reconstructed_dist_atr": self.dist_atr,
            "reconstructed_entry_price": self.entry_price,
            "reconstructed_stop_loss": self.stop_loss,
            "reconstructed_take_profit_1": self.take_profit_1,
            "reconstructed_displacement_ai": self.displacement_ai,
            "reconstructed_displacement_mso": self.displacement_mso,
            "reconstructed_confidence_grade": self.confidence_grade,
            "reconstructed_confidence_multiplier": self.confidence_multiplier,
            "reconstructed_trade_record_path": self.trade_record_path,
        }
        return rec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_ts(s: str) -> Optional[dt.datetime]:
    """Parse a timestamp string to UTC tz-aware datetime."""
    if not s:
        return None
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        try:
            d = dt.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def _isoformat_minute(d: dt.datetime) -> str:
    """ISO-8601 string truncated to whole minute."""
    d = d.replace(second=0, microsecond=0)
    return d.isoformat()


def _extract_symbol_from_filename(name: str) -> Optional[str]:
    """Map ``agent_<SYMBOL>(_demo|_mock)?.log`` to canonical symbol key."""
    m = LOG_FILENAME_RE.match(name)
    if not m:
        return None
    raw = m.group("symbol")
    if not raw:
        return None
    # Preserve underscored suffixes as lowercase (US30_cash convention)
    if "_" in raw:
        prefix, rest = raw.split("_", 1)
        return f"{prefix.upper()}_{rest.lower()}"
    return raw.upper()


def _list_log_files(logs_dir: Path) -> List[Path]:
    """Return all ``agent_*.log`` files in ``logs_dir`` (non-recursive)."""
    if not logs_dir.exists() or not logs_dir.is_dir():
        return []
    return sorted(
        p for p in logs_dir.iterdir()
        if p.is_file() and LOG_FILENAME_RE.match(p.name) and _extract_symbol_from_filename(p.name)
    )


def _resolve_logs_dir(primary: Optional[Path]) -> Path:
    """Return a logs dir that contains agent_*.log files.

    Tries ``primary`` first, then falls back to
    ``$PROJECT_ROOT/knowledge_base/logs`` (where this codebase
    historically preserves logs).
    """
    if primary and _list_log_files(primary):
        return primary
    fallback = _PROJECT_ROOT / "knowledge_base" / "logs"
    if _list_log_files(fallback):
        return fallback
    # Try logs/ at project root (gitignored — present only on the live host)
    canonical = _PROJECT_ROOT / "logs"
    if _list_log_files(canonical):
        return canonical
    return primary or canonical  # let caller error out


def _existing_eval_keys(canonical_dir: Path) -> Set[Tuple[str, str]]:
    """Build the dedup set: ``{(symbol, candle_time_minute)}``.

    Reads canonical ``live_evaluations/`` so we never re-emit a record
    that's already there.
    """
    keys: Set[Tuple[str, str]] = set()
    if not canonical_dir.exists():
        return keys
    for symbol_dir in canonical_dir.iterdir():
        if not symbol_dir.is_dir():
            continue
        sym = symbol_dir.name
        for jsonl in symbol_dir.glob("*.jsonl"):
            try:
                with open(jsonl, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        ct = rec.get("candle_time")
                        if not ct:
                            continue
                        d = _parse_ts(str(ct))
                        if d is None:
                            continue
                        keys.add((sym, _isoformat_minute(d)))
            except OSError:
                continue
    return keys


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


@dataclass
class ParseStats:
    files_scanned: int = 0
    bytes_scanned: int = 0
    lines_scanned: int = 0
    candles_started: int = 0
    candles_emitted: int = 0
    candles_dedup_skipped: int = 0
    candles_outside_window: int = 0
    candles_no_signal: int = 0
    parse_errors: int = 0
    earliest_ts: Optional[str] = None
    latest_ts: Optional[str] = None


def parse_log_file(
    path: Path,
    *,
    start_dt: Optional[dt.datetime],
    end_dt: Optional[dt.datetime],
    stats: Optional[ParseStats] = None,
) -> Iterator[CandleEval]:
    """Stream :class:`CandleEval` records from one agent log file.

    Each "Processing candle" line begins a new cycle; the cycle is
    flushed at the next "Processing candle" or end-of-file.
    """
    if stats is None:
        stats = ParseStats()

    sym = _extract_symbol_from_filename(path.name)
    if sym is None:
        return

    log_file_label = path.name

    current: Optional[CandleEval] = None

    def _flush() -> Optional[CandleEval]:
        nonlocal current
        out = current
        current = None
        return out

    try:
        size = path.stat().st_size
        stats.bytes_scanned += size
        stats.files_scanned += 1
    except OSError:
        return

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            stats.lines_scanned += 1
            line = raw.rstrip("\r\n")
            m = LINE_PREFIX_RE.match(line)
            if not m:
                # Continuation line (traceback, etc) — append to no-where.
                continue
            ts_str = f"{m.group('ts')}.{m.group('ms')}"
            ts = _parse_ts(f"{m.group('ts')}+00:00")
            if ts is None:
                stats.parse_errors += 1
                continue

            # Track earliest/latest log timestamp
            if stats.earliest_ts is None or ts.isoformat() < stats.earliest_ts:
                stats.earliest_ts = ts.isoformat()
            if stats.latest_ts is None or ts.isoformat() > stats.latest_ts:
                stats.latest_ts = ts.isoformat()

            # Window filter on TIMESTAMP (cycle is flushed only when
            # in-window — out-of-window cycles are dropped).
            in_window = True
            if start_dt is not None and ts < start_dt:
                in_window = False
            if end_dt is not None and ts >= end_dt:
                in_window = False

            logger_name = m.group("logger")
            msg = m.group("msg")

            # --- Cycle boundary ---
            pc = PROCESSING_CANDLE_RE.search(msg)
            if pc:
                # Flush previous cycle
                prev = _flush()
                if prev is not None:
                    if not prev.has_useful_signal:
                        stats.candles_no_signal += 1
                    else:
                        yield prev
                stats.candles_started += 1
                if not in_window:
                    stats.candles_outside_window += 1
                    current = None
                    continue
                current = CandleEval(
                    symbol=sym,
                    candle_time=_isoformat_minute(ts),
                    kill_zone=pc.group("kz").lower(),
                    log_file=log_file_label,
                )
                continue

            if current is None:
                # Lines outside any cycle (bootstrap, shutdown, etc).
                continue

            # --- Within-cycle event handlers ---

            # Align score
            asm = ALIGN_SCORE_RE.search(msg)
            if asm:
                try:
                    current.align_score = int(asm.group("score"))
                    current.align_total = int(asm.group("total"))
                except (TypeError, ValueError):
                    pass
                if current.daily_bias_direction is None:
                    current.daily_bias_direction = asm.group("bias")
                continue

            # Deterministic bias
            dbm = DETERMINISTIC_BIAS_RE.search(msg)
            if dbm:
                current.daily_bias_direction = dbm.group("bias")
                current.daily_bias_source = dbm.group("source")
                continue

            # Pre-screen failure (before AI call)
            psm = PRE_SCREEN_FAIL_RE.search(msg)
            if psm:
                current.pre_screen_fail = psm.group("reason").strip()
                continue

            # Pre-AI gate skip
            pgm = PRE_AI_GATE_RE.search(msg)
            if pgm:
                current.pre_ai_skip = pgm.group("reason").strip()
                continue

            # AI HTTP call
            hm = HTTP_ANTHROPIC_RE.search(msg)
            if hm:
                current.ai_called = True
                try:
                    current.ai_http_status = int(hm.group("status"))
                except (TypeError, ValueError):
                    pass
                continue

            # Malformed AI response
            if MALFORMED_RE.search(msg):
                current.malformed_responses += 1
                continue

            # AI-emitted entry/SL/TP1 — extracted from the TP1 placement warning
            tpm = TP1_PLACEMENT_RE.search(msg)
            if tpm:
                try:
                    current.entry_price = float(tpm.group("entry"))
                    current.stop_loss = float(tpm.group("sl"))
                    current.take_profit_1 = float(tpm.group("tp1"))
                except (TypeError, ValueError):
                    pass
                continue

            # Displacement AI vs MSO
            dm = DISPLACEMENT_MISMATCH_RE.search(msg)
            if dm:
                try:
                    current.displacement_ai = float(dm.group("ai"))
                    current.displacement_mso = float(dm.group("mso"))
                except (TypeError, ValueError):
                    pass
                continue

            # L2 verification rejection
            lm = L2_VERIFICATION_FAIL_RE.search(msg)
            if lm:
                current.l2_fail_rule = lm.group("rule")
                try:
                    current.l2_sl_value = float(lm.group("sl"))
                    current.l2_ob_value = float(lm.group("ob"))
                except (TypeError, ValueError):
                    pass
                continue

            # Proximity shadow
            pm = PROXIMITY_SHADOW_RE.search(msg)
            if pm:
                current.proximity = pm.group("prox")
                try:
                    current.dist_atr = float(pm.group("dist"))
                except (TypeError, ValueError):
                    pass
                continue

            # Confidence
            cm = CONFIDENCE_RE.search(msg)
            if cm:
                current.confidence_grade = cm.group("grade")
                try:
                    current.confidence_multiplier = float(cm.group("mult"))
                    current.confidence_price_levels = int(cm.group("lvls"))
                except (TypeError, ValueError):
                    pass
                continue

            # Trade record saved → preserve provenance link
            trm = TRADE_RECORD_RE.search(msg)
            if trm:
                current.trade_record_path = (
                    f"{trm.group('symbol')}/{trm.group('filename')}"
                )
                continue

    # Flush tail
    last = _flush()
    if last is not None:
        if not last.has_useful_signal:
            stats.candles_no_signal += 1
        else:
            yield last


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def reconstruct(
    *,
    logs_dir: Path,
    output_dir: Path,
    start: Optional[str] = DEFAULT_START,
    end: Optional[str] = DEFAULT_END,
    canonical_evals_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> ParseStats:
    """Run the full reconstruction sweep.

    Returns the :class:`ParseStats` summary for caller logging.
    """
    start_dt = _parse_ts(f"{start}T00:00:00+00:00") if start else None
    end_dt = _parse_ts(f"{end}T23:59:59+00:00") if end else None

    if canonical_evals_dir is None:
        canonical_evals_dir = _PROJECT_ROOT / "knowledge_base" / "live_evaluations"

    dedup_keys = _existing_eval_keys(canonical_evals_dir)
    logger.info("Built dedup set: %d existing canonical eval keys", len(dedup_keys))

    files = _list_log_files(logs_dir)
    if not files:
        logger.warning("No agent_*.log files found in %s", logs_dir)
        return ParseStats()

    logger.info("Scanning %d log files in %s", len(files), logs_dir)

    stats = ParseStats()
    # Bucket by (symbol, date) to write one JSONL per day per symbol.
    buckets: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

    for path in files:
        for ev in parse_log_file(path, start_dt=start_dt, end_dt=end_dt, stats=stats):
            d = _parse_ts(ev.candle_time)
            if d is None:
                continue
            key = (ev.symbol, _isoformat_minute(d))
            if key in dedup_keys:
                stats.candles_dedup_skipped += 1
                continue
            stats.candles_emitted += 1
            buckets.setdefault((ev.symbol, d.strftime("%Y-%m-%d")), []).append(
                ev.to_jsonl_dict()
            )
            # Also track in dedup_keys to suppress within-batch dupes
            dedup_keys.add(key)

    # --- Write outputs ---
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        for (sym, date_str), recs in sorted(buckets.items()):
            sym_dir = output_dir / sym
            sym_dir.mkdir(parents=True, exist_ok=True)
            out_path = sym_dir / f"{date_str}.jsonl"
            with open(out_path, "w", encoding="utf-8") as f:
                for r in recs:
                    f.write(json.dumps(r) + "\n")
        logger.info("Wrote %d buckets across %d symbols to %s",
                    len(buckets), len({s for s, _ in buckets}), output_dir)
    else:
        logger.info(
            "DRY RUN: would write %d buckets across %d symbols",
            len(buckets), len({s for s, _ in buckets}),
        )

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="reconstruct_h1_evaluations.py",
        description="F8 — Reconstruct H1-2026 evaluations from agent_*.log files.",
    )
    p.add_argument(
        "--logs-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing agent_*.log files. Defaults to "
            "$PROJECT_ROOT/logs (gitignored, live host) with fallback to "
            "$PROJECT_ROOT/knowledge_base/logs."
        ),
    )
    p.add_argument(
        "--output",
        "--output-dir",
        type=Path,
        default=_PROJECT_ROOT / "knowledge_base" / "live_evaluations_h1_reconstructed",
        help="Output directory for reconstructed JSONL files.",
    )
    p.add_argument(
        "--start",
        type=str,
        default=DEFAULT_START,
        help=f"ISO date (inclusive); default {DEFAULT_START}.",
    )
    p.add_argument(
        "--end",
        type=str,
        default=DEFAULT_END,
        help=f"ISO date (inclusive); default {DEFAULT_END}.",
    )
    p.add_argument(
        "--canonical-evals-dir",
        type=Path,
        default=None,
        help=(
            "Path to canonical live_evaluations/ for dedup. Defaults to "
            "$PROJECT_ROOT/knowledge_base/live_evaluations."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse + report stats but do NOT write any output files.",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose logging.",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logs_dir = _resolve_logs_dir(args.logs_dir)
    files = _list_log_files(logs_dir)
    if not files:
        logger.error(
            "No agent_*.log files found. Tried: %s, %s, %s",
            args.logs_dir, _PROJECT_ROOT / "logs", _PROJECT_ROOT / "knowledge_base" / "logs",
        )
        return 2

    stats = reconstruct(
        logs_dir=logs_dir,
        output_dir=args.output,
        start=args.start,
        end=args.end,
        canonical_evals_dir=args.canonical_evals_dir,
        dry_run=args.dry_run,
    )

    print()
    print("=" * 60)
    print("F8 reconstruction stats")
    print("=" * 60)
    print(f"  logs dir            : {logs_dir}")
    print(f"  output dir          : {args.output}")
    print(f"  window              : {args.start} to {args.end}")
    print(f"  files scanned       : {stats.files_scanned}")
    print(f"  bytes scanned       : {stats.bytes_scanned:,}")
    print(f"  lines scanned       : {stats.lines_scanned:,}")
    print(f"  log earliest ts     : {stats.earliest_ts}")
    print(f"  log latest ts       : {stats.latest_ts}")
    print(f"  candles started     : {stats.candles_started:,}")
    print(f"  candles emitted     : {stats.candles_emitted:,}")
    print(f"  candles dedup skip  : {stats.candles_dedup_skipped:,}")
    print(f"  candles no signal   : {stats.candles_no_signal:,}")
    print(f"  candles out window  : {stats.candles_outside_window:,}")
    print(f"  parse errors        : {stats.parse_errors:,}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
