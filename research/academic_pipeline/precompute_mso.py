#!/usr/bin/env python3
"""T4 Pre-Computation Module — Move arithmetic from LLM to Python.

This module takes a raw MSO user_message string and:
1. Parses structural data (OBs, FVGs, breaks, ATR, etc.)
2. Computes Q3-Q7 scores with verified arithmetic
3. Returns both a dict of computed values and a formatted summary for the LLM

The LLM still handles C1-C3 structural judgment and Q1-Q2 scoring.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OrderBlock:
    """Parsed order block data."""
    direction: str  # 'bullish' or 'bearish'
    high: float
    low: float
    timestamp: str
    mitigated: bool = False

    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2

    @property
    def width(self) -> float:
        return abs(self.high - self.low)


@dataclass
class StructuralBreak:
    """Parsed BOS/CHoCH event."""
    break_type: str  # 'BOS' or 'CHoCH'
    timestamp: str
    level: float
    direction: str  # 'bullish' or 'bearish'
    has_displacement: bool
    displacement_ratio: float


@dataclass
class FVG:
    """Parsed fair value gap."""
    direction: str
    high: float
    low: float


@dataclass
class Swing:
    """Parsed swing point."""
    swing_type: str  # 'high' or 'low'
    price: float
    timestamp: str


@dataclass
class TimeframeData:
    """Parsed data for a single timeframe."""
    name: str  # 'H1' or 'M15'
    structure_direction: str  # 'bullish' or 'bearish'
    protected_swing_price: float
    protected_swing_time: str
    breaks: list[StructuralBreak] = field(default_factory=list)
    unmitigated_obs: list[OrderBlock] = field(default_factory=list)
    fvgs: list[FVG] = field(default_factory=list)
    equilibrium: float = 0.0
    fib62: float = 0.0
    fib79: float = 0.0
    avg_body: float = 0.0
    atr_14: float = 0.0


@dataclass
class ParsedMSO:
    """Complete parsed MSO data."""
    candle_time: str
    session_high: float
    session_low: float
    h1: TimeframeData | None = None
    m15: TimeframeData | None = None
    recent_m15_swings: list[Swing] = field(default_factory=list)
    sweeps: list[dict] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# SYMBOL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Symbol-specific configuration
SYMBOL_CONFIG = {
    "XAUUSD": {
        "sl_min_absolute": 5.0,  # $5.00
        "pip_value": 1.0,  # Gold uses dollars
        "unit": "dollars",
        "precision": 2,
    },
    "GBPUSD": {
        "sl_min_absolute": 0.0050,  # 50 pips
        "pip_value": 0.0001,
        "unit": "pips",
        "precision": 5,
    },
    "GBPJPY": {
        "sl_min_absolute": 0.50,  # 50 pips
        "pip_value": 0.01,
        "unit": "pips",
        "precision": 3,
    },
    "USDJPY": {
        "sl_min_absolute": 0.50,  # 50 pips
        "pip_value": 0.01,
        "unit": "pips",
        "precision": 3,
    },
    "US30": {
        "sl_min_absolute": 50.0,  # 50 points
        "pip_value": 1.0,
        "unit": "points",
        "precision": 2,
    },
}

def get_symbol_config(symbol: str) -> dict:
    """Get configuration for a symbol, with sensible defaults."""
    return SYMBOL_CONFIG.get(symbol.upper(), SYMBOL_CONFIG["XAUUSD"])


# ═══════════════════════════════════════════════════════════════════════════
# PARSING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def parse_mso(user_message: str) -> ParsedMSO:
    """Parse the MSO user_message text into structured data."""

    result = ParsedMSO(
        candle_time="",
        session_high=0.0,
        session_low=0.0,
    )

    lines = user_message.split('\n')

    # Parse header
    for line in lines:
        if line.startswith('Candle:'):
            result.candle_time = line.replace('Candle:', '').strip()
        elif 'Session H/L:' in line:
            match = re.search(r'Session H/L:\s*([\d.]+)/([\d.]+)', line)
            if match:
                result.session_high = float(match.group(1))
                result.session_low = float(match.group(2))

    # Parse timeframe sections
    result.h1 = _parse_timeframe_section(user_message, 'H1')
    result.m15 = _parse_timeframe_section(user_message, 'M15')

    # Parse recent M15 swings
    result.recent_m15_swings = _parse_recent_swings(user_message)

    # Parse sweeps
    result.sweeps = _parse_sweeps(user_message)

    return result


def _parse_timeframe_section(text: str, tf_name: str) -> TimeframeData | None:
    """Parse a single timeframe section (H1 or M15)."""

    # Find the section
    pattern = rf'## {tf_name} — Structure: (\w+), Protected Swing: at ([\d.]+) \(([^)]+)\)'
    header_match = re.search(pattern, text)

    if not header_match:
        return None

    tf_data = TimeframeData(
        name=tf_name,
        structure_direction=header_match.group(1).lower(),
        protected_swing_price=float(header_match.group(2)),
        protected_swing_time=header_match.group(3),
    )

    # Find section boundaries
    section_start = header_match.start()
    next_section = re.search(rf'\n## (?!{tf_name})', text[section_start + 10:])
    section_end = section_start + 10 + next_section.start() if next_section else len(text)
    section_text = text[section_start:section_end]

    # Parse structural breaks
    break_pattern = r'(BOS|CHoCH) (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}) lvl=([\d.]+) dir=(\w+) disp=(True|False) ratio=([\d.]+)'
    for match in re.finditer(break_pattern, section_text):
        tf_data.breaks.append(StructuralBreak(
            break_type=match.group(1),
            timestamp=match.group(2),
            level=float(match.group(3)),
            direction=match.group(4).lower(),
            has_displacement=match.group(5) == 'True',
            displacement_ratio=float(match.group(6)),
        ))

    # Parse unmitigated OBs
    ob_pattern = r'(\w+) ([\d.]+)-([\d.]+) \((\d{4}-\d{2}-\d{2}T\d{2}:\d{2})\)'
    in_ob_section = False
    for line in section_text.split('\n'):
        if 'Unmitigated OBs' in line:
            in_ob_section = True
            continue
        if in_ob_section:
            if line.strip().startswith('#') or 'FVG' in line or 'P/D:' in line or 'Avg body:' in line:
                in_ob_section = False
                continue
            ob_match = re.search(ob_pattern, line)
            if ob_match:
                tf_data.unmitigated_obs.append(OrderBlock(
                    direction=ob_match.group(1).lower(),
                    high=float(ob_match.group(2)),
                    low=float(ob_match.group(3)),
                    timestamp=ob_match.group(4),
                    mitigated=False,
                ))

    # Parse FVGs
    fvg_pattern = r'(\w+) ([\d.]+)-([\d.]+)'
    in_fvg_section = False
    for line in section_text.split('\n'):
        if 'Unfilled FVGs' in line:
            in_fvg_section = True
            continue
        if in_fvg_section:
            if line.strip().startswith('#') or 'P/D:' in line or 'Avg body:' in line:
                in_fvg_section = False
                continue
            fvg_match = re.search(fvg_pattern, line)
            if fvg_match and fvg_match.group(1).lower() in ('bullish', 'bearish'):
                tf_data.fvgs.append(FVG(
                    direction=fvg_match.group(1).lower(),
                    high=float(fvg_match.group(2)),
                    low=float(fvg_match.group(3)),
                ))

    # Parse P/D levels
    pd_pattern = r'P/D: eq=([\d.]+) fib62=([\d.]+) fib79=([\d.]+)'
    pd_match = re.search(pd_pattern, section_text)
    if pd_match:
        tf_data.equilibrium = float(pd_match.group(1))
        tf_data.fib62 = float(pd_match.group(2))
        tf_data.fib79 = float(pd_match.group(3))

    # Parse ATR and avg body
    atr_pattern = r'Avg body:\s*([\d.]+)\s+ATR\(14\):\s*([\d.]+)'
    atr_match = re.search(atr_pattern, section_text)
    if atr_match:
        tf_data.avg_body = float(atr_match.group(1))
        tf_data.atr_14 = float(atr_match.group(2))

    return tf_data


def _parse_recent_swings(text: str) -> list[Swing]:
    """Parse recent M15 swings section."""
    swings = []

    # Find section
    section_match = re.search(r'## Recent M15 Swings.*?\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
    if not section_match:
        return swings

    section_text = section_match.group(1)

    # Parse each swing
    swing_pattern = r'(high|low) ([\d.]+) \((\d{4}-\d{2}-\d{2}T\d{2}:\d{2})\)'
    for match in re.finditer(swing_pattern, section_text, re.IGNORECASE):
        swings.append(Swing(
            swing_type=match.group(1).lower(),
            price=float(match.group(2)),
            timestamp=match.group(3),
        ))

    return swings


def _parse_sweeps(text: str) -> list[dict]:
    """Parse sweeps section."""
    sweeps = []

    # Find section
    section_match = re.search(r'## Sweeps.*?\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
    if not section_match:
        return sweeps

    section_text = section_match.group(1)

    # Parse each sweep
    sweep_pattern = r'(sweep|run) of (\w+) wick=([\d.]+) close=([\d.]+) \((\d{4}-\d{2}-\d{2}T\d{2}:\d{2})\)'
    for match in re.finditer(sweep_pattern, section_text, re.IGNORECASE):
        sweeps.append({
            'type': match.group(1).lower(),
            'level': match.group(2),
            'wick': float(match.group(3)),
            'close': float(match.group(4)),
            'timestamp': match.group(5),
        })

    return sweeps


# ═══════════════════════════════════════════════════════════════════════════
# ZONE DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════

def find_nearest_zone(
    parsed: ParsedMSO,
    current_price: float,
    direction: str,  # 'bullish' or 'bearish'
) -> tuple[OrderBlock | None, float]:
    """
    Find the nearest unmitigated OB zone for the given direction.
    Searches both H1 and M15 OBs.
    Returns (zone, distance_to_nearest_boundary).
    """
    all_zones = find_all_zones_ranked(parsed, current_price, direction)
    if not all_zones:
        return None, float('inf')
    nearest_ob, distance, _ = all_zones[0]
    return nearest_ob, distance


def find_all_zones_ranked(
    parsed: ParsedMSO,
    current_price: float,
    direction: str | None = None,
) -> list[tuple[OrderBlock, float, str]]:
    """
    Find all unmitigated OBs ranked by proximity.
    Returns list of (zone, distance, source_timeframe).
    """
    zones = []

    # H1 zones
    if parsed.h1:
        for ob in parsed.h1.unmitigated_obs:
            if direction and ob.direction != direction:
                continue

            if ob.low <= current_price <= ob.high:
                distance = 0.0
            elif current_price < ob.low:
                distance = ob.low - current_price
            else:
                distance = current_price - ob.high

            zones.append((ob, distance, 'H1'))

    # M15 zones
    if parsed.m15:
        for ob in parsed.m15.unmitigated_obs:
            if direction and ob.direction != direction:
                continue

            if ob.low <= current_price <= ob.high:
                distance = 0.0
            elif current_price < ob.low:
                distance = ob.low - current_price
            else:
                distance = current_price - ob.high

            zones.append((ob, distance, 'M15'))

    # Sort by distance
    zones.sort(key=lambda x: x[1])

    return zones


# ═══════════════════════════════════════════════════════════════════════════
# Q-SCORE COMPUTATIONS
# ═══════════════════════════════════════════════════════════════════════════

def compute_q3_proximity(
    current_price: float,
    zone: OrderBlock | None,
    atr: float,
) -> dict:
    """
    Q3: Price proximity to zone.
    Returns computed values and score.
    """
    if zone is None:
        return {
            'q3_has_zone': False,
            'q3_distance_abs': None,
            'q3_distance_atr': None,
            'q3_is_inside': False,
            'q3_label': 'NO_ZONE',
        }

    # Check if inside
    is_inside = zone.low <= current_price <= zone.high

    # Distance to nearest boundary
    if is_inside:
        distance_abs = 0.0
    elif current_price < zone.low:
        distance_abs = zone.low - current_price
    else:
        distance_abs = current_price - zone.high

    # Distance in ATR units
    distance_atr = distance_abs / atr if atr > 0 else float('inf')

    # Factual label (not a score — LLM interprets)
    if is_inside:
        label = 'INSIDE'
    elif distance_atr <= 1.0:
        label = 'WITHIN_1ATR'
    else:
        label = 'BEYOND'

    return {
        'q3_has_zone': True,
        'q3_zone_high': zone.high,
        'q3_zone_low': zone.low,
        'q3_zone_direction': zone.direction,
        'q3_distance_abs': distance_abs,
        'q3_distance_atr': round(distance_atr, 3),
        'q3_is_inside': is_inside,
        'q3_label': label,
    }


def compute_q4_premium_discount(
    current_price: float,
    equilibrium: float,
    fib62: float,
    fib79: float,
    direction: str,
) -> dict:
    """
    Q4: Premium/discount position.
    For longs: discount (below 50%) = correct.
    For shorts: premium (above 50%) = correct.
    """
    if equilibrium == 0:
        return {
            'q4_equilibrium': None,
            'q4_position_pct': None,
            'q4_label': 'NO_DATA',
        }

    # Factual label: where is price relative to equilibrium?
    if direction == 'bullish':
        if current_price < equilibrium:
            label = 'DISCOUNT'
        elif abs(current_price - equilibrium) / equilibrium < 0.05:
            label = 'EQUILIBRIUM'
        else:
            label = 'PREMIUM'
    else:  # bearish
        if current_price > equilibrium:
            label = 'PREMIUM'
        elif abs(current_price - equilibrium) / equilibrium < 0.05:
            label = 'EQUILIBRIUM'
        else:
            label = 'DISCOUNT'

    # Calculate position percentage (rough estimate using fib levels)
    if fib62 != 0 and equilibrium != 0:
        range_estimate = abs(equilibrium - fib62) / 0.12  # 50%-38% = 12% of range
        if range_estimate > 0:
            if direction == 'bullish':
                low_estimate = equilibrium - 0.5 * range_estimate
                position_pct = (current_price - low_estimate) / range_estimate * 100
            else:
                high_estimate = equilibrium + 0.5 * range_estimate
                position_pct = (high_estimate - current_price) / range_estimate * 100
        else:
            position_pct = 50.0
    else:
        position_pct = 50.0

    return {
        'q4_equilibrium': equilibrium,
        'q4_fib62': fib62,
        'q4_fib79': fib79,
        'q4_position_pct': round(position_pct, 1),
        'q4_label': label,
    }


def compute_q5_displacement(
    current_body: float | None,
    avg_body: float,
    has_m15_choch: bool,
) -> dict:
    """
    Q5: M15 confirmation (CHoCH + displacement).
    """
    if current_body is None or avg_body <= 0:
        return {
            'q5_current_body': current_body,
            'q5_avg_body': avg_body,
            'q5_ratio': None,
            'q5_has_choch': has_m15_choch,
            'q5_label': 'WEAK',
        }

    ratio = current_body / avg_body

    # Factual label describing displacement strength
    if not has_m15_choch:
        label = 'WEAK'
    elif ratio >= 1.5:
        label = 'STRONG'
    elif ratio >= 1.2:
        label = 'MODERATE'
    else:
        label = 'WEAK'

    return {
        'q5_current_body': round(current_body, 4),
        'q5_avg_body': round(avg_body, 4),
        'q5_ratio': round(ratio, 3),
        'q5_has_choch': has_m15_choch,
        'q5_label': label,
    }


def compute_q6_rr(
    entry: float,
    sl: float,
    direction: str,
) -> dict:
    """
    Q6: Risk-reward calculation.
    TP1 = entry ± 1.5 * (entry - SL) distance.
    """
    if entry == 0 or sl == 0 or entry == sl:
        return {
            'q6_entry': entry,
            'q6_sl': sl,
            'q6_tp1': None,
            'q6_rr': None,
            'q6_label': 'INVALID',
        }

    sl_distance = abs(entry - sl)

    if direction == 'bullish' or direction == 'LONG':
        # Long: TP1 = entry + 1.5 * (entry - SL)
        tp1 = entry + 1.5 * sl_distance
    else:
        # Short: TP1 = entry - 1.5 * (SL - entry)
        tp1 = entry - 1.5 * sl_distance

    # RR is always 1.5 by construction (TP1 = 1.5x SL distance)
    rr = 1.5

    return {
        'q6_entry': round(entry, 5),
        'q6_sl': round(sl, 5),
        'q6_sl_distance': round(sl_distance, 5),
        'q6_tp1': round(tp1, 5),
        'q6_rr': round(rr, 2),
        'q6_label': 'MET',
    }


def compute_q7_sl_adequacy(
    entry: float,
    sl: float,
    atr: float,
    symbol: str,
) -> dict:
    """
    Q7: SL adequacy check.
    SL must be >= 1.5x M15 ATR AND >= absolute minimum.
    """
    config = get_symbol_config(symbol)
    sl_min_absolute = config['sl_min_absolute']

    sl_distance = abs(entry - sl)

    if atr <= 0:
        sl_in_atr = 0.0
    else:
        sl_in_atr = sl_distance / atr

    meets_atr = sl_in_atr >= 1.5
    meets_minimum = sl_distance >= sl_min_absolute
    adequate = meets_atr and meets_minimum

    label = 'ADEQUATE' if adequate else 'INADEQUATE'

    flags = []
    if not meets_atr:
        flags.append(f'SL/ATR={sl_in_atr:.2f}x (need >=1.5x)')
    if not meets_minimum:
        flags.append(f'SL={sl_distance:.5g} (need >={sl_min_absolute})')

    return {
        'q7_sl_distance': round(sl_distance, 5),
        'q7_sl_in_atr': round(sl_in_atr, 3),
        'q7_sl_min_absolute': sl_min_absolute,
        'q7_meets_atr': meets_atr,
        'q7_meets_minimum': meets_minimum,
        'q7_label': label,
        'q7_flags': flags,
    }


def compute_bonus_factors(
    zone: OrderBlock | None,
    parsed: ParsedMSO,
    impulse_candle_count: int | None = None,
) -> dict:
    """Compute bonus facts: first touch, FVG present, compact impulse."""

    factors = []

    # First touch: all unmitigated OBs are by definition first touch
    first_touch = zone is not None
    if first_touch:
        factors.append('first_touch')

    # FVG present near zone
    fvg_present = False
    if zone and parsed.m15 and parsed.m15.fvgs:
        for fvg in parsed.m15.fvgs:
            if fvg.low <= zone.high and fvg.high >= zone.low:
                fvg_present = True
                break
    if fvg_present:
        factors.append('fvg_overlap')

    # Compact impulse (<=7 H1 candles)
    compact_impulse = impulse_candle_count is not None and impulse_candle_count <= 7
    if compact_impulse:
        factors.append('compact_impulse')

    return {
        'bonus_first_touch': first_touch,
        'bonus_fvg_present': fvg_present,
        'bonus_compact_impulse': compact_impulse,
        'bonus_factors': factors,
    }


# ═══════════════════════════════════════════════════════════════════════════
# MAIN PRECOMPUTE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def precompute(
    user_message: str,
    symbol: str = "XAUUSD",
    current_price: float | None = None,
    current_body: float | None = None,
    direction: str | None = None,
) -> tuple[dict, str]:
    """
    Pre-compute arithmetic values from MSO.

    Args:
        user_message: Raw MSO text from the API
        symbol: Trading symbol (for SL minimums, precision)
        current_price: Current candle close price (from CSV)
        current_body: Current candle body size (from CSV)
        direction: Trade direction ('bullish' or 'bearish')

    Returns:
        (computed_values_dict, formatted_summary_string)
    """

    # Parse MSO
    parsed = parse_mso(user_message)

    # Get ATR
    m15_atr = parsed.m15.atr_14 if parsed.m15 else 0.0

    # Infer direction from H1 structure if not provided
    if direction is None and parsed.h1:
        direction = parsed.h1.structure_direction

    # If no current_price, try to infer from session data or sweeps
    if current_price is None:
        if parsed.sweeps:
            # Use most recent sweep close
            current_price = parsed.sweeps[0]['close']
        elif parsed.session_high and parsed.session_low:
            # Use session midpoint
            current_price = (parsed.session_high + parsed.session_low) / 2
        else:
            current_price = 0.0

    # Get all zones ranked (both H1 and M15)
    all_zones = find_all_zones_ranked(parsed, current_price, direction)

    # Find nearest zone (now searches both H1 and M15)
    zone, distance = find_nearest_zone(parsed, current_price, direction or 'bullish')

    # Find nearest H1 and M15 zones separately for the summary
    nearest_h1 = next(((ob, d) for ob, d, tf in all_zones if tf == 'H1'), (None, float('inf')))
    nearest_m15 = next(((ob, d) for ob, d, tf in all_zones if tf == 'M15'), (None, float('inf')))

    # Track which timeframe the nearest zone comes from
    nearest_zone_source = None
    if all_zones:
        nearest_zone_source = all_zones[0][2]  # 'H1' or 'M15'

    # Compute Q3
    q3 = compute_q3_proximity(current_price, zone, m15_atr)

    # Compute Q4
    eq = parsed.h1.equilibrium if parsed.h1 else 0.0
    fib62 = parsed.h1.fib62 if parsed.h1 else 0.0
    fib79 = parsed.h1.fib79 if parsed.h1 else 0.0
    q4 = compute_q4_premium_discount(current_price, eq, fib62, fib79, direction or 'bullish')

    # Compute Q5
    avg_body = parsed.m15.avg_body if parsed.m15 else 0.0
    # Detect M15 CHoCH from recent structural breaks
    has_m15_choch = False
    if parsed.m15 and parsed.m15.breaks:
        # Check last break
        last_break = parsed.m15.breaks[-1]
        if last_break.break_type == 'CHoCH':
            has_m15_choch = True
        elif last_break.break_type == 'BOS' and last_break.direction == direction:
            has_m15_choch = True  # BOS in direction counts as confirmation

    q5 = compute_q5_displacement(current_body, avg_body, has_m15_choch)

    # Compute Q6 and Q7 (need entry/SL)
    # Entry = current price, SL = zone extreme + buffer
    entry = current_price
    if zone:
        config = get_symbol_config(symbol)
        buffer = m15_atr * 0.3 if m15_atr > 0 else config['sl_min_absolute'] * 0.3

        if direction == 'bullish':
            sl = zone.low - buffer
        else:
            sl = zone.high + buffer
    else:
        sl = 0.0

    q6 = compute_q6_rr(entry, sl, direction or 'bullish')
    q7 = compute_q7_sl_adequacy(entry, sl, m15_atr, symbol)

    # Compute bonus
    bonus = compute_bonus_factors(zone, parsed)

    # Compile all computed values (facts only — no scores)
    computed = {
        'symbol': symbol,
        'candle_time': parsed.candle_time,
        'current_price': current_price,
        'direction': direction,
        'm15_atr': m15_atr,

        # Zone discovery
        'nearest_zone': {
            'high': zone.high if zone else None,
            'low': zone.low if zone else None,
            'direction': zone.direction if zone else None,
            'timestamp': zone.timestamp if zone else None,
            'width': zone.width if zone else None,
        } if zone else None,
        'nearest_zone_source': nearest_zone_source,
        'nearest_h1_zone': {
            'high': nearest_h1[0].high,
            'low': nearest_h1[0].low,
            'direction': nearest_h1[0].direction,
            'distance': nearest_h1[1],
        } if nearest_h1[0] else None,
        'nearest_m15_zone': {
            'high': nearest_m15[0].high,
            'low': nearest_m15[0].low,
            'direction': nearest_m15[0].direction,
            'distance': nearest_m15[1],
        } if nearest_m15[0] else None,
        'all_zones_count': len(all_zones),

        # Computed facts (Q3-Q7 + bonus)
        **q3,
        **q4,
        **q5,
        **q6,
        **q7,
        **bonus,

        # Structural context (for LLM to interpret)
        'h1_structure_direction': parsed.h1.structure_direction if parsed.h1 else None,
        'h1_protected_swing': parsed.h1.protected_swing_price if parsed.h1 else None,
        'h1_last_break': {
            'type': parsed.h1.breaks[-1].break_type,
            'level': parsed.h1.breaks[-1].level,
            'direction': parsed.h1.breaks[-1].direction,
            'displacement': parsed.h1.breaks[-1].has_displacement,
        } if parsed.h1 and parsed.h1.breaks else None,
        'm15_structure_direction': parsed.m15.structure_direction if parsed.m15 else None,
        'm15_protected_swing': parsed.m15.protected_swing_price if parsed.m15 else None,
    }

    # Build formatted summary
    summary = _build_formatted_summary(computed, parsed, user_message, symbol)

    return computed, summary


def _build_formatted_summary(
    computed: dict,
    parsed: ParsedMSO,
    raw_mso: str,
    symbol: str,
) -> str:
    """Build the natural language summary for the LLM prompt."""

    config = get_symbol_config(symbol)
    precision = config['precision']

    def fmt_price(p: float | None) -> str:
        if p is None:
            return "N/A"
        return f"{p:.{precision}f}"

    lines = []

    # Header
    lines.append("=== PRE-COMPUTED TRADE EVALUATION ===")
    lines.append(f"Symbol: {symbol} | Time: {computed.get('candle_time', 'N/A')}")
    lines.append("")

    # Structural context
    lines.append("── STRUCTURAL CONTEXT (interpret these — your judgment needed) ──")
    lines.append("")

    if parsed.h1:
        lines.append("H1 STRUCTURE:")
        lines.append(f"  Direction: {parsed.h1.structure_direction.upper()}")
        lines.append(f"  Protected swing: {fmt_price(parsed.h1.protected_swing_price)} ({parsed.h1.protected_swing_time})")
        if parsed.h1.breaks:
            last = parsed.h1.breaks[-1]
            lines.append(f"  Most recent break: {last.break_type} {last.direction.upper()} at {fmt_price(last.level)}")
            lines.append(f"    Displacement: {'YES' if last.has_displacement else 'NO'} (ratio: {last.displacement_ratio}x)")
        lines.append("")

    if parsed.m15:
        lines.append("M15 STRUCTURE:")
        lines.append(f"  Direction: {parsed.m15.structure_direction.upper()}")
        lines.append(f"  Protected swing: {fmt_price(parsed.m15.protected_swing_price)} ({parsed.m15.protected_swing_time})")
        if parsed.m15.breaks:
            last = parsed.m15.breaks[-1]
            lines.append(f"  Most recent break: {last.break_type} {last.direction.upper()} at {fmt_price(last.level)}")
        lines.append("")

    # ── COMPUTED ARITHMETIC ──────────────────────────────────
    lines.append("── COMPUTED ARITHMETIC (verified — use these exact numbers) ──")
    lines.append("")

    # Zone proximity
    lines.append("ZONE PROXIMITY:")
    h1z = computed.get('nearest_h1_zone')
    m15z = computed.get('nearest_m15_zone')
    if h1z:
        lines.append(f"  Nearest H1 OB: {fmt_price(h1z['low'])} – {fmt_price(h1z['high'])} ({h1z['direction']}, H1)")
    else:
        lines.append("  Nearest H1 OB: none")
    if m15z:
        lines.append(f"  Nearest M15 OB: {fmt_price(m15z['low'])} – {fmt_price(m15z['high'])} ({m15z['direction']}, M15)")
    else:
        lines.append("  Nearest M15 OB: none")
    lines.append(f"  Current price: {fmt_price(computed['current_price'])}")

    if computed.get('q3_distance_abs') is not None:
        dist_abs = computed['q3_distance_abs']
        dist_atr = computed.get('q3_distance_atr', 'N/A')
        if computed.get('q3_is_inside'):
            lines.append(f"  Distance to nearest zone boundary: 0.00 (INSIDE zone)")
            lines.append(f"  Price position: INSIDE zone")
        else:
            lines.append(f"  Distance to nearest zone boundary: {fmt_price(dist_abs)} ({dist_atr}x M15 ATR)")
            zone_label = computed.get('q3_label', '')
            lines.append(f"  Price position: {zone_label} zone — ({dist_atr}x ATR; inside=0, within 1ATR=approaching, beyond=away)")
    else:
        lines.append("  Distance: N/A (no zone found)")
    lines.append("")

    # Premium/discount position
    lines.append("PREMIUM/DISCOUNT POSITION:")
    if computed.get('q4_equilibrium'):
        eq = computed['q4_equilibrium']
        price = computed['current_price']
        delta = price - eq
        direction_str = computed.get('direction', 'bullish')
        side_note = "discount is below 50% for longs" if direction_str == 'bullish' else "premium is above 50% for shorts"
        delta_sign = f"+{fmt_price(delta)}" if delta >= 0 else fmt_price(delta)
        pos_label = "ABOVE equilibrium (premium)" if delta >= 0 else "BELOW equilibrium (discount)"
        lines.append(f"  H1 equilibrium: {fmt_price(eq)}")
        lines.append(f"  Current price vs equilibrium: {pos_label} ({delta_sign})")
        lines.append(f"  Label: {computed.get('q4_label', 'N/A')} ({side_note})")
        if computed.get('q4_position_pct') is not None:
            lines.append(f"  Impulse position: ~{computed['q4_position_pct']}%")
    else:
        lines.append("  H1 equilibrium: N/A")
    lines.append("")

    # M15 displacement
    lines.append("M15 DISPLACEMENT:")
    lines.append(f"  M15 CHoCH detected: {'YES' if computed.get('q5_has_choch') else 'NO'}")
    if computed.get('q5_current_body') is not None:
        lines.append(f"  Current M15 body: {computed['q5_current_body']}")
        lines.append(f"  Average M15 body (20-period): {computed['q5_avg_body']}")
        ratio = computed.get('q5_ratio', 'N/A')
        label_q5 = computed.get('q5_label', 'N/A')
        lines.append(f"  Body ratio: {ratio}x average — {label_q5} (threshold for STRONG is 1.5x, MODERATE is 1.2x)")
    else:
        lines.append("  Body ratio: N/A (no candle body data)")
    lines.append("")

    # Risk/reward
    lines.append("RISK/REWARD (exact computation):")
    entry = computed.get('q6_entry')
    sl = computed.get('q6_sl')
    tp = computed.get('q6_tp1')
    sl_dist = computed.get('q6_sl_distance')
    rr = computed.get('q6_rr')
    m15_atr_val = computed.get('m15_atr', 0)
    buf_note = f"zone extreme - 0.3 ATR buffer" if m15_atr_val else "zone extreme"
    dir_note = "entry + 1.5 × SL distance" if computed.get('direction') == 'bullish' else "entry - 1.5 × SL distance"
    lines.append(f"  Entry: {fmt_price(entry)}")
    lines.append(f"  Proposed SL: {fmt_price(sl)} ({buf_note})")
    lines.append(f"  Proposed TP1: {fmt_price(tp)} ({dir_note})")
    lines.append(f"  SL distance: {fmt_price(sl_dist)}")
    lines.append(f"  RR ratio: {rr}:1")
    lines.append("")

    # SL adequacy
    lines.append("SL ADEQUACY:")
    sl_in_atr = computed.get('q7_sl_in_atr', 0)
    meets_atr = computed.get('q7_meets_atr', False)
    meets_min = computed.get('q7_meets_minimum', False)
    sl_min_abs = computed.get('q7_sl_min_absolute', 'N/A')
    atr_check = "✓" if meets_atr else "✗"
    min_check = "✓" if meets_min else "✗"
    lines.append(f"  SL distance: {fmt_price(computed.get('q7_sl_distance'))}")
    lines.append(f"  SL / M15 ATR: {sl_in_atr}x (minimum: 1.5x) {atr_check}")
    lines.append(f"  SL vs instrument minimum: {fmt_price(computed.get('q7_sl_distance'))} >= {sl_min_abs} {min_check}")
    lines.append("")

    # Bonus facts
    freshness = "First touch (unmitigated) ✓" if computed.get('bonus_first_touch') else "Zone previously touched ✗"
    fvg_note = "Yes, M15 FVG overlaps zone ✓" if computed.get('bonus_fvg_present') else "No FVG overlap"
    compact = "Yes (<=7 H1 candles) ✓" if computed.get('bonus_compact_impulse') else "Not detected"
    lines.append(f"ZONE FRESHNESS: {freshness}")
    lines.append(f"FVG OVERLAP: {fvg_note}")
    lines.append(f"COMPACT IMPULSE: {compact}")
    lines.append("")

    # Flags
    flags = []
    if computed.get('q7_flags'):
        flags.extend(computed['q7_flags'])
    if not computed.get('q5_has_choch'):
        flags.append("No M15 CHoCH detected — Q5 body ratio alone cannot make STRONG")
    if not computed.get('nearest_zone'):
        flags.append("No unmitigated OB found in H1 or M15 — Q2/Q3 will be 0")

    if flags:
        lines.append("⚠ FLAGS:")
        for flag in flags:
            lines.append(f"  - {flag}")
        lines.append("")

    # Raw MSO appendix (trimmed)
    lines.append("── RAW MSO DATA (for verification) ──")
    lines.append("")
    # Include key sections only
    lines.append(raw_mso[:4000] if len(raw_mso) > 4000 else raw_mso)

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# CLI / TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    # Quick test with a sample MSO
    sample_mso = """## Dynamic Market Data (H1/M15 — this candle)
