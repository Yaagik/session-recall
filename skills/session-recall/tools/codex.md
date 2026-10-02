# Codex CLI

**Status:** experimental (from third-party documentation; not yet verified on a real install).

In the commands below, `<sessions>` is `HOME/.codex/sessions` (on Windows `HOME\.codex\sessions`) and `<file>` is one rollout file. Use the form that matches the shell your command tool runs (SKILL.md rule 4).

## Locations
- macOS / Linux: `HOME/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<id>.jsonl`
- Windows: `HOME\.codex\sessions\YYYY\MM\DD\rollout-<timestamp>-<id>.jsonl`
- If `--home` is not given and the environment variable `CODEX_HOME` is set, use `<CODEX_HOME>/sessions/` instead.
- **Compressed files.** Some versions may compress files as `.jsonl.zst`. For those, replace the file argument of the first command in a pipeline with `zstd -dc "<file>" |` in front. Never write a decompressed copy to disk. If `zstd` is missing, report "Codex sessions are compressed and zstd is not installed" and skip Codex.

## Match to project
The first line of each rollout file is `{"type":"session_meta","payload":{"id":…,"cwd":…,"timestamp":…,…}}`. It can also carry another project's full instructions, so **never print the line**. Print only `cwd` per file, in one batched command. With `--since`, scan only the `YYYY/MM/DD` folders on or after that date.
- macOS / Linux: `find "<sessions>" -name 'rollout-*.jsonl' | while read -r f; do printf '%s ' "$f"; head -n 1 "$f" | grep -o -m1 '"cwd":"[^"]*"'; done`
- Windows PowerShell: `Get-ChildItem -LiteralPath '<sessions>' -Recurse -Filter 'rollout-*.jsonl' | ForEach-Object { $m = (Get-Content -LiteralPath $_.FullName -TotalCount 1) | Select-String -Pattern '"cwd":"([^"]*)"'; if ($m) { "$($_.FullName) $($m.Matches[0].Groups[1].Value)" } }`

A session belongs to the project if its `cwd` equals a known path or is inside one (SKILL.md rules 5 and 6). If many sessions are printed, you may append a filter for the known paths: `| grep -F '<known path>'` or `| Select-String -SimpleMatch '<known path>'`. Write Windows paths with doubled backslashes there, as they appear in JSON.

## List sessions
- **ID:** the first `"id"` value in the first line, which is `payload.id`:
  - macOS / Linux: `head -n 1 "<file>" | grep -o -m1 '"id":"[^"]*"'`
  - Windows PowerShell: `((Get-Content -LiteralPath '<file>' -TotalCount 1) | Select-String -Pattern '"id":"([^"]*)"').Matches[0].Groups[1].Value`
- **Started:** the date in the folder path (`YYYY/MM/DD`) and the time in the file name.
- **Title:** the first real user message, cut to 70 characters. Run the Extraction below and take the first `"text"` value:
  - macOS / Linux: append `| grep '"role":"user"' | grep -o -m1 '"text":"[^"]*"' | cut -c1-80`
  - Windows PowerShell: append `| Where-Object { $_ -match '"role":"user"' } | Select-Object -First 1 | ForEach-Object { ([regex]'"text":"([^"]*)"').Match($_).Groups[1].Value }`

## Estimate
Count the characters of the Extraction output without printing it. Estimated tokens ≈ characters ÷ 4. Use one loop over all listed files:
- macOS / Linux: append `| wc -c` to the Extraction, in a `for f in "<file 1>" "<file 2>"; do printf '%s ' "$f"; …; done` loop.
- Windows PowerShell: wrap it as `foreach ($f in '<file 1>', '<file 2>') { $n = (<Extraction with $f> | Measure-Object -Character).Characters; "$f $n" }`.

## Extraction (use this instead of opening the file)
- macOS / Linux: `grep -h '"type":"response_item"' "<file>" | grep -E '"type":"(message|function_call)"' | grep -v -E 'environment_context|user_instructions|# AGENTS.md' | cut -c1-3000`
- Windows PowerShell: `Select-String -LiteralPath '<file>' -Pattern '"type":"response_item"' | Where-Object { $_.Line -match '"type":"(message|function_call)"' -and $_.Line -notmatch 'environment_context|user_instructions|# AGENTS.md' } | ForEach-Object { $_.Line.Substring(0, [Math]::Min(3000, $_.Line.Length)) }`

## Read
Apply these rules to the Extraction output:
- **Keep:** `"type":"response_item"` records whose `payload.type` is `"message"`:
  - `role: "user"`: the `input_text` items (injected context is already filtered out);
  - `role: "assistant"`: the `output_text` items.
- **`payload.type: "function_call"`:** keep only `name` and the command or path from `arguments`, for "Notable" and "Files touched".
- **Already excluded by the Extraction:** `function_call_output` (tool output), `reasoning`, and `event_msg` records, which duplicate the messages.

## Format check
Passes if this prints `"type":"session_meta"` and the Match command prints a `cwd` for the file:
- macOS / Linux: `head -n 1 "<file>" | grep -o -m1 '"type":"session_meta"'`
- Windows PowerShell: `((Get-Content -LiteralPath '<file>' -TotalCount 1) | Select-String -Pattern '"type":"session_meta"').Matches[0].Value`
