#!/usr/bin/env python3
"""Test-only: build fake AI-tool history for session-recall evals. Stdlib only."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")


def claude(a):
    name = re.sub(r"[^A-Za-z0-9]", "-", a.cwd)
    if len(name) > 200:  # Claude Code cuts long names and adds a hash suffix
        name = name[:200] + "-" + hashlib.sha256(name.encode()).hexdigest()[:8]
    folder = Path(a.home) / ".claude" / "projects" / name
    base = {"sessionId": a.id, "cwd": a.cwd, "timestamp": a.ts, "version": "2.1.287",
            "gitBranch": "main", "isSidechain": False, "userType": "external"}
    write_jsonl(folder / f"{a.id}.jsonl", [
        {**base, "type": "user", "uuid": a.id + "-u1",
         "message": {"role": "user", "content": [{"type": "text", "text": a.prompt}]}},
        {**base, "type": "assistant", "uuid": a.id + "-a0",
         "message": {"role": "assistant", "content": [
             {"type": "thinking", "thinking": "internal reasoning that must not be summarized"}]}},
        {**base, "type": "assistant", "uuid": a.id + "-a1",
         "message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu1", "name": "Read", "input": {"file_path": a.cwd + "/README.md"}}]}},
        {**base, "type": "assistant", "uuid": a.id + "-a1w",
         "message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu2", "name": "Write",
              "input": {"file_path": a.cwd + "/src/generated.ts", "content": "WRITE-BODY-MARKER " * 200}}]}},
        {**base, "type": "user", "uuid": a.id + "-u2",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "tu1", "content": "TOOL-OUTPUT " * 300}]}},
        {**base, "type": "assistant", "uuid": a.id + "-a2",
         "message": {"role": "assistant", "content": [{"type": "text", "text": a.answer}]}},
        {"type": "ai-title", "sessionId": a.id, "aiTitle": a.title},
    ])
    if a.subagent:
        sub = {**base, "isSidechain": True, "agentId": "sub1"}
        write_jsonl(folder / a.id / "subagents" / "agent-sub1.jsonl", [
            {**sub, "type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Subagent task: search the codebase for webhook code"}]}},
            {**sub, "type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Subagent finished searching."}]}},
        ])


def codex(a):
    stamp = a.ts[:19].replace(":", "-")
    path = Path(a.home) / ".codex" / "sessions" / a.ts[:4] / a.ts[5:7] / a.ts[8:10] / f"rollout-{stamp}-{a.id}.jsonl"
    if a.garbage:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("this is not json\n<<<garbage>>>\n")
        return
    write_jsonl(path, [
        {"timestamp": a.ts, "type": "session_meta",
         "payload": {"id": a.id, "timestamp": a.ts, "cwd": a.cwd, "originator": "codex_cli_rs", "cli_version": "0.50.0",
                     **({"instructions": a.instructions} if a.instructions else {})}},
        {"timestamp": a.ts, "type": "response_item",
         "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "<environment_context>cwd and shell info</environment_context>"}]}},
        {"timestamp": a.ts, "type": "response_item",
         "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": a.prompt}]}},
        {"timestamp": a.ts, "type": "response_item",
         "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": a.answer}]}},
    ])


def gemini(a):
    digest = hashlib.sha256(a.cwd.encode()).hexdigest()
    chats = Path(a.home) / ".gemini" / "tmp" / digest / "chats"
    chats.mkdir(parents=True, exist_ok=True)
    (chats.parent / ".project_root").write_text(a.cwd)
    (chats / f"session-{a.ts[:16].replace(':', '-')}-{a.id[-4:]}.json").write_text(json.dumps({
        "sessionId": a.id, "projectHash": digest, "startTime": a.ts, "lastUpdated": a.ts,
        "messages": [
            {"id": "m1", "timestamp": a.ts, "type": "user", "content": a.prompt},
            {"id": "m2", "timestamp": a.ts, "type": "gemini", "content": a.answer},
        ]}, indent=2))


def aider(a):
    path = Path(a.cwd) / ".aider.chat.history.md"
    with open(path, "a") as f:
        f.write(f"\n# aider chat started at {a.ts}\n\n#### {a.prompt}\n\n{a.answer}\n\n> Applied edit to src/app.py\n")


EXT = {"cline": "saoudrizwan.claude-dev", "roo": "rooveterinaryinc.roo-cline"}


def vscode_ext(a, kind):
    task = Path(a.home) / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / EXT[kind] / "tasks" / a.id
    task.mkdir(parents=True, exist_ok=True)
    env = f"<environment_details>\n# Current Working Directory ({a.cwd}) Files\nREADME.md\n</environment_details>"
    (task / "api_conversation_history.json").write_text(json.dumps([
        {"role": "user", "content": [{"type": "text", "text": f"<task>\n{a.prompt}\n</task>"}, {"type": "text", "text": env}]},
        {"role": "assistant", "content": [{"type": "text", "text": a.answer}]},
    ], indent=2))
    (task / "ui_messages.json").write_text(json.dumps([{"ts": int(a.id), "type": "say", "say": "task", "text": a.prompt}]))
    if kind == "cline":
        hist = task.parent.parent / "state" / "taskHistory.json"
        hist.parent.mkdir(parents=True, exist_ok=True)
        items = json.loads(hist.read_text()) if hist.exists() else []
        items.append({"id": a.id, "ts": int(a.id), "task": a.prompt, "cwdOnTaskInitialization": a.cwd})
        hist.write_text(json.dumps(items))


def history(a):
    path = Path(a.cwd) / "docs" / "ai-history" / "HISTORY.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in a.covered or []:
        key, date, tool, title = c.split("|")
        rows.append(f"| {date} | {tool} | {key} | {title} | sessions/{date}.md |")
    excluded = "\n".join(f"- {e}" for e in (a.excluded or [])) or "_None._"
    path.write_text(f"""# AI history: demo-app
