import json
import time
from pathlib import Path

import src.gtos_context_os.pack as pack_module
from src.gtos_context_os.catalog import (
    StaleCatalogError,
    build_catalog,
    catalog_freshness,
    catalog_stats,
    search_catalog,
)
from src.gtos_context_os.classifier import COLD_RAW_EVIDENCE, PLATINUM_CURRENT_AUTHORITY, classify_path
from src.gtos_context_os.cli import main as cli_main
from src.gtos_context_os.health import context_intelligence_health
from src.gtos_context_os.ingest import ingest_finding
from src.gtos_context_os.memory import search_memory
from src.gtos_context_os.pack import build_context_pack, render_markdown_pack
from src.gtos_context_os.resume import build_resume_bundle
from src.gtos_context_os.route import route_overview
from src.gtos_context_os.server import handle_request
from src.gtos_context_os.second_brain import (
    capture_idea,
    distill_idea,
    generate_second_brain_graph,
    init_second_brain,
    search_second_brain,
    second_brain_distillation_queue,
    second_brain_status,
)
from src.gtos_context_os.session import create_session_capsule, list_session_capsules, session_capsule_status
from src.gtos_context_os.session_state import (
    load_active_session_state,
    load_continuation_cursor,
    summarize_active_state_payload,
    summarize_continuation_cursor_payload,
    write_context_checkpoint,
    write_active_session_state,
    write_continuation_cursor,
)
from src.gtos_context_os.starter import build_starter_prompt
from src.gtos_context_os.symbols import search_symbols
from src.gtos_context_os.mcp_stdio import handle_mcp_request, handle_stdio_request
from src.gtos_context_os.writeback import create_writeback_proposal


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_classifies_current_authority_and_raw_evidence():
    live = classify_path(".context/LIVE_STATE.md")
    raw = classify_path("research/operations/route/TRADE_LEDGER.jsonl")

    assert live.authority_tier == PLATINUM_CURRENT_AUTHORITY
    assert live.evidence_class == "current_context_authority"
    assert raw.authority_tier == COLD_RAW_EVIDENCE
    assert raw.evidence_class == "raw_or_large_evidence_pointer"


def test_catalog_search_keeps_jsonl_metadata_without_indexing_text_by_default(tmp_path):
    repo = tmp_path
    _write(repo / ".context/LIVE_STATE.md", "# Live State\nStatus: current disk authority\n")
    _write(repo / ".context/00_core/current_vnext_system_map.md", "# System Map\nselector scheduler authority\n")
    _write(repo / ".context/00_core/current_repo_reading_order.md", "# Reading Order\n")
    _write(repo / ".context/00_core/quick_reference_card.md", "# Quick Reference\n")
    _write(repo / ".context/00_core/repo_cleanup_and_staleness_policy.md", "# Cleanup\nlarge JSONL cold evidence\n")
    _write(repo / ".context/00_core/research_operating_doctrine.md", "# Doctrine\n")
    _write(repo / ".context/00_core/goal_session_research_discipline.md", "# Discipline\n")
    _write(
        repo / "research/operations/final_moonshot_route/ROUTE_SUMMARY.json",
        '{"route": "final_moonshot_route", "finding": "selector scheduler replay parity"}',
    )
    _write(
        repo / "research/operations/final_moonshot_route/RAW_REPLAY_LEDGER.jsonl",
        '{"finding": "this raw-only phrase should not be indexed"}\n',
    )
    _write(
        repo / "research/operations/final_moonshot_route/BROAD_LIVE_AS_IF_REPLAY_PARTIAL_SMOKE_SUMMARY.json",
        '{"finding": "volatile smoke summary should stay metadata only"}',
    )

    result = build_catalog(repo=repo, db_path="catalog.sqlite", roots=(".context", "research/operations"))
    assert result.indexed_documents >= 8
    assert result.metadata_only_documents >= 2

    hits = search_catalog("selector scheduler replay parity", db_path="catalog.sqlite", repo=repo)
    paths = {hit["path"] for hit in hits}
    assert "research/operations/final_moonshot_route/ROUTE_SUMMARY.json" in paths
    assert "research/operations/final_moonshot_route/RAW_REPLAY_LEDGER.jsonl" not in paths
    assert (
        "research/operations/final_moonshot_route/BROAD_LIVE_AS_IF_REPLAY_PARTIAL_SMOKE_SUMMARY.json"
        not in paths
    )
    assert not search_catalog(
        "volatile smoke summary",
        db_path="catalog.sqlite",
        repo=repo,
    )

    stats = catalog_stats(db_path="catalog.sqlite", repo=repo)
    assert stats["total_documents"] == result.indexed_documents + result.metadata_only_documents
    assert stats["authority_tiers"][COLD_RAW_EVIDENCE] >= 1


def test_context_pack_includes_anchors_and_task_hits(tmp_path):
    repo = tmp_path
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\nStatus: current\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
        "src/components/selector_v4.py": "def selector():\n    return 'risk scheduler replay parity'\n",
    }.items():
        _write(repo / rel, text)

    _write(
        repo / "research/operations/final_moonshot_route/ROUTE_SUMMARY.json",
        '{"status": "current", "route": "final_moonshot_route", "finding": "risk scheduler replay parity"}',
    )
    build_catalog(
        repo=repo,
        db_path="catalog.sqlite",
        roots=(".context", "src/components", "research/operations"),
    )
    pack = build_context_pack(
        "risk scheduler replay parity",
        repo=repo,
        db_path="catalog.sqlite",
        profile="ultimate",
        route="final_moonshot_route",
        auto_build=False,
    )
    markdown = render_markdown_pack(pack)

    assert pack["schema_version"] == "gtos_context_pack_v1"
    assert pack["profile"] == "ultimate"
    assert pack["route_overview"]["route"] == "final_moonshot_route"
    assert any(doc["path"] == ".context/LIVE_STATE.md" for doc in pack["anchors"])
    assert any(doc["path"] == "src/components/selector_v4.py" for doc in pack["relevant_hits"])
    assert "large JSONL/LFS/raw evidence is cold by default" in markdown
    assert "## Route Overview" in markdown
    assert "doctrine_checklist" in pack
    assert "## Doctrine Checklist" in markdown


