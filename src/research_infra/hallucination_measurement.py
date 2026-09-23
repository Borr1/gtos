"""B7 — Hallucination Rate Systematic Measurement.

Programmatic comparison of AI-stated price levels vs MSO ``raw_data`` on
every historical evaluation we have on disk. Phase 1 = $0 API. NO AI
re-run. Pure-Python OHLCV / structured-record join.

Why this exists
===============
A1 (dumb-baseline) verdict (2026-04-26) said the H2-2026 XAUUSD WR
decay is *AI-side* — the gap between mechanical OB-pullback realized R
and AI realized R is closing in H2 because the AI side is collapsing,
not because the mechanical side is collapsing. B7 decomposes one
candidate failure-mode driving that AI-side collapse: **hallucination**.

A hallucination here is a price the AI cited (in trade parameters,
``reasoning`` JSON sub-fields, or the explanation text) that does not
appear in the MSO it was given, beyond a tolerance window. If the
hallucination rate spiked H1 → H2 we have a concrete decay mechanism;
if it stayed flat we can rule one mechanism out and continue down the
B-series checklist (B12 confidence, B14 walk-level, K53 anti-pattern,
…).

Inputs (read-only)
==================
The data we have on disk for THIS task:

* ``knowledge_base/trade_records/{SYMBOL}/*.json`` — 148 CANDIDATE
  records (April 2026 only). Each carries the FULL MSO at decision
  time under ``mso``, the FULL AI response under ``ai_response``, and
  pre-paired ``mso_value`` / ``ai_value`` blocks under
  ``decision_pipeline.level2_verification.checks``.

* ``knowledge_base/live_evaluations/{SYMBOL}/*.jsonl`` — 1,240 records
  (NO_TRADE + CANDIDATE) over 2026-04-06 → 2026-04-24. These are
  text-only — they carry ``overall_reasoning`` + ``no_trade_reason``
  explanation strings but **not** the MSO that was sent to the AI.
  They are still useful because we can extract AI-cited prices from
  the text and compare to the OHLCV range at the candle's time
  (data/historical_2026/) — but classification is coarser there
  (cited price either is or isn't inside the recent candle range).

We support BOTH sources. The trade_records source is the precise
source-of-truth (paired ``mso_value`` / ``ai_value``); the
live_evaluations source is the broader-coverage source (NO_TRADEs
included; rate denominator is reasoning text).

Outputs
=======
:class:`HallucinationReport` aggregates per-instrument, per-period
(month + H1/H2 partition), per-framework, per-decision rates:

* ``accurate``        — cited price exists in MSO within tolerance
* ``hallucinated``    — cited price has NO match in MSO
* ``misattributed``   — cited price exists in MSO but at a different
                        role/label than the AI claimed (e.g. claimed
                        "OB top" but the price is actually a swing low)

K54 handoff
===========
This module **measures** hallucination rate. It does not propose a
fix. The K54 handoff (post-Monday research kickoff) decides whether
to:

* feed the AI a tool-use confirmation step ("verify this OB exists
  before citing it") — research/tool_use_grounding/DESIGN.md
* tighten the L2 verifier ``h1_poi_exists`` to bit-exact match
* add a shadow logger that flags hallucinations live for Telegram
  alerts (additive — does not block trades)

Hard rules
==========
* **No AI / Anthropic API calls.** Pure file-system + regex + struct
  comparison.
* **Read-only inputs.** ``knowledge_base/trade_records/``,
  ``knowledge_base/live_evaluations/``, ``data/historical_2026/`` are
  read-only. Outputs go to a caller-supplied directory.
* **No production-code dependencies.** This file does not import from
  ``src/components/`` (production trading code) and does not modify
  any ``shadow_logs/`` files.
* **Walk-level + realized-R discipline** (memory
  ``feedback_walk_level_evidence_not_predictive``): hallucination is
  a behavioural metric (walk-level by nature). We additionally join
  realized R per CAND when available so the H1→H2 verdict carries
  both signals.
* **Never fabricate.** When MSO is missing or the cited price cannot
  be parsed, we record the row with ``classification=None`` and
  exclude it from rate aggregations — never invent a value.

Tolerance choice
================
Default tolerance is **5 ticks** (per the brief). Per-instrument tick
sizes (mirroring :mod:`src.research_infra.dumb_baseline`):

* XAUUSD : 0.01 → 0.05 USD tolerance
* USDJPY / GBPJPY : 0.001 → 0.005 JPY tolerance (≈ 0.5 pip)
* GBPUSD / EURUSD : 0.00001 → 5 ticks = 0.00005 (≈ 0.5 pip)
* US30_cash / NAS100 : 0.01 → 0.05 USD tolerance

Why 5 ticks: per-instrument minimum-quoted-precision floor. Tighter
than 5 ticks would over-flag rounding-induced mismatches between the
AI's quoted price (3-5 dp) and the broker's tick grid. Looser would
hide real hallucinations on tight-FX pairs. The `--tolerance-ticks`
CLI flag sweeps this; the default mirrors the L2 verifier's
``sl_beyond_ob_tick_floor`` (config), which is the closest production
analogue.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project-root resolution + default paths
# ---------------------------------------------------------------------------

# src/research_infra/hallucination_measurement.py → project root is parents[2]
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DEFAULT_TRADE_RECORDS_DIR: Path = PROJECT_ROOT / "knowledge_base" / "trade_records"
DEFAULT_LIVE_EVALUATIONS_DIR: Path = PROJECT_ROOT / "knowledge_base" / "live_evaluations"
DEFAULT_OHLCV_DIR: Path = PROJECT_ROOT / "data" / "historical_2026"

#: Harness version embedded in summary.json; bump when contract changes.
HARNESS_VERSION: str = "B7-v1"

#: F13 role-stratified harness version (B7-v2). Emitted in summary
#: artifacts when ``role_class`` aggregations are requested. The v1
#: tag remains the default for backward compatibility — v2 only
#: surfaces in the additive ``role_class`` aggregation paths.
HARNESS_VERSION_V2: str = "B7-v2"

#: Default tolerance for the price-match check, in ticks.
DEFAULT_TOLERANCE_TICKS: int = 5


# ---------------------------------------------------------------------------
# Tick / pip table — mirrors mechanical_backtest.get_pip_size
# ---------------------------------------------------------------------------

#: Per-instrument tick size used for the tolerance computation.
TICK_SIZE: Dict[str, float] = {
    "XAUUSD": 0.01,
    "XAGUSD": 0.001,
    "US30_cash": 0.01,
    "US30": 0.01,
    "NAS100": 0.01,
    "USDJPY": 0.001,
    "GBPJPY": 0.001,
    "EURJPY": 0.001,
    "GBPUSD": 0.00001,
    "EURUSD": 0.00001,
}

#: Map instrument key → OHLCV file stem. ``US30`` and ``US30_cash``
#: share ``US30_cash`` files.
OHLCV_STEM: Dict[str, str] = {
    "XAUUSD": "XAUUSD",
    "XAGUSD": "XAGUSD",
    "US30_cash": "US30_cash",
    "US30": "US30_cash",
    "NAS100": "NAS100",
    "USDJPY": "USDJPY",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
}

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Classification = Literal["accurate", "hallucinated", "misattributed"]

#: F13 — Role class taxonomy. Each AI-cited role is bucketed into ONE
#: of three classes. The MSO_GROUNDED bucket is the only one where a
#: ``hallucinated`` classification reflects a real grounding failure;
#: FORWARD_DERIVED roles (take_profit, trailing_stop_target) are
#: forward-projected (entry + N×R or future targets) and DO NOT appear
#: in the MSO by construction, so a ``hallucinated`` verdict for them
#: is a measurement artifact of the v1 harness, not a real failure.
#:
#: AMBIGUOUS roles are case-by-case — the AI's ``equilibrium`` claim
#: sometimes matches a structural midpoint (MSO_GROUNDED), sometimes
#: is a Fibonacci-style derivation that doesn't appear in MSO. We mark
#: them AMBIGUOUS so per-instrument comparison does not silently
#: include them in the strict MSO-grounded rate.
#:
#: F9 (commit ``cffb99c``) decomposed US30's headline 23.4% rate and
#: showed 40.3% of it came from the take_profit artifact. F13 makes
#: that decomposition first-class.
RoleClass = Literal["MSO_GROUNDED", "FORWARD_DERIVED", "AMBIGUOUS"]

#: Mapping from cited-price ``role`` → :data:`RoleClass`.
#:
#: MSO_GROUNDED — the AI is claiming a price that should appear in the
#: MSO. A hallucinated verdict here is a real grounding failure. Roles
#: whose values come directly from the MSO (``ob_high``, ``ob_low``,
#: ``swing_high`` …) plus the entry/SL roles which the AI synthesizes
#: from MSO geometry (entry from OB band, SL from OB beyond / swing
#: beyond). Per the F13 brief, ``entry_price`` and ``stop_loss`` are
#: MSO_GROUNDED — the AI is required to anchor them to MSO structure
#: and ``classify_price`` accepts an ``all_values()`` match within
#: tolerance for those roles, so a hallucinated verdict means the AI
#: cited a value that doesn't appear ANYWHERE in the MSO band.
#:
#: FORWARD_DERIVED — the AI is computing the price from the trade plan
#: (``take_profit`` = entry + N × R; ``trailing_stop_target`` is a
#: planned exit level). These prices are not expected to match MSO
#: data; flagging them as hallucinated is a definitional artifact.
#:
#: AMBIGUOUS — semantically can go either way. ``equilibrium`` is the
#: 50% level between recent swings, sometimes structurally inside an
#: OB body (matches MSO_GROUNDED) and sometimes a Fibonacci-style
#: derivation off the swings without an exact MSO match. Since the
#: ``parse_ai_prices`` regex doesn't surface enough context to
#: disambiguate, we record it as AMBIGUOUS and exclude it from the
#: strict MSO-grounded rate.
ROLE_TAXONOMY: Dict[str, RoleClass] = {
    # ---- MSO_GROUNDED — should match MSO data; hallucinated = real failure ----
    "current_price": "MSO_GROUNDED",
    "entry_price": "MSO_GROUNDED",
    "stop_loss": "MSO_GROUNDED",
    "ob_high": "MSO_GROUNDED",
    "ob_low": "MSO_GROUNDED",
    "ob_mid": "MSO_GROUNDED",
    "ob_body": "MSO_GROUNDED",
    "breaker_high": "MSO_GROUNDED",
    "breaker_low": "MSO_GROUNDED",
    "breaker_mid": "MSO_GROUNDED",
    "fvg_high": "MSO_GROUNDED",
    "fvg_low": "MSO_GROUNDED",
    "fvg_mid": "MSO_GROUNDED",
    "swing_high": "MSO_GROUNDED",
    "swing_low": "MSO_GROUNDED",
    "protected_swing": "MSO_GROUNDED",
    "sweep_price": "MSO_GROUNDED",
    "liquidity_high": "MSO_GROUNDED",
    "liquidity_low": "MSO_GROUNDED",
    # ---- FORWARD_DERIVED — not in MSO by construction ----
    "take_profit": "FORWARD_DERIVED",
    "trailing_stop_target": "FORWARD_DERIVED",
    # ---- AMBIGUOUS — case-by-case ----
    "equilibrium": "AMBIGUOUS",
}


def role_class_of(role: str) -> RoleClass:
    """Return the :data:`RoleClass` for a role.

    Unknown / novel roles default to ``AMBIGUOUS`` so they do not
    silently inflate the MSO-grounded rate. New canonical roles must
    be added to :data:`ROLE_TAXONOMY` explicitly.
    """
    return ROLE_TAXONOMY.get(role, "AMBIGUOUS")


#: Roles we attempt to verify per evaluation. The role drives the
#: lookup strategy in :func:`classify_price` — e.g. "ob_high" looks at
#: H1 ``order_blocks[*].high``; "swing_high" looks at H1 swings; etc.
ROLE_KEYS = (
    "current_price",
    "entry_price",
    "stop_loss",
    "take_profit",
    "ob_high",
    "ob_low",
    "ob_mid",
    "breaker_high",
    "breaker_low",
    "fvg_high",
    "fvg_low",
    "swing_high",
    "swing_low",
    "sweep_price",
    "protected_swing",
)


def _canonical_symbol(sym: str) -> str:
    """Return canonical instrument key (preserve underscored suffixes)."""
    if not sym:
        return ""
    s = sym.strip()
    if "_" in s:
        prefix, rest = s.split("_", 1)
        return f"{prefix.upper()}_{rest.lower()}"
    return s.upper()


def _tick_size(symbol: str) -> float:
    """Return tick size for a symbol; defaults to 0.01 if unknown."""
    canonical = _canonical_symbol(symbol)
    return TICK_SIZE.get(canonical, TICK_SIZE.get(canonical.upper(), 0.01))


def _normalize_to_utc_minute(ts: Any) -> Optional[dt.datetime]:
    """Normalize a timestamp to whole-minute UTC tz-aware datetime."""
    if ts is None:
        return None
    if isinstance(ts, dt.datetime):
        parsed = ts
    else:
        s = str(ts).strip()
        if not s:
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            parsed = dt.datetime.fromisoformat(s)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    parsed = parsed.astimezone(dt.timezone.utc)
    return parsed.replace(second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Pure data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CitedPrice:
    """One AI-cited price extracted from a record.

    ``role`` is the AI's claim ("ob_high", "current_price", ...). The
    classifier compares the value to the MSO field implied by the role.

    ``source_field`` is a short human-readable provenance ("trade_parameters.entry_price",
    "reasoning.h1_setup.poi_price_level", "explanation_regex:Price 4667.64").
    """

    role: str
    value: float
    source_field: str


@dataclass
class PriceClassification:
    role: str
    value: float
    source_field: str
    classification: Optional[Classification]
    matched_mso_field: Optional[str] = None
    matched_mso_value: Optional[float] = None
    delta_ticks: Optional[float] = None
    note: Optional[str] = None
    #: F13 — auto-derived from :data:`ROLE_TAXONOMY` (see
    #: :func:`role_class_of`). Defaults to the lookup at construction
    #: time so existing call sites (which do not know about role
    #: classes) still produce v2-compatible records.
    role_class: RoleClass = field(default="AMBIGUOUS")

    def __post_init__(self) -> None:
        # Auto-derive role_class from role unless caller passed an
        # explicit non-default. We can't tell "explicit AMBIGUOUS" from
        # "default AMBIGUOUS" — so we re-derive whenever the role is
        # in the taxonomy. This means callers can trust
        # ``cls.role_class`` matches ``role_class_of(cls.role)``
        # whenever the role is known.
        if self.role in ROLE_TAXONOMY:
            self.role_class = ROLE_TAXONOMY[self.role]


@dataclass
class EvaluationCheck:
    """One hallucination-checked evaluation row."""

    record_source: str  # "trade_records" or "live_evaluations"
    symbol: str
    candle_time_utc: Optional[str]
    period_month: Optional[str]  # "YYYY-MM"
    period_half: Optional[str]   # "H1-2026" / "H2-2026" / None
    decision: Optional[str]
    framework: Optional[str]
    realized_r: Optional[float] = None
    classifications: List[PriceClassification] = field(default_factory=list)


@dataclass
class HallucinationRateRow:
    """Aggregated hallucination rate at one cohort key."""

    key: str  # e.g. "XAUUSD|H1-2026" or "USDJPY|2026-04|ob_retest"
    instrument: Optional[str]
    period: Optional[str]
    framework: Optional[str]
    decision: Optional[str]
    n_evaluations: int = 0
    n_prices: int = 0
    n_accurate: int = 0
    n_hallucinated: int = 0
    n_misattributed: int = 0
    #: F13 — role class for role-stratified rows. ``None`` for
    #: aggregations that span multiple role classes (e.g. the original
    #: per-instrument row).
    role_class: Optional[RoleClass] = None

    @property
    def accurate_pct(self) -> Optional[float]:
        return None if self.n_prices == 0 else 100.0 * self.n_accurate / self.n_prices

    @property
    def hallucinated_pct(self) -> Optional[float]:
        return None if self.n_prices == 0 else 100.0 * self.n_hallucinated / self.n_prices

    @property
    def misattributed_pct(self) -> Optional[float]:
        return None if self.n_prices == 0 else 100.0 * self.n_misattributed / self.n_prices


@dataclass
class HallucinationReport:
    """Top-level result of :func:`measure_hallucination_rate`."""

    harness_version: str
    tolerance_ticks: int
    n_records_scanned: int
    n_records_with_classifications: int
    rows: List[EvaluationCheck] = field(default_factory=list)
    by_instrument: List[HallucinationRateRow] = field(default_factory=list)
    by_instrument_period: List[HallucinationRateRow] = field(default_factory=list)
    by_instrument_month: List[HallucinationRateRow] = field(default_factory=list)
    by_instrument_framework: List[HallucinationRateRow] = field(default_factory=list)
    by_role: List[HallucinationRateRow] = field(default_factory=list)
    h1_h2_delta_pp: Optional[float] = None
    most_hallucinated_role: Optional[str] = None

    # ---- F13 (B7-v2) role-stratified aggregations (additive) ----
    #: Per-instrument × per-role-class aggregation. Each instrument gets
    #: up to 3 rows: one per :data:`RoleClass`. The MSO_GROUNDED row is
    #: the corrected per-instrument hallucination rate (TP artifact
    #: stripped). Empty unless the report was built via the v2
    #: aggregator path (default in :func:`measure_hallucination_rate`,
    #: opt-in via the CLI ``--by-role-class`` flag, which is ON by
    #: default).
    by_instrument_role_class: List[HallucinationRateRow] = field(default_factory=list)
    #: Per-instrument MSO_GROUNDED-only row — convenience accessor.
    #: Populated alongside :attr:`by_instrument_role_class`.
    by_instrument_mso_grounded: List[HallucinationRateRow] = field(default_factory=list)

    def to_summary_dict(self) -> Dict[str, Any]:
        """Compact dict suitable for JSON serialization.

        Includes the v1 schema unchanged. v2 (role-stratified) rows
        appear under ``by_instrument_role_class`` and
        ``by_instrument_mso_grounded`` when populated; absent (empty
        lists) for v1-only callers, which keeps backward compatibility.
        """
        return {
            "harness_version": self.harness_version,
            "tolerance_ticks": self.tolerance_ticks,
            "n_records_scanned": self.n_records_scanned,
            "n_records_with_classifications": self.n_records_with_classifications,
            "by_instrument": [_row_to_dict(r) for r in self.by_instrument],
            "by_instrument_period": [_row_to_dict(r) for r in self.by_instrument_period],
            "by_instrument_month": [_row_to_dict(r) for r in self.by_instrument_month],
            "by_instrument_framework": [_row_to_dict(r) for r in self.by_instrument_framework],
            "by_role": [_row_to_dict(r) for r in self.by_role],
            "by_instrument_role_class": [_row_to_dict(r) for r in self.by_instrument_role_class],
            "by_instrument_mso_grounded": [_row_to_dict(r) for r in self.by_instrument_mso_grounded],
            "h1_h2_delta_pp": self.h1_h2_delta_pp,
            "most_hallucinated_role": self.most_hallucinated_role,
        }


def _row_to_dict(r: HallucinationRateRow) -> Dict[str, Any]:
    return {
        "key": r.key,
        "instrument": r.instrument,
        "period": r.period,
        "framework": r.framework,
        "decision": r.decision,
        "role_class": r.role_class,
        "n_evaluations": r.n_evaluations,
        "n_prices": r.n_prices,
        "n_accurate": r.n_accurate,
        "n_hallucinated": r.n_hallucinated,
        "n_misattributed": r.n_misattributed,
        "accurate_pct": r.accurate_pct,
        "hallucinated_pct": r.hallucinated_pct,
        "misattributed_pct": r.misattributed_pct,
    }


# ---------------------------------------------------------------------------
# AI-cited-price extraction
# ---------------------------------------------------------------------------

# Regex patterns for explanation-text price extraction. The roles are
# the heuristic labels we apply when the role can be inferred from
# context. Patterns match a price (with decimal point) that follows /
# precedes a role-disambiguating keyword.
#
# We deliberately under-extract rather than over-extract: a price
# appearing in a sentence like "All three C-gates pass" with a number
# is more likely a count (5 BOS, 3 candles) than a price, so we
# REQUIRE a decimal point.
PRICE_PATTERN = r"(\d{1,5}\.\d{1,5})"

#: Patterns: each tuple is ``(role, regex, source_label)``. The regex
#: must capture the price as group(1).
EXPLANATION_PATTERNS: Sequence[Tuple[str, re.Pattern[str], str]] = (
    # Current/spot price
    ("current_price", re.compile(r"[Cc]urrent price[^\d]*" + PRICE_PATTERN), "explanation:current_price"),
    ("current_price", re.compile(r"[Pp]rice (?:at|is|of) " + PRICE_PATTERN), "explanation:price_at"),
    ("current_price", re.compile(r"[Pp]rice trading (?:in [a-z]+ )?at " + PRICE_PATTERN), "explanation:price_trading"),
    # OB top/bottom — pattern "OB X-Y" or "OB at X-Y" → high=max, low=min
    # Accepts: "H1 OB 4518.23-4501.61", "OB at 214.13-214.02", "order blocks 211.40-211.30"
    ("ob_pair", re.compile(r"OB(?:s)?(?: (?:at|is at|are at))? " + PRICE_PATTERN + r"[\-–—]" + PRICE_PATTERN), "explanation:ob_pair"),
    ("ob_pair", re.compile(r"order block(?:s)?(?: (?:at|is at|are at))? " + PRICE_PATTERN + r"[\-–—]" + PRICE_PATTERN), "explanation:ob_pair_long"),
    # Breaker
    ("breaker_pair", re.compile(r"breaker(?:s)?(?: at)? " + PRICE_PATTERN + r"[\-–—]" + PRICE_PATTERN), "explanation:breaker_pair"),
    # FVG
    ("fvg_pair", re.compile(r"FVG[^\d]*?" + PRICE_PATTERN + r"[\-–—]" + PRICE_PATTERN), "explanation:fvg_pair"),
    # Swing
    ("swing_high", re.compile(r"swing high[^\d]*" + PRICE_PATTERN), "explanation:swing_high"),
    ("swing_low", re.compile(r"swing low[^\d]*" + PRICE_PATTERN), "explanation:swing_low"),
    # Sweep
    ("sweep_price", re.compile(r"sweep[^\d]*" + PRICE_PATTERN), "explanation:sweep"),
    # Equilibrium / 50%
    ("equilibrium", re.compile(r"[Ee]quilibrium (?:at |is at )" + PRICE_PATTERN), "explanation:equilibrium"),
)


def parse_ai_prices(ai_output: Mapping[str, Any]) -> List[CitedPrice]:
    """Extract every AI-cited price from one record.

    Accepts BOTH the trade_records ``ai_response`` shape (rich dict
    with ``trade_parameters`` + ``reasoning`` sub-blocks) and the
    live_evaluations flat shape (``overall_reasoning`` text, plus
    optional structured fields like ``no_trade_reason``).
    """
    cited: List[CitedPrice] = []

    # --- Structured: trade_parameters block (trade_records) ---
    tp = ai_output.get("trade_parameters") if isinstance(ai_output, Mapping) else None
    if isinstance(tp, Mapping):
        for key, role in (
            ("entry_price", "entry_price"),
            ("stop_loss", "stop_loss"),
            ("take_profit_1", "take_profit"),
            ("take_profit_2", "take_profit"),
            ("take_profit_3", "take_profit"),
        ):
            v = tp.get(key)
            if isinstance(v, (int, float)) and not _is_zero_or_nan(v):
                cited.append(CitedPrice(role=role, value=float(v), source_field=f"trade_parameters.{key}"))

    # --- Structured: reasoning sub-blocks (trade_records) ---
    reasoning = ai_output.get("reasoning") if isinstance(ai_output, Mapping) else None
    if isinstance(reasoning, Mapping):
        # h1_setup.poi_price_level → ob_mid (POI midpoint)
        h1 = reasoning.get("h1_setup") or {}
        if isinstance(h1, Mapping):
            v = h1.get("poi_price_level")
            if isinstance(v, (int, float)) and not _is_zero_or_nan(v):
                # role depends on poi_type
                poi_type = (h1.get("poi_type") or "").lower()
                if poi_type == "ob":
                    role = "ob_mid"
                elif poi_type == "fvg":
                    role = "fvg_mid"
                elif poi_type == "breaker":
                    role = "breaker_mid"
                else:
                    role = "ob_mid"  # default conservative guess
                cited.append(CitedPrice(role=role, value=float(v), source_field="reasoning.h1_setup.poi_price_level"))

            # h1_setup.explanation often has "OB at HIGH-LOW (midpoint MID)"
            text = h1.get("explanation") or ""
            cited.extend(_extract_text_prices(text, source_prefix="reasoning.h1_setup.explanation"))

        # daily_bias.protected_swing_level
        db = reasoning.get("daily_bias") or {}
        if isinstance(db, Mapping):
            v = db.get("protected_swing_level")
            if isinstance(v, (int, float)) and not _is_zero_or_nan(v):
                cited.append(CitedPrice(role="protected_swing", value=float(v), source_field="reasoning.daily_bias.protected_swing_level"))

        # liquidity_sweep.sweep_price
        lq = reasoning.get("liquidity_sweep") or {}
        if isinstance(lq, Mapping):
            v = lq.get("sweep_price")
            if isinstance(v, (int, float)) and not _is_zero_or_nan(v):
                cited.append(CitedPrice(role="sweep_price", value=float(v), source_field="reasoning.liquidity_sweep.sweep_price"))

        # overall_reasoning text
        text = reasoning.get("overall_reasoning") or ""
        cited.extend(_extract_text_prices(text, source_prefix="reasoning.overall_reasoning"))

    # --- live_evaluations shape: top-level overall_reasoning + no_trade_reason ---
    if "overall_reasoning" in ai_output and isinstance(ai_output.get("overall_reasoning"), str):
        # Avoid double-extracting if reasoning was already nested above
        if not isinstance(reasoning, Mapping) or "overall_reasoning" not in (reasoning or {}):
            cited.extend(_extract_text_prices(ai_output["overall_reasoning"], source_prefix="overall_reasoning"))
    if "no_trade_reason" in ai_output and isinstance(ai_output.get("no_trade_reason"), str):
        cited.extend(_extract_text_prices(ai_output["no_trade_reason"], source_prefix="no_trade_reason"))

    return cited


def _extract_text_prices(text: str, *, source_prefix: str) -> List[CitedPrice]:
    """Apply EXPLANATION_PATTERNS to a free-text string."""
    if not text:
        return []
    out: List[CitedPrice] = []
    for role, pattern, label in EXPLANATION_PATTERNS:
        for m in pattern.finditer(text):
            try:
                if role.endswith("_pair"):
                    a = float(m.group(1))
                    b = float(m.group(2))
                    if math.isnan(a) or math.isnan(b):
                        continue
                    high = max(a, b)
                    low = min(a, b)
                    base = role.replace("_pair", "")
                    out.append(CitedPrice(role=f"{base}_high", value=high, source_field=f"{source_prefix}|{label}|high"))
                    out.append(CitedPrice(role=f"{base}_low", value=low, source_field=f"{source_prefix}|{label}|low"))
                else:
                    v = float(m.group(1))
                    if not math.isnan(v):
                        out.append(CitedPrice(role=role, value=v, source_field=f"{source_prefix}|{label}"))
            except (ValueError, IndexError):
                continue
    return out


def _is_zero_or_nan(v: Any) -> bool:
    """Filter sentinels: 0.0 (unset) and NaN."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return True
    return math.isnan(f) or f == 0.0