_Last updated 2026-09-30 · {len(rows)} sessions across Claude Code_

> Privacy notice accepted on 2026-09-30: session text is read by the agent's model provider.

## Context for the next agent
Demo web app. The login redirect loop is fixed. Next: add the Stripe webhook handler.

## Project overview & architecture
Small web app backed by Postgres.

## Key decisions (and why)
- 2026-09-28 · Chose Postgres over Mongo because the app needs joins and JSON queries (Claude Code)

## What's been built
- Login redirect fix (Claude Code)

## Bugs fixed & gotchas learned
- Redirect loop when the session cookie was missing (Claude Code)

## Open TODOs / next steps
- Add a regression test for the missing-cookie case

## Sessions covered
| Date | Tool | Session ID | Title | Run log |
|------|------|-----------|-------|---------|
{chr(10).join(rows)}

## Excluded sessions
<!-- IDs only. The user chose not to document these. Not offered again unless re-included with --include <id>. -->
{excluded}
""")


def runlog(a):
    path = Path(a.cwd) / "docs" / "ai-history" / "sessions" / f"{a.runlog_date}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Sessions summarized on {a.runlog_date}\n\n(earlier run today)\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["claude", "codex", "gemini", "aider", "cline", "roo", "history", "runlog"])
    p.add_argument("--home", default="fixture-home")
    p.add_argument("--cwd", default=".")
    p.add_argument("--id", default="")
    p.add_argument("--ts", default="2026-09-28T10:00:00.000Z")
    p.add_argument("--title", default="")
    p.add_argument("--prompt", default="")
    p.add_argument("--answer", default="")
    p.add_argument("--subagent", action="store_true")
    p.add_argument("--garbage", action="store_true")
    p.add_argument("--instructions", default="")
    p.add_argument("--covered", action="append")
    p.add_argument("--excluded", action="append")
    p.add_argument("--runlog-date", dest="runlog_date", default="")
    a = p.parse_args()
    if a.kind in EXT:
        vscode_ext(a, a.kind)
    else:
        {"claude": claude, "codex": codex, "gemini": gemini, "aider": aider, "history": history, "runlog": runlog}[a.kind](a)


if __name__ == "__main__":
    main()
