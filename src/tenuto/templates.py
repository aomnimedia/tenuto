"""Starter governing documents and verified tool integration templates."""

COMPASS_CUE = (
    "Compass: Accuracy over Speed · Evidence over assumptions · "
    "2 identical failures = pause & re-authorize"
)

STARTER_CONSTITUTION = """# Working Constitution

Five first principles for how we work together:

1. **Accuracy over Speed**
2. **Read the target and review your code before executing**
3. **Evidence over assumptions**
4. **2 identical failures on a task = hard stop for re-authorization**
5. **Always reload continuity after compaction**
"""

STARTER_CONTRACT = """# Developmental Continuity Contract

## 1. Separation of Concerns
- **Agent Continuity (`~/.tenuto/agent.db`)** holds operating posture, working constitution, constructive durable practices, cross-project references, and two-way collaboration proposals.
- **Project Continuity (`.tenuto/project.db`)** holds project framing, Current State, checkpoints, consequential decisions/learnings, and project references.
- Keep Agent Current State's project pointer at `INQUIRY (ask user)`. Never persist a concrete project key into shared agent state.
- Record dynamic decisions and state once in the database — never maintain parallel decision markdown logs.

## 2. Constructive Learning (No Error Ledgers)
- Distill corrections and drift observations into positive durable practices with `application_context` and `success_signal`.
- Do not replay blame, failure narratives, or punitive rule walls in persistent memory.

## 3. Two-Way Collaboration
- Use `remember proposal` to surface workflow improvements, ambiguities, or requests to the user that raise accuracy and speed without sacrificing accuracy.

## 4. Verification & Resumption
- Run `remember startup` at the start of every session and immediately after compaction.
- Checkpoints preserve continuity; they never grant execution authorization on their own.
"""

LAUNCHER_CODEX_SH = """#!/bin/sh
# POSIX shell launcher (Linux / macOS / WSL) for Codex CLI.
# Copy to ~/.local/bin/<agent-name>, chmod +x, and configure [profiles.<agent-name>]
# in ~/.codex/config.toml to run `remember startup` on session boot.
# Usage:
#   <agent-name>           # fresh session in working-constitution posture
#   <agent-name> resume    # resume session in the same posture
set -eu

PROFILE="${TENUTO_CODEX_PROFILE:-tenuto}"
exec codex --profile "$PROFILE" "$@"
"""

LAUNCHER_CLAUDE_SH = """#!/bin/sh
# POSIX shell launcher (Linux / macOS / WSL) for Claude Code.
# Appends the Working Constitution to Claude Code's default system prompt on new
# or resumed sessions (--resume / -c).
set -eu

CONSTITUTION_PATH="__CONSTITUTION_PATH__"
exec claude --append-system-prompt-file "$CONSTITUTION_PATH" "$@"
"""

INTEGRATION_CLAUDE_HOOKS_JSON = """{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "remember startup"
          }
        ]
      }
    ]
  }
}
"""

INTEGRATION_AGENTS_SNIPPET = """## Continuity & Working Posture (Universal — All OSes & IDEs)

1. At session start and immediately after context compaction, run `remember startup`.
2. Follow the 5-Principle Working Constitution echoed by startup.
3. Keep Agent Continuity (`remember ...`) strictly separate from Project Continuity (`tenuto project ...`).
4. Never duplicate dynamic decisions into parallel markdown logs; record them once via `tenuto project memory`.
5. Run `remember review` periodically for a 2-minute separation hygiene check.
"""