# ---------------------------------------------------------------------------
# MSO price-set extraction
# ---------------------------------------------------------------------------


@dataclass
class MSOPriceSet:
    """Flattened lookup of price levels appearing in an MSO.

    Keys are role labels; values are lists of ``(value, mso_field)``
    tuples. The classifier loops every (role, value) emitted by the AI
    and tries to find a match in the same role bucket within tolerance.
    """

    by_role: Dict[str, List[Tuple[float, str]]] = field(default_factory=dict)

    def add(self, role: str, value: Any, mso_field: str) -> None:
        try:
            f = float(value)
        except (TypeError, ValueError):
            return
        if math.isnan(f):
            return
        self.by_role.setdefault(role, []).append((f, mso_field))

    def all_values(self) -> List[Tuple[float, str, str]]:
        """Flatten to (value, role, mso_field) — used for misattribution."""
        out: List[Tuple[float, str, str]] = []
        for role, items in self.by_role.items():
            for v, fld in items:
                out.append((v, role, fld))
        return out


def build_mso_price_set(mso: Mapping[str, Any]) -> MSOPriceSet:
    """Extract every relevant price level from an MSO dict.

    Tolerant to missing fields. Operates over each timeframe's
    structured blocks (order_blocks, breaker_blocks, fair_value_gaps,
    swings) and the session_levels block.
    """
    ps = MSOPriceSet()

    if not isinstance(mso, Mapping):
        return ps

    # --- Per-timeframe blocks ---
    timeframes = mso.get("timeframes") or {}
    if isinstance(timeframes, Mapping):
        for tf, block in timeframes.items():
            if not isinstance(block, Mapping):
                continue

            # Order blocks
            for i, ob in enumerate(block.get("order_blocks") or []):
                if isinstance(ob, Mapping):
                    ps.add("ob_high", ob.get("high"), f"timeframes.{tf}.order_blocks[{i}].high")
                    ps.add("ob_low", ob.get("low"), f"timeframes.{tf}.order_blocks[{i}].low")
                    # OB body (open/close) — useful for entry-derivation matching.
                    if isinstance(ob.get("open"), (int, float)):
                        ps.add("ob_body", ob["open"], f"timeframes.{tf}.order_blocks[{i}].open")
                    if isinstance(ob.get("close"), (int, float)):
                        ps.add("ob_body", ob["close"], f"timeframes.{tf}.order_blocks[{i}].close")
                    h, l = ob.get("high"), ob.get("low")
                    if isinstance(h, (int, float)) and isinstance(l, (int, float)):
                        ps.add("ob_mid", (float(h) + float(l)) / 2.0, f"timeframes.{tf}.order_blocks[{i}].midpoint")

            # Breakers — production MSOs use ``zone_high``/``zone_low``
            for i, bb in enumerate(block.get("breaker_blocks") or []):
                if isinstance(bb, Mapping):
                    bb_high = bb.get("zone_high", bb.get("high"))
                    bb_low = bb.get("zone_low", bb.get("low"))
                    ps.add("breaker_high", bb_high, f"timeframes.{tf}.breaker_blocks[{i}].zone_high")
                    ps.add("breaker_low", bb_low, f"timeframes.{tf}.breaker_blocks[{i}].zone_low")
                    if isinstance(bb_high, (int, float)) and isinstance(bb_low, (int, float)):
                        ps.add("breaker_mid", (float(bb_high) + float(bb_low)) / 2.0, f"timeframes.{tf}.breaker_blocks[{i}].midpoint")

            # FVG — production MSOs use ``top``/``bottom`` (sometimes ``high``/``low``)
            for i, fvg in enumerate(block.get("fair_value_gaps") or []):
                if isinstance(fvg, Mapping):
                    fvg_high = fvg.get("top", fvg.get("high"))
                    fvg_low = fvg.get("bottom", fvg.get("low"))
                    fvg_mid = fvg.get("midpoint")
                    ps.add("fvg_high", fvg_high, f"timeframes.{tf}.fair_value_gaps[{i}].top")
                    ps.add("fvg_low", fvg_low, f"timeframes.{tf}.fair_value_gaps[{i}].bottom")
                    if isinstance(fvg_mid, (int, float)):
                        ps.add("fvg_mid", fvg_mid, f"timeframes.{tf}.fair_value_gaps[{i}].midpoint")
                    elif isinstance(fvg_high, (int, float)) and isinstance(fvg_low, (int, float)):
                        ps.add("fvg_mid", (float(fvg_high) + float(fvg_low)) / 2.0, f"timeframes.{tf}.fair_value_gaps[{i}].midpoint")

            # Swings
            for i, sw in enumerate(block.get("swings") or []):
                if isinstance(sw, Mapping):
                    typ = (sw.get("type") or "").lower()
                    price = sw.get("price")
                    if "high" in typ:
                        ps.add("swing_high", price, f"timeframes.{tf}.swings[{i}].price(high)")
                    elif "low" in typ:
                        ps.add("swing_low", price, f"timeframes.{tf}.swings[{i}].price(low)")

            # Last candle close → current price candidate
            candles = block.get("candles") or []
            if candles and isinstance(candles[-1], Mapping):
                last = candles[-1]
                ps.add("current_price", last.get("close"), f"timeframes.{tf}.candles[-1].close")
                # Also add the candle range so a tight tolerance still flags
                ps.add("current_price", last.get("high"), f"timeframes.{tf}.candles[-1].high")
                ps.add("current_price", last.get("low"), f"timeframes.{tf}.candles[-1].low")

    # --- Session levels ---
    sl = mso.get("session_levels") or {}
    if isinstance(sl, Mapping):
        # Each session level has both a "polarity" (high/low) and pushes to
        # multiple roles so the AI's role-claim has a chance to match.
        SESSION_LEVEL_POLARITY = {
            "asian_high": "high",
            "asian_low": "low",
            "pdh": "high",   # previous day's high
            "pdl": "low",    # previous day's low
            "session_high": "high",
            "session_low": "low",
            "london_high": "high",
            "london_low": "low",
        }
        for key, polarity in SESSION_LEVEL_POLARITY.items():
            v = sl.get(key)
            if isinstance(v, (int, float)) and not _is_zero_or_nan(v):
                if polarity == "high":
                    ps.add("swing_high", v, f"session_levels.{key}")
                    ps.add("sweep_price", v, f"session_levels.{key}")
                    ps.add("liquidity_high", v, f"session_levels.{key}")
                else:
                    ps.add("swing_low", v, f"session_levels.{key}")
                    ps.add("sweep_price", v, f"session_levels.{key}")
                    ps.add("liquidity_low", v, f"session_levels.{key}")

    # --- Equal highs / lows (also liquidity proxies) ---
    for key, role in (("equal_highs", "swing_high"), ("equal_lows", "swing_low")):
        for i, lvl in enumerate(mso.get(key) or []):
            if isinstance(lvl, Mapping):
                v = lvl.get("price") or lvl.get("level")
                if isinstance(v, (int, float)):
                    ps.add(role, v, f"{key}[{i}].price")

    return ps


