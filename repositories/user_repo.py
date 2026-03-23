import sqlite3
import os
from config.settings import DATABASE_PATH
from datetime import datetime


class UserRepo:
    """Database access layer for user and auth data"""

    @staticmethod
    def _get_connection():
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                cf_handle TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pending_auths (
                discord_id TEXT PRIMARY KEY,
                cf_handle TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                last_updated REAL NOT NULL
            )
        ''')
        return conn

    # -------------------- User Links --------------------

    @staticmethod
    def link_user(discord_id, cf_handle):
        """Link a Discord ID to a Codeforces handle"""
        with UserRepo._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (discord_id, cf_handle) VALUES (?, ?)",
                (str(discord_id), cf_handle)
            )
            conn.commit()

    @staticmethod
    def get_cf_handle(discord_id):
        """Get the linked CF handle for a Discord ID, or None"""
        with UserRepo._get_connection() as conn:
            row = conn.execute(
                "SELECT cf_handle FROM users WHERE discord_id = ?",
                (str(discord_id),)
            ).fetchone()
            return row[0] if row else None

    # -------------------- Pending Auth --------------------

    @staticmethod
    def add_pending_auth(discord_id, cf_handle, problem_id):
        with UserRepo._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO pending_auths "
                "(discord_id, cf_handle, problem_id, timestamp) VALUES (?, ?, ?, ?)",
                (str(discord_id), cf_handle, problem_id, datetime.now().isoformat())
            )
            conn.commit()

    @staticmethod
    def get_pending_auth(discord_id):
        with UserRepo._get_connection() as conn:
            row = conn.execute(
                "SELECT cf_handle, problem_id, timestamp FROM pending_auths WHERE discord_id = ?",
                (str(discord_id),)
            ).fetchone()
            if row:
                return {
                    'cf_handle': row[0],
                    'problem_id': row[1],
                    'timestamp': row[2]
                }
            return None

    @staticmethod
    def remove_pending_auth(discord_id):
        with UserRepo._get_connection() as conn:
            conn.execute(
                "DELETE FROM pending_auths WHERE discord_id = ?",
                (str(discord_id),)
            )
            conn.commit()
