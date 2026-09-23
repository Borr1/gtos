#!/usr/bin/env python3
"""Verify G12 SCID as-of packet audit artifacts."""

from __future__ import annotations

import json

import build_g12_scid_asof_packet_audit_2026_05_11 as audit


def main() -> int:
    result = audit.verify_route(write_result=True)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
