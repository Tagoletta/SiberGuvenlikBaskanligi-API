from __future__ import annotations

import json
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = os.environ.get("BASE_URL", "https://siberguvenlik.gov.tr")
API_URL = f"{BASE_URL}/api/address/index"

USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
)

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
ALL_TYPES = ["domain", "url", "ip", "ip6", "ip6net"]
PER_PAGE = int(os.environ.get("PER_PAGE", "1000"))

MIN_DELAY = float(os.environ.get("MIN_DELAY", "5"))
MAX_DELAY = float(os.environ.get("MAX_DELAY", "12"))
INC_MIN_DELAY = float(os.environ.get("INC_MIN_DELAY", "2"))
INC_MAX_DELAY = float(os.environ.get("INC_MAX_DELAY", "6"))
TIME_BUDGET_SECONDS = float(os.environ.get("TIME_BUDGET_SECONDS", "18000"))
INCREMENTAL_MAX_PAGES = int(os.environ.get("INCREMENTAL_MAX_PAGES", "50"))
FULL_RESYNC_DAYS = float(os.environ.get("FULL_RESYNC_DAYS", "7"))
FORCE_FULL_RESYNC = os.environ.get("FORCE_FULL_RESYNC", "0") == "1"
SEED_COMPLETE_FRACTION = float(os.environ.get("SEED_COMPLETE_FRACTION", "0.8"))
WINDOWS = [30, 60, 90, 120]
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "30"))

DB_FILE = DATA_DIR / "database.jsonl"
STATE_FILE = DATA_DIR / "_state.json"
REMOVED_LOG = DATA_DIR / "removed.log"

EXIT_OK = 0
EXIT_CONTINUE = 10

_TYPE_SUFFIX = {
    "domain": "domains",
    "url": "urls",
    "ip": "ips",
    "ip6": "ip6",
    "ip6net": "ip6net",
}


def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


def fetch_page(session: requests.Session, addr_type: str, page: int) -> dict:
    resp = session.get(
        API_URL,
        params={"type": addr_type, "page": page, "per-page": PER_PAGE},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def load_db() -> dict[int, dict]:
    db: dict[int, dict] = {}
    if not DB_FILE.exists():
        return db
    with DB_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                db[int(rec["id"])] = rec
            except (ValueError, KeyError):
                continue
    return db


def save_db(db: dict[int, dict]) -> None:
    tmp = DB_FILE.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        for _id in sorted(db.keys()):
            rec = db[_id]
            out = {
                "id": rec["id"],
                "url": rec["url"],
                "type": rec.get("type", "domain"),
                "date": rec.get("date", ""),
            }
            if rec.get("p") is not None:
                out["p"] = rec["p"]
            fh.write(json.dumps(out, ensure_ascii=False) + "\n")
    tmp.replace(DB_FILE)


def store_records(db: dict[int, dict], models: list[dict], pass_id: int) -> int:
    new = 0
    for m in models:
        try:
            _id = int(m["id"])
        except (KeyError, ValueError, TypeError):
            continue
        if _id not in db:
            new += 1
        db[_id] = {
            "id": _id,
            "url": m.get("url", ""),
            "type": m.get("type", "domain"),
            "date": m.get("date", ""),
            "p": pass_id,
        }
    return new


def log_removals(records: list[dict]) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    lines = [
        f"{ts}\tREMOVED\t{rec.get('url', '')}\ttype={rec.get('type', '')}\t"
        f"id={rec.get('id')}\tadded={rec.get('date', '')}"
        for rec in records
    ]
    with REMOVED_LOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def sweep_removed(db: dict[int, dict], pass_id: int) -> int:
    stale = [
        rec
        for rec in db.values()
        if rec.get("p") is not None and int(rec["p"]) < pass_id
    ]
    if not stale:
        return 0
    log_removals(stale)
    for rec in stale:
        db.pop(int(rec["id"]), None)
    print(f"[removed] {len(stale)} delisted -> {REMOVED_LOG.name}")
    return len(stale)


def _empty_type_state() -> dict:
    return {
        "full_crawl_complete": False,
        "next_page": 1,
        "total_pages": None,
        "last_max_id": None,
        "total_count": None,
    }


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {
        "pass_id": 1,
        "last_run": None,
        "last_full_completed": None,
        "types": {t: _empty_type_state() for t in ALL_TYPES},
    }


def save_state(state: dict) -> None:
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    tmp.replace(STATE_FILE)


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _ip_sort_key(s: str):
    parts = s.split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return (s,)


def write_list(path: Path, entries: set[str], addr_type: str) -> None:
    ordered = (
        sorted(entries, key=_ip_sort_key)
        if addr_type == "ip"
        else sorted(entries, key=str.lower)
    )
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        "\n".join(ordered) + ("\n" if ordered else ""),
        encoding="utf-8",
        newline="\n",
    )
    tmp.replace(path)


