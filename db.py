import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "report.db"


def get_conn() -> sqlite3.Connection:
    # timeout: wait for a concurrent writer (e.g. a report mid-render) instead of failing.
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER,
            customer TEXT,
            product TEXT,
            amount REAL,
            created_at DATE
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY,
            path TEXT,
            created_at DATE
        );
        """
    )
    conn.commit()
