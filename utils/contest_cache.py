import json
import os
import time
import config.settings as settings

CACHE_FILE = settings.CONTEST_CACHE_FILE
CACHE_TTL = settings.CACHE_TTL_SECONDS


def is_contest_cache_valid():
    if not os.path.exists(CACHE_FILE):
        return False

    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        return time.time() - data["last_updated"] < CACHE_TTL
    except Exception:
        return False


def load_cached_contests():
    with open(CACHE_FILE, "r") as f:
        return json.load(f)["contests"]


def save_contests(contests):
    with open(CACHE_FILE, "w") as f:
        json.dump(
            {
                "last_updated": time.time(),
                "contests": contests
            },
            f
        )
