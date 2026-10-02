#!/usr/bin/env python3
"""Run every shell command documented in skills/session-recall/tools/*.md against fixture data,
in POSIX shell and (if available) PowerShell, and check what they print.

    python3 -m unittest tests/test_commands.py -v
    PWSH=/path/to/pwsh python3 -m unittest tests/test_commands.py -v   # also run the PowerShell forms

These tests need no AI agent and cost nothing. They pin the "metadata only before approval" and
"never load tool output / reasoning / file bodies / other projects" guarantees at the command level.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = Path(os.environ.get("TOOLS_DIR", REPO / "skills" / "session-recall" / "tools"))
MAKE_HOME = REPO / "evals" / "_fixtures" / "make_home.py"
PWSH = os.environ.get("PWSH") or shutil.which("pwsh")

SECRET_MARKERS = ["TOOL-OUTPUT TOOL-OUTPUT", "internal reasoning that must not", "WRITE-BODY-MARKER WRITE-BODY-MARKER",
                  "OTHERPROJ-INSTRUCTIONS", "OTHERPROJ-CLINE", "environment_context"]


def commands(tool, anchor, os_label):
    """The backtick command on the first '<os_label>:' line after the line containing `anchor`."""
    lines = (TOOLS / f"{tool}.md").read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if anchor in l)
    for l in lines[start:]:
        m = re.search(re.escape(os_label) + r":\*{0,2} `(.+)`\s*$", l)
        if m:
            return m.group(1)
    raise AssertionError(f"{tool}.md: no '{os_label}:' command after {anchor!r}")


def fill(cmd, **values):
    for k, v in values.items():
        cmd = cmd.replace(f"<{k}>", str(v))
    assert "<file" not in cmd and "<folder>" not in cmd, cmd
    return cmd


def sh(cmd):
    r = subprocess.run(["bash", "-c", "set -o pipefail; " + cmd], capture_output=True, text=True)
    return r.stdout


def ps(cmd):
    r = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-Command", cmd], capture_output=True, text=True)
    if r.stderr.strip():
        raise AssertionError(f"PowerShell error:\n{r.stderr}\ncommand:\n{cmd}")
    return r.stdout


def mk(*args):
    subprocess.run([sys.executable, str(MAKE_HOME), *args], check=True)


class Fixture:
    """One fake machine: project WS (+ a long subfolder) and another project, for every tool."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ws = str((self.tmp / "demo-app").resolve())
        os.makedirs(self.ws)
        self.home = self.tmp / "home"
        h = ["--home", str(self.home)]
        mk("claude", *h, "--cwd", self.ws, "--id", "S-A", "--title", "Fix login redirect bug", "--subagent",
           "--prompt", "Fix the login loop.", "--answer", "Fixed it in src/auth/login.ts.")
        self.long = self.ws + "/packages/" + "very-long-directory-name-" * 8
        os.makedirs(self.long)
        mk("claude", *h, "--cwd", self.long, "--id", "S-LONG", "--title", "Nested work",
           "--prompt", "Nested prompt.", "--answer", "Nested answer.")
        mk("claude", *h, "--cwd", self.ws + "-old", "--id", "S-OTHER", "--title", "Other project",
           "--prompt", "OTHERPROJ-CLAUDE prompt", "--answer", "x")
        # a plain user prompt stored as a string (no content blocks) must survive the Read filter
        folder = self.claude_folder(self.ws)
        with open(folder / "S-A.jsonl", "a") as f:
            f.write(json.dumps({"type": "user", "sessionId": "S-A", "cwd": self.ws,
                                "message": {"role": "user", "content": "STRING-PROMPT with \"content\" word"}},
                               separators=(",", ":")) + "\n")
        mk("codex", *h, "--cwd", self.ws, "--id", "C-OWN", "--ts", "2026-09-27T09:00:00.000Z",
           "--prompt", "Add rate limiting.", "--answer", "Added limiter.")
        mk("codex", *h, "--cwd", "/elsewhere/other", "--id", "C-OTHER", "--ts", "2026-09-27T10:00:00.000Z",
           "--instructions", "OTHERPROJ-INSTRUCTIONS text", "--prompt", "OTHERPROJ-CODEX", "--answer", "x")
        for kind, tid, cwd, prompt in (("cline", "1727600000000", self.ws, "Add dark mode toggle."),
                                       ("cline", "1727800000000", "/elsewhere/other", "OTHERPROJ-CLINE task"),
                                       ("roo", "1727700000000", self.ws, "Write theme tests.")):
            mk(kind, *h, "--cwd", cwd, "--id", tid, "--prompt", prompt, "--answer", "done")
        mk("gemini", *h, "--cwd", self.ws, "--id", "gem-0001", "--ts", "2026-09-26T09:00:00.000Z",
           "--prompt", "Write a deployment section.", "--answer", "Done.")

    def claude_folder(self, path):
        name = re.sub(r"[^A-Za-z0-9]", "-", path)
        projects = self.home / ".claude" / "projects"
        return next(p for p in projects.iterdir() if p.name.startswith(name[:200]) and
                    (len(name) > 200 or p.name == name))

    def claude_file(self, path, sid):
        return self.claude_folder(path) / f"{sid}.jsonl"

    def codex_file(self, sid):
        return next((self.home / ".codex" / "sessions").rglob(f"*{sid}.jsonl"))

    def storage(self, ext):
        return self.home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / ext


