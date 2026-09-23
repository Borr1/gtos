from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from scripts import audit_expanded_oos_replay_portability as audit


def _scratch_dir() -> Path:
    root = Path(".test_expanded_oos_replay_portability_tmp")
    root.mkdir(exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()
    return path


def test_extract_cli_args_finds_long_options() -> None:
    scratch = _scratch_dir()
    script = scratch / "tool.py"
    try:
        script.write_text(
            "parser.add_argument('--event-log')\n"
            "parser.add_argument('--output-json', default='x')\n"
            "parser.add_argument('-q', '--quiet', action='store_true')\n",
            encoding="utf-8",
        )

        assert audit.extract_cli_args(script) == {"--event-log", "--output-json"}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_payload_preserves_no_promotion_and_no_opened_outcomes() -> None:
    payload = audit.build_payload()

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["outcome_batches_opened_by_this_audit"] == 0
    assert payload["summary"]["tools_audited"] >= 8
    assert any(row["tool_id"] == "REPLAY-V2-STRUCTURAL" for row in payload["tools"])


def test_tool_audit_reports_missing_args_for_fake_tool() -> None:
    scratch = _scratch_dir()
    fake = scratch / "fake.py"
    try:
        fake.write_text("parser.add_argument('--present')\n", encoding="utf-8")
        spec = audit.ToolSpec(
            tool_id="FAKE",
            path=str(fake.resolve().relative_to(audit.ROOT.resolve())),
            role="fake",
            required_args=("--present", "--missing"),
            candidate_coverage=("none",),
            evidence_classes=("DISCOVERY_ONLY",),
            current_scope="fake",
            portability_status="fake",
            blocker=None,
            next_adapter=None,
        )

        row = audit.audit_tool(spec)

        assert row["readiness"] == "PARTIAL_CLI_CONTRACT"
        assert row["missing_required_args"] == ["--missing"]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_markdown_writer_includes_first_batch_recommendation() -> None:
    scratch = _scratch_dir()
    out = scratch / "audit.md"
    try:
        payload = audit.build_payload()
        audit.write_markdown(out, payload)

        text = out.read_text(encoding="utf-8")
        assert "NO_PROMOTION_VERDICT" in text
        assert "First Batch Recommendation" in text
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