def build_ohlcv_price_set(
    ohlcv_window: Sequence[Mapping[str, Any]],
    *,
    label_prefix: str = "ohlcv",
) -> MSOPriceSet:
    """Build a coarse price set from raw OHLCV when no MSO is available.

    Used for live_evaluations rows. Each candle contributes its high
    and low as ``swing_high``/``swing_low`` candidates and its close as
    a ``current_price`` candidate. We tag classification as
    ``accurate`` if a cited price falls within tolerance of any
    candle's high/low/close in the lookback window — this is the
    coarse approximation the brief calls out (the AI's MSO contained
    these candles by construction, so any cited price not inside any
    candle's range is HIGH-confidence hallucination).
    """
    ps = MSOPriceSet()
    for i, c in enumerate(ohlcv_window):
        if not isinstance(c, Mapping):
            continue
        h, l, cl = c.get("high"), c.get("low"), c.get("close")
        if isinstance(h, (int, float)):
            ps.add("swing_high", h, f"{label_prefix}[{i}].high")
            ps.add("any", h, f"{label_prefix}[{i}].high")
        if isinstance(l, (int, float)):
            ps.add("swing_low", l, f"{label_prefix}[{i}].low")
            ps.add("any", l, f"{label_prefix}[{i}].low")
        if isinstance(cl, (int, float)):
            ps.add("current_price", cl, f"{label_prefix}[{i}].close")
            ps.add("any", cl, f"{label_prefix}[{i}].close")
    return ps


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------

