---
name: xts_table_process
description: Operate the xTS Failure Tracker web system via its HTTP API. Batch-edit case status/detail, change owner, query/search cases, or import reports. Trigger on phrases like "把这些case的status改成", "改一下owner", "mark these cases", "batch update", "change owner to", "查一下这个case", "search cases", "import report", "导入报告", "xTS table", "failure tracker".
license: MIT
compatibility: opencode
metadata:
  author: Maximus
  category: tooling
---

# xTS Table Process

Operate the xTS Failure Tracker system through its web API. The system stores per-release SQLite databases of xTS (CTS/VTS/CTS-on-GSI/GTS/STS) failure cases; each case has `suite`, `module`, `case_name`, `owner`, `status`, `detail`, `rc_version`.

## HARD RULES (never violate)

1. **NEVER touch the database file directly.** All reads and writes MUST go through the web HTTP API. Do NOT open `.db` files, do NOT run `sqlite3`, do NOT run SQL. Never fall back to editing `.db` directly to "get around" an API error.
2. **Always ask the user for the API base URL** at the start of any task. The deployment address changes and may move servers, so never hardcode or assume it. Store the URL for the rest of the session.
3. **Always ask the user for their identity** before any write:
   - `changed_by` — recorded in change history for status/detail edits.
   - For owner changes and imports: ask for the **admin password** (these are admin-only).
4. **Owner and status columns have database-level foreign key constraints** (`PRAGMA foreign_keys = ON`). Invalid values are rejected at the DB layer. The skill does not need to independently validate owner/status — the DB is the final arbiter.

## Owner name mapping table

The system uses surname-first pinyin names ("xTS names") as the canonical owner identifiers. Team members also go by English names and Chinese names. The skill supports **fuzzy matching**: the user can refer to a person by any name form (English first name, surname, Chinese name, etc.), and the skill resolves it to the xTS canonical name using the table below.

**If a fuzzy input matches >1 person (e.g. "Sun" matches Sun Xiachen AND Sun Dandan, "Wang" matches 3 people), STOP and list the candidates for the user to choose. Never guess.**

| English Name | xTS Canonical Name | Notes |
|---|---|---|
| Maximus Sun | Sun Xiachen | 孙夏晨 |
| Chloe Sun | Sun Dandan | |
| Elven Wang | Wang Haoran | 王浩然 |
| Ji Luo | Luo Ji | |
| Jessie Hao | Hao Juan | 郝娟 |
| Faqiang Zhu | Zhu Faqiang | |
| Zhai He | Zhai He | |
| Anle Pan | Pan Anle | |
| Zhipeng Wang | Wang Zhipeng | |
| Junmeng Li | Li Junmeng | |
| Jindong Yue | Yue Jindong | |
| Yunjie Jia | Jia Yunjie | |
| Hui Fang | Fang Hui | |

Additional owners not in the table above (no English name mapping, match by xTS name directly): `Liu Xuegang`, `Bao Xiahong`, `Zhang Bo`, `Zhou Ming`, `Xu Mao`, `Li Jian`, `Wang Hui`.

Examples of fuzzy resolution:
- "我是 BAO" → `Bao Xiahong` (only one Bao)
- "Elven" → `Wang Haoran`
- "Sun" → STOP: "Sun Xiachen or Sun Dandan?"
- "Wang" → STOP: "Wang Haoran, Wang Zhipeng, or Wang Hui?"

## Step 0 — Gather connection context (every task)

Ask the user (unless already provided this session):
1. **API base URL** (required, no default).
2. **Identity**: `changed_by` name (use fuzzy matching above); for owner/import operations, also the **admin password**.

Verify reachability: `GET {BASE}/api/releases` — should return a list.

## Step 1 — Resolve the release

- If the user names a release, use it.
- Otherwise **default to the latest**: `GET {BASE}/api/releases` returns a list (newest-first); use the **first** element. Tell the user which release was auto-selected.
- Remember the release for follow-up operations until the user changes it.

## Case matching rules

All case lookups follow these rules:

1. **User must specify `suite`** before any search/edit. A search without suite is rejected — ask the user which suite.
2. Search via `GET {BASE}/api/{release}/failures?suite={suite}&keyword={case_name}&page_size=200`.
   - The `keyword` parameter is a **substring match** on `case_name`.
   - If the user also provides `module`, further filter the results by `module` match.
3. After filtering:
   - **Exactly 1 result** → proceed (write directly for edits).
   - **0 results** → report "case not found" to the user. Do NOT fall back to fuzzy/partial search.
   - **>1 results** → STOP, list all matched cases for the user to clarify or provide a more complete case_name. Do NOT guess which one.