def test_route_overview_separates_compact_docs_from_cold_raw(tmp_path):
    repo = tmp_path
    route = "final_moonshot_route"
    _write(repo / f"research/operations/{route}/ROUTE_SUMMARY.json", '{"finding": "selector"}')
    _write(repo / f"research/operations/{route}/RAW_REPLAY_LEDGER.jsonl", '{"raw": true}\n')

    build_catalog(repo=repo, db_path="catalog.sqlite", roots=(f"research/operations/{route}",))
    overview = route_overview(route, repo=repo, db_path="catalog.sqlite")

    assert overview["compact_documents"] == 1
    assert overview["cold_raw_pointers"] == 1
    assert overview["read_first"][0]["path"].endswith("ROUTE_SUMMARY.json")


def test_route_overview_hydrates_exact_route_without_deep_catalog(tmp_path):
    repo = tmp_path
    route = "final_moonshot_route"
    _write(repo / ".context/LIVE_STATE.md", "# Live State\n")
    _write(repo / ".context/00_core/current_vnext_system_map.md", "# System Map\n")
    _write(repo / ".context/00_core/current_repo_reading_order.md", "# Reading Order\n")
    _write(repo / ".context/00_core/gtos_context_os.md", "# Context OS\n")
    _write(repo / f"research/operations/{route}/ROUTE_SUMMARY.json", '{"finding": "selector"}')
    _write(repo / f"research/operations/{route}/OUTPUT_MANIFEST.json", '{"outputs": []}')
    _write(repo / f"research/operations/{route}/RAW_REPLAY_LEDGER.jsonl", '{"raw": true}\n')
    build_catalog(repo=repo, db_path="catalog.sqlite")

    assert not search_catalog("selector", db_path="catalog.sqlite", repo=repo)
    overview = route_overview(route, repo=repo, db_path="catalog.sqlite")

    assert overview["source"] == "exact_route_filesystem"
    assert overview["filesystem_manifest"]["route_exists"] is True
    assert overview["filesystem_manifest"]["scanned_files"] == 3
    assert overview["compact_documents"] >= 2
    assert overview["cold_raw_pointers"] == 1
    assert overview["read_first"][0]["path"].endswith("ROUTE_SUMMARY.json")
    assert overview["filesystem_manifest"]["cold_raw_pointers"][0]["path"].endswith("RAW_REPLAY_LEDGER.jsonl")


def test_catalog_freshness_fails_closed_and_can_rebuild(tmp_path):
    repo = tmp_path
    _write(repo / ".context/LIVE_STATE.md", "# Live State\nfirst\n")
    _write(repo / ".context/00_core/current_vnext_system_map.md", "# System Map\n")
    _write(repo / ".context/00_core/current_repo_reading_order.md", "# Reading Order\n")
    _write(repo / ".context/00_core/gtos_context_os.md", "# Context OS\n")
    build_catalog(repo=repo, db_path="catalog.sqlite", roots=(".context",))

    assert catalog_freshness(db_path="catalog.sqlite", repo=repo)["fresh"] is True
    _write(repo / ".context/LIVE_STATE.md", "# Live State\nsecond\n")

    freshness = catalog_freshness(db_path="catalog.sqlite", repo=repo)
    assert freshness["fresh"] is False
    assert "authority_anchor_changed" in freshness["reasons"]

    try:
        build_context_pack("freshness check", repo=repo, db_path="catalog.sqlite", auto_build=False)
    except StaleCatalogError as exc:
        assert "catalog is stale" in str(exc)
    else:
        raise AssertionError("stale catalog should fail closed")

    pack = build_context_pack(
        "freshness check",
        repo=repo,
        db_path="catalog.sqlite",
        auto_build=False,
        auto_rebuild_stale=True,
    )
    assert pack["catalog_freshness"]["fresh"] is True


def test_cli_pack_and_starter_self_refresh_stale_catalog_by_default(tmp_path, capsys):
    repo = tmp_path
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\nfirst\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/gtos_context_os.md": "# Context OS\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
        "src/components/selector_v4.py": (
            "def selector_replay_parity():\n"
            "    \"\"\"selector scheduler replay parity\"\"\"\n"
            "    return True\n"
        ),
    }.items():
        _write(repo / rel, text)
    build_catalog(repo=repo, db_path="catalog.sqlite", roots=(".context", "src"))

    _write(repo / ".context/LIVE_STATE.md", "# Live State\nsecond\n")
    assert (
        cli_main(
            [
                "--repo",
                repo.as_posix(),
                "--db",
                "catalog.sqlite",
                "pack",
                "--task",
                "selector scheduler replay parity",
                "--profile",
                "selector-scheduler",
                "--format",
                "json",
            ]
        )
        == 0
    )
    pack = json.loads(capsys.readouterr().out)
    assert pack["catalog_freshness"]["fresh"] is True
    assert "Act decisively from current disk evidence" in pack["doctrine_checklist"]["operating_posture"]

    _write(repo / ".context/LIVE_STATE.md", "# Live State\nthird\n")
    assert (
        cli_main(
            [
                "--repo",
                repo.as_posix(),
                "--db",
                "catalog.sqlite",
                "starter",
                "--task",
                "selector scheduler replay parity",
                "--lane",
                "selector-scheduler",
                "--profile",
                "selector-scheduler",
            ]
        )
        == 0
    )
    starter = capsys.readouterr().out
    assert "Execution posture:" in starter
    assert "Use this pack to move the work forward" in starter
    assert catalog_freshness(db_path="catalog.sqlite", repo=repo)["fresh"] is True

    _write(repo / ".context/LIVE_STATE.md", "# Live State\nfourth\n")
    try:
        cli_main(
            [
                "--repo",
                repo.as_posix(),
                "--db",
                "catalog.sqlite",
                "pack",
                "--task",
                "selector scheduler replay parity",
                "--profile",
                "selector-scheduler",
                "--format",
                "json",
                "--no-auto-rebuild-stale",
            ]
        )
    except StaleCatalogError:
        pass
    else:
        raise AssertionError("explicit no-auto-rebuild mode should fail closed on stale catalog")


