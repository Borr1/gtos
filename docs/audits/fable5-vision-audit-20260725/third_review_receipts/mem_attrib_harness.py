"""Third-review memory-attribution harness.

Derived from docs/audits/opus5-architecture-20260725/receipts/profile_day_harness.py
(the audit's annotated invocation), with three changes:
  1. Contract -> R2 (R1 now fails on the P1-fixed verifier it still binds; B83).
  2. wallsampler replaced by an in-process watcher: RSS + tracemalloc timeline,
     threshold-triggered snapshot statistics at the Python-heap high-water mark.
  3. tracemalloc(1) runs for the whole arm so every allocation site is attributed.

This is a PROFILE, not a sealed reproduction. No contract-bound file is touched;
the engine runs the sealed source layer (no columnar bridge is installed).

Safety valves: tracing stops if RSS crosses STOP_TRACING_RSS; the watcher never
aborts the engine.
"""

from __future__ import annotations

import gc
import json
import os
import resource
import subprocess
import sys
import threading
import time
import tracemalloc
import traceback
from pathlib import Path

REPO = Path(os.environ["GTOS_AUDIT_REPO"])
sys.path.insert(0, str(REPO))

from src.research_infra import b7_5_post_acceleration_runner as runner  # noqa: E402
from src.research_infra import (  # noqa: E402
    replay_acceleration_attempt5_typed_sparse_runner as attempt5,
)

DAY = "2026-01-01"
END_DAY = "2026-01-02"
ARM = "S1R1"
OUT = os.environ["MEMATTRIB_OUT"]

SNAP_TRIGGER_TRACED = 5.5e9      # first snapshot once Python heap crosses this
SNAP_STEP = 0.7e9                # further snapshots every +0.7 GB traced
MAX_SNAPSHOTS = 4
STOP_TRACING_RSS = 13.0e9        # shed tracemalloc overhead if RSS gets here
PID = os.getpid()


def rss_bytes() -> int:
    out = subprocess.run(
        ["ps", "-o", "rss=", "-p", str(PID)], capture_output=True, text=True
    ).stdout.strip()
    return int(out) * 1024 if out else -1


def snapshot_stats(tag: str) -> dict:
    t0 = time.perf_counter()
    snap = tracemalloc.take_snapshot()
    by_line = snap.statistics("lineno")
    by_file = snap.statistics("filename")
    res = {
        "tag": tag,
        "t": time.perf_counter(),
        "traced_current": tracemalloc.get_traced_memory()[0],
        "top_lines": [
            {"where": str(s.traceback), "size": s.size, "count": s.count}
            for s in by_line[:80]
        ],
        "top_files": [
            {"where": str(s.traceback), "size": s.size, "count": s.count}
            for s in by_file[:40]
        ],
        "snapshot_seconds": None,
    }
    del snap, by_line, by_file
    gc.collect()
    res["snapshot_seconds"] = time.perf_counter() - t0
    return res


