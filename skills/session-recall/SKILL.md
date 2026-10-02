---
name: session-recall
description: Use when the user wants to save, summarize, back up or carry over the AI coding-agent session history of the current project (Claude Code, Codex CLI, Gemini CLI, opencode, Aider, Cline, Roo Code) into Markdown inside the repo - for example before switching laptops, or when they say "recall my sessions", "document my AI history" or run /session-recall.
---

# session-recall

Turn this project's AI session history, from every supported tool on this machine, into Markdown in `docs/ai-history/`, so it travels with the repo to any machine (macOS or Windows).

**Arguments** (all optional, any order):
- `--since YYYY-MM-DD`: only consider sessions that started on or after this date.
- `--all`: choose every candidate session without asking which (Step 7a still shows the list). The token estimate is still shown and must be approved.
- `--include <tool-key>:<id>`: offer a previously excluded session again. Repeatable.
- `--home <path>`: read tool history from this folder instead of the user's home folder (for example a backup of an old laptop's home folder). Relative paths are relative to the current folder.
- `--path <old project path>`: also count sessions recorded under this path as this project's, for example where the project lived on the old laptop (`/Users/olduser/code/app` or `C:\Users\old\app`). Repeatable.

If the user's message already answers a question this skill asks (privacy acceptance, which sessions to document, whether exclusions are permanent, approval of the token estimate), use that answer and do not ask again.

## Rules that always apply

1. Read tool history; never modify any tool's files or settings. Write only inside `docs/ai-history/`. Never commit. Everything stays on this computer.
   - **Never open credential or account files**, even though some sit next to session history. These include:
     - `~/.claude/.credentials.json`, `~/.claude.json`, the macOS Keychain;
     - `~/.codex/auth.json`;
     - `~/.gemini/oauth_creds.json`, `~/.gemini/google_accounts.json`, `.env` files;
     - `~/.local/share/opencode/auth.json`;
     - editors' `state.vscdb` and secret storage.

     Read only the session paths named in the tool files.