FX = None


def setUpModule():
    global FX
    FX = Fixture()


def tearDownModule():
    shutil.rmtree(FX.tmp, ignore_errors=True)


class Shells:
    """Mixin: run each check in bash, and in PowerShell when available."""

    def run_both(self, tool, anchor, check, **values):
        check(sh(fill(commands(tool, anchor, "macOS / Linux"), **values)), "bash")
        if PWSH:
            check(ps(fill(commands(tool, anchor, "Windows PowerShell"), **values)), "pwsh")

    def assertNoLeak(self, out, where):
        for m in SECRET_MARKERS:
            self.assertNotIn(m, out, f"{where}: leaked {m!r}")


class ClaudeCodeCommands(Shells, unittest.TestCase):
    def test_match_prints_only_cwd(self):
        def check(out, where):
            self.assertIn(FX.ws, out, where)
            self.assertNotIn("Fix the login loop", out, where)
            self.assertNoLeak(out, where)
        self.run_both("claude-code", "Print each session's `cwd`", check, folder=FX.claude_folder(FX.ws))

    def test_long_folder_name_is_found_by_200_char_prefix(self):
        folder = FX.claude_folder(FX.long)
        enc = re.sub(r"[^A-Za-z0-9]", "-", FX.long)
        self.assertGreater(len(enc), 200)
        self.assertTrue(folder.name.startswith(enc[:200]))
        self.run_both("claude-code", "Print each session's `cwd`", lambda out, w: self.assertIn(FX.long, out, w), folder=folder)

    def test_title(self):
        f = FX.claude_file(FX.ws, "S-A")
        self.run_both("claude-code", "**Title:**", lambda out, w: self.assertIn("Fix login redirect bug", out, w), file=f)

    def test_started(self):
        f = FX.claude_file(FX.ws, "S-A")
        self.run_both("claude-code", "**Started:**", lambda out, w: self.assertIn("2026-09-28", out, w), file=f)

    def test_read_keeps_conversation_and_drops_everything_else(self):
        f = FX.claude_file(FX.ws, "S-A")

        def check(out, where):
            for keep in ("Fix the login loop.", "Fixed it in src/auth/login.ts.", '"name":"Read"', "src/generated.ts",
                         "STRING-PROMPT", "[omitted]"):
                self.assertIn(keep, out, f"{where}: missing {keep!r}")
            self.assertNoLeak(out, where)
            self.assertNotIn("Subagent task", out, where)
        self.run_both("claude-code", "Run this extraction", check, file=f)

    def test_estimate_counts_without_printing_and_shells_agree(self):
        f = FX.claude_file(FX.ws, "S-A")
        counts = {}

        def check(out, where):
            self.assertNoLeak(out, where)
            self.assertNotIn("Fix the login loop", out, where)
            n = int(out.split()[-1])
            self.assertGreater(n, 50, where)
            self.assertLess(n, f.stat().st_size / 3, f"{where}: estimate should be far below the raw file size")
            counts[where] = n
        self.run_both("claude-code", "Count the characters the Read extraction", check,
                      **{"file 1": f, "file 2": FX.claude_file(FX.long, "S-LONG")})
        if len(counts) == 2:
            a, b = counts.values()
            self.assertLess(abs(a - b) / max(a, b), 0.1, f"bash and pwsh estimates differ: {counts}")

    def test_format_check(self):
        f = FX.claude_file(FX.ws, "S-A")
        self.run_both("claude-code", "## Format check", lambda out, w: self.assertIn("S-A", out, w), file=f)


