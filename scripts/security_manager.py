#!/usr/bin/env python3
"""Security management CLI for environment sanitization audit.

SECURITY CONTEXT: Critical tool for Red Team Audit remediation
Reference: research/kap_outputs/red_team_audit_april7.md

Usage:
    python scripts/security_manager.py env-check
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.security import (
    get_sanitized_environment,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cmd_env_check(args):
    """Check environment sanitization."""
    try:
        import os
        print("Environment Security Check")

        # Get original environment count
        original_count = len(os.environ)

        # Get sanitized environment
        clean_env = get_sanitized_environment()
        clean_count = len(clean_env)

        removed_count = original_count - clean_count

        print(f"  Original environment variables: {original_count}")
        print(f"  After sanitization: {clean_count}")
        print(f"  Removed (sensitive): {removed_count}")

        if removed_count > 0:
            print(f"✅ Environment sanitization active ({removed_count} sensitive vars removed)")
        else:
            print("⚠️  No sensitive variables detected (this may be expected)")

        if args.verbose:
            print(f"\nFirst 10 remaining variables:")
            for i, key in enumerate(sorted(clean_env.keys())[:10]):
                print(f"  {key}")
            if len(clean_env) > 10:
                print(f"  ... and {len(clean_env) - 10} more")

    except Exception as e:
        print(f"❌ Failed to check environment: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Security Manager for Gold Trading Agent")
    parser.add_argument("--path", default=".", help="Base path for operations (default: current directory)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Environment check command
    env_parser = subparsers.add_parser("env-check", help="Check environment sanitization")
    env_parser.set_defaults(func=cmd_env_check)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    main()