#!/usr/bin/env python3
"""Hydrate the committed-but-sparse-excluded inputs the test suite reads.

Session AT measured that 419 of 639 standing failures were absence of data, and that its own
hydration was worktree-local: `.git/worktrees/<n>/info/sparse-checkout` is not committed, so a
fresh worktree re-manufactures the same 15+ "failures" out of a clean tree (AT result §2.2/§8).
This is the twenty-line fix AT specified and did not build. Run it once per worktree, before any
full-suite capture:

    python3 scripts/gtos_hydrate_test_data.py

Sources of truth, in order:
  1. every `missing_path` in `TEST_TRIAGE_V1.json` with `missing_path_committed: true`
  2. `EXTRA_HYDRATIONS` — directories tests read that the triage could not carry a row for
     (they were hydrated *before* the final triage pass, so their rows show no missing path)

Safety, and read this before widening anything: paths are added as EXACT non-cone patterns,
never as parent directories, and anything matching `REPLAY_EXTENSION` is refused. The
cold-demoted denominator route (`…denominator_to_deployment_execution_2026_06_20/`) contains two
`REPLAY_EXTENSION_*` paths that are load-bearing BY THEIR ABSENCE (`CLAUDE.md` §4, B53) — a
directory-level add there would materialise them and break the route. LFS pointers among the
hydrated files are checked out per path afterwards; `git lfs checkout` never touches paths it is
not given.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TRIAGE = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/TEST_TRIAGE_V1.json"

#: Directories the suite reads whose triage rows predate their own hydration, or that carry a
#: committed module/route the tests import (a triage row names ONE missing file; the import needs
#: the whole directory). Directory adds are allowed here ONLY because each is checked against the
#: REPLAY_EXTENSION refusal below anyway — verified 2026-07-30: no REPLAY_EXTENSION path exists in
#: any of these; the two load-bearing-by-absence files live in the denominator route, which is
#: deliberately NOT in this list.
EXTRA_HYDRATIONS = [
    "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26",
    "research/operations/spread_model_2026_07_29",
    # BROKER_TRUE_COSTS_V1.json — the cost artifact `src.costs.load_broker_true_costs` defaults
    # to. Absent from the sparse profile until 2026-08-01, so EVERY cost-true research driver died
    # on a fresh worktree, and the exception it raised recommended re-running the *broker-truth*
    # capture rather than hydrating one committed file (Session AR handoff 7; confirmed absent again
    # at the start of Session AU, in a worktree where `gtos_hydrate_test_data.py` had already
    # reported completion). One line, and it is the difference between "the layer needs rebuilding"
    # and "the file is not checked out".
    "research/operations/broker_truth_layer_2026_07_27",
    "research/operations/broker_truth_layer_2026_07_29",
    "research/operations/trial_budget",
    # committed test-imported modules and route evidence, one directory each (wave-8 quieting):
    "research/retest_geometry",
    "research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02",
    "research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01",
    "research/operations/vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01",
    "research/operations/vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01",
    "research/operations/replay_acceleration_normalized_slice_2026_07_19",
    "research/operations/replay_acceleration_progressive_benchmark_2026_07_19",
    "research/operations/replay_acceleration_typed_proofs_2026_07_19",
    "research/operations/replay_acceleration_isolated_reducers_2026_07_19",
    "research/operations/replay_acceleration_bounded_slice_2026_07_19",
    "research/operations/replay_acceleration_partial_golden_2026_07_19",
    # Wave-19's SOL repair route. Committed 2026-08-01, after the triage pass that built the
    # rows above, so nothing carried it and a fresh worktree manufactured 15 red tests out of a
    # clean tree: `conditions/CONDITIONS_PROTOCOL.json`, `exit/OVERLAY_PROTOCOL.json`,
    # `exit/EXECUTED_OVERLAY_REPLAY.json`, `defects/REPRODUCTION_AND_BIAS.json` and the
    # `grid/session_fb_sol_grid.py` module `tests/research_infra/test_session_fb_sol_grid.py`
    # loads by path (an absent module is a COLLECTION error, not a failure). 52 files, 13.7 MiB.
    "research/operations/wave19_sol_repair_2026_08_01",
]

FORBIDDEN = "REPLAY_EXTENSION"


def main() -> int:
    rows = json.loads(TRIAGE.read_text(encoding="utf-8"))["rows"]
    wanted = sorted(
        {r["missing_path"] for r in rows if r.get("missing_path") and r.get("missing_path_committed")}
        | set(EXTRA_HYDRATIONS)
    )
    refused = [p for p in wanted if FORBIDDEN in p]
    patterns = [f"/{p}" for p in wanted if FORBIDDEN not in p]
    if refused:
        print(f"refused {len(refused)} path(s) matching {FORBIDDEN!r} — load-bearing by absence")

    listed = subprocess.run(
        ["git", "sparse-checkout", "list"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    new = [p for p in patterns if p not in listed]
    if not new:
        print("nothing to hydrate — all paths already in the sparse profile")
    else:
        # `add` inherits the worktree's cone/non-cone mode; `--no-cone` is a `set`-only flag.
        subprocess.run(["git", "sparse-checkout", "add", *new], cwd=REPO, check=True)
        print(f"added {len(new)} sparse pattern(s)")

    # Re-materialise LFS content for anything that arrived as a pointer. Explicit paths only.
    subprocess.run(["git", "lfs", "checkout", *[p.lstrip("/") for p in patterns]], cwd=REPO, check=False)

    missing = [p for p in wanted if FORBIDDEN not in p and not (REPO / p).exists()]
    if missing:
        print(f"WARNING: {len(missing)} path(s) still absent after hydration:")
        for p in missing[:10]:
            print(f"  {p}")
        return 1
    print(f"hydrated: {len(patterns)} path(s) present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
