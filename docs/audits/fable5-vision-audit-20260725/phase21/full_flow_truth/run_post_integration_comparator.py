#!/usr/bin/env python3
"""Fresh full-flow comparator producer run under integrated code (wave 21, post-integration).

Why this driver exists
----------------------
`wave21_full_flow_harness.main source-worker` (the committed CLI) forwards the
verified source-estate authority payload into ``execute_full_flow``, whose
``_loader_owned_raw_source_authority_fields_by_symbol`` is a deliberately
fail-closed stub: the producer-attached v2 source-authority receipt machinery is
NOT integrated (it is the un-commissioned truth-chain work recorded as an open
item in ``WAVE21_INTEGRATION.md`` §11), so any non-empty ``source_authority``
raises ``loader_owned_source_authority_receipt_v2_dependency_not_integrated``.
The committed ``source-worker`` path is therefore structurally unrunnable at
HEAD — measured, not assumed: a plain ``source-worker`` invocation for
2025-10-28 raised exactly that error after estate byte-verification.

Every producer run on record — the eleven retained comparator ledgers and the
DAG-repair session's fresh one-day mirror proof — executed with
``inputs.source_authority == {}`` and
``raw_source_authority_fields_by_symbol_root_sha256 == sha256({})`` (verified by
direct read of their run receipts). This driver reproduces exactly those
recorded producer semantics under integrated code: estates are still
byte-verified, sources still load through the same lane resolvers, and the only
difference from ``run_source_bound_worker`` is ``source_authority=None`` at the
``execute_full_flow`` call — the argument every prior run's receipt shows it
effectively ran with. The full verified authority payload and loaded projection
are still written into the run artifacts, unchanged.

This is an offline ``research_timewarp`` engineering comparator. No broker
client, no activation token, no live state. Days must be already-opened
development days inside the harness's preregistered interval.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.wave21_full_flow_harness import (  # noqa: E402
    _atomic_write_json,
    _inclusive_days,
    _raw_campaign,
    _resource_measurement,
    _safe_label,
    execute_full_flow,
    load_real_source_bound_inputs,
    load_repaired_replay_config,
    strict_json_primitive,
    verify_real_source_estates,
    write_run_artifacts,
)


def run(*, output_dir: Path, label: str, start: str, end: str) -> dict:
    days = _inclusive_days(start, end)
    authority = verify_real_source_estates(verify_payload_bytes=True)
    sources, loaded = load_real_source_bound_inputs(
        days=days, source_authority=authority
    )
    label = _safe_label(label)
    stage_path = output_dir / f"harness_{label}_stage_ledger.jsonl.gz"
    sink_root = output_dir / f"harness_{label}_compact_events"
    payload = execute_full_flow(
        campaign=_raw_campaign(days, truth_mode=False),
        config=load_repaired_replay_config(),
        sources=sources,
        result_scope="source_bound_engineering_comparator",
        truth_mode=False,
        compact_sink_root=sink_root,
        # Recorded producer semantics of every retained run (see docstring):
        # the v2 receipt dependency stays fail-closed for any FORWARDED
        # authority; nothing here weakens that stub.
        source_authority=None,
        compact_oracle=None,
        stage_ledger_path=stage_path,
    )
    initial_paths = write_run_artifacts(
        output_dir,
        label=label,
        payload=payload,
        source_authority=authority,
        loaded_projection=loaded,
    )
    measurement = _resource_measurement(
        result=payload["result"], output_paths=list(initial_paths.values())
    )
    _atomic_write_json(initial_paths["resource"], measurement)
    from src.research_infra.wave21_full_flow_verifier import (
        VerificationError,
        verify as independent_verify,
    )

    try:
        verification = independent_verify(
            stage_ledger=initial_paths["stage_ledger"],
            fingerprint_path=initial_paths["fingerprint"],
            receipt_path=initial_paths["receipt"],
        )
    except VerificationError as exc:
        # Fail-closed disclosure: the refusal is the verification result.  The
        # producer artifacts above are complete; a crashed driver would hide
        # exactly the refusal a comparator receipt must report.
        verification = {
            "status": "REFUSED",
            "refusal": str(exc),
            "refusal_class": "independent_verifier_fail_closed",
        }
    verification_path = output_dir / f"harness_{label}_independent_verification.json"
    _atomic_write_json(verification_path, verification)
    return {
        "label": label,
        "paths": {
            **{key: str(value) for key, value in initial_paths.items()},
            "independent_verification": str(verification_path),
        },
        "receipt": payload["receipt"],
        "independent_verification": verification,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    args = parser.parse_args(argv)
    result = run(
        output_dir=args.output_dir,
        label=args.label,
        start=args.start,
        end=args.end,
    )
    summary = {
        "label": result["label"],
        "paths": result["paths"],
        "status": result["receipt"].get("status"),
        "independent_verification_status": result[
            "independent_verification"
        ].get("status"),
    }
    print(json.dumps(strict_json_primitive(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
