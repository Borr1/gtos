#!/usr/bin/env python3
"""Fit GEOMETRY_BOUND_OUTCOME_MODEL_V1 on the opened Wave 21 estate (44 days).

Result-bearing fitter for the geometry-bound outcome calibration model -- the
replacement probability authority for the falsified action-support score.

Corpus: exactly the opened estate and nothing else.

* October/November 2025 -- the six preregistered development days plus the two
  formerly-untouched days (2025-10-30, 2025-11-06) that the frozen decision
  read opened; the preregistration's untouched_repair_rule moved them into
  development permanently.
* January 2026 -- the 16 expanded-development days.
* February 2026 -- the 20 regenerated r2 validation days (used-once VAL,
  already outcome-read by FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2).

Excluded by rule: April/May 2026 (frozen read in progress -- the aprmay-r3
root is not touched), the held reserve days 2025-10-31 and 2025-11-05, and
anything READ_RESTRICTED.

Every compact root is opened through its sealed authority hash, every M1
label source is verified against its pinned manifest root, rows are labeled
by the committed ``candidate_funnel_analysis._lifecycle_row`` (the same
labeler every prior Wave 21 read used), and the pure fitter in
``src.research_infra.geometry_bound_outcome_model`` recomputes and seals the
artifact.  Environment-bound absolute paths follow the committed
``w21_score_feb_market_top_r2.py`` precedent.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

FUNNEL_PATH = Path(__file__).resolve().parent / "candidate_funnel_analysis.py"
_FUNNEL_SPEC = importlib.util.spec_from_file_location(
    "w21_funnel_for_geometry_bound_fit", FUNNEL_PATH
)
assert _FUNNEL_SPEC is not None and _FUNNEL_SPEC.loader is not None
funnel = importlib.util.module_from_spec(_FUNNEL_SPEC)
sys.modules[_FUNNEL_SPEC.name] = funnel
_FUNNEL_SPEC.loader.exec_module(funnel)

from src.components.ultimate_book.primitives import Bar
from src.research_infra.geometry_bound_outcome_model import (
    fit_geometry_bound_outcome_model,
)
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from src.research_infra.walkforward.quote_side import spread_for

PREREGISTRATION_PATH = (
    Path(__file__).resolve().parent / "OUTCOME_AUTHORITY_PREREGISTRATION_V1.json"
)
OUTPUT_PATH = (
    Path(__file__).resolve().parent / "GEOMETRY_BOUND_OUTCOME_MODEL_V1.json"
)

HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
LANE_MANIFEST_DIR = HOLD / (
    ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"
)
JANUARY_MANIFEST_PATH = LANE_MANIFEST_DIR / "january_2026.json"
JANUARY_MANIFEST_ROOT = (
    "8b7d3b269081f3e84672d57dbb304c4a81f8328600284c876c3a4ecf518754e3"
)
FEBRUARY_MANIFEST_PATH = LANE_MANIFEST_DIR / "february_2026.json"
FEBRUARY_MANIFEST_ROOT = (
    "955937e4f0c4c66ea95dcf52f1c3ac1a40b90e7c00411a9b1490e19a623e9148"
)

#: October/November opened days: sealed compact roots + authority hashes as
#: bound by every prior Wave 21 read of this estate.
OCT_NOV_RUNS = (
    (
        "2025-10-27",
        "/private/tmp/w21-current-funnel-56c5-2025-10-27.ldQ6hW/compact_events",
        "709f096615056e5dc703e0d200d6d47b29cee095a0e0e71494fd01e4e8898eb3",
    ),
    (
        "2025-10-28",
        "/private/tmp/w21-current-funnel-56c5-20251028.YTxPq3/compact_events",
        "3c577a593bf9b61f11236fbc04ca27815ddb571f6e0866657058fcdaf5065928",
    ),
    (
        "2025-10-29",
        "/private/tmp/w21-current-funnel-56c5-2025-10-29.sOmsft/compact_events",
        "487e0a5754eb0258ee12301fa2c1b7e84654632fc8b43a94a6b21562978dba11",
    ),
    (
        "2025-10-30",
        "/private/tmp/w21-decision-funnel-20251030.cNA4KU/compact_events",
        "734b57b1c99a6816b9e0d4d465283b49771acb2f5035e81f0c7befbc36efa6b4",
    ),
    (
        "2025-11-03",
        "/private/tmp/w21-current-funnel-56c5-2025-11-03.U5BWls/compact_events",
        "3df9eec140fcd052082b0c41327802dcc04c9c610306b6cdccd337564728fece",
    ),
    (
        "2025-11-04",
        "/private/tmp/w21-current-funnel-56c5-2025-11-04.FFkTOS/compact_events",
        "ac7a50c425d8138ce81c39bc582dcd3c97040c63c320d4d9595561c7c94f9a88",
    ),
    (
        "2025-11-06",
        "/private/tmp/w21-decision-funnel-20251106.lZlS3j/compact_events",
        "ed2ced2d0f7fb1a2a43708d9d4565b0e2f678c73615526ae332a1b91814f5197",
    ),
    (
        "2025-11-07",
        "/private/tmp/w21-current-funnel-56c5-2025-11-07.gwm033/compact_events",
        "351c4fbfd3433f58e4cd82c1dc0d4c27abdc47e67d96b0149181a23ae7a35cca",
    ),
)

JAN_ROOT = Path("/private/tmp/w21-expanded-development-jan-6a31.OaqMpQ")
JAN_RUNS = (
    ("2026-01-05", "caac9f4a052315faf62f0e2d2c3cb575c353c04257f9965d8f465b7001277509"),
    ("2026-01-06", "3da6c61af07b4d47d3e156a0cd865d17cc70db185dc94932bf150f562c377272"),
    ("2026-01-07", "b1199d640165febcacb9fd28a4f62d47a2130620c2171f5c688dfcf03f9712ca"),
    ("2026-01-08", "83b48a667dda9b46a06af1aaed204f2e5dc0fcf8b358a873cfbd43fd1c08ce7d"),
    ("2026-01-12", "105a68f89d9b76bcceb2d897e613d6cd41587fc089fcc9c6853c61ac99feef06"),
    ("2026-01-13", "7a34da5d7eaf5e1c7e223d008513109be4f4e1565433b14cd9bb5041c05623d1"),
    ("2026-01-14", "e392efdb5a78ce0a676fd9699d4d99027e2c25d22a16b22ecdeaa0f43ae69583"),
    ("2026-01-15", "32bc0af0c581302d0358315385665f847c49e49b435758778e442805e7cd08dc"),
    ("2026-01-19", "6fb9b98729ca20aa1aa6bf314ff3f295d6cb0e14b512d172277457a41ff5e22b"),
    ("2026-01-20", "de35d50917f1e989a0b795ac2c31e2cea70392b59d10c3a1cd8d2c15a44d3d20"),
    ("2026-01-21", "5d6bc1d85a5d500ec6c74107bed3423078ca749dc187a4215c785ff5c7a328ee"),
    ("2026-01-22", "51e6d292832faa0b14c315c01fc7b8fa1f506fcf4bdfe3b5e607e361947e1a70"),
    ("2026-01-26", "ff0440d6667d19c7ad58495cba88086d6c6fc32f2920c903a9744acfb6c56fd0"),
    ("2026-01-27", "51ad12e582e712fad387d210821e0ab9fc1c732d3a795af8ce9d0631ccc675b4"),
    ("2026-01-28", "0a32625429823192854b10ad82dea63218ed7b9cead810a864879a967c87757b"),
    ("2026-01-29", "89b75ac517b561b95cd827c3a87fa7db0c54588a5d6a953074311dc752e00df5"),
)

FEB_ROOT = Path("/private/tmp/w21-market-top-feb-r2")
FEB_RUNS = (
    ("2026-02-02", "bf2eeea72aa9d94a393e315f6472b1fa06a8fabe28d356084a60526eb5486b2d"),
    ("2026-02-03", "ef0c92fd42909b01bb606ca53d10c8111e32ed432778f5f81debf17907befd4b"),
    ("2026-02-04", "65d60ece7fa52375a0406dbfbf6077592e4a18ae532fdb4d7b76eaa7474277c9"),
    ("2026-02-05", "246db7e32f1e6217989f8c706f74be3ac83939e024acf25d70e68badedf2bf9b"),
    ("2026-02-06", "baa752a34420fa7f81ce98c432f4ec0bffcf673d0f2fbf67565adce2711dc14e"),
    ("2026-02-09", "34e49b2f74b016e0cf14059eecc39f4e32bbd61481064016d3ca9f455f1548ef"),
    ("2026-02-10", "55784f351fe898f1b1faf5b72d96a799b6deabfcb886c4f4e11006d5c078573d"),
    ("2026-02-11", "583c8d78e1e8bdea2ea1e0f6a43430e92e4692bb4b8ebb37844a92d2f0dafba0"),
    ("2026-02-12", "4458ad0f3a888b88e146d0c833f2368b54dba56e0ed1c2f40bb6b60bd0f8ff78"),
    ("2026-02-13", "0e2ee7cab5083cc802f269132edff9cfa07e6e4049d12b46c4c38badcaca61b8"),
    ("2026-02-16", "6e81a947e2324c5423118712005fac3e963e901dd1f00a119a2804311cb0f292"),
    ("2026-02-17", "c485682671a97b9fb113a7445a09b1cd9bbd1a2d70a0dc2884b9a3efca5823b6"),
    ("2026-02-18", "98f540c52192826037527dd53aa6078256c8905389865711660716c61d3d5efe"),
    ("2026-02-19", "2aa5f2e50195a248206c1b0718872bba46077ce526367190b8e526d33ba459b2"),
    ("2026-02-20", "e8a19bd53cfff5b1f2f689653324333e0e798c4bd2b5aa21009ebcd2181b45ba"),
    ("2026-02-23", "d408e6114ec251c4198d4df96eecdeb305048ae92bf787ade7392fa4d83a04fb"),
    ("2026-02-24", "5afe9712bc9f29f30ee20e9061a106545320497268e99d9f37e00664e3650907"),
    ("2026-02-25", "b60adf703e5475392593ab0ba93529d5cfa2fcc6ef2e815bfc30df89bdf362a3"),
    ("2026-02-26", "049bfde6e590811d8d208e49b559a8c633f33f5449891b5416fe6981c9752bdc"),
    ("2026-02-27", "dd9f8ba8ce45bbccd9973314178ff9993a847459994fd3468378686be55980cb"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_hold_m1_sources(manifest_path: Path, expected_root: str):
    """Load a lane-hold month's 24 M1 sources in the funnel's bundle shape."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["manifest_root_sha256"] != expected_root:
        raise ValueError(f"manifest root changed: {manifest_path}")
    bundle = {}
    for entry in manifest["bar_sources"]:
        if entry["timeframe"] != "M1":
            continue
        path = HOLD / entry["repo_relpath"]
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"M1 source missing: {path}")
        observed = sha256_file(path)
        if observed != entry["sha256"]:
            raise ValueError(f"M1 source hash mismatch: {path}")
        times, bars = [], []
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["time", "open", "high", "low", "close", "volume"]:
                raise ValueError(f"M1 source schema mismatch: {path}")
            for row in reader:
                times.append(funnel._utc(row["time"]))
                bars.append(
                    Bar(
                        float(row["open"]),
                        float(row["high"]),
                        float(row["low"]),
                        float(row["close"]),
                    )
                )
        if len(times) != entry["row_count"] or any(
            left >= right for left, right in zip(times, times[1:])
        ):
            raise ValueError(f"M1 source chronology mismatch: {path}")
        spread_cache: dict[dt.datetime, float] = {}
        spreads = []
        for instant in times:
            hour = instant.replace(minute=0, second=0, microsecond=0)
            if hour not in spread_cache:
                spread_cache[hour] = spread_for(
                    entry["symbol"], hour, account="FTMO", band="mid"
                )
            spreads.append(spread_cache[hour])
        bundle[entry["symbol"]] = (
            SimpleNamespace(sha256=observed),
            tuple(times),
            tuple(bars),
            tuple(spreads),
        )
    if len(bundle) != 24:
        raise ValueError(f"M1 symbol denominator is not 24: {manifest_path}")
    return manifest["manifest_root_sha256"], bundle


