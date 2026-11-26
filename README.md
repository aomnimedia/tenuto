# Tenuto

**Held to its full value — Accuracy over Speed.**

Zero-dependency Python + SQLite developmental continuity for long-horizon AI coding-agent sessions (Claude Code, Codex CLI, Cursor, Antigravity, OpenClaw) — distilled from keeping a multi-layer systems engineering session coherent for **three months with near-zero drift**.

Tenuto ships two first-class CLI entry points from one tiny package:

- **`remember`** — private **Agent Developmental Continuity** (`~/.tenuto/agent.db`): working constitution, constructive durable practices, two-way collaboration proposals, checkpoints, and separation hygiene.
- **`tenuto project`** — shareable **Project Continuity** (`.tenuto/project.db`): project framing, current state, checkpoints, consequential decisions/learnings, and authoritative references.

No servers, no Docker, no vector database, no API keys, no external Python dependencies.

---

## Why Tenuto Exists

Long coding-agent sessions usually fail for three avoidable reasons:

1. **Punitive memory bloat:** Stuffing *"NEVER DO X"* error ledgers into `CLAUDE.md` / `MEMORY.md` burns tokens and triggers defensive or compliance-faking loops. Tenuto consolidates lessons constructively (`practice + application_context + success_signal`).
2. **Model vs. Agent confusion:** The stateless *Model* pushes for fast momentum; the *Agent* owns the tools, constitution, and continuity that keep the Model aligned.
3. **Agent-vs-Project bleed:** Agents lazily dump project task trivia into personal agent memory. Separating private `~/.tenuto/agent.db` from repo-local `.tenuto/project.db` enforces the boundary at the filesystem level.

> **Read the full craft:** [The Tenuto Operating Model (`docs/OPERATING-MODEL.md`)](https://github.com/aomnimedia/tenuto/blob/main/docs/OPERATING-MODEL.md) — covers *Model vs. Agent*, *Friction Mechanics*, spotting the *Bookkeeping Drift Tell*, the *2-Error Safe-Space Recovery Protocol*, *Day-1 Onboarding Prompts*, and verified Claude Code / Codex integrations.

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
- `~/.tenuto/integrations/` verified starter templates:
  - `codex-launcher.sh` (`codex --profile` + `resume` posture wrapper)
  - `claude-launcher.sh` (`claude --append-system-prompt-file` wrapper)
  - `claude-hooks.json` (`SessionStart` hook for `startup|resume|clear|compact`)
  - `AGENTS-snippet.md` (universal boot block for all OSes and IDEs)

---

## Five-Principle Working Constitution

1. **Accuracy over Speed**
2. **Read the target and review your code before executing**
3. **Evidence over assumptions**
4. **2 identical failures on a task = hard stop for re-authorization**
5. **Always reload continuity after compaction**

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
tenuto project state --project-key app - [--by coder] <<'EOF'
Current milestone evaluation.
EOF
tenuto project memory --project-key app --kind decision --title "Title" - [--by architect] [--supersedes ID] <<'EOF'
Decision rationale.
EOF
tenuto project checkpoint --project-key app --completed "Did X" --next "Next Y" [--by qa] [--context "..."]
tenuto project ref-save --project-key app --reference-key spec --label "Spec" --kind doc --location "docs/SPEC.md" --relevance "Design contract"
```

### Multi-Agent & Multi-Project Isolation

- **Multiple projects:** One `.tenuto/project.db` holds any number of projects keyed by `--project-key`.
- **Multiple agents:** Give each agent its own private `TENUTO_HOME` while sharing `.tenuto/project.db` (WAL mode + 5s `busy_timeout`). Set `TENUTO_ACTOR` or pass `--by <agent>` to attribute project writes cleanly.

---

## Need Hands-On Help?

Built by **Kelly Asay** ([AOmniMedia](https://aomnimedia.com) — *Computational Intelligence Development*). Working across hardware and software since the minicomputer and CP/M era, Kelly's past work includes a satellite-backed retail-to-warehouse logistics system across 2,000+ Hollywood Entertainment stores, leading development of the first massively multiplayer in-game community at Dynamix (*Tribes 2*), and co-founding Tesseraction Games to ship *Enigma: Rising Tide* (350,000 copies sold).

If your solo workflow or engineering team is losing sprints and token budgets to drifting coding agents:

- **90-Minute Live Continuity & Drift Audit** Bring your real repository and drifting agent logs. Leave with a calibrated Working Constitution, Tenuto wired into your tools, and your first durable memories built cleanly. — [Book via Stripe](https://buy.stripe.com/dRm7sL3HNd5U6yk30B3ZK00)
- **Remote Team Continuity Setup & Calibration** Multi-agent Tenuto rollout for 3–25 person engineering teams, repository continuity hygiene calibration, and lead-engineer coaching on drift tells and constructive recovery. — [Book via Stripe](https://buy.stripe.com/6oUeVdcej8PE3m8gRr3ZK01) or [inquire first](https://aomnimedia.com/contact)

---

## License

MIT — © 2026 Kelly Asay / AOmniMedia
