import os
from pathlib import Path

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    db_path = base_dir / "data" / "bot_data.db"

    print("Deleting database file...\nConfirm(y/n)")
    confirm = input()
    if confirm != "y":
        print("Aborting...")
        exit()

    if db_path.exists():
        os.remove(db_path)
        print("Database file deleted.")
    else:
        print("Database file does not exist.")