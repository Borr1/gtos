#!/usr/bin/env python3
"""B6 broker-cost calibration audit for the Fable ultimate-system ladder.

This is a read-only proof script.  It samples broker-cost REFUSED candidate
rows, joins them to owner-authorized ordered tick evidence when available, and
classifies whether the refusal is still valid under raw/measured tick spread.

It does not loosen REFUSED gates and does not make broker/live/final claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
DEFAULT_PREFIX = (
    "BROAD_LIVE_AS_IF_REPLAY_V122J_FABLE_B4_HOSTILE_5D_FILL_REALISM_TICK_HYDRATED_"
    "20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH"
)
DEFAULT_TICK_MANIFEST = (
    REPO_ROOT
    / "data/mt5_research_exports/bridge_ftmo_ticks_v122i_20260513_20260517_full_plus_expiry/manifest.json"
)
DEFAULT_SAMPLE_PER_CELL = 20
DEFAULT_LOOKBACK_MINUTES = 60.0
DEFAULT_MAX_SPREAD_R = 0.10
DEFAULT_MAX_TOTAL_COST_R = 0.15

try:
    from src.components.ultimate_book.admission import TICK_SPREAD_FLOOR_R
except Exception:  # pragma: no cover - import failure is reported in outputs.
    TICK_SPREAD_FLOOR_R = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def listish(value: Any) -> list[Any]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if isinstance(row, dict):
                yield row


def normalize_refusal_family(reason: Any) -> str:
    text = str(reason or "").strip()
    if not text:
        return "unknown_refusal_reason"
    return text.split(":", 1)[0] or "unknown_refusal_reason"


def parse_limit(reason: str, default: float | None) -> float | None:
    match = re.search(r">([0-9]+(?:\.[0-9]+)?)", str(reason or ""))
    if match:
        return safe_float(match.group(1), default)
    return default


def pretrade_cost_refusal_reasons(row: Mapping[str, Any]) -> list[str]:
    packet = mapping(row.get("pretrade_broker_net_cost_packet"))
    raw_reasons = first_present(
        row.get("pretrade_cost_refusal_reasons"),
        row.get("broker_net_pretrade_cost_refusal_reasons"),
        row.get("broker_cost_refusal_reasons"),
        packet.get("refusal_reasons"),
    )
    reasons = [str(item).strip() for item in listish(raw_reasons) if item not in (None, "")]
    if reasons:
        return reasons
    reason = first_present(
        row.get("broker_pretrade_cost_executable_block_reason"),
        row.get("pretrade_cost_packet_refusal_reason"),
        row.get("broker_net_cost_refusal_reason"),
        packet.get("refusal_reason"),
    )
    reasons = [str(item).strip() for item in listish(reason) if item not in (None, "")]
    return reasons or ["unknown_refusal_reason"]


def cost_refused(row: Mapping[str, Any]) -> bool:
    packet = mapping(row.get("pretrade_broker_net_cost_packet"))
    status = str(first_present(row.get("pretrade_cost_packet_status"), packet.get("status")) or "").upper()
    if status == "REFUSED":
        return True
    executable = row.get("broker_pretrade_cost_executable")
    return executable is False and bool(pretrade_cost_refusal_reasons(row))


def session_key(row: Mapping[str, Any]) -> str:
    return str(
        first_present(
            row.get("session"),
            row.get("route_session"),
            row.get("authority_session"),
            row.get("kill_zone"),
            "unknown_session",
        )
    )


def cell_key(row: Mapping[str, Any], reason: str) -> tuple[str, str, str]:
    return (
        str(row.get("symbol") or "unknown_symbol"),
        session_key(row),
        normalize_refusal_family(reason),
    )


def compact_sample(row: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "candidate_id": row.get("candidate_id"),
        "canonical_replay_candidate_instance_key": row.get("canonical_replay_candidate_instance_key"),
        "decision_time_utc": row.get("decision_time_utc"),
        "symbol": row.get("symbol"),
        "session": session_key(row),
        "side": row.get("side") or row.get("direction"),
        "entry_price": row.get("entry_price"),
        "stop_loss": row.get("stop_loss"),
        "reason": reason,
        "reason_family": normalize_refusal_family(reason),
        "all_reasons": pretrade_cost_refusal_reasons(row),
        "expected_cost_r": first_present(
            row.get("expected_cost_r"),
            row.get("broker_pretrade_cost_non_executable_diagnostic_expected_cost_r"),
            row.get("cost_r"),
        ),
        "spread_r": row.get("spread_r"),
        "expected_slippage_r": row.get("expected_slippage_r"),
        "swap_cost_r": row.get("swap_cost_r"),
        "cost_quote_source": row.get("cost_quote_source"),
        "historical_tick_time_utc": row.get("historical_tick_time_utc"),
        "measured_tick_spread_floor_r": row.get("measured_tick_spread_floor_r"),
        "measured_tick_spread_floor_enforced": row.get("measured_tick_spread_floor_enforced"),
        "cost_source_gap_status": row.get("cost_source_gap_status"),
        "candidate_cost_r_fallback_is_authority": row.get("candidate_cost_r_fallback_is_authority"),
        "package_replay_executable_candidate_use_allowed": row.get("package_replay_executable_candidate_use_allowed"),
        "package_replay_executable_candidate_use_allowed_reason": row.get(
            "package_replay_executable_candidate_use_allowed_reason"
        ),
    }


def sample_refused_rows(
    candidate_ledger: Path,
    *,
    sample_per_cell: int,
) -> tuple[dict[tuple[str, str, str], list[dict[str, Any]]], Counter[str]]:
    samples: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    counts: Counter[str] = Counter()
    for row in iter_jsonl(candidate_ledger):
        counts["candidate_rows"] += 1
        if not cost_refused(row):
            continue
        counts["refused_candidate_rows"] += 1
        for reason in pretrade_cost_refusal_reasons(row):
            key = cell_key(row, reason)
            counts["refusal_reason_instances"] += 1
            counts[f"cell::{json.dumps(key, separators=(',', ':'))}"] += 1
            if len(samples[key]) < sample_per_cell:
                samples[key].append(compact_sample(row, reason))
    return samples, counts


def manifest_files_by_symbol(manifest_path: Path) -> dict[str, dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = Path(manifest.get("output_dir") or manifest_path.parent)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    files = {}
    for meta in mapping(manifest.get("files")).values():
        if not isinstance(meta, Mapping):
            continue
        symbol = str(first_present(meta.get("file_symbol"), meta.get("symbol")) or "")
        path_text = meta.get("path")
        if not symbol or not path_text:
            continue
        path = Path(str(path_text))
        if not path.is_absolute():
            path = REPO_ROOT / path
        files[symbol] = {
            "path": path,
            "sha256": meta.get("sha256"),
            "first": meta.get("first"),
            "last": meta.get("last"),
            "row_count": meta.get("row_count") or meta.get("rows"),
            "source_truth_scope": meta.get("source_truth_scope"),
            "source_broker": meta.get("source_broker"),
            "source_role": meta.get("source_role"),
        }
    return files


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_tick_evidence(
    samples_by_cell: Mapping[tuple[str, str, str], list[dict[str, Any]]],
    manifest_path: Path,
    *,
    lookback_minutes: float,
    validate_sha: bool,
) -> dict[str, dict[str, Any]]:
    files = manifest_files_by_symbol(manifest_path)
    needed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rows in samples_by_cell.values():
        for sample in rows:
            symbol = str(sample.get("symbol") or "")
            asof = parse_dt(sample.get("decision_time_utc"))
            if symbol and asof is not None:
                needed[symbol].append({"asof": asof, "sample": sample})
    output: dict[str, dict[str, Any]] = {}
    for symbol, requests in needed.items():
        requests.sort(key=lambda item: item["asof"])
        meta = files.get(symbol)
        if not meta:
            for request in requests:
                output[_sample_id(request["sample"])] = {
                    "tick_status": "missing_symbol_tick_manifest",
                    "manifest_symbol_present": False,
                }
            continue
        path = Path(meta["path"])
        sha_status = "not_checked"
        if validate_sha and path.exists() and meta.get("sha256"):
            sha_status = "matched" if file_sha256(path) == meta.get("sha256") else "mismatch"
        req_idx = 0
        recent: list[dict[str, Any]] = []
        max_lookback = timedelta(minutes=max(1.0, lookback_minutes))
        if not path.exists():
            for request in requests:
                output[_sample_id(request["sample"])] = {
                    "tick_status": "tick_file_missing",
                    "manifest_symbol_present": True,
                    "tick_path": str(path),
                    "tick_sha256_status": sha_status,
                }
            continue
        for tick in iter_jsonl(path):
            tick_time = parse_dt(first_present(tick.get("ts_utc"), tick.get("time_utc"), tick.get("time")))
            if tick_time is None:
                continue
            recent.append({"time": tick_time, "row": tick})
            while recent and tick_time - recent[0]["time"] > max_lookback:
                recent.pop(0)
            while req_idx < len(requests) and requests[req_idx]["asof"] <= tick_time:
                request = requests[req_idx]
                asof = request["asof"]
                candidate_ticks = [item for item in recent if item["time"] <= asof]
                selected = candidate_ticks[-1] if candidate_ticks else None
                output[_sample_id(request["sample"])] = tick_evidence_from_selected_tick(
                    request["sample"],
                    selected,
                    meta=meta,
                    tick_path=path,
                    sha_status=sha_status,
                )
                req_idx += 1
        while req_idx < len(requests):
            request = requests[req_idx]
            asof = request["asof"]
            candidate_ticks = [item for item in recent if item["time"] <= asof and asof - item["time"] <= max_lookback]
            selected = candidate_ticks[-1] if candidate_ticks else None
            output[_sample_id(request["sample"])] = tick_evidence_from_selected_tick(
                request["sample"],
                selected,
                meta=meta,
                tick_path=path,
                sha_status=sha_status,
            )
            req_idx += 1
    return output


def _sample_id(sample: Mapping[str, Any]) -> str:
    return "::".join(
        str(first_present(sample.get(key), ""))
        for key in ("candidate_id", "decision_time_utc", "reason_family")
    )


def tick_evidence_from_selected_tick(
    sample: Mapping[str, Any],
    selected: Mapping[str, Any] | None,
    *,
    meta: Mapping[str, Any],
    tick_path: Path,
    sha_status: str,
) -> dict[str, Any]:
    if not selected:
        return {
            "tick_status": "no_predecision_tick_in_lookback",
            "manifest_symbol_present": True,
            "tick_path": str(tick_path),
            "tick_sha256_status": sha_status,
            "manifest_first": meta.get("first"),
            "manifest_last": meta.get("last"),
        }
    row = mapping(selected.get("row"))
    bid = safe_float(row.get("bid"), 0.0) or 0.0
    ask = safe_float(row.get("ask"), 0.0) or 0.0
    entry = safe_float(sample.get("entry_price"))
    stop = safe_float(sample.get("stop_loss"))
    risk = abs(entry - stop) if entry is not None and stop is not None else None
    raw_spread_r = ((ask - bid) / risk) if risk and risk > 0 and ask >= bid and bid > 0 else None
    symbol = str(sample.get("symbol") or "")
    floor_r = safe_float(TICK_SPREAD_FLOOR_R.get(symbol))
    enforced_spread_r = raw_spread_r
    floor_enforced = False
    if floor_r is not None and (enforced_spread_r is None or enforced_spread_r < floor_r):
        enforced_spread_r = floor_r
        floor_enforced = True
    return {
        "tick_status": "historical_tick_found",
        "manifest_symbol_present": True,
        "tick_path": str(tick_path),
        "tick_sha256_status": sha_status,
        "tick_time_utc": selected["time"].isoformat(),
        "bid": bid,
        "ask": ask,
        "stop_distance": risk,
        "raw_tick_spread_r": raw_spread_r,
        "measured_tick_spread_floor_r": floor_r,
        "floor_enforced": floor_enforced,
        "recomputed_spread_r": enforced_spread_r,
        "manifest_first": meta.get("first"),
        "manifest_last": meta.get("last"),
        "source_truth_scope": meta.get("source_truth_scope"),
    }


def classify_sample(sample: Mapping[str, Any], tick: Mapping[str, Any]) -> dict[str, Any]:
    reasons = listish(sample.get("all_reasons")) or [sample.get("reason")]
    spread_limit = DEFAULT_MAX_SPREAD_R
    total_limit = DEFAULT_MAX_TOTAL_COST_R
    for reason in reasons:
        family = normalize_refusal_family(reason)
        if family == "spread_r_exceeds_selected_cell_limit":
            spread_limit = parse_limit(str(reason), spread_limit) or spread_limit
        if family == "total_cost_r_exceeds_limit":
            total_limit = parse_limit(str(reason), total_limit) or total_limit
    spread_r = safe_float(tick.get("recomputed_spread_r"))
    slippage_r = safe_float(sample.get("expected_slippage_r"), 0.02) or 0.0
    swap_r = safe_float(sample.get("swap_cost_r"), 0.0) or 0.0
    recomputed_total_r = None if spread_r is None else spread_r + slippage_r + swap_r
    original_cost_r = safe_float(sample.get("expected_cost_r"))
    original_spread_r = safe_float(sample.get("spread_r"))
    recomputed_reasons: list[str] = []
    if spread_r is None:
        recomputed_reasons.append("missing_recomputed_spread_r")
    elif spread_r > spread_limit + 1e-9:
        recomputed_reasons.append(
            f"spread_r_exceeds_selected_cell_limit:{spread_r:.6f}>{spread_limit:.6f}"
        )
    if recomputed_total_r is not None and recomputed_total_r > total_limit + 1e-9:
        recomputed_reasons.append(f"total_cost_r_exceeds_limit:{recomputed_total_r:.6f}>{total_limit:.6f}")
    if tick.get("tick_status") != "historical_tick_found":
        classification = "source_gap_needs_tick_capture_or_manifest_mapping"
    elif not recomputed_reasons:
        classification = "mapping_bug_or_stale_floor_original_refused_but_measured_tick_passes"
    elif original_cost_r is not None and recomputed_total_r is not None and abs(original_cost_r - recomputed_total_r) <= 0.02:
        classification = "honest_refusal_measured_tick_matches_original_cost"
    elif original_spread_r is not None and spread_r is not None and abs(original_spread_r - spread_r) <= 0.02:
        classification = "honest_refusal_measured_tick_matches_original_spread"
    else:
        classification = "honest_refusal_with_cost_delta_requires_metadata_review"
    return {
        "classification": classification,
        "recomputed_refusal_reasons": recomputed_reasons,
        "recomputed_spread_r": spread_r,
        "recomputed_total_cost_r": recomputed_total_r,
        "spread_limit_r": spread_limit,
        "total_cost_limit_r": total_limit,
        "original_expected_cost_r": original_cost_r,
        "original_spread_r": original_spread_r,
        "old_proxy_vs_broker_calibrated_delta_r": safe_float(
            sample.get("old_proxy_vs_broker_calibrated_delta_r")
        ),
    }


def build_audit(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidate_ledger = Path(args.candidate_ledger) if args.candidate_ledger else ROUTE_DIR / f"{args.prefix}_CANDIDATE_LEDGER.jsonl"
    tick_manifest = Path(args.tick_manifest)
    samples_by_cell, counts = sample_refused_rows(candidate_ledger, sample_per_cell=args.sample_per_cell)
    tick_evidence = build_tick_evidence(
        samples_by_cell,
        tick_manifest,
        lookback_minutes=args.lookback_minutes,
        validate_sha=args.validate_tick_sha,
    )
    classification_rows: list[dict[str, Any]] = []
    cell_summary: dict[tuple[str, str, str], dict[str, Any]] = {}
    for key, samples in samples_by_cell.items():
        summary = {
            "symbol": key[0],
            "session": key[1],
            "refusal_reason_family": key[2],
            "sampled_rows": 0,
            "observed_cell_count": counts.get(f"cell::{json.dumps(key, separators=(',', ':'))}", 0),
            "classification_counts": Counter(),
            "tick_status_counts": Counter(),
            "recomputed_refusal_reason_counts": Counter(),
        }
        for sample in samples:
            tick = tick_evidence.get(_sample_id(sample), {"tick_status": "tick_lookup_not_run"})
            classification = classify_sample(sample, tick)
            row = {**sample, **tick, **classification}
            classification_rows.append(row)
            summary["sampled_rows"] += 1
            summary["classification_counts"][classification["classification"]] += 1
            summary["tick_status_counts"][tick.get("tick_status")] += 1
            for reason in classification["recomputed_refusal_reasons"]:
                summary["recomputed_refusal_reason_counts"][reason.split(":", 1)[0]] += 1
        summary["classification_counts"] = dict(summary["classification_counts"].most_common())
        summary["tick_status_counts"] = dict(summary["tick_status_counts"].most_common())
        summary["recomputed_refusal_reason_counts"] = dict(
            summary["recomputed_refusal_reason_counts"].most_common()
        )
        summary["cell_classification"] = cell_classification(summary["classification_counts"])
        cell_summary[key] = summary
    output_summary = {
        "schema": "gtos.final_moonshot.b6_broker_cost_calibration_audit.v1",
        "generated_utc": utc_now(),
        "status": "b6_broker_cost_calibration_audit_materialized",
        "broker_live_authority": False,
        "final_selection_claim": False,
        "prefix": args.prefix,
        "candidate_ledger": str(candidate_ledger),
        "tick_manifest": str(tick_manifest),
        "tick_truth_boundary": "ordered_price_path_only_not_broker_order_lifecycle_truth",
        "sample_per_cell": args.sample_per_cell,
        "lookback_minutes": args.lookback_minutes,
        "candidate_rows": counts.get("candidate_rows", 0),
        "refused_candidate_rows": counts.get("refused_candidate_rows", 0),
        "refusal_reason_instances": counts.get("refusal_reason_instances", 0),
        "cell_count": len(cell_summary),
        "sampled_rows": len(classification_rows),
        "classification_counts": dict(Counter(row["classification"] for row in classification_rows).most_common()),
        "tick_status_counts": dict(Counter(row.get("tick_status") for row in classification_rows).most_common()),
        "cell_classification_counts": dict(
            Counter(row["cell_classification"] for row in cell_summary.values()).most_common()
        ),
        "cells": sorted(cell_summary.values(), key=lambda row: (-row["observed_cell_count"], row["symbol"], row["session"], row["refusal_reason_family"])),
        "acceptance_interpretation": {
            "honest_refusal": "do not loosen REFUSED; current measured tick/source evidence still violates cost limits",
            "mapping_bug_or_stale_floor_original_refused_but_measured_tick_passes": "implementation/config repair required before any replay release",
            "source_gap_needs_tick_capture_or_manifest_mapping": "hydrate or map tick source before promoting any cost decision",
            "metadata_review": "cost remains refused but source/provenance fields need repair before B6 proof can close",
        },
    }
    return output_summary, classification_rows


def cell_classification(class_counts: Mapping[str, int]) -> str:
    if not class_counts:
        return "no_samples"
    if class_counts.get("mapping_bug_or_stale_floor_original_refused_but_measured_tick_passes"):
        return "mapping_bug_or_stale_floor"
    if class_counts.get("source_gap_needs_tick_capture_or_manifest_mapping"):
        return "source_gap_needs_tick_capture_or_manifest_mapping"
    if class_counts.get("honest_refusal_with_cost_delta_requires_metadata_review"):
        return "honest_refusal_with_metadata_review"
    if (
        class_counts.get("honest_refusal_measured_tick_matches_original_cost")
        or class_counts.get("honest_refusal_measured_tick_matches_original_spread")
    ):
        return "honest_refusal"
    return sorted(class_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def write_outputs(summary: Mapping[str, Any], rows: list[dict[str, Any]], output_dir: Path, tag: str) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"BROKER_COST_CALIBRATION_AUDIT_{tag}.json"
    row_path = output_dir / f"BROKER_COST_CALIBRATION_AUDIT_{tag}_SAMPLED_ROWS.jsonl"
    cell_path = output_dir / f"BROKER_COST_CALIBRATION_AUDIT_{tag}_CLASSIFICATION_LEDGER.jsonl"
    summary_with_artifacts = dict(summary)
    summary_with_artifacts["artifacts"] = {
        "summary": str(summary_path),
        "sampled_rows": str(row_path),
        "classification_ledger": str(cell_path),
    }
    summary_path.write_text(json.dumps(summary_with_artifacts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with row_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with cell_path.open("w", encoding="utf-8") as handle:
        for cell in summary["cells"]:
            handle.write(json.dumps(cell, sort_keys=True) + "\n")
    return summary_with_artifacts["artifacts"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--candidate-ledger", default=None)
    parser.add_argument("--tick-manifest", default=str(DEFAULT_TICK_MANIFEST))
    parser.add_argument("--artifact-tag", default="V123_B6_BROKER_COST_CALIBRATION_AUDIT")
    parser.add_argument("--output-dir", default=str(ROUTE_DIR))
    parser.add_argument("--sample-per-cell", type=int, default=DEFAULT_SAMPLE_PER_CELL)
    parser.add_argument("--lookback-minutes", type=float, default=DEFAULT_LOOKBACK_MINUTES)
    parser.add_argument("--validate-tick-sha", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary, rows = build_audit(args)
    artifacts = write_outputs(summary, rows, Path(args.output_dir), args.artifact_tag)
    print(json.dumps({"status": summary["status"], "artifacts": artifacts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
