"""Cross-instrument correlation-aware risk gate.

Layered ON TOP of ``portfolio_risk.check_correlation_risk`` (which is
group-scoped). Where the existing correlation gate operates *within* a
named group (JPY_CROSSES, EUR_GBP, ...) at sizing time, this gate looks
across the entire fleet at the live Pearson correlation matrix and catches
the failure mode the group-scoped cap misses:

    USD-weakness day -> GBPUSD signals LONG with US30 LONG, XAUUSD LONG,
    GBPJPY LONG already filled. None of these share a formal correlation
    group, but they all spike together when DXY drops. Group-scoped cap
    sees no overlap; gross open exposure climbs to 4% with no governor.

Structural-screen finding (research/instrument_expansion_2026-04-25,
generated from 6 months of M15 closes Oct 2025 - Apr 2026): GBPUSD
correlates +0.4-0.6 with multiple non-group instruments simultaneously
(EURUSD, GBPJPY, NZDUSD, AUDUSD all > 0.55). The pre-existing
DEFAULT_CORRELATION_GROUPS only formalizes EUR/GBP and JPY pairs - it
has no entry that connects GBPUSD to US30, XAUUSD, or AUDUSD.

Gate behavior (additive — never weakens an existing gate):

    | Same-direction correlated open positions (|r| >= threshold) | Action            |
    |--------------------------------------------------------------|-------------------|
    | 0 or 1                                                       | NONE (pass)       |
    | 2                                                            | RISK_REDUCE_HALF  |
    | 3+                                                           | REJECT            |

The HALVE response is the soft action — sizing reduction only, downstream
of the existing ``check_correlation_risk`` adjustment in the orchestrator.
The REJECT response is the hard action — surfaced as ``ExecutionDenial``
through ``permissions.py``.

Configuration (all under ``risk`` in ``agent_config.yaml``):

    cross_instrument_correlation_enabled         : bool, default True
    cross_instrument_correlation_threshold       : float, default 0.4
    cross_instrument_correlation_min_positions   : int, default 2
                                                   (>= triggers HALVE;
                                                   +1 triggers REJECT)

Per-instrument risk overrides (e.g., FN's XAUUSD 0.5%) are honored
naturally because the HALVE action multiplies the *already-resolved*
risk_pct from the orchestrator's pipeline (DD-reduced -> group-corr
adjusted -> cross-instrument adjusted). There is no path that re-reads
``risk.risk_per_trade_pct`` after this gate, so the 0.5%-of-XAUUSD
config flows through correctly.

Same-direction filter:

    A position counts toward the cluster IF AND ONLY IF its open direction
    aligns with the candidate direction in the SIGNED-correlation sense:

        candidate LONG  + open LONG  + r > +threshold  -> cluster member
        candidate SHORT + open SHORT + r > +threshold  -> cluster member
        candidate LONG  + open SHORT + r < -threshold  -> cluster member
        candidate SHORT + open LONG  + r < -threshold  -> cluster member

    Otherwise the open position diversifies the candidate exposure rather
    than amplifying it (a SHORT position with r=+0.5 to a LONG candidate
    is a hedge — sizing should NOT be reduced).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

from src.components.gtos_vnext_runtime import (
    normalize_vnext_symbol_key,
    resolve_vnext_symbol_family,
)
from src.components.cross_instrument_correlation_gate_logger import (
    log_cross_instrument_correlation_decision,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Static correlation table
# ============================================================================
#
# Sourced from `exports/multi_instrument/screening_results/correlation_matrix.json`
# (24×24 Pearson on log-returns of M15 closes from `data/historical_2026/`,
# data window 2026-01-02 → 2026-04-24). The hardcoded fallback below mirrors
# that file so the gate keeps working in environments that don't ship the
# screening export (test sandboxes, fresh clones).
#
# Last refresh: 2026-04-25 (per `research/staleness_audit/04_CORRELATION_INFRA_AUDIT.md`).
# The previous matrix dated 2026-04-04 missed 15 |r|≥0.4 threshold flips
# including the operationally critical USD-weakness cluster
# (GBPUSD↔XAUUSD +0.284→+0.419, GBPUSD↔US30_cash +0.283→+0.444,
# GBPUSD↔USDJPY −0.293→−0.547). Schema unchanged: flat
# {sym: {sym2: r, ...}, ...}; broker-symbol naming follows
# `data/historical_2026/` (e.g. SPX500, NAS100 — no "_cash" suffix on
# index symbols here, but the live FN/FTMO labels US30_cash and US500_cash
# are aliased via _SYMBOL_ALIASES).
#
# Updating: regenerate the matrix via
#     python research/staleness_audit/compute_correlations.py
# then re-derive both the JSON file and the fallback dict below from
# `research/staleness_audit/fresh_correlation_matrix_<DATE>.json` so the two
# remain byte-equivalent (or close enough — fallback is rounded to 3dp).

_CORRELATION_JSON_PATH = (
    Path(__file__).resolve().parents[2]
    / "exports" / "multi_instrument" / "screening_results"
    / "correlation_matrix.json"
)


# Hardcoded fallback — kept rounded to 3 decimals (matches the previous
# fallback's precision; 0.001-rounding delta is well below the 0.4 cluster
# threshold and any threshold-flip semantics). Diagonal entries are omitted —
# same-symbol returns None in lookup_correlation() and the runtime filter
# would skip them anyway.
_FALLBACK_CORRELATION_TABLE: dict[str, dict[str, float]] = {
    "AUDJPY": {
        "AUDUSD": 0.747, "BTCUSD": 0.292, "CHFJPY": 0.512, "ETHUSD": 0.287,
        "EURGBP": -0.095, "EURJPY": 0.682, "EURUSD": 0.354, "GBPJPY": 0.685,
        "GBPUSD": 0.402, "GER40": 0.38, "JP225": 0.448, "NAS100": 0.467, "NZDUSD": 0.578,
        "SPX500": 0.487, "UK100": 0.387, "UKOIL_cash": -0.114, "US30_cash": 0.414,
        "USDCAD": -0.309, "USDCHF": -0.143, "USDJPY": 0.26, "USOIL_cash": -0.098,
        "XAGUSD": 0.371, "XAUUSD": 0.378,
    },
    "AUDUSD": {
        "AUDJPY": 0.747, "BTCUSD": 0.348, "CHFJPY": 0.182, "ETHUSD": 0.347,
        "EURGBP": -0.098, "EURJPY": 0.247, "EURUSD": 0.749, "GBPJPY": 0.283,
        "GBPUSD": 0.748, "GER40": 0.53, "JP225": 0.506, "NAS100": 0.564, "NZDUSD": 0.878,
        "SPX500": 0.595, "UK100": 0.507, "UKOIL_cash": -0.29, "US30_cash": 0.553,
        "USDCAD": -0.561, "USDCHF": -0.544, "USDJPY": -0.445, "USOIL_cash": -0.275,
        "XAGUSD": 0.481, "XAUUSD": 0.514,
    },
    "BTCUSD": {
        "AUDJPY": 0.292, "AUDUSD": 0.348, "CHFJPY": 0.062, "ETHUSD": 0.896,
        "EURGBP": -0.103, "EURJPY": 0.103, "EURUSD": 0.23, "GBPJPY": 0.15, "GBPUSD": 0.264,
        "GER40": 0.379, "JP225": 0.388, "NAS100": 0.49, "NZDUSD": 0.312, "SPX500": 0.479,
        "UK100": 0.341, "UKOIL_cash": -0.154, "US30_cash": 0.419, "USDCAD": -0.181,
        "USDCHF": -0.169, "USDJPY": -0.116, "USOIL_cash": -0.156, "XAGUSD": 0.29,
        "XAUUSD": 0.284,
    },
    "CHFJPY": {
        "AUDJPY": 0.512, "AUDUSD": 0.182, "BTCUSD": 0.062, "ETHUSD": 0.051,
        "EURGBP": 0.081, "EURJPY": 0.756, "EURUSD": 0.24, "GBPJPY": 0.661, "GBPUSD": 0.204,
        "GER40": 0.042, "JP225": 0.115, "NAS100": 0.059, "NZDUSD": 0.195, "SPX500": 0.06,
        "UK100": 0.049, "UKOIL_cash": 0.017, "US30_cash": 0.068, "USDCAD": -0.131,
        "USDCHF": -0.397, "USDJPY": 0.423, "USOIL_cash": 0.032, "XAGUSD": 0.127,
        "XAUUSD": 0.148,
    },
    "ETHUSD": {
        "AUDJPY": 0.287, "AUDUSD": 0.347, "BTCUSD": 0.896, "CHFJPY": 0.051,
        "EURGBP": -0.107, "EURJPY": 0.097, "EURUSD": 0.229, "GBPJPY": 0.146,
        "GBPUSD": 0.265, "GER40": 0.397, "JP225": 0.391, "NAS100": 0.503, "NZDUSD": 0.31,
        "SPX500": 0.495, "UK100": 0.35, "UKOIL_cash": -0.162, "US30_cash": 0.429,
        "USDCAD": -0.187, "USDCHF": -0.168, "USDJPY": -0.121, "USOIL_cash": -0.155,
        "XAGUSD": 0.279, "XAUUSD": 0.276,
    },
    "EURGBP": {
        "AUDJPY": -0.095, "AUDUSD": -0.098, "BTCUSD": -0.103, "CHFJPY": 0.081,
        "ETHUSD": -0.107, "EURJPY": 0.154, "EURUSD": 0.127, "GBPJPY": -0.398,
        "GBPUSD": -0.392, "GER40": -0.163, "JP225": -0.137, "NAS100": -0.165,
        "NZDUSD": -0.083, "SPX500": -0.177, "UK100": -0.101, "UKOIL_cash": 0.021,
        "US30_cash": -0.166, "USDCAD": 0.088, "USDCHF": 0.007, "USDJPY": 0.02,
        "USOIL_cash": 0.013, "XAGUSD": -0.097, "XAUUSD": -0.084,
    },
    "EURJPY": {
        "AUDJPY": 0.682, "AUDUSD": 0.247, "BTCUSD": 0.103, "CHFJPY": 0.756,
        "ETHUSD": 0.097, "EURGBP": 0.154, "EURUSD": 0.308, "GBPJPY": 0.824,
        "GBPUSD": 0.222, "GER40": 0.104, "JP225": 0.204, "NAS100": 0.151, "NZDUSD": 0.207,
        "SPX500": 0.167, "UK100": 0.099, "UKOIL_cash": 0.004, "US30_cash": 0.124,
        "USDCAD": -0.105, "USDCHF": -0.074, "USDJPY": 0.562, "USOIL_cash": -0.013,
        "XAGUSD": 0.125, "XAUUSD": 0.141,
    },
    "EURUSD": {
        "AUDJPY": 0.354, "AUDUSD": 0.749, "BTCUSD": 0.23, "CHFJPY": 0.24, "ETHUSD": 0.229,
        "EURGBP": 0.127, "EURJPY": 0.308, "GBPJPY": 0.204, "GBPUSD": 0.844, "GER40": 0.395,
        "JP225": 0.35, "NAS100": 0.361, "NZDUSD": 0.771, "SPX500": 0.388, "UK100": 0.344,
        "UKOIL_cash": -0.305, "US30_cash": 0.403, "USDCAD": -0.549, "USDCHF": -0.764,
        "USDJPY": -0.612, "USOIL_cash": -0.317, "XAGUSD": 0.35, "XAUUSD": 0.41,
    },
    "GBPJPY": {
        "AUDJPY": 0.685, "AUDUSD": 0.283, "BTCUSD": 0.15, "CHFJPY": 0.661, "ETHUSD": 0.146,
        "EURGBP": -0.398, "EURJPY": 0.824, "EURUSD": 0.204, "GBPUSD": 0.438,
        "GER40": 0.176, "JP225": 0.254, "NAS100": 0.221, "NZDUSD": 0.248, "SPX500": 0.24,
        "UK100": 0.135, "UKOIL_cash": -0.007, "US30_cash": 0.197, "USDCAD": -0.12,
        "USDCHF": -0.037, "USDJPY": 0.508, "USOIL_cash": -0.011, "XAGUSD": 0.166,
        "XAUUSD": 0.177,
    },
    "GBPUSD": {
        "AUDJPY": 0.402, "AUDUSD": 0.748, "BTCUSD": 0.264, "CHFJPY": 0.204,
        "ETHUSD": 0.265, "EURGBP": -0.392, "EURJPY": 0.222, "EURUSD": 0.844,
        "GBPJPY": 0.438, "GER40": 0.435, "JP225": 0.383, "NAS100": 0.407, "NZDUSD": 0.766,
        "SPX500": 0.436, "UK100": 0.355, "UKOIL_cash": -0.285, "US30_cash": 0.444,
        "USDCAD": -0.52, "USDCHF": -0.658, "USDJPY": -0.547, "USOIL_cash": -0.283,
        "XAGUSD": 0.366, "XAUUSD": 0.419,
    },
    "GER40": {
        "AUDJPY": 0.38, "AUDUSD": 0.53, "BTCUSD": 0.379, "CHFJPY": 0.042, "ETHUSD": 0.397,
        "EURGBP": -0.163, "EURJPY": 0.104, "EURUSD": 0.395, "GBPJPY": 0.176,
        "GBPUSD": 0.435, "JP225": 0.73, "NAS100": 0.753, "NZDUSD": 0.489, "SPX500": 0.813,
        "UK100": 0.799, "UKOIL_cash": -0.463, "US30_cash": 0.778, "USDCAD": -0.278,
        "USDCHF": -0.302, "USDJPY": -0.257, "USOIL_cash": -0.514, "XAGUSD": 0.334,
        "XAUUSD": 0.352,
    },
    "JP225": {
        "AUDJPY": 0.448, "AUDUSD": 0.506, "BTCUSD": 0.388, "CHFJPY": 0.115,
        "ETHUSD": 0.391, "EURGBP": -0.137, "EURJPY": 0.204, "EURUSD": 0.35,
        "GBPJPY": 0.254, "GBPUSD": 0.383, "GER40": 0.73, "NAS100": 0.74, "NZDUSD": 0.461,
        "SPX500": 0.767, "UK100": 0.666, "UKOIL_cash": -0.365, "US30_cash": 0.719,
        "USDCAD": -0.247, "USDCHF": -0.244, "USDJPY": -0.137, "USOIL_cash": -0.469,
        "XAGUSD": 0.354, "XAUUSD": 0.351,
    },
    "NAS100": {
        "AUDJPY": 0.467, "AUDUSD": 0.564, "BTCUSD": 0.49, "CHFJPY": 0.059, "ETHUSD": 0.503,
        "EURGBP": -0.165, "EURJPY": 0.151, "EURUSD": 0.361, "GBPJPY": 0.221,
        "GBPUSD": 0.407, "GER40": 0.753, "JP225": 0.74, "NZDUSD": 0.506, "SPX500": 0.96,
        "UK100": 0.641, "UKOIL_cash": -0.338, "US30_cash": 0.792, "USDCAD": -0.31,
        "USDCHF": -0.251, "USDJPY": -0.186, "USOIL_cash": -0.414, "XAGUSD": 0.353,
        "XAUUSD": 0.357,
    },
    "NZDUSD": {
        "AUDJPY": 0.578, "AUDUSD": 0.878, "BTCUSD": 0.312, "CHFJPY": 0.195, "ETHUSD": 0.31,
        "EURGBP": -0.083, "EURJPY": 0.207, "EURUSD": 0.771, "GBPJPY": 0.248,
        "GBPUSD": 0.766, "GER40": 0.489, "JP225": 0.461, "NAS100": 0.506, "SPX500": 0.533,
        "UK100": 0.456, "UKOIL_cash": -0.288, "US30_cash": 0.512, "USDCAD": -0.553,
        "USDCHF": -0.594, "USDJPY": -0.496, "USOIL_cash": -0.285, "XAGUSD": 0.439,
        "XAUUSD": 0.472,
    },
    "SPX500": {
        "AUDJPY": 0.487, "AUDUSD": 0.595, "BTCUSD": 0.479, "CHFJPY": 0.06, "ETHUSD": 0.495,
        "EURGBP": -0.177, "EURJPY": 0.167, "EURUSD": 0.388, "GBPJPY": 0.24,
        "GBPUSD": 0.436, "GER40": 0.813, "JP225": 0.767, "NAS100": 0.96, "NZDUSD": 0.533,
        "UK100": 0.719, "UKOIL_cash": -0.388, "US30_cash": 0.906, "USDCAD": -0.333,
        "USDCHF": -0.263, "USDJPY": -0.191, "USOIL_cash": -0.47, "XAGUSD": 0.348,
        "XAUUSD": 0.355,
    },
    "UK100": {
        "AUDJPY": 0.387, "AUDUSD": 0.507, "BTCUSD": 0.341, "CHFJPY": 0.049, "ETHUSD": 0.35,
        "EURGBP": -0.101, "EURJPY": 0.099, "EURUSD": 0.344, "GBPJPY": 0.135,
        "GBPUSD": 0.355, "GER40": 0.799, "JP225": 0.666, "NAS100": 0.641, "NZDUSD": 0.456,
        "SPX500": 0.719, "UKOIL_cash": -0.328, "US30_cash": 0.712, "USDCAD": -0.283,
        "USDCHF": -0.274, "USDJPY": -0.217, "USOIL_cash": -0.402, "XAGUSD": 0.334,
        "XAUUSD": 0.346,
    },
    "UKOIL_cash": {
        "AUDJPY": -0.114, "AUDUSD": -0.29, "BTCUSD": -0.154, "CHFJPY": 0.017,
        "ETHUSD": -0.162, "EURGBP": 0.021, "EURJPY": 0.004, "EURUSD": -0.305,
        "GBPJPY": -0.007, "GBPUSD": -0.285, "GER40": -0.463, "JP225": -0.365,
        "NAS100": -0.338, "NZDUSD": -0.288, "SPX500": -0.388, "UK100": -0.328,
        "US30_cash": -0.392, "USDCAD": 0.076, "USDCHF": 0.248, "USDJPY": 0.272,
        "USOIL_cash": 0.827, "XAGUSD": -0.113, "XAUUSD": -0.158,
    },
    "US30_cash": {
        "AUDJPY": 0.414, "AUDUSD": 0.553, "BTCUSD": 0.419, "CHFJPY": 0.068,
        "ETHUSD": 0.429, "EURGBP": -0.166, "EURJPY": 0.124, "EURUSD": 0.403,
        "GBPJPY": 0.197, "GBPUSD": 0.444, "GER40": 0.778, "JP225": 0.719, "NAS100": 0.792,
        "NZDUSD": 0.512, "SPX500": 0.906, "UK100": 0.712, "UKOIL_cash": -0.392,
        "USDCAD": -0.32, "USDCHF": -0.317, "USDJPY": -0.247, "USOIL_cash": -0.504,
        "XAGUSD": 0.34, "XAUUSD": 0.346,
    },
    "USDCAD": {
        "AUDJPY": -0.309, "AUDUSD": -0.561, "BTCUSD": -0.181, "CHFJPY": -0.131,
        "ETHUSD": -0.187, "EURGBP": 0.088, "EURJPY": -0.105, "EURUSD": -0.549,
        "GBPJPY": -0.12, "GBPUSD": -0.52, "GER40": -0.278, "JP225": -0.247,
        "NAS100": -0.31, "NZDUSD": -0.553, "SPX500": -0.333, "UK100": -0.283,
        "UKOIL_cash": 0.076, "US30_cash": -0.32, "USDCHF": 0.532, "USDJPY": 0.379,
        "USOIL_cash": 0.066, "XAGUSD": -0.379, "XAUUSD": -0.399,
    },
    "USDCHF": {
        "AUDJPY": -0.143, "AUDUSD": -0.544, "BTCUSD": -0.169, "CHFJPY": -0.397,
        "ETHUSD": -0.168, "EURGBP": 0.007, "EURJPY": -0.074, "EURUSD": -0.764,
        "GBPJPY": -0.037, "GBPUSD": -0.658, "GER40": -0.302, "JP225": -0.244,
        "NAS100": -0.251, "NZDUSD": -0.594, "SPX500": -0.263, "UK100": -0.274,
        "UKOIL_cash": 0.248, "US30_cash": -0.317, "USDCAD": 0.532, "USDJPY": 0.606,
        "USOIL_cash": 0.246, "XAGUSD": -0.306, "XAUUSD": -0.353,
    },
    "USDJPY": {
        "AUDJPY": 0.26, "AUDUSD": -0.445, "BTCUSD": -0.116, "CHFJPY": 0.423,
        "ETHUSD": -0.121, "EURGBP": 0.02, "EURJPY": 0.562, "EURUSD": -0.612,
        "GBPJPY": 0.508, "GBPUSD": -0.547, "GER40": -0.257, "JP225": -0.137,
        "NAS100": -0.186, "NZDUSD": -0.496, "SPX500": -0.191, "UK100": -0.217,
        "UKOIL_cash": 0.272, "US30_cash": -0.247, "USDCAD": 0.379, "USDCHF": 0.606,
        "USOIL_cash": 0.256, "XAGUSD": -0.2, "XAUUSD": -0.239,
    },
    "USOIL_cash": {
        "AUDJPY": -0.098, "AUDUSD": -0.275, "BTCUSD": -0.156, "CHFJPY": 0.032,
        "ETHUSD": -0.155, "EURGBP": 0.013, "EURJPY": -0.013, "EURUSD": -0.317,
        "GBPJPY": -0.011, "GBPUSD": -0.283, "GER40": -0.514, "JP225": -0.469,
        "NAS100": -0.414, "NZDUSD": -0.285, "SPX500": -0.47, "UK100": -0.402,
        "UKOIL_cash": 0.827, "US30_cash": -0.504, "USDCAD": 0.066, "USDCHF": 0.246,
        "USDJPY": 0.256, "XAGUSD": -0.084, "XAUUSD": -0.1,
    },
    "XAGUSD": {
        "AUDJPY": 0.371, "AUDUSD": 0.481, "BTCUSD": 0.29, "CHFJPY": 0.127, "ETHUSD": 0.279,
        "EURGBP": -0.097, "EURJPY": 0.125, "EURUSD": 0.35, "GBPJPY": 0.166,
        "GBPUSD": 0.366, "GER40": 0.334, "JP225": 0.354, "NAS100": 0.353, "NZDUSD": 0.439,
        "SPX500": 0.348, "UK100": 0.334, "UKOIL_cash": -0.113, "US30_cash": 0.34,
        "USDCAD": -0.379, "USDCHF": -0.306, "USDJPY": -0.2, "USOIL_cash": -0.084,
        "XAUUSD": 0.799,
    },
    "XAUUSD": {
        "AUDJPY": 0.378, "AUDUSD": 0.514, "BTCUSD": 0.284, "CHFJPY": 0.148,
        "ETHUSD": 0.276, "EURGBP": -0.084, "EURJPY": 0.141, "EURUSD": 0.41,
        "GBPJPY": 0.177, "GBPUSD": 0.419, "GER40": 0.352, "JP225": 0.351, "NAS100": 0.357,
        "NZDUSD": 0.472, "SPX500": 0.355, "UK100": 0.346, "UKOIL_cash": -0.158,
        "US30_cash": 0.346, "USDCAD": -0.399, "USDCHF": -0.353, "USDJPY": -0.239,
        "USOIL_cash": -0.1, "XAGUSD": 0.799,
    },
}


# Symbol aliases — broker-specific naming variants map to the canonical
# screening-table key. Keeps the gate working when MT5 returns broker aliases
# (``US30.cash``) or futures contracts (``YM``, ``ESM26-CME``) while the
# screening JSON is keyed by CFD-style matrix symbols.
_SYMBOL_ALIASES: dict[str, str] = {
    "US30": "US30_cash",
    "US30_CASH": "US30_cash",
    "US30.cash": "US30_cash",
    "US500": "SPX500",
    "US500_CASH": "SPX500",
    "US500.cash": "SPX500",
    "SPX500": "SPX500",
    "USOIL": "USOIL_cash",
    "USOIL.cash": "USOIL_cash",
}

_VNEXT_FAMILY_TO_CORRELATION_SYMBOL: dict[str, str] = {
    "EURUSD_6E_FAMILY": "EURUSD",
    "GBPUSD_6B_FAMILY": "GBPUSD",
    "NAS100_NQ_FAMILY": "NAS100",
    "SPX500_ES_FAMILY": "SPX500",
    "US30_YM_FAMILY": "US30_cash",
    "USDJPY_6J_FAMILY": "USDJPY",
    "XAGUSD_SILVER_FAMILY": "XAGUSD",
    "XAUUSD_GC_FAMILY": "XAUUSD",
}


def _canonicalize(symbol: str) -> str:
    """Return canonical form of *symbol* per ``_SYMBOL_ALIASES``.

    Returns *symbol* unchanged if no alias is registered. Idempotent.
    """
    if not symbol:
        return symbol
    family = resolve_vnext_symbol_family(symbol)
    if family in _VNEXT_FAMILY_TO_CORRELATION_SYMBOL:
        return _VNEXT_FAMILY_TO_CORRELATION_SYMBOL[family]
    key = normalize_vnext_symbol_key(symbol)
    return _SYMBOL_ALIASES.get(symbol) or _SYMBOL_ALIASES.get(key) or symbol


def _load_correlation_table() -> dict[str, dict[str, float]]:
    """Load the correlation matrix from JSON, falling back to the hardcoded copy.

    Failures are logged at WARN — the gate must continue to function with the
    fallback rather than disable itself silently. Both branches return a
    pre-canonicalized table (keys already match canonical symbol names).
    """
    if not _CORRELATION_JSON_PATH.exists():
        logger.info(
            "cross_instrument_corr: matrix JSON not found at %s, using fallback table",
            _CORRELATION_JSON_PATH,
        )
        return _FALLBACK_CORRELATION_TABLE
    try:
        with open(_CORRELATION_JSON_PATH, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(
            "cross_instrument_corr: failed to read matrix JSON (%s); using fallback table: %s",
            _CORRELATION_JSON_PATH, e,
        )
        return _FALLBACK_CORRELATION_TABLE

    # Strip diagonal entries (self-correlation) — keep float coercion defensive.
    normalized: dict[str, dict[str, float]] = {}
    for sym, row in raw.items():
        if not isinstance(row, dict):
            continue
        clean: dict[str, float] = {}
        for other, val in row.items():
            if other == sym:
                continue
            try:
                clean[other] = float(val)
            except (TypeError, ValueError):
                continue
        normalized[sym] = clean
    return normalized


# Module-level cache; tests can override via ``set_correlation_table()``.
_CORRELATION_TABLE: dict[str, dict[str, float]] = _load_correlation_table()


def get_correlation_table() -> dict[str, dict[str, float]]:
    """Return the active correlation table (read-only handle)."""
    return _CORRELATION_TABLE


def set_correlation_table(table: dict[str, dict[str, float]]) -> None:
    """Override the correlation table — TESTS ONLY.

    Production code never calls this. Tests use it to inject deterministic
    correlations without depending on the screening-export file.
    """
    global _CORRELATION_TABLE
    _CORRELATION_TABLE = table


def lookup_correlation(symbol_a: str, symbol_b: str) -> Optional[float]:
    """Return Pearson correlation between two symbols, or None if unknown.

    Symmetric: lookup(A, B) == lookup(B, A) when both directions exist.
    Same-symbol returns None (not 1.0) because same-symbol clusters are handled
    by the explicit vNext lifecycle conflict gate, not this cross-symbol gate.
    """
    if not symbol_a or not symbol_b:
        return None
    a = _canonicalize(symbol_a)
    b = _canonicalize(symbol_b)
    if a == b:
        return None
    table = _CORRELATION_TABLE
    row = table.get(a)
    if row and b in row:
        return row[b]
    row_b = table.get(b)
    if row_b and a in row_b:
        return row_b[a]
    return None


# ============================================================================
# Result types
# ============================================================================

GateAction = Literal["NONE", "RISK_REDUCE_HALF", "REJECT"]


@dataclass
class CrossInstrumentCorrelationResult:
    """Outcome of a cross-instrument correlation check.

    Attributes
    ----------
    action : str
        ``"NONE"`` (no action), ``"RISK_REDUCE_HALF"`` (halve sizing only),
        or ``"REJECT"`` (block the trade).
    risk_multiplier : float
        Factor to apply to the resolved per-trade risk pct. ``1.0`` for
        NONE/REJECT (REJECT halts before sizing matters), ``0.5`` for
        RISK_REDUCE_HALF.
    correlated_positions : list of dict
        Open positions that contributed to the cluster, each
        ``{"symbol": str, "direction": str, "correlation": float}``.
        Useful for telemetry; not required by the gate.
    threshold : float
        Effective ``correlation_threshold`` used for this evaluation.
    min_positions : int
        Effective ``min_positions`` floor used for this evaluation.
    reason : str
        Short string suitable for logs / ExecutionDenial.reason.
    """
    action: GateAction
    risk_multiplier: float
    correlated_positions: list[dict[str, Any]] = field(default_factory=list)
    threshold: float = 0.4
    min_positions: int = 2
    reason: str = "no_action"

    @property
    def adjusted(self) -> bool:
        """True when the gate altered behavior (HALVE or REJECT)."""
        return self.action != "NONE"


# ============================================================================
# Core check
# ============================================================================

def _resolve_positions(mt5: Any) -> list[dict[str, Any]]:
    """Best-effort cross-symbol position fetch shaped for the gate.

    Returns a list of ``{"symbol": str, "direction": "LONG"|"SHORT"}`` for
    every open GTOS position visible to the MT5 wrapper. Mirrors the dual
    code path used by ``concurrent_tracker.get_filled_position_count``:
    raw MetaTrader5 module first (RealMT5), MockMT5._positions fallback,
    fail-open empty list on any exception.
    """
    if mt5 is None:
        return []

    # Lazy import to avoid pulling MT5 init into module-load time.
    try:
        from src.mt5.mt5_interface import MAGIC_NUMBER
    except Exception:  # noqa: BLE001 — defensive
        MAGIC_NUMBER = None

    # Raw MetaTrader5 module path — RealMT5 stashes it as ``_mt5``.
    raw = getattr(mt5, "_mt5", None)
    if raw is not None and hasattr(raw, "positions_get"):
        try:
            positions = raw.positions_get() or []
        except Exception as e:  # noqa: BLE001 — fail open
            logger.warning(
                "cross_instrument_corr: positions_get failed; failing open: %s", e,
            )
            return []
        out: list[dict[str, Any]] = []
        for p in positions:
            magic = getattr(p, "magic", None)
            if MAGIC_NUMBER is not None and magic != MAGIC_NUMBER:
                continue
            sym = getattr(p, "symbol", None)
            ptype = getattr(p, "type", None)
            if sym is None or ptype is None:
                continue
            direction = "LONG" if ptype == 0 else "SHORT" if ptype == 1 else None
            if direction is None:
                continue
            out.append({"symbol": sym, "direction": direction})
        return out

    # Test-double / explicit module path — same as concurrent_tracker.
    if hasattr(mt5, "positions_get"):
        try:
            positions = mt5.positions_get() or []
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "cross_instrument_corr: positions_get failed; failing open: %s", e,
            )
            return []
        out_2: list[dict[str, Any]] = []
        for p in positions:
            magic = getattr(p, "magic", None)
            if MAGIC_NUMBER is not None and magic is not None and magic != MAGIC_NUMBER:
                continue
            sym = getattr(p, "symbol", None)
            ptype = getattr(p, "type", None)
            if sym is None or ptype is None:
                continue
            direction = "LONG" if ptype == 0 else "SHORT" if ptype == 1 else None
            if direction is None:
                continue
            out_2.append({"symbol": sym, "direction": direction})
        return out_2

    # MockMT5._positions fallback — same dual path as concurrent_tracker.
    positions_attr = getattr(mt5, "_positions", None)
    if positions_attr is not None:
        out_3: list[dict[str, Any]] = []
        for p in positions_attr:
            magic = getattr(p, "magic", None)
            if MAGIC_NUMBER is not None and magic != MAGIC_NUMBER:
                continue
            sym = getattr(p, "symbol", None)
            ptype = getattr(p, "type", None)
            if sym is None or ptype is None:
                continue
            direction = "LONG" if ptype == 0 else "SHORT" if ptype == 1 else None
            if direction is None:
                continue
            out_3.append({"symbol": sym, "direction": direction})
        return out_3

    return []


def _is_same_directional_cluster(
    candidate_direction: str,
    open_direction: str,
    correlation: float,
    threshold: float,
) -> bool:
    """True iff the open position amplifies the candidate's directional risk.

    Logic table (positive r = positions move together; negative = inversely):

        candidate=LONG  open=LONG   r >= +threshold  -> AMPLIFY
        candidate=SHORT open=SHORT  r >= +threshold  -> AMPLIFY
        candidate=LONG  open=SHORT  r <= -threshold  -> AMPLIFY
        candidate=SHORT open=LONG   r <= -threshold  -> AMPLIFY
        anything else                                -> NOT AMPLIFY (hedge or weak)
    """
    if candidate_direction not in ("LONG", "SHORT"):
        return False
    if open_direction not in ("LONG", "SHORT"):
        return False
    same_sign = candidate_direction == open_direction
    if same_sign:
        return correlation >= threshold
    return correlation <= -threshold


def check_cross_instrument_correlation(
    candidate_symbol: str,
    candidate_direction: str,
    mt5: Any = None,
    *,
    correlation_threshold: float = 0.4,
    min_correlated_positions: int = 2,
    open_positions: Optional[list[dict[str, Any]]] = None,
    pair_budget_groups: Optional[list[dict[str, Any]]] = None,
) -> CrossInstrumentCorrelationResult:
    """Decide whether the cross-instrument correlation cluster warrants action.

    Parameters
    ----------
    candidate_symbol : str
        Symbol of the new trade under consideration. Aliased via
        ``_SYMBOL_ALIASES`` before lookup.
    candidate_direction : "LONG" | "SHORT"
        Direction of the new trade. Used to determine whether each open
        position amplifies or hedges the candidate's exposure.
    mt5 : MT5Interface | None
        MT5 wrapper. Used to enumerate open GTOS positions when
        ``open_positions`` is not provided. ``None`` -> empty cluster.
    correlation_threshold : float
        Minimum |Pearson correlation| for an open position to count toward
        the cluster. 0.4 default; conservative — won't trigger on the
        crossed-pair noise floor (~0.2-0.3).
    min_correlated_positions : int
        Cluster size at which RISK_REDUCE_HALF triggers. ``+1`` triggers
        REJECT. Default 2 / 3.
    open_positions : list of dict, optional
        Pre-resolved positions in
        ``[{"symbol": str, "direction": "LONG"|"SHORT"}, ...]`` form.
        When provided, ``mt5`` is ignored. Used by tests to avoid an MT5
        dependency.
    pair_budget_groups : list of dict, optional
        Exact shared-exposure groups where one correlated peer position is
        enough to reduce risk without changing the broader cluster threshold.

    Returns
    -------
    CrossInstrumentCorrelationResult
        Action, risk multiplier, contributing positions.

    Notes
    -----
    Same-symbol positions are skipped; vNext same-symbol exposure is governed
    by the explicit lifecycle conflict gate.
    Positions on symbols without a correlation entry are skipped — the
    gate is silent on uninstrumented pairs rather than fail-closed.
    """
    if open_positions is None:
        open_positions = _resolve_positions(mt5)

    if not open_positions:
        return CrossInstrumentCorrelationResult(
            action="NONE",
            risk_multiplier=1.0,
            correlated_positions=[],
            threshold=correlation_threshold,
            min_positions=min_correlated_positions,
            reason="no_open_positions",
        )

    # Defensive coercion — config could feed non-int / non-float values.
    try:
        threshold = float(correlation_threshold)
    except (TypeError, ValueError):
        threshold = 0.4
    threshold = abs(threshold)
    try:
        min_positions = int(min_correlated_positions)
    except (TypeError, ValueError):
        min_positions = 2
    if min_positions < 1:
        min_positions = 1

    candidate_canonical = _canonicalize(candidate_symbol)
    cluster: list[dict[str, Any]] = []
    for pos in open_positions:
        pos_symbol = pos.get("symbol", "")
        pos_direction = pos.get("direction", "")
        if not pos_symbol or not pos_direction:
            continue
        pos_canonical = _canonicalize(pos_symbol)
        if pos_canonical == candidate_canonical:
            # Same-symbol vNext exposure is handled before this cross-symbol gate.
            continue
        corr = lookup_correlation(candidate_canonical, pos_canonical)
        if corr is None:
            continue
        if abs(corr) < threshold:
            continue
        if not _is_same_directional_cluster(
            candidate_direction, pos_direction, corr, threshold,
        ):
            continue
        cluster.append({
            "symbol": pos_symbol,
            "direction": pos_direction,
            "correlation": corr,
        })

    cluster_size = len(cluster)
    reject_floor = min_positions + 1

    if cluster_size >= reject_floor:
        logger.warning(
            "CROSS_INSTRUMENT_CORR_REJECT: %s %s — %d correlated same-direction "
            "positions (>= reject floor %d); cluster=%s",
            candidate_symbol, candidate_direction, cluster_size,
            reject_floor, cluster,
        )
        return CrossInstrumentCorrelationResult(
            action="REJECT",
            risk_multiplier=1.0,  # Sizing irrelevant when rejecting.
            correlated_positions=cluster,
            threshold=threshold,
            min_positions=min_positions,
            reason=(
                f"cross_instrument_correlation_excess: {cluster_size} same-direction "
                f"correlated positions (>= reject floor {reject_floor})"
            ),
        )

    if cluster_size >= min_positions:
        logger.info(
            "CROSS_INSTRUMENT_CORR_HALVE: %s %s — %d correlated same-direction "
            "positions (>= halve threshold %d); cluster=%s",
            candidate_symbol, candidate_direction, cluster_size,
            min_positions, cluster,
        )
        return CrossInstrumentCorrelationResult(
            action="RISK_REDUCE_HALF",
            risk_multiplier=0.5,
            correlated_positions=cluster,
            threshold=threshold,
            min_positions=min_positions,
            reason=(
                f"cross_instrument_correlation_cluster: {cluster_size} same-direction "
                f"correlated positions (>= halve threshold {min_positions}); "
                f"halving risk"
            ),
        )

    pair_budget = _match_pair_budget_group(
        candidate_canonical=candidate_canonical,
        cluster=cluster,
        pair_budget_groups=pair_budget_groups or [],
    )
    if pair_budget is not None:
        multiplier = pair_budget["risk_multiplier"]
        group_name = pair_budget["name"]
        logger.info(
            "CROSS_INSTRUMENT_PAIR_BUDGET_HALVE: %s %s group=%s peers=%s",
            candidate_symbol, candidate_direction, group_name,
            pair_budget["matched_symbols"],
        )
        return CrossInstrumentCorrelationResult(
            action="RISK_REDUCE_HALF",
            risk_multiplier=multiplier,
            correlated_positions=pair_budget["matched_positions"],
            threshold=threshold,
            min_positions=min_positions,
            reason=(
                f"cross_instrument_pair_budget: {group_name} shared exposure "
                f"with {pair_budget['matched_symbols']}; risk multiplier {multiplier}"
            ),
        )

    return CrossInstrumentCorrelationResult(
        action="NONE",
        risk_multiplier=1.0,
        correlated_positions=cluster,
        threshold=threshold,
        min_positions=min_positions,
        reason="below_cluster_threshold",
    )


# ============================================================================
# Config helpers
# ============================================================================

def is_enabled(config: Optional[dict[str, Any]]) -> bool:
    """Whether the gate is active per config (default True)."""
    risk_cfg = (config or {}).get("risk", {}) or {}
    return bool(risk_cfg.get("cross_instrument_correlation_enabled", True))


def resolve_threshold(config: Optional[dict[str, Any]]) -> float:
    """Resolve the configured correlation threshold (default 0.4)."""
    risk_cfg = (config or {}).get("risk", {}) or {}
    raw = risk_cfg.get("cross_instrument_correlation_threshold", 0.4)
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return 0.4
    return val


def resolve_min_positions(config: Optional[dict[str, Any]]) -> int:
    """Resolve the configured halve-cluster floor (default 2)."""
    risk_cfg = (config or {}).get("risk", {}) or {}
    raw = risk_cfg.get("cross_instrument_correlation_min_positions", 2)
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return 2
    if val < 1:
        return 1
    return val


def resolve_pair_budget_groups(config: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve exact shared-exposure pair-budget groups from config."""
    risk_cfg = (config or {}).get("risk", {}) or {}
    if not bool(risk_cfg.get("cross_instrument_pair_budget_enabled", False)):
        return []
    raw_groups = risk_cfg.get("cross_instrument_pair_budget_groups", [])
    if not isinstance(raw_groups, list):
        return []
    groups: list[dict[str, Any]] = []
    for item in raw_groups:
        if not isinstance(item, dict):
            continue
        raw_instruments = item.get("instruments", [])
        if not isinstance(raw_instruments, list):
            continue
        instruments = sorted(
            {
                _canonicalize(str(symbol))
                for symbol in raw_instruments
                if str(symbol or "").strip()
            }
        )
        if len(instruments) < 2:
            continue
        try:
            multiplier = float(item.get("risk_multiplier", 0.5))
        except (TypeError, ValueError):
            multiplier = 0.5
        if multiplier <= 0 or multiplier >= 1:
            multiplier = 0.5
        groups.append({
            "name": str(item.get("name") or "PAIR_BUDGET"),
            "instruments": instruments,
            "risk_multiplier": multiplier,
            "source_path": item.get("source_path"),
            "source_line_no": item.get("source_line_no"),
        })
    return groups


