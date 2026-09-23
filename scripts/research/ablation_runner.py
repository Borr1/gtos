"""L57 — Ablation runner CLI.

Loops the ``AblationRun`` framework over a manifest, invoking the L56
prompt A/B harness once per manifest entry. The framework lives in
``src/research_infra/ablation_framework.py`` — this script is the loop
driver and CLI surface.

Quick examples
==============
Dry run (prints planned ablations, skips harness invocations):

    python scripts/research/ablation_runner.py \\
        --baseline-prompt prompts/short_validation_batch_prompt.md \\
        --manifest scripts/research/manifests/ablation_default_v1.yaml \\
        --fixtures historical_cands \\
        --metrics scripts/research/metrics/prompt_ab_default.yaml \\
        --output research/ablation_smoke \\
        --dry-run

Mocked harness run (Wave 1 default):

    python scripts/research/ablation_runner.py \\
        --baseline-prompt prompts/short_validation_batch_prompt.md \\
        --manifest scripts/research/manifests/ablation_default_v1.yaml \\
        --fixtures historical_cands \\
        --metrics scripts/research/metrics/prompt_ab_default.yaml \\
        --output research/ablation_v1

With realized-R join (verdict surfacing — recommended):

    python scripts/research/ablation_runner.py \\
        --baseline-prompt prompts/short_validation_batch_prompt.md \\
        --manifest scripts/research/manifests/ablation_default_v1.yaml \\
        --fixtures historical_cands \\
        --metrics scripts/research/metrics/prompt_ab_default.yaml \\
        --realized-r-join knowledge_base/trade_records \\
        --output research/ablation_v1_with_r

Pre-registration contract
=========================
The manifest filename + content are hashed into the run report. Editing
the manifest and re-running on the same baseline prompt produces a
DIFFERENT run hash — review tooling can detect the change. To run
fresh ablations, commit a NEW manifest (e.g.
``ablation_default_v2.yaml`` with ``manifest_set_id:
ablation_default_v2``) instead of editing the existing one.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import textwrap
from pathlib import Path
from typing import Sequence

# Resolve project root so the script can be invoked from anywhere
_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.ablation_framework import (  # noqa: E402
    AblationManifest,
    AblationRun,
)


logger = logging.getLogger("ablation_runner")


def _setup_logging(verbose: bool = False) -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s",
                          datefmt="%H:%M:%S")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ablation_runner",
        description=(
            "L57 — drive the L56 prompt A/B harness over an ablation "
            "manifest. Mocked-by-default; --live forwards to the harness."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Pre-registration: the manifest filename + content are hashed
            into the run report. Editing the manifest and re-running
            produces a different run hash. To run fresh ablations
            without breaking the audit trail, commit a NEW manifest
            (e.g. ablation_default_v2.yaml with a new manifest_set_id)
            and pass it via --manifest.
        """).strip(),
    )
    parser.add_argument("--baseline-prompt", required=True,
                        help="Path to the baseline prompt (.md/.txt).")
    parser.add_argument("--manifest", required=True,
                        help="Path to the ablation manifest (.yaml/.json).")
    parser.add_argument("--fixtures", required=True,
                        help=("Named set or path; passed through to "
                              "prompt_ab_harness."))
    parser.add_argument("--metrics", required=True,
                        help="Path to the pre-registered metrics YAML.")
    parser.add_argument("--output", required=True,
                        help="Output directory.")
    parser.add_argument("--realized-r-join", default=None,
                        help=("Trade-records dir or all_results.json path; "
                              "passed through to prompt_ab_harness."))
    parser.add_argument("--seed", type=int, default=1,
                        help="Mocked-mode seed.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print plan and exit without harness invocations.")
    parser.add_argument("--live", action="store_true",
                        help=("Forward --live to the harness (real Anthropic "
                              "API). NOT used in Wave 1; CEO will run "
                              "separately."))
    parser.add_argument("--harness-path", default=None,
                        help=("Override the prompt_ab_harness.py path "
                              "(default: scripts/research/prompt_ab_harness.py)."))
    parser.add_argument("--python-executable", default=None,
                        help=("Override the python executable used for "
                              "harness subprocesses (default: sys.executable)."))
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser


def _print_plan(run: AblationRun, manifest: AblationManifest) -> None:
    print("=== ablation_runner DRY-RUN PLAN ===")
    print(f"manifest: {manifest.path}")
    print(f"  set_id: {manifest.manifest_set_id}")
    print(f"  sha256: {manifest.sha256[:12]}")
    print(f"  run_hash: {manifest.run_hash[:12]}")
    print(f"baseline_prompt: {run.baseline_prompt}")
    print(f"fixtures: {run.fixtures_spec}")
    print(f"metrics: {run.metrics_path}")
    print(f"realized_r_join: {run.realized_r_join}")
    print(f"output: {run.output_dir}")
    print(f"seed: {run.seed}  live: {run.live}  dry-run: {run.dry_run}")
    print()
    print(f"Planned ablations ({len(manifest)}):")
    for entry in manifest:
        params_one_line = json.dumps(dict(entry.params), separators=(",", ":"))
        print(f"  - {entry.name:40s}  {entry.transformation:16s}  "
              f"params={params_one_line}")
    print()
    print("(skipping harness invocations — dry-run)")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    manifest = AblationManifest.load(args.manifest)

    run = AblationRun(
        baseline_prompt=args.baseline_prompt,
        manifest=manifest,
        fixtures_spec=args.fixtures,
        metrics_path=args.metrics,
        output_dir=args.output,
        realized_r_join=args.realized_r_join,
        seed=args.seed,
        dry_run=args.dry_run,
        live=args.live,
        harness_path=args.harness_path,
        python_executable=args.python_executable,
    )

    if args.dry_run:
        _print_plan(run, manifest)
        return 0

    summary = run.execute()
    n_errors = sum(1 for ent in summary["ablations"] if ent.get("error"))
    n_total = len(summary["ablations"])
    logger.info("Done. %d/%d ablations OK, %d errors. Wrote %s",
                n_total - n_errors, n_total, n_errors, run.output_dir)
    if summary.get("verdict_suppressed"):
        logger.info("Verdict suppressed: %s",
                    summary["verdict_suppressed"])
    return 0 if n_errors == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
