"""Proximity Shadow Logger — observation-only.

For every CANDIDATE trade, computes Python-side zone proximity at M15 candle
close time: how far is the current price from the nearest H1 unmitigated OB
in the trade direction?

This is NOT an LLM assessment — it parses the MSO text directly and computes
distance / ATR ratios. The LLM never sees this classification.

Evidence from T7/T8 in-sample (n=104-115):
  inside:      WR ~62-100%  (price at OB edge)
  approaching: WR ~76-78%   (within 2x M15 ATR)
  far:         WR ~61-63%   (> 2x M15 ATR)

Proximity at candle-close != proximity at entry (entries happen at the wick
during the session, not at close). This logger collects live data to test
whether proximity-at-close predicts outcomes.

Promotion criteria (after 50+ trades with 'approaching' or 'inside'):
- Fisher exact: approaching/inside WR vs far WR
- If p < 0.05 and delta_WR > 10pp: promote to hard gate
- If p > 0.20 after 50 trades: kill and document
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/proximity_shadow_log.jsonl"


def parse_mso_zones(user_message: str) -> dict:
    """Extract OBs, ATR, and approximate price from MSO text.

    Returns dict with keys:
      h1_obs, m15_obs: lists of {direction, high, low, timestamp}
      h1_atr, m15_atr: float or None
      current_price_approx: float or None
    """
    result = {
        "h1_obs": [],
        "m15_obs": [],
        "h1_atr": None,
        "m15_atr": None,
        "current_price_approx": None,
    }

    # Current price: M15 candle close from the "Candle:" line, or session H/L midpoint
    # The dynamic context starts with "Candle: <timestamp>" then has Session H/L
    m = re.search(r"Session H/L:\s*([\d.]+)/([\d.]+)", user_message)
    if not m:
        m = re.search(r"London H/L:\s*([\d.]+)/([\d.]+)", user_message)
    if m:
        h, l = float(m.group(1)), float(m.group(2))
        result["current_price_approx"] = (h + l) / 2.0

    def _parse_obs(section_text: str) -> list:
        obs = []
        obs_match = re.search(
            r"Unmitigated OBs \(\d+\):(.*?)(?=Unfilled FVGs|Unretested Breaker|P/D:|Avg body:|## |$)",
            section_text,
            re.DOTALL,
        )
        if not obs_match:
            return obs
        for line in obs_match.group(1).strip().split("\n"):
            # Actual MSO format:
            #   bullish 3210.50-3205.20 body=3208.00-3209.50 evt=BOS (2026-04-10T14:00)
            # Allow any content between the range and the parenthesized timestamp.
            ob_m = re.search(
                r"(bullish|bearish)\s+([\d.]+)-([\d.]+)\s+.*?\(([^)]+)\)",
                line.strip(),
            )
            if ob_m:
                obs.append({
                    "direction": ob_m.group(1),
                    "high": float(ob_m.group(2)),
                    "low": float(ob_m.group(3)),
                    "timestamp": ob_m.group(4),
                })
        return obs

    def _parse_atr(section_text: str) -> float | None:
        atr_m = re.search(r"ATR\(14\):\s*([\d.]+)", section_text)
        return float(atr_m.group(1)) if atr_m else None

    # H1 section
    h1_match = re.search(r"## H1.*?(?=## M15|## Recent|## Current|$)", user_message, re.DOTALL)
    if h1_match:
        result["h1_obs"] = _parse_obs(h1_match.group(0))
        result["h1_atr"] = _parse_atr(h1_match.group(0))

    # M15 section
    m15_match = re.search(r"## M15.*?(?=## Recent M15|## Current|$)", user_message, re.DOTALL)
    if m15_match:
        result["m15_obs"] = _parse_obs(m15_match.group(0))
        result["m15_atr"] = _parse_atr(m15_match.group(0))

    return result


def compute_proximity(
    current_price: float,
    obs: list[dict],
    direction: str,
    atr: float,
) -> tuple[str, dict | None, float | None]:
    """Compute proximity of current price to nearest relevant OB.

    Uses 2x M15 ATR(14) as the approaching/far threshold.

    Returns (label, nearest_ob, distance):
      label: 'inside' | 'approaching' | 'far' | 'none'
    """
    if not obs or current_price is None or atr is None or atr <= 0:
        return "none", None, None

    relevant = [ob for ob in obs if ob["direction"] == direction]
    if not relevant:
        return "none", None, None

    threshold = 2.0 * atr
    best_ob = None
    best_dist = float("inf")

    for ob in relevant:
        ob_high = ob["high"]
        ob_low = ob["low"]

        if ob_low <= current_price <= ob_high:
            return "inside", ob, 0.0

        if direction == "bullish":
            if current_price > ob_high:
                dist = current_price - ob_high
            else:
                continue
        else:
            if current_price < ob_low:
                dist = ob_low - current_price
            else:
                continue

        if dist < best_dist:
            best_dist = dist
            best_ob = ob

    if best_ob is None:
        return "none", None, None

    label = "approaching" if best_dist <= threshold else "far"
    return label, best_ob, best_dist


def compute_trade_proximity(user_message: str, trade_direction: str) -> dict:
    """Full proximity computation for a single trade.

    Args:
        user_message: The MSO text sent to the LLM.
        trade_direction: 'LONG' or 'SHORT' (from trade parameters).

    Returns dict suitable for shadow logging.
    """
    zones = parse_mso_zones(user_message)

    # Map trade direction to OB direction
    ob_direction = "bullish" if trade_direction == "LONG" else "bearish"

    # Combine H1 + M15 OBs (same as T7 post-hoc methodology)
    all_obs = zones["h1_obs"] + zones["m15_obs"]

    # Standardize on M15 ATR (fallback to H1 if M15 unavailable)
    atr = zones["m15_atr"] or zones["h1_atr"]
    current_price = zones["current_price_approx"]

    if current_price is None or atr is None:
        return {
            "proximity": "unknown",
            "reason": "missing_price_or_atr",
            "current_price": current_price,
            "atr_used": atr,
            "h1_ob_count": len(zones["h1_obs"]),
            "m15_ob_count": len(zones["m15_obs"]),
        }

    label, nearest_ob, dist = compute_proximity(current_price, all_obs, ob_direction, atr)

    return {
        "proximity": label,
        "current_price": round(current_price, 5),
        "atr_used": round(atr, 5),
        "atr_source": "m15" if zones["m15_atr"] else "h1",
        "distance_to_ob": round(dist, 4) if dist is not None else None,
        "distance_atr_ratio": round(dist / atr, 3) if dist is not None and atr > 0 else None,
        "nearest_ob": nearest_ob,
        "h1_ob_count": len(zones["h1_obs"]),
        "m15_ob_count": len(zones["m15_obs"]),
        "relevant_ob_count": sum(
            1 for ob in all_obs if ob["direction"] == ob_direction
        ),
    }


def write_proximity_shadow_log(
    trade_id: str,
    symbol: str,
    kill_zone: str,
    candle_time: str,
    trade_direction: str,
    proximity_data: dict,
    log_path: str = SHADOW_LOG_PATH,
) -> None:
    """Append a proximity shadow entry to the JSONL log."""
    entry = {
        "trade_id": trade_id,
        "symbol": symbol,
        "kill_zone": kill_zone,
        "candle_time": candle_time,
        "trade_direction": trade_direction,
        "proximity": proximity_data.get("proximity"),
        "distance_to_ob": proximity_data.get("distance_to_ob"),
        "distance_atr_ratio": proximity_data.get("distance_atr_ratio"),
        "atr_used": proximity_data.get("atr_used"),
        "atr_source": proximity_data.get("atr_source"),
        "h1_ob_count": proximity_data.get("h1_ob_count"),
        "m15_ob_count": proximity_data.get("m15_ob_count"),
        "relevant_ob_count": proximity_data.get("relevant_ob_count"),
        "timestamp_logged": datetime.now(timezone.utc).isoformat(),
        # Outcome fields — filled at trade close
        "actual_r_multiple": None,
        "outcome": None,
    }
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(
            "PROXIMITY_SHADOW: trade=%s proximity=%s dist_atr=%.2f",
            trade_id,
            entry["proximity"],
            entry.get("distance_atr_ratio") or 0,
        )
    except Exception as e:
        logger.warning("Failed to write proximity shadow log (non-blocking): %s", e)


def update_proximity_outcome(
    trade_id: str,
    actual_r_multiple: float,
    outcome: str,
    log_path: str = SHADOW_LOG_PATH,
) -> None:
    """Update the proximity log entry with trade outcome.

    Reads the JSONL, finds the matching trade_id, updates outcome fields,
    rewrites. This is called at trade close.
    """
    path = Path(log_path)
    if not path.exists():
        return

    try:
        lines = path.read_text().strip().split("\n")
        updated = False
        new_lines = []
        for line in lines:
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("trade_id") == trade_id and entry.get("outcome") is None:
                entry["actual_r_multiple"] = round(actual_r_multiple, 4)
                entry["outcome"] = outcome
                updated = True
            new_lines.append(json.dumps(entry))

        if updated:
            path.write_text("\n".join(new_lines) + "\n")
            logger.info(
                "PROXIMITY_SHADOW: updated outcome for %s: %s %.4fR",
                trade_id, outcome, actual_r_multiple,
            )
    except Exception as e:
        logger.warning("Failed to update proximity outcome (non-blocking): %s", e)
