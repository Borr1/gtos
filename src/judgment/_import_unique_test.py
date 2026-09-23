"""Side-test unique_loader. Never stamp the Challenge canonical file."""

from __future__ import annotations

import json
import os
import sys

os.environ["GTOS_UNIQUE_LOADER_SIDE_TEST"] = "1"
sys.path.insert(0, r"host-local\redacted_host\repo")

from src.judgment.unique_loader import load_unique_apply  # noqa: E402

stamp = load_unique_apply()
print(json.dumps(
    {
        "n_declared": stamp.get("n_declared"),
        "n_loaded": stamp.get("n_loaded"),
        "n_failed": stamp.get("n_failed"),
        "failed": stamp.get("failed"),
        "persist": stamp.get("persist"),
        "extra_pass": stamp.get("extra_pass"),
        "challenge_writer": stamp.get("challenge_writer"),
        "pid": stamp.get("pid"),
        "never_book_owner": stamp.get("never_book_owner"),
    },
    indent=2,
    sort_keys=True,
))
