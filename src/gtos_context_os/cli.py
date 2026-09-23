"""Command-line interface for GTOS Context OS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.gtos_context_os.catalog import (
    DEFAULT_DB_PATH,
    DEFAULT_MAX_TEXT_BYTES,
    DEFAULT_ROOTS,
    DEEP_CONTEXT_ROOTS,
    build_catalog,
    catalog_stats,
    catalog_freshness,
    search_catalog,
)
from src.gtos_context_os.classifier import classify_path
from src.gtos_context_os.health import context_intelligence_health
from src.gtos_context_os.ingest import ingest_finding
from src.gtos_context_os.memory import search_memory
from src.gtos_context_os.pack import build_context_pack, render_markdown_pack
from src.gtos_context_os.resume import build_resume_bundle
from src.gtos_context_os.route import route_overview
from src.gtos_context_os.server import serve_context_os
from src.gtos_context_os.second_brain import (
    DEFAULT_SECOND_BRAIN_ROOT,
    capture_idea,
    distill_idea,
    generate_second_brain_graph,
    init_second_brain,
    search_second_brain,
    second_brain_status,
)
from src.gtos_context_os.session import create_session_capsule, list_session_capsules, session_capsule_status
from src.gtos_context_os.session_state import (
    load_continuation_cursor,
    load_active_session_state,
    write_context_checkpoint,
    write_continuation_cursor,
    write_active_session_state,
)
from src.gtos_context_os.starter import build_starter_prompt
from src.gtos_context_os.symbols import search_symbols
from src.gtos_context_os.writeback import create_writeback_proposal
from src.gtos_context_os.mcp_stdio import serve_stdio


PACK_PROFILES = (
    "standard",
    "implementation",
    "research",
    "ultimate",
    "replay-repair",
    "selector-scheduler",
    "cost-order",
    "lifecycle-exit",
    "verifier-audit",
    "context-cleanup",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Catalog SQLite path, repo-relative unless absolute.")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    build = sub.add_parser("build", help="Build or rebuild the context catalog.")
    build.add_argument("--root", action="append", dest="roots", help="Root/path to index. May be repeated.")
    build.add_argument(
        "--scope",
        choices=("current", "deep"),
        default="current",
        help="Catalog root profile when --root is not supplied. Default: current.",
    )
    build.add_argument("--include-jsonl", action="store_true", help="Index JSONL text. Off by default.")
    build.add_argument(
        "--include-cold-metadata",
        action="store_true",
        default=True,
        help="Catalog metadata-only pointers for cold or large files without indexing their text. Default: on.",
    )
    build.add_argument(
        "--no-cold-metadata",
        action="store_false",
        dest="include_cold_metadata",
        help="Skip cold/raw metadata pointers.",
    )
    build.add_argument("--max-file-bytes", type=int, default=1_000_000)
    build.add_argument("--max-text-bytes", type=int, default=DEFAULT_MAX_TEXT_BYTES)
    build.add_argument(
        "--hash-indexed-text",
        action="store_true",
        help="Compute sha256 for every indexed text file. Off by default for fast preflight builds.",
    )
    build.add_argument(
        "--force",
        action="store_true",
        help="Force a rebuild even when an equivalent fresh catalog already exists.",
    )
    build.add_argument("--format", choices=("json", "text"), default="text")

    search = sub.add_parser("search", help="Search the context catalog.")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=12)
    search.add_argument("--format", choices=("json", "text"), default="text")

    symbols = sub.add_parser("symbols", help="Search live Python symbols by name/path/docstring.")
    symbols.add_argument("query")
    symbols.add_argument("--root", action="append", dest="roots", help="Root/path to scan. May be repeated.")
    symbols.add_argument("--limit", type=int, default=20)
    symbols.add_argument("--max-files", type=int, default=5000)
    symbols.add_argument("--max-file-bytes", type=int, default=750_000)
    symbols.add_argument("--max-elapsed-seconds", type=float, default=5.0)
    symbols.add_argument("--format", choices=("json", "text"), default="text")

    pack = sub.add_parser("pack", help="Build a compact context pack for an agent task.")
    pack.add_argument("--task", required=True)
    pack.add_argument("--limit", type=int, default=10)
    pack.add_argument("--profile", choices=PACK_PROFILES, default="standard")
    pack.add_argument("--route")
    pack.add_argument("--include-memory", action="store_true")
    pack.add_argument("--memory-root")
    pack.add_argument("--include-second-brain", action="store_true")
    pack.add_argument("--second-brain-root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    pack.add_argument("--second-brain-query")
    pack.add_argument("--fast", action="store_true", help="Skip health and use short section timeouts.")
    pack.add_argument("--no-health", action="store_true", help="Skip context health inside the pack.")
    pack.add_argument("--section-timeout-seconds", type=float, default=None)
    pack.add_argument("--allow-stale", action="store_true")
    pack.add_argument(
        "--auto-rebuild-stale",
        action="store_true",
        default=True,
        help="Rebuild automatically when the catalog is stale. Default: on.",
    )
    pack.add_argument(
        "--no-auto-rebuild-stale",
        action="store_false",
        dest="auto_rebuild_stale",
        help="Fail closed instead of rebuilding when the catalog is stale.",
    )
    pack.add_argument("--format", choices=("json", "markdown"), default="markdown")
    pack.add_argument("--no-auto-build", action="store_true")

    starter = sub.add_parser("starter", help="Generate a doctrine-aware subagent/goal starter prompt.")
    starter.add_argument("--task", required=True)
    starter.add_argument("--lane", default="general")
    starter.add_argument("--limit", type=int, default=10)
    starter.add_argument("--profile", choices=PACK_PROFILES, default="ultimate")
    starter.add_argument("--route")
    starter.add_argument("--include-memory", action="store_true")
    starter.add_argument("--memory-root")
    starter.add_argument("--include-second-brain", action="store_true")
    starter.add_argument("--second-brain-root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    starter.add_argument("--second-brain-query")
    starter.add_argument("--fast", action="store_true", help="Skip health and use short section timeouts.")
    starter.add_argument("--no-health", action="store_true", help="Skip context health inside the pack.")
    starter.add_argument("--section-timeout-seconds", type=float, default=None)
    starter.add_argument("--allow-stale", action="store_true")
    starter.add_argument(
        "--auto-rebuild-stale",
        action="store_true",
        default=True,
        help="Rebuild automatically when the catalog is stale. Default: on.",
    )
    starter.add_argument(
        "--no-auto-rebuild-stale",
        action="store_false",
        dest="auto_rebuild_stale",
        help="Fail closed instead of rebuilding when the catalog is stale.",
    )
    starter.add_argument("--no-auto-build", action="store_true")

    resume = sub.add_parser("resume", help="Build a one-stop resume bundle after compaction or restart.")
    resume.add_argument("--task", required=True)
    resume.add_argument("--limit", type=int, default=10)
    resume.add_argument("--profile", choices=PACK_PROFILES, default="ultimate")
    resume.add_argument("--route")
    resume.add_argument("--include-memory", action="store_true", default=True)
    resume.add_argument("--no-memory", action="store_false", dest="include_memory")
    resume.add_argument("--include-second-brain", action="store_true", default=True)
    resume.add_argument("--no-second-brain", action="store_false", dest="include_second_brain")
    resume.add_argument("--second-brain-root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    resume.add_argument("--no-write-capsule", action="store_true")
    resume.add_argument("--pack-markdown", action="store_true")
    resume.add_argument("--format", choices=("json", "text"), default="json")

    memory = sub.add_parser("memory", help="Search controlled Codex memory registry files.")
    memory.add_argument("query")
    memory.add_argument("--limit", type=int, default=8)
    memory.add_argument("--memory-root")
    memory.add_argument("--format", choices=("json", "text"), default="text")

    route = sub.add_parser("route", help="Summarize route artifacts from the catalog.")
    route.add_argument("route")
    route.add_argument("--limit", type=int, default=25)
    route.add_argument("--format", choices=("json", "text"), default="text")

    export = sub.add_parser("obsidian-export", help="Write a markdown context pack for an Obsidian vault/file.")
    export.add_argument("--task", required=True)
    export.add_argument("--out", required=True)
    export.add_argument("--limit", type=int, default=12)
    export.add_argument("--profile", choices=PACK_PROFILES, default="ultimate")
    export.add_argument("--route")
    export.add_argument("--include-memory", action="store_true")
    export.add_argument("--memory-root")
    export.add_argument("--include-second-brain", action="store_true")
    export.add_argument("--second-brain-root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    export.add_argument("--second-brain-query")

    writeback = sub.add_parser("propose-writeback", help="Create a source-backed canonical memory/context proposal.")
    writeback.add_argument("--title", required=True)
    writeback.add_argument("--body", required=True)
    writeback.add_argument("--source", action="append", default=[])
    writeback.add_argument("--out-dir", default=".context/context_os/writeback_proposals")
    writeback.add_argument("--format", choices=("json", "text"), default="text")

    capsule = sub.add_parser("session-capsule", help="Write a local structured session capsule.")
    capsule.add_argument("--title", required=True)
    capsule.add_argument("--summary", required=True)
    capsule.add_argument("--task", default="")
    capsule.add_argument("--source", action="append", default=[])
    capsule.add_argument("--command", action="append", default=[])
    capsule.add_argument("--decision", action="append", default=[])
    capsule.add_argument("--out-dir", default=".context/context_os/session_capsules")
    capsule.add_argument("--format", choices=("json", "text"), default="text")

    sessions = sub.add_parser("session-capsules", help="Read recent local continuity capsules.")
    sessions.add_argument("--limit", type=int, default=5)
    sessions.add_argument("--task-query")
    sessions.add_argument("--out-dir", default=".context/context_os/session_capsules")
    sessions.add_argument("--status", action="store_true", help="Show capsule store status instead of recent capsules.")
    sessions.add_argument("--format", choices=("json", "text"), default="text")

    active_state = sub.add_parser("active-state", help="Read or write compact active session/root-cause state.")
    active_state.add_argument("--write", action="store_true", help="Write a compact active-state checkpoint.")
    active_state.add_argument("--kind", choices=("session", "root-cause"), default="session")
    active_state.add_argument("--path", help="Optional repo-relative state path override.")
    active_state.add_argument("--title", default="")
    active_state.add_argument("--task", default="")
    active_state.add_argument("--latest-replay-prefix", default="")
    active_state.add_argument("--current-checkpoint", default="")
    active_state.add_argument("--next-patch-batch", default="")
    active_state.add_argument("--fixed", action="append", default=[])
    active_state.add_argument("--partially-fixed", action="append", default=[])
    active_state.add_argument("--remaining", action="append", default=[])
    active_state.add_argument("--blocker", action="append", default=[])
    active_state.add_argument("--source", action="append", default=[])
    active_state.add_argument("--decision", action="append", default=[])
    active_state.add_argument("--note", action="append", default=[])
    active_state.add_argument("--extra-json", help="Optional JSON object merged under payload.extra.")
    active_state.add_argument("--format", choices=("json", "text"), default="json")

    cursor = sub.add_parser("cursor", help="Read or write the compact continuation cursor.")
    cursor.add_argument("--write", action="store_true", help="Write the continuation cursor.")
    cursor.add_argument("--task", default="")
    cursor.add_argument("--mode", default="checkpoint")
    cursor.add_argument("--last-observation", default="")
    cursor.add_argument("--current-hypothesis", default="")
    cursor.add_argument("--next-atomic-step", default="")
    cursor.add_argument("--file", action="append", default=[], dest="files_recently_read")
    cursor.add_argument("--symbol", action="append", default=[], dest="symbols_recently_checked")
    cursor.add_argument("--command", action="append", default=[], dest="commands_recently_run")
    cursor.add_argument("--action", action="append", default=[], dest="recent_actions")
    cursor.add_argument("--do-not-repeat", action="append", default=[])
    cursor.add_argument("--verify-next", action="append", default=[])
    cursor.add_argument("--source", action="append", default=[])
    cursor.add_argument("--note", action="append", default=[])
    cursor.add_argument("--format", choices=("json", "text"), default="json")

    checkpoint = sub.add_parser("checkpoint", help="Write active state and continuation cursor together.")
    checkpoint.add_argument("--title", required=True)
    checkpoint.add_argument("--task", required=True)
    checkpoint.add_argument("--current-checkpoint", required=True)
    checkpoint.add_argument("--next-patch-batch", default="")
    checkpoint.add_argument("--last-observation", required=True)
    checkpoint.add_argument("--current-hypothesis", default="")
    checkpoint.add_argument("--next-atomic-step", default="")
    checkpoint.add_argument("--fixed", action="append", default=[])
    checkpoint.add_argument("--partially-fixed", action="append", default=[])
    checkpoint.add_argument("--remaining", action="append", default=[])
    checkpoint.add_argument("--blocker", action="append", default=[])
    checkpoint.add_argument("--file", action="append", default=[], dest="files_recently_read")
    checkpoint.add_argument("--symbol", action="append", default=[], dest="symbols_recently_checked")
    checkpoint.add_argument("--command", action="append", default=[], dest="commands_recently_run")
    checkpoint.add_argument("--action", action="append", default=[], dest="recent_actions")
    checkpoint.add_argument("--do-not-repeat", action="append", default=[])
    checkpoint.add_argument("--verify-next", action="append", default=[])
    checkpoint.add_argument("--source", action="append", default=[])
    checkpoint.add_argument("--decision", action="append", default=[])
    checkpoint.add_argument("--note", action="append", default=[])
    checkpoint.add_argument("--format", choices=("json", "text"), default="json")

    ingest = sub.add_parser("ingest-finding", help="Capture a subagent/session finding as bounded continuity intelligence.")
    ingest.add_argument("--title", required=True)
    ingest.add_argument("--body")
    ingest.add_argument("--body-file")
    ingest.add_argument("--task", default="")
    ingest.add_argument("--source", action="append", default=[])
    ingest.add_argument("--command", action="append", default=[])
    ingest.add_argument("--decision", action="append", default=[])
    ingest.add_argument("--tag", action="append", default=[])
    ingest.add_argument("--to-second-brain", action="store_true")
    ingest.add_argument("--reviewed", action="store_true")
    ingest.add_argument("--second-brain-root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    ingest.add_argument("--format", choices=("json", "text"), default="json")

    serve = sub.add_parser("serve", help="Run the read-only local Context OS HTTP sidecar.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    sub.add_parser("mcp-stdio", help="Run the read-only GTOS Context OS MCP stdio server.")

    brain = sub.add_parser("brain", help="Capture, distill, search, and graph the GTOS second-brain vault.")
    brain_sub = brain.add_subparsers(dest="brain_command", required=True)
    brain_init = brain_sub.add_parser("init", help="Create the second-brain vault scaffold.")
    brain_init.add_argument("--root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    brain_init.add_argument("--format", choices=("json", "text"), default="text")

    brain_capture = brain_sub.add_parser("capture", help="Capture one raw idea into the inbox.")
    brain_capture.add_argument("--title")
    brain_capture.add_argument("--body")
    brain_capture.add_argument("--body-file")
    brain_capture.add_argument("--tag", action="append", default=[])
    brain_capture.add_argument("--source", default="manual")
    brain_capture.add_argument("--root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    brain_capture.add_argument("--format", choices=("json", "text"), default="text")

    brain_distill = brain_sub.add_parser("distill", help="Distill one raw inbox note into a structured card.")
    brain_distill.add_argument("--source")
    brain_distill.add_argument("--latest", action="store_true")
    brain_distill.add_argument("--reviewed", action="store_true")
    brain_distill.add_argument("--root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    brain_distill.add_argument("--format", choices=("json", "text"), default="text")

    brain_search = brain_sub.add_parser("search", help="Search distilled second-brain notes.")
    brain_search.add_argument("query")
    brain_search.add_argument("--limit", type=int, default=10)
    brain_search.add_argument("--include-raw", action="store_true")
    brain_search.add_argument("--root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    brain_search.add_argument("--format", choices=("json", "text"), default="text")

    brain_graph = brain_sub.add_parser("graph", help="Regenerate the graph JSON, Mermaid map, and index.")
    brain_graph.add_argument("--root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    brain_graph.add_argument("--format", choices=("json", "text"), default="text")

    brain_status = brain_sub.add_parser("status", help="Show second-brain vault status.")
    brain_status.add_argument("--root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    brain_status.add_argument("--format", choices=("json", "text"), default="text")

    classify = sub.add_parser("classify", help="Classify one repo-relative path.")
    classify.add_argument("path")
    classify.add_argument("--format", choices=("json", "text"), default="text")

    stats = sub.add_parser("stats", help="Show catalog stats.")
    stats.add_argument("--format", choices=("json", "text"), default="text")

    freshness = sub.add_parser("freshness", help="Check whether the catalog matches current HEAD/authority anchors.")
    freshness.add_argument("--format", choices=("json", "text"), default="text")

    health = sub.add_parser("health", help="Show Context OS, second-brain, and continuity health.")
    health.add_argument("--second-brain-root", default=str(DEFAULT_SECOND_BRAIN_ROOT))
    health.add_argument("--session-capsule-limit", type=int, default=5)
    health.add_argument("--format", choices=("json", "text"), default="text")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo)
    db = Path(args.db)

    if args.subcommand == "build":
        roots = tuple(args.roots) if args.roots else (
            DEEP_CONTEXT_ROOTS if args.scope == "deep" else DEFAULT_ROOTS
        )
        result = build_catalog(
            repo=repo,
            db_path=db,
            roots=roots,
            include_jsonl=args.include_jsonl,
            include_cold_metadata=args.include_cold_metadata,
            max_file_bytes=args.max_file_bytes,
            max_text_bytes=args.max_text_bytes,
            hash_indexed_text=args.hash_indexed_text,
            reuse_fresh=not args.force,
        )
        payload: dict[str, Any] = {
            "db_path": result.db_path.as_posix(),
            "indexed_documents": result.indexed_documents,
            "metadata_only_documents": result.metadata_only_documents,
            "skipped_paths": result.skipped_paths,
            "roots": list(result.roots),
            "generated_at_utc": result.generated_at_utc,
            "reused_existing": result.reused_existing,
        }
        _emit(payload, args.format)
        return 0

    if args.subcommand == "search":
        _emit(search_catalog(args.query, db_path=db, repo=repo, limit=args.limit), args.format)
        return 0

    if args.subcommand == "symbols":
        _emit(
            search_symbols(
                args.query,
                repo=repo,
                roots=tuple(args.roots) if args.roots else ("src", "scripts", "tests"),
                limit=args.limit,
                max_files=args.max_files,
                max_file_bytes=args.max_file_bytes,
                max_elapsed_seconds=args.max_elapsed_seconds,
            ),
            args.format,
        )
        return 0

    if args.subcommand == "pack":
        section_timeout = (
            args.section_timeout_seconds
            if args.section_timeout_seconds is not None
            else (3.0 if args.fast else 8.0)
        )
        allow_stale = args.allow_stale or args.fast
        auto_rebuild_stale = False if args.fast else args.auto_rebuild_stale
        auto_build = False if args.fast else not args.no_auto_build
        payload = build_context_pack(
            args.task,
            repo=repo,
            db_path=db,
            limit=args.limit,
            profile=args.profile,
            route=args.route,
            include_memory=args.include_memory,
            memory_root=args.memory_root,
            include_second_brain=args.include_second_brain,
            second_brain_root=args.second_brain_root,
            second_brain_query=args.second_brain_query,
            include_health=not (args.no_health or args.fast),
            section_timeout_seconds=section_timeout,
            allow_stale=allow_stale,
            auto_rebuild_stale=auto_rebuild_stale,
            auto_build=auto_build,
        )
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(render_markdown_pack(payload), end="")
        return 0

    if args.subcommand == "starter":
        section_timeout = (
            args.section_timeout_seconds
            if args.section_timeout_seconds is not None
            else (3.0 if args.fast else 8.0)
        )
        allow_stale = args.allow_stale or args.fast
        auto_rebuild_stale = False if args.fast else args.auto_rebuild_stale
        auto_build = False if args.fast else not args.no_auto_build
        payload = build_context_pack(
            args.task,
            repo=repo,
            db_path=db,
            limit=args.limit,
            profile=args.profile,
            route=args.route,
            include_memory=args.include_memory,
            memory_root=args.memory_root,
            include_second_brain=args.include_second_brain,
            second_brain_root=args.second_brain_root,
            second_brain_query=args.second_brain_query,
            include_health=not (args.no_health or args.fast),
            section_timeout_seconds=section_timeout,
            allow_stale=allow_stale,
            auto_rebuild_stale=auto_rebuild_stale,
            auto_build=auto_build,
        )
        print(build_starter_prompt(payload, lane=args.lane), end="")
        return 0

    if args.subcommand == "resume":
        payload = build_resume_bundle(
            args.task,
            repo=repo,
            db_path=db,
            limit=args.limit,
            profile=args.profile,
            route=args.route,
            include_memory=args.include_memory,
            include_second_brain=args.include_second_brain,
            second_brain_root=args.second_brain_root,
            write_capsule=not args.no_write_capsule,
            markdown_pack=args.pack_markdown,
        )
        _emit(payload, args.format)
        return 0

    if args.subcommand == "memory":
        _emit(
            search_memory(args.query, memory_root=args.memory_root, limit=args.limit),
            args.format,
        )
        return 0

    if args.subcommand == "route":
        _emit(route_overview(args.route, repo=repo, db_path=db, limit=args.limit), args.format)
        return 0

    if args.subcommand == "obsidian-export":
        payload = build_context_pack(
            args.task,
            repo=repo,
            db_path=db,
            limit=args.limit,
            profile=args.profile,
            route=args.route,
            include_memory=args.include_memory,
            memory_root=args.memory_root,
            include_second_brain=args.include_second_brain,
            second_brain_root=args.second_brain_root,
            second_brain_query=args.second_brain_query,
            auto_rebuild_stale=True,
        )
        out = Path(args.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        rendered = "---\n"
        rendered += "gtos_context_os: true\n"
        rendered += "schema: gtos_context_pack_obsidian_export_v1\n"
        rendered += "status: generated_human_snapshot\n"
        rendered += "evidence_class: context_pack_snapshot\n"
        rendered += f"generated_at_utc: {payload['generated_at_utc']}\n"
        rendered += f"profile: {payload['profile']}\n"
        if payload.get("task"):
            rendered += f"task: {json.dumps(payload['task'])}\n"
        rendered += "---\n\n"
        rendered += render_markdown_pack(payload)
        out.write_text(rendered, encoding="utf-8")
        print(out.as_posix())
        return 0

    if args.subcommand == "propose-writeback":
        path = create_writeback_proposal(
            args.title,
            args.body,
            sources=args.source,
            repo=repo,
            out_dir=args.out_dir,
        )
        payload = {"path": path.as_posix()}
        _emit(payload, args.format)
        return 0

    if args.subcommand == "session-capsule":
        path = create_session_capsule(
            args.title,
            args.summary,
            task=args.task,
            sources=args.source,
            commands=args.command,
            decisions=args.decision,
            repo=repo,
            out_dir=args.out_dir,
        )
        _emit({"path": path.as_posix()}, args.format)
        return 0

    if args.subcommand == "session-capsules":
        if args.status:
            _emit(
                session_capsule_status(
                    repo=repo,
                    out_dir=args.out_dir,
                    limit=args.limit,
                ),
                args.format,
            )
            return 0
        _emit(
            list_session_capsules(
                repo=repo,
                out_dir=args.out_dir,
                limit=args.limit,
                task_query=args.task_query,
            ),
            args.format,
        )
        return 0

    if args.subcommand == "active-state":
        if args.write:
            extra = json.loads(args.extra_json) if args.extra_json else None
            if extra is not None and not isinstance(extra, dict):
                raise SystemExit("--extra-json must be a JSON object")
            _emit(
                write_active_session_state(
                    repo=repo,
                    kind=args.kind,
                    path=args.path,
                    title=args.title,
                    task=args.task,
                    latest_replay_prefix=args.latest_replay_prefix,
                    current_checkpoint=args.current_checkpoint,
                    next_patch_batch=args.next_patch_batch,
                    fixed=args.fixed,
                    partially_fixed=args.partially_fixed,
                    remaining=args.remaining,
                    blockers=args.blocker,
                    sources=args.source,
                    decisions=args.decision,
                    notes=args.note,
                    extra=extra,
                ),
                args.format,
            )
            return 0
        _emit(load_active_session_state(repo=repo), args.format)
        return 0

    if args.subcommand == "cursor":
        if args.write:
            _emit(
                write_continuation_cursor(
                    repo=repo,
                    task=args.task,
                    mode=args.mode,
                    last_observation=args.last_observation,
                    current_hypothesis=args.current_hypothesis,
                    next_atomic_step=args.next_atomic_step,
                    files_recently_read=args.files_recently_read,
                    symbols_recently_checked=args.symbols_recently_checked,
                    commands_recently_run=args.commands_recently_run,
                    recent_actions=args.recent_actions,
                    do_not_repeat=args.do_not_repeat,
                    verify_next=args.verify_next,
                    sources=args.source,
                    notes=args.note,
                ),
                args.format,
            )
            return 0
        _emit(load_continuation_cursor(repo=repo), args.format)
        return 0

    if args.subcommand == "checkpoint":
        _emit(
            write_context_checkpoint(
                repo=repo,
                title=args.title,
                task=args.task,
                current_checkpoint=args.current_checkpoint,
                next_patch_batch=args.next_patch_batch,
                last_observation=args.last_observation,
                current_hypothesis=args.current_hypothesis,
                next_atomic_step=args.next_atomic_step,
                fixed=args.fixed,
                partially_fixed=args.partially_fixed,
                remaining=args.remaining,
                blockers=args.blocker,
                files_recently_read=args.files_recently_read,
                symbols_recently_checked=args.symbols_recently_checked,
                commands_recently_run=args.commands_recently_run,
                recent_actions=args.recent_actions,
                do_not_repeat=args.do_not_repeat,
                verify_next=args.verify_next,
                sources=args.source,
                decisions=args.decision,
                notes=args.note,
            ),
            args.format,
        )
        return 0

    if args.subcommand == "ingest-finding":
        body = _read_body_arg(args.body, args.body_file)
        _emit(
            ingest_finding(
                args.title,
                body,
                task=args.task,
                sources=args.source,
                commands=args.command,
                decisions=args.decision,
                tags=args.tag,
                repo=repo,
                to_second_brain=args.to_second_brain,
                second_brain_root=args.second_brain_root,
                reviewed=args.reviewed,
            ),
            args.format,
        )
        return 0

    if args.subcommand == "serve":
        serve_context_os(repo=repo, db_path=db, host=args.host, port=args.port)
        return 0

    if args.subcommand == "mcp-stdio":
        return serve_stdio(repo=repo, db_path=db)

    if args.subcommand == "brain":
        return _handle_brain_command(args, repo=repo)

    if args.subcommand == "classify":
        classification = classify_path(args.path)
        payload = {
            "path": args.path,
            "authority_tier": classification.authority_tier,
            "evidence_class": classification.evidence_class,
            "freshness": classification.freshness,
            "doc_type": classification.doc_type,
            "route": classification.route,
        }
        _emit(payload, args.format)
        return 0

    if args.subcommand == "stats":
        _emit(catalog_stats(db_path=db, repo=repo), args.format)
        return 0

    if args.subcommand == "freshness":
        _emit(catalog_freshness(db_path=db, repo=repo), args.format)
        return 0

    if args.subcommand == "health":
        _emit(
            context_intelligence_health(
                repo=repo,
                db_path=db,
                second_brain_root=args.second_brain_root,
                session_capsule_limit=args.session_capsule_limit,
            ),
            args.format,
        )
        return 0

    raise AssertionError(args.subcommand)


def _handle_brain_command(args: argparse.Namespace, *, repo: Path) -> int:
    if args.brain_command == "init":
        _emit(init_second_brain(root=args.root, repo=repo), args.format)
        return 0
    if args.brain_command == "capture":
        body = _read_body_arg(args.body, args.body_file)
        path = capture_idea(
            body,
            title=args.title,
            tags=args.tag,
            source=args.source,
            root=args.root,
        )
        _emit({"path": path.as_posix()}, args.format)
        return 0
    if args.brain_command == "distill":
        source = None if args.latest else args.source
        path = distill_idea(source, root=args.root, reviewed=args.reviewed)
        _emit({"path": path.as_posix()}, args.format)
        return 0
    if args.brain_command == "search":
        _emit(
            search_second_brain(
                args.query,
                root=args.root,
                limit=args.limit,
                include_raw=args.include_raw,
            ),
            args.format,
        )
        return 0
    if args.brain_command == "graph":
        _emit(generate_second_brain_graph(root=args.root), args.format)
        return 0
    if args.brain_command == "status":
        _emit(second_brain_status(root=args.root), args.format)
        return 0
    raise AssertionError(args.brain_command)


def _read_body_arg(body: str | None, body_file: str | None) -> str:
    if body_file:
        return Path(body_file).expanduser().read_text(encoding="utf-8")
    if body:
        return body
    raise SystemExit("brain capture requires --body or --body-file")


def _emit(payload: Any, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, list):
        for item in payload:
            if {"score", "authority_tier", "path", "evidence_class"} <= set(item):
                print(
                    f"{item['score']:>4} {item['authority_tier']} {item['path']} "
                    f"({item['evidence_class']})"
                )
            else:
                print(json.dumps(item, sort_keys=True))
        return
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        print(f"{key}: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
