FROM python:3.12-slim

# Turkey time so the day-window ageing matches the source data's local time.
ENV TZ=Europe/Istanbul \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

WORKDIR /app

# Install dependencies first for better layer caching.
COPY scraper/requirements.txt /app/scraper/requirements.txt
RUN pip install --no-cache-dir -r /app/scraper/requirements.txt

COPY scraper/ /app/scraper/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Lists + database live on a volume so state survives container restarts.
VOLUME ["/data"]

ENTRYPOINT ["/app/entrypoint.sh"]
