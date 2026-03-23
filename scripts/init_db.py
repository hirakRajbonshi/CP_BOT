import sqlite3
import os
from pathlib import Path

def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            discord_id TEXT PRIMARY KEY,
            cf_handle TEXT NOT NULL
        )
    ''')
    
    # Create pending_auths table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_auths (
            discord_id TEXT PRIMARY KEY,
            cf_handle TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    # Create cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            last_updated REAL NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent  # go up from scripts/ → project root
    db_path = base_dir / "data" / "bot_data.db"
    init_db(str(db_path))