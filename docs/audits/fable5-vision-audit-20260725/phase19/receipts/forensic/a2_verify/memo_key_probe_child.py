#!/usr/bin/env python3
"""Child probe: compare base vs repaired _exact_content_key under one hash seed.

Pure-function property check (NOT the test suite): equal mappings with permuted
insertion order must produce equal memo keys. Also probes the set/frozenset
branch at HEAD for the same pickle-order instability class.
"""

import importlib.util
import json
import os
import sys

SOL = "/Users/borr/GTOSActive/worktrees/wave19-sol-defects-20260801"
BASE_FILE = os.environ["CUTS_BASE_FILE"]

sys.path.insert(0, SOL)

from src.research_infra.train_engine import cuts as head  # noqa: E402

spec = importlib.util.spec_from_file_location("cuts_base_f8c05d0ac", BASE_FILE)
base = importlib.util.module_from_spec(spec)
sys.modules["cuts_base_f8c05d0ac"] = base
spec.loader.exec_module(base)

a = {"a": 1, "b": [2]}
b = {"b": [2], "a": 1}

t1 = ("a", 1)
t2 = ("b", 2)
set_a = {"x": frozenset([t1, t2])}
set_b = {"x": frozenset([t2, t1])}

print(
    json.dumps(
        {
            "seed": os.environ.get("PYTHONHASHSEED"),
            "base_mapping_equal": bool(
                base._exact_content_key(a) == base._exact_content_key(b)
            ),
            "head_mapping_equal": bool(
                head._exact_content_key(a) == head._exact_content_key(b)
            ),
            "head_set_equal": bool(
                head._exact_content_key(set_a) == head._exact_content_key(set_b)
            ),
            "base_set_equal": bool(
                base._exact_content_key(set_a) == base._exact_content_key(set_b)
            ),
        }
    )
)
