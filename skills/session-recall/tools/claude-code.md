# Claude Code

**Status:** verified 2026-10-02 against Claude Code 2.1.287 on macOS. Windows: experimental.

In the commands below, `<projects>` is `HOME/.claude/projects` (on Windows `HOME\.claude\projects`), `<folder>` is one project folder inside it, and `<file>` is one session file. Use the form that matches the shell your command tool runs (SKILL.md rule 4). The Windows PowerShell forms also work in PowerShell 7 on any OS.

## Locations
- macOS / Linux: `HOME/.claude/projects/`
- Windows: `HOME\.claude\projects\` (HOME is `%USERPROFILE%` unless `--home` is given)
- If `--home` is not given and the environment variable `CLAUDE_CONFIG_DIR` is set, use `<CLAUDE_CONFIG_DIR>/projects/` instead.

## Layout
- **One folder per working directory.** The folder name is the absolute path with every character that is not `A-Z`, `a-z` or `0-9` replaced by `-`:
  - `/Users/me/.superset/worktrees/app` becomes `-Users-me--superset-worktrees-app`
  - `C:\Users\me\app` becomes `C--Users-me-app`
- **Long names are cut.** If the encoded name is longer than 200 characters, Claude Code keeps only the first 200 and appends `-<hash>`.
- **A session** is `<folder>/<session-id>.jsonl`, directly inside the folder.
- **Subagent transcripts** are `<folder>/<session-id>/subagents/agent-*.jsonl` (records have `"isSidechain":true`). They are part of the parent session. Never list them as separate sessions.
- **`<folder>/memory/`** is auto-memory, not a session. Ignore it.

## Match to project
1. **Encode the known paths.** Encode every known path (SKILL.md Step 1) with the rule above, and keep only its first 200 characters. Candidate folders are those whose name **starts with** one of these encoded prefixes. Paths inside a known path (subfolders) also start with that prefix.
2. **Print each session's `cwd`, and nothing else**, for every session file directly inside the candidate folders:
   - macOS / Linux: `for f in "<folder>"/*.jsonl; do printf '%s ' "$f"; head -n 50 "$f" | grep -o -m1 '"cwd":"[^"]*"'; done`
   - Windows PowerShell: `Get-ChildItem -LiteralPath '<folder>' -Filter *.jsonl | ForEach-Object { $m = Select-String -LiteralPath $_.FullName -Pattern '"cwd":"([^"]*)"' -List; "$($_.FullName) $($m.Matches[0].Groups[1].Value)" }`
3. **Decide.** A session belongs to the project if its `cwd` equals a known path or is inside one (SKILL.md rules 5 and 6). This check removes prefix collisions (`app` vs `app-old`) and confirms folders whose names were cut.

## List sessions
- **ID:** the file name without `.jsonl`. It equals the `sessionId` field.
- **Started:** the first `timestamp` value:
  - macOS / Linux: `head -n 50 "<file>" | grep -o -m1 '"timestamp":"[^"]*"'`
  - Windows PowerShell: `(Select-String -LiteralPath '<file>' -Pattern '"timestamp":"([^"]*)"' -List).Matches[0].Groups[1].Value`
- **Title:** the last `aiTitle` value:
  - macOS / Linux: `grep -o '"aiTitle":"[^"]*"' "<file>" | tail -n 1`
  - Windows PowerShell: `(Select-String -LiteralPath '<file>' -Pattern '"aiTitle":"([^"]*)"' | Select-Object -Last 1).Matches[0].Groups[1].Value`

  If that prints nothing, use the first user prompt cut to 70 characters: the first line of the Read extraction, cut to 300 characters.

## Estimate
Count the characters the Read extraction would return, without printing them. Estimated tokens ≈ characters ÷ 4. Run one command for all chosen-to-list files, not one per session. List each file path in quotes.
- macOS / Linux: `for f in "<file 1>" "<file 2>"; do printf '%s ' "$f"; grep -h -E '"type":"(user|assistant)"' "$f" | grep -v -E '"tool_result"|"type":"thinking"|"isMeta":true' | sed -E '/"type":"tool_use"/ s/"(content|old_string|new_string|new_source)":"([^"\\]|\\.)*"/"\1":"[omitted]"/g' | cut -c1-3000 | wc -c; done`
- Windows PowerShell: `foreach ($f in '<file 1>', '<file 2>') { $n = (Select-String -LiteralPath $f -Pattern '"type":"(user|assistant)"' | Where-Object { $_.Line -notmatch '"tool_result"|"type":"thinking"|"isMeta":true' } | ForEach-Object { $l = $_.Line; if ($l -match '"type":"tool_use"') { $l = $l -replace '"(content|old_string|new_string|new_source)":"(?:[^"\\]|\\.)*"', '"$1":"[omitted]"' }; $l.Substring(0, [Math]::Min(3000, $l.Length)) } | Measure-Object -Character).Characters; "$f $n" }`

## Read
The file is JSONL with compact JSON, one record per line, and each content block is usually its own record. **Do not open the file directly.** Run this extraction, which drops tool output, reasoning, meta records and the bodies of file writes and edits before the text reaches you:
- macOS / Linux: `grep -h -E '"type":"(user|assistant)"' "<file>" | grep -v -E '"tool_result"|"type":"thinking"|"isMeta":true' | sed -E '/"type":"tool_use"/ s/"(content|old_string|new_string|new_source)":"([^"\\]|\\.)*"/"\1":"[omitted]"/g' | cut -c1-3000`
- Windows PowerShell: `Select-String -LiteralPath '<file>' -Pattern '"type":"(user|assistant)"' | Where-Object { $_.Line -notmatch '"tool_result"|"type":"thinking"|"isMeta":true' } | ForEach-Object { $l = $_.Line; if ($l -match '"type":"tool_use"') { $l = $l -replace '"(content|old_string|new_string|new_source)":"(?:[^"\\]|\\.)*"', '"$1":"[omitted]"' }; $l.Substring(0, [Math]::Min(3000, $l.Length)) }`

From the lines this returns:
- **`"type":"user"` with `text` content:** the user's prompts.
- **`"type":"assistant"` with `text` blocks:** the replies.
- **`"type":"assistant"` with `tool_use` blocks:** keep only `name` and `input.file_path` / `input.command`, for "Files touched" and "Notable".

If the output is very long, page through it: `| sed -n '1,400p'`, then `'401,800p'`, and so on (PowerShell: `| Select-Object -First 400`, then `-Skip 400 -First 400`).

## Format check
Passes if both the `cwd` command in "Match to project" and this `sessionId` command print a value. Only those fields are printed, never the records.
- macOS / Linux: `head -n 50 "<file>" | grep -o -m1 '"sessionId":"[^"]*"'`
- Windows PowerShell: `(Select-String -LiteralPath '<file>' -Pattern '"sessionId":"([^"]*)"' -List).Matches[0].Groups[1].Value`