2. Apply the redaction rules (Step 9) to everything you write and to your replies.
3. For an excluded session, the only thing ever written is its key `<tool-key>:<id>` in "Excluded sessions": no title, no content.
4. Prefer your built-in file tools (glob/search/read) over shell commands. When a command is needed, use the form that matches **the shell your command tool actually runs**. On Windows, Claude Code's Bash tool runs Git Bash, so use the POSIX (`macOS / Linux`) form there. Use the `Windows PowerShell` form only when your tool runs PowerShell. If unsure, run `echo $0` or `$PSVersionTable` once to find out.
5. Path comparison: compare paths after resolving symlinks (macOS `/var/...` and `/private/var/...` are the same folder). On Windows, compare case-insensitively and treat `\` and `/` as equal. Paths read from JSON have their backslashes doubled (`C:\\Users\\me\\app`), so un-double them before comparing. Keep both the as-given and the resolved form of every known path, and try both when matching.
6. A session belongs to the project when its recorded working directory **equals a known path or is inside one** (a subfolder). Sharing a prefix is not enough: `/code/app-old` is not inside `/code/app`.
7. **Spend as few tokens as possible.** The user pays for every token you read.
   - **Before approval** (Steps 1–7), every command may print only metadata: paths, IDs, timestamps, `cwd` values, counts, and titles of *this project's* sessions (cut to about 70 characters). Extract single fields with `grep -o` / `Select-String` and its `Matches`. Never print whole lines, records or files, and never open a session file or a tool-wide index (for example Cline's `taskHistory.json`) with your file reader. Other projects' session text must never reach you.
   - **When reading a session** (Step 8), use the tool file's **Read** extraction. It filters out tool output, reasoning and injected context *before* the text reaches you. Never read a session file in full when an extraction command exists.
   - **Cap long text:** each user prompt at about 1,000 characters and each assistant reply at about 2,000. Never re-read sessions already covered.
   - **No subagents.** Do not summarize through subagents. Each one adds thousands of tokens of overhead that the estimate doesn't include.

## Step 1: Identify the project

- `ROOT`: output of `git rev-parse --show-toplevel`. Remote: `git remote get-url origin` (may not exist; that's fine).
- `KNOWN_PATHS`: `ROOT` plus every path from the `worktree <path>` lines of `git worktree list --porcelain`. This covers worktree managers such as Superset and Conductor. Also add:
  - the current folder as your shell reports it (`$PWD`, PowerShell `(Get-Location).Path`). This may be a symlinked (logical) form of `ROOT`.
  - on macOS, for every known path starting with `/private/`, the same path without the `/private` prefix (`/private/tmp/x` is also recorded as `/tmp/x`, `/private/var/...` as `/var/...`).
  - every `--path` value.
- `WORKTREE_PARENTS`: the parent folder of every linked worktree (every `KNOWN_PATHS` entry from `git worktree list` except the main one). Used in Step 4 to find sessions of deleted worktrees.
- **If the `git` command is not available but a `.git` folder exists** (common on Windows machines without git on PATH):
  - `ROOT` is the folder containing `.git`.
  - **If `.git` is a file** (you are inside a linked worktree), it holds `gitdir: <main repo>/.git/worktrees/<name>`. The main repo's `.git` folder is two levels above that path, and the main repo's folder is its parent. Add the main repo's folder to `KNOWN_PATHS`, and use its `.git` folder for the next two bullets.
  - Read the worktree paths from `<.git folder>/worktrees/*/gitdir`. Each such file holds `<worktree path>/.git`, so drop the trailing `/.git`.
  - Read the remote from the `url =` line under `[remote "origin"]` in `.git/config`.
- **Never treat the user's real home folder as `ROOT`.** That is the `HOME` / `%USERPROFILE%` environment variable, not `--home`. If the repo found (by `git` or the fallback) is the home folder itself, which happens with dotfiles repos, treat the folder as not a git repo, as in the next bullet. This keeps `docs/ai-history/` from being written into the home folder.
- If this is not a git repo: `ROOT` and `KNOWN_PATHS` are the current folder only. Tell the user that worktrees can't be detected outside a git repo.
- `HOME`: `--home` if given, otherwise the user's home folder.
- `APPSUPPORT`:
  - macOS: `HOME/Library/Application Support`.
  - Windows: `%APPDATA%`, or `HOME\AppData\Roaming` when `--home` is given.
  - Linux: `HOME/.config`.

## Step 2: Load prior state

If `docs/ai-history/HISTORY.md` exists, read it:
- `COVERED`: every key in the "Session ID" column of "Sessions covered".
- `EXCLUDED`: every key listed under "Excluded sessions".
- `PRIVACY_ACCEPTED`: true if the file has a line starting `> Privacy notice accepted`.

For each `--include` key: if it is in `EXCLUDED`, remove it from `EXCLUDED` (it will also be removed from the file in Step 11). Otherwise report "`<key>` is not in the excluded list" and ignore it.

## Step 3: Privacy notice (only if not PRIVACY_ACCEPTED)

Tell the user:

> session-recall will read your saved AI sessions for this project. The text of the sessions you choose will be read by this agent's model provider to be summarized, and the summary will be written to `docs/ai-history/` in this repo. Nothing else leaves this computer. Continue? (yes / no)

Wait for the answer unless the user already gave it. On "no", stop and write nothing.

## Step 4: Discover sessions

Check each tool below. A tool is **found** if any of its detect locations exists. `<Editor>` means each of: `Code`, `Code - Insiders`, `Cursor`, `Windsurf`, `VSCodium`.

| Tool key | Display name | Detect (any exists) | Tool file |
|---|---|---|---|
| `claude-code` | Claude Code | `HOME/.claude/projects` | `tools/claude-code.md` |
| `codex` | Codex CLI | `HOME/.codex/sessions` | `tools/codex.md` |
| `gemini-cli` | Gemini CLI | `HOME/.gemini/tmp` | `tools/gemini-cli.md` |
| `opencode` | opencode | `HOME/.local/share/opencode` | `tools/opencode.md` |
| `aider` | Aider | `.aider.chat.history.md` in any known path | `tools/aider.md` |
| `cline` | Cline | `HOME/.cline/data`, or `APPSUPPORT/<Editor>/User/globalStorage/saoudrizwan.claude-dev` | `tools/cline.md` |
| `roo-code` | Roo Code | `APPSUPPORT/<Editor>/User/globalStorage/rooveterinaryinc.roo-cline` | `tools/roo-code.md` |

For each **found** tool:
1. Read its tool file (paths are relative to this SKILL.md).
2. Run its **Format check** on one or two of its files. If the check fails, record the tool as *format mismatch*, skip it, and continue with the other tools.
3. **Match.** Use **Match to project** and the **ID** and **Started** commands of **List sessions** to find this project's sessions. Each one gets a key `<tool-key>:<id>`.
4. **Filter before anything else (Step 6).** Drop sessions whose key is in `COVERED` or `EXCLUDED`, and with `--since` those started before that date. Covered and excluded sessions get no title, no estimate and no further command.
5. **Build the candidates.** Only for the sessions that remain, add the display name, a title (from the tool's **Title** command, or the first user prompt cut to about 70 characters), the location and the **estimated input tokens** from the tool file's **Estimate** section. That section prints a character count, not content; tokens ≈ characters ÷ 4. Batch these commands: one command for all of a tool's remaining sessions, not one per session.

This finds every session still on disk, including sessions created before this skill was installed.

**Sessions of deleted worktrees.** Worktree managers delete a worktree after merging, but its sessions stay on disk.
- **What counts:** a session whose recorded working directory no longer exists *and* sits directly inside one of `WORKTREE_PARENTS` (for example `~/.superset/worktrees/<project>/<deleted-name>`) is a *possible* match.
- **In the list:** show these in a separate group headed "Possibly from deleted worktrees of this repo (confirm before documenting)".
- **Never chosen automatically:** not with `--all`, and not by answers such as `all` or `all except …`. Only document one when the user names it explicitly.

## Step 5: Retention warning (first run only, same condition as Step 3)

For each found tool that deletes old history automatically, tell the user once:
- **Claude Code:** deletes sessions older than `cleanupPeriodDays` days (default 30). To keep more, set e.g. `"cleanupPeriodDays": 3650` in `~/.claude/settings.json`.
- **Gemini CLI:** deletes sessions older than its session retention setting (default 30 days); see Gemini CLI's session-management docs.

Never change these settings yourself. Sessions these tools have already deleted cannot be recovered.

## Step 6: Filter

This is applied in Step 4, item 4, as soon as sessions are matched: candidates whose key is in `COVERED` or `EXCLUDED`, or that started before `--since`, are dropped.

If no candidates remain: reply "No new sessions to document." (plus the report lines for tools not found or skipped), write nothing, and stop. If `--home` was given and no session matched at all, the old machine probably used other paths. List up to 10 of the `cwd` values found under `--home`, paths only, and suggest re-running with `--path <one of them>`.

## Step 7: Let the user choose, then approve the token estimate

**7a. Choose.** Always show the candidates newest first (ties by tool key, then ID), numbered from 1. With `--all`, show the list without the final question and choose every listed session, except possible deleted-worktree sessions.

```
Found <N> sessions for this project not yet in AI history:

  #  Date        Tool         Title / first prompt                          Est. tokens
  1  2026-10-02  Claude Code  Session migration research                    ~10,000
  2  2026-09-28  Codex CLI    Add Stripe webhook handler                    ~3,000

Which should I document?  all · 1,3,5-9 · all except 2 · since <date> · none · later
```

Interpret the answer. Descriptions such as "the Stripe ones" or "skip the big ones" are allowed; if one is ambiguous, ask.
- **`later`:** document nothing, exclude nothing, write nothing, and stop.
- **Anything else:** the chosen sessions are the ones to document. Every candidate *not* chosen is to be excluded. Before excluding, confirm in one line: "Exclude <n> sessions permanently? (yes / ask me next time)", unless the user already said. "ask me next time" means they are not excluded.

**7b. Approve the token estimate (always when at least one session is chosen, also with `--all`).** If no session was chosen (for example the answer `none`), skip 7b: write only the confirmed exclusions (Step 11), report, and stop. Before reading any session content, show exactly these two lines, filling in only the numbers, and keep the `~` and the words `input` and `output`:

```
Estimated token use for <n> sessions: ~<IN> input + ~<OUT> output tokens (rough; actual use depends on your model and agent).
Proceed? (yes / no / choose fewer)
```

- `IN` is the sum of the chosen sessions' estimates, plus the size of an existing `HISTORY.md` ÷ 4, plus 3,000 (this skill and its tool files).
- `OUT` is 600 per session, plus the size of an existing `HISTORY.md` ÷ 4, plus 1,500.
- Round both to the nearest 1,000.

Wait for the answer unless the user already approved the estimate in their message.
- **"no":** stop. Write nothing, not even exclusions.
- **"choose fewer":** go back to 7a.

## Step 8: Read and summarize

Process the chosen sessions **oldest first**, so later sessions override earlier facts.

For each session, use the **Read** section of its tool file (rule 7):
- Run its extraction command, so that only the user's prompts, the agent's replies, the file paths touched and the notable commands reach you.
- Never load tool output, thinking/reasoning blocks or images.
- If the extraction output is very long, process it in chunks.

From each session, collect:
- **Goal, Outcome, Files touched, Notable** (for the run log).
- **Decisions with their reasons, what was built, bugs fixed and gotchas, open TODOs** (for HISTORY.md).

## Step 9: Redact

Never write any of these. Write `[REDACTED]` instead:
- API keys and tokens (`sk-…`, `ghp_…`, `github_pat_…`, `AKIA…`, `xox…-`, JWTs `eyJ…`)
- passwords
- private-key blocks
- connection strings that contain credentials
- the values in `.env` files

Do not copy long verbatim code or file contents: summarize, and name file paths. When in doubt, leave it out.

## Step 10: Write the run log

Write `docs/ai-history/sessions/<YYYY-MM-DD>.md` using today's local date. If that file exists, use `<YYYY-MM-DD>-2.md`, then `-3`, and so on. Never overwrite a run log. Skip this step if no session was chosen.

```markdown
# Sessions summarized on <YYYY-MM-DD>

## <Display name> · <session start date> · <tool-key>:<id> · "<title>"
- **Goal:** <what the user wanted>
- **Outcome:** <what was done or decided>
- **Files touched:** <paths, comma-separated, or "none">
- **Notable:** <errors hit, key commands, follow-ups, or "none">
```

One `##` section per documented session, oldest first.

## Step 11: Update HISTORY.md

Create `docs/ai-history/HISTORY.md` from this template if it doesn't exist. If it does exist, merge into it.

```markdown
# AI history: <repo folder name>
_Last updated <YYYY-MM-DD> · <number of rows in Sessions covered> sessions across <display names>_

> Privacy notice accepted on <YYYY-MM-DD>: session text is read by the agent's model provider.

## Context for the next agent
<5-10 lines: what this project is, its current state, and what to do next. Written so a fresh agent on a new machine can read only this section and continue.>

## Project overview & architecture
## Key decisions (and why)
- <YYYY-MM-DD> · <decision> because <reason> (<display name>)
## What's been built
## Bugs fixed & gotchas learned
## Open TODOs / next steps
## Sessions covered
| Date | Tool | Session ID | Title | Run log |
|------|------|-----------|-------|---------|
| <start date> | <display name> | <tool-key>:<id> | <title> | sessions/<run log file name> |

## Excluded sessions
<!-- IDs only. The user chose not to document these. Not offered again unless re-included with --include <id>. -->
- <tool-key>:<id>
```

Merge rules:
- Deduplicate items. Update outdated items instead of keeping both: for example, a TODO that a later session completed moves to "What's been built".
- Keep the date and tool on every item.
- Rewrite "Context for the next agent" to reflect the current state.
- **Keep every existing row in "Sessions covered"**, even if its session file isn't on this machine (it may come from another machine). Add a row for each newly documented session, and only after its summary is written.
- In "Excluded sessions": add newly excluded keys, and remove keys re-included with `--include`. Write `_None._` when the list is empty.
- Add the privacy line if it is missing and the user accepted in this run.
- Update the "Last updated" line.

If only exclusions changed (nothing documented), still update "Excluded sessions" and the privacy line.

## Step 12: Report

Reply in exactly this format. Keep each line's label word for word (`Not found on this machine:`, `Skipped (format looks different from what this skill expects; reference may be outdated):`, and so on), because users and scripts look for them. Omit lines that don't apply. Add any extra notes after the block.

```
session-recall: documented <N> sessions (<display name> <count>, ...).
- Not found on this machine: <display names>
- Skipped (format looks different from what this skill expects; reference may be outdated): <display names>
- Excluded this run: <count> (only their IDs were recorded)
- Tokens: estimated ~<IN> input + ~<OUT> output before the run (approved by you)
- Files written: <paths>
- Retention: <the Step 5 warning, first run only>
Review docs/ai-history/ before committing it, especially if this repo is public. I did not commit anything.
```
