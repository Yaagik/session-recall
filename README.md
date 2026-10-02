# session-recall

**Never lose your AI coding history when you switch laptops.**

Claude Code, Codex, Gemini CLI and other AI coding tools save your chats only on the laptop where you had them. Get a new laptop and that history is gone.

`session-recall` fixes this. It reads your project's past AI sessions and writes the useful parts into your project as Markdown files: what was built, decisions and why, bugs fixed, and what to do next. You commit those files like any other code. On your new laptop, clone the project and your AI agent can read where you left off.

---

## How to use it (3 steps)

### 1. Install (one time)

In **Claude Code**, type:

```
/plugin marketplace add Yaagik/session-recall
/plugin install session-recall@session-recall
```

Then restart Claude Code.

**Using Codex, Gemini CLI or another agent?** Copy the folder `skills/session-recall` into that agent's skills folder:

| Agent | Copy the folder into |
|---|---|
| Claude Code (without the plugin) | `~/.claude/skills/` |
| Agents that read the shared skills folder (for example through Superset) | `~/.agents/skills/` |
| Codex CLI (not yet verified) | `~/.codex/skills/` |
| Gemini CLI (not yet verified) | `~/.gemini/skills/` |

### 2. Run it inside your project

```
/session-recall
```

It will:
1. **Ask once** if it's OK for your AI agent to read your saved sessions.
2. **Show a list** of this project's sessions, each with an estimated token cost:
   ```
     #  Date        Tool         Title                          Est. tokens
     1  2026-10-02  Claude Code  Fix login redirect bug          ~10,000
     2  2026-09-28  Codex CLI    Add Stripe webhook handler      ~3,000
   Which should I document?  all · 1,3 · all except 2 · none · later
   ```
3. **Let you choose.** Only the sessions you pick are written down. Sessions you don't pick can be skipped forever, and only their ID is remembered.
4. **Show the total cost and wait for your "yes"** before reading anything:
   ```
   Estimated token use for 2 sessions: ~13,000 input + ~3,000 output tokens
   Proceed? (yes / no / choose fewer)
   ```
5. **Write two files** in your project:
   - `docs/ai-history/HISTORY.md`: the big picture, kept up to date. It starts with a short "Context for the next agent" section.
   - `docs/ai-history/sessions/<date>.md`: a short summary of each session from this run.

### 3. Commit the files

```
git add docs/ai-history
git commit -m "Save AI session history"
```

**On your new laptop:** clone the project and tell your agent *"read docs/ai-history/HISTORY.md and continue"*.

> **Tip:** run `/session-recall` every week or so, and always before you switch laptops. Claude Code and Gemini CLI **delete sessions older than 30 days** by default. The skill shows you how to raise that limit.

---

## Options

| Command | What it does |
|---|---|
| `/session-recall` | Show new sessions and let you choose |
| `/session-recall --all` | Choose all new sessions (you still see the list and approve the cost) |
| `/session-recall --since 2026-09-01` | Only sessions from this date on |
| `/session-recall --include claude-code:<id>` | Bring back a session you skipped earlier |
| `/session-recall --home /Volumes/Backup/Users/me` | Read from a backup of your old laptop (for example Time Machine) |
| `/session-recall --home … --path /Users/oldname/code/app` | Same, when the project lived at a different path on the old laptop |

Running it again only looks at **new** sessions. Sessions already saved are never read again.

---

## What it supports

| Tool | Status |
|---|---|
| Claude Code | ✅ tested on macOS |
| Codex CLI, Gemini CLI, opencode, Aider, Cline, Roo Code | 🧪 tested on sample data; not yet checked against real installs |
| Cursor, Windsurf, GitHub Copilot Chat, Continue | Planned |

Works on **macOS** and **Windows**. Git worktrees, including Superset and Conductor, are handled: sessions from all worktrees of a repo are found. Sessions from worktrees that were already deleted are listed separately and only saved if you pick them.

---

## Privacy and cost

- **Nothing is uploaded by this skill.** It only reads files on your computer and writes Markdown into your project.
- **Your AI agent's provider sees the text of the sessions you choose,** because the agent summarizes them. For example, running it in Codex sends that text to OpenAI. You're asked once per project before anything is read.
- **Tokens are kept low.**
  - Before your "yes", only titles, dates and sizes are read.
  - After it, only your prompts and the agent's replies are read. Tool output, hidden reasoning, file contents and other projects' sessions are left out.
  - On a real session this was about **94% fewer tokens** than reading the whole file.
- **Secrets are removed.** API keys, tokens, passwords, private keys and `.env` values are written as `[REDACTED]`.
- **It never commits for you.** Look over `docs/ai-history/` before committing, especially in public repos.

---

## For contributors

```bash
claude plugin validate .claude-plugin/plugin.json      # check the plugin files
python3 -m unittest tests/test_commands.py -v          # free: every shell command, bash + PowerShell (set PWSH=/path/to/pwsh)
bash tests/e2e.sh                                      # real run with real git (~$0.50 on your Claude account)
claude plugin eval . --scaffold --trust-plugin --allow-tools Bash Write Edit --runs 1 --no-publish   # 20 behaviour tests (~$6)
```

- **How it's built:** the skill is plain instructions in `skills/session-recall/SKILL.md`, with one reference file per tool in `skills/session-recall/tools/`.
- **How the tests work:** behaviour tests live in `evals/`. Each builds fake tool history with `evals/_fixtures/make_home.py` and runs the skill on it.
- **Inspecting a real session file:** `python3 evals/_fixtures/shape.py <file>` shows its structure without showing its content.

MIT License.
