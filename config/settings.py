import discord
import os
from dotenv import load_dotenv

load_dotenv()


# Bot Configuration
BOT_PREFIX = ';'
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True
ERROR_CHANNEL_ID = os.getenv('ERROR_CHANNEL_ID')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')


# File Paths
DATABASE_PATH = 'data/bot_data.db'

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