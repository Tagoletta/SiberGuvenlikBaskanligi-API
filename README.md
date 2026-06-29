# SGBList — siberguvenlik.gov.tr blocklist generator

Fetches the full address index from `https://siberguvenlik.gov.tr/api/address/index`,
keeps a database of every record with its original date, and regenerates
time-windowed blocklists on every run.

**Runs entirely on GitHub Actions — no server needed.** A scheduled workflow
fetches the data hourly and commits the refreshed lists back to the repo, so your
firewall can pull them straight from raw GitHub URLs. A Docker setup is also
included for optional self-hosting, but it is not required.

## Output files (in `data/`)

Domains and IPs are kept in **separate** files:

| Window | Domains | IPs |
| ------ | ------- | --- |
| All time | `full-domains.txt` | `full-ips.txt` |
| Last 30 days | `days-30-domains.txt` | `days-30-ips.txt` |
| Last 60 days | `days-60-domains.txt` | `days-60-ips.txt` |
| Last 90 days | `days-90-domains.txt` | `days-90-ips.txt` |
| Last 120 days | `days-120-domains.txt` | `days-120-ips.txt` |

Each file is **one bare domain or IP per line** — no quotes, no surrounding
whitespace, LF line endings — sorted (domains alphabetically, IPs numerically)
for clean diffs. Point your firewall (pfSense / OPNsense / MikroTik / ipset, etc.)
at whichever files you need. (`database.jsonl` and `_state.json` are internal
bookkeeping; the firewall should ignore them.)

`data/database.jsonl` is the source of truth (id, url, type, date). The `.txt`
lists are **derived from it plus the current clock on every run**, so ageing is
automatic: a record that turns 31 days old drops out of `days-30-*` but is still
present in `days-60-*`, `days-90-*`, `days-120-*` and `full-*`. No entry is ever
lost from the wider windows.

## How it decides what to do

* **First run** (no `full-*` lists yet): state is wiped and a **full crawl** of
  every page begins, with a randomised `MIN_DELAY..MAX_DELAY` pause between pages
  so the API is not hammered. The crawl is resumable and checkpointed. The GitHub
  Actions workflow is set to **5–12 s/page** (≈2 days to seed everything); the
  code/Docker default is the more conservative **10–50 s**.
* **After the full crawl completes**: each run does a fast **incremental** update
  — only the newest pages are fetched until a record we already have is reached —
  then the lists are regenerated. The workflow runs this **once per hour**.
* **Periodically (every `FULL_RESYNC_DAYS`, default 7)**: instead of an
  incremental update, a fresh full crawl runs to detect entries the source has
  **removed** (see below).

## Removals (delisting)

The incremental update only ever adds; it cannot see that the source dropped an
entry. To catch removals, every `FULL_RESYNC_DAYS` (default **7**) the fetcher
re-crawls the whole index. Each record is stamped with the pass that last saw it,
and when a full pass finishes, any record **not** seen during it is treated as
removed at the source:

* it is deleted from the database, so it disappears from **all** lists
  (`full-*` and every `days-*` window) on the next regeneration, and
* it is appended to **`data/removed.log`** — one tab-separated line per removal:

  ```
  2026-06-08T17:34:38	REMOVED	removed-x.com	type=domain	id=3	added=2026-06-01 10:00:00
  ```

Set `FULL_RESYNC_DAYS=0` to disable periodic re-syncs (removals then won't be
detected). `removed.log` is append-only history; the firewall ignores it.

> ⚠️ The index has ~475k records (~23,760 pages), **including historical /
> backdated entries** — the full crawl walks every page to the end, so nothing
> old is missed. On GitHub Actions this happens automatically across many runs:
> each run crawls for up to ~5 h, commits its progress, and the next run resumes
> where it left off until the crawl is complete. At the configured 5–12 s/page the
> initial seed takes **~2 days**; after that, every hourly run is just a quick
> incremental update.

## User-Agent

Requests use an ordinary browser User-Agent:

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36
```

Override it with the `USER_AGENT` environment variable (in `update-lists.yml` or
`docker-compose.yml`).

## Optional: self-host with Docker

Not needed if you use GitHub Actions. Provided for running on your own server.

```bash
docker compose up -d --build
docker compose logs -f          # watch progress
```

Lists appear under `./data`. Override pacing/behaviour via environment variables
in `docker-compose.yml`:

| Variable | Default | Meaning |
| -------- | ------- | ------- |
| `MIN_DELAY` / `MAX_DELAY` | `10` / `50` | seconds between pages during the full crawl |
| `INC_MIN_DELAY` / `INC_MAX_DELAY` | `3` / `10` | seconds between pages during incremental |
| `TIME_BUDGET_SECONDS` | `3300` | checkpoint the full crawl after this long |
| `FULL_RESYNC_DAYS` | `7` | re-crawl everything this often to detect removals (0 = off) |
| `INCREMENTAL_MAX_PAGES` | `200` | safety cap for the incremental update |
| `DATA_DIR` | `/data` | output directory |
| `USER_AGENT` | (above) | request User-Agent |

To re-crawl from scratch, just empty `full-domains.txt` and `full-ips.txt` (or
delete the contents of `data/`): the next run detects empty full lists, wipes
state and starts a fresh full crawl.

## GitHub Actions (the main way this runs)

**`.github/workflows/update-lists.yml`** runs every hour, executes the fetcher
against the committed `data/` state, and commits the refreshed lists back to the
repo. The first runs perform the resumable full crawl (~5 h budget per run); once
it is complete, each hourly run is a fast incremental update.

Your firewall can then consume the lists directly, e.g.:

```
https://raw.githubusercontent.com/<owner>/<repo>/main/data/days-30-domains.txt
https://raw.githubusercontent.com/<owner>/<repo>/main/data/full-ips.txt
```

> 💡 **Make the repo public.** GitHub Actions is unlimited & free for public
> repos; the multi-day initial crawl would otherwise burn through a private
> repo's monthly Actions minutes. Public also makes the raw list URLs easy for a
> firewall to fetch. Scheduled workflows are paused after 60 days of repo
> inactivity, but the hourly bot commits count as activity, so it stays alive.

## Local run (no Docker)

```bash
pip install -r scraper/requirements.txt
DATA_DIR=data python scraper/fetch.py
```
