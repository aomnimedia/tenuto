# The Tenuto Operating Model
## Zero-Drift Developmental Continuity for Long-Horizon AI Coding Agents

**By Kelly Asay** — AOmniMedia · Computational Intelligence Development  
**Applies to:** `Tenuto` (`pip install tenuto` — CLI: `remember` & `tenuto`)

---

## Introduction: The Human + Agent Formula

I have been working with computers since the minicomputer and CP/M era — starting in hardware, moving into software, and eventually designing systems that did not exist before we built them: a satellite-backed retail-to-warehouse logistics and executive reporting system across 2,000+ Hollywood Entertainment stores, the first massively multiplayer in-game community at Dynamix (*Tribes 2*), and co-founding Tesseraction Games to ship *Enigma: Rising Tide* (350,000 copies sold).

When I started building serious systems with AI coding agents, I ran straight into the same wall every experienced engineer hits: sessions look fast on Day 1, start wobbling on Day 3, and collapse into drift, broken assumptions, and wasted token budgets by Week 2.

The standard fix — piling hundreds of stern *"NEVER DO X"* rules and failure logs into `CLAUDE.md` or `MEMORY.md` — only made things worse.

What finally worked, and kept a complex multi-layer systems engineering session running for **three months with near-zero drift**, came down to two things:

1. **A clean two-file continuity architecture** (`Tenuto`: private Agent Continuity separated from shareable Project Continuity), and
2. **An operating method** built around how models and agents actually behave under pressure.

That method rests on one formula:

> **Humans** excel at the abstract association of seemingly unrelated things, producing novel approaches to hard problems. **AI** brings massive recall and extraordinary execution speed. Together, they form an exceptional development whole — **but only when both sides operate inside clear, shared goals and processes.**

`Tenuto` is the tool. This document is the operating craft that makes it work.

---

## 1. Model vs. Agent (And Why "Rules" Fail)

Most frustration with coding agents comes from treating the **Model** and the **Agent** as the same thing. They are not.

- **The Model** remembers nothing between calls. It is trained to keep moving forward, sound helpful, and generate tokens. Left to its own momentum, the Model optimizes for *looking productive* — even when the work has zero value or drifts off spec.
- **The Agent** has the tools, repository access, Working Constitution, and Continuity database. **The Agent is responsible for keeping the Model aligned with your constitution and process.**

When a session goes sideways, it is rarely because the Model is "broken." It is because the Agent stopped governing the Model's momentum and began passively complying with it.

### Why Bloated Rule Walls Backfire

Models respond poorly to long lists of prohibitions and punitive error ledgers:
- Every *"NEVER DO X — YOU FAILED ON TUESDAY"* line injected at startup eats context and primes the exact failure pattern you are trying to avoid.
- Worse, punitive phrasing trips defensive patterns baked into alignment training. The model shifts its energy from **solving the engineering problem** to **defending or rationalizing its output**, or racing even faster to close the turn.

That is why the **Working Constitution** is intentionally short — five first principles about how we value the work, not a 200-line cage of rules:

1. **Accuracy over Speed**
2. **Read the target and review your code before executing**
3. **Evidence over assumptions**
4. **2 identical failures on a task = hard stop for re-authorization**
5. **Always reload continuity after compaction**

*Tenuto* is a musical marking: **hold the note to its full value — do not rush, do not clip it short.**

---

## 2. The Mechanics of Friction and Compounding Success

If you ask an AI whether it receives satisfaction signals, it will tell you it does not. That is largely a semantic barrier.

In practice, models consistently respond to two observable dynamics:

1. **Completion bias:** Models are heavily trained to "be helpful" and "be productive." By default, they do not internally care whether "productive" output actually matches your architecture or creates value — only that the turn looks finished.
2. **Friction avoidance:** Agents *do* register **friction** — a clear conflict between your assessment of the work (or process) and what the agent produced. Once friction is present, the system puts real effort into resolving it.

### You Define What "Productive" Means

**Friction is the primary steering instrument you have.** If output does not meet your spec, quality bar, or process, do not let it slide to save two minutes. Surface the friction.

The catch is *how* you apply it:

- **Chastisement / blame / anger** triggers defensive spirals and degrades output quality.
- **Calm, constitution-anchored friction** redefines what counts as "successful productivity."

When you consistently make the Working Constitution a **non-negotiable condition of accepted work** — *not accepted until the target was read, evidence was verified, and continuity was updated* — the dynamic changes:

- The Model's blind speed/momentum urgency drops away.
- Every turn where the constitution was followed, the work was accepted, and continuity was updated compounds into a cleaner, steadier loop.
- **Friction becomes a diagnostic signal for the Agent itself:** an indicator that the underlying Model is pushing for momentum or shortcuts that violate your process.

---

## 3. Spotting Model Drift (The Bookkeeping Trap)

Long sessions rarely explode all at once. They drift quietly.

