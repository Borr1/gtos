import importlib.util
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "build_orderflow_mbo_full_day_manifest.py"
    spec = importlib.util.spec_from_file_location("build_orderflow_mbo_full_day_manifest", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_mbo_manifest_uses_candidate_dates_and_midnight_start():
    mod = _load_module()
    source = {
        "schema_version": "test_manifest",
        "events": [
            {
                "event_id": "cand",
                "symbol": "NAS100",
                "databento_symbols": ["NQ.v.0"],
                "event_class": "candidate",
                "canonical_m15_close_utc": "2026-04-28T17:00:00+00:00",
            },
            {
                "event_id": "ctx_same_day",
                "symbol": "NAS100",
                "databento_symbols": ["NQ.v.0"],
                "event_class": "structural_context",
                "canonical_m15_close_utc": "2026-04-28T07:15:00+00:00",
            },
            {
                "event_id": "ctx_only_day",
                "symbol": "NAS100",
                "databento_symbols": ["NQ.v.0"],
                "event_class": "structural_context",
                "canonical_m15_close_utc": "2026-04-30T07:15:00+00:00",
            },
        ],
    }

    payload = mod.build_payload(
        source,
        gtos_symbol="NAS100",
        futures_symbol="NQ.v.0",
        candidate_dates_only=True,
        include_context_on_candidate_dates=True,
        end_buffer_minutes=0,
    )

    assert payload["synthesis"]["event_count"] == 2
    assert len(payload["fetch_groups"]) == 1
    group = payload["fetch_groups"][0]
    assert group["start_utc"] == "2026-04-28T00:00:00+00:00"
    assert group["end_utc"] == "2026-04-28T17:00:00+00:00"
    assert group["event_ids"] == ["ctx_same_day", "cand"]
    assert group["mbo_start_policy"] == "UTC_MIDNIGHT_SYNTHETIC_BOOK_SNAPSHOT_REQUIRED"
