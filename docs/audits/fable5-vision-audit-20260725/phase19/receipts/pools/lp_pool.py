"""Session LP -- project one r0 lane arm into a mineable diagnostic pool.

Same contract as Session CS's `compact_arm` (`src/research_infra/cs_breaker_folds.py:487`)
and the same reader (`phase14/receipts/cd_pool.py`), so a pool produced here is
join-compatible with `CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz`,
`CS_APRIL_S0R0_POOL_V1.jsonl.gz` and `CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz` without
any downstream reconciliation.

It is NOT `cs_breaker_folds.compact_arm` itself: that function is bound to the
pre-declared April/May breaker fold plan (`_validate_arm_report_boundary` checks
a frozen look ledger and a V27 family digest) and refuses any window that is not
in its `WINDOWS` table. These 2025 windows carry no fold plan, no declared look,
and no gate -- by design, because LP produces inputs and takes no look.

Two deliberate differences from CS's payload, both stated in the receipt itself:

  * `compact_pool` carries no `train_dates` / `oos_dates`. CS derives those from
    its window's declared local split; LP has none, and inventing one here would
    be a fold decision made by the wrong session.
  * `fold_split_declared: false` and `looks_taken: 0` are stamped explicitly so a
    later reader cannot mistake the absence for an oversight.

The economic summary is a mechanical byproduct of the canonical reader, not an
analysis: it is written to the receipt because every prior pool receipt carries
it and the next wave's tooling reads it. LP does not read it.

Usage:
  lp_pool.py --prefix LP_OCT_2025_S0R0 --window-id october_2025 \
             --capture 2025-10-01 2025-10-31 \
             --source-plan-digest <DIGEST> --out <RECEIPT.json> \
             --compact <POOL.jsonl.gz>
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts"))

import cd_pool as CD_POOL  # noqa: E402

ARM_ID = "S0R0"
ROUTES = REPO / (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse"
)

#: The identity + geometry columns CS requires of any compact pool. Kept
#: verbatim so a pool refused there is refused here, at production time, rather
#: than at consumption time in a later session.
REQUIRED = {
    "candidate_id",
    "decision_time_utc",
    "symbol",
    "side",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "cost_r",
    "opportunity_net_proxy_r",
    "origin_family",
}


class LPRefusal(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path.resolve())


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:  # pragma: no cover - provenance only
        return "unknown"


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _pool_meta(pool: Path, capture: tuple[str, str]) -> tuple[int, dict[str, Any]]:
    """Validate the compact pool row-by-row and describe it. CS's checks."""
    rows = 0
    keys: set[tuple[str, str, str]] = set()
    dates: set[str] = set()
    for index, row in enumerate(_iter_gzip_jsonl(pool)):
        rows += 1
        missing = sorted(REQUIRED - set(row))
        if missing:
            raise LPRefusal(
                f"compact_pool_required_fields_missing_at_{index}:" + ",".join(missing)
            )
        raw = str(row.get("decision_time_utc") or "")
        try:
            decision = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise LPRefusal(f"compact_pool_time_unparseable_at_{index}:{raw}") from exc
        if decision.tzinfo is None:
            decision = decision.replace(tzinfo=dt.timezone.utc)
        day = decision.astimezone(dt.timezone.utc).date().isoformat()
        if not (capture[0] <= day <= capture[1]):
            raise LPRefusal(f"compact_pool_row_outside_capture_window:{day}")
        key = (ARM_ID, str(row.get("candidate_id") or ""), decision.isoformat())
        if not key[1] or key in keys:
            raise LPRefusal(f"compact_pool_join_key_invalid_or_duplicate:{key}")
        if (
            not str(row.get("symbol") or "")
            or str(row.get("side") or "").upper() not in {"LONG", "SHORT"}
            or not str(row.get("origin_family") or "")
        ):
            raise LPRefusal(f"compact_pool_identity_invalid:{key}")
        try:
            entry = float(row["entry_price"])
            stop = float(row["stop_loss"])
            values = (
                entry,
                stop,
                float(row["take_profit_1"]),
                float(row["cost_r"]),
                float(row["opportunity_net_proxy_r"]),
            )
        except (TypeError, ValueError) as exc:
            raise LPRefusal(f"compact_pool_numeric_invalid:{key}") from exc
        if not all(math.isfinite(value) for value in values) or entry == stop:
            raise LPRefusal(f"compact_pool_geometry_invalid:{key}")
        keys.add(key)
        dates.add(day)
    if not rows:
        raise LPRefusal("compact_pool_empty")
    return rows, {
        "path": _repo_path(pool),
        "sha256": _sha256_file(pool),
        "rows": rows,
        "unique_join_keys": len(keys),
        "dates": sorted(dates),
        "fold_split_declared": False,
        "fold_split_absent_reason": (
            "LP declares no local train/oos split for these windows; a fold plan "
            "is the consuming session's declaration, not the producer's"
        ),
    }


