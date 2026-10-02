# Aider

**Status:** experimental (format from Aider's docs and its history-file convention; not yet verified on a real install).

## Locations
- `.aider.chat.history.md` at the root of each known path (repo root and each worktree). The same on macOS and Windows; `--home` does not affect it.
- A custom location can be set with the `AIDER_CHAT_HISTORY_FILE` environment variable or `chat-history-file:` in `.aider.conf.yml`. Check both if present.

## Match to project
The file is inside the project, so every session in it belongs to the project.

## List sessions
- Each line `# aider chat started at YYYY-MM-DD HH:MM:SS` starts a new session.
- **ID:** that timestamp with the space replaced by `T`, e.g. `2026-09-25T11:00:00`, giving the key `aider:2026-09-25T11:00:00`.
- **Started:** the same timestamp.
- **Title:** the first line starting with `#### ` in that session.
- **Size:** the bytes in that session's section.

## Read
- **Your prompts:** lines starting with `#### `.
- **Aider's own output:** lines starting with `> `. Skip them, except that `Applied edit to <file>` gives "Files touched" and `Commit <hash> <message>` goes in "Notable".
- **Everything else:** the assistant's replies.

## Estimate
Find the session boundaries without reading content: `grep -n '^# aider chat started at' .aider.chat.history.md` (PowerShell: `Select-String -Path .aider.chat.history.md -Pattern '^# aider chat started at'`). A session's estimated tokens ≈ (its line count × 60) ÷ 4. Read only the chosen sessions' line ranges (offset/limit), not the whole file.

## Format check
Passes if the file contains at least one line starting with `# aider chat started at`.