def test_catalog_build_reuses_fresh_same_options_catalog(tmp_path):
    repo = tmp_path
    _write(repo / ".context/LIVE_STATE.md", "# Live State\nfirst\n")
    _write(repo / ".context/00_core/current_vnext_system_map.md", "# System Map\n")
    _write(repo / ".context/00_core/current_repo_reading_order.md", "# Reading Order\n")
    _write(repo / ".context/00_core/gtos_context_os.md", "# Context OS\n")
    _write(repo / ".context/backlog_old/OLD.md", "# Old Backlog\nstale backlog only phrase\n")
    _write(repo / "config/runtime.yaml", "selector: scheduler\n")

    first = build_catalog(repo=repo, db_path="catalog.sqlite", roots=(".context", "config"))
    second = build_catalog(repo=repo, db_path="catalog.sqlite", roots=(".context", "config"))

    assert first.reused_existing is False
    assert second.reused_existing is True
    assert second.indexed_documents == first.indexed_documents
    assert second.metadata_only_documents == first.metadata_only_documents

    changed_roots = build_catalog(repo=repo, db_path="catalog.sqlite", roots=(".context",))
    assert changed_roots.reused_existing is False


def test_cli_build_current_scope_skips_research_operations_until_deep(tmp_path, capsys):
    repo = tmp_path
    _write(repo / ".context/LIVE_STATE.md", "# Live State\n")
    _write(repo / ".context/00_core/current_vnext_system_map.md", "# System Map\n")
    _write(repo / ".context/00_core/current_repo_reading_order.md", "# Reading Order\n")
    _write(repo / ".context/00_core/gtos_context_os.md", "# Context OS\n")
    _write(repo / ".context/backlog_old/OLD.md", "# Old Backlog\nstale backlog only phrase\n")
    _write(repo / "config/runtime.yaml", "selector: scheduler\n")
    _write(
        repo / "research/operations/route/ROUTE_SUMMARY.json",
        '{"finding": "deep route only phrase"}',
    )

    assert (
        cli_main(
            [
                "--repo",
                repo.as_posix(),
                "--db",
                "catalog.sqlite",
                "build",
                "--format",
                "json",
            ]
        )
        == 0
    )
    current_payload = json.loads(capsys.readouterr().out)
    assert "research/operations" not in current_payload["roots"]
    assert not search_catalog("deep route only phrase", db_path="catalog.sqlite", repo=repo)
    assert not search_catalog("stale backlog only phrase", db_path="catalog.sqlite", repo=repo)

    assert (
        cli_main(
            [
                "--repo",
                repo.as_posix(),
                "--db",
                "catalog.sqlite",
                "build",
                "--scope",
                "deep",
                "--force",
                "--format",
                "json",
            ]
        )
        == 0
    )
    deep_payload = json.loads(capsys.readouterr().out)
    assert "research/operations" in deep_payload["roots"]
    assert search_catalog("deep route only phrase", db_path="catalog.sqlite", repo=repo)
    assert search_catalog("stale backlog only phrase", db_path="catalog.sqlite", repo=repo)


def test_memory_search_and_writeback_proposal_are_controlled(tmp_path):
    memory_root = tmp_path / "memory"
    _write(
        memory_root / "MEMORY.md",
        "# Memory\nselector scheduler context hygiene current disk authority\n",
    )
    hits = search_memory("selector context hygiene", memory_root=memory_root)

    assert hits
    assert hits[0]["authority_tier"] == "bronze_chat_or_memory"
    assert hits[0]["freshness"] == "memory_derived_verify_against_current_disk"

    proposal = create_writeback_proposal(
        "Selector context rule",
        "Verify selector facts from current disk before canonical memory promotion.",
        sources=["src/components/selector_v4.py"],
        repo=tmp_path,
    )
    payload = proposal.read_text(encoding="utf-8")
    assert "proposal_only_not_canonical_memory" in payload
    assert "src/components/selector_v4.py" in payload

    capsule = create_session_capsule(
        "Session hardening",
        "Added stale fail-closed checks.",
        task="context hardening",
        sources=["src/gtos_context_os/catalog.py"],
        commands=["python3 -m pytest tests/test_gtos_context_os.py -q"],
        decisions=["fail closed on stale catalog"],
        repo=tmp_path,
    )
    capsule_payload = capsule.read_text(encoding="utf-8")
    assert "local_session_capsule_not_canonical_until_promoted" in capsule_payload


