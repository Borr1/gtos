#!/usr/bin/env python3
"""Run the GTOS AI companion supervisor.

The companion supervisor is not an order executor. It observes runtime logs and
publishes typed, bounded control_state.json for the live book to consume.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv(override=True)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.ai_companion.control_state import ai_companion_config
from src.components.ai_companion.supervisor import AICompanionSupervisor


class _BelowLevelFilter(logging.Filter):
    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self.max_level


def configure_runtime_logging(level: int) -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except Exception:
            pass
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.addFilter(_BelowLevelFilter(logging.ERROR))
    stdout_handler.setFormatter(formatter)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(stdout_handler)
    root.addHandler(stderr_handler)


def main() -> int:
    parser = argparse.ArgumentParser(description="GTOS AI companion supervisor")
    parser.add_argument("--config", default="config/agent_config.yaml")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    configure_runtime_logging(getattr(logging, str(args.log_level).upper(), logging.INFO))

    cfg_path = Path(args.config)
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    companion_cfg = ai_companion_config(cfg)
    supervisor = AICompanionSupervisor(companion_cfg, repo_root=args.repo_root)
    logging.info(
        "ai companion supervisor starting enabled=%s authority=%s once=%s",
        supervisor.enabled,
        supervisor.authority_level,
        args.once,
    )
    if args.once:
        decision = supervisor.run_once()
        logging.info("ai companion supervisor cycle: %s", decision)
        return 0 if decision.get("enabled") is not None else 1
    supervisor.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