def generate_lists(db: dict[int, dict]) -> dict[str, int]:
    now = datetime.now()
    cutoffs = {w: now - timedelta(days=w) for w in WINDOWS}

    full: dict[str, set[str]] = {t: set() for t in ALL_TYPES}
    windowed: dict[int, dict[str, set[str]]] = {
        w: {t: set() for t in ALL_TYPES} for w in WINDOWS
    }

    for rec in db.values():
        entry = (rec.get("url") or "").strip()
        if not entry:
            continue
        rtype = rec.get("type", "domain")
        if rtype not in full:
            rtype = "domain"

        full[rtype].add(entry)
        dt = parse_date(rec.get("date", ""))
        if dt is None:
            continue
        for w, cutoff in cutoffs.items():
            if dt >= cutoff:
                windowed[w][rtype].add(entry)

    stats: dict[str, int] = {}
    for t in ALL_TYPES:
        suffix = _TYPE_SUFFIX[t]
        write_list(DATA_DIR / f"full-{suffix}.txt", full[t], t)
        stats[f"full-{suffix}"] = len(full[t])
        for w in WINDOWS:
            write_list(DATA_DIR / f"days-{w}-{suffix}.txt", windowed[w][t], t)
            stats[f"days-{w}-{suffix}"] = len(windowed[w][t])

    return stats


def _full_list_paths() -> list[Path]:
    return [DATA_DIR / f"full-{_TYPE_SUFFIX[t]}.txt" for t in ALL_TYPES]


def is_first_run() -> bool:
    return all((not p.exists()) or p.stat().st_size == 0 for p in _full_list_paths())


def reset_everything() -> None:
    print("[reset] starting fresh full crawl")
    for p in list(DATA_DIR.glob("*.txt")) + list(DATA_DIR.glob("*.tmp")):
        try:
            p.unlink()
        except FileNotFoundError:
            pass
    for p in [DB_FILE, STATE_FILE]:
        try:
            p.unlink()
        except FileNotFoundError:
            pass


def sleep_between(lo: float, hi: float) -> None:
    delay = random.uniform(lo, hi)
    print(f"  sleeping {delay:.1f}s", flush=True)
    time.sleep(delay)


def all_types_complete(state: dict) -> bool:
    return all(
        state["types"].get(t, _empty_type_state()).get("full_crawl_complete", False)
        for t in ALL_TYPES
    )


def full_resync_due(state: dict) -> bool:
    if FULL_RESYNC_DAYS <= 0:
        return False
    last = state.get("last_full_completed")
    if not last:
        return False
    try:
        last_dt = datetime.fromisoformat(last)
    except ValueError:
        return False
    return datetime.now() - last_dt >= timedelta(days=FULL_RESYNC_DAYS)


