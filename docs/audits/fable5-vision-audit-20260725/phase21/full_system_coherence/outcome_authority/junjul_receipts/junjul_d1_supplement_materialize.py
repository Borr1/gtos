#!/usr/bin/env python3
"""D1 lead-in supplement materializer (june_2026 only) — executed 2026-08-11.

Verbatim record of the driver run against the LANE_INPUTS_TRUE_UTC_V1 hold from
a sparse origin/main (eed6c496b) worktree. See
JUNJUL_D1_SUPPLEMENT_MATERIALIZATION_V1.md for the receipt; the pre-write
cross-check lives in t2-style sibling D1_SUPP_XCHECK.json (driver for it in the
receipt's section 2).
"""
import hashlib, json, sys, time
from pathlib import Path
sys.path.insert(0, '.')
from src.research_infra import lane_rematerialization as lane

HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1")
REGISTRY = HOLD / "LANE_INPUT_REGISTRY.json"
LEADIN = Path("/tmp/junjul-lane-mat-20260810/export/junjul_2026_d1_leadin_20260811")
SCR = Path("/tmp/junjul-lane-mat-20260810/scratch")
FAMILY = "junjul_2026_d1_leadin_20260811"
COMMIT = "3725c30a6aa2f3abf4ea23317a34d857fedcb797"
started = time.perf_counter()

def fatal(m): raise SystemExit("FATAL: "+m)

famdir = HOLD/"sources/bars"/FAMILY
if famdir.exists(): fatal(f"family dir exists: {famdir}")

reg_before_bytes = REGISTRY.read_bytes()
(SCR/"LANE_INPUT_REGISTRY.pre-d1supp.backup.json").write_bytes(reg_before_bytes)
jm_before_bytes = (HOLD/"manifests/june_2026.json").read_bytes()
(SCR/"june_2026.pre-d1supp.backup.json").write_bytes(jm_before_bytes)
reg_before_sha = hashlib.sha256(reg_before_bytes).hexdigest()
print("backups taken; registry before:", reg_before_sha)

reg = json.loads(reg_before_bytes)
if reg.get("registry_root_sha256") != lane._manifest_root(reg, "registry_root_sha256"):
    fatal("registry invalid at start")
old_manifest = json.loads(jm_before_bytes)
if old_manifest["manifest_root_sha256"] != "7498a9d5fe18435c352f6b64cdac1109a79ea875a415f274ff9964655fdf2248":
    fatal("june manifest root moved since main run - re-inspect before proceeding")

vps = json.loads((LEADIN/"manifest.json").read_text())
raw_sha = {row["file_symbol"]: row["sha256"] for row in vps["files"].values()}

ref_manifest = json.loads((HOLD/reg["windows"]["january_2026"]["source_manifest"]).read_text())
logical_root = lane._logical_repo_root_for_registry(registry_path=REGISTRY, manifest=ref_manifest)

window = lane.WindowSpec("june_2026","2026-06-01","2026-06-30","lane_validation","202606")
lane.WINDOWS["june_2026"] = window

new_rows = []
for sym in sorted({r["symbol"] for r in old_manifest["bar_sources"]}):
    src, mapped = lane._find_bar_source(LEADIN, sym, "D1")
    if hashlib.sha256(src.read_bytes()).hexdigest() != raw_sha[sym]:
        fatal(f"raw sha mismatch {sym}")
    dest = famdir/f"{mapped}_D1.csv"
    if dest.exists(): fatal(f"dest exists {dest}")
    row = lane._transform_bar_file(source=src, destination=dest, symbol=sym, mapped_symbol=mapped,
        timeframe="D1", source_family=FAMILY, lane_root=HOLD, repo_root=logical_root)
    new_rows.append(row)
print("converted", len(new_rows), "files into", famdir.name)
if len(new_rows) != 24: fatal("expected 24")

old_bars = [dict(r) for r in old_manifest["bar_sources"]]
if len(old_bars) != 96: fatal("expected 96 existing bar rows")
manifest = lane._source_manifest(lane_root=HOLD, window=window, bars=[*old_bars, *new_rows],
    ticks=[], repo_root=logical_root,
    tick_gap_status="captured_tick_archive_ends_before_window")
new_bars = manifest["bar_sources"]
if len(new_bars) != 120 or manifest["bar_source_count"] != 120 or manifest["bar_symbol_count"] != 24:
    fatal(f"counts wrong: {len(new_bars)} {manifest['bar_source_count']} {manifest['bar_symbol_count']}")
