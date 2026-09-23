"""CLI verdict writer binds fingerprint from latest_slate."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.f5_desk import write_inbox_verdict as wiv


def test_bind_overwrites_fingerprint(tmp_path: Path):
    repo = tmp_path
    state = repo / "pipeline_state" / "ultimate_book" / "operator" / "judgment" / "state"
    state.mkdir(parents=True)
    slate = {"slate_id": "s1", "fingerprint": "fp-live", "candidates": []}
    (state / "latest_slate.json").write_text(json.dumps(slate), encoding="utf-8")
    bound = wiv.bind({"schema": "nope", "fingerprint": "stale", "verdicts": []}, slate)
    assert bound["schema"] == "gtos.f5.judge.verdict.v1"
    assert bound["fingerprint"] == "fp-live"
    assert bound["slate_id"] == "s1"
    assert bound["written_at_utc"]


def test_cli_writes_inbox(tmp_path: Path, monkeypatch):
    repo = tmp_path
    state = repo / "pipeline_state" / "ultimate_book" / "operator" / "judgment" / "state"
    inbox = repo / "pipeline_state" / "ultimate_book" / "operator" / "judgment" / "inbox"
    state.mkdir(parents=True)
    (state / "latest_slate.json").write_text(
        json.dumps({"slate_id": "abc", "fingerprint": "deadbeef", "candidates": [{"candidate_id": "c1"}]}),
        encoding="utf-8",
    )
    rc = wiv.main(["--repo", str(repo), "--abstain-all", "--memory", "180775761 EURUSD orig_stop"])
    assert rc == 0
    payload = json.loads((inbox / "verdict.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "gtos.f5.judge.verdict.v1"
    assert payload["fingerprint"] == "deadbeef"
    assert payload["verdicts"][0]["verdict"] == "abstain"
    assert payload["memory"]
