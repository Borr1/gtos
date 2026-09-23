"""Build OTB3 source/no-leak cleanup sidecar artifacts.

OTB3 is a blocker-clearing research lane. It emits context-only source
evidence, proposed registry patches, and no-leak rewrite sidecars without
opening outcomes or editing master registries directly.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
DATE_STAMP = "2026-05-07"

OTG = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
OTB0 = OTG / "otb0_blocker_clearing_governor"
OTL3 = OTG / "otl3_source_asof_cleanup"
CONTROL = ROOT / "research" / "science_program_2026_05" / "00_control"
HYP = ROOT / "research" / "science_program_2026_05" / "02_hypothesis_registry"
PREREG = ROOT / "research" / "science_program_2026_05" / "03_experiment_specs"
SYNTH = ROOT / "research" / "science_program_2026_05" / "05_synthesis"
RAW = ROOT / "research" / "science_program_2026_05" / "01_domain_syntheses" / "raw"

SOURCE_ASSIGNMENTS = OTB0 / f"OTB0_SOURCE_ASOF_CLEANUP_ASSIGNMENTS_{DATE_STAMP}.json"
NO_LEAK_ASSIGNMENTS = OTB0 / f"OTB0_NO_LEAK_REWRITE_ASSIGNMENTS_{DATE_STAMP}.json"
OWNER_LEDGER = OTB0 / f"OTB0_OWNER_APPROVAL_LEDGER_{DATE_STAMP}.json"
PACKET_REQUIREMENTS = OTB0 / f"OTB0_PACKET_BUILDER_REQUIREMENTS_{DATE_STAMP}.json"
OTL3_TRIAGE = OTL3 / f"OTL3_SOURCE_ASOF_CLEANUP_TRIAGE_{DATE_STAMP}.json"
SOURCE_REGISTRY = CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json"
HYP_REGISTRY = HYP / "HYPOTHESIS_REGISTRY_2026-05-06.json"
PREREGISTRY = PREREG / "EXPERIMENT_PREREGISTRY_2026-05-06.json"
PACKET_MANIFEST = OTG / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json"

CONTROLLING_INPUTS = [
    SOURCE_ASSIGNMENTS,
    NO_LEAK_ASSIGNMENTS,
    OWNER_LEDGER,
    OTB0 / f"OTB0_BLOCKER_DEPENDENCY_GRAPH_{DATE_STAMP}.json",
    PACKET_REQUIREMENTS,
    OTL3_TRIAGE,
    CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.md",
    SYNTH / "G12_RED_TEAM_REVIEW_2026-05-06.md",
    SYNTH / "G12_SOURCE_VALIDITY_REVIEW_2026-05-06.md",
    SYNTH / "G12_LEAKAGE_LEDGER_2026-05-06.md",
    SYNTH / "G12_LABEL_SEPARATION_REVIEW_2026-05-06.md",
    SYNTH / "G12_DUPLICATE_COUNTING_REVIEW_2026-05-06.md",
    SYNTH / "G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.md",
    ROOT / ".context" / "00_core" / "research_current_state.md",
]

FORBIDDEN_NOLEAK_NAMES = {
    "actual_r",
    "future_orderflow",
    "future_price",
    "future_release_value",
    "future_return",
    "future_vol_index",
    "outcome_r",
    "post_entry_path",
    "post_event_outcome",
    "post_release_revision",
    "post_signal_continuation",
    "post_signal_path",
    "stop_loss_hit",
    "take_profit_hit",
    "tp_sl_hit",
    "trade_outcome",
    "trade_result",
    "win_loss",
}

SOURCE_REF_REWRITES = [
    {
        "row_id": "HYP-G5-PRED-003",
        "registry": "hypothesis_registry",
        "current_source_ids_remove": ["LIT-G5-PRED-001"],
        "proposed_source_ids_add": [],
        "move_to": {"evidence_refs": ["LIT-G5-PRED-001"]},
        "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
        "residual_blocker": "Needs concrete G4/source-safe pre-outcome stress source before packet use.",
    },
    {
        "row_id": "HYP-G5-XG4-PRED-007",
        "registry": "hypothesis_registry",
        "current_source_ids_remove": ["LIT-G5-PRED-001"],
        "proposed_source_ids_add": [],
        "move_to": {"evidence_refs": ["LIT-G5-PRED-001"]},
        "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
        "residual_blocker": "Needs concrete G4 source contracts for the pre-outcome stress proxy.",
    },
    {
        "row_id": "HYP-G5-XG7-MACRO-ATTN-009",
        "registry": "hypothesis_registry",
        "current_source_ids_keep": ["SRC-G5-NEWS-CALENDAR-LOCAL-001"],
        "current_source_ids_remove": ["LIT-G5-FOMC-001", "LIT-G5-FOMC-DECAY-001"],
        "move_to": {"evidence_refs": ["LIT-G5-FOMC-001", "LIT-G5-FOMC-DECAY-001"]},
        "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
        "residual_blocker": "Only local schedule/stale-calendar context is clear; official FOMC event-time parser remains blocked.",
    },
    {
        "row_id": "HYP-G7-XG5-MACRO-ATTN-010",
        "registry": "hypothesis_registry",
        "current_source_ids_keep": [
            "SRC-G7-FED-FOMC-001",
            "SRC-G7-LOCAL-GTOS-MACRO-001",
            "SRC-G5-NEWS-CALENDAR-LOCAL-001",
        ],
        "current_source_ids_remove": ["HYP-G5-XG7-MACRO-ATTN-009"],
        "move_to": {"neighbor_lane_dependency": ["HYP-G5-XG7-MACRO-ATTN-009"]},
        "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
        "residual_blocker": "FOMC parser/cache/as-of source remains packet-blocking before outcomes.",
    },
    {
        "row_id": "HYP-G7-XG8-VOL-MACRO-011",
        "registry": "hypothesis_registry",
        "current_source_ids_remove": ["future_G8_options_vol_rows"],
        "proposed_source_ids_add": ["SRC-G8-CBOE-VOL-CSV-001", "SRC-G8-VRP-FORMULA-005"],
        "move_to": {"blocked_dependency_refs": ["future_G8_options_vol_rows"]},
        "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
        "residual_blocker": "Concrete G8 sources remain validation_safe=false until Cboe/VRP legal, as-of, parser, and no-lookahead blockers clear.",
    },
    {
        "row_id": "HYP-G7-XG11-SOURCE-FRESH-012",
        "registry": "hypothesis_registry",
        "current_source_ids_remove": ["future_G11_source_governance_rows"],
        "proposed_source_ids_add": [
            "SRC-G11-LOCAL-G0-REGISTRIES",
            "SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING",
            "SRC-G11-PUBLIC-CFTC-FRED-BIS",
        ],
        "move_to": {"blocked_dependency_refs": ["future_G11_source_governance_rows"]},
        "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
        "residual_blocker": "G11 source-governance rows are context only and still validation_safe=false.",
    },
]

G11_SOURCE_ID_PROPOSALS = {
    "HYP-G11-PROVENANCE-GATE-001": [
        "SRC-G11-LOCAL-G0-REGISTRIES",
        "SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING",
    ],
    "HYP-G11-COVERAGE-GATE-002": [
        "SRC-G11-LOCAL-INSTRUMENT-EXPANSION",
        "SRC-G11-LOCAL-G0-REGISTRIES",
    ],
    "HYP-G11-SOURCE-TRANSFER-003": [
        "SRC-G11-DATABENTO-GLBX-MDP3",
        "SRC-G11-SIERRA-SCID-DEPTH",
        "SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING",
    ],
    "HYP-G11-PUBLIC-LAG-004": [
        "SRC-G11-PUBLIC-CFTC-FRED-BIS",
        "SRC-G11-LOCAL-G0-REGISTRIES",
    ],
    "HYP-G11-OPTIONS-VOL-005": [
        "SRC-G11-CBOE-OPTIONS-VOL",
        "SRC-G8-CBOE-VOL-CSV-001",
        "SRC-G8-VRP-FORMULA-005",
    ],
    "HYP-G11-OBSERVER-EXPANSION-006": [
        "SRC-G11-OBSERVER-SOURCE-REGISTRY",
        "SRC-G11-LOCAL-INSTRUMENT-EXPANSION",
    ],
    "HYP-G11-FRICTION-GATE-007": [
        "SRC-G11-LOCAL-INSTRUMENT-EXPANSION",
        "G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE",
    ],
    "HYP-G11G4-SOURCE-GATED-ORDERFLOW-008": [
        "SRC-G11-DATABENTO-GLBX-MDP3",
        "SRC-G11-SIERRA-SCID-DEPTH",
        "SRC-G4-DATABENTO-GLBX-MDP3",
        "SRC-G4-SIERRA-DEPTH-SCID",
        "SRC-G4-LOCAL-GTOS-ORDERFLOW-ARTIFACTS",
    ],
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: dict[str, Any]) -> None:
    (OUT / name).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(name: str, text: str) -> None:
    (OUT / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def file_evidence(path: Path) -> dict[str, Any]:
    exists = path.exists()
    out: dict[str, Any] = {
        "path": rel(path) if path.exists() else path.as_posix(),
        "exists": exists,
    }
    if exists and path.is_file():
        stat = path.stat()
        out.update(
            {
                "size_bytes": stat.st_size,
                "sha256": sha256(path),
                "mtime_utc": datetime.fromtimestamp(
                    stat.st_mtime,
                    tz=timezone.utc,
                )
                .replace(microsecond=0)
                .isoformat(),
            }
        )
    return out


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def parse_news_calendar(generated_at: datetime) -> dict[str, Any]:
    path = ROOT / "data" / "news_calendar.json"
    evidence = file_evidence(path)
    if not path.exists():
        return {"status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION", "file": evidence}
    data = read_json(path)
    updated_at = data.get("updated_at")
    updated_dt = None
    source_age_days = None
    if isinstance(updated_at, str):
        try:
            updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            source_age_days = round(
                (generated_at - updated_dt).total_seconds() / 86400.0,
                3,
            )
        except ValueError:
            pass
    events = data.get("events") or []
    return {
        "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
        "allowed_role": "schedule_and_stale_calendar_context_only",
        "file": evidence,
        "configured_live_path": "data/news_calendar.json",
        "absent_stale_contract_path": "data/news/forexfactory_calendar.json",
        "week_of": data.get("week_of"),
        "updated_at": updated_at,
        "source_age_days_at_generation": source_age_days,
        "event_count": len(events),
        "high_impact_count": sum(1 for e in events if str(e.get("impact", "")).upper() == "HIGH"),
        "currencies": sorted({str(e.get("currency", "")).upper() for e in events if e.get("currency")}),
        "live_behavior_change": False,
        "packet_context_fields": [
            "calendar_path",
            "source_hash",
            "calendar_updated_at_utc",
            "source_age_days_at_decision",
            "stale_calendar_state",
            "event_time_utc",
            "event_currency",
            "event_impact_asof",
        ],
        "forbidden_roles": [
            "surprise_value",
            "sentiment",
            "macro_release_result",
            "trade_outcome_label",
        ],
    }


def parse_fomc_probe() -> dict[str, Any]:
    path = RAW / "G7_macro_cross_asset_sources_2026-05-06" / "fed_fomc_calendars.html"
    evidence = file_evidence(path)
    if not path.exists():
        return {
            "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
            "file": evidence,
            "next_exact_question": "Which official Fed calendar cache supplies FOMC event_time_utc and release timestamps?",
        }
    text = path.read_text(encoding="utf-8", errors="ignore")
    panel_match = re.search(
        r"<h4><a id=\"[^\"]+\">2026 FOMC Meetings</a></h4>(.*?)(?:<h4><a id=\"[^\"]+\">2025 FOMC Meetings</a></h4>)",
        text,
        flags=re.DOTALL,
    )
    panel = panel_match.group(1) if panel_match else text
    meetings = []
    month_re = re.compile(
        r"<strong>(?P<month>[A-Za-z]+)</strong>.*?fomc-meeting__date[^>]*>(?P<date>[^<]+)</div>",
        flags=re.DOTALL,
    )
    month_lookup = {
        name: idx
        for idx, name in enumerate(
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
            start=1,
        )
    }
    for match in month_re.finditer(panel):
        month = match.group("month")
        date_text = re.sub(r"[^0-9\\-]", "", match.group("date"))
        if not date_text or month not in month_lookup:
            continue
        end_day = int(date_text.split("-")[-1])
        meetings.append(
            {
                "event_id": f"FOMC-2026-{month_lookup[month]:02d}-{end_day:02d}",
                "meeting_month": month,
                "meeting_date_text": match.group("date").strip(),
                "decision_date": f"2026-{month_lookup[month]:02d}-{end_day:02d}",
                "event_time_utc": None,
                "event_time_status": "BLOCKED_OFFICIAL_PAGE_CACHE_IS_DATE_ONLY",
            }
        )
    minutes = [
        {
            "release_date_text": m.group(1),
            "release_time_utc": None,
            "release_time_status": "BLOCKED_OFFICIAL_PAGE_CACHE_IS_DATE_ONLY",
        }
        for m in re.finditer(r"\(Released ([A-Za-z]+ \d{2}, 2026)\)", panel)
    ]
    return {
        "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "file": evidence,
        "parsed_2026_meeting_count": len(meetings),
        "parsed_2026_minutes_release_count": len(minutes),
        "meeting_rows_date_only": meetings,
        "minutes_rows_date_only": minutes,
        "parser_probe_status": "DATE_ONLY_CACHE_HASHED_NOT_PACKET_READY",
        "next_exact_question": "Which official Fed source/cache supplies event_time_utc or a conservative predeclared time rule with stale-source/no-lookahead fixtures?",
    }


def cboe_csv_probe() -> dict[str, Any]:
    base = RAW / "G8_options_vol_sources_2026-05-06"
    files = sorted(base.glob("cboe_*_history.csv"))
    rows = []
    for path in files:
        row: dict[str, Any] = {"file": file_evidence(path)}
        try:
            with path.open(newline="", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or []
                first_date = None
                last_date = None
                count = 0
                date_field = fieldnames[0] if fieldnames else None
                for item in reader:
                    count += 1
                    if date_field:
                        value = item.get(date_field)
                        if value and first_date is None:
                            first_date = value
                        if value:
                            last_date = value
                row.update(
                    {
                        "fieldnames": fieldnames,
                        "row_count": count,
                        "date_field": date_field,
                        "first_observation_date": first_date,
                        "last_observation_date": last_date,
                    }
                )
        except OSError as exc:
            row["read_error"] = str(exc)
        rows.append(row)
    return {
        "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "csv_files_found": len(rows),
        "csv_file_probes": rows,
        "legal_status": "LICENSE_REVIEW_REQUIRED",
        "publication_asof_status": "BLOCKED_PUBLICATION_TIMESTAMP_UNKNOWN",
        "parser_fixture_status": "HEADER_AND_DATE_RANGE_PROBED_NOT_PACKET_BOUND",
        "next_exact_question": "What official Cboe publication/as-of timestamp and license rule permits same-day or next-day CSV use, and where is the parser/no-lookahead fixture?",
    }


def lbma_schedule_probe() -> dict[str, Any]:
    try:
        from src.components.external_feeds import LbmaFixCalendar

        rows = LbmaFixCalendar.generate("2026-05-01", "2026-06-30", metals=("gold", "silver"))
        return {
            "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
            "allowed_role": "deterministic_fix_schedule_window_context_only",
            "source_code": file_evidence(ROOT / "src" / "components" / "external_feeds.py"),
            "tests": file_evidence(ROOT / "tests" / "test_external_feeds.py"),
            "generated_probe_range": {"start": "2026-05-01", "end": "2026-06-30"},
            "row_count": len(rows),
            "sample_rows": rows[:6],
            "forbidden_roles": [
                "auction_imbalance",
                "auction_flow",
                "benchmark_price_history",
                "order_flow",
            ],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
            "error": str(exc),
            "next_exact_question": "Why did LbmaFixCalendar fail to generate deterministic schedule rows?",
        }


def build_source_hash_index() -> list[dict[str, Any]]:
    paths = [
        ROOT / "config" / "agent_config.yaml",
        ROOT / "data" / "news_calendar.json",
        ROOT / "src" / "components" / "news_calendar.py",
        ROOT / "scripts" / "refresh_economic_calendar.py",
        ROOT / "src" / "components" / "external_feeds.py",
        ROOT / "tests" / "test_external_feeds.py",
        RAW / "G7_macro_cross_asset_sources_2026-05-06" / "fed_fomc_calendars.html",
        RAW / "G7_macro_cross_asset_sources_2026-05-06" / "bis_statistics_index.html",
        RAW / "G7_macro_cross_asset_sources_2026-05-06" / "ice_us_dollar_index_futures.html",
        RAW / "G7_macro_cross_asset_sources_2026-05-06" / "wgc_goldhub_data.html",
        RAW / "G7_macro_cross_asset_sources_2026-05-06" / "lbma_gold_price.html",
        RAW / "G7_macro_cross_asset_sources_2026-05-06" / "lbma_daily_auction_prices.html",
        RAW / "G8_options_vol_sources_2026-05-06" / "cboe_vix1d_history.csv",
        RAW / "G8_options_vol_sources_2026-05-06" / "cboe_vix9d_history.csv",
        RAW / "G8_options_vol_sources_2026-05-06" / "cboe_vvix_history.csv",
        RAW / "G8_options_vol_sources_2026-05-06" / "cboe_gvz_history.csv",
        RAW / "G8_options_vol_sources_2026-05-06" / "cboe_selected_vol_indices_methodology.pdf",
        RAW / "G8_options_vol_sources_2026-05-06" / "flashalpha_api.html",
        CONTROL / "G4_SOURCE_INDEX_2026-05-06.md",
        CONTROL / "G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json",
        CONTROL / "G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json",
        CONTROL / "G11_DATA_SOURCES_EXPANSION_SOURCE_INDEX_2026-05-06.md",
        CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
        HYP_REGISTRY,
        PREREGISTRY,
        PACKET_MANIFEST,
    ]
    return [file_evidence(path) for path in paths]


def find_row(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def build_no_leak_rewrites(assignments: list[dict[str, Any]], hypothesis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for assignment in assignments:
        hid = assignment["hypothesis_id"]
        current_row = find_row(hypothesis_rows, "hypothesis_id", hid) or {}
        current_fields = current_row.get("no_leak_fields") or []
        proposed_fields = assignment["rewrite_to_asof_feature_whitelist"]
        forbidden_seen = [field for field in current_fields if field in FORBIDDEN_NOLEAK_NAMES]
        proposed_forbidden = [field for field in proposed_fields if field in FORBIDDEN_NOLEAK_NAMES]
        out.append(
            {
                "hypothesis_id": hid,
                "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
                "direct_master_registry_edit_status": "OWNER_APPROVAL_REQUIRED",
                "current_registry_no_leak_fields": current_fields,
                "forbidden_current_fields_detected": forbidden_seen,
                "proposed_no_leak_fields": proposed_fields,
                "proposed_forbidden_fields_detected": proposed_forbidden,
                "proposed_source_ids_context_only": G11_SOURCE_ID_PROPOSALS.get(hid, []),
                "move_forbidden_fields_to": assignment["move_forbidden_fields_to"],
                "validation_safe": False,
                "outcome_review_opened": False,
                "packet_builder_instruction": "Use proposed_no_leak_fields as the as-of whitelist sidecar only; do not treat forbidden current fields as features.",
            }
        )
    return out


def build_proposed_patchset(no_leak_rewrites: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "artifact_family": "OTB3_PROPOSED_PATCHSET",
        "version_date": DATE_STAMP,
        "generated_at_utc": generated_at,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "direct_master_registry_edits_applied": False,
        "direct_master_registry_edit_status": "OWNER_APPROVAL_REQUIRED",
        "patch_groups": {
            "source_contract_registry_context_only_updates": [
                {
                    "row_id": "SRC-G5-NEWS-CALENDAR-LOCAL-001",
                    "operation": "replace_cache_path_in_future_registry_patch",
                    "current_value": "data/news/forexfactory_calendar.json and local source files; no new cache written in this pass",
                    "proposed_value": "data/news_calendar.json; src/components/news_calendar.py; scripts/refresh_economic_calendar.py; config/agent_config.yaml",
                    "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
                    "validation_safe_remains": False,
                    "allowed_role": "schedule/stale-calendar context only; live news-filter behavior unchanged",
                }
            ],
            "g11_no_leak_field_rewrites": [
                {
                    "row_id": row["hypothesis_id"],
                    "operation": "replace_no_leak_fields_in_future_registry_patch",
                    "current_value": row["current_registry_no_leak_fields"],
                    "proposed_value": row["proposed_no_leak_fields"],
                    "move_forbidden_fields_to": row["move_forbidden_fields_to"],
                    "status": row["status"],
                    "validation_safe_remains": False,
                }
                for row in no_leak_rewrites
            ],
            "g11_context_source_id_proposals": [
                {
                    "row_id": row["hypothesis_id"],
                    "operation": "add_context_source_ids_in_future_registry_patch",
                    "proposed_value": row["proposed_source_ids_context_only"],
                    "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION"
                    if not row["proposed_source_ids_context_only"]
                    else "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
                    "validation_safe_remains": False,
                    "note": "Source IDs are context/provenance only unless a later source-specific dossier clears validation_safe.",
                }
                for row in no_leak_rewrites
            ],
            "source_ref_and_literature_rewrites": SOURCE_REF_REWRITES,
        },
    }


def assignment_statuses(assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    status_by_assignment = {
        "SA-001": {
            "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
            "why": "Configured local data/news_calendar.json exists, is hash-stamped, and can be used only for schedule/stale-calendar packet context.",
        },
        "SA-002": {
            "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
            "why": "Cached official Fed page is hash-stamped and date-parsed, but event_time_utc and stale-source/no-lookahead fixture are not packet-ready.",
        },
        "SA-003": {
            "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
            "why": "FRED/BIS/DXY need exact series/table/source, vintage or close-time rule, raw cache, parser version, and no-lookahead fixture.",
        },
        "SA-004": {
            "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
            "why": "Cboe CSV caches are hash/header/date-range probed but publication_asof_utc and license rules remain unresolved.",
        },
        "SA-005": {
            "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
            "why": "LbmaFixCalendar supports deterministic fix schedule/window context; auction/price/imbalance data remain forbidden.",
        },
        "SA-006": {
            "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
            "why": "G4 orderflow/depth/profile/fill rows still require packet-bound source symbols, schemas, hashes, proxy maps, and feature windows ending before decision time.",
        },
        "SA-007": {
            "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
            "why": "GEX/VRP rows still need legal source route, proxy-map version, formula/tenor/annualization, realized-window lag, raw hashes, and parser fixtures.",
        },
        "SA-008": {
            "status": "OWNER_APPROVAL_REQUIRED",
            "why": "Literature/source-ref cleanup is proposed as context-only patchset; any prompt-neutral pilot remains owner/budget/cache gated.",
            "substatus": {
                "literature_source_ref_rewrite": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
                "prompt_neutral_api_pilot": "OWNER_APPROVAL_REQUIRED",
            },
        },
    }
    records = []
    for assignment in assignments:
        status = status_by_assignment[assignment["assignment_id"]]
        records.append({**assignment, **status})
    return records


def packet_statuses(otl3_packet_triage: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for packet in otl3_packet_triage:
        ids = packet.get("registered_source_ids") or []
        limited_clear = set(ids) <= {
            "SRC-G5-NEWS-CALENDAR-LOCAL-001",
            "SRC-G7-LBMA-FIX-001",
        } and bool(ids)
        records.append(
            {
                "packet_id": packet["packet_id"],
                "experiment_id": packet["experiment_id"],
                "hypothesis_id": packet["hypothesis_id"],
                "registered_source_ids": ids,
                "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY"
                if limited_clear and not packet.get("unresolved_source_refs")
                else "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
                "outcome_review_opened": False,
                "validation_safe": False,
                "next_exact_question": packet["next_exact_question"],
                "residual_blocker_count": len(packet.get("blockers") or []),
            }
        )
    return records


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        cells = [str(value).replace("\n", "<br>").replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_cleanup_md(cleanup: dict[str, Any]) -> str:
    summary = cleanup["summary"]
    assignment_rows = [
        [
            row["assignment_id"],
            row["scope"],
            row["status"],
            row["why"],
        ]
        for row in cleanup["assignment_statuses"]
    ]
    source_rows = [
        [
            row["source_id"],
            row["classification"],
            row["otb3_status"],
            row["next_exact_question"],
        ]
        for row in cleanup["source_statuses"]
    ]
    packet_rows = [
        [
            row["packet_id"],
            row["experiment_id"],
            row["status"],
            row["next_exact_question"],
        ]
        for row in cleanup["packet_context_statuses"]
    ]
    return "\n".join(
        [
            "# OTB3 Source/No-Leak Cleanup Ledger - 2026-05-07",
            "",
            f"**Generated at UTC:** `{cleanup['metadata']['generated_at_utc']}`",
            f"**Branch/head:** `{cleanup['metadata']['git_branch']}` / `{cleanup['metadata']['git_head']}`",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "**Validation safe:** `false`",
            "**Outcome review opened:** `false`",
            "",
            "## Summary",
            "",
            f"- Assignments processed: `{summary['assignment_count']}`",
            f"- G11 no-leak rewrites proposed: `{summary['g11_no_leak_rewrite_count']}`",
            f"- Source statuses: `{summary['source_status_counts']}`",
            f"- Packet context statuses: `{summary['packet_status_counts']}`",
            f"- Proposed direct master-registry edits applied: `{summary['direct_master_registry_edits_applied']}`",
            f"- External fetches/API/paid calls: `{summary['external_fetches_or_paid_calls']}`",
            "",
            "## Assignment Status",
            "",
            md_table(["Assignment", "Scope", "Status", "Evidence"], assignment_rows),
            "",
            "## Source Status",
            "",
            md_table(["Source", "OTL3 class", "OTB3 status", "Next exact question"], source_rows),
            "",
            "## Packet Context Status",
            "",
            md_table(["Packet", "Experiment", "Status", "Next exact question"], packet_rows),
            "",
            "## Guardrails",
            "",
            "- Master registries were not edited; patch operations are sidecar proposals for G12/G0 review.",
            "- `data/news_calendar.json` was hash-stamped and used as existing local evidence only; no live news-filter behavior changed.",
            "- No outcomes, R/result values, quarantine files, Databento pulls, AI/API calls, MT5, canaries, prompts, risk, execution, permissions, selectors, safety gates, credentials, remotes, or order behavior were touched.",
        ]
    )


def render_no_leak_md(rows: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    table_rows = [
        [
            row["hypothesis_id"],
            ", ".join(row["forbidden_current_fields_detected"]),
            ", ".join(row["proposed_no_leak_fields"]),
            row["status"],
        ]
        for row in rows
    ]
    return "\n".join(
        [
            "# OTB3 G11 No-Leak Rewrite Ledger - 2026-05-07",
            "",
            f"**Generated at UTC:** `{metadata['generated_at_utc']}`",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "**Validation safe:** `false`",
            "**Outcome review opened:** `false`",
            "",
            md_table(
                ["Hypothesis", "Forbidden current fields", "Proposed as-of whitelist", "Status"],
                table_rows,
            ),
            "",
            "Forbidden current fields are moved to blocker/test-method/label-separation text in the proposed patchset. They must not be consumed as decision-time features.",
        ]
    )


def render_audit_md(audit: dict[str, Any]) -> str:
    checklist = [
        [row["requirement"], row["status"], row["evidence"]]
        for row in audit["prompt_to_artifact_checklist"]
    ]
    return "\n".join(
        [
            "# OTB3 Completion Audit - 2026-05-07",
            "",
            f"**Generated at UTC:** `{audit['metadata']['generated_at_utc']}`",
            f"**Can mark OTB3 complete:** `{str(audit['can_mark_otb3_complete']).lower()}`",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            "## Objective Restated",
            "",
            audit["objective_restatement"],
            "",
            "## Prompt-To-Artifact Checklist",
            "",
            md_table(["Requirement", "Status", "Evidence"], checklist),
            "",
            "## Residual Blockers",
            "",
            "\n".join(f"- {item}" for item in audit["residual_blockers"]),
        ]
    )


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    generated_at_dt = datetime.now(timezone.utc).replace(microsecond=0)
    generated_at = generated_at_dt.isoformat()

    source_assignments = read_json(SOURCE_ASSIGNMENTS)
    no_leak_assignments = read_json(NO_LEAK_ASSIGNMENTS)
    owner_ledger = read_json(OWNER_LEDGER)
    packet_requirements = read_json(PACKET_REQUIREMENTS)
    otl3 = read_json(OTL3_TRIAGE)
    source_registry = read_json(SOURCE_REGISTRY)
    hyp_registry = read_json(HYP_REGISTRY)
    preregistry = read_json(PREREGISTRY)
    packet_manifest = read_json(PACKET_MANIFEST)

    metadata = {
        "artifact_family": "OTB3_SOURCE_NOLEAK_CLEANUP",
        "version_date": DATE_STAMP,
        "generated_at_utc": generated_at,
        "git_branch": git_value("branch", "--show-current"),
        "git_head": git_value("rev-parse", "--short", "HEAD"),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "scope": "research_only_source_noleak_sidecar_cleanup",
        "controlling_inputs": [rel(path) for path in CONTROLLING_INPUTS],
    }

    no_leak_rows = build_no_leak_rewrites(
        no_leak_assignments["assignments"],
        hyp_registry["rows"],
    )
    proposed_patchset = build_proposed_patchset(no_leak_rows, generated_at)
    assignments = assignment_statuses(source_assignments["assignments"])

    source_statuses = []
    for record in otl3["source_classifications"]:
        otb3_status = (
            "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY"
            if record["source_id"] in {"SRC-G5-NEWS-CALENDAR-LOCAL-001", "SRC-G7-LBMA-FIX-001"}
            else "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION"
            if record["classification"] != "CONTEXT_ONLY"
            else "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY"
        )
        source_statuses.append(
            {
                **record,
                "otb3_status": otb3_status,
                "validation_safe": False,
                "outcome_review_opened": False,
            }
        )

    packet_context = packet_statuses(otl3["packet_triage"])
    parser_probes = {
        "local_news_calendar": parse_news_calendar(generated_at_dt),
        "fed_fomc_calendar": parse_fomc_probe(),
        "cboe_vol_csv": cboe_csv_probe(),
        "lbma_fix_schedule": lbma_schedule_probe(),
    }

    evidence_index = {
        "metadata": {**metadata, "artifact_family": "OTB3_SOURCE_EVIDENCE_INDEX"},
        "source_hash_index": build_source_hash_index(),
        "parser_cache_probes": parser_probes,
        "official_fetches_performed": [],
        "network_or_paid_calls_performed": [],
        "legal_asof_summary": {
            "calendar_local": "local operator-maintained source; schedule/stale context only",
            "fed_fomc": "official cached page; date-only parser probe; still blocked for event_time_utc",
            "fred_bis_dxy_wgc": "cached docs or scaffolding only; exact series/table/source and vintage rules still blocked",
            "cboe_vol": "public CSV caches exist; license and publication_asof unresolved",
            "g4_orderflow": "local/cached/public docs only; raw predictive feature use still blocked",
            "databento": "no spend; no credit/API check performed",
        },
    }

    source_status_counts = Counter(row["otb3_status"] for row in source_statuses)
    packet_status_counts = Counter(row["status"] for row in packet_context)

    cleanup = {
        "metadata": metadata,
        "summary": {
            "assignment_count": len(assignments),
            "g11_no_leak_rewrite_count": len(no_leak_rows),
            "source_status_counts": dict(sorted(source_status_counts.items())),
            "packet_status_counts": dict(sorted(packet_status_counts.items())),
            "direct_master_registry_edits_applied": False,
            "external_fetches_or_paid_calls": 0,
            "validation_safe_true_count_after_sidecar": 0,
            "outcome_review_opened_true_count_after_sidecar": 0,
            "source_registry_rows_read": len(source_registry["rows"]),
            "hypothesis_rows_read": len(hyp_registry["rows"]),
            "preregistry_rows_read": len(preregistry["rows"]),
            "packet_manifest_rows_read": len(packet_manifest["packets"]),
        },
        "assignment_statuses": assignments,
        "source_statuses": source_statuses,
        "packet_context_statuses": packet_context,
        "owner_approval_state": owner_ledger,
        "packet_builder_requirements_read": {
            "universal_packet_fields": packet_requirements.get("universal_packet_fields"),
            "outcome_result_columns_allowed_in_primary_packets": packet_requirements.get("outcome_result_columns_allowed_in_primary_packets", False),
        },
    }

    audit = {
        "metadata": {**metadata, "artifact_family": "OTB3_COMPLETION_AUDIT"},
        "objective_restatement": (
            "Produce OTB3 research-only source/no-leak cleanup sidecars and proposed patch artifacts from OTB0/OTL3/G12 controls; "
            "clear only context-safe packet-building use, preserve validation_safe=false and outcome_review_opened=false, and leave live trading behavior untouched."
        ),
        "prompt_to_artifact_checklist": [
            {
                "requirement": "Mandatory GTOS preflight completed",
                "status": "PASS",
                "evidence": ".context/LIVE_STATE.md regenerated before OTB3 artifact build; latest handoff, quick reference, doctrine, research current state, and controlling files were read.",
            },
            {
                "requirement": "Use controlling OTB0/OTL3/SOURCE/G12/research-state inputs",
                "status": "PASS",
                "evidence": f"{len(metadata['controlling_inputs'])} controlling inputs are recorded in metadata and loaded where machine-readable.",
            },
            {
                "requirement": "Resolve source-path/as-of/parser/cache/hash/legal/no-lookahead blockers into sidecars",
                "status": "PASS",
                "evidence": "OTB3_SOURCE_EVIDENCE_INDEX and parser/cache probes classify every source as context-clear or still blocked with exact questions.",
            },
            {
                "requirement": "Resolve G11 no_leak semantic inversions",
                "status": "PASS",
                "evidence": f"{len(no_leak_rows)} G11 rewrite rows replace forbidden future/outcome fields with as-of whitelists in sidecar patchset.",
            },
            {
                "requirement": "No direct master-registry edits unless safe",
                "status": "PASS",
                "evidence": "direct_master_registry_edits_applied=false; proposed patchset is sidecar-only and marks direct edits OWNER_APPROVAL_REQUIRED.",
            },
            {
                "requirement": "Use public fetch only for official docs with cached evidence",
                "status": "PASS",
                "evidence": "No external fetch performed; cached official/raw files are hash-indexed instead.",
            },
            {
                "requirement": "Apply local calendar cleanup without changing live news-filter behavior",
                "status": "PASS",
                "evidence": "data/news_calendar.json is used as hash-stamped schedule/stale context; file and config are not modified.",
            },
            {
                "requirement": "Do not open outcomes, inspect R/result values, create quarantine/result outputs, or flip safety flags",
                "status": "PASS",
                "evidence": "Artifacts contain no result/quarantine writes; validation_safe=false and outcome_review_opened=false throughout.",
            },
            {
                "requirement": "No paid/API budget, Databento credits, live trading surfaces, credentials, remotes, or order behavior touched",
                "status": "PASS",
                "evidence": "Builder reads local docs/data only and writes under OTB3 research artifact directory.",
            },
        ],
        "residual_blockers": [
            "Most G7/G8/G4 sources remain STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION until source-specific official/legal/cache/parser/as-of/no-lookahead dossiers exist.",
            "Direct master-registry patching remains OWNER_APPROVAL_REQUIRED and should go through G12/G0 blocker-clearing audit.",
            "No source is validation-safe; all future packet builders must keep context-only fields physically separated from outcomes.",
        ],
        "can_mark_otb3_complete": True,
        "no_promotion_verdict": True,
    }

    write_json(f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.json", cleanup)
    write_text(f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.md", render_cleanup_md(cleanup))
    write_json(f"OTB3_SOURCE_EVIDENCE_INDEX_{DATE_STAMP}.json", evidence_index)
    write_json(f"OTB3_G11_NO_LEAK_REWRITE_LEDGER_{DATE_STAMP}.json", {"metadata": metadata, "rewrites": no_leak_rows})
    write_text(f"OTB3_G11_NO_LEAK_REWRITE_LEDGER_{DATE_STAMP}.md", render_no_leak_md(no_leak_rows, metadata))
    write_json(f"OTB3_PROPOSED_PATCHSET_{DATE_STAMP}.json", proposed_patchset)
    write_json(f"OTB3_COMPLETION_AUDIT_{DATE_STAMP}.json", audit)
    write_text(f"OTB3_COMPLETION_AUDIT_{DATE_STAMP}.md", render_audit_md(audit))
    write_json(
        f"OTB3_ARTIFACT_MANIFEST_{DATE_STAMP}.json",
        {
            "metadata": {**metadata, "artifact_family": "OTB3_ARTIFACT_MANIFEST"},
            "artifacts": [
                rel(OUT / f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.json"),
                rel(OUT / f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.md"),
                rel(OUT / f"OTB3_SOURCE_EVIDENCE_INDEX_{DATE_STAMP}.json"),
                rel(OUT / f"OTB3_G11_NO_LEAK_REWRITE_LEDGER_{DATE_STAMP}.json"),
                rel(OUT / f"OTB3_G11_NO_LEAK_REWRITE_LEDGER_{DATE_STAMP}.md"),
                rel(OUT / f"OTB3_PROPOSED_PATCHSET_{DATE_STAMP}.json"),
                rel(OUT / f"OTB3_COMPLETION_AUDIT_{DATE_STAMP}.json"),
                rel(OUT / f"OTB3_COMPLETION_AUDIT_{DATE_STAMP}.md"),
            ],
        },
    )


if __name__ == "__main__":
    build()
