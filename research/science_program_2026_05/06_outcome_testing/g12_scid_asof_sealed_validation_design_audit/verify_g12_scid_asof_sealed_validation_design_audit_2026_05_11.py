"""Standalone verifier for the G12 SCID sealed-validation design audit."""

from __future__ import annotations

import json

import build_g12_scid_asof_sealed_validation_design_audit_2026_05_11 as route


def main() -> int:
    result = route.verify_route(write_result=True, run_focused_tests=True)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