#: Role equivalence map — semantically-equivalent role aliases.
#: When the AI cites a role NOT in the MSO bucket directly, we accept
#: matches in the equivalent buckets as ACCURATE (instead of mis-).
#:
#: Justification:
#: * ``protected_swing`` is an AI-named role for what is structurally a
#:   ``swing_high`` or ``swing_low`` in the MSO.
#: * ``equilibrium`` (50% level between recent swings) often falls inside
#:   the OB body or close to it; matching ``ob_mid`` / ``ob_body`` is fair.
#: * ``ob_body`` (open/close from the OB candle body) is interchangeable
#:   with ``ob_high``/``ob_low`` for entry-derivation purposes.
#: * ``fvg_mid`` should match ``fvg_high``/``fvg_low``; ditto ``breaker_mid``.
ROLE_EQUIVALENT_BUCKETS: Dict[str, Tuple[str, ...]] = {
    "protected_swing": ("swing_high", "swing_low"),
    "equilibrium": ("ob_mid", "ob_body", "fvg_mid", "breaker_mid"),
    "ob_body": ("ob_high", "ob_low", "ob_mid"),
    "fvg_mid": ("fvg_high", "fvg_low"),
    "breaker_mid": ("breaker_high", "breaker_low"),
    # A "sweep_price" is structurally a swing high/low (or a session
    # extreme like PDH / PDL) — the AI is consuming the same MSO field
    # under a different label, so swing match is ACCURATE not misatt.
    "sweep_price": ("swing_high", "swing_low", "liquidity_high", "liquidity_low"),
}


