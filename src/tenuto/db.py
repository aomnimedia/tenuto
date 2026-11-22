"""Two-file SQLite storage layer for Tenuto (Agent Continuity + Project Continuity)."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .templates import (
    INTEGRATION_AGENTS_SNIPPET,
    INTEGRATION_CLAUDE_HOOKS_JSON,
    LAUNCHER_CLAUDE_SH,
    LAUNCHER_CODEX_SH,
    STARTER_CONSTITUTION,
    STARTER_CONTRACT,
)

DURABLE_KINDS = ("knowledge", "behavior", "focus", "preference")
RECORD_STATUSES = ("active", "retired")
PROPOSAL_STATUSES = ("open", "exploring", "resolved", "archived")
DAILY_CATEGORIES = (
    "significant_decision",
    "client_recognition",
    "permission_change",
    "work_status_change",
    "trust_event",
    "significant_learning",
    "focus",
    "design_control",
    "session_end",
    "heartbeat",
    "general",
)
PROJECT_MEMORY_KINDS = ("decision", "outcome", "learning", "revelation")

AGENT_SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE current_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    status_text TEXT NOT NULL,
    active_work TEXT,
    posture TEXT,
    superseded_at TEXT,
    source_name TEXT NOT NULL DEFAULT 'cli',
    content_sha256 TEXT NOT NULL,
    CHECK (length(trim(status_text)) > 0)
);
CREATE INDEX idx_agent_state_active ON current_state(superseded_at, created_at);

CREATE TABLE durable_memories (
    memory_key TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('knowledge', 'behavior', 'focus', 'preference')),
    content TEXT NOT NULL,
    application_context TEXT,
    success_signal TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'retired')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (memory_key <> '' AND memory_key = trim(memory_key)),
    CHECK (length(trim(title)) > 0 AND length(trim(content)) > 0)
);
CREATE INDEX idx_agent_durable_status ON durable_memories(kind, status);

CREATE TABLE continuity_references (
    reference_key TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    kind TEXT NOT NULL,
    location TEXT NOT NULL,
    relevance TEXT NOT NULL,
    revision TEXT,
    last_verified_at TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'retired')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (reference_key <> '' AND reference_key = trim(reference_key)),
    CHECK (length(trim(label)) > 0 AND length(trim(kind)) > 0 AND length(trim(location)) > 0 AND length(trim(relevance)) > 0)
);
CREATE INDEX idx_agent_ref_status ON continuity_references(kind, status);

CREATE TABLE proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    proposal TEXT NOT NULL,
    context TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'exploring', 'resolved', 'archived')),
    resolved_at TEXT,
    resolution TEXT,
    CHECK (length(trim(proposal)) > 0)
);
CREATE INDEX idx_agent_proposals_status ON proposals(status);

CREATE TABLE daily_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    entry_date TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    tags TEXT,
    content_sha256 TEXT NOT NULL,
    superseded_by_id INTEGER REFERENCES daily_memory(id),
    CHECK (length(trim(title)) > 0 AND length(trim(body)) > 0)
);
CREATE INDEX idx_agent_daily_active ON daily_memory(superseded_by_id, created_at);
CREATE INDEX idx_agent_daily_category ON daily_memory(category);

CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    summary TEXT NOT NULL,
    next_objectives TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    content_sha256 TEXT NOT NULL,
    CHECK (length(trim(summary)) > 0)
);
CREATE INDEX idx_agent_checkpoints_created ON checkpoints(created_at);
"""

PROJECT_SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE projects (
    project_key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    purpose TEXT NOT NULL,
    scope TEXT NOT NULL,
    intended_outcomes TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (project_key <> '' AND project_key = trim(project_key)),
    CHECK (length(trim(name)) > 0 AND length(trim(purpose)) > 0 AND length(trim(scope)) > 0 AND length(trim(intended_outcomes)) > 0)
);

