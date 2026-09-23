"""Forward-capture claim ledger helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "forward_capture_claim_ledger_v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_claim_row(
    *,
    claim_id: str,
    claim: str,
    evidence_class: str,
    opened_slice: str,
    sample_size: int,
    label_lane: str,
    cost_model: str,
    status: str,
    dsr_status: str = "not_computable",
    pbo_status: str = "not_computable",
    effective_n_status: str = "not_computable",
    not_computable_reason: str = "sample_floor_or_validation_lane_not_met",
    source_artifact: str | None = None,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "claim": claim,
        "evidence_class": evidence_class,
        "opened_slice": opened_slice,
        "sample_size": int(sample_size),
        "label_lane": label_lane,
        "cost_model": cost_model,
        "status": status,
        "dsr_status": dsr_status,
        "pbo_status": pbo_status,
        "effective_n_status": effective_n_status,
        "not_computable_reason": not_computable_reason,
        "source_artifact": source_artifact,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def build_claim_ledger(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    evidence_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        evidence_counts[row["evidence_class"]] = evidence_counts.get(row["evidence_class"], 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now_iso(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status_counts": dict(sorted(status_counts.items())),
        "evidence_class_counts": dict(sorted(evidence_counts.items())),
        "claims": rows,
        "promotion_dossier_required": True,
        "promotion_boundary": (
            "This ledger records research claims only. Promotion requires a "
            "separate dossier with frozen rules, unseen validation, cost "
            "accounting, concentration diagnostics, DSR/PBO/effective-N where "
            "computable, and explicit owner approval."
        ),
    }


def write_claim_ledger(payload: dict[str, Any], json_path: str | Path, md_path: str | Path) -> None:
    out_json = Path(json_path)
    out_md = Path(md_path)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_claim_ledger_md(payload), encoding="utf-8")


def render_claim_ledger_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Forward Capture Claim Ledger - 2026-05-04",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Claims",
        "",
        "| Claim | Evidence | Slice | n | Label lane | Status | DSR/PBO/effective-N |",
        "|---|---|---|---:|---|---|---|",
    ]
    for row in payload["claims"]:
        lines.append(
            "| {claim_id} | `{evidence}` | `{slice}` | {n} | `{lane}` | `{status}` | `{dsr}` / `{pbo}` / `{eff}` |".format(
                claim_id=row["claim_id"],
                evidence=row["evidence_class"],
                slice=row["opened_slice"],
                n=row["sample_size"],
                lane=row["label_lane"],
                status=row["status"],
                dsr=row["dsr_status"],
                pbo=row["pbo_status"],
                eff=row["effective_n_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Promotion Boundary",
            "",
            payload["promotion_boundary"],
        ]
    )
    return "\n".join(lines) + "\n"
