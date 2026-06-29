#!/bin/sh
# Long-running loop for the Docker container.
#
#  * While the full crawl is in progress (fetch.py exits 10), re-run immediately
#    so the multi-day initial crawl makes continuous progress (checkpointed).
#  * Once the full crawl is complete (exit 0), sleep until the top of the next
#    hour and then do an incremental update. Repeat forever.
set -eu

cd /app

seconds_to_next_hour() {
    # Whole seconds remaining until the next HH:00:00.
    # Use epoch seconds to avoid sh octal pitfalls with values like 08/09.
    remain=$(( 3600 - ($(date +%s) % 3600) ))
    # Avoid a zero/near-zero sleep right on the boundary.
    [ "$remain" -le 0 ] && remain=3600
    echo "$remain"
}

echo "[entrypoint] starting SGBList fetcher"

while true; do
    set +e
    python /app/scraper/fetch.py
    rc=$?
    set -e

    if [ "$rc" -eq 10 ]; then
        echo "[entrypoint] full crawl in progress -> continuing immediately"
        continue
    fi

    if [ "$rc" -ne 0 ]; then
        echo "[entrypoint] fetch.py exited with $rc -> retry in 60s"
        sleep 60
        continue
    fi

    secs=$(seconds_to_next_hour)
    echo "[entrypoint] up to date. sleeping ${secs}s until the next hour."
    sleep "$secs"
done
