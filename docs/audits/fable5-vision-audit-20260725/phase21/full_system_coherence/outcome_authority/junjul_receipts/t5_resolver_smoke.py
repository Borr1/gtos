#!/usr/bin/env python3
"""T5 — resolver smoke for june_2026 / july_2026, sources only.

Two phases, both recorded:

PHASE 1 (formal, machinery as-committed): `LaneInputRegistry.resolve` exactly as
the wave-21 generator calls it. At origin/main HEAD the training-lane surface
map leaves 2026-06-01..2026-07-28 as a declared UncoveredGap and 2026-07-29+ is
the TEST band, so the guard is EXPECTED to refuse both windows. The verbatim
refusal is captured — it is the measured proof that the June/July confirm read
still needs its own committed authorization (the march_one_shot precedent).

PHASE 2 (source-integrity smoke, process-local disclosed overrides):
  * `lane.WINDOWS` extended with the two WindowSpecs (a naming table; every
    fuse is independent of it — module's own comment);
  * `guard.authorize_window` wrapped to pass a smoke-only SurfaceMap whose
    single addition is a TRAIN band 2026-06-01..2026-07-31 (T3's gap note names
    TRAIN as the honest label for this burned span; 07-29..31 sit in the
    ratified TEST band and are disclosed below — this smoke binds their BAR
    SOURCES only, builds no outcome object, and the override dies with this
    process);
  * `attempt5.{D1,H4,M15}_ROOT_ORDER` extended with the new static family name
    (the committed tuples cannot see it yet — machinery note for the
    orchestrator).
Then, inside `inputs.runtime_bindings()`:
  `lane._resolver_for(inputs).build_sources_for_days((day,), symbols=GTOS_24,
   source_authority_days=(day,))` for the first and last day of each window,
and every resolved symbol is checked for all five frames D1/H4/H1/M15/M1.

No sink, no campaign, no candidate, no outcome objects, no economics.
"""
import json
import sys
import traceback
from pathlib import Path

RT = Path("/tmp/junjul-lane-mat-20260810/rt-wt")
sys.path.insert(0, str(RT))

from src.research_infra import lane_rematerialization as lane  # noqa: E402
from src.research_infra import (  # noqa: E402
    replay_acceleration_attempt5_typed_sparse_runner as attempt5,
)
from src.research_infra import trainer_partitions as tp  # noqa: E402
from src.research_infra import (  # noqa: E402
    v4_timewarp_simulated_live_research_loop as timewarp,
)
from src.research_infra.train_engine import guard  # noqa: E402

HOLD = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
REGISTRY = HOLD / "LANE_INPUT_REGISTRY.json"
STATIC_FAMILY = "junjul_2026_lane_source_20260811"
OUT = Path("/tmp/junjul-lane-mat-20260810/scratch/T5_RESULT.json")

NEW_WINDOWS = {
    "june_2026": lane.WindowSpec(
        "june_2026", "2026-06-01", "2026-06-30", "lane_validation", "202606"
    ),
    "july_2026": lane.WindowSpec(
        "july_2026", "2026-07-01", "2026-07-31", "lane_validation", "202607"
    ),
}
SMOKE_DAYS = {
    "june_2026": ("2026-06-01", "2026-06-30"),
    "july_2026": ("2026-07-01", "2026-07-31"),
}
FRAMES = ("D1", "H4", "H1", "M15", "M1")

lane.WINDOWS.update(NEW_WINDOWS)

result: dict = {"phase1_formal": {}, "phase2_integrity": {}}

# --------------------------- PHASE 1: formal -------------------------------
for wid in NEW_WINDOWS:
    try:
        lane.LaneInputRegistry(
            REGISTRY, allow_registered_march_metadata=True
        ).resolve(window_id=wid, purpose=guard.PURPOSE_LANE_ITERATION)
        result["phase1_formal"][wid] = {
            "outcome": "RESOLVED_WITHOUT_REFUSAL",
            "note": "unexpected at origin/main HEAD - surface map must have changed",
        }
    except Exception as exc:  # noqa: BLE001
        result["phase1_formal"][wid] = {
            "outcome": "REFUSED",
            "exception_type": type(exc).__name__,
            "message": str(exc)[:600],
        }
    print(f"PHASE1 {wid}: {result['phase1_formal'][wid]['outcome']}")