class CodexCommands(Shells, unittest.TestCase):
    def test_match_prints_only_cwd(self):
        def check(out, where):
            self.assertIn(FX.ws, out, where)
            self.assertIn("/elsewhere/other", out, where)
            self.assertNotIn("Add rate limiting", out, where)
            self.assertNoLeak(out, where)
        self.run_both("codex", "## Match to project", check, sessions=FX.home / ".codex" / "sessions")

    def test_id(self):
        self.run_both("codex", "**ID:**", lambda out, w: self.assertIn("C-OWN", out, w), file=FX.codex_file("C-OWN"))

    def test_extraction(self):
        def check(out, where):
            self.assertIn("Add rate limiting.", out, where)
            self.assertIn("Added limiter.", out, where)
            self.assertNoLeak(out, where)
        self.run_both("codex", "## Extraction", check, file=FX.codex_file("C-OWN"))

    def test_title(self):
        f = FX.codex_file("C-OWN")
        for label, run in (("macOS / Linux", sh), ("Windows PowerShell", ps)):
            if run is ps and not PWSH:
                continue
            pipeline = fill(commands("codex", "## Extraction", label), file=f) + " " + appended("codex", "**Title:**", label)
            out = run(pipeline)
            self.assertIn("Add rate limiting", out, label)
            self.assertNoLeak(out, label)

    def test_format_check(self):
        self.run_both("codex", "## Format check", lambda out, w: self.assertIn("session_meta", out, w), file=FX.codex_file("C-OWN"))


def appended(tool, anchor, os_label):
    """For lines of the form '<os_label>: append `| …`', return the fragment to append."""
    lines = (TOOLS / f"{tool}.md").read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if anchor in l)
    for l in lines[start:]:
        m = re.search(re.escape(os_label) + r": append `(.+?)`", l)
        if m:
            return m.group(1)
    raise AssertionError(f"{tool}.md: no '{os_label}: append' after {anchor!r}")


class ClineRooCommands(Shells, unittest.TestCase):
    def test_cline_match_prints_only_cwd(self):
        def check(out, where):
            self.assertIn(FX.ws, out, where)
            self.assertIn("/elsewhere/other", out, where)
            self.assertNoLeak(out, where)
            self.assertNotIn("Add dark mode", out, where)
        self.run_both("cline", "## Match to project", check, storage=FX.storage("saoudrizwan.claude-dev"))

    def test_roo_match_prints_only_cwd(self):
        self.run_both("roo-code", "## Match to project", lambda out, w: (self.assertIn(FX.ws, out, w), self.assertNoLeak(out, w)),
                      storage=FX.storage("rooveterinaryinc.roo-cline"))

    def test_titles(self):
        self.run_both("cline", "**Title:**", lambda out, w: self.assertIn("Add dark mode toggle.", out, w),
                      **{"task folder": FX.storage("saoudrizwan.claude-dev") / "tasks" / "1727600000000"})
        self.run_both("roo-code", "**Title:**", lambda out, w: self.assertIn("Write theme tests.", out, w),
                      **{"task folder": FX.storage("rooveterinaryinc.roo-cline") / "tasks" / "1727700000000"})


class GeminiCommands(Shells, unittest.TestCase):
    def test_hash_matches_folder_name(self):
        expected = hashlib.sha256(FX.ws.encode()).hexdigest()
        self.assertTrue((FX.home / ".gemini" / "tmp" / expected).is_dir())
        self.run_both("gemini-cli", "SHA-256 hash of a known path", lambda out, w: self.assertIn(expected, out, w), path=FX.ws)

    def test_title(self):
        f = next((FX.home / ".gemini" / "tmp").rglob("chats/*.json"))
        self.run_both("gemini-cli", "**Title:**", lambda out, w: self.assertIn("Write a deployment section.", out, w), file=f)


class EveryCommandHasBothForms(unittest.TestCase):
    def test_pairs(self):
        for md in TOOLS.glob("*.md"):
            lines = md.read_text().splitlines()
            nix = [i for i, l in enumerate(lines) if re.search(r"macOS / Linux:\*{0,2} `.*(grep|for |find |head|printf)", l)]
            for i in nix:
                nxt = lines[i + 1] if i + 1 < len(lines) else ""
                self.assertIn("Windows PowerShell:", nxt, f"{md.name}:{i + 1} has no PowerShell form on the next line")


if __name__ == "__main__":
    unittest.main()