def classify_price(
    price: float,
    label: str,
    mso_raw_data: Mapping[str, Any],
    tolerance_ticks: int = DEFAULT_TOLERANCE_TICKS,
    *,
    symbol: Optional[str] = None,
    mso_price_set: Optional[MSOPriceSet] = None,
) -> Classification:
    """Classify a single AI-cited price.

    *price* is the AI's value; *label* is the AI's claimed role
    (``"ob_high"`` / ``"current_price"`` / ...). *mso_raw_data* is the
    MSO the AI was given (or a stand-in derived from OHLCV).

    Returns one of ``"accurate"`` / ``"hallucinated"`` / ``"misattributed"``.

    *symbol* drives tick-size lookup. *mso_price_set* is an optional
    pre-built lookup; pass it for batched calls to avoid rebuilding
    per price.
    """
    if mso_price_set is None:
        mso_price_set = build_mso_price_set(mso_raw_data)

    if symbol is None:
        symbol = ""
        try:
            symbol = mso_raw_data.get("symbol", "") or ""  # type: ignore[union-attr]
        except AttributeError:
            symbol = ""

    tick = _tick_size(symbol)
    tolerance = tolerance_ticks * tick

    # Try same-role match first
    same_role_values = mso_price_set.by_role.get(label, [])
    for v, _fld in same_role_values:
        if abs(price - v) <= tolerance:
            return "accurate"

    # Equivalent-role match — semantically-OK substitutions (defined in
    # ROLE_EQUIVALENT_BUCKETS).
    for equiv_role in ROLE_EQUIVALENT_BUCKETS.get(label, ()):
        for v, _fld in mso_price_set.by_role.get(equiv_role, []):
            if abs(price - v) <= tolerance:
                return "accurate"

    # Try a "neighbour" role list — entry_price, stop_loss, take_profit
    # don't appear directly in MSO, so for those we look at OB/swing/FVG
    # bands for entry; OB beyond / swing beyond for SL; opposing levels
    # for TP. We treat ANY MSO price within tolerance as accurate for
    # these synthesized roles (the AI is allowed to derive them).
    if label in ("entry_price", "stop_loss", "take_profit"):
        for v, _r, _fld in mso_price_set.all_values():
            if abs(price - v) <= tolerance:
                return "accurate"

    # Look across ALL roles. If found in some other role: misattributed.
    # If found nowhere: hallucinated.
    for v, role, _fld in mso_price_set.all_values():
        if abs(price - v) <= tolerance:
            return "misattributed"

    return "hallucinated"


def classify_price_detailed(
    cited: CitedPrice,
    mso_price_set: MSOPriceSet,
    *,
    symbol: str,
    tolerance_ticks: int,
) -> PriceClassification:
    """Same as :func:`classify_price` but returns a rich record.

    Useful for caller-side debugging / per-row JSONL output.
    """
    tick = _tick_size(symbol)
    tolerance = tolerance_ticks * tick

    # Same-role match first (best evidence)
    same_role_values = mso_price_set.by_role.get(cited.role, [])
    best_same_role: Optional[Tuple[float, str, float]] = None
    for v, fld in same_role_values:
        d = abs(cited.value - v)
        if best_same_role is None or d < best_same_role[2]:
            best_same_role = (v, fld, d)
    if best_same_role and best_same_role[2] <= tolerance:
        return PriceClassification(
            role=cited.role,
            value=cited.value,
            source_field=cited.source_field,
            classification="accurate",
            matched_mso_field=best_same_role[1],
            matched_mso_value=best_same_role[0],
            delta_ticks=best_same_role[2] / tick if tick > 0 else None,
        )

    # Equivalent-role match — semantically-OK substitutions
    equivalents = ROLE_EQUIVALENT_BUCKETS.get(cited.role, ())
    for equiv_role in equivalents:
        for v, fld in mso_price_set.by_role.get(equiv_role, []):
            d = abs(cited.value - v)
            if d <= tolerance:
                return PriceClassification(
                    role=cited.role,
                    value=cited.value,
                    source_field=cited.source_field,
                    classification="accurate",
                    matched_mso_field=fld,
                    matched_mso_value=v,
                    delta_ticks=d / tick if tick > 0 else None,
                    note=f"equivalent-role match against {equiv_role}",
                )

    # Synthesized roles: entry/sl/tp can match any MSO price band
    if cited.role in ("entry_price", "stop_loss", "take_profit"):
        best_any: Optional[Tuple[float, str, str, float]] = None
        for v, role, fld in mso_price_set.all_values():
            d = abs(cited.value - v)
            if best_any is None or d < best_any[3]:
                best_any = (v, role, fld, d)
        if best_any and best_any[3] <= tolerance:
            return PriceClassification(
                role=cited.role,
                value=cited.value,
                source_field=cited.source_field,
                classification="accurate",
                matched_mso_field=best_any[2],
                matched_mso_value=best_any[0],
                delta_ticks=best_any[3] / tick if tick > 0 else None,
                note=f"derived-role match against role={best_any[1]}",
            )

    # Cross-role match → misattributed
    best_other: Optional[Tuple[float, str, str, float]] = None
    for v, role, fld in mso_price_set.all_values():
        if role == cited.role:
            continue
        d = abs(cited.value - v)
        if best_other is None or d < best_other[3]:
            best_other = (v, role, fld, d)
    if best_other and best_other[3] <= tolerance:
        return PriceClassification(
            role=cited.role,
            value=cited.value,
            source_field=cited.source_field,
            classification="misattributed",
            matched_mso_field=best_other[2],
            matched_mso_value=best_other[0],
            delta_ticks=best_other[3] / tick if tick > 0 else None,
            note=f"price exists in MSO but at role={best_other[1]}",
        )

    # No match anywhere → hallucinated
    return PriceClassification(
        role=cited.role,
        value=cited.value,
        source_field=cited.source_field,
        classification="hallucinated",
        matched_mso_field=None,
        matched_mso_value=None,
        delta_ticks=None,
    )


