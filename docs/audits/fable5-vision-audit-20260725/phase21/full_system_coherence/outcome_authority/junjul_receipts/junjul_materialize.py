#!/usr/bin/env python3
"""T3/T4 — materialize june_2026 + july_2026 lane windows into the LANE hold.

Additive-only, fail-closed, ZERO outcome reads. Mirrors origin/main's
`lane_rematerialization.materialize_lane_window_sources` (Session LM-MAT's
extension producer) with exactly two parameterizations, both forced by the fact
that this is the first window pair whose static D1/H4/M15 authorities must come
from a NEW capture (the existing static families end 2026-06-10/2026-06-16):

  P1  D1/H4/M15 are freshly converted from the verified VPS export
      (`junjul_2026_lane_source_20260811`, commit e38ace15c...) through the
      module's own `_transform_bar_file`, instead of being reused by reference
      from the catalog's static families. Coverage is asserted per timeframe
      with the producer's own thresholds, except D1's tail: the producer's
      `end_exclusive - 1 day` bar-OPEN proxy demands a D1 bar opening on the
      window's final calendar day, which no summer month-final series can
      satisfy (the bar COVERING broker Friday 2026-07-31 opens 2026-07-30T21:00Z).
      D1 uses `end_exclusive - 1 day - 3 h` (the exact summer broker offset),
      i.e. "a D1 bar covering the final trading day exists".

  P2  M1 is month-cut to the producer's own per-month family convention
      (`bridge_ftmo_m1_202606` / `bridge_ftmo_m1_202607`, the names the engine
      derives from a day's month). Conversion is the module's, verbatim, over
      the full export file; the cut is a pure row filter at the broker-month
      bounds on the CONVERTED rows (conversion is monotone, so this equals
      cutting raw rows at broker month boundaries — the raw capture convention
      every existing `bridge_ftmo_m1_*` family embodies). `source_sha256` stays
      the RAW export file hash, so provenance binds to the VPS manifest.

Everything else — manifest assembly, `manifest_root_sha256`, tick-gap
disclosure via `_tick_capture_span`, the locked registry transaction, the
pre-existing-window invariance assertion, and the SOURCES receipt — is the
module's own code or its exact recipe.
"""
import csv
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

RT = Path("/tmp/junjul-lane-mat-20260810/rt-wt")
sys.path.insert(0, str(RT))
from src.research_infra import lane_rematerialization as lane  # noqa: E402
from src.research_infra import (  # noqa: E402
    v4_timewarp_simulated_live_research_loop as timewarp,
)

HOLD = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
REGISTRY = HOLD / "LANE_INPUT_REGISTRY.json"
EXPORT = Path("/tmp/junjul-lane-mat-20260810/export/junjul_2026_lane_source_20260811")
EXPORT_COMMIT = "e38ace15c1de5844c28da44b06ec3f45008458aa"
STATIC_FAMILY = "junjul_2026_lane_source_20260811"
SCRATCH = Path("/tmp/junjul-lane-mat-20260810/scratch")
BACKUP = SCRATCH / "LANE_INPUT_REGISTRY.pre-junjul.backup.json"
RESULT = SCRATCH / "T3_T4_RESULT.json"

NEW_WINDOWS = {
    "june_2026": lane.WindowSpec(
        "june_2026", "2026-06-01", "2026-06-30", "lane_validation", "202606"
    ),
    "july_2026": lane.WindowSpec(
        "july_2026", "2026-07-01", "2026-07-31", "lane_validation", "202607"
    ),
}

SUMMER_BROKER_OFFSET_H = 3  # broker = America/New_York + 7 = UTC+3 in US DST


def fatal(msg: str) -> None:
    raise SystemExit(f"FATAL: {msg}")


