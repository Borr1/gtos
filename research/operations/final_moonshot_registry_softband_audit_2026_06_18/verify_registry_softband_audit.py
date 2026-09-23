#!/usr/bin/env python3
"""Audit active ultimate_book registry coverage and metals_softband low-vol sizing."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.components.ultimate_book.admission import (  # noqa: E402
    CLEAN3_REGISTRY,
    CLEAN4_REGISTRY,
    SLEEVE_REGISTRY,
    effective_registry,
)
from src.components.ultimate_book.sleeves import metals as MT  # noqa: E402
from src.components.ultimate_book.sleeves.registry import BUILT  # noqa: E402


def _runtime_config() -> dict:
    cfg = yaml.safe_load((ROOT / "config/agent_config.yaml").read_text())
    return cfg["gtos_vnext_runtime"]


def _check(name: str, passed: bool, detail: dict | None = None) -> dict:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


def _softband_table() -> list[dict]:
    rows = []
    for ac in (0.0399, 0.04, 0.06, 0.09, 0.099):
        rows.append(
            {
                "ac60": ac,
                "vr_1p34_boosted": MT._size_mult_soft(ac, 1.34),
                "vr_1p35_neutral": MT._size_mult_soft(ac, 1.35),
                "vr_1p599_neutral": MT._size_mult_soft(ac, 1.599),
                "vr_1p60_reduced": MT._size_mult_soft(ac, 1.60),
                "effective_confidence_boosted": round(0.50 * MT._size_mult_soft(ac, 1.34), 6),
            }
        )
    return rows


def main() -> int:
    cfg = _runtime_config()
    active = effective_registry(
        include_clean3=cfg["ultimate_book_include_clean3"],
        include_clean4=cfg["ultimate_book_include_clean4"],
    )
    core = set(SLEEVE_REGISTRY)
    clean3 = set(CLEAN3_REGISTRY)
    clean4 = set(CLEAN4_REGISTRY)
    table = _softband_table()
    boosted_rows = [r for r in table if r["ac60"] >= MT.AC_FLOOR_SB]

    checks = [
        _check(
            "active_config_is_core8",
            cfg.get("ultimate_book_include_clean3") is False
            and cfg.get("ultimate_book_include_clean4") is False
            and set(active) == core,
            {
                "active_count": len(active),
                "active": sorted(active),
                "clean3_intersection": sorted(set(active) & clean3),
                "clean4_intersection": sorted(set(active) & clean4),
            },
        ),
        _check(
            "generation_registry_covers_active_sleeves",
            core <= set(BUILT),
            {"missing_from_built": sorted(core - set(BUILT))},
        ),
        _check(
            "softband_low_vol_boost_exact",
            all(
                r["vr_1p34_boosted"] == round(r["vr_1p35_neutral"] * 1.15, 4)
                for r in boosted_rows
            ),
            {"table": table},
        ),
        _check(
            "softband_neutral_band_flat_until_high_vol_cut",
            all(r["vr_1p35_neutral"] == r["vr_1p599_neutral"] for r in boosted_rows),
            {"table": table},
        ),
        _check(
            "softband_high_vol_cut_exact",
            all(
                r["vr_1p60_reduced"] == round(r["vr_1p599_neutral"] * 0.90, 4)
                for r in boosted_rows
            ),
            {"table": table},
        ),
        _check(
            "softband_effective_confidence_remains_sub_core",
            all(r["effective_confidence_boosted"] <= 0.75 for r in boosted_rows),
            {"max_effective_confidence": max(r["effective_confidence_boosted"] for r in boosted_rows)},
        ),
        _check(
            "softband_ac_band_is_disjoint_from_core_generation",
            MT.AC_FLOOR_SB == 0.04 and MT.AC_THR == 0.10,
            {"softband_floor": MT.AC_FLOOR_SB, "core_threshold": MT.AC_THR},
        ),
    ]
    ok = all(c["passed"] for c in checks)
    result = {
        "ok": ok,
        "decision": "PRESERVE_CORE8_REGISTRY_AND_SOFTBAND_LOW_VOL_BOOST_WITH_GUARDS"
        if ok
        else "BLOCK_REGISTRY_SOFTBAND_UNTIL_REPAIRED",
        "active_config": {
            "ultimate_book_include_clean3": cfg.get("ultimate_book_include_clean3"),
            "ultimate_book_include_clean4": cfg.get("ultimate_book_include_clean4"),
            "ultimate_book_profile": cfg.get("ultimate_book_profile"),
            "ultimate_book_metals_confluence_gate": cfg.get("ultimate_book_metals_confluence_gate"),
        },
        "active_registry": sorted(active),
        "softband_size_table": table,
        "checks": checks,
    }
    (ROUTE / "REGISTRY_SOFTBAND_AUDIT_RESULT.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    manifest = {
        "route": ROUTE.name,
        "decision": result["decision"],
        "files": [
            "verify_registry_softband_audit.py",
            "REGISTRY_SOFTBAND_AUDIT_RESULT.json",
            "REGISTRY_SOFTBAND_AUDIT_OUTPUT_MANIFEST.json",
            "REGISTRY_SOFTBAND_AUDIT_COMPLETION_AUDIT.json",
        ],
    }
    (ROUTE / "REGISTRY_SOFTBAND_AUDIT_OUTPUT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    audit = {
        "ok": ok,
        "issue_count": 0 if ok else sum(1 for c in checks if not c["passed"]),
        "no_broker_or_order_mutation": True,
        "runtime_behavior_mutation": "none; audit and regression guard only",
        "next_research_requirement": (
            "If softband risk is changed later, rerun a book-level MC sensitivity rather than editing "
            "the 1.15x low-vol multiplier by inspection."
        ),
    }
    (ROUTE / "REGISTRY_SOFTBAND_AUDIT_COMPLETION_AUDIT.json").write_text(
        json.dumps(audit, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
