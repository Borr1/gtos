"""Post-hoc confidence scoring based on empirical reasoning text features.

Replaces the broken confidence_score (105/111 trades scored 80) with
metrics derived from the vertical analysis of 101 ob_retest trades.

Key findings from the analysis:
- price_level_count >= 8: 75.0% WR vs 57.6% WR (delta +17.4%)
- hesitation_score <= 2: 73.2% WR vs 60.0% WR (delta +13.2%)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


# ── Phrase lists (from vertical analysis) ────────────────────────────────

HESITATION_PHRASES: list[str] = [
    r"\bhowever\b",
    r"\balthough\b",
    r"\bbut\s",
    r"\bconcern",
    r"\bunclear\b",
    r"\buncertain\b",
    r"\bambiguous\b",
    r"\bmixed\b",
    r"\bchoppy\b",
    r"\branging\b",
    r"\bmoderate\b",
    r"\bmedium\b",
    r"\bonly\b",
    r"\bbarely\b",
    r"\bminimal\b",
    r"\bweak\b",
    r"\bthin\b",
    r"\bshallow\b",
    r"\brisk\b",
]

QUALITY_PHRASES: list[str] = [
    r"strong displacement",
    r"clean displacement",
    r"decisive displacement",
    r"clear bos",
    r"confirmed bos",
    r"strong bos",
    r"clean structure",
    r"clear structure",
    r"multiple confluences",
    r"strong confluence",
    r"session level swept",
    r"liquidity swept",
    r"sweep confirmed",
    r"strong rejection",
    r"decisive break",
]

# Default price regex: gold — 4 digits, decimal, 1-2 digits (e.g. 2882.35, 3120.5)
_PRICE_PATTERN = re.compile(r"\b(\d{4}\.\d{1,2})\b")
_PRICE_RANGE = (1500.0, 6000.0)


# ── Output model ─────────────────────────────────────────────────────────

class ConfidenceMetrics(BaseModel):
    """Empirical confidence metrics extracted from PA reasoning."""

    price_level_count: int = Field(
        description="Count of distinct XAUUSD price levels in the reasoning JSON"
    )
    hesitation_score: int = Field(
        description="Count of hedging/uncertainty phrases in reasoning text"
    )
    quality_score: int = Field(
        description="Count of quality/confidence phrases in reasoning text"
    )
    word_count: int = Field(
        description="Total words in overall_reasoning field"
    )
    confidence_grade: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="HIGH if price_level_count>=8 AND hesitation_score<=2, "
        "MEDIUM if one condition met, LOW if neither"
    )
    position_size_multiplier: float = Field(
        description="1.0 for HIGH, 0.75 for MEDIUM, 0.5 for LOW"
    )


@dataclass(frozen=True)
class ConfidenceFilterMode:
    requested_mode: str
    effective_mode: Literal["shadow", "active"]
    blocked_reason: str | None = None


# ── Scoring logic ────────────────────────────────────────────────────────

def _flatten_text(obj: object) -> str:
    """Recursively extract all string values from a nested dict/list."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return " ".join(_flatten_text(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return " ".join(_flatten_text(item) for item in obj)
    return ""


def _count_patterns(text: str, patterns: list[str]) -> int:
    """Count total matches of regex patterns in text."""
    total = 0
    for pattern in patterns:
        total += len(re.findall(pattern, text, re.IGNORECASE))
    return total


def _count_price_levels(text: str, config: dict | None = None) -> int:
    """Count distinct price levels matching the instrument's price pattern."""
    if config and config.get("confidence"):
        pattern_str = config["confidence"].get("price_regex")
        price_range = config["confidence"].get("price_range", list(_PRICE_RANGE))
        pattern = re.compile(pattern_str) if pattern_str else _PRICE_PATTERN
        lo, hi = price_range[0], price_range[1]
    else:
        pattern = _PRICE_PATTERN
        lo, hi = _PRICE_RANGE

    matches = pattern.findall(text)
    valid = set()
    for m in matches:
        try:
            v = float(m)
            if lo <= v <= hi:
                valid.add(m)
        except ValueError:
            continue
    return len(valid)


def _compute_grade(
    price_level_count: int, hesitation_score: int,
) -> tuple[Literal["HIGH", "MEDIUM", "LOW"], float]:
    """Determine confidence grade and position size multiplier."""
    price_ok = price_level_count >= 8
    hesitation_ok = hesitation_score <= 2

    if price_ok and hesitation_ok:
        return "HIGH", 1.0
    elif price_ok or hesitation_ok:
        return "MEDIUM", 0.75
    else:
        return "LOW", 0.5


def score_confidence(reasoning_json: dict, config: dict | None = None) -> ConfidenceMetrics:
    """Extract empirical confidence metrics from PA reasoning output.

    Args:
        reasoning_json: The full PrimaryAnalysisOutput as a dict,
            OR just the ``reasoning`` sub-object. Both are supported.

    Returns:
        ConfidenceMetrics with all extracted features and the derived grade.
    """
    # Accept either the full PA output or just the reasoning sub-object
    reasoning = reasoning_json.get("reasoning", reasoning_json)

    # Flatten all text from the reasoning structure
    full_text = _flatten_text(reasoning)

    # Extract overall_reasoning specifically for word count
    overall = ""
    if isinstance(reasoning, dict):
        overall = reasoning.get("overall_reasoning", "")

    # Count features
    price_level_count = _count_price_levels(full_text, config)
    hesitation_score = _count_patterns(full_text, HESITATION_PHRASES)
    quality_score = _count_patterns(full_text, QUALITY_PHRASES)
    word_count = len(overall.split()) if overall else 0

    grade, multiplier = _compute_grade(price_level_count, hesitation_score)

    return ConfidenceMetrics(
        price_level_count=price_level_count,
        hesitation_score=hesitation_score,
        quality_score=quality_score,
        word_count=word_count,
        confidence_grade=grade,
        position_size_multiplier=multiplier,
    )


def resolve_confidence_filter_mode(config: dict | None) -> ConfidenceFilterMode:
    """Resolve the confidence filter mode with active-promotion quarantine."""
    config = config or {}
    requested = str(config.get("confidence_filter_mode", "shadow") or "shadow").strip().lower()
    active_policy = str(config.get("confidence_filter_active_policy", "") or "").strip().lower()
    if requested not in {"shadow", "active"}:
        return ConfidenceFilterMode(
            requested_mode=requested,
            effective_mode="shadow",
            blocked_reason="unknown_confidence_filter_mode",
        )
    if requested == "active":
        if active_policy in {
            "disabled_until_new_validated_intra_candidate_signal",
            "killed_by_intra_candidate_evidence",
        }:
            return ConfidenceFilterMode(
                requested_mode=requested,
                effective_mode="shadow",
                blocked_reason="active_confidence_filter_killed_by_intra_candidate_evidence",
            )
        approval = config.get("confidence_filter_active_promotion") or {}
        validated = bool(approval.get("validated", False)) if isinstance(approval, dict) else False
        if not validated:
            return ConfidenceFilterMode(
                requested_mode=requested,
                effective_mode="shadow",
                blocked_reason="active_confidence_filter_requires_validated_promotion",
            )
    return ConfidenceFilterMode(requested_mode=requested, effective_mode=requested)
