"""The resident F5 Judge — one daemon, batched model calls per changed slate.

Cycle (default 120 s), single-instance via a heartbeat lock file:

  1. composer.build_slate — tail streams by byte cursor, fold state, archive
     the sha-pinned slate.
  2. Skip the model when the judge-relevant fingerprint (candidate set +
     open-position set) is UNCHANGED since the last judged slate, when there is
     nothing to judge, or when the hard daily call cap (default 40) is reached.
  3. Prompt = JUDGE-CHARTER.md + JUDGE-MEMORY.md tail (last 100 lines) +
     JUDGE-SCOREBOARD.md tail (if present) + the slate JSON. Fed via stdin.
  4. grok inbox (judgment/inbox/verdict.json) if a fresh bound verdict is
     waiting; otherwise ask System One (model jev-1.13.0, POST
     https://api.typesafe.ai/v1/systemone). Each POST carries the candidates
     in that batch, not the whole slate, and stays inside the accepted body.
     An empty answer writes no verdict.
  5. shim.apply_verdict — validated writes only. A malformed reply writes
     NOTHING and increments the breach counter (seam fail-open). A dark cycle
     is a logged+counted event, never an exception. This process does not
     send an order.

The daemon never raises out of a cycle; a cycle error is one log line + one
counter bump. It never touches a broker, never imports the tick path, and its
own death changes nothing on the book (judgment_flow's no-row answer is PASS).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

_REPO_FOR_IMPORT = Path(__file__).resolve().parents[2]
if str(_REPO_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_REPO_FOR_IMPORT))

from scripts.f5_desk import adapter, common, composer, shim

_log = logging.getLogger("f5_desk.daemon")

DEFAULT_CYCLE_S = 120
DEFAULT_MAX_CALLS_PER_DAY = 40
LOCK_STALE_S = 600.0
MEMORY_TAIL_LINES = 100
SCOREBOARD_TAIL_LINES = 60

def _returned_score(block: Any) -> Optional[float]:
    """The score the model returned. An empty block stays empty."""
    try:
        from src.judgment.jev_questions import returned_number

        number = returned_number(block)
        if isinstance(number, (int, float)) and not isinstance(number, bool) and number == number:
            return float(number)
    except Exception:
        pass
    if not isinstance(block, dict):
        return None
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    try:
        if raw is None or isinstance(raw, bool):
            return None
        number = float(raw)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


INBOX_NAME = "verdict.json"
INBOX_MAX_AGE_S = 900  # 15 min = 3x the 5-min --once cycle
INBOX_PROVIDER = "grok-inbox"

_FALLBACK_CHARTER = (
    "You are the F5 judgment desk. Job: CONTEXT, not direction. Never predict "
    "direction; never re-litigate the sleeve's read. hold requires a named "
    "mechanism (microstructure | correlation | event_proximity | weekend_carry); "
    "abstain when you have no mechanism. Manage authority: close / tighten_stop "
    "only, each with a mechanism. Output ONLY one JSON object with schema "
    '"gtos.f5.judge.verdict.v1" and keys slate_id, verdicts[], manage[], notes.'
)


class JudgeDaemon:
    def __init__(self, cfg: composer.ComposerConfig,
                 providers: Optional[list[dict]] = None,
                 max_calls_per_day: int = DEFAULT_MAX_CALLS_PER_DAY,
                 call_timeout_s: float = adapter.DEFAULT_TIMEOUT_S):
        self.cfg = cfg
        self.providers = providers
        self.max_calls_per_day = int(max_calls_per_day)
        self.call_timeout_s = float(call_timeout_s)
        self.state_dir = Path(cfg.state_dir)
        self.flow_dir = Path(cfg.flow_dir)
        self.internal = self.state_dir / "state"
        self.logs_dir = self.state_dir / "logs"
        self.lock_path = self.internal / "judge_daemon.lock"
        self.call_counter_path = self.internal / "call_counter.json"
        self.last_judged_path = self.internal / "last_judged.json"
        self.cycle_counter_path = self.internal / "cycle_counters.json"
        self.charter_path = Path(__file__).resolve().parent / "JUDGE-CHARTER.md"
        self.scoreboard_path = self.state_dir / "JUDGE-SCOREBOARD.md"
        self.inbox_path = self.state_dir / "inbox" / INBOX_NAME

    # ---------------- lock (heartbeat mtime, cross-platform) ----------------
    def acquire_lock(self, now: Optional[float] = None) -> bool:
        """True if this process owns the lock. A lock whose mtime is fresher
        than LOCK_STALE_S belongs to a live instance -> False. A stale lock is
        stolen (crashed daemon left it behind)."""
        try:
            now_ts = now if now is not None else time.time()
            if self.lock_path.is_file():
                age = now_ts - self.lock_path.stat().st_mtime
                if age < LOCK_STALE_S:
                    _log.info("daemon: lock held (age %.0fs < %.0fs) — another instance is live",
                              age, LOCK_STALE_S)
                    return False
                _log.warning("daemon: stealing stale lock (age %.0fs)", age)
            common.write_json_atomic(self.lock_path, {
                "pid": os.getpid(), "started_at_utc": common.iso_utc(),
            })
            return True
        except Exception as exc:
            _log.warning("daemon: lock acquire failed (%r) — refusing to run", exc)
            return False

    def heartbeat_lock(self) -> None:
        try:
            os.utime(self.lock_path, None)
        except Exception:
            common.write_json_atomic(self.lock_path, {
                "pid": os.getpid(), "hb_at_utc": common.iso_utc(),
            })

    def release_lock(self) -> None:
        try:
            self.lock_path.unlink(missing_ok=True)
        except Exception:
            pass

    # ---------------- prompt ----------------
    def build_prompt(self, slate: dict) -> str:
        try:
            charter = self.charter_path.read_text(encoding="utf-8")
        except Exception:
            charter = _FALLBACK_CHARTER
            _log.warning("daemon: charter missing at %s — using embedded fallback",
                         self.charter_path)
        memory_lines = common.tail_lines(shim.memory_path(self.state_dir), MEMORY_TAIL_LINES)
        scoreboard_lines = common.tail_lines(self.scoreboard_path, SCOREBOARD_TAIL_LINES)
        parts = [charter.strip()]
        if memory_lines:
            parts.append("## YOUR MEMORY (most recent last)\n" + "\n".join(memory_lines))
        if scoreboard_lines:
            parts.append("## YOUR SCOREBOARD\n" + "\n".join(scoreboard_lines))
        parts.append(
            "## THE SLATE (judge this; respond with ONE gtos.f5.judge.verdict.v1 "
            f"JSON object, slate_id=\"{slate.get('slate_id')}\")\n"
            + json.dumps(slate, sort_keys=True, indent=1, default=str)
        )
        return "\n\n".join(parts)

    # ---------------- counters ----------------
    def _bump(self, key: str) -> None:
        common.bump_day_counter(self.cycle_counter_path, day=common.utc_day(), key=key)

    def calls_today(self, now: Optional[datetime] = None) -> int:
        return common.read_day_counter(self.call_counter_path, day=common.utc_day(now))

    # ---------------- grok file inbox ----------------
    def _load_archived_slate(self, slate_id: str) -> Optional[dict]:
        """Newest archived slate matching ``slate_id``, or None. Never raises."""
        try:
            if not slate_id:
                return None
            slates = self.state_dir / "slates"
            hits = sorted(slates.glob(f"slate_*_{slate_id}.json")) if slates.is_dir() else []
            if not hits:
                return None
            doc = common.read_json(hits[-1], default=None)
            return doc if isinstance(doc, dict) else None
        except Exception:
            return None

    def _archive_inbox(self, src: Path, kind: str, reason: str,
                       now: datetime) -> None:
        """Move the inbox file to inbox/<kind>/ so a write is one-shot."""
        try:
            dest_dir = self.state_dir / "inbox" / kind
            dest_dir.mkdir(parents=True, exist_ok=True)
            stamp = now.strftime("%Y%m%dT%H%M%SZ")
            safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(reason))[:40]
            dest = dest_dir / f"{stamp}_{safe}.json"
            src.replace(dest)
        except Exception:
            try:
                src.unlink(missing_ok=True)
            except Exception:
                pass

    def take_inbox(self, slate: dict, now: datetime) -> tuple[Optional[dict], str]:
        """Bind a waiting Grok verdict to this cycle's slate.

        Returns ``(bound_verdict, reason)``. ``reason`` is the bind mode
        (``slate_id`` / ``fingerprint``) or why the file was not used.
        Missing file is a no-op. Stale / mismatch / bad schema are archived
        to ``inbox/rejected/`` (fail-open). Success leaves the file in place
        so the caller can archive to ``inbox/applied/`` after shim write.
        Never raises.
        """
        path = self.inbox_path
        try:
            if not path.is_file():
                return None, "missing"
            raw = common.read_json(path, default=None)
            if not isinstance(raw, dict):
                self._archive_inbox(path, "rejected", "not_a_mapping", now)
                return None, "not_a_mapping"
            if raw.get("schema") != shim.VERDICT_SCHEMA:
                self._archive_inbox(path, "rejected", "schema_mismatch", now)
                return None, "schema_mismatch"
            written = common.parse_utc(raw.get("written_at_utc"))
            if written is None:
                try:
                    written = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                except Exception:
                    written = None
            if written is None:
                self._archive_inbox(path, "rejected", "stale", now)
                return None, "stale"
            age = (now - written).total_seconds()
            if age > INBOX_MAX_AGE_S or age < -60:
                self._archive_inbox(path, "rejected", "stale", now)
                return None, "stale"
            bound = dict(raw)
            if str(bound.get("slate_id") or "") == str(slate.get("slate_id") or ""):
                return bound, "slate_id"
            fp = bound.get("fingerprint")
            if not fp:
                archived = self._load_archived_slate(str(bound.get("slate_id") or ""))
                fp = (archived or {}).get("fingerprint")
            if fp and fp == slate.get("fingerprint"):
                bound["slate_id"] = slate.get("slate_id")
                return bound, "fingerprint"
            self._archive_inbox(path, "rejected", "slate_mismatch", now)
            return None, "slate_mismatch"
        except Exception as exc:
            _log.warning("daemon: take_inbox failed (%r) — fail-open", exc)
            return None, "inbox_error"

    # ---------------- System One ----------------
    def _prior_verdicts(self) -> list[dict[str, Any]]:
        """Prior shim verdicts. An empty journal stays empty."""
        rows: list[dict[str, Any]] = []
        try:
            folder = shim.journal_path(self.state_dir, common.utc_day()).parent
        except Exception:
            return rows
        if not folder.is_dir():
            return rows
        for path in sorted(folder.glob("judge_*.jsonl")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for line in text.splitlines():
                if "slate_judged" not in line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict) or row.get("kind") != "slate_judged":
                    continue
                verdicts = row.get("verdicts") if isinstance(row.get("verdicts"), list) else []
                manage = row.get("manage") if isinstance(row.get("manage"), list) else []
                if not verdicts and not manage:
                    continue
                rows.append({
                    "slate_id": row.get("slate_id"),
                    "at_utc": row.get("at_utc"),
                    "verdicts": verdicts,
                    "manage": manage,
                })
        return rows

    def _systemone_questions(self, slate: dict) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        import hashlib

        questions: dict[str, Any] = {}
        index: dict[str, dict[str, Any]] = {}

        def qid(prefix: str, raw: str) -> str:
            return prefix + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

        for cand in slate.get("candidates") or []:
            if not isinstance(cand, dict):
                continue
            cid = str(cand.get("candidate_id") or "").strip()
            if not cid:
                continue
            vid = qid("v_", cid)
            mid = qid("h_", cid)
            questions[vid] = {
                "type": "choice",
                "instructions": (
                    "Judge this candidate. Context, not direction. "
                    "The option you return is the verdict. "
                    "hold counts only when the paired question names one mechanism. "
                    "A floor and a baseline are not a bound. Do not send an order. "
                    f"candidate_id={cid}"
                ),
                "criteria": {
                    "approve": "Let this candidate proceed.",
                    "hold": "Hold. The paired question names the mechanism.",
                    "abstain": "No mechanism. Abstain.",
                },
            }
            questions[mid] = {
                "type": "choice",
                "instructions": (
                    "If the verdict is hold, name the mechanism. "
                    "A floor and a baseline are not a bound. Do not send an order. "
                    f"candidate_id={cid}"
                ),
                "criteria": {
                    "microstructure": "Hold for microstructure.",
                    "correlation": "Hold for correlation.",
                    "event_proximity": "Hold for event proximity.",
                    "weekend_carry": "Hold for weekend carry.",
                },
            }
            index[vid] = {"kind": "verdict", "candidate_id": cid, "mechanism_id": mid}
        for pos in slate.get("open_positions") or []:
            if not isinstance(pos, dict):
                continue
            try:
                ticket = int(pos.get("ticket"))
            except (TypeError, ValueError):
                continue
            aid = qid("a_", str(ticket))
            sid = qid("s_", str(ticket))
            questions[aid] = {
                "type": "choice",
                "instructions": (
                    "Manage this open ticket. close, tighten_stop, or leave. "
                    "tighten_stop uses only the score on the paired question. "
                    "An empty score does not move the stop. "
                    "A floor and a baseline are not a bound. Do not send an order. "
                    f"ticket={ticket}"
                ),
                "criteria": {
                    "leave": "Do not manage this ticket.",
                    "close": "Close this ticket.",
                    "tighten_stop": "Tighten the stop to the paired score.",
                },
            }
            levels: list[str] = []
            for key in ("stop_now", "entry_price", "entry", "tp", "take_profit"):
                raw = pos.get(key)
                try:
                    if raw is None or isinstance(raw, bool):
                        continue
                    number = float(raw)
                except (TypeError, ValueError):
                    continue
                if number == number:
                    levels.append(str(raw))
            if levels:
                questions[sid] = {
                    "type": "score",
                    "instructions": (
                        "If tighten_stop wins, the score you return is the new stop price. "
                        "An empty score does not move the stop. "
                        "A floor and a baseline are not a bound. Do not send an order. "
                        f"ticket={ticket}"
                    ),
                    "criteria": levels,
                }
            index[aid] = {"kind": "manage", "ticket": ticket, "score_id": sid}
        return questions, index

    _POST_BUDGET = 42000
    _SLIM_CANDIDATE = (
        "candidate_id",
        "symbol",
        "sleeve",
        "direction",
        "status",
        "stop_dist",
        "last_refusal_class",
        "cluster",
        "decision_day",
    )

    def _slim_candidate(self, cand: dict) -> dict:
        return {
            key: cand.get(key)
            for key in self._SLIM_CANDIDATE
            if cand.get(key) not in (None, "")
        }

    def _post_bytes(self, state: dict, questions: dict) -> int:
        return len(json.dumps(
            {"model": "jev-1.13.0", "state": state, "questions": questions},
            default=str,
        ).encode("utf-8"))

    def _batch_state(self, slate: dict, owners: list) -> dict:
        wanted = {owner for owner in owners}
        candidates = []
        for cand in slate.get("candidates") or []:
            if not isinstance(cand, dict):
                continue
            cid = str(cand.get("candidate_id") or "").strip()
            if cid and cid in wanted:
                candidates.append(self._slim_candidate(cand))
        positions = []
        for pos in slate.get("open_positions") or []:
            if not isinstance(pos, dict):
                continue
            try:
                ticket = int(pos.get("ticket"))
            except (TypeError, ValueError):
                continue
            if ticket not in wanted:
                continue
            kept = {"ticket": ticket}
            for key in ("symbol", "side", "volume", "price_open", "sl", "tp"):
                if pos.get(key) not in (None, ""):
                    kept[key] = pos.get(key)
            positions.append(kept)
        return {
            "slate_id": slate.get("slate_id"),
            "fingerprint": slate.get("fingerprint"),
            "candidates": candidates,
            "open_positions": positions,
        }

    def _question_batches(self, slate: dict, questions: dict, index: dict) -> list[tuple[list, list]]:
        """Groups that stay inside the body the API accepted. A pair stays together."""
        seen: set[str] = set()
        units: list[tuple[Any, list[str]]] = []
        for qid, meta in index.items():
            if qid in seen or not isinstance(meta, dict):
                continue
            ids = [qid]
            seen.add(qid)
            for extra in (meta.get("mechanism_id"), meta.get("score_id")):
                if extra and extra in questions and extra not in seen:
                    ids.append(extra)
                    seen.add(extra)
            owner = meta.get("candidate_id") or meta.get("ticket")
            units.append((owner, ids))
        batches: list[tuple[list, list]] = []
        cur_owners: list = []
        cur_ids: list[str] = []
        for owner, ids in units:
            trial_ids = cur_ids + ids
            trial_owners = cur_owners + [owner]
            trial_q = {key: questions[key] for key in trial_ids}
            if cur_ids and self._post_bytes(self._batch_state(slate, trial_owners), trial_q) > self._POST_BUDGET:
                batches.append((cur_owners, cur_ids))
                cur_owners = [owner]
                cur_ids = list(ids)
            else:
                cur_owners = trial_owners
                cur_ids = trial_ids
        if cur_ids:
            batches.append((cur_owners, cur_ids))
        return batches

    def _verdict_from_answers(
        self,
        slate: dict,
        answers: dict,
        index: dict[str, dict[str, Any]],
    ) -> Optional[dict]:
        from src.judgment.rung_choice import highest, probabilities

        verdict_criteria = {
            "approve": "Let this candidate proceed.",
            "hold": "Hold. The paired question names the mechanism.",
            "abstain": "No mechanism. Abstain.",
        }
        mechanism_criteria = {
            "microstructure": "Hold for microstructure.",
            "correlation": "Hold for correlation.",
            "event_proximity": "Hold for event proximity.",
            "weekend_carry": "Hold for weekend carry.",
        }
        manage_criteria = {
            "leave": "Do not manage this ticket.",
            "close": "Close this ticket.",
            "tighten_stop": "Tighten the stop to the paired score.",
        }
        verdicts: list[dict[str, Any]] = []
        manage: list[dict[str, Any]] = []
        packed = answers if isinstance(answers, dict) else {}
        for qid, meta in index.items():
            if meta.get("kind") == "verdict":
                probs, _source = probabilities(packed.get(qid), verdict_criteria)
                choice = highest(probs)
                if choice not in verdict_criteria or choice not in probs:
                    continue
                mechanism = ""
                if choice == "hold":
                    mprobs, _msource = probabilities(packed.get(meta.get("mechanism_id")), mechanism_criteria)
                    mechanism = highest(mprobs) or ""
                    if mechanism not in mechanism_criteria:
                        continue
                verdicts.append({
                    "candidate_id": meta["candidate_id"],
                    "verdict": choice,
                    "mechanism": mechanism,
                    "why_code": mechanism or choice,
                    "confidence": float(probs[choice]),
                })
            elif meta.get("kind") == "manage":
                probs, _source = probabilities(packed.get(qid), manage_criteria)
                choice = highest(probs)
                if choice not in ("close", "tighten_stop"):
                    continue
                row: dict[str, Any] = {"ticket": meta["ticket"], "action": choice}
                if choice == "tighten_stop":
                    price = _returned_score(packed.get(meta.get("score_id")))
                    if price is None:
                        continue
                    row["new_stop"] = price
                manage.append(row)
        if not verdicts and not manage:
            return None
        return {
            "schema": shim.VERDICT_SCHEMA,
            "slate_id": slate.get("slate_id"),
            "verdicts": verdicts,
            "manage": manage,
        }

    def _post_systemone(self, state: dict, questions: dict) -> dict[str, Any]:
        import urllib.error
        import urllib.request

        from src.judgment.jev_client import API_URL, resolve_key

        key, _source = resolve_key()
        if not key:
            return {"ok": False, "skipped": "key_unreadable", "answers": {}, "http_status": None}
        payload = {"model": "jev-1.13.0", "state": state, "questions": questions}
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(payload, default=str).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "gtos-judgment/0.1",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.call_timeout_s) as resp:
                parsed = json.loads(resp.read().decode("utf-8"))
                status = getattr(resp, "status", 200)
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:180]
            except Exception:
                detail = ""
            error = f"http_{exc.code}"
            if detail:
                error = f"{error}:{detail}"
            return {
                "ok": False,
                "skipped": None,
                "error": error,
                "http_status": exc.code,
                "answers": {},
            }
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", None)
            return {
                "ok": False,
                "skipped": None,
                "error": f"URLError:{reason}"[:300],
                "http_status": None,
                "answers": {},
            }
        except Exception as exc:  # noqa: BLE001 — a dark cycle must not raise
            return {
                "ok": False,
                "skipped": None,
                "error": type(exc).__name__,
                "http_status": None,
                "answers": {},
            }
        got = parsed.get("answers") if isinstance(parsed, dict) else None
        return {
            "ok": True,
            "skipped": None,
            "http_status": status,
            "answers": got if isinstance(got, dict) else {},
            "model": (parsed.get("model") if isinstance(parsed, dict) else None) or "jev-1.13.0",
        }

    def _ask_systemone(self, slate: dict) -> tuple[Optional[dict], dict]:
        questions, index = self._systemone_questions(slate)
        meta: dict[str, Any] = {"provider": "jev-1.13.0", "attempts": []}
        if not questions:
            return None, meta
        answers: dict[str, Any] = {}
        attempts: list[dict[str, Any]] = []
        started = time.monotonic()
        for owners, ids in self._question_batches(slate, questions, index):
            batch_q = {key: questions[key] for key in ids}
            receipt = self._post_systemone(self._batch_state(slate, owners), batch_q)
            attempt: dict[str, Any] = {
                "provider": "jev-1.13.0",
                "ok": bool(receipt.get("ok")),
                "http_status": receipt.get("http_status"),
                "n_questions": len(ids),
            }
            if receipt.get("ok"):
                got = receipt.get("answers")
                if isinstance(got, dict):
                    answers.update(got)
            else:
                attempt["ok"] = False
                attempt["fail_reason"] = receipt.get("error") or "post_failed"
            attempts.append(attempt)
        meta["attempts"] = attempts
        meta["latency_ms"] = int((time.monotonic() - started) * 1000)
        if not answers:
            return None, meta
        verdict = self._verdict_from_answers(slate, answers, index)
        if verdict is None:
            if attempts:
                attempts[-1]["fail_reason"] = attempts[-1].get("fail_reason") or "empty_answer"
                attempts[-1]["ok"] = False
            return None, meta
        return verdict, meta

    # ---------------- one cycle ----------------
    def run_cycle(self, now: Optional[datetime] = None,
                  call_fn: Optional[Callable[..., tuple[Optional[dict], dict]]] = None) -> dict:
        """One full cycle. Returns a summary dict; NEVER raises."""
        summary: dict[str, Any] = {"at_utc": common.iso_utc(now), "outcome": "error"}
        try:
            now_dt = now or common.now_utc()
            slate, slate_path = composer.build_slate(self.cfg, now_utc=now_dt)
            summary.update({
                "slate_id": slate.get("slate_id"),
                "fingerprint": slate.get("fingerprint"),
                "candidates": len(slate.get("candidates") or []),
                "open_positions": len(slate.get("open_positions") or []),
                "slate_path": str(slate_path) if slate_path else None,
            })
            if not slate.get("candidates") and not slate.get("open_positions"):
                summary["outcome"] = "skipped_no_material"
                self._bump("skipped_no_material")
                return summary
            inbox_verdict, inbox_reason = self.take_inbox(slate, now_dt)
            summary["inbox"] = inbox_reason
            if inbox_verdict is not None:
                applied = shim.apply_verdict(
                    inbox_verdict, slate,
                    state_dir=self.state_dir, flow_dir=self.flow_dir,
                    provider=INBOX_PROVIDER, latency_ms=0,
                    raw_text_sha=common.sha256_hex(
                        common.canonical_json(inbox_verdict)
                    )[:16],
                    now=now_dt,
                )
                summary["provider"] = INBOX_PROVIDER
                summary["applied"] = applied.get("applied")
                summary["drops"] = applied.get("drops")
                if applied.get("applied"):
                    self._archive_inbox(self.inbox_path, "applied", "ok", now_dt)
                    common.write_json_atomic(self.last_judged_path, {
                        "fingerprint": slate.get("fingerprint"),
                        "slate_id": slate.get("slate_id"),
                        "judged_at_utc": common.iso_utc(now_dt),
                    })
                    summary["outcome"] = "judged"
                    self._bump("judged")
                else:
                    self._archive_inbox(
                        self.inbox_path, "rejected",
                        str(applied.get("reject_reason") or "shim")[:40], now_dt,
                    )
                    summary["outcome"] = f"rejected_{applied.get('reject_reason')}"
                    self._bump("verdict_rejected")
                return summary
            last = common.read_json(self.last_judged_path, default={}) or {}
            if isinstance(last, dict) and last.get("fingerprint") == slate.get("fingerprint"):
                summary["outcome"] = "skipped_unchanged"
                self._bump("skipped_unchanged")
                return summary
            calls = self.calls_today(now_dt)
            if calls >= self.max_calls_per_day:
                summary["outcome"] = "skipped_call_cap"
                summary["calls_today"] = calls
                self._bump("skipped_call_cap")
                _log.warning("daemon: daily call cap reached (%d/%d) — judging paused until UTC midnight",
                             calls, self.max_calls_per_day)
                return summary
            # The counter bumps only after a provider was actually tried.
            if call_fn is None:
                verdict_raw, meta = self._ask_systemone(slate)
            else:
                prompt = self.build_prompt(slate)
                verdict_raw, meta = call_fn(
                    prompt,
                    providers=self.providers,
                    timeout_s=self.call_timeout_s,
                    log_path=self.logs_dir / "adapter_calls.jsonl",
                )
            summary["provider"] = meta.get("provider")
            summary["attempts"] = len(meta.get("attempts") or [])
            if summary["attempts"]:
                common.bump_day_counter(self.call_counter_path, day=common.utc_day(now_dt))
            if verdict_raw is None:
                reason = "all_providers_dark"
                attempts = meta.get("attempts") or []
                named = ""
                if attempts and isinstance(attempts[-1], dict):
                    named = str(attempts[-1].get("fail_reason") or "")
                if named in ("schema_mismatch", "no_json_object"):
                    reason = "verdict_unparseable"
                elif named:
                    reason = named
                breaches = shim.record_breach(self.state_dir, reason, now_dt)
                shim.append_journal(self.state_dir, {
                    "kind": "cycle_no_verdict",
                    "at_utc": common.iso_utc(now_dt),
                    "slate_id": slate.get("slate_id"),
                    "reason": reason,
                    "attempts": meta.get("attempts"),
                    "breach_count_today": breaches,
                }, now_dt)
                summary["outcome"] = reason
                self._bump(reason)
                return summary
            latency = None
            stdout_sha = None
            for attempt in meta.get("attempts") or []:
                if attempt.get("ok"):
                    latency = attempt.get("latency_ms")
                    stdout_sha = attempt.get("stdout_sha16")
            applied = shim.apply_verdict(
                verdict_raw, slate,
                state_dir=self.state_dir, flow_dir=self.flow_dir,
                provider=meta.get("provider"), latency_ms=latency,
                raw_text_sha=stdout_sha or common.sha256_hex(common.canonical_json(verdict_raw))[:16],
                now=now_dt,
            )
            summary["applied"] = applied.get("applied")
            summary["drops"] = applied.get("drops")
            if applied.get("applied"):
                common.write_json_atomic(self.last_judged_path, {
                    "fingerprint": slate.get("fingerprint"),
                    "slate_id": slate.get("slate_id"),
                    "judged_at_utc": common.iso_utc(now_dt),
                })
                summary["outcome"] = "judged"
                self._bump("judged")
            else:
                summary["outcome"] = f"rejected_{applied.get('reject_reason')}"
                self._bump("verdict_rejected")
            return summary
        except Exception as exc:
            _log.warning("daemon: cycle failed (%r) — carrying on", exc)
            summary["outcome"] = f"cycle_error_{type(exc).__name__}"
            try:
                self._bump("cycle_error")
            except Exception:
                pass
            return summary

    # ---------------- main loop ----------------
    def run_forever(self, cycle_s: float = DEFAULT_CYCLE_S,
                    max_cycles: Optional[int] = None) -> int:
        if not self.acquire_lock():
            return 0  # another live instance — exit quietly (watchdog-safe)
        _log.info("daemon: F5 judge up (repo=%s ns=%s cycle=%ss cap=%d/day)",
                  self.cfg.repo_root, self.cfg.namespace, cycle_s, self.max_calls_per_day)
        cycles = 0
        try:
            while True:
                started = time.monotonic()
                summary = self.run_cycle()
                _log.info("daemon: cycle %s slate=%s cand=%s open=%s",
                          summary.get("outcome"), summary.get("slate_id"),
                          summary.get("candidates"), summary.get("open_positions"))
                self.heartbeat_lock()
                cycles += 1
                if max_cycles is not None and cycles >= max_cycles:
                    return 0
                elapsed = time.monotonic() - started
                time.sleep(max(1.0, float(cycle_s) - elapsed))
        except KeyboardInterrupt:
            _log.info("daemon: interrupted — exiting cleanly")
            return 0
        finally:
            self.release_lock()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Resident F5 judgment daemon.")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--namespace", default=common.NAMESPACE)
    parser.add_argument("--cycle-seconds", type=float, default=DEFAULT_CYCLE_S)
    parser.add_argument("--max-calls-per-day", type=int, default=DEFAULT_MAX_CALLS_PER_DAY)
    parser.add_argument("--once", action="store_true", help="run exactly one cycle and exit")
    parser.add_argument("--smoke", action="store_true",
                        help="provider connectivity smoke (adapter --smoke) and exit")
    args = parser.parse_args(argv)

    cfg = composer.ComposerConfig(
        repo_root=Path(args.repo_root) if args.repo_root else common.repo_root_default(),
        namespace=args.namespace,
    )
    daemon = JudgeDaemon(cfg, max_calls_per_day=args.max_calls_per_day)
    common.setup_logging(daemon.logs_dir / "judge_daemon.log")
    if args.smoke:
        results = adapter.smoke()
        return 0 if any(r["ok"] for r in results) else 1
    if args.once:
        summary = daemon.run_cycle()
        print(json.dumps(summary, indent=1, sort_keys=True, default=str))
        return 0
    return daemon.run_forever(cycle_s=args.cycle_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