kept = [r for r in new_bars if r["source_family"] != FAMILY]
def key(r): return (r["symbol"], r["timeframe"], r["source_family"])
if {key(r): r for r in kept} != {key(r): r for r in old_bars}:
    fatal("existing 96 entries not preserved")
diff_fields = [k for k in set(old_manifest)|set(manifest)
               if k not in ("bar_sources","bar_source_count","manifest_root_sha256")
               and old_manifest.get(k) != manifest.get(k)]
if diff_fields: fatal(f"unexpected manifest field changes: {diff_fields}")
lane._write_json(HOLD/"manifests/june_2026.json", manifest)
new_root = manifest["manifest_root_sha256"]
print("june manifest rebuilt: 120 bar_sources, root", new_root)

with lane._registry_write_lock(REGISTRY):
    current = json.loads(REGISTRY.read_text())
    if current.get("registry_root_sha256") != lane._manifest_root(current, "registry_root_sha256"):
        fatal("registry invalid inside lock")
    core = dict(current); core.pop("registry_root_sha256", None)
    before = {k: dict(v) for k, v in core["windows"].items()}
    entry = dict(before["june_2026"])
    if entry["source_manifest_root_sha256"] != old_manifest["manifest_root_sha256"]:
        fatal("june entry root unexpected inside lock")
    entry["source_manifest_root_sha256"] = new_root
    windows = {k: dict(v) for k, v in before.items()}
    windows["june_2026"] = entry
    core["windows"] = windows
    updated = {**core, "registry_root_sha256": lane._stable_sha256(core)}
    lane._write_json(REGISTRY, updated)

final = json.loads(REGISTRY.read_text())
backup = json.loads(reg_before_bytes)
for k, v in backup["windows"].items():
    if k == "june_2026":
        d = {f for f in set(v)|set(final["windows"][k]) if v.get(f) != final["windows"][k].get(f)}
        if d != {"source_manifest_root_sha256"}: fatal(f"june entry unexpected diff: {d}")
    elif final["windows"].get(k) != v:
        fatal(f"entry changed: {k}")
if final["windows"]["july_2026"]["window"] != ["2026-07-01","2026-07-28"]:
    fatal("july rebound window not preserved")
top = {k for k in set(backup)|set(final) if backup.get(k) != final.get(k)}
if top != {"windows","registry_root_sha256"}: fatal(f"unexpected top-level change: {top}")
reg_after_sha = hashlib.sha256(REGISTRY.read_bytes()).hexdigest()

receipt_core = {
    "schema": lane.MATERIALIZATION_SCHEMA,
    "status": "LANE_TRUE_UTC_D1_LEADIN_SUPPLEMENT_COMPLETE",
    "campaign_sealed": False,
    "evidence_class": lane.LANE_EVIDENCE,
    "window_id": "june_2026",
    "supplement_family": FAMILY,
    "supplement_export_commit": COMMIT,
    "supplement_source_count": 24,
    "supplement_row_count": sum(int(r["row_count"]) for r in new_rows),
    "supplement_span_utc": [min(r["first_utc"] for r in new_rows), max(r["last_utc"] for r in new_rows)],
    "converted_overlap_rows_verified_equal": 1387,
    "leadin_only_rows": 782,
    "june_manifest_root_sha256_before": old_manifest["manifest_root_sha256"],
    "june_manifest_root_sha256_after": new_root,
    "registry_file_sha256_before": reg_before_sha,
    "registry_file_sha256_after": reg_after_sha,
    "registry_root_sha256_after": final["registry_root_sha256"],
    "july_2026_entry_preserved_with_rebound_window": ["2026-07-01","2026-07-28"],
    "bar_source_count_after": 120,
    "clock_conversion": "src.utils.broker_clock.broker_epoch_to_utc",
    "broker_clock_rule": lane.NEW_YORK_PLUS_7.name,
    "economic_outcomes_read": False,
    "march_outcomes_read": False,
    "broker_live_authority": False,
    "broker_mutation_enabled": False,
    "wall_seconds": round(time.perf_counter()-started, 3),
}
receipt = {**receipt_core, "receipt_root_sha256": lane._stable_sha256(receipt_core)}
lane._write_json(HOLD/"receipts/SOURCES_june_2026_d1_supplement.json", receipt)
print("done")
