"""Comprehensive unittest suite for Tenuto v0.9.0 (zero external dependencies)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"


class TenutoCLITest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.agent_home = self.root / "agent home #1"
        self.repo_dir = self.root / "sample repo #2"
        self.repo_dir.mkdir()
        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(SRC_DIR)
        self.env["TENUTO_HOME"] = str(self.agent_home)
        self.env.pop("TENUTO_PROJECT_DB", None)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(
        self,
        args: list[str],
        *,
        prog: str = "tenuto",
        stdin_text: str | None = None,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        entry = "main_remember" if prog == "remember" else "main_tenuto"
        code = f"import sys; sys.argv = [{prog!r}] + sys.argv[1:]; from tenuto.cli import {entry}; {entry}()"
        return subprocess.run(
            [sys.executable, "-c", code, *args],
            input=stdin_text,
            text=True,
            capture_output=True,
            cwd=str(cwd or self.repo_dir),
            env=self.env,
        )

    def test_help_and_version_never_create_database(self) -> None:
        for prog in ("remember", "tenuto"):
            res = self.run_cli(["--help"], prog=prog)
            self.assertEqual(res.returncode, 0)
            self.assertIn(prog, res.stdout)
            ver = self.run_cli(["--version"], prog=prog)
            self.assertEqual(ver.returncode, 0)
            self.assertIn("0.9.0", ver.stdout)
        self.assertEqual(self.run_cli(["project", "--help"]).returncode, 0)
        self.assertEqual(self.run_cli(["project", "save", "--help"]).returncode, 0)
        self.assertFalse((self.agent_home / "agent.db").exists())
        self.assertFalse((self.repo_dir / ".tenuto" / "project.db").exists())

    def test_init_two_files_spaces_in_paths_and_non_destructive(self) -> None:
        res = self.run_cli(["init"])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue((self.agent_home / "agent.db").is_file())
        self.assertTrue((self.repo_dir / ".tenuto" / "project.db").is_file())
        self.assertTrue((self.agent_home / "WORKING-CONSTITUTION.md").is_file())
        self.assertTrue((self.agent_home / "CONTINUITY-CONTRACT.md").is_file())

        integ = self.agent_home / "integrations"
        for sh_name in ("codex-launcher.sh", "claude-launcher.sh"):
            sh_file = integ / sh_name
            self.assertTrue(sh_file.is_file())
            self.assertTrue(os.access(sh_file, os.X_OK))
            chk = subprocess.run(["sh", "-n", str(sh_file)], capture_output=True, text=True)
            self.assertEqual(chk.returncode, 0, chk.stderr)

        hooks = json.loads((integ / "claude-hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(hooks["hooks"]["SessionStart"][0]["matcher"], "startup|resume|clear|compact")
        self.assertEqual(hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"], "remember startup")

        w = self.run_cli(
            [
                "durable-save", "k1", "Keep", "Practice",
                "--kind", "behavior", "--application", "Always", "--success", "Clean",
            ],
            prog="remember",
        )
        self.assertEqual(w.returncode, 0, w.stderr)
        res2 = self.run_cli(["init"])
        self.assertEqual(res2.returncode, 0)
        self.assertIn("preserved existing", res2.stdout)
        lst = self.run_cli(["durable-list", "--json"], prog="remember")
        self.assertEqual(lst.returncode, 0)
        self.assertEqual(json.loads(lst.stdout)[0]["memory_key"], "k1")

    def test_agent_full_surface_and_aliases(self) -> None:
        self.assertEqual(self.run_cli(["init"]).returncode, 0)

        # File-based input
        state_file = self.root / "state.txt"
        state_file.write_text("File state with $1,000 and Kelly's note.", encoding="utf-8")
        self.assertEqual(
            self.run_cli(
                ["state", "-", "--file", str(state_file), "--active", "INQUIRY (ask user)", "--posture", "Evidence-first"],
                prog="remember",
            ).returncode,
            0,
        )

        # Durable save, show, revise, retire
        self.assertEqual(
            self.run_cli(
                [
                    "durable-save", "p1", "Practice 1", "-",
                    "--kind", "behavior", "--application", "Coding", "--success", "Tests pass",
                ],
                prog="remember",
                stdin_text="Verify output before claims.",
            ).returncode,
            0,
        )
        show = self.run_cli(["durable-show", "p1", "--json"], prog="remember")
        self.assertEqual(show.returncode, 0)
        self.assertEqual(json.loads(show.stdout)["title"], "Practice 1")
        self.assertEqual(self.run_cli(["durable-retire", "p1"], prog="remember").returncode, 0)
        self.assertEqual(json.loads(self.run_cli(["durable-list", "--json"], prog="remember").stdout), [])
        self.assertEqual(len(json.loads(self.run_cli(["durable-list", "--status", "all", "--json"], prog="remember").stdout)), 1)

        # References save, list, retire
        self.assertEqual(
            self.run_cli(
                [
                    "reference-save", "doc1", "Constitution", "doc",
                    str(self.agent_home / "WORKING-CONSTITUTION.md"),
                    "Governing principles", "--revision", "v1", "--verified", "2026-11-21",
                ],
                prog="remember",
            ).returncode,
            0,
        )
        self.assertEqual(len(json.loads(self.run_cli(["reference-list", "--json"], prog="remember").stdout)), 1)
        self.assertEqual(self.run_cli(["reference-retire", "doc1"], prog="remember").returncode, 0)
        self.assertEqual(json.loads(self.run_cli(["reference-list", "--json"], prog="remember").stdout), [])

        # Two-way collaboration proposals + question/questions/answer aliases
        self.assertEqual(
            self.run_cli(["question", "Short signal for exec mode?", "--context", "Speed + accuracy"], prog="remember").returncode,
            0,
        )
        qs = json.loads(self.run_cli(["questions", "--status", "open", "--json"], prog="remember").stdout)
        self.assertEqual(len(qs), 1)
        self.assertEqual(
            self.run_cli(["answer", "1", "-"], prog="remember", stdin_text="Say 'ship it'.").returncode,
            0,
        )
        self.assertEqual(json.loads(self.run_cli(["proposals", "--status", "open", "--json"], prog="remember").stdout), [])

        # Construction + compass cue + search + stats
        con = self.run_cli(
            [
                "construction", "Built v0.9",
                "--objective", "Ship clean CLI",
                "--evidence", "All tests pass",
                "--result", "Ready for packaging",
                "--boundaries", "No external deps",
                "--hold", "Await publish OK",
                "--tags", "release",
            ],
            prog="remember",
        )
        self.assertEqual(con.returncode, 0, con.stderr)
        self.assertIn("Compass:", con.stdout)
        srch = self.run_cli(["search", "Built v0.9"], prog="remember")
        self.assertIn("Built v0.9", srch.stdout)
        stats = json.loads(self.run_cli(["stats", "--json"], prog="remember").stdout)
        self.assertEqual(stats["daily_active"], 1)
        self.assertEqual(stats["proposals_resolved"], 1)

    def test_project_full_surface_supersedes_and_subdir_discovery(self) -> None:
        self.assertEqual(self.run_cli(["init"]).returncode, 0)
        subdir = self.repo_dir / "nested" / "pkg"
        subdir.mkdir(parents=True)

        # Save + list + state + checkpoint + memory + --supersedes + ref-save/list/retire + history
        self.assertEqual(
            self.run_cli(
                [
                    "project", "save",
                    "--project-key", "demo",
                    "--name", "Demo",
                    "--purpose", "Prove two-file SQLite",
                    "--scope", "v0.9",
                    "--intended-outcomes", "Zero drift",
                ],
                cwd=subdir,
            ).returncode,
            0,
        )
        plist = json.loads(self.run_cli(["project", "list", "--json"], cwd=subdir).stdout)
        self.assertEqual(plist[0]["project_key"], "demo")

        self.assertEqual(
            self.run_cli(["project", "state", "--project-key", "demo", "-"], stdin_text="Milestone $1,000 ready.", cwd=subdir).returncode,
            0,
        )
        self.assertEqual(
            self.run_cli(
                ["project", "checkpoint", "--project-key", "demo", "--completed", "Built", "--next", "Package", "--context", "Clean"],
                cwd=subdir,
            ).returncode,
            0,
        )
        self.assertEqual(
            self.run_cli(
                ["project", "memory", "--project-key", "demo", "--kind", "decision", "--title", "Bad", "Mangled 9-9"],
                cwd=subdir,
            ).returncode,
            0,
        )
        self.assertEqual(
            self.run_cli(
                [
                    "project", "memory", "--project-key", "demo",
                    "--kind", "decision", "--title", "Exact", "-", "--supersedes", "1",
                ],
                stdin_text="Exact $49-$79 & $1,500-$2,500.",
                cwd=subdir,
            ).returncode,
            0,
        )
        self.assertEqual(
            self.run_cli(
                [
                    "project", "ref-save", "--project-key", "demo", "--reference-key", "spec",
                    "--label", "Spec", "--kind", "doc", "--location", "README.md", "--relevance", "Primary doc",
                ],
                cwd=subdir,
            ).returncode,
            0,
        )
        self.assertEqual(len(json.loads(self.run_cli(["project", "ref-list", "--project-key", "demo", "--json"], cwd=subdir).stdout)), 1)
        self.assertEqual(
            self.run_cli(["project", "ref-retire", "--project-key", "demo", "--reference-key", "spec"], cwd=subdir).returncode,
            0,
        )
        self.assertEqual(json.loads(self.run_cli(["project", "ref-list", "--project-key", "demo", "--json"], cwd=subdir).stdout), [])

        # Plain-text and JSON project history
        hist_txt = self.run_cli(["project", "history", "--project-key", "demo", "--table", "memory"], cwd=subdir)
        self.assertEqual(hist_txt.returncode, 0)
        self.assertIn("Exact $49-$79 & $1,500-$2,500.", hist_txt.stdout)
        self.assertNotIn("Mangled 9-9", hist_txt.stdout)
        hist_all = self.run_cli(
            ["project", "history", "--project-key", "demo", "--table", "memory", "--include-superseded"],
            cwd=subdir,
        )
        self.assertIn("SUPERSEDED BY #2", hist_all.stdout)

        # Read-only combined startup --project does not mutate agent active_work
        self.assertEqual(
            self.run_cli(["state", "Ready", "--active", "INQUIRY (ask user)"], prog="remember").returncode,
            0,
        )
        st = self.run_cli(["startup", "--project", "demo", "--json"], prog="remember", cwd=subdir)
        self.assertEqual(st.returncode, 0, st.stderr)
        payload = json.loads(st.stdout)
        self.assertEqual(payload["current_state"]["active_work"], "INQUIRY (ask user)")
        self.assertEqual(payload["project_resume"]["project"]["project_key"], "demo")
        self.assertEqual(len(payload["project_resume"]["latest_memories"]), 1)

    def test_error_paths_and_hygiene_advisories_never_dump_tracebacks(self) -> None:
        self.assertEqual(self.run_cli(["init"]).returncode, 0)

        # Unknown project key returns clean Error:, exit 1, zero traceback
        bad_proj = self.run_cli(["project", "state", "--project-key", "ghost", "Hello"])
        self.assertEqual(bad_proj.returncode, 1)
        self.assertIn("Project 'ghost' not found", bad_proj.stderr)
        self.assertNotIn("Traceback", bad_proj.stderr)

        # Missing --file returns clean Error:, exit 1, zero traceback
        bad_file = self.run_cli(["state", "-", "--file", str(self.root / "nope.txt")], prog="remember")
        self.assertEqual(bad_file.returncode, 1)
        self.assertIn("Error:", bad_file.stderr)
        self.assertNotIn("Traceback", bad_file.stderr)

        # Bad flag on review / stats rejected cleanly
        bad_flag = self.run_cli(["review", "--bogus"], prog="remember")
        self.assertEqual(bad_flag.returncode, 1)
        self.assertIn("Error:", bad_flag.stderr)

        # Double-supersede rejected cleanly
        self.assertEqual(self.run_cli(["daily", "A", "Body A", "--category", "general"], prog="remember").returncode, 0)
        self.assertEqual(self.run_cli(["daily", "B", "Body B", "--category", "general", "--supersedes", "1"], prog="remember").returncode, 0)
        dup_sup = self.run_cli(["daily", "C", "Body C", "--category", "general", "--supersedes", "1"], prog="remember")
        self.assertEqual(dup_sup.returncode, 1)
        self.assertIn("already superseded", dup_sup.stderr)

        # Drift advisories: active_work != INQUIRY, missing constitution doc, broken ref path
        self.assertEqual(self.run_cli(["state", "Working on app", "--active", "demo"], prog="remember").returncode, 0)
        self.assertEqual(
            self.run_cli(
                ["reference-save", "broken", "Missing", "doc", "/no/such/file/here.md", "Test"],
                prog="remember",
            ).returncode,
            0,
        )
        (self.agent_home / "WORKING-CONSTITUTION.md").unlink()
        rev = json.loads(self.run_cli(["review", "--json"], prog="remember").stdout)
        joined = " | ".join(rev["advisories"])
        self.assertIn("Missing governing docs", joined)
        self.assertIn("INQUIRY", joined)
        self.assertIn("path missing", joined)


if __name__ == "__main__":
    unittest.main()
