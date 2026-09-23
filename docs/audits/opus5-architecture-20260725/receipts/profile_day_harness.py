"""Audit-only engine profiling harness.

Calls the same argument builder and engine entrypoint the sealed Phase-D runner
uses, but for a caller-chosen day window, under a low-overhead wall-clock
sampler. This is a PROFILE, not a sealed reproduction: the execution-seal
window/path binding is deliberately not applied because it pins a single
absolute worktree path and the full calendar month.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import resource
import sys
import threading
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve()
REPO = Path(os.environ["GTOS_AUDIT_REPO"])
sys.path.insert(0, str(REPO))

SCRATCH = Path(os.environ["GTOS_AUDIT_SCRATCH"])
sys.path.insert(0, str(SCRATCH))

from wallsampler import Sampler  # noqa: E402

from src.research_infra import b7_5_post_acceleration_runner as runner  # noqa: E402
from src.research_infra import (  # noqa: E402
    replay_acceleration_attempt5_typed_sparse_runner as attempt5,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", required=True)
    ap.add_argument("--end-day", default=None)
    ap.add_argument("--arm", default="S1R1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval-ms", type=float, default=5.0)
    ns = ap.parse_args()

    end_day = ns.end_day or ns.day
    E = REPO / ".hermes/evidence/phase-d/january-post-acceleration-source-20260723T225928Z"
    # The sealed source authority pins ABSOLUTE paths into the producing
    # worktree, so byte-identical local copies are rejected. Read those
    # inputs from the original location (read-only) and keep all writable
    # caches/outputs local.
    ORIG = Path("/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719")
    OE = ORIG / ".hermes/evidence/phase-d/january-post-acceleration-source-20260723T225928Z"
    PACK = REPO / "audit_runs/PHASE_D_JANUARY_ARM_NEUTRAL_PACK_R4_20260724T003240Z/prepared-day-packs"
    contract = (
        REPO
        / "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
        / "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json"
    )
    seal = json.loads((E / "JANUARY_EXECUTION_SEAL_R3.json").read_text())
    src_binding = seal["source_authority_binding"]

    outdir = (REPO / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse"
              / f"AUDIT_PROFILE_{ns.day.replace(chr(45),chr(48)*0)}_{end_day}_{ns.arm}")
    outdir.parent.mkdir(parents=True, exist_ok=True)

    # Neutralise only the two seal bindings that are structurally un-runnable
    # outside the producing worktree: the calendar-month window and the
    # absolute-path pin. Everything else stays exactly as the sealed runner
    # builds it.
    args = runner.build_standard_args(
        output_dir=outdir,
        output_prefix=f"AUDIT_PROFILE_B7_5_{ns.day.replace(chr(45), chr(95))}_{ns.arm}",
        window_id="development_january",
        start=seal["window_binding"]["start"],
        end=seal["window_binding"]["end"],
        arm_id=ns.arm,
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

    # The prepared pack is sealed for the whole month and the engine requires
    # exact set equality between pack roots and the chunk plan, so a sub-window
    # profile must narrow the declared roots to the days actually replayed.
    args.engineering_stop_after_day = end_day
    roots = dict(args.expected_prepared_day_pack_roots)
    args.expected_prepared_day_pack_roots = {
        k: v for k, v in roots.items() if str(k[1]) <= end_day
    }
    print(
        f"[profile_day] pack roots {len(roots)} -> {len(args.expected_prepared_day_pack_roots)}",
        file=sys.stderr,
    )

    # Mirror run_sealed_arm's prelude exactly, minus the two seal bindings
    # (calendar-month window, absolute-path pin) that make sub-window
    # profiling structurally impossible.
    attempt5.bind_attempt5_finalizer_conflict_key_order()
    attempt5.configure_runtime_evidence_root(attempt5.ATTEMPT5_RUNTIME_EVIDENCE_ROOT)
    runner.bind_fresh_source(args)
    shared = runner.current_shared_contract(args)
    args.expected_shared_execution_contract_sha256 = shared[
        "shared_execution_contract_digest_sha256"
    ]
    attempt5.configure_output_namespace(Path(args.output_dir))


    sampler = Sampler(
        main_tid=threading.get_ident(),
        interval=ns.interval_ms / 1000.0,
        repo_root=str(REPO),
    )
    sampler.start()
    t0 = time.perf_counter()
    err = None
    receipt = None
    try:
        receipt = attempt5.run_replay_engine(args)
    except BaseException:
        err = traceback.format_exc()
    wall = time.perf_counter() - t0
    sampler.stop_flag.set()
    sampler.join(timeout=5)

    rep = sampler.report(wall)
    ru = resource.getrusage(resource.RUSAGE_SELF)
    rep["rusage"] = {
        "utime": ru.ru_utime,
        "stime": ru.ru_stime,
        "maxrss_bytes": ru.ru_maxrss,
        "inblock": ru.ru_inblock,
        "oublock": ru.ru_oublock,
        "majflt": ru.ru_majflt,
        "minflt": ru.ru_minflt,
    }
    rep["day"] = ns.day
    rep["end_day"] = end_day
    rep["arm"] = ns.arm
    rep["error"] = err
    if isinstance(receipt, dict):
        rep["receipt_keys"] = sorted(receipt)[:80]
        for k in (
            "candidate_rows",
            "missed_opportunity_rows",
            "order_rows",
            "trade_rows",
            "scorecard_rows",
            "progress_rows",
        ):
            v = receipt.get(k)
            if k == "progress_rows" and isinstance(v, list):
                rep["progress_rows"] = [
                    {
                        kk: vv
                        for kk, vv in row.items()
                        if kk
                        in (
                            "start_day",
                            "economic_hot_path_seconds",
                            "proof_finalization_seconds",
                            "selected_order_sequence",
                        )
                    }
                    for row in v
                ]
            else:
                rep[k] = v
    Path(ns.out).write_text(json.dumps(rep, indent=1))
    print(
        f"[profile_day] day={ns.day}..{end_day} wall={wall:.2f}s "
        f"samples={sampler.samples} maxrss={ru.ru_maxrss/1e9:.2f}GB -> {ns.out}",
        file=sys.stderr,
    )
    if err:
        print(err[-4000:], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