def _match_pair_budget_group(
    *,
    candidate_canonical: str,
    cluster: list[dict[str, Any]],
    pair_budget_groups: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not cluster or not pair_budget_groups:
        return None
    for group in pair_budget_groups:
        instruments = set(group.get("instruments") or [])
        if candidate_canonical not in instruments:
            continue
        matched_positions = [
            pos
            for pos in cluster
            if _canonicalize(pos.get("symbol", "")) in instruments
        ]
        if not matched_positions:
            continue
        return {
            "name": group.get("name") or "PAIR_BUDGET",
            "risk_multiplier": group.get("risk_multiplier", 0.5),
            "matched_positions": matched_positions,
            "matched_symbols": sorted({pos.get("symbol", "") for pos in matched_positions}),
        }
    return None


def evaluate_for_candidate(
    candidate_symbol: str,
    candidate_direction: str,
    mt5: Any,
    config: Optional[dict[str, Any]] = None,
    evaluation_context: str | None = None,
) -> CrossInstrumentCorrelationResult:
    """Convenience: resolve config + run check in one call.

    Returns a NONE result without consulting MT5 when the gate is disabled.
    """
    if not is_enabled(config):
        result = CrossInstrumentCorrelationResult(
            action="NONE",
            risk_multiplier=1.0,
            correlated_positions=[],
            threshold=resolve_threshold(config),
            min_positions=resolve_min_positions(config),
            reason="gate_disabled",
        )
        log_cross_instrument_correlation_decision(
            candidate_symbol=candidate_symbol,
            candidate_direction=candidate_direction,
            result=result,
            config=config,
            evaluation_context=evaluation_context,
        )
        return result
    result = check_cross_instrument_correlation(
        candidate_symbol,
        candidate_direction,
        mt5,
        correlation_threshold=resolve_threshold(config),
        min_correlated_positions=resolve_min_positions(config),
        pair_budget_groups=resolve_pair_budget_groups(config),
    )
    log_cross_instrument_correlation_decision(
        candidate_symbol=candidate_symbol,
        candidate_direction=candidate_direction,
        result=result,
        config=config,
        evaluation_context=evaluation_context,
    )
    return result


def apply_risk_multiplier(base_risk_pct: float,
                          result: CrossInstrumentCorrelationResult) -> float:
    """Apply the gate's risk multiplier to a base risk pct.

    Used by the orchestrator at sizing time to layer this gate's HALVE
    response on top of the existing correlation_risk adjustment. REJECT
    short-circuits before this is reached, so the multiplier of 1.0 is
    intentional safety in case the call path is misordered.
    """
    try:
        base = float(base_risk_pct)
    except (TypeError, ValueError):
        return base_risk_pct
    multiplier = result.risk_multiplier if result is not None else 1.0
    if multiplier >= 1.0:
        return base
    return round(base * multiplier, 4)
