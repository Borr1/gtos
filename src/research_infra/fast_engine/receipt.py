"""Assemble the session's reproduction receipt from the run artifacts.

The receipt is the deliverable. It states, in one place: what was run, on which
sealed inputs, with which patches, what it cost, and whether the answer was the
frozen engine's answer. Anything the comparator excluded is named in it, because
an exclusion list you cannot read is indistinguishable from a comparator that
passes everything.
"""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from typing import Any


def _load(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    p = Path(path)
    return json.loads(p.read_text()) if p.is_file() else None


def build_receipt(
    *,
    baseline_report: dict[str, Any],
    fast_report: dict[str, Any],
    comparison: dict[str, Any],
    concurrency: dict[str, Any] | None = None,
    notes: list[str] | None = None,
    control_comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the receipt.

    ``control_comparison`` is a frozen-vs-frozen run of the same fixture. Two
    runs of one arm cannot produce identical ledgers (the engine refuses to
    reuse an output namespace and stamps it inside hashed payloads), so a
    ``PROVENANCE_DIGESTS_ONLY`` verdict counts as reproduction **only** when the
    control produces the same difference signature. Without a control it does
    not count, and this function will not mark it accepted.
    """
    base_wall = float(baseline_report["wall_seconds"])
    fast_wall = float(fast_report["wall_seconds"])
    base_rss = int(baseline_report["rusage"]["maxrss_bytes"])
    fast_rss = int(fast_report["rusage"]["maxrss_bytes"])

    receipt: dict[str, Any] = {
        "schema": "gtos.fast_engine.reproduction_receipt.v1",
        "session": "AX",
        "blocks": "B1700-B1749",
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "fixture": {
            "arm": baseline_report.get("arm"),
            "window_start": baseline_report.get("window_start"),
            "stop_after_day": baseline_report.get("stop_after_day"),
            "is_sealed_arm_of_record": baseline_report.get("stop_after_day") is None,
            "note": (
                "A day-bounded run sets engineering_stop_after_day, which the "
                "sealed path hardcodes to None (CLAUDE.md H5). It is a fixture, "
                "never an arm of record."
            ),
        },
        "frozen": {
            "wall_seconds": base_wall,
            "maxrss_bytes": base_rss,
            "patches_applied": baseline_report.get("patches_applied"),
            "receipt_counts": baseline_report.get("receipt_counts"),
            "progress_rows": baseline_report.get("progress_rows"),
        },
        "fast": {
            "wall_seconds": fast_wall,
            "maxrss_bytes": fast_rss,
            "evidence_level": fast_report.get("evidence_level"),
            "patches_applied": fast_report.get("patches_applied"),
            "sealed_lane_compatible": fast_report.get("patch_manifest", {}).get(
                "sealed_lane_compatible"
            ),
            "memo_report": fast_report.get("memo_report"),
            "verify_report": fast_report.get("verify_report"),
            "receipt_counts": fast_report.get("receipt_counts"),
            "progress_rows": fast_report.get("progress_rows"),
        },
        "delta": {
            "wall_speedup": round(base_wall / fast_wall, 4) if fast_wall else None,
            "wall_seconds_saved": round(base_wall - fast_wall, 3),
            "maxrss_ratio": round(fast_rss / base_rss, 4) if base_rss else None,
            "maxrss_bytes_delta": fast_rss - base_rss,
        },
        "reproduction": comparison,
        "notes": notes or [],
    }

    signature_matches_control = None
    if control_comparison is not None:
        receipt["control"] = {
            "verdict": control_comparison.get("verdict"),
            "difference_count": control_comparison.get("difference_count"),
            "quantity_difference_count": control_comparison.get(
                "quantity_difference_count"
            ),
            "difference_signature": control_comparison.get("difference_signature"),
        }
        signature_matches_control = control_comparison.get(
            "difference_signature"
        ) == comparison.get("difference_signature")
        receipt["control"]["signature_matches_candidate"] = signature_matches_control

    verdict_ok = comparison.get("verdict") in {"R_IDENTICAL", "ECONOMICALLY_IDENTICAL"} or (
        comparison.get("verdict") == "PROVENANCE_DIGESTS_ONLY"
        and comparison.get("quantity_difference_count") == 0
        and signature_matches_control is True
    )
    receipt["accepted"] = bool(
        verdict_ok
        and baseline_report.get("error") is None
        and fast_report.get("error") is None
        and baseline_report.get("receipt_counts") == fast_report.get("receipt_counts")
    )
    receipt["acceptance_basis"] = (
        "R_IDENTICAL"
        if comparison.get("verdict") == "R_IDENTICAL"
        else (
            "PROVENANCE_DIGESTS_ONLY validated by a frozen-vs-frozen control with "
            "an identical difference signature and zero moved quantities"
            if receipt["accepted"]
            else "NOT ACCEPTED"
        )
    )
    if concurrency is not None:
        receipt["concurrency"] = concurrency
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--fast", required=True)
    parser.add_argument("--comparison", required=True)
    parser.add_argument("--concurrency", default=None)
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument("--out", required=True)
    ns = parser.parse_args()

    receipt = build_receipt(
        baseline_report=_load(ns.baseline),
        fast_report=_load(ns.fast),
        comparison=_load(ns.comparison),
        concurrency=_load(ns.concurrency),
        notes=list(ns.note),
    )
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=1, default=str))
    print(
        f"[receipt] accepted={receipt['accepted']} "
        f"verdict={receipt['reproduction'].get('verdict')} "
        f"speedup={receipt['delta']['wall_speedup']}x "
        f"rss_ratio={receipt['delta']['maxrss_ratio']} -> {out}"
    )
    return 0 if receipt["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