def labeled_rows(day: str, root: Path, authority: str, manifest_root: str, sources):
    sink = ReplayCompactEventSink.open_sealed(
        root=root, expected_authority_root_sha256=authority
    )
    rows = [
        funnel._lifecycle_row(raw, manifest_root=manifest_root, sources=sources)
        for raw in sink.ledger("missed")
    ]
    print(json.dumps({"labeled": day, "occurrences": len(rows)}), flush=True)
    return rows


def main() -> int:
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    rows_by_day: dict[str, list[dict]] = {}
    corpus_days: list[dict] = []

    for day, root, authority in OCT_NOV_RUNS:
        manifest_root, sources = funnel._source_bundle(day)
        rows_by_day[day] = labeled_rows(
            day, Path(root), authority, manifest_root, sources
        )
        corpus_days.append(
            {
                "trading_day": day,
                "window_id": (
                    "october_2025" if day.startswith("2025-10") else "november_2025"
                ),
                "compact_root": str(root),
                "authority_root_sha256": authority,
                "source_manifest_root_sha256": manifest_root,
            }
        )

    jan_manifest_root, jan_sources = load_hold_m1_sources(
        JANUARY_MANIFEST_PATH, JANUARY_MANIFEST_ROOT
    )
    for day, authority in JAN_RUNS:
        root = JAN_ROOT / day / "compact_events"
        rows_by_day[day] = labeled_rows(
            day, root, authority, jan_manifest_root, jan_sources
        )
        corpus_days.append(
            {
                "trading_day": day,
                "window_id": "january_2026",
                "compact_root": str(root),
                "authority_root_sha256": authority,
                "source_manifest_root_sha256": jan_manifest_root,
            }
        )

    feb_manifest_root, feb_sources = load_hold_m1_sources(
        FEBRUARY_MANIFEST_PATH, FEBRUARY_MANIFEST_ROOT
    )
    for day, authority in FEB_RUNS:
        root = FEB_ROOT / day / "compact_events"
        summary = json.loads(
            (FEB_ROOT / day / "run_summary.json").read_text(encoding="utf-8")
        )
        if summary["authority_root_sha256"] != authority:
            raise ValueError(f"February authority drift at {day}")
        rows_by_day[day] = labeled_rows(
            day, root, authority, feb_manifest_root, feb_sources
        )
        corpus_days.append(
            {
                "trading_day": day,
                "window_id": "february_2026",
                "compact_root": str(root),
                "authority_root_sha256": authority,
                "source_manifest_root_sha256": feb_manifest_root,
            }
        )

    created_utc = (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    artifact = fit_geometry_bound_outcome_model(
        rows_by_day,
        corpus_days=corpus_days,
        limit_origin_families=sorted(funnel.LIMIT_FAMILIES),
        preregistration=preregistration,
        created_utc=created_utc,
    )
    OUTPUT_PATH.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    strict = artifact["prequential_evaluation"]["strict_endpoint"]
    print(
        "W21_GEOMETRY_BOUND_OUTCOME_MODEL="
        + json.dumps(
            {
                "path": str(OUTPUT_PATH),
                "artifact_file_sha256": sha256_file(OUTPUT_PATH),
                "payload_sha256": artifact["payload_sha256"],
                "day_count": artifact["training_corpus"]["day_count"],
                "totals": artifact["training_corpus"]["totals"],
                "strict_scored_rows": strict["scored_rows"],
                "strict_brier": strict["brier"],
                "strict_base_rate_brier": strict["base_rate_brier"],
                "cells": len(artifact["final_fit"]["cells"]),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