CREATE TABLE project_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT NOT NULL REFERENCES projects(project_key),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    actor TEXT,
    content TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    CHECK (length(trim(content)) > 0)
);
CREATE INDEX idx_project_states_key ON project_states(project_key, id);

CREATE TABLE project_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT NOT NULL REFERENCES projects(project_key),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    actor TEXT,
    completed TEXT NOT NULL,
    next_step TEXT NOT NULL,
    context TEXT,
    CHECK (length(trim(completed)) > 0 AND length(trim(next_step)) > 0)
);
CREATE INDEX idx_project_checkpoints_key ON project_checkpoints(project_key, id);

CREATE TABLE project_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT NOT NULL REFERENCES projects(project_key),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    actor TEXT,
    kind TEXT NOT NULL CHECK (kind IN ('decision', 'outcome', 'learning', 'revelation')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    superseded_by_id INTEGER REFERENCES project_memories(id),
    CHECK (length(trim(title)) > 0 AND length(trim(body)) > 0)
);
CREATE INDEX idx_project_memories_key ON project_memories(project_key, kind, superseded_by_id, id);

CREATE TABLE project_references (
    project_key TEXT NOT NULL REFERENCES projects(project_key),
    reference_key TEXT NOT NULL,
    label TEXT NOT NULL,
    kind TEXT NOT NULL,
    location TEXT NOT NULL,
    relevance TEXT NOT NULL,
    revision TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'retired')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (project_key, reference_key),
    CHECK (reference_key <> '' AND reference_key = trim(reference_key)),
    CHECK (length(trim(label)) > 0 AND length(trim(kind)) > 0 AND length(trim(location)) > 0 AND length(trim(relevance)) > 0)
);
"""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_agent_home(override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    env_home = os.environ.get("TENUTO_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()
    return (Path.home() / ".tenuto").resolve()


def resolve_project_db(override: str | None = None, for_init: bool = False) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    env_db = os.environ.get("TENUTO_PROJECT_DB")
    if env_db:
        return Path(env_db).expanduser().resolve()
    cwd = Path.cwd().resolve()
    if for_init:
        return cwd / ".tenuto" / "project.db"
    for parent in (cwd, *cwd.parents):
        candidate = parent / ".tenuto" / "project.db"
        if candidate.is_file():
            return candidate
    return cwd / ".tenuto" / "project.db"


def connect_rw(db_path: Path) -> sqlite3.Connection:
    if not db_path.is_file():
        raise FileNotFoundError(f"Database not initialized: {db_path} (run `tenuto init`)")
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def connect_ro(db_path: Path) -> sqlite3.Connection:
    if not db_path.is_file():
        raise FileNotFoundError(f"Database not initialized: {db_path} (run `tenuto init`)")
    encoded = quote(db_path.as_posix(), safe="/:")
    uri = f"file:{encoded}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_agent_home(agent_home: Path) -> dict[str, Any]:
    agent_home.mkdir(parents=True, exist_ok=True)
    db_path = agent_home / "agent.db"
    db_created = False
    if not db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.executescript(AGENT_SCHEMA_SQL)
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        conn.commit()
        conn.close()
        db_created = True

    const_path = agent_home / "WORKING-CONSTITUTION.md"
    contract_path = agent_home / "CONTINUITY-CONTRACT.md"
    if not const_path.exists():
        const_path.write_text(STARTER_CONSTITUTION, encoding="utf-8")
    if not contract_path.exists():
        contract_path.write_text(STARTER_CONTRACT, encoding="utf-8")

    integrations_dir = agent_home / "integrations"
    integrations_dir.mkdir(parents=True, exist_ok=True)
    templates = {
        "codex-launcher.sh": (LAUNCHER_CODEX_SH, True),
        "claude-launcher.sh": (
            LAUNCHER_CLAUDE_SH.replace("__CONSTITUTION_PATH__", str(const_path)),
            True,
        ),
        "claude-hooks.json": (INTEGRATION_CLAUDE_HOOKS_JSON, False),
        "AGENTS-snippet.md": (INTEGRATION_AGENTS_SNIPPET, False),
    }
    written_integrations = []
    for name, (body, executable) in templates.items():
        target = integrations_dir / name
        if not target.exists():
            target.write_text(body, encoding="utf-8")
            if executable:
                os.chmod(target, 0o755)
            written_integrations.append(name)

    return {
        "agent_home": str(agent_home),
        "agent_db": str(db_path),
        "agent_db_created": db_created,
        "constitution": str(const_path),
        "contract": str(contract_path),
        "integrations_dir": str(integrations_dir),
        "integrations_written": written_integrations,
    }


def init_project_store(project_db: Path) -> dict[str, Any]:
    project_db.parent.mkdir(parents=True, exist_ok=True)
    created = False
    if not project_db.exists():
        conn = sqlite3.connect(str(project_db))
        conn.executescript(PROJECT_SCHEMA_SQL)
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        conn.commit()
        conn.close()
        created = True
    return {
        "project_db": str(project_db),
        "project_db_created": created,
    }


def verify_governing_docs(agent_home: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    verified: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    for key, filename in (
        ("constitution", "WORKING-CONSTITUTION.md"),
        ("contract", "CONTINUITY-CONTRACT.md"),
    ):
        path = agent_home / filename
        if path.is_file():
            raw = path.read_bytes()
            verified.append(
                {
                    "key": key,
                    "path": str(path),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "text": raw.decode("utf-8").strip(),
                }
            )
        else:
            missing.append({"key": key, "path": str(path)})
    return verified, missing


def load_agent_orientation(agent_home: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    db_path = agent_home / "agent.db"
    if not db_path.is_file():
        return None, {
            "missing_database": True,
            "missing_current_state": True,
            "missing_checkpoint": True,
            "missing_durable_memory": True,
            "project_pointer_not_inquiry": False,
        }

    conn = connect_ro(db_path)
    try:
        cs_row = conn.execute(
            "SELECT id, created_at, status_text, active_work, posture "
            "FROM current_state WHERE superseded_at IS NULL "
            "ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
        durable_rows = conn.execute(
            "SELECT memory_key, kind, title, content, application_context, success_signal, updated_at "
            "FROM durable_memories WHERE status='active' ORDER BY kind, memory_key"
        ).fetchall()
        ref_rows = conn.execute(
            "SELECT reference_key, kind, label, location, relevance, revision, last_verified_at "
            "FROM continuity_references WHERE status='active' ORDER BY kind, reference_key"
        ).fetchall()
        prop_rows = conn.execute(
            "SELECT id, created_at, proposal, context, status "
            "FROM proposals WHERE status IN ('open', 'exploring') ORDER BY id"
        ).fetchall()
        daily_row = conn.execute(
            "SELECT id, created_at, entry_date, category, title, body, tags "
            "FROM daily_memory WHERE superseded_by_id IS NULL "
            "ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
        cp_row = conn.execute(
            "SELECT id, created_at, summary, next_objectives, status "
            "FROM checkpoints ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    current_state = dict(cs_row) if cs_row else None
    durable = [dict(r) for r in durable_rows]
    references = [dict(r) for r in ref_rows]
    proposals = [dict(r) for r in prop_rows]
    latest_daily = dict(daily_row) if daily_row else None
    checkpoint = dict(cp_row) if cp_row else None

    gaps = {
        "missing_database": False,
        "missing_current_state": current_state is None,
        "missing_checkpoint": checkpoint is None,
        "missing_durable_memory": len(durable) == 0,
        "project_pointer_not_inquiry": bool(
            current_state
            and current_state.get("active_work")
            and "INQUIRY" not in str(current_state["active_work"]).upper()
        ),
    }

    return (
        {
            "current_state": current_state,
            "durable_memory": durable,
            "references": references,
            "open_proposals": proposals,
            "latest_daily_memory": latest_daily,
            "checkpoint": checkpoint,
        },
        gaps,
    )


def load_project_resume(project_db: Path, project_key: str) -> dict[str, Any]:
    conn = connect_ro(project_db)
    try:
        proj = conn.execute(
            "SELECT project_key, name, purpose, scope, intended_outcomes, created_at, updated_at "
            "FROM projects WHERE project_key=?",
            (project_key,),
        ).fetchone()
        if proj is None:
            raise KeyError(f"Project '{project_key}' not found in {project_db}")

        state = conn.execute(
            "SELECT id, created_at, actor, content FROM project_states "
            "WHERE project_key=? ORDER BY id DESC LIMIT 1",
            (project_key,),
        ).fetchone()
        cp = conn.execute(
            "SELECT id, created_at, actor, completed, next_step, context FROM project_checkpoints "
            "WHERE project_key=? ORDER BY id DESC LIMIT 1",
            (project_key,),
        ).fetchone()
        memories = conn.execute(
            "SELECT id, created_at, actor, kind, title, body FROM project_memories "
            "WHERE project_key=? AND superseded_by_id IS NULL ORDER BY id DESC LIMIT 10",
            (project_key,),
        ).fetchall()
        refs = conn.execute(
            "SELECT reference_key, label, kind, location, relevance, revision, updated_at "
            "FROM project_references WHERE project_key=? AND status='active' "
            "ORDER BY kind, reference_key",
            (project_key,),
        ).fetchall()
    finally:
        conn.close()

    return {
        "gaps": {
            "missing_current_state": state is None,
            "missing_checkpoint": cp is None,
        },
        "project": dict(proj),
        "current_state": dict(state) if state else None,
        "checkpoint": dict(cp) if cp else None,
        "latest_memories": [dict(r) for r in memories],
        "references": [dict(r) for r in refs],
    }


def compute_review(agent_home: Path, project_db: Path | None = None) -> dict[str, Any]:
    verified, missing = verify_governing_docs(agent_home)
    data, gaps = load_agent_orientation(agent_home)
    advisories: list[str] = []

    if missing:
        advisories.append(f"Missing governing docs: {[m['key'] for m in missing]}")
    if data is None:
        advisories.append("Agent continuity database not initialized. Run `tenuto init`.")
    else:
        cs = data["current_state"]
        if cs:
            if len(cs["status_text"]) > 800:
                advisories.append(
                    f"Agent Current State is {len(cs['status_text'])} chars (>800); move project details into `tenuto project state`."
                )
            if gaps.get("project_pointer_not_inquiry"):
                advisories.append(
                    f"Agent active_work pointer is '{cs['active_work']}' instead of 'INQUIRY (ask user)'."
                )
        else:
            advisories.append("No active Agent Current State recorded.")
        if len(data["durable_memory"]) > 12:
            advisories.append(
                f"{len(data['durable_memory'])} active durable memories; consider retiring stale items."
            )
        for item in data["durable_memory"]:
            if not item.get("application_context") or not item.get("success_signal"):
                advisories.append(
                    f"Durable memory '{item['memory_key']}' is missing application_context or success_signal."
                )
        for ref in data["references"]:
            loc = ref["location"]
            if loc.startswith("/") and not os.path.exists(loc):
                advisories.append(f"Reference '{ref['reference_key']}' path missing: {loc}")

    project_db_present = bool(project_db and project_db.is_file())
    project_count = 0
    if project_db_present and project_db is not None:
        conn = connect_ro(project_db)
        try:
            project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        finally:
            conn.close()

    return {
        "verified_docs_count": len(verified),
        "total_docs_count": len(verified) + len(missing),
        "gaps": gaps,
        "advisories": advisories,
        "counts": {
            "current_state_chars": len(data["current_state"]["status_text"]) if (data and data["current_state"]) else 0,
            "active_work": data["current_state"]["active_work"] if (data and data["current_state"]) else None,
            "durable_memory": len(data["durable_memory"]) if data else 0,
            "references": len(data["references"]) if data else 0,
            "open_proposals": len(data["open_proposals"]) if data else 0,
            "project_db_present": project_db_present,
            "projects": project_count,
        },
    }