def test_session_capsules_feed_health_pack_and_starter(tmp_path):
    repo = tmp_path / "repo"
    brain_root = tmp_path / "second-brain"
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/gtos_context_os.md": "# Context OS\n",
        ".context/00_core/gtos_second_brain.md": "# Second Brain\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
        "src/components/selector_v4.py": (
            "def selector_replay_parity():\n"
            "    \"\"\"selector scheduler replay parity\"\"\"\n"
            "    return True\n"
        ),
    }.items():
        _write(repo / rel, text)

    build_catalog(repo=repo, db_path="catalog.sqlite")
    capsule = create_session_capsule(
        "Selector continuity checkpoint",
        "Patched selector context flow and verified focused tests.",
        task="selector scheduler replay parity",
        sources=["src/components/selector_v4.py"],
        commands=["python3 -m pytest tests/test_gtos_context_os.py -q"],
        decisions=["carry continuity capsules into packs"],
        repo=repo,
    )

    recent = list_session_capsules(repo=repo, limit=3)
    assert recent
    assert recent[0]["abs_path"] == capsule.as_posix()
    assert session_capsule_status(repo=repo)["count"] == 1

    health = context_intelligence_health(repo=repo, db_path="catalog.sqlite", second_brain_root=brain_root)
    assert health["session_capsules"]["count"] == 1
    assert "no_session_capsules" not in health["warnings"]

    pack = build_context_pack(
        "selector scheduler replay parity",
        repo=repo,
        db_path="catalog.sqlite",
        profile="selector-scheduler",
        second_brain_root=brain_root,
    )
    assert pack["context_health"]["session_capsules"]["count"] == 1
    assert pack["recent_session_capsules"][0]["title"] == "Selector continuity checkpoint"
    markdown = render_markdown_pack(pack)
    assert "## Operating Posture" in markdown
    assert "Act decisively from current disk evidence" in markdown
    assert "Warnings identify specific repairs or refresh steps; they are triage signals, not broad brakes" in markdown
    assert "## Context Intelligence Health" in markdown
    assert "## Recent Session Capsules" in markdown
    starter = build_starter_prompt(pack, lane="selector-scheduler")
    starter_head = "\n".join(starter.splitlines()[:12])
    assert "Execution posture:" in starter_head
    assert "Use this pack to move the work forward" in starter
    assert "conservative" not in starter.lower()
    assert "passive" not in starter.lower()
    assert "latest_session_capsule:" in starter
    assert "Selector continuity checkpoint" in starter or "selector-continuity-checkpoint" in starter


def test_active_session_state_feeds_pack_markdown_and_starter(tmp_path, capsys):
    repo = tmp_path / "repo"
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/gtos_context_os.md": "# Context OS\n",
        ".context/00_core/gtos_second_brain.md": "# Second Brain\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
        "src/components/selector_v4.py": (
            "def selector_replay_parity():\n"
            "    \"\"\"selector scheduler replay parity\"\"\"\n"
            "    return True\n"
        ),
    }.items():
        _write(repo / rel, text)
    session_write = write_active_session_state(
        repo=repo,
        kind="session",
        title="Current session map",
        task="selector scheduler replay parity",
        current_checkpoint="context os checkpoint writer",
        fixed=["fast pack timeout"],
    )
    assert session_write["status"] == "written"
    time.sleep(0.001)
    assert (
        cli_main(
            [
                "--repo",
                repo.as_posix(),
                "active-state",
                "--write",
                "--kind",
                "root-cause",
                "--title",
                "Current root map",
                "--task",
                "selector scheduler replay parity",
                "--latest-replay-prefix",
                "BROAD_LIVE_AS_IF_REPLAY_TEST",
                "--next-patch-batch",
                "canonical finalizer authority surface",
                "--remaining",
                "route manifest hydration",
                "--source",
                ".context/00_core/gtos_context_os.md",
                "--extra-json",
                '{"confidence": "checkpoint"}',
                "--format",
                "json",
            ]
        )
        == 0
    )
    written = json.loads(capsys.readouterr().out)
    assert written["payload"]["extra"]["confidence"] == "checkpoint"
    build_catalog(repo=repo, db_path="catalog.sqlite")

    state = load_active_session_state(repo=repo)
    assert state["status"] == "present"
    assert state["count"] == 2
    assert state["latest"]["payload"]["latest_replay_prefix"] == "BROAD_LIVE_AS_IF_REPLAY_TEST"
    assert state["latest"]["payload"]["remaining"] == ["route manifest hydration"]

    pack = build_context_pack(
        "selector scheduler replay parity",
        repo=repo,
        db_path="catalog.sqlite",
        profile="selector-scheduler",
    )
    assert pack["active_session_state"]["latest"]["path"].endswith("CURRENT_ROOT_CAUSE_MAP.json")
    markdown = render_markdown_pack(pack)
    assert "## Active Session State" in markdown
    assert "BROAD_LIVE_AS_IF_REPLAY_TEST" in markdown
    starter = build_starter_prompt(pack, lane="selector-scheduler")
    assert "Active session state, verify before use" in starter
    assert "canonical finalizer authority surface" in starter


def test_active_state_renderer_understands_current_root_cause_map_schema(tmp_path):
    repo = tmp_path / "repo"
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/gtos_context_os.md": "# Context OS\n",
        ".context/00_core/gtos_second_brain.md": "# Second Brain\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
    }.items():
        _write(repo / rel, text)
    _write(
        repo / ".context/context_os/CURRENT_ROOT_CAUSE_MAP.json",
        json.dumps(
            {
                "schema_version": "gtos_current_root_cause_map_v1",
                "generated_at_utc": "2026-07-02T13:45:00Z",
                "latest_replay": {
                    "prefix": "BROAD_LIVE_AS_IF_REPLAY_CONTEXT_OS_TEST",
                    "headline_net_r": 1.23,
                },
                "next_same_root_patch_batch": {"name": "route manifest hydration"},
                "fixed": ["fast pack"],
                "partially_fixed": ["route overview"],
                "remaining": ["mcp lifecycle"],
                "subagent_findings": [{"agent": "context"}],
            }
        ),
    )
    build_catalog(repo=repo, db_path="catalog.sqlite")

    state = load_active_session_state(repo=repo)
    payload = state["latest"]["payload"]
    summary = summarize_active_state_payload(payload)
    assert summary["title"] == "Current root-cause map"
    assert summary["latest_replay_prefix"] == "BROAD_LIVE_AS_IF_REPLAY_CONTEXT_OS_TEST"
    assert summary["next_patch_batch"] == "route manifest hydration"
    assert summary["remaining_count"] == 1

    pack = build_context_pack("context os", repo=repo, db_path="catalog.sqlite", allow_stale=True)
    markdown = render_markdown_pack(pack)
    assert "BROAD_LIVE_AS_IF_REPLAY_CONTEXT_OS_TEST" in markdown
    starter = build_starter_prompt(pack)
    assert "route manifest hydration" in starter


