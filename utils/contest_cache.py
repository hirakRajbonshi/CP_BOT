import sqlite3
import json
import time
from config.settings import DATABASE_PATH, CACHE_TTL_SECONDS

def get_connection():
    return sqlite3.connect(DATABASE_PATH)

def is_contest_cache_valid():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_updated FROM cache WHERE key = 'contests'")
            result = cursor.fetchone()
            if result:
                return time.time() - result[0] < CACHE_TTL_SECONDS
    except Exception:
        pass
    return False

def load_cached_contests():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM cache WHERE key = 'contests'")
        result = cursor.fetchone()
        if result:
            return json.loads(result[0])
    return []

def save_contests(contests):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO cache (key, data, last_updated) VALUES (?, ?, ?)",
            ('contests', json.dumps(contests), time.time())
        )
        conn.commit()