# ----------------------- PHASE 2: integrity smoke --------------------------
smoke_map = tp.SurfaceMap(
    map_id=tp.DEFAULT_SURFACE_MAP.map_id + "+junjul_source_integrity_smoke",
    authored_utc="2026-08-11T00:00:00+00:00",
    bands=(
        *[
            b
            for b in tp.DEFAULT_SURFACE_MAP.bands
            if b.band_id != "test_live_forward_stream"
        ],
        tp.SurfaceBand(
            band_id="smoke_train_junjul_2026_source_integrity",
            surface="TRAIN",
            start="2026-06-01",
            end="2026-07-31",
            basis=(
                "PROCESS-LOCAL SMOKE ONLY - never committed. T3's gap note names "
                "TRAIN as the honest label for 2026-06-01..2026-07-28 (burned by "
                "every full-history gate walk). 2026-07-29..31 are on the ratified "
                "TEST band (live forward stream); this smoke binds their BAR "
                "SOURCES only and reads no outcome. The real June/July read needs "
                "its own committed authorization (march_one_shot precedent)."
            ),
        ),
        tp.SurfaceBand(
            band_id="test_live_forward_stream_smoke_shifted",
            surface="TEST",
            start="2026-08-01",
            end=tp.OPEN_END,
            basis="TEST band re-anchored past the smoke span; smoke-local only.",
        ),
    ),
    gaps=(),
)

_original_authorize = guard.authorize_window


def _smoke_authorize(**kwargs):
    kwargs.setdefault("surfaces", smoke_map)
    kwargs["surfaces"] = smoke_map
    return _original_authorize(**kwargs)


guard.authorize_window = _smoke_authorize
for name in ("D1_ROOT_ORDER", "H4_ROOT_ORDER", "M15_ROOT_ORDER"):
    order = getattr(attempt5, name)
    if STATIC_FAMILY not in order:
        setattr(attempt5, name, (*order, STATIC_FAMILY))

try:
    for wid in NEW_WINDOWS:
        wres: dict = {"days": {}}
        registry = lane.LaneInputRegistry(
            REGISTRY, allow_registered_march_metadata=True
        )
        inputs = registry.resolve(
            window_id=wid, purpose=guard.PURPOSE_LANE_ITERATION
        )
        for day in SMOKE_DAYS[wid]:
            day_res: dict = {}
            try:
                with inputs.runtime_bindings():
                    resolver = lane._resolver_for(inputs)
                    sources = resolver.build_sources_for_days(
                        (day,),
                        symbols=tuple(timewarp.GTOS_24_SYMBOL_SURFACE),
                        source_authority_days=(day,),
                    )
                resolved = sorted(sources)
                missing_frames = {
                    sym: [
                        f
                        for f in FRAMES
                        if f not in sources[sym] or sources[sym][f] is None
                    ]
                    for sym in resolved
                }
                incomplete = {s: m for s, m in missing_frames.items() if m}
                dropped = sorted(
                    set(timewarp.GTOS_24_SYMBOL_SURFACE) - set(resolved)
                )
                day_res = {
                    "outcome": "OK" if (not incomplete) else "INCOMPLETE_FRAMES",
                    "resolved_symbol_count": len(resolved),
                    "dropped_symbols": dropped,
                    "symbols_with_missing_frames": incomplete,
                }
            except Exception as exc:  # noqa: BLE001
                day_res = {
                    "outcome": "ERROR",
                    "exception_type": type(exc).__name__,
                    "message": str(exc)[:600],
                    "trace_tail": traceback.format_exc().splitlines()[-4:],
                }
            wres["days"][day] = day_res
            print(f"PHASE2 {wid} {day}: {json.dumps(day_res)[:300]}")
        result["phase2_integrity"][wid] = wres
finally:
    guard.authorize_window = _original_authorize

OUT.write_text(json.dumps(result, indent=1, default=str))
print("wrote", OUT)
