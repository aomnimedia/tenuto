"""Zero-dependency CLI for Tenuto (`tenuto` and `remember` entry points)."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .db import (
    DAILY_CATEGORIES,
    DURABLE_KINDS,
    PROJECT_MEMORY_KINDS,
    PROPOSAL_STATUSES,
    RECORD_STATUSES,
    compute_review,
    connect_ro,
    connect_rw,
    init_agent_home,
    init_project_store,
    load_agent_orientation,
    load_project_resume,
    resolve_agent_home,
    resolve_project_db,
    sha256_text,
    verify_governing_docs,
)
from .templates import COMPASS_CUE

HELP_FLAGS = {"-h", "--help", "-help"}


def _header(label: str) -> None:
    print(label)
    print("-" * len(label))


def _resolve_text(raw: str, file_path: str | None = None) -> str:
    if file_path is not None:
        return Path(file_path).expanduser().read_text(encoding="utf-8").strip()
    if raw == "-":
        return sys.stdin.read().strip()
    return raw


def _require_text(value: str, label: str) -> str:
    if not value or value != value.strip():
        raise ValueError(f"Invalid {label}: must be nonblank without surrounding whitespace.")
    return value


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _main_help(prog: str) -> str:
    return f"""{prog} {__version__} — Tenuto Developmental Agent & Project Continuity

HELP (never touches any database):
  {prog} --help | help [COMMAND]
  {prog} COMMAND --help
  {prog} project --help | project SUBCOMMAND --help

BOOTSTRAP & ORIENTATION (plain text default; pass --json for machine output):
  {prog} init [--agent-only | --project-only] [--agent-home DIR] [--project-db PATH]
  {prog} startup [--project KEY] [--json]
  {prog} fetchstate [--json]
  {prog} review [--json]

AGENT CONTINUITY (private ~/.tenuto/agent.db — primary verb: `remember`):
  {prog} state "status|-" [--active X] [--posture X] [--file PATH]
  {prog} durable-save "key" "title" "content|-" --kind knowledge|behavior|focus|preference [--application X] [--success X] [--status active|retired] [--file PATH]
  {prog} durable-list [--kind X] [--status active|retired|all] [--json]
  {prog} durable-show "key" [--json]
  {prog} durable-retire "key"
  {prog} reference-save "key" "label" "kind" "location" "relevance" [--revision X] [--verified X] [--status active|retired]
  {prog} reference-list [--kind X] [--status active|retired|all] [--json]
  {prog} reference-retire "key"
  {prog} proposal "text|-" [--context X] [--file PATH]       (alias: question)
  {prog} proposals [--status open|exploring|resolved|archived] [--json]   (alias: questions)
  {prog} resolve <id> "resolution|-" [--file PATH]           (alias: answer)
  {prog} daily "title" "body|-" --category X [--tags X] [--supersedes ID] [--file PATH]
  {prog} construction "title" --objective X --evidence X --result X --boundaries X --hold X [--tags X]
  {prog} checkpoint "summary|-" [--next X] [--file PATH]
  {prog} fetch [--tag X] [--category X] [--limit N] [--since YYYY-MM-DD] [--include-superseded]
  {prog} search "term"
  {prog} stats [--json]

PROJECT CONTINUITY (shareable .tenuto/project.db — distinct `project` namespace):
  {prog} project save --project-key KEY --name N --purpose P --scope S --intended-outcomes O
  {prog} project list [--json]
  {prog} project resume --project-key KEY [--json]
  {prog} project state --project-key KEY "content|-" [--file PATH]
  {prog} project checkpoint --project-key KEY --completed C --next N [--context X]
  {prog} project memory --project-key KEY --kind decision|outcome|learning|revelation --title T "body|-" [--supersedes ID] [--file PATH]
  {prog} project ref-save --project-key KEY --reference-key RK --label L --kind K --location LOC --relevance REL [--revision R]
  {prog} project ref-list --project-key KEY [--status active|retired|all] [--json]
  {prog} project ref-retire --project-key KEY --reference-key RK
  {prog} project history --project-key KEY --table state|checkpoint|memory [--kind K] [--include-superseded] [--json]

SHELL-SAFE INPUT:
  Pass '-' for any text body to read safely from stdin (e.g. quoted heredoc <<'EOF'),
  preserving $ amounts and apostrophes without bash escaping issues.
