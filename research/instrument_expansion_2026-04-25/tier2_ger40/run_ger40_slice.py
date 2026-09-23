#!/usr/bin/env python3
"""GER40 Tier-2 Instrument Expansion — F3-style 12-slice backtest wrapper.

Wraps `scripts/simulate_t7_live_period.py` for GER40, injecting:
  - GER40 entry into the runtime config (no agent_config.yaml mutation)
  - GER40 KZ window (London-late 10:00-12:00 + NY-afternoon 14:00-19:00 UTC,
    per `research/instrument_expansion_2026-04-25/03_MICROSTRUCTURE.md` §3.2-3.3
    natural-density windows: 13.4% London-late at 1.74×, 30.7% NY-afternoon
    at 1.70× over uniform baseline)
  - GER40 fill epsilon (2.0 = 2 × 1.0 tick like NAS100/US30)

Usage::

    python run_ger40_slice.py --start 2026-01-02 --end 2026-01-09 \
        --slice-tag s01 --budget 3.0

The wrapper only patches sim-side dicts; it does not write to
agent_config.yaml or any committed file. Output: `slices/<slice-tag>/`.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import logging
import os
import sys
from datetime import time
from pathlib import Path

from dotenv import load_dotenv

# Project root — research/instrument_expansion_2026-04-25/tier2_ger40/run_ger40_slice.py
_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[3]
sys.path.insert(0, str(_PROJECT_ROOT))

load_dotenv(_PROJECT_ROOT / ".env", override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger("run_ger40_slice")


# ── GER40 instrument config (deep-merged on top of base config) ─────────
# Sourced proportionally from NAS100 (similar index microstructure):
#   ATR-M15(NAS100)=40.7, ATR-M15(GER40)=57.79 → scale = 1.42
#   round-number step 50.0 (per per_instrument_scorecard.csv)
#   pip_size 1.0
#
# Spread (FTMO published, microstructure §1.1): typ 1.4 pts, p99 5.5 pts
# R-cost typ 3.10% (best-tier per microstructure §1.2).
GER40_OVERRIDES: dict = {
    "trading_enabled": False,  # Research-only — never trade GER40 in this run.
    "skip_first_ny_candle": False,
    "market": {
        "symbol": "GER40",
        "kill_zones": {
            # Microstructure §3.2 GER40 natural-density windows:
            # 14:00-19:00 (30.7% / 1.70×) + 10:00-12:00 (13.4% / 1.74×).
            "london": {
                "start_utc": "10:00",
                "end_utc": "12:00",
                "core_end_utc": "12:00",
            },
            "ny": {
                "start_utc": "14:00",
                "end_utc": "19:00",
                "core_end_utc": "16:30",
            },
        },
    },
    "risk": {
        # CFD; broker-dependent contract size, set provisionally
        "contract_size": 1,
        "max_spread_cents": 800,        # 8 pts
        "sl_buffer_dollars": 5.30,      # ~5% of M15 ATR (57.79)
        "sl_absolute_min": 38.0,        # ~P25 OB zone height × 0.7 proportional
    },
    "model_a": {
        "equal_level_tolerance": 11.20,  # NAS100 7.87 × (57.79/40.72)
    },
    "data": {
        "fvg_min_gap": {
            "D1": 42.0,
            "H4": 25.1,
            "H1": 16.7,
            "M15": 8.4,
        },
    },
    "m5_refinement": {
        "sl_floor": 83.7,                # 50% of H1 ATR (~167)
    },
    "prompt": {
        "zone_width_max": 127.6,         # NAS100 90 × 1.42
        "ob_buffer": 5.30,
        "price_format": ".2f",
    },
    "confidence": {
        "price_regex": r"\b(\d{5}\.\d{1,2})\b",
        "price_range": [15000.0, 30000.0],
    },
}


def _patch_simulator() -> None:
    """Monkeypatch GER40-specific dicts into the sim module + apply_instrument_overrides."""
    import scripts.simulate_t7_live_period as sim
    import src.utils.config as ucfg

    # 1. KZ_WINDOWS — add GER40 entry. Used by enumerate_kz_candles().
    sim.KZ_WINDOWS["GER40"] = {
        "london": (time(10, 0), time(12, 0)),
        "ny":     (time(14, 0), time(19, 0)),
    }
    logger.info("Patched KZ_WINDOWS[GER40] = London 10-12, NY 14-19 UTC")

    # 2. EPSILON_BY_SYMBOL — add GER40 fill epsilon (2 × 1.0 tick like indices).
    sim.EPSILON_BY_SYMBOL["GER40"] = 2.0
    logger.info("Patched EPSILON_BY_SYMBOL[GER40] = 2.0 (2 × 1.0 tick)")

    # 3. apply_instrument_overrides — wrap to inject GER40 entry on the fly.
    _original_apply = ucfg.apply_instrument_overrides

    def _patched_apply(config: dict, symbol: str | None = None) -> dict:
        if symbol == "GER40" and "GER40" not in (config.get("instruments") or {}):
            cfg = copy.deepcopy(config)
            cfg.setdefault("instruments", {})["GER40"] = GER40_OVERRIDES
            return _original_apply(cfg, symbol)
        return _original_apply(config, symbol)

    ucfg.apply_instrument_overrides = _patched_apply
    # The simulator imports the symbol directly at line 621:
    #   from src.utils.config import apply_instrument_overrides
    # so we must also patch the in-module reference.
    sim.apply_instrument_overrides = _patched_apply
    logger.info("Patched apply_instrument_overrides to inject GER40 overrides at runtime")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--slice-tag", required=True)
    p.add_argument("--budget", type=float, default=3.0)
    p.add_argument("--data-dir", default=str(_PROJECT_ROOT / "data" / "historical_2026"))
    p.add_argument("--detector-version", default=None,
                   help="Optional --detector-version override (default: read from agent_config.yaml = v2_shadow).")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    out_dir = _THIS.parent / "slices" / args.slice_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    _patch_simulator()

    import scripts.simulate_t7_live_period as sim

    sim.OUTPUT_DIR = out_dir

    sim_args = argparse.Namespace(
        source="csv",
        start=args.start,
        end=args.end,
        symbol="GER40",
        budget=args.budget,
        dry_run=args.dry_run,
        data_dir=args.data_dir,
        output_dir=str(out_dir),
        detector_version=args.detector_version,
        a1_backtest_log_path=None,
        slice_tag=args.slice_tag,
    )

    logger.info(
        "Starting GER40 slice %s: %s → %s, budget $%.2f, output=%s",
        args.slice_tag, args.start, args.end, args.budget, out_dir,
    )
    asyncio.run(sim.run_simulation(sim_args))
    logger.info("Slice %s complete", args.slice_tag)


if __name__ == "__main__":
    main()
