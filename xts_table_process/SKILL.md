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
2. **API base URL**: The system is deployed at a fixed address — `http://androidtools.agents.nxp.com/xts-tracker/`. Use this as the default `{BASE}` for all API calls. Only ask the user if this address is unreachable or the user indicates it has moved.
3. **Always ask the user for their identity** before any write:
   - `changed_by` — recorded in change history for status/detail edits.
   - For owner changes and imports: ask for the **admin password** (these are admin-only).
4. **Owner and status columns have database-level foreign key constraints** (`PRAGMA foreign_keys = ON`). Invalid values are rejected at the DB layer. The skill does not need to independently validate owner/status — the DB is the final arbiter.
5. **IMPORT WRITES THE DATABASE — TREAT IT AS DANGEROUS.** An import mutates the live release database and is not trivially undoable. A wrong suite/board/release/source can pollute real data or need a full restore from backup. **Before EVERY import, STOP and get the user's explicit confirmation of all four:**
   - **Suite** (CTS / VTS / CTS-on-GSI / GTS / STS)
   - **Board** (the tracker board name it will write to, after mapping)
   - **Database / release** (which `imx_android-*` release it writes into)
   - **Report source** (which report file / URL it reads from)

   Present these as a table and wait for a "yes" before calling the import API. Never chain imports without this gate. This confirmation is mandatory even when the user says "just import" — echo the four back and confirm.


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

Additional owners not in the table above (no English name mapping, match by xTS name directly): `Liu Xuegang`, `Bao Xiahong`, `Zhou Ming`, `Xu Mao`, `Li Jian`.

**Departed owners (do NOT assign new work to them):** `Wang Hui` (handed over to `Sun Dandan`), `Zhang Bo` (handed over to `Zhai He`). They still appear in historical data, so they remain valid for **querying/filtering** existing cases, but must NEVER be used as the target of a new owner assignment. If the user asks to assign work to a departed owner, use the handover target instead and tell the user.

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

## User import habits (Maximus)

Observed defaults for this user's "import / 升级xts" requests — use these as
sensible starting assumptions, but STILL confirm the four points (HARD RULE 5)
before writing:

- **Report source is usually Source A** — `http://10.52.9.140/xTS_Report/`,
  release-RC directory layout, import the `need_check.txt` per (board, suite).
- **Target release is usually the latest** — e.g. `imx_android-17.0_1.0.0`
  (from the `android-17.0.0_1.0.0-rc1/` report dir). Verify via `GET /api/releases`.
- **"检查有没有新报告" ≠ import.** The user often first asks to CHECK for new
  reports without importing. In that case: list the report server, compare every
  (mapped board, suite) against `meta.imported`, and REPORT the new ones. Do NOT
  import until the user explicitly says to.
- **Authoritative "already imported" state is `meta.imported`**, never memory or a
  prior chat log. Always re-fetch `GET /api/{release}/meta` and diff against the
  report server. Some pairs may already be imported from earlier sessions.
- **Board-name mapping matters** — apply the Source A table (`8MQ_WEVK`→`8MQWEVK`,
  `8ULP_9x9`→`8ULP9`, `937_FRDM`→`937FRDM`) and confirm each with the user.
- **Admin password** is required for import; the user supplies it (do not assume).
- After importing, always deliver the dedup-then-assign reminder (Operation D step 3).


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

`{BASE}` defaults to `http://androidtools.agents.nxp.com/xts-tracker/` (fixed deployment). Only override if the user says it has moved.

### Read (no auth)
- `GET {BASE}/api/releases` — list release names (newest first).
- `GET {BASE}/api/{release}/meta` — `{boards, owners, active_owners, statuses, rc_versions, locked}`. Use `statuses` as the valid **status whitelist**; `owners` is the full list (incl. historical/departed) for **filtering**; `active_owners` is the list valid for **new assignment**; `rc_versions` are the RC values present in this release.
- `GET {BASE}/api/{release}/failures?suite=&board=&status=&owner=&rc_version=&keyword=&page=&page_size=` — search/list cases. `page_size` max 200. `board`/`status`/`owner`/`rc_version` accept **multiple values** (repeat the param, e.g. `board=8QM&board=8MP`) and are OR-ed within each field. `keyword` matches inside `case_name`. To filter empty owner/status use the literal value `__none__`.
- `GET {BASE}/api/{release}/command?suite=&board=&status=&owner=&rc_version=&keyword=` — generate the xTS runner `--include-filter` command for the matched cases (suite required). Returns `{command, count}`.
- `GET {BASE}/api/{release}/stats/need-check` — per-suite Need-Check counts by owner.

### User-level write (no password, needs `changed_by`)
- `PATCH {BASE}/api/{release}/failures/{id}` with JSON `{"status": "...", "detail": "...", "changed_by": "<name>"}`.
  - Only `status` and `detail` may be edited. Records change history.

