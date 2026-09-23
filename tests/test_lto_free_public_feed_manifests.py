from __future__ import annotations

import json
from pathlib import Path

from scripts import build_lto031_lto032_free_public_source_manifests as script
from scripts import build_lto031_lto032_source_unblocking_plan as plan
from src.research_infra import lto_free_public_feed_manifests as mod
from src.research_infra.lto_source_contract_registry import build_registry_payload


def _write(path: Path, text: str = "{}\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_external(root: Path) -> None:
    _write(root / "raw/cftc_cot/disagg_combined_20260501T000000Z.json", "[]")
    _write(root / "normalized/cftc_cot/disagg_combined_20260501T000000Z.jsonl", '{"gtos_symbol":"XAUUSD"}\n')
    _write(root / "status/cftc_cot__disagg_combined_088691_XAUUSD.json")
    _write(root / "normalized/fred/DGS10_observations_20260501T000000Z.jsonl", '{"series_id":"DGS10"}\n')
    _write(root / "normalized/fred/VIXCLS_observations_20260501T000000Z.jsonl", '{"series_id":"VIXCLS"}\n')
    _write(root / "status/fred__DGS10.json")
    _write(root / "raw/flashalpha_gex/QQQ_20260501T000000Z.json", "{}")
    _write(root / "normalized/flashalpha_gex/QQQ_gex_20260501T000000Z.jsonl", '{"proxy_symbol":"QQQ"}\n')
    _write(root / "status/flashalpha_gex__QQQ_NAS100_2026-05-15.json")


def _registry_payload():
    return build_registry_payload(plan.build_source_contracts(), generated_at_utc="2026-05-06T00:00:00+00:00")


def test_p1_manifest_covers_free_public_and_existing_sources(tmp_path: Path):
    external = tmp_path / "data/external"
    _seed_external(external)

    payload = mod.build_manifest_payload(
        _registry_payload(),
        repo_root=tmp_path,
        external_root=external,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )
    rows = {row["source_key"]: row for row in payload["manifests"]}

    assert payload["status"] == mod.STATUS_READY
    assert payload["promotion_verdict"] == mod.PROMOTION_VERDICT
    assert set(rows) == set(mod.P1_SOURCE_KEYS)
    assert payload["manifest_count"] == 5
    assert rows["fx_cot"]["manifest_status"] == "PARTIAL_LOCAL_CACHE_PRESENT_FX_MAPPING_REQUIRED"
    assert rows["bis_macro"]["manifest_status"] == "SOURCE_MANIFEST_READY_NO_LOCAL_BIS_CACHE"
    assert rows["fed_fred_research"]["manifest_status"] == "PARTIAL_LOCAL_CACHE_PRESENT_FRED_REGISTRY_REQUIRED"
    assert rows["vix_vix9d_gvz_vvix_vix1d"]["manifest_status"] == "PARTIAL_FRED_VOL_CACHE_PRESENT_CBOE_RAW_REQUIRED"
    assert rows["flashalpha_basic_gex_forward_proxy"]["manifest_status"] == "EXISTING_FORWARD_CONTEXT_CACHE_PRESENT"


def test_manifest_rows_preserve_validation_and_no_fetch_boundaries(tmp_path: Path):
    payload = mod.build_manifest_payload(
        _registry_payload(),
        repo_root=tmp_path,
        external_root=tmp_path / "data/external",
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )

    assert payload["validation_safe_counts"] == {"false": 5, "true": 0}
    assert payload["paid_data_calls"] == 0
    assert payload["paid_fetch_attempted"] is False
    assert payload["ai_calls"] == 0
    assert payload["order_calls"] == 0
    assert all(row["validation_safe"] is False for row in payload["manifests"])
    assert all("P1_MANIFEST_ONLY_NO_NEW_FETCH" in row["validation_safe_blockers"] for row in payload["manifests"])


def test_manifest_separates_cboe_raw_from_fred_vol_mirror(tmp_path: Path):
    external = tmp_path / "data/external"
    _write(external / "normalized/fred/VIXCLS_observations_20260501T000000Z.jsonl", '{"series_id":"VIXCLS"}\n')

    payload = mod.build_manifest_payload(
        _registry_payload(),
        repo_root=tmp_path,
        external_root=external,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )
    rows = {row["source_key"]: row for row in payload["manifests"]}
    cboe = rows["vix_vix9d_gvz_vvix_vix1d"]

    assert cboe["local_inventory"]["local_source_name"] == "fred"
    assert cboe["manifest_status"] == "PARTIAL_FRED_VOL_CACHE_PRESENT_CBOE_RAW_REQUIRED"
    assert any("Cboe raw CSV source index" in action for action in cboe["next_actions"])
    assert cboe["validation_safe"] is False


def test_script_writes_manifest_artifacts(tmp_path: Path):
    external = tmp_path / "data/external"
    _seed_external(external)
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(_registry_payload()), encoding="utf-8")
    out_json = tmp_path / "manifests.json"
    out_md = tmp_path / "manifests.md"
    ops_md = tmp_path / "ops.md"

    assert script.main(
        [
            "--repo-root",
            str(tmp_path),
            "--external-root",
            str(external),
            "--registry-json",
            str(registry_path),
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
    assert "No feed was fetched" in ops_md.read_text(encoding="utf-8")
