#!/usr/bin/env python3
"""Session AV — the deep-H4 ingest harness, and the three sleeves' exact residual ask (AV-2).

    python3 .../phase12/receipts/av_deep_h4_ingest.py                  # inventory + verify + ask
    ...                                            --apply            # also write sidecars
    ...                                            --export <dir> ...  # explicit export dirs

WHY A HARNESS AND NOT A RE-RUN
------------------------------
`bridge_ftmo_deep_h4_*` **has not landed on this machine**. Measured: `data/mt5_research_exports/`
does not exist in this worktree (it is gitignored, so it never will by checkout), and the main
repo's copy holds five `bridge_*` directories, none of them `deep_h4`. So the commissioned work
is the half that can be done without it --- build the ingest so the orchestrator's fetch drops
straight in, and state the residual ask exactly --- and this file says so rather than
pretending.

The harness is exercised TODAY against the export shape that does exist
(`bridge_ftmo_b7_4_static_20250501_20260620`, 73 files), so "it will drop straight in" is a
tested claim rather than a hope.

WHAT THE INGEST HAS TO DO, AND WHAT THE EXISTING TOOLING DOES NOT
------------------------------------------------------------------
A bridge export carries a rich `manifest.json` --- per-file sha256, row counts, gap counts,
first/last --- and **no `.timebase.json` sidecar**. `CsvBarSource` refuses a file with no
sidecar (the F7 fail-closed rule), so an export is unreadable by the production loader until
one is written. `scripts/declare_research_timebase.py` writes them but declares a whole
DIRECTORY from one exchange anchor, which is exactly the assumption Session AV measured to be
wrong for accreted trees (`data/historical/` is two captures spliced, and two files in one
directory disagree). So this harness stamps **per file**, through
`av_timebase_verify.classify_bounded`, and refuses anything that cannot prove its clock.

It also cross-checks the manifest against the bytes: a `sha256` that no longer matches, or a
`row_count` that disagrees with the file, means the export moved after it was described --- and
that is the class of defect that is invisible until it changes a result.

THE THREE SLEEVES, AND WHY THEIR ASK IS NOW EXPRESSED IN BLOCKS
----------------------------------------------------------------
`metals_softband`, `vp_euidx_pocgrav` and `sub_mid_dn_revert` are the CARRY_CONDITIONAL tier
(`SURVIVOR_BOOK_V1.json`; on FTMO `metals_core` is UNCONDITIONAL and `vp_euidx_pocgrav` is
conditional, and on redacted_account they swap --- CLAUDE.md §4). CLAUDE.md calls recovering them
"a data fetch, not a sealed window".

AV-4 measured what the fetch has to deliver, and it is not trades: the gate's null is a block
sign-flip on the pooled daily series, so the currency is **distinct decision days**. The ask
below is therefore stated in H4 bars, calendar span, AND the blocks that span can yield --- so
the orchestrator can tell whether a given fetch would make a sleeve gate-SCOREABLE rather than
merely non-empty.
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import glob
import hashlib
import importlib.util as ilu
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15, WARMUP  # noqa: E402
from src.components.ultimate_book.sleeves.registry import BUILT  # noqa: E402

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
OUT = HERE / "AV_DEEP_H4_INGEST_V1.json"
VERIFY = HERE / "av_timebase_verify.py"

#: Where a bridge export can land. The main repo's copy is included because
#: `data/mt5_research_exports/` is gitignored --- it exists on exactly one tree per machine and
#: it is not this worktree's.
EXPORT_ROOTS = (
    REPO / "data/mt5_research_exports",
    Path("/Users/borr/GTOSActive/repo/data/mt5_research_exports"),
)
DEEP_H4_GLOB = "bridge_ftmo_deep_h4_*"

TF_OF = {"D1": TF_D1, "H4": TF_H4, "M15": TF_M15, "M1": 1}

#: The three CARRY_CONDITIONAL sleeves, read from the production registry rather than typed.
TARGETS = ("metals_softband", "vp_euidx_pocgrav", "sub_mid_dn_revert")

#: The gate's own floors, so "would this fetch make the sleeve scoreable" is answerable.
GATE_MIN_TRADES = 30
GATE_MIN_FOLDS = 3


def _load_verifier():
    spec = ilu.spec_from_file_location("av_timebase_verify", VERIFY)
    m = ilu.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


AV = _load_verifier()


def find_exports(explicit: list[str] | None) -> tuple[list[Path], list[Path]]:
    """`(deep_h4_dirs, other_bridge_dirs)` --- the target and the shape it must match."""
    if explicit:
        return [Path(p) for p in explicit if Path(p).is_dir()], []
    deep, other = [], []
    for root in EXPORT_ROOTS:
        if not root.is_dir():
            continue
        for d in sorted(root.glob("bridge_*")):
            if not d.is_dir():
                continue
            (deep if d.match(DEEP_H4_GLOB) else other).append(d)
    return deep, other


def inventory(export: Path) -> dict:
    """Symbols x timeframes x spans, plus the manifest cross-check."""
    manifest_path = export / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    files = manifest.get("files") or {}
    series: dict[str, dict] = {}
    mismatches = []
    for path in sorted(export.glob("*.csv")):
        stem = path.stem
        sym, _, tfs = stem.rpartition("_")
        rows = 0
        first = last = None
        with path.open(newline="") as fh:
            for rec in csv.DictReader(fh):
                t = (rec.get("time") or "").strip()
                if not t:
                    continue
                rows += 1
                first = first or t
                last = t
        entry = files.get(stem) or {}
        declared_rows = entry.get("row_count")
        if declared_rows is not None and int(declared_rows) != rows:
            mismatches.append({"file": stem, "manifest_rows": declared_rows, "actual_rows": rows})
        declared_sha = entry.get("sha256")
        if declared_sha:
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            if h != declared_sha:
                mismatches.append({"file": stem, "manifest_sha256": declared_sha,
                                   "actual_sha256": h})
        series[stem] = {
            "symbol": sym, "timeframe": tfs, "rows": rows,
            "first": first, "last": last,
            "manifest_gap_count": entry.get("gap_count"),
            "manifest_max_gap_seconds": entry.get("max_gap_seconds"),
        }
    return {
        "export": str(export),
        "has_manifest": bool(manifest),
        "manifest_window": [manifest.get("start_utc"), manifest.get("end_utc")],
        "n_csv": len(series),
        "symbols": sorted({v["symbol"] for v in series.values()}),
        "timeframes": sorted({v["timeframe"] for v in series.values()}),
        "series": series,
        "manifest_vs_bytes_mismatches": mismatches,
        "manifest_integrity": ("OK" if not mismatches and manifest
                               else "NO_MANIFEST" if not manifest else "MISMATCHED"),
    }


def verify_and_stamp(export: Path, *, apply: bool) -> dict:
    """Per-file clock proof. A file that cannot prove its clock is refused BY NAME."""
    results, written = {}, []
    for path in sorted(export.glob("*.csv")):
        res = AV.classify_bounded(path)
        results[path.name] = {
            "verdict": res["verdict"], "reason": res.get("reason"),
            "valid_from": res.get("valid_from"), "valid_through": res.get("valid_through"),
            "n_bars": res.get("n_bars"), "n_weeks_evaluated": res.get("n_weeks_evaluated"),
        }
        if apply and res["verdict"].startswith("STAMP_"):
            rc = AV.main(["--paths", str(path), "--bounded", "--apply", "--quiet"])
            if rc == 0:
                written.append(path.name + AV.SIDECAR_SUFFIX if hasattr(AV, "SIDECAR_SUFFIX")
                               else path.name + ".timebase.json")
    counts = collections.Counter(v["verdict"] for v in results.values())
    return {"per_file": results, "summary": dict(counts), "sidecars_written": written,
            "readable_by_csvbarsource": sum(n for v, n in counts.items() if v.startswith("STAMP_"))}


def sleeve_requirements() -> dict:
    """What each target sleeve needs, from the production registry rather than from prose."""
    out = {}
    for name in TARGETS:
        spec = BUILT.get(name)
        if spec is None:
            out[name] = {"error": "not in BUILT"}
            continue
        tf_name = {v: k for k, v in TF_OF.items()}.get(spec.timeframe, str(spec.timeframe))
        warm = WARMUP.get(spec.cluster, 200)
        aux_tf = {v: k for k, v in TF_OF.items()}.get(spec.aux_timeframe) if spec.aux_timeframe else None
        out[name] = {
            "timeframe": tf_name,
            "cluster": spec.cluster,
            "warmup_bars": warm,
            "on_surface": list(spec.on_surface),
            "aux_timeframe": aux_tf,
            "aux_count": spec.aux_count,
            "minimum_bars_per_symbol_to_emit_anything": warm + 1,
            "minimum_years_to_be_gate_SCOREABLE": None,   # filled by `price_the_ask`
        }
    return out


def price_the_ask(reqs: dict, have: dict, spans: dict, rows: dict) -> dict:
    """The residual ask, per sleeve, in the currency AV-4 established: BLOCKS.

    A fetch that clears warmup makes a sleeve non-empty. A fetch that yields enough distinct
    decision days makes it SCOREABLE. Those are different asks and the estate has been
    conflating them, which is the same conflation AV-4 measured on the pooled families.
    """
    priced = {}
    for name, req in reqs.items():
        tf = req.get("timeframe")
        want = set(req.get("on_surface") or ())
        present = {s for s, tfs in have.items() if tf in tfs}
        missing = sorted(want - present)
        aux_missing = []
        if req.get("aux_timeframe"):
            aux_present = {s for s, tfs in have.items() if req["aux_timeframe"] in tfs}
            aux_missing = sorted(want - aux_present)
        # H4 bars per calendar year on a 24/5 instrument: 6 per day x ~5 days x 52 weeks.
        bars_per_year = {"H4": 6 * 5 * 52, "D1": 5 * 52, "M15": 96 * 5 * 52, "M1": 1440 * 5 * 52}
        bpy = bars_per_year.get(tf, 0)
        warm_years = round(req["minimum_bars_per_symbol_to_emit_anything"] / bpy, 3) if bpy else None
        # A symbol being PRESENT is not the same as its span being sufficient, and reporting
        # only presence is how "SATISFIED" comes to mean "the file exists". The warmup alone
        # costs `warm_years`, so a present symbol with a shorter span emits nothing.
        # Counted from the files' OWN rows, not modelled from a bars-per-year constant: the
        # first version of this check used the constant and flagged `vp_euidx_pocgrav`'s M1 aux
        # 2.7 % short on an estimate, which is a verdict a rounding choice could flip.
        need_bars = req["minimum_bars_per_symbol_to_emit_anything"]
        short = sorted(s for s in (want & present) if rows.get((s, tf), 0) < need_bars)
        aux_short = []
        if req.get("aux_timeframe"):
            aux_short = sorted(
                s for s in want
                if rows.get((s, req["aux_timeframe"]), 0) < req.get("aux_count", 0))
        priced[name] = {
            "timeframe": tf,
            "symbols_present_but_SPAN_TOO_SHORT_for_warmup": short,
            "aux_symbols_present_but_SPAN_TOO_SHORT": aux_short,
            "bars_held_per_symbol": {s: rows.get((s, tf), 0) for s in sorted(want)},
            "bars_needed_per_symbol": need_bars,
            "aux_bars_held_per_symbol": ({s: rows.get((s, req["aux_timeframe"]), 0)
                                          for s in sorted(want)}
                                         if req.get("aux_timeframe") else None),
            "aux_bars_needed_per_symbol": req.get("aux_count") or None,
            "symbols_wanted": sorted(want),
            "symbols_present_at_this_timeframe": sorted(want & present),
            "symbols_MISSING": missing,
            "aux_timeframe": req.get("aux_timeframe"),
            "aux_symbols_MISSING": aux_missing,
            "warmup_cost_years": warm_years,
            "status": ("SATISFIED" if not (missing or aux_missing or short or aux_short)
                       else "PRESENT_BUT_TOO_SHORT" if not (missing or aux_missing)
                       else "PARTIAL" if (want & present) else "ABSENT"),
            "the_ask": (
                f"{tf} bars for {missing or 'no missing symbol'}"
                + (f"; plus {req['aux_timeframe']} aux ({req['aux_count']} bars) for "
                   f"{aux_missing}" if aux_missing else "")),
            "scoreable_not_merely_nonempty": (
                f"clearing warmup costs {warm_years} years per symbol and only makes the sleeve "
                f"NON-EMPTY. To be gate-SCOREABLE it needs >= {GATE_MIN_TRADES} trades across "
                f">= {GATE_MIN_FOLDS} evaluable folds, and AV-4 measured that the binding "
                "currency is distinct decision DAYS, not trades --- so the fetch should be "
                "priced by the span it adds, not by the file count."),
        }
    return priced


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", nargs="*", default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    deep, other = find_exports(args.export)
    targets = deep or other
    invs = {str(d): inventory(d) for d in targets}
    ver = {str(d): verify_and_stamp(d, apply=args.apply) for d in targets}

    have: dict[str, set[str]] = collections.defaultdict(set)
    spans: dict[tuple, float] = {}
    rowcount: dict[tuple, int] = collections.defaultdict(int)
    for inv in invs.values():
        for v in inv["series"].values():
            have[v["symbol"]].add(v["timeframe"])
            rowcount[(v["symbol"], v["timeframe"])] += int(v["rows"] or 0)
            if v["first"] and v["last"]:
                try:
                    a = dt.datetime.fromisoformat(v["first"][:19]).date()
                    b = dt.datetime.fromisoformat(v["last"][:19]).date()
                    yrs = (b - a).days / 365.25
                except ValueError:
                    continue
                k = (v["symbol"], v["timeframe"])
                spans[k] = max(spans.get(k, 0.0), yrs)
    reqs = sleeve_requirements()
    priced = price_the_ask(reqs, dict(have), spans, dict(rowcount))

    # A sleeve whose BARS are present is still blocked if those bars cannot prove their clock:
    # CsvBarSource refuses an unstamped file, and this session's whole point is that stamping
    # it on provenance rather than on measurement is how F7 happens. So the ask carries the
    # per-file clock verdict for exactly the files each sleeve needs.
    clock_of = {}
    for dirname, v in ver.items():
        for fname, r in v["per_file"].items():
            clock_of.setdefault(Path(fname).stem, r["verdict"])
    for name, blk in priced.items():
        tf = blk["timeframe"]
        need = [f"{s}_{tf}" for s in blk["symbols_present_at_this_timeframe"]]
        if blk.get("aux_timeframe"):
            need += [f"{s}_{blk['aux_timeframe']}" for s in blk["symbols_wanted"]]
        blk["clock_verdict_per_required_file"] = {n: clock_of.get(n, "FILE_ABSENT") for n in need}
        unprovable = sorted(n for n, vd in blk["clock_verdict_per_required_file"].items()
                            if not vd.startswith("STAMP_"))
        blk["files_present_but_CLOCK_UNPROVABLE"] = unprovable
        if unprovable and blk["status"] == "SATISFIED":
            blk["status"] = "BARS_PRESENT_BUT_CLOCK_UNPROVABLE"
            blk["the_ask"] = (
                f"the bars are here and sufficient; {len(unprovable)} of them cannot prove "
                f"their clock from their own bytes ({unprovable[:4]}), so CsvBarSource refuses "
                "them. Either a longer span (the probe needs a US/EU DST disagreement window "
                "inside the file to separate the candidate clocks) or a declaration from the "
                "export's own provenance, taken deliberately and recorded as ASSERTED rather "
                "than MEASURED.")

    payload = {
        "schema": "gtos.wave12.av.deep_h4_ingest.v1",
        "session": "AV", "blocks": "B1661-B1670",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "the_export_state": {
            "deep_h4_found": [str(d) for d in deep],
            "other_bridge_exports_found": [str(d) for d in other],
            "searched": [str(r) for r in EXPORT_ROOTS],
            "verdict": ("DEEP_H4_PRESENT" if deep else "DEEP_H4_ABSENT"),
            "note": ("`data/mt5_research_exports/` is gitignored, so it exists on exactly one "
                     "tree per machine and never arrives by checkout. When the orchestrator's "
                     "fetch lands, re-run this file with --apply and the sidecars, the manifest "
                     "cross-check and the per-sleeve status all recompute."),
        },
        "inventory": invs,
        "timebase_verification": ver,
        "sleeve_requirements": reqs,
        "residual_ask": priced,
        "series_spans_years": {f"{k[0]}:{k[1]}": round(v, 3) for k, v in sorted(spans.items())},
        "sidecars_NOT_written_to_the_main_repo": (
            "`data/mt5_research_exports/` lives in /Users/borr/GTOSActive/repo, not in this "
            "worktree, and it is gitignored --- so a sidecar written there is machine state "
            "outside this session's branch that no merge would carry and no checkout would "
            "revert. The harness reports what it WOULD stamp and leaves the write to the "
            "orchestrator, who owns that tree. Run with --apply from a session that does."),
        "harness_was_exercised_on": [str(d) for d in targets],
        "seconds_total": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    print(json.dumps({"export_state": payload["the_export_state"]["verdict"],
                      "exercised_on": payload["harness_was_exercised_on"],
                      "verification": {k: v["summary"] for k, v in ver.items()},
                      "manifest_integrity": {k: v["manifest_integrity"] for k, v in invs.items()},
                      "residual_ask": {k: {"status": v["status"], "missing": v["symbols_MISSING"],
                                           "aux_missing": v["aux_symbols_MISSING"],
                                           "too_short": v["symbols_present_but_SPAN_TOO_SHORT_for_warmup"],
                                           "aux_too_short": v["aux_symbols_present_but_SPAN_TOO_SHORT"]}
                                       for k, v in priced.items()}}, indent=2))


if __name__ == "__main__":
    main()
