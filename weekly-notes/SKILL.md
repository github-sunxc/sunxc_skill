---
name: weekly-notes
description: >-
  Use to record weekly work notes and generate a weekly report for the Thursday
  noon team meeting. Trigger on: "记笔记", "记录工作", "记到笔记", "写周报",
  "weekly report", "周报", "本周工作", "note this", "log my work", or any request
  to save work progress or produce the weekly summary.
---

# Weekly Notes and Report Helper

Help the user keep weekly work notes and turn them into a short English weekly
report for the Thursday noon team meeting.

## CRITICAL: These Are the User's Private Notes — Do Not Alter Without Consent

The notes belong to the user and are private. You MUST NOT change them without
explicit permission.

- **Append only, and only when explicitly asked.** Never edit, rewrite,
  reword, reorder, summarize-in-place, delete, rename, or overwrite ANY existing
  note content or note file.
- **Never auto-save.** Do not write to the notes during normal conversation.
  Only append when the user clearly asks (see Rule 1).
- If you believe an existing entry is wrong or should change, **ask the user
  first** and only proceed after they explicitly agree. Describe exactly what
  you would change and wait for a clear "yes".
- When in doubt, do nothing to the notes and ask.

## Storage: Shared Remote Server (works from any machine)

Notes are NOT stored locally. They live on a shared server so the user can work
from many different machines and always reach the same notes.

- Server: `10.193.108.180`, user `build`, password `build`
- Notes dir: `/home/build/share_write/maximus/weekly_report`
- IMPORTANT: NEVER touch any file on that server outside this notes dir.

All access goes through the helper script (uses paramiko over SFTP, so no
sshpass / no interactive password prompt is needed):

```
/home/maximus/.opencode/skills/weekly-notes/notes_remote.py
```

### Helper commands

```bash
# Print current week's note file path
python3 /home/maximus/.opencode/skills/weekly-notes/notes_remote.py path

# Test connection + list existing note files
python3 /home/maximus/.opencode/skills/weekly-notes/notes_remote.py test

# Show current week's note content (says so if none yet)
python3 /home/maximus/.opencode/skills/weekly-notes/notes_remote.py show

# List all week_*.md files
python3 /home/maximus/.opencode/skills/weekly-notes/notes_remote.py list

# Append ONE timestamped work item (auto-creates the week file if missing)
python3 /home/maximus/.opencode/skills/weekly-notes/notes_remote.py append "fixed RPMSG power key report"
```

The script computes the week automatically and picks the right file. The
append command creates the week's file with a header the first time.

## Week Boundary Definition

A "week" runs from **Thursday 15:00** to the **next Thursday 15:00**.
File name is `week_YYYY-MM-DD.md` where the date is the Thursday the week began.
This logic is built into the helper script - do not compute it by hand.

## Rule 1: Recording a Work Item (ONLY when explicitly asked)

Only write to notes when the user CLEARLY asks (e.g. "记一下", "记到笔记里",
"log this"). Do NOT auto-save during normal chat.

When asked:
1. Run the `append` command. The script checks if this week's file exists,
   creates it if not, and appends the entry with a timestamp - all in one step.
2. Confirm to the user in Chinese what was recorded.

NOTES MUST BE DETAILED (this is different from the report). The note is the raw
record and should capture enough that a report can be written from it later, and
that the user can recall exactly what happened. For each work item include, when
known:
   - WHAT was done (the concrete action/change)
   - WHERE (project name, change/bug number, file, module, server, path)
   - WHY / the problem it solves (root cause, symptom)
   - HOW it was solved (key steps, commands, options, decisions)
   - RESULT / status (done, submitted, pending, blocked, next step)
   - any numbers, IDs, error messages, or config values that matter

Use a multi-line entry when one line is not enough. The `append` command puts a
timestamp on the first line. To create sub-bullets, put a literal `\n` (backslash
+ n) in the text you pass; the helper converts each `\n` into a real newline in
the note file. Example:

```bash
python3 .../notes_remote.py append "fixed X problem\n- root cause: ...\n- fix: ...\n- result: done"
```

Prefer detail over brevity for notes.


## Rule 2: Do Not Delete History

Never delete, rename, or overwrite older `week_*.md` files. The helper only
appends to the current week's file or creates a new one. Each week = new file.

## Rule 3: Writing the Weekly Report (when asked for 周报 / weekly report)

1. Run `show` to read the current week's note content. Do NOT modify the file.
2. Produce an English weekly report that is:
   - SHORT and clear
   - Simple, common words (CET-6 level, NOT GRE/TOEFL vocabulary)
   - Bullet points, one short sentence per task, past tense
3. Suggested structure:
   ```
   Weekly Report (<week start> to <week end>)

   Done this week:
   - ...
   - ...

   Next week plan:
   - ...   (only if the notes mention plans; otherwise omit)
   ```
4. Show the report to the user in chat. Do not write it back to the note file
   unless asked.

### English Style Rules for the Report

- Simple words: "fix", "add", "check", "test", "update", "finish".
- Avoid: "leverage", "facilitate", "endeavor", "utilize" (say "use").
- Keep each bullet to one short sentence.
- Use technical terms as-is (RPMSG, kernel, CTS, driver).

## Notes

- If the connection fails, tell the user the shared server may be down or the
  credentials/path changed; do not fall back to local storage silently.
- Credentials are stored in the helper script. If they change, update
  `notes_remote.py` (HOST/USER/PASSWORD/NOTES_DIR at the top).