def test_continuation_cursor_checkpoint_feeds_pack_starter_http_and_mcp(tmp_path, capsys):
    repo = tmp_path / "repo"
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/gtos_context_os.md": "# Context OS\n",
        ".context/00_core/gtos_second_brain.md": "# Second Brain\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
        "src/components/selector_v4.py": (
            "def finalize_scheduler_risk_authority():\n"
            "    \"\"\"Finalize selected scheduler risk authority.\"\"\"\n"
            "    return 'selector scheduler risk authority'\n"
        ),
    }.items():
        _write(repo / rel, text)
    checkpoint = write_context_checkpoint(
        repo=repo,
        title="Context OS cursor checkpoint",
        task="finalize scheduler risk authority",
        current_checkpoint="pack renders active state and cursor",
        next_patch_batch="wire live symbols into starter",
        last_observation="Read selector finalizer and found risk authority split.",
        current_hypothesis="Continuation loss is caused by missing last-edge cursor.",
        next_atomic_step="Open finalize_scheduler_risk_authority and patch the caller.",
        fixed=["active-state reader"],
        remaining=["starter cursor rendering"],
        files_recently_read=["src/components/selector_v4.py"],
        symbols_recently_checked=["finalize_scheduler_risk_authority"],
        commands_recently_run=["rg finalize_scheduler_risk_authority src"],
        recent_actions=["read selector finalizer"],
        do_not_repeat=["do not rescan raw JSONL before opening exact symbol"],
        verify_next=["python3 -m pytest tests/test_gtos_context_os.py -q"],
        sources=["src/components/selector_v4.py"],
        decisions=["cursor is short-lived working memory"],
        notes=["verify against current disk before acting"],
    )
    assert checkpoint["status"] == "written"
    build_catalog(repo=repo, db_path="catalog.sqlite")

    cursor = load_continuation_cursor(repo=repo)
    assert cursor["status"] == "present"
    cursor_payload = cursor["latest"]["payload"]
    cursor_summary = summarize_continuation_cursor_payload(cursor_payload)
    assert cursor_summary["last_observation"].startswith("Read selector finalizer")
    assert cursor_summary["next_atomic_step"].startswith("Open finalize_scheduler")

    pack = build_context_pack(
        "finalize scheduler risk authority",
        repo=repo,
        db_path="catalog.sqlite",
        profile="selector-scheduler",
    )
    markdown = render_markdown_pack(pack)
    assert pack["continuation_cursor"]["status"] == "present"
    assert pack["symbol_hits"]["hits"]
    assert "## Continuation Cursor" in markdown
    assert "Read selector finalizer" in markdown
    assert "## Live Symbol Hits" in markdown
    assert "finalize_scheduler_risk_authority" in markdown

    starter = build_starter_prompt(pack, lane="selector-scheduler")
    assert "Continuation cursor, verify before use" in starter
    assert "Open finalize_scheduler_risk_authority" in starter
    assert "Live symbol hits, open exact source before claims" in starter

    status, _, body = handle_request("/cursor", repo=repo, db_path="catalog.sqlite")
    assert status == 200
    assert b"Read selector finalizer" in body
    status, _, body = handle_request(
        "/symbols?q=finalize%20scheduler%20risk%20authority&limit=5",
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert status == 200
    assert b"finalize_scheduler_risk_authority" in body

    cursor_response = handle_stdio_request(
        {"method": "cursor", "params": {}},
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert cursor_response["ok"] is True
    assert cursor_response["result"]["latest"]["payload"]["next_atomic_step"].startswith("Open")

    symbol_response = handle_stdio_request(
        {
            "method": "symbols",
            "params": {
                "query": "finalize scheduler risk authority",
                "roots": ["src"],
                "limit": 5,
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert symbol_response["ok"] is True
    assert symbol_response["result"]["hits"][0]["qualname"] == "finalize_scheduler_risk_authority"

    assert (
        cli_main(
            [
                "--repo",
                repo.as_posix(),
                "--db",
                "catalog.sqlite",
                "cursor",
                "--write",
                "--task",
                "finalize scheduler risk authority",
                "--last-observation",
                "CLI cursor wrote a focused continuation edge.",
                "--next-atomic-step",
                "Open the exact symbol before patching.",
                "--format",
                "json",
            ]
        )
        == 0
    )
    cli_cursor = json.loads(capsys.readouterr().out)
    assert cli_cursor["payload"]["last_observation"].startswith("CLI cursor wrote")

    assert (
        cli_main(
            [
                "--repo",
                repo.as_posix(),
                "symbols",
                "finalize scheduler risk authority",
                "--root",
                "src",
                "--limit",
                "5",
                "--format",
                "json",
            ]
        )
        == 0
    )
    cli_symbols = json.loads(capsys.readouterr().out)
    assert cli_symbols["hits"][0]["qualname"] == "finalize_scheduler_risk_authority"


def test_symbol_search_finds_live_python_symbols(tmp_path):
    repo = tmp_path / "repo"
    _write(
        repo / "src/components/scheduler_bridge.py",
        "class SchedulerBridge:\n"
        "    \"\"\"Bridge selected package candidates into scheduler decisions.\"\"\"\n"
        "    def selected_package_bridge_parity(self):\n"
        "        \"\"\"Preserve selected package bridge parity.\"\"\"\n"
        "        return True\n",
    )

    result = search_symbols(
        "selected package bridge parity",
        repo=repo,
        roots=("src",),
        limit=5,
    )

    assert result["parsed_files"] == 1
    assert result["hits"]
    assert result["hits"][0]["qualname"] == "SchedulerBridge.selected_package_bridge_parity"
    assert result["hits"][0]["path"] == "src/components/scheduler_bridge.py"


def test_symbol_search_does_not_parse_large_unrelated_files_by_default(tmp_path):
    repo = tmp_path / "repo"
    _write(
        repo / "src/gtos_context_os/pack.py",
        "def build_context_pack():\n"
        "    return 'context os cursor'\n",
    )
    _write(
        repo / "src/research_infra/huge_blob.py",
        "# uniquegenericneedle generic text\n" * 5000
        + "def unrelated_large_symbol():\n"
        + "    return True\n",
    )

    result = search_symbols(
        "build_context_pack uniquegenericneedle",
        repo=repo,
        roots=("src",),
        limit=5,
        max_files=20,
        max_file_bytes=1000,
        max_elapsed_seconds=1.0,
    )

    assert result["hits"]
    assert result["hits"][0]["qualname"] == "build_context_pack"
    assert all(hit["qualname"] != "unrelated_large_symbol" for hit in result["hits"])
    assert result["elapsed_seconds"] < 1.5


def test_pack_returns_partial_when_optional_health_times_out(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/gtos_context_os.md": "# Context OS\n",
        ".context/00_core/gtos_second_brain.md": "# Second Brain\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
        "src/components/selector_v4.py": "selector scheduler replay parity",
    }.items():
        _write(repo / rel, text)
    build_catalog(repo=repo, db_path="catalog.sqlite")

    def slow_health(**_kwargs):
        time.sleep(2)
        return {"status": "should_not_return"}

    monkeypatch.setattr(pack_module, "context_intelligence_health", slow_health)
    pack = build_context_pack(
        "selector scheduler replay parity",
        repo=repo,
        db_path="catalog.sqlite",
        profile="selector-scheduler",
        section_timeout_seconds=1.0,
    )

    diagnostics = pack["pack_diagnostics"]
    assert diagnostics["partial_result"] is True
    assert diagnostics["section_status"]["context_health"]["status"] == "error"
    assert diagnostics["section_status"]["context_health"]["error_type"] == (
        "ContextPackSectionTimeout"
    )
    assert pack["context_health"]["status"] == "unavailable"


def test_resume_bundle_and_ingest_finding_are_self_contained(tmp_path):
    repo = tmp_path / "repo"
    brain_root = tmp_path / "second-brain"
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/gtos_context_os.md": "# Context OS\n",
        ".context/00_core/gtos_second_brain.md": "# Second Brain\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
        "src/components/selector_v4.py": "selector scheduler replay parity",
    }.items():
        _write(repo / rel, text)

    init_second_brain(root=brain_root, repo=repo)
    finding = ingest_finding(
        "Subagent selector finding",
        "Selector agent found a context mismatch and provided source-backed repair notes.",
        task="selector scheduler replay parity",
        sources=["src/components/selector_v4.py"],
        decisions=["ingest subagent findings as continuity intelligence"],
        tags=["selector", "methodology"],
        repo=repo,
        to_second_brain=True,
        second_brain_root=brain_root,
        reviewed=True,
    )
    assert Path(finding["session_capsule"]).exists()
    assert Path(finding["second_brain_raw"]).exists()
    assert Path(finding["second_brain_card"]).exists()
    assert second_brain_distillation_queue(root=brain_root)

    bundle = build_resume_bundle(
        "selector scheduler replay parity",
        repo=repo,
        db_path="catalog.sqlite",
        profile="selector-scheduler",
        include_memory=False,
        include_second_brain=True,
        second_brain_root=brain_root,
        write_capsule=True,
    )
    assert bundle["schema_version"] == "gtos_context_resume_bundle_v1"
    assert bundle["catalog_build"]["db_path"].endswith("catalog.sqlite")
    assert bundle["health"]["schema_version"] == "gtos_context_intelligence_health_v1"
    assert bundle["health"]["operating_posture"]["mode"] == "strongest_evidence_bound_action"
    assert bundle["health"]["processes"]["status"] in {"ok", "unavailable"}
    assert bundle["health"]["workspace_hygiene"]["raw_evidence_policy"]
    assert bundle["pack"]["context_health"]["session_capsules"]["count"] >= 1
    assert Path(bundle["created_resume_capsule"]).exists()
    assert bundle["git_state"]["scope"] == "context_os_bounded_status_not_full_repo_porcelain"


def test_http_sidecar_serves_read_only_pack_and_errors(tmp_path):
    repo = tmp_path
    _write(repo / ".context/LIVE_STATE.md", "# Live State\n")
    _write(repo / ".context/00_core/current_vnext_system_map.md", "# System Map\n")
    _write(repo / ".context/00_core/current_repo_reading_order.md", "# Reading Order\n")
    _write(repo / ".context/00_core/quick_reference_card.md", "# Quick Reference\n")
    _write(repo / ".context/00_core/repo_cleanup_and_staleness_policy.md", "# Cleanup\n")
    _write(repo / ".context/00_core/research_operating_doctrine.md", "# Doctrine\n")
    _write(repo / ".context/00_core/goal_session_research_discipline.md", "# Discipline\n")
    _write(repo / "src/components/selector_v4.py", "selector scheduler replay parity")
    write_active_session_state(
        repo=repo,
        kind="session",
        title="HTTP active state",
        task="selector scheduler replay parity",
        current_checkpoint="http sidecar active state",
    )
    build_catalog(
        repo=repo,
        db_path="catalog.sqlite",
        roots=(".context", "src/components"),
    )

    status, content_type, body = handle_request(
        "/pack?task=selector%20scheduler%20replay%20parity&profile=ultimate",
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert status == 200
    assert content_type.startswith("application/json")
    assert b"selector scheduler replay parity" in body

    status, _, body = handle_request("/search", repo=repo, db_path="catalog.sqlite")
    assert status == 400
    assert b"missing required query parameter" in body

    status, _, body = handle_request("/health", repo=repo, db_path="catalog.sqlite")
    assert status == 200
    assert b"context_intelligence_health" in body

    status, _, body = handle_request("/active-state", repo=repo, db_path="catalog.sqlite")
    assert status == 200
    assert b"HTTP active state" in body

    status, _, body = handle_request(
        "/resume?task=selector%20scheduler%20replay%20parity&profile=ultimate",
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert status == 200
    assert b"gtos_context_resume_bundle_v1" in body


def test_starter_and_stdio_tool_surface(tmp_path):
    repo = tmp_path
    _write(repo / ".context/LIVE_STATE.md", "# Live State\n")
    _write(repo / ".context/00_core/current_vnext_system_map.md", "# System Map\n")
    _write(repo / ".context/00_core/current_repo_reading_order.md", "# Reading Order\n")
    _write(repo / ".context/00_core/quick_reference_card.md", "# Quick Reference\n")
    _write(repo / ".context/00_core/repo_cleanup_and_staleness_policy.md", "# Cleanup\n")
    _write(repo / ".context/00_core/research_operating_doctrine.md", "# Doctrine\n")
    _write(repo / ".context/00_core/goal_session_research_discipline.md", "# Discipline\n")
    _write(repo / ".context/00_core/gtos_context_os.md", "# Context OS\n")
    _write(repo / "src/components/selector_v4.py", "selector scheduler replay parity")
    build_catalog(
        repo=repo,
        db_path="catalog.sqlite",
        roots=(".context", "src/components"),
    )

    pack = build_context_pack(
        "selector scheduler replay parity",
        repo=repo,
        db_path="catalog.sqlite",
        profile="selector-scheduler",
    )
    starter = build_starter_prompt(pack, lane="selector-scheduler")
    assert "Context OS starter for lane: selector-scheduler" in starter
    assert "Doctrine checklist" in starter
    assert "src/components/selector_v4.py" in starter

    response = handle_stdio_request(
        {
            "method": "pack",
            "params": {
                "task": "selector scheduler replay parity",
                "profile": "selector-scheduler",
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert response["ok"] is True
    assert response["result"]["profile"] == "selector-scheduler"

    health_response = handle_stdio_request(
        {"method": "health", "params": {"session_capsule_limit": 3}},
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert health_response["ok"] is True
    assert health_response["result"]["schema_version"] == "gtos_context_intelligence_health_v1"

    resume_response = handle_stdio_request(
        {
            "method": "resume",
            "params": {
                "task": "selector scheduler replay parity",
                "profile": "selector-scheduler",
                "include_memory": False,
                "include_second_brain": False,
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert resume_response["ok"] is True
    assert resume_response["result"]["schema_version"] == "gtos_context_resume_bundle_v1"


def test_mcp_stdio_supports_real_mcp_tool_lifecycle(tmp_path):
    repo = tmp_path
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\nfirst\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
        ".context/00_core/gtos_context_os.md": "# Context OS\n",
        "src/components/selector_v4.py": (
            "def selector_replay_parity():\n"
            "    \"\"\"selector scheduler replay parity\"\"\"\n"
            "    return True\n"
        ),
    }.items():
        _write(repo / rel, text)
    build_catalog(repo=repo, db_path="catalog.sqlite", roots=(".context", "src/components"))

    init_response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "0"},
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert init_response["jsonrpc"] == "2.0"
    assert init_response["result"]["capabilities"]["tools"]["listChanged"] is False

    tools_response = handle_mcp_request(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        repo=repo,
        db_path="catalog.sqlite",
    )
    tool_names = {tool["name"] for tool in tools_response["result"]["tools"]}
    assert "gtos_context_pack" in tool_names
    assert "gtos_context_fast_pack" in tool_names
    assert "gtos_second_brain_search" in tool_names
    assert "gtos_second_brain_read" in tool_names
    assert "gtos_context_read_file" in tool_names
    assert "gtos_active_session_state" in tool_names
    assert "gtos_continuation_cursor" in tool_names
    assert "gtos_code_symbol_search" in tool_names

    call_response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "gtos_context_pack",
                "arguments": {
                    "task": "selector scheduler replay parity",
                    "profile": "selector-scheduler",
                },
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    result = call_response["result"]
    assert result["isError"] is False
    assert result["content"][0]["type"] == "text"
    assert result["structuredContent"]["profile"] == "selector-scheduler"
    assert result["structuredContent"]["pack_diagnostics"]["section_status"]

    fast_response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 33,
            "method": "tools/call",
            "params": {
                "name": "gtos_context_fast_pack",
                "arguments": {
                    "task": "selector scheduler replay parity",
                    "profile": "selector-scheduler",
                },
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    fast_result = fast_response["result"]
    assert fast_result["isError"] is False
    assert fast_result["structuredContent"]["context_health"]["status"] == "skipped"

    _write(repo / ".context/LIVE_STATE.md", "# Live State\nchanged after catalog build\n")
    stale_fast_response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 34,
            "method": "tools/call",
            "params": {
                "name": "gtos_context_fast_pack",
                "arguments": {
                    "task": "selector scheduler replay parity",
                    "profile": "selector-scheduler",
                },
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    stale_fast_result = stale_fast_response["result"]
    assert stale_fast_result["isError"] is False
    assert stale_fast_result["structuredContent"]["catalog_freshness"]["status"] == "stale"
    assert stale_fast_result["structuredContent"]["context_health"]["status"] == "skipped"

    write_active_session_state(
        repo=repo,
        kind="session",
        title="MCP active state",
        task="selector scheduler replay parity",
    )
    active_state_response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 35,
            "method": "tools/call",
            "params": {
                "name": "gtos_active_session_state",
                "arguments": {},
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    active_state_result = active_state_response["result"]
    assert active_state_result["isError"] is False
    assert active_state_result["structuredContent"]["latest"]["payload"]["title"] == "MCP active state"

    write_continuation_cursor(
        repo=repo,
        task="selector scheduler replay parity",
        last_observation="MCP cursor observation",
        next_atomic_step="Open selector_v4 symbol.",
    )
    cursor_response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 36,
            "method": "tools/call",
            "params": {
                "name": "gtos_continuation_cursor",
                "arguments": {},
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    cursor_result = cursor_response["result"]
    assert cursor_result["isError"] is False
    assert cursor_result["structuredContent"]["latest"]["payload"]["last_observation"] == "MCP cursor observation"

    symbol_response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 37,
            "method": "tools/call",
            "params": {
                "name": "gtos_code_symbol_search",
                "arguments": {"query": "selector", "roots": ["src"], "limit": 5},
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    symbol_result = symbol_response["result"]
    assert symbol_result["isError"] is False
    assert symbol_result["structuredContent"]["hit_count"] >= 1

    read_response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "gtos_context_read_file",
                "arguments": {"path": "src/components/selector_v4.py", "max_chars": 5000},
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert read_response["result"]["isError"] is False
    assert "selector scheduler replay parity" in read_response["result"]["structuredContent"]["text"]


def test_second_brain_capture_distill_graph_and_search(tmp_path):
    root = tmp_path / "second-brain"
    init_result = init_second_brain(root=root, repo=tmp_path)

    assert init_result["status"] == "ready"
    assert (root / "inbox").exists()
    assert (root / "00_START_HERE.md").exists()

    raw = capture_idea(
        "We need agents to keep context hygiene strong and not treat stale raw thoughts as authority.",
        title="Context hygiene idea",
        tags=["methodology"],
        root=root,
    )
    assert raw.exists()
    assert "raw_inbox_not_agent_authority" in raw.read_text(encoding="utf-8")

    distilled = distill_idea(raw, root=root)
    distilled_text = distilled.read_text(encoding="utf-8")
    assert "candidate_distillation_needs_review" in distilled_text
    assert "[[inbox/" in distilled_text

    hits = search_second_brain("context hygiene authority", root=root)
    assert hits
    assert hits[0]["authority_tier"] == "second_brain_distilled_intelligence"
    assert hits[0]["freshness"] == "verify_against_current_disk"

    pack_snapshot = root / "context-packs" / "GTOS_CURRENT_CONTEXT_PACK.md"
    pack_snapshot.parent.mkdir(parents=True, exist_ok=True)
    pack_snapshot.write_text(
        "---\nstatus: generated_human_snapshot\n---\n# Old context hygiene authority pack\n",
        encoding="utf-8",
    )
    assert all("context-packs/" not in hit["path"] for hit in search_second_brain("context hygiene authority", root=root))

    graph = generate_second_brain_graph(root=root)
    assert graph["nodes"] >= 2
    assert Path(graph["json"]).exists()
    assert Path(graph["mermaid"]).exists()
    assert Path(graph["index"]).exists()
    index_text = Path(graph["index"]).read_text(encoding="utf-8")
    assert "status: generated_human_snapshot" in index_text
    assert "#methodology` `tag`" in index_text
    assert "[[tag/methodology" not in index_text

    status = second_brain_status(root=root)
    assert status["exists"] is True
    assert status["counts_by_status"]["raw_inbox_not_agent_authority"] >= 1
    assert status["counts_by_status"]["candidate_distillation_needs_review"] >= 1
    assert "unlabeled" not in status["counts_by_status"]
    assert all(not hit["path"].endswith("README.md") for hit in hits)


def test_second_brain_search_prefers_specific_title_over_broad_body_repetition(tmp_path):
    root = tmp_path / "second-brain"
    init_second_brain(root=root, repo=tmp_path)
    _write(
        root / "conversation-intelligence" / "Broad_Index.md",
        "---\nstatus: current_retrieval_intelligence\ntitle: Broad Index\n---\n"
        "# Broad Index\n\nselector scheduler context hygiene " * 20,
    )
    _write(
        root / "component-flow" / "Selector_Scheduler_Context_Hygiene_Map.md",
        "---\nstatus: current_retrieval_intelligence\ntitle: Selector Scheduler Context Hygiene Map\n---\n"
        "# Selector Scheduler Context Hygiene Map\n\nspecific map\n",
    )

    hits = search_second_brain("selector scheduler context hygiene", root=root, limit=3)

    assert hits
    assert hits[0]["path"] == "component-flow/Selector_Scheduler_Context_Hygiene_Map.md"


def test_pack_http_and_stdio_include_second_brain(tmp_path):
    repo = tmp_path / "repo"
    brain_root = tmp_path / "second-brain"
    for rel, text in {
        ".context/LIVE_STATE.md": "# Live State\n",
        ".context/00_core/current_vnext_system_map.md": "# System Map\n",
        ".context/00_core/current_repo_reading_order.md": "# Reading Order\n",
        ".context/00_core/quick_reference_card.md": "# Quick Reference\n",
        ".context/00_core/gtos_context_os.md": "# Context OS\n",
        ".context/00_core/gtos_second_brain.md": "# Second Brain\n",
        ".context/00_core/repo_cleanup_and_staleness_policy.md": "# Cleanup\n",
        ".context/00_core/research_operating_doctrine.md": "# Doctrine\n",
        ".context/00_core/goal_session_research_discipline.md": "# Discipline\n",
        "src/components/selector_v4.py": "selector scheduler replay parity",
    }.items():
        _write(repo / rel, text)

    build_catalog(repo=repo, db_path="catalog.sqlite")
    init_second_brain(root=brain_root, repo=repo)
    raw = capture_idea(
        "Selector scheduler agents should retrieve distilled methodology and verify current disk.",
        title="Selector methodology",
        root=brain_root,
    )
    distill_idea(raw, root=brain_root)

    pack = build_context_pack(
        "selector scheduler methodology",
        repo=repo,
        db_path="catalog.sqlite",
        profile="ultimate",
        include_second_brain=True,
        second_brain_root=brain_root,
    )
    markdown = render_markdown_pack(pack)
    assert pack["second_brain"]["hits"]
    assert "## GTOS Second Brain" in markdown
    assert "raw inbox notes are preserved, not direct agent authority" in markdown

    status, _, body = handle_request(
        f"/pack?task=selector%20scheduler%20methodology&profile=ultimate&include_second_brain=1&second_brain_root={brain_root.as_posix()}",
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert status == 200
    assert b"second_brain" in body

    response = handle_stdio_request(
        {
            "method": "second_brain_search",
            "params": {
                "query": "selector methodology",
                "root": brain_root.as_posix(),
            },
        },
        repo=repo,
        db_path="catalog.sqlite",
    )
    assert response["ok"] is True
    assert response["result"]
