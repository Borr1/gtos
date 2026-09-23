"""CB-3.3 + CB-4 -- the train lane's entrypoint, sub-window, and output contract.

Three things live here, and each is a commission item:

* **the gate order** -- resolve the window the ENGINE will run, authorize it
  through `guard`, and only then install cuts and run. A window is never
  authorized from what a caller declares.
* **the sub-window** -- `--days N` bounds the run to the first N calendar days
  of the sealed window, so a one-day iteration costs one day. `H5` (no
  sub-window replay) is a property of the SEALED path, which hardcodes
  `engineering_stop_after_day = None`; this lane is not the sealed path, so the
  bound is available and every artifact records it.
* **the output contract** -- a compact per-arm trade table plus a fingerprint,
  both stamped `TRAINING_EVIDENCE - never admission-grade`. No 6.4 GB evidence
  tree reaches the iteration ledger.

## The honest limit of the sub-window, stated where it is used

Only a **prefix** window preserves outcome identity. Account equity, the running
conviction ledger and the risk budget all accumulate across days, so starting on
day 7 is a different arm, not a cheaper view of the same one. `--days N` is
therefore a prefix bound and there is deliberately no `--start-day`: an option
that silently changed the economics would be worse than its absence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

from src.research_infra.train_engine import (
    TRAIN_ENGINE_VERSION,
    TRAINING_EVIDENCE_STAMP,
    cuts,
    guard,
    identity,
    lane,
    repairs as repairs_mod,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

#: A training artifact must be tied to the surface it was produced on, or a
#: later reader cannot tell two arms apart. Read-only.
SPEC_DIGEST_PATHS = (
    "config/agent_config.yaml",
    "config/profiles/ftmo.yaml",
)


class TrainingOutputRefused(RuntimeError):
    """A run tried to emit training evidence it is not authorized to emit."""


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def fingerprint(
    *,
    sealed: Any,
    args: Any,
    patch_manifest: dict[str, Any],
    shared_execution_contract_sha256: str | None = None,
) -> dict[str, Any]:
    """The config fingerprint CC's iteration ledger logs against every look.

    Three groups: what code decided (engine + cuts), what contract bound it
    (R2 + the shared execution digest + the source authority), and what surface
    it ran on (symbol set + spec digests).

    `shared_execution_contract_sha256` is passed IN, from the report of the run
    that bound it. It cannot be recovered afterwards: `sealed_inputs.prelude`
    stamps it on the args object the run used, and a rebuilt args is a different
    object -- binding one after the fact raises
    `shared_execution_contract_invalid`. It read `None` on four runs of this
    session before anyone looked, which is why the reason is recorded rather
    than the field left empty.
    """

    from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp

    surface = tuple(getattr(timewarp, "GTOS_24_SYMBOL_SURFACE", ()) or ())
    source_binding = dict(sealed.seal.get("source_authority_binding") or {})

    shared_digest = shared_execution_contract_sha256 or getattr(
        args, "expected_shared_execution_contract_sha256", None
    )
    shared_digest_unavailable = (
        "" if shared_digest else "not_reported_by_the_run_that_bound_it"
    )

    return {
        "train_engine_version": TRAIN_ENGINE_VERSION,
        "identity_tuple_version": identity.TUPLE_VERSION,
        "cuts_applied": list(patch_manifest.get("applied") or ()),
        "cuts_sealed_lane_compatible": patch_manifest.get("sealed_lane_compatible"),
        "arm_id": getattr(args, "arm_id", None),
        "window": [getattr(args, "start", None), getattr(args, "end", None)],
        "engineering_stop_after_day": getattr(args, "engineering_stop_after_day", None),
        "source_prewarm_workers": getattr(args, "source_prewarm_workers", None),
        "bounded_prewarm_previous_workers": getattr(
            args, "bounded_prewarm_previous_workers", None
        ),
        "bounded_prewarm_policy": getattr(args, "bounded_prewarm_policy", None),
        "decision_contract_path": str(sealed.contract),
        "decision_contract_sha256": _sha256_file(sealed.contract),
        "shared_execution_contract_digest_sha256": shared_digest,
        "shared_execution_contract_digest_unavailable_reason": (
            shared_digest_unavailable
        ),
        "source_authority_root_sha256": source_binding.get("authority_root_sha256"),
        "source_bundle_root_sha256": source_binding.get("bundle_root_sha256"),
        "source_plan_digest_sha256": source_binding.get("source_plan_digest_sha256"),
        "symbol_surface_count": len(surface),
        "symbol_surface_sha256": hashlib.sha256(
            json.dumps(sorted(surface)).encode("utf-8")
        ).hexdigest(),
        "spec_digests": {
            name: _sha256_file(REPO_ROOT / name) for name in SPEC_DIGEST_PATHS
        },
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }


def write_training_outputs(
    *,
    out_dir: Path,
    authorization: guard.WindowAuthorization,
    economics: dict[str, Any],
    run_fingerprint: dict[str, Any],
    measurements: dict[str, Any],
) -> dict[str, Path]:
    """Emit the compact trade table + receipt. Refuses an unauthorized purpose.

    This is the structural half of the guard's split (see `guard`): a
    reproduction run passes the blackout gate and can still never produce a
    training artifact, because this function checks the authorization object
    rather than a caller's intent.
    """

    if not authorization.may_emit_training_evidence:
        raise TrainingOutputRefused(
            "training outputs refused: window authorized for "
            f"{authorization.purpose!r} (trainable_checked="
            f"{authorization.trainable_checked}). Only a TRAINING window whose "
            "days all carry a trainable role may emit a training trade table."
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    table = out_dir / "TRAIN_TRADE_TABLE.jsonl"
    header = {
        "row_kind": "header",
        "evidence_class": TRAINING_EVIDENCE_STAMP,
        "identity_tuple_version": identity.TUPLE_VERSION,
        "identity_fields": list(identity.TRADE_IDENTITY_FIELDS),
        "fingerprint": run_fingerprint,
        "partition_authorization": authorization.as_dict(),
        "counts": economics.get("counts"),
    }
    lines = [json.dumps(header, sort_keys=True, default=str)]
    for row in economics.get("trades") or ():
        lines.append(
            json.dumps(
                {
                    "row_kind": "trade",
                    "evidence_class": TRAINING_EVIDENCE_STAMP,
                    **{
                        field: row.get(field)
                        for field in identity.TRADE_IDENTITY_FIELDS
                    },
                },
                sort_keys=True,
                default=str,
            )
        )
    table.write_text("\n".join(lines) + "\n")

    receipt = out_dir / "TRAIN_RUN_RECEIPT.json"
    receipt.write_text(
        json.dumps(
            {
                "evidence_class": TRAINING_EVIDENCE_STAMP,
                "fingerprint": run_fingerprint,
                "partition_authorization": authorization.as_dict(),
                "measurements": measurements,
                "counts": economics.get("counts"),
                "missed_opportunity_pool": economics.get("missed_digest"),
                "trade_table": str(table),
            },
            indent=1,
            sort_keys=True,
            default=str,
        )
    )
    return {"trade_table": table, "receipt": receipt}


def _resolve_run_inputs(
    *,
    sealed_inputs: Any,
    lane_input_registry: Path | None,
    lane_window_id: str | None,
    purpose: str,
    lane_source_plan_digest: str | None = None,
) -> tuple[Any, Any | None, str]:
    """Resolve exactly one replay window before any economic work starts.

    The historical path has exactly one legal window: sealed January.  A
    re-materialized LANE registry may carry several windows, so selecting one
    is mandatory and explicit.  Defaulting a registry run back to January is a
    dangerous failure mode: a caller asking for February could get a valid
    January arm and only discover the substitution after reading economics.
    """

    if lane_input_registry is None:
        if lane_window_id is not None:
            raise ValueError("lane_window_requires_lane_input_registry")
        if lane_source_plan_digest is not None:
            raise ValueError("lane_source_plan_digest_requires_lane_input_registry")
        sealed = sealed_inputs.resolve_sealed_january(REPO_ROOT)
        return sealed, None, "january_2026"

    if purpose != guard.PURPOSE_LANE_ITERATION:
        raise ValueError("lane_input_registry_requires_LANE_ITERATION")
    if not lane_window_id:
        raise ValueError("lane_input_registry_requires_explicit_window")

    from src.research_infra.lane_rematerialization import LaneInputRegistry

    provider = LaneInputRegistry(lane_input_registry).resolve(
        window_id=lane_window_id,
        purpose=purpose,
    )
    return provider, provider, lane_window_id


def _prefix_lane_inputs(
    input_provider: Any | None,
    *,
    effective_end: str,
    stop_after_day: str | None,
) -> Any | None:
    """Bind a requested LANE prefix before the engine builds source authority."""

    if input_provider is None or stop_after_day is None:
        return input_provider
    prefixer = getattr(input_provider, "for_prefix", None)
    if not callable(prefixer):
        raise ValueError("lane_input_provider_does_not_support_prefix_binding")
    bounded = prefixer(effective_end)
    if str(getattr(bounded, "window_end", "")) != effective_end:
        raise ValueError("lane_input_provider_prefix_end_mismatch")
    return bounded


def _effective_lane_inputs(
    input_provider: Any | None,
    *,
    effective_end: str,
    stop_after_day: str | None,
    source_plan_digest: str | None,
) -> Any | None:
    """Bind source scope first, then its explicitly measured plan digest.

    A prefix deliberately drops any full-window plan.  Applying the CLI digest
    before that operation would therefore erase the exact prefix authority and
    make every bounded arm refuse.  The digest is bound only after the effective
    provider exists, immediately before it reaches the engine.
    """

    effective = _prefix_lane_inputs(
        input_provider,
        effective_end=effective_end,
        stop_after_day=stop_after_day,
    )
    if effective is None or source_plan_digest is None:
        return effective
    binder = getattr(effective, "with_canonical_source_plan_digest", None)
    if not callable(binder):
        raise ValueError("lane_input_provider_does_not_support_source_plan_binding")
    bound = binder(source_plan_digest)
    if str(getattr(bound, "window_end", "")) != effective_end:
        raise ValueError("lane_input_provider_source_plan_changed_effective_end")
    return bound


def run(
    *,
    arm: str,
    days: int | None,
    stop_after_day: str | None,
    output_prefix: str,
    purpose: str,
    patches: list[str],
    abc_symbols: tuple[str, ...],
    verify: bool,
    profile_interval_ms: float,
    out: Path,
    keep_outputs: bool = False,
    training_out_dir: Path | None = None,
    repairs: "list[str] | None" = None,
    session: str = "",
    verdict: str = "evaluated",
    note: str = "",
    log_look: bool = True,
    iteration_ledger: Path | None = None,
    lane_input_registry: Path | None = None,
    lane_window_id: str | None = None,
    lane_source_plan_digest: str | None = None,
) -> dict[str, Any]:
    """Authorize, run, measure, and emit whatever the PURPOSE authorizes.

    Three purposes, three outputs, and the emitter for each checks the
    authorization object rather than this function's arguments:

    * `TRAINING` -> `TRAIN_TRADE_TABLE.jsonl` (CB)
    * `LANE_ITERATION` -> `LANE_TRADE_TABLE.jsonl` + one row in CC's shared
      iteration ledger (CD)
    * `ACCEPTANCE_REPRODUCTION` -> neither; the run report only.
    """

    from src.research_infra.fast_engine import bench, sealed_inputs

    repair_ids = list(repairs or ())
    sealed, input_provider, resolved_window_id = _resolve_run_inputs(
        sealed_inputs=sealed_inputs,
        lane_input_registry=lane_input_registry,
        lane_window_id=lane_window_id,
        purpose=purpose,
        lane_source_plan_digest=lane_source_plan_digest,
    )

    # Resolve the bound the ENGINE will use, then authorize THAT.
    window_days = guard.calendar_days(sealed.window_start, sealed.window_end)
    if stop_after_day is None and days is not None:
        if days < 1 or days > len(window_days):
            raise ValueError(f"days_out_of_range:1..{len(window_days)}")
        stop_after_day = window_days[days - 1]
    effective_end = stop_after_day or sealed.window_end
    input_provider = _effective_lane_inputs(
        input_provider,
        effective_end=effective_end,
        stop_after_day=stop_after_day,
        source_plan_digest=lane_source_plan_digest,
    )
    if input_provider is not None:
        sealed = input_provider

    authorization = guard.authorize_window(
        start=sealed.window_start,
        end=effective_end,
        purpose=purpose,
        context=f"train_engine:{arm}",
        note=(
            "prefix sub-window; account equity and the running conviction "
            "ledger accumulate across days, so only a prefix preserves "
            "outcome identity"
            if stop_after_day
            else "full sealed window"
        ),
    )

    # A repair is a patch like any other -- `--repairs` is a separate flag only
    # so that a receipt can tell a SPEED cut (must not change an outcome) from an
    # ECONOMIC repair (exists to change one). Both go through the one installer.
    repairs_mod.validate_repair_ids(repair_ids)
    all_patches = list(patches) + [
        rid for rid in repair_ids if rid not in patches
    ]

    def installer_factory(**kwargs: Any) -> Any:
        installer = cuts.build_installer(**kwargs)
        repairs_mod.register_repairs(installer, verify=kwargs.get("verify", False))
        return installer

    started = time.time()
    repairs_mod.reset_repair_stats()
    report = bench.run_window(
        arm=arm,
        stop_after_day=stop_after_day,
        output_prefix=output_prefix,
        patches=all_patches,
        abc_symbols=abc_symbols,
        verify=verify,
        profile_interval_ms=profile_interval_ms,
        keep_outputs=keep_outputs,
        evidence="full",
        installer_factory=installer_factory,
        extra_report={
            "train_engine_version": TRAIN_ENGINE_VERSION,
            "purpose": purpose,
            "partition_authorization": authorization.as_dict(),
            "cut_report": cuts.cut_report(),
        },
        input_provider=input_provider,
    )
    report["cut_report"] = cuts.cut_report()
    report["repairs_requested"] = repair_ids
    report["repair_report"] = repairs_mod.repair_report()
    report["wall_clock_started_epoch"] = started
    report["resolved_window_id"] = resolved_window_id

    if input_provider is None:
        args = sealed_inputs.build_january_args(
            repo_root=REPO_ROOT,
            arm_id=arm,
            output_dir=Path(report["route"]),
            output_prefix=output_prefix,
            stop_after_day=stop_after_day,
            sealed=sealed,
        )
    else:
        fingerprint_args = getattr(input_provider, "fingerprint_args", None)
        if callable(fingerprint_args):
            # A runtime input provider may have a one-shot fail-closed prelude
            # (`output namespace must be new`). Fingerprinting must describe the
            # args already run, never execute that prelude a second time.
            args = fingerprint_args(
                arm_id=arm,
                stop_after_day=stop_after_day,
            )
        else:
            args = input_provider.build_args(
                arm_id=arm,
                output_dir=Path(report["route"]),
                output_prefix=output_prefix,
                stop_after_day=stop_after_day,
            )
    run_fingerprint = fingerprint(
        sealed=sealed,
        args=args,
        patch_manifest=report.get("patch_manifest") or {},
        shared_execution_contract_sha256=report.get(
            "expected_shared_execution_contract_sha256"
        ),
    )
    report["fingerprint"] = run_fingerprint

    out.parent.mkdir(parents=True, exist_ok=True)
    slim = {key: value for key, value in report.items() if key != "economics"}
    if "economics" in report:
        slim["economics_counts"] = report["economics"]["counts"]
        slim["missed_digest"] = report["economics"]["missed_digest"]
        (out.parent / f"{out.stem}_ECONOMICS.json").write_text(
            json.dumps(report["economics"], indent=1, default=str)
        )
    out.write_text(json.dumps(slim, indent=1, default=str))

    measurements = {
        "wall_seconds": report.get("wall_seconds"),
        "maxrss_bytes": (report.get("rusage") or {}).get("maxrss_bytes"),
        "rss_peak_bytes": report.get("rss_peak_bytes"),
        "cut_report": report.get("cut_report"),
        "repair_report": report.get("repair_report"),
    }

    if purpose == guard.PURPOSE_TRAINING and "economics" in report:
        emitted = write_training_outputs(
            out_dir=training_out_dir or out.parent / f"{output_prefix}_TRAINING",
            authorization=authorization,
            economics=report["economics"],
            run_fingerprint=run_fingerprint,
            measurements=measurements,
        )
        report["training_outputs"] = {k: str(v) for k, v in emitted.items()}

    if purpose == guard.PURPOSE_LANE_ITERATION:
        spec = lane.run_spec(
            arm=arm,
            authorization=authorization,
            patches=report.get("patches_applied") or all_patches,
            repairs=repair_ids,
            contract_sha256=run_fingerprint.get("decision_contract_sha256"),
            shared_execution_contract_sha256=run_fingerprint.get(
                "shared_execution_contract_digest_sha256"
            ),
            extra={"lane_window_id": resolved_window_id},
        )
        report["lane_spec"] = spec
        lane_receipt = ""
        if "economics" in report:
            emitted = lane.write_iteration_outputs(
                out_dir=training_out_dir or out.parent / f"{output_prefix}_LANE",
                authorization=authorization,
                economics=report["economics"],
                run_fingerprint=run_fingerprint,
                measurements=measurements,
                spec=spec,
            )
            report["lane_outputs"] = {k: str(v) for k, v in emitted.items()}
            lane_receipt = str(emitted["receipt"])
        if log_look:
            # Logged even when the run ERRORED -- an abandoned look is still a
            # look, and the template's rule is "log as you go, not at the end".
            row = lane.log_look(
                authorization=authorization,
                spec=spec,
                session=session or "CD",
                verdict=("error" if report.get("error") else verdict),
                note=note,
                receipt=lane_receipt or str(out),
                ledger_path=iteration_ledger,
                extra={
                    "arm": arm,
                    "output_prefix": output_prefix,
                    "wall_seconds": report.get("wall_seconds"),
                    "maxrss_bytes": (report.get("rusage") or {}).get("maxrss_bytes"),
                    "counts": (report.get("economics") or {}).get("counts"),
                    "missed_opportunity_pool": (report.get("economics") or {}).get(
                        "missed_digest"
                    ),
                },
            )
            report["iteration_ledger_row"] = row
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", default="S1R1")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="bound the run to the first N calendar days of the window (prefix only)",
    )
    parser.add_argument("--stop-after-day", default=None)
    parser.add_argument(
        "--prefix",
        required=True,
        help=(
            "historical sealed runs require _B7_5_; an explicitly unsealed "
            "--lane-input-registry run must omit it so it cannot assert the "
            "historical decision-contract binding"
        ),
    )
    parser.add_argument(
        "--purpose",
        default=guard.PURPOSE_REPRODUCTION,
        choices=list(guard.PURPOSES),
        help=(
            "TRAINING enforces the trainable-role gate and emits the training "
            "contract; ACCEPTANCE_REPRODUCTION allows a sealed window for "
            "identity checking and can never emit training evidence"
        ),
    )
    parser.add_argument(
        "--patches",
        default=None,
        help="comma-separated cut ids; 'none' for the frozen baseline",
    )
    parser.add_argument("--abc-symbols", default=",".join(cuts.TRAIN_ABC_SYMBOLS))
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--profile-interval-ms", type=float, default=0.0)
    parser.add_argument("--keep-outputs", action="store_true")
    parser.add_argument(
        "--repairs",
        default=None,
        help=(
            "comma-separated repaired-stack repair ids to inject "
            f"(available: {','.join(repairs_mod.REPAIR_IDS)}); 'none' or omitted "
            "runs the frozen economics"
        ),
    )
    parser.add_argument("--session", default="CD", help="session id for the ledger row")
    parser.add_argument(
        "--verdict",
        default="evaluated",
        help="iteration-ledger verdict; the sealed gate's words are refused",
    )
    parser.add_argument("--note", default="")
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="do not write an iteration-ledger row (tests and dry runs only)",
    )
    parser.add_argument("--iteration-ledger", default=None)
    parser.add_argument(
        "--lane-input-registry",
        default=None,
        help=(
            "repo-local true-UTC LANE registry; requires --purpose "
            "LANE_ITERATION and intentionally breaks historical source/pack seals"
        ),
    )
    parser.add_argument(
        "--window",
        dest="lane_window_id",
        default=None,
        help=(
            "explicit LANE registry window id (for example january_2026 or "
            "february_2026); required with --lane-input-registry and refused "
            "without it"
        ),
    )
    parser.add_argument(
        "--lane-source-plan-digest",
        default=None,
        help=(
            "read-only canonical source-plan digest override for a registry "
            "window whose owning worktree must not be mutated"
        ),
    )
    parser.add_argument("--out", required=True)
    ns = parser.parse_args()

    if ns.days is not None and ns.stop_after_day is not None:
        parser.error("--days and --stop-after-day are mutually exclusive")

    report = run(
        arm=ns.arm,
        days=ns.days,
        stop_after_day=ns.stop_after_day,
        output_prefix=ns.prefix,
        purpose=ns.purpose,
        patches=cuts.resolve_patches(ns.patches),
        abc_symbols=tuple(s.strip() for s in ns.abc_symbols.split(",") if s.strip()),
        verify=ns.verify,
        profile_interval_ms=ns.profile_interval_ms,
        out=Path(ns.out),
        keep_outputs=ns.keep_outputs,
        repairs=repairs_mod.resolve_repairs(ns.repairs),
        session=ns.session,
        verdict=ns.verdict,
        note=ns.note,
        log_look=not ns.no_log,
        iteration_ledger=Path(ns.iteration_ledger) if ns.iteration_ledger else None,
        lane_input_registry=(
            Path(ns.lane_input_registry) if ns.lane_input_registry else None
        ),
        lane_window_id=ns.lane_window_id,
        lane_source_plan_digest=ns.lane_source_plan_digest,
    )
    print(
        f"[train-engine] arm={ns.arm} purpose={ns.purpose} "
        f"wall={report['wall_seconds']:.1f}s "
        f"maxrss={report['rusage']['maxrss_bytes'] / 1e9:.2f}GB "
        f"cuts={report['patches_applied']} "
        f"repairs={report.get('repairs_requested')} "
        f"surface={report['partition_authorization'].get('dominant_surface')}",
        file=sys.stderr,
    )
    if report.get("error"):
        print(report["error"][-4000:], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
