#!/usr/bin/env python3
"""Print the login_sha256 digest for an MT5 login.

The digest is SHA-256 of the login string as UTF-8, the same value
``broker_profile.expected_account.login_sha256`` stores
(``sha256_text`` in ``src/utils/broker_profile.py``).

This script does not read a profile, does not open a terminal, and does
not print the login back.

    python3 scripts/gtos_account_digest.py 0
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.broker_profile import sha256_text  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not str(argv[1]).strip():
        print(
            "usage: python3 scripts/gtos_account_digest.py <login>",
            file=sys.stderr,
        )
        return 2
    print(sha256_text(str(argv[1]).strip()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
