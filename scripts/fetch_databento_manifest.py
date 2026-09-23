#!/usr/bin/env python3
"""Estimate or fetch Databento windows from an orderflow event manifest.

Research/tooling only. The default mode estimates cost and writes a plan. Data
is fetched only with `--execute`, after per-group and total cost caps pass.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.databento_futures import (  # noqa: E402
    DEFAULT_DATABENTO_DATASET,
    DEFAULT_DATABENTO_RAW_ROOT,
    DEFAULT_DATABENTO_SCHEMA,
    DEFAULT_DATABENTO_STYPE_IN,
    DatabentoRequest,
    estimate_request,
    estimate_to_dict,
    fetch_request,
    historical_client,
    load_databento_env,
    request_output_path,
)


DEFAULT_MANIFEST = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_FETCH_PLAN_OF_DATA_2_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_FETCH_PLAN_OF_DATA_2_2026-05-02.md"
)


def load_manifest(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def request_from_group(
    group: dict[str, Any],
    *,
    dataset: str,
    schema: str,
    stype_in: str,
) -> DatabentoRequest:
    return DatabentoRequest(
        dataset=dataset,
        schema=schema,
        symbols=tuple(group["databento_symbols"]),
        start=group["start_utc"],
        end=group["end_utc"],
        stype_in=stype_in,
    )


def select_groups(manifest: dict[str, Any], group_ids: list[str] | None) -> list[dict[str, Any]]:
    groups = list(manifest.get("fetch_groups") or [])
    if not group_ids:
        return groups
    wanted = set(group_ids)
    return [group for group in groups if group.get("group_id") in wanted]


def build_plan(
    manifest: dict[str, Any],
    *,
    client: Any,
    dataset: str,
    schema: str,
    stype_in: str,
    root: Path | str,
    max_group_cost_usd: float,
    max_total_cost_usd: float,
    group_ids: list[str] | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total_cost = 0.0
    blockers: list[str] = []
    for group in select_groups(manifest, group_ids):
        request = request_from_group(group, dataset=dataset, schema=schema, stype_in=stype_in)
        estimate = estimate_request(client, request)
        output_path = request_output_path(request, root)
        row = {
            "group_id": group["group_id"],
            "event_count": group["event_count"],
            "event_classes": group["event_classes"],
            "request": asdict(request),
            "estimate": estimate_to_dict(estimate),
            "output_path": str(output_path),
            "output_exists": output_path.exists(),
            "status": "planned",
        }
        total_cost += estimate.cost_usd
        if estimate.cost_usd > max_group_cost_usd:
            row["status"] = "blocked_group_cost"
            blockers.append(
                f"{group['group_id']} cost ${estimate.cost_usd:.6f} exceeds group cap ${max_group_cost_usd:.6f}"
            )
        rows.append(row)

    if total_cost > max_total_cost_usd:
        blockers.append(
            f"total cost ${total_cost:.6f} exceeds total cap ${max_total_cost_usd:.6f}"
        )

    return {
        "schema_version": "orderflow_event_window_fetch_plan_v1",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "manifest_schema_version": manifest.get("schema_version"),
            "dataset": dataset,
            "schema": schema,
            "stype_in": stype_in,
            "root": str(root),
            "group_ids": group_ids,
            "max_group_cost_usd": max_group_cost_usd,
            "max_total_cost_usd": max_total_cost_usd,
        },
        "groups": rows,
        "blocked": bool(blockers),
        "blockers": blockers,
        "total_estimated_cost_usd": total_cost,
    }


def execute_plan(
    plan: dict[str, Any],
    *,
    client: Any,
    root: Path | str,
    force: bool,
) -> None:
    if plan["blocked"]:
        raise RuntimeError(f"refusing to execute blocked plan: {plan['blockers']}")
    group_cap = float(plan["inputs"]["max_group_cost_usd"])
    for row in plan["groups"]:
        if row["output_exists"] and not force:
            row["status"] = "cached"
            row["output_exists"] = True
            continue
        request = DatabentoRequest(**row["request"])
        result = fetch_request(
            client,
            request,
            root=root,
            max_cost_usd=group_cap,
            force=force,
        )
        row["status"] = "fetched"
        row["output_path"] = result.output_path
        row["metadata_path"] = result.metadata_path
        row["output_exists"] = True


def add_synthesis(plan: dict[str, Any], *, executed: bool) -> None:
    statuses = {}
    for row in plan["groups"]:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    schema = plan.get("inputs", {}).get("schema", "requested")
    if schema == "trades":
        schema_limitation = "Trades schema cannot reproduce full heatmap/depth visuals; depth pulls need a later gate."
    elif schema == "mbp-1":
        schema_limitation = "MBP-1 schema exposes top-of-book updates only; full ladder reconstruction needs deeper book or MBO pulls."
    elif schema == "mbp-10":
        schema_limitation = "MBP-10 schema exposes top ten book levels, but not full order identity, queue position, or complete MBO reconstruction."
    else:
        schema_limitation = f"{schema} schema limitations must be documented before using it for inference."
    plan["executed"] = executed
    plan["synthesis"] = {
        "summary": (
            f"This plan estimates or fetches {schema}-schema Databento windows from "
            "the GTOS orderflow event manifest. It is data acquisition plumbing, "
            "not an alpha or promotion claim."
        ),
        "group_status_counts": statuses,
        "ambiguities": [
            "Cost estimates are vendor metadata values and may differ from final billing.",
            schema_limitation,
            "Cached files are treated as available raw inputs but are not revalidated unless force is used.",
        ],
        "open_questions": [
            "After trades windows are fetched, which features survive candidate-versus-context diagnostics?",
            "Are any event groups too sparse or truncated to use for orderflow inference?",
            "Which subset, if any, justifies a depth-schema spend?",
        ],
        "next_steps": [
            "Extract trades-level orderflow features for fetched windows.",
            "Join features to GTOS event rows and synthetic/actual outcomes.",
            "Register any structural hypothesis before testing a decision rule.",
        ],
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    synth = payload["synthesis"]
    lines = [
        "# Orderflow Event Window Fetch Plan",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Cost",
        "",
        f"- Executed: {payload['executed']}",
        f"- Blocked: {payload['blocked']}",
        f"- Total estimated cost USD: ${payload['total_estimated_cost_usd']:.6f}",
        f"- Status counts: {synth['group_status_counts']}",
        "",
        "## Groups",
        "",
        "| Group | Status | Cost USD | Records | Output exists |",
        "|---|---|---:|---:|---:|",
    ]
    for row in payload["groups"]:
        lines.append(
            "| "
            f"{row['group_id']} | "
            f"{row['status']} | "
            f"{row['estimate']['cost_usd']:.6f} | "
            f"{row['estimate']['record_count']} | "
            f"{row['output_exists']} |"
        )
    lines.extend(
        [
            "",
            "## Blockers",
            "",
            *([f"- {item}" for item in payload["blockers"]] or ["- None"]),
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguities"]],
            "",
            "## Open Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["open_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.write_text("\n".join(lines), encoding="utf-8")


def parse_group_ids(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    out: list[str] = []
    for value in values:
        out.extend(part.strip() for part in value.split(",") if part.strip())
    return out or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--dataset", default=DEFAULT_DATABENTO_DATASET)
    parser.add_argument("--schema", default=DEFAULT_DATABENTO_SCHEMA)
    parser.add_argument("--stype-in", default=DEFAULT_DATABENTO_STYPE_IN)
    parser.add_argument("--root", default=str(DEFAULT_DATABENTO_RAW_ROOT))
    parser.add_argument("--group-id", action="append", help="Optional group id filter; repeatable or comma-separated.")
    parser.add_argument("--max-group-cost-usd", type=float, default=1.0)
    parser.add_argument("--max-total-cost-usd", type=float, default=8.0)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        parser.exit(2, f"manifest not found: {manifest_path}\n")
    load_databento_env(PROJECT_ROOT)
    client = historical_client()
    manifest = load_manifest(manifest_path)
    plan = build_plan(
        manifest,
        client=client,
        dataset=args.dataset,
        schema=args.schema,
        stype_in=args.stype_in,
        root=args.root,
        max_group_cost_usd=args.max_group_cost_usd,
        max_total_cost_usd=args.max_total_cost_usd,
        group_ids=parse_group_ids(args.group_id),
    )
    if args.execute:
        execute_plan(plan, client=client, root=args.root, force=args.force)
    add_synthesis(plan, executed=args.execute)
    write_json(plan, args.output_json)
    write_markdown(plan, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"executed={args.execute} blocked={plan['blocked']} "
        f"groups={len(plan['groups'])} cost=${plan['total_estimated_cost_usd']:.6f}"
    )
    if plan["blockers"]:
        for blocker in plan["blockers"]:
            print(f"blocker: {blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