def main() -> None:
    started = time.perf_counter()
    if not REGISTRY.is_file():
        fatal(f"registry missing: {REGISTRY}")
    if not EXPORT.is_dir():
        fatal(f"export missing: {EXPORT}")

    # ---- backup + preconditions --------------------------------------------
    pre_bytes = REGISTRY.read_bytes()
    BACKUP.write_bytes(pre_bytes)
    pre_sha = hashlib.sha256(pre_bytes).hexdigest()
    print(f"registry backup -> {BACKUP} (sha256 {pre_sha})")

    payload = json.loads(pre_bytes)
    if payload.get("registry_root_sha256") != lane._manifest_root(
        payload, "registry_root_sha256"
    ):
        fatal("lane_input_registry_invalid at start")
    prior = dict(payload.get("windows") or {})
    for wid in NEW_WINDOWS:
        if wid in prior:
            fatal(f"lane_window_already_registered:{wid}")
        if (HOLD / "manifests" / f"{wid}.json").exists():
            fatal(f"manifest already exists for {wid}")

    # extend the naming table (runtime only; WINDOWS "is a naming table, and
    # every fuse (blackout, surface, registry) is independent of it")
    lane.WINDOWS.update(NEW_WINDOWS)

    # verify export bytes against the VPS manifest once more, in this process
    vps_manifest = json.loads((EXPORT / "manifest.json").read_text())
    files_meta = vps_manifest["files"]
    if len(files_meta) != 96:
        fatal(f"export manifest expected 96 files, has {len(files_meta)}")
    raw_sha: dict[tuple[str, str], str] = {}
    for key, row in files_meta.items():
        p = EXPORT / f"{key}.csv"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h != row["sha256"]:
            fatal(f"export sha mismatch for {key}: {h} != {row['sha256']}")
        raw_sha[(row["file_symbol"], row["timeframe"])] = h
    print("export re-verified: 96/96 sha256 OK against VPS manifest")

    # logical root exactly as the producer recovers it
    ref_manifest = json.loads(
        lane._safe_relative(HOLD, str(prior["january_2026"]["source_manifest"]))
        .read_text(encoding="utf-8")
    )
    logical_root = lane._logical_repo_root_for_registry(
        registry_path=REGISTRY, manifest=ref_manifest
    )
    print("logical repo root:", logical_root)

    symbols = tuple(timewarp.GTOS_24_SYMBOL_SURFACE)
    assert len(symbols) == 24

    # ---- P1: static D1/H4/M15 conversion (module transform, verbatim) -----
    static_rows: dict[tuple[str, str], dict] = {}
    for symbol in symbols:
        for timeframe in ("D1", "H4", "M15"):
            source, mapped = lane._find_bar_source(EXPORT, symbol, timeframe)
            if raw_sha.get((symbol, timeframe)) != lane._file_sha256(source):
                fatal(f"raw sha inconsistency {symbol} {timeframe}")
            destination = (
                HOLD / "sources/bars" / STATIC_FAMILY / f"{mapped}_{timeframe}.csv"
            )
            if destination.exists() or destination.is_symlink():
                fatal(f"lane_extension_bar_exists:{destination}")
            row = lane._transform_bar_file(
                source=source,
                destination=destination,
                symbol=symbol,
                mapped_symbol=mapped,
                timeframe=timeframe,
                source_family=STATIC_FAMILY,
                lane_root=HOLD,
                repo_root=logical_root,
            )
            static_rows[(symbol, timeframe)] = row
    print(f"static conversion done: {len(static_rows)} files under {STATIC_FAMILY}")

    # ---- P2: M1 month-cut families -----------------------------------------
    m1_rows_by_window: dict[str, list[dict]] = {}
    m1_scratch = SCRATCH / "m1_full_converted"
    m1_scratch.mkdir(parents=True, exist_ok=True)
    month_bounds = {
        "202606": (
            lane._parse_broker_bar_time("2026-06-01 00:00:00"),
            lane._parse_broker_bar_time("2026-07-01 00:00:00"),
        ),
        "202607": (
            lane._parse_broker_bar_time("2026-07-01 00:00:00"),
            lane._parse_broker_bar_time("2026-08-01 00:00:00"),
        ),
    }
    full_m1_cache: dict[str, tuple[Path, dict]] = {}
    for symbol in symbols:
        source, mapped = lane._find_bar_source(EXPORT, symbol, "M1")
        scratch_dest = m1_scratch / f"{mapped}_M1.csv"
        lane._transform_bar_file(
            source=source,
            destination=scratch_dest,
            symbol=symbol,
            mapped_symbol=mapped,
            timeframe="M1",
            source_family="__scratch_full__",
            lane_root=m1_scratch,
            repo_root=m1_scratch,
        )
        full_m1_cache[symbol] = (scratch_dest, {"mapped": mapped, "source": source})

    for wid, window in NEW_WINDOWS.items():
        family = f"bridge_ftmo_m1_{window.month}"
        lo, hi = month_bounds[window.month]
        rows: list[dict] = []
        for symbol in symbols:
            scratch_dest, meta = full_m1_cache[symbol]
            mapped = meta["mapped"]
            source = meta["source"]
            destination = HOLD / "sources/bars" / family / f"{mapped}_M1.csv"
            if destination.exists() or destination.is_symlink():
                fatal(f"lane_extension_bar_exists:{destination}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            row_count = 0
            first_utc = None
            last_utc = None
            with scratch_dest.open("r", newline="", encoding="utf-8") as src:
                reader = csv.DictReader(src)
                fieldnames = list(reader.fieldnames)
                with destination.open("w", newline="", encoding="utf-8") as dst:
                    writer = csv.DictWriter(dst, fieldnames=fieldnames)
                    writer.writeheader()
                    for raw in reader:
                        t = datetime.fromisoformat(raw["time"])
                        if not (lo <= t < hi):
                            continue
                        writer.writerow(raw)
                        row_count += 1
                        first_utc = first_utc or raw["time"]
                        last_utc = raw["time"]
                    dst.flush()
                    import os as _os
                    _os.fsync(dst.fileno())
            if row_count <= 0:
                fatal(f"m1_month_cut_empty:{wid}:{symbol}")
            rows.append(
                {
                    "symbol": symbol,
                    "mapped_symbol": mapped,
                    "timeframe": "M1",
                    "source_family": family,
                    "lane_relpath": destination.relative_to(HOLD).as_posix(),
                    "repo_relpath": lane._repo_relative(
                        destination, repo_root=logical_root
                    ),
                    "row_count": row_count,
                    "first_utc": first_utc,
                    "last_utc": last_utc,
                    "source_snapshot_name": source.parent.name,
                    "source_file_name": source.name,
                    "source_sha256": raw_sha[(symbol, "M1")],
                    "sha256": lane._file_sha256(destination),
                    "time_column_basis": "true_utc",
                    "clock_conversion": "broker_epoch_to_utc",
                    "broker_clock_rule": lane.NEW_YORK_PLUS_7.name,
                    "economic_columns_rewritten": [],
                }
            )
        m1_rows_by_window[wid] = rows
        print(f"M1 month-cut done for {wid}: {len(rows)} files under {family}")

    # ---- coverage assertions (producer thresholds; D1 tail documented) -----
    coverage_report: dict[str, dict] = {}
    for wid, window in NEW_WINDOWS.items():
        cov: dict[str, dict] = {}
        for timeframe in ("D1", "H4", "M15"):
            firsts = [
                str(static_rows[(s, timeframe)]["first_utc"]) for s in symbols
            ]
            lasts = [
                str(static_rows[(s, timeframe)]["last_utc"]) for s in symbols
            ]
            cov[timeframe] = {
                "max_first_utc": max(firsts),
                "min_last_utc": min(lasts),
                "symbol_count": len(firsts),
            }
            if datetime.fromisoformat(max(firsts)) > window.start_utc:
                fatal(
                    f"lane_static_coverage_starts_after_window:{wid}:{timeframe}:{max(firsts)}"
                )
            threshold = window.end_exclusive_utc - timedelta(days=1)
            if timeframe == "D1":
                threshold -= timedelta(hours=SUMMER_BROKER_OFFSET_H)
            if datetime.fromisoformat(min(lasts)) < threshold:
                fatal(
                    f"lane_static_coverage_ends_before_window:{wid}:{timeframe}:{min(lasts)}"
                )
        m1_firsts = [str(r["first_utc"]) for r in m1_rows_by_window[wid]]
        m1_lasts = [str(r["last_utc"]) for r in m1_rows_by_window[wid]]
        cov["M1"] = {
            "max_first_utc": max(m1_firsts),
            "min_last_utc": min(m1_lasts),
            "symbol_count": len(m1_firsts),
        }
        # NOTE deliberately NO M1 start-side coverage check: the producer has
        # none (only D1/H4/M15 statics are coverage-checked), and its accepted
        # estate contains the same shape — may_2026's GER40 M1 first_utc is
        # 2026-05-04T00:16 (3 days after window start) and october_2025's
        # UKOIL_cash starts 2025-10-01T00:05. Session-scaled per-day floors
        # govern M1 sufficiency at resolve time.
        if datetime.fromisoformat(min(m1_lasts)) < window.end_exclusive_utc - timedelta(days=1):
            fatal(f"m1_coverage_ends_before_window:{wid}:{min(m1_lasts)}")
        coverage_report[wid] = cov
        print(f"coverage OK for {wid}: " + json.dumps(cov))

    # ---- tick gap status (producer's capture-span logic, verbatim) ---------
    capture_span = lane._tick_capture_span(lane.DEFAULT_TICK_ROOT)
    tick_status_by_window: dict[str, str] = {}
    for wid, window in NEW_WINDOWS.items():
        if capture_span is None:
            status = "captured_tick_archive_coverage_undeclared"
        elif window.end_exclusive_utc <= capture_span[0]:
            status = "captured_tick_archive_begins_after_window"
        elif window.start_utc >= capture_span[1]:
            status = "captured_tick_archive_ends_before_window"
        else:
            fatal(
                f"tick capture span {capture_span} INTERSECTS {wid}; "
                "this driver deliberately does not materialize ticks - STOP"
            )
        tick_status_by_window[wid] = status
    print("tick capture span:", capture_span, "| statuses:", tick_status_by_window)

    # ---- manifests + locked registry transaction (producer recipe) ---------
    results: dict[str, dict] = {}
    for wid, window in NEW_WINDOWS.items():
        bars = [
            *(static_rows[(s, tf)] for s in symbols for tf in ("D1", "H4", "M15")),
            *m1_rows_by_window[wid],
        ]
        if len(bars) != 96:
            fatal(f"expected 96 bar rows for {wid}, got {len(bars)}")
        manifest = lane._source_manifest(
            lane_root=HOLD,
            window=window,
            bars=bars,
            ticks=[],
            repo_root=logical_root,
            tick_gap_status=tick_status_by_window[wid],
        )
        if manifest["bar_source_count"] != 96 or manifest["bar_symbol_count"] != 24:
            fatal(f"manifest counts wrong for {wid}")
        if manifest["tick_symbol_count"] != 0 or manifest["tick_gap_count"] != 24:
            fatal(f"manifest tick disclosure wrong for {wid}")
        manifest_rel = Path("manifests") / f"{wid}.json"
        manifest_path = HOLD / manifest_rel
        if manifest_path.exists() or manifest_path.is_symlink():
            fatal(f"lane_extension_manifest_exists:{manifest_path}")
        lane._write_json(manifest_path, manifest)

        with lane._registry_write_lock(REGISTRY):
            current = json.loads(REGISTRY.read_text(encoding="utf-8"))
            if current.get("registry_root_sha256") != lane._manifest_root(
                current, "registry_root_sha256"
            ):
                fatal("lane_input_registry_invalid inside lock")
            core = dict(current)
            core.pop("registry_root_sha256", None)
            before = {k: dict(v) for k, v in core["windows"].items()}
            if wid in before:
                fatal(f"lane_window_already_registered:{wid}")
            raced = sorted(set(before) - set(lane.WINDOWS))
            if raced:
                fatal(f"lane_registry_window_unknown:{raced}")
            windows = {k: dict(v) for k, v in before.items()}
            windows[wid] = {
                "window": [window.start, window.end],
                "split": window.split,
                "surface": "VAL",
                "source_manifest": manifest_rel.as_posix(),
                "source_manifest_root_sha256": manifest["manifest_root_sha256"],
                "pack_root": (Path("packs") / wid).as_posix(),
                "pack_roots": {},
                "pack_status": "NOT_BUILT",
                "campaign_sealed": False,
            }
            core["windows"] = windows
            core["status"] = "LANE_TRUE_UTC_INPUT_REGISTRY_SOURCE_READY"
            updated = {**core, "registry_root_sha256": lane._stable_sha256(core)}
            lane._write_json(REGISTRY, updated)

        unchanged = {k: (updated["windows"][k] == before[k]) for k in before}
        if not all(unchanged.values()):
            fatal(
                "lane_pre_existing_windows_mutated:"
                f"{sorted(k for k, v in unchanged.items() if not v)}"
            )

        receipt_core = {
            "schema": lane.MATERIALIZATION_SCHEMA,
            "status": "LANE_TRUE_UTC_WINDOW_SOURCE_EXTENSION_COMPLETE",
            "campaign_sealed": False,
            "evidence_class": lane.LANE_EVIDENCE,
            "window_id": wid,
            "window": [window.start, window.end],
            "surface": "VAL",
            "day_count": len(window.days),
            "lane_root_repo_relpath": lane._repo_relative(
                HOLD, repo_root=logical_root
            ),
            "logical_source_repo_root": str(logical_root),
            "registry_root_sha256": updated["registry_root_sha256"],
            "source_manifest_root_sha256": manifest["manifest_root_sha256"],
            "static_bar_family": STATIC_FAMILY,
            "static_bar_family_export_commit": EXPORT_COMMIT,
            "static_bar_source_count": 72,
            "m1_source_family": f"bridge_ftmo_m1_{window.month}",
            "m1_source_count": len(m1_rows_by_window[wid]),
            "m1_row_count": sum(int(r["row_count"]) for r in m1_rows_by_window[wid]),
            "m1_month_cut_from_export": True,
            "static_bar_coverage": coverage_report[wid],
            "tick_source_count": 0,
            "tick_row_count": 0,
            "tick_gap_count": int(manifest["tick_gap_count"]),
            "tick_gap_status": tick_status_by_window[wid],
            "captured_tick_archive_span": (
                [capture_span[0].isoformat(), capture_span[1].isoformat()]
                if capture_span is not None
                else None
            ),
            "bar_symbol_count": int(manifest["bar_symbol_count"]),
            "pre_existing_window_entries_unchanged": unchanged,
            "pre_existing_source_manifest_root_sha256": {
                k: before[k]["source_manifest_root_sha256"] for k in before
            },
            "d1_tail_coverage_rule": (
                "producer threshold end_exclusive-1d demands a D1 bar OPENING on the "
                "final calendar day; the bar COVERING broker Friday 2026-07-31 opens "
                "2026-07-30T21:00Z (summer broker offset +3h), so D1 uses "
                "end_exclusive-1d-3h. All other timeframes use the producer threshold "
                "verbatim."
            ),
            "clock_conversion": "src.utils.broker_clock.broker_epoch_to_utc",
            "broker_clock_rule": lane.NEW_YORK_PLUS_7.name,
            "economic_outcomes_read": False,
            "march_outcomes_read": False,
            "outcome_summary_statistics_computed": False,
            "broker_live_authority": False,
            "broker_mutation_enabled": False,
            "wall_seconds": round(time.perf_counter() - started, 3),
        }
        receipt = {
            **receipt_core,
            "receipt_root_sha256": lane._stable_sha256(receipt_core),
        }
        lane._write_json(HOLD / "receipts" / f"SOURCES_{wid}.json", receipt)
        results[wid] = {
            "manifest_root_sha256": manifest["manifest_root_sha256"],
            "registry_root_sha256_after": updated["registry_root_sha256"],
            "m1_row_count": receipt["m1_row_count"],
            "tick_gap_status": tick_status_by_window[wid],
            "receipt": str(HOLD / "receipts" / f"SOURCES_{wid}.json"),
        }
        print(f"REGISTERED {wid}: manifest_root_sha256={manifest['manifest_root_sha256']}")

    # ---- final invariance proof vs the pre-run backup ----------------------
    final = json.loads(REGISTRY.read_text(encoding="utf-8"))
    backup = json.loads(BACKUP.read_text(encoding="utf-8"))
    diffs = []
    for k, v in backup["windows"].items():
        if final["windows"].get(k) != v:
            diffs.append(k)
    if diffs:
        fatal(f"pre-existing window entries changed: {diffs}")
    top_changed = {
        k
        for k in set(backup) | set(final)
        if backup.get(k) != final.get(k)
    }
    expected_changed = {"windows", "status", "registry_root_sha256"}
    if not top_changed <= expected_changed:
        fatal(f"unexpected top-level registry changes: {top_changed - expected_changed}")
    if final.get("registry_root_sha256") != lane._manifest_root(
        final, "registry_root_sha256"
    ):
        fatal("registry root hash invalid after update")
    new_ids = sorted(set(final["windows"]) - set(backup["windows"]))
    if new_ids != ["july_2026", "june_2026"] and new_ids != ["june_2026", "july_2026"]:
        fatal(f"unexpected new window set: {new_ids}")
    post_sha = hashlib.sha256(REGISTRY.read_bytes()).hexdigest()
    summary = {
        "verdict": "MATERIALIZED_AND_REGISTERED",
        "export_commit": EXPORT_COMMIT,
        "registry_file_sha256_before": pre_sha,
        "registry_file_sha256_after": post_sha,
        "registry_status_before": backup.get("status"),
        "registry_status_after": final.get("status"),
        "pre_existing_windows_byte_identical": True,
        "top_level_changes": sorted(top_changed),
        "windows": results,
    }
    RESULT.write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
