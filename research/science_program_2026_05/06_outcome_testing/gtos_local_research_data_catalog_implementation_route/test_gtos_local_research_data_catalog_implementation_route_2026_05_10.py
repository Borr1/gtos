from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py"
VERIFIER_PATH = ROUTE_DIR / "verify_gtos_local_research_data_catalog_implementation_route_2026_05_10.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


builder = _load_module(BUILDER_PATH, "gtos_local_catalog_builder")


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path):
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_symbol_inference_does_not_match_msi_as_si():
    path = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\GBPJPY\2026-04-28.parquet")
    assert builder.infer_symbol(path) == "GBPJPY"
    assert builder.infer_symbol(Path(r"C:\Users\MSI\Documents\plain_file.json")) == "not_inferred"


def test_catalog_scan_hashes_small_files_defers_large_and_skips_sensitive(tmp_path):
    root = tmp_path / "data" / "ticks" / "NAS100"
    root.mkdir(parents=True)
    small = root / "2026-05-08.parquet"
    small.write_bytes(b"abc")
    large = root / "2026-05-09.parquet"
    large.write_bytes(b"009")
    sensitive = root / "broker_actual_r_2026-05-08.jsonl"
    sensitive.write_text('{"secret": 1}\n', encoding="utf-8")
    config = builder.base_payload(
        "root_resolver_config",
        hash_size_limit_bytes=4,
        max_total_catalog_rows=10,
        sensitive_path_fragments=list(builder.SENSITIVE_PATH_FRAGMENTS),
        roots=[
            {
                "root_id": "tmp_tick_root",
                "root_path": str(tmp_path / "data" / "ticks"),
                "root_role": "ticks",
                "source_family_hint": "mt5_tick_parquet",
                "max_depth": 4,
                "max_files": 10,
                "include_extensions": [".parquet", ".jsonl"],
                "read_policy": "stat_and_hash_small_safe_files_only",
            }
        ],
        search_queries=[],
    )
    rows, root_ledgers, skipped = builder.build_catalog_from_config(config)
    assert len(rows) == 2
    assert any(row["hash_status"] == "sha256_complete" and row["sha256"] for row in rows)
    assert any(row["hash_status"] == "deferred_large_file_requires_dedicated_hash_manifest" for row in rows)
    assert skipped and skipped[0]["read_action"] == "not_opened"
    assert root_ledgers[0]["file_count_skipped_sensitive"] == 1


def test_generated_catalog_rows_are_source_control_only():
    rows = _load_jsonl(ROUTE_DIR / f"{builder.PREFIX}_CATALOG_{builder.DATE}.jsonl")
    assert rows
    assert all(row["allowed_evidence_class"] == "SOURCE_CONTROL_ONLY" for row in rows)
    assert all(row["hash_status"] in {"sha256_complete", "deferred_large_file_requires_dedicated_hash_manifest"} for row in rows)
    assert any(row["hash_status"] == "sha256_complete" for row in rows)
    assert any(row["hash_status"] == "deferred_large_file_requires_dedicated_hash_manifest" for row in rows)


def test_missing_window_ledger_separates_market_data_from_source_state():
    ledger = _load_json(ROUTE_DIR / f"{builder.PREFIX}_MISSING_WINDOW_LEDGER_{builder.DATE}.json")
    assert ledger["recoverable_market_data_count"] > 0
    assert ledger["non_generatable_source_state_count"] > 0
    codes = {row["blocker_code"] for row in ledger["rows"]}
    assert "NON_GENERATABLE_SOURCE_STATE" in codes
    assert "RECOVERABLE_BY_APPROVED_EXTRACTION" in codes or "RECOVERED_LOCAL_SOURCE" in codes


def test_acquisition_manifest_is_manifest_only_and_zero_cost():
    manifest = _load_json(ROUTE_DIR / f"{builder.PREFIX}_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_{builder.DATE}.json")
    assert manifest["request_count"] > 0
    assert all(row["execution_status"] == "not_executed_manifest_only" for row in manifest["requests"])
    assert all(row["cost_cap_usd"] == 0 for row in manifest["requests"])


def test_verifier_accepts_generated_route():
    verifier = _load_module(VERIFIER_PATH, "gtos_local_catalog_verifier")
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["catalog_row_count"] > 0