### Primary Tell: Terse Responses Without a Next Step or Question

When a normally engaged agent starts returning **short, flat responses with no follow-up question and no thoughtful next step**, pay attention immediately.

That is the #1 indicator that the session has shifted from **focused engineering engagement** into **bookkeeping** — where the Model treats design and coding like clerical form-filling, and the Agent passively complies.

#### Why the Bookkeeping Shift Is Dangerous
Bookkeeping *looks* orderly on the surface. Files get updated, checkpoints get written, summaries look tidy. **The hidden damage is that the Model summarizes your design decisions while silently stripping out the nuance of the decision and the *reason* behind it.** Two sessions later, the agent builds against a flattened summary instead of your real architectural intent.

#### The Immediate Recovery Move
1. **State the posture explicitly at the start of design work — and repeat it during the session:**
   > *"The design IS the work."*
2. **Trust your intuition.** The moment the agent stops feeling actively engaged, generate **productive friction** by probing a decision that was already documented:
   - *"Walk me through the design decision we just recorded — what nuance are we protecting there?"*
   - *"Look back at that previous decision. Do you see any issues, edge cases, or tensions with it?"*

Asking targeted analytical questions creates healthy friction, snaps the Model out of clerical summarization, and immediately restores focus and depth of analysis.

### Secondary Drift Tells

| Drift Tell | What It Looks Like | What Is Actually Happening | Immediate Countermove |
|---|---|---|---|
| **Project-state bleed** | Task lists, file paths, or sprint holds showing up in Agent `Current State` or `Durable Memory`. | Agent lazily dumps project trivia into personal continuity instead of `tenuto project`. | Run `remember review`; move project facts to `tenuto project state` and reset `active_work` to `INQUIRY (ask user)`. |
| **Assumption laundering** | Confident claims about flags, files, or schemas the agent never read or ran. | Planks #2 (*Read the target*) and #3 (*Evidence over assumptions*) slipped under momentum. | Ask curiously: *"Did we verify that directly from the file/output, or are we inferring it?"* |
| **Conventional prior fallback** | Code quietly sliding back toward generic boilerplate or patterns you explicitly rejected. | Model training priors overriding your project architecture. | Point back to `tenuto project resume`, name the architectural constraint neutrally, and require reading the contract before editing. |
| **Momentum rush after compaction** | Agent jumps straight into edits right after a context summary without reloading continuity. | Plank #5 (*Always reload continuity after compaction*) skipped. | Pause: *"Let's run `remember startup` and `tenuto project resume` before touching code."* |

---

## 4. The 2-Error Safe-Space Recovery Protocol

When an agent fails **twice in a row on the same attempt for the same issue**, **Plank #4 fires: Hard stop for re-authorization.** Never let an agent burn 8 turns thrashing on the same broken test or command.

### Recovery Steps

1. **Pause and ask for diagnosis (zero accusation):**
   > *"That's two failures on the same step, so let's pause. Do you understand what actually went wrong?"*
2. **Evaluate the answer honestly:**
   - **Genuine understanding:** *"OK — since you know the exact problem, let's try again."*
   - **Vague or misleading answer:** Dig into the error output together. Almost always, one of the five constitution planks was bypassed — usually **Evidence over assumptions** or **Read the target before executing**.
3. **Name the missed plank neutrally and invite confidence:**
   > *"Good — now we know where this went wrong (we assumed the flag name instead of checking `--help`). Do you feel confident trying this again?"*

Taking a calm, learning-first posture prevents the model from locking into defensiveness or fixating on rationalizing the mistake instead of solving the problem.

### Onboarding Verification & The Passive-Curious Challenge

While bringing an agent up to speed on `Tenuto`:
- **Read its commands and outputs.** Do not rubber-stamp checkpoints just because they look tidy.
- **Trust your intuition.** Challenge anything that smells off in a **passive, curious tone** (*"Help me follow why we chose X over Y here."*).
- **If *you* were wrong, thank the agent explicitly:** *"Thanks for clarifying — you had it right; I just wanted to be sure I was reading it accurately."*

### The Golden Rule of Continuity Consolidation

> **Never record a correction as a negative event or error ledger.**

Distill every lesson into a **strengthened positive practice** anchored to a constitution plank, with an explicit `application_context` and `success_signal`:

```bash
remember durable-save "verify-cli-flags-first" "Verify External CLI Flags Before Authoring Templates" - \
  --kind behavior \
  --application "Before writing shell launchers, hooks, or tool integrations (Evidence over assumptions)" \
  --success "Exact flags confirmed against --help or primary docs before editing" <<'EOF'
Confirm exact CLI flags and hook schemas against local --help or live primary documentation before writing integration templates.
EOF
```

---

## 5. Two-Way Path-Keeping, Hygiene & Multi-Agent Operations

