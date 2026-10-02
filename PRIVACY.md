# Privacy Policy: session-recall

_Last updated: 2 October 2026_

`session-recall` is a Claude Code plugin and Agent Skill. It runs entirely on your own computer, inside the AI coding agent you already use. Its author operates no server and receives no data from it.

## What it reads
- **The saved session history of AI coding tools on your computer,** and only for the project you run it in. Examples: Claude Code's `~/.claude/projects/` and Codex CLI's `~/.codex/sessions/`.
- **Before you approve anything,** it reads only metadata: file paths, session IDs, dates and titles.
- **After you approve,** it reads the prompts and replies of the sessions **you choose**.
- **It never opens credential or account files,** for example `~/.claude/.credentials.json`, `~/.claude.json`, `~/.codex/auth.json`, `~/.gemini/oauth_creds.json` or editor secret storage.

Session history can incidentally contain personal data, such as a name or email address that appeared in a conversation. The skill reads it only as part of the session text and never stores it (see below).

## What it stores
- **Two kinds of Markdown file, in your project:** a summary in `docs/ai-history/HISTORY.md`, and one run log per run in `docs/ai-history/sessions/<date>.md`.
- **No personal data is stored.** Names of people, email addresses, phone numbers and postal addresses are never written. People are referred to by role ("the user", "a teammate"), or the value is written as `[REDACTED]`.
- **Secrets are removed:** API keys, tokens, passwords, private keys, connection strings with credentials and `.env` values are written as `[REDACTED]`.
- **Excluded sessions:** for sessions you choose not to document, only the session ID is recorded, so you aren't asked about them again.
- **You stay in control:** the plugin never commits these files. You decide whether to commit, change or delete them.

## What it sends
- **The plugin makes no network requests** and sends nothing to its author or to any third party.
- **Your agent's provider processes the text you approve,** as with anything else you ask that agent to do: Anthropic for Claude Code, or OpenAI if you run the skill in Codex. That processing follows your agreement with that provider. On first use in each project, the skill asks for your permission before reading any session.

## Retention
The plugin retains nothing. Its only output is the Markdown files in your own repository, and they stay until you delete them.

## Children
This plugin is a developer tool and is not intended for users under 18.

## Contact
For privacy questions, open an issue in this plugin's GitHub repository (`Yaagik/session-recall`).
