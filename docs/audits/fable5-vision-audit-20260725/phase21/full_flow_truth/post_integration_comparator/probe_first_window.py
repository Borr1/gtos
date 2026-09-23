#!/usr/bin/env python3
"""Probe: which scheduler rows lack candidate_occurrence_key in the first failing window."""
import json
import sys
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/wave21-post-integration-measurements")
sys.path.insert(0, str(REPO))

import src.research.moonshot_scheduler_v4_best_trade_allocator as alloc  # noqa: E402

_orig = alloc._allocate_decision_window_impl


def probing(window, config=None, *, raw_config=None, _pristine_trace_sink=None):
    try:
        return _orig(
            window,
            config,
            raw_config=raw_config,
            _pristine_trace_sink=_pristine_trace_sink,
        )
    except ValueError as exc:
        if "pristine" not in str(exc):
            raise
        rows = (
            window.get("candidates")
            if isinstance(window, dict)
            else getattr(window, "candidates", None)
        )
        report = {"error": str(exc), "n_rows": None, "rows": []}
        if rows is not None:
            seq = list(rows)
            report["n_rows"] = len(seq)
            for i, row in enumerate(seq):
                if hasattr(row, "metadata"):
                    m = dict(row.metadata)
                    cid = getattr(row, "candidate_id", "")
                else:
                    m = dict(row)
                    cid = row.get("candidate_id")
                report["rows"].append(
                    {
                        "i": i,
                        "candidate_id": cid,
                        "candidate_id_source": m.get("candidate_id_source"),
                        "has_occurrence_key": bool(
                            str(m.get("candidate_occurrence_key") or "").strip()
                        ),
                        "occurrence_key": str(
                            m.get("candidate_occurrence_key") or ""
                        )[:100],
                        "has_fingerprint": bool(
                            m.get("candidate_source_safe_fingerprint_sha256")
                            or m.get("candidate_source_safe_fingerprint")
                        ),
                        "emission_ordinal": m.get("candidate_emission_ordinal"),
                        "instance_key": str(
                            m.get("canonical_replay_candidate_instance_key") or ""
                        )[:100],
                        "symbol": m.get("symbol"),
                        "origin_family": (
                            m.get("origin_family")
                            or m.get("candidate_origin_family")
                            or m.get("framework")
                        ),
                        "selector_action": m.get("selector_action"),
                        "row_keys_sample": sorted(m.keys())[:0],
                    }
                )
        Path("/private/tmp/w21-postinteg-taskB/probe_window_report.json").write_text(
            json.dumps(report, indent=1, default=str) + "\n"
        )
        missing = [r for r in report["rows"] if not r["has_occurrence_key"]]
        print(
            json.dumps(
                {
                    "error": report["error"],
                    "n_rows": report["n_rows"],
                    "n_missing_occurrence_key": len(missing),
                    "missing_sample": missing[:8],
                },
                indent=1,
                default=str,
            ),
            file=sys.stderr,
        )
        raise SystemExit(3)


alloc._allocate_decision_window_impl = probing

sys.path.insert(
    0,
    str(
        REPO
        / "docs/audits/fable5-vision-audit-20260725/phase21/full_flow_truth"
    ),
)
import run_post_integration_comparator as driver  # noqa: E402

driver.run(
    output_dir=Path("/private/tmp/w21-postinteg-probe-20251028"),
    label="wave21_probe_20251028",
    start="2025-10-28",
    end="2025-10-28",
)
