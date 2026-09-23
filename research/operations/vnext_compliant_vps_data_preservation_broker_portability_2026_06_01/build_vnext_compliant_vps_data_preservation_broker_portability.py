#!/usr/bin/env python3
"""Build the compliant VPS data-preservation and broker-portability route.

This is a research/control artifact builder. It fetches public redacted_account
policy pages, inventories local evidence, and writes route ledgers. It never
imports MT5 and never performs broker-changing actions.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
RAW_SOURCE_DIR = ROUTE_DIR / "raw" / "official_sources"

PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_COMPLIANT_VPS_DATA_PRESERVATION_AND_BROKER_PORTABILITY_GOAL_PROMPT_2026-06-01.md"
)
STARTER_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_COMPLIANT_VPS_DATA_PRESERVATION_AND_BROKER_PORTABILITY_STARTER_2026-06-01.txt"
)

ACTIVE_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

OFFICIAL_SOURCES = [
    {
        "source_id": "redacted_account_restricted_countries",
        "url": "https://help.redacted_account.com/en/articles/8020080-does-redacted_account-have-any-country-restrictions",
        "required_fact_family": "restricted_country_and_mt5_usa_ip_policy",
    },
    {
        "source_id": "redacted_account_vpn_vps_policy",
        "url": "https://help.redacted_account.com/en/articles/8223809-can-i-use-a-vpn-or-vps",
        "required_fact_family": "vpn_vps_policy",
    },
    {
        "source_id": "redacted_account_device_network_policy",
        "url": "https://help.redacted_account.com/en/articles/9351758-redacted_account-trading-device-and-network-policy",
        "required_fact_family": "device_network_policy",
    },
    {
        "source_id": "redacted_account_terms_of_service",
        "url": "https://redacted_account.com/terms-of-service",
        "required_fact_family": "terms_identity_residence_and_platform_controls",
    },
]

REQUIRED_ARTIFACTS = [
    "ROUTE_CONTEXT_ANCHOR.json",
    "OFFICIAL_redacted_account_SOURCE_INDEX.json",
    "COMPLIANCE_FACT_LEDGER.jsonl",
    "LOCAL_EVIDENCE_INVENTORY.jsonl",
    "LOCAL_EVIDENCE_COVERAGE_SUMMARY.json",
    "DATA_SURFACE_RETENTION_DECISION_LEDGER.jsonl",
    "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl",
    "VPS_MIGRATION_CONTRACT.md",
    "VPS_STARTUP_VERIFICATION_RUNBOOK.md",
    "BROKER_PORTABILITY_MAP.json",
    "BROKER_PORTABILITY_GAP_LEDGER.jsonl",
    "MT5_EXPORT_READINESS_CHECKLIST.json",
    "DEFAULT_OFF_EXPORT_SCRIPT_MANIFEST.json",
    "ABSOLUTE_MOONSHOT_DATA_REQUIREMENT_MAP.json",
    "OUTPUT_MANIFEST.json",
    "VERIFICATION_RESULT.json",
    "COMPLETION_AUDIT.json",
]

TEXT_EXTENSIONS = {
    ".bat",
    ".cfg",
    ".csv",
    ".ini",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}

SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
}

SECRET_NAME_RE = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|credential)", re.I
)
DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}(?:[T _]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?")
SYMBOL_TOKEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(symbol) for symbol in sorted(ACTIVE_SYMBOLS, key=len, reverse=True)) + r")\b",
    re.I,
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "svg", "noscript"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "svg", "noscript"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)

    def text(self) -> str:
        return re.sub(r"\s+", " ", html.unescape(" ".join(self.parts))).strip()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("/", "\\")
    except ValueError:
        return str(path)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if limit is not None and len(rows) >= limit:
                    break
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    rows.append(value)
    except OSError:
        return []
    return rows


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def file_hash_record(path: Path, full_hash_limit: int = 32 * 1024 * 1024) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        if size <= full_hash_limit:
            return {"hash_strategy": "sha256_full", "sha256": sha256_file(path)}
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            first = handle.read(1024 * 1024)
            handle.seek(max(0, size - 1024 * 1024))
            last = handle.read(1024 * 1024)
        digest.update(first)
        digest.update(str(size).encode("ascii"))
        digest.update(last)
        return {
            "hash_strategy": "sha256_first_last_1mb_plus_size",
            "sha256_chunk": digest.hexdigest(),
            "full_sha256_required_for_export": True,
        }
    except OSError as exc:
        return {"hash_strategy": "unreadable", "hash_error": str(exc)}


def git_text(args: list[str]) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()


def git_head() -> dict[str, Any]:
    try:
        return {
            "head": git_text(["rev-parse", "HEAD"]),
            "head_short": git_text(["rev-parse", "--short=9", "HEAD"]),
            "head_subject": git_text(["log", "-1", "--pretty=%s"]),
        }
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"head": None, "error": str(exc)}


def tracked_paths() -> set[str]:
    try:
        out = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO_ROOT)
    except (OSError, subprocess.CalledProcessError):
        return set()
    return {item.decode("utf-8", "replace").replace("/", "\\") for item in out.split(b"\0") if item}


def status_map() -> dict[str, str]:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            cwd=REPO_ROOT,
        )
    except (OSError, subprocess.CalledProcessError):
        return {}
    parts = [part.decode("utf-8", "replace") for part in out.split(b"\0") if part]
    result: dict[str, str] = {}
    i = 0
    while i < len(parts):
        entry = parts[i]
        code = entry[:2]
        path = entry[3:].replace("/", "\\")
        result[path] = code.strip() or "modified"
        if code.startswith("R") or code.startswith("C"):
            i += 1
        i += 1
    return result


def html_to_text(raw: bytes) -> str:
    parser = _TextExtractor()
    parser.feed(raw.decode("utf-8", errors="replace"))
    return parser.text()


def normalize_country_list(text: str) -> list[str]:
    cleaned = text.replace("\xa0", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    parts = cleaned.split(",")
    countries = []
    for part in parts:
        country = re.sub(r"^\s*and\s+", "", part, flags=re.I).strip(" .;:")
        if country:
            countries.append(country)
    return countries


def extract_restricted_countries(text: str) -> list[str]:
    match = re.search(
        r"residents and citizens of (?P<countries>.*?) are not able to access",
        text,
        flags=re.I,
    )
    if not match:
        return []
    return normalize_country_list(match.group("countries"))


def extract_policy_facts(source_id: str, text: str) -> dict[str, Any]:
    lower = text.lower()
    facts: dict[str, Any] = {"source_id": source_id}
    if source_id == "redacted_account_restricted_countries":
        countries = extract_restricted_countries(text)
        facts.update(
            {
                "restricted_basis": "residents_and_citizens" if "residents and citizens" in lower else "not_extracted",
                "restricted_countries": countries,
                "malaysia_listed_restricted": any(country.lower() == "malaysia" for country in countries),
                "tunisia_listed_restricted": any(country.lower() == "tunisia" for country in countries),
                "usa_based_ip_for_mt5_not_allowed": (
                    "usa-based ip address" in lower
                    and ("metaquotes" in lower or "metatrader" in lower or "mt5" in lower)
                ),
                "false_identity_or_location_hiding_incompatible": "third-party identities" in lower
                or "inaccurate declarations" in lower,
            }
        )
    elif source_id == "redacted_account_vpn_vps_policy":
        facts.update(
            {
                "vpn_allowed_with_restrictions": "permitted to use a vpn" in lower,
                "restricted_country_ip_prohibited": "ip addresses from restricted countries" in lower,
                "vps_allowed_with_fee": "allowed to use a vps" in lower and "usage fee" in lower,
                "private_dedicated_vps_required": "private vps" in lower and "dedicated ip" in lower,
                "shared_vps_prohibited": "sharing your vps connection" in lower and "prohibited" in lower,
                "trade_taking_ea_required_for_vps": "trade-taking expert advisors" in lower,
                "manual_trading_through_vps_prohibited": "manual trading" in lower and "strictly prohibited" in lower,
                "broker_sponsored_vps_prohibited": "broker" in lower and "sponsored" in lower,
                "vps_ea_addon_or_fee_required_when_applicable": "add-on" in lower and "additional usage fee" in lower,
            }
        )
    elif source_id == "redacted_account_device_network_policy":
        facts.update(
            {
                "personal_device_only": "personal devices exclusively owned by the trader" in lower,
                "shared_device_prohibited": "shared with another trader" in lower,
                "network_allowed_if_ip_not_restricted": "ip address does not originate from a restricted country" in lower,
                "vpn_must_follow_country_ip_restrictions": "vpn is used" in lower
                and "country-based ip restrictions" in lower,
                "usa_based_ip_for_mt4_mt5_not_allowed": "usa-based ip addresses is not allowed" in lower
                and ("mt4" in lower or "mt5" in lower),
            }
        )
    elif source_id == "redacted_account_terms_of_service":
        facts.update(
            {
                "policies_incorporated_by_reference": "policies form an integral part" in lower,
                "identity_residence_location_discrepancy_can_trigger_review": "identity, residence/location" in lower,
                "vpn_proxy_vps_misuse_can_trigger_review": "vpn/proxy/vps" in lower,
                "terms_require_policy_compliance": "compliance with these terms and the policies" in lower,
            }
        )
    return facts


def fetch_official_sources(skip_fetch: bool = False) -> dict[str, Any]:
    RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = iso_now()
    entries: list[dict[str, Any]] = []
    for source in OFFICIAL_SOURCES:
        source_id = source["source_id"]
        raw_path = RAW_SOURCE_DIR / f"{source_id}.html.gz"
        text_path = RAW_SOURCE_DIR / f"{source_id}.txt"
        status = "not_fetched"
        final_url = source["url"]
        error = None
        raw = b""
        if skip_fetch and raw_path.exists():
            raw = gzip.decompress(raw_path.read_bytes())
            status = "loaded_existing_capture"
        elif skip_fetch and (RAW_SOURCE_DIR / f"{source_id}.html").exists():
            raw = (RAW_SOURCE_DIR / f"{source_id}.html").read_bytes()
            status = "loaded_existing_legacy_capture"
        else:
            try:
                request = Request(
                    source["url"],
                    headers={
                        "User-Agent": "Mozilla/5.0 GTOS compliant route source capture",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )
                with urlopen(request, timeout=30) as response:
                    raw = response.read()
                    final_url = response.geturl()
                    status = f"fetched_http_{getattr(response, 'status', 'ok')}"
                raw_path.write_bytes(gzip.compress(raw, mtime=0))
            except (OSError, URLError) as exc:
                error = str(exc)
                if raw_path.exists():
                    raw = gzip.decompress(raw_path.read_bytes())
                    status = "fetch_failed_loaded_existing_capture"
                elif (RAW_SOURCE_DIR / f"{source_id}.html").exists():
                    raw = (RAW_SOURCE_DIR / f"{source_id}.html").read_bytes()
                    status = "fetch_failed_loaded_existing_legacy_capture"
                else:
                    status = "fetch_failed_no_capture"
        if raw and not raw_path.exists():
            raw_path.write_bytes(gzip.compress(raw, mtime=0))
        text = html_to_text(raw) if raw else ""
        text_path.write_text(text + "\n", encoding="utf-8")
        facts = extract_policy_facts(source_id, text)
        entries.append(
            {
                "source_id": source_id,
                "required_fact_family": source["required_fact_family"],
                "url": source["url"],
                "final_url": final_url,
                "fetch_timestamp_utc": generated_at,
                "fetch_status": status,
                "fetch_error": error,
                "raw_path": rel(raw_path),
                "raw_sha256": sha256_bytes(raw) if raw else None,
                "raw_storage": "gzip_compressed_exact_response_bytes",
                "raw_gzip_sha256": sha256_file(raw_path) if raw_path.exists() else None,
                "raw_bytes": len(raw),
                "extracted_text_path": rel(text_path),
                "extracted_text_sha256": sha256_bytes(text.encode("utf-8")),
                "extracted_text_bytes": len(text.encode("utf-8")),
                "extracted_policy_facts": facts,
            }
        )
    summary = {
        "schema_version": "official_redacted_account_source_index_v1",
        "generated_at_utc": generated_at,
        "source_use_state": "official_pages_fetched_or_existing_raw_captures_hashed",
        "entries": entries,
    }
    write_json(ROUTE_DIR / "OFFICIAL_redacted_account_SOURCE_INDEX.json", summary)
    return summary


def build_compliance_fact_ledger(index: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {entry["source_id"]: entry for entry in index.get("entries", [])}
    restricted = by_id.get("redacted_account_restricted_countries", {}).get("extracted_policy_facts", {})
    vpn_vps = by_id.get("redacted_account_vpn_vps_policy", {}).get("extracted_policy_facts", {})
    device = by_id.get("redacted_account_device_network_policy", {}).get("extracted_policy_facts", {})
    terms = by_id.get("redacted_account_terms_of_service", {}).get("extracted_policy_facts", {})

    rows = [
        {
            "fact_id": "owner_identity_tunisia_residency_temporary_malaysia_travel",
            "fact_type": "owner_provided_identity_fact",
            "fact_value": {
                "citizenship_or_national_identity": "Tunisian",
                "residency_permanent_address": "Tunisia",
                "malaysia_status": "temporary_travel_only",
                "do_not_reclassify_as_malaysia_resident_without_official_kyc": True,
            },
            "source_ids": ["owner_provided_goal_context"],
            "route_decision": "preserve_as_current_identity_fact_unless_official_kyc_evidence_contradicts_it",
            "downstream_consumer": "VPS_MIGRATION_CONTRACT.md",
        },
        {
            "fact_id": "restricted_country_rule_applies_to_residents_and_citizens",
            "fact_type": "official_policy_fact",
            "fact_value": restricted.get("restricted_basis"),
            "source_ids": ["redacted_account_restricted_countries"],
            "route_decision": "evaluate_true_residency_and_citizenship_not_temporary_travel_label",
            "downstream_consumer": "VPS_STARTUP_VERIFICATION_RUNBOOK.md",
        },
        {
            "fact_id": "restricted_country_list_malaysia_true_tunisia_false",
            "fact_type": "official_policy_fact",
            "fact_value": {
                "malaysia_listed_restricted": bool(restricted.get("malaysia_listed_restricted")),
                "tunisia_listed_restricted": bool(restricted.get("tunisia_listed_restricted")),
                "restricted_countries": restricted.get("restricted_countries") or [],
            },
            "source_ids": ["redacted_account_restricted_countries"],
            "route_decision": "do_not_use_malaysia_network_origin_for_redacted_account_or_mt5_access",
            "downstream_consumer": "VPS_MIGRATION_CONTRACT.md",
        },
        {
            "fact_id": "mt5_usa_ip_not_allowed",
            "fact_type": "official_policy_fact",
            "fact_value": bool(restricted.get("usa_based_ip_for_mt5_not_allowed"))
            or bool(device.get("usa_based_ip_for_mt4_mt5_not_allowed")),
            "source_ids": ["redacted_account_restricted_countries", "redacted_account_device_network_policy"],
            "route_decision": "do_not_select_united_states_vps_for_metaquotes_mt5_access",
            "downstream_consumer": "DEFAULT_OFF_EXPORT_SCRIPT_MANIFEST.json",
        },
        {
            "fact_id": "vps_private_dedicated_non_shared_fee_and_trade_taking_ea_rules",
            "fact_type": "official_policy_fact",
            "fact_value": {
                "vps_allowed_with_fee": bool(vpn_vps.get("vps_allowed_with_fee")),
                "private_dedicated_vps_required": bool(vpn_vps.get("private_dedicated_vps_required")),
                "shared_vps_prohibited": bool(vpn_vps.get("shared_vps_prohibited")),
                "trade_taking_ea_required_for_vps": bool(vpn_vps.get("trade_taking_ea_required_for_vps")),
                "manual_trading_through_vps_prohibited": bool(vpn_vps.get("manual_trading_through_vps_prohibited")),
                "broker_sponsored_vps_prohibited": bool(vpn_vps.get("broker_sponsored_vps_prohibited")),
                "addon_or_fee_required_when_applicable": bool(
                    vpn_vps.get("vps_ea_addon_or_fee_required_when_applicable")
                ),
            },
            "source_ids": ["redacted_account_vpn_vps_policy"],
            "route_decision": "future_vps_must_be_private_dedicated_non_restricted_non_us_for_mt5_and_document_vps_ea_fee_state",
            "downstream_consumer": "MT5_EXPORT_READINESS_CHECKLIST.json",
        },
        {
            "fact_id": "device_and_network_personal_device_non_restricted_ip",
            "fact_type": "official_policy_fact",
            "fact_value": {
                "personal_device_only": bool(device.get("personal_device_only")),
                "shared_device_prohibited": bool(device.get("shared_device_prohibited")),
                "network_allowed_if_ip_not_restricted": bool(device.get("network_allowed_if_ip_not_restricted")),
                "vpn_must_follow_country_ip_restrictions": bool(
                    device.get("vpn_must_follow_country_ip_restrictions")
                ),
            },
            "source_ids": ["redacted_account_device_network_policy"],
            "route_decision": "local_machine_in_malaysia_is_research_control_only_until_network_origin_compliance_is_proven",
            "downstream_consumer": "VPS_STARTUP_VERIFICATION_RUNBOOK.md",
        },
        {
            "fact_id": "terms_policy_identity_and_platform_controls",
            "fact_type": "official_terms_fact",
            "fact_value": {
                "policies_incorporated": bool(terms.get("policies_incorporated_by_reference")),
                "identity_residence_location_discrepancy_review": bool(
                    terms.get("identity_residence_location_discrepancy_can_trigger_review")
                ),
                "vpn_proxy_vps_misuse_review": bool(terms.get("vpn_proxy_vps_misuse_can_trigger_review")),
            },
            "source_ids": ["redacted_account_terms_of_service"],
            "route_decision": "artifacts_must_preserve_true_identity_residency_and_compliant_infrastructure_only",
            "downstream_consumer": "COMPLETION_AUDIT.json",
        },
    ]
    write_jsonl(ROUTE_DIR / "COMPLIANCE_FACT_LEDGER.jsonl", rows)
    return rows


def discover_required_roots() -> list[dict[str, Any]]:
    explicit = [
        ("data", "all_local_market_data_roots"),
        ("data/ticks", "tick_capture_bid_ask_paths"),
        ("data/m1", "continuous_closed_m1_forward_capture"),
        ("data/m5", "normalized_m5_root_absence_or_export_requirement"),
        ("data/m15", "normalized_m15_root_absence_or_export_requirement"),
        ("data/h1", "normalized_h1_root_absence_or_export_requirement"),
        ("data/h4", "normalized_h4_root_absence_or_export_requirement"),
        ("data/d1", "normalized_d1_root_absence_or_export_requirement"),
        ("data/spreads", "normalized_spread_root_absence_or_export_requirement"),
        ("data/bid_ask", "normalized_bid_ask_root_absence_or_export_requirement"),
        ("data/symbol_specs", "normalized_symbol_spec_root_absence_or_export_requirement"),
        ("data/mt5_logs", "normalized_mt5_log_root_absence_or_export_requirement"),
        ("data/mt5_exports", "normalized_mt5_export_root_absence_or_export_requirement"),
        ("exports", "legacy_export_surfaces"),
        ("logs", "runtime_log_surfaces"),
        ("mt5_ea", "local_ea_source_surface"),
        ("shadow_logs", "runtime_shadow_decision_and_lifecycle_logs"),
        ("pipeline_state", "hot_runtime_state_and_heartbeats"),
        ("knowledge_base", "trade_records_and_monitoring_state"),
        ("config", "active_config_and_broker_profiles"),
        ("src", "active_runtime_source_code"),
        ("tests", "local_test_contracts"),
        (".context/00_core", "current_context_authority"),
        ("research/science_program_2026_05/04_goal_prompts", "goal_prompt_pack"),
        ("research/operations/vnext_live_activation_active_repair_companion_2026_05_28", "current_live_companion"),
        (
            "research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31",
            "friday_microscope_route",
        ),
        ("research/operations/vnext_next_level_master_orchestration_2026_05_31", "next_level_master_orchestration"),
        (
            "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27",
            "activation_repair_hardening_route",
        ),
        (
            "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26",
            "activation_market_source_and_broker_geometry_route",
        ),
    ]
    for path in sorted((REPO_ROOT / "research/operations").glob("vnext_lane*_2026_05_31")):
        explicit.append((rel(path), "next_level_lane_output"))
    explicit.append((rel(ROUTE_DIR), "current_route_outputs"))
    seen: set[str] = set()
    roots = []
    for path, purpose in explicit:
        normalized = path.replace("/", "\\")
        if normalized in seen:
            continue
        seen.add(normalized)
        roots.append({"path": normalized, "purpose": purpose})
    return roots


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def is_probably_secret_path(path: Path) -> bool:
    return any(SECRET_NAME_RE.search(part) for part in path.parts)


def safe_sample_bytes(path: Path, max_bytes: int = 256 * 1024) -> bytes:
    try:
        with path.open("rb") as handle:
            first = handle.read(max_bytes // 2)
            if path.stat().st_size > max_bytes:
                handle.seek(max(0, path.stat().st_size - max_bytes // 2))
                return first + b"\n" + handle.read(max_bytes // 2)
            return first
    except OSError:
        return b""


def line_count_if_practical(path: Path, size: int) -> int | None:
    if path.suffix.lower() not in TEXT_EXTENSIONS or size > 64 * 1024 * 1024:
        return None
    try:
        count = 0
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                count += chunk.count(b"\n")
        return count
    except OSError:
        return None


def schema_preview(path: Path, size: int) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if is_probably_secret_path(path):
        return {"preview_status": "redacted_path_name_matches_secret_pattern"}
    if suffix == ".json" and size <= 16 * 1024 * 1024:
        value = read_json(path, default=None)
        if isinstance(value, dict):
            return {"top_level_type": "object", "top_level_keys": sorted(map(str, value.keys()))[:40]}
        if isinstance(value, list):
            item_keys = []
            if value and isinstance(value[0], dict):
                item_keys = sorted(map(str, value[0].keys()))[:40]
            return {"top_level_type": "array", "array_length": len(value), "first_item_keys": item_keys}
        return {"top_level_type": type(value).__name__ if value is not None else "unparsed"}
    if suffix == ".jsonl":
        keys: set[str] = set()
        rows = 0
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if rows >= 5:
                        break
                    if not line.strip():
                        continue
                    rows += 1
                    value = json.loads(line)
                    if isinstance(value, dict):
                        keys.update(map(str, value.keys()))
        except (OSError, json.JSONDecodeError):
            return {"top_level_type": "jsonl", "preview_status": "parse_failed_in_first_rows"}
        return {"top_level_type": "jsonl", "sampled_rows": rows, "sample_keys": sorted(keys)[:60]}
    if suffix == ".csv":
        try:
            first = path.open("r", encoding="utf-8", errors="replace").readline().strip()
        except OSError:
            first = ""
        return {"top_level_type": "csv", "header": first[:500]}
    return {"top_level_type": suffix.lstrip(".") or "file", "preview_status": "schema_not_applicable"}


def path_symbols(path: Path, sample: bytes) -> list[str]:
    text = rel(path) + "\n" + sample.decode("utf-8", errors="ignore")
    found = {match.group(1).upper().replace("_CASH", "_cash") for match in SYMBOL_TOKEN_RE.finditer(text)}
    return sorted(symbol for symbol in ACTIVE_SYMBOLS if symbol.upper() in {item.upper() for item in found})


def path_time_coverage(path: Path, sample: bytes) -> dict[str, Any]:
    text = rel(path) + "\n" + sample.decode("utf-8", errors="ignore")
    values = sorted(set(DATE_RE.findall(text)))
    return {
        "date_values_sampled": values[:10],
        "date_min_sampled": values[0] if values else None,
        "date_max_sampled": values[-1] if values else None,
    }


def classify_retention(path: Path, root_purpose: str) -> tuple[str, list[str]]:
    rel_path = rel(path).replace("/", "\\")
    lower = rel_path.lower()
    if lower.startswith("data\\ticks"):
        return "hot_market_tick_evidence_preserve", ["tick_replay", "execution_microstructure", "ml_feature_store"]
    if lower.startswith("data\\m1"):
        return "hot_market_m1_evidence_preserve", ["m1_path_replay", "candidate_path_ordering", "ml_feature_store"]
    if lower.startswith("data\\"):
        return "market_data_preserve", ["historical_microscope", "replay", "selector_validation"]
    if lower.startswith("shadow_logs\\"):
        return "hot_runtime_shadow_log_preserve", ["candidate_lifecycle_truth", "selector_scheduler_execution_forensics"]
    if lower.startswith("pipeline_state\\"):
        return "hot_runtime_state_preserve", ["startup_verification", "capture_health", "broker_truth_join"]
    if lower.startswith("knowledge_base\\"):
        return "trade_record_and_monitoring_preserve", ["vnext_candidate_packets", "trade_record_reproducibility"]
    if lower.startswith(("config\\", "src\\", "tests\\")):
        return "active_code_config_test_preserve", ["broker_portability", "startup_verification", "default_off_tooling"]
    if lower.startswith(".context\\"):
        return "current_context_preserve", ["agent_preflight", "stale_context_control"]
    if "vnext_lane" in lower or "vnext_friday" in lower or "vnext_live_activation" in lower:
        return "current_vnext_route_evidence_preserve", ["next_level_lanes", "friday_microscope", "broker_lifecycle_truth"]
    if "official_sources" in lower:
        return "official_policy_capture_preserve", ["compliance_fact_ledger", "vps_migration_contract"]
    if root_purpose == "current_route_outputs":
        return "route_output_preserve", ["route_verification", "future_resume"]
    return "research_evidence_preserve", ["absolute_moonshot_research"]


def inventory_file(path: Path, root: dict[str, Any], tracked: set[str], statuses: dict[str, str]) -> dict[str, Any]:
    stat = path.stat()
    sample = b"" if is_probably_secret_path(path) else safe_sample_bytes(path)
    retention, downstream = classify_retention(path, root["purpose"])
    rel_path = rel(path)
    row: dict[str, Any] = {
        "schema_version": "local_evidence_inventory_v1",
        "path": rel_path,
        "root_path": root["path"],
        "root_purpose": root["purpose"],
        "type": "file",
        "bytes": stat.st_size,
        "modified_time_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "tracked_status": "tracked" if rel_path in tracked else statuses.get(rel_path, "untracked_or_ignored"),
        "line_count": line_count_if_practical(path, stat.st_size),
        "schema_preview": schema_preview(path, stat.st_size),
        "symbol_coverage": path_symbols(path, sample),
        "time_coverage": path_time_coverage(path, sample),
        "retention_class": retention,
        "downstream_use": downstream,
        "secret_redaction_policy": "content_not_sampled_due_path_name" if is_probably_secret_path(path) else "no_secret_value_extraction",
    }
    row.update(file_hash_record(path))
    return row


def discover_external_mt5_roots() -> list[dict[str, Any]]:
    home = Path.home()
    candidates = [
        home / "AppData/Roaming/MetaQuotes/Terminal",
        home / "AppData/Roaming/MetaQuotes/Terminal/Common/Files",
        home / "AppData/Roaming/MetaQuotes/Terminal/Common/Logs",
        home / "AppData/Local/MetaQuotes/Terminal",
        Path("C:/Program Files/MetaTrader 5"),
        Path("C:/Program Files (x86)/MetaTrader 5"),
    ]
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows.append(
            {
                "schema_version": "local_evidence_inventory_v1",
                "path": str(candidate),
                "root_path": str(candidate),
                "root_purpose": "external_mt5_terminal_or_export_root",
                "type": "external_directory_presence",
                "exists": candidate.exists(),
                "tracked_status": "outside_git",
                "retention_class": "external_mt5_presence_or_export_requirement",
                "downstream_use": ["MT5_EXPORT_READINESS_CHECKLIST.json", "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl"],
                "secret_redaction_policy": "presence_only_no_file_content_or_credentials",
            }
        )
    terminal_root = candidates[0]
    if terminal_root.exists():
        for subdir in terminal_root.glob("*"):
            if not subdir.is_dir():
                continue
            for rel_sub in ["MQL5/Files", "MQL5/Logs", "logs", "Logs", "bases"]:
                safe_dir = subdir / rel_sub
                if safe_dir.exists():
                    rows.append(
                        {
                            "schema_version": "local_evidence_inventory_v1",
                            "path": str(safe_dir),
                            "root_path": str(terminal_root),
                            "root_purpose": "external_mt5_terminal_safe_export_or_log_subdir",
                            "type": "external_directory_presence",
                            "exists": True,
                            "tracked_status": "outside_git",
                            "retention_class": "external_mt5_export_or_log_presence",
                            "downstream_use": [
                                "MT5_EXPORT_READINESS_CHECKLIST.json",
                                "VPS_STARTUP_VERIFICATION_RUNBOOK.md",
                            ],
                            "secret_redaction_policy": "presence_only_no_file_content_or_credentials",
                        }
                    )
    return rows


def build_local_inventory() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    roots = discover_required_roots()
    tracked = tracked_paths()
    statuses = status_map()
    rows: list[dict[str, Any]] = []
    root_summaries: list[dict[str, Any]] = []
    for root in roots:
        root_path = REPO_ROOT / root["path"]
        if not root_path.exists():
            rows.append(
                {
                    "schema_version": "local_evidence_inventory_v1",
                    "path": root["path"],
                    "root_path": root["path"],
                    "root_purpose": root["purpose"],
                    "type": "required_root_absent",
                    "exists": False,
                    "retention_class": "missing_source_export_requirement",
                    "downstream_use": ["MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl"],
                }
            )
            root_summaries.append({"root_path": root["path"], "purpose": root["purpose"], "exists": False, "files": 0, "bytes": 0})
            continue
        file_count = 0
        byte_count = 0
        for file_path in root_path.rglob("*"):
            if should_skip(file_path) or not file_path.is_file():
                continue
            try:
                row = inventory_file(file_path, root, tracked, statuses)
            except OSError as exc:
                row = {
                    "schema_version": "local_evidence_inventory_v1",
                    "path": rel(file_path),
                    "root_path": root["path"],
                    "root_purpose": root["purpose"],
                    "type": "file_unreadable",
                    "error": str(exc),
                    "retention_class": "preserve_with_read_error",
                    "downstream_use": ["MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl"],
                }
            rows.append(row)
            file_count += 1
            byte_count += int(row.get("bytes") or 0)
        root_summaries.append(
            {
                "root_path": root["path"],
                "purpose": root["purpose"],
                "exists": True,
                "files": file_count,
                "bytes": byte_count,
            }
        )
    rows.extend(discover_external_mt5_roots())

    symbol_counter: Counter[str] = Counter()
    retention_counter: Counter[str] = Counter()
    timeframe_by_symbol: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        retention_counter[str(row.get("retention_class"))] += 1
        for symbol in row.get("symbol_coverage") or []:
            symbol_counter[symbol] += 1
        path = str(row.get("path") or "")
        for symbol in ACTIVE_SYMBOLS:
            if symbol.upper() in path.upper():
                for tf in ["TICK", "M1", "M5", "M15", "H1", "H4", "D1"]:
                    if re.search(rf"(^|[_\\/.-]){tf}([_\\/.-]|$)", path, flags=re.I):
                        timeframe_by_symbol[symbol].add(tf)
    summary = {
        "schema_version": "local_evidence_coverage_summary_v1",
        "generated_at_utc": iso_now(),
        "inventory_rows": len(rows),
        "file_rows": sum(1 for row in rows if row.get("type") == "file"),
        "required_root_summaries": root_summaries,
        "retention_class_counts": dict(sorted(retention_counter.items())),
        "symbol_file_reference_counts": {symbol: symbol_counter.get(symbol, 0) for symbol in ACTIVE_SYMBOLS},
        "timeframe_coverage_by_symbol": {
            symbol: sorted(timeframe_by_symbol.get(symbol, set())) for symbol in ACTIVE_SYMBOLS
        },
        "external_mt5_presence_rows": [
            row for row in rows if str(row.get("type", "")).startswith("external_directory")
        ],
        "coverage_decision": "required_local_surfaces_inventory_written_absent_surfaces_emit_export_requirements",
    }
    write_jsonl(ROUTE_DIR / "LOCAL_EVIDENCE_INVENTORY.jsonl", rows)
    write_json(ROUTE_DIR / "LOCAL_EVIDENCE_COVERAGE_SUMMARY.json", summary)
    return rows, summary


def build_retention_rows(inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for row in inventory_rows:
        key = (str(row.get("root_path")), str(row.get("retention_class")))
        item = groups.setdefault(
            key,
            {
                "schema_version": "data_surface_retention_decision_v1",
                "root_path": row.get("root_path"),
                "retention_class": row.get("retention_class"),
                "file_count": 0,
                "bytes": 0,
                "downstream_use": set(),
            },
        )
        if row.get("type") == "file":
            item["file_count"] += 1
            item["bytes"] += int(row.get("bytes") or 0)
        for use in row.get("downstream_use") or []:
            item["downstream_use"].add(use)
    rows = []
    for item in groups.values():
        downstream = sorted(item.pop("downstream_use"))
        decision = "preserve_and_export_with_hash_manifest"
        if item["retention_class"] == "missing_source_export_requirement":
            decision = "record_absence_and_export_requirement"
        if str(item["retention_class"]).startswith("external_mt5"):
            decision = "presence_only_now_future_compliant_export_required"
        item.update(
            {
                "decision": decision,
                "compression_decision": "do_not_compress_hot_evidence_in_this_route",
                "manifest_feed": "OUTPUT_MANIFEST.json",
                "verifier_feed": "VERIFICATION_RESULT.json",
                "downstream_use": downstream,
            }
        )
        rows.append(item)
    rows.sort(key=lambda row: (str(row.get("root_path")), str(row.get("retention_class"))))
    write_jsonl(ROUTE_DIR / "DATA_SURFACE_RETENTION_DECISION_LEDGER.jsonl", rows)
    return rows


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}


def effective_symbol_config(symbol: str) -> dict[str, Any]:
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from src.utils.config import apply_instrument_overrides, apply_profile_overrides

        base = load_yaml(REPO_ROOT / "config/agent_config.yaml")
        profiled = apply_profile_overrides(base, "redacted_account")
        return apply_instrument_overrides(profiled, symbol)
    except Exception:
        profile = load_yaml(REPO_ROOT / "config/profiles/redacted_account.yaml")
        base = load_yaml(REPO_ROOT / "config/agent_config.yaml")
        instruments = base.get("instruments") or {}
        profile_instruments = profile.get("instruments") or {}
        block = dict(instruments.get(symbol) or {})
        overlay = profile_instruments.get(symbol) or {}
        for key, value in overlay.items():
            if isinstance(value, dict) and isinstance(block.get(key), dict):
                merged = dict(block[key])
                merged.update(value)
                block[key] = merged
            else:
                block[key] = value
        return block


def asset_class(symbol: str) -> str:
    if symbol.endswith("JPY") or symbol in {"AUDUSD", "EURGBP", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF"}:
        return "fx"
    if symbol in {"XAUUSD", "XAGUSD"}:
        return "metals_cfd"
    if symbol in {"UKOIL_cash", "USOIL_cash"}:
        return "energy_cfd"
    if symbol in {"BTCUSD", "ETHUSD"}:
        return "crypto_cfd"
    return "index_cfd"


def live_symbol_specs() -> dict[str, dict[str, Any]]:
    path = ROUTE_DIR.parents[0] / "vnext_live_activation_active_repair_companion_2026_05_28" / "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl"
    return {row.get("symbol"): row for row in read_jsonl(path) if row.get("symbol")}


def build_broker_portability() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    specs = live_symbol_specs()
    rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    detailed_symbol_info_fields = [
        "trade_tick_size",
        "trade_tick_value",
        "trade_tick_value_profit",
        "trade_tick_value_loss",
        "trade_calc_mode",
        "currency_base",
        "currency_profit",
        "currency_margin",
        "margin_initial",
        "margin_maintenance",
        "margin_hedged",
        "filling_mode",
        "order_mode",
        "expiration_mode",
    ]
    portable_schedule_cost_fields = [
        "broker_trading_sessions_by_weekday",
        "broker_holiday_calendar",
        "server_timezone_and_dst",
        "commission_schedule",
        "swap_long_short_mode_triple_day_rollover",
        "time_varying_spread_samples",
        "time_varying_stop_freeze_samples",
        "full_order_deal_position_lifecycle_export",
    ]
    for symbol in ACTIVE_SYMBOLS:
        cfg = effective_symbol_config(symbol)
        market = cfg.get("market") if isinstance(cfg.get("market"), dict) else {}
        risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
        spec = specs.get(symbol, {})
        broker_symbol = spec.get("broker_symbol") or market.get("mt5_symbol") or market.get("symbol") or symbol
        contract_size = spec.get("trade_contract_size") or risk.get("contract_size")
        tick_size = spec.get("trade_tick_size") or spec.get("point") or market.get("tick_size")
        tick_value = spec.get("trade_tick_value")
        point_value = None
        if tick_value is not None and tick_size:
            try:
                point_value = float(tick_value) / float(tick_size)
            except (TypeError, ValueError, ZeroDivisionError):
                point_value = None
        missing = []
        for field, value in {
            "trade_tick_size": spec.get("trade_tick_size"),
            "tick_value": tick_value,
            "point_value": point_value,
        }.items():
            if value in (None, "", []):
                missing.append(field)
        missing.extend(portable_schedule_cost_fields)
        missing.extend(
            field
            for field in detailed_symbol_info_fields
            if field not in {"trade_tick_size", "trade_tick_value"} and spec.get(field) in (None, "", [])
        )
        row = {
            "canonical_gtos_symbol": symbol,
            "redacted_account_broker_native_symbol": broker_symbol,
            "asset_class": asset_class(symbol),
            "contract_size": contract_size,
            "tick_size": tick_size,
            "tick_value": tick_value,
            "point_value": point_value,
            "min_lot": spec.get("volume_min"),
            "max_lot": spec.get("volume_max"),
            "lot_step": spec.get("volume_step"),
            "stops_level": spec.get("trade_stops_level"),
            "freeze_level": spec.get("trade_freeze_level"),
            "sessions_or_hours": market.get("kill_zones") or {},
            "commission_availability": "captured_in_lane06_for_real_deals_when_symbol_traded"
            if symbol in {"NAS100", "XAUUSD"}
            else "requires_future_broker_history_or_symbol_spec_export",
            "swap_availability": "captured_in_lane06_open_positions_when_symbol_traded"
            if symbol in {"NAS100", "XAUUSD"}
            else "requires_future_broker_history_or_symbol_spec_export",
            "spread_evidence_availability": "live_symbol_spec_spread_price" if spec.get("spread_price") is not None else "requires_export",
            "current_data_roots": [
                root
                for root in [
                    f"data/ticks/{symbol}",
                    f"data/m1/{symbol}",
                    f"data/historical_2026/{symbol}_M15.csv",
                    f"data/mt5_research_exports",
                    "shadow_logs",
                ]
                if (REPO_ROOT / root).exists() or root == "shadow_logs"
            ],
            "missing_broker_specific_fields": sorted(set(missing)),
            "migration_risk": "medium_requires_broker_native_spec_reverification_on_target_vps_or_future_broker"
            if missing
            else "low_reverify_on_target_vps",
            "future_broker_mapping_requirement": "do_not_assume_symbol_name_contract_size_tick_value_sessions_costs_or_fill_model_match_redacted_account",
            "source_refs": [rel(REPO_ROOT / "config/profiles/redacted_account.yaml"), rel(REPO_ROOT / "config/agent_config.yaml")],
        }
        if spec:
            row["source_refs"].append(
                rel(
                    ROUTE_DIR.parents[0]
                    / "vnext_live_activation_active_repair_companion_2026_05_28"
                    / "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl"
                )
            )
        rows.append(row)
        for field in sorted(set(missing)):
            gap_rows.append(
                {
                    "schema_version": "broker_portability_gap_v1",
                    "symbol": symbol,
                    "broker_symbol": broker_symbol,
                    "missing_field": field,
                    "risk": "future_broker_or_vps_migration_cannot_assume_redacted_account_current_value",
                    "required_export": (
                        "read_only_symbol_info_session_cost_spread_swap_and_account_history_export_"
                        "from_compliant_non_restricted_non_us_mt5_origin"
                    ),
                    "feeds": ["BROKER_PORTABILITY_MAP.json", "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl"],
                }
            )
    output = {
        "schema_version": "broker_portability_map_v1",
        "generated_at_utc": iso_now(),
        "broker": "redacted_account current profile",
        "canonical_symbol_count": len(rows),
        "symbols": rows,
    }
    write_json(ROUTE_DIR / "BROKER_PORTABILITY_MAP.json", output)
    write_jsonl(ROUTE_DIR / "BROKER_PORTABILITY_GAP_LEDGER.jsonl", gap_rows)
    return output, gap_rows


def build_missing_export_requirements(summary: dict[str, Any], gap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    timeframe_by_symbol = summary.get("timeframe_coverage_by_symbol") or {}
    for symbol in ACTIVE_SYMBOLS:
        have = set(timeframe_by_symbol.get(symbol) or [])
        missing_tfs = [tf for tf in ["TICK", "M1", "M5", "M15", "H1", "H4", "D1"] if tf not in have]
        if missing_tfs:
            rows.append(
                {
                    "schema_version": "missing_source_export_requirement_v1",
                    "requirement_id": f"market_data_{symbol}_missing_timeframes",
                    "source_family": "market_data",
                    "symbol": symbol,
                    "missing_fields_or_windows": missing_tfs,
                    "required_action": "export_or_capture_missing_timeframes_from_compliant_non_restricted_non_us_mt5_origin_or_approved_alternate_source",
                    "proof_required": "file_hashes_row_counts_time_coverage_and_source_contract",
                    "consumer": "ABSOLUTE_MOONSHOT_DATA_REQUIREMENT_MAP.json",
                }
            )
    rows.extend(
        [
            {
                "schema_version": "missing_source_export_requirement_v1",
                "requirement_id": "redacted_account_vps_ea_addon_or_fee_proof",
                "source_family": "compliance",
                "required_action": "owner_capture_support_or_dashboard_proof_that_vps_ea_usage_is permitted_for_the_account",
                "proof_required": "dated_screenshot_or_written_support_confirmation_saved_without_secrets",
                "consumer": "VPS_MIGRATION_CONTRACT.md",
            },
            {
                "schema_version": "missing_source_export_requirement_v1",
                "requirement_id": "vps_public_ip_country_provider_dedicated_proof",
                "source_family": "network_origin_compliance",
                "required_action": "capture_public_ip_country_provider_and_dedicated_private_vps_evidence_before_any_mt5_server_access",
                "proof_required": "ip_country_json_provider_invoice_or_panel_evidence_with_secrets_redacted",
                "consumer": "VPS_STARTUP_VERIFICATION_RUNBOOK.md",
            },
            {
                "schema_version": "missing_source_export_requirement_v1",
                "requirement_id": "full_mt5_account_orders_deals_positions_export",
                "source_family": "broker_lifecycle_truth",
                "required_action": "run_read_only_history_orders_deals_positions_export_from_compliant_vps_before_live_runtime_start",
                "proof_required": "orders_deals_positions_jsonl_hash_manifest_no_order_send_calls",
                "consumer": "BROKER_PORTABILITY_MAP.json",
            },
            {
                "schema_version": "missing_source_export_requirement_v1",
                "requirement_id": "alternate_broker_symbol_contract_cost_map",
                "source_family": "broker_portability",
                "required_action": "for any future broker export symbol_info sessions costs swaps commissions fill_mode stop_freeze_and_contract_geometry",
                "proof_required": "per_symbol_read_only_spec_export_and_mapping_diff_against_canonical_gtos_symbols",
                "consumer": "BROKER_PORTABILITY_GAP_LEDGER.jsonl",
            },
        ]
    )
    for gap in gap_rows:
        rows.append(
            {
                "schema_version": "missing_source_export_requirement_v1",
                "requirement_id": f"broker_field_{gap['symbol']}_{gap['missing_field']}",
                "source_family": "broker_specific_symbol_geometry",
                "symbol": gap["symbol"],
                "missing_fields_or_windows": [gap["missing_field"]],
                "required_action": gap["required_export"],
                "proof_required": "read_only_symbol_info_export_hash_and_source_timestamp",
                "consumer": "BROKER_PORTABILITY_MAP.json",
            }
        )
    write_jsonl(ROUTE_DIR / "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl", rows)
    return rows


def build_mt5_checklist() -> dict[str, Any]:
    checklist = {
        "schema_version": "mt5_export_readiness_checklist_v1",
        "generated_at_utc": iso_now(),
        "default_state": "off_no_mt5_server_access_performed_by_this_route",
        "required_before_any_mt5_server_access": [
            "public_ip_country_not_restricted",
            "public_ip_country_not_united_states_for_mt5",
            "dedicated_private_vps_proof",
            "redacted_account VPS/EA add-on or fee status documented when applicable",
            "secrets available locally without printing values",
        ],
        "read_only_export_steps": [
            "symbol_info for all 24 canonical symbols and redacted_account aliases",
            "history_orders_get and history_deals_get for approved date window",
            "positions_get and orders_get snapshot before runtime start",
            "M1/M5/M15/H1/H4/D1 bars for all symbols and needed windows",
            "tick capture health snapshot and hash manifest",
        ],
        "forbidden_calls": ["order_send", "order_check for trade placement", "position close", "order cancel", "live runtime start"],
        "status": "ready_as_default_off_plan_requires_compliant_vps_proof_before_execute_readonly",
    }
    write_json(ROUTE_DIR / "MT5_EXPORT_READINESS_CHECKLIST.json", checklist)
    return checklist


def build_default_off_manifest() -> dict[str, Any]:
    script = rel(ROUTE_DIR / "default_off_vps_tools.py")
    commands = [
        ("source_inventory", "python " + script + " source-inventory --repo-root . --json"),
        ("mt5_symbol_spec_export_readiness", "python " + script + " mt5-readiness-plan --json"),
        ("broker_history_export_verifier", "python " + script + " broker-history-export-verify --input <export.jsonl> --json"),
        ("tick_m1_m15_capture_health", "python " + script + " capture-health --repo-root . --json"),
        ("evidence_package_hash_verifier", "python " + script + " hash-verify --manifest research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01/OUTPUT_MANIFEST.json --json"),
        ("startup_preflight_verifier", "python " + script + " startup-preflight --network-origin-json <origin.json> --json"),
    ]
    manifest = {
        "schema_version": "default_off_export_script_manifest_v1",
        "generated_at_utc": iso_now(),
        "default_off": True,
        "no_broker_changing_actions": True,
        "no_live_runtime_start": True,
        "mt5_server_access_default": False,
        "network_origin_refusal_policy": {
            "restricted_country_refuses": True,
            "united_states_refuses_for_mt5": True,
            "requires_explicit_execute_readonly_flag_for_mt5_access": True,
        },
        "script": script,
        "commands": [
            {
                "script_role": role,
                "command_template": command,
                "writes_broker_state": False,
                "requires_explicit_execute_readonly_for_server_access": role
                in {"mt5_symbol_spec_export_readiness", "broker_history_export_verifier"},
            }
            for role, command in commands
        ],
    }
    write_json(ROUTE_DIR / "DEFAULT_OFF_EXPORT_SCRIPT_MANIFEST.json", manifest)
    return manifest


def build_moonshot_map(missing_rows: list[dict[str, Any]]) -> dict[str, Any]:
    data = {
        "schema_version": "absolute_moonshot_data_requirement_map_v1",
        "generated_at_utc": iso_now(),
        "programs": [
            {
                "program": "historical_microscopic_replay_at_scale",
                "local_evidence": ["data/ticks", "data/m1", "data/historical_2026", "research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"],
                "missing_requirement_ids": [
                    row["requirement_id"] for row in missing_rows if row.get("source_family") == "market_data"
                ],
            },
            {
                "program": "feature_store_and_label_store",
                "local_evidence": ["shadow_logs", "knowledge_base", "pipeline_state", "research/operations/vnext_lane01*_2026_05_31", "research/operations/vnext_lane04*_2026_05_31"],
                "missing_requirement_ids": ["full_mt5_account_orders_deals_positions_export"],
            },
            {
                "program": "broker_truth_cost_execution_policy",
                "local_evidence": ["research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31", "research/operations/vnext_lane08_execution_policy_microstructure_stress_2026_05_31"],
                "missing_requirement_ids": [
                    row["requirement_id"]
                    for row in missing_rows
                    if row.get("source_family") in {"broker_lifecycle_truth", "broker_specific_symbol_geometry"}
                ],
            },
            {
                "program": "selector_scheduler_command_center",
                "local_evidence": ["research/operations/vnext_lane03_meta_selector_discovery_implementation_2026_05_31", "research/operations/vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31", "config", "src", "tests"],
                "missing_requirement_ids": ["alternate_broker_symbol_contract_cost_map"],
            },
        ],
        "decision": "preserve_local_evidence_now_and_require_exact_compliant_exports_for_nonlocal_broker_or_network_proofs",
    }
    write_json(ROUTE_DIR / "ABSOLUTE_MOONSHOT_DATA_REQUIREMENT_MAP.json", data)
    return data


def write_markdown_docs() -> None:
    contract = f"""# VPS Migration Contract

