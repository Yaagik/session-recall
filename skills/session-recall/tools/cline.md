# Cline

**Status:** experimental (from third-party documentation; not yet verified on a real install).

## Locations
Check all of these. Each `tasks/<task-id>/` folder is one session.
- `HOME/.cline/data/tasks/` (Cline 4.x and newer). The same layout on Windows under `HOME\.cline\data\tasks\`.
- `APPSUPPORT/<Editor>/User/globalStorage/saoudrizwan.claude-dev/tasks/` for every `<Editor>` in SKILL.md Step 4:
  - macOS: `HOME/Library/Application Support/<Editor>/...`
  - Windows: `%APPDATA%\<Editor>\...`

Each task folder contains `api_conversation_history.json` and `ui_messages.json`, and sometimes `task_metadata.json`.

## Match to project
Print only the working directory of each task, in one batched command. Never open `api_conversation_history.json` or a tool-wide index such as `state/taskHistory.json` before approval: these hold other projects' text.
- macOS / Linux: `for d in "<storage>/tasks"/*/; do printf '%s ' "$d"; grep -o -m1 'Current Working Directory ([^)]*)' "$d/api_conversation_history.json"; done`
- Windows PowerShell: `Get-ChildItem -LiteralPath '<storage>\tasks' -Directory | ForEach-Object { $m = Select-String -LiteralPath (Join-Path $_.FullName 'api_conversation_history.json') -Pattern 'Current Working Directory \(([^)]*)\)' -List; "$($_.FullName) $($m.Matches[0].Groups[1].Value)" }`

The session belongs to the project if that path equals a known path or is inside one.

## List sessions
- **ID:** the task folder name (a millisecond Unix timestamp).
- **Started:** that timestamp converted to a date.
- **Title:** only for tasks that matched, cut to 70 characters. If it prints nothing, use "(untitled task)".
  - macOS / Linux: `grep -o -m1 '<task>[^<]*' "<task folder>/api_conversation_history.json" | cut -c1-90`
  - Windows PowerShell: `(Select-String -LiteralPath '<task folder>\api_conversation_history.json' -Pattern '<task>([^<]*)' -List).Matches[0].Groups[1].Value`
- **Size:** the total size of the task folder.

## Read
`api_conversation_history.json` is a JSON array of `{ "role", "content" }`.
- **User messages:** keep `text` blocks after removing `<environment_details>…</environment_details>` sections and the `<task>` tags. Skip `tool_result` blocks.
- **Assistant messages:** keep `text` blocks. From `tool_use` blocks, keep the tool name and input path or command.
  - Older versions embed tool calls as tags in the text (`<write_to_file><path>…</path>`, `<execute_command><command>…</command>`). Take the path or command from these tags and drop their body.

## Estimate
An upper bound: the size of `api_conversation_history.json` ÷ 4, from `wc -c` (macOS/Linux) or `(Get-Item <file>).Length` (PowerShell). The file also holds tool results and environment details, which you skip while reading, so actual use is usually lower. Read the file in chunks.

## Format check
Passes if `head -c 1 "<file>"` prints `[` and `grep -c '"role"' "<file>"` prints at least 1, where `<file>` is `api_conversation_history.json`. Don't load the file to check it.