### Admin-level write (header `x-admin-password: <password>`)
- `PATCH {BASE}/api/admin/{release}/failures/{id}` with JSON containing any of `{"owner","status","detail","rc_version"}`.
  - This is the **only** way to change `owner`.
- `POST {BASE}/api/admin/{release}/import` — multipart form: `suite` (string), `board` (string), `file` (HTML, Excel, or `need_check.txt`). The `.txt` format is `module<TAB>case_name` per line.
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
   - Resolve `suite` (CTS/VTS/CTS-on-GSI/GTS/STS) and `board` (map to a name in `meta.boards`).
   - **MANDATORY confirmation gate (HARD RULE 5):** before calling the import API,
     STOP and show the user a table of the four facts and wait for explicit "yes":

     | Field | Value |
     |---|---|
     | Suite | e.g. CTS |
     | Board (tracker name) | e.g. 952_19x19 |
     | Database / release | e.g. imx_android-17.0_1.0.0 |
     | Report source | e.g. http://10.52.9.140/.../952_19x19/CTS/need_check.txt |

     Import writes the live DB and is not trivially undoable — never skip this even
     if the user said "just import". Echo the four back and confirm first.
   - After confirmation: `POST {BASE}/api/admin/{release}/import` as multipart form.
   - Report `added`/`updated` counts.
3. **After all imports are done**, deliver this mandatory reminder:

   > ⚠️ Import 完成。接下来你**必须去 web 前端按顺序执行**：
   > 1. **去重 (Deduplicate)** — 在 Admin 页面点 Deduplicate
   > 2. **Assign** — 在 Admin 页面点 Assign
   >
   > 这两步必须按顺序做，不可跳过。AI 无法执行这两个操作。

   Do NOT attempt to call the dedup or assign API endpoints. These operations require interactive review in the web UI.

## Operation E — "升级xts": auto-import new reports from a report server (Admin)

Trigger: the user says **"升级xts"** / "upgrade xts" / "导入最新报告", or gives report URLs
directly. The test team publishes xTS results to report servers; this operation finds
reports not yet imported into the tracker and imports only those.

**CONFIRMATION GATE (mandatory).** This operation is destructive (writes to the tracker
DB). At EVERY step below you MUST stop and get the user's explicit confirmation before
proceeding to the next step — never chain steps automatically. In particular, confirm:
the report source, the resolved release, EVERY board-name mapping, and the final list of
(suite, board) pairs to import. If any board mapping is ambiguous, STOP and ask; never guess.

### Report sources

There are two known report-server layouts. Detect which one the user's URL/base matches,
or ask the user which source to use.

**Source A — `http://10.52.9.140/xTS_Report/`** (release-RC directory layout):
```
http://10.52.9.140/xTS_Report/
  android-<major>.0.0_<x.y.z>-rc<n>/     <- one directory per release+RC
    <BOARD>/                             <- board directory (report-server naming)
      <SUITE>/                           <- CTS / CTS-on-GSI / GTS / STS / VTS
        need_check.txt                   <- the file to import (TAB: module<TAB>case_name)
        need_checks.xml                  <- same list, SubPlan XML (do NOT import)
        *_test_results.xls               <- raw CTS result (do NOT import)
```
Import **`need_check.txt`** (natively supported; `module<TAB>case_name`). Do NOT import `.xls`/`.xml`.

**Source B — `http://10.193.108.180/share_write/xts_autorun/`** (suite/board/timestamp layout):
```
http://10.193.108.180/share_write/xts_autorun/
  <suite>/                               <- vts / cts / cts-on-gsi / gts / sts (lowercase)
    <board_dir>/                         <- e.g. evk_8mp, mek_8qm, frdm_937 (see mapping)
      <YYYY.MM.DD_HH.MM.SS>/             <- timestamped run; use the newest per board
        test_result_failures_suite.html <- the file to import (standard CTS/VTS HTML report)
```
Import **`test_result_failures_suite.html`** (standard HTML report; natively parsed).
The user often pastes the full URLs directly — one per (board, run).

### Step E1 — locate the reports

- **Source A**: list `http://10.52.9.140/xTS_Report/`; among `android-<number>...` dirs pick
  the latest (highest android version, then x.y.z, then rc, or newest mtime).
- **Source B**: use the URLs the user pasted, or list
  `http://10.193.108.180/share_write/xts_autorun/<suite>/<board_dir>/` and take the
  newest timestamp directory per board.
- Tell the user which reports were selected and **get confirmation**.

### Step E2 — map the report to a tracker release

- **Source A**: dir `android-<M>.0.0_<x.y.z>-rc<n>` → release `imx_android-<M>.0_<x.y.z>`.
  Example: `android-16.0.0_2.0.0-rc3` → `imx_android-16.0_2.0.0`.
