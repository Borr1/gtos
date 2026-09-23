#!/usr/bin/env python3
"""Verify SCID as-of bar builder and candidate input packet artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import build_scid_asof_bar_builder_and_candidate_input_packet_source_control_2026_05_11 as builder


def main() -> int:
    result = builder.verify_route(write_result=True)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