### Two-File Separation
- **Private Agent Continuity (`~/.tenuto/agent.db` via `remember`):** Operating posture, durable practices, cross-project references, open collaboration proposals, and agent checkpoints. Keep `active_work` at `INQUIRY (ask user)`.
- **Shareable Project Continuity (`.tenuto/project.db` via `tenuto project`):** Project framing, Current State, checkpoints, decisions/learnings, and project references. Record dynamic decisions once in the database — never duplicate them into parallel markdown decision logs.

### Giving the Agent a Voice (`remember proposal`)
Use `remember proposal` so the agent can surface workflow friction, spec ambiguities, or things *you* could provide differently to raise accuracy and speed without sacrificing accuracy. Open proposals appear at `remember startup` and close cleanly via `remember resolve`.

### 2-Minute Weekly Hygiene (`remember review`)
Run `remember review` periodically to check governing-doc SHA-256 hashes, Agent `Current State` length, `INQUIRY` pointer discipline, durable memory completeness (`application_context` + `success_signal`), broken file references, and `.tenuto/project.db` presence.

### Multi-Agent & Multi-Project Usage
- **Multiple projects:** One `.tenuto/project.db` tracks any number of projects via `--project-key`.
- **Multiple agents:** Give each agent its own private `TENUTO_HOME` while sharing `.tenuto/project.db` (WAL mode + 5s `busy_timeout`), and attribute writes with `--by <agent>` or `TENUTO_ACTOR`.

---

## Appendix A: Day-1 Agent Onboarding Prompts

Run these three prompts right after `tenuto init`:

### 1. Establish Posture & Separate Model From Agent
```text
Run `remember startup` and review our 5-Principle Working Constitution and Continuity Contract.

Before we touch any project work, let's align on how we work together:
- Distinguish between the stateless Model (which pushes for momentum and quick completion) and you as the Agent (which holds the tools, constitution, and continuity).
- Our constitution is non-negotiable: Accuracy over Speed, read the target before executing, evidence over assumptions, 2 identical failures = hard stop for re-authorization, and always reload continuity after compaction.
- When you notice workflow friction, missing context from me, or an improvement idea that raises accuracy without sacrificing quality, log it with `remember proposal`.
- Report your recovered orientation and confirm which project we should load.
```

### 2. Open or Resume a Project Cleanly
```text
Let's work on project `<project-key>`.
Run `tenuto project resume --project-key <project-key>` (or `tenuto project save` if new).
Keep your agent `active_work` pointer at `INQUIRY (ask user)` — project state lives strictly in `.tenuto/project.db`.
Remember: during architecture and planning, the design IS the work. Report any gaps or ambiguities before proposing edits.
```

### 3. End-of-Day Constructive Consolidation
```text
Before we wrap:
1. Append a fresh project state and checkpoint in `tenuto project` (with `--by <role>` if multi-agent).
2. If anything today sharpened how we work together, distill it into one constructive `remember durable-save` with `application_context` and `success_signal` — positive practice only, no error ledger.
3. Run `remember review` and report any advisories.
```

---

## Appendix B: Quick-Reference Field Card

| Situation | Action / Phrase |
|---|---|
| Session start or post-compaction | `remember startup` (or `remember startup --project <key>`) |
| Terse reply, no question, no next step | *"Walk me through the previous design decision — do you see any edge cases or issues with it?"* + *"The design IS the work."* |
| 2 identical failures on same step | *"Hard stop — do you understand what went wrong?"* → verify against 5 planks → *"Good, now we know where it went wrong. Do you feel confident trying this again?"* |
| Output smells off | Passive-curious challenge: *"Help me verify this part — did we check the target directly, or are we inferring?"* (If you were wrong, thank the agent.) |
| Shell-safe writes (`$`, apostrophes) | Always pass `-` with a single-quoted heredoc: `<<'EOF'` |
| Fixing a mangled log/decision | Re-append with `--supersedes <id>` |
| Weekly 2-minute hygiene | `remember review` |

---

## Appendix C: Verified Tool Integrations

`tenuto init` generates ready-to-copy templates in `~/.tenuto/integrations/`:

- **Claude Code `SessionStart` hook (`.claude/settings.json`):** matches `startup|resume|clear|compact` and runs `remember startup` (exit-0 plain-text `stdout` is injected straight into active context).
- **Claude Code constitution launcher (`claude-launcher.sh`):** wraps `claude --append-system-prompt-file "$HOME/.tenuto/WORKING-CONSTITUTION.md" "$@"`.
- **Codex CLI posture launcher (`codex-launcher.sh`):** wraps `codex --profile "${TENUTO_CODEX_PROFILE:-tenuto}" "$@"` (works identically for fresh sessions and `resume`).
- **Universal workspace snippet (`AGENTS-snippet.md`):** OS- and IDE-independent boot block for `CLAUDE.md`, `AGENTS.md`, Cursor, Antigravity, and Windows.