def _validate_arm(report: dict[str, Any], window_id: str, capture: tuple[str, str],
                  digest: str) -> None:
    if report.get("error") is not None:
        raise LPRefusal(f"arm_errored:{report.get('error')}")
    if report.get("arm") != ARM_ID:
        raise LPRefusal(f"arm_id_mismatch:{report.get('arm')}")
    if report.get("purpose") != "LANE_ITERATION":
        raise LPRefusal(f"purpose_not_lane_iteration:{report.get('purpose')}")
    authority = report.get("lane_input_authority") or {}
    if authority.get("window_id") != window_id:
        raise LPRefusal(f"window_id_mismatch:{authority.get('window_id')}")
    if list(authority.get("window") or []) != list(capture):
        raise LPRefusal(f"capture_window_mismatch:{authority.get('window')}")
    if authority.get("canonical_source_plan_digest_sha256") != digest:
        raise LPRefusal(
            "source_plan_digest_mismatch:"
            f"{authority.get('canonical_source_plan_digest_sha256')}"
        )
    if authority.get("campaign_sealed") is not False:
        raise LPRefusal("campaign_sealed_true_on_a_lane_window")
    if authority.get("clock_rule") != "new_york_plus_7":
        raise LPRefusal(f"clock_rule_unexpected:{authority.get('clock_rule')}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--window-id", required=True)
    ap.add_argument("--capture", nargs=2, required=True, metavar=("START", "END"))
    ap.add_argument("--source-plan-digest", required=True)
    ap.add_argument("--arm-report", default="")
    ap.add_argument("--compact", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--read-restricted",
        action="store_true",
        help=(
            "stamp the pool as built-but-unspent: the artifact exists and is "
            "join-ready, and no analysis may read its economics until a "
            "pre-declared test names the window"
        ),
    )
    ns = ap.parse_args()

    prefix = ns.prefix
    capture = (ns.capture[0], ns.capture[1])
    route = ROUTES / prefix
    ledger = route / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl.gz"
    if not ledger.is_file():
        plain = route / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl"
        if not plain.is_file():
            raise LPRefusal(f"missed_opportunity_ledger_absent:{ledger}")
        ledger = plain

    report_path = Path(ns.arm_report) if ns.arm_report else (
        Path(__file__).parent / "arm_receipts" / f"{prefix}_RECEIPT.json"
    )
    if not report_path.is_file():
        raise LPRefusal(f"arm_report_absent:{report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    _validate_arm(report, ns.window_id, capture, ns.source_plan_digest)

    compact = Path(ns.compact)
    compact.parent.mkdir(parents=True, exist_ok=True)
    summary = CD_POOL.summarise(ledger, compact)

    rows, pool_meta = _pool_meta(compact, capture)
    stated = summary.get("diagnostic_scoreable_rows")
    if stated is None or int(stated) != rows:
        raise LPRefusal(f"compact_scoreable_count_mismatch:{stated}!={rows}")

    payload: dict[str, Any] = {
        "schema": "gtos-session-lp-compact-s0r0-pool-v1",
        "compatible_with": "gtos-session-cs-compact-s0r0-pool-v1",
        "generated_at_utc": _utc_now(),
        "source_head": _git_head(),
        "surface": "VAL",
        "billed": False,
        "looks_taken": 0,
        "window_id": ns.window_id,
        "capture_window": [capture[0], capture[1]],
        "source_arm_id": ARM_ID,
        "raw_ledger": {
            "path": _repo_path(ledger),
            "sha256": _sha256_file(ledger),
            "bytes": ledger.stat().st_size,
        },
        "arm_report": {
            "path": _repo_path(report_path),
            "sha256": _sha256_file(report_path),
            "wall_seconds": report.get("wall_seconds"),
            "maxrss_bytes": (report.get("rusage") or {}).get("maxrss_bytes"),
            "receipt_counts": report.get("receipt_counts"),
        },
        "canonical_source_plan": {
            "canonical_source_plan_digest_sha256": ns.source_plan_digest,
            "authority": "LANE_INPUT_REGISTRY.json (read-only, external hold)",
            "registry_root_sha256": (report.get("lane_input_authority") or {}).get(
                "registry_root_sha256"
            ),
            "source_manifest_root_sha256": (
                report.get("lane_input_authority") or {}
            ).get("source_manifest_root_sha256"),
        },
        "compact_pool": pool_meta,
        "cd_reader_complete_summary": summary,
        "march_2026_outcomes_read": False,
        "february_2026_economics_read": False,
        "selection_authority": "NONE_SUBSTRATE_ONLY",
        "evidence_class": (
            "LANE_ITERATION_EVIDENCE - unbilled exploration, never admission-grade"
        ),
        "status": "DECLARED_S0R0_SURFACE_COMPACTED",
    }
    payload["read_restricted"] = bool(ns.read_restricted)
    if ns.read_restricted:
        payload["read_restriction"] = {
            "status": "BUILT_UNSPENT_HELD_OUT",
            "rule": (
                "No analysis may read this pool's economics until a "
                "pre-declared test names this window. Building a pool is not "
                "reading it; the artifact is an input, and its first economic "
                "read is a look that must be declared before it happens."
            ),
            "marker": str(compact) + ".READ_RESTRICTED",
        }

    body = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    payload["self_sha256"] = hashlib.sha256(body).hexdigest()
    Path(ns.out).write_text(json.dumps(payload, indent=1, default=str))

    if ns.read_restricted:
        Path(str(compact) + ".READ_RESTRICTED").write_text(
            "READ-RESTRICTED — built, unspent, held out.\n\n"
            f"window_id: {ns.window_id}\n"
            f"capture_window: {capture[0]} .. {capture[1]}\n"
            f"pool: {pool_meta['path']}\n"
            f"pool_sha256: {pool_meta['sha256']}\n"
            f"rows: {pool_meta['rows']}\n"
            f"receipt: {_repo_path(Path(ns.out))}\n\n"
            "This pool exists so that a future test does not have to wait three\n"
            "hours for it. It is NOT available to any analysis until a\n"
            "pre-declared test names this window. Reading its economics without\n"
            "that declaration spends the estate's held-out set and cannot be\n"
            "undone. Session LP produced it and did not read it.\n"
        )

    # Structural only. The economic columns of `summary` are deliberately not
    # printed: LP produces inputs.
    print(
        json.dumps(
            {
                "window_id": ns.window_id,
                "pool": pool_meta["path"],
                "rows": pool_meta["rows"],
                "unique_join_keys": pool_meta["unique_join_keys"],
                "days": len(pool_meta["dates"]),
                "sha256": pool_meta["sha256"],
                "receipt": str(Path(ns.out)),
                "self_sha256": payload["self_sha256"],
            },
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