Candle: 2025-03-13T13:45:00Z
Session H/L: 2938.05/2932.00

## Sweeps (10)
  sweep of asian_high wick=2937.92 close=2936.50 (2025-03-13T07:00)

## H1 — Structure: bullish, Protected Swing: at 2900.00 (2025-03-12T16:00)
  Breaks (last 5 of 10):
    BOS 2025-03-13T09:00 lvl=2935.52 dir=bullish disp=True ratio=1.7
  Unmitigated OBs (2):
    bullish 2938.05-2932.99 (2025-03-13T09:00)
    bullish 2920.00-2915.00 (2025-03-12T14:00)
  Unfilled FVGs (3):
    bullish 2936.00-2933.00
  P/D: eq=2925.00 fib62=2918.00 fib79=2910.00
  Avg body: 4.89  ATR(14): 11.78

## M15 — Structure: bullish, Protected Swing: at 2932.99 (2025-03-13T09:45)
  Breaks (last 5 of 20):
    BOS 2025-03-13T13:30 lvl=2935.52 dir=bullish disp=False ratio=1.3
  Unmitigated OBs (1):
    bullish 2935.00-2933.00 (2025-03-13T13:00)
  Unfilled FVGs (2):
    bullish 2936.00-2934.00
  P/D: eq=2935.00 fib62=2933.00 fib79=2930.00
  Avg body: 1.93  ATR(14): 4.53

## Recent M15 Swings (last 10):
  high 2935.52 (2025-03-13T13:30)
  low 2932.99 (2025-03-13T09:45)

## Current Time: 2025-03-13T13:45:00Z
## Candle Being Evaluated: M15 close at 2025-03-13T13:45:00Z
"""

    # Test with sample data
    computed, summary = precompute(
        sample_mso,
        symbol="XAUUSD",
        current_price=2935.52,
        current_body=2.50,
        direction="bullish",
    )

    print("=== COMPUTED VALUES ===")
    for key, value in computed.items():
        print(f"  {key}: {value}")

    print("\n=== FORMATTED SUMMARY ===")
    print(summary[:2000])
