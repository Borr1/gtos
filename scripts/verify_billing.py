#!/usr/bin/env python3
"""Billing verification script — run ONCE before your first subscription-mode batch.

Confirms that `claude -p` routes to Max subscription, not API billing.

Usage:
    python scripts/verify_billing.py

Prerequisites:
    1. Install Claude Code CLI:  npm install -g @anthropic-ai/claude-code
    2. Login to subscription:    claude logout && claude login
       → Select option: "Claude account with subscription"
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.llm_backend import LLMBackend


def main() -> None:
    print()
    print("=" * 60)
    print("  CLAUDE MAX SUBSCRIPTION — BILLING VERIFICATION")
    print("=" * 60)
    print()

    try:
        backend = LLMBackend(mode="subscription")
    except RuntimeError as e:
        print(f"  FATAL: {e}")
        sys.exit(1)

    success = backend.verify_billing_route()

    if success:
        print("  Verification passed.")
        print()
        print("  You can now run backtests with subscription billing:")
        print("    python scripts/backtest_runner.py --billing subscription \\")
        print("        --start 2025-01-27 --end 2025-03-21 --no-debate")
        print()
    else:
        print("  Verification FAILED.")
        print("  Do NOT use --billing subscription until this passes.")
        sys.exit(1)


if __name__ == "__main__":
    main()