"""


COMMAND_HELP = {
    "init": (
        "Usage: tenuto init [--agent-only | --project-only] [--agent-home DIR] [--project-db PATH]\n"
        "Safely initialize ~/.tenuto/agent.db (plus constitution, contract, and tool integrations)\n"
        "and .tenuto/project.db in the current directory. Never overwrites existing databases.\n"
        "Example: tenuto init"
    ),
    "startup": (
        "Usage: remember startup [--project KEY] [--json]\n"
        "Verify governing docs by SHA-256, echo the 5-Principle Working Constitution, check\n"
        "explicit continuity gaps, and read private agent orientation read-only.\n"
        "If --project KEY is passed, also displays that project's Resume View read-only without\n"
        "storing the project key in shared agent state.\n"
        "Example: remember startup --project myapp"
    ),
    "fetchstate": (
        "Usage: remember fetchstate [--json]\n"
        "Read private agent orientation and explicit gaps without repeating SHA-256 doc headers.\n"
        "Example: remember fetchstate --json"
    ),
    "review": (
        "Usage: remember review [--json]\n"
        "Run a 2-minute separation hygiene check across governing docs, agent Current State,\n"
        "durable memories, references, open proposals, and project DB presence.\n"
        "Example: remember review"
    ),
    "state": (
        'Usage: remember state "status|-" [--active "INQUIRY (ask user)"] [--posture X] [--file PATH]\n'
        "Write a fresh complete Agent Current State and supersede the previous active row.\n"
        "Example: remember state - --active 'INQUIRY (ask user)' <<'EOF'\nReady.\nEOF"
    ),
    "durable-save": (
        'Usage: remember durable-save "key" "title" "content|-" --kind knowledge|behavior|focus|preference '
        "[--application X] [--success X] [--status active|retired] [--file PATH]\n"
        "Create or revise a constructive durable practice by stable key."
    ),
    "durable-list": "Usage: remember durable-list [--kind X] [--status active|retired|all] [--json]",
    "durable-show": 'Usage: remember durable-show "key" [--json]',
    "durable-retire": 'Usage: remember durable-retire "key"',
    "reference-save": (
        'Usage: remember reference-save "key" "label" "kind" "location" "relevance" '
        "[--revision X] [--verified X] [--status active|retired]"
    ),
    "reference-list": "Usage: remember reference-list [--kind X] [--status active|retired|all] [--json]",
    "reference-retire": 'Usage: remember reference-retire "key"',
    "proposal": (
        'Usage: remember proposal "text|-" [--context X] [--file PATH]  (alias: question)\n'
        "Record an agent-to-user improvement proposal, friction note, or open question."
    ),
    "proposals": "Usage: remember proposals [--status open|exploring|resolved|archived] [--json]  (alias: questions)",
    "resolve": 'Usage: remember resolve <id> "resolution|-" [--file PATH]  (alias: answer)',
    "daily": (
        'Usage: remember daily "title" "body|-" --category X [--tags "t1,t2"] [--supersedes ID] [--file PATH]\n'
        f"Categories: {', '.join(DAILY_CATEGORIES)}\n"
        "Use --supersedes ID to link an immutable correction and hide the old record from default reads."
    ),
    "construction": (
        'Usage: remember construction "title" --objective X --evidence X --result X --boundaries X --hold X [--tags X]\n'
        "Record a positively framed completed-construction entry and echo the 1-line constitution compass."
    ),
    "checkpoint": (
        'Usage: remember checkpoint "summary|-" [--next X] [--file PATH]\n'
        "Append an immutable checkpoint (preserves continuity; never grants execution authorization)."
    ),
    "fetch": "Usage: remember fetch [--tag X] [--category X] [--limit N] [--since YYYY-MM-DD] [--include-superseded]",
    "search": 'Usage: remember search "term"',
    "stats": "Usage: remember stats [--json]",
    "project": (
        "Usage: tenuto project SUBCOMMAND [OPTIONS]\n"
        "Subcommands: save, list, resume, state, checkpoint, memory, ref-save, ref-list, ref-retire, history.\n"
        "Run `tenuto project SUBCOMMAND --help` for exact flags and examples."
    ),
}

PROJECT_HELP = {
    "save": (
        "Usage: tenuto project save --project-key KEY --name NAME --purpose P --scope S --intended-outcomes O\n"
        "Create or revise a project's framing in .tenuto/project.db.\n"
        "Example: tenuto project save --project-key app --name 'App' --purpose 'Ship v1' --scope 'Core CLI' --intended-outcomes 'First paying users'"
    ),
    "list": "Usage: tenuto project list [--json]\nList projects stored in .tenuto/project.db.",
    "resume": (
        "Usage: tenuto project resume --project-key KEY [--json]\n"
        "Return the complete Project Resume View (framing, gaps, latest state, checkpoint, memories, references)."
    ),
    "state": (
        'Usage: tenuto project state --project-key KEY "content|-" [--by AGENT] [--file PATH]\n'
        "Append a fresh, complete project Current State evaluation (actor falls back to TENUTO_ACTOR)."
    ),
    "checkpoint": (
        "Usage: tenuto project checkpoint --project-key KEY --completed TEXT --next TEXT [--context TEXT] [--by AGENT]\n"
        "Append a project task boundary checkpoint (actor falls back to TENUTO_ACTOR)."
    ),
    "memory": (
        'Usage: tenuto project memory --project-key KEY --kind decision|outcome|learning|revelation --title TITLE "body|-" [--supersedes ID] [--by AGENT] [--file PATH]\n'
        "Append a consequential project decision, outcome, learning, or revelation."
    ),
    "ref-save": (
        "Usage: tenuto project ref-save --project-key KEY --reference-key RK --label L --kind K --location LOC --relevance REL [--revision R]\n"
        "Create or revise an authoritative project reference."
    ),
    "ref-list": "Usage: tenuto project ref-list --project-key KEY [--status active|retired|all] [--json]",
    "ref-retire": "Usage: tenuto project ref-retire --project-key KEY --reference-key RK",
    "history": (
        "Usage: tenuto project history --project-key KEY --table state|checkpoint|memory [--kind K] [--include-superseded] [--json]\n"
        "Retrieve chronological project state, checkpoint, or memory history."
    ),
}


def _render_project_resume(resume: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(resume, indent=2))
        return

    proj = resume["project"]
    gaps = resume["gaps"]
    _header(f"PROJECT: {proj['name']} ({proj['project_key']})")
    print(f"Purpose:  {proj['purpose']}")
    print(f"Scope:    {proj['scope']}")
    print(f"Outcomes: {proj['intended_outcomes']}")
    print()

    active_gaps = [k for k, v in gaps.items() if v]
    _header("PROJECT GAPS")
    print(", ".join(active_gaps) if active_gaps else "None (Current State and Checkpoint present).")
    print()

    _header("PROJECT CURRENT STATE")
    cs = resume["current_state"]
    if cs:
        who = f" by {cs['actor']}" if cs.get("actor") else ""
        print(f"Updated: {cs['created_at']} (#{cs['id']}{who})")
        print(cs["content"])
    else:
        print("No project Current State recorded.")
    print()

    _header("PROJECT CHECKPOINT")
    cp = resume["checkpoint"]
    if cp:
        who = f" by {cp['actor']}" if cp.get("actor") else ""
        print(f"Updated:   {cp['created_at']} (#{cp['id']}{who})")
        print(f"Completed: {cp['completed']}")
        print(f"Next:      {cp['next_step']}")
        if cp.get("context"):
            print(f"Context:   {cp['context']}")
    else:
        print("No project checkpoint recorded.")
    print()

    _header("PROJECT MEMORIES (LATEST)")
    if resume["latest_memories"]:
        for m in resume["latest_memories"]:
            who = f" · by {m['actor']}" if m.get("actor") else ""
            print(f"#{m['id']} [{m['kind']}] {m['title']} ({m['created_at']}{who})")
            print(f"  {m['body']}")
    else:
        print("No project memories recorded.")
    print()

    _header("PROJECT REFERENCES")
    if resume["references"]:
        for ref in resume["references"]:
            rev = f" (rev {ref['revision']})" if ref.get("revision") else ""
            print(f"{ref['reference_key']} [{ref['kind']}] {ref['label']}{rev}")
            print(f"  Location:  {ref['location']}")
            print(f"  Relevance: {ref['relevance']}")
    else:
        print("No active project references.")


def _render_agent_orientation(
    data: dict[str, Any] | None,
    gaps: dict[str, Any],
    verified: list[dict[str, str]] | None = None,
    missing_docs: list[dict[str, str]] | None = None,
    project_resume: dict[str, Any] | None = None,
    as_json: bool = False,
    include_constitution: bool = False,
) -> None:
    gaps = dict(gaps)
    gaps["missing_governing_docs"] = [d["key"] for d in (missing_docs or [])]

    if as_json:
        payload: dict[str, Any] = {"gaps": gaps}
        if verified is not None:
            payload["verified_docs"] = [
                {"key": d["key"], "path": d["path"], "sha256": d["sha256"]} for d in verified
            ]
        if data is not None:
            payload.update(data)
        if project_resume is not None:
            payload["project_resume"] = project_resume
        print(json.dumps(payload, indent=2))
        return

    if verified is not None:
        for d in verified:
            print(f"VERIFIED {d['path']} sha256={d['sha256']}")
        for d in (missing_docs or []):
            print(f"MISSING  {d['path']}")
        print()

    if include_constitution and verified:
        for d in verified:
            if d["key"] == "constitution":
                _header("WORKING CONSTITUTION")
                print(d["text"])
                print()

    active_gaps = [k for k, v in gaps.items() if v]
    _header("CONTINUITY GAPS")
    if active_gaps:
        for g in active_gaps:
            print(f"  - {g}: {gaps[g]}")
    else:
        print("None (all anchors present; project pointer at INQUIRY).")
    print()

    if data is None:
        print("Agent database not initialized. Run: tenuto init")
        return

    _header("CURRENT STATE")
    cs = data["current_state"]
    if cs:
        print(f"Updated: {cs['created_at']}")
        print(cs["status_text"])
        if cs.get("active_work"):
            print(f"Active work: {cs['active_work']}")
        if cs.get("posture"):
            print(f"Posture: {cs['posture']}")
    else:
        print("No current state set.")
    print()

    _header("DURABLE MEMORY")
    if data["durable_memory"]:
        for item in data["durable_memory"]:
            print(f"{item['memory_key']} [{item['kind']}] {item['title']}")
            print(item["content"])
            if item.get("application_context"):
                print(f"Application: {item['application_context']}")
            if item.get("success_signal"):
                print(f"Success signal: {item['success_signal']}")
            print()
    else:
        print("No active durable memories.")
        print()

    _header("REFERENCES")
    if data["references"]:
        for ref in data["references"]:
            print(f"{ref['reference_key']} [{ref['kind']}] {ref['label']}")
            print(f"Location: {ref['location']}")
            print(f"Relevance: {ref['relevance']}")
            if ref.get("revision"):
                print(f"Revision: {ref['revision']}")
            if ref.get("last_verified_at"):
                print(f"Verified: {ref['last_verified_at']}")
            print()
    else:
        print("No active references.")
        print()

    _header("OPEN COLLABORATION PROPOSALS / QUESTIONS")
    if data["open_proposals"]:
        for p in data["open_proposals"]:
            print(f"#{p['id']} [{p['status']}] {p['proposal']}")
            if p.get("context"):
                print(f"Context: {p['context']}")
            print()
    else:
        print("No open collaboration proposals.")
        print()

    _header("LATEST DAILY MEMORY")
    dm = data["latest_daily_memory"]
    if dm:
        print(f"Updated: {dm['created_at']} (#{dm['id']})")
        print(f"Category: {dm['category']}  Tags: {dm.get('tags') or 'none'}")
        print(f"Title: {dm['title']}")
        print(dm["body"])
    else:
        print("No daily memory entry.")
    print()

    _header("CHECKPOINT")
    cp = data["checkpoint"]
    if cp:
        print(f"Updated: {cp['created_at']} (#{cp['id']})")
        print(f"Summary: {cp['summary']}")
        if cp.get("next_objectives"):
            print(f"Next: {cp['next_objectives']}")
    else:
        print("No checkpoints.")

    if project_resume is not None:
        print()
        _render_project_resume(project_resume, as_json=False)


# ─── COMMAND HANDLERS ─────────────────────────────────────────────────────

def cmd_init(args: list[str]) -> None:
    agent_only = False
    project_only = False
    agent_home_arg = None
    project_db_arg = None
    i = 0
    while i < len(args):
        if args[i] == "--agent-only":
            agent_only = True
            i += 1
        elif args[i] == "--project-only":
            project_only = True
            i += 1
        elif args[i] == "--agent-home" and i + 1 < len(args):
            agent_home_arg = args[i + 1]
            i += 2
        elif args[i] == "--project-db" and i + 1 < len(args):
            project_db_arg = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid init argument: {args[i]}")
    if agent_only and project_only:
        raise ValueError("Cannot pass both --agent-only and --project-only.")

    if not project_only:
        res = init_agent_home(resolve_agent_home(agent_home_arg))
        status = "created" if res["agent_db_created"] else "preserved existing"
        print(f"Agent Continuity ({status}): {res['agent_db']}")
        print(f"  Constitution: {res['constitution']}")
        print(f"  Contract:     {res['contract']}")
        print(f"  Integrations: {res['integrations_dir']}/")
    if not agent_only:
        pres = init_project_store(resolve_project_db(project_db_arg, for_init=True))
        pstatus = "created" if pres["project_db_created"] else "preserved existing"
        print(f"Project Continuity ({pstatus}): {pres['project_db']}")
    print()
    print("Next: run `remember startup` (and drop AGENTS-snippet.md into CLAUDE.md or AGENTS.md).")


def cmd_startup(args: list[str], include_constitution: bool = True) -> None:
    as_json = False
    project_key = None
    i = 0
    while i < len(args):
        if args[i] == "--json":
            as_json = True
            i += 1
        elif args[i] == "--project" and i + 1 < len(args):
            project_key = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid startup argument: {args[i]}")

    agent_home = resolve_agent_home()
    verified, missing = verify_governing_docs(agent_home) if include_constitution else (None, None)
    data, gaps = load_agent_orientation(agent_home)
    proj_resume = None
    if project_key:
        proj_resume = load_project_resume(resolve_project_db(), project_key)
    _render_agent_orientation(
        data,
        gaps,
        verified=verified,
        missing_docs=missing,
        project_resume=proj_resume,
        as_json=as_json,
        include_constitution=include_constitution,
    )


def cmd_review(args: list[str]) -> None:
    pos, f = _parse_flags(args, set(), {"--json"})
    if pos:
        raise ValueError(f"Unexpected review arguments: {' '.join(pos)}")
    as_json = bool(f["--json"])
    agent_home = resolve_agent_home()
    project_db = resolve_project_db()
    report = compute_review(agent_home, project_db)
    if as_json:
        print(json.dumps(report, indent=2))
        return

    c = report["counts"]
    _header("TENUTO HYGIENE REVIEW")
    print(f"Governing docs verified:  {report['verified_docs_count']}/{report['total_docs_count']}")
    print(f"Agent State length:       {c['current_state_chars']} chars")
    print(f"Agent active_work:        {c['active_work'] or 'none'}")
    print(f"Active Durable Memories:  {c['durable_memory']}")
    print(f"Active References:        {c['references']}")
    print(f"Open Proposals/Questions: {c['open_proposals']}")
    print(f"Project DB present:       {'yes' if c['project_db_present'] else 'no'} ({c['projects']} projects)")
    print()
    _header("ADVISORIES")
    if report["advisories"]:
        for adv in report["advisories"]:
            print(f"  - {adv}")
    else:
        print("Clean — separation boundary and continuity anchors look healthy.")


def cmd_state(args: list[str]) -> None:
    if len(args) < 1:
        raise ValueError(COMMAND_HELP["state"])
    raw_text = args[0]
    active_work = None
    posture = None
    file_path = None
    i = 1
    while i < len(args):
        if args[i] == "--active" and i + 1 < len(args):
            active_work = args[i + 1]
            i += 2
        elif args[i] == "--posture" and i + 1 < len(args):
            posture = args[i + 1]
            i += 2
        elif args[i] == "--file" and i + 1 < len(args):
            file_path = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid state argument: {args[i]}")
    text = _require_text(_resolve_text(raw_text, file_path), "status text")
    now = _now_ts()
    conn = connect_rw(resolve_agent_home() / "agent.db")
    try:
        conn.execute("UPDATE current_state SET superseded_at=? WHERE superseded_at IS NULL", (now,))
        cur = conn.execute(
            "INSERT INTO current_state (created_at, status_text, active_work, posture, source_name, content_sha256) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (now, text, active_work, posture, Path(file_path).name if file_path else "cli", sha256_text(text)),
        )
        conn.commit()
        print(f"Agent state #{cur.lastrowid} set at {now} (previous superseded).")
    finally:
        conn.close()


def cmd_durable_save(args: list[str]) -> None:
    if len(args) < 4:
        raise ValueError(COMMAND_HELP["durable-save"])
    key, title, raw_content = args[:3]
    vals: dict[str, Any] = {"kind": None, "application": None, "success": None, "status": "active", "file": None}
    i = 3
    while i < len(args):
        flag = args[i]
        if flag in ("--kind", "--application", "--success", "--status", "--file") and i + 1 < len(args):
            vals[flag[2:]] = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid durable-save argument: {flag}")
    _require_text(key, "memory key")
    _require_text(title, "title")
    content = _require_text(_resolve_text(raw_content, vals["file"]), "content")
    if vals["kind"] not in DURABLE_KINDS:
        raise ValueError(f"Invalid --kind. Choose from: {', '.join(DURABLE_KINDS)}")
    if vals["status"] not in RECORD_STATUSES:
        raise ValueError(f"Invalid --status. Choose from: {', '.join(RECORD_STATUSES)}")

    conn = connect_rw(resolve_agent_home() / "agent.db")
    try:
        created = conn.execute("SELECT 1 FROM durable_memories WHERE memory_key=?", (key,)).fetchone() is None
        conn.execute(
            "INSERT INTO durable_memories (memory_key, title, kind, content, application_context, success_signal, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(memory_key) DO UPDATE SET "
            "title=excluded.title, kind=excluded.kind, content=excluded.content, "
            "application_context=excluded.application_context, success_signal=excluded.success_signal, "
            "status=excluded.status, updated_at=datetime('now')",
            (key, title, vals["kind"], content, vals["application"], vals["success"], vals["status"]),
        )
        conn.commit()
        print(f"Durable memory '{key}' {'created' if created else 'revised'} [{vals['kind']} | {vals['status']}].")
    finally:
        conn.close()


def cmd_durable_list(args: list[str]) -> None:
    kind = None
    status = "active"
    as_json = False
    i = 0
    while i < len(args):
        if args[i] == "--json":
            as_json = True
            i += 1
        elif args[i] == "--kind" and i + 1 < len(args):
            kind = args[i + 1]
            i += 2
        elif args[i] == "--status" and i + 1 < len(args):
            status = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid durable-list argument: {args[i]}")
    conn = connect_ro(resolve_agent_home() / "agent.db")
    try:
        q = "SELECT memory_key, kind, status, updated_at, title FROM durable_memories WHERE 1=1"
        params: list[Any] = []
        if kind:
            q += " AND kind=?"
            params.append(kind)
        if status != "all":
            q += " AND status=?"
            params.append(status)
        q += " ORDER BY kind, memory_key"
        rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    finally:
        conn.close()
    if as_json:
        print(json.dumps(rows, indent=2))
        return
    if not rows:
        print("No durable memories found.")
        return
    for r in rows:
        print(f"{r['memory_key']}  [{r['kind']} | {r['status']}]  {r['title']}  updated:{r['updated_at']}")


def cmd_durable_show(args: list[str]) -> None:
    as_json = "--json" in args
    pos = [a for a in args if a != "--json"]
    if len(pos) != 1:
        raise ValueError(COMMAND_HELP["durable-show"])
    conn = connect_ro(resolve_agent_home() / "agent.db")
    try:
        row = conn.execute("SELECT * FROM durable_memories WHERE memory_key=?", (pos[0],)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise KeyError(f"Durable memory '{pos[0]}' not found.")
    data = dict(row)
    if as_json:
        print(json.dumps(data, indent=2))
        return
    for k, v in data.items():
        print(f"{k}: {v or 'none'}")


def cmd_durable_retire(args: list[str]) -> None:
    if len(args) != 1:
        raise ValueError(COMMAND_HELP["durable-retire"])
    conn = connect_rw(resolve_agent_home() / "agent.db")
    try:
        cur = conn.execute(
            "UPDATE durable_memories SET status='retired', updated_at=datetime('now') "
            "WHERE memory_key=? AND status='active'",
            (args[0],),
        )
        if cur.rowcount != 1:
            raise KeyError(f"Active durable memory '{args[0]}' not found.")
        conn.commit()
        print(f"Durable memory '{args[0]}' retired.")
    finally:
        conn.close()


def cmd_reference_save(args: list[str]) -> None:
    if len(args) < 5:
        raise ValueError(COMMAND_HELP["reference-save"])
    key, label, kind, location, relevance = args[:5]
    for v, lbl in ((key, "reference key"), (label, "label"), (kind, "kind"), (location, "location"), (relevance, "relevance")):
        _require_text(v, lbl)
    vals: dict[str, Any] = {"revision": None, "verified": None, "status": "active"}
    i = 5
    while i < len(args):
        if args[i] in ("--revision", "--verified", "--status") and i + 1 < len(args):
            vals[args[i][2:]] = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid reference-save argument: {args[i]}")
    if vals["status"] not in RECORD_STATUSES:
        raise ValueError(f"Invalid status. Choose from: {', '.join(RECORD_STATUSES)}")
    conn = connect_rw(resolve_agent_home() / "agent.db")
    try:
        created = conn.execute("SELECT 1 FROM continuity_references WHERE reference_key=?", (key,)).fetchone() is None
        conn.execute(
            "INSERT INTO continuity_references (reference_key, label, kind, location, relevance, revision, last_verified_at, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(reference_key) DO UPDATE SET "
            "label=excluded.label, kind=excluded.kind, location=excluded.location, relevance=excluded.relevance, "
            "revision=excluded.revision, last_verified_at=excluded.last_verified_at, status=excluded.status, "
            "updated_at=datetime('now')",
            (key, label, kind, location, relevance, vals["revision"], vals["verified"], vals["status"]),
        )
        conn.commit()
        print(f"Reference '{key}' {'created' if created else 'revised'}.")
    finally:
        conn.close()


def cmd_reference_list(args: list[str]) -> None:
    kind = None
    status = "active"
    as_json = False
    i = 0
    while i < len(args):
        if args[i] == "--json":
            as_json = True
            i += 1
        elif args[i] == "--kind" and i + 1 < len(args):
            kind = args[i + 1]
            i += 2
        elif args[i] == "--status" and i + 1 < len(args):
            status = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid reference-list argument: {args[i]}")
    conn = connect_ro(resolve_agent_home() / "agent.db")
    try:
        q = "SELECT * FROM continuity_references WHERE 1=1"
        params: list[Any] = []
        if kind:
            q += " AND kind=?"
            params.append(kind)
        if status != "all":
            q += " AND status=?"
            params.append(status)
        q += " ORDER BY kind, reference_key"
        rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    finally:
        conn.close()
    if as_json:
        print(json.dumps(rows, indent=2))
        return
    if not rows:
        print("No references found.")
        return
    for r in rows:
        print(f"{r['reference_key']}  [{r['kind']} | {r['status']}]  {r['label']}")
        print(f"  Location:  {r['location']}")
        print(f"  Relevance: {r['relevance']}")


def cmd_reference_retire(args: list[str]) -> None:
    if len(args) != 1:
        raise ValueError(COMMAND_HELP["reference-retire"])
    conn = connect_rw(resolve_agent_home() / "agent.db")
    try:
        cur = conn.execute(
            "UPDATE continuity_references SET status='retired', updated_at=datetime('now') "
            "WHERE reference_key=? AND status='active'",
            (args[0],),
        )
        if cur.rowcount != 1:
            raise KeyError(f"Active reference '{args[0]}' not found.")
        conn.commit()
        print(f"Reference '{args[0]}' retired.")
    finally:
        conn.close()


def cmd_proposal(args: list[str]) -> None:
    if len(args) < 1:
        raise ValueError(COMMAND_HELP["proposal"])
    raw_text = args[0]
    context = None
    file_path = None
    i = 1
    while i < len(args):
        if args[i] == "--context" and i + 1 < len(args):
            context = args[i + 1]
            i += 2
        elif args[i] == "--file" and i + 1 < len(args):
            file_path = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid proposal argument: {args[i]}")
    text = _require_text(_resolve_text(raw_text, file_path), "proposal")
    conn = connect_rw(resolve_agent_home() / "agent.db")
    try:
        cur = conn.execute("INSERT INTO proposals (proposal, context, status) VALUES (?, ?, 'open')", (text, context))
        conn.commit()
        print(f"Collaboration proposal #{cur.lastrowid} added.")
    finally:
        conn.close()


def cmd_proposals(args: list[str]) -> None:
    status = None
    as_json = False
    i = 0
    while i < len(args):
        if args[i] == "--json":
            as_json = True
            i += 1
        elif args[i] == "--status" and i + 1 < len(args):
            status = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid proposals argument: {args[i]}")
    conn = connect_ro(resolve_agent_home() / "agent.db")
    try:
        if status and status != "all":
            rows = [dict(r) for r in conn.execute("SELECT * FROM proposals WHERE status=? ORDER BY id DESC", (status,)).fetchall()]
        else:
            rows = [dict(r) for r in conn.execute("SELECT * FROM proposals ORDER BY id DESC").fetchall()]
    finally:
        conn.close()
    if as_json:
        print(json.dumps(rows, indent=2))
        return
    if not rows:
        print("No collaboration proposals found.")
        return
    for r in rows:
        print(f"#{r['id']} [{r['status']}] {r['proposal']}")
        if r.get("context"):
            print(f"  Context:    {r['context']}")
        if r.get("resolution"):
            print(f"  Resolution: {r['resolution']}")


def cmd_resolve(args: list[str]) -> None:
    if len(args) < 2:
        raise ValueError(COMMAND_HELP["resolve"])
    pid = int(args[0])
    raw_res = args[1]
    file_path = None
    i = 2
    while i < len(args):
        if args[i] == "--file" and i + 1 < len(args):
            file_path = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid resolve argument: {args[i]}")
    resolution = _require_text(_resolve_text(raw_res, file_path), "resolution")
    conn = connect_rw(resolve_agent_home() / "agent.db")
    try:
        cur = conn.execute(
            "UPDATE proposals SET status='resolved', resolved_at=?, resolution=? WHERE id=?",
            (_now_ts(), resolution, pid),
        )
        if cur.rowcount != 1:
            raise KeyError(f"Proposal #{pid} not found.")
        conn.commit()
        print(f"Collaboration proposal #{pid} resolved.")
    finally:
        conn.close()


def cmd_daily(args: list[str]) -> None:
    if len(args) < 2:
        raise ValueError(COMMAND_HELP["daily"])
    title, raw_body = args[:2]
    category = "general"
    tags = None
    supersedes_id = None
    file_path = None
    i = 2
    while i < len(args):
        if args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == "--tags" and i + 1 < len(args):
            tags = args[i + 1]
            i += 2
        elif args[i] == "--supersedes" and i + 1 < len(args):
            supersedes_id = int(args[i + 1])
            i += 2
        elif args[i] == "--file" and i + 1 < len(args):
            file_path = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid daily argument: {args[i]}")
    _require_text(title, "title")
    body = _require_text(_resolve_text(raw_body, file_path), "body")
    if category not in DAILY_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Choose from: {', '.join(DAILY_CATEGORIES)}")

    conn = connect_rw(resolve_agent_home() / "agent.db")
    try:
        if supersedes_id is not None:
            prior = conn.execute("SELECT id, superseded_by_id FROM daily_memory WHERE id=?", (supersedes_id,)).fetchone()
            if prior is None:
                raise KeyError(f"Daily memory #{supersedes_id} not found.")
            if prior["superseded_by_id"] is not None:
                raise ValueError(f"Daily memory #{supersedes_id} is already superseded by #{prior['superseded_by_id']}.")
        now = _now_ts()
        cur = conn.execute(
            "INSERT INTO daily_memory (created_at, entry_date, category, title, body, tags, content_sha256) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (now, date.today().isoformat(), category, title, body, tags, sha256_text(f"{title}\n{body}")),
        )
        new_id = cur.lastrowid
        if supersedes_id is not None:
            conn.execute("UPDATE daily_memory SET superseded_by_id=? WHERE id=?", (new_id, supersedes_id))
        conn.commit()
        suffix = f" (supersedes #{supersedes_id})" if supersedes_id is not None else ""
        print(f"Daily memory #{new_id} added: [{category}] {title}{suffix}")
    finally:
        conn.close()


def cmd_construction(args: list[str]) -> None:
    if not args:
        raise ValueError(COMMAND_HELP["construction"])
    title = args[0]
    fields = ("objective", "evidence", "result", "boundaries", "hold")
    values: dict[str, str] = {}
    tags = ["continuity", "construction"]
    i = 1
    while i < len(args):
        if args[i] == "--tags" and i + 1 < len(args):
            for t in args[i + 1].split(","):
                t = t.strip()
                if t and t not in tags:
                    tags.append(t)
            i += 2
        elif args[i].startswith("--") and i + 1 < len(args):
            values[args[i][2:]] = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid construction argument: {args[i]}")
    missing = [f for f in fields if not values.get(f)]
    if missing:
        raise ValueError(f"Missing construction fields: {', '.join(missing)}")
    body = "\n\n".join(f"**{f.title()}:** {values[f]}" for f in fields)
    cmd_daily([title, body, "--category", "work_status_change", "--tags", ",".join(tags)])
    print(COMPASS_CUE)


def cmd_checkpoint(args: list[str]) -> None:
    if len(args) < 1:
        raise ValueError(COMMAND_HELP["checkpoint"])
    raw_summary = args[0]
    next_obj = None
    file_path = None
    i = 1
    while i < len(args):
        if args[i] == "--next" and i + 1 < len(args):
            next_obj = args[i + 1]
            i += 2
        elif args[i] == "--file" and i + 1 < len(args):
            file_path = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid checkpoint argument: {args[i]}")
    summary = _require_text(_resolve_text(raw_summary, file_path), "summary")
    now = _now_ts()
    conn = connect_rw(resolve_agent_home() / "agent.db")
    try:
        cur = conn.execute(
            "INSERT INTO checkpoints (created_at, summary, next_objectives, content_sha256) VALUES (?, ?, ?, ?)",
            (now, summary, next_obj, sha256_text(f"{summary}\n{next_obj or ''}")),
        )
        conn.commit()
        print(f"Checkpoint #{cur.lastrowid} added at {now}.")
        print(COMPASS_CUE)
    finally:
        conn.close()


def cmd_fetch(args: list[str]) -> None:
    tag = None
    category = None
    limit = 50
    since = None
    include_sup = False
    i = 0
    while i < len(args):
        if args[i] == "--include-superseded":
            include_sup = True
            i += 1
        elif args[i] == "--tag" and i + 1 < len(args):
            tag = args[i + 1]
            i += 2
        elif args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        elif args[i] == "--since" and i + 1 < len(args):
            since = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Invalid fetch argument: {args[i]}")
    conn = connect_ro(resolve_agent_home() / "agent.db")
    try:
        q = "SELECT * FROM daily_memory WHERE 1=1"
        params: list[Any] = []
        if not include_sup:
            q += " AND superseded_by_id IS NULL"
        if tag:
            q += " AND tags LIKE ?"
            params.append(f"%{tag}%")
        if category:
            q += " AND category=?"
            params.append(category)
        if since:
            q += " AND entry_date >= ?"
            params.append(since)
        q += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
    finally:
        conn.close()
    if not rows:
        print("No entries found.")
        return
    for r in rows:
        sup = f" [SUPERSEDED BY #{r['superseded_by_id']}]" if r["superseded_by_id"] else ""
        print(f"#{r['id']} [{r['entry_date']} | {r['category']}] {r['title']}{sup}")
        print(f"  {r['body']}")


def cmd_search(args: list[str]) -> None:
    if len(args) != 1:
        raise ValueError(COMMAND_HELP["search"])
    term = f"%{args[0]}%"
    conn = connect_ro(resolve_agent_home() / "agent.db")
    try:
        dur = conn.execute(
            "SELECT memory_key, kind, title FROM durable_memories "
            "WHERE memory_key LIKE ? OR title LIKE ? OR content LIKE ?",
            (term, term, term),
        ).fetchall()
        refs = conn.execute(
            "SELECT reference_key, kind, label, location FROM continuity_references "
            "WHERE reference_key LIKE ? OR label LIKE ? OR location LIKE ? OR relevance LIKE ?",
            (term, term, term, term),
        ).fetchall()
        dm = conn.execute(
            "SELECT id, category, title FROM daily_memory "
            "WHERE superseded_by_id IS NULL AND (title LIKE ? OR body LIKE ? OR tags LIKE ?)",
            (term, term, term),
        ).fetchall()
        props = conn.execute(
            "SELECT id, status, proposal FROM proposals WHERE proposal LIKE ? OR context LIKE ?",
            (term, term),
        ).fetchall()
    finally:
        conn.close()
    found = False
    if dur:
        print("=== Durable Memory ===")
        for r in dur:
            print(f"  {r['memory_key']} [{r['kind']}] {r['title']}")
        found = True
    if refs:
        print("=== References ===")
        for r in refs:
            print(f"  {r['reference_key']} [{r['kind']}] {r['label']}: {r['location']}")
        found = True
    if dm:
        print("=== Daily Memory ===")
        for r in dm:
            print(f"  #{r['id']} [{r['category']}] {r['title']}")
        found = True
    if props:
        print("=== Collaboration Proposals ===")
        for r in props:
            print(f"  #{r['id']} [{r['status']}] {r['proposal']}")
        found = True
    if not found:
        print("Nothing found.")


def cmd_stats(args: list[str]) -> None:
    pos, f = _parse_flags(args, set(), {"--json"})
    if pos:
        raise ValueError(f"Unexpected stats arguments: {' '.join(pos)}")
    as_json = bool(f["--json"])
    conn = connect_ro(resolve_agent_home() / "agent.db")
    try:
        stats = {
            "durable_active": conn.execute("SELECT COUNT(*) FROM durable_memories WHERE status='active'").fetchone()[0],
            "durable_total": conn.execute("SELECT COUNT(*) FROM durable_memories").fetchone()[0],
            "references_active": conn.execute("SELECT COUNT(*) FROM continuity_references WHERE status='active'").fetchone()[0],
            "proposals_open": conn.execute("SELECT COUNT(*) FROM proposals WHERE status IN ('open','exploring')").fetchone()[0],
            "proposals_resolved": conn.execute("SELECT COUNT(*) FROM proposals WHERE status='resolved'").fetchone()[0],
            "current_state_entries": conn.execute("SELECT COUNT(*) FROM current_state").fetchone()[0],
            "checkpoints": conn.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0],
            "daily_active": conn.execute("SELECT COUNT(*) FROM daily_memory WHERE superseded_by_id IS NULL").fetchone()[0],
            "daily_superseded": conn.execute("SELECT COUNT(*) FROM daily_memory WHERE superseded_by_id IS NOT NULL").fetchone()[0],
        }
    finally:
        conn.close()
    if as_json:
        print(json.dumps(stats, indent=2))
        return
    print("Tenuto Agent Continuity — Stats")
    for k, v in stats.items():
        print(f"  {k}: {v}")


# ─── PROJECT CONTINUITY SUBCOMMANDS (.tenuto/project.db) ──────────────────

def _resolve_actor(explicit: str | None) -> str | None:
    raw = explicit if explicit is not None else os.environ.get("TENUTO_ACTOR")
    if raw is None:
        return None
    cleaned = raw.strip()
    return cleaned or None


def _ensure_project_exists(conn: sqlite3.Connection, project_key: str) -> None:
    if conn.execute("SELECT 1 FROM projects WHERE project_key=?", (project_key,)).fetchone() is None:
        raise KeyError(
            f"Project '{project_key}' not found. Run `tenuto project save --project-key {project_key} ...` first."
        )


def _parse_flags(args: list[str], value_flags: set[str], bool_flags: set[str] | None = None) -> tuple[list[str], dict[str, Any]]:
    bool_flags = bool_flags or set()
    pos: list[str] = []
    parsed: dict[str, Any] = {f: False for f in bool_flags}
    i = 0
    while i < len(args):
        a = args[i]
        if a in bool_flags:
            parsed[a] = True
            i += 1
        elif a in value_flags and i + 1 < len(args):
            parsed[a] = args[i + 1]
            i += 2
        elif a.startswith("--"):
            raise ValueError(f"Unknown or incomplete flag: {a}")
        else:
            pos.append(a)
            i += 1
    return pos, parsed


def cmd_project(args: list[str]) -> None:
    if not args or args[0] in HELP_FLAGS:
        print(COMMAND_HELP["project"])
        return
    sub = args[0]
    sub_args = args[1:]
    if sub == "help":
        if not sub_args:
            print(COMMAND_HELP["project"])
        elif sub_args[0] in PROJECT_HELP:
            print(PROJECT_HELP[sub_args[0]])
        else:
            raise ValueError(f"Unknown project subcommand: {sub_args[0]}")
        return
    if sub not in PROJECT_HELP:
        raise ValueError(f"Unknown project subcommand: {sub}. Run `tenuto project --help`.")
    if any(a in HELP_FLAGS for a in sub_args):
        print(PROJECT_HELP[sub])
        return

    project_db = resolve_project_db()

    if sub == "save":
        _, f = _parse_flags(sub_args, {"--project-key", "--name", "--purpose", "--scope", "--intended-outcomes"})
        for req in ("--project-key", "--name", "--purpose", "--scope", "--intended-outcomes"):
            if not f.get(req):
                raise ValueError(f"Missing {req}. Run `tenuto project save --help`.")
            _require_text(f[req], req)
        conn = connect_rw(project_db)
        try:
            created = conn.execute("SELECT 1 FROM projects WHERE project_key=?", (f["--project-key"],)).fetchone() is None
            conn.execute(
                "INSERT INTO projects (project_key, name, purpose, scope, intended_outcomes) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(project_key) DO UPDATE SET "
                "name=excluded.name, purpose=excluded.purpose, scope=excluded.scope, "
                "intended_outcomes=excluded.intended_outcomes, updated_at=datetime('now')",
                (f["--project-key"], f["--name"], f["--purpose"], f["--scope"], f["--intended-outcomes"]),
            )
            conn.commit()
            print(f"Project '{f['--project-key']}' {'created' if created else 'revised'}.")
        finally:
            conn.close()

    elif sub == "list":
        _, f = _parse_flags(sub_args, set(), {"--json"})
        conn = connect_ro(project_db)
        try:
            rows = [dict(r) for r in conn.execute("SELECT project_key, name, updated_at FROM projects ORDER BY project_key").fetchall()]
        finally:
            conn.close()
        if f["--json"]:
            print(json.dumps(rows, indent=2))
            return
        if not rows:
            print("No projects recorded.")
            return
        for r in rows:
            print(f"{r['project_key']}  —  {r['name']}  (updated: {r['updated_at']})")

    elif sub == "resume":
        _, f = _parse_flags(sub_args, {"--project-key"}, {"--json"})
        if not f.get("--project-key"):
            raise ValueError("Missing --project-key. Run `tenuto project resume --help`.")
        resume = load_project_resume(project_db, f["--project-key"])
        _render_project_resume(resume, as_json=bool(f["--json"]))

    elif sub == "state":
        pos, f = _parse_flags(sub_args, {"--project-key", "--file", "--by"})
        if not f.get("--project-key") or (not pos and not f.get("--file")):
            raise ValueError(PROJECT_HELP["state"])
        content = _require_text(_resolve_text(pos[0] if pos else "-", f.get("--file")), "content")
        actor = _resolve_actor(f.get("--by"))
        conn = connect_rw(project_db)
        try:
            _ensure_project_exists(conn, f["--project-key"])
            now = _now_ts()
            cur = conn.execute(
                "INSERT INTO project_states (project_key, created_at, actor, content, content_sha256) VALUES (?, ?, ?, ?, ?)",
                (f["--project-key"], now, actor, content, sha256_text(content)),
            )
            conn.commit()
            who = f" by {actor}" if actor else ""
            print(f"Project '{f['--project-key']}' state #{cur.lastrowid} appended at {now}{who}.")
        finally:
            conn.close()

    elif sub == "checkpoint":
        _, f = _parse_flags(sub_args, {"--project-key", "--completed", "--next", "--context", "--by"})
        for req in ("--project-key", "--completed", "--next"):
            if not f.get(req):
                raise ValueError(f"Missing {req}. Run `tenuto project checkpoint --help`.")
            _require_text(f[req], req)
        actor = _resolve_actor(f.get("--by"))
        conn = connect_rw(project_db)
        try:
            _ensure_project_exists(conn, f["--project-key"])
            now = _now_ts()
            cur = conn.execute(
                "INSERT INTO project_checkpoints (project_key, created_at, actor, completed, next_step, context) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (f["--project-key"], now, actor, f["--completed"], f["--next"], f.get("--context")),
            )
            conn.commit()
            who = f" by {actor}" if actor else ""
            print(f"Project '{f['--project-key']}' checkpoint #{cur.lastrowid} appended at {now}{who}.")
            print(COMPASS_CUE)
        finally:
            conn.close()

    elif sub == "memory":
        pos, f = _parse_flags(sub_args, {"--project-key", "--kind", "--title", "--supersedes", "--file", "--by"})
        for req in ("--project-key", "--kind", "--title"):
            if not f.get(req):
                raise ValueError(f"Missing {req}. Run `tenuto project memory --help`.")
        if f["--kind"] not in PROJECT_MEMORY_KINDS:
            raise ValueError(f"Invalid --kind. Choose from: {', '.join(PROJECT_MEMORY_KINDS)}")
        if not pos and not f.get("--file"):
            raise ValueError("Missing memory body (or pass '-' for stdin / --file PATH).")
        body = _require_text(_resolve_text(pos[0] if pos else "-", f.get("--file")), "body")
        actor = _resolve_actor(f.get("--by"))
        sup_id = int(f["--supersedes"]) if f.get("--supersedes") else None
        conn = connect_rw(project_db)
        try:
            _ensure_project_exists(conn, f["--project-key"])
            if sup_id is not None:
                prior = conn.execute(
                    "SELECT id, superseded_by_id FROM project_memories WHERE id=? AND project_key=?",
                    (sup_id, f["--project-key"]),
                ).fetchone()
                if prior is None:
                    raise KeyError(f"Project memory #{sup_id} not found for '{f['--project-key']}'.")
                if prior["superseded_by_id"] is not None:
                    raise ValueError(f"Project memory #{sup_id} is already superseded by #{prior['superseded_by_id']}.")
            now = _now_ts()
            cur = conn.execute(
                "INSERT INTO project_memories (project_key, created_at, actor, kind, title, body) VALUES (?, ?, ?, ?, ?, ?)",
                (f["--project-key"], now, actor, f["--kind"], f["--title"], body),
            )
            new_id = cur.lastrowid
            if sup_id is not None:
                conn.execute("UPDATE project_memories SET superseded_by_id=? WHERE id=?", (new_id, sup_id))
            conn.commit()
            suffix = f" (supersedes #{sup_id})" if sup_id is not None else ""
            who = f" by {actor}" if actor else ""
            print(f"Project '{f['--project-key']}' memory #{new_id} added: [{f['--kind']}] {f['--title']}{who}{suffix}")
        finally:
            conn.close()

    elif sub == "ref-save":
        _, f = _parse_flags(sub_args, {"--project-key", "--reference-key", "--label", "--kind", "--location", "--relevance", "--revision"})
        for req in ("--project-key", "--reference-key", "--label", "--kind", "--location", "--relevance"):
            if not f.get(req):
                raise ValueError(f"Missing {req}. Run `tenuto project ref-save --help`.")
            _require_text(f[req], req)
        conn = connect_rw(project_db)
        try:
            _ensure_project_exists(conn, f["--project-key"])
            created = conn.execute(
                "SELECT 1 FROM project_references WHERE project_key=? AND reference_key=?",
                (f["--project-key"], f["--reference-key"]),
            ).fetchone() is None
            conn.execute(
                "INSERT INTO project_references (project_key, reference_key, label, kind, location, relevance, revision, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'active') "
                "ON CONFLICT(project_key, reference_key) DO UPDATE SET "
                "label=excluded.label, kind=excluded.kind, location=excluded.location, relevance=excluded.relevance, "
                "revision=excluded.revision, status='active', updated_at=datetime('now')",
                (f["--project-key"], f["--reference-key"], f["--label"], f["--kind"], f["--location"], f["--relevance"], f.get("--revision")),
            )
            conn.commit()
            print(f"Project reference '{f['--reference-key']}' {'created' if created else 'revised'}.")
        finally:
            conn.close()

    elif sub == "ref-list":
        _, f = _parse_flags(sub_args, {"--project-key", "--status"}, {"--json"})
        if not f.get("--project-key"):
            raise ValueError("Missing --project-key.")
        status = f.get("--status") or "active"
        conn = connect_ro(project_db)
        try:
            _ensure_project_exists(conn, f["--project-key"])
            q = "SELECT * FROM project_references WHERE project_key=?"
            params: list[Any] = [f["--project-key"]]
            if status != "all":
                q += " AND status=?"
                params.append(status)
            q += " ORDER BY kind, reference_key"
            rows = [dict(r) for r in conn.execute(q, params).fetchall()]
        finally:
            conn.close()
        if f["--json"]:
            print(json.dumps(rows, indent=2))
            return
        if not rows:
            print("No project references found.")
            return
        for r in rows:
            print(f"{r['reference_key']} [{r['kind']} | {r['status']}] {r['label']} -> {r['location']}")

    elif sub == "ref-retire":
        _, f = _parse_flags(sub_args, {"--project-key", "--reference-key"})
        if not f.get("--project-key") or not f.get("--reference-key"):
            raise ValueError("Missing --project-key or --reference-key.")
        conn = connect_rw(project_db)
        try:
            _ensure_project_exists(conn, f["--project-key"])
            cur = conn.execute(
                "UPDATE project_references SET status='retired', updated_at=datetime('now') "
                "WHERE project_key=? AND reference_key=? AND status='active'",
                (f["--project-key"], f["--reference-key"]),
            )
            if cur.rowcount != 1:
                raise KeyError(f"Active project reference '{f['--reference-key']}' not found.")
            conn.commit()
            print(f"Project reference '{f['--reference-key']}' retired.")
        finally:
            conn.close()

    elif sub == "history":
        _, f = _parse_flags(sub_args, {"--project-key", "--table", "--kind"}, {"--include-superseded", "--json"})
        if not f.get("--project-key") or f.get("--table") not in ("state", "checkpoint", "memory"):
            raise ValueError(PROJECT_HELP["history"])
        conn = connect_ro(project_db)
        try:
            _ensure_project_exists(conn, f["--project-key"])
            if f["--table"] == "state":
                rows = [dict(r) for r in conn.execute("SELECT * FROM project_states WHERE project_key=? ORDER BY id DESC", (f["--project-key"],)).fetchall()]
            elif f["--table"] == "checkpoint":
                rows = [dict(r) for r in conn.execute("SELECT * FROM project_checkpoints WHERE project_key=? ORDER BY id DESC", (f["--project-key"],)).fetchall()]
            else:
                q = "SELECT * FROM project_memories WHERE project_key=?"
                params = [f["--project-key"]]
                if not f["--include-superseded"]:
                    q += " AND superseded_by_id IS NULL"
                if f.get("--kind"):
                    q += " AND kind=?"
                    params.append(f["--kind"])
                q += " ORDER BY id DESC"
                rows = [dict(r) for r in conn.execute(q, params).fetchall()]
        finally:
            conn.close()
        if f["--json"]:
            print(json.dumps(rows, indent=2))
            return
        if not rows:
            print("No history records found.")
            return
        for r in rows:
            who = f" · by {r['actor']}" if r.get("actor") else ""
            if f["--table"] == "state":
                print(f"#{r['id']} ({r['created_at']}{who})\n  {r['content']}")
            elif f["--table"] == "checkpoint":
                print(f"#{r['id']} ({r['created_at']}{who}) Completed: {r['completed']} | Next: {r['next_step']}")
                if r.get("context"):
                    print(f"  Context: {r['context']}")
            else:
                sup = f" [SUPERSEDED BY #{r['superseded_by_id']}]" if r.get("superseded_by_id") else ""
                print(f"#{r['id']} [{r['kind']}] {r['title']} ({r['created_at']}{who}){sup}\n  {r['body']}")


def _dispatch(argv: list[str], prog: str) -> int:
    if not argv or argv[0] in HELP_FLAGS:
        print(_main_help(prog))
        return 0
    if argv[0] == "--version":
        print(f"{prog} {__version__}")
        return 0
    if argv[0] == "help":
        if len(argv) == 1:
            print(_main_help(prog))
            return 0
        target = argv[1]
        if target in COMMAND_HELP:
            print(COMMAND_HELP[target])
            return 0
        print(f"Unknown command: {target}", file=sys.stderr)
        return 1

    cmd = argv[0]
    rest = argv[1:]

    aliases = {
        "question": "proposal",
        "questions": "proposals",
        "answer": "resolve",
    }
    canonical = aliases.get(cmd, cmd)

    if canonical != "project" and any(a in HELP_FLAGS for a in rest):
        if canonical in COMMAND_HELP:
            print(COMMAND_HELP[canonical])
            return 0

    handlers = {
        "init": cmd_init,
        "startup": lambda a: cmd_startup(a, include_constitution=True),
        "fetchstate": lambda a: cmd_startup(a, include_constitution=False),
        "review": cmd_review,
        "state": cmd_state,
        "durable-save": cmd_durable_save,
        "durable-list": cmd_durable_list,
        "durable-show": cmd_durable_show,
        "durable-retire": cmd_durable_retire,
        "reference-save": cmd_reference_save,
        "reference-list": cmd_reference_list,
        "reference-retire": cmd_reference_retire,
        "proposal": cmd_proposal,
        "proposals": cmd_proposals,
        "resolve": cmd_resolve,
        "daily": cmd_daily,
        "construction": cmd_construction,
        "checkpoint": cmd_checkpoint,
        "fetch": cmd_fetch,
        "search": cmd_search,
        "stats": cmd_stats,
        "project": cmd_project,
    }
    if canonical not in handlers:
        print(f"Unknown command: {cmd}. Run `{prog} --help`.", file=sys.stderr)
        return 1

    try:
        handlers[canonical](rest)
        return 0
    except (ValueError, KeyError, FileNotFoundError, sqlite3.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main_tenuto() -> None:
    sys.exit(_dispatch(sys.argv[1:], "tenuto"))


def main_remember() -> None:
    sys.exit(_dispatch(sys.argv[1:], "remember"))