Generated: {iso_now()}

## Scope

This route prepares compliant infrastructure and data preservation only. It does not start the live runtime, connect to MT5, change credentials, or perform broker/order/deal/position actions.

## Identity And Residency Basis

- Owner-provided fact: the owner is Tunisian with Tunisia residency/permanent address.
- Owner-provided fact: Malaysia is temporary travel only.
- Do not classify the owner as Malaysia resident or citizen unless official KYC evidence says so.
- Do not invent United States residency, citizenship, or broker eligibility.

## redacted_account/VPS Compatibility Contract

- VPS must be private/dedicated and use a stable dedicated IP.
- VPS country/IP must not be on redacted_account's restricted-country list.
- VPS country/IP must not be the United States when using MetaQuotes/MT5 access.
- Shared VPS use is incompatible with this route.
- Broker-sponsored MetaTrader VPS use is incompatible with this route.
- Manual trading through the VPS is incompatible with this route.
- VPS use must be tied to the trade-taking EA/system requirement where redacted_account policy requires it.
- redacted_account VPS/EA add-on or fee state must be documented before any MT5 server access.
- Any inaccurate residency, inaccurate nationality, inaccurate identity, restricted-country IP, shared VPS, or identity/location misstatement is a hard stop.

## Machine Roles

- Local machine while traveling: development, research, source inventory, and control artifacts only unless network-origin compliance is proven before broker access.
- VPS machine: read-only export first, then dry-run verifier, then a separate owner-approved live-ops action for any runtime start.