class Watcher(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.stop_flag = threading.Event()
        self.timeline: list[tuple[float, int, int]] = []  # (t, rss, traced)
        self.snaps: list[dict] = []
        self.tracing_stopped_at = None
        self._next_trigger = SNAP_TRIGGER_TRACED
        self.t0 = time.perf_counter()

    def run(self) -> None:
        while not self.stop_flag.is_set():
            t = time.perf_counter() - self.t0
            rss = rss_bytes()
            traced = tracemalloc.get_traced_memory()[0] if tracemalloc.is_tracing() else -1
            self.timeline.append((round(t, 2), rss, traced))
            if tracemalloc.is_tracing():
                if rss > STOP_TRACING_RSS:
                    tracemalloc.stop()
                    self.tracing_stopped_at = t
                elif traced >= self._next_trigger and len(self.snaps) < MAX_SNAPSHOTS:
                    try:
                        self.snaps.append(snapshot_stats(f"traced>{traced/1e9:.2f}GB@{t:.0f}s"))
                    except Exception as e:  # snapshot failure must not kill the watcher
                        self.snaps.append({"tag": "snapshot_error", "error": repr(e)})
                    self._next_trigger = max(
                        self._next_trigger + SNAP_STEP,
                        (tracemalloc.get_traced_memory()[0] if tracemalloc.is_tracing() else 0)
                        + 0.2e9,
                    )
            self.stop_flag.wait(1.0)


def cache_probes() -> dict:
    """Lengths of the known module-global caches, for corroboration."""
    probes = {}
    try:
        probes["attempt5._file_cache_entries"] = len(getattr(attempt5, "_file_cache", {}))
        probes["attempt5._day_file_cache_entries"] = len(getattr(attempt5, "_day_file_cache", {}))
    except Exception as e:
        probes["attempt5_error"] = repr(e)
    try:
        import v4_timewarp_simulated_live_research_loop as v4  # noqa: F401

        for name in dir(v4):
            obj = getattr(v4, name)
            if isinstance(obj, dict) and len(obj) > 0 and name.startswith("_"):
                probes[f"v4.{name}_entries"] = len(obj)
    except Exception as e:
        probes["v4_error"] = repr(e)
    return probes


def main() -> int:
    E = REPO / ".hermes/evidence/phase-d/january-post-acceleration-source-20260723T225928Z"
    ORIG = Path("/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719")
    OE = ORIG / ".hermes/evidence/phase-d/january-post-acceleration-source-20260723T225928Z"
    PACK = REPO / "audit_runs/PHASE_D_JANUARY_ARM_NEUTRAL_PACK_R4_20260724T003240Z/prepared-day-packs"
    contract = (
        REPO
        / "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
        / "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"
    )
    seal = json.loads((E / "JANUARY_EXECUTION_SEAL_R3.json").read_text())
    src_binding = seal["source_authority_binding"]

    outdir = (
        REPO
        / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse"
        / f"MEMATTRIB_{DAY.replace('-', '')}_{END_DAY}_{ARM}"
    )
    outdir.parent.mkdir(parents=True, exist_ok=True)

    args = runner.build_standard_args(
        output_dir=outdir,
        output_prefix=f"MEMATTRIB_B7_5_{DAY.replace('-', '_')}_{ARM}",
        window_id="development_january",
        start=seal["window_binding"]["start"],
        end=seal["window_binding"]["end"],
        arm_id=ARM,
        decision_contract_path=contract,
        source_bundle_dir=OE / "materialization-current/bundle",
        source_selection_path=ORIG
        / ".hermes/evidence/task4/source-bundle-selection-refresh-20260722-r5/CURRENT_SOURCE_SELECTION_RECEIPT.json",
        source_authority_path=OE / "FRESH_CURRENT_BUNDLE_AUTHORITY.json",
        source_authority_file_sha256=src_binding["file_sha256"],
        source_authority_root_sha256=src_binding["authority_root_sha256"],
        source_bundle_root_sha256=src_binding["bundle_root_sha256"],
        source_plan_digest_sha256=src_binding["source_plan_digest_sha256"],
        typed_cache_root=E / "typed-cache",
        tick_sparse_cache_root=E / "tick-sparse-cache",
        prepared_day_pack_root=PACK,
        prepared_pack_authority_path=E / "JANUARY_PREPARED_PACK_REBIND_AUTHORITY_R3.json",
    )

    args.engineering_stop_after_day = END_DAY
    roots = dict(args.expected_prepared_day_pack_roots)
    args.expected_prepared_day_pack_roots = {
        k: v for k, v in roots.items() if str(k[1]) <= END_DAY
    }
    print(
        f"[memattrib] pack roots {len(roots)} -> {len(args.expected_prepared_day_pack_roots)}",
        file=sys.stderr,
    )

    attempt5.bind_attempt5_finalizer_conflict_key_order()
    attempt5.configure_runtime_evidence_root(attempt5.ATTEMPT5_RUNTIME_EVIDENCE_ROOT)
    runner.bind_fresh_source(args)
    shared = runner.current_shared_contract(args)
    args.expected_shared_execution_contract_sha256 = shared[
        "shared_execution_contract_digest_sha256"
    ]
    attempt5.configure_output_namespace(Path(args.output_dir))

    tracemalloc.start(1)
    watcher = Watcher()
    watcher.start()
    t0 = time.perf_counter()
    err = None
    receipt = None
    try:
        receipt = attempt5.run_replay_engine(args)
    except BaseException:
        err = traceback.format_exc()
    wall = time.perf_counter() - t0

    end_probes = cache_probes()
    end_snap = None
    if tracemalloc.is_tracing():
        try:
            end_snap = snapshot_stats("end_of_run")
        except Exception as e:
            end_snap = {"tag": "end_snapshot_error", "error": repr(e)}
        tracemalloc.stop()
    watcher.stop_flag.set()
    watcher.join(timeout=5)

    ru = resource.getrusage(resource.RUSAGE_SELF)
    rep = {
        "day": DAY,
        "end_day": END_DAY,
        "arm": ARM,
        "wall_seconds": wall,
        "error": err,
        "tracing_stopped_at": watcher.tracing_stopped_at,
        "rusage": {
            "utime": ru.ru_utime,
            "stime": ru.ru_stime,
            "maxrss_bytes": ru.ru_maxrss,
            "majflt": ru.ru_majflt,
            "minflt": ru.ru_minflt,
        },
        "cache_probes_end": end_probes,
        "snapshots": watcher.snaps + ([end_snap] if end_snap else []),
        "timeline": watcher.timeline,
    }
    if isinstance(receipt, dict):
        for k in (
            "candidate_rows",
            "missed_opportunity_rows",
            "order_rows",
            "trade_rows",
            "scorecard_rows",
        ):
            rep[k] = receipt.get(k)
        pr = receipt.get("progress_rows")
        if isinstance(pr, list):
            rep["progress_rows"] = [
                {
                    kk: vv
                    for kk, vv in row.items()
                    if kk
                    in (
                        "start_day",
                        "economic_hot_path_seconds",
                        "proof_finalization_seconds",
                    )
                }
                for row in pr
            ]
    Path(OUT).write_text(json.dumps(rep, indent=1))
    print(
        f"[memattrib] wall={wall:.1f}s maxrss={ru.ru_maxrss/1e9:.2f}GB "
        f"snaps={len(rep['snapshots'])} -> {OUT}",
        file=sys.stderr,
    )
    if err:
        print(err[-4000:], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
