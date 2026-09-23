"""p4 — re-run lane r1's estate analysis at the CORRECTED armed set.

r1 published `R1_ESTATE_DELTA_V1.json` and `R1_ADMISSION_STAT_V1.json` with an `ARMED`
tuple that omitted `sub_mid_dn_revert` (armed on both accounts) and included
`mx_btcusd_d1_donchian_20_breakout` (disarmed by the owner 2026-08-05). The omission is
why the estate's largest proportional casualty of r1's own repair never got a fold table
or a p-value in r1's receipts.

This driver imports r1's own scripts unmodified in behaviour -- same bars, same walker,
same spread model, same controls -- and only redirects their outputs and widens the
admission-statistic cell list. Re-deriving rather than editing the published V1 files
keeps the history intact (CLAUDE.md section 10); V1 stays exactly as published and V2 is
the correction.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R1 = HERE.parents[1] / "receipts" / "r1"
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

from src.safety.armed_set import armed_sleeves  # noqa: E402

ARMED = tuple(sorted(armed_sleeves()))
FORMERLY_ARMED = ("metals_core", "fx_jpy", "mx_btcusd_d1_donchian_20_breakout")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"p4_{name}", R1 / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def run_estate() -> int:
    mod = _load("r1_estate_rewalk")
    assert set(mod.ARMED) == set(ARMED), (mod.ARMED, ARMED)
    mod.OUT = HERE / "R1_ESTATE_DELTA_V2.json"
    mod.ROWS = HERE / "R1_ESTATE_ROWS_V2.json.gz"
    rc = mod.main()
    if rc == 0:
        doc = json.loads(mod.OUT.read_text())
        doc["corrected_armed_set_20260807"] = {
            "supersedes": "R1_ESTATE_DELTA_V1.json",
            "v1_armed_four": ["crypto", "energy_agri", "sub_xvol_pullback",
                              "mx_btcusd_d1_donchian_20_breakout"],
            "v2_armed": list(ARMED),
            "why": ("v1 omitted sub_mid_dn_revert, armed on both accounts, and included "
                    "mx_btcusd_d1_donchian_20_breakout, disarmed by the owner 2026-08-05 "
                    "(D-2 CLOSED, host 2fa77722d)"),
            "source_of_truth": "src/safety/armed_set.armed_sleeves()",
        }
        mod.OUT.write_text(json.dumps(doc, indent=1, sort_keys=True))
    return rc


def run_admission() -> int:
    mod = _load("r1_admission_stat")
    v1_cells = list(mod.CELLS)
    # The gap this lane exists to close: the armed sleeve r1's repair moves most had no
    # p-value at the corrected walk anywhere in the wave. Its live contract is `as_walked`
    # (no --frontier-exits on either account).
    mod.CELLS = v1_cells + [("sub_mid_dn_revert", "as_walked", None)]
    mod.OUT = HERE / "R1_ADMISSION_STAT_V2.json"
    rc = mod.main()
    if rc == 0:
        doc = json.loads(mod.OUT.read_text())
        doc["corrected_armed_set_20260807"] = {
            "supersedes": "R1_ADMISSION_STAT_V1.json",
            "v1_cells": [[c[0], c[1]] for c in v1_cells],
            "added_cell": ["sub_mid_dn_revert", "as_walked"],
            "why": ("sub_mid_dn_revert is armed on BOTH accounts and is the estate's largest "
                    "proportional casualty of r1's own repair; v1's cell list omitted it, so "
                    "no fold table or p-value existed for it at the corrected walk"),
            "armed_set": list(ARMED),
        }
        mod.OUT.write_text(json.dumps(doc, indent=1, sort_keys=True))
    return rc


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    rc = 0
    if which in ("estate", "both"):
        rc |= run_estate()
    if which in ("admission", "both"):
        rc |= run_admission()
    raise SystemExit(rc)
