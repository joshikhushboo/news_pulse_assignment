import sqlite3
from pathlib import Path

from database import client, create_table, save_articles

ROOT_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = ROOT_DIR / "scraper" / "newspulse.db"


def migrate():
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"Legacy SQLite backup not found: {SQLITE_PATH}")

    connection = sqlite3.connect(SQLITE_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute("SELECT * FROM articles").fetchall()
    connection.close()

    create_table()
    save_articles([dict(row) for row in rows])
    print(f"Migrated {len(rows)} articles to MongoDB")


if __name__ == "__main__":
    try:
        migrate()
    finally:
        client.close()
