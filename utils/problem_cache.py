import json
import os
import time
import config.settings as settings

CACHE_FILE = settings.PROBLEM_CACHE_FILE
CACHE_TTL = settings.CACHE_TTL_SECONDS


def is_problems_cache_valid():
    if not os.path.exists(CACHE_FILE):
        return False

    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        return time.time() - data["last_updated"] < CACHE_TTL
    except Exception:
        return False


def load_cached_problems():
    with open(CACHE_FILE, "r") as f:
        return json.load(f)["problems"]


def save_problems(problems):
    with open(CACHE_FILE, "w") as f:
        json.dump(
            {
                "last_updated": time.time(),
                "problems": problems
            },
            f
        )
