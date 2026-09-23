from __future__ import annotations

from pathlib import Path

from scripts import build_lto032_options_gamma_vrp_source_manifests as script
from scripts import build_lto031_lto032_source_unblocking_plan as plan
from src.research_infra import lto_options_gamma_vrp_source_manifests as mod
from src.research_infra.lto_source_contract_registry import build_registry_payload


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _registry() -> dict:
    return build_registry_payload(
        plan.build_source_contracts(),
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )


def _seed_options_sources(root: Path) -> None:
    for proxy, gtos in [("QQQ", "NAS100"), ("DIA", "US30"), ("SPY", "SPX"), ("GLD", "XAUUSD"), ("SLV", "XAGUSD")]:
        _write(
            root / "data/external/status" / f"flashalpha_gex__{proxy}.json",
            '{"source":"flashalpha_gex","status_key":"'
            + proxy
            + '","status":"OK","row_count":1,"extra":{"proxy_symbol":"'
            + proxy
            + '","gtos_symbol":"'
            + gtos
            + '"}}\n',
        )
        _write(
            root / "data/external/normalized/flashalpha_gex" / f"{proxy}_gex_2026-05-06.jsonl",
            '{"proxy_symbol":"'
            + proxy
            + '","gtos_symbol":"'
            + gtos
            + '","expiration":"2026-05-15","as_of_utc":"2026-05-06T00:00:00Z","net_gex":1.0,"net_gex_label":"positive","gamma_flip":100.0}\n',
        )
    _write(
        root / "data/external/status/fred__VIXCLS.json",
        '{"source":"fred","status_key":"VIXCLS","status":"OK","extra":{"series_id":"VIXCLS"}}\n',
    )
    _write(
        root / "data/external/status/fred__GVZCLS.json",
        '{"source":"fred","status_key":"GVZCLS","status":"OK","extra":{"series_id":"GVZCLS"}}\n',
    )
    _write(root / "data/external/normalized/fred/VIXCLS_observations_2026-05-06.jsonl", '{"series_id":"VIXCLS"}\n')


def test_flashalpha_inventory_counts_proxy_rows_and_coverage(tmp_path: Path):
    _seed_options_sources(tmp_path)

    inventory = mod.inventory_flashalpha_gex(tmp_path)

    assert inventory["status_file_count"] == 5
    assert inventory["normalized_file_count"] == 5
    assert inventory["normalized_row_count"] == 5
    assert inventory["proxy_counts"] == {"DIA": 1, "GLD": 1, "QQQ": 1, "SLV": 1, "SPY": 1}
    assert all(inventory["core_proxy_coverage"].values())


def test_options_gamma_payload_keeps_flashalpha_forward_only_and_blocks_historical(tmp_path: Path):
    _seed_options_sources(tmp_path)

    payload = mod.build_payload(
        _registry(),
        repo_root=tmp_path,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )
    rows = {row["manifest_key"]: row for row in payload["source_rows"]}

    assert payload["status"] == mod.STATUS_READY
    assert payload["promotion_verdict"] == mod.PROMOTION_VERDICT
    assert payload["validation_issues"] == []
    assert rows["flashalpha_basic_gex_forward_proxy"]["forward_context_allowed"] is True
    assert rows["flashalpha_basic_gex_forward_proxy"]["historical_validation_allowed"] is False
    assert rows["official_or_historical_aggregate_gex"]["status"] == "BLOCKED_LEGAL_TIMESTAMPED_HISTORICAL_GEX_REQUIRED"
    assert rows["official_or_historical_aggregate_gex"]["local_evidence"]["flashalpha_is_substitute"] is False
    assert all(row["validation_safe"] is False for row in payload["source_rows"])


def test_options_gamma_payload_blocks_vix_spread_and_vrp_until_sources_and_formula_exist(tmp_path: Path):
    _seed_options_sources(tmp_path)

    payload = mod.build_payload(
        _registry(),
        repo_root=tmp_path,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )
    rows = {row["manifest_key"]: row for row in payload["source_rows"]}

    assert rows["vix1d_vix9d_spread"]["status"] == "BLOCKED_VIX1D_VIX9D_SOURCE_REQUIRED"
    assert rows["vix1d_vix9d_spread"]["local_evidence"]["terms_present"]["VIXCLS"] is True
    assert rows["vix1d_vix9d_spread"]["local_evidence"]["terms_present"]["GVZCLS"] is True
    assert rows["vix1d_vix9d_spread"]["local_evidence"]["missing_required_terms"] == ["VIX1D", "VIX9D"]
    assert rows["vrp_delta"]["status"] == "BLOCKED_VRP_CONSTRUCTION_PREREGISTRATION_REQUIRED"
    assert rows["vrp_delta"]["formula_contract"]["status"] == "PREREGISTRATION_ONLY_NOT_SOURCE_READY"
    assert rows["vrp_delta"]["local_evidence"]["vrp_term_present"] is False


def test_options_gamma_payload_has_no_action_counters(tmp_path: Path):
    payload = mod.build_payload(
        _registry(),
        repo_root=tmp_path,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )

    assert payload["ai_calls"] == 0
    assert payload["canary_calls"] == 0
    assert payload["order_calls"] == 0
    assert payload["paid_data_calls"] == 0
    assert payload["paid_fetch_attempted"] is False
    assert payload["validation_safe_counts"] == {"false": 4, "true": 0}
    assert payload["historical_validation_allowed_counts"] == {"false": 4, "true": 0}


def test_validation_rejects_historical_flashalpha_and_promoted_rows(tmp_path: Path):
    payload = mod.build_payload(
        _registry(),
        repo_root=tmp_path,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )
    payload["source_rows"][0]["historical_validation_allowed"] = True
    payload["source_rows"][0]["validation_safe"] = True

    issues = mod.validate_payload(payload)

    assert "flashalpha_basic_gex_forward_proxy:HISTORICAL_VALIDATION_UNEXPECTEDLY_ALLOWED" in issues
    assert "flashalpha_basic_gex_forward_proxy:UNEXPECTED_VALIDATION_SAFE_TRUE" in issues
    assert "flashalpha_basic_gex_forward_proxy:UNEXPECTED_HISTORICAL_VALIDATION_ALLOWED" in issues


def test_script_writes_options_gamma_vrp_artifacts(tmp_path: Path):
    _seed_options_sources(tmp_path)
    out_json = tmp_path / "options.json"
    out_md = tmp_path / "options.md"
    ops_md = tmp_path / "ops.md"

    assert script.main(
        [
            "--repo-root",
            str(tmp_path),
            "--registry-json",
            str(tmp_path / "missing_registry.json"),
            "--output-json",
            str(out_json),
            "--output-md",
            str(out_md),
            "--operations-md",
            str(ops_md),
            "--generated-at-utc",
            "2026-05-06T00:00:00+00:00",
        ]
    ) == 0

    assert out_json.exists()
    assert out_md.exists()
    assert ops_md.exists()
    assert "NO_PROMOTION_VERDICT" in out_md.read_text(encoding="utf-8")
    assert "FlashAlpha Basic cannot be used for historical gamma validation" in ops_md.read_text(encoding="utf-8")
