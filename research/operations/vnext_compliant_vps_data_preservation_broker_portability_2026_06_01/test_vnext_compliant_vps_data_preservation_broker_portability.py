from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
if str(ROUTE_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTE_DIR))

import build_vnext_compliant_vps_data_preservation_broker_portability as builder
import default_off_vps_tools as tools
import verify_vnext_compliant_vps_data_preservation_broker_portability as verifier


def test_policy_extracts_restricted_country_and_tunisia_distinction() -> None:
    text = (
        "As of now, residents and citizens of Bangladesh, Malaysia, Fiji are not able to access "
        "redacted_account's trading platform. Additionally, clients who are using a MetaQuotes server "
        "cannot use a USA-based IP address. Any attempt using third-party identities or "
        "inaccurate declarations will result in termination."
    )
    facts = builder.extract_policy_facts("redacted_account_restricted_countries", text)

    assert facts["restricted_basis"] == "residents_and_citizens"
    assert facts["malaysia_listed_restricted"] is True
    assert facts["tunisia_listed_restricted"] is False
    assert facts["usa_based_ip_for_mt5_not_allowed"] is True
    assert facts["false_identity_or_location_hiding_incompatible"] is True


def test_network_origin_classifier_rejects_malaysia_and_us_for_mt5() -> None:
    malaysia = tools.classify_network_origin({"country": "Malaysia", "country_code": "MY"})
    assert malaysia["ok_for_redacted_account_mt5"] is False
    assert "network_origin_restricted_country" in malaysia["issues"]

    usa = tools.classify_network_origin({"country": "United States", "country_code": "US"})
    assert usa["ok_for_redacted_account_mt5"] is False
    assert "network_origin_united_states_not_allowed_for_mt5" in usa["issues"]

    singapore = tools.classify_network_origin({"country": "Singapore", "country_code": "SG"})
    assert singapore["ok_for_redacted_account_mt5"] is True


def test_verifier_detects_minimal_good_route_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    route = tmp_path / "route"
    route.mkdir()
    for name in verifier.REQUIRED_ARTIFACTS:
        path = route / name
        if name.endswith(".json"):
            path.write_text("{}\n", encoding="utf-8")
        elif name.endswith(".jsonl"):
            path.write_text("", encoding="utf-8")
        else:
            path.write_text("minimal invalid fixture\n", encoding="utf-8")

    # The real route verifier should reject content-free artifacts; this guards
    # against a presence-only verifier.
    monkeypatch.setattr(verifier, "ROUTE_DIR", route)
    monkeypatch.setattr(verifier, "RESULT_PATH", route / "VERIFICATION_RESULT.json")
    result = verifier.verify_route(write_completion_audit=False)

    assert result["ok"] is False
    assert result["issues"]


def test_default_off_broker_history_export_verifier(tmp_path: Path) -> None:
    export = tmp_path / "deals.jsonl"
    export.write_text(
        json.dumps({"ticket": 1, "order": 2, "position_id": 3, "symbol": "XAUUSD"}) + "\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(ROUTE_DIR / "default_off_vps_tools.py"),
            "broker-history-export-verify",
            "--input",
            str(export),
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["ok"] is True
    assert result["rows"] == 1


def test_no_forbidden_concealment_language_in_runbook_templates() -> None:
    forbidden = verifier.FORBIDDEN_TEXT_RE
    assert forbidden.search((ROUTE_DIR / "VPS_MIGRATION_CONTRACT.md").read_text(encoding="utf-8")) is None
    assert forbidden.search((ROUTE_DIR / "VPS_STARTUP_VERIFICATION_RUNBOOK.md").read_text(encoding="utf-8")) is None
