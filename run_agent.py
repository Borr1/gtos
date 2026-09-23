#!/usr/bin/env python3
"""Entry point for the Gold Trading Agent.

Usage:
    python run_agent.py --mode demo    # Real MT5, demo account
    python run_agent.py --mode mock    # Mock MT5, for testing
    python run_agent.py --mode live    # Production (future)

    # Lock walk-forward window (prevents prompt changes for N months)
    python run_agent.py --lock-walk-forward --window WF-1 --months 3
"""

import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(override=True)

# Install security monitoring at startup
from src.security import install_runtime_monitoring
install_runtime_monitoring()

from src.components.orchestrator import SessionOrchestrator
from src.safety.runtime_halt import (
    append_runtime_halt_audit,
    read_runtime_halt_state,
)


def main():
    # HARD DOUBLE-TRADE GUARD (MACRO-A5 / MACRO-RES-04): the legacy per-symbol fleet and the W7 book trade
    # the SAME real-money prop accounts. If a W7 book (run_book.py) is alive, this legacy entrypoint MUST
    # refuse to start -- two trading systems on one account = double-trade / double-risk. This in-code
    # fail-safe sits on top of the Disabled GTOS_Watchdog / TradingAgentDaily tasks, so a task re-enable,
    # reboot-time provisioning, or a manual launch can no longer silently double-trade the live accounts.
    try:
        import psutil
        for _p in psutil.process_iter(["name", "cmdline"]):
            _cl = " ".join(_p.info.get("cmdline") or [])
            if "python" in (_p.info.get("name") or "").lower() and "run_book.py" in _cl:
                logging.basicConfig(level=logging.ERROR)
                logging.error("REFUSING to start the legacy per-symbol fleet: a W7 book (run_book.py) is "
                              "running on the live prop accounts. Two systems on one account = double-trade. "
                              "Stop the W7 book first (this fleet is hard-halted).")
                return 9
    except Exception:
        pass   # psutil unavailable -> defer to the Disabled-task guard; do not block a legit isolated run
    parser = argparse.ArgumentParser(description="Gold Trading Agent")
    parser.add_argument("--mode", choices=["mock", "demo", "live"],
                        default="demo", help="Execution mode")
    parser.add_argument("--config", default="config/agent_config.yaml",
                        help="Config file path")
    parser.add_argument("--symbol", default=None,
                        help="Trading instrument (e.g., XAUUSD, GBPUSD). "
                             "Applies per-instrument config overrides.")
    parser.add_argument("--profile", default=None,
                        help="Prop-firm profile (e.g., ftmo, redacted_account). "
                             "Overlays config/profiles/<name>.yaml on top "
                             "of agent_config.yaml. Falls back to "
                             "GTOS_PROFILE env var; default is base config.")
    parser.add_argument("--terminal-path", default=None,
                        help="Optional MT5 terminal64.exe path. Overrides "
                             "GTOS_MT5_TERMINAL_PATH and profile mt5.terminal_path.")
    parser.add_argument("--runtime-namespace", default=None,
                        help="Optional broker/account namespace for logs, locks, "
                             "state, and checkpoints. Existing launches omit this.")

    # Walk-forward lock management
    parser.add_argument("--lock-walk-forward", action="store_true",
                        help="Create/update a walk-forward lock on the prompt file")
    parser.add_argument("--window", default="WF-1",
                        help="Walk-forward window identifier (e.g., WF-1)")
    parser.add_argument("--months", type=int, default=3,
                        help="Lock duration in months (default: 3)")

    args = parser.parse_args()

    # Operator notification delivery is default-deny per process (F30 / Q7,
    # src/safety/notification_authorization.py). A demo/live orchestrator must
    # be able to page the operator, so it takes the grant explicitly. "mock"
    # never does: a mock run is a simulation and has no business reaching
    # anybody's phone.
    if args.mode in {"demo", "live"}:
        from src.safety.notification_authorization import authorize_operator_delivery
        authorize_operator_delivery(
            reason=(
                f"run_agent.py orchestrator mode={args.mode} "
                f"symbol={args.symbol or 'XAUUSD'} profile={args.profile}"
            )
        )

    if args.mode in {"demo", "live"}:
        halt_config = {
            "runtime_control": {
                "enabled": True,
                "audit_log_path": "pipeline_state/runtime_control_atomic_halt_audit.jsonl",
            }
        }
        halt_snapshot = read_runtime_halt_state(halt_config)
        if halt_snapshot.active:
            append_runtime_halt_audit(
                action="run_agent_start",
                snapshot=halt_snapshot,
                context={
                    "mode": args.mode,
                    "symbol": args.symbol or "XAUUSD",
                    "profile": args.profile,
                    "runtime_namespace": args.runtime_namespace,
                },
                config=halt_config,
            )
            active_paths = [
                item.get("path") for item in halt_snapshot.active_flags
            ] or [
                item.get("path") for item in halt_snapshot.unreadable_paths
            ]
            active_path_text = ", ".join(str(path) for path in active_paths)
            print(
                f"{halt_snapshot.status} ({active_path_text}); "
                f"refusing to start {args.mode} orchestrator."
            )
            return

    # Ensure log directory exists
    log_dir = Path("knowledge_base/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Per-symbol log file to avoid collision when running multiple instruments
    namespace_part = f"{args.runtime_namespace}_" if args.runtime_namespace else ""
    log_name = f"agent_{namespace_part}{args.symbol or 'XAUUSD'}_{args.mode}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_dir / log_name)),
        ],
    )

    # Handle walk-forward lock command
    if args.lock_walk_forward:
        from src.components.walk_forward import create_lock
        lock = create_lock(window=args.window, months=args.months)
        print(f"Walk-forward lock created:")
        print(f"  Window:  {lock['window']}")
        print(f"  Hash:    {lock['prompt_hash'][:16]}...")
        print(f"  Locked:  {lock['locked_at']}")
        print(f"  Expires: {lock['lock_expires']}")
        return

    orchestrator = SessionOrchestrator(
        mode=args.mode,
        config_path=args.config,
        symbol=args.symbol,
        profile=args.profile,
        terminal_path=args.terminal_path,
        runtime_namespace=args.runtime_namespace,
    )
    orchestrator.run()


if __name__ == "__main__":
    main()