## Support Confirmation Slot

Save any written redacted_account support confirmation under this route with secrets redacted, then add it to `OFFICIAL_redacted_account_SOURCE_INDEX.json` or a follow-up support-confirmation ledger.
"""
    runbook = f"""# VPS Startup Verification Runbook

Generated: {iso_now()}

Run this before any future live runtime start on a compliant VPS. This runbook is default-off and read-only until the owner separately approves live operations.

1. Regenerate `LIVE_STATE.md` and record current `git rev-parse HEAD`.
2. Confirm the worktree is clean or that uncommitted changes are scoped and understood.
3. Confirm identity/residency framing: Tunisian owner, Tunisia residency/permanent address, Malaysia temporary travel only unless official KYC evidence says otherwise.
4. Capture public IP country and provider. It must not be a restricted country and must not be the United States for MT5.
5. Confirm the VPS is private/dedicated with a stable dedicated IP.
6. Document redacted_account VPS/EA add-on or fee state where applicable.
7. Confirm secrets exist without printing values.
8. Verify MT5 terminal/account in read-only mode first: symbol specs, positions, orders, history orders, and history deals.
9. Verify the 24-symbol canonical surface and broker aliases in `BROKER_PORTABILITY_MAP.json`.
10. Verify config points to the vNext/moonshot replacement, current next-level package artifacts, Lane03 selector, Lane05 scheduler, Lane06 broker truth, and Lane08 execution policy evidence.
11. Confirm log, data, tick, M1, and export directories exist and are writable.
12. Start data capture before any trading runtime.
13. Run default-off dry-run checks from `DEFAULT_OFF_EXPORT_SCRIPT_MANIFEST.json`.
14. Keep live broker actions blocked until the owner explicitly approves a separate runtime start.