4. The user must provide accurate, untruncated `case_name` for edits, unless they explicitly request fuzzy/partial search. Parameter suffixes like `[intent=...]` or `[IncludeRunOnPrimaryUser]` are part of the case_name.

## API reference

`{BASE}` is provided by the user.

### Read (no auth)
- `GET {BASE}/api/releases` — list release names (newest first).
- `GET {BASE}/api/{release}/meta` — `{boards, owners, statuses, locked}`. Use `statuses` as the valid **status whitelist** and `owners` as the valid **owner list**.
- `GET {BASE}/api/{release}/failures?suite=&board=&status=&owner=&keyword=&page=&page_size=` — search/list cases. `page_size` max 200. `keyword` matches inside `case_name`. To filter empty owner/status use the literal value `__none__`.
- `GET {BASE}/api/{release}/stats/need-check` — per-suite Need-Check counts by owner.

### User-level write (no password, needs `changed_by`)
- `PATCH {BASE}/api/{release}/failures/{id}` with JSON `{"status": "...", "detail": "...", "changed_by": "<name>"}`.
  - Only `status` and `detail` may be edited. Records change history.

### Admin-level write (header `x-admin-password: <password>`)
- `PATCH {BASE}/api/admin/{release}/failures/{id}` with JSON containing any of `{"owner","status","detail","rc_version"}`.
  - This is the **only** way to change `owner`.
- `POST {BASE}/api/admin/{release}/import` — multipart form: `suite` (string), `board` (string), `file` (HTML or Excel report file).
- `GET {BASE}/api/admin/verify` — check admin credentials.

## Operation A — Batch edit status / detail

1. Gather `changed_by`, target `status`, and `detail` text from the user.
2. **Status validation**: `GET {BASE}/api/{release}/meta` → get `statuses` list. Match the user's status **case-insensitively** against this whitelist:
   - Unique match → use the whitelist's exact casing (e.g. `aosp known issue` → `AOSP Known Issue`).
   - No match → report error and show the full whitelist. Do NOT guess semantically.
3. For each case_name the user provides, find its `id` per the **Case matching rules** above.
4. For each matched id: `PATCH {BASE}/api/{release}/failures/{id}` with `{status, detail, changed_by}`.
5. Report results: `N/N succeeded`. If any case was not found, list those separately.

## Operation B — Change owner (Admin)

1. Confirm admin password with the user.
2. Resolve the target owner name using the **Owner name mapping table** (fuzzy match). If >1 candidate, list and ask.
3. Find each case `id` per the **Case matching rules**.
4. For each id: `PATCH {BASE}/api/admin/{release}/failures/{id}` with `{"owner": "<resolved xTS name>"}` and header `x-admin-password`.
5. Report `N/N`.

## Operation C — Query / search cases

Use `GET {BASE}/api/{release}/failures` with `suite`, `board`, `status`, `owner`, `keyword`, `page`/`page_size` (≤200). Summarise: id, case_name, module, owner, status. Use `__none__` for empty owner/status filters.

## Operation D — Import report (Admin)

1. Confirm admin password.
2. For each report file the user provides:
   - Ask/confirm `suite` (e.g. CTS/VTS/CTS-on-GSI/GTS/STS) and `board` (must be one of `meta.boards`).
   - `POST {BASE}/api/admin/{release}/import` as multipart form.
   - Report `added`/`updated` counts.
3. **After all imports are done**, deliver this mandatory reminder:

   > ⚠️ Import 完成。接下来你**必须去 web 前端按顺序执行**：
   > 1. **去重 (Deduplicate)** — 在 Admin 页面点 Deduplicate
   > 2. **Assign** — 在 Admin 页面点 Assign
   >
   > 这两步必须按顺序做，不可跳过。AI 无法执行这两个操作。

   Do NOT attempt to call the dedup or assign API endpoints. These operations require interactive review in the web UI.

## Failure handling

- **404** → wrong release name or wrong base URL; re-confirm with user.
- **400 `invalid status`** → status not in whitelist; show `meta.statuses`.
- **400 `FOREIGN KEY constraint failed`** → owner or status value does not exist in the database; show `meta.owners` or `meta.statuses` accordingly.
- **401/403** → wrong or missing admin password.
- **423 `database is locked`** → release is locked for maintenance; tell user to unlock in Admin or wait.
- **Never fall back to editing `.db` directly to work around an API error.**
