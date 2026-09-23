from __future__ import annotations

import hashlib
import json

from src.components.gtos_vnext_runtime import load_vnext_evidence_index


def test_vnext_runtime_loads_local_git_lfs_pointer_object(tmp_path):
    repo = tmp_path / "repo"
    git_dir = repo / ".git"
    route = repo / "research" / "vnext"
    route.mkdir(parents=True)
    git_dir.mkdir()

    payload = json.dumps(
        {
            "source_row_id": "row-1",
            "symbol": "US30_cash",
            "action_class": "follow_rule",
            "cost_adjusted_simulated_r": 1.25,
        }
    ) + "\n"
    oid = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    object_path = git_dir / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
    object_path.parent.mkdir(parents=True)
    object_path.write_text(payload, encoding="utf-8")

    pointer = route / "GTOS_VNEXT_SCORER_FILTER_ROUTER_IMPLEMENTATION_LEDGER_2026-05-18.jsonl"
    pointer.write_text(
        "\n".join(
            [
                "version https://git-lfs.github.com/spec/v1",
                f"oid sha256:{oid}",
                f"size {len(payload.encode('utf-8'))}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    index = load_vnext_evidence_index([pointer])

    assert index.rows_loaded_by_path[str(pointer)] == 1
    assert index.rows[0]["source_row_id"] == "row-1"
    assert index.rows[0]["_gtos_vnext_loaded_from"] == str(pointer)
