"""Build OTL3 source/as-of cleanup triage artifacts.

This script is deliberately scoped to the OTL3 source/as-of cleanup packet set.
It reads frozen OTG0 control artifacts, classifies source blockers from local
repo evidence, and writes research-only artifacts. It does not read outcome
files or modify live trading surfaces.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
OTG0_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

DATE_STAMP = "2026-05-07"
MANIFEST = OTG0_DIR / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json"
LEDGER = OTG0_DIR / f"OTG0_PREREG_CLASSIFICATION_LEDGER_{DATE_STAMP}.json"
CONTROL_JSON = OTG0_DIR / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{DATE_STAMP}.json"


CONTROLLING_INPUTS = [
    "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
    "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G0_G12_OWNER_FULL_RESEARCH_REVIEW_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_REVIEW_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G12_SOURCE_VALIDITY_REVIEW_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G12_LEAKAGE_LEDGER_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G0_POST_G12_SOURCE_NO_LEAK_CLEANUP_ASSIGNMENTS_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G0_CD2_08_SOURCE_NO_LEAK_CLEANUP_PROPOSAL_2026-05-06.md",
    "research/science_program_2026_05/01_domain_syntheses/G7_SOURCE_INDEX_2026-05-06.md",
    "research/science_program_2026_05/01_domain_syntheses/G7_AMBIGUITY_LEDGER_2026-05-06.md",
    "research/science_program_2026_05/01_domain_syntheses/G7_CD2_01_MACRO_VOL_SOURCE_FRESHNESS_COMPATIBILITY_LEDGER_2026-05-06.md",
    "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.md",
    "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.json",
    "research/science_program_2026_05/02_hypothesis_registry/G8_OPTIONS_VOL_SOURCE_CONTRACT_ROWS_2026-05-06.json",
    "research/science_program_2026_05/01_domain_syntheses/G8_OPTIONS_VOL_AMBIGUITY_LEDGER_2026-05-06.md",
    "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_INDEX_2026-05-06.md",
    "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json",
    "research/science_program_2026_05/01_domain_syntheses/G11_DATA_SOURCES_EXPANSION_AMBIGUITY_LEDGER_2026-05-06.md",
    "research/science_program_2026_05/01_domain_syntheses/G11_DATA_SOURCES_EXPANSION_CONTEXT_LEDGER_2026-05-06.md",
    "research/science_program_2026_05/00_control/G4_SOURCE_INDEX_2026-05-06.md",
    "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/G4_CD2_04_SOURCE_STATUS_JOIN_MAP_2026-05-06.md",
    "research/science_program_2026_05/02_hypothesis_registry/G5_SOURCE_CONTRACT_ROWS_2026-05-06.json",
    "src/components/external_feeds.py",
    "tests/test_external_feeds.py",
    "config/agent_config.yaml",
    "data/news_calendar.json",
]


SOURCE_CLASS: dict[str, dict[str, Any]] = {
    "G10-SRC-NEIGHBOR-G1-G6-G9": {
        "classification": "CONTEXT_ONLY",
        "allowed_role": "Local neighbor synthesis and control context only.",
        "resolved_evidence": [
            "Packet references committed G1/G6 wave-1 synthesis; G9 is absent.",
            "The cited files are research syntheses, not point-in-time market source rows.",
        ],
        "blockers": [
            "G9 absent blocks full neighbor reconciliation.",
            "G1/G6 rows still require their own promotion guards.",
            "No source row supplies decision-time market features for this packet.",
        ],
        "next_exact_question": "If G10 needs neighbor conditioning beyond context, which registered G9/G6 point-in-time packet supplies source_hash, source_capture_utc, parser_version, and no-lookahead fixtures?",
    },
    "G10-SRC-PHASE3-PATH-REPLAY": {
        "classification": "CONTEXT_ONLY",
        "allowed_role": "Synthetic path-R discovery context and prereg design only.",
        "resolved_evidence": [
            "Local phase-3 replay artifacts are committed research outputs.",
            "OTG0 packet contracts already restrict this source to discovery context.",
        ],
        "blockers": [
            "Same-dataset reuse risk.",
            "No source lifecycle provenance fields for validation.",
            "Missing H1 POI/retrace context for validation-safe path claims.",
        ],
        "next_exact_question": "Which prospective path-replay packet freezes source_capture_utc, source_hash, parser_version, lifecycle labels, and setup geometry before outcome review?",
    },
    "G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Candidate execution lifecycle context after source/as-of proof only.",
        "resolved_evidence": [
            "Local shadow logging exists, but OTG0/G12 controls do not clear it for validation.",
        ],
        "blockers": [
            "Sparse lifecycle/slippage rows.",
            "Close-side cost and broker actual-R joins are incomplete.",
            "Lifecycle label, synthetic path-R, and broker actual-R separation is not proven.",
        ],
        "next_exact_question": "Which packet stores decision_asof/source_capture timestamps, close-side cost rows, broker actual-R join evidence, and separated lifecycle labels without opening outcomes?",
    },
    "SRC-G5-AI-SHADOW-LOCAL-001": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Local AI-shadow context only until paired-run protocol and label separation are proven.",
        "resolved_evidence": [
            "G5 source contract rows exist, but all remain validation_safe=false.",
        ],
        "blockers": [
            "Paired frozen prompt rows are not registered as validation-safe.",
            "Comparator labels and lifecycle/synthetic/broker labels are not separated enough for outcome testing.",
            "Sample floors and cache hashes remain unresolved.",
        ],
        "next_exact_question": "Which frozen paired-prompt/AI-shadow packet contains setup_id, decision_time_utc, prompt/model version, comparator decision, and separated lifecycle/synthetic/broker labels?",
    },
    "SRC-G5-NEWS-CALENDAR-LOCAL-001": {
        "classification": "CLEAR_FOR_RESEARCH_PACKET_USE",
        "allowed_role": "Schedule and stale-calendar context only; not surprise, sentiment, macro release impact, or outcome label.",
        "resolved_evidence": [
            "config/agent_config.yaml points news_filter.json_calendar_file to data/news_calendar.json.",
            "data/news_calendar.json exists locally with updated_at=2026-05-01T00:30:00Z, week_of=2026-05-01, and 29 events.",
            "This resolves the stale path ambiguity noted in G12/G5 for local schedule context.",
        ],
        "blockers": [
            "The file is not a general macro data feed.",
            "No surprise value, revision/vintage, or release-result field is cleared for validation use.",
        ],
        "next_exact_question": "If G5/G7 needs more than schedule context, which official calendar/release source supplies release result, vintage, source_hash, and feature_asof_utc <= decision_time_utc fixtures?",
    },
    "SRC-G5-PROMPT-NEUTRAL-001": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Prompt-neutral rerun design only until budget, protocol, and cache are approved.",
        "resolved_evidence": [
            "G5 source rows preserve the prompt-neutral idea as research-only.",
        ],
        "blockers": [
            "No bounded rerun budget approved in this OTL3 pass.",
            "No frozen prompt-neutral cache, raw response hash, parser version, or paired fixture exists.",
            "Would require model/API execution and possible cost.",
        ],
        "next_exact_question": "Will the owner approve a bounded prompt-neutral rerun budget/cache protocol, or should this remain blocked and context-only?",
    },
    "SRC-G7-BIS-STATS-001": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Official BIS context only until exact table/dataflow and release vintage are frozen.",
        "resolved_evidence": [
            "G7 source index cached official BIS pages.",
            "G7 ambiguity ledger reports exact table and cadence ambiguity.",
        ],
        "blockers": [
            "No exact BIS table/dataflow selected.",
            "No SDMX/bulk parser and no raw hash tied to a numeric feature.",
            "Release/vintage calendar and no-lookahead join fixture are absent.",
        ],
        "next_exact_question": "Which exact BIS table/dataflow, release/vintage field, raw hash, parser version, and no-lookahead fixture supplies the packet feature?",
    },
    "SRC-G7-FED-FOMC-001": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Official FOMC schedule/event context only after event-window parser and stale-source fixture are frozen.",
        "resolved_evidence": [
            "G7 source index cached official Federal Reserve FOMC pages.",
        ],
        "blockers": [
            "No source_hash-backed parser output for event windows.",
            "No stale-source fixture proving the event record was available before decision time.",
            "Does not supply macro surprise or outcome data.",
        ],
        "next_exact_question": "Which FOMC calendar parser/cache hash/stale-source fixture creates event_time_utc and predeclared event-window rows?",
    },
    "SRC-G7-FRED-RATES-001": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Daily rates/macro context only after series, cache, vintage/release rule, and no-lookahead test are packet-bound.",
        "resolved_evidence": [
            "src/components/external_feeds.py contains a conservative FRED daily publication model.",
            "tests/test_external_feeds.py covers publication-time selection and no-lookahead snapshot behavior.",
            "scripts/external_feed_status.py found no current normalized FRED cache/status in data/external during OTL3.",
        ],
        "blockers": [
            "FRED_API_KEY absent in local status check.",
            "No packet-specific FRED series cache with raw response hash.",
            "Vintage/revision handling is not tied to this packet.",
        ],
        "next_exact_question": "Which FRED series cache with vintage/release metadata, raw hash, and parser hash proves feature_asof_utc <= decision_time_utc?",
    },
    "SRC-G7-ICE-DXY-001": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Dollar-index context only after authorized bar source, close-time rule, and parser fixtures are frozen.",
        "resolved_evidence": [
            "G7 source index cached ICE DXY source pages.",
            "G7 ambiguity ledger rejects local stale/suspicious DXY as validation-safe.",
        ],
        "blockers": [
            "No official or authorized historical DXY/broad-dollar cache is packet-bound.",
            "No close-time/publication-time rule.",
            "No no-lookahead fixture or parser version.",
        ],
        "next_exact_question": "Which authorized DXY or broad-dollar source supplies bar close/publication time, retrieval hash, parser version, and no-lookahead fixture?",
    },
    "SRC-G7-LBMA-FIX-001": {
        "classification": "CLEAR_FOR_RESEARCH_PACKET_USE",
        "allowed_role": "Deterministic LBMA fix schedule/window context only; no auction imbalance, auction flow, or benchmark price feature.",
        "resolved_evidence": [
            "src/components/external_feeds.py includes LbmaFixCalendar schedule logic.",
            "tests/test_external_feeds.py includes LBMA DST and next-fix no-lookahead schedule tests.",
            "G7/G11 source ledgers identify paid/licensed auction data separately from public schedule context.",
        ],
        "blockers": [
            "Auction imbalance/order-flow/benchmark price histories remain licensed/blocked.",
            "No numeric LBMA auction feature is cleared.",
        ],
        "next_exact_question": "If the packet needs LBMA auction imbalance or benchmark price history, which licensed source grants access, raw hash, parser version, publication timestamp, and no-lookahead fixture?",
    },
    "SRC-G7-LOCAL-GTOS-MACRO-001": {
        "classification": "CONTEXT_ONLY",
        "allowed_role": "Local GTOS macro-source inventory and blocked-route context only.",
        "resolved_evidence": [
            "G7 local ledgers document source inventory, ambiguity, and blocked routes.",
        ],
        "blockers": [
            "Local docs are not market observations.",
            "Cannot create decision-time macro features without underlying source contracts.",
        ],
        "next_exact_question": "Which underlying official/vendor source row supplies the actual macro feature with source_hash and feature_asof_utc?",
    },
    "SRC-G7-WGC-GOLDHUB-001": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "WGC/Goldhub context only until exact series/download and revision policy are frozen.",
        "resolved_evidence": [
            "G7 source index cached WGC pages.",
            "src/components/external_feeds.py has WGC import scaffolding.",
        ],
        "blockers": [
            "No exact series/workbook/export is packet-bound.",
            "No raw workbook hash or publication/revision policy.",
            "No no-lookahead fixture.",
        ],
        "next_exact_question": "Which WGC series/workbook/export, publication date, revision policy, raw hash, and parser test supplies this feature?",
    },
    "SRC-G8-CBOE-METHODOLOGY-002": {
        "classification": "CONTEXT_ONLY",
        "allowed_role": "Cboe methodology/specification context only.",
        "resolved_evidence": [
            "G8 source index cached Cboe methodology and product pages.",
        ],
        "blockers": [
            "Methodology pages are not decision-time market rows.",
            "They do not resolve CSV publication timing or historical availability.",
        ],
        "next_exact_question": "Which Cboe row-level data source and parser supplies the timestamped feature rows used by the packet?",
    },
    "SRC-G8-CBOE-VOL-CSV-001": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Public Cboe volatility CSV context only until publication timing, license, parser, and no-lookahead fixtures are frozen.",
        "resolved_evidence": [
            "G8 source index reports public Cboe CSV caches through 2026-05-05 for VIX, VIX1D, VIX9D, GVZ, VVIX, and VIX3M.",
            "G8 contract rows explicitly keep validation_safe=false.",
        ],
        "blockers": [
            "Publication/as-of timestamp for same-day availability is unknown.",
            "License review required.",
            "Packet-bound parser tests and no-lookahead join fixtures are missing.",
        ],
        "next_exact_question": "What official Cboe publication/as-of timestamp and license rule permits same-day or next-day CSV use, and where is the parser/no-lookahead fixture?",
    },
    "SRC-G8-FLASHALPHA-GEX-PROXY-003": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Vendor GEX proxy context only until forward snapshot cache and legal state are packet-bound.",
        "resolved_evidence": [
            "src/components/external_feeds.py includes FlashAlpha GEX parser scaffolding.",
            "scripts/external_feed_status.py found no current normalized FlashAlpha status and FLASHALPHA_API_KEY=false during OTL3.",
        ],
        "blockers": [
            "No current forward snapshot cache with as_of_utc.",
            "Vendor plan/legal state and historical replay rights unresolved.",
            "Proxy mapping from option GEX to packet hypothesis unvalidated.",
        ],
        "next_exact_question": "Which forward snapshot cache with as_of_utc, vendor plan/legal state, proxy mapping, raw hash, and parser version clears context-only packet use?",
    },
    "SRC-G8-GAMMA-VRP-LITERATURE-007": {
        "classification": "CONTEXT_ONLY",
        "allowed_role": "Literature mechanism prior only.",
        "resolved_evidence": [
            "G8 ledgers keep gamma/VRP literature as context, not as source rows.",
        ],
        "blockers": [
            "Literature refs are not source_contract_v2 market data rows.",
            "No packet feature_asof_utc can be derived directly from literature.",
        ],
        "next_exact_question": "If used beyond prior/context, which registered market data source supplies the actual gamma/VRP feature rows?",
    },
    "SRC-G8-OFFICIAL-HISTORICAL-GEX-004": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Potential official/vendor GEX source route only.",
        "resolved_evidence": [
            "G8 source ledgers preserve this as an unresolved route.",
        ],
        "blockers": [
            "No legal source selected.",
            "No cache, schema, timestamp rule, budget, or parser fixture.",
        ],
        "next_exact_question": "Which legal exchange/vendor aggregate GEX source, cost, point-in-time rows, raw hash, and parser fixture can be used?",
    },
    "SRC-G8-VRP-FORMULA-005": {
        "classification": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "allowed_role": "Derived VRP formula route only after formula, tenor, realized window, implied source, and as-of rule are frozen.",
        "resolved_evidence": [
            "G8 source contract rows identify VRP as derived and validation_safe=false.",
        ],
        "blockers": [
            "Formula/tenor/annualization not frozen.",
            "Realized window could leak future returns unless explicitly lagged.",
            "Implied volatility source timing and derived cache are missing.",
        ],
        "next_exact_question": "Which frozen VRP formula, tenor, annualization, implied as-of rule, realized-window no-lookahead proof, and derived cache clears this source?",
    },
}


PACKET_NEXT_QUESTIONS = {
    "OTG0-PKT-014": "Which prospective G10 lifecycle/slippage packet supplies source_capture_utc, source_hash, parser_version, close-side cost, and separated lifecycle/synthetic/broker labels?",
    "OTG0-PKT-015": "Should HYP-G11-COVERAGE-GATE-002 adopt CD2-08 proposed source_ids/no_leak_fields, and where is the coverage manifest with as-of timestamps and hashes?",
    "OTG0-PKT-018": "Should HYP-G11-OPTIONS-VOL-005 adopt SRC-G11-CBOE-OPTIONS-VOL plus concrete G8 source rows after Cboe/VRP parser rules are frozen?",
    "OTG0-PKT-039": "Which G4/G10 packet stores pending-native fill/no-fill, spread/depth, source_hash, source_symbol, trade IDs, and separated broker/synthetic/lifecycle labels?",
    "OTG0-PKT-041": "Which concrete G4 orderflow source contract and as-of depth/OFI cache supplies pre60/event15 fields without post-event windows?",
    "OTG0-PKT-042": "Which Sierra/Databento profile/VWAP source contract freezes POC/HVN/LVN/VWAP definitions and source hashes?",
    "OTG0-PKT-047": "Which joint G3/G4 packet proves directional-change and depth features are both as-of and source-hashed?",
    "OTG0-PKT-050": "Which NAS100/NQ depth-regime packet supplies source-safe depth status without date concentration or actual-R floor leakage?",
    "OTG0-PKT-051": "Move LIT-G5-LLM-001 to evidence_refs or SRC-G5-ACADEMIC-LIT-001, then register/cache the prompt-neutral paired-run protocol.",
    "OTG0-PKT-057": "Move LIT-G5-PRED-001 to evidence_refs and add concrete G4 source contracts for the pre-outcome stress proxy.",
    "OTG0-PKT-067": "Which BIS carry-stress table/dataflow and vintage parser supplies the feature rows without date-only or revised-data leakage?",
    "OTG0-PKT-070": "Which authorized DXY or broad-dollar source supplies bar close/publication time and no-lookahead fixtures?",
    "OTG0-PKT-073": "Which WGC/LBMA source rows separate public schedule context from licensed auction/flow/price histories and freeze publication timestamps?",
    "OTG0-PKT-077": "Move HYP-G5-XG7-MACRO-ATTN-009 to neighbor_lane_dependency, then keep only concrete G5/G7 source IDs with source hashes.",
    "OTG0-PKT-078": "Replace future_G8_options_vol_rows with concrete G8 source IDs only after Cboe/VRP source blockers clear.",
    "OTG0-PKT-080": "Which legal forward GEX source or proxy snapshot cache supplies as_of_utc, vendor/legal state, raw hash, and parser version?",
    "OTG0-PKT-081": "Which Cboe GVZ CSV publication/as-of and parser rule permits metals-vol use without same-day availability leakage?",
    "OTG0-PKT-083": "Which proxy map is source-hashed and tested so option-vol proxy rows are not transferred post hoc?",
    "OTG0-PKT-084": "Which Cboe VIX1D/VIX9D publication/as-of rule and parser fixture freezes short-vol stress rows before decision time?",
    "OTG0-PKT-085": "Which frozen VRP formula, implied-vol source timing, and realized-window lag fixture avoids forward return leakage?",
    "OTG0-PKT-086": "Which Cboe VVIX publication/as-of and parser fixture freezes tail-vol rows before decision time?",
}


NO_REGISTERED_SOURCE_PACKET_NOTES = {
    "OTG0-PKT-015": [
        "No registered source_contract_v2 rows in OTG0 packet.",
        "G11 no-leak fields are semantically inverted per G12 leakage ledger.",
        "CD2-08 proposes replacement source_ids and no-leak fields, but those were not registry edits in this OTL3 pass.",
    ],
    "OTG0-PKT-018": [
        "No registered source_contract_v2 rows in OTG0 packet.",
        "G11 options-vol source row exists separately but is validation_safe=false.",
        "No Cboe options-vol/G8 parser and publication-as-of proof is packet-bound.",
    ],
    "OTG0-PKT-039": [
        "No registered source_contract_v2 rows in OTG0 packet.",
        "Fill-quality labels need source-safe pending/order/fill/no-fill lifecycle fields before outcomes.",
    ],
    "OTG0-PKT-041": [
        "No registered source_contract_v2 rows in OTG0 packet.",
        "G4 OFI/depth public docs are capability context only; predictive raw features are quarantined.",
    ],
    "OTG0-PKT-042": [
        "No registered source_contract_v2 rows in OTG0 packet.",
        "Profile/VWAP definitions and source-hashed market profile rows are not frozen.",
    ],
    "OTG0-PKT-047": [
        "No registered source_contract_v2 rows in OTG0 packet.",
        "Joint G3/G4 directional-change plus depth features need both source contracts.",
    ],
    "OTG0-PKT-050": [
        "No registered source_contract_v2 rows in OTG0 packet.",
        "NAS100/NQ depth source remains blocked by vendor/license and status-leak concerns.",
    ],
    "OTG0-PKT-057": [
        "No registered source_contract_v2 rows in OTG0 packet.",
        "Unresolved LIT-G5-PRED-001 is literature/evidence context, not source_contract_v2.",
    ],
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def registered_source_ids(packet: dict[str, Any]) -> list[str]:
    rows = packet.get("registered_source_contracts") or []
    ids = []
    for row in rows:
        source_id = row.get("source_id")
        if source_id:
            ids.append(source_id)
    return ids


def source_contract_lookup(packets: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    lookup: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for packet in packets:
        for row in packet.get("registered_source_contracts") or []:
            source_id = row.get("source_id")
            if source_id:
                lookup[source_id].append(row)
    return lookup


def packet_classification(packet: dict[str, Any], ids: list[str]) -> str:
    unresolved = packet.get("unresolved_source_refs") or []
    if not ids or unresolved:
        return "BLOCKED_WITH_NEXT_EXACT_QUESTION"
    statuses = [SOURCE_CLASS[source_id]["classification"] for source_id in ids]
    if any(status == "BLOCKED_WITH_NEXT_EXACT_QUESTION" for status in statuses):
        return "BLOCKED_WITH_NEXT_EXACT_QUESTION"
    if all(status == "CLEAR_FOR_RESEARCH_PACKET_USE" for status in statuses):
        return "CLEAR_FOR_RESEARCH_PACKET_USE"
    if all(status == "CONTEXT_ONLY" for status in statuses):
        return "CONTEXT_ONLY"
    return "CONTEXT_ONLY"


def packet_blockers(packet: dict[str, Any], ids: list[str]) -> list[str]:
    blockers = []
    for row in packet.get("blockers") or []:
        if row.get("status"):
            blockers.append(f"{row.get('blocker_id')}: {row.get('question')}")
    blockers.extend(NO_REGISTERED_SOURCE_PACKET_NOTES.get(packet["packet_id"], []))
    for source_id in ids:
        source_status = SOURCE_CLASS[source_id]
        if source_status["classification"] == "BLOCKED_WITH_NEXT_EXACT_QUESTION":
            blockers.extend([f"{source_id}: {b}" for b in source_status["blockers"]])
    unresolved = packet.get("unresolved_source_refs") or []
    if unresolved:
        blockers.append("Unresolved source refs remain: " + ", ".join(unresolved))
    return list(dict.fromkeys(blockers))


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        safe = [str(cell).replace("\n", "<br>").replace("|", "\\|") for cell in row]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines)


def build() -> None:
    manifest = read_json(MANIFEST)
    ledger = read_json(LEDGER)
    control = read_json(CONTROL_JSON)

    packets = [
        packet
        for packet in manifest["packets"]
        if packet.get("owner_testing_class") == "SOURCE_ASOF_CLEANUP_BEFORE_OUTCOME_TEST"
    ]
    if len(packets) != 21:
        raise RuntimeError(f"Expected 21 SOURCE_ASOF packets; found {len(packets)}")

    if manifest.get("validation_safe") is not False or ledger.get("validation_safe") is not False:
        raise RuntimeError("Input validation_safe flag unexpectedly true")
    if manifest.get("outcome_review_opened") is not False or ledger.get("outcome_review_opened") is not False:
        raise RuntimeError("Input outcome_review_opened flag unexpectedly true")

    source_ids = sorted({source_id for packet in packets for source_id in registered_source_ids(packet)})
    unknown = sorted(set(source_ids) - set(SOURCE_CLASS))
    if unknown:
        raise RuntimeError(f"Missing source classifications: {unknown}")
    if len(source_ids) != 19:
        raise RuntimeError(f"Expected 19 unique registered source IDs; found {len(source_ids)}")

    contracts = source_contract_lookup(packets)
    source_to_packets: dict[str, list[str]] = defaultdict(list)
    for packet in packets:
        for source_id in registered_source_ids(packet):
            source_to_packets[source_id].append(packet["packet_id"])

    source_records = []
    for source_id in source_ids:
        classification = SOURCE_CLASS[source_id]
        source_records.append(
            {
                "source_id": source_id,
                "classification": classification["classification"],
                "validation_safe": False,
                "allowed_role": classification["allowed_role"],
                "packet_ids": sorted(source_to_packets[source_id]),
                "registered_cache_paths": sorted(
                    {
                        row.get("cache_path", "")
                        for row in contracts.get(source_id, [])
                        if row.get("cache_path")
                    }
                ),
                "registered_publication_asof_rules": sorted(
                    {
                        row.get("publication_asof_timestamp_rule", "")
                        for row in contracts.get(source_id, [])
                        if row.get("publication_asof_timestamp_rule")
                    }
                ),
                "resolved_evidence": classification["resolved_evidence"],
                "blockers": classification["blockers"],
                "next_exact_question": classification["next_exact_question"],
            }
        )

    packet_records = []
    for packet in packets:
        ids = registered_source_ids(packet)
        classification = packet_classification(packet, ids)
        packet_records.append(
            {
                "packet_id": packet["packet_id"],
                "experiment_id": packet["experiment_id"],
                "hypothesis_id": packet["hypothesis_id"],
                "lane": packet["lane"],
                "classification": classification,
                "outcome_test_status": "OUTCOME_TEST_STILL_BLOCKED_NO_OUTCOME_REVIEW_OPENED",
                "validation_safe": False,
                "outcome_review_opened": False,
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "registered_source_ids": ids,
                "unresolved_source_refs": packet.get("unresolved_source_refs") or [],
                "no_leak_fields": packet.get("no_leak_fields_from_hypothesis") or [],
                "required_packet_fields": packet.get("required_packet_fields") or [],
                "blockers": packet_blockers(packet, ids),
                "next_exact_question": PACKET_NEXT_QUESTIONS[packet["packet_id"]],
            }
        )

    source_class_counts = Counter(record["classification"] for record in source_records)
    packet_class_counts = Counter(record["classification"] for record in packet_records)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    git_head = git_value("rev-parse", "--short", "HEAD")
    git_branch = git_value("branch", "--show-current")

    metadata = {
        "artifact_family": "OTL3_SOURCE_ASOF_CLEANUP_TRIAGE",
        "version_date": DATE_STAMP,
        "generated_at_utc": generated_at,
        "git_head_at_generation": git_head,
        "git_branch_at_generation": git_branch,
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "research_only_no_outcome_review",
        "controlling_inputs": CONTROLLING_INPUTS,
    }

    summary = {
        "packet_count": len(packet_records),
        "unique_registered_source_count": len(source_records),
        "source_class_counts": dict(sorted(source_class_counts.items())),
        "packet_class_counts": dict(sorted(packet_class_counts.items())),
        "limited_clear_sources": [
            record["source_id"]
            for record in source_records
            if record["classification"] == "CLEAR_FOR_RESEARCH_PACKET_USE"
        ],
        "context_only_sources": [
            record["source_id"]
            for record in source_records
            if record["classification"] == "CONTEXT_ONLY"
        ],
        "blocked_sources": [
            record["source_id"]
            for record in source_records
            if record["classification"] == "BLOCKED_WITH_NEXT_EXACT_QUESTION"
        ],
        "packet_ids": [record["packet_id"] for record in packet_records],
        "outcome_tests_opened": 0,
        "validation_safe_promotions": 0,
        "external_fetches_performed": 0,
    }

    triage = {
        "metadata": metadata,
        "summary": summary,
        "universal_asof_rule": "feature_asof_utc = max(source_publication_timestamp_utc, source_cache_time_utc, source_bar_or_observation_close_time_utc when applicable); require feature_asof_utc <= candidate_decision_timestamp_utc; unknown/date-only/revised/no hash remains blocked.",
        "strict_controls": [
            "validation_safe remains false for every source and packet.",
            "outcome_review_opened remains false; no outcomes were read or opened in this OTL3 pass.",
            "NO_PROMOTION_VERDICT is preserved.",
            "No live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remotes, or order behavior are touched.",
        ],
        "source_classifications": source_records,
        "packet_triage": packet_records,
        "control_blockers_relevant_to_otl3": [
            row
            for row in control.get("blocker_ledger", [])
            if row.get("blocker_id") in {"OTG0-BLK-002", "OTG0-BLK-003", "OTG0-BLK-004", "OTG0-BLK-009"}
        ],
    }

    evidence_index = {
        "metadata": {**metadata, "artifact_family": "OTL3_SOURCE_EVIDENCE_INDEX"},
        "summary": summary,
        "local_evidence_notes": [
            {
                "evidence_id": "OTL3-EVID-NEWS-CALENDAR-PATH",
                "paths": ["config/agent_config.yaml", "data/news_calendar.json"],
                "finding": "Repo config points the news filter to data/news_calendar.json; the file exists and carries updated_at/week_of/event-count metadata. This resolves source-path ambiguity only for schedule/stale-calendar context.",
                "classification_effect": "SRC-G5-NEWS-CALENDAR-LOCAL-001 limited clear for research packet use.",
            },
            {
                "evidence_id": "OTL3-EVID-LBMA-SCHEDULE-PARSER",
                "paths": ["src/components/external_feeds.py", "tests/test_external_feeds.py"],
                "finding": "LbmaFixCalendar exists with DST/next-fix tests. This supports deterministic fix schedule/window context only.",
                "classification_effect": "SRC-G7-LBMA-FIX-001 limited clear for research packet use.",
            },
            {
                "evidence_id": "OTL3-EVID-EXTERNAL-FEED-ASOF-SCAFFOLD",
                "paths": ["src/components/external_feeds.py", "tests/test_external_feeds.py"],
                "finding": "Generic FRED/CFTC/publication-time/no-lookahead scaffolding exists, but packet-bound caches/status rows are missing for OTL3 macro packets.",
                "classification_effect": "Macro sources remain blocked unless exact source cache and packet fixture are bound.",
            },
            {
                "evidence_id": "OTL3-EVID-G8-CBOE-CACHE",
                "paths": [
                    "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.md",
                    "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.json",
                ],
                "finding": "Public Cboe CSV caches exist through 2026-05-05, but official publication/as-of timing, license review, parser tests, and no-lookahead fixtures remain unresolved.",
                "classification_effect": "SRC-G8-CBOE-VOL-CSV-001 remains blocked.",
            },
            {
                "evidence_id": "OTL3-EVID-G4-PUBLIC-DOCS",
                "paths": [
                    "research/science_program_2026_05/00_control/G4_SOURCE_INDEX_2026-05-06.md",
                    "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json",
                ],
                "finding": "Databento/Sierra/Nasdaq/LBMA public docs are capability context only; raw predictive OFI/depth/profile/auction features remain unregistered or license-blocked.",
                "classification_effect": "G4 no-source packets remain blocked with next exact source questions.",
            },
        ],
        "source_records": source_records,
    }

    completion_audit = {
        "metadata": {**metadata, "artifact_family": "OTL3_COMPLETION_AUDIT"},
        "objective_checklist": [
            {"item": "mandatory_gtos_preflight_completed_before_artifact_work", "status": "PASS"},
            {"item": "all_21_source_asof_packets_triaged", "status": "PASS", "count": len(packet_records)},
            {"item": "unique_registered_sources_classified", "status": "PASS", "count": len(source_records)},
            {"item": "outcome_review_opened_preserved_false", "status": "PASS"},
            {"item": "validation_safe_preserved_false", "status": "PASS"},
            {"item": "promotion_verdict_preserved_no_promotion", "status": "PASS"},
            {"item": "no_external_fetch_or_paid_source_access_performed", "status": "PASS"},
            {"item": "no_live_trading_surface_changes_required", "status": "PASS"},
        ],
        "residual_risks": [
            "Two sources are clear only for limited research packet context, not validation-safe outcome testing.",
            "All 21 packets remain closed to outcome review until packet-specific source/as-of questions are answered.",
            "G11 semantic no-leak fields require separate registry/packet rewrite before G11 packets can advance.",
            "G4 public documentation does not substitute for raw source-safe OFI/depth/profile/auction data.",
            "G7/G8 macro/vol sources still need packet-bound publication/as-of, cache hash, parser, revision/vintage, and no-lookahead fixtures.",
        ],
        "artifacts_written": [
            f"research/science_program_2026_05/06_outcome_testing/otl3_source_asof_cleanup/OTL3_SOURCE_ASOF_CLEANUP_TRIAGE_{DATE_STAMP}.md",
            f"research/science_program_2026_05/06_outcome_testing/otl3_source_asof_cleanup/OTL3_SOURCE_ASOF_CLEANUP_TRIAGE_{DATE_STAMP}.json",
            f"research/science_program_2026_05/06_outcome_testing/otl3_source_asof_cleanup/OTL3_SOURCE_EVIDENCE_INDEX_{DATE_STAMP}.json",
            f"research/science_program_2026_05/06_outcome_testing/otl3_source_asof_cleanup/OTL3_COMPLETION_AUDIT_{DATE_STAMP}.md",
            f"research/science_program_2026_05/06_outcome_testing/otl3_source_asof_cleanup/OTL3_COMPLETION_AUDIT_{DATE_STAMP}.json",
        ],
        "summary": summary,
    }

    write_json(f"OTL3_SOURCE_ASOF_CLEANUP_TRIAGE_{DATE_STAMP}.json", triage)
    write_json(f"OTL3_SOURCE_EVIDENCE_INDEX_{DATE_STAMP}.json", evidence_index)
    write_json(f"OTL3_COMPLETION_AUDIT_{DATE_STAMP}.json", completion_audit)
    write_text(f"OTL3_SOURCE_ASOF_CLEANUP_TRIAGE_{DATE_STAMP}.md", render_triage_md(triage))
    write_text(f"OTL3_COMPLETION_AUDIT_{DATE_STAMP}.md", render_audit_md(completion_audit))


def write_json(name: str, payload: dict[str, Any]) -> None:
    (OUT / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(name: str, text: str) -> None:
    (OUT / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def render_triage_md(triage: dict[str, Any]) -> str:
    summary = triage["summary"]
    metadata = triage["metadata"]
    source_rows = [
        [
            record["source_id"],
            record["classification"],
            ", ".join(record["packet_ids"]),
            record["allowed_role"],
            record["next_exact_question"],
        ]
        for record in triage["source_classifications"]
    ]
    packet_rows = [
        [
            record["packet_id"],
            record["lane"],
            record["experiment_id"],
            record["hypothesis_id"],
            record["classification"],
            ", ".join(record["registered_source_ids"]) or "NONE",
            ", ".join(record["unresolved_source_refs"]) or "NONE",
            record["next_exact_question"],
        ]
        for record in triage["packet_triage"]
    ]
    clear_sources = ", ".join(summary["limited_clear_sources"]) or "NONE"
    context_sources = ", ".join(summary["context_only_sources"]) or "NONE"
    blocked_sources = ", ".join(summary["blocked_sources"]) or "NONE"
    lines = [
        "# OTL3 Source/As-Of Cleanup Triage - 2026-05-07",
        "",
        "## Controls",
        "",
        f"- Generated at UTC: `{metadata['generated_at_utc']}`",
        f"- Git branch/head at generation: `{metadata['git_branch_at_generation']}` / `{metadata['git_head_at_generation']}`",
        "- Scope: research-only source/as-of cleanup. No outcomes were opened.",
        "- `validation_safe=false` for every packet and source.",
        "- `outcome_review_opened=false` for every packet.",
        "- `promotion_verdict=NO_PROMOTION_VERDICT` remains unchanged.",
        "- No live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remotes, or order behavior are touched.",
        "",
        "## Summary",
        "",
        f"- SOURCE_ASOF packets triaged: `{summary['packet_count']}`",
        f"- Unique registered source IDs classified: `{summary['unique_registered_source_count']}`",
        f"- Source classes: `{summary['source_class_counts']}`",
        f"- Packet classes: `{summary['packet_class_counts']}`",
        f"- Limited clear sources: {clear_sources}",
        f"- Context-only sources: {context_sources}",
        f"- Blocked sources: {blocked_sources}",
        "",
        "The two limited-clear sources are not validation-safe promotions. They are restricted to research packet context: local news-calendar schedule/stale-calendar context, and deterministic LBMA fix schedule/window context. Every packet remains closed to outcome review.",
        "",
        "## Universal As-Of Rule",
        "",
        triage["universal_asof_rule"],
        "",
        "## Source Classifications",
        "",
        md_table(
            ["Source ID", "Classification", "Packets", "Allowed role", "Next exact question"],
            source_rows,
        ),
        "",
        "## Packet Triage",
        "",
        md_table(
            [
                "Packet",
                "Lane",
                "Experiment",
                "Hypothesis",
                "Classification",
                "Registered sources",
                "Unresolved refs",
                "Next exact question",
            ],
            packet_rows,
        ),
        "",
        "## Required Follow-Up Before Outcomes",
        "",
        "- G11 packets need source_contract_v2 replacements and no-leak field rewrites from CD2-08/G12, not outcome review.",
        "- G4 packets need concrete OFI/depth/profile/auction/fill source contracts and source-hashed as-of caches.",
        "- G5 literature refs must move to evidence_refs or context-only source rows; prompt-neutral reruns need approved budget/cache protocol.",
        "- G7 macro sources need exact series/table/source selection, release/vintage policy, raw hashes, parser versions, and no-lookahead fixtures.",
        "- G8 vol/gamma sources need legal access state, publication/as-of timing, parser tests, proxy-map rules, and derived-feature no-lookahead fixtures.",
        "",
        "## Verdict",
        "",
        "NO_PROMOTION_VERDICT. OTL3 produced source/as-of triage only. `validation_safe=false` and `outcome_review_opened=false` remain the controlling state.",
    ]
    return "\n".join(lines)


def render_audit_md(audit: dict[str, Any]) -> str:
    metadata = audit["metadata"]
    summary = audit["summary"]
    checklist_rows = [
        [row["item"], row["status"], str(row.get("count", ""))]
        for row in audit["objective_checklist"]
    ]
    lines = [
        "# OTL3 Completion Audit - 2026-05-07",
        "",
        "## Verdict",
        "",
        "PASS for scoped research triage artifacts. NO_PROMOTION_VERDICT remains in force. No outcome review was opened.",
        "",
        "## Controls",
        "",
        f"- Generated at UTC: `{metadata['generated_at_utc']}`",
        f"- Git branch/head at generation: `{metadata['git_branch_at_generation']}` / `{metadata['git_head_at_generation']}`",
        "- `validation_safe=false`",
        "- `outcome_review_opened=false`",
        "- `promotion_verdict=NO_PROMOTION_VERDICT`",
        "- External fetches performed: `0`",
        "- Live trading surfaces touched: `0`",
        "",
        "## Checklist",
        "",
        md_table(["Item", "Status", "Count"], checklist_rows),
        "",
        "## Counts",
        "",
        f"- Packets triaged: `{summary['packet_count']}`",
        f"- Unique registered source IDs classified: `{summary['unique_registered_source_count']}`",
        f"- Source classes: `{summary['source_class_counts']}`",
        f"- Packet classes: `{summary['packet_class_counts']}`",
        "",
        "## Artifacts Written",
        "",
    ]
    lines.extend([f"- `{path}`" for path in audit["artifacts_written"]])
    lines.extend(
        [
            "",
            "## Residual Risks",
            "",
        ]
    )
    lines.extend([f"- {risk}" for risk in audit["residual_risks"]])
    lines.extend(
        [
            "",
            "## Final State",
            "",
            "OTL3 is complete as source/as-of cleanup triage only. All 21 packets stay outcome-blocked pending their packet-specific source questions.",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    build()
