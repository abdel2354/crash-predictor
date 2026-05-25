FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p BIGBULL-ERA/ACCOUNTS BIGBULL-ERA/TOKENS-JWT \
    "BIGBULL-ERA/RARE ACCOUNTS" "BIGBULL-ERA/COUPLES ACCOUNTS" \
    BIGBULL-ERA/GHOST/ACCOUNTS

ENV PYTHONUNBUFFERED=1
ENV BOT_MODE=worker

CMD ["python", "bot_worker.py"]