# ---------------------------------------------------------------------------
# Record loaders
# ---------------------------------------------------------------------------


def _iter_trade_records(records_dir: Path) -> Iterator[Tuple[Path, Mapping[str, Any]]]:
    """Yield (file_path, record_dict) for every trade record JSON."""
    if not records_dir.exists():
        return
    for symbol_dir in sorted(p for p in records_dir.iterdir() if p.is_dir()):
        for json_path in sorted(symbol_dir.glob("*.json")):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    rec = json.load(f)
                yield json_path, rec
            except Exception as exc:
                logger.warning("Skipping unreadable trade record %s: %s", json_path, exc)


def _iter_live_evaluations(evals_dir: Path) -> Iterator[Tuple[Path, Mapping[str, Any]]]:
    """Yield (file_path, eval_dict) for every JSONL evaluation row."""
    if not evals_dir.exists():
        return
    for symbol_dir in sorted(p for p in evals_dir.iterdir() if p.is_dir()):
        for jsonl_path in sorted(symbol_dir.glob("*.jsonl")):
            try:
                with open(jsonl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        yield jsonl_path, rec
            except Exception as exc:
                logger.warning("Skipping unreadable evaluations file %s: %s", jsonl_path, exc)


# ---------------------------------------------------------------------------
# Period assignment
# ---------------------------------------------------------------------------


#: Period-splitting strategy. ``"calendar_half"`` (default) maps Jan-Jun
#: to H1-YYYY and Jul-Dec to H2-YYYY. ``"intra_april_2026"`` (F8) maps
#: Apr 5-15 → ``H1-2026`` and Apr 16-30 → ``H2-2026`` so the H1→H2
#: hallucination delta is computable on the April-only corpus produced
#: by the reconstruction pipeline (
#: :mod:`scripts.research.reconstruct_h1_evaluations`).
#:
#: Override via ``measure_from_disk(period_strategy=...)`` or the public
#: API. The default behavior is unchanged — F8 only adds the new
#: strategy without touching the calendar-half logic shipped in B7-v1.
PeriodStrategy = Literal["calendar_half", "intra_april_2026"]
DEFAULT_PERIOD_STRATEGY: PeriodStrategy = "calendar_half"


def _assign_period(
    candle_time_iso: Optional[str],
    *,
    strategy: PeriodStrategy = DEFAULT_PERIOD_STRATEGY,
) -> Tuple[Optional[str], Optional[str]]:
    """Return (year_month, half_year_label) for a given timestamp.

    Half-year split is calendar-month based by default: Jan-Jun → H1-YYYY,
    Jul-Dec → H2-YYYY. Per the brief and the H2-2026 decay context
    (memory ``project_a1_dumb_baseline_verdict_2026-04-26``),
    H1-2026 and H2-2026 are the canonical aggregation buckets.

    With ``strategy="intra_april_2026"`` (F8), April 2026 is split mid-
    month so the H1→H2 delta can be computed on April-only data. This
    matches the empirical decay window observed in live trading: early-
    April CANDIDATEs perform meaningfully differently from late-April
    CANDIDATEs (memory ``project_b7_hallucination_per_instrument_2026-04-27``).

    Returns (None, None) when timestamp is unparsable.
    """
    if not candle_time_iso:
        return None, None
    parsed = _normalize_to_utc_minute(candle_time_iso)
    if parsed is None:
        return None, None
    year = parsed.year
    month = parsed.month

    if strategy == "intra_april_2026" and year == 2026 and month == 4:
        # Apr 5-15 = H1; Apr 16-30 = H2. Pre-Apr-5 records (none on
        # disk at F8 ship time) fall through to calendar logic.
        if parsed.day <= 15:
            return f"{year:04d}-{month:02d}", "H1-2026"
        else:
            return f"{year:04d}-{month:02d}", "H2-2026"

    half = "H1" if month <= 6 else "H2"
    return f"{year:04d}-{month:02d}", f"{half}-{year:04d}"


# ---------------------------------------------------------------------------
# Per-record check builders
# ---------------------------------------------------------------------------


def _check_trade_record(
    rec: Mapping[str, Any],
    *,
    tolerance_ticks: int,
    period_strategy: PeriodStrategy = DEFAULT_PERIOD_STRATEGY,
) -> Optional[EvaluationCheck]:
    """Run hallucination check on a single trade_records JSON.

    Returns None if the record is unusable (no MSO, no AI response).
    """
    metadata = rec.get("metadata") or {}
    symbol = _canonical_symbol(metadata.get("symbol", ""))
    candle_time = metadata.get("candle_time")

    mso = rec.get("mso") or {}
    ai_response = rec.get("ai_response") or {}

    if not isinstance(mso, Mapping) or not mso:
        return None
    if not isinstance(ai_response, Mapping) or not ai_response:
        return None

    period_month, period_half = _assign_period(candle_time, strategy=period_strategy)

    cited = parse_ai_prices(ai_response)
    if not cited:
        return None

    mso_ps = build_mso_price_set(mso)

    classifications = [
        classify_price_detailed(c, mso_ps, symbol=symbol, tolerance_ticks=tolerance_ticks)
        for c in cited
    ]

    decision_pipeline = rec.get("decision_pipeline") or {}
    framework = decision_pipeline.get("ai_framework") or ai_response.get("framework")
    decision = decision_pipeline.get("ai_decision") or ai_response.get("decision")

    # realized R join — exit.r_multiple is canonical
    r_mult = None
    for path in (
        ("decision_pipeline", "final_outcome", "r_multiple"),
        ("exit", "r_multiple"),
    ):
        cur: Any = rec
        ok = True
        for key in path:
            if isinstance(cur, Mapping):
                cur = cur.get(key)
            else:
                ok = False
                break
        if ok and isinstance(cur, (int, float)):
            r_mult = float(cur)
            break

    return EvaluationCheck(
        record_source="trade_records",
        symbol=symbol,
        candle_time_utc=str(candle_time) if candle_time else None,
        period_month=period_month,
        period_half=period_half,
        decision=decision,
        framework=framework,
        realized_r=r_mult,
        classifications=classifications,
    )


def _check_live_evaluation(
    rec: Mapping[str, Any],
    *,
    tolerance_ticks: int,
    ohlcv_provider: Optional["OHLCVLookbackProvider"] = None,
    period_strategy: PeriodStrategy = DEFAULT_PERIOD_STRATEGY,
) -> Optional[EvaluationCheck]:
    """Run hallucination check on a single live_evaluations row.

    Without an MSO, we use OHLCV in a lookback window as a coarse
    stand-in. If no OHLCV is available, classifications are emitted
    with ``classification=None`` (excluded from rate aggregations).
    """
    symbol = _canonical_symbol(rec.get("symbol", ""))
    candle_time = rec.get("candle_time")
    period_month, period_half = _assign_period(candle_time, strategy=period_strategy)

    cited = parse_ai_prices(rec)
    if not cited:
        return None

    decision = rec.get("decision")
    framework = rec.get("framework")

    # OHLCV-derived MSO stand-in
    classifications: List[PriceClassification] = []
    if ohlcv_provider is not None:
        window = ohlcv_provider.get_window(symbol, candle_time)
        ohlcv_ps = build_ohlcv_price_set(window) if window else MSOPriceSet()
        for c in cited:
            classifications.append(_classify_price_against_ohlcv(c, ohlcv_ps, symbol=symbol, tolerance_ticks=tolerance_ticks))
    else:
        for c in cited:
            classifications.append(PriceClassification(
                role=c.role,
                value=c.value,
                source_field=c.source_field,
                classification=None,
                note="no MSO available",
            ))

    return EvaluationCheck(
        record_source="live_evaluations",
        symbol=symbol,
        candle_time_utc=str(candle_time) if candle_time else None,
        period_month=period_month,
        period_half=period_half,
        decision=decision,
        framework=framework,
        classifications=classifications,
    )


def _classify_price_against_ohlcv(
    cited: CitedPrice,
    ohlcv_ps: MSOPriceSet,
    *,
    symbol: str,
    tolerance_ticks: int,
) -> PriceClassification:
    """Classify against OHLCV-derived stand-in price set.

    With OHLCV alone, we cannot distinguish "OB top" from "swing high"
    — the candle high is BOTH. So we collapse the answer space to:

    * **accurate** — price matches some candle high/low/close within tolerance
    * **hallucinated** — price matches NO candle in the lookback window

    Misattribution is impossible to detect without role labels in the
    stand-in, so we never emit ``misattributed`` for live_evaluations
    rows. This is documented in the report alongside the rate column.
    """
    tick = _tick_size(symbol)
    tolerance = tolerance_ticks * tick

    # current_price → check candle close/range
    if cited.role == "current_price":
        candidates = ohlcv_ps.by_role.get("current_price", []) + ohlcv_ps.by_role.get("any", [])
        for v, fld in candidates:
            if abs(cited.value - v) <= tolerance:
                return PriceClassification(
                    role=cited.role,
                    value=cited.value,
                    source_field=cited.source_field,
                    classification="accurate",
                    matched_mso_field=fld,
                    matched_mso_value=v,
                    delta_ticks=abs(cited.value - v) / tick if tick > 0 else None,
                )
        return PriceClassification(
            role=cited.role,
            value=cited.value,
            source_field=cited.source_field,
            classification="hallucinated",
            note="no OHLCV candle close/high/low matched",
        )

    # All other roles — we only check existence, not role-fidelity
    for v, _role, fld in ohlcv_ps.all_values():
        if abs(cited.value - v) <= tolerance:
            return PriceClassification(
                role=cited.role,
                value=cited.value,
                source_field=cited.source_field,
                classification="accurate",
                matched_mso_field=fld,
                matched_mso_value=v,
                delta_ticks=abs(cited.value - v) / tick if tick > 0 else None,
                note="OHLCV-only stand-in: role-fidelity not enforced",
            )

    return PriceClassification(
        role=cited.role,
        value=cited.value,
        source_field=cited.source_field,
        classification="hallucinated",
        note="cited price not in OHLCV lookback window",
    )


# ---------------------------------------------------------------------------
# OHLCV lookback provider (for live_evaluations stand-in)
# ---------------------------------------------------------------------------


@dataclass
class OHLCVLookbackProvider:
    """Lazy CSV reader serving a candle-window for (symbol, candle_time).

    Default lookback is 168 H1 candles (~7 days) to match
    ``DEFAULT_LOOKBACKS["H1"]`` in the production data ingestion path.
    We use the H1 series as the most informative lookback for most
    role-types (OB/breaker formations are H1; sweep_price typically
    matches H1 swings).
    """

    ohlcv_dir: Path = DEFAULT_OHLCV_DIR
    timeframe: str = "H1"
    lookback_bars: int = 168
    _cache: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    def _load(self, symbol: str) -> List[Dict[str, Any]]:
        canonical = _canonical_symbol(symbol)
        stem = OHLCV_STEM.get(canonical, canonical)
        if stem in self._cache:
            return self._cache[stem]
        csv_path = self.ohlcv_dir / f"{stem}_{self.timeframe}.csv"
        if not csv_path.exists():
            self._cache[stem] = []
            return []
        rows: List[Dict[str, Any]] = []
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                header = f.readline().strip().split(",")
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) != len(header):
                        continue
                    row = dict(zip(header, parts))
                    try:
                        row["high"] = float(row.get("high", "nan"))
                        row["low"] = float(row.get("low", "nan"))
                        row["close"] = float(row.get("close", "nan"))
                        row["open"] = float(row.get("open", "nan"))
                    except (TypeError, ValueError):
                        continue
                    rows.append(row)
        except OSError:
            rows = []
        self._cache[stem] = rows
        return rows

    def get_window(
        self,
        symbol: str,
        candle_time: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Return up to ``lookback_bars`` candles ending AT or BEFORE candle_time."""
        if not candle_time:
            return []
        target = _normalize_to_utc_minute(candle_time)
        if target is None:
            return []
        rows = self._load(symbol)
        if not rows:
            return []

        window: List[Dict[str, Any]] = []
        for row in rows:
            t_str = row.get("time", "")
            try:
                # MT5 CSVs use "YYYY-MM-DD HH:MM:SS" (no tz)
                t_parsed = dt.datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
                t_parsed = t_parsed.replace(tzinfo=dt.timezone.utc)
            except (ValueError, TypeError):
                continue
            if t_parsed <= target:
                window.append(row)
            else:
                break  # rows are already chronologically sorted
        return window[-self.lookback_bars:] if window else []


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------


def measure_hallucination_rate(
    evaluations: Sequence[Mapping[str, Any]],
    tolerance_ticks: int = DEFAULT_TOLERANCE_TICKS,
    period_strategy: PeriodStrategy = DEFAULT_PERIOD_STRATEGY,
) -> HallucinationReport:
    """Compute hallucination rate across a sequence of evaluation dicts.

    Each *evaluation* dict should follow the ``trade_records``-style
    shape (with ``mso`` + ``ai_response`` blocks) for full
    classification, OR the live_evaluations flat shape (which produces
    classification=None rows that are excluded from rates).

    This is the canonical entry point for the test suite. The CLI
    driver in :mod:`scripts.research.run_b7_hallucination` adds
    file-system iteration on top.
    """
    rows: List[EvaluationCheck] = []
    n_with = 0

    for ev in evaluations:
        if not isinstance(ev, Mapping):
            continue
        if "mso" in ev and "ai_response" in ev:
            check = _check_trade_record(
                ev, tolerance_ticks=tolerance_ticks, period_strategy=period_strategy,
            )
        elif "overall_reasoning" in ev or "no_trade_reason" in ev or "decision" in ev:
            check = _check_live_evaluation(
                ev, tolerance_ticks=tolerance_ticks, period_strategy=period_strategy,
            )
        else:
            check = None

        if check is None:
            continue
        rows.append(check)
        if any(c.classification is not None for c in check.classifications):
            n_with += 1

    return _build_report(rows, tolerance_ticks=tolerance_ticks, n_records_scanned=len(evaluations))


def measure_hallucination_rate_by_role_class(
    evaluations: Sequence[Mapping[str, Any]],
    tolerance_ticks: int = DEFAULT_TOLERANCE_TICKS,
) -> Dict[str, Dict[str, HallucinationRateRow]]:
    """Per-instrument × per-role-class hallucination rate.

    Returns a nested dict::

        {
            "GBPUSD": {
                "MSO_GROUNDED":   HallucinationRateRow(...),
                "FORWARD_DERIVED":HallucinationRateRow(...),
                "AMBIGUOUS":      HallucinationRateRow(...),
            },
            ...
        }

    Missing role classes for an instrument are simply absent from the
    inner dict (they had zero classifications). The same data is
    available on :attr:`HallucinationReport.by_instrument_role_class`
    in flat form; this helper is a convenience for callers who want
    direct keyed access.

    The rates emitted here are the apples-to-apples grounding-failure
    metric the F13 brief calls for: the MSO_GROUNDED rate is the
    "real" hallucination rate; FORWARD_DERIVED is informational; the
    sum of n_prices across the three classes equals the v1
    per-instrument n_prices.
    """
    report = measure_hallucination_rate(evaluations, tolerance_ticks=tolerance_ticks)
    out: Dict[str, Dict[str, HallucinationRateRow]] = {}
    for row in report.by_instrument_role_class:
        if row.instrument is None or row.role_class is None:
            continue
        out.setdefault(row.instrument, {})[row.role_class] = row
    return out


def measure_from_disk(
    *,
    trade_records_dir: Path = DEFAULT_TRADE_RECORDS_DIR,
    live_evaluations_dir: Optional[Path] = DEFAULT_LIVE_EVALUATIONS_DIR,
    ohlcv_dir: Path = DEFAULT_OHLCV_DIR,
    tolerance_ticks: int = DEFAULT_TOLERANCE_TICKS,
    include_live_evaluations: bool = True,
    period_strategy: PeriodStrategy = DEFAULT_PERIOD_STRATEGY,
    extra_live_evaluations_dirs: Sequence[Path] = (),
) -> HallucinationReport:
    """Scan disk and run the full B7 measurement.

    *trade_records_dir* is the precise source — we always include it.
    *live_evaluations_dir* is the broad source — opt-in via
    ``include_live_evaluations``. The reason it's opt-in: live
    evaluations produce coarse OHLCV-only classifications that are
    valuable but cannot detect misattribution; mixing them in the
    same numerator without disclosure dilutes the precision arm. The
    CLI emits both arms separately.

    *extra_live_evaluations_dirs* (F8) lets the caller union additional
    JSONL corpora with the canonical one — used by the F8 H1 baseline
    reconstruction to fold the reconstructed records into the same
    rate computation. Each dir is iterated identically to
    *live_evaluations_dir*.

    *period_strategy* controls the H1/H2 partition; see
    :func:`_assign_period` for the canonical shapes.
    """
    rows: List[EvaluationCheck] = []
    scanned = 0

    # Precise arm
    for path, rec in _iter_trade_records(trade_records_dir):
        scanned += 1
        check = _check_trade_record(
            rec, tolerance_ticks=tolerance_ticks, period_strategy=period_strategy,
        )
        if check is not None:
            rows.append(check)

    # Coarse arm
    if include_live_evaluations and live_evaluations_dir:
        ohlcv_provider = OHLCVLookbackProvider(ohlcv_dir=ohlcv_dir)
        live_dirs = [live_evaluations_dir, *extra_live_evaluations_dirs]
        for d in live_dirs:
            if d is None:
                continue
            for path, rec in _iter_live_evaluations(d):
                scanned += 1
                check = _check_live_evaluation(
                    rec, tolerance_ticks=tolerance_ticks,
                    ohlcv_provider=ohlcv_provider,
                    period_strategy=period_strategy,
                )
                if check is not None:
                    rows.append(check)

    return _build_report(rows, tolerance_ticks=tolerance_ticks, n_records_scanned=scanned)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _build_report(
    rows: List[EvaluationCheck],
    *,
    tolerance_ticks: int,
    n_records_scanned: int,
) -> HallucinationReport:
    """Build the aggregate :class:`HallucinationReport` from per-row checks.

    Always populates the v1 (per-instrument, per-period, …) aggregations
    AND the v2 (per-instrument × per-role-class, per-instrument
    MSO_GROUNDED-only) aggregations. v2 fields are additive — callers
    that only consume v1 fields are unaffected.
    """

    # Aggregation buckets
    by_inst: Dict[str, HallucinationRateRow] = {}
    by_inst_period: Dict[Tuple[str, str], HallucinationRateRow] = {}
    by_inst_month: Dict[Tuple[str, str], HallucinationRateRow] = {}
    by_inst_framework: Dict[Tuple[str, str], HallucinationRateRow] = {}
    by_role: Dict[str, HallucinationRateRow] = {}
    # F13 — per-instrument × per-role-class aggregation
    by_inst_role_class: Dict[Tuple[str, str], HallucinationRateRow] = {}
    # Track unique evaluations contributing per (instrument, role_class)
    # so n_evaluations reflects "this many evals had at least one
    # classification in this role class"; rates remain price-weighted.
    irc_eval_ids: Dict[Tuple[str, str], set] = {}

    n_with = 0
    for eval_idx, r in enumerate(rows):
        non_none = [c for c in r.classifications if c.classification is not None]
        if non_none:
            n_with += 1

        inst_key = r.symbol or "?"
        inst_row = by_inst.setdefault(inst_key, HallucinationRateRow(
            key=inst_key, instrument=inst_key, period=None, framework=None, decision=None,
        ))
        inst_row.n_evaluations += 1

        period_key = r.period_half or "unknown_half"
        ip_row_key = (inst_key, period_key)
        ip_row = by_inst_period.setdefault(ip_row_key, HallucinationRateRow(
            key=f"{inst_key}|{period_key}", instrument=inst_key,
            period=period_key, framework=None, decision=None,
        ))
        ip_row.n_evaluations += 1

        month_key = r.period_month or "unknown_month"
        im_row_key = (inst_key, month_key)
        im_row = by_inst_month.setdefault(im_row_key, HallucinationRateRow(
            key=f"{inst_key}|{month_key}", instrument=inst_key,
            period=month_key, framework=None, decision=None,
        ))
        im_row.n_evaluations += 1

        fw_key = r.framework or "?"
        if_row_key = (inst_key, fw_key)
        if_row = by_inst_framework.setdefault(if_row_key, HallucinationRateRow(
            key=f"{inst_key}|{fw_key}", instrument=inst_key,
            period=None, framework=fw_key, decision=None,
        ))
        if_row.n_evaluations += 1

        for c in r.classifications:
            if c.classification is None:
                continue
            for row in (inst_row, ip_row, im_row, if_row):
                row.n_prices += 1
                if c.classification == "accurate":
                    row.n_accurate += 1
                elif c.classification == "hallucinated":
                    row.n_hallucinated += 1
                elif c.classification == "misattributed":
                    row.n_misattributed += 1

            role_row = by_role.setdefault(c.role, HallucinationRateRow(
                key=c.role, instrument=None, period=None, framework=None, decision=None,
            ))
            role_row.n_prices += 1
            if c.classification == "accurate":
                role_row.n_accurate += 1
            elif c.classification == "hallucinated":
                role_row.n_hallucinated += 1
            elif c.classification == "misattributed":
                role_row.n_misattributed += 1

            # F13 — per-instrument × per-role-class aggregation
            rc = c.role_class or role_class_of(c.role)
            irc_key = (inst_key, rc)
            irc_row = by_inst_role_class.setdefault(irc_key, HallucinationRateRow(
                key=f"{inst_key}|{rc}", instrument=inst_key,
                period=None, framework=None, decision=None,
                role_class=rc,
            ))
            irc_row.n_prices += 1
            if c.classification == "accurate":
                irc_row.n_accurate += 1
            elif c.classification == "hallucinated":
                irc_row.n_hallucinated += 1
            elif c.classification == "misattributed":
                irc_row.n_misattributed += 1
            irc_eval_ids.setdefault(irc_key, set()).add(eval_idx)

    # H1 → H2 delta (across all instruments)
    h1_total_h: Dict[str, Tuple[int, int]] = {}  # period_half → (n_hallucinated, n_prices)
    for r in rows:
        if r.period_half is None:
            continue
        nh, np_ = h1_total_h.get(r.period_half, (0, 0))
        for c in r.classifications:
            if c.classification is None:
                continue
            np_ += 1
            if c.classification == "hallucinated":
                nh += 1
        h1_total_h[r.period_half] = (nh, np_)

    h1_h2_delta: Optional[float] = None
    h1 = h1_total_h.get("H1-2026")
    h2 = h1_total_h.get("H2-2026")
    if h1 and h1[1] > 0 and h2 and h2[1] > 0:
        h1_pct = 100.0 * h1[0] / h1[1]
        h2_pct = 100.0 * h2[0] / h2[1]
        h1_h2_delta = h2_pct - h1_pct

    # Most-hallucinated role
    most_role: Optional[str] = None
    worst = -1.0
    for role, row in by_role.items():
        if row.n_prices < 5:
            continue  # require min sample size for "most" claim
        pct = 100.0 * row.n_hallucinated / row.n_prices
        if pct > worst:
            worst = pct
            most_role = role

    # Backfill n_evaluations on the role-class rows from the eval-id set
    for k, ids in irc_eval_ids.items():
        if k in by_inst_role_class:
            by_inst_role_class[k].n_evaluations = len(ids)

    by_inst_role_class_list = sorted(by_inst_role_class.values(), key=lambda r: r.key)
    by_inst_mso_grounded_list = [
        r for r in by_inst_role_class_list if r.role_class == "MSO_GROUNDED"
    ]

    return HallucinationReport(
        harness_version=HARNESS_VERSION,
        tolerance_ticks=tolerance_ticks,
        n_records_scanned=n_records_scanned,
        n_records_with_classifications=n_with,
        rows=rows,
        by_instrument=sorted(by_inst.values(), key=lambda r: r.key),
        by_instrument_period=sorted(by_inst_period.values(), key=lambda r: r.key),
        by_instrument_month=sorted(by_inst_month.values(), key=lambda r: r.key),
        by_instrument_framework=sorted(by_inst_framework.values(), key=lambda r: r.key),
        by_role=sorted(by_role.values(), key=lambda r: r.key),
        by_instrument_role_class=by_inst_role_class_list,
        by_instrument_mso_grounded=by_inst_mso_grounded_list,
        h1_h2_delta_pp=h1_h2_delta,
        most_hallucinated_role=most_role,
    )