Hard stops: restricted-country IP, United States IP for MT5, shared VPS, missing VPS/EA fee proof where required, missing symbol specs, missing secrets, stale HEAD, failed dry-run verifier, or any request to perform broker-changing action inside this route.
"""
    (ROUTE_DIR / "VPS_MIGRATION_CONTRACT.md").write_text(contract, encoding="utf-8")
    (ROUTE_DIR / "VPS_STARTUP_VERIFICATION_RUNBOOK.md").write_text(runbook, encoding="utf-8")


def write_context_anchor(index: dict[str, Any]) -> dict[str, Any]:
    anchor = {
        "schema_version": "route_context_anchor_v1",
        "route_id": ROUTE_DIR.name,
        "generated_at_utc": iso_now(),
        "git": git_head(),
        "prompt_path": PROMPT_PATH,
        "starter_path": STARTER_PATH,
        "route_dir": rel(ROUTE_DIR),
        "evidence_class": "local_evidence_preservation_official_source_capture_broker_portability_vps_migration_readiness_default_off_verification",
        "forbidden_surfaces": {
            "live_broker_order_deal_position_action": False,
            "live_runtime_start": False,
            "restricted_country_mt5_or_redacted_account_server_access": False,
            "paid_api_vendor_call": False,
            "credential_change_or_printing": False,
            "remote_push": False,
        },
        "context_files_read_after_preflight": [
            ".context/LIVE_STATE.md",
            ".context/00_core/current_vnext_system_map.md",
            ".context/00_core/current_repo_reading_order.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/repo_cleanup_and_staleness_policy.md",
            ".context/00_core/vnext_absolute_moonshot_vision_and_limitations.md",
            PROMPT_PATH,
            STARTER_PATH,
        ],
        "official_source_capture_status": [
            {
                "source_id": entry["source_id"],
                "fetch_status": entry["fetch_status"],
                "raw_path": entry["raw_path"],
                "raw_sha256": entry["raw_sha256"],
            }
            for entry in index.get("entries", [])
        ],
        "subagent_integration": {
            "requested": True,
            "status": "subagent_findings_to_be_merged_when_available_or_recorded_in_completion_audit",
        },
    }
    write_json(ROUTE_DIR / "ROUTE_CONTEXT_ANCHOR.json", anchor)
    return anchor


def output_manifest() -> dict[str, Any]:
    files = []
    volatile_names = {"OUTPUT_MANIFEST.json", "VERIFICATION_RESULT.json", "COMPLETION_AUDIT.json"}
    for path in sorted(ROUTE_DIR.rglob("*")):
        if path.is_file() and not should_skip(path):
            is_volatile = path.name in volatile_names
            hash_value = None if is_volatile else sha256_file(path)
            files.append(
                {
                    "path": rel(path),
                    "bytes": None if is_volatile else path.stat().st_size,
                    "sha256": hash_value,
                    "hash_status": "volatile_route_artifact_verified_by_parse_and_presence"
                    if is_volatile
                    else "sha256_fixed",
                    "line_count": None if is_volatile else line_count_if_practical(path, path.stat().st_size),
                }
            )
    manifest = {
        "schema_version": "vps_data_preservation_output_manifest_v1",
        "generated_at_utc": iso_now(),
        "route_dir": rel(ROUTE_DIR),
        "required_artifacts": REQUIRED_ARTIFACTS,
        "missing_required_artifacts": [
            name
            for name in REQUIRED_ARTIFACTS
            if name != "OUTPUT_MANIFEST.json" and not (ROUTE_DIR / name).exists()
        ],
        "artifacts": files,
    }
    write_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", manifest)
    return manifest


def write_initial_verification_result() -> None:
    write_json(
        ROUTE_DIR / "VERIFICATION_RESULT.json",
        {
            "schema_version": "vps_data_preservation_verification_result_v1",
            "generated_at_utc": iso_now(),
            "ok": False,
            "status": "pending_run_verify_vnext_compliant_vps_data_preservation_broker_portability_py",
            "issues": ["verification_not_run_yet"],
        },
    )


def write_completion_audit(can_complete: bool = False, verification_ok: bool = False) -> None:
    audit = {
        "schema_version": "vps_data_preservation_completion_audit_v1",
        "generated_at_utc": iso_now(),
        "route_id": ROUTE_DIR.name,
        "can_mark_goal_complete": can_complete,
        "verification_ok": verification_ok,
        "git": git_head(),
        "requirements": [
            {"requirement": "mandatory_context_read_after_preflight", "status": "recorded_in_ROUTE_CONTEXT_ANCHOR"},
            {"requirement": "official_redacted_account_sources_captured_hashed_summarized", "status": "see_OFFICIAL_redacted_account_SOURCE_INDEX"},
            {"requirement": "tunisia_residency_temp_malaysia_fact_preserved", "status": "see_COMPLIANCE_FACT_LEDGER"},
            {"requirement": "full_local_evidence_inventory_or_absence_requirements", "status": "see_LOCAL_EVIDENCE_INVENTORY"},
            {"requirement": "vps_contract_and_startup_runbook", "status": "see_markdown_runbooks"},
            {"requirement": "broker_portability_map_and_gap_ledger", "status": "see_BROKER_PORTABILITY_MAP_and_gap_ledger"},
            {"requirement": "default_off_scripts_and_manifest", "status": "see_DEFAULT_OFF_EXPORT_SCRIPT_MANIFEST"},
            {"requirement": "verification_result_ok_true", "status": "passed" if verification_ok else "pending"},
            {"requirement": "scoped_commit_with_codex_coauthor", "status": "pending_commit" if not can_complete else "ready_for_commit"},
        ],
        "forbidden_surface_attestation": {
            "live_runtime_started_by_this_route": False,
            "broker_changing_action_by_this_route": False,
            "mt5_server_access_by_this_route": False,
            "paid_api_or_vendor_call_by_this_route": False,
            "credential_print_or_change_by_this_route": False,
            "remote_push_by_this_route": False,
        },
    }
    write_json(ROUTE_DIR / "COMPLETION_AUDIT.json", audit)


def build_all(skip_fetch: bool = False) -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    index = fetch_official_sources(skip_fetch=skip_fetch)
    facts = build_compliance_fact_ledger(index)
    write_context_anchor(index)
    broker_map, gap_rows = build_broker_portability()
    build_mt5_checklist()
    build_default_off_manifest()
    write_markdown_docs()
    inventory_rows, summary = build_local_inventory()
    build_retention_rows(inventory_rows)
    missing = build_missing_export_requirements(summary, gap_rows)
    build_moonshot_map(missing)
    write_initial_verification_result()
    write_completion_audit(can_complete=False, verification_ok=False)
    manifest = output_manifest()
    return {
        "official_source_count": len(index.get("entries", [])),
        "compliance_fact_rows": len(facts),
        "inventory_rows": len(inventory_rows),
        "broker_symbols": len(broker_map.get("symbols", [])),
        "broker_gap_rows": len(gap_rows),
        "missing_requirement_rows": len(missing),
        "manifest_missing_required_artifacts": manifest.get("missing_required_artifacts", []),
        "route_dir": rel(ROUTE_DIR),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fetch", action="store_true", help="Use existing official raw captures if present.")
    args = parser.parse_args(argv)
    result = build_all(skip_fetch=args.skip_fetch)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
