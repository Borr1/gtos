"""Reprocess cached batch results without calling the Anthropic API.

Usage:
    python3 scripts/reprocess_batch.py msgbatch_01NNvwcdiUQwUU9c2x7qbVjD
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env", override=True)

import logging
import yaml

from scripts.batch_backtest import (
    process_results,
    generate_report,
    BATCH_STATE_DIR,
    HISTORICAL_DIR,
)
from scripts.historical_data_loader import parse_tradingview_csv
from src.utils.file_io import atomic_write

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/reprocess_batch.py <batch_id>")
        sys.exit(1)

    batch_id = sys.argv[1]

    # Load config
    with open(_PROJECT_ROOT / "config" / "agent_config.yaml") as fh:
        config = yaml.safe_load(fh)

    # Load historical candles
    all_candles: dict[str, list[dict]] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        csv_path = HISTORICAL_DIR / f"XAUUSD_{tf}.csv"
        if csv_path.exists():
            all_candles[tf] = parse_tradingview_csv(csv_path)
        else:
            logger.warning("No CSV for %s", tf)
            all_candles[tf] = []

    # Load cached prompts
    full_prompts_file = BATCH_STATE_DIR / f"{batch_id}_full_prompts.json"
    prompts_file = BATCH_STATE_DIR / f"{batch_id}_prompts.json"
    if full_prompts_file.exists():
        prompts = json.loads(full_prompts_file.read_text())
        logger.info("Loaded %d prompts from full prompts file", len(prompts))
    elif prompts_file.exists():
        prompts = json.loads(prompts_file.read_text())
        logger.info("Loaded %d prompts from metadata file", len(prompts))
    else:
        logger.error("No saved prompts for batch %s", batch_id)
        sys.exit(1)

    # Load cached raw results (NO API call)
    cache_file = BATCH_STATE_DIR / f"{batch_id}_raw_results.json"
    if not cache_file.exists():
        logger.error("No cached results at %s", cache_file)
        sys.exit(1)
    results = json.loads(cache_file.read_text())
    logger.info("Loaded %d cached results", len(results))

    # Count previously failed parses
    succeeded = sum(1 for r in results.values() if r.get("status") == "succeeded")
    logger.info("Succeeded responses: %d / %d", succeeded, len(results))

    # Reprocess with fixed models
    batch_results, batch_cost = process_results(prompts, results, config, all_candles)

    # Generate report
    report = generate_report(batch_results, batch_cost=batch_cost)
    print("\n" + report)

    # Save
    out_path = BATCH_STATE_DIR / f"{batch_id}_results.json"
    atomic_write(out_path, batch_results)
    report_path = BATCH_STATE_DIR / f"{batch_id}_report.txt"
    report_path.write_text(report)
    logger.info("Results saved to %s", out_path)
    logger.info("Report saved to %s", report_path)


if __name__ == "__main__":
    main()