- **Source B**: the report has no release in its path; read the HTML `Suite / Build`
  field (e.g. `17_r1` = Android 17) to infer the android version, or **ask the user**
  which release to import into.
This is a convention, not a strict rule. **Always verify against `GET {BASE}/api/releases`**;
if no exact match, list candidates and ask the user.

### Step E3 — map board directory names to tracker board names

Report-server board names differ from the tracker's `meta.boards`. **The mapping is NOT
guessable from the name** (e.g. `evk_8ulp` → `8ULP9`, not `8ULP`). Resolve each report
board using the table below, confirm it exists in `GET {BASE}/api/{release}/meta` →
`boards`, and **have the user confirm every mapping**. If a report board is not in the
table or is ambiguous, STOP and ask — never guess.

**Source A (`10.52.9.140`):**

Confirmed tracker board names (from `meta.boards`, release `imx_android-17.0_1.0.0`):
`8QM`, `8QXP`, `8MM`, `8MN`, `8MQWEVK`, `8MP`, `8ULP`, `8ULP9`, `937FRDM`,
`95_19x19`, `95_15x15_FRDM`, `952_19x19`. Always re-check `meta.boards` for the
target release, since the set can differ per release.

| Report-server dir | Tracker board | Note |
|---|---|---|
| `8MQ_WEVK` | `8MQWEVK` | drop underscore |
| `8ULP_9x9` | `8ULP9` | NOT `8ULP` — different board |
| `937_FRDM` | `937FRDM` | drop underscore |
| `8ULP` | `8ULP` | same name (distinct from `8ULP9`) |
| `8QM`, `8QXP`, `8MM`, `8MP`, `8MN`, `95_15x15_FRDM`, `95_19x19`, `952_19x19`, `952_15x15`, `943`, ... | same name | verify against `meta.boards` |

**Watch out:** `8ULP_9x9` → `8ULP9` and plain `8ULP` → `8ULP` are TWO DIFFERENT tracker
boards. Do not conflate them.

**Source B (`10.193.108.180`, `evk_`/`mek_`/`frdm_` prefixed):**

| Report-server dir | Tracker board |
|---|---|
| `mek_8qm` | `8QM` |
| `mek_8qxp` | `8QXP` |
| `evk_8mm` | `8MM` |
| `evk_8mn` | `8MN` |
| `evk_8mp` | `8MP` |
| `evk_8mq` | `8MQWEVK` |
| `evk_8ulp` | `8ULP9` |
| `evk_95` | `95_19x19` |
| `evk_952` | `952_19x19` |
| `frdm_952` | `952_15x15_FRDM` |
| `frdm_937` | `937FRDM` |

If a report board maps to a name NOT in `meta.boards` for that release, SKIP it and
report it to the user (import would fail with `board not defined for this release`).

### Step E4 — determine which (suite, board) are new

1. `GET {BASE}/api/{release}/meta` → `imported` is `{suite: [board, ...]}` already imported.
2. For each report's (mapped board, suite): if it is NOT already in `meta.imported[suite]`,
   mark it for import. Skip already-imported pairs unless the user asks to re-import.
3. **Present the final import list to the user and get confirmation before writing.**

### Step E5 — import each confirmed report

For each confirmed (suite, board): download the report file (Source A: `need_check.txt`;
Source B: `test_result_failures_suite.html`), then
`POST {BASE}/api/admin/{release}/import` as multipart form with `suite`, mapped `board`,
and the file. Report `added`/`updated` per pair, and a summary of skipped pairs.

### Step E6 — mandatory post-import reminder

After all imports, deliver the SAME reminder as Operation D (dedup then assign in the
web UI). Deduplicate and Assign stay manual — do NOT call those APIs.

## Failure handling

- **404** → wrong release name or wrong base URL; re-confirm with user.
- **400 `invalid status`** → status not in whitelist; show `meta.statuses`.
- **400 `FOREIGN KEY constraint failed`** → owner or status value does not exist in the database; show `meta.owners` or `meta.statuses` accordingly.
- **401/403** → wrong or missing admin password.
- **423 `database is locked`** → release is locked for maintenance; tell user to unlock in Admin or wait. (This `db_lock` flag only blocks user-level edits; admin ops ignore it by design.)
- **500 `database disk image is malformed` during import (or any operation)** → the release DB is CORRUPTED. STOP all writes immediately and tell the user. Historically this was caused by the backup thread racing writes; it is fixed in the backend (per-release write lock + checkpoint-before-backup), but if it ever recurs: do NOT keep importing. Recovery is done OUT-OF-BAND by the maintainer (stop the service, `sqlite3 <db> .recover | sqlite3 <new.db>`, verify `PRAGMA integrity_check` = ok and row counts of `failures`/`suite_board_reports` match, then swap the file while the service is stopped). Never attempt DB-file recovery through this skill's API-only workflow.
- **Never fall back to editing `.db` directly to work around an API error.**
