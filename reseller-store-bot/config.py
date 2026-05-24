# M3SB IOS

import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

ADMIN_IDS = list(
    map(int, filter(None, os.getenv("ADMIN_IDS", "").split(",")))
)

DB_PATH = os.getenv("DB_PATH", "store.db")