def run_full_crawl(session, db, state, start_time: float) -> int:
    pass_id = int(state["pass_id"])

    for addr_type in ALL_TYPES:
        ts = state["types"].setdefault(addr_type, _empty_type_state())
        if ts.get("full_crawl_complete"):
            continue

        page = int(ts.get("next_page") or 1)
        print(f"[full] type={addr_type} page={page} pass={pass_id}")

        while True:
            if TIME_BUDGET_SECONDS and (time.monotonic() - start_time) >= TIME_BUDGET_SECONDS:
                print(f"[full] budget reached at type={addr_type} page={page}")
                ts["next_page"] = page
                save_db(db)
                save_state(state)
                generate_lists(db)
                return EXIT_CONTINUE

            try:
                data = fetch_page(session, addr_type, page)
            except requests.RequestException as exc:
                print(f"[full] type={addr_type} page={page} error: {exc}")
                ts["next_page"] = page
                save_db(db)
                save_state(state)
                generate_lists(db)
                return EXIT_CONTINUE

            total_pages = data.get("pageCount")
            if total_pages:
                ts["total_pages"] = total_pages
            total_count = data.get("totalCount")
            if total_count:
                ts["total_count"] = total_count

            models = data.get("models", [])
            total_pages_known = ts.get("total_pages")
            reached_end = bool(total_pages_known) and page >= total_pages_known

            if not models and total_pages_known and not reached_end:
                print(f"[full] type={addr_type} page={page} empty mid-crawl, retrying next run")
                ts["next_page"] = page
                save_db(db)
                save_state(state)
                generate_lists(db)
                return EXIT_CONTINUE

            new = store_records(db, models, pass_id)
            print(
                f"[full] type={addr_type} {page}/{ts.get('total_pages')} "
                f"records={len(models)} new={new} total={len(db)}",
                flush=True,
            )

            if reached_end or not models:
                ts["full_crawl_complete"] = True
                ts["next_page"] = 1
                ts["last_max_id"] = max(
                    (int(rec["id"]) for rec in db.values() if rec.get("type") == addr_type),
                    default=None,
                )
                save_db(db)
                save_state(state)
                break

            page += 1
            if page % 10 == 0:
                ts["next_page"] = page
                save_db(db)
                save_state(state)

            sleep_between(MIN_DELAY, MAX_DELAY)

    removed = sweep_removed(db, pass_id)
    state["last_full_completed"] = datetime.now().isoformat(timespec="seconds")
    save_db(db)
    save_state(state)
    stats = generate_lists(db)
    print(f"[full] complete pass={pass_id} removed={removed} {stats}")
    return EXIT_OK


def run_incremental(session, db, state) -> int:
    print("[incr] incremental update")
    pass_id = int(state["pass_id"])
    total_new = 0

    for addr_type in ALL_TYPES:
        ts = state["types"].setdefault(addr_type, _empty_type_state())
        known_max = ts.get("last_max_id") or 0
        type_new = 0
        page = 1

        while page <= INCREMENTAL_MAX_PAGES:
            try:
                data = fetch_page(session, addr_type, page)
            except requests.RequestException as exc:
                print(f"[incr] type={addr_type} page={page} error: {exc}")
                break

            total_pages = data.get("pageCount")
            if total_pages:
                ts["total_pages"] = total_pages
            total_count = data.get("totalCount")
            if total_count:
                ts["total_count"] = total_count

            if page == 1 and total_count:
                type_in_db = sum(1 for r in db.values() if r.get("type") == addr_type)
                if type_in_db < SEED_COMPLETE_FRACTION * total_count:
                    print(f"[incr] type={addr_type} seed incomplete ({type_in_db}/{total_count}), switching to full")
                    ts["full_crawl_complete"] = False
                    ts["next_page"] = 1
                    state["full_crawl_complete"] = False
                    return run_full_crawl(session, db, state, time.monotonic())

            models = data.get("models", [])
            if not models:
                break

            new = store_records(db, models, pass_id)
            type_new += new
            page_min_id = min(int(m["id"]) for m in models if "id" in m)
            print(f"[incr] type={addr_type} page={page} new={new} min_id={page_min_id}")

            if page_min_id <= known_max:
                break
            page += 1
            sleep_between(INC_MIN_DELAY, INC_MAX_DELAY)

        ts["last_max_id"] = max(
            (int(rec["id"]) for rec in db.values() if rec.get("type") == addr_type),
            default=known_max,
        )
        total_new += type_new
        print(f"[incr] type={addr_type} done new={type_new}")

    save_db(db)
    save_state(state)
    stats = generate_lists(db)
    print(f"[incr] done total_new={total_new} {stats}")
    return EXIT_OK


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if is_first_run():
        reset_everything()

    db = load_db()
    state = load_state()

    for t in ALL_TYPES:
        state["types"].setdefault(t, _empty_type_state())
    if not state.get("pass_id"):
        state["pass_id"] = 1
    state["last_run"] = datetime.now().isoformat(timespec="seconds")

    session = make_session()
    start_time = time.monotonic()

    if not all_types_complete(state):
        return run_full_crawl(session, db, state, start_time)
    elif FORCE_FULL_RESYNC or full_resync_due(state):
        state["pass_id"] = int(state["pass_id"]) + 1
        for t in ALL_TYPES:
            state["types"][t]["full_crawl_complete"] = False
            state["types"][t]["next_page"] = 1
        print(f"[resync] pass={state['pass_id']} forced={FORCE_FULL_RESYNC}")
        return run_full_crawl(session, db, state, start_time)
    else:
        return run_incremental(session, db, state)


if __name__ == "__main__":
    sys.exit(main())
