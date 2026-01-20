import discord

# Bot Configuration
BOT_PREFIX = ';'
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

# File Paths
USER_DATA_FILE = 'data/user_data.json'
PENDING_AUTH_FILE = 'data/pending_auth.json'
CONTEST_CACHE_FILE = 'cache/contest_cache.json'
PROBLEM_CACHE_FILE = 'cache/problems_cache.json'

# Cache
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours


# Codeforces API
CODEFORCES_API_BASE = "https://codeforces.com/api/"
CODEFORCES_PROBLEMSET_URL = "https://codeforces.com/problemset/problem"

# Duel Configuration
MIN_PROBLEMS = 1
MAX_PROBLEMS = 10
PROBLEM_RATING_TOLERANCE = 100

# Colors
COLOR_PRIMARY = discord.Color.blue()
COLOR_SUCCESS = discord.Color.green()
COLOR_ERROR = discord.Color.red()
COLOR_WARNING = discord.Color.orange()
COLOR_DUEL = discord.Color.gold()