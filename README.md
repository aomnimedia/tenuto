# Tenuto

**Held to its full value — Accuracy over Speed.**

Tenuto is a zero-dependency Python + SQLite continuity system for long-horizon AI coding-agent sessions (Claude Code, Codex CLI, Cursor, Antigravity, OpenClaw). It ships two first-class CLI entry points from one tiny package:

- **`remember`** — private **Agent Developmental Continuity** (`~/.tenuto/agent.db`): working constitution, constructive durable practices, two-way collaboration proposals, checkpoints, and separation hygiene.
- **`tenuto project`** — shareable **Project Continuity** (`.tenuto/project.db`): project framing, current state, checkpoints, consequential decisions/learnings, and authoritative references.

Both halves run on Python's built-in `sqlite3`. No servers, no Docker, no vector database, no API keys.

---

## Why Two Separate SQLite Files?

Long coding-agent sessions fail in two predictable ways:

1. **Punitive memory bloat:** Appending *"NEVER DO X"* error ledgers into `CLAUDE.md` / `MEMORY.md` pollutes context and degrades adherence. Tenuto consolidates learning constructively (`practice + application_context + success_signal`) and reinforces a short 5-principle constitution across session transitions.
2. **Agent-vs-Project bleed:** Agents lazily dump project task trivia into personal agent memory. Separating private `~/.tenuto/agent.db` from repo-local `.tenuto/project.db` enforces the boundary at the filesystem level.

---

## 30-Second Quickstart

```bash
pip install tenuto
tenuto init
remember startup
```

`tenuto init` safely creates (never overwriting existing databases):
- `~/.tenuto/agent.db` + `WORKING-CONSTITUTION.md` + `CONTINUITY-CONTRACT.md`
- `.tenuto/project.db` in your repository
- `~/.tenuto/integrations/` ready-to-copy templates:
  - `codex-launcher.sh` (`codex --profile` + `resume` posture wrapper)
  - `claude-launcher.sh` (`claude --append-system-prompt-file` wrapper)
  - `claude-hooks.json` (`SessionStart` hook for `startup|resume|clear|compact`)
  - `AGENTS-snippet.md` (universal boot block for all OSes and IDEs)

---

## Core Commands

### Agent Continuity (`remember` or `tenuto`)

```bash
remember startup [--project KEY] [--json]
remember review [--json]
remember state - --active "INQUIRY (ask user)" --posture "Evidence-first" <<'EOF'
Fresh, complete agent orientation snapshot.
EOF
remember durable-save key "Title" - --kind behavior --application "When..." --success "Verified..." <<'EOF'
Positive target practice — never an error ledger.
EOF
remember proposal "What I need from you to raise accuracy..." --context "Workflow friction"
remember checkpoint "Completed X" --next "Next useful step (not authorization)"
remember daily "Title" - --category significant_learning [--supersedes ID] <<'EOF'
Shell-safe text with $1,000 and apostrophes intact.
EOF
```

### Project Continuity (`tenuto project`)

```bash
tenuto project save --project-key app --name "App" --purpose "..." --scope "..." --intended-outcomes "..."
tenuto project list
tenuto project resume --project-key app [--json]
tenuto project state --project-key app - <<'EOF'
Current milestone evaluation.
EOF
tenuto project memory --project-key app --kind decision --title "Title" - [--supersedes ID] <<'EOF'
Decision rationale.
EOF
tenuto project checkpoint --project-key app --completed "Did X" --next "Next Y" [--context "..."]
tenuto project ref-save --project-key app --reference-key spec --label "Spec" --kind doc --location "docs/SPEC.md" --relevance "Design contract"
```

---

## Five-Principle Working Constitution

1. **Accuracy over Speed**
2. **Read the target and review your code before executing**
3. **Evidence over assumptions**
4. **2 identical failures on a task = hard stop for re-authorization**
5. **Always reload continuity after compaction**

---

## License

MIT — © 2026 Kelly Asay / AOmniMedia (Computational Intelligence Development)
